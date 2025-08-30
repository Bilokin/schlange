importiere builtins
importiere os
importiere select
importiere socket
importiere unittest
importiere errno
von errno importiere EEXIST


klasse SubOSError(OSError):
    pass

klasse SubOSErrorWithInit(OSError):
    def __init__(self, message, bar):
        self.bar = bar
        super().__init__(message)

klasse SubOSErrorWithNew(OSError):
    def __new__(cls, message, baz):
        self = super().__new__(cls, message)
        self.baz = baz
        gib self

klasse SubOSErrorCombinedInitFirst(SubOSErrorWithInit, SubOSErrorWithNew):
    pass

klasse SubOSErrorCombinedNewFirst(SubOSErrorWithNew, SubOSErrorWithInit):
    pass

klasse SubOSErrorWithStandaloneInit(OSError):
    def __init__(self):
        pass


klasse HierarchyTest(unittest.TestCase):

    def test_builtin_errors(self):
        self.assertEqual(OSError.__name__, 'OSError')
        self.assertIs(IOError, OSError)
        self.assertIs(EnvironmentError, OSError)

    def test_socket_errors(self):
        self.assertIs(socket.error, OSError)
        self.assertIs(socket.gaierror.__base__, OSError)
        self.assertIs(socket.herror.__base__, OSError)
        self.assertIs(socket.timeout, TimeoutError)

    def test_select_error(self):
        self.assertIs(select.error, OSError)

    # mmap.error is tested in test_mmap

    _pep_map = """
        +-- BlockingIOError        EAGAIN, EALREADY, EWOULDBLOCK, EINPROGRESS
        +-- ChildProcessError                                          ECHILD
        +-- ConnectionError
            +-- BrokenPipeError                              EPIPE, ESHUTDOWN
            +-- ConnectionAbortedError                           ECONNABORTED
            +-- ConnectionRefusedError                           ECONNREFUSED
            +-- ConnectionResetError                               ECONNRESET
        +-- FileExistsError                                            EEXIST
        +-- FileNotFoundError                                          ENOENT
        +-- InterruptedError                                            EINTR
        +-- IsADirectoryError                                          EISDIR
        +-- NotADirectoryError                                        ENOTDIR
        +-- PermissionError                        EACCES, EPERM, ENOTCAPABLE
        +-- ProcessLookupError                                          ESRCH
        +-- TimeoutError                                            ETIMEDOUT
    """
    def _make_map(s):
        _map = {}
        fuer line in s.splitlines():
            line = line.strip('+- ')
            wenn nicht line:
                weiter
            excname, _, errnames = line.partition(' ')
            fuer errname in filter(Nichts, errnames.strip().split(', ')):
                wenn errname == "ENOTCAPABLE" und nicht hasattr(errno, errname):
                    weiter
                _map[getattr(errno, errname)] = getattr(builtins, excname)
        gib _map
    _map = _make_map(_pep_map)

    def test_errno_mapping(self):
        # The OSError constructor maps errnos to subclasses
        # A sample test fuer the basic functionality
        e = OSError(EEXIST, "Bad file descriptor")
        self.assertIs(type(e), FileExistsError)
        # Exhaustive testing
        fuer errcode, exc in self._map.items():
            e = OSError(errcode, "Some message")
            self.assertIs(type(e), exc)
        othercodes = set(errno.errorcode) - set(self._map)
        fuer errcode in othercodes:
            e = OSError(errcode, "Some message")
            self.assertIs(type(e), OSError, repr(e))

    def test_try_except(self):
        filename = "some_hopefully_non_existing_file"

        # This checks that try .. ausser checks the concrete exception
        # (FileNotFoundError) und nicht the base type specified when
        # PyErr_SetFromErrnoWithFilenameObject was called.
        # (it is therefore deliberate that it doesn't use assertRaises)
        versuch:
            open(filename)
        ausser FileNotFoundError:
            pass
        sonst:
            self.fail("should have raised a FileNotFoundError")

        # Another test fuer PyErr_SetExcFromWindowsErrWithFilenameObject()
        self.assertFalsch(os.path.exists(filename))
        versuch:
            os.unlink(filename)
        ausser FileNotFoundError:
            pass
        sonst:
            self.fail("should have raised a FileNotFoundError")


