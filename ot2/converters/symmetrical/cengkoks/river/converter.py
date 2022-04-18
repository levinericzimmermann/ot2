"""Convert analysis.phrases to time brackets.

Conversion routines for Part "B" (cengkok based / cantus-firmus based parts).
"""

import copy
import typing
import warnings

import abjad
import yamm

from mutwo import converters
from mutwo import events

from ot2 import analysis
from ot2 import constants as ot2_constants
from ot2.events import basic as ot2_basic
from ot2.converters.symmetrical import (
    keyboard_constants as keyboard_converter_constants,
)
from ot2.converters.symmetrical import keyboard as keyboard_converter

from .. import base

from . import bonang
from . import gong
from . import keyboard
from . import imbal
from . import pillow
from . import structure


class CengkokBasedRestructuredPhrasePartsToSimultaneousEventConverter(
    converters.abc.Converter
):
    @staticmethod
    def _nth_sustaining_instrument_to_tag(nth_sustaining_instrument: int):
        return (
            ot2_constants.instruments.ID_SUS0,
            ot2_constants.instruments.ID_SUS1,
            ot2_constants.instruments.ID_SUS2,
        )[nth_sustaining_instrument]

    def _make_bonangan_melodies(
        self, nth_sustaining_instrument: int, restructured_phrase_parts
    ):
        instr_bonangan = events.basic.TaggedSimultaneousEvent(
            [],
            tag=self._nth_sustaining_instrument_to_tag(nth_sustaining_instrument),
        )
        sine_bonangan = events.basic.TaggedSimultaneousEvent(
            [],
            tag=ot2_constants.instruments.ID_SUS_TO_ID_SINE[
                self._nth_sustaining_instrument_to_tag(nth_sustaining_instrument)
            ],
        )

        restructured_phrase_parts_to_bonangan_converter = (
            bonang.RestructuredPhrasePartsToBonanganConverter()
        )
        (
            bonangan_instr,
            bonangan_sine,
        ) = restructured_phrase_parts_to_bonangan_converter.convert(
            restructured_phrase_parts
        )

        instr_bonangan.append(bonangan_instr)
        sine_bonangan.append(bonangan_sine)

        return instr_bonangan, sine_bonangan

    def convert(
        self,
        restructured_phrase_parts: events.basic.SequentialEvent[
            structure.RestructuredPhrasePart
        ],
    ) -> events.basic.SimultaneousEvent:
        simultaneous_event = events.basic.SimultaneousEvent([])

        restructured_phrase_parts_to_cengkok_line_converter = (
            keyboard.RestructuredPhrasePartsToCengkokLineConverter(
                keyboard.RestructuredPhrasePartsToVirtualCengkokLineConverter(irama=1)
            )
        )
        # virtual_cengkok_line = (
        #     restructured_phrase_parts_to_virtual_cengkok_line_converter.convert(
        #         restructured_phrase_parts
        #     )
        # )
        kb_left_hand = restructured_phrase_parts_to_cengkok_line_converter.convert(
            restructured_phrase_parts
        )

        """
        kb_left_hand = events.basic.SequentialEvent([])
        for cengkok in virtual_cengkok_line:
            kb_left_hand.extend(cengkok)
        kb_left_hand = kb_left_hand[:-1]
        missing_duration = restructured_phrase_parts.duration - kb_left_hand.duration
        kb_left_hand.insert(0, events.basic.SimpleEvent(missing_duration))
        """

        restructured_phrase_parts_and_cengkok_line_to_counter_voice_converter = (
            keyboard.RestructuredPhrasePartsAndCengkokLineToCounterVoiceConverter()
        )

        kb_right_hand = restructured_phrase_parts_and_cengkok_line_to_counter_voice_converter.convert(
            restructured_phrase_parts, kb_left_hand
        )

        kb = events.basic.TaggedSimultaneousEvent(
            [kb_right_hand, kb_left_hand], tag=ot2_constants.instruments.ID_KEYBOARD
        )

        (
            bonangan_instr,
            bonangan_sine,
        ) = self._make_bonangan_melodies(1, restructured_phrase_parts)

        simultaneous_event.append(bonangan_instr)
        simultaneous_event.append(kb)

        simultaneous_event.append(bonangan_sine)

        return simultaneous_event


