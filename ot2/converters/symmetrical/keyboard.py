"""Convert keyboard time brackets from sounding pitches to written pitches (tabulature).

Furthermore the respective converter builds .json files for setting up the keyboard
synth patch for live playing.
"""

import abc
import bisect
import dataclasses
import functools
import itertools
import operator
import json
import typing

import ranges

from mutwo import converters
from mutwo import events
from mutwo import generators

# from mutwo import generators
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import parameters as ot2_parameters

from ot2.converters.symmetrical import keyboard_constants


@dataclasses.dataclass(frozen=True)
class PatchNote(object):
    sounding_just_intonation_pitch: parameters.pitches.JustIntonationPitch
    sounding_midi_note: int
    sounding_midi_pitch_bending: int
    written_pitch: parameters.pitches.WesternPitch
    played_midi_note: int
    keyboard_engine_id: int


class Patch(typing.Tuple[PatchNote, ...]):
    def __init__(self, *_):
        super().__init__()
        self._just_intonation_pitch_as_exponent_to_patch_note = {
            patch_note.sounding_just_intonation_pitch.exponents: patch_note
            for patch_note in self
        }

    def __repr__(self):
        return "KeyboardPatch({})".format(super().__repr__()[:50])

    def save(self, path: str):
        data = {
            str(patch_note.played_midi_note): [
                patch_note.sounding_midi_note,
                patch_note.sounding_midi_pitch_bending,
                patch_note.keyboard_engine_id,
            ]
            for patch_note in self
        }
        with open(path, "w") as f:
            f.write(json.dumps(data))

    def apply(
        self,
        pitch_or_pitches: typing.Optional[
            typing.List[parameters.pitches.JustIntonationPitch]
        ],
    ) -> typing.Optional[typing.List[parameters.pitches.WesternPitch]]:
        if pitch_or_pitches:
            return [
                self._just_intonation_pitch_as_exponent_to_patch_note[
                    pitch.exponents
                ].written_pitch
                for pitch in pitch_or_pitches
            ]
        else:
            return pitch_or_pitches


PitchIndex = int


