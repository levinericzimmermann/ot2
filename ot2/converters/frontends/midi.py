import expenvelope

from ot2.constants import instruments

from mutwo.converters.frontends import midi
from mutwo.converters import symmetrical
from mutwo.events import abc


class OT2InstrumentEventToMidiFileConverter(midi.MidiFileConverter):
    _shall_apply_tempo_coverter = True
    _tempo_converter = symmetrical.tempos.TempoConverter(
        # expenvelope.Envelope.from_levels_and_durations(levels=[7.5, 7.5], durations=[1])
        expenvelope.Envelope.from_levels_and_durations(levels=[30, 30], durations=[1])
    )

    def _apply_tempo_coverter(self, event_to_convert: abc.Event) -> abc.Event:
        if self._shall_apply_tempo_coverter:
            return self._tempo_converter.convert(event_to_convert)
        else:
            return event_to_convert

    def convert(self, event_to_convert: abc.Event) -> abc.Event:
        return super().convert(self._apply_tempo_coverter(event_to_convert))


class SustainingInstrumentEventToMidiFileConverter(
    OT2InstrumentEventToMidiFileConverter
):
    def __init__(self, nth_sustaining_instrument: int):
        super().__init__(
            path="builds/sustaining_instrument_{}.mid".format(
                nth_sustaining_instrument
            ),
            midi_file_type=0,  # monophon instruments
        )


class DroneEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self):
        super().__init__(
            path="builds/drone.mid", midi_file_type=1,  # polyphon instruments
        )


class PercussiveEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self):
        super().__init__(
            path="builds/percussive.mid", midi_file_type=1,  # polyphon instruments
        )

    def convert(self, event_to_convert: abc.Event):
        return super().convert(
            event_to_convert.set_parameter(
                "pitch_or_pitches",
                lambda pitch_or_pitches: [
                    instruments.PERCUSSION_EXPONENTS_TO_WRITTEN_PITCH[pitch.exponents]
                    for pitch in pitch_or_pitches
                ],
                mutate=False,
            )
        )


class KeyboardEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self, nth_keyboard: int):
        super().__init__(
            path=f"builds/keyboard{nth_keyboard}.mid",
            midi_file_type=1,  # polyphon instruments
        )


class CommonHarmonicEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self, name: str):
        super().__init__(
            path=f"builds/common_harmonics_{name}.mid",
            midi_file_type=1,  # polyphon instruments
        )
