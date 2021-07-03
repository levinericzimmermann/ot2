import functools
import itertools
import operator
import pickle
import typing

import primesieve
import progressbar

from mutwo.parameters import pitches


def _make_harmonicity_map(
    available_pitches: typing.Tuple[pitches.JustIntonationPitch, ...]
) -> typing.Dict[typing.Tuple[typing.Tuple[int, ...], typing.Tuple[int, ...]], float]:
    harmonicity_map = {}
    for pitch0, pitch1 in itertools.combinations(available_pitches, 2):
        harmonicity = (
            (pitch0 - pitch1).normalize(mutate=False).harmonicity_simplified_barlow
        )
        harmonicity_map.update({(pitch0.exponents, pitch1.exponents): harmonicity})
        harmonicity_map.update({(pitch1.exponents, pitch0.exponents): harmonicity})
    return harmonicity_map


def _make_pitch_candidates(
    used_primes: typing.Tuple[int, ...] = (3, 5, 7, 11),
    max_exponent: typing.Tuple[int, ...] = (2, 1, 1, 1),
    max_combinations: int = 2,
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    elements_per_prime = [[] for _ in used_primes]
    for tonality in (True, False):
        for nth_prime, prime in enumerate(used_primes):
            nth_prime_number = primesieve.count_primes(prime)
            for exponent in range(1, max_exponent[nth_prime] + 1):
                exponents = [0 for _ in range(nth_prime_number)]
                exponents[-1] = exponent
                if not tonality:
                    exponents[-1] = -exponents[-1]
                pitch = pitches.JustIntonationPitch(exponents)
                elements_per_prime[nth_prime].append(pitch)

    candidates = [pitches.JustIntonationPitch()]
    for combination in itertools.product(*elements_per_prime):
        for n_pitches in range(1, max_combinations + 1):
            for elements_to_combine in itertools.combinations(combination, n_pitches):
                pitch = functools.reduce(operator.add, elements_to_combine)
                pitch.normalize()
                if pitch not in candidates:
                    candidates.append(pitch)
    return tuple(candidates)


def _are_canidates_in_valid_cent_range(solution) -> bool:
    are_valid = all(
        (
            all(
                int(abs(pitch0.cents - pitch1.cents)) in VALID_CENT_RANGE
                for pitch0, pitch1 in tuple(itertools.combinations(solution, 2))
            ),
            all(int(abs(pitch.cents)) in VALID_CENT_RANGE for pitch in solution),
        )
    )
    return are_valid


DEFAULT_PITCH_CANIDIDATES = _make_pitch_candidates()
DEFAULT_HARMONICITY_MAP = _make_harmonicity_map(DEFAULT_PITCH_CANIDIDATES)

VALID_CENT_RANGE = tuple(range(80, 1120))


PICKLE_PATH = "ot2/scripts/transitional_harmony/solutions_for_n_pitches.pickle"
"""
# pre-calculated solutions
SOLUTIONS_FOR_N_PITCHES = {
    n_pitches: tuple(
        (
            solution,
            sum(
                DEFAULT_HARMONICITY_MAP[p0.exponents, p1.exponents]
                for p0, p1 in itertools.combinations(solution, 2)
            ),
        )
        for solution in itertools.combinations(DEFAULT_PITCH_CANIDIDATES, n_pitches)
        if _are_canidates_in_valid_cent_range(solution)
    )
    for n_pitches in (3, 4,)
}
with open(PICKLE_PATH, "wb",) as f:
    pickle.dump(SOLUTIONS_FOR_N_PITCHES, f)
"""

with open(PICKLE_PATH, "rb") as f:
    SOLUTIONS_FOR_N_PITCHES = pickle.load(f)

# weights
WEIGHT_TO_ROOT = 0.95
WEIGHT_TO_PREVIOUS_CONNECTION_PITCH = 0.925
WEIGHT_TO_NEXT_CONNECTION_PITCH = 1.05
WEIGHT_FOR_INTER_PITCHES = 0.955


def _find_most_harmonic_set(
    given_pitches: typing.Tuple[pitches.JustIntonationPitch, ...],
    weight_per_given_pitch: typing.Tuple[float, ...],
    weigth_for_inter_added_pitches: float,
    n_pitches_to_add: int,
    harmonicity_map: typing.Dict[
        typing.Tuple[typing.Tuple[int, ...], typing.Tuple[int, ...]], float
    ] = DEFAULT_HARMONICITY_MAP,
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:

    assert len(weight_per_given_pitch) == len(given_pitches)

    # filter given pitches from pitch candidates
    solutions = []
    solution_to_iterate = SOLUTIONS_FOR_N_PITCHES[n_pitches_to_add]
    with progressbar.ProgressBar(max_value=len(solution_to_iterate)) as bar:
        val = 0
        for solution, harmonicity in solution_to_iterate:
            tests_if_solution_shall_be_considered = (
                # avoid repetitions
                all(given_pitch not in solution for given_pitch in given_pitches),
                # avoid microtonal variations of the same pitch within one harmony
                all(
                    int(abs(pitch0.cents - pitch1.cents)) in VALID_CENT_RANGE
                    for pitch0, pitch1 in tuple(
                        itertools.product(given_pitches, solution)
                    )
                ),
            )
            if all(tests_if_solution_shall_be_considered):
                harmonicity *= weigth_for_inter_added_pitches
                harmonicity += sum(
                    sum(
                        harmonicity_map[pitch0.exponents, pitch1.exponents] * weight
                        for pitch0 in solution
                    )
                    for pitch1, weight in zip(given_pitches, weight_per_given_pitch)
                )
                solutions.append((solution, harmonicity))
            val += 1
            bar.update(val)

    return sorted(solutions, key=operator.itemgetter(1))[-1]


def _make_connection_pitch(
    current_pitch: pitches.JustIntonationPitch,
    neighbour_pitch: typing.Optional[pitches.JustIntonationPitch],
) -> typing.Optional[pitches.JustIntonationPitch]:
    if neighbour_pitch:
        connection_pitch = current_pitch + neighbour_pitch
        connection_pitch.normalize()
    else:
        connection_pitch = None
    return connection_pitch


def find_transitional_harmony(
    n_pitches: int,
    current_pitch: pitches.JustIntonationPitch,
    previous_pitch: typing.Optional[pitches.JustIntonationPitch],
    next_pitch: typing.Optional[pitches.JustIntonationPitch],
    harmonicity_map: typing.Dict[
        typing.Tuple[typing.Tuple[int, ...], typing.Tuple[int, ...]], float
    ] = DEFAULT_HARMONICITY_MAP,
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    harmony = [current_pitch]
    weight_per_given_pitch = [WEIGHT_TO_ROOT]
    connection_pitches = tuple(
        _make_connection_pitch(current_pitch, neighbour_pitch)
        for neighbour_pitch in (previous_pitch, next_pitch)
    )
    for weight, connection_pitch in zip(
        (WEIGHT_TO_PREVIOUS_CONNECTION_PITCH, WEIGHT_TO_NEXT_CONNECTION_PITCH),
        connection_pitches,
    ):
        if connection_pitch and connection_pitch not in harmony:
            harmony.append(connection_pitch)
            weight_per_given_pitch.append(weight)

    adjusted_harmony = tuple(
        (pitch - current_pitch).normalize(mutate=False) for pitch in harmony
    )
    added_pitches, harmonicity = _find_most_harmonic_set(
        adjusted_harmony,
        weight_per_given_pitch,
        WEIGHT_FOR_INTER_PITCHES,
        n_pitches - len(harmony),
        harmonicity_map,
    )

    return tuple(sorted(adjusted_harmony + added_pitches)), harmonicity


if __name__ == "__main__":
    import json

    N_PITCHES_PER_HARMONY = 6

    available_pitches = tuple(
        pitches.JustIntonationPitch(pitch)
        for pitch in "3/2 5/4 7/4 11/8 4/3 8/5 8/7 16/11".split(" ")
    )

    data = []
    for current_pitch, next_pitch, previous_pitch in itertools.product(
        available_pitches, available_pitches, available_pitches
    ):
        solution = find_transitional_harmony(
            N_PITCHES_PER_HARMONY, current_pitch, previous_pitch, next_pitch,
        )

        data.append(
            (
                current_pitch.exponents,
                previous_pitch.exponents,
                next_pitch.exponents,
                tuple(pitch.exponents for pitch in solution[0]),
                solution[1],
            )
        )
        print(
            solution, current_pitch, previous_pitch, next_pitch,
        )

    with open(
        f"ot2/scripts/transitional_harmony/solutions{N_PITCHES_PER_HARMONY}.json", "w"
    ) as f:
        f.write(json.dumps(data))
