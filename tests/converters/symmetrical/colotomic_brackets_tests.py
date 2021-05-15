import unittest  # type: ignore

from mutwo.events import basic
from mutwo.events import music
from mutwo.converters.frontends import abjad as mutwo_abjad

from ot2.events import time_brackets
from ot2.converters import symmetrical


class ColotomicBracketToTimeBracketConverterTest(unittest.TestCase):
    def test_get_absolute_time_of_nested_element(self):
        sequential_event = basic.SequentialEvent(
            [
                basic.SimpleEvent(5),
                basic.SequentialEvent([basic.SimpleEvent(4), basic.SimpleEvent(4)]),
                basic.SequentialEvent(
                    [
                        basic.SimpleEvent(3),
                        basic.SequentialEvent([basic.SimpleEvent(2)]),
                    ]
                ),
            ]
        )
        self.assertEqual(
            symmetrical.colotomic_brackets.ColotomicBracketToTimeBracketConverter._get_absolute_time_of_nested_element(
                (1, 1), sequential_event
            ),
            9,
        )
        self.assertEqual(
            symmetrical.colotomic_brackets.ColotomicBracketToTimeBracketConverter._get_absolute_time_of_nested_element(
                (2, 1, 0), sequential_event
            ),
            16,
        )


if __name__ == "__main__":
    unittest.main()
