"""Terminal Minesweeper with first-move safety and three difficulty levels."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random

Coord = tuple[int, int]
HIDDEN = "·"
FLAG = "F"
MINE = "*"


@dataclass(frozen=True)
class Difficulty:
    """Configuration for one Minesweeper difficulty level."""

    name: str
    rows: int
    cols: int
    mines: int


DIFFICULTIES: dict[str, Difficulty] = {
    "1": Difficulty("Beginner", 9, 9, 10),
    "2": Difficulty("Intermediate", 16, 16, 40),
    "3": Difficulty("Expert", 16, 30, 99),
}


class MinesweeperGame:
    """Pure Minesweeper game state, separated from terminal input/output."""

    def __init__(
        self,
        rows: int,
        cols: int,
        mine_count: int,
        *,
        rng: random.Random | None = None,
        mines: set[Coord] | None = None,
    ) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("Board dimensions must be positive.")
        if not 0 < mine_count < rows * cols:
            raise ValueError("Mine count must be between 1 and board size - 1.")

        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self.rng = rng if rng is not None else random.Random()
        self.revealed: set[Coord] = set()
        self.flags: set[Coord] = set()
        self.lost = False

        if mines is None:
            self.mines: set[Coord] = set()
            self._placed = False
        else:
            if len(mines) != mine_count:
                raise ValueError("Provided mines must match mine_count.")
            if any(not self.in_bounds(*cell) for cell in mines):
                raise ValueError("Mine coordinate is outside the board.")
            self.mines = set(mines)
            self._placed = True

    @property
    def mines_placed(self) -> bool:
        """Return whether mines have already been generated."""
        return self._placed

    def in_bounds(self, row: int, col: int) -> bool:
        """Return whether a zero-based cell coordinate is on the board."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def neighbors(self, row: int, col: int) -> list[Coord]:
        """Return all valid neighboring cells around a coordinate."""
        return [
            (neighbor_row, neighbor_col)
            for neighbor_row in range(max(0, row - 1), min(self.rows, row + 2))
            for neighbor_col in range(max(0, col - 1), min(self.cols, col + 2))
            if (neighbor_row, neighbor_col) != (row, col)
        ]

    def _place_mines(self, safe_cell: Coord) -> None:
        """Generate mines after the first reveal while protecting that area."""
        if self._placed:
            return

        safe_zone = {safe_cell, *self.neighbors(*safe_cell)}
        candidates = [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if (row, col) not in safe_zone
        ]

        # Tiny custom boards may not have enough room to protect all neighbors.
        # The clicked cell itself is always protected.
        if len(candidates) < self.mine_count:
            candidates = [
                (row, col)
                for row in range(self.rows)
                for col in range(self.cols)
                if (row, col) != safe_cell
            ]

        self.mines = set(self.rng.sample(candidates, self.mine_count))
        self._placed = True

    def adjacent_mines(self, row: int, col: int) -> int:
        """Count mines in the eight neighboring cells."""
        if not self.in_bounds(row, col):
            raise ValueError("Cell outside board.")
        return sum(cell in self.mines for cell in self.neighbors(row, col))

    def toggle_flag(self, row: int, col: int) -> bool:
        """Toggle a flag. Return True when a flag is placed."""
        if not self.in_bounds(row, col):
            raise ValueError("Cell outside board.")

        cell = (row, col)
        if cell in self.revealed:
            return False
        if cell in self.flags:
            self.flags.remove(cell)
            return False

        self.flags.add(cell)
        return True

    def reveal(self, row: int, col: int) -> None:
        """Reveal a cell and flood-fill connected empty regions."""
        if not self.in_bounds(row, col):
            raise ValueError("Cell outside board.")
        if self.lost or self.is_won():
            return

        cell = (row, col)
        if cell in self.flags:
            return

        self._place_mines(cell)
        if cell in self.mines:
            self.revealed.add(cell)
            self.lost = True
            return

        queue: deque[Coord] = deque([cell])
        while queue:
            current = queue.popleft()
            if current in self.revealed or current in self.flags or current in self.mines:
                continue

            self.revealed.add(current)
            if self.adjacent_mines(*current) == 0:
                for neighbor in self.neighbors(*current):
                    if (
                        neighbor not in self.revealed
                        and neighbor not in self.flags
                        and neighbor not in self.mines
                    ):
                        queue.append(neighbor)

    def is_won(self) -> bool:
        """Return True when every non-mine cell has been revealed."""
        safe_cells = self.rows * self.cols - self.mine_count
        return self._placed and not self.lost and len(self.revealed) == safe_cells

    def symbol_at(self, row: int, col: int, *, reveal_all: bool = False) -> str:
        """Return the terminal symbol representing one cell."""
        cell = (row, col)

        if reveal_all:
            if cell in self.mines:
                return MINE
            count = self.adjacent_mines(row, col)
            return " " if count == 0 else str(count)

        if cell in self.flags:
            return FLAG
        if cell not in self.revealed:
            return HIDDEN

        count = self.adjacent_mines(row, col)
        return " " if count == 0 else str(count)

    def render(self, *, reveal_all: bool = False) -> str:
        """Render the board with one-based row and column coordinates."""
        header = "    " + " ".join(f"{col + 1:>2}" for col in range(self.cols))
        lines = [header]

        for row in range(self.rows):
            cells = " ".join(
                f"{self.symbol_at(row, col, reveal_all=reveal_all):>2}"
                for col in range(self.cols)
            )
            lines.append(f"{row + 1:>2}  {cells}")

        return "\n".join(lines)


