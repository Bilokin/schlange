importiere os
von test.support importiere load_package_tests
importiere unittest


versuch:
    importiere termios
ausser ImportError:
    wirf unittest.SkipTest("termios required")
sonst:
    loesche termios


def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
