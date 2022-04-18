import typing

import abjad  # type: ignore

from mutwo.converters.frontends import abjad as mutwo_abjad

from ot2.converters.frontends.abjad import base
from ot2.converters.frontends import (
    abjad_process_container_routines as ot2_abjad_process_container_routines,
)
from ot2 import constants as ot2_constants


# ######################################################## #
#     IslandSimultaneousEventToAbjadStaffGroupConverter    #
# ######################################################## #


class SequentialEventToAbjadStaffConverter(
    mutwo_abjad.SequentialEventToAbjadVoiceConverter
):
    def convert(self, *args, **kwargs):
        abjad_voice = super().convert(*args, **kwargs)
        return abjad.Staff([abjad_voice])


class IslandSimultaneousEventToAbjadStaffGroupConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    def __init__(
        self,
        post_process_abjad_container_routines: typing.Sequence = [],
        lilypond_type_of_abjad_container: str = "StaffGroup",
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
    ):
        self._mutwo_pitch_to_abjad_pitch_converter = (
            mutwo_pitch_to_abjad_pitch_converter
        )
        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.SequentialEventToDurationLineBasedQuantizedAbjadContainerConverter(
                time_signatures=(abjad.TimeSignature((1, 4)),)
            ),
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

    def convert(self, *args, **kwargs):
        duration = args[0].duration
        n_fours = int(duration * 4)
        time_signatures = (abjad.TimeSignature((n_fours, 4)),)
        # if n_fours != 11:
        #     time_signatures = (abjad.TimeSignature((n_fours, 4)),)
        # else:
        #     time_signatures = (
        #         abjad.TimeSignature((6, 4)),
        #         abjad.TimeSignature((5, 4)),
        #     )
        sequential_event_to_abjad_voice_converter = SequentialEventToAbjadStaffConverter(
            mutwo_abjad.FastSequentialEventToDurationLineBasedQuantizedAbjadContainerConverter(
                time_signatures=time_signatures, do_rewrite_meter=False
            ),
            mutwo_pitch_to_abjad_pitch_converter=self._mutwo_pitch_to_abjad_pitch_converter,
            tempo_envelope_to_abjad_attachment_tempo_converter=None,
            write_multimeasure_rests=False,
        )
        self._nested_complex_event_to_complex_event_to_abjad_container_converters_converter = mutwo_abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
            (sequential_event_to_abjad_voice_converter,)
        )
        abjad_staff_group = super().convert(*args, **kwargs)
        for staff in abjad_staff_group:
            abjad.attach(time_signatures[0], abjad.get.leaf(staff))
        return abjad_staff_group


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
        sustaining_instrument_mixin = (
            ot2_abjad_process_container_routines.SustainingInstrumentMixin(
                nth_sustaining_instrument
            )
        )
        self._instrument_id = sustaining_instrument_mixin._instrument_id
        super().__init__(
            post_process_abjad_container_routines=[sustaining_instrument_mixin],
        )


class IslandNoiseInstrumentToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self):
        noise_instrument_mixin = (
            ot2_abjad_process_container_routines.NoiseInstrumentMixin()
        )
        self._instrument_id = ot2_constants.instruments.ID_NOISE
        super().__init__(
            post_process_abjad_container_routines=[noise_instrument_mixin],
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
        **kwargs,
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
            **kwargs,
        )


class IslandKeyboardToAbjadScoreBlockConverter(
    IslandTimeBracketToAbjadScoreBlockConverter
):
    def __init__(self, **kwargs):

        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    ot2_constants.instruments.ID_KEYBOARD: IslandKeyboardToAbjadStaffGroupConverter()
                }
            ),
            **kwargs,
        )


class IslandSustainingInstrumentToAbjadScoreBlockConverter(
    IslandTimeBracketToAbjadScoreBlockConverter
):
    def __init__(self, nth_sustaining_instrument: int, **kwargs):
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
            ),
            **kwargs,
        )


class IslandNoiseInstrumentToAbjadScoreBlockConverter(
    IslandTimeBracketToAbjadScoreBlockConverter
):
    def __init__(self, **kwargs):
        island_noise_instrument_to_abjad_staff_group_converter = (
            IslandNoiseInstrumentToAbjadStaffGroupConverter()
        )
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    island_noise_instrument_to_abjad_staff_group_converter._instrument_id: island_noise_instrument_to_abjad_staff_group_converter,
                }
            ),
            **kwargs,
        )
