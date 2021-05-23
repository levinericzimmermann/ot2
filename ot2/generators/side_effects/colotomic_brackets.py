import abc
import typing

from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos

from ot2 import constants as ot2_constants
from ot2.events import basic as ot2_basic
from ot2.events import colotomic_brackets


class ColotomicBracketGenerator(abc.ABC):
    @staticmethod
    def _adjust_colotomic_element_indicator(
        colotomic_element_indicator: colotomic_brackets.ColotomicElementIndicator,
        n_predefined_pattern: int,
    ) -> colotomic_brackets.ColotomicElementIndicator:
        adjusted_colotomic_element_indicator = (
            colotomic_element_indicator[0] + n_predefined_pattern,
        ) + colotomic_element_indicator[1:]
        return adjusted_colotomic_element_indicator

    @staticmethod
    def _adjust_indicator_or_indicator_range(
        indicator_or_indicator_range: typing.Union[
            colotomic_brackets.ColotomicElementIndicator,
            typing.Tuple[
                colotomic_brackets.ColotomicElementIndicator,
                colotomic_brackets.ColotomicElementIndicator,
            ],
        ],
        n_predefined_pattern: int,
    ) -> typing.Union[
        colotomic_brackets.ColotomicElementIndicator,
        typing.Tuple[
            colotomic_brackets.ColotomicElementIndicator,
            colotomic_brackets.ColotomicElementIndicator,
        ],
    ]:
        if len(indicator_or_indicator_range) == 2:
            return (
                ColotomicBracketGenerator._adjust_colotomic_element_indicator(
                    indicator_or_indicator_range[0], n_predefined_pattern
                ),
                ColotomicBracketGenerator._adjust_colotomic_element_indicator(
                    indicator_or_indicator_range[1], n_predefined_pattern
                ),
            )
        else:
            return ColotomicBracketGenerator._adjust_colotomic_element_indicator(
                indicator_or_indicator_range, n_predefined_pattern
            )

    @staticmethod
    def _adjust_all_colotomic_element_indicators(
        colotomic_brackets_to_adjust: typing.Tuple[
            colotomic_brackets.ColotomicBracket, ...
        ]
    ):
        n_predefined_pattern = len(ot2_constants.colotomic_pattern.COLOTOMIC_PATTERNS)
        for colotomic_bracket in colotomic_brackets_to_adjust:
            colotomic_bracket.start_or_start_range = ColotomicBracketGenerator._adjust_indicator_or_indicator_range(
                colotomic_bracket.start_or_start_range, n_predefined_pattern
            )
            colotomic_bracket.end_or_end_range = ColotomicBracketGenerator._adjust_indicator_or_indicator_range(
                colotomic_bracket.end_or_end_range, n_predefined_pattern
            )

    @abc.abstractmethod
    def make_colotomic_patterns(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicPattern, ...]:
        raise NotImplementedError

    @abc.abstractmethod
    def make_colotomic_brackets(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicBracket, ...]:
        raise NotImplementedError

    def fill_colotomic_pattern_container(self):
        ot2_constants.colotomic_pattern.COLOTOMIC_PATTERNS.extend(
            self.make_colotomic_patterns()
        )

    def fill_colotomic_brackets_container(self):
        generated_colotomic_brackets = self.make_colotomic_brackets()
        ColotomicBracketGenerator._adjust_all_colotomic_element_indicators(
            generated_colotomic_brackets
        )
        for colotomic_bracket in generated_colotomic_brackets:
            ot2_constants.colotomic_brackets_container.COLOTOMIC_BRACKETS_CONTAINER.register(
                colotomic_bracket
            )

    def run(self):
        # don't change order! When brackets get filled
        # it is important that the colotomic pattern container
        # hasn't been changed yet (for "_adjust_colotomic_pattern_indicators")
        self.fill_colotomic_brackets_container()
        self.fill_colotomic_pattern_container()


