"""Main file for rendering relevant data"""


if __name__ == "__main__":
    from mutwo import parameters

    parameters.volumes_constants.MINIMUM_VELOCITY = 8
    parameters.volumes_constants.MAXIMUM_VELOCITY = 35

    from ot2 import register
    from ot2 import render

    register.main()
    render.main()
