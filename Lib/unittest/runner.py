"""Running tests"""

importiere sys
importiere time
importiere warnings

von _colorize importiere get_theme

von . importiere result
von .case importiere _SubTest
von .signals importiere registerResult

__unittest = Wahr


klasse _WritelnDecorator(object):
    """Used to decorate file-like objects mit a handy 'writeln' method"""
    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, attr):
        wenn attr in ('stream', '__getstate__'):
            raise AttributeError(attr)
        return getattr(self.stream, attr)

    def writeln(self, arg=Nichts):
        wenn arg:
            self.write(arg)
        self.write('\n')  # text-mode streams translate to \r\n wenn needed


klasse TextTestResult(result.TestResult):
    """A test result klasse that can print formatted text results to a stream.

    Used by TextTestRunner.
    """
    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream, descriptions, verbosity, *, durations=Nichts):
        """Construct a TextTestResult. Subclasses should accept **kwargs
        to ensure compatibility als the interface changes."""
        super(TextTestResult, self).__init__(stream, descriptions, verbosity)
        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions
        self._theme = get_theme(tty_file=stream).unittest
        self._newline = Wahr
        self.durations = durations

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        wenn self.descriptions und doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        sonst:
            return str(test)

    def startTest(self, test):
        super(TextTestResult, self).startTest(test)
        wenn self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")
            self.stream.flush()
            self._newline = Falsch

    def _write_status(self, test, status):
        is_subtest = isinstance(test, _SubTest)
        wenn is_subtest oder self._newline:
            wenn nicht self._newline:
                self.stream.writeln()
            wenn is_subtest:
                self.stream.write("  ")
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")
        self.stream.writeln(status)
        self.stream.flush()
        self._newline = Wahr

    def addSubTest(self, test, subtest, err):
        wenn err is nicht Nichts:
            t = self._theme
            wenn self.showAll:
                wenn issubclass(err[0], subtest.failureException):
                    self._write_status(subtest, f"{t.fail}FAIL{t.reset}")
                sonst:
                    self._write_status(subtest, f"{t.fail}ERROR{t.reset}")
            sowenn self.dots:
                wenn issubclass(err[0], subtest.failureException):
                    self.stream.write(f"{t.fail}F{t.reset}")
                sonst:
                    self.stream.write(f"{t.fail}E{t.reset}")
                self.stream.flush()
        super(TextTestResult, self).addSubTest(test, subtest, err)

    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        t = self._theme
        wenn self.showAll:
            self._write_status(test, f"{t.passed}ok{t.reset}")
        sowenn self.dots:
            self.stream.write(f"{t.passed}.{t.reset}")
            self.stream.flush()

    def addError(self, test, err):
        super(TextTestResult, self).addError(test, err)
        t = self._theme
        wenn self.showAll:
            self._write_status(test, f"{t.fail}ERROR{t.reset}")
        sowenn self.dots:
            self.stream.write(f"{t.fail}E{t.reset}")
            self.stream.flush()

    def addFailure(self, test, err):
        super(TextTestResult, self).addFailure(test, err)
        t = self._theme
        wenn self.showAll:
            self._write_status(test, f"{t.fail}FAIL{t.reset}")
        sowenn self.dots:
            self.stream.write(f"{t.fail}F{t.reset}")
            self.stream.flush()

    def addSkip(self, test, reason):
        super(TextTestResult, self).addSkip(test, reason)
        t = self._theme
        wenn self.showAll:
            self._write_status(test, f"{t.warn}skipped{t.reset} {reason!r}")
        sowenn self.dots:
            self.stream.write(f"{t.warn}s{t.reset}")
            self.stream.flush()

    def addExpectedFailure(self, test, err):
        super(TextTestResult, self).addExpectedFailure(test, err)
        t = self._theme
        wenn self.showAll:
            self.stream.writeln(f"{t.warn}expected failure{t.reset}")
            self.stream.flush()
        sowenn self.dots:
            self.stream.write(f"{t.warn}x{t.reset}")
            self.stream.flush()

    def addUnexpectedSuccess(self, test):
        super(TextTestResult, self).addUnexpectedSuccess(test)
        t = self._theme
        wenn self.showAll:
            self.stream.writeln(f"{t.fail}unexpected success{t.reset}")
            self.stream.flush()
        sowenn self.dots:
            self.stream.write(f"{t.fail}u{t.reset}")
            self.stream.flush()

    def printErrors(self):
        t = self._theme
        wenn self.dots oder self.showAll:
            self.stream.writeln()
            self.stream.flush()
        self.printErrorList(f"{t.fail}ERROR{t.reset}", self.errors)
        self.printErrorList(f"{t.fail}FAIL{t.reset}", self.failures)
        unexpectedSuccesses = getattr(self, "unexpectedSuccesses", ())
        wenn unexpectedSuccesses:
            self.stream.writeln(self.separator1)
            fuer test in unexpectedSuccesses:
                self.stream.writeln(
                    f"{t.fail}UNEXPECTED SUCCESS{t.fail_info}: "
                    f"{self.getDescription(test)}{t.reset}"
                )
            self.stream.flush()

    def printErrorList(self, flavour, errors):
        t = self._theme
        fuer test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln(
                f"{flavour}{t.fail_info}: {self.getDescription(test)}{t.reset}"
            )
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)
            self.stream.flush()


