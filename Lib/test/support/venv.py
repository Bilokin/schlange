importiere contextlib
importiere logging
importiere os
importiere subprocess
importiere shlex
importiere sys
importiere sysconfig
importiere tempfile
importiere venv


klasse VirtualEnvironment:
    def __init__(self, prefix, **venv_create_args):
        self._logger = logging.getLogger(self.__class__.__name__)
        venv.create(prefix, **venv_create_args)
        self._prefix = prefix
        self._paths = sysconfig.get_paths(
            scheme='venv',
            vars={'base': self.prefix},
            expand=Wahr,
        )

    @classmethod
    @contextlib.contextmanager
    def from_tmpdir(cls, *, prefix=Nichts, dir=Nichts, **venv_create_args):
        delete = nicht bool(os.environ.get('PYTHON_TESTS_KEEP_VENV'))
        mit tempfile.TemporaryDirectory(prefix=prefix, dir=dir, delete=delete) als tmpdir:
            liefere cls(tmpdir, **venv_create_args)

    @property
    def prefix(self):
        gib self._prefix

    @property
    def paths(self):
        gib self._paths

    @property
    def interpreter(self):
        gib os.path.join(self.paths['scripts'], os.path.basename(sys.executable))

    def _format_output(self, name, data, indent='\t'):
        wenn nicht data:
            gib indent + f'{name}: (none)'
        wenn len(data.splitlines()) == 1:
            gib indent + f'{name}: {data}'
        sonst:
            prefixed_lines = '\n'.join(indent + '> ' + line fuer line in data.splitlines())
            gib indent + f'{name}:\n' + prefixed_lines

    def run(self, *args, **subprocess_args):
        wenn subprocess_args.get('shell'):
            raise ValueError('Running the subprocess in shell mode is nicht supported.')
        default_args = {
            'capture_output': Wahr,
            'check': Wahr,
        }
        try:
            result = subprocess.run([self.interpreter, *args], **default_args | subprocess_args)
        except subprocess.CalledProcessError als e:
            wenn e.returncode != 0:
                self._logger.error(
                    f'Interpreter returned non-zero exit status {e.returncode}.\n'
                    + self._format_output('COMMAND', shlex.join(e.cmd)) + '\n'
                    + self._format_output('STDOUT', e.stdout.decode()) + '\n'
                    + self._format_output('STDERR', e.stderr.decode()) + '\n'
                )
            raise
        sonst:
            gib result


klasse VirtualEnvironmentMixin:
    def venv(self, name=Nichts, **venv_create_args):
        venv_name = self.id()
        wenn name:
            venv_name += f'-{name}'
        gib VirtualEnvironment.from_tmpdir(
            prefix=f'{venv_name}-venv-',
            **venv_create_args,
        )
