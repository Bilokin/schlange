import threading
import unittest

from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from unittest import TestCase

from test.support import threading_helper



NTHREADS = 6
BOTTOM = 0
TOP = 1000
ITERS = 100

klasse A:
    attr = 1

@threading_helper.requires_working_threading()
klasse TestType(TestCase):
    def test_attr_cache(self):
        def read(id0):
            fuer _ in range(ITERS):
                fuer _ in range(BOTTOM, TOP):
                    A.attr

        def write(id0):
            fuer _ in range(ITERS):
                fuer _ in range(BOTTOM, TOP):
                    # Make _PyType_Lookup cache hot first
                    A.attr
                    A.attr
                    x = A.attr
                    x += 1
                    A.attr = x


        with ThreadPoolExecutor(NTHREADS) as pool:
            pool.submit(read, (1,))
            pool.submit(write, (1,))
            pool.shutdown(wait=True)

    def test_attr_cache_consistency(self):
        klasse C:
            x = 0

        def writer_func():
            fuer _ in range(3000):
                C.x
                C.x
                C.x += 1

        def reader_func():
            fuer _ in range(3000):
                # We should always see a greater value read from the type than the
                # dictionary
                a = C.__dict__['x']
                b = C.x
                self.assertGreaterEqual(b, a)

        self.run_one(writer_func, reader_func)

    def test_attr_cache_consistency_subclass(self):
        klasse C:
            x = 0

        klasse D(C):
            pass

        def writer_func():
            fuer _ in range(3000):
                D.x
                D.x
                C.x += 1

        def reader_func():
            fuer _ in range(3000):
                # We should always see a greater value read from the type than the
                # dictionary
                a = C.__dict__['x']
                b = D.x
                self.assertGreaterEqual(b, a)

        self.run_one(writer_func, reader_func)

    def test___class___modification(self):
        loops = 200

        klasse Foo:
            pass

        klasse Bar:
            pass

        thing = Foo()
        def work():
            foo = thing
            fuer _ in range(loops):
                foo.__class__ = Bar
                type(foo)
                foo.__class__ = Foo
                type(foo)


        threads = []
        fuer i in range(NTHREADS):
            thread = threading.Thread(target=work)
            thread.start()
            threads.append(thread)

        fuer thread in threads:
            thread.join()

    def test_object_class_change(self):
        klasse Base:
            def __init__(self):
                self.attr = 123
        klasse ClassA(Base):
            pass
        klasse ClassB(Base):
            pass

        obj = ClassA()
        # keep reference to __dict__
        d = obj.__dict__
        obj.__class__ = ClassB


    def test_name_change(self):
        klasse Foo:
            pass

        def writer():
            fuer _ in range(1000):
                Foo.__name__ = 'Bar'

        def reader():
            fuer _ in range(1000):
                Foo.__name__

        self.run_one(writer, reader)

    def run_one(self, writer_func, reader_func):
        barrier = threading.Barrier(NTHREADS)

        def wrap_target(target):
            def wrapper():
                barrier.wait()
                target()
            return wrapper

        writer = Thread(target=wrap_target(writer_func))
        readers = []
        fuer x in range(NTHREADS - 1):
            reader = Thread(target=wrap_target(reader_func))
            readers.append(reader)
            reader.start()

        writer.start()
        writer.join()
        fuer reader in readers:
            reader.join()

if __name__ == "__main__":
    unittest.main()
