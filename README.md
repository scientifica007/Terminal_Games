# Terminal_Games

A collection of small, polished games designed to run directly in a terminal.

## Goals

- Keep games lightweight and easy to run.
- Prefer the Python standard library unless a game genuinely needs an external dependency.
- Support keyboard-driven terminal play with clear instructions and graceful input handling.
- Keep each game isolated so new games can be added without breaking existing ones.
- Share cross-game services such as persistence instead of reimplementing them in every game.
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

## Shared progress system

All current games use one shared persistence layer.

Before a round, each game presents the same session menu:

```text
N. New game
L. Load saved game
B. Best score
R. Reset
Q. Back
```

### Save

Each game has one local save slot containing the actual in-progress game state.

- Tic-Tac-Toe: type `SAVE` on your turn.
- Connect Four: type `SAVE` on your turn.
- Minesweeper: type `SAVE` at the move prompt.
- 2048: type `SAVE` instead of a movement command.
- Snake: press `S` while the game is running; no Enter is required. The Arabic-layout physical-S character `س` is also recognized.

Saving does not end the current game. Loading later returns to the saved position, score, difficulty/speed, and other state required by that game.

A completed game automatically invalidates its old save slot so a finished position cannot be loaded as an active game.

### Load

`Load saved game` resumes the game's single save slot. New games and saved games are deliberately separate: starting a new game does not silently destroy an older save; using Reset does.

### Best Score

Best Score is persistent and independent from the current save. It survives quitting the application and survives `Reset saved game only`.

Scoring is game-specific:

- **Tic-Tac-Toe:** win = 100, draw = 25, loss = 0. The computer is optimal, so a draw is a valid scored result.
- **Connect Four:** a win has a difficulty-weighted base (Easy 100, Medium 250, Hard 500) plus an efficiency bonus for winning in fewer human moves; a draw receives one fifth of the difficulty base.
- **Minesweeper:** a successful clear is scored from board complexity (`safe cells × 10 + mines × 25`) with a 5-point deduction per effective action, bounded so a successful clear always retains at least 25% of its base value.
- **2048:** the standard merge score is used directly.
- **Snake:** each food item is worth 10 points.

### Reset

`Reset` is deliberately explicit:

```text
1. Delete saved game only (keep Best Score)
2. Delete saved game and Best Score
N. Cancel
```

Clearing Best Score requires an additional `RESET` confirmation. This prevents an ordinary restart from erasing a record accidentally.

### Storage location and integrity

Progress is written to:

```text
~/.terminal_games/progress.json
```

The data lives outside the repository, so playing does not create untracked Git files. Writes use a temporary file followed by an atomic replacement to reduce the risk of a half-written save.

For tests or advanced use, the storage directory can be overridden with:

```bash
TERMINAL_GAMES_DATA_DIR=/some/path python3 launcher.py
```

The persistence format is versioned and validated when loaded. Invalid/corrupted progress is reported rather than silently overwritten.

## Future player profiles / usernames

The persistence schema reserves profile metadata, but username/account code is intentionally not implemented yet.

The planned model is a lightweight **local player profile**: a username selects whose saves and Best Scores are active. It is meant to separate several players on the same computer, not to act as authentication or a security boundary.

The design, migration strategy, Unicode username rules, privacy model, and proposed storage architecture are documented in [`docs/player-profile-design.md`](docs/player-profile-design.md).

## Games

### Tic-Tac-Toe

A single-player Tic-Tac-Toe implementation against an optimal minimax computer opponent.

Features:

- Numbered 1-9 board controls.
- Human plays `X`; computer plays `O`.
- Input validation and quit command.
- Optimal computer strategy.
- Save / Load / Best Score / Reset support.
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
- Save / Load preserves board, difficulty, and move count.
- Best Score rewards difficulty and efficient wins.
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
- Save / Load preserves mines, revealed cells, flags, difficulty, and effective action count.
- Best Score rewards harder boards and efficient clears.
- Full board reveal after a win or loss.
- Replay and quit handling.

