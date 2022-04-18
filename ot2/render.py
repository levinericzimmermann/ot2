"""Script for exporting musical data to scores & sound files

Public interaction via "main" method.
"""


import abjad
import quicktions as fractions

from mutwo.events import basic
from mutwo.events import time_brackets
from mutwo import converters
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import converters as ot2_converters


PLAYING_INDICATORS_CONVERTER = (
    converters.symmetrical.playing_indicators.PlayingIndicatorsConverter(
        [
            converters.symmetrical.playing_indicators.ArpeggioConverter(
                duration_for_each_attack=0.15
            ),
            ot2_converters.symmetrical.playing_indicators.ArticulationConverter(),
        ]
    )
)


def add_names_to_unnamed_scores(abjad_scores_to_post_process):
    nth_unnamed_score = 0
    for score in abjad_scores_to_post_process:
        if not score.items[0].name:
            score.items[0].name = f"unnamed{nth_unnamed_score}"
            nth_unnamed_score += 1


def post_process_common_score_parts(abjad_scores_to_post_process):
    add_names_to_unnamed_scores(abjad_scores_to_post_process)
    abjad_score_names_to_post_process = {
        score.items[0].name: score for score in abjad_scores_to_post_process
    }
    # print(abjad_score_names_to_post_process)
    last_cengkok = abjad_scores_to_post_process[-1]
    for nth_staff_group, staff_group in enumerate(last_cengkok.items[0]):
        for staff in staff_group:
            for voice in staff:
                if nth_staff_group == 0:
                    problematic_bar = voice[19]
                    tuplet0 = problematic_bar[0]
                    for other_tuplet in problematic_bar[1:]:
                        for item in other_tuplet:
                            tuplet0.append(abjad.mutate.copy(item))
                    voice[19] = abjad.Container([abjad.mutate.copy(tuplet0)])
                    # print(problematic_bar[:])
                    problematic_bar = voice[28]
                    problematic_bar[-1] = abjad.Rest(fractions.Fraction(1, 4))
                elif nth_staff_group == 1:
                    problematic_bar = voice[0]
                    problematic_bar[1] = abjad.mutate.copy(problematic_bar[1][0])
                    problematic_bar[1].written_duration = abjad.Duration(1, 4)
                    problematic_bar[1].note_head._written_pitch = voice[1][0][
                        0
                    ].note_head._written_pitch
                    problematic_bar = voice[7]
                    tuplet = problematic_bar[0]
                    problematic_bar[0] = abjad.mutate.copy(tuplet[0])
                    problematic_bar[0].written_duration = abjad.Duration(1, 2)
                    problematic_bar[0].note_head._written_pitch = tuplet[
                        0
                    ].note_head._written_pitch
                """
                last_bar = voice[-2]
                very_last_bar = voice[-1]
                if isinstance(last_bar[0], abjad.Tuplet):
                    last_bar = last_bar[0]
                abjad.attach(
                    abjad.StartTextSpan(
                        left_text=abjad.Markup('\\italic "rit."', direction="up"),
                        direction="up",
                    ),
                    last_bar[0],
                )
                abjad.attach(abjad.StopTextSpan(), very_last_bar[0])
                """


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
                    ev = PLAYING_INDICATORS_CONVERTER.convert(ev)
                    sequential_event.extend(ev)

                event_duration = event.duration
                missing_sequential_events = n_sequential_events - len(event)
                if missing_sequential_events:
                    for sequential_event in simultaneous_event[
                        -missing_sequential_events:
                    ]:
                        sequential_event.append(basic.SimpleEvent(event_duration))

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
    filtered_time_brackets,
    island_to_abjad_score_converter,
    post_process_abjad_scores=lambda abjad_scores: None,
    render_video: bool = False,
):
    abjad_scores = []
    for time_bracket in filtered_time_brackets:
        if isinstance(
            time_bracket,
            (
                ot2_converters.symmetrical.cengkoks.CengkokTimeBracket,
                time_brackets.TempoBasedTimeBracket,
            ),
        ):
            score_converter = ot2_converters.frontends.abjad.CengkokTimeBracketToAbjadScoreBlockConverter(
                time_bracket.time_signatures,
                time_bracket.tempo,
                render_video=render_video,
            )
        else:
            score_converter = island_to_abjad_score_converter

        abjad_score = score_converter.convert(time_bracket)
        abjad_scores.append(abjad_score)
    post_process_abjad_scores(abjad_scores)
    return abjad_scores


def _render_notation_for_instrument(
    filtered_time_brackets,
    island_to_abjad_score_converter,
    instrument,
    post_process_abjad_scores=lambda abjad_scores: None,
):
    if ot2_constants.compute.RENDER_NOTATION:
        score_blocks = _make_score_blocks_for_instrument(
            filtered_time_brackets,
            island_to_abjad_score_converter,
            post_process_abjad_scores,
        )
        lilypond_file_converter = (
            ot2_converters.frontends.abjad.AbjadScoresToLilypondFileConverter(
                instrument_tag=instrument
            )
        )
        lilypond_file = lilypond_file_converter.convert(score_blocks)
        abjad.persist.as_pdf(
            lilypond_file, f"{ot2_constants.paths.NOTATION_PATH}/oT2_{instrument}.pdf"
        )


