import fractions
import itertools
import operator
import typing


from mutwo import converters
from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants

from . import structure


class RestructuredPhrasePartsToBonanganConverter(converters.abc.Converter):
    ambitus = (
        ot2_constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES
    )

    instrumental_phrases = {
        1: ("1`4",),
        2: ("r`4 2`4",),
        4: (
            "r`3 2`3 1`3",
            "r`4 2`4 1`4 2`4",
            "r`4 2`4 1`3 2`6",
            "r`2 1`4 2`4",
            "r`4 2`4 1`3/8 2`8",
        ),
        8: (
            "r`4 2`4 1`4 2`4 r`2 1`4 2`4",
            "r`3 2`3 1`3 r`2 1`4 2`4",
            "r`4 2`4 1`8 2`8 1`8 2`8 r`2 1`3 2`6",
        ),
        16: ("r`4 2`4 1`4 2`4 r`2 1`4 2`4 r`4 2`4 1`4 2`4 r`2 1`4 2`4",),
    }
    sine_phrases = {
        1: ("1`4",),
        2: ("1`4 2`4", "r`8 1`8 2`4"),
        4: ("r`8 1`8 2`4 r`4 2`4", "1`4 2`4 r`4 2`4", "1`3 2`6 r`4 2`4"),
        8: (
            "1`4 2`4 r`3/4 1`2 2`4",
            "1`3 2`6 r`3/4 1`2 2`4",
        ),
        16: ("1`4 2`4 r`3/4 1`2 2`4 1`4 2`4 r`3/4 1`2 2`4",),
    }

    character_to_instrument_phrases = {
        structure.START: {
            1: ("r`4",),
            2: ("r`4 2`4",),
            4: ("r`3/4 2`4",),
            8: ("r`6/4 1`4 2`4",),
            16: ("r`13/4 1`2 2`4",),
        },
        structure.CADENZA: {
            1: ("1`4",),
            2: ("1`8 2`8 1`8 2`8",),
            4: ("r`4 2`4 1`3/16 2`16 1`8 2`8",),
            8: ("r`4 2`4 1`4 2`4 r`2 1`4 2`12 1`12 2`12",),
            16: ("r`4 2`4 1`4 2`4 r`2 1`4 2`4 r`4 2`4 1`4 2`4 r`2 1`4 2`4",),
        },
        structure.END: {
            1: ("1`4",),
            2: ("1`4 r`4",),
            4: ("1`2 r`2",),
            8: ("1`2 r`3/2",),
            16: ("r`4/1",),
        },
        structure.REST: {
            1: ("r`4",),
            2: ("r`2",),
            4: ("r`1",),
            8: ("r`2/1",),
            16: ("r`4/1",),
        },
    }

    character_to_sine_phrases = {
        structure.START: {
            1: ("r`4",),
            2: ("r`4 2`4",),
            4: ("r`2/4 1`4 2`4",),
            8: ("r`1 r`4 1`2 2`4",),
            16: ("1`4 2`4 r`3/4 1`2 2`4 1`4 2`4 r`3/4 1`2 2`4",),
        },
        structure.CADENZA: {
            1: ("1`4",),
            2: ("1`4 2`4",),
            4: ("1`4 2`4 r`4 2`4",),
            8: ("1`4 2`4 r`3/4 1`2 2`4",),
            16: ("1`4 2`4 r`3/4 1`2 2`4 1`4 2`4 r`3/4 1`2 2`4",),
        },
        structure.END: {
            1: ("r`8 1`8",),
            2: ("r`8 1`8 r`4",),
            4: ("r`8 1`3/8 r`2",),
            8: ("1`4 2`4 r`3/4 1`2 2`4",),
            16: ("1`4 2`4 r`3/4 1`2 2`4 1`4 2`4 r`3/4 1`2 2`4",),
        },
        structure.REST: {
            1: ("r`4",),
            2: ("r`2",),
            4: ("r`1",),
            8: ("r`2/1",),
            16: ("r`4/1",),
        },
    }

    preferred_octave = 1
    standard_beat_size = fractions.Fraction(1, 4)

    def __init__(self):
        self._instrumental_cycles = {
            n_beats: itertools.cycle(variants)
            for n_beats, variants in self.instrumental_phrases.items()
        }
        self._character_to_instrumental_cycles = {
            character: {
                n_beats: itertools.cycle(variants)
                for n_beats, variants in character_data.items()
            }
            for character, character_data in self.character_to_instrument_phrases.items()
        }
        self._sine_cycles = {
            n_beats: itertools.cycle(variants)
            for n_beats, variants in self.sine_phrases.items()
        }
        self._character_to_sine_cycles = {
            character: {
                n_beats: itertools.cycle(variants)
                for n_beats, variants in character_data.items()
            }
            for character, character_data in self.character_to_sine_phrases.items()
        }

    def _find_pitch_pair(
        self, phrase_part: structure.RestructuredPhrasePart
    ) -> typing.Tuple[
        parameters.pitches.JustIntonationPitch, parameters.pitches.JustIntonationPitch
    ]:
        pitch0 = phrase_part.connection_pitch0
        if not pitch0:
            pitch0 = phrase_part.root

        pitch1 = phrase_part.connection_pitch1
        if not pitch1:
            pitch1 = phrase_part.root

        if pitch1 == pitch0:
            if pitch0 != phrase_part.root:
                pitch0 = phrase_part.root
            else:
                print("HOW DID THIS HAPPEN???", self.phrase_event)
                raise NotImplementedError

        pitch0_variants = self.ambitus.find_all_pitch_variants(pitch0)
        pitch1_variants = self.ambitus.find_all_pitch_variants(pitch1)

        combinations = []
        for pitch0_variant, pitch1_variant in itertools.product(
            pitch0_variants, pitch1_variants
        ):
            interval = pitch1_variant - pitch0_variant
            distance = abs(interval.cents)
            combinations.append(((pitch0_variant, pitch1_variant), distance))

        smallest_distance = min(combinations, key=operator.itemgetter(1))[1]

        allowed_combinations = (
            combination[0]
            for combination in combinations
            if combination[1] == smallest_distance
        )
        best_allowed_combinations = max(
            allowed_combinations,
            key=lambda combination: sum(
                int(pitch.octave == self.preferred_octave) for pitch in combination
            ),
        )
        return best_allowed_combinations

    def convert(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ) -> typing.Tuple[events.basic.SequentialEvent, events.basic.SequentialEvent]:
        """First seq event for instrument, second seq event for sine tones"""

        bonangans = [events.basic.SequentialEvent([]), events.basic.SequentialEvent([])]
        for phrase_part in restructured_phrase_parts:
            n_beats = int(phrase_part.duration / self.standard_beat_size)
            pitch_pair = self._find_pitch_pair(phrase_part)
            pitch_decodex = {"1": pitch_pair[0], "2": pitch_pair[1]}
            mmml_converter = converters.backends.mmml.MMMLConverter(
                converters.backends.mmml.MMMLEventsConverter(
                    converters.backends.mmml.MMMLPitchesConverter(
                        converters.backends.mmml.MMMLSinglePitchConverter(pitch_decodex)
                    )
                )
            )

            if phrase_part.bar_character in self._character_to_instrumental_cycles:
                phrase_cycle = self._character_to_instrumental_cycles[
                    phrase_part.bar_character
                ][n_beats]
            else:
                phrase_cycle = self._instrumental_cycles[n_beats]

            instrumental_phrase = mmml_converter.convert(next(phrase_cycle))[
                "undefined"
            ]
            sine_phrase = mmml_converter.convert(next(self._sine_cycles[n_beats]))[
                "undefined"
            ]
            assert instrumental_phrase.duration == phrase_part.duration
            bonangans[0].extend(instrumental_phrase)
            bonangans[1].extend(sine_phrase)

        for bonangan in bonangans:
            bonangan.tie_by(
                lambda ev0, ev1: hasattr(ev0, "pitch_or_pitches")
                and hasattr(ev1, "pitch_or_pitches")
                and (
                    (
                        ev0.pitch_or_pitches
                        and ev1.pitch_or_pitches
                        and ev0.pitch_or_pitches[0].normalize(mutate=False)
                        == ev1.pitch_or_pitches[0].normalize(mutate=False)
                    )
                    or (ev0.pitch_or_pitches == ev1.pitch_or_pitches)
                )
            )
            bonangan.set_parameter("volume", parameters.volumes.WesternVolume("p"))

        return tuple(bonangans)
