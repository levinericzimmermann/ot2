import abjad
import expenvelope

from mutwo.converters.symmetrical import tempos
from mutwo.events import basic

from ot2.constants import instruments
from ot2.converters.frontends import abjad as ot2_abjad
from ot2.converters.frontends import csound as ot2_csound
from ot2.converters.frontends import midi as ot2_midi
from ot2.events import basic as ot2_basic


def render_abjad(abjad_score: abjad.Score):
    lilypond_file_converter = ot2_abjad.AbjadScoreToLilypondFileConverter()
    lilypond_file = lilypond_file_converter.convert(abjad_score)

    abjad.persist.as_pdf(lilypond_file, "builds/oT2.pdf")


def render_soundfiles(
    tagged_simultaneous_event: ot2_basic.TaggedSimultaneousEvent,
    tempo_envelope: expenvelope.Envelope,
):
    def render_sustaining_instrument(
        nth_sustaining_instrument: int, simultaneous_event: basic.SimultaneousEvent
    ):
        midi_file_converter = ot2_midi.SustainingInstrumentEventToMidiFileConverter(
            nth_sustaining_instrument
        )
        midi_file_converter.convert(simultaneous_event)

    def render_drone(simultaneous_event: basic.SimultaneousEvent):
        sound_file_converter = ot2_midi.DroneEventToMidiFileConverter()
        sound_file_converter.convert(simultaneous_event)

    def render_percussion(simultaneous_event: basic.SimultaneousEvent):
        csound_converter = ot2_csound.PercussiveSequentialEventToSoundFileConverter()
        csound_converter.convert(simultaneous_event)

    tempo_converter = tempos.TempoConverter(tempo_envelope)
    tagged_simultaneous_event = ot2_basic.TaggedSimultaneousEvent(
        tempo_converter.convert(basic.SimultaneousEvent(tuple(tagged_simultaneous_event))),
        instruments.INSTRUMENT_ID_TO_INDEX,
    )

    render_drone(
        tagged_simultaneous_event[
            tagged_simultaneous_event.tag_to_event_index[instruments.ID_DRONE]
        ]
    )
    render_percussion(
        tagged_simultaneous_event[
            tagged_simultaneous_event.tag_to_event_index[instruments.ID_PERCUSSIVE]
        ]
    )

    render_sustaining_instrument(
        0,
        tagged_simultaneous_event[
            tagged_simultaneous_event.tag_to_event_index[instruments.ID_SUS0]
        ],
    )
    render_sustaining_instrument(
        1,
        tagged_simultaneous_event[
            tagged_simultaneous_event.tag_to_event_index[instruments.ID_SUS1]
        ],
    )
    render_sustaining_instrument(
        2,
        tagged_simultaneous_event[
            tagged_simultaneous_event.tag_to_event_index[instruments.ID_SUS2]
        ],
    )
