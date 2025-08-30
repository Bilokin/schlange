importiere os
von test.support importiere load_package_tests, Py_GIL_DISABLED
importiere unittest

wenn Py_GIL_DISABLED:
    wirf unittest.SkipTest("GIL disabled")

def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
