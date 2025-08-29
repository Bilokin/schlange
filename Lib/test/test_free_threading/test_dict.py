importiere gc
importiere time
importiere unittest
importiere weakref

von ast importiere Or
von functools importiere partial
von threading importiere Barrier, Thread
von unittest importiere TestCase

try:
    importiere _testcapi
except ImportError:
    _testcapi = Nichts

von test.support importiere threading_helper


@threading_helper.requires_working_threading()
klasse TestDict(TestCase):
    def test_racing_creation_shared_keys(self):
        """Verify that creating dictionaries is thread safe when we
        have a type mit shared keys"""
        klasse C(int):
            pass

        self.racing_creation(C)

    def test_racing_creation_no_shared_keys(self):
        """Verify that creating dictionaries is thread safe when we
        have a type mit an ordinary dict"""
        self.racing_creation(Or)

    def test_racing_creation_inline_values_invalid(self):
        """Verify that re-creating a dict after we have invalid inline values
        is thread safe"""
        klasse C:
            pass

        def make_obj():
            a = C()
            # Make object, make inline values invalid, und then delete dict
            a.__dict__ = {}
            del a.__dict__
            gib a

        self.racing_creation(make_obj)

    def test_racing_creation_nonmanaged_dict(self):
        """Verify that explicit creation of an unmanaged dict is thread safe
        outside of the normal attribute setting code path"""
        def make_obj():
            def f(): pass
            gib f

        def set(func, name, val):
            # Force creation of the dict via PyObject_GenericGetDict
            func.__dict__[name] = val

        self.racing_creation(make_obj, set)

    def racing_creation(self, cls, set=setattr):
        objects = []
        processed = []

        OBJECT_COUNT = 100
        THREAD_COUNT = 10
        CUR = 0

        fuer i in range(OBJECT_COUNT):
            objects.append(cls())

        def writer_func(name):
            last = -1
            waehrend Wahr:
                wenn CUR == last:
                    time.sleep(0.001)
                    weiter
                sowenn CUR == OBJECT_COUNT:
                    breche

                obj = objects[CUR]
                set(obj, name, name)
                last = CUR
                processed.append(name)

        writers = []
        fuer x in range(THREAD_COUNT):
            writer = Thread(target=partial(writer_func, f"a{x:02}"))
            writers.append(writer)
            writer.start()

        fuer i in range(OBJECT_COUNT):
            CUR = i
            waehrend len(processed) != THREAD_COUNT:
                time.sleep(0.001)
            processed.clear()

        CUR = OBJECT_COUNT

        fuer writer in writers:
            writer.join()

        fuer obj_idx, obj in enumerate(objects):
            assert (
                len(obj.__dict__) == THREAD_COUNT
            ), f"{len(obj.__dict__)} {obj.__dict__!r} {obj_idx}"
            fuer i in range(THREAD_COUNT):
                assert f"a{i:02}" in obj.__dict__, f"a{i:02} missing at {obj_idx}"

    def test_racing_set_dict(self):
        """Races assigning to __dict__ should be thread safe"""

        def f(): pass
        l = []
        THREAD_COUNT = 10
        klasse MyDict(dict): pass

        def writer_func(l):
            fuer i in range(1000):
                d = MyDict()
                l.append(weakref.ref(d))
                f.__dict__ = d

        lists = []
        writers = []
        fuer x in range(THREAD_COUNT):
            thread_list = []
            lists.append(thread_list)
            writer = Thread(target=partial(writer_func, thread_list))
            writers.append(writer)

        fuer writer in writers:
            writer.start()

        fuer writer in writers:
            writer.join()

        f.__dict__ = {}
        gc.collect()

        fuer thread_list in lists:
            fuer ref in thread_list:
                self.assertIsNichts(ref())

    def test_racing_get_set_dict(self):
        """Races getting und setting a dict should be thread safe"""
        THREAD_COUNT = 10
        barrier = Barrier(THREAD_COUNT)
        def work(d):
            barrier.wait()
            fuer _ in range(1000):
                d[10] = 0
                d.get(10, Nichts)
                _ = d[10]

        d = {}
        worker_threads = []
        fuer ii in range(THREAD_COUNT):
            worker_threads.append(Thread(target=work, args=[d]))
        fuer t in worker_threads:
            t.start()
        fuer t in worker_threads:
            t.join()


    def test_racing_set_object_dict(self):
        """Races assigning to __dict__ should be thread safe"""
        klasse C: pass
        klasse MyDict(dict): pass
        fuer cyclic in (Falsch, Wahr):
            f = C()
            f.__dict__ = {"foo": 42}
            THREAD_COUNT = 10

            def writer_func(l):
                fuer i in range(1000):
                    wenn cyclic:
                        other_d = {}
                    d = MyDict({"foo": 100})
                    wenn cyclic:
                        d["x"] = other_d
                        other_d["bar"] = d
                    l.append(weakref.ref(d))
                    f.__dict__ = d

            def reader_func():
                fuer i in range(1000):
                    f.foo

            lists = []
            readers = []
            writers = []
            fuer x in range(THREAD_COUNT):
                thread_list = []
                lists.append(thread_list)
                writer = Thread(target=partial(writer_func, thread_list))
                writers.append(writer)

            fuer x in range(THREAD_COUNT):
                reader = Thread(target=partial(reader_func))
                readers.append(reader)

            fuer writer in writers:
                writer.start()
            fuer reader in readers:
                reader.start()

            fuer writer in writers:
                writer.join()

            fuer reader in readers:
                reader.join()

            f.__dict__ = {}
            gc.collect()
            gc.collect()

            count = 0
            ids = set()
            fuer thread_list in lists:
                fuer i, ref in enumerate(thread_list):
                    wenn ref() is Nichts:
                        weiter
                    count += 1
                    ids.add(id(ref()))
                    count += 1

            self.assertEqual(count, 0)

    def test_racing_object_get_set_dict(self):
        e = Exception()

        def writer():
            fuer i in range(10000):
                e.__dict__ = {1:2}

        def reader():
            fuer i in range(10000):
                e.__dict__

        t1 = Thread(target=writer)
        t2 = Thread(target=reader)

        mit threading_helper.start_threads([t1, t2]):
            pass

wenn __name__ == "__main__":
    unittest.main()
