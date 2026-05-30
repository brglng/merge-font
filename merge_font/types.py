"""Shared data-classes and enumerations for the font-merging pipeline.

Kept in a separate module so that both the pipeline (``merge_font``) and the
configuration loader (``merge_font_config``) can import from here without
creating a circular dependency.
"""
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DoubleWidthStrategy(Enum):
    """How to fit a glyph into a double-width (fullwidth) cell."""

    STRETCH   = "stretch"
    PAD_LEFT  = "pad_left"
    CENTER    = "center"
    PAD_RIGHT = "pad_right"

    def compute_shift(self, available_space: int) -> int:
        """Return the horizontal shift for padding methods."""
        if self is DoubleWidthStrategy.PAD_LEFT:
            return available_space
        if self is DoubleWidthStrategy.CENTER:
            return available_space // 2
        if self is DoubleWidthStrategy.PAD_RIGHT:
            return 0
        return 0  # STRETCH does not use a shift


# ---------------------------------------------------------------------------
# Per-font configuration
# ---------------------------------------------------------------------------


@dataclass
class DoubleWidthConfig:
    """Rule for expanding a set of characters to double (fullwidth) advance width.

    Attributes
    ----------
    chars : list[str | int | tuple[int, int]]
        Characters, codepoints, or (start, end) ranges to widen.
    strategy : DoubleWidthStrategy
        How to fit the original glyph into the wider cell.
        ``STRETCH`` scales the outline horizontally; the padding variants
        (``PAD_LEFT``, ``CENTER``, ``PAD_RIGHT``) insert whitespace on one or
        both sides without distorting the outline.
    """

    chars: list[str | int | tuple[int, int]]
    strategy: DoubleWidthStrategy


@dataclass
class FontMergeConfig:
    """Full configuration for a single font merging task.

    Attributes
    ----------
    double_width : list[DoubleWidthConfig]
        Rules for expanding characters to double (fullwidth) advance width.
        Each entry specifies a set of characters and a method (``stretch``,
        ``left``, ``center``, or ``right``).
    adjust_baseline : bool
        Whether to auto-align CJK baseline to English baseline.
    new_font_family : str
        Font family name for the output.
    new_font_subfamily : str
        Font subfamily name for the output.
    author : str
        Author name written into metadata.
    description : str
        Description written into metadata.
    mark_as_monospace : bool
        Whether to flag the output font as monospaced.
    cjk_scale : float
        Uniform scale applied to CJK glyphs after UPM normalisation.
    western_scale_x : float
        Additional X-axis scale applied to western glyphs after the uniform
        'A'-advance normalisation.  May be larger or smaller than 1.0.
    western_scale_y : float
        Additional Y-axis scale applied to western glyphs after the uniform
        'A'-advance normalisation.  May be larger or smaller than 1.0.
    remove_hints : bool
        Whether to strip all hinting data from the output font.
    cjk_offset_y : float
        Additional vertical offset applied to CJK glyphs in font units.
        Computed from the subfamily-level ``cjk_offset_y`` setting (a UPM
        ratio) by multiplying with ``upm``.
    western_offset_y : float
        Additional vertical offset applied to western glyphs in font units.
        Computed from the subfamily-level ``western_offset_y`` setting (a UPM
        ratio) by multiplying with ``upm``.
    """

    double_width: list[DoubleWidthConfig]
    adjust_baseline: bool
    new_font_family: str
    new_font_subfamily: str
    author: str
    description: str
    mark_as_monospace: bool
    cjk_scale: float
    western_scale_x: float
    western_scale_y: float
    remove_hints: bool
    nerd_font_mono: bool = True
    cjk_offset_y: int = 0
    western_offset_y: int = 0


# ---------------------------------------------------------------------------
# Scaling parameters (shared across subfamilies)
# ---------------------------------------------------------------------------


