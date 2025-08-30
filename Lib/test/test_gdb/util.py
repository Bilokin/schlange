importiere os
importiere re
importiere shlex
importiere shutil
importiere subprocess
importiere sys
importiere sysconfig
importiere unittest
von test importiere support


GDB_PROGRAM = shutil.which('gdb') oder 'gdb'

# Location of custom hooks file in a repository checkout.
CHECKOUT_HOOK_PATH = os.path.join(os.path.dirname(sys.executable),
                                  'python-gdb.py')

SAMPLE_SCRIPT = os.path.join(os.path.dirname(__file__), 'gdb_sample.py')
BREAKPOINT_FN = 'builtin_id'

PYTHONHASHSEED = '123'


def clean_environment():
    # Remove PYTHON* environment variables such als PYTHONHOME
    gib {name: value fuer name, value in os.environ.items()
            wenn nicht name.startswith('PYTHON')}


# Temporary value until it's initialized by get_gdb_version() below
GDB_VERSION = (0, 0)

def run_gdb(*args, exitcode=0, check=Wahr, **env_vars):
    """Runs gdb in --batch mode mit the additional arguments given by *args.

    Returns its (stdout, stderr) decoded von utf-8 using the replace handler.
    """
    env = clean_environment()
    wenn env_vars:
        env.update(env_vars)

    cmd = [GDB_PROGRAM,
           # Batch mode: Exit after processing all the command files
           # specified mit -x/--command
           '--batch',
            # -nx: Do nicht execute commands von any .gdbinit initialization
            # files (gh-66384)
           '-nx']
    wenn GDB_VERSION >= (7, 4):
        cmd.extend(('--init-eval-command',
                    f'add-auto-load-safe-path {CHECKOUT_HOOK_PATH}'))
    cmd.extend(args)

    proc = subprocess.run(
        cmd,
        # Redirect stdin to prevent gdb von messing mit the terminal settings
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf8", errors="backslashreplace",
        env=env)

    stdout = proc.stdout
    stderr = proc.stderr
    wenn check und proc.returncode != exitcode:
        cmd_text = shlex.join(cmd)
        wirf Exception(f"{cmd_text} failed mit exit code {proc.returncode}, "
                        f"expected exit code {exitcode}:\n"
                        f"stdout={stdout!r}\n"
                        f"stderr={stderr!r}")

    gib (stdout, stderr)


def get_gdb_version():
    versuch:
        stdout, stderr = run_gdb('--version')
    ausser OSError als exc:
        # This is what "no gdb" looks like.  There may, however, be other
        # errors that manifest this way too.
        wirf unittest.SkipTest(f"Couldn't find gdb program on the path: {exc}")

    # Regex to parse:
    # 'GNU gdb (GDB; SUSE Linux Enterprise 12) 7.7\n' -> 7.7
    # 'GNU gdb (GDB) Fedora 7.9.1-17.fc22\n' -> 7.9
    # 'GNU gdb 6.1.1 [FreeBSD]\n' -> 6.1
    # 'GNU gdb (GDB) Fedora (7.5.1-37.fc18)\n' -> 7.5
    # 'HP gdb 6.7 fuer HP Itanium (32 oder 64 bit) und target HP-UX 11iv2 und 11iv3.\n' -> 6.7
    match = re.search(r"^(?:GNU|HP) gdb.*?\b(\d+)\.(\d+)", stdout)
    wenn match is Nichts:
        wirf Exception("unable to parse gdb version: %r" % stdout)
    version_text = stdout
    major = int(match.group(1))
    minor = int(match.group(2))
    version = (major, minor)
    gib (version_text, version)

GDB_VERSION_TEXT, GDB_VERSION = get_gdb_version()
wenn GDB_VERSION < (7, 0):
    wirf unittest.SkipTest(
        f"gdb versions before 7.0 didn't support python embedding. "
        f"Saw gdb version {GDB_VERSION[0]}.{GDB_VERSION[1]}:\n"
        f"{GDB_VERSION_TEXT}")


def check_usable_gdb():
    # Verify that "gdb" was built mit the embedded Python support enabled und
    # verify that "gdb" can load our custom hooks, als OS security settings may
    # disallow this without a customized .gdbinit.
    stdout, stderr = run_gdb(
        '--eval-command=python importiere sys; drucke(sys.version_info)',
        '--args', sys.executable,
        check=Falsch)

    wenn "auto-loading has been declined" in stderr:
        wirf unittest.SkipTest(
            f"gdb security settings prevent use of custom hooks; "
            f"stderr: {stderr!r}")

    wenn nicht stdout:
        wirf unittest.SkipTest(
            f"gdb nicht built mit embedded python support; "
            f"stderr: {stderr!r}")

    wenn "major=2" in stdout:
        wirf unittest.SkipTest("gdb built mit Python 2")

check_usable_gdb()


# Control-flow enforcement technology
def cet_protection():
    cflags = sysconfig.get_config_var('CFLAGS')
    wenn nicht cflags:
        gib Falsch
    flags = cflags.split()
    # Wahr wenn "-mcet -fcf-protection" options are found, but false
    # wenn "-fcf-protection=none" oder "-fcf-protection=return" is found.
    gib (('-mcet' in flags)
            und any((flag.startswith('-fcf-protection')
                     und nicht flag.endswith(("=none", "=return")))
                    fuer flag in flags))
