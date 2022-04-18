import abjad

from mutwo import converters
from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import events as ot2_events


class AddCadenza(
    converters.frontends.abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __call__(
        self,
        _,
        container_to_process: abjad.Container,
    ):
        first_leaf = abjad.get.leaf(container_to_process[0], 0)
        abjad.attach(
            abjad.LilyPondLiteral("\\cadenzaOn"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\omit Staff.TimeSignature"),
            first_leaf,
        )


def _make_standard_sequential_converter(
    quantiser=converters.frontends.abjad.FastSequentialEventToQuantizedAbjadContainerConverter(),
):
    return converters.frontends.abjad.SequentialEventToAbjadVoiceConverter(
        sequential_event_to_quantized_abjad_container_converter=quantiser,
        mutwo_pitch_to_abjad_pitch_converter=converters.frontends.abjad.MutwoPitchToHEJIAbjadPitchConverter(
            ot2_constants.concert_pitch.REFERENCE.pitch_class_name
        ),
        tempo_envelope_to_abjad_attachment_tempo_converter=None,
        mutwo_volume_to_abjad_attachment_dynamic_converter=None,
    )


def _make_standard_score_converter(
    sequential_event_to_abjad_voice_converter=_make_standard_sequential_converter(),
    post_process_abjad_container_routines=[],
):
    return converters.frontends.abjad.NestedComplexEventToAbjadContainerConverter(
        converters.frontends.abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
            (sequential_event_to_abjad_voice_converter,)
        ),
        abjad.Score,
        "Score",
        pre_process_abjad_container_routines=[],
        post_process_abjad_container_routines=[
            converters.frontends.abjad_process_container_routines.AddAccidentalStyle(
                "dodecaphonic"
            )
        ]
        + post_process_abjad_container_routines,
    )


def illustrate(
    name: str,
    *abjad_score: abjad.Score,
    add_book_preamble: bool = True,
    add_ekmeheji: bool = True,
    title: str = None,
):
    margin = 0
    layout_block = abjad.Block("layout")
    layout_block.items.append(r"short-indent = {}\mm".format(margin))
    layout_block.items.append(r"ragged-last = ##f")
    layout_block.items.append(r"indent = {}\mm".format(margin))
    paper_block = abjad.Block("paper")
    paper_block.items.append(
        r"""#(define fonts
    (make-pango-font-tree "EB Garamond"
                          "Nimbus Sans"
                          "Luxi Mono"
                          (/ staff-height pt 20)))"""
    )
    paper_block.items.append(
        r"""score-system-spacing =
      #'((basic-distance . 30)
       (minimum-distance . 18)
       (padding . 1)
       (stretchability . 12))"""
    )
    includes = []
    if add_ekmeheji:
        includes.append("ekme-heji-ref-c-not-tuned.ily")
    if add_book_preamble:
        includes.append("lilypond-book-preamble.ly")
    lilypond_file = abjad.LilyPondFile(
        items=list(abjad_score) + [paper_block, layout_block],
        includes=includes,
    )
    if title:
        header_block = abjad.Block("header")
        header_block.title = title
        header_block.tagline = '""'
        lilypond_file.items.append(header_block)

    abjad.persist.as_pdf(
        lilypond_file, f"{ot2_constants.paths.ILLUSTRATIONS_PATH}/{name}.pdf"
    )


def illustrate_microtonal_pitches_for_sustaining_instrument(
    sustaining_instrument_tag: str,
    add_ratio: bool = False,
    make_clarinet_version: bool = True,
):
    # first collect all relevant pitches
    filtered_time_brackets = ot2_constants.time_brackets_container.TIME_BRACKETS.filter(
        sustaining_instrument_tag
    )

    relevant_pitches_as_exponents = set([])
    for time_bracket in filtered_time_brackets:
        for tagged_event in time_bracket:
            if tagged_event.tag == sustaining_instrument_tag:
                pitch_or_pitches_per_event = tuple(
                    filter(
                        bool, tagged_event.get_parameter("pitch_or_pitches", flat=True)
                    )
                )
                for pitch_or_pitches in pitch_or_pitches_per_event:
                    for pitch in pitch_or_pitches:
                        relevant_pitches_as_exponents.add(pitch.exponents)

    print(
        f"{sustaining_instrument_tag} has to play {len(relevant_pitches_as_exponents)} different pitch classes!"
    )
    relevant_pitches = sorted(
        map(parameters.pitches.JustIntonationPitch, relevant_pitches_as_exponents)
    )

    score_converter = _make_standard_score_converter()

    sequential_event = events.basic.SequentialEvent([])
    for pitch in relevant_pitches:
        note = events.music.NoteLike([], 1)
        note.notation_indicators.cent_deviation.deviation = (
            pitch.cent_deviation_from_closest_western_pitch_class
        )
        if add_ratio:
            note.notation_indicators.markup.content = (
                f"{pitch.numerator}/{pitch.denominator}"
            )
            note.notation_indicators.markup.direction = "^"

        is_sustaining_instrument_1 = (
            sustaining_instrument_tag == ot2_constants.instruments.ID_SUS1
        )
        if is_sustaining_instrument_1 and make_clarinet_version:
            pitch += parameters.pitches.JustIntonationPitch("9/8")

        note.pitch_or_pitches = pitch
        # if is_sustaining_instrument_1:
        #     ot2_constants.instruments.apply_clarient_fingerings(note)
        sequential_event.append(note)

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    abjad.attach(
        abjad.LilyPondLiteral("\\override Score.SpacingSpanner spacing-increment = 4"),
        abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\omit Staff.BarLine"),
        abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral(
            "\\override Score.BarNumber.break-visibility = ##(#f #f #f)"
        ),
        abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\omit Staff.TimeSignature"),
        abjad.get.leaf(score, 0),
    )
    score_block = abjad.Block("score")
    score_block.items.append(score)

    name = f"{sustaining_instrument_tag}_microtonal_pitches"

    if add_ratio:
        name += "_with_ratios"

    illustrate(
        name,
        score_block,
        add_book_preamble=False,
        add_ekmeheji=True,
        title=f'"Pitch list for {ot2_constants.instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[sustaining_instrument_tag]}"',
    )


def illustrate_microtonal_pitches_for_sustaining_instruments(
    make_clarinet_version: bool,
):
    for sustaining_instrument_tag in (
        ot2_constants.instruments.ID_SUS0,
        ot2_constants.instruments.ID_SUS1,
        ot2_constants.instruments.ID_SUS2,
    ):
        illustrate_microtonal_pitches_for_sustaining_instrument(
            sustaining_instrument_tag, make_clarinet_version=make_clarinet_version
        )


def illustrate_microtonal_pitches_for_sustaining_instruments_with_ratio_notation(
    make_clarinet_version: bool = True,
):
    for sustaining_instrument_tag in (
        ot2_constants.instruments.ID_SUS0,
        ot2_constants.instruments.ID_SUS1,
        ot2_constants.instruments.ID_SUS2,
    ):
        illustrate_microtonal_pitches_for_sustaining_instrument(
            sustaining_instrument_tag,
            add_ratio=True,
            make_clarinet_version=make_clarinet_version,
        )


def illustrate_clarinet_fingerings():
    score_converter = _make_standard_score_converter()

    nth_fingering = 0
    for (
        pitch,
        data,
    ) in (
        ot2_constants.instruments.CLARINET_MICROTONAL_PITCHES_TO_FINGERING_AND_EMBOUCHURE.items()
    ):
        pitch = parameters.pitches.JustIntonationPitch(pitch)
        fingering, embouchure = data
        note = events.music.NoteLike(pitch, 1)
        if fingering:
            note.playing_indicators.fingering.cc = fingering.cc
            note.playing_indicators.fingering.rh = fingering.rh
            note.playing_indicators.fingering.lh = fingering.lh

        if embouchure:
            note.notation_indicators.markup.content = embouchure
            note.notation_indicators.markup.direction = "up"

        sequential_event = events.basic.SequentialEvent([note])
        score = score_converter.convert(
            events.basic.SimultaneousEvent([sequential_event])
        )

        score_block = abjad.Block("score")
        score_block.items.append(score)
        name = f"clarinet/fingering_{nth_fingering}"

        nth_fingering += 1

        illustrate(
            name,
            score_block,
            add_book_preamble=False,
            add_ekmeheji=True,
        )


def illustrate_noises():
    score_converter = _make_standard_score_converter(
        _make_standard_sequential_converter(
            converters.frontends.abjad.FastSequentialEventToDurationLineBasedQuantizedAbjadContainerConverter()
        )
    )

    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(1, 2, 1, parameters.volumes.WesternVolume("mf"))]
    )

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    score_block = abjad.Block("score")
    score_block.items.append(score)
    illustrate(
        "noise_0",
        score_block,
        add_book_preamble=True,
        add_ekmeheji=False,
    )


def main(make_clarinet_version: bool = True):
    # illustrate_clarinet_fingerings()  # for debugging wrong fingerings
    illustrate_microtonal_pitches_for_sustaining_instruments(make_clarinet_version)
    illustrate_microtonal_pitches_for_sustaining_instruments_with_ratio_notation(
        make_clarinet_version
    )
    illustrate_noises()
