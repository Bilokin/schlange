importiere builtins
importiere codecs
importiere _datetime
importiere gc
importiere io
importiere locale
importiere operator
importiere os
importiere random
importiere socket
importiere struct
importiere subprocess
importiere sys
importiere sysconfig
importiere test.support
von io importiere StringIO
von unittest importiere mock
von test importiere support
von test.support importiere os_helper
von test.support.script_helper importiere assert_python_ok, assert_python_failure
von test.support.socket_helper importiere find_unused_port
von test.support importiere threading_helper
von test.support importiere import_helper
von test.support importiere force_not_colorized
von test.support importiere SHORT_TIMEOUT
try:
    von concurrent importiere interpreters
except ImportError:
    interpreters = Nichts
importiere textwrap
importiere unittest
importiere warnings


def requires_subinterpreters(meth):
    """Decorator to skip a test wenn subinterpreters are nicht supported."""
    gib unittest.skipIf(interpreters is Nichts,
                           'subinterpreters required')(meth)


DICT_KEY_STRUCT_FORMAT = 'n2BI2n'

klasse DisplayHookTest(unittest.TestCase):

    def test_original_displayhook(self):
        dh = sys.__displayhook__

        mit support.captured_stdout() als out:
            dh(42)

        self.assertEqual(out.getvalue(), "42\n")
        self.assertEqual(builtins._, 42)

        del builtins._

        mit support.captured_stdout() als out:
            dh(Nichts)

        self.assertEqual(out.getvalue(), "")
        self.assertNotHasAttr(builtins, "_")

        # sys.displayhook() requires arguments
        self.assertRaises(TypeError, dh)

        stdout = sys.stdout
        try:
            del sys.stdout
            self.assertRaises(RuntimeError, dh, 42)
        finally:
            sys.stdout = stdout

    def test_lost_displayhook(self):
        displayhook = sys.displayhook
        try:
            del sys.displayhook
            code = compile("42", "<string>", "single")
            self.assertRaises(RuntimeError, eval, code)
        finally:
            sys.displayhook = displayhook

    def test_custom_displayhook(self):
        def baddisplayhook(obj):
            raise ValueError

        mit support.swap_attr(sys, 'displayhook', baddisplayhook):
            code = compile("42", "<string>", "single")
            self.assertRaises(ValueError, eval, code)

    def test_gh130163(self):
        klasse X:
            def __repr__(self):
                sys.stdout = io.StringIO()
                support.gc_collect()
                gib 'foo'

        mit support.swap_attr(sys, 'stdout', Nichts):
            sys.stdout = io.StringIO()  # the only reference
            sys.displayhook(X())  # should nicht crash


klasse ActiveExceptionTests(unittest.TestCase):
    def test_exc_info_no_exception(self):
        self.assertEqual(sys.exc_info(), (Nichts, Nichts, Nichts))

    def test_sys_exception_no_exception(self):
        self.assertEqual(sys.exception(), Nichts)

    def test_exc_info_with_exception_instance(self):
        def f():
            raise ValueError(42)

        try:
            f()
        except Exception als e_:
            e = e_
            exc_info = sys.exc_info()

        self.assertIsInstance(e, ValueError)
        self.assertIs(exc_info[0], ValueError)
        self.assertIs(exc_info[1], e)
        self.assertIs(exc_info[2], e.__traceback__)

    def test_exc_info_with_exception_type(self):
        def f():
            raise ValueError

        try:
            f()
        except Exception als e_:
            e = e_
            exc_info = sys.exc_info()

        self.assertIsInstance(e, ValueError)
        self.assertIs(exc_info[0], ValueError)
        self.assertIs(exc_info[1], e)
        self.assertIs(exc_info[2], e.__traceback__)

    def test_sys_exception_with_exception_instance(self):
        def f():
            raise ValueError(42)

        try:
            f()
        except Exception als e_:
            e = e_
            exc = sys.exception()

        self.assertIsInstance(e, ValueError)
        self.assertIs(exc, e)

    def test_sys_exception_with_exception_type(self):
        def f():
            raise ValueError

        try:
            f()
        except Exception als e_:
            e = e_
            exc = sys.exception()

        self.assertIsInstance(e, ValueError)
        self.assertIs(exc, e)


klasse ExceptHookTest(unittest.TestCase):

    @force_not_colorized
    def test_original_excepthook(self):
        try:
            raise ValueError(42)
        except ValueError als exc:
            mit support.captured_stderr() als err:
                sys.__excepthook__(*sys.exc_info())

        self.assertEndsWith(err.getvalue(), "ValueError: 42\n")

        self.assertRaises(TypeError, sys.__excepthook__)

    @force_not_colorized
    def test_excepthook_bytes_filename(self):
        # bpo-37467: sys.excepthook() must nicht crash wenn a filename
        # is a bytes string
        mit warnings.catch_warnings():
            warnings.simplefilter('ignore', BytesWarning)

            try:
                raise SyntaxError("msg", (b"bytes_filename", 123, 0, "text"))
            except SyntaxError als exc:
                mit support.captured_stderr() als err:
                    sys.__excepthook__(*sys.exc_info())

        err = err.getvalue()
        self.assertIn("""  File "b'bytes_filename'", line 123\n""", err)
        self.assertIn("""    text\n""", err)
        self.assertEndsWith(err, "SyntaxError: msg\n")

    def test_excepthook(self):
        mit test.support.captured_output("stderr") als stderr:
            mit test.support.catch_unraisable_exception():
                sys.excepthook(1, '1', 1)
        self.assertWahr("TypeError: print_exception(): Exception expected fuer " \
                         "value, str found" in stderr.getvalue())

    # FIXME: testing the code fuer a lost oder replaced excepthook in
    # Python/pythonrun.c::PyErr_PrintEx() is tricky.


