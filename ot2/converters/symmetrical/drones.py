import abc
import functools
import itertools
import operator
import typing

from mutwo import converters
from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants


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

            absolute_position = times[0] / ot2_constants.duration.DURATION_IN_SECONDS
            register = ot2_constants.tendencies_and_choices.DRONE_REGISTER_RANGE_DICT[
                absolute_position
            ]

            if len(times) == 3:
                attack = times[1] - times[0]
                sustain = 0.0001
                release = times[2] - times[1]
            else:
                attack = times[1] - times[0]
                sustain = times[2] - times[1]
                release = times[3] - times[2]

            drone_event = SimpleDroneEvent(
                pitch_curve.pitch.register(register, mutate=False),
                times[-1] - times[0],
                0.5,
                attack,
                sustain,
                release,
            )
            new_sequential_event.append(drone_event)
            drones.append(new_sequential_event)
        return drones


class FamilyOfPitchCurvesToDroneBracketsConverter(converters.abc.Converter):
    @abc.abstractmethod
    def convert(
        self, family_of_pitch_curves: events.families.FamilyOfPitchCurves
    ) -> events.time_brackets.TimeBracket:
        raise NotImplementedError


class SimpleCsoundBasedFamilyOfPitchCurvesToDroneBracketsConverter(
    FamilyOfPitchCurvesToDroneBracketsConverter
):
    def convert(
        self, family_of_pitch_curves: events.families.FamilyOfPitchCurves
    ) -> events.time_brackets.TimeBracket[
        events.basic.TaggedSequentialEvent[events.basic.SequentialEvent[DroneEvent]]
    ]:
        family_of_pitch_curves = family_of_pitch_curves.filter_curves_with_tag(
            "root", mutate=False
        )
        time_brackets = []
        current_time_bracket = None
        for pitch_curve in family_of_pitch_curves:
            new_sequential_event = events.basic.SequentialEvent([])
            times = pitch_curve.weight_curve.times
            levels = pitch_curve.weight_curve.levels
            times = times[levels.index(max(levels)) - 1 :]

            absolute_position = times[0] / ot2_constants.duration.DURATION_IN_SECONDS

            add_drone = (
                ot2_constants.tendencies_and_choices.DRONE_PLAY_ISLAND_CHOICE.gamble_at(
                    absolute_position
                )
            )
            if add_drone:
                if current_time_bracket:
                    if current_time_bracket.maximum_end < times[0]:
                        for sequential_event in current_time_bracket[0]:
                            assert round(sequential_event.duration, 3) == round(
                                current_time_bracket[0].duration, 3
                            )
                        time_brackets.append(current_time_bracket)
                        current_time_bracket = None

                if current_time_bracket is None:
                    current_time_bracket = events.time_brackets.TimeBracket(
                        [
                            events.basic.TaggedSimultaneousEvent(
                                [], tag=ot2_constants.instruments.ID_DRONE_SYNTH
                            )
                        ],
                        times[0],
                        times[-1],
                    )

                current_time_bracket.end_or_end_range = times[-1]
                expected_duration = (
                    current_time_bracket.maximum_end
                    - current_time_bracket.minimal_start
                )
                for sequential_event in current_time_bracket[0]:
                    difference = expected_duration - sequential_event.duration
                    if difference > 0:
                        sequential_event.append(events.basic.SimpleEvent(difference))

                difference_to_previous_start = (
                    times[0] - current_time_bracket.minimal_start
                )
                if difference_to_previous_start > 0:
                    rest = events.basic.SimpleEvent(difference_to_previous_start)
                    new_sequential_event.append(rest)

                register = (
                    ot2_constants.tendencies_and_choices.DRONE_REGISTER_RANGE_DICT[
                        absolute_position
                    ]
                )

                if len(times) == 3:
                    attack = times[1] - times[0]
                    sustain = 0.0001
                    release = times[2] - times[1]
                else:
                    attack = times[1] - times[0]
                    sustain = times[2] - times[1]
                    release = times[3] - times[2]

                drone_event = SimpleDroneEvent(
                    pitch_curve.pitch.register(register, mutate=False),
                    times[-1] - times[0],
                    0.5,
                    attack,
                    sustain,
                    release,
                )
                new_sequential_event.append(drone_event)
                current_time_bracket[0].append(new_sequential_event)

        if current_time_bracket:
            time_brackets.append(current_time_bracket)

        return tuple(time_brackets)


