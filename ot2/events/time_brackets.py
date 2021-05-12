import statistics
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.utilities import constants
from mutwo.parameters import tempos


class TimeBracket(
    basic.SimultaneousEvent[
        basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
    ]
):
    def __init__(
        self,
        simultaneous_events: typing.Sequence[
            basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
        start_time_range: typing.Tuple[constants.Real, constants.Real],
        stop_time_range: typing.Tuple[constants.Real, constants.Real],
    ):
        self._start_time_range = start_time_range
        self._stop_time_range = stop_time_range
        super().__init__(simultaneous_events)

    @property
    def start_time_range(self) -> typing.Tuple[constants.Real, constants.Real]:
        return self._start_time_range

    @property
    def stop_time_range(self) -> typing.Tuple[constants.Real, constants.Real]:
        return self._stop_time_range

    @property
    def duration(self) -> constants.Real:
        return statistics.mean(self.stop_time_range) - statistics.mean(
            self.start_time_range
        )


class TempoBasedTimeBracket(TimeBracket):
    def __init__(
        self,
        sequential_events: typing.Sequence[basic.SequentialEvent],
        start_time_range: typing.Tuple[constants.Real, constants.Real],
        tempo_range: typing.Tuple[tempos.TempoPoint, tempos.TempoPoint],
    ):
        self._tempo_range = tempo_range
        stop_time_range = TempoBasedTimeBracket._find_stop_time_range(
            sequential_events, start_time_range, tempo_range
        )
        super().__init__(sequential_events, start_time_range, stop_time_range)

    @staticmethod
    def _find_stop_time_range(
        sequential_events: typing.Sequence[basic.SequentialEvent],
        start_time_range: typing.Tuple[constants.Real, constants.Real],
        tempo_range: typing.Tuple[tempos.TempoPoint, tempos.TempoPoint],
    ) -> typing.Tuple[constants.Real, constants.Real]:
        pass

    @property
    def tempo_range(self) -> typing.Tuple[tempos.TempoPoint, tempos.TempoPoint]:
        return self._tempo_range


class TimeBracketContainer(object):
    def __init__(self, n_instruments: int):
        pass

    def register(
        self, time_bracket: TimeBracket, used_instruments: typing.Sequence[int]
    ) -> None:
        """Register new TimeBracket in TimeBracketContainer"""
        pass

    def filter(
        self, instrument_index: int
    ) -> typing.Tuple[typing.Tuple[typing.Tuple[int, ...], TimeBracket], ...]:
        """Filter all time brackets that belong to a certain instrument

        :return: Instrument indices/TimeBracket pairs sorted by
            start_time_range
        """
        pass
