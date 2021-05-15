import typing


from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos

from ot2.events import basic as ot2_basic


class ColotomicElement(basic.SequentialEvent[music.NoteLike]):
    pass


TempoPoint = typing.Union[float, tempos.TempoPoint]


class ColotomicPattern(basic.SequentialEvent[ColotomicElement]):
    def __init__(
        self,
        colotomic_elements: typing.Sequence[ColotomicElement],
        n_repetitions: int = 3,
        tempo: tempos.TempoPoint = tempos.TempoPoint(60),
        time_signature: typing.Tuple[int, int] = (4, 4),
    ):
        self.tempo = tempo
        self.n_repetitions = n_repetitions
        self.time_signature = time_signature
        super().__init__(colotomic_elements)


# nth pattern, nth repetitions, nth element
ColotomicElementIndicator = typing.Tuple[int, int, int]

PositionOrPositionRange = typing.Union[
    ColotomicElementIndicator,
    typing.Tuple[ColotomicElementIndicator, ColotomicElementIndicator],
]


class ColotomicBracket(
    basic.SimultaneousEvent[
        ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
    ]
):
    def __init__(
        self,
        simultaneous_events: typing.Sequence[
            ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
        start_position_or_start_position_range: PositionOrPositionRange,
        end_position_or_end_position_range: PositionOrPositionRange,
    ):
        super().__init__(simultaneous_events)
        self.start_position_or_start_position_range = (
            start_position_or_start_position_range
        )
        self.end_position_or_end_position_range = end_position_or_end_position_range


class TempoBasedColotomicBracket(ColotomicBracket):
    pass


class ColotomicBracketContainer(object):
    pass
