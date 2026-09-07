# Terminal_Games

A collection of polished keyboard-driven games that run directly in a terminal.

Terminal_Games is both an actively developed game project and a versioned product. Development continues on new games, mechanics, terminal-input work, persistence, testing, and distribution while stable editions remain permanently identifiable through release branches, tags, and GitHub Releases.

## Current product status

The latest official release is:

```text
v1.1.0
```

`v1.1.0` is published as a GitHub Release and is anchored to the permanent `stable/v1.1.0` branch and `v1.1.0` Git tag. The current development line has advanced to:

```text
1.2.0.dev0
```

Stage 3 development is adding the first standalone desktop target: a self-contained Linux x86_64 bundle that does not require a separate Python installation. Until that work is reviewed, manually tested, merged, and included in a later stable release, `v1.1.0` remains the latest official release and does not contain a standalone desktop executable.

The project is not published to PyPI.

## Requirements

For source/package use:

- Python 3.10+
- An interactive terminal for real-time games

The game runtime has no third-party Python dependencies. The Linux standalone builder uses a pinned build-only dependency and does not add a runtime dependency to Terminal_Games.

## Quick start

Run directly from a source checkout:

```bash
python3 launcher.py
```

Or install the checkout as a local Python package:

```bash
python3 -m pip install .
terminal-games
```

Check the installed version:

```bash
terminal-games --version
```

You can also launch the installed package with:

```bash
python3 -m terminal_games
```

The official `v1.1.0` source/wheel artifacts are available from the repository's GitHub Releases page. See the [installation guide](docs/installation.md) for release downloads, local installation, `pipx`, editable installs, and the Linux standalone build/validation path.

## Games

| # | Game | Type |
|---|---|---|
| 1 | Tic-Tac-Toe | turn-based strategy vs optimal minimax AI |
| 2 | Connect Four | turn-based strategy with Easy / Medium / Hard AI |
| 3 | Minesweeper | coordinate-driven puzzle with flags and Chord |
| 4 | 2048 | sliding-tile puzzle |
| 5 | Snake | real-time arcade game with wrap-around movement |
| 6 | Tetris | real-time falling-block game with seven-bag randomization |
| 7 | Terminal Runner | real-time endless side-scrolling runner up to 10.00x speed |

For controls, scoring, saves, difficulty, and game-specific rules, use the **[Terminal_Games User Guide](docs/user-guide.md)**.

## Shared progress system

All games use one shared persistence architecture for:

```text
New game
Load saved game
Best Score
Reset
```

Each game has one active save slot and one persistent Best Score. Progress is stored outside the repository and outside standalone application bundles at:

```text
~/.terminal_games/progress.json
```

Writes use temporary-file replacement to reduce the risk of a partially written progress file. Real-time games keep timing-sensitive Best Score updates out of the hot loop and flush them at explicit safe I/O points.

The storage directory can be overridden for tests or isolated play:

```bash
TERMINAL_GAMES_DATA_DIR=/some/path terminal-games
```

See the [User Guide](docs/user-guide.md) for the player-facing Save / Load / Best Score / Reset behavior.

## Documentation

### Player and product documentation

- **[User Guide](docs/user-guide.md)** — how to launch, save, load, reset, and play every game.
- **[Installation Guide](docs/installation.md)** — release downloads, source/package installation, `pipx`, and Linux standalone validation.
- **[Changelog](CHANGELOG.md)** — product-development history.
- **[Product / Release Strategy](docs/product-release-strategy.md)** — versioning, release channels, desktop distribution, and planned browser architecture.

### Engineering and design records

- [Terminal Runner technical guide](docs/terminal-runner.md)
- [Terminal Runner open-source comparison](docs/terminal-runner-open-source-comparison.md)
- [Snake development retrospective](docs/snake-development-retrospective.md)
- [Future player-profile design](docs/player-profile-design.md)

## Development

The repository keeps each game in its own module under `games/`, with reusable cross-game services for persistence, session menus, and real-time terminal input.

A new game should:

1. expose a `main()` function;
2. keep reusable game logic separable from terminal I/O;
3. use the shared progress/session infrastructure rather than inventing another save format;
4. define a meaningful scoring rule when it participates in Best Score;
5. version and validate its saved-state payload;
6. add game-logic, persistence, and scoring tests;
7. keep disk I/O out of timing-sensitive gameplay loops.

The project intentionally prefers the Python standard library unless an external dependency provides clear product value. Desktop bundlers are build tooling, not game runtime dependencies.

## Tests

Run the full test suite with:

```bash
python3 -m unittest discover -s tests -v
```

CI installs the package and validates the product command before running the test suite across supported Python versions. The release workflow also builds and smoke-tests the Linux x86_64 standalone artifact when relevant packaging or game code changes.

## License

Terminal_Games is licensed under the MIT License. See [LICENSE](LICENSE) for the full terms.

## Project direction

Terminal_Games is not intended to stop at a fixed set of examples. New games, gameplay experiments, terminal techniques, and engineering improvements will continue while stable product editions are cut as versioned releases.

The Python package foundation and tagged GitHub Release path are established. Current product work is Stage 3 Linux standalone distribution; later stages can extend tested desktop targets and add browser play through an isolated server-side terminal session.
