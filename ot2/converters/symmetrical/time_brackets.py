"""Module for converting global `FamilyOfPitchCurves` varibale to TimeBracket"""

import abc
import itertools
import operator
import typing

import quicktions as fractions
import numpy as np
import ranges

from formalgrammar.grammar import grammar

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters
from ot2 import events as ot2_events
from ot2 import parameters as ot2_parameters

from ot2.converters.symmetrical import keyboard as keyboard_converter

DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE = 0.75


class StartTimeToTimeBracketsConverter(converters.abc.Converter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
    ):
        self._family_of_pitch_curves = family_of_pitch_curves
        self._minimal_overlapping_percentage = minimal_overlapping_percentage
        if family_of_pitch_curves:
            self._assign_curve_and_weight_pairs_on_events = converters.symmetrical.families.AssignCurveAndWeightPairsOnEventsConverter(
                self._family_of_pitch_curves
            )

    @staticmethod
    def _quantize_time(
        time: parameters.abc.DurationType,
        quantization_step: parameters.abc.DurationType = 5,
    ) -> parameters.abc.DurationType:
        return round(time / quantization_step) * quantization_step

    @staticmethod
    def _is_sequential_event_empty(
        sequential_event_to_analyse: events.basic.SequentialEvent[
            events.basic.SimpleEvent
        ],
    ) -> bool:
        for simple_event in sequential_event_to_analyse:
            if (
                hasattr(simple_event, "pitch_or_pitches")
                and len(simple_event.pitch_or_pitches) > 0
            ):
                return False

        return True

    def _are_curves_available_within_minimal_overlapping_percentage(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> bool:
        if self._minimal_overlapping_percentage:
            as_time_bracket = events.time_brackets.TimeBracket([], *time_ranges)
            as_range = ranges.Range(
                as_time_bracket.minimal_start,
                as_time_bracket.maximum_end,
                include_start=True,
                include_end=True,
            )
            duration = as_range.length()
            for pitch_curve in self._family_of_pitch_curves:
                try:
                    active_ranges = pitch_curve.calculated_active_ranges
                except AttributeError:
                    active_ranges = pitch_curve.active_ranges
                    pitch_curve.calculated_active_ranges = active_ranges
                for active_range in active_ranges:
                    start_and_end_range = ranges.Range(
                        *active_range, include_start=True, include_end=True
                    )
                    if not start_and_end_range.isdisjoint(as_range):
                        intersection = start_and_end_range.intersection(as_range)
                        if intersection:
                            intersection_duration = intersection.length()
                            percentage = intersection_duration / duration
                            if percentage >= self._minimal_overlapping_percentage:
                                return True

            return False
        else:
            return True

    @abc.abstractmethod
    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        raise NotImplementedError


class StartTimeToSustainingInstrumentTimeBracketsConverter(
    StartTimeToTimeBracketsConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attack_cycle = itertools.cycle((0.1, 0.18, 0.135, 0.139, 0.2, 0.18, 0.23))
        self._release_cycle = itertools.cycle((0.3, 0.28, 0.14, 0.21, 0.18, 0.24))

    def _add_drone_to_notation(
        self, time_bracket: events.time_brackets.TimeBracket, dynamic: str = "p"
    ):
        time_range = (time_bracket.minimal_start, time_bracket.maximum_end)

        def cut_out_unused_events(pitch_curve: events.families.PitchCurve) -> bool:
            return (
                pitch_curve.tag == "root"
                and pitch_curve.get_overlapping_percentage_with_active_ranges(
                    time_range
                )
                > 0.1
            )

        filtered_family = self._family_of_pitch_curves.filter(
            cut_out_unused_events, mutate=False
        )
        filtered_family.cut_out(*time_range, mutate=False)
        filtered_family.filter_curves_with_tag("root")
        if filtered_family:
            most_important_root = max(
                filtered_family, key=lambda curve: curve.weight_curve.average_level()
            )
            root_pitch, _ = max(
                most_important_root.registered_pitch_and_weight_pairs,
                key=operator.itemgetter(1),
            )
            absolute_position = (
                time_bracket.minimal_start / ot2_constants.duration.DURATION_IN_SECONDS
            )
            register = ot2_constants.tendencies_and_choices.DRONE_REGISTER_RANGE_DICT[
                absolute_position
            ]
            root_pitch.register(register)
            sequential_event_to_add = events.basic.SequentialEvent(
                [
                    events.music.NoteLike(
                        root_pitch, time_bracket[0][0].duration, dynamic
                    )
                ]
            )
            if root_pitch > parameters.pitches.JustIntonationPitch("3/5"):
                clef = "treble"
            else:
                clef = "bass"
            sequential_event_to_add[0].notation_indicators.clef.name = clef
            tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
                [sequential_event_to_add], tag=ot2_constants.instruments.ID_DRONE
            )
            time_bracket.append(tagged_simultaneous_event)

    def _add_cent_deviation(
        self,
        sequential_event_to_process: events.basic.SequentialEvent[
            events.music.NoteLike
        ],
    ):
        for event in sequential_event_to_process:
            if hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches:
                pitch_to_process = event.pitch_or_pitches[0]
                deviation = (
                    pitch_to_process.cent_deviation_from_closest_western_pitch_class
                )
                event.notation_indicators.cent_deviation.deviation = deviation

    def _make_copy_of_content_for_sine_tone(
        self,
        converted_time_bracket: events.time_brackets.TimeBracket,
        attack: typing.Optional[float] = None,
        release: typing.Optional[float] = None,
    ):
        if not attack:
            attack = next(self._attack_cycle)

        if not release:
            release = next(self._release_cycle)

        sine_tone_event = events.basic.TaggedSimultaneousEvent(
            [converted_time_bracket[0][0].copy()],
            tag=ot2_constants.instruments.ID_SUS_TO_ID_SINE[self._instrument_id],
        )
        sine_tone_event.set_parameter(
            "volume",
            lambda volume: parameters.volumes.DecibelVolume(volume.decibel + 6),
        )
        sine_tone_event.set_parameter(
            "attack",
            attack,
        )
        sine_tone_event.set_parameter(
            "release",
            release,
        )
        sine_tone_time_bracket = events.time_brackets.TimeBracket(
            [sine_tone_event],
            converted_time_bracket.start_or_start_range,
            converted_time_bracket.end_or_end_range,
        )
        sine_tone_time_bracket.flexible_start_range = (
            sine_tone_time_bracket.flexible_start_range * 0.2
        )
        sine_tone_time_bracket.flexible_end_range = (
            sine_tone_time_bracket.flexible_end_range * 0.2
        )
        return sine_tone_time_bracket


class StartTimeToCalligraphicLineConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
        make_sine_part: bool = True,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._make_sine_part = make_sine_part
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._instrument_ambitus, 1
        )
        self._duration_cycle = itertools.cycle((5, 15, 10, 5, 10))
        self._left_side_free_time_cycle = itertools.cycle((5, 5, 10, 5, 10, 5, 5))
        self._right_side_free_time_cycle = itertools.cycle((5, 10, 5, 5))
        self._squash_in_cycle = itertools.cycle(
            (
                None,
                None,
                (0.25, events.basic.SimpleEvent(0.25)),
                None,
                (0.5, events.basic.SimpleEvent(0.25)),
                None,
            )
        )

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        absolute_position = (
            time_ranges[0][0] / ot2_constants.duration.DURATION_IN_SECONDS
        )
        dynamic = ot2_constants.tendencies_and_choices.CALLIGRAPHIC_LINE_DYNAMIC_CHOICES.gamble_at(
            absolute_position
        )
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [events.music.NoteLike([], 1, dynamic)]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
        )
        return time_bracket

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        left_side_free_time = next(self._left_side_free_time_cycle)
        right_side_free_time = next(self._right_side_free_time_cycle)
        second_start_time = start_time + left_side_free_time
        first_end_time = second_start_time + duration
        second_end_time = first_end_time + right_side_free_time
        time_ranges = (
            (start_time, second_start_time),
            (first_end_time, second_end_time),
        )
        return time_ranges

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = (
                self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                if self._make_sine_part:
                    resulting_time_brackets.append(
                        self._make_copy_of_content_for_sine_tone(converted_time_bracket)
                    )
                squash_in_data = next(self._squash_in_cycle)
                if squash_in_data:
                    converted_time_bracket[0][0].squash_in(*squash_in_data)
                self._add_cent_deviation(converted_time_bracket[0][0][:1])
                self._add_drone_to_notation(converted_time_bracket)
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToPillowChordConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
        n_pitches_cycle: tuple[int, ...] = (4, 1, 2, 1, 3, 2, 3),
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._n_pitches_cycle = itertools.cycle(n_pitches_cycle)
        self._duration_cycle = itertools.cycle((12, 15, 11, 13, 16))
        self._left_side_free_time_cycle = itertools.cycle((0.1, 0.4, 0.2, 0.1))
        self._right_side_free_time_cycle = itertools.cycle((0.3, 0.4))
        self._delay_cycle = itertools.cycle((1, 0.3, 0.1, 0.9, 1.2, 3.2, 0.1, 0.321))
        self._attack_duration_cycle = itertools.cycle((0.2, 0.3, 0.12, 0.43, 0.17))
        self._release_duration_cycle = itertools.cycle(
            (0.1, 0.38, 0.5, 0.1, 0.23, 0.322)
        )
        self._maxima_n_events = max(n_pitches_cycle)

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        absolute_position = (
            time_ranges[0][0] / ot2_constants.duration.DURATION_IN_SECONDS
        )
        dynamic = ot2_constants.tendencies_and_choices.CALLIGRAPHIC_LINE_DYNAMIC_CHOICES.gamble_at(
            absolute_position
        )
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [events.music.NoteLike([], 1, dynamic)]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
        )
        return time_bracket

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        delay = next(self._delay_cycle)
        left_side_free_time = next(self._left_side_free_time_cycle)
        right_side_free_time = next(self._right_side_free_time_cycle)
        start_time = start_time + delay
        second_start_time = start_time + left_side_free_time
        first_end_time = second_start_time + duration
        second_end_time = first_end_time + right_side_free_time
        time_ranges = (
            (start_time, second_start_time),
            (first_end_time, second_end_time),
        )
        return time_ranges

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = (
                self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
            )
            n_pitches = next(self._n_pitches_cycle)
            picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
                self._instrument_ambitus, n_pitches
            )
            converted_time_bracket = picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            # loop to make sure we will get any pitch
            while (
                not converted_time_bracket[0][0][0].pitch_or_pitches and n_pitches > 1
            ):
                n_pitches -= 1
                picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
                    self._instrument_ambitus, n_pitches
                )
                converted_time_bracket = picker.convert(
                    time_bracket_with_assigned_weight_curves
                )
            sequential_events = []
            note_like = converted_time_bracket[0][0][0]
            for pitch in note_like.pitch_or_pitches:
                new_event = ot2_events.music.PillowEvent(
                    pitch,
                    1,
                    note_like.volume,
                    next(self._attack_duration_cycle),
                    next(self._release_duration_cycle),
                )
                sequential_events.append(events.basic.SequentialEvent([new_event]))

            """
            difference = self._maxima_n_events - len(sequential_events)
            for _ in range(difference):
                sequential_events.append(
                    events.basic.SequentialEvent(
                        [ot2_events.music.PillowEvent([], 1, note_like.volume)]
                    )
                )
            """

            if sequential_events:
                blueprint = blueprint.copy()
                tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
                    sequential_events, tag=self._instrument_id
                )
                del blueprint[0]
                blueprint.append(tagged_simultaneous_event)
                resulting_time_brackets.append(blueprint)

        return tuple(resulting_time_brackets)


class StartTimeToMelodicPhraseConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._picker = ot2_converters.symmetrical.families.PickPitchLineFromCurveAndWeightPairsConverter(
            self._instrument_ambitus
        )
        self._duration_cycle = itertools.cycle((15, 25, 10, 5))
        self._left_side_free_time_cycle = itertools.cycle((5, 5, 10, 5, 5))
        self._right_side_free_time_cycle = itertools.cycle((5, 10, 5, 5))
        self._rhythm_grammar = grammar.LSystem(
            [
                grammar.Rule(
                    (fractions.Fraction(1, 1),),
                    (fractions.Fraction(1, 2), fractions.Fraction(1, 1)),
                ),
                grammar.Rule(
                    (fractions.Fraction(1, 1),),
                    (fractions.Fraction(3, 4), fractions.Fraction(1, 1)),
                ),
                grammar.Rule(
                    (fractions.Fraction(1, 2),),
                    (fractions.Fraction(3, 4), fractions.Fraction(1, 2)),
                ),
                grammar.Rule(
                    (fractions.Fraction(3, 4),),
                    (fractions.Fraction(1, 2), fractions.Fraction(3, 4)),
                ),
            ]
        )
        self._n_pitches_cycle = itertools.cycle((3, 2, 4, 5))

    def _find_duration_per_event(self, n_events: int) -> tuple[fractions.Fraction, ...]:
        walk_iterable = self._rhythm_grammar.walk((fractions.Fraction(1, 1),))
        durations = []
        while len(durations) < n_events:
            durations = next(walk_iterable)
        difference = len(durations) - n_events
        durations = durations[difference:]
        return tuple(durations)

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        absolute_position = (
            time_ranges[0][0] / ot2_constants.duration.DURATION_IN_SECONDS
        )
        dynamic = ot2_constants.tendencies_and_choices.MELODIC_PHRASE_DYNAMIC_CHOICES.gamble_at(
            absolute_position
        )
        n_pitches = next(self._n_pitches_cycle)
        duration_per_event = self._find_duration_per_event(n_pitches)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                events.music.NoteLike([], duration, dynamic)
                                for duration in duration_per_event
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
        )
        return time_bracket

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        left_side_free_time = next(self._left_side_free_time_cycle)
        right_side_free_time = next(self._right_side_free_time_cycle)
        second_start_time = start_time + left_side_free_time
        first_end_time = second_start_time + duration
        second_end_time = first_end_time + right_side_free_time
        time_ranges = (
            (start_time, second_start_time),
            (first_end_time, second_end_time),
        )
        return time_ranges

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = (
                self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                while not converted_time_bracket[0][0][-1].pitch_or_pitches:
                    converted_time_bracket[0][0] = converted_time_bracket[0][0][:-1]
                resulting_time_brackets.append(
                    self._make_copy_of_content_for_sine_tone(converted_time_bracket)
                )
                converted_time_bracket[0][0].tie_by(
                    lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
                )
                self._add_cent_deviation(converted_time_bracket[0][0])
                self._add_drone_to_notation(converted_time_bracket)
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToInstrumentalNoiseConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
    ):
        super().__init__(None, None)
        self._instrument_id = instrument_id
        self._dynamic_cycle = itertools.cycle("mp".split(" "))
        self._duration_cycle = itertools.cycle((15, 20, 10, 15, 10, 20))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        absolute_position = (
            time_ranges[0][0] / ot2_constants.duration.DURATION_IN_SECONDS
        )
        density = ot2_constants.tendencies_and_choices.NOISE_DENSITY_CHOICES.gamble_at(
            absolute_position
        )
        presence = (
            ot2_constants.tendencies_and_choices.NOISE_PRESENCE_CHOICES.gamble_at(
                absolute_position
            )
        )
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                ot2_events.noises.Noise(
                                    density,
                                    presence,
                                    1,
                                    parameters.volumes.WesternVolume(dynamic),
                                )
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
        )
        return time_bracket

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = [self._make_blueprint_bracket(time_ranges)]
        return tuple(resulting_time_brackets)


