import abjad
import quicktions as fractions

from mutwo import converters

from mutwo import parameters

from ot2 import converters as ot2_converters
from ot2 import constants as ot2_constants
from ot2 import tweaks as tw


def post_process_cengkok_1(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ]
):
    instruments, tape = time_brackets_to_post_process
    start_duration = instruments[0].duration

    sus_instr0 = instruments[0][0]
    sus_instr2 = instruments[1][0]
    keyboard = instruments[2]
    right_hand, left_hand = keyboard

    duration_of_rest_in_bar_4 = fractions.Fraction(8, 4)
    time_signature_for_bar_4 = abjad.TimeSignature((16, 4))

    sus_instr0[2].pitch_or_pitches[0].add(parameters.pitches.JustIntonationPitch("2/1"))
    sus_instr0[3].pitch_or_pitches[0].add(parameters.pitches.JustIntonationPitch("2/1"))
    sus_instr0[4].pitch_or_pitches[0] = (
        right_hand[2]
        .pitch_or_pitches[0]
        .add(parameters.pitches.JustIntonationPitch("2/1"), mutate=False)
    )
    sus_instr0[6].pitch_or_pitches[0].add(parameters.pitches.JustIntonationPitch("2/1"))
    # sus_instr0[5].pitch_or_pitches[0] = sus_instr2[3].pitch_or_pitches[0]
    sus_instr0[5].pitch_or_pitches[0] = sus_instr0[6].pitch_or_pitches[0]
    sus_instr0[11].pitch_or_pitches[0] = (
        right_hand[5]
        .pitch_or_pitches[0]
        .add(parameters.pitches.JustIntonationPitch("2/1"), mutate=False)
    )

    tw.eat(sus_instr0, 5)
    tw.eat(sus_instr0, 10)
    sus_instr0[10].pitch_or_pitches[0].add(
        parameters.pitches.JustIntonationPitch("1/2")
    )
    tw.split(sus_instr0, len(sus_instr0) - 1, fractions.Fraction(10, 4))
    sus_instr0[-1].pitch_or_pitches = (
        sus_instr0[-3]
        .pitch_or_pitches[0]
        .add(parameters.pitches.JustIntonationPitch("1/1"), mutate=False)
    )
    sus_instr0[-2].pitch_or_pitches = (
        sus_instr2[-2]
        .pitch_or_pitches[0]
        .add(parameters.pitches.JustIntonationPitch("1/1"), mutate=False)
    )

    sus_instr0[6:8], sus_instr2[4:5] = sus_instr2[4:5], sus_instr0[6:8]

    sus_instr0[7:].set_parameter(
        "pitch_or_pitches",
        lambda pitch_or_pitches: pitch_or_pitches[0]
        + parameters.pitches.JustIntonationPitch("2/1"),
    )
    tw.safe_delay(sus_instr0, 1, fractions.Fraction(1, 4))

    tw.safe_delay(sus_instr0, 5, fractions.Fraction(3, 4))
    tw.safe_delay(sus_instr2, 3, fractions.Fraction(3, 4))

    tw.shorten(sus_instr0, 4, fractions.Fraction(1, 2))
    tw.shorten(sus_instr2, 2, fractions.Fraction(1, 2))

    tw.shorten(sus_instr0, 7, fractions.Fraction(1, 2), False)
    tw.shorten(sus_instr2, 6, fractions.Fraction(1, 2), False)

    tw.split(sus_instr0, 8, fractions.Fraction(1, 2), fractions.Fraction(1, 2))
    sus_instr0[9].pitch_or_pitches = []

    tw.split(sus_instr2, 7, fractions.Fraction(1, 2), fractions.Fraction(1, 2))
    sus_instr2[8].pitch_or_pitches = []

    tw.split(sus_instr0, 6, fractions.Fraction(3, 4))
    sus_instr0[7].pitch_or_pitches = right_hand[3].pitch_or_pitches[
        0
    ] + parameters.pitches.JustIntonationPitch("2/1")

    tw.shorten(sus_instr2, 5, fractions.Fraction(1, 4))
    tw.shorten(sus_instr2, 12, fractions.Fraction(3, 2))
    tw.shorten(sus_instr0, 14, fractions.Fraction(3, 2))
    tw.delay(sus_instr0, 16, fractions.Fraction(1, 4))
    tw.split(sus_instr0, 13, fractions.Fraction(1, 2), fractions.Fraction(1, 4))
    sus_instr0[14].pitch_or_pitches = []

    tw.split(right_hand, 2, fractions.Fraction(3, 2))
    tw.split(left_hand, 2, fractions.Fraction(3, 2))

    right_hand[3].pitch_or_pitches = []
    left_hand[3].pitch_or_pitches = []

    tw.split(right_hand, 4, fractions.Fraction(3, 2))
    right_hand[5].pitch_or_pitches = sus_instr0[8].pitch_or_pitches[
        0
    ] - parameters.pitches.JustIntonationPitch("2/1")

    left_hand[5].pitch_or_pitches = sus_instr2[7].pitch_or_pitches[
        0
    ] - parameters.pitches.JustIntonationPitch("4/1")
    right_hand[7].pitch_or_pitches = sus_instr0[12].pitch_or_pitches[
        0
    ] - parameters.pitches.JustIntonationPitch("2/1")
    right_hand[8].pitch_or_pitches = sus_instr2[11].pitch_or_pitches[
        0
    ] - parameters.pitches.JustIntonationPitch("1/1")
    right_hand[9].pitch_or_pitches = right_hand[9].pitch_or_pitches[
        0
    ] + parameters.pitches.JustIntonationPitch("2/1")
    left_hand[8].pitch_or_pitches.append(parameters.pitches.JustIntonationPitch("2/11"))

    # sus_instr0[-1].pitch_or_pitches[0] -= parameters.pitches.JustIntonationPitch("2/1")
    sus_instr0[-1].pitch_or_pitches[0] = parameters.pitches.JustIntonationPitch("1/2")

    # tw.split(left_hand, 8, fractions.Fraction(3, 1))

    tw.eat(sus_instr0, 17)
    tw.eat(sus_instr2, 13)

    sus_instr0[10].duration += duration_of_rest_in_bar_4
    sus_instr2[9].duration += duration_of_rest_in_bar_4
    right_hand[6].duration += duration_of_rest_in_bar_4
    left_hand[5].duration += duration_of_rest_in_bar_4

    keyboard_volume = parameters.volumes.WesternVolume("pp")
    right_hand.set_parameter("volume", keyboard_volume)
    left_hand.set_parameter("volume", keyboard_volume)

    sus_instr_volume = parameters.volumes.WesternVolume("pp")
    sus_instr0.set_parameter("volume", sus_instr_volume)
    sus_instr2.set_parameter("volume", sus_instr_volume)

    tw.add_cent_deviation_to_sequential_event(sus_instr0)
    tw.add_cent_deviation_to_sequential_event(sus_instr2)

    time_signatures = list(instruments.time_signatures)
    time_signatures[4] = time_signature_for_bar_4

    end_duration = sus_instr0.duration
    time_span_in_seconds = instruments.duration
    duration_difference_factor = end_duration / start_duration
    new_time_span_in_seconds = time_span_in_seconds * duration_difference_factor
    new_end_value = instruments.start_or_start_range + new_time_span_in_seconds

    tape.time_signatures = tuple(time_signatures)
    tape.end_or_end_range = new_end_value

    instruments.time_signatures = tuple(time_signatures)
    instruments.end_or_end_range = new_end_value

    return time_brackets_to_post_process
