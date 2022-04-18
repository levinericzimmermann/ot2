"""Convert analysis.phrases to time brackets.

Conversion routines for Part "B" (cengkok based / cantus-firmus based parts).
"""

import functools
import fractions
import operator
import typing

from mu.utils.tools import complex_backtracking

from mutwo import converters
from mutwo import events
from mutwo import parameters

from ot2 import analysis
from ot2 import events as ot2_events
from ot2 import constants as ot2_constants
from ot2 import parameters as ot2_parameters
from ot2.converters.symmetrical import keyboard as keyboard_converter


from . import base


class PhraseToGongConverter(converters.abc.Converter):
    gong_register = -2
    dynamic = "p"

    def __init__(self, skip_first_event: bool = True):
        self._skip_first_event = skip_first_event

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> events.basic.TaggedSimultaneousEvent:
        gongs = events.basic.SequentialEvent([])
        is_first = True
        for phrase_event in phrase_to_convert:
            if (
                not (is_first and self._skip_first_event)
                and phrase_event.is_start_of_phrase
            ):
                gong = events.music.NoteLike(
                    phrase_event.root.register(self.gong_register, mutate=False),
                    phrase_to_convert.duration,
                    self.dynamic,
                )
                gongs.append(gong)
            else:
                rest = events.music.NoteLike(
                    [], duration=phrase_event.duration, volume=self.dynamic
                )
                gongs.append(rest)

            is_first = False

        return events.basic.TaggedSimultaneousEvent(
            [gongs], tag=ot2_constants.instruments.ID_GONG
        )


class PhraseToKeyboardOctavesConverter(converters.abc.Converter):
    def __init__(
        self,
        dynamic: str = "mf",
        modulation_interval_right_hand: typing.Optional[
            parameters.pitches.JustIntonationPitch
        ] = parameters.pitches.JustIntonationPitch(),
        modulation_interval_left_hand: typing.Optional[
            parameters.pitches.JustIntonationPitch
        ] = parameters.pitches.JustIntonationPitch("1/2"),
    ):
        self._dynamic = dynamic
        self._modulation_interval_left_hand = modulation_interval_left_hand
        self._modulation_interval_right_hand = modulation_interval_right_hand

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> events.basic.TaggedSimultaneousEvent:
        keyboard = events.basic.TaggedSimultaneousEvent(
            [events.basic.SequentialEvent([]) for _ in range(2)],
            tag=ot2_constants.instruments.ID_KEYBOARD,
        )
        for bar in phrase_to_convert:
            if self._modulation_interval_right_hand:
                right_hand_pitch = bar.root + self._modulation_interval_right_hand
            else:
                right_hand_pitch = []
            keyboard[0].append(
                events.music.NoteLike(
                    right_hand_pitch,
                    bar.duration,
                    self._dynamic,
                )
            )
            if self._modulation_interval_left_hand:
                left_hand_pitch = bar.root + self._modulation_interval_left_hand
            else:
                left_hand_pitch = []
            keyboard[1].append(
                events.music.NoteLike(
                    left_hand_pitch,
                    bar.duration,
                    self._dynamic,
                )
            )

        return keyboard


