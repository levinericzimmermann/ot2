import itertools
import typing

from mutwo import converters
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot2 import constants
from ot2 import converters as ot2_converters


class TimeBracketContainerToSequentialEventsConverter(converters.abc.Converter):
    puffer = 60 * 6  # 6 minutes longer if music is longer than predefined duration

    def __init__(self, tag: str):
        self._tag = tag

    def convert(
        self,
        time_brackets_container_to_convert: events.time_brackets.TimeBracketContainer,
    ) -> typing.Tuple[events.basic.SequentialEvent, ...]:
        extracted_time_brackets = time_brackets_container_to_convert.filter(self._tag)
        filtered_time_brackets = []
        # TODO(mutate / copy instead of altering the original object?)
        for time_bracket in extracted_time_brackets:
            if not isinstance(
                time_bracket,
                ot2_converters.symmetrical.cengkoks.RiverCengkokTimeBracket,
            ):
                new_time_bracket = events.time_brackets.TimeBracket(
                    [
                        simultaneous_event.copy()
                        for simultaneous_event in time_bracket
                        if simultaneous_event.tag == self._tag
                    ],
                    time_bracket.start_or_start_range,
                    time_bracket.end_or_end_range,
                )
                filtered_time_brackets.append(new_time_bracket)
        resulting_sequential_events = tuple(
            events.basic.SequentialEvent(
                [
                    events.basic.SimpleEvent(
                        constants.duration.DURATION_IN_SECONDS + self.puffer
                    )
                ]
            )
            for _ in range(
                max(
                    len(filtered_time_bracket[0])
                    for filtered_time_bracket in filtered_time_brackets
                )
            )
        )
        for time_bracket in filtered_time_brackets:
            start_time, end_time = time_bracket.minimal_start, time_bracket.maximum_end
            duration = end_time - start_time
            for nth_sequential_event, sequential_event in enumerate(time_bracket[0]):
                adjusted_sequential_event = sequential_event.copy()
                adjusted_sequential_event.duration = duration
                for start_time_for_adjusted_event, event in zip(
                    adjusted_sequential_event.absolute_times, adjusted_sequential_event
                ):
                    resulting_sequential_events[nth_sequential_event].squash_in(
                        start_time_for_adjusted_event + start_time, event
                    )

        return resulting_sequential_events


