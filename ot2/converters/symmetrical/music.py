import fractions
import typing

import expenvelope

from mutwo import converters
from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos

from ot2.constants import instruments
from ot2.converters import symmetrical
from ot2 import events as ot2_events
from ot2.generators import zimmermann

Music = ot2_events.basic.TaggedSimultaneousEvent[
    basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
]


class BarsWithHarmonyToMusicConverter(converters.abc.Converter):
    def _make_rest(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ):
        sequential_event = basic.SequentialEvent([])
        for bar in bars_with_harmony:
            note = music.NoteLike([], bar.duration,)
            sequential_event.append(note)
        return basic.SimultaneousEvent([sequential_event])

    def convert(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> Music:
        raise NotImplementedError()


class IndependentBarsWithHarmonyToMusicConverter(BarsWithHarmonyToMusicConverter):
    def _make_sustaining_instrument_0(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        raise NotImplementedError()

    def _make_sustaining_instrument_1(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        raise NotImplementedError()

    def _make_sustaining_instrument_2(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        raise NotImplementedError()

    def _make_drone(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        raise NotImplementedError()

    def _make_percussion(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        raise NotImplementedError()

    def _make_noise(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        raise NotImplementedError()

    def convert(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> Music:
        return ot2_events.basic.TaggedSimultaneousEvent(
            (
                self._make_sustaining_instrument_0(bars_with_harmony),
                self._make_sustaining_instrument_1(bars_with_harmony),
                self._make_sustaining_instrument_2(bars_with_harmony),
                self._make_drone(bars_with_harmony),
                self._make_percussion(bars_with_harmony),
                self._make_noise(bars_with_harmony),
            ),
            tag_to_event_index=instruments.INSTRUMENT_ID_TO_INDEX,
        )


class SimpleChordConverter(IndependentBarsWithHarmonyToMusicConverter):
    @staticmethod
    def _take_nth_pitch(
        bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...],
        nth_pitch: int,
        ambitus,
    ):
        sequential_event = basic.SequentialEvent([])
        for bar in bars_with_harmony:
            note = music.NoteLike(
                ambitus.find_all_pitch_variants(bar.harmonies[0][nth_pitch])[0],
                bar.duration,
                "pp",
            )
            sequential_event.append(note)
        return basic.SimultaneousEvent([sequential_event])

    def _make_sustaining_instrument_0(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        return self._take_nth_pitch(
            bars_with_harmony,
            1,
            instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
        )

    def _make_sustaining_instrument_1(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        return self._take_nth_pitch(
            bars_with_harmony,
            2,
            instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
        )

    def _make_sustaining_instrument_2(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        return self._take_nth_pitch(
            bars_with_harmony,
            3,
            instruments.AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES,
        )

    def _make_drone(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        return self._take_nth_pitch(
            bars_with_harmony, 0, instruments.AMBITUS_DRONE_INSTRUMENT
        )

    def _make_percussion(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        sequential_event = basic.SequentialEvent([])
        for bar in bars_with_harmony:
            is_first = True
            for subduration in bar[0]:
                if is_first:
                    pitch = "b"
                    is_first = False
                else:
                    pitch = "f"
                note = music.NoteLike(pitch, subduration.duration, "pp")
                sequential_event.append(note)
        return basic.SimultaneousEvent([sequential_event])

    def _make_noise(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]:
        return self._make_rest(bars_with_harmony)

    def convert(
        self, bars_with_harmony: typing.Tuple[ot2_events.bars.BarWithHarmony, ...]
    ) -> Music:
        return ot2_events.basic.TaggedSimultaneousEvent(
            (
                self._make_sustaining_instrument_0(bars_with_harmony),
                self._make_sustaining_instrument_1(bars_with_harmony),
                self._make_sustaining_instrument_2(bars_with_harmony),
                self._make_drone(bars_with_harmony),
                self._make_percussion(bars_with_harmony),
                self._make_noise(bars_with_harmony),
            ),
            tag_to_event_index=instruments.INSTRUMENT_ID_TO_INDEX,
        )


class DataToMusicConverter(converters.abc.Converter):
    def _convert_bars_with_harmony(
        self,
        bars_with_harmony_to_convert: typing.Tuple[ot2_events.bars.BarWithHarmony, ...],
    ) -> typing.Tuple[Music, expenvelope.Envelope]:
        raise NotImplementedError()

    def convert(
        self,
        bars_maker: zimmermann.BarsMaker,
        bars_to_bars_with_harmony_converter: symmetrical.bars.BarsToBarsWithHarmonyConverter,
    ) -> typing.Tuple[
        Music, typing.Tuple[ot2_events.bars.BarWithHarmony, ...], expenvelope.Envelope
    ]:
        bars_with_harmony = bars_to_bars_with_harmony_converter.convert(bars_maker())
        tagged_simultaneous_event, tempo_envelope = self._convert_bars_with_harmony(
            bars_with_harmony
        )
        return tagged_simultaneous_event, bars_with_harmony, tempo_envelope


class DummyDataToMusicConverter(DataToMusicConverter):
    def _convert_bars_with_harmony(
        self,
        bars_with_harmony_to_convert: typing.Tuple[ot2_events.bars.BarWithHarmony, ...],
    ) -> typing.Tuple[Music, expenvelope.Envelope]:
        converter = SimpleChordConverter()
        return (
            converter.convert(bars_with_harmony_to_convert),
            (
                expenvelope.Envelope.from_points(
                    (0, tempos.TempoPoint(30, fractions.Fraction(1, 2))),
                    (1, tempos.TempoPoint(30, fractions.Fraction(1, 2))),
                )
            ),
        )
