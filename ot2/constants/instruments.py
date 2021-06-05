from mutwo.parameters import pitches

from ot2.constants import concert_pitch
from ot2.parameters import ambitus


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
ID_NOISE = "noise"
ID_SUS0 = "sustaining0"
ID_SUS1 = "sustaining1"
ID_SUS2 = "sustaining2"

INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME = {
    ID_PERCUSSIVE: "percussive instrument(s)",
    ID_DRONE: "drone",
    ID_SUS0: "sustaining instrument 1",
    ID_SUS1: "sustaining instrument 2",
    ID_SUS2: "sustaining instrument 3",
    ID_NOISE: "noise",
}

INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME = {
    ID_PERCUSSIVE: "p.i.",
    ID_DRONE: "d.",
    ID_SUS0: "s.i. 1",
    ID_SUS1: "s.i. 2",
    ID_SUS2: "s.i. 3",
    ID_NOISE: "n.",
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
    pitches.WesternPitch("af", 3), pitches.WesternPitch("e", 5),
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

# how many voices (staves) one instrument owns
INSTRUMENT_TO_N_VOICES = {
    ID_PERCUSSIVE: 1,
    ID_DRONE: 1,
    ID_NOISE: 1,
    ID_SUS0: 1,
    ID_SUS1: 1,
    ID_SUS2: 1,
}
