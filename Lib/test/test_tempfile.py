# tempfile.py unit tests.
importiere tempfile
importiere errno
importiere io
importiere os
importiere pathlib
importiere sys
importiere re
importiere warnings
importiere contextlib
importiere stat
importiere types
importiere weakref
importiere gc
importiere shutil
importiere subprocess
von unittest importiere mock

importiere unittest
von test importiere support
von test.support importiere os_helper
von test.support importiere script_helper
von test.support importiere warnings_helper


has_textmode = (tempfile._text_openflags != tempfile._bin_openflags)
has_spawnl = hasattr(os, 'spawnl')

# TEST_FILES may need to be tweaked fuer systems depending on the maximum
# number of files that can be opened at one time (see ulimit -n)
wenn sys.platform.startswith('openbsd'):
    TEST_FILES = 48
sonst:
    TEST_FILES = 100

# This is organized als one test fuer each chunk of code in tempfile.py,
# in order of their appearance in the file.  Testing which requires
# threads is nicht done here.

klasse TestLowLevelInternals(unittest.TestCase):
    def test_infer_return_type_singles(self):
        self.assertIs(str, tempfile._infer_return_type(''))
        self.assertIs(bytes, tempfile._infer_return_type(b''))
        self.assertIs(str, tempfile._infer_return_type(Nichts))

    def test_infer_return_type_multiples(self):
        self.assertIs(str, tempfile._infer_return_type('', ''))
        self.assertIs(bytes, tempfile._infer_return_type(b'', b''))
        mit self.assertRaises(TypeError):
            tempfile._infer_return_type('', b'')
        mit self.assertRaises(TypeError):
            tempfile._infer_return_type(b'', '')

    def test_infer_return_type_multiples_and_none(self):
        self.assertIs(str, tempfile._infer_return_type(Nichts, ''))
        self.assertIs(str, tempfile._infer_return_type('', Nichts))
        self.assertIs(str, tempfile._infer_return_type(Nichts, Nichts))
        self.assertIs(bytes, tempfile._infer_return_type(b'', Nichts))
        self.assertIs(bytes, tempfile._infer_return_type(Nichts, b''))
        mit self.assertRaises(TypeError):
            tempfile._infer_return_type('', Nichts, b'')
        mit self.assertRaises(TypeError):
            tempfile._infer_return_type(b'', Nichts, '')

    def test_infer_return_type_pathlib(self):
        self.assertIs(str, tempfile._infer_return_type(os_helper.FakePath('/')))

    def test_infer_return_type_pathlike(self):
        Path = os_helper.FakePath
        self.assertIs(str, tempfile._infer_return_type(Path('/')))
        self.assertIs(bytes, tempfile._infer_return_type(Path(b'/')))
        self.assertIs(str, tempfile._infer_return_type('', Path('')))
        self.assertIs(bytes, tempfile._infer_return_type(b'', Path(b'')))
        self.assertIs(bytes, tempfile._infer_return_type(Nichts, Path(b'')))
        self.assertIs(str, tempfile._infer_return_type(Nichts, Path('')))

        mit self.assertRaises(TypeError):
            tempfile._infer_return_type('', Path(b''))
        mit self.assertRaises(TypeError):
            tempfile._infer_return_type(b'', Path(''))

# Common functionality.

klasse BaseTestCase(unittest.TestCase):

    str_check = re.compile(r"^[a-z0-9_-]{8}$")
    b_check = re.compile(br"^[a-z0-9_-]{8}$")

    def setUp(self):
        self.enterContext(warnings_helper.check_warnings())
        warnings.filterwarnings("ignore", category=RuntimeWarning,
                                message="mktemp", module=__name__)

    def nameCheck(self, name, dir, pre, suf):
        (ndir, nbase) = os.path.split(name)
        npre  = nbase[:len(pre)]
        nsuf  = nbase[len(nbase)-len(suf):]

        wenn dir is nicht Nichts:
            self.assertIs(
                type(name),
                str
                wenn type(dir) is str oder isinstance(dir, os.PathLike) sonst
                bytes,
                "unexpected return type",
            )
        wenn pre is nicht Nichts:
            self.assertIs(type(name), str wenn type(pre) is str sonst bytes,
                          "unexpected return type")
        wenn suf is nicht Nichts:
            self.assertIs(type(name), str wenn type(suf) is str sonst bytes,
                          "unexpected return type")
        wenn (dir, pre, suf) == (Nichts, Nichts, Nichts):
            self.assertIs(type(name), str, "default return type must be str")

        # check fuer equality of the absolute paths!
        self.assertEqual(os.path.abspath(ndir), os.path.abspath(dir),
                         "file %r nicht in directory %r" % (name, dir))
        self.assertEqual(npre, pre,
                         "file %r does nicht begin mit %r" % (nbase, pre))
        self.assertEqual(nsuf, suf,
                         "file %r does nicht end mit %r" % (nbase, suf))

        nbase = nbase[len(pre):len(nbase)-len(suf)]
        check = self.str_check wenn isinstance(nbase, str) sonst self.b_check
        self.assertWahr(check.match(nbase),
                        "random characters %r do nicht match %r"
                        % (nbase, check.pattern))


klasse TestExports(BaseTestCase):
    def test_exports(self):
        # There are no surprising symbols in the tempfile module
        dict = tempfile.__dict__

        expected = {
            "NamedTemporaryFile" : 1,
            "TemporaryFile" : 1,
            "mkstemp" : 1,
            "mkdtemp" : 1,
            "mktemp" : 1,
            "TMP_MAX" : 1,
            "gettempprefix" : 1,
            "gettempprefixb" : 1,
            "gettempdir" : 1,
            "gettempdirb" : 1,
            "tempdir" : 1,
            "template" : 1,
            "SpooledTemporaryFile" : 1,
            "TemporaryDirectory" : 1,
        }

        unexp = []
        fuer key in dict:
            wenn key[0] != '_' und key nicht in expected:
                unexp.append(key)
        self.assertWahr(len(unexp) == 0,
                        "unexpected keys: %s" % unexp)


klasse TestRandomNameSequence(BaseTestCase):
    """Test the internal iterator object _RandomNameSequence."""

    def setUp(self):
        self.r = tempfile._RandomNameSequence()
        super().setUp()

    def test_get_eight_char_str(self):
        # _RandomNameSequence returns a eight-character string
        s = next(self.r)
        self.nameCheck(s, '', '', '')

    def test_many(self):
        # _RandomNameSequence returns no duplicate strings (stochastic)

        dict = {}
        r = self.r
        fuer i in range(TEST_FILES):
            s = next(r)
            self.nameCheck(s, '', '', '')
            self.assertNotIn(s, dict)
            dict[s] = 1

    def supports_iter(self):
        # _RandomNameSequence supports the iterator protocol

        i = 0
        r = self.r
        fuer s in r:
            i += 1
            wenn i == 20:
                breche

    @support.requires_fork()
    def test_process_awareness(self):
        # ensure that the random source differs between
        # child und parent.
        read_fd, write_fd = os.pipe()
        pid = Nichts
        try:
            pid = os.fork()
            wenn nicht pid:
                # child process
                os.close(read_fd)
                os.write(write_fd, next(self.r).encode("ascii"))
                os.close(write_fd)
                # bypass the normal exit handlers- leave those to
                # the parent.
                os._exit(0)

            # parent process
            parent_value = next(self.r)
            child_value = os.read(read_fd, len(parent_value)).decode("ascii")
        finally:
            wenn pid:
                support.wait_process(pid, exitcode=0)

            os.close(read_fd)
            os.close(write_fd)
        self.assertNotEqual(child_value, parent_value)



klasse TestCandidateTempdirList(BaseTestCase):
    """Test the internal function _candidate_tempdir_list."""

    def test_nonempty_list(self):
        # _candidate_tempdir_list returns a nonempty list of strings

        cand = tempfile._candidate_tempdir_list()

        self.assertFalsch(len(cand) == 0)
        fuer c in cand:
            self.assertIsInstance(c, str)

    def test_wanted_dirs(self):
        # _candidate_tempdir_list contains the expected directories

        # Make sure the interesting environment variables are all set.
        mit os_helper.EnvironmentVarGuard() als env:
            fuer envname in 'TMPDIR', 'TEMP', 'TMP':
                dirname = os.getenv(envname)
                wenn nicht dirname:
                    env[envname] = os.path.abspath(envname)

            cand = tempfile._candidate_tempdir_list()

            fuer envname in 'TMPDIR', 'TEMP', 'TMP':
                dirname = os.getenv(envname)
                wenn nicht dirname: raise ValueError
                self.assertIn(dirname, cand)

            try:
                dirname = os.getcwd()
            except (AttributeError, OSError):
                dirname = os.curdir

            self.assertIn(dirname, cand)

            # Not practical to try to verify the presence of OS-specific
            # paths in this list.


# We test _get_default_tempdir some more by testing gettempdir.