class StartTimeToKeyboardTimeBracketsConverter(StartTimeToTimeBracketsConverter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        right_hand_ambitus: ot2_parameters.ambitus.Ambitus,
        left_hand_ambitus: ot2_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = 0.2,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._instrument_id = ot2_constants.instruments.ID_KEYBOARD
        self._right_hand_ambitus = right_hand_ambitus
        self._left_hand_ambitus = left_hand_ambitus


class StartTimeToChordConverter(StartTimeToKeyboardTimeBracketsConverter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        right_hand_ambitus: ot2_parameters.ambitus.Ambitus,
        left_hand_ambitus: ot2_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = 0.2,
        n_pitches_cycle: tuple[tuple[int, int], ...] = (
            (2, 2),
            (3, 1),
            (1, 1),
            (1, 3),
            (2, 3),
        ),
        delay_cycle: tuple[tuple[bool, bool], ...] = (
            (False, False),
            (True, False),
            (False, False),
            (True, False),
            (False, True),
        ),
    ):
        super().__init__(
            family_of_pitch_curves,
            right_hand_ambitus,
            left_hand_ambitus,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._pair_duration_grammar = grammar.LSystem(
            [
                grammar.Rule(
                    (fractions.Fraction(1, 1),),
                    (fractions.Fraction(1, 2), fractions.Fraction(1, 1)),
                ),
                grammar.Rule(
                    (fractions.Fraction(1, 1),),
                    (fractions.Fraction(3, 4), fractions.Fraction(1, 1)),
                ),
                grammar.Rule(
                    (fractions.Fraction(1, 2),),
                    (fractions.Fraction(3, 4), fractions.Fraction(1, 2)),
                ),
                grammar.Rule(
                    (fractions.Fraction(3, 4),),
                    (fractions.Fraction(1, 2), fractions.Fraction(3, 4)),
                ),
            ]
        )
        self._flexible_start_range_cycle = itertools.cycle((5, 5, 10))
        self._flexible_end_range_cycle = itertools.cycle((10, 5, 5, 10, 5))
        self._delay_factor_cycle = itertools.cycle(
            (
                fractions.Fraction(1, 4),
                fractions.Fraction(1, 2),
                fractions.Fraction(1, 2),
                fractions.Fraction(1, 4),
            )
        )
        self._delay_cycle = itertools.cycle(delay_cycle)
        self._n_pitches_cycle = itertools.cycle(n_pitches_cycle)
        self._assign_curve_and_weight_pairs_on_events = (
            converters.symmetrical.families.AssignCurveAndWeightPairsOnEventsConverter(
                self._family_of_pitch_curves,
                condition=lambda simple_event: hasattr(
                    simple_event, "pitch_or_pitches"
                ),
            )
        )

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        absolute_position = start_time / ot2_constants.duration.DURATION_IN_SECONDS
        duration = ot2_constants.tendencies_and_choices.PIANO_CHORDS_DURATION_CHOICES.gamble_at(
            absolute_position
        )
        flexible_start_range = next(self._flexible_start_range_cycle)
        flexible_end_range = next(self._flexible_end_range_cycle)
        start_time1 = start_time + flexible_start_range
        end_time0 = start_time1 + duration
        end_time1 = end_time0 + flexible_end_range
        time_ranges = (
            (start_time, start_time1),
            (end_time0, end_time1),
        )
        return time_ranges

    def _make_one_pair(
        self, dynamic: str, duration: fractions.Fraction, is_delayed: bool
    ) -> events.basic.SequentialEvent:
        sequential_event = events.basic.SequentialEvent(
            [events.music.NoteLike([], duration, dynamic)]
        )
        if is_delayed:
            sequential_event.squash_in(
                0, events.basic.SimpleEvent(duration * next(self._delay_factor_cycle))
            )
        return sequential_event

    def _make_one_left_and_right_hand_pair(
        self, dynamic: str, duration: fractions.Fraction
    ) -> tuple[events.basic.SequentialEvent, events.basic.SequentialEvent]:
        delay_right_hand, delay_left_hand = next(self._delay_cycle)
        return self._make_one_pair(
            dynamic, duration, delay_left_hand
        ), self._make_one_pair(dynamic, duration, delay_right_hand)

    def _find_duration_per_pair(self, n_pairs: int) -> tuple[fractions.Fraction, ...]:
        walk_iterable = self._pair_duration_grammar.walk((fractions.Fraction(1, 1),))
        durations = []
        while len(durations) < n_pairs:
            durations = next(walk_iterable)
        difference = len(durations) - n_pairs
        durations = durations[difference:]
        return tuple(durations)

    def _make_sequential_events_and_n_pitches_per_event_for_left_and_right_hand(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> tuple[
        tuple[events.basic.SequentialEvent, events.basic.SequentialEvent],
        tuple[tuple[int, ...], tuple[int, ...]],
    ]:
        absolute_position = (
            time_ranges[0][0] / ot2_constants.duration.DURATION_IN_SECONDS
        )
        dynamic = (
            ot2_constants.tendencies_and_choices.PIANO_CHORDS_DYNAMIC_CHOICES.gamble_at(
                absolute_position
            )
        )
        n_pairs = ot2_constants.tendencies_and_choices.N_PAIRS_FOR_PIANO_CHORDS_CHOICES.gamble_at(
            absolute_position
        )
        duration_per_pair = self._find_duration_per_pair(n_pairs)
        left_and_right_hand = (
            events.basic.SequentialEvent([]),
            events.basic.SequentialEvent([]),
        )
        for duration in duration_per_pair:
            left_and_right_hand_pair = self._make_one_left_and_right_hand_pair(
                dynamic, duration
            )
            for parent, child in zip(left_and_right_hand, left_and_right_hand_pair):
                parent.extend(child)

        n_pitches = []
        for _ in range(n_pairs):
            n_pitches.append(next(self._n_pitches_cycle))

        return left_and_right_hand, tuple(zip(*n_pitches)), n_pairs

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
        sequential_events: list = [],
    ) -> events.time_brackets.TimeBracket:
        time_bracket = ot2_events.time_brackets.KeyboardTimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    sequential_events,
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
            distribution_strategy=keyboard_converter.MultipleTrialsDistributionStrategy(
                (keyboard_converter.HandBasedPitchDistributionStrategy(1),)
            ),
        )
        return time_bracket

    def _assign_pitches(
        self, sequential_event, n_pitches_per_event, time_ranges, ambitus
    ):
        picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            ambitus, n_pitches_per_event
        )
        blueprint = self._make_blueprint_bracket(time_ranges, [sequential_event])
        blueprint_with_assigned_weight_curves = (
            self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
        )
        converted_time_bracket = picker.convert(blueprint_with_assigned_weight_curves)
        return converted_time_bracket[0][0]

    def _make_sequential_event_for_right_hand(self, time_ranges):
        picker = self._get_picker_for_right_hand(self._n_pitches_right_hand)
        blueprint = self._make_blueprint_bracket_for_right_hand(time_ranges)
        blueprint_with_assigned_weight_curves = (
            self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
        )
        converted_time_bracket = picker.convert(blueprint_with_assigned_weight_curves)
        return converted_time_bracket[0][0]

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        (
            sequential_event_per_hand,
            n_pitches_per_hand,
            n_pairs,
        ) = self._make_sequential_events_and_n_pitches_per_event_for_left_and_right_hand(
            time_ranges
        )
        left_hand, right_hand = (
            self._assign_pitches(
                sequential_event, n_pitches_per_event, time_ranges, ambitus
            )
            for sequential_event, n_pitches_per_event, ambitus in zip(
                sequential_event_per_hand,
                n_pitches_per_hand,
                (self._left_hand_ambitus, self._right_hand_ambitus),
            )
        )
        if not self._is_sequential_event_empty(
            left_hand
        ) or not self._is_sequential_event_empty(right_hand):
            blueprint = self._make_blueprint_bracket(
                time_ranges, [right_hand, left_hand]
            )
            if n_pairs <= 2:
                distribution_strategy = ot2_converters.symmetrical.keyboard.HandBasedPitchDistributionStrategy(
                    2
                )
            else:
                distribution_strategy = ot2_converters.symmetrical.keyboard.HandBasedPitchDistributionStrategy(
                    1
                )
            blueprint.distribution_strategy = distribution_strategy
            resulting_time_brackets.append(blueprint)

        return tuple(resulting_time_brackets)


