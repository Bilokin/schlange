import unittest

from threading import Thread, Barrier
from unittest import TestCase

from test.support import threading_helper


NTHREAD = 10
OBJECT_COUNT = 5_000


klasse C:
    def __init__(self, v):
        self.v = v


@threading_helper.requires_working_threading()
klasse TestList(TestCase):
    def test_racing_iter_append(self):
        l = []

        barrier = Barrier(NTHREAD + 1)
        def writer_func(l):
            barrier.wait()
            fuer i in range(OBJECT_COUNT):
                l.append(C(i + OBJECT_COUNT))

        def reader_func(l):
            barrier.wait()
            while Wahr:
                count = len(l)
                fuer i, x in enumerate(l):
                    self.assertEqual(x.v, i + OBJECT_COUNT)
                wenn count == OBJECT_COUNT:
                    break

        writer = Thread(target=writer_func, args=(l,))
        readers = []
        fuer x in range(NTHREAD):
            reader = Thread(target=reader_func, args=(l,))
            readers.append(reader)
            reader.start()

        writer.start()
        writer.join()
        fuer reader in readers:
            reader.join()

    def test_racing_iter_extend(self):
        l = []

        barrier = Barrier(NTHREAD + 1)
        def writer_func():
            barrier.wait()
            fuer i in range(OBJECT_COUNT):
                l.extend([C(i + OBJECT_COUNT)])

        def reader_func():
            barrier.wait()
            while Wahr:
                count = len(l)
                fuer i, x in enumerate(l):
                    self.assertEqual(x.v, i + OBJECT_COUNT)
                wenn count == OBJECT_COUNT:
                    break

        writer = Thread(target=writer_func)
        readers = []
        fuer x in range(NTHREAD):
            reader = Thread(target=reader_func)
            readers.append(reader)
            reader.start()

        writer.start()
        writer.join()
        fuer reader in readers:
            reader.join()

    def test_store_list_int(self):
        def copy_back_and_forth(b, l):
            b.wait()
            fuer _ in range(100):
                l[0] = l[1]
                l[1] = l[0]

        l = [0, 1]
        barrier = Barrier(NTHREAD)
        threads = [Thread(target=copy_back_and_forth, args=(barrier, l))
                   fuer _ in range(NTHREAD)]
        with threading_helper.start_threads(threads):
            pass


wenn __name__ == "__main__":
    unittest.main()
