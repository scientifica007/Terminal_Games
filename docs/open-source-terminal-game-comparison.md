# Open-source terminal game comparison

## Purpose

This document compares the six games in `Terminal_Games` with representative open-source implementations of the same games that are designed for terminal or console play.

The goal is not to rank projects by size, age, popularity, or visual polish. The goal is to identify architectural choices, algorithms, terminal-I/O techniques, persistence approaches, and gameplay features that can improve future work in this repository.

No source code from the compared projects is copied into `Terminal_Games`. The comparison is based on reading their public source and documentation.

## Evaluation snapshot

`Terminal_Games` baseline used for this comparison:

- repository: <https://github.com/scientifica007/Terminal_Games>
- branch: `main`
- commit: `37ed53dd673338cf0d7464b60a0c8d0892d461dc`
- Python target: 3.10+
- production dependencies: Python standard library only

External projects were selected using these criteria:

1. source is publicly accessible;
2. the project has an explicit open-source license;
3. the relevant game can be played in a terminal/console, rather than being only a graphical application;
4. the implementation exposes enough source to make a meaningful engineering comparison;
5. where several candidates existed, the example with the most useful contrast to our implementation was preferred.

A public repository without an explicit license was not treated as a primary open-source reference for this study.

## Selected references

| Game | External reference | License | Evaluated commit | Main contrast |
| --- | --- | --- | --- | --- |
| Tic-Tac-Toe | [Cledersonbc/tic-tac-toe-minimax](https://github.com/Cledersonbc/tic-tac-toe-minimax) | GPL-3.0 | `10168a7d9f8a7cca18a47acfdf0aed356515514b` | compact console minimax implementation |
| Connect Four | [duilio/c4](https://github.com/duilio/c4) | MIT | `6dcde8316603192b0bc713d1bedb94290d123a9d` | AI-engine architecture with stronger search infrastructure |
| Minesweeper | [M-Mueller/Minesweeper](https://github.com/M-Mueller/Minesweeper) | GPL-3.0 | `5fb3399902a5e9613c04e56b54eec942c8631363` | curses UI, precomputed hints, chord-like reveal |
| 2048 | [bfontaine/term2048](https://github.com/bfontaine/term2048) | MIT | `6f2d7fce0bbbf00a217a907dd72db3f95d54c6b3` | mature terminal package with immediate keys and save/resume |
| Snake | [asiddiqi18/Snake](https://github.com/asiddiqi18/Snake) | MIT | `8881b18f1e1bd7f319bf5684d817c58ab31b584b` | curses-based real-time loop sized to the terminal |
| Tetris | [wpdevelopment11/blocks](https://github.com/wpdevelopment11/blocks) | MIT | `e47a3be464e21a19077b1ac3ffc611264939bc5b` | `blessed` rendering, colors, and ghost piece |

The commit hashes above make the observations reproducible even if the external repositories change later.

---

## 1. Tic-Tac-Toe

### External implementation

The Python version in `Cledersonbc/tic-tac-toe-minimax` is a small console program centered on recursive minimax. Its board is a mutable 3x3 list using numeric values for human, computer, and empty cells. The search mutates a candidate cell, recursively evaluates it, and then restores the cell before exploring the next move.

Its terminal interface is deliberately simple: it clears the console using the platform's `clear` or `cls` command, prints the board, and asks the user to choose a numpad position from 1 to 9. On a completely empty board, the computer can choose an initial cell randomly; subsequent decisions use minimax.

### `Terminal_Games` implementation

Our `games/tic_tac_toe.py` uses the same fundamental full-game-tree minimax strategy, but its terminal and application responsibilities are broader:

- the board is a flat nine-cell list of `X`, `O`, and spaces;
- winning lines are represented as data in `WINNING_LINES`;
- terminal positions are depth-adjusted so the AI prefers faster wins and delays losses;
- the human always plays `X` and moves first;
- the game participates in the shared launcher and session menu;
- the current board can be saved and validated on load;
- completed rounds update a persistent Best Score;
- the game logic is covered by repository tests.

### Comparison

Algorithmically, both implementations are intentionally straightforward because Tic-Tac-Toe is small enough for exhaustive minimax. The external project is a good example of keeping the minimax teaching implementation compact. Our version is more suitable for a multi-game application because persistence, validation, scoring, replay, and shared services are explicit concerns rather than being mixed into one standalone script.

The depth-adjusted terminal score in our version is also a useful refinement: two theoretically winning branches are not treated as identical if one wins sooner.

### Lessons

There is little reason to make our Tic-Tac-Toe search more complicated. Alpha-beta pruning or memoization could reduce redundant work, but the state space is so small that the additional machinery would provide little player-visible benefit. The stronger direction is to preserve the current separation between pure game logic and application services.

---

## 2. Connect Four

### External implementation

`duilio/c4` is substantially more AI-oriented than our game. It separates board representation, evaluation, move ordering, caches, game orchestration, and several search engines. Its available engine strategies include progressively stronger techniques such as Negamax, alpha-beta pruning, transposition-table caching, iterative deepening, and Principal Variation Search. It also contains arena/best-move tooling intended for comparing engines rather than only playing a casual human-vs-computer round.

A notable design difference is its preference for immutable board states: a move produces another board state, which reduces undo-related mutation hazards at the cost of additional allocation. NumPy is part of the project's dependency model.

### `Terminal_Games` implementation

Our `games/connect_four.py` is optimized for a compact, dependency-free single-player game:

- classic 6x7 board;
- human `X` versus computer `O`;
- Easy, Medium, and Hard difficulty levels;
- Medium/Hard use depth-limited minimax with alpha-beta pruning;
- center-first move ordering improves pruning and reflects Connect Four strategy;
- a heuristic evaluates four-cell windows plus center control;
- the search mutates the board and explicitly undoes each simulated move;
- Save/Load preserves board, difficulty, and human move count;
- Best Score rewards difficulty and efficient wins.

### Comparison

This is the largest AI capability gap among the six comparisons. `duilio/c4` has a search-engine framework suitable for algorithm experimentation and stronger play. Our implementation has a much smaller search stack, but that is consistent with its purpose: predictable response time, three user-facing difficulty levels, no third-party dependencies, and integration with the common Terminal_Games persistence model.

The immutable-board approach in `duilio/c4` makes recursive search easier to reason about. Our mutate/undo approach is more allocation-efficient, but every search path must restore state correctly. The existing tests are therefore important.

### Lessons

If Hard difficulty needs to become materially stronger, the first high-value enhancement would be a transposition table keyed by board state. Iterative deepening would be the next useful step because it allows the engine to return the strongest fully searched result within a time budget. Principal Variation Search is interesting but is not justified until the simpler optimizations have measurable value.

The external project's arena tooling is also a useful testing idea: computer-vs-computer batches could quantify whether a heuristic or search change actually improves play instead of relying only on subjective manual testing.

---

## 3. Minesweeper

### External implementation

`M-Mueller/Minesweeper` separates its game state into mine, flag, and precomputed-hint tables. Cell state is represented by an enum with Unknown, Marked, and Revealed values. Revealing a zero-hint cell recursively opens neighboring cells.

It also implements a useful chord-like behavior: when an already revealed numbered cell has the expected number of marked neighbors, the remaining neighboring cells can be revealed together. An `auto_mark` operation marks all remaining mines once every non-mine cell has been exposed.

The curses interface provides a more interactive TUI than a coordinate-command prompt. However, its random board creation places mines when the board is created; the core implementation does not defer mine placement to guarantee a safe first reveal.

### `Terminal_Games` implementation

Our `games/minesweeper.py` deliberately emphasizes safety and deterministic rules:

- Beginner 9x9/10, Intermediate 16x16/40, and Expert 16x30/99 presets;
- mines are not generated until the first reveal;
- the first cell is guaranteed safe and, when board capacity allows, its surrounding cells are protected too;
- flood fill uses an explicit `deque` rather than recursive calls;
- revealed cells and flags are sets of coordinates;
- command-based input uses one-based row/column coordinates;
- the complete state can be saved and validated, including placed mines, revealed cells, flags, difficulty, and action count;
- successful clears receive a difficulty/efficiency-based Best Score.

### Comparison

The external version offers a richer direct interaction model through curses and has chord behavior that experienced Minesweeper players expect. Our version has stronger first-click guarantees and a persistence model designed for the wider game collection.

The iterative breadth-first flood fill in our version also avoids recursion-depth concerns and makes the expansion mechanism explicit.

### Lessons

A chord command is the clearest feature worth considering. It could be implemented as an explicit terminal command and tested independently without adopting curses or changing the existing coordinate UI.

The current first-reveal-safe design should be retained. It is a player-facing rule improvement over generating the complete minefield before the first action.

---

## 4. 2048

### External implementation

`bfontaine/term2048` is a mature terminal package with separate board, game, keypress, and UI modules. Its movement algorithm follows the standard pattern: compact a row/column, merge adjacent equals, compact again, and add a new tile only when the board actually changed.

The package supports immediate keyboard controls, including arrows and vi-style keys, terminal colors, persistent best score, and a stored session that can be resumed. It uses separate files in the user's home directory for scores and the saved board. Its score increment method updates the in-memory best value, while persistence happens at explicit lifecycle points such as save/pause, interrupt, or game completion.

This last point is particularly relevant to our own 2048 performance incident: the external design also avoids writing the best-score file after every scoring merge.

### `Terminal_Games` implementation

Our `games/game_2048.py` has similar core movement semantics but a different application architecture:

- one pure `merge_line` function is reused to derive all four directions through reversal/transposition;
- the standard merged-tile score is used;
- a 2 is generated with 90% probability and a 4 with 10%;
- ineffective moves do not spawn a new tile;
- the user-requested `S/X/C/W` controls are retained;
- Save/Load uses the shared versioned JSON persistence layer;
- loaded data is validated, including tile powers of two and game-over states;
- the saved payload includes whether the 2048 target announcement has already occurred;
- `BestScoreTracker` keeps record changes in memory during active play and flushes only at Save, Quit, or Game Over.

### Comparison

The core board algorithms converge because the game rules strongly constrain a correct implementation. The major difference is infrastructure. `term2048` is a dedicated package with a richer terminal presentation and immediate arrow/vi-key input. Our implementation is one game inside a dependency-free suite with shared persistence and shared session behavior.

Our current persistence format is more structured and defensive: one versioned JSON store, schema validation, and atomic replacement are used across all games instead of game-specific plain-text files.

### Lessons

The strongest confirmation from this comparison is architectural: Best Score should remain memory-buffered during play. Reintroducing synchronous record writes into the move path would repeat the exact latency problem we already diagnosed.

Arrow or vi-style movement aliases could be added in the future, but they should remain aliases rather than replacing the existing `S/X/C/W` scheme chosen for this project.

---

## 5. Snake

### External implementation

`asiddiqi18/Snake` uses Python `curses` for immediate keyboard input and screen drawing. Its playfield is derived from the current terminal dimensions, the snake wraps at the edges, direct reverse movement is blocked, and self-collision ends the game. It also supports pause through a blocking curses input.

The game is modularized into game, snake, apple, tile, configuration, and entry-point modules. Its README explicitly targets a curses-capable terminal environment; the implementation is not designed around the cross-platform Windows input path that our code supports.

### `Terminal_Games` implementation

Our `games/snake.py` takes a lower-level approach:

- fixed 24x14 logical board gives stable gameplay independent of terminal window size;
- POSIX input is read in cbreak mode with `select`, `os.read`, and explicit escape-sequence decoding;
- Windows arrow input is handled separately with `msvcrt`;
- CSI, SS3, and modified arrow sequences are recognized;
- UTF-8 input allows Arabic physical-key equivalents for Save and Quit;
- the game has Relaxed, Normal, and Fast speed modes;
- vertical movement receives a timing multiplier to compensate for typical terminal cell aspect ratios;
- fixed-timestep movement prevents rapid input from accelerating the simulation;
- Save/Load preserves body, direction, food, score, and speed;
- Best Score is buffered in memory and persisted only at safe points.

### Comparison

Curses removes a large amount of terminal-management code and gives the external implementation an adaptive full-terminal play area with concise input handling. Our implementation accepts more complexity in exchange for direct control over portability, escape-sequence behavior, Unicode keys, timing, and testable transformation functions.

The fixed-size board is not inherently better or worse than terminal-sized play. It makes difficulty and collision geometry reproducible, while an adaptive board makes better use of available screen space.

### Lessons

The most important internal improvement is already visible in our own repository: Tetris introduced `games/terminal_input.py`, while Snake still contains its earlier private key-reader implementation. Snake should eventually migrate to the shared reader, but only in a separate regression-tested PR because terminal input is high-risk and Snake is currently stable.

Adaptive sizing and Pause are reasonable optional features. Neither is important enough to justify replacing the current input architecture with curses.

---

## 6. Tetris

### External implementation

`wpdevelopment11/blocks` is a terminal Tetris implementation built around the `blessed` library. It uses classes for tetrominoes, the grid, game state, and terminal drawing. Tetromino shapes are represented as small text matrices and rotations are computed using matrix transpose/reversal.

Its presentation is richer than ours: pieces are colored and a ghost/shadow piece shows where the active tetromino will land. It also displays score, cleared lines, level, and the next piece.

The implementation uses a 10-cell-wide board, selects the next tetromino with ordinary random choice, increases level as cleared-line count grows, and accelerates its tick interval. Rotation is accepted only if the rotated matrix fits at the current position; the inspected implementation does not apply the generic wall/floor kicks used by our game.

Its scoring model also differs from ours: it includes row-completion scoring and additional adjacency-based scoring rather than our classic line-clear table plus drop-distance points.

### `Terminal_Games` implementation

Our `games/tetris.py` is designed around reproducible mechanics and the shared Terminal_Games architecture:

- standard visible board size of 10x20;
- seven-bag randomizer so all seven tetrominoes occur once per bag;
- four stored rotation states per tetromino;
- small generic wall/floor kick offsets;
- Down performs soft drop and awards one point per moved row;
- Space performs hard drop and awards two points per moved row;
- line clears score 40/100/300/1200 multiplied by `level + 1`;
- level advances every ten lines and gravity accelerates to a lower timing bound;
- next-piece preview and pause;
- immediate keyboard input through the reusable `games.terminal_input.KeyReader`;
- versioned Save/Load preserves locked board, active piece, next piece, remaining seven-bag, score, and lines;
- Best Score remains memory-only in the timing loop and is flushed at safe points;
- an explicit Save resets the gravity deadline after filesystem I/O so saving cannot consume the player's remaining drop interval.

### Comparison

Our implementation has the stronger gameplay-randomization and persistence model. Seven-bag generation avoids long droughts that ordinary independent random choice can produce, and saving the remaining bag preserves the future randomization state well enough for a consistent resumed session.

The external project has the stronger presentation. Color and a ghost piece convey state more efficiently than plain fixed-width symbols.

### Lessons

A ghost piece is the most attractive feature to borrow conceptually. It can be implemented with the existing standard-library renderer by projecting a copy of the active piece downward and drawing the landing cells with a distinct plain-text symbol. No `blessed` dependency is required.

Color could also be added with ANSI sequences, but it should remain optional and degrade cleanly on terminals where color is undesirable.

---

## Cross-project architecture

### Where `Terminal_Games` is stronger

The clearest distinction is that this repository is not six unrelated scripts. It has common application infrastructure:

- one launcher and a consistent game-entry contract (`main()`);
- one shared Save/Load/Best Score/Reset experience;
- one versioned persistence store outside the repository;
- validation before saved state is accepted;
- atomic replacement for progress-file writes;
- `BestScoreTracker` to prevent synchronous persistence from entering real-time or frequently updated gameplay paths;
- standard-library-only production code;
- reusable game logic separated sufficiently from terminal I/O for unit testing;
- CI across supported Python versions;
- a reusable immediate-key reader now available for future real-time games.

Several external projects are deeper in one specific area, but none of the selected references is solving exactly the same multi-game product problem.

### Where the external references are stronger

The external projects expose several useful specialist techniques:

| Area | Strong reference | What it demonstrates |
| --- | --- | --- |
| Search strength | `duilio/c4` | transposition tables, iterative deepening, PVS, engine comparison |
| Minesweeper interaction | `M-Mueller/Minesweeper` | chord-like reveal and curses navigation |
| 2048 terminal UX | `bfontaine/term2048` | immediate arrows/vi keys, colors, mature package/resume workflow |
| Screen adaptation | `asiddiqi18/Snake` | curses-sized playfield using current terminal dimensions |
| Tetris presentation | `wpdevelopment11/blocks` | color and ghost-piece projection |
| Minimal algorithm demonstration | `Cledersonbc/tic-tac-toe-minimax` | compact, readable recursive minimax |

## Recommended follow-up work

Priority should be based on player value and regression risk rather than copying features because another project has them.

1. **Minesweeper chord command — high value, low-to-medium risk.** Add an explicit command to reveal unflagged neighbors when the number of surrounding flags matches a revealed cell's number. Keep first-click safety unchanged.
2. **Tetris ghost piece — high value, low-to-medium risk.** Compute projected landing cells in pure logic and render them with a distinct symbol. This improves planning without changing scoring or physics.
3. **Snake input consolidation — engineering value, medium risk.** Move Snake to `games.terminal_input.KeyReader` in a dedicated PR with regression tests for CSI/SS3 arrows, UTF-8 keys, timing, Save, Quit, and terminal restoration.
4. **Connect Four transposition table — conditional value, medium risk.** Add only if Hard difficulty needs stronger/deeper search. Measure node count and response time before and after.
5. **Connect Four engine-vs-engine harness — testing value, low product risk.** A small simulation harness could objectively compare AI revisions without becoming a player-facing dependency.
6. **Optional richer terminal presentation — lower priority.** ANSI colors, adaptive dimensions, or additional key aliases can improve UX, but they should not compromise the current standard-library-only and cross-platform goals.

## Decisions not recommended from this comparison

- Do not replace the shared persistence system with separate per-game files.
- Do not perform Best Score writes on every score increase.
- Do not introduce `curses`, `blessed`, NumPy, or another dependency solely because a reference project uses it; each dependency would need a concrete benefit that outweighs portability and installation cost.
- Do not replace Tetris seven-bag randomization with independent random choice.
- Do not remove Minesweeper first-click safety.
- Do not change the user-selected 2048 `S/X/C/W` controls merely to match another implementation; additional aliases can be considered separately.

## Licensing note

This document is an engineering comparison, not a source-code import. No external implementation code is incorporated here.

The selected projects use MIT or GPL-3.0 licenses. If implementation code is ever copied or adapted rather than independently reimplemented from the underlying game rules or engineering ideas, the applicable license obligations must be reviewed before that code enters this repository. In particular, GPL-licensed source should not be treated as if it had MIT-style reuse terms.

## Source index

- Tic-Tac-Toe: <https://github.com/Cledersonbc/tic-tac-toe-minimax>
  - inspected Python implementation: `py_version/minimax.py`
  - snapshot: `10168a7d9f8a7cca18a47acfdf0aed356515514b`
- Connect Four: <https://github.com/duilio/c4>
  - inspected package structure, board/search-engine documentation, and test module
  - snapshot: `6dcde8316603192b0bc713d1bedb94290d123a9d`
- Minesweeper: <https://github.com/M-Mueller/Minesweeper>
  - inspected `minesweeper.py` and repository documentation
  - snapshot: `5fb3399902a5e9613c04e56b54eec942c8631363`
- 2048: <https://github.com/bfontaine/term2048>
  - inspected `term2048/board.py`, `term2048/game.py`, package structure, and documentation
  - snapshot: `6f2d7fce0bbbf00a217a907dd72db3f95d54c6b3`
- Snake: <https://github.com/asiddiqi18/Snake>
  - inspected `src/game.py`, source layout, and documentation
  - snapshot: `8881b18f1e1bd7f319bf5684d817c58ab31b584b`
- Tetris: <https://github.com/wpdevelopment11/blocks>
  - inspected `blocks.py`, license header, and documentation
  - snapshot: `e47a3be464e21a19077b1ac3ffc611264939bc5b`

## Summary

The comparison supports the current overall direction of `Terminal_Games`: small dependency-free game engines, a shared persistence/service layer, and explicit testing are a strong fit for a terminal game collection.

The external projects are most valuable as focused references rather than replacements for our architecture. The strongest ideas to carry forward are Minesweeper chord interaction, Tetris ghost projection, optional Connect Four search caching/measurement, and eventually consolidating Snake onto the shared terminal-input layer. The 2048 comparison independently reinforces the performance lesson already learned in this project: persistent state belongs at explicit safe points, not inside a latency-sensitive gameplay path.
