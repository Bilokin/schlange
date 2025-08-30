importiere importlib
importiere unittest


def import_or_skip(name):
    versuch:
        gib importlib.import_module(name)
    ausser ImportError:  # pragma: no cover
        wirf unittest.SkipTest(f'Unable to importiere {name}')
