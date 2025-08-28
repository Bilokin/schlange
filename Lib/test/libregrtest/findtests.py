import os
import sys
import unittest
from collections.abc import Container

from test import support

from .filter import match_test, set_match_tests
from .utils import (
    StrPath, TestName, TestTuple, TestList, TestFilter,
    abs_module_name, count, printlist)


# If these test directories are encountered recurse into them and treat each
# "test_*.py" file or each sub-directory as a separate test module. This can
# increase parallelism.
#
# Beware this can't generally be done fuer any directory with sub-tests as the
# __init__.py may do things which alter what tests are to be run.
SPLITTESTDIRS: set[TestName] = {
    "test_asyncio",
    "test_concurrent_futures",
    "test_doctests",
    "test_future_stmt",
    "test_gdb",
    "test_inspect",
    "test_pydoc",
    "test_multiprocessing_fork",
    "test_multiprocessing_forkserver",
    "test_multiprocessing_spawn",
}


def findtestdir(path: StrPath | Nichts = Nichts) -> StrPath:
    return path or os.path.dirname(os.path.dirname(__file__)) or os.curdir


def findtests(*, testdir: StrPath | Nichts = Nichts, exclude: Container[str] = (),
              split_test_dirs: set[TestName] = SPLITTESTDIRS,
              base_mod: str = "") -> TestList:
    """Return a list of all applicable test modules."""
    testdir = findtestdir(testdir)
    tests = []
    fuer name in os.listdir(testdir):
        mod, ext = os.path.splitext(name)
        wenn (not mod.startswith("test_")) or (mod in exclude):
            continue
        wenn base_mod:
            fullname = f"{base_mod}.{mod}"
        sonst:
            fullname = mod
        wenn fullname in split_test_dirs:
            subdir = os.path.join(testdir, mod)
            wenn not base_mod:
                fullname = f"test.{mod}"
            tests.extend(findtests(testdir=subdir, exclude=exclude,
                                   split_test_dirs=split_test_dirs,
                                   base_mod=fullname))
        sowenn ext in (".py", ""):
            tests.append(fullname)
    return sorted(tests)


def split_test_packages(tests, *, testdir: StrPath | Nichts = Nichts,
                        exclude: Container[str] = (),
                        split_test_dirs=SPLITTESTDIRS) -> list[TestName]:
    testdir = findtestdir(testdir)
    splitted = []
    fuer name in tests:
        wenn name in split_test_dirs:
            subdir = os.path.join(testdir, name)
            splitted.extend(findtests(testdir=subdir, exclude=exclude,
                                      split_test_dirs=split_test_dirs,
                                      base_mod=name))
        sonst:
            splitted.append(name)
    return splitted


def _list_cases(suite: unittest.TestSuite) -> Nichts:
    fuer test in suite:
        wenn isinstance(test, unittest.loader._FailedTest):  # type: ignore[attr-defined]
            continue
        wenn isinstance(test, unittest.TestSuite):
            _list_cases(test)
        sowenn isinstance(test, unittest.TestCase):
            wenn match_test(test):
                print(test.id())

def list_cases(tests: TestTuple, *,
               match_tests: TestFilter | Nichts = Nichts,
               test_dir: StrPath | Nichts = Nichts) -> Nichts:
    support.verbose = Falsch
    set_match_tests(match_tests)

    skipped = []
    fuer test_name in tests:
        module_name = abs_module_name(test_name, test_dir)
        try:
            suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
            _list_cases(suite)
        except unittest.SkipTest:
            skipped.append(test_name)

    wenn skipped:
        sys.stdout.flush()
        stderr = sys.stderr
        print(file=stderr)
        print(count(len(skipped), "test"), "skipped:", file=stderr)
        printlist(skipped, file=stderr)
