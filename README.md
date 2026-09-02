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

On Linux or macOS, from the repository root:

```bash
python3 launcher.py
```

On systems where Python is exposed as `python`, you can use:

```bash
python launcher.py
```

You can also run either game directly:

```bash
python3 -m games.tic_tac_toe
python3 -m games.connect_four
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

### Connect Four

A single-player Connect Four implementation on the classic 6-by-7 board.

Features:

- Numbered 1-7 column controls.
- Human plays `X`; computer plays `O`.
- Easy, Medium, and Hard difficulty levels.
- Medium and Hard use depth-limited Minimax with alpha-beta pruning.
- Center-aware move ordering and heuristic board evaluation.
- Detection of horizontal, vertical, and diagonal wins.
- Full-column validation, replay, and quit handling.

## Project structure

```text
Terminal_Games/
├── launcher.py
├── games/
│   ├── __init__.py
│   ├── connect_four.py
│   └── tic_tac_toe.py
└── tests/
    ├── test_connect_four.py
    └── test_tic_tac_toe.py
```

## Tests

Run all tests with:

```bash
python3 -m unittest discover -s tests -v
```

## Design rule for new games

A new game should expose a `main()` function and live in its own module under `games/`. Shared terminal utilities can be introduced later under a dedicated package when at least two games need them.

## Roadmap

Candidate terminal games include Minesweeper, Hangman, 2048, Snake, Blackjack, Battleship, and terminal roguelikes.
