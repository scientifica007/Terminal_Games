import unittest

from games.terminal_input import (
    ANSI_ARROW_KEYS,
    decode_arrow_sequence,
    decode_text_key,
    is_complete_arrow_sequence,
)


class TerminalInputTests(unittest.TestCase):
    def test_csi_arrows(self):
        self.assertEqual(ANSI_ARROW_KEYS["\x1b[A"], "up")
        self.assertEqual(decode_arrow_sequence(b"\x1b[B"), "down")
        self.assertEqual(decode_arrow_sequence(b"\x1b[C"), "right")
        self.assertEqual(decode_arrow_sequence(b"\x1b[D"), "left")

    def test_ss3_arrows(self):
        self.assertEqual(decode_arrow_sequence(b"\x1bOA"), "up")
        self.assertEqual(decode_arrow_sequence(b"\x1bOD"), "left")

    def test_modified_csi_arrows(self):
        self.assertEqual(decode_arrow_sequence(b"\x1b[1;5A"), "up")
        self.assertEqual(decode_arrow_sequence(b"\x1b[1;2C"), "right")

    def test_invalid_escape_sequence(self):
        self.assertIsNone(decode_arrow_sequence(b"\x1b[Z"))

    def test_arrow_completion_accepts_bytearray(self):
        self.assertTrue(is_complete_arrow_sequence(bytearray(b"\x1b[A")))
        self.assertFalse(is_complete_arrow_sequence(bytearray(b"\x1b[")))

    def test_text_decoder_supports_unicode(self):
        self.assertEqual(decode_text_key(b"Q"), "q")
        self.assertEqual(decode_text_key("ض".encode("utf-8")), "ض")
        self.assertIsNone(decode_text_key(b"\xff"))


if __name__ == "__main__":
    unittest.main()
