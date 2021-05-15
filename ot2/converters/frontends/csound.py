from mutwo.converters.frontends import csound
from mutwo.events import music

from ot2.converters.frontends import csound_constants


class NestedSequentialEventToSoundFileConverter(csound.CsoundConverter):
    def __init__(self):
        csound_score_converter = csound.CsoundScoreConverter(
            "ot2/converters/frontends/percussive.sco",
            p3=lambda note_like: 20,  # set duration of each sample to 20 seconds
            p4=NestedSequentialEventToSoundFileConverter._simple_event_to_sample_path,
            p5=lambda note_like: note_like.volume.amplitude,
        )
        super().__init__(
            "builds/percussive.wav",
            "ot2/converters/frontends/percussive.orc",
            csound_score_converter,
            remove_score_file=True,
        )

    @staticmethod
    def _simple_event_to_sample_path(note_like: music.NoteLike) -> str:
        try:
            pitch = note_like.pitch_or_pitches[0]
        except IndexError:
            raise AttributeError()

        return next(
            csound_constants.PERCUSSION_PITCH_TO_PERCUSSION_SAMPLES_CYCLE[
                pitch.pitch_class_name
            ]
        )


class DroneSimultaneousEventToSoundFileConverter(csound.CsoundConverter):
    def __init__(self):
        csound_score_converter = csound.CsoundScoreConverter(
            "ot2/converters/frontends/percussive.sco",
            p3=lambda note_like: 20,
            p4=NestedSequentialEventToSoundFileConverter._simple_event_to_sample_path,
            p5=lambda note_like: note_like.volume.amplitude,
        )
        super().__init__(
            "builds/percussive.wav",
            "ot2/converters/frontends/percussive.orc",
            csound_score_converter,
            remove_score_file=True,
        )

    @staticmethod
    def _simple_event_to_sample_path(note_like: music.NoteLike) -> str:
        try:
            pitch = note_like.pitch_or_pitches[0]
        except IndexError:
            raise AttributeError()

        return next(
            csound_constants.PERCUSSION_PITCH_TO_PERCUSSION_SAMPLES_CYCLE[
                pitch.pitch_class_name
            ]
        )
