import functools
import operator
import typing

import expenvelope
import mido

from mutwo.converters.frontends import midi
from mutwo.converters import symmetrical
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot2 import constants as ot2_constants


class OT2InstrumentEventToMidiFileConverter(midi.MidiFileConverter):
    _shall_apply_tempo_coverter = True
    _tempo_converter = symmetrical.tempos.TempoConverter(
        expenvelope.Envelope.from_levels_and_durations(levels=[30, 30], durations=[1])
    )

    def __init__(
        self,
        *args,
        min_velocity: int = 0,
        max_velocity: int = 127,
        apply_extrema: bool = False,
        **kwargs,
    ):
        self._min_velocity = min_velocity
        self._max_velocity = max_velocity
        self._apply_extrema = apply_extrema
        super().__init__(*args, **kwargs)

    def _apply_tempo_coverter(
        self, event_to_convert: events.abc.Event
    ) -> events.abc.Event:
        if self._shall_apply_tempo_coverter:
            return self._tempo_converter.convert(event_to_convert)
        else:
            return event_to_convert

    def convert(self, event_to_convert: events.abc.Event) -> events.abc.Event:
        volumes = event_to_convert.get_parameter("volume")
        while hasattr(volumes[0], "__iter__"):
            volumes = functools.reduce(operator.add, volumes)
        velocities = tuple(volume.midi_velocity for volume in volumes if volume)
        self._min_velocity_of_event = min(velocities)
        self._max_velocity_of_event = max(velocities)

        if self._min_velocity_of_event == self._max_velocity_of_event:
            self._max_velocity_of_event += 1
        return super().convert(self._apply_tempo_coverter(event_to_convert))

    def _note_information_to_midi_messages(
        self,
        absolute_tick_start: int,
        absolute_tick_end: int,
        velocity: int,
        pitch: parameters.abc.Pitch,
        available_midi_channels_cycle: typing.Iterator,
    ) -> typing.Tuple[mido.Message, ...]:
        if self._apply_extrema:
            min_vel_ev, max_vel_ev = (
                self._min_velocity_of_event,
                self._max_velocity_of_event,
            )
        else:
            min_vel_ev, max_vel_ev = (0, 127)
        velocity = int(
            utilities.tools.scale(
                velocity, min_vel_ev, max_vel_ev, self._min_velocity, self._max_velocity
            )
        )
        return super()._note_information_to_midi_messages(
            absolute_tick_start,
            absolute_tick_end,
            velocity,
            pitch,
            available_midi_channels_cycle,
        )


class SustainingInstrumentEventToMidiFileConverter(
    OT2InstrumentEventToMidiFileConverter
):
    def __init__(self, nth_sustaining_instrument: int):
        super().__init__(
            path="{}/sustaining_instrument_{}.mid".format(
                ot2_constants.paths.MIDI_FILES_PATH, nth_sustaining_instrument
            ),
            midi_file_type=0,  # monophon instruments
            min_velocity=8,
            max_velocity=35,
        )


class DroneEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self):
        super().__init__(
            path=f"{ot2_constants.paths.MIDI_FILES_PATH}/drone.mid",
            midi_file_type=1,  # polyphon instruments
        )


class PercussiveEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self):
        super().__init__(
            path=f"{ot2_constants.paths.MIDI_FILES_PATH}/percussive.mid",
            midi_file_type=1,  # polyphon ot2_constants.instruments
        )

    def convert(self, event_to_convert: events.abc.Event):
        return super().convert(
            event_to_convert.set_parameter(
                "pitch_or_pitches",
                lambda pitch_or_pitches: [
                    ot2_constants.instruments.PERCUSSION_EXPONENTS_TO_WRITTEN_PITCH[
                        pitch.exponents
                    ]
                    for pitch in pitch_or_pitches
                ],
                mutate=False,
            )
        )


class KeyboardEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self, nth_keyboard: int):
        super().__init__(
            path=f"{ot2_constants.paths.MIDI_FILES_PATH}/keyboard{nth_keyboard}.mid",
            midi_file_type=1,  # polyphon ot2_constants.instruments
            min_velocity=3,
            max_velocity=85,
        )


class CommonHarmonicEventToMidiFileConverter(OT2InstrumentEventToMidiFileConverter):
    def __init__(self, name: str):
        super().__init__(
            path=f"{ot2_constants.paths.MIDI_FILES_PATH}/common_harmonics_{name}.mid",
            midi_file_type=1,  # polyphon ot2_constants.instruments
        )