def _render_video_for_instrument(
    filtered_time_brackets,
    island_to_abjad_score_converter,
    instrument,
    post_process_abjad_scores=lambda abjad_scores: None,
    video_resolution: int = 190,
    delay_between_videos_percentage: float = 0.6,
):
    if ot2_constants.compute.RENDER_VIDEOS:
        # converters.frontends.abjad_video_constants.DEFAULT_RESOLUTION = 230
        converters.frontends.abjad_video_constants.DEFAULT_RESOLUTION = video_resolution
        converters.frontends.abjad_video_constants.DEFAULT_ADDED_X_MARGIN_FOR_COUNT_DOWN = (
            295
        )
        # converters.frontends.abjad_video_constants.DEFAULT_FRAME_IMAGE_ENCODING_FOR_FREE_TIME_BRACKET = "PNG"
        # converters.frontends.abjad_video_constants.DEFAULT_FRAME_IMAGE_WRITE_KWARGS_FOR_FREE_TIME_BRACKET = {}

        score_blocks = _make_score_blocks_for_instrument(
            filtered_time_brackets,
            island_to_abjad_score_converter,
            post_process_abjad_scores,
            render_video=True,
        )
        lilypond_file_converter = (
            ot2_converters.frontends.abjad.AbjadScoresToLilypondFileConverter(
                render_video=True
            )
        )
        lilypond_files = []
        for score_block in score_blocks:
            lilypond_file = lilypond_file_converter.convert([score_block])
            lilypond_files.append(lilypond_file)

        path = f"{ot2_constants.paths.NOTATION_PATH}/oT2_{instrument}_video_score"
        video_converter = converters.frontends.abjad_video.TimeBracketLilypondFilesToVideoConverter(
            # start_render_with_video_index=len(lilypond_files) - 2
            # start_render_with_video_index=35,
            delay_between_videos_percentage=delay_between_videos_percentage,
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
                        ev = PLAYING_INDICATORS_CONVERTER.convert(ev)
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

    keyboard_converter = (
        ot2_converters.symmetrical.keyboard.KeyboardTimeBracketsToAdaptedKeyboardTimeBracketsConverter()
    )
    adapted_filtered_time_brackets = keyboard_converter.convert(filtered_time_brackets)

    for time_bracket in adapted_filtered_time_brackets:
        for tagged_simultaneous_event in time_bracket:
            if tagged_simultaneous_event.tag == ot2_constants.instruments.ID_KEYBOARD:
                tagged_simultaneous_event.mutate_parameter(
                    "notation_indicators",
                    lambda notation_indicators: setattr(
                        notation_indicators.ottava, "n_octaves", 0
                    ),
                )

    _render_notation_for_instrument(
        adapted_filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandKeyboardToAbjadScoreBlockConverter(),
        instrument_id,
        post_process_common_score_parts,
    )
    _render_video_for_instrument(
        adapted_filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandKeyboardToAbjadScoreBlockConverter(
            render_video=True
        ),
        instrument_id,
    )


def _render_nth_sustaining_instrument(nth_sustaining_instrument, make_clarinet_version: bool):
    def post_process_abjad_scores(abjad_scores_to_post_process):
        post_process_common_score_parts(abjad_scores_to_post_process)
        # add dodecaphonic mode to keyboard score
        for abjad_score in abjad_scores_to_post_process:
            for staff_group in abjad_score.items[0]:
                if staff_group.lilypond_type == "PianoStaff":
                    for staff in staff_group:
                        first_leaf = abjad.get.leaf(staff)
                        abjad.attach(
                            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic"),
                            first_leaf,
                        )

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

    video_resolution = 190
    # SPECIAL TREATMENT FOR CLARINET
    if make_clarinet_version and nth_sustaining_instrument == 1:
        # lower resolution for giving enough space for fingerings
        video_resolution = 175
        filtered_time_brackets = tuple(
            map(lambda time_bracket: time_bracket.copy(), filtered_time_brackets)
        )
        for time_bracket in filtered_time_brackets:
            for simultaneous_event in time_bracket:
                if simultaneous_event.tag == instrument_id:
                    for sequential_event in simultaneous_event:
                        for simple_event in sequential_event:
                            ot2_constants.instruments.apply_clarient_fingerings(
                                simple_event
                            )
                        try:
                            sequential_event.set_parameter(
                                "pitch_or_pitches",
                                lambda pitch_or_pitches: [
                                    pitch
                                    + parameters.pitches.JustIntonationPitch("9/8")
                                    for pitch in pitch_or_pitches
                                ]
                                if pitch_or_pitches
                                else None,
                            )
                        # can't set pitch_or_pitches attribute of noise event
                        except AttributeError:
                            pass

    _render_notation_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandSustainingInstrumentToAbjadScoreBlockConverter(
            nth_sustaining_instrument
        ),
        instrument_id,
        post_process_abjad_scores,
    )
    _render_video_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandSustainingInstrumentToAbjadScoreBlockConverter(
            nth_sustaining_instrument, render_video=True
        ),
        instrument_id,
        post_process_abjad_scores,
        video_resolution=video_resolution,
    )


