#!/usr/bin/env python3
"""
Terraria PC <-> PS4 save converter.

Reverse-engineered from:
  - willturr/the-extractinator (the_extractinator.py)      -- PS4 -> PC direction
  - bucanero/save-decrypters ps4-terraria-decrypter/main.c  -- the 8-byte .wld header + .plr AES layer

Formats (all integers little-endian):

  .wld  PS4 = 4-byte magic 0x1AA2227E | uint32 decompressed_size | zlib(PC .wld)
  .plr  PS4 = AES-128-CBC( PC .plr ), key = IV = "h3y_gUyZ" as UTF-16LE
                                   = 68 00 33 00 79 00 5F 00 67 00 55 00 79 00 5A 00

Both directions verified byte-identical against the sample vectors shipped with
ps4-terraria-decrypter (World4.wld.comp/.decomp, magic.plr.enc/.dec).

IMPORTANT: this produces the *decrypted* PS4-format file (the same layer the
Extractinator consumes). You must still place it back into the PS4 save
container and re-encrypt / re-sign it with your own workflow
(Apollo Save Tool, Save Wizard, etc.) before the console will accept it.

Usage:
    python3 terraria_pc_to_ps4.py world.wld              # PC -> PS4, writes world_PS4.wld
    python3 terraria_pc_to_ps4.py player.plr -o out.plr  # PC -> PS4 with explicit output
    python3 terraria_pc_to_ps4.py --to-pc world_PS4.wld   # PS4 -> PC, writes world_PS4_PC.wld
"""

import argparse
import os
import struct
import sys
import zlib

WLD_MAGIC = 0x1AA2227E
PLR_KEY = "h3y_gUyZ".encode("utf-16-le")  # also used as the CBC IV

try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None


# ---------------------------------------------------------------- .wld ----

def wld_pc_to_ps4(data: bytes) -> bytes:
    """Wrap a PC .wld in the PS4 8-byte header + zlib."""
    return struct.pack("<II", WLD_MAGIC, len(data)) + zlib.compress(data)


def wld_ps4_to_pc(data: bytes) -> bytes:
    """Unwrap a decrypted PS4 .wld back to the PC format."""
    if len(data) < 10:
        raise ValueError("file too small to be a PS4 world")
    magic, expected_len = struct.unpack("<II", data[:8])
    if magic != WLD_MAGIC:
        raise ValueError(
            f"bad magic 0x{magic:08X} (expected 0x{WLD_MAGIC:08X}) -- "
            "not all .wld files are compatible with this format"
        )
    out = zlib.decompress(data[8:])
    if len(out) != expected_len:
        raise ValueError(
            f"decompressed size {len(out)} != header size {expected_len}; file may be corrupt"
        )
    return out


# ---------------------------------------------------------------- .plr ----

def _aes():
    if AES is None:
        raise RuntimeError(
            "pycryptodome is required for .plr conversion: pip install pycryptodome"
        )
    return AES.new(PLR_KEY, AES.MODE_CBC, iv=PLR_KEY)


def plr_pc_to_ps4(data: bytes) -> bytes:
    """AES-128-CBC encrypt a PC .plr into the PS4 format."""
    if len(data) % 16:
        pad = 16 - len(data) % 16
        print(f"  [!] .plr not 16-byte aligned, zero-padding {pad} byte(s)", file=sys.stderr)
        data += b"\x00" * pad
    return _aes().encrypt(data)


def plr_ps4_to_pc(data: bytes) -> bytes:
    """AES-128-CBC decrypt a PS4 .plr back to the PC format."""
    data = data[: len(data) & ~15]  # truncate to block boundary, like the C tool
    return _aes().decrypt(data)


# ------------------------------------------------------------- driver ----

CONVERTERS = {
    "wld": (wld_pc_to_ps4, wld_ps4_to_pc, "World"),
    "plr": (plr_pc_to_ps4, plr_ps4_to_pc, "Character"),
}


def detect_type(path: str, to_pc: bool) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext in CONVERTERS:
        return ext
    with open(path, "rb") as f:
        head = f.read(32)
    if to_pc:
        # PS4-format input: .wld wrapper starts with the magic; .plr is raw
        # AES, so trial-decrypt the first block and look for the PC header.
        if len(head) >= 8 and struct.unpack("<I", head[:4])[0] == WLD_MAGIC:
            return "wld"
        if AES is not None and len(head) >= 16:
            try:
                pt = AES.new(PLR_KEY, AES.MODE_CBC, iv=PLR_KEY).decrypt(head[:16])
                if pt[4:11] == b"relogic":
                    return "plr"
            except Exception:  # noqa: BLE001
                pass
    elif len(head) >= 12 and head[4:11] == b"relogic":
        # PC-format input: byte 11 is the file-type tag (0x02 world, 0x03 player)
        return "wld" if head[11] == 0x02 else "plr" if head[11] == 0x03 else None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert Terraria saves between PC and (decrypted) PS4 formats.")
    ap.add_argument("input", help="input .wld or .plr file")
    ap.add_argument("-o", "--out", help="output path (default: <name>_PS4.<ext> or <name>_PC.<ext>)")
    ap.add_argument("--to-pc", action="store_true", help="convert PS4 -> PC instead of PC -> PS4")
    ap.add_argument("--type", choices=["wld", "plr", "auto"], default="auto",
                    help="file type (default: auto-detect from extension/content)")
    ap.add_argument("--no-verify", action="store_true", help="skip the automatic round-trip check")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"error: not a file: {args.input}", file=sys.stderr)
        return 1

    ftype = args.type if args.type != "auto" else detect_type(args.input, args.to_pc)
    if ftype not in CONVERTERS:
        print("error: could not determine file type; use --type wld|plr", file=sys.stderr)
        return 1
    to_ps4, to_pc, label = CONVERTERS[ftype]
    direction = "PC -> PS4" if not args.to_pc else "PS4 -> PC"

    with open(args.input, "rb") as f:
        data = f.read()

    if args.out:
        out_path = args.out
    else:
        base, ext = os.path.splitext(args.input)
        suffix = "_PS4" if not args.to_pc else "_PC"
        out_path = f"{base}{suffix}{ext}"

    print(f"[*] {label} ({ftype}): {direction}")
    print(f"[*] input:  {args.input} ({len(data)} bytes)")

    try:
        converted = (to_ps4 if not args.to_pc else to_pc)(data)
    except Exception as e:  # noqa: BLE001 - report cleanly, keep traceback out of the way
        print(f"error: conversion failed: {e}", file=sys.stderr)
        return 1

    # Round-trip verification.
    #   PC -> PS4: unwrapping our output must reproduce the input byte-for-byte.
    #   PS4 -> PC: re-wrapping our output and unwrapping again must be stable
    #              (byte comparison can't be used here: zlib recompression is
    #              not deterministic across implementations, but any valid zlib
    #              stream decodes identically).
    if not args.no_verify:
        try:
            if not args.to_pc:
                ok = to_pc(converted) == data
            else:
                ok = to_pc(to_ps4(converted)) == converted
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  [!] round-trip check error: {e}", file=sys.stderr)
        print(f"[*] round-trip verification: {'OK' if ok else 'FAILED'}")
        if not ok:
            print("error: refusing to write a file that does not round-trip", file=sys.stderr)
            return 1

    with open(out_path, "wb") as f:
        f.write(converted)
    print(f"[*] wrote:  {out_path} ({len(converted)} bytes)")

    if not args.to_pc:
        print("[*] NOTE: this is the decrypted PS4-format file; re-inject + re-sign it "
              "with your PS4 save workflow before use on console.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
