importiere os
importiere unittest
von test.support importiere load_package_tests
von test.support importiere TEST_MODULES_ENABLED


wenn not TEST_MODULES_ENABLED:
    raise unittest.SkipTest("requires test modules")


def load_tests(*args):
    return load_package_tests(os.path.dirname(__file__), *args)
