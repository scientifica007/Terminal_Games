"""Terminal Connect Four with three computer difficulty levels."""

from __future__ import annotations

import random
from math import inf
from typing import Any

from games.progress import (
    ProgressDataError,
    clear_save,
    get_best_score,
    load_state,
    save_state,
    update_best_score,
)
from games.session_menu import LOAD, NEW, QUIT, choose_session_action

GAME_ID = "connect_four"
SAVE_VERSION = 1
ROWS = 6
COLUMNS = 7
HUMAN = "X"
COMPUTER = "O"
EMPTY = "."
DRAW = "draw"

Board = list[list[str]]


def new_board() -> Board:
    """Return an empty Connect Four board."""
    return [[EMPTY for _ in range(COLUMNS)] for _ in range(ROWS)]


def valid_moves(board: Board) -> list[int]:
    """Return zero-based columns that can still accept a piece."""
    return [column for column in range(COLUMNS) if board[0][column] == EMPTY]


def ordered_moves(board: Board) -> list[int]:
    """Return legal moves ordered from the center outward."""
    center = COLUMNS // 2
    return sorted(valid_moves(board), key=lambda column: (abs(column - center), column))


def drop_piece(board: Board, column: int, piece: str) -> int:
    """Drop a piece into a column and return the row where it lands."""
    if column not in range(COLUMNS):
        raise ValueError("Column must be between 1 and 7.")
    for row in range(ROWS - 1, -1, -1):
        if board[row][column] == EMPTY:
            board[row][column] = piece
            return row
    raise ValueError("Column is full.")


def undo_piece(board: Board, column: int) -> None:
    """Remove the topmost piece from a column."""
    for row in range(ROWS):
        if board[row][column] != EMPTY:
            board[row][column] = EMPTY
            return
    raise ValueError("Column is empty.")


def _has_four(board: Board, piece: str) -> bool:
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for row in range(ROWS):
        for column in range(COLUMNS):
            if board[row][column] != piece:
                continue
            for row_step, column_step in directions:
                end_row = row + 3 * row_step
                end_column = column + 3 * column_step
                if not (0 <= end_row < ROWS and 0 <= end_column < COLUMNS):
                    continue
                if all(
                    board[row + offset * row_step][column + offset * column_step] == piece
                    for offset in range(1, 4)
                ):
                    return True
    return False


def winner(board: Board) -> str | None:
    """Return X, O, 'draw', or None while play can continue."""
    if _has_four(board, HUMAN):
        return HUMAN
    if _has_four(board, COMPUTER):
        return COMPUTER
    if not valid_moves(board):
        return DRAW
    return None


def render_board(board: Board) -> str:
    """Render the board with numbered columns."""
    header = "  " + "   ".join(str(column) for column in range(1, COLUMNS + 1))
    rows = ["| " + " | ".join(row) + " |" for row in board]
    footer = "+" + "---+" * COLUMNS
    return "\n".join([header, footer, *rows, footer])


def round_score(result: str | None, difficulty: str, human_moves: int) -> int:
    """Score a completed round with difficulty and efficiency weighting."""
    base = {"easy": 100, "medium": 250, "hard": 500}.get(difficulty)
    if base is None:
        raise ValueError(f"Unknown difficulty: {difficulty}")
    if human_moves < 0:
        raise ValueError("human_moves cannot be negative.")
    if result == HUMAN:
        return base + max(0, 22 - human_moves) * 10
    if result == DRAW:
        return base // 5
    return 0


def serialize_state(board: Board, difficulty: str, human_moves: int) -> dict[str, Any]:
    return {
        "version": SAVE_VERSION,
        "board": [row[:] for row in board],
        "difficulty": difficulty,
        "human_moves": human_moves,
    }


