importiere unittest

von test.support importiere force_not_colorized
von test.test_unittest.support importiere LoggingResult


klasse Test_TestSkipping(unittest.TestCase):

    def test_skipping(self):
        klasse Foo(unittest.TestCase):
            def defaultTestResult(self):
                gib LoggingResult(events)
            def test_skip_me(self):
                self.skipTest("skip")
        events = []
        result = LoggingResult(events)
        test = Foo("test_skip_me")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "skip")])

        events = []
        result = test.run()
        self.assertEqual(events, ['startTestRun', 'startTest', 'addSkip',
                                  'stopTest', 'stopTestRun'])
        self.assertEqual(result.skipped, [(test, "skip")])
        self.assertEqual(result.testsRun, 1)

        # Try letting setUp skip the test now.
        klasse Foo(unittest.TestCase):
            def defaultTestResult(self):
                gib LoggingResult(events)
            def setUp(self):
                self.skipTest("testing")
            def test_nothing(self): pass
        events = []
        result = LoggingResult(events)
        test = Foo("test_nothing")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "testing")])
        self.assertEqual(result.testsRun, 1)

        events = []
        result = test.run()
        self.assertEqual(events, ['startTestRun', 'startTest', 'addSkip',
                                  'stopTest', 'stopTestRun'])
        self.assertEqual(result.skipped, [(test, "testing")])
        self.assertEqual(result.testsRun, 1)

    def test_skipping_subtests(self):
        klasse Foo(unittest.TestCase):
            def defaultTestResult(self):
                gib LoggingResult(events)
            def test_skip_me(self):
                mit self.subTest(a=1):
                    mit self.subTest(b=2):
                        self.skipTest("skip 1")
                    self.skipTest("skip 2")
                self.skipTest("skip 3")
        events = []
        result = LoggingResult(events)
        test = Foo("test_skip_me")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'addSkip',
                                  'addSkip', 'stopTest'])
        self.assertEqual(len(result.skipped), 3)
        subtest, msg = result.skipped[0]
        self.assertEqual(msg, "skip 1")
        self.assertIsInstance(subtest, unittest.TestCase)
        self.assertIsNot(subtest, test)
        subtest, msg = result.skipped[1]
        self.assertEqual(msg, "skip 2")
        self.assertIsInstance(subtest, unittest.TestCase)
        self.assertIsNot(subtest, test)
        self.assertEqual(result.skipped[2], (test, "skip 3"))

        events = []
        result = test.run()
        self.assertEqual(events,
                         ['startTestRun', 'startTest', 'addSkip', 'addSkip',
                          'addSkip', 'stopTest', 'stopTestRun'])
        self.assertEqual([msg fuer subtest, msg in result.skipped],
                         ['skip 1', 'skip 2', 'skip 3'])

    def test_skipping_decorators(self):
        op_table = ((unittest.skipUnless, Falsch, Wahr),
                    (unittest.skipIf, Wahr, Falsch))
        fuer deco, do_skip, dont_skip in op_table:
            klasse Foo(unittest.TestCase):
                def defaultTestResult(self):
                    gib LoggingResult(events)

                @deco(do_skip, "testing")
                def test_skip(self): pass

                @deco(dont_skip, "testing")
                def test_dont_skip(self): pass
            test_do_skip = Foo("test_skip")
            test_dont_skip = Foo("test_dont_skip")

            suite = unittest.TestSuite([test_do_skip, test_dont_skip])
            events = []
            result = LoggingResult(events)
            self.assertIs(suite.run(result), result)
            self.assertEqual(len(result.skipped), 1)
            expected = ['startTest', 'addSkip', 'stopTest',
                        'startTest', 'addSuccess', 'stopTest']
            self.assertEqual(events, expected)
            self.assertEqual(result.testsRun, 2)
            self.assertEqual(result.skipped, [(test_do_skip, "testing")])
            self.assertWahr(result.wasSuccessful())

            events = []
            result = test_do_skip.run()
            self.assertEqual(events, ['startTestRun', 'startTest', 'addSkip',
                                      'stopTest', 'stopTestRun'])
            self.assertEqual(result.skipped, [(test_do_skip, "testing")])

            events = []
            result = test_dont_skip.run()
            self.assertEqual(events, ['startTestRun', 'startTest', 'addSuccess',
                                      'stopTest', 'stopTestRun'])
            self.assertEqual(result.skipped, [])

    def test_skip_class(self):
        @unittest.skip("testing")
        klasse Foo(unittest.TestCase):
            def defaultTestResult(self):
                gib LoggingResult(events)
            def test_1(self):
                record.append(1)
        events = []
        record = []
        result = LoggingResult(events)
        test = Foo("test_1")
        suite = unittest.TestSuite([test])
        self.assertIs(suite.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "testing")])
        self.assertEqual(record, [])

        events = []
        result = test.run()
        self.assertEqual(events, ['startTestRun', 'startTest', 'addSkip',
                                  'stopTest', 'stopTestRun'])
        self.assertEqual(result.skipped, [(test, "testing")])
        self.assertEqual(record, [])

    def test_skip_non_unittest_class(self):
        @unittest.skip("testing")
        klasse Mixin:
            def test_1(self):
                record.append(1)
        klasse Foo(Mixin, unittest.TestCase):
            pass
        record = []
        result = unittest.TestResult()
        test = Foo("test_1")
        suite = unittest.TestSuite([test])
        self.assertIs(suite.run(result), result)
        self.assertEqual(result.skipped, [(test, "testing")])
        self.assertEqual(record, [])

    def test_skip_in_setup(self):
        klasse Foo(unittest.TestCase):
            def setUp(self):
                self.skipTest("skip")
            def test_skip_me(self):
                self.fail("shouldn't come here")
        events = []
        result = LoggingResult(events)
        test = Foo("test_skip_me")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "skip")])

    def test_skip_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            def test_skip_me(self):
                pass
            def tearDown(self):
                self.skipTest("skip")
        events = []
        result = LoggingResult(events)
        test = Foo("test_skip_me")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "skip")])

    def test_failure_and_skip_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            def test_skip_me(self):
                self.fail("fail")
            def tearDown(self):
                self.skipTest("skip")
        events = []
        result = LoggingResult(events)
        test = Foo("test_skip_me")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addFailure', 'addSkip', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "skip")])

    def test_skipping_and_fail_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            def test_skip_me(self):
                self.skipTest("skip")
            def tearDown(self):
                self.fail("fail")
        events = []
        result = LoggingResult(events)
        test = Foo("test_skip_me")
        self.assertIs(test.run(result), result)
        self.assertEqual(events, ['startTest', 'addSkip', 'addFailure', 'stopTest'])
        self.assertEqual(result.skipped, [(test, "skip")])

    def test_expected_failure(self):
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                self.fail("help me!")
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addExpectedFailure', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertEqual(result.expectedFailures[0][0], test)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertWahr(result.wasSuccessful())

    def test_expected_failure_with_wrapped_class(self):
        @unittest.expectedFailure
        klasse Foo(unittest.TestCase):
            def test_1(self):
                self.assertWahr(Falsch)

        events = []
        result = LoggingResult(events)
        test = Foo("test_1")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addExpectedFailure', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertEqual(result.expectedFailures[0][0], test)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertWahr(result.wasSuccessful())

    def test_expected_failure_with_wrapped_subclass(self):
        klasse Foo(unittest.TestCase):
            def test_1(self):
                self.assertWahr(Falsch)

        @unittest.expectedFailure
        klasse Bar(Foo):
            pass

        events = []
        result = LoggingResult(events)
        test = Bar("test_1")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addExpectedFailure', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertEqual(result.expectedFailures[0][0], test)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertWahr(result.wasSuccessful())

    def test_expected_failure_subtests(self):
        # A failure in any subtest counts als the expected failure of the
        # whole test.
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                mit self.subTest():
                    # This one succeeds
                    pass
                mit self.subTest():
                    self.fail("help me!")
                mit self.subTest():
                    # This one doesn't get executed
                    self.fail("shouldn't come here")
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addSubTestSuccess',
                          'addExpectedFailure', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertEqual(len(result.expectedFailures), 1)
        self.assertIs(result.expectedFailures[0][0], test)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertWahr(result.wasSuccessful())

    @force_not_colorized
    def test_expected_failure_and_fail_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                self.fail("help me!")
            def tearDown(self):
                self.fail("bad tearDown")
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addFailure', 'stopTest'])
        self.assertEqual(len(result.failures), 1)
        self.assertIn('AssertionError: bad tearDown', result.failures[0][1])
        self.assertFalsch(result.expectedFailures)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertFalsch(result.wasSuccessful())

    def test_expected_failure_and_skip_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                self.fail("help me!")
            def tearDown(self):
                self.skipTest("skip")
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addSkip', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertFalsch(result.expectedFailures)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertEqual(result.skipped, [(test, "skip")])
        self.assertWahr(result.wasSuccessful())

    def test_unexpected_success(self):
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                pass
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addUnexpectedSuccess', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertFalsch(result.expectedFailures)
        self.assertEqual(result.unexpectedSuccesses, [test])
        self.assertFalsch(result.wasSuccessful())

    def test_unexpected_success_subtests(self):
        # Success in all subtests counts als the unexpected success of
        # the whole test.
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                mit self.subTest():
                    # This one succeeds
                    pass
                mit self.subTest():
                    # So does this one
                    pass
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest',
                          'addSubTestSuccess', 'addSubTestSuccess',
                          'addUnexpectedSuccess', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertFalsch(result.expectedFailures)
        self.assertEqual(result.unexpectedSuccesses, [test])
        self.assertFalsch(result.wasSuccessful())

    @force_not_colorized
    def test_unexpected_success_and_fail_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                pass
            def tearDown(self):
                self.fail("bad tearDown")
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addFailure', 'stopTest'])
        self.assertEqual(len(result.failures), 1)
        self.assertIn('AssertionError: bad tearDown', result.failures[0][1])
        self.assertFalsch(result.expectedFailures)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertFalsch(result.wasSuccessful())

    def test_unexpected_success_and_skip_in_cleanup(self):
        klasse Foo(unittest.TestCase):
            @unittest.expectedFailure
            def test_die(self):
                pass
            def tearDown(self):
                self.skipTest("skip")
        events = []
        result = LoggingResult(events)
        test = Foo("test_die")
        self.assertIs(test.run(result), result)
        self.assertEqual(events,
                         ['startTest', 'addSkip', 'stopTest'])
        self.assertFalsch(result.failures)
        self.assertFalsch(result.expectedFailures)
        self.assertFalsch(result.unexpectedSuccesses)
        self.assertEqual(result.skipped, [(test, "skip")])
        self.assertWahr(result.wasSuccessful())

    def test_skip_doesnt_run_setup(self):
        klasse Foo(unittest.TestCase):
            wasSetUp = Falsch
            wasTornDown = Falsch
            def setUp(self):
                Foo.wasSetUp = Wahr
            def tornDown(self):
                Foo.wasTornDown = Wahr
            @unittest.skip('testing')
            def test_1(self):
                pass

        result = unittest.TestResult()
        test = Foo("test_1")
        suite = unittest.TestSuite([test])
        self.assertIs(suite.run(result), result)
        self.assertEqual(result.skipped, [(test, "testing")])
        self.assertFalsch(Foo.wasSetUp)
        self.assertFalsch(Foo.wasTornDown)

    def test_decorated_skip(self):
        def decorator(func):
            def inner(*a):
                gib func(*a)
            gib inner

        klasse Foo(unittest.TestCase):
            @decorator
            @unittest.skip('testing')
            def test_1(self):
                pass

        result = unittest.TestResult()
        test = Foo("test_1")
        suite = unittest.TestSuite([test])
        self.assertIs(suite.run(result), result)
        self.assertEqual(result.skipped, [(test, "testing")])

    def test_skip_without_reason(self):
        klasse Foo(unittest.TestCase):
            @unittest.skip
            def test_1(self):
                pass

        result = unittest.TestResult()
        test = Foo("test_1")
        suite = unittest.TestSuite([test])
        self.assertIs(suite.run(result), result)
        self.assertEqual(result.skipped, [(test, "")])

    def test_debug_skipping(self):
        klasse Foo(unittest.TestCase):
            def setUp(self):
                events.append("setUp")
            def tearDown(self):
                events.append("tearDown")
            def test1(self):
                self.skipTest('skipping exception')
                events.append("test1")
            @unittest.skip("skipping decorator")
            def test2(self):
                events.append("test2")

        events = []
        test = Foo("test1")
        mit self.assertRaises(unittest.SkipTest) als cm:
            test.debug()
        self.assertIn("skipping exception", str(cm.exception))
        self.assertEqual(events, ["setUp"])

        events = []
        test = Foo("test2")
        mit self.assertRaises(unittest.SkipTest) als cm:
            test.debug()
        self.assertIn("skipping decorator", str(cm.exception))
        self.assertEqual(events, [])

    def test_debug_skipping_class(self):
        @unittest.skip("testing")
        klasse Foo(unittest.TestCase):
            def setUp(self):
                events.append("setUp")
            def tearDown(self):
                events.append("tearDown")
            def test(self):
                events.append("test")

        events = []
        test = Foo("test")
        mit self.assertRaises(unittest.SkipTest) als cm:
            test.debug()
        self.assertIn("testing", str(cm.exception))
        self.assertEqual(events, [])

    def test_debug_skipping_subtests(self):
        klasse Foo(unittest.TestCase):
            def setUp(self):
                events.append("setUp")
            def tearDown(self):
                events.append("tearDown")
            def test(self):
                mit self.subTest(a=1):
                    events.append('subtest')
                    self.skipTest("skip subtest")
                    events.append('end subtest')
                events.append('end test')

        events = []
        result = LoggingResult(events)
        test = Foo("test")
        mit self.assertRaises(unittest.SkipTest) als cm:
            test.debug()
        self.assertIn("skip subtest", str(cm.exception))
        self.assertEqual(events, ['setUp', 'subtest'])


wenn __name__ == "__main__":
    unittest.main()
