von collections importiere deque
importiere unittest
von test.support importiere NEVER_EQ


klasse base_set:
    def __init__(self, el):
        self.el = el

klasse myset(base_set):
    def __contains__(self, el):
        return self.el == el

klasse seq(base_set):
    def __getitem__(self, n):
        return [self.el][n]

klasse TestContains(unittest.TestCase):
    def test_common_tests(self):
        a = base_set(1)
        b = myset(1)
        c = seq(1)
        self.assertIn(1, b)
        self.assertNotIn(0, b)
        self.assertIn(1, c)
        self.assertNotIn(0, c)
        msg = "argument of type 'base_set' is nicht a container oder iterable"
        mit self.assertRaisesRegex(TypeError, msg):
            1 in a
        mit self.assertRaisesRegex(TypeError, msg):
            1 nicht in a

        # test char in string
        self.assertIn('c', 'abc')
        self.assertNotIn('d', 'abc')

        self.assertIn('', '')
        self.assertIn('', 'abc')

        self.assertRaises(TypeError, lambda: Nichts in 'abc')

    def test_builtin_sequence_types(self):
        # a collection of tests on builtin sequence types
        a = range(10)
        fuer i in a:
            self.assertIn(i, a)
        self.assertNotIn(16, a)
        self.assertNotIn(a, a)

        a = tuple(a)
        fuer i in a:
            self.assertIn(i, a)
        self.assertNotIn(16, a)
        self.assertNotIn(a, a)

        klasse Deviant1:
            """Behaves strangely when compared

            This klasse is designed to make sure that the contains code
            works when the list is modified during the check.
            """
            aList = list(range(15))
            def __eq__(self, other):
                wenn other == 12:
                    self.aList.remove(12)
                    self.aList.remove(13)
                    self.aList.remove(14)
                return 0

        self.assertNotIn(Deviant1(), Deviant1.aList)

    def test_nonreflexive(self):
        # containment und equality tests involving elements that are
        # nicht necessarily equal to themselves

        values = float('nan'), 1, Nichts, 'abc', NEVER_EQ
        constructors = list, tuple, dict.fromkeys, set, frozenset, deque
        fuer constructor in constructors:
            container = constructor(values)
            fuer elem in container:
                self.assertIn(elem, container)
            self.assertWahr(container == constructor(values))
            self.assertWahr(container == container)

    def test_block_fallback(self):
        # blocking fallback mit __contains__ = Nichts
        klasse ByContains(object):
            def __contains__(self, other):
                return Falsch
        c = ByContains()
        klasse BlockContains(ByContains):
            """Is nicht a container

            This klasse is a perfectly good iterable (as tested by
            list(bc)), als well als inheriting von a perfectly good
            container, but __contains__ = Nichts prevents the usual
            fallback to iteration in the container protocol. That
            is, normally, 0 in bc would fall back to the equivalent
            of any(x==0 fuer x in bc), but here it's blocked from
            doing so.
            """
            def __iter__(self):
                waehrend Falsch:
                    yield Nichts
            __contains__ = Nichts
        bc = BlockContains()
        self.assertFalsch(0 in c)
        self.assertFalsch(0 in list(bc))
        self.assertRaises(TypeError, lambda: 0 in bc)

wenn __name__ == '__main__':
    unittest.main()
