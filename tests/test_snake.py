import random
import unittest

from games.snake import (
    ANSI_ARROW_KEYS,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    DIRECTION_KEYS,
    FOOD_SCORE,
    GameState,
    advance_snake,
    change_direction,
    decode_arrow_sequence,
    initial_snake,
    is_complete_arrow_sequence,
    new_game,
    next_head,
    place_food,
    render_board,
    wrap_position,
)


class SnakeTests(unittest.TestCase):
    def test_initial_snake_has_requested_length(self):
        snake = initial_snake(20, 10, 3)
        self.assertEqual(len(snake), 3)
        self.assertEqual(snake[0], (10, 5))
        self.assertEqual(snake, [(10, 5), (9, 5), (8, 5)])

    def test_small_board_is_rejected(self):
        with self.assertRaises(ValueError):
            initial_snake(4, 2, 3)

    def test_arrow_direction_mapping(self):
        self.assertEqual(DIRECTION_KEYS["up"], UP)
        self.assertEqual(DIRECTION_KEYS["down"], DOWN)
        self.assertEqual(DIRECTION_KEYS["right"], RIGHT)
        self.assertEqual(DIRECTION_KEYS["left"], LEFT)

    def test_ansi_arrow_sequences(self):
        self.assertEqual(ANSI_ARROW_KEYS["\x1b[A"], "up")
        self.assertEqual(ANSI_ARROW_KEYS["\x1b[B"], "down")
        self.assertEqual(ANSI_ARROW_KEYS["\x1b[C"], "right")
        self.assertEqual(ANSI_ARROW_KEYS["\x1b[D"], "left")

    def test_ss3_arrow_sequences(self):
        self.assertEqual(decode_arrow_sequence(b"\x1bOA"), "up")
        self.assertEqual(decode_arrow_sequence(b"\x1bOB"), "down")
        self.assertEqual(decode_arrow_sequence(b"\x1bOC"), "right")
        self.assertEqual(decode_arrow_sequence(b"\x1bOD"), "left")

    def test_modified_csi_arrow_sequences(self):
        self.assertEqual(decode_arrow_sequence(b"\x1b[1;2A"), "up")
        self.assertEqual(decode_arrow_sequence(b"\x1b[1;5B"), "down")
        self.assertEqual(decode_arrow_sequence(b"\x1b[1;3C"), "right")
        self.assertEqual(decode_arrow_sequence(b"\x1b[1;4D"), "left")

    def test_invalid_escape_sequence_returns_none(self):
        self.assertIsNone(decode_arrow_sequence(b"\x1b[Z"))
        self.assertIsNone(decode_arrow_sequence(b"x"))

    def test_bytearray_arrow_completion_is_hash_safe(self):
        self.assertTrue(is_complete_arrow_sequence(bytearray(b"\x1b[A")))
        self.assertTrue(is_complete_arrow_sequence(bytearray(b"\x1bOD")))
        self.assertFalse(is_complete_arrow_sequence(bytearray(b"\x1b[")))

    def test_change_direction_accepts_perpendicular_turn(self):
        self.assertEqual(change_direction(RIGHT, "up"), UP)

    def test_change_direction_blocks_reverse_turn(self):
        self.assertEqual(change_direction(RIGHT, "left"), RIGHT)
        self.assertEqual(change_direction(UP, "down"), UP)

    def test_unknown_key_keeps_direction(self):
        self.assertEqual(change_direction(DOWN, "z"), DOWN)

    def test_next_head(self):
        self.assertEqual(next_head((5, 5), UP), (5, 4))
        self.assertEqual(next_head((5, 5), RIGHT), (6, 5))

    def test_wrap_position_across_all_edges(self):
        self.assertEqual(wrap_position((-1, 2), 10, 6), (9, 2))
        self.assertEqual(wrap_position((10, 2), 10, 6), (0, 2))
        self.assertEqual(wrap_position((3, -1), 10, 6), (3, 5))
        self.assertEqual(wrap_position((3, 6), 10, 6), (3, 0))

    def test_advance_moves_without_growth(self):
        snake = [(3, 2), (2, 2), (1, 2)]
        result, ate, alive = advance_snake(snake, RIGHT, (8, 8), 10, 10)
        self.assertTrue(alive)
        self.assertFalse(ate)
        self.assertEqual(result, [(4, 2), (3, 2), (2, 2)])

    def test_eating_food_grows_snake(self):
        snake = [(3, 2), (2, 2), (1, 2)]
        result, ate, alive = advance_snake(snake, RIGHT, (4, 2), 10, 10)
        self.assertTrue(alive)
        self.assertTrue(ate)
        self.assertEqual(result, [(4, 2), (3, 2), (2, 2), (1, 2)])

    def test_horizontal_edge_wraps(self):
        snake = [(0, 2), (1, 2), (2, 2)]
        result, ate, alive = advance_snake(snake, LEFT, None, 10, 10)
        self.assertTrue(alive)
        self.assertFalse(ate)
        self.assertEqual(result[0], (9, 2))

    def test_vertical_edge_wraps(self):
        snake = [(4, 0), (4, 1), (4, 2)]
        result, ate, alive = advance_snake(snake, UP, None, 10, 6)
        self.assertTrue(alive)
        self.assertFalse(ate)
        self.assertEqual(result[0], (4, 5))

    def test_self_collision_ends_round(self):
        snake = [(2, 2), (2, 3), (1, 3), (1, 2), (1, 1), (2, 1)]
        _, ate, alive = advance_snake(snake, DOWN, None, 10, 10)
        self.assertFalse(alive)
        self.assertFalse(ate)

    def test_wrapped_self_collision_still_ends_round(self):
        snake = [(0, 2), (9, 2), (9, 3), (0, 3)]
        _, ate, alive = advance_snake(snake, LEFT, None, 10, 10)
        self.assertFalse(alive)
        self.assertFalse(ate)

    def test_moving_into_vacating_tail_is_legal(self):
        snake = [(2, 2), (2, 3), (1, 3), (1, 2)]
        result, ate, alive = advance_snake(snake, LEFT, None, 10, 10)
        self.assertTrue(alive)
        self.assertFalse(ate)
        self.assertEqual(result[0], (1, 2))

    def test_place_food_never_uses_snake_cell(self):
        snake = [(0, 0), (1, 0), (2, 0)]
        food = place_food(snake, 4, 4, random.Random(7))
        self.assertIsNotNone(food)
        self.assertNotIn(food, snake)

    def test_place_food_returns_none_when_full(self):
        snake = [(0, 0), (1, 0), (0, 1), (1, 1)]
        self.assertIsNone(place_food(snake, 2, 2, random.Random(1)))

    def test_new_game_has_food_and_rightward_direction(self):
        state = new_game(12, 8, random.Random(4))
        self.assertEqual(state.direction, RIGHT)
        self.assertIsNotNone(state.food)
        self.assertNotIn(state.food, state.snake)

    def test_rendering_contains_head_body_food_score_and_wrap_hint(self):
        state = GameState(
            snake=[(2, 1), (1, 1), (0, 1)],
            direction=RIGHT,
            food=(3, 2),
            score=FOOD_SCORE * 2,
        )
        rendered = render_board(state, 5, 4, "Normal")
        self.assertIn("@", rendered)
        self.assertIn("o", rendered)
        self.assertIn("*", rendered)
        self.assertIn("Score: 20", rendered)
        self.assertIn("Normal", rendered)
        self.assertIn("Arrow keys", rendered)
        self.assertIn("wrap", rendered)


if __name__ == "__main__":
    unittest.main()
