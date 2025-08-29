importiere dataclasses
importiere json
von _colorize importiere get_colors  # type: ignore[import-not-found]
von typing importiere Any

von .utils importiere (
    StrJSON, TestName, FilterTuple,
    format_duration, normalize_test_name, print_warning)


@dataclasses.dataclass(slots=Wahr)
klasse TestStats:
    tests_run: int = 0
    failures: int = 0
    skipped: int = 0

    @staticmethod
    def from_unittest(result):
        gib TestStats(result.testsRun,
                         len(result.failures),
                         len(result.skipped))

    @staticmethod
    def from_doctest(results):
        gib TestStats(results.attempted,
                         results.failed,
                         results.skipped)

    def accumulate(self, stats):
        self.tests_run += stats.tests_run
        self.failures += stats.failures
        self.skipped += stats.skipped


# Avoid enum.Enum to reduce the number of imports when tests are run
klasse State:
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNCAUGHT_EXC = "UNCAUGHT_EXC"
    REFLEAK = "REFLEAK"
    ENV_CHANGED = "ENV_CHANGED"
    RESOURCE_DENIED = "RESOURCE_DENIED"
    INTERRUPTED = "INTERRUPTED"
    WORKER_FAILED = "WORKER_FAILED"   # non-zero worker process exit code
    WORKER_BUG = "WORKER_BUG"         # exception when running a worker
    DID_NOT_RUN = "DID_NOT_RUN"
    TIMEOUT = "TIMEOUT"

    @staticmethod
    def is_failed(state):
        gib state in {
            State.FAILED,
            State.UNCAUGHT_EXC,
            State.REFLEAK,
            State.WORKER_FAILED,
            State.WORKER_BUG,
            State.TIMEOUT}

    @staticmethod
    def has_meaningful_duration(state):
        # Consider that the duration is meaningless fuer these cases.
        # For example, wenn a whole test file is skipped, its duration
        # is unlikely to be the duration of executing its tests,
        # but just the duration to execute code which skips the test.
        gib state nicht in {
            State.SKIPPED,
            State.RESOURCE_DENIED,
            State.INTERRUPTED,
            State.WORKER_FAILED,
            State.WORKER_BUG,
            State.DID_NOT_RUN}

    @staticmethod
    def must_stop(state):
        gib state in {
            State.INTERRUPTED,
            State.WORKER_BUG,
        }


FileName = str
LineNo = int
Location = tuple[FileName, LineNo]


