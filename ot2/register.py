"""Script for building and registering time brackets at the global TimeBracketContainer

Public interaction via "main" method.
"""

import progressbar

from mutwo import parameters
from mutwo import utilities

from ot2 import constants
from ot2 import converters
from ot2 import noise_constants
from ot2 import manual
from ot2 import stochastic
from ot2 import postprocess
from ot2 import third_way


def _sort_cengkok_time_bracket(cengkok_time_bracket_to_sort):
    to_sort = (
        constants.instruments.ID_SUS0,
        constants.instruments.ID_SUS1,
        constants.instruments.ID_SUS2,
        constants.instruments.ID_KEYBOARD,
        constants.instruments.ID_SUS_TO_ID_SINE[constants.instruments.ID_SUS0],
        constants.instruments.ID_SUS_TO_ID_SINE[constants.instruments.ID_SUS1],
        constants.instruments.ID_SUS_TO_ID_SINE[constants.instruments.ID_SUS2],
    )
    to_sort += constants.instruments.PILLOW_IDS
    sorted_cengkok_time_bracket = cengkok_time_bracket_to_sort.copy()
    sorted_cengkok_time_bracket[:] = sorted(
        sorted_cengkok_time_bracket,
        key=lambda tagged_simultaneous_event: to_sort.index(
            tagged_simultaneous_event.tag
        )
        if tagged_simultaneous_event.tag in to_sort
        else 100,
    )
    return sorted_cengkok_time_bracket


