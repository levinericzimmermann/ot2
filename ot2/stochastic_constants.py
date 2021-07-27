import expenvelope

from mutwo import generators
from mutwo import parameters

from ot2 import constants
from ot2.converters import symmetrical as ot2_symmetrical
from ot2.parameters import ambitus


INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY = {
    constants.instruments.ID_SUS0: generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToCalligraphicLineConverter(
                constants.instruments.ID_SUS0,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToInstrumentalNoiseConverter(
                constants.instruments.ID_SUS0,
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 0.7), (1, 0.7)),
            expenvelope.Envelope.from_points((0, 0.35), (1, 0.2)),
            expenvelope.Envelope.from_points((0, 0.25), (1, 0.5)),
        ),
    ),
    constants.instruments.ID_SUS1: generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToCalligraphicLineConverter(
                constants.instruments.ID_SUS1,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToMelodicPhraseConverter(
                constants.instruments.ID_SUS1,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToInstrumentalNoiseConverter(
                constants.instruments.ID_SUS1,
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 0.7), (1, 0.7)),
            expenvelope.Envelope.from_points((0, 0.35), (1, 0.2)),
            expenvelope.Envelope.from_points((0, 0.35), (1, 0.3)),
            expenvelope.Envelope.from_points((0, 0.15), (1, 0.1)),
        ),
    ),
    constants.instruments.ID_SUS2: generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToCalligraphicLineConverter(
                constants.instruments.ID_SUS2,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToMelodicPhraseConverter(
                constants.instruments.ID_SUS2,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToInstrumentalNoiseConverter(
                constants.instruments.ID_SUS2,
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 0.7), (1, 0.7)),
            expenvelope.Envelope.from_points((0, 0.35), (1, 0.2)),
            expenvelope.Envelope.from_points((0, 0.25), (1, 0.1)),
            expenvelope.Envelope.from_points((0, 0.1), (1, 0.1)),
        ),
    ),
    constants.instruments.ID_KEYBOARD: generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToChordConverter(
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/3"),
                    parameters.pitches.JustIntonationPitch("1/1"),
                ),
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/8"),
                    parameters.pitches.JustIntonationPitch("1/3"),
                ),
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 0.6), (1, 0.6)),
            expenvelope.Envelope.from_points((0, 0), (0.4 / 50, 0.45), (1, 0.45)),
        ),
    ),
}
