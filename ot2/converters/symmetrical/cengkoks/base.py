"""Convert analysis.phrases to time brackets.

Conversion routines for Part "B" (cengkok based / cantus-firmus based parts).
"""

import abc
import typing

import abjad

from mutwo import converters
from mutwo import events

from ot2 import analysis
from ot2.converters.symmetrical import keyboard as keyboard_converter
from ot2.converters.symmetrical import (
    keyboard_constants as keyboard_converter_constants,
)
from ot2 import events as ot2_events


class CengkokTimeBracket(events.time_brackets.TempoBasedTimeBracket):
    _class_specific_side_attributes = (
        events.time_brackets.TimeBracket._class_specific_side_attributes
        + (
            "tempo",
            "time_signatures",
            "distribution_strategy",
            "engine_distribution_strategy",
        )
    )

    # distribution_strategy = (
    #     keyboard_converter.HandBasedPitchDistributionStrategy()
    # )
    # is object attribute
    # distribution_strategy = keyboard_converter.MultipleTrialsDistributionStrategy(
    #     (
    #         keyboard_converter.HandBasedPitchDistributionStrategy(),
    #         keyboard_converter.HandBasedPitchDistributionStrategy(
    #             available_keys=tuple(
    #                 sorted(
    #                     keyboard_converter_constants.DIATONIC_PITCHES
    #                     + keyboard_converter_constants.CHROMATIC_PITCHES
    #                 )
    #             )
    #         ),
    #     )
    # )

    def __init__(
        self,
        tagged_events: typing.Sequence[
            typing.Union[
                events.basic.TaggedSequentialEvent,
                events.basic.TaggedSimpleEvent,
                events.basic.TaggedSimultaneousEvent,
            ]
        ],
        start_or_start_range: events.time_brackets.TimeOrTimeRange,
        end_or_end_range: events.time_brackets.TimeOrTimeRange,
        time_signatures: typing.Sequence[abjad.TimeSignature],
        tempo: float,
        seed: typing.Optional[int] = None,
        force_spanning_of_end_or_end_range: bool = False,
        distribution_strategy=keyboard_converter.MultipleTrialsDistributionStrategy(
            (
                keyboard_converter.HandBasedPitchDistributionStrategy(),
                keyboard_converter.HandBasedPitchDistributionStrategy(
                    available_keys=tuple(
                        sorted(
                            keyboard_converter_constants.DIATONIC_PITCHES
                            + keyboard_converter_constants.CHROMATIC_PITCHES
                        )
                    )
                ),
            )
        ),
        engine_distribution_strategy=None,
    ):
        super().__init__(
            tagged_events,
            start_or_start_range,
            end_or_end_range,
            tempo,
            seed,
            force_spanning_of_end_or_end_range,
        )
        self.distribution_strategy = distribution_strategy
        self.engine_distribution_strategy = engine_distribution_strategy
        self.time_signatures = time_signatures


class RiverCengkokTimeBracket(CengkokTimeBracket):
    pass


class PhraseToTimeBracketsConverter(converters.abc.Converter):
    time_bracket_class = CengkokTimeBracket

    def __init__(
        self,
        start_or_start_range: events.time_brackets.TimeOrTimeRange,
        end_or_end_range: events.time_brackets.TimeOrTimeRange,
    ):
        self._start_or_start_range = start_or_start_range
        self._end_or_end_range = end_or_end_range

    @staticmethod
    def _add_cent_deviation(
        sequential_event_to_process: events.basic.SequentialEvent[
            events.music.NoteLike
        ],
    ):
        previous_pitch = None
        for event in sequential_event_to_process:
            if hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches:
                if (pitch_to_process := event.pitch_or_pitches[0]) != previous_pitch:
                    deviation = (
                        pitch_to_process.cent_deviation_from_closest_western_pitch_class
                    )
                    event.notation_indicators.cent_deviation.deviation = deviation
                    previous_pitch = pitch_to_process
            else:
                previous_pitch = None

    def _make_time_bracket_blueprint(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> CengkokTimeBracket:
        time_signatures = [
            abjad.TimeSignature((int(event.duration * 4), 4))
            for event in phrase_to_convert
        ]
        time_bracket = self.time_bracket_class(
            [],
            self._start_or_start_range,
            self._end_or_end_range,
            time_signatures=time_signatures,
            tempo=phrase_to_convert.tempo,
            seed=100,
        )
        return time_bracket

    @abc.abstractmethod
    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> typing.Tuple[CengkokTimeBracket, ...]:
        raise NotImplementedError
