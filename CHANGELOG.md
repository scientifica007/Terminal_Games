# Changelog

All notable product-level changes should be recorded here. Terminal_Games uses Semantic Versioning for stable product releases.

## [1.2.0] - Unreleased

Development has resumed after the official `v1.1.0` release. Package metadata now uses `1.2.0.dev0` while Stage 3 desktop distribution is developed and validated.

### Added

- A Linux x86_64 standalone build path using pinned PyInstaller build tooling.
- A self-contained one-file executable packaged in a versioned `tar.gz` bundle with the MIT `LICENSE` and bundle-specific launch instructions.
- Target-specific SHA-256 verification for the Linux desktop archive.
- Automated frozen-binary validation covering `--version` and launcher startup/quit behavior.
- Unit tests for target gating, version extraction, PyInstaller command construction, bundle contents, executable permissions, and checksums.

### Changed

- The release workflow now builds the Linux x86_64 standalone bundle on relevant pull requests and manual dry runs.
- Future validated stable-tag releases are configured to attach the Linux desktop archive and its checksum alongside wheel/source artifacts.
- Linux desktop builds use the explicit `ubuntu-22.04` x64 runner rather than `ubuntu-latest` to keep a deliberately older glibc build baseline.

### Notes

- `1.2.0.dev0` is a development version, not a published stable release.
- `v1.1.0` remains the latest official release while this Stage 3 work is reviewed and manually tested.
- The first desktop target is Linux x86_64 only. Windows, macOS, and Linux ARM are not yet certified or distributed.
- No PyPI publication or browser-hosted edition exists at this stage.

## [1.1.0] - 2026-09-07

`v1.1.0` is the first productized Terminal_Games release. It was finalized after successful `1.1.0rc1` automated and manual validation, then published from the exact approved finalization commit through the permanent `stable/v1.1.0` branch, annotated `v1.1.0` tag, and GitHub Release.

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
- The release guard correctly rejected `1.1.0rc1` as a stable publication version.
- The finalized `1.1.0` state passed the same automated matrix and dry-run build.
- The pushed `v1.1.0` tag resolved to the exact approved finalization commit, passed the guarded publishing workflow, and produced the official GitHub Release.

### Notes

- The `v1.1.0` GitHub Release contains the Python wheel, source distribution, and SHA-256 checksum manifest.
- `v1.1.0` predates Stage 3 and therefore does not contain a standalone desktop binary.
- No PyPI publication or browser-hosted edition exists at this stage.

## Historical baseline: stable/v1.0.0

`stable/v1.0.0` is an immutable historical branch at commit:

```text
37ed53dd673338cf0d7464b60a0c8d0892d461dc
```

It includes the real-time Tetris implementation and predates the later Minesweeper Chord and Terminal Runner work.

This historical reference was created as a stable branch only. It was not retroactively published as a Git tag or GitHub Release, and this changelog does not claim otherwise.