class FourFofBasedFamiliesOfPitchCurvesToDroneBracketsConverter(
    FamilyOfPitchCurvesToDroneBracketsConverter
):
    n_voices = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._voice_to_skip_cycle = itertools.cycle(
            functools.reduce(operator.add, itertools.permutations(range(self.n_voices)))
        )
        self._delay_cycles_per_active_voices = {
            1: itertools.cycle((((0, 0),),)),
            2: itertools.cycle(itertools.permutations(((0.15, 0), (0, 0.15)))),
            3: itertools.cycle(
                itertools.permutations(((0.15, 0), (0, 0.15), (0.05, 0.05)))
            ),
            4: itertools.cycle(
                itertools.permutations(
                    ((0.15, 0), (0, 0.15), (0.075, 0.05), (0.05, 0.075))
                )
            ),
        }

    def _make_drone_events_from_pitch_curves(
        self, pitch_curves: tuple[events.families.PitchCurve, ...]
    ) -> events.basic.SequentialEvent:
        drone_events = events.basic.SequentialEvent([])
        for curve in pitch_curves:
            active_range = curve.active_ranges[
                0
            ]  # root curves only have one active range
            drone_events_duration = drone_events.duration
            difference = active_range[0] - drone_events_duration
            if difference:
                drone_events.append(events.basic.SimpleEvent(difference))
            event = events.music.NoteLike(
                curve.pitch, active_range[-1] - active_range[0]
            )
            drone_events.append(event)
        return drone_events

    def _make_even_drone_events(
        self, filtered_family_of_pitch_curves: events.families.FamilyOfPitchCurves
    ) -> events.basic.SequentialEvent:
        even_pitch_curves = tuple(filtered_family_of_pitch_curves)[::2]
        return self._make_drone_events_from_pitch_curves(even_pitch_curves)

    def _make_odd_drone_events(
        self, filtered_family_of_pitch_curves: events.families.FamilyOfPitchCurves
    ) -> events.basic.SequentialEvent:
        even_pitch_curves = tuple(filtered_family_of_pitch_curves)[1::2]
        return self._make_drone_events_from_pitch_curves(even_pitch_curves)

    def _distribute_drone_event_on_voices(
        self, absolute_position: float, drone_event: events.music.NoteLike
    ) -> tuple[
        events.basic.SequentialEvent,
        events.basic.SequentialEvent,
        events.basic.SequentialEvent,
        events.basic.SequentialEvent,
    ]:
        density = ot2_constants.tendencies_and_choices.DRONE_DENSITY_TENDENCY.value_at(
            absolute_position
        )
        n_voices_to_play = int(self.n_voices * density)
        n_voices_to_omit = self.n_voices - n_voices_to_play
        voices_to_omit = tuple(
            next(self._voice_to_skip_cycle) for _ in range(n_voices_to_omit)
        )
        voices_to_play = tuple(
            voice_index
            for voice_index in range(self.n_voices)
            if voice_index not in voices_to_omit
        )

        event_per_voice = [None for _ in range(self.n_voices)]

        for nth_voice in voices_to_omit:
            event_per_voice[nth_voice] = events.basic.SequentialEvent(
                [events.basic.SimpleEvent(drone_event.duration)]
            )

        delays_per_voice_to_play = next(
            self._delay_cycles_per_active_voices[len(voices_to_play)]
        )
        for nth_voice, delays in zip(voices_to_play, delays_per_voice_to_play):
            register = (
                ot2_constants.tendencies_and_choices.DRONE_REGISTER_CHOICE.gamble_at(
                    absolute_position
                )
            )
            pitch = drone_event.pitch_or_pitches[0].register(register, mutate=False)
            sequential_event = events.basic.SequentialEvent([])
            for delay in delays:
                rest = events.basic.SimpleEvent(delay * drone_event.duration)
                sequential_event.append(rest)
            playing_duration = drone_event.duration - sequential_event.duration
            active_event = events.music.NoteLike(pitch, playing_duration, "mf")
            sequential_event.insert(1, active_event)
            event_per_voice[nth_voice] = sequential_event

        return tuple(event_per_voice)

    def _make_four_voices_from_drone_events(
        self,
        absolute_entry_delay: parameters.abc.DurationType,
        drone_events: events.basic.SequentialEvent,
    ) -> tuple[
        # exactly four
        events.basic.SequentialEvent,
        events.basic.SequentialEvent,
        events.basic.SequentialEvent,
        events.basic.SequentialEvent,
    ]:
        voices = [events.basic.SequentialEvent([]) for _ in range(self.n_voices)]
        for absolute_time, drone_event in zip(
            drone_events.absolute_times, drone_events
        ):
            if hasattr(drone_event, "pitch_or_pitches"):
                absolute_position = (
                    absolute_time + absolute_entry_delay
                ) / ot2_constants.duration.DURATION_IN_SECONDS
                for voice, new_sequential_event in zip(
                    voices,
                    self._distribute_drone_event_on_voices(
                        absolute_position, drone_event
                    ),
                ):
                    voice.extend(new_sequential_event)

            else:
                for voice in voices:
                    voice.append(events.basic.SimpleEvent(drone_event.duration))

        for voice in voices:
            voice.tie_by(
                lambda ev0, ev1: (not hasattr(ev0, "pitch_or_pitches"))
                and (not hasattr(ev1, "pitch_or_pitches"))
            )

        return tuple(voices)

    def _make_time_bracket_from_family_of_pitch_curves(
        self,
        absolute_entry_delay: parameters.abc.DurationType,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
    ) -> events.time_brackets.TimeBracket:
        filtered_family_of_pitch_curves = family_of_pitch_curves.filter_curves_with_tag(
            "root", mutate=False
        )
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [], tag=ot2_constants.instruments.ID_DRONE_SYNTH
                )
                for _ in range(self.n_voices)
            ],
            start_or_start_range=absolute_entry_delay,
            end_or_end_range=absolute_entry_delay + family_of_pitch_curves.duration,
        )
        even_drone_events = self._make_even_drone_events(
            filtered_family_of_pitch_curves
        )
        odd_drone_events = self._make_odd_drone_events(filtered_family_of_pitch_curves)
        for drone_events in (even_drone_events, odd_drone_events):
            voices = self._make_four_voices_from_drone_events(
                absolute_entry_delay, drone_events
            )
            for nth_voice, voice in enumerate(voices):
                time_bracket[nth_voice].append(voice)

        max_duration = max(map(lambda ev: ev.duration, time_bracket))
        for tagged_simultaneous_event in time_bracket:
            for sequential_event in tagged_simultaneous_event:
                difference = max_duration - sequential_event.duration
                if difference:
                    sequential_event.append(events.basic.SimpleEvent(difference))

        return time_bracket

    def convert(
        self,
        families_of_pitch_curves: events.basic.SequentialEvent[
            typing.Union[events.families.FamilyOfPitchCurves, events.basic.SimpleEvent]
        ],
    ) -> tuple[
        events.time_brackets.TimeBracket[
            events.basic.SimultaneousEvent[events.basic.SequentialEvent]
        ],
        ...,
    ]:
        time_brackets = []
        for absolute_time, family_of_pitch_curves_or_simple_event in zip(
            families_of_pitch_curves.absolute_times, families_of_pitch_curves
        ):
            if isinstance(
                family_of_pitch_curves_or_simple_event,
                events.families.FamilyOfPitchCurves,
            ):
                absolute_position = (
                    absolute_time / ot2_constants.duration.DURATION_IN_SECONDS
                )
                shall_play_island = ot2_constants.tendencies_and_choices.DRONE_PLAY_ISLAND_CHOICE.gamble_at(
                    absolute_position
                )
                if shall_play_island:
                    time_bracket = self._make_time_bracket_from_family_of_pitch_curves(
                        absolute_time, family_of_pitch_curves_or_simple_event
                    )
                    time_brackets.append(time_bracket)

        return tuple(time_brackets)