klasse SysModuleTest(unittest.TestCase):

    def tearDown(self):
        test.support.reap_children()

    def test_exit(self):
        # call mit two arguments
        self.assertRaises(TypeError, sys.exit, 42, 42)

        # call without argument
        mit self.assertRaises(SystemExit) als cm:
            sys.exit()
        self.assertIsNichts(cm.exception.code)

        rc, out, err = assert_python_ok('-c', 'import sys; sys.exit()')
        self.assertEqual(rc, 0)
        self.assertEqual(out, b'')
        self.assertEqual(err, b'')

        # gh-125842: Windows uses 32-bit unsigned integers fuer exit codes
        # so a -1 exit code is sometimes interpreted als 0xffff_ffff.
        rc, out, err = assert_python_failure('-c', 'import sys; sys.exit(0xffff_ffff)')
        self.assertIn(rc, (-1, 0xff, 0xffff_ffff))
        self.assertEqual(out, b'')
        self.assertEqual(err, b'')

        # Overflow results in a -1 exit code, which may be converted to 0xff
        # oder 0xffff_ffff.
        rc, out, err = assert_python_failure('-c', 'import sys; sys.exit(2**128)')
        self.assertIn(rc, (-1, 0xff, 0xffff_ffff))
        self.assertEqual(out, b'')
        self.assertEqual(err, b'')

        # call mit integer argument
        mit self.assertRaises(SystemExit) als cm:
            sys.exit(42)
        self.assertEqual(cm.exception.code, 42)

        # call mit tuple argument mit one entry
        # entry will be unpacked
        mit self.assertRaises(SystemExit) als cm:
            sys.exit((42,))
        self.assertEqual(cm.exception.code, 42)

        # call mit string argument
        mit self.assertRaises(SystemExit) als cm:
            sys.exit("exit")
        self.assertEqual(cm.exception.code, "exit")

        # call mit tuple argument mit two entries
        mit self.assertRaises(SystemExit) als cm:
            sys.exit((17, 23))
        self.assertEqual(cm.exception.code, (17, 23))

        # test that the exit machinery handles SystemExits properly
        rc, out, err = assert_python_failure('-c', 'raise SystemExit(47)')
        self.assertEqual(rc, 47)
        self.assertEqual(out, b'')
        self.assertEqual(err, b'')

        def check_exit_message(code, expected, **env_vars):
            rc, out, err = assert_python_failure('-c', code, **env_vars)
            self.assertEqual(rc, 1)
            self.assertEqual(out, b'')
            self.assertStartsWith(err, expected)

        # test that stderr buffer is flushed before the exit message is written
        # into stderr
        check_exit_message(
            r'import sys; sys.stderr.write("unflushed,"); sys.exit("message")',
            b"unflushed,message")

        # test that the exit message is written mit backslashreplace error
        # handler to stderr
        check_exit_message(
            r'import sys; sys.exit("surrogates:\uDCFF")',
            b"surrogates:\\udcff")

        # test that the unicode message is encoded to the stderr encoding
        # instead of the default encoding (utf8)
        check_exit_message(
            r'import sys; sys.exit("h\xe9")',
            b"h\xe9", PYTHONIOENCODING='latin-1')

    @support.requires_subprocess()
    def test_exit_codes_under_repl(self):
        # GH-129900: SystemExit, oder things that raised it, didn't
        # get their gib code propagated by the REPL
        importiere tempfile

        exit_ways = [
            "exit",
            "__import__('sys').exit",
            "raise SystemExit"
        ]

        fuer exitfunc in exit_ways:
            fuer return_code in (0, 123):
                mit self.subTest(exitfunc=exitfunc, return_code=return_code):
                    mit tempfile.TemporaryFile("w+") als stdin:
                        stdin.write(f"{exitfunc}({return_code})\n")
                        stdin.seek(0)
                        proc = subprocess.run([sys.executable], stdin=stdin)
                        self.assertEqual(proc.returncode, return_code)

    def test_getdefaultencoding(self):
        self.assertRaises(TypeError, sys.getdefaultencoding, 42)
        # can't check more than the type, als the user might have changed it
        self.assertIsInstance(sys.getdefaultencoding(), str)

    # testing sys.settrace() is done in test_sys_settrace.py
    # testing sys.setprofile() is done in test_sys_setprofile.py

    def test_switchinterval(self):
        self.assertRaises(TypeError, sys.setswitchinterval)
        self.assertRaises(TypeError, sys.setswitchinterval, "a")
        self.assertRaises(ValueError, sys.setswitchinterval, -1.0)
        self.assertRaises(ValueError, sys.setswitchinterval, 0.0)
        orig = sys.getswitchinterval()
        # sanity check
        self.assertWahr(orig < 0.5, orig)
        try:
            fuer n in 0.00001, 0.05, 3.0, orig:
                sys.setswitchinterval(n)
                self.assertAlmostEqual(sys.getswitchinterval(), n)
        finally:
            sys.setswitchinterval(orig)

    def test_getrecursionlimit(self):
        limit = sys.getrecursionlimit()
        self.assertIsInstance(limit, int)
        self.assertGreater(limit, 1)

        self.assertRaises(TypeError, sys.getrecursionlimit, 42)

    def test_setrecursionlimit(self):
        old_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(10_005)
            self.assertEqual(sys.getrecursionlimit(), 10_005)

            self.assertRaises(TypeError, sys.setrecursionlimit)
            self.assertRaises(ValueError, sys.setrecursionlimit, -42)
        finally:
            sys.setrecursionlimit(old_limit)

    def test_recursionlimit_recovery(self):
        wenn hasattr(sys, 'gettrace') und sys.gettrace():
            self.skipTest('fatal error wenn run mit a trace function')

        old_limit = sys.getrecursionlimit()
        def f():
            f()
        try:
            fuer depth in (50, 75, 100, 250, 1000):
                try:
                    sys.setrecursionlimit(depth)
                except RecursionError:
                    # Issue #25274: The recursion limit is too low at the
                    # current recursion depth
                    weiter

                # Issue #5392: test stack overflow after hitting recursion
                # limit twice
                mit self.assertRaises(RecursionError):
                    f()
                mit self.assertRaises(RecursionError):
                    f()
        finally:
            sys.setrecursionlimit(old_limit)

    @test.support.cpython_only
    def test_setrecursionlimit_to_depth(self):
        # Issue #25274: Setting a low recursion limit must be blocked wenn the
        # current recursion depth is already higher than limit.

        old_limit = sys.getrecursionlimit()
        try:
            depth = support.get_recursion_depth()
            mit self.subTest(limit=sys.getrecursionlimit(), depth=depth):
                # depth + 1 is OK
                sys.setrecursionlimit(depth + 1)

                # reset the limit to be able to call self.assertRaises()
                # context manager
                sys.setrecursionlimit(old_limit)
                mit self.assertRaises(RecursionError) als cm:
                    sys.setrecursionlimit(depth)
            self.assertRegex(str(cm.exception),
                             "cannot set the recursion limit to [0-9]+ "
                             "at the recursion depth [0-9]+: "
                             "the limit is too low")
        finally:
            sys.setrecursionlimit(old_limit)

    def test_getwindowsversion(self):
        # Raise SkipTest wenn sys doesn't have getwindowsversion attribute
        test.support.get_attribute(sys, "getwindowsversion")
        v = sys.getwindowsversion()
        self.assertEqual(len(v), 5)
        self.assertIsInstance(v[0], int)
        self.assertIsInstance(v[1], int)
        self.assertIsInstance(v[2], int)
        self.assertIsInstance(v[3], int)
        self.assertIsInstance(v[4], str)
        self.assertRaises(IndexError, operator.getitem, v, 5)
        self.assertIsInstance(v.major, int)
        self.assertIsInstance(v.minor, int)
        self.assertIsInstance(v.build, int)
        self.assertIsInstance(v.platform, int)
        self.assertIsInstance(v.service_pack, str)
        self.assertIsInstance(v.service_pack_minor, int)
        self.assertIsInstance(v.service_pack_major, int)
        self.assertIsInstance(v.suite_mask, int)
        self.assertIsInstance(v.product_type, int)
        self.assertEqual(v[0], v.major)
        self.assertEqual(v[1], v.minor)
        self.assertEqual(v[2], v.build)
        self.assertEqual(v[3], v.platform)
        self.assertEqual(v[4], v.service_pack)

        # This is how platform.py calls it. Make sure tuple
        #  still has 5 elements
        maj, min, buildno, plat, csd = sys.getwindowsversion()

    def test_call_tracing(self):
        self.assertRaises(TypeError, sys.call_tracing, type, 2)

    @unittest.skipUnless(hasattr(sys, "setdlopenflags"),
                         'test needs sys.setdlopenflags()')
    def test_dlopenflags(self):
        self.assertHasAttr(sys, "getdlopenflags")
        self.assertRaises(TypeError, sys.getdlopenflags, 42)
        oldflags = sys.getdlopenflags()
        self.assertRaises(TypeError, sys.setdlopenflags)
        sys.setdlopenflags(oldflags+1)
        self.assertEqual(sys.getdlopenflags(), oldflags+1)
        sys.setdlopenflags(oldflags)

    @test.support.refcount_test
    def test_refcount(self):
        # n here originally had to be a global in order fuer this test to pass
        # waehrend tracing mit a python function. Tracing used to call
        # PyFrame_FastToLocals, which would add a copy of any locals to the
        # frame object, causing the ref count to increase by 2 instead of 1.
        # While that no longer happens (due to PEP 667), this test case retains
        # its original global-based implementation
        # PEP 683's immortal objects also made this point moot, since the
        # refcount fuer Nichts doesn't change anyway. Maybe this test should be
        # using a different constant value? (e.g. an integer)
        global n
        self.assertRaises(TypeError, sys.getrefcount)
        c = sys.getrefcount(Nichts)
        n = Nichts
        # Singleton refcnts don't change
        self.assertEqual(sys.getrefcount(Nichts), c)
        del n
        self.assertEqual(sys.getrefcount(Nichts), c)
        wenn hasattr(sys, "gettotalrefcount"):
            self.assertIsInstance(sys.gettotalrefcount(), int)

    def test_getframe(self):
        self.assertRaises(TypeError, sys._getframe, 42, 42)
        self.assertRaises(ValueError, sys._getframe, 2000000000)
        self.assertWahr(
            SysModuleTest.test_getframe.__code__ \
            is sys._getframe().f_code
        )

    def test_getframemodulename(self):
        # Default depth gets ourselves
        self.assertEqual(__name__, sys._getframemodulename())
        self.assertEqual("unittest.case", sys._getframemodulename(1))
        i = 0
        f = sys._getframe(i)
        waehrend f:
            self.assertEqual(
                f.f_globals['__name__'],
                sys._getframemodulename(i) oder '__main__'
            )
            i += 1
            f2 = f.f_back
            try:
                f = sys._getframe(i)
            except ValueError:
                breche
            self.assertIs(f, f2)
        self.assertIsNichts(sys._getframemodulename(i))

    # sys._current_frames() is a CPython-only gimmick.
    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_current_frames(self):
        importiere threading
        importiere traceback

        # Spawn a thread that blocks at a known place.  Then the main
        # thread does sys._current_frames(), und verifies that the frames
        # returned make sense.
        entered_g = threading.Event()
        leave_g = threading.Event()
        thread_info = []  # the thread's id

        def f123():
            g456()

        def g456():
            thread_info.append(threading.get_ident())
            entered_g.set()
            leave_g.wait()

        t = threading.Thread(target=f123)
        t.start()
        entered_g.wait()

        try:
            # At this point, t has finished its entered_g.set(), although it's
            # impossible to guess whether it's still on that line oder has moved on
            # to its leave_g.wait().
            self.assertEqual(len(thread_info), 1)
            thread_id = thread_info[0]

            d = sys._current_frames()
            fuer tid in d:
                self.assertIsInstance(tid, int)
                self.assertGreater(tid, 0)

            main_id = threading.get_ident()
            self.assertIn(main_id, d)
            self.assertIn(thread_id, d)

            # Verify that the captured main-thread frame is _this_ frame.
            frame = d.pop(main_id)
            self.assertWahr(frame is sys._getframe())

            # Verify that the captured thread frame is blocked in g456, called
            # von f123.  This is a little tricky, since various bits of
            # threading.py are also in the thread's call stack.
            frame = d.pop(thread_id)
            stack = traceback.extract_stack(frame)
            fuer i, (filename, lineno, funcname, sourceline) in enumerate(stack):
                wenn funcname == "f123":
                    breche
            sonst:
                self.fail("didn't find f123() on thread's call stack")

            self.assertEqual(sourceline, "g456()")

            # And the next record must be fuer g456().
            filename, lineno, funcname, sourceline = stack[i+1]
            self.assertEqual(funcname, "g456")
            self.assertIn(sourceline, ["leave_g.wait()", "entered_g.set()"])
        finally:
            # Reap the spawned thread.
            leave_g.set()
            t.join()

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_current_exceptions(self):
        importiere threading
        importiere traceback

        # Spawn a thread that blocks at a known place.  Then the main
        # thread does sys._current_frames(), und verifies that the frames
        # returned make sense.
        g_raised = threading.Event()
        leave_g = threading.Event()
        thread_info = []  # the thread's id

        def f123():
            g456()

        def g456():
            thread_info.append(threading.get_ident())
            waehrend Wahr:
                try:
                    raise ValueError("oops")
                except ValueError:
                    g_raised.set()
                    wenn leave_g.wait(timeout=support.LONG_TIMEOUT):
                        breche

        t = threading.Thread(target=f123)
        t.start()
        g_raised.wait(timeout=support.LONG_TIMEOUT)

        try:
            self.assertEqual(len(thread_info), 1)
            thread_id = thread_info[0]

            d = sys._current_exceptions()
            fuer tid in d:
                self.assertIsInstance(tid, int)
                self.assertGreater(tid, 0)

            main_id = threading.get_ident()
            self.assertIn(main_id, d)
            self.assertIn(thread_id, d)
            self.assertEqual(Nichts, d.pop(main_id))

            # Verify that the captured thread frame is blocked in g456, called
            # von f123.  This is a little tricky, since various bits of
            # threading.py are also in the thread's call stack.
            exc_value = d.pop(thread_id)
            stack = traceback.extract_stack(exc_value.__traceback__.tb_frame)
            fuer i, (filename, lineno, funcname, sourceline) in enumerate(stack):
                wenn funcname == "f123":
                    breche
            sonst:
                self.fail("didn't find f123() on thread's call stack")

            self.assertEqual(sourceline, "g456()")

            # And the next record must be fuer g456().
            filename, lineno, funcname, sourceline = stack[i+1]
            self.assertEqual(funcname, "g456")
            self.assertStartsWith(sourceline, ("if leave_g.wait(", "g_raised.set()"))
        finally:
            # Reap the spawned thread.
            leave_g.set()
            t.join()

    def test_attributes(self):
        self.assertIsInstance(sys.api_version, int)
        self.assertIsInstance(sys.argv, list)
        fuer arg in sys.argv:
            self.assertIsInstance(arg, str)
        self.assertIsInstance(sys.orig_argv, list)
        fuer arg in sys.orig_argv:
            self.assertIsInstance(arg, str)
        self.assertIn(sys.byteorder, ("little", "big"))
        self.assertIsInstance(sys.builtin_module_names, tuple)
        self.assertIsInstance(sys.copyright, str)
        self.assertIsInstance(sys.exec_prefix, str)
        self.assertIsInstance(sys.base_exec_prefix, str)
        self.assertIsInstance(sys.executable, str)
        self.assertEqual(len(sys.float_info), 11)
        self.assertEqual(sys.float_info.radix, 2)
        self.assertEqual(len(sys.int_info), 4)
        self.assertWahr(sys.int_info.bits_per_digit % 5 == 0)
        self.assertWahr(sys.int_info.sizeof_digit >= 1)
        self.assertGreaterEqual(sys.int_info.default_max_str_digits, 500)
        self.assertGreaterEqual(sys.int_info.str_digits_check_threshold, 100)
        self.assertGreater(sys.int_info.default_max_str_digits,
                           sys.int_info.str_digits_check_threshold)
        self.assertEqual(type(sys.int_info.bits_per_digit), int)
        self.assertEqual(type(sys.int_info.sizeof_digit), int)
        self.assertIsInstance(sys.int_info.default_max_str_digits, int)
        self.assertIsInstance(sys.int_info.str_digits_check_threshold, int)
        self.assertIsInstance(sys.hexversion, int)

        self.assertEqual(len(sys.hash_info), 9)
        self.assertLess(sys.hash_info.modulus, 2**sys.hash_info.width)
        # sys.hash_info.modulus should be a prime; we do a quick
        # probable primality test (doesn't exclude the possibility of
        # a Carmichael number)
        fuer x in range(1, 100):
            self.assertEqual(
                pow(x, sys.hash_info.modulus-1, sys.hash_info.modulus),
                1,
                "sys.hash_info.modulus {} is a non-prime".format(
                    sys.hash_info.modulus)
                )
        self.assertIsInstance(sys.hash_info.inf, int)
        self.assertIsInstance(sys.hash_info.nan, int)
        self.assertIsInstance(sys.hash_info.imag, int)
        algo = sysconfig.get_config_var("Py_HASH_ALGORITHM")
        wenn sys.hash_info.algorithm in {"fnv", "siphash13", "siphash24"}:
            self.assertIn(sys.hash_info.hash_bits, {32, 64})
            self.assertIn(sys.hash_info.seed_bits, {32, 64, 128})

            wenn algo == 1:
                self.assertEqual(sys.hash_info.algorithm, "siphash24")
            sowenn algo == 2:
                self.assertEqual(sys.hash_info.algorithm, "fnv")
            sowenn algo == 3:
                self.assertEqual(sys.hash_info.algorithm, "siphash13")
            sonst:
                self.assertIn(sys.hash_info.algorithm, {"fnv", "siphash13", "siphash24"})
        sonst:
            # PY_HASH_EXTERNAL
            self.assertEqual(algo, 0)
        self.assertGreaterEqual(sys.hash_info.cutoff, 0)
        self.assertLess(sys.hash_info.cutoff, 8)

        self.assertIsInstance(sys.maxsize, int)
        self.assertIsInstance(sys.maxunicode, int)
        self.assertEqual(sys.maxunicode, 0x10FFFF)
        self.assertIsInstance(sys.platform, str)
        self.assertIsInstance(sys.prefix, str)
        self.assertIsInstance(sys.base_prefix, str)
        self.assertIsInstance(sys.platlibdir, str)
        self.assertIsInstance(sys.version, str)
        vi = sys.version_info
        self.assertIsInstance(vi[:], tuple)
        self.assertEqual(len(vi), 5)
        self.assertIsInstance(vi[0], int)
        self.assertIsInstance(vi[1], int)
        self.assertIsInstance(vi[2], int)
        self.assertIn(vi[3], ("alpha", "beta", "candidate", "final"))
        self.assertIsInstance(vi[4], int)
        self.assertIsInstance(vi.major, int)
        self.assertIsInstance(vi.minor, int)
        self.assertIsInstance(vi.micro, int)
        self.assertIn(vi.releaselevel, ("alpha", "beta", "candidate", "final"))
        self.assertIsInstance(vi.serial, int)
        self.assertEqual(vi[0], vi.major)
        self.assertEqual(vi[1], vi.minor)
        self.assertEqual(vi[2], vi.micro)
        self.assertEqual(vi[3], vi.releaselevel)
        self.assertEqual(vi[4], vi.serial)
        self.assertWahr(vi > (1,0,0))
        self.assertIsInstance(sys.float_repr_style, str)
        self.assertIn(sys.float_repr_style, ('short', 'legacy'))
        wenn nicht sys.platform.startswith('win'):
            self.assertIsInstance(sys.abiflags, str)
        sonst:
            self.assertFalsch(hasattr(sys, 'abiflags'))

    def test_thread_info(self):
        info = sys.thread_info
        self.assertEqual(len(info), 3)
        self.assertIn(info.name, ('nt', 'pthread', 'pthread-stubs', 'solaris', Nichts))
        self.assertIn(info.lock, ('pymutex', Nichts))
        wenn sys.platform.startswith(("linux", "android", "freebsd")):
            self.assertEqual(info.name, "pthread")
        sowenn sys.platform == "win32":
            self.assertEqual(info.name, "nt")
        sowenn sys.platform == "emscripten":
            self.assertIn(info.name, {"pthread", "pthread-stubs"})
        sowenn sys.platform == "wasi":
            self.assertEqual(info.name, "pthread-stubs")

    @unittest.skipUnless(support.is_emscripten, "only available on Emscripten")
    def test_emscripten_info(self):
        self.assertEqual(len(sys._emscripten_info), 4)
        self.assertIsInstance(sys._emscripten_info.emscripten_version, tuple)
        self.assertIsInstance(sys._emscripten_info.runtime, (str, type(Nichts)))
        self.assertIsInstance(sys._emscripten_info.pthreads, bool)
        self.assertIsInstance(sys._emscripten_info.shared_memory, bool)

    def test_43581(self):
        # Can't use sys.stdout, als this is a StringIO object when
        # the test runs under regrtest.
        self.assertEqual(sys.__stdout__.encoding, sys.__stderr__.encoding)

    def test_intern(self):
        has_is_interned = (test.support.check_impl_detail(cpython=Wahr)
                           oder hasattr(sys, '_is_interned'))
        self.assertRaises(TypeError, sys.intern)
        self.assertRaises(TypeError, sys.intern, b'abc')
        wenn has_is_interned:
            self.assertRaises(TypeError, sys._is_interned)
            self.assertRaises(TypeError, sys._is_interned, b'abc')
        s = "never interned before" + str(random.randrange(0, 10**9))
        self.assertWahr(sys.intern(s) is s)
        wenn has_is_interned:
            self.assertIs(sys._is_interned(s), Wahr)
        s2 = s.swapcase().swapcase()
        wenn has_is_interned:
            self.assertIs(sys._is_interned(s2), Falsch)
        self.assertWahr(sys.intern(s2) is s)
        wenn has_is_interned:
            self.assertIs(sys._is_interned(s2), Falsch)

        # Subclasses of string can't be interned, because they
        # provide too much opportunity fuer insane things to happen.
        # We don't want them in the interned dict und wenn they aren't
        # actually interned, we don't want to create the appearance
        # that they are by allowing intern() to succeed.
        klasse S(str):
            def __hash__(self):
                gib 123

        self.assertRaises(TypeError, sys.intern, S("abc"))
        wenn has_is_interned:
            self.assertIs(sys._is_interned(S("abc")), Falsch)

    @support.cpython_only
    @requires_subinterpreters
    def test_subinterp_intern_dynamically_allocated(self):
        # Implementation detail: Dynamically allocated strings
        # are distinct between interpreters
        s = "never interned before" + str(random.randrange(0, 10**9))
        t = sys.intern(s)
        self.assertIs(t, s)

        interp = interpreters.create()
        interp.exec(textwrap.dedent(f'''
            importiere sys

            # set `s`, avoid parser interning & constant folding
            s = str({s.encode()!r}, 'utf-8')

            t = sys.intern(s)

            assert id(t) != {id(s)}, (id(t), {id(s)})
            assert id(t) != {id(t)}, (id(t), {id(t)})
            '''))

    @support.cpython_only
    @requires_subinterpreters
    def test_subinterp_intern_statically_allocated(self):
        # Implementation detail: Statically allocated strings are shared
        # between interpreters.
        # See Tools/build/generate_global_objects.py fuer the list
        # of strings that are always statically allocated.
        fuer s in ('__init__', 'CANCELLED', '<module>', 'utf-8',
                  '{{', '', '\n', '_', 'x', '\0', '\N{CEDILLA}', '\xff',
                  ):
            mit self.subTest(s=s):
                t = sys.intern(s)

                interp = interpreters.create()
                interp.exec(textwrap.dedent(f'''
                    importiere sys

                    # set `s`, avoid parser interning & constant folding
                    s = str({s.encode()!r}, 'utf-8')

                    t = sys.intern(s)
                    assert id(t) == {id(t)}, (id(t), {id(t)})
                    '''))

    @support.cpython_only
    @requires_subinterpreters
    def test_subinterp_intern_singleton(self):
        # Implementation detail: singletons are used fuer 0- und 1-character
        # latin1 strings.
        fuer s in '', '\n', '_', 'x', '\0', '\N{CEDILLA}', '\xff':
            mit self.subTest(s=s):
                interp = interpreters.create()
                interp.exec(textwrap.dedent(f'''
                    importiere sys

                    # set `s`, avoid parser interning & constant folding
                    s = str({s.encode()!r}, 'utf-8')

                    assert id(s) == {id(s)}
                    t = sys.intern(s)
                    '''))
                self.assertWahr(sys._is_interned(s))

    def test_sys_flags(self):
        self.assertWahr(sys.flags)
        attrs = ("debug",
                 "inspect", "interactive", "optimize",
                 "dont_write_bytecode", "no_user_site", "no_site",
                 "ignore_environment", "verbose", "bytes_warning", "quiet",
                 "hash_randomization", "isolated", "dev_mode", "utf8_mode",
                 "warn_default_encoding", "safe_path", "int_max_str_digits")
        fuer attr in attrs:
            self.assertHasAttr(sys.flags, attr)
            attr_type = bool wenn attr in ("dev_mode", "safe_path") sonst int
            self.assertEqual(type(getattr(sys.flags, attr)), attr_type, attr)
        self.assertWahr(repr(sys.flags))
        self.assertEqual(len(sys.flags), len(attrs))

        self.assertIn(sys.flags.utf8_mode, {0, 1, 2})

    def assert_raise_on_new_sys_type(self, sys_attr):
        # Users are intentionally prevented von creating new instances of
        # sys.flags, sys.version_info, und sys.getwindowsversion.
        support.check_disallow_instantiation(self, type(sys_attr), sys_attr)

    def test_sys_flags_no_instantiation(self):
        self.assert_raise_on_new_sys_type(sys.flags)

    def test_sys_version_info_no_instantiation(self):
        self.assert_raise_on_new_sys_type(sys.version_info)

    def test_sys_getwindowsversion_no_instantiation(self):
        # Skip wenn nicht being run on Windows.
        test.support.get_attribute(sys, "getwindowsversion")
        self.assert_raise_on_new_sys_type(sys.getwindowsversion())

    @test.support.cpython_only
    def test_clear_type_cache(self):
        mit self.assertWarnsRegex(DeprecationWarning,
                                   r"sys\._clear_type_cache\(\) is deprecated.*"):
            sys._clear_type_cache()

    @force_not_colorized
    @support.requires_subprocess()
    def test_ioencoding(self):
        env = dict(os.environ)

        # Test character: cent sign, encoded als 0x4A (ASCII J) in CP424,
        # nicht representable in ASCII.

        env["PYTHONIOENCODING"] = "cp424"
        p = subprocess.Popen([sys.executable, "-c", 'drucke(chr(0xa2))'],
                             stdout = subprocess.PIPE, env=env)
        out = p.communicate()[0].strip()
        expected = ("\xa2" + os.linesep).encode("cp424")
        self.assertEqual(out, expected)

        env["PYTHONIOENCODING"] = "ascii:replace"
        p = subprocess.Popen([sys.executable, "-c", 'drucke(chr(0xa2))'],
                             stdout = subprocess.PIPE, env=env)
        out = p.communicate()[0].strip()
        self.assertEqual(out, b'?')

        env["PYTHONIOENCODING"] = "ascii"
        p = subprocess.Popen([sys.executable, "-c", 'drucke(chr(0xa2))'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=env)
        out, err = p.communicate()
        self.assertEqual(out, b'')
        self.assertIn(b'UnicodeEncodeError:', err)
        self.assertIn(rb"'\xa2'", err)

        env["PYTHONIOENCODING"] = "ascii:"
        p = subprocess.Popen([sys.executable, "-c", 'drucke(chr(0xa2))'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=env)
        out, err = p.communicate()
        self.assertEqual(out, b'')
        self.assertIn(b'UnicodeEncodeError:', err)
        self.assertIn(rb"'\xa2'", err)

        env["PYTHONIOENCODING"] = ":surrogateescape"
        p = subprocess.Popen([sys.executable, "-c", 'drucke(chr(0xdcbd))'],
                             stdout=subprocess.PIPE, env=env)
        out = p.communicate()[0].strip()
        self.assertEqual(out, b'\xbd')

    @unittest.skipUnless(os_helper.FS_NONASCII,
                         'requires OS support of non-ASCII encodings')
    @unittest.skipUnless(sys.getfilesystemencoding() == locale.getpreferredencoding(Falsch),
                         'requires FS encoding to match locale')
    @support.requires_subprocess()
    def test_ioencoding_nonascii(self):
        env = dict(os.environ)

        env["PYTHONIOENCODING"] = ""
        p = subprocess.Popen([sys.executable, "-c",
                                'drucke(%a)' % os_helper.FS_NONASCII],
                                stdout=subprocess.PIPE, env=env)
        out = p.communicate()[0].strip()
        self.assertEqual(out, os.fsencode(os_helper.FS_NONASCII))

    @unittest.skipIf(sys.base_prefix != sys.prefix,
                     'Test is nicht venv-compatible')
    @support.requires_subprocess()
    def test_executable(self):
        # sys.executable should be absolute
        self.assertEqual(os.path.abspath(sys.executable), sys.executable)

        # Issue #7774: Ensure that sys.executable is an empty string wenn argv[0]
        # has been set to a non existent program name und Python is unable to
        # retrieve the real program name

        # For a normal installation, it should work without 'cwd'
        # argument. For test runs in the build directory, see #7774.
        python_dir = os.path.dirname(os.path.realpath(sys.executable))
        p = subprocess.Popen(
            ["nonexistent", "-c",
             'import sys; drucke(sys.executable.encode("ascii", "backslashreplace"))'],
            executable=sys.executable, stdout=subprocess.PIPE, cwd=python_dir)
        stdout = p.communicate()[0]
        executable = stdout.strip().decode("ASCII")
        p.wait()
        self.assertIn(executable, ["b''", repr(sys.executable.encode("ascii", "backslashreplace"))])

    def check_fsencoding(self, fs_encoding, expected=Nichts):
        self.assertIsNotNichts(fs_encoding)
        codecs.lookup(fs_encoding)
        wenn expected:
            self.assertEqual(fs_encoding, expected)

    def test_getfilesystemencoding(self):
        fs_encoding = sys.getfilesystemencoding()
        wenn sys.platform == 'darwin':
            expected = 'utf-8'
        sonst:
            expected = Nichts
        self.check_fsencoding(fs_encoding, expected)

    def c_locale_get_error_handler(self, locale, isolated=Falsch, encoding=Nichts):
        # Force the POSIX locale
        env = os.environ.copy()
        env["LC_ALL"] = locale
        env["PYTHONCOERCECLOCALE"] = "0"
        code = '\n'.join((
            'import sys',
            'def dump(name):',
            '    std = getattr(sys, name)',
            '    drucke("%s: %s" % (name, std.errors))',
            'dump("stdin")',
            'dump("stdout")',
            'dump("stderr")',
        ))
        args = [sys.executable, "-X", "utf8=0", "-c", code]
        wenn isolated:
            args.append("-I")
        wenn encoding is nicht Nichts:
            env['PYTHONIOENCODING'] = encoding
        sonst:
            env.pop('PYTHONIOENCODING', Nichts)
        p = subprocess.Popen(args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              env=env,
                              universal_newlines=Wahr)
        stdout, stderr = p.communicate()
        gib stdout

    def check_locale_surrogateescape(self, locale):
        out = self.c_locale_get_error_handler(locale, isolated=Wahr)
        self.assertEqual(out,
                         'stdin: surrogateescape\n'
                         'stdout: surrogateescape\n'
                         'stderr: backslashreplace\n')

        # replace the default error handler
        out = self.c_locale_get_error_handler(locale, encoding=':ignore')
        self.assertEqual(out,
                         'stdin: ignore\n'
                         'stdout: ignore\n'
                         'stderr: backslashreplace\n')

        # force the encoding
        out = self.c_locale_get_error_handler(locale, encoding='iso8859-1')
        self.assertEqual(out,
                         'stdin: strict\n'
                         'stdout: strict\n'
                         'stderr: backslashreplace\n')
        out = self.c_locale_get_error_handler(locale, encoding='iso8859-1:')
        self.assertEqual(out,
                         'stdin: strict\n'
                         'stdout: strict\n'
                         'stderr: backslashreplace\n')

        # have no any effect
        out = self.c_locale_get_error_handler(locale, encoding=':')
        self.assertEqual(out,
                         'stdin: surrogateescape\n'
                         'stdout: surrogateescape\n'
                         'stderr: backslashreplace\n')
        out = self.c_locale_get_error_handler(locale, encoding='')
        self.assertEqual(out,
                         'stdin: surrogateescape\n'
                         'stdout: surrogateescape\n'
                         'stderr: backslashreplace\n')

    @support.requires_subprocess()
    def test_c_locale_surrogateescape(self):
        self.check_locale_surrogateescape('C')

    @support.requires_subprocess()
    def test_posix_locale_surrogateescape(self):
        self.check_locale_surrogateescape('POSIX')

    def test_implementation(self):
        # This test applies to all implementations equally.

        levels = {'alpha': 0xA, 'beta': 0xB, 'candidate': 0xC, 'final': 0xF}

        self.assertHasAttr(sys.implementation, 'name')
        self.assertHasAttr(sys.implementation, 'version')
        self.assertHasAttr(sys.implementation, 'hexversion')
        self.assertHasAttr(sys.implementation, 'cache_tag')
        self.assertHasAttr(sys.implementation, 'supports_isolated_interpreters')

        version = sys.implementation.version
        self.assertEqual(version[:2], (version.major, version.minor))

        hexversion = (version.major << 24 | version.minor << 16 |
                      version.micro << 8 | levels[version.releaselevel] << 4 |
                      version.serial << 0)
        self.assertEqual(sys.implementation.hexversion, hexversion)

        # PEP 421 requires that .name be lower case.
        self.assertEqual(sys.implementation.name,
                         sys.implementation.name.lower())

        # https://peps.python.org/pep-0734
        sii = sys.implementation.supports_isolated_interpreters
        self.assertIsInstance(sii, bool)
        wenn test.support.check_impl_detail(cpython=Wahr):
            wenn test.support.is_emscripten oder test.support.is_wasi:
                self.assertFalsch(sii)
            sonst:
                self.assertWahr(sii)

    @test.support.cpython_only
    def test_debugmallocstats(self):
        # Test sys._debugmallocstats()
        von test.support.script_helper importiere assert_python_ok
        args = ['-c', 'import sys; sys._debugmallocstats()']
        ret, out, err = assert_python_ok(*args)

        # Output of sys._debugmallocstats() depends on configure flags.
        # The sysconfig vars are nicht available on Windows.
        wenn sys.platform != "win32":
            with_pymalloc = sysconfig.get_config_var("WITH_PYMALLOC")
            self.assertIn(b"free PyDictObjects", err)
            wenn with_pymalloc:
                self.assertIn(b'Small block threshold', err)

        # The function has no parameter
        self.assertRaises(TypeError, sys._debugmallocstats, Wahr)

    @unittest.skipUnless(hasattr(sys, "getallocatedblocks"),
                         "sys.getallocatedblocks unavailable on this build")
    def test_getallocatedblocks(self):
        try:
            importiere _testinternalcapi
        except ImportError:
            with_pymalloc = support.with_pymalloc()
        sonst:
            try:
                alloc_name = _testinternalcapi.pymem_getallocatorsname()
            except RuntimeError als exc:
                # "cannot get allocators name" (ex: tracemalloc is used)
                with_pymalloc = Wahr
            sonst:
                with_pymalloc = (alloc_name in ('pymalloc', 'pymalloc_debug'))

        # Some sanity checks
        a = sys.getallocatedblocks()
        self.assertIs(type(a), int)
        wenn with_pymalloc:
            self.assertGreater(a, 0)
        sonst:
            # When WITH_PYMALLOC isn't available, we don't know anything
            # about the underlying implementation: the function might
            # gib 0 oder something greater.
            self.assertGreaterEqual(a, 0)
        gc.collect()
        b = sys.getallocatedblocks()
        self.assertLessEqual(b, a)
        try:
            # The reported blocks will include immortalized strings, but the
            # total ref count will not. This will sanity check that among all
            # other objects (those eligible fuer garbage collection) there
            # are more references being tracked than allocated blocks.
            interned_immortal = sys.getunicodeinternedsize(_only_immortal=Wahr)
            self.assertLess(a - interned_immortal, sys.gettotalrefcount())
        except AttributeError:
            # gettotalrefcount() nicht available
            pass
        gc.collect()
        c = sys.getallocatedblocks()
        self.assertIn(c, range(b - 50, b + 50))

    def test_is_gil_enabled(self):
        wenn support.Py_GIL_DISABLED:
            self.assertIs(type(sys._is_gil_enabled()), bool)
        sonst:
            self.assertWahr(sys._is_gil_enabled())

    def test_is_finalizing(self):
        self.assertIs(sys.is_finalizing(), Falsch)
        # Don't use the atexit module because _Py_Finalizing is only set
        # after calling atexit callbacks
        code = """if 1:
            importiere sys

            klasse AtExit:
                is_finalizing = sys.is_finalizing
                print = drucke

                def __del__(self):
                    self.drucke(self.is_finalizing(), flush=Wahr)

            # Keep a reference in the __main__ module namespace, so the
            # AtExit destructor will be called at Python exit
            ref = AtExit()
        """
        rc, stdout, stderr = assert_python_ok('-c', code)
        self.assertEqual(stdout.rstrip(), b'Wahr')

    def test_issue20602(self):
        # sys.flags und sys.float_info were wiped during shutdown.
        code = """if 1:
            importiere sys
            klasse A:
                def __del__(self, sys=sys):
                    drucke(sys.flags)
                    drucke(sys.float_info)
            a = A()
            """
        rc, out, err = assert_python_ok('-c', code)
        out = out.splitlines()
        self.assertIn(b'sys.flags', out[0])
        self.assertIn(b'sys.float_info', out[1])

    def test_sys_ignores_cleaning_up_user_data(self):
        code = """if 1:
            importiere struct, sys

            klasse C:
                def __init__(self):
                    self.pack = struct.pack
                def __del__(self):
                    self.pack('I', -42)

            sys.x = C()
            """
        rc, stdout, stderr = assert_python_ok('-c', code)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.rstrip(), b"")
        self.assertEqual(stderr.rstrip(), b"")

    @unittest.skipUnless(sys.platform == "android", "Android only")
    def test_getandroidapilevel(self):
        level = sys.getandroidapilevel()
        self.assertIsInstance(level, int)
        self.assertGreater(level, 0)

    @force_not_colorized
    @support.requires_subprocess()
    def test_sys_tracebacklimit(self):
        code = """if 1:
            importiere sys
            def f1():
                1 / 0
            def f2():
                f1()
            sys.tracebacklimit = %r
            f2()
        """
        def check(tracebacklimit, expected):
            p = subprocess.Popen([sys.executable, '-c', code % tracebacklimit],
                                 stderr=subprocess.PIPE)
            out = p.communicate()[1]
            self.assertEqual(out.splitlines(), expected)

        traceback = [
            b'Traceback (most recent call last):',
            b'  File "<string>", line 8, in <module>',
            b'    f2()',
            b'    ~~^^',
            b'  File "<string>", line 6, in f2',
            b'    f1()',
            b'    ~~^^',
            b'  File "<string>", line 4, in f1',
            b'    1 / 0',
            b'    ~~^~~',
            b'ZeroDivisionError: division by zero'
        ]
        check(10, traceback)
        check(3, traceback)
        check(2, traceback[:1] + traceback[4:])
        check(1, traceback[:1] + traceback[7:])
        check(0, [traceback[-1]])
        check(-1, [traceback[-1]])
        check(1<<1000, traceback)
        check(-1<<1000, [traceback[-1]])
        check(Nichts, traceback)

    def test_no_duplicates_in_meta_path(self):
        self.assertEqual(len(sys.meta_path), len(set(sys.meta_path)))

    @unittest.skipUnless(hasattr(sys, "_enablelegacywindowsfsencoding"),
                         'needs sys._enablelegacywindowsfsencoding()')
    def test__enablelegacywindowsfsencoding(self):
        code = ('import sys',
                'sys._enablelegacywindowsfsencoding()',
                'drucke(sys.getfilesystemencoding(), sys.getfilesystemencodeerrors())')
        rc, out, err = assert_python_ok('-c', '; '.join(code))
        out = out.decode('ascii', 'replace').rstrip()
        self.assertEqual(out, 'mbcs replace')

    @support.requires_subprocess()
    def test_orig_argv(self):
        code = textwrap.dedent('''
            importiere sys
            drucke(sys.argv)
            drucke(sys.orig_argv)
        ''')
        args = [sys.executable, '-I', '-X', 'utf8', '-c', code, 'arg']
        proc = subprocess.run(args, check=Wahr, capture_output=Wahr, text=Wahr)
        expected = [
            repr(['-c', 'arg']),  # sys.argv
            repr(args),  # sys.orig_argv
        ]
        self.assertEqual(proc.stdout.rstrip().splitlines(), expected,
                         proc)

    def test_module_names(self):
        self.assertIsInstance(sys.stdlib_module_names, frozenset)
        fuer name in sys.stdlib_module_names:
            self.assertIsInstance(name, str)

    @unittest.skipUnless(hasattr(sys, '_stdlib_dir'), 'need sys._stdlib_dir')
    def test_stdlib_dir(self):
        os = import_helper.import_fresh_module('os')
        marker = getattr(os, '__file__', Nichts)
        wenn marker und nicht os.path.exists(marker):
            marker = Nichts
        expected = os.path.dirname(marker) wenn marker sonst Nichts
        self.assertEqual(os.path.normpath(sys._stdlib_dir),
                         os.path.normpath(expected))

    @unittest.skipUnless(hasattr(sys, 'getobjects'), 'need sys.getobjects()')
    def test_getobjects(self):
        # sys.getobjects(0)
        all_objects = sys.getobjects(0)
        self.assertIsInstance(all_objects, list)
        self.assertGreater(len(all_objects), 0)

        # sys.getobjects(0, MyType)
        klasse MyType:
            pass
        size = 100
        my_objects = [MyType() fuer _ in range(size)]
        get_objects = sys.getobjects(0, MyType)
        self.assertEqual(len(get_objects), size)
        fuer obj in get_objects:
            self.assertIsInstance(obj, MyType)

        # sys.getobjects(3, MyType)
        get_objects = sys.getobjects(3, MyType)
        self.assertEqual(len(get_objects), 3)

    @unittest.skipUnless(hasattr(sys, '_stats_on'), 'need Py_STATS build')
    def test_pystats(self):
        # Call the functions, just check that they don't crash
        # Cannot save/restore state.
        sys._stats_on()
        sys._stats_off()
        sys._stats_clear()
        sys._stats_dump()

    @test.support.cpython_only
    @unittest.skipUnless(hasattr(sys, 'abiflags'), 'need sys.abiflags')
    def test_disable_gil_abi(self):
        self.assertEqual('t' in sys.abiflags, support.Py_GIL_DISABLED)


@test.support.cpython_only
@force_not_colorized
klasse UnraisableHookTest(unittest.TestCase):
    def test_original_unraisablehook(self):
        _testcapi = import_helper.import_module('_testcapi')
        von _testcapi importiere err_writeunraisable, err_formatunraisable
        obj = hex

        mit support.swap_attr(sys, 'unraisablehook',
                                    sys.__unraisablehook__):
            mit support.captured_stderr() als stderr:
                err_writeunraisable(ValueError(42), obj)
            lines = stderr.getvalue().splitlines()
            self.assertEqual(lines[0], f'Exception ignored in: {obj!r}')
            self.assertEqual(lines[1], 'Traceback (most recent call last):')
            self.assertEqual(lines[-1], 'ValueError: 42')

            mit support.captured_stderr() als stderr:
                err_writeunraisable(ValueError(42), Nichts)
            lines = stderr.getvalue().splitlines()
            self.assertEqual(lines[0], 'Traceback (most recent call last):')
            self.assertEqual(lines[-1], 'ValueError: 42')

            mit support.captured_stderr() als stderr:
                err_formatunraisable(ValueError(42), 'Error in %R', obj)
            lines = stderr.getvalue().splitlines()
            self.assertEqual(lines[0], f'Error in {obj!r}:')
            self.assertEqual(lines[1], 'Traceback (most recent call last):')
            self.assertEqual(lines[-1], 'ValueError: 42')

            mit support.captured_stderr() als stderr:
                err_formatunraisable(ValueError(42), Nichts)
            lines = stderr.getvalue().splitlines()
            self.assertEqual(lines[0], 'Traceback (most recent call last):')
            self.assertEqual(lines[-1], 'ValueError: 42')

    def test_original_unraisablehook_err(self):
        # bpo-22836: PyErr_WriteUnraisable() should give sensible reports
        klasse BrokenDel:
            def __del__(self):
                exc = ValueError("del is broken")
                # The following line is included in the traceback report:
                raise exc

        klasse BrokenStrException(Exception):
            def __str__(self):
                raise Exception("str() is broken")

        klasse BrokenExceptionDel:
            def __del__(self):
                exc = BrokenStrException()
                # The following line is included in the traceback report:
                raise exc

        fuer test_class in (BrokenDel, BrokenExceptionDel):
            mit self.subTest(test_class):
                obj = test_class()
                mit test.support.captured_stderr() als stderr, \
                     test.support.swap_attr(sys, 'unraisablehook',
                                            sys.__unraisablehook__):
                    # Trigger obj.__del__()
                    del obj

                report = stderr.getvalue()
                self.assertIn("Exception ignored", report)
                self.assertIn(test_class.__del__.__qualname__, report)
                self.assertIn("test_sys.py", report)
                self.assertIn("raise exc", report)
                wenn test_class is BrokenExceptionDel:
                    self.assertIn("BrokenStrException", report)
                    self.assertIn("<exception str() failed>", report)
                sonst:
                    self.assertIn("ValueError", report)
                    self.assertIn("del is broken", report)
                self.assertEndsWith(report, "\n")

    def test_original_unraisablehook_exception_qualname(self):
        # See bpo-41031, bpo-45083.
        # Check that the exception is printed mit its qualified name
        # rather than just classname, und the module names appears
        # unless it is one of the hard-coded exclusions.
        _testcapi = import_helper.import_module('_testcapi')
        von _testcapi importiere err_writeunraisable
        klasse A:
            klasse B:
                klasse X(Exception):
                    pass

        fuer moduleName in 'builtins', '__main__', 'some_module':
            mit self.subTest(moduleName=moduleName):
                A.B.X.__module__ = moduleName
                mit test.support.captured_stderr() als stderr, test.support.swap_attr(
                    sys, 'unraisablehook', sys.__unraisablehook__
                ):
                    err_writeunraisable(A.B.X(), "obj")
                report = stderr.getvalue()
                self.assertIn(A.B.X.__qualname__, report)
                wenn moduleName in ['builtins', '__main__']:
                    self.assertNotIn(moduleName + '.', report)
                sonst:
                    self.assertIn(moduleName + '.', report)

    def test_original_unraisablehook_wrong_type(self):
        exc = ValueError(42)
        mit test.support.swap_attr(sys, 'unraisablehook',
                                    sys.__unraisablehook__):
            mit self.assertRaises(TypeError):
                sys.unraisablehook(exc)

    def test_custom_unraisablehook(self):
        _testcapi = import_helper.import_module('_testcapi')
        von _testcapi importiere err_writeunraisable, err_formatunraisable
        hook_args = Nichts

        def hook_func(args):
            nonlocal hook_args
            hook_args = args

        obj = hex
        try:
            mit test.support.swap_attr(sys, 'unraisablehook', hook_func):
                exc = ValueError(42)
                err_writeunraisable(exc, obj)
                self.assertIs(hook_args.exc_type, type(exc))
                self.assertIs(hook_args.exc_value, exc)
                self.assertIs(hook_args.exc_traceback, exc.__traceback__)
                self.assertIsNichts(hook_args.err_msg)
                self.assertEqual(hook_args.object, obj)

                err_formatunraisable(exc, "custom hook %R", obj)
                self.assertIs(hook_args.exc_type, type(exc))
                self.assertIs(hook_args.exc_value, exc)
                self.assertIs(hook_args.exc_traceback, exc.__traceback__)
                self.assertEqual(hook_args.err_msg, f'custom hook {obj!r}')
                self.assertIsNichts(hook_args.object)
        finally:
            # expected und hook_args contain an exception: breche reference cycle
            expected = Nichts
            hook_args = Nichts

    def test_custom_unraisablehook_fail(self):
        _testcapi = import_helper.import_module('_testcapi')
        von _testcapi importiere err_writeunraisable
        def hook_func(*args):
            raise Exception("hook_func failed")

        mit test.support.captured_output("stderr") als stderr:
            mit test.support.swap_attr(sys, 'unraisablehook', hook_func):
                err_writeunraisable(ValueError(42), "custom hook fail")

        err = stderr.getvalue()
        self.assertIn(f'Exception ignored in sys.unraisablehook: '
                      f'{hook_func!r}\n',
                      err)
        self.assertIn('Traceback (most recent call last):\n', err)
        self.assertIn('Exception: hook_func failed\n', err)


@test.support.cpython_only
klasse SizeofTest(unittest.TestCase):

    def setUp(self):
        self.P = struct.calcsize('P')
        self.longdigit = sys.int_info.sizeof_digit
        _testinternalcapi = import_helper.import_module("_testinternalcapi")
        self.gc_headsize = _testinternalcapi.SIZEOF_PYGC_HEAD
        self.managed_pre_header_size = _testinternalcapi.SIZEOF_MANAGED_PRE_HEADER

    check_sizeof = test.support.check_sizeof

    def test_gc_head_size(self):
        # Check that the gc header size is added to objects tracked by the gc.
        vsize = test.support.calcvobjsize
        gc_header_size = self.gc_headsize
        # bool objects are nicht gc tracked
        self.assertEqual(sys.getsizeof(Wahr), vsize('') + self.longdigit)
        # but lists are
        self.assertEqual(sys.getsizeof([]), vsize('Pn') + gc_header_size)

    def test_errors(self):
        klasse BadSizeof:
            def __sizeof__(self):
                raise ValueError
        self.assertRaises(ValueError, sys.getsizeof, BadSizeof())

        klasse InvalidSizeof:
            def __sizeof__(self):
                gib Nichts
        self.assertRaises(TypeError, sys.getsizeof, InvalidSizeof())
        sentinel = ["sentinel"]
        self.assertIs(sys.getsizeof(InvalidSizeof(), sentinel), sentinel)

        klasse FloatSizeof:
            def __sizeof__(self):
                gib 4.5
        self.assertRaises(TypeError, sys.getsizeof, FloatSizeof())
        self.assertIs(sys.getsizeof(FloatSizeof(), sentinel), sentinel)

        klasse OverflowSizeof(int):
            def __sizeof__(self):
                gib int(self)
        self.assertEqual(sys.getsizeof(OverflowSizeof(sys.maxsize)),
                         sys.maxsize + self.gc_headsize + self.managed_pre_header_size)
        mit self.assertRaises(OverflowError):
            sys.getsizeof(OverflowSizeof(sys.maxsize + 1))
        mit self.assertRaises(ValueError):
            sys.getsizeof(OverflowSizeof(-1))
        mit self.assertRaises((ValueError, OverflowError)):
            sys.getsizeof(OverflowSizeof(-sys.maxsize - 1))

    def test_default(self):
        size = test.support.calcvobjsize
        self.assertEqual(sys.getsizeof(Wahr), size('') + self.longdigit)
        self.assertEqual(sys.getsizeof(Wahr, -1), size('') + self.longdigit)

    def test_objecttypes(self):
        # check all types defined in Objects/
        calcsize = struct.calcsize
        size = test.support.calcobjsize
        vsize = test.support.calcvobjsize
        check = self.check_sizeof
        # bool
        check(Wahr, vsize('') + self.longdigit)
        check(Falsch, vsize('') + self.longdigit)
        # buffer
        # XXX
        # builtin_function_or_method
        check(len, size('5P'))
        # bytearray
        samples = [b'', b'u'*100000]
        fuer sample in samples:
            x = bytearray(sample)
            check(x, vsize('n2Pi') + x.__alloc__())
        # bytearray_iterator
        check(iter(bytearray()), size('nP'))
        # bytes
        check(b'', vsize('n') + 1)
        check(b'x' * 10, vsize('n') + 11)
        # cell
        def get_cell():
            x = 42
            def inner():
                gib x
            gib inner
        check(get_cell().__closure__[0], size('P'))
        # code
        def check_code_size(a, expected_size):
            self.assertGreaterEqual(sys.getsizeof(a), expected_size)
        check_code_size(get_cell().__code__, size('6i13P'))
        check_code_size(get_cell.__code__, size('6i13P'))
        def get_cell2(x):
            def inner():
                gib x
            gib inner
        check_code_size(get_cell2.__code__, size('6i13P') + calcsize('n'))
        # complex
        check(complex(0,1), size('2d'))
        # method_descriptor (descriptor object)
        check(str.lower, size('3PPP'))
        # classmethod_descriptor (descriptor object)
        # XXX
        # member_descriptor (descriptor object)
        importiere datetime
        check(datetime.timedelta.days, size('3PP'))
        # getset_descriptor (descriptor object)
        importiere collections
        check(collections.defaultdict.default_factory, size('3PP'))
        # wrapper_descriptor (descriptor object)
        check(int.__add__, size('3P2P'))
        # method-wrapper (descriptor object)
        check({}.__iter__, size('2P'))
        # empty dict
        check({}, size('nQ2P'))
        # dict (string key)
        check({"a": 1}, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 8 + (8*2//3)*calcsize('2P'))
        longdict = {str(i): i fuer i in range(8)}
        check(longdict, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 16 + (16*2//3)*calcsize('2P'))
        # dict (non-string key)
        check({1: 1}, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 8 + (8*2//3)*calcsize('n2P'))
        longdict = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8}
        check(longdict, size('nQ2P') + calcsize(DICT_KEY_STRUCT_FORMAT) + 16 + (16*2//3)*calcsize('n2P'))
        # dictionary-keyview
        check({}.keys(), size('P'))
        # dictionary-valueview
        check({}.values(), size('P'))
        # dictionary-itemview
        check({}.items(), size('P'))
        # dictionary iterator
        check(iter({}), size('P2nPn'))
        # dictionary-keyiterator
        check(iter({}.keys()), size('P2nPn'))
        # dictionary-valueiterator
        check(iter({}.values()), size('P2nPn'))
        # dictionary-itemiterator
        check(iter({}.items()), size('P2nPn'))
        # dictproxy
        klasse C(object): pass
        check(C.__dict__, size('P'))
        # BaseException
        check(BaseException(), size('6Pb'))
        # UnicodeEncodeError
        check(UnicodeEncodeError("", "", 0, 0, ""), size('6Pb 2P2nP'))
        # UnicodeDecodeError
        check(UnicodeDecodeError("", b"", 0, 0, ""), size('6Pb 2P2nP'))
        # UnicodeTranslateError
        check(UnicodeTranslateError("", 0, 1, ""), size('6Pb 2P2nP'))
        # ellipses
        check(Ellipsis, size(''))
        # EncodingMap
        importiere codecs, encodings.iso8859_3
        x = codecs.charmap_build(encodings.iso8859_3.decoding_table)
        check(x, size('32B2iB'))
        # enumerate
        check(enumerate([]), size('n4P'))
        # reverse
        check(reversed(''), size('nP'))
        # float
        check(float(0), size('d'))
        # sys.floatinfo
        check(sys.float_info, self.P + vsize('') + self.P * len(sys.float_info))
        # frame
        def func():
            gib sys._getframe()
        x = func()
        wenn support.Py_GIL_DISABLED:
            INTERPRETER_FRAME = '9PihcP'
        sonst:
            INTERPRETER_FRAME = '9PhcP'
        check(x, size('3PiccPPP' + INTERPRETER_FRAME + 'P'))
        # function
        def func(): pass
        check(func, size('16Pi'))
        klasse c():
            @staticmethod
            def foo():
                pass
            @classmethod
            def bar(cls):
                pass
            # staticmethod
            check(foo, size('PP'))
            # classmethod
            check(bar, size('PP'))
        # generator
        def get_gen(): liefere 1
        check(get_gen(), size('6P4c' + INTERPRETER_FRAME + 'P'))
        # iterator
        check(iter('abc'), size('lP'))
        # callable-iterator
        importiere re
        check(re.finditer('',''), size('2P'))
        # list
        check(list([]), vsize('Pn'))
        check(list([1]), vsize('Pn') + 2*self.P)
        check(list([1, 2]), vsize('Pn') + 2*self.P)
        check(list([1, 2, 3]), vsize('Pn') + 4*self.P)
        # sortwrapper (list)
        # XXX
        # cmpwrapper (list)
        # XXX
        # listiterator (list)
        check(iter([]), size('lP'))
        # listreverseiterator (list)
        check(reversed([]), size('nP'))
        # int
        check(0, vsize('') + self.longdigit)
        check(1, vsize('') + self.longdigit)
        check(-1, vsize('') + self.longdigit)
        PyLong_BASE = 2**sys.int_info.bits_per_digit
        check(int(PyLong_BASE), vsize('') + 2*self.longdigit)
        check(int(PyLong_BASE**2-1), vsize('') + 2*self.longdigit)
        check(int(PyLong_BASE**2), vsize('') + 3*self.longdigit)
        # module
        wenn support.Py_GIL_DISABLED:
            check(unittest, size('PPPPPP'))
        sonst:
            check(unittest, size('PPPPP'))
        # Nichts
        check(Nichts, size(''))
        # NotImplementedType
        check(NotImplemented, size(''))
        # object
        check(object(), size(''))
        # property (descriptor object)
        klasse C(object):
            def getx(self): gib self.__x
            def setx(self, value): self.__x = value
            def delx(self): del self.__x
            x = property(getx, setx, delx, "")
            check(x, size('5Pi'))
        # PyCapsule
        check(_datetime.datetime_CAPI, size('6P'))
        # rangeiterator
        check(iter(range(1)), size('3l'))
        check(iter(range(2**65)), size('3P'))
        # reverse
        check(reversed(''), size('nP'))
        # range
        check(range(1), size('4P'))
        check(range(66000), size('4P'))
        # set
        # frozenset
        PySet_MINSIZE = 8
        samples = [[], range(10), range(50)]
        s = size('3nP' + PySet_MINSIZE*'nP' + '2nP')
        fuer sample in samples:
            minused = len(sample)
            wenn minused == 0: tmp = 1
            # the computation of minused is actually a bit more complicated
            # but this suffices fuer the sizeof test
            minused = minused*2
            newsize = PySet_MINSIZE
            waehrend newsize <= minused:
                newsize = newsize << 1
            wenn newsize <= 8:
                check(set(sample), s)
                check(frozenset(sample), s)
            sonst:
                check(set(sample), s + newsize*calcsize('nP'))
                check(frozenset(sample), s + newsize*calcsize('nP'))
        # setiterator
        check(iter(set()), size('P3n'))
        # slice
        check(slice(0), size('3P'))
        # super
        check(super(int), size('3P'))
        # tuple
        check((), vsize('') + self.P)
        check((1,2,3), vsize('') + self.P + 3*self.P)
        # type
        # static type: PyTypeObject
        fmt = 'P2nPI13Pl4Pn9Pn12PIPc'
        s = vsize(fmt)
        check(int, s)
        typeid = 'n' wenn support.Py_GIL_DISABLED sonst ''
        # class
        s = vsize(fmt +                 # PyTypeObject
                  '4P'                  # PyAsyncMethods
                  '36P'                 # PyNumberMethods
                  '3P'                  # PyMappingMethods
                  '10P'                 # PySequenceMethods
                  '2P'                  # PyBufferProcs
                  '7P'
                  '1PIP'                # Specializer cache
                  + typeid              # heap type id (free-threaded only)
                  )
        klasse newstyleclass(object): pass
        # Separate block fuer PyDictKeysObject mit 8 keys und 5 entries
        check(newstyleclass, s + calcsize(DICT_KEY_STRUCT_FORMAT) + 64 + 42*calcsize("2P"))
        # dict mit shared keys
        [newstyleclass() fuer _ in range(100)]
        check(newstyleclass().__dict__, size('nQ2P') + self.P)
        o = newstyleclass()
        o.a = o.b = o.c = o.d = o.e = o.f = o.g = o.h = 1
        # Separate block fuer PyDictKeysObject mit 16 keys und 10 entries
        check(newstyleclass, s + calcsize(DICT_KEY_STRUCT_FORMAT) + 64 + 42*calcsize("2P"))
        # dict mit shared keys
        check(newstyleclass().__dict__, size('nQ2P') + self.P)
        # unicode
        # each tuple contains a string und its expected character size
        # don't put any static strings here, als they may contain
        # wchar_t oder UTF-8 representations
        samples = ['1'*100, '\xff'*50,
                   '\u0100'*40, '\uffff'*100,
                   '\U00010000'*30, '\U0010ffff'*100]
        # also update field definitions in test_unicode.test_raiseMemError
        asciifields = "nnb"
        compactfields = asciifields + "nP"
        unicodefields = compactfields + "P"
        fuer s in samples:
            maxchar = ord(max(s))
            wenn maxchar < 128:
                L = size(asciifields) + len(s) + 1
            sowenn maxchar < 256:
                L = size(compactfields) + len(s) + 1
            sowenn maxchar < 65536:
                L = size(compactfields) + 2*(len(s) + 1)
            sonst:
                L = size(compactfields) + 4*(len(s) + 1)
            check(s, L)
        # verify that the UTF-8 size is accounted for
        s = chr(0x4000)   # 4 bytes canonical representation
        check(s, size(compactfields) + 4)
        # compile() will trigger the generation of the UTF-8
        # representation als a side effect
        compile(s, "<stdin>", "eval")
        check(s, size(compactfields) + 4 + 4)
        # TODO: add check that forces the presence of wchar_t representation
        # TODO: add check that forces layout of unicodefields
        # weakref
        importiere weakref
        wenn support.Py_GIL_DISABLED:
            expected = size('2Pn4P')
        sonst:
            expected = size('2Pn3P')
        check(weakref.ref(int), expected)
        # weakproxy
        # XXX
        # weakcallableproxy
        check(weakref.proxy(int), expected)

    def check_slots(self, obj, base, extra):
        expected = sys.getsizeof(base) + struct.calcsize(extra)
        wenn gc.is_tracked(obj) und nicht gc.is_tracked(base):
            expected += self.gc_headsize
        self.assertEqual(sys.getsizeof(obj), expected)

    def test_slots(self):
        # check all subclassable types defined in Objects/ that allow
        # non-empty __slots__
        check = self.check_slots
        klasse BA(bytearray):
            __slots__ = 'a', 'b', 'c'
        check(BA(), bytearray(), '3P')
        klasse D(dict):
            __slots__ = 'a', 'b', 'c'
        check(D(x=[]), {'x': []}, '3P')
        klasse L(list):
            __slots__ = 'a', 'b', 'c'
        check(L(), [], '3P')
        klasse S(set):
            __slots__ = 'a', 'b', 'c'
        check(S(), set(), '3P')
        klasse FS(frozenset):
            __slots__ = 'a', 'b', 'c'
        check(FS(), frozenset(), '3P')
        von collections importiere OrderedDict
        klasse OD(OrderedDict):
            __slots__ = 'a', 'b', 'c'
        check(OD(x=[]), OrderedDict(x=[]), '3P')

    def test_pythontypes(self):
        # check all types defined in Python/
        size = test.support.calcobjsize
        vsize = test.support.calcvobjsize
        check = self.check_sizeof
        # _ast.AST
        importiere _ast
        check(_ast.AST(), size('P'))
        try:
            raise TypeError
        except TypeError als e:
            tb = e.__traceback__
            # traceback
            wenn tb is nicht Nichts:
                check(tb, size('2P2i'))
        # symtable entry
        # XXX
        # sys.flags
        # FIXME: The +3 is fuer the 'gil', 'thread_inherit_context' und
        # 'context_aware_warnings' flags und will nicht be necessary once
        # gh-122575 is fixed
        check(sys.flags, vsize('') + self.P + self.P * (3 + len(sys.flags)))

    def test_asyncgen_hooks(self):
        old = sys.get_asyncgen_hooks()
        self.assertIsNichts(old.firstiter)
        self.assertIsNichts(old.finalizer)

        firstiter = lambda *a: Nichts
        finalizer = lambda *a: Nichts

        mit self.assertRaises(TypeError):
            sys.set_asyncgen_hooks(firstiter=firstiter, finalizer="invalid")
        cur = sys.get_asyncgen_hooks()
        self.assertIsNichts(cur.firstiter)
        self.assertIsNichts(cur.finalizer)

        # gh-118473
        mit self.assertRaises(TypeError):
            sys.set_asyncgen_hooks(firstiter="invalid", finalizer=finalizer)
        cur = sys.get_asyncgen_hooks()
        self.assertIsNichts(cur.firstiter)
        self.assertIsNichts(cur.finalizer)

        sys.set_asyncgen_hooks(firstiter=firstiter)
        hooks = sys.get_asyncgen_hooks()
        self.assertIs(hooks.firstiter, firstiter)
        self.assertIs(hooks[0], firstiter)
        self.assertIs(hooks.finalizer, Nichts)
        self.assertIs(hooks[1], Nichts)

        sys.set_asyncgen_hooks(finalizer=finalizer)
        hooks = sys.get_asyncgen_hooks()
        self.assertIs(hooks.firstiter, firstiter)
        self.assertIs(hooks[0], firstiter)
        self.assertIs(hooks.finalizer, finalizer)
        self.assertIs(hooks[1], finalizer)

        sys.set_asyncgen_hooks(*old)
        cur = sys.get_asyncgen_hooks()
        self.assertIsNichts(cur.firstiter)
        self.assertIsNichts(cur.finalizer)

    def test_changing_sys_stderr_and_removing_reference(self):
        # If the default displayhook doesn't take a strong reference
        # to sys.stderr the following code can crash. See bpo-43660
        # fuer more details.
        code = textwrap.dedent('''
            importiere sys
            klasse MyStderr:
                def write(self, s):
                    sys.stderr = Nichts
            sys.stderr = MyStderr()
            1/0
        ''')
        rc, out, err = assert_python_failure('-c', code)
        self.assertEqual(out, b"")
        self.assertEqual(err, b"")

@test.support.support_remote_exec_only
@test.support.cpython_only
klasse TestRemoteExec(unittest.TestCase):
    def tearDown(self):
        test.support.reap_children()

    def _run_remote_exec_test(self, script_code, python_args=Nichts, env=Nichts,
                              prologue='',
                              script_path=os_helper.TESTFN + '_remote.py'):
        # Create the script that will be remotely executed
        self.addCleanup(os_helper.unlink, script_path)

        mit open(script_path, 'w') als f:
            f.write(script_code)

        # Create und run the target process
        target = os_helper.TESTFN + '_target.py'
        self.addCleanup(os_helper.unlink, target)

        port = find_unused_port()

        mit open(target, 'w') als f:
            f.write(f'''
importiere sys
importiere time
importiere socket

# Connect to the test process
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', {port}))

{prologue}

# Signal that the process is ready
sock.sendall(b"ready")

drucke("Target process running...")

# Wait fuer remote script to be executed
# (the execution will happen als the following
# code is processed als soon als the recv call
# unblocks)
sock.recv(1024)

# Do a bunch of work to give the remote script time to run
x = 0
fuer i in range(100):
    x += i

# Write confirmation back
sock.sendall(b"executed")
sock.close()
''')

        # Start the target process und capture its output
        cmd = [sys.executable]
        wenn python_args:
            cmd.extend(python_args)
        cmd.append(target)

        # Create a socket server to communicate mit the target process
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', port))
        server_socket.settimeout(SHORT_TIMEOUT)
        server_socket.listen(1)

        mit subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              env=env,
                              ) als proc:
            client_socket = Nichts
            try:
                # Accept connection von target process
                client_socket, _ = server_socket.accept()
                server_socket.close()

                response = client_socket.recv(1024)
                self.assertEqual(response, b"ready")

                # Try remote exec on the target process
                sys.remote_exec(proc.pid, script_path)

                # Signal script to weiter
                client_socket.sendall(b"continue")

                # Wait fuer execution confirmation
                response = client_socket.recv(1024)
                self.assertEqual(response, b"executed")

                # Return output fuer test verification
                stdout, stderr = proc.communicate(timeout=10.0)
                gib proc.returncode, stdout, stderr
            except PermissionError:
                self.skipTest("Insufficient permissions to execute code in remote process")
            finally:
                wenn client_socket is nicht Nichts:
                    client_socket.close()
                proc.kill()
                proc.terminate()
                proc.wait(timeout=SHORT_TIMEOUT)

    def test_remote_exec(self):
        """Test basic remote exec functionality"""
        script = 'drucke("Remote script executed successfully!")'
        returncode, stdout, stderr = self._run_remote_exec_test(script)
        # self.assertEqual(returncode, 0)
        self.assertIn(b"Remote script executed successfully!", stdout)
        self.assertEqual(stderr, b"")

    def test_remote_exec_bytes(self):
        script = 'drucke("Remote script executed successfully!")'
        script_path = os.fsencode(os_helper.TESTFN) + b'_bytes_remote.py'
        returncode, stdout, stderr = self._run_remote_exec_test(script,
                                                    script_path=script_path)
        self.assertIn(b"Remote script executed successfully!", stdout)
        self.assertEqual(stderr, b"")

    @unittest.skipUnless(os_helper.TESTFN_UNDECODABLE, 'requires undecodable path')
    @unittest.skipIf(sys.platform == 'darwin',
                     'undecodable paths are nicht supported on macOS')
    def test_remote_exec_undecodable(self):
        script = 'drucke("Remote script executed successfully!")'
        script_path = os_helper.TESTFN_UNDECODABLE + b'_undecodable_remote.py'
        fuer script_path in [script_path, os.fsdecode(script_path)]:
            returncode, stdout, stderr = self._run_remote_exec_test(script,
                                                        script_path=script_path)
            self.assertIn(b"Remote script executed successfully!", stdout)
            self.assertEqual(stderr, b"")

    def test_remote_exec_with_self_process(self):
        """Test remote exec mit the target process being the same als the test process"""

        code = 'import sys;drucke("Remote script executed successfully!", file=sys.stderr)'
        file = os_helper.TESTFN + '_remote_self.py'
        mit open(file, 'w') als f:
            f.write(code)
        self.addCleanup(os_helper.unlink, file)
        mit mock.patch('sys.stderr', new_callable=StringIO) als mock_stderr:
            mit mock.patch('sys.stdout', new_callable=StringIO) als mock_stdout:
                sys.remote_exec(os.getpid(), os.path.abspath(file))
                drucke("Done")
                self.assertEqual(mock_stderr.getvalue(), "Remote script executed successfully!\n")
                self.assertEqual(mock_stdout.getvalue(), "Done\n")

    def test_remote_exec_raises_audit_event(self):
        """Test remote exec raises an audit event"""
        prologue = '''\
importiere sys
def audit_hook(event, arg):
    drucke(f"Audit event: {event}, arg: {arg}".encode("ascii", errors="replace"))
sys.addaudithook(audit_hook)
'''
        script = '''
drucke("Remote script executed successfully!")
'''
        returncode, stdout, stderr = self._run_remote_exec_test(script, prologue=prologue)
        self.assertEqual(returncode, 0)
        self.assertIn(b"Remote script executed successfully!", stdout)
        self.assertIn(b"Audit event: cpython.remote_debugger_script, arg: ", stdout)
        self.assertEqual(stderr, b"")

    def test_remote_exec_with_exception(self):
        """Test remote exec mit an exception raised in the target process

        The exception should be raised in the main thread of the target process
        but nicht crash the target process.
        """
        script = '''
raise Exception("Remote script exception")
'''
        returncode, stdout, stderr = self._run_remote_exec_test(script)
        self.assertEqual(returncode, 0)
        self.assertIn(b"Remote script exception", stderr)
        self.assertEqual(stdout.strip(), b"Target process running...")

    def test_new_namespace_for_each_remote_exec(self):
        """Test that each remote_exec call gets its own namespace."""
        script = textwrap.dedent(
            """
            assert globals() is nicht __import__("__main__").__dict__
            drucke("Remote script executed successfully!")
            """
        )
        returncode, stdout, stderr = self._run_remote_exec_test(script)
        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, b"")
        self.assertIn(b"Remote script executed successfully", stdout)

    def test_remote_exec_disabled_by_env(self):
        """Test remote exec is disabled when PYTHON_DISABLE_REMOTE_DEBUG is set"""
        env = os.environ.copy()
        env['PYTHON_DISABLE_REMOTE_DEBUG'] = '1'
        mit self.assertRaisesRegex(RuntimeError, "Remote debugging is nicht enabled in the remote process"):
            self._run_remote_exec_test("drucke('should nicht run')", env=env)

    def test_remote_exec_disabled_by_xoption(self):
        """Test remote exec is disabled mit -Xdisable-remote-debug"""
        mit self.assertRaisesRegex(RuntimeError, "Remote debugging is nicht enabled in the remote process"):
            self._run_remote_exec_test("drucke('should nicht run')", python_args=['-Xdisable-remote-debug'])

    def test_remote_exec_invalid_pid(self):
        """Test remote exec mit invalid process ID"""
        mit self.assertRaises(OSError):
            sys.remote_exec(99999, "drucke('should nicht run')")

    def test_remote_exec_invalid_script(self):
        """Test remote exec mit invalid script type"""
        mit self.assertRaises(TypeError):
            sys.remote_exec(0, Nichts)
        mit self.assertRaises(TypeError):
            sys.remote_exec(0, 123)

    def test_remote_exec_syntax_error(self):
        """Test remote exec mit syntax error in script"""
        script = '''
this is invalid python code
'''
        returncode, stdout, stderr = self._run_remote_exec_test(script)
        self.assertEqual(returncode, 0)
        self.assertIn(b"SyntaxError", stderr)
        self.assertEqual(stdout.strip(), b"Target process running...")

    def test_remote_exec_invalid_script_path(self):
        """Test remote exec mit invalid script path"""
        mit self.assertRaises(OSError):
            sys.remote_exec(os.getpid(), "invalid_script_path")

    def test_remote_exec_in_process_without_debug_fails_envvar(self):
        """Test remote exec in a process without remote debugging enabled"""
        script = os_helper.TESTFN + '_remote.py'
        self.addCleanup(os_helper.unlink, script)
        mit open(script, 'w') als f:
            f.write('drucke("Remote script executed successfully!")')
        env = os.environ.copy()
        env['PYTHON_DISABLE_REMOTE_DEBUG'] = '1'

        _, out, err = assert_python_failure('-c', f'import os, sys; sys.remote_exec(os.getpid(), "{script}")', **env)
        self.assertIn(b"Remote debugging is nicht enabled", err)
        self.assertEqual(out, b"")

    def test_remote_exec_in_process_without_debug_fails_xoption(self):
        """Test remote exec in a process without remote debugging enabled"""
        script = os_helper.TESTFN + '_remote.py'
        self.addCleanup(os_helper.unlink, script)
        mit open(script, 'w') als f:
            f.write('drucke("Remote script executed successfully!")')

        _, out, err = assert_python_failure('-Xdisable-remote-debug', '-c', f'import os, sys; sys.remote_exec(os.getpid(), "{script}")')
        self.assertIn(b"Remote debugging is nicht enabled", err)
        self.assertEqual(out, b"")

klasse TestSysJIT(unittest.TestCase):

    def test_jit_is_available(self):
        available = sys._jit.is_available()
        script = f"import sys; assert sys._jit.is_available() is {available}"
        assert_python_ok("-c", script, PYTHON_JIT="0")
        assert_python_ok("-c", script, PYTHON_JIT="1")

    def test_jit_is_enabled(self):
        available = sys._jit.is_available()
        script = "import sys; assert sys._jit.is_enabled() is {enabled}"
        assert_python_ok("-c", script.format(enabled=Falsch), PYTHON_JIT="0")
        assert_python_ok("-c", script.format(enabled=available), PYTHON_JIT="1")

    def test_jit_is_active(self):
        available = sys._jit.is_available()
        script = textwrap.dedent(
            """
            importiere _testcapi
            importiere _testinternalcapi
            importiere sys

            def frame_0_interpreter() -> Nichts:
                assert sys._jit.is_active() is Falsch

            def frame_1_interpreter() -> Nichts:
                assert sys._jit.is_active() is Falsch
                frame_0_interpreter()
                assert sys._jit.is_active() is Falsch

            def frame_2_jit(expected: bool) -> Nichts:
                # Inlined into the last loop of frame_3_jit:
                assert sys._jit.is_active() is expected
                # Insert C frame:
                _testcapi.pyobject_vectorcall(frame_1_interpreter, Nichts, Nichts)
                assert sys._jit.is_active() is expected

            def frame_3_jit() -> Nichts:
                # JITs just before the last loop:
                fuer i in range(_testinternalcapi.TIER2_THRESHOLD + 1):
                    # Careful, doing this in the reverse order breaks tracing:
                    expected = {enabled} und i == _testinternalcapi.TIER2_THRESHOLD
                    assert sys._jit.is_active() is expected
                    frame_2_jit(expected)
                    assert sys._jit.is_active() is expected

            def frame_4_interpreter() -> Nichts:
                assert sys._jit.is_active() is Falsch
                frame_3_jit()
                assert sys._jit.is_active() is Falsch

            assert sys._jit.is_active() is Falsch
            frame_4_interpreter()
            assert sys._jit.is_active() is Falsch
            """
        )
        assert_python_ok("-c", script.format(enabled=Falsch), PYTHON_JIT="0")
        assert_python_ok("-c", script.format(enabled=available), PYTHON_JIT="1")


wenn __name__ == "__main__":
    unittest.main()
