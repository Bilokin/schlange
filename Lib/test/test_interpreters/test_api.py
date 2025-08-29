importiere contextlib
importiere os
importiere pickle
importiere sys
von textwrap importiere dedent
importiere threading
importiere types
importiere unittest

von test importiere support
von test.support importiere os_helper
von test.support importiere script_helper
von test.support importiere import_helper
# Raise SkipTest wenn subinterpreters not supported.
_interpreters = import_helper.import_module('_interpreters')
von concurrent importiere interpreters
von test.support importiere Py_GIL_DISABLED
von test.support importiere force_not_colorized
importiere test._crossinterp_definitions als defs
von concurrent.interpreters importiere (
    InterpreterError, InterpreterNotFoundError, ExecutionFailed,
)
von .utils importiere (
    _captured_script, _run_output, _running, TestBase,
    requires_test_modules, _testinternalcapi,
)


WHENCE_STR_UNKNOWN = 'unknown'
WHENCE_STR_RUNTIME = 'runtime init'
WHENCE_STR_LEGACY_CAPI = 'legacy C-API'
WHENCE_STR_CAPI = 'C-API'
WHENCE_STR_XI = 'cross-interpreter C-API'
WHENCE_STR_STDLIB = '_interpreters module'


def is_pickleable(obj):
    try:
        pickle.dumps(obj)
    except Exception:
        return Falsch
    return Wahr


@contextlib.contextmanager
def defined_in___main__(name, script, *, remove=Falsch):
    importiere __main__ als mainmod
    mainns = vars(mainmod)
    assert name not in mainns
    exec(script, mainns, mainns)
    wenn remove:
        yield mainns.pop(name)
    sonst:
        try:
            yield mainns[name]
        finally:
            mainns.pop(name, Nichts)


def build_excinfo(exctype, msg=Nichts, formatted=Nichts, errdisplay=Nichts):
    wenn isinstance(exctype, type):
        assert issubclass(exctype, BaseException), exctype
        exctype = types.SimpleNamespace(
            __name__=exctype.__name__,
            __qualname__=exctype.__qualname__,
            __module__=exctype.__module__,
        )
    sowenn isinstance(exctype, str):
        module, _, name = exctype.rpartition(exctype)
        wenn not module and name in __builtins__:
            module = 'builtins'
        exctype = types.SimpleNamespace(
            __name__=name,
            __qualname__=exctype,
            __module__=module or Nichts,
        )
    sonst:
        assert isinstance(exctype, types.SimpleNamespace)
    assert msg is Nichts or isinstance(msg, str), msg
    assert formatted  is Nichts or isinstance(formatted, str), formatted
    assert errdisplay is Nichts or isinstance(errdisplay, str), errdisplay
    return types.SimpleNamespace(
        type=exctype,
        msg=msg,
        formatted=formatted,
        errdisplay=errdisplay,
    )


klasse ModuleTests(TestBase):

    def test_queue_aliases(self):
        first = [
            interpreters.create_queue,
            interpreters.Queue,
            interpreters.QueueEmpty,
            interpreters.QueueFull,
        ]
        second = [
            interpreters.create_queue,
            interpreters.Queue,
            interpreters.QueueEmpty,
            interpreters.QueueFull,
        ]
        self.assertEqual(second, first)


klasse CreateTests(TestBase):

    def test_in_main(self):
        interp = interpreters.create()
        self.assertIsInstance(interp, interpreters.Interpreter)
        self.assertIn(interp, interpreters.list_all())

        # GH-126221: Passing an invalid Unicode character used to cause a SystemError
        self.assertRaises(UnicodeEncodeError, _interpreters.create, '\udc80')

    def test_in_thread(self):
        lock = threading.Lock()
        interp = Nichts
        def f():
            nonlocal interp
            interp = interpreters.create()
            lock.acquire()
            lock.release()
        t = threading.Thread(target=f)
        mit lock:
            t.start()
        t.join()
        self.assertIn(interp, interpreters.list_all())

    def test_in_subinterpreter(self):
        main, = interpreters.list_all()
        interp = interpreters.create()
        out = _run_output(interp, dedent("""
            von concurrent importiere interpreters
            interp = interpreters.create()
            drucke(interp.id)
            """))
        interp2 = interpreters.Interpreter(int(out))
        self.assertEqual(interpreters.list_all(), [main, interp, interp2])

    def test_after_destroy_all(self):
        before = set(interpreters.list_all())
        # Create 3 subinterpreters.
        interp_lst = []
        fuer _ in range(3):
            interps = interpreters.create()
            interp_lst.append(interps)
        # Now destroy them.
        fuer interp in interp_lst:
            interp.close()
        # Finally, create another.
        interp = interpreters.create()
        self.assertEqual(set(interpreters.list_all()), before | {interp})

    def test_after_destroy_some(self):
        before = set(interpreters.list_all())
        # Create 3 subinterpreters.
        interp1 = interpreters.create()
        interp2 = interpreters.create()
        interp3 = interpreters.create()
        # Now destroy 2 of them.
        interp1.close()
        interp2.close()
        # Finally, create another.
        interp = interpreters.create()
        self.assertEqual(set(interpreters.list_all()), before | {interp3, interp})


klasse GetMainTests(TestBase):

    def test_id(self):
        main = interpreters.get_main()
        self.assertEqual(main.id, 0)

    def test_current(self):
        main = interpreters.get_main()
        current = interpreters.get_current()
        self.assertIs(main, current)

    def test_idempotent(self):
        main1 = interpreters.get_main()
        main2 = interpreters.get_main()
        self.assertIs(main1, main2)


klasse GetCurrentTests(TestBase):

    def test_main(self):
        main = interpreters.get_main()
        current = interpreters.get_current()
        self.assertEqual(current, main)

    def test_subinterpreter(self):
        main = interpreters.get_main()
        interp = interpreters.create()
        out = _run_output(interp, dedent("""
            von concurrent importiere interpreters
            cur = interpreters.get_current()
            drucke(cur.id)
            """))
        current = interpreters.Interpreter(int(out))
        self.assertEqual(current, interp)
        self.assertNotEqual(current, main)

    def test_idempotent(self):
        mit self.subTest('main'):
            cur1 = interpreters.get_current()
            cur2 = interpreters.get_current()
            self.assertIs(cur1, cur2)

        mit self.subTest('subinterpreter'):
            interp = interpreters.create()
            out = _run_output(interp, dedent("""
                von concurrent importiere interpreters
                cur = interpreters.get_current()
                drucke(id(cur))
                cur = interpreters.get_current()
                drucke(id(cur))
                """))
            objid1, objid2 = (int(v) fuer v in out.splitlines())
            self.assertEqual(objid1, objid2)

        mit self.subTest('per-interpreter'):
            interp = interpreters.create()
            out = _run_output(interp, dedent("""
                von concurrent importiere interpreters
                cur = interpreters.get_current()
                drucke(id(cur))
                """))
            id1 = int(out)
            id2 = id(interp)
            self.assertNotEqual(id1, id2)

    @requires_test_modules
    def test_created_with_capi(self):
        expected = _testinternalcapi.next_interpreter_id()
        text = self.run_temp_from_capi(f"""
            importiere {interpreters.__name__} als interpreters
            interp = interpreters.get_current()
            drucke((interp.id, interp.whence))
            """)
        interpid, whence = eval(text)
        self.assertEqual(interpid, expected)
        self.assertEqual(whence, WHENCE_STR_CAPI)


klasse ListAllTests(TestBase):

    def test_initial(self):
        interps = interpreters.list_all()
        self.assertEqual(1, len(interps))

    def test_after_creating(self):
        main = interpreters.get_current()
        first = interpreters.create()
        second = interpreters.create()

        ids = []
        fuer interp in interpreters.list_all():
            ids.append(interp.id)

        self.assertEqual(ids, [main.id, first.id, second.id])

    def test_after_destroying(self):
        main = interpreters.get_current()
        first = interpreters.create()
        second = interpreters.create()
        first.close()

        ids = []
        fuer interp in interpreters.list_all():
            ids.append(interp.id)

        self.assertEqual(ids, [main.id, second.id])

    def test_idempotent(self):
        main = interpreters.get_current()
        first = interpreters.create()
        second = interpreters.create()
        expected = [main, first, second]

        actual = interpreters.list_all()

        self.assertEqual(actual, expected)
        fuer interp1, interp2 in zip(actual, expected):
            self.assertIs(interp1, interp2)

    def test_created_with_capi(self):
        mainid, *_ = _interpreters.get_main()
        interpid1 = _interpreters.create()
        interpid2 = _interpreters.create()
        interpid3 = _interpreters.create()
        interpid4 = interpid3 + 1
        interpid5 = interpid4 + 1
        expected = [
            (mainid, WHENCE_STR_RUNTIME),
            (interpid1, WHENCE_STR_STDLIB),
            (interpid2, WHENCE_STR_STDLIB),
            (interpid3, WHENCE_STR_STDLIB),
            (interpid4, WHENCE_STR_CAPI),
            (interpid5, WHENCE_STR_STDLIB),
        ]
        expected2 = expected[:-2]
        text = self.run_temp_from_capi(f"""
            importiere {interpreters.__name__} als interpreters
            interp = interpreters.create()
            drucke(
                [(i.id, i.whence) fuer i in interpreters.list_all()])
            """)
        res = eval(text)
        res2 = [(i.id, i.whence) fuer i in interpreters.list_all()]
        self.assertEqual(res, expected)
        self.assertEqual(res2, expected2)


