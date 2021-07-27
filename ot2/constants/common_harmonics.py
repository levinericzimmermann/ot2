import expenvelope

from mutwo import generators

MINIMA_PARTIAL_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 1), (1, 1)),
    expenvelope.Envelope.from_points((0, 2), (1, 2)),
)
MAXIMA_PARTIAL_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 18), (1, 18)),
    expenvelope.Envelope.from_points((0, 21), (1, 21)),
)

LOWER_FREQUENCY_BORDER = 600
UPPER_FREQUENCY_BORDER = 20000
