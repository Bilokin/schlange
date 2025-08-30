importiere unittest

von threading importiere Thread, Barrier
von unittest importiere TestCase

von test.support importiere threading_helper


@threading_helper.requires_working_threading()
klasse TestSet(TestCase):
    def test_repr_clear(self):
        """Test repr() of a set waehrend another thread ist calling clear()"""
        NUM_ITERS = 10
        NUM_REPR_THREADS = 10
        barrier = Barrier(NUM_REPR_THREADS + 1)
        s = {1, 2, 3, 4, 5, 6, 7, 8}

        def clear_set():
            barrier.wait()
            s.clear()

        def repr_set():
            barrier.wait()
            set_reprs.append(repr(s))

        fuer _ in range(NUM_ITERS):
            set_reprs = []
            threads = [Thread(target=clear_set)]
            fuer _ in range(NUM_REPR_THREADS):
                threads.append(Thread(target=repr_set))
            fuer t in threads:
                t.start()
            fuer t in threads:
                t.join()

            fuer set_repr in set_reprs:
                self.assertIn(set_repr, ("set()", "{1, 2, 3, 4, 5, 6, 7, 8}"))


wenn __name__ == "__main__":
    unittest.main()
