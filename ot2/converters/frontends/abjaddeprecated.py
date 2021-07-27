import typing

import abjad  # type: ignore
from abjadext import nauert  # type: ignore
import expenvelope  # type: ignore

from mutwo.converters import abc as converters_abc
from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.events import basic
from mutwo.events import music

from ot2.constants import instruments
from ot2.events import basic as ot2_basic


class TaggedSimultaneousEventToAbjadScoreConverter(converters_abc.Converter):
    search_tree = nauert.UnweightedSearchTree(
        definition={
            2: {
                2: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
                3: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
            },
            3: {
                2: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
                3: {2: {2: {2: {2: None,},},}, 3: {2: {2: {2: {2: None,},},},}},
            },
        },
    )

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
    def _prepare_percussion_sequential_event(
        sequential_event: basic.SequentialEvent[music.NoteLike],
    ) -> basic.SequentialEvent:
        # absolute_times = sequential_event.absolute_times
        # for start, event in zip(reversed(absolute_times), reversed(sequential_event)):
        #     if event.duration > fractions.Fraction(1, 4) and event.pitch_or_pitches:
        #         sequential_event.squash_in(
        #             start + fractions.Fraction(1, 4),
        #             music.NoteLike([], event.duration - fractions.Fraction(1, 4)),
        #         )
        return sequential_event

    @staticmethod
    def _prepare_voice(voice: abjad.Voice, instrument_id: str):
        # Preparation that applies to all voices

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
        abjad.attach(abjad.BarLine("|.", format_slot="absolute_after"), last_leaf)
        abjad.attach(
            abjad.LilyPondLiteral(
                r"\undo \hide Staff.BarLine", format_slot="absolute_after"
            ),
            last_leaf,
        )

    @staticmethod
    def _prepare_duration_line_voice(voice: abjad.Voice):
        # Preparation that applies to voices with duration line notation

        first_leaf = abjad.get.leaf(voice, 0)
        abjad.attach(
            abjad.LilyPondLiteral('\\accidentalStyle "dodecaphonic"'), first_leaf
        )

    @staticmethod
    def _prepare_drone_voice(voice: abjad.Voice):
        # Preparation that applies to drone

        first_leaf = abjad.get.leaf(voice, 0)
        abjad.attach(abjad.Clef("bass"), first_leaf)

    @staticmethod
    def _prepare_percussion_voice(voice: abjad.Voice):
        # Preparation that applies to drone

        first_leaf = abjad.get.leaf(voice, 0)
        abjad.attach(abjad.Clef("percussion"), first_leaf)

    def _make_sequential_event_to_abjad_voice_converter_for_sustaining_instrument(
        self,
    ) -> mutwo_abjad.SequentialEventToAbjadVoiceConverter:
        return mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.SequentialEventToDurationLineBasedQuantizedAbjadContainerConverter(
                self._time_signatures,
                tempo_envelope=self._tempo_envelope,
                # search_tree=self.search_tree,
            ),
            mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(),
        )

    # def _make_sequential_event_to_abjad_voice_converter_for_percussion_instrument(
    #     self,
    # ) -> mutwo_abjad.SequentialEventToAbjadVoiceConverter:
    #     return mutwo_abjad.SequentialEventToAbjadVoiceConverter(
    #         mutwo_abjad.SequentialEventToQuantizedAbjadContainerConverter(
    #             self._time_signatures,
    #             tempo_envelope=self._tempo_envelope,
    #             search_tree=self.search_tree,
    #         ),
    #         mutwo_pitch_to_abjad_pitch_converter=ColotomicPitchToMutwoPitchConverter(),
    #     )

    def _make_instrument_id_to_sequential_event_to_abjad_voice_converter(
        self,
    ) -> typing.Dict[str, mutwo_abjad.SequentialEventToAbjadVoiceConverter]:
        sequential_event_to_abjad_voice_converter_for_sustaining_instrument = (
            self._make_sequential_event_to_abjad_voice_converter_for_sustaining_instrument()
        )
        # sequential_event_to_abjad_voice_converter_for_percussion_instrument = (
        #     self._make_sequential_event_to_abjad_voice_converter_for_percussion_instrument()
        # )

        return {
            instruments.ID_SUS0: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_SUS1: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_SUS2: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            instruments.ID_DRONE: sequential_event_to_abjad_voice_converter_for_sustaining_instrument,
            # instruments.ID_PERCUSSIVE: sequential_event_to_abjad_voice_converter_for_percussion_instrument,
            # instruments.ID_NOISE: sequential_event_to_abjad_voice_converter_for_percussion_instrument,
        }

    def convert(
        self,
        tagged_simultaneous_event: ot2_basic.TaggedSimultaneousEvent[
            basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
        ],
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
            simultaneous_event = tagged_simultaneous_event[instrument_id]

            staff = abjad.Staff([], simultaneous=True)
            # staff.remove_commands.append("Time_signature_engraver")
            for sequential_event in simultaneous_event:
                difference = duration - sequential_event.duration
                if difference:
                    sequential_event.append(music.NoteLike([], difference))

                if instrument_id == instruments.ID_PERCUSSIVE:
                    sequential_event = self._prepare_percussion_sequential_event(
                        sequential_event
                    )

                abjad_voice = converter.convert(sequential_event)

                if instrument_id not in (
                    instruments.ID_PERCUSSIVE,
                    instruments.ID_NOISE,
                ):
                    self._prepare_duration_line_voice(abjad_voice)

                if instrument_id == instruments.ID_PERCUSSIVE:
                    self._prepare_percussion_voice(abjad_voice)
                elif instrument_id == instruments.ID_DRONE:
                    self._prepare_drone_voice(abjad_voice)
                elif instrument_id == instruments.ID_NOISE:
                    self._prepare_percussion_voice(abjad_voice)

                self._prepare_voice(abjad_voice, instrument_id)
                staff.append(abjad_voice)

            staff_group.append(staff)

        abjad_score = abjad.Score([staff_group])
        return abjad_score
