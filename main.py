"""Main file for rendering relevant data"""

if __name__ == "__main__":
    import abjad

    from mutwo.events import music
    from mutwo.parameters import tempos

    from ot2.events import colotomic_brackets
    from ot2.converters.frontends import abjad as ot2_abjad
    from ot2.converters.frontends import csound as ot2_csound
    from ot2.converters import symmetrical

    pattern = colotomic_brackets.ColotomicPattern(
        [
            colotomic_brackets.ColotomicElement([music.NoteLike("d", 0.5)]),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.5)]),
            colotomic_brackets.ColotomicElement(
                [music.NoteLike("d", 0.25), music.NoteLike("f", 0.25)]
            ),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
            colotomic_brackets.ColotomicElement([music.NoteLike("g", 0.5)]),
        ],
        tempo=tempos.TempoPoint((10, 20)),
    )

    pattern[1][0].playing_indicators.fermata.fermata_type = "fermata"

    nested_sequential_event_converter = (
        symmetrical.colotomic_brackets.ColotomicPatternToNestedSequentialEventConverter()
    )
    csound_converter = ot2_csound.NestedSequentialEventToSoundFileConverter()
    csound_converter.convert(nested_sequential_event_converter.convert(pattern))

    lilypond_file_converter = ot2_abjad.ColotomicPatternsToLilypondFileConverter()

    lilypond_file = lilypond_file_converter.convert(
        [pattern, pattern.destructive_copy(), pattern.destructive_copy()]
    )
    print(abjad.lilypond(lilypond_file))
    abjad.show(lilypond_file)
