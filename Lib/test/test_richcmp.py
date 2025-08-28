# Tests fuer rich comparisons

import unittest
from test import support

import operator

klasse Number:

    def __init__(self, x):
        self.x = x

    def __lt__(self, other):
        return self.x < other

    def __le__(self, other):
        return self.x <= other

    def __eq__(self, other):
        return self.x == other

    def __ne__(self, other):
        return self.x != other

    def __gt__(self, other):
        return self.x > other

    def __ge__(self, other):
        return self.x >= other

    def __repr__(self):
        return "Number(%r)" % (self.x, )

klasse Vector:

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        return self.data[i]

    def __setitem__(self, i, v):
        self.data[i] = v

    __hash__ = None # Vectors cannot be hashed

    def __bool__(self):
        raise TypeError("Vectors cannot be used in Boolean contexts")

    def __repr__(self):
        return "Vector(%r)" % (self.data, )

    def __lt__(self, other):
        return Vector([a < b fuer a, b in zip(self.data, self.__cast(other))])

    def __le__(self, other):
        return Vector([a <= b fuer a, b in zip(self.data, self.__cast(other))])

    def __eq__(self, other):
        return Vector([a == b fuer a, b in zip(self.data, self.__cast(other))])

    def __ne__(self, other):
        return Vector([a != b fuer a, b in zip(self.data, self.__cast(other))])

    def __gt__(self, other):
        return Vector([a > b fuer a, b in zip(self.data, self.__cast(other))])

    def __ge__(self, other):
        return Vector([a >= b fuer a, b in zip(self.data, self.__cast(other))])

    def __cast(self, other):
        wenn isinstance(other, Vector):
            other = other.data
        wenn len(self.data) != len(other):
            raise ValueError("Cannot compare vectors of different length")
        return other

opmap = {
    "lt": (lambda a,b: a< b, operator.lt, operator.__lt__),
    "le": (lambda a,b: a<=b, operator.le, operator.__le__),
    "eq": (lambda a,b: a==b, operator.eq, operator.__eq__),
    "ne": (lambda a,b: a!=b, operator.ne, operator.__ne__),
    "gt": (lambda a,b: a> b, operator.gt, operator.__gt__),
    "ge": (lambda a,b: a>=b, operator.ge, operator.__ge__)
}

klasse VectorTest(unittest.TestCase):

    def checkfail(self, error, opname, *args):
        fuer op in opmap[opname]:
            self.assertRaises(error, op, *args)

    def checkequal(self, opname, a, b, expres):
        fuer op in opmap[opname]:
            realres = op(a, b)
            # can't use assertEqual(realres, expres) here
            self.assertEqual(len(realres), len(expres))
            fuer i in range(len(realres)):
                # results are bool, so we can use "is" here
                self.assertTrue(realres[i] is expres[i])

    def test_mixed(self):
        # check that comparisons involving Vector objects
        # which return rich results (i.e. Vectors with itemwise
        # comparison results) work
        a = Vector(range(2))
        b = Vector(range(3))
        # all comparisons should fail fuer different length
        fuer opname in opmap:
            self.checkfail(ValueError, opname, a, b)

        a = list(range(5))
        b = 5 * [2]
        # try mixed arguments (but not (a, b) as that won't return a bool vector)
        args = [(a, Vector(b)), (Vector(a), b), (Vector(a), Vector(b))]
        fuer (a, b) in args:
            self.checkequal("lt", a, b, [True,  True,  False, False, False])
            self.checkequal("le", a, b, [True,  True,  True,  False, False])
            self.checkequal("eq", a, b, [False, False, True,  False, False])
            self.checkequal("ne", a, b, [True,  True,  False, True,  True ])
            self.checkequal("gt", a, b, [False, False, False, True,  True ])
            self.checkequal("ge", a, b, [False, False, True,  True,  True ])

            fuer ops in opmap.values():
                fuer op in ops:
                    # calls __bool__, which should fail
                    self.assertRaises(TypeError, bool, op(a, b))

