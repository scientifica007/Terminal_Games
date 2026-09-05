# Terminal Runner: open-source comparison and engineering lessons

This document records a focused comparison between `Terminal_Games`' **Terminal Runner** and several open-source terminal games with similar real-time scrolling, obstacle-avoidance, or endless-runner mechanics.

The goal is not to copy any implementation. The goal is to preserve useful engineering observations, record the external references that informed them, and make future design decisions traceable.

## Comparison baseline

Our implementation was compared at the following stable repository state:

- Project: `scientifica007/Terminal_Games`
- Terminal Runner commit: `c8254b1974fc37b1056475748ad4c2dc24c6668f`
- Commit link: <https://github.com/scientifica007/Terminal_Games/commit/c8254b1974fc37b1056475748ad4c2dc24c6668f>
- Main game module: `games/terminal_runner.py`

At this point Terminal Runner has:

- Python standard-library-only implementation;
- immediate terminal input through `games.terminal_input.KeyReader`;
- automatic horizontal world scrolling;
- velocity/gravity jump physics;
- simple parallax background movement;
- eight obstacle families: crate, rock, spikes, pillar, barrier, stack, double blocks, and pit;
- weighted, level-gated procedural obstacle generation;
- selectable starting speeds: 1.00x, 1.50x, 2.00x, and 3.00x;
- progression up to a 10.00x speed cap;
- longer adaptation periods at higher speeds;
- reaction-time-aware obstacle spacing;
- collision-safe simulation substeps at high speed;
- Save, Load, Reset, and persistent Best Score integration;
- backward-compatible save migration for earlier Runner preview schemas;
- Best Score buffering so persistence I/O stays out of the hot gameplay loop;
- automated fairness tests, including maximum-speed coverage.

## External projects studied

The projects below were selected because they are public, terminal-oriented, and sufficiently similar to provide useful design comparisons. Where possible, this document pins the exact commit inspected so future readers can return to the same code rather than a changed default branch.

### 1. SATYADAHAL/termrex

Repository:

<https://github.com/SATYADAHAL/termrex>

Pinned revision used for this comparison:

<https://github.com/SATYADAHAL/termrex/tree/18d381ad9edbeced1386d45b8d7fd3d6c7333876>

Relevant files:

- `game.hpp`
- `game.cpp`
- `obstacles.hpp`
- `score.hpp`
- `input_handler.cpp`
- `terminal.cpp`

License: MIT.

Technology: C++ on POSIX-like terminals.

This project is a direct terminal interpretation of the Chrome Dino endless runner. It supports ASCII and Unicode modes and explicitly addresses low-level terminal behavior, including the fact that many terminals do not provide ordinary key-release events.

Notable design characteristics:

- jump and duck are separate player actions;
- ground cacti and flying pterodactyls require different responses;
- the game uses a real-time `dt` loop rather than tying physics directly to a fixed number of frames;
- scroll speed increases continuously with time;
- obstacle types are represented through an object hierarchy;
- obstacle creation uses factories;
- terminal input handling is treated as a substantial subsystem rather than a trivial `getch()` wrapper;
- Kitty Keyboard Protocol behavior is considered explicitly;
- high score persistence is intentionally simple, using a dedicated file in the user's home directory.

### 2. jianongHe/Term-Rex

Repository:

<https://github.com/jianongHe/Term-Rex>

Pinned revision used for this comparison:

<https://github.com/jianongHe/Term-Rex/tree/639e2550ff6b3bfdbcfb138e477c71e5c6022e9e>

Especially relevant configuration file:

<https://github.com/jianongHe/Term-Rex/blob/639e2550ff6b3bfdbcfb138e477c71e5c6022e9e/game/config.go>

License: MIT.

Technology: Go with `termbox-go`.

This implementation is useful because its difficulty model changes more than speed alone. It defines multiple stage configurations with different speed values, obstacle probabilities, subtype distributions, and obstacle gap ranges.

Notable design characteristics:

- jump and duck actions;
- multiple cactus families;
- small and large flying birds;
- birds can appear at different heights;
- some airborne threats are intended to be jumped over while others are intended to be ducked under;
- animated clouds and richer background presentation;
- audio support;
- 60 FPS-oriented timing;
- score-threshold-based stages;
- each stage can change obstacle composition and spacing as well as speed;
- obstacle combinations become part of later difficulty.

This project demonstrated particularly clearly that an endless runner's difficulty can be multidimensional rather than merely `speed += constant`.

### 3. kirti34n/arcade-games — Dino Runner

Repository:

<https://github.com/kirti34n/arcade-games>

Pinned revision used for this comparison:

<https://github.com/kirti34n/arcade-games/tree/83e91645887dc742d419569a2b4ade097d12363d>

