importiere os.path
importiere unittest
von test importiere support

wenn support.PGO:
    raise unittest.SkipTest("test is nicht helpful fuer PGO")

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
