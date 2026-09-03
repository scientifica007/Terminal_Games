"""Real-time terminal Tetris using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
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

GAME_ID = "tetris"
SAVE_VERSION = 1
WIDTH = 10
HEIGHT = 20
SPAWN_X = WIDTH // 2 - 2
SPAWN_Y = 0

PIECE_TYPES = ("I", "O", "T", "S", "Z", "J", "L")
EMPTY = ""
LINE_CLEAR_SCORES = {1: 40, 2: 100, 3: 300, 4: 1200}
MIN_DROP_INTERVAL = 0.08
BASE_DROP_INTERVAL = 0.80
DROP_ACCELERATION = 0.85

QUIT_KEYS = {"q", "ض", "escape", "\x03"}
SAVE_KEYS = {"s", "س"}
PAUSE_KEYS = {"p", "ح"}

ROTATIONS: dict[str, tuple[tuple[tuple[int, int], ...], ...]] = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
}

ROTATION_KICKS = ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1))

Board = list[list[str]]
Position = tuple[int, int]


@dataclass
class Piece:
    kind: str
    rotation: int = 0
    x: int = SPAWN_X
    y: int = SPAWN_Y


@dataclass
class GameState:
    board: Board
    active: Piece
    next_kind: str
    bag: list[str]
    score: int = 0
    lines: int = 0
    game_over: bool = False


def empty_board(width: int = WIDTH, height: int = HEIGHT) -> Board:
    """Return a fresh empty board."""
    if width <= 0 or height <= 0:
        raise ValueError("Board dimensions must be positive.")
    return [[EMPTY for _ in range(width)] for _ in range(height)]


def spawn_piece(kind: str) -> Piece:
    """Create a piece at the standard spawn position."""
    if kind not in PIECE_TYPES:
        raise ValueError("Unknown tetromino kind.")
    return Piece(kind=kind)


def piece_cells(piece: Piece) -> tuple[Position, ...]:
    """Return board coordinates occupied by ``piece``."""
    if piece.kind not in ROTATIONS or not 0 <= piece.rotation < 4:
        raise ValueError("Invalid tetromino.")
    return tuple(
        (piece.x + dx, piece.y + dy)
        for dx, dy in ROTATIONS[piece.kind][piece.rotation]
    )


def can_place(board: Board, piece: Piece) -> bool:
    """Return whether a piece is inside the board and avoids locked cells."""
    if len(board) != HEIGHT or any(len(row) != WIDTH for row in board):
        raise ValueError("Board dimensions do not match Tetris.")
    for x, y in piece_cells(piece):
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return False
        if board[y][x] != EMPTY:
            return False
    return True


def try_move(state: GameState, dx: int, dy: int) -> bool:
    """Move the active piece when the target position is legal."""
    candidate = Piece(
        state.active.kind,
        state.active.rotation,
        state.active.x + dx,
        state.active.y + dy,
    )
    if not can_place(state.board, candidate):
        return False
    state.active = candidate
    return True


def try_rotate(state: GameState, clockwise: bool = True) -> bool:
    """Rotate the active piece, applying small wall/floor kicks when needed."""
    delta = 1 if clockwise else -1
    rotation = (state.active.rotation + delta) % 4
    for kick_x, kick_y in ROTATION_KICKS:
        candidate = Piece(
            state.active.kind,
            rotation,
            state.active.x + kick_x,
            state.active.y + kick_y,
        )
        if can_place(state.board, candidate):
            state.active = candidate
            return True
    return False


def refill_bag(rng: Random) -> list[str]:
    """Return a shuffled seven-bag containing every tetromino exactly once."""
    bag = list(PIECE_TYPES)
    rng.shuffle(bag)
    return bag


def draw_kind(bag: list[str], rng: Random) -> str:
    """Draw from a seven-bag, refilling it when empty."""
    if not bag:
        bag.extend(refill_bag(rng))
    return bag.pop()


def new_game(rng: Random | None = None) -> GameState:
    """Create a new Tetris session with a seven-bag randomizer."""
    generator = rng or Random()
    bag: list[str] = []
    active_kind = draw_kind(bag, generator)
    next_kind = draw_kind(bag, generator)
    state = GameState(empty_board(), spawn_piece(active_kind), next_kind, bag)
    if not can_place(state.board, state.active):
        state.game_over = True
    return state


def level_for_lines(lines: int) -> int:
    """Return the zero-based level; every ten cleared lines advances a level."""
    if isinstance(lines, bool) or not isinstance(lines, int) or lines < 0:
        raise ValueError("Lines must be a non-negative integer.")
    return lines // 10


def drop_interval(level: int) -> float:
    """Return gravity interval for a level, bounded for terminal playability."""
    if isinstance(level, bool) or not isinstance(level, int) or level < 0:
        raise ValueError("Level must be a non-negative integer.")
    return max(MIN_DROP_INTERVAL, BASE_DROP_INTERVAL * (DROP_ACCELERATION**level))


def line_clear_score(cleared: int, level: int) -> int:
    """Return classic line-clear points for 1-4 simultaneous lines."""
    if cleared == 0:
        return 0
    if cleared not in LINE_CLEAR_SCORES:
        raise ValueError("A tetromino can clear at most four lines at once.")
    if isinstance(level, bool) or not isinstance(level, int) or level < 0:
        raise ValueError("Level must be a non-negative integer.")
    return LINE_CLEAR_SCORES[cleared] * (level + 1)


def clear_full_lines(board: Board) -> tuple[Board, int]:
    """Remove full rows and insert the same number of empty rows at the top."""
    if len(board) != HEIGHT or any(len(row) != WIDTH for row in board):
        raise ValueError("Board dimensions do not match Tetris.")
    remaining = [row[:] for row in board if any(cell == EMPTY for cell in row)]
    cleared = HEIGHT - len(remaining)
    empty_rows = [[EMPTY for _ in range(WIDTH)] for _ in range(cleared)]
    return [*empty_rows, *remaining], cleared


def lock_piece(state: GameState, rng: Random) -> int:
    """Lock the active piece, clear lines, score them, and spawn the next piece."""
    if not can_place(state.board, state.active):
        raise ValueError("Cannot lock an invalid active piece.")

    for x, y in piece_cells(state.active):
        state.board[y][x] = state.active.kind

    old_level = level_for_lines(state.lines)
    state.board, cleared = clear_full_lines(state.board)
    state.score += line_clear_score(cleared, old_level)
    state.lines += cleared

    state.active = spawn_piece(state.next_kind)
    state.next_kind = draw_kind(state.bag, rng)
    state.game_over = not can_place(state.board, state.active)
    return cleared


def gravity_step(state: GameState, rng: Random) -> tuple[bool, int]:
    """Advance gravity once; lock when downward movement is blocked."""
    if state.game_over:
        return False, 0
    if try_move(state, 0, 1):
        return True, 0
    return False, lock_piece(state, rng)


def soft_drop(state: GameState, rng: Random) -> tuple[bool, int]:
    """Move down one row for one point, or lock when already grounded."""
    if state.game_over:
        return False, 0
    if try_move(state, 0, 1):
        state.score += 1
        return True, 0
    return False, lock_piece(state, rng)


def hard_drop(state: GameState, rng: Random) -> tuple[int, int]:
    """Drop to the floor, award two points per row, then lock immediately."""
    if state.game_over:
        return 0, 0
    distance = 0
    while try_move(state, 0, 1):
        distance += 1
    state.score += distance * 2
    cleared = lock_piece(state, rng)
    return distance, cleared


def _preview_lines(kind: str) -> list[str]:
    cells = set(ROTATIONS[kind][0])
    return [
        "".join("[]" if (x, y) in cells else "  " for x in range(4))
        for y in range(4)
    ]


def render_board(state: GameState, best_score: int = 0, status: str = "") -> str:
    """Render a complete Tetris frame with the next-piece preview."""
    active_cells = set(piece_cells(state.active)) if not state.game_over else set()
    top = "+" + "-" * (WIDTH * 2) + "+"
    preview = _preview_lines(state.next_kind)
    level = level_for_lines(state.lines)
    lines = [
        "=== Tetris ===",
        "Arrows: move/soft-drop/rotate | Space: hard drop | P: pause | S: save | Q/Esc: quit",
        f"Score: {state.score}   Lines: {state.lines}   Level: {level}   Best: {best_score}",
    ]
    if status:
        lines.append(status)
    lines.append(top + f"   Next: {state.next_kind}")

    for y in range(HEIGHT):
        cells: list[str] = []
        for x in range(WIDTH):
            if (x, y) in active_cells:
                cells.append("<>")
            elif state.board[y][x] != EMPTY:
                cells.append("[]")
            else:
                cells.append("  ")
        side = f"   {preview[y]}" if y < len(preview) else ""
        lines.append("|" + "".join(cells) + "|" + side)
    lines.append(top)
    return "\n".join(lines)


def serialize_session(state: GameState) -> dict[str, Any]:
    """Serialize the full in-progress state required to resume Tetris."""
    return {
        "version": SAVE_VERSION,
        "board": [row[:] for row in state.board],
        "active": {
            "kind": state.active.kind,
            "rotation": state.active.rotation,
            "x": state.active.x,
            "y": state.active.y,
        },
        "next_kind": state.next_kind,
        "bag": state.bag[:],
        "score": state.score,
        "lines": state.lines,
    }


def _decode_nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid saved {label}.")
    return value


def deserialize_session(payload: dict[str, Any]) -> GameState:
    """Validate and restore a saved Tetris session."""
    if not isinstance(payload, dict) or payload.get("version") != SAVE_VERSION:
        raise ValueError("Unsupported Tetris save version.")

    raw_board = payload.get("board")
    if not isinstance(raw_board, list) or len(raw_board) != HEIGHT:
        raise ValueError("Invalid saved board height.")
    board: Board = []
    allowed_cells = {EMPTY, *PIECE_TYPES}
    for raw_row in raw_board:
        if not isinstance(raw_row, list) or len(raw_row) != WIDTH:
            raise ValueError("Invalid saved board width.")
        if any(not isinstance(cell, str) or cell not in allowed_cells for cell in raw_row):
            raise ValueError("Invalid saved board cell.")
        board.append(raw_row[:])

    raw_active = payload.get("active")
    if not isinstance(raw_active, dict):
        raise ValueError("Invalid saved active piece.")
    kind = raw_active.get("kind")
    if kind not in PIECE_TYPES:
        raise ValueError("Invalid saved active piece kind.")
    rotation = raw_active.get("rotation")
    x = raw_active.get("x")
    y = raw_active.get("y")
    if (
        isinstance(rotation, bool)
        or not isinstance(rotation, int)
        or rotation not in range(4)
        or isinstance(x, bool)
        or not isinstance(x, int)
        or isinstance(y, bool)
        or not isinstance(y, int)
    ):
        raise ValueError("Invalid saved active piece position.")
    active = Piece(str(kind), rotation, x, y)

    next_kind = payload.get("next_kind")
    if next_kind not in PIECE_TYPES:
        raise ValueError("Invalid saved next piece.")

    raw_bag = payload.get("bag")
    if (
        not isinstance(raw_bag, list)
        or len(raw_bag) > len(PIECE_TYPES)
        or any(kind not in PIECE_TYPES for kind in raw_bag)
        or len(set(raw_bag)) != len(raw_bag)
    ):
        raise ValueError("Invalid saved seven-bag.")

    score = _decode_nonnegative_int(payload.get("score"), "score")
    lines = _decode_nonnegative_int(payload.get("lines"), "lines")
    state = GameState(board, active, str(next_kind), list(raw_bag), score, lines)
    if not can_place(state.board, state.active):
        raise ValueError("Saved active piece collides with the board.")
    return state


def is_quit_key(key: str | None) -> bool:
    return key is not None and key.lower() in QUIT_KEYS


def is_save_key(key: str | None) -> bool:
    return key is not None and key.lower() in SAVE_KEYS


def is_pause_key(key: str | None) -> bool:
    return key is not None and key.lower() in PAUSE_KEYS


def _status_for_lock(cleared: int) -> str:
    if cleared == 4:
        return "TETRIS! Four lines cleared."
    if cleared:
        return f"Cleared {cleared} line{'s' if cleared != 1 else ''}."
    return ""


def _observe_score(best: BestScoreTracker, state: GameState, status: str) -> str:
    if best.observe(state.score):
        return f"New Best: {best.best_score}" + (f" | {status}" if status else "")
    return status


def _flush_best_score(best: BestScoreTracker) -> None:
    """Persist a buffered record only at explicit non-gameplay I/O points."""
    best.flush()


def _save_live_state(state: GameState, best: BestScoreTracker) -> str:
    """Save game and buffered Best Score; explicit Save is an allowed I/O point."""
    try:
        save_state(GAME_ID, serialize_session(state))
    except ProgressDataError:
        return "Save failed."
    try:
        _flush_best_score(best)
    except ProgressDataError:
        return "Game saved; Best Score sync failed."
    return "Game saved."


def play_round(rng: Random | None = None, saved: GameState | None = None) -> bool:
    """Play one real-time Tetris round. Return False when the player quits."""
    generator = rng or Random()
    state = saved if saved is not None else new_game(generator)
    best = BestScoreTracker.load(GAME_ID, state.score)
    status = ""
    paused = False

    if not sys.stdin.isatty():
        print("Tetris requires an interactive terminal (TTY).")
        return False

    print("\033[2J\033[?25l", end="", flush=True)
    try:
        try:
            with KeyReader() as reader:
                next_drop = time.monotonic() + drop_interval(level_for_lines(state.lines))
                while not state.game_over:
                    frame_status = "PAUSED - press P to resume." if paused else status
                    print(
                        "\033[H" + render_board(state, best.best_score, frame_status),
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
                            next_drop = time.monotonic() + drop_interval(
                                level_for_lines(state.lines)
                            )
                        continue

                    remaining = max(0.0, next_drop - time.monotonic())
                    key = reader.read_key(remaining)

                    if is_quit_key(key):
                        try:
                            _flush_best_score(best)
                        except ProgressDataError:
                            pass
                        return False

                    if is_save_key(key):
                        status = _save_live_state(state, best)
                        next_drop = time.monotonic() + drop_interval(
                            level_for_lines(state.lines)
                        )
                        continue

                    if is_pause_key(key):
                        paused = True
                        status = ""
                        continue

                    if key is None:
                        _, cleared = gravity_step(state, generator)
                        status = _status_for_lock(cleared)
                        status = _observe_score(best, state, status)
                        next_drop = time.monotonic() + drop_interval(
                            level_for_lines(state.lines)
                        )
                        continue

                    cleared = 0
                    score_may_change = False
                    if key == "left":
                        try_move(state, -1, 0)
                    elif key == "right":
                        try_move(state, 1, 0)
                    elif key == "up":
                        try_rotate(state)
                    elif key == "down":
                        _, cleared = soft_drop(state, generator)
                        score_may_change = True
                        next_drop = time.monotonic() + drop_interval(
                            level_for_lines(state.lines)
                        )
                    elif key == " ":
                        _, cleared = hard_drop(state, generator)
                        score_may_change = True
                        next_drop = time.monotonic() + drop_interval(
                            level_for_lines(state.lines)
                        )
                    else:
                        continue

                    status = _status_for_lock(cleared)
                    if score_may_change:
                        status = _observe_score(best, state, status)
        except KeyboardInterrupt:
            try:
                _flush_best_score(best)
            except ProgressDataError:
                pass
            return False
    finally:
        print("\033[?25h", flush=True)

    try:
        _flush_best_score(best)
        clear_save(GAME_ID)
    except ProgressDataError as exc:
        print(f"\nProgress data error after game over: {exc}")

    print("\nGame over.")
    print(f"Final score: {state.score}")
    print(f"Lines cleared: {state.lines}")
    print(f"Best Score: {best.best_score}")
    return True


def _load_saved_game() -> GameState | None:
    try:
        payload = load_state(GAME_ID)
    except ProgressDataError as exc:
        print(f"\nCould not load Tetris: {exc}")
        return None
    if payload is None:
        return None
    try:
        return deserialize_session(payload)
    except ValueError as exc:
        print(f"\nSaved game is invalid: {exc}")
        return None


def main() -> None:
    """Run Tetris."""
    print("=== Tetris ===")
    print("Move in real time with the arrow keys; no Enter is required.")
    print("Up rotates, Down soft-drops, and Space hard-drops.")
    print("Press P to pause, S to save, and Q or Esc to quit.")

    while True:
        action = choose_session_action(GAME_ID, "Tetris")
        if action == QUIT:
            print("Goodbye.")
            return

        saved = None
        if action == LOAD:
            saved = _load_saved_game()
            if saved is None:
                continue
            print("\nSaved game loaded.")
        elif action != NEW:
            continue

        if not play_round(saved=saved):
            print("\nGoodbye.")
            return

        again = input("\nPlay another round? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return
        print()


if __name__ == "__main__":
    main()
