# Terraria PC → PS4 Save Converter

Convert Terraria worlds (`.wld`) and players (`.plr`) **from PC to (decrypted) PS4 format** — the direction no other tool covers. Also converts back (PS4 → PC).

Every existing converter (the Extractinator, `ps4-terraria-decrypter`) only goes PS4 → PC. This tool was built by reverse-engineering those tools' source code, then verified byte-for-byte against real save data and tested end-to-end on a stock PS5.

## Download

No Python needed — grab **TerrariaConverter.exe** from the [latest release](../../releases/latest).

## Quick start (the app)

1. Open **TerrariaConverter.exe**.
2. Pick your **PC world** (`.wld`).
3. Pick your **decrypted PS4 save folder** (the one with a `.wld` and `sce_sys/` inside).
4. Hit **PACKAGE FOR PS4**.

You get a `.zip` ready to upload for encryption. The app converts your world, swaps it into the save (keeping the original filename, backing up the old one), and zips everything the way encryption tools expect.

## What to do with the ZIP

1. Go to [GarlicSaves](https://garlicsaves.com) (free — no Save Wizard needed).
2. Upload the ZIP and encrypt it for **your** account ID.
3. Copy the encrypted save back to your console via USB.

The world shows up in your world list. Old PC worlds work too — a 1.3.5-era world was tested loading on a 1.4.5 console, which auto-migrates it on first load.

Don't have a decrypted save to start from? Decrypt any of your PS4 Terraria saves first (GarlicSaves, Save Wizard, or Apollo Save Tool), then use that folder in the app.

## Command line (Python script)

Prefer the terminal, or only need a straight conversion without packaging? Use `terraria_pc_to_ps4.py`:

```bash
# PC -> PS4 (default): writes _PS4.wld next to the input
python3 terraria_pc_to_ps4.py myworld.wld

# PC -> PS4 with an explicit output path
python3 terraria_pc_to_ps4.py myplayer.plr -o converted.plr

# PS4 -> PC: writes _PC.wld
python3 terraria_pc_to_ps4.py --to-pc myworld_PS4.wld

# Force the file type (auto-detected from extension/content otherwise)
python3 terraria_pc_to_ps4.py --type wld somefile.bin
```

Every conversion is **round-trip verified** before anything is written: PC → PS4 output is unwrapped again and compared byte-for-byte with the input. If verification fails, no file is written.

If you only did a straight conversion (not the app's packaging), the manual swap is:

1. Decrypt your PS4 save.
2. In the decrypted folder, replace the existing `.wld` with the converted file, **renamed to match exactly** (e.g. `World25.wld`). Leave `sce_sys/` and everything else untouched.
3. Re-encrypt and re-sign, copy back via USB.

## The format

A decrypted PS4 Terraria save wraps the PC file as follows (all integers little-endian):

**Worlds (`.wld`)**

| Offset | Size | Content |
|--------|------|---------|
| 0x00 | 4 | Magic `0x1AA2227E` |
| 0x04 | 4 | Decompressed (PC file) size |
| 0x08 | … | zlib-compressed PC `.wld` |

**Players (`.plr`)**

The whole PC `.plr` is encrypted with **AES-128-CBC**, key = IV = the UTF-16LE string `h3y_gUyZ`:

```
68 00 33 00 79 00 5F 00 67 00 55 00 79 00 5A 00
```

PC files are already 16-byte aligned, so no padding is needed in practice.

## Requirements (Python script only)

- Python 3.8+
- `pycryptodome` (only needed for `.plr` conversion — worlds use only the standard library)

```bash
pip install -r requirements.txt
```

The `.exe` needs nothing — it's self-contained.

## Verification

- `.wld` and `.plr` conversions verified byte-identical against the sample vectors shipped with `ps4-terraria-decrypter` (`World4`, `magic.plr`).
- Header bytes, magic, and size fields verified against a real decrypted PS4 save (CUSA00740).
- End-to-end test: PC world → converted → swapped into a decrypted save → re-signed → **loaded and playable on a stock PS5**.

## Credits

Reverse-engineered from:

- [willturr/the-extractinator](https://github.com/willturr/the-extractinator) — PS4 → PC direction
- [bucanero/save-decrypters](https://github.com/bucanero/save-decrypters) (`ps4-terraria-decrypter` by [hzh](https://github.com/hzh)) — the 8-byte `.wld` header and the `.plr` AES layer

## Disclaimer

Not affiliated with Re-Logic, 505 Games, or DR Studios. For interoperability and personal backup use. Back up your saves before converting — use at your own risk.
