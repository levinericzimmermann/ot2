import typing

from PyPDF2 import PdfFileMerger

from ot2 import constants as ot2_constants


def _merge_parts(parts: typing.Sequence[str], path: str):
    merger = PdfFileMerger()
    for pdf in parts:
        merger.append(pdf)
    merger.write(path)
    merger.close()


def _get_microtonal_pitches_list_name(instrument_tag: str):
    return "{}/{}_microtonal_pitches.pdf".format(
        ot2_constants.paths.ILLUSTRATIONS_PATH, instrument_tag
    )


def main():
    preamble = (
        f"{ot2_constants.paths.COVER_PATH}/cover.pdf",
        f"{ot2_constants.paths.INTRODUCTIONS_PATH}/introduction.pdf",
        f"{ot2_constants.paths.INTRODUCTIONS_PATH}/HEJI-legend-portrait.pdf",
    )

    instrument_tags_to_render = (
        ot2_constants.instruments.ID_SUS0,
        ot2_constants.instruments.ID_SUS1,
        ot2_constants.instruments.ID_SUS2,
        ot2_constants.instruments.ID_KEYBOARD,
        ot2_constants.instruments.ID_NOISE,
    )

    instruments = tuple(
        f"{ot2_constants.paths.NOTATION_PATH}/oT2_{tag}.pdf"
        for tag in instrument_tags_to_render
    )

    _merge_parts(
        preamble
        + tuple(
            _get_microtonal_pitches_list_name(tag)
            for tag in instrument_tags_to_render[:3]
        )
        + instruments,
        f"{ot2_constants.paths.SCORES_PATH}/ohneTitel2.pdf",
    )

    for instrument_notation_path, tag in zip(instruments, instrument_tags_to_render):
        instrument_score_path = f"{ot2_constants.paths.SCORES_PATH}/oT2_{tag}.pdf"
        instrument_parts = []
        if tag in instrument_tags_to_render[:3]:
            instrument_parts.append(_get_microtonal_pitches_list_name(tag))
            local_preamble = tuple(preamble)
        else:
            local_preamble = tuple(preamble)[:-1]
        instrument_parts.append(instrument_notation_path)

        _merge_parts(
            local_preamble + tuple(instrument_parts),
            instrument_score_path,
        )
