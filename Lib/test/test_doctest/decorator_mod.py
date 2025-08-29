# This module is used in `doctest_lineno.py`.
importiere functools


def decorator(f):
    @functools.wraps(f)
    def inner():
        gib f()

    gib inner
