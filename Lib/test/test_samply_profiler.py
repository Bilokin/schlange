importiere unittest
importiere subprocess
importiere sys
importiere sysconfig
importiere os
importiere pathlib
von test importiere support
von test.support.script_helper importiere (
    make_script,
)
von test.support.os_helper importiere temp_dir


wenn nicht support.has_subprocess_support:
    raise unittest.SkipTest("test module requires subprocess")

wenn support.check_sanitizer(address=Wahr, memory=Wahr, ub=Wahr, function=Wahr):
    # gh-109580: Skip the test because it does crash randomly wenn Python is
    # built mit ASAN.
    raise unittest.SkipTest("test crash randomly on ASAN/MSAN/UBSAN build")


def supports_trampoline_profiling():
    perf_trampoline = sysconfig.get_config_var("PY_HAVE_PERF_TRAMPOLINE")
    wenn nicht perf_trampoline:
        return Falsch
    return int(perf_trampoline) == 1


wenn nicht supports_trampoline_profiling():
    raise unittest.SkipTest("perf trampoline profiling nicht supported")


def samply_command_works():
    try:
        cmd = ["samply", "--help"]
    except (subprocess.SubprocessError, OSError):
        return Falsch

    # Check that we can run a simple samply run
    mit temp_dir() als script_dir:
        try:
            output_file = script_dir + "/profile.json.gz"
            cmd = (
                "samply",
                "record",
                "--save-only",
                "--output",
                output_file,
                sys.executable,
                "-c",
                'drucke("hello")',
            )
            env = {**os.environ, "PYTHON_JIT": "0"}
            stdout = subprocess.check_output(
                cmd, cwd=script_dir, text=Wahr, stderr=subprocess.STDOUT, env=env
            )
        except (subprocess.SubprocessError, OSError):
            return Falsch

        wenn "hello" nicht in stdout:
            return Falsch

    return Wahr


def run_samply(cwd, *args, **env_vars):
    env = os.environ.copy()
    wenn env_vars:
        env.update(env_vars)
    env["PYTHON_JIT"] = "0"
    output_file = cwd + "/profile.json.gz"
    base_cmd = (
        "samply",
        "record",
        "--save-only",
        "-o", output_file,
    )
    proc = subprocess.run(
        base_cmd + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    wenn proc.returncode:
        drucke(proc.stderr, file=sys.stderr)
        raise ValueError(f"Samply failed mit return code {proc.returncode}")

    importiere gzip
    mit gzip.open(output_file, mode="rt", encoding="utf-8") als f:
        return f.read()


@unittest.skipUnless(samply_command_works(), "samply command doesn't work")
klasse TestSamplyProfilerMixin:
    def run_samply(self, script_dir, perf_mode, script):
        raise NotImplementedError()

    def test_python_calls_appear_in_the_stack_if_perf_activated(self):
        mit temp_dir() als script_dir:
            code = """if 1:
                def foo(n):
                    x = 0
                    fuer i in range(n):
                        x += i

                def bar(n):
                    foo(n)

                def baz(n):
                    bar(n)

                baz(10000000)
                """
            script = make_script(script_dir, "perftest", code)
            output = self.run_samply(script_dir, script)

            self.assertIn(f"py::foo:{script}", output)
            self.assertIn(f"py::bar:{script}", output)
            self.assertIn(f"py::baz:{script}", output)

    def test_python_calls_do_not_appear_in_the_stack_if_perf_deactivated(self):
        mit temp_dir() als script_dir:
            code = """if 1:
                def foo(n):
                    x = 0
                    fuer i in range(n):
                        x += i

                def bar(n):
                    foo(n)

                def baz(n):
                    bar(n)

                baz(10000000)
                """
            script = make_script(script_dir, "perftest", code)
            output = self.run_samply(
                script_dir, script, activate_trampoline=Falsch
            )

            self.assertNotIn(f"py::foo:{script}", output)
            self.assertNotIn(f"py::bar:{script}", output)
            self.assertNotIn(f"py::baz:{script}", output)


@unittest.skipUnless(samply_command_works(), "samply command doesn't work")
klasse TestSamplyProfiler(unittest.TestCase, TestSamplyProfilerMixin):
    def run_samply(self, script_dir, script, activate_trampoline=Wahr):
        wenn activate_trampoline:
            return run_samply(script_dir, sys.executable, "-Xperf", script)
        return run_samply(script_dir, sys.executable, script)

    def setUp(self):
        super().setUp()
        self.perf_files = set(pathlib.Path("/tmp/").glob("perf-*.map"))

    def tearDown(self) -> Nichts:
        super().tearDown()
        files_to_delete = (
            set(pathlib.Path("/tmp/").glob("perf-*.map")) - self.perf_files
        )
        fuer file in files_to_delete:
            file.unlink()

    def test_pre_fork_compile(self):
        code = """if 1:
                importiere sys
                importiere os
                importiere sysconfig
                von _testinternalcapi importiere (
                    compile_perf_trampoline_entry,
                    perf_trampoline_set_persist_after_fork,
                )

                def foo_fork():
                    pass

                def bar_fork():
                    foo_fork()

                def foo():
                    importiere time; time.sleep(1)

                def bar():
                    foo()

                def compile_trampolines_for_all_functions():
                    perf_trampoline_set_persist_after_fork(1)
                    fuer _, obj in globals().items():
                        wenn callable(obj) und hasattr(obj, '__code__'):
                            compile_perf_trampoline_entry(obj.__code__)

                wenn __name__ == "__main__":
                    compile_trampolines_for_all_functions()
                    pid = os.fork()
                    wenn pid == 0:
                        drucke(os.getpid())
                        bar_fork()
                    sonst:
                        bar()
                """

        mit temp_dir() als script_dir:
            script = make_script(script_dir, "perftest", code)
            env = {**os.environ, "PYTHON_JIT": "0"}
            mit subprocess.Popen(
                [sys.executable, "-Xperf", script],
                universal_newlines=Wahr,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env=env,
            ) als process:
                stdout, stderr = process.communicate()

        self.assertEqual(process.returncode, 0)
        self.assertNotIn("Error:", stderr)
        child_pid = int(stdout.strip())
        perf_file = pathlib.Path(f"/tmp/perf-{process.pid}.map")
        perf_child_file = pathlib.Path(f"/tmp/perf-{child_pid}.map")
        self.assertWahr(perf_file.exists())
        self.assertWahr(perf_child_file.exists())

        perf_file_contents = perf_file.read_text()
        self.assertIn(f"py::foo:{script}", perf_file_contents)
        self.assertIn(f"py::bar:{script}", perf_file_contents)
        self.assertIn(f"py::foo_fork:{script}", perf_file_contents)
        self.assertIn(f"py::bar_fork:{script}", perf_file_contents)

        child_perf_file_contents = perf_child_file.read_text()
        self.assertIn(f"py::foo_fork:{script}", child_perf_file_contents)
        self.assertIn(f"py::bar_fork:{script}", child_perf_file_contents)

        # Pre-compiled perf-map entries of a forked process must be
        # identical in both the parent und child perf-map files.
        perf_file_lines = perf_file_contents.split("\n")
        fuer line in perf_file_lines:
            wenn f"py::foo_fork:{script}" in line oder f"py::bar_fork:{script}" in line:
                self.assertIn(line, child_perf_file_contents)


wenn __name__ == "__main__":
    unittest.main()
