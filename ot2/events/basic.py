import typing

from mutwo.events import abc
from mutwo.events import basic


class AssignedSimultaneousEvent(basic.SimultaneousEvent):
    """SimultaneousEvent which has been assigned to a certain instrument"""

    def __init__(self, events: typing.Sequence[abc.Event], instrument: str):
        super().__init__(events)
        self.instrument = instrument
