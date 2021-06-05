import abc
import typing

import abjad
import expenvelope

from ot2.converters.frontends import abjad as ot2_abjad
from ot2.events import bars
from ot2.events import basic


class PartMaker(abc.ABC):
    # ################################################## #
    #             predefined methods                     #
    # ################################################## #

    def make_abjad_score(
        self,
        tagged_simultaneous_event: basic.TaggedSimultaneousEvent,
        generated_bars: typing.Tuple[bars.Bar, ...],
        tempo_envelope: expenvelope.Envelope,
    ) -> abjad.Score:
        abjad_score_converter = ot2_abjad.TaggedSimultaneousEventToAbjadScoreConverter(
            tuple(abjad.TimeSignature(bar.time_signature) for bar in generated_bars),
            tempo_envelope,
        )
        abjad_score = abjad_score_converter.convert(tagged_simultaneous_event)
        return abjad_score

    def __call__(self) -> typing.Tuple[basic.TaggedSimultaneousEvent, abjad.Score]:
        tagged_simultaneous_event, generated_bars, tempo_envelope = self.make_mutwo()
        (
            tagged_simultaneous_event,
            generated_bars,
            tempo_envelope,
        ) = self.post_process_mutwo(
            tagged_simultaneous_event, generated_bars, tempo_envelope
        )
        abjad_score = self.make_abjad_score(
            tagged_simultaneous_event, generated_bars, tempo_envelope
        )
        abjad_score = self.post_process_abjad(abjad_score)
        return tagged_simultaneous_event, abjad_score, tempo_envelope

    # ################################################## #
    #          methods which have to be overriden        #
    # ################################################## #

    def make_mutwo(
        self,
    ) -> typing.Tuple[
        basic.TaggedSimultaneousEvent, typing.Tuple[bars.Bar, ...], expenvelope.Envelope
    ]:
        raise NotImplementedError()

    # ################################################## #
    #           methods which can be overriden           #
    # ################################################## #

    def post_process_mutwo(
        self,
        tagged_simultaneous_event: basic.TaggedSimultaneousEvent,
        generated_bars: typing.Tuple[bars.Bar, ...],
        tempo_envelope: expenvelope.Envelope,
    ) -> typing.Tuple[
        basic.TaggedSimultaneousEvent, typing.Tuple[bars.Bar, ...], expenvelope.Envelope
    ]:
        return tagged_simultaneous_event, generated_bars, tempo_envelope

    def post_process_abjad(self, abjad_score: abjad.Score) -> abjad.Score:
        return abjad_score
