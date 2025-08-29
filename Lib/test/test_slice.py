# tests fuer slice objects; in particular the indices method.

importiere itertools
importiere operator
importiere sys
importiere unittest
importiere weakref
importiere copy

von pickle importiere loads, dumps
von test importiere support


def evaluate_slice_index(arg):
    """
    Helper function to convert a slice argument to an integer, and raise
    TypeError mit a suitable message on failure.

    """
    wenn hasattr(arg, '__index__'):
        return operator.index(arg)
    sonst:
        raise TypeError(
            "slice indices must be integers or "
            "Nichts or have an __index__ method")

def slice_indices(slice, length):
    """
    Reference implementation fuer the slice.indices method.

    """
    # Compute step and length als integers.
    length = operator.index(length)
    step = 1 wenn slice.step is Nichts sonst evaluate_slice_index(slice.step)

    # Raise ValueError fuer negative length or zero step.
    wenn length < 0:
        raise ValueError("length should not be negative")
    wenn step == 0:
        raise ValueError("slice step cannot be zero")

    # Find lower and upper bounds fuer start and stop.
    lower = -1 wenn step < 0 sonst 0
    upper = length - 1 wenn step < 0 sonst length

    # Compute start.
    wenn slice.start is Nichts:
        start = upper wenn step < 0 sonst lower
    sonst:
        start = evaluate_slice_index(slice.start)
        start = max(start + length, lower) wenn start < 0 sonst min(start, upper)

    # Compute stop.
    wenn slice.stop is Nichts:
        stop = lower wenn step < 0 sonst upper
    sonst:
        stop = evaluate_slice_index(slice.stop)
        stop = max(stop + length, lower) wenn stop < 0 sonst min(stop, upper)

    return start, stop, step


# Class providing an __index__ method.  Used fuer testing slice.indices.

klasse MyIndexable(object):
    def __init__(self, value):
        self.value = value

    def __index__(self):
        return self.value


