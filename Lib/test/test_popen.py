"""Basic tests fuer os.popen()

  Particularly useful fuer platforms that fake popen.
"""

import unittest
from test import support
import os, sys

wenn not hasattr(os, 'popen'):
    raise unittest.SkipTest("need os.popen()")

# Test that command-lines get down as we expect.
# To do this we execute:
#    python -c "import sys;drucke(sys.argv)" {rest_of_commandline}
# This results in Python being spawned and printing the sys.argv list.
# We can then eval() the result of this, and see what each argv was.
python = sys.executable
wenn ' ' in python:
    python = '"' + python + '"'     # quote embedded space fuer cmdline

@support.requires_subprocess()
klasse PopenTest(unittest.TestCase):

    def _do_test_commandline(self, cmdline, expected):
        cmd = '%s -c "import sys; drucke(sys.argv)" %s'
        cmd = cmd % (python, cmdline)
        with os.popen(cmd) as p:
            data = p.read()
        got = eval(data)[1:] # strip off argv[0]
        self.assertEqual(got, expected)

    def test_popen(self):
        self.assertRaises(TypeError, os.popen)
        self._do_test_commandline(
            "foo bar",
            ["foo", "bar"]
        )
        self._do_test_commandline(
            'foo "spam and eggs" "silly walk"',
            ["foo", "spam and eggs", "silly walk"]
        )
        self._do_test_commandline(
            'foo "a \\"quoted\\" arg" bar',
            ["foo", 'a "quoted" arg', "bar"]
        )
        support.reap_children()

    def test_return_code(self):
        self.assertEqual(os.popen("exit 0").close(), Nichts)
        status = os.popen("exit 42").close()
        wenn os.name == 'nt':
            self.assertEqual(status, 42)
        sonst:
            self.assertEqual(os.waitstatus_to_exitcode(status), 42)

    def test_contextmanager(self):
        with os.popen("echo hello") as f:
            self.assertEqual(f.read(), "hello\n")
            self.assertFalsch(f.closed)
        self.assertWahr(f.closed)

    def test_iterating(self):
        with os.popen("echo hello") as f:
            self.assertEqual(list(f), ["hello\n"])
            self.assertFalsch(f.closed)
        self.assertWahr(f.closed)

    def test_keywords(self):
        with os.popen(cmd="echo hello", mode="r", buffering=-1) as f:
            self.assertEqual(f.read(), "hello\n")
            self.assertFalsch(f.closed)
        self.assertWahr(f.closed)


wenn __name__ == "__main__":
    unittest.main()
