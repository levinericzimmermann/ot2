import math

import progressbar

from mutwo import events
from mutwo import utilities

from ot2 import constants
from ot2 import third_way_constants


@utilities.decorators.compute_lazy(
    "ot2/constants/.timeBracketsThirdWay.pickle",
    force_to_compute=constants.compute.COMPUTE_THE_THIRD_WAY,
)
def main() -> tuple[tuple[tuple[str, ...], events.time_brackets.TimeBracket], ...]:
    time_bracket_factory = third_way_constants.TIME_BRACKET_FACTORY
    resulting_time_brackets = []
    start_time = 0
    step_size = 5
    print("\nCALCULATE TIME BRACKETS FOR THE THIRD WAY...")
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
                    for time_bracket in generated_time_brackets:
                        instruments_ids = [
                            tagged_simultaneous_event.tag
                            for tagged_simultaneous_event in time_bracket
                        ]
                        resulting_time_brackets.append((instruments_ids, time_bracket))
                    start_time = math.ceil(generated_time_brackets[0].maximum_end / 5) * 5
            else:
                start_time += step_size

            update_value = start_time
            if update_value > constants.duration.DURATION_IN_SECONDS:
                update_value = constants.duration.DURATION_IN_SECONDS
            bar.update(update_value)

    return tuple(resulting_time_brackets)
