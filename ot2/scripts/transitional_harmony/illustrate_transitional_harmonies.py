import fractions
import json

import abjad

from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

with open("ot2/scripts/transitional_harmony/solutions6.json", "r") as f:
    DATA = json.load(f)


converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
    mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter()
)
lilypond_file = abjad.LilyPondFile(includes=["ekme-heji-ref-c.ily"])
for current_pitch, previous_pitch, next_pitch, solution, harmonicity in DATA:
    movement_pitches = tuple(
        pitches.JustIntonationPitch(exponents)
        for exponents in (previous_pitch, current_pitch, next_pitch)
    )
    solution_pitches = tuple(
        pitches.JustIntonationPitch(exponents) for exponents in solution
    )

    sequential_event = basic.SequentialEvent([])
    for movement_pitch in movement_pitches:
        sequential_event.append(
            music.NoteLike(movement_pitch, fractions.Fraction(1, 3))
        )

    for solution_pitch in solution_pitches:
        sequential_event.append(
            music.NoteLike(solution_pitch, fractions.Fraction(1, 6))
        )

    voice = converter.convert(sequential_event)
    abjad.attach(
        abjad.Markup(
            "\\teeny { movement: "
            + str(' - '.join(str(pitch.ratio) for pitch in movement_pitches))
            + ", harmonicity = "
            + str(round(harmonicity, 3))
            + " }",
            direction="^",
        ),
        voice[0][0][0],
    )
    abjad.attach(
        abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), voice[0][0][0]
    )
    score = abjad.Score([abjad.Staff([voice])])
    lilypond_file.items.append(score)

abjad.persist.as_pdf(lilypond_file, "transition_harmonies.pdf")
