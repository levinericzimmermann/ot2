import unittest  # type: ignore

try:
    import quicktions as fractions  # type: ignore
except ImportError:
    import fractions  # type: ignore

import abjad  # type: ignore

from mutwo.events import basic
from mutwo.events import music
from mutwo.converters.frontends import abjad as mutwo_abjad

from ot2.events import time_brackets
from ot2.converters.frontends import abjad as ot2_abjad


class TimeBracketToAbjadScoreConverter(unittest.TestCase):
    def test_convert(self):
        time_bracket = time_brackets.TimeBracket(
            [
                basic.SequentialEvent(
                    [
                        music.NoteLike(p, r)
                        for p, r in zip(
                            "1/1 9/8 7/6 4/3 11/8 11/10 4/5".split(" "),
                            (
                                0.125,
                                0.25,
                                0.125,
                                fractions.Fraction(3, 10),
                                fractions.Fraction(1, 10),
                                fractions.Fraction(1, 10),
                                fractions.Fraction(2, 3),
                            ),
                        )
                    ]
                )
            ],
            (5, 15),
            (30, 35),
        )

        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter()
        )

        time_bracket_to_abjad_score_converter = ot2_abjad.TimeBracketToAbjadScoreConverter(
            0, sequential_event_to_abjad_voice_converter
        )

        abjad_score = time_bracket_to_abjad_score_converter.convert(
            ((0,), time_bracket)
        )
        # TODO(abstrahiere diese zwei zeilen irgendwo, in sowas wie "prepare_lilypond_file")
        abjad.attach(
            abjad.LilyPondLiteral(r'\accidentalStyle "dodecaphonic"'),
            abjad_score[0][0][0][0],
        )
        lilypond_file = abjad.LilyPondFile(
            items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
        )
        abjad.persist.as_pdf(lilypond_file, "test.pdf")
