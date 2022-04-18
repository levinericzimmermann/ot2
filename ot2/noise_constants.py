import abjad

from mutwo import events
from mutwo import parameters

from ot2 import constants as ot2_constants
from ot2 import events as ot2_events


def _make_time_bracket(
    sequential_event: events.basic.SequentialEvent,
    start_or_start_range: events.time_brackets.TimeOrTimeRange,
    end_or_end_range: events.time_brackets.TimeOrTimeRange,
):
    return events.time_brackets.TimeBracket(
        [
            events.basic.TaggedSimultaneousEvent(
                [sequential_event], tag=ot2_constants.instruments.ID_NOISE
            )
        ],
        start_or_start_range,
        end_or_end_range,
    )


def _make_first_clicks_time_bracket():
    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(0, 0, 1, parameters.volumes.WesternVolume("ppp"))]
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((3 * 60) + 50, (3 * 60) + 55)
    end_or_end_range = ((4 * 60) + 20, (4 * 60) + 25)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_first_bass_drum_time_bracket():
    sequential_event = events.basic.SequentialEvent(
        [
            ot2_events.noises.Noise(
                0, 1, 1, parameters.volumes.WesternVolume("ppp"), is_periodic=True
            )
        ]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                ["mostly periodic, very low frequency range"],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((5 * 60) + 25, (5 * 60) + 35)
    end_or_end_range = ((6 * 60) + 40, (6 * 60) + 50)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_piano_duo_time_bracket():
    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(1, 1, 1, parameters.volumes.WesternVolume("ppp"))]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                [
                                    "add short or long rests ad lib., vary density and presence ad lib. (but keep generally quiet)"
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((9 * 60) + 10, (9 * 60) + 30)
    end_or_end_range = ((11 * 60) + 45, (12 * 60) + 15)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_dirty_pitch_bracket():
    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(3, 1, 1, parameters.volumes.WesternVolume("ppp"))]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                ["noisy, rather high pitch"],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((12 * 60) + 55, (13 * 60) + 0)
    end_or_end_range = ((13 * 60) + 30, (13 * 60) + 35)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_second_bass_drum_time_bracket():
    sequential_event = events.basic.SequentialEvent(
        [
            ot2_events.noises.Noise(
                0, 2, 1, parameters.volumes.WesternVolume("ppp"), is_periodic=True
            )
        ]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                ["mostly periodic, very low frequency range"],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((24 * 60) + 5, (24 * 60) + 15)
    end_or_end_range = ((25 * 60) + 15, (25 * 60) + 25)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_inaudible_time_bracket_islands():
    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(3, 0, 1, parameters.volumes.WesternVolume("ppp"))]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                [
                                    "almost inaudible islands, each island lasting approximately 10 to 15 seconds"
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((18 * 60) + 15, (18 * 60) + 35)
    end_or_end_range = ((20 * 60) + 35, (20 * 60) + 55)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_before_first_cantus_firmus_time_brackets():
    def _make_one():
        sequential_event = events.basic.SequentialEvent(
            [ot2_events.noises.Noise(3, 0, 1, parameters.volumes.WesternVolume("ppp"))]
        )
        sequential_event[0].notation_indicators.markup.direction = "up"
        start_or_start_range = ((25 * 60) + 40, (25 * 60) + 45)
        end_or_end_range = ((26 * 60) + 0, (26 * 60) + 10)
        return _make_time_bracket(
            sequential_event, start_or_start_range, end_or_end_range
        )

    def _make_two():
        sequential_event = events.basic.SequentialEvent(
            [ot2_events.noises.Noise(3, 1, 1, parameters.volumes.WesternVolume("ppp"))]
        )
        sequential_event[0].notation_indicators.markup.direction = "up"
        start_or_start_range = ((26 * 60) + 20, (26 * 60) + 25)
        end_or_end_range = ((26 * 60) + 40, (26 * 60) + 55)
        return _make_time_bracket(
            sequential_event, start_or_start_range, end_or_end_range
        )

    def _make_three():
        sequential_event = events.basic.SequentialEvent(
            [ot2_events.noises.Noise(3, 1, 1, parameters.volumes.WesternVolume("ppp"))]
        )
        sequential_event[0].notation_indicators.markup.direction = "up"
        start_or_start_range = ((27 * 60) + 18, (27 * 60) + 22)
        end_or_end_range = ((27 * 60) + 50, (27 * 60) + 55)
        return _make_time_bracket(
            sequential_event, start_or_start_range, end_or_end_range
        )

    def _make_four():
        sequential_event = events.basic.SequentialEvent(
            [ot2_events.noises.Noise(3, 2, 1, parameters.volumes.WesternVolume("ppp"))]
        )
        sequential_event[
            0
        ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
            "hspace",
            "#4",
            [
                abjad.markups.MarkupCommand(
                    "center-column",
                    [
                        abjad.markups.MarkupCommand(
                            "vspace",
                            "#-0.5",
                            [
                                abjad.markups.MarkupCommand(
                                    "small",
                                    ["sudden, aggressive"],
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        sequential_event[0].notation_indicators.markup.direction = "up"
        start_or_start_range = ((28 * 60) + 5, (28 * 60) + 10)
        end_or_end_range = ((28 * 60) + 35, (28 * 60) + 40)
        return _make_time_bracket(
            sequential_event, start_or_start_range, end_or_end_range
        )

    def _make_five():
        sequential_event = events.basic.SequentialEvent(
            [ot2_events.noises.Noise(1, 1, 1, parameters.volumes.WesternVolume("ppp"))]
        )
        start_or_start_range = ((29 * 60) + 25, (29 * 60) + 35)
        end_or_end_range = ((30 * 60) + 25, (30 * 60) + 30)
        return _make_time_bracket(
            sequential_event, start_or_start_range, end_or_end_range
        )

    def _make_six():
        sequential_event = events.basic.SequentialEvent(
            [ot2_events.noises.Noise(1, 0, 1, parameters.volumes.WesternVolume("ppp"))]
        )
        start_or_start_range = ((31 * 60) + 25, (31 * 60) + 35)
        end_or_end_range = ((32 * 60) + 25, (32 * 60) + 30)
        return _make_time_bracket(
            sequential_event, start_or_start_range, end_or_end_range
        )

    return (
        _make_one(),
        _make_two(),
        _make_three(),
        _make_four(),
        _make_five(),
        _make_six(),
    )


def _make_dark_clicks_at_end0():
    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(0, 0, 1, parameters.volumes.WesternVolume("ppp"))]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                [
                                    "spare, damped, lower frequency range, short denser islands can be added ad lib."
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = ((32 * 60) + 30, (32 * 60) + 55)
    # end_or_end_range = ((35 * 60) + 30, (35 * 60) + 50)
    # end_or_end_range = (33 * 60) + 0
    end_or_end_range = ((33 * 60) + 0, (33 * 60) + 5)
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_super_high_pitch_bracket():
    sequential_event = events.basic.SequentialEvent(
        [
            ot2_events.noises.Noise(
                3, 0, 1, parameters.volumes.WesternVolume("ppp"), is_pitch=True
            )
        ]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                ["very high clean pitch, exact pitch doesn't matter"],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = (33 * 60) + 5
    end_or_end_range = (33 * 60) + 30
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_dark_clicks_at_end1():
    sequential_event = events.basic.SequentialEvent(
        [ot2_events.noises.Noise(0, 0, 1, parameters.volumes.WesternVolume("ppp"))]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                [
                                    "spare, damped, lower frequency range, short denser islands can be added ad lib."
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = (33 * 60) + 30
    end_or_end_range = (35 * 60) + 0
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_super_high_pitch_bracket1():
    sequential_event = events.basic.SequentialEvent(
        [
            ot2_events.noises.Noise(
                3, 0, 1, parameters.volumes.WesternVolume("ppp"), is_pitch=True
            )
        ]
    )
    sequential_event[
        0
    ].notation_indicators.markup.content = abjad.markups.MarkupCommand(
        "hspace",
        "#3",
        [
            abjad.markups.MarkupCommand(
                "center-column",
                [
                    abjad.markups.MarkupCommand(
                        "vspace",
                        "#-0.5",
                        [
                            abjad.markups.MarkupCommand(
                                "small",
                                ["very high clean pitch, exact pitch doesn't matter"],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sequential_event[0].notation_indicators.markup.direction = "up"
    start_or_start_range = (35 * 60) + 0
    end_or_end_range = (36 * 60) + 0
    return _make_time_bracket(sequential_event, start_or_start_range, end_or_end_range)


def _make_noise_time_brackets() -> tuple[events.time_brackets.TimeBracket, ...]:
    time_brackets = [
        _make_first_clicks_time_bracket(),
        _make_first_bass_drum_time_bracket(),
        _make_piano_duo_time_bracket(),
        _make_dirty_pitch_bracket(),
        _make_inaudible_time_bracket_islands(),
        _make_second_bass_drum_time_bracket(),
    ]
    time_brackets.extend(_make_before_first_cantus_firmus_time_brackets())
    time_brackets.append(_make_dark_clicks_at_end0())
    time_brackets.append(_make_super_high_pitch_bracket())
    time_brackets.append(_make_dark_clicks_at_end1())
    time_brackets.append(_make_super_high_pitch_bracket1())
    return tuple(time_brackets)


NOISE_TIME_BRACKETS = _make_noise_time_brackets()
