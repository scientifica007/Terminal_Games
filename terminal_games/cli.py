"""Command-line entry point for the Terminal_Games product."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from terminal_games import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terminal-games",
        description="Launch the Terminal_Games collection.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse product-level options, then delegate to the existing launcher."""
    parser = build_parser()
    parser.parse_args(argv)

    # Keep the product wrapper deliberately thin. Import lazily so commands
    # such as --version do not initialize every game module.
    from launcher import main as launcher_main

    launcher_main()
