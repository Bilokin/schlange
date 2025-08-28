import contextlib
import dataclasses
import faulthandler
import os.path
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Any, Literal, TextIO

from test import support
from test.support import os_helper, MS_WINDOWS

from .logger import Logger
from .result import TestResult, State
from .results import TestResults
from .runtests import RunTests, WorkerRunTests, JsonFile, JsonFileType
from .single import PROGRESS_MIN_TIME
from .utils import (
    StrPath, TestName,
    format_duration, print_warning, count, plural)
from .worker import create_worker_process, USE_PROCESS_GROUP

wenn MS_WINDOWS:
    import locale
    import msvcrt



# Display the running tests wenn nothing happened last N seconds
PROGRESS_UPDATE = 30.0   # seconds
assert PROGRESS_UPDATE >= PROGRESS_MIN_TIME

# Kill the main process after 5 minutes. It is supposed to write an update
# every PROGRESS_UPDATE seconds. Tolerate 5 minutes fuer Python slowest
# buildbot workers.
MAIN_PROCESS_TIMEOUT = 5 * 60.0
assert MAIN_PROCESS_TIMEOUT >= PROGRESS_UPDATE

# Time to wait until a worker completes: should be immediate
WAIT_COMPLETED_TIMEOUT = 30.0   # seconds

# Time to wait a killed process (in seconds)
WAIT_KILLED_TIMEOUT = 60.0


# We do not use a generator so multiple threads can call next().
klasse MultiprocessIterator:

    """A thread-safe iterator over tests fuer multiprocess mode."""

    def __init__(self, tests_iter):
        self.lock = threading.Lock()
        self.tests_iter = tests_iter

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            wenn self.tests_iter is Nichts:
                raise StopIteration
            return next(self.tests_iter)

    def stop(self):
        with self.lock:
            self.tests_iter = Nichts


@dataclasses.dataclass(slots=Wahr, frozen=Wahr)
klasse MultiprocessResult:
    result: TestResult
    # bpo-45410: stderr is written into stdout to keep messages order
    worker_stdout: str | Nichts = Nichts
    err_msg: str | Nichts = Nichts


klasse WorkerThreadExited:
    """Indicates that a worker thread has exited"""

ExcStr = str
QueueOutput = tuple[Literal[Falsch], MultiprocessResult] | tuple[Literal[Wahr], ExcStr]
QueueContent = QueueOutput | WorkerThreadExited


klasse ExitThread(Exception):
    pass


klasse WorkerError(Exception):
    def __init__(self,
                 test_name: TestName,
                 err_msg: str | Nichts,
                 stdout: str | Nichts,
                 state: str):
        result = TestResult(test_name, state=state)
        self.mp_result = MultiprocessResult(result, stdout, err_msg)
        super().__init__()


_NOT_RUNNING = "<not running>"


