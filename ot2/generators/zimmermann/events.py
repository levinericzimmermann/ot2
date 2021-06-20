import typing

import abjad

from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.generators.zimmermann.pitches import imitations


def imitate_melody(
    melody_to_imitate: basic.SequentialEvent[music.NoteLike],
    harmony: typing.Sequence[pitches.JustIntonationPitch],
) -> basic.SequentialEvent[music.NoteLike]:
    melodic_pitches = tuple(
        pitch_or_pitches[0]
        for pitch_or_pitches in melody_to_imitate.get_parameter("pitch_or_pitches")
        if pitch_or_pitches
    )
    transformed_pitches = iter(imitations.imitate(melodic_pitches, harmony))
    imitated_melody = basic.SequentialEvent(
        [
            music.NoteLike(next(transformed_pitches), duration)
            if original_pitch
            else music.NoteLike([], duration)
            for original_pitch, duration in zip(
                melody_to_imitate.get_parameter("pitch_or_pitches"),
                melody_to_imitate.get_parameter("duration"),
            )
        ]
    )
    return imitated_melody


def illustrate_melody(
    path: str, melody_to_illustrate: basic.SequentialEvent[music.NoteLike]
):
    abjad_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    )
    abjad_voice = abjad_converter.convert(melody_to_illustrate)
    abjad.attach(
        abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), abjad_voice[0][0]
    )
    abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
    lilypond_file = abjad.LilyPondFile(
        items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
    )
    abjad.persist.as_pdf(lilypond_file, path)
