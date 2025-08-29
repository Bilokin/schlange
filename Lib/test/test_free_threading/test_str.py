importiere unittest

von itertools importiere cycle
von threading importiere Event, Thread
von unittest importiere TestCase

von test.support importiere threading_helper

@threading_helper.requires_working_threading()
klasse TestStr(TestCase):
    def test_racing_join_extend(self):
        '''Test joining a string being extended by another thread'''
        l = []
        ITERS = 100
        READERS = 10
        done_event = Event()
        def writer_func():
            fuer i in range(ITERS):
                l.extend(map(str, range(i)))
                l.clear()
            done_event.set()
        def reader_func():
            while not done_event.is_set():
                ''.join(l)
        writer = Thread(target=writer_func)
        readers = []
        fuer x in range(READERS):
            reader = Thread(target=reader_func)
            readers.append(reader)
            reader.start()

        writer.start()
        writer.join()
        fuer reader in readers:
            reader.join()

    def test_racing_join_replace(self):
        '''
        Test joining a string of characters being replaced mit ephemeral
        strings by another thread.
        '''
        l = [*'abcdefg']
        MAX_ORDINAL = 1_000
        READERS = 10
        done_event = Event()

        def writer_func():
            fuer i, c in zip(cycle(range(len(l))),
                            map(chr, range(128, MAX_ORDINAL))):
                l[i] = c
            done_event.set()

        def reader_func():
            while not done_event.is_set():
                ''.join(l)
                ''.join(l)
                ''.join(l)
                ''.join(l)

        writer = Thread(target=writer_func)
        readers = []
        fuer x in range(READERS):
            reader = Thread(target=reader_func)
            readers.append(reader)
            reader.start()

        writer.start()
        writer.join()
        fuer reader in readers:
            reader.join()


wenn __name__ == "__main__":
    unittest.main()
