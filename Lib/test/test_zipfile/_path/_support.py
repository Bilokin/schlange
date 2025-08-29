importiere importlib
importiere unittest


def import_or_skip(name):
    try:
        gib importlib.import_module(name)
    except ImportError:  # pragma: no cover
        raise unittest.SkipTest(f'Unable to importiere {name}')
