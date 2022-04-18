import copy

import abjad
import quicktions as fractions

from mutwo import converters
from mutwo import events

from mutwo import parameters

from ot2 import converters as ot2_converters
from ot2 import constants as ot2_constants
from ot2 import tweaks as tw


MMML_CONVERTER = converters.backends.mmml.MMMLConverter(
    converters.backends.mmml.MMMLEventsConverter(
        converters.backends.mmml.MMMLPitchesConverter(
            converters.backends.mmml.MMMLSingleJIPitchConverter()
        )
    )
)


def add_last_bar_via_mmml(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ],
    time_signatures,
):
    added_part = f"""
${ot2_constants.instruments.ID_SUS0}
7+3--:-1`3/16*p r`16
3+`4
7+3--`4
7+`3/8 7+3--`8
3+`12 7+3--`12 7+`12

${ot2_constants.instruments.ID_SUS1}
7+3-:-1`3/8*p
1`8
3++`8 7+3-`8
7+3+`3/8 7+3-`8
3++`12 7+3-`12 7+3+`12

${ot2_constants.instruments.ID_SUS2}
7+3-:-1`4*p
r`8 7+`8
7+3--`8 3+`8
7+3+`12 7+3-`12 3++`6
7+3-`12 7+3+`6
7+3-`12 3++`12

${ot2_constants.instruments.ID_KEYBOARD}0
1`8*p 7+3-:0`16 3++`16
1`8 3++`16 1:0`16
1`16 7+:-1`8 3+:-1`16
7+3--:-1`16 7+:-1`16 1:0`16 3++`16
7+3--:-1`16 7+:-1`16 1:0`16 3++`16
7+3--:-1`12 1:0`12 3++`12

${ot2_constants.instruments.ID_KEYBOARD}1
7+3--:-2`16*p 3+`8 7+`16
# 7+3--:-2`16 3+`8 7+`16
7+3--:-2`8 3+`8
7+3--:-2`16 3+`16 7+`16 3++:-1`16
7+3-:-1`16 3++`16 1`16 7+:-2`16
7+3-:-1`16 3++`16 1`16 7+:-2`16
7+3-:-1`12 1`12 7+:-2`12
"""
    convertered_mmml_part = MMML_CONVERTER.convert(added_part)

    instruments, tape = time_brackets_to_post_process

    sus_instr0 = instruments[0][0]
    sus_instr1 = instruments[1][0]
    sus_instr2 = instruments[2][0]
    keyboard = instruments[3]
    right_hand, left_hand = keyboard

    for _ in range(3):
        time_signatures.append(abjad.TimeSignature((3, 4)))

    sus_instr0.extend(convertered_mmml_part[ot2_constants.instruments.ID_SUS0])
    sus_instr1.extend(convertered_mmml_part[ot2_constants.instruments.ID_SUS1])
    sus_instr2.extend(convertered_mmml_part[ot2_constants.instruments.ID_SUS2])
    right_hand.extend(
        convertered_mmml_part[ot2_constants.instruments.ID_KEYBOARD + "0"]
    )
    left_hand.extend(convertered_mmml_part[ot2_constants.instruments.ID_KEYBOARD + "1"])

    # sus_instr0[-1].playing_indicators.tie.is_active = True
    # sus_instr1[-1].playing_indicators.tie.is_active = True
    # sus_instr2[-1].playing_indicators.tie.is_active = True

    for instr in (sus_instr0, sus_instr1, sus_instr2, right_hand, left_hand):
        instr[-1].playing_indicators.tie.is_active = True
        instr.append(
            events.music.NoteLike(
                instr[-1].pitch_or_pitches, fractions.Fraction(1, 4), instr[-1].volume
            )
        )

    # for instr in (right_hand, left_hand):
    #     instr[-2].playing_indicators.tie.is_active = False
    #     instr[-1].pitch_or_pitches = []


