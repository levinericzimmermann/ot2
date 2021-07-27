from mutwo import converters
from mutwo import events
from mutwo import parameters


class DroneEvent(events.music.NoteLike):
    def __init__(
        self,
        pitch_or_pitches: events.music.PitchOrPitches,
        duration: parameters.abc.DurationType,
        volume: events.music.Volume,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection = None,
        notation_indicators: parameters.notation_indicators.NotationIndicatorCollection = None,
        instrument_number: int = 1,
    ):
        super().__init__(
            pitch_or_pitches, duration, volume, playing_indicators, notation_indicators
        )
        self.instrument_number = instrument_number


class SimpleDroneEvent(DroneEvent):
    def __init__(
        self,
        pitch_or_pitches: events.music.PitchOrPitches,
        duration: parameters.abc.DurationType,
        volume: events.music.Volume,
        attack: parameters.abc.DurationType,
        sustain: parameters.abc.DurationType,
        release: parameters.abc.DurationType,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection = None,
        notation_indicators: parameters.notation_indicators.NotationIndicatorCollection = None,
    ):
        super().__init__(
            pitch_or_pitches, duration, volume, playing_indicators, notation_indicators
        )
        self.attack = attack
        self.sustain = sustain
        self.release = release


class FamilyOfPitchCurvesToDroneConverter(converters.abc.Converter):
    def convert(
        self, family_of_pitch_curves: events.families.FamilyOfPitchCurves
    ) -> events.basic.SimultaneousEvent[events.basic.SequentialEvent[DroneEvent]]:
        family_of_pitch_curves = family_of_pitch_curves.filter_curves_with_tag(
            "root", mutate=False
        )
        drones = events.basic.SimultaneousEvent([])
        for pitch_curve in family_of_pitch_curves:
            new_sequential_event = events.basic.SequentialEvent([])
            times = pitch_curve.weight_curve.times
            levels = pitch_curve.weight_curve.levels
            times = times[levels.index(max(levels)) - 1 :]
            if times[0] > 0:
                rest = events.basic.SimpleEvent(times[0])
                new_sequential_event.append(rest)

            if len(times) == 3:
                attack = times[1] - times[0]
                sustain = 0.0001
                release = times[2] - times[1]
            else:
                attack = times[1] - times[0]
                sustain = times[2] - times[1]
                release = times[3] - times[2]

            drone_event = SimpleDroneEvent(
                pitch_curve.pitch.register(-2, mutate=False),
                times[-1] - times[0],
                0.5,
                attack,
                sustain,
                release,
            )
            new_sequential_event.append(drone_event)
            drones.append(new_sequential_event)
        return drones
