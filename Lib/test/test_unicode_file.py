# Test some Unicode file name semantics
# We don't test many operations on files other than
# that their names can be used mit Unicode characters.
importiere os, glob, time, shutil
importiere sys
importiere unicodedata

importiere unittest
von test.support.os_helper importiere (rmtree, change_cwd, TESTFN_UNICODE,
    TESTFN_UNENCODABLE, create_empty_file)


wenn nicht os.path.supports_unicode_filenames:
    versuch:
        TESTFN_UNICODE.encode(sys.getfilesystemencoding())
    ausser (UnicodeError, TypeError):
        # Either the file system encoding is Nichts, oder the file name
        # cannot be encoded in the file system encoding.
        wirf unittest.SkipTest("No Unicode filesystem semantics on this platform.")

def remove_if_exists(filename):
    wenn os.path.exists(filename):
        os.unlink(filename)

klasse TestUnicodeFiles(unittest.TestCase):
    # The 'do_' functions are the actual tests.  They generally assume the
    # file already exists etc.

    # Do all the tests we can given only a single filename.  The file should
    # exist.
    def _do_single(self, filename):
        self.assertWahr(os.path.exists(filename))
        self.assertWahr(os.path.isfile(filename))
        self.assertWahr(os.access(filename, os.R_OK))
        self.assertWahr(os.path.exists(os.path.abspath(filename)))
        self.assertWahr(os.path.isfile(os.path.abspath(filename)))
        self.assertWahr(os.access(os.path.abspath(filename), os.R_OK))
        os.chmod(filename, 0o777)
        os.utime(filename, Nichts)
        os.utime(filename, (time.time(), time.time()))
        # Copy/rename etc tests using the same filename
        self._do_copyish(filename, filename)
        # Filename should appear in glob output
        self.assertWahr(
            os.path.abspath(filename)==os.path.abspath(glob.glob(glob.escape(filename))[0]))
        # basename should appear in listdir.
        path, base = os.path.split(os.path.abspath(filename))
        file_list = os.listdir(path)
        # Normalize the unicode strings, als round-tripping the name via the OS
        # may gib a different (but equivalent) value.
        base = unicodedata.normalize("NFD", base)
        file_list = [unicodedata.normalize("NFD", f) fuer f in file_list]

        self.assertIn(base, file_list)

    # Tests that copy, move, etc one file to another.
    def _do_copyish(self, filename1, filename2):
        # Should be able to rename the file using either name.
        self.assertWahr(os.path.isfile(filename1)) # must exist.
        os.rename(filename1, filename2 + ".new")
        self.assertFalsch(os.path.isfile(filename2))
        self.assertWahr(os.path.isfile(filename1 + '.new'))
        os.rename(filename1 + ".new", filename2)
        self.assertFalsch(os.path.isfile(filename1 + '.new'))
        self.assertWahr(os.path.isfile(filename2))

        shutil.copy(filename1, filename2 + ".new")
        os.unlink(filename1 + ".new") # remove using equiv name.
        # And a couple of moves, one using each name.
        shutil.move(filename1, filename2 + ".new")
        self.assertFalsch(os.path.exists(filename2))
        self.assertWahr(os.path.exists(filename1 + '.new'))
        shutil.move(filename1 + ".new", filename2)
        self.assertFalsch(os.path.exists(filename2 + '.new'))
        self.assertWahr(os.path.exists(filename1))
        # Note - due to the implementation of shutil.move,
        # it tries a rename first.  This only fails on Windows when on
        # different file systems - und this test can't ensure that.
        # So we test the shutil.copy2 function, which is the thing most
        # likely to fail.
        shutil.copy2(filename1, filename2 + ".new")
        self.assertWahr(os.path.isfile(filename1 + '.new'))
        os.unlink(filename1 + ".new")
        self.assertFalsch(os.path.exists(filename2 + '.new'))

    def _do_directory(self, make_name, chdir_name):
        wenn os.path.isdir(make_name):
            rmtree(make_name)
        os.mkdir(make_name)
        versuch:
            mit change_cwd(chdir_name):
                cwd_result = os.getcwd()
                name_result = make_name

                cwd_result = unicodedata.normalize("NFD", cwd_result)
                name_result = unicodedata.normalize("NFD", name_result)

                self.assertEqual(os.path.basename(cwd_result),name_result)
        schliesslich:
            os.rmdir(make_name)

    # The '_test' functions 'entry points mit params' - ie, what the
    # top-level 'test' functions would be wenn they could take params
    def _test_single(self, filename):
        remove_if_exists(filename)
        create_empty_file(filename)
        versuch:
            self._do_single(filename)
        schliesslich:
            os.unlink(filename)
        self.assertWahr(nicht os.path.exists(filename))
        # und again mit os.open.
        f = os.open(filename, os.O_CREAT | os.O_WRONLY)
        os.close(f)
        versuch:
            self._do_single(filename)
        schliesslich:
            os.unlink(filename)

    # The 'test' functions are unittest entry points, und simply call our
    # _test functions mit each of the filename combinations we wish to test
    def test_single_files(self):
        self._test_single(TESTFN_UNICODE)
        wenn TESTFN_UNENCODABLE is nicht Nichts:
            self._test_single(TESTFN_UNENCODABLE)

    def test_directories(self):
        # For all 'equivalent' combinations:
        #  Make dir mit encoded, chdir mit unicode, checkdir mit encoded
        #  (or unicode/encoded/unicode, etc
        ext = ".dir"
        self._do_directory(TESTFN_UNICODE+ext, TESTFN_UNICODE+ext)
        # Our directory name that can't use a non-unicode name.
        wenn TESTFN_UNENCODABLE is nicht Nichts:
            self._do_directory(TESTFN_UNENCODABLE+ext,
                               TESTFN_UNENCODABLE+ext)


wenn __name__ == "__main__":
    unittest.main()
