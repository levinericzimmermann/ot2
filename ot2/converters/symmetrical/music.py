import copy
import fractions
import functools
import itertools
import operator
import typing

import expenvelope

from mutwo import converters
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches
from mutwo.parameters import tempos

from ot2.constants import instruments
from ot2.converters import symmetrical
from ot2 import events as ot2_events
from ot2.generators import zimmermann

Music = ot2_events.basic.TaggedSimultaneousEvent[
    basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
]


class BarsWithHarmonyToMusicConverter(converters.abc.Converter):
    def _take_nth_pitch(
        self,
        bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...],
        nth_pitch: int,
        ambitus,
    ):
        sequential_event = basic.SequentialEvent([])
        for bar in bars_with_harmony:
            note = music.NoteLike(
                ambitus.find_all_pitch_variants(bar.harmonies[0][nth_pitch])[0],
                bar.duration,
                "pp",
            )
            sequential_event.append(note)
        return basic.SimultaneousEvent([sequential_event])

    def _make_rest(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ):
        sequential_event = basic.SequentialEvent([])
        for bar in bars_with_harmony:
            note = music.NoteLike([], bar.duration,)
            sequential_event.append(note)
        return basic.SimultaneousEvent([sequential_event])

    def _make_static_percussion(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        sequential_event = basic.SequentialEvent([])
        for bar in bars_with_harmony:
            is_first = True
            for subduration in bar[0]:
                if is_first:
                    pitch = "b"
                    is_first = False
                else:
                    pitch = "f"
                note = music.NoteLike(pitch, subduration.duration, "pp")
                sequential_event.append(note)
        return basic.SimultaneousEvent([sequential_event])

    def convert(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> Music:
        raise NotImplementedError()


class SimpleChordConverter(BarsWithHarmonyToMusicConverter):
    def convert(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> Music:
        return ot2_events.basic.TaggedSimultaneousEvent(
            (
                self._take_nth_pitch(
                    bars_with_harmony,
                    1,
                    instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
                ),
                self._take_nth_pitch(
                    bars_with_harmony,
                    2,
                    instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
                ),
                self._take_nth_pitch(
                    bars_with_harmony,
                    3,
                    instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
                ),
                self._take_nth_pitch(
                    bars_with_harmony, 0, instruments.AMBITUS_DRONE_INSTRUMENT
                ),
                self._make_static_percussion(bars_with_harmony),
                self._make_rest(bars_with_harmony),
            ),
            tag_to_event_index=instruments.INSTRUMENT_ID_TO_INDEX,
        )


class SimpleDingDongMelodyConverter(BarsWithHarmonyToMusicConverter):
    @staticmethod
    def _find_goal_for_mono_directional_phase(
        potential_goals: typing.Tuple[pitches.JustIntonationPitch, ...],
        simultaneous_pitches_for_each_pitch: typing.Tuple[
            typing.Tuple[pitches.JustIntonationPitch, ...], ...
        ],
    ) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
        sorted_potential_goals = sorted(potential_goals)
        intervals_between_goals_and_simultaenous_pitches = tuple(
            tuple(
                abs(goal - given_pitch)
                for given_pitch in simultaneous_pitches_for_each_pitch[-1]
            )
            for goal in sorted_potential_goals
        )
        filtered_potential_goals = zimmermann.filter_untunable_pitches(
            potential_goals,
            sorted_potential_goals,
            intervals_between_goals_and_simultaenous_pitches,
            2,
        )
        if filtered_potential_goals:
            pitches_to_sort = filtered_potential_goals
        else:
            pitches_to_sort = potential_goals

        sorted_potential_goals = zimmermann.sort_pitches_by_harmonicity(
            pitches_to_sort,
            sorted_potential_goals,
            intervals_between_goals_and_simultaenous_pitches,
        )

        return sorted_potential_goals[0]

    @staticmethod
    def _make_mono_direction_phrase(
        direction: bool,
        potential_goals: typing.Tuple[pitches.JustIntonationPitch, ...],
        available_pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        simultaneous_pitches_for_each_pitch: typing.Tuple[
            typing.Tuple[pitches.JustIntonationPitch, ...], ...
        ],
    ) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
        goal = SimpleDingDongMelodyConverter._find_goal_for_mono_directional_phase(
            potential_goals, simultaneous_pitches_for_each_pitch
        )
        choosen_pitches = [goal]
        for simultaneous_pitches in reversed(simultaneous_pitches_for_each_pitch[:-1]):
            choosen_pitch = zimmermann.find_next_melodic_pitch(
                choosen_pitches[-1],
                available_pitches,
                not direction,
                simultaneous_pitches,
            )
            choosen_pitches.append(choosen_pitch)
        return tuple(reversed(choosen_pitches))

    @staticmethod
    def _sort_connection_pitches_by_harmonicity(
        potential_connection_pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
        roots: typing.Tuple[pitches.JustIntonationPitch, ...],
    ) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
        pitch_fitness_pairs = []
        for pitch in potential_connection_pitches:
            fitness = sum(
                (pitch - root).harmonicity_simplified_barlow for root in roots
            )
            pitch_fitness_pairs.append((pitch, fitness))
        return tuple(
            pitch
            for pitch, _ in sorted(
                pitch_fitness_pairs, reverse=True, key=operator.itemgetter(1)
            )
        )

    @staticmethod
    def _make_pitches_for_main_melody(
        bar0: ot2_events.bars.BarWithHarmony,
        bar1: ot2_events.bars.BarWithHarmony,
        direction: bool,
        n_notes_left: int,
        n_notes_right: int,
    ) -> typing.Tuple[
        typing.Tuple[pitches.JustIntonationPitch, ...],
        typing.Tuple[pitches.JustIntonationPitch, ...],
    ]:
        connection_pitches = bar0.harmonies[-1]
        connection_pitches = tuple(
            pitch
            for pitch in connection_pitches
            if pitch.normalize(mutate=False) != pitches.JustIntonationPitch()
        )
        roots = (bar0.harmonies[0][0], bar1.harmonies[0][0])
        sorted_connection_pitches = SimpleDingDongMelodyConverter._sort_connection_pitches_by_harmonicity(
            connection_pitches, roots,
        )
        possible_goals = functools.reduce(
            operator.add,
            (
                tuple(
                    reversed(
                        instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.find_all_pitch_variants(
                            pitch
                        )
                    )
                )
                for pitch in sorted_connection_pitches
            ),
        )
        available_pitches0 = tuple(
            sorted(
                functools.reduce(
                    operator.add,
                    (
                        instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.find_all_pitch_variants(
                            pitch
                        )
                        for pitch in bar0.harmonies[0]
                    ),
                )
            )
        )
        available_pitches1 = tuple(
            sorted(
                functools.reduce(
                    operator.add,
                    (
                        instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.find_all_pitch_variants(
                            pitch
                        )
                        for pitch in bar1.harmonies[0]
                    ),
                )
            )
        )
        drone_pitch0, drone_pitch1 = (
            instruments.AMBITUS_DRONE_INSTRUMENT.find_all_pitch_variants(
                bar.harmonies[0][0]
            )[0]
            for bar in (bar0, bar1)
        )
        simultaneous_pitches_for_each_pitch_left = tuple(
            (drone_pitch0,) for _ in range(n_notes_left - 1)
        )
        simultaneous_pitches_for_each_pitch_right = tuple(
            (drone_pitch1,) for _ in range(n_notes_right - 1)
        )
        simultaneous_pitches_for_each_pitch_left += ((drone_pitch0, drone_pitch1),)
        simultaneous_pitches_for_each_pitch_right += ((drone_pitch0, drone_pitch1),)
        pitches_left = SimpleDingDongMelodyConverter._make_mono_direction_phrase(
            direction,
            possible_goals,
            available_pitches0,
            simultaneous_pitches_for_each_pitch_left,
        )
        choosen_goal = (pitches_left[-1],)
        pitches_right = tuple(
            reversed(
                SimpleDingDongMelodyConverter._make_mono_direction_phrase(
                    direction,
                    choosen_goal,
                    available_pitches1,
                    simultaneous_pitches_for_each_pitch_right,
                )
            )
        )
        return pitches_left, pitches_right

    @staticmethod
    def _find_most_balanced_rhythm_for_given_absolute_beats(
        possible_absolute_beats_per_pitch: typing.Tuple[
            typing.Tuple[fractions.Fraction, ...], ...
        ]
    ) -> typing.Tuple[fractions.Fraction, ...]:
        # simple brute force searching
        solution_and_fitness_pairs = []
        for absolute_beats in itertools.product(*possible_absolute_beats_per_pitch):
            difference_between_beats = tuple(
                beat1 - beat0
                for beat0, beat1 in zip(absolute_beats, absolute_beats[1:])
            )
            fitness = sum(
                abs(diff0 - diff1)
                for diff0, diff1 in itertools.combinations(difference_between_beats, 2)
            ) / len(difference_between_beats)
            solution_and_fitness_pairs.append((absolute_beats, fitness))
        best = sorted(solution_and_fitness_pairs, key=operator.itemgetter(1))[0][0]
        return best

    @staticmethod
    def _make_rhythm_for_main_melody(
        bar0: ot2_events.bars.BarWithHarmony,
        bar1: ot2_events.bars.BarWithHarmony,
        n_notes_left: int,
        n_notes_right: int,
    ) -> typing.Tuple[
        typing.Tuple[fractions.Fraction, ...], typing.Optional[fractions.Fraction]
    ]:
        subdivisions_left = bar0[0].absolute_times[-n_notes_left:]
        subdivisions_right = bar1[0].absolute_times[: n_notes_right + 1]
        absolute_beats_left = bar0[1].absolute_times
        absolute_beats_right = bar1[1].absolute_times
        bar0_duration = bar0.duration
        absolute_beats_left_per_division = tuple(
            tuple(beat for beat in absolute_beats_left if beat > sub0 and beat < sub1)
            for sub0, sub1 in zip(
                subdivisions_left, subdivisions_left[1:] + (bar0_duration,)
            )
        )
        absolute_beats_right_per_division = tuple(
            tuple(
                beat + bar0_duration
                for beat in absolute_beats_right
                if beat > sub0 and beat < sub1
            )
            for sub0, sub1 in zip(subdivisions_right, subdivisions_right[1:])
        )
        possible_absolute_beats_per_pitch = (
            absolute_beats_left_per_division + absolute_beats_right_per_division
        )
        most_balanced_rhythm = SimpleDingDongMelodyConverter._find_most_balanced_rhythm_for_given_absolute_beats(
            possible_absolute_beats_per_pitch
        )
        if most_balanced_rhythm[0] == 0:
            rest = None
        else:
            rest = most_balanced_rhythm[0]

        rhythm = tuple(
            absolute_beat1 - absolute_beat0
            for absolute_beat0, absolute_beat1 in zip(
                most_balanced_rhythm, most_balanced_rhythm[1:]
            )
        )
        return rhythm, rest

    def _make_main_melody_phrase(
        self,
        bar0: ot2_events.bars.BarWithHarmony,
        bar1: ot2_events.bars.BarWithHarmony,
        direction: bool,
        n_notes_left: int,
        n_notes_right: int,
    ) -> basic.SequentialEvent[music.NoteLike]:
        left_pitches, right_pitches = self._make_pitches_for_main_melody(
            bar0, bar1, direction, n_notes_left, n_notes_right
        )
        rhythm, rest_duration = self._make_rhythm_for_main_melody(
            bar0, bar1, n_notes_left, n_notes_right
        )
        sequential_event = basic.SequentialEvent(
            [
                music.NoteLike(pitch, duration, "pp")
                for pitch, duration in zip(left_pitches + right_pitches[1:], rhythm)
            ]
        )
        sequential_event.insert(0, music.NoteLike([], rest_duration))
        difference = (bar0.duration + bar1.duration) - sequential_event.duration
        if difference > 0:
            sequential_event.append(music.NoteLike([], difference))
        return sequential_event

    def _make_main_melody(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent:
        n_notes_left_cycle = itertools.cycle((3, 2))
        n_notes_right_cycle = itertools.cycle((2, 3))
        direction_cycle = itertools.cycle((True, False,))
        sequential_event = basic.SequentialEvent([])
        is_first = True
        cut_off_position = 0
        for bar0, bar1 in zip(bars_with_harmony, bars_with_harmony[1:]):
            melodic_phrase = self._make_main_melody_phrase(
                bar0,
                bar1,
                next(direction_cycle),
                next(n_notes_left_cycle),
                next(n_notes_right_cycle),
            )
            if is_first:
                sequential_event.extend(melodic_phrase)
                is_first = False

            else:
                cut_at = melodic_phrase[0].duration
                sequential_event.cut_off(
                    cut_off_position + cut_at, sequential_event.duration
                )
                sequential_event.extend(melodic_phrase[1:])

            cut_off_position += bar0.duration

        return basic.SimultaneousEvent([sequential_event])

    def _make_adjusted_main_melody(
        self,
        main_melody: basic.SimultaneousEvent,
        interval: pitches.JustIntonationPitch = pitches.JustIntonationPitch("4/5"),
    ) -> basic.SimultaneousEvent:
        adjusted_main_melody = copy.deepcopy(main_melody)
        adjusted_main_melody.set_parameter(
            "pitch_or_pitches",
            lambda pitch_or_pitches: [pitch + interval for pitch in pitch_or_pitches],
        )
        return adjusted_main_melody

    def _make_interlocking_drone(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent:
        voices = basic.SimultaneousEvent(
            [basic.SequentialEvent([]), basic.SequentialEvent([])]
        )

        n_bars = len(bars_with_harmony)

        previous_pitch = None
        previous_voice = 1

        for nth_bar, bar_with_harmony in enumerate(bars_with_harmony):
            root = bar_with_harmony.harmony_per_beat[0][0]
            root_variants = instruments.AMBITUS_DRONE_INSTRUMENT.find_all_pitch_variants(
                root
            )
            pitch = root_variants[0]
            duration = bar_with_harmony.duration

            if previous_pitch == pitch:
                voice_to_append, voice_to_sleep = (
                    voices[previous_voice],
                    voices[not previous_voice],
                )
                voice_to_append[-1].duration += duration

            else:
                note = music.NoteLike(pitch, duration, "pp")

                if previous_voice == 1:
                    voice_to_append, voice_to_sleep = voices[0], voices[1]
                    previous_voice = 0
                else:
                    voice_to_append, voice_to_sleep = voices[1], voices[0]
                    previous_voice = 1

                voice_to_append.append(note)

                if nth_bar > 0:
                    previous_bar_with_harmony = bars_with_harmony[nth_bar - 1]
                    add_by = previous_bar_with_harmony[0][-1].duration
                    voice_to_append[-1].duration += add_by
                    voice_to_append[-2].duration -= add_by

            rest = music.NoteLike([], duration)
            voice_to_sleep.append(rest)

            if nth_bar + 1 == n_bars:
                voice_to_append[-1].duration -= bar_with_harmony[0][-1].duration
                voice_to_append.append(
                    music.NoteLike([], bar_with_harmony[0][-1].duration)
                )

            previous_pitch = pitch

        return voices

    def convert(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> Music:
        main_melody = self._make_main_melody(bars_with_harmony)
        adjusted_main_melody = self._make_adjusted_main_melody(
            main_melody, interval=pitches.JustIntonationPitch("4/5")
        )
        adjusted_main_melody0 = self._make_adjusted_main_melody(
            main_melody, interval=pitches.JustIntonationPitch("7/12")
        )
        return ot2_events.basic.TaggedSimultaneousEvent(
            (
                main_melody,
                # adjusted_main_melody,
                adjusted_main_melody0,
                # self._make_rest(bars_with_harmony),
                self._take_nth_pitch(
                    bars_with_harmony,
                    2,
                    instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
                ),
                self._make_interlocking_drone(bars_with_harmony),
                self._make_static_percussion(bars_with_harmony),
                self._make_rest(bars_with_harmony),
            ),
            tag_to_event_index=instruments.INSTRUMENT_ID_TO_INDEX,
        )


class DataToMusicConverter(converters.abc.Converter):
    @staticmethod
    def _tie_rests(sequential_event: basic.SequentialEvent):
        new_sequential_event = []
        for nth_event, event in enumerate(sequential_event):
            if nth_event != 0:
                tests = (
                    len(event.pitch_or_pitches) == 0,
                    len(new_sequential_event[-1].pitch_or_pitches) == 0,
                )

                if all(tests):
                    new_sequential_event[-1].duration += event.duration
                else:
                    new_sequential_event.append(event)
            else:
                new_sequential_event.append(event)
        return basic.SequentialEvent(new_sequential_event)

    def _convert_bars_with_harmony(
        self,
        bars_with_harmony_to_convert: typing.Tuple[ot2_events.bars.BarWithHarmony, ...],
    ) -> typing.Tuple[Music, expenvelope.Envelope]:
        raise NotImplementedError()

    def convert(
        self,
        bars_maker: zimmermann.nested_loops.BarsMaker,
        bars_to_bars_with_harmony_converter: symmetrical.bars.BarsToBarsWithHarmonyConverter,
    ) -> typing.Tuple[
        Music, typing.Tuple[ot2_events.bars.BarWithHarmony, ...], expenvelope.Envelope
    ]:
        bars_with_harmony = bars_to_bars_with_harmony_converter.convert(bars_maker())
        tagged_simultaneous_event, tempo_envelope = self._convert_bars_with_harmony(
            bars_with_harmony
        )
        for nth_simultaneous_event, simultaneous_event in enumerate(
            tagged_simultaneous_event
        ):
            for nth_sequential_event, sequential_event in enumerate(simultaneous_event):
                tagged_simultaneous_event[nth_simultaneous_event][
                    nth_sequential_event
                ] = self._tie_rests(sequential_event)
        return tagged_simultaneous_event, bars_with_harmony, tempo_envelope


class DummyDataToMusicConverter(DataToMusicConverter):
    def _convert_bars_with_harmony(
        self,
        bars_with_harmony_to_convert: typing.Tuple[ot2_events.bars.BarWithHarmony, ...],
    ) -> typing.Tuple[Music, expenvelope.Envelope]:
        converter = SimpleDingDongMelodyConverter()
        return (
            converter.convert(bars_with_harmony_to_convert),
            (
                expenvelope.Envelope.from_points(
                    (0, tempos.TempoPoint(40, fractions.Fraction(1, 1))),
                    (1, tempos.TempoPoint(40, fractions.Fraction(1, 1))),
                )
            ),
        )
