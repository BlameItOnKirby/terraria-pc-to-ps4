# Terraria PC → PS4 Save Converter

Convert Terraria worlds (`.wld`) and players (`.plr`) **from PC to (decrypted) PS4 format** — the direction no other tool covers. Also converts back (PS4 → PC).

Every existing converter (the Extractinator, `ps4-terraria-decrypter`) only goes PS4 → PC. This tool was built by reverse-engineering those tools' source code, then verified byte-for-byte against real save data and tested end-to-end on a stock PS5.

## Download
No Python Needed - grab **TerrariaConverter.exe** from the [Latest Release](../../releases/latest).

pick a (`.wld`) or (`.plr`), hit convert, done.

Prefer the command line? see [Usage](#usage) below

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

## Requirements

- Python 3.8+
- `pycryptodome` (only needed for `.plr` conversion — worlds use only the standard library)

```bash
pip install -r requirements.txt
```

## Usage

```bash
# PC -> PS4 (default): writes <name>_PS4.wld next to the input
python3 terraria_pc_to_ps4.py myworld.wld

# PC -> PS4 with an explicit output path
python3 terraria_pc_to_ps4.py myplayer.plr -o converted.plr

# PS4 -> PC: writes <name>_PC.wld
python3 terraria_pc_to_ps4.py --to-pc myworld_PS4.wld

# Force the file type (auto-detected from extension/content otherwise)
python3 terraria_pc_to_ps4.py --type wld somefile.bin
```

Every conversion is **round-trip verified** before anything is written: PC → PS4 output is unwrapped again and compared byte-for-byte with the input. If verification fails, no file is written.

## Full workflow (worlds)

This tool produces the *decrypted* PS4-format file — the same layer the Extractinator consumes. To get it onto a console:

1. Convert: `python3 terraria_pc_to_ps4.py myworld.wld`
2. Decrypt your PS4 save (Apollo Save Tool, Save Wizard, etc.) — no jailbreak required, stock consoles work.
3. In the decrypted save folder, replace the existing `.wld` with the converted file, keeping the original filename (e.g. `World25.wld`). Leave `sce_sys/` and everything else untouched.
4. Re-encrypt and re-sign the save with your usual process.
5. Copy it back to the console via USB.

Old PC worlds work too — a 1.3.5-era world (v194) was tested loading on a 1.4.5 console, which auto-migrates it on first load.

## Full workflow for TerrariaConverter.exe
The converter outputs the **decrypted** PS4-format file. To get it onto your console:

1. **Decrypt one of your PS4 saves.** You need an existing decrypted world save to swap into. Free option: [GarlicSaves](https://garlicsaves.com) — no Save Wizard required. (Save Wizard and Apollo Save Tool also work.)
2. **Swap the world file.** In the decrypted save folder, find the `.wld` (e.g. `World25.wld`). Back it up, then copy in your converted file **renamed to match exactly** — if the original was `World25.wld`, your file must be named `World25.wld`. Leave `sce_sys/` and everything else untouched.
3. **Re-encrypt and re-sign** the save with the same tool you used to decrypt.
4. **Copy it back** to your console via USB.

The world will show up in your world list. Old PC worlds work too — a 1.3.5-era world was tested loading on a 1.4.5 console, which auto-migrates it on first load.

## Verification

- `.wld` and `.plr` conversions verified byte-identical against the sample vectors shipped with `ps4-terraria-decrypter` (`World4`, `magic.plr`).
- Header bytes, magic, and size fields verified against a real decrypted PS4 save (CUSA00740).
- End-to-end test: PC world → converted → swapped into a decrypted save → re-signed → **loaded and playable on a stock PS5**.

## Credits

Reverse-engineered from:

- [willturr/the-extractinator](https://github.com/willturr/the-extractinator) — PS4 → PC direction
- [bucanero/save-decrypters](https://github.com/bucanero/save-decrypters) (`ps4-terraria-decrypter` by [hzh](https://github.com/hzhreal/)) — the 8-byte `.wld` header and the `.plr` AES layer

## Disclaimer

Not affiliated with Re-Logic, 505 Games, or DR Studios. For interoperability and personal backup use. Back up your saves before converting — use at your own risk.
"# terraria-pc-to-ps4" 
