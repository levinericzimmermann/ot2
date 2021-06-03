import itertools
import typing

try:
    import quicktions as fractions  # type: ignore
except ImportError:
    import fractions  # type: ignore

from mutwo.parameters import pitches

from ot2.generators import zimmermann_constants


class SymmetricalPermutation(object):
    """Make symmetrical otonalities / utonalities.

    :param k: The constant number.
    :param r: The varying numbers.

    This algorithm has been described in "Bewegungen im unendlichen
    Tonraum" [2018] by Levin Eric Zimmermann.
    """

    def __init__(self, k: int, r: typing.Sequence[int]):
        self._harmonies = SymmetricalPermutation._make_harmonies(k, r)
        self._connections = SymmetricalPermutation._make_connections(k, r)
        self._k = k
        self._r = r

    # ######################################################## #
    #                     static methods                       #
    # ######################################################## #

    @staticmethod
    def _make_harmonies(
        k: int, r: typing.Sequence[int]
    ) -> typing.Dict[str, typing.Tuple[pitches.JustIntonationPitch, ...]]:
        harmonies = {}
        for exponent_k, exponent_r, name in (
            (1, 1, zimmermann_constants.OTONAL_HARMONY_NAME),
            (-1, -1, zimmermann_constants.UTONAL_HARMONY_NAME),
            (-1, 1, zimmermann_constants.F_OTONAL_HARMONY_NAME),
            (1, -1, zimmermann_constants.F_UTONAL_HARMONY_NAME),
        ):
            harmony = []
            k_pitch = pitches.JustIntonationPitch(
                fractions.Fraction(k ** exponent_k).limit_denominator(k)
            )
            for prime_number in r:
                r_pitch = pitches.JustIntonationPitch(
                    fractions.Fraction(prime_number ** exponent_r).limit_denominator(
                        prime_number
                    )
                )
                harmony.append(r_pitch + k_pitch)
                harmonies.update({name: tuple(harmony)})

        return harmonies

    @staticmethod
    def _make_connections(
        k: int, r: typing.Sequence[int]
    ) -> typing.Dict[
        typing.Tuple[str, str], typing.Tuple[pitches.JustIntonationPitch, ...]
    ]:
        connections = {}

        connection_pitches_0 = (pitches.JustIntonationPitch("{}/1".format(k)),)
        connection_pitches_1 = (pitches.JustIntonationPitch("1/{}".format(k)),)
        connection_pitches_2 = tuple(
            pitches.JustIntonationPitch("{}/1".format(prime)) for prime in r
        )
        connection_pitches_3 = tuple(
            pitches.JustIntonationPitch("1/{}".format(prime)) for prime in r
        )

        for harmony0, harmony1, connection_pitches in (
            (
                zimmermann_constants.OTONAL_HARMONY_NAME,
                zimmermann_constants.F_UTONAL_HARMONY_NAME,
                connection_pitches_0,
            ),
            (
                zimmermann_constants.UTONAL_HARMONY_NAME,
                zimmermann_constants.F_OTONAL_HARMONY_NAME,
                connection_pitches_1,
            ),
            (
                zimmermann_constants.OTONAL_HARMONY_NAME,
                zimmermann_constants.F_OTONAL_HARMONY_NAME,
                connection_pitches_2,
            ),
            (
                zimmermann_constants.UTONAL_HARMONY_NAME,
                zimmermann_constants.F_UTONAL_HARMONY_NAME,
                connection_pitches_3,
            ),
        ):
            connections.update({(harmony0, harmony1): connection_pitches})
            connections.update({(harmony1, harmony0): connection_pitches})

        return connections

    # ######################################################## #
    #                       properties                         #
    # ######################################################## #

    @property
    def k(self) -> int:
        return self._k

    @property
    def r(self) -> typing.Sequence[int]:
        return self._r

    @property
    def harmonies(
        self,
    ) -> typing.Dict[str, typing.Tuple[pitches.JustIntonationPitch, ...]]:
        return self._harmonies

    @property
    def connections(
        self,
    ) -> typing.Dict[
        typing.Tuple[str, str], typing.Tuple[pitches.JustIntonationPitch, ...]
    ]:
        return self._connections


def make_nested_loop(*loop: typing.Sequence[int]) -> typing.Tuple:
    """Build nested loops from loop durations.

    :param loop: Loops of durations which indicate how often
        items of the next level shall be repeated. From outer level
        to inner level.
    :type loop: typing.Sequence[int]

    **Example:**

    >>> from ot2.generators import zimmermann
    >>> nested_loop = make_nested_loop((3, 2), (2, 2, 1))
    >>> nested_loop.get_parameter('duration')
    ((2, 2, 1), (2, 2), (1, 2, 2), (1, 2), (2, 1, 2), (2, 1))

    The function repeat loops until all loops are back to their
    start position.
    """

    try:
        assert len(loop) >= 1
    except AssertionError:
        message = "Found only {} loops ({}). Please provide at least two loops!".format(
            len(loop), loop
        )
        raise ValueError(message)

    class Looper(object):
        def __init__(self, *item: int):
            self._loop = itertools.cycle(item)
            self._position = itertools.cycle(range(len(item)))
            self._current_position = 0

        def __next__(self):
            self._current_position = next(self._position)
            return next(self._loop)

        @property
        def position(self) -> int:
            return self._current_position

    loopers = tuple(Looper(*lo) for lo in loop)

    @typing.overload
    def build_loop(n_times: int, loopers: None) -> int:
        ...

    @typing.overload
    def build_loop(n_times: int, loopers: typing.Tuple[Looper, ...]) -> typing.Tuple:
        ...

    def build_loop(
        n_times: int, loopers: typing.Optional[typing.Tuple[Looper, ...]]
    ) -> typing.Union[typing.Tuple, int]:
        if not loopers:
            return n_times
        else:
            loops = []
            for _ in range(n_times):
                remaining = loopers[1:]
                if not remaining:
                    remaining = None
                loops.append(build_loop(next(loopers[0]), loopers[1:]))
            return tuple(loops)

    loops = []
    loops.append(build_loop(next(loopers[0]), loopers[1:]))
    while any(looper.position != 0 for looper in loopers):
        loops.append(build_loop(next(loopers[0]), loopers[1:]))
    return tuple(loops)
