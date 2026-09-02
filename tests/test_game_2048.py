import random
import unittest

from games.game_2048 import (
    add_random_tile,
    can_move,
    empty_cells,
    max_tile,
    merge_line,
    move,
    new_board,
    render_board,
)


class Game2048Tests(unittest.TestCase):
    def test_new_board_is_empty(self):
        board = new_board()
        self.assertEqual(len(board), 4)
        self.assertTrue(all(value == 0 for row in board for value in row))

    def test_merge_line_compresses_and_merges(self):
        result, gained = merge_line([2, 0, 2, 4])
        self.assertEqual(result, [4, 4, 0, 0])
        self.assertEqual(gained, 4)

    def test_merge_line_merges_each_pair_once(self):
        result, gained = merge_line([2, 2, 2, 2])
        self.assertEqual(result, [4, 4, 0, 0])
        self.assertEqual(gained, 8)

    def test_merge_line_does_not_chain_merge_same_move(self):
        result, gained = merge_line([2, 2, 4, 0])
        self.assertEqual(result, [4, 4, 0, 0])
        self.assertEqual(gained, 4)

    def test_move_left(self):
        board = [
            [2, 0, 2, 4],
            [0, 2, 2, 0],
            [4, 4, 8, 8],
            [0, 0, 0, 2],
        ]
        result, gained, changed = move(board, "left")
        self.assertTrue(changed)
        self.assertEqual(gained, 32)
        self.assertEqual(result[0], [4, 4, 0, 0])
        self.assertEqual(result[1], [4, 0, 0, 0])
        self.assertEqual(result[2], [8, 16, 0, 0])
        self.assertEqual(result[3], [2, 0, 0, 0])

    def test_move_right(self):
        board = [[2, 0, 2, 4]] + [[0, 0, 0, 0] for _ in range(3)]
        result, gained, changed = move(board, "d")
        self.assertTrue(changed)
        self.assertEqual(gained, 4)
        self.assertEqual(result[0], [0, 0, 4, 4])

    def test_move_up(self):
        board = [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
            [4, 0, 0, 0],
        ]
        result, gained, changed = move(board, "up")
        self.assertTrue(changed)
        self.assertEqual(gained, 4)
        self.assertEqual([row[0] for row in result], [4, 4, 0, 0])

    def test_move_down(self):
        board = [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
            [4, 0, 0, 0],
        ]
        result, gained, changed = move(board, "s")
        self.assertTrue(changed)
        self.assertEqual(gained, 4)
        self.assertEqual([row[0] for row in result], [0, 0, 4, 4])

    def test_unchanged_move_is_reported(self):
        board = [
            [2, 4, 8, 16],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        result, gained, changed = move(board, "left")
        self.assertFalse(changed)
        self.assertEqual(gained, 0)
        self.assertEqual(result, board)

    def test_can_move_with_empty_cell(self):
        board = [[2, 4, 8, 16] for _ in range(4)]
        board[3][3] = 0
        self.assertTrue(can_move(board))

    def test_can_move_with_adjacent_equal_tiles(self):
        board = [
            [2, 4, 8, 16],
            [32, 64, 128, 256],
            [512, 1024, 2, 4],
            [8, 16, 32, 32],
        ]
        self.assertTrue(can_move(board))

    def test_game_over_when_full_and_no_equal_neighbors(self):
        board = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        self.assertFalse(can_move(board))

    def test_random_tile_uses_one_empty_cell(self):
        board = new_board()
        rng = random.Random(42)
        self.assertTrue(add_random_tile(board, rng))
        non_zero = [value for row in board for value in row if value]
        self.assertEqual(len(non_zero), 1)
        self.assertIn(non_zero[0], {2, 4})
        self.assertEqual(len(empty_cells(board)), 15)

    def test_random_tile_returns_false_on_full_board(self):
        board = [[2, 4, 2, 4] for _ in range(4)]
        self.assertFalse(add_random_tile(board, random.Random(1)))

    def test_max_tile_and_rendering(self):
        board = new_board()
        board[1][2] = 2048
        self.assertEqual(max_tile(board), 2048)
        rendered = render_board(board, 1234)
        self.assertIn("2048", rendered)
        self.assertIn("1234", rendered)


if __name__ == "__main__":
    unittest.main()
