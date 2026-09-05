"""Fairness regression tests for Terminal Runner obstacle geometry."""

from __future__ import annotations

import random
import unittest

from games import terminal_runner as runner


class TerminalRunnerFairnessTests(unittest.TestCase):
    def test_every_obstacle_is_individually_jumpable_at_max_speed(self) -> None:
        """A correctly timed jump must clear every obstacle family at the 10x cap."""
        peak_time = runner.JUMP_VELOCITY / runner.GRAVITY
        player_center = runner.PLAYER_X + runner.PLAYER_HITBOX_WIDTH / 2

        for spec in runner.OBSTACLE_SPECS:
            with self.subTest(obstacle=spec.kind):
                obstacle_x = (
                    player_center
                    + runner.MAX_SPEED * peak_time
                    - spec.width / 2
                )
                state = runner.GameState(
                    obstacles=[runner.Obstacle(spec, obstacle_x)],
                    spawn_remaining=999.0,
                    speed_mode="expert",
                    level=runner.max_level_for_mode("expert"),
                )
                self.assertEqual(runner.MAX_SPEED, runner.current_speed(state))
                self.assertTrue(runner.try_jump(state))

                for _ in range(100):
                    runner.step_game(state, 0.02, random.Random(1))
                    self.assertTrue(
                        state.alive,
                        f"{spec.kind} cannot be cleared at maximum speed",
                    )
                    if (
                        not state.obstacles
                        or state.obstacles[0].x + spec.width < runner.PLAYER_X - 2
                    ):
                        break
                else:
                    self.fail(f"{spec.kind} did not pass the runner in expected time")


if __name__ == "__main__":
    unittest.main()
