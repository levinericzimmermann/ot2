import itertools
import os

import abjad

from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.converters.frontends import midi
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.constants import instruments
from ot2.constants import sabat
from ot2.generators import zimmermann
from ot2.parameters import ambitus

STRUCTURAL_PRIMES = (3, 5, 7, 11, 13)
CHORD_PRIMES = (3, 5, 7, 9, 11, 13)
N_PRIMES_PER_SYMMETRY = 4
BUILD_PATH = "scripts/chords"
DRONE_BUILD_PATH = "scripts/drones"

try:
    os.mkdir(BUILD_PATH)
except FileExistsError:
    pass

for structural_prime in STRUCTURAL_PRIMES:
    structural_path = "{}/str{}".format(BUILD_PATH, structural_prime)
    try:
        os.mkdir(structural_path)
    except FileExistsError:
        pass

    for chord_primes in itertools.combinations(CHORD_PRIMES, N_PRIMES_PER_SYMMETRY - 1):
        chord_primes_path = "{}/active{}".format(
            structural_path, str(chord_primes).replace(" ", "")
        )

        if structural_prime not in chord_primes:
            symmetrical_structure = zimmermann.SymmetricalPermutation(
                structural_prime, chord_primes
            )

            for harmony_name, harmony in symmetrical_structure.harmonies.items():
                variants_per_pitch = tuple(
                    instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.find_all_pitch_variants(
                        pitch
                    )
                    for pitch in harmony
                )

                harmony_path = "{}/h_{}".format(chord_primes_path, harmony_name)

                for (
                    nth_pitch_variant_combination,
                    pitch_variant_combination,
                ) in enumerate(itertools.product(*variants_per_pitch)):

                    intervallv = 0
                    is_addable = True
                    for p0, p1 in itertools.combinations(pitch_variant_combination, 2):
                        interval = p0 - p1
                        if interval.cents < 0:
                            interval.inverse()
                        if interval.exponents in sabat.TUNEABLE_INTERVALS:
                            intervallv += sabat.TUNEABLE_INTERVALS[interval.exponents]
                        else:
                            is_addable = False

                    if is_addable:

                        try:
                            os.mkdir(chord_primes_path)
                        except FileExistsError:
                            pass

                        try:
                            os.mkdir(harmony_path)
                        except FileExistsError:
                            pass

                        sequential_event = basic.SequentialEvent(
                            [music.NoteLike(pitch_variant_combination, 8, 0.25)]
                        )
                        pitch_variant_name = "s{}cp{}h_{}_{}_DIFF_{}".format(
                            structural_prime,
                            str(chord_primes).replace(" ", ""),
                            harmony_name,
                            nth_pitch_variant_combination,
                            intervallv,
                        )

                        midi_file_converter = midi.MidiFileConverter(
                            "{}/{}.mid".format(harmony_path, pitch_variant_name)
                        )
                        midi_file_converter.convert(sequential_event)

                        abjad_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
                            mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter()
                        )
                        abjad_voice = abjad_converter.convert(sequential_event)
                        abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
                        lilypond_file = abjad.LilyPondFile(
                            items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
                        )
                        abjad.persist.as_pdf(
                            lilypond_file,
                            "{}/{}.pdf".format(harmony_path, pitch_variant_name),
                        )

try:
    os.mkdir(DRONE_BUILD_PATH)
except FileExistsError:
    pass

DRONE_AMBITUS = ambitus.Ambitus(
    pitches.JustIntonationPitch("1/4"), pitches.JustIntonationPitch("1/2")
)

for structural_prime in (3, 5, 7, 9, 11, 13):
    for tonality in (True, False):
        if tonality:
            pitch = pitches.JustIntonationPitch("{}/1".format(structural_prime))
        else:
            pitch = pitches.JustIntonationPitch("1/{}".format(structural_prime))

        for nth_pitch_variant, pitch_variant in enumerate(
            DRONE_AMBITUS.find_all_pitch_variants(pitch)
        ):
            sequential_event = basic.SequentialEvent(
                [music.NoteLike(pitch_variant, 16, 0.2)]
            )
            midi_file_converter = midi.MidiFileConverter(
                "{}/{}_{}.mid".format(DRONE_BUILD_PATH, structural_prime, tonality)
            )
            midi_file_converter.convert(sequential_event)
