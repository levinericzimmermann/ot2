from mutwo import events

from ot2 import constants as ot2_constants
from ot2 import tweaks as tw


def _add_delays_to_time_brackets_container(
    time_brackets_container: events.time_brackets.TimeBracketContainer,
):
    # add initial delay (tape intro) to all time brackets
    time_brackets_container.delay(ot2_constants.initial_delay.INITIAL_DELAY)
    # after broke cantus firmus melody around minute 30
    # there is a long rest, which should be removed
    # constants.time_brackets_container.TIME_BRACKETS.delay(-65, 30.5 * 60)
    # time_brackets_container.delay(-50, 30.5 * 60)
    time_brackets_container.delay(-50, 30.5 * 60)
    # increase pause between two pillow-dominated areas
    time_brackets_container.delay(15, 26.5 * 60)
    # less distance between last long instrumental structure and last stochastic area
    # constants.time_brackets_container.TIME_BRACKETS.delay((-4.25 * 60) - 15, 33.25 * 60)
    # time_brackets_container.delay((-3.25 * 60) - 65, 33.5 * 60)
    time_brackets_container.delay((-3.15 * 60) - 15, 34.7 * 60)
    # longer pause between second cantus firmus and keyboard+noise - duo
    time_brackets_container.delay(15, 8 * 60)
    # longer pause before second cantus firmus
    time_brackets_container.delay(15, (6 * 60) + 38)
    # longer pause after first cantus firmus
    time_brackets_container.delay(30, (4 * 60) + 25)
    # longer pause between first and second island in area between first and second cantus firmus
    time_brackets_container.delay(15, (6 * 60) + 10)

    # PIANO CHORDS PART
    time_brackets_container.delay(10, (11 * 60))
    time_brackets_container.delay(10, (10 * 60) + 15)
    # smaller rest between second cantus firmus and piano chords + noise
    # time_brackets_container.delay(-15, (9 * 60))
    time_brackets_container.delay(-20, (9 * 60))
    return time_brackets_container


def _add_delays_to_time_brackets_container_2(
    time_brackets_container: events.time_brackets.TimeBracketContainer,
):
    # increase initial delay
    time_brackets_container.delay(60)
    # make longer rest after climax / before first river
    time_brackets_container.delay(30, (30 * 60) + 19.25)
    return time_brackets_container


def _concatenate_ending_brackets(
    time_brackets_container: events.time_brackets.TimeBracketContainer,
):
    tbs0 = tuple(
        filter(
            lambda time_bracket: round(time_bracket.minimal_start) == ((35 * 60) + 57),
            time_brackets_container,
        )
    )
    tbs1 = tuple(
        filter(
            lambda time_bracket: round(time_bracket.minimal_start) == ((38 * 60) + 43),
            time_brackets_container,
        )
    )

    for tb0, tb1 in zip(tbs0, tbs1):
        for tagged_simultaneous_event0, tagged_simultaneous_event1 in zip(tb0, tb1):
            assert tagged_simultaneous_event0.tag == tagged_simultaneous_event1.tag
            for sequential_event0, sequential_event1 in zip(
                tagged_simultaneous_event0, tagged_simultaneous_event1
            ):
                sequential_event0.extend(sequential_event1.copy())
        tb0.time_signatures += tb1.time_signatures
        tb0.end_or_end_range = tb1.end_or_end_range
        del time_brackets_container._brackets[
            time_brackets_container._brackets.index(tb1)
        ]
        time_brackets_container._brackets[
            time_brackets_container._brackets.index(tb0)
        ] = tb0
    return time_brackets_container


def _postprocess_keyboard_brackets(
    time_brackets_container: events.time_brackets.TimeBracketContainer,
):
    lonely_chord = tuple(
        filter(
            lambda time_bracket: time_bracket.start_or_start_range
            == ((11 * 60) + 50, (11 * 60) + 55),
            time_brackets_container,
        )
    )[0]
    tw.eat(lonely_chord[0][1], 0, 2)
    lonely_chord.end_or_end_range = tuple(
        map(lambda time: time - 10, lonely_chord.end_or_end_range)
    )

    too_early_cord = tuple(
        filter(
            lambda time_bracket: time_bracket.start_or_start_range
            == ((2 * 60) + 15, (2 * 60) + 25),
            time_brackets_container,
        )
    )[0]
    too_early_cord.start_or_start_range = ((2 * 60) + 25, (2 * 60) + 30)
    return time_brackets_container


def post_process_time_brackets_container(
    time_brackets_container: events.time_brackets.TimeBracketContainer,
):
    time_brackets_container = _add_delays_to_time_brackets_container(
        time_brackets_container
    )
    time_brackets_container = _concatenate_ending_brackets(time_brackets_container)
    time_brackets_container = _postprocess_keyboard_brackets(time_brackets_container)
    return time_brackets_container


def post_process_time_brackets_container_2(
    time_brackets_container: events.time_brackets.TimeBracketContainer,
):
    time_brackets_container = _add_delays_to_time_brackets_container_2(
        time_brackets_container
    )
    return time_brackets_container

