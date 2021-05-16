class ValueNotAssignedError(Exception):
    def __init__(self):
        super().__init__(
            "TimeBracket values haven't been assigned yet, run"
            " 'assign_concrete_times' method first"
        )
