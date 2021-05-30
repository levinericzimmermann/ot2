import itertools

PERCUSSION_PITCH_TO_PERCUSSION_SAMPLES_CYCLE = {
    "g": itertools.cycle(
        (
            "ot2/samples/percussion/framedrum/HDrumL_Hit_v2_rr2_Sum.wav",
            "ot2/samples/percussion/framedrum/HDrumL_Hit_v2_rr1_Sum.wav",
        )
    ),
    "b": itertools.cycle(
        (
            "ot2/samples/percussion/framedrum/HDrumL_HitMuted_v2_rr1_Sum.wav",
            "ot2/samples/percussion/framedrum/HDrumS_HitMuted_v2_rr1_Sum.wav",
            "ot2/samples/percussion/framedrum/HDrumL_HitMuted_v2_rr1_Sum.wav",
        )
    ),
    "d": itertools.cycle(
        (
            "ot2/samples/percussion/cymbals/0.wav",
            "ot2/samples/percussion/cymbals/1.wav",
            "ot2/samples/percussion/cymbals/2.wav",
        )
    ),
    "f": itertools.cycle(
        # the woodblock samples are kind of noisy..
        # (
        #     "ot2/samples/percussion/woodblock/wood_click_f_rr1.wav",
        #     "ot2/samples/percussion/woodblock/wood_click_f_rr2.wav",
        #     "ot2/samples/percussion/woodblock/wood_click3_vl2.wav",
        #     "ot2/samples/percussion/woodblock/wood_click3_vl1.wav",
        # )
        (
            "ot2/samples/percussion/claves/claves_mp.wav",
            "ot2/samples/percussion/claves/claves_ff.wav",
            "ot2/samples/percussion/claves/claves_mf_2.wav",
            "ot2/samples/percussion/claves/claves_pp1.wav",
            "ot2/samples/percussion/claves/claves_mf.wav",
            "ot2/samples/percussion/claves/claves_mf_3.wav",
        )
    ),
}


FILES_PATH = "ot2/converters/frontends"
