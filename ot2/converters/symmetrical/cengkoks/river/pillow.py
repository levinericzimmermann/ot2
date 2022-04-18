import abc
import functools
import itertools
import operator
import random
import typing

import numpy as np
import more_itertools

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters

from ot2 import analysis
from ot2 import constants as ot2_constants
from ot2 import events as ot2_events


PillowEventsPerLoudspeaker = tuple[
    # for each loudspeaker one tuple
    tuple[ot2_events.music.PillowEvent, ...],
    tuple[ot2_events.music.PillowEvent, ...],
    tuple[ot2_events.music.PillowEvent, ...],
    tuple[ot2_events.music.PillowEvent, ...],
]


class PhraseEventToPillowEventsPerLoudspeaker(converters.abc.Converter):
    n_loudspeaker = 4
    loudspeaker_distribution_cycle = itertools.cycle(
        functools.reduce(
            operator.add, more_itertools.circular_shifts(range(n_loudspeaker))
        )
    )

    root_volume = -6
    connection_volume = -8
    other_volume = -12

    root_attack_duration_factor_range = (0.1, 0.3)
    root_release_duration_factor_range = (0.1, 0.3)

    connection0_attack_duration_factor = 0.05
    connection0_release_duration_factor = 0.5
    connection1_attack_duration_factor = 0.5
    connection1_release_duration_factor = 0.05

    other_percentage = 0.4

    def _add_root_and_connection_pitches(
        self,
        pillow_events_per_loudspeaker: list[list[ot2_events.music.PillowEvent]],
        phrase_event_to_convert: analysis.phrases.PhraseEvent,
        max_volume: parameters.volumes.DecibelVolume,
        register_range: tuple[int, int],
    ):
        for nth_register, register in enumerate(
            range(register_range[0], register_range[1] + 1)
        ):
            if nth_register % 2 == 0:
                pitches_to_distribute = (phrase_event_to_convert.root,)
                envelope_factors = (
                    (
                        random.uniform(*self.root_attack_duration_factor_range),
                        random.uniform(*self.root_release_duration_factor_range),
                    ),
                )
                volume_modification = self.root_volume
            else:
                pitches_to_distribute = (
                    phrase_event_to_convert.connection_pitch0,
                    phrase_event_to_convert.connection_pitch1,
                )
                volume_modification = self.connection_volume
                envelope_factors = (
                    (
                        self.connection0_attack_duration_factor,
                        self.connection0_release_duration_factor,
                    ),
                    (
                        self.connection1_attack_duration_factor,
                        self.connection1_release_duration_factor,
                    ),
                )
            for (
                pitch,
                attack_duration_and_release_duration_factor,
            ) in zip(pitches_to_distribute, envelope_factors):
                (
                    attack_duration_factor,
                    release_duration_factor,
                ) = attack_duration_and_release_duration_factor
                if pitch:
                    volume = parameters.volumes.DecibelVolume(
                        max_volume.decibel + volume_modification
                    )
                    pillow_event = ot2_events.music.PillowEvent(
                        pitch.register(register, mutate=False),
                        phrase_event_to_convert.duration,
                        volume,
                        attack_duration_factor,
                        release_duration_factor,
                    )
                    pillow_events_per_loudspeaker[
                        next(self.loudspeaker_distribution_cycle)
                    ].append(pillow_event)

    def _find_most_harmonic_registers_per_other_pitch(
        self,
        pillow_events_per_loudspeaker: list[list[ot2_events.music.PillowEvent]],
        register_range: tuple[int, int],
        n_variants_per_other_pitch: int,
        other_pitches: tuple[parameters.pitches.JustIntonationPitch, ...],
    ) -> tuple[tuple[int, ...], ...]:
        valid_register_combinations = tuple(
            itertools.combinations(
                range(register_range[0], register_range[1] + 1),
                n_variants_per_other_pitch,
            )
        )
        candidate = [
            valid_register_combinations[0] for _ in pillow_events_per_loudspeaker
        ]
        pillow_events = functools.reduce(operator.add, pillow_events_per_loudspeaker)
        fitness = 0
        for current_candidate in itertools.product(
            *[valid_register_combinations for _ in other_pitches]
        ):
            other_pitches_for_current_candidate = []
            for registers, other_pitch in zip(current_candidate, other_pitches):
                other_pitches_for_current_candidate.append(
                    [
                        other_pitch.register(register, mutate=False)
                        for register in registers
                    ]
                )
            current_fitness = 0
            for other_pitches0, other_pitches1 in itertools.combinations(
                other_pitches_for_current_candidate, 2
            ):
                for p0, p1 in itertools.product(other_pitches0, other_pitches1):
                    interval = p0 - p1
                    current_fitness += interval.harmonicity_simplified_barlow
            for other_pitches0, pillow_event in itertools.product(
                other_pitches_for_current_candidate, pillow_events
            ):
                for other_pitch in other_pitches0:
                    interval = other_pitch - pillow_event.pitch
                    current_fitness += interval.harmonicity_simplified_barlow
            if current_fitness > fitness:
                candidate = current_candidate

        return candidate

    def _get_attack_duration_and_release_duration_for_each_other_pitch_variant(
        self,
        duration: parameters.abc.DurationType,
        other_pitches: tuple[parameters.pitches.JustIntonationPitch, ...],
        n_variants_per_other_pitch: int,
    ) -> tuple[
        tuple[tuple[parameters.abc.DurationType, parameters.abc.DurationType], ...], ...
    ]:
        n_other_pitches = len(other_pitches)
        n_different_other_pitches = n_other_pitches * n_variants_per_other_pitch
        n_steps = n_different_other_pitches + 1
        step_size = duration / n_steps
        attack_duration_and_release_duration_for_each_other_pitch_variant = [
            [] for _ in other_pitches
        ]
        other_pitches_index_cycle = itertools.cycle((range(n_other_pitches)))
        for nth_step in range(n_different_other_pitches):
            other_pitches_index = next(other_pitches_index_cycle)
            n_steps_for_attack_duration = nth_step + 1
            n_steps_for_release_duration = n_steps - n_steps_for_attack_duration
            attack_duration = (n_steps_for_attack_duration * step_size) / duration
            release_duration = (n_steps_for_release_duration * step_size) / duration
            attack_duration_and_release_duration_for_each_other_pitch_variant[
                other_pitches_index
            ].append((attack_duration, release_duration))
        return tuple(
            map(
                tuple, attack_duration_and_release_duration_for_each_other_pitch_variant
            )
        )

    def _make_pillow_events_for_other_pitches(
        self,
        pillow_events_per_loudspeaker: list[list[ot2_events.music.PillowEvent]],
        phrase_event_to_convert: analysis.phrases.PhraseEvent,
        max_volume: parameters.volumes.DecibelVolume,
        register_range: tuple[int, int],
    ) -> tuple[tuple[ot2_events.music.PillowEvent], ...]:
        other_pitches = [
            pitch
            for pitch in phrase_event_to_convert.all_pitches
            if pitch
            not in (
                phrase_event_to_convert.root,
                phrase_event_to_convert.connection_pitch0,
                phrase_event_to_convert.connection_pitch1,
            )
        ]
        n_variants_per_other_pitch = int(
            (register_range[1] - register_range[0] + 1) * self.other_percentage
        )
        if n_variants_per_other_pitch < 1:
            n_variants_per_other_pitch = 1

        registers_per_other_pitch = self._find_most_harmonic_registers_per_other_pitch(
            pillow_events_per_loudspeaker,
            register_range,
            n_variants_per_other_pitch,
            other_pitches,
        )

        attack_duration_and_release_duration_for_each_other_pitch_variant = (
            self._get_attack_duration_and_release_duration_for_each_other_pitch_variant(
                phrase_event_to_convert.duration,
                other_pitches,
                n_variants_per_other_pitch,
            )
        )
        volume = parameters.volumes.DecibelVolume(
            max_volume.decibel + self.other_volume
        )
        pillow_events_per_other_pitch = []
        for (
            attack_duration_and_release_duration_per_register,
            registers,
            other_pitch,
        ) in zip(
            attack_duration_and_release_duration_for_each_other_pitch_variant,
            registers_per_other_pitch,
            other_pitches,
        ):
            pillow_events_for_current_other_pitch = []
            for register, attack_duration_and_release_duration in zip(
                registers, attack_duration_and_release_duration_per_register
            ):
                pillow_event = ot2_events.music.PillowEvent(
                    other_pitch.register(register, mutate=False),
                    phrase_event_to_convert.duration,
                    volume,
                    *attack_duration_and_release_duration
                )
                pillow_events_for_current_other_pitch.append(pillow_event)
            pillow_events_per_other_pitch.append(
                tuple(pillow_events_for_current_other_pitch)
            )

        return tuple(pillow_events_per_other_pitch)

    def _distribute_pillow_events_for_other_pitches_on_loudspeaker(
        self,
        pillow_events_per_loudspeaker: list[list[ot2_events.music.PillowEvent]],
        pillow_events_for_other_pitches: tuple[
            tuple[ot2_events.music.PillowEvent, ...], ...
        ],
    ):
        for pillow_events in pillow_events_for_other_pitches:
            for pillow_event in pillow_events:
                n_events_per_loudspeaker = [
                    len(pe) for pe in pillow_events_per_loudspeaker
                ]
                minima = n_events_per_loudspeaker.index(min(n_events_per_loudspeaker))
                pillow_events_per_loudspeaker[minima].append(pillow_event)

    def _add_other_pitches(
        self,
        pillow_events_per_loudspeaker: list[list[ot2_events.music.PillowEvent]],
        phrase_event_to_convert: analysis.phrases.PhraseEvent,
        max_volume: parameters.volumes.DecibelVolume,
        register_range: tuple[int, int],
    ):
        pillow_events_for_other_pitches = self._make_pillow_events_for_other_pitches(
            pillow_events_per_loudspeaker,
            phrase_event_to_convert,
            max_volume,
            register_range,
        )
        self._distribute_pillow_events_for_other_pitches_on_loudspeaker(
            pillow_events_per_loudspeaker, pillow_events_for_other_pitches
        )

    def convert(
        self,
        phrase_event_to_convert: analysis.phrases.PhraseEvent,
        max_volume: parameters.volumes.DecibelVolume,
        register_range: tuple[int, int],
    ) -> PillowEventsPerLoudspeaker:
        pillow_events_per_loudspeaker = [[] for _ in range(self.n_loudspeaker)]
        self._add_root_and_connection_pitches(
            pillow_events_per_loudspeaker,
            phrase_event_to_convert,
            max_volume,
            register_range,
        )
        self._add_other_pitches(
            pillow_events_per_loudspeaker,
            phrase_event_to_convert,
            max_volume,
            register_range,
        )
        return tuple(map(tuple, pillow_events_per_loudspeaker))


