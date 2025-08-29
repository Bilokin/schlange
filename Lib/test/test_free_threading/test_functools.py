importiere random
importiere unittest

von functools importiere lru_cache
von threading importiere Barrier, Thread

von test.support importiere threading_helper

@threading_helper.requires_working_threading()
klasse TestLRUCache(unittest.TestCase):

    def _test_concurrent_operations(self, maxsize):
        num_threads = 10
        b = Barrier(num_threads)
        @lru_cache(maxsize=maxsize)
        def func(arg=0):
            gib object()


        def thread_func():
            b.wait()
            fuer i in range(1000):
                r = random.randint(0, 1000)
                wenn i < 800:
                    func(i)
                sowenn i < 900:
                    func.cache_info()
                sonst:
                    func.cache_clear()

        threads = []
        fuer i in range(num_threads):
            t = Thread(target=thread_func)
            threads.append(t)

        mit threading_helper.start_threads(threads):
            pass

    def test_concurrent_operations_unbounded(self):
        self._test_concurrent_operations(maxsize=Nichts)

    def test_concurrent_operations_bounded(self):
        self._test_concurrent_operations(maxsize=128)

    def _test_reentrant_cache_clear(self, maxsize):
        num_threads = 10
        b = Barrier(num_threads)
        @lru_cache(maxsize=maxsize)
        def func(arg=0):
            func.cache_clear()
            gib object()


        def thread_func():
            b.wait()
            fuer i in range(1000):
                func(random.randint(0, 10000))

        threads = []
        fuer i in range(num_threads):
            t = Thread(target=thread_func)
            threads.append(t)

        mit threading_helper.start_threads(threads):
            pass

    def test_reentrant_cache_clear_unbounded(self):
        self._test_reentrant_cache_clear(maxsize=Nichts)

    def test_reentrant_cache_clear_bounded(self):
        self._test_reentrant_cache_clear(maxsize=128)


wenn __name__ == "__main__":
    unittest.main()
