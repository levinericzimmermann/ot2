import typing

import abjad  # type: ignore
from abjadext import nauert  # type: ignore
import expenvelope  # type: ignore

from mutwo.converters import abc as converters_abc
from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.converters.frontends import abjad_process_container_routines
from mutwo.parameters import tempos

from ot2.constants import instruments
from ot2.converters.frontends import abjad_constants as ot2_abjad_constants
from ot2.converters.frontends import (
    abjad_process_container_routines as ot2_abjad_process_container_routines,
)


class TimeBracketToAbjadScoreConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    def __init__(
        self,
        nested_complex_event_to_complex_event_to_abjad_container_converters_converter: mutwo_abjad.NestedComplexEventToComplexEventToAbjadContainerConvertersConverter,
        complex_event_to_abjad_container_name=lambda complex_event: complex_event.tag,
        post_process_abjad_container_routines: typing.Sequence = tuple([]),
    ):
        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        ) + (abjad_process_container_routines.AddTimeBracketMarks(),)
        super().__init__(
            nested_complex_event_to_complex_event_to_abjad_container_converters_converter,
            abjad.Score,
            "Score",
            complex_event_to_abjad_container_name,
            [],
            post_process_abjad_container_routines,
        )


# ######################################################## #
#                      OTHER                               #
# ######################################################## #


class MutwoPitchToDiatonicAbjadPitchConverter(
    mutwo_abjad.MutwoPitchToAbjadPitchConverter
):
    def convert(self, pitch_to_convert):
        abjad_pitch = super().convert(pitch_to_convert)
        return abjad.NamedPitch(round(abjad_pitch.number))


# ######################################################## #
#     IslandSimultaneousEventToAbjadStaffGroupConverter    #
# ######################################################## #


class IslandSimultaneousEventToAbjadStaffGroupConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    def __init__(
        self,
        post_process_abjad_container_routines: typing.Sequence = [],
        lilypond_type_of_abjad_container: str = "StaffGroup",
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    ):
        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.SequentialEventToDurationLineBasedQuantizedAbjadContainerConverter(),
            mutwo_pitch_to_abjad_pitch_converter=mutwo_pitch_to_abjad_pitch_converter,
            tempo_envelope_to_abjad_attachment_tempo_converter=None,
            write_multimeasure_rests=False,
        )
        super().__init__(
            mutwo_abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                (sequential_event_to_abjad_voice_converter,)
            ),
            abjad.StaffGroup,
            lilypond_type_of_abjad_container,
            pre_process_abjad_container_routines=[],
            post_process_abjad_container_routines=post_process_abjad_container_routines,
        )


class IslandKeyboardToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self):
        super().__init__(
            post_process_abjad_container_routines=[
                ot2_abjad_process_container_routines.KeyboardMixin()
            ],
            lilypond_type_of_abjad_container="PianoStaff",
            mutwo_pitch_to_abjad_pitch_converter=MutwoPitchToDiatonicAbjadPitchConverter(),
        )


class IslandSustainingInstrumentToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self, nth_sustaining_instrument: int = 0):
        sustaining_instrument_mixin = ot2_abjad_process_container_routines.SustainingInstrumentMixin(
            nth_sustaining_instrument
        )
        self._instrument_id = sustaining_instrument_mixin._instrument_id
        super().__init__(
            post_process_abjad_container_routines=[sustaining_instrument_mixin],
        )


class IslandDroneToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self):
        super().__init__(
            post_process_abjad_container_routines=[
                ot2_abjad_process_container_routines.DroneMixin()
            ],
        )


# ######################################################## #
#         IslandTimeBracketToAbjadScoreConverter           #
# ######################################################## #


