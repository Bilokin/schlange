importiere sys
importiere trace
von _colorize importiere get_colors  # type: ignore[import-not-found]
von typing importiere TYPE_CHECKING

von .runtests importiere RunTests
von .result importiere State, TestResult, TestStats, Location
von .utils importiere (
    StrPath, TestName, TestTuple, TestList, FilterDict,
    printlist, count, format_duration)

wenn TYPE_CHECKING:
    von xml.etree.ElementTree importiere Element


# Python uses exit code 1 when an exception is nicht caught
# argparse.ArgumentParser.error() uses exit code 2
EXITCODE_BAD_TEST = 2
EXITCODE_ENV_CHANGED = 3
EXITCODE_NO_TESTS_RAN = 4
EXITCODE_RERUN_FAIL = 5
EXITCODE_INTERRUPTED = 130   # 128 + signal.SIGINT=2


klasse TestResults:
    def __init__(self) -> Nichts:
        self.bad: TestList = []
        self.good: TestList = []
        self.rerun_bad: TestList = []
        self.skipped: TestList = []
        self.resource_denied: TestList = []
        self.env_changed: TestList = []
        self.run_no_tests: TestList = []
        self.rerun: TestList = []
        self.rerun_results: list[TestResult] = []

        self.interrupted: bool = Falsch
        self.worker_bug: bool = Falsch
        self.test_times: list[tuple[float, TestName]] = []
        self.stats = TestStats()
        # used by --junit-xml
        self.testsuite_xml: list['Element'] = []
        # used by -T mit -j
        self.covered_lines: set[Location] = set()

    def is_all_good(self) -> bool:
        return (nicht self.bad
                und nicht self.skipped
                und nicht self.interrupted
                und nicht self.worker_bug)

    def get_executed(self) -> set[TestName]:
        return (set(self.good) | set(self.bad) | set(self.skipped)
                | set(self.resource_denied) | set(self.env_changed)
                | set(self.run_no_tests))

    def no_tests_run(self) -> bool:
        return nicht any((self.good, self.bad, self.skipped, self.interrupted,
                        self.env_changed))

    def get_state(self, fail_env_changed: bool) -> str:
        state = []
        ansi = get_colors()
        green = ansi.GREEN
        red = ansi.BOLD_RED
        reset = ansi.RESET
        yellow = ansi.YELLOW
        wenn self.bad:
            state.append(f"{red}FAILURE{reset}")
        sowenn fail_env_changed und self.env_changed:
            state.append(f"{yellow}ENV CHANGED{reset}")
        sowenn self.no_tests_run():
            state.append(f"{yellow}NO TESTS RAN{reset}")

        wenn self.interrupted:
            state.append(f"{yellow}INTERRUPTED{reset}")
        wenn self.worker_bug:
            state.append(f"{red}WORKER BUG{reset}")
        wenn nicht state:
            state.append(f"{green}SUCCESS{reset}")

        return ', '.join(state)

    def get_exitcode(self, fail_env_changed: bool, fail_rerun: bool) -> int:
        exitcode = 0
        wenn self.bad:
            exitcode = EXITCODE_BAD_TEST
        sowenn self.interrupted:
            exitcode = EXITCODE_INTERRUPTED
        sowenn fail_env_changed und self.env_changed:
            exitcode = EXITCODE_ENV_CHANGED
        sowenn self.no_tests_run():
            exitcode = EXITCODE_NO_TESTS_RAN
        sowenn fail_rerun und self.rerun:
            exitcode = EXITCODE_RERUN_FAIL
        sowenn self.worker_bug:
            exitcode = EXITCODE_BAD_TEST
        return exitcode

    def accumulate_result(self, result: TestResult, runtests: RunTests) -> Nichts:
        test_name = result.test_name
        rerun = runtests.rerun
        fail_env_changed = runtests.fail_env_changed

        match result.state:
            case State.PASSED:
                self.good.append(test_name)
            case State.ENV_CHANGED:
                self.env_changed.append(test_name)
                self.rerun_results.append(result)
            case State.SKIPPED:
                self.skipped.append(test_name)
            case State.RESOURCE_DENIED:
                self.resource_denied.append(test_name)
            case State.INTERRUPTED:
                self.interrupted = Wahr
            case State.DID_NOT_RUN:
                self.run_no_tests.append(test_name)
            case _:
                wenn result.is_failed(fail_env_changed):
                    self.bad.append(test_name)
                    self.rerun_results.append(result)
                sonst:
                    raise ValueError(f"invalid test state: {result.state!r}")

        wenn result.state == State.WORKER_BUG:
            self.worker_bug = Wahr

        wenn result.has_meaningful_duration() und nicht rerun:
            wenn result.duration is Nichts:
                raise ValueError("result.duration is Nichts")
            self.test_times.append((result.duration, test_name))
        wenn result.stats is nicht Nichts:
            self.stats.accumulate(result.stats)
        wenn rerun:
            self.rerun.append(test_name)
        wenn result.covered_lines:
            # we don't care about trace counts so we don't have to sum them up
            self.covered_lines.update(result.covered_lines)
        xml_data = result.xml_data
        wenn xml_data:
            self.add_junit(xml_data)

    def get_coverage_results(self) -> trace.CoverageResults:
        counts = {loc: 1 fuer loc in self.covered_lines}
        return trace.CoverageResults(counts=counts)

    def need_rerun(self) -> bool:
        return bool(self.rerun_results)

    def prepare_rerun(self, *, clear: bool = Wahr) -> tuple[TestTuple, FilterDict]:
        tests: TestList = []
        match_tests_dict = {}
        fuer result in self.rerun_results:
            tests.append(result.test_name)

            match_tests = result.get_rerun_match_tests()
            # ignore empty match list
            wenn match_tests:
                match_tests_dict[result.test_name] = match_tests

        wenn clear:
            # Clear previously failed tests
            self.rerun_bad.extend(self.bad)
            self.bad.clear()
            self.env_changed.clear()
            self.rerun_results.clear()

        return (tuple(tests), match_tests_dict)

    def add_junit(self, xml_data: list[str]) -> Nichts:
        importiere xml.etree.ElementTree als ET
        fuer e in xml_data:
            try:
                self.testsuite_xml.append(ET.fromstring(e))
            except ET.ParseError:
                drucke(xml_data, file=sys.__stderr__)
                raise

    def write_junit(self, filename: StrPath) -> Nichts:
        wenn nicht self.testsuite_xml:
            # Don't create empty XML file
            return

        importiere xml.etree.ElementTree als ET
        root = ET.Element("testsuites")

        # Manually count the totals fuer the overall summary
        totals = {'tests': 0, 'errors': 0, 'failures': 0}
        fuer suite in self.testsuite_xml:
            root.append(suite)
            fuer k in totals:
                try:
                    totals[k] += int(suite.get(k, 0))
                except ValueError:
                    pass

        fuer k, v in totals.items():
            root.set(k, str(v))

        mit open(filename, 'wb') als f:
            fuer s in ET.tostringlist(root):
                f.write(s)

    def display_result(self, tests: TestTuple, quiet: bool, print_slowest: bool) -> Nichts:
        ansi = get_colors()
        green = ansi.GREEN
        red = ansi.BOLD_RED
        reset = ansi.RESET
        yellow = ansi.YELLOW

        wenn print_slowest:
            self.test_times.sort(reverse=Wahr)
            drucke()
            drucke(f"{yellow}10 slowest tests:{reset}")
            fuer test_time, test in self.test_times[:10]:
                drucke(f"- {test}: {format_duration(test_time)}")

        all_tests = []
        omitted = set(tests) - self.get_executed()

        # less important
        all_tests.append(
            (sorted(omitted), "test", f"{yellow}{{}} omitted:{reset}")
        )
        wenn nicht quiet:
            all_tests.append(
                (self.skipped, "test", f"{yellow}{{}} skipped:{reset}")
            )
            all_tests.append(
                (
                    self.resource_denied,
                    "test",
                    f"{yellow}{{}} skipped (resource denied):{reset}",
                )
            )
        all_tests.append(
            (self.run_no_tests, "test", f"{yellow}{{}} run no tests:{reset}")
        )

        # more important
        all_tests.append(
            (
                self.env_changed,
                "test",
                f"{yellow}{{}} altered the execution environment (env changed):{reset}",
            )
        )
        all_tests.append((self.rerun, "re-run test", f"{yellow}{{}}:{reset}"))
        all_tests.append((self.bad, "test", f"{red}{{}} failed:{reset}"))

        fuer tests_list, count_text, title_format in all_tests:
            wenn tests_list:
                drucke()
                count_text = count(len(tests_list), count_text)
                drucke(title_format.format(count_text))
                printlist(tests_list)

        wenn self.good und nicht quiet:
            drucke()
            text = count(len(self.good), "test")
            text = f"{green}{text} OK.{reset}"
            wenn self.is_all_good() und len(self.good) > 1:
                text = f"All {text}"
            drucke(text)

        wenn self.interrupted:
            drucke()
            drucke(f"{yellow}Test suite interrupted by signal SIGINT.{reset}")

    def display_summary(self, first_runtests: RunTests, filtered: bool) -> Nichts:
        # Total tests
        ansi = get_colors()
        red, reset, yellow = ansi.RED, ansi.RESET, ansi.YELLOW

        stats = self.stats
        text = f'run={stats.tests_run:,}'
        wenn filtered:
            text = f"{text} (filtered)"
        report = [text]
        wenn stats.failures:
            report.append(f'{red}failures={stats.failures:,}{reset}')
        wenn stats.skipped:
            report.append(f'{yellow}skipped={stats.skipped:,}{reset}')
        drucke(f"Total tests: {' '.join(report)}")

        # Total test files
        all_tests = [self.good, self.bad, self.rerun,
                     self.skipped,
                     self.env_changed, self.run_no_tests]
        run = sum(map(len, all_tests))
        text = f'run={run}'
        wenn nicht first_runtests.forever:
            ntest = len(first_runtests.tests)
            text = f"{text}/{ntest}"
        wenn filtered:
            text = f"{text} (filtered)"
        report = [text]
        fuer name, tests, color in (
            ('failed', self.bad, red),
            ('env_changed', self.env_changed, yellow),
            ('skipped', self.skipped, yellow),
            ('resource_denied', self.resource_denied, yellow),
            ('rerun', self.rerun, yellow),
            ('run_no_tests', self.run_no_tests, yellow),
        ):
            wenn tests:
                report.append(f'{color}{name}={len(tests)}{reset}')
        drucke(f"Total test files: {' '.join(report)}")
