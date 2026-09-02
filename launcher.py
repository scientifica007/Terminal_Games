"""Terminal_Games launcher."""

from __future__ import annotations

from collections.abc import Callable

from games.connect_four import main as connect_four
from games.game_2048 import main as game_2048
from games.minesweeper import main as minesweeper
from games.tic_tac_toe import main as tic_tac_toe

Game = tuple[str, Callable[[], None]]

GAMES: dict[str, Game] = {
    "1": ("Tic-Tac-Toe", tic_tac_toe),
    "2": ("Connect Four", connect_four),
    "3": ("Minesweeper", minesweeper),
    "4": ("2048", game_2048),
}


def main() -> None:
    while True:
        print("=== Terminal Games ===")
        for key, (name, _) in GAMES.items():
            print(f"{key}. {name}")
        print("Q. Quit")

        choice = input("\nSelect a game: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Goodbye.")
            return

        game = GAMES.get(choice)
        if game is None:
            print("\nInvalid selection.\n")
            continue

        name, run_game = game
        print(f"\nLaunching {name}...\n")
        run_game()
        print("\nReturning to game menu...\n")


if __name__ == "__main__":
    main()
