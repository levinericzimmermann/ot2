"""base for river cengkoks

"""

import dataclasses
import typing


import abjad

from mutwo import converters
from mutwo import events
from mutwo import parameters

from ot2 import analysis


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class BarCharacter(object):
    character: str
    keys: typing.Optional[typing.Dict[str, typing.Any]] = None


MOVING = BarCharacter("moving")
CADENZA = BarCharacter("cadenza")
END = BarCharacter("end")
END_AND_START = BarCharacter("end-and-start")
START = BarCharacter("start")
REST = BarCharacter("rest")


class RestructuredPhrasePart(analysis.phrases.PhraseEvent):
    """Redefine which pitch is which scale index (1, 2, 3, 4, 5, 6)"""

    def __init__(
        self,
        phrase_event_to_restructure: analysis.phrases.PhraseEvent,
        bar_character: BarCharacter,
        time_signature: abjad.TimeSignature,
    ):
        super().__init__(
            phrase_event_to_restructure.duration,
            phrase_event_to_restructure.all_pitches,
            phrase_event_to_restructure.root,
            phrase_event_to_restructure.connection_pitch0,
            phrase_event_to_restructure.connection_pitch1,
            phrase_event_to_restructure.is_start_of_phrase,
        )

        def octave_mark_processor(
            pitch_to_process: parameters.pitches.JustIntonationPitch,
            octave_mark_to_apply: typing.Optional[str],
        ) -> parameters.pitches.JustIntonationPitch:
            if octave_mark_to_apply and pitch_to_process:
                processed_pitch = (
                    pitch_to_process
                    + parameters.pitches.JustIntonationPitch("1/1").register(
                        int(octave_mark_to_apply), mutate=False
                    )
                )
            else:
                processed_pitch = pitch_to_process.copy()
            return processed_pitch

        pitch_for_scale_index_4 = RestructuredPhrasePart._find_pitch_for_scale_index_4(
            phrase_event_to_restructure
        )
        restructured_pitches = RestructuredPhrasePart._restructure_pitches(
            phrase_event_to_restructure, pitch_for_scale_index_4
        )

        self._phrase_event = phrase_event_to_restructure
        self._restructured_pitches = restructured_pitches
        self._normalized_restructured_pitches = tuple(
            pitch.normalize(mutate=False) for pitch in self._restructured_pitches
        )
        self._scale_decodex = {
            str(index + 1): pitch
            for index, pitch in enumerate(self._restructured_pitches)
        }
        self._mmml_pitches_converter = converters.backends.mmml.MMMLPitchesConverter(
            converters.backends.mmml.MMMLSinglePitchConverter(
                self._scale_decodex, octave_mark_processor
            )
        )
        self._bar_character = bar_character
        self._time_signature = time_signature

    def __repr__(self) -> str:
        return f"RestructuredPhrasePart({self._time_signature}, {self._bar_character})"

    @staticmethod
    def _find_pitch_for_scale_index_4(
        phrase_event_to_restructure: analysis.phrases.PhraseEvent,
    ) -> parameters.pitches.JustIntonationPitch:
        prohibited_pitches_for_scale_index_4 = tuple(
            pitch.normalize(mutate=False)
            for pitch in (
                phrase_event_to_restructure.root,
                phrase_event_to_restructure.connection_pitch0,
                phrase_event_to_restructure.connection_pitch1,
            )
            if pitch
        )
        candidates_for_scale_index_4 = tuple(
            filter(
                lambda candidate: candidate not in prohibited_pitches_for_scale_index_4,
                phrase_event_to_restructure.normalized_all_pitches,
            )
        )

        harmonicity_per_candidate = []
        for candidate in candidates_for_scale_index_4:
            harmonicities = []
            for pitch in phrase_event_to_restructure.normalized_all_pitches:
                if pitch != candidate:
                    interval = candidate - pitch
                    interval.normalize()
                    harmonicities.append(interval.harmonicity_simplified_barlow)
            harmonicity = sum(harmonicities) / len(harmonicities)
            harmonicity_per_candidate.append(harmonicity)

        # the pitch with the lowest harmonicity to all other pitches will be pitch 4
        winner_index = harmonicity_per_candidate.index(min(harmonicity_per_candidate))
        winner = candidates_for_scale_index_4[winner_index]
        return winner

    @staticmethod
    def _restructure_pitches(
        phrase_event_to_restructure: analysis.phrases.PhraseEvent,
        pitch_for_scale_index_4: parameters.pitches.JustIntonationPitch,
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        winner_index_in_normalized_pitches = (
            phrase_event_to_restructure.normalized_all_pitches.index(
                pitch_for_scale_index_4
            )
        )
        expected_index_in_normalized_pitches = 3
        difference_between_expected_index_and_actual_index = (
            winner_index_in_normalized_pitches - expected_index_in_normalized_pitches
        )
        part0 = phrase_event_to_restructure.normalized_all_pitches[
            difference_between_expected_index_and_actual_index:
        ]
        if difference_between_expected_index_and_actual_index > 0:
            part1 = phrase_event_to_restructure.normalized_all_pitches[
                :difference_between_expected_index_and_actual_index
            ]
        else:
            part1 = phrase_event_to_restructure.normalized_all_pitches[
                : 6 + difference_between_expected_index_and_actual_index
            ]

        restructured_pitches = list(part0 + part1)

        assert len(restructured_pitches) == 6

        for pitch0, pitch1 in zip(
            restructured_pitches[expected_index_in_normalized_pitches:],
            restructured_pitches[expected_index_in_normalized_pitches + 1 :],
        ):
            if pitch1 < pitch0:
                pitch1.add(parameters.pitches.JustIntonationPitch("2/1"))

        for pitch0, pitch1 in reversed(
            tuple(
                zip(
                    restructured_pitches[: expected_index_in_normalized_pitches + 1],
                    restructured_pitches[1 : expected_index_in_normalized_pitches + 1],
                )
            )
        ):
            if pitch1 < pitch0:
                pitch0.subtract(parameters.pitches.JustIntonationPitch("2/1"))

        assert sorted(restructured_pitches) == restructured_pitches

        return tuple(restructured_pitches)

    @property
    def phrase_event(self) -> analysis.phrases.PhraseEvent:
        return self._phrase_event

    @property
    def bar_character(self) -> BarCharacter:
        return self._bar_character

    def get_scale_index_and_octave_mark(
        self, pitch_to_convert: parameters.pitches.JustIntonationPitch
    ) -> typing.Tuple[int, int]:
        pitch_index = self._normalized_restructured_pitches.index(
            pitch_to_convert.normalize(mutate=False)
        )
        difference = pitch_to_convert - self._restructured_pitches[pitch_index]
        if exponents := difference.exponents:
            octave_mark = exponents[0]
        else:
            octave_mark = 0
        return (pitch_index + 1, octave_mark)

    def convert_cengkok(
        self, cengkok_to_convert: typing.Tuple[str, typing.Tuple[int, ...]]
    ) -> events.basic.SequentialEvent[events.music.NoteLike]:
        pitches_to_convert, rhythms_to_convert = cengkok_to_convert
        converted_pitches = tuple(
            self._mmml_pitches_converter.convert(pitch_or_pitches)
            for pitch_or_pitches in pitches_to_convert.split(" ")
        )
        summed_rhythm = sum(rhythms_to_convert)
        rhythm_factor = self.duration / summed_rhythm
        converted_rhythms = tuple(
            rhythm * rhythm_factor for rhythm in rhythms_to_convert
        )
        sequential_event = events.basic.SequentialEvent([])
        for pitch_or_pitches, rhythm in zip(converted_pitches, converted_rhythms):
            note = events.music.NoteLike(list(pitch_or_pitches[0]), rhythm)
            sequential_event.append(note)
        return sequential_event

    def get_two_beat_cengkoks(
        self, goal_scale_index: int
    ) -> typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]], ...]:
        neighbour = [goal_scale_index - 1, goal_scale_index + 1]
        if neighbour[0] < 1:
            neighbour[0] = "6:-1"
        if neighbour[1] > 6:
            neighbour[2] = "1:1"

        cengkok0 = "{} {}".format(neighbour[0], goal_scale_index)
        cengkok1 = "{} {}".format(neighbour[1], goal_scale_index)

        cengkoks = tuple((cengkok, (1, 1)) for cengkok in (cengkok0, cengkok1))
        return cengkoks

    def filter_cengkok_candidates(
        self, irama: int = 1
    ) -> typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]], ...]:
        if self.phrase_event.connection_pitch1:
            goal_pitch = self.phrase_event.connection_pitch1
        else:
            goal_pitch = self.phrase_event.root

        goal_scale_index, _ = self.get_scale_index_and_octave_mark(goal_pitch)
        n_beats = self._time_signature.numerator * (2 ** (irama - 1))
        if n_beats == 32:
            n_beats = 16
        if n_beats == 2:
            return self.get_two_beat_cengkoks(goal_scale_index)
        elif n_beats == 1:
            return (
                (f"{goal_scale_index}", (1,)),
                (f"{goal_scale_index}:-1", (1,)),
                (f"{goal_scale_index}:1", (1,)),
            )
        else:
            return analysis.cengkoks.CENGKOKS[n_beats][goal_scale_index]