Minesweeper commands:

```text
R row col   reveal a cell
F row col   place or remove a flag
row col     reveal shorthand
SAVE        save current game
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
- Save / Load preserves board, score, and 2048-announcement state.
- Persistent Best Score updates as the score grows.
- Reaching 2048 is announced, but play may continue beyond it.
- Automatic game-over detection when no legal move remains.
- Replay and quit handling.

2048 controls:

```text
S      move up
X      move down
C      move right
W      move left
SAVE   save current game
Q      quit
```

### Snake

A real-time terminal Snake game with immediate keyboard input; movement does not require pressing Enter.

Features:

- 24x14 play field.
- Keyboard arrow controls, read directly from the terminal without Enter.
- Supports common POSIX CSI/SS3 arrow escape sequences and Windows arrow-key input.
- Three speed levels: Relaxed, Normal, and Fast.
- Horizontal speed values are preserved; vertical ticks are slowed by a 2x terminal-cell aspect-ratio compensation so movement looks more consistent on typical terminal fonts.
- The snake grows by one cell for every food item eaten.
- Score increases by 10 points per food item.
- Save / Load preserves the snake body, direction, food, score, and selected speed.
- Persistent Best Score updates during the live round.
- Crossing any edge wraps the snake to the opposite side.
- Self-collision remains lethal, including after wrapping across an edge.
- Immediate 180-degree turns are blocked.
- Fixed-timestep movement, so rapid key presses do not increase game speed.
- `Q`, `Esc`, and `Ctrl+C` can exit cleanly; the Arabic physical-Q character `ض` is also recognized when an Arabic keyboard layout is active.
- `S` / Arabic-layout `س` saves immediately without Enter.
- ANSI redraw with terminal state restored after the round.
- Uses only the Python standard library.

Snake controls:

```text
↑       move up
↓       move down
→       move right
←       move left
S       save
Q / Esc quit
```

The controls are read directly while the game is running; do not press Enter after an arrow key or Save key.

The complete engineering record of the Snake implementation—including failed approaches, terminal-input bugs, root causes, fixes, design reversals, regression rules, and lessons for future real-time terminal games—is documented in [`docs/snake-development-retrospective.md`](docs/snake-development-retrospective.md).

## Project structure

```text
Terminal_Games/
├── launcher.py
├── docs/
│   ├── player-profile-design.md
│   └── snake-development-retrospective.md
├── games/
│   ├── __init__.py
│   ├── connect_four.py
│   ├── game_2048.py
│   ├── minesweeper.py
│   ├── progress.py
│   ├── session_menu.py
│   ├── snake.py
│   └── tic_tac_toe.py
└── tests/
    ├── test_connect_four.py
    ├── test_game_2048.py
    ├── test_minesweeper.py
    ├── test_progress.py
    ├── test_progress_integration.py
    ├── test_snake.py
    └── test_tic_tac_toe.py
```

## Tests

Run all tests with:

```bash
python3 -m unittest discover -s tests -v
```

The persistence tests use `TERMINAL_GAMES_DATA_DIR` with temporary directories so they never touch the player's real save file.

## Design rules for new games

A new game should:

1. expose a `main()` function and live in its own module under `games/`;
2. keep reusable game logic separable from terminal I/O;
3. use `games.progress` and `games.session_menu` for Save / Load / Best Score / Reset rather than creating another storage format;
4. define and document a meaningful scoring rule if it participates in Best Score;
5. version and validate its own saved-state payload;
6. add save round-trip and scoring tests in addition to ordinary game-logic tests.

Shared terminal utilities can be introduced under a dedicated package when at least two games need them.

## Roadmap

Before adding another game, the persistence feature should be manually tested on the real Ubuntu terminal, especially Save/Load for Snake and Reset behavior. Candidate future games include Hangman, Blackjack, Battleship, and terminal roguelikes.
