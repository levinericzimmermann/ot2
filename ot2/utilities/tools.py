import functools
import math
import typing

from mutwo.events import basic

from ot2.constants import instruments
from ot2.events import basic as ot2_basic


def gcd(*arg):
    return functools.reduce(math.gcd, arg)


def lcm(*arg: int) -> int:
    """from

    https://stackoverflow.com/questions/37237954/
    calculate-the-lcm-of-a-list-of-given-numbers-in-python
    """
    lcm = arg[0]
    for i in arg[1:]:
        lcm = lcm * i // gcd(lcm, i)
    return lcm


def convert_dict_to_tagged_event(
    data: typing.Dict[str, basic.SequentialEvent]
) -> ot2_basic.TaggedSimultaneousEvent:
    return ot2_basic.TaggedSimultaneousEvent(
        [
            basic.SimultaneousEvent([data[instrument_name]])
            for instrument_name in "sus0 sus1 sus2 drone percussion noise".split(" ")
        ],
        tag_to_event_index=instruments.INSTRUMENT_ID_TO_INDEX,
    )
