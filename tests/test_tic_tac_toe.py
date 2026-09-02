import unittest

from games.tic_tac_toe import (
    COMPUTER,
    DRAW,
    EMPTY,
    HUMAN,
    available_moves,
    best_computer_move,
    minimax,
    winner,
)


class TicTacToeTests(unittest.TestCase):
    def test_detects_row_win(self) -> None:
        board = [HUMAN, HUMAN, HUMAN, EMPTY, COMPUTER, EMPTY, COMPUTER, EMPTY, EMPTY]
        self.assertEqual(winner(board), HUMAN)

    def test_detects_diagonal_win(self) -> None:
        board = [COMPUTER, HUMAN, EMPTY, HUMAN, COMPUTER, EMPTY, EMPTY, EMPTY, COMPUTER]
        self.assertEqual(winner(board), COMPUTER)

    def test_detects_draw(self) -> None:
        board = [HUMAN, COMPUTER, HUMAN, HUMAN, COMPUTER, COMPUTER, COMPUTER, HUMAN, HUMAN]
        self.assertEqual(winner(board), DRAW)

    def test_available_moves(self) -> None:
        board = [HUMAN, EMPTY, COMPUTER, EMPTY, EMPTY, HUMAN, COMPUTER, EMPTY, EMPTY]
        self.assertEqual(available_moves(board), [1, 3, 4, 7, 8])

    def test_computer_takes_winning_move(self) -> None:
        board = [COMPUTER, COMPUTER, EMPTY, HUMAN, HUMAN, EMPTY, EMPTY, EMPTY, EMPTY]
        self.assertEqual(best_computer_move(board), 2)

    def test_computer_blocks_immediate_loss(self) -> None:
        board = [HUMAN, HUMAN, EMPTY, COMPUTER, EMPTY, EMPTY, EMPTY, COMPUTER, EMPTY]
        self.assertEqual(best_computer_move(board), 2)

    def test_minimax_scores_draw_as_zero(self) -> None:
        board = [HUMAN, COMPUTER, HUMAN, HUMAN, COMPUTER, COMPUTER, COMPUTER, HUMAN, HUMAN]
        self.assertEqual(minimax(board, True), 0)


if __name__ == "__main__":
    unittest.main()
