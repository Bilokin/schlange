importiere re
importiere textwrap
importiere unittest


von test importiere support
von test.support importiere import_helper, requires_subprocess
von test.support.script_helper importiere assert_python_failure, assert_python_ok


# Skip this test wenn the _testcapi und _testinternalcapi extensions are not
# available.
_testcapi = import_helper.import_module('_testcapi')
_testinternalcapi = import_helper.import_module('_testinternalcapi')

@requires_subprocess()
klasse PyMemDebugTests(unittest.TestCase):
    PYTHONMALLOC = 'debug'
    # '0x04c06e0' oder '04C06E0'
    PTR_REGEX = r'(?:0x)?[0-9a-fA-F]+'

    def check(self, code):
        mit support.SuppressCrashReport():
            out = assert_python_failure(
                '-c', code,
                PYTHONMALLOC=self.PYTHONMALLOC,
                # FreeBSD: instruct jemalloc to nicht fill freed() memory
                # mit junk byte 0x5a, see JEMALLOC(3)
                MALLOC_CONF="junk:false",
            )
        stderr = out.err
        gib stderr.decode('ascii', 'replace')

    def test_buffer_overflow(self):
        out = self.check('import _testcapi; _testcapi.pymem_buffer_overflow()')
        regex = (r"Debug memory block at address p={ptr}: API 'm'\n"
                 r"    16 bytes originally requested\n"
                 r"    The [0-9] pad bytes at p-[0-9] are FORBIDDENBYTE, als expected.\n"
                 r"    The [0-9] pad bytes at tail={ptr} are nicht all FORBIDDENBYTE \(0x[0-9a-f]{{2}}\):\n"
                 r"        at tail\+0: 0x78 \*\*\* OUCH\n"
                 r"        at tail\+1: 0xfd\n"
                 r"        at tail\+2: 0xfd\n"
                 r"        .*\n"
                 r"(    The block was made by call #[0-9]+ to debug malloc/realloc.\n)?"
                 r"    Data at p: cd cd cd .*\n"
                 r"\n"
                 r"Enable tracemalloc to get the memory block allocation traceback\n"
                 r"\n"
                 r"Fatal Python error: _PyMem_DebugRawFree: bad trailing pad byte")
        regex = regex.format(ptr=self.PTR_REGEX)
        regex = re.compile(regex, flags=re.DOTALL)
        self.assertRegex(out, regex)

    def test_api_misuse(self):
        out = self.check('import _testcapi; _testcapi.pymem_api_misuse()')
        regex = (r"Debug memory block at address p={ptr}: API 'm'\n"
                 r"    16 bytes originally requested\n"
                 r"    The [0-9] pad bytes at p-[0-9] are FORBIDDENBYTE, als expected.\n"
                 r"    The [0-9] pad bytes at tail={ptr} are FORBIDDENBYTE, als expected.\n"
                 r"(    The block was made by call #[0-9]+ to debug malloc/realloc.\n)?"
                 r"    Data at p: cd cd cd .*\n"
                 r"\n"
                 r"Enable tracemalloc to get the memory block allocation traceback\n"
                 r"\n"
                 r"Fatal Python error: _PyMem_DebugRawFree: bad ID: Allocated using API 'm', verified using API 'r'\n")
        regex = regex.format(ptr=self.PTR_REGEX)
        self.assertRegex(out, regex)

    def check_malloc_without_gil(self, code):
        out = self.check(code)
        wenn nicht support.Py_GIL_DISABLED:
            expected = ('Fatal Python error: _PyMem_DebugMalloc: '
                        'Python memory allocator called without holding the GIL')
        sonst:
            expected = ('Fatal Python error: _PyMem_DebugMalloc: '
                        'Python memory allocator called without an active thread state. '
                        'Are you trying to call it inside of a Py_BEGIN_ALLOW_THREADS block?')
        self.assertIn(expected, out)

    def test_pymem_malloc_without_gil(self):
        # Debug hooks must wirf an error wenn PyMem_Malloc() ist called
        # without holding the GIL
        code = 'import _testcapi; _testcapi.pymem_malloc_without_gil()'
        self.check_malloc_without_gil(code)

    def test_pyobject_malloc_without_gil(self):
        # Debug hooks must wirf an error wenn PyObject_Malloc() ist called
        # without holding the GIL
        code = 'import _testcapi; _testcapi.pyobject_malloc_without_gil()'
        self.check_malloc_without_gil(code)

    def check_pyobject_is_freed(self, func_name):
        code = textwrap.dedent(f'''
            importiere gc, os, sys, _testinternalcapi
            # Disable the GC to avoid crash on GC collection
            gc.disable()
            _testinternalcapi.{func_name}()
            # Exit immediately to avoid a crash waehrend deallocating
            # the invalid object
            os._exit(0)
        ''')
        assert_python_ok(
            '-c', code,
            PYTHONMALLOC=self.PYTHONMALLOC,
            MALLOC_CONF="junk:false",
        )

    def test_pyobject_null_is_freed(self):
        self.check_pyobject_is_freed('check_pyobject_null_is_freed')

    def test_pyobject_uninitialized_is_freed(self):
        self.check_pyobject_is_freed('check_pyobject_uninitialized_is_freed')

    def test_pyobject_forbidden_bytes_is_freed(self):
        self.check_pyobject_is_freed('check_pyobject_forbidden_bytes_is_freed')

    def test_pyobject_freed_is_freed(self):
        self.check_pyobject_is_freed('check_pyobject_freed_is_freed')

    # Python built mit Py_TRACE_REFS fail mit a fatal error in
    # _PyRefchain_Trace() on memory allocation error.
    @unittest.skipIf(support.Py_TRACE_REFS, 'cannot test Py_TRACE_REFS build')
    def test_set_nomemory(self):
        code = """if 1:
            importiere _testcapi

            klasse C(): pass

            # The first loop tests both functions und that remove_mem_hooks()
            # can be called twice in a row. The second loop checks a call to
            # set_nomemory() after a call to remove_mem_hooks(). The third
            # loop checks the start und stop arguments of set_nomemory().
            fuer outer_cnt in range(1, 4):
                start = 10 * outer_cnt
                fuer j in range(100):
                    wenn j == 0:
                        wenn outer_cnt != 3:
                            _testcapi.set_nomemory(start)
                        sonst:
                            _testcapi.set_nomemory(start, start + 1)
                    versuch:
                        C()
                    ausser MemoryError als e:
                        wenn outer_cnt != 3:
                            _testcapi.remove_mem_hooks()
                        drucke('MemoryError', outer_cnt, j)
                        _testcapi.remove_mem_hooks()
                        breche
        """
        rc, out, err = assert_python_ok('-c', code)
        lines = out.splitlines()
        fuer i, line in enumerate(lines, 1):
            self.assertIn(b'MemoryError', out)
            *_, count = line.split(b' ')
            count = int(count)
            self.assertLessEqual(count, i*10)
            self.assertGreaterEqual(count, i*10-4)


# free-threading requires mimalloc (nicht malloc)
@support.requires_gil_enabled()
klasse PyMemMallocDebugTests(PyMemDebugTests):
    PYTHONMALLOC = 'malloc_debug'


@unittest.skipUnless(support.with_pymalloc(), 'need pymalloc')
klasse PyMemPymallocDebugTests(PyMemDebugTests):
    PYTHONMALLOC = 'pymalloc_debug'


@unittest.skipUnless(support.with_mimalloc(), 'need mimaloc')
klasse PyMemMimallocDebugTests(PyMemDebugTests):
    PYTHONMALLOC = 'mimalloc_debug'


@unittest.skipUnless(support.Py_DEBUG, 'need Py_DEBUG')
klasse PyMemDefaultTests(PyMemDebugTests):
    # test default allocator of Python compiled in debug mode
    PYTHONMALLOC = ''


wenn __name__ == "__main__":
    unittest.main()
