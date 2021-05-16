import typing

from mutwo.converters import abc as converters_abc
from mutwo.events import basic
from mutwo.events import music
from mutwo.utilities import constants

from ot2.events import basic as ot2_basic
from ot2.events import time_brackets
from ot2.utilities import exceptions


class TimeBracketsToSimultaneousEventConverter(converters_abc.Converter):
    def __init__(self, instrument: str, n_voices: int = 1):
        self._instrument = instrument
        self._n_voices = 1

    @staticmethod
    def _get_start_and_end_time(
        time_bracket: time_brackets.TimeBracket,
    ) -> typing.Tuple[constants.Real, constants.Real]:
        try:
            start_time, end_time = (
                time_bracket.assigned_start_time,
                time_bracket.assigned_end_time,
            )
        except exceptions.ValueNotAssignedError:
            time_bracket.assign_concrete_times()
            (
                start_time,
                end_time,
            ) = TimeBracketsToSimultaneousEventConverter._get_start_and_end_time(
                time_bracket
            )

        return start_time, end_time

    @staticmethod
    def _adjust_assigned_simultaneous_event(
        assigned_simultaneous_event: ot2_basic.AssignedSimultaneousEvent[
            basic.SequentialEvent[music.NoteLike]
        ],
        duration_in_seconds: constants.Real,
    ) -> ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        assigned_simultaneous_event.duration = duration_in_seconds
        return assigned_simultaneous_event

    def _extract_assigned_simultaneous_event(
        self,
        simultaneous_events: typing.Sequence[
            ot2_basic.AssignedSimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
    ) -> ot2_basic.AssignedSimultaneousEvent:
        for assigned_simultaneous_event in simultaneous_events:
            if assigned_simultaneous_event.instrument == self._instrument:
                return assigned_simultaneous_event

        raise NotImplementedError(
            "Couldn't find instrument '{}' in bracket.".format(self._instrument)
        )

    def convert(
        self, time_brackets_to_convert: typing.Sequence[time_brackets.TimeBracket]
    ) -> basic.SequentialEvent[typing.Union[music.NoteLike, basic.SimpleEvent]]:
        simultaneous_event = basic.SimultaneousEvent(
            [basic.SequentialEvent([]) for _ in range(self._n_voices)]
        )
        previous_end_time = 0
        for time_bracket in time_brackets_to_convert:
            (
                start_time,
                end_time,
            ) = TimeBracketsToSimultaneousEventConverter._get_start_and_end_time(
                time_bracket
            )

            # add rest if there is time between last time bracket and current bracket
            if previous_end_time < start_time:
                for sequential_event in simultaneous_event:
                    sequential_event.append(
                        basic.SimpleEvent(start_time - previous_end_time)
                    )
            # raise error if last bracket is still running while the current
            # time bracket already started
            elif previous_end_time > start_time:
                raise ValueError("Found overlapping time brackets!")

            duration_in_seconds = end_time - start_time
            assigned_simultaneous_event = self._extract_assigned_simultaneous_event(
                tuple(time_bracket)
            )
            processed_assigned_simultaneous_event = TimeBracketsToSimultaneousEventConverter._adjust_assigned_simultaneous_event(
                assigned_simultaneous_event, duration_in_seconds
            )
            for (nth_sequential_event, sequential_event,) in enumerate(
                processed_assigned_simultaneous_event
            ):
                simultaneous_event[nth_sequential_event].extend(sequential_event)

            previous_end_time = end_time

        return simultaneous_event
