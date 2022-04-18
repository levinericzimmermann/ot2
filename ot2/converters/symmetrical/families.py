import copy
import functools
import itertools
import operator
import typing

import expenvelope

from mutwo import converters
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot2 import parameters as ot2_parameters


class PickPitchesFromCurveAndWeightPairsConverter(
    converters.symmetrical.families.PickElementFromCurveAndWeightPairsConverter
):
    def __init__(
        self,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus,
        seed: int = 10,
    ):
        super().__init__(None, seed)
        self.instrument_ambitus = instrument_ambitus

    @staticmethod
    def _get_potential_pitch_and_weight_pairs_from_one_curve_and_weight_pair(
        curve_and_weight_pair: typing.Tuple[events.families.PitchCurve, float]
    ) -> typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...]:
        curve, weight = curve_and_weight_pair
        return tuple(
            (pitch, register_weight * weight)
            for pitch, register_weight in curve.registered_pitch_and_weight_pairs
        )

    @staticmethod
    def _get_potential_pitch_and_weight_pairs(
        curve_and_weight_pairs: typing.Tuple[
            typing.Tuple[events.families.PitchCurve, float], ...
        ]
    ) -> typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...]:
        potential_pitch_and_weight_pairs = []
        for curve_and_weight_pair in curve_and_weight_pairs:
            potential_pitch_and_weight_pairs.extend(
                PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs_from_one_curve_and_weight_pair(
                    curve_and_weight_pair
                )
            )
        return tuple(potential_pitch_and_weight_pairs)

    def _filter_potential_pitches_by_ambitus(
        self,
        potential_pitch_and_weight_pairs: typing.Tuple[
            typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...
        ],
    ) -> typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...]:
        potential_pitches, _ = zip(*potential_pitch_and_weight_pairs)
        filtered_potential_pitches = self.instrument_ambitus.filter_members(
            potential_pitches
        )
        return tuple(
            (pitch, weight)
            for pitch, weight in potential_pitch_and_weight_pairs
            if pitch in filtered_potential_pitches
        )


class PickChordFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(
        self,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus,
        n_pitches_to_pick: typing.Union[int, typing.Sequence[int]],
        seed: int = 10,
    ):
        super().__init__(instrument_ambitus, seed)
        if isinstance(n_pitches_to_pick, int):
            n_pitches_to_pick = (n_pitches_to_pick,)
        n_pitches_to_pick_cycle = itertools.cycle(n_pitches_to_pick)
        self.n_pitches_to_pick_cycle = n_pitches_to_pick_cycle

    def _get_potential_chord_and_weight_pairs(
        self,
        potential_pitch_and_weight_pairs: typing.Tuple[
            typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...
        ],
    ) -> typing.Tuple[
        typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, ...], float],
        ...,
    ]:
        potential_chord_and_weight_pairs = []
        n_pitches_to_pick = next(self.n_pitches_to_pick_cycle)
        for combination in itertools.combinations(
            potential_pitch_and_weight_pairs, n_pitches_to_pick
        ):
            chord, weights = zip(*combination)
            resulting_intervals = tuple(
                pitch0 - pitch1 for pitch0, pitch1 in itertools.combinations(chord, 2)
            )
            # avoid seconds in chords
            if all(abs(interval.cents) > 200 for interval in resulting_intervals):
                weight = functools.reduce(operator.mul, weights)
                potential_chord_and_weight_pairs.append((chord, weight))
        return tuple(potential_chord_and_weight_pairs)

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SimpleEvent:
        try:
            curve_and_weight_pairs = self._get_curve_and_weight_pairs(event_to_convert)
        except AttributeError:
            curve_and_weight_pairs = None
        converted_event = copy.copy(event_to_convert)
        if curve_and_weight_pairs:
            potential_pitch_and_weight_pairs = PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs(
                curve_and_weight_pairs
            )
            potential_pitch_and_weight_pairs = (
                self._filter_potential_pitches_by_ambitus(
                    potential_pitch_and_weight_pairs
                )
            )
            potential_chord_and_weight_pairs = (
                self._get_potential_chord_and_weight_pairs(
                    potential_pitch_and_weight_pairs
                )
            )
            if potential_chord_and_weight_pairs:
                chords, weights = zip(*potential_chord_and_weight_pairs)
                choosen_pitches = tuple(
                    self._random.choice(
                        chords, p=utilities.tools.scale_sequence_to_sum(weights, 1)
                    )
                )
                converted_event.pitch_or_pitches = choosen_pitches
            del converted_event.curve_and_weight_pairs

        return converted_event


class PickPitchLineFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def _calculate_new_weight(
        self,
        previous_weight: float,
        previous_pitch_cents: float,
        pitch: parameters.pitches.JustIntonationPitch,
    ) -> float:
        distance = abs(previous_pitch_cents - pitch.cents)
        min_distance = 50
        best_distance0 = 100
        best_distance1 = 230
        max_distance = 500
        distance_weight_envelope = expenvelope.Envelope.from_points(
            (min_distance, 0),
            (best_distance0, 1),
            (best_distance1, 1),
            (max_distance, 0),
        )
        return distance_weight_envelope.value_at(distance) * previous_weight

    def _find_pitches_for_phrase(
        self,
        curve_and_weight_pairs_per_event: typing.List[
            typing.Tuple[typing.Tuple[events.families.PitchCurve, float], ...]
        ],
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        potential_pitch_and_weight_pairs_per_event = []
        for curve_and_weight_pairs in curve_and_weight_pairs_per_event:
            potential_pitch_and_weight_pairs = (
                self._get_potential_pitch_and_weight_pairs(curve_and_weight_pairs)
            )
            potential_pitch_and_weight_pairs = (
                self._filter_potential_pitches_by_ambitus(
                    potential_pitch_and_weight_pairs
                )
            )
            potential_pitch_and_weight_pairs_per_event.append(
                potential_pitch_and_weight_pairs
            )

        pitch_per_event = []
        for (
            potential_pitch_and_weight_pairs
        ) in potential_pitch_and_weight_pairs_per_event:
            if pitch_per_event:
                previous_pitch = pitch_per_event[-1]
                previous_pitch_cents = previous_pitch.cents
                potential_pitch_and_weight_pairs = tuple(
                    (
                        pitch,
                        self._calculate_new_weight(weight, previous_pitch_cents, pitch),
                    )
                    for pitch, weight in potential_pitch_and_weight_pairs
                )

            pitches, weights = zip(*potential_pitch_and_weight_pairs)
            choosen_pitch = self._random.choice(
                pitches, p=utilities.tools.scale_sequence_to_sum(weights, 1)
            )
            pitch_per_event.append(choosen_pitch)
        return pitch_per_event

    def _apply_pitches_on_sequential_event(
        self,
        sequential_event_to_convert: events.basic.SequentialEvent,
    ):
        curve_and_weight_pairs_per_event = []
        melodic_phrases_indices = []
        start_index = None
        for event_index, simple_event in enumerate(sequential_event_to_convert):
            try:
                curve_and_weight_pairs = self._get_curve_and_weight_pairs(simple_event)
            except AttributeError:
                curve_and_weight_pairs = None

            if curve_and_weight_pairs is None or len(curve_and_weight_pairs) == 0:
                curve_and_weight_pairs = None
                if start_index:
                    melodic_phrases_indices.append((start_index, event_index))
                start_index = None

            if start_index is None and curve_and_weight_pairs:
                start_index = event_index

            curve_and_weight_pairs_per_event.append(curve_and_weight_pairs)

        if start_index is not None:
            melodic_phrases_indices.append((start_index, event_index + 1))

        for start_index, end_index in melodic_phrases_indices:
            pitch_per_event = self._find_pitches_for_phrase(
                curve_and_weight_pairs_per_event[start_index:end_index]
            )
            for index, pitch in enumerate(pitch_per_event):
                sequential_event_to_convert[index + start_index].pitch_or_pitches = [
                    pitch
                ]

    def _convert_sequential_event(
        self,
        sequential_event_to_convert: events.basic.SequentialEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SequentialEvent:
        if isinstance(sequential_event_to_convert[0], events.basic.SimpleEvent):
            sequential_event_to_apply_pitches_to = sequential_event_to_convert.copy()
            self._apply_pitches_on_sequential_event(
                sequential_event_to_apply_pitches_to
            )
            return sequential_event_to_apply_pitches_to
        else:
            return super()._convert_sequential_event(
                sequential_event_to_convert, absolute_entry_delay
            )

    def convert(self, event_to_convert: events.abc.Event) -> events.abc.Event:
        return self._convert_event(event_to_convert, 0)
