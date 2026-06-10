"""Command-line entry point for the ``merge-font`` CLI."""
import argparse

from merge_font import config, process_family


def main() -> None:
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

    families = config.load_families(args.config)
    for family in families:
        process_family(family)


if __name__ == "__main__":
    main()