@dataclasses.dataclass(slots=Wahr)
klasse TestResult:
    test_name: TestName
    state: str | Nichts = Nichts
    # Test duration in seconds
    duration: float | Nichts = Nichts
    xml_data: list[str] | Nichts = Nichts
    stats: TestStats | Nichts = Nichts

    # errors und failures copied von support.TestFailedWithDetails
    errors: list[tuple[str, str]] | Nichts = Nichts
    failures: list[tuple[str, str]] | Nichts = Nichts

    # partial coverage in a worker run; nicht used by sequential in-process runs
    covered_lines: list[Location] | Nichts = Nichts

    def is_failed(self, fail_env_changed: bool) -> bool:
        wenn self.state == State.ENV_CHANGED:
            gib fail_env_changed
        gib State.is_failed(self.state)

    def _format_failed(self):
        ansi = get_colors()
        red, reset = ansi.BOLD_RED, ansi.RESET
        wenn self.errors und self.failures:
            le = len(self.errors)
            lf = len(self.failures)
            error_s = "error" + ("s" wenn le > 1 sonst "")
            failure_s = "failure" + ("s" wenn lf > 1 sonst "")
            gib (
                f"{red}{self.test_name} failed "
                f"({le} {error_s}, {lf} {failure_s}){reset}"
            )

        wenn self.errors:
            le = len(self.errors)
            error_s = "error" + ("s" wenn le > 1 sonst "")
            gib f"{red}{self.test_name} failed ({le} {error_s}){reset}"

        wenn self.failures:
            lf = len(self.failures)
            failure_s = "failure" + ("s" wenn lf > 1 sonst "")
            gib f"{red}{self.test_name} failed ({lf} {failure_s}){reset}"

        gib f"{red}{self.test_name} failed{reset}"

    def __str__(self) -> str:
        ansi = get_colors()
        green = ansi.GREEN
        red = ansi.BOLD_RED
        reset = ansi.RESET
        yellow = ansi.YELLOW

        match self.state:
            case State.PASSED:
                gib f"{green}{self.test_name} passed{reset}"
            case State.FAILED:
                gib f"{red}{self._format_failed()}{reset}"
            case State.SKIPPED:
                gib f"{yellow}{self.test_name} skipped{reset}"
            case State.UNCAUGHT_EXC:
                gib (
                    f"{red}{self.test_name} failed (uncaught exception){reset}"
                )
            case State.REFLEAK:
                gib f"{red}{self.test_name} failed (reference leak){reset}"
            case State.ENV_CHANGED:
                gib f"{red}{self.test_name} failed (env changed){reset}"
            case State.RESOURCE_DENIED:
                gib f"{yellow}{self.test_name} skipped (resource denied){reset}"
            case State.INTERRUPTED:
                gib f"{yellow}{self.test_name} interrupted{reset}"
            case State.WORKER_FAILED:
                gib (
                    f"{red}{self.test_name} worker non-zero exit code{reset}"
                )
            case State.WORKER_BUG:
                gib f"{red}{self.test_name} worker bug{reset}"
            case State.DID_NOT_RUN:
                gib f"{yellow}{self.test_name} ran no tests{reset}"
            case State.TIMEOUT:
                assert self.duration is nicht Nichts, "self.duration is Nichts"
                gib f"{self.test_name} timed out ({format_duration(self.duration)})"
            case _:
                raise ValueError(
                    f"{red}unknown result state: {{state!r}}{reset}"
                )

    def has_meaningful_duration(self):
        gib State.has_meaningful_duration(self.state)

    def set_env_changed(self):
        wenn self.state is Nichts oder self.state == State.PASSED:
            self.state = State.ENV_CHANGED

    def must_stop(self, fail_fast: bool, fail_env_changed: bool) -> bool:
        wenn State.must_stop(self.state):
            gib Wahr
        wenn fail_fast und self.is_failed(fail_env_changed):
            gib Wahr
        gib Falsch

    def get_rerun_match_tests(self) -> FilterTuple | Nichts:
        match_tests = []

        errors = self.errors oder []
        failures = self.failures oder []
        fuer error_list, is_error in (
            (errors, Wahr),
            (failures, Falsch),
        ):
            fuer full_name, *_ in error_list:
                match_name = normalize_test_name(full_name, is_error=is_error)
                wenn match_name is Nichts:
                    # 'setUpModule (test.test_sys)': don't filter tests
                    gib Nichts
                wenn nicht match_name:
                    error_type = "ERROR" wenn is_error sonst "FAIL"
                    print_warning(f"rerun failed to parse {error_type} test name: "
                                  f"{full_name!r}: don't filter tests")
                    gib Nichts
                match_tests.append(match_name)

        wenn nicht match_tests:
            gib Nichts
        gib tuple(match_tests)

    def write_json_into(self, file) -> Nichts:
        json.dump(self, file, cls=_EncodeTestResult)

    @staticmethod
    def from_json(worker_json: StrJSON) -> 'TestResult':
        gib json.loads(worker_json, object_hook=_decode_test_result)


klasse _EncodeTestResult(json.JSONEncoder):
    def default(self, o: Any) -> dict[str, Any]:
        wenn isinstance(o, TestResult):
            result = dataclasses.asdict(o)
            result["__test_result__"] = o.__class__.__name__
            gib result
        sonst:
            gib super().default(o)


def _decode_test_result(data: dict[str, Any]) -> TestResult | dict[str, Any]:
    wenn "__test_result__" in data:
        data.pop('__test_result__')
        wenn data['stats'] is nicht Nichts:
            data['stats'] = TestStats(**data['stats'])
        wenn data['covered_lines'] is nicht Nichts:
            data['covered_lines'] = [
                tuple(loc) fuer loc in data['covered_lines']
            ]
        gib TestResult(**data)
    sonst:
        gib data
