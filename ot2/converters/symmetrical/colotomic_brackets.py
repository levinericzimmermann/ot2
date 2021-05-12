from mutwo.events import basic
from mutwo.events import music

from mutwo.converters import abc

from ot2.events import colotomic_brackets


class ColotomicPatternToNestedSequentialEventConverter(abc.Converter):
    def _convert_colotomic_pattern(
        self, colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern
    ) -> basic.SequentialEvent[basic.SequentialEvent[music.NoteLike]]:
        pass

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
