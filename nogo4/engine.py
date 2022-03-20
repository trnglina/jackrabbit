import random
from copy import copy
from typing import List, Optional, Union

from board import BLACK, Board, GoStone, opponent


class Engine:
    def __init__(self) -> None:
        self._board: Board = Board(7)
        self._current_player: GoStone = BLACK
        self._time_limit: float = 30.0

    def get_name(self) -> str:
        return "NoGo Assignment 4"

    def get_version(self) -> float:
        return 0.0

    def get_board(self) -> Board:
        return copy(self._board)

    def get_current_player(self) -> GoStone:
        return self._current_player

    def get_board_size(self) -> int:
        return self._board.size

    def set_board_size(self, size: int) -> None:
        self._board = Board(size)
        self._current_player = BLACK

    def get_time_limit(self) -> float:
        return self._time_limit

    def set_time_limit(self, time_limit: float) -> None:
        self._time_limit = time_limit

    def clear_board(self) -> None:
        self._board = Board(self._board.size)
        self._current_player = BLACK

    def play_move(self, point: int, color: GoStone) -> bool:
        legal = self._board.play_for(point, color)
        if legal:
            self._current_player = opponent(color)
        return legal

    def generate_move(self, color: GoStone) -> Optional[int]:
        # TODO: Replace with MCTS
        legal_moves = self._board.get_legal_moves_for(color)
        if not legal_moves:
            return None

        move = random.choice(legal_moves)
        self.play_move(move, color)
        return move


class Node:
    def __init__(self, parent: Union["Node", None] = None) -> None:
        self.parent = parent
        self.wins = 0
        self.visits = 0
        self.children: List[Node] = []
