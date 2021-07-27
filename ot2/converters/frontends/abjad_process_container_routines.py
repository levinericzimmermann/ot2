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
            self._add_accidental_style = abjad_process_container_routines.AddAccidentalStyle(
                accidental_style
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
    def __init__(self):
        super().__init__(instruments.ID_KEYBOARD)

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        # attach keyboard clefs
        abjad.attach(abjad.Clef("treble"), abjad.get.leaf(container_to_process[0], 0))
        if len(container_to_process) > 1:
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
        abjad.attach(abjad.Clef("bass"), abjad.get.leaf(container_to_process[0], 0))


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
    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
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
