# Terminal Runner

`Terminal Runner` is the seventh game in Terminal_Games: a real-time endless side-scrolling runner implemented with the Python standard library only.

## Core loop

The runner stays near a fixed horizontal position while the world moves from right to left. Ground texture and distant scenery move at different rates to create a small terminal-friendly parallax effect.

The game runs on a fixed 50 ms simulation tick. Keyboard input is read immediately through `games.terminal_input.KeyReader`; pressing Enter is not required.

## Controls

```text
Space / Up   jump
P            pause / resume
S            save the current run
Q / Esc      quit
```

Arabic physical-key equivalents are recognized for Pause (`ح`), Save (`س`), and Quit (`ض`).

## Jump physics

Jumping uses velocity and gravity rather than a fixed animation script:

- initial vertical velocity: 12.5 terminal rows/second;
- gravity: 22 terminal rows/second squared;
- the player can jump only while grounded;
- landing clamps the vertical position and velocity back to zero.

Collision uses a compact hitbox rather than the visible ASCII sprite, so animation changes do not alter gameplay geometry.

## Obstacles

Obstacle selection is weighted and level-gated. Version 1 contains eight obstacle families:

- crate;
- rock;
- spikes;
- pillar;
- barrier;
- stacked blocks;
- double blocks;
- pit.

Early levels use only the simpler crate, rock, and spikes. Taller, wider, and pit obstacles unlock later.

A pit is modeled differently from a solid obstacle: a grounded runner falls into it, while an airborne runner can cross it.

## Fair generation

Obstacle timing is generated in world-distance units rather than frame counts. The minimum distance between spawns depends on current world speed, a reaction-time allowance, and the maximum obstacle width. A randomized extra distance is then added.

This keeps obstacle spacing from collapsing as the game becomes faster. Automated tests assert that generated gaps never fall below the calculated minimum and that every obstacle family is individually jumpable at maximum speed when the jump is timed correctly.

## Difficulty and scoring

Score combines distance travelled with a small bonus for each obstacle passed:

```text
score = floor(distance * 10) + obstacles_passed * 25
```

A new level begins every 700 points. World speed starts at 7.5 terminal columns/second and increases by 0.75 columns/second per level until reaching a cap of 16.5 columns/second.

The HUD shows Score, Best Score, Level, speed multiplier, and the number of obstacles passed.

## Persistence

Terminal Runner uses the shared Terminal_Games progress architecture:

- one versioned save slot;
- persistent Best Score;
- Reset through the shared session menu;
- atomic progress-file replacement in `games.progress`.

The saved run contains player jump physics, obstacle kinds and positions, distance, passed-obstacle count, spawn distance, and animation frame index.

The random generator's internal state is intentionally not serialized. Loading restores the visible/current run exactly, but later obstacle choices after the saved state may differ from the abandoned future of the original process.

Best Score follows the same latency rule used by 2048, Snake, and Tetris: the live loop only updates `BestScoreTracker` in memory. Disk I/O occurs only at explicit safe points such as Save, quit, or game over.

A completed run clears its stale save slot.

## Architecture

The module keeps game mechanics separable from terminal I/O. Core functions cover:

- scoring and level progression;
- speed calculation;
- jump physics;
- obstacle eligibility and weighted selection;
- fair spawn-distance calculation;
- collision detection;
- fixed-timestep world updates;
- serialization and validation;
- pure frame rendering.

This makes the runner logic unit-testable without an interactive terminal.
