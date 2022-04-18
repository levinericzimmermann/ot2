import typing

from mutwo import events


class KeyboardTimeBracket(events.time_brackets.TimeBracket):
    _class_specific_side_attributes = (
        events.time_brackets.TimeBracket._class_specific_side_attributes
        + ("distribution_strategy", "engine_distribution_strategy")
    )

    def __init__(
        self,
        *args,
        distribution_strategy: typing.Optional = None,
        engine_distribution_strategy: typing.Optional = None,
        **kwargs,
    ):
        self.distribution_strategy = distribution_strategy
        self.engine_distribution_strategy = engine_distribution_strategy
        super().__init__(*args, **kwargs)
