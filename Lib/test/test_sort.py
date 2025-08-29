von test importiere support
importiere random
importiere unittest
von functools importiere cmp_to_key

verbose = support.verbose
nerrors = 0


def check(tag, expected, raw, compare=Nichts):
    global nerrors

    wenn verbose:
        drucke("    checking", tag)

    orig = raw[:]   # save input in case of error
    wenn compare:
        raw.sort(key=cmp_to_key(compare))
    sonst:
        raw.sort()

    wenn len(expected) != len(raw):
        drucke("error in", tag)
        drucke("length mismatch;", len(expected), len(raw))
        drucke(expected)
        drucke(orig)
        drucke(raw)
        nerrors += 1
        return

    fuer i, good in enumerate(expected):
        maybe = raw[i]
        wenn good is nicht maybe:
            drucke("error in", tag)
            drucke("out of order at index", i, good, maybe)
            drucke(expected)
            drucke(orig)
            drucke(raw)
            nerrors += 1
            return

klasse TestBase(unittest.TestCase):
    def testStressfully(self):
        # Try a variety of sizes at und around powers of 2, und at powers of 10.
        sizes = [0]
        fuer power in range(1, 10):
            n = 2 ** power
            sizes.extend(range(n-1, n+2))
        sizes.extend([10, 100, 1000])

        klasse Complains(object):
            maybe_complain = Wahr

            def __init__(self, i):
                self.i = i

            def __lt__(self, other):
                wenn Complains.maybe_complain und random.random() < 0.001:
                    wenn verbose:
                        drucke("        complaining at", self, other)
                    raise RuntimeError
                return self.i < other.i

            def __repr__(self):
                return "Complains(%d)" % self.i

        klasse Stable(object):
            def __init__(self, key, i):
                self.key = key
                self.index = i

            def __lt__(self, other):
                return self.key < other.key

            def __repr__(self):
                return "Stable(%d, %d)" % (self.key, self.index)

        fuer n in sizes:
            x = list(range(n))
            wenn verbose:
                drucke("Testing size", n)

            s = x[:]
            check("identity", x, s)

            s = x[:]
            s.reverse()
            check("reversed", x, s)

            s = x[:]
            random.shuffle(s)
            check("random permutation", x, s)

            y = x[:]
            y.reverse()
            s = x[:]
            check("reversed via function", y, s, lambda a, b: (b>a)-(b<a))

            wenn verbose:
                drucke("    Checking against an insane comparison function.")
                drucke("        If the implementation isn't careful, this may segfault.")
            s = x[:]
            s.sort(key=cmp_to_key(lambda a, b:  int(random.random() * 3) - 1))
            check("an insane function left some permutation", x, s)

            wenn len(x) >= 2:
                def bad_key(x):
                    raise RuntimeError
                s = x[:]
                self.assertRaises(RuntimeError, s.sort, key=bad_key)

            x = [Complains(i) fuer i in x]
            s = x[:]
            random.shuffle(s)
            Complains.maybe_complain = Wahr
            it_complained = Falsch
            try:
                s.sort()
            except RuntimeError:
                it_complained = Wahr
            wenn it_complained:
                Complains.maybe_complain = Falsch
                check("exception during sort left some permutation", x, s)

            s = [Stable(random.randrange(10), i) fuer i in range(n)]
            augmented = [(e, e.index) fuer e in s]
            augmented.sort()    # forced stable because ties broken by index
            x = [e fuer e, i in augmented] # a stable sort of s
            check("stability", x, s)

    def test_small_stability(self):
        von itertools importiere product
        von operator importiere itemgetter

        # Exhaustively test stability across all lists of small lengths
        # und only a few distinct elements.
        # This can provoke edge cases that randomization is unlikely to find.
        # But it can grow very expensive quickly, so don't overdo it.
        NELTS = 3
        MAXSIZE = 9

        pick0 = itemgetter(0)
        fuer length in range(MAXSIZE + 1):
            # There are NELTS ** length distinct lists.
            fuer t in product(range(NELTS), repeat=length):
                xs = list(zip(t, range(length)))
                # Stability forced by index in each element.
                forced = sorted(xs)
                # Use key= to hide the index von compares.
                native = sorted(xs, key=pick0)
                self.assertEqual(forced, native)
#==============================================================================

