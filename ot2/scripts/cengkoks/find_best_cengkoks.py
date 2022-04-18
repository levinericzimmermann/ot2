import fractions
import functools
import itertools
import operator
import os
import pickle
import typing

import pygmo as pg

from mutwo.converters.backends import mmml
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import pitches

from ot2.analysis import applied_cantus_firmus
from ot2.analysis import cengkoks
from ot2.constants import instruments
from ot2.scripts.cengkoks import vanitas_melody_parts
from ot2.scripts.cengkoks import rhythms


class BestCengkokFinder(object):
    def __init__(
        self,
        melody_part: typing.Tuple[
            typing.Tuple[
                typing.Tuple[pitches.JustIntonationPitch, ...],
                fractions.Fraction,
                typing.Optional[basic.SequentialEvent[music.NoteLike]],
            ],
            ...,
        ],
        rhythm_per_duration: typing.Dict[int, basic.SequentialEvent[basic.SimpleEvent]],
    ):
        self._melody_part = melody_part
        self._rhythm_per_duration = rhythm_per_duration
        self._drone = BestCengkokFinder._make_drone(melody_part)
        (
            self._bars_to_fill,
            self._event_blueprint,
        ) = BestCengkokFinder._get_variable_data(melody_part)
        (
            self._possible_melodies_for_each_bar_to_fill,
            self._bars_to_fill,
        ) = self._get_possible_melodies_for_each_bar_to_fill(
            melody_part, self._bars_to_fill
        )

    @staticmethod
    def _get_variable_data(
        melody_part: typing.Tuple[
            typing.Tuple[
                typing.Tuple[pitches.JustIntonationPitch, ...],
                fractions.Fraction,
                typing.Optional[basic.SequentialEvent[music.NoteLike]],
            ],
            ...,
        ],
    ) -> typing.Tuple[
        typing.Tuple[typing.Tuple[int, fractions.Fraction], ...], basic.SequentialEvent
    ]:
        event_blueprint = basic.SequentialEvent([])
        bars_to_fill = []
        for nth_bar, bar in enumerate(melody_part):
            _, duration, brahms_melody = bar
            if brahms_melody:
                brahms_melody_pitches = functools.reduce(
                    operator.add, brahms_melody.get_parameter("pitch_or_pitches")
                )
            if brahms_melody and (
                min(brahms_melody_pitches)
                >= instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.borders[
                    0
                ]
                and max(brahms_melody_pitches)
                <= instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.borders[
                    1
                ]
            ):
                event_blueprint.append(brahms_melody)
            else:
                bars_to_fill.append((nth_bar, duration))
                event_blueprint.append(basic.SimpleEvent(duration))
        return tuple(bars_to_fill), event_blueprint

    def _apply_vanitas_rhythm_grid_on_melody(
        self, melody: basic.SequentialEvent[music.NoteLike],
    ):
        melody_duration = int(melody.duration)
        vanitas_rhythm = self._rhythm_per_duration[melody_duration * 2]
        for event, start_and_end_time in zip(
            melody, melody.start_and_end_time_per_event
        ):
            start, end = (int(4 * time) for time in start_and_end_time)
            event.duration = vanitas_rhythm[start:end].duration

    def _build_possible_melodies_for_bar(
        self,
        available_cengkoks: typing.Dict[
            int, typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]]]
        ],
        current_harmony: typing.Tuple[pitches.JustIntonationPitch, ...],
        next_harmony: typing.Optional[typing.Tuple[pitches.JustIntonationPitch, ...]],
        use_four_beats: bool,
    ) -> typing.Tuple[basic.SequentialEvent[music.NoteLike], ...]:
        def apply_octave_mark(pitch, octave_mark):
            octave_mark = int(octave_mark)
            oct_pitch = pitches.JustIntonationPitch([octave_mark])
            return pitch + oct_pitch

        if next_harmony:
            exponents_per_bar0, exponents_per_bar1 = (
                tuple(
                    map(
                        lambda pitch: pitch.normalize(mutate=False).exponents,
                        pitch_or_pitches,
                    )
                )
                for pitch_or_pitches in (current_harmony, next_harmony,)
            )
            common_exponents = tuple(
                set(exponents_per_bar0).intersection(set(exponents_per_bar1))
            )
            common_pitch_index = exponents_per_bar0.index(common_exponents[0])
        else:
            common_pitch_index = 0

        seleh = (1, 2, 3, 4, 5, 6)[common_pitch_index]
        seleh_is_four = False
        if seleh == 4:
            seleh_is_four = True
            seleh = 3

        cengkoks_to_use = available_cengkoks[seleh]

        decodex = {
            java_pitch_index: pitch
            for java_pitch_index, pitch in zip(
                "1 2 3 4 5 6".split(" "), current_harmony
            )
        }
        pitch_converter = mmml.MMMLPitchesConverter(
            mmml.MMMLSinglePitchConverter(decodex, apply_octave_mark,)
        )

        possible_melodies = []
        for cengkok_pitches, cengkok_rhythms in cengkoks_to_use:
            cengkok_pitches = pitch_converter.convert(cengkok_pitches)
            if seleh_is_four:
                cengkok_pitches = cengkok_pitches[:-1] + (
                    (
                        decodex["4"].register(
                            cengkok_pitches[-1][0].octave, mutate=False
                        ),
                    ),
                )

            melody = basic.SequentialEvent(
                [
                    music.NoteLike(pitch, fractions.Fraction(rhythm, 4))
                    for pitch, rhythm in zip(cengkok_pitches, cengkok_rhythms)
                ]
            )
            if use_four_beats:
                melody.cut_off(0, 1)

            self._apply_vanitas_rhythm_grid_on_melody(melody)

            def register_pitches0(pitch_or_pitches):
                return [
                    pitch - pitches.JustIntonationPitch("2/1")
                    for pitch in pitch_or_pitches
                ]

            def register_pitches1(pitch_or_pitches):
                return [
                    pitch + pitches.JustIntonationPitch("2/1")
                    for pitch in pitch_or_pitches
                ]

            melodies_to_add = (
                melody,
                melody.set_parameter(
                    "pitch_or_pitches", register_pitches0, mutate=False
                ),
                melody.set_parameter(
                    "pitch_or_pitches", register_pitches1, mutate=False
                ),
            )

            for melody in melodies_to_add:
                available_pitches = functools.reduce(
                    operator.add, melody.get_parameter("pitch_or_pitches")
                )
                if (
                    min(available_pitches)
                    >= instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES.borders[
                        0
                    ]
                    and max(available_pitches)
                    <= instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES[
                        1
                    ]
                ):
                    possible_melodies.append(melody)

        return tuple(possible_melodies)

    def _get_possible_melodies_for_each_bar_to_fill(
        self,
        melody_part: typing.Tuple[
            typing.Tuple[
                typing.Tuple[pitches.JustIntonationPitch, ...],
                fractions.Fraction,
                typing.Optional[basic.SequentialEvent[music.NoteLike]],
            ],
            ...,
        ],
        bars_to_fill: typing.Tuple[typing.Tuple[int, fractions.Fraction], ...],
    ) -> typing.Tuple[typing.Tuple[basic.SequentialEvent[music.NoteLike], ...], ...]:
        possible_melodies_for_each_bar_to_fill = []
        adjusted_bars_to_fill = []
        for nth_bar, bar_duration in bars_to_fill:
            cengkok_duration = int(bar_duration * 4)
            use_four_beats = False
            if cengkok_duration == 4:
                cengkok_duration = 8
                use_four_beats = True
            available_cengkoks = cengkoks.CENGKOKS[cengkok_duration]
            current_harmony = melody_part[nth_bar][0]
            try:
                next_harmony = melody_part[nth_bar + 1][0]
            except IndexError:
                next_harmony = None
            possible_melodies = self._build_possible_melodies_for_bar(
                available_cengkoks, current_harmony, next_harmony, use_four_beats
            )
            n_possible_melodies = len(possible_melodies)
            if n_possible_melodies == 1:
                self._event_blueprint[nth_bar] = possible_melodies[0]
            elif n_possible_melodies > 0:
                adjusted_bars_to_fill.append((nth_bar, bar_duration))
                possible_melodies_for_each_bar_to_fill.append(possible_melodies)
            else:
                self._event_blueprint[nth_bar] = basic.SequentialEvent(
                    [music.NoteLike([], self._event_blueprint[nth_bar].duration)]
                )

        return (
            tuple(possible_melodies_for_each_bar_to_fill),
            tuple(adjusted_bars_to_fill),
        )

    @staticmethod
    def _make_drone(
        melody_part: typing.Tuple[
            typing.Tuple[
                typing.Tuple[pitches.JustIntonationPitch, ...],
                fractions.Fraction,
                typing.Optional[basic.SequentialEvent[music.NoteLike]],
            ],
            ...,
        ],
    ) -> basic.SequentialEvent[music.NoteLike]:
        drone = basic.SequentialEvent([])
        for harmony, duration, _ in melody_part:
            drone.append(
                music.NoteLike(harmony[0].register(-2, mutate=False), duration)
            )
        drone[0].duration -= fractions.Fraction(1, 4)
        drone[-1].duration += fractions.Fraction(1, 4)
        return drone

    def _convert_x_to_nested_sequential_event(
        self, x: typing.Tuple[int, ...]
    ) -> basic.SequentialEvent[basic.SequentialEvent[music.NoteLike]]:
        nested_sequential_event = self._event_blueprint.copy()
        for nth_melody, possible_melodies, bar_data in zip(
            x, self._possible_melodies_for_each_bar_to_fill, self._bars_to_fill
        ):
            nth_bar, _ = bar_data
            choosen_melody = possible_melodies[int(nth_melody)]
            nested_sequential_event[nth_bar] = choosen_melody
        return nested_sequential_event

    @staticmethod
    def _convert_nested_sequential_event_to_sequential_event(
        nested_sequential_event: basic.SequentialEvent[
            basic.SequentialEvent[music.NoteLike]
        ],
    ) -> basic.SequentialEvent[music.NoteLike]:
        sequential_event = functools.reduce(operator.add, nested_sequential_event)
        sequential_event.tie_by(
            lambda _, event1: not (hasattr(event1, "pitch_or_pitches"))
            or len(event1.pitch_or_pitches) == 0,
            event_type_to_examine=basic.SimpleEvent,
        )
        return sequential_event

    def _fitness_harmonicity(
        self, sequential_event: basic.SequentialEvent[music.NoteLike]
    ) -> float:
        harmonicity = 0
        for absolute_time, event in zip(
            sequential_event.absolute_times, sequential_event
        ):
            simultaneous_drone_event = self._drone.get_event_at(absolute_time)
            for pitch0, pitch1 in itertools.product(
                event.pitch_or_pitches, simultaneous_drone_event.pitch_or_pitches
            ):
                harmonicity += (pitch0 - pitch1).harmonicity_simplified_barlow
        return -harmonicity

    def _fitness_melodic_contour(
        self, sequential_event: basic.SequentialEvent[music.NoteLike]
    ) -> float:
        pitches = tuple(
            map(
                lambda pitches: pitches[0] if pitches else None,
                sequential_event.get_parameter("pitch_or_pitches"),
            )
        )
        distance = 0
        for pitch0, pitch1 in zip(pitches, pitches[1:]):
            if pitch0 and pitch1:
                distance += abs(pitch0.cents - pitch1.cents)
        return distance

    def fitness(self, x: typing.Tuple[int, ...]) -> typing.List[float]:
        sequential_event = self._convert_nested_sequential_event_to_sequential_event(
            self._convert_x_to_nested_sequential_event(x)
        )
        fitness_melodic_contour = self._fitness_melodic_contour(sequential_event)
        # fitness_harmonicity = self._fitness_harmonicity(sequential_event)
        return [fitness_melodic_contour]

    def get_nobj(self):
        return 1

    def get_nix(self):
        return len(self._possible_melodies_for_each_bar_to_fill)

    def get_bounds(self) -> typing.Tuple[typing.List[int]]:
        return tuple(
            zip(
                *tuple(
                    [0, len(possible_melodies) - 1]
                    for possible_melodies in self._possible_melodies_for_each_bar_to_fill
                )
            )
        )


