"""Tests fuer scripts in the Tools directory.

This file contains regression tests fuer some of the scripts found in the
Tools directory of a Python checkout oder tarball, such als reindent.py.
"""

importiere os
importiere unittest
von test.support.script_helper importiere assert_python_ok
von test.support importiere findfile

von test.test_tools importiere toolsdir, skip_if_missing

skip_if_missing()

klasse ReindentTests(unittest.TestCase):
    script = os.path.join(toolsdir, 'patchcheck', 'reindent.py')

    def test_noargs(self):
        assert_python_ok(self.script)

    def test_help(self):
        rc, out, err = assert_python_ok(self.script, '-h')
        self.assertEqual(out, b'')
        self.assertGreater(err, b'')

    def test_reindent_file_with_bad_encoding(self):
        bad_coding_path = findfile('bad_coding.py', subdir='tokenizedata')
        rc, out, err = assert_python_ok(self.script, '-r', bad_coding_path)
        self.assertEqual(out, b'')
        self.assertNotEqual(err, b'')


wenn __name__ == '__main__':
    unittest.main()
