"""Main file for rendering relevant data"""

if __name__ == "__main__":
    import abjad

    from ot2.converters.frontends import abjad as ot2_abjad
    from ot2.converters.frontends import csound as ot2_csound
    from ot2.converters import symmetrical

    import ot2

    nested_sequential_event_converter = (
        symmetrical.colotomic_brackets.ColotomicPatternToNestedSequentialEventConverter()
    )
    csound_converter = ot2_csound.NestedSequentialEventToSoundFileConverter()
    csound_converter.convert(
        nested_sequential_event_converter.convert(
            ot2.constants.colotomic_pattern.COLOTOMIC_PATTERNS[0]
        )
    )

    lilypond_file_converter = ot2_abjad.ColotomicPatternsToLilypondFileConverter()

    lilypond_file = lilypond_file_converter.convert(
        ot2.constants.colotomic_pattern.COLOTOMIC_PATTERNS
    )
    print(abjad.lilypond(lilypond_file))
    abjad.show(lilypond_file)