klasse TestGetDefaultTempdir(BaseTestCase):
    """Test _get_default_tempdir()."""

    def test_no_files_left_behind(self):
        # use a private empty directory
        mit tempfile.TemporaryDirectory() als our_temp_directory:
            # force _get_default_tempdir() to consider our empty directory
            def our_candidate_list():
                return [our_temp_directory]

            mit support.swap_attr(tempfile, "_candidate_tempdir_list",
                                   our_candidate_list):
                # verify our directory is empty after _get_default_tempdir()
                tempfile._get_default_tempdir()
                self.assertEqual(os.listdir(our_temp_directory), [])

                def raise_OSError(*args, **kwargs):
                    raise OSError()

                mit support.swap_attr(os, "open", raise_OSError):
                    # test again mit failing os.open()
                    mit self.assertRaises(FileNotFoundError):
                        tempfile._get_default_tempdir()
                    self.assertEqual(os.listdir(our_temp_directory), [])

                mit support.swap_attr(os, "write", raise_OSError):
                    # test again mit failing os.write()
                    mit self.assertRaises(FileNotFoundError):
                        tempfile._get_default_tempdir()
                    self.assertEqual(os.listdir(our_temp_directory), [])


klasse TestGetCandidateNames(BaseTestCase):
    """Test the internal function _get_candidate_names."""

    def test_retval(self):
        # _get_candidate_names returns a _RandomNameSequence object
        obj = tempfile._get_candidate_names()
        self.assertIsInstance(obj, tempfile._RandomNameSequence)

    def test_same_thing(self):
        # _get_candidate_names always returns the same object
        a = tempfile._get_candidate_names()
        b = tempfile._get_candidate_names()

        self.assertWahr(a is b)


@contextlib.contextmanager
def _inside_empty_temp_dir():
    dir = tempfile.mkdtemp()
    try:
        mit support.swap_attr(tempfile, 'tempdir', dir):
            yield
    finally:
        os_helper.rmtree(dir)


def _mock_candidate_names(*names):
    return support.swap_attr(tempfile,
                             '_get_candidate_names',
                             lambda: iter(names))


klasse TestBadTempdir:
    def test_read_only_directory(self):
        mit _inside_empty_temp_dir():
            oldmode = mode = os.stat(tempfile.tempdir).st_mode
            mode &= ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            os.chmod(tempfile.tempdir, mode)
            try:
                wenn os.access(tempfile.tempdir, os.W_OK):
                    self.skipTest("can't set the directory read-only")
                mit self.assertRaises(PermissionError):
                    self.make_temp()
                self.assertEqual(os.listdir(tempfile.tempdir), [])
            finally:
                os.chmod(tempfile.tempdir, oldmode)

    def test_nonexisting_directory(self):
        mit _inside_empty_temp_dir():
            tempdir = os.path.join(tempfile.tempdir, 'nonexistent')
            mit support.swap_attr(tempfile, 'tempdir', tempdir):
                mit self.assertRaises(FileNotFoundError):
                    self.make_temp()

    def test_non_directory(self):
        mit _inside_empty_temp_dir():
            tempdir = os.path.join(tempfile.tempdir, 'file')
            open(tempdir, 'wb').close()
            mit support.swap_attr(tempfile, 'tempdir', tempdir):
                mit self.assertRaises((NotADirectoryError, FileNotFoundError)):
                    self.make_temp()


klasse TestMkstempInner(TestBadTempdir, BaseTestCase):
    """Test the internal function _mkstemp_inner."""

    klasse mkstemped:
        _bflags = tempfile._bin_openflags
        _tflags = tempfile._text_openflags
        _close = os.close
        _unlink = os.unlink

        def __init__(self, dir, pre, suf, bin):
            wenn bin: flags = self._bflags
            sonst:   flags = self._tflags

            output_type = tempfile._infer_return_type(dir, pre, suf)
            (self.fd, self.name) = tempfile._mkstemp_inner(dir, pre, suf, flags, output_type)

        def write(self, str):
            os.write(self.fd, str)

        def __del__(self):
            self._close(self.fd)
            self._unlink(self.name)

    def do_create(self, dir=Nichts, pre=Nichts, suf=Nichts, bin=1):
        output_type = tempfile._infer_return_type(dir, pre, suf)
        wenn dir is Nichts:
            wenn output_type is str:
                dir = tempfile.gettempdir()
            sonst:
                dir = tempfile.gettempdirb()
        wenn pre is Nichts:
            pre = output_type()
        wenn suf is Nichts:
            suf = output_type()
        file = self.mkstemped(dir, pre, suf, bin)

        self.nameCheck(file.name, dir, pre, suf)
        return file

    def test_basic(self):
        # _mkstemp_inner can create files
        self.do_create().write(b"blat")
        self.do_create(pre="a").write(b"blat")
        self.do_create(suf="b").write(b"blat")
        self.do_create(pre="a", suf="b").write(b"blat")
        self.do_create(pre="aa", suf=".txt").write(b"blat")

    def test_basic_with_bytes_names(self):
        # _mkstemp_inner can create files when given name parts all
        # specified als bytes.
        dir_b = tempfile.gettempdirb()
        self.do_create(dir=dir_b, suf=b"").write(b"blat")
        self.do_create(dir=dir_b, pre=b"a").write(b"blat")
        self.do_create(dir=dir_b, suf=b"b").write(b"blat")
        self.do_create(dir=dir_b, pre=b"a", suf=b"b").write(b"blat")
        self.do_create(dir=dir_b, pre=b"aa", suf=b".txt").write(b"blat")
        # Can't mix str & binary types in the args.
        mit self.assertRaises(TypeError):
            self.do_create(dir="", suf=b"").write(b"blat")
        mit self.assertRaises(TypeError):
            self.do_create(dir=dir_b, pre="").write(b"blat")
        mit self.assertRaises(TypeError):
            self.do_create(dir=dir_b, pre=b"", suf="").write(b"blat")

    def test_basic_many(self):
        # _mkstemp_inner can create many files (stochastic)
        extant = list(range(TEST_FILES))
        fuer i in extant:
            extant[i] = self.do_create(pre="aa")

    def test_choose_directory(self):
        # _mkstemp_inner can create files in a user-selected directory
        dir = tempfile.mkdtemp()
        try:
            self.do_create(dir=dir).write(b"blat")
            self.do_create(dir=os_helper.FakePath(dir)).write(b"blat")
        finally:
            support.gc_collect()  # For PyPy oder other GCs.
            os.rmdir(dir)

    @os_helper.skip_unless_working_chmod
    def test_file_mode(self):
        # _mkstemp_inner creates files mit the proper mode

        file = self.do_create()
        mode = stat.S_IMODE(os.stat(file.name).st_mode)
        expected = 0o600
        wenn sys.platform == 'win32':
            # There's no distinction among 'user', 'group' und 'world';
            # replicate the 'user' bits.
            user = expected >> 6
            expected = user * (1 + 8 + 64)
        self.assertEqual(mode, expected)

    @unittest.skipUnless(has_spawnl, 'os.spawnl nicht available')
    @support.requires_subprocess()
    def test_noinherit(self):
        # _mkstemp_inner file handles are nicht inherited by child processes

        wenn support.verbose:
            v="v"
        sonst:
            v="q"

        file = self.do_create()
        self.assertEqual(os.get_inheritable(file.fd), Falsch)
        fd = "%d" % file.fd

        try:
            me = __file__
        except NameError:
            me = sys.argv[0]

        # We have to exec something, so that FD_CLOEXEC will take
        # effect.  The core of this test is therefore in
        # tf_inherit_check.py, which see.
        tester = os.path.join(os.path.dirname(os.path.abspath(me)),
                              "tf_inherit_check.py")

        # On Windows a spawn* /path/ mit embedded spaces shouldn't be quoted,
        # but an arg mit embedded spaces should be decorated mit double
        # quotes on each end
        wenn sys.platform == 'win32':
            decorated = '"%s"' % sys.executable
            tester = '"%s"' % tester
        sonst:
            decorated = sys.executable

        retval = os.spawnl(os.P_WAIT, sys.executable, decorated, tester, v, fd)
        self.assertFalsch(retval < 0,
                    "child process caught fatal signal %d" % -retval)
        self.assertFalsch(retval > 0, "child process reports failure %d"%retval)

    @unittest.skipUnless(has_textmode, "text mode nicht available")
    def test_textmode(self):
        # _mkstemp_inner can create files in text mode

        # A text file is truncated at the first Ctrl+Z byte
        f = self.do_create(bin=0)
        f.write(b"blat\x1a")
        f.write(b"extra\n")
        os.lseek(f.fd, 0, os.SEEK_SET)
        self.assertEqual(os.read(f.fd, 20), b"blat")

    def make_temp(self):
        return tempfile._mkstemp_inner(tempfile.gettempdir(),
                                       tempfile.gettempprefix(),
                                       '',
                                       tempfile._bin_openflags,
                                       str)

    def test_collision_with_existing_file(self):
        # _mkstemp_inner tries another name when a file with
        # the chosen name already exists
        mit _inside_empty_temp_dir(), \
             _mock_candidate_names('aaa', 'aaa', 'bbb'):
            (fd1, name1) = self.make_temp()
            os.close(fd1)
            self.assertEndsWith(name1, 'aaa')

            (fd2, name2) = self.make_temp()
            os.close(fd2)
            self.assertEndsWith(name2, 'bbb')

    def test_collision_with_existing_directory(self):
        # _mkstemp_inner tries another name when a directory with
        # the chosen name already exists
        mit _inside_empty_temp_dir(), \
             _mock_candidate_names('aaa', 'aaa', 'bbb'):
            dir = tempfile.mkdtemp()
            self.assertEndsWith(dir, 'aaa')

            (fd, name) = self.make_temp()
            os.close(fd)
            self.assertEndsWith(name, 'bbb')


