import typing


from ot2 import constants as ot2_constants
from ot2.events import colotomic_brackets


def _adjust_colotomic_element_indicator(
    colotomic_element_indicator: colotomic_brackets.ColotomicElementIndicator,
    n_predefined_pattern: int,
) -> colotomic_brackets.ColotomicElementIndicator:
    adjusted_colotomic_element_indicator = (
        colotomic_element_indicator[0] + n_predefined_pattern,
    ) + colotomic_element_indicator[1:]
    return adjusted_colotomic_element_indicator


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
            _adjust_colotomic_element_indicator(
                indicator_or_indicator_range[0], n_predefined_pattern
            ),
            _adjust_colotomic_element_indicator(
                indicator_or_indicator_range[1], n_predefined_pattern
            ),
        )
    else:
        return _adjust_colotomic_element_indicator(
            indicator_or_indicator_range, n_predefined_pattern
        )


def _adjust_all_colotomic_element_indicators(
    colotomic_brackets_to_adjust: typing.Tuple[colotomic_brackets.ColotomicBracket, ...]
):
    n_predefined_pattern = len(ot2_constants.colotomic_pattern.COLOTOMIC_PATTERNS)
    for colotomic_bracket in colotomic_brackets_to_adjust:
        colotomic_bracket.start_or_start_range = _adjust_indicator_or_indicator_range(
            colotomic_bracket.start_or_start_range, n_predefined_pattern
        )
        colotomic_bracket.end_or_end_range = _adjust_indicator_or_indicator_range(
            colotomic_bracket.end_or_end_range, n_predefined_pattern
        )


def _fill_colotomic_pattern_container(
    colotomic_patterns_to_add: typing.Tuple[colotomic_brackets.ColotomicPattern, ...]
):
    ot2_constants.colotomic_pattern.COLOTOMIC_PATTERNS.extend(colotomic_patterns_to_add)


def _fill_colotomic_brackets_container(
    colotomic_patterns_to_add: typing.Tuple[colotomic_brackets.ColotomicPattern, ...]
):
    _adjust_all_colotomic_element_indicators(colotomic_patterns_to_add)
    for colotomic_bracket in colotomic_patterns_to_add:
        ot2_constants.colotomic_brackets_container.COLOTOMIC_BRACKETS_CONTAINER.register(
            colotomic_bracket
        )


def add_colotomic_patterns_and_colotomic_brackets(
    colotomic_patterns_to_add: typing.Tuple[colotomic_brackets.ColotomicPattern, ...],
    colotomic_brackets_to_add: typing.Tuple[colotomic_brackets.ColotomicBracket, ...],
):
    """Add data to global containers."""

    # don't change order! When brackets get filled
    # it is important that the colotomic pattern container
    # hasn't been changed yet (for "_adjust_colotomic_pattern_indicators")
    _fill_colotomic_brackets_container(colotomic_brackets_to_add)
    _fill_colotomic_pattern_container(colotomic_patterns_to_add)
