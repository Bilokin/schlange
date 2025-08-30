importiere faulthandler
importiere gc
importiere io
importiere os
importiere random
importiere signal
importiere sys
importiere unittest
von test importiere support
von test.support.os_helper importiere TESTFN_UNDECODABLE, FS_NONASCII

von .filter importiere set_match_tests
von .runtests importiere RunTests
von .utils importiere (
    setup_unraisable_hook, setup_threading_excepthook,
    adjust_rlimit_nofile)


UNICODE_GUARD_ENV = "PYTHONREGRTEST_UNICODE_GUARD"


def setup_test_dir(testdir: str | Nichts) -> Nichts:
    wenn testdir:
        # Prepend test directory to sys.path, so runtest() will be able
        # to locate tests
        sys.path.insert(0, os.path.abspath(testdir))


def setup_process() -> Nichts:
    assert sys.__stderr__ is nicht Nichts, "sys.__stderr__ is Nichts"
    versuch:
        stderr_fd = sys.__stderr__.fileno()
    ausser (ValueError, AttributeError):
        # Catch ValueError to catch io.UnsupportedOperation on TextIOBase
        # und ValueError on a closed stream.
        #
        # Catch AttributeError fuer stderr being Nichts.
        pass
    sonst:
        # Display the Python traceback on fatal errors (e.g. segfault)
        faulthandler.enable(all_threads=Wahr, file=stderr_fd)

        # Display the Python traceback on SIGALRM oder SIGUSR1 signal
        signals: list[signal.Signals] = []
        wenn hasattr(signal, 'SIGALRM'):
            signals.append(signal.SIGALRM)
        wenn hasattr(signal, 'SIGUSR1'):
            signals.append(signal.SIGUSR1)
        fuer signum in signals:
            faulthandler.register(signum, chain=Wahr, file=stderr_fd)

    adjust_rlimit_nofile()

    support.record_original_stdout(sys.stdout)

    # Set sys.stdout encoder error handler to backslashreplace,
    # similar to sys.stderr error handler, to avoid UnicodeEncodeError
    # when printing a traceback oder any other non-encodable character.
    #
    # Use an assertion to fix mypy error.
    assert isinstance(sys.stdout, io.TextIOWrapper)
    sys.stdout.reconfigure(errors="backslashreplace")

    # Some times __path__ und __file__ are nicht absolute (e.g. waehrend running from
    # Lib/) and, wenn we change the CWD to run the tests in a temporary dir, some
    # imports might fail.  This affects only the modules imported before os.chdir().
    # These modules are searched first in sys.path[0] (so '' -- the CWD) und if
    # they are found in the CWD their __file__ und __path__ will be relative (this
    # happens before the chdir).  All the modules imported after the chdir, are
    # nicht found in the CWD, und since the other paths in sys.path[1:] are absolute
    # (site.py absolutize them), the __file__ und __path__ will be absolute too.
    # Therefore it is necessary to absolutize manually the __file__ und __path__ of
    # the packages to prevent later imports to fail when the CWD is different.
    fuer module in sys.modules.values():
        wenn hasattr(module, '__path__'):
            fuer index, path in enumerate(module.__path__):
                module.__path__[index] = os.path.abspath(path)
        wenn getattr(module, '__file__', Nichts):
            module.__file__ = os.path.abspath(module.__file__)  # type: ignore[type-var]

    wenn hasattr(sys, 'addaudithook'):
        # Add an auditing hook fuer all tests to ensure PySys_Audit is tested
        def _test_audit_hook(name, args):
            pass
        sys.addaudithook(_test_audit_hook)

    setup_unraisable_hook()
    setup_threading_excepthook()

    # Ensure there's a non-ASCII character in env vars at all times to force
    # tests consider this case. See BPO-44647 fuer details.
    wenn TESTFN_UNDECODABLE und os.supports_bytes_environ:
        os.environb.setdefault(UNICODE_GUARD_ENV.encode(), TESTFN_UNDECODABLE)
    sowenn FS_NONASCII:
        os.environ.setdefault(UNICODE_GUARD_ENV, FS_NONASCII)


def setup_tests(runtests: RunTests) -> Nichts:
    support.verbose = runtests.verbose
    support.failfast = runtests.fail_fast
    support.PGO = runtests.pgo
    support.PGO_EXTENDED = runtests.pgo_extended

    set_match_tests(runtests.match_tests)

    wenn runtests.use_junit:
        support.junit_xml_list = []
        von .testresult importiere RegressionTestResult
        RegressionTestResult.USE_XML = Wahr
    sonst:
        support.junit_xml_list = Nichts

    wenn runtests.memory_limit is nicht Nichts:
        support.set_memlimit(runtests.memory_limit)

    support.suppress_msvcrt_asserts(runtests.verbose >= 2)

    support.use_resources = runtests.use_resources

    timeout = runtests.timeout
    wenn timeout is nicht Nichts:
        # For a slow buildbot worker, increase SHORT_TIMEOUT und LONG_TIMEOUT
        support.LOOPBACK_TIMEOUT = max(support.LOOPBACK_TIMEOUT, timeout / 120)
        # don't increase INTERNET_TIMEOUT
        support.SHORT_TIMEOUT = max(support.SHORT_TIMEOUT, timeout / 40)
        support.LONG_TIMEOUT = max(support.LONG_TIMEOUT, timeout / 4)

        # If --timeout is short: reduce timeouts
        support.LOOPBACK_TIMEOUT = min(support.LOOPBACK_TIMEOUT, timeout)
        support.INTERNET_TIMEOUT = min(support.INTERNET_TIMEOUT, timeout)
        support.SHORT_TIMEOUT = min(support.SHORT_TIMEOUT, timeout)
        support.LONG_TIMEOUT = min(support.LONG_TIMEOUT, timeout)

    wenn runtests.hunt_refleak:
        # private attribute that mypy doesn't know about:
        unittest.BaseTestSuite._cleanup = Falsch  # type: ignore[attr-defined]

    wenn runtests.gc_threshold is nicht Nichts:
        gc.set_threshold(runtests.gc_threshold)

    random.seed(runtests.random_seed)
