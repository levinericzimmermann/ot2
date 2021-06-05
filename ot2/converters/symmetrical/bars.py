import itertools
import typing

from mutwo import converters
from mutwo.parameters import pitches

from ot2.events import bars
from ot2.generators import zimmermann
from ot2.generators import zimmermann_constants


class BarsToBarsWithHarmonyConverter(converters.abc.Converter):
    def convert(
        self, bars_to_convert: typing.Tuple[bars.Bar, ...]
    ) -> typing.Tuple[bars.BarWithHarmony, ...]:
        raise NotImplementedError()


class SymmetricalPermutationBasedBarsToBarsWithHarmonyConverter(
    BarsToBarsWithHarmonyConverter
):
    def __init__(self, symmetrical_permutation: zimmermann.SymmetricalPermutation):
        self._symmetrical_permutation = symmetrical_permutation

    @staticmethod
    def _link_each_bar_to_harmony_id(
        bars_to_convert: typing.Tuple[bars.Bar, ...]
    ) -> typing.Tuple[str, ...]:
        cycle = itertools.cycle(
            (
                zimmermann_constants.OTONAL_HARMONY_NAME,
                zimmermann_constants.F_OTONAL_HARMONY_NAME,
                zimmermann_constants.UTONAL_HARMONY_NAME,
                zimmermann_constants.F_UTONAL_HARMONY_NAME,
            )
        )
        return tuple(next(cycle) for _ in bars_to_convert)

    def _make_pitch_weigth_pairs_per_beat(
        self,
        harmony0: typing.Tuple[pitches.JustIntonationPitch, ...],
        harmony1: typing.Tuple[pitches.JustIntonationPitch, ...],
        connection_pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        previous_connection_pitches: typing.Optional[
            typing.Tuple[pitches.JustIntonationPitch, ...]
        ],
        bar: bars.Bar,
    ) -> typing.Tuple[
        typing.Tuple[
            typing.Tuple[typing.Tuple[pitches.JustIntonationPitch, float], ...], ...
        ]
    ]:
        # TODO(add pitch weight pairs)
        pitch_weigth_pairs_per_beat = [[] for _ in bar[1]]
        return tuple(
            tuple(pitch_weight_pairs)
            for pitch_weight_pairs in pitch_weigth_pairs_per_beat
        )

    def _make_harmony_grid_positions_pairs(
        self,
        harmony0: typing.Tuple[pitches.JustIntonationPitch, ...],
        connection_pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        bar: bars.Bar,
    ) -> typing.Tuple[
        typing.Tuple[
            typing.Tuple[pitches.JustIntonationPitch, ...], typing.Tuple[int, ...]
        ],
        ...,
    ]:
        harmony0_until_nth_grid_position = bar[1].absolute_times.index(
            bar[0].absolute_times[-1]
        )
        return (
            (harmony0, tuple(range(0, harmony0_until_nth_grid_position))),
            (
                connection_pitches,
                tuple(range(harmony0_until_nth_grid_position, len(bar[1]))),
            ),
        )

    def _get_pitch_data(
        self,
        harmony0: typing.Tuple[pitches.JustIntonationPitch, ...],
        harmony1: typing.Tuple[pitches.JustIntonationPitch, ...],
        connection_pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        previous_connection_pitches: typing.Optional[
            typing.Tuple[pitches.JustIntonationPitch, ...]
        ],
        bar: bars.Bar,
    ) -> typing.Tuple[
        typing.Tuple[
            typing.Tuple[typing.Tuple[pitches.JustIntonationPitch, float], ...], ...
        ],
        typing.Tuple[
            typing.Tuple[
                typing.Tuple[pitches.JustIntonationPitch, ...], typing.Tuple[int, ...]
            ],
            ...,
        ],
    ]:
        return (
            self._make_pitch_weigth_pairs_per_beat(
                harmony0, harmony1, connection_pitches, previous_connection_pitches, bar
            ),
            self._make_harmony_grid_positions_pairs(harmony0, connection_pitches, bar),
        )

    def convert(
        self, bars_to_convert: typing.Tuple[bars.Bar, ...]
    ) -> typing.Tuple[bars.BarWithHarmony, ...]:

        harmony_id_per_bar = self._link_each_bar_to_harmony_id(bars_to_convert)

        previous_connection_pitches = None
        bars_with_harmony = []
        for harmony_id0, harmony_id1, bar in zip(
            harmony_id_per_bar, harmony_id_per_bar[1:], bars_to_convert
        ):
            harmony0 = self._symmetrical_permutation.harmonies[harmony_id0]
            harmony1 = self._symmetrical_permutation.harmonies[harmony_id1]
            connection_pitches = self._symmetrical_permutation.connections[
                (harmony_id0, harmony_id1)
            ]
            (
                pitch_weigth_pairs_per_beat,
                harmony_grid_positions_pairs,
            ) = self._get_pitch_data(
                harmony0, harmony1, connection_pitches, previous_connection_pitches, bar
            )
            time_signature, subdivisions, grid = (
                bar.time_signature,
                bar[0].get_parameter("duration"),
                bar[1].get_parameter("duration"),
            )
            bar_with_harmony = bars.BarWithHarmony(
                time_signature,
                subdivisions,
                grid,
                pitch_weigth_pairs_per_beat,
                harmony_grid_positions_pairs,
            )
            bars_with_harmony.append(bar_with_harmony)
            previous_connection_pitches = connection_pitches

        return tuple(bars_with_harmony)
