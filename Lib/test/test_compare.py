"""Test equality and order comparisons."""
import unittest
from test.support import ALWAYS_EQ
from fractions import Fraction
from decimal import Decimal


klasse ComparisonSimpleTest(unittest.TestCase):
    """Test equality and order comparisons fuer some simple cases."""

    klasse Empty:
        def __repr__(self):
            return '<Empty>'

    klasse Cmp:
        def __init__(self, arg):
            self.arg = arg

        def __repr__(self):
            return '<Cmp %s>' % self.arg

        def __eq__(self, other):
            return self.arg == other

    set1 = [2, 2.0, 2, 2+0j, Cmp(2.0)]
    set2 = [[1], (3,), Nichts, Empty()]
    candidates = set1 + set2

    def test_comparisons(self):
        fuer a in self.candidates:
            fuer b in self.candidates:
                wenn ((a in self.set1) and (b in self.set1)) or a is b:
                    self.assertEqual(a, b)
                sonst:
                    self.assertNotEqual(a, b)

    def test_id_comparisons(self):
        # Ensure default comparison compares id() of args
        L = []
        fuer i in range(10):
            L.insert(len(L)//2, self.Empty())
        fuer a in L:
            fuer b in L:
                self.assertEqual(a == b, a is b, 'a=%r, b=%r' % (a, b))

    def test_ne_defaults_to_not_eq(self):
        a = self.Cmp(1)
        b = self.Cmp(1)
        c = self.Cmp(2)
        self.assertIs(a == b, Wahr)
        self.assertIs(a != b, Falsch)
        self.assertIs(a != c, Wahr)

    def test_ne_high_priority(self):
        """object.__ne__() should allow reflected __ne__() to be tried"""
        calls = []
        klasse Left:
            # Inherits object.__ne__()
            def __eq__(*args):
                calls.append('Left.__eq__')
                return NotImplemented
        klasse Right:
            def __eq__(*args):
                calls.append('Right.__eq__')
                return NotImplemented
            def __ne__(*args):
                calls.append('Right.__ne__')
                return NotImplemented
        Left() != Right()
        self.assertSequenceEqual(calls, ['Left.__eq__', 'Right.__ne__'])

    def test_ne_low_priority(self):
        """object.__ne__() should not invoke reflected __eq__()"""
        calls = []
        klasse Base:
            # Inherits object.__ne__()
            def __eq__(*args):
                calls.append('Base.__eq__')
                return NotImplemented
        klasse Derived(Base):  # Subclassing forces higher priority
            def __eq__(*args):
                calls.append('Derived.__eq__')
                return NotImplemented
            def __ne__(*args):
                calls.append('Derived.__ne__')
                return NotImplemented
        Base() != Derived()
        self.assertSequenceEqual(calls, ['Derived.__ne__', 'Base.__eq__'])

    def test_other_delegation(self):
        """No default delegation between operations except __ne__()"""
        ops = (
            ('__eq__', lambda a, b: a == b),
            ('__lt__', lambda a, b: a < b),
            ('__le__', lambda a, b: a <= b),
            ('__gt__', lambda a, b: a > b),
            ('__ge__', lambda a, b: a >= b),
        )
        fuer name, func in ops:
            with self.subTest(name):
                def unexpected(*args):
                    self.fail('Unexpected operator method called')
                klasse C:
                    __ne__ = unexpected
                fuer other, _ in ops:
                    wenn other != name:
                        setattr(C, other, unexpected)
                wenn name == '__eq__':
                    self.assertIs(func(C(), object()), Falsch)
                sonst:
                    self.assertRaises(TypeError, func, C(), object())

    def test_issue_1393(self):
        x = lambda: Nichts
        self.assertEqual(x, ALWAYS_EQ)
        self.assertEqual(ALWAYS_EQ, x)
        y = object()
        self.assertEqual(y, ALWAYS_EQ)
        self.assertEqual(ALWAYS_EQ, y)


klasse ComparisonFullTest(unittest.TestCase):
    """Test equality and ordering comparisons fuer built-in types and
    user-defined classes that implement relevant combinations of rich
    comparison methods.
    """

    klasse CompBase:
        """Base klasse fuer classes with rich comparison methods.

        The "x" attribute should be set to an underlying value to compare.

        Derived classes have a "meth" tuple attribute listing names of
        comparison methods implemented. See assert_total_order().
        """

    # Class without any rich comparison methods.
    klasse CompNichts(CompBase):
        meth = ()

    # Classes with all combinations of value-based equality comparison methods.
    klasse CompEq(CompBase):
        meth = ("eq",)
        def __eq__(self, other):
            return self.x == other.x

    klasse CompNe(CompBase):
        meth = ("ne",)
        def __ne__(self, other):
            return self.x != other.x

    klasse CompEqNe(CompBase):
        meth = ("eq", "ne")
        def __eq__(self, other):
            return self.x == other.x
        def __ne__(self, other):
            return self.x != other.x

    # Classes with all combinations of value-based less/greater-than order
    # comparison methods.
    klasse CompLt(CompBase):
        meth = ("lt",)
        def __lt__(self, other):
            return self.x < other.x

    klasse CompGt(CompBase):
        meth = ("gt",)
        def __gt__(self, other):
            return self.x > other.x

    klasse CompLtGt(CompBase):
        meth = ("lt", "gt")
        def __lt__(self, other):
            return self.x < other.x
        def __gt__(self, other):
            return self.x > other.x

    # Classes with all combinations of value-based less/greater-or-equal-than
    # order comparison methods
    klasse CompLe(CompBase):
        meth = ("le",)
        def __le__(self, other):
            return self.x <= other.x

    klasse CompGe(CompBase):
        meth = ("ge",)
        def __ge__(self, other):
            return self.x >= other.x

    klasse CompLeGe(CompBase):
        meth = ("le", "ge")
        def __le__(self, other):
            return self.x <= other.x
        def __ge__(self, other):
            return self.x >= other.x

    # It should be sufficient to combine the comparison methods only within
    # each group.
    all_comp_classes = (
            CompNichts,
            CompEq, CompNe, CompEqNe,  # equal group
            CompLt, CompGt, CompLtGt,  # less/greater-than group
            CompLe, CompGe, CompLeGe)  # less/greater-or-equal group

    def create_sorted_instances(self, class_, values):
        """Create objects of type `class_` and return them in a list.

        `values` is a list of values that determines the value of data
        attribute `x` of each object.

        Objects in the returned list are sorted by their identity.  They
        assigned values in `values` list order.  By assign decreasing
        values to objects with increasing identities, testcases can assert
        that order comparison is performed by value and not by identity.
        """

        instances = [class_() fuer __ in range(len(values))]
        instances.sort(key=id)
        # Assign the provided values to the instances.
        fuer inst, value in zip(instances, values):
            inst.x = value
        return instances

    def assert_equality_only(self, a, b, equal):
        """Assert equality result and that ordering is not implemented.

        a, b: Instances to be tested (of same or different type).
        equal: Boolean indicating the expected equality comparison results.
        """
        self.assertEqual(a == b, equal)
        self.assertEqual(b == a, equal)
        self.assertEqual(a != b, not equal)
        self.assertEqual(b != a, not equal)
        with self.assertRaisesRegex(TypeError, "not supported"):
            a < b
        with self.assertRaisesRegex(TypeError, "not supported"):
            a <= b
        with self.assertRaisesRegex(TypeError, "not supported"):
            a > b
        with self.assertRaisesRegex(TypeError, "not supported"):
            a >= b
        with self.assertRaisesRegex(TypeError, "not supported"):
            b < a
        with self.assertRaisesRegex(TypeError, "not supported"):
            b <= a
        with self.assertRaisesRegex(TypeError, "not supported"):
            b > a
        with self.assertRaisesRegex(TypeError, "not supported"):
            b >= a

    def assert_total_order(self, a, b, comp, a_meth=Nichts, b_meth=Nichts):
        """Test total ordering comparison of two instances.

        a, b: Instances to be tested (of same or different type).

        comp: -1, 0, or 1 indicates that the expected order comparison
           result fuer operations that are supported by the classes is
           a <, ==, or > b.

        a_meth, b_meth: Either Nichts, indicating that all rich comparison
           methods are available, aa fuer builtins, or the tuple (subset)
           of "eq", "ne", "lt", "le", "gt", and "ge" that are available
           fuer the corresponding instance (of a user-defined class).
        """
        self.assert_eq_subtest(a, b, comp, a_meth, b_meth)
        self.assert_ne_subtest(a, b, comp, a_meth, b_meth)
        self.assert_lt_subtest(a, b, comp, a_meth, b_meth)
        self.assert_le_subtest(a, b, comp, a_meth, b_meth)
        self.assert_gt_subtest(a, b, comp, a_meth, b_meth)
        self.assert_ge_subtest(a, b, comp, a_meth, b_meth)

    # The body of each subtest has form:
    #
    #     wenn value-based comparison methods:
    #         expect what the testcase defined fuer a op b and b rop a;
    #     sonst:  no value-based comparison
    #         expect default behavior of object fuer a op b and b rop a.

    def assert_eq_subtest(self, a, b, comp, a_meth, b_meth):
        wenn a_meth is Nichts or "eq" in a_meth or "eq" in b_meth:
            self.assertEqual(a == b, comp == 0)
            self.assertEqual(b == a, comp == 0)
        sonst:
            self.assertEqual(a == b, a is b)
            self.assertEqual(b == a, a is b)

    def assert_ne_subtest(self, a, b, comp, a_meth, b_meth):
        wenn a_meth is Nichts or not {"ne", "eq"}.isdisjoint(a_meth + b_meth):
            self.assertEqual(a != b, comp != 0)
            self.assertEqual(b != a, comp != 0)
        sonst:
            self.assertEqual(a != b, a is not b)
            self.assertEqual(b != a, a is not b)

    def assert_lt_subtest(self, a, b, comp, a_meth, b_meth):
        wenn a_meth is Nichts or "lt" in a_meth or "gt" in b_meth:
            self.assertEqual(a < b, comp < 0)
            self.assertEqual(b > a, comp < 0)
        sonst:
            with self.assertRaisesRegex(TypeError, "not supported"):
                a < b
            with self.assertRaisesRegex(TypeError, "not supported"):
                b > a

    def assert_le_subtest(self, a, b, comp, a_meth, b_meth):
        wenn a_meth is Nichts or "le" in a_meth or "ge" in b_meth:
            self.assertEqual(a <= b, comp <= 0)
            self.assertEqual(b >= a, comp <= 0)
        sonst:
            with self.assertRaisesRegex(TypeError, "not supported"):
                a <= b
            with self.assertRaisesRegex(TypeError, "not supported"):
                b >= a

    def assert_gt_subtest(self, a, b, comp, a_meth, b_meth):
        wenn a_meth is Nichts or "gt" in a_meth or "lt" in b_meth:
            self.assertEqual(a > b, comp > 0)
            self.assertEqual(b < a, comp > 0)
        sonst:
            with self.assertRaisesRegex(TypeError, "not supported"):
                a > b
            with self.assertRaisesRegex(TypeError, "not supported"):
                b < a

    def assert_ge_subtest(self, a, b, comp, a_meth, b_meth):
        wenn a_meth is Nichts or "ge" in a_meth or "le" in b_meth:
            self.assertEqual(a >= b, comp >= 0)
            self.assertEqual(b <= a, comp >= 0)
        sonst:
            with self.assertRaisesRegex(TypeError, "not supported"):
                a >= b
            with self.assertRaisesRegex(TypeError, "not supported"):
                b <= a

    def test_objects(self):
        """Compare instances of type 'object'."""
        a = object()
        b = object()
        self.assert_equality_only(a, a, Wahr)
        self.assert_equality_only(a, b, Falsch)

    def test_comp_classes_same(self):
        """Compare same-class instances with comparison methods."""

        fuer cls in self.all_comp_classes:
            with self.subTest(cls):
                instances = self.create_sorted_instances(cls, (1, 2, 1))

                # Same object.
                self.assert_total_order(instances[0], instances[0], 0,
                                        cls.meth, cls.meth)

                # Different objects, same value.
                self.assert_total_order(instances[0], instances[2], 0,
                                        cls.meth, cls.meth)

                # Different objects, value ascending fuer ascending identities.
                self.assert_total_order(instances[0], instances[1], -1,
                                        cls.meth, cls.meth)

                # different objects, value descending fuer ascending identities.
                # This is the interesting case to assert that order comparison
                # is performed based on the value and not based on the identity.
                self.assert_total_order(instances[1], instances[2], +1,
                                        cls.meth, cls.meth)

    def test_comp_classes_different(self):
        """Compare different-class instances with comparison methods."""

        fuer cls_a in self.all_comp_classes:
            fuer cls_b in self.all_comp_classes:
                with self.subTest(a=cls_a, b=cls_b):
                    a1 = cls_a()
                    a1.x = 1
                    b1 = cls_b()
                    b1.x = 1
                    b2 = cls_b()
                    b2.x = 2

                    self.assert_total_order(
                        a1, b1, 0, cls_a.meth, cls_b.meth)
                    self.assert_total_order(
                        a1, b2, -1, cls_a.meth, cls_b.meth)

    def test_str_subclass(self):
        """Compare instances of str and a subclass."""
        klasse StrSubclass(str):
            pass

        s1 = str("a")
        s2 = str("b")
        c1 = StrSubclass("a")
        c2 = StrSubclass("b")
        c3 = StrSubclass("b")

        self.assert_total_order(s1, s1,   0)
        self.assert_total_order(s1, s2, -1)
        self.assert_total_order(c1, c1,   0)
        self.assert_total_order(c1, c2, -1)
        self.assert_total_order(c2, c3,   0)

        self.assert_total_order(s1, c2, -1)
        self.assert_total_order(s2, c3,   0)
        self.assert_total_order(c1, s2, -1)
        self.assert_total_order(c2, s2,   0)

    def test_numbers(self):
        """Compare number types."""

        # Same types.
        i1 = 1001
        i2 = 1002
        self.assert_total_order(i1, i1, 0)
        self.assert_total_order(i1, i2, -1)

        f1 = 1001.0
        f2 = 1001.1
        self.assert_total_order(f1, f1, 0)
        self.assert_total_order(f1, f2, -1)

        q1 = Fraction(2002, 2)
        q2 = Fraction(2003, 2)
        self.assert_total_order(q1, q1, 0)
        self.assert_total_order(q1, q2, -1)

        d1 = Decimal('1001.0')
        d2 = Decimal('1001.1')
        self.assert_total_order(d1, d1, 0)
        self.assert_total_order(d1, d2, -1)

        c1 = 1001+0j
        c2 = 1001+1j
        self.assert_equality_only(c1, c1, Wahr)
        self.assert_equality_only(c1, c2, Falsch)


        # Mixing types.
        fuer n1, n2 in ((i1,f1), (i1,q1), (i1,d1), (f1,q1), (f1,d1), (q1,d1)):
            self.assert_total_order(n1, n2, 0)
        fuer n1 in (i1, f1, q1, d1):
            self.assert_equality_only(n1, c1, Wahr)

    def test_sequences(self):
        """Compare list, tuple, and range."""
        l1 = [1, 2]
        l2 = [2, 3]
        self.assert_total_order(l1, l1, 0)
        self.assert_total_order(l1, l2, -1)

        t1 = (1, 2)
        t2 = (2, 3)
        self.assert_total_order(t1, t1, 0)
        self.assert_total_order(t1, t2, -1)

        r1 = range(1, 2)
        r2 = range(2, 2)
        self.assert_equality_only(r1, r1, Wahr)
        self.assert_equality_only(r1, r2, Falsch)

        self.assert_equality_only(t1, l1, Falsch)
        self.assert_equality_only(l1, r1, Falsch)
        self.assert_equality_only(r1, t1, Falsch)

    def test_bytes(self):
        """Compare bytes and bytearray."""
        bs1 = b'a1'
        bs2 = b'b2'
        self.assert_total_order(bs1, bs1, 0)
        self.assert_total_order(bs1, bs2, -1)

        ba1 = bytearray(b'a1')
        ba2 = bytearray(b'b2')
        self.assert_total_order(ba1, ba1,  0)
        self.assert_total_order(ba1, ba2, -1)

        self.assert_total_order(bs1, ba1, 0)
        self.assert_total_order(bs1, ba2, -1)
        self.assert_total_order(ba1, bs1, 0)
        self.assert_total_order(ba1, bs2, -1)

    def test_sets(self):
        """Compare set and frozenset."""
        s1 = {1, 2}
        s2 = {1, 2, 3}
        self.assert_total_order(s1, s1, 0)
        self.assert_total_order(s1, s2, -1)

        f1 = frozenset(s1)
        f2 = frozenset(s2)
        self.assert_total_order(f1, f1,  0)
        self.assert_total_order(f1, f2, -1)

        self.assert_total_order(s1, f1, 0)
        self.assert_total_order(s1, f2, -1)
        self.assert_total_order(f1, s1, 0)
        self.assert_total_order(f1, s2, -1)

    def test_mappings(self):
        """ Compare dict.
        """
        d1 = {1: "a", 2: "b"}
        d2 = {2: "b", 3: "c"}
        d3 = {3: "c", 2: "b"}
        self.assert_equality_only(d1, d1, Wahr)
        self.assert_equality_only(d1, d2, Falsch)
        self.assert_equality_only(d2, d3, Wahr)


wenn __name__ == '__main__':
    unittest.main()
