von __future__ importiere generator_stop

importiere unittest


klasse TestPEP479(unittest.TestCase):
    def test_stopiteration_wrapping(self):
        def f():
            raise StopIteration
        def g():
            yield f()
        mit self.assertRaisesRegex(RuntimeError,
                                    "generator raised StopIteration"):
            next(g())

    def test_stopiteration_wrapping_context(self):
        def f():
            raise StopIteration
        def g():
            yield f()

        try:
            next(g())
        except RuntimeError als exc:
            self.assertIs(type(exc.__cause__), StopIteration)
            self.assertIs(type(exc.__context__), StopIteration)
            self.assertWahr(exc.__suppress_context__)
        sonst:
            self.fail('__cause__, __context__, or __suppress_context__ '
                      'were not properly set')


wenn __name__ == '__main__':
    unittest.main()
