import itertools

from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants


def is_rest(event: events.basic.SimpleEvent):
    if hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches:
        return False
    return True


def eat(sequential_event: events.basic.SequentialEvent, nth: int, n: int = 1):
    duration = sequential_event[nth : nth + n + 1].duration
    sequential_event[nth].duration = duration
    for index in reversed(tuple(range(nth + 1, nth + n + 1))):
        del sequential_event[index]


def prolong(
    sequential_event: events.basic.SequentialEvent,
    nth: int,
    duration: parameters.abc.DurationType,
):
    next_event_index = nth + 1
    sequential_event[next_event_index].duration -= duration
    sequential_event[nth].duration += duration


def delay(
    sequential_event: events.basic.SequentialEvent,
    nth: int,
    duration: parameters.abc.DurationType,
):
    previous_event_index = nth - 1
    if previous_event_index >= 0 and is_rest(sequential_event[previous_event_index]):
        sequential_event[previous_event_index].duration += duration
    else:
        sequential_event.insert(nth, events.music.NoteLike([], duration))
    sequential_event[nth].duration -= duration


def safe_delay(
    sequential_event: events.basic.SequentialEvent,
    nth: int,
    duration: parameters.abc.DurationType,
):
    if is_rest(sequential_event[nth]):
        return
    previous_event_index = nth - 1
    if previous_event_index >= 0 and is_rest(sequential_event[previous_event_index]):
        sequential_event[previous_event_index].duration += duration
    else:
        sequential_event.insert(nth, events.music.NoteLike([], duration))
        nth += 1
    sequential_event[nth].duration -= duration


def shorten(
    sequential_event: events.basic.SequentialEvent,
    nth: int,
    duration: parameters.abc.DurationType,
    add_rest: bool = True,
):
    sequential_event[nth].duration -= duration
    next_index = nth + 1
    try:
        next_event = sequential_event[next_index]
    except IndexError:
        next_event = None
    if next_event and (is_rest(next_event) or not add_rest):
        sequential_event[next_index].duration += duration
    else:
        sequential_event.insert(nth + 1, events.music.NoteLike([], duration))


def split(
    sequential_event: events.basic.SequentialEvent,
    nth_child: int,
    *durations: parameters.abc.DurationType
):
    child = sequential_event[nth_child]
    difference = child.duration - sum(durations)
    assert difference >= 0
    absolute_time = sequential_event.absolute_times[nth_child]
    for duration in durations:
        absolute_time += duration
        sequential_event.split_child_at(absolute_time)


def add_cent_deviation_to_sequential_event(
    sequential_event_to_process: events.basic.SequentialEvent[events.music.NoteLike],
):
    previous_event_pitch = None
    for event in sequential_event_to_process:
        if hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches:
            pitch_to_process = event.pitch_or_pitches[0]
            if pitch_to_process != previous_event_pitch:
                deviation = (
                    pitch_to_process.cent_deviation_from_closest_western_pitch_class
                )
                event.notation_indicators.cent_deviation.deviation = deviation
            previous_event_pitch = pitch_to_process
        else:
            if hasattr(event, "notation_indicators"):
                event.notation_indicators.cent_deviation.deviation = None
            previous_event_pitch = None


def add_cent_deviation_to_simultaneous_event(simultaneous_event_to_process):
    for sequential_event in simultaneous_event_to_process:
        add_cent_deviation_to_sequential_event(sequential_event)


def make_sine_tones_tagged_simultaneous_event_from_sus_instr_simultaneous_event(
    sus_instr_simultaneous_event: events.basic.TaggedSimultaneousEvent, id_sine: str
) -> events.basic.TaggedSimultaneousEvent:
    attack_cycle = itertools.cycle((0.1, 0.08, 0.05, 0.2, 0.3, 0.01))
    release_cycle = itertools.cycle((0.07, 0.1, 0.25, 0.2, 0.31))
    sine_tones_tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
        [], tag=id_sine
    )
    sequential_event = sus_instr_simultaneous_event[0].destructive_copy()
    sequential_event.tie_by(
        lambda event0, event1: event0.get_parameter("pitch_or_pitches")
        == event1.get_parameter("pitch_or_pitches")
    )
    sequential_event.set_parameter(
        "volume",
        lambda volume: parameters.volumes.DecibelVolume(volume.decibel + 8),
    )
    sequential_event.set_parameter("attack", lambda _: next(attack_cycle))
    sequential_event.set_parameter("release", lambda _: next(release_cycle))
    sine_tones_tagged_simultaneous_event.append(sequential_event)
    return sine_tones_tagged_simultaneous_event


def make_sine_tones_copy_from_instrumental_time_bracket(
    instrumental_time_bracket: events.time_brackets.TimeBracket,
) -> events.time_brackets.TimeBracket:
    sine_tones_time_bracket = instrumental_time_bracket.empty_copy()
    for tagged_simultaneous_event in instrumental_time_bracket:
        try:
            id_sine = ot2_constants.instruments.ID_SUS_TO_ID_SINE[
                tagged_simultaneous_event.tag
            ]
        except KeyError:
            pass
        else:
            sine_tones_tagged_simultaneous_event = make_sine_tones_tagged_simultaneous_event_from_sus_instr_simultaneous_event(
                tagged_simultaneous_event, id_sine
            )
            sine_tones_time_bracket.append(sine_tones_tagged_simultaneous_event)

    return sine_tones_time_bracket


def update_sine_tone_events_of_tape_time_bracket(
    instrumental_time_bracket: events.time_brackets.TimeBracket,
    tape_time_bracket: events.time_brackets.TimeBracket,
):
    sine_tones_time_bracket = make_sine_tones_copy_from_instrumental_time_bracket(
        instrumental_time_bracket
    )
    sine_tones_time_bracket_keys = tuple(
        map(
            lambda tagged_simultaneous_event: tagged_simultaneous_event.tag,
            sine_tones_time_bracket,
        )
    )
    for tagged_simultaneous_event in tape_time_bracket:
        if tagged_simultaneous_event.tag in sine_tones_time_bracket_keys:
            tagged_simultaneous_event[0] = sine_tones_time_bracket[
                sine_tones_time_bracket_keys.index(tagged_simultaneous_event.tag)
            ][0]
