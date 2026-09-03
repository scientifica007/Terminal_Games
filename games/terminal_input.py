"""Reusable immediate terminal key input for real-time games."""

from __future__ import annotations

import os
import select
import sys
import time
from typing import TextIO

ANSI_ARROW_KEYS = {
    "\x1b[A": "up",
    "\x1b[B": "down",
    "\x1b[C": "right",
    "\x1b[D": "left",
    "\x1bOA": "up",
    "\x1bOB": "down",
    "\x1bOC": "right",
    "\x1bOD": "left",
}

ARROW_FINALS = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
}

WINDOWS_ARROW_KEYS = {
    "H": "up",
    "P": "down",
    "M": "right",
    "K": "left",
}


def decode_arrow_sequence(sequence: bytes | str) -> str | None:
    """Decode common CSI/SS3 terminal arrow sequences."""
    if isinstance(sequence, bytes):
        try:
            text = sequence.decode("ascii")
        except UnicodeDecodeError:
            return None
    else:
        text = sequence

    direct = ANSI_ARROW_KEYS.get(text)
    if direct is not None:
        return direct

    if len(text) >= 3 and (text.startswith("\x1b[") or text.startswith("\x1bO")):
        return ARROW_FINALS.get(text[-1])
    return None


def decode_text_key(sequence: bytes) -> str | None:
    """Decode one regular UTF-8 key collected from a raw terminal."""
    try:
        text = sequence.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text.lower() or None


def _utf8_length(first_byte: int) -> int:
    if first_byte < 0x80:
        return 1
    if first_byte & 0xE0 == 0xC0:
        return 2
    if first_byte & 0xF0 == 0xE0:
        return 3
    if first_byte & 0xF8 == 0xF0:
        return 4
    return 1


def is_complete_arrow_sequence(sequence: bytes | bytearray) -> bool:
    """Return whether a raw escape sequence contains a complete arrow key."""
    raw = bytes(sequence)
    return (
        len(raw) >= 3
        and raw[:2] in {b"\x1b[", b"\x1bO"}
        and raw[-1:] in {b"A", b"B", b"C", b"D"}
    )


class KeyReader:
    """Read single keys/arrows without Enter and restore terminal state."""

    def __init__(self, stream: TextIO = sys.stdin) -> None:
        self.stream = stream
        self._fd: int | None = None
        self._settings = None

    def __enter__(self) -> "KeyReader":
        if os.name != "nt":
            import termios
            import tty

            self._fd = self.stream.fileno()
            self._settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if os.name != "nt" and self._fd is not None and self._settings is not None:
            import termios

            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._settings)

    def _read_utf8_key(self, fd: int, first: bytes) -> str | None:
        expected = _utf8_length(first[0])
        if expected == 1:
            return decode_text_key(first)

        sequence = bytearray(first)
        deadline = time.monotonic() + 0.04
        while len(sequence) < expected:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            ready, _, _ = select.select([fd], [], [], remaining)
            if not ready:
                break
            chunk = os.read(fd, expected - len(sequence))
            if not chunk:
                break
            sequence.extend(chunk)
        return decode_text_key(bytes(sequence))

    def read_key(self, timeout: float) -> str | None:
        """Return an arrow name, regular key, or None when timeout expires."""
        if timeout < 0:
            raise ValueError("Timeout cannot be negative.")

        if os.name == "nt":
            import msvcrt

            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if msvcrt.kbhit():
                    first = msvcrt.getwch()
                    if first in {"\x00", "\xe0"}:
                        return WINDOWS_ARROW_KEYS.get(msvcrt.getwch())
                    if first == "\x1b":
                        return "escape"
                    return first.lower()
                time.sleep(min(0.01, timeout))
            return None

        fd = self._fd if self._fd is not None else self.stream.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None

        first = os.read(fd, 1)
        if not first:
            return None
        if first != b"\x1b":
            return self._read_utf8_key(fd, first)

        sequence = bytearray(first)
        deadline = time.monotonic() + 0.04
        while len(sequence) < 16:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            ready, _, _ = select.select([fd], [], [], remaining)
            if not ready:
                break
            chunk = os.read(fd, 1)
            if not chunk:
                break
            sequence.extend(chunk)
            if is_complete_arrow_sequence(sequence):
                break

        if sequence == b"\x1b":
            return "escape"
        return decode_arrow_sequence(bytes(sequence))
