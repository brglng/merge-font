"""Nerd Font symbol merging – independent module.

Implements per-glyph / per-group scaling strategies aligned with the upstream
Nerd Fonts font-patcher 3.4.0 / script 4.22.1:
  https://github.com/ryanoasis/nerd-fonts/blob/1514941a80397d93361f4193346d9cbb9ed21c6e/font-patcher

Key algorithms ported from fontforge to fontTools/TTFont:
  - SYM_ATTR_* per-glyph attribute tables (align, valign, stretch, params)
  - *_SCALE_LIST ScaleGroups with combined bounding-box scaling
  - get_scale_factors  ('^', 'pa', 'xy', '1', '2', '!', overlap, ypadding)
  - xy-ratio limit
  - Horizontal l/c/r and vertical c alignment
  - Careful (skip existing glyphs) and dont_copy semantics
  - Mono (single-width) vs non-mono (proportional) target advance
"""
from __future__ import annotations

from typing import Any

from fontTools.ttLib import TTFont


# ---------------------------------------------------------------------------
# Attribute Tables  (font-patcher SYM_ATTR_* / setup_patch_set ~line 1080)
# ---------------------------------------------------------------------------
# Each dict maps int codepoint → {'align', 'valign', 'stretch', 'params'}.
# 'default' is the fallback for codepoints not explicitly listed.
#
# stretch flags:
#   'pa'  – preserve aspect ratio
#   'xy'  – stretch independently in x and y
#   '^'   – use full line height (not icon height)
#   '1'   – force 1-cell advance
#   '2'   – force 2-cell advance (xy-mode, non-mono)
#   '!'   – scale up even for non-mono fonts
# params keys: overlap, xy-ratio, ypadding, careful, dont_copy

SYM_ATTR_DEFAULT: dict = {
    'default': {'align': 'c', 'valign': 'c', 'stretch': 'pa', 'params': {}}
}

SYM_ATTR_POWERLINE: dict = {
    'default': {'align': 'c', 'valign': 'c', 'stretch': '^pa', 'params': {}},

    # Arrow tips
    0xe0b0: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.06, 'xy-ratio': 0.7}},
    0xe0b1: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'xy-ratio': 0.7}},
    0xe0b2: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.06, 'xy-ratio': 0.7}},
    0xe0b3: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'xy-ratio': 0.7}},

    # Inverse arrow tips
    0xe0d6: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05, 'xy-ratio': 0.7}},
    0xe0d7: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05, 'xy-ratio': 0.7}},

    # Rounded arcs
    0xe0b4: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.06, 'xy-ratio': 0.59}},
    0xe0b5: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'xy-ratio': 0.5}},
    0xe0b6: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.06, 'xy-ratio': 0.59}},
    0xe0b7: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'xy-ratio': 0.5}},

    # Bottom Triangles
    0xe0b8: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05}},
    0xe0b9: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {}},
    0xe0ba: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05}},
    0xe0bb: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {}},

    # Top Triangles
    0xe0bc: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05}},
    0xe0bd: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {}},
    0xe0be: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05}},
    0xe0bf: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {}},

    # Flames
    0xe0c0: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': 0.05}},
    0xe0c1: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {}},
    0xe0c2: {'align': 'r', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': 0.05}},
    0xe0c3: {'align': 'r', 'valign': 'c', 'stretch': '^xy2', 'params': {}},

    # Small squares
    0xe0c4: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': -0.03, 'xy-ratio': 0.86}},
    0xe0c5: {'align': 'r', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': -0.03, 'xy-ratio': 0.86}},

    # Bigger squares
    0xe0c6: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': -0.03, 'xy-ratio': 0.78}},
    0xe0c7: {'align': 'r', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': -0.03, 'xy-ratio': 0.78}},

    # Waveform
    0xe0c8: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': 0.05}},
    0xe0ca: {'align': 'r', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': 0.05}},

    # Hexagons
    0xe0cc: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {'overlap': 0.02, 'xy-ratio': 0.85}},
    0xe0cd: {'align': 'l', 'valign': 'c', 'stretch': '^xy2', 'params': {'xy-ratio': 0.865}},

    # Legos
    0xe0ce: {'align': 'l', 'valign': 'c', 'stretch': '^pa', 'params': {}},
    0xe0cf: {'align': 'c', 'valign': 'c', 'stretch': '^pa', 'params': {}},
    0xe0d0: {'align': 'l', 'valign': 'c', 'stretch': '^pa', 'params': {}},
    0xe0d1: {'align': 'l', 'valign': 'c', 'stretch': '^pa', 'params': {}},

    # Top and bottom trapezoid
    0xe0d2: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.02, 'xy-ratio': 0.7}},
    0xe0d4: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.02, 'xy-ratio': 0.7}},
}

