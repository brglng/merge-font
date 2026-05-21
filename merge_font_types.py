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


class Alignment(Enum):
    """Horizontal alignment when padding glyphs with whitespace."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"

    def compute_shift(self, available_space: int) -> int:
        """Return the horizontal shift for the given alignment and space."""
        if self is Alignment.LEFT:
            return 0
        if self is Alignment.CENTER:
            return available_space // 2
        if self is Alignment.RIGHT:
            return available_space


# ---------------------------------------------------------------------------
# Per-font configuration
# ---------------------------------------------------------------------------


@dataclass
class PadConfig:
    """Configuration for padding specific characters with whitespace.

    Attributes
    ----------
    chars : list[str | int | tuple[int, int]]
        Characters, codepoints, or (start, end) ranges to pad.
    alignment : Alignment
        How to align the original glyph within the padded width.
    """

    chars: list[str | int | tuple[int, int]]
    alignment: Alignment


@dataclass
class FontMergeConfig:
    """Full configuration for a single font merging task.

    Attributes
    ----------
    stretch_chars : list[str | int | tuple[int, int]]
        Characters to stretch horizontally to double width.
    pad_configs : list[PadConfig]
        Per-character padding rules.
    adjust_baseline : bool
        Whether to auto-align CJK baseline to English baseline.
    new_font_family : str
        Font family name for the output.
    new_font_subfamily : str
        Font subfamily name for the output.
    new_author : str
        Author name written into metadata.
    new_description : str
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
    """

    stretch_chars: list[str | int | tuple[int, int]]
    pad_configs: list[PadConfig]
    adjust_baseline: bool
    new_font_family: str
    new_font_subfamily: str
    new_author: str
    new_description: str
    mark_as_monospace: bool
    cjk_scale: float
    western_scale_x: float
    western_scale_y: float
    remove_hints: bool


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
    western_font_path : str
        Path to the western (Latin) font for this subfamily.
    cjk_font_path : str
        Path to the CJK font for this subfamily.  Italic subfamilies may
        point to a different typeface than the upright ones.
    cjk_scale : float
        Uniform scale applied to CJK glyphs after UPM normalisation.
    western_scale_x : float
        Additional X-axis scale applied to western glyphs after the uniform
        'A'-advance normalisation.  May be larger or smaller than 1.0.
        Defaults to 1.0 (no extra horizontal scaling).
    western_scale_y : float
        Additional Y-axis scale applied to western glyphs after the uniform
        'A'-advance normalisation.  May be larger or smaller than 1.0.
        Defaults to 1.0 (no extra vertical scaling).
    """

    western_font_path: str
    cjk_font_path: str
    cjk_scale: float = 1.0
    western_scale_x: float = 1.0
    western_scale_y: float = 1.0


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
    new_author : str
        Author name written into metadata.
    new_description : str
        Description written into metadata.
    mark_as_monospace : bool
        Whether to flag the output fonts as monospaced.
    adjust_baseline : bool
        Auto-align CJK baseline to the western baseline.
    stretch_chars : list[str | int | tuple[int, int]]
        Characters to stretch horizontally to double width.
    pad_configs : list[PadConfig]
        Per-character padding rules.
    symbol_font_paths : list[str]
        Paths to symbol fonts to overlay.
    remove_hints : bool
        Strip all hinting data (``fpgm``, ``prep``, ``cvt ``, per-glyph
        programs, and hint-dependent metric tables) from the output fonts.
    subfamilies : dict[str, SubfamilySpec]
        Ordered map of subfamily name → per-subfamily settings.  Each key is
        used as ``new_font_subfamily`` in the output metadata and to derive
        the output filename.
    """

    new_author: str
    new_description: str
    mark_as_monospace: bool
    adjust_baseline: bool
    stretch_chars: list[str | int | tuple[int, int]]
    pad_configs: list[PadConfig]
    symbol_font_paths: list[str]
    remove_hints: bool
    subfamilies: dict[str, SubfamilySpec]