class AppearingPitchesAndHandPairsDivisionStrategy(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[tuple[PitchIndex, parameters.pitches.JustIntonationPitch], ...]:
        raise NotImplementedError


class ByHandsDivisionStrategy(AppearingPitchesAndHandPairsDivisionStrategy):
    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[tuple[PitchIndex, parameters.pitches.JustIntonationPitch], ...]:
        hands = {"left": [], "right": []}
        for nth_pitch, pitch_and_hand in enumerate(appearing_pitches_and_hand_pairs):
            pitch, hand = pitch_and_hand
            hands[hand].append((nth_pitch, pitch))
        return (tuple(hands["left"]), tuple(hands["right"]))


class ByPitchDivisionStrategy(AppearingPitchesAndHandPairsDivisionStrategy):
    def __init__(self, division_pitch: parameters.pitches.JustIntonationPitch):
        self._division_pitch = division_pitch

    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[tuple[PitchIndex, parameters.pitches.JustIntonationPitch], ...]:
        hands = [], []
        for nth_pitch, pitch_and_hand in enumerate(appearing_pitches_and_hand_pairs):
            pitch, _ = pitch_and_hand
            hands[pitch > self._division_pitch].append((nth_pitch, pitch))
        return tuple(tuple(index_and_pitch_pairs) for index_and_pitch_pairs in hands)


class EngineDistributionPartStrategy(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        index_and_pitch_pairs: tuple[
            tuple[PitchIndex, parameters.pitches.JustIntonationPitch], ...
        ],
    ) -> tuple[int, ...]:
        raise NotImplementedError


class SimpleEngineDistributionPartStrategy(EngineDistributionPartStrategy):
    def __init__(self, engine: int):
        self.engine = engine

    def __call__(
        self,
        index_and_pitch_pairs: tuple[
            tuple[PitchIndex, parameters.pitches.JustIntonationPitch], ...
        ],
    ) -> tuple[int, ...]:
        return tuple(self.engine for _ in index_and_pitch_pairs)


class ByActivityLevelDistributionPartStrategy(EngineDistributionPartStrategy):
    """ByActivityLevelDistributionPartStrategy

    when activity_level returns 0 -> engine 0,
    when activity_level retunrs 1 -> engine 1
    """

    def __init__(self, engine0: int, engine1: int, activity_level: int):
        self.engine0 = engine0
        self.engine1 = engine1
        self.activity_level = activity_level
        self.activity_level_maker = generators.edwards.ActivityLevel()

    def __call__(
        self,
        index_and_pitch_pairs: tuple[
            tuple[PitchIndex, parameters.pitches.JustIntonationPitch], ...
        ],
    ) -> tuple[int, ...]:
        return tuple(
            (self.engine0, self.engine1)[self.activity_level_maker(self.activity_level)]
            for _ in index_and_pitch_pairs
        )


class EngineDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[int, ...]:
        raise NotImplementedError


class SimpleEngineDistributionStrategy(EngineDistributionStrategy):
    def __init__(self, engine: int = 0):
        self.engine = engine

    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[int, ...]:
        return tuple([self.engine] * len(appearing_pitches_and_hand_pairs))


class ComplexEngineDistributionStrategy(EngineDistributionStrategy):
    def __init__(
        self,
        division_strategy: AppearingPitchesAndHandPairsDivisionStrategy,
        distribution_strategies: tuple[EngineDistributionPartStrategy, ...],
    ):
        self.division_strategy = division_strategy
        self.distribution_strategies = distribution_strategies

    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[int, ...]:
        divided_pitches = self.division_strategy(appearing_pitches_and_hand_pairs)
        engine_per_pitch = [None for _ in appearing_pitches_and_hand_pairs]
        for part, part_distibution in zip(
            divided_pitches, self.distribution_strategies
        ):
            local_engine_per_pitch = part_distibution(part)
            for engine, index_and_pitch in zip(local_engine_per_pitch, part):
                index, _ = index_and_pitch
                engine_per_pitch[index] = engine
        assert all((engine is not None for engine in engine_per_pitch))
        return tuple(engine_per_pitch)


class PitchDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
        sounding_midi_data_per_pitch: typing.Sequence[tuple[int, int]],
    ) -> tuple[int, ...]:
        raise NotImplementedError


