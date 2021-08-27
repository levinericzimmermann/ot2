import typing

import abjad  # type: ignore

from mutwo.converters import abc as converters_abc

from ot2.converters.frontends import abjad_constants
from ot2 import constants as ot2_constants

from . import settings


# ######################################################## #
#            AbjadScoresToLilypondFileConverter            #
# ######################################################## #


class AbjadScoresToLilypondFileConverter(converters_abc.Converter):
    def __init__(
        self,
        instrument: typing.Optional[str] = None,
        paper_format: abjad_constants.PaperFormat = abjad_constants.A4,
    ):
        self._instrument = instrument
        self._paper_format = paper_format

    def _stress_instrument(self, abjad_score: abjad.Score):
        pass

    @staticmethod
    def _make_header_block(instrument: typing.Optional[str]) -> abjad.Block:
        header_block = abjad.Block("header")
        header_block.title = '"ohne Titel (2)"'
        header_block.year = '"2021"'
        header_block.composer = '"Levin Eric Zimmermann"'
        header_block.tagline = '"oT(2) // 2021"'
        if instrument:
            header_block.instrument = (
                ot2_constants.instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[
                    instrument
                ]
            )
        return header_block

    @staticmethod
    def _make_paper_block() -> abjad.Block:
        paper_block = abjad.Block("paper")
        if not settings.USE_VIDEO_SETTINGS:
            paper_block.items.append(
                r"""#(define fonts
        (make-pango-font-tree "EB Garamond"
                            "Nimbus Sans"
                            "Luxi Mono"
                            (/ staff-height pt 20)))"""
            )
            paper_block.items.append(
                r"""score-system-spacing =
        #'((basic-distance . 30)
        (minimum-distance . 18)
        (padding . 1)
        (stretchability . 12))"""
            )
        return paper_block

    def convert(self, abjad_scores: typing.Sequence[abjad.Block]) -> abjad.LilyPondFile:
        lilypond_file = abjad.LilyPondFile(
            includes=["ekme-heji-ref-c-not-tuned.ily"],
            default_paper_size=self._paper_format.name,
        )

        for abjad_score in abjad_scores:
            lilypond_file.items.append(abjad_score)

        if not settings.USE_VIDEO_SETTINGS:
            lilypond_file.items.append(
                AbjadScoresToLilypondFileConverter._make_header_block(self._instrument)
            )
        lilypond_file.items.append(
            AbjadScoresToLilypondFileConverter._make_paper_block()
        )

        lilypond_file.items.append("\\pointAndClickOff\n")

        return lilypond_file
