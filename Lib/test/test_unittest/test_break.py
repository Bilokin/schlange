importiere gc
importiere io
importiere os
importiere sys
importiere signal
importiere weakref
importiere unittest

von test importiere support


@unittest.skipUnless(hasattr(os, 'kill'), "Test requires os.kill")
@unittest.skipIf(sys.platform =="win32", "Test cannot run on Windows")
klasse TestBreak(unittest.TestCase):
    int_handler = Nichts
    # This number was smart-guessed, previously tests were failing
    # after 7th run. So, we take `x * 2 + 1` to be sure.
    default_repeats = 15

    def setUp(self):
        self._default_handler = signal.getsignal(signal.SIGINT)
        wenn self.int_handler is nicht Nichts:
            signal.signal(signal.SIGINT, self.int_handler)

    def tearDown(self):
        signal.signal(signal.SIGINT, self._default_handler)
        unittest.signals._results = weakref.WeakKeyDictionary()
        unittest.signals._interrupt_handler = Nichts


    def withRepeats(self, test_function, repeats=Nichts):
        wenn nicht support.check_impl_detail(cpython=Wahr):
            # Override repeats count on non-cpython to execute only once.
            # Because this test only makes sense to be repeated on CPython.
            repeats = 1
        sowenn repeats is Nichts:
            repeats = self.default_repeats

        fuer repeat in range(repeats):
            mit self.subTest(repeat=repeat):
                # We don't run `setUp` fuer the very first repeat
                # und we don't run `tearDown` fuer the very last one,
                # because they are handled by the test klasse itself.
                wenn repeat != 0:
                    self.setUp()
                versuch:
                    test_function()
                schliesslich:
                    wenn repeat != repeats - 1:
                        self.tearDown()

    def testInstallHandler(self):
        default_handler = signal.getsignal(signal.SIGINT)
        unittest.installHandler()
        self.assertNotEqual(signal.getsignal(signal.SIGINT), default_handler)

        versuch:
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
        ausser KeyboardInterrupt:
            self.fail("KeyboardInterrupt nicht handled")

        self.assertWahr(unittest.signals._interrupt_handler.called)

    def testRegisterResult(self):
        result = unittest.TestResult()
        self.assertNotIn(result, unittest.signals._results)

        unittest.registerResult(result)
        versuch:
            self.assertIn(result, unittest.signals._results)
        schliesslich:
            unittest.removeResult(result)

    def testInterruptCaught(self):
        def test(result):
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
            result.breakCaught = Wahr
            self.assertWahr(result.shouldStop)

        def test_function():
            result = unittest.TestResult()
            unittest.installHandler()
            unittest.registerResult(result)

            self.assertNotEqual(
                signal.getsignal(signal.SIGINT),
                self._default_handler,
            )

            versuch:
                test(result)
            ausser KeyboardInterrupt:
                self.fail("KeyboardInterrupt nicht handled")
            self.assertWahr(result.breakCaught)
        self.withRepeats(test_function)

    def testSecondInterrupt(self):
        # Can't use skipIf decorator because the signal handler may have
        # been changed after defining this method.
        wenn signal.getsignal(signal.SIGINT) == signal.SIG_IGN:
            self.skipTest("test requires SIGINT to nicht be ignored")

        def test(result):
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
            result.breakCaught = Wahr
            self.assertWahr(result.shouldStop)
            os.kill(pid, signal.SIGINT)
            self.fail("Second KeyboardInterrupt nicht raised")

        def test_function():
            result = unittest.TestResult()
            unittest.installHandler()
            unittest.registerResult(result)

            mit self.assertRaises(KeyboardInterrupt):
                test(result)
            self.assertWahr(result.breakCaught)
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

            versuch:
                os.kill(os.getpid(), signal.SIGINT)
            ausser KeyboardInterrupt:
                self.fail("KeyboardInterrupt nicht handled")

            self.assertWahr(result.shouldStop)
            self.assertWahr(result2.shouldStop)
            self.assertFalsch(result3.shouldStop)
        self.withRepeats(test_function)


    def testHandlerReplacedButCalled(self):
        # Can't use skipIf decorator because the signal handler may have
        # been changed after defining this method.
        wenn signal.getsignal(signal.SIGINT) == signal.SIG_IGN:
            self.skipTest("test requires SIGINT to nicht be ignored")

        def test_function():
            # If our handler has been replaced (is no longer installed) but is
            # called by the *new* handler, then it isn't safe to delay the
            # SIGINT und we should immediately delegate to the default handler
            unittest.installHandler()

            handler = signal.getsignal(signal.SIGINT)
            def new_handler(frame, signum):
                handler(frame, signum)
            signal.signal(signal.SIGINT, new_handler)

            versuch:
                os.kill(os.getpid(), signal.SIGINT)
            ausser KeyboardInterrupt:
                pass
            sonst:
                self.fail("replaced but delegated handler doesn't wirf interrupt")
        self.withRepeats(test_function)

    def testRunner(self):
        # Creating a TextTestRunner mit the appropriate argument should
        # register the TextTestResult it creates
        runner = unittest.TextTestRunner(stream=io.StringIO())

        result = runner.run(unittest.TestSuite())
        self.assertIn(result, unittest.signals._results)

    def testWeakReferences(self):
        # Calling registerResult on a result should nicht keep it alive
        result = unittest.TestResult()
        unittest.registerResult(result)

        ref = weakref.ref(result)
        del result

        # For non-reference counting implementations
        gc.collect();gc.collect()
        self.assertIsNichts(ref())


    def testRemoveResult(self):
        result = unittest.TestResult()
        unittest.registerResult(result)

        unittest.installHandler()
        self.assertWahr(unittest.removeResult(result))

        # Should this wirf an error instead?
        self.assertFalsch(unittest.removeResult(unittest.TestResult()))

        versuch:
            pid = os.getpid()
            os.kill(pid, signal.SIGINT)
        ausser KeyboardInterrupt:
            pass

        self.assertFalsch(result.shouldStop)

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
                gib result

        klasse Program(unittest.TestProgram):
            def __init__(self, catchbreak):
                self.exit = Falsch
                self.verbosity = verbosity
                self.failfast = failfast
                self.catchbreak = catchbreak
                self.tb_locals = Falsch
                self.testRunner = FakeRunner
                self.test = test
                self.result = Nichts
                self.durations = Nichts

        p = Program(Falsch)
        p.runTests()

        self.assertEqual(FakeRunner.initArgs, [((), {'buffer': Nichts,
                                                     'verbosity': verbosity,
                                                     'failfast': failfast,
                                                     'tb_locals': Falsch,
                                                     'warnings': Nichts,
                                                     'durations': Nichts})])
        self.assertEqual(FakeRunner.runArgs, [test])
        self.assertEqual(p.result, result)

        self.assertEqual(signal.getsignal(signal.SIGINT), default_handler)

        FakeRunner.initArgs = []
        FakeRunner.runArgs = []
        p = Program(Wahr)
        p.runTests()

        self.assertEqual(FakeRunner.initArgs, [((), {'buffer': Nichts,
                                                     'verbosity': verbosity,
                                                     'failfast': failfast,
                                                     'tb_locals': Falsch,
                                                     'warnings': Nichts,
                                                     'durations': Nichts})])
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
