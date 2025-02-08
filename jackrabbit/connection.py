import re
from sys import stderr, stdin, stdout
from typing import List, Optional

from board import BLACK, BORDER, EMPTY, MAXSIZE, WHITE, GoStone, opponent
from engine import Engine


class Connection:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

        self.commands = {
            "protocol_version": self._protocol_version_cmd,
            "quit": self._quit_cmd,
            "name": self._name_cmd,
            "boardsize": self._boardsize_cmd,
            "timelimit": self._timelimit_cmd,
            "showboard": self._showboard_cmd,
            "clear_board": self._clear_board_cmd,
            "komi": self._komi_cmd,
            "version": self._version_cmd,
            "known_command": self._known_command_cmd,
            "list_commands": self._list_commands_cmd,
            "legal_moves": self._legal_moves_cmd,
            "genmove": self._genmove_cmd,
            "play": self._play_cmd,
            "gogui-rules_game_id": self._gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self._gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self._gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self._gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self._gogui_rules_board_cmd,
            "gogui-rules_final_result": self._gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self._gogui_analyze_cmd,
        }

    def respond(self, response: str = "") -> None:
        stdout.write("= {}\n\n".format(response))
        stdout.flush()

    def error(self, message: str) -> None:
        stdout.write("? {}\n\n".format(message))
        stdout.flush()

    def start(self) -> None:
        while line := stdin.readline():
            line = line.strip(" \r\t")

            if len(line) == 0 or line[0] == "#":
                return
            if line[0].isdigit():
                line = re.sub("^\d+", "", line).lstrip()

            elements = line.split()
            if not elements:
                return

            if elements[0] in self.commands:
                self.commands[elements[0]](elements[1:])
            else:
                self.error("Unknown command")

    def _protocol_version_cmd(self, _: List[str]) -> None:
        self.respond("2")

    def _quit_cmd(self, _: List[str]) -> None:
        self.respond()
        exit()

    def _name_cmd(self, _: List[str]) -> None:
        self.respond(self._engine.get_name())

    def _boardsize_cmd(self, args: List[str]) -> None:
        self._engine.set_board_size(int(args[0]))
        self.respond()

    def _timelimit_cmd(self, args: List[str]) -> None:
        self._engine.set_time_limit(float(args[0]))
        self.respond()

    def _showboard_cmd(self, _: List[str]) -> None:
        self.respond("\n" + repr(self._engine.get_board()))

    def _clear_board_cmd(self, _: List[str]) -> None:
        self._engine.clear_board()
        self.respond()

    def _komi_cmd(self, _: List[str]) -> None:
        self.respond()

    def _version_cmd(self, _: List[str]) -> None:
        self.respond(str(self._engine.get_version()))

    def _known_command_cmd(self, args: List[str]) -> None:
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def _list_commands_cmd(self, _: List[str]) -> None:
        self.respond(" ".join(list(self.commands.keys())))

    def _legal_moves_cmd(self, args: List[str]) -> None:
        color = parse_color(args[0].lower())
        board = self._engine.get_board()
        moves = board.get_legal_moves_for(color)
        self.respond(format_moves(moves, board.size))

    def _genmove_cmd(self, args: List[str]) -> None:
        color = parse_color(args[0].lower())
        if (move := self._engine.generate_move(color)) is None:
            self.respond("resign")
            return
        self.respond(format_point(move, self._engine.get_board_size()))

    def _play_cmd(self, args: List[str]) -> None:
        color = parse_color(args[0].lower())
        if not (move := parse_move(args[1], self._engine.get_board_size())):
            self.respond(f'illegal move: "{args[0]} {args[1]}"')
            return
        if not self._engine.play_move(move, color):
            self.respond(f'illegal move: "{args[0]} {args[1]}"')
            return
        self.respond()

    def _gogui_rules_game_id_cmd(self, _: List[str]) -> None:
        self.respond("NoGo")

    def _gogui_rules_board_size_cmd(self, _: List[str]) -> None:
        self.respond(str(self._engine.get_board_size()))

    def _gogui_rules_legal_moves_cmd(self, _: List[str]) -> None:
        color = self._engine.get_current_player()
        board = self._engine.get_board()
        moves = board.get_legal_moves_for(color)
        self.respond(format_moves(moves, board.size))

    def _gogui_rules_side_to_move_cmd(self, _: List[str]) -> None:
        color = self._engine.get_current_player()
        if color_str := format_color(opponent(color)):
            self.respond(color_str)
            return
        self.respond()

    def _gogui_rules_board_cmd(self, _: List[str]) -> None:
        board = self._engine.get_board()
        str = ""
        for row in range(board.size - 1, -1, -1):
            start = (row + 1) * board.ns + 1
            for i in range(board.size):
                point = board.board[start + i]
                if point == BLACK:
                    str += "X"
                elif point == WHITE:
                    str += "O"
                elif point == EMPTY:
                    str += "."
                else:
                    assert False
            str += "\n"
        self.respond(str)

    def _gogui_rules_final_result_cmd(self, _: List[str]) -> None:
        color = self._engine.get_current_player()
        board = self._engine.get_board()
        if not board.get_legal_moves_for(color) and (
            color_str := format_color(opponent(color))
        ):
            self.respond(color_str)
            return
        self.respond("unknown")

    def _gogui_analyze_cmd(self, _: List[str]) -> None:
        self.respond(
            "pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
            "pstring/Side to Play/gogui-rules_side_to_move\n"
            "pstring/Final Result/gogui-rules_final_result\n"
            "pstring/Board Size/gogui-rules_board_size\n"
            "pstring/Rules GameID/gogui-rules_game_id\n"
            "pstring/Show Board/gogui-rules_board\n"
        )


def parse_color(str: str) -> GoStone:
    return {"b": BLACK, "w": WHITE, "e": EMPTY, "BORDER": BORDER}[str]


def parse_move(str: str, board_size: int) -> Optional[int]:
    if not 2 <= board_size <= MAXSIZE:
        return None
    s = str.lower()
    if s == "pass":
        return None
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        return None
    if not (col <= board_size and row <= board_size):
        return None
    return (board_size + 1) * row + col


def format_color(color: GoStone) -> Optional[str]:
    return [None, "black", "white", None][color]


def format_point(point: int, board_size: int) -> str:
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    row, col = divmod(point, board_size + 1)
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)


def format_moves(moves: List[int], board_size: int) -> str:
    gtp_moves = [format_point(move, board_size) for move in moves]
    return " ".join(sorted(gtp_moves))
