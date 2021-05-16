import copy
import random
import typing

import expenvelope  # type: ignore

from mutwo.converters import abc
from mutwo.converters import symmetrical
from mutwo.events import abc as mutwo_abc_events
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos
from mutwo.utilities import constants as mutwo_constants

from ot2.converters.symmetrical import playing_indicators as ot2_playing_indicators
from ot2.events import colotomic_brackets
from ot2.events import time_brackets


class ColotomicPatternToNestedSequentialEventConverter(abc.Converter):
    @staticmethod
    def _make_tempo_envelope(
        colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern,
    ) -> expenvelope.Envelope:
        tempo = colotomic_pattern_to_convert.tempo
        if isinstance(tempo.tempo_or_tempo_range_in_beats_per_minute, tuple):
            tempo_in_beats_per_minute = random.uniform(
                *tempo.tempo_or_tempo_range_in_beats_per_minute
            )
            tempo = tempos.TempoPoint(
                tempo_in_beats_per_minute, reference=tempo.reference
            )

        return expenvelope.Envelope.from_levels_and_durations(
            levels=[tempo, tempo], durations=[1]
        )

    @staticmethod
    def _make_tempo_converter(
        colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern,
    ) -> symmetrical.tempos.TempoConverter:
        tempo_envelope = ColotomicPatternToNestedSequentialEventConverter._make_tempo_envelope(
            colotomic_pattern_to_convert
        )
        tempo_converter = symmetrical.tempos.TempoConverter(tempo_envelope)
        return tempo_converter

    @staticmethod
    def _make_playing_indicators_converter() -> symmetrical.playing_indicators.PlayingIndicatorsConverter:
        return symmetrical.playing_indicators.PlayingIndicatorsConverter(
            [ot2_playing_indicators.ExplicitFermataConverter()]
        )

    def _convert_colotomic_pattern(
        self, colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern
    ) -> basic.SequentialEvent[basic.SequentialEvent[music.NoteLike]]:
        tempo_converter = ColotomicPatternToNestedSequentialEventConverter._make_tempo_converter(
            colotomic_pattern_to_convert
        )
        playing_indicators_converter = (
            ColotomicPatternToNestedSequentialEventConverter._make_playing_indicators_converter()
        )

        converted_colotomic_pattern = basic.SequentialEvent([])
        for colotomic_element in colotomic_pattern_to_convert:
            adjusted_colotomic_element = playing_indicators_converter.convert(
                tempo_converter.convert(colotomic_element)
            )
            # adjusted_colotomic_element = tempo_converter.convert(colotomic_element)
            converted_colotomic_pattern.append(adjusted_colotomic_element)

        return converted_colotomic_pattern

    def convert(
        self, colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern
    ) -> basic.SequentialEvent[
        basic.SequentialEvent[basic.SequentialEvent[music.NoteLike]]
    ]:
        """Convert colotomic pattern.

        Nested return structure is:
            [
                ColotomicPattern_Repetition_0[ColotomicElement[Item]],
                ColotomicPattern_Repetition_1[ColotomicElement[Item]],
                ColotomicPattern_Repetition_2[ColotomicElement[Item]],
                ...
            ]
        """

        repetitions = basic.SequentialEvent([])
        for _ in range(colotomic_pattern_to_convert.n_repetitions):
            repetitions.append(
                self._convert_colotomic_pattern(colotomic_pattern_to_convert)
            )

        return repetitions


class ColotomicBracketToTimeBracketConverter(abc.Converter):
    def __init__(
        self,
        converted_colotomic_pattern: basic.SequentialEvent[
            basic.SequentialEvent[basic.SequentialEvent[music.NoteLike]]
        ],
    ):
        self._converted_colotomic_pattern = converted_colotomic_pattern

    @staticmethod
    def _get_absolute_time_of_nested_element(
        indices: typing.Sequence[int], nested_event: mutwo_abc_events.ComplexEvent
    ) -> mutwo_constants.Real:
        absolute_time = 0
        for nth_index, index in enumerate(indices):
            absolute_time += nested_event.get_event_from_indices(
                indices[:nth_index]
            ).absolute_times[index]

        return absolute_time

    def _convert_position_to_time(
        self, position: colotomic_brackets.ColotomicElementIndicator
    ) -> mutwo_constants.Real:
        return ColotomicBracketToTimeBracketConverter._get_absolute_time_of_nested_element(
            position, self._converted_colotomic_pattern
        )

    def _position_or_position_range_to_time_or_time_range(
        self, position_or_position_range: colotomic_brackets.PositionOrPositionRange,
    ) -> time_brackets.TimeOrTimeRange:
        if hasattr(position_or_position_range, "__getitem__"):
            return (
                self._convert_position_to_time(position_or_position_range[0]),
                self._convert_position_to_time(position_or_position_range[1]),
            )
        else:
            return self._convert_position_to_time(position_or_position_range)

    def convert(
        self, colotomic_bracket_to_convert: colotomic_brackets.ColotomicBracket
    ) -> time_brackets.TimeBracket:
        start_time_or_start_time_range = self._position_or_position_range_to_time_or_time_range(
            colotomic_bracket_to_convert.start_position_or_start_position_range
        )
        end_time_or_end_time_range = self._position_or_position_range_to_time_or_time_range(
            colotomic_bracket_to_convert.end_position_or_end_position_range
        )

        converted_time_bracket = time_brackets.TimeBracket(
            tuple(colotomic_bracket_to_convert),
            start_time_or_start_time_range,
            end_time_or_end_time_range,
        )

        return converted_time_bracket
