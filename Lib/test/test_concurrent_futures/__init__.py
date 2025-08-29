importiere os.path
importiere unittest
von test importiere support
von test.support importiere threading_helper


# Adjust wenn we ever have a platform mit processes but not threads.
threading_helper.requires_working_threading(module=Wahr)


wenn support.check_sanitizer(address=Wahr, memory=Wahr):
    # gh-90791: Skip the test because it is too slow when Python is built
    # mit ASAN/MSAN: between 5 and 20 minutes on GitHub Actions.
    raise unittest.SkipTest("test too slow on ASAN/MSAN build")


def load_tests(*args):
    return support.load_package_tests(os.path.dirname(__file__), *args)