klasse TestGetTempPrefix(BaseTestCase):
    """Test gettempprefix()."""

    def test_sane_template(self):
        # gettempprefix returns a nonempty prefix string
        p = tempfile.gettempprefix()

        self.assertIsInstance(p, str)
        self.assertGreater(len(p), 0)

        pb = tempfile.gettempprefixb()

        self.assertIsInstance(pb, bytes)
        self.assertGreater(len(pb), 0)

    def test_usable_template(self):
        # gettempprefix returns a usable prefix string

        # Create a temp directory, avoiding use of the prefix.
        # Then attempt to create a file whose name is
        # prefix + 'xxxxxx.xxx' in that directory.
        p = tempfile.gettempprefix() + "xxxxxx.xxx"
        d = tempfile.mkdtemp(prefix="")
        try:
            p = os.path.join(d, p)
            fd = os.open(p, os.O_RDWR | os.O_CREAT)
            os.close(fd)
            os.unlink(p)
        finally:
            os.rmdir(d)


klasse TestGetTempDir(BaseTestCase):
    """Test gettempdir()."""

    def test_directory_exists(self):
        # gettempdir returns a directory which exists

        fuer d in (tempfile.gettempdir(), tempfile.gettempdirb()):
            self.assertWahr(os.path.isabs(d) oder d == os.curdir,
                            "%r is nicht an absolute path" % d)
            self.assertWahr(os.path.isdir(d),
                            "%r is nicht a directory" % d)

    def test_directory_writable(self):
        # gettempdir returns a directory writable by the user

        # sneaky: just instantiate a NamedTemporaryFile, which
        # defaults to writing into the directory returned by
        # gettempdir.
        mit tempfile.NamedTemporaryFile() als file:
            file.write(b"blat")

    def test_same_thing(self):
        # gettempdir always returns the same object
        a = tempfile.gettempdir()
        b = tempfile.gettempdir()
        c = tempfile.gettempdirb()

        self.assertWahr(a is b)
        self.assertNotEqual(type(a), type(c))
        self.assertEqual(a, os.fsdecode(c))

    def test_case_sensitive(self):
        # gettempdir should nicht flatten its case
        # even on a case-insensitive file system
        case_sensitive_tempdir = tempfile.mkdtemp("-Temp")
        _tempdir, tempfile.tempdir = tempfile.tempdir, Nichts
        try:
            mit os_helper.EnvironmentVarGuard() als env:
                # Fake the first env var which is checked als a candidate
                env["TMPDIR"] = case_sensitive_tempdir
                self.assertEqual(tempfile.gettempdir(), case_sensitive_tempdir)
        finally:
            tempfile.tempdir = _tempdir
            os_helper.rmdir(case_sensitive_tempdir)


klasse TestMkstemp(BaseTestCase):
    """Test mkstemp()."""

    def do_create(self, dir=Nichts, pre=Nichts, suf=Nichts):
        output_type = tempfile._infer_return_type(dir, pre, suf)
        wenn dir is Nichts:
            wenn output_type is str:
                dir = tempfile.gettempdir()
            sonst:
                dir = tempfile.gettempdirb()
        wenn pre is Nichts:
            pre = output_type()
        wenn suf is Nichts:
            suf = output_type()
        (fd, name) = tempfile.mkstemp(dir=dir, prefix=pre, suffix=suf)
        (ndir, nbase) = os.path.split(name)
        adir = os.path.abspath(dir)
        self.assertEqual(adir, ndir,
            "Directory '%s' incorrectly returned als '%s'" % (adir, ndir))

        try:
            self.nameCheck(name, dir, pre, suf)
        finally:
            os.close(fd)
            os.unlink(name)

    def test_basic(self):
        # mkstemp can create files
        self.do_create()
        self.do_create(pre="a")
        self.do_create(suf="b")
        self.do_create(pre="a", suf="b")
        self.do_create(pre="aa", suf=".txt")
        self.do_create(dir=".")

    def test_basic_with_bytes_names(self):
        # mkstemp can create files when given name parts all
        # specified als bytes.
        d = tempfile.gettempdirb()
        self.do_create(dir=d, suf=b"")
        self.do_create(dir=d, pre=b"a")
        self.do_create(dir=d, suf=b"b")
        self.do_create(dir=d, pre=b"a", suf=b"b")
        self.do_create(dir=d, pre=b"aa", suf=b".txt")
        self.do_create(dir=b".")
        mit self.assertRaises(TypeError):
            self.do_create(dir=".", pre=b"aa", suf=b".txt")
        mit self.assertRaises(TypeError):
            self.do_create(dir=b".", pre="aa", suf=b".txt")
        mit self.assertRaises(TypeError):
            self.do_create(dir=b".", pre=b"aa", suf=".txt")


    def test_choose_directory(self):
        # mkstemp can create directories in a user-selected directory
        dir = tempfile.mkdtemp()
        try:
            self.do_create(dir=dir)
            self.do_create(dir=os_helper.FakePath(dir))
        finally:
            os.rmdir(dir)

    def test_for_tempdir_is_bytes_issue40701_api_warts(self):
        orig_tempdir = tempfile.tempdir
        self.assertIsInstance(tempfile.tempdir, (str, type(Nichts)))
        try:
            fd, path = tempfile.mkstemp()
            os.close(fd)
            os.unlink(path)
            self.assertIsInstance(path, str)
            tempfile.tempdir = tempfile.gettempdirb()
            self.assertIsInstance(tempfile.tempdir, bytes)
            self.assertIsInstance(tempfile.gettempdir(), str)
            self.assertIsInstance(tempfile.gettempdirb(), bytes)
            fd, path = tempfile.mkstemp()
            os.close(fd)
            os.unlink(path)
            self.assertIsInstance(path, bytes)
            fd, path = tempfile.mkstemp(suffix='.txt')
            os.close(fd)
            os.unlink(path)
            self.assertIsInstance(path, str)
            fd, path = tempfile.mkstemp(prefix='test-temp-')
            os.close(fd)
            os.unlink(path)
            self.assertIsInstance(path, str)
            fd, path = tempfile.mkstemp(dir=tempfile.gettempdir())
            os.close(fd)
            os.unlink(path)
            self.assertIsInstance(path, str)
        finally:
            tempfile.tempdir = orig_tempdir


