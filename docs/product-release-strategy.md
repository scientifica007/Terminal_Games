# Terminal_Games product and release strategy

## Purpose

Terminal_Games remains an active personal development playground: new games, experiments, refactors, gameplay ideas, and distribution work should continue on ordinary feature branches. Productization must not slow that work down or force every experiment to become part of a public release immediately.

At the same time, players should have clearly identifiable stable editions that can be installed, launched, and revisited later. The project therefore uses a dual-track model: continuous development plus versioned product releases.

## Development track versus product track

The repository keeps the existing development discipline:

- `main` is the current integrated development line after reviewed/tested pull requests.
- Feature work happens on independent branches and is merged only after testing and explicit approval.
- Stable release references are created from known-good commits rather than by moving an old stable branch.

A product release adds three distinct references:

1. a permanent branch such as `stable/v1.1.0` for long-term maintenance/reference;
2. an immutable Git tag such as `v1.1.0` identifying the release commit;
3. a GitHub Release named for the same version, containing release notes and downloadable artifacts.

These are not interchangeable. A stable branch is a maintenance reference; a tag is the immutable source identity; a GitHub Release is the user-facing distribution record.

`v1.1.0` is the first fully productized Terminal_Games release. Its stable branch, tag, and GitHub Release were created from the exact approved finalization commit:

```text
6d0f10ace9b141acee3c107b0b6309ef738aa815
```

The older `stable/v1.0.0` branch remains an immutable historical baseline and was never retroactively converted into a tag or GitHub Release.

## Versioning policy

Terminal_Games uses Semantic Versioning for product releases:

- **MAJOR**: incompatible product-level changes or deliberately broken compatibility;
- **MINOR**: new games or substantial backward-compatible features, including a meaningful new distribution capability;
- **PATCH**: backward-compatible fixes and small corrections.

After publishing `v1.1.0`, the development line advances to the next planned minor-development version:

```text
1.2.0.dev0
```

This prevents post-release `main` changes from continuing to claim the already-published `1.1.0` identity. Development and pre-release versions remain non-publishable through the stable release guard.

Product versioning is separate from each game's saved-state schema. For example, the product can move from 1.1.0 to 1.2.0 while Terminal Runner's save payload remains version 3. Save-schema versions change only when persistence compatibility requires them.

## Product identity and entry points

The canonical installed command is:

```text
terminal-games
```

The historical developer/source entry point remains supported:

```text
python3 launcher.py
```

The Python package also supports:

```text
python3 -m terminal_games
```

and exposes a product version through:

```text
terminal-games --version
```

Packaging and desktop distribution must remain adapters around the current launcher. They must not change game behavior merely to satisfy bundling conventions.

## Distribution stages

### Stage 1: Python package foundation — complete

The product layer provides:

- `pyproject.toml` package metadata;
- a single source of truth for the product version;
- the `terminal-games` console command;
- `python3 -m terminal_games` support;
- installation instructions from a source checkout;
- automated tests for version/CLI behavior;
- CI validation that the repository can actually be installed as a package.

No PyPI publication is implied. Commands such as `pipx install terminal-games` must not be advertised until a package is actually published under that name.

### Stage 2: release automation — complete

Release automation lives in `.github/workflows/release.yml` and has deliberately different dry-run and publishing behavior.

A manual `workflow_dispatch` run and relevant pull-request runs are non-publishing. They execute the supported Python test matrix and build/validate release artifacts without creating a GitHub Release.

A push of a tag beginning with `v` enters the publishing path only after validation succeeds. Before publication, `scripts/release_guard.py` requires:

- an exact stable `MAJOR.MINOR.PATCH` package version;
- a tag exactly equal to `v<package-version>`.

A development version, pre-release version, malformed stable version, or mismatched tag fails before publication.

For `v1.1.0`, this process successfully:

1. ran the complete unit-test suite on Python 3.10 through 3.13;
2. validated the exact `v1.1.0` / `1.1.0` match;
3. built source and wheel distributions;
4. installed the built wheel and re-validated command/version/license metadata;
5. generated SHA-256 checksums;
6. uploaded validated workflow artifacts;
7. created the official GitHub Release and attached the validated Python artifacts.

The workflow does **not** create Git tags or stable branches. Those remain explicit release-management actions from an approved commit. The workflow also does not publish to PyPI.

### Release-candidate validation

A release candidate is an explicit pre-release package state used to validate the exact product intended for a stable release without publishing that stable release prematurely.