Dino Runner module:

<https://github.com/kirti34n/arcade-games/blob/83e91645887dc742d419569a2b4ade097d12363d/arcade_games/games/dino.py>

Persistence module:

<https://github.com/kirti34n/arcade-games/blob/83e91645887dc742d419569a2b4ade097d12363d/arcade_games/config.py>

License: MIT.

Technology: Python with `curses` (`windows-curses` where needed on Windows).

This is the closest architectural comparison because it is also a collection of terminal games rather than a single standalone runner. It has shared infrastructure, persistent state, high scores, tests, and game modules.

Notable design characteristics:

- velocity/gravity jump physics;
- jump and duck actions;
- several cactus sizes;
- flying pterodactyls at different vertical bands;
- hitboxes deliberately smaller than visible sprites to make near misses feel fair;
- swept horizontal collision testing to prevent high-speed tunneling;
- speed ramping over time;
- automated tests that search for valid jump timing against obstacle/speed combinations;
- save/resume support for the Dino game;
- cached high score during active gameplay;
- atomic JSON persistence;
- migration support for earlier configuration-directory names;
- cross-process locking around high-score updates.

The collision implementation is especially relevant because it solves the same class of high-speed problem that Terminal Runner addresses with simulation substeps, but uses a different algorithmic technique.

### 4. UpGado/ascii_racer

Repository:

<https://github.com/UpGado/ascii_racer>

Pinned revision used as the reference point:

<https://github.com/UpGado/ascii_racer/tree/36ab0185399d518117f16865089ba4e5a2002b96>

License: MIT.

Technology: Python.

This project is a terminal racing game rather than a jump-based runner, so it is a secondary reference rather than a direct gameplay comparator. It is still useful for studying continuous scrolling, terminal animation, and the problem of making the player perceive forward motion in a character-cell display.

Its relevance to Terminal Runner is primarily visual and temporal: the world must move convincingly and responsively even though the terminal is not a graphical framebuffer.

## Direct comparison

| Area | Terminal Runner | SATYADAHAL/termrex | jianongHe/Term-Rex | arcade-games Dino |
| --- | --- | --- | --- | --- |
| Primary language | Python | C++ | Go | Python |
| Terminal dependency | stdlib-only custom input | custom POSIX terminal layer | `termbox-go` | `curses` |
| Jump | Yes | Yes | Yes | Yes |
| Duck | No | Yes | Yes | Yes |
| Flying obstacles | No | Yes | Yes | Yes |
| Ground obstacle variety | High: 8 families including pits | Mainly cactus families | Several cactus families | Several cactus sizes |
| Pit/gap obstacle | Yes | Not a core feature studied | Not a core feature studied | No equivalent in studied Dino module |
| Start-speed selection | 1.00x / 1.50x / 2.00x / 3.00x | No equivalent user preset studied | Stage-controlled | No equivalent user preset studied |
| Maximum progression | 10.00x cap | Continuous internal speed cap | Stage table | 1.5 internal cap in studied module |
| High-speed tunneling defense | Simulation substeps | Frame/dt movement | Stage-controlled movement | Swept horizontal collision |
| Procedural fairness | Reaction-time spacing + automated tests | Spawner distances | Stage-specific gap ranges | Tested valid jump windows |
| Save/Load current run | Yes | No comparable full run save observed | Not a focus of studied code | Yes |
| Save schema migration | Yes, v1/v2 -> v3 | No equivalent observed | No equivalent observed | Config migration infrastructure |
| Best Score hot-loop I/O | Buffered in memory | High score written at game over | High score persisted outside movement loop | Cached during active game |
| Parallax/background | Simple multi-rate scenery | Terrain scrolling | Clouds and ground decoration | Scrolling ground |
| Audio | No | No core audio dependency | Yes | No in studied Dino module |
| Automated tests in comparison focus | Extensive Runner mechanics/fairness | Not the main strength observed | Not the main strength observed | Strong mechanics/fairness coverage |

## What Terminal Runner currently does well

### 1. It is more general than a Chrome Dino clone

The three direct runner references are strongly centered on cactus/bird gameplay. Terminal Runner instead has a broader environmental obstacle vocabulary, including solid blocks, spikes, stacks, paired structures, and pits.

This gives the game a distinct identity and means future improvements do not need to move it toward a literal dinosaur clone.

### 2. The 10.00x design forced explicit high-speed engineering

At high speed, a naive discrete simulation can let a narrow obstacle move from one side of the player's hitbox to the other between collision checks. This is the classic tunneling problem.

Terminal Runner prevents that by subdividing each rendered frame so world movement is limited to a maximum of 0.5 terminal columns per internal collision step.

