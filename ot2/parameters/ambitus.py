import copy
import typing

from mutwo import parameters


# REMARK:
# ambitus "find_all_pitch_variants" can only handle pitches that know an
# "add" and a "subtract" method! Furthermore add needs to know something
# similar to an "octave" (how much to add via each step)


class Ambitus(object):
    def __init__(
        self, border_down: parameters.abc.Pitch, border_up: parameters.abc.Pitch
    ) -> None:
        try:
            assert border_down < border_up
        except AssertionError:
            msg = "The lower border has to be a lower pitch than the upper border!"
            raise ValueError(msg)

        self._borders = (border_down, border_up)

    # ######################################################## #
    #                       static methods                     #
    # ######################################################## #

    @staticmethod
    def _guess_period(pitch: parameters.abc.Pitch) -> typing.Any:
        if isinstance(pitch, parameters.pitches.JustIntonationPitch):
            period = parameters.pitches.JustIntonationPitch("2/1")

        elif isinstance(pitch, parameters.pitches.EqualDividedOctavePitch):
            period = pitch.n_pitch_classes_per_octave

        else:
            message = (
                "Mutwo can't guess 'period' for pitch {} of type {}! Please"
                " explicitly set a value for 'period' argument.".format(
                    pitch, type(pitch)
                )
            )
            raise NotImplementedError(message)

        return period

    # ######################################################## #
    #                     magic methods                        #
    # ######################################################## #

    def __repr__(self) -> str:
        return "Ambitus({})".format(self._borders)

    def __iter__(self) -> iter:
        return iter(self._borders)

    def __getitem__(self, idx: int):
        return self._borders[idx]

    # ######################################################## #
    #                       properties                         #
    # ######################################################## #

    @property
    def borders(self) -> typing.Tuple[parameters.abc.Pitch, parameters.abc.Pitch]:
        return self._borders

    @property
    def range(self) -> parameters.abc.Pitch:
        return self._borders[1] - self._borders[0]

    # ######################################################## #
    #                       public methods                     #
    # ######################################################## #

    def find_all_pitch_variants(
        self, pitch: parameters.abc.Pitch, period: typing.Any = None
    ) -> typing.Tuple[parameters.abc.Pitch]:
        """Return pitches in all possible register between minima and maxima."""

        if period is None:
            period = Ambitus._guess_period(pitch)

        minima, maxima = self._borders

        variants = []

        # TODO(reduce redundancy)
        dummy_pitch = copy.copy(pitch)
        while dummy_pitch <= maxima:
            if dummy_pitch >= minima:
                variants.append(copy.copy(dummy_pitch))

            dummy_pitch.add(period)

        dummy_pitch = copy.copy(pitch)
        dummy_pitch.subtract(period)
        while dummy_pitch >= minima:
            if dummy_pitch <= maxima:
                variants.append(copy.copy(dummy_pitch))

            dummy_pitch.subtract(period)

        return tuple(sorted(variants))
