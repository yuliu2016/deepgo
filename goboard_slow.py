import copy
from gotypes import Player, Point


class Move:
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = point is not None
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point):
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

    def remove_liberty(self, liberty_point):
        self.liberties.remove(liberty_point)

    def add_liberty(self, liberty_point):
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
        self._grid: "dict[Point, Group]" = {}  # List of pairs of [Point, Group] for efficient lookup

    def place_stone(self, player, point):
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

    def is_on_grid(self, point):
        return 1 <= point.row <= self.rows and 1 <= point.col <= self.cols

    def get(self, point):
        group = self._grid.get(point)
        if group is None:
            return None
        return group.color

    def get_group(self, point):
        group = self._grid.get(point)
        if group is None:
            return None
        return group
