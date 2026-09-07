import tempfile
import unittest
from pathlib import Path

from scripts import release_guard


class ReleaseGuardTests(unittest.TestCase):
    def test_matching_stable_tag_is_accepted(self):
        release_guard.validate_release_tag("v1.1.0", "1.1.0")

    def test_development_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a stable"):
            release_guard.validate_release_tag("v1.1.0", "1.1.0.dev0")

    def test_release_candidate_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a stable"):
            release_guard.validate_release_tag("v1.1.0", "1.1.0rc1")

    def test_mismatched_tag_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            release_guard.validate_release_tag("v1.2.0", "1.1.0")

    def test_malformed_stable_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a stable"):
            release_guard.validate_release_tag("v1.1", "1.1")

    def test_read_product_version_reads_literal_assignment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            version_file = Path(tmpdir) / "__init__.py"
            version_file.write_text('__version__ = "2.3.4"\n', encoding="utf-8")
            self.assertEqual(release_guard.read_product_version(version_file), "2.3.4")

    def test_read_product_version_requires_assignment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            version_file = Path(tmpdir) / "__init__.py"
            version_file.write_text("VALUE = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No __version__ assignment"):
                release_guard.read_product_version(version_file)


if __name__ == "__main__":
    unittest.main()