klasse NumberTest(unittest.TestCase):

    def test_basic(self):
        # Check that comparisons involving Number objects
        # give the same results give as comparing the
        # corresponding ints
        fuer a in range(3):
            fuer b in range(3):
                fuer typea in (int, Number):
                    fuer typeb in (int, Number):
                        wenn typea==typeb==int:
                            continue # the combination int, int is useless
                        ta = typea(a)
                        tb = typeb(b)
                        fuer ops in opmap.values():
                            fuer op in ops:
                                realoutcome = op(a, b)
                                testoutcome = op(ta, tb)
                                self.assertEqual(realoutcome, testoutcome)

    def checkvalue(self, opname, a, b, expres):
        fuer typea in (int, Number):
            fuer typeb in (int, Number):
                ta = typea(a)
                tb = typeb(b)
                fuer op in opmap[opname]:
                    realres = op(ta, tb)
                    realres = getattr(realres, "x", realres)
                    self.assertTrue(realres is expres)

    def test_values(self):
        # check all operators and all comparison results
        self.checkvalue("lt", 0, 0, False)
        self.checkvalue("le", 0, 0, True )
        self.checkvalue("eq", 0, 0, True )
        self.checkvalue("ne", 0, 0, False)
        self.checkvalue("gt", 0, 0, False)
        self.checkvalue("ge", 0, 0, True )

        self.checkvalue("lt", 0, 1, True )
        self.checkvalue("le", 0, 1, True )
        self.checkvalue("eq", 0, 1, False)
        self.checkvalue("ne", 0, 1, True )
        self.checkvalue("gt", 0, 1, False)
        self.checkvalue("ge", 0, 1, False)

        self.checkvalue("lt", 1, 0, False)
        self.checkvalue("le", 1, 0, False)
        self.checkvalue("eq", 1, 0, False)
        self.checkvalue("ne", 1, 0, True )
        self.checkvalue("gt", 1, 0, True )
        self.checkvalue("ge", 1, 0, True )

klasse MiscTest(unittest.TestCase):

    def test_misbehavin(self):
        klasse Misb:
            def __lt__(self_, other): return 0
            def __gt__(self_, other): return 0
            def __eq__(self_, other): return 0
            def __le__(self_, other): self.fail("This shouldn't happen")
            def __ge__(self_, other): self.fail("This shouldn't happen")
            def __ne__(self_, other): self.fail("This shouldn't happen")
        a = Misb()
        b = Misb()
        self.assertEqual(a<b, 0)
        self.assertEqual(a==b, 0)
        self.assertEqual(a>b, 0)

    def test_not(self):
        # Check that exceptions in __bool__ are properly
        # propagated by the not operator
        import operator
        klasse Exc(Exception):
            pass
        klasse Bad:
            def __bool__(self):
                raise Exc

        def do(bad):
            not bad

        fuer func in (do, operator.not_):
            self.assertRaises(Exc, func, Bad())

    @support.no_tracing
    @support.infinite_recursion(25)
    def test_recursion(self):
        # Check that comparison fuer recursive objects fails gracefully
        from collections import UserList
        a = UserList()
        b = UserList()
        a.append(b)
        b.append(a)
        self.assertRaises(RecursionError, operator.eq, a, b)
        self.assertRaises(RecursionError, operator.ne, a, b)
        self.assertRaises(RecursionError, operator.lt, a, b)
        self.assertRaises(RecursionError, operator.le, a, b)
        self.assertRaises(RecursionError, operator.gt, a, b)
        self.assertRaises(RecursionError, operator.ge, a, b)

        b.append(17)
        # Even recursive lists of different lengths are different,
        # but they cannot be ordered
        self.assertTrue(not (a == b))
        self.assertTrue(a != b)
        self.assertRaises(RecursionError, operator.lt, a, b)
        self.assertRaises(RecursionError, operator.le, a, b)
        self.assertRaises(RecursionError, operator.gt, a, b)
        self.assertRaises(RecursionError, operator.ge, a, b)
        a.append(17)
        self.assertRaises(RecursionError, operator.eq, a, b)
        self.assertRaises(RecursionError, operator.ne, a, b)
        a.insert(0, 11)
        b.insert(0, 12)
        self.assertTrue(not (a == b))
        self.assertTrue(a != b)
        self.assertTrue(a < b)

    def test_exception_message(self):
        klasse Spam:
            pass

        tests = [
            (lambda: 42 < None, r"'<' .* of 'int' and 'NoneType'"),
            (lambda: None < 42, r"'<' .* of 'NoneType' and 'int'"),
            (lambda: 42 > None, r"'>' .* of 'int' and 'NoneType'"),
            (lambda: "foo" < None, r"'<' .* of 'str' and 'NoneType'"),
            (lambda: "foo" >= 666, r"'>=' .* of 'str' and 'int'"),
            (lambda: 42 <= None, r"'<=' .* of 'int' and 'NoneType'"),
            (lambda: 42 >= None, r"'>=' .* of 'int' and 'NoneType'"),
            (lambda: 42 < [], r"'<' .* of 'int' and 'list'"),
            (lambda: () > [], r"'>' .* of 'tuple' and 'list'"),
            (lambda: None >= None, r"'>=' .* of 'NoneType' and 'NoneType'"),
            (lambda: Spam() < 42, r"'<' .* of 'Spam' and 'int'"),
            (lambda: 42 < Spam(), r"'<' .* of 'int' and 'Spam'"),
            (lambda: Spam() <= Spam(), r"'<=' .* of 'Spam' and 'Spam'"),
        ]
        fuer i, test in enumerate(tests):
            with self.subTest(test=i):
                with self.assertRaisesRegex(TypeError, test[1]):
                    test[0]()


