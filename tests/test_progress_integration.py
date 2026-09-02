import random
import unittest

from games.connect_four import (
    HUMAN as CONNECT_HUMAN,
    deserialize_state as deserialize_connect_four,
    drop_piece,
    new_board as new_connect_board,
    round_score as connect_score,
    serialize_state as serialize_connect_four,
)
from games.game_2048 import (
    deserialize_state as deserialize_2048,
    serialize_state as serialize_2048,
)
from games.minesweeper import (
    DIFFICULTIES,
    MinesweeperGame,
    deserialize_state as deserialize_minesweeper,
    minesweeper_score,
    serialize_state as serialize_minesweeper,
)
from games.snake import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    GameState,
    deserialize_session,
    serialize_session,
)
from games.tic_tac_toe import (
    DRAW,
    EMPTY,
    deserialize_state as deserialize_tic_tac_toe,
    round_score as tic_tac_toe_score,
    serialize_state as serialize_tic_tac_toe,
)


class GameProgressIntegrationTests(unittest.TestCase):
    def test_tic_tac_toe_round_scoring(self) -> None:
        self.assertEqual(tic_tac_toe_score(DRAW), 25)
        self.assertEqual(tic_tac_toe_score("O"), 0)
        self.assertEqual(tic_tac_toe_score("X"), 100)

    def test_tic_tac_toe_save_round_trip(self) -> None:
        board = ["X", "O", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]
        self.assertEqual(
            deserialize_tic_tac_toe(serialize_tic_tac_toe(board)),
            board,
        )

    def test_connect_four_score_rewards_difficulty_and_efficiency(self) -> None:
        easy = connect_score(CONNECT_HUMAN, "easy", 8)
        hard = connect_score(CONNECT_HUMAN, "hard", 8)
        faster = connect_score(CONNECT_HUMAN, "hard", 6)
        self.assertGreater(hard, easy)
        self.assertGreater(faster, hard)

    def test_connect_four_save_round_trip(self) -> None:
        board = new_connect_board()
        drop_piece(board, 3, "X")
        drop_piece(board, 3, "O")
        restored, difficulty, human_moves = deserialize_connect_four(
            serialize_connect_four(board, "medium", 1)
        )
        self.assertEqual(restored, board)
        self.assertEqual(difficulty, "medium")
        self.assertEqual(human_moves, 1)

    def test_minesweeper_save_round_trip_before_first_reveal(self) -> None:
        difficulty = DIFFICULTIES["1"]
        game = MinesweeperGame(difficulty.rows, difficulty.cols, difficulty.mines)
        restored, restored_difficulty, actions = deserialize_minesweeper(
            serialize_minesweeper(game, difficulty, 0)
        )
        self.assertFalse(restored.mines_placed)
        self.assertEqual(restored_difficulty, difficulty)
        self.assertEqual(actions, 0)

    def test_minesweeper_save_round_trip_after_mines_are_placed(self) -> None:
        difficulty = DIFFICULTIES["1"]
        game = MinesweeperGame(
            difficulty.rows,
            difficulty.cols,
            difficulty.mines,
            rng=random.Random(4),
        )
        game.reveal(0, 0)
        restored, _, _ = deserialize_minesweeper(
            serialize_minesweeper(game, difficulty, 1)
        )
        self.assertTrue(restored.mines_placed)
        self.assertEqual(restored.mines, game.mines)
        self.assertEqual(restored.revealed, game.revealed)

    def test_minesweeper_score_rewards_fewer_actions(self) -> None:
        difficulty = DIFFICULTIES["2"]
        self.assertGreater(
            minesweeper_score(difficulty, 20),
            minesweeper_score(difficulty, 40),
        )

    def test_2048_save_round_trip(self) -> None:
        board = [
            [2, 4, 0, 0],
            [8, 16, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        restored = deserialize_2048(serialize_2048(board, 128, False))
        self.assertEqual(restored, (board, 128, False))

    def test_snake_save_round_trip_for_every_direction(self) -> None:
        for direction in (UP, DOWN, LEFT, RIGHT):
            with self.subTest(direction=direction):
                state = GameState(
                    snake=[(10, 7), (9, 7), (8, 7)],
                    direction=direction,
                    food=(4, 3),
                    score=70,
                )
                restored, speed_name, tick = deserialize_session(
                    serialize_session(state, "Normal")
                )
                self.assertEqual(restored.snake, state.snake)
                self.assertEqual(restored.direction, direction)
                self.assertEqual(restored.food, state.food)
                self.assertEqual(restored.score, 70)
                self.assertEqual(speed_name, "Normal")
                self.assertEqual(tick, 0.12)


if __name__ == "__main__":
    unittest.main()
