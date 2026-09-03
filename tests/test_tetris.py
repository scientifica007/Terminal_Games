import random
import unittest
from unittest.mock import Mock, patch

from games.tetris import (
    BASE_DROP_INTERVAL,
    HEIGHT,
    LINE_CLEAR_SCORES,
    MIN_DROP_INTERVAL,
    PIECE_TYPES,
    ROTATIONS,
    WIDTH,
    GameState,
    Piece,
    _observe_score,
    _save_live_state,
    can_place,
    clear_full_lines,
    deserialize_session,
    draw_kind,
    drop_interval,
    empty_board,
    gravity_step,
    hard_drop,
    is_pause_key,
    is_quit_key,
    is_save_key,
    level_for_lines,
    line_clear_score,
    lock_piece,
    new_game,
    piece_cells,
    refill_bag,
    render_board,
    serialize_session,
    soft_drop,
    spawn_piece,
    try_move,
    try_rotate,
)


class TetrisTests(unittest.TestCase):
    def test_seven_piece_types_are_present(self):
        self.assertEqual(set(PIECE_TYPES), {"I", "O", "T", "S", "Z", "J", "L"})
        self.assertEqual(len(PIECE_TYPES), 7)

    def test_every_rotation_has_four_unique_cells_inside_local_box(self):
        for kind in PIECE_TYPES:
            self.assertEqual(len(ROTATIONS[kind]), 4)
            for rotation in ROTATIONS[kind]:
                self.assertEqual(len(rotation), 4)
                self.assertEqual(len(set(rotation)), 4)
                self.assertTrue(all(0 <= x < 4 and 0 <= y < 4 for x, y in rotation))

    def test_empty_board_dimensions(self):
        board = empty_board()
        self.assertEqual(len(board), HEIGHT)
        self.assertTrue(all(len(row) == WIDTH for row in board))
        self.assertTrue(all(not cell for row in board for cell in row))

    def test_refill_bag_contains_each_piece_once(self):
        bag = refill_bag(random.Random(3))
        self.assertEqual(len(bag), 7)
        self.assertEqual(set(bag), set(PIECE_TYPES))

    def test_drawing_seven_times_consumes_one_complete_bag(self):
        rng = random.Random(8)
        bag = []
        drawn = [draw_kind(bag, rng) for _ in range(7)]
        self.assertEqual(set(drawn), set(PIECE_TYPES))
        self.assertEqual(bag, [])

    def test_new_game_has_valid_active_piece(self):
        state = new_game(random.Random(4))
        self.assertIn(state.active.kind, PIECE_TYPES)
        self.assertIn(state.next_kind, PIECE_TYPES)
        self.assertEqual(len(state.bag), 5)
        self.assertTrue(can_place(state.board, state.active))
        self.assertFalse(state.game_over)

    def test_piece_cells_use_piece_origin_and_rotation(self):
        piece = Piece("T", 0, 3, 5)
        self.assertEqual(set(piece_cells(piece)), {(4, 5), (3, 6), (4, 6), (5, 6)})

    def test_can_place_rejects_walls_floor_and_locked_cells(self):
        board = empty_board()
        self.assertFalse(can_place(board, Piece("I", 0, -1, 0)))
        self.assertFalse(can_place(board, Piece("I", 1, 0, HEIGHT - 3)))
        piece = spawn_piece("O")
        x, y = piece_cells(piece)[0]
        board[y][x] = "T"
        self.assertFalse(can_place(board, piece))

    def test_try_move_changes_position_only_when_legal(self):
        state = new_game(random.Random(1))
        x = state.active.x
        self.assertTrue(try_move(state, -1, 0))
        self.assertEqual(state.active.x, x - 1)
        while try_move(state, -1, 0):
            pass
        leftmost = state.active.x
        self.assertFalse(try_move(state, -1, 0))
        self.assertEqual(state.active.x, leftmost)

    def test_rotation_uses_wall_kick(self):
        state = GameState(empty_board(), Piece("I", 1, 7, 0), "O", [])
        self.assertTrue(can_place(state.board, state.active))
        self.assertTrue(try_rotate(state))
        self.assertEqual(state.active.rotation, 2)
        self.assertEqual(state.active.x, 6)

    def test_o_rotation_keeps_same_cells(self):
        state = GameState(empty_board(), spawn_piece("O"), "I", [])
        before = set(piece_cells(state.active))
        self.assertTrue(try_rotate(state))
        self.assertEqual(set(piece_cells(state.active)), before)

    def test_level_advances_every_ten_lines(self):
        self.assertEqual(level_for_lines(0), 0)
        self.assertEqual(level_for_lines(9), 0)
        self.assertEqual(level_for_lines(10), 1)
        self.assertEqual(level_for_lines(27), 2)

    def test_drop_interval_decreases_but_has_floor(self):
        self.assertEqual(drop_interval(0), BASE_DROP_INTERVAL)
        self.assertLess(drop_interval(1), drop_interval(0))
        self.assertGreaterEqual(drop_interval(100), MIN_DROP_INTERVAL)
        self.assertEqual(drop_interval(100), MIN_DROP_INTERVAL)

    def test_line_clear_scoring(self):
        self.assertEqual(line_clear_score(0, 0), 0)
        for count, base in LINE_CLEAR_SCORES.items():
            self.assertEqual(line_clear_score(count, 0), base)
            self.assertEqual(line_clear_score(count, 2), base * 3)

    def test_clear_full_line_inserts_empty_row_at_top(self):
        board = empty_board()
        board[-1] = ["I"] * WIDTH
        board[-2][0] = "T"
        result, cleared = clear_full_lines(board)
        self.assertEqual(cleared, 1)
        self.assertEqual(result[0], [""] * WIDTH)
        self.assertEqual(result[-1][0], "T")

    def test_clear_four_lines(self):
        board = empty_board()
        for y in range(HEIGHT - 4, HEIGHT):
            board[y] = ["I"] * WIDTH
        result, cleared = clear_full_lines(board)
        self.assertEqual(cleared, 4)
        self.assertTrue(all(not cell for row in result for cell in row))

    def test_lock_piece_places_cells_and_spawns_next(self):
        rng = random.Random(2)
        state = GameState(empty_board(), Piece("O", 0, 3, 17), "T", ["I"])
        old_cells = piece_cells(state.active)
        cleared = lock_piece(state, rng)
        self.assertEqual(cleared, 0)
        self.assertTrue(all(state.board[y][x] == "O" for x, y in old_cells))
        self.assertEqual(state.active.kind, "T")
        self.assertEqual(state.next_kind, "I")

    def test_lock_piece_scores_line_clear(self):
        board = empty_board()
        board[-1] = ["J"] * WIDTH
        board[-1][4] = ""
        board[-1][5] = ""
        state = GameState(board, Piece("O", 0, 3, 18), "T", ["I"])
        cleared = lock_piece(state, random.Random(1))
        self.assertEqual(cleared, 1)
        self.assertEqual(state.lines, 1)
        self.assertEqual(state.score, 40)

    def test_gravity_moves_without_scoring(self):
        state = new_game(random.Random(1))
        y = state.active.y
        moved, cleared = gravity_step(state, random.Random(2))
        self.assertTrue(moved)
        self.assertEqual(cleared, 0)
        self.assertEqual(state.active.y, y + 1)
        self.assertEqual(state.score, 0)

    def test_soft_drop_awards_one_point(self):
        state = new_game(random.Random(1))
        moved, cleared = soft_drop(state, random.Random(2))
        self.assertTrue(moved)
        self.assertEqual(cleared, 0)
        self.assertEqual(state.score, 1)

    def test_hard_drop_awards_two_points_per_row_and_locks(self):
        state = GameState(empty_board(), Piece("I", 0, 3, 0), "O", ["T"])
        distance, cleared = hard_drop(state, random.Random(1))
        self.assertEqual(distance, 18)
        self.assertEqual(cleared, 0)
        self.assertEqual(state.score, 36)
        self.assertEqual(state.active.kind, "O")
        self.assertTrue(any(cell == "I" for row in state.board for cell in row))

    def test_spawn_collision_sets_game_over(self):
        board = empty_board()
        next_piece = spawn_piece("O")
        for x, y in piece_cells(next_piece):
            board[y][x] = "J"
        state = GameState(board, Piece("I", 0, 3, 17), "O", ["T"])
        lock_piece(state, random.Random(1))
        self.assertTrue(state.game_over)

    def test_save_round_trip_preserves_session(self):
        state = new_game(random.Random(7))
        try_move(state, -1, 0)
        try_rotate(state)
        soft_drop(state, random.Random(8))
        payload = serialize_session(state)
        restored = deserialize_session(payload)
        self.assertEqual(restored, state)
        self.assertIsNot(restored.board, state.board)
        self.assertIsNot(restored.bag, state.bag)

    def test_invalid_save_version_is_rejected(self):
        payload = serialize_session(new_game(random.Random(1)))
        payload["version"] = 999
        with self.assertRaises(ValueError):
            deserialize_session(payload)

    def test_invalid_saved_board_dimensions_are_rejected(self):
        payload = serialize_session(new_game(random.Random(1)))
        payload["board"].pop()
        with self.assertRaises(ValueError):
            deserialize_session(payload)

    def test_invalid_saved_board_cell_is_rejected(self):
        payload = serialize_session(new_game(random.Random(1)))
        payload["board"][0][0] = "X"
        with self.assertRaises(ValueError):
            deserialize_session(payload)

    def test_saved_active_collision_is_rejected(self):
        state = new_game(random.Random(1))
        payload = serialize_session(state)
        x, y = piece_cells(state.active)[0]
        payload["board"][y][x] = "J"
        with self.assertRaises(ValueError):
            deserialize_session(payload)

    def test_invalid_saved_bag_duplicate_is_rejected(self):
        payload = serialize_session(new_game(random.Random(1)))
        payload["bag"] = ["I", "I"]
        with self.assertRaises(ValueError):
            deserialize_session(payload)

    def test_render_contains_board_stats_next_controls_and_status(self):
        state = new_game(random.Random(1))
        rendered = render_board(state, best_score=900, status="Paused")
        self.assertIn("=== Tetris ===", rendered)
        self.assertIn("Score: 0", rendered)
        self.assertIn("Lines: 0", rendered)
        self.assertIn("Level: 0", rendered)
        self.assertIn("Best: 900", rendered)
        self.assertIn("Next:", rendered)
        self.assertIn("Space: hard drop", rendered)
        self.assertIn("P: pause", rendered)
        self.assertIn("S: save", rendered)
        self.assertIn("Q/Esc: quit", rendered)
        self.assertIn("Paused", rendered)
        self.assertIn("<>", rendered)

    def test_control_keys_support_english_arabic_and_escape(self):
        self.assertTrue(is_quit_key("q"))
        self.assertTrue(is_quit_key("ض"))
        self.assertTrue(is_quit_key("escape"))
        self.assertTrue(is_save_key("s"))
        self.assertTrue(is_save_key("س"))
        self.assertTrue(is_pause_key("p"))
        self.assertTrue(is_pause_key("ح"))

    def test_best_score_observation_stays_in_memory(self):
        state = new_game(random.Random(1))
        state.score = 125
        best = Mock()
        best.best_score = 125
        best.observe.return_value = True
        status = _observe_score(best, state, "Cleared 1 line.")
        best.observe.assert_called_once_with(125)
        best.flush.assert_not_called()
        self.assertIn("New Best: 125", status)

    def test_explicit_save_flushes_buffered_best_score(self):
        state = new_game(random.Random(1))
        best = Mock()
        best.best_score = 10
        with patch("games.tetris.save_state") as persist:
            status = _save_live_state(state, best)
        persist.assert_called_once()
        best.flush.assert_called_once_with()
        self.assertEqual(status, "Game saved.")

    def test_negative_counters_and_levels_are_rejected(self):
        with self.assertRaises(ValueError):
            level_for_lines(-1)
        with self.assertRaises(ValueError):
            drop_interval(-1)
        with self.assertRaises(ValueError):
            line_clear_score(1, -1)


if __name__ == "__main__":
    unittest.main()
