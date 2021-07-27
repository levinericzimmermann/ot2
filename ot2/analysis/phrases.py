"""Split applied cantus firmus in parts and split parts in phrases.

The cantus firmus has 11 parts (11 repetitions / transpostions of the same melody).
Each part has four phrases.
Each phrase has four pitches (the last part has five pitches).

Furthermore assign duration in seconds to each event.
"""

import copy
import functools
import operator
import pickle
import typing

from mutwo.events import basic
from mutwo.parameters import pitches
from mutwo.parameters import volumes

from ot2.analysis import phrases_constants
from ot2.generators.zimmermann import pulse_transitions


class PhraseEvent(basic.SimpleEvent):
    def __init__(
        self,
        duration,
        all_pitches: typing.Tuple[pitches.JustIntonationPitch],
        root: pitches.JustIntonationPitch,
        connection_pitch0: typing.Optional[pitches.JustIntonationPitch],
        connection_pitch1: typing.Optional[pitches.JustIntonationPitch],
    ):
        super().__init__(duration)
        self.all_pitches = all_pitches
        self.normalized_all_pitches = tuple(
            pitch.normalize(mutate=False) for pitch in self.all_pitches
        )
        self.root = root
        self.connection_pitch0 = connection_pitch0
        if self.connection_pitch0:
            self.connection_pitch0_index = self.normalized_all_pitches.index(
                connection_pitch0
            )
        else:
            self.connection_pitch0_index = None
        self.connection_pitch1 = connection_pitch1
        if self.connection_pitch1:
            self.connection_pitch1_index = self.normalized_all_pitches.index(
                connection_pitch1
            )
        else:
            self.connection_pitch1_index = None


Phrases = typing.Tuple[basic.SequentialEvent[PhraseEvent], ...]


def _get_common_pitch(event0, event1):
    pitches_per_bar0, pitches_per_bar1 = (
        set(
            map(lambda pitch: pitch.normalize(mutate=False).exponents, pitch_or_pitches)
        )
        for pitch_or_pitches in (event0.pitch_or_pitches, event1.pitch_or_pitches,)
    )
    roots = (
        event0.pitch_or_pitches[0].normalize(mutate=False).exponents,
        event1.pitch_or_pitches[0].normalize(mutate=False).exponents,
    )
    common_pitches = tuple(
        pitches.JustIntonationPitch(pitch)
        for pitch in pitches_per_bar0.intersection(pitches_per_bar1)
        if pitch not in roots
    )
    return sorted(common_pitches)[0]


def _split_part_in_phrases(part: basic.SequentialEvent) -> Phrases:
    phrases = []
    current_phrase = basic.SequentialEvent([])

    if len(part) == 17:
        phrase_size = iter((4, 4, 4, 5))
    else:
        phrase_size = iter((4, 4, 4, 23))
    current_phrase_size = next(phrase_size)

    for nth_event, event in enumerate(part):
        if len(current_phrase) == current_phrase_size:
            phrases.append(current_phrase)
            current_phrase = basic.SequentialEvent([])
            current_phrase_size = next(phrase_size)

        try:
            next_event = part[nth_event + 1]
        except IndexError:
            next_event = None

        if nth_event > 0:
            previous_event = part[nth_event - 1]
        else:
            previous_event = None

        if previous_event:
            connection_pitch0 = _get_common_pitch(event, previous_event)
        else:
            connection_pitch0 = None

        if next_event:
            connection_pitch1 = _get_common_pitch(event, next_event)
        else:
            connection_pitch1 = None

        phrase_event = PhraseEvent(
            event.duration,
            event.pitch_or_pitches,
            event.pitch_or_pitches[0],
            connection_pitch0,
            connection_pitch1,
        )
        current_phrase.append(phrase_event)

    phrases.append(current_phrase)
    return tuple(phrases)


