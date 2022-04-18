import expenvelope
import ranges

from mutwo import generators

# ################################################ #
#                    DURATION                      #
# ################################################ #


PIANO_CHORDS_DURATION_CHOICES = generators.generic.DynamicChoice(
    [10, 15, 25, 30, 35],
    [
        expenvelope.Envelope.from_points(
            (0, 0.5), (0.14, 0.5), (0.15, 0), (0.25, 0), (0.26, 0.5)
        ),
        expenvelope.Envelope.from_points(
            (0, 0.5), (0.14, 0.5), (0.15, 0), (0.25, 0), (0.26, 0.5)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.13, 0), (0.15, 1), (0.25, 1), (0.26, 0)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.13, 0), (0.15, 1), (0.25, 1), (0.26, 0)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.13, 0), (0.15, 1), (0.25, 1), (0.26, 0)
        ),
    ],
)

# ################################################ #
#                    DYNAMIC                       #
# ################################################ #

CALLIGRAPHIC_LINE_DYNAMIC_CHOICES = generators.generic.DynamicChoice(
    ["ppp", "pp", "p", "mp", "mf"],
    [
        expenvelope.Envelope.from_points((0, 0.5), (0.2, 0.5), (0.3, 0), (0.32, 0)),
        expenvelope.Envelope.from_points(
            (0, 0.5),
            (0.25, 0.5),
            (0.26, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0.1), (0.25, 0.3), (0.27, 0.6), (0.3, 0.7), (0.5, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.26, 0), (0.27, 0.4), (0.3, 0.5), (0.32, 0), (0.5, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.26, 0),
        ),
    ],
)

MELODIC_PHRASE_DYNAMIC_CHOICES = generators.generic.DynamicChoice(
    ["ppp", "pp", "p", "mp", "mf"],
    [
        expenvelope.Envelope.from_points((0, 0.5), (0.2, 0.5), (0.3, 0), (0.32, 0)),
        expenvelope.Envelope.from_points(
            (0, 0.5),
            (0.25, 0.5),
            (0.26, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0.1), (0.25, 0.3), (0.27, 0.6), (0.3, 0.7), (0.5, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.26, 0), (0.27, 0.4), (0.3, 0.5), (0.32, 0), (0.5, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.26, 0),
        ),
    ],
)

PIANO_CHORDS_DYNAMIC_CHOICES = generators.generic.DynamicChoice(
    ["ppp", "pp", "p", "mp", "mf"],
    [
        expenvelope.Envelope.from_points((0, 0.5), (0.25, 0.8), (0.3, 0.2), (0.5, 0.1)),
        expenvelope.Envelope.from_points((0, 0.5), (0.25, 0.8), (0.3, 0.2), (0.5, 0.1)),
        expenvelope.Envelope.from_points(
            (0, 0.1), (0.25, 0.3), (0.27, 0), (0.3, 0.1), (0.5, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.26, 0), (0.27, 0.1), (0.3, 0.2), (0.5, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.26, 0),
        ),
    ],
)

# ################################################ #
#                other timebrackets                #
# ################################################ #


NOISE_PRESENCE_CHOICES = generators.generic.DynamicChoice(
    [0, 1, 2],
    [
        expenvelope.Envelope.from_points(
            (0, 0.5),
            (0.25, 0.8),
            (0.3, 0.2),
            (0.365, 0),
            (0.38, 1),
            (0.41, 1),
            (0.42, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.25, 0.1),
            (0.3, 0.4),
            (0.37, 0.3),
            (0.41, 0.3),
            (0.42, 0),
            (0.51, 0),
            (0.52, 0.8),
            (0.62, 0.9),
            (0.63, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.25, 0),
            (0.3, 0),
            (0.35, 0),
            (0.4, 0),
            (0.41, 0),
            (0.51, 0),
            (0.52, 0.35),
            (0.62, 0.35),
            (0.63, 0),
        ),
    ],
)

NOISE_DENSITY_CHOICES = generators.generic.DynamicChoice(
    [0, 1, 2, 3],
    [
        expenvelope.Envelope.from_points(
            (0, 0.5), (0.23, 0), (0.25, 0.5), (0.3, 0.6), (0.32, 0), (0.5, 0)
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.23, 0),
            (0.25, 0.5),
            (0.3, 0.7),
            (0.32, 0),
            (0.51, 0),
            (0.52, 0.32),
            (0.62, 0.32),
            (0.63, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.23, 0),
            (0.25, 0),
            (0.29, 0),
            (0.3, 0),
            (0.51, 0),
            (0.52, 0.25),
            (0.62, 0.24),
            (0.63, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.35, 0),
            (0.365, 0),
            (0.38, 1),
            (0.41, 1),
            (0.42, 0),
            (0.51, 0),
            (0.52, 0.3),
            (0.62, 0.3),
            (0.63, 0),
        ),
    ],
)


N_PAIRS_FOR_PIANO_CHORDS_CHOICES = generators.generic.DynamicChoice(
    [1, 2, 3, 4],
    [
        expenvelope.Envelope.from_points(
            (0, 0.5),
            (0.14, 0.5),
            (0.15, 0),
            (0.25, 0),
            (0.26, 0.5),
            (0.46, 0),
            (0.47, 0.8),
            (0.64, 0.8),
            (0.65, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.14, 0),
            (0.15, 0),
            (0.25, 0),
            (0.46, 0),
            (0.47, 0.4),
            (0.64, 0.4),
            (0.65, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.13, 0), (0.15, 1), (0.25, 1), (0.26, 0)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.13, 0), (0.15, 1), (0.25, 1), (0.26, 0)
        ),
    ],
)


# ################################################ #
#                   drone                          #
# ################################################ #


DRONE_REGISTER_RANGE_DICT = ranges.RangeDict(
    {
        ranges.Range(0, 0.25): -2,
        ranges.Range(0.25, 0.375): -1,
        ranges.Range(0.375, 1): -2,
    }
)

DRONE_REGISTER_CHOICE = generators.generic.DynamicChoice(
    (-3, -2, -1, 0),
    [
        expenvelope.Envelope.from_points(
            (0, 0.5),
            (0.25, 0.7),
            (0.26, 0),
            (0.375, 0),
            (0.38, 0.5),
            (1, 0.5),
        ),
        expenvelope.Envelope.from_points(
            (0, 1),
            (0.25, 1),
            (0.26, 0.4),
            (0.375, 0.4),
            (0.38, 1),
            (1, 1),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.25, 0),
            (0.26, 1),
            (0.375, 1),
            (0.38, 0),
            (1, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.25, 0),
            (0.26, 0.1),
            (0.375, 0.1),
            (0.38, 0),
            (1, 0),
        ),
    ],
)

DRONE_PLAY_ISLAND_CHOICE = generators.generic.DynamicChoice(
    [False, True],
    [
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.6, 0),
            (0.61, 1),
            (1, 1),
        ),
        expenvelope.Envelope.from_points(
            (0, 1),
            (0.6, 1),
            (0.61, 0),
        ),
    ],
)

DRONE_DENSITY_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 0.75), (0.325, 0.75), (0.375, 0.25), (0.4, 0.75), (1, 0.75)
    ),
    expenvelope.Envelope.from_points((0, 1), (0.33, 1), (0.375, 0.5), (0.4, 1), (1, 1)),
    random_seed=123,
)
