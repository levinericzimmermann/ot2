from mutwo import parameters


def _get_diatonic_and_chromatic_pitches():
    diatonic_pitches = []
    chromatic_pitches = []
    for midi_pitch_number in range(
        LOWEST_ALLOWED_MIDI_NOTE, HIGHEST_ALLOWED_MIDI_NOTE + 1
    ):
        western_pitch = parameters.pitches.WesternPitch.from_midi_pitch_number(
            midi_pitch_number
        )
        if len(western_pitch.pitch_class_name) > 1:
            chromatic_pitches.append(midi_pitch_number)
        else:
            diatonic_pitches.append(midi_pitch_number)
    return tuple(diatonic_pitches), tuple(chromatic_pitches)


LOWEST_ALLOWED_MIDI_NOTE = 24
HIGHEST_ALLOWED_MIDI_NOTE = 107  # 108 should also be possible

DIATONIC_PITCHES, CHROMATIC_PITCHES = _get_diatonic_and_chromatic_pitches()
