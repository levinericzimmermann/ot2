import typing

import abjad  # type: ignore
import expenvelope  # type: ignore

from mutwo.events import basic
from mutwo.events import music

from mutwo.converters import abc as converters_abc
from mutwo.converters.frontends import abjad as mutwo_abjad

from ot2.events import colotomic_brackets
from ot2.events import time_brackets


class ColotomicPatternToAbjadScoreConverter(converters_abc.Converter):
    @staticmethod
    def _prepare_abjad_voice(
        abjad_voice: abjad.Voice,
        colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern,
    ) -> None:
        abjad.attach(abjad.Clef("percussion"), abjad_voice[0][0])

        # add repeat and n repetitions
        abjad.attach(
            abjad.Repeat(repeat_count=colotomic_pattern_to_convert.n_repetitions),
            abjad_voice,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\mark \\markup { \\smallCaps "
                + '"{}x"'.format(colotomic_pattern_to_convert.n_repetitions)
                + "}",
                format_slot="after",
            ),
            abjad_voice[-1][-1],
        )

    @staticmethod
    def _extract_sequential_event_from_colotomic_pattern(
        colotomic_pattern: colotomic_brackets.ColotomicPattern,
    ) -> basic.SequentialEvent[music.NoteLike]:
        sequential_event = basic.SequentialEvent([])
        for colotomic_element in colotomic_pattern:
            sequential_event.extend(colotomic_element)
        return sequential_event

    def _make_sequential_event_to_abjad_voice_converter(
        self, colotomic_pattern: colotomic_brackets.ColotomicPattern
    ) -> mutwo_abjad.SequentialEventToAbjadVoiceConverter:
        tempo_envelope = expenvelope.Envelope.from_levels_and_durations(
            levels=[colotomic_pattern.tempo, colotomic_pattern.tempo], durations=[1]
        )
        sequential_event_to_quantized_abjad_container_converter = mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
            tempo_envelope=tempo_envelope
        )
        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            sequential_event_to_quantized_abjad_container_converter
        )
        return sequential_event_to_abjad_voice_converter

    def convert(
        self, colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern
    ) -> abjad.Score:
        sequential_event = ColotomicPatternToAbjadScoreConverter._extract_sequential_event_from_colotomic_pattern(
            colotomic_pattern_to_convert
        )
        converter = self._make_sequential_event_to_abjad_voice_converter(
            colotomic_pattern_to_convert
        )
        abjad_voice = converter.convert(sequential_event)

        ColotomicPatternToAbjadScoreConverter._prepare_abjad_voice(
            abjad_voice, colotomic_pattern_to_convert
        )

        abjad_score = abjad.Score([abjad_voice])
        return abjad_score


class ColotomicPatternsToLilypondFileConverter(converters_abc.Converter):
    def __init__(self):
        self._colotomic_pattern_to_abjad_score_converter = (
            ColotomicPatternToAbjadScoreConverter()
        )

    def convert(
        self, colotomic_patterns: typing.Sequence[colotomic_brackets.ColotomicPattern]
    ) -> abjad.LilyPondFile:
        # add margin markup (pattern number)
        for nth_pattern, colotomic_pattern in enumerate(colotomic_patterns):
            colotomic_pattern[0][0].notation_indicators.margin_markup.content = (
                "{}".format(nth_pattern + 1)
            )

        abjad_scores = [
            self._colotomic_pattern_to_abjad_score_converter.convert(colotomic_pattern)
            for colotomic_pattern in colotomic_patterns
        ]

        lilypond_file = abjad.LilyPondFile()

        header = abjad.Block('header')
        header.title = '"ohne Titel (2)"'
        header.instrument = '"percussive instrument(s)"'
        header.composer = '"Levin Eric Zimmermann"'
        # header.tagline = '"oT(2)"'
        header.tagline = '""'
        lilypond_file.items.append(header)

        lilypond_file.items.extend(abjad_scores)

        return lilypond_file


class TimeBracketToAbjadScoreConverter(converters_abc.Converter):
    def __init__(
        self,
        main_instrument_index: int,
        sequential_event_to_abjad_voice_converter: mutwo_abjad.SequentialEventToAbjadVoiceConverter,
    ):
        self._sequential_event_to_abjad_voice_converter = (
            sequential_event_to_abjad_voice_converter
        )
        self._main_instrument_index = main_instrument_index

    def convert(
        self,
        instrument_indices_and_time_bracket_to_convert: typing.Tuple[
            typing.Tuple[typing.Tuple[int, ...], time_brackets.TimeBracket], ...
        ],
    ) -> abjad.Score:
        (
            instrument_indices,
            time_bracket,
        ) = instrument_indices_and_time_bracket_to_convert
        abjad_voices = [
            self._sequential_event_to_abjad_voice_converter.convert(sequential_event)
            for sequential_event in time_bracket
        ]
        abjad_score = abjad.Score(
            [abjad.Staff([abjad_voice]) for abjad_voice in abjad_voices]
        )
        return abjad_score
