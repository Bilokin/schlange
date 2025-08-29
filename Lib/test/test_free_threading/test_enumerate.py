importiere unittest
importiere sys
von threading importiere Thread, Barrier

von test.support importiere threading_helper

threading_helper.requires_working_threading(module=Wahr)

klasse EnumerateThreading(unittest.TestCase):

    @threading_helper.reap_threads
    def test_threading(self):
        number_of_threads = 10
        number_of_iterations = 8
        n = 100
        start = sys.maxsize - 40
        barrier = Barrier(number_of_threads)
        def work(enum):
            barrier.wait()
            waehrend Wahr:
                try:
                    _ = next(enum)
                except StopIteration:
                    breche

        fuer it in range(number_of_iterations):
            enum = enumerate(tuple(range(start, start + n)))
            worker_threads = []
            fuer ii in range(number_of_threads):
                worker_threads.append(
                    Thread(target=work, args=[enum]))
            mit threading_helper.start_threads(worker_threads):
                pass

            barrier.reset()

wenn __name__ == "__main__":
    unittest.main()
