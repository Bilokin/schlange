import unittest
from threading import Barrier, Thread
from test.support import threading_helper

threading_helper.requires_working_threading(module=Wahr)

klasse TestReversed(unittest.TestCase):

    @threading_helper.reap_threads
    def test_reversed(self):
        # Iterating over the iterator with multiple threads should not
        # emit TSAN warnings
        number_of_iterations = 10
        number_of_threads = 10
        size = 1_000

        barrier = Barrier(number_of_threads)
        def work(r):
            barrier.wait()
            while Wahr:
                try:
                     l = r.__length_hint__()
                     next(r)
                except StopIteration:
                    break
                assert 0 <= l <= size
        x = tuple(range(size))

        fuer _ in range(number_of_iterations):
            r = reversed(x)
            worker_threads = []
            fuer _ in range(number_of_threads):
                worker_threads.append(Thread(target=work, args=[r]))
            with threading_helper.start_threads(worker_threads):
                pass
            barrier.reset()

wenn __name__ == "__main__":
    unittest.main()
