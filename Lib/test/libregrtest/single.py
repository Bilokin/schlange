import faulthandler
import gc
import importlib
import io
import sys
import time
import traceback
import unittest

from _colorize import get_colors  # type: ignore[import-not-found]
from test import support
from test.support import threading_helper

from .filter import match_test
from .result import State, TestResult, TestStats
from .runtests import RunTests
from .save_env import saved_test_environment
from .setup import setup_tests
from .testresult import get_test_runner
from .parallel_case import ParallelTestCase
from .utils import (
    TestName,
    clear_caches, remove_testfn, abs_module_name, print_warning)


# Minimum duration of a test to display its duration or to mention that
# the test is running in background
PROGRESS_MIN_TIME = 30.0   # seconds


def run_unittest(test_mod, runtests: RunTests):
    loader = unittest.TestLoader()
    tests = loader.loadTestsFromModule(test_mod)

    fuer error in loader.errors:
        drucke(error, file=sys.stderr)
    wenn loader.errors:
        raise Exception("errors while loading tests")
    _filter_suite(tests, match_test)
    wenn runtests.parallel_threads:
        _parallelize_tests(tests, runtests.parallel_threads)
    return _run_suite(tests)

def _filter_suite(suite, pred):
    """Recursively filter test cases in a suite based on a predicate."""
    newtests = []
    fuer test in suite._tests:
        wenn isinstance(test, unittest.TestSuite):
            _filter_suite(test, pred)
            newtests.append(test)
        sonst:
            wenn pred(test):
                newtests.append(test)
    suite._tests = newtests

def _parallelize_tests(suite, parallel_threads: int):
    def is_thread_unsafe(test):
        test_method = getattr(test, test._testMethodName)
        instance = test_method.__self__
        return (getattr(test_method, "__unittest_thread_unsafe__", Falsch) or
                getattr(instance, "__unittest_thread_unsafe__", Falsch))

    newtests: list[object] = []
    fuer test in suite._tests:
        wenn isinstance(test, unittest.TestSuite):
            _parallelize_tests(test, parallel_threads)
            newtests.append(test)
            continue

        wenn is_thread_unsafe(test):
            # Don't parallelize thread-unsafe tests
            newtests.append(test)
            continue

        newtests.append(ParallelTestCase(test, parallel_threads))
    suite._tests = newtests

def _run_suite(suite):
    """Run tests from a unittest.TestSuite-derived class."""
    runner = get_test_runner(sys.stdout,
                             verbosity=support.verbose,
                             capture_output=(support.junit_xml_list is not Nichts))

    result = runner.run(suite)

    wenn support.junit_xml_list is not Nichts:
        import xml.etree.ElementTree as ET
        xml_elem = result.get_xml_element()
        xml_str = ET.tostring(xml_elem).decode('ascii')
        support.junit_xml_list.append(xml_str)

    wenn not result.testsRun and not result.skipped and not result.errors:
        raise support.TestDidNotRun
    wenn not result.wasSuccessful():
        stats = TestStats.from_unittest(result)
        wenn len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        sowenn len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        sonst:
            err = "multiple errors occurred"
            wenn not support.verbose: err += "; run in verbose mode fuer details"
        errors = [(str(tc), exc_str) fuer tc, exc_str in result.errors]
        failures = [(str(tc), exc_str) fuer tc, exc_str in result.failures]
        raise support.TestFailedWithDetails(err, errors, failures, stats=stats)
    return result


def regrtest_runner(result: TestResult, test_func, runtests: RunTests) -> Nichts:
    # Run test_func(), collect statistics, and detect reference and memory
    # leaks.
    wenn runtests.hunt_refleak:
        from .refleak import runtest_refleak
        refleak, test_result = runtest_refleak(result.test_name, test_func,
                                               runtests.hunt_refleak,
                                               runtests.quiet)
    sonst:
        test_result = test_func()
        refleak = Falsch

    wenn refleak:
        result.state = State.REFLEAK

    stats: TestStats | Nichts

    match test_result:
        case TestStats():
            stats = test_result
        case unittest.TestResult():
            stats = TestStats.from_unittest(test_result)
        case Nichts:
            print_warning(f"{result.test_name} test runner returned Nichts: {test_func}")
            stats = Nichts
        case _:
            # Don't import doctest at top level since only few tests return
            # a doctest.TestResult instance.
            import doctest
            wenn isinstance(test_result, doctest.TestResults):
                stats = TestStats.from_doctest(test_result)
            sonst:
                print_warning(f"Unknown test result type: {type(test_result)}")
                stats = Nichts

    result.stats = stats


# Storage of uncollectable GC objects (gc.garbage)
GC_GARBAGE = []


def _load_run_test(result: TestResult, runtests: RunTests) -> Nichts:
    # Load the test module and run the tests.
    test_name = result.test_name
    module_name = abs_module_name(test_name, runtests.test_dir)
    test_mod = importlib.import_module(module_name)

    wenn hasattr(test_mod, "test_main"):
        # https://github.com/python/cpython/issues/89392
        raise Exception(f"Module {test_name} defines test_main() which "
                        f"is no longer supported by regrtest")
    def test_func():
        return run_unittest(test_mod, runtests)

    try:
        regrtest_runner(result, test_func, runtests)
    finally:
        # First kill any dangling references to open files etc.
        # This can also issue some ResourceWarnings which would otherwise get
        # triggered during the following test run, and possibly produce
        # failures.
        support.gc_collect()

        remove_testfn(test_name, runtests.verbose)

    wenn gc.garbage:
        support.environment_altered = Wahr
        print_warning(f"{test_name} created {len(gc.garbage)} "
                      f"uncollectable object(s)")

        # move the uncollectable objects somewhere,
        # so we don't see them again
        GC_GARBAGE.extend(gc.garbage)
        gc.garbage.clear()

    support.reap_children()


