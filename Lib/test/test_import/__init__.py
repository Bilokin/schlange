importiere builtins
importiere errno
importiere glob
importiere json
importiere importlib.util
von importlib._bootstrap_external importiere _get_sourcefile
von importlib.machinery importiere (
    AppleFrameworkLoader,
    BuiltinImporter,
    ExtensionFileLoader,
    FrozenImporter,
    SourceFileLoader,
)
importiere marshal
importiere os
importiere py_compile
importiere random
importiere shutil
importiere stat
importiere subprocess
importiere sys
importiere textwrap
importiere threading
importiere time
importiere types
importiere unittest
von unittest importiere mock
importiere _imp

von test.support importiere os_helper
von test.support importiere (
    STDLIB_DIR,
    swap_attr,
    swap_item,
    cpython_only,
    is_apple_mobile,
    is_emscripten,
    is_wasm32,
    run_in_subinterp,
    run_in_subinterp_with_config,
    Py_TRACE_REFS,
    requires_gil_enabled,
    Py_GIL_DISABLED,
    no_rerun,
    force_not_colorized_test_class,
)
von test.support.import_helper importiere (
    forget, make_legacy_pyc, unlink, unload, ready_to_import,
    DirsOnSysPath, CleanImport, import_module)
von test.support.os_helper importiere (
    TESTFN, rmtree, temp_umask, TESTFN_UNENCODABLE)
von test.support importiere script_helper
von test.support importiere threading_helper
von test.test_importlib.util importiere uncache
von types importiere ModuleType
versuch:
    importiere _testsinglephase
ausser ImportError:
    _testsinglephase = Nichts
versuch:
    importiere _testmultiphase
ausser ImportError:
    _testmultiphase = Nichts
versuch:
    importiere _interpreters
ausser ModuleNotFoundError:
    _interpreters = Nichts
versuch:
    importiere _testinternalcapi
ausser ImportError:
    _testinternalcapi = Nichts


skip_if_dont_write_bytecode = unittest.skipIf(
        sys.dont_write_bytecode,
        "test meaningful only when writing bytecode")


def _require_loader(module, loader, skip):
    wenn isinstance(module, str):
        module = __import__(module)

    MODULE_KINDS = {
        BuiltinImporter: 'built-in',
        ExtensionFileLoader: 'extension',
        AppleFrameworkLoader: 'framework extension',
        FrozenImporter: 'frozen',
        SourceFileLoader: 'pure Python',
    }

    expected = loader
    assert isinstance(expected, type), expected
    expected = MODULE_KINDS[expected]

    actual = module.__spec__.loader
    wenn nicht isinstance(actual, type):
        actual = type(actual)
    actual = MODULE_KINDS[actual]

    wenn actual != expected:
        err = f'expected module to be {expected}, got {module.__spec__}'
        wenn skip:
            wirf unittest.SkipTest(err)
        wirf Exception(err)
    gib module

def require_builtin(module, *, skip=Falsch):
    module = _require_loader(module, BuiltinImporter, skip)
    assert module.__spec__.origin == 'built-in', module.__spec__

def require_extension(module, *, skip=Falsch):
    # Apple extensions must be distributed als frameworks. This requires
    # a specialist loader.
    wenn is_apple_mobile:
        _require_loader(module, AppleFrameworkLoader, skip)
    sonst:
        _require_loader(module, ExtensionFileLoader, skip)

def require_frozen(module, *, skip=Wahr):
    module = _require_loader(module, FrozenImporter, skip)
    assert module.__spec__.origin == 'frozen', module.__spec__

def require_pure_python(module, *, skip=Falsch):
    _require_loader(module, SourceFileLoader, skip)

def create_extension_loader(modname, filename):
    # Apple extensions must be distributed als frameworks. This requires
    # a specialist loader.
    wenn is_apple_mobile:
        gib AppleFrameworkLoader(modname, filename)
    sonst:
        gib ExtensionFileLoader(modname, filename)