The `arcade-games` Dino solves the same class of problem with a swept collision test between the obstacle's previous and current positions.

Both are valid approaches:

- swept collision is more mathematically direct for a simple moving rectangle;
- substepping is easier to apply consistently to physics, obstacle movement, spawning, timers, and collision as one simulation.

There is no current reason to replace Terminal Runner's substep model solely because another project uses swept collision.

### 3. Persistence is unusually mature for an endless terminal runner

Terminal Runner stores enough state to resume an active run, including jump state, obstacle positions, score-related state, selected speed mode, current level, and level timing.

It also accepts earlier preview save versions and migrates their speed/progression representation into the current system.

That is a stronger continuity guarantee than the standalone runner implementations studied here.

### 4. Keeping disk I/O out of the hot loop remains the correct decision

The Best Score architecture developed earlier for 2048 and Snake carried over correctly to Terminal Runner.

The active game observes new best scores in memory. Persistence occurs only at safe points such as explicit Save, quit, or game over.

The comparison reinforces this design. Other mature implementations also cache score/high-score state during active play instead of treating each frame or score increment as a reason to synchronously write a file.

## Most valuable ideas learned from the external projects

### 1. Ducking is more valuable than adding another ground obstacle

The clearest missing gameplay dimension is a second defensive action.

At present, Terminal Runner's main decision is effectively:

> When should I jump?

Adding ducking plus airborne obstacles changes this to:

> Should I jump, duck, or remain neutral?

That is a much larger increase in gameplay depth than adding a ninth ground obstacle with different ASCII art.

A future implementation should preserve the current simple jump control while adding, for example:

- Down Arrow for duck;
- a shorter player hitbox while grounded and ducking;
- low airborne obstacles that require jumping;
- high airborne obstacles that require ducking;
- explicit fairness tests proving each airborne obstacle has a valid response window at every supported speed band.

### 2. Difficulty should change obstacle composition, not only velocity

The Go `Term-Rex` stage table is a strong reference here.

Its later stages change:

- speed;
- cactus-versus-bird probability;
- subtype ratios;
- obstacle spacing;
- combination frequency.

Terminal Runner already level-gates obstacle families, which is a good foundation, but the fixed weights of unlocked obstacles can be improved.

A future difficulty director could gradually alter weights such as:

- early game: crate, rock, spikes dominate;
- middle game: pillar, barrier, stack and pits become more common;
- high speed: carefully selected obstacle combinations become more common, while fairness constraints remain mandatory;
- airborne obstacle probability rises only after the player has had time to learn ducking.

The important lesson is that increasing difficulty should not mean only making the same events happen faster.

### 3. Hitbox tuning should be independent from sprite art

The `arcade-games` Dino intentionally insets collision boxes relative to visible art. That is a practical game-feel technique.

Terminal Runner already separates visible sprite shape from its compact collision geometry. This should remain an explicit design rule:

- art may change for readability or animation;
- hitboxes should be tuned for fairness;
- a visual near miss should generally feel like a near miss rather than an inexplicable death.

If future user testing reports edge-contact deaths that feel unfair, small hitbox insets should be tested before changing jump physics.

### 4. Terminal key-release behavior is a real design constraint

Both `termrex` projects demonstrate that ducking is harder than jumping in a terminal.

Jump is naturally edge-triggered: one key event starts the action.

Duck is naturally stateful: the game wants to know whether a key is still held, but ordinary terminal input often provides key presses/repeats rather than reliable release events.

Therefore a future duck implementation must not assume desktop-game-style key-up events.

Possible approaches include:

- repeat/latch timing, as used by other terminal runners;
- explicit press-to-toggle ducking, though this changes expected runner controls;
- enhanced behavior where Kitty Keyboard Protocol is available, with a portable fallback;
- a short, carefully measured hold-latch that is tested under realistic OS key-repeat delays.

This is the main engineering risk in adding ducking, not the sprite or collision code.

### 5. Automated playability tests are worth keeping and extending

The `arcade-games` Dino comments describe brute-force-style validation that at least one jump timing clears every ground obstacle across supported speeds.

Terminal Runner already has fairness tests at its 10.00x cap. This comparison confirms that those tests are not excessive; they are appropriate for procedural real-time games.

When airborne obstacles are added, tests should verify at minimum:

- every ground obstacle is jumpable;
- every high airborne obstacle is duckable for its complete dangerous interval;
- every low airborne obstacle has a valid jump timing;
- no generated pair/combo is impossible given the player's jump arc, duck transition, world speed, and reaction allowance;
- tunneling protection still works at 10.00x.

### 6. Cross-process persistence locking is a possible infrastructure improvement

`arcade-games` goes beyond atomic replacement and also protects some high-score read/modify/write operations with a small cross-process lock.

