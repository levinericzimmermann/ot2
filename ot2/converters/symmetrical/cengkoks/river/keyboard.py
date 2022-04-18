import abc
import copy
import fractions
import functools
import itertools
import operator
import typing


import abjad
import expenvelope
import numpy as np

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters
from mutwo import utilities

from ot2 import parameters as ot2_parameters

from . import structure


class RhythmMutation(object):
    def __init__(
        self,
        rhythmical_gestalt_to_mutated_gestalt: typing.Dict[
            typing.Tuple[fractions.Fraction, ...], generators.generic.DynamicChoice
        ],
    ):
        self._rhythmical_gestalt_to_mutated_gestalt = (
            rhythmical_gestalt_to_mutated_gestalt
        )
        self._rhythmical_gestalt_sizes = tuple(
            sorted(
                set(
                    sum(rhythmical_gestalt)
                    for rhythmical_gestalt in rhythmical_gestalt_to_mutated_gestalt.keys()
                ),
                reverse=True,
            )
        )

    def __call__(
        self,
        sequential_event_to_process: events.basic.SequentialEvent[
            events.music.NoteLike
        ],
    ):
        grid_to_scan = events.basic.SequentialEvent(
            [
                events.basic.SimpleEvent(self._rhythmical_gestalt_sizes[0])
                for _ in range(
                    int(
                        sequential_event_to_process.duration
                        / self._rhythmical_gestalt_sizes[0]
                    )
                )
            ]
        )
        start_and_end_time_per_event_for_sequential_event_to_process = (
            sequential_event_to_process.start_and_end_time_per_event
        )
        start_times, end_times = zip(
            *start_and_end_time_per_event_for_sequential_event_to_process
        )
        for start, end in grid_to_scan.start_and_end_time_per_event:
            if start in start_times and end in end_times:
                start_index, end_index = start_times.index(start), end_times.index(end)
                rhythmical_gestalt = tuple(
                    map(
                        fractions.Fraction,
                        sequential_event_to_process.get_parameter("duration")[
                            start_index : end_index + 1
                        ],
                    )
                )
                if rhythmical_gestalt in self._rhythmical_gestalt_to_mutated_gestalt:
                    absolute_position = start / end_times[-1]
                    if mutated_gestalt := self._rhythmical_gestalt_to_mutated_gestalt[
                        rhythmical_gestalt
                    ].gamble_at(absolute_position):
                        for index, rhythm in zip(
                            range(start_index, end_index + 1), mutated_gestalt
                        ):
                            sequential_event_to_process[index].duration = rhythm


class TieMutation(object):
    def __init__(
        self,
        absolute_tie_percentage: float,
        tie_likelihood_curve: expenvelope.Envelope,
        seed: int = 5,
    ):
        self._absolute_tie_percentage = absolute_tie_percentage
        self._tie_likelihood_curve = tie_likelihood_curve
        self._random = np.random.default_rng(seed)

    def _tie(
        self,
        sequential_event_to_process: events.basic.SequentialEvent[
            events.music.NoteLike
        ],
    ):
        indices = []
        weights = []
        duration = sequential_event_to_process.duration
        durations = tuple(
            sorted(
                set(sequential_event_to_process.get_parameter("duration")), reverse=True
            )
        )
        n_different_durations = len(durations) - 1

        cent_gain_per_event = []
        for note_like0, note_like1, note_like2 in zip(
            sequential_event_to_process,
            sequential_event_to_process[1:],
            sequential_event_to_process[2:],
        ):
            if (
                note_like0.pitch_or_pitches
                and note_like1.pitch_or_pitches
                and note_like2.pitch_or_pitches
                and note_like0.pitch_or_pitches != note_like2.pitch_or_pitches
            ):
                current_distance = abs(
                    (
                        note_like0.pitch_or_pitches[0] - note_like1.pitch_or_pitches[0]
                    ).cents
                )
                new_distance = abs(
                    (
                        note_like0.pitch_or_pitches[0] - note_like2.pitch_or_pitches[0]
                    ).cents
                )
                gain = current_distance - new_distance
                if gain < 0:
                    gain = 0
                cent_gain_per_event.append(gain)
            else:
                cent_gain_per_event.append(0)

        max_cent_gain = max(cent_gain_per_event)

        for index, absolute_time, note_like0, note_like1 in zip(
            range(len(sequential_event_to_process)),
            sequential_event_to_process.absolute_times,
            sequential_event_to_process,
            sequential_event_to_process[1:],
        ):
            if not note_like1.is_goal and note_like0.pitch_or_pitches:
                absolute_position = absolute_time / duration
                position_likelihood = self._tie_likelihood_curve.value_at(
                    absolute_position
                )
                is_goal_likelihood = note_like0.is_goal
                if n_different_durations:
                    duration_likelihood = (
                        durations.index(note_like0.duration) / n_different_durations
                    )
                else:
                    duration_likelihood = 1
                if max_cent_gain:
                    pitch_likelihood = cent_gain_per_event[index] / max_cent_gain
                else:
                    pitch_likelihood = 0
                likelihood = (
                    (pitch_likelihood * 0.65)
                    + (duration_likelihood * 0.25)
                    + (is_goal_likelihood * 0.1)
                ) * position_likelihood

                indices.append(index)
                weights.append(likelihood)

        choosen_index_to_tie = self._random.choice(
            indices, p=utilities.tools.scale_sequence_to_sum(weights, 1)
        )

        sequential_event_to_process[
            choosen_index_to_tie
        ].duration += sequential_event_to_process[choosen_index_to_tie + 1].duration
        del sequential_event_to_process[choosen_index_to_tie + 1]

    def __call__(
        self,
        sequential_event_to_process: events.basic.SequentialEvent,
        restructured_phrase_parts: typing.Tuple,
    ):
        n_not_tiable_notes = len(restructured_phrase_parts)
        n_notes = len(sequential_event_to_process)
        n_tiable_notes = n_notes - n_not_tiable_notes
        n_notes_to_tie = int(self._absolute_tie_percentage * n_tiable_notes)
        for _ in range(n_notes_to_tie):
            self._tie(sequential_event_to_process)


