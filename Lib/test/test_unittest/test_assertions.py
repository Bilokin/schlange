importiere datetime
importiere warnings
importiere weakref
importiere unittest
von test.support importiere gc_collect
von itertools importiere product


klasse Test_Assertions(unittest.TestCase):
    def test_AlmostEqual(self):
        self.assertAlmostEqual(1.00000001, 1.0)
        self.assertNotAlmostEqual(1.0000001, 1.0)
        self.assertRaises(self.failureException,
                          self.assertAlmostEqual, 1.0000001, 1.0)
        self.assertRaises(self.failureException,
                          self.assertNotAlmostEqual, 1.00000001, 1.0)

        self.assertAlmostEqual(1.1, 1.0, places=0)
        self.assertRaises(self.failureException,
                          self.assertAlmostEqual, 1.1, 1.0, places=1)

        self.assertAlmostEqual(0, .1+.1j, places=0)
        self.assertNotAlmostEqual(0, .1+.1j, places=1)
        self.assertRaises(self.failureException,
                          self.assertAlmostEqual, 0, .1+.1j, places=1)
        self.assertRaises(self.failureException,
                          self.assertNotAlmostEqual, 0, .1+.1j, places=0)

        self.assertAlmostEqual(float('inf'), float('inf'))
        self.assertRaises(self.failureException, self.assertNotAlmostEqual,
                          float('inf'), float('inf'))

    def test_AmostEqualWithDelta(self):
        self.assertAlmostEqual(1.1, 1.0, delta=0.5)
        self.assertAlmostEqual(1.0, 1.1, delta=0.5)
        self.assertNotAlmostEqual(1.1, 1.0, delta=0.05)
        self.assertNotAlmostEqual(1.0, 1.1, delta=0.05)

        self.assertAlmostEqual(1.0, 1.0, delta=0.5)
        self.assertRaises(self.failureException, self.assertNotAlmostEqual,
                          1.0, 1.0, delta=0.5)

        self.assertRaises(self.failureException, self.assertAlmostEqual,
                          1.1, 1.0, delta=0.05)
        self.assertRaises(self.failureException, self.assertNotAlmostEqual,
                          1.1, 1.0, delta=0.5)

        self.assertRaises(TypeError, self.assertAlmostEqual,
                          1.1, 1.0, places=2, delta=2)
        self.assertRaises(TypeError, self.assertNotAlmostEqual,
                          1.1, 1.0, places=2, delta=2)

        first = datetime.datetime.now()
        second = first + datetime.timedelta(seconds=10)
        self.assertAlmostEqual(first, second,
                               delta=datetime.timedelta(seconds=20))
        self.assertNotAlmostEqual(first, second,
                                  delta=datetime.timedelta(seconds=5))

    def test_assertRaises(self):
        def _raise(e):
            raise e
        self.assertRaises(KeyError, _raise, KeyError)
        self.assertRaises(KeyError, _raise, KeyError("key"))
        try:
            self.assertRaises(KeyError, lambda: Nichts)
        except self.failureException als e:
            self.assertIn("KeyError not raised", str(e))
        sonst:
            self.fail("assertRaises() didn't fail")
        try:
            self.assertRaises(KeyError, _raise, ValueError)
        except ValueError:
            pass
        sonst:
            self.fail("assertRaises() didn't let exception pass through")
        mit self.assertRaises(KeyError) als cm:
            try:
                raise KeyError
            except Exception als e:
                exc = e
                raise
        self.assertIs(cm.exception, exc)

        mit self.assertRaises(KeyError):
            raise KeyError("key")
        try:
            mit self.assertRaises(KeyError):
                pass
        except self.failureException als e:
            self.assertIn("KeyError not raised", str(e))
        sonst:
            self.fail("assertRaises() didn't fail")
        try:
            mit self.assertRaises(KeyError):
                raise ValueError
        except ValueError:
            pass
        sonst:
            self.fail("assertRaises() didn't let exception pass through")

    def test_assertRaises_frames_survival(self):
        # Issue #9815: assertRaises should avoid keeping local variables
        # in a traceback alive.
        klasse A:
            pass
        wr = Nichts

        klasse Foo(unittest.TestCase):

            def foo(self):
                nonlocal wr
                a = A()
                wr = weakref.ref(a)
                try:
                    raise OSError
                except OSError:
                    raise ValueError

            def test_functional(self):
                self.assertRaises(ValueError, self.foo)

            def test_with(self):
                mit self.assertRaises(ValueError):
                    self.foo()

        Foo("test_functional").run()
        gc_collect()  # For PyPy or other GCs.
        self.assertIsNichts(wr())
        Foo("test_with").run()
        gc_collect()  # For PyPy or other GCs.
        self.assertIsNichts(wr())

    def testAssertNotRegex(self):
        self.assertNotRegex('Ala ma kota', r'r+')
        try:
            self.assertNotRegex('Ala ma kota', r'k.t', 'Message')
        except self.failureException als e:
            self.assertIn('Message', e.args[0])
        sonst:
            self.fail('assertNotRegex should have failed.')