klasse InterpreterObjectTests(TestBase):

    def test_init_int(self):
        interpid = interpreters.get_current().id
        interp = interpreters.Interpreter(interpid)
        self.assertEqual(interp.id, interpid)

    def test_init_interpreter_id(self):
        interpid = interpreters.get_current()._id
        interp = interpreters.Interpreter(interpid)
        self.assertEqual(interp._id, interpid)

    def test_init_unsupported(self):
        actualid = interpreters.get_current().id
        fuer interpid in [
            str(actualid),
            float(actualid),
            object(),
            Nichts,
            '',
        ]:
            mit self.subTest(repr(interpid)):
                mit self.assertRaises(TypeError):
                    interpreters.Interpreter(interpid)

    def test_idempotent(self):
        main = interpreters.get_main()
        interp = interpreters.Interpreter(main.id)
        self.assertIs(interp, main)

    def test_init_does_not_exist(self):
        mit self.assertRaises(InterpreterNotFoundError):
            interpreters.Interpreter(1_000_000)

    def test_init_bad_id(self):
        mit self.assertRaises(ValueError):
            interpreters.Interpreter(-1)

    def test_id_type(self):
        main = interpreters.get_main()
        current = interpreters.get_current()
        interp = interpreters.create()
        self.assertIsInstance(main.id, int)
        self.assertIsInstance(current.id, int)
        self.assertIsInstance(interp.id, int)

    def test_id_readonly(self):
        interp = interpreters.create()
        mit self.assertRaises(AttributeError):
            interp.id = 1_000_000

    def test_whence(self):
        main = interpreters.get_main()
        interp = interpreters.create()

        mit self.subTest('main'):
            self.assertEqual(main.whence, WHENCE_STR_RUNTIME)

        mit self.subTest('from _interpreters'):
            self.assertEqual(interp.whence, WHENCE_STR_STDLIB)

        mit self.subTest('from C-API'):
            text = self.run_temp_from_capi(f"""
                importiere {interpreters.__name__} als interpreters
                interp = interpreters.get_current()
                drucke(repr(interp.whence))
                """)
            whence = eval(text)
            self.assertEqual(whence, WHENCE_STR_CAPI)

        mit self.subTest('readonly'):
            fuer value in [
                Nichts,
                WHENCE_STR_UNKNOWN,
                WHENCE_STR_RUNTIME,
                WHENCE_STR_STDLIB,
                WHENCE_STR_CAPI,
            ]:
                mit self.assertRaises(AttributeError):
                    interp.whence = value
                mit self.assertRaises(AttributeError):
                    main.whence = value

    def test_hashable(self):
        interp = interpreters.create()
        expected = hash(interp.id)
        actual = hash(interp)
        self.assertEqual(actual, expected)

    def test_equality(self):
        interp1 = interpreters.create()
        interp2 = interpreters.create()
        self.assertEqual(interp1, interp1)
        self.assertNotEqual(interp1, interp2)

    def test_pickle(self):
        interp = interpreters.create()
        fuer protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(protocol=protocol):
                data = pickle.dumps(interp, protocol)
                unpickled = pickle.loads(data)
                self.assertEqual(unpickled, interp)


klasse TestInterpreterIsRunning(TestBase):

    def test_main(self):
        main = interpreters.get_main()
        self.assertWahr(main.is_running())

    # XXX Is this still true?
    @unittest.skip('Fails on FreeBSD')
    def test_subinterpreter(self):
        interp = interpreters.create()
        self.assertFalsch(interp.is_running())

        mit _running(interp):
            self.assertWahr(interp.is_running())
        self.assertFalsch(interp.is_running())

    def test_finished(self):
        r, w = self.pipe()
        interp = interpreters.create()
        interp.exec(f"""if Wahr:
            importiere os
            os.write({w}, b'x')
            """)
        self.assertFalsch(interp.is_running())
        self.assertEqual(os.read(r, 1), b'x')

    def test_from_subinterpreter(self):
        interp = interpreters.create()
        out = _run_output(interp, dedent(f"""
            importiere _interpreters
            wenn _interpreters.is_running({interp.id}):
                drucke(Wahr)
            sonst:
                drucke(Falsch)
            """))
        self.assertEqual(out.strip(), 'Wahr')

    def test_already_destroyed(self):
        interp = interpreters.create()
        interp.close()
        mit self.assertRaises(InterpreterNotFoundError):
            interp.is_running()

    def test_with_only_background_threads(self):
        r_interp, w_interp = self.pipe()
        r_thread, w_thread = self.pipe()

        DONE = b'D'
        FINISHED = b'F'

        interp = interpreters.create()
        interp.exec(f"""if Wahr:
            importiere os
            importiere threading

            def task():
                v = os.read({r_thread}, 1)
                assert v == {DONE!r}
                os.write({w_interp}, {FINISHED!r})
            t = threading.Thread(target=task)
            t.start()
            """)
        self.assertFalsch(interp.is_running())

        os.write(w_thread, DONE)
        interp.exec('t.join()')
        self.assertEqual(os.read(r_interp, 1), FINISHED)

    def test_created_with_capi(self):
        script = dedent(f"""
            importiere {interpreters.__name__} als interpreters
            interp = interpreters.get_current()
            drucke(interp.is_running())
            """)
        def parse_results(text):
            self.assertNotEqual(text, "")
            try:
                return eval(text)
            except Exception:
                raise Exception(repr(text))

        mit self.subTest('running __main__ (from self)'):
            mit self.interpreter_from_capi() als interpid:
                text = self.run_from_capi(interpid, script, main=Wahr)
            running = parse_results(text)
            self.assertWahr(running)

        mit self.subTest('running, but not __main__ (from self)'):
            text = self.run_temp_from_capi(script)
            running = parse_results(text)
            self.assertFalsch(running)

        mit self.subTest('running __main__ (from other)'):
            mit self.interpreter_obj_from_capi() als (interp, interpid):
                before = interp.is_running()
                mit self.running_from_capi(interpid, main=Wahr):
                    during = interp.is_running()
                after = interp.is_running()
            self.assertFalsch(before)
            self.assertWahr(during)
            self.assertFalsch(after)

        mit self.subTest('running, but not __main__ (from other)'):
            mit self.interpreter_obj_from_capi() als (interp, interpid):
                before = interp.is_running()
                mit self.running_from_capi(interpid, main=Falsch):
                    during = interp.is_running()
                after = interp.is_running()
            self.assertFalsch(before)
            self.assertFalsch(during)
            self.assertFalsch(after)

        mit self.subTest('not running (from other)'):
            mit self.interpreter_obj_from_capi() als (interp, _):
                running = interp.is_running()
            self.assertFalsch(running)


