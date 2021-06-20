import unittest

from ot2.analysis import applied_cantus_firmus
from ot2.analysis import brahms
from ot2.generators import zimmermann


class ImitationTest(unittest.TestCase):
    def test_imitate(self):
        harmony = tuple(applied_cantus_firmus.APPLIED_CANTUS_FIRMUS[3].pitch_or_pitches)
        melodies = (brahms.BRAHMS0, brahms.BRAHMS1)

        for nth_melody, melody in enumerate(melodies):
            zimmermann.events.illustrate_melody(
                f"tests/generators/zimmermann/brahms_imitation{nth_melody}.pdf",
                zimmermann.events.imitate_melody(melody, harmony),
            )


if __name__ == "__main__":
    unittest.main()