class IslandTimeBracketToAbjadScoreConverter(TimeBracketToAbjadScoreConverter):
    _nth_island_counter = 0

    def __init__(
        self,
        nested_complex_event_to_complex_event_to_abjad_container_converters_converter: mutwo_abjad.NestedComplexEventToComplexEventToAbjadContainerConvertersConverter,
        post_process_abjad_container_routines: typing.Sequence = tuple([]),
    ):
        def get_score_name(_):
            score_name = f"islandScore{self._nth_island_counter}"
            self._nth_island_counter += 1
            return score_name

        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        ) + (ot2_abjad_process_container_routines.PostProcessIslandTimeBracket(),)

        super().__init__(
            nested_complex_event_to_complex_event_to_abjad_container_converters_converter,
            get_score_name,
            post_process_abjad_container_routines,
        )


class IslandKeyboardToAbjadScoreConverter(IslandTimeBracketToAbjadScoreConverter):
    def __init__(self):
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {instruments.ID_KEYBOARD: IslandKeyboardToAbjadStaffGroupConverter()}
            )
        )


class IslandSustainingInstrumentToAbjadScoreConverter(
    IslandTimeBracketToAbjadScoreConverter
):
    def __init__(self, nth_sustaining_instrument: int):
        island_sustaining_instrument_to_abjad_staff_group_converter = IslandSustainingInstrumentToAbjadStaffGroupConverter(
            nth_sustaining_instrument
        )
        drone_to_abjad_staff_group_converter = IslandDroneToAbjadStaffGroupConverter()
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    island_sustaining_instrument_to_abjad_staff_group_converter._instrument_id: island_sustaining_instrument_to_abjad_staff_group_converter,
                    instruments.ID_DRONE: drone_to_abjad_staff_group_converter,
                }
            )
        )


# ######################################################## #
#   CengkokSimultaneousEventToAbjadStaffGroupConverter     #
# ######################################################## #


class CengkokSimultaneousEventToAbjadStaffGroupConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):

    _search_tree = nauert.UnweightedSearchTree(
        definition={
            2: {
                2: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
                3: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
            },
            3: {
                2: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
                3: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
            },
        },
    )

    def __init__(
        self,
        time_signatures: typing.Sequence[abjad.TimeSignature],
        tempo_point: tempos.TempoPoint,
        post_process_abjad_container_routines: typing.Sequence = [],
        lilypond_type_of_abjad_container: str = "StaffGroup",
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    ):
        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        ) + (
            ot2_abjad_process_container_routines.PostProcessCengkokSimultaneousEvent(),
        )
        tempo_envelope = expenvelope.Envelope.from_points(
            (0, tempo_point), (10, tempo_point)
        )
        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
                time_signatures=time_signatures,
                tempo_envelope=tempo_envelope,
                search_tree=self._search_tree,
            ),
            mutwo_pitch_to_abjad_pitch_converter=mutwo_pitch_to_abjad_pitch_converter,
        )
        super().__init__(
            mutwo_abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                (sequential_event_to_abjad_voice_converter,)
            ),
            abjad.StaffGroup,
            lilypond_type_of_abjad_container,
            pre_process_abjad_container_routines=[],
            post_process_abjad_container_routines=post_process_abjad_container_routines,
        )


