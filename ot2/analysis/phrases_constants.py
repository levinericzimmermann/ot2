PULSE_DURATION_IN_SECONDS_AT_START = 30
EVENT_INDEX_TO_PULSE_TRANSITION_DATA = {
    # event_index:
    #   ((min_duration_of_pulse, max_duration_of_pulse),
    #    percentage_how_many_steps_shall_rise)
    50: ((14, 18), 0.3),
    100: ((38, 42), 0.5),
    170: ((9, 12), 0.4),
    205: ((48, 55), 0.6),
}

assert 205 in EVENT_INDEX_TO_PULSE_TRANSITION_DATA.keys()


SPLITTED_PARTS_PATH = "ot2/analysis/data/splitted_parts.pickle"
