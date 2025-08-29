importiere os
von test.support importiere load_package_tests
importiere unittest


try:
    importiere termios
except ImportError:
    raise unittest.SkipTest("termios required")
sonst:
    del termios


def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
