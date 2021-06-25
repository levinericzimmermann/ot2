import functools
import operator
import os
import json
import typing


def _load_bonang_cengkoks() -> typing.Dict[
    int, typing.Dict[int, typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]], ...]]
]:
    basic_path = "ot2/analysis/data/cengkoks/bonang/seleh"
    bonang_cengkoks = {}
    for n_beats, path_suffix in ((8, "8beats"), (16, "16beats")):
        n_beats_data = {}
        path = f"{basic_path}/{path_suffix}"
        for seleh in (1, 2, 3, 5, 6):
            json_path = f"{path}/{seleh}.json"
            with open(json_path, "r") as f:
                cengkok_data = json.load(f)
            n_beats_data.update(
                {
                    seleh: tuple(
                        (cengkok["pitches"], tuple(cengkok["rhythms"]))
                        for cengkok in cengkok_data
                    )
                }
            )
        bonang_cengkoks.update({n_beats: n_beats_data})
    return bonang_cengkoks


def _load_celempung_cengkoks() -> typing.Dict[
    int, typing.Dict[int, typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]], ...]]
]:
    basic_path = "ot2/analysis/data/cengkoks/celempung/seleh/ngracik"
    eight_beats_cengkoks = {}
    for seleh in (1, 2, 3, 5, 6):
        seleh_path = f"{basic_path}/{seleh}"
        cengkoks = []

        for subpath in os.listdir(seleh_path):
            with open(f"{seleh_path}/{subpath}", "r") as f:
                pitches = f.read().replace("\n", " ")
            rhythms = (1, 1, 1, 1, 1, 1, 1, 1)
            cengkoks.append((pitches, rhythms))

        eight_beats_cengkoks.update({seleh: tuple(cengkoks)})

    return {8: eight_beats_cengkoks}


def _concatenate_cengkok_collections(
    *cengkok_collections: typing.Dict[
        int,
        typing.Dict[int, typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]], ...]],
    ]
) -> typing.Dict[
    int, typing.Dict[int, typing.Tuple[typing.Tuple[str, typing.Tuple[int, ...]], ...]]
]:
    cengkoks = {}
    for n_beats in set(
        functools.reduce(
            operator.add,
            (
                tuple(cengkok_collection.keys())
                for cengkok_collection in cengkok_collections
            ),
        )
    ):
        cengkoks_per_seleh = {}
        for seleh in (1, 2, 3, 5, 6):
            cengkoks_for_current_seleh = []
            for cengkok_collection in cengkok_collections:
                if n_beats in cengkok_collection:
                    cengkoks_for_current_seleh.extend(
                        cengkok_collection[n_beats][seleh]
                    )
            cengkoks_per_seleh.update({seleh: tuple(cengkoks_for_current_seleh)})
        cengkoks.update({n_beats: cengkoks_per_seleh})
    return cengkoks


BONANG_CENGKOKS = _load_bonang_cengkoks()
CELEMPUNG_CENGKOKS = _load_celempung_cengkoks()
CENGKOKS = _concatenate_cengkok_collections(BONANG_CENGKOKS, CELEMPUNG_CENGKOKS)
