# merge-font

[English](./README.md) | [简体中文](./README.zh-Hans.md) | [繁體中文](./README.zh-Hant.md)

一個將西文（拉丁）與中日韓（CJK）字型合併為單一等寬字型的工具。

## 功能特性

- **2:1 寬度比** — 每個 CJK 字形的步進寬度恰好是西文字形的兩倍，符合終端模擬器和程式碼編輯器的慣例。
- **可設定縮放** — 精細調整 CJK 字形大小，並可在每個軸上獨立調整西文字形比例。
- **基線對齊** — 自動將 CJK 字面中心對齊西文排版基線，支援手動偏移以進行精確調整。
- **符號字型疊加** — 在合併結果之上疊加 Nerd Font 圖示和 Flog Symbols，支援每個字形的獨立縮放策略（保持寬高比、拉伸填充單元格等），並在水平和垂直方向居中。
- **雙寬字元** — 將選定的 ASCII 標點（…、—、‘、“ 等）拉伸或填充至全形寬度。
- **中繼資料自訂** — 設定字型家族名稱、子家族、作者和描述。
- **OTF → TTF 轉換** — PostScript 輪廓自動轉換為 TrueType 以確保相容性。
- **可選的提示資訊移除** — 從輸出中剥離所有 TrueType 提示資料。

---

## 預建字型

