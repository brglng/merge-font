# merge-font

[English](./README.md) | [简体中文](./README.zh-Hans.md) | [繁體中文](./README.zh-Hant.md)

A tool for merging western (Latin) and CJK fonts into a single monospaced font
file.

## Features

- **2:1 width ratio** — every CJK glyph is exactly twice the advance width of a
  western glyph, matching the convention used by terminal emulators and code
  editors.
- **Configurable scaling** — fine-tune the size of CJK glyphs and adjust
  western glyph proportions independently on each axis.
- **Baseline alignment** — automatically centres the CJK typeface on the
  western typographic baseline, with manual offsets for precise adjustment.
- **Symbol font overlays** — layer Nerd Font icons and Flog Symbols on top of
  the merged result, with per-glyph scaling strategies (preserve aspect ratio,
  stretch to fill cell, etc.) and both horizontal and vertical centering.
- **Double-width characters** — stretch or pad selected ASCII punctuation (…,
  —, ‘, ’, etc.) to fill a fullwidth cell.
- **Per-subfamily configuration** — each subfamily (e.g. Regular, Italic, Bold)
  can use a different CJK font and independent scaling / offset parameters,
  allowing mix-and-match designs such as pairing a serif CJK font for upright
  styles with a handwriting CJK font for italics.
- **Metadata customisation** — set the font family name, subfamily, author, and
  description.
- **OTF → TTF conversion** — PostScript outlines are automatically converted
  to TrueType for compatibility.
- **Optional hint removal** — strip all TrueType hinting data from the output.

---

## Pre-built Fonts

