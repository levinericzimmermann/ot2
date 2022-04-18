import typing
import warnings

from mutwo.parameters import pitches

from ot2.constants import concert_pitch
from ot2.parameters import ambitus
from ot2.parameters import playing_indicators


def _convert_western_pitch_to_ji_pitch(
    western_pitch: pitches.WesternPitch,
) -> pitches.JustIntonationPitch:
    difference_to_reference = western_pitch - concert_pitch.REFERENCE
    return pitches.JustIntonationPitch(
        pitches.JustIntonationPitch.cents_to_ratio(
            difference_to_reference * 100
        ).limit_denominator(1000)
    )


# instrument ids
ID_PERCUSSIVE = "percussive"
ID_DRONE = "drone"
ID_DRONE_SYNTH = "droneSynthesized"
ID_NOISE = "noise"
ID_SUS0 = "sustaining0"
ID_SUS1 = "sustaining1"
ID_SUS2 = "sustaining2"
ID_KEYBOARD = "keyboard"
ID_GONG = "gong"
PILLOW_IDS = ("pillow0", "pillow1", "pillow2", "pillow3")


ID_SUS_TO_ID_SINE = {ID_SUS0: "sine0", ID_SUS1: "sine1", ID_SUS2: "sine2"}

INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME = {
    ID_PERCUSSIVE: "perc. instr.",
    ID_DRONE: "drone",
    ID_SUS0: "sus. ins. 1",
    ID_SUS1: "sus. ins. 2",
    ID_SUS2: "sus. ins. 3",
    ID_NOISE: "noise",
    ID_KEYBOARD: "keyboard",
}

INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME = {
    ID_PERCUSSIVE: "p.i.",
    ID_DRONE: "d.",
    ID_SUS0: "s.i. 1",
    ID_SUS1: "s.i. 2",
    ID_SUS2: "s.i. 3",
    ID_NOISE: "n.",
    ID_KEYBOARD: "kb.",
}

INSTRUMENT_ID_TO_INDEX = {
    ID_SUS0: 0,
    ID_SUS1: 1,
    ID_SUS2: 2,
    ID_DRONE: 3,
    ID_PERCUSSIVE: 4,
    ID_NOISE: 5,
}

AMBITUS_SUSTAINING_INSTRUMENTS_WESTERN_PITCHES = ambitus.Ambitus(
    pitches.WesternPitch("af", 3),
    pitches.WesternPitch("e", 5),
)

AMBITUS_SUSTAINING_INSTRUMENTS_JUST_INTONATION_PITCHES = ambitus.Ambitus(
    _convert_western_pitch_to_ji_pitch(
        AMBITUS_SUSTAINING_INSTRUMENTS_WESTERN_PITCHES.borders[0]
    ),
    _convert_western_pitch_to_ji_pitch(
        AMBITUS_SUSTAINING_INSTRUMENTS_WESTERN_PITCHES.borders[1]
    ),
)

AMBITUS_DRONE_INSTRUMENT = ambitus.Ambitus(
    pitches.JustIntonationPitch("1/4"), pitches.JustIntonationPitch("1/2")
)

AMBITUS_KEYBOARD = ambitus.Ambitus(
    pitches.JustIntonationPitch("1/4"), pitches.JustIntonationPitch("4/1")
)

# how many voices (staves) one instrument owns
INSTRUMENT_TO_N_VOICES = {
    ID_PERCUSSIVE: 1,
    ID_DRONE: 1,
    ID_NOISE: 1,
    ID_SUS0: 1,
    ID_SUS1: 1,
    ID_SUS2: 1,
    ID_KEYBOARD: 2,
}


PERCUSSION_EXPONENTS_TO_WRITTEN_PITCH = {
    tuple([]): pitches.WesternPitch("g", octave=3),
    (-1, 1): pitches.WesternPitch("b", octave=3),
    (-2, 0, 1): pitches.WesternPitch("d", octave=4),
    (-2, 0, 0, 1): pitches.WesternPitch("f", octave=4),
}


