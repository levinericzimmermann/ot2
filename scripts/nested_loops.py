import itertools
import typing

from ortools.sat.python import cp_model


class VarArraySolutionSaver(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

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


class TwoLevelFinder(object):
    def __init__(
        self,
        loop: typing.Sequence[int],
        n_items: int,
        lower_bound: int,
        upper_bound: int,
        min_sum: int,
        max_sum: int,
    ):
        self._model = cp_model.CpModel()
        self._variables = TwoLevelFinder._init_variables(
            self._model, n_items, lower_bound, upper_bound
        )
        TwoLevelFinder._init_constraints(
            self._model,
            loop,
            n_items,
            lower_bound,
            upper_bound,
            min_sum,
            max_sum,
            self._variables,
        )

    @staticmethod
    def _init_variables(
        model: cp_model.CpModel, n_items: int, lower_bound: int, upper_bound: int
    ) -> typing.Tuple[cp_model.IntVar, ...]:
        return tuple(
            model.NewIntVar(lower_bound, upper_bound, "var{}".format(nth_variable),)
            for nth_variable in range(n_items)
        )

    @staticmethod
    def _init_constraints(
        model: cp_model.CpModel,
        loop: typing.Sequence[int],
        n_items: int,
        lower_bound: int,
        upper_bound: int,
        min_sum: int,
        max_sum: int,
        variables: typing.Tuple[cp_model.IntVar, ...],
    ):
        combinations = set([])
        cycled_items = itertools.cycle(variables)
        for _ in range(n_items):
            for loopsize in loop:
                combination = tuple(next(cycled_items) for __ in range(loopsize))
                combinations.add(combination)

        for nth_combination, combination in enumerate(combinations):
            sum_variable = model.NewIntVar(
                lower_bound * len(combination),
                upper_bound * len(combination),
                "SumVar{}".format(nth_combination),
            )
            model.Add(sum_variable == sum(combination))
            model.AddModuloEquality(0, sum_variable, 4)
            model.Add(sum_variable >= min_sum)
            model.Add(sum_variable <= max_sum)

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
            if not TwoLevelFinder._test_for_loops(solution):
                filtered_solutions.append(solution)
        return tuple(filtered_solutions)

    def solve(self) -> typing.Tuple[typing.Tuple[int, ...], ...]:
        solver = cp_model.CpSolver()
        solution_saver = VarArraySolutionSaver(self._variables)
        solver.SearchForAllSolutions(self._model, solution_saver)
        solutions = tuple(solution_saver.solutions)
        return TwoLevelFinder._filter_solutions(solutions)



if __name__ == "__main__":
    tlf = TwoLevelFinder((4, 4, 2), 6, 1, 3, 4, 15)
    solutions = tlf.solve()
    print(solutions)
