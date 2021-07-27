from mutwo.parameters import pitches


def _find_best_diatonic_root(start_pitch_to_root):
    import functools
    import operator

    candidates = []
    combined_pitches = functools.reduce(
        operator.add,
        (
            functools.reduce(
                operator.add,
                (
                    tuple(interval + start_pitch for interval in intervals_per_pitch)
                    for intervals_per_pitch in INTERVALS
                ),
            )
            for start_pitch in start_pitch_to_root.values()
        ),
    )
    for interval_candidate in combined_pitches:
        resulting_pitches = tuple(
            map(
                lambda pitch: (pitch - interval_candidate).normalize(mutate=False),
                combined_pitches,
            )
        )
        fitness = sum(
            sum(
                map(
                    abs,
                    pitch.helmholtz_ellis_just_intonation_notation_commas.prime_to_exponent.values(),
                )
            )
            for pitch in resulting_pitches
        )
        candidates.append(((interval_candidate, resulting_pitches), fitness))

    best = min(candidates, key=operator.itemgetter(1))[0]

    print(tuple(map(lambda c: c[1], candidates)))
    print("")

    print(best[1])
    print("")
    print("")
    print(best[0])
    print("")

    candidates = []
    for possible_diatonic_pitch in "c d e f g a b".split(" "):
        fitness = sum(
            len(pitch.get_closest_pythagorean_pitch_name(possible_diatonic_pitch))
            for pitch in best[1]
        )
        candidates.append((possible_diatonic_pitch, fitness))

    best = min(candidates, key=operator.itemgetter(1))[0]
    print(best)


INTERVALS = (
    (pitches.JustIntonationPitch("7/4"),),
    (pitches.JustIntonationPitch("8/5"),),
    (pitches.JustIntonationPitch("3/2"), pitches.JustIntonationPitch("16/11")),
    (pitches.JustIntonationPitch("5/4"),),
    (pitches.JustIntonationPitch("16/11"),),
    (pitches.JustIntonationPitch("4/3"),),
    (pitches.JustIntonationPitch("7/4"),),
    (pitches.JustIntonationPitch("7/4"),),
    (pitches.JustIntonationPitch("16/11"),),
    (pitches.JustIntonationPitch("4/3"),),
    (pitches.JustIntonationPitch("5/4"),),
    (pitches.JustIntonationPitch("16/11"), pitches.JustIntonationPitch("3/2"),),
    (pitches.JustIntonationPitch("8/5"),),
    (pitches.JustIntonationPitch("7/4"),),
)
"""JI Counterpart for each note of cantus firmus"""


START_PITCH_TO_ROOT = {
    "a": pitches.JustIntonationPitch("1/1"),
    "c": pitches.JustIntonationPitch("6/5"),
    "e": pitches.JustIntonationPitch("3/2"),
    "d": pitches.JustIntonationPitch("4/3"),
    "g": pitches.JustIntonationPitch("16/9"),
}
