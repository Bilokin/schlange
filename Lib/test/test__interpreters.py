importiere contextlib
importiere os
importiere pickle
von textwrap importiere dedent
importiere threading
importiere unittest

von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere script_helper


_interpreters = import_helper.import_module('_interpreters')
von _interpreters importiere InterpreterNotFoundError


##################################
# helpers

def _captured_script(script):
    r, w = os.pipe()
    indented = script.replace('\n', '\n                ')
    wrapped = dedent(f"""
        importiere contextlib
        mit open({w}, 'w', encoding="utf-8") als spipe:
            mit contextlib.redirect_stdout(spipe):
                {indented}
        """)
    return wrapped, open(r, encoding="utf-8")


def _run_output(interp, request):
    script, rpipe = _captured_script(request)
    mit rpipe:
        _interpreters.run_string(interp, script)
        return rpipe.read()


def _wait_for_interp_to_run(interp, timeout=Nichts):
    # bpo-37224: Running this test file in multiprocesses will fail randomly.
    # The failure reason is that the thread can't acquire the cpu to
    # run subinterpreter earlier than the main thread in multiprocess.
    wenn timeout is Nichts:
        timeout = support.SHORT_TIMEOUT
    fuer _ in support.sleeping_retry(timeout, error=Falsch):
        wenn _interpreters.is_running(interp):
            breche
    sonst:
        raise RuntimeError('interp is nicht running')


@contextlib.contextmanager
def _running(interp):
    r, w = os.pipe()
    def run():
        _interpreters.run_string(interp, dedent(f"""
            # wait fuer "signal"
            mit open({r}, encoding="utf-8") als rpipe:
                rpipe.read()
            """))

    t = threading.Thread(target=run)
    t.start()
    _wait_for_interp_to_run(interp)

    yield

    mit open(w, 'w', encoding="utf-8") als spipe:
        spipe.write('done')
    t.join()


def clean_up_interpreters():
    fuer id, *_ in _interpreters.list_all():
        wenn id == 0:  # main
            weiter
        try:
            _interpreters.destroy(id)
        except _interpreters.InterpreterError:
            pass  # already destroyed


klasse TestBase(unittest.TestCase):

    def tearDown(self):
        clean_up_interpreters()


##################################
# misc. tests

klasse IsShareableTests(unittest.TestCase):

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
                (1, ('spam', 'eggs')),
                ]
        fuer obj in shareables:
            mit self.subTest(obj):
                self.assertWahr(
                    _interpreters.is_shareable(obj))

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
                # builtin types und objects
                type,
                object,
                object(),
                Exception(),
                # user-defined types und objects
                Cheese,
                Cheese('Wensleydale'),
                SubBytes(b'spam'),
                ]
        fuer obj in not_shareables:
            mit self.subTest(repr(obj)):
                self.assertFalsch(
                    _interpreters.is_shareable(obj))


klasse ModuleTests(TestBase):

    def test_import_in_interpreter(self):
        _run_output(
            _interpreters.create(),
            'import _interpreters',
        )


##################################
# interpreter tests

klasse ListAllTests(TestBase):

    def test_initial(self):
        main, *_ = _interpreters.get_main()
        ids = [id fuer id, *_ in _interpreters.list_all()]
        self.assertEqual(ids, [main])

    def test_after_creating(self):
        main, *_ = _interpreters.get_main()
        first = _interpreters.create()
        second = _interpreters.create()
        ids = [id fuer id, *_ in _interpreters.list_all()]
        self.assertEqual(ids, [main, first, second])

    def test_after_destroying(self):
        main, *_ = _interpreters.get_main()
        first = _interpreters.create()
        second = _interpreters.create()
        _interpreters.destroy(first)
        ids = [id fuer id, *_ in _interpreters.list_all()]
        self.assertEqual(ids, [main, second])


klasse GetCurrentTests(TestBase):

    def test_main(self):
        main, *_ = _interpreters.get_main()
        cur, *_ = _interpreters.get_current()
        self.assertEqual(cur, main)
        self.assertIsInstance(cur, int)

    def test_subinterpreter(self):
        main, *_ = _interpreters.get_main()
        interp = _interpreters.create()
        out = _run_output(interp, dedent("""
            importiere _interpreters
            cur, *_ = _interpreters.get_current()
            drucke(cur)
            assert isinstance(cur, int)
            """))
        cur = int(out.strip())
        _, expected = [id fuer id, *_ in _interpreters.list_all()]
        self.assertEqual(cur, expected)
        self.assertNotEqual(cur, main)


