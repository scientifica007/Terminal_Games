"""Real-time endless runner for the terminal using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from random import Random
import sys
import time
from typing import Any

from games.progress import (
    BestScoreTracker,
    ProgressDataError,
    clear_save,
    load_state,
    save_state,
)
from games.session_menu import LOAD, NEW, QUIT, choose_session_action
from games.terminal_input import KeyReader

GAME_ID = "terminal_runner"
SAVE_VERSION = 1

VIEW_WIDTH = 68
VIEW_HEIGHT = 16
GROUND_ROW = 12
PLAYER_X = 7.0
PLAYER_HITBOX_WIDTH = 2.0
PLAYER_HITBOX_HEIGHT = 2.6

FRAME_INTERVAL = 0.05
BASE_SPEED = 7.5
SPEED_PER_LEVEL = 0.75
MAX_SPEED = 16.5
LEVEL_SCORE_STEP = 700

JUMP_VELOCITY = 12.5
GRAVITY = 22.0
MIN_REACTION_TIME = 0.85
EXTRA_SPAWN_DISTANCE = 10.0

QUIT_KEYS = {"q", "ض", "escape", "\x03"}
PAUSE_KEYS = {"p", "ح"}
SAVE_KEYS = {"s", "س"}
JUMP_KEYS = {" ", "up"}

RUN_FRAMES = (
    (" O ", "/|>", "/ >"),
    (" O ", "<|\\", "< \\"),
)
JUMP_FRAME = (" O ", "/|\\", "/ \\")
GROUND_PATTERN = "__..___..._._"


@dataclass(frozen=True)
class ObstacleSpec:
    """Static description of one obstacle family."""

    kind: str
    width: int
    height: int
    sprite: tuple[str, ...]
    min_level: int = 1
    weight: int = 1
    pit: bool = False

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("Obstacle width must be positive.")
        if self.height < 0:
            raise ValueError("Obstacle height cannot be negative.")
        if self.min_level < 1 or self.weight < 1:
            raise ValueError("Obstacle level and weight must be positive.")
        if self.pit:
            if self.height != 0 or self.sprite:
                raise ValueError("Pit obstacles do not have an above-ground sprite.")
            return
        if len(self.sprite) != self.height:
            raise ValueError("Obstacle sprite height does not match its hitbox.")
        if any(len(row) != self.width for row in self.sprite):
            raise ValueError("Obstacle sprite width does not match its hitbox.")


OBSTACLE_SPECS: tuple[ObstacleSpec, ...] = (
    ObstacleSpec("crate", 2, 2, ("[]", "[]"), 1, 5),
    ObstacleSpec("rock", 3, 1, ("/^\\",), 1, 5),
    ObstacleSpec("spikes", 5, 1, ("/^/^\\",), 1, 4),
    ObstacleSpec("pillar", 1, 3, ("#", "#", "#"), 2, 3),
    ObstacleSpec("barrier", 4, 1, ("####",), 2, 4),
    ObstacleSpec("stack", 4, 2, ("[][]", "[][]"), 3, 3),
    ObstacleSpec("double", 5, 2, ("[] []", "[] []"), 4, 2),
    ObstacleSpec("pit", 4, 0, (), 3, 2, pit=True),
)
OBSTACLE_BY_KIND = {spec.kind: spec for spec in OBSTACLE_SPECS}


@dataclass
class Obstacle:
    """One obstacle moving through the viewport."""

    spec: ObstacleSpec
    x: float
    counted: bool = False


@dataclass
class GameState:
    """Mutable state for one endless-runner round."""

    player_y: float = 0.0
    player_vy: float = 0.0
    obstacles: list[Obstacle] = field(default_factory=list)
    distance: float = 0.0
    obstacles_passed: int = 0
    spawn_remaining: float = 26.0
    alive: bool = True
    frame_index: int = 0
    collision_kind: str = ""


def score_for_state(state: GameState) -> int:
    """Return distance score plus a small bonus for cleared obstacles."""
    return max(0, int(state.distance * 10) + state.obstacles_passed * 25)


def level_for_score(score: int) -> int:
    """Return a one-based level that advances at fixed score intervals."""
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("Score must be a non-negative integer.")
    return score // LEVEL_SCORE_STEP + 1


def speed_for_level(level: int) -> float:
    """Return world speed in terminal columns per second."""
    if isinstance(level, bool) or not isinstance(level, int) or level < 1:
        raise ValueError("Level must be a positive integer.")
    return min(MAX_SPEED, BASE_SPEED + (level - 1) * SPEED_PER_LEVEL)


def current_speed(state: GameState) -> float:
    return speed_for_level(level_for_score(score_for_state(state)))


def is_grounded(state: GameState) -> bool:
    return state.player_y <= 1e-9 and state.player_vy <= 1e-9


def try_jump(state: GameState) -> bool:
    """Start a jump only while the runner is on the ground."""
    if not state.alive or not is_grounded(state):
        return False
    state.player_y = 0.0
    state.player_vy = JUMP_VELOCITY
    return True


def advance_player(state: GameState, dt: float) -> None:
    """Advance vertical jump physics using a small fixed timestep."""
    if dt <= 0:
        raise ValueError("dt must be positive.")
    if is_grounded(state):
        state.player_y = 0.0
        state.player_vy = 0.0
        return

    state.player_y += state.player_vy * dt
    state.player_vy -= GRAVITY * dt
    if state.player_y <= 0.0 and state.player_vy < 0.0:
        state.player_y = 0.0
        state.player_vy = 0.0


def minimum_spawn_distance(speed: float) -> float:
    """Return a conservative lead distance between consecutive obstacles."""
    if speed <= 0:
        raise ValueError("Speed must be positive.")
    max_width = max(spec.width for spec in OBSTACLE_SPECS)
    return max(12.0, speed * MIN_REACTION_TIME) + max_width


def next_spawn_distance(speed: float, rng: Random) -> float:
    """Choose a fair randomized distance before the next obstacle."""
    return minimum_spawn_distance(speed) + rng.uniform(0.0, EXTRA_SPAWN_DISTANCE)


def eligible_obstacles(level: int) -> tuple[ObstacleSpec, ...]:
    """Return obstacle families unlocked for the current level."""
    if isinstance(level, bool) or not isinstance(level, int) or level < 1:
        raise ValueError("Level must be a positive integer.")
    return tuple(spec for spec in OBSTACLE_SPECS if spec.min_level <= level)


def choose_obstacle(level: int, rng: Random) -> ObstacleSpec:
    """Choose an obstacle with level gates and weighted variety."""
    choices = eligible_obstacles(level)
    return rng.choices(choices, weights=[spec.weight for spec in choices], k=1)[0]


def spawn_obstacle(state: GameState, rng: Random) -> Obstacle:
    """Append one level-appropriate obstacle just beyond the right edge."""
    level = level_for_score(score_for_state(state))
    obstacle = Obstacle(choose_obstacle(level, rng), float(VIEW_WIDTH + 1))
    state.obstacles.append(obstacle)
    return obstacle


def horizontal_overlap(obstacle: Obstacle) -> bool:
    player_right = PLAYER_X + PLAYER_HITBOX_WIDTH
    obstacle_right = obstacle.x + obstacle.spec.width
    return PLAYER_X < obstacle_right and player_right > obstacle.x


def collides_with_player(state: GameState, obstacle: Obstacle) -> bool:
    """Return whether the runner's hitbox intersects an obstacle."""
    if not horizontal_overlap(obstacle):
        return False
    if obstacle.spec.pit:
        return state.player_y < 0.35

    player_bottom = state.player_y
    player_top = state.player_y + PLAYER_HITBOX_HEIGHT
    return player_bottom < obstacle.spec.height and player_top > 0.0


