"""Here the time brackets for the stochastic parts get generated.

Public interaction via "main" method.
"""

import typing

from mutwo import events
from mutwo import generators
from mutwo import utilities

from ot2 import constants
from ot2 import stochastic_constants


def _calculate_time_brackets_for_instrument(
    time_bracket_factory: generators.generic.DynamicChoice,
) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
    resulting_time_brackets = []
    start_time = 0
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
            start_time += 5
    return tuple(resulting_time_brackets)


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_SUS0}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS,
)
def _calculate_time_brackets_for_sustaining0() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_SUS0
        ]
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_SUS1}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS,
)
def _calculate_time_brackets_for_sustaining1() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_SUS1
        ]
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_SUS2}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS,
)
def _calculate_time_brackets_for_sustaining2() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_SUS2
        ]
    )


@utilities.decorators.compute_lazy(
    f"ot2/constants/.timeBrackets{constants.instruments.ID_KEYBOARD}.pickle",
    force_to_compute=constants.compute.COMPUTE_STOCHASTIC_PARTS,
    # force_to_compute=True,
    # force_to_compute=False,
)
def _calculate_time_brackets_for_keyboard() -> typing.Tuple[
    events.time_brackets.TimeBracket, ...
]:
    return _calculate_time_brackets_for_instrument(
        stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY[
            constants.instruments.ID_KEYBOARD
        ]
    )


INSTRUMENT_ID_TO_CALCULATE_TIME_BRACKETS_FUNCTION = {
    constants.instruments.ID_SUS0: _calculate_time_brackets_for_sustaining0,
    constants.instruments.ID_SUS1: _calculate_time_brackets_for_sustaining1,
    constants.instruments.ID_SUS2: _calculate_time_brackets_for_sustaining2,
    constants.instruments.ID_KEYBOARD: _calculate_time_brackets_for_keyboard,
}


def main() -> typing.Tuple[typing.Tuple[str, events.time_brackets.TimeBracket], ...]:
    collected_instrument_id_and_time_bracket_pairs = []

    for (
        instrument_id
    ) in stochastic_constants.INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY.keys():
        instrument_specific_time_brackets = INSTRUMENT_ID_TO_CALCULATE_TIME_BRACKETS_FUNCTION[
            instrument_id
        ]()
        collected_instrument_id_and_time_bracket_pairs.extend(
            map(
                lambda bracket: (instrument_id, bracket),
                instrument_specific_time_brackets,
            )
        )

    return tuple(collected_instrument_id_and_time_bracket_pairs)
