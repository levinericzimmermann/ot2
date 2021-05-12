"""Main file for rendering relevant data"""

if __name__ == "__main__":
    import abjad

    from mutwo.events import music
    from mutwo.parameters import tempos

    from ot2.events import colotomic_brackets
    from ot2.converters.frontends import abjad as ot2_abjad

    pattern = colotomic_brackets.ColotomicPattern(
        [
            colotomic_brackets.ColotomicElement([music.NoteLike("c", 0.5)]),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.5)]),
            colotomic_brackets.ColotomicElement(
                [music.NoteLike("e", 0.25), music.NoteLike("e", 0.25)]
            ),
            colotomic_brackets.ColotomicElement([music.NoteLike([], 0.75)]),
            colotomic_brackets.ColotomicElement([music.NoteLike("c", 0.5)]),
        ],
        tempo=tempos.TempoPoint((40, 50)),
    )

    pattern[1][0].playing_indicators.fermata.fermata_type = "fermata"

    converter = ot2_abjad.ColotomicPatternsToLilypondFileConverter()

    lilypond_file = converter.convert(
        [pattern, pattern.destructive_copy(), pattern.destructive_copy()]
    )
    print(abjad.lilypond(lilypond_file))
    abjad.show(lilypond_file)
