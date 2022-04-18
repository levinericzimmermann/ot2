import copy

import abjad
import ranges

import quicktions as fractions

from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters
from ot2 import tweaks as tw


def post_process_cengkok_11(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ]
):
    instruments, tape = time_brackets_to_post_process

    start_duration = instruments[0].duration

    sus_instr0 = instruments[0][0]
    sus_instr1 = instruments[1][0]
    sus_instr2 = instruments[2][0]
    keyboard = instruments[3]
    right_hand, left_hand = keyboard

    time_signature_for_bar_4 = abjad.TimeSignature((7, 4))
    duration_of_rest_in_bar_4 = fractions.Fraction(3, 4)

    time_signature_for_bar_16 = abjad.TimeSignature((10, 4))
    duration_of_rest_in_bar_16 = fractions.Fraction(2, 4)

    tw.shorten(sus_instr0, 4, fractions.Fraction(1, 12))
    tw.eat(sus_instr0, 6)
    sus_instr0[6].playing_indicators.tie.is_active = False
    tw.delay(sus_instr0, 6, fractions.Fraction(1, 6))
    tw.shorten(sus_instr0, 7, fractions.Fraction(1, 8))
    tw.shorten(sus_instr0, 10, fractions.Fraction(1, 8))
    sus_instr0[10].playing_indicators.tie.is_active = False
    tw.eat(sus_instr0, 11)
    tw.prolong(sus_instr0, 11, fractions.Fraction(1, 16))
    sus_instr0[11].duration += duration_of_rest_in_bar_4
    tw.shorten(sus_instr0, 13, fractions.Fraction(5, 24))
    tw.eat(sus_instr0, 14, 2)
    tw.eat(sus_instr0, 16, 2)
    tw.prolong(sus_instr0, 15, fractions.Fraction(1, 6))
    tw.eat(sus_instr0, 28, 4)
    tw.shorten(sus_instr0, 28, fractions.Fraction(1, 6), False)
    tw.eat(sus_instr0, 42)
    sus_instr0[42].playing_indicators.tie.is_active = False
    tw.shorten(
        sus_instr0, 42, fractions.Fraction(1, 12) + fractions.Fraction(1, 4), False
    )
    tw.shorten(sus_instr0, 43, fractions.Fraction(1, 6), False)
    tw.prolong(sus_instr0, len(sus_instr0) - 2, fractions.Fraction(1, 4))
    sus_instr0[-1].duration += duration_of_rest_in_bar_16
    tw.split(
        sus_instr0,
        len(sus_instr0) - 7,
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 2),
    )
    sus_instr0[-8].pitch_or_pitches = []

    tw.eat(sus_instr1, 5, 2)
    tw.shorten(sus_instr1, 5, fractions.Fraction(1, 16), False)
    tw.prolong(sus_instr1, 7, fractions.Fraction(1, 16))
    tw.prolong(sus_instr1, 1, fractions.Fraction(1, 6))
    # tw.prolong(sus_instr1, 2, fractions.Fraction(1, 12))
    # tw.shorten(sus_instr1, 4, fractions.Fraction(1, 12))
    sus_instr1[11].pitch_or_pitches = sus_instr1[10].pitch_or_pitches
    tw.eat(sus_instr1, 11)
    tw.shorten(sus_instr1, 11, fractions.Fraction(2, 4))
    sus_instr1[12].duration += duration_of_rest_in_bar_4
    sus_instr1[17].pitch_or_pitches = []
    tw.eat(sus_instr1, 17)
    tw.eat(sus_instr1, 27)
    # tw.eat(sus_instr1, 35, 3)
    tw.eat(sus_instr1, 35, 9)
    tw.prolong(sus_instr1, 34, fractions.Fraction(1, 4))
    tw.eat(sus_instr1, 37)
    tw.eat(sus_instr1, 38)
    tw.eat(sus_instr1, 39)
    sus_instr1[40].pitch_or_pitches[0].add(
        parameters.pitches.JustIntonationPitch("2/1")
    )
    sus_instr1[41].pitch_or_pitches[0].add(
        parameters.pitches.JustIntonationPitch("2/1")
    )
    tw.eat(sus_instr1, 42)
    for n in (43, 44, 46, 47, 48, 49):
        sus_instr1[n].pitch_or_pitches[0] = (
            sus_instr1[n]
            .pitch_or_pitches[0]
            .add(parameters.pitches.JustIntonationPitch("2/1"), mutate=False)
        )
    tw.prolong(sus_instr1, 44, fractions.Fraction(1, 4))
    tw.prolong(sus_instr1, 48, fractions.Fraction(1, 12))
    sus_instr1[46].pitch_or_pitches = sus_instr1[47].pitch_or_pitches
    tw.split(sus_instr1, 39, fractions.Fraction(1, 4))
    sus_instr1[39].playing_indicators.tie.is_active = True
    sus_instr1[-1].duration += duration_of_rest_in_bar_16
    tw.shorten(sus_instr1, len(sus_instr1) - 2, fractions.Fraction(1, 4))
    # tw.delay(sus_instr1, len(sus_instr1) - 2, fractions.Fraction(1, 8))
    # tw.eat(sus_instr1, len(sus_instr1) - 9, 6)
    # tw.eat(sus_instr1, len(sus_instr1) - 7, 6)
    tw.eat(sus_instr1, len(sus_instr1) - 6, 5)

    # tw.delay(sus_instr2, 5, fractions.Fraction(1, 8))
    tw.eat(sus_instr2, 4)
    tw.shorten(sus_instr2, 7, fractions.Fraction(3, 8))
    tw.shorten(sus_instr2, 13, fractions.Fraction(1, 12))
    sus_instr2[13].playing_indicators.tie.is_active = False
    tw.eat(sus_instr2, 14)
    tw.delay(sus_instr2, 15, fractions.Fraction(5, 24))
    sus_instr2[14].duration += duration_of_rest_in_bar_4
    tw.shorten(sus_instr2, 16, fractions.Fraction(1, 12))
    tw.shorten(sus_instr2, 18, fractions.Fraction(1, 24), False)
    tw.shorten(sus_instr2, 20, fractions.Fraction(1, 2))
    tw.delay(sus_instr2, 22, fractions.Fraction(1, 8))
    tw.shorten(sus_instr2, 24, fractions.Fraction(1, 4))
    tw.shorten(sus_instr2, 29, fractions.Fraction(5, 12))
    # tw.eat(sus_instr2, 30)
    tw.eat(sus_instr2, 30, 8)
    sus_instr2[34] = copy.deepcopy(sus_instr2[34])
    sus_instr2[34].playing_indicators.articulation.name = "."
    tw.split(
        sus_instr2,
        26,
        fractions.Fraction(1, 3) + fractions.Fraction(1, 4),
        fractions.Fraction(2, 3),
        fractions.Fraction(1, 3),
    )
    sus_instr2[27].pitch_or_pitches = []
    tw.split(sus_instr2, 26, fractions.Fraction(1, 4))
    sus_instr2[26].playing_indicators.tie.is_active = True
    tw.eat(sus_instr2, 43, 3)
    sus_instr2[-2] = copy.deepcopy(sus_instr2[-2])
    sus_instr2[-2].pitch_or_pitches[0] -= parameters.pitches.JustIntonationPitch("2/1")
    tw.prolong(sus_instr2, len(sus_instr2) - 2, fractions.Fraction(1, 4))
    sus_instr2[-1].duration += duration_of_rest_in_bar_16
    tw.split(sus_instr2, len(sus_instr2) - 7, fractions.Fraction(2, 3))
    sus_instr2[-7].pitch_or_pitches = []
    sus_instr2[-6:-3].set_parameter(
        "pitch_or_pitches",
        lambda pitch_or_pitches: [
            pitch - parameters.pitches.JustIntonationPitch("2/1")
            for pitch in pitch_or_pitches
        ]
        if pitch_or_pitches
        else pitch_or_pitches,
        False,
    )

    tw.eat(right_hand, 12, 4)
    tw.split(right_hand, 12, *([fractions.Fraction(1, 4)] * 4))
    tw.eat(right_hand, 8)
    right_hand[13].duration += duration_of_rest_in_bar_4
    lower_octave_range = (14, 34)
    right_hand[lower_octave_range[0] : lower_octave_range[1]].set_parameter(
        "pitch_or_pitches",
        lambda pitch_or_pitches: [
            pitch - parameters.pitches.JustIntonationPitch("2/1")
            for pitch in pitch_or_pitches
        ]
        if pitch_or_pitches
        else pitch_or_pitches,
        False,
    )
    right_hand[lower_octave_range[0] : lower_octave_range[1]].mutate_parameter(
        "notation_indicators",
        lambda notation_indicators: setattr(notation_indicators.ottava, "n_octaves", 0),
    )

    right_hand[16].duration = fractions.Fraction(1, 12)
    right_hand[18].duration = fractions.Fraction(1, 2)
    right_hand[59] = copy.deepcopy(right_hand[58])
    right_hand[59].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("32/15")]
    tw.eat(right_hand, 66, 14)
    tw.shorten(right_hand, 48, fractions.Fraction(1, 12))
    tw.prolong(right_hand, 49, fractions.Fraction(1, 6))
    tw.eat(right_hand, 54)
    tw.split(right_hand, 54, fractions.Fraction(1, 4))
    right_hand[-1].duration += duration_of_rest_in_bar_16
    tw.shorten(right_hand, 13, fractions.Fraction(1, 4))

    left_hand.set_parameter(
        "pitch_or_pitches",
        lambda pitch_or_pitches: [
            pitch - parameters.pitches.JustIntonationPitch("2/1")
            for pitch in pitch_or_pitches
        ]
        if pitch_or_pitches
        else pitch_or_pitches,
        False,
    )
    # set to minor third of c
    left_hand[8].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("7/20")]
    tw.shorten(left_hand, 6, fractions.Fraction(1, 12), False)
    tw.eat(left_hand, 13, 2)
    tw.split(
        left_hand,
        13,
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 8),
    )
    tw.eat(left_hand, 10)
    tw.prolong(left_hand, 15, fractions.Fraction(1, 24))
    tw.split(left_hand, 15, fractions.Fraction(1, 12))
    left_hand[16].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("2/5")]
    tw.eat(left_hand, 14)
    # left_hand[15:24].set_parameter(
    #     "pitch_or_pitches",
    #     lambda pitch_or_pitches: [
    #         pitch - parameters.pitches.JustIntonationPitch("2/1")
    #         for pitch in pitch_or_pitches
    #     ]
    #     if pitch_or_pitches
    #     else pitch_or_pitches,
    #     False,
    # )
    tw.split(left_hand, 11, fractions.Fraction(3, 16))
    # left_hand[11].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("4/11")]
    left_hand[11].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("16/33")]
    tw.split(left_hand, 10, fractions.Fraction(5, 8))
    left_hand[11].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("4/11")]
    left_hand[16].duration += duration_of_rest_in_bar_4
    tw.shorten(left_hand, 21, fractions.Fraction(1, 8), False)
    left_hand[49] = events.music.NoteLike(
        # left_hand[48].pitch_or_pitches, left_hand[49].duration, left_hand[48].volume
        [parameters.pitches.JustIntonationPitch("2/11")],
        left_hand[49].duration,
        left_hand[48].volume,
    )
    tw.eat(left_hand, 59, 5)
    left_hand[59].pitch_or_pitches = [
        # parameters.pitches.JustIntonationPitch("7/25"),
        # parameters.pitches.JustIntonationPitch("7/40"),
        parameters.pitches.JustIntonationPitch("14/25"),
        parameters.pitches.JustIntonationPitch("14/40"),
    ]
    left_hand[59].duration += duration_of_rest_in_bar_16
    tw.split(
        left_hand,
        59,
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
    )
    tw.eat(left_hand, 41)
    left_hand[41].duration, left_hand[42].duration = (
        left_hand[42].duration,
        left_hand[41].duration,
    )
    tw.eat(left_hand, 63)
    tw.shorten(left_hand, 16, fractions.Fraction(1, 3))

    # for n in (39, 40, 41):
    #     left_hand[n].duration = fractions.Fraction(1, 6)

    keyboard.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr0.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr1.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr2.set_parameter("volume", parameters.volumes.WesternVolume("p"))

    for tagged_simultaneous_event in tape:
        for sequential_event in tagged_simultaneous_event:
            sequential_event.get_event_at(
                fractions.Fraction(80, 4)
            ).duration += duration_of_rest_in_bar_16

            sequential_event.get_event_at(
                fractions.Fraction(16, 4)
            ).duration += duration_of_rest_in_bar_4

        if tagged_simultaneous_event.tag == ot2_constants.instruments.ID_GONG:
            gong = tagged_simultaneous_event[0]
            tw.split(gong, 16, fractions.Fraction(5, 4))
            gong[-1].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("7/10")]
            tw.delay(gong, len(gong) - 1, fractions.Fraction(1, 2))

    time_signatures = list(instruments.time_signatures)
    time_signatures[4] = time_signature_for_bar_4
    time_signatures[16] = time_signature_for_bar_16

    # REMOVING LAST BAR! crazy stuff happening here
    del time_signatures[16]
    too_long = fractions.Fraction(10, 4)
    for time_bracket in time_brackets_to_post_process:
        for tagged_simultaneous_event in time_bracket:
            for sequential_event in tagged_simultaneous_event:
                duration = sequential_event.duration
                sequential_event.cut_off(duration - too_long, duration)

    tw.eat(sus_instr0, len(sus_instr0) - 2, 1)
    tw.eat(sus_instr0, len(sus_instr0) - 3, 1)
    tw.safe_delay(sus_instr0, len(sus_instr0) - 1, fractions.Fraction(1, 2))
    # sus_instr0[-2].pitch_or_pitches = sus_instr0[-3].pitch_or_pitches
    # tw.eat(sus_instr0, len(sus_instr0) - 4, 1)
    # tw.safe_delay(sus_instr0, len(sus_instr0) - 2, fractions.Fraction(1, 4))
    tw.prolong(sus_instr0, len(sus_instr0) - 3, fractions.Fraction(1, 8))
    tw.prolong(sus_instr2, len(sus_instr2) - 4, fractions.Fraction(1, 4))

    tw.eat(sus_instr2, len(sus_instr2) - 2)
    tw.shorten(sus_instr2, len(sus_instr2) - 3, fractions.Fraction(5, 12))

    end_duration = sus_instr0.duration
    time_span_in_seconds = instruments.duration
    duration_difference_factor = end_duration / start_duration
    new_time_span_in_seconds = time_span_in_seconds * duration_difference_factor
    new_end_value = instruments.start_or_start_range + new_time_span_in_seconds

    tape.time_signatures = tuple(time_signatures)
    tape.end_or_end_range = new_end_value

    instruments.time_signatures = tuple(time_signatures)
    instruments.end_or_end_range = new_end_value

    instruments.cue_ranges = (
        ranges.Range(0, fractions.Fraction(5, 4) + 4),
        ranges.Range(fractions.Fraction(5, 4) + 4, fractions.Fraction(7, 4) + 8),
        ranges.Range(fractions.Fraction(7, 4) + 8, fractions.Fraction(7, 4) + 8 + 11),
        ranges.Range(
            fractions.Fraction(7, 4) + 8 + 11,
            fractions.Fraction(7, 4) + 8 + 11 + fractions.Fraction(22, 4),
        ),
        ranges.Range(
            fractions.Fraction(7, 4) + 8 + 11 + fractions.Fraction(22, 4),
            fractions.Fraction(9, 4)
            + 8
            + 11
            + sum(fractions.Fraction(n, 4) for n in (4, 5, 6, 4, 7, 4, 4, 8, 8)),
        ),
        ranges.Range(
            fractions.Fraction(9, 4)
            + 8
            + 11
            + sum(fractions.Fraction(n, 4) for n in (4, 5, 6, 4, 7, 4, 4, 8, 8)),
            fractions.Fraction(11, 4)
            + 8
            + 11
            + sum(fractions.Fraction(n, 4) for n in (4, 5, 6, 4, 7, 4, 4, 8, 8, 8)),
        ),
        ranges.Range(
            fractions.Fraction(11, 4)
            + 8
            + 11
            + sum(fractions.Fraction(n, 4) for n in (4, 5, 6, 4, 7, 4, 4, 8, 8, 8)),
            fractions.Fraction(11, 4)
            + 8
            + 11
            + sum(
                fractions.Fraction(n, 4)
                # for n in (4, 5, 6, 4, 7, 4, 4, 8, 8, 8, 7, 5, 5, 3, 3, 3, 6)
                for n in (4, 5, 6, 4, 7, 4, 4, 8, 8, 8, 7, 5, 5, 3, 3, 3, 6, 8)
            ),
        ),
    )

    instruments.distribution_strategies = (
        None,
        None,
        None,
        None,
        ot2_converters.symmetrical.keyboard.HandBasedPitchDistributionStrategy(
            available_keys=tuple(
                sorted(
                    ot2_converters.symmetrical.keyboard_constants.DIATONIC_PITCHES
                    + ot2_converters.symmetrical.keyboard_constants.CHROMATIC_PITCHES
                )
            )
        ),
        None,
        None,
    )

    tw.add_cent_deviation_to_sequential_event(sus_instr0)
    tw.add_cent_deviation_to_sequential_event(sus_instr1)
    tw.add_cent_deviation_to_sequential_event(sus_instr2)

    tw.update_sine_tone_events_of_tape_time_bracket(instruments, tape)

    return time_brackets_to_post_process
