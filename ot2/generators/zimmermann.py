import functools
import itertools
import math
import typing

try:
    import quicktions as fractions  # type: ignore
except ImportError:
    import fractions  # type: ignore

from mutwo.parameters import pitches
from ortools.sat.python import cp_model

from ot2.events import bars
from ot2.generators import zimmermann_constants


class SymmetricalPermutation(object):
    """Make symmetrical otonalities / utonalities.

    :param k: The constant number.
    :param r: The varying numbers.

    This algorithm has been described in "Bewegungen im unendlichen
    Tonraum" [2018] by Levin Eric Zimmermann.
    """

    def __init__(self, k: int, r: typing.Sequence[int]):
        self._harmonies = SymmetricalPermutation._make_harmonies(k, r)
        self._connections = SymmetricalPermutation._make_connections(k, r)
        self._k = k
        self._r = r

    # ######################################################## #
    #                     static methods                       #
    # ######################################################## #

    @staticmethod
    def _make_harmonies(
        k: int, r: typing.Sequence[int]
    ) -> typing.Dict[str, typing.Tuple[pitches.JustIntonationPitch, ...]]:
        harmonies = {}
        for exponent_k, exponent_r, name in (
            (1, 1, zimmermann_constants.OTONAL_HARMONY_NAME),
            (-1, -1, zimmermann_constants.UTONAL_HARMONY_NAME),
            (-1, 1, zimmermann_constants.F_OTONAL_HARMONY_NAME),
            (1, -1, zimmermann_constants.F_UTONAL_HARMONY_NAME),
        ):
            harmony = []
            k_pitch = pitches.JustIntonationPitch(
                fractions.Fraction(k ** exponent_k).limit_denominator(k)
            )
            for prime_number in r:
                r_pitch = pitches.JustIntonationPitch(
                    fractions.Fraction(prime_number ** exponent_r).limit_denominator(
                        prime_number
                    )
                )
                harmony.append(r_pitch + k_pitch)
                harmonies.update({name: tuple(harmony)})

        return harmonies

    @staticmethod
    def _make_connections(
        k: int, r: typing.Sequence[int]
    ) -> typing.Dict[
        typing.Tuple[str, str], typing.Tuple[pitches.JustIntonationPitch, ...]
    ]:
        connections = {}

        connection_pitches_0 = (pitches.JustIntonationPitch("{}/1".format(k)),)
        connection_pitches_1 = (pitches.JustIntonationPitch("1/{}".format(k)),)
        connection_pitches_2 = tuple(
            pitches.JustIntonationPitch("{}/1".format(prime)) for prime in r
        )
        connection_pitches_3 = tuple(
            pitches.JustIntonationPitch("1/{}".format(prime)) for prime in r
        )

        for harmony0, harmony1, connection_pitches in (
            (
                zimmermann_constants.OTONAL_HARMONY_NAME,
                zimmermann_constants.F_UTONAL_HARMONY_NAME,
                connection_pitches_0,
            ),
            (
                zimmermann_constants.UTONAL_HARMONY_NAME,
                zimmermann_constants.F_OTONAL_HARMONY_NAME,
                connection_pitches_1,
            ),
            (
                zimmermann_constants.OTONAL_HARMONY_NAME,
                zimmermann_constants.F_OTONAL_HARMONY_NAME,
                connection_pitches_2,
            ),
            (
                zimmermann_constants.UTONAL_HARMONY_NAME,
                zimmermann_constants.F_UTONAL_HARMONY_NAME,
                connection_pitches_3,
            ),
        ):
            connections.update({(harmony0, harmony1): connection_pitches})
            connections.update({(harmony1, harmony0): connection_pitches})

        return connections

    # ######################################################## #
    #                       properties                         #
    # ######################################################## #

    @property
    def k(self) -> int:
        return self._k

    @property
    def r(self) -> typing.Sequence[int]:
        return self._r

    @property
    def harmonies(
        self,
    ) -> typing.Dict[str, typing.Tuple[pitches.JustIntonationPitch, ...]]:
        return self._harmonies

    @property
    def connections(
        self,
    ) -> typing.Dict[
        typing.Tuple[str, str], typing.Tuple[pitches.JustIntonationPitch, ...]
    ]:
        return self._connections


def make_nested_loop(*loop: typing.Sequence[int]) -> typing.Tuple:
    """Build nested loops from loop durations.

    :param loop: Loops of durations which indicate how often
        items of the next level shall be repeated. From outer level
        to inner level.
    :type loop: typing.Sequence[int]

    **Example:**

    >>> from ot2.generators import zimmermann
    >>> nested_loop = make_nested_loop((3, 2), (2, 2, 1))
    >>> nested_loop.get_parameter('duration')
    ((2, 2, 1), (2, 2), (1, 2, 2), (1, 2), (2, 1, 2), (2, 1))

    The function repeat loops until all loops are returned to their
    start position.
    """

    try:
        assert len(loop) >= 1
    except AssertionError:
        message = "Found only {} loops ({}). Please provide at least two loops!".format(
            len(loop), loop
        )
        raise ValueError(message)

    class Looper(object):
        def __init__(self, *item: int):
            self._loop = itertools.cycle(item)
            self._position = itertools.cycle(range(len(item)))
            self._current_position = 0

        def __next__(self):
            self._current_position = next(self._position)
            return next(self._loop)

        @property
        def position(self) -> int:
            return self._current_position

    loopers = tuple(Looper(*lo) for lo in loop)

    @typing.overload
    def build_loop(n_times: int, loopers: None) -> int:
        ...

    @typing.overload
    def build_loop(n_times: int, loopers: typing.Tuple[Looper, ...]) -> typing.Tuple:
        ...

    def build_loop(
        n_times: int, loopers: typing.Optional[typing.Tuple[Looper, ...]]
    ) -> typing.Union[typing.Tuple, int]:
        if not loopers:
            return n_times
        else:
            loops = []
            for _ in range(n_times):
                remaining = loopers[1:]
                if not remaining:
                    remaining = None
                loops.append(build_loop(next(loopers[0]), loopers[1:]))
            return tuple(loops)

    loops = []
    loops.append(build_loop(next(loopers[0]), loopers[1:]))
    while any(looper.position != 0 for looper in loopers):
        loops.append(build_loop(next(loopers[0]), loopers[1:]))
    return tuple(loops)


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


