import functools
import math


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
