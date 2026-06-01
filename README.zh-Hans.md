# merge-font

[English](./README.md) | [简体中文](./README.zh-Hans.md) | [繁體中文](./README.zh-Hant.md)

一个将西文（拉丁）与中日韩（CJK）字体合并为单一等宽字体的工具。

## 功能特性

- **2:1 宽度比** — 每个 CJK 字形的步进宽度恰好是西文字形的两倍，符合终端模拟器和代码编辑器的惯例。
- **可配置缩放** — 精细调整 CJK 字形大小，并可在每个轴上独立调整西文字形比例。
- **基线对齐** — 自动将 CJK 字面中心对齐西文排版基线，支持手动偏移以进行精确调整。
- **符号字体叠加** — 在合并结果之上叠加 Nerd Font 图标和 Flog Symbols，支持每个字形的独立缩放策略（保持宽高比、拉伸填充单元格等），并在水平和垂直方向居中。
- **双宽字符** — 将选定的 ASCII 标点（…、—、‘、“ 等）拉伸或填充至全角宽度。
- **每个子家族独立配置** — 每个子家族（如 Regular、Italic、Bold）可以使用不同的 CJK 字体和独立的缩放/偏移参数，支持混合搭配设计，例如正体使用宋体 CJK 字体、斜体使用手写风格 CJK 字体。
- **元数据自定义** — 设置字体家族名称、子家族、作者和描述。
- **OTF → TTF 转换** — PostScript 轮廓自动转换为 TrueType 以确保兼容性。
- **可选的提示信息移除** — 从输出中剥离所有 TrueType 提示数据。

---

## 预构建字体