class OldDiatonicPitchDistributionStrategy(PitchDistributionStrategy):
    def __init__(self, minimize_distance_between_pitches_factor: float = 1):
        self._minimize_distance_between_pitches_factor = (
            minimize_distance_between_pitches_factor
        )

    def _find_distances_between_pitches(
        self, sounding_midi_pitch_numbers: typing.Tuple[int, ...]
    ) -> typing.Tuple[typing.Tuple[int, ...], bool, bool]:
        distance_between_pitches = []
        for sounding_midi_pitch_number0, sounding_midi_pitch_number1 in zip(
            sounding_midi_pitch_numbers, sounding_midi_pitch_numbers[1:]
        ):
            distance_between_pitches.append(
                sounding_midi_pitch_number1 - sounding_midi_pitch_number0
            )

        add_lowest_border = False
        if sounding_midi_pitch_numbers[0] > keyboard_constants.LOWEST_ALLOWED_MIDI_NOTE:
            distance_between_pitches.insert(
                0,
                sounding_midi_pitch_numbers[0]
                - keyboard_constants.LOWEST_ALLOWED_MIDI_NOTE,
            )
            add_lowest_border = True

        add_highest_border = False
        if (
            sounding_midi_pitch_numbers[-1]
            < keyboard_constants.HIGHEST_ALLOWED_MIDI_NOTE
        ):
            distance_between_pitches.append(
                keyboard_constants.HIGHEST_ALLOWED_MIDI_NOTE
                - sounding_midi_pitch_numbers[-1]
            )
            add_highest_border = True

        return tuple(distance_between_pitches), add_lowest_border, add_highest_border

    def _find_used_diatonic_keys_indices(
        self,
        n_free_diatonic_pitches: int,
        distance_between_pitches: typing.Tuple[int, ...],
        add_lowest_border: bool,
        add_highest_border: bool,
    ) -> typing.Tuple[int, ...]:
        summed_distance_between_pitches = sum(distance_between_pitches)
        n_keys_distance_between_pitches = [
            int((distance / summed_distance_between_pitches) * n_free_diatonic_pitches)
            for distance in distance_between_pitches
        ]

        difference_between_actual_and_suggested_free_diatonic_pitches = (
            n_free_diatonic_pitches - sum(n_keys_distance_between_pitches)
        )

        """
        # may be better to omit
        for index, n_more_keys in enumerate(
            generators.toussaint.euclidean(
                difference_between_actual_and_suggested_free_diatonic_pitches,
                len(n_keys_distance_between_pitches),
            )
        ):
            if n_more_keys:
                n_keys_distance_between_pitches[index] += n_more_keys
        """

        used_diatonic_keys_indices = [0]
        for n_keys_distance in n_keys_distance_between_pitches:
            used_diatonic_keys_indices.append(
                used_diatonic_keys_indices[-1] + n_keys_distance + 1
            )

        if add_lowest_border:
            used_diatonic_keys_indices = used_diatonic_keys_indices[1:]

        if add_highest_border:
            used_diatonic_keys_indices = used_diatonic_keys_indices[:-1]

        return tuple(used_diatonic_keys_indices)

    def _adjust_distances_between_pitches(
        self,
        distance_between_pitches: typing.Tuple[int, ...],
        add_lowest_border: bool,
        add_highest_border: bool,
    ) -> typing.Tuple[int]:
        if self._minimize_distance_between_pitches_factor != 1:
            adjusted_distance_between_pitches = list(distance_between_pitches)
            adjust_range = [0, len(adjusted_distance_between_pitches)]
            if add_lowest_border:
                adjust_range[0] += 1
            if add_highest_border:
                adjust_range[1] -= 1
            for nth_distance in range(*adjust_range):
                adjusted_distance_between_pitches[
                    nth_distance
                ] *= self._minimize_distance_between_pitches_factor

            return tuple(adjusted_distance_between_pitches)
        else:
            return distance_between_pitches

    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
        sounding_midi_data_per_pitch: typing.Sequence[tuple[int, int]],
    ) -> tuple[int, ...]:
        appearing_pitches, _ = zip(*appearing_pitches_and_hand_pairs)
        n_appearing_pitches = len(appearing_pitches)
        n_diatonic_pitches = len(keyboard_constants.DIATONIC_PITCHES)
        n_free_diatonic_pitches = n_diatonic_pitches - n_appearing_pitches

        if n_free_diatonic_pitches > 0:
            sounding_midi_pitch_numbers, _ = zip(*sounding_midi_data_per_pitch)

            (
                distance_between_pitches,
                add_lowest_border,
                add_highest_border,
            ) = self._find_distances_between_pitches(sounding_midi_pitch_numbers)

            distance_between_pitches = self._adjust_distances_between_pitches(
                distance_between_pitches, add_lowest_border, add_highest_border
            )

            used_diatonic_keys_indices = self._find_used_diatonic_keys_indices(
                n_free_diatonic_pitches,
                distance_between_pitches,
                add_lowest_border,
                add_highest_border,
            )

            used_diatonic_keys = tuple(
                keyboard_constants.DIATONIC_PITCHES[diatonic_key_index]
                for diatonic_key_index in used_diatonic_keys_indices
            )

            return used_diatonic_keys
        else:
            return tuple(keyboard_constants.DIATONIC_PITCHES)