class CengkokKeyboardToAbjadStaffGroupConverter(
    CengkokSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(
        self,
        time_signatures: typing.Sequence[abjad.TimeSignature],
        tempo_point: tempos.TempoPoint,
    ):
        super().__init__(
            time_signatures,
            tempo_point,
            post_process_abjad_container_routines=[
                ot2_abjad_process_container_routines.KeyboardMixin()
            ],
            lilypond_type_of_abjad_container="PianoStaff",
        )


class CengkokSustainingInstrumentToAbjadStaffGroupConverter(
    CengkokSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(
        self,
        nth_sustaining_instrument,
        time_signatures: typing.Sequence[abjad.TimeSignature],
        tempo_point: tempos.TempoPoint,
    ):
        super().__init__(
            time_signatures,
            tempo_point,
            post_process_abjad_container_routines=[
                ot2_abjad_process_container_routines.SustainingInstrumentMixin(
                    nth_sustaining_instrument
                )
            ],
        )


# ######################################################## #
#        CengkokTimeBracketToAbjadScoreConverter           #
# ######################################################## #


class CengkokTimeBracketToAbjadScoreConverter(TimeBracketToAbjadScoreConverter):
    nth_score_counter = 0

    def __init__(
        self,
        time_signatures: typing.Sequence[abjad.TimeSignature],
        tempo_point: tempos.TempoPoint,
        post_process_abjad_container_routines: typing.Sequence = [],
    ):
        def get_score_name(_):
            score_name = f"cengkokScore{self._nth_score_counter}"
            self._nth_score_counter += 1
            return score_name

        tag_to_converter = {}
        for converter_class, instrument_id, convert_class_arguments in (
            (
                CengkokSustainingInstrumentToAbjadStaffGroupConverter,
                instruments.ID_SUS0,
                [0],
            ),
            (
                CengkokSustainingInstrumentToAbjadStaffGroupConverter,
                instruments.ID_SUS1,
                [1],
            ),
            (
                CengkokSustainingInstrumentToAbjadStaffGroupConverter,
                instruments.ID_SUS2,
                [2],
            ),
            (CengkokKeyboardToAbjadStaffGroupConverter, instruments.ID_KEYBOARD, []),
        ):
            converter_instance = converter_class(
                *convert_class_arguments,
                time_signatures=time_signatures,
                tempo_point=tempo_point,
            )
            tag = instrument_id
            tag_to_converter.update({tag: converter_instance})

        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        ) + (ot2_abjad_process_container_routines.PostProcessCengkokTimeBracket(),)
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                tag_to_converter
            ),
            post_process_abjad_container_routines=post_process_abjad_container_routines,
            complex_event_to_abjad_container_name=get_score_name,
        )


# ######################################################## #
#            AbjadScoresToLilypondFileConverter            #
# ######################################################## #


class AbjadScoresToLilypondFileConverter(converters_abc.Converter):
    def __init__(
        self,
        instrument: typing.Optional[str] = None,
        paper_format: ot2_abjad_constants.PaperFormat = ot2_abjad_constants.A4,
        margin: float = 4,
    ):
        self._instrument = instrument
        self._paper_format = paper_format
        self._margin = margin

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
            header_block.instrument = instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[
                instrument
            ]
        return header_block

    @staticmethod
    def _make_paper_block() -> abjad.Block:
        paper_block = abjad.Block("paper")
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

    @staticmethod
    def _make_layout_block(margin: int) -> abjad.Block:
        layout_block = abjad.Block("layout")
        layout_block.items.append(r"short-indent = {}\mm".format(margin))
        layout_block.items.append(r"ragged-last = ##f")
        # layout_block.items.append(r"indent = 23\mm")
        layout_block.items.append(r"indent = {}\mm".format(margin))
        # layout_block.items.append(
        #     r"\override StaffGroup.BarLine.hair-thickness = 0.0001"
        # )
        return layout_block

    def convert(self, abjad_scores: typing.Sequence[abjad.Score]) -> abjad.LilyPondFile:
        lilypond_file = abjad.LilyPondFile(
            includes=["ekme-heji-ref-c.ily"], default_paper_size=self._paper_format.name
        )

        for abjad_score in abjad_scores:
            lilypond_file.items.append(abjad_score)
            # score_block = abjad.Block("score")
            # score_block.items.append(abjad_score)

        # lilypond_file.items.append(score_block)
        lilypond_file.items.append(
            AbjadScoresToLilypondFileConverter._make_header_block(self._instrument)
        )
        lilypond_file.items.append(
            AbjadScoresToLilypondFileConverter._make_layout_block(self._margin)
        )
        lilypond_file.items.append(
            AbjadScoresToLilypondFileConverter._make_paper_block()
        )

        return lilypond_file