预生成的字体文件可在 [Releases](https://github.com/brglng/merge-font/releases) 页面下载。下载最新版本的压缩包，直接安装其中的 `.ttf` 文件即可，无需自行构建。

---

## 截图

### Monaspace Argon + LXGW Bright

![Monaspace Argon LXGW NF](images/Monaspace%20Argon%20LXGW%20NF.png)

### Monaspace Argon + LXGW Bright GB

![Monaspace Argon LXGW GB NF](images/Monaspace%20Argon%20LXGW%20GB%20NF.png)

### Monaspace Argon + LXGW Bright TC

![Monaspace Argon LXGW TC NF](images/Monaspace%20Argon%20LXGW%20TC%20NF.png)

### Monaspace Xenon + Noto Serif SC（常规体）/ LXGW Bright GB（斜体）

![Monaspace Xenon Noto LXGW SC NF](images/Monaspace%20Xenon%20Noto%20LXGW%20SC%20NF.png)

### Monaspace Xenon + Noto Serif TC（常规体）/ LXGW Bright TC（斜体）

![Monaspace Xenon Noto LXGW TC NF](images/Monaspace%20Xenon%20Noto%20LXGW%20TC%20NF.png)

### JetBrains Mono + Noto Sans SC（常规体）/ LXGW Bright GB（斜体）

![JetBrains Noto LXGW SC NF](images/JetBrains%20Noto%20LXGW%20SC%20NF.png)

### JetBrains Mono + Noto Sans TC（常规体）/ LXGW Bright TC（斜体）

![JetBrains Noto LXGW TC NF](images/JetBrains%20Noto%20LXGW%20TC%20NF.png)

---

## 目录

- [环境要求](#环境要求)
- [使用 uv 设置环境](#使用-uv-设置环境)
- [从项目根目录运行](#从项目根目录运行)
- [全局安装并随时随地运行](#全局安装并随时随地运行)
- [配置文件](#配置文件)
  - [顶层默认值](#顶层默认值)
  - [double\_width 规则](#double_width-规则)
  - [符号字体叠加](#符号字体叠加)
  - [字体家族与子家族](#字体家族与子家族)
  - [家族级设置](#家族级设置)
  - [每个子家族的设置](#每个子家族的设置)
  - [完整示例](#完整示例)

---

## 环境要求

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)（推荐）或 `pip`
- [`fonttools`](https://github.com/fonttools/fonttools) ≥ 4.0（自动安装）

---

## 使用 uv 设置环境

```bash
# 克隆仓库
git clone https://github.com/brglng/merge-font.git
cd merge-font

# 创建虚拟环境并安装依赖
uv sync
```

这会在项目根目录创建一个 `.venv` 目录，并安装 `pyproject.toml` 中声明的所有必需依赖。

---

## 从项目根目录运行

通过 `uv` 设置虚拟环境后，无需激活环境即可直接运行工具：

```bash
uv run merge-font config.toml
```

或者等效地，使用模块入口点：

```bash
uv run python -m merge_font config.toml
```

将 `config.toml` 替换为您自己的配置文件路径。

---

## 全局安装并随时随地运行

使用 `uv tool` 将 `merge-font` 安装到隔离的全局环境中，使 `merge-font` 命令在系统范围内可用：

```bash
uv tool install path/to/merge-font
```

或者，直接从 GitHub 仓库安装：

```bash
uv tool install git+https://github.com/brglng/merge-font.git
```

之后可以在任何目录下运行：

```bash
merge-font /path/to/your/config.toml
```

后续升级工具：

```bash
uv tool upgrade merge-font
```

卸载：

```bash
uv tool uninstall merge-font
```

---

## 配置文件

配置文件使用 [TOML](https://toml.io/) 编写，包含三个层级：

1. **顶层键** — 每个字体家族共享的全局默认值。
2. **`[[families]]`** — 家族块数组，每个块包含一个 ``name`` 键以及可选的默认值覆盖。
3. **`[[families.subfamilies]]`** — 每个字重的字体文件路径和缩放因子，嵌套在家族块内。

### 顶层默认值

| 键 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `author` | 字符串 | *(必填)* | 写入字体元数据的作者名称。 |
| `description` | 字符串 | `""` | 写入字体元数据的描述。 |
| `mark_as_monospace` | 布尔值 | `true` | 更新 `xAvgCharWidth` 以表明是等宽字体。 |
| `adjust_baseline` | 布尔值 | `true` | 自动将 CJK 基线对齐到西文基线。 |
| `remove_hints` | 布尔值 | `false` | 从输出中剥离所有 TrueType 提示数据。 |
| `nerd_font` | 字符串 | `""` | Nerd Font 符号字体路径（如 `SymbolsNerdFont-Regular.ttf`）。空字符串表示禁用。 |
| `nerd_font_mono` | 布尔值 | `false` | 为 `true` 时使用 Nerd Font Mono 缩放（图标限制在单元格宽度和减小高度）；为 `false` 时图标可使用全行高和双宽单元格。 |
| `flog_symbols` | 字符串 | `""` | Flog Symbols 字体路径（如 `FlogSymbols.ttf`）。空字符串表示禁用。 |
| `western_scale_x` | 浮点数 | `1.0` | 步进宽度标准化后应用于西文字形的额外水平缩放。 |
| `western_scale_y` | 浮点数 | `1.0` | 步进宽度标准化后应用于西文字形的额外垂直缩放。 |
| `[[double_width]]` | 表格数组 | `[]` | 将字形扩展为全角宽度的规则。 |

所有这些键都可以在任何 ``[[families]]`` 块中覆盖。

### double\_width 规则

每个 `[[double_width]]` 表格指定一组要扩展为双宽（全角，2×）步进宽度的字符：

```toml
[[double_width]]
chars    = ["…", "—"]   # Unicode 字符、十进制码位或 [start, end] 范围
strategy = "stretch"    # "stretch" | "pad_left" | "center" | "pad_right"
```

| 策略 | 行为 |
|---|---|
| `stretch` | 水平缩放字形轮廓以填满整个宽度。 |
| `pad_left` | 保持原始宽度；在左侧添加空白。 |
| `center` | 保持原始宽度；在两侧添加等量空白。 |
| `pad_right` | 保持原始宽度；在右侧添加空白。 |

`chars` 列表接受三种元素类型：

- 单字符字符串：`"…"`
- 十进制码位整数：`8230`
- 包含两个元素的码位范围数组：`[0xFF01, 0xFF60]`

### 符号字体叠加

支持两种符号字体叠加，各有其独立的缩放策略：

```toml
nerd_font      = "~/Library/Fonts/SymbolsNerdFont-Regular.ttf"
nerd_font_mono = false
flog_symbols   = "FlogSymbols.ttf"
```

**Nerd Font** 符号使用与上游 Nerd Font 补丁程序一致的每类别缩放策略：
- **默认字形** — 保持宽高比，适应单元格（mono 模式下限制高度）。
- **Powerline / Heavy Angle / Progress** — 保持宽高比，缩放至全行高。
- **Box Drawing / Block Elements** — 在 X 和 Y 轴上独立拉伸以填充整个单元格。
- **Braille** — 无额外缩放（仅 UPM 标准化）。

所有 Nerd Font 字形在其目标单元格内水平和垂直方向均居中。

**Flog Symbols** 统一缩放（保持宽高比），使最高字形填充全行高，保持所有字形之间一致的相对比例。

所有路径字符串中的 `~` 和环境变量都会被展开。

### 字体家族与子家族

家族以 TOML 表格数组（`[[families]]`）的形式声明。每个家族块必须有一个 `name` 键；所有其他设置回退到顶层默认值，并可在家族级别覆盖。子家族嵌套在同一家族块中，作为 `[[families.subfamilies]]` 条目：

```toml
[[families]]
name = "My Font NF"
western_scale_x = 0.9
# 可选：仅针对此家族覆盖任何顶层默认值
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

输出文件保存在当前工作目录中，文件名由家族和子家族名称派生，例如 `MyFontNF-Regular.ttf`。

### 家族级设置

这些键可以出现在顶层（作为默认值）或 `[[families]]` 块内以覆盖该家族的默认值：

| 键 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `western_scale_x` | 浮点数 | `1.0` | 步进宽度标准化后应用于西文字形的额外水平缩放。使用小于 `1.0` 的值可收窄西文文本。 |
| `western_scale_y` | 浮点数 | `1.0` | 步进宽度标准化后应用于西文字形的额外垂直缩放。 |
| `nerd_font` | 字符串 | `""` | Nerd Font 符号字体路径。 |
| `nerd_font_mono` | 布尔值 | `false` | Nerd Font 缩放模式（mono 或非 mono）。 |
| `flog_symbols` | 字符串 | `""` | Flog Symbols 字体路径。 |

### 每个子家族的设置

| 键 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `western_font` | 字符串 | *(必填)* | 西文（拉丁）字体文件路径。 |
| `cjk_font` | 字符串 | *(必填)* | CJK 字体文件路径。 |
| `cjk_scale` | 浮点数 | `1.0` | UPM 标准化后应用于 CJK 字形的统一缩放。大于 `1.0` 的值使 CJK 字符相对于西文文本更大。 |
| `cjk_offset_y` | 浮点数（UPM 比率）| `0.0` | 在所有 CJK 处理后应用于 CJK 字形的额外垂直偏移，以字体 UPM 的比率表示（1.0 = 一个全 em）。正值将 CJK 字形向上移动。 |

### 完整示例

参见 [`config.toml`](config.toml) 获取一个完整的、带注释的配置文件，涵盖多个字体家族，使用不同的 CJK 字体、缩放因子、双宽规则和 Nerd Font 符号叠加。
