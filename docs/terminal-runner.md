# Terminal Runner

`Terminal Runner` is the seventh game in Terminal_Games: a real-time endless side-scrolling runner implemented with the Python standard library only.

## Core loop

The runner stays near a fixed horizontal position while the world moves from right to left. Ground texture and distant scenery move at different rates to create a small terminal-friendly parallax effect.

The game renders on a fixed 50 ms frame cadence. Keyboard input is read immediately through `games.terminal_input.KeyReader`; pressing Enter is not required.

At very high speeds, one rendered frame can represent several terminal columns of travel. To prevent narrow obstacles from being skipped between frames, each frame is internally subdivided into collision-safe world steps of at most 0.5 terminal columns.

## Starting speed

Before every new run, the player chooses one of four starting-speed presets:

```text
1. Relaxed (1.00x start)
2. Normal  (1.50x start)
3. Fast    (2.00x start)
4. Expert  (3.00x start)
```

All modes continue to accelerate and can eventually reach the same maximum speed of **10.00x**.

A loaded run retains its saved progression. Save schemas from the earlier preview builds are migrated toward the closest equivalent physical speed so loading an older run does not intentionally jump straight to the new preset speed.

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

Obstacle selection is weighted and level-gated. The current game contains eight obstacle families:

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

The minimum high-speed spacing preserves a **1.15 second** world-distance reaction allowance. This prevents obstacle density from collapsing near the 10.00x cap.

Automated fairness tests assert that generated gaps never fall below the calculated minimum and that every obstacle family is individually jumpable at the 10.00x maximum when the jump is timed correctly.

## Adaptive level pacing

Level progression is based on **active gameplay time**. Paused time does not advance the level clock.

Speed increases in **0.25x increments per level**. The selected mode determines only the starting multiplier; all modes eventually converge on the same 10.00x cap.

Fast levels deliberately last longer before another speed increase. The duration formula is:

```text
base duration = 10 seconds
extra duration = max(0, speed_multiplier - 2.00) * 5 seconds
maximum duration = 50 seconds
```

Representative examples:

```text
1.00x -> 10 seconds
1.50x -> 10 seconds
2.00x -> 10 seconds
3.00x -> 15 seconds
4.00x -> 20 seconds
5.00x -> 25 seconds
6.00x -> 30 seconds
7.00x -> 35 seconds
8.00x -> 40 seconds
9.00x -> 45 seconds
10.00x -> speed cap (no further level increase)
```

This deliberately stretches the high-speed part of a run so the player spends substantially more time adapting before each subsequent increase. The HUD shows `Next: ...s`; at the cap it shows `Next: MAX`.

## Scoring

Score remains independent of the level clock:

```text
score = floor(distance * 10) + obstacles_passed * 25
```

The HUD shows Score, Best Score, selected speed mode, Level, current speed multiplier, time until the next increase, and obstacles passed.

## Persistence

Terminal Runner uses the shared Terminal_Games progress architecture:

- one versioned save slot;
- persistent Best Score;
- Reset through the shared session menu;
- atomic progress-file replacement in `games.progress`.

Save schema version 3 stores player jump physics, obstacle kinds and positions, distance, passed-obstacle count, spawn distance, animation frame, selected speed mode, current level, and elapsed active time in that level.

Version-1 and version-2 preview saves remain accepted. Their previous physical speed is mapped to the closest new mode/level combination, and version-2 level-timer progress is translated proportionally to the new duration curve.

The random generator's internal state is intentionally not serialized. Loading restores the visible/current run, but later obstacle choices may differ from the abandoned future of the original process.

Best Score follows the same latency rule used by 2048, Snake, and Tetris: the live loop updates `BestScoreTracker` only in memory. Disk I/O occurs at safe points such as Save, quit, or game over.

A completed run clears its stale save slot.

## Architecture

The module keeps mechanics separable from terminal I/O. Core functions cover scoring, speed-profile selection, adaptive level timing, speed-cap enforcement, jump physics, obstacle generation, collision detection, high-speed substepping, persistence migration/validation, and pure frame rendering.
