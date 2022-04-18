from mutwo.events import basic
from mutwo.generators import toussaint

import functools
import itertools
import operator

from mu.utils import tools


def __make_timeline(name, nested_structure):
    def make_getter_method(name, depth, attribute_names):
        if depth == 0:

            def getter(self) -> tuple:
                return self._TimeLine__iterable

        else:

            def getter(self) -> tuple:
                iterable = self._TimeLine__iterable
                current_attribute = attribute_names[depth]
                iterable = tuple(getattr(item, current_attribute) for item in iterable)
                iterable = functools.reduce(operator.add, iterable)
                return tuple(iterable)

        return getter

    def make_setter_method(name, depth, attribute_names):
        if depth == 0:

            def setter(self, idx, item: "TimeLine") -> None:
                self._TimeLine__iterable[idx] = item

        else:

            def setter(self, idx, item: "TimeLine") -> None:
                def identify_position_and_new_idx(iterable: tuple, att: str, idx: int):
                    length_per_sub = tuple(
                        getattr(sub, "{0}_amount".format(att)) for sub in iterable
                    )
                    accumulated = tuple(itertools.accumulate((0,) + length_per_sub))
                    for item_idx, item in enumerate(accumulated):
                        if item > idx:
                            number = item_idx - 1
                            new_idx = idx - accumulated[number]
                            break

                    return number, new_idx, iterable[number]

                def identify_vector(iterable: tuple, idx: int) -> tuple:
                    att = attribute_names[depth]
                    current_idx = int(idx)
                    current_iterable = tuple(iterable)
                    vector = []
                    for n in range(depth):
                        data = identify_position_and_new_idx(
                            current_iterable, att, current_idx
                        )
                        vector.append(data[0])
                        current_idx = data[1]
                        current_iterable = data[2]
                    vector.append(current_idx)
                    return tuple(vector)

                def set_vec_element(ls, vec: tuple, item: "TimeLine", current_depth=0):
                    if current_depth == depth:
                        ls[vec[-1]] = item
                    else:
                        for idx, ls_item in enumerate(ls):
                            if idx == vec[current_depth]:
                                ls[idx] = set_vec_element(
                                    ls_item, vec, item, current_depth + 1
                                )
                    return ls

                iterable = self._TimeLine__iterable
                vector = identify_vector(iterable, idx)
                self._TimeLine__iterable = tuple(
                    set_vec_element(list(iterable), vector, item)
                )

        return setter

    def make_size_per_attribute_property(name):
        def getter(self) -> tuple:
            return tuple(item.size for item in getattr(self, name))

        return getter

    def make_amount_per_attribute_property(name):
        def getter(self) -> tuple:
            return len(getattr(self, name))

        return getter

    def make_size_property(highest_attribute):
        def getter(self) -> int:
            return sum(getattr(self, "{0}_size".format(highest_attribute)))

        return getter

    class TimeLine(object):
        def __init__(self, *item):
            self.__iterable = tuple(item)

        def __getitem__(self, idx):
            return self.__iterable[idx]

        def __setitem__(self, idx, obj):
            self.__iterable = tuple(
                item if ix != idx else obj for ix, item in enumerate(self.__iterable)
            )

        def __iter__(self) -> iter:
            return iter(self.__iterable)

        def __repr__(self) -> str:
            return str(self.__iterable)

        def __len__(self) -> int:
            return len(self.__iterable)

        def copy(self) -> "TimeLine":
            return type(self)(*tuple(item.copy() for item in self.__iterable))

        def reverse(self) -> "TimeLine":
            return type(self)(*tuple(reversed(self.__iterable)))

        def add(self, item) -> "TimeLine":
            return type(self)(self.__iterable + (item,))

    attribute_names = tuple(c.__name__.lower() for c in nested_structure)
    for depth, attribute in enumerate(attribute_names):
        getter_method = make_getter_method(attribute, depth, attribute_names)
        setter_method = make_setter_method(attribute, depth, attribute_names)
        size_method = make_size_per_attribute_property(attribute)
        amount_method = make_amount_per_attribute_property(attribute)
        setattr(TimeLine, attribute, property(getter_method))
        setattr(TimeLine, "set_nth_{0}".format(attribute), setter_method)
        setattr(TimeLine, "{0}_size".format(attribute), property(size_method))
        setattr(TimeLine, "{0}_amount".format(attribute), property(amount_method))

    TimeLine.__name__ = name
    TimeLine.__hierarchy = attribute_names
    TimeLine.nested_structure = property(lambda self: self.__hierarchy)
    setattr(TimeLine, "size", property(make_size_property(attribute_names[0])))
    return TimeLine


