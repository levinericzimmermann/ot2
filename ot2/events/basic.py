import typing

from mutwo.events import abc
from mutwo.events import basic


T = typing.TypeVar("T", bound=abc.Event)


class AssignedSimultaneousEvent(basic.SimultaneousEvent, typing.Generic[T]):
    """SimultaneousEvent which has been assigned to a certain instrument"""

    def __init__(self, events: typing.Sequence[abc.Event], instrument: str):
        super().__init__(events)
        self.instrument = instrument


class TaggedSimultaneousEvent(basic.SimultaneousEvent, typing.Generic[T]):
    def __init__(
        self,
        events: typing.Sequence[abc.Event],
        tag_to_event_index: typing.Dict[str, int],
    ):
        super().__init__(events)
        self.tag_to_event_index = tag_to_event_index

    def __getitem__(self, index_or_slice: typing.Union[str, slice, int]):
        if index_or_slice in self.tag_to_event_index:
            index_or_slice = self.tag_to_event_index[index_or_slice]

        return super().__getitem__(index_or_slice)


class SequentialEventWithTempo(basic.SequentialEvent, typing.Generic[T]):
    _class_specific_side_attributes = (
        "tempo",
    ) + basic.SequentialEvent._class_specific_side_attributes

    def __init__(self, events: typing.Sequence[abc.Event], tempo: float):
        super().__init__(events)
        self.tempo = tempo
