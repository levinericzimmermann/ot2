import expenvelope

from mutwo.converters.frontends import midi
from mutwo.converters import symmetrical
from mutwo.events import abc


class OT2InstrumentEventToMidiFileConverter(midi.MidiFileConverter):
    _shall_apply_tempo_coverter = True
    _tempo_converter = symmetrical.tempos.TempoConverter(
        expenvelope.Envelope.from_levels_and_durations(levels=[7.5, 7.5], durations=[1])
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