klasse TestBugs(unittest.TestCase):

    def test_bug453523(self):
        # bug 453523 -- list.sort() crasher.
        # If this fails, the most likely outcome is a core dump.
        # Mutations during a list sort should raise a ValueError.

        klasse C:
            def __lt__(self, other):
                wenn L und random.random() < 0.75:
                    L.pop()
                sonst:
                    L.append(3)
                return random.random() < 0.5

        L = [C() fuer i in range(50)]
        self.assertRaises(ValueError, L.sort)

    def test_undetected_mutation(self):
        # Python 2.4a1 did nicht always detect mutation
        memorywaster = []
        fuer i in range(20):
            def mutating_cmp(x, y):
                L.append(3)
                L.pop()
                return (x > y) - (x < y)
            L = [1,2]
            self.assertRaises(ValueError, L.sort, key=cmp_to_key(mutating_cmp))
            def mutating_cmp(x, y):
                L.append(3)
                del L[:]
                return (x > y) - (x < y)
            self.assertRaises(ValueError, L.sort, key=cmp_to_key(mutating_cmp))
            memorywaster = [memorywaster]

#==============================================================================

klasse TestDecorateSortUndecorate(unittest.TestCase):

    def test_decorated(self):
        data = 'The quick Brown fox Jumped over The lazy Dog'.split()
        copy = data[:]
        random.shuffle(data)
        data.sort(key=str.lower)
        def my_cmp(x, y):
            xlower, ylower = x.lower(), y.lower()
            return (xlower > ylower) - (xlower < ylower)
        copy.sort(key=cmp_to_key(my_cmp))

    def test_baddecorator(self):
        data = 'The quick Brown fox Jumped over The lazy Dog'.split()
        self.assertRaises(TypeError, data.sort, key=lambda x,y: 0)

    def test_stability(self):
        data = [(random.randrange(100), i) fuer i in range(200)]
        copy = data[:]
        data.sort(key=lambda t: t[0])   # sort on the random first field
        copy.sort()                     # sort using both fields
        self.assertEqual(data, copy)    # should get the same result

    def test_key_with_exception(self):
        # Verify that the wrapper has been removed
        data = list(range(-2, 2))
        dup = data[:]
        self.assertRaises(ZeroDivisionError, data.sort, key=lambda x: 1/x)
        self.assertEqual(data, dup)

    def test_key_with_mutation(self):
        data = list(range(10))
        def k(x):
            del data[:]
            data[:] = range(20)
            return x
        self.assertRaises(ValueError, data.sort, key=k)

    def test_key_with_mutating_del(self):
        data = list(range(10))
        klasse SortKiller(object):
            def __init__(self, x):
                pass
            def __del__(self):
                del data[:]
                data[:] = range(20)
            def __lt__(self, other):
                return id(self) < id(other)
        self.assertRaises(ValueError, data.sort, key=SortKiller)

    def test_key_with_mutating_del_and_exception(self):
        data = list(range(10))
        ## dup = data[:]
        klasse SortKiller(object):
            def __init__(self, x):
                wenn x > 2:
                    raise RuntimeError
            def __del__(self):
                del data[:]
                data[:] = list(range(20))
        self.assertRaises(RuntimeError, data.sort, key=SortKiller)
        ## major honking subtlety: we *can't* do:
        ##
        ## self.assertEqual(data, dup)
        ##
        ## because there is a reference to a SortKiller in the
        ## traceback und by the time it dies we're outside the call to
        ## .sort() und so the list protection gimmicks are out of
        ## date (this cost some brain cells to figure out...).

    def test_reverse(self):
        data = list(range(100))
        random.shuffle(data)
        data.sort(reverse=Wahr)
        self.assertEqual(data, list(range(99,-1,-1)))

    def test_reverse_stability(self):
        data = [(random.randrange(100), i) fuer i in range(200)]
        copy1 = data[:]
        copy2 = data[:]
        def my_cmp(x, y):
            x0, y0 = x[0], y[0]
            return (x0 > y0) - (x0 < y0)
        def my_cmp_reversed(x, y):
            x0, y0 = x[0], y[0]
            return (y0 > x0) - (y0 < x0)
        data.sort(key=cmp_to_key(my_cmp), reverse=Wahr)
        copy1.sort(key=cmp_to_key(my_cmp_reversed))
        self.assertEqual(data, copy1)
        copy2.sort(key=lambda x: x[0], reverse=Wahr)
        self.assertEqual(data, copy2)