def find_best_cengkoks(generations: int = 10, population_size: int = 40):
    def _get_best_of_multi_objective_population(pop):
        sorted_pop = pg.sort_population_mo(points=pop.get_f())
        x = pop.get_x()[sorted_pop[0]]
        x = tuple(int(x) for x in x)
        fitness = pop.get_f()[sorted_pop[0]]
        fitness = tuple(float(n) for n in fitness)
        return x, fitness

    for vanitas_rhythm, vanitas_melody_part in zip(
        rhythms.RHYTHMS, vanitas_melody_parts.VANITAS_MELODY_PARTS.items()
    ):
        start_time, vanitas_melody = vanitas_melody_part

        bcf = BestCengkokFinder(vanitas_melody, vanitas_rhythm)
        problem = pg.problem(bcf)

        algorithm = pg.algorithm(pg.gaco(gen=generations))
        algorithm.set_verbosity(1)

        population = pg.population(problem, population_size)
        resulting_population = algorithm.evolve(population)

        best_x = resulting_population.champion_x
        best_fitness = resulting_population.champion_f

        # best_x, best_fitness = _get_best_of_multi_objective_population(
        #     resulting_population
        # )
        result = bcf._convert_nested_sequential_event_to_sequential_event(
            bcf._convert_x_to_nested_sequential_event(best_x)
        )

        print(best_fitness)
        print("")

        with open(
            "{}/{}_{}.pickle".format(
                PICKLE_PATH, start_time.numerator, start_time.denominator
            ),
            "wb",
        ) as f:
            pickle.dump((start_time, result), f)


