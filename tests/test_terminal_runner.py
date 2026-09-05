"""Tests for the real-time Terminal Runner game."""

from __future__ import annotations

import random
import unittest
from unittest.mock import Mock, patch

from games import terminal_runner as runner


class TerminalRunnerTests(unittest.TestCase):
    def test_obstacle_specs_are_well_formed_and_varied(self) -> None:
        self.assertGreaterEqual(len(runner.OBSTACLE_SPECS), 7)
        self.assertEqual(len(runner.OBSTACLE_SPECS), len(runner.OBSTACLE_BY_KIND))
        self.assertTrue(any(spec.pit for spec in runner.OBSTACLE_SPECS))
        shapes = {(spec.width, spec.height) for spec in runner.OBSTACLE_SPECS}
        self.assertGreaterEqual(len(shapes), 5)

    def test_score_uses_distance_and_passed_bonus(self) -> None:
        state = runner.GameState(distance=12.3, obstacles_passed=2)
        self.assertEqual(173, runner.score_for_state(state))

    def test_speed_profiles_offer_distinct_starting_speeds(self) -> None:
        starts = [
            runner.speed_for_level(1, mode) / runner.BASE_SPEED
            for mode in runner.SPEED_PROFILES
        ]
        self.assertEqual(sorted(starts), starts)
        self.assertEqual(4, len(set(starts)))
        self.assertAlmostEqual(0.85, starts[0])
        self.assertAlmostEqual(1.50, starts[-1])

    def test_speed_increases_and_caps_at_three_x(self) -> None:
        self.assertEqual(runner.BASE_SPEED, runner.speed_for_level(1, "normal"))
        self.assertGreater(runner.speed_for_level(3, "normal"), runner.BASE_SPEED)
        self.assertEqual(runner.MAX_SPEED, runner.speed_for_level(100, "expert"))
        self.assertAlmostEqual(3.0, runner.MAX_SPEED / runner.BASE_SPEED)

    def test_fast_levels_last_longer_for_adaptation(self) -> None:
        early = runner.level_duration(1, "normal")
        medium = runner.level_duration(13, "normal")
        maximum = runner.level_duration(100, "normal")
        self.assertEqual(runner.BASE_LEVEL_DURATION, early)
        self.assertGreater(medium, early)
        self.assertGreater(maximum, medium)
        self.assertEqual(runner.MAX_LEVEL_DURATION, maximum)

    def test_level_clock_advances_by_active_time(self) -> None:
        state = runner.GameState(speed_mode="normal")
        duration = runner.level_duration(1, "normal")
        state.level_elapsed = duration - 0.02
        runner.step_game(state, 0.05, random.Random(1))
        self.assertEqual(2, state.level)
        self.assertAlmostEqual(0.03, state.level_elapsed, places=6)

    def test_level_time_remaining_uses_current_profile(self) -> None:
        state = runner.GameState(speed_mode="fast", level=7, level_elapsed=2.0)
        expected = runner.level_duration(7, "fast") - 2.0
        self.assertAlmostEqual(expected, runner.level_time_remaining(state))

    def test_jump_starts_only_on_ground(self) -> None:
        state = runner.GameState()
        self.assertTrue(runner.try_jump(state))
        self.assertFalse(runner.try_jump(state))

    def test_jump_returns_to_ground_and_reaches_required_height(self) -> None:
        state = runner.GameState()
        runner.try_jump(state)
        peak = 0.0
        for _ in range(300):
            runner.advance_player(state, 0.01)
            peak = max(peak, state.player_y)
            if runner.is_grounded(state):
                break
        self.assertGreater(peak, 3.0)
        self.assertTrue(runner.is_grounded(state))
        self.assertEqual(0.0, state.player_y)

    def test_grounded_runner_hits_solid_obstacle(self) -> None:
        obstacle = runner.Obstacle(
            runner.OBSTACLE_BY_KIND["crate"],
            runner.PLAYER_X + 0.5,
        )
        self.assertTrue(runner.collides_with_player(runner.GameState(), obstacle))

    def test_high_jump_clears_tall_obstacle(self) -> None:
        state = runner.GameState(player_y=3.1, player_vy=0.1)
        obstacle = runner.Obstacle(
            runner.OBSTACLE_BY_KIND["pillar"],
            runner.PLAYER_X + 0.5,
        )
        self.assertFalse(runner.collides_with_player(state, obstacle))

    def test_pit_hits_grounded_runner_but_not_airborne_runner(self) -> None:
        obstacle = runner.Obstacle(
            runner.OBSTACLE_BY_KIND["pit"],
            runner.PLAYER_X + 0.5,
        )
        self.assertTrue(runner.collides_with_player(runner.GameState(), obstacle))
        airborne = runner.GameState(player_y=0.5, player_vy=1.0)
        self.assertFalse(runner.collides_with_player(airborne, obstacle))

    def test_no_horizontal_overlap_means_no_collision(self) -> None:
        obstacle = runner.Obstacle(runner.OBSTACLE_BY_KIND["pillar"], 30.0)
        self.assertFalse(runner.collides_with_player(runner.GameState(), obstacle))

    def test_level_one_contains_only_beginner_obstacles(self) -> None:
        kinds = {spec.kind for spec in runner.eligible_obstacles(1)}
        self.assertEqual({"crate", "rock", "spikes"}, kinds)

    def test_higher_levels_unlock_more_obstacles(self) -> None:
        kinds = {spec.kind for spec in runner.eligible_obstacles(4)}
        self.assertIn("pit", kinds)
        self.assertIn("double", kinds)
        self.assertEqual({spec.kind for spec in runner.OBSTACLE_SPECS}, kinds)

    def test_weighted_choice_never_bypasses_level_gate(self) -> None:
        rng = random.Random(2)
        for _ in range(100):
            self.assertLessEqual(runner.choose_obstacle(1, rng).min_level, 1)

    def test_spawn_distance_never_drops_below_fair_minimum(self) -> None:
        rng = random.Random(3)
        for speed in (runner.BASE_SPEED, 12.0, runner.MAX_SPEED):
            minimum = runner.minimum_spawn_distance(speed)
            for _ in range(100):
                gap = runner.next_spawn_distance(speed, rng)
                self.assertGreaterEqual(gap, minimum)
                self.assertLessEqual(gap, minimum + runner.EXTRA_SPAWN_DISTANCE)

    def test_high_speed_spawn_spacing_keeps_reaction_time(self) -> None:
        minimum = runner.minimum_spawn_distance(runner.MAX_SPEED)
        max_width = max(spec.width for spec in runner.OBSTACLE_SPECS)
        reaction_distance = minimum - max_width
        self.assertGreaterEqual(
            reaction_distance / runner.MAX_SPEED,
            runner.MIN_REACTION_TIME,
        )

    def test_step_moves_obstacles_and_advances_distance(self) -> None:
        obstacle = runner.Obstacle(runner.OBSTACLE_BY_KIND["rock"], 50.0)
        state = runner.GameState(obstacles=[obstacle], spawn_remaining=999.0)
        runner.step_game(state, 0.1, random.Random(1))
        self.assertGreater(state.distance, 0.0)
        self.assertLess(obstacle.x, 50.0)

    def test_step_spawns_obstacle_when_spawn_distance_expires(self) -> None:
        state = runner.GameState(spawn_remaining=0.01)
        runner.step_game(state, 0.1, random.Random(1))
        self.assertEqual(1, len(state.obstacles))
        self.assertGreater(state.spawn_remaining, 0.0)

    def test_passed_obstacle_is_counted_once(self) -> None:
        spec = runner.OBSTACLE_BY_KIND["rock"]
        obstacle = runner.Obstacle(spec, runner.PLAYER_X - spec.width - 0.2)
        state = runner.GameState(obstacles=[obstacle], spawn_remaining=999.0)
        runner.step_game(state, 0.05, random.Random(1))
        runner.step_game(state, 0.05, random.Random(1))
        self.assertEqual(1, state.obstacles_passed)

    def test_collision_marks_game_over(self) -> None:
        obstacle = runner.Obstacle(
            runner.OBSTACLE_BY_KIND["crate"],
            runner.PLAYER_X + 0.5,
        )
        state = runner.GameState(obstacles=[obstacle], spawn_remaining=999.0)
        runner.step_game(state, 0.05, random.Random(1))
        self.assertFalse(state.alive)
        self.assertEqual("crate", state.collision_kind)

    def test_save_round_trip_restores_speed_level_physics_and_obstacles(self) -> None:
        state = runner.GameState(
            player_y=1.2,
            player_vy=4.5,
            distance=123.4,
            obstacles_passed=8,
            spawn_remaining=15.0,
            frame_index=77,
            speed_mode="fast",
            level=9,
            level_elapsed=3.2,
        )
        state.obstacles = [
            runner.Obstacle(runner.OBSTACLE_BY_KIND["rock"], 30.5),
            runner.Obstacle(runner.OBSTACLE_BY_KIND["pit"], 50.0),
        ]
        restored = runner.deserialize_session(runner.serialize_session(state))
        self.assertAlmostEqual(state.player_y, restored.player_y)
        self.assertAlmostEqual(state.player_vy, restored.player_vy)
        self.assertAlmostEqual(state.distance, restored.distance)
        self.assertEqual("fast", restored.speed_mode)
        self.assertEqual(9, restored.level)
        self.assertAlmostEqual(3.2, restored.level_elapsed)
        self.assertEqual(
            [obstacle.spec.kind for obstacle in state.obstacles],
            [obstacle.spec.kind for obstacle in restored.obstacles],
        )

    def test_legacy_preview_save_migrates_to_normal_mode(self) -> None:
        state = runner.GameState(distance=123.4, obstacles_passed=8)
        payload = runner.serialize_session(state)
        payload["version"] = runner.LEGACY_SAVE_VERSION
        payload.pop("speed_mode")
        payload.pop("level")
        payload.pop("level_elapsed")
        restored = runner.deserialize_session(payload)
        expected_score = runner.score_for_state(state)
        expected_level = expected_score // runner.LEGACY_LEVEL_SCORE_STEP + 1
        self.assertEqual("normal", restored.speed_mode)
        self.assertEqual(expected_level, restored.level)
        self.assertEqual(0.0, restored.level_elapsed)

    def test_invalid_save_rejects_unknown_speed_mode(self) -> None:
        payload = runner.serialize_session(runner.GameState())
        payload["speed_mode"] = "warp"
        with self.assertRaises(ValueError):
            runner.deserialize_session(payload)

    def test_invalid_save_rejects_elapsed_time_beyond_level(self) -> None:
        state = runner.GameState(speed_mode="normal", level=1)
        payload = runner.serialize_session(state)
        payload["level_elapsed"] = runner.level_duration(1, "normal") + 0.1
        with self.assertRaises(ValueError):
            runner.deserialize_session(payload)

    def test_invalid_save_rejects_unknown_obstacle(self) -> None:
        payload = runner.serialize_session(runner.GameState())
        payload["obstacles"] = [{"kind": "dragon", "x": 30.0, "counted": False}]
        with self.assertRaises(ValueError):
            runner.deserialize_session(payload)

    def test_invalid_save_rejects_existing_collision(self) -> None:
        payload = runner.serialize_session(runner.GameState())
        payload["obstacles"] = [
            {
                "kind": "crate",
                "x": runner.PLAYER_X + 0.5,
                "counted": False,
            }
        ]
        with self.assertRaises(ValueError):
            runner.deserialize_session(payload)

    def test_invalid_save_rejects_nonfinite_number(self) -> None:
        payload = runner.serialize_session(runner.GameState())
        payload["distance"] = float("inf")
        with self.assertRaises(ValueError):
            runner.deserialize_session(payload)

    def test_render_contains_speed_mode_countdown_stats_and_obstacle(self) -> None:
        state = runner.GameState(
            speed_mode="fast",
            obstacles=[runner.Obstacle(runner.OBSTACLE_BY_KIND["crate"], 30.0)],
        )
        text = runner.render_world(state, 123)
        self.assertIn("Terminal Runner", text)
        self.assertIn("Best: 00123", text)
        self.assertIn("Mode: Fast", text)
        self.assertIn("Next:", text)
        self.assertIn("Space/Up: jump", text)
        self.assertIn("[]", text)
        self.assertIn("===", text)

    def test_render_pause_message(self) -> None:
        self.assertIn("PAUSED", runner.render_world(runner.GameState(), paused=True))

    def test_choose_speed_mode_accepts_number_and_name(self) -> None:
        with patch("builtins.input", return_value="3"):
            self.assertEqual("fast", runner.choose_speed_mode())
        with patch("builtins.input", return_value="expert"):
            self.assertEqual("expert", runner.choose_speed_mode())
        with patch("builtins.input", return_value="q"):
            self.assertIsNone(runner.choose_speed_mode())

    def test_key_aliases_include_arabic_physical_keys(self) -> None:
        self.assertTrue(runner.is_jump_key(" "))
        self.assertTrue(runner.is_jump_key("up"))
        self.assertTrue(runner.is_pause_key("P"))
        self.assertTrue(runner.is_pause_key("ح"))
        self.assertTrue(runner.is_save_key("S"))
        self.assertTrue(runner.is_save_key("س"))
        self.assertTrue(runner.is_quit_key("Q"))
        self.assertTrue(runner.is_quit_key("ض"))

    def test_explicit_save_flushes_best_score_at_safe_point(self) -> None:
        state = runner.GameState(distance=10.0)
        best = Mock()
        with patch("games.terminal_runner.save_state") as save_state:
            status = runner._save_live_state(state, best)
        self.assertEqual("Run saved.", status)
        save_state.assert_called_once()
        best.flush.assert_called_once_with()

    def test_step_game_performs_no_progress_file_io(self) -> None:
        state = runner.GameState(spawn_remaining=999.0)
        with (
            patch("games.terminal_runner.save_state") as save_state,
            patch("games.terminal_runner.load_state") as load_state,
            patch("games.terminal_runner.clear_save") as clear_save,
        ):
            runner.step_game(state, 0.05, random.Random(1))
        save_state.assert_not_called()
        load_state.assert_not_called()
        clear_save.assert_not_called()

    def test_invalid_numeric_and_speed_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            runner.speed_for_level(0)
        with self.assertRaises(ValueError):
            runner.speed_for_level(1, "warp")
        with self.assertRaises(ValueError):
            runner.level_duration(0)
        with self.assertRaises(ValueError):
            runner.advance_level_clock(runner.GameState(), 0.0)
        with self.assertRaises(ValueError):
            runner.advance_player(runner.GameState(), 0.0)
        with self.assertRaises(ValueError):
            runner.minimum_spawn_distance(0.0)


if __name__ == "__main__":
    unittest.main()
