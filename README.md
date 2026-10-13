# Terraria Converter V3 — PC ↔ PS4 Toolkit

Convert Terraria worlds (`.wld`) and players (`.plr`) between **PC and PS4** with a single tool. No other converter covers the PC → PS4 direction — this was built by reverse-engineering existing tools, then verified on real hardware.

## Download

Get `TerrariaConverterV3.exe` from the [latest release](../../releases/latest). No Python needed — it's a single self-contained app.

To build from source, see [Building](#building).

## How it works

V3 uses **template slots** — 10 pre-made PS4 saves called "Terraria PC to PS4" (World2, World4–World12). You pick a slot, drop in your PC world, and V3 swaps it into the template. The output is a decrypted save ready to encrypt for your console.

Why templates instead of generating from scratch? The PS4 save metadata (`param.sfo`) contains a 1024-byte `PARAMS` field with save-specific cryptographic data that can't be forged. Swapping into a real template is the only reliable method — proven on stock PS5 hardware.

## Worlds tab

1. **Pick a template slot** from the dropdown (World2, World4, World5, … World12)
2. **Pick your PC `.wld`** file
3. Optionally set **difficulty** (Normal / Expert / Master / Journey — requires world version 209+)
4. Optionally set a new **world name**
5. Hit **CONVERT WORLD** → get a ZIP ready for GarlicSaves

To go the other way (PS4 → PC), flip the direction toggle.

### Getting it on your console

1. Convert your world in V3 → you get a ZIP
2. Upload the ZIP to [GarlicSaves](https://garlicsaves.com) to encrypt for your account
3. Copy the encrypted save to USB → PS5/PS4 → load and play

Old PC worlds work — a 1.3.5-era world (v194) was tested loading on a 1.4.5 console, which auto-migrates on first load.

## Players tab

Convert `.plr` files between PC and PS4 format (AES-128-CBC layer). Requires `pycryptodome` when running from source (bundled in the exe).

### Inventory editor

Hit **EDIT INVENTORY** to open Terrasavr Plus (bundled, works offline):

1. Pick your `.plr` file
2. Click Edit Inventory — V3 converts to PC format and opens the editor
3. Load the temp file in your browser, edit items/equipment
4. Download the modified `.plr`
5. Convert back with PC → PS4

## The format

Decrypted PS4 saves wrap PC files as follows (all integers little-endian):

**Worlds (`.wld`)**

| Offset | Size | Content |
|--------|------|---------|
| 0x00 | 4 | Magic `0x1AA2227E` |
| 0x04 | 4 | Decompressed (PC file) size |
| 0x08 | … | zlib-compressed PC `.wld` |

**Players (`.plr`)**

AES-128-CBC encrypted, key = IV = UTF-16LE `"h3y_gUyZ"`:

```
68 00 33 00 79 00 5F 00 67 00 55 00 79 00 5A 00
```

## Building

```bash
pip install pyinstaller pycryptodome
```

Double-click `build_exe_v3.bat` (Windows). The exe lands in `dist/`.

Or manually:

```bash
pyinstaller --onefile --windowed --name=TerrariaConverterV3 \
  --add-data "v3_templates;v3_templates" \
  --add-data "terrasavr;terrasavr" \
  terraria_converter_v3.py
```

## CLI

The core conversion also works from the command line:

```bash
# PC -> PS4 world (via template slot)
python3 terraria_converter_v3.py  # launches GUI
```

For scriptable conversions, see `v3_swap.py`:

```python
from v3_swap import swap_pc_to_ps4
swap_pc_to_ps4("myworld.wld", "World5", "/tmp/out")
```

## Verification

- `.wld` / `.plr` conversions verified byte-identical against `ps4-terraria-decrypter` sample vectors
- Template swap method tested end-to-end on **stock PS5**: PC world → swapped into template → encrypted via GarlicSaves → loaded and playable
- From-scratch save generation was attempted and **rejected** — shows up in the world list but hangs on load due to unforgable `PARAMS` crypto. The template swap is the correct approach.

## Credits

Reverse-engineered from:

- [willturr/the-extractinator](https://github.com/willturr/the-extractinator)
- [bucanero/save-decrypters](https://github.com/bucanero/save-decrypters) (ps4-terraria-decrypter by [hzh](https://github.com/hzhreal/))
- [Terrasavr Plus](https://yellowafterlife.itch.io/terrasavr) by YellowAfterlife (bundled for offline inventory editing)

## Disclaimer

Not affiliated with Re-Logic, 505 Games, or DR Studios. For interoperability and personal backup use. Back up your saves before converting.