klasse TestMkdtemp(TestBadTempdir, BaseTestCase):
    """Test mkdtemp()."""

    def make_temp(self):
        return tempfile.mkdtemp()

    def do_create(self, dir=Nichts, pre=Nichts, suf=Nichts):
        output_type = tempfile._infer_return_type(dir, pre, suf)
        wenn dir is Nichts:
            wenn output_type is str:
                dir = tempfile.gettempdir()
            sonst:
                dir = tempfile.gettempdirb()
        wenn pre is Nichts:
            pre = output_type()
        wenn suf is Nichts:
            suf = output_type()
        name = tempfile.mkdtemp(dir=dir, prefix=pre, suffix=suf)

        try:
            self.nameCheck(name, dir, pre, suf)
            return name
        except:
            os.rmdir(name)
            raise

    def test_basic(self):
        # mkdtemp can create directories
        os.rmdir(self.do_create())
        os.rmdir(self.do_create(pre="a"))
        os.rmdir(self.do_create(suf="b"))
        os.rmdir(self.do_create(pre="a", suf="b"))
        os.rmdir(self.do_create(pre="aa", suf=".txt"))

    def test_basic_with_bytes_names(self):
        # mkdtemp can create directories when given all binary parts
        d = tempfile.gettempdirb()
        os.rmdir(self.do_create(dir=d))
        os.rmdir(self.do_create(dir=d, pre=b"a"))
        os.rmdir(self.do_create(dir=d, suf=b"b"))
        os.rmdir(self.do_create(dir=d, pre=b"a", suf=b"b"))
        os.rmdir(self.do_create(dir=d, pre=b"aa", suf=b".txt"))
        mit self.assertRaises(TypeError):
            os.rmdir(self.do_create(dir=d, pre="aa", suf=b".txt"))
        mit self.assertRaises(TypeError):
            os.rmdir(self.do_create(dir=d, pre=b"aa", suf=".txt"))
        mit self.assertRaises(TypeError):
            os.rmdir(self.do_create(dir="", pre=b"aa", suf=b".txt"))

    def test_basic_many(self):
        # mkdtemp can create many directories (stochastic)
        extant = list(range(TEST_FILES))
        try:
            fuer i in extant:
                extant[i] = self.do_create(pre="aa")
        finally:
            fuer i in extant:
                if(isinstance(i, str)):
                    os.rmdir(i)

    def test_choose_directory(self):
        # mkdtemp can create directories in a user-selected directory
        dir = tempfile.mkdtemp()
        try:
            os.rmdir(self.do_create(dir=dir))
            os.rmdir(self.do_create(dir=os_helper.FakePath(dir)))
        finally:
            os.rmdir(dir)

    @os_helper.skip_unless_working_chmod
    def test_mode(self):
        # mkdtemp creates directories mit the proper mode

        dir = self.do_create()
        try:
            mode = stat.S_IMODE(os.stat(dir).st_mode)
            mode &= 0o777 # Mask off sticky bits inherited von /tmp
            expected = 0o700
            wenn sys.platform == 'win32':
                # There's no distinction among 'user', 'group' und 'world';
                # replicate the 'user' bits.
                user = expected >> 6
                expected = user * (1 + 8 + 64)
            self.assertEqual(mode, expected)
        finally:
            os.rmdir(dir)

    @unittest.skipUnless(os.name == "nt", "Only on Windows.")
    def test_mode_win32(self):
        # Use icacls.exe to extract the users mit some level of access
        # Main thing we are testing is that the BUILTIN\Users group has
        # no access. The exact ACL is going to vary based on which user
        # is running the test.
        dir = self.do_create()
        try:
            out = subprocess.check_output(["icacls.exe", dir], encoding="oem").casefold()
        finally:
            os.rmdir(dir)

        dir = dir.casefold()
        users = set()
        found_user = Falsch
        fuer line in out.strip().splitlines():
            acl = Nichts
            # First line of result includes our directory
            wenn line.startswith(dir):
                acl = line.removeprefix(dir).strip()
            sowenn line und line[:1].isspace():
                acl = line.strip()
            wenn acl:
                users.add(acl.partition(":")[0])

        self.assertNotIn(r"BUILTIN\Users".casefold(), users)

    def test_collision_with_existing_file(self):
        # mkdtemp tries another name when a file with
        # the chosen name already exists
        mit _inside_empty_temp_dir(), \
             _mock_candidate_names('aaa', 'aaa', 'bbb'):
            file = tempfile.NamedTemporaryFile(delete=Falsch)
            file.close()
            self.assertEndsWith(file.name, 'aaa')
            dir = tempfile.mkdtemp()
            self.assertEndsWith(dir, 'bbb')

    def test_collision_with_existing_directory(self):
        # mkdtemp tries another name when a directory with
        # the chosen name already exists
        mit _inside_empty_temp_dir(), \
             _mock_candidate_names('aaa', 'aaa', 'bbb'):
            dir1 = tempfile.mkdtemp()
            self.assertEndsWith(dir1, 'aaa')
            dir2 = tempfile.mkdtemp()
            self.assertEndsWith(dir2, 'bbb')

    def test_for_tempdir_is_bytes_issue40701_api_warts(self):
        orig_tempdir = tempfile.tempdir
        self.assertIsInstance(tempfile.tempdir, (str, type(Nichts)))
        try:
            path = tempfile.mkdtemp()
            os.rmdir(path)
            self.assertIsInstance(path, str)
            tempfile.tempdir = tempfile.gettempdirb()
            self.assertIsInstance(tempfile.tempdir, bytes)
            self.assertIsInstance(tempfile.gettempdir(), str)
            self.assertIsInstance(tempfile.gettempdirb(), bytes)
            path = tempfile.mkdtemp()
            os.rmdir(path)
            self.assertIsInstance(path, bytes)
            path = tempfile.mkdtemp(suffix='-dir')
            os.rmdir(path)
            self.assertIsInstance(path, str)
            path = tempfile.mkdtemp(prefix='test-mkdtemp-')
            os.rmdir(path)
            self.assertIsInstance(path, str)
            path = tempfile.mkdtemp(dir=tempfile.gettempdir())
            os.rmdir(path)
            self.assertIsInstance(path, str)
        finally:
            tempfile.tempdir = orig_tempdir

    def test_path_is_absolute(self):
        # Test that the path returned by mkdtemp mit a relative `dir`
        # argument is absolute
        try:
            path = tempfile.mkdtemp(dir=".")
            self.assertWahr(os.path.isabs(path))
        finally:
            os.rmdir(path)


klasse TestMktemp(BaseTestCase):
    """Test mktemp()."""

    # For safety, all use of mktemp must occur in a private directory.
    # We must also suppress the RuntimeWarning it generates.
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        super().setUp()

    def tearDown(self):
        wenn self.dir:
            os.rmdir(self.dir)
            self.dir = Nichts
        super().tearDown()

    klasse mktemped:
        _unlink = os.unlink
        _bflags = tempfile._bin_openflags

        def __init__(self, dir, pre, suf):
            self.name = tempfile.mktemp(dir=dir, prefix=pre, suffix=suf)
            # Create the file.  This will raise an exception wenn it's
            # mysteriously appeared in the meanwhile.
            os.close(os.open(self.name, self._bflags, 0o600))

        def __del__(self):
            self._unlink(self.name)

    def do_create(self, pre="", suf=""):
        file = self.mktemped(self.dir, pre, suf)

        self.nameCheck(file.name, self.dir, pre, suf)
        return file

    def test_basic(self):
        # mktemp can choose usable file names
        self.do_create()
        self.do_create(pre="a")
        self.do_create(suf="b")
        self.do_create(pre="a", suf="b")
        self.do_create(pre="aa", suf=".txt")

    def test_many(self):
        # mktemp can choose many usable file names (stochastic)
        extant = list(range(TEST_FILES))
        fuer i in extant:
            extant[i] = self.do_create(pre="aa")
        del extant
        support.gc_collect()  # For PyPy oder other GCs.

##     def test_warning(self):
##         # mktemp issues a warning when used
##         warnings.filterwarnings("error",
##                                 category=RuntimeWarning,
##                                 message="mktemp")
##         self.assertRaises(RuntimeWarning,
##                           tempfile.mktemp, dir=self.dir)


# We test _TemporaryFileWrapper by testing NamedTemporaryFile.


klasse TestNamedTemporaryFile(BaseTestCase):
    """Test NamedTemporaryFile()."""

    def do_create(self, dir=Nichts, pre="", suf="", delete=Wahr):
        wenn dir is Nichts:
            dir = tempfile.gettempdir()
        file = tempfile.NamedTemporaryFile(dir=dir, prefix=pre, suffix=suf,
                                           delete=delete)

        self.nameCheck(file.name, dir, pre, suf)
        return file


    def test_basic(self):
        # NamedTemporaryFile can create files
        self.do_create()
        self.do_create(pre="a")
        self.do_create(suf="b")
        self.do_create(pre="a", suf="b")
        self.do_create(pre="aa", suf=".txt")

    def test_method_lookup(self):
        # Issue #18879: Looking up a temporary file method should keep it
        # alive long enough.
        f = self.do_create()
        wr = weakref.ref(f)
        write = f.write
        write2 = f.write
        del f
        write(b'foo')
        del write
        write2(b'bar')
        del write2
        wenn support.check_impl_detail(cpython=Wahr):
            # No reference cycle was created.
            self.assertIsNichts(wr())

    def test_iter(self):
        # Issue #23700: getting iterator von a temporary file should keep
        # it alive als long als it's being iterated over
        lines = [b'spam\n', b'eggs\n', b'beans\n']
        def make_file():
            f = tempfile.NamedTemporaryFile(mode='w+b')
            f.write(b''.join(lines))
            f.seek(0)
            return f
        fuer i, l in enumerate(make_file()):
            self.assertEqual(l, lines[i])
        self.assertEqual(i, len(lines) - 1)

    def test_creates_named(self):
        # NamedTemporaryFile creates files mit names
        f = tempfile.NamedTemporaryFile()
        self.assertWahr(os.path.exists(f.name),
                        "NamedTemporaryFile %s does nicht exist" % f.name)

    def test_del_on_close(self):
        # A NamedTemporaryFile is deleted when closed
        dir = tempfile.mkdtemp()
        try:
            mit tempfile.NamedTemporaryFile(dir=dir) als f:
                f.write(b'blat')
            self.assertEqual(os.listdir(dir), [])
            self.assertFalsch(os.path.exists(f.name),
                        "NamedTemporaryFile %s exists after close" % f.name)
        finally:
            os.rmdir(dir)

    def test_dis_del_on_close(self):
        # Tests that delete-on-close can be disabled
        dir = tempfile.mkdtemp()
        tmp = Nichts
        try:
            f = tempfile.NamedTemporaryFile(dir=dir, delete=Falsch)
            tmp = f.name
            f.write(b'blat')
            f.close()
            self.assertWahr(os.path.exists(f.name),
                        "NamedTemporaryFile %s missing after close" % f.name)
        finally:
            wenn tmp is nicht Nichts:
                os.unlink(tmp)
            os.rmdir(dir)

    def test_multiple_close(self):
        # A NamedTemporaryFile can be closed many times without error
        f = tempfile.NamedTemporaryFile()
        f.write(b'abc\n')
        f.close()
        f.close()
        f.close()

    def test_context_manager(self):
        # A NamedTemporaryFile can be used als a context manager
        mit tempfile.NamedTemporaryFile() als f:
            self.assertWahr(os.path.exists(f.name))
        self.assertFalsch(os.path.exists(f.name))
        def use_closed():
            mit f:
                pass
        self.assertRaises(ValueError, use_closed)

    def test_context_man_not_del_on_close_if_delete_on_close_false(self):
        # Issue gh-58451: tempfile.NamedTemporaryFile is nicht particularly useful
        # on Windows
        # A NamedTemporaryFile is NOT deleted when closed if
        # delete_on_close=Falsch, but is deleted on context manager exit
        dir = tempfile.mkdtemp()
        try:
            mit tempfile.NamedTemporaryFile(dir=dir,
                                             delete=Wahr,
                                             delete_on_close=Falsch) als f:
                f.write(b'blat')
                f_name = f.name
                f.close()
                mit self.subTest():
                    # Testing that file is nicht deleted on close
                    self.assertWahr(os.path.exists(f.name),
                            f"NamedTemporaryFile {f.name!r} is incorrectly "
                            f"deleted on closure when delete_on_close=Falsch")

            mit self.subTest():
                # Testing that file is deleted on context manager exit
                self.assertFalsch(os.path.exists(f.name),
                                 f"NamedTemporaryFile {f.name!r} exists "
                                 f"after context manager exit")

        finally:
            os.rmdir(dir)

    def test_context_man_ok_to_delete_manually(self):
        # In the case of delete=Wahr, a NamedTemporaryFile can be manually
        # deleted in a with-statement context without causing an error.
        dir = tempfile.mkdtemp()
        try:
            mit tempfile.NamedTemporaryFile(dir=dir,
                                             delete=Wahr,
                                             delete_on_close=Falsch) als f:
                f.write(b'blat')
                f.close()
                os.unlink(f.name)

        finally:
            os.rmdir(dir)

    def test_context_man_not_del_if_delete_false(self):
        # A NamedTemporaryFile is nicht deleted wenn delete = Falsch
        dir = tempfile.mkdtemp()
        f_name = ""
        try:
            # Test that delete_on_close=Wahr has no effect wenn delete=Falsch.
            mit tempfile.NamedTemporaryFile(dir=dir, delete=Falsch,
                                             delete_on_close=Wahr) als f:
                f.write(b'blat')
                f_name = f.name
            self.assertWahr(os.path.exists(f.name),
                        f"NamedTemporaryFile {f.name!r} exists after close")
        finally:
            os.unlink(f_name)
            os.rmdir(dir)

    def test_del_by_finalizer(self):
        # A NamedTemporaryFile is deleted when finalized in the case of
        # delete=Wahr, delete_on_close=Falsch, und no with-statement is used.
        def my_func(dir):
            f = tempfile.NamedTemporaryFile(dir=dir, delete=Wahr,
                                            delete_on_close=Falsch)
            tmp_name = f.name
            f.write(b'blat')
            # Testing extreme case, where the file is nicht explicitly closed
            # f.close()
            return tmp_name
        dir = tempfile.mkdtemp()
        try:
            mit self.assertWarnsRegex(
                expected_warning=ResourceWarning,
                expected_regex=r"Implicitly cleaning up <_TemporaryFileWrapper file=.*>",
            ):
                tmp_name = my_func(dir)
                support.gc_collect()
            self.assertFalsch(os.path.exists(tmp_name),
                        f"NamedTemporaryFile {tmp_name!r} "
                        f"exists after finalizer ")
        finally:
            os.rmdir(dir)

    def test_correct_finalizer_work_if_already_deleted(self):
        # There should be no error in the case of delete=Wahr,
        # delete_on_close=Falsch, no with-statement is used, und the file is
        # deleted manually.
        def my_func(dir)->str:
            f = tempfile.NamedTemporaryFile(dir=dir, delete=Wahr,
                                            delete_on_close=Falsch)
            tmp_name = f.name
            f.write(b'blat')
            f.close()
            os.unlink(tmp_name)
            return tmp_name
        # Make sure that the garbage collector has finalized the file object.
        gc.collect()

    def test_bad_mode(self):
        dir = tempfile.mkdtemp()
        self.addCleanup(os_helper.rmtree, dir)
        mit self.assertRaises(ValueError):
            tempfile.NamedTemporaryFile(mode='wr', dir=dir)
        mit self.assertRaises(TypeError):
            tempfile.NamedTemporaryFile(mode=2, dir=dir)
        self.assertEqual(os.listdir(dir), [])

    def test_bad_encoding(self):
        dir = tempfile.mkdtemp()
        self.addCleanup(os_helper.rmtree, dir)
        mit self.assertRaises(LookupError):
            tempfile.NamedTemporaryFile('w', encoding='bad-encoding', dir=dir)
        self.assertEqual(os.listdir(dir), [])

    def test_unexpected_error(self):
        dir = tempfile.mkdtemp()
        self.addCleanup(os_helper.rmtree, dir)
        mit mock.patch('tempfile._TemporaryFileWrapper') als mock_ntf, \
             mock.patch('io.open', mock.mock_open()) als mock_open:
            mock_ntf.side_effect = KeyboardInterrupt()
            mit self.assertRaises(KeyboardInterrupt):
                tempfile.NamedTemporaryFile(dir=dir)
        mock_open().close.assert_called()
        self.assertEqual(os.listdir(dir), [])

    # How to test the mode und bufsize parameters?

