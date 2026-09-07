# Changelog

All notable product-level changes should be recorded here. Terminal_Games uses Semantic Versioning for stable product releases.

## [1.1.0] - 2026-09-07

The `1.1.0` source state is finalized after successful `1.1.0rc1` automated and manual validation. Package metadata now uses the stable version `1.1.0`. Publication of the permanent stable branch, `v1.1.0` tag, and GitHub Release remains a separate explicitly approved release-management step.

### Added

- Terminal Runner, including selectable starting speeds, progression up to 10.00x, save/load support, buffered Best Score updates, and high-speed fairness coverage.
- A product packaging foundation using `pyproject.toml`.
- The canonical `terminal-games` console command.
- `python -m terminal_games` module launching.
- Product version reporting through `terminal-games --version`.
- Product/release strategy and installation documentation.
- A dedicated player-facing User Guide covering installation entry points, shared progress behavior, controls, scoring, and rules for all seven games.
- CI installation validation for the packaged command.
- Release automation with a non-publishing manual build path, release-tag validation, source/wheel artifact builds, SHA-256 checksums, and GitHub Release publication for validated stable tags.
- MIT License with SPDX package metadata and license-file inclusion in built distributions.

### Changed

- Minesweeper supports the Chord action for revealed numbered cells.
- Product versioning is now explicitly separate from per-game save-schema versions.
- The root README is now a concise product landing page that directs players to the User Guide and Installation Guide while keeping engineering documentation discoverable.
- Product metadata advanced from development build `1.1.0.dev0` to release candidate `1.1.0rc1`, then to stable `1.1.0` after candidate validation.

### Validation

- `1.1.0rc1` passed the complete Python 3.10–3.13 CI matrix.
- The release dry run built and reinstalled the candidate wheel and source distribution, generated SHA-256 checksums, and uploaded the validated artifacts without publishing.
- The CI-built wheel was manually checksum-verified, installed in an isolated virtual environment, and smoke-tested across all seven games.
- The release guard correctly rejected `1.1.0rc1` as a stable publication version and already validates an exact stable `v1.1.0` / `1.1.0` match.

### Notes

- This finalization entry does not itself imply that the `v1.1.0` Git tag or GitHub Release has already been created.
- No PyPI publication, standalone binary, or browser-hosted edition exists at this stage.

## Historical baseline: stable/v1.0.0

`stable/v1.0.0` is an immutable historical branch at commit:

```text
37ed53dd673338cf0d7464b60a0c8d0892d461dc
```

It includes the real-time Tetris implementation and predates the later Minesweeper Chord and Terminal Runner work.

This historical reference was created as a stable branch only. It was not retroactively published as a Git tag or GitHub Release, and this changelog does not claim otherwise.
