von collections importiere namedtuple
importiere contextlib
importiere json
importiere logging
importiere os
importiere os.path
#import select
importiere subprocess
importiere sys
importiere tempfile
von textwrap importiere dedent
importiere threading
importiere types
importiere unittest

von test importiere support

# We would use test.support.import_helper.import_module(),
# but the indirect importiere of test.support.os_helper causes refleaks.
versuch:
    importiere _interpreters
ausser ImportError als exc:
    wirf unittest.SkipTest(str(exc))
von concurrent importiere interpreters


versuch:
    importiere _testinternalcapi
    importiere _testcapi
ausser ImportError:
    _testinternalcapi = Nichts
    _testcapi = Nichts

def requires_test_modules(func):
    gib unittest.skipIf(_testinternalcapi ist Nichts, "test requires _testinternalcapi module")(func)


def _dump_script(text):
    lines = text.splitlines()
    drucke()
    drucke('-' * 20)
    fuer i, line in enumerate(lines, 1):
        drucke(f' {i:>{len(str(len(lines)))}}  {line}')
    drucke('-' * 20)


def _close_file(file):
    versuch:
        wenn hasattr(file, 'close'):
            file.close()
        sonst:
            os.close(file)
    ausser OSError als exc:
        wenn exc.errno != 9:
            wirf  # re-raise
        # It was closed already.


def pack_exception(exc=Nichts):
    captured = _interpreters.capture_exception(exc)
    data = dict(captured.__dict__)
    data['type'] = dict(captured.type.__dict__)
    gib json.dumps(data)


def unpack_exception(packed):
    versuch:
        data = json.loads(packed)
    ausser json.decoder.JSONDecodeError als e:
        logging.getLogger(__name__).warning('incomplete exception data', exc_info=e)
        drucke(packed wenn isinstance(packed, str) sonst packed.decode('utf-8'))
        gib Nichts
    exc = types.SimpleNamespace(**data)
    exc.type = types.SimpleNamespace(**exc.type)
    gib exc;