def add_longer_cadenza(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ],
    time_signatures,
):
    instruments, tape = time_brackets_to_post_process

    sus_instr0 = instruments[0][0]
    sus_instr1 = instruments[1][0]
    sus_instr2 = instruments[2][0]
    keyboard = instruments[3]
    right_hand, left_hand = keyboard

    for sequential_event in keyboard:
        tw.shorten(
            sequential_event, len(sequential_event) - 1, fractions.Fraction(1, 2)
        )

    left_hand[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("5/10")
    tw.safe_delay(left_hand, len(left_hand) - 1, fractions.Fraction(3, 8))
    left_hand[-1].volume = left_hand[-3].volume

    right_hand[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("5/4")
    tw.safe_delay(right_hand, len(right_hand) - 1, fractions.Fraction(3, 8))
    right_hand[-1].volume = right_hand[-3].volume

    delay_size = fractions.Fraction(2, 8)
    upbeat_size = fractions.Fraction(2, 8)
    alteration_intervals = (
        (
            parameters.pitches.JustIntonationPitch("15/14"),
            # parameters.pitches.JustIntonationPitch("15/14"),
            # parameters.pitches.JustIntonationPitch("36/35"),
            # parameters.pitches.JustIntonationPitch("20/21"),
            parameters.pitches.JustIntonationPitch("8/7"),
            # parameters.pitches.JustIntonationPitch("1/1"),
            # parameters.pitches.JustIntonationPitch("1/1"),
            # parameters.pitches.JustIntonationPitch("32/35"),
        ),
    )
    for sequential_event, instrument_id in (
        (sus_instr0, ot2_constants.instruments.ID_SUS0),
        (sus_instr1, ot2_constants.instruments.ID_SUS1),
        (sus_instr2, ot2_constants.instruments.ID_SUS2),
        (left_hand, ot2_constants.instruments.ID_KEYBOARD),
        (right_hand, ot2_constants.instruments.ID_KEYBOARD),
    ):
        is_keyboard = instrument_id == ot2_constants.instruments.ID_KEYBOARD
        if not is_keyboard:
            tw.safe_delay(sequential_event, len(sequential_event) - 1, delay_size)
        if not is_keyboard:
            tw.split(
                sequential_event,
                len(sequential_event) - 1,
                fractions.Fraction(4, 4)
                - delay_size
                - upbeat_size
                - fractions.Fraction(2, 8),
                fractions.Fraction(1, 8),
                fractions.Fraction(1, 8),
            )
            sequential_event[-3].pitch_or_pitches = []
        if instrument_id == ot2_constants.instruments.ID_SUS1:
            tw.eat(sequential_event, len(sequential_event) - 3, 2)
        for nth_alt_intervals, alt_intervals in enumerate(alteration_intervals):
            end_alteration_interval, common_alteration_interval = alt_intervals
            if not is_keyboard:
                if instrument_id != ot2_constants.instruments.ID_SUS1:
                    sequential_event[-1].pitch_or_pitches[0] = (
                        sequential_event[-2]
                        .pitch_or_pitches[0]
                        .add(end_alteration_interval, mutate=False)
                    )
            """
            duration_of_last_two_bars = fractions.Fraction(8 + 4, 4)
            duration = sequential_event.duration
            repetition = sequential_event.cut_out(
                duration - duration_of_last_two_bars, duration, mutate=False
            )
            """
            duration_of_last_two_bars = fractions.Fraction(8 + 4, 4)
            duration_of_removed_bar = fractions.Fraction(4, 4)
            duration = sequential_event.duration
            repetition = sequential_event.cut_out(
                duration - duration_of_last_two_bars,
                duration - duration_of_removed_bar,
                mutate=False,
            )
            repetition.set_parameter(
                "pitch_or_pitches",
                lambda pitch_or_pitches: [
                    pitch + common_alteration_interval for pitch in pitch_or_pitches
                ]
                if pitch_or_pitches
                else None,
            )

            if instrument_id == ot2_constants.instruments.ID_SUS0:
                repetition[-3].pitch_or_pitches = [
                    parameters.pitches.JustIntonationPitch("3/4")
                ]
                repetition[3].pitch_or_pitches = [
                    parameters.pitches.JustIntonationPitch("8/9")
                ]
                # tw.shorten(repetition, 8, fractions.Fraction(1, 12), False)
                repetition[-2] = repetition[-1]
                tw.eat(repetition, len(repetition) - 2)
                # repetition[5].pitch_or_pitches = parameters.pitches.JustIntonationPitch('9/10')
                repetition[5].pitch_or_pitches[
                    0
                ] -= parameters.pitches.JustIntonationPitch("81/80")
                tw.shorten(repetition, 3, fractions.Fraction(1, 6))
                tw.prolong(repetition, 1, fractions.Fraction(1, 6))
                tw.eat(sus_instr0, len(sus_instr0) - 3, 2)

            if instrument_id == ot2_constants.instruments.ID_SUS1:
                tw.eat(repetition, len(repetition) - 2)
                repetition[-1].pitch_or_pitches = [
                    parameters.pitches.JustIntonationPitch("3/4")
                ]
                # tw.split(repetition, 1, fractions.Fraction(1, 4))
                # repetition[1].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
                #     "1/2"
                # )
                tw.safe_delay(repetition, 1, fractions.Fraction(1, 4))
                # repetition[4].pitch_or_pitches = parameters.pitches.JustIntonationPitch('45/64')
                tw.prolong(repetition, 3, fractions.Fraction(1, 12))

            if instrument_id == ot2_constants.instruments.ID_SUS2:
                tw.split(repetition, 2, fractions.Fraction(3, 4))
                repetition[3].pitch_or_pitches = [
                    parameters.pitches.JustIntonationPitch("9/8")
                ]
                tw.split(repetition, 2, fractions.Fraction(1, 4))
                repetition[3].pitch_or_pitches = []
                tw.shorten(repetition, 0, fractions.Fraction(1, 8))

            if instrument_id == ot2_constants.instruments.ID_KEYBOARD:
                repetition[2].pitch_or_pitches[
                    0
                ] -= parameters.pitches.JustIntonationPitch("5/4")
                repetition[4].pitch_or_pitches[
                    0
                ] += parameters.pitches.JustIntonationPitch("20/27")
                # repetition[4].pitch_or_pitches[
                #     0
                # ] += parameters.pitches.JustIntonationPitch("81/80")
                repetition[7].pitch_or_pitches[
                    0
                ] += parameters.pitches.JustIntonationPitch("15/14")
                repetition[8].pitch_or_pitches[
                    0
                ] += parameters.pitches.JustIntonationPitch("81/80")
                repetition[1].pitch_or_pitches[
                    0
                ] += parameters.pitches.JustIntonationPitch("81/80")
                # repetition[5].pitch_or_pitches[
                #     0
                # ] += parameters.pitches.JustIntonationPitch("36/35")
                repetition[5].pitch_or_pitches[
                    0
                ] -= parameters.pitches.JustIntonationPitch("81/80")

                if repetition[-1].duration == fractions.Fraction(1, 16):
                    repetition[-2].pitch_or_pitches[
                        0
                    ] += parameters.pitches.JustIntonationPitch("15/14")
                    # repetition[-1].pitch_or_pitches[
                    #     0
                    # ] = parameters.pitches.JustIntonationPitch("9/4")
                    repetition[-1].pitch_or_pitches[
                        0
                        # ] = parameters.pitches.JustIntonationPitch("32/15")
                    ] = parameters.pitches.JustIntonationPitch("70/36")
                    repetition[
                        3
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("16/9")
                    tw.split(repetition, 3, fractions.Fraction(3, 16))
                    repetition[4].pitch_or_pitches[0].add(
                        parameters.pitches.JustIntonationPitch("15/16")
                    )
                    tw.safe_delay(repetition, 0, fractions.Fraction(1, 8))
                    tw.prolong(repetition, 2, fractions.Fraction(1, 8))
                    repetition[
                        0
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("2/1")
                    repetition[0].volume = repetition[1].volume
                    repetition.set_parameter(
                        "pitch_or_pitches",
                        lambda pitch_or_pitches: [
                            pitch - parameters.pitches.JustIntonationPitch("2/1")
                            for pitch in pitch_or_pitches
                        ]
                        if pitch_or_pitches
                        else pitch_or_pitches,
                    )

                else:
                    repetition[
                        3
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("4/9")

                    tw.split(repetition, 3, fractions.Fraction(3, 16))
                    repetition[4].pitch_or_pitches[0].add(
                        parameters.pitches.JustIntonationPitch("15/16")
                    )

            sequential_event.extend(repetition)

    # postprocess added modulated cadenza

    added_time_signatures = [abjad.TimeSignature((8, 4))]
    duration_of_last_musical_data = fractions.Fraction(4, 4)
    duration = sequential_event.duration
    n_waitings = 3
    is_first = True
    for sequential_event, instrument_id in (
        (sus_instr0, ot2_constants.instruments.ID_SUS0),
        (sus_instr1, ot2_constants.instruments.ID_SUS1),
        (sus_instr2, ot2_constants.instruments.ID_SUS2),
        (left_hand, ot2_constants.instruments.ID_KEYBOARD),
        (right_hand, ot2_constants.instruments.ID_KEYBOARD),
    ):
        blueprint = sequential_event.cut_out(
            duration - duration_of_last_musical_data, duration, mutate=False
        )
        for waiting in range(n_waitings):
            version = blueprint.destructive_copy()
            if instrument_id == ot2_constants.instruments.ID_SUS0:
                version[1].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
                    "8/9"
                )
            elif instrument_id == ot2_constants.instruments.ID_KEYBOARD:
                version[1].pitch_or_pitches[
                    0
                ] += parameters.pitches.JustIntonationPitch("36/35")
                version[3].pitch_or_pitches[
                    0
                ] += parameters.pitches.JustIntonationPitch("128/135")
                version[3].pitch_or_pitches = version[1].pitch_or_pitches
                version[3].pitch_or_pitches = version[1].pitch_or_pitches
                if version[-1].duration == fractions.Fraction(1, 16):
                    version[
                        -1
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("9/4")

            time_signature = abjad.TimeSignature((4, 4))
            if waiting == 0:
                if instrument_id == ot2_constants.instruments.ID_SUS0:
                    version[-2].pitch_or_pitches = copy.deepcopy(
                        version[-1].pitch_or_pitches
                    )
                    tw.eat(version, len(version) - 2)
                    tw.prolong(version, 0, fractions.Fraction(1, 12))
                    version[0].duration = fractions.Fraction(1, 8)
                    for n in (1, 2):
                        version[n].duration = fractions.Fraction(1, 8)
                    version[3].duration = fractions.Fraction(5, 8)
                    tw.prolong(version, 2, fractions.Fraction(1, 4))
                    tw.shorten(version, len(version) - 1, fractions.Fraction(1, 8))

                elif instrument_id == ot2_constants.instruments.ID_SUS1:
                    tw.prolong(version, 0, fractions.Fraction(1, 24))

                elif instrument_id == ot2_constants.instruments.ID_SUS2:
                    tw.shorten(version, len(version) - 1, fractions.Fraction(1, 8))

                elif instrument_id == ot2_constants.instruments.ID_KEYBOARD:
                    version[3].pitch_or_pitches = []
                    if version[-1].duration == fractions.Fraction(1, 16):
                        tw.eat(version, len(version) - 2)
                    else:
                        for n in (0, 1, 2):
                            version[n].pitch_or_pitches[
                                0
                            ] -= parameters.pitches.JustIntonationPitch("2/1")
                        tw.eat(version, len(version) - 2)

                time_signature = abjad.TimeSignature((7, 4))
                added_left = fractions.Fraction(3, 8)
                shorten_right = fractions.Fraction(1, 8)
                added_right = fractions.Fraction(3, 8)
                # version[-1].duration += added_right
                tw.shorten(version, len(version) - 1, shorten_right)
                version[-1].duration += added_right
                # version.append(
                #     events.music.NoteLike([], added_right, version[-1].volume)
                # )
                version[0].duration += added_left
                tw.safe_delay(version, 0, added_left)
                # version[1].pitch_or_pitches[
                #     0
                # ] -= parameters.pitches.JustIntonationPitch("2/1")

            elif waiting == 1:
                if instrument_id == ot2_constants.instruments.ID_SUS0:
                    version[-2].pitch_or_pitches = copy.deepcopy(
                        version[-1].pitch_or_pitches
                    )
                    tw.eat(version, len(version) - 2)
                    version[1].pitch_or_pitches = copy.deepcopy(
                        version[-1].pitch_or_pitches
                    )
                    tw.prolong(version, 0, fractions.Fraction(1, 12))
                    tw.shorten(version, 3, fractions.Fraction(1, 4))

                elif instrument_id == ot2_constants.instruments.ID_SUS1:
                    tw.prolong(version, 0, fractions.Fraction(1, 24))
                    # version[0].pitch_or_pitches = copy.deepcopy(version[-1].pitch_or_pitches)
                    pass

                elif instrument_id == ot2_constants.instruments.ID_SUS2:
                    version[0].pitch_or_pitches = copy.deepcopy(
                        version[1].pitch_or_pitches
                    )
                    tw.eat(version, 0)
                    tw.safe_delay(version, 0, fractions.Fraction(1, 4))
                    tw.shorten(version, 1, fractions.Fraction(2, 4))

                elif instrument_id == ot2_constants.instruments.ID_KEYBOARD:
                    version[0].pitch_or_pitches[
                        0
                    ] += parameters.pitches.JustIntonationPitch("81/80")
                    for n in (1, 3):
                        version[n].pitch_or_pitches[
                            0
                        ] += parameters.pitches.JustIntonationPitch("135/128")

                    if version[-1].duration == fractions.Fraction(1, 16):
                        version[-1].pitch_or_pitches[0] = version[-1].pitch_or_pitches[
                            0
                        ] - parameters.pitches.JustIntonationPitch("2/1")

                time_signature = abjad.TimeSignature((5, 4))
                absolute_time_where_to_add = fractions.Fraction(2, 4)
                added = fractions.Fraction(1, 4)
                version.get_event_at(absolute_time_where_to_add).duration += added

                if instrument_id == ot2_constants.instruments.ID_SUS1:
                    tw.shorten(version, len(version) - 2, fractions.Fraction(3, 8))

            elif waiting in (2,):
                if instrument_id == ot2_constants.instruments.ID_SUS0:
                    version[
                        1
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("7/8")
                    version[
                        2
                        # ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("4/5")
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("7/9")
                    version[
                        3
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("7/8")
                    tw.eat(version, 3)

                elif instrument_id == ot2_constants.instruments.ID_SUS1:
                    tw.shorten(version, 0, fractions.Fraction(1, 24), False)
                    version[0].pitch_or_pitches = version[2].pitch_or_pitches[
                        0
                    ] + parameters.pitches.JustIntonationPitch("1/1")
                    version[0].volume = version[1].volume
                    tw.eat(version, 0, 2)
                    tw.safe_delay(version, 0, fractions.Fraction(4, 8))
                    tw.split(version, 1, fractions.Fraction(1, 4))
                    version[
                        -1
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("21/32")

                elif instrument_id == ot2_constants.instruments.ID_SUS2:
                    version[0].pitch_or_pitches = copy.deepcopy(
                        version[1].pitch_or_pitches
                    )
                    tw.eat(version, 0)
                    version[0].pitch_or_pitches[0].add(
                        parameters.pitches.JustIntonationPitch("1/2")
                        # parameters.pitches.JustIntonationPitch("1/1")
                    )
                    tw.split(
                        version,
                        0,
                        fractions.Fraction(1, 3),
                        fractions.Fraction(1, 6),
                    )
                    version[
                        1
                    ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("7/12")
                    # ].pitch_or_pitches = parameters.pitches.JustIntonationPitch("7/6")

                elif instrument_id == ot2_constants.instruments.ID_KEYBOARD:
                    to_adjust = version[0].pitch_or_pitches[0].normalize(mutate=False)
                    for event in version:
                        try:
                            pitch = event.pitch_or_pitches[0]
                        except IndexError:
                            pitch = None
                        if pitch:
                            normalized_pitch = pitch.normalize(mutate=False)
                            if (
                                normalized_pitch
                                == parameters.pitches.JustIntonationPitch("15/8")
                            ):
                                event.pitch_or_pitches[0].add(
                                    parameters.pitches.JustIntonationPitch("14/15")
                                )
                            elif (
                                normalized_pitch
                                == parameters.pitches.JustIntonationPitch("5/3")
                            ):
                                event.pitch_or_pitches[0].add(
                                    # parameters.pitches.JustIntonationPitch("24/25")
                                    parameters.pitches.JustIntonationPitch("14/15")
                                )

                            elif (
                                normalized_pitch
                                == parameters.pitches.JustIntonationPitch("16/9")
                            ):
                                event.pitch_or_pitches[0].add(
                                    parameters.pitches.JustIntonationPitch("63/64")
                                )

                            elif normalized_pitch == to_adjust:
                                event.pitch_or_pitches[0].add(
                                    parameters.pitches.JustIntonationPitch("81/80")
                                )

                            elif (
                                normalized_pitch
                                == parameters.pitches.JustIntonationPitch("5/4")
                            ):
                                event.pitch_or_pitches[0].add(
                                    parameters.pitches.JustIntonationPitch("14/15")
                                )

                    version[3].pitch_or_pitches = []
                    version[6].pitch_or_pitches = []

                    if version[-1].duration == fractions.Fraction(1, 16):
                        version[-1].pitch_or_pitches[0] = version[-1].pitch_or_pitches[
                            0
                        ] - parameters.pitches.JustIntonationPitch("2/1")
                        # version[
                        #     0
                        # ].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
                        #     "1/1"
                        # )
                    else:
                        pass

                    # tw.prolong(version, 1, fractions.Fraction(1, 16))
                    # tw.prolong(version, 3, fractions.Fraction(1, 16))

                time_signature = abjad.TimeSignature((5, 4))
                if waiting == 2:
                    absolute_time_where_to_add = fractions.Fraction(3, 4)
                elif waiting == 3:
                    absolute_time_where_to_add = fractions.Fraction(1, 4)
                elif waiting == 4:
                    absolute_time_where_to_add = fractions.Fraction(0, 4)
                else:
                    absolute_time_where_to_add = fractions.Fraction(3, 4)
                added = fractions.Fraction(1, 4)
                version.get_event_at(absolute_time_where_to_add).duration += added

                if instrument_id == ot2_constants.instruments.ID_KEYBOARD:
                    if version[-1].duration == fractions.Fraction(1, 16):
                        tw.split(version, 6, fractions.Fraction(1, 4))
                        version[
                            7
                        ].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
                            "1/1"
                        )
                        tw.split(version, 8, fractions.Fraction(1, 16))
                        version[
                            9
                        ].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
                            "7/6"
                        )
                    else:
                        tw.split(version, 6, fractions.Fraction(5, 16))
                        version[
                            7
                        ].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
                            "3/8"
                        )
                        tw.prolong(version, 7, fractions.Fraction(1, 16))

            """
            if waiting + 1 == n_waitings:
                time_signature = abjad.TimeSignature((7, 4))
                # time_signature = abjad.TimeSignature((6, 4))
                added = fractions.Fraction(2, 4)
                # added_rest = fractions.Fraction(1, 8)
                version[-1].duration += added
                # version[-1].duration += added_rest
                # version.append(events.music.NoteLike([], added_rest))
            """

            sequential_event.extend(version)
            if is_first:
                added_time_signatures.append(time_signature)

            if waiting == 1:
                if instrument_id == ot2_constants.instruments.ID_SUS1:
                    tw.eat(sequential_event, len(sequential_event) - 4)
                    tw.shorten(
                        sequential_event,
                        len(sequential_event) - 1,
                        fractions.Fraction(1, 4),
                    )

        is_first = False

    tw.safe_delay(right_hand, 41, delay_size)
    tw.safe_delay(left_hand, 38, delay_size)

    add_last_bar_via_mmml(time_brackets_to_post_process, added_time_signatures)

    vol = "p"
    # rest = fractions.Fraction(4, 8)
    rest = fractions.Fraction(6, 8)
    duration = fractions.Fraction(8, 4) - rest
    for pitch, instr in (
        (parameters.pitches.JustIntonationPitch("7/9"), sus_instr0),
        # (parameters.pitches.JustIntonationPitch("6/7"), sus_instr0),
        (parameters.pitches.JustIntonationPitch("1/2"), sus_instr2),  # for tonal sound
        # (parameters.pitches.JustIntonationPitch("9/16"), sus_instr2),  # for dissonant sound
        # (parameters.pitches.JustIntonationPitch("1/2"), sus_instr2),
        (parameters.pitches.JustIntonationPitch("7/12"), sus_instr1),
        # (parameters.pitches.JustIntonationPitch("9/14"), sus_instr1),
        (parameters.pitches.JustIntonationPitch("7/6"), right_hand),
        # (parameters.pitches.JustIntonationPitch("18/7"), right_hand),
        (parameters.pitches.JustIntonationPitch("7/18"), left_hand),
        # (parameters.pitches.JustIntonationPitch("3/7"), left_hand),
    ):
        instr.append(events.music.NoteLike([], rest, vol))
        instr.append(events.music.NoteLike(pitch, duration, vol))

    # tw.prolong(sus_instr0, len(sus_instr0) - 3, fractions.Fraction(1, 8))
    # tw.prolong(sus_instr1, len(sus_instr1) - 3, fractions.Fraction(1, 8))

    for sus_instr in (sus_instr0, sus_instr1, sus_instr2):
        tw.prolong(sus_instr, len(sus_instr) - 3, fractions.Fraction(1, 8))
        # tw.split(sus_instr, len(sus_instr) - 2, fractions.Fraction(1, 8))
        # sus_instr[-3].pitch_or_pitches = sus_instr[-4].pitch_or_pitches

    tw.eat(left_hand, len(left_hand) - 3)
    tw.eat(right_hand, len(right_hand) - 3)

    # tw.split(left_hand, len(left_hand) - 2, fractions.Fraction(8, 16))
    # tw.split(right_hand, len(right_hand) - 2, fractions.Fraction(8, 16))
    tw.split(
        left_hand,
        len(left_hand) - 2,
        fractions.Fraction(12, 16),
        fractions.Fraction(2, 16),
    )
    tw.split(
        right_hand,
        len(right_hand) - 2,
        fractions.Fraction(12, 16),
        fractions.Fraction(2, 16),
    )
    right_hand[-3].pitch_or_pitches = []
    right_hand[-2].pitch_or_pitches = []
    left_hand[-3].pitch_or_pitches = []
    left_hand[-2].pitch_or_pitches = left_hand[-5].pitch_or_pitches

    # added_time_signatures.append(abjad.TimeSignature((8, 4)))
    added_time_signatures.append(abjad.TimeSignature((6, 4)))

    instr_duration = sus_instr0.duration

    """
    common_difference = instr_duration - tape[0][0].duration
    for tagged_simultaneous_event in instruments:
        for sequential_event in tagged_simultaneous_event:
            start = sequential_event.get_event_index_at(
                instr_duration - common_difference
            )
            sequential_event[start:].set_parameter(
                "pitch_or_pitches",
                lambda pitch_or_pitches: [
                    pitch - parameters.pitches.JustIntonationPitch("8/7")
                    for pitch in pitch_or_pitches
                ]
                if pitch_or_pitches
                else pitch_or_pitches,
            )
    """

    for tagged_simultaneous_event in tape:
        for sequential_event in tagged_simultaneous_event:
            difference = instr_duration - sequential_event.duration
            sequential_event.append(events.music.NoteLike([], difference))
        if tagged_simultaneous_event.tag == ot2_constants.instruments.ID_GONG:
            sequential_event[-2].pitch_or_pitches = []
            tw.split(
                sequential_event,
                len(sequential_event) - 1,
                sequential_event[-1].duration - fractions.Fraction(8, 4),
            )
            sequential_event[-1].pitch_or_pitches = [
                parameters.pitches.JustIntonationPitch("7/18")
            ]
            sequential_event[-1].volume = "pp"

    time_signatures.extend(added_time_signatures)


def add_tonality_flux(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ],
    time_signatures,
):
    new_time_signature = abjad.TimeSignature((12, 4))
    duration = fractions.Fraction(new_time_signature.duration)
    time_signatures[-1] = abjad.TimeSignature((7, 4))
    time_signatures.append(new_time_signature)

    instruments, tape = time_brackets_to_post_process

    sus_instr0 = instruments[0][0]
    sus_instr1 = instruments[1][0]
    sus_instr2 = instruments[2][0]
    keyboard = instruments[3]
    right_hand, left_hand = keyboard

    tw.split(
        sus_instr0,
        len(sus_instr0) - 1,
        # fractions.Fraction(1, 2),
        # fractions.Fraction(1, 4),
        # fractions.Fraction(1, 2),
        # fractions.Fraction(1, 2),
        fractions.Fraction(1, 4),
        fractions.Fraction(3, 4),
    )
    sus_instr0[-2].pitch_or_pitches = []
    sus_instr0[-1].playing_indicators.glissando.is_active = True

    tw.split(
        sus_instr1,
        len(sus_instr1) - 1,
        # fractions.Fraction(3, 4),
        # fractions.Fraction(1, 4),
        # fractions.Fraction(1, 2),
        fractions.Fraction(3, 8),
        # fractions.Fraction(1, 2),
        # fractions.Fraction(3, 8),
        fractions.Fraction(4, 8),
        # fractions.Fraction(1, 8),
        fractions.Fraction(1, 4),
    )
    sus_instr1[-3].pitch_or_pitches = []
    # sus_instr1[-1].playing_indicators.glissando.is_active = True

    tw.split(
        sus_instr2,
        len(sus_instr2) - 1,
        # fractions.Fraction(3, 4),
        # fractions.Fraction(1, 4),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
    )
    sus_instr2[-2].pitch_or_pitches = []
    sus_instr2[-1].playing_indicators.glissando.is_active = True

    tw.split(
        right_hand,
        len(right_hand) - 1,
        fractions.Fraction(6, 8),
        fractions.Fraction(1, 8),
        fractions.Fraction(1, 8),
    )
    right_hand[-3].pitch_or_pitches = parameters.pitches.JustIntonationPitch("1/1")
    right_hand[-2].pitch_or_pitches = parameters.pitches.JustIntonationPitch("9/8")
    right_hand[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("4/3")

    pitch_per_event = (
        parameters.pitches.JustIntonationPitch("16/21"),
        parameters.pitches.JustIntonationPitch("16/27"),
        parameters.pitches.JustIntonationPitch("32/63"),
        parameters.pitches.JustIntonationPitch("4/27"),
        parameters.pitches.JustIntonationPitch("32/21"),
    )
    for pitch, sequential_event in zip(
        pitch_per_event, (sus_instr0, sus_instr1, sus_instr2, left_hand, right_hand)
    ):
        note = events.music.NoteLike(pitch, duration, "p")
        sequential_event.append(note)

    # for sequential_event in (right_hand, left_hand):
    #     tw.prolong(sequential_event, len(sequential_event) - 2, fractions.Fraction(1, 2))

    sus_instr1[-2].pitch_or_pitches = sus_instr1[-1].pitch_or_pitches
    tw.eat(sus_instr1, len(sus_instr1) - 2)

    part0_duration = fractions.Fraction(3, 8)
    tw.split(sus_instr0, len(sus_instr0) - 1, part0_duration + fractions.Fraction(1, 8))
    tw.split(sus_instr2, len(sus_instr2) - 1, part0_duration + fractions.Fraction(3, 8))
    tw.split(right_hand, len(right_hand) - 1, part0_duration)
    sus_instr0[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("20/27")
    sus_instr2[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("40/81")
    right_hand[-1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("40/27")

    tw.split(
        left_hand,
        len(left_hand) - 1,
        fractions.Fraction(1, 2),
        # fractions.Fraction(1, 2),
        fractions.Fraction(1, 1),
    )

    added = fractions.Fraction(1, 4)
    sus_instr0[-3].duration += added
    sus_instr1[-1].duration += added
    sus_instr2[-3].duration += added
    right_hand[-3].duration += added
    left_hand[-4].duration += added

    tw.split(sus_instr1, len(sus_instr1) - 1, fractions.Fraction(1, 4))

    tw.split(right_hand, len(right_hand) - 3, fractions.Fraction(3, 8))
    right_hand[-3].pitch_or_pitches = right_hand[-2].pitch_or_pitches

    tw.split(
        right_hand,
        len(right_hand) - 1,
        fractions.Fraction(1, 8),
        # fractions.Fraction(3, 8),
        fractions.Fraction(3, 8) + fractions.Fraction(1, 2),
        fractions.Fraction(1, 8),
    )

    for sus_instr in (sus_instr0, sus_instr2):
        tw.split(sus_instr, len(sus_instr) - 3, fractions.Fraction(1, 4))
        sus_instr[-4].playing_indicators.glissando.is_active = False
        sus_instr[-4].playing_indicators.tie.is_active = True

    for sequential_event in (sus_instr0, sus_instr1, sus_instr2, left_hand, right_hand):
        sequential_event[-1].playing_indicators.fermata.fermata_type = "longfermata"

    for tagged_simultaneous_event in tape:
        for sequential_event in tagged_simultaneous_event:
            sequential_event.append(events.music.NoteLike([], duration))


def post_process_cengkok_12(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ]
):
    for time_bracket in time_brackets_to_post_process:
        time_bracket.delay(0)
        # time_bracket.delay(30)
        # time_bracket.delay(50)

    time_signature_for_bar_0 = abjad.TimeSignature((9, 4))
    duration_of_rest_in_bar_0 = fractions.Fraction(5, 4)

    time_signature_for_bar_1 = abjad.TimeSignature((6, 4))
    duration_of_rest_in_bar_1 = fractions.Fraction(2, 4)

    time_signature_for_bar_3 = abjad.TimeSignature((7, 4))
    duration_of_rest_in_bar_3 = fractions.Fraction(3, 4)

    instruments, tape = time_brackets_to_post_process

    old_tempo = instruments.tempo
    new_tempo = 30
    factor_between_tempo = old_tempo / new_tempo
    start_duration = instruments[0].duration

    sus_instr0 = instruments[0][0]
    sus_instr1 = instruments[1][0]
    sus_instr2 = instruments[2][0]
    keyboard = instruments[3]
    right_hand, left_hand = keyboard

    sus_instr0[0].duration += duration_of_rest_in_bar_0
    sus_instr0[3].duration += duration_of_rest_in_bar_1
    tw.shorten(sus_instr0, 4, fractions.Fraction(1, 24), False)
    tw.delay(sus_instr0, 4, fractions.Fraction(2, 24))
    tw.shorten(sus_instr0, 2, fractions.Fraction(1, 12))
    sus_instr0[10].duration += duration_of_rest_in_bar_3
    tw.shorten(sus_instr0, 10, duration_of_rest_in_bar_3 + fractions.Fraction(1, 4))
    tw.eat(sus_instr0, 18, 12)
    tw.shorten(sus_instr0, 18, fractions.Fraction(2, 3), False)
    tw.split(
        sus_instr0,
        19,
        fractions.Fraction(2, 3),
        fractions.Fraction(1, 3),
        fractions.Fraction(1, 3),
        fractions.Fraction(1, 3),
    )
    sus_instr0[20].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("49/64")]
    sus_instr0[21].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("35/48")]
    sus_instr0[22].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("49/64")]
    # sus_instr0[21].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("35/48")]
    # sus_instr0[21].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("49/72")]
    tw.eat(sus_instr0, 23)
    tw.split(sus_instr0, 18, fractions.Fraction(3, 4), fractions.Fraction(5, 4))
    sus_instr0[20] = events.music.NoteLike(
        [parameters.pitches.JustIntonationPitch("32/33")],
        sus_instr0[20].duration,
        sus_instr0[21].volume,
    )
    tw.shorten(sus_instr0, 20, fractions.Fraction(4, 12), False)
    tw.shorten(sus_instr0, 21, fractions.Fraction(1, 3), False)
    tw.split(sus_instr0, 23, fractions.Fraction(1, 6))
    tw.split(sus_instr0, 25, fractions.Fraction(1, 6))
    sus_instr0[24].pitch_or_pitches = [
        parameters.pitches.JustIntonationPitch("35/36")
        - parameters.pitches.JustIntonationPitch("3/2")
    ]
    sus_instr0[25].pitch_or_pitches = copy.deepcopy(sus_instr0[23].pitch_or_pitches)
    tw.split(
        sus_instr0,
        21,
        fractions.Fraction(1, 6),
        fractions.Fraction(1, 6),
        fractions.Fraction(1, 3),
    )
    sus_instr0[22].pitch_or_pitches = []
    tw.split(
        sus_instr0,
        24,
        fractions.Fraction(1, 3),
        fractions.Fraction(1, 6),
        fractions.Fraction(1, 6),
    )
    sus_instr0[25].pitch_or_pitches = []
    sus_instr0[30].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
        "7/8"
    ) - parameters.pitches.JustIntonationPitch("16/15")
    tw.split(sus_instr0, 0, fractions.Fraction(1, 8), fractions.Fraction(2, 8))
    sus_instr0[1] = events.music.NoteLike(
        [parameters.pitches.JustIntonationPitch("7/10")], sus_instr0[1].duration
    )
    sus_instr0[1].volume = parameters.volumes.WesternVolume("mp")

    sus_instr1[0].duration += duration_of_rest_in_bar_0
    tw.eat(sus_instr1, 2, 3)
    sus_instr1[2].duration += duration_of_rest_in_bar_1
    sus_instr1[6].duration += duration_of_rest_in_bar_3
    tw.eat(sus_instr1, 6, 3)
    tw.eat(sus_instr1, 20, 4)
    tw.shorten(sus_instr1, 20, fractions.Fraction(2, 4))
    sus_instr1[21].pitch_or_pitches = [
        sus_instr1[20].pitch_or_pitches[0]
        # .add(parameters.pitches.JustIntonationPitch("5/4"), mutate=False)
        .add(parameters.pitches.JustIntonationPitch("1/1"), mutate=False)
    ]
    # tw.split(sus_instr1, 20, fractions.Fraction(3, 4))
    tw.split(sus_instr1, 20, fractions.Fraction(4, 4))
    sus_instr1[21].pitch_or_pitches = [
        parameters.pitches.JustIntonationPitch("35/36")
        - parameters.pitches.JustIntonationPitch("3/2")
    ]
    tw.safe_delay(sus_instr0, 21, fractions.Fraction(1, 4))
    tw.split(sus_instr1, 20, fractions.Fraction(1, 4), fractions.Fraction(1, 4))
    sus_instr1[21].pitch_or_pitches = []
    tw.split(
        sus_instr1,
        23,
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 4),
        fractions.Fraction(1, 4),
    )
    sus_instr1[24].pitch_or_pitches = []
    sus_instr1[25].pitch_or_pitches = copy.deepcopy(sus_instr1[22].pitch_or_pitches)
    sus_instr1[27].pitch_or_pitches = parameters.pitches.JustIntonationPitch("21/32")
    tw.split(sus_instr1, 26, fractions.Fraction(3, 8))
    sus_instr1[27].pitch_or_pitches = [
        parameters.pitches.JustIntonationPitch("315/512")
    ]
    tw.eat(sus_instr1, 0, 3)

    sus_instr2[0].duration += duration_of_rest_in_bar_0
    tw.delay(sus_instr2, 1, fractions.Fraction(1, 4))
    sus_instr2[0].duration += duration_of_rest_in_bar_1
    sus_instr2[7].duration += duration_of_rest_in_bar_3
    tw.shorten(sus_instr2, 15, fractions.Fraction(13, 12))
    tw.delay(sus_instr2, 17, fractions.Fraction(5, 12))
    tw.split(sus_instr2, 0, fractions.Fraction(3, 8))
    sus_instr2[0] = events.music.NoteLike(
        [parameters.pitches.JustIntonationPitch("7/10")], sus_instr2[0].duration
    )
    sus_instr2[1:2], sus_instr0[2:6] = sus_instr0[2:6], sus_instr2[1:2]
    # tw.eat(sus_instr2)
    tw.eat(sus_instr2, 22)
    tw.shorten(
        sus_instr2, 22, fractions.Fraction(1, 12) + fractions.Fraction(3, 4), False
    )
    tw.eat(sus_instr2, 23)
    tw.eat(sus_instr2, 24, 3)
    # tw.safe_delay(sus_instr2, 23, fractions.Fraction(1, 2))
    tw.safe_delay(sus_instr2, 23, fractions.Fraction(1, 4))
    tw.split(sus_instr2, 0, fractions.Fraction(1, 8))
    sus_instr2[0].pitch_or_pitches = []
    sus_instr2[1].volume = parameters.volumes.WesternVolume("mp")
    # sus_instr2[1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("14/25")
    # sus_instr0[1].pitch_or_pitches = parameters.pitches.JustIntonationPitch("14/25")
    # sus_instr0[1].pitch_or_pitches[0] += parameters.pitches.JustIntonationPitch("4/3")
    # sus_instr0[1].pitch_or_pitches[0] += parameters.pitches.JustIntonationPitch("6/5")
    # sus_instr0[1].pitch_or_pitches[0] += parameters.pitches.JustIntonationPitch("5/4")
    # sus_instr0[1].pitch_or_pitches = []
    # sus_instr2[1].pitch_or_pitches = []
    # sus_instr0[1].pitch_or_pitches[0] = parameters.pitches.JustIntonationPitch("56/75")
    sus_instr0[1].pitch_or_pitches[0] = parameters.pitches.JustIntonationPitch(
        "14/25"
    ) + parameters.pitches.JustIntonationPitch("3/2")
    sus_instr2[1].pitch_or_pitches[0] = parameters.pitches.JustIntonationPitch("14/25")
    # sus_instr0[1].pitch_or_pitches[0] += parameters.pitches.JustIntonationPitch("16/15")
    # sus_instr2[1].pitch_or_pitches[0] += parameters.pitches.JustIntonationPitch("16/15")
    # sus_instr2[1].pitch_or_pitches[0] -= parameters.pitches.JustIntonationPitch("3/2")
    sus_instr2[4].pitch_or_pitches = parameters.pitches.JustIntonationPitch("1/1")
    tw.split(sus_instr2, 3, fractions.Fraction(1, 6), fractions.Fraction(1, 6))
    sus_instr2[3].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("7/10")]
    sus_instr2[4].pitch_or_pitches = [
        parameters.pitches.JustIntonationPitch("7/10")
        + parameters.pitches.JustIntonationPitch("9/8")
    ]
    # tw.shorten(sus_instr2, 7, fractions.Fraction(1, 4), False)
    # tw.split(sus_instr2, 8, fractions.Fraction(1, 6), fractions.Fraction(1, 6), fractions.Fraction(1, 6))
    # sus_instr2[10].pitch_or_pitches = parameters.pitches.JustIntonationPitch('2/3')
    # sus_instr2[8].pitch_or_pitches = []
    tw.shorten(sus_instr2, 7, fractions.Fraction(1, 8), False)
    tw.split(sus_instr2, 8, fractions.Fraction(1, 8), fractions.Fraction(1, 8))
    sus_instr2[9].pitch_or_pitches = parameters.pitches.JustIntonationPitch("2/3")

    right_hand[0].duration += duration_of_rest_in_bar_0
    tw.eat(right_hand, 1, 1)
    right_hand[1].duration += duration_of_rest_in_bar_1
    right_hand[4].duration += duration_of_rest_in_bar_3
    tw.eat(right_hand, 4, 4)
    tw.eat(right_hand, 28, 13)
    lower_octave_range = (0, 28)
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
    right_hand.mutate_parameter(
        "notation_indicators",
        lambda notation_indicators: setattr(notation_indicators.ottava, "n_octaves", 0),
    )
    tw.eat(right_hand, 0)

    left_hand[0] = events.music.NoteLike(
        [
            # parameters.pitches.JustIntonationPitch("7/25"),
            # parameters.pitches.JustIntonationPitch("14/40"),
            # LAST VERSION BELOW
            parameters.pitches.JustIntonationPitch("14/25"),
            parameters.pitches.JustIntonationPitch("14/25")
            - parameters.pitches.JustIntonationPitch("4/3"),
            # parameters.pitches.JustIntonationPitch("7/20"),
            # parameters.pitches.JustIntonationPitch("7/20")
            # + parameters.pitches.JustIntonationPitch("5/4"),
        ],
        left_hand[0].duration,
    )
    left_hand[0].duration += duration_of_rest_in_bar_0
    tw.eat(left_hand, 0)
    tw.split(
        left_hand,
        0,
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
        fractions.Fraction(1, 2),
    )
    left_hand[0].pitch_or_pitches = []
    # alternative last interval for left hand
    # left_hand[3].pitch_or_pitches = [
    #     parameters.pitches.JustIntonationPitch("7/20"),
    #     parameters.pitches.JustIntonationPitch("7/20")
    #     + parameters.pitches.JustIntonationPitch("3/2"),
    # ]
    tw.eat(left_hand, 4, 3)
    left_hand[4] = events.music.NoteLike(
        [
            # parameters.pitches.JustIntonationPitch("1/4"),
            # parameters.pitches.JustIntonationPitch("1/5"),
            parameters.pitches.JustIntonationPitch("1/2"),
            parameters.pitches.JustIntonationPitch("2/5"),
        ],
        left_hand[4].duration,
        left_hand[1].volume,
    )
    left_hand[4].duration += duration_of_rest_in_bar_1
    tw.split(left_hand, 4, fractions.Fraction(1, 2), fractions.Fraction(1, 2))
    left_hand[4].pitch_or_pitches = []
    left_hand[12].duration += duration_of_rest_in_bar_3
    tw.eat(left_hand, 12, 1)
    left_hand[12] = events.music.NoteLike(
        [
            # parameters.pitches.JustIntonationPitch("5/11"),
            # parameters.pitches.JustIntonationPitch("2/11"),
        ],
        left_hand[12].duration,
        left_hand[11].volume,
    )
    tw.split(left_hand, 12, fractions.Fraction(1, 4), fractions.Fraction(1, 2))
    left_hand[12].pitch_or_pitches = []
    tw.eat(left_hand, 11, 2)
    for a, b in ((7, 25),):
        left_hand[a:b].set_parameter(
            "pitch_or_pitches",
            lambda pitch_or_pitches: [
                pitch - parameters.pitches.JustIntonationPitch("2/1")
                for pitch in pitch_or_pitches
            ]
            if pitch_or_pitches
            else pitch_or_pitches,
            False,
        )
    left_hand[:7].set_parameter("volume", parameters.volumes.WesternVolume("pp"))

    tw.split(left_hand, 32, fractions.Fraction(1, 8))
    left_hand[33].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("49/128")]
    left_hand[34].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("7/16")]
    tw.split(left_hand, 27, fractions.Fraction(1, 4))
    left_hand[28].pitch_or_pitches = copy.deepcopy(left_hand[30].pitch_or_pitches[0])
    tw.split(
        left_hand,
        31,
        fractions.Fraction(3, 16),
        fractions.Fraction(1, 16),
        fractions.Fraction(1, 8),
    )
    left_hand[32].pitch_or_pitches = copy.deepcopy(left_hand[37].pitch_or_pitches[0])
    left_hand[33].pitch_or_pitches = copy.deepcopy(left_hand[36].pitch_or_pitches[0])
    left_hand[34].pitch_or_pitches = copy.deepcopy(left_hand[37].pitch_or_pitches[0])
    right_hand[27:29] = left_hand[27:39].copy()
    right_hand[27:39].set_parameter(
        "pitch_or_pitches",
        lambda pitch_or_pitches: pitch_or_pitches[0]
        + parameters.pitches.JustIntonationPitch("4/1"),
    )
    tw.split(right_hand, 35, fractions.Fraction(3, 16))
    right_hand[35].pitch_or_pitches = copy.deepcopy(right_hand[30].pitch_or_pitches[0])
    right_hand[36].pitch_or_pitches = copy.deepcopy(right_hand[27].pitch_or_pitches[0])
    right_hand[37].pitch_or_pitches = copy.deepcopy(right_hand[29].pitch_or_pitches[0])
    right_hand[38].pitch_or_pitches = copy.deepcopy(right_hand[28].pitch_or_pitches[0])
    tw.split(right_hand, 38, fractions.Fraction(1, 16))
    right_hand[38].pitch_or_pitches = copy.deepcopy(right_hand[31].pitch_or_pitches[0])
    tw.split(right_hand, 37, fractions.Fraction(1, 16))
    right_hand[38].pitch_or_pitches = copy.deepcopy(right_hand[32].pitch_or_pitches[0])
    tw.split(left_hand, 35, fractions.Fraction(1, 8))
    tw.shorten(right_hand, 25, fractions.Fraction(1, 16), False)
    tw.eat(right_hand, 38)
    left_hand[35].pitch_or_pitches = [
        parameters.pitches.JustIntonationPitch("35/36")
        - parameters.pitches.JustIntonationPitch("3/1")
    ]
    left_hand[38].pitch_or_pitches = parameters.pitches.JustIntonationPitch(
        "7/16"
    ) - parameters.pitches.JustIntonationPitch("16/15")
    tw.shorten(left_hand, 11, fractions.Fraction(3, 8))
    tw.shorten(right_hand, 3, fractions.Fraction(3, 4))

    for n in (
        22,
        23,
        25,
    ):
        left_hand[n].pitch_or_pitches[0] -= parameters.pitches.JustIntonationPitch(
            "2/1"
        )

    tw.eat(left_hand, 2)
    # tw.eat(left_hand, 0)
    # left_hand[1] = copy.deepcopy(left_hand[1])
    # left_hand[1].pitch_or_pitches = sorted(left_hand[1].pitch_or_pitches)
    # left_hand[1].pitch_or_pitches[0].add(parameters.pitches.JustIntonationPitch('10/9'))
    # left_hand[1].pitch_or_pitches[1].add(parameters.pitches.JustIntonationPitch('7/8'))
    # tw.eat(left_hand, 2)
    # tw.delay(left_hand, 1, fractions.Fraction(1, 4))
    # tw.delay(left_hand, 1, fractions.Fraction(1, 8))

    keyboard.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr0.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr1.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    sus_instr2.set_parameter("volume", parameters.volumes.WesternVolume("p"))

    for tagged_simultaneous_event in tape:
        for sequential_event in tagged_simultaneous_event:
            sequential_event.get_event_at(
                fractions.Fraction(12, 4)
            ).duration += duration_of_rest_in_bar_3
            sequential_event.get_event_at(
                fractions.Fraction(4, 4)
            ).duration += duration_of_rest_in_bar_1
            sequential_event.get_event_at(
                fractions.Fraction(0, 4)
            ).duration += duration_of_rest_in_bar_0

        if tagged_simultaneous_event.tag == ot2_constants.instruments.ID_GONG:
            gong = tagged_simultaneous_event[0]
            gong[0].pitch_or_pitches[0].add(
                parameters.pitches.JustIntonationPitch("2/1")
            )
            # tw.split(gong, 0, fractions.Fraction(1, 4))
            # gong[0].pitch_or_pitches = []
            # gong[1].pitch_or_pitches = [parameters.pitches.JustIntonationPitch("7/10")]

    time_signatures = list(instruments.time_signatures)
    # time_signatures[0] = time_signature_for_bar_0
    time_signatures[0] = abjad.TimeSignature((4, 4))
    time_signatures[1] = time_signature_for_bar_1
    time_signatures[3] = time_signature_for_bar_3
    time_signatures.insert(1, abjad.TimeSignature((5, 4)))

    # start_or_start_range = 2446.923076922923 + 28
    # start_or_start_range = 2446.923076922923
    start_or_start_range = 2446.923076922923 - 20

    # REMOVING A LOT OF BARS! crazy stuff happening here
    from_ts = 10
    too_long = sum(
        map(lambda ts: fractions.Fraction(ts.duration), time_signatures[from_ts:])
    ) + fractions.Fraction(4, 4)
    del time_signatures[9:]
    time_signatures[-1] = abjad.TimeSignature((8, 4))
    time_signatures.append(abjad.TimeSignature((4, 4)))
    for time_bracket in time_brackets_to_post_process:
        for tagged_simultaneous_event in time_bracket:
            for sequential_event in tagged_simultaneous_event:
                duration = sequential_event.duration
                sequential_event.cut_off(duration - too_long, duration)

    add_longer_cadenza(time_brackets_to_post_process, time_signatures)

    tw.shorten(sus_instr0, 31, fractions.Fraction(1, 8))
    tw.shorten(sus_instr1, 26, fractions.Fraction(1, 8))
    tw.shorten(sus_instr2, 31, fractions.Fraction(1, 8))

    add_tonality_flux(time_brackets_to_post_process, time_signatures)

    end_duration = sus_instr0.duration
    time_span_in_seconds = instruments.duration
    duration_difference_factor = end_duration / start_duration
    new_time_span_in_seconds = (
        time_span_in_seconds * duration_difference_factor * factor_between_tempo
    )
    new_end_value = start_or_start_range + new_time_span_in_seconds

    tape.start_or_start_range = start_or_start_range
    tape.time_signatures = tuple(time_signatures)
    tape.end_or_end_range = new_end_value
    tape.tempo = new_tempo

    instruments.start_or_start_range = start_or_start_range
    instruments.time_signatures = tuple(time_signatures)
    instruments.end_or_end_range = new_end_value
    instruments.tempo = new_tempo

    tw.add_cent_deviation_to_sequential_event(sus_instr0)
    tw.add_cent_deviation_to_sequential_event(sus_instr1)
    tw.add_cent_deviation_to_sequential_event(sus_instr2)

    tw.update_sine_tone_events_of_tape_time_bracket(instruments, tape)

    return time_brackets_to_post_process
