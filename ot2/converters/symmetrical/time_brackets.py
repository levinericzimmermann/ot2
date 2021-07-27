"""Module for converting global `FamilyOfPitchCurves` varibale to TimeBracket"""

import abc
import itertools
import operator
import typing

from mutwo import converters
from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters
from ot2 import events as ot2_events
from ot2.parameters import ambitus

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

    def _filter_family_by_minimal_overlapping_percentage(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> float:
        time_range = (time_ranges[0][0], time_ranges[1][1])

        def condition(pitch_curve: events.families.PitchCurve) -> bool:
            overlapping_percentage = pitch_curve.get_overlapping_percentage_with_active_ranges(
                time_range
            )
            return overlapping_percentage >= self._minimal_overlapping_percentage

        return self._family_of_pitch_curves.filter(condition, mutate=False)

    def _are_curves_available_within_minimal_overlapping_percentage(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> bool:
        return (
            len(self._filter_family_by_minimal_overlapping_percentage(time_ranges)) > 0
        )

    @abc.abstractmethod
    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        raise NotImplementedError


class StartTimeToSustainingInstrumentTimeBracketsConverter(
    StartTimeToTimeBracketsConverter
):
    def _add_drone_to_notation(
        self, time_bracket: events.time_brackets.TimeBracket,
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
            root_pitch.register(-2)
            sequential_event_to_add = events.basic.SequentialEvent(
                [events.music.NoteLike(root_pitch, time_bracket[0][0].duration, "mp")]
            )
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
        self, converted_time_bracket: events.time_brackets.TimeBracket
    ):
        sine_tone_event = events.basic.TaggedSimultaneousEvent(
            [converted_time_bracket[0][0].copy()],
            tag=ot2_constants.instruments.ID_SUS_TO_ID_SINE[self._instrument_id],
        )
        return events.time_brackets.TimeBracket(
            [sine_tone_event],
            converted_time_bracket.start_or_start_range,
            converted_time_bracket.end_or_end_range,
        )


class StartTimeToCalligraphicLineConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ambitus.Ambitus,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._instrument_ambitus, 1
        )
        self._dynamic_cycle = itertools.cycle("p pp mp ppp mf".split(" "))
        self._duration_cycle = itertools.cycle((10, 15, 10))
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
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
                blueprint
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
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


class StartTimeToMelodicPhraseConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ambitus.Ambitus,
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
        self._dynamic_cycle = itertools.cycle("p pp mp ppp mf".split(" "))
        self._duration_cycle = itertools.cycle((15, 25, 10))
        self._rhythm_cycle = itertools.cycle((1, 1, 1, 0.5, 1, 0.5, 0.5, 1))

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
                            [
                                events.music.NoteLike(
                                    [], next(self._rhythm_cycle), dynamic
                                )
                                for _ in range(3)
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
                blueprint
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                resulting_time_brackets.append(
                    self._make_copy_of_content_for_sine_tone(converted_time_bracket)
                )
                self._add_cent_deviation(converted_time_bracket[0][0])
                self._add_drone_to_notation(converted_time_bracket)
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToInstrumentalNoiseConverter(
    StartTimeToSustainingInstrumentTimeBracketsConverter
):
    def __init__(
        self, instrument_id: str,
    ):
        super().__init__(None, None)
        self._instrument_id = instrument_id
        self._dynamic_cycle = itertools.cycle("mf".split(" "))
        self._duration_cycle = itertools.cycle((10, 15, 10))
        self._presence_cycle = itertools.cycle((2, 0, 1, 0, 1))
        self._density_cycle = itertools.cycle((2, 3, 0, 1, 2, 3, 1, 0))

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
                            [
                                ot2_events.noises.Noise(
                                    next(self._density_cycle),
                                    next(self._presence_cycle),
                                    1,
                                    parameters.volumes.WesternVolume(dynamic),
                                )
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = [self._make_blueprint_bracket(time_ranges)]
        return tuple(resulting_time_brackets)


class StartTimeToKeyboardTimeBracketsConverter(StartTimeToTimeBracketsConverter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        right_hand_ambitus: ambitus.Ambitus,
        left_hand_ambitus: ambitus.Ambitus,
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
        right_hand_ambitus: ambitus.Ambitus,
        left_hand_ambitus: ambitus.Ambitus,
        minimal_overlapping_percentage: float = 0.2,
    ):
        super().__init__(
            family_of_pitch_curves,
            right_hand_ambitus,
            left_hand_ambitus,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._dynamic_cycle = itertools.cycle("p pp mp ppp p".split(" "))
        self._duration_cycle = itertools.cycle((10, 15, 10))
        self._delay_cycle = itertools.cycle(
            (
                (False, False),
                (True, False),
                (False, False),
                (True, False),
                (False, True),
            )
        )
        self._n_pitches_cycle = itertools.cycle(
            ((2, 2), (3, 1), (1, 1), (1, 3), (2, 3))
        )
        self._assign_curve_and_weight_pairs_on_events = converters.symmetrical.families.AssignCurveAndWeightPairsOnEventsConverter(
            self._family_of_pitch_curves,
            condition=lambda simple_event: hasattr(simple_event, "pitch_or_pitches"),
        )

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        time_bracket = events.time_brackets.TimeBracket(
            [events.basic.TaggedSimultaneousEvent([], tag=self._instrument_id,)],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        end_time = start_time + duration
        time_ranges = (
            (start_time, start_time + 5),
            (end_time, end_time + 5),
        )
        return time_ranges

    def _make_blueprint_bracket_for_left_hand(
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
            *time_ranges
        )
        if self._delay_left_hand:
            time_bracket[0][0].squash_in(0, events.basic.SimpleEvent(0.25))
        return time_bracket

    def _make_blueprint_bracket_for_right_hand(
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
            *time_ranges
        )
        if self._delay_right_hand:
            time_bracket[0][0].squash_in(0, events.basic.SimpleEvent(0.25))
        return time_bracket

    def _get_picker_for_right_hand(self, n_pitches: int = 2):
        return ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._right_hand_ambitus, n_pitches
        )

    def _get_picker_for_left_hand(self, n_pitches: int = 2):
        return ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._left_hand_ambitus, n_pitches
        )

    def _make_sequential_event_for_left_hand(self, time_ranges):
        picker = self._get_picker_for_left_hand(self._n_pitches_left_hand)
        blueprint = self._make_blueprint_bracket_for_left_hand(time_ranges)
        blueprint_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
            blueprint
        )
        converted_time_bracket = picker.convert(blueprint_with_assigned_weight_curves)
        return converted_time_bracket[0][0]

    def _make_sequential_event_for_right_hand(self, time_ranges):
        picker = self._get_picker_for_right_hand(self._n_pitches_right_hand)
        blueprint = self._make_blueprint_bracket_for_right_hand(time_ranges)
        blueprint_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
            blueprint
        )
        converted_time_bracket = picker.convert(blueprint_with_assigned_weight_curves)
        return converted_time_bracket[0][0]

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        self._delay_right_hand, self._delay_left_hand = next(self._delay_cycle)
        self._n_pitches_right_hand, self._n_pitches_left_hand = next(
            self._n_pitches_cycle
        )
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            right_hand = self._make_sequential_event_for_right_hand(time_ranges)
            left_hand = self._make_sequential_event_for_left_hand(time_ranges)
            if not self._is_sequential_event_empty(
                left_hand
            ) or not self._is_sequential_event_empty(right_hand):
                blueprint[0].append(right_hand)
                blueprint[0].append(left_hand)
                resulting_time_brackets.append(blueprint)

        return tuple(resulting_time_brackets)
