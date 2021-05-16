"""Composed structures for sustaining instruments"""

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
                [basic.SequentialEvent([music.NoteLike("3/4", 1, 'f')])],
                instruments.ID_SUS0,
            ),
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("5/8", 1, 'f')])],
                instruments.ID_SUS1,
            ),
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("1/2", 1, 'f')])],
                instruments.ID_SUS2,
            ),
        ),
        (0, 1, 1),
        ((0, 1, 1), (0, 2, 0)),
    ),
    colotomic_brackets.ColotomicBracket(
        (
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("15/16", 1, 'f')])],
                instruments.ID_SUS0,
            ),
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("9/16", 1, 'f')])],
                instruments.ID_SUS1,
            ),
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("15/32", 1, 'f')])],
                instruments.ID_SUS2,
            ),
        ),
        (0, 2, 1),
        ((0, 3, 0), (0, 3, 1)),
    ),
    colotomic_brackets.ColotomicBracket(
        (
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("7/8", 1, 'f')])],
                instruments.ID_SUS0,
            ),
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("3/4", 1, 'f')])],
                instruments.ID_SUS1,
            ),
            ot2_basic.AssignedSimultaneousEvent(
                [basic.SequentialEvent([music.NoteLike("1/2", 1, 'f')])],
                instruments.ID_SUS2,
            ),
        ),
        (1, 0, 2),
        ((1, 1, 1), (1, 2, 0)),
    ),
)

for colotomic_bracket in COLOTOMIC_BRACKETS:
    colotomic_brackets_container.COLOTOMIC_BRACKETS_CONTAINER.register(
        colotomic_bracket
    )