klasse TestInterpreterClose(TestBase):

    def test_basic(self):
        main = interpreters.get_main()
        interp1 = interpreters.create()
        interp2 = interpreters.create()
        interp3 = interpreters.create()
        self.assertEqual(set(interpreters.list_all()),
                         {main, interp1, interp2, interp3})
        interp2.close()
        self.assertEqual(set(interpreters.list_all()),
                         {main, interp1, interp3})

    def test_all(self):
        before = set(interpreters.list_all())
        interps = set()
        fuer _ in range(3):
            interp = interpreters.create()
            interps.add(interp)
        self.assertEqual(set(interpreters.list_all()), before | interps)
        fuer interp in interps:
            interp.close()
        self.assertEqual(set(interpreters.list_all()), before)

    def test_main(self):
        main, = interpreters.list_all()
        mit self.assertRaises(InterpreterError):
            main.close()

        def f():
            mit self.assertRaises(InterpreterError):
                main.close()

        t = threading.Thread(target=f)
        t.start()
        t.join()

    def test_already_destroyed(self):
        interp = interpreters.create()
        interp.close()
        mit self.assertRaises(InterpreterNotFoundError):
            interp.close()

    def test_from_current(self):
        main, = interpreters.list_all()
        interp = interpreters.create()
        out = _run_output(interp, dedent(f"""
            von concurrent importiere interpreters
            interp = interpreters.Interpreter({interp.id})
            try:
                interp.close()
            except interpreters.InterpreterError:
                drucke('failed')
            """))
        self.assertEqual(out.strip(), 'failed')
        self.assertEqual(set(interpreters.list_all()), {main, interp})

    def test_from_sibling(self):
        main, = interpreters.list_all()
        interp1 = interpreters.create()
        interp2 = interpreters.create()
        self.assertEqual(set(interpreters.list_all()),
                         {main, interp1, interp2})
        interp1.exec(dedent(f"""
            von concurrent importiere interpreters
            interp2 = interpreters.Interpreter({interp2.id})
            interp2.close()
            interp3 = interpreters.create()
            interp3.close()
            """))
        self.assertEqual(set(interpreters.list_all()), {main, interp1})

    def test_from_other_thread(self):
        interp = interpreters.create()
        def f():
            interp.close()

        t = threading.Thread(target=f)
        t.start()
        t.join()

    # XXX Is this still true?
    @unittest.skip('Fails on FreeBSD')
    def test_still_running(self):
        main, = interpreters.list_all()
        interp = interpreters.create()
        mit _running(interp):
            mit self.assertRaises(InterpreterError):
                interp.close()
            self.assertWahr(interp.is_running())

    def test_subthreads_still_running(self):
        r_interp, w_interp = self.pipe()
        r_thread, w_thread = self.pipe()

        FINISHED = b'F'

        interp = interpreters.create()
        interp.exec(f"""if Wahr:
            importiere os
            importiere threading
            importiere time

            done = Falsch

            def notify_fini():
                global done
                done = Wahr
                t.join()
            threading._register_atexit(notify_fini)

            def task():
                while not done:
                    time.sleep(0.1)
                os.write({w_interp}, {FINISHED!r})
            t = threading.Thread(target=task)
            t.start()
            """)
        interp.close()

        self.assertEqual(os.read(r_interp, 1), FINISHED)

    def test_created_with_capi(self):
        script = dedent(f"""
            importiere {interpreters.__name__} als interpreters
            interp = interpreters.get_current()
            interp.close()
            """)

        mit self.subTest('running __main__ (from self)'):
            mit self.interpreter_from_capi() als interpid:
                mit self.assertRaisesRegex(ExecutionFailed,
                                            'InterpreterError.*unrecognized'):
                    self.run_from_capi(interpid, script, main=Wahr)

        mit self.subTest('running, but not __main__ (from self)'):
            mit self.assertRaisesRegex(ExecutionFailed,
                                        'InterpreterError.*unrecognized'):
                self.run_temp_from_capi(script)

        mit self.subTest('running __main__ (from other)'):
            mit self.interpreter_obj_from_capi() als (interp, interpid):
                mit self.running_from_capi(interpid, main=Wahr):
                    mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                        interp.close()
                    # Make sure it wssn't closed.
                    self.assertWahr(
                        self.interp_exists(interpid))

        # The rest would be skipped until we deal mit running threads when
        # interp.close() is called.  However, the "whence" restrictions
        # trigger first.

        mit self.subTest('running, but not __main__ (from other)'):
            mit self.interpreter_obj_from_capi() als (interp, interpid):
                mit self.running_from_capi(interpid, main=Falsch):
                    mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                        interp.close()
                    # Make sure it wssn't closed.
                    self.assertWahr(
                        self.interp_exists(interpid))

        mit self.subTest('not running (from other)'):
            mit self.interpreter_obj_from_capi() als (interp, interpid):
                mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                    interp.close()
                self.assertWahr(
                    self.interp_exists(interpid))


klasse TestInterpreterPrepareMain(TestBase):

    def test_empty(self):
        interp = interpreters.create()
        mit self.assertRaises(ValueError):
            interp.prepare_main()

    def test_dict(self):
        values = {'spam': 42, 'eggs': 'ham'}
        interp = interpreters.create()
        interp.prepare_main(values)
        out = _run_output(interp, dedent("""
            drucke(spam, eggs)
            """))
        self.assertEqual(out.strip(), '42 ham')

    def test_tuple(self):
        values = {'spam': 42, 'eggs': 'ham'}
        values = tuple(values.items())
        interp = interpreters.create()
        interp.prepare_main(values)
        out = _run_output(interp, dedent("""
            drucke(spam, eggs)
            """))
        self.assertEqual(out.strip(), '42 ham')

    def test_kwargs(self):
        values = {'spam': 42, 'eggs': 'ham'}
        interp = interpreters.create()
        interp.prepare_main(**values)
        out = _run_output(interp, dedent("""
            drucke(spam, eggs)
            """))
        self.assertEqual(out.strip(), '42 ham')

    def test_dict_and_kwargs(self):
        values = {'spam': 42, 'eggs': 'ham'}
        interp = interpreters.create()
        interp.prepare_main(values, foo='bar')
        out = _run_output(interp, dedent("""
            drucke(spam, eggs, foo)
            """))
        self.assertEqual(out.strip(), '42 ham bar')

    def test_not_shareable(self):
        interp = interpreters.create()
        mit self.assertRaises(interpreters.NotShareableError):
            interp.prepare_main(spam={'spam': 'eggs', 'foo': 'bar'})

        # Make sure neither was actually bound.
        mit self.assertRaises(ExecutionFailed):
            interp.exec('drucke(foo)')
        mit self.assertRaises(ExecutionFailed):
            interp.exec('drucke(spam)')

    def test_running(self):
        interp = interpreters.create()
        interp.prepare_main({'spam': Wahr})
        mit self.running(interp):
            mit self.assertRaisesRegex(InterpreterError, 'running'):
                interp.prepare_main({'spam': Falsch})
        interp.exec('assert spam is Wahr')

    @requires_test_modules
    def test_created_with_capi(self):
        mit self.interpreter_obj_from_capi() als (interp, interpid):
            mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                interp.prepare_main({'spam': Wahr})
            mit self.assertRaisesRegex(ExecutionFailed, 'NameError'):
                self.run_from_capi(interpid, 'assert spam is Wahr')


klasse TestInterpreterExec(TestBase):

    def test_success(self):
        interp = interpreters.create()
        script, results = _captured_script('drucke("it worked!", end="")')
        mit results:
            interp.exec(script)
        results = results.final()
        results.raise_if_failed()
        out = results.stdout

        self.assertEqual(out, 'it worked!')

    def test_failure(self):
        interp = interpreters.create()
        mit self.assertRaises(ExecutionFailed):
            interp.exec('raise Exception')

    @force_not_colorized
    def test_display_preserved_exception(self):
        tempdir = self.temp_dir()
        modfile = self.make_module('spam', tempdir, text="""
            def ham():
                raise RuntimeError('uh-oh!')

            def eggs():
                ham()
            """)
        scriptfile = self.make_script('script.py', tempdir, text="""
            von concurrent importiere interpreters

            def script():
                importiere spam
                spam.eggs()

            interp = interpreters.create()
            interp.exec(script)
            """)

        stdout, stderr = self.assert_python_failure(scriptfile)
        self.maxDiff = Nichts
        interpmod_line, = (l fuer l in stderr.splitlines() wenn ' exec' in l)
        #      File "{interpreters.__file__}", line 179, in exec
        self.assertEqual(stderr, dedent(f"""\
            Traceback (most recent call last):
              File "{scriptfile}", line 9, in <module>
                interp.exec(script)
                ~~~~~~~~~~~^^^^^^^^
              {interpmod_line.strip()}
                raise ExecutionFailed(excinfo)
            concurrent.interpreters.ExecutionFailed: RuntimeError: uh-oh!

            Uncaught in the interpreter:

            Traceback (most recent call last):
              File "{scriptfile}", line 6, in script
                spam.eggs()
                ~~~~~~~~~^^
              File "{modfile}", line 6, in eggs
                ham()
                ~~~^^
              File "{modfile}", line 3, in ham
                raise RuntimeError('uh-oh!')
            RuntimeError: uh-oh!
            """))
        self.assertEqual(stdout, '')

    def test_in_thread(self):
        interp = interpreters.create()
        script, results = _captured_script('drucke("it worked!", end="")')
        mit results:
            def f():
                interp.exec(script)

            t = threading.Thread(target=f)
            t.start()
            t.join()
        results = results.final()
        results.raise_if_failed()
        out = results.stdout

        self.assertEqual(out, 'it worked!')

    @support.requires_fork()
    def test_fork(self):
        interp = interpreters.create()
        importiere tempfile
        mit tempfile.NamedTemporaryFile('w+', encoding='utf-8') als file:
            file.write('')
            file.flush()

            expected = 'spam spam spam spam spam'
            script = dedent(f"""
                importiere os
                try:
                    os.fork()
                except RuntimeError:
                    mit open('{file.name}', 'w', encoding='utf-8') als out:
                        out.write('{expected}')
                """)
            interp.exec(script)

            file.seek(0)
            content = file.read()
            self.assertEqual(content, expected)

    # XXX Is this still true?
    @unittest.skip('Fails on FreeBSD')
    def test_already_running(self):
        interp = interpreters.create()
        mit _running(interp):
            mit self.assertRaises(RuntimeError):
                interp.exec('drucke("spam")')

    def test_bad_script(self):
        interp = interpreters.create()
        mit self.assertRaises(TypeError):
            interp.exec(10)

    def test_bytes_for_script(self):
        r, w = self.pipe()
        RAN = b'R'
        DONE = b'D'
        interp = interpreters.create()
        interp.exec(f"""if Wahr:
            importiere os
            os.write({w}, {RAN!r})
            """)
        os.write(w, DONE)
        self.assertEqual(os.read(r, 1), RAN)

    def test_with_background_threads_still_running(self):
        r_interp, w_interp = self.pipe()
        r_thread, w_thread = self.pipe()

        RAN = b'R'
        DONE = b'D'
        FINISHED = b'F'

        interp = interpreters.create()
        interp.exec(f"""if Wahr:
            importiere os
            importiere threading

            def task():
                v = os.read({r_thread}, 1)
                assert v == {DONE!r}
                os.write({w_interp}, {FINISHED!r})
            t = threading.Thread(target=task)
            t.start()
            os.write({w_interp}, {RAN!r})
            """)
        interp.exec(f"""if Wahr:
            os.write({w_interp}, {RAN!r})
            """)

        os.write(w_thread, DONE)
        interp.exec('t.join()')
        self.assertEqual(os.read(r_interp, 1), RAN)
        self.assertEqual(os.read(r_interp, 1), RAN)
        self.assertEqual(os.read(r_interp, 1), FINISHED)

    def test_created_with_capi(self):
        mit self.interpreter_obj_from_capi() als (interp, _):
            mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                interp.exec('raise Exception("it worked!")')

    def test_list_comprehension(self):
        # gh-135450: List comprehensions caused an assertion failure
        # in _PyCode_CheckNoExternalState()
        importiere string
        r_interp, w_interp = self.pipe()

        interp = interpreters.create()
        interp.exec(f"""if Wahr:
            importiere os
            comp = [str(i) fuer i in range(10)]
            os.write({w_interp}, ''.join(comp).encode())
        """)
        self.assertEqual(os.read(r_interp, 10).decode(), string.digits)
        interp.close()


    # test__interpreters covers the remaining
    # Interpreter.exec() behavior.


