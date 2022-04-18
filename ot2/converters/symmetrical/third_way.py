import itertools

import abjad
import quicktions as fractions
import numpy as np

from mutwo import events
from mutwo import generators
from mutwo import parameters
from mutwo import utilities

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters
from ot2 import tweaks as tw

from ot2.converters.symmetrical import cengkoks
from ot2.converters.symmetrical import keyboard
from ot2.converters.symmetrical import time_brackets

StartTimeRange = events.time_brackets.TimeRange
EndTimeRange = events.time_brackets.TimeRange
Tempo = float
NBeatsUpbeat = int
NBeatsChord = int
StructuralData = tuple[StartTimeRange, EndTimeRange, Tempo, NBeatsUpbeat, NBeatsChord]


class StartTimeToHomophonicChordsConverter(
    time_brackets.StartTimeToTimeBracketsConverter
):
    sustaining_instrument_ids = (
        ot2_constants.instruments.ID_SUS0,
        ot2_constants.instruments.ID_SUS1,
        ot2_constants.instruments.ID_SUS2,
    )

    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        minimal_overlapping_percentage: float = time_brackets.DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
        n_pitches_cycle: tuple[int, ...] = (4, 2, 3, 1, 2, 3),
        n_beats_upbeat_cycle: tuple[int, ...] = (2, 3, 2, 4),
        n_beats_chord_cycle: tuple[int, ...] = (5, 6, 3, 7, 4),
        beat_length_in_seconds_cycle: tuple[float, ...] = (1.45, 2, 2.5, 1.75),
        beat_length_in_seconds_blur_cycle: tuple[float, ...] = (0.25, 0.2, 0.185),
        minimal_amount_of_sustaining_instruments: int = 2,
        dynamic_cycle: tuple[str, ...] = ("pp", "p", "ppp"),
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._n_pitches_cycle = itertools.cycle(n_pitches_cycle)
        self._n_beats_upbeat_cycle = itertools.cycle(n_beats_upbeat_cycle)
        self._n_beats_chord_cycle = itertools.cycle(n_beats_chord_cycle)
        self._beat_length_in_seconds_cycle = itertools.cycle(
            beat_length_in_seconds_cycle
        )
        self._dynamic_cycle = itertools.cycle(dynamic_cycle)
        self._beat_length_in_seconds_blur_cycle = itertools.cycle(
            beat_length_in_seconds_blur_cycle
        )
        is_sustaining_instrument_active_per_event = tuple(
            filter(
                lambda code: sum(code) >= minimal_amount_of_sustaining_instruments,
                generators.gray.reflected_binary_code(3, 2),
            )
        )
        self._responsible_sustaining_instrument_cycle = itertools.cycle(
            is_sustaining_instrument_active_per_event
        )
        self._left_hand_keyboard_pitches_modification_cycle = itertools.cycle(
            (
                parameters.pitches.JustIntonationPitch("1/2"),
                parameters.pitches.JustIntonationPitch("1/4"),
                parameters.pitches.JustIntonationPitch("1/2"),
            )
        )
        self._tie_cycle = itertools.cycle((False, True, False, True, True, False))
        self._tie_random = np.random.default_rng(32)
        self._random_attack = np.random.default_rng(10)
        self._random_release = np.random.default_rng(100)

    def _find_structural_data_for_homophonic_event(
        self, start_time: float
    ) -> StructuralData:
        n_beats_upbeat = next(self._n_beats_upbeat_cycle)
        n_beats_chord = next(self._n_beats_chord_cycle)
        beat_length_in_seconds = next(self._beat_length_in_seconds_cycle)
        beat_length_blur = next(self._beat_length_in_seconds_blur_cycle) / 2
        assert beat_length_in_seconds > beat_length_blur
        min_beat_length, max_beat_length = (
            beat_length_in_seconds - beat_length_blur,
            beat_length_in_seconds + beat_length_blur,
        )
        n_beats = n_beats_upbeat + n_beats_chord
        min_duration = n_beats * min_beat_length
        max_duration = n_beats * max_beat_length
        start_time_flexibility = 5
        start_time_range = (start_time, start_time + start_time_flexibility)
        min_end_time = start_time_range[0] + min_duration
        max_end_time = start_time_range[1] + max_duration
        end_time_range = (min_end_time, max_end_time)
        min_tempo = 60 / min_beat_length
        max_tempo = 60 / max_beat_length
        tempo = parameters.tempos.TempoPoint((min_tempo, max_tempo))
        return (start_time_range, end_time_range, tempo, n_beats_upbeat, n_beats_chord)

    def _find_pitches(
        self,
        start_time_range: StartTimeRange,
        end_time_range: EndTimeRange,
        n_pitches: int,
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        mock_time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([events.music.NoteLike([], 1)])],
                    tag="mocking",
                )
            ],
            start_time_range,
            end_time_range,
        )
        mock_time_bracket_with_assigned_weight_curves = (
            self._assign_curve_and_weight_pairs_on_events.convert(mock_time_bracket)
        )
        picker = ot2_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            n_pitches,
        )
        converted_time_bracket = picker.convert(
            mock_time_bracket_with_assigned_weight_curves
        )
        return converted_time_bracket[0][0][0].pitch_or_pitches

    def _add_sustaining_instrument_to_time_bracket(
        self,
        time_bracket: cengkoks.CengkokTimeBracket,
        structural_data: StructuralData,
        active_sustaining_instrument_id: str,
        dynamic: str,
    ):
        sequential_event = events.basic.SequentialEvent(
            [
                events.basic.SimpleEvent(fractions.Fraction(structural_data[3], 4)),
                events.music.NoteLike(
                    [], fractions.Fraction(structural_data[4], 4), dynamic
                ),
            ]
        )
        tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
            [sequential_event], tag=active_sustaining_instrument_id
        )
        time_bracket.append(tagged_simultaneous_event)

    def _add_keyboard_to_time_bracket(
        self,
        time_bracket: cengkoks.CengkokTimeBracket,
        structural_data: StructuralData,
        dynamic: str,
    ):
        sequential_event = events.basic.SequentialEvent([])
        for _ in range(structural_data[3]):
            sequential_event.append(
                events.music.NoteLike([], fractions.Fraction(1, 4), dynamic)
            )

        sequential_event.append(
            events.music.NoteLike(
                [], fractions.Fraction(structural_data[4], 4), dynamic
            )
        )

        if len(sequential_event) >= 4:
            shall_tie = next(self._tie_cycle)
            if shall_tie:
                tie_position_options = []
                for n in range(len(sequential_event) - 3):
                    tie_position_options.append(n)
                tie_position = self._tie_random.choice(tie_position_options)
                tw.eat(sequential_event, tie_position)

        tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
            [sequential_event.copy(), sequential_event.copy()],
            tag=ot2_constants.instruments.ID_KEYBOARD,
        )
        time_bracket.append(tagged_simultaneous_event)

    def _make_time_bracket(
        self, structural_data: StructuralData
    ) -> cengkoks.CengkokTimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = cengkoks.CengkokTimeBracket(
            [],
            structural_data[0],
            structural_data[1],
            [
                abjad.TimeSignature((structural_data[3], 4)),
                abjad.TimeSignature((structural_data[4], 4)),
            ],
            structural_data[2],
            force_spanning_of_end_or_end_range=True,
        )
        time_bracket.force_spanning_of_end_or_end_range = True
        active_sustaining_instruments = tuple(
            self.sustaining_instrument_ids[index]
            for index, is_active in enumerate(
                next(self._responsible_sustaining_instrument_cycle)
            )
            if is_active
        )
        for active_sustaining_instrument_id in active_sustaining_instruments:
            self._add_sustaining_instrument_to_time_bracket(
                time_bracket, structural_data, active_sustaining_instrument_id, dynamic
            )

        self._add_keyboard_to_time_bracket(time_bracket, structural_data, dynamic)

        return time_bracket

    def _distribute_pitches_on_events(
        self,
        pitches_to_distribute: tuple[parameters.pitches.JustIntonationPitch, ...],
        time_bracket: cengkoks.CengkokTimeBracket,
    ):
        n_simultaneous_events = len(time_bracket)
        n_sustaining_instruments = n_simultaneous_events - 1
        if len(pitches_to_distribute) > (n_simultaneous_events + 1):
            sustaining_instrument_pitches = pitches_to_distribute[
                :n_sustaining_instruments
            ]
            keyboard_pitches = pitches_to_distribute[n_sustaining_instruments:]
        else:
            pitches_cycle = itertools.cycle(pitches_to_distribute)
            sustaining_instrument_pitches = tuple(
                next(pitches_cycle) for _ in range(n_sustaining_instruments)
            )
            keyboard_pitches = sorted(tuple(next(pitches_cycle) for _ in range(2)))

        for sustaining_instrument, sustaining_instrument_pitch in zip(
            time_bracket, sustaining_instrument_pitches
        ):
            sustaining_instrument[0][1].pitch_or_pitches = [sustaining_instrument_pitch]
            tw.add_cent_deviation_to_simultaneous_event(sustaining_instrument)

        keyboard_pitches_distribution = tuple(
            utilities.tools.accumulate_from_zero(
                generators.toussaint.euclidean(len(keyboard_pitches), 2)
            )
        )
        left_hand_keyboard_pitches = keyboard_pitches[
            keyboard_pitches_distribution[0] : keyboard_pitches_distribution[1]
        ]
        left_hand_keyboard_pitches = [
            pitch + next(self._left_hand_keyboard_pitches_modification_cycle)
            for pitch in left_hand_keyboard_pitches
        ]
        right_hand_keyboard_pitches = keyboard_pitches[
            keyboard_pitches_distribution[1] : keyboard_pitches_distribution[2]
        ]

        for hand_pitches, hand in zip(
            (right_hand_keyboard_pitches, left_hand_keyboard_pitches), time_bracket[-1]
        ):
            for note in hand:
                note.pitch_or_pitches = hand_pitches

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

    def _make_sine_tones_time_bracket_for_homophonic_chord(
        self, instrumental_time_bracket: events.time_brackets.TimeBracket
    ) -> events.time_brackets.TimeBracket:
        new_time_bracket = instrumental_time_bracket.empty_copy()
        new_time_bracket.flexible_start_range = (
            new_time_bracket.flexible_start_range * 0.2
        )
        new_time_bracket.flexible_end_range = new_time_bracket.flexible_end_range * 0.2
        for tagged_simultaneous_event in instrumental_time_bracket:
            try:
                id_sine = ot2_constants.instruments.ID_SUS_TO_ID_SINE[
                    tagged_simultaneous_event.tag
                ]
            except KeyError:
                pass
            else:
                played_pitch = tuple(
                    filter(
                        lambda pitch: pitch is not None,
                        tagged_simultaneous_event.get_parameter(
                            "pitch_or_pitches", flat=True
                        ),
                    )
                )[0]
                note_like = events.music.NoteLike(played_pitch, 1, "p")
                note_like.attack = self._random_attack.uniform(0.25, 0.4)
                note_like.release = self._random_release.uniform(0.275, 0.4)
                sine_tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([note_like])], tag=id_sine
                )
                new_time_bracket.append(sine_tagged_simultaneous_event)

        return new_time_bracket

    def convert(
        self,
        start_time: parameters.abc.DurationType,
    ) -> tuple[events.time_brackets.TimeBracket, ...]:
        structural_data = self._find_structural_data_for_homophonic_event(start_time)
        n_pitches = next(self._n_pitches_cycle)
        pitches = self._find_pitches(structural_data[0], structural_data[1], n_pitches)
        if pitches:
            time_bracket = self._make_time_bracket(structural_data)
            time_bracket.engine_distribution_strategy = (
                keyboard.SimpleEngineDistributionStrategy(2)
            )
            self._distribute_pitches_on_events(pitches, time_bracket)
            sines_time_bracket = (
                self._make_sine_tones_time_bracket_for_homophonic_chord(time_bracket)
            )
            return (time_bracket, sines_time_bracket)
        return tuple([])
