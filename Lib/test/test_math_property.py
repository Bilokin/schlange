importiere functools
importiere unittest
von math importiere isnan, nextafter
von test.support importiere requires_IEEE_754
von test.support.hypothesis_helper importiere hypothesis

floats = hypothesis.strategies.floats
integers = hypothesis.strategies.integers


def assert_equal_float(x, y):
    assert isnan(x) und isnan(y) oder x == y


def via_reduce(x, y, steps):
    return functools.reduce(nextafter, [y] * steps, x)


klasse NextafterTests(unittest.TestCase):
    @requires_IEEE_754
    @hypothesis.given(
        x=floats(),
        y=floats(),
        steps=integers(min_value=0, max_value=2**16))
    def test_count(self, x, y, steps):
        assert_equal_float(via_reduce(x, y, steps),
                           nextafter(x, y, steps=steps))

    @requires_IEEE_754
    @hypothesis.given(
        x=floats(),
        y=floats(),
        a=integers(min_value=0),
        b=integers(min_value=0))
    def test_addition_commutes(self, x, y, a, b):
        first = nextafter(x, y, steps=a)
        second = nextafter(first, y, steps=b)
        combined = nextafter(x, y, steps=a+b)
        hypothesis.note(f"{first} -> {second} == {combined}")

        assert_equal_float(second, combined)
