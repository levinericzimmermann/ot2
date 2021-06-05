import unittest  # type: ignore

try:
    import quicktions as fractions  # type: ignore
except ImportError:
    import fractions  # type: ignore

import abjad  # type: ignore

from mutwo.events import basic
from mutwo.events import music

from ot2.converters.frontends import abjad as ot2_abjad
from ot2.constants import instruments
from ot2.events import basic as ot2_basic


class AbjadScoreToLilypondFileConverterTest(unittest.TestCase):
    def test_convert(self):
        musical_data = ot2_basic.TaggedSimultaneousEvent(
            [
                basic.SimultaneousEvent(
                    [
                        basic.SequentialEvent(
                            [
                                music.NoteLike("1/1", 1, "pp"),
                                music.NoteLike("15/16", 1, "pp"),
                                music.NoteLike([], 0.5, "pp"),
                                music.NoteLike("16/15", 0.75, "p"),
                                music.NoteLike([], 1.25, "p"),
                                music.NoteLike("9/8", 1.5, "p"),
                            ]
                        )
                    ]
                ),
                basic.SimultaneousEvent(
                    [
                        basic.SequentialEvent(
                            [
                                music.NoteLike("5/8", 0.5, "pp"),
                                music.NoteLike("11/16", 1, "pp"),
                                music.NoteLike([], 1, "pp"),
                                music.NoteLike("3/4", 0.75, "p"),
                                music.NoteLike([], 0.25, "p"),
                                music.NoteLike("3/4", 0.75, "p"),
                            ]
                        )
                    ]
                ),
                basic.SimultaneousEvent(
                    [
                        basic.SequentialEvent(
                            [
                                music.NoteLike([], 0.75, "pp"),
                                music.NoteLike("11/9", 1, "pp"),
                                music.NoteLike("4/3", 1, "pp"),
                                music.NoteLike("3/2", 0.75, "ppp"),
                                music.NoteLike([], 0.75, "ppp"),
                                music.NoteLike("3/5", 0.75, "ppp"),
                            ]
                        )
                    ]
                ),
                basic.SimultaneousEvent(
                    [
                        basic.SequentialEvent(
                            [
                                music.NoteLike("1/4", 4, "pp"),
                                music.NoteLike([], 1, "pp"),
                                music.NoteLike("1/4", 1, "pp"),
                            ]
                        ),
                        basic.SequentialEvent(
                            [
                                music.NoteLike([], 3, "pp"),
                                music.NoteLike("3/8", 2.5, "pp"),
                                music.NoteLike([], 0.5, "pp"),
                            ]
                        ),
                    ]
                ),
                basic.SimultaneousEvent(
                    [
                        basic.SequentialEvent(
                            [
                                music.NoteLike("g", 0.25, "pp"),
                                music.NoteLike("g", 0.5, "pp"),
                                music.NoteLike("g", 0.25, "pp"),
                                music.NoteLike("b", fractions.Fraction(1, 6), "pp"),
                                music.NoteLike("f", fractions.Fraction(1, 12), "pp"),
                                music.NoteLike("g", 1, "pp"),
                                music.NoteLike("f", 1, "pp"),
                                music.NoteLike("g", 1, "pp"),
                                music.NoteLike("g", 1, "pp"),
                            ]
                        )
                    ]
                ),
                basic.SimultaneousEvent(
                    [basic.SequentialEvent([music.NoteLike([], 6, "ppp")])]
                ),
            ],
            tag_to_event_index=instruments.INSTRUMENT_ID_TO_INDEX,
        )

        abjad_score_converter = ot2_abjad.TaggedSimultaneousEventToAbjadScoreConverter(
            (
                abjad.TimeSignature((4, 2)),
                abjad.TimeSignature((4, 2)),
                abjad.TimeSignature((4, 2)),
                abjad.TimeSignature((4, 2)),
            )
        )
        abjad_score = abjad_score_converter.convert(musical_data)

        lilypond_file_converter = ot2_abjad.AbjadScoreToLilypondFileConverter()
        lilypond_file = lilypond_file_converter.convert(abjad_score)

        abjad.persist.as_pdf(lilypond_file, "tests/converters/frontends/score_test.pdf")


if __name__ == "__main__":
    unittest.main()