Pre-generated font files are available on the
[Releases](https://github.com/brglng/merge-font/releases) page. Download the
latest release archive and install the `.ttf` files directly — no build step
required.

---

## Screenshots

### Monaspace Argon + LXGW Bright

![Monaspace Argon LXGW NF](images/Monaspace%20Argon%20LXGW%20NF.png)

### Monaspace Argon + LXGW Bright GB

![Monaspace Argon LXGW GB NF](images/Monaspace%20Argon%20LXGW%20GB%20NF.png)

### Monaspace Argon + LXGW Bright TC

![Monaspace Argon LXGW TC NF](images/Monaspace%20Argon%20LXGW%20TC%20NF.png)

### Monaspace Xenon + Noto Serif SC (Regular) / LXGW Bright GB (Italic)

![Monaspace Xenon Noto LXGW SC NF](images/Monaspace%20Xenon%20Noto%20LXGW%20SC%20NF.png)

### Monaspace Xenon + Noto Serif TC (Regular) / LXGW Bright TC (Italic)

![Monaspace Xenon Noto LXGW TC NF](images/Monaspace%20Xenon%20Noto%20LXGW%20TC%20NF.png)

### JetBrains Mono + Noto Sans SC (Regular) / LXGW Bright GB (Italic)

![JetBrains Noto LXGW SC NF](images/JetBrains%20Noto%20LXGW%20SC%20NF.png)

### JetBrains Mono + Noto Sans TC (Regular) / LXGW Bright TC (Italic)

![JetBrains Noto LXGW TC NF](images/JetBrains%20Noto%20LXGW%20TC%20NF.png)

---

## Table of Contents

- [Requirements](#requirements)
- [Setting Up the Environment with uv](#setting-up-the-environment-with-uv)
- [Running from the Project Root](#running-from-the-project-root)
- [Installing Globally and Running from Anywhere](#installing-globally-and-running-from-anywhere)
- [Configuration File](#configuration-file)
  - [Top-level Defaults](#top-level-defaults)
  - [double\_width Rules](#double_width-rules)
  - [Symbol Font Overlays](#symbol-font-overlays)
  - [Font Families and Subfamilies](#font-families-and-subfamilies)
  - [Family-level Settings](#family-level-settings)
  - [Per-subfamily Settings](#per-subfamily-settings)
  - [Full Example](#full-example)

---

## Requirements

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- [`fonttools`](https://github.com/fonttools/fonttools) ≥ 4.0 (installed automatically)

---

## Setting Up the Environment with uv

```bash
# Clone the repository
git clone https://github.com/brglng/merge-font.git
cd merge-font

# Create a virtual environment and install dependencies
uv sync
```

This creates a `.venv` directory in the project root and installs all required
dependencies declared in `pyproject.toml`.

---

## Running from the Project Root

With the virtual environment set up via `uv`, run the tool directly without
activating the environment:

```bash
uv run merge-font config.toml
```

Or equivalently, using the CLI module entry point:

```bash
uv run python -m merge_font.cli config.toml
```

Replace `config.toml` with the path to your own configuration file.

---

## Installing Globally and Running from Anywhere

Use `uv tool` to install `merge-font` into an isolated global environment so
that the `merge-font` command is available system-wide:

```bash
uv tool install path/to/merge-font
```

Or, install directly from the GitHub repository:

```bash
uv tool install git+https://github.com/brglng/merge-font.git
```

Afterwards you can run it from any directory:

```bash
merge-font /path/to/your/config.toml
```

To upgrade the tool later:

```bash
uv tool upgrade merge-font
```

To uninstall:

```bash
uv tool uninstall merge-font
```

---

## Configuration File

Configuration is written in [TOML](https://toml.io/). The file has three
levels:

1. **Top-level keys** — global defaults shared by every font family.
2. **`[[families]]`** — array of family blocks, each with a ``name`` key and
   optional overrides for the defaults above.
3. **`[[families.subfamilies]]`** — per-weight font file paths and scaling
   factors, nested within a family block.

### Top-level Defaults

| Key | Type | Default | Description |
|---|---|---|---|
| `author` | string | *(required)* | Author name written into font metadata. |
| `description` | string | `""` | Description written into font metadata. |
| `mark_as_monospace` | bool | `true` | Update `xAvgCharWidth` to indicate a monospaced font. |
| `adjust_baseline` | bool | `true` | Auto-align the CJK baseline to the western baseline. |
| `remove_hints` | bool | `false` | Strip all TrueType hinting data from the output. |
| `nerd_font` | string | `""` | Path to the Nerd Font symbols font (e.g. `SymbolsNerdFont-Regular.ttf`). Empty string disables. |
| `nerd_font_mono` | bool | `false` | When `true`, use Nerd Font Mono scaling (icons limited to single cell width and reduced height). When `false`, icons may use full line height and double-width cells. |
| `flog_symbols` | string | `""` | Path to the Flog Symbols font (e.g. `FlogSymbols.ttf`). Empty string disables. |
| `western_scale_x` | float | `1.0` | Additional horizontal scale applied to western glyphs after advance-width normalisation. |
| `western_scale_y` | float | `1.0` | Additional vertical scale applied to western glyphs after advance-width normalisation. |
| `[[double_width]]` | array of tables | `[]` | Rules for widening glyphs to a fullwidth cell. |

All of these keys can be overridden inside any ``[[families]]`` block.

### double\_width Rules

Each `[[double_width]]` table specifies a set of characters to expand to the
double-width (fullwidth, 2×) advance cell:

```toml
[[double_width]]
chars    = ["…", "—"]   # Unicode characters, decimal codepoints, or [start, end] ranges
strategy = "stretch"    # "stretch" | "pad_left" | "center" | "pad_right"
```

| Strategy | Behaviour |
|---|---|
| `stretch` | Scale the glyph outline horizontally to fill the cell. |
| `pad_left` | Keep the glyph's original width; add whitespace on the left. |
| `center` | Keep the glyph's original width; add equal whitespace on both sides. |
| `pad_right` | Keep the glyph's original width; add whitespace on the right. |

The `chars` list accepts three element types:

- A single-character string: `"…"`
- A decimal codepoint integer: `8230`
- An inclusive codepoint range as a two-element array: `[0xFF01, 0xFF60]`

### Symbol Font Overlays

Two symbol font overlays are supported, each with its own scaling strategy:

```toml
nerd_font      = "~/Library/Fonts/SymbolsNerdFont-Regular.ttf"
nerd_font_mono = false
flog_symbols   = "FlogSymbols.ttf"
```

**Nerd Font** symbols are scaled using per-category strategies matching the
upstream Nerd Font patcher:
- **Default glyphs** — preserve aspect ratio, fit within the cell (height
  limited in mono mode).
- **Powerline / Heavy Angle / Progress** — preserve aspect ratio, scale to
  full line height.
- **Box Drawing / Block Elements** — stretch independently in X and Y to fill
  the full cell.
- **Braille** — no additional scaling (UPM normalisation only).

All Nerd Font glyphs are centered both horizontally and vertically within their
target cell.

**Flog Symbols** are scaled uniformly (preserve aspect ratio) so that the
tallest glyph fills the full typographic line height, maintaining consistent
relative proportions across all glyphs.

`~` and environment variables are expanded in all path strings.

### Font Families and Subfamilies

Families are declared as TOML array-of-tables (`[[families]]`). Each family
block must have a `name` key; all other settings fall back to the top-level
defaults and can be overridden at the family level. Subfamilies are nested
under the same family block as `[[families.subfamilies]]` entries:

```toml
[[families]]
name = "My Font NF"
western_scale_x = 0.9
# Optional: override any top-level default for this family only
# remove_hints = false

[[families.subfamilies]]
name         = "Regular"
western_font = "~/Library/Fonts/MyFont-Regular.ttf"
cjk_font     = "~/Library/Fonts/NotoSansCJKtc-Regular.otf"
cjk_scale    = 1.15

[[families.subfamilies]]
name         = "Bold"
western_font = "~/Library/Fonts/MyFont-Bold.ttf"
cjk_font     = "~/Library/Fonts/NotoSansCJKtc-Bold.otf"
cjk_scale    = 1.15
```

Output files are saved in the current working directory with names derived from
the family and subfamily names, e.g. `MyFontNF-Regular.ttf`.

### Family-level Settings

These keys can appear at the top level (as defaults) or inside a `[[families]]`
block to override the default for that family:

| Key | Type | Default | Description |
|---|---|---|---|
| `western_scale_x` | float | `1.0` | Additional horizontal scale applied to western glyphs after advance-width normalisation. Use values below `1.0` to narrow the western text. |
| `western_scale_y` | float | `1.0` | Additional vertical scale applied to western glyphs after advance-width normalisation. |
| `nerd_font` | string | `""` | Path to the Nerd Font symbols font. |
| `nerd_font_mono` | bool | `false` | Nerd Font scaling mode (mono vs non-mono). |
| `flog_symbols` | string | `""` | Path to the Flog Symbols font. |

### Per-subfamily Settings

| Key | Type | Default | Description |
|---|---|---|---|
| `western_font` | string | *(required)* | Path to the western (Latin) font file. |
| `cjk_font` | string | *(required)* | Path to the CJK font file. |
| `cjk_scale` | float | `1.0` | Uniform scale applied to CJK glyphs after UPM normalisation. Values above `1.0` make CJK characters appear larger relative to the western text. |
| `cjk_offset_y` | float (UPM ratio) | `0.0` | Additional vertical offset applied to CJK glyphs after all CJK processing, as a ratio of the font UPM (1.0 = one full em). Positive values shift CJK glyphs upward. |

### Full Example

See [`config.toml`](config.toml) for a complete, annotated configuration file
covering multiple font families with different CJK fonts, scaling factors,
double-width rules, and Nerd Font symbol overlays.
