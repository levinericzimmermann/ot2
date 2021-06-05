import typing

import expenvelope

from ot2.converters import symmetrical
from ot2.events import basic
from ot2.events import bars
from ot2.generators import zimmermann
from ot2.parts import abc


class DummyPart(abc.PartMaker):
    def make_mutwo(
        self,
    ) -> typing.Tuple[
        basic.TaggedSimultaneousEvent, typing.Tuple[bars.Bar, ...], expenvelope.Envelope
    ]:
        converter = symmetrical.music.DummyDataToMusicConverter()
        return converter.convert(
            zimmermann.LoopBarsConverter(0, (4, 4, 6), 6, 1, 3, 4, 15),
            symmetrical.bars.SymmetricalPermutationBasedBarsToBarsWithHarmonyConverter(
                zimmermann.SymmetricalPermutation(13, (1, 3, 9, 7))
            ),
        )
