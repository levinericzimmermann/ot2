"""Script for exporting musical data to scores & sound files

Public interaction via "main" method.
"""


import abjad

from mutwo.converters.symmetrical import time_brackets
from mutwo.events import basic

from ot2.constants import compute
from ot2.constants import instruments
from ot2.constants import families_pitch
from ot2.constants import time_brackets_container
from ot2.converters.frontends import abjad as ot2_abjad
from ot2.converters.frontends import csound as ot2_csound
from ot2.converters.frontends import midi as ot2_midi
from ot2.converters.symmetrical import cengkoks
from ot2.converters.symmetrical import drones


def _render_soundfile_for_instrument(
    instrument_id,
    filtered_time_brackets,
    midi_file_converter,
    return_pitch: bool = False,
):
    if compute.RENDER_MIDIFILES:
        time_brackets_converter = time_brackets.TimeBracketsToEventConverter(instrument_id)
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


def _render_notation_for_instrument(
    filtered_time_brackets, island_to_abjad_score_converter, instrument
):
    if compute.RENDER_NOTATION:
        abjad_scores = []
        for time_bracket in filtered_time_brackets:
            if isinstance(time_bracket, cengkoks.CengkokTimeBracket):
                score_converter = ot2_abjad.CengkokTimeBracketToAbjadScoreConverter(
                    time_bracket.time_signatures, time_bracket.tempo
                )
            else:
                score_converter = island_to_abjad_score_converter

            abjad_score = score_converter.convert(time_bracket)
            abjad_scores.append(abjad_score)

        lilypond_file_converter = ot2_abjad.AbjadScoresToLilypondFileConverter()
        lilypond_file = lilypond_file_converter.convert(abjad_scores)
        abjad.persist.as_pdf(lilypond_file, f"builds/oT2_{instrument}.pdf")


def _render_keyboard():
    def _render_soundfile_for_keyboard(instrument_id, filtered_time_brackets):
        time_brackets_converter = time_brackets.TimeBracketsToEventConverter(
            instrument_id
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
                midi_file_converter = ot2_midi.KeyboardEventToMidiFileConverter(
                    nth_seq_event
                )
                midi_file_converter.convert(sequential_event)

    instrument_id = instruments.ID_KEYBOARD
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    if compute.RENDER_MIDIFILES:
        _render_soundfile_for_keyboard(
            instrument_id, filtered_time_brackets,
        )

    _render_notation_for_instrument(
        filtered_time_brackets,
        ot2_abjad.IslandKeyboardToAbjadScoreConverter(),
        instrument_id,
    )


def _render_nth_sustaining_instrument(nth_sustaining_instrument):
    instrument_id = (instruments.ID_SUS0, instruments.ID_SUS1, instruments.ID_SUS2)[
        nth_sustaining_instrument
    ]
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_midi.SustainingInstrumentEventToMidiFileConverter(
            nth_sustaining_instrument
        ),
        return_pitch=True,
    )

    _render_notation_for_instrument(
        filtered_time_brackets,
        ot2_abjad.IslandSustainingInstrumentToAbjadScoreConverter(
            nth_sustaining_instrument
        ),
        instrument_id,
    )


def _render_sustaining_instruments():
    for nth_sustaining_instrument in range(3):
        _render_nth_sustaining_instrument(nth_sustaining_instrument)


def _render_drone():
    if compute.RENDER_SOUNDFILES:
        family_of_pitch_curves_to_drone_converter = (
            drones.FamilyOfPitchCurvesToDroneConverter()
        )
        simultaneous_event = family_of_pitch_curves_to_drone_converter.convert(
            families_pitch.FAMILY_PITCH
        )

        csound_converter = ot2_csound.DroneSimultaneousEventToSoundFileConverter()
        csound_converter.convert(simultaneous_event)


def _render_sine(instrument_id):
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot2_csound.SineTonesToSoundFileConverter(instrument_id),
    )


def _render_sines():
    if compute.RENDER_SOUNDFILES:
        for instrument_id in instruments.ID_SUS_TO_ID_SINE.values():
            _render_sine(instrument_id)


def _render_common_harmonics():
    from ot2 import common_harmonics

    for name, resulting_sequential_event in common_harmonics.main():
        midi_converter = ot2_midi.CommonHarmonicEventToMidiFileConverter(name)
        midi_converter.convert(resulting_sequential_event)


def main():
    _render_common_harmonics()
    _render_sines()
    _render_keyboard()
    _render_sustaining_instruments()
    _render_drone()
