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

You can also run any game directly:

```bash
python3 -m games.tic_tac_toe
python3 -m games.connect_four
python3 -m games.minesweeper
python3 -m games.game_2048
python3 -m games.snake
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

### Minesweeper

A classic Minesweeper implementation with coordinate-driven terminal controls.

Difficulty levels:

- Beginner: 9x9 with 10 mines.
- Intermediate: 16x16 with 40 mines.
- Expert: 16x30 with 99 mines.

Features:

- First revealed cell is always safe; on standard boards its neighboring cells are protected too.
- Automatic flood-fill opening of connected empty areas.
- Flags for suspected mines.
- One-based row and column coordinates.
- Reveal shorthand by entering `row col`.
- Full board reveal after a win or loss.
- Replay and quit handling.

Minesweeper commands:

```text
R row col   reveal a cell
F row col   place or remove a flag
row col     reveal shorthand
Q           quit
```

### 2048

A terminal version of the classic 4x4 sliding tile puzzle.

Features:

- Custom `S`, `X`, `C`, `W` movement controls.
- Standard 4x4 board.
- Equal tiles merge only once per move.
- Score increases by the value of each newly merged tile.
- New tiles are `2` most of the time and occasionally `4`.
- Invalid or ineffective moves do not create a new tile.
- Reaching 2048 is announced, but play may continue beyond it.
- Automatic game-over detection when no legal move remains.
- Replay and quit handling.

2048 controls:

```text
S   move up
X   move down
C   move right
W   move left
Q   quit
```

### Snake

A real-time terminal Snake game with immediate keyboard input; movement does not require pressing Enter.

Features:

- 24x14 play field.
- Keyboard arrow controls, read directly from the terminal without Enter.
- Supports common POSIX CSI/SS3 arrow escape sequences and Windows arrow-key input.
- Three fixed speed levels: Relaxed, Normal, and Fast.
- The snake grows by one cell for every food item eaten.
- Score increases by 10 points per food item.
- Crossing any edge wraps the snake to the opposite side.
- Self-collision remains lethal, including after wrapping across an edge.
- Immediate 180-degree turns are blocked.
- Fixed-timestep movement, so rapid key presses do not increase game speed.
- ANSI redraw with terminal state restored after the round.
- Uses only the Python standard library.

Snake controls:

```text
↑   move up
↓   move down
→   move right
←   move left
Q   quit
```

The controls are read directly while the game is running; do not press Enter after an arrow key.

## Project structure

```text
Terminal_Games/
├── launcher.py
├── games/
│   ├── __init__.py
│   ├── connect_four.py
│   ├── game_2048.py
│   ├── minesweeper.py
│   ├── snake.py
│   └── tic_tac_toe.py
└── tests/
    ├── test_connect_four.py
    ├── test_game_2048.py
    ├── test_minesweeper.py
    ├── test_snake.py
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

Candidate terminal games include Hangman, Blackjack, Battleship, and terminal roguelikes.
