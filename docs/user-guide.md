# Terminal_Games User Guide

This is the player-facing guide for Terminal_Games. It explains how to launch the collection, use the shared save system, and play each included game.

For installation details, including local package installation and `pipx`, see [`installation.md`](installation.md).

## Product status

Terminal_Games is being prepared as a versioned installable product while development continues.

The current development package version is:

```text
1.1.0.dev0
```

This is a development build toward the planned `v1.1.0` product release. It is not yet a published PyPI package, standalone desktop download, Git tag, or GitHub Release.

## Requirements

- Python 3.10 or newer.
- An interactive terminal.
- A keyboard for the real-time games.

The current game runtime has no third-party Python dependencies.

## Quick start

### Run from a source checkout

From the repository root:

```bash
python3 launcher.py
```

On systems where Python is exposed as `python` instead of `python3`:

```bash
python launcher.py
```

### Run as an installed local package

From the repository root, install the checkout:

```bash
python3 -m pip install .
```

Then launch from any directory:

```bash
terminal-games
```

You can also use:

```bash
python3 -m terminal_games
```

Check the installed version with:

```bash
terminal-games --version
```

`pip install terminal-games` from PyPI is **not** an advertised installation method yet; the project has not been published there.

## Main game menu

Launching Terminal_Games presents the collection menu:

```text
=== Terminal Games ===
1. Tic-Tac-Toe
2. Connect Four
3. Minesweeper
4. 2048
5. Snake
6. Tetris
7. Terminal Runner
Q. Quit
```

Enter the number of the game you want to play. When a game ends or returns, control goes back to this menu.

## Shared session menu

Every game uses the shared progress system. Before starting a round, the game presents actions equivalent to:

```text
N. New game
L. Load saved game
B. Best score
R. Reset
Q. Back
```

### New game

Starts a new round. Starting a new game does not silently delete an older save slot.

### Load saved game

Each game has one local save slot. Loading restores the game-specific state required to continue the saved round.

A finished game clears its stale active save so a completed position cannot later be loaded as an in-progress game.

### Best Score

Best Score is persistent and separate from the active save slot.

For timing-sensitive games, record updates can be held in memory during live play and written at safe points such as Save, quit, or game over. This avoids disk access interrupting a real-time frame loop.

### Reset

Reset is deliberately explicit:

```text
1. Delete saved game only (keep Best Score)
2. Delete saved game and Best Score
N. Cancel
```

Deleting Best Score requires an additional `RESET` confirmation.

## Progress and save location

By default, Terminal_Games stores shared progress outside the repository at:

```text
~/.terminal_games/progress.json
```

The file contains versioned data for saves and Best Scores. Writes use a temporary file followed by atomic replacement to reduce the risk of leaving a half-written progress file.

Advanced users and tests can override the data directory:

```bash
TERMINAL_GAMES_DATA_DIR=/some/path terminal-games
```

or, when running from source:

```bash
TERMINAL_GAMES_DATA_DIR=/some/path python3 launcher.py
```

## Real-time controls and terminals

Snake, Tetris, and Terminal Runner read keys immediately. Do **not** press Enter after arrow keys, Space, Save, Pause, or Quit controls in those games.

These games are intended for an interactive terminal and use ANSI terminal control sequences for redraw and cursor handling.

Common real-time quit controls include:

```text
Q
Esc
Ctrl+C
```

Where documented below, Arabic-layout physical-key equivalents are also accepted:

```text
س   physical S key -> Save
ح   physical P key -> Pause
ض   physical Q key -> Quit
```

---

# Game guides

## 1. Tic-Tac-Toe

### Goal

Complete a row, column, or diagonal of three `X` marks before the computer completes three `O` marks.

The human plays `X`. The computer plays `O` using an optimal minimax strategy, so a draw is a legitimate successful defensive outcome.

### Controls

The board uses positions `1` through `9`. Enter the number of the empty square where you want to place `X`.

During your turn:

```text
1-9    place X
SAVE   save the current game
Q      quit the round
```

### Score

```text
Win    100
Draw    25
Loss     0
```

