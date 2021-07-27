"""Phrases distributed on the time-line.

"""

import typing

from mutwo.events import basic

from ot2.analysis import distributed_phrases_constants
from ot2.analysis import phrases


def distribute_phrases(splitted_parts: typing.Tuple[phrases.Phrases, ...]):
    distribute_phrases = basic.SequentialEvent([])
    splitted_parts_as_sequential_event = basic.SequentialEvent(basic.SequentialEvent(part) for part in splitted_parts)
    duration = splitted_parts_as_sequential_event.duration
    for absolute_time_of_phrase, phrase in zip(
        splitted_parts_as_sequential_event.absolute_times,
        splitted_parts_as_sequential_event,
    ):
        is_first = True
        for absolute_time_of_element, phrase_element in zip(
            phrase.absolute_times, phrase
        ):
            absolute_position = (
                absolute_time_of_phrase + absolute_time_of_element
            ) / duration

            pause_duration = distributed_phrases_constants.PAUSE_DURATION_BETWEEN_PHRASES_DECIDER.gamble_at(
                absolute_position
            )

            if pause_duration == 0:
                extend_to_previous = True
            else:
                pause_duration = pause_duration.value_at(absolute_position)
                extend_to_previous = False

            if is_first:
                extend_to_previous = False
                is_first = False

            if extend_to_previous:
                distribute_phrases[-1].extend(phrase_element)
            else:
                distribute_phrases.append(phrase_element)

    return distribute_phrases


DISTRIBUTED_PHRASES = distribute_phrases(phrases.SPLITTED_PARTS)