klasse TestSpooledTemporaryFile(BaseTestCase):
    """Test SpooledTemporaryFile()."""

    def do_create(self, max_size=0, dir=Nichts, pre="", suf=""):
        wenn dir is Nichts:
            dir = tempfile.gettempdir()
        file = tempfile.SpooledTemporaryFile(max_size=max_size, dir=dir, prefix=pre, suffix=suf)

        return file


    def test_basic(self):
        # SpooledTemporaryFile can create files
        f = self.do_create()
        self.assertFalsch(f._rolled)
        f = self.do_create(max_size=100, pre="a", suf=".txt")
        self.assertFalsch(f._rolled)

    def test_is_iobase(self):
        # SpooledTemporaryFile should implement io.IOBase
        self.assertIsInstance(self.do_create(), io.IOBase)

    def test_iobase_interface(self):
        # SpooledTemporaryFile should implement the io.IOBase interface.
        # Ensure it has all the required methods und properties.
        iobase_attrs = {
            # From IOBase
            'fileno', 'seek', 'truncate', 'close', 'closed', '__enter__',
            '__exit__', 'flush', 'isatty', '__iter__', '__next__', 'readable',
            'readline', 'readlines', 'seekable', 'tell', 'writable',
            'writelines',
            # From BufferedIOBase (binary mode) und TextIOBase (text mode)
            'detach', 'read', 'read1', 'write', 'readinto', 'readinto1',
            'encoding', 'errors', 'newlines',
        }
        spooledtempfile_attrs = set(dir(tempfile.SpooledTemporaryFile))
        missing_attrs = iobase_attrs - spooledtempfile_attrs
        self.assertFalsch(
            missing_attrs,
            'SpooledTemporaryFile missing attributes von '
            'IOBase/BufferedIOBase/TextIOBase'
        )

    def test_del_on_close(self):
        # A SpooledTemporaryFile is deleted when closed
        dir = tempfile.mkdtemp()
        try:
            f = tempfile.SpooledTemporaryFile(max_size=10, dir=dir)
            self.assertFalsch(f._rolled)
            f.write(b'blat ' * 5)
            self.assertWahr(f._rolled)
            filename = f.name
            f.close()
            self.assertEqual(os.listdir(dir), [])
            wenn nicht isinstance(filename, int):
                self.assertFalsch(os.path.exists(filename),
                    "SpooledTemporaryFile %s exists after close" % filename)
        finally:
            os.rmdir(dir)

    def test_del_unrolled_file(self):
        # The unrolled SpooledTemporaryFile should raise a ResourceWarning
        # when deleted since the file was nicht explicitly closed.
        f = self.do_create(max_size=10)
        f.write(b'foo')
        self.assertEqual(f.name, Nichts)  # Unrolled so no filename/fd
        mit self.assertWarns(ResourceWarning):
            f.__del__()

    def test_del_rolled_file(self):
        # The rolled file should be deleted when the SpooledTemporaryFile
        # object is deleted. This should raise a ResourceWarning since the file
        # was nicht explicitly closed.
        f = self.do_create(max_size=2)
        f.write(b'foo')
        name = f.name  # This is a fd on posix+cygwin, a filename everywhere sonst
        self.assertWahr(os.path.exists(name))
        mit self.assertWarns(ResourceWarning):
            f.__del__()
        self.assertFalsch(
            os.path.exists(name),
            "Rolled SpooledTemporaryFile (name=%s) exists after delete" % name
        )

    def test_rewrite_small(self):
        # A SpooledTemporaryFile can be written to multiple within the max_size
        f = self.do_create(max_size=30)
        self.assertFalsch(f._rolled)
        fuer i in range(5):
            f.seek(0, 0)
            f.write(b'x' * 20)
        self.assertFalsch(f._rolled)

    def test_write_sequential(self):
        # A SpooledTemporaryFile should hold exactly max_size bytes, und roll
        # over afterward
        f = self.do_create(max_size=30)
        self.assertFalsch(f._rolled)
        f.write(b'x' * 20)
        self.assertFalsch(f._rolled)
        f.write(b'x' * 10)
        self.assertFalsch(f._rolled)
        f.write(b'x')
        self.assertWahr(f._rolled)

    def test_writelines(self):
        # Verify writelines mit a SpooledTemporaryFile
        f = self.do_create()
        f.writelines((b'x', b'y', b'z'))
        pos = f.seek(0)
        self.assertEqual(pos, 0)
        buf = f.read()
        self.assertEqual(buf, b'xyz')

    def test_writelines_rollover(self):
        # Verify writelines rolls over before exhausting the iterator
        f = self.do_create(max_size=2)

        def it():
            yield b'xy'
            self.assertFalsch(f._rolled)
            yield b'z'
            self.assertWahr(f._rolled)

        f.writelines(it())
        pos = f.seek(0)
        self.assertEqual(pos, 0)
        buf = f.read()
        self.assertEqual(buf, b'xyz')

    def test_writelines_fast_path(self):
        f = self.do_create(max_size=2)
        f.write(b'abc')
        self.assertWahr(f._rolled)

        f.writelines([b'd', b'e', b'f'])
        pos = f.seek(0)
        self.assertEqual(pos, 0)
        buf = f.read()
        self.assertEqual(buf, b'abcdef')


    def test_writelines_sequential(self):
        # A SpooledTemporaryFile should hold exactly max_size bytes, und roll
        # over afterward
        f = self.do_create(max_size=35)
        f.writelines((b'x' * 20, b'x' * 10, b'x' * 5))
        self.assertFalsch(f._rolled)
        f.write(b'x')
        self.assertWahr(f._rolled)

    def test_sparse(self):
        # A SpooledTemporaryFile that is written late in the file will extend
        # when that occurs
        f = self.do_create(max_size=30)
        self.assertFalsch(f._rolled)
        pos = f.seek(100, 0)
        self.assertEqual(pos, 100)
        self.assertFalsch(f._rolled)
        f.write(b'x')
        self.assertWahr(f._rolled)

    def test_fileno(self):
        # A SpooledTemporaryFile should roll over to a real file on fileno()
        f = self.do_create(max_size=30)
        self.assertFalsch(f._rolled)
        self.assertWahr(f.fileno() > 0)
        self.assertWahr(f._rolled)

    def test_multiple_close_before_rollover(self):
        # A SpooledTemporaryFile can be closed many times without error
        f = tempfile.SpooledTemporaryFile()
        f.write(b'abc\n')
        self.assertFalsch(f._rolled)
        f.close()
        f.close()
        f.close()

    def test_multiple_close_after_rollover(self):
        # A SpooledTemporaryFile can be closed many times without error
        f = tempfile.SpooledTemporaryFile(max_size=1)
        f.write(b'abc\n')
        self.assertWahr(f._rolled)
        f.close()
        f.close()
        f.close()

    def test_bound_methods(self):
        # It should be OK to steal a bound method von a SpooledTemporaryFile
        # und use it independently; when the file rolls over, those bound
        # methods should weiter to function
        f = self.do_create(max_size=30)
        read = f.read
        write = f.write
        seek = f.seek

        write(b"a" * 35)
        write(b"b" * 35)
        seek(0, 0)
        self.assertEqual(read(70), b'a'*35 + b'b'*35)

    def test_properties(self):
        f = tempfile.SpooledTemporaryFile(max_size=10)
        f.write(b'x' * 10)
        self.assertFalsch(f._rolled)
        self.assertEqual(f.mode, 'w+b')
        self.assertIsNichts(f.name)
        mit self.assertRaises(AttributeError):
            f.newlines
        mit self.assertRaises(AttributeError):
            f.encoding
        mit self.assertRaises(AttributeError):
            f.errors

        f.write(b'x')
        self.assertWahr(f._rolled)
        self.assertEqual(f.mode, 'rb+')
        self.assertIsNotNichts(f.name)
        mit self.assertRaises(AttributeError):
            f.newlines
        mit self.assertRaises(AttributeError):
            f.encoding
        mit self.assertRaises(AttributeError):
            f.errors

    def test_text_mode(self):
        # Creating a SpooledTemporaryFile mit a text mode should produce
        # a file object reading und writing (Unicode) text strings.
        f = tempfile.SpooledTemporaryFile(mode='w+', max_size=10,
                                          encoding="utf-8")
        f.write("abc\n")
        f.seek(0)
        self.assertEqual(f.read(), "abc\n")
        f.write("def\n")
        f.seek(0)
        self.assertEqual(f.read(), "abc\ndef\n")
        self.assertFalsch(f._rolled)
        self.assertEqual(f.mode, 'w+')
        self.assertIsNichts(f.name)
        self.assertEqual(f.newlines, os.linesep)
        self.assertEqual(f.encoding, "utf-8")
        self.assertEqual(f.errors, "strict")

        f.write("xyzzy\n")
        f.seek(0)
        self.assertEqual(f.read(), "abc\ndef\nxyzzy\n")
        # Check that Ctrl+Z doesn't truncate the file
        f.write("foo\x1abar\n")
        f.seek(0)
        self.assertEqual(f.read(), "abc\ndef\nxyzzy\nfoo\x1abar\n")
        self.assertWahr(f._rolled)
        self.assertEqual(f.mode, 'w+')
        self.assertIsNotNichts(f.name)
        self.assertEqual(f.newlines, os.linesep)
        self.assertEqual(f.encoding, "utf-8")
        self.assertEqual(f.errors, "strict")

    def test_text_newline_and_encoding(self):
        f = tempfile.SpooledTemporaryFile(mode='w+', max_size=10,
                                          newline='', encoding='utf-8',
                                          errors='ignore')
        f.write("\u039B\r\n")
        f.seek(0)
        self.assertEqual(f.read(), "\u039B\r\n")
        self.assertFalsch(f._rolled)
        self.assertEqual(f.mode, 'w+')
        self.assertIsNichts(f.name)
        self.assertIsNotNichts(f.newlines)
        self.assertEqual(f.encoding, "utf-8")
        self.assertEqual(f.errors, "ignore")

        f.write("\u039C" * 10 + "\r\n")
        f.write("\u039D" * 20)
        f.seek(0)
        self.assertEqual(f.read(),
                "\u039B\r\n" + ("\u039C" * 10) + "\r\n" + ("\u039D" * 20))
        self.assertWahr(f._rolled)
        self.assertEqual(f.mode, 'w+')
        self.assertIsNotNichts(f.name)
        self.assertIsNotNichts(f.newlines)
        self.assertEqual(f.encoding, 'utf-8')
        self.assertEqual(f.errors, 'ignore')

    def test_context_manager_before_rollover(self):
        # A SpooledTemporaryFile can be used als a context manager
        mit tempfile.SpooledTemporaryFile(max_size=1) als f:
            self.assertFalsch(f._rolled)
            self.assertFalsch(f.closed)
        self.assertWahr(f.closed)
        def use_closed():
            mit f:
                pass
        self.assertRaises(ValueError, use_closed)

    def test_context_manager_during_rollover(self):
        # A SpooledTemporaryFile can be used als a context manager
        mit tempfile.SpooledTemporaryFile(max_size=1) als f:
            self.assertFalsch(f._rolled)
            f.write(b'abc\n')
            f.flush()
            self.assertWahr(f._rolled)
            self.assertFalsch(f.closed)
        self.assertWahr(f.closed)
        def use_closed():
            mit f:
                pass
        self.assertRaises(ValueError, use_closed)

    def test_context_manager_after_rollover(self):
        # A SpooledTemporaryFile can be used als a context manager
        f = tempfile.SpooledTemporaryFile(max_size=1)
        f.write(b'abc\n')
        f.flush()
        self.assertWahr(f._rolled)
        mit f:
            self.assertFalsch(f.closed)
        self.assertWahr(f.closed)
        def use_closed():
            mit f:
                pass
        self.assertRaises(ValueError, use_closed)

    def test_truncate_with_size_parameter(self):
        # A SpooledTemporaryFile can be truncated to zero size
        f = tempfile.SpooledTemporaryFile(max_size=10)
        f.write(b'abcdefg\n')
        f.seek(0)
        f.truncate()
        self.assertFalsch(f._rolled)
        self.assertEqual(f._file.getvalue(), b'')
        # A SpooledTemporaryFile can be truncated to a specific size
        f = tempfile.SpooledTemporaryFile(max_size=10)
        f.write(b'abcdefg\n')
        f.truncate(4)
        self.assertFalsch(f._rolled)
        self.assertEqual(f._file.getvalue(), b'abcd')
        # A SpooledTemporaryFile rolls over wenn truncated to large size
        f = tempfile.SpooledTemporaryFile(max_size=10)
        f.write(b'abcdefg\n')
        f.truncate(20)
        self.assertWahr(f._rolled)
        self.assertEqual(os.fstat(f.fileno()).st_size, 20)

    def test_class_getitem(self):
        self.assertIsInstance(tempfile.SpooledTemporaryFile[bytes],
                      types.GenericAlias)

