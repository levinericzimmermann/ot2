import typing

import abjad  # type: ignore
import expenvelope  # type: ignore

from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.parameters import tempos

from ot2.converters.frontends.abjad import base
from ot2.converters.frontends import abjad_constants as ot2_abjad_constants
from ot2.converters.frontends import abjad_process_container_routines as ot2_abjad_process_container_routines
from ot2 import constants as ot2_constants


# ######################################################## #
#   CengkokSimultaneousEventToAbjadStaffGroupConverter     #
# ######################################################## #


class CengkokSimultaneousEventToAbjadStaffGroupConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
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
                search_tree=ot2_abjad_constants.SEARCH_TREE,
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


class CengkokTimeBracketToAbjadScoreBlockConverter(
    base.TimeBracketToAbjadScoreBlockConverter
):
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
                ot2_constants.instruments.ID_SUS0,
                [0],
            ),
            (
                CengkokSustainingInstrumentToAbjadStaffGroupConverter,
                ot2_constants.instruments.ID_SUS1,
                [1],
            ),
            (
                CengkokSustainingInstrumentToAbjadStaffGroupConverter,
                ot2_constants.instruments.ID_SUS2,
                [2],
            ),
            (
                CengkokKeyboardToAbjadStaffGroupConverter,
                ot2_constants.instruments.ID_KEYBOARD,
                [],
            ),
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
        ) + (
            ot2_abjad_process_container_routines.PostProcessCengkokTimeBracket(),
        )
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                tag_to_converter
            ),
            post_process_abjad_container_routines=post_process_abjad_container_routines,
            complex_event_to_abjad_container_name=get_score_name,
        )