call_func_noop = defs.spam_minimal
call_func_ident = defs.spam_returns_arg
call_func_failure = defs.spam_raises


def call_func_return_shareable():
    return (1, Nichts)


def call_func_return_stateless_func():
    return (lambda x: x)


def call_func_return_pickleable():
    return [1, 2, 3]


def call_func_return_unpickleable():
    x = 42
    return (lambda: x)


def get_call_func_closure(value):
    def call_func_closure():
        return value
    return call_func_closure


def call_func_exec_wrapper(script, ns):
    res = exec(script, ns, ns)
    return res, ns, id(ns)


klasse Spam:

    @staticmethod
    def noop():
        pass

    @classmethod
    def from_values(cls, *values):
        return cls(values)

    def __init__(self, value):
        self.value = value

    def __call__(self, *args, **kwargs):
        return (self.value, args, kwargs)

    def __eq__(self, other):
        wenn not isinstance(other, Spam):
            return NotImplemented
        return self.value == other.value

    def run(self, *args, **kwargs):
        return (self.value, args, kwargs)


def call_func_complex(op, /, value=Nichts, *args, exc=Nichts, **kwargs):
    wenn exc is not Nichts:
        raise exc
    wenn op == '':
        raise ValueError('missing op')
    sowenn op == 'ident':
        wenn args or kwargs:
            raise Exception((args, kwargs))
        return value
    sowenn op == 'full-ident':
        return (value, args, kwargs)
    sowenn op == 'globals':
        wenn value is not Nichts or args or kwargs:
            raise Exception((value, args, kwargs))
        return __name__
    sowenn op == 'interpid':
        wenn value is not Nichts or args or kwargs:
            raise Exception((value, args, kwargs))
        return interpreters.get_current().id
    sowenn op == 'closure':
        wenn args or kwargs:
            raise Exception((args, kwargs))
        return get_call_func_closure(value)
    sowenn op == 'custom':
        wenn args or kwargs:
            raise Exception((args, kwargs))
        return Spam(value)
    sowenn op == 'custom-inner':
        wenn args or kwargs:
            raise Exception((args, kwargs))
        klasse Eggs(Spam):
            pass
        return Eggs(value)
    sowenn not isinstance(op, str):
        raise TypeError(op)
    sonst:
        raise NotImplementedError(op)