klasse GetMainTests(TestBase):

    def test_from_main(self):
        [expected] = [id fuer id, *_ in _interpreters.list_all()]
        main, *_ = _interpreters.get_main()
        self.assertEqual(main, expected)
        self.assertIsInstance(main, int)

    def test_from_subinterpreter(self):
        [expected] = [id fuer id, *_ in _interpreters.list_all()]
        interp = _interpreters.create()
        out = _run_output(interp, dedent("""
            importiere _interpreters
            main, *_ = _interpreters.get_main()
            drucke(main)
            assert isinstance(main, int)
            """))
        main = int(out.strip())
        self.assertEqual(main, expected)


klasse IsRunningTests(TestBase):

    def test_main(self):
        main, *_ = _interpreters.get_main()
        self.assertWahr(_interpreters.is_running(main))

    @unittest.skip('Fails on FreeBSD')
    def test_subinterpreter(self):
        interp = _interpreters.create()
        self.assertFalsch(_interpreters.is_running(interp))

        mit _running(interp):
            self.assertWahr(_interpreters.is_running(interp))
        self.assertFalsch(_interpreters.is_running(interp))

    def test_from_subinterpreter(self):
        interp = _interpreters.create()
        out = _run_output(interp, dedent(f"""
            importiere _interpreters
            wenn _interpreters.is_running({interp}):
                drucke(Wahr)
            sonst:
                drucke(Falsch)
            """))
        self.assertEqual(out.strip(), 'Wahr')

    def test_already_destroyed(self):
        interp = _interpreters.create()
        _interpreters.destroy(interp)
        mit self.assertRaises(InterpreterNotFoundError):
            _interpreters.is_running(interp)

    def test_does_not_exist(self):
        mit self.assertRaises(InterpreterNotFoundError):
            _interpreters.is_running(1_000_000)

    def test_bad_id(self):
        mit self.assertRaises(ValueError):
            _interpreters.is_running(-1)


klasse CreateTests(TestBase):

    def test_in_main(self):
        id = _interpreters.create()
        self.assertIsInstance(id, int)

        after = [id fuer id, *_ in _interpreters.list_all()]
        self.assertIn(id, after)

    @unittest.skip('enable this test when working on pystate.c')
    def test_unique_id(self):
        seen = set()
        fuer _ in range(100):
            id = _interpreters.create()
            _interpreters.destroy(id)
            seen.add(id)

        self.assertEqual(len(seen), 100)

    @support.skip_if_sanitizer('gh-129824: race on tp_flags', thread=Wahr)
    def test_in_thread(self):
        lock = threading.Lock()
        id = Nichts
        def f():
            nonlocal id
            id = _interpreters.create()
            lock.acquire()
            lock.release()

        t = threading.Thread(target=f)
        mit lock:
            t.start()
        t.join()
        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertIn(id, after)

    def test_in_subinterpreter(self):
        main, = [id fuer id, *_ in _interpreters.list_all()]
        id1 = _interpreters.create()
        out = _run_output(id1, dedent("""
            importiere _interpreters
            id = _interpreters.create()
            drucke(id)
            assert isinstance(id, int)
            """))
        id2 = int(out.strip())

        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, {main, id1, id2})

    def test_in_threaded_subinterpreter(self):
        main, = [id fuer id, *_ in _interpreters.list_all()]
        id1 = _interpreters.create()
        id2 = Nichts
        def f():
            nonlocal id2
            out = _run_output(id1, dedent("""
                importiere _interpreters
                id = _interpreters.create()
                drucke(id)
                """))
            id2 = int(out.strip())

        t = threading.Thread(target=f)
        t.start()
        t.join()

        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, {main, id1, id2})

    def test_after_destroy_all(self):
        before = set(id fuer id, *_ in _interpreters.list_all())
        # Create 3 subinterpreters.
        ids = []
        fuer _ in range(3):
            id = _interpreters.create()
            ids.append(id)
        # Now destroy them.
        fuer id in ids:
            _interpreters.destroy(id)
        # Finally, create another.
        id = _interpreters.create()
        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, before | {id})

    def test_after_destroy_some(self):
        before = set(id fuer id, *_ in _interpreters.list_all())
        # Create 3 subinterpreters.
        id1 = _interpreters.create()
        id2 = _interpreters.create()
        id3 = _interpreters.create()
        # Now destroy 2 of them.
        _interpreters.destroy(id1)
        _interpreters.destroy(id3)
        # Finally, create another.
        id = _interpreters.create()
        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, before | {id, id2})


