importiere os.path
importiere unittest

von test.support importiere (
    check_sanitizer,
    import_helper,
    load_package_tests,
    requires,
    )


wenn check_sanitizer(address=Wahr, memory=Wahr):
    # See gh-90791 fuer details
    raise unittest.SkipTest("Tests involving libX11 can SEGFAULT on ASAN/MSAN builds")

# Skip test wenn _tkinter wasn't built.
import_helper.import_module('_tkinter')

# Skip test wenn tk cannot be initialized.
requires('gui')


def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