SYM_ATTR_TRIGRAPH: dict = {
    'default': {'align': 'c', 'valign': 'c', 'stretch': 'pa1!',
                'params': {'overlap': -0.10, 'careful': True}}
}

SYM_ATTR_BRAILLE: dict = {
    # No scaling; glyphs are already generated at the correct size.
    'default': {'align': '', 'valign': '', 'stretch': '', 'params': {'careful': False}}
}

SYM_ATTR_HEAVYBRACKETS: dict = {
    'default': {'align': 'c', 'valign': 'c', 'stretch': '^pa1!',
                'params': {'ypadding': 0.3, 'careful': True}}
}

SYM_ATTR_BOX: dict = {
    'default': {'align': 'c', 'valign': 'c', 'stretch': '^xy',
                'params': {'overlap': 0.02}},
}

SYM_ATTR_PROGRESS: dict = {
    # Circles (default)
    'default': {'align': 'c', 'valign': 'c', 'stretch': '^pa1!',
                'params': {'overlap': -0.03, 'careful': True}},
    # Squares
    0xee00: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05, 'careful': True}},
    0xee01: {'align': 'c', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.10, 'careful': True}},
    0xee02: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05, 'careful': True}},
    0xee03: {'align': 'r', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05, 'careful': True}},
    0xee04: {'align': 'c', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.10, 'careful': True}},
    0xee05: {'align': 'l', 'valign': 'c', 'stretch': '^xy', 'params': {'overlap': 0.05, 'careful': True}},
}


# ---------------------------------------------------------------------------
# Scale Rule Lists  (font-patcher *_SCALE_LIST, setup_patch_set ~line 1170)
# ---------------------------------------------------------------------------
# ScaleGroups: each sub-list / range is one group whose glyphs share a combined
# bounding box for uniform scaling and alignment.  ShiftMode 'xy' means the
# combined BB also governs horizontal alignment (monospaced symbol source).

HEAVY_SCALE_LIST: dict = {
    'ShiftMode': 'xy',
    'ScaleGroups': [range(0x276c, 0x2771 + 1)],
}

BOX_SCALE_LIST: dict = {
    'ShiftMode': 'xy',
    'ScaleGroups': [
        [*range(0x2500, 0x2570 + 1), *range(0x2574, 0x257f + 1)],  # box drawing
        range(0x2571, 0x2573 + 1),   # diagonals
        range(0x2580, 0x259f + 1),   # blocks / greys
    ],
}

PROGR_SCALE_LIST: dict = {
    'ShiftMode': 'xy',
    'ScaleGroups': [
        range(0xedff, 0xee05 + 1),   # boxes + helper glyph 0xEDFF for Y padding
        range(0xee06, 0xee0b + 1),   # circles
    ],
}


# ---------------------------------------------------------------------------
# Patch-rule table  (priority-ordered; first match wins)
# ---------------------------------------------------------------------------

_POWERLINE_CODEPOINTS: set[int] = set()
for _s, _e in [
    (0xE0A0, 0xE0A2), (0xE0B0, 0xE0B3),
    (0xE0A3, 0xE0A3), (0xE0B4, 0xE0C8),
    (0xE0CA, 0xE0CA), (0xE0CC, 0xE0D7),
]:
    _POWERLINE_CODEPOINTS.update(range(_s, _e + 1))

# (codepoint_set_or_None, attributes_dict, scale_rules_or_None)
# None codepoint_set = catch-all (must be last)
_PATCH_RULES: list[tuple] = [
    (set(range(0x276c, 0x2771 + 1)), SYM_ATTR_HEAVYBRACKETS, HEAVY_SCALE_LIST),
    (set(range(0x2500, 0x259f + 1)), SYM_ATTR_BOX,           BOX_SCALE_LIST),
    (set(range(0xee00, 0xee0b + 1)), SYM_ATTR_PROGRESS,      PROGR_SCALE_LIST),
    (_POWERLINE_CODEPOINTS,          SYM_ATTR_POWERLINE,      None),
    ({0x2630},                       SYM_ATTR_TRIGRAPH,       None),
    (set(range(0x2800, 0x28ff + 1)), SYM_ATTR_BRAILLE,        None),
    (None,                           SYM_ATTR_DEFAULT,         None),   # catch-all
]


