import typing


from mutwo.events import basic
from mutwo.events import music
from mutwo.parameters import tempos


class ColotomicElement(basic.SequentialEvent[music.NoteLike]):
    pass


TempoPoint = typing.Union[float, tempos.TempoPoint]


class ColotomicPattern(basic.SequentialEvent[ColotomicElement]):
    def __init__(
        self,
        colotomic_elements: typing.Sequence[ColotomicElement],
        n_repetitions: int = 3,
        tempo: tempos.TempoPoint = tempos.TempoPoint(60),
    ):
        self.tempo = tempo
        self.n_repetitions = n_repetitions
        super().__init__(colotomic_elements)


class ColotomicBracket(
    basic.SimultaneousEvent[
        basic.SimultaneousEvent[basic.SequentialEvent[music.NoteLike]]
    ]
):
    pass


class TempoBasedColotomicBracket(ColotomicBracket):
    pass
