import copy
import random

from mutwo.converters import symmetrical
from mutwo import events
from mutwo import parameters

from ot2.parameters import playing_indicators as ot2_playing_indicators


class ExplicitFermataConverter(
    symmetrical.playing_indicators.PlayingIndicatorConverter
):
    def _apply_playing_indicator(
        self,
        simple_event_to_convert: events.basic.SimpleEvent,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection,
    ) -> events.basic.SequentialEvent[events.basic.SimpleEvent]:
        try:
            explicit_fermata = playing_indicators.explicit_fermata
        except AttributeError:
            explicit_fermata = ot2_playing_indicators.ExplicitFermata()

        simple_event_to_convert = copy.deepcopy(simple_event_to_convert)
        if explicit_fermata.is_active:
            simple_event_to_convert.duration += random.uniform(
                *explicit_fermata.waiting_range
            )

        return events.basic.SequentialEvent([simple_event_to_convert])
