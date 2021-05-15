import statistics
import random
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.utilities import constants
from mutwo.parameters import tempos

from ot2.events import basic as ot2_basic
from ot2.utilities import exceptions

TimeOrTimeRange = typing.Union[
    constants.Real, typing.Tuple[constants.Real, constants.Real]
]


class TimeBracket(
    basic.SimultaneousEvent[
        ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
    ]
):
    def __init__(
        self,
        simultaneous_events: typing.Sequence[
            ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
        start_time_or_start_time_range: TimeOrTimeRange,
        end_time_or_end_time_range: TimeOrTimeRange,
    ):
        self._start_time_or_start_time_range = start_time_or_start_time_range
        self._end_time_or_end_time_range = end_time_or_end_time_range
        super().__init__(simultaneous_events)

    @staticmethod
    def _get_mean_of_time_or_time_range(
        time_or_time_range: TimeOrTimeRange,
    ) -> constants.Real:
        if isinstance(time_or_time_range, typing.Sequence):
            return statistics.mean(time_or_time_range)
        else:
            return time_or_time_range

    @staticmethod
    def _assign_concrete_time(time_or_time_range: TimeOrTimeRange) -> constants.Real:
        if hasattr(time_or_time_range, "__getitem__"):
            return random.uniform(*time_or_time_range)
        else:
            return time_or_time_range

    @property
    def start_time_or_start_time_range(self) -> TimeOrTimeRange:
        return self._start_time_or_start_time_range

    @property
    def end_time_or_end_time_range(self) -> TimeOrTimeRange:
        return self._end_time_or_end_time_range

    @property
    def mean_start_time(self) -> constants.Real:
        return TimeBracket._get_mean_of_time_or_time_range(
            self.start_time_or_start_time_range
        )

    @property
    def mean_end_time(self) -> constants.Real:
        return TimeBracket._get_mean_of_time_or_time_range(
            self.end_time_or_end_time_range
        )

    @property
    def duration(self) -> constants.Real:
        return self.mean_end_time - self.mean_start_time

    @property
    def assigned_start_time(self) -> constants.Real:
        try:
            return self._assigned_start_time
        except AttributeError:
            raise exceptions.ValueNotAssignedError()

    @property
    def assigned_end_time(self) -> constants.Real:
        try:
            return self._assigned_end_time
        except AttributeError:
            raise exceptions.ValueNotAssignedError()

    def assign_concrete_times(self):
        """Assign concrete values for start and end time"""
        self._assigned_start_time = TimeBracket._assign_concrete_time(
            self.start_time_or_start_time_range
        )
        self._assigned_end_time = TimeBracket._assign_concrete_time(
            self.end_time_or_end_time_range
        )


class TempoBasedTimeBracket(TimeBracket):
    def __init__(
        self,
        sequential_events: typing.Sequence[basic.SequentialEvent],
        start_time_range: typing.Tuple[constants.Real, constants.Real],
        tempo_range: typing.Tuple[tempos.TempoPoint, tempos.TempoPoint],
    ):
        self._tempo_range = tempo_range
        end_time_range = TempoBasedTimeBracket._find_end_time_range(
            sequential_events, start_time_range, tempo_range
        )
        super().__init__(sequential_events, start_time_range, end_time_range)

    @staticmethod
    def _find_end_time_range(
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
