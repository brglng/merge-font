"""Entry point for ``python -m merge_font`` and the ``merge-font`` CLI."""
import argparse
from merge_font import load_families, process_family


def main():
    """Parse arguments, load TOML configuration, and run all merging tasks."""
    parser = argparse.ArgumentParser(
        description="Merge western and CJK fonts according to a TOML configuration.",
    )
    parser.add_argument(
        "config",
        metavar="FILE",
        help="Path to the TOML configuration file",
    )
    args = parser.parse_args()

    families = load_families(args.config)
    for family in families:
        process_family(family)
