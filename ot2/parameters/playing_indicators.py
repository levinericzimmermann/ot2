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


@dataclasses.dataclass(frozen=True)
class OT2PlayingIndicatorCollection(playing_indicators.PlayingIndicatorCollection):
    # this is kind of redundant, but perhaps still better than without using
    # the `dataclasses` module
    explicit_fermata: ExplicitFermata = dataclasses.field(
        default_factory=ExplicitFermata
    )


# set mutwo default values
music_constants.DEFAULT_PLAYING_INDICATORS_COLLECTION_CLASS = (
    OT2PlayingIndicatorCollection
)
