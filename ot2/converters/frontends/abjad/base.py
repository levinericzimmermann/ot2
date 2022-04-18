import typing

import abjad  # type: ignore

from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.converters.frontends import abjad_process_container_routines


class TimeBracketToAbjadScoreBlockConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    def __init__(
        self,
        nested_complex_event_to_complex_event_to_abjad_container_converters_converter: mutwo_abjad.NestedComplexEventToComplexEventToAbjadContainerConvertersConverter,
        complex_event_to_abjad_container_name=lambda complex_event: complex_event.tag,
        post_process_abjad_container_routines: typing.Sequence = tuple([]),
        margin: float = 4,
        render_video: bool = False,
    ):
        self.render_video = render_video
        self._margin = margin
        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        )
        if not self.render_video:
            post_process_abjad_container_routines += (
                abjad_process_container_routines.AddTimeBracketMarks(),
            )
        super().__init__(
            nested_complex_event_to_complex_event_to_abjad_container_converters_converter,
            abjad.Score,
            "Score",
            complex_event_to_abjad_container_name,
            [],
            post_process_abjad_container_routines,
        )

    @property
    def layout_block(self) -> abjad.Block:
        layout_block = abjad.Block("layout")
        layout_block.items.append(r"short-indent = {}\mm".format(self._margin))
        layout_block.items.append(r"ragged-last = ##f")
        layout_block.items.append(r"indent = {}\mm".format(self._margin))
        return layout_block

    @property
    def midi_block(self) -> abjad.Block:
        return abjad.Block(name="midi")

    def convert(self, *args, **kwargs) -> abjad.Block:
        score = super().convert(*args, **kwargs)
        score_block = abjad.Block(name="score")
        score_block.items.append(score)
        if not self.render_video:
            score_block.items.append(self.layout_block)
        # if self.render_video:
        #     score_block.items.append(self.midi_block)
        return score_block


# ######################################################## #
#                      OTHER                               #
# ######################################################## #


class MutwoPitchToDiatonicAbjadPitchConverter(
    mutwo_abjad.MutwoPitchToAbjadPitchConverter
):
    def convert(self, pitch_to_convert):
        abjad_pitch = super().convert(pitch_to_convert)
        return abjad.NamedPitch(round(abjad_pitch.number))
