Terminal_Games {version} - Linux x86_64 standalone bundle

This bundle contains a self-contained Terminal_Games executable. A separate
Python installation is not required.

Run from a terminal:

    ./terminal-games

Check the bundled version:

    ./terminal-games --version

The archive preserves the executable bit. If a third-party extraction tool
removes it, restore it with:

    chmod +x terminal-games

Real-time games require an interactive terminal/TTY for keyboard input.
Progress remains outside the application bundle at:

    ~/.terminal_games/progress.json

Compatibility scope:
- Linux x86_64 only for this first desktop target.
- Built on Ubuntu 22.04 to use an older glibc baseline than ubuntu-latest.
- Intended for systems with a compatible or newer GNU/Linux userspace; not
  certified on every Linux distribution.
- Windows, macOS, and Linux ARM builds are not provided by this bundle.

Terminal_Games is licensed under the MIT License. See the included LICENSE
file for the full terms.
