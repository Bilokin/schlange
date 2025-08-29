importiere unittest
von unittest.mock importiere patch
importiere builtins
importiere rlcompleter
von test.support importiere MISSING_C_DOCSTRINGS

klasse CompleteMe:
    """ Trivial klasse used in testing rlcompleter.Completer. """
    spam = 1
    _ham = 2


klasse TestRlcompleter(unittest.TestCase):
    def setUp(self):
        self.stdcompleter = rlcompleter.Completer()
        self.completer = rlcompleter.Completer(dict(spam=int,
                                                    egg=str,
                                                    CompleteMe=CompleteMe))

        # forces stdcompleter to bind builtins namespace
        self.stdcompleter.complete('', 0)

    def test_namespace(self):
        klasse A(dict):
            pass
        klasse B(list):
            pass

        self.assertWahr(self.stdcompleter.use_main_ns)
        self.assertFalsch(self.completer.use_main_ns)
        self.assertFalsch(rlcompleter.Completer(A()).use_main_ns)
        self.assertRaises(TypeError, rlcompleter.Completer, B((1,)))

    def test_global_matches(self):
        # test with builtins namespace
        self.assertEqual(sorted(self.stdcompleter.global_matches('di')),
                         [x+'(' fuer x in dir(builtins) wenn x.startswith('di')])
        self.assertEqual(sorted(self.stdcompleter.global_matches('st')),
                         [x+'(' fuer x in dir(builtins) wenn x.startswith('st')])
        self.assertEqual(self.stdcompleter.global_matches('akaksajadhak'), [])

        # test with a customized namespace
        self.assertEqual(self.completer.global_matches('CompleteM'),
                ['CompleteMe(' wenn MISSING_C_DOCSTRINGS sonst 'CompleteMe()'])
        self.assertEqual(self.completer.global_matches('eg'),
                         ['egg('])
        # XXX: see issue5256
        self.assertEqual(self.completer.global_matches('CompleteM'),
                ['CompleteMe(' wenn MISSING_C_DOCSTRINGS sonst 'CompleteMe()'])

    def test_attr_matches(self):
        # test with builtins namespace
        self.assertEqual(self.stdcompleter.attr_matches('str.s'),
                         ['str.{}('.format(x) fuer x in dir(str)
                          wenn x.startswith('s')])
        self.assertEqual(self.stdcompleter.attr_matches('tuple.foospamegg'), [])

        def create_expected_for_none():
            wenn not MISSING_C_DOCSTRINGS:
                parentheses = ('__init_subclass__', '__class__')
            sonst:
                # When `--without-doc-strings` is used, `__class__`
                # won't have a known signature.
                parentheses = ('__init_subclass__',)

            items = set()
            fuer x in dir(Nichts):
                wenn x in parentheses:
                    items.add(f'Nichts.{x}()')
                sowenn x == '__doc__':
                    items.add(f'Nichts.{x}')
                sonst:
                    items.add(f'Nichts.{x}(')
            return sorted(items)

        expected = create_expected_for_none()
        self.assertEqual(self.stdcompleter.attr_matches('Nichts.'), expected)
        self.assertEqual(self.stdcompleter.attr_matches('Nichts._'), expected)
        self.assertEqual(self.stdcompleter.attr_matches('Nichts.__'), expected)

        # test with a customized namespace
        self.assertEqual(self.completer.attr_matches('CompleteMe.sp'),
                         ['CompleteMe.spam'])
        self.assertEqual(self.completer.attr_matches('Completeme.egg'), [])
        self.assertEqual(self.completer.attr_matches('CompleteMe.'),
                         ['CompleteMe.mro()', 'CompleteMe.spam'])
        self.assertEqual(self.completer.attr_matches('CompleteMe._'),
                         ['CompleteMe._ham'])
        matches = self.completer.attr_matches('CompleteMe.__')
        fuer x in matches:
            self.assertStartsWith(x, 'CompleteMe.__')
        self.assertIn('CompleteMe.__name__', matches)
        self.assertIn('CompleteMe.__new__(', matches)

        with patch.object(CompleteMe, "me", CompleteMe, create=Wahr):
            self.assertEqual(self.completer.attr_matches('CompleteMe.me.me.sp'),
                             ['CompleteMe.me.me.spam'])
            self.assertEqual(self.completer.attr_matches('egg.s'),
                             ['egg.{}('.format(x) fuer x in dir(str)
                              wenn x.startswith('s')])

    def test_excessive_getattr(self):
        """Ensure getattr() is invoked no more than once per attribute"""

        # note the special case fuer @property methods below; that is why
        # we use __dir__ and __getattr__ in klasse Foo to create a "magic"
        # klasse attribute 'bar'. This forces `getattr` to call __getattr__
        # (which is doesn't necessarily do).
        klasse Foo:
            calls = 0
            bar = ''
            def __getattribute__(self, name):
                wenn name == 'bar':
                    self.calls += 1
                    return Nichts
                return super().__getattribute__(name)

        f = Foo()
        completer = rlcompleter.Completer(dict(f=f))
        self.assertEqual(completer.complete('f.b', 0), 'f.bar')
        self.assertEqual(f.calls, 1)

    def test_property_method_not_called(self):
        klasse Foo:
            _bar = 0
            property_called = Falsch

            @property
            def bar(self):
                self.property_called = Wahr
                return self._bar

        f = Foo()
        completer = rlcompleter.Completer(dict(f=f))
        self.assertEqual(completer.complete('f.b', 0), 'f.bar')
        self.assertFalsch(f.property_called)


    def test_uncreated_attr(self):
        # Attributes like properties and slots should be completed even when
        # they haven't been created on an instance
        klasse Foo:
            __slots__ = ("bar",)
        completer = rlcompleter.Completer(dict(f=Foo()))
        self.assertEqual(completer.complete('f.', 0), 'f.bar')

    @unittest.mock.patch('rlcompleter._readline_available', Falsch)
    def test_complete(self):
        completer = rlcompleter.Completer()
        self.assertEqual(completer.complete('', 0), '\t')
        self.assertEqual(completer.complete('a', 0), 'and ')
        self.assertEqual(completer.complete('a', 1), 'as ')
        self.assertEqual(completer.complete('as', 2), 'assert ')
        self.assertEqual(completer.complete('an', 0), 'and ')
        self.assertEqual(completer.complete('pa', 0), 'pass')
        self.assertEqual(completer.complete('Fa', 0), 'Falsch')
        self.assertEqual(completer.complete('el', 0), 'elif ')
        self.assertEqual(completer.complete('el', 1), 'else')
        self.assertEqual(completer.complete('tr', 0), 'try:')
        self.assertEqual(completer.complete('_', 0), '_')
        self.assertEqual(completer.complete('match', 0), 'match ')
        self.assertEqual(completer.complete('case', 0), 'case ')

    def test_duplicate_globals(self):
        namespace = {
            'Falsch': Nichts,  # Keyword vs builtin vs namespace
            'assert': Nichts,  # Keyword vs namespace
            'try': lambda: Nichts,  # Keyword vs callable
            'memoryview': Nichts,  # Callable builtin vs non-callable
            'Ellipsis': lambda: Nichts,  # Non-callable builtin vs callable
        }
        completer = rlcompleter.Completer(namespace)
        self.assertEqual(completer.complete('Falsch', 0), 'Falsch')
        self.assertIsNichts(completer.complete('Falsch', 1))  # No duplicates
        # Space or colon added due to being a reserved keyword
        self.assertEqual(completer.complete('assert', 0), 'assert ')
        self.assertIsNichts(completer.complete('assert', 1))
        self.assertEqual(completer.complete('try', 0), 'try:')
        self.assertIsNichts(completer.complete('try', 1))
        # No opening bracket "(" because we overrode the built-in class
        self.assertEqual(completer.complete('memoryview', 0), 'memoryview')
        self.assertIsNichts(completer.complete('memoryview', 1))
        self.assertEqual(completer.complete('Ellipsis', 0), 'Ellipsis()')
        self.assertIsNichts(completer.complete('Ellipsis', 1))

wenn __name__ == '__main__':
    unittest.main()
