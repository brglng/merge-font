"""Nerd Font symbol patching logic.

The scaling rules in this module mirror the upstream Nerd Font
``font-patcher`` attributes and scale groups for the symbol ranges that need
special handling.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Literal

from fontTools.ttLib import TTFont

from merge_font import (
    FontTables,
    GlyphTransformer,
    _get_glyph_bbox,
    copy_glyph_into,
    copy_hinting_tables,
    get_glyph_dependencies,
    get_typical_advance,
)


StretchMode = Literal["", "pa", "^pa", "^pa1!", "^xy", "^xy2", "pa1!"]
AlignMode = Literal["", "l", "c", "r"]
MAX_VERTICAL_OVERLAP = 0.01


@dataclass(frozen=True)
class SymbolAttributes:
    """Upstream font-patcher symbol placement attributes."""

    align: AlignMode = "c"
    valign: AlignMode = "c"
    stretch: StretchMode = "pa"
    overlap: float | None = None
    ypadding: float = 0.0
    xy_ratio: float | None = None


@dataclass(frozen=True)
class ScaleGroup:
    """A set of glyphs that share an upstream combined bounding-box scale."""

    codepoints: frozenset[int]
    shift_mode: str = ""


@dataclass(frozen=True)
class GlyphDimensions:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    width: float
    height: float
    advance: float | None = None

    def scaled(self, scale_x: float, scale_y: float) -> GlyphDimensions:
        return GlyphDimensions(
            xmin=self.xmin * scale_x,
            ymin=self.ymin * scale_y,
            xmax=self.xmax * scale_x,
            ymax=self.ymax * scale_y,
            width=self.width * scale_x,
            height=self.height * scale_y,
            # Horizontal advances are X-axis metrics; vertical metrics stay in vmtx.
            advance=None if self.advance is None else self.advance * scale_x,
        )


def _range_set(start: int, end: int) -> frozenset[int]:
    return frozenset(range(start, end + 1))


def _ranges_set(ranges: Iterable[tuple[int, int]]) -> frozenset[int]:
    result: set[int] = set()
    for start, end in ranges:
        result.update(range(start, end + 1))
    return frozenset(result)


POWERLINE_SET = _ranges_set((
    (0xE0A0, 0xE0A2),
    (0xE0B0, 0xE0B3),
    (0xE0A3, 0xE0A3),
    (0xE0B4, 0xE0C8),
    (0xE0CA, 0xE0CA),
    (0xE0CC, 0xE0D7),
    (0x2630, 0x2630),
))
HEAVY_ANGLE_SET = _range_set(0x276C, 0x2771)
BOX_DRAWING_SET = _range_set(0x2500, 0x259F)
PROGRESS_SET = _range_set(0xEE00, 0xEE0B)
BRAILLE_SET = _range_set(0x2800, 0x28FF)


def _offset_range(start: int, end: int, offset: int) -> frozenset[int]:
    return frozenset(range(start + offset, end + offset + 1))


def _offset_values(values: Iterable[int], offset: int) -> frozenset[int]:
    return frozenset(value + offset for value in values)


WEATHER_OFFSET = 0xE300 - 0xF000
OCTICONS_OFFSET_1 = 0xF400 - 0xF000
OCTICONS_OFFSET_2 = 0xF4A9 - 0xF27C


UNCONDITIONAL_RANGES = (
    (0xE5FA, 0xE6FF),  # Seti-UI + Custom
    (0x276C, 0x2771),  # Heavy Angle Brackets
    (0xEE00, 0xEE0B),  # Progress Indicators
    (0xE700, 0xE8EF),  # Devicons
    (0xE0A0, 0xE0A2),  # Powerline Symbols
    (0xE0B0, 0xE0B3),
    (0xE0A3, 0xE0A3),  # Powerline Extra Symbols
    (0xE0B4, 0xE0C8),
    (0xE0CA, 0xE0CA),
    (0xE0CC, 0xE0D7),
    (0x2630, 0x2630),
    (0xE000, 0xE00A),  # Pomicons
    (0xED00, 0xF2FF),  # Font Awesome
    (0xE200, 0xE2A9),  # Font Awesome Extension
    (0x23FB, 0x23FE),  # Power Symbols
    (0x2B58, 0x2B58),
    (0xF0001, 0xF1AF0),  # Material Design Icons
    (0xE300, 0xE3EB),  # Weather Icons
    (0xF300, 0xF381),  # Font Logos
    (0xF400, 0xF505),  # Octicons, remapped first range
    (0x2665, 0x2665),
    (0x26A1, 0x26A1),
    (0xF4A9, 0xF533),  # Octicons, remapped second range
    (0xEA60, 0xEC1E),  # Codicons
)
UNCONDITIONAL_SET = _ranges_set(UNCONDITIONAL_RANGES)
CAREFUL_SET = HEAVY_ANGLE_SET | PROGRESS_SET | frozenset({0x2630})


POWERLINE_ATTRIBUTES: dict[int, SymbolAttributes] = {
    0xE0B0: SymbolAttributes("l", "c", "^xy", overlap=0.06, xy_ratio=0.7),
    0xE0B1: SymbolAttributes("l", "c", "^xy", xy_ratio=0.7),
    0xE0B2: SymbolAttributes("r", "c", "^xy", overlap=0.06, xy_ratio=0.7),
    0xE0B3: SymbolAttributes("r", "c", "^xy", xy_ratio=0.7),
    0xE0D6: SymbolAttributes("l", "c", "^xy", overlap=0.05, xy_ratio=0.7),
    0xE0D7: SymbolAttributes("r", "c", "^xy", overlap=0.05, xy_ratio=0.7),
    0xE0B4: SymbolAttributes("l", "c", "^xy", overlap=0.06, xy_ratio=0.59),
    0xE0B5: SymbolAttributes("l", "c", "^xy", xy_ratio=0.5),
    0xE0B6: SymbolAttributes("r", "c", "^xy", overlap=0.06, xy_ratio=0.59),
    0xE0B7: SymbolAttributes("r", "c", "^xy", xy_ratio=0.5),
    0xE0B8: SymbolAttributes("l", "c", "^xy", overlap=0.05),
    0xE0B9: SymbolAttributes("l", "c", "^xy"),
    0xE0BA: SymbolAttributes("r", "c", "^xy", overlap=0.05),
    0xE0BB: SymbolAttributes("r", "c", "^xy"),
    0xE0BC: SymbolAttributes("l", "c", "^xy", overlap=0.05),
    0xE0BD: SymbolAttributes("l", "c", "^xy"),
    0xE0BE: SymbolAttributes("r", "c", "^xy", overlap=0.05),
    0xE0BF: SymbolAttributes("r", "c", "^xy"),
    0xE0C0: SymbolAttributes("l", "c", "^xy2", overlap=0.05),
    0xE0C1: SymbolAttributes("l", "c", "^xy2"),
    0xE0C2: SymbolAttributes("r", "c", "^xy2", overlap=0.05),
    0xE0C3: SymbolAttributes("r", "c", "^xy2"),
    0xE0C4: SymbolAttributes("l", "c", "^xy2", overlap=-0.03, xy_ratio=0.86),
    0xE0C5: SymbolAttributes("r", "c", "^xy2", overlap=-0.03, xy_ratio=0.86),
    0xE0C6: SymbolAttributes("l", "c", "^xy2", overlap=-0.03, xy_ratio=0.78),
    0xE0C7: SymbolAttributes("r", "c", "^xy2", overlap=-0.03, xy_ratio=0.78),
    0xE0C8: SymbolAttributes("l", "c", "^xy2", overlap=0.05),
    0xE0CA: SymbolAttributes("r", "c", "^xy2", overlap=0.05),
    0xE0CC: SymbolAttributes("l", "c", "^xy2", overlap=0.02, xy_ratio=0.85),
    0xE0CD: SymbolAttributes("l", "c", "^xy2", xy_ratio=0.865),
    0xE0CE: SymbolAttributes("l", "c", "^pa"),
    0xE0CF: SymbolAttributes("c", "c", "^pa"),
    0xE0D0: SymbolAttributes("l", "c", "^pa"),
    0xE0D1: SymbolAttributes("l", "c", "^pa"),
    0xE0D2: SymbolAttributes("l", "c", "^xy", overlap=0.02, xy_ratio=0.7),
    0xE0D4: SymbolAttributes("r", "c", "^xy", overlap=0.02, xy_ratio=0.7),
    0x2630: SymbolAttributes("c", "c", "pa1!", overlap=-0.10),
}


PROGRESS_ATTRIBUTES: dict[int, SymbolAttributes] = {
    0xEE00: SymbolAttributes("r", "c", "^xy", overlap=0.05),
    0xEE01: SymbolAttributes("c", "c", "^xy", overlap=0.10),
    0xEE02: SymbolAttributes("l", "c", "^xy", overlap=0.05),
    0xEE03: SymbolAttributes("r", "c", "^xy", overlap=0.05),
    0xEE04: SymbolAttributes("c", "c", "^xy", overlap=0.10),
    0xEE05: SymbolAttributes("l", "c", "^xy", overlap=0.05),
}


SCALE_GROUPS: tuple[ScaleGroup, ...] = (
    ScaleGroup(frozenset((*range(0x2500, 0x2570 + 1), *range(0x2574, 0x257F + 1))), "xy"),
    ScaleGroup(_range_set(0x2571, 0x2573), "xy"),
    ScaleGroup(_range_set(0x2580, 0x259F), "xy"),
    ScaleGroup(HEAVY_ANGLE_SET, "xy"),
    ScaleGroup(_range_set(0xEDFF, 0xEE05), "xy"),
    ScaleGroup(_range_set(0xEE06, 0xEE0B), "xy"),
    ScaleGroup(frozenset({0xF005, 0xF006, 0xF089})),
    ScaleGroup(_range_set(0xF026, 0xF028)),
    ScaleGroup(_range_set(0xF02B, 0xF02C)),
    ScaleGroup(_range_set(0xF031, 0xF035)),
    ScaleGroup(_range_set(0xF044, 0xF046)),
    ScaleGroup(_range_set(0xF048, 0xF052)),
    ScaleGroup(_range_set(0xF060, 0xF063)),
    ScaleGroup(frozenset({0xF053, 0xF054, 0xF077, 0xF078})),
    ScaleGroup(_range_set(0xF07D, 0xF07E)),
    ScaleGroup(_range_set(0xF0A4, 0xF0A7)),
    ScaleGroup(frozenset({0xF0D7, 0xF0D8, 0xF0D9, 0xF0DA, 0xF0DC, 0xF0DD, 0xF0DE})),
    ScaleGroup(_range_set(0xF100, 0xF107)),
    ScaleGroup(_range_set(0xF130, 0xF131)),
    ScaleGroup(_range_set(0xF141, 0xF142)),
    ScaleGroup(_range_set(0xF153, 0xF15A)),
    ScaleGroup(_range_set(0xF175, 0xF178)),
    ScaleGroup(_range_set(0xF182, 0xF183)),
    ScaleGroup(_range_set(0xF221, 0xF22D)),
    ScaleGroup(_range_set(0xF255, 0xF25B)),
    ScaleGroup(frozenset({0xEA61, 0xEB13}), "xy"),
    ScaleGroup(_range_set(0xEAB4, 0xEAB7), "xy"),
    ScaleGroup(frozenset((0xEA7D, *range(0xEA99, 0xEAA1 + 1), 0xEBCB)), "xy"),
    ScaleGroup(frozenset({0xEAA2, 0xEB9A, 0xEC08, 0xEC09}), "xy"),
    ScaleGroup(_range_set(0xEAD4, 0xEAD6), "xy"),
    ScaleGroup(frozenset({0xEB43, 0xEC0B, 0xEC0C}), "xy"),
    ScaleGroup(_range_set(0xEB6E, 0xEB71), "xy"),
    ScaleGroup(frozenset((*range(0xEB89, 0xEB8B + 1), 0xEC07)), "xy"),
    ScaleGroup(_range_set(0xEBD5, 0xEBD7), "xy"),
    ScaleGroup(frozenset((
        *_offset_range(0xF03D, 0xF040, OCTICONS_OFFSET_1),
        *_offset_values((0xF019, 0xF030, 0xF04A, 0xF051, 0xF071, 0xF08C), OCTICONS_OFFSET_1),
    ))),
    ScaleGroup(frozenset((
        *_offset_values((
            0xF0E7,
            0xF044,
            0xF05A,
            0xF05B,
            0xF0AA,
            0xF052,
            0xF053,
            0xF078,
            0xF0A2,
            0xF0A3,
            0xF0A4,
            0xF0CA,
            0xF081,
            0xF092,
        ), OCTICONS_OFFSET_1),
        *_offset_values((0xF296, 0xF2F0), OCTICONS_OFFSET_2),
    ))),
    ScaleGroup(_offset_values((0xF09C, 0xF09F, 0xF0DE), OCTICONS_OFFSET_1)),
    ScaleGroup(_offset_range(0xF2C2, 0xF2C5, OCTICONS_OFFSET_2)),
    ScaleGroup(frozenset((
        *_offset_values((0xF07B, 0xF0A1, 0xF0D6), OCTICONS_OFFSET_1),
        0xF306 + OCTICONS_OFFSET_2,
    ))),
    ScaleGroup(_offset_values((0xF03C, 0xF042, 0xF045), WEATHER_OFFSET)),
    ScaleGroup(_offset_values((
        0xF043,
        0xF044,
        0xF048,
        0xF04B,
        0xF04C,
        0xF04D,
        0xF057,
        0xF058,
        0xF087,
        0xF088,
    ), WEATHER_OFFSET)),
    ScaleGroup(_offset_range(0xF053, 0xF055, WEATHER_OFFSET)),
    ScaleGroup(frozenset((
        *_offset_range(0xF059, 0xF061, WEATHER_OFFSET),
        0xF0B1 + WEATHER_OFFSET,
    ))),
    ScaleGroup(_offset_range(0xF089, 0xF094, WEATHER_OFFSET)),
    ScaleGroup(_offset_range(0xF095, 0xF0B0, WEATHER_OFFSET)),
    ScaleGroup(_offset_range(0xF0B7, 0xF0C3, WEATHER_OFFSET)),
    ScaleGroup(_offset_values((0xF06E, 0xF070), WEATHER_OFFSET)),
    ScaleGroup(_offset_values((0xF051, 0xF052, 0xF0C9, 0xF0CA, 0xF072), WEATHER_OFFSET)),
    ScaleGroup(frozenset((
        *_offset_values((0xF049, 0xF056, 0xF071, 0xF08A), WEATHER_OFFSET),
        *_offset_range(0xF073, 0xF07C, WEATHER_OFFSET),
    ))),
    ScaleGroup(frozenset((
        *_offset_range(0xF000, 0xF041, WEATHER_OFFSET),
        *_offset_range(0xF064, 0xF06D, WEATHER_OFFSET),
        *_offset_range(0xF07D, 0xF083, WEATHER_OFFSET),
        *_offset_range(0xF085, 0xF086, WEATHER_OFFSET),
        *_offset_range(0xF0B2, 0xF0B6, WEATHER_OFFSET),
    ))),
)


def _attributes_for(codepoint: int) -> SymbolAttributes:
    if codepoint in BRAILLE_SET:
        return SymbolAttributes("", "", "")
    if codepoint in HEAVY_ANGLE_SET:
        return SymbolAttributes("c", "c", "^pa1!", ypadding=0.3)
    if codepoint in BOX_DRAWING_SET:
        return SymbolAttributes("c", "c", "^xy", overlap=0.02)
    if codepoint in PROGRESS_ATTRIBUTES:
        return PROGRESS_ATTRIBUTES[codepoint]
    if codepoint in PROGRESS_SET:
        return SymbolAttributes("c", "c", "^pa1!", overlap=-0.03)
    if codepoint in POWERLINE_ATTRIBUTES:
        return POWERLINE_ATTRIBUTES[codepoint]
    if codepoint in POWERLINE_SET:
        return SymbolAttributes("c", "c", "^pa")
    if codepoint in {0xF0DC, 0xF0DD, 0xF0DE}:
        return SymbolAttributes("c", "", "pa")
    return SymbolAttributes()


def _effective_attributes_for(codepoint: int, font_extrawide: bool) -> SymbolAttributes:
    attr = _attributes_for(codepoint)
    if font_extrawide and "2" in attr.stretch:
        return replace(attr, stretch=attr.stretch.replace("2", ""))  # type: ignore[arg-type]
    return attr


def _should_merge_codepoint(
    codepoint: int,
    original_base_codepoints: frozenset[int],
    mono: bool,
    box_enabled: bool,
    braille_enabled: bool,
) -> bool:
    if codepoint in CAREFUL_SET and codepoint in original_base_codepoints:
        return False
    if codepoint in BOX_DRAWING_SET:
        return box_enabled
    if codepoint in BRAILLE_SET:
        return braille_enabled
    return codepoint in UNCONDITIONAL_SET


def _glyph_dimensions(tables: FontTables, glyph_name: str) -> GlyphDimensions | None:
    bbox = _get_glyph_bbox(tables.glyf, glyph_name)
    if bbox is None:
        return None
    xmin, ymin, xmax, ymax = bbox
    advance = None
    if glyph_name in tables.hmtx.metrics:
        advance = float(tables.hmtx.metrics[glyph_name][0])
    return GlyphDimensions(
        xmin=float(xmin),
        ymin=float(ymin),
        xmax=float(xmax),
        ymax=float(ymax),
        width=float(xmax - xmin),
        height=float(ymax - ymin),
        advance=advance,
    )


def _combined_dimensions(
    tables: FontTables,
    codepoints: Iterable[int],
    cmap: dict[int, str],
) -> GlyphDimensions | None:
    boxes: list[tuple[float, float, float, float]] = []
    advances: set[int] = set()
    for codepoint in codepoints:
        glyph_name = cmap.get(codepoint)
        if not glyph_name:
            continue
        dim = _glyph_dimensions(tables, glyph_name)
        if dim is None:
            continue
        boxes.append((dim.xmin, dim.ymin, dim.xmax, dim.ymax))
        if dim.advance is not None:
            advances.add(int(dim.advance))

    if not boxes:
        return None

    xmin = min(box[0] for box in boxes)
    ymin = min(box[1] for box in boxes)
    xmax = max(box[2] for box in boxes)
    ymax = max(box[3] for box in boxes)
    shared_advance = None
    if len(advances) == 1:
        shared_advance = float(next(iter(advances)))

    return GlyphDimensions(
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        width=float(xmax - xmin),
        height=float(ymax - ymin),
        advance=shared_advance,
    )


def _target_width_cells(stretch: str, mono: bool) -> int:
    if mono or ("pa" not in stretch and "2" not in stretch) or "1" in stretch:
        return 1
    return 2


def _scale_factors(
    dim: GlyphDimensions,
    attr: SymbolAttributes,
    mono: bool,
    cell_width: float,
    line_height: float,
    icon_height: float,
    em: int,
) -> tuple[float, float]:
    if dim.width <= 0 or dim.height <= 0:
        return (1.0, 1.0)
    glyph_width = max(dim.width, 1.0)
    glyph_height = max(dim.height, 1.0)

    target_width = cell_width * _target_width_cells(attr.stretch, mono)
    if attr.overlap:
        target_width += cell_width * attr.overlap
    target_height = line_height if "^" in attr.stretch else icon_height
    target_height *= 1.0 - attr.ypadding
    if attr.overlap:
        target_height *= 1.0 + min(MAX_VERTICAL_OVERLAP, attr.overlap)

    scale_x = target_width / glyph_width
    scale_y = target_height / glyph_height
    if "pa" in attr.stretch:
        scale_x = min(scale_x, scale_y)
        if not mono and "!" not in attr.stretch and not attr.overlap:
            scale_x = min(scale_x, 1.0)
        scale_y = scale_x
    else:
        if "x" not in attr.stretch:
            scale_x = 1.0
        if "y" not in attr.stretch:
            scale_y = 1.0

    if attr.xy_ratio:
        xy_ratio = glyph_width * scale_x / (glyph_height * scale_y)
        if xy_ratio > attr.xy_ratio:
            scale_x *= attr.xy_ratio / xy_ratio

    if scale_x != 1.0 or scale_y != 1.0:
        # Match font-patcher's tiny X-axis shrink to avoid rounded outlines
        # spilling past cell bounds after integer coordinate conversion.
        scale_x *= em / (em + 1)
    return (scale_x, scale_y)


def _center_shifts(
    dim: GlyphDimensions,
    attr: SymbolAttributes,
    mono: bool,
    cell_width: float,
    target_advance: int,
    cell_center_y: float,
) -> tuple[int, int]:
    shift_y = 0
    if attr.valign == "c":
        shift_y = int(round(cell_center_y - ((dim.ymin + dim.ymax) / 2.0)))

    shift_x = 0
    if attr.align:
        shift_x = -dim.xmin
        align_width = (
            dim.advance
            if not mono and "pa" in attr.stretch and dim.advance is not None
            else cell_width
        )
        if attr.align == "c":
            shift_x += int(round((align_width - dim.width) / 2.0))
        elif attr.align == "r":
            shift_x += int(round(cell_width * _target_width_cells(attr.stretch, mono) - dim.width))
        if not attr.overlap:
            shift_x = max(int(round(-dim.xmin)), shift_x)

    if attr.overlap:
        overlap_width = cell_width * attr.overlap
        if attr.align == "l":
            shift_x -= int(round(overlap_width))
        elif attr.align == "r":
            target_xmax = cell_width * _target_width_cells(attr.stretch, mono) + overlap_width
            correction = target_xmax - (dim.xmax + shift_x)
            shift_x += int(round(correction))

    return (shift_x, shift_y)


def merge_nerd_font(
    base_font: TTFont,
    symbol_font: TTFont,
    mono: bool = True,
    copy_hints: bool = True,
) -> None:
    """Merge Nerd Font symbols using upstream font-patcher scale rules."""
    if copy_hints:
        copy_hinting_tables(symbol_font, base_font)

    base_cmap = base_font.getBestCmap()
    symbol_cmap = symbol_font.getBestCmap()
    original_base_codepoints = frozenset(base_cmap)
    box_enabled = mono and not BOX_DRAWING_SET.issubset(original_base_codepoints)
    braille_enabled = mono and not BRAILLE_SET.issubset(original_base_codepoints)
    merge_cmap = {
        codepoint: glyph_name
        for codepoint, glyph_name in symbol_cmap.items()
        if _should_merge_codepoint(
            codepoint,
            original_base_codepoints,
            mono,
            box_enabled,
            braille_enabled,
        )
    }
    base_tables = FontTables.from_font(base_font)
    sym_tables = FontTables(
        glyf=symbol_font["glyf"],
        hmtx=symbol_font["hmtx"],
        vmtx=symbol_font["vmtx"] if "vmtx" in symbol_font and "vmtx" in base_font else None,
    )

    base_os2 = base_font["OS/2"]
    line_height = float(base_os2.sTypoAscender - base_os2.sTypoDescender)
    cap_height = float(
        base_os2.sCapHeight
        if hasattr(base_os2, "sCapHeight") and base_os2.sCapHeight > 0
        else int(line_height)
    )
    icon_height = (cap_height * 2 + line_height) / 3.0 if mono else line_height
    cell_width = float(get_typical_advance(base_font, ord("A")))
    cell_center_y = (base_os2.sTypoAscender + base_os2.sTypoDescender) / 2.0
    upm_scale = base_font["head"].unitsPerEm / float(symbol_font["head"].unitsPerEm)
    font_extrawide = line_height * 1.8 < cell_width * 2

    for codepoint, sym_glyph_name in merge_cmap.items():
        for dep_name in get_glyph_dependencies(sym_glyph_name, sym_tables.glyf):
            if dep_name not in base_tables.glyf:
                copy_glyph_into(
                    sym_tables,
                    base_tables,
                    dep_name,
                    dep_name,
                    base_font,
                    scale_x=upm_scale,
                    scale_y=upm_scale,
                    copy_hints=copy_hints,
                )

    for codepoint, sym_glyph_name in merge_cmap.items():
        for dep_name in get_glyph_dependencies(sym_glyph_name, sym_tables.glyf):
            if dep_name in base_tables.glyf:
                glyph = base_tables.glyf[dep_name]
                if hasattr(glyph, "recalcBounds"):
                    glyph.recalcBounds(base_tables.glyf)

    group_data: dict[int, tuple[float, GlyphDimensions | None]] = {}
    for group in SCALE_GROUPS:
        dim = _combined_dimensions(sym_tables, group.codepoints, symbol_cmap)
        if dim is None:
            continue
        dim = dim.scaled(upm_scale, upm_scale)
        sample_cp = next((cp for cp in group.codepoints if cp in merge_cmap), None)
        if sample_cp is None:
            continue
        attr = _effective_attributes_for(sample_cp, font_extrawide)
        scale = _scale_factors(
            dim,
            attr,
            mono,
            cell_width,
            line_height,
            icon_height,
            base_font["head"].unitsPerEm,
        )[0]
        shared_dim = dim if group.shift_mode else None
        for codepoint in group.codepoints:
            if codepoint not in group_data:
                group_data[codepoint] = (scale, shared_dim)

    for codepoint, sym_glyph_name in merge_cmap.items():
        base_cmap[codepoint] = sym_glyph_name
        if sym_glyph_name not in base_tables.glyf:
            continue

        attr = _effective_attributes_for(codepoint, font_extrawide)
        if codepoint in BRAILLE_SET:
            continue

        glyph_dim = _glyph_dimensions(base_tables, sym_glyph_name)
        if glyph_dim is None:
            continue

        shared_scale = group_data.get(codepoint)
        if shared_scale:
            scale_x = scale_y = shared_scale[0]
            align_dim = shared_scale[1] or glyph_dim
        else:
            scale_x, scale_y = _scale_factors(
                glyph_dim,
                attr,
                mono,
                cell_width,
                line_height,
                icon_height,
                base_font["head"].unitsPerEm,
            )
            align_dim = glyph_dim

        glyph = base_tables.glyf[sym_glyph_name]
        GlyphTransformer.scale(glyph, scale_x, scale_y)

        scaled_align_dim = align_dim.scaled(scale_x, scale_y)
        shift_x, shift_y = _center_shifts(
            scaled_align_dim,
            attr,
            mono,
            cell_width,
            int(round(cell_width * _target_width_cells(attr.stretch, mono))),
            cell_center_y,
        )

        if shift_x:
            GlyphTransformer.shift_horizontal(glyph, shift_x)
        if shift_y:
            GlyphTransformer.shift_vertical(glyph, shift_y)

        if sym_glyph_name in base_tables.hmtx.metrics:
            old_adv, old_lsb = base_tables.hmtx.metrics[sym_glyph_name]
            if mono:
                target_advance = int(round(cell_width))
            elif scaled_align_dim.advance is not None:
                target_advance = int(round(scaled_align_dim.advance))
            else:
                target_advance = int(round(scaled_align_dim.width))
            if not mono and attr.overlap:
                target_advance -= int(round(cell_width * attr.overlap))
            base_tables.hmtx.metrics[sym_glyph_name] = (
                target_advance,
                int(round(old_lsb * scale_x)) + shift_x,
            )
