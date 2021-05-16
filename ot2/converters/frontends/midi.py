import expenvelope

from mutwo.converters.frontends import midi
from mutwo.converters import symmetrical
from mutwo.events import abc


class SustainingInstrumentEventToMidiFileConverter(midi.MidiFileConverter):
    _tempo_converter = symmetrical.tempos.TempoConverter(
        expenvelope.Envelope.from_levels_and_durations(levels=[30, 30], durations=[1])
    )

    def __init__(self, nth_sustaining_instrument: int):
        super().__init__(
            path="builds/sustaining_instrument_{}.mid".format(
                nth_sustaining_instrument
            ),
            midi_file_type=0,  # monophon instruments
        )

    def convert(self, event_to_convert: abc.Event) -> abc.Event:
        return super().convert(self._tempo_converter.convert(event_to_convert))
