"""Terminal Tic-Tac-Toe with an optimal minimax computer opponent."""

from __future__ import annotations

from math import inf

HUMAN = "X"
COMPUTER = "O"
EMPTY = " "
DRAW = "draw"

WINNING_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def winner(board: list[str]) -> str | None:
    """Return X, O, 'draw', or None when the game is still in progress."""
    for a, b, c in WINNING_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    if EMPTY not in board:
        return DRAW
    return None


def available_moves(board: list[str]) -> list[int]:
    """Return zero-based indexes for all empty cells."""
    return [index for index, cell in enumerate(board) if cell == EMPTY]


def render_board(board: list[str]) -> str:
    """Render the board, showing numbers for empty cells."""
    cells = [
        cell if cell != EMPTY else str(index + 1)
        for index, cell in enumerate(board)
    ]
    rows = [f" {cells[i]} | {cells[i + 1]} | {cells[i + 2]} " for i in (0, 3, 6)]
    return "\n---+---+---\n".join(rows)


def _score_terminal(result: str | None) -> int | None:
    if result == COMPUTER:
        return 10
    if result == HUMAN:
        return -10
    if result == DRAW:
        return 0
    return None


def minimax(board: list[str], maximizing: bool, depth: int = 0) -> int:
    """Evaluate a board using minimax. Higher scores favor the computer."""
    result = winner(board)
    terminal_score = _score_terminal(result)
    if terminal_score is not None:
        if terminal_score > 0:
            return terminal_score - depth
        if terminal_score < 0:
            return terminal_score + depth
        return 0

    if maximizing:
        best = -inf
        for move in available_moves(board):
            board[move] = COMPUTER
            best = max(best, minimax(board, False, depth + 1))
            board[move] = EMPTY
        return int(best)

    best = inf
    for move in available_moves(board):
        board[move] = HUMAN
        best = min(best, minimax(board, True, depth + 1))
        board[move] = EMPTY
    return int(best)


def best_computer_move(board: list[str]) -> int:
    """Choose the strongest legal move for the computer."""
    moves = available_moves(board)
    if not moves:
        raise ValueError("No legal moves remain.")

    best_score = -inf
    best_move = moves[0]
    for move in moves:
        board[move] = COMPUTER
        score = minimax(board, False, 0)
        board[move] = EMPTY
        if score > best_score:
            best_score = score
            best_move = move
    return best_move


def _read_human_move(board: list[str]) -> int | None:
    while True:
        raw = input("Choose a square [1-9] or Q to quit: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return None
        if not raw.isdigit():
            print("Enter a number from 1 to 9.")
            continue

        move = int(raw) - 1
        if move not in range(9):
            print("Enter a number from 1 to 9.")
            continue
        if board[move] != EMPTY:
            print("That square is already occupied.")
            continue
        return move


def play_round() -> bool:
    """Play one round. Return False when the player asks to quit."""
    board = [EMPTY] * 9
    print("\nYou are X. The computer is O. You move first.\n")

    while winner(board) is None:
        print(render_board(board))
        print()

        human_move = _read_human_move(board)
        if human_move is None:
            return False
        board[human_move] = HUMAN

        result = winner(board)
        if result is not None:
            break

        computer_move = best_computer_move(board)
        board[computer_move] = COMPUTER
        print(f"\nComputer chooses {computer_move + 1}.\n")

    print(render_board(board))
    result = winner(board)
    if result == HUMAN:
        print("\nYou win.")
    elif result == COMPUTER:
        print("\nComputer wins.")
    else:
        print("\nDraw.")
    return True


def main() -> None:
    """Run the interactive terminal game."""
    print("=== Tic-Tac-Toe ===")
    while True:
        if not play_round():
            print("\nGoodbye.")
            return

        again = input("\nPlay again? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Goodbye.")
            return


if __name__ == "__main__":
    main()
