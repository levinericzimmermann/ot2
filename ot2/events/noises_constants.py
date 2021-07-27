import itertools

from mutwo import parameters

DENSITY_RANGE = tuple(range(4))
"""0, 1 and 2 for different density levels of discreet sounds,
3 for continuous sounds."""

PRESENCE_RANGE = tuple(range(3))
"""0 for soft, 1 for present, 2 for harsh"""

DENSITY_AND_PRESENCE_TO_WESTERN_PITCH = {
    density_and_presence_pair: parameters.pitches.WesternPitch("c", -1).add(
        nth_combination, mutate=False
    )
    for nth_combination, density_and_presence_pair in enumerate(
        itertools.product(DENSITY_RANGE, PRESENCE_RANGE)
    )
}
"""Mapping for midi (SFZ) instruments."""

DENSITY_AND_PRESENCE_TO_MARKUP_COMMAND = {

}