class TestColotomicBracketGenerator(ColotomicBracketGenerator):
    """Dummy class which return hard coded structures"""

    def make_colotomic_brackets(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicBracket, ...]:
        return (
            # drone
            colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("15/32", 1)])],
                        ot2_constants.instruments.ID_DRONE,
                    ),
                ),
                ((0, 0, 1), (0, 1, 0)),
                ((0, 2, 1), (0, 3, 0)),
            ),
            colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("21/64", 1)])],
                        ot2_constants.instruments.ID_DRONE,
                    ),
                ),
                ((1, 0, 0), (1, 0, 1)),
                ((1, 2, 0), (1, 2, 1)),
            ),
            # sustaining ot2_constants.instruments
            colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("3/4", 1, "f")])],
                        ot2_constants.instruments.ID_SUS0,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("5/8", 1, "f")])],
                        ot2_constants.instruments.ID_SUS1,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("1/2", 1, "f")])],
                        ot2_constants.instruments.ID_SUS2,
                    ),
                ),
                (0, 1, 1),
                (0, 2, 0),
            ),
            colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("45/64", 1, "f")])],
                        ot2_constants.instruments.ID_SUS0,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("5/8", 1, "f")])],
                        ot2_constants.instruments.ID_SUS1,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("15/32", 1, "f")])],
                        ot2_constants.instruments.ID_SUS2,
                    ),
                ),
                (0, 2, 1),
                (0, 2, 2),
            ),
            colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("7/8", 1, "f")])],
                        ot2_constants.instruments.ID_SUS0,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("3/4", 1, "f")])],
                        ot2_constants.instruments.ID_SUS1,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("1/2", 1, "f")])],
                        ot2_constants.instruments.ID_SUS2,
                    ),
                ),
                (1, 0, 2),
                ((1, 1, 1), (1, 1, 2)),
            ),
            colotomic_brackets.ColotomicBracket(
                (
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("1/1", 1, "f")])],
                        ot2_constants.instruments.ID_SUS0,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("7/12", 1, "f")])],
                        ot2_constants.instruments.ID_SUS1,
                    ),
                    ot2_basic.AssignedSimultaneousEvent(
                        [basic.SequentialEvent([music.NoteLike("7/16", 1, "f")])],
                        ot2_constants.instruments.ID_SUS2,
                    ),
                ),
                (1, 1, 2),
                (1, 3, 0),
            ),
        )

    def make_colotomic_patterns(
        self,
    ) -> typing.Tuple[colotomic_brackets.ColotomicPattern, ...]:
        pattern0 = colotomic_brackets.ColotomicPattern(
            [
                colotomic_brackets.ColotomicElement([music.NoteLike("f", 0.75)]),
                colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
                colotomic_brackets.ColotomicElement(
                    [
                        music.NoteLike("f", 0.5),
                        music.NoteLike("f", 2 / 3),
                        music.NoteLike("f", 1 / 3),
                    ]
                ),
                colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
            ],
            tempo=tempos.TempoPoint((70, 90)),
            time_signature=(3, 4),
            n_repetitions=4,
        )

        pattern0.set_parameter("volume", "mp")

        pattern0[1][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
        pattern0[1][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)
        pattern0[3][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
        pattern0[3][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)

        pattern1 = colotomic_brackets.ColotomicPattern(
            [
                colotomic_brackets.ColotomicElement(
                    [
                        music.NoteLike("f", 0.5),
                        music.NoteLike("f", 2 / 3),
                        music.NoteLike("f", 1 / 3),
                    ]
                ),
                colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
                colotomic_brackets.ColotomicElement(
                    [music.NoteLike("g", 0.75), music.NoteLike("f", 0.75)]
                ),
                colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
            ],
            tempo=tempos.TempoPoint((60, 80)),
            time_signature=(3, 4),
            n_repetitions=6,
        )

        pattern1.set_parameter("volume", "mf")

        pattern1[1][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
        pattern1[1][0].playing_indicators.explicit_fermata.waiting_range = (5, 10)
        pattern1[3][0].playing_indicators.explicit_fermata.fermata_type = "fermata"
        pattern1[3][0].playing_indicators.explicit_fermata.waiting_range = (5, 15)

        return (pattern0, pattern1)


class LoopBasedColotomicBracketGenerator(ColotomicBracketGenerator):
    pass
