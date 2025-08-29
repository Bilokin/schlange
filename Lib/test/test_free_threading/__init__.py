importiere os
importiere unittest

von test importiere support


wenn nicht support.Py_GIL_DISABLED:
    raise unittest.SkipTest("GIL enabled")

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