class OldChromaticPitchDistributionStrategy(PitchDistributionStrategy):
    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
        _: typing.Sequence[tuple[int, int]],
    ) -> tuple[int, ...]:
        appearing_pitches, _ = zip(*appearing_pitches_and_hand_pairs)
        # einfach erst alle weisse tasten verteilen, dann stueck fuer stueck im quintenzirkel aufgehen
        # und immer neue chromatische toene hinzufuegen, also erst alle f-sharp, dann, c-sharp, usw.
        missing_chromatic_pitches = len(appearing_pitches) - len(
            keyboard_constants.DIATONIC_PITCHES
        )
        return sorted(
            keyboard_constants.DIATONIC_PITCHES
            + keyboard_constants.CHROMATIC_PITCHES[:missing_chromatic_pitches]
        )


class HandBasedPitchDistributionStrategy(PitchDistributionStrategy):
    def __init__(
        self,
        chroma: int = 1,
        available_keys: tuple[int, ...] = keyboard_constants.DIATONIC_PITCHES,
        left_hand_start_key: int = parameters.pitches.WesternPitch(
            "e", 3
        ).midi_pitch_number,
        right_hand_start_key: int = parameters.pitches.WesternPitch(
            "f", 4
        ).midi_pitch_number,
    ):
        self._chroma = chroma
        self._available_keys = available_keys
        self._left_hand_start_key = self._find_key(left_hand_start_key)
        self._right_hand_start_key = self._find_key(right_hand_start_key)
        both_hands_center = (
            (right_hand_start_key - left_hand_start_key) // 2
        ) + left_hand_start_key
        self._both_hands_center = self._find_key(both_hands_center)

    def _find_key(self, seed_key: int) -> int:
        return self._available_keys[bisect.bisect_left(self._available_keys, seed_key)]

    def _distribute_pitches_on_hands(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ):
        left_hand_pitches = []
        right_hand_pitches = []
        both_hands_pitches = []
        for appearing_pitch, hand in appearing_pitches_and_hand_pairs:
            if hand == "left":
                left_hand_pitches.append(appearing_pitch)
            elif hand == "right":
                right_hand_pitches.append(appearing_pitch)
            else:
                both_hands_pitches.append(appearing_pitch)

        return (
            tuple(left_hand_pitches),
            tuple(right_hand_pitches),
            tuple(both_hands_pitches),
        )

    def _make_alternating_zone(
        self, n_items: int, start_point: int, border_left: int, border_right: int
    ) -> tuple[int, ...]:
        if n_items > 0:
            allowed_range = ranges.Range(border_left, border_right)
            zone = [start_point]
            alteration_cycle = itertools.cycle((True, False))
            is_dead_end = [False, False]
            while len(zone) < n_items:
                if all(is_dead_end):
                    raise ValueError(
                        f"NO SOLUTION FOUND FOR {n_items} pitches with (start_point = {start_point}, border_left = {border_left}, border_right = {border_right}, chroma = {self._chroma})."
                    )

                insert_position = next(alteration_cycle)
                if insert_position:
                    last_value = zone[-1]
                    operation = lambda value: value + self._chroma
                else:
                    last_value = zone[0]
                    operation = lambda value: value - self._chroma

                new_index = operation(self._available_keys.index(last_value))
                new_value = self._available_keys[new_index]

                if new_value in allowed_range:
                    is_dead_end = [False, False]
                    if insert_position:
                        zone.append(new_value)
                    else:
                        zone.insert(0, new_value)
                else:
                    is_dead_end[insert_position] = True

            return tuple(zone)
        else:
            return tuple([])

    def _make_both_hands_zone(self, both_hands_pitches):
        n_both_hands_pitches = len(both_hands_pitches)
        return self._make_alternating_zone(
            n_both_hands_pitches,
            self._both_hands_center,
            self._available_keys[0],
            self._available_keys[-1],
        )

    def _make_right_hand_zone(self, right_hand_pitches, both_hands_zone):
        if both_hands_zone:
            border_left = both_hands_zone[-1]
        else:
            border_left = self._both_hands_center
        start_point = self._right_hand_start_key
        if border_left > start_point:
            start_point = border_left + 1
        return self._make_alternating_zone(
            len(right_hand_pitches), start_point, border_left, self._available_keys[-1]
        )

    def _make_left_hand_zone(self, left_hand_pitches, both_hands_zone):
        if both_hands_zone:
            border_right = both_hands_zone[0]
        else:
            border_right = self._both_hands_center
        start_point = self._left_hand_start_key
        if border_right < start_point:
            start_point = border_right - 1
        return self._make_alternating_zone(
            len(left_hand_pitches), start_point, self._available_keys[0], border_right
        )

    def _make_pitch_to_key_dict(self, zones, pitches_per_zone):
        pitch_to_key = {}
        for zone, pitches in zip(zones, pitches_per_zone):
            for key, pitch in zip(zone, pitches):
                pitch_to_key.update({pitch.exponents: key})
        return pitch_to_key

    def _make_zones(
        self, left_hand_pitches, right_hand_pitches, both_hands_pitches
    ) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
        both_hands_zone = self._make_both_hands_zone(both_hands_pitches)
        right_hand_zone = self._make_right_hand_zone(
            right_hand_pitches, both_hands_zone
        )
        left_hand_zone = self._make_left_hand_zone(left_hand_pitches, both_hands_zone)
        return left_hand_zone, right_hand_zone, both_hands_zone

    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
        _: typing.Sequence[tuple[int, int]],
    ) -> tuple[int, ...]:
        (
            left_hand_pitches,
            right_hand_pitches,
            both_hands_pitches,
        ) = self._distribute_pitches_on_hands(appearing_pitches_and_hand_pairs)
        left_hand_zone, right_hand_zone, both_hands_zone = self._make_zones(
            left_hand_pitches, right_hand_pitches, both_hands_pitches
        )
        pitch_to_key_dict = self._make_pitch_to_key_dict(
            (left_hand_zone, right_hand_zone, both_hands_zone),
            (
                left_hand_pitches,
                right_hand_pitches,
                both_hands_pitches,
            ),
        )
        keys = []
        for pitch, _ in appearing_pitches_and_hand_pairs:
            keys.append(pitch_to_key_dict[pitch.exponents])
        return tuple(keys)


