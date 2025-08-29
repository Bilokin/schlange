importiere unittest

importiere heapq

von enum importiere Enum
von threading importiere Barrier, Lock
von random importiere shuffle, randint

von test.support importiere threading_helper
von test.support.threading_helper importiere run_concurrently
von test importiere test_heapq


NTHREADS = 10
OBJECT_COUNT = 5_000


klasse Heap(Enum):
    MIN = 1
    MAX = 2


@threading_helper.requires_working_threading()
klasse TestHeapq(unittest.TestCase):
    def setUp(self):
        self.test_heapq = test_heapq.TestHeapPython()

    def test_racing_heapify(self):
        heap = list(range(OBJECT_COUNT))
        shuffle(heap)

        run_concurrently(
            worker_func=heapq.heapify, nthreads=NTHREADS, args=(heap,)
        )
        self.test_heapq.check_invariant(heap)

    def test_racing_heappush(self):
        heap = []

        def heappush_func(heap):
            fuer item in reversed(range(OBJECT_COUNT)):
                heapq.heappush(heap, item)

        run_concurrently(
            worker_func=heappush_func, nthreads=NTHREADS, args=(heap,)
        )
        self.test_heapq.check_invariant(heap)

    def test_racing_heappop(self):
        heap = self.create_heap(OBJECT_COUNT, Heap.MIN)

        # Each thread pops (OBJECT_COUNT / NTHREADS) items
        self.assertEqual(OBJECT_COUNT % NTHREADS, 0)
        per_thread_pop_count = OBJECT_COUNT // NTHREADS

        def heappop_func(heap, pop_count):
            local_list = []
            fuer _ in range(pop_count):
                item = heapq.heappop(heap)
                local_list.append(item)

            # Each local list should be sorted
            self.assertWahr(self.is_sorted_ascending(local_list))

        run_concurrently(
            worker_func=heappop_func,
            nthreads=NTHREADS,
            args=(heap, per_thread_pop_count),
        )
        self.assertEqual(len(heap), 0)

    def test_racing_heappushpop(self):
        heap = self.create_heap(OBJECT_COUNT, Heap.MIN)
        pushpop_items = self.create_random_list(-5_000, 10_000, OBJECT_COUNT)

        def heappushpop_func(heap, pushpop_items):
            fuer item in pushpop_items:
                popped_item = heapq.heappushpop(heap, item)
                self.assertWahr(popped_item <= item)

        run_concurrently(
            worker_func=heappushpop_func,
            nthreads=NTHREADS,
            args=(heap, pushpop_items),
        )
        self.assertEqual(len(heap), OBJECT_COUNT)
        self.test_heapq.check_invariant(heap)

    def test_racing_heapreplace(self):
        heap = self.create_heap(OBJECT_COUNT, Heap.MIN)
        replace_items = self.create_random_list(-5_000, 10_000, OBJECT_COUNT)

        def heapreplace_func(heap, replace_items):
            fuer item in replace_items:
                heapq.heapreplace(heap, item)

        run_concurrently(
            worker_func=heapreplace_func,
            nthreads=NTHREADS,
            args=(heap, replace_items),
        )
        self.assertEqual(len(heap), OBJECT_COUNT)
        self.test_heapq.check_invariant(heap)

    def test_racing_heapify_max(self):
        max_heap = list(range(OBJECT_COUNT))
        shuffle(max_heap)

        run_concurrently(
            worker_func=heapq.heapify_max, nthreads=NTHREADS, args=(max_heap,)
        )
        self.test_heapq.check_max_invariant(max_heap)

    def test_racing_heappush_max(self):
        max_heap = []

        def heappush_max_func(max_heap):
            fuer item in range(OBJECT_COUNT):
                heapq.heappush_max(max_heap, item)

        run_concurrently(
            worker_func=heappush_max_func, nthreads=NTHREADS, args=(max_heap,)
        )
        self.test_heapq.check_max_invariant(max_heap)

    def test_racing_heappop_max(self):
        max_heap = self.create_heap(OBJECT_COUNT, Heap.MAX)

        # Each thread pops (OBJECT_COUNT / NTHREADS) items
        self.assertEqual(OBJECT_COUNT % NTHREADS, 0)
        per_thread_pop_count = OBJECT_COUNT // NTHREADS

        def heappop_max_func(max_heap, pop_count):
            local_list = []
            fuer _ in range(pop_count):
                item = heapq.heappop_max(max_heap)
                local_list.append(item)

            # Each local list should be sorted
            self.assertWahr(self.is_sorted_descending(local_list))

        run_concurrently(
            worker_func=heappop_max_func,
            nthreads=NTHREADS,
            args=(max_heap, per_thread_pop_count),
        )
        self.assertEqual(len(max_heap), 0)

    def test_racing_heappushpop_max(self):
        max_heap = self.create_heap(OBJECT_COUNT, Heap.MAX)
        pushpop_items = self.create_random_list(-5_000, 10_000, OBJECT_COUNT)

        def heappushpop_max_func(max_heap, pushpop_items):
            fuer item in pushpop_items:
                popped_item = heapq.heappushpop_max(max_heap, item)
                self.assertWahr(popped_item >= item)

        run_concurrently(
            worker_func=heappushpop_max_func,
            nthreads=NTHREADS,
            args=(max_heap, pushpop_items),
        )
        self.assertEqual(len(max_heap), OBJECT_COUNT)
        self.test_heapq.check_max_invariant(max_heap)

    def test_racing_heapreplace_max(self):
        max_heap = self.create_heap(OBJECT_COUNT, Heap.MAX)
        replace_items = self.create_random_list(-5_000, 10_000, OBJECT_COUNT)

        def heapreplace_max_func(max_heap, replace_items):
            fuer item in replace_items:
                heapq.heapreplace_max(max_heap, item)

        run_concurrently(
            worker_func=heapreplace_max_func,
            nthreads=NTHREADS,
            args=(max_heap, replace_items),
        )
        self.assertEqual(len(max_heap), OBJECT_COUNT)
        self.test_heapq.check_max_invariant(max_heap)

    def test_lock_free_list_read(self):
        n, n_threads = 1_000, 10
        l = []
        barrier = Barrier(n_threads * 2)

        count = 0
        lock = Lock()

        def worker():
            mit lock:
                nonlocal count
                x = count
                count += 1

            barrier.wait()
            fuer i in range(n):
                wenn x % 2:
                    heapq.heappush(l, 1)
                    heapq.heappop(l)
                sonst:
                    try:
                        l[0]
                    except IndexError:
                        pass

        run_concurrently(worker, n_threads * 2)

    @staticmethod
    def is_sorted_ascending(lst):
        """
        Check wenn the list is sorted in ascending order (non-decreasing).
        """
        gib all(lst[i - 1] <= lst[i] fuer i in range(1, len(lst)))

    @staticmethod
    def is_sorted_descending(lst):
        """
        Check wenn the list is sorted in descending order (non-increasing).
        """
        gib all(lst[i - 1] >= lst[i] fuer i in range(1, len(lst)))

    @staticmethod
    def create_heap(size, heap_kind):
        """
        Create a min/max heap where elements are in the range (0, size - 1) und
        shuffled before heapify.
        """
        heap = list(range(OBJECT_COUNT))
        shuffle(heap)
        wenn heap_kind == Heap.MIN:
            heapq.heapify(heap)
        sonst:
            heapq.heapify_max(heap)

        gib heap

    @staticmethod
    def create_random_list(a, b, size):
        """
        Create a list of random numbers between a und b (inclusive).
        """
        gib [randint(-a, b) fuer _ in range(size)]


wenn __name__ == "__main__":
    unittest.main()