For `v1.1.0`, `1.1.0rc1` validation included:

1. the complete automated test suite on Python 3.10 through 3.13;
2. the release-workflow dry run;
3. checksum verification of the built wheel and source distribution;
4. installation of the CI-built wheel in an isolated virtual environment;
5. manual launch and smoke testing of all seven games, including Snake, Tetris, and Terminal Runner;
6. review of README, installation documentation, changelog, and release claims;
7. verification that the release guard rejected the pre-release version for stable publication.

The same pattern should be reused for future stable releases: automated artifact validation first, then manual testing of the exact CI-built artifact before permanent release references are created.

### Release finalization

After candidate validation succeeds, a separate finalization change sets package metadata to the exact stable version, updates version-sensitive tests and documentation, and records the release date in the changelog.

For `v1.1.0`, finalization produced the approved commit `6d0f10ace9b141acee3c107b0b6309ef738aa815`. Release management then created `stable/v1.1.0` and the annotated `v1.1.0` tag on that exact commit. Pushing the tag activated the guarded publishing workflow and produced the official GitHub Release.

Future releases should preserve this order and exact-commit discipline.

### Stage 3: standalone desktop artifacts — Linux x86_64 first

The target user experience is a downloadable artifact that does not require Git knowledge and does not require a separately installed Python interpreter.

The first implementation deliberately targets only:

```text
GNU/Linux x86_64
```

#### Bundling technology

The Linux executable is built with PyInstaller `6.22.2`, pinned in:

```text
requirements/desktop-linux.txt
```

PyInstaller is a build-only dependency. Terminal_Games runtime package dependencies remain empty.

The builder uses PyInstaller `--onefile` mode and the existing `terminal_games/__main__.py` entry point. No alternate gameplay launcher is introduced.

The resulting release unit is a versioned archive rather than a naked browser-downloaded executable:

```text
terminal-games-<version>-linux-x86_64.tar.gz
```

The archive contains:

- `terminal-games` — the self-contained executable;
- `LICENSE` — Terminal_Games MIT terms;
- `README.txt` — target-specific launch, persistence, and compatibility instructions.

A separate target-specific checksum manifest is generated:

```text
SHA256SUMS-linux-x86_64.txt
```

Using an archive preserves the executable permission bit and provides a natural place for the license and launch instructions.

#### Linux compatibility baseline

The desktop build job runs on the explicit GitHub-hosted:

```text
ubuntu-22.04
```

x64 runner rather than `ubuntu-latest`.

PyInstaller does not bundle the GNU/Linux C library (`glibc`), so binaries built on newer systems may fail on older systems. Building on the older Ubuntu 22.04 baseline improves forward compatibility with newer compatible GNU/Linux systems. This is still not a promise that every Linux distribution is certified.

The build script rejects non-Linux and non-x86_64 machines so an artifact cannot silently acquire the wrong platform label.

#### Automated desktop validation

`scripts/build_linux_desktop.py` performs more than compilation. It:

1. reads the product version from the source tree;
2. enforces Linux x86_64 as the target;
3. builds a PyInstaller one-file executable;
4. runs the frozen executable with `--version` and requires an exact product-version match;
5. runs the frozen launcher with scripted `q` input and requires menu startup and clean exit;
6. packages the executable with license/instructions;
7. writes the target-specific SHA-256 manifest.

The release workflow independently runs `sha256sum -c` against the generated archive before uploading the `desktop-linux-dist` workflow artifact.

Unit tests cover target gating, version extraction, command construction, archive contents, executable permissions, and checksum generation.

#### Manual desktop validation gate

Automated execution without a real TTY is not sufficient to certify the real-time games. Before the first stable release containing a Linux standalone artifact, the **CI-built** `desktop-linux-dist` artifact should be downloaded and tested on a real Linux terminal.

At minimum, manual validation should confirm:

- archive checksum succeeds;
- archive extraction preserves/permits execution;
- `./terminal-games --version` reports the expected version;
- launcher startup and normal exit work;
- Snake arrow input, timing, wrapping, save, and quit remain correct;
- Tetris real-time input, drop/pause/save/quit behavior remains correct;
- Terminal Runner jump/timing/save/quit behavior remains correct;
- shared progress remains under `~/.terminal_games` (or an explicit override), not inside the extracted bundle.

Only after that exact artifact is approved should the Stage 3 PR be merged or a later stable version be finalized.

#### Release integration