def _split_applied_cantus_firmus_in_parts(
    cantus_firmus: basic.SequentialEvent,
) -> typing.Tuple[basic.SequentialEvent, ...]:
    parts = []
    current_part = basic.SequentialEvent([])
    for event in cantus_firmus:
        if event.pitch_or_pitches:
            current_part.append(event)

        else:
            if current_part:
                parts.append(current_part)
                current_part = basic.SequentialEvent([])

    parts.append(current_part)
    return tuple(parts)


def _calculate_pulse_duration_for_each_event():
    previous_pulse_duration = phrases_constants.PULSE_DURATION_IN_SECONDS_AT_START
    previous_index = 0
    pulses = []
    for nth_event in sorted(
        phrases_constants.EVENT_INDEX_TO_PULSE_TRANSITION_DATA.keys()
    ):
        (
            pulse_duration_range_at_end,
            rising_transition_percentage,
        ) = phrases_constants.EVENT_INDEX_TO_PULSE_TRANSITION_DATA[nth_event]
        n_pulses = nth_event - previous_index
        cptm = pulse_transitions.ContinousPulseTransitionsMaker(
            previous_pulse_duration,
            pulse_duration_range_at_end,
            n_pulses,
            rising_transition_percentage,
        )
        new_pulses = pulse_transitions.find_pulses(cptm)
        pulses.extend(new_pulses)
        previous_pulse_duration = new_pulses[-1]
        previous_index = nth_event

    return tuple(pulses)


def _apply_pulse_duration_on_cantus_firmus(
    cantus_firmus: basic.SequentialEvent,
    pulse_duration_for_each_event: typing.Tuple[float, ...],
) -> basic.SequentialEvent:
    transformed_cantus_firmus = basic.SequentialEvent([])
    pulse_duration_generator = iter(pulse_duration_for_each_event)
    for event in cantus_firmus:
        transformed_cantus_firmus.append(copy.copy(event))
        if event.pitch_or_pitches:
            pulse_duration = next(pulse_duration_generator)
            transformed_cantus_firmus[-1].duration *= pulse_duration * 1 / 2
    return transformed_cantus_firmus


def _export_splitted_parts(splitted_parts=typing.Tuple[Phrases, ...]):
    with open(phrases_constants.SPLITTED_PARTS_PATH, "wb",) as f:
        pickle.dump(splitted_parts, f)


def _make_splitted_parts():
    from ot2.analysis import applied_cantus_firmus

    cantus_firmus = applied_cantus_firmus.APPLIED_CANTUS_FIRMUS
    # pulse_duration_for_each_event = _calculate_pulse_duration_for_each_event()
    # cantus_firmus = _apply_pulse_duration_on_cantus_firmus(
    #     cantus_firmus, pulse_duration_for_each_event
    # )
    parts = _split_applied_cantus_firmus_in_parts(cantus_firmus)
    splitted_parts = tuple(_split_part_in_phrases(part) for part in parts)
    _export_splitted_parts(splitted_parts)


def _import_splitted_parts() -> typing.Tuple[Phrases, ...]:
    with open(phrases_constants.SPLITTED_PARTS_PATH, "rb",) as f:
        splitted_parts = pickle.load(f)
    return splitted_parts


def synthesize_splitted_parts(splitted_parts: typing.Tuple[Phrases, ...]):
    from mutwo.converters.frontends import midi

    melody = basic.SequentialEvent(
        [basic.SequentialEvent(phrase) for phrase in splitted_parts]
    )

    melody = functools.reduce(operator.add, functools.reduce(operator.add, melody))

    def simple_event_to_pitches(simple_event):
        return [simple_event.root - pitches.JustIntonationPitch('2/1')]

    converter = midi.MidiFileConverter(
        "builds/materials/splitted_parts.mid",
        simple_event_to_pitches=simple_event_to_pitches,
        simple_event_to_volume=lambda _: volumes.DecibelVolume(-12),
    )
    converter.convert(
        melody.set_parameter("duration", lambda duration: duration * 2, mutate=False)
    )


# _make_splitted_parts()
SPLITTED_PARTS = _import_splitted_parts()

synthesize_splitted_parts(SPLITTED_PARTS)
