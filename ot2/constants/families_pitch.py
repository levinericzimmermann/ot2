"""Definition of global 'FamilyOfPitchCurves'.
"""

import copy
import itertools
import operator
import pickle
import typing

from mutwo.converters.frontends import ekmelily_constants
from mutwo.events import basic
from mutwo.events import families
from mutwo.parameters import pitches
from mutwo.utilities import tools

from ot2.constants import compute
from ot2.constants import common_product_set_scales
from ot2.constants import structure


def _find_closest_approximation_of_interval_in_cps_scale_candidates(
    interval_to_approximate: pitches.JustIntonationPitch,
    *common_product_set_scales: typing.Tuple[pitches.JustIntonationPitch, ...],
) -> typing.Tuple[
    typing.Tuple[pitches.JustIntonationPitch, ...],
    typing.Tuple[pitches.JustIntonationPitch, pitches.JustIntonationPitch],
]:
    """Find frame pitches for a stochastic part.

    The frame pitches try to interpolate between the last pitch of the
    previous part and the first pitch of the next part.

    It returns a tuple where the first element is the 'CommonProductSetScale'
    with the best result and the second element a tuple with the suggested
    frame pitches.
    """

    interval_to_approximate = interval_to_approximate.normalize(mutate=False)

    candidates = []
    for common_product_set_scale in common_product_set_scales:
        for pitch0, pitch1 in itertools.combinations(common_product_set_scale, 2):
            for frame_pitch0, frame_pitch1 in ((pitch0, pitch1), (pitch1, pitch0)):
                interval = frame_pitch1 - frame_pitch0
                difference = interval - interval_to_approximate
                difference.normalize()
                candidates.append(
                    (
                        (common_product_set_scale, (frame_pitch0, frame_pitch1)),
                        len(difference.factorised),
                    )
                )

    best = min(candidates, key=operator.itemgetter(1))[0]
    return best


def _find_neighbours_for_each_pitch(
    scale: typing.Tuple[pitches.JustIntonationPitch, ...]
) -> typing.Dict[typing.Tuple[int, ...], typing.Tuple[typing.Set[int], ...]]:
    pitch_to_pitch_neighbours = {pitch.exponents: set([]) for pitch in scale}
    for pitch0, pitch1 in itertools.combinations(scale, 2):
        intersection = pitch0.intersection(pitch1, mutate=False)
        intersection.normalize()
        if intersection != pitches.JustIntonationPitch("1/1"):
            pitch_to_pitch_neighbours[pitch0.exponents].add(pitch1.exponents)
            pitch_to_pitch_neighbours[pitch1.exponents].add(pitch0.exponents)

    return pitch_to_pitch_neighbours


def _find_connection_pitch_between_two_pitches(
    scale: typing.Tuple[pitches.JustIntonationPitch, ...]
) -> typing.Dict[
    typing.Tuple[typing.Tuple[int, ...], ...], pitches.JustIntonationPitch
]:
    pitch_pair_to_connection_pitch = {}
    for pitch0, pitch1 in itertools.combinations(scale, 2):
        intersection = pitch0.intersection(pitch1, mutate=False, strict=True)
        intersection.normalize()
        if intersection == pitches.JustIntonationPitch("1/1"):
            intersection = pitch0.intersection(pitch1, mutate=False, strict=False)
            intersection.normalize()
        if intersection != pitches.JustIntonationPitch("1/1"):
            pitch_pair_to_connection_pitch.update(
                {(pitch0.exponents, pitch1.exponents): intersection}
            )
            pitch_pair_to_connection_pitch.update(
                {(pitch1.exponents, pitch0.exponents): intersection}
            )

    return pitch_pair_to_connection_pitch