PillowEvents = tuple[
    events.basic.TaggedSimultaneousEvent[
        events.basic.SequentialEvent[ot2_events.music.PillowEvent]
    ],
    events.basic.TaggedSimultaneousEvent[
        events.basic.SequentialEvent[ot2_events.music.PillowEvent]
    ],
    events.basic.TaggedSimultaneousEvent[
        events.basic.SequentialEvent[ot2_events.music.PillowEvent]
    ],
    events.basic.TaggedSimultaneousEvent[
        events.basic.SequentialEvent[ot2_events.music.PillowEvent]
    ],
]


class PhraseEventsToTaggedSimultaneousEvents(converters.abc.Converter):
    @abc.abstractmethod
    def convert(
        self, phrase_events_to_convert: tuple[analysis.phrases.PhraseEvent, ...]
    ) -> PillowEvents:
        raise NotImplementedError


class SimplePhraseEventsToTaggedSimultaneousEvents(
    PhraseEventsToTaggedSimultaneousEvents
):
    def _make_pillow_events_per_loudspeaker_per_phrase_event(
        self, phrase_events_to_convert: tuple[analysis.phrases.PhraseEvent, ...]
    ) -> tuple[PillowEventsPerLoudspeaker, ...]:
        tagged_simultaneous_event_per_phrase_event = []
        for phrase_event in phrase_events_to_convert:
            register_range = (0, 2)
            tagged_simultaneous_events = (
                PhraseEventToPillowEventsPerLoudspeaker().convert(
                    phrase_event, parameters.volumes.DecibelVolume(-6), register_range
                )
            )
            tagged_simultaneous_event_per_phrase_event.append(
                tagged_simultaneous_events
            )
        return tuple(tagged_simultaneous_event_per_phrase_event)

    def _prolong_pitches_which_appear_in_previous_bar_and_return_all_not_prolongable_pitches(
        self,
        pillow_events_per_loudspeaker: PillowEventsPerLoudspeaker,
        tagged_simultaneous_events: PillowEvents,
    ):
        adjusted_pillow_events_per_loudspeaker = []
        for pillow_events in pillow_events_per_loudspeaker:
            adjusted_pillow_events = []
            for pillow_event in pillow_events:
                has_been_added = False
                for tagged_simultaneous_event in tagged_simultaneous_events:
                    for sequential_event in tagged_simultaneous_event:
                        if (
                            hasattr(sequential_event[-1], "pitch")
                            and sequential_event[-1].pitch == pillow_event.pitch
                        ):
                            sequential_event[-1].duration += pillow_event.duration
                            sequential_event[
                                -1
                            ].release_duration = pillow_event.release_duration
                            has_been_added = True
                            break
                if not has_been_added:
                    adjusted_pillow_events.append(pillow_event)
            adjusted_pillow_events_per_loudspeaker.append(tuple(adjusted_pillow_events))
        return tuple(adjusted_pillow_events_per_loudspeaker)

    def _add_adjusted_pillow_events_per_loudspeaker_to_global_tagged_simultaneous_events(
        self,
        adjusted_pillow_events_per_loudspeaker,
        tagged_simultaneous_events,
        absolute_time,
        duration,
    ):
        for nth_loudspeaker, adjusted_pillow_events in enumerate(
            adjusted_pillow_events_per_loudspeaker
        ):
            responsible_tagged_simultaneous_event = tagged_simultaneous_events[
                nth_loudspeaker
            ]
            useable_sequential_event_indices = []
            for sequential_event_index, sequential_event in enumerate(
                responsible_tagged_simultaneous_event
            ):
                if sequential_event.duration == absolute_time:
                    useable_sequential_event_indices.append(sequential_event_index)

            difference = len(adjusted_pillow_events) - len(
                useable_sequential_event_indices
            )
            if difference > 0:
                for _ in range(difference):
                    responsible_tagged_simultaneous_event.append(
                        events.basic.SequentialEvent(
                            [events.basic.SimpleEvent(absolute_time)]
                        )
                    )
                    useable_sequential_event_indices.append(
                        len(responsible_tagged_simultaneous_event) - 1
                    )

            assert len(responsible_tagged_simultaneous_event) >= len(
                adjusted_pillow_events
            )

            for nth_sequential_event, pillow_event in zip(
                useable_sequential_event_indices, adjusted_pillow_events
            ):
                responsible_tagged_simultaneous_event[nth_sequential_event].append(
                    pillow_event
                )

            for sequential_event in responsible_tagged_simultaneous_event:
                difference_to_expected_duration = (
                    absolute_time + duration
                ) - sequential_event.duration
                if difference_to_expected_duration > 0:
                    sequential_event.append(
                        events.basic.SimpleEvent(difference_to_expected_duration)
                    )

    def _make_sure_all_tagged_simultaneous_events_are_equally_long(
        self, tagged_simultaneous_events: PillowEvents
    ):
        duration = tagged_simultaneous_events[0].duration
        for tagged_simultaneous_event in tagged_simultaneous_events:
            for sequential_event in tagged_simultaneous_event:
                assert sequential_event.duration == duration

    def _concatenate_tagged_simultaneous_events_per_phrase_event(
        self,
        pillow_events_per_loudspeaker_per_phrase_event: tuple[
            PillowEventsPerLoudspeaker, ...
        ],
        phrase_events: tuple[analysis.phrases.PhraseEvent, ...],
    ) -> PillowEvents:
        tagged_simultaneous_events = [
            events.basic.TaggedSimultaneousEvent([], tag=pillow_id)
            for pillow_id in ot2_constants.instruments.PILLOW_IDS
        ]
        for (pillow_events_per_loudspeaker, absolute_time, duration) in zip(
            pillow_events_per_loudspeaker_per_phrase_event,
            phrase_events.absolute_times,
            phrase_events.get_parameter("duration"),
        ):
            # adjusted_pillow_events_per_loudspeaker = self._prolong_pitches_which_appear_in_previous_bar_and_return_all_not_prolongable_pitches(
            #     pillow_events_per_loudspeaker, tagged_simultaneous_events
            # )
            self._add_adjusted_pillow_events_per_loudspeaker_to_global_tagged_simultaneous_events(
                # adjusted_pillow_events_per_loudspeaker,
                pillow_events_per_loudspeaker,
                tagged_simultaneous_events,
                absolute_time,
                duration,
            )

        self._make_sure_all_tagged_simultaneous_events_are_equally_long(
            tagged_simultaneous_events
        )

        return tagged_simultaneous_events

    def convert(
        self, phrase_events_to_convert: tuple[analysis.phrases.PhraseEvent, ...]
    ) -> PillowEvents:
        pillow_events_per_loudspeaker_per_phrase_event = (
            self._make_pillow_events_per_loudspeaker_per_phrase_event(
                phrase_events_to_convert
            )
        )
        tagged_simultaneous_events = (
            self._concatenate_tagged_simultaneous_events_per_phrase_event(
                pillow_events_per_loudspeaker_per_phrase_event, phrase_events_to_convert
            )
        )
        return tagged_simultaneous_events


