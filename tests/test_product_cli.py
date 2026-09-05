from __future__ import annotations

import contextlib
from io import StringIO
import unittest
from unittest.mock import patch

import terminal_games
from terminal_games import cli


class ProductVersionTests(unittest.TestCase):
    def test_development_version_targets_v1_1_0(self) -> None:
        self.assertEqual(terminal_games.__version__, "1.1.0.dev0")


class ProductCliTests(unittest.TestCase):
    def test_version_flag_prints_product_version_without_launching_games(self) -> None:
        output = StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), "terminal-games 1.1.0.dev0")

    def test_no_product_options_delegate_to_existing_launcher(self) -> None:
        with patch("launcher.main") as launcher_main:
            cli.main([])

        launcher_main.assert_called_once_with()

    def test_unknown_product_option_is_rejected_before_launcher(self) -> None:
        error = StringIO()
        with contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["--not-a-real-option"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unrecognized arguments", error.getvalue())


if __name__ == "__main__":
    unittest.main()
