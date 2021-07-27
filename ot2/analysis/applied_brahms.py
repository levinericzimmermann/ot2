"""Apply Brahms melodies whenever possible on applied cantus firmus."""

import fractions
import functools
import operator
import pickle
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.analysis import applied_cantus_firmus
from ot2.analysis import brahms
from ot2.generators import zimmermann


def _post_process_brahms_melody(brahms_melody: basic.SequentialEvent):
    brahms_melody.tie_by(
        lambda event0, event1: event0.pitch_or_pitches == event1.pitch_or_pitches
    )
    if min(
        functools.reduce(operator.add, brahms_melody.get_parameter("pitch_or_pitches"))
    ) > pitches.JustIntonationPitch("1/1"):
        brahms_melody.set_parameter(
            "pitch_or_pitches",
            lambda pitch_or_pitches: [
                pitch + pitches.JustIntonationPitch("1/2") for pitch in pitch_or_pitches
            ],
        )


def _make_potential_brahms_melodies(
    event: music.NoteLike,
) -> typing.Tuple[basic.SequentialEvent, ...]:
    harmony = tuple(event.pitch_or_pitches)
    if harmony and event.duration in (
        fractions.Fraction(4, 2),
        fractions.Fraction(8, 2),
    ):
        if event.duration == 2:
            used_melodies = (brahms.BRAHMS0.copy(), brahms.BRAHMS1.copy())
            used_melodies[1][4].duration = fractions.Fraction(1, 4)
            used_melodies[1][7].duration = fractions.Fraction(1, 4)
            used_melodies[0].set_parameter(
                "duration", lambda duration: duration * fractions.Fraction(2, 3)
            )
            used_melodies[1].set_parameter(
                "duration", lambda duration: duration * fractions.Fraction(2, 3)
            )
            used_melodies[0].insert(0, music.NoteLike([], fractions.Fraction(1, 4)))
            used_melodies[0][-1].duration = fractions.Fraction(1, 4)
            used_melodies[1][0].duration = fractions.Fraction(1, 4)
            used_melodies[1][-1].duration = fractions.Fraction(1, 4)
        else:
            used_melodies = (brahms.BRAHMS1.copy(),)
            used_melodies[0].insert(0, music.NoteLike([], fractions.Fraction(3, 4)))

        potential_brahms_melodies = []
        for melody_to_imitate in used_melodies:
            potential_brahms_melodies.append(
                zimmermann.events.imitate_melody(melody_to_imitate, harmony)
            )
        for potential_brahms_melody in potential_brahms_melodies:
            _post_process_brahms_melody(potential_brahms_melody)
        return tuple(potential_brahms_melodies)
    else:
        return tuple([])


def _select_from_potential_brahms_melodies(
    potential_brahms_melodies: typing.Tuple[basic.SequentialEvent, ...],
    current_bar: music.NoteLike,
    next_bar: music.NoteLike,
) -> basic.SequentialEvent[music.NoteLike]:
    pitches_per_bar0, pitches_per_bar1 = (
        set(
            map(lambda pitch: pitch.normalize(mutate=False).exponents, pitch_or_pitches)
        )
        for pitch_or_pitches in (
            current_bar.pitch_or_pitches,
            next_bar.pitch_or_pitches,
        )
    )
    common_pitches = tuple(
        pitches.JustIntonationPitch(pitch)
        for pitch in pitches_per_bar0.intersection(pitches_per_bar1)
    )
    is_last_pitch_connection_pitch_per_brahms_melody = tuple(
        brahms_melody[-1].pitch_or_pitches[0].normalize(mutate=False) in common_pitches
        for brahms_melody in potential_brahms_melodies
    )
    if any(is_last_pitch_connection_pitch_per_brahms_melody):
        nth_melody_is_possible = is_last_pitch_connection_pitch_per_brahms_melody.index(
            True
        )
        return potential_brahms_melodies[nth_melody_is_possible]
    else:
        return basic.SequentialEvent([music.NoteLike([], current_bar.duration)])


