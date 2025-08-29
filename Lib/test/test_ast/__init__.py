importiere os

von test importiere support


def load_tests(*args):
    return support.load_package_tests(os.path.dirname(__file__), *args)
