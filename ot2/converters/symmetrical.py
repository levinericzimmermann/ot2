from mutwo.converters import abc as converters_abc
from mutwo.events import basic

from ot2.events import time_brackets


class TimeBracketsToSequentialEventConverter(converters_abc.Converter):
    def __init__(self, instrument_index: int):
        self._instrument_index = instrument_index

    def convert(
        self,
        instrument_indices_and_time_bracket_pairs: typing.Tuple[
            [int, time_brackets.TimeBracket], ...
        ],
    ) -> basic.SequentialEvent[basic.SimpleEvent]:
        pass