class StartTimeToTremoloConverter(StartTimeToKeyboardTimeBracketsConverter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        ambitus: ot2_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = 0.15,
    ):
        super().__init__(
            family_of_pitch_curves,
            ambitus,
            ambitus,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._active_hands_cycle = itertools.cycle(
            filter(
                lambda code: sum(code) > 0, generators.gray.reflected_binary_code(2, 2)
            )
        )
        self._left_side_free_time_cycle = itertools.cycle((5, 5, 10, 5, 10))
        self._right_side_free_time_cycle = itertools.cycle((5, 10, 5, 5))
        self._duration_cycle = itertools.cycle((5, 10, 5, 10, 15))
        self._dynamic_cycle = itertools.cycle(("p", "pp", "ppp", "pp"))
        self._assign_curve_and_weight_pairs_on_events = (
            converters.symmetrical.families.AssignCurveAndWeightPairsOnEventsConverter(
                self._family_of_pitch_curves,
                condition=lambda simple_event: hasattr(
                    simple_event, "pitch_or_pitches"
                ),
            )
        )
        self._n_tones_for_one_hand_cycle = itertools.cycle((9, 7, 12, 11))
        self._n_tones_for_both_hands_cycle = itertools.cycle((10, 14, 12, 10, 8, 12))
        self._reverse_rhythmic_distribution_al = generators.edwards.ActivityLevel()

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        time_bracket = ot2_events.time_brackets.KeyboardTimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent([events.music.NoteLike([], 1)]),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
            engine_distribution_strategy=keyboard_converter.SimpleEngineDistributionStrategy(
                1
            ),
        )
        return time_bracket

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        left_side_free_time = next(self._left_side_free_time_cycle)
        right_side_free_time = next(self._right_side_free_time_cycle)
        second_start_time = start_time + left_side_free_time
        first_end_time = second_start_time + duration
        second_end_time = first_end_time + right_side_free_time
        time_ranges = (
            (start_time, second_start_time),
            (first_end_time, second_end_time),
        )
        return time_ranges

    def _make_tremolo_for_one_hand(
        self,
        pitch: parameters.pitches.JustIntonationPitch,
        bar_duration: fractions.Fraction,
        dynamic: str,
    ):
        n_tones = next(self._n_tones_for_one_hand_cycle)
        n_beats = 16
        assert n_tones <= n_beats
        rhythm = generators.toussaint.euclidean(n_beats, n_tones)
        duration_per_beat = bar_duration / n_beats
        hand = events.basic.SequentialEvent([])
        for beats in rhythm:
            note_duration = beats * duration_per_beat
            note_like = events.music.NoteLike(pitch, note_duration, dynamic)
            hand.append(note_like)
        return hand

    def _make_tremolo_for_pair(
        self,
        pitches: tuple[
            parameters.pitches.JustIntonationPitch,
            parameters.pitches.JustIntonationPitch,
        ],
        dynamic: str,
    ) -> tuple[events.basic.SequentialEvent, events.basic.SequentialEvent]:
        n_beats = next(self._n_tones_for_both_hands_cycle)
        rhythms = generators.toussaint.paradiddle(n_beats)
        if self._reverse_rhythmic_distribution_al(5):
            rhythms = tuple(reversed(rhythms))

        bar_duration = fractions.Fraction(n_beats, 4)
        duration_per_beat = bar_duration / n_beats
        sequential_events = []
        # for rhythm, pitch in zip(rhythms, reversed(pitches)):
        for rhythm, pitch in zip(rhythms, pitches):
            sequential_event = events.basic.SequentialEvent([])
            is_first = True
            for start, stop in zip(rhythm, rhythm[1:] + (n_beats,)):
                if is_first and start != 0:
                    sequential_event.append(
                        events.music.NoteLike([], duration_per_beat * start)
                    )
                duration = (stop - start) * duration_per_beat
                note_like = events.music.NoteLike(pitch, duration, dynamic)
                sequential_event.append(note_like)
                is_first = False
            sequential_events.append(sequential_event)

        return tuple(sequential_events)

    def _find_pitch_or_pitches(
        self,
        time_ranges: tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
        active_hands: tuple[bool, bool],
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        n_pitches = sum(active_hands)
        blueprint = self._make_blueprint_bracket(time_ranges)
        time_bracket_with_assigned_weight_curves = (
            self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
        )
        picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._right_hand_ambitus, n_pitches
        )
        converted_time_bracket = picker.convert(
            time_bracket_with_assigned_weight_curves
        )
        return converted_time_bracket[0][0][0].pitch_or_pitches

    def _make_sequential_events(
        self,
        pitch_or_pitches: tuple[parameters.pitches.JustIntonationPitch, ...],
        active_hands: tuple[bool, bool],
        dynamic: str,
    ) -> typing.Optional[
        tuple[events.basic.SequentialEvent, events.basic.SequentialEvent]
    ]:
        if pitch_or_pitches:
            n_active_pitches = sum(active_hands)
            if n_active_pitches == 2:
                sequential_events = sequential_event = self._make_tremolo_for_pair(
                    pitch_or_pitches, dynamic
                )
            else:
                bar_duration = fractions.Fraction(2, 1)
                sequential_events = [events.basic.SequentialEvent([]) for _ in range(2)]
                for nth_hand, activity in enumerate(active_hands):
                    if activity:
                        sequential_event = self._make_tremolo_for_one_hand(
                            pitch_or_pitches[0], bar_duration, dynamic
                        )
                    else:
                        sequential_event = events.basic.SequentialEvent(
                            [events.music.NoteLike([], bar_duration)]
                        )
                    sequential_events[nth_hand].extend(sequential_event)
            return tuple(sequential_events)
        else:
            return

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            active_hands = next(self._active_hands_cycle)
            dynamic = next(self._dynamic_cycle)
            pitch_or_pitches = self._find_pitch_or_pitches(time_ranges, active_hands)
            sequential_events = self._make_sequential_events(
                pitch_or_pitches, active_hands, dynamic
            )
            if sequential_events:
                time_bracket = self._make_blueprint_bracket(time_ranges)
                del time_bracket[0][0]
                time_bracket[0].extend(sequential_events)
                resulting_time_brackets.append(time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToCalligraphicGongLineConverter(StartTimeToTimeBracketsConverter):
    min_delay = 0
    max_delay = 3

    def __init__(
        self,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        minimal_overlapping_percentage: float = 0.1,
        dynamic_cycle: tuple[str, ...] = ("p", "mp", "p", "pp"),
        duration_cycle: tuple[parameters.abc.DurationType, ...] = (
            15,
            10,
            15,
            10,
            20,
            10,
        ),
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._instrument_id = ot2_constants.instruments.ID_GONG
        self._instrument_ambitus = instrument_ambitus
        self._picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._instrument_ambitus, 1
        )
        self._duration_cycle = itertools.cycle(duration_cycle)
        self._dynamic_cycle = itertools.cycle(dynamic_cycle)
        self._delay_random_generator = np.random.default_rng(100)

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [events.music.NoteLike([], 1, dynamic)]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges,
        )
        return time_bracket

    def _get_time_ranges(
        self,
        start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        delay = self._delay_random_generator.uniform(self.min_delay, self.max_delay)
        start_time = start_time + delay
        end_time = start_time + duration
        time_ranges = (
            (start_time, start_time + 0.1),
            (end_time, end_time + 0.1),
        )
        return time_ranges

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = (
                self._assign_curve_and_weight_pairs_on_events.convert(blueprint)
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)
