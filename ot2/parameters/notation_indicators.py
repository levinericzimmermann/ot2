import dataclasses
import typing

from mutwo.events import music_constants
from mutwo.parameters import abc
from mutwo.parameters import notation_indicators


@dataclasses.dataclass()
class Noise(abc.ImplicitPlayingIndicator):
    presence: typing.Optional[int] = None
    density: typing.Optional[int] = None
    is_periodic: typing.Optional[bool] = False
    is_pitch: typing.Optional[bool] = False


@dataclasses.dataclass()
class CentDeviation(abc.ImplicitPlayingIndicator):
    deviation: typing.Optional[float] = None


@dataclasses.dataclass(frozen=True)
class OT2NotationIndicatorCollection(notation_indicators.NotationIndicatorCollection):
    # this is kind of redundant, but perhaps still better than without using
    # the `dataclasses` module
    noise: Noise = dataclasses.field(default_factory=Noise)
    cent_deviation: CentDeviation = dataclasses.field(default_factory=CentDeviation)


# set mutwo default values
music_constants.DEFAULT_NOTATION_INDICATORS_COLLECTION_CLASS = (
    OT2NotationIndicatorCollection
)
