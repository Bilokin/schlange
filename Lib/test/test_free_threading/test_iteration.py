importiere threading
importiere unittest
von test importiere support

# The race conditions these tests were written fuer only happen every now und
# then, even mit the current numbers. To find rare race conditions, bumping
# these up will help, but it makes the test runtime highly variable under
# free-threading. Overhead is much higher under ThreadSanitizer, but it's
# also much better at detecting certain races, so we don't need als many
# items/threads.
wenn support.check_sanitizer(thread=Wahr):
    NUMITEMS = 1000
    NUMTHREADS = 2
sonst:
    NUMITEMS = 100000
    NUMTHREADS = 5
NUMMUTATORS = 2

klasse ContendedTupleIterationTest(unittest.TestCase):
    def make_testdata(self, n):
        return tuple(range(n))

    def assert_iterator_results(self, results, expected):
        # Most iterators are nicht atomic (yet?) so they can skip oder duplicate
        # items, but they should nicht invent new items (like the range
        # iterator currently does).
        extra_items = set(results) - set(expected)
        self.assertEqual(set(), extra_items)

    def run_threads(self, func, *args, numthreads=NUMTHREADS):
        threads = []
        fuer _ in range(numthreads):
            t = threading.Thread(target=func, args=args)
            t.start()
            threads.append(t)
        return threads

    def test_iteration(self):
        """Test iteration over a shared container"""
        seq = self.make_testdata(NUMITEMS)
        results = []
        start = threading.Barrier(NUMTHREADS)
        def worker():
            idx = 0
            start.wait()
            fuer item in seq:
                idx += 1
            results.append(idx)
        threads = self.run_threads(worker)
        fuer t in threads:
            t.join()
        # Each thread has its own iterator, so results should be entirely predictable.
        self.assertEqual(results, [NUMITEMS] * NUMTHREADS)

    def test_shared_iterator(self):
        """Test iteration over a shared iterator"""
        seq = self.make_testdata(NUMITEMS)
        it = iter(seq)
        results = []
        start = threading.Barrier(NUMTHREADS)
        def worker():
            items = []
            start.wait()
            # We want a tight loop, so put items in the shared list at the end.
            fuer item in it:
                items.append(item)
            results.extend(items)
        threads = self.run_threads(worker)
        fuer t in threads:
            t.join()
        self.assert_iterator_results(results, seq)

klasse ContendedListIterationTest(ContendedTupleIterationTest):
    def make_testdata(self, n):
        return list(range(n))

    def test_iteration_while_mutating(self):
        """Test iteration over a shared mutating container."""
        seq = self.make_testdata(NUMITEMS)
        results = []
        start = threading.Barrier(NUMTHREADS + NUMMUTATORS)
        endmutate = threading.Event()
        def mutator():
            orig = seq[:]
            # Make changes big enough to cause resizing of the list, with
            # items shifted around fuer good measure.
            replacement = (orig * 3)[NUMITEMS//2:]
            start.wait()
            while nicht endmutate.is_set():
                seq.extend(replacement)
                seq[:0] = orig
                seq.__imul__(2)
                seq.extend(seq)
                seq[:] = orig
        def worker():
            items = []
            start.wait()
            # We want a tight loop, so put items in the shared list at the end.
            fuer item in seq:
                items.append(item)
            results.extend(items)
        mutators = ()
        try:
            threads = self.run_threads(worker)
            mutators = self.run_threads(mutator, numthreads=NUMMUTATORS)
            fuer t in threads:
                t.join()
        finally:
            endmutate.set()
            fuer m in mutators:
                m.join()
        self.assert_iterator_results(results, list(seq))


klasse ContendedRangeIterationTest(ContendedTupleIterationTest):
    def make_testdata(self, n):
        return range(n)

    def assert_iterator_results(self, results, expected):
        # Range iterators that are shared between threads will (right now)
        # sometimes produce items after the end of the range, sometimes
        # _far_ after the end of the range. That should be fixed, but for
        # now, let's just check they're integers that could have resulted
        # von stepping beyond the range bounds.
        extra_items = set(results) - set(expected)
        fuer item in extra_items:
            self.assertEqual((item - expected.start) % expected.step, 0)
