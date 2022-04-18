import abjad
import ranges

import quicktions as fractions

from mutwo import parameters

from ot2 import converters as ot2_converters
from ot2 import constants as ot2_constants
from ot2 import tweaks as tw


def post_process_cengkok_8(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ]
):
    instruments, tape = time_brackets_to_post_process

    start_duration = instruments[0].duration

    n_seconds_delay = 3
    instruments.delay(n_seconds_delay)
    tape.delay(n_seconds_delay)

    time_signature_for_bar_1 = abjad.TimeSignature((6, 4))
    duration_of_rest_in_bar_1 = fractions.Fraction(2, 4)
    time_signature_for_bar_4 = abjad.TimeSignature((7, 4))
    duration_of_rest_in_bar_4 = fractions.Fraction(3, 4)
    # time_signature_for_bar_7 = abjad.TimeSignature((15, 4))
    time_signature_for_bar_7 = abjad.TimeSignature((8, 4))
    duration_of_rest_in_bar_7 = fractions.Fraction(7, 4)

    cut_off_position = sum(
        (
            fractions.Fraction(4, 4),
            fractions.Fraction(4, 4),
            fractions.Fraction(4, 4),
            fractions.Fraction(4, 4),
            fractions.Fraction(4, 4),
            fractions.Fraction(8, 4),
            fractions.Fraction(8, 4),
            # fractions.Fraction(8, 4),
            duration_of_rest_in_bar_1,
            duration_of_rest_in_bar_4,
            duration_of_rest_in_bar_7,
        )
    )

    sine1 = tape[1][0]
    sine1[0].pitch_or_pitches = []
    sine1[1].pitch_or_pitches = []

    sine1[3].pitch_or_pitches = []

    sus_instr0 = instruments[0][0]
    tw.eat(sus_instr0, 3)
    tw.delay(sus_instr0, 4, fractions.Fraction(1, 8))
    tw.prolong(sus_instr0, 15, fractions.Fraction(1, 12))
    sus_instr0[15].duration += duration_of_rest_in_bar_4
    tw.eat(sus_instr0, 15)
    tw.split(sus_instr0, 15, fractions.Fraction(11, 8))
    tw.shorten(sus_instr0, 15, fractions.Fraction(5, 8))
    # tw.delay(sus_instr0, 17, fractions.Fraction(1, 8))
    tw.shorten(sus_instr0, 17, fractions.Fraction(1, 24), False)
    tw.prolong(sus_instr0, 2, fractions.Fraction(1, 12))
    tw.eat(sus_instr0, 23)
    sus_instr0[3].duration += duration_of_rest_in_bar_1
    sus_instr0[30].duration += duration_of_rest_in_bar_7
    tw.eat(sus_instr0, 33, 2)
    tw.eat(sus_instr0, 27, 6)
    tw.shorten(sus_instr0, 22, fractions.Fraction(1, 12))

    sus_instr1 = instruments[1][0]
    # tw.prolong(sus_instr1, 1, fractions.Fraction(1, 6))
    tw.delay(sus_instr1, 3, fractions.Fraction(1, 6))
    tw.eat(sus_instr1, 5)
    # tw.delay(sus_instr1, 6, fractions.Fraction(1, 16))
    tw.shorten(sus_instr1, 5, fractions.Fraction(1, 16), False)
    tw.shorten(sus_instr1, 6, fractions.Fraction(1, 16), False)
    # tw.prolong(sus_instr1, 6, fractions.Fraction(1, 16))
    tw.prolong(sus_instr1, 7, fractions.Fraction(1, 8))
    sus_instr1[12].pitch_or_pitches = sus_instr1[11].pitch_or_pitches
    sus_instr1[13].pitch_or_pitches = []
    sus_instr1[12].duration += duration_of_rest_in_bar_4
    tw.shorten(sus_instr1, 12, fractions.Fraction(1, 2))
    tw.eat(sus_instr1, 13)
    sus_instr1[2].duration += duration_of_rest_in_bar_1
    sus_instr1[3].pitch_or_pitches[0].add(parameters.pitches.JustIntonationPitch("2/1"))
    tw.shorten(sus_instr1, 27, fractions.Fraction(3, 8))
    sus_instr1[28].duration += duration_of_rest_in_bar_7
    tw.eat(sus_instr1, 30, 4)  # works
    tw.eat(sus_instr1, 31, 2)
    # tw.shorten(sus_instr1, 30, fractions.Fraction(8, 8))
    tw.shorten(sus_instr1, 30, fractions.Fraction(6, 8))
    tw.eat(sus_instr1, 29, 2)

    sus_instr2 = instruments[2][0]
    tw.shorten(sus_instr2, 1, fractions.Fraction(1, 8))
    tw.shorten(sus_instr2, 7, fractions.Fraction(1, 16), False)
    sus_instr2[12].pitch_or_pitches = sus_instr1[11].pitch_or_pitches[0]
    sus_instr2[12].playing_indicators.tie.is_active = False
    tw.shorten(sus_instr2, 12, fractions.Fraction(1, 8))
    sus_instr2[12].duration += duration_of_rest_in_bar_4
    tw.eat(sus_instr2, 13)
    tw.shorten(sus_instr2, 12, fractions.Fraction(1, 2))
    tw.eat(sus_instr2, 13, 2)
    tw.shorten(sus_instr2, 17, fractions.Fraction(13, 12))
    # tw.delay(sus_instr2, 19, fractions.Fraction(5, 24))
    tw.shorten(sus_instr2, 21, fractions.Fraction(1, 4))
    # tw.split(sus_instr2, 22, fractions.Fraction(3, 4))
    sus_instr2[0].duration += duration_of_rest_in_bar_1
    sus_instr2[22].duration += duration_of_rest_in_bar_7
    sus_instr2[26].playing_indicators.tie.is_active = False
    tw.shorten(sus_instr2, 26, fractions.Fraction(8, 8))
    tw.eat(sus_instr2, 27, 2)
    # tw.shorten(sus_instr2, 25, fractions.Fraction(3, 8), False)
    # tw.shorten(sus_instr2, 25, fractions.Fraction(1, 16))
    # tw.eat(sus_instr2, 26)
    tw.eat(sus_instr2, 25)
    tw.eat(sus_instr2, 22, 4)

    keyboard = instruments[3]

    keyboard.set_parameter(
        "pitch_or_pitches",
        lambda pitch_or_pitches: [
            pitch - parameters.pitches.JustIntonationPitch("2/1")
            for pitch in pitch_or_pitches
        ]
        if pitch_or_pitches
        else pitch_or_pitches,
        False,
    )
    keyboard[0].mutate_parameter(
        "notation_indicators",
        lambda notation_indicators: setattr(notation_indicators.ottava, "n_octaves", 0),
    )

    tw.shorten(keyboard[0], 2, fractions.Fraction(1, 16), False)
    keyboard[0][4].pitch_or_pitches = []
    # tw.split(keyboard[0], 9, fractions.Fraction(1, 6), fractions.Fraction(1, 6))
    # tw.shorten(keyboard[0], 11, fractions.Fraction(1, 12))
    tw.shorten(keyboard[0], 9, fractions.Fraction(1, 12))
    tw.eat(keyboard[0], 10, 3)
    keyboard[0][9].duration += duration_of_rest_in_bar_4
    tw.shorten(keyboard[0], 10, fractions.Fraction(1, 24), False)
    tw.eat(keyboard[0], 9)
    keyboard[0][1].duration += duration_of_rest_in_bar_1
    keyboard[0][32].duration += duration_of_rest_in_bar_7
    tw.eat(keyboard[0], 33, 4)
    tw.shorten(keyboard[0], 33, fractions.Fraction(3, 2))
    keyboard[0][33].pitch_or_pitches = []
    tw.shorten(keyboard[0], 7, fractions.Fraction(3, 8), False)
    tw.split(keyboard[0], 8, fractions.Fraction(1, 4))
    tw.shorten(keyboard[0], 10, fractions.Fraction(3, 8))

    keyboard[1][2].pitch_or_pitches.extend(keyboard[1][3].pitch_or_pitches)
    tw.eat(keyboard[1], 2)
    tw.prolong(keyboard[1], 3, fractions.Fraction(1, 8))
    tw.eat(keyboard[1], 5)
    keyboard[1][12].duration += keyboard[1][11].duration
    del keyboard[1][11]
    tw.eat(keyboard[1], 11, 2)
    keyboard[1][11].duration += duration_of_rest_in_bar_4
    keyboard[1][10].pitch_or_pitches[0].add(
        parameters.pitches.JustIntonationPitch("2/1")
    )
    for nth in (19, 18, 17, 16):
        tw.split(keyboard[1], nth, fractions.Fraction(1, 4))
    keyboard[1][2].duration += duration_of_rest_in_bar_1
    keyboard[1][25].duration += duration_of_rest_in_bar_7
    tw.eat(keyboard[1], 26)
    tw.shorten(keyboard[1], 26, fractions.Fraction(1, 4), False)
    tw.eat(keyboard[1], 27, 6)
    tw.shorten(keyboard[1], 27, fractions.Fraction(3, 2))
    keyboard[1][27].pitch_or_pitches = []
    tw.eat(keyboard[1], 26, 1)
    tw.split(keyboard[1], 10, fractions.Fraction(1, 4))
    keyboard[1][12].pitch_or_pitches = keyboard[0][10].pitch_or_pitches[
        0
    ] - parameters.pitches.JustIntonationPitch("2/1")
    tw.eat(keyboard[1], 25, 1)
    tw.shorten(keyboard[1], 12, fractions.Fraction(1, 2))

    sus_instr0.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr1.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr2.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    keyboard.set_parameter("volume", parameters.volumes.WesternVolume("p"))

    for tagged_simultaneous_event in tape:
        for sequential_event in tagged_simultaneous_event:
            sequential_event.get_event_at(
                fractions.Fraction(32, 4)
            ).duration += duration_of_rest_in_bar_7
            sequential_event.get_event_at(
                fractions.Fraction(16, 4)
            ).duration += duration_of_rest_in_bar_4
            sequential_event.get_event_at(
                fractions.Fraction(5, 4)
            ).duration += duration_of_rest_in_bar_1
            sequential_event.cut_out(0, cut_off_position)

        if tagged_simultaneous_event.tag == ot2_constants.instruments.ID_GONG:
            gong = tagged_simultaneous_event[0]
            gong[-1].pitch_or_pitches = []
            tw.split(gong, 1, fractions.Fraction(3, 4))
            gong[2].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("1/5")]
            gong[2].volume = "p"
            tw.split(gong, len(gong) - 1, fractions.Fraction(6, 4))
            gong[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("7/16")
            tw.shorten(gong, len(gong) - 1, fractions.Fraction(3, 8))

    time_signatures = list(instruments.time_signatures)
    time_signatures[1] = time_signature_for_bar_1
    time_signatures[4] = time_signature_for_bar_4
    time_signatures[7] = time_signature_for_bar_7
    time_signatures = time_signatures[:8]
    time_signatures.append(abjad.TimeSignature((7, 4)))

    instruments.time_signatures = tuple(time_signatures)
    tape.time_signatures = tuple(time_signatures)

    sus_instr0.cut_out(0, cut_off_position)
    sus_instr1.cut_out(0, cut_off_position)
    sus_instr2.cut_out(0, cut_off_position)
    keyboard[0].cut_out(0, cut_off_position)
    keyboard[1].cut_out(0, cut_off_position)

    end_duration = sus_instr0.duration
    time_span_in_seconds = instruments.duration
    duration_difference_factor = end_duration / start_duration
    new_time_span_in_seconds = time_span_in_seconds * duration_difference_factor
    new_end_value = instruments.start_or_start_range + new_time_span_in_seconds

    instruments.end_or_end_range = new_end_value
    tape.end_or_end_range = new_end_value

    instruments.cue_ranges = (
        ranges.Range(0, fractions.Fraction(7, 4) + 4),
        ranges.Range(fractions.Fraction(7, 4) + 4, cut_off_position),
    )

    tw.add_cent_deviation_to_sequential_event(sus_instr0)
    tw.add_cent_deviation_to_sequential_event(sus_instr1)
    tw.add_cent_deviation_to_sequential_event(sus_instr2)

    tw.update_sine_tone_events_of_tape_time_bracket(instruments, tape)

    return time_brackets_to_post_process
