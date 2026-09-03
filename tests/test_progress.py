import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from games.progress import (
    BestScoreTracker,
    DATA_DIR_ENV,
    ProgressDataError,
    clear_save,
    data_file_path,
    get_best_score,
    has_saved_game,
    load_state,
    reset_game_data,
    save_state,
    update_best_score,
)


class ProgressPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous = os.environ.get(DATA_DIR_ENV)
        os.environ[DATA_DIR_ENV] = self.temp_dir.name

    def tearDown(self) -> None:
        if self.previous is None:
            os.environ.pop(DATA_DIR_ENV, None)
        else:
            os.environ[DATA_DIR_ENV] = self.previous
        self.temp_dir.cleanup()

    def test_data_file_uses_configured_directory(self) -> None:
        self.assertEqual(
            data_file_path(),
            Path(self.temp_dir.name) / "progress.json",
        )

    def test_save_and_load_are_independent_copies(self) -> None:
        original = {"board": [[1, 2], [3, 4]], "score": 12}
        save_state("demo", original)
        original["board"][0][0] = 99

        loaded = load_state("demo")
        self.assertEqual(loaded, {"board": [[1, 2], [3, 4]], "score": 12})
        assert loaded is not None
        loaded["board"][0][0] = 88
        self.assertEqual(load_state("demo")["board"][0][0], 1)

    def test_clear_save_preserves_best_score(self) -> None:
        save_state("demo", {"turn": 4})
        update_best_score("demo", 500)
        self.assertTrue(clear_save("demo"))
        self.assertFalse(has_saved_game("demo"))
        self.assertEqual(get_best_score("demo"), 500)

    def test_best_score_only_increases(self) -> None:
        self.assertTrue(update_best_score("demo", 40))
        self.assertFalse(update_best_score("demo", 10))
        self.assertFalse(update_best_score("demo", 40))
        self.assertTrue(update_best_score("demo", 75))
        self.assertEqual(get_best_score("demo"), 75)

    def test_best_score_tracker_observes_without_disk_io(self) -> None:
        update_best_score("demo", 100)
        tracker = BestScoreTracker.load("demo")

        with patch("games.progress.update_best_score") as persist:
            self.assertTrue(tracker.observe(120))
            self.assertTrue(tracker.observe(140))
            self.assertFalse(tracker.observe(130))
            persist.assert_not_called()

            self.assertTrue(tracker.dirty)
            self.assertEqual(tracker.best_score, 140)
            persist.return_value = True
            self.assertTrue(tracker.flush())
            persist.assert_called_once_with("demo", 140)
            self.assertFalse(tracker.dirty)

    def test_best_score_tracker_flushes_only_when_dirty(self) -> None:
        update_best_score("demo", 80)
        tracker = BestScoreTracker.load("demo", current_score=80)

        with patch("games.progress.update_best_score") as persist:
            self.assertFalse(tracker.flush())
            persist.assert_not_called()

    def test_best_score_tracker_seeds_from_loaded_game_score(self) -> None:
        update_best_score("demo", 50)
        tracker = BestScoreTracker.load("demo", current_score=75)
        self.assertEqual(tracker.persisted_score, 50)
        self.assertEqual(tracker.best_score, 75)
        self.assertTrue(tracker.dirty)

    def test_reset_can_keep_or_clear_best(self) -> None:
        save_state("demo", {"turn": 1})
        update_best_score("demo", 90)
        reset_game_data("demo", include_best=False)
        self.assertIsNone(load_state("demo"))
        self.assertEqual(get_best_score("demo"), 90)

        save_state("demo", {"turn": 2})
        reset_game_data("demo", include_best=True)
        self.assertIsNone(load_state("demo"))
        self.assertEqual(get_best_score("demo"), 0)

    def test_file_is_utf8_json_and_reserves_profile_metadata(self) -> None:
        save_state("demo", {"label": "مرحبا"})
        payload = json.loads(data_file_path().read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["profile"]["mode"], "local-anonymous")
        self.assertIsNone(payload["profile"]["username"])

    def test_invalid_json_raises_clear_error(self) -> None:
        data_file_path().parent.mkdir(parents=True, exist_ok=True)
        data_file_path().write_text("{broken", encoding="utf-8")
        with self.assertRaises(ProgressDataError):
            get_best_score("demo")

    def test_negative_or_boolean_score_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            update_best_score("demo", -1)
        with self.assertRaises(ValueError):
            update_best_score("demo", True)
        tracker = BestScoreTracker("demo", 0, 0)
        with self.assertRaises(ValueError):
            tracker.observe(-1)
        with self.assertRaises(ValueError):
            tracker.observe(True)


if __name__ == "__main__":
    unittest.main()
