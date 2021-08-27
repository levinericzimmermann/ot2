"""Script for exporting musical data to scores & sound files

Public interaction via "main" method.
"""


import abjad

from mutwo.events import basic
from mutwo import converters

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters


def _render_soundfile_or_midi_file_for_instrument(
    instrument_id,
    filtered_time_brackets,
    midi_file_converter,
    return_pitch: bool = False,
):
    time_brackets_converter = (
        converters.symmetrical.time_brackets.TimeBracketsToEventConverter(instrument_id)
    )
    converted_time_brackets = time_brackets_converter.convert(filtered_time_brackets)
    if converted_time_brackets:
        n_sequential_events = max(
            len(simultaneous_event)
            for simultaneous_event in converted_time_brackets
            if isinstance(simultaneous_event, basic.SimultaneousEvent)
        )
        simultaneous_event = basic.SimultaneousEvent(
            [basic.SequentialEvent([]) for _ in range(n_sequential_events)]
        )
        for event in converted_time_brackets:
            if isinstance(event, basic.SimpleEvent):
                rest = basic.SimpleEvent(event.duration)
                for seq in simultaneous_event:
                    seq.append(rest)
            else:
                for ev, sequential_event in zip(event, simultaneous_event):
                    sequential_event.extend(ev)

        if return_pitch:
            simultaneous_event.set_parameter("return_pitch", True)

        midi_file_converter.convert(simultaneous_event)


def _render_soundfile_for_instrument(
    instrument_id,
    filtered_time_brackets,
    midi_file_converter,
    return_pitch: bool = False,
):
    if ot2_constants.compute.RENDER_SOUNDFILES:
        _render_soundfile_or_midi_file_for_instrument(
            instrument_id,
            filtered_time_brackets,
            midi_file_converter,
            return_pitch=return_pitch,
        )


def _render_midi_for_instrument(
    instrument_id,
    filtered_time_brackets,
    midi_file_converter,
    return_pitch: bool = False,
):
    if ot2_constants.compute.RENDER_MIDIFILES:
        _render_soundfile_or_midi_file_for_instrument(
            instrument_id,
            filtered_time_brackets,
            midi_file_converter,
            return_pitch=return_pitch,
        )


def _make_score_blocks_for_instrument(
    filtered_time_brackets, island_to_abjad_score_converter
):
    abjad_scores = []
    for time_bracket in filtered_time_brackets:
        if isinstance(
            time_bracket, ot2_converters.symmetrical.cengkoks.CengkokTimeBracket
        ):
            score_converter = ot2_converters.frontends.abjad.CengkokTimeBracketToAbjadScoreBlockConverter(
                time_bracket.time_signatures, time_bracket.tempo
            )
        else:
            score_converter = island_to_abjad_score_converter

        abjad_score = score_converter.convert(time_bracket)
        abjad_scores.append(abjad_score)
    return abjad_scores


def _render_notation_for_instrument(
    filtered_time_brackets, island_to_abjad_score_converter, instrument
):
    if ot2_constants.compute.RENDER_NOTATION:
        score_blocks = _make_score_blocks_for_instrument(
            filtered_time_brackets, island_to_abjad_score_converter
        )
        lilypond_file_converter = (
            ot2_converters.frontends.abjad.AbjadScoresToLilypondFileConverter()
        )
        lilypond_file = lilypond_file_converter.convert(score_blocks)
        abjad.persist.as_pdf(
            lilypond_file, f"{ot2_constants.paths.NOTATION_PATH}/oT2_{instrument}.pdf"
        )


def _render_video_for_instrument(
    filtered_time_brackets, island_to_abjad_score_converter, instrument
):
    if ot2_constants.compute.RENDER_VIDEOS:
        converters.frontends.abjad_video_constants.DEFAULT_RESOLUTION = 230
        converters.frontends.abjad_video_constants.DEFAULT_ADDED_X_MARGIN_FOR_COUNT_DOWN = (
            295
        )
        # converters.frontends.abjad_video_constants.DEFAULT_FRAME_IMAGE_ENCODING_FOR_FREE_TIME_BRACKET = "PNG"
        # converters.frontends.abjad_video_constants.DEFAULT_FRAME_IMAGE_WRITE_KWARGS_FOR_FREE_TIME_BRACKET = {}

        score_blocks = _make_score_blocks_for_instrument(
            filtered_time_brackets, island_to_abjad_score_converter
        )
        lilypond_file_converter = (
            ot2_converters.frontends.abjad.AbjadScoresToLilypondFileConverter()
        )
        lilypond_files = []
        for score_block in score_blocks:
            lilypond_file = lilypond_file_converter.convert([score_block])
            lilypond_files.append(lilypond_file)

        path = f"{ot2_constants.paths.NOTATION_PATH}/oT2_{instrument}_video_score"
        video_converter = (
            converters.frontends.abjad_video.TimeBracketLilypondFilesToVideoConverter()
        )
        video_converter.convert(
            path,
            filtered_time_brackets,
            lilypond_files,
        )