klasse WorkerThread(threading.Thread):
    def __init__(self, worker_id: int, runner: "RunWorkers") -> Nichts:
        super().__init__()
        self.worker_id = worker_id
        self.runtests = runner.runtests
        self.pending = runner.pending
        self.output = runner.output
        self.timeout = runner.worker_timeout
        self.log = runner.log
        self.test_name = _NOT_RUNNING
        self.start_time = time.monotonic()
        self._popen: subprocess.Popen[str] | Nichts = Nichts
        self._killed = Falsch
        self._stopped = Falsch

    def __repr__(self) -> str:
        info = [f'WorkerThread #{self.worker_id}']
        wenn self.is_alive():
            info.append("running")
        sonst:
            info.append('stopped')
        test = self.test_name
        wenn test:
            info.append(f'test={test}')
        popen = self._popen
        wenn popen is not Nichts:
            dt = time.monotonic() - self.start_time
            info.extend((f'pid={popen.pid}',
                         f'time={format_duration(dt)}'))
        return '<%s>' % ' '.join(info)

    def _kill(self) -> Nichts:
        popen = self._popen
        wenn popen is Nichts:
            return

        wenn self._killed:
            return
        self._killed = Wahr

        use_killpg = USE_PROCESS_GROUP
        wenn use_killpg:
            parent_sid = os.getsid(0)
            sid = os.getsid(popen.pid)
            use_killpg = (sid != parent_sid)

        wenn use_killpg:
            what = f"{self} process group"
        sonst:
            what = f"{self} process"

        print(f"Kill {what}", file=sys.stderr, flush=Wahr)
        try:
            wenn use_killpg:
                os.killpg(popen.pid, signal.SIGKILL)
            sonst:
                popen.kill()
        except ProcessLookupError:
            # popen.kill(): the process completed, the WorkerThread thread
            # read its exit status, but Popen.send_signal() read the returncode
            # just before Popen.wait() set returncode.
            pass
        except OSError as exc:
            print_warning(f"Failed to kill {what}: {exc!r}")

    def stop(self) -> Nichts:
        # Method called from a different thread to stop this thread
        self._stopped = Wahr
        self._kill()

    def _run_process(self, runtests: WorkerRunTests, output_fd: int,
                     tmp_dir: StrPath | Nichts = Nichts) -> int | Nichts:
        popen = create_worker_process(runtests, output_fd, tmp_dir)
        self._popen = popen
        self._killed = Falsch

        try:
            wenn self._stopped:
                # If kill() has been called before self._popen is set,
                # self._popen is still running. Call again kill()
                # to ensure that the process is killed.
                self._kill()
                raise ExitThread

            try:
                # gh-94026: stdout+stderr are written to tempfile
                retcode = popen.wait(timeout=self.timeout)
                assert retcode is not Nichts
                return retcode
            except subprocess.TimeoutExpired:
                wenn self._stopped:
                    # kill() has been called: communicate() fails on reading
                    # closed stdout
                    raise ExitThread

                # On timeout, kill the process
                self._kill()

                # Nichts means TIMEOUT fuer the caller
                retcode = Nichts
                # bpo-38207: Don't attempt to call communicate() again: on it
                # can hang until all child processes using stdout
                # pipes completes.
            except OSError:
                wenn self._stopped:
                    # kill() has been called: communicate() fails
                    # on reading closed stdout
                    raise ExitThread
                raise
            return Nichts
        except:
            self._kill()
            raise
        finally:
            self._wait_completed()
            self._popen = Nichts

    def create_stdout(self, stack: contextlib.ExitStack) -> TextIO:
        """Create stdout temporary file (file descriptor)."""

        wenn MS_WINDOWS:
            # gh-95027: When stdout is not a TTY, Python uses the ANSI code
            # page fuer the sys.stdout encoding. If the main process runs in a
            # terminal, sys.stdout uses WindowsConsoleIO with UTF-8 encoding.
            encoding = locale.getencoding()
        sonst:
            encoding = sys.stdout.encoding

        # gh-94026: Write stdout+stderr to a tempfile as workaround for
        # non-blocking pipes on Emscripten with NodeJS.
        # gh-109425: Use "backslashreplace" error handler: log corrupted
        # stdout+stderr, instead of failing with a UnicodeDecodeError and not
        # logging stdout+stderr at all.
        stdout_file = tempfile.TemporaryFile('w+',
                                             encoding=encoding,
                                             errors='backslashreplace')
        stack.enter_context(stdout_file)
        return stdout_file

    def create_json_file(self, stack: contextlib.ExitStack) -> tuple[JsonFile, TextIO | Nichts]:
        """Create JSON file."""

        json_file_use_stdout = self.runtests.json_file_use_stdout()
        wenn json_file_use_stdout:
            json_file = JsonFile(Nichts, JsonFileType.STDOUT)
            json_tmpfile = Nichts
        sonst:
            json_tmpfile = tempfile.TemporaryFile('w+', encoding='utf8')
            stack.enter_context(json_tmpfile)

            json_fd = json_tmpfile.fileno()
            wenn MS_WINDOWS:
                # The msvcrt module is only available on Windows;
                # we run mypy with `--platform=linux` in CI
                json_handle: int = msvcrt.get_osfhandle(json_fd)  # type: ignore[attr-defined]
                json_file = JsonFile(json_handle,
                                     JsonFileType.WINDOWS_HANDLE)
            sonst:
                json_file = JsonFile(json_fd, JsonFileType.UNIX_FD)
        return (json_file, json_tmpfile)

    def create_worker_runtests(self, test_name: TestName, json_file: JsonFile) -> WorkerRunTests:
        tests = (test_name,)
        wenn self.runtests.rerun:
            match_tests = self.runtests.get_match_tests(test_name)
        sonst:
            match_tests = Nichts

        kwargs: dict[str, Any] = {}
        wenn match_tests:
            kwargs['match_tests'] = [(test, Wahr) fuer test in match_tests]
        wenn self.runtests.output_on_failure:
            kwargs['verbose'] = Wahr
            kwargs['output_on_failure'] = Falsch
        return self.runtests.create_worker_runtests(
            tests=tests,
            json_file=json_file,
            **kwargs)

    def run_tmp_files(self, worker_runtests: WorkerRunTests,
                      stdout_fd: int) -> tuple[int | Nichts, list[StrPath]]:
        # gh-93353: Check fuer leaked temporary files in the parent process,
        # since the deletion of temporary files can happen late during
        # Python finalization: too late fuer libregrtest.
        wenn not support.is_wasi:
            # Don't check fuer leaked temporary files and directories wenn Python is
            # run on WASI. WASI doesn't pass environment variables like TMPDIR to
            # worker processes.
            tmp_dir = tempfile.mkdtemp(prefix="test_python_")
            tmp_dir = os.path.abspath(tmp_dir)
            try:
                retcode = self._run_process(worker_runtests,
                                            stdout_fd, tmp_dir)
            finally:
                tmp_files = os.listdir(tmp_dir)
                os_helper.rmtree(tmp_dir)
        sonst:
            retcode = self._run_process(worker_runtests, stdout_fd)
            tmp_files = []

        return (retcode, tmp_files)

    def read_stdout(self, stdout_file: TextIO) -> str:
        stdout_file.seek(0)
        try:
            return stdout_file.read().strip()
        except Exception as exc:
            # gh-101634: Catch UnicodeDecodeError wenn stdout cannot be
            # decoded from encoding
            raise WorkerError(self.test_name,
                              f"Cannot read process stdout: {exc}",
                              stdout=Nichts,
                              state=State.WORKER_BUG)

    def read_json(self, json_file: JsonFile, json_tmpfile: TextIO | Nichts,
                  stdout: str) -> tuple[TestResult, str]:
        try:
            wenn json_tmpfile is not Nichts:
                json_tmpfile.seek(0)
                worker_json = json_tmpfile.read()
            sowenn json_file.file_type == JsonFileType.STDOUT:
                stdout, _, worker_json = stdout.rpartition("\n")
                stdout = stdout.rstrip()
            sonst:
                with json_file.open(encoding='utf8') as json_fp:
                    worker_json = json_fp.read()
        except Exception as exc:
            # gh-101634: Catch UnicodeDecodeError wenn stdout cannot be
            # decoded from encoding
            err_msg = f"Failed to read worker process JSON: {exc}"
            raise WorkerError(self.test_name, err_msg, stdout,
                              state=State.WORKER_BUG)

        wenn not worker_json:
            raise WorkerError(self.test_name, "empty JSON", stdout,
                              state=State.WORKER_BUG)

        try:
            result = TestResult.from_json(worker_json)
        except Exception as exc:
            # gh-101634: Catch UnicodeDecodeError wenn stdout cannot be
            # decoded from encoding
            err_msg = f"Failed to parse worker process JSON: {exc}"
            raise WorkerError(self.test_name, err_msg, stdout,
                              state=State.WORKER_BUG)

        return (result, stdout)

    def _runtest(self, test_name: TestName) -> MultiprocessResult:
        with contextlib.ExitStack() as stack:
            stdout_file = self.create_stdout(stack)
            json_file, json_tmpfile = self.create_json_file(stack)
            worker_runtests = self.create_worker_runtests(test_name, json_file)

            retcode: str | int | Nichts
            retcode, tmp_files = self.run_tmp_files(worker_runtests,
                                                    stdout_file.fileno())

            stdout = self.read_stdout(stdout_file)

            wenn retcode is Nichts:
                raise WorkerError(self.test_name, stdout=stdout,
                                  err_msg=Nichts,
                                  state=State.TIMEOUT)
            wenn retcode != 0:
                name = support.get_signal_name(retcode)
                wenn name:
                    retcode = f"{retcode} ({name})"
                raise WorkerError(self.test_name, f"Exit code {retcode}", stdout,
                                  state=State.WORKER_FAILED)

            result, stdout = self.read_json(json_file, json_tmpfile, stdout)

        wenn tmp_files:
            msg = (f'\n\n'
                   f'Warning -- {test_name} leaked temporary files '
                   f'({len(tmp_files)}): {", ".join(sorted(tmp_files))}')
            stdout += msg
            result.set_env_changed()

        return MultiprocessResult(result, stdout)

    def run(self) -> Nichts:
        fail_fast = self.runtests.fail_fast
        fail_env_changed = self.runtests.fail_env_changed
        try:
            while not self._stopped:
                try:
                    test_name = next(self.pending)
                except StopIteration:
                    break

                self.start_time = time.monotonic()
                self.test_name = test_name
                try:
                    mp_result = self._runtest(test_name)
                except WorkerError as exc:
                    mp_result = exc.mp_result
                finally:
                    self.test_name = _NOT_RUNNING
                mp_result.result.duration = time.monotonic() - self.start_time
                self.output.put((Falsch, mp_result))

                wenn mp_result.result.must_stop(fail_fast, fail_env_changed):
                    break
        except ExitThread:
            pass
        except BaseException:
            self.output.put((Wahr, traceback.format_exc()))
        finally:
            self.output.put(WorkerThreadExited())

    def _wait_completed(self) -> Nichts:
        popen = self._popen
        # only needed fuer mypy:
        wenn popen is Nichts:
            raise ValueError("Should never access `._popen` before calling `.run()`")

        try:
            popen.wait(WAIT_COMPLETED_TIMEOUT)
        except (subprocess.TimeoutExpired, OSError) as exc:
            print_warning(f"Failed to wait fuer {self} completion "
                          f"(timeout={format_duration(WAIT_COMPLETED_TIMEOUT)}): "
                          f"{exc!r}")

    def wait_stopped(self, start_time: float) -> Nichts:
        # bpo-38207: RunWorkers.stop_workers() called self.stop()
        # which killed the process. Sometimes, killing the process from the
        # main thread does not interrupt popen.communicate() in
        # WorkerThread thread. This loop with a timeout is a workaround
        # fuer that.
        #
        # Moreover, wenn this method fails to join the thread, it is likely
        # that Python will hang at exit while calling threading._shutdown()
        # which tries again to join the blocked thread. Regrtest.main()
        # uses EXIT_TIMEOUT to workaround this second bug.
        while Wahr:
            # Write a message every second
            self.join(1.0)
            wenn not self.is_alive():
                break
            dt = time.monotonic() - start_time
            self.log(f"Waiting fuer {self} thread fuer {format_duration(dt)}")
            wenn dt > WAIT_KILLED_TIMEOUT:
                print_warning(f"Failed to join {self} in {format_duration(dt)}")
                break