@dataclass
class ScalingParams:
    """Pre-computed scaling parameters shared across every subfamily.

    Computed from the union of **all** subfamily font files so that cell
    geometry is consistent across weights and styles.

    Attributes
    ----------
    upm : int
        Unified UPM — maximum found across every western and CJK font in
        the family.
    target_adv_c : int
        Full-width (CJK) cell advance in unified UPM units.
        Always ``2 * target_adv_w``.
    target_adv_w : int
        Half-width (western / symbol) cell advance — the maximum
        UPM-normalised advance of ``'A'`` across all western subfamilies.
    """

    upm: int
    target_adv_c: int
    target_adv_w: int


# ---------------------------------------------------------------------------
# Font family specification
# ---------------------------------------------------------------------------


@dataclass
class SubfamilySpec:
    """Font file paths and per-subfamily settings.

    Attributes
    ----------
    name : str
        Subfamily name (e.g. ``"Regular"``, ``"Bold Italic"``).
    western_font : str
        Path to the western (Latin) font for this subfamily.
    cjk_font : str
        Path to the CJK font for this subfamily.  Italic subfamilies may
        point to a different typeface than the upright ones.
    cjk_scale : float
        Uniform scale applied to CJK glyphs after UPM normalisation.
    cjk_offset_y : float
        Additional vertical offset applied to CJK glyphs **after** all CJK
        processing (UPM scaling, cjk_scale, baseline alignment).  Expressed
        as a ratio relative to the font UPM (1.0 = one full em).  Positive
        values shift CJK glyphs downward.  Defaults to 0.0 (no additional
        offset).
    """

    name: str
    western_font: str
    cjk_font: str
    cjk_scale: float = 1.0
    cjk_offset_y: float = 0.0


@dataclass
class FontFamilySpec:
    """Configuration for an entire font family.

    Common settings (metadata, glyph adjustments, symbol overlays) are
    declared once and shared across all subfamilies.  Scaling is computed
    from all pre-loaded subfamily fonts so that cell geometry is consistent
    across weights and styles, even when italic subfamilies use a different
    CJK font.

    Attributes
    ----------
    name : str
        Family name (e.g. ``"My Family NF"``).
    author : str
        Author name written into metadata.
    description : str
        Description written into metadata.
    mark_as_monospace : bool
        Whether to flag the output fonts as monospaced.
    adjust_baseline : bool
        Auto-align CJK baseline to the western baseline.
    double_width : list[DoubleWidthConfig]
        Rules for expanding characters to double (fullwidth) advance width.
    nerd_font : str
        Path to the Nerd Font symbols font (e.g. SymbolsNerdFont-Regular.ttf).
        Empty string means no Nerd Font overlay.
    nerd_font_mono : bool
        When True, use Nerd Font Mono scaling (limit icon height to a weighted
        average of capHeight and line height, constrain all glyphs to single
        cell width).  When False, use Nerd Font (non-mono) scaling (icons can
        use full line height and double-width cells).
    flog_symbols : str
        Path to the Flog Symbols font (e.g. FlogSymbols.ttf).
        Empty string means no Flog Symbols overlay.
    remove_hints : bool
        Strip all hinting data (``fpgm``, ``prep``, ``cvt ``, per-glyph
        programs, and hint-dependent metric tables) from the output fonts.
    western_scale_x : float
        Additional X-axis scale applied to western glyphs after the uniform
        'A'-advance normalisation.  Defaults to 1.0.
    western_scale_y : float
        Additional Y-axis scale applied to western glyphs after the uniform
        'A'-advance normalisation.  Defaults to 1.0.
    western_offset_y : float
        Vertical offset applied to western glyphs, expressed as a ratio
        relative to the font UPM.  Defaults to 0.0.
    subfamilies : list[SubfamilySpec]
        Ordered list of per-subfamily settings.
    """

    name: str
    author: str
    description: str
    mark_as_monospace: bool
    adjust_baseline: bool
    double_width: list[DoubleWidthConfig]
    nerd_font: str
    flog_symbols: str
    nerd_font_mono: bool
    remove_hints: bool
    western_scale_x: float
    western_scale_y: float
    western_offset_y: float
    subfamilies: list[SubfamilySpec]
