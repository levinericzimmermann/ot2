import itertools
import typing

from mutwo import events
from mutwo import utilities

from ot2 import constants
from ot2 import converters


@utilities.decorators.compute_lazy(
    f"ot2/constants/.commonHarmonics.pickle",
    force_to_compute=constants.compute.COMPUTE_COMMON_HARMONICS,
)
def main() -> typing.Tuple[typing.Tuple[str, events.basic.SequentialEvent], ...]:
    instrument_id_and_sequential_events = {}
    for instrument_id in (
        constants.instruments.ID_SUS0,
        constants.instruments.ID_SUS1,
        constants.instruments.ID_SUS2,
        constants.instruments.ID_KEYBOARD,
        constants.instruments.ID_DRONE,
    ):
        converter = converters.symmetrical.spectrals.TimeBracketContainerToSequentialEventsConverter(
            instrument_id
        )
        sequential_events = converter.convert(
            constants.time_brackets_container.TIME_BRACKETS
        )
        instrument_id_and_sequential_events.update({instrument_id: sequential_events})

    sequential_event_and_name_pairs = []
    for instrument_id0, instrument_id1 in itertools.combinations(
        instrument_id_and_sequential_events.keys(), 2
    ):
        for (
            index_and_sequential_event0,
            index_and_sequential_event1,
        ) in itertools.product(
            enumerate(instrument_id_and_sequential_events[instrument_id0]),
            enumerate(instrument_id_and_sequential_events[instrument_id1]),
        ):
            index0, sequential_event0 = index_and_sequential_event0
            index1, sequential_event1 = index_and_sequential_event1
            resulting_sequential_event = converters.symmetrical.spectrals.SequentialEventPairToCommonHarmonicsSequentialEvent().convert(
                (sequential_event0, sequential_event1)
            )

            name = f"{instrument_id0}_{index0}_{instrument_id1}_{index1}"
            sequential_event_and_name_pairs.append((name, resulting_sequential_event))
    return tuple(sequential_event_and_name_pairs)
