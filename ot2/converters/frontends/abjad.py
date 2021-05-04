import typing

import abjad  # type: ignore

from mutwo.converters import abc as converters_abc
from mutwo.converters.frontends import abjad as mutwo_abjad

from ot2.events import time_brackets


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
