import expenvelope

from mutwo import generators
from mutwo import parameters

from ot2 import constants
from ot2.converters import symmetrical as ot2_symmetrical
from ot2.parameters import ambitus


def _make_pillow_choice(
    instrument_id: str, seed: int
) -> generators.generic.DynamicChoice:
    # equal for all four different voices, only change the seed when copying
    dynamic_choice = generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToPillowChordConverter(
                instrument_id,
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("3/2"),
                    parameters.pitches.JustIntonationPitch("7/1"),
                ),
                minimal_overlapping_percentage=0.12,
            ),
            ot2_symmetrical.time_brackets.StartTimeToPillowChordConverter(
                instrument_id,
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("2/1"),
                    parameters.pitches.JustIntonationPitch("8/1"),
                ),
                minimal_overlapping_percentage=0.02,
                n_pitches_cycle=(4, 3, 3, 4, 2, 4, 1),
            ),
            ot2_symmetrical.time_brackets.StartTimeToPillowChordConverter(
                instrument_id,
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("3/1"),
                    parameters.pitches.JustIntonationPitch("16/1"),
                ),
                minimal_overlapping_percentage=0.02,
                n_pitches_cycle=(4, 3, 3, 4, 2, 4, 1),
            ),
        ),
        (
            expenvelope.Envelope.from_points((0, 0.7), (1, 0.7)),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.23, 0),
                (0.25, 0.9),
                (0.32, 1.5),
                (0.35, 1.2),
                (0.41, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.64, 1),
                (0.645, 0),
                (0.65, 0),
                (0.66, 0.3),
                (0.7, 0.3),
                (0.75, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.65, 0),
                (0.66, 1),
                (0.7, 1),
                (0.75, 0),
            ),
        ),
        random_seed=seed,
    )
    return dynamic_choice


INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY = {
    constants.instruments.ID_SUS0: generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToCalligraphicLineConverter(
                constants.instruments.ID_SUS0,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToMelodicPhraseConverter(
                constants.instruments.ID_SUS0,
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
                constants.instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
            ),
            ot2_symmetrical.time_brackets.StartTimeToInstrumentalNoiseConverter(
                constants.instruments.ID_SUS0,
            ),
        ),
        (
            expenvelope.Envelope.from_points(
                (0, 0.7), (0.22, 0.7), (0.23, 0.4), (0.3, 0.4), (1, 0.7)
            ),
            expenvelope.Envelope.from_points(
                (0, 0.35),
                (0.13, 0.3),
                (0.14, 0),
                (0.22, 0),
                (0.23, 0.4),
                (0.25, 0.9),
                (0.3, 1.3),
                (0.34, 1.3),
                (0.38, 0.8),
                (0.39, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.52, 1),
                (0.525, 0),
                (1, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.04, 0.05),
                (0.11, 0.3),
                (0.15, 0),
                (0.24, 0),
                (0.29, 0.3),
                (0.36, 0.3),
                (0.37, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.5185, 1),
                (0.53, 0),
                (1, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.09, 0),
                (0.15, 0.03),
                (0.2, 0),
                (0.3, 0),
                (0.37, 0),
                (0.384, 0.28),
                (0.415, 0.27),
                (0.425, 0),
                (0.53, 0),
                (0.545, 0.4),
                (0.57, 1),
                (0.6, 0.4),
                (0.622, 0),
                (1, 0),
            ),
        ),
        random_seed=10,
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
            expenvelope.Envelope.from_points(
                (0, 0.7), (0.22, 0.7), (0.23, 0.4), (0.35, 0.3), (1, 0.7)
            ),
            expenvelope.Envelope.from_points(
                (0, 0.35),
                (0.13, 0.3),
                (0.15, 0),
                (0.22, 0),
                (0.23, 0.4),
                (0.29, 0.9),
                (0.34, 0.8),
                (0.36, 0.8),
                (0.39, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.52, 1),
                (0.525, 0),
                (1, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.09, 0.3),
                (0.12, 0.2),
                (0.15, 0),
                (0.22, 0),
                (0.23, 0.3),
                (0.28, 0.5),
                (0.31, 1.1),
                (0.34, 0.8),
                (0.36, 1.2),
                (0.38, 0.9),
                (0.4, 0.8),
                (0.41, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.52, 1),
                (0.54, 0),
                (1, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.2, 0),
                # (0.27, 0),
                # (0.29, 0.6),
                # (0.3, 0.4),
                (0.31, 0),
                (0.4, 0),
                (0.415, 0.27),
                (0.425, 0),
                (0.53, 0),
                (0.545, 0.4),
                (0.565, 1),
                (0.6, 0.2),
                (0.615, 0),
                (1, 0),
            ),
        ),
        random_seed=70,
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
            expenvelope.Envelope.from_points(
                (0, 0.7), (0.21, 0.7), (0.23, 0.4), (0.3, 0.3), (0.32, 0.4), (1, 0.7)
            ),
            expenvelope.Envelope.from_points(
                (0, 0.35),
                (0.11, 0.3),
                (0.14, 0),
                (0.23, 0),
                (0.24, 0.4),
                (0.29, 0.8),
                (0.34, 1.2),
                (0.36, 0.8),
                (0.37, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.52, 1),
                (0.535, 0),
                (1, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.06, 0),
                (0.09, 0.1),
                (0.11, 0.3),
                (0.15, 0),
                (0.23, 0),
                (0.24, 0.1),
                (0.33, 0.8),
                (0.34, 0.8),
                (0.36, 0.8),
                (0.39, 0),
                (0.46, 0),
                (0.47, 1.2),
                (0.52, 1),
                (0.535, 0),
                (1, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                # (0.27, 0),
                # (0.28, 0.5),
                (0.3, 0),
                (0.37, 0),
                (0.3825, 0.27),
                (0.415, 0.27),
                (0.425, 0),
                (0.53, 0),
                (0.545, 0.4),
                (0.57, 1),
                (0.617, 0),
                (1, 0),
            ),
        ),
        random_seed=100,
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
            ot2_symmetrical.time_brackets.StartTimeToChordConverter(
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/1"),
                    parameters.pitches.JustIntonationPitch("3/2"),
                ),
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/4"),
                    parameters.pitches.JustIntonationPitch("1/2"),
                ),
            ),
            ot2_symmetrical.time_brackets.StartTimeToChordConverter(
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("3/4"),
                    parameters.pitches.JustIntonationPitch("3/2"),
                ),
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/4"),
                    parameters.pitches.JustIntonationPitch("1/2"),
                ),
                delay_cycle=((False, False),),
                n_pitches_cycle=((1, 2), (2, 1), (1, 1)),
            ),
            ot2_symmetrical.time_brackets.StartTimeToTremoloConverter(
                constants.families_pitch.FAMILY_PITCH,
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("3/1"),
                    parameters.pitches.JustIntonationPitch("10/1"),
                ),
            ),
        ),
        (
            expenvelope.Envelope.from_points(
                (0, 0.6),
                (0.11, 0.6),
                (0.13, 0.6),
                (0.14, 1),
                (0.15, 0.12),
                (0.16, 0),
                (0.17, 0),
                (0.175, 0.01),
                (0.24, 0.01),
                (0.25, 0.6),
                (0.29, 0.6),
                (0.32, 0.4),
                (1, 0.6),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.4 / 43, 0.45),
                (0.14, 0.45),
                (0.15, 1),
                (0.2, 0.7),
                (0.24, 0.2),
                (0.28, 0),
                (0.4, 0),
                (0.46, 0),
                (0.47, 0.8),
                (0.61, 0.8),
                (0.615, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.10, 0),
                (0.12, 0.3),
                (0.16, 0.4),
                (0.20, 0.3),
                (0.2185, 0.2),
                (0.23, 0),
                (0.24, 0),
                (0.4, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.20, 0),
                (0.23, 0.5),
                (0.25, 0.6),
                (0.3, 0.6),
                (0.33, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.25, 0),
                (0.3, 0.7),
                (0.32, 1),
                (0.34, 1.2),
                (0.37, 1),
                (0.41, 0),
            ),
        ),
    ),
    constants.instruments.ID_GONG: generators.generic.DynamicChoice(
        (
            None,
            ot2_symmetrical.time_brackets.StartTimeToCalligraphicGongLineConverter(
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/5"),
                    parameters.pitches.JustIntonationPitch("1/2"),
                ),
                constants.families_pitch.FAMILY_PITCH,
                0.7,
                dynamic_cycle=("pp", "ppp", "pp"),
            ),
            ot2_symmetrical.time_brackets.StartTimeToCalligraphicGongLineConverter(
                ambitus.Ambitus(
                    parameters.pitches.JustIntonationPitch("1/4"),
                    parameters.pitches.JustIntonationPitch("1/2"),
                ),
                constants.families_pitch.FAMILY_PITCH,
                0,
                duration_cycle=(8, 10, 7, 5, 11, 15),
            ),
        ),
        (
            expenvelope.Envelope.from_points(
                (0, 0.7), (0.55, 0.7), (0.6, 0.4), (0.62, 0.4), (0.65, 0.7), (1, 0.7)
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.02, 0.4),
                (0.08, 0),
            ),
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.47, 0),
                (0.53, 0.2),
                (0.6, 0.4),
                (0.62, 0.3),
                (0.65, 0.2),
                (0.665, 0.5),
                (0.7, 0.6),
                (0.76, 0.7),
                (0.78, 0),
                (1, 0),
            ),
        ),
        random_seed=41203020,
    ),
}

for instrument_id, seed in zip(
    constants.instruments.PILLOW_IDS, (1000, 200000, 30000000, 500000000)
):
    INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY.update(
        {instrument_id: _make_pillow_choice(instrument_id, seed)}
    )