def _render_keyboard():
    def _render_soundfile_for_keyboard(instrument_id, filtered_time_brackets):
        time_brackets_converter = (
            converters.symmetrical.time_brackets.TimeBracketsToEventConverter(
                instrument_id
            )
        )
        converted_time_brackets = time_brackets_converter.convert(
            filtered_time_brackets
        )
        if converted_time_brackets:
            n_sequential_events = max(
                len(simultaneous_event)
                for simultaneous_event in converted_time_brackets
                if isinstance(simultaneous_event, basic.SimultaneousEvent)
            )
            simultaneous_event = basic.SimultaneousEvent(
                [basic.SequentialEvent([]) for _ in range(n_sequential_events)]
            )
            for event in converted_time_brackets:
                if isinstance(event, basic.SimpleEvent):
                    rest = basic.SimpleEvent(event.duration)
                    for seq in simultaneous_event:
                        seq.append(rest)
                else:
                    for ev, sequential_event in zip(event, simultaneous_event):
                        sequential_event.extend(ev)
            for nth_seq_event, sequential_event in enumerate(simultaneous_event):
                midi_file_converter = (
                    ot2_converters.frontends.midi.KeyboardEventToMidiFileConverter(
                        nth_seq_event
                    )
                )
                midi_file_converter.convert(sequential_event)

    instrument_id = ot2_constants.instruments.ID_KEYBOARD
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )

    if ot2_constants.compute.RENDER_MIDIFILES:
        _render_soundfile_for_keyboard(
            instrument_id,
            filtered_time_brackets,
        )

    _render_notation_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandKeyboardToAbjadScoreBlockConverter(),
        instrument_id,
    )
    _render_video_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandKeyboardToAbjadScoreBlockConverter(),
        instrument_id,
    )


def _render_nth_sustaining_instrument(nth_sustaining_instrument):
    instrument_id = (
        ot2_constants.instruments.ID_SUS0,
        ot2_constants.instruments.ID_SUS1,
        ot2_constants.instruments.ID_SUS2,
    )[nth_sustaining_instrument]
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )

    _render_midi_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_converters.frontends.midi.SustainingInstrumentEventToMidiFileConverter(
            nth_sustaining_instrument
        ),
        return_pitch=True,
    )

    _render_notation_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandSustainingInstrumentToAbjadScoreBlockConverter(
            nth_sustaining_instrument
        ),
        instrument_id,
    )
    _render_video_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandSustainingInstrumentToAbjadScoreBlockConverter(
            nth_sustaining_instrument
        ),
        instrument_id,
    )


def _render_sustaining_instruments():
    for nth_sustaining_instrument in range(3):
        _render_nth_sustaining_instrument(nth_sustaining_instrument)


def _render_drone():
    if ot2_constants.compute.RENDER_SOUNDFILES:
        family_of_pitch_curves_to_drone_converter = (
            ot2_converters.symmetrical.drones.FamilyOfPitchCurvesToDroneConverter()
        )
        simultaneous_event = family_of_pitch_curves_to_drone_converter.convert(
            ot2_constants.families_pitch.FAMILY_PITCH
        )

        csound_converter = (
            ot2_converters.frontends.csound.DroneSimultaneousEventToSoundFileConverter()
        )
        csound_converter.convert(simultaneous_event)


def _render_sine(instrument_id):
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_converters.frontends.csound.SineTonesToSoundFileConverter(instrument_id),
    )


def _render_sines():
    if ot2_constants.compute.RENDER_SOUNDFILES:
        for instrument_id in ot2_constants.instruments.ID_SUS_TO_ID_SINE.values():
            _render_sine(instrument_id)


def _render_common_harmonics():
    from ot2 import common_harmonics

    for name, resulting_sequential_event in common_harmonics.main():
        midi_converter = (
            ot2_converters.frontends.midi.CommonHarmonicEventToMidiFileConverter(name)
        )
        if ot2_constants.compute.RENDER_MIDIFILES:
            midi_converter.convert(resulting_sequential_event)


def main():
    _render_common_harmonics()
    _render_sines()
    _render_keyboard()
    _render_sustaining_instruments()
    _render_drone()
