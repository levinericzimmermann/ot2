import expenvelope

from mutwo.generators import generic
from mutwo.generators import koenig

PAUSE_DURATION_BETWEEN_PHRASES_DECIDER = generic.DynamicChoice(
    # the first element: make no pause,
    # the second element: the pause duration
    (
        0,
        koenig.Tendency(
            # min duration of pauses
            expenvelope.Envelope.from_points((0, 2), (1, 2)),
            # max duration of pauses
            expenvelope.Envelope.from_points((0, 5), (1, 5)),
        ),
    ),
    # the first element: likelihood for no pause,
    # the second element: likelihood for pause
    (
        expenvelope.Envelope.from_points((0, 0), (1, 0)),
        expenvelope.Envelope.from_points((0, 0.5), (1, 0.5)),
    ),
)
