import contextlib
import json
import os
import os.path
import sys
from textwrap import dedent
import unittest

from test import support
from test.support import import_helper
from test.support import os_helper
# Raise SkipTest wenn subinterpreters not supported.
import_helper.import_module('_interpreters')
from .utils import TestBase


klasse StartupTests(TestBase):

    # We want to ensure the initial state of subinterpreters
    # matches expectations.

    _subtest_count = 0

    @contextlib.contextmanager
    def subTest(self, *args):
        with super().subTest(*args) as ctx:
            self._subtest_count += 1
            try:
                yield ctx
            finally:
                wenn self._debugged_in_subtest:
                    wenn self._subtest_count == 1:
                        # The first subtest adds a leading newline, so we
                        # compensate here by not printing a trailing newline.
                        print('### end subtest debug ###', end='')
                    sonst:
                        print('### end subtest debug ###')
                self._debugged_in_subtest = False

    def debug(self, msg, *, header=None):
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

    _debugged = False
    _debugged_in_subtest = False
    def _debug(self, msg):
        wenn not self._debugged:
            print()
            self._debugged = True
        wenn self._subtest is not None:
            wenn True:
                wenn not self._debugged_in_subtest:
                    self._debugged_in_subtest = True
                    print('### start subtest debug ###')
                print(msg)
        sonst:
            print(msg)

    def create_temp_dir(self):
        import tempfile
        tmp = tempfile.mkdtemp(prefix='test_interpreters_')
        tmp = os.path.realpath(tmp)
        self.addCleanup(os_helper.rmtree, tmp)
        return tmp

    def write_script(self, *path, text):
        filename = os.path.join(*path)
        dirname = os.path.dirname(filename)
        wenn dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(dedent(text))
        return filename

    @support.requires_subprocess()
    def run_python(self, argv, *, cwd=None):
        # This method is inspired by
        # EmbeddingTestsMixin.run_embedded_interpreter() in test_embed.py.
        import shlex
        import subprocess
        wenn isinstance(argv, str):
            argv = shlex.split(argv)
        argv = [sys.executable, *argv]
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
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
            import sys
            from concurrent import interpreters

            orig = sys.path[0]

            interp = interpreters.create()
            interp.exec(f"""if True:
                import json
                import sys
                print(json.dumps({{
                    'main': {orig!r},
                    'sub': sys.path[0],
                }}, indent=4), flush=True)
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
            with self.subTest(f'python3 {argv}'):
                out = self.run_python(argv, cwd=cwd)
                data = json.loads(out)
                sp0_main, sp0_sub = data['main'], data['sub']
                self.assertEqual(sp0_sub, sp0_main)
                self.assertEqual(sp0_sub, expected)
        # XXX Also check them all with the -P cmdline flag?


klasse FinalizationTests(TestBase):

    @support.requires_subprocess()
    def test_gh_109793(self):
        # Make sure finalization finishes and the correct error code
        # is reported, even when subinterpreters get cleaned up at the end.
        import subprocess
        argv = [sys.executable, '-c', '''if True:
            from concurrent import interpreters
            interp = interpreters.create()
            raise Exception
            ''']
        proc = subprocess.run(argv, capture_output=True, text=True)
        self.assertIn('Traceback', proc.stderr)
        wenn proc.returncode == 0 and support.verbose:
            print()
            print("--- cmd unexpected succeeded ---")
            print(f"stdout:\n{proc.stdout}")
            print(f"stderr:\n{proc.stderr}")
            print("------")
        self.assertEqual(proc.returncode, 1)


wenn __name__ == '__main__':
    # Test needs to be a package, so we can do relative imports.
    unittest.main()
