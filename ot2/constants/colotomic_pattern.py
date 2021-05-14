import typing

from mutwo.events import music
from mutwo.parameters import tempos

from ot2.events import colotomic_brackets


def _make_patterns() -> typing.Tuple[colotomic_brackets.ColotomicPattern, ...]:
    pattern0 = colotomic_brackets.ColotomicPattern(
        [
            colotomic_brackets.ColotomicElement([music.NoteLike("f", 0.75)]),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
            colotomic_brackets.ColotomicElement(
                [
                    music.NoteLike("f", 0.5),
                    music.NoteLike("f", 2 / 3),
                    music.NoteLike("f", 1 / 3),
                ]
            ),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
        ],
        tempo=tempos.TempoPoint((70, 90)),
        time_signature=(3, 4),
        n_repetitions=4,
    )

    pattern0.set_parameter("volume", "mp")

    pattern0[1][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
    pattern0[1][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)
    pattern0[3][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
    pattern0[3][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)

    pattern1 = colotomic_brackets.ColotomicPattern(
        [
            colotomic_brackets.ColotomicElement(
                [
                    music.NoteLike("f", 0.5),
                    music.NoteLike("f", 2 / 3),
                    music.NoteLike("f", 1 / 3),
                ]
            ),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
            colotomic_brackets.ColotomicElement(
                [music.NoteLike("g", 0.75), music.NoteLike("f", 0.75)]
            ),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
        ],
        tempo=tempos.TempoPoint((60, 80)),
        time_signature=(3, 4),
        n_repetitions=6,
    )

    pattern1.set_parameter("volume", "mf")

    pattern1[1][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
    pattern1[1][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)
    pattern1[3][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
    pattern1[3][0].playing_indicators.explicit_fermata.waiting_range = (5, 15)

    return (pattern0, pattern1)


COLOTOMIC_PATTERNS = _make_patterns()