class PolyphonicPhraseEventsToTaggedSimultaneousEvents(converters.abc.Converter):
    def __init__(self, seed: int = 150000):
        self._loudspeaker_cycle = itertools.cycle(
            functools.reduce(operator.add, itertools.permutations(range(4)))
        )
        self._random = np.random.default_rng(seed)

    def _make_pitch_to_harmonicity(
        self, registered_pitches: tuple[parameters.pitches.JustIntonationPitch, ...]
    ) -> typing.Dict[parameters.pitches.JustIntonationPitch, float]:
        pitch_to_harmonicity = {pitch.exponents: 0 for pitch in registered_pitches}
        pitch_to_n_intervals = {pitch.exponents: 0 for pitch in registered_pitches}
        for pair in itertools.combinations(registered_pitches, 2):
            interval = pair[0] - pair[1]
            harmonicity = interval.harmonicity_simplified_barlow
            pitch_to_harmonicity[pair[0].exponents] += harmonicity
            pitch_to_harmonicity[pair[1].exponents] += harmonicity
            pitch_to_n_intervals[pair[0].exponents] += 1
            pitch_to_n_intervals[pair[1].exponents] += 1

        for exponents in pitch_to_harmonicity:
            pitch_to_harmonicity[exponents] /= pitch_to_n_intervals[exponents]

        return pitch_to_harmonicity

    def _collect_pitches_per_bar(
        self,
        phrase_events_to_convert: tuple[analysis.phrases.PhraseEvent, ...],
        minimal_register: int = -2,
        maximum_register: int = 2,
    ) -> tuple[
        tuple[tuple[parameters.pitches.JustIntonationPitch, str, float], ...], ...
    ]:

        pitches_to_registered_pitches_converter = converters.symmetrical.pitches.JustIntonationPitchesToRegisteredJustIntonationPitchesConverter(
            just_intonation_pitches_and_register_offsets_to_registered_just_intonation_pitches_converter=converters.symmetrical.pitches.JustIntonationPitchesAndRegisterOffsetsToRegisteredJustIntonationPitchesConverter(
                minimal_register=minimal_register, maximum_register=maximum_register
            )
        )

        pitches_per_bar = []
        for phrase_event in phrase_events_to_convert:
            pitches = []
            pitch_to_tag = {}
            for pitch in phrase_event.normalized_all_pitches:
                if pitch == phrase_event.root.normalize(mutate=False):
                    tag = "root"
                elif (
                    phrase_event.connection_pitch1
                    and pitch == phrase_event.connection_pitch1.normalize(mutate=False)
                ):
                    tag = "connection"
                else:
                    tag = "common"

                # avoid the first connection pitch (we will always use the second
                # one and tie the second one over two bars)
                if (
                    not phrase_event.connection_pitch0
                    or pitch != phrase_event.connection_pitch0.normalize(mutate=False)
                ):
                    pitch_to_tag.update({pitch.normalize(mutate=False).exponents: tag})
                    pitches.append(pitch)
                    # # play root and connection twice :)
                    if tag in ("root", "connection"):
                        pitches.append(pitch)

            # register pitches
            registered_pitches = pitches_to_registered_pitches_converter.convert(
                pitches
            )
            pitch_to_harmonicity = self._make_pitch_to_harmonicity(registered_pitches)
            registered_pitch_and_tag_and_harmonicity_items = tuple(
                (
                    pitch,
                    pitch_to_tag[pitch.normalize(mutate=False).exponents],
                    pitch_to_harmonicity[pitch.exponents],
                )
                for pitch in registered_pitches
            )
            pitches_per_bar.append(registered_pitch_and_tag_and_harmonicity_items)
        return tuple(pitches_per_bar)

    def _distribute_pulses(
        self,
        offsets: tuple[float, ...],
        pitch_indices: tuple[int, ...],
        pitch_data_and_start_and_end_time: list[
            list[
                parameters.pitches.JustIntonationPitch,
                typing.Optional[float],
                typing.Optional[float],
            ],
        ],
        flat_pitch_data: tuple[
            tuple[parameters.pitches.JustIntonationPitch, str, float], ...
        ],
        reverse: bool = False,
        set_index: int = 1,
    ):
        pitch_index_and_fitness_pairs = tuple(
            map(
                lambda index: (
                    index,
                    flat_pitch_data[index][-1] * self._random.uniform(0.5, 2),
                ),
                pitch_indices,
            )
        )
        sorted_pitch_index_and_fitness_pairs = sorted(
            pitch_index_and_fitness_pairs, key=operator.itemgetter(1), reverse=reverse
        )
        for pitch_index_and_fitness, offset in zip(
            sorted_pitch_index_and_fitness_pairs, offsets
        ):
            pitch_index, _ = pitch_index_and_fitness
            pitch_data_and_start_and_end_time[pitch_index][set_index] = offset

    def convert(
        self,
        phrase_events_to_convert: tuple[analysis.phrases.PhraseEvent, ...],
        minimal_register: int = -2,
        maximum_register: int = 2,
    ) -> PillowEvents:
        phrase_events_to_convert = events.basic.SequentialEvent(
            phrase_events_to_convert
        )
        pitches_per_bar = self._collect_pitches_per_bar(
            phrase_events_to_convert, minimal_register, maximum_register
        )

        flat_pitch_data = []
        start_and_end_pitches_per_bar = [[[], []] for _ in phrase_events_to_convert]
        for nth_bar, pitch_data_in_current_bar in enumerate(pitches_per_bar):
            for pitch, tag, harmonicity in pitch_data_in_current_bar:
                current_pitch_index = len(flat_pitch_data)
                if tag == "connection":
                    start_bar = nth_bar
                    end_bar = nth_bar + 1
                    try:
                        start_and_end_pitches_per_bar[end_bar]
                    except IndexError:
                        end_bar = nth_bar
                else:
                    start_bar = nth_bar
                    end_bar = nth_bar
                start_and_end_pitches_per_bar[start_bar][0].append(current_pitch_index)
                start_and_end_pitches_per_bar[end_bar][1].append(current_pitch_index)
                flat_pitch_data.append((pitch, tag, harmonicity))

        pitch_data_and_start_and_end_time = [
            [pitch_data, None, None] for pitch_data in flat_pitch_data
        ]

        blurry_pulses = generators.generic.BlurryPulses()

        for absolute_time, duration, start_and_end_pitches in zip(
            phrase_events_to_convert.absolute_times,
            phrase_events_to_convert.get_parameter("duration"),
            start_and_end_pitches_per_bar,
        ):
            n_positions = sum(map(len, start_and_end_pitches))
            pulse_size = duration / (n_positions - 1)
            pulse_positions = list(
                map(
                    lambda offset: offset + absolute_time,
                    blurry_pulses(pulse_size, n_positions - 1),
                )
            )
            if pulse_positions[0] < 0:
                pulse_positions[0] = 0

            pulse_positions.append(absolute_time + duration)

            n_start_pitches = len(start_and_end_pitches[0])
            start_pulses = pulse_positions[:n_start_pitches]
            end_pulses = pulse_positions[n_start_pitches:]
            self._distribute_pulses(
                start_pulses,
                start_and_end_pitches[0],
                pitch_data_and_start_and_end_time,
                flat_pitch_data,
                reverse=False,
                set_index=1,
            )
            self._distribute_pulses(
                end_pulses,
                start_and_end_pitches[1],
                pitch_data_and_start_and_end_time,
                flat_pitch_data,
                reverse=True,
                set_index=2,
            )

        sorted_pitch_data_and_start_and_end_time = sorted(
            pitch_data_and_start_and_end_time, key=operator.itemgetter(1)
        )

        duration = phrase_events_to_convert.duration

        sequential_events = []
        for (
            pitch_data,
            start_time,
            end_time,
        ) in sorted_pitch_data_and_start_and_end_time:
            sequential_event = events.basic.SequentialEvent([])
            if start_time != 0:
                sequential_event.append(events.basic.SimpleEvent(start_time))
            if pitch_data[1] == "root":
                volume = self._random.uniform(-8, -4)
            elif pitch_data[1] == "connection":
                volume = self._random.uniform(-14, -10)
            else:
                volume = self._random.uniform(-23, -19)
            note_like = events.music.NoteLike(
                pitch_data[0],
                end_time - start_time,
                parameters.volumes.DecibelVolume(volume),
            )
            sequential_event.append(note_like)
            difference_to_end = duration - end_time
            if difference_to_end:
                sequential_event.append(events.basic.SimpleEvent(difference_to_end))
            sequential_events.append(sequential_event)

        tagged_simultaneous_events = [
            events.basic.TaggedSimultaneousEvent([], tag=pillow_id)
            for pillow_id in ot2_constants.instruments.PILLOW_IDS
        ]

        for sequential_event in sequential_events:
            tagged_simultaneous_events[next(self._loudspeaker_cycle)].append(
                sequential_event
            )

        return tagged_simultaneous_events
