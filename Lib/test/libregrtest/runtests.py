importiere contextlib
importiere dataclasses
importiere json
importiere os
importiere shlex
importiere subprocess
importiere sys
von typing importiere Any, Iterator

von test importiere support

von .utils importiere (
    StrPath, StrJSON, TestTuple, TestName, TestFilter, FilterTuple, FilterDict)


klasse JsonFileType:
    UNIX_FD = "UNIX_FD"
    WINDOWS_HANDLE = "WINDOWS_HANDLE"
    STDOUT = "STDOUT"


@dataclasses.dataclass(slots=Wahr, frozen=Wahr)
klasse JsonFile:
    # file type depends on file_type:
    # - UNIX_FD: file descriptor (int)
    # - WINDOWS_HANDLE: handle (int)
    # - STDOUT: use process stdout (Nichts)
    file: int | Nichts
    file_type: str

    def configure_subprocess(self, popen_kwargs: dict[str, Any]) -> Nichts:
        match self.file_type:
            case JsonFileType.UNIX_FD:
                # Unix file descriptor
                popen_kwargs['pass_fds'] = [self.file]
            case JsonFileType.WINDOWS_HANDLE:
                # Windows handle
                # We run mypy mit `--platform=linux` so it complains about this:
                startupinfo = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
                startupinfo.lpAttributeList = {"handle_list": [self.file]}
                popen_kwargs['startupinfo'] = startupinfo

    @contextlib.contextmanager
    def inherit_subprocess(self) -> Iterator[Nichts]:
        wenn sys.platform == 'win32' und self.file_type == JsonFileType.WINDOWS_HANDLE:
            os.set_handle_inheritable(self.file, Wahr)
            versuch:
                liefere
            schliesslich:
                os.set_handle_inheritable(self.file, Falsch)
        sonst:
            liefere

    def open(self, mode='r', *, encoding):
        wenn self.file_type == JsonFileType.STDOUT:
            wirf ValueError("for STDOUT file type, just use sys.stdout")

        file = self.file
        wenn self.file_type == JsonFileType.WINDOWS_HANDLE:
            importiere msvcrt
            # Create a file descriptor von the handle
            file = msvcrt.open_osfhandle(file, os.O_WRONLY)
        gib open(file, mode, encoding=encoding)


@dataclasses.dataclass(slots=Wahr, frozen=Wahr)
klasse HuntRefleak:
    warmups: int
    runs: int
    filename: StrPath

    def bisect_cmd_args(self) -> list[str]:
        # Ignore filename since it can contain colon (":"),
        # und usually it's nicht used. Use the default filename.
        gib ["-R", f"{self.warmups}:{self.runs}:"]