def deserialize_state(state: dict[str, Any]) -> tuple[Board, str, int]:
    if state.get("version") != SAVE_VERSION:
        raise ValueError("Unsupported Connect Four save version.")
    board = state.get("board")
    difficulty = state.get("difficulty")
    human_moves = state.get("human_moves")
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("Invalid saved difficulty.")
    if isinstance(human_moves, bool) or not isinstance(human_moves, int) or human_moves < 0:
        raise ValueError("Invalid saved move count.")
    if not isinstance(board, list) or len(board) != ROWS:
        raise ValueError("Invalid saved board.")
    restored: Board = []
    for row in board:
        if not isinstance(row, list) or len(row) != COLUMNS:
            raise ValueError("Invalid saved board row.")
        if any(cell not in {HUMAN, COMPUTER, EMPTY} for cell in row):
            raise ValueError("Invalid saved board symbols.")
        restored.append(list(row))
    if winner(restored) is not None:
        raise ValueError("Saved Connect Four game is already finished.")
    return restored, difficulty, human_moves


def _score_window(window: list[str]) -> int:
    score = 0
    computer = window.count(COMPUTER)
    human = window.count(HUMAN)
    empty = window.count(EMPTY)

    if computer == 4:
        score += 100_000
    elif computer == 3 and empty == 1:
        score += 80
    elif computer == 2 and empty == 2:
        score += 12

    if human == 4:
        score -= 100_000
    elif human == 3 and empty == 1:
        score -= 100
    elif human == 2 and empty == 2:
        score -= 14

    return score