class MultipleTrialsDistributionStrategy(PitchDistributionStrategy):
    def __init__(self, strategies: tuple[PitchDistributionStrategy, ...]):
        self._strategies = strategies

    def __call__(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
        _: typing.Sequence[tuple[int, int]],
    ) -> tuple[int, ...]:
        for strategy in self._strategies:
            try:
                return strategy(appearing_pitches_and_hand_pairs, _)
            except Exception:
                pass
        raise Exception


class KeyboardEventToPatchConverter(converters.abc.Converter):
    mutwo_pitch_to_midi_pitch_converter = (
        converters.frontends.midi.MutwoPitchToMidiPitchConverter()
    )

    def __init__(
        self,
        pitch_distribution_strategy: PitchDistributionStrategy = HandBasedPitchDistributionStrategy(
            1
        ),
        engine_distribution_strategy: EngineDistributionStrategy = SimpleEngineDistributionStrategy(),
    ):
        self._pitch_distribution_strategy = pitch_distribution_strategy
        self._engine_distribution_strategy = engine_distribution_strategy

    @staticmethod
    def _collect_appearing_pitches_and_hand_pairs(
        keyboard_event_to_convert: events.basic.TaggedSimultaneousEvent,
    ) -> tuple[tuple[parameters.pitches.JustIntonationPitch, str], ...]:
        pitch_or_pitches_per_event = filter(
            bool, keyboard_event_to_convert.get_parameter("pitch_or_pitches", flat=True)
        )
        pitches_as_exponents = set([])
        for pitch_or_pitches in pitch_or_pitches_per_event:
            for pitch in pitch_or_pitches:
                if hasattr(pitch, "exponents"):
                    pitches_as_exponents.add(pitch.exponents)

        appearing_pitches = tuple(
            sorted(map(parameters.pitches.JustIntonationPitch, pitches_as_exponents))
        )
        appearing_pitches_and_hand_pairs = []
        try:
            right_hand_pitches = tuple(
                functools.reduce(
                    operator.add,
                    filter(
                        bool,
                        keyboard_event_to_convert[0].get_parameter(
                            "pitch_or_pitches", flat=True
                        ),
                    ),
                )
            )
        except TypeError:
            right_hand_pitches = tuple([])
        try:
            left_hand_pitches = tuple(
                functools.reduce(
                    operator.add,
                    filter(
                        bool,
                        keyboard_event_to_convert[1].get_parameter(
                            "pitch_or_pitches", flat=True
                        ),
                    ),
                )
            )
        except TypeError:
            left_hand_pitches = tuple([])
        for appearing_pitch in appearing_pitches:
            if (
                appearing_pitch in right_hand_pitches
                and appearing_pitches in left_hand_pitches
            ):
                hand = "both"
            elif appearing_pitch in right_hand_pitches:
                hand = "right"
            elif appearing_pitch in left_hand_pitches:
                hand = "left"
            else:
                raise ValueError()
            appearing_pitches_and_hand_pairs.append((appearing_pitch, hand))
        return tuple(appearing_pitches_and_hand_pairs)

    def _distribute_chromatic_pitches(
        self,
        appearing_pitches: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
    ) -> typing.Tuple[int, ...]:
        # einfach erst alle weisse tasten verteilen, dann stueck fuer stueck im quintenzirkel aufgehen
        # und immer neue chromatische toene hinzufuegen, also erst alle f-sharp, dann, c-sharp, usw.
        missing_chromatic_pitches = len(appearing_pitches) - len(
            keyboard_constants.DIATONIC_PITCHES
        )
        return sorted(
            keyboard_constants.DIATONIC_PITCHES
            + keyboard_constants.CHROMATIC_PITCHES[:missing_chromatic_pitches]
        )

    def _distribute_midi_pitches(
        self,
        nth_cue: int,
        appearing_pitches: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
        sounding_midi_pitches_per_appearing_pitch: typing.Sequence[
            typing.Tuple[int, int]
        ],
    ) -> typing.Tuple[int, ...]:
        n_pitches = len(appearing_pitches)
        if n_pitches <= len(keyboard_constants.DIATONIC_PITCHES):
            midi_pitch_distribution = self._pitch_distribution_strategy(
                appearing_pitches, sounding_midi_pitches_per_appearing_pitch
            )
        elif n_pitches <= len(keyboard_constants.DIATONIC_PITCHES) + len(
            keyboard_constants.CHROMATIC_PITCHES
        ):
            midi_pitch_distribution = OldChromaticPitchDistributionStrategy(
                appearing_pitches, sounding_midi_pitches_per_appearing_pitch
            )
        else:
            message = f"Cue {nth_cue} has too many different pitch classes for the keyboard. Found {n_pitches}!"
            raise ValueError(message)
        return midi_pitch_distribution

    def _distribute_pitches_on_engines(
        self,
        appearing_pitches_and_hand_pairs: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str], ...
        ],
    ) -> tuple[int, ...]:
        return self._engine_distribution_strategy(appearing_pitches_and_hand_pairs)

    def _make_patch(
        self,
        appearing_pitches: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
        sounding_midi_pitches_per_appearing_pitch: typing.Sequence[
            typing.Tuple[int, int]
        ],
        midi_pitch_distribution: typing.Tuple[int, ...],
        engine_distribution: tuple[int, ...],
    ) -> Patch:
        patch_notes = []
        for (
            sounding_just_intonation_pitch,
            sounding_midi_pitch_data,
            played_midi_note,
            engine_id,
        ) in zip(
            appearing_pitches,
            sounding_midi_pitches_per_appearing_pitch,
            midi_pitch_distribution,
            engine_distribution,
        ):
            (
                sounding_midi_note,
                sounding_midi_pitch_bending,
            ) = sounding_midi_pitch_data
            written_pitch = parameters.pitches.WesternPitch.from_midi_pitch_number(
                played_midi_note
            )
            patch_note = PatchNote(
                sounding_just_intonation_pitch=sounding_just_intonation_pitch,
                sounding_midi_note=sounding_midi_note,
                sounding_midi_pitch_bending=sounding_midi_pitch_bending,
                written_pitch=written_pitch,
                played_midi_note=played_midi_note,
                keyboard_engine_id=engine_id,
            )
            patch_notes.append(patch_note)

        return Patch(patch_notes)

    def convert(
        self,
        nth_cue: int,
        keyboard_event_to_convert: events.basic.TaggedSimultaneousEvent,
    ) -> Patch:
        appearing_pitches_and_hand_pairs = (
            KeyboardEventToPatchConverter._collect_appearing_pitches_and_hand_pairs(
                keyboard_event_to_convert
            )
        )
        if appearing_pitches_and_hand_pairs:
            sounding_midi_pitches_per_appearing_pitch = []
            for sounding_just_intonation_pitch, _ in appearing_pitches_and_hand_pairs:
                (
                    sounding_midi_note,
                    sounding_midi_pitch_bending,
                ) = self.mutwo_pitch_to_midi_pitch_converter.convert(
                    sounding_just_intonation_pitch
                )
                sounding_midi_pitch_bending += (
                    converters.frontends.midi_constants.NEUTRAL_PITCH_BEND
                )
                sounding_midi_pitches_per_appearing_pitch.append(
                    (sounding_midi_note, sounding_midi_pitch_bending)
                )

            midi_pitch_distribution = self._distribute_midi_pitches(
                nth_cue,
                appearing_pitches_and_hand_pairs,
                sounding_midi_pitches_per_appearing_pitch,
            )
            engine_distribution = self._distribute_pitches_on_engines(
                appearing_pitches_and_hand_pairs
            )
            patch = self._make_patch(
                tuple(zip(*appearing_pitches_and_hand_pairs))[0],
                sounding_midi_pitches_per_appearing_pitch,
                midi_pitch_distribution,
                engine_distribution,
            )
        else:
            patch = Patch([])

        return patch


