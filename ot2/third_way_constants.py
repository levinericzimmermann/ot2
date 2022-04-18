import expenvelope

from mutwo import generators

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters

TIME_BRACKET_FACTORY = generators.generic.DynamicChoice(
    (
        None,
        ot2_converters.symmetrical.third_way.StartTimeToHomophonicChordsConverter(
            ot2_constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
        ),
    ),
    (
        expenvelope.Envelope.from_points((0, 0.7), (1, 0.7)),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.38, 0),
            (0.4, 0.12),
            (0.42, 0.12),
            (0.43, 0),
            (0.47, 0),
            (0.53, 0),
            (0.55, 0.19),
            (0.58, 0.25),
            (0.61, 0.17),
            (0.65, 0),
            (0.666, 0.285),
            (0.7, 0.385),
            (0.725, 0.31),
            (0.76, 0),
        ),
    ),
    random_seed=233333333333333333,
)