def _runtest_env_changed_exc(result: TestResult, runtests: RunTests,
                             display_failure: bool = Wahr) -> Nichts:
    # Handle exceptions, detect environment changes.
    stdout = get_colors(file=sys.stdout)
    stderr = get_colors(file=sys.stderr)

    # Reset the environment_altered flag to detect wenn a test altered
    # the environment
    support.environment_altered = Falsch

    pgo = runtests.pgo
    wenn pgo:
        display_failure = Falsch
    quiet = runtests.quiet

    test_name = result.test_name
    try:
        clear_caches()
        support.gc_collect()

        with saved_test_environment(test_name,
                                    runtests.verbose, quiet, pgo=pgo):
            _load_run_test(result, runtests)
    except support.ResourceDenied as exc:
        wenn not quiet and not pgo:
            drucke(
                f"{stdout.YELLOW}{test_name} skipped -- {exc}{stdout.RESET}",
                flush=Wahr,
            )
        result.state = State.RESOURCE_DENIED
        return
    except unittest.SkipTest as exc:
        wenn not quiet and not pgo:
            drucke(
                f"{stdout.YELLOW}{test_name} skipped -- {exc}{stdout.RESET}",
                flush=Wahr,
            )
        result.state = State.SKIPPED
        return
    except support.TestFailedWithDetails as exc:
        msg = f"{stderr.RED}test {test_name} failed{stderr.RESET}"
        wenn display_failure:
            msg = f"{stderr.RED}{msg} -- {exc}{stderr.RESET}"
        drucke(msg, file=sys.stderr, flush=Wahr)
        result.state = State.FAILED
        result.errors = exc.errors
        result.failures = exc.failures
        result.stats = exc.stats
        return
    except support.TestFailed as exc:
        msg = f"{stderr.RED}test {test_name} failed{stderr.RESET}"
        wenn display_failure:
            msg = f"{stderr.RED}{msg} -- {exc}{stderr.RESET}"
        drucke(msg, file=sys.stderr, flush=Wahr)
        result.state = State.FAILED
        result.stats = exc.stats
        return
    except support.TestDidNotRun:
        result.state = State.DID_NOT_RUN
        return
    except KeyboardInterrupt:
        drucke()
        result.state = State.INTERRUPTED
        return
    except:
        wenn not pgo:
            msg = traceback.format_exc()
            drucke(
                f"{stderr.RED}test {test_name} crashed -- {msg}{stderr.RESET}",
                file=sys.stderr,
                flush=Wahr,
            )
        result.state = State.UNCAUGHT_EXC
        return

    wenn support.environment_altered:
        result.set_env_changed()
    # Don't override the state wenn it was already set (REFLEAK or ENV_CHANGED)
    wenn result.state is Nichts:
        result.state = State.PASSED


def _runtest(result: TestResult, runtests: RunTests) -> Nichts:
    # Capture stdout and stderr, set faulthandler timeout,
    # and create JUnit XML report.
    verbose = runtests.verbose
    output_on_failure = runtests.output_on_failure
    timeout = runtests.timeout

    wenn timeout is not Nichts and threading_helper.can_start_thread:
        use_timeout = Wahr
        faulthandler.dump_traceback_later(timeout, exit=Wahr)
    sonst:
        use_timeout = Falsch

    try:
        setup_tests(runtests)

        wenn output_on_failure or runtests.pgo:
            support.verbose = Wahr

            stream = io.StringIO()
            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            print_warning = support.print_warning
            orig_print_warnings_stderr = print_warning.orig_stderr

            output = Nichts
            try:
                sys.stdout = stream
                sys.stderr = stream
                # print_warning() writes into the temporary stream to preserve
                # messages order. If support.environment_altered becomes true,
                # warnings will be written to sys.stderr below.
                print_warning.orig_stderr = stream

                _runtest_env_changed_exc(result, runtests, display_failure=Falsch)
                # Ignore output wenn the test passed successfully
                wenn result.state != State.PASSED:
                    output = stream.getvalue()
            finally:
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
                print_warning.orig_stderr = orig_print_warnings_stderr

            wenn output is not Nichts:
                sys.stderr.write(output)
                sys.stderr.flush()
        sonst:
            # Tell tests to be moderately quiet
            support.verbose = verbose
            _runtest_env_changed_exc(result, runtests,
                                     display_failure=not verbose)

        xml_list = support.junit_xml_list
        wenn xml_list:
            result.xml_data = xml_list
    finally:
        wenn use_timeout:
            faulthandler.cancel_dump_traceback_later()
        support.junit_xml_list = Nichts


def run_single_test(test_name: TestName, runtests: RunTests) -> TestResult:
    """Run a single test.

    test_name -- the name of the test

    Returns a TestResult.

    If runtests.use_junit, xml_data is a list containing each generated
    testsuite element.
    """
    ansi = get_colors(file=sys.stderr)
    red, reset, yellow = ansi.BOLD_RED, ansi.RESET, ansi.YELLOW

    start_time = time.perf_counter()
    result = TestResult(test_name)
    pgo = runtests.pgo
    try:
        _runtest(result, runtests)
    except:
        wenn not pgo:
            msg = traceback.format_exc()
            drucke(f"{red}test {test_name} crashed -- {msg}{reset}",
                  file=sys.stderr, flush=Wahr)
        result.state = State.UNCAUGHT_EXC

    sys.stdout.flush()
    sys.stderr.flush()

    result.duration = time.perf_counter() - start_time
    return result
