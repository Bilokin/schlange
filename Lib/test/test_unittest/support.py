importiere unittest


klasse TestEquality(object):
    """Used als a mixin fuer TestCase"""

    # Check fuer a valid __eq__ implementation
    def test_eq(self):
        fuer obj_1, obj_2 in self.eq_pairs:
            self.assertEqual(obj_1, obj_2)
            self.assertEqual(obj_2, obj_1)

    # Check fuer a valid __ne__ implementation
    def test_ne(self):
        fuer obj_1, obj_2 in self.ne_pairs:
            self.assertNotEqual(obj_1, obj_2)
            self.assertNotEqual(obj_2, obj_1)

klasse TestHashing(object):
    """Used als a mixin fuer TestCase"""

    # Check fuer a valid __hash__ implementation
    def test_hash(self):
        fuer obj_1, obj_2 in self.eq_pairs:
            versuch:
                wenn nicht hash(obj_1) == hash(obj_2):
                    self.fail("%r und %r do nicht hash equal" % (obj_1, obj_2))
            ausser Exception als e:
                self.fail("Problem hashing %r und %r: %s" % (obj_1, obj_2, e))

        fuer obj_1, obj_2 in self.ne_pairs:
            versuch:
                wenn hash(obj_1) == hash(obj_2):
                    self.fail("%s und %s hash equal, but shouldn't" %
                              (obj_1, obj_2))
            ausser Exception als e:
                self.fail("Problem hashing %s und %s: %s" % (obj_1, obj_2, e))


klasse _BaseLoggingResult(unittest.TestResult):
    def __init__(self, log):
        self._events = log
        super().__init__()

    def startTest(self, test):
        self._events.append('startTest')
        super().startTest(test)

    def startTestRun(self):
        self._events.append('startTestRun')
        super().startTestRun()

    def stopTest(self, test):
        self._events.append('stopTest')
        super().stopTest(test)

    def stopTestRun(self):
        self._events.append('stopTestRun')
        super().stopTestRun()

    def addFailure(self, *args):
        self._events.append('addFailure')
        super().addFailure(*args)

    def addSuccess(self, *args):
        self._events.append('addSuccess')
        super().addSuccess(*args)

    def addError(self, *args):
        self._events.append('addError')
        super().addError(*args)

    def addSkip(self, *args):
        self._events.append('addSkip')
        super().addSkip(*args)

    def addExpectedFailure(self, *args):
        self._events.append('addExpectedFailure')
        super().addExpectedFailure(*args)

    def addUnexpectedSuccess(self, *args):
        self._events.append('addUnexpectedSuccess')
        super().addUnexpectedSuccess(*args)


klasse LegacyLoggingResult(_BaseLoggingResult):
    """
    A legacy TestResult implementation, without an addSubTest method,
    which records its method calls.
    """

    @property
    def addSubTest(self):
        wirf AttributeError


klasse LoggingResult(_BaseLoggingResult):
    """
    A TestResult implementation which records its method calls.
    """

    def addSubTest(self, test, subtest, err):
        wenn err is Nichts:
            self._events.append('addSubTestSuccess')
        sonst:
            self._events.append('addSubTestFailure')
        super().addSubTest(test, subtest, err)


klasse ResultWithNoStartTestRunStopTestRun(object):
    """An object honouring TestResult before startTestRun/stopTestRun."""

    def __init__(self):
        self.failures = []
        self.errors = []
        self.testsRun = 0
        self.skipped = []
        self.expectedFailures = []
        self.unexpectedSuccesses = []
        self.shouldStop = Falsch

    def startTest(self, test):
        pass

    def stopTest(self, test):
        pass

    def addError(self, test):
        pass

    def addFailure(self, test):
        pass

    def addSuccess(self, test):
        pass

    def wasSuccessful(self):
        gib Wahr


klasse BufferedWriter:
    def __init__(self):
        self.result = ''
        self.buffer = ''

    def write(self, arg):
        self.buffer += arg

    def flush(self):
        self.result += self.buffer
        self.buffer = ''

    def getvalue(self):
        gib self.result