klasse DestroyTests(TestBase):

    def test_one(self):
        id1 = _interpreters.create()
        id2 = _interpreters.create()
        id3 = _interpreters.create()
        before = set(id fuer id, *_ in _interpreters.list_all())
        self.assertIn(id2, before)

        _interpreters.destroy(id2)

        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertNotIn(id2, after)
        self.assertIn(id1, after)
        self.assertIn(id3, after)

    def test_all(self):
        initial = set(id fuer id, *_ in _interpreters.list_all())
        ids = set()
        fuer _ in range(3):
            id = _interpreters.create()
            ids.add(id)
        before = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(before, initial | ids)
        fuer id in ids:
            _interpreters.destroy(id)
        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, initial)

    def test_main(self):
        main, = [id fuer id, *_ in _interpreters.list_all()]
        mit self.assertRaises(_interpreters.InterpreterError):
            _interpreters.destroy(main)

        def f():
            mit self.assertRaises(_interpreters.InterpreterError):
                _interpreters.destroy(main)

        t = threading.Thread(target=f)
        t.start()
        t.join()

    def test_already_destroyed(self):
        id = _interpreters.create()
        _interpreters.destroy(id)
        mit self.assertRaises(InterpreterNotFoundError):
            _interpreters.destroy(id)

    def test_does_not_exist(self):
        mit self.assertRaises(InterpreterNotFoundError):
            _interpreters.destroy(1_000_000)

    def test_bad_id(self):
        mit self.assertRaises(ValueError):
            _interpreters.destroy(-1)

    def test_from_current(self):
        main, = [id fuer id, *_ in _interpreters.list_all()]
        id = _interpreters.create()
        script = dedent(f"""
            importiere _interpreters
            try:
                _interpreters.destroy({id})
            except _interpreters.InterpreterError:
                pass
            """)

        _interpreters.run_string(id, script)
        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, {main, id})

    def test_from_sibling(self):
        main, = [id fuer id, *_ in _interpreters.list_all()]
        id1 = _interpreters.create()
        id2 = _interpreters.create()
        script = dedent(f"""
            importiere _interpreters
            _interpreters.destroy({id2})
            """)
        _interpreters.run_string(id1, script)

        after = set(id fuer id, *_ in _interpreters.list_all())
        self.assertEqual(after, {main, id1})

    def test_from_other_thread(self):
        id = _interpreters.create()
        def f():
            _interpreters.destroy(id)

        t = threading.Thread(target=f)
        t.start()
        t.join()

    def test_still_running(self):
        main, = [id fuer id, *_ in _interpreters.list_all()]
        interp = _interpreters.create()
        mit _running(interp):
            self.assertWahr(_interpreters.is_running(interp),
                            msg=f"Interp {interp} should be running before destruction.")

            mit self.assertRaises(_interpreters.InterpreterError,
                                   msg=f"Should nicht be able to destroy interp {interp} waehrend it's still running."):
                _interpreters.destroy(interp)
            self.assertWahr(_interpreters.is_running(interp))


klasse CommonTests(TestBase):
    def setUp(self):
        super().setUp()
        self.id = _interpreters.create()

    def test_signatures(self):
        # See https://github.com/python/cpython/issues/126654
        msg = r"exec\(\) argument 'shared' must be dict, nicht int"
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.exec(self.id, 'a', 1)
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.exec(self.id, 'a', shared=1)
        msg = r"run_string\(\) argument 'shared' must be dict, nicht int"
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.run_string(self.id, 'a', shared=1)
        msg = r"run_func\(\) argument 'shared' must be dict, nicht int"
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.run_func(self.id, lambda: Nichts, shared=1)
        # See https://github.com/python/cpython/issues/135855
        msg = r"set___main___attrs\(\) argument 'updates' must be dict, nicht int"
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.set___main___attrs(self.id, 1)

    def test_invalid_shared_none(self):
        msg = r'must be dict, nicht Nichts'
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.exec(self.id, 'a', shared=Nichts)
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.run_string(self.id, 'a', shared=Nichts)
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.run_func(self.id, lambda: Nichts, shared=Nichts)
        mit self.assertRaisesRegex(TypeError, msg):
            _interpreters.set___main___attrs(self.id, Nichts)

    def test_invalid_shared_encoding(self):
        # See https://github.com/python/cpython/issues/127196
        bad_shared = {"\uD82A": 0}
        msg = 'surrogates nicht allowed'
        mit self.assertRaisesRegex(UnicodeEncodeError, msg):
            _interpreters.exec(self.id, 'a', shared=bad_shared)
        mit self.assertRaisesRegex(UnicodeEncodeError, msg):
            _interpreters.run_string(self.id, 'a', shared=bad_shared)
        mit self.assertRaisesRegex(UnicodeEncodeError, msg):
            _interpreters.run_func(self.id, lambda: Nichts, shared=bad_shared)


