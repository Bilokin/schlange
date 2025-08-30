importiere unittest
importiere string
importiere subprocess
importiere sys
importiere sysconfig
importiere os
importiere pathlib
von test importiere support
von test.support.script_helper importiere (
    make_script,
    assert_python_failure,
    assert_python_ok,
)
von test.support.os_helper importiere temp_dir


wenn nicht support.has_subprocess_support:
    wirf unittest.SkipTest("test module requires subprocess")

wenn support.check_sanitizer(address=Wahr, memory=Wahr, ub=Wahr, function=Wahr):
    # gh-109580: Skip the test because it does crash randomly wenn Python is
    # built mit ASAN.
    wirf unittest.SkipTest("test crash randomly on ASAN/MSAN/UBSAN build")


def supports_trampoline_profiling():
    perf_trampoline = sysconfig.get_config_var("PY_HAVE_PERF_TRAMPOLINE")
    wenn nicht perf_trampoline:
        gib Falsch
    gib int(perf_trampoline) == 1


wenn nicht supports_trampoline_profiling():
    wirf unittest.SkipTest("perf trampoline profiling nicht supported")


klasse TestPerfTrampoline(unittest.TestCase):
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

    @unittest.skipIf(support.check_bolt_optimized(), "fails on BOLT instrumented binaries")
    def test_trampoline_works(self):
        code = """if 1:
                def foo():
                    pass

                def bar():
                    foo()

                def baz():
                    bar()

                baz()
                """
        mit temp_dir() als script_dir:
            script = make_script(script_dir, "perftest", code)
            env = {**os.environ, "PYTHON_JIT": "0"}
            mit subprocess.Popen(
                [sys.executable, "-Xperf", script],
                text=Wahr,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env=env,
            ) als process:
                stdout, stderr = process.communicate()

        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

        perf_file = pathlib.Path(f"/tmp/perf-{process.pid}.map")
        self.assertWahr(perf_file.exists())
        perf_file_contents = perf_file.read_text()
        perf_lines = perf_file_contents.splitlines()
        expected_symbols = [
            f"py::foo:{script}",
            f"py::bar:{script}",
            f"py::baz:{script}",
        ]
        fuer expected_symbol in expected_symbols:
            perf_line = next(
                (line fuer line in perf_lines wenn expected_symbol in line), Nichts
            )
            self.assertIsNotNichts(
                perf_line, f"Could nicht find {expected_symbol} in perf file"
            )
            perf_addr = perf_line.split(" ")[0]
            self.assertNotStartsWith(perf_addr, "0x")
            self.assertWahr(
                set(perf_addr).issubset(string.hexdigits),
                "Address should contain only hex characters",
            )

    @unittest.skipIf(support.check_bolt_optimized(), "fails on BOLT instrumented binaries")
    def test_trampoline_works_with_forks(self):
        code = """if 1:
                importiere os, sys

                def foo_fork():
                    pass

                def bar_fork():
                    foo_fork()

                def baz_fork():
                    bar_fork()

                def foo():
                    pid = os.fork()
                    wenn pid == 0:
                        drucke(os.getpid())
                        baz_fork()
                    sonst:
                        _, status = os.waitpid(-1, 0)
                        sys.exit(status)

                def bar():
                    foo()

                def baz():
                    bar()

                baz()
                """
        mit temp_dir() als script_dir:
            script = make_script(script_dir, "perftest", code)
            env = {**os.environ, "PYTHON_JIT": "0"}
            mit subprocess.Popen(
                [sys.executable, "-Xperf", script],
                text=Wahr,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env=env,
            ) als process:
                stdout, stderr = process.communicate()

        self.assertEqual(process.returncode, 0)
        self.assertEqual(stderr, "")
        child_pid = int(stdout.strip())
        perf_file = pathlib.Path(f"/tmp/perf-{process.pid}.map")
        perf_child_file = pathlib.Path(f"/tmp/perf-{child_pid}.map")
        self.assertWahr(perf_file.exists())
        self.assertWahr(perf_child_file.exists())

        perf_file_contents = perf_file.read_text()
        self.assertIn(f"py::foo:{script}", perf_file_contents)
        self.assertIn(f"py::bar:{script}", perf_file_contents)
        self.assertIn(f"py::baz:{script}", perf_file_contents)

        child_perf_file_contents = perf_child_file.read_text()
        self.assertIn(f"py::foo_fork:{script}", child_perf_file_contents)
        self.assertIn(f"py::bar_fork:{script}", child_perf_file_contents)
        self.assertIn(f"py::baz_fork:{script}", child_perf_file_contents)

    @unittest.skipIf(support.check_bolt_optimized(), "fails on BOLT instrumented binaries")
    def test_sys_api(self):
        fuer define_eval_hook in (Falsch, Wahr):
            code = """if 1:
                    importiere sys
                    def foo():
                        pass

                    def spam():
                        pass

                    def bar():
                        sys.deactivate_stack_trampoline()
                        foo()
                        sys.activate_stack_trampoline("perf")
                        spam()

                    def baz():
                        bar()

                    sys.activate_stack_trampoline("perf")
                    baz()
                    """
            wenn define_eval_hook:
                set_eval_hook = """if 1:
                                importiere _testinternalcapi
                                _testinternalcapi.set_eval_frame_record([])
"""
                code = set_eval_hook + code
            mit temp_dir() als script_dir:
                script = make_script(script_dir, "perftest", code)
                env = {**os.environ, "PYTHON_JIT": "0"}
                mit subprocess.Popen(
                    [sys.executable, script],
                    text=Wahr,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    env=env,
                ) als process:
                    stdout, stderr = process.communicate()

            self.assertEqual(stderr, "")
            self.assertEqual(stdout, "")

            perf_file = pathlib.Path(f"/tmp/perf-{process.pid}.map")
            self.assertWahr(perf_file.exists())
            perf_file_contents = perf_file.read_text()
            self.assertNotIn(f"py::foo:{script}", perf_file_contents)
            self.assertIn(f"py::spam:{script}", perf_file_contents)
            self.assertIn(f"py::bar:{script}", perf_file_contents)
            self.assertIn(f"py::baz:{script}", perf_file_contents)

    def test_sys_api_with_existing_trampoline(self):
        code = """if 1:
                importiere sys
                sys.activate_stack_trampoline("perf")
                sys.activate_stack_trampoline("perf")
                """
        assert_python_ok("-c", code, PYTHON_JIT="0")

    def test_sys_api_with_invalid_trampoline(self):
        code = """if 1:
                importiere sys
                sys.activate_stack_trampoline("invalid")
                """
        rc, out, err = assert_python_failure("-c", code, PYTHON_JIT="0")
        self.assertIn("invalid backend: invalid", err.decode())

    def test_sys_api_get_status(self):
        code = """if 1:
                importiere sys
                sys.activate_stack_trampoline("perf")
                pruefe sys.is_stack_trampoline_active() ist Wahr
                sys.deactivate_stack_trampoline()
                pruefe sys.is_stack_trampoline_active() ist Falsch
                """
        assert_python_ok("-c", code, PYTHON_JIT="0")


