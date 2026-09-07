# Installing and launching Terminal_Games

Terminal_Games is being prepared as a versioned installable product while preserving the existing source-development workflow.

## Current product status

The current package metadata reports:

```text
1.1.0rc1
```

This is the first release candidate for the planned `v1.1.0` product release. It is intended for final validation and is not yet the stable release. The project is not yet published to PyPI and does not yet have a standalone desktop binary or a stable `v1.1.0` GitHub Release.

## Requirements

- Python 3.10 or newer.
- An interactive terminal for the real-time games.

The game runtime has no third-party Python dependencies.

## Run directly from a source checkout

The existing workflow remains supported:

```bash
cd Terminal_Games
python3 launcher.py
```

No gameplay behavior is changed by the packaging layer.

## Install the checkout as a Python package

From the repository root:

```bash
python3 -m pip install .
```

Then launch from any working directory with:

```bash
terminal-games
```

Check the installed product version with:

```bash
terminal-games --version
```

Expected release-candidate output:

```text
terminal-games 1.1.0rc1
```

You can also launch the installed package as a module:

```bash
python3 -m terminal_games
```

## Isolated local installation with pipx

If `pipx` is already installed on the computer, it can install the local checkout into an isolated environment:

```bash
pipx install .
terminal-games
```

This does **not** mean `pipx install terminal-games` is available from PyPI. A package-index publication has not been made yet.

## Development/editable installation

For packaging or CLI development, an editable installation is convenient:

```bash
python3 -m pip install -e .
terminal-games --version
```

Changes in the checkout are then visible without reinstalling the package.

## Progress data

Installation does not relocate game saves into the Python package. Progress continues to use the existing external data directory:

```text
~/.terminal_games/progress.json
```

Tests and isolated environments can continue overriding the storage directory with `TERMINAL_GAMES_DATA_DIR`.

## Platform status

The current automated test matrix certifies Python 3.10 through 3.13 on Linux. Packaging is intentionally not yet advertised as fully certified on Windows or macOS; dedicated CI and real-time terminal testing should be added before those platforms are listed as supported product downloads.

## Release-candidate validation

The repository already has guarded release automation that can run without publishing. The dry-run path:

1. runs the supported Python test matrix;
2. builds the source distribution and wheel;
3. installs the built wheel and re-validates the installed command and metadata;
4. generates SHA-256 checksums;
5. uploads the resulting distribution files as a GitHub Actions artifact.

For `1.1.0rc1`, this path is used to validate the candidate without creating a Git tag or GitHub Release.

## Remaining distribution stages

After a release candidate is approved, the stable release process finalizes the package version as `1.1.0`, records the release date, creates an approved stable branch and `v1.1.0` tag, and lets the guarded release workflow build and attach source/wheel/checksum artifacts to the GitHub Release.

Later product stages can add:

1. standalone downloadable executables, beginning with a tested Linux target;
2. dedicated Windows/macOS certification when those platforms are actually tested;
3. browser play through an isolated server-side PTY connected to a terminal frontend over WebSocket.

See [`product-release-strategy.md`](product-release-strategy.md) for the release and browser architecture decisions.