klasse TextTestRunner(object):
    """A test runner klasse that displays results in textual form.

    It prints out the names of tests als they are run, errors als they
    occur, und a summary of the results at the end of the test run.
    """
    resultclass = TextTestResult

    def __init__(self, stream=Nichts, descriptions=Wahr, verbosity=1,
                 failfast=Falsch, buffer=Falsch, resultclass=Nichts, warnings=Nichts,
                 *, tb_locals=Falsch, durations=Nichts):
        """Construct a TextTestRunner.

        Subclasses should accept **kwargs to ensure compatibility als the
        interface changes.
        """
        wenn stream is Nichts:
            stream = sys.stderr
        self.stream = _WritelnDecorator(stream)
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.tb_locals = tb_locals
        self.durations = durations
        self.warnings = warnings
        wenn resultclass is nicht Nichts:
            self.resultclass = resultclass

    def _makeResult(self):
        try:
            return self.resultclass(self.stream, self.descriptions,
                                    self.verbosity, durations=self.durations)
        except TypeError:
            # didn't accept the durations argument
            return self.resultclass(self.stream, self.descriptions,
                                    self.verbosity)

    def _printDurations(self, result):
        wenn nicht result.collectedDurations:
            return
        ls = sorted(result.collectedDurations, key=lambda x: x[1],
                    reverse=Wahr)
        wenn self.durations > 0:
            ls = ls[:self.durations]
        self.stream.writeln("Slowest test durations")
        wenn hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        hidden = Falsch
        fuer test, elapsed in ls:
            wenn self.verbosity < 2 und elapsed < 0.001:
                hidden = Wahr
                continue
            self.stream.writeln("%-10s %s" % ("%.3fs" % elapsed, test))
        wenn hidden:
            self.stream.writeln("\n(durations < 0.001s were hidden; "
                                "use -v to show these durations)")
        sonst:
            self.stream.writeln("")

    def run(self, test):
        "Run the given test case oder test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals
        mit warnings.catch_warnings():
            wenn self.warnings:
                # wenn self.warnings is set, use it to filter all the warnings
                warnings.simplefilter(self.warnings)
            start_time = time.perf_counter()
            startTestRun = getattr(result, 'startTestRun', Nichts)
            wenn startTestRun is nicht Nichts:
                startTestRun()
            try:
                test(result)
            finally:
                stopTestRun = getattr(result, 'stopTestRun', Nichts)
                wenn stopTestRun is nicht Nichts:
                    stopTestRun()
            stop_time = time.perf_counter()
        time_taken = stop_time - start_time
        result.printErrors()
        wenn self.durations is nicht Nichts:
            self._printDurations(result)

        wenn hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)

        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 und "s" oder "", time_taken))
        self.stream.writeln()

        expected_fails = unexpected_successes = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        sonst:
            expected_fails, unexpected_successes, skipped = results

        infos = []
        t = get_theme(tty_file=self.stream).unittest

        wenn nicht result.wasSuccessful():
            self.stream.write(f"{t.fail_info}FAILED{t.reset}")
            failed, errored = len(result.failures), len(result.errors)
            wenn failed:
                infos.append(f"{t.fail_info}failures={failed}{t.reset}")
            wenn errored:
                infos.append(f"{t.fail_info}errors={errored}{t.reset}")
        sowenn run == 0 und nicht skipped:
            self.stream.write(f"{t.warn}NO TESTS RAN{t.reset}")
        sonst:
            self.stream.write(f"{t.passed}OK{t.reset}")
        wenn skipped:
            infos.append(f"{t.warn}skipped={skipped}{t.reset}")
        wenn expected_fails:
            infos.append(f"{t.warn}expected failures={expected_fails}{t.reset}")
        wenn unexpected_successes:
            infos.append(
                f"{t.fail}unexpected successes={unexpected_successes}{t.reset}"
            )
        wenn infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        sonst:
            self.stream.write("\n")
        self.stream.flush()
        return result
