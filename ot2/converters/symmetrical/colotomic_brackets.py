import random

import expenvelope  # type: ignore

from mutwo.converters import abc
from mutwo.converters import symmetrical
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos

from ot2.events import colotomic_brackets
from ot2.converters.symmetrical import playing_indicators as ot2_playing_indicators


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
