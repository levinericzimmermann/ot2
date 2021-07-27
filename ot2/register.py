"""Script for building and registering time brackets at the global TimeBracketContainer

Public interaction via "main" method.
"""

from mutwo import utilities


from ot2 import constants
from ot2 import converters
from ot2 import stochastic


def _register_cengkok_brackets():
    absolute_time = 0
    for part in constants.structure.STRUCTURE:
        absolute_time += part[0].duration
        cengkok_phrase = part[1]
        start_time_of_cengkok = float(absolute_time)
        converter = converters.symmetrical.cengkoks.PhraseToTimeBracketConverter(
            start_time_of_cengkok,
            start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
        )
        time_bracket = converter.convert(cengkok_phrase)
        constants.time_brackets_container.TIME_BRACKETS.register(time_bracket, False)
        absolute_time += cengkok_phrase.duration_in_seconds


def _register_stochastic_brackets():
    collected_time_brackets = stochastic.main()
    for instrument_id, time_bracket in collected_time_brackets:
        try:
            constants.time_brackets_container.TIME_BRACKETS.register(
                time_bracket, tags_to_analyse=(instrument_id,)
            )
        except utilities.exceptions.OverlappingTimeBracketsError:
            pass


def main():
    _register_cengkok_brackets()
    _register_stochastic_brackets()
