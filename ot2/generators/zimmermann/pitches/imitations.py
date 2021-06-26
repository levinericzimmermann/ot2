"""Imitate a given melodic contour within a user-defined harmony."""

import typing

from mutwo.parameters import abc
from mutwo.parameters import pitches
from ortools.sat.python import cp_model


def _build_model(
    distance_in_cents_between_melodic_pitches: typing.Tuple[int, ...],
    cents_to_pitch: typing.Dict,
    melodic_pitches: typing.Tuple[abc.Pitch, ...],
) -> typing.Tuple[cp_model.CpModel, typing.List]:
    """Build ortools model for finding best imitation in given harmony."""

    model = cp_model.CpModel()

    domain = cp_model.Domain.FromValues(cents_to_pitch.keys())
    variables = [
        model.NewIntVarFromDomain(domain, f"pitch{nth_pitch}")
        for nth_pitch in range(len(melodic_pitches))
    ]

    max_step = max(cents_to_pitch.keys()) - min(cents_to_pitch.keys())

    absolute_differences = []

    for nth_step, variable0, variable1, distance in zip(
        range(len(distance_in_cents_between_melodic_pitches)),
        variables,
        variables[1:],
        distance_in_cents_between_melodic_pitches,
    ):
        difference_between_desired_and_real_distance = model.NewIntVar(
            -max_step,
            max_step,
            f"difference_between_desired_and_real_distance{nth_step}_0",
        )
        abs_difference_between_desired_and_real_distance = model.NewIntVar(
            0, max_step, f"abs_difference_between_desired_and_real_distance{nth_step}_1"
        )
        model.Add(
            difference_between_desired_and_real_distance
            == distance - (variable1 - variable0)
        )
        model.AddAbsEquality(
            abs_difference_between_desired_and_real_distance,
            difference_between_desired_and_real_distance,
        )
        absolute_differences.append(abs_difference_between_desired_and_real_distance)

    model.Minimize(sum(absolute_differences))
    return model, variables


def imitate(
    melodic_pitches: typing.Tuple[abc.Pitch, ...],
    harmony: typing.Tuple[pitches.JustIntonationPitch, ...],
    cent_factor: int = 10,
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    """Find best imitation of melodic pitches with given harmony.

    :param melodic_pitches: The pitches which contour shall be imitated.
    :param harmony: The given harmony.
    :param cent_factor: Factor to multiply cent values. Higher values give
        more precise results.

    This function uses Googles ortools for constraint programming.
    """

    distance_in_cents_between_melodic_pitches = tuple(
        int(abc.Pitch.hertz_to_cents(pitch0.frequency, pitch1.frequency) * cent_factor)
        for pitch0, pitch1 in zip(melodic_pitches, melodic_pitches[1:])
    )

    harmony_with_one_octave_lower = tuple(
        pitch + pitches.JustIntonationPitch("1/2") for pitch in harmony
    )
    harmony_with_one_octave_higher = tuple(
        pitch + pitches.JustIntonationPitch("2/1") for pitch in harmony
    )
    available_pitches = (
        harmony_with_one_octave_lower + harmony + harmony_with_one_octave_higher
    )

    cents_to_pitch = {
        int(pitch.cents * cent_factor): pitch for pitch in available_pitches
    }

    model, variables = _build_model(
        distance_in_cents_between_melodic_pitches, cents_to_pitch, melodic_pitches
    )
    solver = cp_model.CpSolver()
    solver.Solve(model)

    return tuple(cents_to_pitch[solver.Value(variable)] for variable in variables)
