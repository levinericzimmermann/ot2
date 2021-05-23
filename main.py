"""Main file for rendering relevant data"""

from ot2.events import time_brackets


def _run():
    from mutwo.events import music
    from mutwo.parameters import tempos

    from ot2 import events
    from ot2 import generators

    colotomic_bracket_generators = (
        generators.colotomic_brackets.HoquetusDingDong(
            (11, 5, 11, 3, 5),
            lambda: events.colotomic_brackets.ColotomicPattern(
                [
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("g", 6, "mp")]
                    ),
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("f", 4, "mp")]
                    ),
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("f", 4, "mp")]
                    ),
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("f", 4, "mp")]
                    ),
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("b", 6, "mp")]
                    ),
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("f", 4, "mp")]
                    ),
                    events.colotomic_brackets.ColotomicElement(
                        [music.NoteLike("f", 4, "mp")]
                    ),
                ],
                tempo=tempos.TempoPoint(40),
                n_repetitions=3,
            ),
        ),
    )
    for colotomic_bracket_generator in colotomic_bracket_generators:
        (
            colotomic_patterns_to_add,
            colotomic_brackets_to_add,
        ) = colotomic_bracket_generator.run()
        generators.side_effects.colotomic_brackets.add_colotomic_patterns_and_colotomic_brackets(
            colotomic_patterns_to_add, colotomic_brackets_to_add
        )


def _make_converted_colotomic_patterns():
    from mutwo.events import basic
    from ot2.converters import symmetrical

    import ot2

    nested_sequential_event_converter = (
        symmetrical.colotomic_brackets.ColotomicPatternToNestedSequentialEventConverter()
    )
    converted_patterns = basic.SequentialEvent(
        [
            nested_sequential_event_converter.convert(pattern)
            for pattern in ot2.constants.colotomic_pattern.COLOTOMIC_PATTERNS
        ]
    )
    return converted_patterns


def _make_time_brackets_container(
    converted_colotomic_pattens,
) -> time_brackets.TimeBracketContainer:
    from ot2.constants import colotomic_brackets_container
    from ot2.converters import symmetrical

    converter = symmetrical.colotomic_brackets.ColotomicBracketToTimeBracketConverter(
        converted_colotomic_pattens
    )
    time_brackets_container = time_brackets.TimeBracketContainer(
        tuple(
            converter.convert(colotomic_bracket)
            for colotomic_bracket in colotomic_brackets_container.COLOTOMIC_BRACKETS_CONTAINER
        )
    )

    return time_brackets_container


def _render_colotomic_pattern(converted_patterns):
    import abjad

    from ot2.converters.frontends import abjad as ot2_abjad
    from ot2.converters.frontends import csound as ot2_csound

    import ot2

    # render sound file
    csound_converter = ot2_csound.PercussiveSequentialEventToSoundFileConverter()
    csound_converter.convert(converted_patterns)

    # render notation
    lilypond_file_converter = ot2_abjad.ColotomicPatternsToLilypondFileConverter()
    lilypond_file = lilypond_file_converter.convert(
        ot2.constants.colotomic_pattern.COLOTOMIC_PATTERNS
    )
    abjad.persist.as_pdf(lilypond_file, "builds/percussion_brackets.pdf")
    # abjad.show(lilypond_file)


def _render_drone_instrument(
    time_brackets_container: time_brackets.TimeBracketContainer,
):
    from ot2.constants import instruments
    from ot2.converters import frontends
    from ot2.converters import symmetrical

    relevant_time_brackets = time_brackets_container.filter(instruments.ID_DRONE)

    # render sound file
    simultaneous_event_converter = symmetrical.time_brackets.TimeBracketsToSimultaneousEventConverter(
        instruments.ID_DRONE, instruments.INSTRUMENT_TO_N_VOICES[instruments.ID_DRONE]
    )
    sound_file_converter = frontends.midi.DroneEventToMidiFileConverter()
    simultaneous_event = simultaneous_event_converter.convert(relevant_time_brackets)
    sound_file_converter.convert(simultaneous_event)

    # render notation
    pass


def _render_sustaining_instruments(
    time_brackets_container: time_brackets.TimeBracketContainer,
):
    from ot2.constants import instruments
    from ot2.converters import frontends
    from ot2.converters import symmetrical

    for nth_sustaining_instrument, instrument_id in enumerate(
        (instruments.ID_SUS0, instruments.ID_SUS1, instruments.ID_SUS2)
    ):
        relevant_time_brackets = time_brackets_container.filter(instrument_id)

        # render sound file
        simultaneous_event_converter = symmetrical.time_brackets.TimeBracketsToSimultaneousEventConverter(
            instrument_id, instruments.INSTRUMENT_TO_N_VOICES[instrument_id]
        )
        midi_file_converter = frontends.midi.SustainingInstrumentEventToMidiFileConverter(
            nth_sustaining_instrument
        )
        simultaneous_event = simultaneous_event_converter.convert(
            relevant_time_brackets
        )
        midi_file_converter.convert(simultaneous_event)


if __name__ == "__main__":
    _run()

    converted_colotomic_pattens = _make_converted_colotomic_patterns()
    time_brackets_container = _make_time_brackets_container(converted_colotomic_pattens)

    _render_drone_instrument(time_brackets_container)
    _render_sustaining_instruments(time_brackets_container)
    _render_colotomic_pattern(converted_colotomic_pattens)