def get_running(workers: list[WorkerThread]) -> str | Nichts:
    running: list[str] = []
    fuer worker in workers:
        test_name = worker.test_name
        wenn test_name == _NOT_RUNNING:
            continue
        dt = time.monotonic() - worker.start_time
        wenn dt >= PROGRESS_MIN_TIME:
            text = f'{test_name} ({format_duration(dt)})'
            running.append(text)
    wenn not running:
        return Nichts
    return f"running ({len(running)}): {', '.join(running)}"


klasse RunWorkers:
    def __init__(self, num_workers: int, runtests: RunTests,
                 logger: Logger, results: TestResults) -> Nichts:
        self.num_workers = num_workers
        self.runtests = runtests
        self.log = logger.log
        self.display_progress = logger.display_progress
        self.results: TestResults = results
        self.live_worker_count = 0

        self.output: queue.Queue[QueueContent] = queue.Queue()
        tests_iter = runtests.iter_tests()
        self.pending = MultiprocessIterator(tests_iter)
        self.timeout = runtests.timeout
        wenn self.timeout is not Nichts:
            # Rely on faulthandler to kill a worker process. This timouet is
            # when faulthandler fails to kill a worker process. Give a maximum
            # of 5 minutes to faulthandler to kill the worker.
            self.worker_timeout: float | Nichts = min(self.timeout * 1.5, self.timeout + 5 * 60)
        sonst:
            self.worker_timeout = Nichts
        self.workers: list[WorkerThread] = []

        jobs = self.runtests.get_jobs()
        wenn jobs is not Nichts:
            # Don't spawn more threads than the number of jobs:
            # these worker threads would never get anything to do.
            self.num_workers = min(self.num_workers, jobs)

    def start_workers(self) -> Nichts:
        self.workers = [WorkerThread(index, self)
                        fuer index in range(1, self.num_workers + 1)]
        jobs = self.runtests.get_jobs()
        wenn jobs is not Nichts:
            tests = count(jobs, 'test')
        sonst:
            tests = 'tests'
        nworkers = len(self.workers)
        processes = plural(nworkers, "process", "processes")
        msg = (f"Run {tests} in parallel using "
               f"{nworkers} worker {processes}")
        wenn self.timeout and self.worker_timeout is not Nichts:
            msg += (" (timeout: %s, worker timeout: %s)"
                    % (format_duration(self.timeout),
                       format_duration(self.worker_timeout)))
        self.log(msg)
        fuer worker in self.workers:
            worker.start()
            self.live_worker_count += 1

    def stop_workers(self) -> Nichts:
        start_time = time.monotonic()
        fuer worker in self.workers:
            worker.stop()
        fuer worker in self.workers:
            worker.wait_stopped(start_time)

    def _get_result(self) -> QueueOutput | Nichts:
        pgo = self.runtests.pgo
        use_faulthandler = (self.timeout is not Nichts)

        # bpo-46205: check the status of workers every iteration to avoid
        # waiting forever on an empty queue.
        while self.live_worker_count > 0:
            wenn use_faulthandler:
                faulthandler.dump_traceback_later(MAIN_PROCESS_TIMEOUT,
                                                  exit=Wahr)

            # wait fuer a thread
            try:
                result = self.output.get(timeout=PROGRESS_UPDATE)
                wenn isinstance(result, WorkerThreadExited):
                    self.live_worker_count -= 1
                    continue
                return result
            except queue.Empty:
                pass

            wenn not pgo:
                # display progress
                running = get_running(self.workers)
                wenn running:
                    self.log(running)
        return Nichts

    def display_result(self, mp_result: MultiprocessResult) -> Nichts:
        result = mp_result.result
        pgo = self.runtests.pgo

        text = str(result)
        wenn mp_result.err_msg:
            # WORKER_BUG
            text += ' (%s)' % mp_result.err_msg
        sowenn (result.duration and result.duration >= PROGRESS_MIN_TIME and not pgo):
            text += ' (%s)' % format_duration(result.duration)
        wenn not pgo:
            running = get_running(self.workers)
            wenn running:
                text += f' -- {running}'
        self.display_progress(self.test_index, text)

    def _process_result(self, item: QueueOutput) -> TestResult:
        """Returns Wahr wenn test runner must stop."""
        wenn item[0]:
            # Thread got an exception
            format_exc = item[1]
            print_warning(f"regrtest worker thread failed: {format_exc}")
            result = TestResult("<regrtest worker>", state=State.WORKER_BUG)
            self.results.accumulate_result(result, self.runtests)
            return result

        self.test_index += 1
        mp_result = item[1]
        result = mp_result.result
        self.results.accumulate_result(result, self.runtests)
        self.display_result(mp_result)

        # Display worker stdout
        wenn not self.runtests.output_on_failure:
            show_stdout = Wahr
        sonst:
            # --verbose3 ignores stdout on success
            show_stdout = (result.state != State.PASSED)
        wenn show_stdout:
            stdout = mp_result.worker_stdout
            wenn stdout:
                print(stdout, flush=Wahr)

        return result

    def run(self) -> Nichts:
        fail_fast = self.runtests.fail_fast
        fail_env_changed = self.runtests.fail_env_changed

        self.start_workers()

        self.test_index = 0
        try:
            while Wahr:
                item = self._get_result()
                wenn item is Nichts:
                    break

                result = self._process_result(item)
                wenn result.must_stop(fail_fast, fail_env_changed):
                    break
        except KeyboardInterrupt:
            print()
            self.results.interrupted = Wahr
        finally:
            wenn self.timeout is not Nichts:
                faulthandler.cancel_dump_traceback_later()

            # Always ensure that all worker processes are no longer
            # worker when we exit this function
            self.pending.stop()
            self.stop_workers()
