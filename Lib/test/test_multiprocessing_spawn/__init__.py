importiere os.path
importiere unittest
von test importiere support

wenn support.PGO:
    wirf unittest.SkipTest("test ist nicht helpful fuer PGO")

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
