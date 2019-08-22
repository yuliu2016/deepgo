import copy
from gotypes import Player, Point
from typing import Optional


class Move:
    def __init__(self, point: "Point" = None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = point is not None
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point: "Point"):
        return Move(point=point)

    @classmethod
    def do_pass(cls):
        return Move(is_pass=True)

    @classmethod
    def do_resign(cls):
        return Move(is_resign=True)


class Group:
    def __init__(self, color, stones: "set[Point]", liberties: "set[Point]"):
        self.color = color
        self.stones = set(stones)
        self.liberties = set(liberties)

    def remove_liberty(self, liberty_point: "Point"):
        self.liberties.remove(liberty_point)

    def add_liberty(self, liberty_point: "Point"):
        self.liberties.add(liberty_point)

    @property
    def num_liberties(self):
        return len(self.liberties)

    def merge(self, other_group: "Group"):
        assert self.color == other_group.color
        # Merge the stones of both groups
        new_stones = self.stones | other_group.stones
        # Merge the liberties of both groups and subtract the stone positions from the set
        new_liberties = (self.liberties | other.liberties) - new_stones
        return Group(self.color, new_stones, new_liberties)

    def __eq__(self, other):
        return isinstance(other, Group) and self.color == other.color and \
               self.stones == other.stones and self.liberties == other.liberties


class Board:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self._grid: "dict[Point, Optional[Group]]" = {}  # List of pairs of [Point, Group] for efficient lookup

    def place_stone(self, player: "Player", point: "Point"):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        liberties = set()
        adjacent_same_colour = []
        adjacent_opposite_colour = []
        for neighbour in point.neighbours():
            neighbour_group = self._grid.get(neighbour)
            if neighbour_group is None:
                liberties.append(neighbour)
            elif neighbour_group.color == player:
                if neighbour_group not in adjacent_same_colour:
                    adjacent_same_colour.append(neighbour_group)
            else:
                if neighbour_group not in adjacent_opposite_colour:
                    adjacent_opposite_colour.append(neighbour_group)
        new_group = Group(player, {point}, liberties)
        for group in adjacent_same_colour:
            new_group = new_group.merge(group)
        for point in new_group.stones:
            self._grid[point] = new_group
        for other_group in adjacent_opposite_colour:
            other_group.remove_liberty(point)
        for other_group in adjacent_opposite_colour:
            if other_group.num_liberties == 0:
                self.remove_group(other_group)

    def remove_group(self, group: "Group"):
        for point in group.stones:
            for neighbour in point.neighbours():
                neighbour_group = self._grid.get(neighbour)
                if neighbour_group is None:
                    continue
                if neighbour_group is not group:
                    neighbour_group.add_liberty(point)
            self._grid[point] = None

    def is_on_grid(self, point: "Point"):
        return 1 <= point.row <= self.rows and 1 <= point.col <= self.cols

    def get(self, point: "Point"):
        group = self._grid.get(point)
        if group is None:
            return None
        return group.color

    def get_group(self, point):
        group = self._grid.get(point)
        if group is None:
            return None
        return group


class GameState:
    def __init__(self, board: "Board", next_player: "Player",
                 previous_state: "Optional[GameState]", last_move: "Optional[Move]"):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous_state
        self.last_move = last_move

    def apply_move(self, move: "Move"):
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    def is_self_capture(self, player: "Player", move: "Move"):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_group = next_board.get_group(move.point)
        return new_group.num_liberties == 0

    def is_violate_super_ko(self, player: "Player", move: "Move"):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = player.other, next_board
        past_state = self.previous_state
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state
        return False

    def is_valid_move(self, move: "Move"):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return self.board.get(move.point) is None and \
               not self.is_self_capture(self.next_player, move) and \
               not self.is_violate_super_ko(self.next_player, move)

    @property
    def situation(self):
        return self.next_player, self.board

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)
