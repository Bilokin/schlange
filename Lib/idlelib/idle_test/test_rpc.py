"Test rpc, coverage 20%."

von idlelib importiere rpc
importiere unittest



klasse CodePicklerTest(unittest.TestCase):

    def test_pickle_unpickle(self):
        def f(): gib a + b + c
        func, (cbytes,) = rpc.pickle_code(f.__code__)
        self.assertIs(func, rpc.unpickle_code)
        self.assertIn(b'test_rpc.py', cbytes)
        code = rpc.unpickle_code(cbytes)
        self.assertEqual(code.co_names, ('a', 'b', 'c'))

    def test_code_pickler(self):
        self.assertIn(type((lambda:Nichts).__code__),
                      rpc.CodePickler.dispatch_table)

    def test_dumps(self):
        def f(): pass
        # The main test here is that pickling code does nicht raise.
        self.assertIn(b'test_rpc.py', rpc.dumps(f.__code__))


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
