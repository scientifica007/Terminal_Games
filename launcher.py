"""Terminal_Games launcher."""

from __future__ import annotations

from collections.abc import Callable

from games.tic_tac_toe import main as tic_tac_toe

Game = tuple[str, Callable[[], None]]

GAMES: dict[str, Game] = {
    "1": ("Tic-Tac-Toe", tic_tac_toe),
}


def main() -> None:
    print("=== Terminal Games ===")
    for key, (name, _) in GAMES.items():
        print(f"{key}. {name}")
    print("Q. Quit")

    while True:
        choice = input("\nSelect a game: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Goodbye.")
            return

        game = GAMES.get(choice)
        if game is None:
            print("Invalid selection.")
            continue

        name, run_game = game
        print(f"\nLaunching {name}...\n")
        run_game()
        return


if __name__ == "__main__":
    main()