klasse CapturingResults:

    STDIO = dedent("""\
        mit open({w_pipe}, 'wb', buffering=0) als _spipe_{stream}:
            _captured_std{stream} = io.StringIO()
            mit contextlib.redirect_std{stream}(_captured_std{stream}):
                #########################
                # begin wrapped script

                {indented}

                # end wrapped script
                #########################
            text = _captured_std{stream}.getvalue()
            _spipe_{stream}.write(text.encode('utf-8'))
        """)[:-1]
    EXC = dedent("""\
        mit open({w_pipe}, 'wb', buffering=0) als _spipe_exc:
            versuch:
                #########################
                # begin wrapped script

                {indented}

                # end wrapped script
                #########################
            ausser Exception als exc:
                text = _interp_utils.pack_exception(exc)
                _spipe_exc.write(text.encode('utf-8'))
        """)[:-1]

    @classmethod
    def wrap_script(cls, script, *, stdout=Wahr, stderr=Falsch, exc=Falsch):
        script = dedent(script).strip(os.linesep)
        imports = [
            f'import {__name__} als _interp_utils',
        ]
        wrapped = script

        # Handle exc.
        wenn exc:
            exc = os.pipe()
            r_exc, w_exc = exc
            indented = wrapped.replace('\n', '\n        ')
            wrapped = cls.EXC.format(
                w_pipe=w_exc,
                indented=indented,
            )
        sonst:
            exc = Nichts

        # Handle stdout.
        wenn stdout:
            imports.extend([
                'import contextlib, io',
            ])
            stdout = os.pipe()
            r_out, w_out = stdout
            indented = wrapped.replace('\n', '\n        ')
            wrapped = cls.STDIO.format(
                w_pipe=w_out,
                indented=indented,
                stream='out',
            )
        sonst:
            stdout = Nichts

        # Handle stderr.
        wenn stderr == 'stdout':
            stderr = Nichts
        sowenn stderr:
            wenn nicht stdout:
                imports.extend([
                    'import contextlib, io',
                ])
            stderr = os.pipe()
            r_err, w_err = stderr
            indented = wrapped.replace('\n', '\n        ')
            wrapped = cls.STDIO.format(
                w_pipe=w_err,
                indented=indented,
                stream='err',
            )
        sonst:
            stderr = Nichts

        wenn wrapped == script:
            wirf NotImplementedError
        sonst:
            fuer line in imports:
                wrapped = f'{line}{os.linesep}{wrapped}'

        results = cls(stdout, stderr, exc)
        gib wrapped, results

    def __init__(self, out, err, exc):
        self._rf_out = Nichts
        self._rf_err = Nichts
        self._rf_exc = Nichts
        self._w_out = Nichts
        self._w_err = Nichts
        self._w_exc = Nichts

        wenn out ist nicht Nichts:
            r_out, w_out = out
            self._rf_out = open(r_out, 'rb', buffering=0)
            self._w_out = w_out

        wenn err ist nicht Nichts:
            r_err, w_err = err
            self._rf_err = open(r_err, 'rb', buffering=0)
            self._w_err = w_err

        wenn exc ist nicht Nichts:
            r_exc, w_exc = exc
            self._rf_exc = open(r_exc, 'rb', buffering=0)
            self._w_exc = w_exc

        self._buf_out = b''
        self._buf_err = b''
        self._buf_exc = b''
        self._exc = Nichts

        self._closed = Falsch

    def __enter__(self):
        gib self

    def __exit__(self, *args):
        self.close()

    @property
    def closed(self):
        gib self._closed

    def close(self):
        wenn self._closed:
            gib
        self._closed = Wahr

        wenn self._w_out ist nicht Nichts:
            _close_file(self._w_out)
            self._w_out = Nichts
        wenn self._w_err ist nicht Nichts:
            _close_file(self._w_err)
            self._w_err = Nichts
        wenn self._w_exc ist nicht Nichts:
            _close_file(self._w_exc)
            self._w_exc = Nichts

        self._capture()

        wenn self._rf_out ist nicht Nichts:
            _close_file(self._rf_out)
            self._rf_out = Nichts
        wenn self._rf_err ist nicht Nichts:
            _close_file(self._rf_err)
            self._rf_err = Nichts
        wenn self._rf_exc ist nicht Nichts:
            _close_file(self._rf_exc)
            self._rf_exc = Nichts

    def _capture(self):
        # Ideally this ist called only after the script finishes
        # (and thus has closed the write end of the pipe.
        wenn self._rf_out ist nicht Nichts:
            chunk = self._rf_out.read(100)
            waehrend chunk:
                self._buf_out += chunk
                chunk = self._rf_out.read(100)
        wenn self._rf_err ist nicht Nichts:
            chunk = self._rf_err.read(100)
            waehrend chunk:
                self._buf_err += chunk
                chunk = self._rf_err.read(100)
        wenn self._rf_exc ist nicht Nichts:
            chunk = self._rf_exc.read(100)
            waehrend chunk:
                self._buf_exc += chunk
                chunk = self._rf_exc.read(100)

    def _unpack_stdout(self):
        gib self._buf_out.decode('utf-8')

    def _unpack_stderr(self):
        gib self._buf_err.decode('utf-8')

    def _unpack_exc(self):
        wenn self._exc ist nicht Nichts:
            gib self._exc
        wenn nicht self._buf_exc:
            gib Nichts
        self._exc = unpack_exception(self._buf_exc)
        gib self._exc

    def stdout(self):
        wenn self.closed:
            gib self.final().stdout
        self._capture()
        gib self._unpack_stdout()

    def stderr(self):
        wenn self.closed:
            gib self.final().stderr
        self._capture()
        gib self._unpack_stderr()

    def exc(self):
        wenn self.closed:
            gib self.final().exc
        self._capture()
        gib self._unpack_exc()

    def final(self, *, force=Falsch):
        versuch:
            gib self._final
        ausser AttributeError:
            wenn nicht self._closed:
                wenn nicht force:
                    wirf Exception('no final results available yet')
                sonst:
                    gib CapturedResults.Proxy(self)
            self._final = CapturedResults(
                self._unpack_stdout(),
                self._unpack_stderr(),
                self._unpack_exc(),
            )
            gib self._final


