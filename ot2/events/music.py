from mutwo import events
from mutwo import parameters


class PillowEvent(events.music.NoteLike):
    def __init__(
        self,
        pitch_or_pitches: parameters.pitches.JustIntonationPitch,
        duration: parameters.abc.DurationType,
        volume: parameters.volumes.DecibelVolume,
        attack_duration: float = 0.1,
        release_duration: float = 0.1,
    ):
        super().__init__(pitch_or_pitches, duration, volume)
        self.attack_duration = attack_duration
        self.release_duration = release_duration

    @property
    def pitch(self) -> parameters.pitches.JustIntonationPitch:
        if self.pitch_or_pitches:
            return self.pitch_or_pitches[0]
        else:
            return None
