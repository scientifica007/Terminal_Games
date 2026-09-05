# Terminal_Games product and release strategy

## Purpose

Terminal_Games remains an active personal development playground: new games, experiments, refactors, and gameplay ideas should continue on ordinary feature branches. Productization must not slow that work down or force every experiment to become part of a public release immediately.

At the same time, players should have a clearly identifiable stable edition that can be installed, launched, and revisited later. The project therefore adopts a dual-track model: continuous development plus versioned product releases.

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

The existing `stable/v1.0.0` branch remains an immutable historical baseline. It is not retroactively treated as a Git tag or GitHub Release. The first planned productized release after this foundation is therefore `v1.1.0`.

## Versioning policy

Terminal_Games uses Semantic Versioning for product releases:

- **MAJOR**: incompatible product-level changes or deliberately broken compatibility;
- **MINOR**: new games or substantial backward-compatible features;
- **PATCH**: backward-compatible fixes and small corrections.

Before `v1.1.0` is actually released, package metadata may use the PEP 440 development form `1.1.0.dev0`. This means “development work targeting 1.1.0”; it is not itself a stable release.

Product versioning is separate from each game's saved-state schema. For example, the product can move from 1.1.0 to 1.2.0 while Terminal Runner's save payload remains version 3. Save-schema versions change only when persistence compatibility requires them.

## Product identity and entry points

The product should have one canonical command:

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

The first packaging layer must be an adapter around the current launcher. It must not move game modules or change gameplay behavior merely to satisfy packaging conventions.

## Distribution stages

### Stage 1: Python package foundation

The first product layer provides:

- `pyproject.toml` package metadata;
- a single source of truth for the product version;
- the `terminal-games` console command;
- `python -m terminal_games` support;
- installation instructions from a source checkout;
- automated tests for version/CLI behavior;
- CI validation that the repository can actually be installed as a package.

No PyPI publication is implied by this stage. Commands such as `pipx install terminal-games` must not be advertised until a package is actually published under that name.

### Stage 2: release automation

A later release workflow should, for a release tag:

1. run the complete test suite;
2. build source and wheel distributions;
3. build supported standalone executables;
4. generate checksums;
5. create a GitHub Release and attach the artifacts.

Release automation is deliberately separated from the first packaging layer so we can validate installation and version semantics before automating publication.

### Stage 3: standalone desktop artifacts

The target user experience is eventually a downloadable artifact that does not require Git knowledge and, where practical, does not require a preinstalled Python interpreter.

Potential artifacts include Linux, Windows, and macOS builds. Platform support must be based on real tests, not assumptions. The current GitHub Actions test matrix runs on Linux, so the project should not claim fully certified Windows/macOS support until dedicated platform CI and manual real-time terminal testing exist.

Linux is the natural first binary target because the existing real-time terminal implementation is already exercised there.

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

Desktop productization must keep progress outside the installation directory, as it does today. Packaging must not move saves into package files or repository-local paths.

Browser sessions should not reuse the server operator's normal `~/.terminal_games` directory. Each session needs an isolated `TERMINAL_GAMES_DATA_DIR` (temporary initially; account-scoped later if cloud profiles are introduced).

## Licensing release gate

The repository currently needs an explicit project-license decision before broad third-party distribution is treated as a formal public product release. Package metadata must not invent a license. Before `v1.1.0` is published as a downloadable public release, the owner should choose and add the intended project license and ensure third-party assets/code, if any are ever introduced, are compatible with it.

Researching MIT-licensed comparison projects does not automatically license Terminal_Games under MIT.

## Compatibility and quality rules

Productization must follow these rules:

- Do not change gameplay merely to simplify packaging.
- Keep runtime dependencies at zero unless a concrete product feature justifies one.
- Keep version information centralized rather than duplicated manually across files.
- Treat installability as CI-tested behavior.
- Do not advertise a platform, package index, binary, or web endpoint until it exists and is tested.
- Keep save-schema compatibility independent from product release numbering.
- Preserve `stable/v1.0.0`; future stable editions receive new permanent branch names.

## Immediate implementation target

This document authorizes the first Product/Release foundation only:

1. introduce package/version metadata targeting `1.1.0.dev0`;
2. add the `terminal-games` console entry point and module entry point;
3. retain `python3 launcher.py` unchanged as a supported source workflow;
4. add packaging/CLI tests and CI installation validation;
5. document installation and release status;
6. add a changelog that distinguishes unreleased work from historical baselines.

Standalone executables, PyPI publication, Git tags, GitHub Releases, and browser hosting remain subsequent stages and require their own tested changes.