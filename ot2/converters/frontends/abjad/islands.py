import typing

import abjad  # type: ignore

from mutwo.converters.frontends import abjad as mutwo_abjad

from ot2.converters.frontends.abjad import base
from ot2.converters.frontends import abjad_process_container_routines as ot2_abjad_process_container_routines
from ot2 import constants as ot2_constants


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
            mutwo_pitch_to_abjad_pitch_converter=base.MutwoPitchToDiatonicAbjadPitchConverter(),
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
#         IslandTimeBracketToAbjadScoreBlockConverter      #
# ######################################################## #


class IslandTimeBracketToAbjadScoreBlockConverter(
    base.TimeBracketToAbjadScoreBlockConverter
):
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
        ) + (
            ot2_abjad_process_container_routines.PostProcessIslandTimeBracket(),
        )

        super().__init__(
            nested_complex_event_to_complex_event_to_abjad_container_converters_converter,
            get_score_name,
            post_process_abjad_container_routines,
        )


class IslandKeyboardToAbjadScoreBlockConverter(
    IslandTimeBracketToAbjadScoreBlockConverter
):
    def __init__(self):
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    ot2_constants.instruments.ID_KEYBOARD: IslandKeyboardToAbjadStaffGroupConverter()
                }
            )
        )


class IslandSustainingInstrumentToAbjadScoreBlockConverter(
    IslandTimeBracketToAbjadScoreBlockConverter
):
    def __init__(self, nth_sustaining_instrument: int):
        island_sustaining_instrument_to_abjad_staff_group_converter = (
            IslandSustainingInstrumentToAbjadStaffGroupConverter(
                nth_sustaining_instrument
            )
        )
        drone_to_abjad_staff_group_converter = IslandDroneToAbjadStaffGroupConverter()
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    island_sustaining_instrument_to_abjad_staff_group_converter._instrument_id: island_sustaining_instrument_to_abjad_staff_group_converter,
                    ot2_constants.instruments.ID_DRONE: drone_to_abjad_staff_group_converter,
                }
            )
        )
