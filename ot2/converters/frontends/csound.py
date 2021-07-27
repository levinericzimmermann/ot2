from mutwo.converters.frontends import csound
from mutwo.events import music

from ot2.converters.frontends import csound_constants


class PercussiveSequentialEventToSoundFileConverter(csound.CsoundConverter):
    def __init__(self):
        csound_score_converter = csound.CsoundScoreConverter(
            "ot2/converters/frontends/percussive.sco",
            p3=lambda note_like: 20,  # set duration of each sample to 20 seconds
            p4=PercussiveSequentialEventToSoundFileConverter._simple_event_to_sample_path,
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
            "{}/drone.sco".format(csound_constants.FILES_PATH),
            p4=lambda note_like: note_like.pitch_or_pitches[0].frequency,
            p5=lambda note_like: note_like.volume.amplitude,
            p6=lambda note_like: note_like.attack,
            p7=lambda note_like: note_like.sustain,
            p8=lambda note_like: note_like.release,
        )
        super().__init__(
            "builds/drone.wav",
            "{}/drone.orc".format(csound_constants.FILES_PATH),
            csound_score_converter,
            remove_score_file=True,
        )


class SineTonesToSoundFileConverter(csound.CsoundConverter):
    def __init__(self, instrument_id: str):
        def get_pitch(note_like):
            pitch_or_pitches = note_like.pitch_or_pitches
            if len(pitch_or_pitches) > 0:
                return note_like.pitch_or_pitches[0].frequency

        csound_score_converter = csound.CsoundScoreConverter(
            f"{csound_constants.FILES_PATH}/{instrument_id}.sco",
            p4=get_pitch,
            p5=lambda note_like: note_like.volume.amplitude,
        )
        super().__init__(
            f"builds/{instrument_id}.wav",
            "{}/sine.orc".format(csound_constants.FILES_PATH),
            csound_score_converter,
            remove_score_file=True,
        )
