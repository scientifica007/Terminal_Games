"""Real-time terminal Snake using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
import os
import select
import sys
import time
from typing import Any, TextIO

from games.progress import (
    ProgressDataError,
    clear_save,
    get_best_score,
    load_state,
    save_state,
    update_best_score,
)
from games.session_menu import LOAD, NEW, QUIT, choose_session_action

GAME_ID = "snake"
SAVE_VERSION = 1
WIDTH = 24
HEIGHT = 14
INITIAL_LENGTH = 3
FOOD_SCORE = 10
VERTICAL_TICK_MULTIPLIER = 2.0

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

DIRECTION_KEYS = {
    "up": UP,
    "down": DOWN,
    "left": LEFT,
    "right": RIGHT,
}

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

QUIT_KEYS = {"q", "ض", "escape", "\x03"}
SAVE_KEYS = {"s", "س"}

SPEEDS = {
    "1": ("Relaxed", 0.18),
    "2": ("Normal", 0.12),
    "3": ("Fast", 0.08),
}

Position = tuple[int, int]
Direction = tuple[int, int]


@dataclass
class GameState:
    snake: list[Position]
    direction: Direction
    food: Position | None
    score: int = 0
    alive: bool = True


def initial_snake(
    width: int = WIDTH,
    height: int = HEIGHT,
    length: int = INITIAL_LENGTH,
) -> list[Position]:
    """Create a centered horizontal snake facing right."""
    if width < length + 2 or height < 3:
        raise ValueError("Board is too small for the initial snake.")
    head_x = width // 2
    y = height // 2
    return [(head_x - offset, y) for offset in range(length)]


def change_direction(current: Direction, key: str) -> Direction:
    """Apply an arrow direction while preventing an immediate 180-degree turn."""
    requested = DIRECTION_KEYS.get(key.lower())
    if requested is None:
        return current
    if requested == (-current[0], -current[1]):
        return current
    return requested


def movement_interval(base_seconds: float, direction: Direction) -> float:
    """Return the tick interval adjusted for terminal cell aspect ratio.

    Terminal character cells are usually much taller than they are wide. A
    vertical logical step therefore looks faster than a horizontal step even
    when both use the same timestep. Keep horizontal timing unchanged and slow
    vertical movement so perceived speed is closer on both axes.
    """
    if base_seconds <= 0:
        raise ValueError("Base tick duration must be positive.")
    if direction in {UP, DOWN}:
        return base_seconds * VERTICAL_TICK_MULTIPLIER
    return base_seconds


def is_quit_key(key: str | None) -> bool:
    """Return True for supported quit inputs in English or Arabic layouts."""
    return key is not None and key.lower() in QUIT_KEYS


def is_save_key(key: str | None) -> bool:
    """Return True for the physical S key in English or Arabic layouts."""
    return key is not None and key.lower() in SAVE_KEYS


def next_head(head: Position, direction: Direction) -> Position:
    """Return the unwrapped next head position for a direction."""
    return head[0] + direction[0], head[1] + direction[1]


def wrap_position(position: Position, width: int, height: int) -> Position:
    """Wrap a position across the board edges."""
    if width <= 0 or height <= 0:
        raise ValueError("Board dimensions must be positive.")
    return position[0] % width, position[1] % height


def advance_snake(
    snake: list[Position],
    direction: Direction,
    food: Position | None,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> tuple[list[Position], bool, bool]:
    """Advance one tick and wrap across board edges.

    Return (new_snake, ate_food, alive). The walls are portals: crossing one
    edge enters from the opposite edge. Moving into the current tail is legal
    when no food is eaten because the tail vacates during the same tick.
    """
    if not snake:
        raise ValueError("Snake cannot be empty.")

    new_head = wrap_position(next_head(snake[0], direction), width, height)
    ate_food = food is not None and new_head == food
    occupied = snake if ate_food else snake[:-1]
    if new_head in occupied:
        return snake[:], False, False

    if ate_food:
        new_snake = [new_head, *snake]
    else:
        new_snake = [new_head, *snake[:-1]]
    return new_snake, ate_food, True


def place_food(
    snake: list[Position],
    width: int = WIDTH,
    height: int = HEIGHT,
    rng: Random | None = None,
) -> Position | None:
    """Place food on a random empty cell, or return None if the board is full."""
    occupied = set(snake)
    empty = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in occupied
    ]
    if not empty:
        return None
    generator = rng or Random()
    return generator.choice(empty)


def new_game(
    width: int = WIDTH,
    height: int = HEIGHT,
    rng: Random | None = None,
) -> GameState:
    """Create a new playable state."""
    snake = initial_snake(width, height)
    return GameState(
        snake=snake,
        direction=RIGHT,
        food=place_food(snake, width, height, rng),
    )


def render_board(
    state: GameState,
    width: int = WIDTH,
    height: int = HEIGHT,
    status: str = "",
) -> str:
    """Render the current game state as a terminal frame."""
    snake_cells = set(state.snake[1:])
    head = state.snake[0]
    top = "+" + "-" * width + "+"
    lines = [
        "=== Snake ===",
        "Controls: Arrow keys = move; S = save; Q / Esc = quit. Edges wrap.",
        f"Score: {state.score}   Length: {len(state.snake)}"
        + (f"   {status}" if status else ""),
        top,
    ]
    for y in range(height):
        row = []
        for x in range(width):
            position = (x, y)
            if position == head:
                row.append("@")
            elif position in snake_cells:
                row.append("o")
            elif position == state.food:
                row.append("*")
            else:
                row.append(" ")
        lines.append("|" + "".join(row) + "|")
    lines.append(top)
    return "\n".join(lines)


def serialize_session(state: GameState, speed_name: str) -> dict[str, Any]:
    """Serialize a live Snake state and its selected speed."""
    return {
        "version": SAVE_VERSION,
        "snake": [list(cell) for cell in state.snake],
        "direction": list(state.direction),
        "food": None if state.food is None else list(state.food),
        "score": state.score,
        "speed": speed_name,
    }


def _decode_position(value: Any, label: str) -> Position:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or isinstance(value[0], bool)
        or isinstance(value[1], bool)
        or not isinstance(value[0], int)
        or not isinstance(value[1], int)
    ):
        raise ValueError(f"Invalid saved {label}.")
    position = (value[0], value[1])
    if not (0 <= position[0] < WIDTH and 0 <= position[1] < HEIGHT):
        raise ValueError(f"Saved {label} is outside the board.")
    return position


def _decode_direction(value: Any) -> Direction:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or isinstance(value[0], bool)
        or isinstance(value[1], bool)
        or not isinstance(value[0], int)
        or not isinstance(value[1], int)
    ):
        raise ValueError("Invalid saved direction.")
    direction = (value[0], value[1])
    if direction not in {UP, DOWN, LEFT, RIGHT}:
        raise ValueError("Invalid saved direction.")
    return direction


def deserialize_session(state: dict[str, Any]) -> tuple[GameState, str, float]:
    """Validate and restore a live Snake state."""
    if state.get("version") != SAVE_VERSION:
        raise ValueError("Unsupported Snake save version.")
    raw_snake = state.get("snake")
    if not isinstance(raw_snake, list) or not raw_snake:
        raise ValueError("Invalid saved snake.")
    snake = [_decode_position(cell, "snake cell") for cell in raw_snake]
    if len(set(snake)) != len(snake):
        raise ValueError("Saved snake overlaps itself.")

    direction = _decode_direction(state.get("direction"))

    raw_food = state.get("food")
    food = None if raw_food is None else _decode_position(raw_food, "food")
    if food in snake:
        raise ValueError("Saved food overlaps the snake.")

    score = state.get("score")
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("Invalid saved score.")

    speed_name = state.get("speed")
    speed_lookup = {name: delay for name, delay in SPEEDS.values()}
    if speed_name not in speed_lookup:
        raise ValueError("Invalid saved speed.")

    restored = GameState(snake=snake, direction=direction, food=food, score=score, alive=True)
    return restored, str(speed_name), speed_lookup[str(speed_name)]


def decode_arrow_sequence(sequence: bytes | str) -> str | None:
    """Decode common POSIX terminal arrow escape sequences.

    Supports normal CSI arrows (ESC [ A), application-cursor SS3 arrows
    (ESC O A), and CSI variants carrying modifiers such as ESC [ 1 ; 2 A.
    """
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
    """Decode one regular UTF-8 key collected from the raw terminal."""
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
    """Return True when a raw POSIX escape sequence contains a full arrow key."""
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
        """Return an arrow name, a regular key, or None when timeout expires."""
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


def _choose_speed() -> tuple[str, float] | None:
    print("Choose speed:")
    for key, (name, delay) in SPEEDS.items():
        print(f"{key}. {name} ({delay:.2f}s horizontal tick)")
    print("Q. Quit")

    while True:
        choice = input("\nSpeed: ").strip().lower()
        if is_quit_key(choice) or choice in {"quit", "exit"}:
            return None
        speed = SPEEDS.get(choice)
        if speed is not None:
            return speed
        print("Choose 1, 2, or 3.")


def play_round(
    rng: Random | None = None,
    saved: tuple[GameState, str, float] | None = None,
) -> bool:
    """Play one real-time round. Return False when the player asks to quit."""
    generator = rng or Random()
    if saved is None:
        speed = _choose_speed()
        if speed is None:
            return False
        speed_name, tick_seconds = speed
        state = new_game(rng=generator)
    else:
        state, speed_name, tick_seconds = saved

    status = f"Speed: {speed_name} | Best: {get_best_score(GAME_ID)}"

    if not sys.stdin.isatty():
        print("Snake requires an interactive terminal (TTY).")
        return False

    print("\033[2J\033[?25l", end="", flush=True)
    try:
        try:
            with KeyReader() as reader:
                next_tick = time.monotonic() + movement_interval(tick_seconds, state.direction)
                pending_direction = state.direction

                while state.alive:
                    print("\033[H" + render_board(state, status=status), end="", flush=True)

                    while True:
                        remaining = next_tick - time.monotonic()
                        if remaining <= 0:
                            break

                        key = reader.read_key(remaining)
                        if is_quit_key(key):
                            return False
                        if is_save_key(key):
                            try:
                                save_state(GAME_ID, serialize_session(state, speed_name))
                                status = (
                                    f"Saved | Speed: {speed_name} | "
                                    f"Best: {get_best_score(GAME_ID)}"
                                )
                            except ProgressDataError:
                                status = "Save failed"
                            continue
                        if key in DIRECTION_KEYS:
                            pending_direction = change_direction(state.direction, key)

                    state.direction = pending_direction
                    snake, ate_food, alive = advance_snake(
                        state.snake,
                        state.direction,
                        state.food,
                    )
                    state.snake = snake
                    state.alive = alive
                    next_tick += movement_interval(tick_seconds, state.direction)

                    if not alive:
                        break

                    if ate_food:
                        state.score += FOOD_SCORE
                        if update_best_score(GAME_ID, state.score):
                            status = f"New Best! {state.score} | Speed: {speed_name}"
                        else:
                            status = (
                                f"Speed: {speed_name} | "
                                f"Best: {get_best_score(GAME_ID)}"
                            )
                        state.food = place_food(state.snake, rng=generator)
                        if state.food is None:
                            print(
                                "\033[H"
                                + render_board(state, status="Board cleared!"),
                                end="",
                                flush=True,
                            )
                            break

                if not state.alive:
                    print(
                        "\033[H" + render_board(state, status="Self collision"),
                        end="",
                        flush=True,
                    )
        except KeyboardInterrupt:
            return False
    finally:
        print("\033[?25h", flush=True)

    clear_save(GAME_ID)
    update_best_score(GAME_ID, state.score)
    if state.food is None:
        print(f"\nYou filled the entire board. Final score: {state.score}")
    else:
        print(f"\nYou hit your own body. Final score: {state.score}")
    print(f"Best Score: {get_best_score(GAME_ID)}")
    return True


def _load_saved_game() -> tuple[GameState, str, float] | None:
    state = load_state(GAME_ID)
    if state is None:
        return None
    try:
        return deserialize_session(state)
    except ValueError as exc:
        print(f"\nSaved game is invalid: {exc}")
        return None


def main() -> None:
    """Run Snake."""
    print("=== Snake ===")
    print("Move in real time with the arrow keys. No Enter needed.")
    print("Eat * to grow. Crossing an edge wraps you to the opposite side.")
    print("Avoid your own body. Press S to save, Q or Esc to quit.")

    while True:
        action = choose_session_action(GAME_ID, "Snake")
        if action == QUIT:
            print("Goodbye.")
            return

        saved = None
        if action == LOAD:
            saved = _load_saved_game()
            if saved is None:
                continue
            print("\nSaved game loaded.")
        elif action != NEW:
            continue

        if not play_round(saved=saved):
            print("\nGoodbye.")
            return

        again = input("\nPlay another round? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return
        print()


if __name__ == "__main__":
    main()
