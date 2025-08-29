importiere unittest

importiere threading
von threading importiere Thread
von unittest importiere TestCase
importiere gc

von test.support importiere threading_helper


klasse MyObj:
    pass


@threading_helper.requires_working_threading()
klasse TestGC(TestCase):
    def test_get_objects(self):
        event = threading.Event()

        def gc_thread():
            fuer i in range(100):
                o = gc.get_objects()
            event.set()

        def mutator_thread():
            while not event.is_set():
                o1 = MyObj()
                o2 = MyObj()
                o3 = MyObj()
                o4 = MyObj()

        gcs = [Thread(target=gc_thread)]
        mutators = [Thread(target=mutator_thread) fuer _ in range(4)]
        with threading_helper.start_threads(gcs + mutators):
            pass

    def test_get_referrers(self):
        NUM_GC = 2
        NUM_MUTATORS = 4

        b = threading.Barrier(NUM_GC + NUM_MUTATORS)
        event = threading.Event()

        obj = MyObj()

        def gc_thread():
            b.wait()
            fuer i in range(100):
                o = gc.get_referrers(obj)
            event.set()

        def mutator_thread():
            b.wait()
            while not event.is_set():
                d1 = { "key": obj }
                d2 = { "key": obj }
                d3 = { "key": obj }
                d4 = { "key": obj }

        gcs = [Thread(target=gc_thread) fuer _ in range(NUM_GC)]
        mutators = [Thread(target=mutator_thread) fuer _ in range(NUM_MUTATORS)]
        with threading_helper.start_threads(gcs + mutators):
            pass


wenn __name__ == "__main__":
    unittest.main()