def parse_command(raw: str) -> tuple[str, int | None, int | None]:
    """Parse a terminal command into action and zero-based coordinates."""
    parts = raw.strip().lower().split()
    if not parts:
        raise ValueError("Enter a command.")

    if parts[0] in {"q", "quit", "exit"}:
        if len(parts) != 1:
            raise ValueError("Quit command takes no coordinates.")
        return "quit", None, None

    # Two bare numbers are shorthand for revealing a cell.
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        return "reveal", int(parts[0]) - 1, int(parts[1]) - 1

    if len(parts) == 3:
        action = parts[0]
        if action in {"r", "reveal", "open"}:
            normalized = "reveal"
        elif action in {"f", "flag"}:
            normalized = "flag"
        else:
            raise ValueError("Use R row col, F row col, or Q.")

        if not parts[1].isdigit() or not parts[2].isdigit():
            raise ValueError("Row and column must be numbers.")

        return normalized, int(parts[1]) - 1, int(parts[2]) - 1

    raise ValueError("Use R row col, F row col, or Q.")


def choose_difficulty() -> Difficulty | None:
    """Prompt for a difficulty, returning None when the player quits."""
    print("Choose difficulty:")
    for key, difficulty in DIFFICULTIES.items():
        print(
            f"{key}. {difficulty.name} "
            f"({difficulty.rows}x{difficulty.cols}, {difficulty.mines} mines)"
        )
    print("Q. Quit")

    while True:
        choice = input("\nDifficulty: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return None
        difficulty = DIFFICULTIES.get(choice)
        if difficulty is not None:
            return difficulty
        print("Invalid selection.")


def play_round(difficulty: Difficulty) -> bool:
    """Play one round. Return False if the player quits the game."""
    game = MinesweeperGame(
        difficulty.rows,
        difficulty.cols,
        difficulty.mines,
    )

    print(
        f"\n{difficulty.name}: {difficulty.rows}x{difficulty.cols}, "
        f"{difficulty.mines} mines"
    )
    print("Commands: R row col = reveal, F row col = flag, Q = quit")
    print("Shortcut: entering just 'row col' reveals that cell.")
    print("The first revealed cell is always safe.\n")

    while not game.lost and not game.is_won():
        print(game.render())
        remaining = game.mine_count - len(game.flags)
        print(f"\nMines: {game.mine_count} | Flags: {len(game.flags)} | Unflagged estimate: {remaining}")

        try:
            action, row, col = parse_command(input("Move: "))
        except ValueError as exc:
            print(f"\n{exc}\n")
            continue

        if action == "quit":
            return False

        assert row is not None and col is not None
        if not game.in_bounds(row, col):
            print(
                f"\nCoordinates must be within rows 1-{game.rows} "
                f"and columns 1-{game.cols}.\n"
            )
            continue

        if action == "flag":
            if (row, col) in game.revealed:
                print("\nThat cell is already revealed.\n")
            else:
                placed = game.toggle_flag(row, col)
                print("\nFlag placed.\n" if placed else "\nFlag removed.\n")
            continue

        if (row, col) in game.flags:
            print("\nRemove the flag before revealing that cell.\n")
            continue

        game.reveal(row, col)
        print()

    print(game.render(reveal_all=True))
    if game.lost:
        print("\nBoom. You hit a mine.")
    else:
        print("\nYou cleared the minefield. You win.")
    return True


def main() -> None:
    """Run the interactive terminal game."""
    print("=== Minesweeper ===")

    while True:
        difficulty = choose_difficulty()
        if difficulty is None:
            print("Goodbye.")
            return

        if not play_round(difficulty):
            print("\nGoodbye.")
            return

        again = input("\nPlay again? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return
        print()


if __name__ == "__main__":
    main()