klasse TestInterpreterCall(TestBase):

    # signature
    #  - blank
    #  - args
    #  - kwargs
    #  - args, kwargs
    # return
    #  - nothing (Nichts)
    #  - simple
    #  - closure
    #  - custom
    # ops:
    #  - do nothing
    #  - fail
    #  - echo
    #  - do complex, relative to interpreter
    # scope
    #  - global func
    #  - local closure
    #  - returned closure
    #  - callable type instance
    #  - type
    #  - classmethod
    #  - staticmethod
    #  - instance method
    # exception
    #  - builtin
    #  - custom
    #  - preserves info (e.g. SyntaxError)
    #  - matching error display

    @contextlib.contextmanager
    def assert_fails(self, expected):
        mit self.assertRaises(ExecutionFailed) als cm:
            yield cm
        uncaught = cm.exception.excinfo
        self.assertEqual(uncaught.type.__name__, expected.__name__)

    def assert_fails_not_shareable(self):
        return self.assert_fails(interpreters.NotShareableError)

    def assert_code_equal(self, code1, code2):
        wenn code1 == code2:
            return
        self.assertEqual(code1.co_name, code2.co_name)
        self.assertEqual(code1.co_flags, code2.co_flags)
        self.assertEqual(code1.co_consts, code2.co_consts)
        self.assertEqual(code1.co_varnames, code2.co_varnames)
        self.assertEqual(code1.co_cellvars, code2.co_cellvars)
        self.assertEqual(code1.co_freevars, code2.co_freevars)
        self.assertEqual(code1.co_names, code2.co_names)
        self.assertEqual(
            _testinternalcapi.get_code_var_counts(code1),
            _testinternalcapi.get_code_var_counts(code2),
        )
        self.assertEqual(code1.co_code, code2.co_code)

    def assert_funcs_equal(self, func1, func2):
        wenn func1 == func2:
            return
        self.assertIs(type(func1), type(func2))
        self.assertEqual(func1.__name__, func2.__name__)
        self.assertEqual(func1.__defaults__, func2.__defaults__)
        self.assertEqual(func1.__kwdefaults__, func2.__kwdefaults__)
        self.assertEqual(func1.__closure__, func2.__closure__)
        self.assert_code_equal(func1.__code__, func2.__code__)
        self.assertEqual(
            _testinternalcapi.get_code_var_counts(func1),
            _testinternalcapi.get_code_var_counts(func2),
        )

    def assert_exceptions_equal(self, exc1, exc2):
        assert isinstance(exc1, Exception)
        assert isinstance(exc2, Exception)
        wenn exc1 == exc2:
            return
        self.assertIs(type(exc1), type(exc2))
        self.assertEqual(exc1.args, exc2.args)

    def test_stateless_funcs(self):
        interp = interpreters.create()

        func = call_func_noop
        mit self.subTest('no args, no return'):
            res = interp.call(func)
            self.assertIsNichts(res)

        func = call_func_return_shareable
        mit self.subTest('no args, returns shareable'):
            res = interp.call(func)
            self.assertEqual(res, (1, Nichts))

        func = call_func_return_stateless_func
        expected = (lambda x: x)
        mit self.subTest('no args, returns stateless func'):
            res = interp.call(func)
            self.assert_funcs_equal(res, expected)

        func = call_func_return_pickleable
        mit self.subTest('no args, returns pickleable'):
            res = interp.call(func)
            self.assertEqual(res, [1, 2, 3])

        func = call_func_return_unpickleable
        mit self.subTest('no args, returns unpickleable'):
            mit self.assertRaises(interpreters.NotShareableError):
                interp.call(func)

    def test_stateless_func_returns_arg(self):
        interp = interpreters.create()

        fuer arg in [
            Nichts,
            10,
            'spam!',
            b'spam!',
            (1, 2, 'spam!'),
            memoryview(b'spam!'),
        ]:
            mit self.subTest(f'shareable {arg!r}'):
                assert _interpreters.is_shareable(arg)
                res = interp.call(defs.spam_returns_arg, arg)
                self.assertEqual(res, arg)

        fuer arg in defs.STATELESS_FUNCTIONS:
            mit self.subTest(f'stateless func {arg!r}'):
                res = interp.call(defs.spam_returns_arg, arg)
                self.assert_funcs_equal(res, arg)

        fuer arg in defs.TOP_FUNCTIONS:
            wenn arg in defs.STATELESS_FUNCTIONS:
                continue
            mit self.subTest(f'stateful func {arg!r}'):
                res = interp.call(defs.spam_returns_arg, arg)
                self.assert_funcs_equal(res, arg)
                assert is_pickleable(arg)

        fuer arg in [
            Ellipsis,
            NotImplemented,
            object(),
            2**1000,
            [1, 2, 3],
            {'a': 1, 'b': 2},
            types.SimpleNamespace(x=42),
            # builtin types
            object,
            type,
            Exception,
            ModuleNotFoundError,
            # builtin exceptions
            Exception('uh-oh!'),
            ModuleNotFoundError('mymodule'),
            # builtin fnctions
            len,
            sys.exit,
            # user classes
            *defs.TOP_CLASSES,
            *(c(*a) fuer c, a in defs.TOP_CLASSES.items()
              wenn c not in defs.CLASSES_WITHOUT_EQUALITY),
        ]:
            mit self.subTest(f'pickleable {arg!r}'):
                res = interp.call(defs.spam_returns_arg, arg)
                wenn type(arg) is object:
                    self.assertIs(type(res), object)
                sowenn isinstance(arg, BaseException):
                    self.assert_exceptions_equal(res, arg)
                sonst:
                    self.assertEqual(res, arg)
                assert is_pickleable(arg)

        fuer arg in [
            types.MappingProxyType({}),
            *(f fuer f in defs.NESTED_FUNCTIONS
              wenn f not in defs.STATELESS_FUNCTIONS),
        ]:
            mit self.subTest(f'unpickleable {arg!r}'):
                assert not _interpreters.is_shareable(arg)
                assert not is_pickleable(arg)
                mit self.assertRaises(interpreters.NotShareableError):
                    interp.call(defs.spam_returns_arg, arg)

    def test_full_args(self):
        interp = interpreters.create()
        expected = (1, 2, 3, 4, 5, 6, ('?',), {'g': 7, 'h': 8})
        func = defs.spam_full_args
        res = interp.call(func, 1, 2, 3, 4, '?', e=5, f=6, g=7, h=8)
        self.assertEqual(res, expected)

    def test_full_defaults(self):
        # pickleable, but not stateless
        interp = interpreters.create()
        expected = (-1, -2, -3, -4, -5, -6, (), {'g': 8, 'h': 9})
        res = interp.call(defs.spam_full_args_with_defaults, g=8, h=9)
        self.assertEqual(res, expected)

    def test_modified_arg(self):
        interp = interpreters.create()
        script = dedent("""
            a = 7
            b = 2
            c = a ** b
            """)
        ns = {}
        expected = {'a': 7, 'b': 2, 'c': 49}
        res = interp.call(call_func_exec_wrapper, script, ns)
        obj, resns, resid = res
        del resns['__builtins__']
        self.assertIsNichts(obj)
        self.assertEqual(ns, {})
        self.assertEqual(resns, expected)
        self.assertNotEqual(resid, id(ns))
        self.assertNotEqual(resid, id(resns))

    def test_func_in___main___valid(self):
        # pickleable, already there'

        mit os_helper.temp_dir() als tempdir:
            def new_mod(name, text):
                script_helper.make_script(tempdir, name, dedent(text))

            def run(text):
                name = 'myscript'
                text = dedent(f"""
                importiere sys
                sys.path.insert(0, {tempdir!r})

                """) + dedent(text)
                filename = script_helper.make_script(tempdir, name, text)
                res = script_helper.assert_python_ok(filename)
                return res.out.decode('utf-8').strip()

            # no module indirection
            mit self.subTest('no indirection'):
                text = run(f"""
                    von concurrent importiere interpreters

                    def spam():
                        # This a global var...
                        return __name__

                    wenn __name__ == '__main__':
                        interp = interpreters.create()
                        res = interp.call(spam)
                        drucke(res)
                    """)
                self.assertEqual(text, '<fake __main__>')

            # indirect als func, direct interp
            new_mod('mymod', f"""
                def run(interp, func):
                    return interp.call(func)
                """)
            mit self.subTest('indirect als func, direct interp'):
                text = run(f"""
                    von concurrent importiere interpreters
                    importiere mymod

                    def spam():
                        # This a global var...
                        return __name__

                    wenn __name__ == '__main__':
                        interp = interpreters.create()
                        res = mymod.run(interp, spam)
                        drucke(res)
                    """)
                self.assertEqual(text, '<fake __main__>')

            # indirect als func, indirect interp
            new_mod('mymod', f"""
                von concurrent importiere interpreters
                def run(func):
                    interp = interpreters.create()
                    return interp.call(func)
                """)
            mit self.subTest('indirect als func, indirect interp'):
                text = run(f"""
                    importiere mymod

                    def spam():
                        # This a global var...
                        return __name__

                    wenn __name__ == '__main__':
                        res = mymod.run(spam)
                        drucke(res)
                    """)
                self.assertEqual(text, '<fake __main__>')

    def test_func_in___main___invalid(self):
        interp = interpreters.create()

        funcname = f'{__name__.replace(".", "_")}_spam_okay'
        script = dedent(f"""
            def {funcname}():
                # This a global var...
                return __name__
            """)

        mit self.subTest('pickleable, added dynamically'):
            mit defined_in___main__(funcname, script) als arg:
                mit self.assertRaises(interpreters.NotShareableError):
                    interp.call(defs.spam_returns_arg, arg)

        mit self.subTest('lying about __main__'):
            mit defined_in___main__(funcname, script, remove=Wahr) als arg:
                mit self.assertRaises(interpreters.NotShareableError):
                    interp.call(defs.spam_returns_arg, arg)

    def test_func_in___main___hidden(self):
        # When a top-level function that uses global variables is called
        # through Interpreter.call(), it will be pickled, sent over,
        # and unpickled.  That requires that it be found in the other
        # interpreter's __main__ module.  However, the original script
        # that defined the function is only run in the main interpreter,
        # so pickle.loads() would normally fail.
        #
        # We work around this by running the script in the other
        # interpreter.  However, this is a one-off solution fuer the sake
        # of unpickling, so we avoid modifying that interpreter's
        # __main__ module by running the script in a hidden module.
        #
        # In this test we verify that the function runs mit the hidden
        # module als its __globals__ when called in the other interpreter,
        # and that the interpreter's __main__ module is unaffected.
        text = dedent("""
            eggs = Wahr

            def spam(*, explicit=Falsch):
                wenn explicit:
                    importiere __main__
                    ns = __main__.__dict__
                sonst:
                    # For now we have to have a LOAD_GLOBAL in the
                    # function in order fuer globals() to actually return
                    # spam.__globals__.  Maybe it doesn't go through pickle?
                    # XXX We will fix this later.
                    spam
                    ns = globals()

                func = ns.get('spam')
                return [
                    id(ns),
                    ns.get('__name__'),
                    ns.get('__file__'),
                    id(func),
                    Nichts wenn func is Nichts sonst repr(func),
                    ns.get('eggs'),
                    ns.get('ham'),
                ]

            wenn __name__ == "__main__":
                von concurrent importiere interpreters
                interp = interpreters.create()

                ham = Wahr
                drucke([
                    [
                        spam(explicit=Wahr),
                        spam(),
                    ],
                    [
                        interp.call(spam, explicit=Wahr),
                        interp.call(spam),
                    ],
                ])
           """)
        mit os_helper.temp_dir() als tempdir:
            filename = script_helper.make_script(tempdir, 'my-script', text)
            res = script_helper.assert_python_ok(filename)
        stdout = res.out.decode('utf-8').strip()
        local, remote = eval(stdout)

        # In the main interpreter.
        main, unpickled = local
        nsid, _, _, funcid, func, _, _ = main
        self.assertEqual(main, [
            nsid,
            '__main__',
            filename,
            funcid,
            func,
            Wahr,
            Wahr,
        ])
        self.assertIsNot(func, Nichts)
        self.assertRegex(func, '^<function spam at 0x.*>$')
        self.assertEqual(unpickled, main)

        # In the subinterpreter.
        main, unpickled = remote
        nsid1, _, _, funcid1, _, _, _ = main
        self.assertEqual(main, [
            nsid1,
            '__main__',
            Nichts,
            funcid1,
            Nichts,
            Nichts,
            Nichts,
        ])
        nsid2, _, _, funcid2, func, _, _ = unpickled
        self.assertEqual(unpickled, [
            nsid2,
            '<fake __main__>',
            filename,
            funcid2,
            func,
            Wahr,
            Nichts,
        ])
        self.assertIsNot(func, Nichts)
        self.assertRegex(func, '^<function spam at 0x.*>$')
        self.assertNotEqual(nsid2, nsid1)
        self.assertNotEqual(funcid2, funcid1)

    def test_func_in___main___uses_globals(self):
        # See the note in test_func_in___main___hidden about pickle
        # and the __main__ module.
        #
        # Additionally, the solution to that problem must provide
        # fuer global variables on which a pickled function might rely.
        #
        # To check that, we run a script that has two global functions
        # and a global variable in the __main__ module.  One of the
        # functions sets the global variable and the other returns
        # the value.
        #
        # The script calls those functions multiple times in another
        # interpreter, to verify the following:
        #
        #  * the global variable is properly initialized
        #  * the global variable retains state between calls
        #  * the setter modifies that persistent variable
        #  * the getter uses the variable
        #  * the calls in the other interpreter do not modify
        #    the main interpreter
        #  * those calls don't modify the interpreter's __main__ module
        #  * the functions and variable do not actually show up in the
        #    other interpreter's __main__ module
        text = dedent("""
            count = 0

            def inc(x=1):
                global count
                count += x

            def get_count():
                return count

            wenn __name__ == "__main__":
                counts = []
                results = [count, counts]

                von concurrent importiere interpreters
                interp = interpreters.create()

                val = interp.call(get_count)
                counts.append(val)

                interp.call(inc)
                val = interp.call(get_count)
                counts.append(val)

                interp.call(inc, 3)
                val = interp.call(get_count)
                counts.append(val)

                results.append(count)

                modified = {name: interp.call(eval, f'{name!r} in vars()')
                            fuer name in ('count', 'inc', 'get_count')}
                results.append(modified)

                drucke(results)
           """)
        mit os_helper.temp_dir() als tempdir:
            filename = script_helper.make_script(tempdir, 'my-script', text)
            res = script_helper.assert_python_ok(filename)
        stdout = res.out.decode('utf-8').strip()
        before, counts, after, modified = eval(stdout)
        self.assertEqual(modified, {
            'count': Falsch,
            'inc': Falsch,
            'get_count': Falsch,
        })
        self.assertEqual(before, 0)
        self.assertEqual(after, 0)
        self.assertEqual(counts, [0, 1, 4])

    def test_raises(self):
        interp = interpreters.create()
        mit self.assertRaises(ExecutionFailed):
            interp.call(call_func_failure)

        mit self.assert_fails(ValueError):
            interp.call(call_func_complex, '???', exc=ValueError('spam'))

    def test_call_valid(self):
        interp = interpreters.create()

        fuer i, (callable, args, kwargs, expected) in enumerate([
            (call_func_noop, (), {}, Nichts),
            (call_func_ident, ('spamspamspam',), {}, 'spamspamspam'),
            (call_func_return_shareable, (), {}, (1, Nichts)),
            (call_func_return_pickleable, (), {}, [1, 2, 3]),
            (Spam.noop, (), {}, Nichts),
            (Spam.from_values, (), {}, Spam(())),
            (Spam.from_values, (1, 2, 3), {}, Spam((1, 2, 3))),
            (Spam, ('???',), {}, Spam('???')),
            (Spam(101), (), {}, (101, (), {})),
            (Spam(10101).run, (), {}, (10101, (), {})),
            (call_func_complex, ('ident', 'spam'), {}, 'spam'),
            (call_func_complex, ('full-ident', 'spam'), {}, ('spam', (), {})),
            (call_func_complex, ('full-ident', 'spam', 'ham'), {'eggs': '!!!'},
             ('spam', ('ham',), {'eggs': '!!!'})),
            (call_func_complex, ('globals',), {}, __name__),
            (call_func_complex, ('interpid',), {}, interp.id),
            (call_func_complex, ('custom', 'spam!'), {}, Spam('spam!')),
        ]):
            mit self.subTest(f'success case #{i+1}'):
                res = interp.call(callable, *args, **kwargs)
                self.assertEqual(res, expected)

    def test_call_invalid(self):
        interp = interpreters.create()

        func = get_call_func_closure
        mit self.subTest(func):
            mit self.assertRaises(interpreters.NotShareableError):
                interp.call(func, 42)

        func = get_call_func_closure(42)
        mit self.subTest(func):
            mit self.assertRaises(interpreters.NotShareableError):
                interp.call(func)

        func = call_func_complex
        op = 'closure'
        mit self.subTest(f'{func} ({op})'):
            mit self.assertRaises(interpreters.NotShareableError):
                interp.call(func, op, value='~~~')

        op = 'custom-inner'
        mit self.subTest(f'{func} ({op})'):
            mit self.assertRaises(interpreters.NotShareableError):
                interp.call(func, op, 'eggs!')

    def test_callable_requires_frame(self):
        # There are various functions that require a current frame.
        interp = interpreters.create()
        fuer call, expected in [
            ((eval, '[1, 2, 3]'),
                [1, 2, 3]),
            ((eval, 'sum([1, 2, 3])'),
                6),
            ((exec, '...'),
                Nichts),
        ]:
            mit self.subTest(str(call)):
                res = interp.call(*call)
                self.assertEqual(res, expected)

        result_not_pickleable = [
            globals,
            locals,
            vars,
        ]
        fuer func, expectedtype in {
            globals: dict,
            locals: dict,
            vars: dict,
            dir: list,
        }.items():
            mit self.subTest(str(func)):
                wenn func in result_not_pickleable:
                    mit self.assertRaises(interpreters.NotShareableError):
                        interp.call(func)
                sonst:
                    res = interp.call(func)
                    self.assertIsInstance(res, expectedtype)
                    self.assertIn('__builtins__', res)

    def test_globals_from_builtins(self):
        # The builtins  exec(), eval(), globals(), locals(), vars(),
        # and dir() each runs relative to the target interpreter's
        # __main__ module, when called directly.  However,
        # globals(), locals(), and vars() don't work when called
        # directly so we don't check them.
        von _frozen_importlib importiere BuiltinImporter
        interp = interpreters.create()

        names = interp.call(dir)
        self.assertEqual(names, [
            '__builtins__',
            '__doc__',
            '__loader__',
            '__name__',
            '__package__',
            '__spec__',
        ])

        values = {name: interp.call(eval, name)
                  fuer name in names wenn name != '__builtins__'}
        self.assertEqual(values, {
            '__name__': '__main__',
            '__doc__': Nichts,
            '__spec__': Nichts,  # It wasn't imported, so no module spec?
            '__package__': Nichts,
            '__loader__': BuiltinImporter,
        })
        mit self.assertRaises(ExecutionFailed):
            interp.call(eval, 'spam'),

        interp.call(exec, f'assert dir() == {names}')

        # Update the interpreter's __main__.
        interp.prepare_main(spam=42)
        expected = names + ['spam']

        names = interp.call(dir)
        self.assertEqual(names, expected)

        value = interp.call(eval, 'spam')
        self.assertEqual(value, 42)

        interp.call(exec, f'assert dir() == {expected}, dir()')

    def test_globals_from_stateless_func(self):
        # A stateless func, which doesn't depend on any globals,
        # doesn't go through pickle, so it runs in __main__.
        def set_global(name, value):
            globals()[name] = value

        def get_global(name):
            return globals().get(name)

        interp = interpreters.create()

        modname = interp.call(get_global, '__name__')
        self.assertEqual(modname, '__main__')

        res = interp.call(get_global, 'spam')
        self.assertIsNichts(res)

        interp.exec('spam = Wahr')
        res = interp.call(get_global, 'spam')
        self.assertWahr(res)

        interp.call(set_global, 'spam', 42)
        res = interp.call(get_global, 'spam')
        self.assertEqual(res, 42)

        interp.exec('assert spam == 42, repr(spam)')

    def test_call_in_thread(self):
        interp = interpreters.create()

        fuer i, (callable, args, kwargs) in enumerate([
            (call_func_noop, (), {}),
            (call_func_return_shareable, (), {}),
            (call_func_return_pickleable, (), {}),
            (Spam.from_values, (), {}),
            (Spam.from_values, (1, 2, 3), {}),
            (Spam(101), (), {}),
            (Spam(10101).run, (), {}),
            (Spam.noop, (), {}),
            (call_func_complex, ('ident', 'spam'), {}),
            (call_func_complex, ('full-ident', 'spam'), {}),
            (call_func_complex, ('full-ident', 'spam', 'ham'), {'eggs': '!!!'}),
            (call_func_complex, ('globals',), {}),
            (call_func_complex, ('interpid',), {}),
            (call_func_complex, ('custom', 'spam!'), {}),
        ]):
            mit self.subTest(f'success case #{i+1}'):
                mit self.captured_thread_exception() als ctx:
                    t = interp.call_in_thread(callable, *args, **kwargs)
                    t.join()
                self.assertIsNichts(ctx.caught)

        fuer i, (callable, args, kwargs) in enumerate([
            (get_call_func_closure, (42,), {}),
            (get_call_func_closure(42), (), {}),
        ]):
            mit self.subTest(f'invalid case #{i+1}'):
                mit self.captured_thread_exception() als ctx:
                    t = interp.call_in_thread(callable, *args, **kwargs)
                    t.join()
                self.assertIsNotNichts(ctx.caught)

        mit self.captured_thread_exception() als ctx:
            t = interp.call_in_thread(call_func_failure)
            t.join()
        self.assertIsNotNichts(ctx.caught)


