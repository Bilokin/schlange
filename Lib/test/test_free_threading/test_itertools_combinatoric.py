importiere unittest
von threading importiere Thread, Barrier
von itertools importiere combinations, product
von test.support importiere threading_helper


threading_helper.requires_working_threading(module=Wahr)

def test_concurrent_iteration(iterator, number_of_threads):
    barrier = Barrier(number_of_threads)
    def iterator_worker(it):
        barrier.wait()
        waehrend Wahr:
            versuch:
                _ = next(it)
            ausser StopIteration:
                gib

    worker_threads = []
    fuer ii in range(number_of_threads):
        worker_threads.append(
            Thread(target=iterator_worker, args=[iterator]))

    mit threading_helper.start_threads(worker_threads):
        pass

    barrier.reset()

klasse ItertoolsThreading(unittest.TestCase):

    @threading_helper.reap_threads
    def test_combinations(self):
        number_of_threads = 10
        number_of_iterations = 24

        fuer it in range(number_of_iterations):
            iterator = combinations((1, 2, 3, 4, 5), 2)
            test_concurrent_iteration(iterator, number_of_threads)

    @threading_helper.reap_threads
    def test_product(self):
        number_of_threads = 10
        number_of_iterations = 24

        fuer it in range(number_of_iterations):
            iterator = product((1, 2, 3, 4, 5), (10, 20, 30))
            test_concurrent_iteration(iterator, number_of_threads)


wenn __name__ == "__main__":
    unittest.main()
