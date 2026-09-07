# Installing and launching Terminal_Games

Terminal_Games supports source execution, local Python-package installation, official GitHub Release artifacts, and an in-development Linux standalone build path.

## Current product status

The latest official release is:

```text
v1.1.0
```

`v1.1.0` is published as a GitHub Release and is tied to the permanent `stable/v1.1.0` branch and `v1.1.0` tag. Its release assets are the Python wheel, source distribution, and SHA-256 checksum manifest.

The current development package metadata reports:

```text
1.2.0.dev0
```

Stage 3 development adds a Linux x86_64 standalone bundle. That bundle is a development/validation artifact until it is manually tested, merged, and included in a later stable GitHub Release. The existing `v1.1.0` release does **not** contain a standalone desktop executable.

The project is not published to PyPI.

## Requirements

### Source or Python-package use

- Python 3.10 or newer.
- An interactive terminal for the real-time games.

The game runtime has no third-party Python dependencies.

### Linux standalone bundle

The resulting standalone executable does not require Python to be installed. The first desktop target is Linux x86_64 and is built on Ubuntu 22.04. Real-time games still require an interactive terminal/TTY.

PyInstaller is used only as build tooling and is pinned in `requirements/desktop-linux.txt`; it is not a Terminal_Games runtime dependency.

## Official v1.1.0 GitHub Release

The official release page is:

```text
https://github.com/scientifica007/Terminal_Games/releases/tag/v1.1.0
```

It contains:

- `terminal_games-1.1.0-py3-none-any.whl`
- `terminal_games-1.1.0.tar.gz`
- `SHA256SUMS.txt`

These are Python distribution artifacts, not standalone desktop binaries.

## Run directly from a source checkout

The historical workflow remains supported:

```bash
cd Terminal_Games
python3 launcher.py
```

No gameplay behavior is changed by the packaging/distribution layers.

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

On the current development branch the expected output is:

```text
terminal-games 1.2.0.dev0
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

This does **not** mean `pipx install terminal-games` is available from PyPI. A package-index publication has not been made.

## Development/editable installation

For packaging or CLI development, an editable installation is convenient:

```bash
python3 -m pip install -e .
terminal-games --version
```

Changes in the checkout are then visible without reinstalling the package.

## Build the Linux x86_64 standalone bundle locally

This is a **build/development** workflow. It requires Python on the build machine, but the resulting executable is self-contained.

Create an isolated build environment and install the pinned desktop build dependency:

```bash
cd Terminal_Games
python3 -m venv /tmp/terminal-games-desktop-build
source /tmp/terminal-games-desktop-build/bin/activate
python3 -m pip install -r requirements/desktop-linux.txt
```

Build and automatically smoke-test the frozen executable:

```bash
python3 scripts/build_linux_desktop.py
```

The build script:

1. rejects non-Linux and non-x86_64 targets;
2. builds a PyInstaller one-file executable;
3. verifies `./terminal-games --version` against the product version;
4. launches the frozen menu and exercises a clean `q` exit;
5. packages the executable with `LICENSE` and Linux bundle instructions;
6. generates a target-specific SHA-256 manifest.

The resulting files are written under:

```text
desktop-dist/
```

For the current development version, the archive is named:

```text
terminal-games-1.2.0.dev0-linux-x86_64.tar.gz
```

Verify it:

```bash
cd desktop-dist
sha256sum -c SHA256SUMS-linux-x86_64.txt
```

Extract it:

```bash
tar -xzf terminal-games-1.2.0.dev0-linux-x86_64.tar.gz
cd terminal-games-1.2.0.dev0-linux-x86_64
./terminal-games --version
./terminal-games
```

When finished with the build environment:

```bash
deactivate
rm -rf /tmp/terminal-games-desktop-build
```

## CI-built Linux standalone artifact

The release workflow builds the same Linux x86_64 bundle on an explicit `ubuntu-22.04` GitHub-hosted x64 runner for relevant pull requests and manual dry runs. The job uploads a `desktop-linux-dist` Actions artifact containing:

- the versioned Linux `tar.gz` bundle;
- `SHA256SUMS-linux-x86_64.txt`.

This CI artifact is the preferred object for manual pre-merge testing because it is the exact bundle produced by the automation that future stable-tag releases will use.

Automated smoke tests cannot certify timing-sensitive TTY interaction. Before the first stable release that includes the Linux desktop asset, the CI-built bundle should be extracted on a real Linux terminal and manually tested, especially with Snake, Tetris, and Terminal Runner.

## Progress data

Neither package installation nor standalone bundling relocates game saves into the application files. Progress continues to use:

```text
~/.terminal_games/progress.json
```

Tests and isolated environments can override the storage directory with `TERMINAL_GAMES_DATA_DIR`.

## Platform status

Current source/package CI exercises Python 3.10 through 3.13 on Linux.

The first standalone target is deliberately narrower:

- OS family: GNU/Linux
- architecture: x86_64
- CI build image: Ubuntu 22.04
- real-time input requirement: interactive terminal/TTY

Building on Ubuntu 22.04 rather than `ubuntu-latest` provides an older glibc baseline for better forward compatibility with newer GNU/Linux systems. This does not certify every distribution.

Windows, macOS, and Linux ARM remain unsupported as standalone download targets until dedicated build jobs and real terminal tests exist for them.

## Release validation

The guarded release workflow now has three validated artifact paths:

1. Python test matrix and package metadata validation;
2. source/wheel build, reinstall validation, and SHA-256 manifest;
3. Linux x86_64 standalone build, frozen-CLI smoke test, archive, and target-specific checksum.

On pull requests and manual workflow runs, these are non-publishing dry runs. On a future explicitly approved stable `v*` tag, the release guard must first accept the exact stable version/tag match. Only then does the publish job create the GitHub Release and attach both Python artifacts and the validated Linux desktop artifacts.

## Remaining distribution stages

After Linux x86_64 is manually validated and released, later work can add:

1. additional Linux compatibility testing where useful;
2. Windows standalone builds and terminal-input certification;
3. macOS standalone builds and terminal-input certification;
4. Linux ARM if there is a concrete target/user need;
5. browser play through an isolated server-side PTY connected to a terminal frontend over WebSocket.

See [`product-release-strategy.md`](product-release-strategy.md) for the release and browser architecture decisions.