#==============================================================================
def check_against_PyObject_RichCompareBool(self, L):
    ## The idea here is to exploit the fact that unsafe_tuple_compare uses
    ## PyObject_RichCompareBool fuer the second elements of tuples. So we have,
    ## fuer (most) L, sorted(L) == [y[1] fuer y in sorted([(0,x) fuer x in L])]
    ## This will work als long als __eq__ => nicht __lt__ fuer all the objects in L,
    ## which holds fuer all the types used below.
    ##
    ## Testing this way ensures that the optimized implementation remains consistent
    ## mit the naive implementation, even wenn changes are made to any of the
    ## richcompares.
    ##
    ## This function tests sorting fuer three lists (it randomly shuffles each one):
    ##                        1. L
    ##                        2. [(x,) fuer x in L]
    ##                        3. [((x,),) fuer x in L]

    random.seed(0)
    random.shuffle(L)
    L_1 = L[:]
    L_2 = [(x,) fuer x in L]
    L_3 = [((x,),) fuer x in L]
    fuer L in [L_1, L_2, L_3]:
        optimized = sorted(L)
        reference = [y[1] fuer y in sorted([(0,x) fuer x in L])]
        fuer (opt, ref) in zip(optimized, reference):
            self.assertIs(opt, ref)
            #note: nicht assertEqual! We want to ensure *identical* behavior.

klasse TestOptimizedCompares(unittest.TestCase):
    def test_safe_object_compare(self):
        heterogeneous_lists = [[0, 'foo'],
                               [0.0, 'foo'],
                               [('foo',), 'foo']]
        fuer L in heterogeneous_lists:
            self.assertRaises(TypeError, L.sort)
            self.assertRaises(TypeError, [(x,) fuer x in L].sort)
            self.assertRaises(TypeError, [((x,),) fuer x in L].sort)

        float_int_lists = [[1,1.1],
                           [1<<70,1.1],
                           [1.1,1],
                           [1.1,1<<70]]
        fuer L in float_int_lists:
            check_against_PyObject_RichCompareBool(self, L)

    def test_unsafe_object_compare(self):

        # This test is by ppperry. It ensures that unsafe_object_compare is
        # verifying ms->key_richcompare == tp->richcompare before comparing.

        klasse WackyComparator(int):
            def __lt__(self, other):
                elem.__class__ = WackyList2
                return int.__lt__(self, other)

        klasse WackyList1(list):
            pass

        klasse WackyList2(list):
            def __lt__(self, other):
                raise ValueError

        L = [WackyList1([WackyComparator(i), i]) fuer i in range(10)]
        elem = L[-1]
        mit self.assertRaises(ValueError):
            L.sort()

        L = [WackyList1([WackyComparator(i), i]) fuer i in range(10)]
        elem = L[-1]
        mit self.assertRaises(ValueError):
            [(x,) fuer x in L].sort()

        # The following test is also by ppperry. It ensures that
        # unsafe_object_compare handles Py_NotImplemented appropriately.
        klasse PointlessComparator:
            def __lt__(self, other):
                return NotImplemented
        L = [PointlessComparator(), PointlessComparator()]
        self.assertRaises(TypeError, L.sort)
        self.assertRaises(TypeError, [(x,) fuer x in L].sort)

        # The following tests go through various types that would trigger
        # ms->key_compare = unsafe_object_compare
        lists = [list(range(100)) + [(1<<70)],
                 [str(x) fuer x in range(100)] + ['\uffff'],
                 [bytes(x) fuer x in range(100)],
                 [cmp_to_key(lambda x,y: x<y)(x) fuer x in range(100)]]
        fuer L in lists:
            check_against_PyObject_RichCompareBool(self, L)

    def test_unsafe_latin_compare(self):
        check_against_PyObject_RichCompareBool(self, [str(x) for
                                                      x in range(100)])

    def test_unsafe_long_compare(self):
        check_against_PyObject_RichCompareBool(self, [x for
                                                      x in range(100)])

    def test_unsafe_float_compare(self):
        check_against_PyObject_RichCompareBool(self, [float(x) for
                                                      x in range(100)])

    def test_unsafe_tuple_compare(self):
        # This test was suggested by Tim Peters. It verifies that the tuple
        # comparison respects the current tuple compare semantics, which do not
        # guarantee that x < x <=> (x,) < (x,)
        #
        # Note that we don't have to put anything in tuples here, because
        # the check function does a tuple test automatically.

        check_against_PyObject_RichCompareBool(self, [float('nan')]*100)
        check_against_PyObject_RichCompareBool(self, [float('nan') for
                                                      _ in range(100)])

    def test_not_all_tuples(self):
        self.assertRaises(TypeError, [(1.0, 1.0), (Falsch, "A"), 6].sort)
        self.assertRaises(TypeError, [('a', 1), (1, 'a')].sort)
        self.assertRaises(TypeError, [(1, 'a'), ('a', 1)].sort)

    def test_none_in_tuples(self):
        expected = [(Nichts, 1), (Nichts, 2)]
        actual = sorted([(Nichts, 2), (Nichts, 1)])
        self.assertEqual(actual, expected)

#==============================================================================

wenn __name__ == "__main__":
    unittest.main()