DEFAULT_RHYTHMICAL_GESTALT_TO_MUTATED_GESTALT = {
    (
        fractions.Fraction(1, 8),
        fractions.Fraction(1, 8),
        fractions.Fraction(1, 8),
        fractions.Fraction(1, 8),
    ): generators.generic.DynamicChoice(
        (
            None,
            (
                fractions.Fraction(1, 6),
                fractions.Fraction(1, 12),
                fractions.Fraction(1, 12),
                fractions.Fraction(1, 6),
            ),
            (
                fractions.Fraction(1, 8),
                fractions.Fraction(1, 8),
                fractions.Fraction(3, 16),
                fractions.Fraction(1, 16),
            ),
            (
                fractions.Fraction(1, 8),
                fractions.Fraction(3, 16),
                fractions.Fraction(1, 16),
                fractions.Fraction(1, 8),
            ),
            (
                fractions.Fraction(1, 8),
                fractions.Fraction(3, 16),
                fractions.Fraction(1, 8),
                fractions.Fraction(1, 16),
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 2.15), (1, 2.15)),
            expenvelope.Envelope.from_points((0, 0.3), (1, 0.3)),
            expenvelope.Envelope.from_points((0, 0.4), (1, 0.4)),
            expenvelope.Envelope.from_points((0, 0.1), (1, 0.1)),
            expenvelope.Envelope.from_points((0, 0.1), (1, 0.1)),
        ),
    ),
    (
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 4),
    ): generators.generic.DynamicChoice(
        (
            None,
            (
                fractions.Fraction(3, 8),
                fractions.Fraction(1, 8),
            ),
            (
                fractions.Fraction(1, 3),
                fractions.Fraction(1, 6),
            ),
            (
                fractions.Fraction(1, 6),
                fractions.Fraction(1, 3),
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 1.9), (1, 1.9)),
            expenvelope.Envelope.from_points((0, 0.4), (1, 0.4)),
            expenvelope.Envelope.from_points((0, 0.6), (1, 0.6)),
            expenvelope.Envelope.from_points((0, 0.35), (1, 0.35)),
        ),
    ),
}


class RestructuredPhrasePartToCengkokPartConverter(converters.abc.Converter):
    def convert(
        self, restructured_phrase_part_to_convert: structure.RestructuredPhrasePart
    ) -> events.basic.SequentialEvent:
        pass


