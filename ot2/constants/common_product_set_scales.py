import itertools

from mutwo.generators import wilson

NUMBERS = (3, 5, 7, 9, 11)
TONALITIES = (True, False)

COMMON_PRODUCT_SET_SCALES = []
for subset_of_number in itertools.combinations(NUMBERS, 4):
    for tonality in TONALITIES:
        COMMON_PRODUCT_SET_SCALES.append(
            wilson.make_common_product_set_scale(
                subset_of_number, 2, tonality, normalize=True
            )
        )

COMMON_PRODUCT_SET_SCALES = tuple(COMMON_PRODUCT_SET_SCALES)
