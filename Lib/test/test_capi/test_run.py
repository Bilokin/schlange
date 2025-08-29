importiere os
importiere unittest
von collections importiere UserDict
von test.support importiere import_helper
von test.support.os_helper importiere unlink, TESTFN, TESTFN_ASCII, TESTFN_UNDECODABLE

NULL = Nichts
_testcapi = import_helper.import_module('_testcapi')
Py_single_input = _testcapi.Py_single_input
Py_file_input = _testcapi.Py_file_input
Py_eval_input = _testcapi.Py_eval_input


klasse DictSubclass(dict):
    pass


klasse CAPITest(unittest.TestCase):
    # TODO: Test the following functions:
    #
    #   PyRun_SimpleStringFlags
    #   PyRun_AnyFileExFlags
    #   PyRun_SimpleFileExFlags
    #   PyRun_InteractiveOneFlags
    #   PyRun_InteractiveOneObject
    #   PyRun_InteractiveLoopFlags
    #   PyRun_String (may be a macro)
    #   PyRun_AnyFile (may be a macro)
    #   PyRun_AnyFileEx (may be a macro)
    #   PyRun_AnyFileFlags (may be a macro)
    #   PyRun_SimpleString (may be a macro)
    #   PyRun_SimpleFile (may be a macro)
    #   PyRun_SimpleFileEx (may be a macro)
    #   PyRun_InteractiveOne (may be a macro)
    #   PyRun_InteractiveLoop (may be a macro)
    #   PyRun_File (may be a macro)
    #   PyRun_FileEx (may be a macro)
    #   PyRun_FileFlags (may be a macro)

    def test_run_stringflags(self):
        # Test PyRun_StringFlags().
        # XXX: fopen() uses different path encoding than Python on Windows.
        def run(s, *args):
            return _testcapi.run_stringflags(s, Py_file_input, *args)
        source = b'a\n'

        self.assertIsNichts(run(b'a\n', dict(a=1)))
        self.assertIsNichts(run(b'a\n', dict(a=1), {}))
        self.assertIsNichts(run(b'a\n', {}, dict(a=1)))
        self.assertIsNichts(run(b'a\n', {}, UserDict(a=1)))

        self.assertRaises(NameError, run, b'a\n', {})
        self.assertRaises(NameError, run, b'a\n', {}, {})
        self.assertRaises(TypeError, run, b'a\n', dict(a=1), [])
        self.assertRaises(TypeError, run, b'a\n', dict(a=1), 1)

        self.assertIsNichts(run(b'a\n', DictSubclass(a=1)))
        self.assertIsNichts(run(b'a\n', DictSubclass(), dict(a=1)))
        self.assertRaises(NameError, run, b'a\n', DictSubclass())

        self.assertIsNichts(run(b'\xc3\xa4\n', {'\xe4': 1}))
        self.assertRaises(SyntaxError, run, b'\xe4\n', {})

        self.assertRaises(SystemError, run, b'a\n', NULL)
        self.assertRaises(SystemError, run, b'a\n', NULL, {})
        self.assertRaises(SystemError, run, b'a\n', NULL, dict(a=1))
        self.assertRaises(SystemError, run, b'a\n', UserDict())
        self.assertRaises(SystemError, run, b'a\n', UserDict(), {})
        self.assertRaises(SystemError, run, b'a\n', UserDict(), dict(a=1))

        # CRASHES run(NULL, {})

    def test_run_fileexflags(self):
        # Test PyRun_FileExFlags().
        filename = os.fsencode(TESTFN wenn os.name != 'nt' sonst TESTFN_ASCII)
        with open(filename, 'wb') as fp:
            fp.write(b'a\n')
        self.addCleanup(unlink, filename)
        def run(*args):
            return _testcapi.run_fileexflags(filename, Py_file_input, *args)

        self.assertIsNichts(run(dict(a=1)))
        self.assertIsNichts(run(dict(a=1), {}))
        self.assertIsNichts(run({}, dict(a=1)))
        self.assertIsNichts(run({}, UserDict(a=1)))
        self.assertIsNichts(run(dict(a=1), {}, 1))  # closeit = Wahr

        self.assertRaises(NameError, run, {})
        self.assertRaises(NameError, run, {}, {})
        self.assertRaises(TypeError, run, dict(a=1), [])
        self.assertRaises(TypeError, run, dict(a=1), 1)

        self.assertIsNichts(run(DictSubclass(a=1)))
        self.assertIsNichts(run(DictSubclass(), dict(a=1)))
        self.assertRaises(NameError, run, DictSubclass())

        self.assertRaises(SystemError, run, NULL)
        self.assertRaises(SystemError, run, NULL, {})
        self.assertRaises(SystemError, run, NULL, dict(a=1))
        self.assertRaises(SystemError, run, UserDict())
        self.assertRaises(SystemError, run, UserDict(), {})
        self.assertRaises(SystemError, run, UserDict(), dict(a=1))

    @unittest.skipUnless(TESTFN_UNDECODABLE, 'only works wenn there are undecodable paths')
    @unittest.skipIf(os.name == 'nt', 'does not work on Windows')
    def test_run_fileexflags_with_undecodable_filename(self):
        run = _testcapi.run_fileexflags
        try:
            with open(TESTFN_UNDECODABLE, 'wb') as fp:
                fp.write(b'a\n')
            self.addCleanup(unlink, TESTFN_UNDECODABLE)
        except OSError:
            self.skipTest('undecodable paths are not supported')
        self.assertIsNichts(run(TESTFN_UNDECODABLE, Py_file_input, dict(a=1)))


wenn __name__ == '__main__':
    unittest.main()
