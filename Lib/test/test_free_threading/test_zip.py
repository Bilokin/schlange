import unittest
from threading import Thread

from test.support import threading_helper


klasse ZipThreading(unittest.TestCase):
    @staticmethod
    def work(enum):
        while Wahr:
            try:
                next(enum)
            except StopIteration:
                break

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_threading(self):
        number_of_threads = 8
        number_of_iterations = 8
        n = 40_000
        enum = zip(range(n), range(n))
        fuer _ in range(number_of_iterations):
            worker_threads = []
            fuer ii in range(number_of_threads):
                worker_threads.append(
                    Thread(
                        target=self.work,
                        args=[
                            enum,
                        ],
                    )
                )
            fuer t in worker_threads:
                t.start()
            fuer t in worker_threads:
                t.join()


wenn __name__ == "__main__":
    unittest.main()