class RestructuredPhrasePartsToVirtualCengkokLineConverter(object):
    def __init__(
        self,
        rhythmical_gestalt_to_mutated_gestalt: typing.Dict[
            typing.Tuple[fractions.Fraction, ...], generators.generic.DynamicChoice
        ] = DEFAULT_RHYTHMICAL_GESTALT_TO_MUTATED_GESTALT,
        absolute_tie_percentage: float = 0.12,
        tie_likelihood_curve: expenvelope.Envelope = expenvelope.Envelope.from_points(
            (0, 1), (0.5, 0.7), (1, 1)
        ),
        irama: int = 1,
        modulation_pitch: parameters.pitches.JustIntonationPitch = parameters.pitches.JustIntonationPitch(
            "1/2"
        ),
    ):
        self._rhythm_mutation = RhythmMutation(rhythmical_gestalt_to_mutated_gestalt)
        self._tie_mutation = TieMutation(absolute_tie_percentage, tie_likelihood_curve)
        self._irama = irama
        self._added_delay_size = fractions.Fraction(1, 4 * (2 ** (irama - 1)))
        self._modulation_pitch = modulation_pitch

        if irama == 1:
            assert self._added_delay_size == fractions.Fraction(1, 4)
        elif irama == 2:
            assert self._added_delay_size == fractions.Fraction(1, 8)
        elif irama == 3:
            assert self._added_delay_size == fractions.Fraction(1, 16)

    def _get_cengkoks_with_passed_start_candidate(
        self,
        start_cengkok: events.basic.SequentialEvent,
        converted_cengkok_candidates_per_phrase_part: typing.Tuple[
            typing.Tuple[events.basic.SequentialEvent, ...], ...
        ],
    ) -> typing.Tuple[events.basic.SequentialEvent, float]:
        summed_distance = 0
        for note in start_cengkok:
            note.is_goal = False
        start_cengkok[-1].is_goal = True
        cengkoks = [start_cengkok]
        for (
            converted_cengkok_candidates
        ) in converted_cengkok_candidates_per_phrase_part[1:]:
            previous_cengkok = cengkoks[-1]
            previous_pitch = previous_cengkok[-1].pitch_or_pitches[0]
            candidate_and_fitness_pairs = []
            for candidate in converted_cengkok_candidates:
                index = 0
                first_pitch = None
                while not first_pitch:
                    if pitch_or_pitches := candidate[index].pitch_or_pitches:
                        first_pitch = pitch_or_pitches[0]
                    index += 1
                if first_pitch != previous_pitch:
                    distance = abs((first_pitch - previous_pitch).cents)
                else:
                    distance = (
                        1000000  # only repeat pitches if no other candidate exist
                    )
                candidate_and_fitness_pairs.append((candidate, distance))
            best, distance = min(
                candidate_and_fitness_pairs, key=operator.itemgetter(1)
            )
            for note in best:
                note.is_goal = False
            best[-1].is_goal = True
            summed_distance += distance
            cengkoks.append(best)
        return tuple(cengkoks), summed_distance

    def _get_best_cengkok_chain(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ) -> typing.Tuple[events.basic.SequentialEvent, ...]:
        converted_cengkok_candidates_per_phrase_part = tuple(
            tuple(
                map(
                    restructured_phrase_part.convert_cengkok,
                    restructured_phrase_part.filter_cengkok_candidates(
                        irama=self._irama
                    ),
                )
            )
            for restructured_phrase_part in restructured_phrase_parts
        )

        cengkoks_and_fitness_pairs = []
        for cengkok in converted_cengkok_candidates_per_phrase_part[0]:
            cengkoks_and_fitness_pairs.append(
                self._get_cengkoks_with_passed_start_candidate(
                    cengkok, converted_cengkok_candidates_per_phrase_part
                )
            )

        best_cengkoks, _ = min(cengkoks_and_fitness_pairs, key=operator.itemgetter(1))

        return tuple(best_cengkoks)

    def _split_concatenated_cengkok_chain_to_cengkok_chain(
        self, concatenated_cengkok_chain: events.basic.SequentialEvent
    ) -> typing.Tuple[events.basic.SequentialEvent, ...]:
        concatenated_cengkok_chain.cut_off(0, self._added_delay_size)
        cengkok_chain = [events.basic.SequentialEvent([])]
        for index, event in enumerate(concatenated_cengkok_chain):
            cengkok_chain[-1].append(event)
            if event.is_goal and index + 1 != len(concatenated_cengkok_chain):
                cengkok_chain.append(events.basic.SequentialEvent([]))
        return cengkok_chain

    def _split_concatenated_cengkok_chain_to_bars(
        self,
        concatenated_cengkok_chain: events.basic.SequentialEvent,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ):
        bars = events.basic.SequentialEvent([events.basic.SequentialEvent([])])
        for index, event in enumerate(concatenated_cengkok_chain):
            if event.is_goal:
                bars.append(events.basic.SequentialEvent([]))
            bars[-1].append(event)
        bars = bars[:-1]

        for bar, restructured_phrase_part in zip(bars, restructured_phrase_parts):
            difference = restructured_phrase_part.duration - bar.duration
            bar[0].duration += difference
            if bar[0].duration <= 0:
                bar = bar[1:]
                print("Warning: HAD TO REMOVE GOAL")

        assert len(bars) == len(restructured_phrase_parts)
        for bar, restructured_phrase_part in zip(bars, restructured_phrase_parts):
            assert bar.duration == restructured_phrase_part.duration

        return bars

    def convert(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ) -> typing.Tuple[events.basic.SequentialEvent, ...]:
        cengkok_chain = self._get_best_cengkok_chain(restructured_phrase_parts)

        concatenated_cengkok_chain = functools.reduce(operator.add, cengkok_chain)
        delay = events.music.NoteLike([], self._added_delay_size)
        delay.is_goal = False
        concatenated_cengkok_chain.insert(0, delay)

        # 1. Apply rhythm mutation
        self._rhythm_mutation(concatenated_cengkok_chain)

        # 2. Recursively add ties
        self._tie_mutation(concatenated_cengkok_chain, restructured_phrase_parts)

        # 3. Remove single events for building rests

        # 4. Add chords

        # adjust pitches
        concatenated_cengkok_chain.set_parameter(
            "pitch_or_pitches",
            lambda pitch_or_pitches: [
                pitch + self._modulation_pitch for pitch in pitch_or_pitches
            ]
            if pitch_or_pitches
            else pitch_or_pitches,
        )

        concatenated_cengkok_chain.set_parameter(
            "volume", parameters.volumes.WesternVolume("p")
        )
        bars = self._split_concatenated_cengkok_chain_to_bars(
            concatenated_cengkok_chain, restructured_phrase_parts
        )
        return bars


class CengkokAdaption(object):
    def __init__(self, restructured_phrase_parts):
        self._restructured_phrase_parts = restructured_phrase_parts

    @abc.abstractmethod
    def __call__(
        self,
        bar_to_adapt: events.basic.SequentialEvent,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
    ) -> events.basic.SequentialEvent:
        raise NotImplementedError


class AdaptCenkokEnding(CengkokAdaption):
    def __call__(
        self,
        bar_to_adapt: events.basic.SequentialEvent,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
    ) -> events.basic.SequentialEvent:
        bar_to_adapt = bar_to_adapt.copy()
        bar_to_adapt[0].duration = bar_to_adapt.duration
        for _ in bar_to_adapt[1:]:
            del bar_to_adapt[1]
        bar_to_adapt[0].pitch_or_pitches[0].register(-1)
        bar_to_adapt[0].pitch_or_pitches[0].add(modulation_pitch)
        return bar_to_adapt


class AdaptCenkokStart(CengkokAdaption):
    def __call__(
        self,
        bar_to_adapt: events.basic.SequentialEvent,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
    ) -> events.basic.SequentialEvent:
        n_tones_to_rest = int(len(bar_to_adapt) * 0.8)
        duration_of_rest_tones = bar_to_adapt[:n_tones_to_rest].duration
        new_bar = events.basic.SequentialEvent(
            [events.basic.SimpleEvent(duration_of_rest_tones)]
        )
        for event in bar_to_adapt[n_tones_to_rest:]:
            new_bar.append(copy.copy(event))
        return new_bar


