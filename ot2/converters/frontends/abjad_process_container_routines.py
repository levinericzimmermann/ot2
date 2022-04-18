import typing

import abjad

from mutwo.converters.frontends import abjad_process_container_routines
from mutwo import events

from ot2.constants import instruments


class InstrumentMixin(abjad_process_container_routines.ProcessAbjadContainerRoutine):
    def __init__(
        self, instrument_id: str, accidental_style: typing.Optional[str] = None
    ):
        self._add_instrument_name = abjad_process_container_routines.AddInstrumentName(
            lambda _: instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[instrument_id],
            lambda _: instruments.INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME[instrument_id],
        )
        if accidental_style:
            self._add_accidental_style = (
                abjad_process_container_routines.AddAccidentalStyle(accidental_style)
            )
        else:
            self._add_accidental_style = None

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        self._add_instrument_name(complex_event_to_convert, container_to_process)
        if self._add_accidental_style:
            self._add_accidental_style(complex_event_to_convert, container_to_process)


class KeyboardMixin(InstrumentMixin):
    def __init__(self, add_bass_clef: bool = True):
        self._add_bass_clef = add_bass_clef
        super().__init__(
            instruments.ID_KEYBOARD,
            # "dodecaphonic",
        )

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        # attach keyboard clefs
        abjad.attach(abjad.Clef("treble"), abjad.get.leaf(container_to_process[0], 0))
        if len(container_to_process) > 1 and self._add_bass_clef:
            abjad.attach(abjad.Clef("bass"), abjad.get.leaf(container_to_process[1], 0))


class SustainingInstrumentMixin(InstrumentMixin):
    def __init__(self, nth_sustaining_instrument: int):
        instrument_id = (instruments.ID_SUS0, instruments.ID_SUS1, instruments.ID_SUS2)[
            nth_sustaining_instrument
        ]
        self._instrument_id = instrument_id
        super().__init__(
            instrument_id,
            "dodecaphonic",
        )

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        abjad.attach(abjad.Clef("treble"), abjad.get.leaf(container_to_process[0], 0))


class DroneMixin(InstrumentMixin):
    _instrument_id = instruments.ID_DRONE
    instrument_specific_keywords_for_parent = {
        "instrument_name": instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[
            _instrument_id
        ],
        "short_instrument_name": instruments.INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME[
            _instrument_id
        ],
        "lilypond_type_of_staff": "Staff",
        "accidental_style": "dodecaphonic",
    }

    def __init__(self):
        super().__init__(instruments.ID_DRONE, "dodecaphonic")

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        # attach drone clef
        # abjad.attach(abjad.Clef("bass"), abjad.get.leaf(container_to_process[0], 0))


class NoiseInstrumentMixin(InstrumentMixin):
    _instrument_id = instruments.ID_NOISE
    instrument_specific_keywords_for_parent = {
        "instrument_name": instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[
            _instrument_id
        ],
        "short_instrument_name": instruments.INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME[
            _instrument_id
        ],
        "lilypond_type_of_staff": "Staff",
    }

    def __init__(self):
        super().__init__(instruments.ID_NOISE)

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        # attach drone clef
        # abjad.attach(abjad.Clef("bass"), abjad.get.leaf(container_to_process[0], 0))


class PostProcessIslandTimeBracket(
    abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        for staff_group in container_to_process:
            for staff in staff_group:
                first_leaf = abjad.get.leaf(staff, 0)
                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\set Score.proportionalNotationDuration = #(ly:make-moment"
                        " 1/8)"
                    ),
                    first_leaf,
                )

                last_leaf = abjad.get.leaf(staff, -1)

                abjad.attach(abjad.LilyPondLiteral("\\hide Staff.BarLine"), first_leaf)
                abjad.attach(
                    abjad.LilyPondLiteral("\\omit Staff.TimeSignature"), first_leaf
                )
                # abjad.attach(
                #     abjad.LilyPondLiteral('\\remove "Bar_engraver"'), first_leaf
                # )
                # abjad.attach(
                #     abjad.LilyPondLiteral('\\hide Score.BarLine'), first_leaf
                # )
                # abjad.attach(
                #     abjad.LilyPondLiteral('\\hide StaffGroup.BarLine'), first_leaf
                # )

                try:
                    abjad.attach(
                        abjad.BarLine("|.", format_slot="absolute_after"), last_leaf
                    )
                except Exception:
                    pass
                abjad.attach(
                    abjad.LilyPondLiteral(
                        r"\undo \hide Staff.BarLine", format_slot="absolute_after"
                    ),
                    last_leaf,
                )


class PostProcessCengkokSimultaneousEvent(
    abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        for staff in container_to_process:
            first_leaf = abjad.get.leaf(staff, 0)
            abjad.attach(
                abjad.LilyPondLiteral(
                    "\\override Staff.TimeSignature.style = #'single-digit"
                ),
                first_leaf,
            )


class PostProcessCengkokTimeBracket(
    abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __init__(self, render_video: bool = False):
        self._render_video = render_video

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        if self._render_video:
            make_moment_duration = 8
        else:
            make_moment_duration = 16

        for staff_group in container_to_process:
            for staff in staff_group:
                last_leaf = abjad.get.leaf(staff, -1)
                try:
                    abjad.attach(
                        abjad.BarLine("|.", format_slot="absolute_after"), last_leaf
                    )
                except Exception:
                    pass
                abjad.attach(
                    abjad.LilyPondLiteral(
                        r"\undo \hide Staff.BarLine", format_slot="absolute_after"
                    ),
                    last_leaf,
                )

                first_leaf = abjad.get.leaf(staff, 0)
                # only attach proportional notation for videos
                if self._render_video:
                    abjad.attach(
                        abjad.LilyPondLiteral(
                            "\\set Score.proportionalNotationDuration = #(ly:make-moment"
                            " 1/{})".format(make_moment_duration)
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
                        "\\override SpacingSpanner.base-shortest-duration = #(ly:make-moment 1/{})".format(
                            make_moment_duration
                        )
                    ),
                    first_leaf,
                )
                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\override Staff.Stem.stemlet-length = #0.75"
                    ),
                    first_leaf,
                )
                abjad.attach(
                    abjad.LilyPondLiteral("\\set strictBeatBeaming = ##t"),
                    first_leaf,
                )

                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\override Staff.NoteHead.style = #'baroque"
                    ),
                    first_leaf,
                )
                last_leaf = abjad.get.leaf(staff, -1)

                try:
                    abjad.attach(
                        abjad.BarLine("|.", format_slot="absolute_after"), last_leaf
                    )
                except Exception:
                    pass


class TicksMixin(abjad_process_container_routines.ProcessAbjadContainerRoutine):
    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        first_leaf = abjad.get.leaf(container_to_process, 0)
        abjad.attach(
            abjad.LilyPondLiteral(r"\stopStaff"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.TimeSignature.transparent = ##t"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.BarNumber.transparent = ##t"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.BarLine.transparent = ##t"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.Clef.transparent = ##t"), first_leaf
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.GridLine.transparent = ##t"),
            first_leaf,
        )
        # abjad.attach(
        #     abjad.LilyPondLiteral(r"\override NoteHead.transparent = ##t"), first_leaf
        # )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Stem.transparent = ##t"), first_leaf
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Beam.transparent = ##t"), first_leaf
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                r"\override Staff.StaffSymbol.line-count = #0", format_slot="before"
            ),
            first_leaf,
        )
