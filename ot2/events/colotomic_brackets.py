import typing


from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos
from mutwo.utilities import constants

from ot2.events import basic as ot2_basic
from ot2.events import brackets


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


class ColotomicBracket(brackets.Bracket):
    def __init__(
        self,
        simultaneous_events: typing.Sequence[
            ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
        start_position_or_start_position_range: PositionOrPositionRange,
        end_position_or_end_position_range: PositionOrPositionRange,
    ):
        super().__init__(
            simultaneous_events,
            start_position_or_start_position_range,
            end_position_or_end_position_range,
        )

    @staticmethod
    def _position_to_position_index(
        position: ColotomicElementIndicator,
    ) -> constants.Real:
        return int("{}{}{}".format(*position))

    @staticmethod
    def _position_or_position_range_to_position_index_or_position_index_range(
        position_or_position_range: PositionOrPositionRange,
    ) -> typing.Union[constants.Real, typing.Tuple[constants.Real, constants.Real]]:
        if len(position_or_position_range) == 2:
            return (
                ColotomicBracket._position_to_position_index(
                    position_or_position_range[0]
                ),
                ColotomicBracket._position_to_position_index(
                    position_or_position_range[1]
                ),
            )
        else:
            return ColotomicBracket._position_to_position_index(
                position_or_position_range
            )

    @property
    def mean_start(self) -> constants.Real:
        return brackets.Bracket._get_mean_of_value_or_value_range(
            ColotomicBracket._position_or_position_range_to_position_index_or_position_index_range(
                self.start_or_start_range
            )
        )

    @property
    def mean_end(self) -> constants.Real:
        return brackets.Bracket._get_mean_of_value_or_value_range(
            ColotomicBracket._position_or_position_range_to_position_index_or_position_index_range(
                self.end_or_end_range
            )
        )


class TempoBasedColotomicBracket(ColotomicBracket):
    pass


class ColotomicBracketContainer(brackets.BracketContainer[ColotomicBracket]):
    pass
