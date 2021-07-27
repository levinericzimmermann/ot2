"""Divide the time line in different parts.

The complete duration get divided in different subparts. Each subpart can be
divided again in two areas:
    1. Time-Brackets-based / stochastic / free flow
    2. cengkok-based / cantus-firmus - melody / piano solo
Which parts of the analysed cantus firmus melody get played at which position
is defined in the "PHRASE_PARTS" constant.
"""

import typing
import warnings

import quicktions as fractions

from mutwo.events import basic
from mutwo.converters.symmetrical import tempos

from ot2.analysis import phrases
from ot2.constants import duration as ot2_duration
from ot2.constants import phrase_parts
from ot2.events import basic as ot2_basic


StructureType = basic.SequentialEvent[
    basic.SequentialEvent[
        typing.Union[basic.SimpleEvent, basic.SequentialEvent[phrases.PhraseEvent]]
    ]
]


def _structure_time(
    splitted_parts: typing.Tuple[phrases.Phrases, ...],
    phrase_parts: typing.Tuple[
        typing.Tuple[
            typing.Tuple[typing.Tuple[int, typing.Tuple[int, ...]], ...], float
        ],
        ...,
    ],
    duration_in_seconds: float,
) -> StructureType:
    """Make composition structure.

    Returns SequentialEvent which consist of SequentialEvents.
    Each contained SequentialEvent represent one part.
    Each part contains two sub events again.
        1. The first sub-event is only a SimpleEvent. Its duration indicates the
           duration (in seconds) of the timebracket based / stochastic / free flow area
           of this part.
        2. The second sub-event is a SequentialEvent which contains PhraseEvents.
           It represents the cengkok based area of this part.
    """

    n_parts = len(phrase_parts)
    duration_per_part_in_seconds = duration_in_seconds / n_parts
    structure = basic.SequentialEvent([])
    for nth_phrase_part, phrase_part in enumerate(phrase_parts):
        phrase_indices, tempo = phrase_part
        cengkok_based_area = ot2_basic.SequentialEventWithTempo([], tempo=tempo)
        for (
            reptition_of_cantus_firmus_index,
            phrases_of_cantus_firmus_repetition_indices,
        ) in phrase_indices:
            nth_reptition_of_cantus_firmus = splitted_parts[
                reptition_of_cantus_firmus_index
            ]
            for (
                phrase_of_cantus_firmus_repetition_index
            ) in phrases_of_cantus_firmus_repetition_indices:
                cengkok_based_area.extend(
                    nth_reptition_of_cantus_firmus[
                        phrase_of_cantus_firmus_repetition_index
                    ]
                )

        # make last tone longer if its not the complete of the phrase
        if phrase_of_cantus_firmus_repetition_index != 3:
            cengkok_based_area[-1].duration *= 2

        # change grid from 1/2 to 1/4
        cengkok_based_area = cengkok_based_area.set_parameter(
            "duration",
            lambda old_duration: old_duration * fractions.Fraction(1, 2),
            mutate=False,
        )

        duration_of_cengkok_based_area_in_seconds = (
            cengkok_based_area.duration * 4 * tempos.TempoPointConverter().convert(tempo)
        )
        cengkok_based_area.duration_in_seconds = duration_of_cengkok_based_area_in_seconds

        remaining_duration = (
            duration_per_part_in_seconds - duration_of_cengkok_based_area_in_seconds
        )

        if remaining_duration < 0:
            remaining_duration = 30
            warnings.warn(
                f"The phrase part number '{nth_phrase_part}' has a too long cengkok"
                " based area, so that there isn't any time left for the stochastic"
                " area!"
            )

        structure.append(
            basic.SequentialEvent(
                [basic.SimpleEvent(remaining_duration), cengkok_based_area]
            )
        )

    return structure


STRUCTURE: StructureType = _structure_time(
    phrases.SPLITTED_PARTS, phrase_parts.PHRASE_PARTS, ot2_duration.DURATION_IN_SECONDS
)
