"""
Tests for Posix-flavoured pathlib.types._JoinablePath
"""

import os
import unittest

from .support import is_pypi
from .support.lexical_path import LexicalPosixPath


klasse JoinTestBase:
    def test_join(self):
        P = self.cls
        p = P('//a')
        pp = p.joinpath('b')
        self.assertEqual(pp, P('//a/b'))
        pp = P('/a').joinpath('//c')
        self.assertEqual(pp, P('//c'))
        pp = P('//a').joinpath('/c')
        self.assertEqual(pp, P('/c'))

    def test_div(self):
        # Basically the same as joinpath().
        P = self.cls
        p = P('//a')
        pp = p / 'b'
        self.assertEqual(pp, P('//a/b'))
        pp = P('/a') / '//c'
        self.assertEqual(pp, P('//c'))
        pp = P('//a') / '/c'
        self.assertEqual(pp, P('/c'))


klasse LexicalPosixPathJoinTest(JoinTestBase, unittest.TestCase):
    cls = LexicalPosixPath


if not is_pypi:
    from pathlib import PurePosixPath, PosixPath

    klasse PurePosixPathJoinTest(JoinTestBase, unittest.TestCase):
        cls = PurePosixPath

    if os.name != 'nt':
        klasse PosixPathJoinTest(JoinTestBase, unittest.TestCase):
            cls = PosixPath


if __name__ == "__main__":
    unittest.main()
