import fractions

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches


def load_melody(path: str) -> basic.SequentialEvent[music.NoteLike]:
    import music21

    m21_melody = music21.converter.parse(path)[1].getElementsByClass("Measure")
    mutwo_melody = basic.SequentialEvent([])
    for bar in m21_melody:
        for event in bar:
            if isinstance(event, music21.note.GeneralNote):
                event_duration = fractions.Fraction(event.duration.quarterLength) / 4

                if event.isRest:
                    mutwo_pitches = []

                else:
                    mutwo_pitches = [
                        pitches.WesternPitch(
                            event.pitch.name.lower().replace("#", "s"),
                            octave=event.pitch.octave,
                        )
                    ]

                mutwo_event = music.NoteLike(mutwo_pitches, event_duration)
                mutwo_melody.append(mutwo_event)

    return mutwo_melody


BRAHMS0 = load_melody("ot2/analysis/data/brahms0.mxl")
BRAHMS1 = load_melody("ot2/analysis/data/brahms1.mxl")
