import dataclasses
import typing

from mutwo.events import music_constants
from mutwo.parameters import abc
from mutwo.parameters import playing_indicators


@dataclasses.dataclass()
class ExplicitFermata(abc.ImplicitPlayingIndicator):
    fermata_type: typing.Optional[
        str
    ] = None  # TODO(for future usage add typing.Literal)
    waiting_range: typing.Optional[typing.Tuple[int, int]] = None


@dataclasses.dataclass()
class Cue(abc.ImplicitPlayingIndicator):
    nth_cue: typing.Optional[int] = None


@dataclasses.dataclass()
class Embouchure(abc.ImplicitPlayingIndicator):
    hint: typing.Optional[str] = None



@dataclasses.dataclass()
class Fingering(abc.ImplicitPlayingIndicator):
    cc: typing.Optional[typing.Tuple[str, ...]] = None
    lh: typing.Optional[typing.Tuple[str, ...]] = None
    rh: typing.Optional[typing.Tuple[str, ...]] = None


@dataclasses.dataclass(frozen=True)
class OT2PlayingIndicatorCollection(playing_indicators.PlayingIndicatorCollection):
    cue: Cue = dataclasses.field(default_factory=Cue)
    embouchure: Embouchure = dataclasses.field(default_factory=Embouchure)
    explicit_fermata: ExplicitFermata = dataclasses.field(
        default_factory=ExplicitFermata
    )
    fingering: Fingering = dataclasses.field(default_factory=Fingering)


# set mutwo default values
music_constants.DEFAULT_PLAYING_INDICATORS_COLLECTION_CLASS = (
    OT2PlayingIndicatorCollection
)
