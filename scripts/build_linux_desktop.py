"""Build and validate the Linux x86_64 standalone Terminal_Games bundle."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import platform
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "terminal_games" / "__init__.py"
LICENSE_FILE = ROOT / "LICENSE"
BUNDLE_README = ROOT / "packaging" / "linux" / "README.txt"
DEFAULT_BUILD_ROOT = ROOT / "build" / "desktop-linux"
DEFAULT_OUTPUT_DIR = ROOT / "desktop-dist"
SUPPORTED_MACHINES = {"x86_64", "amd64"}


def read_product_version(path: Path = VERSION_FILE) -> str:
    """Read the literal product version without importing the package."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
        raise ValueError("__version__ must be assigned a string literal")
    raise ValueError(f"No __version__ assignment found in {path}")


def validate_target(system_name: str | None = None, machine_name: str | None = None) -> None:
    """Reject accidental builds for an unsupported desktop target."""
    system_name = system_name or platform.system()
    machine_name = machine_name or platform.machine()

    if system_name.lower() != "linux":
        raise RuntimeError(f"Linux desktop build requires Linux, got {system_name!r}")
    if machine_name.lower() not in SUPPORTED_MACHINES:
        raise RuntimeError(
            "Linux desktop build currently supports x86_64 only, "
            f"got {machine_name!r}"
        )


def bundle_name(version: str) -> str:
    if not version:
        raise ValueError("Product version must not be empty")
    return f"terminal-games-{version}-linux-x86_64"


def pyinstaller_command(build_root: Path, root: Path = ROOT) -> list[str]:
    """Return the exact one-file PyInstaller invocation used by CI and local builds."""
    dist_dir = build_root / "pyinstaller-dist"
    work_dir = build_root / "pyinstaller-work"
    spec_dir = build_root / "spec"
    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--name",
        "terminal-games",
        "--paths",
        str(root),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        str(root / "terminal_games" / "__main__.py"),
    ]


def build_executable(build_root: Path = DEFAULT_BUILD_ROOT, root: Path = ROOT) -> Path:
    """Build the self-contained executable and return its path."""
    dist_dir = build_root / "pyinstaller-dist"
    work_dir = build_root / "pyinstaller-work"
    spec_dir = build_root / "spec"

    for directory in (dist_dir, work_dir, spec_dir):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True, exist_ok=True)

    subprocess.run(pyinstaller_command(build_root, root), cwd=root, check=True)

    binary = dist_dir / "terminal-games"
    if not binary.is_file():
        raise RuntimeError(f"PyInstaller did not create expected executable: {binary}")
    binary.chmod(0o755)
    return binary


def validate_executable(binary: Path, version: str) -> None:
    """Validate the frozen CLI and launcher before packaging it."""
    version_result = subprocess.run(
        [str(binary), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expected = f"terminal-games {version}"
    actual = version_result.stdout.strip()
    if actual != expected:
        raise RuntimeError(f"Frozen version mismatch: expected {expected!r}, got {actual!r}")

    launcher_result = subprocess.run(
        [str(binary)],
        input="q\n",
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if "=== Terminal Games ===" not in launcher_result.stdout:
        raise RuntimeError("Frozen launcher did not render the game menu")
    if "Goodbye." not in launcher_result.stdout:
        raise RuntimeError("Frozen launcher did not complete the quit smoke test")


def _normalize_tarinfo(info: tarfile.TarInfo) -> tarfile.TarInfo:
    """Normalize archive metadata while preserving executable semantics."""
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.pax_headers = {}

    filename = PurePosixPath(info.name).name
    if info.isdir() or filename == "terminal-games":
        info.mode = 0o755
    else:
        info.mode = 0o644
    return info


def _write_tar_gz(source_dir: Path, archive_path: Path) -> None:
    """Write a gzip-compressed tar archive with normalized container metadata."""
    with archive_path.open("wb") as raw_file:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_file, mtime=0) as gzip_file:
            with tarfile.open(fileobj=gzip_file, mode="w", format=tarfile.PAX_FORMAT) as archive:
                archive.add(
                    source_dir,
                    arcname=source_dir.name,
                    recursive=True,
                    filter=_normalize_tarinfo,
                )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_bundle(
    binary: Path,
    version: str,
    *,
    build_root: Path = DEFAULT_BUILD_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    license_path: Path = LICENSE_FILE,
    readme_template: Path = BUNDLE_README,
) -> tuple[Path, Path]:
    """Create the distributable archive and checksum manifest."""
    name = bundle_name(version)
    staging_parent = build_root / "bundle-stage"
    bundle_dir = staging_parent / name

    shutil.rmtree(staging_parent, ignore_errors=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    bundled_binary = bundle_dir / "terminal-games"
    shutil.copy2(binary, bundled_binary)
    bundled_binary.chmod(0o755)
    shutil.copy2(license_path, bundle_dir / "LICENSE")

    readme = readme_template.read_text(encoding="utf-8").format(version=version)
    (bundle_dir / "README.txt").write_text(readme, encoding="utf-8")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{name}.tar.gz"
    checksum_path = output_dir / "SHA256SUMS-linux-x86_64.txt"
    archive_path.unlink(missing_ok=True)
    checksum_path.unlink(missing_ok=True)

    _write_tar_gz(bundle_dir, archive_path)
    checksum_path.write_text(
        f"{sha256_file(archive_path)}  {archive_path.name}\n",
        encoding="utf-8",
    )
    return archive_path, checksum_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the validated Terminal_Games Linux x86_64 standalone bundle."
    )
    parser.add_argument(
        "--build-root",
        type=Path,
        default=DEFAULT_BUILD_ROOT,
        help="temporary build directory (default: build/desktop-linux)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="final artifact directory (default: desktop-dist)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_target()
    version = read_product_version()

    binary = build_executable(args.build_root)
    validate_executable(binary, version)
    archive_path, checksum_path = create_bundle(
        binary,
        version,
        build_root=args.build_root,
        output_dir=args.output_dir,
    )

    print(f"Validated executable: {binary}")
    print(f"Desktop archive: {archive_path}")
    print(f"Checksums: {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