def detect_collision(state: GameState) -> Obstacle | None:
    return next(
        (obstacle for obstacle in state.obstacles if collides_with_player(state, obstacle)),
        None,
    )


def step_game(state: GameState, dt: float, rng: Random) -> None:
    """Advance physics, scrolling, spawning, scoring, and collision by one tick."""
    if dt <= 0:
        raise ValueError("dt must be positive.")
    if not state.alive:
        return

    speed = current_speed(state)
    advance_player(state, dt)

    travel = speed * dt
    state.distance += travel
    state.spawn_remaining -= travel
    state.frame_index += 1

    for obstacle in state.obstacles:
        obstacle.x -= travel
        if not obstacle.counted and obstacle.x + obstacle.spec.width < PLAYER_X:
            obstacle.counted = True
            state.obstacles_passed += 1

    state.obstacles = [
        obstacle
        for obstacle in state.obstacles
        if obstacle.x + obstacle.spec.width >= -1.0
    ]

    if state.spawn_remaining <= 0.0:
        spawn_obstacle(state, rng)
        state.spawn_remaining = next_spawn_distance(current_speed(state), rng)

    collision = detect_collision(state)
    if collision is not None:
        state.alive = False
        state.collision_kind = collision.spec.kind


def is_quit_key(key: str | None) -> bool:
    return key is not None and key.lower() in QUIT_KEYS


