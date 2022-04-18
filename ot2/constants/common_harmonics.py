import expenvelope

from mutwo import generators

MINIMA_PARTIAL_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 1), (0.5, 1), (0.8, 0)),
    expenvelope.Envelope.from_points((0, 2), (0.5, 2), (0.8, 1)),
)
MAXIMA_PARTIAL_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 3), (0.1, 4), (0.2, 18), (0.65, 18), (0.8, 1.9)
    ),
    expenvelope.Envelope.from_points((0, 4), (0.1, 8), (0.2, 21), (0.65, 20), (0.8, 2)),
)

LOWER_FREQUENCY_BORDER = 450
UPPER_FREQUENCY_BORDER = 20000
