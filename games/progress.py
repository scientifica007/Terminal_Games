"""Shared local persistence for Terminal_Games.

The module intentionally keeps storage independent from any one game.  Current
progress is stored in one JSON document under the user's home directory, while
individual games own the schema of their saved state.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SCHEMA_VERSION = 1
DATA_DIR_ENV = "TERMINAL_GAMES_DATA_DIR"
DATA_FILE_NAME = "progress.json"


class ProgressDataError(RuntimeError):
    """Raised when persisted progress cannot be read safely."""


def data_file_path() -> Path:
    """Return the JSON progress file path.

    Tests and advanced users may override the directory with
    ``TERMINAL_GAMES_DATA_DIR``.  The default deliberately lives outside the
    repository so playing never dirties the Git working tree.
    """
    configured = os.environ.get(DATA_DIR_ENV)
    directory = Path(configured).expanduser() if configured else Path.home() / ".terminal_games"
    return directory / DATA_FILE_NAME


def _empty_store() -> dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "profile": {"mode": "local-anonymous", "username": None},
        "games": {},
    }


def _read_store() -> dict[str, Any]:
    path = data_file_path()
    if not path.exists():
        return _empty_store()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProgressDataError(f"Could not read progress data from {path}.") from exc

    if not isinstance(payload, dict) or payload.get("version") != SCHEMA_VERSION:
        raise ProgressDataError("Unsupported or invalid progress-data format.")
    if not isinstance(payload.get("games"), dict):
        raise ProgressDataError("Invalid progress-data games section.")
    return payload


def _write_store(store: dict[str, Any]) -> None:
    path = data_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write beside the destination and atomically replace it.  A crash during
    # serialization therefore cannot leave a half-written progress file.
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".progress-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(store, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temp_name = handle.name
        os.replace(temp_name, path)
    except OSError as exc:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
        raise ProgressDataError(f"Could not write progress data to {path}.") from exc


def _game_record(store: dict[str, Any], game_id: str) -> dict[str, Any]:
    games = store["games"]
    record = games.setdefault(game_id, {"save": None, "best_score": 0})
    if not isinstance(record, dict):
        raise ProgressDataError(f"Invalid progress record for {game_id}.")
    record.setdefault("save", None)
    record.setdefault("best_score", 0)
    return record


def has_saved_game(game_id: str) -> bool:
    """Return whether a game has a saved in-progress state."""
    return load_state(game_id) is not None


def save_state(game_id: str, state: dict[str, Any]) -> None:
    """Replace the single save slot for ``game_id``."""
    if not isinstance(state, dict):
        raise TypeError("Saved state must be a dictionary.")
    store = _read_store()
    record = _game_record(store, game_id)
    record["save"] = deepcopy(state)
    _write_store(store)


def load_state(game_id: str) -> dict[str, Any] | None:
    """Return a deep copy of the saved state, or ``None`` when no save exists."""
    store = _read_store()
    record = _game_record(store, game_id)
    state = record.get("save")
    if state is None:
        return None
    if not isinstance(state, dict):
        raise ProgressDataError(f"Invalid saved state for {game_id}.")
    return deepcopy(state)


def clear_save(game_id: str) -> bool:
    """Delete only the current save.  Best score is preserved."""
    store = _read_store()
    record = _game_record(store, game_id)
    existed = record.get("save") is not None
    record["save"] = None
    _write_store(store)
    return existed


def get_best_score(game_id: str) -> int:
    """Return the persistent best score for a game."""
    store = _read_store()
    record = _game_record(store, game_id)
    score = record.get("best_score", 0)
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ProgressDataError(f"Invalid best score for {game_id}.")
    return score


def update_best_score(game_id: str, score: int) -> bool:
    """Persist ``score`` when it exceeds the current best.

    Return ``True`` only when a new record was written.
    """
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("Score must be a non-negative integer.")

    store = _read_store()
    record = _game_record(store, game_id)
    current = record.get("best_score", 0)
    if isinstance(current, bool) or not isinstance(current, int) or current < 0:
        raise ProgressDataError(f"Invalid best score for {game_id}.")
    if score <= current:
        return False

    record["best_score"] = score
    _write_store(store)
    return True


def reset_game_data(game_id: str, *, include_best: bool = False) -> None:
    """Reset saved progress, optionally including the best score."""
    store = _read_store()
    record = _game_record(store, game_id)
    record["save"] = None
    if include_best:
        record["best_score"] = 0
    _write_store(store)
