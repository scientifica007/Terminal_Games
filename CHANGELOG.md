# Changelog

All notable product-level changes should be recorded here. Terminal_Games uses Semantic Versioning for stable product releases.

## [1.1.0] - Unreleased

The repository is currently targeting `1.1.0`. Until the release is actually cut, Python package metadata uses the development version `1.1.0.dev0`.

### Added

- Terminal Runner, including selectable starting speeds, progression up to 10.00x, save/load support, buffered Best Score updates, and high-speed fairness coverage.
- A product packaging foundation using `pyproject.toml`.
- The canonical `terminal-games` console command.
- `python -m terminal_games` module launching.
- Product version reporting through `terminal-games --version`.
- Product/release strategy and installation documentation.
- A dedicated player-facing User Guide covering installation entry points, shared progress behavior, controls, scoring, and rules for all seven games.
- CI installation validation for the packaged command.

### Changed

- Minesweeper supports the Chord action for revealed numbered cells.
- Product versioning is now explicitly separate from per-game save-schema versions.
- The root README is now a concise product landing page that directs players to the User Guide and Installation Guide while keeping engineering documentation discoverable.

### Notes

- This section does not imply that `v1.1.0` has been tagged or published yet.
- No PyPI publication, standalone binary, or browser-hosted edition exists at this stage.

## Historical baseline: stable/v1.0.0

`stable/v1.0.0` is an immutable historical branch at commit:

```text
37ed53dd673338cf0d7464b60a0c8d0892d461dc
```

It includes the real-time Tetris implementation and predates the later Minesweeper Chord and Terminal Runner work.

This historical reference was created as a stable branch only. It was not retroactively published as a Git tag or GitHub Release, and this changelog does not claim otherwise.
