"""Real-time terminal Snake using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
import os
import select
import sys
import time
from typing import TextIO

WIDTH = 24
HEIGHT = 14
INITIAL_LENGTH = 3
FOOD_SCORE = 10

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
}

WINDOWS_ARROW_KEYS = {
    "H": "up",
    "P": "down",
    "M": "right",
    "K": "left",
}

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
        "Controls: Arrow keys = move, Q = quit. Edges wrap to the opposite side.",
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
                    return first.lower()
                time.sleep(min(0.01, timeout))
            return None

        ready, _, _ = select.select([self.stream], [], [], timeout)
        if not ready:
            return None

        first = self.stream.read(1)
        if first != "\x1b":
            return first.lower()

        sequence = first
        deadline = time.monotonic() + 0.02
        while len(sequence) < 3:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            ready, _, _ = select.select([self.stream], [], [], remaining)
            if not ready:
                break
            sequence += self.stream.read(1)
        return ANSI_ARROW_KEYS.get(sequence)


def _choose_speed() -> tuple[str, float] | None:
    print("Choose speed:")
    for key, (name, delay) in SPEEDS.items():
        print(f"{key}. {name} ({delay:.2f}s/tick)")
    print("Q. Quit")

    while True:
        choice = input("\nSpeed: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return None
        speed = SPEEDS.get(choice)
        if speed is not None:
            return speed
        print("Choose 1, 2, or 3.")


def play_round(rng: Random | None = None) -> bool:
    """Play one real-time round. Return False when the player asks to quit."""
    speed = _choose_speed()
    if speed is None:
        return False

    speed_name, tick_seconds = speed
    generator = rng or Random()
    state = new_game(rng=generator)
    status = f"Speed: {speed_name}"

    if not sys.stdin.isatty():
        print("Snake requires an interactive terminal (TTY).")
        return False

    print("\033[2J\033[?25l", end="", flush=True)
    try:
        with KeyReader() as reader:
            next_tick = time.monotonic() + tick_seconds
            pending_direction = state.direction

            while state.alive:
                print("\033[H" + render_board(state, status=status), end="", flush=True)

                while True:
                    remaining = next_tick - time.monotonic()
                    if remaining <= 0:
                        break

                    key = reader.read_key(remaining)
                    if key in {"q", "\x03"}:
                        return False
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
                next_tick += tick_seconds

                if not alive:
                    break

                if ate_food:
                    state.score += FOOD_SCORE
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
    finally:
        print("\033[?25h", flush=True)

    if state.food is None:
        print(f"\nYou filled the entire board. Final score: {state.score}")
    else:
        print(f"\nYou hit your own body. Final score: {state.score}")
    return True


def main() -> None:
    """Run Snake."""
    print("=== Snake ===")
    print("Move in real time with the arrow keys. No Enter needed.")
    print("Eat * to grow. Crossing an edge wraps you to the opposite side.")
    print("Avoid your own body. Press Q to quit.")

    while True:
        if not play_round():
            print("\nGoodbye.")
            return

        again = input("\nPlay again? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return
        print()


if __name__ == "__main__":
    main()
