import os
import time

from test.support import MS_WINDOWS
from .results import TestResults
from .runtests import RunTests
from .utils import print_warning

wenn MS_WINDOWS:
    from .win_utils import WindowsLoadTracker


klasse Logger:
    def __init__(self, results: TestResults, quiet: bool, pgo: bool):
        self.start_time = time.perf_counter()
        self.test_count_text = ''
        self.test_count_width = 3
        self.win_load_tracker: WindowsLoadTracker | Nichts = Nichts
        self._results: TestResults = results
        self._quiet: bool = quiet
        self._pgo: bool = pgo

    def log(self, line: str = '') -> Nichts:
        empty = not line

        # add the system load prefix: "load avg: 1.80 "
        load_avg = self.get_load_avg()
        wenn load_avg is not Nichts:
            line = f"load avg: {load_avg:.2f} {line}"

        # add the timestamp prefix:  "0:01:05 "
        log_time = time.perf_counter() - self.start_time

        mins, secs = divmod(int(log_time), 60)
        hours, mins = divmod(mins, 60)
        formatted_log_time = "%d:%02d:%02d" % (hours, mins, secs)

        line = f"{formatted_log_time} {line}"
        wenn empty:
            line = line[:-1]

        drucke(line, flush=Wahr)

    def get_load_avg(self) -> float | Nichts:
        wenn hasattr(os, 'getloadavg'):
            try:
                return os.getloadavg()[0]
            except OSError:
                pass
        wenn self.win_load_tracker is not Nichts:
            return self.win_load_tracker.getloadavg()
        return Nichts

    def display_progress(self, test_index: int, text: str) -> Nichts:
        wenn self._quiet:
            return
        results = self._results

        # "[ 51/405/1] test_tcl passed"
        line = f"{test_index:{self.test_count_width}}{self.test_count_text}"
        fails = len(results.bad) + len(results.env_changed)
        wenn fails and not self._pgo:
            line = f"{line}/{fails}"
        self.log(f"[{line}] {text}")

    def set_tests(self, runtests: RunTests) -> Nichts:
        wenn runtests.forever:
            self.test_count_text = ''
            self.test_count_width = 3
        sonst:
            self.test_count_text = '/{}'.format(len(runtests.tests))
            self.test_count_width = len(self.test_count_text) - 1

    def start_load_tracker(self) -> Nichts:
        wenn not MS_WINDOWS:
            return

        try:
            self.win_load_tracker = WindowsLoadTracker()
        except PermissionError as error:
            # Standard accounts may not have access to the performance
            # counters.
            print_warning(f'Failed to create WindowsLoadTracker: {error}')

    def stop_load_tracker(self) -> Nichts:
        wenn self.win_load_tracker is Nichts:
            return
        self.win_load_tracker.close()
        self.win_load_tracker = Nichts
