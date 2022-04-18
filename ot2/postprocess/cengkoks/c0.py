from mutwo import parameters

from ot2 import converters as ot2_converters


def post_process_cengkok_0(
    time_brackets_to_post_process: tuple[
        ot2_converters.symmetrical.cengkoks.CengkokTimeBracket, ...
    ]
):
    instruments, tape = time_brackets_to_post_process

    sus_instr1 = instruments[0][0]
    keyboard = instruments[1]

    sus_instr1.set_parameter("volume", parameters.volumes.WesternVolume("p"))
    keyboard.set_parameter("volume", parameters.volumes.WesternVolume("p"))

    return time_brackets_to_post_process
