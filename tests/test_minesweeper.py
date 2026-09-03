"""Tests for the terminal Minesweeper game."""

from __future__ import annotations

import random
import unittest

from games.minesweeper import FLAG, HIDDEN, MINE, MinesweeperGame, parse_command


class MinesweeperGameTests(unittest.TestCase):
    def test_first_reveal_is_safe_and_protects_neighbors(self) -> None:
        game = MinesweeperGame(9, 9, 10, rng=random.Random(7))

        game.reveal(4, 4)

        self.assertNotIn((4, 4), game.mines)
        self.assertTrue(set(game.neighbors(4, 4)).isdisjoint(game.mines))
        self.assertEqual(10, len(game.mines))

    def test_first_reveal_still_safe_on_tiny_board(self) -> None:
        game = MinesweeperGame(2, 2, 3, rng=random.Random(3))

        game.reveal(0, 0)

        self.assertNotIn((0, 0), game.mines)
        self.assertFalse(game.lost)

    def test_adjacent_mine_count(self) -> None:
        game = MinesweeperGame(3, 3, 2, mines={(0, 0), (0, 2)})

        self.assertEqual(2, game.adjacent_mines(1, 1))
        self.assertEqual(1, game.adjacent_mines(1, 0))

    def test_toggle_flag_places_and_removes_flag(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})

        self.assertTrue(game.toggle_flag(1, 1))
        self.assertIn((1, 1), game.flags)
        self.assertFalse(game.toggle_flag(1, 1))
        self.assertNotIn((1, 1), game.flags)

    def test_revealed_cell_cannot_be_flagged(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})
        game.reveal(1, 1)

        self.assertFalse(game.toggle_flag(1, 1))
        self.assertNotIn((1, 1), game.flags)

    def test_flagged_cell_is_not_revealed(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})
        game.toggle_flag(1, 1)

        game.reveal(1, 1)

        self.assertNotIn((1, 1), game.revealed)
        self.assertFalse(game.lost)

    def test_revealing_mine_loses_game(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})

        game.reveal(0, 0)

        self.assertTrue(game.lost)
        self.assertIn((0, 0), game.revealed)
        self.assertFalse(game.is_won())

    def test_empty_region_flood_fill_reveals_safe_cells(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})

        game.reveal(2, 2)

        self.assertEqual(8, len(game.revealed))
        self.assertNotIn((0, 0), game.revealed)
        self.assertTrue(game.is_won())

    def test_wrong_flag_blocks_win_until_removed(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})
        game.toggle_flag(2, 2)
        game.reveal(2, 1)

        self.assertFalse(game.is_won())
        game.toggle_flag(2, 2)
        game.reveal(2, 2)
        self.assertTrue(game.is_won())

    def test_chord_reveals_unflagged_neighbors_when_flag_count_matches(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})
        game.reveal(1, 1)
        game.toggle_flag(0, 0)

        changed = game.chord(1, 1)

        self.assertTrue(changed)
        self.assertFalse(game.lost)
        self.assertTrue(game.is_won())
        self.assertNotIn((0, 0), game.revealed)

    def test_chord_does_nothing_until_adjacent_flag_count_matches(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})
        game.reveal(1, 1)
        before = set(game.revealed)

        changed = game.chord(1, 1)

        self.assertFalse(changed)
        self.assertEqual(before, game.revealed)
        self.assertFalse(game.lost)

    def test_chord_with_wrong_matching_flag_can_detonate_mine(self) -> None:
        game = MinesweeperGame(3, 3, 1, mines={(0, 0)})
        game.reveal(1, 1)
        game.toggle_flag(0, 1)

        changed = game.chord(1, 1)

        self.assertTrue(changed)
        self.assertTrue(game.lost)
        self.assertIn((0, 0), game.revealed)

    def test_hidden_flag_and_mine_symbols(self) -> None:
        game = MinesweeperGame(2, 2, 1, mines={(0, 0)})
        game.toggle_flag(1, 1)

        self.assertEqual(HIDDEN, game.symbol_at(0, 1))
        self.assertEqual(FLAG, game.symbol_at(1, 1))
        self.assertEqual(MINE, game.symbol_at(0, 0, reveal_all=True))

    def test_parse_bare_coordinates_as_reveal(self) -> None:
        self.assertEqual(("reveal", 2, 3), parse_command("3 4"))

    def test_parse_explicit_reveal_flag_and_chord(self) -> None:
        self.assertEqual(("reveal", 1, 0), parse_command("r 2 1"))
        self.assertEqual(("flag", 4, 5), parse_command("flag 5 6"))
        self.assertEqual(("chord", 2, 3), parse_command("c 3 4"))
        self.assertEqual(("chord", 1, 2), parse_command("chord 2 3"))

    def test_parse_quit(self) -> None:
        self.assertEqual(("quit", None, None), parse_command("Q"))

    def test_invalid_command_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_command("explode 2 3")


if __name__ == "__main__":
    unittest.main()