def _get_connection_pitches_for_root_pitches(
    root_notes: typing.Tuple[pitches.JustIntonationPitch, ...],
    pitch_pair_to_connection_pitch: typing.Dict[
        typing.Tuple[typing.Tuple[int, ...], ...], pitches.JustIntonationPitch
    ],
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    connection_pitches = []
    for pitch0, pitch1 in zip(root_notes, root_notes[1:]):
        connection_pitches.append(
            pitch_pair_to_connection_pitch[(pitch0.exponents, pitch1.exponents)]
        )

    return tuple(connection_pitches)


def _extend_cps_scale_melody(
    given_melody: typing.Tuple[pitches.JustIntonationPitch, ...],
    given_scale: typing.Tuple[pitches.JustIntonationPitch, ...],
    size_of_resulting_melody: int,
) -> typing.Tuple[pitches.JustIntonationPitch, ...]:
    pitch_to_counter = {pitch.exponents: 0 for pitch in given_scale}
    for pitch in given_melody:
        pitch_to_counter[pitch.exponents] += 1

    neighbours = _find_neighbours_for_each_pitch(given_scale)

    resulting_melody = list(map(copy.copy, given_melody))
    while len(resulting_melody) < size_of_resulting_melody:
        for nth_pair, melody_pitches in enumerate(
            tuple(zip(resulting_melody, resulting_melody[1:]))
        ):
            neighbours_pitches = tuple(
                neighbours[pitch.exponents] for pitch in melody_pitches
            )
            common_neighbours = tuple(
                neighbours_pitches[0].intersection(neighbours_pitches[1])
            )
            if not common_neighbours:
                raise NotImplementedError(
                    f"Couldn't find any neighbour between '{melody_pitches[0]}' and"
                    f" '{melody_pitches[1]}'!"
                )
            choosen_neighbour = min(
                common_neighbours, key=lambda exponents: pitch_to_counter[exponents]
            )
            pitch_to_counter[choosen_neighbour] += 1
            choosen_neighbour_as_pitch = pitches.JustIntonationPitch(choosen_neighbour)
            resulting_melody.insert((nth_pair * 2) + 1, choosen_neighbour_as_pitch)
            if len(resulting_melody) >= size_of_resulting_melody:
                break

    return tuple(resulting_melody)


def _family_data_to_families(
    last_pitch_of_last_melodic_phrase: pitches.JustIntonationPitch,
    first_pitch_of_next_melodic_phrase: pitches.JustIntonationPitch,
    duration_in_seconds: float,
    duration_of_following_cengkok_part_in_seconds: float,
    n_root_notes_per_family: typing.Tuple[int, ...],
    density: float,
    rest_distribution: typing.Tuple[float, ...],
) -> basic.SequentialEvent[
    typing.Union[families.FamilyOfPitchCurves, basic.SimpleEvent]
]:
    # (1) get root notes
    n_root_notes_summed = sum(n_root_notes_per_family)
    (
        choosen_cps_scale,
        frame_pitches,
    ) = _find_closest_approximation_of_interval_in_cps_scale_candidates(
        first_pitch_of_next_melodic_phrase - last_pitch_of_last_melodic_phrase,
        *common_product_set_scales.COMMON_PRODUCT_SET_SCALES,
    )
    root_notes = _extend_cps_scale_melody(
        frame_pitches, choosen_cps_scale, n_root_notes_summed
    )
    difference_between_root_note_and_last_cantus_firmus_pitch = (
        last_pitch_of_last_melodic_phrase - root_notes[0]
    )
    pitch_pair_to_connection_pitch = _find_connection_pitch_between_two_pitches(
        choosen_cps_scale
    )

    # (2) get duration for each family / for each rest
    concatenated_duration_for_all_families = duration_in_seconds * density
    concatenated_duration_for_all_rests = (
        duration_in_seconds - concatenated_duration_for_all_families
    )
    duration_per_family_in_seconds = tuple(
        (n_root_notes / n_root_notes_summed) * concatenated_duration_for_all_families
        for n_root_notes in n_root_notes_per_family
    )
    assert round(sum(duration_per_family_in_seconds), 4) == round(
        concatenated_duration_for_all_families, 4
    )
    n_families = len(n_root_notes_per_family)
    n_rests = n_families + 1
    if rest_distribution:
        assert len(rest_distribution) == n_rests
        summed_weights = sum(rest_distribution)
        duration_per_rest_in_seconds = [
            concatenated_duration_for_all_rests * (weight / summed_weights)
            for weight in rest_distribution
        ]
    else:
        duration_per_rest_in_seconds = [
            concatenated_duration_for_all_rests / n_rests for _ in range(n_rests)
        ]

    # (3) build families / rests
    family_structure = basic.SequentialEvent([])
    root_note_indices = tuple(tools.accumulate_from_zero(n_root_notes_per_family))
    for (
        root_notes_index_start,
        root_notes_index_end,
        duration_for_current_family_in_seconds,
        duration_for_current_rest,
    ) in zip(
        root_note_indices,
        root_note_indices[1:],
        duration_per_family_in_seconds,
        duration_per_rest_in_seconds,
    ):
        # between each family there is a rest
        family_structure.append(basic.SimpleEvent(duration_for_current_rest))
        root_notes_for_current_family = root_notes[
            root_notes_index_start:root_notes_index_end
        ]
        connection_notes_for_current_family = _get_connection_pitches_for_root_pitches(
            root_notes_for_current_family, pitch_pair_to_connection_pitch
        )
        new_family = families.RootAndConnectionBasedFamilyOfPitchCurves(
            duration_for_current_family_in_seconds,
            tuple(
                (
                    pitch + difference_between_root_note_and_last_cantus_firmus_pitch
                ).normalize(mutate=False)
                for pitch in root_notes_for_current_family
            ),
            tuple(
                (
                    pitch + difference_between_root_note_and_last_cantus_firmus_pitch
                ).normalize(mutate=False)
                for pitch in connection_notes_for_current_family
            ),
            generations=GENERATIONS,
            population_size=POPULATION_SIZE,
        )
        family_structure.append(new_family)

    family_structure.append(
        basic.SimpleEvent(
            duration_per_rest_in_seconds[-1]
            + duration_of_following_cengkok_part_in_seconds
        )
    )

    assert round(family_structure.duration, 3) == (
        round(duration_in_seconds + duration_of_following_cengkok_part_in_seconds, 3)
    )

    return family_structure


def _make_families(
    family_data_per_part: typing.Tuple[
        typing.Tuple[typing.Tuple[int, ...], float], ...
    ],
    composition_structure: structure.StructureType,
) -> basic.SequentialEvent[
    typing.Union[basic.SimpleEvent, families.FamilyOfPitchCurves]
]:
    import progressbar

    families_for_all_parts = basic.SequentialEvent([])
    with progressbar.ProgressBar(max_value=len(family_data_per_part)) as bar:
        nth_part = 0
        for part0, part1, family_data in zip(
            basic.SequentialEvent([None]) + composition_structure,
            composition_structure,
            family_data_per_part,
        ):
            duration_in_seconds = part1[0].duration
            duration_of_following_cengkok_part_in_seconds = part1[1].duration_in_seconds
            if part0:
                last_pitch_of_last_melodic_phrase = part0[1][-1].root
            else:
                last_pitch_of_last_melodic_phrase = pitches.JustIntonationPitch("1/1")

            first_pitch_of_next_melodic_phrase = part1[1][0].root

            n_root_notes_per_family, density, *rest_distribution = family_data

            if rest_distribution:
                rest_distribution = rest_distribution[0]

            family_structure_for_current_part = _family_data_to_families(
                last_pitch_of_last_melodic_phrase,
                first_pitch_of_next_melodic_phrase,
                duration_in_seconds,
                duration_of_following_cengkok_part_in_seconds,
                n_root_notes_per_family,
                density,
                rest_distribution,
            )

            assert round(family_structure_for_current_part.duration, 5) == round(
                duration_in_seconds + duration_of_following_cengkok_part_in_seconds, 5
            )

            families_for_all_parts.extend(family_structure_for_current_part)
            bar.update(nth_part)
            nth_part += 1

    return families_for_all_parts


def _concatenate_families(
    families_pitch: basic.SequentialEvent[
        typing.Union[basic.SimpleEvent, families.FamilyOfPitchCurves]
    ]
) -> families.FamilyOfPitchCurves:
    absolute_entry_delay_and_family_of_pitch_curve_pairs = [
        (absolute_entry_delay, family_of_pitch_curves)
        for absolute_entry_delay, family_of_pitch_curves in zip(
            families_pitch.absolute_times, families_pitch
        )
        if type(family_of_pitch_curves) != basic.SimpleEvent
    ]
    return families.FamilyOfPitchCurves.from_families_of_curves(
        *absolute_entry_delay_and_family_of_pitch_curve_pairs
    )


def _filter_curves_with_unnotateable_pitches(
    family_of_pitch_curves: families.FamilyOfPitchCurves,
) -> families.FamilyOfPitchCurves:
    def condition(pitch_curve: families.PitchCurve) -> bool:
        pitch = pitch_curve.pitch
        is_notateable = True
        for exponent, prime in zip(pitch.exponents, pitch.primes):
            if prime > 3:
                try:
                    max_exponent = (
                        ekmelily_constants.DEFAULT_PRIME_TO_HIGHEST_ALLOWED_EXPONENT[
                            prime
                        ]
                    )
                except KeyError:
                    max_exponent = None
                    is_notateable = False
                if max_exponent and abs(exponent) > max_exponent:
                    is_notateable = False
        return is_notateable

    return family_of_pitch_curves.filter(condition, mutate=False)


def _export(object_: families.FamilyOfPitchCurves, path: str):
    with open(path, "wb") as f:
        pickle.dump(object_, f)


def _import(path: str):
    with open(path, "rb") as f:
        object_ = pickle.load(f)
    return object_


# GENERATIONS = 100
# GENERATIONS = 2
GENERATIONS = 200
POPULATION_SIZE = 80

FAMILIES_PITCH_PATH = "ot2/constants/FAMILIES_PITCH.pickle"

FAMILY_DATA_PER_PART = (
    # PART(N_ROOT_NOTES_PER_FAMILY, DENSITY, REST_DURATION_PERCENTAGE)
    ((2, 3), 0.75, (0.25, 0.9, 0.1)),  # 1  langsamer anfang mit field recording, erste inseln
    ((3, 2), 0.7, (0.335, 0.65, 0.085)),  # weiter inseln, am ende contapunctus_simpliccisimus
    ((3, 4), 0.885, (0.3, 0.2, 0.1)),  # sehr leise, nur klavierakkorde & noise
    ((2, 3), 0.7),  # wieder aufgehen, ploetzlich wieder sustaining instruments
    ((2, 2, 3), 0.83, (0.35, 0.25, 0.2, 0.2)),  # 5  nur klaenge mit tonhoehen, dicht, hohe sinustoene
    ((4,), 0.7),  # noise instrument + klarinette solo + pop - song - kaufhaus fieldrecording
    ((4,), 0.6, (0.89, 0.13)),  # augmentierter cantus firmus teil, lange mono/homo-phone melodie, einstieg in dichte inseln mit viel tape
    ((3, 2, 5), 0.9),  # dichte inseln mit viel tape, bis dann in gerauesche (instr + noise) uebergeht, und dann lange
    ((3,), 0.95),  # kurze stelle, weiter mit geraueschen, ist nicht sehr lange, weil danach recht lange cantus firmus kommt
    ((5,), 0.95),  # 10  # was passiert nach langem cantus firmus? -> es gibt extrem viel stille und dazwischen homophone akkorde
    ((5,), 0.95),
    ((3, 2, 5), 0.5),
    ((4,), 0.8),
)

if compute.COMPUTE_FAMILIES_PITCH:
    FAMILIES_PITCH = _make_families(FAMILY_DATA_PER_PART, structure.STRUCTURE)
    _export(FAMILIES_PITCH, FAMILIES_PITCH_PATH)
else:
    FAMILIES_PITCH = _import(FAMILIES_PITCH_PATH)

FAMILY_PITCH = _concatenate_families(FAMILIES_PITCH)
FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES = _filter_curves_with_unnotateable_pitches(
    FAMILY_PITCH
)
# FAMILY_PITCH.show_plot()  # insane plot showing function