class AdaptCenkokCadenza(CengkokAdaption):
    def __call__(
        self,
        bar_to_adapt: events.basic.SequentialEvent,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
    ) -> events.basic.SequentialEvent:
        # return bar_to_adapt

        goal_pitch = self._restructured_phrase_parts[nth_bar].connection_pitch1
        if not goal_pitch:
            try:
                goal_pitch = self._restructured_phrase_parts[nth_bar + 1].root
            except IndexError:
                goal_pitch = self._restructured_phrase_parts[nth_bar].root

        goal_pitch.register(-1)
        goal_pitch.add(modulation_pitch)

        start_pitch = bar_to_adapt[0].pitch_or_pitches[0]

        if start_pitch == goal_pitch:
            return bar_to_adapt.copy()

        sorted_goal_and_start_pitch = sorted((goal_pitch, start_pitch))

        ambitus = ot2_parameters.ambitus.Ambitus(*sorted_goal_and_start_pitch)

        pitch_line = [start_pitch, goal_pitch]
        for pitch in self._restructured_phrase_parts[nth_bar].all_pitches:
            for pitch_variant in ambitus.find_all_pitch_variants(pitch):
                if pitch_variant not in pitch_line:
                    pitch_line.append(pitch_variant)

        sorted_pitch_line = sorted(
            pitch_line, reverse=start_pitch == sorted_goal_and_start_pitch[1]
        )[:-1]
        n_pitches_in_pitch_line = len(sorted_pitch_line)

        advanced_pitch_line = functools.reduce(
            operator.add,
            zip(
                sorted_pitch_line,
                sorted_pitch_line[2:] + list(reversed(sorted_pitch_line[-2:])),
            ),
        )

        advanced_pitch_line = sorted_pitch_line

        n_factor = 1
        n_needed_beats = n_pitches_in_pitch_line * n_factor

        available_duration = bar_to_adapt.duration

        pulse_size = available_duration
        n_pulses = 1
        while n_pulses < n_needed_beats:
            pulse_size /= 2
            n_pulses = int(available_duration / pulse_size)

        rhythm = generators.toussaint.euclidean(n_pulses, n_needed_beats)
        cadential_bar = events.basic.SequentialEvent([])
        for n_beats, pitch in zip(rhythm, advanced_pitch_line):
            note = events.music.NoteLike(
                [pitch], duration=n_beats * pulse_size, volume="p"
            )
            cadential_bar.append(note)

        try:
            cadential_bar[-2].pitch_or_pitches = [goal_pitch]
        except IndexError:
            cadential_bar[-1].pitch_or_pitches = [goal_pitch]

        assert cadential_bar.duration == bar_to_adapt.duration

        return cadential_bar