Terminal_Games currently protects individual writes through atomic temp-file replacement, which prevents partially written JSON, but concurrent independent processes can still create higher-level read/modify/write races.

This is not currently a reported problem and should not be mixed into Runner gameplay work. However, if the project later supports multiple launchers or parallel game sessions, a small persistence-locking enhancement could be justified as a separate infrastructure PR.

## Ideas deliberately not adopted

### Do not switch the project to `curses` or `termbox`

The comparison shows clear advantages to mature terminal UI libraries, especially around rendering and event handling. However, Terminal_Games has intentionally developed a standard-library input path that is already shared by Tetris and Terminal Runner.

Changing the dependency model would create a large architectural shift for relatively little direct gameplay benefit.

The better approach is to copy the *engineering lessons* without copying the dependency model.

### Do not replace substepping merely for algorithmic elegance

Swept collision is attractive, but the current substep system is already designed around the extreme 10.00x speed cap and integrates cleanly with the rest of the simulation.

A replacement would need measurable benefits and regression evidence, not just conceptual neatness.

### Do not add audio before adding a second gameplay action

The Go project demonstrates that sound can improve presentation, but gameplay depth should remain the higher priority.

Duck + airborne threats materially change player decisions. Audio does not.

### Do not copy Chrome Dino's obstacle set wholesale

Terminal Runner should retain its own obstacle identity. Flying threats can be added without turning every ground object into a cactus or every airborne object into a pterodactyl.

## Recommended future sequence

If Terminal Runner is improved later, the current evidence supports this order:

1. **Duck input model prototype**
   - Solve terminal hold/release semantics first.
   - Test on the same real terminals already used for Snake/Tetris/Runner.

2. **Duck + two airborne obstacle classes**
   - one high obstacle primarily cleared by ducking;
   - one lower obstacle requiring a jump;
   - preserve existing ground obstacles.

3. **Automated airborne fairness suite**
   - prove valid action windows across speed modes and high-speed levels;
   - include 10.00x coverage.

4. **Dynamic obstacle weighting**
   - change composition by progression stage, not merely unlock status;
   - retain reaction-time-aware spacing.

5. **Optional hitbox tuning**
   - only if manual testing identifies unfair edge collisions.

6. **Optional presentation improvements**
   - richer scenery or sound only after gameplay changes are stable.

7. **Separate persistence-concurrency review**
   - evaluate cross-process locking in `games.progress` independently from Runner gameplay.

## Reference links for future work

Keep this section as the quick return point when revisiting the research.

### Direct endless-runner references

- SATYADAHAL/termrex: <https://github.com/SATYADAHAL/termrex>
- SATYADAHAL/termrex pinned comparison revision: <https://github.com/SATYADAHAL/termrex/tree/18d381ad9edbeced1386d45b8d7fd3d6c7333876>
- jianongHe/Term-Rex: <https://github.com/jianongHe/Term-Rex>
- jianongHe/Term-Rex pinned comparison revision: <https://github.com/jianongHe/Term-Rex/tree/639e2550ff6b3bfdbcfb138e477c71e5c6022e9e>
- kirti34n/arcade-games: <https://github.com/kirti34n/arcade-games>
- `arcade-games` Dino module at pinned revision: <https://github.com/kirti34n/arcade-games/blob/83e91645887dc742d419569a2b4ade097d12363d/arcade_games/games/dino.py>

### Secondary scrolling reference

- UpGado/ascii_racer: <https://github.com/UpGado/ascii_racer>
- UpGado/ascii_racer pinned comparison revision: <https://github.com/UpGado/ascii_racer/tree/36ab0185399d518117f16865089ba4e5a2002b96>

### Our baseline

- Terminal_Games: <https://github.com/scientifica007/Terminal_Games>
- Terminal Runner baseline commit: <https://github.com/scientifica007/Terminal_Games/commit/c8254b1974fc37b1056475748ad4c2dc24c6668f>

## Licensing note

All four external repositories listed above were public and identified as MIT-licensed at the time of this comparison. This document records observations only; no external source code was copied into Terminal_Games.

If code is ever reused directly rather than independently reimplemented, its exact source revision and required MIT copyright/license notice must be preserved as required by the relevant license.

## Final takeaway

The most important conclusion is that Terminal Runner is already technically strong in high-speed simulation, persistence, migration, procedural spacing, and ground-obstacle variety. The strongest external idea is not simply "more speed" or "more obstacle art". It is **adding a second player action and designing obstacle composition around meaningful choices**.

The next substantial gameplay improvement, if pursued, should therefore be **ducking plus airborne obstacles**, implemented with terminal-specific key-hold semantics and backed by the same kind of fairness testing that currently protects the 10.00x runner.