"""Terminal Minesweeper with first-move safety and three difficulty levels."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random
from typing import Any

from games.progress import (
    ProgressDataError,
    clear_save,
    get_best_score,
    load_state,
    save_state,
    update_best_score,
)
from games.session_menu import LOAD, NEW, QUIT, choose_session_action

GAME_ID = "minesweeper"
SAVE_VERSION = 1
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

    def chord(self, row: int, col: int) -> bool:
        """Reveal unflagged neighbors when a revealed number has enough flags.

        A chord is allowed only on a revealed numbered cell whose adjacent flag
        count exactly matches its mine hint. Incorrectly placed flags can leave
        a real mine unflagged; chording in that situation detonates that mine,
        matching the risk of the classic Minesweeper shortcut.

        Return True when the board changes, including a mine detonation.
        """
        if not self.in_bounds(row, col):
            raise ValueError("Cell outside board.")
        if self.lost or self.is_won():
            return False

        cell = (row, col)
        if cell not in self.revealed:
            return False

        required_flags = self.adjacent_mines(row, col)
        if required_flags <= 0:
            return False

        neighbors = self.neighbors(row, col)
        adjacent_flags = sum(neighbor in self.flags for neighbor in neighbors)
        if adjacent_flags != required_flags:
            return False

        targets = [
            neighbor
            for neighbor in neighbors
            if neighbor not in self.flags and neighbor not in self.revealed
        ]
        if not targets:
            return False

        mine_target = next((target for target in targets if target in self.mines), None)
        if mine_target is not None:
            self.revealed.add(mine_target)
            self.lost = True
            return True

        before = len(self.revealed)
        for target in targets:
            self.reveal(*target)
        return len(self.revealed) > before

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


def minesweeper_score(difficulty: Difficulty, actions: int) -> int:
    """Score a successful clear using board complexity and action efficiency."""
    if actions < 0:
        raise ValueError("actions cannot be negative.")
    safe_cells = difficulty.rows * difficulty.cols - difficulty.mines
    base = safe_cells * 10 + difficulty.mines * 25
    return max(base // 4, base - actions * 5)


def serialize_state(
    game: MinesweeperGame,
    difficulty: Difficulty,
    actions: int,
) -> dict[str, Any]:
    return {
        "version": SAVE_VERSION,
        "difficulty": {
            "name": difficulty.name,
            "rows": difficulty.rows,
            "cols": difficulty.cols,
            "mines": difficulty.mines,
        },
        "actions": actions,
        "mines_placed": game.mines_placed,
        "mines": [list(cell) for cell in sorted(game.mines)],
        "revealed": [list(cell) for cell in sorted(game.revealed)],
        "flags": [list(cell) for cell in sorted(game.flags)],
    }


def _decode_coords(value: Any, label: str) -> set[Coord]:
    if not isinstance(value, list):
        raise ValueError(f"Invalid saved {label}.")
    result: set[Coord] = set()
    for cell in value:
        if (
            not isinstance(cell, list)
            or len(cell) != 2
            or isinstance(cell[0], bool)
            or isinstance(cell[1], bool)
            or not isinstance(cell[0], int)
            or not isinstance(cell[1], int)
        ):
            raise ValueError(f"Invalid saved {label} coordinate.")
        result.add((cell[0], cell[1]))
    return result


def deserialize_state(state: dict[str, Any]) -> tuple[MinesweeperGame, Difficulty, int]:
    if state.get("version") != SAVE_VERSION:
        raise ValueError("Unsupported Minesweeper save version.")
    raw_difficulty = state.get("difficulty")
    if not isinstance(raw_difficulty, dict):
        raise ValueError("Invalid saved difficulty.")
    try:
        difficulty = Difficulty(
            str(raw_difficulty["name"]),
            int(raw_difficulty["rows"]),
            int(raw_difficulty["cols"]),
            int(raw_difficulty["mines"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid saved difficulty.") from exc
    if difficulty not in DIFFICULTIES.values():
        raise ValueError("Saved difficulty is not supported.")

    actions = state.get("actions")
    if isinstance(actions, bool) or not isinstance(actions, int) or actions < 0:
        raise ValueError("Invalid saved action count.")

    mines_placed = state.get("mines_placed")
    if not isinstance(mines_placed, bool):
        raise ValueError("Invalid saved mine-placement state.")
    mines = _decode_coords(state.get("mines", []), "mines")
    revealed = _decode_coords(state.get("revealed", []), "revealed")
    flags = _decode_coords(state.get("flags", []), "flags")

    if mines_placed:
        if len(mines) != difficulty.mines:
            raise ValueError("Saved mine count is invalid.")
        game = MinesweeperGame(
            difficulty.rows,
            difficulty.cols,
            difficulty.mines,
            mines=mines,
        )
    else:
        if mines:
            raise ValueError("Unplaced save cannot contain mines.")
        game = MinesweeperGame(difficulty.rows, difficulty.cols, difficulty.mines)

    for cell in mines | revealed | flags:
        if not game.in_bounds(*cell):
            raise ValueError("Saved coordinate is outside the board.")
    if revealed & flags:
        raise ValueError("Saved cells cannot be both revealed and flagged.")

    game.revealed = revealed
    game.flags = flags
    if game.is_won():
        raise ValueError("Saved Minesweeper game is already finished.")
    return game, difficulty, actions


def parse_command(raw: str) -> tuple[str, int | None, int | None]:
    """Parse a terminal command into action and zero-based coordinates."""
    parts = raw.strip().lower().split()
    if not parts:
        raise ValueError("Enter a command.")

    if parts[0] in {"q", "quit", "exit"}:
        if len(parts) != 1:
            raise ValueError("Quit command takes no coordinates.")
        return "quit", None, None
    if parts[0] in {"save", "sv"}:
        if len(parts) != 1:
            raise ValueError("Save command takes no coordinates.")
        return "save", None, None

    if len(parts) == 2 and all(part.isdigit() for part in parts):
        return "reveal", int(parts[0]) - 1, int(parts[1]) - 1

    if len(parts) == 3:
        action = parts[0]
        if action in {"r", "reveal", "open"}:
            normalized = "reveal"
        elif action in {"f", "flag"}:
            normalized = "flag"
        elif action in {"c", "chord"}:
            normalized = "chord"
        else:
            raise ValueError("Use R row col, F row col, C row col, SAVE, or Q.")

        if not parts[1].isdigit() or not parts[2].isdigit():
            raise ValueError("Row and column must be numbers.")

        return normalized, int(parts[1]) - 1, int(parts[2]) - 1

    raise ValueError("Use R row col, F row col, C row col, SAVE, or Q.")


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


def play_round(
    difficulty: Difficulty,
    game: MinesweeperGame | None = None,
    actions: int = 0,
) -> bool:
    """Play one round. Return False if the player quits the game."""
    game = game or MinesweeperGame(
        difficulty.rows,
        difficulty.cols,
        difficulty.mines,
    )

    print(
        f"\n{difficulty.name}: {difficulty.rows}x{difficulty.cols}, "
        f"{difficulty.mines} mines"
    )
    print(
        "Commands: R row col = reveal, F row col = flag, "
        "C row col = chord, SAVE = save, Q = quit"
    )
    print("Shortcut: entering just 'row col' reveals that cell.")
    print("Chord opens a revealed number's unflagged neighbors when its flag count matches.")
    print("The first revealed cell is always safe.\n")

    while not game.lost and not game.is_won():
        print(game.render())
        remaining = game.mine_count - len(game.flags)
        print(
            f"\nMines: {game.mine_count} | Flags: {len(game.flags)} "
            f"| Unflagged estimate: {remaining} | Actions: {actions}"
        )

        try:
            action, row, col = parse_command(input("Move: "))
        except ValueError as exc:
            print(f"\n{exc}\n")
            continue

        if action == "quit":
            return False
        if action == "save":
            try:
                save_state(GAME_ID, serialize_state(game, difficulty, actions))
                print("\nGame saved.\n")
            except ProgressDataError as exc:
                print(f"\nCould not save game: {exc}\n")
            continue

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
                actions += 1
                print("\nFlag placed.\n" if placed else "\nFlag removed.\n")
            continue

        if action == "chord":
            if game.chord(row, col):
                actions += 1
                print()
            else:
                print(
                    "\nChord requires a revealed numbered cell with exactly "
                    "the matching number of adjacent flags.\n"
                )
            continue

        if (row, col) in game.flags:
            print("\nRemove the flag before revealing that cell.\n")
            continue

        before = len(game.revealed)
        game.reveal(row, col)
        if len(game.revealed) != before or game.lost:
            actions += 1
        print()

    print(game.render(reveal_all=True))
    clear_save(GAME_ID)
    if game.lost:
        score = 0
        print("\nBoom. You hit a mine.")
    else:
        score = minesweeper_score(difficulty, actions)
        new_record = update_best_score(GAME_ID, score)
        print("\nYou cleared the minefield. You win.")
        if new_record:
            print("New Best Score!")
    print(f"Score: {score} | Best Score: {get_best_score(GAME_ID)}")
    return True


def _load_saved_game() -> tuple[MinesweeperGame, Difficulty, int] | None:
    state = load_state(GAME_ID)
    if state is None:
        return None
    try:
        return deserialize_state(state)
    except ValueError as exc:
        print(f"\nSaved game is invalid: {exc}")
        return None


def main() -> None:
    """Run the interactive terminal game."""
    print("=== Minesweeper ===")

    while True:
        action = choose_session_action(GAME_ID, "Minesweeper")
        if action == QUIT:
            print("Goodbye.")
            return

        if action == LOAD:
            loaded = _load_saved_game()
            if loaded is None:
                continue
            game, difficulty, actions = loaded
            print("\nSaved game loaded.")
        elif action == NEW:
            difficulty = choose_difficulty()
            if difficulty is None:
                print("Goodbye.")
                return
            game = None
            actions = 0
        else:
            continue

        if not play_round(difficulty, game, actions):
            print("\nGoodbye.")
            return

        again = input("\nPlay another round? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return
        print()


if __name__ == "__main__":
    main()