class SequentialEventPairToCommonHarmonicsSequentialEvent(converters.abc.Converter):
    @staticmethod
    def _make_two_pitches_to_common_harmonics_converters(
        absolute_time: parameters.abc.DurationType,
    ) -> typing.Tuple[
        converters.symmetrical.spectrals.TwoPitchesToCommonHarmonicsConverter, ...
    ]:
        absolute_position = absolute_time / constants.duration.DURATION_IN_SECONDS
        minima_partial = int(
            constants.common_harmonics.MINIMA_PARTIAL_TENDENCY.value_at(
                absolute_position
            )
        )
        maxima_partial = int(
            constants.common_harmonics.MAXIMA_PARTIAL_TENDENCY.value_at(
                absolute_position
            )
        )

        return tuple(
            converters.symmetrical.spectrals.TwoPitchesToCommonHarmonicsConverter(
                tonality, minima_partial, maxima_partial
            )
            for tonality in (True, False, None)
        )

    @staticmethod
    def _find_common_harmonics(
        absolute_time: parameters.abc.DurationType,
        pitches0: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
        pitches1: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        two_pitches_to_common_harmonics_converters = SequentialEventPairToCommonHarmonicsSequentialEvent._make_two_pitches_to_common_harmonics_converters(
            absolute_time
        )
        common_harmonics = []
        for converter in two_pitches_to_common_harmonics_converters:
            common_harmonics.extend(converter.convert((pitches0, pitches1)))
        common_harmonics.extend(converter.convert((pitches1, pitches0)))
        return tuple(utilities.tools.uniqify_iterable(common_harmonics))

    @staticmethod
    def _filter_illegal_common_harmonics(
        found_common_harmonics: typing.Sequence[parameters.pitches.CommonHarmonic],
    ) -> typing.Sequence[parameters.pitches.CommonHarmonic]:
        # make sure all common harmonics are within the allowed frequency range and
        # that partials between octaves or unions are omitted

        def filter_function(common_harmonic: parameters.pitches.CommonHarmonic) -> bool:
            frequency = common_harmonic.frequency
            tests = (
                frequency < constants.common_harmonics.UPPER_FREQUENCY_BORDER
                and frequency > constants.common_harmonics.LOWER_FREQUENCY_BORDER,
                not all(
                    tuple(
                        partial.nth_partial // 2 == 0
                        for partial in common_harmonic.partials
                    )
                ),
            )
            return all(tests)

        return tuple(filter(filter_function, found_common_harmonics))

    @staticmethod
    def _filter_overpopulated_common_harmonics(
        found_common_harmonics: typing.Sequence[parameters.pitches.CommonHarmonic],
    ) -> typing.Sequence[parameters.pitches.CommonHarmonic]:
        # make sure that there are not more than 16 pitches in one harmony (due to
        # the restrictions of midi, which makes more than 16 microtonal pitches
        # impossible to render

        return found_common_harmonics

    def convert(
        self,
        sequential_events_pair: typing.Tuple[
            events.basic.SequentialEvent, events.basic.SequentialEvent
        ],
    ) -> events.basic.SequentialEvent:
        first_sequential_event, second_sequential_event = sequential_events_pair
        resulting_sequential_event = events.basic.SequentialEvent([])
        for start_and_end_time, event in zip(
            first_sequential_event.start_and_end_time_per_event, first_sequential_event
        ):
            if hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches:
                start_time, end_time = start_and_end_time
                simultaneous_events = second_sequential_event.cut_out(
                    start_time, end_time, mutate=False
                )
                for start_time_for_partner_event, partner_event in zip(
                    simultaneous_events.absolute_times, simultaneous_events
                ):
                    if (
                        hasattr(partner_event, "pitch_or_pitches")
                        and partner_event.pitch_or_pitches
                    ):
                        resulting_common_harmonics = []
                        for pitch0, pitch1 in itertools.product(
                            event.pitch_or_pitches, partner_event.pitch_or_pitches
                        ):
                            resulting_common_harmonics.extend(
                                SequentialEventPairToCommonHarmonicsSequentialEvent._find_common_harmonics(
                                    start_time_for_partner_event + start_time,
                                    pitch0,
                                    pitch1,
                                )
                            )
                        filtered_common_harmonics = SequentialEventPairToCommonHarmonicsSequentialEvent._filter_illegal_common_harmonics(
                            utilities.tools.uniqify_iterable(resulting_common_harmonics)
                        )
                        filtered_common_harmonics = SequentialEventPairToCommonHarmonicsSequentialEvent._filter_overpopulated_common_harmonics(
                            filtered_common_harmonics
                        )

                        resulting_sequential_event.append(
                            events.music.NoteLike(
                                filtered_common_harmonics, partner_event.duration
                            )
                        )
                    else:
                        resulting_sequential_event.append(
                            events.basic.SimpleEvent(partner_event.duration)
                        )

            else:
                resulting_sequential_event.append(
                    events.basic.SimpleEvent(event.duration)
                )

        resulting_sequential_event.tie_by(
            lambda event0, event1: all(
                tuple(
                    not (hasattr(event, "pitch_or_pitches") and event.pitch_or_pitches)
                    for event in (event0, event1)
                )
            ),
            event_type_to_examine=events.basic.SimpleEvent,
        )
        # assert (
        #     round(resulting_sequential_event.duration)
        #     == constants.duration.DURATION_IN_SECONDS
        # )
        return resulting_sequential_event