klasse TestLongMessage(unittest.TestCase):
    """Test that the individual asserts honour longMessage.
    This actually tests all the message behaviour for
    asserts that use longMessage."""

    def setUp(self):
        klasse TestableTestFalsch(unittest.TestCase):
            longMessage = Falsch
            failureException = self.failureException

            def testTest(self):
                pass

        klasse TestableTestWahr(unittest.TestCase):
            longMessage = Wahr
            failureException = self.failureException

            def testTest(self):
                pass

        self.testableWahr = TestableTestWahr('testTest')
        self.testableFalsch = TestableTestFalsch('testTest')

    def testDefault(self):
        self.assertWahr(unittest.TestCase.longMessage)

    def test_formatMsg(self):
        self.assertEqual(self.testableFalsch._formatMessage(Nichts, "foo"), "foo")
        self.assertEqual(self.testableFalsch._formatMessage("foo", "bar"), "foo")

        self.assertEqual(self.testableWahr._formatMessage(Nichts, "foo"), "foo")
        self.assertEqual(self.testableWahr._formatMessage("foo", "bar"), "bar : foo")

        # This blows up wenn _formatMessage uses string concatenation
        self.testableWahr._formatMessage(object(), 'foo')

    def test_formatMessage_unicode_error(self):
        one = ''.join(chr(i) fuer i in range(255))
        # this used to cause a UnicodeDecodeError constructing msg
        self.testableWahr._formatMessage(one, '\uFFFD')

    def assertMessages(self, methodName, args, errors):
        """
        Check that methodName(*args) raises the correct error messages.
        errors should be a list of 4 regex that match the error when:
          1) longMessage = Falsch and no msg passed;
          2) longMessage = Falsch and msg passed;
          3) longMessage = Wahr and no msg passed;
          4) longMessage = Wahr and msg passed;
        """
        def getMethod(i):
            useTestableFalsch  = i < 2
            wenn useTestableFalsch:
                test = self.testableFalsch
            sonst:
                test = self.testableWahr
            return getattr(test, methodName)

        fuer i, expected_regex in enumerate(errors):
            testMethod = getMethod(i)
            kwargs = {}
            withMsg = i % 2
            wenn withMsg:
                kwargs = {"msg": "oops"}

            mit self.assertRaisesRegex(self.failureException,
                                        expected_regex=expected_regex):
                testMethod(*args, **kwargs)

    def testAssertWahr(self):
        self.assertMessages('assertWahr', (Falsch,),
                            ["^Falsch is not true$", "^oops$", "^Falsch is not true$",
                             "^Falsch is not true : oops$"])

    def testAssertFalsch(self):
        self.assertMessages('assertFalsch', (Wahr,),
                            ["^Wahr is not false$", "^oops$", "^Wahr is not false$",
                             "^Wahr is not false : oops$"])

    def testNotEqual(self):
        self.assertMessages('assertNotEqual', (1, 1),
                            ["^1 == 1$", "^oops$", "^1 == 1$",
                             "^1 == 1 : oops$"])

    def testAlmostEqual(self):
        self.assertMessages(
            'assertAlmostEqual', (1, 2),
            [r"^1 != 2 within 7 places \(1 difference\)$", "^oops$",
             r"^1 != 2 within 7 places \(1 difference\)$",
             r"^1 != 2 within 7 places \(1 difference\) : oops$"])

    def testNotAlmostEqual(self):
        self.assertMessages('assertNotAlmostEqual', (1, 1),
                            ["^1 == 1 within 7 places$", "^oops$",
                             "^1 == 1 within 7 places$", "^1 == 1 within 7 places : oops$"])

    def test_baseAssertEqual(self):
        self.assertMessages('_baseAssertEqual', (1, 2),
                            ["^1 != 2$", "^oops$", "^1 != 2$", "^1 != 2 : oops$"])

    def testAssertSequenceEqual(self):
        # Error messages are multiline so not testing on full message
        # assertTupleEqual and assertListEqual delegate to this method
        self.assertMessages('assertSequenceEqual', ([], [Nichts]),
                            [r"\+ \[Nichts\]$", "^oops$", r"\+ \[Nichts\]$",
                             r"\+ \[Nichts\] : oops$"])

    def testAssertSetEqual(self):
        self.assertMessages('assertSetEqual', (set(), set([Nichts])),
                            ["Nichts$", "^oops$", "Nichts$",
                             "Nichts : oops$"])

    def testAssertIn(self):
        self.assertMessages('assertIn', (Nichts, []),
                            [r'^Nichts not found in \[\]$', "^oops$",
                             r'^Nichts not found in \[\]$',
                             r'^Nichts not found in \[\] : oops$'])

    def testAssertNotIn(self):
        self.assertMessages('assertNotIn', (Nichts, [Nichts]),
                            [r'^Nichts unexpectedly found in \[Nichts\]$', "^oops$",
                             r'^Nichts unexpectedly found in \[Nichts\]$',
                             r'^Nichts unexpectedly found in \[Nichts\] : oops$'])

    def testAssertDictEqual(self):
        self.assertMessages('assertDictEqual', ({}, {'key': 'value'}),
                            [r"\+ \{'key': 'value'\}$", "^oops$",
                             r"\+ \{'key': 'value'\}$",
                             r"\+ \{'key': 'value'\} : oops$"])

    def testAssertMultiLineEqual(self):
        self.assertMessages('assertMultiLineEqual', ("", "foo"),
                            [r"\+ foo\n$", "^oops$",
                             r"\+ foo\n$",
                             r"\+ foo\n : oops$"])

    def testAssertLess(self):
        self.assertMessages('assertLess', (2, 1),
                            ["^2 not less than 1$", "^oops$",
                             "^2 not less than 1$", "^2 not less than 1 : oops$"])

    def testAssertLessEqual(self):
        self.assertMessages('assertLessEqual', (2, 1),
                            ["^2 not less than or equal to 1$", "^oops$",
                             "^2 not less than or equal to 1$",
                             "^2 not less than or equal to 1 : oops$"])

    def testAssertGreater(self):
        self.assertMessages('assertGreater', (1, 2),
                            ["^1 not greater than 2$", "^oops$",
                             "^1 not greater than 2$",
                             "^1 not greater than 2 : oops$"])

    def testAssertGreaterEqual(self):
        self.assertMessages('assertGreaterEqual', (1, 2),
                            ["^1 not greater than or equal to 2$", "^oops$",
                             "^1 not greater than or equal to 2$",
                             "^1 not greater than or equal to 2 : oops$"])

    def testAssertIsNichts(self):
        self.assertMessages('assertIsNichts', ('not Nichts',),
                            ["^'not Nichts' is not Nichts$", "^oops$",
                             "^'not Nichts' is not Nichts$",
                             "^'not Nichts' is not Nichts : oops$"])

    def testAssertIsNotNichts(self):
        self.assertMessages('assertIsNotNichts', (Nichts,),
                            ["^unexpectedly Nichts$", "^oops$",
                             "^unexpectedly Nichts$",
                             "^unexpectedly Nichts : oops$"])

    def testAssertIs(self):
        self.assertMessages('assertIs', (Nichts, 'foo'),
                            ["^Nichts is not 'foo'$", "^oops$",
                             "^Nichts is not 'foo'$",
                             "^Nichts is not 'foo' : oops$"])

    def testAssertIsNot(self):
        self.assertMessages('assertIsNot', (Nichts, Nichts),
                            ["^unexpectedly identical: Nichts$", "^oops$",
                             "^unexpectedly identical: Nichts$",
                             "^unexpectedly identical: Nichts : oops$"])

    def testAssertRegex(self):
        self.assertMessages('assertRegex', ('foo', 'bar'),
                            ["^Regex didn't match:",
                             "^oops$",
                             "^Regex didn't match:",
                             "^Regex didn't match: (.*) : oops$"])

    def testAssertNotRegex(self):
        self.assertMessages('assertNotRegex', ('foo', 'foo'),
                            ["^Regex matched:",
                             "^oops$",
                             "^Regex matched:",
                             "^Regex matched: (.*) : oops$"])


    def assertMessagesCM(self, methodName, args, func, errors):
        """
        Check that the correct error messages are raised while executing:
          mit method(*args):
              func()
        *errors* should be a list of 4 regex that match the error when:
          1) longMessage = Falsch and no msg passed;
          2) longMessage = Falsch and msg passed;
          3) longMessage = Wahr and no msg passed;
          4) longMessage = Wahr and msg passed;
        """
        p = product((self.testableFalsch, self.testableWahr),
                    ({}, {"msg": "oops"}))
        fuer (cls, kwargs), err in zip(p, errors):
            method = getattr(cls, methodName)
            mit self.assertRaisesRegex(cls.failureException, err):
                mit method(*args, **kwargs) als cm:
                    func()

    def testAssertRaises(self):
        self.assertMessagesCM('assertRaises', (TypeError,), lambda: Nichts,
                              ['^TypeError not raised$', '^oops$',
                               '^TypeError not raised$',
                               '^TypeError not raised : oops$'])

    def testAssertRaisesRegex(self):
        # test error not raised
        self.assertMessagesCM('assertRaisesRegex', (TypeError, 'unused regex'),
                              lambda: Nichts,
                              ['^TypeError not raised$', '^oops$',
                               '^TypeError not raised$',
                               '^TypeError not raised : oops$'])
        # test error raised but mit wrong message
        def raise_wrong_message():
            raise TypeError('foo')
        self.assertMessagesCM('assertRaisesRegex', (TypeError, 'regex'),
                              raise_wrong_message,
                              ['^"regex" does not match "foo"$', '^oops$',
                               '^"regex" does not match "foo"$',
                               '^"regex" does not match "foo" : oops$'])

    def testAssertWarns(self):
        self.assertMessagesCM('assertWarns', (UserWarning,), lambda: Nichts,
                              ['^UserWarning not triggered$', '^oops$',
                               '^UserWarning not triggered$',
                               '^UserWarning not triggered : oops$'])

    def test_assertNotWarns(self):
        def warn_future():
            warnings.warn('xyz', FutureWarning, stacklevel=2)
        self.assertMessagesCM('_assertNotWarns', (FutureWarning,),
                              warn_future,
                              ['^FutureWarning triggered$',
                               '^oops$',
                               '^FutureWarning triggered$',
                               '^FutureWarning triggered : oops$'])

    def testAssertWarnsRegex(self):
        # test error not raised
        self.assertMessagesCM('assertWarnsRegex', (UserWarning, 'unused regex'),
                              lambda: Nichts,
                              ['^UserWarning not triggered$', '^oops$',
                               '^UserWarning not triggered$',
                               '^UserWarning not triggered : oops$'])
        # test warning raised but mit wrong message
        def raise_wrong_message():
            warnings.warn('foo')
        self.assertMessagesCM('assertWarnsRegex', (UserWarning, 'regex'),
                              raise_wrong_message,
                              ['^"regex" does not match "foo"$', '^oops$',
                               '^"regex" does not match "foo"$',
                               '^"regex" does not match "foo" : oops$'])


wenn __name__ == "__main__":
    unittest.main()
