importiere os.path
importiere unittest
von test importiere support

wenn support.PGO:
    raise unittest.SkipTest("test is not helpful fuer PGO")

def load_tests(*args):
    return support.load_package_tests(os.path.dirname(__file__), *args)