def is_pause_key(key: str | None) -> bool:
    return key is not None and key.lower() in PAUSE_KEYS


def is_save_key(key: str | None) -> bool:
    return key is not None and key.lower() in SAVE_KEYS


def is_jump_key(key: str | None) -> bool:
    return key is not None and key.lower() in JUMP_KEYS


def _finite_number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid saved {label}.")
    number = float(value)
    if not math.isfinite(number) or (minimum is not None and number < minimum):
        raise ValueError(f"Invalid saved {label}.")
    return number


def _nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid saved {label}.")
    return value


def serialize_session(state: GameState) -> dict[str, Any]:
    """Serialize a live runner session without depending on RNG internals."""
    return {
        "version": SAVE_VERSION,
        "player_y": state.player_y,
        "player_vy": state.player_vy,
        "obstacles": [
            {
                "kind": obstacle.spec.kind,
                "x": obstacle.x,
                "counted": obstacle.counted,
            }
            for obstacle in state.obstacles
        ],
        "distance": state.distance,
        "obstacles_passed": state.obstacles_passed,
        "spawn_remaining": state.spawn_remaining,
        "frame_index": state.frame_index,
    }


def deserialize_session(payload: dict[str, Any]) -> GameState:
    """Validate and restore an in-progress Terminal Runner session."""
    if not isinstance(payload, dict) or payload.get("version") != SAVE_VERSION:
        raise ValueError("Unsupported Terminal Runner save version.")

    player_y = _finite_number(payload.get("player_y"), "player height", minimum=0.0)
    player_vy = _finite_number(payload.get("player_vy"), "player velocity")
    if player_y > 10.0 or (player_y <= 1e-9 and player_vy < 0.0):
        raise ValueError("Invalid saved player physics state.")

    distance = _finite_number(payload.get("distance"), "distance", minimum=0.0)
    spawn_remaining = _finite_number(
        payload.get("spawn_remaining"),
        "spawn distance",
        minimum=0.0,
    )
    obstacles_passed = _nonnegative_int(payload.get("obstacles_passed"), "obstacle count")
    frame_index = _nonnegative_int(payload.get("frame_index"), "frame index")

    raw_obstacles = payload.get("obstacles")
    if not isinstance(raw_obstacles, list) or len(raw_obstacles) > 12:
        raise ValueError("Invalid saved obstacle list.")

    obstacles: list[Obstacle] = []
    for raw in raw_obstacles:
        if not isinstance(raw, dict):
            raise ValueError("Invalid saved obstacle.")
        kind = raw.get("kind")
        spec = OBSTACLE_BY_KIND.get(kind)
        if spec is None:
            raise ValueError("Unknown saved obstacle kind.")
        x = _finite_number(raw.get("x"), "obstacle position")
        if not -10.0 <= x <= VIEW_WIDTH + 3.0:
            raise ValueError("Saved obstacle is outside the expected world range.")
        counted = raw.get("counted")
        if not isinstance(counted, bool):
            raise ValueError("Invalid saved obstacle count state.")
        obstacles.append(Obstacle(spec, x, counted))

    state = GameState(
        player_y=player_y,
        player_vy=player_vy,
        obstacles=obstacles,
        distance=distance,
        obstacles_passed=obstacles_passed,
        spawn_remaining=spawn_remaining,
        alive=True,
        frame_index=frame_index,
    )
    if detect_collision(state) is not None:
        raise ValueError("Saved runner already collides with an obstacle.")
    return state


