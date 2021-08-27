import typing

from PyPDF2 import PdfFileMerger

from ot2 import constants as ot2_constants


def _merge_parts(parts: typing.Sequence[str], path: str):
    merger = PdfFileMerger()
    for pdf in parts:
        merger.append(pdf)
    merger.write(path)
    merger.close()


def main():
    preamble = (
        f"{ot2_constants.paths.COVER_PATH}/cover.pdf",
        f"{ot2_constants.paths.INTRODUCTIONS_PATH}/introduction.pdf",
    )

    instrument_tags_to_render = (
        ot2_constants.instruments.ID_SUS0,
        ot2_constants.instruments.ID_SUS1,
        ot2_constants.instruments.ID_SUS2,
        ot2_constants.instruments.ID_KEYBOARD,
    )

    instruments = tuple(
        f"{ot2_constants.paths.NOTATION_PATH}/oT2_{tag}.pdf"
        for tag in instrument_tags_to_render
    )

    _merge_parts(
        preamble + instruments, f"{ot2_constants.paths.SCORES_PATH}/ohneTitel2.pdf"
    )

    for instrument_notation_path, tag in zip(instruments, instrument_tags_to_render):
        instrument_score_path = f"{ot2_constants.paths.SCORES_PATH}/oT2_{tag}.pdf"
        _merge_parts(preamble + (instrument_notation_path,), instrument_score_path)