def import_extension_from_file(modname, filename, *, put_in_sys_modules=Wahr):
    loader = create_extension_loader(modname, filename)
    spec = importlib.util.spec_from_loader(modname, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    wenn put_in_sys_modules:
        sys.modules[modname] = module
    gib module


def remove_files(name):
    fuer f in (name + ".py",
              name + ".pyc",
              name + ".pyw",
              name + "$py.class"):
        unlink(f)
    rmtree('__pycache__')


wenn _testsinglephase ist nicht Nichts:
    def restore__testsinglephase(*, _orig=_testsinglephase):
        # We started mit the module imported und want to restore
        # it to its nominal state.
        sys.modules.pop('_testsinglephase', Nichts)
        _orig._clear_globals()
        origin = _orig.__spec__.origin
        _testinternalcapi.clear_extension('_testsinglephase', origin)
        importiere _testsinglephase


def requires_singlephase_init(meth):
    """Decorator to skip wenn single-phase init modules are nicht supported."""
    wenn nicht isinstance(meth, type):
        def meth(self, _meth=meth):
            versuch:
                gib _meth(self)
            schliesslich:
                restore__testsinglephase()
    meth = cpython_only(meth)
    msg = "gh-117694: free-threaded build does nicht currently support single-phase init modules in sub-interpreters"
    meth = requires_gil_enabled(msg)(meth)
    gib unittest.skipIf(_testsinglephase ist Nichts,
                           'test requires _testsinglephase module')(meth)


def requires_subinterpreters(meth):
    """Decorator to skip a test wenn subinterpreters are nicht supported."""
    gib unittest.skipIf(_interpreters ist Nichts,
                           'subinterpreters required')(meth)


klasse ModuleSnapshot(types.SimpleNamespace):
    """A representation of a module fuer testing.

    Fields:

    * id - the module's object ID
    * module - the actual module oder an adequate substitute
       * __file__
       * __spec__
          * name
          * origin
    * ns - a copy (dict) of the module's __dict__ (or Nichts)
    * ns_id - the object ID of the module's __dict__
    * cached - the sys.modules[mod.__spec__.name] entry (or Nichts)
    * cached_id - the object ID of the sys.modules entry (or Nichts)

    In cases where the value ist nicht available (e.g. due to serialization),
    the value will be Nichts.
    """
    _fields = tuple('id module ns ns_id cached cached_id'.split())

    @classmethod
    def from_module(cls, mod):
        name = mod.__spec__.name
        cached = sys.modules.get(name)
        gib cls(
            id=id(mod),
            module=mod,
            ns=types.SimpleNamespace(**mod.__dict__),
            ns_id=id(mod.__dict__),
            cached=cached,
            cached_id=id(cached),
        )

    SCRIPT = textwrap.dedent('''
        {imports}

        name = {name!r}

        {prescript}

        mod = {name}

        {body}

        {postscript}
        ''')
    IMPORTS = textwrap.dedent('''
        importiere sys
        ''').strip()
    SCRIPT_BODY = textwrap.dedent('''
        # Capture the snapshot data.
        cached = sys.modules.get(name)
        snapshot = dict(
            id=id(mod),
            module=dict(
                __file__=mod.__file__,
                __spec__=dict(
                    name=mod.__spec__.name,
                    origin=mod.__spec__.origin,
                ),
            ),
            ns=Nichts,
            ns_id=id(mod.__dict__),
            cached=Nichts,
            cached_id=id(cached) wenn cached sonst Nichts,
        )
        ''').strip()
    CLEANUP_SCRIPT = textwrap.dedent('''
        # Clean up the module.
        sys.modules.pop(name, Nichts)
        ''').strip()

    @classmethod
    def build_script(cls, name, *,
                     prescript=Nichts,
                     import_first=Falsch,
                     postscript=Nichts,
                     postcleanup=Falsch,
                     ):
        wenn postcleanup ist Wahr:
            postcleanup = cls.CLEANUP_SCRIPT
        sowenn isinstance(postcleanup, str):
            postcleanup = textwrap.dedent(postcleanup).strip()
            postcleanup = cls.CLEANUP_SCRIPT + os.linesep + postcleanup
        sonst:
            postcleanup = ''
        prescript = textwrap.dedent(prescript).strip() wenn prescript sonst ''
        postscript = textwrap.dedent(postscript).strip() wenn postscript sonst ''

        wenn postcleanup:
            wenn postscript:
                postscript = postscript + os.linesep * 2 + postcleanup
            sonst:
                postscript = postcleanup

        wenn import_first:
            prescript += textwrap.dedent(f'''

                # Now importiere the module.
                assert name nicht in sys.modules
                importiere {name}''')

        gib cls.SCRIPT.format(
            imports=cls.IMPORTS.strip(),
            name=name,
            prescript=prescript.strip(),
            body=cls.SCRIPT_BODY.strip(),
            postscript=postscript,
        )

    @classmethod
    def parse(cls, text):
        raw = json.loads(text)
        mod = raw['module']
        mod['__spec__'] = types.SimpleNamespace(**mod['__spec__'])
        raw['module'] = types.SimpleNamespace(**mod)
        gib cls(**raw)

    @classmethod
    def from_subinterp(cls, name, interpid=Nichts, *, pipe=Nichts, **script_kwds):
        wenn pipe ist nicht Nichts:
            gib cls._from_subinterp(name, interpid, pipe, script_kwds)
        pipe = os.pipe()
        versuch:
            gib cls._from_subinterp(name, interpid, pipe, script_kwds)
        schliesslich:
            r, w = pipe
            os.close(r)
            os.close(w)

    @classmethod
    def _from_subinterp(cls, name, interpid, pipe, script_kwargs):
        r, w = pipe

        # Build the script.
        postscript = textwrap.dedent(f'''
            # Send the result over the pipe.
            importiere json
            importiere os
            os.write({w}, json.dumps(snapshot).encode())

            ''')
        _postscript = script_kwargs.get('postscript')
        wenn _postscript:
            _postscript = textwrap.dedent(_postscript).lstrip()
            postscript += _postscript
        script_kwargs['postscript'] = postscript.strip()
        script = cls.build_script(name, **script_kwargs)

        # Run the script.
        wenn interpid ist Nichts:
            ret = run_in_subinterp(script)
            wenn ret != 0:
                wirf AssertionError(f'{ret} != 0')
        sonst:
            _interpreters.run_string(interpid, script)

        # Parse the results.
        text = os.read(r, 1000)
        gib cls.parse(text.decode())


@force_not_colorized_test_class
klasse ImportTests(unittest.TestCase):

    def setUp(self):
        remove_files(TESTFN)
        importlib.invalidate_caches()

    def tearDown(self):
        unload(TESTFN)

    def test_import_raises_ModuleNotFoundError(self):
        mit self.assertRaises(ModuleNotFoundError):
            importiere something_that_should_not_exist_anywhere

    def test_from_import_missing_module_raises_ModuleNotFoundError(self):
        mit self.assertRaises(ModuleNotFoundError):
            von something_that_should_not_exist_anywhere importiere blah

    def test_from_import_missing_attr_raises_ImportError(self):
        mit self.assertRaises(ImportError):
            von importlib importiere something_that_should_not_exist_anywhere

    def test_from_import_missing_attr_has_name_and_path(self):
        mit CleanImport('os'):
            importiere os
            mit self.assertRaises(ImportError) als cm:
                von os importiere i_dont_exist
        self.assertEqual(cm.exception.name, 'os')
        self.assertEqual(cm.exception.path, os.__file__)
        self.assertRegex(str(cm.exception), r"cannot importiere name 'i_dont_exist' von 'os' \(.*os.py\)")

    @cpython_only
    def test_from_import_missing_attr_has_name_and_so_path(self):
        _testcapi = import_module("_testcapi")
        mit self.assertRaises(ImportError) als cm:
            von _testcapi importiere i_dont_exist
        self.assertEqual(cm.exception.name, '_testcapi')
        wenn hasattr(_testcapi, "__file__"):
            # The path on the exception ist strictly the spec origin, nicht the
            # module's __file__. For most cases, these are the same; but on
            # iOS, the Framework relocation process results in the exception
            # being raised von the spec location.
            self.assertEqual(cm.exception.path, _testcapi.__spec__.origin)
            self.assertRegex(
                str(cm.exception),
                r"cannot importiere name 'i_dont_exist' von '_testcapi' \(.*(\.(so|pyd))?\)"
            )
        sonst:
            self.assertEqual(
                str(cm.exception),
                "cannot importiere name 'i_dont_exist' von '_testcapi' (unknown location)"
            )

    def test_from_import_missing_attr_has_name(self):
        mit self.assertRaises(ImportError) als cm:
            # _warning has no path als it's a built-in module.
            von _warning importiere i_dont_exist
        self.assertEqual(cm.exception.name, '_warning')
        self.assertIsNichts(cm.exception.path)

    def test_from_import_missing_attr_path_is_canonical(self):
        mit self.assertRaises(ImportError) als cm:
            von os.path importiere i_dont_exist
        self.assertIn(cm.exception.name, {'posixpath', 'ntpath'})
        self.assertIsNotNichts(cm.exception)

    def test_from_import_star_invalid_type(self):
        importiere re
        mit ready_to_import() als (name, path):
            mit open(path, 'w', encoding='utf-8') als f:
                f.write("__all__ = [b'invalid_type']")
            globals = {}
            mit self.assertRaisesRegex(
                TypeError, f"{re.escape(name)}\\.__all__ must be str"
            ):
                exec(f"from {name} importiere *", globals)
            self.assertNotIn(b"invalid_type", globals)
        mit ready_to_import() als (name, path):
            mit open(path, 'w', encoding='utf-8') als f:
                f.write("globals()[b'invalid_type'] = object()")
            globals = {}
            mit self.assertRaisesRegex(
                TypeError, f"{re.escape(name)}\\.__dict__ must be str"
            ):
                exec(f"from {name} importiere *", globals)
            self.assertNotIn(b"invalid_type", globals)

    def test_case_sensitivity(self):
        # Brief digression to test that importiere ist case-sensitive:  wenn we got
        # this far, we know fuer sure that "random" exists.
        mit self.assertRaises(ImportError):
            importiere RAnDoM

    def test_double_const(self):
        # Importing double_const checks that float constants
        # serialized by marshal als PYC files don't lose precision
        # (SF bug 422177).
        von test.test_import.data importiere double_const
        unload('test.test_import.data.double_const')
        von test.test_import.data importiere double_const  # noqa: F811

    def test_import(self):
        def test_with_extension(ext):
            # The extension ist normally ".py", perhaps ".pyw".
            source = TESTFN + ext
            pyc = TESTFN + ".pyc"

            mit open(source, "w", encoding='utf-8') als f:
                drucke("# This tests Python's ability to importiere a",
                      ext, "file.", file=f)
                a = random.randrange(1000)
                b = random.randrange(1000)
                drucke("a =", a, file=f)
                drucke("b =", b, file=f)

            wenn TESTFN in sys.modules:
                loesche sys.modules[TESTFN]
            importlib.invalidate_caches()
            versuch:
                versuch:
                    mod = __import__(TESTFN)
                ausser ImportError als err:
                    self.fail("import von %s failed: %s" % (ext, err))

                self.assertEqual(mod.a, a,
                    "module loaded (%s) but contents invalid" % mod)
                self.assertEqual(mod.b, b,
                    "module loaded (%s) but contents invalid" % mod)
            schliesslich:
                forget(TESTFN)
                unlink(source)
                unlink(pyc)

        sys.path.insert(0, os.curdir)
        versuch:
            test_with_extension(".py")
            wenn sys.platform.startswith("win"):
                fuer ext in [".PY", ".Py", ".pY", ".pyw", ".PYW", ".pYw"]:
                    test_with_extension(ext)
        schliesslich:
            loesche sys.path[0]

    def test_module_with_large_stack(self, module='longlist'):
        # Regression test fuer http://bugs.python.org/issue561858.
        filename = module + '.py'

        # Create a file mit a list of 65000 elements.
        mit open(filename, 'w', encoding='utf-8') als f:
            f.write('d = [\n')
            fuer i in range(65000):
                f.write('"",\n')
            f.write(']')

        versuch:
            # Compile & remove .py file; we only need .pyc.
            # Bytecode must be relocated von the PEP 3147 bytecode-only location.
            py_compile.compile(filename)
        schliesslich:
            unlink(filename)

        # Need to be able to load von current dir.
        sys.path.append('')
        importlib.invalidate_caches()

        namespace = {}
        versuch:
            make_legacy_pyc(filename)
            # This used to crash.
            exec('import ' + module, Nichts, namespace)
        schliesslich:
            # Cleanup.
            loesche sys.path[-1]
            unlink(filename + 'c')
            unlink(filename + 'o')

            # Remove references to the module (unload the module)
            namespace.clear()
            versuch:
                loesche sys.modules[module]
            ausser KeyError:
                pass

    def test_failing_import_sticks(self):
        source = TESTFN + ".py"
        mit open(source, "w", encoding='utf-8') als f:
            drucke("a = 1/0", file=f)

        # New in 2.4, we shouldn't be able to importiere that no matter how often
        # we try.
        sys.path.insert(0, os.curdir)
        importlib.invalidate_caches()
        wenn TESTFN in sys.modules:
            loesche sys.modules[TESTFN]
        versuch:
            fuer i in [1, 2, 3]:
                self.assertRaises(ZeroDivisionError, __import__, TESTFN)
                self.assertNotIn(TESTFN, sys.modules,
                                 "damaged module in sys.modules on %i try" % i)
        schliesslich:
            loesche sys.path[0]
            remove_files(TESTFN)

    def test_import_name_binding(self):
        # importiere x.y.z binds x in the current namespace
        importiere test als x
        importiere test.support
        self.assertIs(x, test, x.__name__)
        self.assertHasAttr(test.support, "__file__")

        # importiere x.y.z als w binds z als w
        importiere test.support als y
        self.assertIs(y, test.support, y.__name__)

    def test_issue31286(self):
        # importiere in a 'finally' block resulted in SystemError
        versuch:
            x = ...
        schliesslich:
            importiere test.support.script_helper als x

        # importiere in a 'while' loop resulted in stack overflow
        i = 0
        waehrend i < 10:
            importiere test.support.script_helper als x
            i += 1

        # importiere in a 'for' loop resulted in segmentation fault
        fuer i in range(2):
            importiere test.support.script_helper als x  # noqa: F811

    def test_failing_reload(self):
        # A failing reload should leave the module object in sys.modules.
        source = TESTFN + os.extsep + "py"
        mit open(source, "w", encoding='utf-8') als f:
            f.write("a = 1\nb=2\n")

        sys.path.insert(0, os.curdir)
        versuch:
            mod = __import__(TESTFN)
            self.assertIn(TESTFN, sys.modules)
            self.assertEqual(mod.a, 1, "module has wrong attribute values")
            self.assertEqual(mod.b, 2, "module has wrong attribute values")

            # On WinXP, just replacing the .py file wasn't enough to
            # convince reload() to reparse it.  Maybe the timestamp didn't
            # move enough.  We force it to get reparsed by removing the
            # compiled file too.
            remove_files(TESTFN)

            # Now damage the module.
            mit open(source, "w", encoding='utf-8') als f:
                f.write("a = 10\nb=20//0\n")

            self.assertRaises(ZeroDivisionError, importlib.reload, mod)
            # But we still expect the module to be in sys.modules.
            mod = sys.modules.get(TESTFN)
            self.assertIsNotNichts(mod, "expected module to be in sys.modules")

            # We should have replaced a w/ 10, but the old b value should
            # stick.
            self.assertEqual(mod.a, 10, "module has wrong attribute values")
            self.assertEqual(mod.b, 2, "module has wrong attribute values")

        schliesslich:
            loesche sys.path[0]
            remove_files(TESTFN)
            unload(TESTFN)

    @skip_if_dont_write_bytecode
    def test_file_to_source(self):
        # check wenn __file__ points to the source file where available
        source = TESTFN + ".py"
        mit open(source, "w", encoding='utf-8') als f:
            f.write("test = Nichts\n")

        sys.path.insert(0, os.curdir)
        versuch:
            mod = __import__(TESTFN)
            self.assertEndsWith(mod.__file__, '.py')
            os.remove(source)
            loesche sys.modules[TESTFN]
            make_legacy_pyc(source)
            importlib.invalidate_caches()
            mod = __import__(TESTFN)
            base, ext = os.path.splitext(mod.__file__)
            self.assertEqual(ext, '.pyc')
        schliesslich:
            loesche sys.path[0]
            remove_files(TESTFN)
            wenn TESTFN in sys.modules:
                loesche sys.modules[TESTFN]

    def test_import_by_filename(self):
        path = os.path.abspath(TESTFN)
        encoding = sys.getfilesystemencoding()
        versuch:
            path.encode(encoding)
        ausser UnicodeEncodeError:
            self.skipTest('path ist nicht encodable to {}'.format(encoding))
        mit self.assertRaises(ImportError) als c:
            __import__(path)

    def test_import_in_del_does_not_crash(self):
        # Issue 4236
        testfn = script_helper.make_script('', TESTFN, textwrap.dedent("""\
            importiere sys
            klasse C:
               def __del__(self):
                  importiere importlib
            sys.argv.insert(0, C())
            """))
        script_helper.assert_python_ok(testfn)

    @skip_if_dont_write_bytecode
    def test_timestamp_overflow(self):
        # A modification timestamp larger than 2**32 should nicht be a problem
        # when importing a module (issue #11235).
        sys.path.insert(0, os.curdir)
        versuch:
            source = TESTFN + ".py"
            compiled = importlib.util.cache_from_source(source)
            mit open(source, 'w', encoding='utf-8') als f:
                pass
            versuch:
                os.utime(source, (2 ** 33 - 5, 2 ** 33 - 5))
            ausser OverflowError:
                self.skipTest("cannot set modification time to large integer")
            ausser OSError als e:
                wenn e.errno nicht in (getattr(errno, 'EOVERFLOW', Nichts),
                                   getattr(errno, 'EINVAL', Nichts)):
                    wirf
                self.skipTest("cannot set modification time to large integer ({})".format(e))
            __import__(TESTFN)
            # The pyc file was created.
            os.stat(compiled)
        schliesslich:
            loesche sys.path[0]
            remove_files(TESTFN)

    def test_bogus_fromlist(self):
        versuch:
            __import__('http', fromlist=['blah'])
        ausser ImportError:
            self.fail("fromlist must allow bogus names")

    @cpython_only
    def test_delete_builtins_import(self):
        args = ["-c", "del __builtins__.__import__; importiere os"]
        popen = script_helper.spawn_python(*args)
        stdout, stderr = popen.communicate()
        self.assertIn(b"ImportError", stdout)

    def test_from_import_message_for_nonexistent_module(self):
        mit self.assertRaisesRegex(ImportError, "^No module named 'bogus'"):
            von bogus importiere foo

    def test_from_import_message_for_existing_module(self):
        mit self.assertRaisesRegex(ImportError, "^cannot importiere name 'bogus'"):
            von re importiere bogus

    def test_from_import_AttributeError(self):
        # Issue #24492: trying to importiere an attribute that raises an
        # AttributeError should lead to an ImportError.
        klasse AlwaysAttributeError:
            def __getattr__(self, _):
                wirf AttributeError

        module_name = 'test_from_import_AttributeError'
        self.addCleanup(unload, module_name)
        sys.modules[module_name] = AlwaysAttributeError()
        mit self.assertRaises(ImportError) als cm:
            von test_from_import_AttributeError importiere does_not_exist

        self.assertEqual(str(cm.exception),
            "cannot importiere name 'does_not_exist' von '<unknown module name>' (unknown location)")

    @cpython_only
    def test_issue31492(self):
        # There shouldn't be an assertion failure in case of failing to import
        # von a module mit a bad __name__ attribute, oder in case of failing
        # to access an attribute of such a module.
        mit swap_attr(os, '__name__', Nichts):
            mit self.assertRaises(ImportError):
                von os importiere does_not_exist

            mit self.assertRaises(AttributeError):
                os.does_not_exist

    @threading_helper.requires_working_threading()
    def test_concurrency(self):
        # bpo 38091: this ist a hack to slow down the code that calls
        # has_deadlock(); the logic was itself sometimes deadlocking.
        def delay_has_deadlock(frame, event, arg):
            wenn event == 'call' und frame.f_code.co_name == 'has_deadlock':
                time.sleep(0.1)

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))
        versuch:
            exc = Nichts
            def run():
                sys.settrace(delay_has_deadlock)
                event.wait()
                versuch:
                    importiere package
                ausser BaseException als e:
                    nonlocal exc
                    exc = e
                sys.settrace(Nichts)

            fuer i in range(10):
                event = threading.Event()
                threads = [threading.Thread(target=run) fuer x in range(2)]
                versuch:
                    mit threading_helper.start_threads(threads, event.set):
                        time.sleep(0)
                schliesslich:
                    sys.modules.pop('package', Nichts)
                    sys.modules.pop('package.submodule', Nichts)
                wenn exc ist nicht Nichts:
                    wirf exc
        schliesslich:
            loesche sys.path[0]

    @unittest.skipUnless(sys.platform == "win32", "Windows-specific")
    def test_dll_dependency_import(self):
        von _winapi importiere GetModuleFileName
        dllname = GetModuleFileName(sys.dllhandle)
        pydname = importlib.util.find_spec("_sqlite3").origin
        depname = os.path.join(
            os.path.dirname(pydname),
            "sqlite3{}.dll".format("_d" wenn "_d" in pydname sonst ""))

        mit os_helper.temp_dir() als tmp:
            tmp2 = os.path.join(tmp, "DLLs")
            os.mkdir(tmp2)

            pyexe = os.path.join(tmp, os.path.basename(sys.executable))
            shutil.copy(sys.executable, pyexe)
            shutil.copy(dllname, tmp)
            fuer f in glob.glob(os.path.join(glob.escape(sys.prefix), "vcruntime*.dll")):
                shutil.copy(f, tmp)

            shutil.copy(pydname, tmp2)

            env = Nichts
            env = {k.upper(): os.environ[k] fuer k in os.environ}
            env["PYTHONPATH"] = tmp2 + ";" + STDLIB_DIR

            # Test 1: importiere mit added DLL directory
            subprocess.check_call([
                pyexe, "-Sc", ";".join([
                    "import os",
                    "p = os.add_dll_directory({!r})".format(
                        os.path.dirname(depname)),
                    "import _sqlite3",
                    "p.close"
                ])],
                stderr=subprocess.STDOUT,
                env=env,
                cwd=os.path.dirname(pyexe))

            # Test 2: importiere mit DLL adjacent to PYD
            shutil.copy(depname, tmp2)
            subprocess.check_call([pyexe, "-Sc", "import _sqlite3"],
                                    stderr=subprocess.STDOUT,
                                    env=env,
                                    cwd=os.path.dirname(pyexe))

    def test_issue105979(self):
        # this used to crash
        mit self.assertRaises(ImportError) als cm:
            _imp.get_frozen_object("x", b"6\'\xd5Cu\x12")
        self.assertIn("Frozen object named 'x' ist invalid",
                      str(cm.exception))

    def test_frozen_module_from_import_error(self):
        mit self.assertRaises(ImportError) als cm:
            von os importiere this_will_never_exist
        self.assertIn(
            f"cannot importiere name 'this_will_never_exist' von 'os' ({os.__file__})",
            str(cm.exception),
        )
        mit self.assertRaises(ImportError) als cm:
            von sys importiere this_will_never_exist
        self.assertIn(
            "cannot importiere name 'this_will_never_exist' von 'sys' (unknown location)",
            str(cm.exception),
        )

        scripts = [
            """
importiere os
os.__spec__.has_location = Falsch
os.__file__ = []
von os importiere this_will_never_exist
""",
            """
importiere os
os.__spec__.has_location = Falsch
loesche os.__file__
von os importiere this_will_never_exist
""",
              """
importiere os
os.__spec__.origin = []
os.__file__ = []
von os importiere this_will_never_exist
"""
        ]
        fuer script in scripts:
            mit self.subTest(script=script):
                expected_error = (
                    b"cannot importiere name 'this_will_never_exist' "
                    b"from 'os' (unknown location)"
                )
                popen = script_helper.spawn_python("-c", script)
                stdout, stderr = popen.communicate()
                self.assertIn(expected_error, stdout)

    def test_non_module_from_import_error(self):
        prefix = """
importiere sys
klasse NotAModule: ...
nm = NotAModule()
nm.symbol = 123
sys.modules["not_a_module"] = nm
von not_a_module importiere symbol
"""
        scripts = [
            prefix + "from not_a_module importiere missing_symbol",
            prefix + "nm.__spec__ = []\nfrom not_a_module importiere missing_symbol",
        ]
        fuer script in scripts:
            mit self.subTest(script=script):
                expected_error = (
                    b"ImportError: cannot importiere name 'missing_symbol' von "
                    b"'<unknown module name>' (unknown location)"
                )
            popen = script_helper.spawn_python("-c", script)
            stdout, stderr = popen.communicate()
            self.assertIn(expected_error, stdout)

    def test_script_shadowing_stdlib(self):
        script_errors = [
            (
                "import fractions\nfractions.Fraction",
                rb"AttributeError: module 'fractions' has no attribute 'Fraction'"
            ),
            (
                "from fractions importiere Fraction",
                rb"ImportError: cannot importiere name 'Fraction' von 'fractions'"
            )
        ]
        fuer script, error in script_errors:
            mit self.subTest(script=script), os_helper.temp_dir() als tmp:
                mit open(os.path.join(tmp, "fractions.py"), "w", encoding='utf-8') als f:
                    f.write(script)

                expected_error = error + (
                    rb" \(consider renaming '.*fractions.py' since it has the "
                    rb"same name als the standard library module named 'fractions' "
                    rb"and prevents importing that standard library module\)"
                )

                popen = script_helper.spawn_python(os.path.join(tmp, "fractions.py"), cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                popen = script_helper.spawn_python('-m', 'fractions', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                popen = script_helper.spawn_python('-c', 'import fractions', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                # und there's no error at all when using -P
                popen = script_helper.spawn_python('-P', 'fractions.py', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertEqual(stdout, b'')

                tmp_child = os.path.join(tmp, "child")
                os.mkdir(tmp_child)

                # test the logic mit different cwd
                popen = script_helper.spawn_python(os.path.join(tmp, "fractions.py"), cwd=tmp_child)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                popen = script_helper.spawn_python('-m', 'fractions', cwd=tmp_child)
                stdout, stderr = popen.communicate()
                self.assertEqual(stdout, b'')  # no error

                popen = script_helper.spawn_python('-c', 'import fractions', cwd=tmp_child)
                stdout, stderr = popen.communicate()
                self.assertEqual(stdout, b'')  # no error

    def test_package_shadowing_stdlib_module(self):
        script_errors = [
            (
                "fractions.Fraction",
                rb"AttributeError: module 'fractions' has no attribute 'Fraction'"
            ),
            (
                "from fractions importiere Fraction",
                rb"ImportError: cannot importiere name 'Fraction' von 'fractions'"
            )
        ]
        fuer script, error in script_errors:
            mit self.subTest(script=script), os_helper.temp_dir() als tmp:
                os.mkdir(os.path.join(tmp, "fractions"))
                mit open(
                    os.path.join(tmp, "fractions", "__init__.py"), "w", encoding='utf-8'
                ) als f:
                    f.write("shadowing_module = Wahr")
                mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                    f.write("import fractions; fractions.shadowing_module\n")
                    f.write(script)

                expected_error = error + (
                    rb" \(consider renaming '.*[\\/]fractions[\\/]+__init__.py' since it has the "
                    rb"same name als the standard library module named 'fractions' "
                    rb"and prevents importing that standard library module\)"
                )

                popen = script_helper.spawn_python(os.path.join(tmp, "main.py"), cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                popen = script_helper.spawn_python('-m', 'main', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                # und there's no shadowing at all when using -P
                popen = script_helper.spawn_python('-P', 'main.py', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, b"module 'fractions' has no attribute 'shadowing_module'")

    def test_script_shadowing_third_party(self):
        script_errors = [
            (
                "import numpy\nnumpy.array",
                rb"AttributeError: module 'numpy' has no attribute 'array'"
            ),
            (
                "from numpy importiere array",
                rb"ImportError: cannot importiere name 'array' von 'numpy'"
            )
        ]
        fuer script, error in script_errors:
            mit self.subTest(script=script), os_helper.temp_dir() als tmp:
                mit open(os.path.join(tmp, "numpy.py"), "w", encoding='utf-8') als f:
                    f.write(script)

                expected_error = error + (
                    rb" \(consider renaming '.*numpy.py' wenn it has the "
                    rb"same name als a library you intended to import\)\s+\z"
                )

                popen = script_helper.spawn_python(os.path.join(tmp, "numpy.py"))
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                popen = script_helper.spawn_python('-m', 'numpy', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

                popen = script_helper.spawn_python('-c', 'import numpy', cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

    def test_script_maybe_not_shadowing_third_party(self):
        mit os_helper.temp_dir() als tmp:
            mit open(os.path.join(tmp, "numpy.py"), "w", encoding='utf-8') als f:
                f.write("this_script_does_not_attempt_to_import_numpy = Wahr")

            expected_error = (
                rb"AttributeError: module 'numpy' has no attribute 'attr'\s+\z"
            )
            popen = script_helper.spawn_python('-c', 'import numpy; numpy.attr', cwd=tmp)
            stdout, stderr = popen.communicate()
            self.assertRegex(stdout, expected_error)

            expected_error = (
                rb"ImportError: cannot importiere name 'attr' von 'numpy' \(.*\)\s+\z"
            )
            popen = script_helper.spawn_python('-c', 'from numpy importiere attr', cwd=tmp)
            stdout, stderr = popen.communicate()
            self.assertRegex(stdout, expected_error)

    def test_script_shadowing_stdlib_edge_cases(self):
        mit os_helper.temp_dir() als tmp:
            mit open(os.path.join(tmp, "fractions.py"), "w", encoding='utf-8') als f:
                f.write("shadowing_module = Wahr")

            # Unhashable str subclass
            mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                f.write("""
importiere fractions
fractions.shadowing_module
klasse substr(str):
    __hash__ = Nichts
fractions.__name__ = substr('fractions')
versuch:
    fractions.Fraction
ausser TypeError als e:
    drucke(str(e))
""")
            popen = script_helper.spawn_python("main.py", cwd=tmp)
            stdout, stderr = popen.communicate()
            self.assertIn(b"unhashable type: 'substr'", stdout.rstrip())

            mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                f.write("""
importiere fractions
fractions.shadowing_module
klasse substr(str):
    __hash__ = Nichts
fractions.__name__ = substr('fractions')
versuch:
    von fractions importiere Fraction
ausser TypeError als e:
    drucke(str(e))
""")

            popen = script_helper.spawn_python("main.py", cwd=tmp)
            stdout, stderr = popen.communicate()
            self.assertIn(b"unhashable type: 'substr'", stdout.rstrip())

            # Various issues mit sys module
            mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                f.write("""
importiere fractions
fractions.shadowing_module

importiere sys
sys.stdlib_module_names = Nichts
versuch:
    fractions.Fraction
ausser AttributeError als e:
    drucke(str(e))

loesche sys.stdlib_module_names
versuch:
    fractions.Fraction
ausser AttributeError als e:
    drucke(str(e))

sys.path = [0]
versuch:
    fractions.Fraction
ausser AttributeError als e:
    drucke(str(e))
""")
            popen = script_helper.spawn_python("main.py", cwd=tmp)
            stdout, stderr = popen.communicate()
            lines = stdout.splitlines()
            self.assertEqual(len(lines), 3)
            fuer line in lines:
                self.assertEqual(line, b"module 'fractions' has no attribute 'Fraction'")

            mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                f.write("""
importiere fractions
fractions.shadowing_module

importiere sys
sys.stdlib_module_names = Nichts
versuch:
    von fractions importiere Fraction
ausser ImportError als e:
    drucke(str(e))

loesche sys.stdlib_module_names
versuch:
    von fractions importiere Fraction
ausser ImportError als e:
    drucke(str(e))

sys.path = [0]
versuch:
    von fractions importiere Fraction
ausser ImportError als e:
    drucke(str(e))
""")
            popen = script_helper.spawn_python("main.py", cwd=tmp)
            stdout, stderr = popen.communicate()
            lines = stdout.splitlines()
            self.assertEqual(len(lines), 3)
            fuer line in lines:
                self.assertRegex(line, rb"cannot importiere name 'Fraction' von 'fractions' \(.*\)")

            # Various issues mit origin
            mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                f.write("""
importiere fractions
fractions.shadowing_module
loesche fractions.__spec__.origin
versuch:
    fractions.Fraction
ausser AttributeError als e:
    drucke(str(e))

fractions.__spec__.origin = []
versuch:
    fractions.Fraction
ausser AttributeError als e:
    drucke(str(e))
""")

            popen = script_helper.spawn_python("main.py", cwd=tmp)
            stdout, stderr = popen.communicate()
            lines = stdout.splitlines()
            self.assertEqual(len(lines), 2)
            fuer line in lines:
                self.assertEqual(line, b"module 'fractions' has no attribute 'Fraction'")

            mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                f.write("""
importiere fractions
fractions.shadowing_module
loesche fractions.__spec__.origin
versuch:
    von fractions importiere Fraction
ausser ImportError als e:
    drucke(str(e))

fractions.__spec__.origin = []
versuch:
    von fractions importiere Fraction
ausser ImportError als e:
    drucke(str(e))
""")
            popen = script_helper.spawn_python("main.py", cwd=tmp)
            stdout, stderr = popen.communicate()
            lines = stdout.splitlines()
            self.assertEqual(len(lines), 2)
            fuer line in lines:
                self.assertRegex(line, rb"cannot importiere name 'Fraction' von 'fractions' \(.*\)")

    @unittest.skipIf(sys.platform == 'win32', 'Cannot delete cwd on Windows')
    @unittest.skipIf(sys.platform == 'sunos5', 'Cannot delete cwd on Solaris/Illumos')
    def test_script_shadowing_stdlib_cwd_failure(self):
        mit os_helper.temp_dir() als tmp:
            subtmp = os.path.join(tmp, "subtmp")
            os.mkdir(subtmp)
            mit open(os.path.join(subtmp, "main.py"), "w", encoding='utf-8') als f:
                f.write(f"""
importiere sys
assert sys.path[0] == ''

importiere os
importiere shutil
shutil.rmtree(os.getcwd())

os.does_not_exist
""")
            # Use -c to ensure sys.path[0] ist ""
            popen = script_helper.spawn_python("-c", "import main", cwd=subtmp)
            stdout, stderr = popen.communicate()
            expected_error = rb"AttributeError: module 'os' has no attribute 'does_not_exist'"
            self.assertRegex(stdout, expected_error)

    def test_script_shadowing_stdlib_sys_path_modification(self):
        script_errors = [
            (
                "import fractions\nfractions.Fraction",
                rb"AttributeError: module 'fractions' has no attribute 'Fraction'"
            ),
            (
                "from fractions importiere Fraction",
                rb"ImportError: cannot importiere name 'Fraction' von 'fractions'"
            )
        ]
        fuer script, error in script_errors:
            mit self.subTest(script=script), os_helper.temp_dir() als tmp:
                mit open(os.path.join(tmp, "fractions.py"), "w", encoding='utf-8') als f:
                    f.write("shadowing_module = Wahr")
                mit open(os.path.join(tmp, "main.py"), "w", encoding='utf-8') als f:
                    f.write('import sys; sys.path.insert(0, "this_folder_does_not_exist")\n')
                    f.write(script)
                expected_error = error + (
                    rb" \(consider renaming '.*fractions.py' since it has the "
                    rb"same name als the standard library module named 'fractions' "
                    rb"and prevents importing that standard library module\)"
                )

                popen = script_helper.spawn_python("main.py", cwd=tmp)
                stdout, stderr = popen.communicate()
                self.assertRegex(stdout, expected_error)

    def test_create_dynamic_null(self):
        mit self.assertRaisesRegex(ValueError, 'embedded null character'):
            klasse Spec:
                name = "a\x00b"
                origin = "abc"
            _imp.create_dynamic(Spec())

        mit self.assertRaisesRegex(ValueError, 'embedded null character'):
            klasse Spec2:
                name = "abc"
                origin = "a\x00b"
            _imp.create_dynamic(Spec2())


@skip_if_dont_write_bytecode
klasse FilePermissionTests(unittest.TestCase):
    # tests fuer file mode on cached .pyc files

    @unittest.skipUnless(os.name == 'posix',
                         "test meaningful only on posix systems")
    @unittest.skipIf(
        is_wasm32,
        "Emscripten's/WASI's umask ist a stub."
    )
    def test_creation_mode(self):
        mask = 0o022
        mit temp_umask(mask), ready_to_import() als (name, path):
            cached_path = importlib.util.cache_from_source(path)
            module = __import__(name)
            wenn nicht os.path.exists(cached_path):
                self.fail("__import__ did nicht result in creation of "
                          "a .pyc file")
            stat_info = os.stat(cached_path)

        # Check that the umask ist respected, und the executable bits
        # aren't set.
        self.assertEqual(oct(stat.S_IMODE(stat_info.st_mode)),
                         oct(0o666 & ~mask))

    @unittest.skipUnless(os.name == 'posix',
                         "test meaningful only on posix systems")
    @os_helper.skip_unless_working_chmod
    def test_cached_mode_issue_2051(self):
        # permissions of .pyc should match those of .py, regardless of mask
        mode = 0o600
        mit temp_umask(0o022), ready_to_import() als (name, path):
            cached_path = importlib.util.cache_from_source(path)
            os.chmod(path, mode)
            __import__(name)
            wenn nicht os.path.exists(cached_path):
                self.fail("__import__ did nicht result in creation of "
                          "a .pyc file")
            stat_info = os.stat(cached_path)

        self.assertEqual(oct(stat.S_IMODE(stat_info.st_mode)), oct(mode))

    @unittest.skipUnless(os.name == 'posix',
                         "test meaningful only on posix systems")
    @os_helper.skip_unless_working_chmod
    def test_cached_readonly(self):
        mode = 0o400
        mit temp_umask(0o022), ready_to_import() als (name, path):
            cached_path = importlib.util.cache_from_source(path)
            os.chmod(path, mode)
            __import__(name)
            wenn nicht os.path.exists(cached_path):
                self.fail("__import__ did nicht result in creation of "
                          "a .pyc file")
            stat_info = os.stat(cached_path)

        expected = mode | 0o200 # Account fuer fix fuer issue #6074
        self.assertEqual(oct(stat.S_IMODE(stat_info.st_mode)), oct(expected))

    def test_pyc_always_writable(self):
        # Initially read-only .pyc files on Windows used to cause problems
        # mit later updates, see issue #6074 fuer details
        mit ready_to_import() als (name, path):
            # Write a Python file, make it read-only und importiere it
            mit open(path, 'w', encoding='utf-8') als f:
                f.write("x = 'original'\n")
            # Tweak the mtime of the source to ensure pyc gets updated later
            s = os.stat(path)
            os.utime(path, (s.st_atime, s.st_mtime-100000000))
            os.chmod(path, 0o400)
            m = __import__(name)
            self.assertEqual(m.x, 'original')
            # Change the file und then reimport it
            os.chmod(path, 0o600)
            mit open(path, 'w', encoding='utf-8') als f:
                f.write("x = 'rewritten'\n")
            unload(name)
            importlib.invalidate_caches()
            m = __import__(name)
            self.assertEqual(m.x, 'rewritten')
            # Now delete the source file und check the pyc was rewritten
            unlink(path)
            unload(name)
            importlib.invalidate_caches()
            bytecode_only = path + "c"
            os.rename(importlib.util.cache_from_source(path), bytecode_only)
            m = __import__(name)
            self.assertEqual(m.x, 'rewritten')


klasse PycRewritingTests(unittest.TestCase):
    # Test that the `co_filename` attribute on code objects always points
    # to the right file, even when various things happen (e.g. both the .py
    # und the .pyc file are renamed).

    module_name = "unlikely_module_name"
    module_source = """
importiere sys
code_filename = sys._getframe().f_code.co_filename
module_filename = __file__
constant = 1000
def func():
    pass
func_filename = func.__code__.co_filename
"""
    dir_name = os.path.abspath(TESTFN)
    file_name = os.path.join(dir_name, module_name) + os.extsep + "py"
    compiled_name = importlib.util.cache_from_source(file_name)

    def setUp(self):
        self.sys_path = sys.path[:]
        self.orig_module = sys.modules.pop(self.module_name, Nichts)
        os.mkdir(self.dir_name)
        mit open(self.file_name, "w", encoding='utf-8') als f:
            f.write(self.module_source)
        sys.path.insert(0, self.dir_name)
        importlib.invalidate_caches()

    def tearDown(self):
        sys.path[:] = self.sys_path
        wenn self.orig_module ist nicht Nichts:
            sys.modules[self.module_name] = self.orig_module
        sonst:
            unload(self.module_name)
        unlink(self.file_name)
        unlink(self.compiled_name)
        rmtree(self.dir_name)

    def import_module(self):
        ns = globals()
        __import__(self.module_name, ns, ns)
        gib sys.modules[self.module_name]

    def test_basics(self):
        mod = self.import_module()
        self.assertEqual(mod.module_filename, self.file_name)
        self.assertEqual(mod.code_filename, self.file_name)
        self.assertEqual(mod.func_filename, self.file_name)
        loesche sys.modules[self.module_name]
        mod = self.import_module()
        self.assertEqual(mod.module_filename, self.file_name)
        self.assertEqual(mod.code_filename, self.file_name)
        self.assertEqual(mod.func_filename, self.file_name)

    def test_incorrect_code_name(self):
        py_compile.compile(self.file_name, dfile="another_module.py")
        mod = self.import_module()
        self.assertEqual(mod.module_filename, self.file_name)
        self.assertEqual(mod.code_filename, self.file_name)
        self.assertEqual(mod.func_filename, self.file_name)

    def test_module_without_source(self):
        target = "another_module.py"
        py_compile.compile(self.file_name, dfile=target)
        os.remove(self.file_name)
        pyc_file = make_legacy_pyc(self.file_name)
        importlib.invalidate_caches()
        mod = self.import_module()
        self.assertEqual(mod.module_filename, pyc_file)
        self.assertEqual(mod.code_filename, target)
        self.assertEqual(mod.func_filename, target)

    def test_foreign_code(self):
        py_compile.compile(self.file_name)
        mit open(self.compiled_name, "rb") als f:
            header = f.read(16)
            code = marshal.load(f)
        constants = list(code.co_consts)
        foreign_code = importlib.import_module.__code__
        pos = constants.index(1000)
        constants[pos] = foreign_code
        code = code.replace(co_consts=tuple(constants))
        mit open(self.compiled_name, "wb") als f:
            f.write(header)
            marshal.dump(code, f)
        mod = self.import_module()
        self.assertEqual(mod.constant.co_filename, foreign_code.co_filename)


klasse PathsTests(unittest.TestCase):
    SAMPLES = ('test', 'test\u00e4\u00f6\u00fc\u00df', 'test\u00e9\u00e8',
               'test\u00b0\u00b3\u00b2')
    path = TESTFN

    def setUp(self):
        os.mkdir(self.path)
        self.syspath = sys.path[:]

    def tearDown(self):
        rmtree(self.path)
        sys.path[:] = self.syspath

    # Regression test fuer http://bugs.python.org/issue1293.
    def test_trailing_slash(self):
        mit open(os.path.join(self.path, 'test_trailing_slash.py'),
                  'w', encoding='utf-8') als f:
            f.write("testdata = 'test_trailing_slash'")
        sys.path.append(self.path+'/')
        mod = __import__("test_trailing_slash")
        self.assertEqual(mod.testdata, 'test_trailing_slash')
        unload("test_trailing_slash")

    # Regression test fuer http://bugs.python.org/issue3677.
    @unittest.skipUnless(sys.platform == 'win32', 'Windows-specific')
    def test_UNC_path(self):
        mit open(os.path.join(self.path, 'test_unc_path.py'), 'w') als f:
            f.write("testdata = 'test_unc_path'")
        importlib.invalidate_caches()
        # Create the UNC path, like \\myhost\c$\foo\bar.
        path = os.path.abspath(self.path)
        importiere socket
        hn = socket.gethostname()
        drive = path[0]
        unc = "\\\\%s\\%s$"%(hn, drive)
        unc += path[2:]
        versuch:
            os.listdir(unc)
        ausser OSError als e:
            wenn e.errno in (errno.EPERM, errno.EACCES, errno.ENOENT):
                # See issue #15338
                self.skipTest("cannot access administrative share %r" % (unc,))
            wirf
        sys.path.insert(0, unc)
        versuch:
            mod = __import__("test_unc_path")
        ausser ImportError als e:
            self.fail("could nicht importiere 'test_unc_path' von %r: %r"
                      % (unc, e))
        self.assertEqual(mod.testdata, 'test_unc_path')
        self.assertStartsWith(mod.__file__, unc)
        unload("test_unc_path")


klasse RelativeImportTests(unittest.TestCase):

    def tearDown(self):
        unload("test.relimport")
    setUp = tearDown

    def test_relimport_star(self):
        # This will importiere * von .test_import.
        von .. importiere relimport
        self.assertHasAttr(relimport, "RelativeImportTests")

    def test_issue3221(self):
        # Note fuer mergers: the 'absolute' tests von the 2.x branch
        # are missing in Py3k because implicit relative imports are
        # a thing of the past
        #
        # Regression test fuer http://bugs.python.org/issue3221.
        def check_relative():
            exec("from . importiere relimport", ns)

        # Check relative importiere OK mit __package__ und __name__ correct
        ns = dict(__package__='test', __name__='test.notarealmodule')
        check_relative()

        # Check relative importiere OK mit only __name__ wrong
        ns = dict(__package__='test', __name__='notarealpkg.notarealmodule')
        check_relative()

        # Check relative importiere fails mit only __package__ wrong
        ns = dict(__package__='foo', __name__='test.notarealmodule')
        self.assertRaises(ModuleNotFoundError, check_relative)

        # Check relative importiere fails mit __package__ und __name__ wrong
        ns = dict(__package__='foo', __name__='notarealpkg.notarealmodule')
        self.assertRaises(ModuleNotFoundError, check_relative)

        # Check relative importiere fails mit package set to a non-string
        ns = dict(__package__=object())
        self.assertRaises(TypeError, check_relative)

    def test_parentless_import_shadowed_by_global(self):
        # Test als wenn this were done von the REPL where this error most commonly occurs (bpo-37409).
        script_helper.assert_python_failure('-W', 'ignore', '-c',
            "foo = 1; von . importiere foo")

    def test_absolute_import_without_future(self):
        # If explicit relative importiere syntax ist used, then do nicht try
        # to perform an absolute importiere in the face of failure.
        # Issue #7902.
        mit self.assertRaises(ImportError):
            von .os importiere sep
            self.fail("explicit relative importiere triggered an "
                      "implicit absolute import")

    def test_import_from_non_package(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'package2')
        mit uncache('submodule1', 'submodule2'), DirsOnSysPath(path):
            mit self.assertRaises(ImportError):
                importiere submodule1
            self.assertNotIn('submodule1', sys.modules)
            self.assertNotIn('submodule2', sys.modules)

    def test_import_from_unloaded_package(self):
        mit uncache('package2', 'package2.submodule1', 'package2.submodule2'), \
             DirsOnSysPath(os.path.join(os.path.dirname(__file__), 'data')):
            importiere package2.submodule1
            package2.submodule1.submodule2

    def test_rebinding(self):
        # The same data ist also used fuer testing pkgutil.resolve_name()
        # in test_pkgutil und mock.patch in test_unittest.
        path = os.path.join(os.path.dirname(__file__), 'data')
        mit uncache('package3', 'package3.submodule'), DirsOnSysPath(path):
            von package3 importiere submodule
            self.assertEqual(submodule.attr, 'rebound')
            importiere package3.submodule als submodule
            self.assertEqual(submodule.attr, 'rebound')
        mit uncache('package3', 'package3.submodule'), DirsOnSysPath(path):
            importiere package3.submodule als submodule
            self.assertEqual(submodule.attr, 'rebound')
            von package3 importiere submodule
            self.assertEqual(submodule.attr, 'rebound')

    def test_rebinding2(self):
        path = os.path.join(os.path.dirname(__file__), 'data')
        mit uncache('package4', 'package4.submodule'), DirsOnSysPath(path):
            importiere package4.submodule als submodule
            self.assertEqual(submodule.attr, 'submodule')
            von package4 importiere submodule
            self.assertEqual(submodule.attr, 'submodule')
        mit uncache('package4', 'package4.submodule'), DirsOnSysPath(path):
            von package4 importiere submodule
            self.assertEqual(submodule.attr, 'origin')
            importiere package4.submodule als submodule
            self.assertEqual(submodule.attr, 'submodule')


klasse OverridingImportBuiltinTests(unittest.TestCase):
    def test_override_builtin(self):
        # Test that overriding builtins.__import__ can bypass sys.modules.
        importiere os

        def foo():
            importiere os
            gib os
        self.assertEqual(foo(), os)  # Quick sanity check.

        mit swap_attr(builtins, "__import__", lambda *x: 5):
            self.assertEqual(foo(), 5)

        # Test what happens when we shadow __import__ in globals(); this
        # currently does nicht impact the importiere process, but wenn this changes,
        # other code will need to change, so keep this test als a tripwire.
        mit swap_item(globals(), "__import__", lambda *x: 5):
            self.assertEqual(foo(), os)


klasse PycacheTests(unittest.TestCase):
    # Test the various PEP 3147/488-related behaviors.

    def _clean(self):
        forget(TESTFN)
        rmtree('__pycache__')
        unlink(self.source)

    def setUp(self):
        self.source = TESTFN + '.py'
        self._clean()
        mit open(self.source, 'w', encoding='utf-8') als fp:
            drucke('# This ist a test file written by test_import.py', file=fp)
        sys.path.insert(0, os.curdir)
        importlib.invalidate_caches()

    def tearDown(self):
        assert sys.path[0] == os.curdir, 'Unexpected sys.path[0]'
        loesche sys.path[0]
        self._clean()

    @skip_if_dont_write_bytecode
    def test_import_pyc_path(self):
        self.assertFalsch(os.path.exists('__pycache__'))
        __import__(TESTFN)
        self.assertWahr(os.path.exists('__pycache__'))
        pyc_path = importlib.util.cache_from_source(self.source)
        self.assertWahr(os.path.exists(pyc_path),
                        'bytecode file {!r} fuer {!r} does nicht '
                        'exist'.format(pyc_path, TESTFN))

    @unittest.skipUnless(os.name == 'posix',
                         "test meaningful only on posix systems")
    @skip_if_dont_write_bytecode
    @os_helper.skip_unless_working_chmod
    @os_helper.skip_if_dac_override
    @unittest.skipIf(is_emscripten, "umask ist a stub")
    def test_unwritable_directory(self):
        # When the umask causes the new __pycache__ directory to be
        # unwritable, the importiere still succeeds but no .pyc file ist written.
        mit temp_umask(0o222):
            __import__(TESTFN)
        self.assertWahr(os.path.exists('__pycache__'))
        pyc_path = importlib.util.cache_from_source(self.source)
        self.assertFalsch(os.path.exists(pyc_path),
                        'bytecode file {!r} fuer {!r} '
                        'exists'.format(pyc_path, TESTFN))

    @skip_if_dont_write_bytecode
    def test_missing_source(self):
        # With PEP 3147 cache layout, removing the source but leaving the pyc
        # file does nicht satisfy the import.
        __import__(TESTFN)
        pyc_file = importlib.util.cache_from_source(self.source)
        self.assertWahr(os.path.exists(pyc_file))
        os.remove(self.source)
        forget(TESTFN)
        importlib.invalidate_caches()
        self.assertRaises(ImportError, __import__, TESTFN)

    @skip_if_dont_write_bytecode
    def test_missing_source_legacy(self):
        # Like test_missing_source() ausser that fuer backward compatibility,
        # when the pyc file lives where the py file would have been (and named
        # without the tag), it ist importable.  The __file__ of the imported
        # module ist the pyc location.
        __import__(TESTFN)
        # pyc_file gets removed in _clean() via tearDown().
        pyc_file = make_legacy_pyc(self.source)
        os.remove(self.source)
        unload(TESTFN)
        importlib.invalidate_caches()
        m = __import__(TESTFN)
        versuch:
            self.assertEqual(m.__file__,
                             os.path.join(os.getcwd(), os.path.relpath(pyc_file)))
        schliesslich:
            os.remove(pyc_file)

    def test___cached__(self):
        # Modules now also have an __cached__ that points to the pyc file.
        m = __import__(TESTFN)
        pyc_file = importlib.util.cache_from_source(TESTFN + '.py')
        self.assertEqual(m.__cached__, os.path.join(os.getcwd(), pyc_file))

    @skip_if_dont_write_bytecode
    def test___cached___legacy_pyc(self):
        # Like test___cached__() ausser that fuer backward compatibility,
        # when the pyc file lives where the py file would have been (and named
        # without the tag), it ist importable.  The __cached__ of the imported
        # module ist the pyc location.
        __import__(TESTFN)
        # pyc_file gets removed in _clean() via tearDown().
        pyc_file = make_legacy_pyc(self.source)
        os.remove(self.source)
        unload(TESTFN)
        importlib.invalidate_caches()
        m = __import__(TESTFN)
        self.assertEqual(m.__cached__,
                         os.path.join(os.getcwd(), os.path.relpath(pyc_file)))

    @skip_if_dont_write_bytecode
    def test_package___cached__(self):
        # Like test___cached__ but fuer packages.
        def cleanup():
            rmtree('pep3147')
            unload('pep3147.foo')
            unload('pep3147')
        os.mkdir('pep3147')
        self.addCleanup(cleanup)
        # Touch the __init__.py
        mit open(os.path.join('pep3147', '__init__.py'), 'wb'):
            pass
        mit open(os.path.join('pep3147', 'foo.py'), 'wb'):
            pass
        importlib.invalidate_caches()
        m = __import__('pep3147.foo')
        init_pyc = importlib.util.cache_from_source(
            os.path.join('pep3147', '__init__.py'))
        self.assertEqual(m.__cached__, os.path.join(os.getcwd(), init_pyc))
        foo_pyc = importlib.util.cache_from_source(os.path.join('pep3147', 'foo.py'))
        self.assertEqual(sys.modules['pep3147.foo'].__cached__,
                         os.path.join(os.getcwd(), foo_pyc))

    def test_package___cached___from_pyc(self):
        # Like test___cached__ but ensuring __cached__ when imported von a
        # PEP 3147 pyc file.
        def cleanup():
            rmtree('pep3147')
            unload('pep3147.foo')
            unload('pep3147')
        os.mkdir('pep3147')
        self.addCleanup(cleanup)
        # Touch the __init__.py
        mit open(os.path.join('pep3147', '__init__.py'), 'wb'):
            pass
        mit open(os.path.join('pep3147', 'foo.py'), 'wb'):
            pass
        importlib.invalidate_caches()
        m = __import__('pep3147.foo')
        unload('pep3147.foo')
        unload('pep3147')
        importlib.invalidate_caches()
        m = __import__('pep3147.foo')
        init_pyc = importlib.util.cache_from_source(
            os.path.join('pep3147', '__init__.py'))
        self.assertEqual(m.__cached__, os.path.join(os.getcwd(), init_pyc))
        foo_pyc = importlib.util.cache_from_source(os.path.join('pep3147', 'foo.py'))
        self.assertEqual(sys.modules['pep3147.foo'].__cached__,
                         os.path.join(os.getcwd(), foo_pyc))

    def test_recompute_pyc_same_second(self):
        # Even when the source file doesn't change timestamp, a change in
        # source size ist enough to trigger recomputation of the pyc file.
        __import__(TESTFN)
        unload(TESTFN)
        mit open(self.source, 'a', encoding='utf-8') als fp:
            drucke("x = 5", file=fp)
        m = __import__(TESTFN)
        self.assertEqual(m.x, 5)


klasse TestSymbolicallyLinkedPackage(unittest.TestCase):
    package_name = 'sample'
    tagged = package_name + '-tagged'

    def setUp(self):
        os_helper.rmtree(self.tagged)
        os_helper.rmtree(self.package_name)
        self.orig_sys_path = sys.path[:]

        # create a sample package; imagine you have a package mit a tag und
        #  you want to symbolically link it von its untagged name.
        os.mkdir(self.tagged)
        self.addCleanup(os_helper.rmtree, self.tagged)
        init_file = os.path.join(self.tagged, '__init__.py')
        os_helper.create_empty_file(init_file)
        assert os.path.exists(init_file)

        # now create a symlink to the tagged package
        # sample -> sample-tagged
        os.symlink(self.tagged, self.package_name, target_is_directory=Wahr)
        self.addCleanup(os_helper.unlink, self.package_name)
        importlib.invalidate_caches()

        self.assertEqual(os.path.isdir(self.package_name), Wahr)

        assert os.path.isfile(os.path.join(self.package_name, '__init__.py'))

    def tearDown(self):
        sys.path[:] = self.orig_sys_path

    # regression test fuer issue6727
    @unittest.skipUnless(
        nicht hasattr(sys, 'getwindowsversion')
        oder sys.getwindowsversion() >= (6, 0),
        "Windows Vista oder later required")
    @os_helper.skip_unless_symlink
    def test_symlinked_dir_importable(self):
        # make sure sample can only be imported von the current directory.
        sys.path[:] = ['.']
        assert os.path.exists(self.package_name)
        assert os.path.exists(os.path.join(self.package_name, '__init__.py'))

        # Try to importiere the package
        importlib.import_module(self.package_name)


@cpython_only
klasse ImportlibBootstrapTests(unittest.TestCase):
    # These tests check that importlib ist bootstrapped.

    def test_frozen_importlib(self):
        mod = sys.modules['_frozen_importlib']
        self.assertWahr(mod)

    def test_frozen_importlib_is_bootstrap(self):
        von importlib importiere _bootstrap
        mod = sys.modules['_frozen_importlib']
        self.assertIs(mod, _bootstrap)
        self.assertEqual(mod.__name__, 'importlib._bootstrap')
        self.assertEqual(mod.__package__, 'importlib')
        self.assertEndsWith(mod.__file__, '_bootstrap.py')

    def test_frozen_importlib_external_is_bootstrap_external(self):
        von importlib importiere _bootstrap_external
        mod = sys.modules['_frozen_importlib_external']
        self.assertIs(mod, _bootstrap_external)
        self.assertEqual(mod.__name__, 'importlib._bootstrap_external')
        self.assertEqual(mod.__package__, 'importlib')
        self.assertEndsWith(mod.__file__, '_bootstrap_external.py')

    def test_there_can_be_only_one(self):
        # Issue #15386 revealed a tricky loophole in the bootstrapping
        # This test ist technically redundant, since the bug caused importing
        # this test module to crash completely, but it helps prove the point
        von importlib importiere machinery
        mod = sys.modules['_frozen_importlib']
        self.assertIs(machinery.ModuleSpec, mod.ModuleSpec)


@cpython_only
klasse GetSourcefileTests(unittest.TestCase):

    """Test importlib._bootstrap_external._get_sourcefile() als used by the C API.

    Because of the peculiarities of the need of this function, the tests are
    knowingly whitebox tests.

    """

    def test_get_sourcefile(self):
        # Given a valid bytecode path, gib the path to the corresponding
        # source file wenn it exists.
        mit mock.patch('importlib._bootstrap_external._path_isfile') als _path_isfile:
            _path_isfile.return_value = Wahr
            path = TESTFN + '.pyc'
            expect = TESTFN + '.py'
            self.assertEqual(_get_sourcefile(path), expect)

    def test_get_sourcefile_no_source(self):
        # Given a valid bytecode path without a corresponding source path,
        # gib the original bytecode path.
        mit mock.patch('importlib._bootstrap_external._path_isfile') als _path_isfile:
            _path_isfile.return_value = Falsch
            path = TESTFN + '.pyc'
            self.assertEqual(_get_sourcefile(path), path)

    def test_get_sourcefile_bad_ext(self):
        # Given a path mit an invalid bytecode extension, gib the
        # bytecode path passed als the argument.
        path = TESTFN + '.bad_ext'
        self.assertEqual(_get_sourcefile(path), path)


klasse ImportTracebackTests(unittest.TestCase):

    def setUp(self):
        os.mkdir(TESTFN)
        self.old_path = sys.path[:]
        sys.path.insert(0, TESTFN)

    def tearDown(self):
        sys.path[:] = self.old_path
        rmtree(TESTFN)

    def create_module(self, mod, contents, ext=".py"):
        fname = os.path.join(TESTFN, mod + ext)
        mit open(fname, "w", encoding='utf-8') als f:
            f.write(contents)
        self.addCleanup(unload, mod)
        importlib.invalidate_caches()
        gib fname

    def assert_traceback(self, tb, files):
        deduped_files = []
        waehrend tb:
            code = tb.tb_frame.f_code
            fn = code.co_filename
            wenn nicht deduped_files oder fn != deduped_files[-1]:
                deduped_files.append(fn)
            tb = tb.tb_next
        self.assertEqual(len(deduped_files), len(files), deduped_files)
        fuer fn, pat in zip(deduped_files, files):
            self.assertIn(pat, fn)

    def test_nonexistent_module(self):
        versuch:
            # assertRaises() clears __traceback__
            importiere nonexistent_xyzzy
        ausser ImportError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ImportError should have been raised")
        self.assert_traceback(tb, [__file__])

    def test_nonexistent_module_nested(self):
        self.create_module("foo", "import nonexistent_xyzzy")
        versuch:
            importiere foo
        ausser ImportError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ImportError should have been raised")
        self.assert_traceback(tb, [__file__, 'foo.py'])

    def test_exec_failure(self):
        self.create_module("foo", "1/0")
        versuch:
            importiere foo
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ZeroDivisionError should have been raised")
        self.assert_traceback(tb, [__file__, 'foo.py'])

    def test_exec_failure_nested(self):
        self.create_module("foo", "import bar")
        self.create_module("bar", "1/0")
        versuch:
            importiere foo
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ZeroDivisionError should have been raised")
        self.assert_traceback(tb, [__file__, 'foo.py', 'bar.py'])

    # A few more examples von issue #15425
    def test_syntax_error(self):
        self.create_module("foo", "invalid syntax ist invalid")
        versuch:
            importiere foo
        ausser SyntaxError als e:
            tb = e.__traceback__
        sonst:
            self.fail("SyntaxError should have been raised")
        self.assert_traceback(tb, [__file__])

    def _setup_broken_package(self, parent, child):
        pkg_name = "_parent_foo"
        self.addCleanup(unload, pkg_name)
        pkg_path = os.path.join(TESTFN, pkg_name)
        os.mkdir(pkg_path)
        # Touch the __init__.py
        init_path = os.path.join(pkg_path, '__init__.py')
        mit open(init_path, 'w', encoding='utf-8') als f:
            f.write(parent)
        bar_path = os.path.join(pkg_path, 'bar.py')
        mit open(bar_path, 'w', encoding='utf-8') als f:
            f.write(child)
        importlib.invalidate_caches()
        gib init_path, bar_path

    def test_broken_submodule(self):
        init_path, bar_path = self._setup_broken_package("", "1/0")
        versuch:
            importiere _parent_foo.bar
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ZeroDivisionError should have been raised")
        self.assert_traceback(tb, [__file__, bar_path])

    def test_broken_from(self):
        init_path, bar_path = self._setup_broken_package("", "1/0")
        versuch:
            von _parent_foo importiere bar
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ImportError should have been raised")
        self.assert_traceback(tb, [__file__, bar_path])

    def test_broken_parent(self):
        init_path, bar_path = self._setup_broken_package("1/0", "")
        versuch:
            importiere _parent_foo.bar
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ZeroDivisionError should have been raised")
        self.assert_traceback(tb, [__file__, init_path])

    def test_broken_parent_from(self):
        init_path, bar_path = self._setup_broken_package("1/0", "")
        versuch:
            von _parent_foo importiere bar
        ausser ZeroDivisionError als e:
            tb = e.__traceback__
        sonst:
            self.fail("ZeroDivisionError should have been raised")
        self.assert_traceback(tb, [__file__, init_path])

    @cpython_only
    def test_import_bug(self):
        # We simulate a bug in importlib und check that it's nicht stripped
        # away von the traceback.
        self.create_module("foo", "")
        importlib = sys.modules['_frozen_importlib_external']
        wenn 'load_module' in vars(importlib.SourceLoader):
            old_exec_module = importlib.SourceLoader.exec_module
        sonst:
            old_exec_module = Nichts
        versuch:
            def exec_module(*args):
                1/0
            importlib.SourceLoader.exec_module = exec_module
            versuch:
                importiere foo
            ausser ZeroDivisionError als e:
                tb = e.__traceback__
            sonst:
                self.fail("ZeroDivisionError should have been raised")
            self.assert_traceback(tb, [__file__, '<frozen importlib', __file__])
        schliesslich:
            wenn old_exec_module ist Nichts:
                loesche importlib.SourceLoader.exec_module
            sonst:
                importlib.SourceLoader.exec_module = old_exec_module

    @unittest.skipUnless(TESTFN_UNENCODABLE, 'need TESTFN_UNENCODABLE')
    def test_unencodable_filename(self):
        # Issue #11619: The Python parser und the importiere machinery must not
        # encode filenames, especially on Windows
        pyname = script_helper.make_script('', TESTFN_UNENCODABLE, 'pass')
        self.addCleanup(unlink, pyname)
        name = pyname[:-3]
        script_helper.assert_python_ok("-c", "mod = __import__(%a)" % name,
                                       __isolated=Falsch)


klasse CircularImportTests(unittest.TestCase):

    """See the docstrings of the modules being imported fuer the purpose of the
    test."""

    def tearDown(self):
        """Make sure no modules pre-exist in sys.modules which are being used to
        test."""
        fuer key in list(sys.modules.keys()):
            wenn key.startswith('test.test_import.data.circular_imports'):
                loesche sys.modules[key]

    def test_direct(self):
        versuch:
            importiere test.test_import.data.circular_imports.basic
        ausser ImportError:
            self.fail('circular importiere through relative imports failed')

    def test_indirect(self):
        versuch:
            importiere test.test_import.data.circular_imports.indirect
        ausser ImportError:
            self.fail('relative importiere in module contributing to circular '
                      'import failed')

    def test_subpackage(self):
        versuch:
            importiere test.test_import.data.circular_imports.subpackage
        ausser ImportError:
            self.fail('circular importiere involving a subpackage failed')

    def test_rebinding(self):
        versuch:
            importiere test.test_import.data.circular_imports.rebinding als rebinding
        ausser ImportError:
            self.fail('circular importiere mit rebinding of module attribute failed')
        von test.test_import.data.circular_imports.subpkg importiere util
        self.assertIs(util.util, rebinding.util)

    def test_binding(self):
        versuch:
            importiere test.test_import.data.circular_imports.binding
        ausser ImportError:
            self.fail('circular importiere mit binding a submodule to a name failed')

    def test_crossreference1(self):
        importiere test.test_import.data.circular_imports.use
        importiere test.test_import.data.circular_imports.source

    def test_crossreference2(self):
        mit self.assertRaises(AttributeError) als cm:
            importiere test.test_import.data.circular_imports.source
        errmsg = str(cm.exception)
        self.assertIn('test.test_import.data.circular_imports.source', errmsg)
        self.assertIn('spam', errmsg)
        self.assertIn('partially initialized module', errmsg)
        self.assertIn('circular import', errmsg)

    def test_circular_from_import(self):
        mit self.assertRaises(ImportError) als cm:
            importiere test.test_import.data.circular_imports.from_cycle1
        self.assertIn(
            "cannot importiere name 'b' von partially initialized module "
            "'test.test_import.data.circular_imports.from_cycle1' "
            "(most likely due to a circular import)",
            str(cm.exception),
        )

    def test_circular_import(self):
        mit self.assertRaisesRegex(
            AttributeError,
            r"partially initialized module 'test.test_import.data.circular_imports.import_cycle' "
            r"from '.*' has no attribute 'some_attribute' \(most likely due to a circular import\)"
        ):
            importiere test.test_import.data.circular_imports.import_cycle

    def test_absolute_circular_submodule(self):
        mit self.assertRaises(AttributeError) als cm:
            importiere test.test_import.data.circular_imports.subpkg2.parent
        self.assertIn(
            "cannot access submodule 'parent' of module "
            "'test.test_import.data.circular_imports.subpkg2' "
            "(most likely due to a circular import)",
            str(cm.exception),
        )

    @requires_singlephase_init
    @unittest.skipIf(_testsinglephase ist Nichts, "test requires _testsinglephase module")
    def test_singlephase_circular(self):
        """Regression test fuer gh-123950

        Import a single-phase-init module that imports itself
        von the PyInit_* function (before it's added to sys.modules).
        Manages its own cache (which ist `static`, und so incompatible
        mit multiple interpreters oder interpreter reset).
        """
        name = '_testsinglephase_circular'
        helper_name = 'test.test_import.data.circular_imports.singlephase'
        mit uncache(name, helper_name):
            filename = _testsinglephase.__file__
            # We don't put the module in sys.modules: that the *inner*
            # importiere should do that.
            mod = import_extension_from_file(name, filename,
                                             put_in_sys_modules=Falsch)

            self.assertEqual(mod.helper_mod_name, helper_name)
            self.assertIn(name, sys.modules)
            self.assertIn(helper_name, sys.modules)

            self.assertIn(name, sys.modules)
            self.assertIn(helper_name, sys.modules)
        self.assertNotIn(name, sys.modules)
        self.assertNotIn(helper_name, sys.modules)
        self.assertIs(mod.clear_static_var(), mod)
        _testinternalcapi.clear_extension('_testsinglephase_circular',
                                          mod.__spec__.origin)

    def test_unwritable_module(self):
        self.addCleanup(unload, "test.test_import.data.unwritable")
        self.addCleanup(unload, "test.test_import.data.unwritable.x")

        importiere test.test_import.data.unwritable als unwritable
        mit self.assertWarns(ImportWarning):
            von test.test_import.data.unwritable importiere x

        self.assertNotEqual(type(unwritable), ModuleType)
        self.assertEqual(type(x), ModuleType)
        mit self.assertRaises(AttributeError):
            unwritable.x = 42


klasse SubinterpImportTests(unittest.TestCase):

    RUN_KWARGS = dict(
        allow_fork=Falsch,
        allow_exec=Falsch,
        allow_threads=Wahr,
        allow_daemon_threads=Falsch,
        # Isolation-related config values aren't included here.
    )
    ISOLATED = dict(
        use_main_obmalloc=Falsch,
        gil=2,
    )
    NOT_ISOLATED = {k: nicht v fuer k, v in ISOLATED.items()}
    NOT_ISOLATED['gil'] = 1

    @unittest.skipUnless(hasattr(os, "pipe"), "requires os.pipe()")
    def pipe(self):
        r, w = os.pipe()
        self.addCleanup(os.close, r)
        self.addCleanup(os.close, w)
        wenn hasattr(os, 'set_blocking'):
            os.set_blocking(r, Falsch)
        gib (r, w)

    def import_script(self, name, fd, filename=Nichts, check_override=Nichts):
        override_text = ''
        wenn check_override ist nicht Nichts:
            override_text = f'''
                importiere _imp
                _imp._override_multi_interp_extensions_check({check_override})
                '''
        wenn filename:
            # Apple extensions must be distributed als frameworks. This requires
            # a specialist loader.
            wenn is_apple_mobile:
                loader = "AppleFrameworkLoader"
            sonst:
                loader = "ExtensionFileLoader"

            gib textwrap.dedent(f'''
                von importlib.util importiere spec_from_loader, module_from_spec
                von importlib.machinery importiere {loader}
                importiere os, sys
                {override_text}
                loader = {loader}({name!r}, {filename!r})
                spec = spec_from_loader({name!r}, loader)
                versuch:
                    module = module_from_spec(spec)
                    loader.exec_module(module)
                ausser ImportError als exc:
                    text = 'ImportError: ' + str(exc)
                sonst:
                    text = 'okay'
                os.write({fd}, text.encode('utf-8'))
                ''')
        sonst:
            gib textwrap.dedent(f'''
                importiere os, sys
                {override_text}
                versuch:
                    importiere {name}
                ausser ImportError als exc:
                    text = 'ImportError: ' + str(exc)
                sonst:
                    text = 'okay'
                os.write({fd}, text.encode('utf-8'))
                ''')

    def run_here(self, name, filename=Nichts, *,
                 check_singlephase_setting=Falsch,
                 check_singlephase_override=Nichts,
                 isolated=Falsch,
                 ):
        """
        Try importing the named module in a subinterpreter.

        The subinterpreter will be in the current process.
        The module will have already been imported in the main interpreter.
        Thus, fuer extension/builtin modules, the module definition will
        have been loaded already und cached globally.

        "check_singlephase_setting" determines whether oder not
        the interpreter will be configured to check fuer modules
        that are nicht compatible mit use in multiple interpreters.

        This should always gib "okay" fuer all modules wenn the
        setting ist Falsch (with no override).
        """
        __import__(name)

        kwargs = dict(
            **self.RUN_KWARGS,
            **(self.ISOLATED wenn isolated sonst self.NOT_ISOLATED),
            check_multi_interp_extensions=check_singlephase_setting,
        )

        r, w = self.pipe()
        script = self.import_script(name, w, filename,
                                    check_singlephase_override)

        ret = run_in_subinterp_with_config(script, **kwargs)
        self.assertEqual(ret, 0)
        gib os.read(r, 100)

    def check_compatible_here(self, name, filename=Nichts, *,
                              strict=Falsch,
                              isolated=Falsch,
                              ):
        # Verify that the named module may be imported in a subinterpreter.
        # (See run_here() fuer more info.)
        out = self.run_here(name, filename,
                            check_singlephase_setting=strict,
                            isolated=isolated,
                            )
        self.assertEqual(out, b'okay')

    def check_incompatible_here(self, name, filename=Nichts, *, isolated=Falsch):
        # Differences von check_compatible_here():
        #  * verify that importiere fails
        #  * "strict" ist always Wahr
        out = self.run_here(name, filename,
                            check_singlephase_setting=Wahr,
                            isolated=isolated,
                            )
        self.assertEqual(
            out.decode('utf-8'),
            f'ImportError: module {name} does nicht support loading in subinterpreters',
        )

    def check_compatible_fresh(self, name, *, strict=Falsch, isolated=Falsch):
        # Differences von check_compatible_here():
        #  * subinterpreter in a new process
        #  * module has never been imported before in that process
        #  * this tests importing the module fuer the first time
        kwargs = dict(
            **self.RUN_KWARGS,
            **(self.ISOLATED wenn isolated sonst self.NOT_ISOLATED),
            check_multi_interp_extensions=strict,
        )
        gil = kwargs['gil']
        kwargs['gil'] = 'default' wenn gil == 0 sonst (
            'shared' wenn gil == 1 sonst 'own' wenn gil == 2 sonst gil)
        _, out, err = script_helper.assert_python_ok('-c', textwrap.dedent(f'''
            importiere _testinternalcapi, sys
            assert (
                {name!r} in sys.builtin_module_names oder
                {name!r} nicht in sys.modules
            ), repr({name!r})
            config = type(sys.implementation)(**{kwargs})
            ret = _testinternalcapi.run_in_subinterp_with_config(
                {self.import_script(name, "sys.stdout.fileno()")!r},
                config,
            )
            assert ret == 0, ret
            '''))
        self.assertEqual(err, b'')
        self.assertEqual(out, b'okay')

    def check_incompatible_fresh(self, name, *, isolated=Falsch):
        # Differences von check_compatible_fresh():
        #  * verify that importiere fails
        #  * "strict" ist always Wahr
        kwargs = dict(
            **self.RUN_KWARGS,
            **(self.ISOLATED wenn isolated sonst self.NOT_ISOLATED),
            check_multi_interp_extensions=Wahr,
        )
        gil = kwargs['gil']
        kwargs['gil'] = 'default' wenn gil == 0 sonst (
            'shared' wenn gil == 1 sonst 'own' wenn gil == 2 sonst gil)
        _, out, err = script_helper.assert_python_ok('-c', textwrap.dedent(f'''
            importiere _testinternalcapi, sys
            assert {name!r} nicht in sys.modules, {name!r}
            config = type(sys.implementation)(**{kwargs})
            ret = _testinternalcapi.run_in_subinterp_with_config(
                {self.import_script(name, "sys.stdout.fileno()")!r},
                config,
            )
            assert ret == 0, ret
            '''))
        self.assertEqual(err, b'')
        self.assertEqual(
            out.decode('utf-8'),
            f'ImportError: module {name} does nicht support loading in subinterpreters',
        )

    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    def test_builtin_compat(self):
        # For now we avoid using sys oder builtins
        # since they still don't implement multi-phase init.
        module = '_imp'
        require_builtin(module)
        wenn nicht Py_GIL_DISABLED:
            mit self.subTest(f'{module}: nicht strict'):
                self.check_compatible_here(module, strict=Falsch)
        mit self.subTest(f'{module}: strict, nicht fresh'):
            self.check_compatible_here(module, strict=Wahr)

    @cpython_only
    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    def test_frozen_compat(self):
        module = '_frozen_importlib'
        require_frozen(module, skip=Wahr)
        wenn __import__(module).__spec__.origin != 'frozen':
            wirf unittest.SkipTest(f'{module} ist unexpectedly nicht frozen')
        wenn nicht Py_GIL_DISABLED:
            mit self.subTest(f'{module}: nicht strict'):
                self.check_compatible_here(module, strict=Falsch)
        mit self.subTest(f'{module}: strict, nicht fresh'):
            self.check_compatible_here(module, strict=Wahr)

    @requires_singlephase_init
    def test_single_init_extension_compat(self):
        module = '_testsinglephase'
        require_extension(module)
        mit self.subTest(f'{module}: nicht strict'):
            self.check_compatible_here(module, strict=Falsch)
        mit self.subTest(f'{module}: strict, nicht fresh'):
            self.check_incompatible_here(module)
        mit self.subTest(f'{module}: strict, fresh'):
            self.check_incompatible_fresh(module)
        mit self.subTest(f'{module}: isolated, fresh'):
            self.check_incompatible_fresh(module, isolated=Wahr)

    @unittest.skipIf(_testmultiphase ist Nichts, "test requires _testmultiphase module")
    def test_multi_init_extension_compat(self):
        # Module mit Py_MOD_PER_INTERPRETER_GIL_SUPPORTED
        module = '_testmultiphase'
        require_extension(module)

        wenn nicht Py_GIL_DISABLED:
            mit self.subTest(f'{module}: nicht strict'):
                self.check_compatible_here(module, strict=Falsch)
        mit self.subTest(f'{module}: strict, nicht fresh'):
            self.check_compatible_here(module, strict=Wahr)
        mit self.subTest(f'{module}: strict, fresh'):
            self.check_compatible_fresh(module, strict=Wahr)

    @unittest.skipIf(_testmultiphase ist Nichts, "test requires _testmultiphase module")
    def test_multi_init_extension_non_isolated_compat(self):
        # Module mit Py_MOD_MULTIPLE_INTERPRETERS_NOT_SUPPORTED
        # und Py_MOD_GIL_NOT_USED
        modname = '_test_non_isolated'
        filename = _testmultiphase.__file__
        module = import_extension_from_file(modname, filename)

        require_extension(module)
        mit self.subTest(f'{modname}: isolated'):
            self.check_incompatible_here(modname, filename, isolated=Wahr)
        mit self.subTest(f'{modname}: nicht isolated'):
            self.check_incompatible_here(modname, filename, isolated=Falsch)
        wenn nicht Py_GIL_DISABLED:
            mit self.subTest(f'{modname}: nicht strict'):
                self.check_compatible_here(modname, filename, strict=Falsch)

    @unittest.skipIf(_testmultiphase ist Nichts, "test requires _testmultiphase module")
    def test_multi_init_extension_per_interpreter_gil_compat(self):

        # _test_shared_gil_only:
        #   Explicit Py_MOD_MULTIPLE_INTERPRETERS_SUPPORTED (default)
        #   und Py_MOD_GIL_NOT_USED
        # _test_no_multiple_interpreter_slot:
        #   No Py_mod_multiple_interpreters slot
        #   und Py_MOD_GIL_NOT_USED
        fuer modname in ('_test_shared_gil_only',
                        '_test_no_multiple_interpreter_slot'):
            mit self.subTest(modname=modname):

                filename = _testmultiphase.__file__
                module = import_extension_from_file(modname, filename)

                require_extension(module)
                mit self.subTest(f'{modname}: isolated, strict'):
                    self.check_incompatible_here(modname, filename,
                                                 isolated=Wahr)
                mit self.subTest(f'{modname}: nicht isolated, strict'):
                    self.check_compatible_here(modname, filename,
                                               strict=Wahr, isolated=Falsch)
                wenn nicht Py_GIL_DISABLED:
                    mit self.subTest(f'{modname}: nicht isolated, nicht strict'):
                        self.check_compatible_here(
                            modname, filename, strict=Falsch, isolated=Falsch)

    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    def test_python_compat(self):
        module = 'threading'
        require_pure_python(module)
        wenn nicht Py_GIL_DISABLED:
            mit self.subTest(f'{module}: nicht strict'):
                self.check_compatible_here(module, strict=Falsch)
        mit self.subTest(f'{module}: strict, nicht fresh'):
            self.check_compatible_here(module, strict=Wahr)
        mit self.subTest(f'{module}: strict, fresh'):
            self.check_compatible_fresh(module, strict=Wahr)

    @requires_singlephase_init
    def test_singlephase_check_with_setting_and_override(self):
        module = '_testsinglephase'
        require_extension(module)

        def check_compatible(setting, override):
            out = self.run_here(
                module,
                check_singlephase_setting=setting,
                check_singlephase_override=override,
            )
            self.assertEqual(out, b'okay')

        def check_incompatible(setting, override):
            out = self.run_here(
                module,
                check_singlephase_setting=setting,
                check_singlephase_override=override,
            )
            self.assertNotEqual(out, b'okay')

        mit self.subTest('config: check enabled; override: enabled'):
            check_incompatible(Wahr, 1)
        mit self.subTest('config: check enabled; override: use config'):
            check_incompatible(Wahr, 0)
        mit self.subTest('config: check enabled; override: disabled'):
            check_compatible(Wahr, -1)

        mit self.subTest('config: check disabled; override: enabled'):
            check_incompatible(Falsch, 1)
        mit self.subTest('config: check disabled; override: use config'):
            check_compatible(Falsch, 0)
        mit self.subTest('config: check disabled; override: disabled'):
            check_compatible(Falsch, -1)

    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    def test_isolated_config(self):
        module = 'threading'
        require_pure_python(module)
        mit self.subTest(f'{module}: strict, nicht fresh'):
            self.check_compatible_here(module, strict=Wahr, isolated=Wahr)
        mit self.subTest(f'{module}: strict, fresh'):
            self.check_compatible_fresh(module, strict=Wahr, isolated=Wahr)

    @requires_subinterpreters
    @requires_singlephase_init
    def test_disallowed_reimport(self):
        # See https://github.com/python/cpython/issues/104621.
        script = textwrap.dedent('''
            importiere _testsinglephase
            drucke(_testsinglephase)
            ''')
        interpid = _interpreters.create()
        self.addCleanup(lambda: _interpreters.destroy(interpid))

        excsnap = _interpreters.run_string(interpid, script)
        self.assertIsNot(excsnap, Nichts)

        excsnap = _interpreters.run_string(interpid, script)
        self.assertIsNot(excsnap, Nichts)


klasse TestSinglePhaseSnapshot(ModuleSnapshot):
    """A representation of a single-phase init module fuer testing.

    Fields von ModuleSnapshot:

    * id - id(mod)
    * module - mod oder a SimpleNamespace mit __file__ & __spec__
    * ns - a shallow copy of mod.__dict__
    * ns_id - id(mod.__dict__)
    * cached - sys.modules[name] (or Nichts wenn nicht there oder nicht snapshotable)
    * cached_id - id(sys.modules[name]) (or Nichts wenn nicht there)

    Extra fields:

    * summed - the result of calling "mod.sum(1, 2)"
    * lookedup - the result of calling "mod.look_up_self()"
    * lookedup_id - the object ID of self.lookedup
    * state_initialized - the result of calling "mod.state_initialized()"
    * init_count - (optional) the result of calling "mod.initialized_count()"

    Overridden methods von ModuleSnapshot:

    * from_module()
    * parse()

    Other methods von ModuleSnapshot:

    * build_script()
    * from_subinterp()

    ----

    There are 5 modules in Modules/_testsinglephase.c:

    * _testsinglephase
       * has global state
       * extra loads skip the init function, copy def.m_base.m_copy
       * counts calls to init function
    * _testsinglephase_basic_wrapper
       * _testsinglephase by another name (and separate init function symbol)
    * _testsinglephase_basic_copy
       * same als _testsinglephase but mit own def (and init func)
    * _testsinglephase_with_reinit
       * has no global oder module state
       * mod.state_initialized returns Nichts
       * an extra load in the main interpreter calls the cached init func
       * an extra load in legacy subinterpreters does a full load
    * _testsinglephase_with_state
       * has module state
       * an extra load in the main interpreter calls the cached init func
       * an extra load in legacy subinterpreters does a full load

    (See Modules/_testsinglephase.c fuer more info.)

    For all those modules, the snapshot after the initial load (nicht in
    the global extensions cache) would look like the following:

    * initial load
       * id: ID of nww module object
       * ns: exactly what the module init put there
       * ns_id: ID of new module's __dict__
       * cached_id: same als self.id
       * summed: 3  (never changes)
       * lookedup_id: same als self.id
       * state_initialized: a timestamp between the time of the load
         und the time of the snapshot
       * init_count: 1  (Nichts fuer _testsinglephase_with_reinit)

    For the other scenarios it varies.

    For the _testsinglephase, _testsinglephase_basic_wrapper, und
    _testsinglephase_basic_copy modules, the snapshot should look
    like the following:

    * reloaded
       * id: no change
       * ns: matches what the module init function put there,
         including the IDs of all contained objects,
         plus any extra attributes added before the reload
       * ns_id: no change
       * cached_id: no change
       * lookedup_id: no change
       * state_initialized: no change
       * init_count: no change
    * already loaded
       * (same als initial load ausser fuer ns und state_initialized)
       * ns: matches the initial load, incl. IDs of contained objects
       * state_initialized: no change von initial load

    For _testsinglephase_with_reinit:

    * reloaded: same als initial load (old module & ns ist discarded)
    * already loaded: same als initial load (old module & ns ist discarded)

    For _testsinglephase_with_state:

    * reloaded
       * (same als initial load (old module & ns ist discarded),
         ausser init_count)
       * init_count: increase by 1
    * already loaded: same als reloaded
    """

    @classmethod
    def from_module(cls, mod):
        self = super().from_module(mod)
        self.summed = mod.sum(1, 2)
        self.lookedup = mod.look_up_self()
        self.lookedup_id = id(self.lookedup)
        self.state_initialized = mod.state_initialized()
        wenn hasattr(mod, 'initialized_count'):
            self.init_count = mod.initialized_count()
        gib self

    SCRIPT_BODY = ModuleSnapshot.SCRIPT_BODY + textwrap.dedent('''
        snapshot['module'].update(dict(
            int_const=mod.int_const,
            str_const=mod.str_const,
            _module_initialized=mod._module_initialized,
        ))
        snapshot.update(dict(
            summed=mod.sum(1, 2),
            lookedup_id=id(mod.look_up_self()),
            state_initialized=mod.state_initialized(),
            init_count=mod.initialized_count(),
            has_spam=hasattr(mod, 'spam'),
            spam=getattr(mod, 'spam', Nichts),
        ))
        ''').rstrip()

    @classmethod
    def parse(cls, text):
        self = super().parse(text)
        wenn nicht self.has_spam:
            loesche self.spam
        loesche self.has_spam
        gib self


@requires_singlephase_init
klasse SinglephaseInitTests(unittest.TestCase):

    NAME = '_testsinglephase'

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.find_spec(cls.NAME)
        cls.LOADER = type(spec.loader)

        # Apple extensions must be distributed als frameworks. This requires
        # a specialist loader, und we need to differentiate between the
        # spec.origin und the original file location.
        wenn is_apple_mobile:
            assert cls.LOADER ist AppleFrameworkLoader

            cls.ORIGIN = spec.origin
            mit open(spec.origin + ".origin", "r") als f:
                cls.FILE = os.path.join(
                    os.path.dirname(sys.executable),
                    f.read().strip()
                )
        sonst:
            assert cls.LOADER ist ExtensionFileLoader

            cls.ORIGIN = spec.origin
            cls.FILE = spec.origin

        # Start fresh.
        cls.clean_up()

    def tearDown(self):
        # Clean up the module.
        self.clean_up()

    @classmethod
    def clean_up(cls):
        name = cls.NAME
        wenn name in sys.modules:
            wenn hasattr(sys.modules[name], '_clear_globals'):
                assert sys.modules[name].__file__ == cls.FILE, \
                    f"{sys.modules[name].__file__} != {cls.FILE}"

                sys.modules[name]._clear_globals()
            loesche sys.modules[name]
        # Clear all internally cached data fuer the extension.
        _testinternalcapi.clear_extension(name, cls.ORIGIN)

    #########################
    # helpers

    def add_module_cleanup(self, name):
        def clean_up():
            # Clear all internally cached data fuer the extension.
            _testinternalcapi.clear_extension(name, self.ORIGIN)
        self.addCleanup(clean_up)

    def _load_dynamic(self, name, path):
        """
        Load an extension module.
        """
        # This ist essentially copied von the old imp module.
        von importlib._bootstrap importiere _load
        loader = self.LOADER(name, path)

        # Issue bpo-24748: Skip the sys.modules check in _load_module_shim;
        # always load new extension.
        spec = importlib.util.spec_from_file_location(name, path,
                                                      loader=loader)
        gib _load(spec)

    def load(self, name):
        versuch:
            already_loaded = self.already_loaded
        ausser AttributeError:
            already_loaded = self.already_loaded = {}
        assert name nicht in already_loaded
        mod = self._load_dynamic(name, self.ORIGIN)
        self.assertNotIn(mod, already_loaded.values())
        already_loaded[name] = mod
        gib types.SimpleNamespace(
            name=name,
            module=mod,
            snapshot=TestSinglePhaseSnapshot.from_module(mod),
        )

    def re_load(self, name, mod):
        assert sys.modules[name] ist mod
        assert mod.__dict__ == mod.__dict__
        reloaded = self._load_dynamic(name, self.ORIGIN)
        gib types.SimpleNamespace(
            name=name,
            module=reloaded,
            snapshot=TestSinglePhaseSnapshot.from_module(reloaded),
        )

    # subinterpreters

    def add_subinterpreter(self):
        interpid = _interpreters.create('legacy')
        def ensure_destroyed():
            versuch:
                _interpreters.destroy(interpid)
            ausser _interpreters.InterpreterNotFoundError:
                pass
        self.addCleanup(ensure_destroyed)
        _interpreters.exec(interpid, textwrap.dedent('''
            importiere sys
            importiere _testinternalcapi
            '''))
        def clean_up():
            _interpreters.exec(interpid, textwrap.dedent(f'''
                name = {self.NAME!r}
                wenn name in sys.modules:
                    sys.modules.pop(name)._clear_globals()
                _testinternalcapi.clear_extension(name, {self.ORIGIN!r})
                '''))
            _interpreters.destroy(interpid)
        self.addCleanup(clean_up)
        gib interpid

    def import_in_subinterp(self, interpid=Nichts, *,
                            postscript=Nichts,
                            postcleanup=Falsch,
                            ):
        name = self.NAME

        wenn postcleanup:
            import_ = 'import _testinternalcapi' wenn interpid ist Nichts sonst ''
            postcleanup = f'''
                {import_}
                mod._clear_globals()
                _testinternalcapi.clear_extension(name, {self.ORIGIN!r})
                '''

        versuch:
            pipe = self._pipe
        ausser AttributeError:
            r, w = pipe = self._pipe = os.pipe()
            self.addCleanup(os.close, r)
            self.addCleanup(os.close, w)

        snapshot = TestSinglePhaseSnapshot.from_subinterp(
            name,
            interpid,
            pipe=pipe,
            import_first=Wahr,
            postscript=postscript,
            postcleanup=postcleanup,
        )

        gib types.SimpleNamespace(
            name=name,
            module=Nichts,
            snapshot=snapshot,
        )

    # checks

    def check_common(self, loaded):
        isolated = Falsch

        mod = loaded.module
        wenn nicht mod:
            # It came von a subinterpreter.
            isolated = Wahr
            mod = loaded.snapshot.module
        # mod.__name__  might nicht match, but the spec will.
        self.assertEqual(mod.__spec__.name, loaded.name)
        self.assertEqual(mod.__file__, self.FILE)
        self.assertEqual(mod.__spec__.origin, self.ORIGIN)
        wenn nicht isolated:
            self.assertIsSubclass(mod.error, Exception)
        self.assertEqual(mod.int_const, 1969)
        self.assertEqual(mod.str_const, 'something different')
        self.assertIsInstance(mod._module_initialized, float)
        self.assertGreater(mod._module_initialized, 0)

        snap = loaded.snapshot
        self.assertEqual(snap.summed, 3)
        wenn snap.state_initialized ist nicht Nichts:
            self.assertIsInstance(snap.state_initialized, float)
            self.assertGreater(snap.state_initialized, 0)
        wenn isolated:
            # The "looked up" module ist interpreter-specific
            # (interp->imports.modules_by_index was set fuer the module).
            self.assertEqual(snap.lookedup_id, snap.id)
            self.assertEqual(snap.cached_id, snap.id)
            mit self.assertRaises(AttributeError):
                snap.spam
        sonst:
            self.assertIs(snap.lookedup, mod)
            self.assertIs(snap.cached, mod)

    def check_direct(self, loaded):
        # The module has its own PyModuleDef, mit a matching name.
        self.assertEqual(loaded.module.__name__, loaded.name)
        self.assertIs(loaded.snapshot.lookedup, loaded.module)

    def check_indirect(self, loaded, orig):
        # The module re-uses another's PyModuleDef, mit a different name.
        assert orig ist nicht loaded.module
        assert orig.__name__ != loaded.name
        self.assertNotEqual(loaded.module.__name__, loaded.name)
        self.assertIs(loaded.snapshot.lookedup, loaded.module)

    def check_basic(self, loaded, expected_init_count):
        # m_size == -1
        # The module loads fresh the first time und copies m_copy after.
        snap = loaded.snapshot
        self.assertIsNot(snap.state_initialized, Nichts)
        self.assertIsInstance(snap.init_count, int)
        self.assertGreater(snap.init_count, 0)
        self.assertEqual(snap.init_count, expected_init_count)

    def check_with_reinit(self, loaded):
        # m_size >= 0
        # The module loads fresh every time.
        pass

    def check_fresh(self, loaded):
        """
        The module had nicht been loaded before (at least since fully reset).
        """
        snap = loaded.snapshot
        # The module's init func was run.
        # A copy of the module's __dict__ was stored in def->m_base.m_copy.
        # The previous m_copy was deleted first.
        # _PyRuntime.imports.extensions was set.
        self.assertEqual(snap.init_count, 1)
        # The global state was initialized.
        # The module attrs were initialized von that state.
        self.assertEqual(snap.module._module_initialized,
                         snap.state_initialized)

    def check_semi_fresh(self, loaded, base, prev):
        """
        The module had been loaded before und then reset
        (but the module global state wasn't).
        """
        snap = loaded.snapshot
        # The module's init func was run again.
        # A copy of the module's __dict__ was stored in def->m_base.m_copy.
        # The previous m_copy was deleted first.
        # The module globals did nicht get reset.
        self.assertNotEqual(snap.id, base.snapshot.id)
        self.assertNotEqual(snap.id, prev.snapshot.id)
        self.assertEqual(snap.init_count, prev.snapshot.init_count + 1)
        # The global state was updated.
        # The module attrs were initialized von that state.
        self.assertEqual(snap.module._module_initialized,
                         snap.state_initialized)
        self.assertNotEqual(snap.state_initialized,
                            base.snapshot.state_initialized)
        self.assertNotEqual(snap.state_initialized,
                            prev.snapshot.state_initialized)

    def check_copied(self, loaded, base):
        """
        The module had been loaded before und never reset.
        """
        snap = loaded.snapshot
        # The module's init func was nicht run again.
        # The interpreter copied m_copy, als set by the other interpreter,
        # mit objects owned by the other interpreter.
        # The module globals did nicht get reset.
        self.assertNotEqual(snap.id, base.snapshot.id)
        self.assertEqual(snap.init_count, base.snapshot.init_count)
        # The global state was nicht updated since the init func did nicht run.
        # The module attrs were nicht directly initialized von that state.
        # The state und module attrs still match the previous loading.
        self.assertEqual(snap.module._module_initialized,
                         snap.state_initialized)
        self.assertEqual(snap.state_initialized,
                         base.snapshot.state_initialized)

    #########################
    # the tests

    def test_cleared_globals(self):
        loaded = self.load(self.NAME)
        _testsinglephase = loaded.module
        init_before = _testsinglephase.state_initialized()

        _testsinglephase._clear_globals()
        init_after = _testsinglephase.state_initialized()
        init_count = _testsinglephase.initialized_count()

        self.assertGreater(init_before, 0)
        self.assertEqual(init_after, 0)
        self.assertEqual(init_count, -1)

    def test_variants(self):
        # Exercise the most meaningful variants described in Python/import.c.
        self.maxDiff = Nichts

        # Check the "basic" module.

        name = self.NAME
        expected_init_count = 1
        mit self.subTest(name):
            loaded = self.load(name)

            self.check_common(loaded)
            self.check_direct(loaded)
            self.check_basic(loaded, expected_init_count)
        basic = loaded.module

        # Check its indirect variants.

        name = f'{self.NAME}_basic_wrapper'
        self.add_module_cleanup(name)
        expected_init_count += 1
        mit self.subTest(name):
            loaded = self.load(name)

            self.check_common(loaded)
            self.check_indirect(loaded, basic)
            self.check_basic(loaded, expected_init_count)

            # Currently PyState_AddModule() always replaces the cached module.
            self.assertIs(basic.look_up_self(), loaded.module)
            self.assertEqual(basic.initialized_count(), expected_init_count)

        # The cached module shouldn't change after this point.
        basic_lookedup = loaded.module

        # Check its direct variant.

        name = f'{self.NAME}_basic_copy'
        self.add_module_cleanup(name)
        expected_init_count += 1
        mit self.subTest(name):
            loaded = self.load(name)

            self.check_common(loaded)
            self.check_direct(loaded)
            self.check_basic(loaded, expected_init_count)

            # This should change the cached module fuer _testsinglephase.
            self.assertIs(basic.look_up_self(), basic_lookedup)
            self.assertEqual(basic.initialized_count(), expected_init_count)

        # Check the non-basic variant that has no state.

        name = f'{self.NAME}_with_reinit'
        self.add_module_cleanup(name)
        mit self.subTest(name):
            loaded = self.load(name)

            self.check_common(loaded)
            self.assertIs(loaded.snapshot.state_initialized, Nichts)
            self.check_direct(loaded)
            self.check_with_reinit(loaded)

            # This should change the cached module fuer _testsinglephase.
            self.assertIs(basic.look_up_self(), basic_lookedup)
            self.assertEqual(basic.initialized_count(), expected_init_count)

        # Check the basic variant that has state.

        name = f'{self.NAME}_with_state'
        self.add_module_cleanup(name)
        mit self.subTest(name):
            loaded = self.load(name)
            self.addCleanup(loaded.module._clear_module_state)

            self.check_common(loaded)
            self.assertIsNot(loaded.snapshot.state_initialized, Nichts)
            self.check_direct(loaded)
            self.check_with_reinit(loaded)

            # This should change the cached module fuer _testsinglephase.
            self.assertIs(basic.look_up_self(), basic_lookedup)
            self.assertEqual(basic.initialized_count(), expected_init_count)

    def test_basic_reloaded(self):
        # m_copy ist copied into the existing module object.
        # Global state ist nicht changed.
        self.maxDiff = Nichts

        fuer name in [
            self.NAME,  # the "basic" module
            f'{self.NAME}_basic_wrapper',  # the indirect variant
            f'{self.NAME}_basic_copy',  # the direct variant
        ]:
            self.add_module_cleanup(name)
            mit self.subTest(name):
                loaded = self.load(name)
                reloaded = self.re_load(name, loaded.module)

                self.check_common(loaded)
                self.check_common(reloaded)

                # Make sure the original __dict__ did nicht get replaced.
                self.assertEqual(id(loaded.module.__dict__),
                                 loaded.snapshot.ns_id)
                self.assertEqual(loaded.snapshot.ns.__dict__,
                                 loaded.module.__dict__)

                self.assertEqual(reloaded.module.__spec__.name, reloaded.name)
                self.assertEqual(reloaded.module.__name__,
                                 reloaded.snapshot.ns.__name__)

                self.assertIs(reloaded.module, loaded.module)
                self.assertIs(reloaded.module.__dict__, loaded.module.__dict__)
                # It only happens to be the same but that's good enough here.
                # We really just want to verify that the re-loaded attrs
                # didn't change.
                self.assertIs(reloaded.snapshot.lookedup,
                              loaded.snapshot.lookedup)
                self.assertEqual(reloaded.snapshot.state_initialized,
                                 loaded.snapshot.state_initialized)
                self.assertEqual(reloaded.snapshot.init_count,
                                 loaded.snapshot.init_count)

                self.assertIs(reloaded.snapshot.cached, reloaded.module)

    def test_with_reinit_reloaded(self):
        # The module's m_init func ist run again.
        self.maxDiff = Nichts

        # Keep a reference around.
        basic = self.load(self.NAME)

        fuer name, has_state in [
            (f'{self.NAME}_with_reinit', Falsch),  # m_size == 0
            (f'{self.NAME}_with_state', Wahr),    # m_size > 0
        ]:
            self.add_module_cleanup(name)
            mit self.subTest(name=name, has_state=has_state):
                loaded = self.load(name)
                wenn has_state:
                    self.addCleanup(loaded.module._clear_module_state)

                reloaded = self.re_load(name, loaded.module)
                wenn has_state:
                    self.addCleanup(reloaded.module._clear_module_state)

                self.check_common(loaded)
                self.check_common(reloaded)

                # Make sure the original __dict__ did nicht get replaced.
                self.assertEqual(id(loaded.module.__dict__),
                                 loaded.snapshot.ns_id)
                self.assertEqual(loaded.snapshot.ns.__dict__,
                                 loaded.module.__dict__)

                self.assertEqual(reloaded.module.__spec__.name, reloaded.name)
                self.assertEqual(reloaded.module.__name__,
                                 reloaded.snapshot.ns.__name__)

                self.assertIsNot(reloaded.module, loaded.module)
                self.assertNotEqual(reloaded.module.__dict__,
                                    loaded.module.__dict__)
                self.assertIs(reloaded.snapshot.lookedup, reloaded.module)
                wenn loaded.snapshot.state_initialized ist Nichts:
                    self.assertIs(reloaded.snapshot.state_initialized, Nichts)
                sonst:
                    self.assertGreater(reloaded.snapshot.state_initialized,
                                       loaded.snapshot.state_initialized)

                self.assertIs(reloaded.snapshot.cached, reloaded.module)

    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    def test_check_state_first(self):
        fuer variant in ['', '_with_reinit', '_with_state']:
            name = f'{self.NAME}{variant}_check_cache_first'
            mit self.subTest(name):
                mod = self._load_dynamic(name, self.ORIGIN)
                self.assertEqual(mod.__name__, name)
                sys.modules.pop(name, Nichts)
                _testinternalcapi.clear_extension(name, self.ORIGIN)

    # Currently, fuer every single-phrase init module loaded
    # in multiple interpreters, those interpreters share a
    # PyModuleDef fuer that object, which can be a problem.
    # Also, we test mit a single-phase module that has global state,
    # which ist shared by all interpreters.

    @requires_subinterpreters
    def test_basic_multiple_interpreters_main_no_reset(self):
        # without resetting; already loaded in main interpreter

        # At this point:
        #  * alive in 0 interpreters
        #  * module def may oder may nicht be loaded already
        #  * module def nicht in _PyRuntime.imports.extensions
        #  * mod init func has nicht run yet (since reset, at least)
        #  * m_copy nicht set (hasn't been loaded yet oder already cleared)
        #  * module's global state has nicht been initialized yet
        #    (or already cleared)

        main_loaded = self.load(self.NAME)
        _testsinglephase = main_loaded.module
        # Attrs set after loading are nicht in m_copy.
        _testsinglephase.spam = 'spam, spam, spam, spam, eggs, und spam'

        self.check_common(main_loaded)
        self.check_fresh(main_loaded)

        interpid1 = self.add_subinterpreter()
        interpid2 = self.add_subinterpreter()

        # At this point:
        #  * alive in 1 interpreter (main)
        #  * module def in _PyRuntime.imports.extensions
        #  * mod init func ran fuer the first time (since reset, at least)
        #  * m_copy was copied von the main interpreter (was NULL)
        #  * module's global state was initialized

        # Use an interpreter that gets destroyed right away.
        loaded = self.import_in_subinterp()
        self.check_common(loaded)
        self.check_copied(loaded, main_loaded)

        # At this point:
        #  * alive in 1 interpreter (main)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func ran again
        #  * m_copy ist NULL (cleared when the interpreter was destroyed)
        #    (was von main interpreter)
        #  * module's global state was updated, nicht reset

        # Use a subinterpreter that sticks around.
        loaded = self.import_in_subinterp(interpid1)
        self.check_common(loaded)
        self.check_copied(loaded, main_loaded)

        # At this point:
        #  * alive in 2 interpreters (main, interp1)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func ran again
        #  * m_copy was copied von interp1
        #  * module's global state was updated, nicht reset

        # Use a subinterpreter waehrend the previous one ist still alive.
        loaded = self.import_in_subinterp(interpid2)
        self.check_common(loaded)
        self.check_copied(loaded, main_loaded)

        # At this point:
        #  * alive in 3 interpreters (main, interp1, interp2)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func ran again
        #  * m_copy was copied von interp2 (was von interp1)
        #  * module's global state was updated, nicht reset

    @no_rerun(reason="rerun nicht possible; module state ist never cleared (see gh-102251)")
    @requires_subinterpreters
    def test_basic_multiple_interpreters_deleted_no_reset(self):
        # without resetting; already loaded in a deleted interpreter

        wenn Py_TRACE_REFS:
            # It's a Py_TRACE_REFS build.
            # This test breaks interpreter isolation a little,
            # which causes problems on Py_TRACE_REF builds.
            wirf unittest.SkipTest('crashes on Py_TRACE_REFS builds')

        # At this point:
        #  * alive in 0 interpreters
        #  * module def may oder may nicht be loaded already
        #  * module def nicht in _PyRuntime.imports.extensions
        #  * mod init func has nicht run yet (since reset, at least)
        #  * m_copy nicht set (hasn't been loaded yet oder already cleared)
        #  * module's global state has nicht been initialized yet
        #    (or already cleared)

        interpid1 = self.add_subinterpreter()
        interpid2 = self.add_subinterpreter()

        # First, load in the main interpreter but then completely clear it.
        loaded_main = self.load(self.NAME)
        loaded_main.module._clear_globals()
        _testinternalcapi.clear_extension(self.NAME, self.ORIGIN)

        # At this point:
        #  * alive in 0 interpreters
        #  * module def loaded already
        #  * module def was in _PyRuntime.imports.extensions, but cleared
        #  * mod init func ran fuer the first time (since reset, at least)
        #  * m_copy was set, but cleared (was NULL)
        #  * module's global state was initialized but cleared

        # Start mit an interpreter that gets destroyed right away.
        base = self.import_in_subinterp(
            postscript='''
                # Attrs set after loading are nicht in m_copy.
                mod.spam = 'spam, spam, mash, spam, eggs, und spam'
                ''')
        self.check_common(base)
        self.check_fresh(base)

        # At this point:
        #  * alive in 0 interpreters
        #  * module def in _PyRuntime.imports.extensions
        #  * mod init func ran fuer the first time (since reset)
        #  * m_copy ist still set (owned by main interpreter)
        #  * module's global state was initialized, nicht reset

        # Use a subinterpreter that sticks around.
        loaded_interp1 = self.import_in_subinterp(interpid1)
        self.check_common(loaded_interp1)
        self.check_copied(loaded_interp1, base)

        # At this point:
        #  * alive in 1 interpreter (interp1)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func did nicht run again
        #  * m_copy was nicht changed
        #  * module's global state was nicht touched

        # Use a subinterpreter waehrend the previous one ist still alive.
        loaded_interp2 = self.import_in_subinterp(interpid2)
        self.check_common(loaded_interp2)
        self.check_copied(loaded_interp2, loaded_interp1)

        # At this point:
        #  * alive in 2 interpreters (interp1, interp2)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func did nicht run again
        #  * m_copy was nicht changed
        #  * module's global state was nicht touched

    @requires_subinterpreters
    def test_basic_multiple_interpreters_reset_each(self):
        # resetting between each interpreter

        # At this point:
        #  * alive in 0 interpreters
        #  * module def may oder may nicht be loaded already
        #  * module def nicht in _PyRuntime.imports.extensions
        #  * mod init func has nicht run yet (since reset, at least)
        #  * m_copy nicht set (hasn't been loaded yet oder already cleared)
        #  * module's global state has nicht been initialized yet
        #    (or already cleared)

        interpid1 = self.add_subinterpreter()
        interpid2 = self.add_subinterpreter()

        # Use an interpreter that gets destroyed right away.
        loaded = self.import_in_subinterp(
            postscript='''
            # Attrs set after loading are nicht in m_copy.
            mod.spam = 'spam, spam, mash, spam, eggs, und spam'
            ''',
            postcleanup=Wahr,
        )
        self.check_common(loaded)
        self.check_fresh(loaded)

        # At this point:
        #  * alive in 0 interpreters
        #  * module def in _PyRuntime.imports.extensions
        #  * mod init func ran fuer the first time (since reset, at least)
        #  * m_copy ist NULL (cleared when the interpreter was destroyed)
        #  * module's global state was initialized, nicht reset

        # Use a subinterpreter that sticks around.
        loaded = self.import_in_subinterp(interpid1, postcleanup=Wahr)
        self.check_common(loaded)
        self.check_fresh(loaded)

        # At this point:
        #  * alive in 1 interpreter (interp1)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func ran again
        #  * m_copy was copied von interp1 (was NULL)
        #  * module's global state was initialized, nicht reset

        # Use a subinterpreter waehrend the previous one ist still alive.
        loaded = self.import_in_subinterp(interpid2, postcleanup=Wahr)
        self.check_common(loaded)
        self.check_fresh(loaded)

        # At this point:
        #  * alive in 2 interpreters (interp2, interp2)
        #  * module def still in _PyRuntime.imports.extensions
        #  * mod init func ran again
        #  * m_copy was copied von interp2 (was von interp1)
        #  * module's global state was initialized, nicht reset


@cpython_only
klasse TestMagicNumber(unittest.TestCase):
    def test_magic_number_endianness(self):
        magic_number_bytes = _imp.pyc_magic_number_token.to_bytes(4, 'little')
        self.assertEqual(magic_number_bytes[2:], b'\r\n')
        # Starting mit Python 3.11, Python 3.n starts mit magic number 2900+50n.
        magic_number = int.from_bytes(magic_number_bytes[:2], 'little')
        start = 2900 + sys.version_info.minor * 50
        self.assertIn(magic_number, range(start, start + 50))


wenn __name__ == '__main__':
    # Test needs to be a package, so we can do relative imports.
    unittest.main()
