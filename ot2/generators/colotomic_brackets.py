import itertools
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.constants import instruments
from ot2.events import basic as ot2_basic
from ot2.events import colotomic_brackets


class DingDongUnit(object):
    def __init__(
        self,
        pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        colotomic_indicators: typing.Tuple[
            colotomic_brackets.ColotomicElementIndicator, ...
        ],
    ):
        self.pitches = pitches
        self.colotomic_indicators = colotomic_indicators


class ClearDingDongUnit(DingDongUnit):
    def __init__(
        self,
        pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        colotomic_indicators: typing.Tuple[
            colotomic_brackets.ColotomicElementIndicator, ...
        ],
        quality: bool,
        root: pitches.JustIntonationPitch,
    ):
        self.quality = quality
        self.root = root
        super().__init__(pitches, colotomic_indicators)


class BlurryDingDongUnit(DingDongUnit):
    def __init__(
        self,
        pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        colotomic_indicators: typing.Tuple[
            colotomic_brackets.ColotomicElementIndicator, ...
        ],
        quality0: bool,
        quality1: bool,
        connection_pitch: pitches.JustIntonationPitch,
    ):
        self.quality0 = quality0
        self.quality1 = quality1
        self.connection_pitch = connection_pitch
        super().__init__(pitches, colotomic_indicators)