class BarsMaker(object):
    def __call__(self) -> typing.Tuple[typing.Tuple[bars.Bar, ...], ...]:
        raise NotImplementedError()


class LoopBarsConverter(BarsMaker):
    class _VarArraySolutionSaver(cp_model.CpSolverSolutionCallback):
        """Save intermediate solutions."""

        def __init__(self, variables):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._variables = variables
            self._solution_count = 0
            self._solutions = []

        @property
        def solutions(self) -> typing.List[typing.Tuple[int, ...]]:
            return self._solutions

        def on_solution_callback(self):
            self._solution_count += 1
            solution = []
            for variable in self._variables:
                solution.append(self.Value(variable))
            self._solutions.append(tuple(solution))

        def solution_count(self):
            return self._solution_count

    def __init__(
        self,
        nth_solution: int,
        loop: typing.Sequence[int],
        n_items: int,
        lower_bound: int,
        upper_bound: int,
        min_sum: int,  # min_sum / 4 (quarter notes)
        max_sum: int,  # max_sum / 4 (quarter notes)
    ):
        self._nth_solution = nth_solution
        self._loop = loop
        self._n_items = n_items
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound
        self._min_sum = min_sum
        self._max_sum = max_sum
        self._model = cp_model.CpModel()
        self._variables = self._init_variables()
        self._init_constraints()

    @staticmethod
    def _test_for_loops(pattern: typing.Tuple[int, ...]) -> bool:
        pattern_length = len(pattern)
        half = pattern_length // 2
        for division_size in range(1, half + 1):
            if pattern_length % division_size == 0:
                items = tuple(
                    pattern[n : n + division_size]
                    for n in range(0, pattern_length, division_size)
                )
                if len(set(items)) == 1:
                    return True

        return False

    @staticmethod
    def _filter_solutions(
        solutions: typing.Tuple[typing.Tuple[int, ...], ...]
    ) -> typing.Tuple[typing.Tuple[int, ...], ...]:
        filtered_solutions = []
        for solution in solutions:
            if not LoopBarsConverter._test_for_loops(solution):
                filtered_solutions.append(solution)
        return tuple(filtered_solutions)

    def _init_variables(self,) -> typing.Tuple[cp_model.IntVar, ...]:
        return tuple(
            self._model.NewIntVar(
                self._lower_bound, self._upper_bound, "var{}".format(nth_variable),
            )
            for nth_variable in range(self._n_items)
        )

    def _init_constraints(self):
        combinations = set(self._unfold_pattern(self._variables))

        for nth_combination, combination in enumerate(combinations):
            sum_variable = self._model.NewIntVar(
                self._lower_bound * len(combination),
                self._upper_bound * len(combination),
                "SumVar{}".format(nth_combination),
            )
            self._model.Add(sum_variable == sum(combination))
            self._model.AddModuloEquality(0, sum_variable, 4)
            self._model.Add(sum_variable >= self._min_sum)
            self._model.Add(sum_variable <= self._max_sum)

    def _unfold_pattern(
        self, pattern: typing.Tuple[typing.Any, ...]
    ) -> typing.Tuple[typing.Tuple[typing.Any, ...], ...]:
        n_loops = lcm(self._n_items, sum(self._loop)) // sum(self._loop)
        abstract_bars = []
        cycled_items = itertools.cycle(pattern)
        for _ in range(n_loops):
            for loopsize in self._loop:
                combination = tuple(next(cycled_items) for __ in range(loopsize))
                abstract_bars.append(combination)
        return tuple(abstract_bars)

    def _solve(self) -> typing.Tuple[typing.Tuple[int, ...], ...]:
        solver = cp_model.CpSolver()
        solution_saver = self._VarArraySolutionSaver(self._variables)
        solver.SearchForAllSolutions(self._model, solution_saver)
        solutions = tuple(solution_saver.solutions)
        return LoopBarsConverter._filter_solutions(solutions)

    def _make_grid(self, duration: int) -> typing.Tuple[fractions.Fraction, ...]:
        # TODO(Improve make grid function)
        return tuple([fractions.Fraction(3, 16), fractions.Fraction(1, 16)] * duration)

    def __call__(self) -> typing.Tuple[bars.Bar, ...]:
        found_loops = []
        for solution in self._solve():
            ot2_bars = []
            for bar_data in self._unfold_pattern(solution):
                duration = sum(bar_data)
                time_signature = (int(duration / 2), 2)
                subdivisions = tuple(fractions.Fraction(n, 4) for n in bar_data)
                grid = self._make_grid(duration)
                assert sum(grid) == sum(subdivisions)
                bar = bars.Bar(time_signature, subdivisions, grid)
                ot2_bars.append(bar)

            found_loops.append(tuple(ot2_bars))

        return tuple(found_loops)[self._nth_solution]
