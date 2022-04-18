from ot2 import converters as ot2_converters
from ot2 import constants as ot2_constants

from .c0 import post_process_cengkok_0
from .c1 import post_process_cengkok_1
from .c5 import post_process_cengkok_5
from .c8 import post_process_cengkok_8
from .c11 import post_process_cengkok_11
from .c12 import post_process_cengkok_12


NTH_CENGKOK_PART_TO_POST_PROCESS_FUNCTION = {
    0: post_process_cengkok_0,
    1: post_process_cengkok_1,
    # 4: _post_process_cengkok_4,
    5: post_process_cengkok_5,
    8: post_process_cengkok_8,
    11: post_process_cengkok_11,
    12: post_process_cengkok_12,
}


def _add_ottava_to_left_hand_keyboard(time_brackets):
    for time_bracket in time_brackets:
        if isinstance(
            time_bracket, ot2_converters.symmetrical.cengkoks.RiverCengkokTimeBracket
        ):
            for tagged_simultaneous_event in time_bracket:
                if (
                    tagged_simultaneous_event.tag
                    == ot2_constants.instruments.ID_KEYBOARD
                ):
                    for simple_event in tagged_simultaneous_event[0]:
                        if hasattr(simple_event, "notation_indicators"):
                            simple_event.notation_indicators.ottava.n_octaves = 1


def post_process_cengkok_time_brackets(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ],
    nth_part: int,
):
    _add_ottava_to_left_hand_keyboard(time_brackets_to_post_process)
    if nth_part in NTH_CENGKOK_PART_TO_POST_PROCESS_FUNCTION:
        return NTH_CENGKOK_PART_TO_POST_PROCESS_FUNCTION[nth_part](
            time_brackets_to_post_process
        )
    else:
        return time_brackets_to_post_process
