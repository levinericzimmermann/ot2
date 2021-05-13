import typing

from mutwo.events import music
from mutwo.parameters import tempos

from ot2.events import colotomic_brackets


def _make_patterns() -> typing.Tuple[colotomic_brackets.ColotomicPattern, ...]:
    pattern0 = colotomic_brackets.ColotomicPattern(
        [
            colotomic_brackets.ColotomicElement([music.NoteLike("f", 0.5)]),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 1)]),
            colotomic_brackets.ColotomicElement(
                [
                    music.NoteLike("f", 0.5),
                    music.NoteLike("f", 2 / 3),
                    music.NoteLike("f", 1 / 3),
                ]
            ),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 1.5)]),
        ],
        tempo=tempos.TempoPoint((50, 70)),
        time_signature=(3, 2),
        n_repetitions=6,
    )

    pattern0.set_parameter('volume', 'mp')

    pattern0[1][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
    pattern0[1][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)
    pattern0[3][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
    pattern0[3][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)

    return (pattern0,)


COLOTOMIC_PATTERNS = _make_patterns()
