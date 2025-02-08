import gc
import signal
from copy import copy
from typing import Any, Dict, Optional, Tuple

import numpy as np

from board import BLACK, Board, GoStone, opponent

SIM_C = 0.4
INFINITY = float("inf")


def uct_score(parent: "TreeNode", child: "TreeNode", max_flag: bool) -> float:
    if child.visits == 0:
        return INFINITY
    elif max_flag:
        return child.black_wins / child.visits + SIM_C * np.sqrt(
            np.log(parent.visits) / child.visits
        )
    else:
        return (child.visits - child.black_wins) / child.visits + SIM_C * np.sqrt(
            np.log(parent.visits) / child.visits
        )


class TimerExpired(Exception):
    pass


class Engine:
    def __init__(self) -> None:
        self._board: Board = Board(7)
        self._current_player: GoStone = BLACK

        self._time_epsilon: float = 0.1
        self._time_limit: float = 30.0

        self._rng = np.random.default_rng()

        signal.signal(signal.SIGALRM, self._timer_handler)

    def _timer_handler(self, _signum: Any, _fram: Any) -> None:
        raise TimerExpired()

    def _playout(self, node: "TreeNode", board: Board, player: GoStone) -> None:
        # Select
        if not node.expanded:
            node.expand(board, player)
        while not node.is_leaf():
            move, node = node.select(player == BLACK)
            board.play_legal_move_for(move, player)
            player = opponent(player)

        # Expand
        if not node.expanded:
            node.expand(board, player)

        # Simulate
        value = self._simulate(board, player)

        # Backpropogate
        node.update(value)

    def _simulate(self, board: Board, player: GoStone) -> int:
        while move := board.get_random_move_for(self._rng, player):
            board.play_legal_move_for(move, player)
            player = opponent(player)

        return int(player != BLACK)

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
        root = TreeNode(None)
        gc.collect()

        try:
            # Initialise timer
            signal.setitimer(signal.ITIMER_REAL, self._time_limit - self._time_epsilon)
            while True:
                board = copy(self._board)
                self._playout(root, board, color)
                del board

        except TimerExpired:
            signal.setitimer(signal.ITIMER_REAL, 0.0)

        # Select best move
        if not root.children:
            return None
        move, _ = max(root.children.items(), key=lambda items: items[1].visits)

        # Update board with move
        self._board.play_legal_move_for(move, color)
        self._current_player = opponent(color)

        return move


class TreeNode:
    __slots__ = "parent", "children", "visits", "black_wins", "expanded", "move"

    def __init__(self, parent: Optional["TreeNode"] = None) -> None:
        self.parent = parent
        self.children: Dict[int, TreeNode] = {}
        self.visits = 0
        self.black_wins = 0
        self.expanded = False
        self.move: Optional[int] = None

    def select(self, max_flag: bool) -> Tuple[int, "TreeNode"]:
        return max(
            self.children.items(), key=lambda items: uct_score(self, items[1], max_flag)
        )

    def expand(self, board: Board, player: GoStone) -> None:
        moves = board.get_legal_moves_for(player)
        for move in moves:
            if move not in self.children:
                node = TreeNode(self)
                node.move = move
                self.children[move] = node
        self.expanded = True

    def update(self, value: int) -> None:
        if self.parent:
            self.parent.update(value)

        self.black_wins += value
        self.visits += 1

    def is_leaf(self) -> bool:
        return not self.children

    def is_root(self) -> bool:
        return not self.parent