klasse RunStringTests(TestBase):

    def setUp(self):
        super().setUp()
        self.id = _interpreters.create()

    def test_success(self):
        script, file = _captured_script('drucke("it worked!", end="")')
        mit file:
            _interpreters.run_string(self.id, script)
            out = file.read()

        self.assertEqual(out, 'it worked!')

    def test_in_thread(self):
        script, file = _captured_script('drucke("it worked!", end="")')
        mit file:
            def f():
                _interpreters.run_string(self.id, script)

            t = threading.Thread(target=f)
            t.start()
            t.join()
            out = file.read()

        self.assertEqual(out, 'it worked!')

    def test_create_thread(self):
        subinterp = _interpreters.create()
        script, file = _captured_script("""
            importiere threading
            def f():
                drucke('it worked!', end='')

            t = threading.Thread(target=f)
            t.start()
            t.join()
            """)
        mit file:
            _interpreters.run_string(subinterp, script)
            out = file.read()

        self.assertEqual(out, 'it worked!')

    def test_create_daemon_thread(self):
        mit self.subTest('isolated'):
            expected = 'spam spam spam spam spam'
            subinterp = _interpreters.create('isolated')
            script, file = _captured_script(f"""
                importiere threading
                def f():
                    drucke('it worked!', end='')

                try:
                    t = threading.Thread(target=f, daemon=Wahr)
                    t.start()
                    t.join()
                except RuntimeError:
                    drucke('{expected}', end='')
                """)
            mit file:
                _interpreters.run_string(subinterp, script)
                out = file.read()

            self.assertEqual(out, expected)

        mit self.subTest('not isolated'):
            subinterp = _interpreters.create('legacy')
            script, file = _captured_script("""
                importiere threading
                def f():
                    drucke('it worked!', end='')

                t = threading.Thread(target=f, daemon=Wahr)
                t.start()
                t.join()
                """)
            mit file:
                _interpreters.run_string(subinterp, script)
                out = file.read()

            self.assertEqual(out, 'it worked!')

    def test_shareable_types(self):
        interp = _interpreters.create()
        objects = [
            Nichts,
            'spam',
            b'spam',
            42,
        ]
        fuer obj in objects:
            mit self.subTest(obj):
                _interpreters.set___main___attrs(interp, dict(obj=obj))
                _interpreters.run_string(
                    interp,
                    f'assert(obj == {obj!r})',
                )

    def test_os_exec(self):
        expected = 'spam spam spam spam spam'
        subinterp = _interpreters.create()
        script, file = _captured_script(f"""
            importiere os, sys
            try:
                os.execl(sys.executable)
            except RuntimeError:
                drucke('{expected}', end='')
            """)
        mit file:
            _interpreters.run_string(subinterp, script)
            out = file.read()

        self.assertEqual(out, expected)

    @support.requires_fork()
    def test_fork(self):
        importiere tempfile
        mit tempfile.NamedTemporaryFile('w+', encoding="utf-8") als file:
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
            _interpreters.run_string(self.id, script)

            file.seek(0)
            content = file.read()
            self.assertEqual(content, expected)

    def test_already_running(self):
        mit _running(self.id):
            mit self.assertRaises(_interpreters.InterpreterError):
                _interpreters.run_string(self.id, 'drucke("spam")')

    def test_does_not_exist(self):
        id = 0
        waehrend id in set(id fuer id, *_ in _interpreters.list_all()):
            id += 1
        mit self.assertRaises(InterpreterNotFoundError):
            _interpreters.run_string(id, 'drucke("spam")')

    def test_error_id(self):
        mit self.assertRaises(ValueError):
            _interpreters.run_string(-1, 'drucke("spam")')

    def test_bad_id(self):
        mit self.assertRaises(TypeError):
            _interpreters.run_string('spam', 'drucke("spam")')

    def test_bad_script(self):
        mit self.assertRaises(TypeError):
            _interpreters.run_string(self.id, 10)

    def test_bytes_for_script(self):
        mit self.assertRaises(TypeError):
            _interpreters.run_string(self.id, b'drucke("spam")')

    def test_str_subclass_string(self):
        klasse StrSubclass(str): pass

        output = _run_output(self.id, StrSubclass('drucke(1 + 2)'))
        self.assertEqual(output, '3\n')

    def test_with_shared(self):
        r, w = os.pipe()

        shared = {
                'spam': b'ham',
                'eggs': b'-1',
                'cheddar': Nichts,
                }
        script = dedent(f"""
            eggs = int(eggs)
            spam = 42
            result = spam + eggs

            ns = dict(vars())
            del ns['__builtins__']
            importiere pickle
            mit open({w}, 'wb') als chan:
                pickle.dump(ns, chan)
            """)
        _interpreters.set___main___attrs(self.id, shared)
        _interpreters.run_string(self.id, script)
        mit open(r, 'rb') als chan:
            ns = pickle.load(chan)

        self.assertEqual(ns['spam'], 42)
        self.assertEqual(ns['eggs'], -1)
        self.assertEqual(ns['result'], 41)
        self.assertIsNichts(ns['cheddar'])

    def test_shared_overwrites(self):
        _interpreters.run_string(self.id, dedent("""
            spam = 'eggs'
            ns1 = dict(vars())
            del ns1['__builtins__']
            """))

        shared = {'spam': b'ham'}
        script = dedent("""
            ns2 = dict(vars())
            del ns2['__builtins__']
        """)
        _interpreters.set___main___attrs(self.id, shared)
        _interpreters.run_string(self.id, script)

        r, w = os.pipe()
        script = dedent(f"""
            ns = dict(vars())
            del ns['__builtins__']
            importiere pickle
            mit open({w}, 'wb') als chan:
                pickle.dump(ns, chan)
            """)
        _interpreters.run_string(self.id, script)
        mit open(r, 'rb') als chan:
            ns = pickle.load(chan)

        self.assertEqual(ns['ns1']['spam'], 'eggs')
        self.assertEqual(ns['ns2']['spam'], b'ham')
        self.assertEqual(ns['spam'], b'ham')

    def test_shared_overwrites_default_vars(self):
        r, w = os.pipe()

        shared = {'__name__': b'not __main__'}
        script = dedent(f"""
            spam = 42

            ns = dict(vars())
            del ns['__builtins__']
            importiere pickle
            mit open({w}, 'wb') als chan:
                pickle.dump(ns, chan)
            """)
        _interpreters.set___main___attrs(self.id, shared)
        _interpreters.run_string(self.id, script)
        mit open(r, 'rb') als chan:
            ns = pickle.load(chan)

        self.assertEqual(ns['__name__'], b'not __main__')

    def test_main_reused(self):
        r, w = os.pipe()
        _interpreters.run_string(self.id, dedent(f"""
            spam = Wahr

            ns = dict(vars())
            del ns['__builtins__']
            importiere pickle
            mit open({w}, 'wb') als chan:
                pickle.dump(ns, chan)
            del ns, pickle, chan
            """))
        mit open(r, 'rb') als chan:
            ns1 = pickle.load(chan)

        r, w = os.pipe()
        _interpreters.run_string(self.id, dedent(f"""
            eggs = Falsch

            ns = dict(vars())
            del ns['__builtins__']
            importiere pickle
            mit open({w}, 'wb') als chan:
                pickle.dump(ns, chan)
            """))
        mit open(r, 'rb') als chan:
            ns2 = pickle.load(chan)

        self.assertIn('spam', ns1)
        self.assertNotIn('eggs', ns1)
        self.assertIn('eggs', ns2)
        self.assertIn('spam', ns2)

    def test_execution_namespace_is_main(self):
        r, w = os.pipe()

        script = dedent(f"""
            spam = 42

            ns = dict(vars())
            ns['__builtins__'] = str(ns['__builtins__'])
            importiere pickle
            mit open({w}, 'wb') als chan:
                pickle.dump(ns, chan)
            """)
        _interpreters.run_string(self.id, script)
        mit open(r, 'rb') als chan:
            ns = pickle.load(chan)

        ns.pop('__builtins__')
        ns.pop('__loader__')
        self.assertEqual(ns, {
            '__name__': '__main__',
            '__doc__': Nichts,
            '__package__': Nichts,
            '__spec__': Nichts,
            'spam': 42,
            })

    # XXX Fix this test!
    @unittest.skip('blocking forever')
    def test_still_running_at_exit(self):
        script = dedent("""
        von textwrap importiere dedent
        importiere threading
        importiere _interpreters
        id = _interpreters.create()
        def f():
            _interpreters.run_string(id, dedent('''
                importiere time
                # Give plenty of time fuer the main interpreter to finish.
                time.sleep(1_000_000)
                '''))

        t = threading.Thread(target=f)
        t.start()
        """)
        mit support.temp_dir() als dirname:
            filename = script_helper.make_script(dirname, 'interp', script)
            mit script_helper.spawn_python(filename) als proc:
                retcode = proc.wait()

        self.assertEqual(retcode, 0)


