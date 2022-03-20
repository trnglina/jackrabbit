import math
import random
from copy import copy
from typing import List, Optional

from board import BLACK, Board, GoStone, opponent

SIM_C = 1.41
SIM_N = 1
SIM_T = 3


class Engine:
    def __init__(self) -> None:
        self._board: Board = Board(7)
        self._current_player: GoStone = BLACK

        self._time_epsilon: float = 0.5
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
        if legal := self._board.play_for(point, color):
            self._current_player = opponent(color)
        return legal

    def generate_move(self, color: GoStone) -> Optional[int]:
        # Initialise tree search
        root = Node(copy(self._board), self._current_player, None)

        # TODO: Timeout
        while True:
            # Select & Expand
            node = root.select().expand()

            # Simulate & Backpropogate
            for _ in range(SIM_N):
                node.simulate()

        # TODO: Select best move
        return None


class Node:
    def __init__(
        self, board: Board, player: GoStone, parent: Optional["Node"] = None
    ) -> None:
        self.board = board
        self.player = player

        self.parent = parent
        self.wins = 0
        self.visits = 0
        self.children: List[Node] = []

    def _uct_score(self) -> float:
        assert self.parent
        mean = self.wins / self.visits
        return mean + SIM_C * math.sqrt(math.log(self.parent.visits) / self.visits)

    def select(self) -> "Node":
        node = self
        while node.visits > SIM_T and node.children:
            node = max(node.children, key=lambda child: child._uct_score())
        return node

    def expand(self) -> "Node":
        if move := self.board.get_random_move_for(self.player):
            child_board = copy(self.board)
            child_board.play_for(move, self.player)
            child = Node(child_board, opponent(self.player), self)
            self.children.append(child)
            return child
        return self

    def simulate(self) -> None:
        # TODO: Implement simulation & backpropogation
        pass