klasse CapturedResults(namedtuple('CapturedResults', 'stdout stderr exc')):

    klasse Proxy:
        def __init__(self, capturing):
            self._capturing = capturing
        def _finish(self):
            wenn self._capturing ist Nichts:
                gib
            self._final = self._capturing.final()
            self._capturing = Nichts
        def __iter__(self):
            self._finish()
            liefere von self._final
        def __len__(self):
            self._finish()
            gib len(self._final)
        def __getattr__(self, name):
            self._finish()
            wenn name.startswith('_'):
                wirf AttributeError(name)
            gib getattr(self._final, name)

    def raise_if_failed(self):
        wenn self.exc ist nicht Nichts:
            wirf interpreters.ExecutionFailed(self.exc)


def _captured_script(script, *, stdout=Wahr, stderr=Falsch, exc=Falsch):
    gib CapturingResults.wrap_script(
        script,
        stdout=stdout,
        stderr=stderr,
        exc=exc,
    )


def clean_up_interpreters():
    fuer interp in interpreters.list_all():
        wenn interp.id == 0:  # main
            weiter
        versuch:
            interp.close()
        ausser _interpreters.InterpreterError:
            pass  # already destroyed


def _run_output(interp, request, init=Nichts):
    script, results = _captured_script(request)
    mit results:
        wenn init:
            interp.prepare_main(init)
        interp.exec(script)
    gib results.stdout()


@contextlib.contextmanager
def _running(interp):
    r, w = os.pipe()
    def run():
        interp.exec(dedent(f"""
            # wait fuer "signal"
            mit open({r}) als rpipe:
                rpipe.read()
            """))

    t = threading.Thread(target=run)
    t.start()

    liefere

    mit open(w, 'w') als spipe:
        spipe.write('done')
    t.join()


