import typing

from mutwo import events

from ot2 import analysis
from ot2 import constants as ot2_constants
from ot2 import events as ot2_events

from . import base
from . import river
from . import simple


class MixedPhraseToTimeBracketsConverter0(base.PhraseToTimeBracketsConverter):
    def __init__(
        self,
        start_or_start_range: events.time_brackets.TimeOrTimeRange,
        end_or_end_range: events.time_brackets.TimeOrTimeRange,
        phrase_to_connection_pitches_melodies_converter=river.imbal.RestructuredPhrasePartsAndCengkokLineToImbalBasedRootMelodiesConverter(),
        phrase_to_keyboard_octaves_converter: typing.Optional[
            simple.PhraseToKeyboardOctavesConverter
        ] = simple.PhraseToKeyboardOctavesConverter(),
    ):
        super().__init__(start_or_start_range, end_or_end_range)
        self._phrase_to_connection_pitches_melodies_converter = (
            phrase_to_connection_pitches_melodies_converter
        )
        self._phrase_to_keyboard_octaves_converter = (
            phrase_to_keyboard_octaves_converter
        )

    def convert(
        self,
        phrase_to_convert: ot2_events.basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> typing.Tuple[base.CengkokTimeBracket, ...]:
        time_bracket = self._make_time_bracket_blueprint(phrase_to_convert)

        if self._phrase_to_connection_pitches_melodies_converter:
            connection_pitches_melodies = (
                self._phrase_to_connection_pitches_melodies_converter.convert(
                    phrase_to_convert, []
                )
            )
            for instrument_id, connection_pitches_melody in zip(
                (ot2_constants.instruments.ID_SUS2, ot2_constants.instruments.ID_SUS0),
                connection_pitches_melodies,
            ):
                tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
                    [connection_pitches_melody], tag=instrument_id
                )
                time_bracket.append(tagged_simultaneous_event)

        if self._phrase_to_keyboard_octaves_converter:
            keyboard = self._phrase_to_keyboard_octaves_converter.convert(
                phrase_to_convert
            )
            time_bracket.append(keyboard)
        return (time_bracket,)
