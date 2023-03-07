from itertools import combinations
from enum import Enum


class Shape(Enum):
    oval = 1
    squiggle = 2
    diamond = 3


class Color(Enum):
    red = 1
    green = 2
    purple = 3


class Number(Enum):
    one = 1
    two = 2
    three = 3


class Fill(Enum):
    empty = 1
    striped = 2
    solid = 3


class Card:
    def __init__(self, shape, color, number, fill):
        self.shape = Shape(shape)
        self.color = Color(color)
        self.number = Number(number)
        self.fill = Fill(fill)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"{self.shape.name} {self.color.name} {self.number.name} {self.fill.name}"
        )

    def __eq__(self, other):
        return (
            self.shape == other.shape
            and self.color == other.color
            and self.number == other.number
            and self.fill == other.fill
        )

    def __hash__(self):
        return hash((self.shape, self.color, self.number, self.fill))


def find_sets(cards):
    sets = set()
    for c1, c2, c3 in combinations(cards, 3):

        if c1.shape != c2.shape and c1.shape != c3.shape and c2.shape != c3.shape:
            if c1.color != c2.color and c1.color != c3.color and c2.color != c3.color:
                if (
                    c1.number != c2.number
                    and c1.number != c3.number
                    and c2.number != c3.number
                ):
                    if c1.fill != c2.fill and c1.fill != c3.fill and c2.fill != c3.fill:
                        sets.add((c1, c2, c3))

        if c1.shape == c2.shape and c1.shape == c3.shape:
            if c1.color != c2.color and c1.color != c3.color and c2.color != c3.color:
                if (
                    c1.number != c2.number
                    and c1.number != c3.number
                    and c2.number != c3.number
                ):
                    if c1.fill != c2.fill and c1.fill != c3.fill and c2.fill != c3.fill:
                        sets.add((c1, c2, c3))

        if c1.color == c2.color and c1.color == c3.color:
            if c1.shape != c2.shape and c1.shape != c3.shape and c2.shape != c3.shape:
                if (
                    c1.number != c2.number
                    and c1.number != c3.number
                    and c2.number != c3.number
                ):
                    if c1.fill != c2.fill and c1.fill != c3.fill and c2.fill != c3.fill:
                        sets.add((c1, c2, c3))

        if c1.number == c2.number and c1.number == c3.number:
            if c1.shape != c2.shape and c1.shape != c3.shape and c2.shape != c3.shape:
                if (
                    c1.color != c2.color
                    and c1.color != c3.color
                    and c2.color != c3.color
                ):
                    if c1.fill != c2.fill and c1.fill != c3.fill and c2.fill != c3.fill:
                        sets.add((c1, c2, c3))

        if c1.fill == c2.fill and c1.fill == c3.fill:
            if c1.shape != c2.shape and c1.shape != c3.shape and c2.shape != c3.shape:
                if (
                    c1.color != c2.color
                    and c1.color != c3.color
                    and c2.color != c3.color
                ):
                    if (
                        c1.number != c2.number
                        and c1.number != c3.number
                        and c2.number != c3.number
                    ):
                        sets.add((c1, c2, c3))

    return sets


s = """2 3 1 2
3 3 3 1
2 1 3 3
2 3 2 1
1 3 1 3
2 2 1 1
3 3 1 1
2 1 2 3
1 2 3 2
2 1 3 1
2 1 3 2
1 2 3 3"""

cards = set([Card(*map(int, line.split())) for line in s.splitlines()])
sets = find_sets(cards)
for s in sets:
    print(s)