# ---------------------------------------------------------------------------
# Core algorithm helpers
# ---------------------------------------------------------------------------


def _get_glyph_bbox(
    glyf_table: Any, glyph_name: str
) -> tuple[float, float, float, float] | None:
    """Return (xMin, yMin, xMax, yMax) for *glyph_name*, or None if empty."""
    if glyph_name not in glyf_table:
        return None
    g = glyf_table[glyph_name]
    if not hasattr(g, "xMin") or g.xMin is None:
        return None
    if g.numberOfContours == 0:
        return None
    return (float(g.xMin), float(g.yMin), float(g.xMax), float(g.yMax))


def _get_multiglyph_bbox(
    glyf_table: Any,
    hmtx: Any,
    glyph_names: list[str],
) -> dict | None:
    """Return combined bbox dict for a list of glyph names.

    Mirrors font-patcher ``get_multiglyph_boundingBox()``:
    - Empty glyphs are skipped when the list has > 1 entry.
    - ``advance`` is the common advance width when 2+ glyphs share the same
      advance; otherwise ``None`` (non-mono).
    """
    xmin = ymin = None
    xmax = ymax = None
    advance_state: float | None = None   # None=unseen, negative=single, positive=confirmed
    valid = 0
    multiple = len(glyph_names) > 1

    for gname in glyph_names:
        if gname not in glyf_table:
            continue
        g = glyf_table[gname]
        if not hasattr(g, "xMin") or g.xMin is None:
            continue
        # Skip empty glyphs when checking a group
        if multiple and g.xMin == g.xMax and g.yMin == g.yMax:
            continue

        gxmin, gymin, gxmax, gymax = float(g.xMin), float(g.yMin), float(g.xMax), float(g.yMax)
        xmin = gxmin if xmin is None else min(xmin, gxmin)
        ymin = gymin if ymin is None else min(ymin, gymin)
        xmax = gxmax if xmax is None else max(xmax, gxmax)
        ymax = gymax if ymax is None else max(ymax, gymax)

        gadv = float(hmtx.metrics.get(gname, (0, 0))[0])
        if advance_state is None:
            advance_state = -gadv          # first glyph: store negative
        elif advance_state < 0:
            advance_state = gadv if abs(advance_state) == gadv else -1.0
        elif advance_state > 0:
            if advance_state != gadv:
                advance_state = -1.0       # different advances

        valid += 1

    if valid == 0 or xmin is None:
        return None

    # advance > 0 means 2+ glyphs with identical advance (monospaced group)
    advance = advance_state if (advance_state is not None and advance_state > 0) else None
    return {
        "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
        "width": xmax - xmin, "height": ymax - ymin,
        "advance": advance,
    }


def _scale_bbox(bbox: dict, scale_x: float, scale_y: float) -> dict:
    """Return a new bbox dict scaled by (*scale_x*, *scale_y*)."""
    xmin = round(bbox["xmin"] * scale_x)
    ymin = round(bbox["ymin"] * scale_y)
    xmax = round(bbox["xmax"] * scale_x)
    ymax = round(bbox["ymax"] * scale_y)
    adv  = round(bbox["advance"] * scale_x) if bbox["advance"] is not None else None
    return {
        "xmin": float(xmin), "ymin": float(ymin),
        "xmax": float(xmax), "ymax": float(ymax),
        "width": float(xmax - xmin), "height": float(ymax - ymin),
        "advance": float(adv) if adv is not None else None,
    }


def _get_target_width(stretch: str, mono: bool) -> int:
    """Return 1 or 2 cells for the given stretch mode and mono flag.

    Mirrors font-patcher ``get_target_width()``.
    """
    if mono or ("pa" not in stretch and "2" not in stretch) or "1" in stretch:
        return 1
    return 2


