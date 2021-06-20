from mutwo.parameters import pitches

INTERVALS = (
    (pitches.JustIntonationPitch("7/4"),),
    (pitches.JustIntonationPitch("8/5"),),
    (pitches.JustIntonationPitch("3/2"), pitches.JustIntonationPitch("16/11")),
    (pitches.JustIntonationPitch("5/4"),),
    (pitches.JustIntonationPitch("16/11"),),
    (pitches.JustIntonationPitch("4/3"),),
    (pitches.JustIntonationPitch("7/4"),),
    (pitches.JustIntonationPitch("7/4"),),
    (pitches.JustIntonationPitch("16/11"),),
    (pitches.JustIntonationPitch("4/3"),),
    (pitches.JustIntonationPitch("5/4"),),
    (pitches.JustIntonationPitch("16/11"), pitches.JustIntonationPitch("3/2"),),
    (pitches.JustIntonationPitch("8/5"),),
    (pitches.JustIntonationPitch("7/4"),),
)
"""JI Counterpart for each note of cantus firmus"""


START_PITCH_TO_ROOT = {
    "a": pitches.JustIntonationPitch("1/1"),
    "c": pitches.JustIntonationPitch("6/5"),
    "e": pitches.JustIntonationPitch("3/2"),
    "d": pitches.JustIntonationPitch("4/3"),
    "g": pitches.JustIntonationPitch("16/9"),
}
