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

Before `v1.1.0` is actually published, package metadata may use PEP 440 development or pre-release forms. Development work used `1.1.0.dev0`; final validation used `1.1.0rc1`. After the candidate passed automated and manual validation, release finalization set the package metadata to the stable version `1.1.0`.

A stable package version in the source tree is necessary but not sufficient to claim a published release. The `stable/v1.1.0` branch, `v1.1.0` tag, and GitHub Release remain separate explicit release-management actions and must all refer to the same approved finalization commit.

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
- `python3 -m terminal_games` support;
- installation instructions from a source checkout;
- automated tests for version/CLI behavior;
- CI validation that the repository can actually be installed as a package.

No PyPI publication is implied by this stage. Commands such as `pipx install terminal-games` must not be advertised until a package is actually published under that name.

### Stage 2: release automation

Release automation lives in `.github/workflows/release.yml` and has two deliberately different paths.

A manual `workflow_dispatch` run is non-publishing. It runs the supported Python test matrix, builds the source distribution and wheel, installs the built wheel for validation, generates SHA-256 checksums, and uploads the resulting files as a workflow artifact. This provides a safe dry-run path for development, pre-release, and finalized-but-not-yet-published package states.

A push of a tag beginning with `v` enters the publishing path only after the same tests pass. Before building, `scripts/release_guard.py` requires the package version to be an exact stable `MAJOR.MINOR.PATCH` value and requires the tag to equal `v<package-version>`. A development or pre-release package version, malformed stable version, or mismatched tag fails before publication.

For a validated stable tag, the workflow:

1. runs the complete unit-test suite on Python 3.10, 3.11, 3.12, and 3.13;
2. validates that the release tag exactly matches the stable product version;
3. builds source and wheel distributions;
4. installs the built wheel and re-validates the installed command/version metadata;
5. generates SHA-256 checksums;
6. uploads the release files as a GitHub Actions artifact;
7. creates the GitHub Release and attaches the validated files.

The workflow does **not** create Git tags or stable branches. Those remain explicit release-management actions and must only be performed from an approved known-good commit. The workflow also does not publish to PyPI.

Standalone executables are intentionally not fabricated at this stage. The release workflow is structured so platform-specific binary build jobs can be added when Stage 3 establishes a tested desktop packaging method. Until then, a GitHub Release contains the source distribution, wheel, and checksums only.

### Release-candidate validation

A release candidate is an explicit pre-release package state used to validate the exact product intended for a stable release without publishing that stable release prematurely.

For `v1.1.0`, the first candidate was `1.1.0rc1`. Candidate validation included:

1. the complete automated test suite on Python 3.10 through 3.13;
2. the release-workflow dry run;
3. checksum verification of the built wheel and source distribution;
4. installation of the CI-built wheel in an isolated virtual environment;
5. manual launch and smoke testing of all seven games, including the real-time Snake, Tetris, and Terminal Runner paths;
6. review of README, installation documentation, changelog, and release claims;
7. verification that the release guard rejected the pre-release version for stable publication.

The candidate itself created no `stable/v1.1.0`, `v1.1.0` tag, or GitHub Release.

### Release finalization

After candidate validation succeeds, a separate finalization change sets package metadata to the exact stable version, updates version-sensitive tests and documentation, and records the release date in the changelog.

For `v1.1.0`, finalization sets the package version to `1.1.0` and records `2026-09-07` in the changelog. The finalization PR must itself pass the complete CI matrix and non-publishing release dry run. It still does not create permanent release references or publish anything.

After the finalization PR is manually reviewed and explicitly approved, release management must re-check the exact merged finalization commit and then create:

1. `stable/v1.1.0` from that exact commit;
2. the immutable tag `v1.1.0` on that exact commit.

Pushing the approved tag activates the guarded publishing workflow. Publication is valid only if the package version is exactly `1.1.0` and the tag is exactly `v1.1.0`. The resulting GitHub Release is therefore tied to the same source identity that was approved during finalization.

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

## Licensing policy

Terminal_Games is licensed under the MIT License. The repository carries the full terms in `LICENSE`, and package metadata declares the SPDX expression `MIT` and includes the license file in built distributions.

Licensing is therefore no longer an unresolved release gate for `v1.1.0`. Future third-party code or assets must still be reviewed for license compatibility, attribution requirements, and redistribution terms before they are incorporated into a public release.

The MIT license applies to Terminal_Games itself; researching or comparing other open-source projects does not transfer their code or licensing obligations into this repository unless their material is actually incorporated.

## Compatibility and quality rules

Productization must follow these rules:

- Do not change gameplay merely to simplify packaging.
- Keep runtime dependencies at zero unless a concrete product feature justifies one.
- Keep version information centralized rather than duplicated manually across files.
- Treat installability as CI-tested behavior.
- Treat license metadata and inclusion of the license file as CI-tested packaging behavior.
- Do not advertise a platform, package index, binary, or web endpoint until it exists and is tested.
- Keep save-schema compatibility independent from product release numbering.
- Preserve `stable/v1.0.0`; future stable editions receive new permanent branch names.

## Immediate implementation target

The product foundation, release automation, and `1.1.0` finalization process now provide:

1. stable package/version metadata at `1.1.0` after successful release-candidate validation;
2. the `terminal-games` console entry point and module entry point;
3. continued support for `python3 launcher.py` as a source workflow;
4. packaging/CLI tests and CI installation validation;
5. installation, user, changelog, and release-strategy documentation;
6. a dry-run release workflow for tests, distribution builds, checksums, and artifact inspection;
7. guarded GitHub Release publication for an explicitly created matching stable tag;
8. MIT licensing with standardized SPDX package metadata and license-file inclusion.

The `stable/v1.1.0` branch, `v1.1.0` Git tag, and GitHub Release remain explicit release-management actions until they are actually created from the approved finalization commit. Standalone executables, PyPI publication, and browser hosting remain later stages requiring their own tested changes and explicit decisions.