def _get_scale_factors(
    sym_dim: dict,
    stretch: str,
    font_dim: dict,
    mono: bool,
    overlap: float | None = None,
    ypadding: float = 0.0,
) -> tuple[float, float]:
    """Compute (scale_x, scale_y) matching font-patcher ``get_scale_factors()``.

    Parameters
    ----------
    sym_dim:
        Glyph (or combined-group) bounding-box dict with keys
        ``width``, ``height``.
    stretch:
        Stretch mode string (e.g. ``'pa'``, ``'^xy'``, ``'^pa1!'``).
    font_dim:
        Font cell dimensions dict (``width``, ``height``, ``iconheight``).
    mono:
        ``True`` for Nerd Font Mono / single-width (``--single``).
    overlap:
        Fractional overlap; added to the target width and (minimally) height.
    ypadding:
        Fraction of cell height to subtract from the target height (0–1).
    """
    w = sym_dim["width"]
    h = sym_dim["height"]
    if not w or not h:
        return (1.0, 1.0)

    target_width = font_dim["width"] * _get_target_width(stretch, mono)
    if overlap:
        target_width += font_dim["width"] * overlap
    sx = target_width / w

    target_height = font_dim["height"] if "^" in stretch else font_dim["iconheight"]
    target_height *= 1.0 - ypadding
    if overlap:
        target_height *= 1.0 + min(0.01, overlap)   # never aggressive vertical overlap
    sy = target_height / h

    if "pa" in stretch:
        sx = min(sx, sy)
        if not mono and "!" not in stretch and not overlap:
            sx = min(sx, 1.0)   # non-mono: never scale up without '!'
        sy = sx
    else:
        if "x" not in stretch:
            sx = 1.0
        if "y" not in stretch:
            sy = 1.0

    return (sx, sy)