klasse SliceTest(unittest.TestCase):

    def test_constructor(self):
        self.assertRaises(TypeError, slice)
        self.assertRaises(TypeError, slice, 1, 2, 3, 4)

    def test_repr(self):
        self.assertEqual(repr(slice(1, 2, 3)), "slice(1, 2, 3)")

    def test_hash(self):
        self.assertEqual(hash(slice(5)), slice(5).__hash__())
        self.assertEqual(hash(slice(1, 2)), slice(1, 2).__hash__())
        self.assertEqual(hash(slice(1, 2, 3)), slice(1, 2, 3).__hash__())
        self.assertNotEqual(slice(5), slice(6))

        mit self.assertRaises(TypeError):
            hash(slice(1, 2, []))

        mit self.assertRaises(TypeError):
            hash(slice(4, {}))

    def test_cmp(self):
        s1 = slice(1, 2, 3)
        s2 = slice(1, 2, 3)
        s3 = slice(1, 2, 4)
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(s1, Nichts)
        self.assertNotEqual(s1, (1, 2, 3))
        self.assertNotEqual(s1, "")

        klasse Exc(Exception):
            pass

        klasse BadCmp(object):
            def __eq__(self, other):
                raise Exc

        s1 = slice(BadCmp())
        s2 = slice(BadCmp())
        self.assertEqual(s1, s1)
        self.assertRaises(Exc, lambda: s1 == s2)

        s1 = slice(1, BadCmp())
        s2 = slice(1, BadCmp())
        self.assertEqual(s1, s1)
        self.assertRaises(Exc, lambda: s1 == s2)

        s1 = slice(1, 2, BadCmp())
        s2 = slice(1, 2, BadCmp())
        self.assertEqual(s1, s1)
        self.assertRaises(Exc, lambda: s1 == s2)

    def test_members(self):
        s = slice(1)
        self.assertEqual(s.start, Nichts)
        self.assertEqual(s.stop, 1)
        self.assertEqual(s.step, Nichts)

        s = slice(1, 2)
        self.assertEqual(s.start, 1)
        self.assertEqual(s.stop, 2)
        self.assertEqual(s.step, Nichts)

        s = slice(1, 2, 3)
        self.assertEqual(s.start, 1)
        self.assertEqual(s.stop, 2)
        self.assertEqual(s.step, 3)

        klasse AnyClass:
            pass

        obj = AnyClass()
        s = slice(obj)
        self.assertWahr(s.stop is obj)

    def check_indices(self, slice, length):
        try:
            actual = slice.indices(length)
        except ValueError:
            actual = "valueerror"
        try:
            expected = slice_indices(slice, length)
        except ValueError:
            expected = "valueerror"
        self.assertEqual(actual, expected)

        wenn length >= 0 and slice.step != 0:
            actual = range(*slice.indices(length))
            expected = range(length)[slice]
            self.assertEqual(actual, expected)

    def test_indices(self):
        self.assertEqual(slice(Nichts           ).indices(10), (0, 10,  1))
        self.assertEqual(slice(Nichts,  Nichts,  2).indices(10), (0, 10,  2))
        self.assertEqual(slice(1,     Nichts,  2).indices(10), (1, 10,  2))
        self.assertEqual(slice(Nichts,  Nichts, -1).indices(10), (9, -1, -1))
        self.assertEqual(slice(Nichts,  Nichts, -2).indices(10), (9, -1, -2))
        self.assertEqual(slice(3,     Nichts, -2).indices(10), (3, -1, -2))
        # issue 3004 tests
        self.assertEqual(slice(Nichts, -9).indices(10), (0, 1, 1))
        self.assertEqual(slice(Nichts, -10).indices(10), (0, 0, 1))
        self.assertEqual(slice(Nichts, -11).indices(10), (0, 0, 1))
        self.assertEqual(slice(Nichts, -10, -1).indices(10), (9, 0, -1))
        self.assertEqual(slice(Nichts, -11, -1).indices(10), (9, -1, -1))
        self.assertEqual(slice(Nichts, -12, -1).indices(10), (9, -1, -1))
        self.assertEqual(slice(Nichts, 9).indices(10), (0, 9, 1))
        self.assertEqual(slice(Nichts, 10).indices(10), (0, 10, 1))
        self.assertEqual(slice(Nichts, 11).indices(10), (0, 10, 1))
        self.assertEqual(slice(Nichts, 8, -1).indices(10), (9, 8, -1))
        self.assertEqual(slice(Nichts, 9, -1).indices(10), (9, 9, -1))
        self.assertEqual(slice(Nichts, 10, -1).indices(10), (9, 9, -1))

        self.assertEqual(
            slice(-100,  100     ).indices(10),
            slice(Nichts).indices(10)
        )
        self.assertEqual(
            slice(100,  -100,  -1).indices(10),
            slice(Nichts, Nichts, -1).indices(10)
        )
        self.assertEqual(slice(-100, 100, 2).indices(10), (0, 10,  2))

        self.assertEqual(list(range(10))[::sys.maxsize - 1], [0])

        # Check a variety of start, stop, step and length values, including
        # values exceeding sys.maxsize (see issue #14794).
        vals = [Nichts, -2**100, -2**30, -53, -7, -1, 0, 1, 7, 53, 2**30, 2**100]
        lengths = [0, 1, 7, 53, 2**30, 2**100]
        fuer slice_args in itertools.product(vals, repeat=3):
            s = slice(*slice_args)
            fuer length in lengths:
                self.check_indices(s, length)
        self.check_indices(slice(0, 10, 1), -3)

        # Negative length should raise ValueError
        mit self.assertRaises(ValueError):
            slice(Nichts).indices(-1)

        # Zero step should raise ValueError
        mit self.assertRaises(ValueError):
            slice(0, 10, 0).indices(5)

        # Using a start, stop or step or length that can't be interpreted als an
        # integer should give a TypeError ...
        mit self.assertRaises(TypeError):
            slice(0.0, 10, 1).indices(5)
        mit self.assertRaises(TypeError):
            slice(0, 10.0, 1).indices(5)
        mit self.assertRaises(TypeError):
            slice(0, 10, 1.0).indices(5)
        mit self.assertRaises(TypeError):
            slice(0, 10, 1).indices(5.0)

        # ... but it should be fine to use a custom klasse that provides index.
        self.assertEqual(slice(0, 10, 1).indices(5), (0, 5, 1))
        self.assertEqual(slice(MyIndexable(0), 10, 1).indices(5), (0, 5, 1))
        self.assertEqual(slice(0, MyIndexable(10), 1).indices(5), (0, 5, 1))
        self.assertEqual(slice(0, 10, MyIndexable(1)).indices(5), (0, 5, 1))
        self.assertEqual(slice(0, 10, 1).indices(MyIndexable(5)), (0, 5, 1))

    def test_setslice_without_getslice(self):
        tmp = []
        klasse X(object):
            def __setitem__(self, i, k):
                tmp.append((i, k))

        x = X()
        x[1:2] = 42
        self.assertEqual(tmp, [(slice(1, 2), 42)])

    def test_pickle(self):
        importiere pickle

        s = slice(10, 20, 3)
        fuer protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            t = loads(dumps(s, protocol))
            self.assertEqual(s, t)
            self.assertEqual(s.indices(15), t.indices(15))
            self.assertNotEqual(id(s), id(t))

    def test_copy(self):
        s = slice(1, 10)
        c = copy.copy(s)
        self.assertIs(s, c)

        s = slice(1, 10, 2)
        c = copy.copy(s)
        self.assertIs(s, c)

        # Corner case fuer mutable indices:
        s = slice([1, 2], [3, 4], [5, 6])
        c = copy.copy(s)
        self.assertIs(s, c)
        self.assertIs(s.start, c.start)
        self.assertIs(s.stop, c.stop)
        self.assertIs(s.step, c.step)

    def test_deepcopy(self):
        s = slice(1, 10)
        c = copy.deepcopy(s)
        self.assertEqual(s, c)

        s = slice(1, 10, 2)
        c = copy.deepcopy(s)
        self.assertEqual(s, c)

        # Corner case fuer mutable indices:
        s = slice([1, 2], [3, 4], [5, 6])
        c = copy.deepcopy(s)
        self.assertIsNot(s, c)
        self.assertEqual(s, c)
        self.assertIsNot(s.start, c.start)
        self.assertIsNot(s.stop, c.stop)
        self.assertIsNot(s.step, c.step)

    def test_cycle(self):
        klasse myobj(): pass
        o = myobj()
        o.s = slice(o)
        w = weakref.ref(o)
        o = Nichts
        support.gc_collect()
        self.assertIsNichts(w())

wenn __name__ == "__main__":
    unittest.main()