class HoquetusDingDong(object):
    def __init__(
        self,
        prime_per_unit: typing.Tuple[int, ...],
        colotomic_pattern_maker: typing.Callable[
            [], colotomic_brackets.ColotomicPattern
        ],
        tonality: bool = True,
        modulation_pitch: pitches.JustIntonationPitch = pitches.JustIntonationPitch(),
        n_colotomic_elements_for_main_prime: int = 3,
        n_colotomic_elements_for_side_prime: int = 2,
        n_colotomic_elements_for_blurry_zone: int = 1,
        n_tones_for_main_prime: int = 3,
        n_tones_for_side_prime: int = 2,
        nth_sustaining_instrument_makes_drone_support: int = 0,
        positive_pitches_per_units: typing.Tuple[pitches.JustIntonationPitch, ...] = (
            pitches.JustIntonationPitch(),
            pitches.JustIntonationPitch("9/8"),
            pitches.JustIntonationPitch("5/4"),
            pitches.JustIntonationPitch("11/8"),
            pitches.JustIntonationPitch("3/2"),
            pitches.JustIntonationPitch("7/4"),
        ),
    ):
        self._prime_per_unit = prime_per_unit
        self._colotomic_pattern_maker = colotomic_pattern_maker
        self._tonality = tonality
        self._modulation_pitch = modulation_pitch
        self._n_colotomic_elements_for_main_prime = n_colotomic_elements_for_main_prime
        self._n_colotomic_elements_for_side_prime = n_colotomic_elements_for_side_prime
        self._n_colotomic_elements_for_blurry_zone = (
            n_colotomic_elements_for_blurry_zone
        )
        self._n_tones_for_main_prime = n_tones_for_main_prime
        self._n_tones_for_side_prime = n_tones_for_side_prime
        self._nth_sustaining_instrument_makes_drone_support = (
            nth_sustaining_instrument_makes_drone_support
        )
        self._positive_pitches_per_unit = positive_pitches_per_units
        self._negative_pitches_per_unit = tuple(
            pitch.inverse(mutate=False) for pitch in self._positive_pitches_per_unit
        )

        self._colotomic_patterns = self._make_colotomic_pattern()
        self._ding_dong_units = self._make_ding_dong_units()

    # ######################################################## #
    #                     static methods                       #
    # ######################################################## #

    # ######################################################## #
    #                    private methods                       #
    # ######################################################## #

    def _increment_colotomic_element_indicator(
        self, colotomic_element_indicator: colotomic_brackets.ColotomicElementIndicator
    ) -> colotomic_brackets.ColotomicElementIndicator:
        colotomic_pattern = self._colotomic_patterns[colotomic_element_indicator[0]]
        if len(colotomic_pattern) > colotomic_element_indicator[2] + 1:
            return colotomic_element_indicator[:2] + (
                colotomic_element_indicator[2] + 1,
            )
        elif colotomic_pattern.n_repetitions > colotomic_element_indicator[1] + 1:
            return (
                colotomic_element_indicator[0],
                colotomic_element_indicator[1] + 1,
                0,
            )
        else:
            return (colotomic_element_indicator[0] + 1, 0, 0)

    def _make_colotomic_element_indicator_range(
        self,
        first_colotomic_element_indicator: colotomic_brackets.ColotomicElementIndicator,
        n_items: int,
    ) -> typing.Tuple[colotomic_brackets.ColotomicElementIndicator, ...]:
        colotomic_element_indicator_range = [first_colotomic_element_indicator]
        for _ in range(n_items - 1):
            colotomic_element_indicator_range.append(
                self._increment_colotomic_element_indicator(
                    colotomic_element_indicator_range[-1]
                )
            )
        return tuple(colotomic_element_indicator_range)

    def _make_colotomic_pattern(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicPattern]:
        n_units = len(self._prime_per_unit)
        n_side_units = n_units // 2
        n_main_units = n_side_units + (n_units % 2)
        n_needed_colotomic_elements = (
            (n_main_units * self._n_colotomic_elements_for_main_prime)
            + (n_side_units * self._n_colotomic_elements_for_side_prime)
            + ((n_units * self._n_colotomic_elements_for_blurry_zone) - 1)
        )

        colotomic_patterns = []
        n_colotomic_elements = 0
        while n_colotomic_elements < n_needed_colotomic_elements:
            new_pattern = self._colotomic_pattern_maker()
            n_colotomic_elements += len(new_pattern) * new_pattern.n_repetitions
            colotomic_patterns.append(new_pattern)

        return tuple(colotomic_patterns)

    def _make_pitches_for_clear_unit(
        self, quality: bool, prime: int
    ) -> typing.Tuple[
        typing.Tuple[pitches.JustIntonationPitch, ...], pitches.JustIntonationPitch
    ]:
        tonality = self._tonality if quality else not self._tonality

        if tonality:
            root = pitches.JustIntonationPitch("{}/1".format(prime))
            intervals = self._positive_pitches_per_unit
        else:
            root = pitches.JustIntonationPitch("1/{}".format(prime))
            intervals = self._negative_pitches_per_unit

        root.add(self._modulation_pitch)
        root.normalize()

        return tuple(interval + root for interval in intervals), root

    def _make_clear_unit(
        self,
        current_colotomic_element_indicator: colotomic_brackets.ColotomicElementIndicator,
        quality: bool,
        prime: int,
    ) -> typing.Tuple[ClearDingDongUnit, colotomic_brackets.ColotomicElementIndicator]:
        colotomic_element_indicator_range = self._make_colotomic_element_indicator_range(
            current_colotomic_element_indicator,
            (
                self._n_colotomic_elements_for_side_prime,
                self._n_colotomic_elements_for_main_prime,
            )[quality],
        )
        new_current_colotomic_element_indicator = self._increment_colotomic_element_indicator(
            colotomic_element_indicator_range[-1]
        )
        pitches, root = self._make_pitches_for_clear_unit(quality, prime)
        ding_dong_unit = ClearDingDongUnit(
            pitches, colotomic_element_indicator_range, quality, root
        )
        return ding_dong_unit, new_current_colotomic_element_indicator

    def _make_pitches_for_blurry_unit(
        self, quality: bool, prime0: int, prime1: int
    ) -> typing.Tuple[
        typing.Tuple[pitches.JustIntonationPitch, ...], pitches.JustIntonationPitch
    ]:
        tonality = self._tonality if quality else not self._tonality

        if tonality:
            root0 = pitches.JustIntonationPitch("{}/1".format(prime0))
            root1 = pitches.JustIntonationPitch("1/{}".format(prime1))
            connection_pitch = pitches.JustIntonationPitch(
                "{}/{}".format(prime0, prime1)
            )
        else:
            root0 = pitches.JustIntonationPitch("1/{}".format(prime0))
            root1 = pitches.JustIntonationPitch("{}/1".format(prime1))
            connection_pitch = pitches.JustIntonationPitch(
                "{}/{}".format(prime1, prime0)
            )

        blurry_pitches = (pitches.JustIntonationPitch(), root0, root1, connection_pitch)
        for pitch in blurry_pitches:
            pitch.add(self._modulation_pitch)
            pitch.normalize()

        return blurry_pitches, connection_pitch

    def _make_blurry_unit(
        self,
        current_colotomic_element_indicator: colotomic_brackets.ColotomicElementIndicator,
        quality: bool,
        prime0: int,
        prime1: int,
    ) -> typing.Tuple[BlurryDingDongUnit, colotomic_brackets.ColotomicElementIndicator]:
        colotomic_element_indicator_range = self._make_colotomic_element_indicator_range(
            current_colotomic_element_indicator,
            self._n_colotomic_elements_for_blurry_zone,
        )
        new_current_colotomic_element_indicator = self._increment_colotomic_element_indicator(
            colotomic_element_indicator_range[-1]
        )
        pitches, connection_pitch = self._make_pitches_for_blurry_unit(
            quality, prime0, prime1
        )
        ding_dong_unit = BlurryDingDongUnit(
            pitches,
            colotomic_element_indicator_range,
            quality,
            not quality,
            connection_pitch,
        )
        return ding_dong_unit, new_current_colotomic_element_indicator

    def _make_ding_dong_units(self) -> typing.Tuple[DingDongUnit, ...]:
        quality_cycle = itertools.cycle((True, False))
        ding_dong_units: typing.List[DingDongUnit] = []
        colotomic_element_indicator = 0, 0, 0
        for quality, current_prime, next_prime in zip(
            quality_cycle, self._prime_per_unit, self._prime_per_unit[1:],
        ):
            clear_unit, colotomic_element_indicator = self._make_clear_unit(
                colotomic_element_indicator, quality, current_prime
            )
            blurry_unit, colotomic_element_indicator = self._make_blurry_unit(
                colotomic_element_indicator, quality, current_prime, next_prime
            )
            ding_dong_units.append(clear_unit)
            ding_dong_units.append(blurry_unit)

        clear_unit, colotomic_element_indicator = self._make_clear_unit(
            colotomic_element_indicator, next(quality_cycle), self._prime_per_unit[-1]
        )
        ding_dong_units.append(clear_unit)

        return tuple(ding_dong_units)

    def _make_position_ranges_for_drone_brackets(
        self, nth_ding_dong_unit: int, current_ding_dong_unit: DingDongUnit
    ) -> typing.Tuple[
        typing.Tuple[
            colotomic_brackets.ColotomicElementIndicator,
            colotomic_brackets.ColotomicElementIndicator,
        ],
        typing.Tuple[
            colotomic_brackets.ColotomicElementIndicator,
            colotomic_brackets.ColotomicElementIndicator,
        ],
    ]:
        if nth_ding_dong_unit == 0:
            start_range = current_ding_dong_unit.colotomic_indicators[:2]
        else:
            start_range = (
                self._ding_dong_units[nth_ding_dong_unit - 1].colotomic_indicators[-1:]
                + current_ding_dong_unit.colotomic_indicators[:1]
            )

        try:
            next_ding_dong_unit = self._ding_dong_units[nth_ding_dong_unit + 1]
        except IndexError:
            next_ding_dong_unit = None

        if next_ding_dong_unit:
            end_range = (
                next_ding_dong_unit.colotomic_indicators[0],
                self._ding_dong_units[nth_ding_dong_unit + 2].colotomic_indicators[0],
            )
        else:
            end_range = current_ding_dong_unit.colotomic_indicators[-2:]

        return start_range, end_range

    def _make_colotomic_brackets_for_drone(
        self, start_index: int = 0, instrument: str = instruments.ID_DRONE
    ) -> typing.Tuple[colotomic_brackets.ColotomicBracket, ...]:
        drone_colotomic_brackets: typing.List[colotomic_brackets.ColotomicBracket] = []

        for nth_ding_dong_unit in range(start_index, len(self._ding_dong_units), 4):
            current_ding_dong_unit = self._ding_dong_units[nth_ding_dong_unit]
            start_range, end_range = self._make_position_ranges_for_drone_brackets(
                nth_ding_dong_unit, current_ding_dong_unit
            )

            colotomic_bracket = colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [
                            basic.SequentialEvent(
                                [music.NoteLike(current_ding_dong_unit.root, 1, "p")]
                            )
                        ],
                        instrument,
                    ),
                ),
                start_range,
                end_range,
            )

            drone_colotomic_brackets.append(colotomic_bracket)

        return tuple(drone_colotomic_brackets)

    def _make_colotomic_brackets_for_drone_support(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicBracket, ...]:
        return self._make_colotomic_brackets_for_drone(
            2,
            (instruments.ID_SUS0, instruments.ID_SUS1, instruments.ID_SUS2)[
                self._nth_sustaining_instrument_makes_drone_support
            ],
        )

    def _make_colotomic_brackets_for_hoquetus(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicBracket, ...]:
        return self._make_colotomic_brackets_for_drone(
            2, instruments.ID_SUS1,
        ) + self._make_colotomic_brackets_for_drone(2, instruments.ID_SUS2,)

    # ######################################################## #
    #                     public methods                       #
    # ######################################################## #

    def run(
        self,
    ) -> typing.Tuple[
        typing.Tuple[colotomic_brackets.ColotomicPattern, ...],
        typing.Tuple[colotomic_brackets.ColotomicBracket, ...],
    ]:
        new_colotomic_brackets = (
            self._make_colotomic_brackets_for_drone()
            + self._make_colotomic_brackets_for_drone_support()
            + self._make_colotomic_brackets_for_hoquetus()
        )
        return (
            self._colotomic_patterns,
            new_colotomic_brackets,
        )
