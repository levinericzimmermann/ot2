import fractions
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.analysis import applied_brahms
from ot2.analysis import applied_cantus_firmus


def _get_each_vanitas_melody_part(
    cantus_firmus: basic.SequentialEvent[music.NoteLike], applied_brahms_melodies
) -> typing.Dict[
    fractions.Fraction,
    typing.Tuple[
        typing.Tuple[
            typing.Tuple[pitches.JustIntonationPitch, ...],
            fractions.Fraction,
            typing.Optional[basic.SequentialEvent[music.NoteLike]],
        ],
        ...,
    ],
]:
    """Return {start_time: (harmony, duration, brahms_melody), ...}"""
    parts = {}
    current_vanitas_melody = []
    current_start_time = None
    for absolute_time, bar in zip(cantus_firmus.absolute_times, cantus_firmus):
        if bar.pitch_or_pitches:
            if current_start_time is None:
                current_start_time = absolute_time

            brahms_melody = applied_brahms_melodies.get_event_at(
                absolute_time + fractions.Fraction(1, 4)
            )
            if len(brahms_melody) == 1:
                brahms_melody = None
            bar_data = (bar.pitch_or_pitches, bar.duration, brahms_melody)
            current_vanitas_melody.append(bar_data)

        else:
            if current_vanitas_melody:
                parts.update(
                    {
                        current_start_time
                        + fractions.Fraction(1, 4): tuple(current_vanitas_melody)
                    }
                )
                current_start_time = None
                current_vanitas_melody = []

    if current_vanitas_melody:
        parts.update({current_start_time: tuple(current_vanitas_melody)})
        current_start_time = None
        current_vanitas_melody = []

    return parts


VANITAS_MELODY_PARTS = _get_each_vanitas_melody_part(
    applied_cantus_firmus.APPLIED_CANTUS_FIRMUS, applied_brahms.APPLIED_BRAHMS_MELODIES
)