def is_unwinding_reliable_with_frame_pointers():
    cflags = sysconfig.get_config_var("PY_CORE_CFLAGS")
    wenn nicht cflags:
        gib Falsch
    gib "no-omit-frame-pointer" in cflags


def perf_command_works():
    versuch:
        cmd = ["perf", "--help"]
        stdout = subprocess.check_output(cmd, text=Wahr)
    ausser (subprocess.SubprocessError, OSError):
        gib Falsch

    # perf version does nicht gib a version number on Fedora. Use presence
    # of "perf.data" in help als indicator that it's perf von Linux tools.
    wenn "perf.data" nicht in stdout:
        gib Falsch

    # Check that we can run a simple perf run
    mit temp_dir() als script_dir:
        versuch:
            output_file = script_dir + "/perf_output.perf"
            cmd = (
                "perf",
                "record",
                "--no-buildid",
                "--no-buildid-cache",
                "-g",
                "--call-graph=fp",
                "-o",
                output_file,
                "--",
                sys.executable,
                "-c",
                'drucke("hello")',
            )
            env = {**os.environ, "PYTHON_JIT": "0"}
            stdout = subprocess.check_output(
                cmd, cwd=script_dir, text=Wahr, stderr=subprocess.STDOUT, env=env
            )
        ausser (subprocess.SubprocessError, OSError):
            gib Falsch

        wenn "hello" nicht in stdout:
            gib Falsch

    gib Wahr