class PhraseToRootMelodyConverter(converters.abc.Converter):
    def __init__(
        self,
        instrument_id: str = ot2_constants.instruments.ID_SUS0,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus = ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
        dynamic: str = "mp",
        prefered_pitch_candidate_index: int = 0,
    ):
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._dynamic = dynamic
        self._prefered_pitch_candidate_index = prefered_pitch_candidate_index

    def _generate_pitch_line(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        pitches = []
        for phrase in phrase_to_convert:
            pitch = phrase.root
            pitches.append(pitch)
        pitch_variants = tuple(
            self._instrument_ambitus.find_all_pitch_variants(pitch) for pitch in pitches
        )
        candidate_and_fitness_pairs = []
        for start_pitch in pitch_variants[0]:
            candidate = [start_pitch]
            fitness = 0
            for next_pitches in pitch_variants[1:]:
                distances = tuple(
                    abs((pitch - candidate[-1]).cents) for pitch in next_pitches
                )
                smallest_distance = min(distances)
                fitness += smallest_distance
                choosen_pitch = next_pitches[distances.index(smallest_distance)]
                candidate.append(choosen_pitch)
            candidate_and_fitness_pairs.append((tuple(candidate), fitness))

        candidates, fitness = zip(*candidate_and_fitness_pairs)
        smallest_fitness = min(fitness)
        filtered_candidates = tuple(
            candidate
            for index, candidate in enumerate(candidates)
            if fitness[index] == smallest_fitness
        )

        try:
            return filtered_candidates[self._prefered_pitch_candidate_index]
        except IndexError:
            return filtered_candidates[0]

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> events.basic.TaggedSimultaneousEvent:
        root_melody = events.basic.TaggedSimultaneousEvent(
            [events.basic.SequentialEvent([])],
            tag=self._instrument_id,
        )
        pitch_line = self._generate_pitch_line(phrase_to_convert)
        for bar, pitch in zip(phrase_to_convert, pitch_line):
            root_melody[0].append(
                events.music.NoteLike(
                    pitch,
                    bar.duration,
                    self._dynamic,
                )
            )
        return root_melody


class PhraseToConnectionPitchesMelodyConverter(converters.abc.Converter):
    def __init__(
        self,
        instrument_id: str = ot2_constants.instruments.ID_SUS0,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus = ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
        dynamic: str = "mp",
        prefered_pitch_candidate_index: int = 1,
    ):
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._dynamic = dynamic
        self._prefered_pitch_candidate_index = prefered_pitch_candidate_index

    def _generate_pitch_line(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        pitches = []
        for phrase in phrase_to_convert:
            pitch = phrase.connection_pitch1
            if not pitch:
                pitch = phrase.root
            pitches.append(pitch)
        pitch_variants = tuple(
            self._instrument_ambitus.find_all_pitch_variants(pitch) for pitch in pitches
        )
        candidate_and_fitness_pairs = []
        for start_pitch in pitch_variants[0]:
            candidate = [start_pitch]
            fitness = 0
            for next_pitches in pitch_variants[1:]:
                distances = tuple(
                    abs((pitch - candidate[-1]).cents) for pitch in next_pitches
                )
                smallest_distance = min(distances)
                fitness += smallest_distance
                choosen_pitch = next_pitches[distances.index(smallest_distance)]
                candidate.append(choosen_pitch)
            candidate_and_fitness_pairs.append((tuple(candidate), fitness))

        candidates, fitness = zip(*candidate_and_fitness_pairs)
        smallest_fitness = min(fitness)
        filtered_candidates = tuple(
            candidate
            for index, candidate in enumerate(candidates)
            if fitness[index] == smallest_fitness
        )

        try:
            return filtered_candidates[self._prefered_pitch_candidate_index]
        except IndexError:
            return filtered_candidates[0]

    def _generate_rhythmic_line(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> tuple[fractions.Fraction, ...]:
        rhythmic_line = []
        for phrase0, phrase1 in zip(phrase_to_convert, phrase_to_convert[1:]):
            rhythmic_line.append(
                (phrase0.duration * fractions.Fraction(1, 2))
                + (phrase1.duration * fractions.Fraction(1, 2))
            )
        rhythmic_line.append(phrase_to_convert[-1].duration * fractions.Fraction(1, 2))
        return tuple(rhythmic_line)

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> events.basic.TaggedSimultaneousEvent:
        sequential_event = events.basic.SequentialEvent(
            [events.music.NoteLike([], phrase_to_convert[0].duration * 0.5)]
        )
        pitch_line = self._generate_pitch_line(phrase_to_convert)
        rhythmic_line = self._generate_rhythmic_line(phrase_to_convert)
        for pitch, rhythm in zip(pitch_line, rhythmic_line):
            note = events.music.NoteLike(pitch, rhythm, self._dynamic)
            sequential_event.append(note)
        sequential_event.tie_by(
            condition=lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
        )
        melody_line = events.basic.TaggedSimultaneousEvent(
            [sequential_event],
            tag=self._instrument_id,
        )
        base.PhraseToTimeBracketsConverter._add_cent_deviation(melody_line[0])
        return melody_line


Duration = parameters.abc.DurationType
SimultaneousPitches = tuple[
    parameters.pitches.JustIntonationPitch, parameters.pitches.JustIntonationPitch
]
AvailablePitches = tuple[parameters.pitches.JustIntonationPitch, ...]
BacktrackingData = tuple[tuple[Duration, SimultaneousPitches, AvailablePitches], ...]


class PhraseToContapunctusSimpliccisimusConverter(converters.abc.Converter):
    harmonicity_border = 0.04

    def __init__(
        self,
        instrument_id: str = ot2_constants.instruments.ID_SUS2,
        instrument_ambitus: ot2_parameters.ambitus.Ambitus = ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
        dynamic: str = "mp",
        prefered_pitch_candidate_index: int = 1,
        remove_repeating_pitches: bool = True,
        start_max_distance: float = 250,
    ):
        self._start_max_distance = start_max_distance
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._dynamic = dynamic
        self._prefered_pitch_candidate_index = prefered_pitch_candidate_index
        self._remove_repeating_pitches = remove_repeating_pitches

    def _generate_pitch_line(
        self,
        backtracking_data: BacktrackingData,
    ) -> tuple[parameters.pitches.JustIntonationPitch, ...]:
        _, _, available_pitches_per_item = zip(*backtracking_data)

        def make_tests(max_distance: float = 230):
            def test_melodic_distance(
                pitch_line: tuple[parameters.pitches.JustIntonationPitch],
            ) -> bool:
                for pitch0, pitch1 in zip(pitch_line, pitch_line[1:]):
                    interval = pitch1 - pitch0
                    interval.normalize()
                    if abs(interval.cents) > max_distance:
                        return False
                return True

            return (test_melodic_distance,)

        max_distance = self._start_max_distance
        pitch_line = None
        while not pitch_line:
            try:
                pitch_line = complex_backtracking(
                    available_pitches_per_item, make_tests(max_distance)
                )
            except ValueError:
                max_distance += 50
            if max_distance > 1200:
                raise ValueError(
                    f"CAN'T FIND SOLUTION FOR {available_pitches_per_item} (reached max_distance = {max_distance})"
                )
        return pitch_line

    def _fetch_available_pitches(
        self,
        simultaneous_pitches: SimultaneousPitches,
        available_pitches: AvailablePitches,
    ) -> AvailablePitches:
        available_pitches = functools.reduce(
            operator.add,
            (
                self._instrument_ambitus.find_all_pitch_variants(pitch)
                for pitch in available_pitches
            ),
        )
        dissonant_pitches = []
        repeating_pitches = []
        for pitch in available_pitches:
            for other_pitch in simultaneous_pitches:
                interval = pitch - other_pitch
                interval.normalize()
                if interval == parameters.pitches.JustIntonationPitch():
                    if pitch not in repeating_pitches:
                        repeating_pitches.append(pitch)
                cents = interval.cents
                if (
                    cents <= 230
                    or cents >= 1000
                    or interval.harmonicity_simplified_barlow < self.harmonicity_border
                ):
                    if pitch not in dissonant_pitches:
                        dissonant_pitches.append(pitch)

        prohibited_pitches = dissonant_pitches
        if self._remove_repeating_pitches:
            prohibited_pitches += repeating_pitches

        remaining_pitches = tuple(
            pitch for pitch in available_pitches if pitch not in prohibited_pitches
        )
        if not remaining_pitches:
            remaining_pitches = tuple(repeating_pitches)
        return remaining_pitches

    def _generate_backtracking_data(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> BacktrackingData:
        backtracking_data = []
        is_first = True
        for phrase_event in phrase_to_convert:
            duration = phrase_event.duration * fractions.Fraction(1, 2)
            all_pitches = phrase_event.all_pitches
            if not is_first:
                # first for connection pitch 0
                simultaneous_pitches = (
                    phrase_event.root,
                    phrase_event.connection_pitch0,
                )
                available_pitches = self._fetch_available_pitches(
                    simultaneous_pitches, all_pitches
                )
                backtracking_data.append(
                    (duration, simultaneous_pitches, available_pitches)
                )

            # again for connection pitch 1
            simultaneous_pitches = (phrase_event.root, phrase_event.connection_pitch1)
            available_pitches = self._fetch_available_pitches(
                simultaneous_pitches, all_pitches
            )
            backtracking_data.append(
                (duration, simultaneous_pitches, available_pitches)
            )

            is_first = False

        return backtracking_data

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> events.basic.TaggedSimultaneousEvent:
        sequential_event = events.basic.SequentialEvent(
            [events.music.NoteLike([], phrase_to_convert[0].duration * 0.5)]
        )
        backtracking_data = self._generate_backtracking_data(phrase_to_convert)
        pitch_line = self._generate_pitch_line(backtracking_data)
        rhythmic_line, _, _ = zip(*backtracking_data)
        for pitch, rhythm in zip(pitch_line, rhythmic_line):
            note = events.music.NoteLike(pitch, rhythm, self._dynamic)
            sequential_event.append(note)
        sequential_event.tie_by(
            condition=lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
        )
        melody_line = events.basic.TaggedSimultaneousEvent(
            [sequential_event],
            tag=self._instrument_id,
        )
        base.PhraseToTimeBracketsConverter._add_cent_deviation(melody_line[0])
        return melody_line


class SimplePhraseToTimeBracketsConverter(base.PhraseToTimeBracketsConverter):
    def __init__(
        self,
        start_or_start_range: events.time_brackets.TimeOrTimeRange,
        end_or_end_range: events.time_brackets.TimeOrTimeRange,
        phrase_to_connection_pitches_melody_converter: typing.Optional[
            PhraseToConnectionPitchesMelodyConverter
        ] = PhraseToConnectionPitchesMelodyConverter(),
        phrase_to_keyboard_octaves_converter: typing.Optional[
            PhraseToKeyboardOctavesConverter
        ] = PhraseToKeyboardOctavesConverter(),
        phrase_to_gong_converter: typing.Optional[
            PhraseToGongConverter
        ] = PhraseToGongConverter(),
    ):
        super().__init__(start_or_start_range, end_or_end_range)
        self._phrase_to_connection_pitches_melody_converter = (
            phrase_to_connection_pitches_melody_converter
        )
        self._phrase_to_keyboard_octaves_converter = (
            phrase_to_keyboard_octaves_converter
        )
        self._phrase_to_gong_converter = phrase_to_gong_converter

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> typing.Tuple[base.CengkokTimeBracket, ...]:
        time_bracket = self._make_time_bracket_blueprint(phrase_to_convert)
        time_bracket.engine_distribution_strategy = keyboard_converter.ComplexEngineDistributionStrategy(
            keyboard_converter.ByHandsDivisionStrategy(),
            (
                keyboard_converter.SimpleEngineDistributionPartStrategy(
                    3
                ),
                keyboard_converter.SimpleEngineDistributionPartStrategy(
                    1
                ),
            ),
        )
        tape_time_bracket = self._make_time_bracket_blueprint(phrase_to_convert)

        if self._phrase_to_connection_pitches_melody_converter:
            connection_pitches_melody = (
                self._phrase_to_connection_pitches_melody_converter.convert(
                    phrase_to_convert
                )
            )
            time_bracket.append(connection_pitches_melody)

        if self._phrase_to_keyboard_octaves_converter:
            keyboard = self._phrase_to_keyboard_octaves_converter.convert(
                phrase_to_convert
            )
            time_bracket.append(keyboard)

        if self._phrase_to_gong_converter:
            gong = self._phrase_to_gong_converter.convert(phrase_to_convert)
            tape_time_bracket.append(gong)

        return (time_bracket, tape_time_bracket)


class SimplePhraseWithSimpleContrapunctusToTimeBracketsConverter(
    SimplePhraseToTimeBracketsConverter
):
    def __init__(
        self,
        *args,
        phrase_to_contapunctus_simpliccisimus_converter: PhraseToContapunctusSimpliccisimusConverter = PhraseToContapunctusSimpliccisimusConverter(),
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._phrase_to_contapunctus_simpliccisimus_converter = (
            phrase_to_contapunctus_simpliccisimus_converter
        )

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> typing.Tuple[base.CengkokTimeBracket, ...]:
        time_brackets = super().convert(phrase_to_convert)

        contapunctus_simpliccisimus = (
            self._phrase_to_contapunctus_simpliccisimus_converter.convert(
                phrase_to_convert
            )
        )

        time_brackets[0].insert(1, contapunctus_simpliccisimus)
        return time_brackets
