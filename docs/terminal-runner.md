# Terminal Runner

`Terminal Runner` is the seventh game in Terminal_Games: a real-time endless side-scrolling runner implemented with the Python standard library only.

## Core loop

The runner stays near a fixed horizontal position while the world moves from right to left. Ground texture and distant scenery move at different rates to create a small terminal-friendly parallax effect.

The game runs on a fixed 50 ms simulation tick. Keyboard input is read immediately through `games.terminal_input.KeyReader`; pressing Enter is not required.

## Starting speed

Before every new run, the player chooses one of four starting-speed presets:

```text
1. Relaxed  0.85x
2. Normal   1.00x
3. Fast     1.25x
4. Expert   1.50x
```

The preset changes only the starting world speed. All four modes continue to accelerate with later levels and can eventually reach the same maximum speed of **3.00x**.

A loaded run keeps the speed preset that was saved with it; the player does not silently change the difficulty of a saved session.

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

The minimum high-speed reaction allowance is 1.05 seconds. This prevents obstacle spacing from collapsing when the world is near its 3.00x cap.

Automated fairness tests assert that generated gaps never fall below the calculated minimum and that every obstacle family is individually jumpable at maximum speed when the jump is timed correctly.

## Adaptive level pacing

Level progression is based on **active gameplay time**, not a fixed score threshold. Paused time does not advance the level clock.

Speed starts from the selected preset and increases by 0.75 terminal columns/second per level until the world reaches 22.5 columns/second, which is **3.00x** the Normal base speed of 7.5 columns/second.

Fast levels deliberately last longer before another speed increase. The level duration is calculated from the current speed multiplier:

```text
base duration = 8 seconds
extra duration = max(0, speed_multiplier - 1.50) * 10 seconds
maximum duration = 23 seconds
```

Examples:

```text
1.00x -> 8 seconds
1.50x -> 8 seconds
2.00x -> 13 seconds
2.20x -> 15 seconds
2.50x -> 18 seconds
3.00x -> 23 seconds
```

This gives the player progressively more time to adapt precisely where reaction demands become highest. The HUD shows a `Next: ...s` countdown for the remaining active time in the current level.

## Scoring

Score remains independent of the level clock and combines distance travelled with a small bonus for each obstacle passed:

```text
score = floor(distance * 10) + obstacles_passed * 25
```

The HUD shows Score, Best Score, selected speed mode, Level, current speed multiplier, time until the next level, and the number of obstacles passed.

## Persistence

Terminal Runner uses the shared Terminal_Games progress architecture:

- one versioned save slot;
- persistent Best Score;
- Reset through the shared session menu;
- atomic progress-file replacement in `games.progress`.

The current save schema stores player jump physics, obstacle kinds and positions, distance, passed-obstacle count, spawn distance, animation frame index, selected speed mode, current level, and elapsed active time within that level.

The save schema was advanced to version 2 when speed selection and time-based progression were added. Version-1 saves created during the pre-merge manual preview are still accepted: they migrate to Normal mode and derive their current level from the old 700-points-per-level rule, with the new level timer starting at zero.

The random generator's internal state is intentionally not serialized. Loading restores the visible/current run exactly, but later obstacle choices after the saved state may differ from the abandoned future of the original process.

Best Score follows the same latency rule used by 2048, Snake, and Tetris: the live loop only updates `BestScoreTracker` in memory. Disk I/O occurs only at explicit safe points such as Save, quit, or game over.

A completed run clears its stale save slot.

## Architecture

The module keeps game mechanics separable from terminal I/O. Core functions cover:

- scoring;
- speed-profile selection;
- time-based level progression and adaptation pacing;
- speed calculation and cap enforcement;
- jump physics;
- obstacle eligibility and weighted selection;
- fair spawn-distance calculation;
- collision detection;
- fixed-timestep world updates;
- serialization, legacy migration, and validation;
- pure frame rendering.

This makes the runner logic unit-testable without an interactive terminal.
