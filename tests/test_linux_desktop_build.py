from __future__ import annotations

from pathlib import Path
import tarfile
import tempfile
import unittest

from scripts import build_linux_desktop


class LinuxDesktopTargetTests(unittest.TestCase):
    def test_linux_x86_64_is_supported(self) -> None:
        build_linux_desktop.validate_target("Linux", "x86_64")
        build_linux_desktop.validate_target("linux", "AMD64")

    def test_non_linux_target_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "requires Linux"):
            build_linux_desktop.validate_target("Windows", "AMD64")

    def test_non_x86_64_linux_target_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "x86_64 only"):
            build_linux_desktop.validate_target("Linux", "aarch64")

    def test_bundle_name_includes_version_and_target(self) -> None:
        self.assertEqual(
            build_linux_desktop.bundle_name("1.2.0.dev0"),
            "terminal-games-1.2.0.dev0-linux-x86_64",
        )


class LinuxDesktopVersionTests(unittest.TestCase):
    def test_read_product_version_reads_literal_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            version_file = Path(tmpdir) / "__init__.py"
            version_file.write_text('__version__ = "2.4.0.dev0"\n', encoding="utf-8")
            self.assertEqual(
                build_linux_desktop.read_product_version(version_file),
                "2.4.0.dev0",
            )

    def test_read_product_version_requires_literal_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            version_file = Path(tmpdir) / "__init__.py"
            version_file.write_text("VALUE = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No __version__ assignment"):
                build_linux_desktop.read_product_version(version_file)


class LinuxDesktopCommandTests(unittest.TestCase):
    def test_pyinstaller_command_is_onefile_and_uses_product_entrypoint(self) -> None:
        root = Path("/repo")
        command = build_linux_desktop.pyinstaller_command(Path("/tmp/build"), root)

        self.assertIn("--onefile", command)
        self.assertIn("--name", command)
        self.assertIn("terminal-games", command)
        self.assertIn("--paths", command)
        self.assertEqual(command[-1], "/repo/terminal_games/__main__.py")


class LinuxDesktopBundleTests(unittest.TestCase):
    def test_bundle_contains_executable_license_readme_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            binary = root / "terminal-games"
            binary.write_bytes(b"standalone-binary")
            binary.chmod(0o755)

            license_path = root / "LICENSE"
            license_path.write_text("MIT test license\n", encoding="utf-8")
            readme_template = root / "README.txt"
            readme_template.write_text("Terminal_Games {version}\n", encoding="utf-8")

            output_dir = root / "out"
            archive_path, checksum_path = build_linux_desktop.create_bundle(
                binary,
                "2.0.0",
                build_root=root / "build",
                output_dir=output_dir,
                license_path=license_path,
                readme_template=readme_template,
            )

            self.assertEqual(
                archive_path.name,
                "terminal-games-2.0.0-linux-x86_64.tar.gz",
            )
            self.assertTrue(checksum_path.is_file())

            bundle_root = "terminal-games-2.0.0-linux-x86_64"
            with tarfile.open(archive_path, "r:gz") as archive:
                names = set(archive.getnames())
                self.assertIn(f"{bundle_root}/terminal-games", names)
                self.assertIn(f"{bundle_root}/LICENSE", names)
                self.assertIn(f"{bundle_root}/README.txt", names)

                executable = archive.getmember(f"{bundle_root}/terminal-games")
                self.assertNotEqual(executable.mode & 0o111, 0)

                readme_file = archive.extractfile(f"{bundle_root}/README.txt")
                self.assertIsNotNone(readme_file)
                assert readme_file is not None
                self.assertEqual(
                    readme_file.read().decode("utf-8"),
                    "Terminal_Games 2.0.0\n",
                )

            expected = (
                f"{build_linux_desktop.sha256_file(archive_path)}  {archive_path.name}\n"
            )
            self.assertEqual(checksum_path.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