def _draw_text(canvas: list[list[str]], row: int, col: int, text: str) -> None:
    if not 0 <= row < len(canvas):
        return
    for offset, char in enumerate(text):
        x = col + offset
        if 0 <= x < len(canvas[row]) and char != " ":
            canvas[row][x] = char


def _parallax_positions(distance: float, factor: float, spacing: int) -> list[int]:
    offset = int(distance * factor)
    return list(range(-(offset % spacing), VIEW_WIDTH, spacing))


def _runner_sprite(state: GameState) -> tuple[str, ...]:
    if not is_grounded(state):
        return JUMP_FRAME
    return RUN_FRAMES[(state.frame_index // 3) % len(RUN_FRAMES)]


def render_world(
    state: GameState,
    best_score: int = 0,
    *,
    paused: bool = False,
    status: str = "",
) -> str:
    """Render one full terminal frame with simple parallax scenery."""
    canvas = [[" " for _ in range(VIEW_WIDTH)] for _ in range(VIEW_HEIGHT)]

    for index, x in enumerate(_parallax_positions(state.distance, 0.25, 23)):
        _draw_text(canvas, 2 + (index % 2) * 2, x, ".~~.")
    for index, x in enumerate(_parallax_positions(state.distance, 0.50, 17)):
        _draw_text(canvas, GROUND_ROW - 4 - (index % 2), x, ".^.")

    ground_shift = int(state.distance) % len(GROUND_PATTERN)
    texture = "".join(
        GROUND_PATTERN[(ground_shift + column) % len(GROUND_PATTERN)]
        for column in range(VIEW_WIDTH)
    )
    canvas[GROUND_ROW] = list("=" * VIEW_WIDTH)
    canvas[GROUND_ROW + 1] = list(texture)
    canvas[GROUND_ROW + 2] = list(texture[::-1])

    for obstacle in state.obstacles:
        left = int(round(obstacle.x))
        if obstacle.spec.pit:
            for x in range(left, left + obstacle.spec.width):
                if 0 <= x < VIEW_WIDTH:
                    canvas[GROUND_ROW][x] = " "
                    canvas[GROUND_ROW + 1][x] = " "
                    canvas[GROUND_ROW + 2][x] = "v"
            continue

        top = GROUND_ROW - obstacle.spec.height
        for row_offset, sprite_row in enumerate(obstacle.spec.sprite):
            _draw_text(canvas, top + row_offset, left, sprite_row)

    sprite = _runner_sprite(state)
    lift = int(round(state.player_y))
    player_top = GROUND_ROW - len(sprite) - lift
    for row_offset, sprite_row in enumerate(sprite):
        _draw_text(canvas, player_top + row_offset, int(PLAYER_X), sprite_row)

    score = score_for_state(state)
    level = level_for_score(score)
    speed = current_speed(state)
    lines = [
        "=== Terminal Runner ===",
        "Space/Up: jump | P: pause | S: save | Q/Esc: quit",
        (
            f"Score: {score:05d}   Best: {best_score:05d}   "
            f"Level: {level}   Speed: {speed / BASE_SPEED:.2f}x   "
            f"Passed: {state.obstacles_passed}"
        ),
        "PAUSED - press P to resume." if paused else status,
    ]
    lines.extend("".join(row) for row in canvas)
    return "\n".join(lines)


def _flush_best_score(best: BestScoreTracker) -> None:
    """Persist a buffered record only at an explicit safe I/O point."""
    best.flush()


def _save_live_state(state: GameState, best: BestScoreTracker) -> str:
    """Persist the current run and buffered record outside the hot tick path."""
    try:
        save_state(GAME_ID, serialize_session(state))
    except ProgressDataError:
        return "Save failed."
    try:
        _flush_best_score(best)
    except ProgressDataError:
        return "Run saved; Best Score sync failed."
    return "Run saved."


def play_round(rng: Random | None = None, saved: GameState | None = None) -> bool:
    """Play one real-time round. Return False when the player explicitly quits."""
    generator = rng or Random()
    state = saved if saved is not None else GameState()
    best = BestScoreTracker.load(GAME_ID, score_for_state(state))
    paused = False
    status = ""

    if not sys.stdin.isatty():
        print("Terminal Runner requires an interactive terminal (TTY).")
        return False

    print("\033[2J\033[?25l", end="", flush=True)
    try:
        try:
            with KeyReader() as reader:
                next_tick = time.monotonic() + FRAME_INTERVAL
                while state.alive:
                    print(
                        "\033[H"
                        + render_world(
                            state,
                            best.best_score,
                            paused=paused,
                            status=status,
                        ),
                        end="",
                        flush=True,
                    )

                    if paused:
                        key = reader.read_key(0.10)
                        if is_quit_key(key):
                            try:
                                _flush_best_score(best)
                            except ProgressDataError:
                                pass
                            return False
                        if is_save_key(key):
                            status = _save_live_state(state, best)
                            continue
                        if is_pause_key(key):
                            paused = False
                            status = "Resumed."
                            next_tick = time.monotonic() + FRAME_INTERVAL
                        continue

                    timeout = max(0.0, next_tick - time.monotonic())
                    key = reader.read_key(timeout)
                    if is_quit_key(key):
                        try:
                            _flush_best_score(best)
                        except ProgressDataError:
                            pass
                        return False
                    if is_save_key(key):
                        status = _save_live_state(state, best)
                        next_tick = time.monotonic() + FRAME_INTERVAL
                        continue
                    if is_pause_key(key):
                        paused = True
                        status = ""
                        continue
                    if is_jump_key(key) and try_jump(state):
                        status = "Jump!"

                    now = time.monotonic()
                    if now < next_tick:
                        continue

                    step_game(state, FRAME_INTERVAL, generator)
                    best.observe(score_for_state(state))
                    status = ""
                    next_tick += FRAME_INTERVAL
                    if now - next_tick > FRAME_INTERVAL * 4:
                        next_tick = now + FRAME_INTERVAL
        except KeyboardInterrupt:
            try:
                _flush_best_score(best)
            except ProgressDataError:
                pass
            return False
    finally:
        print("\033[?25h", flush=True)

    final_score = score_for_state(state)
    best.observe(final_score)
    try:
        _flush_best_score(best)
        clear_save(GAME_ID)
    except ProgressDataError as exc:
        print(f"\nProgress data error after game over: {exc}")

    print("\nGame over.")
    if state.collision_kind:
        print(f"Collision: {state.collision_kind}")
    print(f"Final score: {final_score}")
    print(f"Obstacles passed: {state.obstacles_passed}")
    print(f"Best Score: {best.best_score}")
    return True


def _load_saved_game() -> GameState | None:
    try:
        payload = load_state(GAME_ID)
    except ProgressDataError as exc:
        print(f"\nCould not load Terminal Runner: {exc}")
        return None
    if payload is None:
        return None
    try:
        return deserialize_session(payload)
    except ValueError as exc:
        print(f"\nSaved run is invalid: {exc}")
        return None


def main() -> None:
    """Run Terminal Runner."""
    print("=== Terminal Runner ===")
    print("Run automatically, jump with Space or Up, and survive as long as possible.")
    print("Press P to pause, S to save, and Q or Esc to quit.")

    while True:
        action = choose_session_action(GAME_ID, "Terminal Runner")
        if action == QUIT:
            print("Goodbye.")
            return

        saved = None
        if action == LOAD:
            saved = _load_saved_game()
            if saved is None:
                continue
            print("\nSaved run loaded.")
        elif action != NEW:
            continue

        if not play_round(saved=saved):
            print("\nGoodbye.")
            return

        again = input("\nRun again? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return


if __name__ == "__main__":
    main()