def _find_rule(codepoint: int) -> tuple[dict, dict | None]:
    """Return (attributes_dict, scale_rules_or_None) for *codepoint*."""
    for codepoints, attrs, rules in _PATCH_RULES:
        if codepoints is None or codepoint in codepoints:
            return attrs, rules
    return SYM_ATTR_DEFAULT, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_nerd_font(
    base_font: TTFont,
    symbol_font: TTFont,
    mono: bool = True,
    copy_hints: bool = True,
) -> None:
    """Merge Nerd Font symbols into *base_font* using the official patcher rules.

    Scaling strategy is aligned with Nerd Fonts font-patcher 3.4.0 / script 4.22.1:
    https://github.com/ryanoasis/nerd-fonts/blob/1514941a80397d93361f4193346d9cbb9ed21c6e/font-patcher

    Parameters
    ----------
    base_font:
        Destination font (western / Latin).  Modified in place.
    symbol_font:
        Source Nerd Font symbols font (e.g. SymbolsNerdFont-Regular.ttf).
        Read-only.
    mono:
        When ``True`` (Nerd Font Mono / ``nerd_font_mono = true``):
        icon height is capped at ``(capHeight * 2 + lineHeight) / 3`` and
        every glyph is forced to a single cell advance width.
        When ``False`` (Nerd Font non-mono): icons use full line height; 'pa'
        glyphs may span two cells.
    copy_hints:
        When ``True``, copy global hinting tables (``fpgm``, ``prep``,
        ``cvt ``) from *symbol_font* into *base_font* if absent.
    """
    # Deferred import avoids a circular-import error (merge_nerd_font is
    # imported by merge_font/__init__.py after these utilities are defined).
    from merge_font import (
        GlyphTransformer,
        FontTables,
        copy_glyph_into,
        get_glyph_dependencies,
        get_typical_advance,
        copy_hinting_tables,
    )

    if copy_hints:
        copy_hinting_tables(symbol_font, base_font)

    # Snapshot codepoints that already exist in the base font BEFORE merging
    # (used by the 'careful' flag to skip existing glyphs).
    original_base_codepoints: set[int] = set(base_font.getBestCmap())

    base_cmap = base_font.getBestCmap()
    symbol_cmap = symbol_font.getBestCmap()
    base_tables = FontTables.from_font(base_font)
    sym_tables = FontTables(
        glyf=symbol_font["glyf"],
        hmtx=symbol_font["hmtx"],
        vmtx=symbol_font["vmtx"] if "vmtx" in symbol_font else None,
    )

    # ── Font cell dimensions ──────────────────────────────────────────────
    # Mirrors font-patcher get_sourcefont_dimensions().
    base_os2 = base_font["OS/2"]
    line_height = float(base_os2.sTypoAscender - base_os2.sTypoDescender)
    cap_height = float(
        base_os2.sCapHeight
        if hasattr(base_os2, "sCapHeight") and base_os2.sCapHeight > 0
        else line_height
    )
    # iconheight: (capHeight*2 + lineHeight)/3 in mono mode (prevents overly
    # tall icons); full lineHeight in non-mono mode.
    icon_height = (cap_height * 2.0 + line_height) / 3.0 if mono else line_height
    cell_width = float(get_typical_advance(base_font, ord("A")))
    font_dim = {
        "width":      cell_width,
        "height":     line_height,
        "iconheight": icon_height,
        "xmin":       0.0,
        "ymin":       float(base_os2.sTypoDescender),
        "ymax":       float(base_os2.sTypoAscender),
    }

    upm_scale = base_font["head"].unitsPerEm / float(symbol_font["head"].unitsPerEm)

    # ── Phase 1: copy every glyph at UPM scale ────────────────────────────
    for codepoint, sym_glyph_name in symbol_cmap.items():
        for dep_name in get_glyph_dependencies(sym_glyph_name, sym_tables.glyf):
            if dep_name not in base_tables.glyf:
                copy_glyph_into(
                    sym_tables, base_tables, dep_name, dep_name, base_font,
                    scale_x=upm_scale, scale_y=upm_scale,
                    copy_hints=copy_hints,
                )

    # Recompute stored bounding boxes so _get_glyph_bbox is accurate.
    for codepoint, sym_glyph_name in symbol_cmap.items():
        for dep_name in get_glyph_dependencies(sym_glyph_name, sym_tables.glyf):
            if dep_name in base_tables.glyf:
                g = base_tables.glyf[dep_name]
                if hasattr(g, "recalcBounds"):
                    g.recalcBounds(base_tables.glyf)

    # ── Phase 2: pre-compute ScaleGroup combined bounding boxes ───────────
    # For each ScaleGroup, derive the combined bbox from the already-copied
    # UPM-normalised glyphs.  Map codepoint → combined_bbox_dict.
    group_bbox_cache: dict[int, dict | None] = {}
    seen_rule_ids: set[int] = set()

    for _, attrs, rules in _PATCH_RULES:
        if rules is None or "ScaleGroups" not in rules:
            continue
        rid = id(rules)
        if rid in seen_rule_ids:
            continue
        seen_rule_ids.add(rid)

        for group in rules["ScaleGroups"]:
            glyph_names: list[str] = []
            group_codepoints: list[int] = []
            for cp in group:
                gname = symbol_cmap.get(cp)
                if gname and gname in base_tables.glyf:
                    glyph_names.append(gname)
                    group_codepoints.append(cp)

            if not glyph_names:
                continue

            combined = _get_multiglyph_bbox(
                base_tables.glyf, base_tables.hmtx, glyph_names
            )
            for cp in group_codepoints:
                group_bbox_cache[cp] = combined

    # ── Phase 3: scale, align, and set advance for each symbol ───────────
    for codepoint, sym_glyph_name in symbol_cmap.items():
        base_cmap[codepoint] = sym_glyph_name

        if sym_glyph_name not in base_tables.glyf:
            continue

        attrs, rules = _find_rule(codepoint)
        sym_attr: dict = attrs.get(codepoint, attrs["default"])

        stretch: str = sym_attr["stretch"]

        # Braille: no additional scaling; advance still needs to be set.
        if not stretch:
            if sym_glyph_name in base_tables.hmtx.metrics:
                adv, lsb = base_tables.hmtx.metrics[sym_glyph_name]
                base_tables.hmtx.metrics[sym_glyph_name] = (
                    int(round(cell_width)), lsb
                )
            continue

        # Careful: skip codepoints already present in the base font.
        careful = sym_attr["params"].get("careful", False)
        if careful and codepoint in original_base_codepoints:
            continue

        # Individual glyph bbox (pre-scaling, UPM-normalised).
        ind_bbox = _get_glyph_bbox(base_tables.glyf, sym_glyph_name)
        if ind_bbox is None:
            # Empty glyph – just fix the advance width.
            if sym_glyph_name in base_tables.hmtx.metrics:
                adv, lsb = base_tables.hmtx.metrics[sym_glyph_name]
                base_tables.hmtx.metrics[sym_glyph_name] = (
                    int(round(cell_width)), lsb
                )
            continue

        i_xmin, i_ymin, i_xmax, i_ymax = ind_bbox
        ind_dim: dict = {
            "xmin": i_xmin, "ymin": i_ymin, "xmax": i_xmax, "ymax": i_ymax,
            "width":  max(float(i_xmax - i_xmin), 1.0),
            "height": max(float(i_ymax - i_ymin), 1.0),
            "advance": (
                float(base_tables.hmtx.metrics[sym_glyph_name][0])
                if sym_glyph_name in base_tables.hmtx.metrics else None
            ),
        }

        # Use combined ScaleGroup bbox when available, else individual bbox.
        group_bbox = group_bbox_cache.get(codepoint)
        sym_dim = group_bbox if (group_bbox is not None) else ind_dim

        overlap  = sym_attr["params"].get("overlap")
        ypadding = float(sym_attr["params"].get("ypadding", 0.0))

        # ── Scale factors ─────────────────────────────────────────────────
        sx, sy = _get_scale_factors(sym_dim, stretch, font_dim, mono, overlap, ypadding)

        # ── xy-ratio limit ────────────────────────────────────────────────
        xy_ratio_max = sym_attr["params"].get("xy-ratio")
        if xy_ratio_max:
            actual_xy = (sym_dim["width"] * sx) / (sym_dim["height"] * sy)
            if actual_xy > xy_ratio_max:
                sx = sx * xy_ratio_max / actual_xy

        # ── Apply scale to glyph outline ──────────────────────────────────
        glyph = base_tables.glyf[sym_glyph_name]
        GlyphTransformer.scale(glyph, sx, sy)

        # ── Alignment dimensions (post-scaling) ───────────────────────────
        if group_bbox is not None:
            align_dim = _scale_bbox(group_bbox, sx, sy)
            if align_dim["advance"] is None:
                # Non-uniform group advances: use individual glyph h-bounds.
                align_dim["xmin"] = i_xmin * sx
                align_dim["xmax"] = i_xmax * sx
                align_dim["width"] = ind_dim["width"] * sx
        else:
            align_dim = {
                "xmin":    i_xmin   * sx,
                "ymin":    i_ymin   * sy,
                "xmax":    i_xmax   * sx,
                "ymax":    i_ymax   * sy,
                "width":   ind_dim["width"]   * sx,
                "height":  ind_dim["height"]  * sy,
                "advance": (ind_dim["advance"] * sx
                            if ind_dim["advance"] is not None else None),
            }

        # ── Vertical alignment ────────────────────────────────────────────
        y_shift = 0.0
        if sym_attr.get("valign") == "c":
            sym_ycenter  = align_dim["ymax"] - align_dim["height"] / 2.0
            font_ycenter = font_dim["ymax"]  - font_dim["height"]  / 2.0
            y_shift = font_ycenter - sym_ycenter

        # ── Horizontal alignment ──────────────────────────────────────────
        x_shift = 0.0
        simple_nonmono = (not mono) and (align_dim["advance"] is None)
        align = sym_attr.get("align", "")

        if simple_nonmono:
            # Non-mono, non-uniform advances: remove left bearing.
            x_shift = -align_dim["xmin"]
        elif align:
            x_shift = font_dim["xmin"] - align_dim["xmin"]
            cell_w = (
                (align_dim["advance"] or align_dim["width"])
                if (not mono and "pa" in stretch)
                else font_dim["width"]
            )
            if align == "c":
                x_shift += (cell_w - align_dim["width"]) / 2.0
            elif align == "r":
                x_shift += cell_w * _get_target_width(stretch, mono) - align_dim["width"]
            if not overlap:
                x_shift = max(font_dim["xmin"] - align_dim["xmin"], x_shift)

        if overlap:
            overlap_width = font_dim["width"] * overlap
            if align == "l":
                x_shift -= overlap_width
            elif align == "c":
                if overlap_width < 0 and simple_nonmono:
                    x_shift -= overlap_width / 2.0
            elif align == "r" and not simple_nonmono:
                target_xmax = (
                    (font_dim["xmin"] + font_dim["width"])
                    * _get_target_width(stretch, mono)
                    + overlap_width
                )
                glyph_xmax = align_dim["xmax"] + x_shift
                x_shift += target_xmax - glyph_xmax

        # ── Apply translation ──────────────────────────────────────────────
        shift_x = int(round(x_shift))
        shift_y = int(round(y_shift))
        if shift_x:
            GlyphTransformer.shift_horizontal(glyph, shift_x)
        if shift_y:
            GlyphTransformer.shift_vertical(glyph, shift_y)

        # ── Set advance width and LSB ──────────────────────────────────────
        if sym_glyph_name in base_tables.hmtx.metrics:
            new_lsb = int(round(i_xmin * sx)) + shift_x
            if not overlap:
                new_lsb = max(0, new_lsb)

            if mono:
                target_advance = int(round(font_dim["width"]))
            else:
                if align_dim["advance"] is not None:
                    target_advance = int(round(align_dim["advance"]))
                else:
                    target_advance = int(round(align_dim["width"]))
                if overlap:
                    target_advance -= int(round(font_dim["width"] * overlap))

            base_tables.hmtx.metrics[sym_glyph_name] = (target_advance, new_lsb)
