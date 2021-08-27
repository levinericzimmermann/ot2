"""Convert phrases to time brackets.

Conversion routines for Part "B" (cengkok based / cantus-firmus based parts).
"""

import typing

import abjad

from mutwo import converters
from mutwo import events
from mutwo import parameters
from ot2.analysis import phrases
from ot2.constants import instruments
from ot2.events import basic as ot2_basic


class CengkokTimeBracket(events.time_brackets.TempoBasedTimeBracket):
    _class_specific_side_attributes = (
        events.time_brackets.TimeBracket._class_specific_side_attributes
        + ("tempo", "time_signatures")
    )

    def __init__(
        self,
        tagged_events: typing.Sequence[
            typing.Union[
                events.basic.TaggedSequentialEvent,
                events.basic.TaggedSimpleEvent,
                events.basic.TaggedSimultaneousEvent,
            ]
        ],
        start_or_start_range: events.time_brackets.TimeOrTimeRange,
        end_or_end_range: events.time_brackets.TimeOrTimeRange,
        time_signatures: typing.Sequence[abjad.TimeSignature],
        tempo: float,
        seed: typing.Optional[int] = None,
    ):
        super().__init__(
            tagged_events, start_or_start_range, end_or_end_range, tempo, seed
        )
        self.time_signatures = time_signatures


class PhraseToTimeBracketConverter(converters.abc.Converter):
    def __init__(
        self,
        start_or_start_range: events.time_brackets.TimeOrTimeRange,
        end_or_end_range: events.time_brackets.TimeOrTimeRange,
    ):
        self._start_or_start_range = start_or_start_range
        self._end_or_end_range = end_or_end_range

    @staticmethod
    def _add_cent_deviation(
        sequential_event_to_process: events.basic.SequentialEvent[
            events.music.NoteLike
        ],
    ):
        for event in sequential_event_to_process:
            if hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches:
                pitch_to_process = event.pitch_or_pitches[0]
                deviation = (
                    pitch_to_process.cent_deviation_from_closest_western_pitch_class
                )
                event.notation_indicators.cent_deviation.deviation = deviation

    def convert(
        self,
        phrase_to_convert: ot2_basic.SequentialEventWithTempo[phrases.PhraseEvent],
    ) -> CengkokTimeBracket:
        time_signatures = [
            abjad.TimeSignature((int(event.duration * 4), 4))
            for event in phrase_to_convert
        ]
        time_bracket = CengkokTimeBracket(
            [],
            self._start_or_start_range,
            self._end_or_end_range,
            time_signatures=time_signatures,
            tempo=phrase_to_convert.tempo,
            seed=100,
        )

        rough_sustaining_instrument_0 = events.basic.TaggedSimultaneousEvent(
            [events.basic.SequentialEvent([])], tag=instruments.ID_SUS0,
        )

        rough_keyboard = events.basic.TaggedSimultaneousEvent(
            [events.basic.SequentialEvent([]) for _ in range(2)],
            tag=instruments.ID_KEYBOARD,
        )
        for bar in phrase_to_convert:
            rough_sustaining_instrument_0[0].append(
                events.music.NoteLike(bar.connection_pitch0, bar.duration * 0.5, "mp")
            )
            rough_sustaining_instrument_0[0].append(
                events.music.NoteLike(bar.connection_pitch1, bar.duration * 0.5, "mp")
            )
            rough_keyboard[0].append(
                events.music.NoteLike(bar.root, bar.duration, "mf")
            )
            rough_keyboard[1].append(
                events.music.NoteLike(
                    bar.root - parameters.pitches.JustIntonationPitch("2/1"),
                    bar.duration,
                    "mf",
                )
            )

        rough_sustaining_instrument_0[0].tie_by(
            condition=lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
        )
        PhraseToTimeBracketConverter._add_cent_deviation(
            rough_sustaining_instrument_0[0]
        )
        time_bracket.append(rough_sustaining_instrument_0)
        time_bracket.append(rough_keyboard)
        return time_bracket