class Unit(object):
    def __init__(self, size: int) -> None:
        self.__size = size

    def __repr__(self) -> str:
        return "U{0}".format(self.size)

    def copy(self) -> "Unit":
        return type(self)(int(self.size))

    @property
    def size(self) -> int:
        return self.__size


class DividedUnit(Unit):
    """Class for Units that are divided in
    middle kecapi pitches and high kecapi pitches
    """

    def __init__(self, divisions: tuple) -> None:
        Unit.__init__(self, sum(divisions))
        self.__divisions = divisions

    def copy(self) -> "DividedUnit":
        return type(self)(tuple(self.__divisions))

    @property
    def divisions(self) -> tuple:
        return self.__divisions

    @property
    def amount_divisions(self) -> int:
        return len(self.divisions)

    def __repr__(self) -> str:
        return "DU{0}".format(self.size)


class SingleDividedUnit(DividedUnit):
    def __init__(self, size: int, division_size: int) -> None:
        assert size % division_size == 0
        self.__division_size = division_size
        DividedUnit.__init__(self, (division_size,) * (size // division_size))

    def copy(self) -> "SingleDividedUnit":
        return type(self)(int(self.size), int(self.division_size))

    @property
    def division_size(self) -> int:
        return self.__division_size

    def __repr__(self) -> str:
        return "SU{0}({1} * {2})".format(
            self.size, self.amount_divisions, self.division_size
        )


Compound = __make_timeline("Compound", (Unit,))
Metre = __make_timeline("Metre", (Compound, Unit))
TimeFlow = __make_timeline("TimeFlow", (Metre, Compound, Unit))


def define_metre_by_structure(structure: tuple, division=None) -> Metre:
    m = []
    for com in structure:
        c = []
        for size in com:
            if division:
                u = SingleDividedUnit(size * division, division)
            else:
                u = Unit(size)
            c.append(u)
        m.append(Compound(*c))
    return Metre(*m)


class MetreMaker(object):
    """Input expect tuples with two elements per tuple.

    First element has to be an iterable thats infinitly callable.
    The second element is of type bool.
    It declares if the iterable shall repeat the same element
    for multiple
    """

    def __init__(self, *iterable_shall_repeat_pair):
        self.__data = iterable_shall_repeat_pair
        self.__length_data = len(iterable_shall_repeat_pair)

    def make_n_of_m(self, m: int, n: int) -> tuple:
        if self.__data[m][1]:
            return tuple((next(self.__data[m][0]),) * n)
        else:
            return tuple(next(self.__data[m][0]) for i in range(n))

    def _test_if_big_enough(self, needed):
        try:
            assert self.__length_data >= needed
        except AssertionError:
            msg = "Not enough information to make units. "
            msg += "Only {0} iterables has been added, but ".format(self.__length_data)
            msg += " {0} iterables are necessary.".format(needed)

    def make_n_units(self, n: int) -> tuple:
        self._test_if_big_enough(2)
        kecapi0_sizes = self.make_n_of_m(1, n)
        kecapi1_sizes = tuple(self.make_n_of_m(0, k0size) for k0size in kecapi0_sizes)
        units = []
        for k0size, k1size in zip(kecapi0_sizes, kecapi1_sizes):
            if len(set(k1size)) == 1:
                un = SingleDividedUnit(k0size * k1size[0], k1size[0])
            else:
                un = DividedUnit(k1size)
            units.append(un)
        return tuple(units)

    def make_n_compounds(self, n: int) -> tuple:
        self._test_if_big_enough(3)
        return tuple(
            Compound(*self.make_n_units(csize)) for csize in self.make_n_of_m(2, n)
        )

    def make_n_metres(self, n: int) -> tuple:
        self._test_if_big_enough(4)
        return tuple(
            Metre(*self.make_n_compounds(msize)) for msize in self.make_n_of_m(3, n)
        )


class LoopMaker(MetreMaker):
    """Automatically converts the incoming tuples to endless cycles"""

    def __init__(self, *tuple_shall_repeat_pair):
        iterable_shall_repeat_pairs = tuple(
            (itertools.cycle(pair[0]), pair[1]) for pair in tuple_shall_repeat_pair
        )
        MetreMaker.__init__(self, *iterable_shall_repeat_pairs)


class SpecialLoopMaker(LoopMaker):
    def __init__(
        self,
        amount_compounds_loop: tuple,
        amount_units_loop: tuple,
        unitsize_loop: tuple,
        unit_division_size: int,
    ):
        LoopMaker.__init__(
            self,
            ((unit_division_size,), True),
            (unitsize_loop, False),
            (amount_units_loop, False),
            (amount_compounds_loop, False),
        )
        self.__amount_compounds_loop = amount_compounds_loop
        self.__sum_amount_compounds_loop = sum(amount_compounds_loop)
        self.__amount_units_loop = amount_units_loop
        self.__len_units_loop = len(amount_units_loop)
        self.__sum_amount_units_loop = sum(amount_units_loop)
        self.__unitsize_loop = unitsize_loop
        self.__len_unitsize_loop = len(unitsize_loop)

    @property
    def size_until_loop_starts_again(self) -> int:
        lcm0 = tools.lcm(self.__sum_amount_compounds_loop, self.__len_units_loop)
        lcm1 = tools.lcm(self.__sum_amount_units_loop, self.__len_unitsize_loop)
        rep_compounds = lcm0 // self.__sum_amount_compounds_loop
        rep_units_for_compounds = lcm0 // self.__len_units_loop
        rep_units = lcm1 // self.__sum_amount_units_loop

        lcm2 = tools.lcm(rep_units, rep_units_for_compounds)
        solution = (lcm2 // rep_units_for_compounds) * rep_compounds
        solution *= len(self.__amount_compounds_loop)
        return solution

    def make_metres_until_loop_starts_again(self) -> TimeFlow:
        return TimeFlow(*self.make_n_metres(self.size_until_loop_starts_again))



class ConstantMetreMaker(object):
    def __init__(
        self,
        beats_per_part: int,
        units_per_part: int,
        compounds_per_part: int,
        division_size: int,
    ):
        self.__available_solutions = ConstantMetreMaker.find_solutions(
            beats_per_part, units_per_part, compounds_per_part, division_size
        )

    @staticmethod
    def find_solutions(
        beats_per_part: int,
        units_per_part: int,
        compounds_per_part: int,
        division_size: int,
    ) -> tuple:
        possible_cpps = tuple(
            toussaint.euclidean(compounds_per_part, n)
            for n in range(1, compounds_per_part + 1)
            if units_per_part % n == 0
        )
        solutions = []
        for ccp in possible_cpps:
            length_ccp = len(ccp)
            tests_if_addable = (
                units_per_part % length_ccp == 0,
                beats_per_part % length_ccp == 0,
            )

            units_per_metre = units_per_part // length_ccp
            beats_per_metre = beats_per_part // length_ccp

            if all(tests_if_addable):

                is_still_addable = True
                mets = []
                for item in ccp:
                    unit_divisions = toussaint.euclidean(units_per_metre, item)
                    item_tests = (beats_per_metre % item == 0, all(unit_divisions))

                    if all(item_tests):
                        available_unit_sizes_per_compound = beats_per_metre // item
                        comps = []
                        for amount_units in unit_divisions:
                            u_sizes = toussaint.euclidean(
                                available_unit_sizes_per_compound, amount_units
                            )
                            if all(u_sizes):
                                comps.append(
                                    basic.SequentialEvent(
                                        [
                                            basic.SequentialEvent(
                                                [
                                                    basic.SimpleEvent(
                                                        division_size
                                                    )
                                                    for _ in range(s)
                                                ]
                                            )
                                            for s in u_sizes
                                        ]
                                    )
                                )
                            else:
                                is_still_addable = False

                        mets.append(basic.SequentialEvent(comps))

                    else:
                        is_still_addable = False

                if is_still_addable:
                    solutions.append(basic.SequentialEvent(mets))

        return tuple(solutions)

    @property
    def solutions(self) -> tuple:
        return self.__available_solutions
