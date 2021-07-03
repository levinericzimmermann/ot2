import fractions
import itertools
import typing

from mutwo.events import basic
from mutwo.generators import gray


def make_rhythms(
    a: typing.Tuple[fractions.Fraction, fractions.Fraction],
    b: typing.Tuple[fractions.Fraction, fractions.Fraction],
    c: typing.Tuple[fractions.Fraction, fractions.Fraction],
    d: typing.Tuple[fractions.Fraction, fractions.Fraction],
    is_inversed: bool = False,
) -> typing.Dict[int, basic.SequentialEvent[basic.SimpleEvent]]:
    if is_inversed:
        a = tuple(reversed(a))
        b = tuple(reversed(b))
        c = tuple(reversed(c))
        d = tuple(reversed(d))

    rhythms = {
        2: basic.SequentialEvent(
            [basic.SimpleEvent(fractions.Fraction(1, 4)) for _ in range(4)]
        ),
        4: basic.SequentialEvent(
            [
                basic.SimpleEvent(duration)
                for duration in (
                    (fractions.Fraction(1, 4),)
                    + a
                    + (fractions.Fraction(1, 4), fractions.Fraction(1, 4))
                    + tuple(reversed(a))
                    + (fractions.Fraction(1, 4),)
                )
            ]
        ),
        8: basic.SequentialEvent(
            [
                basic.SimpleEvent(duration)
                for duration in (
                    (fractions.Fraction(1, 4),)
                    + b
                    + c
                    + d
                    + (fractions.Fraction(1, 4), fractions.Fraction(1, 4))
                    + tuple(reversed(d))
                    + tuple(reversed(c))
                    + tuple(reversed(b))
                    + (fractions.Fraction(1, 4),)
                )
            ]
        ),
    }
    return rhythms


_VALID_RHYTHMS = (
    # a
    (
        (fractions.Fraction(3, 8), fractions.Fraction(1, 8)),
        (fractions.Fraction(1, 3), fractions.Fraction(1, 6)),
    ),
    # b
    (
        (fractions.Fraction(3, 8), fractions.Fraction(1, 8)),
        (fractions.Fraction(1, 3), fractions.Fraction(1, 6)),
    ),
    # c
    (
        (fractions.Fraction(1, 8), fractions.Fraction(3, 8)),
        (fractions.Fraction(1, 6), fractions.Fraction(1, 3)),
    ),
    # d
    (
        (fractions.Fraction(3, 8), fractions.Fraction(1, 8)),
        (fractions.Fraction(1, 3), fractions.Fraction(1, 6)),
    ),
)
RHYTHMS = tuple(
    make_rhythms(
        *tuple(
            _VALID_RHYTHMS[nth_item][index] for nth_item, index in enumerate(graycode)
        ),
        is_inversed=is_inversed
    )
    for is_inversed, graycode in zip(
        itertools.cycle((False, True)), gray.reflected_binary_code(4, 2)
    )
)
