import math
import signal
from copy import copy
from typing import Any, List, Optional, Tuple

from board import BLACK, Board, GoStone, opponent

SIM_C = 1.41
SIM_T = 3


class TimerExpired(Exception):
    pass


class Engine:
    def __init__(self) -> None:
        self._board: Board = Board(7)
        self._current_player: GoStone = BLACK

        self._time_epsilon: float = 0.1
        self._time_limit: float = 30.0

        signal.signal(signal.SIGALRM, self._timer_handler)

    def _timer_handler(self, _signum: Any, _fram: Any) -> None:
        raise TimerExpired()

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
        root = Node()

        try:
            # Initialise timer
            signal.setitimer(signal.ITIMER_REAL, self._time_limit - self._time_epsilon)
            while True:
                # Initialise board
                board = copy(self._board)
                player = color
                # Select
                node, player = root.select(board, player)
                # Expand
                node, player = node.expand(board, player)
                # Simulate
                value = node.simulate(board, player)
                # Backpropogate
                node.backpropogate(value)
        except TimerExpired:
            signal.setitimer(signal.ITIMER_REAL, 0.0)

        # Select best move
        best = max(root.children, key=lambda child: child.visits)
        if not best:
            return None
        move = best.move
        assert move

        # Update board with move
        if not self.play_move(move, self._current_player):
            raise RuntimeError("BUG: Illegal move generated.")
        return move


class Node:
    def __init__(
        self, parent: Optional["Node"] = None, move: Optional[int] = None
    ) -> None:
        self.parent = parent
        self.move = move
        self.wins = 0
        self.visits = 0
        self.children: List[Node] = []

    def _uct_score(self) -> float:
        assert self.parent
        assert self.visits > 0
        
        mean = self.wins / self.visits
        return mean + SIM_C * math.sqrt(math.log(self.parent.visits) / self.visits)

    def select(self, board: Board, player: GoStone) -> Tuple["Node", GoStone]:
        node = self
        while node.visits > SIM_T and node.children:
            node = max(node.children, key=lambda child: child._uct_score())
            assert node.move
            board.play_legal_move_for(node.move, player)
            player = opponent(player)
        return node, player

    def expand(self, board: Board, player: GoStone) -> Tuple["Node", GoStone]:
        # TODO: Do we want to tweak the expansion criteria, so we're not always expanding?
        node = self
        if move := board.get_random_move_for(player):
            node = Node(self, move)
            self.children.append(node)
            board.play_legal_move_for(move, player)
            player = opponent(player)
        return node, player

    def simulate(self, board: Board, original_player: GoStone) -> int:
        # TODO: Is 1 simulation per simulation phase optimal?
        sim_player = original_player
        while move := board.get_random_move_for(sim_player):
            board.play_legal_move_for(move, sim_player)
            sim_player = opponent(sim_player)

        # TODO: Is this the correct value function?
        return int(sim_player == original_player)

    def backpropogate(self, value: int) -> None:
        # TODO: Does this handle player switching correctly?
        node: Optional["Node"] = self
        while node:
            node.wins += value
            node.visits += 1
            value = 1 - value
            node = node.parent
