"""Apply transition harmonies on cantus firmus."""

import json

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.analysis import applied_cantus_firmus_constants
from ot2.analysis import cantus_firmus


def make_applied_cantus_firmus(
    cantus_firmus: basic.SequentialEvent,
) -> basic.SequentialEvent[music.NoteLike]:
    with open("ot2/analysis/data/transition_harmonies.json", "r") as f:
        transitional_harmonies_raw = json.load(f)

    transitional_harmonies = {}
    for (
        current_pitch,
        previous_pitch,
        next_pitch,
        solution,
        _,
    ) in transitional_harmonies_raw:
        current_pitch_as_pitch = pitches.JustIntonationPitch(current_pitch)
        previous_pitch_as_pitch = pitches.JustIntonationPitch(previous_pitch)
        next_pitch_as_pitch = pitches.JustIntonationPitch(next_pitch)
        interval0 = (previous_pitch_as_pitch - current_pitch_as_pitch).normalize(
            mutate=False
        )
        interval1 = (next_pitch_as_pitch - current_pitch_as_pitch).normalize(
            mutate=False
        )
        solution_as_pitches = tuple(
            pitches.JustIntonationPitch(pitch) for pitch in solution
        )
        transitional_harmonies.update(
            {(interval0.exponents, interval1.exponents): solution_as_pitches}
        )

    previous_pitch_or_pitches = None
    applied_cantus_firmus = basic.SequentialEvent([])
    for pitch_or_pitches, next_pitch_or_pitches, duration in zip(
        cantus_firmus.get_parameter("pitch_or_pitches"),
        cantus_firmus.get_parameter("pitch_or_pitches")[1:] + (None,),
        cantus_firmus.get_parameter("duration"),
    ):
        duration = duration * applied_cantus_firmus_constants.FACTOR
        if pitch_or_pitches:

            current_pitch = pitch_or_pitches[0]
            previous_pitch = (
                previous_pitch_or_pitches[0]
                if previous_pitch_or_pitches
                else current_pitch
            )
            next_pitch = (
                next_pitch_or_pitches[0] if next_pitch_or_pitches else current_pitch
            )
            interval0 = (
                (previous_pitch - current_pitch).normalize(mutate=False).exponents
            )
            interval1 = (next_pitch - current_pitch).normalize(mutate=False).exponents
            try:
                harmony = [
                    current_pitch + pitch
                    for pitch in transitional_harmonies[interval0, interval1]
                ]
            except KeyError:
                harmony = [current_pitch]
            event = music.NoteLike(harmony, duration)

        else:
            event = music.NoteLike([], duration)

        applied_cantus_firmus.append(event)
        previous_pitch_or_pitches = pitch_or_pitches
    return applied_cantus_firmus


def illustrate_applied_cantus_firmus(cantus_firmus: basic.SequentialEvent):
    import abjad

    from mutwo.converters.frontends import abjad as mutwo_abjad

    time_signatures = tuple(
        abjad.TimeSignature((event.duration.numerator, event.duration.denominator))
        for event in cantus_firmus
    )

    abjad_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
        mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(time_signatures),
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    )
    abjad_voice = abjad_converter.convert(cantus_firmus)

    abjad.attach(
        abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), abjad_voice[0][0]
    )
    abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
    lilypond_file = abjad.LilyPondFile(
        items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
    )
    abjad.persist.as_pdf(lilypond_file, "builds/applied_cantus_firmus.pdf")


APPLIED_CANTUS_FIRMUS = make_applied_cantus_firmus(
    cantus_firmus=cantus_firmus.CANTUS_FIRMUS
)


if __name__ == "__main__":
    illustrate_applied_cantus_firmus(APPLIED_CANTUS_FIRMUS)
