import abjad

import quicktions as fractions

from mutwo import converters

from mutwo import parameters

from ot2 import converters as ot2_converters
from ot2 import constants as ot2_constants
from ot2 import tweaks as tw


def post_process_cengkok_5(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ]
):
    # few seconds later to increase the rest between the pop samples
    # and the start of the cantus firmus
    for time_bracket in time_brackets_to_post_process:
        time_bracket.delay(3)
    time_brackets_to_post_process[0][0][0][
        -2
    ].duration += time_brackets_to_post_process[0][0][0][-1].duration
    del time_brackets_to_post_process[0][0][0][-1]
    for hand in time_brackets_to_post_process[0][1]:
        for pitch in hand[-1].pitch_or_pitches:
            pitch.add(parameters.pitches.JustIntonationPitch("2/1"))

    added_part = f"""
${ot2_constants.instruments.ID_SUS0}
r`5/2
7++3-:0`3/2*mp
11-7+3-:-1`5/4 5+11+3--`4
11-3--`1
5+3--`1 r`2
11-5+3-`5/4
11-`2
3-`3/4
7+3-5-`3/2
7++3-:0`3/1

${ot2_constants.instruments.ID_KEYBOARD}0
r`2/1
7+3-`1*mf
7+3-:-1`3/2 7++3-`2
11-3-:-2`2 11-7+3-`4 5+11+3--`4
3--`3 3--11-`3 5+3--`6 3--`6
5+3-`2/1
11-3-`2
1:-1`2
3-5-`1
7+3-`2/1
7+3-:0`2/1

${ot2_constants.instruments.ID_KEYBOARD}1
r`2/1
7+3-:-1`1*mf
7+3-:-2`2/1
r`2 11-3+:-1`2
3--:-2`1
5+3-`2/1
11-3-`2
1:-2`2
3-5-`1
7+3-`2/1
7+3-:-3`2/1
"""
    time_signatures = tuple(
        abjad.TimeSignature(ts)
        for ts in (
            (8, 4),
            (4, 4),
            (8, 4),
            (4, 4),
            (4, 4),
            (8, 4),
            (2, 4),
            (2, 4),
            (4, 4),
            (8, 4),
            (8, 4),
        )
    )
    convertered_mmml_part = MMML_CONVERTER.convert(added_part)

    time_brackets_to_post_process[0][0][0].extend(
        convertered_mmml_part[ot2_constants.instruments.ID_SUS0]
    )
    time_brackets_to_post_process[0][1][0].extend(
        convertered_mmml_part[f"{ot2_constants.instruments.ID_KEYBOARD}0"]
    )
    time_brackets_to_post_process[0][1][1].extend(
        convertered_mmml_part[f"{ot2_constants.instruments.ID_KEYBOARD}1"]
    )

    time_brackets_to_post_process[0].end_or_end_range += (
        converters.symmetrical.tempos.TempoPointConverter().convert(
            time_brackets_to_post_process[0].tempo
        )
        * convertered_mmml_part[ot2_constants.instruments.ID_SUS0].duration
        * 4
    )
    time_brackets_to_post_process[0].time_signatures += time_signatures

    return time_brackets_to_post_process
