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
        colors = {c1.color, c2.color, c3.color}
        shapes = {c1.shape, c2.shape, c3.shape}
        numbers = {c1.number, c2.number, c3.number}
        fills = {c1.fill, c2.fill, c3.fill}
        # chaos set
        if (
            len(colors) == 3
            and len(shapes) == 3
            and len(numbers) == 3
            and len(fills) == 3
        ):
            sets.add((1, frozenset({c1, c2, c3})))
        if len(colors) == 2 or len(shapes) == 2 or len(numbers) == 2 or len(fills) == 2:
            continue
        sets.add((0, frozenset({c1, c2, c3})))
    return sets


_values = [
    Card(Shape.diamond, Color.red, Number.one, Fill.striped),
    Card(Shape.diamond, Color.red, Number.two, Fill.striped),
    Card(Shape.diamond, Color.red, Number.three, Fill.striped),
    Card(Shape.oval, Color.red, Number.one, Fill.striped),
    Card(Shape.oval, Color.red, Number.two, Fill.striped),
    Card(Shape.oval, Color.red, Number.three, Fill.striped),
    Card(Shape.squiggle, Color.red, Number.one, Fill.striped),
    Card(Shape.squiggle, Color.red, Number.two, Fill.striped),
    Card(Shape.squiggle, Color.red, Number.three, Fill.striped),
    Card(Shape.diamond, Color.red, Number.one, Fill.solid),
    Card(Shape.diamond, Color.red, Number.two, Fill.solid),
    Card(Shape.diamond, Color.red, Number.three, Fill.solid),
    Card(Shape.oval, Color.red, Number.one, Fill.solid),
    Card(Shape.oval, Color.red, Number.two, Fill.solid),
    Card(Shape.oval, Color.red, Number.three, Fill.solid),
    Card(Shape.squiggle, Color.red, Number.one, Fill.solid),
    Card(Shape.squiggle, Color.red, Number.two, Fill.solid),
    Card(Shape.squiggle, Color.red, Number.three, Fill.solid),
    Card(Shape.diamond, Color.purple, Number.one, Fill.empty),
    Card(Shape.diamond, Color.purple, Number.two, Fill.empty),
    Card(Shape.diamond, Color.purple, Number.three, Fill.empty),
    Card(Shape.oval, Color.purple, Number.one, Fill.empty),
    Card(Shape.oval, Color.purple, Number.two, Fill.empty),
    Card(Shape.oval, Color.purple, Number.three, Fill.empty),
    Card(Shape.squiggle, Color.purple, Number.one, Fill.empty),
    Card(Shape.squiggle, Color.purple, Number.two, Fill.empty),
    Card(Shape.squiggle, Color.purple, Number.three, Fill.empty),
    Card(Shape.diamond, Color.purple, Number.one, Fill.striped),
    Card(Shape.diamond, Color.purple, Number.two, Fill.striped),
    Card(Shape.diamond, Color.purple, Number.three, Fill.striped),
    Card(Shape.oval, Color.purple, Number.one, Fill.striped),
    Card(Shape.oval, Color.purple, Number.two, Fill.striped),
    Card(Shape.oval, Color.purple, Number.three, Fill.striped),
    Card(Shape.squiggle, Color.purple, Number.one, Fill.striped),
    Card(Shape.squiggle, Color.purple, Number.two, Fill.striped),
    Card(Shape.squiggle, Color.purple, Number.three, Fill.striped),
    Card(Shape.diamond, Color.purple, Number.one, Fill.solid),
    Card(Shape.diamond, Color.purple, Number.two, Fill.solid),
    Card(Shape.diamond, Color.purple, Number.three, Fill.solid),
    Card(Shape.oval, Color.purple, Number.one, Fill.solid),
    Card(Shape.oval, Color.purple, Number.two, Fill.solid),
    Card(Shape.oval, Color.purple, Number.three, Fill.solid),
    Card(Shape.squiggle, Color.purple, Number.one, Fill.solid),
    Card(Shape.squiggle, Color.purple, Number.two, Fill.solid),
    Card(Shape.squiggle, Color.purple, Number.three, Fill.solid),
    Card(Shape.diamond, Color.green, Number.one, Fill.empty),
    Card(Shape.diamond, Color.green, Number.two, Fill.empty),
    Card(Shape.diamond, Color.green, Number.three, Fill.empty),
    Card(Shape.oval, Color.green, Number.one, Fill.empty),
    Card(Shape.oval, Color.green, Number.two, Fill.empty),
    Card(Shape.oval, Color.green, Number.three, Fill.empty),
    Card(Shape.squiggle, Color.green, Number.one, Fill.empty),
    Card(Shape.squiggle, Color.green, Number.two, Fill.empty),
    Card(Shape.squiggle, Color.green, Number.three, Fill.empty),
    Card(Shape.diamond, Color.green, Number.one, Fill.striped),
    Card(Shape.diamond, Color.green, Number.two, Fill.striped),
    Card(Shape.diamond, Color.green, Number.three, Fill.striped),
    Card(Shape.oval, Color.green, Number.one, Fill.striped),
    Card(Shape.oval, Color.green, Number.two, Fill.striped),
    Card(Shape.oval, Color.green, Number.three, Fill.striped),
    Card(Shape.squiggle, Color.green, Number.one, Fill.striped),
    Card(Shape.squiggle, Color.green, Number.two, Fill.striped),
    Card(Shape.squiggle, Color.green, Number.three, Fill.striped),
    Card(Shape.diamond, Color.green, Number.one, Fill.solid),
    Card(Shape.diamond, Color.green, Number.two, Fill.solid),
    Card(Shape.diamond, Color.green, Number.three, Fill.solid),
    Card(Shape.oval, Color.green, Number.one, Fill.solid),
    Card(Shape.oval, Color.green, Number.two, Fill.solid),
    Card(Shape.oval, Color.green, Number.three, Fill.solid),
    Card(Shape.squiggle, Color.green, Number.one, Fill.solid),
    Card(Shape.squiggle, Color.green, Number.two, Fill.solid),
    Card(Shape.squiggle, Color.green, Number.three, Fill.solid),
    Card(Shape.diamond, Color.red, Number.one, Fill.empty),
    Card(Shape.diamond, Color.red, Number.two, Fill.empty),
    Card(Shape.diamond, Color.red, Number.three, Fill.empty),
    Card(Shape.oval, Color.red, Number.one, Fill.empty),
    Card(Shape.oval, Color.red, Number.two, Fill.empty),
    Card(Shape.oval, Color.red, Number.three, Fill.empty),
    Card(Shape.squiggle, Color.red, Number.one, Fill.empty),
    Card(Shape.squiggle, Color.red, Number.two, Fill.empty),
    Card(Shape.squiggle, Color.red, Number.three, Fill.empty),
]

mapping = {k: v for k, v in zip(range(81), _values)}