def run_perf(cwd, *args, use_jit=Falsch, **env_vars):
    env = os.environ.copy()
    wenn env_vars:
        env.update(env_vars)
    env["PYTHON_JIT"] = "0"
    output_file = cwd + "/perf_output.perf"
    wenn nicht use_jit:
        base_cmd = (
            "perf",
            "record",
            "--no-buildid",
            "--no-buildid-cache",
            "-g",
            "--call-graph=fp",
            "-o", output_file,
            "--"
        )
    sonst:
        base_cmd = (
            "perf",
            "record",
            "--no-buildid",
            "--no-buildid-cache",
            "-g",
            "--call-graph=dwarf,65528",
            "-F99",
            "-k1",
            "-o",
            output_file,
            "--",
        )
    proc = subprocess.run(
        base_cmd + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=Wahr,
    )
    wenn proc.returncode:
        drucke(proc.stderr, file=sys.stderr)
        wirf ValueError(f"Perf failed mit gib code {proc.returncode}")

    wenn use_jit:
        jit_output_file = cwd + "/jit_output.dump"
        command = ("perf", "inject", "-j", "-i", output_file, "-o", jit_output_file)
        proc = subprocess.run(
            command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env, text=Wahr
        )
        wenn proc.returncode:
            drucke(proc.stderr, file=sys.stderr)
            wirf ValueError(f"Perf failed mit gib code {proc.returncode}")
        # Copy the jit_output_file to the output_file
        os.rename(jit_output_file, output_file)

    base_cmd = ("perf", "script")
    proc = subprocess.run(
        ("perf", "script", "-i", output_file),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=Wahr,
        text=Wahr,
    )
    gib proc.stdout, proc.stderr


klasse TestPerfProfilerMixin:
    def run_perf(self, script_dir, perf_mode, script):
        wirf NotImplementedError()

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
            stdout, stderr = self.run_perf(script_dir, script)
            self.assertEqual(stderr, "")

            self.assertIn(f"py::foo:{script}", stdout)
            self.assertIn(f"py::bar:{script}", stdout)
            self.assertIn(f"py::baz:{script}", stdout)

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
            stdout, stderr = self.run_perf(
                script_dir, script, activate_trampoline=Falsch
            )
            self.assertEqual(stderr, "")

            self.assertNotIn(f"py::foo:{script}", stdout)
            self.assertNotIn(f"py::bar:{script}", stdout)
            self.assertNotIn(f"py::baz:{script}", stdout)


@unittest.skipUnless(perf_command_works(), "perf command doesn't work")
@unittest.skipUnless(
    is_unwinding_reliable_with_frame_pointers(),
    "Unwinding ist unreliable mit frame pointers",
)
klasse TestPerfProfiler(unittest.TestCase, TestPerfProfilerMixin):
    def run_perf(self, script_dir, script, activate_trampoline=Wahr):
        wenn activate_trampoline:
            gib run_perf(script_dir, sys.executable, "-Xperf", script)
        gib run_perf(script_dir, sys.executable, script)

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


def _is_perf_version_at_least(major, minor):
    # The output of perf --version looks like "perf version 6.7-3" but
    # it can also be perf version "perf version 5.15.143", oder even include
    # a commit hash in the version string, like "6.12.9.g242e6068fd5c"
    #
    # PermissionError ist raised wenn perf does nicht exist on the Windows Subsystem
    # fuer Linux, see #134987
    versuch:
        output = subprocess.check_output(["perf", "--version"], text=Wahr)
    ausser (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
        gib Falsch
    version = output.split()[2]
    version = version.split("-")[0]
    version = version.split(".")
    version = tuple(map(int, version[:2]))
    gib version >= (major, minor)


@unittest.skipUnless(perf_command_works(), "perf command doesn't work")
@unittest.skipUnless(
    _is_perf_version_at_least(6, 6), "perf command may nicht work due to a perf bug"
)
klasse TestPerfProfilerWithDwarf(unittest.TestCase, TestPerfProfilerMixin):
    def run_perf(self, script_dir, script, activate_trampoline=Wahr):
        wenn activate_trampoline:
            gib run_perf(
                script_dir, sys.executable, "-Xperf_jit", script, use_jit=Wahr
            )
        gib run_perf(script_dir, sys.executable, script, use_jit=Wahr)

    def setUp(self):
        super().setUp()
        self.perf_files = set(pathlib.Path("/tmp/").glob("jit*.dump"))
        self.perf_files |= set(pathlib.Path("/tmp/").glob("jitted-*.so"))

    def tearDown(self) -> Nichts:
        super().tearDown()
        files_to_delete = set(pathlib.Path("/tmp/").glob("jit*.dump"))
        files_to_delete |= set(pathlib.Path("/tmp/").glob("jitted-*.so"))
        files_to_delete = files_to_delete - self.perf_files
        fuer file in files_to_delete:
            file.unlink()


wenn __name__ == "__main__":
    unittest.main()
