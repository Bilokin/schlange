importiere os.path
von test.support importiere load_package_tests


def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
