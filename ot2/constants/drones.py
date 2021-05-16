"""Composed structures for Drone instrument"""

from mutwo.events import basic
from mutwo.events import music

from ot2.constants import colotomic_brackets_container
from ot2.constants import instruments
from ot2.events import basic as ot2_basic
from ot2.events import colotomic_brackets


COLOTOMIC_BRACKETS = (
    colotomic_brackets.ColotomicBracket(
        (
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("15/32", 1)])],
                instruments.ID_DRONE,
            ),
        ),
        ((0, 0, 1), (0, 1, 0)),
        ((0, 2, 1), (0, 3, 0)),
    ),
    colotomic_brackets.ColotomicBracket(
        (
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("21/64", 1)])],
                instruments.ID_DRONE,
            ),
        ),
        ((1, 0, 0), (1, 0, 1)),
        ((1, 2, 0), (1, 2, 1)),
    ),
)

for colotomic_bracket in COLOTOMIC_BRACKETS:
    colotomic_brackets_container.COLOTOMIC_BRACKETS_CONTAINER.register(colotomic_bracket)
