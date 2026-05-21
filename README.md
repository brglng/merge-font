# merge-font

A Python tool that merges western (Latin) and CJK fonts into a single font file,
with configurable glyph scaling, symbol font overlays, double-width character
expansion, baseline alignment, and metadata customisation.

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
  - [Per-subfamily Settings](#per-subfamily-settings)
  - [Full Example](#full-example)

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

Or equivalently, using the module entry point:

```bash
uv run python -m merge_font config.toml
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
2. **`[families."<FamilyName>"]`** — overrides for one family (optional).
3. **`[families."<FamilyName>".subfamilies."<SubfamilyName>"]`** — per-weight
   font file paths and scaling factors.

### Top-level Defaults

| Key | Type | Default | Description |
|---|---|---|---|
| `author` | string | *(required)* | Author name written into font metadata. |
| `description` | string | `""` | Description written into font metadata. |
| `mark_as_monospace` | bool | `true` | Update `xAvgCharWidth` to indicate a monospaced font. |
| `adjust_baseline` | bool | `true` | Auto-align the CJK baseline to the western baseline. |
| `remove_hints` | bool | `false` | Strip all TrueType hinting data from the output. |
| `symbol_fonts` | list of paths | `[]` | Symbol fonts to overlay on every subfamily output. |
| `[[double_width]]` | array of tables | `[]` | Rules for widening glyphs to a fullwidth cell. |

All of these keys can be overridden inside any `[families."<Name>"]` section.

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

```toml
symbol_fonts = [
    "~/Library/Fonts/SymbolsNerdFont-Regular.ttf",
    "FlogSymbols.ttf",
]
```

Each listed font is overlaid on top of the merged result. Existing glyphs are
overwritten when names collide. Every symbol glyph's advance width is
normalised to the halfwidth cell.

`~` and environment variables are expanded in all path strings.

### Font Families and Subfamilies

Families are declared as TOML array-of-tables (`[[families]]`). Each family
block must have a `name` key; all other settings fall back to the top-level
defaults and can be overridden at the family level. Subfamilies are nested
under the same family block as `[[families.subfamilies]]` entries:

```toml
[[families]]
name = "My Font NF"
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

### Per-subfamily Settings

| Key | Type | Default | Description |
|---|---|---|---|
| `western_font` | string | *(required)* | Path to the western (Latin) font file. |
| `cjk_font` | string | *(required)* | Path to the CJK font file. |
| `cjk_scale` | float | `1.0` | Uniform scale applied to CJK glyphs after UPM normalisation. Values above `1.0` make CJK characters appear larger relative to the western text. |
| `western_scale_x` | float | `1.0` | Additional horizontal scale applied to western glyphs after advance-width normalisation. Use values below `1.0` to narrow the western text. |
| `western_scale_y` | float | `1.0` | Additional vertical scale applied to western glyphs after advance-width normalisation. |

### Full Example

See [`config.toml`](config.toml) for a complete, annotated configuration file
covering multiple font families with different CJK fonts, scaling factors,
double-width rules, and Nerd Font symbol overlays.