def _apply_brahms_melodies_if_possible(
    cantus_firmus: basic.SequentialEvent[music.NoteLike],
) -> basic.SequentialEvent[basic.SequentialEvent[music.NoteLike]]:
    applied_brahms_melodies = basic.SequentialEvent([])
    current_rest_duration = 0
    last_bar_had_pitches = False
    for current_bar, next_bar in zip(cantus_firmus, cantus_firmus[1:]):
        if current_bar.pitch_or_pitches:
            if current_rest_duration != 0:
                applied_brahms_melodies.append(
                    basic.SequentialEvent(
                        [
                            music.NoteLike(
                                [], current_rest_duration + fractions.Fraction(1, 4)
                            )
                        ]
                    )
                )
                current_rest_duration = 0
            potential_brahms_melodies = _make_potential_brahms_melodies(current_bar)
            applied_brahms_melodies.append(
                _select_from_potential_brahms_melodies(
                    potential_brahms_melodies, current_bar, next_bar
                )
            )
            last_bar_had_pitches = True
        else:
            if last_bar_had_pitches:
                current_rest_duration -= fractions.Fraction(1, 4)
            current_rest_duration += current_bar.duration
            last_bar_had_pitches = False

    applied_brahms_melodies.append(
        basic.SequentialEvent(
            [music.NoteLike([], next_bar.duration - fractions.Fraction(1, 4))]
        )
    )

    return applied_brahms_melodies


def _export_applied_brahms_melodies(applied_brahms_melodies: basic.SequentialEvent):
    with open(APPLIED_BRAHMS_MELODIES_PATH, "wb") as f:
        pickle.dump(applied_brahms_melodies, f)


def _import_applied_brahms_melodies():
    with open(APPLIED_BRAHMS_MELODIES_PATH, "rb") as f:
        applied_brahms_melodies = pickle.load(f)
    return applied_brahms_melodies


def illustrate_applied_brahms_melodies(applied_brahms_melodies: basic.SequentialEvent):
    applied_brahms_melodies = functools.reduce(operator.add, applied_brahms_melodies)
    import abjad

    from mutwo.converters.frontends import abjad as mutwo_abjad

    time_signatures = tuple(
        abjad.TimeSignature((int(event.duration * 2), 2))
        for event in applied_cantus_firmus.APPLIED_CANTUS_FIRMUS
    )

    abjad_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
        mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(time_signatures),
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    )
    abjad_voice = abjad_converter.convert(applied_brahms_melodies)

    abjad.attach(
        abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), abjad_voice[0][0]
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\override Staff.TimeSignature.style = #'single-digit"),
        abjad_voice[0][0],
    )
    abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
    lilypond_file = abjad.LilyPondFile(
        items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
    )
    abjad.persist.as_pdf(lilypond_file, "builds/applied_brahms_melodies.pdf")


def synthesize_applied_brahms(applied_brahms_melodies: basic.SequentialEvent):
    applied_brahms_melodies = functools.reduce(operator.add, applied_brahms_melodies)
    from mutwo.converters.frontends import midi

    converter = midi.MidiFileConverter("builds/materials/applied_brahms.mid")
    converter.convert(
        applied_brahms_melodies.set_parameter(
            "duration", lambda duration: duration * 4, mutate=False
        )
    )

APPLIED_BRAHMS_MELODIES_PATH = "ot2/analysis/data/applied_brahms_melodies.pickle"
APPLIED_BRAHMS_MELODIES = _import_applied_brahms_melodies()

if __name__ == "__main__":
    APPLIED_BRAHMS_MELODIES = _apply_brahms_melodies_if_possible(
        applied_cantus_firmus.APPLIED_CANTUS_FIRMUS
    )
    # pickle applied brahms melody (speed up loading of melodies)
    _export_applied_brahms_melodies(APPLIED_BRAHMS_MELODIES)
    illustrate_applied_brahms_melodies(APPLIED_BRAHMS_MELODIES)
    synthesize_applied_brahms(APPLIED_BRAHMS_MELODIES)
