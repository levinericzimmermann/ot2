PULSE_DURATION_IN_SECONDS_AT_START = 18
EVENT_INDEX_TO_PULSE_TRANSITION_DATA = {
    # event_index:
    #   ((min_duration_of_pulse, max_duration_of_pulse),
    #    percentage_how_many_steps_shall_rise)
    40: ((6, 8), 0.3),
    60: ((10, 12), 0.5),
    100: ((19, 21), 0.2),
    130: ((3, 4), 0.5),
    160: ((3, 5), 0.7),
    205: ((15, 17), 0.6),
}

assert 205 in EVENT_INDEX_TO_PULSE_TRANSITION_DATA.keys()


SPLITTED_PARTS_PATH = "ot2/analysis/data/splitted_parts.pickle"