CLARINET_MICROTONAL_PITCHES_TO_FINGERING_AND_EMBOUCHURE: typing.Dict[
    tuple[int, ...], playing_indicators.Fingering
] = {
    pitch.exponents: (fingering, embouchure)
    for pitch, fingering, embouchure in (
        (
            pitches.JustIntonationPitch("16/33"),
            playing_indicators.Fingering(
                cc="one two three five six".split(" "),
                lh="thumb e".split(" "),
                rh="fis".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("1/2"),
            playing_indicators.Fingering(
                cc="one two three five six".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("28/55"),
            playing_indicators.Fingering(
                cc="one two three six".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("21/40"),
            playing_indicators.Fingering(
                cc="one two three four1h five1h six1h".split(" "),
                lh="thumb e".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("8/15"),
            playing_indicators.Fingering(
                cc="one two three".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("6/11"),
            playing_indicators.Fingering(
                cc="one two three five six".split(" "),
                lh="thumb cis".split(" "),
                rh="f".split(" "),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("49/88"),
            playing_indicators.Fingering(
                cc="one two three five six".split(" "),
                lh="thumb cis".split(" "),
                rh="gis".split(" "),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("14/25"),
            playing_indicators.Fingering(
                cc="one two five six".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("9/16"),
            playing_indicators.Fingering(
                cc="one two three five".split(" "),
                lh="thumb cis".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("32/55"),
            playing_indicators.Fingering(
                cc="one two four five six".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("7/12"),
            playing_indicators.Fingering(
                cc="one two four five six".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("44/75"),
            playing_indicators.Fingering(
                cc="one two four five".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("49/80"),
            playing_indicators.Fingering(
                cc="one two three five six".split(" "),
                lh="cis thumb".split(" "),
                rh="four".split(" "),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("315/512"),
            playing_indicators.Fingering(
                cc="one two three five six".split(" "),
                lh="cis thumb".split(" "),
                rh="four".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("5/8"),
            playing_indicators.Fingering(
                cc="one two three".split(" "),
                lh="thumb cis".split(" "),
                rh="four".split(" "),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("16/25"),
            playing_indicators.Fingering(
                cc="one two three".split(" "),
                lh="thumb ees".split(" "),
                rh="four".split(" "),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("77/120"),
            playing_indicators.Fingering(
                cc="one two three".split(" "),
                lh="thumb ees".split(" "),
                rh="four".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("35/54"),
            playing_indicators.Fingering(
                cc="one two four five six".split(" "),
                lh="ees thumb".split(" "),
                rh="four".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("21/32"),
            playing_indicators.Fingering(
                cc="one four five".split(" "),
                lh="ees thumb e".split(" "),
                rh=tuple([]),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("112/165"),
            playing_indicators.Fingering(
                cc="two four five six".split(" "),
                lh="thumb cis".split(" "),
                rh="f".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("52/75"),
            playing_indicators.Fingering(
                cc="four five six".split(" "),
                lh="thumb fis".split(" "),
                rh="f".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("7/10"),
            playing_indicators.Fingering(
                cc="four".split(" "),
                lh="thumb".split(" "),
                rh=tuple([]),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("8/11"),
            playing_indicators.Fingering(
                cc="one five".split(" "),
                lh="thumb".split(" "),
                rh="three four".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("20/27"),
            playing_indicators.Fingering(
                cc="two".split(" "),
                lh="thumb".split(" "),
                rh="three four".split(" "),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("3/4"),
            playing_indicators.Fingering(
                cc="one five".split(" "),
                lh=tuple([]),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("208/275"),
            playing_indicators.Fingering(
                cc="one".split(" "),
                lh=tuple([]),
                rh="four".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("128/165"),
            playing_indicators.Fingering(
                cc="two three four five six".split(" "),
                lh="e".split(" "),
                rh="f".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("7/9"),
            playing_indicators.Fingering(
                cc="two three four five six".split(" "),
                lh=tuple([]),
                rh="f".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("35/44"),
            playing_indicators.Fingering(
                cc="three four five six".split(" "),
                lh=tuple([]),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("13/16"),
            playing_indicators.Fingering(
                cc="one two four five".split(" "),
                lh="gis".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("48/55"),
            playing_indicators.Fingering(
                cc="four five six".split(" "),
                lh="thumb a".split(" "),
                rh=tuple([]),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("7/8"),
            playing_indicators.Fingering(
                cc="three four five six".split(" "),
                lh="thumb a".split(" "),
                rh="f".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("539/600"),
            playing_indicators.Fingering(
                cc="two three five six".split(" "),
                lh="a".split(" "),
                rh="two".split(" "),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("294/325"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="a".split(" "),
                rh="two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("49/54"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="a".split(" "),
                rh=tuple([]),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("10/11"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="gis thumb".split(" "),
                rh="two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("11/12"),
            playing_indicators.Fingering(
                cc="one two".split(" "),
                lh="thumb R a".split(" "),
                rh="four".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("14/15"),
            playing_indicators.Fingering(
                cc="one two".split(" "),
                lh="thumb a".split(" "),
                rh="two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("189/200"),
            None,
            "↓",
        ),
        (
            pitches.JustIntonationPitch("32/33"),
            playing_indicators.Fingering(
                cc="one two three".split(" "),
                lh="thumb a R".split(" "),
                rh="two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("49/48"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="a".split(" "),
                rh="one".split(" "),
            ),
            None,
        ),
        # old fingering
        # (
        #     pitches.JustIntonationPitch("91/88"),
        #     playing_indicators.Fingering(
        #         cc="six".split(" "),
        #         lh="a".split(" "),
        #         rh="one".split(" "),
        #     ),
        #     None,
        # ),
        (
            pitches.JustIntonationPitch("91/88"),
            playing_indicators.Fingering(
                cc="one two three six".split(" "),
                lh="thumb e".split(" "),
                rh="one".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("16/15"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="thumb R a".split(" "),
                rh="one two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("77/72"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="thumb R a".split(" "),
                rh="one two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("49/45"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R fis".split(" "),
                rh="one two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("12/11"),
            playing_indicators.Fingering(
                cc=tuple([]),
                lh="a R".split(" "),
                rh="one two".split(" "),
            ),
            None,
        ),
        # no need for microtonal fingering (only very small difference)
        (
            pitches.JustIntonationPitch("28/25"),
            None,
            "↓",
        ),
        (
            pitches.JustIntonationPitch("8/7"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R fis".split(" "),
                rh="one two".split(" "),
            ),
            None,
        ),
        # no fingering found yet!
        (
            pitches.JustIntonationPitch("7/6"),
            None,
            "(1x oct. lower)",
        ),
        (
            pitches.JustIntonationPitch("6/5"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R".split(" "),
                rh="one".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("49/40"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R gis".split(" "),
                rh="one".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("27/22"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R gis".split(" "),
                rh="one".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("5/4"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb e R".split(" "),
                rh="gis".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("91/72"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R".split(" "),
                rh="gis".split(" "),
            ),
            "↓",
        ),
        (
            pitches.JustIntonationPitch("14/11"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R".split(" "),
                rh="gis".split(" "),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("77/60"),
            playing_indicators.Fingering(
                cc="one two three four five six".split(" "),
                lh="thumb R".split(" "),
                rh="gis two".split(" "),
            ),
            None,
        ),
        (
            pitches.JustIntonationPitch("15/11"),
            playing_indicators.Fingering(
                cc="one two three four six".split(" "),
                lh="thumb R".split(" "),
                rh="fis".split(" "),
            ),
            "↑",
        ),
        (
            pitches.JustIntonationPitch("273/200"),
            playing_indicators.Fingering(
                cc="one two three four six".split(" "),
                lh="thumb R".split(" "),
                rh=tuple([]),
            ),
            "↓",
        ),
    )
}


def apply_clarient_fingerings(simple_event):
    if hasattr(simple_event, "pitch_or_pitches") and simple_event.pitch_or_pitches:
        pitch_or_pitches = simple_event.pitch_or_pitches
        pitch_to_investigate = pitch_or_pitches[0]
        if hasattr(pitch_to_investigate, "exponents"):
            try:
                (
                    microtonal_fingering,
                    embouchure,
                ) = CLARINET_MICROTONAL_PITCHES_TO_FINGERING_AND_EMBOUCHURE[
                    pitch_to_investigate.exponents
                ]
            except KeyError:
                message = (
                    "No fingering defined yet for microtonal pitch"
                    f" {pitch_to_investigate}!"
                )
                warnings.warn(message)
                microtonal_fingering = None
                embouchure = None

            if microtonal_fingering:
                simple_event.playing_indicators.fingering.cc = microtonal_fingering.cc
                simple_event.playing_indicators.fingering.lh = microtonal_fingering.lh
                simple_event.playing_indicators.fingering.rh = microtonal_fingering.rh

            if embouchure:
                simple_event.playing_indicators.embouchure.hint = embouchure
                # simple_event.notation_indicators.markup.content = embouchure
                # simple_event.notation_indicators.markup.direction = "up"
