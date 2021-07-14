"""Certain generic operations for finding pitches."""


import bisect
import operator
import typing
import warnings

from mutwo.generators import sabat_constants
from mutwo.parameters import pitches


def filter_untunable_pitches(
    pitches_to_filter: typing.Tuple[pitches.JustIntonationPitch, ...],
    sorted_available_pitches_to_choose_from: typing.Tuple[
        pitches.JustIntonationPitch, ...
    ],
    intervals_between_available_pitches_and_given_pitches: typing.Tuple[
        typing.Tuple[pitches.JustIntonationPitch, ...], ...
    ],
    maxima_difficulty: int,
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    filtered_pitches = []
    for pitch in pitches_to_filter:
        intervals = intervals_between_available_pitches_and_given_pitches[
            sorted_available_pitches_to_choose_from.index(pitch)
        ]
        if all(
            tuple(
                interval in sabat_constants.TUNEABLE_INTERVALS
                and sabat_constants.TUNEABLE_INTERVAL_TO_DIFFICULTY[interval.exponents]
                <= maxima_difficulty
                for interval in intervals
            )
        ):
            filtered_pitches.append(pitch)
    return tuple(filtered_pitches)


def sort_pitches_by_harmonicity(
    pitches_to_sort: typing.Tuple[pitches.JustIntonationPitch, ...],
    sorted_available_pitches_to_choose_from: typing.Tuple[
        pitches.JustIntonationPitch, ...
    ],
    intervals_between_available_pitches_and_given_pitches: typing.Tuple[
        typing.Tuple[pitches.JustIntonationPitch, ...], ...
    ],
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    pitch_harmonicity_pairs = []
    for pitch in pitches_to_sort:
        intervals = intervals_between_available_pitches_and_given_pitches[
            sorted_available_pitches_to_choose_from.index(pitch)
        ]
        harmonicity = sum(
            interval.harmonicity_simplified_barlow for interval in intervals
        ) / len(intervals)
        pitch_harmonicity_pairs.append((pitch, harmonicity))
    return tuple(
        map(
            operator.itemgetter(0),
            sorted(pitch_harmonicity_pairs, key=operator.itemgetter(1), reverse=True),
        )
    )


def find_next_melodic_pitch(
    previous_pitch: pitches.JustIntonationPitch,
    available_pitches_to_choose_from: typing.Tuple[pitches.JustIntonationPitch, ...],
    direction: bool,
    pitches_to_tune_to: typing.Tuple[pitches.JustIntonationPitch],
    maxima_difficulty: int = 2,
) -> pitches.JustIntonationPitch:
    """Find next pitch in a melodic context depending on the harmonic situation.

    :arg previous_pitch: The previous pitch in the melody
    :arg available_pitches_to_choose_from: All pitch candidates.
    :arg direction: 'True' for rising and 'False' for falling contour.
    :arg pitches_to_tune_to: Simultaneous pitches to which the new pitch should fit well.
    :arg maxima_difficulty: The highest allowed difficulty for tunable intervals (could
        be 0, 1 or 2). Difficulty refers to Marc Sabats listing.
    """
    sorted_available_pitches_to_choose_from = sorted(available_pitches_to_choose_from)
    intervals_between_available_pitches_and_given_pitches = tuple(
        tuple(abs(available_pitch - given_pitch) for given_pitch in pitches_to_tune_to)
        for available_pitch in sorted_available_pitches_to_choose_from
    )
    center = bisect.bisect_left(sorted_available_pitches_to_choose_from, previous_pitch)
    lower_pitches = tuple(reversed(sorted_available_pitches_to_choose_from[:center]))
    higher_pitches = sorted_available_pitches_to_choose_from[center:]
    if higher_pitches and higher_pitches[0] == previous_pitch:
        higher_pitches = higher_pitches[1:]

    if direction:
        main_pitches_to_choose_from = higher_pitches
        alternative_pitches_to_choose_from = lower_pitches
    else:
        main_pitches_to_choose_from = lower_pitches
        alternative_pitches_to_choose_from = higher_pitches

    filtered_main_pitches_to_choose_from = filter_untunable_pitches(
        main_pitches_to_choose_from,
        sorted_available_pitches_to_choose_from,
        intervals_between_available_pitches_and_given_pitches,
        maxima_difficulty,
    )

    if filtered_main_pitches_to_choose_from:
        return filtered_main_pitches_to_choose_from[0]

    filtered_alternative_pitches_to_choose_from = filter_untunable_pitches(
        alternative_pitches_to_choose_from,
        sorted_available_pitches_to_choose_from,
        intervals_between_available_pitches_and_given_pitches,
        maxima_difficulty,
    )

    if filtered_alternative_pitches_to_choose_from:
        return filtered_alternative_pitches_to_choose_from[0]

    warnings.warn("Couldn't find any pitch which is tunable to all given pitches!")

    sorted_main_pitches = sort_pitches_by_harmonicity(
        main_pitches_to_choose_from,
        sorted_available_pitches_to_choose_from,
        intervals_between_available_pitches_and_given_pitches,
    )
    if sorted_main_pitches:
        return sorted_main_pitches[0]

    sorted_alternative_pitches = sort_pitches_by_harmonicity(
        alternative_pitches_to_choose_from,
        sorted_available_pitches_to_choose_from,
        intervals_between_available_pitches_and_given_pitches,
    )
    if sorted_alternative_pitches:
        return sorted_alternative_pitches[0]

    raise NotImplementedError(
        "No pitch could be found! Is 'available_pitches_to_choose_from' empty?"
        " (available_pitches_to_choose_from = {})".format(
            available_pitches_to_choose_from
        )
    )
