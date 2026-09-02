"""Terminal implementation of the 2048 puzzle game."""

from __future__ import annotations

from random import Random
from typing import Iterable

SIZE = 4
TARGET = 2048
DIRECTIONS = {"w": "up", "a": "left", "s": "down", "d": "right"}

Board = list[list[int]]


def new_board(size: int = SIZE) -> Board:
    """Return an empty square board."""
    if size < 2:
        raise ValueError("Board size must be at least 2.")
    return [[0 for _ in range(size)] for _ in range(size)]


def empty_cells(board: Board) -> list[tuple[int, int]]:
    """Return coordinates of every empty cell."""
    return [
        (row_index, col_index)
        for row_index, row in enumerate(board)
        for col_index, value in enumerate(row)
        if value == 0
    ]


def add_random_tile(board: Board, rng: Random | None = None) -> bool:
    """Add a 2 (90%) or 4 (10%) to a random empty cell.

    Return False if the board has no empty cells.
    """
    generator = rng or Random()
    cells = empty_cells(board)
    if not cells:
        return False

    row, col = generator.choice(cells)
    board[row][col] = 4 if generator.random() < 0.10 else 2
    return True


def merge_line(line: Iterable[int]) -> tuple[list[int], int]:
    """Slide one line left, merge equal pairs once, and return score gained."""
    source = list(line)
    values = [value for value in source if value != 0]
    merged: list[int] = []
    gained = 0
    index = 0

    while index < len(values):
        current = values[index]
        if index + 1 < len(values) and values[index + 1] == current:
            current *= 2
            gained += current
            index += 2
        else:
            index += 1
        merged.append(current)

    return merged + [0] * (len(source) - len(merged)), gained


def _copy_board(board: Board) -> Board:
    return [row[:] for row in board]


def _transpose(board: Board) -> Board:
    return [list(column) for column in zip(*board)]


def _move_left(board: Board) -> tuple[Board, int]:
    result: Board = []
    gained = 0
    for row in board:
        merged, score = merge_line(row)
        result.append(merged)
        gained += score
    return result, gained


def move(board: Board, direction: str) -> tuple[Board, int, bool]:
    """Move in one of up/down/left/right.

    Return (new_board, score_gained, changed).
    """
    normalized = direction.strip().lower()
    if normalized in DIRECTIONS:
        normalized = DIRECTIONS[normalized]
    if normalized not in {"up", "down", "left", "right"}:
        raise ValueError(f"Unknown direction: {direction}")

    original = _copy_board(board)

    if normalized == "left":
        result, gained = _move_left(board)
    elif normalized == "right":
        reversed_board = [list(reversed(row)) for row in board]
        shifted, gained = _move_left(reversed_board)
        result = [list(reversed(row)) for row in shifted]
    elif normalized == "up":
        transposed = _transpose(board)
        shifted, gained = _move_left(transposed)
        result = _transpose(shifted)
    else:  # down
        transposed = _transpose(board)
        reversed_board = [list(reversed(row)) for row in transposed]
        shifted, gained = _move_left(reversed_board)
        restored = [list(reversed(row)) for row in shifted]
        result = _transpose(restored)

    return result, gained, result != original


def can_move(board: Board) -> bool:
    """Return True while at least one legal move remains."""
    if empty_cells(board):
        return True

    size = len(board)
    for row in range(size):
        for col in range(size):
            value = board[row][col]
            if row + 1 < size and board[row + 1][col] == value:
                return True
            if col + 1 < size and board[row][col + 1] == value:
                return True
    return False


def max_tile(board: Board) -> int:
    """Return the largest tile on the board."""
    return max((value for row in board for value in row), default=0)


def render_board(board: Board, score: int) -> str:
    """Render a compact terminal board with score information."""
    largest = max_tile(board)
    cell_width = max(5, len(str(largest)) + 2)
    separator = "+" + "+".join("-" * cell_width for _ in range(len(board))) + "+"

    lines = [f"Score: {score}   Max tile: {largest}", separator]
    for row in board:
        cells = []
        for value in row:
            text = "." if value == 0 else str(value)
            cells.append(text.center(cell_width))
        lines.append("|" + "|".join(cells) + "|")
        lines.append(separator)
    return "\n".join(lines)


def _read_move() -> str | None:
    while True:
        raw = input("Move [W/A/S/D] or Q to quit: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return None
        if raw in DIRECTIONS:
            return raw
        print("Use W, A, S, or D.")


def play_round(rng: Random | None = None) -> bool:
    """Play one round. Return False when the player asks to quit."""
    generator = rng or Random()
    board = new_board()
    add_random_tile(board, generator)
    add_random_tile(board, generator)

    score = 0
    target_announced = False

    print("\nUse W/A/S/D to slide every tile. Equal tiles merge once per move.\n")

    while True:
        print(render_board(board, score))
        print()

        if not can_move(board):
            print("No legal moves remain. Game over.")
            print(f"Final score: {score}")
            return True

        command = _read_move()
        if command is None:
            return False

        moved_board, gained, changed = move(board, command)
        if not changed:
            print("\nThat move changes nothing. Try another direction.\n")
            continue

        board = moved_board
        score += gained
        add_random_tile(board, generator)

        if not target_announced and max_tile(board) >= TARGET:
            target_announced = True
            print(f"\nYou reached {TARGET}! You can keep playing.\n")


def main() -> None:
    """Run the interactive terminal game."""
    print("=== 2048 ===")
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