DEFAULT_LIKELIHOODS = {
    (structure.MOVING,): {structure.MOVING: 0.7, structure.CADENZA: 0.235},
    (structure.CADENZA,): {structure.END: 0.3, structure.END_AND_START: 0.7},
    (structure.END,): {structure.START: 0.8, structure.REST: 0.2},
    (structure.END_AND_START,): {structure.MOVING: 1},
    (structure.START,): {structure.MOVING: 1},
    (structure.REST,): {structure.START: 0.9, structure.REST: 0.1},
}


class PhraseToRestructuredPhrasePartsConverter(converters.abc.Converter):
    def __init__(
        self,
        likelihoods: typing.Dict[
            structure.BarCharacter,
            typing.Tuple[typing.Tuple[structure.BarCharacter, float], ...],
        ] = DEFAULT_LIKELIHOODS,
        start_seed: int = 40,
    ):
        self._likelihoods = likelihoods
        self._start_seed = start_seed

    def _initialise_markov_chain(self, seed: int) -> yamm.Chain:
        return yamm.Chain(self._likelihoods, seed=seed)

    def _find_characters(
        self, n_characters_to_find: int
    ) -> typing.Tuple[structure.BarCharacter, ...]:
        characters = [None]
        seed = self._start_seed
        while characters[-1] != structure.END:
            markov_chain = self._initialise_markov_chain(seed)
            characters = markov_chain.walk_until(
                (structure.START,), n_characters_to_find
            )
            seed += 1
        return characters

    def _split_restructured_phrase_parts_by_characters(
        self,
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
    ) -> typing.Tuple[
        events.basic.SequentialEvent[structure.RestructuredPhrasePart], ...
    ]:
        # first split end-and-start characters to two phrase parts
        processed_restructured_phrase_parts = []
        for restructured_phrase_part in restructured_phrase_parts:
            if (
                restructured_phrase_part.bar_character.character
                == structure.END_AND_START.character
            ):
                phrase_part0 = copy.deepcopy(restructured_phrase_part)
                phrase_part1 = copy.deepcopy(restructured_phrase_part)
                phrase_part0._bar_character = structure.END
                phrase_part1._bar_character = structure.START
                phrase_part0.duration /= 2
                phrase_part1.duration /= 2
                new_time_signature = abjad.TimeSignature(
                    (
                        int(phrase_part0._time_signature.numerator / 2),
                        phrase_part0._time_signature.denominator,
                    )
                )
                phrase_part0._time_signature = new_time_signature
                phrase_part1._time_signature = new_time_signature
                processed_restructured_phrase_parts.extend((phrase_part0, phrase_part1))

            else:
                processed_restructured_phrase_parts.append(restructured_phrase_part)

        # then split phrases
        split_restructured_phrase_parts = [[]]
        for restructured_phrase_part in processed_restructured_phrase_parts:
            split_restructured_phrase_parts[-1].append(restructured_phrase_part)
            if (
                restructured_phrase_part.bar_character.character
                == structure.END.character
            ):
                split_restructured_phrase_parts.append([])

        return tuple(
            phrase_parts
            for phrase_parts in split_restructured_phrase_parts
            if phrase_parts
        )

    def convert(
        self,
        phrase_to_convert: ot2_basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> typing.Tuple[
        events.basic.SequentialEvent[structure.RestructuredPhrasePart], ...
    ]:
        characters = self._find_characters(len(phrase_to_convert))
        time_signatures = [
            abjad.TimeSignature((int(event.duration * 4), 4))
            for event in phrase_to_convert
        ]
        restructured_phrase_parts = tuple(
            structure.RestructuredPhrasePart(
                phrase_event, bar_character, time_signature
            )
            for phrase_event, bar_character, time_signature in zip(
                phrase_to_convert, characters, time_signatures
            )
        )
        split_restructured_phrase_parts = (
            self._split_restructured_phrase_parts_by_characters(
                restructured_phrase_parts
            )
        )
        return tuple(map(events.basic.SequentialEvent, split_restructured_phrase_parts))


class RiverPhraseToTimeBracketsConverter(base.PhraseToTimeBracketsConverter):
    time_bracket_class = base.RiverCengkokTimeBracket

    def __init__(
        self, *args, percentage_of_single_populated_bars: float = 0.23, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._percentage_of_single_populated_bars = percentage_of_single_populated_bars

    @staticmethod
    def _nth_sustaining_instrument_to_tag(nth_sustaining_instrument: int):
        return (
            ot2_constants.instruments.ID_SUS0,
            ot2_constants.instruments.ID_SUS1,
            ot2_constants.instruments.ID_SUS2,
        )[nth_sustaining_instrument]

    def _make_imbal_based_root_melodies(
        self,
        nth_sustaining_instruments: typing.Tuple[int, int],
        restructured_phrase_parts: typing.Tuple[structure.RestructuredPhrasePart, ...],
        cengkok_line,
        percentage_of_single_populated_bars: float = 0.23,
    ):
        sustaining_instruments = [
            events.basic.TaggedSimultaneousEvent(
                [],
                tag=self._nth_sustaining_instrument_to_tag(nth_sustaining_instrument),
            )
            for nth_sustaining_instrument in nth_sustaining_instruments
        ]
        sines_for_repetition = [
            events.basic.TaggedSimultaneousEvent(
                [],
                tag=ot2_constants.instruments.ID_SUS_TO_ID_SINE[
                    self._nth_sustaining_instrument_to_tag(nth_sustaining_instrument)
                ],
            )
            for nth_sustaining_instrument in nth_sustaining_instruments
        ]

        restructured_phrase_parts_and_cengkok_line_to_imbal_based_root_melodies_converter = imbal.RestructuredPhrasePartsAndCengkokLineToImbalBasedRootMelodiesConverter(
            self._percentage_of_single_populated_bars
        )
        (
            imbal_based_melody0,
            imbal_based_melody1,
        ) = restructured_phrase_parts_and_cengkok_line_to_imbal_based_root_melodies_converter.convert(
            restructured_phrase_parts, cengkok_line
        )

        sustaining_instruments[0].append(imbal_based_melody0.copy())
        sustaining_instruments[1].append(imbal_based_melody1.copy())

        sines_for_repetition[0].append(imbal_based_melody0.copy())
        sines_for_repetition[1].append(imbal_based_melody1.copy())

        return tuple(sustaining_instruments), tuple(sines_for_repetition)

    def _append_simultaneous_events_to_time_brackets(
        self,
        simultaneous_events: typing.Sequence[events.basic.SimultaneousEvent],
        time_brackets: typing.Sequence[base.RiverCengkokTimeBracket],
    ):
        for simultaneous_event in simultaneous_events:
            for time_bracket in time_brackets:
                for destination_tagged_simultaneous_event in time_bracket:
                    found_origin = False
                    for origin_tagged_simultaneous_event in simultaneous_event:
                        if (
                            origin_tagged_simultaneous_event.tag
                            == destination_tagged_simultaneous_event.tag
                        ):
                            for (
                                destination_sequential_event,
                                origin_sequential_event,
                            ) in zip(
                                destination_tagged_simultaneous_event,
                                origin_tagged_simultaneous_event,
                            ):
                                destination_sequential_event.extend(
                                    origin_sequential_event
                                )
                            found_origin = True
                            break
                    if not found_origin:
                        for (
                            destination_sequential_event
                        ) in destination_tagged_simultaneous_event:
                            destination_sequential_event.append(
                                events.basic.SimpleEvent(simultaneous_event.duration)
                            )

    def convert(
        self,
        phrase_to_convert: ot2_basic.SequentialEventWithTempo[
            analysis.phrases.PhraseEvent
        ],
    ) -> typing.Tuple[base.RiverCengkokTimeBracket, ...]:

        phrase_to_restructured_phrase_parts_converter = (
            PhraseToRestructuredPhrasePartsConverter()
        )
        split_restructured_phrase_parts = (
            phrase_to_restructured_phrase_parts_converter.convert(phrase_to_convert)
        )
        restructured_phrase_parts_to_simultaneous_event_converter = (
            CengkokBasedRestructuredPhrasePartsToSimultaneousEventConverter()
        )
        simultaneous_events = []
        for restructured_phrase_parts in split_restructured_phrase_parts:
            simultaneous_events.append(
                restructured_phrase_parts_to_simultaneous_event_converter.convert(
                    restructured_phrase_parts
                )
            )

        for simultaneous_event in simultaneous_events:
            for tagged_sim_ev in simultaneous_event:
                for seq in tagged_sim_ev:
                    durations = seq.get_parameter("duration", flat=True)
                    try:
                        assert all(map(lambda duration: duration > 0, durations))
                    except AssertionError:
                        message = f"""
                        Found invalid sequential event with simple event (duration = 0)
                        in simultaneous_event with tag = '{tagged_sim_ev.tag}'!
                        Removed empty event from sequence."""
                        warnings.warn(message)
                        to_remove_indices = []
                        for idx, ev in enumerate(seq):
                            if not ev.duration:
                                to_remove_indices.append(idx)
                        for idx in reversed(to_remove_indices):
                            del seq[idx]
                    # only for safety. Shouldn't happen actually!! (the generator
                    # functions should return events with the correct duration)
                    difference = simultaneous_event.duration - seq.duration
                    if difference:
                        seq.append(events.basic.SimpleEvent(difference))

        time_bracket_to_notate = self._make_time_bracket_blueprint(phrase_to_convert)
        time_bracket_to_synthesize = self._make_time_bracket_blueprint(
            phrase_to_convert
        )

        for instrument_id, n_voices in (
            # (ot2_constants.instruments.ID_SUS0, 1),
            (ot2_constants.instruments.ID_SUS1, 1),
            # (ot2_constants.instruments.ID_SUS2, 1),
            (ot2_constants.instruments.ID_KEYBOARD, 2),
        ):
            time_bracket_to_notate.append(
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([]) for _ in range(n_voices)],
                    tag=instrument_id,
                )
            )

        time_bracket_to_synthesize.append(
            events.basic.TaggedSimultaneousEvent(
                [events.basic.SequentialEvent([])],
                tag=ot2_constants.instruments.ID_SUS_TO_ID_SINE[
                    ot2_constants.instruments.ID_SUS1
                ],
            )
        )

        self._append_simultaneous_events_to_time_brackets(
            simultaneous_events, (time_bracket_to_notate, time_bracket_to_synthesize)
        )

        (
            imbal_based_parts_for_instruments,
            imbal_based_parts_for_sines,
        ) = self._make_imbal_based_root_melodies((0, 2), phrase_to_convert, [])

        time_bracket_to_notate.insert(0, imbal_based_parts_for_instruments[0])
        time_bracket_to_notate.insert(2, imbal_based_parts_for_instruments[1])
        time_bracket_to_synthesize.extend(imbal_based_parts_for_sines)
        time_bracket_to_synthesize.append(
            events.basic.TaggedSimultaneousEvent(
                [
                    gong.RestructuredPhrasePartsToGongConverter().convert(
                        phrase_to_convert
                    )
                ],
                tag=ot2_constants.instruments.ID_GONG,
            )
        )
        time_bracket_to_synthesize.extend(
            # pillow.SimplePhraseEventsToTaggedSimultaneousEvents().convert(phrase_to_convert)
            pillow.PolyphonicPhraseEventsToTaggedSimultaneousEvents().convert(
                phrase_to_convert
            )
        )
        for tagged_simultaneous_event in time_bracket_to_notate:
            if (
                tagged_simultaneous_event.tag
                in ot2_constants.instruments.ID_SUS_TO_ID_SINE.keys()
            ):
                base.PhraseToTimeBracketsConverter._add_cent_deviation(
                    tagged_simultaneous_event[0]
                )

        time_bracket_to_notate.engine_distribution_strategy = (
            keyboard_converter.ComplexEngineDistributionStrategy(
                keyboard_converter.ByHandsDivisionStrategy(),
                (
                    keyboard_converter.ByActivityLevelDistributionPartStrategy(3, 4, 7),
                    keyboard_converter.ByActivityLevelDistributionPartStrategy(6, 5, 7),
                ),
            )
        )

        return time_bracket_to_notate, time_bracket_to_synthesize