def load_cengkoks() -> basic.SequentialEvent[music.NoteLike]:
    blueprint = basic.SequentialEvent(
        [
            basic.SequentialEvent(
                [
                    music.NoteLike(
                        [], applied_cantus_firmus.APPLIED_CANTUS_FIRMUS.duration
                    )
                ]
            )
        ]
    )

    for path in os.listdir(PICKLE_PATH):
        concatenated_path = f"{PICKLE_PATH}/{path}"
        with open(concatenated_path, "rb") as f:
            start_time, applied_melody = pickle.load(f)

        blueprint.squash_in(start_time, applied_melody)

    blueprint.tie_by(
        lambda event0, event1: event0.pitch_or_pitches == event1.pitch_or_pitches,
        event_type_to_examine=basic.SimpleEvent,
    )

    return functools.reduce(operator.add, blueprint)


PICKLE_PATH = "ot2/scripts/cengkoks/solutions_per_melody"


def illustrate_cengkoks(applied_melodies):
    import abjad
    from abjadext import nauert

    from mutwo.converters.frontends import abjad as mutwo_abjad

    time_signatures = tuple(
        abjad.TimeSignature((int(event.duration * 2), 2))
        for event in applied_cantus_firmus.APPLIED_CANTUS_FIRMUS
    )

    search_tree = nauert.UnweightedSearchTree(
        definition={
            2: {
                2: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
                3: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
            },
            3: {
                2: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
                3: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
            },
        },
    )
    abjad_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
        mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
            time_signatures, search_tree=search_tree
        ),
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    )
    abjad_voice = abjad_converter.convert(applied_melodies)

    abjad.attach(
        abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), abjad_voice[0][0]
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\override Staff.TimeSignature.style = #'single-digit"),
        abjad_voice[0][0],
    )
    abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
    lilypond_file = abjad.LilyPondFile(
        items=[abjad_score], includes=["ekme-heji-ref-c.ily"]
    )
    abjad.persist.as_pdf(lilypond_file, "builds/applied_cengkoks.pdf")


def synthesize_applied_cengkoks(applied_cengkoks: basic.SequentialEvent):
    from mutwo.converters.frontends import midi

    converter = midi.MidiFileConverter("builds/materials/applied_cengkoks.mid")
    converter.convert(
        applied_cengkoks.set_parameter(
            "duration", lambda duration: duration * 4, mutate=False
        )
    )


APPLIED_CENGKOKS = load_cengkoks()


if __name__ == "__main__":
    find_best_cengkoks(50, 700)
    APPLIED_CENGKOKS = load_cengkoks()
    synthesize_applied_cengkoks(APPLIED_CENGKOKS)
    illustrate_cengkoks(APPLIED_CENGKOKS)
