"""Brute force trial to find valid nested loops.

Doesn't work
"""

import fractions
import functools
import itertools
import json
import operator

from mutwo.events import basic

from ot2.generators import zimmermann

import sys
import threading

try:
    import thread
except ImportError:
    import _thread as thread

try:  # use code that works the same in Python 2 and 3
    range, _print = xrange, print

    def print(*args, **kwargs):
        flush = kwargs.pop("flush", False)
        _print(*args, **kwargs)
        if flush:
            kwargs.get("file", sys.stdout).flush()


except NameError:
    pass


def cdquit(fn_name):
    # print to stderr, unbuffered in Python 2.
    print("{0} took too long".format(fn_name), file=sys.stderr)
    sys.stderr.flush()  # Python 3 stderr is likely buffered.
    thread.interrupt_main()  # raises KeyboardInterrupt


def exit_after(s):
    """
    use as decorator to exit process if
    function takes longer than s seconds
    """

    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, cdquit, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result

        return inner

    return outer


def convert_nested_loop_to_sequential_event(nested_loop):
    result = basic.SequentialEvent([])
    for element in nested_loop:
        if isinstance(element, tuple):
            result.append(convert_nested_loop_to_sequential_event(element))
        else:
            result.append(basic.SimpleEvent(element))
    return result


def is_nested_loop_valid(nested_loop_as_sequential_event) -> bool:
    for bar in nested_loop_as_sequential_event:
        bar_duration = bar.duration
        if (bar_duration / 4) % 2 != 0:
            print("False bar dur")
            return False

        if (
            bar_duration < ALLOWED_SUMMED_RANGE[0][0]
            or bar_duration > ALLOWED_SUMMED_RANGE[0][1]
        ):
            print("too big/small bar dur")
            return False

        for beat in bar:
            beat_duration = beat.duration
            if (beat_duration / 2) % 2 != 0:
                return False
                print("False beat dur")

            if (
                beat_duration < ALLOWED_SUMMED_RANGE[1][0]
                or beat_duration > ALLOWED_SUMMED_RANGE[1][1]
            ):
                return False
                print("too big/small beat dur")

    return True


@exit_after(5)
def find_loop(loops):
    return zimmermann.make_nested_loop(*loops)


RANGE_LOOPS = tuple(tuple(range(*range_)) for range_ in ((2, 5), (2, 5), (1, 4)))
ALLOWED_SUMMED_RANGE = (
    # min/max pairs
    (fractions.Fraction(1, 1), fractions.Fraction(4, 1)),
    (fractions.Fraction(1, 2), fractions.Fraction(3, 2)),
)
MIN_LOOPSIZE, MAX_LOOPSIZE = 1, 3

VALID_LOOPS = []
for loopsizes in itertools.combinations_with_replacement(
    range(MIN_LOOPSIZE, MAX_LOOPSIZE + 1), 3
):
    for permutated_loopsizes in set(itertools.permutations(loopsizes)):
        possible_loops_for_each_iteration = tuple(
            functools.reduce(
                operator.add,
                (
                    tuple(set(itertools.permutations(comb)))
                    for comb in itertools.combinations_with_replacement(range_, n_items)
                    if not (len(set(comb)) == 1 and len(comb) != 1)
                ),
            )
            for range_, n_items in zip(RANGE_LOOPS, permutated_loopsizes)
        )

        for loops in itertools.product(*possible_loops_for_each_iteration):
            print(loops)
            try:
                nested_loop = find_loop(loops)
            except KeyboardInterrupt:
                nested_loop = None
            if nested_loop:
                nested_loop_as_sequential_event = convert_nested_loop_to_sequential_event(
                    nested_loop
                )
                if is_nested_loop_valid(nested_loop_as_sequential_event):
                    print("VALID: ", nested_loop)
                    VALID_LOOPS.append(nested_loop)
                    print("")
                    print("")


with open("scripts/valid_nested_loops.json", "w") as f:
    f.write(json.dump(VALID_LOOPS))
