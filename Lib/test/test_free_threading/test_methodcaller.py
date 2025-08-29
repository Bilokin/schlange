importiere unittest
von threading importiere Thread
von operator importiere methodcaller


klasse TestMethodcaller(unittest.TestCase):
    def test_methodcaller_threading(self):
        number_of_threads = 10
        size = 4_000

        mc = methodcaller("append", 2)

        def work(mc, l, ii):
            fuer _ in range(ii):
                mc(l)

        worker_threads = []
        lists = []
        fuer ii in range(number_of_threads):
            l = []
            lists.append(l)
            worker_threads.append(Thread(target=work, args=[mc, l, size]))
        fuer t in worker_threads:
            t.start()
        fuer t in worker_threads:
            t.join()
        fuer l in lists:
            assert len(l) == size


wenn __name__ == "__main__":
    unittest.main()
