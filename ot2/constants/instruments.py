from mutwo.parameters import pitches

# instrument ids
ID_PERCUSSIVE = "percussive"
ID_DRONE = "drone"
ID_NOISE = "noise"
ID_SUS0 = "sustaining0"
ID_SUS1 = "sustaining1"
ID_SUS2 = "sustaining2"

AMBITUS_SUSTAINING_INSTRUMENTS = (
    pitches.WesternPitch("af", 3),
    pitches.WesternPitch("e", 5),
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
