from mutwo.parameters import pitches

scale_to_tune = tuple(
    pitches.JustIntonationPitch(pitch)
    for pitch in "1/1 9/8 8/7 5/4 4/3 11/8 16/11 3/2 8/5 7/4 16/9".split(" ")
)

roots = tuple(
    pitches.JustIntonationPitch(pitch)
    for pitch in "3/2 4/3 5/4 8/5 7/4 8/7 11/8 16/11".split(" ")
)

transpose = pitches.JustIntonationPitch("3/4")

for root in roots:
    name = "{}_{}.scl".format(root.primes[-1], root.tonality)
    with open("scl/{}".format(name), "w") as f:
        f.write("! {}\n".format(name))
        f.write("!\n")
        f.write("JustIntonationScale_{}\n".format(name))
        f.write("12\n")
        f.write("!\n")
        for pitch in scale_to_tune:
            new_pitch = pitch + transpose + root
            f.write("{}/{}\n".format(new_pitch.numerator, new_pitch.denominator))
        f.write("2/1\n")
