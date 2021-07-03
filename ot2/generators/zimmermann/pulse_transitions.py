import typing

import numpy as np
import pygmo as pg

from mutwo.generators import toussaint

from ot2.generators import zimmermann_constants


class ContinousPulseTransitionsMaker(object):
    def __init__(
        self,
        pulse_duration_at_start: float,
        pulse_duration_range_at_end: typing.Tuple[float, float],
        n_pulses: int,
        rising_transition_percentage: float,
        n_gradations_per_transition: int = zimmermann_constants.DEFAULT_N_GRADATIONS_PER_TRANSITION,
    ):
        # percentage tests
        assert rising_transition_percentage >= 0 and rising_transition_percentage <= 1

        self._pulse_duration_at_start = pulse_duration_at_start
        self._pulse_duration_range_at_end = pulse_duration_range_at_end
        self._n_pulses = n_pulses
        self._rising_transition_percentage = rising_transition_percentage
        self._n_gradations_per_transition = n_gradations_per_transition

        self._init_movement_direction_per_transition()
        self._init_domains()

    def _init_movement_direction_per_transition(self):
        self._movement_direction_per_transition = toussaint.euclidean(
            int(self._rising_transition_percentage * (self._n_pulses - 1)),
            (self._n_pulses - 1),
        )

    def _make_domain(self, value0: float, value1: float) -> typing.Tuple[float, ...]:
        return tuple(
            np.linspace(
                value0, value1, self._n_gradations_per_transition + 2, dtype=float
            )[1:-1]
        )

    def _init_domains(self):
        self._domains = (
            self._make_domain(zimmermann_constants.MIN_TRANSITION_CHANGE, 1),
            self._make_domain(1, zimmermann_constants.MAX_TRANSITION_CHANGE),
        )

    def _convert_x_to_factors(
        self, x: typing.Tuple[int, ...]
    ) -> typing.Tuple[float, ...]:
        return tuple(
            self._domains[self._movement_direction_per_transition[nth_transition]][
                int(nth_factor)
            ]
            for nth_transition, nth_factor in enumerate(x)
        )

    def _apply_factors(
        self, factors: typing.Tuple[float, ...]
    ) -> typing.Tuple[float, ...]:
        pulses = [self._pulse_duration_at_start]
        for factor in factors:
            pulses.append(pulses[-1] * factor)
        return tuple(pulses)

    def _convert_x_to_pulses(
        self, x: typing.Tuple[int, ...]
    ) -> typing.Tuple[float, ...]:
        return self._apply_factors(self._convert_x_to_factors(x))

    # Inequality Constraints
    def get_nic(self) -> int:
        return 2

    # Equality Constraints
    def get_nec(self) -> int:
        return 0

    # Objectives
    def get_nobj(self) -> int:
        return 1

    # Integer Variables
    def get_nix(self) -> int:
        return self._n_pulses - 1

    # Boundaries
    def get_bounds(self) -> typing.Tuple[typing.List[int]]:
        return (
            [0] * self.get_nix(),
            [self._n_gradations_per_transition - 1] * self.get_nix(),
        )

    def _fitness_different_pulses(self, pulses: typing.Tuple[float, ...]) -> float:
        differences = 0
        for index0, index1 in zip(range(len(pulses)), range(5, len(pulses))):
            pulse0, *pulses_to_compare = pulses[index0:index1]
            differences += sum(
                abs(pulse0 - pulse_to_compare) for pulse_to_compare in pulses_to_compare
            )
        return -differences

    def _fitness_get_inequal_constaints(
        self, pulses: typing.Tuple[float, ...]
    ) -> typing.List[float]:
        # if smaller than min duration: returns value > 0
        ic0 = self._pulse_duration_range_at_end[0] - pulses[-1]
        # if bigger than max duration: returns value > 0
        ic1 = pulses[-1] - self._pulse_duration_range_at_end[1]

        return [ic0, ic1]

    def fitness(self, x: typing.Tuple[int, ...]) -> typing.List[float]:
        pulses = self._convert_x_to_pulses(x)

        different_pulses = self._fitness_different_pulses(pulses)
        inequeal_constaints = self._fitness_get_inequal_constaints(pulses)

        fitness = [different_pulses] + inequeal_constaints

        return fitness


DEFAULT_GENERATIONS = 800
DEFAULT_POPULATION_SIZE = 100
DEFAULT_SEED = 10


def find_pulses(
    cptm: ContinousPulseTransitionsMaker = ContinousPulseTransitionsMaker(
        30, (5, 10), 20, 0.3
    ),
    generations: int = DEFAULT_GENERATIONS,
    population_size: int = DEFAULT_POPULATION_SIZE,
    seed: int = DEFAULT_SEED,
) -> typing.Tuple[float, ...]:
    udp = pg.problem(cptm)
    algorithm = pg.algorithm(pg.gaco(gen=generations, seed=seed))
    # algorithm.set_verbosity(1)
    algorithm.set_verbosity(0)
    population = pg.population(udp, population_size)
    resulting_population = algorithm.evolve(population)

    best_x = resulting_population.champion_x
    best_fitness = resulting_population.champion_f

    pulses = cptm._convert_x_to_pulses(best_x)

    is_valid = best_fitness[1] <= 0 and best_fitness[2] <= 0
    if is_valid:
        print("Found valid solution.")
    else:
        msg = "WARNING: FOUND INVALID SOLUTION!"
        if best_fitness[1] > 0:
            msg += " Solution is too small."
        else:
            msg += " Solution is too big."
        print(msg)

    return pulses