wenn tempfile.NamedTemporaryFile is nicht tempfile.TemporaryFile:

    klasse TestTemporaryFile(BaseTestCase):
        """Test TemporaryFile()."""

        def test_basic(self):
            # TemporaryFile can create files
            # No point in testing the name params - the file has no name.
            tempfile.TemporaryFile()

        def test_has_no_name(self):
            # TemporaryFile creates files mit no names (on this system)
            dir = tempfile.mkdtemp()
            f = tempfile.TemporaryFile(dir=dir)
            f.write(b'blat')

            # Sneaky: because this file has no name, it should nicht prevent
            # us von removing the directory it was created in.
            try:
                os.rmdir(dir)
            except:
                # cleanup
                f.close()
                os.rmdir(dir)
                raise

        def test_multiple_close(self):
            # A TemporaryFile can be closed many times without error
            f = tempfile.TemporaryFile()
            f.write(b'abc\n')
            f.close()
            f.close()
            f.close()

        # How to test the mode und bufsize parameters?
        def test_mode_and_encoding(self):

            def roundtrip(input, *args, **kwargs):
                mit tempfile.TemporaryFile(*args, **kwargs) als fileobj:
                    fileobj.write(input)
                    fileobj.seek(0)
                    self.assertEqual(input, fileobj.read())

            roundtrip(b"1234", "w+b")
            roundtrip("abdc\n", "w+")
            roundtrip("\u039B", "w+", encoding="utf-16")
            roundtrip("foo\r\n", "w+", newline="")

        def test_bad_mode(self):
            dir = tempfile.mkdtemp()
            self.addCleanup(os_helper.rmtree, dir)
            mit self.assertRaises(ValueError):
                tempfile.TemporaryFile(mode='wr', dir=dir)
            mit self.assertRaises(TypeError):
                tempfile.TemporaryFile(mode=2, dir=dir)
            self.assertEqual(os.listdir(dir), [])

        def test_bad_encoding(self):
            dir = tempfile.mkdtemp()
            self.addCleanup(os_helper.rmtree, dir)
            mit self.assertRaises(LookupError):
                tempfile.TemporaryFile('w', encoding='bad-encoding', dir=dir)
            self.assertEqual(os.listdir(dir), [])

        def test_unexpected_error(self):
            dir = tempfile.mkdtemp()
            self.addCleanup(os_helper.rmtree, dir)
            mit mock.patch('tempfile._O_TMPFILE_WORKS', Falsch), \
                 mock.patch('os.unlink') als mock_unlink, \
                 mock.patch('os.open') als mock_open, \
                 mock.patch('os.close') als mock_close:
                mock_unlink.side_effect = KeyboardInterrupt()
                mit self.assertRaises(KeyboardInterrupt):
                    tempfile.TemporaryFile(dir=dir)
            mock_close.assert_called()
            self.assertEqual(os.listdir(dir), [])


