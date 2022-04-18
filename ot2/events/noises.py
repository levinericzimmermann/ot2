import typing

from mutwo import events
from mutwo import parameters

from ot2.events import noises_constants
from ot2 import parameters as ot2_parameters


class Noise(events.basic.SimpleEvent):
    """Abstracted noise sounds defined by certain characteristics.

    :param density: How dense the noise should be (0, 1, 2 for discreet
        sounds of different density and 3 for continuous sounds)
    :type density: int
    :param presence: How present the noise should be. 0 for rather soft
        and 2 for harsh and extreme noises.
    :type presence: int
    :param duration: The complete duration of the event.
    :type duration: parameters.abc.DurationType
    :param return_pitch: Set to ``True`` if the event should return a
        ``parameters.abc.Pitch`` when calling its :attr:`pitch_or_pitches`
        attribute. Can be useful for midi rendering of the noise, where
        low pitches get assigned to noise sounds.
    :type return_pitch: bool
    """

    def __init__(
        self,
        density: int,
        presence: int,
        duration: parameters.abc.DurationType,
        volume: parameters.abc.Volume,
        return_pitch: bool = False,
        is_periodic: bool = False,
        is_pitch: bool = False,
    ):
        self.density = density
        self.presence = presence
        self.volume = volume
        self.return_pitch = return_pitch
        self.is_periodic = is_periodic
        self.is_pitch = is_pitch
        self.extra_notation_indicators = (
            ot2_parameters.notation_indicators.OT2NotationIndicatorCollection()
        )
        self.playing_indicators = (
            ot2_parameters.playing_indicators.OT2PlayingIndicatorCollection()
        )
        super().__init__(duration)

    def _get_pitch(self) -> parameters.pitches.WesternPitch:
        return noises_constants.DENSITY_AND_PRESENCE_TO_WESTERN_PITCH[
            (self.density, self.presence)
        ]

    @property
    def notation_indicators(
        self,
    ) -> parameters.notation_indicators.NotationIndicatorCollection:
        self.extra_notation_indicators.noise.presence = self.presence
        self.extra_notation_indicators.noise.density = self.density
        self.extra_notation_indicators.noise.is_periodic = self.is_periodic
        self.extra_notation_indicators.noise.is_pitch = self.is_pitch
        return self.extra_notation_indicators

    @property
    def pitch_or_pitches(self) -> typing.List[parameters.pitches.WesternPitch]:
        if self.return_pitch:
            return [self._get_pitch()]
        else:
            return []