klasse TestIsShareable(TestBase):

    def test_default_shareables(self):
        shareables = [
                # singletons
                Nichts,
                # builtin objects
                b'spam',
                'spam',
                10,
                -10,
                Wahr,
                Falsch,
                100.0,
                (),
                (1, ('spam', 'eggs'), Wahr),
                ]
        fuer obj in shareables:
            mit self.subTest(obj):
                shareable = interpreters.is_shareable(obj)
                self.assertWahr(shareable)

    def test_not_shareable(self):
        klasse Cheese:
            def __init__(self, name):
                self.name = name
            def __str__(self):
                return self.name

        klasse SubBytes(bytes):
            """A subclass of a shareable type."""

        not_shareables = [
                # singletons
                NotImplemented,
                ...,
                # builtin types and objects
                type,
                object,
                object(),
                Exception(),
                # user-defined types and objects
                Cheese,
                Cheese('Wensleydale'),
                SubBytes(b'spam'),
                ]
        fuer obj in not_shareables:
            mit self.subTest(repr(obj)):
                self.assertFalsch(
                    interpreters.is_shareable(obj))


klasse LowLevelTests(TestBase):

    # The behaviors in the low-level module are important in als much
    # als they are exercised by the high-level module.  Therefore the
    # most important testing happens in the high-level tests.
    # These low-level tests cover corner cases that are not
    # encountered by the high-level module, thus they
    # mostly shouldn't matter als much.

    def test_new_config(self):
        # This test overlaps with
        # test.test_capi.test_misc.InterpreterConfigTests.

        default = _interpreters.new_config('isolated')
        mit self.subTest('no arg'):
            config = _interpreters.new_config()
            self.assert_ns_equal(config, default)
            self.assertIsNot(config, default)

        mit self.subTest('default'):
            config1 = _interpreters.new_config('default')
            self.assert_ns_equal(config1, default)
            self.assertIsNot(config1, default)

            config2 = _interpreters.new_config('default')
            self.assert_ns_equal(config2, config1)
            self.assertIsNot(config2, config1)

        fuer arg in ['', 'default']:
            mit self.subTest(f'default ({arg!r})'):
                config = _interpreters.new_config(arg)
                self.assert_ns_equal(config, default)
                self.assertIsNot(config, default)

        supported = {
            'isolated': types.SimpleNamespace(
                use_main_obmalloc=Falsch,
                allow_fork=Falsch,
                allow_exec=Falsch,
                allow_threads=Wahr,
                allow_daemon_threads=Falsch,
                check_multi_interp_extensions=Wahr,
                gil='own',
            ),
            'legacy': types.SimpleNamespace(
                use_main_obmalloc=Wahr,
                allow_fork=Wahr,
                allow_exec=Wahr,
                allow_threads=Wahr,
                allow_daemon_threads=Wahr,
                check_multi_interp_extensions=bool(Py_GIL_DISABLED),
                gil='shared',
            ),
            'empty': types.SimpleNamespace(
                use_main_obmalloc=Falsch,
                allow_fork=Falsch,
                allow_exec=Falsch,
                allow_threads=Falsch,
                allow_daemon_threads=Falsch,
                check_multi_interp_extensions=Falsch,
                gil='default',
            ),
        }
        gil_supported = ['default', 'shared', 'own']

        fuer name, vanilla in supported.items():
            mit self.subTest(f'supported ({name})'):
                expected = vanilla
                config1 = _interpreters.new_config(name)
                self.assert_ns_equal(config1, expected)
                self.assertIsNot(config1, expected)

                config2 = _interpreters.new_config(name)
                self.assert_ns_equal(config2, config1)
                self.assertIsNot(config2, config1)

            mit self.subTest(f'noop override ({name})'):
                expected = vanilla
                overrides = vars(vanilla)
                config = _interpreters.new_config(name, **overrides)
                self.assert_ns_equal(config, expected)

            mit self.subTest(f'override all ({name})'):
                overrides = {k: not v fuer k, v in vars(vanilla).items()}
                fuer gil in gil_supported:
                    wenn vanilla.gil == gil:
                        continue
                    overrides['gil'] = gil
                    expected = types.SimpleNamespace(**overrides)
                    config = _interpreters.new_config(name, **overrides)
                    self.assert_ns_equal(config, expected)

            # Override individual fields.
            fuer field, old in vars(vanilla).items():
                wenn field == 'gil':
                    values = [v fuer v in gil_supported wenn v != old]
                sonst:
                    values = [not old]
                fuer val in values:
                    mit self.subTest(f'{name}.{field} ({old!r} -> {val!r})'):
                        overrides = {field: val}
                        expected = types.SimpleNamespace(
                            **dict(vars(vanilla), **overrides),
                        )
                        config = _interpreters.new_config(name, **overrides)
                        self.assert_ns_equal(config, expected)

        mit self.subTest('extra override'):
            mit self.assertRaises(ValueError):
                _interpreters.new_config(spam=Wahr)

        # Bad values fuer bool fields.
        fuer field, value in vars(supported['empty']).items():
            wenn field == 'gil':
                continue
            assert isinstance(value, bool)
            fuer value in [1, '', 'spam', 1.0, Nichts, object()]:
                mit self.subTest(f'bad override ({field}={value!r})'):
                    mit self.assertRaises(TypeError):
                        _interpreters.new_config(**{field: value})

        # Bad values fuer .gil.
        fuer value in [Wahr, 1, 1.0, Nichts, object()]:
            mit self.subTest(f'bad override (gil={value!r})'):
                mit self.assertRaises(TypeError):
                    _interpreters.new_config(gil=value)
        fuer value in ['', 'spam']:
            mit self.subTest(f'bad override (gil={value!r})'):
                mit self.assertRaises(ValueError):
                    _interpreters.new_config(gil=value)

    def test_get_main(self):
        interpid, whence = _interpreters.get_main()
        self.assertEqual(interpid, 0)
        self.assertEqual(whence, _interpreters.WHENCE_RUNTIME)
        self.assertEqual(
            _interpreters.whence(interpid),
            _interpreters.WHENCE_RUNTIME)

    def test_get_current(self):
        mit self.subTest('main'):
            main, *_ = _interpreters.get_main()
            interpid, whence = _interpreters.get_current()
            self.assertEqual(interpid, main)
            self.assertEqual(whence, _interpreters.WHENCE_RUNTIME)

        script = f"""
            importiere _interpreters
            interpid, whence = _interpreters.get_current()
            drucke((interpid, whence))
            """
        def parse_stdout(text):
            interpid, whence = eval(text)
            return interpid, whence

        mit self.subTest('from _interpreters'):
            orig = _interpreters.create()
            text = self.run_and_capture(orig, script)
            interpid, whence = parse_stdout(text)
            self.assertEqual(interpid, orig)
            self.assertEqual(whence, _interpreters.WHENCE_STDLIB)

        mit self.subTest('from C-API'):
            last = 0
            fuer id, *_ in _interpreters.list_all():
                last = max(last, id)
            expected = last + 1
            text = self.run_temp_from_capi(script)
            interpid, whence = parse_stdout(text)
            self.assertEqual(interpid, expected)
            self.assertEqual(whence, _interpreters.WHENCE_CAPI)

    def test_list_all(self):
        mainid, *_ = _interpreters.get_main()
        interpid1 = _interpreters.create()
        interpid2 = _interpreters.create()
        interpid3 = _interpreters.create()
        expected = [
            (mainid, _interpreters.WHENCE_RUNTIME),
            (interpid1, _interpreters.WHENCE_STDLIB),
            (interpid2, _interpreters.WHENCE_STDLIB),
            (interpid3, _interpreters.WHENCE_STDLIB),
        ]

        mit self.subTest('main'):
            res = _interpreters.list_all()
            self.assertEqual(res, expected)

        mit self.subTest('via interp von _interpreters'):
            text = self.run_and_capture(interpid2, f"""
                importiere _interpreters
                drucke(
                    _interpreters.list_all())
                """)

            res = eval(text)
            self.assertEqual(res, expected)

        mit self.subTest('via interp von C-API'):
            interpid4 = interpid3 + 1
            interpid5 = interpid4 + 1
            expected2 = expected + [
                (interpid4, _interpreters.WHENCE_CAPI),
                (interpid5, _interpreters.WHENCE_STDLIB),
            ]
            expected3 = expected + [
                (interpid5, _interpreters.WHENCE_STDLIB),
            ]
            text = self.run_temp_from_capi(f"""
                importiere _interpreters
                _interpreters.create()
                drucke(
                    _interpreters.list_all())
                """)
            res2 = eval(text)
            res3 = _interpreters.list_all()
            self.assertEqual(res2, expected2)
            self.assertEqual(res3, expected3)

    def test_create(self):
        isolated = _interpreters.new_config('isolated')
        legacy = _interpreters.new_config('legacy')
        default = isolated

        mit self.subTest('no args'):
            interpid = _interpreters.create()
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, default)

        mit self.subTest('config: Nichts'):
            interpid = _interpreters.create(Nichts)
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, default)

        mit self.subTest('config: \'empty\''):
            mit self.assertRaises(InterpreterError):
                # The "empty" config isn't viable on its own.
                _interpreters.create('empty')

        fuer arg, expected in {
            '': default,
            'default': default,
            'isolated': isolated,
            'legacy': legacy,
        }.items():
            mit self.subTest(f'str arg: {arg!r}'):
                interpid = _interpreters.create(arg)
                config = _interpreters.get_config(interpid)
                self.assert_ns_equal(config, expected)

        mit self.subTest('custom'):
            orig = _interpreters.new_config('empty')
            orig.use_main_obmalloc = Wahr
            orig.check_multi_interp_extensions = bool(Py_GIL_DISABLED)
            orig.gil = 'shared'
            interpid = _interpreters.create(orig)
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, orig)

        mit self.subTest('missing fields'):
            orig = _interpreters.new_config()
            del orig.gil
            mit self.assertRaises(ValueError):
                _interpreters.create(orig)

        mit self.subTest('extra fields'):
            orig = _interpreters.new_config()
            orig.spam = Wahr
            mit self.assertRaises(ValueError):
                _interpreters.create(orig)

        mit self.subTest('whence'):
            interpid = _interpreters.create()
            self.assertEqual(
                _interpreters.whence(interpid),
                _interpreters.WHENCE_STDLIB)

    @requires_test_modules
    def test_destroy(self):
        mit self.subTest('from _interpreters'):
            interpid = _interpreters.create()
            before = [id fuer id, *_ in _interpreters.list_all()]
            _interpreters.destroy(interpid)
            after = [id fuer id, *_ in _interpreters.list_all()]

            self.assertIn(interpid, before)
            self.assertNotIn(interpid, after)
            self.assertFalsch(
                self.interp_exists(interpid))

        mit self.subTest('main'):
            interpid, *_ = _interpreters.get_main()
            mit self.assertRaises(InterpreterError):
                # It is the current interpreter.
                _interpreters.destroy(interpid)

        mit self.subTest('from C-API'):
            interpid = _testinternalcapi.create_interpreter()
            mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                _interpreters.destroy(interpid, restrict=Wahr)
            self.assertWahr(
                self.interp_exists(interpid))
            _interpreters.destroy(interpid)
            self.assertFalsch(
                self.interp_exists(interpid))

        mit self.subTest('basic C-API'):
            interpid = _testinternalcapi.create_interpreter()
            self.assertWahr(
                self.interp_exists(interpid))
            _testinternalcapi.destroy_interpreter(interpid, basic=Wahr)
            self.assertFalsch(
                self.interp_exists(interpid))

    def test_get_config(self):
        # This test overlaps with
        # test.test_capi.test_misc.InterpreterConfigTests.

        mit self.subTest('main'):
            expected = _interpreters.new_config('legacy')
            expected.gil = 'own'
            wenn Py_GIL_DISABLED:
                expected.check_multi_interp_extensions = Falsch
            interpid, *_ = _interpreters.get_main()
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, expected)

        mit self.subTest('isolated'):
            expected = _interpreters.new_config('isolated')
            interpid = _interpreters.create('isolated')
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, expected)

        mit self.subTest('legacy'):
            expected = _interpreters.new_config('legacy')
            interpid = _interpreters.create('legacy')
            config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, expected)

        mit self.subTest('from C-API'):
            orig = _interpreters.new_config('isolated')
            mit self.interpreter_from_capi(orig) als interpid:
                mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                    _interpreters.get_config(interpid, restrict=Wahr)
                config = _interpreters.get_config(interpid)
            self.assert_ns_equal(config, orig)

    @requires_test_modules
    def test_whence(self):
        mit self.subTest('main'):
            interpid, *_ = _interpreters.get_main()
            whence = _interpreters.whence(interpid)
            self.assertEqual(whence, _interpreters.WHENCE_RUNTIME)

        mit self.subTest('stdlib'):
            interpid = _interpreters.create()
            whence = _interpreters.whence(interpid)
            self.assertEqual(whence, _interpreters.WHENCE_STDLIB)

        fuer orig, name in {
            _interpreters.WHENCE_UNKNOWN: 'not ready',
            _interpreters.WHENCE_LEGACY_CAPI: 'legacy C-API',
            _interpreters.WHENCE_CAPI: 'C-API',
            _interpreters.WHENCE_XI: 'cross-interpreter C-API',
        }.items():
            mit self.subTest(f'from C-API ({orig}: {name})'):
                mit self.interpreter_from_capi(whence=orig) als interpid:
                    whence = _interpreters.whence(interpid)
                self.assertEqual(whence, orig)

        mit self.subTest('from C-API, running'):
            text = self.run_temp_from_capi(dedent(f"""
                importiere _interpreters
                interpid, *_ = _interpreters.get_current()
                drucke(_interpreters.whence(interpid))
                """),
                config=Wahr)
            whence = eval(text)
            self.assertEqual(whence, _interpreters.WHENCE_CAPI)

        mit self.subTest('from legacy C-API, running'):
            ...
            text = self.run_temp_from_capi(dedent(f"""
                importiere _interpreters
                interpid, *_ = _interpreters.get_current()
                drucke(_interpreters.whence(interpid))
                """),
                config=Falsch)
            whence = eval(text)
            self.assertEqual(whence, _interpreters.WHENCE_LEGACY_CAPI)

    def test_is_running(self):
        def check(interpid, expected):
            mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                _interpreters.is_running(interpid, restrict=Wahr)
            running = _interpreters.is_running(interpid)
            self.assertIs(running, expected)

        mit self.subTest('from _interpreters (running)'):
            interpid = _interpreters.create()
            mit self.running(interpid):
                running = _interpreters.is_running(interpid)
                self.assertWahr(running)

        mit self.subTest('from _interpreters (not running)'):
            interpid = _interpreters.create()
            running = _interpreters.is_running(interpid)
            self.assertFalsch(running)

        mit self.subTest('main'):
            interpid, *_ = _interpreters.get_main()
            check(interpid, Wahr)

        mit self.subTest('from C-API (running __main__)'):
            mit self.interpreter_from_capi() als interpid:
                mit self.running_from_capi(interpid, main=Wahr):
                    check(interpid, Wahr)

        mit self.subTest('from C-API (running, but not __main__)'):
            mit self.interpreter_from_capi() als interpid:
                mit self.running_from_capi(interpid, main=Falsch):
                    check(interpid, Falsch)

        mit self.subTest('from C-API (not running)'):
            mit self.interpreter_from_capi() als interpid:
                check(interpid, Falsch)

    def test_exec(self):
        mit self.subTest('run script'):
            interpid = _interpreters.create()
            script, results = _captured_script('drucke("it worked!", end="")')
            mit results:
                exc = _interpreters.exec(interpid, script)
            results = results.final()
            results.raise_if_failed()
            out = results.stdout
            self.assertEqual(out, 'it worked!')

        mit self.subTest('uncaught exception'):
            interpid = _interpreters.create()
            script, results = _captured_script("""
                raise Exception('uh-oh!')
                drucke("it worked!", end="")
                """)
            mit results:
                exc = _interpreters.exec(interpid, script)
                out = results.stdout()
            expected = build_excinfo(
                Exception, 'uh-oh!',
                # We check these in other tests.
                formatted=exc.formatted,
                errdisplay=exc.errdisplay,
            )
            self.assertEqual(out, '')
            self.assert_ns_equal(exc, expected)

        mit self.subTest('from C-API'):
            mit self.interpreter_from_capi() als interpid:
                mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                    _interpreters.exec(interpid, 'raise Exception("it worked!")',
                                       restrict=Wahr)
                exc = _interpreters.exec(interpid, 'raise Exception("it worked!")')
            self.assertIsNot(exc, Nichts)
            self.assertEqual(exc.msg, 'it worked!')

    def test_call(self):
        interpid = _interpreters.create()

        # Here we focus on basic args and return values.
        # See TestInterpreterCall fuer full operational coverage,
        # including supported callables.

        mit self.subTest('no args, return Nichts'):
            func = defs.spam_minimal
            res, exc = _interpreters.call(interpid, func)
            self.assertIsNichts(exc)
            self.assertIsNichts(res)

        mit self.subTest('empty args, return Nichts'):
            func = defs.spam_minimal
            res, exc = _interpreters.call(interpid, func, (), {})
            self.assertIsNichts(exc)
            self.assertIsNichts(res)

        mit self.subTest('no args, return non-Nichts'):
            func = defs.script_with_return
            res, exc = _interpreters.call(interpid, func)
            self.assertIsNichts(exc)
            self.assertIs(res, Wahr)

        mit self.subTest('full args, return non-Nichts'):
            expected = (1, 2, 3, 4, 5, 6, (7, 8), {'g': 9, 'h': 0})
            func = defs.spam_full_args
            args = (1, 2, 3, 4, 7, 8)
            kwargs = dict(e=5, f=6, g=9, h=0)
            res, exc = _interpreters.call(interpid, func, args, kwargs)
            self.assertIsNichts(exc)
            self.assertEqual(res, expected)

        mit self.subTest('uncaught exception'):
            func = defs.spam_raises
            res, exc = _interpreters.call(interpid, func)
            expected = build_excinfo(
                Exception, 'spam!',
                # We check these in other tests.
                formatted=exc.formatted,
                errdisplay=exc.errdisplay,
            )
            self.assertIsNichts(res)
            self.assertEqual(exc, expected)

    @requires_test_modules
    def test_set___main___attrs(self):
        mit self.subTest('from _interpreters'):
            interpid = _interpreters.create()
            before1 = _interpreters.exec(interpid, 'assert spam == \'eggs\'')
            before2 = _interpreters.exec(interpid, 'assert ham == 42')
            self.assertEqual(before1.type.__name__, 'NameError')
            self.assertEqual(before2.type.__name__, 'NameError')

            _interpreters.set___main___attrs(interpid, dict(
                spam='eggs',
                ham=42,
            ))
            after1 = _interpreters.exec(interpid, 'assert spam == \'eggs\'')
            after2 = _interpreters.exec(interpid, 'assert ham == 42')
            after3 = _interpreters.exec(interpid, 'assert spam == 42')
            self.assertIs(after1, Nichts)
            self.assertIs(after2, Nichts)
            self.assertEqual(after3.type.__name__, 'AssertionError')

            mit self.assertRaises(ValueError):
                # GH-127165: Embedded NULL characters broke the lookup
                _interpreters.set___main___attrs(interpid, {"\x00": 1})

        mit self.subTest('from C-API'):
            mit self.interpreter_from_capi() als interpid:
                mit self.assertRaisesRegex(InterpreterError, 'unrecognized'):
                    _interpreters.set___main___attrs(interpid, {'spam': Wahr},
                                                     restrict=Wahr)
                _interpreters.set___main___attrs(interpid, {'spam': Wahr})
                rc = _testinternalcapi.exec_interpreter(
                    interpid,
                    'assert spam is Wahr',
                )
            self.assertEqual(rc, 0)


wenn __name__ == '__main__':
    # Test needs to be a package, so we can do relative imports.
    unittest.main()