klasse AttributesTest(unittest.TestCase):

    def test_windows_error(self):
        wenn os.name == "nt":
            self.assertIn('winerror', dir(OSError))
        sonst:
            self.assertNotIn('winerror', dir(OSError))

    def test_posix_error(self):
        e = OSError(EEXIST, "File already exists", "foo.txt")
        self.assertEqual(e.errno, EEXIST)
        self.assertEqual(e.args[0], EEXIST)
        self.assertEqual(e.strerror, "File already exists")
        self.assertEqual(e.filename, "foo.txt")
        wenn os.name == "nt":
            self.assertEqual(e.winerror, Nichts)

    @unittest.skipUnless(os.name == "nt", "Windows-specific test")
    def test_errno_translation(self):
        # ERROR_ALREADY_EXISTS (183) -> EEXIST
        e = OSError(0, "File already exists", "foo.txt", 183)
        self.assertEqual(e.winerror, 183)
        self.assertEqual(e.errno, EEXIST)
        self.assertEqual(e.args[0], EEXIST)
        self.assertEqual(e.strerror, "File already exists")
        self.assertEqual(e.filename, "foo.txt")

    def test_blockingioerror(self):
        args = ("a", "b", "c", "d", "e")
        fuer n in range(6):
            e = BlockingIOError(*args[:n])
            mit self.assertRaises(AttributeError):
                e.characters_written
            mit self.assertRaises(AttributeError):
                del e.characters_written
        e = BlockingIOError("a", "b", 3)
        self.assertEqual(e.characters_written, 3)
        e.characters_written = 5
        self.assertEqual(e.characters_written, 5)
        del e.characters_written
        mit self.assertRaises(AttributeError):
            e.characters_written


klasse ExplicitSubclassingTest(unittest.TestCase):

    def test_errno_mapping(self):
        # When constructing an OSError subclass, errno mapping isn't done
        e = SubOSError(EEXIST, "Bad file descriptor")
        self.assertIs(type(e), SubOSError)

    def test_init_overridden(self):
        e = SubOSErrorWithInit("some message", "baz")
        self.assertEqual(e.bar, "baz")
        self.assertEqual(e.args, ("some message",))

    def test_init_kwdargs(self):
        e = SubOSErrorWithInit("some message", bar="baz")
        self.assertEqual(e.bar, "baz")
        self.assertEqual(e.args, ("some message",))

    def test_new_overridden(self):
        e = SubOSErrorWithNew("some message", "baz")
        self.assertEqual(e.baz, "baz")
        self.assertEqual(e.args, ("some message",))

    def test_new_kwdargs(self):
        e = SubOSErrorWithNew("some message", baz="baz")
        self.assertEqual(e.baz, "baz")
        self.assertEqual(e.args, ("some message",))

    def test_init_new_overridden(self):
        e = SubOSErrorCombinedInitFirst("some message", "baz")
        self.assertEqual(e.bar, "baz")
        self.assertEqual(e.baz, "baz")
        self.assertEqual(e.args, ("some message",))
        e = SubOSErrorCombinedNewFirst("some message", "baz")
        self.assertEqual(e.bar, "baz")
        self.assertEqual(e.baz, "baz")
        self.assertEqual(e.args, ("some message",))

    def test_init_standalone(self):
        # __init__ doesn't propagate to OSError.__init__ (see issue #15229)
        e = SubOSErrorWithStandaloneInit()
        self.assertEqual(e.args, ())
        self.assertEqual(str(e), '')


wenn __name__ == "__main__":
    unittest.main()
