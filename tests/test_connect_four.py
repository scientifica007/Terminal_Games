import unittest

from games.connect_four import (
    COMPUTER,
    HUMAN,
    best_computer_move,
    drop_piece,
    new_board,
    render_board,
    undo_piece,
    valid_moves,
    winner,
)


class ConnectFourTests(unittest.TestCase):
    def test_new_board_has_seven_valid_columns(self):
        self.assertEqual(valid_moves(new_board()), list(range(7)))

    def test_drop_piece_stacks_from_bottom(self):
        board = new_board()
        self.assertEqual(drop_piece(board, 2, HUMAN), 5)
        self.assertEqual(drop_piece(board, 2, COMPUTER), 4)
        self.assertEqual(board[5][2], HUMAN)
        self.assertEqual(board[4][2], COMPUTER)

    def test_undo_piece_removes_topmost_piece(self):
        board = new_board()
        drop_piece(board, 2, HUMAN)
        drop_piece(board, 2, COMPUTER)
        undo_piece(board, 2)
        self.assertEqual(board[4][2], ".")
        self.assertEqual(board[5][2], HUMAN)

    def test_full_column_is_not_valid(self):
        board = new_board()
        for _ in range(6):
            drop_piece(board, 0, HUMAN)
        self.assertNotIn(0, valid_moves(board))
        with self.assertRaises(ValueError):
            drop_piece(board, 0, COMPUTER)

    def test_horizontal_win(self):
        board = new_board()
        for column in range(4):
            drop_piece(board, column, HUMAN)
        self.assertEqual(winner(board), HUMAN)

    def test_vertical_win(self):
        board = new_board()
        for _ in range(4):
            drop_piece(board, 3, COMPUTER)
        self.assertEqual(winner(board), COMPUTER)

    def test_diagonal_down_right_win(self):
        board = new_board()
        for row, column in ((2, 0), (3, 1), (4, 2), (5, 3)):
            board[row][column] = HUMAN
        self.assertEqual(winner(board), HUMAN)

    def test_diagonal_up_right_win(self):
        board = new_board()
        for row, column in ((5, 0), (4, 1), (3, 2), (2, 3)):
            board[row][column] = COMPUTER
        self.assertEqual(winner(board), COMPUTER)

    def test_computer_takes_immediate_win(self):
        board = new_board()
        for column in (0, 1, 2):
            drop_piece(board, column, COMPUTER)
        self.assertEqual(best_computer_move(board, depth=3), 3)

    def test_computer_blocks_immediate_loss(self):
        board = new_board()
        for column in (0, 1, 2):
            drop_piece(board, column, HUMAN)
        self.assertEqual(best_computer_move(board, depth=3), 3)

    def test_render_board_shows_column_numbers(self):
        rendered = render_board(new_board())
        self.assertIn("1   2   3   4   5   6   7", rendered)


if __name__ == "__main__":
    unittest.main()
