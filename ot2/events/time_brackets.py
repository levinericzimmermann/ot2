import random
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.utilities import constants
from mutwo.parameters import tempos

from ot2.events import basic as ot2_basic
from ot2.events import brackets
from ot2.utilities import exceptions

TimeOrTimeRange = typing.Union[
    constants.Real, typing.Tuple[constants.Real, constants.Real]
]


class TimeBracket(brackets.Bracket):
    def __init__(
        self,
        simultaneous_events: typing.Sequence[
            ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
        start_or_start_range: TimeOrTimeRange,
        end_or_end_range: TimeOrTimeRange,
    ):
        super().__init__(simultaneous_events, start_or_start_range, end_or_end_range)

    @staticmethod
    def _assign_concrete_time(time_or_time_range: TimeOrTimeRange) -> constants.Real:
        if hasattr(time_or_time_range, "__getitem__"):
            return random.uniform(*time_or_time_range)
        else:
            return time_or_time_range

    @brackets.Bracket.start_or_start_range.setter
    def start_or_start_range(self, start_or_start_range: TimeOrTimeRange):
        self._start_or_start_range = start_or_start_range
        if hasattr(self, "_assigned_start_time"):
            self.assign_concrete_times()

    @brackets.Bracket.end_or_end_range.setter
    def end_or_end_range(self, end_or_end_range: TimeOrTimeRange):
        self._end_or_end_range = end_or_end_range
        if hasattr(self, "_assigned_end_time"):
            self.assign_concrete_times()

    @property
    def mean_start(self) -> constants.Real:
        return brackets.Bracket._get_mean_of_value_or_value_range(
            self.start_or_start_range
        )

    @property
    def mean_end(self) -> constants.Real:
        return TimeBracket._get_mean_of_value_or_value_range(self.end_or_end_range)

    @property
    def duration(self) -> constants.Real:
        return self.mean_end - self.mean_start

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
            self.start_or_start_range
        )
        self._assigned_end_time = TimeBracket._assign_concrete_time(
            self.end_or_end_range
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


class TimeBracketContainer(brackets.BracketContainer[TimeBracket]):
    pass