For relevant pull requests and manual workflow runs, the Linux desktop job is non-publishing and uploads `desktop-linux-dist` for inspection.

For a future approved stable `v*` tag, the publishing job depends on both:

- validated Python release artifacts;
- validated Linux desktop artifacts.

The GitHub Release then receives the wheel/source/checksum files **and** the versioned Linux standalone archive with its target-specific checksum.

`v1.1.0` predates Stage 3 and therefore correctly contains only the Python artifacts. This workflow change is for later releases; it does not retroactively alter the immutable `v1.1.0` source/tag identity.

#### Unsupported desktop targets

Windows, macOS, and Linux ARM are not inferred from the Linux build. PyInstaller is not a cross-compiler; each target must be built and tested on its own operating system/architecture. Those targets require independent CI jobs and manual terminal-input validation before they are advertised.

## Browser play

The preferred initial browser architecture is **not** a direct rewrite of the games into JavaScript and not a forced Pyodide/WebAssembly port.

The existing games depend on genuine terminal concepts such as raw keyboard input, ANSI escape sequences, TTY behavior, `termios`, `select`, and timing-sensitive reads. The lowest-risk browser design keeps the Python game process on a Linux server inside a real pseudo-terminal (PTY):

```text
Browser
  -> terminal UI (for example xterm.js)
  -> WebSocket
  -> web session service
  -> isolated PTY/process
  -> Terminal_Games
```

This preserves the current gameplay code and makes the browser act as a terminal frontend.

### Browser security requirements

A public browser service must isolate each session. Before exposing game processes to the Internet, the service should have at least:

- one isolated process/container per session;
- CPU and memory limits;
- a hard session timeout;
- no unnecessary network access from the game process;
- read-only application files;
- a temporary or deliberately scoped writable progress directory;
- careful WebSocket/session lifecycle handling.

The first browser prototype should be anonymous and temporary. Accounts, cloud saves, global leaderboards, and authentication should be later features, not prerequisites for proving browser play.

## Persistence implications

Desktop productization must keep progress outside the installation/extraction directory, as it does today. Bundling must not move saves into executable or repository-local paths.

Browser sessions should not reuse the server operator's normal `~/.terminal_games` directory. Each session needs an isolated `TERMINAL_GAMES_DATA_DIR` (temporary initially; account-scoped later if cloud profiles are introduced).

## Licensing policy

Terminal_Games is licensed under the MIT License. The repository carries the full terms in `LICENSE`, and Python package metadata declares the SPDX expression `MIT` and includes the license file in built distributions.

PyInstaller is introduced only as desktop build tooling. Its upstream licensing includes an exception permitting generated application bundles to be distributed under the application's own compatible license; Terminal_Games therefore remains MIT-licensed. No modified PyInstaller source is distributed by this project.

Future third-party code, libraries, or assets must still be reviewed for license compatibility, attribution requirements, and redistribution terms before they are incorporated into a public release.

## Compatibility and quality rules

Productization must follow these rules:

- Do not change gameplay merely to simplify packaging.
- Keep game runtime dependencies at zero unless a concrete product feature justifies one.
- Treat build-only tooling separately from runtime dependencies and pin release-critical build tools.
- Keep version information centralized rather than duplicated manually across source files.
- Treat installability as CI-tested behavior.
- Treat frozen-executable startup/version behavior as CI-tested behavior for desktop targets.
- Treat license metadata and inclusion of the license file as tested packaging behavior.
- Do not advertise a platform, package index, binary, or web endpoint until it exists and is tested.
- Require real-terminal manual testing for timing-sensitive desktop input before calling a target certified.
- Keep save-schema compatibility independent from product release numbering.
- Preserve `stable/v1.0.0` and `stable/v1.1.0`; future stable editions receive new permanent branch names.

## Immediate implementation target

The current product state is:

1. `v1.1.0` is published and remains the latest stable GitHub Release;
2. `main` development advances to `1.2.0.dev0` for post-release feature work;
3. Stage 3 introduces a pinned, CI-built Linux x86_64 standalone artifact;
4. the standalone executable is smoke-tested before archiving;
5. the archive carries MIT license/instructions and a dedicated SHA-256 manifest;
6. future stable-tag publication is wired to include the validated Linux artifact;
7. the exact CI-built desktop artifact still requires manual real-terminal validation before the first stable release that advertises it.

PyPI publication, Windows/macOS/Linux-ARM desktop builds, and browser hosting remain separate future work with their own validation requirements.
