import typing

import abjad  # type: ignore
import expenvelope  # type: ignore

from mutwo.converters import abc as converters_abc
from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.events import music
from mutwo import parameters as mutwo_parameters

from ot2.constants import instruments
from ot2.events import basic as ot2_basic


class ColotomicPitchToMutwoPitchConverter(mutwo_abjad.MutwoPitchToAbjadPitchConverter):
    def convert(
        self, mutwo_pitch: mutwo_parameters.pitches.WesternPitch
    ) -> abjad.NamedPitch:
        mutwo_pitch = {
            "g": mutwo_parameters.pitches.WesternPitch("g", octave=3),
            "b": mutwo_parameters.pitches.WesternPitch("b", octave=3),
            "d": mutwo_parameters.pitches.WesternPitch("d", octave=4),
            "f": mutwo_parameters.pitches.WesternPitch("f", octave=4),
        }[mutwo_pitch.pitch_class_name]
        return super().convert(mutwo_pitch)


class SequentialEventToAbjadScoreConverter(converters_abc.Converter):
    def __init__(
        self,
        time_signatures: typing.Sequence[abjad.TimeSignature] = (
            abjad.TimeSignature((4, 4)),
        ),
        tempo_envelope: expenvelope.Envelope = None,
    ):
        self._time_signatures = time_signatures
        self._tempo_envelope = tempo_envelope
        self._instrument_id_to_sequential_event_to_abjad_voice_converter = (
            self._make_instrument_id_to_sequential_event_to_abjad_voice_converter()
        )

    @staticmethod
    def _prepare_voice(voice: abjad.Voice, instrument_id: str):
        """Preparation that applies to all voices"""

        first_leaf = abjad.get.leaf(voice, 0)

        abjad.attach(
            abjad.LilyPondLiteral(
                "\\set Staff.instrumentName = \\markup {  \\teeny {"
                + instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[instrument_id]
                + " } }"
            ),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\set Staff.shortInstrumentName = \\markup {  \\teeny { "
                + instruments.INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME[instrument_id]
                + " } }"
            ),
            first_leaf,
        )

        abjad.attach(
            abjad.LilyPondLiteral(
                "\\override Staff.TimeSignature.style = #'single-digit"
            ),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\set Score.proportionalNotationDuration = #(ly:make-moment 1/8)"
            ),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\override Score.SpacingSpanner.strict-note-spacing = ##t"
            ),
            first_leaf,
        )
        abjad.attach(abjad.LilyPondLiteral("\\hide Staff.BarLine"), first_leaf)

        last_leaf = abjad.get.leaf(voice, -1)
        abjad.attach(abjad.LilyPondLiteral(r'\undo \hide Staff.BarLine'), last_leaf)
        abjad.attach(abjad.BarLine('|.', format_slot='absolute_after'), last_leaf)

    @staticmethod
    def _prepare_duration_line_voice(voice: abjad.Voice):
        """Preparation that applies to voices with duration line notation"""

        first_leaf = abjad.get.leaf(voice, 0)
        abjad.attach(
            abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), first_leaf
        )
        voice.consists_commands.append("Duration_line_engraver")

    @staticmethod
    def _prepare_drone_voice(voice: abjad.Voice):
        """Preparation that applies to drone"""

        first_leaf = abjad.get.leaf(voice, 0)
        abjad.attach(abjad.Clef("bass"), first_leaf)

    @staticmethod
    def _prepare_percussion_voice(voice: abjad.Voice):
        """Preparation that applies to drone"""

        first_leaf = abjad.get.leaf(voice, 0)
        abjad.attach(abjad.Clef("percussion"), first_leaf)

    def _make_sequential_event_to_abjad_voice_converter_for_sustaining_instrument(
        self,
    ) -> mutwo_abjad.SequentialEventToAbjadVoiceConverter:
        return mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.SequentialEventToDurationLineBasedQuantizedAbjadContainerConverter(
                self._time_signatures, tempo_envelope=self._tempo_envelope
            ),
            mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
        )

    def _make_sequential_event_to_abjad_voice_converter_for_percussion_instrument(
        self,
    ) -> mutwo_abjad.SequentialEventToAbjadVoiceConverter:
        return mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
                self._time_signatures, tempo_envelope=self._tempo_envelope
            ),
            mutwo_pitch_to_abjad_pitch_converter=ColotomicPitchToMutwoPitchConverter(),
        )

    def _make_instrument_id_to_sequential_event_to_abjad_voice_converter(
        self,
    ) -> typing.Dict[str, mutwo_abjad.SequentialEventToAbjadVoiceConverter]:
        sequential_event_to_abjad_voice_converter_for_sustaining_instrument = (
            self._make_sequential_event_to_abjad_voice_converter_for_sustaining_instrument()
        )
        sequential_event_to_abjad_voice_converter_for_percussion_instrument = (
            self._make_sequential_event_to_abjad_voice_converter_for_percussion_instrument()
        )

        return {
            instruments.ID_SUS0: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_SUS1: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_SUS2: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_DRONE: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_PERCUSSIVE: sequential_event_to_abjad_voice_converter_for_percussion_instrument,
            instruments.ID_NOISE: sequential_event_to_abjad_voice_converter_for_percussion_instrument,
        }

    def convert(
        self, tagged_simultaneous_event: ot2_basic.TaggedSimultaneousEvent
    ) -> abjad.Score:
        staff_group = abjad.StaffGroup([])

        duration = tagged_simultaneous_event.duration

        for instrument_id in sorted(
            tagged_simultaneous_event.tag_to_event_index.keys(),
            key=lambda tag: tagged_simultaneous_event.tag_to_event_index[tag],
        ):
            converter = self._instrument_id_to_sequential_event_to_abjad_voice_converter[
                instrument_id
            ]
            sequential_event = tagged_simultaneous_event[instrument_id]

            difference = duration - sequential_event.duration
            if difference:
                sequential_event.append(music.NoteLike([], difference, 'pp'))

            abjad_voice = converter.convert(sequential_event)

            if instrument_id not in (instruments.ID_PERCUSSIVE, instruments.ID_NOISE):
                self._prepare_duration_line_voice(abjad_voice)

            if instrument_id == instruments.ID_PERCUSSIVE:
                self._prepare_percussion_voice(abjad_voice)
            elif instrument_id == instruments.ID_DRONE:
                self._prepare_drone_voice(abjad_voice)
            elif instrument_id == instruments.ID_NOISE:
                self._prepare_percussion_voice(abjad_voice)

            self._prepare_voice(abjad_voice, instrument_id)

            staff_group.append(abjad.Staff([abjad_voice]))

        abjad_score = abjad.Score([staff_group])
        return abjad_score


