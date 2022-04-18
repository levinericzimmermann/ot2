"""Here the time brackets for the stochastic parts get generated.

Public interaction via "main" method.
"""

import typing

import progressbar

from mutwo import events
from mutwo import generators
from mutwo import utilities

from ot2 import constants
from ot2 import stochastic_constants


def _calculate_time_brackets_for_instrument(
    time_bracket_factory: generators.generic.DynamicChoice,
    name: str = "",
    step_size: float = 5,
) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
    resulting_time_brackets = []
    start_time = 0
    print(f"\nCALCULATE {name}...")
    with progressbar.ProgressBar(
        min_value=0, max_value=constants.duration.DURATION_IN_SECONDS
    ) as bar:
        while start_time < constants.duration.DURATION_IN_SECONDS:
            absolute_position = start_time / constants.duration.DURATION_IN_SECONDS
            start_time_to_time_bracket_converter = time_bracket_factory.gamble_at(
                absolute_position
            )
            if start_time_to_time_bracket_converter:
                generated_time_brackets = start_time_to_time_bracket_converter.convert(
                    start_time
                )
                if generated_time_brackets:
                    resulting_time_brackets.extend(generated_time_brackets)
                    start_time = generated_time_brackets[0].maximum_end
            else:
                start_time += step_size

            update_value = start_time
            if update_value > constants.duration.DURATION_IN_SECONDS:
                update_value = constants.duration.DURATION_IN_SECONDS
            bar.update(update_value)

    return tuple(resulting_time_brackets)


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_SUS0}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_SUSTAINING_INSTRUMENT_0_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_sustaining0() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_SUS0
        ],
        "sus 0",
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_SUS1}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_SUSTAINING_INSTRUMENT_1_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_sustaining1() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_SUS1
        ],
        "sus 1",
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_SUS2}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_SUSTAINING_INSTRUMENT_2_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_sustaining2() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_SUS2
        ],
        "sus 2",
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_KEYBOARD}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_KEYBOARD_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_keyboard() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_KEYBOARD
        ],
        "keyboard",
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.PILLOW_IDS[0]}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_PILLOW_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_pillow0() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.PILLOW_IDS[0]
        ],
        "pillow0",
        step_size=6.34233,
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.PILLOW_IDS[1]}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_PILLOW_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_pillow1() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.PILLOW_IDS[1]
        ],
        "pillow1",
        step_size=5.12221,
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.PILLOW_IDS[2]}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_PILLOW_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_pillow2() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.PILLOW_IDS[2]
        ],
        "pillow2",
        step_size=4.8421,
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.PILLOW_IDS[3]}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_PILLOW_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_pillow3() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.PILLOW_IDS[3]
        ],
        "pillow3",
        step_size=7.3,
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_GONG}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS
    and constants.compute.COMPUTE_GONG_STOCHASTIC_PART,
)
def _calculate_time_brackets_for_gong() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_GONG
        ],
        "gong",
    )


INSTRUMENT_ID_TO_CALCULATE_TIME_BRACKETS_FUNCTION = {
    constants.instruments.ID_SUS0: _calculate_time_brackets_for_sustaining0,
    constants.instruments.ID_SUS1: _calculate_time_brackets_for_sustaining1,
    constants.instruments.ID_SUS2: _calculate_time_brackets_for_sustaining2,
    constants.instruments.ID_KEYBOARD: _calculate_time_brackets_for_keyboard,
    constants.instruments.PILLOW_IDS[0]: _calculate_time_brackets_for_pillow0,
    constants.instruments.PILLOW_IDS[1]: _calculate_time_brackets_for_pillow1,
    constants.instruments.PILLOW_IDS[2]: _calculate_time_brackets_for_pillow2,
    constants.instruments.PILLOW_IDS[3]: _calculate_time_brackets_for_pillow3,
    constants.instruments.ID_GONG: _calculate_time_brackets_for_gong,
}


def main() -> typing.Tuple[typing.Tuple[str, events.time_brackets.TimeBracket], ...]:
    collected_instrument_id_and_time_bracket_pairs = []

    for (
        instrument_id
    ) in stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY.keys():
        instrument_specific_time_brackets = (
            INSTRUMENT_ID_TO_CALCULATE_TIME_BRACKETS_FUNCTION[instrument_id]()
        )
        collected_instrument_id_and_time_bracket_pairs.extend(
            map(
                lambda bracket: (instrument_id, bracket),
                instrument_specific_time_brackets,
            )
        )

    return tuple(collected_instrument_id_and_time_bracket_pairs)
