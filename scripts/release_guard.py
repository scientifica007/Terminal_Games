#!/usr/bin/env python3
"""Validate Terminal_Games product versions before release publication."""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path


STABLE_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = PROJECT_ROOT / "terminal_games" / "__init__.py"


def read_product_version(path: Path = VERSION_FILE) -> str:
    """Read __version__ from terminal_games/__init__.py without importing it."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, str) or not value:
            raise ValueError("__version__ must be a non-empty string")
        return value
    raise ValueError(f"No __version__ assignment found in {path}")


def validate_release_tag(tag: str, version: str) -> None:
    """Require an exact vMAJOR.MINOR.PATCH tag matching a stable product version."""
    if not STABLE_VERSION_RE.fullmatch(version):
        raise ValueError(
            f"Product version {version!r} is not a stable MAJOR.MINOR.PATCH version; "
            "development or pre-release versions cannot be published."
        )

    expected_tag = f"v{version}"
    if tag != expected_tag:
        raise ValueError(f"Release tag {tag!r} does not match product version; expected {expected_tag!r}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        help="Git tag to validate for an actual release. Omit for a non-publishing build check.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    version = read_product_version()

    if args.tag:
        validate_release_tag(args.tag, version)
        print(f"Release guard passed: {args.tag} matches stable product version {version}.")
    else:
        print(f"Build check only: product version is {version}; no release tag was supplied.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
