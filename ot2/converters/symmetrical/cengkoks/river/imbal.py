import collections
import copy
import fractions
import itertools
import typing

import numpy as np

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters
from mutwo import utilities

from ot2 import constants as ot2_constants

from . import structure


def is_note(
    note_like: events.music.NoteLike,
) -> typing.Optional[typing.Sequence[parameters.pitches.JustIntonationPitch]]:
    if hasattr(note_like, "pitch_or_pitches") and note_like.pitch_or_pitches:
        return note_like.pitch_or_pitches


class PhrasePart(events.basic.SimpleEvent):
    ambitus = (
        ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES
    )

    def __init__(
        self,
        duration: parameters.abc.DurationType,
        root: parameters.pitches.JustIntonationPitch,
        all_pitches: tuple[parameters.pitches.JustIntonationPitch, ...],
    ):
        super().__init__(duration)
        self.root = root
        self.all_pitches = all_pitches

    def find_possible_registers_for_pitch(
        self, pitch_to_analyse: parameters.pitches.JustIntonationPitch
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        return self.ambitus.find_all_pitch_variants(pitch_to_analyse)

    def find_possible_register_intervals_for_root(
        self,
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        possible_registers = self.find_possible_registers_for_pitch(self.root)
        possible_register_intervals = []
        for variant in possible_registers:
            interval = variant - self.root
            possible_register_intervals.append(interval)
        return tuple(possible_register_intervals)


class ImbalPhrase(events.basic.SequentialEvent[PhrasePart]):
    duration_of_connection_pitch_cycle = itertools.cycle(
        (fractions.Fraction(1, 4), fractions.Fraction(3, 8), fractions.Fraction(1, 3))
    )
    distance_between_pitches_to_connection_pitches_pattern_cycle = {
        1: itertools.cycle([[3, 2], [2], []]),
        -1: itertools.cycle([[-3, -2], [], [-2]]),
        0: itertools.cycle(
            [
                [1],
                [2, 1],
                [-1],
            ]
        ),
    }
    _glissando_likelihood_for_root_notes = 0.49
    _glissando_likelihood_for_melody_notes = 0.385
    _split_activity_level_generator = generators.edwards.ActivityLevel()
    _split_activity_level = 6

    root_duration_to_split_cycles = {
        fractions.Fraction(3, 1): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 1), True),
                    (fractions.Fraction(1, 1), False),
                    (fractions.Fraction(1, 1), True),
                ),
            )
        ),
        fractions.Fraction(2, 1): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 2), True),
                    (fractions.Fraction(5, 4), False),
                    (fractions.Fraction(1, 4), True),
                ),
            )
        ),
        fractions.Fraction(7, 4): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 1), True),
                    (fractions.Fraction(1, 2), False),
                    (fractions.Fraction(1, 4), True),
                ),
                (
                    (fractions.Fraction(1, 2), True),
                    (fractions.Fraction(1, 1), False),
                    (fractions.Fraction(1, 4), True),
                ),
            )
        ),
        fractions.Fraction(3, 2): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 2), True),
                    (fractions.Fraction(2, 3), False),
                    (fractions.Fraction(1, 3), True),
                ),
                (
                    (fractions.Fraction(1, 2), True),
                    (fractions.Fraction(3, 4), False),
                    (fractions.Fraction(1, 4), True),
                ),
            )
        ),
        fractions.Fraction(1, 1): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 4), True),
                    (fractions.Fraction(1, 2), False),
                    (fractions.Fraction(1, 4), True),
                ),
                (
                    (fractions.Fraction(1, 3), True),
                    (fractions.Fraction(1, 3), False),
                    (fractions.Fraction(1, 3), True),
                ),
            )
        ),
        fractions.Fraction(3, 4): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 4), True),
                    (fractions.Fraction(1, 4), False),
                    (fractions.Fraction(1, 4), True),
                ),
            )
        ),
        fractions.Fraction(1, 2): itertools.cycle(
            (
                (
                    (fractions.Fraction(1, 6), True),
                    (fractions.Fraction(1, 6), False),
                    (fractions.Fraction(1, 6), True),
                ),
                (
                    (fractions.Fraction(1, 4), True),
                    (fractions.Fraction(1, 4), False),
                ),
            )
        ),
    }

    connection_making_algorithm_cycle = itertools.cycle(
        (
            "_make_well_distributed_rhythm_for_moving_part",
            "_make_brute_force_rhythm_for_moving_part",
            "_make_well_distributed_rhythm_for_moving_part",
        )
    )

    prolong_al_generator = generators.edwards.ActivityLevel()
    prolong_al = 8

    def __init__(
        self,
        *args,
        seed: int = 1,
        register_interval: typing.Optional[
            parameters.pitches.JustIntonationPitch
        ] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.register_interval = register_interval
        self._random = np.random.default_rng(seed)

    def find_possible_register_intervals_for_root_melody(
        self,
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        possible_register_intervals = []
        is_first = True
        for phrase_part in self:
            possible_register_intervals_for_current_phrase_part = (
                phrase_part.find_possible_register_intervals_for_root()
            )
            if is_first:
                possible_register_intervals.extend(
                    possible_register_intervals_for_current_phrase_part
                )
            else:
                possible_register_intervals = [
                    interval
                    for interval in possible_register_intervals
                    if interval in possible_register_intervals_for_current_phrase_part
                ]
            is_first = False

        return tuple(possible_register_intervals)

    def assign_register_interval(
        self,
        last_assigned_register_interval: parameters.pitches.JustIntonationPitch,
        register_interval_exponents_counter: collections.Counter,
    ) -> parameters.pitches.JustIntonationPitch:
        possible_register_intervals = (
            self.find_possible_register_intervals_for_root_melody()
        )
        if not possible_register_intervals:
            for phrase_part in self:
                phrase_part.root += parameters.pitches.JustIntonationPitch("2/1")
            possible_register_intervals = (
                self.find_possible_register_intervals_for_root_melody()
            )
        if not possible_register_intervals:
            for phrase_part in self:
                phrase_part.root += parameters.pitches.JustIntonationPitch("2/1")
            possible_register_intervals = (
                self.find_possible_register_intervals_for_root_melody()
            )
        if not possible_register_intervals:
            for phrase_part in self:
                phrase_part.root += parameters.pitches.JustIntonationPitch("1/8")
            possible_register_intervals = (
                self.find_possible_register_intervals_for_root_melody()
            )

        if not possible_register_intervals:
            for phrase_part in self:
                phrase_part.root.normalize()
                phrase_part.root.add(parameters.pitches.JustIntonationPitch('1/2'))
            possible_register_intervals = (
                self.find_possible_register_intervals_for_root_melody()
            )

        if not possible_register_intervals:
            raise ValueError(
                "SORRY! Couldn't find any possible register intervals. Ehhm maybe add another option?"
            )

        if len(possible_register_intervals) > 1:
            possible_register_intervals = filter(
                lambda interval: interval != last_assigned_register_interval,
                possible_register_intervals,
            )
            choosen_register_interval = min(
                possible_register_intervals,
                key=lambda interval: register_interval_exponents_counter[
                    interval.exponents
                ],
            )

        else:
            choosen_register_interval = possible_register_intervals[0]

        self.register_interval = choosen_register_interval
        return self.register_interval

    def _convert_start_or_end_phrase_part_to_sequential_event(
        self,
        root_pitch: parameters.pitches.JustIntonationPitch,
        current_phrase_part: PhrasePart,
        is_first_bar: bool,
        dynamic: str,
    ) -> events.basic.SequentialEvent:
        sequential_event = events.basic.SequentialEvent([])
        duration_of_root_note = current_phrase_part.duration / 2
        duration_of_rest = duration_of_root_note
        root_note = events.music.NoteLike(
            root_pitch, duration_of_root_note, volume=dynamic
        )
        root_note.is_root = True
        rest = events.basic.SimpleEvent(duration_of_rest)
        if is_first_bar:
            sequential_event.extend((rest, root_note))
        else:
            sequential_event.extend((root_note, rest))
        assert sequential_event.duration == current_phrase_part.duration
        return sequential_event

    def _add_glissandi_to_sequential_event(
        self, sequential_event: events.basic.SequentialEvent
    ) -> events.basic.SequentialEvent:
        new_sequential_event = events.basic.SequentialEvent([])
        for note_like0, note_like1 in zip(sequential_event, sequential_event[1:]):
            pitches0, pitches1 = is_note(note_like0), is_note(note_like1)
            added_glissando = False
            if (
                pitches0
                and pitches1
                and pitches0 != pitches1
                and abs((pitches0[0] - pitches1[0]).cents) <= 240
            ):
                if hasattr(note_like1, "is_root") and note_like1.is_root:
                    glissando_likelihood = self._glissando_likelihood_for_root_notes
                else:
                    glissando_likelihood = self._glissando_likelihood_for_melody_notes
                if self._random.uniform() < glissando_likelihood:
                    if note_like0.duration.denominator % 3 == 0:
                        glissando_duration = fractions.Fraction(1, 12)
                    elif note_like0.duration <= fractions.Fraction(1, 4):
                        glissando_duration = fractions.Fraction(1, 16)
                    else:
                        glissando_duration = fractions.Fraction(1, 8)
                    if glissando_duration < note_like0.duration:
                        note_like0_stable = note_like0.set_parameter(
                            "duration",
                            lambda duration: duration - glissando_duration,
                            mutate=False,
                        )
                        note_like0_gliss = note_like0.set_parameter(
                            "duration", glissando_duration, mutate=False
                        )
                        note_like0_stable.playing_indicators.tie.is_active = True
                        note_like0_gliss.playing_indicators.glissando.is_active = True
                        note_like0_gliss.playing_indicators.tie.is_active = True
                        new_sequential_event.extend(
                            (note_like0_stable, note_like0_gliss)
                        )
                        added_glissando = True
            if not added_glissando:
                new_sequential_event.append(note_like0)

        new_sequential_event.append(sequential_event[-1])
        return new_sequential_event

    def _split_root_notes(
        self, sequential_event: events.basic.SequentialEvent
    ) -> events.basic.SequentialEvent:
        new_sequential_event = events.basic.SequentialEvent([])
        is_first_note = True
        for note in sequential_event:
            has_been_processed = False
            is_very_long = note.duration in (
                fractions.Fraction(1, 1),
                fractions.Fraction(2, 1),
                fractions.Fraction(3, 2),
                fractions.Fraction(7, 4),
                fractions.Fraction(3, 1),
            )
            if (
                (
                    (hasattr(note, "is_root") and note.is_root)
                    or (is_very_long and hasattr(note, "playing_indicators"))
                )
                and not is_first_note
            ) and not note.playing_indicators.tie.is_active:
                if note.duration in self.root_duration_to_split_cycles and (
                    is_very_long
                    or self._split_activity_level_generator(self._split_activity_level)
                ):
                    has_been_processed = True
                    split = next(self.root_duration_to_split_cycles[note.duration])
                    for duration, is_active in split:
                        if is_active:
                            new_event = copy.copy(note)
                        else:
                            new_event = events.basic.SimpleEvent(0)
                        new_event.duration = duration
                        new_event.is_root = True
                        new_sequential_event.append(new_event)
            if not has_been_processed:
                new_sequential_event.append(note)
            if hasattr(note, "pitch_or_pitches") and note.pitch_or_pitches:
                is_first_note = False
        return new_sequential_event

    def _prolong_notes_before_next_bar(
        self, sequential_event: events.basic.SequentialEvent
    ) -> events.basic.SequentialEvent:
        for absolute_time in self.absolute_times[1:]:
            item_index = sequential_event.get_event_index_at(absolute_time)
            responsible_event = sequential_event[item_index]
            if hasattr(responsible_event, "is_root") and responsible_event.is_root:
                previous_item = sequential_event[item_index - 1]
                if (
                    hasattr(previous_item, "pitch_or_pitches")
                    and previous_item.pitch_or_pitches
                ):
                    if not previous_item.playing_indicators.glissando.is_active:
                        if (
                            responsible_event.duration.denominator % 3 != 0
                            and previous_item.duration.denominator % 3 != 0
                        ):
                            if self.prolong_al_generator(self.prolong_al):
                                if responsible_event.duration.denominator % 3 == 0:
                                    prolong_duration = fractions.Fraction(1, 12)
                                else:
                                    prolong_duration = fractions.Fraction(1, 16)
                                if responsible_event.duration > prolong_duration:
                                    responsible_event.duration -= prolong_duration
                                    previous_item.duration += prolong_duration

        return sequential_event

    def _get_connection_pitches_by_pattern(
        self,
        index_current_root_pitch: int,
        sorted_given_pitches: typing.Sequence[parameters.pitches.JustIntonationPitch],
        pattern: tuple[int, ...],
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        resolved_pattern = tuple(
            map(lambda index: index + index_current_root_pitch, pattern)
        )
        connection_pitches = []
        for index in resolved_pattern:
            try:
                assert index > 0
            except AssertionError:
                # simply return no pitches if a negative index has been created
                return tuple([])
            try:
                connection_pitch = sorted_given_pitches[index]
            except IndexError:
                # simply return no pitches if expected pattern couldn't
                # be constructed
                return tuple([])
            connection_pitches.append(connection_pitch)
        return tuple(connection_pitches)

    def _detect_connection_pitches(
        self,
        current_root_pitch: parameters.pitches.JustIntonationPitch,
        current_phrase_part: PhrasePart,
        next_phrase_part: PhrasePart,
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        connection_pitches = []
        next_root_pitch = next_phrase_part.root + self.register_interval
        given_pitches = [next_root_pitch, current_root_pitch]
        for pitch in current_phrase_part.all_pitches:
            variants = current_phrase_part.find_possible_registers_for_pitch(pitch)
            given_pitches.extend(variants)
        sorted_given_pitches = tuple(
            sorted(utilities.tools.uniqify_iterable(given_pitches))
        )
        index_current_root_pitch = sorted_given_pitches.index(current_root_pitch)
        index_next_root_pitch = sorted_given_pitches.index(next_root_pitch)
        distance_between_pitches = index_next_root_pitch - index_current_root_pitch
        if abs(distance_between_pitches) > 1:
            sorted_indices = sorted((index_current_root_pitch, index_next_root_pitch))
            connection_pitches = sorted_given_pitches[
                sorted_indices[0] + 1 : sorted_indices[1]
            ]
        else:  # distance == 0 (same pitch) or == 1 (one pitch higher /lower)
            pattern = next(
                self.distance_between_pitches_to_connection_pitches_pattern_cycle[
                    distance_between_pitches
                ]
            )
            connection_pitches = self._get_connection_pitches_by_pattern(
                index_current_root_pitch, sorted_given_pitches, pattern
            )
        return tuple(connection_pitches)

    def _make_well_distributed_rhythm_for_moving_part(
        self, duration: parameters.abc.DurationType, n_connection_pitches: int
    ) -> tuple[fractions.Fraction, ...]:
        n_pitches = n_connection_pitches + 1  # plus root pitch
        minimal_grid_size = n_pitches + 1
        while not (minimal_grid_size % 2 != 0 or minimal_grid_size % 3 != 0):
            minimal_grid_size += 1

        pulse_size = duration / minimal_grid_size
        rhythm = generators.toussaint.euclidean(minimal_grid_size, n_pitches)
        resulting_rhythm = tuple(n_beats * pulse_size for n_beats in rhythm)
        return resulting_rhythm

    def _make_brute_force_rhythm_for_moving_part(
        self, duration: parameters.abc.DurationType, n_connection_pitches: int
    ) -> tuple[fractions.Fraction, ...]:
        n_pitches = n_connection_pitches + 1
        beat_size = fractions.Fraction(1, 4)
        while beat_size * n_pitches >= duration:
            beat_size /= 2

        connection_rhythm = [beat_size] * n_connection_pitches
        root_rhythm = duration - sum(connection_rhythm)
        resulting_rhythm = (root_rhythm,) + tuple(connection_rhythm)
        return resulting_rhythm

    def _make_rhythm_for_moving_phrase_part(
        self, duration: parameters.abc.DurationType, n_connection_pitches: int
    ) -> tuple[fractions.Fraction, ...]:
        return getattr(self, next(self.connection_making_algorithm_cycle))(
            duration, n_connection_pitches
        )

    def _convert_moving_phrase_part_to_sequential_event(
        self,
        root_pitch: parameters.pitches.JustIntonationPitch,
        current_phrase_part: PhrasePart,
        next_phrase_part: PhrasePart,
        dynamic: str,
    ) -> events.basic.SequentialEvent:
        root_note = events.music.NoteLike(
            root_pitch, current_phrase_part.duration, dynamic
        )
        root_note.is_root = True
        sequential_event = events.basic.SequentialEvent([root_note])
        connection_pitches = self._detect_connection_pitches(
            root_pitch, current_phrase_part, next_phrase_part
        )
        if connection_pitches:
            rhythm = self._make_rhythm_for_moving_phrase_part(
                current_phrase_part.duration, len(connection_pitches)
            )
            sequential_event[0].duration = rhythm[0]
            for connection_pitch, duration in zip(connection_pitches, rhythm[1:]):
                connection_note = events.music.NoteLike(
                    [connection_pitch],
                    duration=duration,
                    volume=dynamic,
                )
                sequential_event.append(connection_note)
        assert sequential_event.duration == current_phrase_part.duration
        assert root_note.duration > 0
        return sequential_event

    def _convert_phrase_part_to_sequential_event(
        self,
        current_phrase_part: PhrasePart,
        next_phrase_part: typing.Optional[PhrasePart],
        is_first_bar: bool,
        dynamic: str,
    ) -> events.basic.SequentialEvent:
        root_pitch = current_phrase_part.root + self.register_interval
        if next_phrase_part is None or is_first_bar:
            sequential_event = (
                self._convert_start_or_end_phrase_part_to_sequential_event(
                    root_pitch, current_phrase_part, is_first_bar, dynamic
                )
            )
        else:
            sequential_event = self._convert_moving_phrase_part_to_sequential_event(
                root_pitch, current_phrase_part, next_phrase_part, dynamic
            )
        return sequential_event

    def convert_to_sequential_event(
        self, dynamic: str = "mp"
    ) -> events.basic.SequentialEvent:
        try:
            assert self.register_interval is not None
        except AssertionError:
            raise Exception()

        is_first = True
        sequential_event = events.basic.SequentialEvent([])
        for phrase_part0, phrase_part1 in itertools.zip_longest(self, self[1:]):
            sequential_event.extend(
                self._convert_phrase_part_to_sequential_event(
                    phrase_part0, phrase_part1, is_first, dynamic
                )
            )
            is_first = False
        sequential_event = self._split_root_notes(sequential_event)
        sequential_event = self._add_glissandi_to_sequential_event(sequential_event)
        sequential_event = self._prolong_notes_before_next_bar(sequential_event)
        assert sequential_event.duration == self.duration
        return sequential_event


class PhraseRest(events.basic.SimpleEvent):
    pattern_left_side_cycle = itertools.cycle(
        (
            (fractions.Fraction(1, 8), fractions.Fraction(1, 8)),
            (fractions.Fraction(3, 16), fractions.Fraction(1, 16)),
            (fractions.Fraction(1, 16), fractions.Fraction(3, 16)),
        )
    )
    pattern_right_side_cycle = itertools.cycle(
        (
            # do the different rhythms really matter for staccatto
            # (because all of them start at the same position)
            # (fractions.Fraction(1, 6), fractions.Fraction(1, 12)),
            # (fractions.Fraction(1, 16), fractions.Fraction(3, 16)),
            (fractions.Fraction(1, 4),),
            # (fractions.Fraction(1, 12), fractions.Fraction(1, 6)),
            # (fractions.Fraction(3, 16), fractions.Fraction(1, 16)),
        )
    )

    pattern_duration = fractions.Fraction(1, 2)

    activate_pattern_al_generator = generators.edwards.ActivityLevel()
    activate_pattern_al = 8

    ambitus = (
        ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES
    )

    def __init__(
        self,
        duration: parameters.abc.DurationType,
        restructured_phrase_parts: tuple[structure.RestructuredPhrasePart, ...],
    ):
        super().__init__(duration)
        self._restructured_phrase_parts = restructured_phrase_parts

    def _find_pitch_pair(
        self, restructured_phrase_part: structure.RestructuredPhrasePart
    ) -> tuple[
        parameters.pitches.JustIntonationPitch, parameters.pitches.JustIntonationPitch
    ]:
        root_pitch = restructured_phrase_part.root
        root_pitch_variants = self.ambitus.find_all_pitch_variants(root_pitch)
        choosen_root_pitch = root_pitch_variants[0]
        candidate = choosen_root_pitch
        candidate_distance = 1200
        for pitch in restructured_phrase_part.all_pitches:
            for variant in self.ambitus.find_all_pitch_variants(pitch):
                if variant != choosen_root_pitch:
                    distance = abs((choosen_root_pitch - variant).cents)
                    if distance < candidate_distance:
                        candidate = variant
                        candidate_distance = distance
        return candidate, choosen_root_pitch

    def convert_to_rhythmical_pattern(
        self, dynamic: str = "mp"
    ) -> events.basic.SequentialEvent:
        rhythmical_pattern = events.basic.SequentialEvent([])

        for restructured_phrase_part in self._restructured_phrase_parts:
            left_pitch, right_pitch = self._find_pitch_pair(restructured_phrase_part)
            n_pattern = int(restructured_phrase_part.duration / self.pattern_duration)
            for _ in range(n_pattern):
                if self.activate_pattern_al_generator(self.activate_pattern_al):
                    pattern_left, pattern_right = next(
                        self.pattern_left_side_cycle
                    ), next(self.pattern_right_side_cycle)
                    pattern = events.basic.SequentialEvent(
                        [
                            events.music.NoteLike([], pattern_left[0], dynamic),
                            events.music.NoteLike(left_pitch, pattern_left[1], dynamic),
                            events.music.NoteLike(
                                right_pitch, pattern_right[0], dynamic
                            ),
                            # events.music.NoteLike([], pattern_right[1], dynamic),
                        ]
                    )
                    for note in pattern[1:3]:
                        note.playing_indicators.articulation.name = "."
                    rhythmical_pattern.extend(pattern)

                else:
                    rhythmical_pattern.append(
                        events.music.NoteLike([], self.pattern_duration)
                    )

        rhythmical_pattern.tie_by(
            lambda ev0, ev1: hasattr(ev0, "pitch_or_pitches")
            and hasattr(ev1, "pitch_or_pitches")
            and ev0.pitch_or_pitches == ev1.pitch_or_pitches
            and hasattr(ev0, "playing_indicators")
            and not ev0.playing_indicators.tie.is_active
        )

        if len(rhythmical_pattern) >= 8:
            rhythmical_pattern[1].playing_indicators.hairpin.symbol = "<"
            middle_dynamic = "mf"
            middle_notes = (len(rhythmical_pattern) // 2) - 1
            if not rhythmical_pattern[middle_notes].pitch_or_pitches:
                middle_notes += 1

            rhythmical_pattern[middle_notes].volume = parameters.volumes.WesternVolume(
                middle_dynamic
            )

            next_note = middle_notes + 1
            if not rhythmical_pattern[next_note].pitch_or_pitches:
                next_note += 1

            rhythmical_pattern[next_note].playing_indicators.hairpin.symbol = ">"
            for note in rhythmical_pattern[next_note:-2]:
                if hasattr(note, "volume"):
                    note.volume = parameters.volumes.WesternVolume(middle_dynamic)

        assert rhythmical_pattern.duration == self._restructured_phrase_parts.duration
        return rhythmical_pattern


NBars = int
IsPlaying = bool
Phrase = tuple[NBars, IsPlaying]
AbstractPartRepresentation = events.basic.SequentialEvent[
    typing.Union[PhraseRest, ImbalPhrase]
]


class RestructuredPhrasePartsAndCengkokLineToImbalBasedRootMelodiesConverter(
    converters.abc.Converter
):
    def __init__(self, percentage_of_single_populated_bars: float = 0.23):
        self._percentage_of_single_populated_bars = percentage_of_single_populated_bars

    @staticmethod
    def _distribute_bars(
        n_bars: int,
        percentage_of_single_populated_bars: float,
        minimal_sequence_length_of_double_populated_bars: int = 2,
    ) -> tuple[Phrase, Phrase]:
        """Distribute bars on two different voices"""

        n_single_populated_bars = int(n_bars * percentage_of_single_populated_bars)
        n_double_populated_bars = n_bars - n_single_populated_bars
        distribution_of_double_populated_bars = [
            minimal_sequence_length_of_double_populated_bars - 1
        ]
        distribution_frequency = int(n_double_populated_bars // 2)
        while any(
            (
                n < minimal_sequence_length_of_double_populated_bars
                for n in distribution_of_double_populated_bars
            )
        ):
            if distribution_frequency < 0:
                raise ValueError()

            distribution_of_double_populated_bars = generators.toussaint.euclidean(
                n_double_populated_bars, distribution_frequency
            )
            distribution_frequency -= 1

        distribution_of_single_populated_bars = generators.toussaint.euclidean(
            n_single_populated_bars, len(distribution_of_double_populated_bars) + 1
        )

        distribution_time_spans = []
        for n_single_populated_bars, n_double_populated_bars in zip(
            distribution_of_single_populated_bars,
            distribution_of_double_populated_bars + (0,),
        ):
            for n_bars, is_double in (
                (n_single_populated_bars, False),
                (n_double_populated_bars, True),
            ):
                if n_bars:
                    distribution_time_spans.append((n_bars, is_double))

        phrases = [[], []]
        is_playing_cycle = itertools.cycle(((True, False), (False, True)))
        for n_bars, is_double in distribution_time_spans:
            if is_double:
                distribution_on_phrases = (True, True)
            else:
                distribution_on_phrases = next(is_playing_cycle)

            for phrase, is_playing in zip(phrases, distribution_on_phrases):
                has_been_processed = False
                if phrase:
                    if phrase[-1][1] == is_playing:
                        phrase[-1][0] += n_bars
                        has_been_processed = True

                if not has_been_processed:
                    phrase.append([n_bars, is_playing])

        return tuple(map(lambda phrase: tuple(map(tuple, phrase)), phrases))

    @staticmethod
    def _make_abstract_part_representation(
        restructured_phrase_parts: events.basic.SequentialEvent[
            structure.RestructuredPhrasePart
        ],
        phrase_distribution: Phrase,
    ) -> AbstractPartRepresentation:
        part_representation = events.basic.SequentialEvent([])
        nth_bar = 0
        for n_bars, is_active in phrase_distribution:
            responsible_restructured_phrase_parts = restructured_phrase_parts[
                nth_bar : nth_bar + n_bars
            ]
            if is_active:
                part_part = ImbalPhrase(
                    [
                        PhrasePart(
                            phrase_part.duration,
                            phrase_part.root,
                            phrase_part.all_pitches,
                        )
                        for phrase_part in responsible_restructured_phrase_parts
                    ],
                    seed=n_bars + nth_bar,
                )
                part_part.register_interval = parameters.pitches.JustIntonationPitch()
            else:
                part_part = PhraseRest(
                    responsible_restructured_phrase_parts.duration,
                    responsible_restructured_phrase_parts,
                )
            part_representation.append(part_part)
            nth_bar += n_bars
        return part_representation

    @staticmethod
    def _assign_register_intervals_to_abstract_part_representations(
        abstract_part_representations: tuple[
            AbstractPartRepresentation, AbstractPartRepresentation
        ]
    ):
        register_interval_exponents_counter = {
            (exponent - 4,): 0 for exponent in range(8)
        }
        reverse_cycle = itertools.cycle(
            (True, False, False, True, False, True, True, False)
        )
        register_interval_exponents_counter.update({tuple([]): 0})
        last_assigned_register_interval = None
        for part_parts in itertools.zip_longest(*abstract_part_representations):
            if next(reverse_cycle):
                part_parts = reversed(part_parts)
            for part_part in part_parts:
                if part_part and hasattr(part_part, "assign_register_interval"):
                    last_assigned_register_interval = (
                        part_part.assign_register_interval(
                            last_assigned_register_interval,
                            register_interval_exponents_counter,
                        )
                    )
                    register_interval_exponents_counter[
                        last_assigned_register_interval.exponents
                    ] += 1

    def _convert_abstract_part_representation_to_sequential_event(
        self, abstract_part_representation: AbstractPartRepresentation, dynamic: str
    ) -> events.basic.SequentialEvent:
        sequential_event = events.basic.SequentialEvent([])
        is_first = True
        for part_part in abstract_part_representation:
            if isinstance(part_part, ImbalPhrase):
                sequential_event.extend(part_part.convert_to_sequential_event(dynamic))
            else:
                if is_first:
                    sequential_event.append(
                        events.music.NoteLike([], part_part.duration, dynamic)
                    )
                else:
                    sequential_event.extend(
                        part_part.convert_to_rhythmical_pattern(dynamic)
                    )
            is_first = False

        sequential_event.tie_by(
            lambda ev0, ev1: is_note(ev0) is None and is_note(ev0) == is_note(ev1)
        )
        sequential_event.tie_by(
            lambda ev0, ev1: hasattr(ev0, "pitch_or_pitches")
            and hasattr(ev1, "pitch_or_pitches")
            and ev0.pitch_or_pitches == ev1.pitch_or_pitches
            and hasattr(ev0, "playing_indicators")
            and not ev0.playing_indicators.tie.is_active
        )
        return sequential_event

    def convert(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        cengkok_line: events.basic.SequentialEvent[events.music.NoteLike],
    ) -> typing.Tuple[events.basic.SequentialEvent, events.basic.SequentialEvent]:
        distributed_bars = RestructuredPhrasePartsAndCengkokLineToImbalBasedRootMelodiesConverter._distribute_bars(
            len(restructured_phrase_parts), self._percentage_of_single_populated_bars
        )
        abstract_part_representations = tuple(
            RestructuredPhrasePartsAndCengkokLineToImbalBasedRootMelodiesConverter._make_abstract_part_representation(
                restructured_phrase_parts,
                bar_distribution,
            )
            for bar_distribution in distributed_bars
        )
        RestructuredPhrasePartsAndCengkokLineToImbalBasedRootMelodiesConverter._assign_register_intervals_to_abstract_part_representations(
            abstract_part_representations
        )
        dynamic = "mp"
        sequential_events = []
        for abstract_part_representation in abstract_part_representations:
            sequential_event = (
                self._convert_abstract_part_representation_to_sequential_event(
                    abstract_part_representation, dynamic
                )
            )
            sequential_events.append(sequential_event)

        return tuple(sequential_events)