The saved game preserves the board and the state required to continue the round.

---

## 2. Connect Four

### Goal

Drop your `X` pieces into the 6-by-7 board and form four connected pieces horizontally, vertically, or diagonally before the computer does so with `O`.

### Difficulty

New games offer:

```text
Easy
Medium
Hard
```

Medium and Hard use depth-limited minimax with alpha-beta pruning. Higher difficulties carry higher potential scores.

### Controls

Columns are numbered `1` through `7`.

```text
1-7    drop X into that column
SAVE   save the current game
Q      quit the round
```

A full column cannot accept another piece.

### Score

A win uses a difficulty-weighted base score plus an efficiency bonus for winning in fewer human moves:

```text
Easy      100 base
Medium    250 base
Hard      500 base
```

A draw receives one fifth of the selected difficulty's base score.

---

## 3. Minesweeper

### Goal

Reveal every non-mine cell without detonating a mine. Flags can mark suspected mines.

### Difficulty

```text
Beginner       9x9   10 mines
Intermediate  16x16  40 mines
Expert        16x30  99 mines
```

The first revealed cell is always safe. On standard boards, the game also attempts to protect its neighboring cells during initial mine placement.

### Coordinates

Rows and columns are one-based. For example, `4 7` means row 4, column 7.

### Commands

```text
R row col       reveal a cell
F row col       place or remove a flag
C row col       chord a revealed numbered cell
row col         reveal shorthand
SAVE            save the current game
Q               quit the round
```

`REVEAL`, `FLAG`, and `CHORD` are also accepted in their corresponding command forms.

### Chord

Chord is a classic Minesweeper shortcut. Use it on a revealed numbered cell after the number of adjacent flags exactly matches that cell's hint.

When the flag count matches, Chord opens all adjacent cells that are still hidden and unflagged as one action.

Chord does **not** verify that your flags are correct. If you have placed the right number of flags on the wrong cells, an unflagged mine can be opened and the round can be lost.

If the adjacent flag count does not match the number, the command makes no board change.

### Score

A successful clear is based on board complexity and action efficiency:

```text
base = safe_cells * 10 + mines * 25
score = max(base / 4 floor, base - actions * 5)
```

Only successful clears produce a positive completion score; hitting a mine gives a score of zero.

---

## 4. 2048

### Goal

Slide equal tiles together to merge them and build larger values. Reaching `2048` is announced, but you may continue playing beyond it.

The round ends when no legal move remains.

### Controls

Terminal_Games intentionally uses this keyboard layout:

```text
S      move up
X      move down
C      move right
W      move left
SAVE   save the current game
Q      quit the round
```

These controls are not WASD; note the exact mapping above.

An ineffective move does not spawn a new tile.

### Score

The standard merge score is used: when tiles merge, the value of the newly created tile is added to the score.

The saved game preserves the board, score, and whether the 2048 announcement has already occurred.

---

## 5. Snake

### Goal

Guide the snake to food, grow the body, and avoid colliding with yourself.

Crossing an edge wraps the snake to the opposite side. Wall collision is therefore not lethal, but self-collision is.

Immediate 180-degree direction reversals are blocked.

### Speed

New games offer three speed levels:

```text
Relaxed
Normal
Fast
```

### Controls

Controls are immediate; do not press Enter.

```text
Up Arrow       move up
Down Arrow     move down
Right Arrow    move right
Left Arrow     move left
S              save
Q / Esc        quit
Ctrl+C         quit cleanly
```

Arabic physical-key equivalents include Save (`س`) and Quit (`ض`).

### Score

Each food item is worth:

```text
10 points
```

The saved game preserves the snake body, direction, food position, score, and selected speed.

---

## 6. Tetris

### Goal

Move and rotate falling tetrominoes to complete horizontal rows. Completed rows disappear. The game ends when a new active piece can no longer enter the play field.

The board is 10 columns by 20 rows and uses all seven standard tetrominoes through a seven-bag randomizer.

### Controls

Controls are immediate; do not press Enter.

