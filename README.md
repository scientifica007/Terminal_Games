# Terminal_Games

A collection of small, polished games designed to run directly in a terminal.

## Goals

- Keep games lightweight and easy to run.
- Prefer the Python standard library unless a game genuinely needs an external dependency.
- Support keyboard-driven terminal play with clear instructions and graceful input handling.
- Keep each game isolated so new games can be added without breaking existing ones.
- Add automated tests for reusable game logic.

## Requirements

- Python 3.10+

No third-party packages are required for the current games.

## Run

From the repository root:

```bash
python launcher.py
```

You can also run a game directly:

```bash
python -m games.tic_tac_toe
```

## Games

### Tic-Tac-Toe

A single-player Tic-Tac-Toe implementation against an optimal minimax computer opponent.

Features:

- Numbered 1-9 board controls.
- Human plays `X`; computer plays `O`.
- Input validation and quit command.
- Optimal computer strategy.
- Replay support.

## Project structure

```text
Terminal_Games/
├── launcher.py
├── games/
│   ├── __init__.py
│   └── tic_tac_toe.py
└── tests/
    └── test_tic_tac_toe.py
```

## Tests

Run all tests with:

```bash
python -m unittest discover -s tests -v
```

## Design rule for new games

A new game should expose a `main()` function and live in its own module under `games/`. Shared terminal utilities can be introduced later under a dedicated package when at least two games need them.

## Roadmap

Candidate terminal games include Snake, Minesweeper, Hangman, 2048, Connect Four, Blackjack, Battleship, and terminal roguelikes.
