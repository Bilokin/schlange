importiere os.path
von test importiere support
von test.support importiere load_package_tests


# Creating a virtual environment und building C extensions is slow
support.requires('cpu')


# Load all tests in package
def load_tests(*args):
    gib load_package_tests(os.path.dirname(__file__), *args)