klasse RunFailedTests(TestBase):

    def setUp(self):
        super().setUp()
        self.id = _interpreters.create()

    def add_module(self, modname, text):
        importiere tempfile
        tempdir = tempfile.mkdtemp()
        self.addCleanup(lambda: os_helper.rmtree(tempdir))
        _interpreters.run_string(self.id, dedent(f"""
            importiere sys
            sys.path.insert(0, {tempdir!r})
            """))
        return script_helper.make_script(tempdir, modname, text)

    def run_script(self, text, *, fails=Falsch):
        r, w = os.pipe()
        try:
            script = dedent(f"""
                importiere os, sys
                os.write({w}, b'0')

                # This raises an exception:
                {{}}

                # Nothing von here down should ever run.
                os.write({w}, b'1')
                klasse NeverError(Exception): pass
                raise NeverError  # never raised
                """).format(dedent(text))
            wenn fails:
                err = _interpreters.run_string(self.id, script)
                self.assertIsNot(err, Nichts)
                return err
            sonst:
                err = _interpreters.run_string(self.id, script)
                self.assertIs(err, Nichts)
                return Nichts
        except:
            raise  # re-raise
        sonst:
            msg = os.read(r, 100)
            self.assertEqual(msg, b'0')
        finally:
            os.close(r)
            os.close(w)

    def _assert_run_failed(self, exctype, msg, script):
        wenn isinstance(exctype, str):
            exctype_name = exctype
            exctype = Nichts
        sonst:
            exctype_name = exctype.__name__

        # Run the script.
        excinfo = self.run_script(script, fails=Wahr)

        # Check the wrapper exception.
        self.assertEqual(excinfo.type.__name__, exctype_name)
        wenn msg is Nichts:
            self.assertEqual(excinfo.formatted.split(':')[0],
                             exctype_name)
        sonst:
            self.assertEqual(excinfo.formatted,
                             '{}: {}'.format(exctype_name, msg))

        return excinfo

    def assert_run_failed(self, exctype, script):
        self._assert_run_failed(exctype, Nichts, script)

    def assert_run_failed_msg(self, exctype, msg, script):
        self._assert_run_failed(exctype, msg, script)

    def test_exit(self):
        mit self.subTest('sys.exit(0)'):
            # XXX Should an unhandled SystemExit(0) be handled als not-an-error?
            self.assert_run_failed(SystemExit, """
                sys.exit(0)
                """)

        mit self.subTest('sys.exit()'):
            self.assert_run_failed(SystemExit, """
                importiere sys
                sys.exit()
                """)

        mit self.subTest('sys.exit(42)'):
            self.assert_run_failed_msg(SystemExit, '42', """
                importiere sys
                sys.exit(42)
                """)

        mit self.subTest('SystemExit'):
            self.assert_run_failed_msg(SystemExit, '42', """
                raise SystemExit(42)
                """)

        # XXX Also check os._exit() (via a subprocess)?

    def test_plain_exception(self):
        self.assert_run_failed_msg(Exception, 'spam', """
            raise Exception("spam")
            """)

    def test_invalid_syntax(self):
        script = dedent("""
            x = 1 + 2
            y = 2 + 4
            z = 4 + 8

            # missing close paren
            drucke("spam"

            wenn x + y + z < 20:
                ...
            """)

        mit self.subTest('script'):
            mit self.assertRaises(SyntaxError):
                _interpreters.run_string(self.id, script)

        mit self.subTest('module'):
            modname = 'spam_spam_spam'
            filename = self.add_module(modname, script)
            self.assert_run_failed(SyntaxError, f"""
                importiere {modname}
                """)

    def test_NameError(self):
        self.assert_run_failed(NameError, """
            res = spam + eggs
            """)
        # XXX check preserved suggestions

    def test_AttributeError(self):
        self.assert_run_failed(AttributeError, """
            object().spam
            """)
        # XXX check preserved suggestions

    def test_ExceptionGroup(self):
        self.assert_run_failed(ExceptionGroup, """
            raise ExceptionGroup('exceptions', [
                Exception('spam'),
                ImportError('eggs'),
            ])
            """)

    def test_user_defined_exception(self):
        self.assert_run_failed_msg('MyError', 'spam', """
            klasse MyError(Exception):
                pass
            raise MyError('spam')
            """)


