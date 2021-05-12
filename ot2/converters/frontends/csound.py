from mutwo.converters.frontends import csound
from mutwo.events import music

_pitch_to_path = {
    "g": "ot2/samples/percussion/woodblock/wood_click_ff.wav",
    "b": "ot2/samples/percussion/woodblock/wood_click_ff.wav",
    "d": "ot2/samples/percussion/woodblock/wood_click_ff.wav",
    "f": "ot2/samples/percussion/woodblock/wood_click_ff.wav",
}


class NestedSequentialEventToSoundFileConverter(csound.CsoundConverter):
    def __init__(self):
        csound_score_converter = csound.CsoundScoreConverter(
            "ot2/converters/frontends/percussive.sco",
            p4=NestedSequentialEventToSoundFileConverter._event_to_path,
        )
        super().__init__(
            "builds/percussive.wav",
            "ot2/converters/frontends/percussive.orc",
            csound_score_converter,
        )

    @staticmethod
    def _event_to_path(note_like: music.NoteLike) -> str:
        try:
            pitch = note_like.pitch_or_pitches[0]
        except IndexError:
            raise AttributeError()

        return _pitch_to_path[pitch.pitch_class_name]
