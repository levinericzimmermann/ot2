import fractions

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.analysis import cantus_firmus_constants


def _tie_rests(sequential_event: basic.SequentialEvent):
    new_sequential_event = []
    for nth_event, event in enumerate(sequential_event):
        if nth_event != 0:
            tests = (
                len(event.pitch_or_pitches) == 0,
                len(new_sequential_event[-1].pitch_or_pitches) == 0,
            )

            if all(tests):
                new_sequential_event[-1].duration += event.duration
            else:
                new_sequential_event.append(event)
        else:
            new_sequential_event.append(event)
    return basic.SequentialEvent(new_sequential_event)


def load_cantus_firmus():
    import music21

    m21_lasso_measures = music21.converter.parse(
        "ot2/analysis/data/lasso_cantus_firmus.mxl"
    )[1].getElementsByClass("Measure")
    mutwo_lasso = basic.SequentialEvent([])

    current_root_pitch = None
    previous_event = None
    melodic_pitch_counter = 0

    for measure in m21_lasso_measures:
        for event in measure:
            if isinstance(event, music21.note.GeneralNote):
                event_duration = fractions.Fraction(event.duration.quarterLength) / 4
                if previous_event and previous_event.isRest and not event.isRest:
                    current_root_pitch = cantus_firmus_constants.START_PITCH_TO_ROOT[
                        event.pitch.name.lower()
                    ]

                if event.isRest:
                    melodic_pitch_counter = 0
                    mutwo_lasso.append(music.NoteLike([], event_duration))
                else:
                    try:
                        ji_ratios = cantus_firmus_constants.INTERVALS[
                            melodic_pitch_counter
                        ]
                    except IndexError:
                        ji_ratios = cantus_firmus_constants.INTERVALS[-1]

                    duration_per_ratio = event_duration / len(ji_ratios)
                    for ji_ratio in ji_ratios:
                        pitch = (
                            ji_ratio
                            + current_root_pitch
                            - pitches.JustIntonationPitch("2/1")
                        )
                        note = music.NoteLike([pitch], duration_per_ratio)
                        mutwo_lasso.append(note)
                    melodic_pitch_counter += 1

                previous_event = event

    return mutwo_lasso


def illustrate_cantus_firmus(cantus_firmus: basic.SequentialEvent):
    import abjad

    from mutwo.converters.frontends import abjad as mutwo_abjad

    abjad_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
        mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
            (abjad.TimeSignature((2, 1)),)
        ),
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    )
    abjad_voice = abjad_converter.convert(_tie_rests(cantus_firmus))

    abjad.attach(
        abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), abjad_voice[0][0]
    )
    abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
    lilypond_file = abjad.LilyPondFile(
        items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
    )
    abjad.persist.as_pdf(lilypond_file, "builds/cantus_firmus.pdf")


CANTUS_FIRMUS = load_cantus_firmus()

if __name__ == "__main__":
    illustrate_cantus_firmus(CANTUS_FIRMUS)
