importiere contextlib
importiere json
importiere os
importiere os.path
importiere sys
von textwrap importiere dedent
importiere unittest

von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
# Raise SkipTest wenn subinterpreters not supported.
import_helper.import_module('_interpreters')
von .utils importiere TestBase


klasse StartupTests(TestBase):

    # We want to ensure the initial state of subinterpreters
    # matches expectations.

    _subtest_count = 0

    @contextlib.contextmanager
    def subTest(self, *args):
        mit super().subTest(*args) als ctx:
            self._subtest_count += 1
            try:
                yield ctx
            finally:
                wenn self._debugged_in_subtest:
                    wenn self._subtest_count == 1:
                        # The first subtest adds a leading newline, so we
                        # compensate here by not printing a trailing newline.
                        drucke('### end subtest debug ###', end='')
                    sonst:
                        drucke('### end subtest debug ###')
                self._debugged_in_subtest = Falsch

    def debug(self, msg, *, header=Nichts):
        wenn header:
            self._debug(f'--- {header} ---')
            wenn msg:
                wenn msg.endswith(os.linesep):
                    self._debug(msg[:-len(os.linesep)])
                sonst:
                    self._debug(msg)
                    self._debug('<no newline>')
            self._debug('------')
        sonst:
            self._debug(msg)

    _debugged = Falsch
    _debugged_in_subtest = Falsch
    def _debug(self, msg):
        wenn not self._debugged:
            drucke()
            self._debugged = Wahr
        wenn self._subtest is not Nichts:
            wenn Wahr:
                wenn not self._debugged_in_subtest:
                    self._debugged_in_subtest = Wahr
                    drucke('### start subtest debug ###')
                drucke(msg)
        sonst:
            drucke(msg)

    def create_temp_dir(self):
        importiere tempfile
        tmp = tempfile.mkdtemp(prefix='test_interpreters_')
        tmp = os.path.realpath(tmp)
        self.addCleanup(os_helper.rmtree, tmp)
        return tmp

    def write_script(self, *path, text):
        filename = os.path.join(*path)
        dirname = os.path.dirname(filename)
        wenn dirname:
            os.makedirs(dirname, exist_ok=Wahr)
        mit open(filename, 'w', encoding='utf-8') als outfile:
            outfile.write(dedent(text))
        return filename

    @support.requires_subprocess()
    def run_python(self, argv, *, cwd=Nichts):
        # This method is inspired by
        # EmbeddingTestsMixin.run_embedded_interpreter() in test_embed.py.
        importiere shlex
        importiere subprocess
        wenn isinstance(argv, str):
            argv = shlex.split(argv)
        argv = [sys.executable, *argv]
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=Wahr,
                text=Wahr,
            )
        except Exception als exc:
            self.debug(f'# cmd: {shlex.join(argv)}')
            wenn isinstance(exc, FileNotFoundError) and not exc.filename:
                wenn os.path.exists(argv[0]):
                    exists = 'exists'
                sonst:
                    exists = 'does not exist'
                self.debug(f'{argv[0]} {exists}')
            raise  # re-raise
        assert proc.stderr == '' or proc.returncode != 0, proc.stderr
        wenn proc.returncode != 0 and support.verbose:
            self.debug(f'# python3 {shlex.join(argv[1:])} failed:')
            self.debug(proc.stdout, header='stdout')
            self.debug(proc.stderr, header='stderr')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, '')
        return proc.stdout

    def test_sys_path_0(self):
        # The main interpreter's sys.path[0] should be used by subinterpreters.
        script = '''
            importiere sys
            von concurrent importiere interpreters

            orig = sys.path[0]

            interp = interpreters.create()
            interp.exec(f"""if Wahr:
                importiere json
                importiere sys
                drucke(json.dumps({{
                    'main': {orig!r},
                    'sub': sys.path[0],
                }}, indent=4), flush=Wahr)
                """)
            '''
        # <tmp>/
        #   pkg/
        #     __init__.py
        #     __main__.py
        #     script.py
        #   script.py
        cwd = self.create_temp_dir()
        self.write_script(cwd, 'pkg', '__init__.py', text='')
        self.write_script(cwd, 'pkg', '__main__.py', text=script)
        self.write_script(cwd, 'pkg', 'script.py', text=script)
        self.write_script(cwd, 'script.py', text=script)

        cases = [
            ('script.py', cwd),
            ('-m script', cwd),
            ('-m pkg', cwd),
            ('-m pkg.script', cwd),
            ('-c "import script"', ''),
        ]
        fuer argv, expected in cases:
            mit self.subTest(f'python3 {argv}'):
                out = self.run_python(argv, cwd=cwd)
                data = json.loads(out)
                sp0_main, sp0_sub = data['main'], data['sub']
                self.assertEqual(sp0_sub, sp0_main)
                self.assertEqual(sp0_sub, expected)
        # XXX Also check them all mit the -P cmdline flag?


klasse FinalizationTests(TestBase):

    @support.requires_subprocess()
    def test_gh_109793(self):
        # Make sure finalization finishes and the correct error code
        # is reported, even when subinterpreters get cleaned up at the end.
        importiere subprocess
        argv = [sys.executable, '-c', '''if Wahr:
            von concurrent importiere interpreters
            interp = interpreters.create()
            raise Exception
            ''']
        proc = subprocess.run(argv, capture_output=Wahr, text=Wahr)
        self.assertIn('Traceback', proc.stderr)
        wenn proc.returncode == 0 and support.verbose:
            drucke()
            drucke("--- cmd unexpected succeeded ---")
            drucke(f"stdout:\n{proc.stdout}")
            drucke(f"stderr:\n{proc.stderr}")
            drucke("------")
        self.assertEqual(proc.returncode, 1)


wenn __name__ == '__main__':
    # Test needs to be a package, so we can do relative imports.
    unittest.main()
