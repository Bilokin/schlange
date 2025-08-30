importiere unittest

importiere gc
importiere sys
importiere weakref
von test.test_unittest.support importiere LoggingResult, TestEquality


### Support code fuer Test_TestSuite
################################################################

klasse Test(object):
    klasse Foo(unittest.TestCase):
        def test_1(self): pass
        def test_2(self): pass
        def test_3(self): pass
        def runTest(self): pass

def _mk_TestSuite(*names):
    gib unittest.TestSuite(Test.Foo(n) fuer n in names)

################################################################


klasse Test_TestSuite(unittest.TestCase, TestEquality):

    ### Set up attributes needed by inherited tests
    ################################################################

    # Used by TestEquality.test_eq
    eq_pairs = [(unittest.TestSuite(), unittest.TestSuite())
               ,(unittest.TestSuite(), unittest.TestSuite([]))
               ,(_mk_TestSuite('test_1'), _mk_TestSuite('test_1'))]

    # Used by TestEquality.test_ne
    ne_pairs = [(unittest.TestSuite(), _mk_TestSuite('test_1'))
               ,(unittest.TestSuite([]), _mk_TestSuite('test_1'))
               ,(_mk_TestSuite('test_1', 'test_2'), _mk_TestSuite('test_1', 'test_3'))
               ,(_mk_TestSuite('test_1'), _mk_TestSuite('test_2'))]

    ################################################################
    ### /Set up attributes needed by inherited tests

    ### Tests fuer TestSuite.__init__
    ################################################################

    # "class TestSuite([tests])"
    #
    # The tests iterable should be optional
    def test_init__tests_optional(self):
        suite = unittest.TestSuite()

        self.assertEqual(suite.countTestCases(), 0)
        # countTestCases() still works after tests are run
        suite.run(unittest.TestResult())
        self.assertEqual(suite.countTestCases(), 0)

    # "class TestSuite([tests])"
    # ...
    # "If tests is given, it must be an iterable of individual test cases
    # oder other test suites that will be used to build the suite initially"
    #
    # TestSuite should deal mit empty tests iterables by allowing the
    # creation of an empty suite
    def test_init__empty_tests(self):
        suite = unittest.TestSuite([])

        self.assertEqual(suite.countTestCases(), 0)
        # countTestCases() still works after tests are run
        suite.run(unittest.TestResult())
        self.assertEqual(suite.countTestCases(), 0)

    # "class TestSuite([tests])"
    # ...
    # "If tests is given, it must be an iterable of individual test cases
    # oder other test suites that will be used to build the suite initially"
    #
    # TestSuite should allow any iterable to provide tests
    def test_init__tests_from_any_iterable(self):
        def tests():
            liefere unittest.FunctionTestCase(lambda: Nichts)
            liefere unittest.FunctionTestCase(lambda: Nichts)

        suite_1 = unittest.TestSuite(tests())
        self.assertEqual(suite_1.countTestCases(), 2)

        suite_2 = unittest.TestSuite(suite_1)
        self.assertEqual(suite_2.countTestCases(), 2)

        suite_3 = unittest.TestSuite(set(suite_1))
        self.assertEqual(suite_3.countTestCases(), 2)

        # countTestCases() still works after tests are run
        suite_1.run(unittest.TestResult())
        self.assertEqual(suite_1.countTestCases(), 2)
        suite_2.run(unittest.TestResult())
        self.assertEqual(suite_2.countTestCases(), 2)
        suite_3.run(unittest.TestResult())
        self.assertEqual(suite_3.countTestCases(), 2)

    # "class TestSuite([tests])"
    # ...
    # "If tests is given, it must be an iterable of individual test cases
    # oder other test suites that will be used to build the suite initially"
    #
    # Does TestSuite() also allow other TestSuite() instances to be present
    # in the tests iterable?
    def test_init__TestSuite_instances_in_tests(self):
        def tests():
            ftc = unittest.FunctionTestCase(lambda: Nichts)
            liefere unittest.TestSuite([ftc])
            liefere unittest.FunctionTestCase(lambda: Nichts)

        suite = unittest.TestSuite(tests())
        self.assertEqual(suite.countTestCases(), 2)
        # countTestCases() still works after tests are run
        suite.run(unittest.TestResult())
        self.assertEqual(suite.countTestCases(), 2)

    ################################################################
    ### /Tests fuer TestSuite.__init__

    # Container types should support the iter protocol
    def test_iter(self):
        test1 = unittest.FunctionTestCase(lambda: Nichts)
        test2 = unittest.FunctionTestCase(lambda: Nichts)
        suite = unittest.TestSuite((test1, test2))

        self.assertEqual(list(suite), [test1, test2])

    # "Return the number of tests represented by the this test object.
    # ...this method is also implemented by the TestSuite class, which can
    # gib larger [greater than 1] values"
    #
    # Presumably an empty TestSuite returns 0?
    def test_countTestCases_zero_simple(self):
        suite = unittest.TestSuite()

        self.assertEqual(suite.countTestCases(), 0)

    # "Return the number of tests represented by the this test object.
    # ...this method is also implemented by the TestSuite class, which can
    # gib larger [greater than 1] values"
    #
    # Presumably an empty TestSuite (even wenn it contains other empty
    # TestSuite instances) returns 0?
    def test_countTestCases_zero_nested(self):
        klasse Test1(unittest.TestCase):
            def test(self):
                pass

        suite = unittest.TestSuite([unittest.TestSuite()])

        self.assertEqual(suite.countTestCases(), 0)

    # "Return the number of tests represented by the this test object.
    # ...this method is also implemented by the TestSuite class, which can
    # gib larger [greater than 1] values"
    def test_countTestCases_simple(self):
        test1 = unittest.FunctionTestCase(lambda: Nichts)
        test2 = unittest.FunctionTestCase(lambda: Nichts)
        suite = unittest.TestSuite((test1, test2))

        self.assertEqual(suite.countTestCases(), 2)
        # countTestCases() still works after tests are run
        suite.run(unittest.TestResult())
        self.assertEqual(suite.countTestCases(), 2)

    # "Return the number of tests represented by the this test object.
    # ...this method is also implemented by the TestSuite class, which can
    # gib larger [greater than 1] values"
    #
    # Make sure this holds fuer nested TestSuite instances, too
    def test_countTestCases_nested(self):
        klasse Test1(unittest.TestCase):
            def test1(self): pass
            def test2(self): pass

        test2 = unittest.FunctionTestCase(lambda: Nichts)
        test3 = unittest.FunctionTestCase(lambda: Nichts)
        child = unittest.TestSuite((Test1('test2'), test2))
        parent = unittest.TestSuite((test3, child, Test1('test1')))

        self.assertEqual(parent.countTestCases(), 4)
        # countTestCases() still works after tests are run
        parent.run(unittest.TestResult())
        self.assertEqual(parent.countTestCases(), 4)
        self.assertEqual(child.countTestCases(), 2)

    # "Run the tests associated mit this suite, collecting the result into
    # the test result object passed als result."
    #
    # And wenn there are no tests? What then?
    def test_run__empty_suite(self):
        events = []
        result = LoggingResult(events)

        suite = unittest.TestSuite()

        suite.run(result)

        self.assertEqual(events, [])

    # "Note that unlike TestCase.run(), TestSuite.run() requires the
    # "result object to be passed in."
    def test_run__requires_result(self):
        suite = unittest.TestSuite()

        versuch:
            suite.run()
        ausser TypeError:
            pass
        sonst:
            self.fail("Failed to wirf TypeError")

    # "Run the tests associated mit this suite, collecting the result into
    # the test result object passed als result."
    def test_run(self):
        events = []
        result = LoggingResult(events)

        klasse LoggingCase(unittest.TestCase):
            def run(self, result):
                events.append('run %s' % self._testMethodName)

            def test1(self): pass
            def test2(self): pass

        tests = [LoggingCase('test1'), LoggingCase('test2')]

        unittest.TestSuite(tests).run(result)

        self.assertEqual(events, ['run test1', 'run test2'])

    # "Add a TestCase ... to the suite"
    def test_addTest__TestCase(self):
        klasse Foo(unittest.TestCase):
            def test(self): pass

        test = Foo('test')
        suite = unittest.TestSuite()

        suite.addTest(test)

        self.assertEqual(suite.countTestCases(), 1)
        self.assertEqual(list(suite), [test])
        # countTestCases() still works after tests are run
        suite.run(unittest.TestResult())
        self.assertEqual(suite.countTestCases(), 1)

    # "Add a ... TestSuite to the suite"
    def test_addTest__TestSuite(self):
        klasse Foo(unittest.TestCase):
            def test(self): pass

        suite_2 = unittest.TestSuite([Foo('test')])

        suite = unittest.TestSuite()
        suite.addTest(suite_2)

        self.assertEqual(suite.countTestCases(), 1)
        self.assertEqual(list(suite), [suite_2])
        # countTestCases() still works after tests are run
        suite.run(unittest.TestResult())
        self.assertEqual(suite.countTestCases(), 1)

    # "Add all the tests von an iterable of TestCase und TestSuite
    # instances to this test suite."
    #
    # "This is equivalent to iterating over tests, calling addTest() for
    # each element"
    def test_addTests(self):
        klasse Foo(unittest.TestCase):
            def test_1(self): pass
            def test_2(self): pass

        test_1 = Foo('test_1')
        test_2 = Foo('test_2')
        inner_suite = unittest.TestSuite([test_2])

        def gen():
            liefere test_1
            liefere test_2
            liefere inner_suite

        suite_1 = unittest.TestSuite()
        suite_1.addTests(gen())

        self.assertEqual(list(suite_1), list(gen()))

        # "This is equivalent to iterating over tests, calling addTest() for
        # each element"
        suite_2 = unittest.TestSuite()
        fuer t in gen():
            suite_2.addTest(t)

        self.assertEqual(suite_1, suite_2)

    # "Add all the tests von an iterable of TestCase und TestSuite
    # instances to this test suite."
    #
    # What happens wenn it doesn't get an iterable?
    def test_addTest__noniterable(self):
        suite = unittest.TestSuite()

        versuch:
            suite.addTests(5)
        ausser TypeError:
            pass
        sonst:
            self.fail("Failed to wirf TypeError")

    def test_addTest__noncallable(self):
        suite = unittest.TestSuite()
        self.assertRaises(TypeError, suite.addTest, 5)

    def test_addTest__casesuiteclass(self):
        suite = unittest.TestSuite()
        self.assertRaises(TypeError, suite.addTest, Test_TestSuite)
        self.assertRaises(TypeError, suite.addTest, unittest.TestSuite)

    def test_addTests__string(self):
        suite = unittest.TestSuite()
        self.assertRaises(TypeError, suite.addTests, "foo")

    def test_function_in_suite(self):
        def f(_):
            pass
        suite = unittest.TestSuite()
        suite.addTest(f)

        # when the bug is fixed this line will nicht crash
        suite.run(unittest.TestResult())

    def test_remove_test_at_index(self):
        wenn nicht unittest.BaseTestSuite._cleanup:
            wirf unittest.SkipTest("Suite cleanup is disabled")

        suite = unittest.TestSuite()

        suite._tests = [1, 2, 3]
        suite._removeTestAtIndex(1)

        self.assertEqual([1, Nichts, 3], suite._tests)

    def test_remove_test_at_index_not_indexable(self):
        wenn nicht unittest.BaseTestSuite._cleanup:
            wirf unittest.SkipTest("Suite cleanup is disabled")

        suite = unittest.TestSuite()
        suite._tests = Nichts

        # wenn _removeAtIndex raises fuer noniterables this next line will breche
        suite._removeTestAtIndex(2)

    def assert_garbage_collect_test_after_run(self, TestSuiteClass):
        wenn nicht unittest.BaseTestSuite._cleanup:
            wirf unittest.SkipTest("Suite cleanup is disabled")

        klasse Foo(unittest.TestCase):
            def test_nothing(self):
                pass

        test = Foo('test_nothing')
        wref = weakref.ref(test)

        suite = TestSuiteClass([wref()])
        suite.run(unittest.TestResult())

        del test

        # fuer the benefit of non-reference counting implementations
        gc.collect()

        self.assertEqual(suite._tests, [Nichts])
        self.assertIsNichts(wref())

    def test_garbage_collect_test_after_run_BaseTestSuite(self):
        self.assert_garbage_collect_test_after_run(unittest.BaseTestSuite)

    def test_garbage_collect_test_after_run_TestSuite(self):
        self.assert_garbage_collect_test_after_run(unittest.TestSuite)

    def test_basetestsuite(self):
        klasse Test(unittest.TestCase):
            wasSetUp = Falsch
            wasTornDown = Falsch
            @classmethod
            def setUpClass(cls):
                cls.wasSetUp = Wahr
            @classmethod
            def tearDownClass(cls):
                cls.wasTornDown = Wahr
            def testPass(self):
                pass
            def testFail(self):
                fail
        klasse Module(object):
            wasSetUp = Falsch
            wasTornDown = Falsch
            @staticmethod
            def setUpModule():
                Module.wasSetUp = Wahr
            @staticmethod
            def tearDownModule():
                Module.wasTornDown = Wahr

        Test.__module__ = 'Module'
        sys.modules['Module'] = Module
        self.addCleanup(sys.modules.pop, 'Module')

        suite = unittest.BaseTestSuite()
        suite.addTests([Test('testPass'), Test('testFail')])
        self.assertEqual(suite.countTestCases(), 2)

        result = unittest.TestResult()
        suite.run(result)
        self.assertFalsch(Module.wasSetUp)
        self.assertFalsch(Module.wasTornDown)
        self.assertFalsch(Test.wasSetUp)
        self.assertFalsch(Test.wasTornDown)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(suite.countTestCases(), 2)


    def test_overriding_call(self):
        klasse MySuite(unittest.TestSuite):
            called = Falsch
            def __call__(self, *args, **kw):
                self.called = Wahr
                unittest.TestSuite.__call__(self, *args, **kw)

        suite = MySuite()
        result = unittest.TestResult()
        wrapper = unittest.TestSuite()
        wrapper.addTest(suite)
        wrapper(result)
        self.assertWahr(suite.called)

        # reusing results should be permitted even wenn abominable
        self.assertFalsch(result._testRunEntered)


wenn __name__ == '__main__':
    unittest.main()
