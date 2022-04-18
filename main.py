"""Main file for rendering relevant data"""


if __name__ == "__main__":
    from mutwo import converters
    from ot2 import constants as ot2_constants

    converters.symmetrical.time_brackets_constants.DEFAULT_TIME_GRID = (
        ot2_constants.stochastic_calculation.TIME_GRID
    )
    converters.symmetrical.time_brackets_constants.DEFAULT_PRECISION = (
        ot2_constants.stochastic_calculation.PRECISION
    )

    from ot2 import concatenate_score_parts
    from ot2 import illustrate
    from ot2 import register
    from ot2 import render
    from ot2 import tape

    MAKE_CLARINET_VERSION = False

    register.main()
    illustrate.main(MAKE_CLARINET_VERSION)
    render.main(MAKE_CLARINET_VERSION)
    concatenate_score_parts.main()

    # tape.add_resonators()
