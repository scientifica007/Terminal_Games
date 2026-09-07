# Linux standalone distribution

This document records the first Stage 3 desktop target for Terminal_Games.

## Scope

The initial standalone target is **GNU/Linux x86_64** only. The build produces a self-contained executable that does not require a separately installed Python interpreter.

The development package version is currently `1.2.0.dev0`; `v1.1.0` remains the latest official release and does not contain this desktop artifact.

## Build technology

The executable is frozen with pinned PyInstaller build tooling from:

```text
requirements/desktop-linux.txt
```

PyInstaller is a build-only dependency. Terminal_Games runtime dependencies remain empty.

The build command used by CI and local validation is:

```bash
python3 scripts/build_linux_desktop.py
```

The script enforces Linux x86_64, builds a one-file executable, validates `--version`, exercises launcher startup/quit, creates a versioned archive, and writes a SHA-256 manifest.

## Artifact layout

For product version `<version>`, the output is:

```text
desktop-dist/
├── SHA256SUMS-linux-x86_64.txt
└── terminal-games-<version>-linux-x86_64.tar.gz
```

The archive contains:

```text
terminal-games-<version>-linux-x86_64/
├── terminal-games
├── LICENSE
└── README.txt
```

The archive format is intentional: it preserves executable permissions and keeps the license and launch instructions next to the binary.

## CI baseline

The desktop build job uses the explicit GitHub-hosted `ubuntu-22.04` x64 runner. PyInstaller does not bundle glibc, so using an older supported build image improves compatibility with newer compatible GNU/Linux environments compared with building on the newest available image.

This is not a blanket compatibility claim for every distribution.

## Automated validation

CI requires all of the following before uploading `desktop-linux-dist`:

1. the normal Python 3.10–3.13 test matrix passes;
2. PyInstaller completes the one-file build;
3. the frozen executable reports the exact product version;
4. the frozen launcher displays the menu and exits cleanly on scripted `q` input;
5. the archive contains the executable, MIT license, and target README;
6. `sha256sum -c SHA256SUMS-linux-x86_64.txt` succeeds.

## Manual validation gate

The automated launcher smoke test is not a substitute for a real TTY. Before a stable release advertises the Linux standalone target, manually test the **exact CI-built artifact** on a real Linux terminal.

Minimum manual checks:

- checksum verification;
- archive extraction and executable permission;
- `./terminal-games --version`;
- launcher start/exit;
- Snake arrow input, timing, wrapping, save, and quit;
- Tetris movement/drop/pause/save/quit;
- Terminal Runner jump/timing/save/quit;
- shared progress remains in `~/.terminal_games/progress.json` or the explicit `TERMINAL_GAMES_DATA_DIR` override.

## Release integration

Pull requests and manual workflow runs build the desktop bundle without publishing it. Future stable `v*` tags, after passing the existing release guard, will require both the Python release artifacts and the Linux desktop artifacts before the GitHub Release publish job runs.

Windows, macOS, and Linux ARM are separate future targets and require their own build/test pipelines.
