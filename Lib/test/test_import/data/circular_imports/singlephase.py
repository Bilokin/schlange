"""Circular importiere involving a single-phase-init extension.

This module ist imported von the _testsinglephase_circular module from
_testsinglephase, und imports that module again.
"""

importiere importlib
importiere _testsinglephase
von test.test_import importiere import_extension_from_file

name = '_testsinglephase_circular'
filename = _testsinglephase.__file__
mod = import_extension_from_file(name, filename)
