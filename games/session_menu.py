"""Shared New/Load/Best/Reset menu for persistent games."""

from __future__ import annotations

from games.progress import (
    ProgressDataError,
    get_best_score,
    has_saved_game,
    reset_game_data,
)

NEW = "new"
LOAD = "load"
QUIT = "quit"


def choose_session_action(game_id: str, game_name: str) -> str:
    """Return NEW, LOAD, or QUIT after handling informational/reset actions."""
    while True:
        try:
            best = get_best_score(game_id)
            saved = has_saved_game(game_id)
        except ProgressDataError as exc:
            print(f"\nProgress data error: {exc}")
            print("Fix or remove the local progress file before continuing.")
            return QUIT

        print(f"\n--- {game_name} ---")
        print(f"Best score: {best}")
        print(f"Saved game: {'available' if saved else 'none'}")
        print("N. New game")
        print("L. Load saved game")
        print("B. Best score")
        print("R. Reset")
        print("Q. Back")

        choice = input("\nChoice: ").strip().lower()
        if choice in {"n", "new", "1"}:
            return NEW
        if choice in {"l", "load", "2"}:
            if not saved:
                print("\nNo saved game exists.")
                continue
            return LOAD
        if choice in {"b", "best", "3"}:
            print(f"\nBest score for {game_name}: {best}")
            continue
        if choice in {"r", "reset", "4"}:
            _reset_menu(game_id)
            continue
        if choice in {"q", "quit", "exit", "back"}:
            return QUIT
        print("\nInvalid selection.")


def _reset_menu(game_id: str) -> None:
    print("\nReset options:")
    print("1. Delete saved game only (keep Best Score)")
    print("2. Delete saved game and Best Score")
    print("N. Cancel")

    while True:
        choice = input("Reset: ").strip().lower()
        if choice in {"n", "no", "cancel", "q"}:
            print("Reset cancelled.")
            return
        if choice == "1":
            reset_game_data(game_id, include_best=False)
            print("Saved game reset. Best Score preserved.")
            return
        if choice == "2":
            confirm = input("Type RESET to confirm clearing all data for this game: ").strip()
            if confirm == "RESET":
                reset_game_data(game_id, include_best=True)
                print("Saved game and Best Score reset.")
            else:
                print("Reset cancelled.")
            return
        print("Choose 1, 2, or N.")
