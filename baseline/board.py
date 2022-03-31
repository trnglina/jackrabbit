from typing import List, Optional

import numpy as np
from numpy.typing import NDArray

EMPTY = np.uint8(0)
BLACK = np.uint8(1)
WHITE = np.uint8(2)
BORDER = np.uint8(3)

MAXSIZE = 25

GoStone = np.uint8


class Board:
    def __init__(self, size: int) -> None:
        self.size = size
        self.ns = size + 1
        self.maxpoint = size * size + 3 * (size + 1)
        # self.history: List[int] = []

        self.board: NDArray[GoStone] = np.full(self.maxpoint, BORDER, dtype=GoStone)
        for row in range(1, self.size + 1):
            start = row * self.ns + 1
            self.board[start : start + self.size] = EMPTY

        self.neighbors: List[List[int]] = [[] for _ in range(self.maxpoint)]
        for pos, arr in enumerate(self.neighbors):
            if self.board[pos] != BORDER:
                for nb in (pos - 1, pos + 1, pos - self.ns, pos + self.ns):
                    if self.board[nb] != BORDER:
                        arr.append(nb)

        self.visited = np.full(self.maxpoint, False, dtype=bool)

    def __repr__(self) -> str:
        repr = np.zeros((self.size, self.size), dtype=GoStone)
        for row in range(self.size):
            start = (row + 1) * self.ns + 1
            repr[row, :] = self.board[start : start + self.size]
        return str(repr)

    def __copy__(self) -> "Board":
        copy = Board(self.size)
        # copy.history = self.history[:]
        copy.board = np.copy(self.board)
        return copy

    def _block_has_liberty(self, stone: int) -> bool:
        color = self.board[stone]
        stack = []

        for nb in self.neighbors[stone]:
            if self.board[nb] == EMPTY:
                return True
            elif self.board[nb] == color:
                stack.append(nb)

        self.visited.fill(False)

        while stack:
            current = stack.pop()
            self.visited[current] = True
            for nb in self.neighbors[current]:
                if self.board[nb] == EMPTY:
                    return True
                elif not self.visited[nb] and self.board[nb] == color:
                    stack.append(nb)

        return False

    def _detect_captures_of(self, point: int, color: GoStone) -> bool:
        for nb in self.neighbors[point]:
            if self.board[nb] == color and not self._block_has_liberty(nb):
                return True
        return False

    def get_empty_points(self) -> NDArray:
        return np.where(self.board == EMPTY)[0]

    def get_legal_moves_for(self, color: GoStone) -> List[int]:
        legal_moves = []
        for move in self.get_empty_points():
            if self.is_move_legal_for(move, color):
                legal_moves.append(move)
        return legal_moves

    def get_random_move_for(self, color: GoStone) -> Optional[int]:
        points = self.get_empty_points()
        np.random.shuffle(points)
        for move in points:
            if self.is_move_legal_for(move, color):
                return move
        return None

    def is_move_legal_for(self, point: int, color: GoStone) -> bool:
        if self.board[point] != EMPTY:
            return False

        self.board[point] = color
        if not self._block_has_liberty(point) or self._detect_captures_of(
            point, opponent(color)
        ):
            self.board[point] = EMPTY
            return False

        self.board[point] = EMPTY
        return True

    def play_legal_move_for(self, point: int, color: GoStone) -> None:
        # self.history.append(point)
        self.board[point] = color

    def play_for(self, point: int, color: GoStone) -> bool:
        if not self.is_move_legal_for(point, color):
            return False
        self.play_legal_move_for(point, color)
        return True

    # def unplay(self) -> None:
    #     point = self.history.pop()
    #     self.board[point] = EMPTY


def opponent(color: GoStone) -> GoStone:
    return WHITE + BLACK - color