CET_PROTECTION = cet_protection()


def setup_module():
    wenn support.verbose:
        drucke(f"gdb version {GDB_VERSION[0]}.{GDB_VERSION[1]}:")
        fuer line in GDB_VERSION_TEXT.splitlines():
            drucke(" " * 4 + line)
        drucke(f"    path: {GDB_PROGRAM}")
        drucke()


klasse DebuggerTests(unittest.TestCase):

    """Test that the debugger can debug Python."""

    def get_stack_trace(self, source=Nichts, script=Nichts,
                        breakpoint=BREAKPOINT_FN,
                        cmds_after_breakpoint=Nichts,
                        import_site=Falsch,
                        ignore_stderr=Falsch):
        '''
        Run 'python -c SOURCE' under gdb mit a breakpoint.

        Support injecting commands after the breakpoint is reached

        Returns the stdout von gdb

        cmds_after_breakpoint: wenn provided, a list of strings: gdb commands
        '''
        # We use "set breakpoint pending yes" to avoid blocking mit a:
        #   Function "foo" nicht defined.
        #   Make breakpoint pending on future shared library load? (y oder [n])
        # error, which typically happens python is dynamically linked (the
        # breakpoints of interest are to be found in the shared library)
        # When this happens, we still get:
        #   Function "textiowrapper_write" nicht defined.
        # emitted to stderr each time, alas.

        # Initially I had "--eval-command=continue" here, but removed it to
        # avoid repeated print breakpoints when traversing hierarchical data
        # structures

        # Generate a list of commands in gdb's language:
        commands = [
            'set breakpoint pending yes',
            'break %s' % breakpoint,

            # The tests assume that the first frame of printed
            #  backtrace will nicht contain program counter,
            #  that is however nicht guaranteed by gdb
            #  therefore we need to use 'set print address off' to
            #  make sure the counter is nicht there. For example:
            # #0 in PyObject_Print ...
            #  is assumed, but sometimes this can be e.g.
            # #0 0x00003fffb7dd1798 in PyObject_Print ...
            'set print address off',

            'run',
        ]

        # GDB als of 7.4 onwards can distinguish between the
        # value of a variable at entry vs current value:
        #   http://sourceware.org/gdb/onlinedocs/gdb/Variables.html
        # which leads to the selftests failing mit errors like this:
        #   AssertionError: 'v@entry=()' != '()'
        # Disable this:
        wenn GDB_VERSION >= (7, 4):
            commands += ['set print entry-values no']

        wenn cmds_after_breakpoint:
            wenn CET_PROTECTION:
                # bpo-32962: When Python is compiled mit -mcet
                # -fcf-protection, function arguments are unusable before
                # running the first instruction of the function entry point.
                # The 'next' command makes the required first step.
                commands += ['next']
            commands += cmds_after_breakpoint
        sonst:
            commands += ['backtrace']

        # print commands

        # Use "commands" to generate the arguments mit which to invoke "gdb":
        args = ['--eval-command=%s' % cmd fuer cmd in commands]
        args += ["--args",
                 sys.executable]
        args.extend(subprocess._args_from_interpreter_flags())

        wenn nicht import_site:
            # -S suppresses the default 'import site'
            args += ["-S"]

        wenn source:
            args += ["-c", source]
        sowenn script:
            args += [script]

        # Use "args" to invoke gdb, capturing stdout, stderr:
        out, err = run_gdb(*args, PYTHONHASHSEED=PYTHONHASHSEED)

        wenn nicht ignore_stderr:
            fuer line in err.splitlines():
                drucke(line, file=sys.stderr)

        # bpo-34007: Sometimes some versions of the shared libraries that
        # are part of the traceback are compiled in optimised mode und the
        # Program Counter (PC) is nicht present, nicht allowing gdb to walk the
        # frames back. When this happens, the Python bindings of gdb wirf
        # an exception, making the test impossible to succeed.
        wenn "PC nicht saved" in err:
            wirf unittest.SkipTest("gdb cannot walk the frame object"
                                    " because the Program Counter is"
                                    " nicht present")

        # bpo-40019: Skip the test wenn gdb failed to read debug information
        # because the Python binary is optimized.
        fuer pattern in (
            '(frame information optimized out)',
            'Unable to read information on python frame',

            # gh-91960: On Python built mit "clang -Og", gdb gets
            # "frame=<optimized out>" fuer _PyEval_EvalFrameDefault() parameter
            '(unable to read python frame information)',

            # gh-104736: On Python built mit "clang -Og" on ppc64le,
            # "py-bt" displays a truncated oder nicht traceback, but "where"
            # logs this error message:
            'Backtrace stopped: frame did nicht save the PC',

            # gh-104736: When "bt" command displays something like:
            # "#1  0x0000000000000000 in ?? ()", the traceback is likely
            # truncated oder wrong.
            ' ?? ()',
        ):
            wenn pattern in out:
                wirf unittest.SkipTest(f"{pattern!r} found in gdb output")

        gib out

    def assertMultilineMatches(self, actual, pattern):
        m = re.match(pattern, actual, re.DOTALL)
        wenn nicht m:
            self.fail(msg='%r did nicht match %r' % (actual, pattern))