@utilities.decorators.compute_lazy(
    f"ot2/constants/.cengkokBrackets{constants.instruments.ID_KEYBOARD}.pickle",
    force_to_compute=constants.compute.COMPUTE_CENGKOK,
)
def _calculate_cengkok_brackets():
    cengkok_time_brackets = []
    absolute_time = 0
    print("CALCULATE CENGKOK BRACKETS...")
    with progressbar.ProgressBar(max_value=(len(constants.structure.STRUCTURE))) as bar:
        for nth_part, part in enumerate(constants.structure.STRUCTURE):
            absolute_time += part[0].duration
            cengkok_phrase = part[1]
            start_time_of_cengkok = float(absolute_time)
            if nth_part == 0:
                converter = converters.symmetrical.cengkoks.SimplePhraseToTimeBracketsConverter(
                    start_time_of_cengkok,
                    start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                    phrase_to_connection_pitches_melody_converter=converters.symmetrical.cengkoks.PhraseToConnectionPitchesMelodyConverter(
                        instrument_id=constants.instruments.ID_SUS1
                    ),
                )
            elif nth_part == 1:
                converter = converters.symmetrical.cengkoks.SimplePhraseWithSimpleContrapunctusToTimeBracketsConverter(
                    start_time_of_cengkok,
                    start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                    phrase_to_connection_pitches_melody_converter=converters.symmetrical.cengkoks.PhraseToConnectionPitchesMelodyConverter(
                        instrument_id=constants.instruments.ID_SUS2
                    ),
                    phrase_to_contapunctus_simpliccisimus_converter=converters.symmetrical.cengkoks.PhraseToContapunctusSimpliccisimusConverter(
                        instrument_id=constants.instruments.ID_SUS0
                    ),
                )
            elif nth_part == 2:
                # converter = converters.symmetrical.cengkoks.SimplePhraseToTimeBracketsConverter(
                #     start_time_of_cengkok,
                #     start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                #     phrase_to_connection_pitches_melody_converter=None,
                #     phrase_to_keyboard_octaves_converter=converters.symmetrical.cengkoks.PhraseToKeyboardOctavesConverter(
                #         modulation_interval_right_hand=parameters.pitches.JustIntonationPitch(
                #             "4/3"
                #         ),
                #         modulation_interval_left_hand="1/1",
                #     ),
                # )
                converter = None
            elif nth_part == 3:
                # converter = converters.symmetrical.cengkoks.MixedPhraseToTimeBracketsConverter0(
                # converter = converters.symmetrical.cengkoks.SimplePhraseToTimeBracketsConverter(
                # converter = converters.symmetrical.cengkoks.SimplePhraseWithSimpleContrapunctusToTimeBracketsConverter(
                #     start_time_of_cengkok,
                #     start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                #     # phrase_to_connection_pitches_melody_converter=converters.symmetrical.cengkoks.PhraseToConnectionPitchesMelodyConverter(
                #     #     instrument_id=constants.instruments.ID_SUS0
                #     # ),
                #     phrase_to_keyboard_octaves_converter=converters.symmetrical.cengkoks.PhraseToRootMelodyConverter(
                #         instrument_id=constants.instruments.ID_SUS1
                #     ),
                #     phrase_to_contapunctus_simpliccisimus_converter=converters.symmetrical.cengkoks.PhraseToContapunctusSimpliccisimusConverter(
                #         instrument_id=constants.instruments.ID_SUS2,
                #         remove_repeating_pitches=True,
                #         start_max_distance=750,
                #     ),
                # )
                converter = None
            elif nth_part == 4:
                # converter = converters.symmetrical.cengkoks.SimplePhraseToTimeBracketsConverter(
                #     start_time_of_cengkok,
                #     start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                #     phrase_to_connection_pitches_melody_converter=converters.symmetrical.cengkoks.PhraseToConnectionPitchesMelodyConverter(
                #         instrument_id=constants.instruments.ID_SUS1, dynamic="pp"
                #     ),
                #     phrase_to_keyboard_octaves_converter=converters.symmetrical.cengkoks.PhraseToKeyboardOctavesConverter(
                #         modulation_interval_right_hand=parameters.pitches.JustIntonationPitch(
                #             "4/1"
                #         ),
                #         modulation_interval_left_hand=parameters.pitches.JustIntonationPitch(
                #             "2/1"
                #         ),
                #         dynamic="ppp",
                #     ),
                # )
                converter = None
            # 5 is normal and not changed
            elif nth_part == 5:
                converter = (
                    converters.symmetrical.cengkoks.SimplePhraseToTimeBracketsConverter(
                        start_time_of_cengkok,
                        start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                        phrase_to_gong_converter=None,
                    )
                )
            elif nth_part == 6:
                converter = None
            elif nth_part == 7:
                converter = None
            elif nth_part == 8:
                converter = (
                    converters.symmetrical.cengkoks.RiverPhraseToTimeBracketsConverter(
                        start_time_of_cengkok,
                        start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                    )
                )
            elif nth_part == 9:
                converter = None
            elif nth_part == 10:
                converter = None
            elif nth_part == 11:
                converter = (
                    converters.symmetrical.cengkoks.RiverPhraseToTimeBracketsConverter(
                        start_time_of_cengkok,
                        start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                    )
                )
            elif nth_part == 12:
                converter = (
                    converters.symmetrical.cengkoks.RiverPhraseToTimeBracketsConverter(
                        start_time_of_cengkok,
                        start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                        percentage_of_single_populated_bars=0.3,
                    )
                )
            else:
                converter = (
                    converters.symmetrical.cengkoks.SimplePhraseToTimeBracketsConverter(
                        start_time_of_cengkok,
                        start_time_of_cengkok + cengkok_phrase.duration_in_seconds,
                    )
                )
            if converter:
                time_brackets = converter.convert(cengkok_phrase)
                if nth_part == 5:
                    for time_bracket in time_brackets:
                        time_bracket.engine_distribution_strategy = converters.symmetrical.keyboard.ComplexEngineDistributionStrategy(
                            converters.symmetrical.keyboard.ByPitchDivisionStrategy(
                                parameters.pitches.JustIntonationPitch("4/9")
                                - parameters.pitches.JustIntonationPitch("5/4")
                                # parameters.pitches.JustIntonationPitch("5/8")
                            ),
                            (
                                converters.symmetrical.keyboard.SimpleEngineDistributionPartStrategy(
                                    3
                                ),
                                converters.symmetrical.keyboard.SimpleEngineDistributionPartStrategy(
                                    1
                                ),
                            ),
                        )
            else:
                time_brackets = tuple([])
            sorted_time_brackets = []
            for time_bracket in time_brackets:
                sorted_time_brackets.append(_sort_cengkok_time_bracket(time_bracket))
            cengkok_time_brackets.append(tuple(sorted_time_brackets))
            absolute_time += cengkok_phrase.duration_in_seconds
            bar.update(nth_part + 1)
    return cengkok_time_brackets