class AdaptCenkokMoving(CengkokAdaption):
    gantungan_al = generators.edwards.ActivityLevel(1)
    activity_level = 3

    arpeggio_al = generators.edwards.ActivityLevel(0)
    arpeggio_activity_level = 3
    arpeggio_direction_al = generators.edwards.ActivityLevel(0)
    arpeggio_direction_activity_level = 5

    """
    gantungan_pattern_cycle = itertools.cycle(
        (
            ((fractions.Fraction(1, 6), False), (fractions.Fraction(1, 12), True)),
            ((fractions.Fraction(1, 8), False), (fractions.Fraction(1, 8), True)),
            ((fractions.Fraction(3, 16), False), (fractions.Fraction(1, 16), True)),
            ((fractions.Fraction(1, 8), False), (fractions.Fraction(1, 8), True)),
        )
    )
    gantungan_pattern_duration = fractions.Fraction(1, 4)
    """
    gantungan_pattern_duration = fractions.Fraction(1, 2)
    gantungan_pattern_cycle = itertools.cycle(
        (
            ((fractions.Fraction(1, 3), False), (fractions.Fraction(1, 6), True)),
            ((fractions.Fraction(1, 4), False), (fractions.Fraction(1, 4), True)),
            ((fractions.Fraction(3, 8), False), (fractions.Fraction(1, 8), True)),
            ((fractions.Fraction(1, 4), False), (fractions.Fraction(1, 4), True)),
        )
    )

    def _detect_gantungan_event_pitch_or_pitches(
        self,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
        nth_gantungan_pattern_percentage: float,
    ) -> list[parameters.pitches.JustIntonationPitch]:
        current_restructured_phrase_part = self._restructured_phrase_parts[nth_bar]
        connection_pitch0, connection_pitch1 = (
            current_restructured_phrase_part.connection_pitch0,
            current_restructured_phrase_part.connection_pitch1,
        )
        if not connection_pitch0:
            connection_pitch0 = current_restructured_phrase_part.root
        if not connection_pitch1:
            connection_pitch1 = current_restructured_phrase_part.root

        connection_pitch0 += modulation_pitch
        connection_pitch1 += modulation_pitch

        if connection_pitch0 == connection_pitch1:
            pitch_or_pitches = [connection_pitch0]
        else:
            absolute_distance = abs((connection_pitch0 - connection_pitch1).cents)
            if absolute_distance > 270 and absolute_distance < 900:
                pitch_or_pitches = [
                    connection_pitch0,
                    connection_pitch1,
                ]
            else:
                if nth_gantungan_pattern_percentage > 0.5:
                    pitch_or_pitches = [connection_pitch1]
                else:
                    pitch_or_pitches = [connection_pitch0]
        return pitch_or_pitches

    def _convert_gantungan_pattern_to_sequential_event(
        self,
        gantungan_pattern_to_convert: tuple[tuple[fractions.Fraction, bool], ...],
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
        nth_gantungan_pattern_percentage: float,
    ):
        sequential_event = events.basic.SequentialEvent([])
        for event_duration, is_tone in gantungan_pattern_to_convert:
            if is_tone:
                pitch_or_pitches = self._detect_gantungan_event_pitch_or_pitches(
                    nth_bar, modulation_pitch, nth_gantungan_pattern_percentage
                )
                event = events.music.NoteLike(pitch_or_pitches, event_duration, "p")
                if len(pitch_or_pitches) > 1:
                    if self.arpeggio_al(self.arpeggio_activity_level):
                        if self.arpeggio_direction_al(
                            self.arpeggio_direction_activity_level
                        ):
                            direction = abjad.enums.Up
                        else:
                            direction = abjad.enums.Down
                        event.playing_indicators.arpeggio.direction = direction
            else:
                event = events.basic.SimpleEvent(event_duration)
            sequential_event.append(event)
        return sequential_event

    def _add_gantungan(
        self,
        bar_to_adapt: events.basic.SequentialEvent,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
    ) -> events.basic.SequentialEvent:
        adapted_bar = bar_to_adapt.copy()
        to_remain = self.gantungan_pattern_duration
        absolute_times = adapted_bar.absolute_times
        items_to_remain = 1
        for absolute_time in reversed(absolute_times):
            if absolute_time % to_remain == 0:
                break
            else:
                items_to_remain += 1
        adapted_bar = adapted_bar[-items_to_remain:]
        free_space = bar_to_adapt.duration - adapted_bar.duration
        if free_space:
            n_gantungan_pattern = int(free_space // to_remain)
            gantungan = events.basic.SequentialEvent([])
            for nth_gantungan_pattern in range(n_gantungan_pattern):
                nth_gantungan_pattern_percentage = nth_gantungan_pattern / (
                    n_gantungan_pattern
                )
                gantungan_pattern = next(self.gantungan_pattern_cycle)
                gantungan.extend(
                    self._convert_gantungan_pattern_to_sequential_event(
                        gantungan_pattern,
                        nth_bar,
                        modulation_pitch,
                        nth_gantungan_pattern_percentage,
                    )
                )
            adapted_bar = gantungan + adapted_bar
        assert adapted_bar.duration == bar_to_adapt.duration
        return adapted_bar

    def __call__(
        self,
        bar_to_adapt: events.basic.SequentialEvent,
        nth_bar: int,
        modulation_pitch: parameters.pitches.JustIntonationPitch,
    ) -> events.basic.SequentialEvent:
        if self.gantungan_al(self.activity_level):
            return self._add_gantungan(bar_to_adapt, nth_bar, modulation_pitch)
        else:
            return bar_to_adapt.copy()


class RestructuredPhrasePartsToCengkokLineConverter(converters.abc.Converter):
    character_to_adaption_blueprint = {
        structure.START: AdaptCenkokStart,
        structure.MOVING: AdaptCenkokMoving,
        structure.CADENZA: AdaptCenkokCadenza,
        structure.END: AdaptCenkokEnding,
    }

    def __init__(
        self,
        restructured_phrase_parts_to_virtual_cengkok_line_converter: RestructuredPhrasePartsToVirtualCengkokLineConverter = RestructuredPhrasePartsToVirtualCengkokLineConverter(),
    ):
        self._restructured_phrase_parts_to_virtual_cengkok_line_converter = (
            restructured_phrase_parts_to_virtual_cengkok_line_converter
        )

    def _adapt_phrase_part_characters(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        bars: events.basic.SequentialEvent[events.basic.SequentialEvent],
    ) -> events.basic.SequentialEvent[events.basic.SequentialEvent]:
        new_bars = events.basic.SequentialEvent([])
        for phrase_part, bar, nth_bar in zip(
            restructured_phrase_parts, bars, range(len(bars))
        ):
            character = phrase_part.bar_character
            if character in self._character_to_adaption:
                new_bar = self._character_to_adaption[character](
                    bar,
                    nth_bar,
                    self._restructured_phrase_parts_to_virtual_cengkok_line_converter._modulation_pitch,
                )
                assert new_bar.duration == bar.duration
            else:
                new_bar = bar.copy()
            new_bars.append(new_bar)

        return new_bars

    def convert(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ) -> typing.Tuple[events.basic.SequentialEvent, ...]:
        self._character_to_adaption = {
            character: blueprint(restructured_phrase_parts)
            for character, blueprint in self.character_to_adaption_blueprint.items()
        }

        # first build general purpose / moving cengkok bars
        bars = (
            self._restructured_phrase_parts_to_virtual_cengkok_line_converter.convert(
                restructured_phrase_parts
            )
        )
        # then postprocess bars according to the musical structure
        bars = self._adapt_phrase_part_characters(restructured_phrase_parts, bars)
        # finally: concatenate bars to one sequential event
        concatenated_bars = functools.reduce(operator.add, bars)
        """
        # then tie notes
        concatenated_bars.tie_by(
            lambda ev0, ev1: hasattr(ev0, "pitch_or_pitches")
            and hasattr(ev1, "pitch_or_pitches")
            and (
                (
                    ev0.pitch_or_pitches
                    and ev1.pitch_or_pitches
                    and ev0.pitch_or_pitches[0].normalize(mutate=False)
                    == ev1.pitch_or_pitches[0].normalize(mutate=False)
                    and len(ev0.pitch_or_pitches) == 1
                    and len(ev1.pitch_or_pitches) == 1
                    and ev1.duration.denominator == ev0.duration.denominator
                )
                or (ev0.pitch_or_pitches == ev1.pitch_or_pitches)
            )
        )
        """
        for ev0, ev1 in zip(concatenated_bars, concatenated_bars[1:]):
            if hasattr(ev0, "pitch_or_pitches") and hasattr(ev1, "pitch_or_pitches"):
                """
                for pitch in ev0.pitch_or_pitches:
                    if pitch in ev1.pitch_or_pitches:
                        ev0.playing_indicators.tie.is_active = True
                """
                if len(ev0.pitch_or_pitches) == 1 and len(ev1.pitch_or_pitches) == 1:
                    if ev0.pitch_or_pitches[0].normalize(
                        mutate=False
                    ) == ev1.pitch_or_pitches[0].normalize(mutate=False):
                        ev1.pitch_or_pitches = []
        return concatenated_bars


class RestructuredPhrasePartsAndCengkokLineToCounterVoiceConverter(object):
    _prohibit_common_beats_factor = (
        0.5  # factor to reduce the likelihood of common beats
    )
    cadenza_grid_step_size = fractions.Fraction(1, 12)
    cadenza_density = 0.6
    prolong_al_generator = generators.edwards.ActivityLevel()
    prolong_al = 7

    def __init__(
        self,
        density_curve: expenvelope.Envelope = expenvelope.Envelope.from_points(
            (0, 0.2), (0.5, 0.45), (1, 0.2)
        ),
        position_to_grid_step_size_likelihood: generators.generic.DynamicChoice = generators.generic.DynamicChoice(
            # (
            #     fractions.Fraction(1, 8),
            #     fractions.Fraction(1, 16),
            #     fractions.Fraction(1, 12),
            # ),
            (
                fractions.Fraction(1, 8),
                fractions.Fraction(1, 16),
                fractions.Fraction(1, 12),
            ),
            (
                expenvelope.Envelope.from_points(
                    (0, 1), (0.3, 0.9), (0.5, 0.1), (0.75, 0), (1, 1)
                ),
                expenvelope.Envelope.from_points(
                    (0, 0.3), (0.3, 0.4), (0.5, 1), (0.75, 0.8), (1, 0)
                ),
                # expenvelope.Envelope.from_points(
                #     (0, 0.3), (0.3, 0.3), (0.5, 0.8), (0.75, 0.3), (1, 0.3)
                # ),
                expenvelope.Envelope.from_points(
                    (0, 0), (0.3, 0.1), (0.6, 0.8), (0.75, 0.9), (1, 0.0)
                ),
            ),
        ),
        seed: int = 3123,
    ):
        self._density_curve = density_curve
        self._random = np.random.default_rng(seed)
        self._position_to_grid_step_size_likelihood = (
            position_to_grid_step_size_likelihood
        )
        self._root_change_interval = parameters.pitches.JustIntonationPitch("4/1")
        self._ambitus_interval = parameters.pitches.JustIntonationPitch("4/3")

    def _make_grid_blueprints(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ) -> typing.Tuple[typing.Tuple[fractions.Fraction, typing.Tuple[float, ...]], ...]:
        rhythmical_strata_to_indispensability_converter = (
            converters.symmetrical.metricities.RhythmicalStrataToIndispensabilityConverter()
        )
        grids = []
        complete_duration = restructured_phrase_parts.duration
        for absolute_time, restructured_phrase_part in zip(
            restructured_phrase_parts.absolute_times, restructured_phrase_parts
        ):
            absolute_position = absolute_time / complete_duration
            if restructured_phrase_part.bar_character == structure.CADENZA:
                grid_step_size = self.cadenza_grid_step_size
            else:
                grid_step_size = self._position_to_grid_step_size_likelihood.gamble_at(
                    absolute_position
                )
            prime_factors = utilities.prime_factors.factorise(
                int(restructured_phrase_part.duration * grid_step_size.denominator)
            )
            grid = rhythmical_strata_to_indispensability_converter.convert(
                prime_factors
            )
            scaled_grid = tuple(
                map(
                    lambda number: utilities.tools.scale(
                        number, min(grid), max(grid), 0, 1
                    ),
                    grid,
                )
            )
            grids.append((grid_step_size, scaled_grid))

        return tuple(grids)

    def _adjust_grids_by_cengkok_line(
        self,
        grids: typing.Tuple[
            typing.Tuple[fractions.Fraction, typing.Tuple[float, ...]], ...
        ],
        cengkok_line: events.basic.SequentialEvent[events.music.NoteLike],
    ):
        # adjust grids by rhythm of cengkok line (reduce likelihood if there is already
        # a note of the cengkok line)
        cengkok_line_absolute_times = cengkok_line.absolute_times
        grid_delay = 0
        adjusted_grids = []
        for grid_step_size, grid in grids:
            adjusted_grid = list(grid)
            for nth_grid_position, factor in enumerate(grid):
                if grid_delay in cengkok_line_absolute_times:
                    new_factor = factor * self._prohibit_common_beats_factor
                    adjusted_grid[nth_grid_position] = new_factor
                grid_delay += grid_step_size
            adjusted_grids.append((grid_step_size, tuple(adjusted_grid)))
        return adjusted_grids

    def _make_grids(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        cengkok_line: events.basic.SequentialEvent[events.music.NoteLike],
    ) -> typing.Tuple[typing.Tuple[fractions.Fraction, typing.Tuple[float, ...]], ...]:
        grid_blueprints = self._make_grid_blueprints(restructured_phrase_parts)
        grids = self._adjust_grids_by_cengkok_line(grid_blueprints, cengkok_line)
        return grids

    @staticmethod
    def _sort_legal_pitches(
        cengkok_part_per_event, choices, legal_pitches_to_sort, last_pitch
    ):
        distance_per_pitch = tuple(
            map(
                lambda pitch: abs((pitch - last_pitch).cents),
                legal_pitches_to_sort,
            )
        )
        sorted_distances = sorted(set(distance_per_pitch), reverse=True)
        n_distances = len(sorted_distances) - 1

        current_cengkok_part = cengkok_part_per_event[len(choices) - 1]
        current_cengkok_part_duration = current_cengkok_part.duration

        harmonicity_per_legal_pitch = []
        for pitch in legal_pitches_to_sort:
            harmonicities = [0]
            for note in current_cengkok_part:
                if hasattr(note, "pitch_or_pitches") and note.pitch_or_pitches:
                    for note_pitch in note.pitch_or_pitches:
                        interval = pitch - note_pitch
                        interval.normalize()
                        harmonicities.append(
                            interval.harmonicity_simplified_barlow
                            * (note.duration / current_cengkok_part_duration),
                        )
            harmonicity = sum(harmonicities)
            harmonicity_per_legal_pitch.append(harmonicity)

        sorted_harmonicities = sorted(set(harmonicity_per_legal_pitch))
        n_harmonicities = len(sorted_harmonicities) - 1

        def key(pitch):
            legal_pitch_index = legal_pitches_to_sort.index(pitch)
            distance_percentage = (
                sorted_distances.index(distance_per_pitch[legal_pitch_index])
                / n_distances
            )
            if n_harmonicities:
                harmonicity_percentage = (
                    sorted_harmonicities.index(
                        harmonicity_per_legal_pitch[legal_pitch_index]
                    )
                    / n_harmonicities
                )
            else:
                harmonicity_percentage = 1
            return (distance_percentage + harmonicity_percentage) / 2

        legal_pitches = sorted(
            legal_pitches_to_sort,
            key=key,
        )
        return legal_pitches

    def _get_pitches_by_backtracking(
        self,
        ambitus: ot2_parameters.ambitus.Ambitus,
        start_pitch: parameters.pitches.JustIntonationPitch,
        end_pitch: parameters.pitches.JustIntonationPitch,
        cengkok_extract: events.basic.SequentialEvent,
        rhythm: events.basic.SequentialEvent,
        restructured_phrase_part: structure.RestructuredPhrasePart,
    ) -> typing.Sequence[parameters.pitches.JustIntonationPitch]:
        def is_valid(choices, choice_indices) -> bool:
            elements = tuple(
                choice[index] for index, choice in zip(choice_indices, choices)
            )
            are_in_ambitus = all(map(ambitus.is_member, elements))
            is_close_enough_to_goal_pitch = True
            if len(elements) == len(rhythm):
                is_close_enough_to_goal_pitch = (
                    abs((elements[-1] - end_pitch).cents) < 280
                )
            return are_in_ambitus and is_close_enough_to_goal_pitch

        def find_choices():
            last_pitch = choices[-1][choice_indices[-1]]
            available_pitches = restructured_phrase_part.phrase_event.all_pitches
            valid_ambitus = ot2_parameters.ambitus.Ambitus(
                last_pitch - parameters.pitches.JustIntonationPitch("5/4"),
                last_pitch + parameters.pitches.JustIntonationPitch("5/4"),
            )
            legal_pitches = []
            for pitch in available_pitches:
                variants = valid_ambitus.find_all_pitch_variants(pitch)
                for variant in variants:
                    if variant != last_pitch:
                        legal_pitches.append(variant)
            legal_pitches = RestructuredPhrasePartsAndCengkokLineToCounterVoiceConverter._sort_legal_pitches(
                cengkok_part_per_event, choices, legal_pitches, last_pitch
            )
            return legal_pitches

        cengkok_part_per_event = tuple(
            cengkok_extract.cut_out(start, end, mutate=False)
            for start, end in rhythm.start_and_end_time_per_event
        )

        choices = [(start_pitch,)]
        choice_indices = [0]
        # backtracking algorithm
        while True:
            if is_valid(choices, choice_indices):
                if len(choices) < len(rhythm):
                    choices.append(find_choices())
                    choice_indices.append(0)
                else:
                    break
            else:
                while choice_indices[-1] + 1 == len(choices[-1]):
                    choice_indices = choice_indices[:-1]
                    choices = choices[:-1]
                    if len(choices) == 0:
                        raise ValueError("No solution found")

                choice_indices[-1] += 1

        pitches = tuple(choice[index] for index, choice in zip(choice_indices, choices))
        return pitches

    def _assign_pitches(
        self,
        rhythm: events.basic.SequentialEvent[events.music.NoteLike],
        restructured_phrase_part: structure.RestructuredPhrasePart,
        next_restructured_phrase_part: typing.Optional[
            structure.RestructuredPhrasePart
        ],
        cengkok_extract: events.basic.SequentialEvent[events.music.NoteLike],
    ):
        start_pitch = (
            restructured_phrase_part.phrase_event.root + self._root_change_interval
        )
        if next_restructured_phrase_part:
            end_pitch = (
                next_restructured_phrase_part.phrase_event.root
                + self._root_change_interval
            )
        else:
            end_pitch = start_pitch

        start_and_end_pitches = (start_pitch, end_pitch)
        ambitus = ot2_parameters.ambitus.Ambitus(
            min(start_and_end_pitches) - self._ambitus_interval,
            max(start_and_end_pitches) + self._ambitus_interval,
        )

        pitches = self._get_pitches_by_backtracking(
            ambitus,
            start_pitch,
            end_pitch,
            cengkok_extract,
            rhythm,
            restructured_phrase_part,
        )
        for pitch, note in zip(pitches, rhythm):
            note.pitch_or_pitches = pitch

    def _make_moving_part(
        self,
        nth_grid: int,
        n_grids: int,
        grid_data,
        restructured_phrase_part: structure.RestructuredPhrasePart,
        next_restructured_phrase_part: structure.RestructuredPhrasePart,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        cengkok_line: events.basic.SequentialEvent,
        counter_melody: events.basic.SequentialEvent,
    ):
        grid_step_size, grid = grid_data
        if restructured_phrase_part.bar_character == structure.CADENZA:
            density = self.cadenza_density
        else:
            density = self._density_curve.value_at(nth_grid / n_grids)
        n_added_notes = int((len(grid) - 1) * density)
        positions = tuple(
            utilities.tools.accumulate_from_zero([grid_step_size for _ in grid])
        )[1:-1]
        choosen_indices = tuple(
            sorted(
                self._random.choice(
                    positions,
                    p=utilities.tools.scale_sequence_to_sum(grid[1:], 1),
                    size=n_added_notes,
                    replace=False,
                )
            )
        )
        rhythm = events.basic.SequentialEvent([])
        for position0, position1 in zip(
            (0,) + choosen_indices,
            choosen_indices + (len(grid) * grid_step_size,),
        ):
            duration = position1 - position0
            rhythm.append(
                events.music.NoteLike(
                    [
                        restructured_phrase_part.phrase_event.root
                        - parameters.pitches.JustIntonationPitch("2/1")
                    ],
                    duration=duration,
                )
            )

        cut_out_start = counter_melody.duration
        cengkok_extract = cengkok_line.cut_out(
            cut_out_start, cut_out_start + rhythm.duration, mutate=False
        )

        self._assign_pitches(
            rhythm,
            restructured_phrase_parts[nth_grid],
            next_restructured_phrase_part,
            cengkok_extract,
        )

        return rhythm

    def _make_end_part(
        self, restructured_phrase_part: structure.RestructuredPhrasePart
    ) -> events.basic.SequentialEvent:
        pitch = restructured_phrase_part.root + self._root_change_interval
        duration = restructured_phrase_part.duration
        sequential_event = events.basic.SequentialEvent(
            [events.music.NoteLike(pitch, duration)]
        )
        return sequential_event

    def _make_start_part(
        self, restructured_phrase_part: structure.RestructuredPhrasePart
    ) -> events.basic.SequentialEvent:
        duration = restructured_phrase_part.duration
        sequential_event = events.basic.SequentialEvent(
            [events.basic.SimpleEvent(duration)]
        )
        return sequential_event

    def _prolong_last_beat_of_previous_bar(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        sequential_event: events.basic.SequentialEvent,
    ):
        is_first = True
        for absolute_time, restructured_phrase_part in zip(
            restructured_phrase_parts.absolute_times, restructured_phrase_parts
        ):
            event_index_to_shorten = sequential_event.get_event_index_at(absolute_time)
            event_to_prolong = sequential_event[event_index_to_shorten - 1]
            event_to_shorten = sequential_event[event_index_to_shorten]
            if (
                restructured_phrase_part.bar_character
                not in (structure.END, structure.END_AND_START)
                and not is_first
                and hasattr(event_to_prolong, "pitch_or_pitches")
                and event_to_prolong.pitch_or_pitches
                and event_to_shorten.duration.denominator % 2 == 0
                and event_to_shorten.duration.denominator % 3 != 0
                and event_to_prolong.duration.denominator % 2 == 0
                and event_to_prolong.duration.denominator % 3 != 0
            ):
                if self.prolong_al_generator(self.prolong_al):
                    event_to_shorten.duration /= 2
                    event_to_prolong.duration += event_to_shorten.duration

            is_first = False

        return sequential_event

    def convert(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        cengkok_line: events.basic.SequentialEvent[events.music.NoteLike],
    ) -> events.basic.SequentialEvent:
        cengkok_line = cengkok_line.copy()
        grids = self._make_grids(restructured_phrase_parts, cengkok_line)

        counter_melody = events.basic.SequentialEvent([])

        n_grids = len(grids) - 1

        for (
            nth_grid,
            grid_data,
            phrase_part,
            next_restructured_phrase_part,
        ) in itertools.zip_longest(
            range(len(grids)),
            grids,
            restructured_phrase_parts,
            restructured_phrase_parts[1:],
        ):
            if phrase_part.bar_character == structure.END:
                sequential_event = self._make_end_part(
                    phrase_part,
                )
            elif phrase_part.bar_character == structure.START:
                sequential_event = self._make_start_part(
                    phrase_part,
                )
            else:
                sequential_event = self._make_moving_part(
                    nth_grid,
                    n_grids,
                    grid_data,
                    phrase_part,
                    next_restructured_phrase_part,
                    restructured_phrase_parts,
                    cengkok_line,
                    counter_melody,
                )
            counter_melody.extend(sequential_event)

        counter_melody = self._prolong_last_beat_of_previous_bar(
            restructured_phrase_parts,
            counter_melody,
        )
        counter_melody.set_parameter(
            "volume", parameters.volumes.WesternVolume("p")
        )

        return counter_melody