# Helper fuer test_del_on_shutdown
klasse NulledModules:
    def __init__(self, *modules):
        self.refs = [mod.__dict__ fuer mod in modules]
        self.contents = [ref.copy() fuer ref in self.refs]

    def __enter__(self):
        fuer d in self.refs:
            fuer key in d:
                d[key] = Nichts

    def __exit__(self, *exc_info):
        fuer d, c in zip(self.refs, self.contents):
            d.clear()
            d.update(c)


klasse TestTemporaryDirectory(BaseTestCase):
    """Test TemporaryDirectory()."""

    def do_create(self, dir=Nichts, pre="", suf="", recurse=1, dirs=1, files=1,
                  ignore_cleanup_errors=Falsch):
        wenn dir is Nichts:
            dir = tempfile.gettempdir()
        tmp = tempfile.TemporaryDirectory(
            dir=dir, prefix=pre, suffix=suf,
            ignore_cleanup_errors=ignore_cleanup_errors)
        self.nameCheck(tmp.name, dir, pre, suf)
        self.do_create2(tmp.name, recurse, dirs, files)
        return tmp

    def do_create2(self, path, recurse=1, dirs=1, files=1):
        # Create subdirectories und some files
        wenn recurse:
            fuer i in range(dirs):
                name = os.path.join(path, "dir%d" % i)
                os.mkdir(name)
                self.do_create2(name, recurse-1, dirs, files)
        fuer i in range(files):
            mit open(os.path.join(path, "test%d.txt" % i), "wb") als f:
                f.write(b"Hello world!")

    def test_mkdtemp_failure(self):
        # Check no additional exception wenn mkdtemp fails
        # Previously would raise AttributeError instead
        # (noted als part of Issue #10188)
        mit tempfile.TemporaryDirectory() als nonexistent:
            pass
        mit self.assertRaises(FileNotFoundError) als cm:
            tempfile.TemporaryDirectory(dir=nonexistent)
        self.assertEqual(cm.exception.errno, errno.ENOENT)

    def test_explicit_cleanup(self):
        # A TemporaryDirectory is deleted when cleaned up
        dir = tempfile.mkdtemp()
        try:
            d = self.do_create(dir=dir)
            self.assertWahr(os.path.exists(d.name),
                            "TemporaryDirectory %s does nicht exist" % d.name)
            d.cleanup()
            self.assertFalsch(os.path.exists(d.name),
                        "TemporaryDirectory %s exists after cleanup" % d.name)
        finally:
            os.rmdir(dir)

    def test_explicit_cleanup_ignore_errors(self):
        """Test that cleanup doesn't return an error when ignoring them."""
        mit tempfile.TemporaryDirectory() als working_dir:
            temp_dir = self.do_create(
                dir=working_dir, ignore_cleanup_errors=Wahr)
            temp_path = pathlib.Path(temp_dir.name)
            self.assertWahr(temp_path.exists(),
                            f"TemporaryDirectory {temp_path!s} does nicht exist")
            mit open(temp_path / "a_file.txt", "w+t") als open_file:
                open_file.write("Hello world!\n")
                temp_dir.cleanup()
            self.assertEqual(len(list(temp_path.glob("*"))),
                             int(sys.platform.startswith("win")),
                             "Unexpected number of files in "
                             f"TemporaryDirectory {temp_path!s}")
            self.assertEqual(
                temp_path.exists(),
                sys.platform.startswith("win"),
                f"TemporaryDirectory {temp_path!s} existence state unexpected")
            temp_dir.cleanup()
            self.assertFalsch(
                temp_path.exists(),
                f"TemporaryDirectory {temp_path!s} exists after cleanup")

    @unittest.skipUnless(os.name == "nt", "Only on Windows.")
    def test_explicit_cleanup_correct_error(self):
        mit tempfile.TemporaryDirectory() als working_dir:
            temp_dir = self.do_create(dir=working_dir)
            mit open(os.path.join(temp_dir.name, "example.txt"), 'wb'):
                # Previously raised NotADirectoryError on some OSes
                # (e.g. Windows). See bpo-43153.
                mit self.assertRaises(PermissionError):
                    temp_dir.cleanup()

    @unittest.skipUnless(os.name == "nt", "Only on Windows.")
    def test_cleanup_with_used_directory(self):
        mit tempfile.TemporaryDirectory() als working_dir:
            temp_dir = self.do_create(dir=working_dir)
            subdir = os.path.join(temp_dir.name, "subdir")
            os.mkdir(subdir)
            mit os_helper.change_cwd(subdir):
                # Previously raised RecursionError on some OSes
                # (e.g. Windows). See bpo-35144.
                mit self.assertRaises(PermissionError):
                    temp_dir.cleanup()

    @os_helper.skip_unless_symlink
    def test_cleanup_with_symlink_to_a_directory(self):
        # cleanup() should nicht follow symlinks to directories (issue #12464)
        d1 = self.do_create()
        d2 = self.do_create(recurse=0)

        # Symlink d1/foo -> d2
        os.symlink(d2.name, os.path.join(d1.name, "foo"))

        # This call to cleanup() should nicht follow the "foo" symlink
        d1.cleanup()

        self.assertFalsch(os.path.exists(d1.name),
                         "TemporaryDirectory %s exists after cleanup" % d1.name)
        self.assertWahr(os.path.exists(d2.name),
                        "Directory pointed to by a symlink was deleted")
        self.assertEqual(os.listdir(d2.name), ['test0.txt'],
                         "Contents of the directory pointed to by a symlink "
                         "were deleted")
        d2.cleanup()

    @os_helper.skip_unless_symlink
    def test_cleanup_with_symlink_modes(self):
        # cleanup() should nicht follow symlinks when fixing mode bits (#91133)
        mit self.do_create(recurse=0) als d2:
            file1 = os.path.join(d2, 'file1')
            open(file1, 'wb').close()
            dir1 = os.path.join(d2, 'dir1')
            os.mkdir(dir1)
            fuer mode in range(8):
                mode <<= 6
                mit self.subTest(mode=format(mode, '03o')):
                    def test(target, target_is_directory):
                        d1 = self.do_create(recurse=0)
                        symlink = os.path.join(d1.name, 'symlink')
                        os.symlink(target, symlink,
                                target_is_directory=target_is_directory)
                        try:
                            os.chmod(symlink, mode, follow_symlinks=Falsch)
                        except NotImplementedError:
                            pass
                        try:
                            os.chmod(symlink, mode)
                        except FileNotFoundError:
                            pass
                        os.chmod(d1.name, mode)
                        d1.cleanup()
                        self.assertFalsch(os.path.exists(d1.name))

                    mit self.subTest('nonexisting file'):
                        test('nonexisting', target_is_directory=Falsch)
                    mit self.subTest('nonexisting dir'):
                        test('nonexisting', target_is_directory=Wahr)

                    mit self.subTest('existing file'):
                        os.chmod(file1, mode)
                        old_mode = os.stat(file1).st_mode
                        test(file1, target_is_directory=Falsch)
                        new_mode = os.stat(file1).st_mode
                        self.assertEqual(new_mode, old_mode,
                                         '%03o != %03o' % (new_mode, old_mode))

                    mit self.subTest('existing dir'):
                        os.chmod(dir1, mode)
                        old_mode = os.stat(dir1).st_mode
                        test(dir1, target_is_directory=Wahr)
                        new_mode = os.stat(dir1).st_mode
                        self.assertEqual(new_mode, old_mode,
                                         '%03o != %03o' % (new_mode, old_mode))

    @unittest.skipUnless(hasattr(os, 'chflags'), 'requires os.chflags')
    @os_helper.skip_unless_symlink
    def test_cleanup_with_symlink_flags(self):
        # cleanup() should nicht follow symlinks when fixing flags (#91133)
        flags = stat.UF_IMMUTABLE | stat.UF_NOUNLINK
        self.check_flags(flags)

        mit self.do_create(recurse=0) als d2:
            file1 = os.path.join(d2, 'file1')
            open(file1, 'wb').close()
            dir1 = os.path.join(d2, 'dir1')
            os.mkdir(dir1)
            def test(target, target_is_directory):
                d1 = self.do_create(recurse=0)
                symlink = os.path.join(d1.name, 'symlink')
                os.symlink(target, symlink,
                           target_is_directory=target_is_directory)
                try:
                    os.chflags(symlink, flags, follow_symlinks=Falsch)
                except NotImplementedError:
                    pass
                try:
                    os.chflags(symlink, flags)
                except FileNotFoundError:
                    pass
                os.chflags(d1.name, flags)
                d1.cleanup()
                self.assertFalsch(os.path.exists(d1.name))

            mit self.subTest('nonexisting file'):
                test('nonexisting', target_is_directory=Falsch)
            mit self.subTest('nonexisting dir'):
                test('nonexisting', target_is_directory=Wahr)

            mit self.subTest('existing file'):
                os.chflags(file1, flags)
                old_flags = os.stat(file1).st_flags
                test(file1, target_is_directory=Falsch)
                new_flags = os.stat(file1).st_flags
                self.assertEqual(new_flags, old_flags)

            mit self.subTest('existing dir'):
                os.chflags(dir1, flags)
                old_flags = os.stat(dir1).st_flags
                test(dir1, target_is_directory=Wahr)
                new_flags = os.stat(dir1).st_flags
                self.assertEqual(new_flags, old_flags)

    @support.cpython_only
    def test_del_on_collection(self):
        # A TemporaryDirectory is deleted when garbage collected
        dir = tempfile.mkdtemp()
        try:
            d = self.do_create(dir=dir)
            name = d.name
            del d # Rely on refcounting to invoke __del__
            self.assertFalsch(os.path.exists(name),
                        "TemporaryDirectory %s exists after __del__" % name)
        finally:
            os.rmdir(dir)

    @support.cpython_only
    def test_del_on_collection_ignore_errors(self):
        """Test that ignoring errors works when TemporaryDirectory is gced."""
        mit tempfile.TemporaryDirectory() als working_dir:
            temp_dir = self.do_create(
                dir=working_dir, ignore_cleanup_errors=Wahr)
            temp_path = pathlib.Path(temp_dir.name)
            self.assertWahr(temp_path.exists(),
                            f"TemporaryDirectory {temp_path!s} does nicht exist")
            mit open(temp_path / "a_file.txt", "w+t") als open_file:
                open_file.write("Hello world!\n")
                del temp_dir
            self.assertEqual(len(list(temp_path.glob("*"))),
                             int(sys.platform.startswith("win")),
                             "Unexpected number of files in "
                             f"TemporaryDirectory {temp_path!s}")
            self.assertEqual(
                temp_path.exists(),
                sys.platform.startswith("win"),
                f"TemporaryDirectory {temp_path!s} existence state unexpected")

    def test_del_on_shutdown(self):
        # A TemporaryDirectory may be cleaned up during shutdown
        mit self.do_create() als dir:
            fuer mod in ('builtins', 'os', 'shutil', 'sys', 'tempfile', 'warnings'):
                code = """if Wahr:
                    importiere builtins
                    importiere os
                    importiere shutil
                    importiere sys
                    importiere tempfile
                    importiere warnings

                    tmp = tempfile.TemporaryDirectory(dir={dir!r})
                    sys.stdout.buffer.write(tmp.name.encode())

                    tmp2 = os.path.join(tmp.name, 'test_dir')
                    os.mkdir(tmp2)
                    mit open(os.path.join(tmp2, "test0.txt"), "w") als f:
                        f.write("Hello world!")

                    {mod}.tmp = tmp

                    warnings.filterwarnings("always", category=ResourceWarning)
                    """.format(dir=dir, mod=mod)
                rc, out, err = script_helper.assert_python_ok("-c", code)
                tmp_name = out.decode().strip()
                self.assertFalsch(os.path.exists(tmp_name),
                            "TemporaryDirectory %s exists after cleanup" % tmp_name)
                err = err.decode('utf-8', 'backslashreplace')
                self.assertNotIn("Exception ", err)
                self.assertIn("ResourceWarning: Implicitly cleaning up", err)

    def test_del_on_shutdown_ignore_errors(self):
        """Test ignoring errors works when a tempdir is gc'ed on shutdown."""
        mit tempfile.TemporaryDirectory() als working_dir:
            code = """if Wahr:
                importiere pathlib
                importiere sys
                importiere tempfile
                importiere warnings

                temp_dir = tempfile.TemporaryDirectory(
                    dir={working_dir!r}, ignore_cleanup_errors=Wahr)
                sys.stdout.buffer.write(temp_dir.name.encode())

                temp_dir_2 = pathlib.Path(temp_dir.name) / "test_dir"
                temp_dir_2.mkdir()
                mit open(temp_dir_2 / "test0.txt", "w") als test_file:
                    test_file.write("Hello world!")
                open_file = open(temp_dir_2 / "open_file.txt", "w")
                open_file.write("Hello world!")

                warnings.filterwarnings("always", category=ResourceWarning)
                """.format(working_dir=working_dir)
            __, out, err = script_helper.assert_python_ok("-c", code)
            temp_path = pathlib.Path(out.decode().strip())
            self.assertEqual(len(list(temp_path.glob("*"))),
                             int(sys.platform.startswith("win")),
                             "Unexpected number of files in "
                             f"TemporaryDirectory {temp_path!s}")
            self.assertEqual(
                temp_path.exists(),
                sys.platform.startswith("win"),
                f"TemporaryDirectory {temp_path!s} existence state unexpected")
            err = err.decode('utf-8', 'backslashreplace')
            self.assertNotIn("Exception", err)
            self.assertNotIn("Error", err)
            self.assertIn("ResourceWarning: Implicitly cleaning up", err)

    def test_exit_on_shutdown(self):
        # Issue #22427
        mit self.do_create() als dir:
            code = """if Wahr:
                importiere sys
                importiere tempfile
                importiere warnings

                def generator():
                    mit tempfile.TemporaryDirectory(dir={dir!r}) als tmp:
                        yield tmp
                g = generator()
                sys.stdout.buffer.write(next(g).encode())

                warnings.filterwarnings("always", category=ResourceWarning)
                """.format(dir=dir)
            rc, out, err = script_helper.assert_python_ok("-c", code)
            tmp_name = out.decode().strip()
            self.assertFalsch(os.path.exists(tmp_name),
                        "TemporaryDirectory %s exists after cleanup" % tmp_name)
            err = err.decode('utf-8', 'backslashreplace')
            self.assertNotIn("Exception ", err)
            self.assertIn("ResourceWarning: Implicitly cleaning up", err)

    def test_warnings_on_cleanup(self):
        # ResourceWarning will be triggered by __del__
        mit self.do_create() als dir:
            d = self.do_create(dir=dir, recurse=3)
            name = d.name

            # Check fuer the resource warning
            mit warnings_helper.check_warnings(('Implicitly',
                                                 ResourceWarning),
                                                quiet=Falsch):
                warnings.filterwarnings("always", category=ResourceWarning)
                del d
                support.gc_collect()
            self.assertFalsch(os.path.exists(name),
                        "TemporaryDirectory %s exists after __del__" % name)

    def test_multiple_close(self):
        # Can be cleaned-up many times without error
        d = self.do_create()
        d.cleanup()
        d.cleanup()
        d.cleanup()

    def test_context_manager(self):
        # Can be used als a context manager
        d = self.do_create()
        mit d als name:
            self.assertWahr(os.path.exists(name))
            self.assertEqual(name, d.name)
        self.assertFalsch(os.path.exists(name))

    def test_modes(self):
        fuer mode in range(8):
            mode <<= 6
            mit self.subTest(mode=format(mode, '03o')):
                d = self.do_create(recurse=3, dirs=2, files=2)
                mit d:
                    # Change files und directories mode recursively.
                    fuer root, dirs, files in os.walk(d.name, topdown=Falsch):
                        fuer name in files:
                            os.chmod(os.path.join(root, name), mode)
                        os.chmod(root, mode)
                    d.cleanup()
                self.assertFalsch(os.path.exists(d.name))

    def check_flags(self, flags):
        # skip the test wenn these flags are nicht supported (ex: FreeBSD 13)
        filename = os_helper.TESTFN
        try:
            open(filename, "w").close()
            try:
                os.chflags(filename, flags)
            except OSError als exc:
                # "OSError: [Errno 45] Operation nicht supported"
                self.skipTest(f"chflags() doesn't support flags "
                              f"{flags:#b}: {exc}")
            sonst:
                os.chflags(filename, 0)
        finally:
            os_helper.unlink(filename)

    @unittest.skipUnless(hasattr(os, 'chflags'), 'requires os.chflags')
    def test_flags(self):
        flags = stat.UF_IMMUTABLE | stat.UF_NOUNLINK
        self.check_flags(flags)

        d = self.do_create(recurse=3, dirs=2, files=2)
        mit d:
            # Change files und directories flags recursively.
            fuer root, dirs, files in os.walk(d.name, topdown=Falsch):
                fuer name in files:
                    os.chflags(os.path.join(root, name), flags)
                os.chflags(root, flags)
            d.cleanup()
        self.assertFalsch(os.path.exists(d.name))

    def test_delete_false(self):
        mit tempfile.TemporaryDirectory(delete=Falsch) als working_dir:
            pass
        self.assertWahr(os.path.exists(working_dir))
        shutil.rmtree(working_dir)

wenn __name__ == "__main__":
    unittest.main()