@utilities.decorators.compute_lazy(
    f"ot2/constants/.{constants.instruments.ID_DRONE_SYNTH}-brackets.pickle",
    force_to_compute=constants.compute.COMPUTE_DRONE,
)
def _calculate_csound_drone_brackets():
    time_brackets = converters.symmetrical.drones.FamilyOfPitchCurvesToDroneBracketsConverter().convert(
        constants.families_pitch.FAMILY_PITCH
    )
    return time_brackets


@utilities.decorators.compute_lazy(
    f"ot2/constants/.{constants.instruments.ID_DRONE_SYNTH}-midi-brackets.pickle",
    force_to_compute=constants.compute.COMPUTE_DRONE,
)
def _calculate_midi_drone_brackets():
    time_brackets = converters.symmetrical.drones.FourFofBasedFamiliesOfPitchCurvesToDroneBracketsConverter().convert(
        constants.families_pitch.FAMILIES_PITCH
    )
    return time_brackets


def _register_cengkok_brackets():
    time_brackets_per_cengkok = _calculate_cengkok_brackets()
    for nth_time_brackets, time_brackets in enumerate(time_brackets_per_cengkok):
        time_brackets = postprocess.post_process_cengkok_time_brackets(
            time_brackets, nth_time_brackets
        )
        for time_bracket in time_brackets:
            constants.time_brackets_container.TIME_BRACKETS.register(
                time_bracket, False
            )


def _register_manual_brackets():
    time_brackets = manual.main()
    for instrument_ids, time_bracket in time_brackets:
        try:
            constants.time_brackets_container.TIME_BRACKETS.register(
                time_bracket, tags_to_analyse=instrument_ids
            )
        except utilities.exceptions.OverlappingTimeBracketsError:
            print(
                f"COULD'T REGISTER MANUAL TIME BRACKET WITH INSTRUMENTS: {instrument_ids}"
            )


def _register_third_way_brackets():
    collected_time_brackets = third_way.main()
    for instrument_ids, time_bracket in collected_time_brackets:
        try:
            constants.time_brackets_container.TIME_BRACKETS.register(
                time_bracket, tags_to_analyse=instrument_ids
            )
        except utilities.exceptions.OverlappingTimeBracketsError:
            pass


def _register_stochastic_brackets():
    collected_time_brackets = stochastic.main()
    for instrument_id, time_bracket in collected_time_brackets:
        try:
            constants.time_brackets_container.TIME_BRACKETS.register(
                time_bracket, tags_to_analyse=(instrument_id,)
            )
        except utilities.exceptions.OverlappingTimeBracketsError:
            pass


def _register_synthesized_csound_drone_brackets():
    time_brackets = _calculate_csound_drone_brackets()
    for time_bracket in time_brackets:
        constants.time_brackets_container.TIME_BRACKETS.register(
            time_bracket, tags_to_analyse=(constants.instruments.ID_DRONE_SYNTH,)
        )


def _register_synthesized_midi_drone_brackets():
    time_brackets = _calculate_midi_drone_brackets()
    for time_bracket in time_brackets:
        constants.time_brackets_container.TIME_BRACKETS.register(
            time_bracket, tags_to_analyse=(constants.instruments.ID_DRONE_SYNTH,)
        )


def _register_synthesized_drone_brackets():
    # _register_synthesized_csound_drone_brackets()
    _register_synthesized_midi_drone_brackets()


def _register_noise_brackets():
    for time_bracket in noise_constants.NOISE_TIME_BRACKETS:
        constants.time_brackets_container.TIME_BRACKETS.register(
            time_bracket, tags_to_analyse=(constants.instruments.ID_NOISE,)
        )


def main():
    _register_cengkok_brackets()
    _register_manual_brackets()
    _register_third_way_brackets()
    _register_stochastic_brackets()
    _register_synthesized_drone_brackets()

    constants.time_brackets_container.TIME_BRACKETS = (
        postprocess.post_process_time_brackets_container(
            constants.time_brackets_container.TIME_BRACKETS
        )
    )

    _register_noise_brackets()

    constants.time_brackets_container.TIME_BRACKETS = (
        postprocess.post_process_time_brackets_container_2(
            constants.time_brackets_container.TIME_BRACKETS
        )
    )
