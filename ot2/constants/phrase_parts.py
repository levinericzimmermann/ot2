PHRASE_PARTS = (
    # divided cantus firmus phrases
    # PART(((CANTUS_FIRMUS_MOTIV_INDEX, (NTH_PHRASE,)),), TEMPO)
    # 1
    (((0, (0,)),), 45),
    # 2
    (((0, (1, 2)),), 50),
    # 3
    (((0, (3,)),), 95),  # increase tempo for even smaller rest!
    # (((0, (3,)),), 61),  # increase tempo for even smaller rest!
    # (((0, (3,)),), 55),
    # 4
    (((1, (0, 1, 2)),), 50),
    # 5
    (((1, (3,)),), 42),  # slightly decrease tempo
    # (((1, (3,)),), 45),
    # 6
    (((2, (0, 1, 2, 3)),), 50),
    # 7
    (((3, (0, 1,)),), 120),  # make super fast tempo for a rather short break in the skipped parts
    # (((3, (0, 1,)),), 50),
    # 8
    (((3, (2, 3,)),), 120),  # make super fast tempo for a rather short break in the skipped parts
    # (((3, (2, 3,)),), 60),
    # 9
    # (((4, (0, 1, 2, 3)), (5, (0, 1))), 60),  # first part with river cengkok?? didn't work
    (((4, (0, 1, 2, 3)), ), 30),  # first part with river cengkok?? didn't work -> does work!
    # 10
    # (((5, (2, 3)), (6, (0,)),), 500),  # JUST SKIPPED
    (((5, (0, 1, 2, 3)), (6, (0,)),), 500),  # JUST SKIPPED
    # 11
    # (((6, (1, 2, 3,)), (7, (0, 1, 2, 3,))), 45),
    (((6, (1, 2, 3,)), (7, (0, 1, 2, 3,))), 500),  # also skipped
    # 12
    (((8, (0, 1, 2, 3,)),), 30),
    # 13
    # (((9, (0, 1, 2, 3,)), (10, (0, 1, 2, 3,))), 35),
    (((9, (0, 1, 2, 3,)),), 35),
)