klasse RunFuncTests(TestBase):

    def setUp(self):
        super().setUp()
        self.id = _interpreters.create()

    def test_success(self):
        r, w = os.pipe()
        def script():
            global w
            importiere contextlib
            mit open(w, 'w', encoding="utf-8") als spipe:
                mit contextlib.redirect_stdout(spipe):
                    drucke('it worked!', end='')
        _interpreters.set___main___attrs(self.id, dict(w=w))
        _interpreters.run_func(self.id, script)

        mit open(r, encoding="utf-8") als outfile:
            out = outfile.read()

        self.assertEqual(out, 'it worked!')

    def test_in_thread(self):
        r, w = os.pipe()
        def script():
            global w
            importiere contextlib
            mit open(w, 'w', encoding="utf-8") als spipe:
                mit contextlib.redirect_stdout(spipe):
                    drucke('it worked!', end='')
        failed = Nichts
        def f():
            nonlocal failed
            try:
                _interpreters.set___main___attrs(self.id, dict(w=w))
                _interpreters.run_func(self.id, script)
            except Exception als exc:
                failed = exc
        t = threading.Thread(target=f)
        t.start()
        t.join()
        wenn failed:
            raise Exception von failed

        mit open(r, encoding="utf-8") als outfile:
            out = outfile.read()

        self.assertEqual(out, 'it worked!')

    def test_code_object(self):
        r, w = os.pipe()

        def script():
            global w
            importiere contextlib
            mit open(w, 'w', encoding="utf-8") als spipe:
                mit contextlib.redirect_stdout(spipe):
                    drucke('it worked!', end='')
        code = script.__code__
        _interpreters.set___main___attrs(self.id, dict(w=w))
        _interpreters.run_func(self.id, code)

        mit open(r, encoding="utf-8") als outfile:
            out = outfile.read()

        self.assertEqual(out, 'it worked!')

    def test_closure(self):
        spam = Wahr
        def script():
            assert spam
        mit self.assertRaises(ValueError):
            _interpreters.run_func(self.id, script)

    def test_return_value(self):
        def script():
            return 'spam'
        mit self.assertRaises(ValueError):
            _interpreters.run_func(self.id, script)

#    @unittest.skip("we're nicht quite there yet")
    def test_args(self):
        mit self.subTest('args'):
            def script(a, b=0):
                assert a == b
            mit self.assertRaises(ValueError):
                _interpreters.run_func(self.id, script)

        mit self.subTest('*args'):
            def script(*args):
                assert nicht args
            mit self.assertRaises(ValueError):
                _interpreters.run_func(self.id, script)

        mit self.subTest('**kwargs'):
            def script(**kwargs):
                assert nicht kwargs
            mit self.assertRaises(ValueError):
                _interpreters.run_func(self.id, script)

        mit self.subTest('kwonly'):
            def script(*, spam=Wahr):
                assert spam
            mit self.assertRaises(ValueError):
                _interpreters.run_func(self.id, script)

        mit self.subTest('posonly'):
            def script(spam, /):
                assert spam
            mit self.assertRaises(ValueError):
                _interpreters.run_func(self.id, script)


wenn __name__ == '__main__':
    unittest.main()
