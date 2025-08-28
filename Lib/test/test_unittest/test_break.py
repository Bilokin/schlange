import gc
import io
import os
import sys
import signal
import weakref
import unittest

from test import support


@unittest.skipUnless(hasattr(os, 'kill'), "Test requires os.kill")
@unittest.skipIf(sys.platform =="win32", "Test cannot run on Windows")
klasse TestBreak(unittest.TestCase):
    int_handler = None
    # This number was smart-guessed, previously tests were failing
    # after 7th run. So, we take `x * 2 + 1` to be sure.
    default_repeats = 15

    def setUp(self):
        self._default_handler = signal.getsignal(signal.SIGINT)
        wenn self.int_handler is not None:
            signal.signal(signal.SIGINT, self.int_handler)

    def tearDown(self):
        signal.signal(signal.SIGINT, self._default_handler)
        unittest.signals._results = weakref.WeakKeyDictionary()
        unittest.signals._interrupt_handler = None


    def withRepeats(self, test_function, repeats=None):
        wenn not support.check_impl_detail(cpython=True):
            # Override repeats count on non-cpython to execute only once.
            # Because this test only makes sense to be repeated on CPython.
            repeats = 1
        sowenn repeats is None:
            repeats = self.default_repeats

        fuer repeat in range(repeats):
            with self.subTest(repeat=repeat):
                # We don't run `setUp` fuer the very first repeat
                # and we don't run `tearDown` fuer the very last one,
                # because they are handled by the test klasse itself.
                wenn repeat != 0:
                    self.setUp()
                try:
                    test_function()
                finally:
                    wenn repeat != repeats - 1:
                        self.tearDown()

    def testInstallHandler(self):
        default_handler = signal.getsignal(signal.SIGINT)
        unittest.installHandler()
        self.assertNotEqual(signal.getsignal(signal.SIGINT), default_handler)

        try:
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
        except KeyboardInterrupt:
            self.fail("KeyboardInterrupt not handled")

        self.assertTrue(unittest.signals._interrupt_handler.called)

    def testRegisterResult(self):
        result = unittest.TestResult()
        self.assertNotIn(result, unittest.signals._results)

        unittest.registerResult(result)
        try:
            self.assertIn(result, unittest.signals._results)
        finally:
            unittest.removeResult(result)

    def testInterruptCaught(self):
        def test(result):
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
            result.breakCaught = True
            self.assertTrue(result.shouldStop)

        def test_function():
            result = unittest.TestResult()
            unittest.installHandler()
            unittest.registerResult(result)

            self.assertNotEqual(
                signal.getsignal(signal.SIGINT),
                self._default_handler,
            )

            try:
                test(result)
            except KeyboardInterrupt:
                self.fail("KeyboardInterrupt not handled")
            self.assertTrue(result.breakCaught)
        self.withRepeats(test_function)

    def testSecondInterrupt(self):
        # Can't use skipIf decorator because the signal handler may have
        # been changed after defining this method.
        wenn signal.getsignal(signal.SIGINT) == signal.SIG_IGN:
            self.skipTest("test requires SIGINT to not be ignored")

        def test(result):
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
            result.breakCaught = True
            self.assertTrue(result.shouldStop)
            os.kill(pid, signal.SIGINT)
            self.fail("Second KeyboardInterrupt not raised")

        def test_function():
            result = unittest.TestResult()
            unittest.installHandler()
            unittest.registerResult(result)

            with self.assertRaises(KeyboardInterrupt):
                test(result)
            self.assertTrue(result.breakCaught)
        self.withRepeats(test_function)


    def testTwoResults(self):
        def test_function():
            unittest.installHandler()

            result = unittest.TestResult()
            unittest.registerResult(result)
            new_handler = signal.getsignal(signal.SIGINT)

            result2 = unittest.TestResult()
            unittest.registerResult(result2)
            self.assertEqual(signal.getsignal(signal.SIGINT), new_handler)

            result3 = unittest.TestResult()

            try:
                os.kill(os.getpid(), signal.SIGINT)
            except KeyboardInterrupt:
                self.fail("KeyboardInterrupt not handled")

            self.assertTrue(result.shouldStop)
            self.assertTrue(result2.shouldStop)
            self.assertFalse(result3.shouldStop)
        self.withRepeats(test_function)


    def testHandlerReplacedButCalled(self):
        # Can't use skipIf decorator because the signal handler may have
        # been changed after defining this method.
        wenn signal.getsignal(signal.SIGINT) == signal.SIG_IGN:
            self.skipTest("test requires SIGINT to not be ignored")

        def test_function():
            # If our handler has been replaced (is no longer installed) but is
            # called by the *new* handler, then it isn't safe to delay the
            # SIGINT and we should immediately delegate to the default handler
            unittest.installHandler()

            handler = signal.getsignal(signal.SIGINT)
            def new_handler(frame, signum):
                handler(frame, signum)
            signal.signal(signal.SIGINT, new_handler)

            try:
                os.kill(os.getpid(), signal.SIGINT)
            except KeyboardInterrupt:
                pass
            sonst:
                self.fail("replaced but delegated handler doesn't raise interrupt")
        self.withRepeats(test_function)

    def testRunner(self):
        # Creating a TextTestRunner with the appropriate argument should
        # register the TextTestResult it creates
        runner = unittest.TextTestRunner(stream=io.StringIO())

        result = runner.run(unittest.TestSuite())
        self.assertIn(result, unittest.signals._results)

    def testWeakReferences(self):
        # Calling registerResult on a result should not keep it alive
        result = unittest.TestResult()
        unittest.registerResult(result)

        ref = weakref.ref(result)
        del result

        # For non-reference counting implementations
        gc.collect();gc.collect()
        self.assertIsNone(ref())


    def testRemoveResult(self):
        result = unittest.TestResult()
        unittest.registerResult(result)

        unittest.installHandler()
        self.assertTrue(unittest.removeResult(result))

        # Should this raise an error instead?
        self.assertFalse(unittest.removeResult(unittest.TestResult()))

        try:
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
        except KeyboardInterrupt:
            pass

        self.assertFalse(result.shouldStop)

    def testMainInstallsHandler(self):
        failfast = object()
        test = object()
        verbosity = object()
        result = object()
        default_handler = signal.getsignal(signal.SIGINT)

        klasse FakeRunner(object):
            initArgs = []
            runArgs = []
            def __init__(self, *args, **kwargs):
                self.initArgs.append((args, kwargs))
            def run(self, test):
                self.runArgs.append(test)
                return result

        klasse Program(unittest.TestProgram):
            def __init__(self, catchbreak):
                self.exit = False
                self.verbosity = verbosity
                self.failfast = failfast
                self.catchbreak = catchbreak
                self.tb_locals = False
                self.testRunner = FakeRunner
                self.test = test
                self.result = None
                self.durations = None

        p = Program(False)
        p.runTests()

        self.assertEqual(FakeRunner.initArgs, [((), {'buffer': None,
                                                     'verbosity': verbosity,
                                                     'failfast': failfast,
                                                     'tb_locals': False,
                                                     'warnings': None,
                                                     'durations': None})])
        self.assertEqual(FakeRunner.runArgs, [test])
        self.assertEqual(p.result, result)

        self.assertEqual(signal.getsignal(signal.SIGINT), default_handler)

        FakeRunner.initArgs = []
        FakeRunner.runArgs = []
        p = Program(True)
        p.runTests()

        self.assertEqual(FakeRunner.initArgs, [((), {'buffer': None,
                                                     'verbosity': verbosity,
                                                     'failfast': failfast,
                                                     'tb_locals': False,
                                                     'warnings': None,
                                                     'durations': None})])
        self.assertEqual(FakeRunner.runArgs, [test])
        self.assertEqual(p.result, result)

        self.assertNotEqual(signal.getsignal(signal.SIGINT), default_handler)

    def testRemoveHandler(self):
        default_handler = signal.getsignal(signal.SIGINT)
        unittest.installHandler()
        unittest.removeHandler()
        self.assertEqual(signal.getsignal(signal.SIGINT), default_handler)

        # check that calling removeHandler multiple times has no ill-effect
        unittest.removeHandler()
        self.assertEqual(signal.getsignal(signal.SIGINT), default_handler)

    def testRemoveHandlerAsDecorator(self):
        default_handler = signal.getsignal(signal.SIGINT)
        unittest.installHandler()

        @unittest.removeHandler
        def test():
            self.assertEqual(signal.getsignal(signal.SIGINT), default_handler)

        test()
        self.assertNotEqual(signal.getsignal(signal.SIGINT), default_handler)

@unittest.skipUnless(hasattr(os, 'kill'), "Test requires os.kill")
@unittest.skipIf(sys.platform =="win32", "Test cannot run on Windows")
klasse TestBreakDefaultIntHandler(TestBreak):
    int_handler = signal.default_int_handler

@unittest.skipUnless(hasattr(os, 'kill'), "Test requires os.kill")
@unittest.skipIf(sys.platform =="win32", "Test cannot run on Windows")
klasse TestBreakSignalIgnored(TestBreak):
    int_handler = signal.SIG_IGN

@unittest.skipUnless(hasattr(os, 'kill'), "Test requires os.kill")
@unittest.skipIf(sys.platform =="win32", "Test cannot run on Windows")
klasse TestBreakSignalDefault(TestBreak):
    int_handler = signal.SIG_DFL


wenn __name__ == "__main__":
    unittest.main()