def _render_sustaining_instruments(make_clarinet_version: bool):
    # _render_nth_sustaining_instrument(2)
    for nth_sustaining_instrument in range(3):
        _render_nth_sustaining_instrument(nth_sustaining_instrument, make_clarinet_version)


def _render_csound_drone():
    if ot2_constants.compute.RENDER_SOUNDFILES and ot2_constants.compute.RENDER_DRONE:
        """
        family_of_pitch_curves_to_drone_converter = (
            ot2_converters.symmetrical.drones.FamilyOfPitchCurvesToDroneConverter()
        )
        simultaneous_event = family_of_pitch_curves_to_drone_converter.convert(
            ot2_constants.families_pitch.FAMILY_PITCH
        )
        """

        instrument_id = ot2_constants.instruments.ID_DRONE_SYNTH

        filtered_time_brackets = (
            ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
                ot2_constants.instruments.ID_DRONE_SYNTH
            )
        )

        csound_converter = (
            ot2_converters.frontends.csound.DroneSimultaneousEventToSoundFileConverter()
        )

        _render_soundfile_for_instrument(
            instrument_id,
            filtered_time_brackets,
            csound_converter,
        )


def _render_midi_drone():
    instrument_id = ot2_constants.instruments.ID_DRONE_SYNTH

    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        ot2_constants.instruments.ID_DRONE_SYNTH
    )

    for nth_voice in range(4):
        prepared_filtered_time_brackets = tuple(
            time_bracket[nth_voice : nth_voice + 1]
            for time_bracket in filtered_time_brackets
        )

        midi_converter = ot2_converters.frontends.midi.DroneFofEventToMidiFileConverter(
            nth_voice
        )

        _render_midi_for_instrument(
            instrument_id,
            prepared_filtered_time_brackets,
            midi_converter,
        )


def _render_drone():
    # _render_csound_drone()
    _render_midi_drone()


def _render_sine(instrument_id):
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )

    _render_midi_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_converters.frontends.midi.MonitorSineEventToMidiFileConverter(
            instrument_id
        ),
    )

    if ot2_constants.compute.RENDER_SOUNDFILES and ot2_constants.compute.RENDER_SINES:
        _render_soundfile_for_instrument(
            instrument_id,
            filtered_time_brackets,
            ot2_converters.frontends.csound.SineTonesToSoundFileConverter(
                instrument_id
            ),
        )


def _render_sines():
    for instrument_id in ot2_constants.instruments.ID_SUS_TO_ID_SINE.values():
        _render_sine(instrument_id)


def _render_pillow(instrument_id):
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )

    _render_midi_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_converters.frontends.midi.PillowEventToMidiFileConverter(instrument_id),
    )

    if ot2_constants.compute.RENDER_SOUNDFILES and ot2_constants.compute.RENDER_PILLOW:
        _render_soundfile_for_instrument(
            instrument_id,
            filtered_time_brackets,
            ot2_converters.frontends.csound.PillowEventsToSoundFileConverter(instrument_id),
        )


def _render_pillows():
    for instrument_id in ot2_constants.instruments.PILLOW_IDS:
        _render_pillow(instrument_id)


def _render_common_harmonics():
    from ot2 import common_harmonics

    for name, resulting_sequential_event in common_harmonics.main():
        midi_converter = (
            ot2_converters.frontends.midi.CommonHarmonicEventToMidiFileConverter(name)
        )
        if ot2_constants.compute.RENDER_MIDIFILES:
            midi_converter.convert(resulting_sequential_event)


def _render_gong():
    instrument_id = ot2_constants.instruments.ID_GONG
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )
    _render_midi_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_converters.frontends.midi.GongEventToMidiFileConverter(),
    )


def _render_noise():
    instrument_id = ot2_constants.instruments.ID_NOISE
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        instrument_id
    )

    _render_notation_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandNoiseInstrumentToAbjadScoreBlockConverter(),
        instrument_id,
    )
    _render_video_for_instrument(
        filtered_time_brackets,
        ot2_converters.frontends.abjad.IslandNoiseInstrumentToAbjadScoreBlockConverter(
            render_video=True
        ),
        instrument_id,
        delay_between_videos_percentage=1,
    )


def main(make_clarinet_version: bool = True):
    _render_keyboard()
    # _render_noise()
    _render_drone()
    _render_sustaining_instruments(make_clarinet_version)
    _render_pillows()
    _render_gong()
    _render_common_harmonics()
    _render_sines()