def evaluate_position(board: Board) -> int:
    """Heuristically score a non-terminal board for the computer."""
    score = 8 * sum(row[COLUMNS // 2] == COMPUTER for row in board)
    score -= 8 * sum(row[COLUMNS // 2] == HUMAN for row in board)

    for row in range(ROWS):
        for column in range(COLUMNS - 3):
            score += _score_window(board[row][column : column + 4])

    for column in range(COLUMNS):
        for row in range(ROWS - 3):
            window = [board[row + offset][column] for offset in range(4)]
            score += _score_window(window)

    for row in range(ROWS - 3):
        for column in range(COLUMNS - 3):
            window = [board[row + offset][column + offset] for offset in range(4)]
            score += _score_window(window)

    for row in range(3, ROWS):
        for column in range(COLUMNS - 3):
            window = [board[row - offset][column + offset] for offset in range(4)]
            score += _score_window(window)

    return score


def minimax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
) -> int:
    """Evaluate a position using depth-limited minimax with alpha-beta pruning."""
    result = winner(board)
    if result == COMPUTER:
        return 1_000_000 + depth
    if result == HUMAN:
        return -1_000_000 - depth
    if result == DRAW:
        return 0
    if depth == 0:
        return evaluate_position(board)

    moves = ordered_moves(board)
    if maximizing:
        value = -inf
        for column in moves:
            drop_piece(board, column, COMPUTER)
            value = max(value, minimax(board, depth - 1, alpha, beta, False))
            undo_piece(board, column)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return int(value)

    value = inf
    for column in moves:
        drop_piece(board, column, HUMAN)
        value = min(value, minimax(board, depth - 1, alpha, beta, True))
        undo_piece(board, column)
        beta = min(beta, value)
        if alpha >= beta:
            break
    return int(value)


def best_computer_move(board: Board, depth: int = 5) -> int:
    """Choose the strongest move found at the requested search depth."""
    moves = ordered_moves(board)
    if not moves:
        raise ValueError("No legal moves remain.")

    best_score = -inf
    best_move = moves[0]
    for column in moves:
        drop_piece(board, column, COMPUTER)
        score = minimax(board, depth - 1, -inf, inf, False)
        undo_piece(board, column)
        if score > best_score:
            best_score = score
            best_move = column
    return best_move


def choose_computer_move(board: Board, difficulty: str) -> int:
    """Choose a computer move for easy, medium, or hard difficulty."""
    if difficulty == "easy":
        moves = valid_moves(board)
        if not moves:
            raise ValueError("No legal moves remain.")
        return random.choice(moves)
    if difficulty == "medium":
        return best_computer_move(board, depth=3)
    if difficulty == "hard":
        return best_computer_move(board, depth=5)
    raise ValueError(f"Unknown difficulty: {difficulty}")


def _read_difficulty() -> str | None:
    options = {
        "1": "easy",
        "2": "medium",
        "3": "hard",
        "easy": "easy",
        "medium": "medium",
        "hard": "hard",
    }
    print("\nDifficulty:")
    print("1. Easy")
    print("2. Medium")
    print("3. Hard")
    while True:
        raw = input("Choose difficulty [1-3] or Q to quit: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return None
        difficulty = options.get(raw)
        if difficulty is not None:
            return difficulty
        print("Enter 1, 2, or 3.")


def _read_human_move(board: Board) -> int | str | None:
    while True:
        raw = input("Choose column [1-7], SAVE, or Q: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return None
        if raw in {"save", "sv"}:
            return "save"
        if not raw.isdigit():
            print("Enter a number from 1 to 7, SAVE, or Q.")
            continue

        column = int(raw) - 1
        if column not in range(COLUMNS):
            print("Enter a number from 1 to 7.")
            continue
        if column not in valid_moves(board):
            print("That column is full.")
            continue
        return column


def play_round(
    difficulty: str,
    board: Board | None = None,
    human_moves: int = 0,
) -> bool:
    """Play one round. Return False when the player asks to quit."""
    board = new_board() if board is None else [row[:] for row in board]
    print(f"\nYou are {HUMAN}. The computer is {COMPUTER}. You move first.")
    print(f"Difficulty: {difficulty.title()}")
    print("Type SAVE on your turn to store this exact position.\n")

    while winner(board) is None:
        print(render_board(board))
        print()

        human_move = _read_human_move(board)
        if human_move is None:
            return False
        if human_move == "save":
            try:
                save_state(GAME_ID, serialize_state(board, difficulty, human_moves))
                print("\nGame saved.\n")
            except ProgressDataError as exc:
                print(f"\nCould not save game: {exc}\n")
            continue

        assert isinstance(human_move, int)
        drop_piece(board, human_move, HUMAN)
        human_moves += 1

        result = winner(board)
        if result is not None:
            break

        computer_move = choose_computer_move(board, difficulty)
        drop_piece(board, computer_move, COMPUTER)
        print(f"\nComputer chooses column {computer_move + 1}.\n")

    print(render_board(board))
    result = winner(board)
    score = round_score(result, difficulty, human_moves)
    new_record = update_best_score(GAME_ID, score)
    clear_save(GAME_ID)

    if result == HUMAN:
        print("\nYou win.")
    elif result == COMPUTER:
        print("\nComputer wins.")
    else:
        print("\nDraw.")
    print(f"Score: {score} | Best Score: {get_best_score(GAME_ID)}")
    if new_record:
        print("New Best Score!")
    return True


def _load_saved_game() -> tuple[Board, str, int] | None:
    state = load_state(GAME_ID)
    if state is None:
        return None
    try:
        return deserialize_state(state)
    except ValueError as exc:
        print(f"\nSaved game is invalid: {exc}")
        return None


def main() -> None:
    """Run the interactive terminal game."""
    print("=== Connect Four ===")
    while True:
        action = choose_session_action(GAME_ID, "Connect Four")
        if action == QUIT:
            print("Goodbye.")
            return

        if action == LOAD:
            loaded = _load_saved_game()
            if loaded is None:
                continue
            board, difficulty, human_moves = loaded
            print("\nSaved game loaded.")
        elif action == NEW:
            difficulty = _read_difficulty()
            if difficulty is None:
                print("\nGoodbye.")
                return
            board = None
            human_moves = 0
        else:
            continue

        if not play_round(difficulty, board, human_moves):
            print("\nGoodbye.")
            return

        again = input("\nPlay another round? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return


if __name__ == "__main__":
    main()