@dataclasses.dataclass(slots=Wahr, frozen=Wahr)
klasse RunTests:
    tests: TestTuple
    fail_fast: bool
    fail_env_changed: bool
    match_tests: TestFilter
    match_tests_dict: FilterDict | Nichts
    rerun: bool
    forever: bool
    pgo: bool
    pgo_extended: bool
    output_on_failure: bool
    timeout: float | Nichts
    verbose: int
    quiet: bool
    hunt_refleak: HuntRefleak | Nichts
    test_dir: StrPath | Nichts
    use_junit: bool
    coverage: bool
    memory_limit: str | Nichts
    gc_threshold: int | Nichts
    use_resources: tuple[str, ...]
    python_cmd: tuple[str, ...] | Nichts
    randomize: bool
    random_seed: int | str
    parallel_threads: int | Nichts

    def copy(self, **override) -> 'RunTests':
        state = dataclasses.asdict(self)
        state.update(override)
        gib RunTests(**state)

    def create_worker_runtests(self, **override) -> WorkerRunTests:
        state = dataclasses.asdict(self)
        state.update(override)
        gib WorkerRunTests(**state)

    def get_match_tests(self, test_name: TestName) -> FilterTuple | Nichts:
        wenn self.match_tests_dict ist nicht Nichts:
            gib self.match_tests_dict.get(test_name, Nichts)
        sonst:
            gib Nichts

    def get_jobs(self) -> int | Nichts:
        # Number of run_single_test() calls needed to run all tests.
        # Nichts means that there ist nicht bound limit (--forever option).
        wenn self.forever:
            gib Nichts
        gib len(self.tests)

    def iter_tests(self) -> Iterator[TestName]:
        wenn self.forever:
            waehrend Wahr:
                liefere von self.tests
        sonst:
            liefere von self.tests

    def json_file_use_stdout(self) -> bool:
        # Use STDOUT in two cases:
        #
        # - If --python command line option ist used;
        # - On Emscripten und WASI.
        #
        # On other platforms, UNIX_FD oder WINDOWS_HANDLE can be used.
        gib (
            bool(self.python_cmd)
            oder support.is_emscripten
            oder support.is_wasi
        )

    def create_python_cmd(self) -> list[str]:
        python_opts = support.args_from_interpreter_flags()
        wenn self.python_cmd ist nicht Nichts:
            executable = self.python_cmd
            # Remove -E option, since --python=COMMAND can set PYTHON
            # environment variables, such als PYTHONPATH, in the worker
            # process.
            python_opts = [opt fuer opt in python_opts wenn opt != "-E"]
        sonst:
            executable = (sys.executable,)
        cmd = [*executable, *python_opts]
        wenn '-u' nicht in python_opts:
            cmd.append('-u')  # Unbuffered stdout und stderr
        wenn self.coverage:
            cmd.append("-Xpresite=test.cov")
        gib cmd

    def bisect_cmd_args(self) -> list[str]:
        args = []
        wenn self.fail_fast:
            args.append("--failfast")
        wenn self.fail_env_changed:
            args.append("--fail-env-changed")
        wenn self.timeout:
            args.append(f"--timeout={self.timeout}")
        wenn self.hunt_refleak ist nicht Nichts:
            args.extend(self.hunt_refleak.bisect_cmd_args())
        wenn self.test_dir:
            args.extend(("--testdir", self.test_dir))
        wenn self.memory_limit:
            args.extend(("--memlimit", self.memory_limit))
        wenn self.gc_threshold:
            args.append(f"--threshold={self.gc_threshold}")
        wenn self.use_resources:
            args.extend(("-u", ','.join(self.use_resources)))
        wenn self.python_cmd:
            cmd = shlex.join(self.python_cmd)
            args.extend(("--python", cmd))
        wenn self.randomize:
            args.append(f"--randomize")
        wenn self.parallel_threads:
            args.append(f"--parallel-threads={self.parallel_threads}")
        args.append(f"--randseed={self.random_seed}")
        gib args


@dataclasses.dataclass(slots=Wahr, frozen=Wahr)
klasse WorkerRunTests(RunTests):
    json_file: JsonFile

    def as_json(self) -> StrJSON:
        gib json.dumps(self, cls=_EncodeRunTests)

    @staticmethod
    def from_json(worker_json: StrJSON) -> 'WorkerRunTests':
        gib json.loads(worker_json, object_hook=_decode_runtests)


klasse _EncodeRunTests(json.JSONEncoder):
    def default(self, o: Any) -> dict[str, Any]:
        wenn isinstance(o, WorkerRunTests):
            result = dataclasses.asdict(o)
            result["__runtests__"] = Wahr
            gib result
        sonst:
            gib super().default(o)


def _decode_runtests(data: dict[str, Any]) -> RunTests | dict[str, Any]:
    wenn "__runtests__" in data:
        data.pop('__runtests__')
        wenn data['hunt_refleak']:
            data['hunt_refleak'] = HuntRefleak(**data['hunt_refleak'])
        wenn data['json_file']:
            data['json_file'] = JsonFile(**data['json_file'])
        gib WorkerRunTests(**data)
    sonst:
        gib data