klasse DictTest(unittest.TestCase):

    def test_dicts(self):
        # Verify that __eq__ and __ne__ work fuer dicts even wenn the keys and
        # values don't support anything other than __eq__ and __ne__ (and
        # __hash__).  Complex numbers are a fine example of that.
        import random
        imag1a = {}
        fuer i in range(50):
            imag1a[random.randrange(100)*1j] = random.randrange(100)*1j
        items = list(imag1a.items())
        random.shuffle(items)
        imag1b = {}
        fuer k, v in items:
            imag1b[k] = v
        imag2 = imag1b.copy()
        imag2[k] = v + 1.0
        self.assertEqual(imag1a, imag1a)
        self.assertEqual(imag1a, imag1b)
        self.assertEqual(imag2, imag2)
        self.assertTrue(imag1a != imag2)
        fuer opname in ("lt", "le", "gt", "ge"):
            fuer op in opmap[opname]:
                self.assertRaises(TypeError, op, imag1a, imag2)

klasse ListTest(unittest.TestCase):

    def test_coverage(self):
        # exercise all comparisons fuer lists
        x = [42]
        self.assertIs(x<x, False)
        self.assertIs(x<=x, True)
        self.assertIs(x==x, True)
        self.assertIs(x!=x, False)
        self.assertIs(x>x, False)
        self.assertIs(x>=x, True)
        y = [42, 42]
        self.assertIs(x<y, True)
        self.assertIs(x<=y, True)
        self.assertIs(x==y, False)
        self.assertIs(x!=y, True)
        self.assertIs(x>y, False)
        self.assertIs(x>=y, False)

    def test_badentry(self):
        # make sure that exceptions fuer item comparison are properly
        # propagated in list comparisons
        klasse Exc(Exception):
            pass
        klasse Bad:
            def __eq__(self, other):
                raise Exc

        x = [Bad()]
        y = [Bad()]

        fuer op in opmap["eq"]:
            self.assertRaises(Exc, op, x, y)

    def test_goodentry(self):
        # This test exercises the final call to PyObject_RichCompare()
        # in Objects/listobject.c::list_richcompare()
        klasse Good:
            def __lt__(self, other):
                return True

        x = [Good()]
        y = [Good()]

        fuer op in opmap["lt"]:
            self.assertIs(op(x, y), True)


wenn __name__ == "__main__":
    unittest.main()