class PaperFormat(object):
    def __init__(self, name: str, height: float, width: float):
        self.name = name
        self.height = height
        self.width = width


A4 = PaperFormat("a4", 210, 297)
A3 = PaperFormat("a3", 297, 420)
A2 = PaperFormat("a2", 420, 594)


class AbjadScoreToLilypondFileConverter(converters_abc.Converter):
    def __init__(
        self,
        instrument: typing.Optional[str] = None,
        paper_format: PaperFormat = A4,
        margin: float = 4,
    ):
        self._instrument = instrument
        self._paper_format = paper_format
        self._margin = margin

    def _stress_instrument(self, abjad_score: abjad.Score):
        pass

    @staticmethod
    def _make_header_block(instrument: typing.Optional[str]) -> abjad.Block:
        header_block = abjad.Block("header")
        header_block.title = '"ohne Titel (2)"'
        header_block.year = '"2021"'
        header_block.composer = '"Levin Eric Zimmermann"'
        header_block.tagline = '"oT(2) // 2021"'
        if instrument:
            header_block.instrument = instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[
                instrument
            ]
        return header_block

    @staticmethod
    def _make_paper_block() -> abjad.Block:
        paper_block = abjad.Block("paper")
        paper_block.items.append(
            r"""#(define fonts
    (make-pango-font-tree "EB Garamond"
                          "Nimbus Sans"
                          "Luxi Mono"
                          (/ staff-height pt 20)))"""
        )
        return paper_block

    @staticmethod
    def _make_layout_block(margin: int) -> abjad.Block:
        layout_block = abjad.Block("layout")
        layout_block.items.append(r"short-indent = {}\mm".format(margin))
        layout_block.items.append(r"ragged-last = ##f")
        layout_block.items.append(r"indent = 23\mm".format(margin))
        return layout_block

    def convert(self, abjad_score: abjad.Score) -> abjad.LilyPondFile:
        lilypond_file = abjad.LilyPondFile(
            includes=["ekme-heji-ref-c.ily"], default_paper_size=self._paper_format.name
        )

        if self._instrument:
            self._stress_instrument(abjad_score)

        score_block = abjad.Block("score")
        score_block.items.append(abjad_score)

        lilypond_file.items.append(score_block)
        lilypond_file.items.append(
            AbjadScoreToLilypondFileConverter._make_header_block(self._instrument)
        )
        lilypond_file.items.append(
            AbjadScoreToLilypondFileConverter._make_layout_block(self._margin)
        )
        lilypond_file.items.append(
            AbjadScoreToLilypondFileConverter._make_paper_block()
        )

        return lilypond_file