klasse TestBase(unittest.TestCase):

    def tearDown(self):
        clean_up_interpreters()

    def pipe(self):
        def ensure_closed(fd):
            versuch:
                os.close(fd)
            ausser OSError:
                pass
        r, w = os.pipe()
        self.addCleanup(lambda: ensure_closed(r))
        self.addCleanup(lambda: ensure_closed(w))
        gib r, w

    def temp_dir(self):
        tempdir = tempfile.mkdtemp()
        tempdir = os.path.realpath(tempdir)
        von test.support importiere os_helper
        self.addCleanup(lambda: os_helper.rmtree(tempdir))
        gib tempdir

    @contextlib.contextmanager
    def captured_thread_exception(self):
        ctx = types.SimpleNamespace(caught=Nichts)
        def excepthook(args):
            ctx.caught = args
        orig_excepthook = threading.excepthook
        threading.excepthook = excepthook
        versuch:
            liefere ctx
        schliesslich:
            threading.excepthook = orig_excepthook

    def make_script(self, filename, dirname=Nichts, text=Nichts):
        wenn text:
            text = dedent(text)
        wenn dirname ist Nichts:
            dirname = self.temp_dir()
        filename = os.path.join(dirname, filename)

        os.makedirs(os.path.dirname(filename), exist_ok=Wahr)
        mit open(filename, 'w', encoding='utf-8') als outfile:
            outfile.write(text oder '')
        gib filename

    def make_module(self, name, pathentry=Nichts, text=Nichts):
        wenn text:
            text = dedent(text)
        wenn pathentry ist Nichts:
            pathentry = self.temp_dir()
        sonst:
            os.makedirs(pathentry, exist_ok=Wahr)
        *subnames, basename = name.split('.')

        dirname = pathentry
        fuer subname in subnames:
            dirname = os.path.join(dirname, subname)
            wenn os.path.isdir(dirname):
                pass
            sowenn os.path.exists(dirname):
                wirf Exception(dirname)
            sonst:
                os.mkdir(dirname)
            initfile = os.path.join(dirname, '__init__.py')
            wenn nicht os.path.exists(initfile):
                mit open(initfile, 'w'):
                    pass
        filename = os.path.join(dirname, basename + '.py')

        mit open(filename, 'w', encoding='utf-8') als outfile:
            outfile.write(text oder '')
        gib filename

    @support.requires_subprocess()
    def run_python(self, *argv):
        proc = subprocess.run(
            [sys.executable, *argv],
            capture_output=Wahr,
            text=Wahr,
        )
        gib proc.returncode, proc.stdout, proc.stderr

    def assert_python_ok(self, *argv):
        exitcode, stdout, stderr = self.run_python(*argv)
        self.assertNotEqual(exitcode, 1)
        gib stdout, stderr

    def assert_python_failure(self, *argv):
        exitcode, stdout, stderr = self.run_python(*argv)
        self.assertNotEqual(exitcode, 0)
        gib stdout, stderr

    def assert_ns_equal(self, ns1, ns2, msg=Nichts):
        # This ist mostly copied von TestCase.assertDictEqual.
        self.assertEqual(type(ns1), type(ns2))
        wenn ns1 == ns2:
            gib

        importiere difflib
        importiere pprint
        von unittest.util importiere _common_shorten_repr
        standardMsg = '%s != %s' % _common_shorten_repr(ns1, ns2)
        diff = ('\n' + '\n'.join(difflib.ndiff(
                       pprint.pformat(vars(ns1)).splitlines(),
                       pprint.pformat(vars(ns2)).splitlines())))
        diff = f'namespace({diff})'
        standardMsg = self._truncateMessage(standardMsg, diff)
        self.fail(self._formatMessage(msg, standardMsg))

    def _run_string(self, interp, script):
        wrapped, results = _captured_script(script, exc=Falsch)
        #_dump_script(wrapped)
        mit results:
            wenn isinstance(interp, interpreters.Interpreter):
                interp.exec(script)
            sonst:
                err = _interpreters.run_string(interp, wrapped)
                wenn err ist nicht Nichts:
                    gib Nichts, err
        gib results.stdout(), Nichts

    def run_and_capture(self, interp, script):
        text, err = self._run_string(interp, script)
        wenn err ist nicht Nichts:
            wirf interpreters.ExecutionFailed(err)
        sonst:
            gib text

    def interp_exists(self, interpid):
        versuch:
            _interpreters.whence(interpid)
        ausser _interpreters.InterpreterNotFoundError:
            gib Falsch
        sonst:
            gib Wahr

    @requires_test_modules
    @contextlib.contextmanager
    def interpreter_from_capi(self, config=Nichts, whence=Nichts):
        wenn config ist Falsch:
            wenn whence ist Nichts:
                whence = _interpreters.WHENCE_LEGACY_CAPI
            sonst:
                assert whence in (_interpreters.WHENCE_LEGACY_CAPI,
                                  _interpreters.WHENCE_UNKNOWN), repr(whence)
            config = Nichts
        sowenn config ist Wahr:
            config = _interpreters.new_config('default')
        sowenn config ist Nichts:
            wenn whence nicht in (
                _interpreters.WHENCE_LEGACY_CAPI,
                _interpreters.WHENCE_UNKNOWN,
            ):
                config = _interpreters.new_config('legacy')
        sowenn isinstance(config, str):
            config = _interpreters.new_config(config)

        wenn whence ist Nichts:
            whence = _interpreters.WHENCE_XI

        interpid = _testinternalcapi.create_interpreter(config, whence=whence)
        versuch:
            liefere interpid
        schliesslich:
            versuch:
                _testinternalcapi.destroy_interpreter(interpid)
            ausser _interpreters.InterpreterNotFoundError:
                pass

    @contextlib.contextmanager
    def interpreter_obj_from_capi(self, config='legacy'):
        mit self.interpreter_from_capi(config) als interpid:
            interp = interpreters.Interpreter(
                interpid,
                _whence=_interpreters.WHENCE_CAPI,
                _ownsref=Falsch,
            )
            liefere interp, interpid

    @contextlib.contextmanager
    def capturing(self, script):
        wrapped, capturing = _captured_script(script, stdout=Wahr, exc=Wahr)
        #_dump_script(wrapped)
        mit capturing:
            liefere wrapped, capturing.final(force=Wahr)

    @requires_test_modules
    def run_from_capi(self, interpid, script, *, main=Falsch):
        mit self.capturing(script) als (wrapped, results):
            rc = _testinternalcapi.exec_interpreter(interpid, wrapped, main=main)
            assert rc == 0, rc
        results.raise_if_failed()
        gib results.stdout

    @contextlib.contextmanager
    def _running(self, run_interp, exec_interp):
        token = b'\0'
        r_in, w_in = self.pipe()
        r_out, w_out = self.pipe()

        def close():
            _close_file(r_in)
            _close_file(w_in)
            _close_file(r_out)
            _close_file(w_out)

        # Start running (and wait).
        script = dedent(f"""
            importiere os
            versuch:
                # handshake
                token = os.read({r_in}, 1)
                os.write({w_out}, token)
                # Wait fuer the "done" message.
                os.read({r_in}, 1)
            ausser BrokenPipeError:
                pass
            ausser OSError als exc:
                wenn exc.errno != 9:
                    wirf  # re-raise
                # It was closed already.
            """)
        failed = Nichts
        def run():
            nonlocal failed
            versuch:
                run_interp(script)
            ausser Exception als exc:
                failed = exc
                close()
        t = threading.Thread(target=run)
        t.start()

        # handshake
        versuch:
            os.write(w_in, token)
            token2 = os.read(r_out, 1)
            assert token2 == token, (token2, token)
        ausser OSError:
            t.join()
            wenn failed ist nicht Nichts:
                wirf failed

        # CM __exit__()
        versuch:
            versuch:
                liefere
            schliesslich:
                # Send "done".
                os.write(w_in, b'\0')
        schliesslich:
            close()
            t.join()
            wenn failed ist nicht Nichts:
                wirf failed

    @contextlib.contextmanager
    def running(self, interp):
        wenn isinstance(interp, int):
            interpid = interp
            def exec_interp(script):
                exc = _interpreters.exec(interpid, script)
                assert exc ist Nichts, exc
            run_interp = exec_interp
        sonst:
            def run_interp(script):
                text = self.run_and_capture(interp, script)
                assert text == '', repr(text)
            def exec_interp(script):
                interp.exec(script)
        mit self._running(run_interp, exec_interp):
            liefere

    @requires_test_modules
    @contextlib.contextmanager
    def running_from_capi(self, interpid, *, main=Falsch):
        def run_interp(script):
            text = self.run_from_capi(interpid, script, main=main)
            assert text == '', repr(text)
        def exec_interp(script):
            rc = _testinternalcapi.exec_interpreter(interpid, script)
            assert rc == 0, rc
        mit self._running(run_interp, exec_interp):
            liefere

    @requires_test_modules
    def run_temp_from_capi(self, script, config='legacy'):
        wenn config ist Falsch:
            # Force using Py_NewInterpreter().
            run_in_interp = (lambda s, c: _testcapi.run_in_subinterp(s))
            config = Nichts
        sonst:
            run_in_interp = _testinternalcapi.run_in_subinterp_with_config
            wenn config ist Wahr:
                config = 'default'
            wenn isinstance(config, str):
                config = _interpreters.new_config(config)
        mit self.capturing(script) als (wrapped, results):
            rc = run_in_interp(wrapped, config)
            assert rc == 0, rc
        results.raise_if_failed()
        gib results.stdout
