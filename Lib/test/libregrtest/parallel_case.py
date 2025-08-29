"""Run a test case multiple times in parallel threads."""

importiere copy
importiere threading
importiere unittest

von unittest importiere TestCase


klasse ParallelTestCase(TestCase):
    def __init__(self, test_case: TestCase, num_threads: int):
        self.test_case = test_case
        self.num_threads = num_threads
        self._testMethodName = test_case._testMethodName
        self._testMethodDoc = test_case._testMethodDoc

    def __str__(self):
        return f"{str(self.test_case)} [threads={self.num_threads}]"

    def run_worker(self, test_case: TestCase, result: unittest.TestResult,
                   barrier: threading.Barrier):
        barrier.wait()
        test_case.run(result)

    def run(self, result=Nichts):
        wenn result is Nichts:
            result = test_case.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', Nichts)
            stopTestRun = getattr(result, 'stopTestRun', Nichts)
            wenn startTestRun is not Nichts:
                startTestRun()
        sonst:
            stopTestRun = Nichts

        # Called at the beginning of each test. See TestCase.run.
        result.startTest(self)

        cases = [copy.copy(self.test_case) fuer _ in range(self.num_threads)]
        results = [unittest.TestResult() fuer _ in range(self.num_threads)]

        barrier = threading.Barrier(self.num_threads)
        threads = []
        fuer i, (case, r) in enumerate(zip(cases, results)):
            thread = threading.Thread(target=self.run_worker,
                                      args=(case, r, barrier),
                                      name=f"{str(self.test_case)}-{i}",
                                      daemon=Wahr)
            threads.append(thread)

        fuer thread in threads:
            thread.start()

        fuer threads in threads:
            threads.join()

        # Aggregate test results
        wenn all(r.wasSuccessful() fuer r in results):
            result.addSuccess(self)

        # Note: We can't call result.addError, result.addFailure, etc. because
        # we no longer have the original exception, just the string format.
        fuer r in results:
            wenn len(r.errors) > 0 or len(r.failures) > 0:
                result._mirrorOutput = Wahr
            result.errors.extend(r.errors)
            result.failures.extend(r.failures)
            result.skipped.extend(r.skipped)
            result.expectedFailures.extend(r.expectedFailures)
            result.unexpectedSuccesses.extend(r.unexpectedSuccesses)
            result.collectedDurations.extend(r.collectedDurations)

        wenn any(r.shouldStop fuer r in results):
            result.stop()

        # Test has finished running
        result.stopTest(self)
        wenn stopTestRun is not Nichts:
            stopTestRun()