預先產生的字型檔案可在 [Releases](https://github.com/brglng/merge-font/releases) 頁面下載。下載最新版本的壓縮檔，直接安裝其中的 `.ttf` 檔案即可，無需自行建置。

---

## 螢幕截圖

### Monaspace Argon + LXGW Bright

![Monaspace Argon LXGW NF](images/Monaspace%20Argon%20LXGW%20NF.png)

### Monaspace Argon + LXGW Bright GB

![Monaspace Argon LXGW GB NF](images/Monaspace%20Argon%20LXGW%20GB%20NF.png)

### Monaspace Argon + LXGW Bright TC

![Monaspace Argon LXGW TC NF](images/Monaspace%20Argon%20LXGW%20TC%20NF.png)

### Monaspace Xenon + Noto Serif SC（常規體）/ LXGW Bright GB（斜體）

![Monaspace Xenon Noto LXGW SC NF](images/Monaspace%20Xenon%20Noto%20LXGW%20SC%20NF.png)

### Monaspace Xenon + Noto Serif TC（常規體）/ LXGW Bright TC（斜體）

![Monaspace Xenon Noto LXGW TC NF](images/Monaspace%20Xenon%20Noto%20LXGW%20TC%20NF.png)

### JetBrains Mono + Noto Sans SC（常規體）/ LXGW Bright GB（斜體）

![JetBrains Noto LXGW SC NF](images/JetBrains%20Noto%20LXGW%20SC%20NF.png)

### JetBrains Mono + Noto Sans TC（常規體）/ LXGW Bright TC（斜體）

![JetBrains Noto LXGW TC NF](images/JetBrains%20Noto%20LXGW%20TC%20NF.png)

---

## 目錄

- [環境要求](#環境要求)
- [使用 uv 設定環境](#使用-uv-設定環境)
- [從專案根目錄執行](#從專案根目錄執行)
- [全域安裝並隨時隨地執行](#全域安裝並隨時隨地執行)
- [設定檔](#設定檔)
  - [頂層預設值](#頂層預設值)
  - [double\_width 規則](#double_width-規則)
  - [符號字型疊加](#符號字型疊加)
  - [字型家族與子家族](#字型家族與子家族)
  - [家族級設定](#家族級設定)
  - [每個子家族的設定](#每個子家族的設定)
  - [完整範例](#完整範例)

---

## 環境要求

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)（推薦）或 `pip`
- [`fonttools`](https://github.com/fonttools/fonttools) ≥ 4.0（自動安裝）

---

## 使用 uv 設定環境

```bash
# 複製存放庫
git clone https://github.com/brglng/merge-font.git
cd merge-font

# 建立虛擬環境並安裝依賴
uv sync
```

這會在專案根目錄建立一個 `.venv` 目錄，並安裝 `pyproject.toml` 中宣告的所有必要依賴。

---

## 從專案根目錄執行

透過 `uv` 設定虛擬環境後，無需啟用環境即可直接執行工具：

```bash
uv run merge-font config.toml
```

或者等效地，使用模組進入點：

```bash
uv run python -m merge_font config.toml
```

將 `config.toml` 替換為您自己的設定檔路徑。

---

## 全域安裝並隨時隨地執行

使用 `uv tool` 將 `merge-font` 安裝到隔離的全域環境中，使 `merge-font` 命令在系統範圍內可用：

```bash
uv tool install path/to/merge-font
```

或者，直接從 GitHub 存放庫安裝：

```bash
uv tool install git+https://github.com/brglng/merge-font.git
```

之後可以在任何目錄下執行：

```bash
merge-font /path/to/your/config.toml
```

後續升級工具：

```bash
uv tool upgrade merge-font
```

解除安裝：

```bash
uv tool uninstall merge-font
```

---

## 設定檔

設定檔使用 [TOML](https://toml.io/) 編寫，包含三個層級：

1. **頂層鍵** — 每個字型家族共享的全域預設值。
2. **`[[families]]`** — 家族區塊陣列，每個區塊包含一個 ``name`` 鍵以及可選的預設值覆蓋。
3. **`[[families.subfamilies]]`** — 每個字重的字型檔案路徑和縮放因子，巢套在家族區塊內。

### 頂層預設值

| 鍵 | 類型 | 預設值 | 描述 |
|---|---|---|---|
| `author` | 字串 | *(必填)* | 寫入字型中繼資料的作者名稱。 |
| `description` | 字串 | `""` | 寫入字型中繼資料的描述。 |
| `mark_as_monospace` | 布林值 | `true` | 更新 `xAvgCharWidth` 以表明是等寬字型。 |
| `adjust_baseline` | 布林值 | `true` | 自動將 CJK 基線對齊到西文基線。 |
| `remove_hints` | 布林值 | `false` | 從輸出中剥離所有 TrueType 提示資料。 |
| `nerd_font` | 字串 | `""` | Nerd Font 符號字型路徑（如 `SymbolsNerdFont-Regular.ttf`）。空字串表示停用。 |
| `nerd_font_mono` | 布林值 | `true` | 為 `true` 時使用 Nerd Font Mono 縮放（圖示限制在單元格寬度和減小高度）；為 `false` 時圖示可使用全行高和雙寬單元格。 |
| `flog_symbols` | 字串 | `""` | Flog Symbols 字型路徑（如 `FlogSymbols.ttf`）。空字串表示停用。 |
| `western_scale_x` | 浮點數 | `1.0` | 步進寬度標準化後套用於西文字形的額外水平縮放。 |
| `western_scale_y` | 浮點數 | `1.0` | 步進寬度標準化後套用於西文字形的額外垂直縮放。 |
| `western_offset_y` | 浮點數（UPM 比率）| `0.0` | 縮放後套用於西文字形的額外垂直偏移，以字型 UPM 的比率表示。正值向上移動。 |
| `[[double_width]]` | 表格陣列 | `[]` | 將字形擴展為全形寬度的規則。 |

所有這些鍵都可以在任何 ``[[families]]`` 區塊中覆蓋。

### double\_width 規則

每個 `[[double_width]]` 表格指定一組要擴展為雙寬（全形，2×）步進寬度的字元：

```toml
[[double_width]]
chars    = ["…", "—"]   # Unicode 字元、十進位碼位或 [start, end] 範圍
strategy = "stretch"    # "stretch" | "pad_left" | "center" | "pad_right"
```

| 策略 | 行為 |
|---|---|
| `stretch` | 水平縮放字形輪廓以填滿整個寬度。 |
| `pad_left` | 保持原始寬度；在左側新增空白。 |
| `center` | 保持原始寬度；在兩側新增等量空白。 |
| `pad_right` | 保持原始寬度；在右側新增空白。 |

`chars` 列表接受三種元素類型：

- 單字元字串：`"…"`
- 十進位碼位整數：`8230`
- 包含兩個元素的碼位範圍陣列：`[0xFF01, 0xFF60]`

### 符號字型疊加

支援兩種符號字型疊加，各有其獨立的縮放策略：

```toml
nerd_font      = "~/Library/Fonts/SymbolsNerdFont-Regular.ttf"
nerd_font_mono = false
flog_symbols   = "FlogSymbols.ttf"
```

**Nerd Font** 符號使用與上游 Nerd Font 補丁程式一致的每類別縮放策略：
- **預設字形** — 保持寬高比，適應單元格（mono 模式下限制高度）。
- **Powerline / Heavy Angle / Progress** — 保持寬高比，縮放至全行高。
- **Box Drawing / Block Elements** — 在 X 和 Y 軸上獨立拉伸以填充整個單元格。
- **Braille** — 無額外縮放（僅 UPM 標準化）。

所有 Nerd Font 字形在其目標單元格內水平和垂直方向均居中。

**Flog Symbols** 統一縮放（保持寬高比），使最高字形填充全行高，保持所有字形之間一致的相對比例。

所有路徑字串中的 `~` 和環境變數都會被展開。

### 字型家族與子家族

家族以 TOML 表格陣列（`[[families]]`）的形式宣告。每個家族區塊必須有一個 `name` 鍵；所有其他設定回退到頂層預設值，並可在家族級別覆蓋。子家族巢套在同一家族區塊中，作為 `[[families.subfamilies]]` 條目：

```toml
[[families]]
name = "My Font NF"
western_scale_x = 0.9
# 可選：僅針對此家族覆蓋任何頂層預設值
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

輸出檔案儲存在目前工作目錄中，檔案名稱由家族和子家族名稱派生，例如 `MyFontNF-Regular.ttf`。

### 家族級設定

這些鍵可以出現在頂層（作為預設值）或 `[[families]]` 區塊內以覆蓋該家族的預設值：

| 鍵 | 類型 | 預設值 | 描述 |
|---|---|---|---|
| `western_scale_x` | 浮點數 | `1.0` | 步進寬度標準化後套用於西文字形的額外水平縮放。使用小於 `1.0` 的值可收窄西文文字。 |
| `western_scale_y` | 浮點數 | `1.0` | 步進寬度標準化後套用於西文字形的額外垂直縮放。 |
| `western_offset_y` | 浮點數（UPM 比率）| `0.0` | 縮放後套用於西文字形的額外垂直偏移，以字型 UPM 的比率表示（1.0 = 一個全 em）。正值將西文字形向上移動。 |
| `nerd_font` | 字串 | `""` | Nerd Font 符號字型路徑。 |
| `nerd_font_mono` | 布林值 | `false` | Nerd Font 縮放模式（mono 或非 mono）。 |
| `flog_symbols` | 字串 | `""` | Flog Symbols 字型路徑。 |

### 每個子家族的設定

| 鍵 | 類型 | 預設值 | 描述 |
|---|---|---|---|
| `western_font` | 字串 | *(必填)* | 西文（拉丁）字型檔案路徑。 |
| `cjk_font` | 字串 | *(必填)* | CJK 字型檔案路徑。 |
| `cjk_scale` | 浮點數 | `1.0` | UPM 標準化後套用於 CJK 字形的統一縮放。大於 `1.0` 的值使 CJK 字元相對於西文文字更大。 |
| `cjk_offset_y` | 浮點數（UPM 比率）| `0.0` | 在所有 CJK 處理後套用於 CJK 字形的額外垂直偏移，以字型 UPM 的比率表示（1.0 = 一個全 em）。正值將 CJK 字形向上移動。 |

### 完整範例

參見 [`config.toml`](config.toml) 獲取一個完整的、帶註解的設定檔，涵蓋多個字型家族，使用不同的 CJK 字型、縮放因子、雙寬規則和 Nerd Font 符號疊加。
