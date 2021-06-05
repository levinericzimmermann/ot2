import functools
import operator
import typing

try:
    import quicktions as fractions
except ImportError:
    import fractions

from mutwo.events import basic
from mutwo.parameters import pitches


class Bar(basic.SimultaneousEvent[basic.SequentialEvent[basic.SimpleEvent]]):
    def __init__(
        self,
        time_signature: typing.Tuple[int, int],
        subdivisions: typing.Tuple[fractions.Fraction, ...],
        grid: typing.Tuple[fractions.Fraction, ...],
    ):
        self._time_signature = time_signature
        subdivisions = basic.SequentialEvent(
            [basic.SimpleEvent(subdivision) for subdivision in subdivisions]
        )
        grid = basic.SequentialEvent([basic.SimpleEvent(size) for size in grid])
        super().__init__((subdivisions, grid))

    def __repr__(self) -> str:
        return "Bar({})".format(self.time_signature[0])

    @property
    def time_signature(self) -> typing.Tuple[int, int]:
        return self._time_signature


class BarWithHarmony(Bar):
    def __init__(
        self,
        time_signature: typing.Tuple[int, int],
        subdivisions: typing.Tuple[fractions.Fraction, ...],
        grid: typing.Tuple[fractions.Fraction, ...],
        pitch_weigth_pairs_per_beat: typing.Tuple[
            typing.Tuple[typing.Tuple[pitches.JustIntonationPitch, float], ...],...
        ],
        harmony_grid_positions_pairs: typing.Tuple[
            typing.Tuple[
                typing.Tuple[pitches.JustIntonationPitch, ...], typing.Tuple[int, ...]
            ],
            ...,
        ],
    ):
        super().__init__(time_signature, subdivisions, grid)
        self._pitch_weigth_pairs_per_beat = pitch_weigth_pairs_per_beat
        self._harmony_grid_positions_pairs = harmony_grid_positions_pairs

    @property
    def pitch_weigth_pairs_per_beat(
        self,
    ) -> typing.Tuple[typing.Tuple[pitches.JustIntonationPitch, float], ...]:
        return self._pitch_weigth_pairs_per_beat

    @property
    def harmony_grid_positions_pairs(
        self,
    ) -> typing.Tuple[
        typing.Tuple[
            typing.Tuple[pitches.JustIntonationPitch, ...], typing.Tuple[int, ...]
        ],
        ...,
    ]:
        return self._harmony_grid_positions_pairs

    @property
    def harmonies(
        self,
    ) -> typing.Tuple[typing.Tuple[pitches.JustIntonationPitch, ...], ...]:
        return tuple(harmony for harmony, _ in self._harmony_grid_positions_pairs)

    @property
    def harmony_per_beat(
        self,
    ) -> typing.Tuple[typing.Tuple[pitches.JustIntonationPitch, ...], ...]:
        return functools.reduce(
            operator.add,
            (
                tuple(harmony for _ in range(len(grid_positions)))
                for harmony, grid_positions in self.harmony_grid_positions_pairs
            ),
        )