```text
Left / Right   move the active piece
Down           soft drop
Up             rotate clockwise
Space          hard drop
P              pause / resume
S              save
Q / Esc        quit
```

Arabic physical-key equivalents are supported for Save (`س`), Pause (`ح`), and Quit (`ض`).

### Progression

The level increases every 10 cleared lines. Gravity accelerates as the level rises, subject to a lower timing bound.

The HUD includes a `Next` preview for the upcoming tetromino.

### Score

Line clears use the classic values multiplied by the current level factor:

```text
1 line      40 * (level + 1)
2 lines    100 * (level + 1)
3 lines    300 * (level + 1)
4 lines   1200 * (level + 1)
```

Drops also score:

```text
Soft drop    +1 per row
Hard drop    +2 per row
```

The saved game preserves the board, active piece, next piece, remaining seven-bag, score, and cleared-line count.

---

## 7. Terminal Runner

### Goal

Survive an endless side-scrolling course. The runner remains near a fixed horizontal position while the world moves from right to left.

Jump over solid obstacles and pits while the game progressively accelerates.

### Starting speed

New runs offer four starting presets:

```text
1. Relaxed  1.00x
2. Normal   1.50x
3. Fast     2.00x
4. Expert   3.00x
```

All presets continue accelerating in `0.25x` increments and can eventually reach the same `10.00x` maximum speed.

Higher-speed levels deliberately last longer before the next increase, giving the player more time to adapt.

### Controls

Controls are immediate; do not press Enter.

```text
Space / Up    jump
P             pause / resume
S             save the current run
Q / Esc       quit
```

Arabic physical-key equivalents are supported for Pause (`ح`), Save (`س`), and Quit (`ض`).

### Obstacles

The game contains eight obstacle families:

```text
crate
rock
spikes
pillar
barrier
stacked blocks
double blocks
pit
```

More complex obstacles unlock as progression advances.

### Score

Score is independent from the level timer:

```text
score = floor(distance * 10) + obstacles_passed * 25
```

The HUD shows Score, Best Score, selected speed mode, Level, current speed multiplier, time until the next speed increase, and obstacles passed.

For a deeper technical description of fairness, high-speed substeps, persistence migration, and obstacle generation, see [`terminal-runner.md`](terminal-runner.md).

---

# Troubleshooting

## `terminal-games: command not found`

The console command exists only after installing the checkout into the active Python environment.

From the repository root:

```bash
python3 -m pip install .
```

Then try:

```bash
terminal-games --version
terminal-games
```

You can always run the source checkout directly with:

```bash
python3 launcher.py
```

## A real-time game does not read keys correctly

Use an interactive terminal rather than piping input/output through another process. Arrow-key and immediate-key handling depends on terminal input facilities.

If you are testing through an unusual terminal emulator, SSH client, IDE console, or multiplexer, compare behavior with a standard local terminal before reporting an input bug.

## The screen redraw looks corrupted

The real-time games rely on ANSI terminal control sequences. Use a terminal emulator with normal ANSI cursor-control support and give the game enough visible rows and columns to render its board.

## I want a clean test save directory

Set `TERMINAL_GAMES_DATA_DIR` to another directory before launching:

```bash
TERMINAL_GAMES_DATA_DIR=/tmp/terminal-games-test terminal-games
```

This keeps the normal `~/.terminal_games/progress.json` untouched.

## A saved game is reported as invalid

Terminal_Games validates saved-state payloads instead of silently accepting malformed or incompatible state. Keep the reported error if you need to file a bug report.

# Version and release information

To see the installed product version:

```bash
terminal-games --version
```

Product versions and individual game save-schema versions are separate concepts. A product release can change without every game's save format changing.

Release history and development changes are recorded in [`../CHANGELOG.md`](../CHANGELOG.md).

# More documentation

- [Installation guide](installation.md)
- [Product and release strategy](product-release-strategy.md)
- [Terminal Runner technical guide](terminal-runner.md)
- [Snake development retrospective](snake-development-retrospective.md)
- [Terminal Runner open-source comparison](terminal-runner-open-source-comparison.md)
- [Future player-profile design](player-profile-design.md)
