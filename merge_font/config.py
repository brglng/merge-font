"""TOML configuration loader for the font-merging pipeline.

Reads a TOML file whose top-level keys supply the **common/default** settings
shared across every font family.  Each ``[[families]]`` section may override
any of those defaults.  Subfamily-specific settings live under
``[[families.subfamilies]]``.

Example structure
-----------------
::

    author  = "Alice"
    description = ""
    mark_as_monospace = true
    remove_hints = true
    adjust_baseline = true
    symbol_fonts = ["~/Library/Fonts/SymbolsNerdFont-Regular.ttf"]

    [[double_width]]
    chars    = ["…", "—"]
    strategy = "stretch"

    [[double_width]]
    chars    = ["'", "\u201c"]
    strategy = "pad_left"

    [[double_width]]
    chars    = ["'", "\u201d"]
    strategy = "pad_right"

    [[families]]
    name = "My Family"

    [[families.subfamilies]]
    name         = "Regular"
    western_font = "~/Library/Fonts/MyFont-Regular.ttf"
    cjk_font     = "~/Library/Fonts/NotoSansCJK-Regular.ttf"
    cjk_scale    = 1.15
"""
import os

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        raise ImportError("Python 3.11+ or the 'tomli' package is required.")

from merge_font.types import DoubleWidthConfig, DoubleWidthStrategy, FontFamilySpec, SubfamilySpec


# Keys that are considered "common" and can appear at the top level as well
# as inside individual ``[families.<name>]`` sections.
_COMMON_KEYS = frozenset({
    "author",
    "description",
    "mark_as_monospace",
    "remove_hints",
    "adjust_baseline",
    "double_width",
    "symbol_fonts",
})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_chars(raw: list) -> list[str | int | tuple[int, int]]:
    """Convert a raw TOML list to the internal ``chars`` format.

    Accepted TOML element types:

    * ``str`` — a single Unicode character (e.g. ``"…"``)
    * ``int`` — a codepoint (e.g. ``8230``)
    * ``[int, int]`` — an inclusive (start, end) codepoint range
    """
    result: list[str | int | tuple[int, int]] = []
    for item in raw:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, int):
            result.append(item)
        elif isinstance(item, list) and len(item) == 2:  # [start, end] range
            result.append((int(item[0]), int(item[1])))
    return result


def _parse_double_width(raw: list[dict]) -> list[DoubleWidthConfig]:
    """Convert a list of raw TOML double-width dicts to :class:`DoubleWidthConfig` objects."""
    return [
        DoubleWidthConfig(
            chars=_parse_chars(entry["chars"]),
            strategy=DoubleWidthStrategy(entry["strategy"]),
        )
        for entry in raw
    ]


def _expand_paths(paths: list[str]) -> list[str]:
    """Expand ``~`` and environment variables in a list of path strings."""
    return [os.path.expandvars(os.path.expanduser(p)) for p in paths]


def _extract_common(data: dict) -> dict:
    """Pull every recognised common key out of *data* and return them as a dict."""
    return {key: data[key] for key in _COMMON_KEYS if key in data}


def _build_family_spec(merged: dict) -> FontFamilySpec:
    """Construct a :class:`FontFamilySpec` from a fully-merged settings dict."""
    subfamilies: dict[str, SubfamilySpec] = {
        spec["name"]: SubfamilySpec(
            western_font=os.path.expandvars(os.path.expanduser(spec["western_font"])),
            cjk_font=os.path.expandvars(os.path.expanduser(spec["cjk_font"])),
            cjk_scale=float(spec.get("cjk_scale", 1.0)),
            western_scale_x=float(spec.get("western_scale_x", 1.0)),
            western_scale_y=float(spec.get("western_scale_y", 1.0)),
        )
        for spec in merged.get("subfamilies", [])
    }

    return FontFamilySpec(
        author=merged["author"],
        description=merged.get("description", ""),
        mark_as_monospace=bool(merged.get("mark_as_monospace", True)),
        adjust_baseline=bool(merged.get("adjust_baseline", True)),
        double_width=_parse_double_width(merged.get("double_width", [])),
        symbol_fonts=_expand_paths(merged.get("symbol_fonts", [])),
        remove_hints=bool(merged.get("remove_hints", False)),
        subfamilies=subfamilies,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_families(path: str) -> dict[str, FontFamilySpec]:
    """Load font family configurations from a TOML file.

    Parameters
    ----------
    path:
        Filesystem path to the ``.toml`` configuration file.

    Returns
    -------
    dict[str, FontFamilySpec]
        Ordered mapping of family name → :class:`FontFamilySpec`, with
        common defaults merged in and family-level overrides applied.

    Raises
    ------
    FileNotFoundError
        When *path* does not exist.
    KeyError
        When a required key (e.g. ``author``) is missing from both the
        common defaults and a specific family section.
    """
    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    common = _extract_common(data)
    families_raw: list[dict] = data.get("families", [])

    families: dict[str, FontFamilySpec] = {}
    for family_data in families_raw:
        family_name: str = family_data["name"]
        # Family-level keys (excluding "name" and "subfamilies") override the
        # common defaults; subfamily specs are passed through unmodified.
        overrides = {k: v for k, v in family_data.items() if k not in ("name", "subfamilies")}
        merged: dict = {**common, **overrides}
        merged["subfamilies"] = family_data.get("subfamilies", [])
        families[family_name] = _build_family_spec(merged)

    return families
