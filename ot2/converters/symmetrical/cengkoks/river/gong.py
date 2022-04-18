from mutwo import converters
from mutwo import events

from . import structure


class RestructuredPhrasePartsToGongConverter(converters.abc.Converter):
    gong_register = -2
    dynamic = "p"

    def convert(
        self,
        restructured_phrase_parts: tuple[structure.RestructuredPhrasePart, ...],
    ) -> events.basic.SequentialEvent:
        gongs = events.basic.SequentialEvent([])
        for restructured_phrase_part in restructured_phrase_parts:
            if restructured_phrase_part.is_start_of_phrase:
                gong = events.music.NoteLike(
                    restructured_phrase_part.root.register(
                        self.gong_register, mutate=False
                    ),
                    restructured_phrase_part.duration,
                    self.dynamic,
                )
                gongs.append(gong)
            else:
                rest = events.music.NoteLike(
                    [], duration=restructured_phrase_part.duration, volume=self.dynamic
                )
                gongs.append(rest)

        return gongs