class KeyboardTimeBracketToAdaptedKeyboardTimeBracketConverter(
    converters.abc.Converter
):
    def __init__(self, json_settings_path: str):
        self._json_settings_path = json_settings_path

    def _add_cue_mark(
        self,
        nth_cue: int,
        keyboard_event_to_adapt: events.basic.TaggedSimultaneousEvent,
        cue_range: ranges.Range,
    ):
        first_leaf = keyboard_event_to_adapt[0].get_event_at(cue_range.start)
        if first_leaf is not None:
            if not hasattr(first_leaf, "playing_indicators"):
                first_leaf.playing_indicators = (
                    ot2_parameters.playing_indicators.OT2PlayingIndicatorCollection()
                )
            first_leaf.playing_indicators.cue.nth_cue = nth_cue

    def _adapt_keyboard_event(
        self,
        nth_cue: int,
        keyboard_event_to_adapt: events.basic.TaggedSimultaneousEvent,
        cue_ranges: tuple[ranges.Range, ...],
        distribution_strategies: typing.Optional[tuple[PitchDistributionStrategy, ...]],
    ) -> int:
        if not distribution_strategies:
            distribution_strategies = tuple(None for _ in cue_ranges)
        for cue_range, local_distribution_strategy in zip(
            cue_ranges, distribution_strategies
        ):
            self._add_cue_mark(nth_cue, keyboard_event_to_adapt, cue_range)
            if local_distribution_strategy:
                keyboard_event_to_patch_converter = KeyboardEventToPatchConverter(
                    local_distribution_strategy,
                    self.keyboard_event_to_patch_converter._engine_distribution_strategy,
                )
            else:
                keyboard_event_to_patch_converter = (
                    self.keyboard_event_to_patch_converter
                )
            patch = keyboard_event_to_patch_converter.convert(
                nth_cue,
                keyboard_event_to_adapt.cut_out(
                    cue_range.start, cue_range.end, mutate=False
                ),
            )
            for sequential_event in keyboard_event_to_adapt:
                for absolute_time, simple_event in zip(
                    sequential_event.absolute_times, sequential_event
                ):
                    if absolute_time in cue_range:
                        simple_event.set_parameter("pitch_or_pitches", patch.apply)
            patch.save(f"{self._json_settings_path}/{nth_cue}.json")
            nth_cue += 1
        return nth_cue

    def convert(
        self,
        nth_cue: int,
        time_bracket_to_convert: events.time_brackets.TimeBracket,
    ) -> tuple[events.time_brackets.TimeBracket, int]:
        try:
            distribution_strategies = time_bracket_to_convert.distribution_strategies
        except AttributeError:
            distribution_strategies = None

        try:
            distribution_strategy = time_bracket_to_convert.distribution_strategy
        except AttributeError:
            if isinstance(
                time_bracket_to_convert, events.time_brackets.TempoBasedTimeBracket
            ):
                distribution_strategy = HandBasedPitchDistributionStrategy(
                    1,
                    available_keys=tuple(
                        sorted(
                            keyboard_constants.DIATONIC_PITCHES
                            + keyboard_constants.CHROMATIC_PITCHES
                        )
                    ),
                )
            else:
                distribution_strategy = HandBasedPitchDistributionStrategy(2)

        try:
            engine_distribution_strategy = (
                time_bracket_to_convert.engine_distribution_strategy
            )
        except AttributeError:
            engine_distribution_strategy = SimpleEngineDistributionStrategy()
        else:
            if engine_distribution_strategy is None:
                engine_distribution_strategy = SimpleEngineDistributionStrategy()

        if distribution_strategy is None:
            distribution_strategy = MultipleTrialsDistributionStrategy(
                (
                    HandBasedPitchDistributionStrategy(),
                    HandBasedPitchDistributionStrategy(
                        available_keys=tuple(
                            sorted(
                                keyboard_constants.DIATONIC_PITCHES
                                + keyboard_constants.CHROMATIC_PITCHES
                            )
                        )
                    ),
                )
            )

        self.keyboard_event_to_patch_converter = KeyboardEventToPatchConverter(
            distribution_strategy, engine_distribution_strategy
        )
        adapted_time_bracket = time_bracket_to_convert.empty_copy()
        for tagged_simultaneous_event in time_bracket_to_convert:
            adapted_time_bracket.append(tagged_simultaneous_event.copy())
        for tagged_event in adapted_time_bracket:
            if tagged_event.tag == ot2_constants.instruments.ID_KEYBOARD:
                try:
                    cue_ranges = time_bracket_to_convert.cue_ranges
                except AttributeError:
                    cue_ranges = (ranges.Range(0, tagged_event.duration),)
                nth_cue = self._adapt_keyboard_event(
                    nth_cue, tagged_event, cue_ranges, distribution_strategies
                )
        return adapted_time_bracket, nth_cue


class KeyboardTimeBracketsToAdaptedKeyboardTimeBracketsConverter(
    converters.abc.Converter
):
    def __init__(
        self, json_settings_path: str = ot2_constants.paths.KEYBOARD_CUES_PATH
    ):
        self._keyboard_time_bracket_to_adapted_keyboard_time_bracket_converter = (
            KeyboardTimeBracketToAdaptedKeyboardTimeBracketConverter(json_settings_path)
        )

    def convert(
        self,
        time_brackets_to_convert: typing.Sequence[events.time_brackets.TimeBracket],
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        adapted_time_brackets = []
        nth_cue = 1
        for time_bracket in time_brackets_to_convert:
            (
                adapted_time_bracket,
                nth_cue,
            ) = self._keyboard_time_bracket_to_adapted_keyboard_time_bracket_converter.convert(
                nth_cue, time_bracket
            )
            adapted_time_brackets.append(adapted_time_bracket)

        return tuple(adapted_time_brackets)