"""
class ColotomicPatternToAbjadScoreConverter(converters_abc.Converter):
    @staticmethod
    def _prepare_abjad_voice(
        abjad_voice: abjad.Voice,
        colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern,
    ) -> None:
        abjad.attach(abjad.Clef("percussion"), abjad_voice[0][0])

        # add repeat and n repetitions
        abjad.attach(
            abjad.Repeat(repeat_count=colotomic_pattern_to_convert.n_repetitions),
            abjad_voice,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\mark \\markup { \\smallCaps "
                + '"{}x"'.format(colotomic_pattern_to_convert.n_repetitions)
                + "}",
                format_slot="after",
            ),
            abjad_voice[-1][-1],
        )

    @staticmethod
    def _extract_sequential_event_from_colotomic_pattern(
        colotomic_pattern: colotomic_brackets.ColotomicPattern,
    ) -> basic.SequentialEvent[music.NoteLike]:
        sequential_event = basic.SequentialEvent([])
        for colotomic_element in colotomic_pattern:
            sequential_event.extend(colotomic_element)
        return sequential_event

    def _make_sequential_event_to_abjad_voice_converter(
        self, colotomic_pattern: colotomic_brackets.ColotomicPattern
    ) -> mutwo_abjad.SequentialEventToAbjadVoiceConverter:
        tempo_envelope = expenvelope.Envelope.from_levels_and_durations(
            levels=[colotomic_pattern.tempo, colotomic_pattern.tempo], durations=[1]
        )
        sequential_event_to_quantized_abjad_container_converter = mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
            time_signatures=(
                colotomic_pattern.time_signature,
                colotomic_pattern.time_signature,
            ),
            tempo_envelope=tempo_envelope,
        )
        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            sequential_event_to_quantized_abjad_container_converter,
            mutwo_pitch_to_abjad_pitch_converter=ColotomicPitchToMutwoPitchConverter(),
        )
        return sequential_event_to_abjad_voice_converter

    def convert(
        self, colotomic_pattern_to_convert: colotomic_brackets.ColotomicPattern
    ) -> abjad.Score:
        sequential_event = ColotomicPatternToAbjadScoreConverter._extract_sequential_event_from_colotomic_pattern(
            colotomic_pattern_to_convert
        )
        converter = self._make_sequential_event_to_abjad_voice_converter(
            colotomic_pattern_to_convert
        )
        abjad_voice = converter.convert(sequential_event)

        ColotomicPatternToAbjadScoreConverter._prepare_abjad_voice(
            abjad_voice, colotomic_pattern_to_convert
        )

        abjad_score = abjad.Score([abjad.Staff([abjad_voice])])
        return abjad_score


class ColotomicPatternsToLilypondFileConverter(converters_abc.Converter):
    def __init__(self):
        self._colotomic_pattern_to_abjad_score_converter = (
            ColotomicPatternToAbjadScoreConverter()
        )

    def convert(
        self, colotomic_patterns: typing.Sequence[colotomic_brackets.ColotomicPattern]
    ) -> abjad.LilyPondFile:
        # add margin markup (pattern number)
        for nth_pattern, colotomic_pattern in enumerate(colotomic_patterns):
            colotomic_pattern[0][0].notation_indicators.margin_markup.content = (
                "{}".format(nth_pattern + 1)
            )

        abjad_scores = [
            self._colotomic_pattern_to_abjad_score_converter.convert(colotomic_pattern)
            for colotomic_pattern in colotomic_patterns
        ]

        lilypond_file = abjad.LilyPondFile()

        header = abjad.Block("header")
        header.title = '"ohne Titel (2)"'
        header.instrument = '"percussive instrument(s)"'
        header.composer = '"Levin Eric Zimmermann"'
        # header.tagline = '"oT(2)"'
        header.tagline = '""'
        lilypond_file.items.append(header)

        lilypond_file.items.extend(abjad_scores)

        return lilypond_file
"""
