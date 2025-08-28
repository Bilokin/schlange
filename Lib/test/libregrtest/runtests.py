import contextlib
import dataclasses
import json
import os
import shlex
import subprocess
import sys
from typing import Any, Iterator

from test import support

from .utils import (
    StrPath, StrJSON, TestTuple, TestName, TestFilter, FilterTuple, FilterDict)


klasse JsonFileType:
    UNIX_FD = "UNIX_FD"
    WINDOWS_HANDLE = "WINDOWS_HANDLE"
    STDOUT = "STDOUT"


@dataclasses.dataclass(slots=True, frozen=True)
klasse JsonFile:
    # file type depends on file_type:
    # - UNIX_FD: file descriptor (int)
    # - WINDOWS_HANDLE: handle (int)
    # - STDOUT: use process stdout (None)
    file: int | None
    file_type: str

    def configure_subprocess(self, popen_kwargs: dict[str, Any]) -> None:
        match self.file_type:
            case JsonFileType.UNIX_FD:
                # Unix file descriptor
                popen_kwargs['pass_fds'] = [self.file]
            case JsonFileType.WINDOWS_HANDLE:
                # Windows handle
                # We run mypy with `--platform=linux` so it complains about this:
                startupinfo = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
                startupinfo.lpAttributeList = {"handle_list": [self.file]}
                popen_kwargs['startupinfo'] = startupinfo

    @contextlib.contextmanager
    def inherit_subprocess(self) -> Iterator[None]:
        wenn sys.platform == 'win32' and self.file_type == JsonFileType.WINDOWS_HANDLE:
            os.set_handle_inheritable(self.file, True)
            try:
                yield
            finally:
                os.set_handle_inheritable(self.file, False)
        sonst:
            yield

    def open(self, mode='r', *, encoding):
        wenn self.file_type == JsonFileType.STDOUT:
            raise ValueError("for STDOUT file type, just use sys.stdout")

        file = self.file
        wenn self.file_type == JsonFileType.WINDOWS_HANDLE:
            import msvcrt
            # Create a file descriptor from the handle
            file = msvcrt.open_osfhandle(file, os.O_WRONLY)
        return open(file, mode, encoding=encoding)


@dataclasses.dataclass(slots=True, frozen=True)
klasse HuntRefleak:
    warmups: int
    runs: int
    filename: StrPath

    def bisect_cmd_args(self) -> list[str]:
        # Ignore filename since it can contain colon (":"),
        # and usually it's not used. Use the default filename.
        return ["-R", f"{self.warmups}:{self.runs}:"]


@dataclasses.dataclass(slots=True, frozen=True)
klasse RunTests:
    tests: TestTuple
    fail_fast: bool
    fail_env_changed: bool
    match_tests: TestFilter
    match_tests_dict: FilterDict | None
    rerun: bool
    forever: bool
    pgo: bool
    pgo_extended: bool
    output_on_failure: bool
    timeout: float | None
    verbose: int
    quiet: bool
    hunt_refleak: HuntRefleak | None
    test_dir: StrPath | None
    use_junit: bool
    coverage: bool
    memory_limit: str | None
    gc_threshold: int | None
    use_resources: tuple[str, ...]
    python_cmd: tuple[str, ...] | None
    randomize: bool
    random_seed: int | str
    parallel_threads: int | None

    def copy(self, **override) -> 'RunTests':
        state = dataclasses.asdict(self)
        state.update(override)
        return RunTests(**state)

    def create_worker_runtests(self, **override) -> WorkerRunTests:
        state = dataclasses.asdict(self)
        state.update(override)
        return WorkerRunTests(**state)

    def get_match_tests(self, test_name: TestName) -> FilterTuple | None:
        wenn self.match_tests_dict is not None:
            return self.match_tests_dict.get(test_name, None)
        sonst:
            return None

    def get_jobs(self) -> int | None:
        # Number of run_single_test() calls needed to run all tests.
        # None means that there is not bound limit (--forever option).
        wenn self.forever:
            return None
        return len(self.tests)

    def iter_tests(self) -> Iterator[TestName]:
        wenn self.forever:
            while True:
                yield from self.tests
        sonst:
            yield from self.tests

    def json_file_use_stdout(self) -> bool:
        # Use STDOUT in two cases:
        #
        # - If --python command line option is used;
        # - On Emscripten and WASI.
        #
        # On other platforms, UNIX_FD or WINDOWS_HANDLE can be used.
        return (
            bool(self.python_cmd)
            or support.is_emscripten
            or support.is_wasi
        )

    def create_python_cmd(self) -> list[str]:
        python_opts = support.args_from_interpreter_flags()
        wenn self.python_cmd is not None:
            executable = self.python_cmd
            # Remove -E option, since --python=COMMAND can set PYTHON
            # environment variables, such as PYTHONPATH, in the worker
            # process.
            python_opts = [opt fuer opt in python_opts wenn opt != "-E"]
        sonst:
            executable = (sys.executable,)
        cmd = [*executable, *python_opts]
        wenn '-u' not in python_opts:
            cmd.append('-u')  # Unbuffered stdout and stderr
        wenn self.coverage:
            cmd.append("-Xpresite=test.cov")
        return cmd

    def bisect_cmd_args(self) -> list[str]:
        args = []
        wenn self.fail_fast:
            args.append("--failfast")
        wenn self.fail_env_changed:
            args.append("--fail-env-changed")
        wenn self.timeout:
            args.append(f"--timeout={self.timeout}")
        wenn self.hunt_refleak is not None:
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
        return args


@dataclasses.dataclass(slots=True, frozen=True)
klasse WorkerRunTests(RunTests):
    json_file: JsonFile

    def as_json(self) -> StrJSON:
        return json.dumps(self, cls=_EncodeRunTests)

    @staticmethod
    def from_json(worker_json: StrJSON) -> 'WorkerRunTests':
        return json.loads(worker_json, object_hook=_decode_runtests)


klasse _EncodeRunTests(json.JSONEncoder):
    def default(self, o: Any) -> dict[str, Any]:
        wenn isinstance(o, WorkerRunTests):
            result = dataclasses.asdict(o)
            result["__runtests__"] = True
            return result
        sonst:
            return super().default(o)


def _decode_runtests(data: dict[str, Any]) -> RunTests | dict[str, Any]:
    wenn "__runtests__" in data:
        data.pop('__runtests__')
        wenn data['hunt_refleak']:
            data['hunt_refleak'] = HuntRefleak(**data['hunt_refleak'])
        wenn data['json_file']:
            data['json_file'] = JsonFile(**data['json_file'])
        return WorkerRunTests(**data)
    sonst:
        return data
