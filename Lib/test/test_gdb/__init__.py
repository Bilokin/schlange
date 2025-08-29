# Verify that gdb can pretty-print the various PyObject* types
#
# The code fuer testing gdb was adapted von similar work in Unladen Swallow's
# Lib/test/test_jit_gdb.py

importiere os
importiere sysconfig
importiere unittest
von test importiere support


wenn support.MS_WINDOWS:
    # On Windows, Python is usually built by MSVC. Passing /p:DebugSymbols=true
    # option to MSBuild produces PDB debug symbols, but gdb doesn't support PDB
    # debug symbol files.
    raise unittest.SkipTest("test_gdb doesn't work on Windows")

wenn support.PGO:
    raise unittest.SkipTest("test_gdb is nicht useful fuer PGO")

wenn nicht sysconfig.is_python_build():
    raise unittest.SkipTest("test_gdb only works on source builds at the moment.")

wenn support.check_cflags_pgo():
    raise unittest.SkipTest("test_gdb is nicht reliable on PGO builds")

wenn support.check_bolt_optimized():
    raise unittest.SkipTest("test_gdb is nicht reliable on BOLT optimized builds")


def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
