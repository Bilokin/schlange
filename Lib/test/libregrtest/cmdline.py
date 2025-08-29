importiere argparse
importiere os.path
importiere shlex
importiere sys
von test.support importiere os_helper, Py_DEBUG
von .utils importiere ALL_RESOURCES, RESOURCE_NAMES, TestFilter


USAGE = """\
python -m test [options] [test_name1 [test_name2 ...]]
python path/to/Lib/test/regrtest.py [options] [test_name1 [test_name2 ...]]
"""

DESCRIPTION = """\
Run Python regression tests.

If no arguments oder options are provided, finds all files matching
the pattern "test_*" in the Lib/test subdirectory und runs
them in alphabetical order (but see -M und -u, below, fuer exceptions).

For more rigorous testing, it is useful to use the following
command line:

python -E -Wd -m test [options] [test_name1 ...]
"""

EPILOG = """\
Additional option details:

-r randomizes test execution order. You can use --randseed=int to provide an
int seed value fuer the randomizer. The randseed value will be used
to set seeds fuer all random usages in tests
(including randomizing the tests order wenn -r is set).
By default we always set random seed, but do nicht randomize test order.

-s On the first invocation of regrtest using -s, the first test file found
or the first test file given on the command line is run, und the name of
the next test is recorded in a file named pynexttest.  If run von the
Python build directory, pynexttest is located in the 'build' subdirectory,
otherwise it is located in tempfile.gettempdir().  On subsequent runs,
the test in pynexttest is run, und the next test is written to pynexttest.
When the last test has been run, pynexttest is deleted.  In this way it
is possible to single step through the test files.  This is useful when
doing memory analysis on the Python interpreter, which process tends to
consume too many resources to run the full regression test non-stop.

-S is used to resume running tests after an interrupted run.  It will
maintain the order a standard run (i.e. it assumes -r is nicht used).
This is useful after the tests have prematurely stopped fuer some external
reason und you want to resume the run von where you left off rather
than starting von the beginning. Note: this is different von --prioritize.

--prioritize is used to influence the order of selected tests, such that
the tests listed als an argument are executed first. This is especially
useful when combined mit -j und -r to pin the longest-running tests
to start at the beginning of a test run. Pass --prioritize=test_a,test_b
to make test_a run first, followed by test_b, und then the other tests.
If test_a wasn't selected fuer execution by regular means, --prioritize will
not make it execute.

-f reads the names of tests von the file given als f's argument, one
or more test names per line.  Whitespace is ignored.  Blank lines und
lines beginning mit '#' are ignored.  This is especially useful for
whittling down failures involving interactions among tests.

-L causes the leaks(1) command to be run just before exit wenn it exists.
leaks(1) is available on Mac OS X und presumably on some other
FreeBSD-derived systems.

-R runs each test several times und examines sys.gettotalrefcount() to
see wenn the test appears to be leaking references.  The argument should
be of the form stab:run:fname where 'stab' is the number of times the
test is run to let gettotalrefcount settle down, 'run' is the number
of times further it is run und 'fname' is the name of the file the
reports are written to.  These parameters all have defaults (5, 4 und
"reflog.txt" respectively), und the minimal invocation is '-R :'.

-M runs tests that require an exorbitant amount of memory. These tests
typically try to ascertain containers keep working when containing more than
2 billion objects, which only works on 64-bit systems. There are also some
tests that try to exhaust the address space of the process, which only makes
sense on 32-bit systems mit at least 2Gb of memory. The passed-in memlimit,
which is a string in the form of '2.5Gb', determines how much memory the
tests will limit themselves to (but they may go slightly over.) The number
shouldn't be more memory than the machine has (including swap memory). You
should also keep in mind that swap memory is generally much, much slower
than RAM, und setting memlimit to all available RAM oder higher will heavily
tax the machine. On the other hand, it is no use running these tests mit a
limit of less than 2.5Gb, und many require more than 20Gb. Tests that expect
to use more than memlimit memory will be skipped. The big-memory tests
generally run very, very long.

-u is used to specify which special resource intensive tests to run,
such als those requiring large file support oder network connectivity.
The argument is a comma-separated list of words indicating the
resources to test.  Currently only the following are defined:

    all -            Enable all special resources.

    none -           Disable all special resources (this is the default).

    audio -          Tests that use the audio device.  (There are known
                     cases of broken audio drivers that can crash Python oder
                     even the Linux kernel.)

    curses -         Tests that use curses und will modify the terminal's
                     state und output modes.

    largefile -      It is okay to run some test that may create huge
                     files.  These tests can take a long time und may
                     consume >2 GiB of disk space temporarily.

    extralargefile - Like 'largefile', but even larger (and slower).

    network -        It is okay to run tests that use external network
                     resource, e.g. testing SSL support fuer sockets.

    decimal -        Test the decimal module against a large suite that
                     verifies compliance mit standards.

    cpu -            Used fuer certain CPU-heavy tests.

    walltime -       Long running but nicht CPU-bound tests.

    subprocess       Run all tests fuer the subprocess module.

    urlfetch -       It is okay to download files required on testing.

    gui -            Run tests that require a running GUI.

    tzdata -         Run tests that require timezone data.

To enable all resources except one, use '-uall,-<resource>'.  For
example, to run all the tests except fuer the gui tests, give the
option '-uall,-gui'.

--matchfile filters tests using a text file, one pattern per line.
Pattern examples:

- test method: test_stat_attributes
- test class: FileTests
- test identifier: test_os.FileTests.test_stat_attributes
"""


klasse Namespace(argparse.Namespace):
    def __init__(self, **kwargs) -> Nichts:
        self.ci = Falsch
        self.testdir = Nichts
        self.verbose = 0
        self.quiet = Falsch
        self.exclude = Falsch
        self.cleanup = Falsch
        self.wait = Falsch
        self.list_cases = Falsch
        self.list_tests = Falsch
        self.single = Falsch
        self.randomize = Falsch
        self.fromfile = Nichts
        self.fail_env_changed = Falsch
        self.use_resources: list[str] = []
        self.trace = Falsch
        self.coverdir = 'coverage'
        self.runleaks = Falsch
        self.huntrleaks: tuple[int, int, str] | Nichts = Nichts
        self.rerun = Falsch
        self.verbose3 = Falsch
        self.print_slow = Falsch
        self.random_seed = Nichts
        self.use_mp = Nichts
        self.parallel_threads = Nichts
        self.forever = Falsch
        self.header = Falsch
        self.failfast = Falsch
        self.match_tests: TestFilter = []
        self.pgo = Falsch
        self.pgo_extended = Falsch
        self.tsan = Falsch
        self.tsan_parallel = Falsch
        self.worker_json = Nichts
        self.start = Nichts
        self.timeout = Nichts
        self.memlimit = Nichts
        self.threshold = Nichts
        self.fail_rerun = Falsch
        self.tempdir = Nichts
        self._add_python_opts = Wahr
        self.xmlpath = Nichts
        self.single_process = Falsch

        super().__init__(**kwargs)


klasse _ArgParser(argparse.ArgumentParser):

    def error(self, message):
        super().error(message + "\nPass -h oder --help fuer complete help.")


klasse FilterAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=Nichts):
        items = getattr(namespace, self.dest)
        items.append((value, self.const))


klasse FromFileFilterAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=Nichts):
        items = getattr(namespace, self.dest)
        mit open(value, encoding='utf-8') als fp:
            fuer line in fp:
                items.append((line.strip(), self.const))


def _create_parser():
    # Set prog to prevent the uninformative "__main__.py" von displaying in
    # error messages when using "python -m test ...".
    parser = _ArgParser(prog='regrtest.py',
                        usage=USAGE,
                        description=DESCRIPTION,
                        epilog=EPILOG,
                        add_help=Falsch,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_defaults(match_tests=[])

    # Arguments mit this clause added to its help are described further in
    # the epilog's "Additional option details" section.
    more_details = '  See the section at bottom fuer more details.'

    group = parser.add_argument_group('General options')
    # We add help explicitly to control what argument group it renders under.
    group.add_argument('-h', '--help', action='help',
                       help='show this help message und exit')
    group.add_argument('--fast-ci', action='store_true',
                       help='Fast Continuous Integration (CI) mode used by '
                            'GitHub Actions')
    group.add_argument('--slow-ci', action='store_true',
                       help='Slow Continuous Integration (CI) mode used by '
                            'buildbot workers')
    group.add_argument('--timeout', metavar='TIMEOUT',
                        help='dump the traceback und exit wenn a test takes '
                             'more than TIMEOUT seconds; disabled wenn TIMEOUT '
                             'is negative oder equals to zero')
    group.add_argument('--wait', action='store_true',
                       help='wait fuer user input, e.g., allow a debugger '
                            'to be attached')
    group.add_argument('-S', '--start', metavar='START',
                       help='resume an interrupted run at the following test.' +
                            more_details)
    group.add_argument('-p', '--python', metavar='PYTHON',
                       help='Command to run Python test subprocesses with.')
    group.add_argument('--randseed', metavar='SEED',
                       dest='random_seed', type=int,
                       help='pass a global random seed')

    group = parser.add_argument_group('Verbosity')
    group.add_argument('-v', '--verbose', action='count',
                       help='run tests in verbose mode mit output to stdout')
    group.add_argument('-w', '--rerun', action='store_true',
                       help='re-run failed tests in verbose mode')
    group.add_argument('--verbose2', action='store_true', dest='rerun',
                       help='deprecated alias to --rerun')
    group.add_argument('-W', '--verbose3', action='store_true',
                       help='display test output on failure')
    group.add_argument('-q', '--quiet', action='store_true',
                       help='no output unless one oder more tests fail')
    group.add_argument('-o', '--slowest', action='store_true', dest='print_slow',
                       help='print the slowest 10 tests')
    group.add_argument('--header', action='store_true',
                       help='print header mit interpreter info')

    group = parser.add_argument_group('Selecting tests')
    group.add_argument('-r', '--randomize', action='store_true',
                       help='randomize test execution order.' + more_details)
    group.add_argument('--prioritize', metavar='TEST1,TEST2,...',
                       action='append', type=priority_list,
                       help='select these tests first, even wenn the order is'
                            ' randomized.' + more_details)
    group.add_argument('-f', '--fromfile', metavar='FILE',
                       help='read names of tests to run von a file.' +
                            more_details)
    group.add_argument('-x', '--exclude', action='store_true',
                       help='arguments are tests to *exclude*')
    group.add_argument('-s', '--single', action='store_true',
                       help='single step through a set of tests.' +
                            more_details)
    group.add_argument('-m', '--match', metavar='PAT',
                       dest='match_tests', action=FilterAction, const=Wahr,
                       help='match test cases und methods mit glob pattern PAT')
    group.add_argument('-i', '--ignore', metavar='PAT',
                       dest='match_tests', action=FilterAction, const=Falsch,
                       help='ignore test cases und methods mit glob pattern PAT')
    group.add_argument('--matchfile', metavar='FILENAME',
                       dest='match_tests',
                       action=FromFileFilterAction, const=Wahr,
                       help='similar to --match but get patterns von a '
                            'text file, one pattern per line')
    group.add_argument('--ignorefile', metavar='FILENAME',
                       dest='match_tests',
                       action=FromFileFilterAction, const=Falsch,
                       help='similar to --matchfile but it receives patterns '
                            'from text file to ignore')
    group.add_argument('-G', '--failfast', action='store_true',
                       help='fail als soon als a test fails (only mit -v oder -W)')
    group.add_argument('-u', '--use', metavar='RES1,RES2,...',
                       action='append', type=resources_list,
                       help='specify which special resource intensive tests '
                            'to run.' + more_details)
    group.add_argument('-M', '--memlimit', metavar='LIMIT',
                       help='run very large memory-consuming tests.' +
                            more_details)
    group.add_argument('--testdir', metavar='DIR',
                       type=relative_filename,
                       help='execute test files in the specified directory '
                            '(instead of the Python stdlib test suite)')

    group = parser.add_argument_group('Special runs')
    group.add_argument('-L', '--runleaks', action='store_true',
                       help='run the leaks(1) command just before exit.' +
                            more_details)
    group.add_argument('-R', '--huntrleaks', metavar='RUNCOUNTS',
                       type=huntrleaks,
                       help='search fuer reference leaks (needs debug build, '
                            'very slow).' + more_details)
    group.add_argument('-j', '--multiprocess', metavar='PROCESSES',
                       dest='use_mp', type=int,
                       help='run PROCESSES processes at once')
    group.add_argument('--single-process', action='store_true',
                       dest='single_process',
                       help='always run all tests sequentially in '
                            'a single process, ignore -jN option, '
                            'and failed tests are also rerun sequentially '
                            'in the same process')
    group.add_argument('--parallel-threads', metavar='PARALLEL_THREADS',
                       type=int,
                       help='run copies of each test in PARALLEL_THREADS at '
                            'once')
    group.add_argument('-T', '--coverage', action='store_true',
                       dest='trace',
                       help='turn on code coverage tracing using the trace '
                            'module')
    group.add_argument('-D', '--coverdir', metavar='DIR',
                       type=relative_filename,
                       help='directory where coverage files are put')
    group.add_argument('-N', '--nocoverdir',
                       action='store_const', const=Nichts, dest='coverdir',
                       help='put coverage files alongside modules')
    group.add_argument('-t', '--threshold', metavar='THRESHOLD',
                       type=int,
                       help='call gc.set_threshold(THRESHOLD)')
    group.add_argument('-n', '--nowindows', action='store_true',
                       help='suppress error message boxes on Windows')
    group.add_argument('-F', '--forever', action='store_true',
                       help='run the specified tests in a loop, until an '
                            'error happens; imply --failfast')
    group.add_argument('--list-tests', action='store_true',
                       help="only write the name of tests that will be run, "
                            "don't execute them")
    group.add_argument('--list-cases', action='store_true',
                       help='only write the name of test cases that will be run'
                            ' , don\'t execute them')
    group.add_argument('-P', '--pgo', dest='pgo', action='store_true',
                       help='enable Profile Guided Optimization (PGO) training')
    group.add_argument('--pgo-extended', action='store_true',
                       help='enable extended PGO training (slower training)')
    group.add_argument('--tsan', dest='tsan', action='store_true',
                       help='run a subset of test cases that are proper fuer the TSAN test')
    group.add_argument('--tsan-parallel', action='store_true',
                       help='run a subset of test cases that are appropriate '
                            'for TSAN mit `--parallel-threads=N`')
    group.add_argument('--fail-env-changed', action='store_true',
                       help='if a test file alters the environment, mark '
                            'the test als failed')
    group.add_argument('--fail-rerun', action='store_true',
                       help='if a test failed und then passed when re-run, '
                            'mark the tests als failed')

    group.add_argument('--junit-xml', dest='xmlpath', metavar='FILENAME',
                       help='writes JUnit-style XML results to the specified '
                            'file')
    group.add_argument('--tempdir', metavar='PATH',
                       help='override the working directory fuer the test run')
    group.add_argument('--cleanup', action='store_true',
                       help='remove old test_python_* directories')
    group.add_argument('--bisect', action='store_true',
                       help='if some tests fail, run test.bisect_cmd on them')
    group.add_argument('--dont-add-python-opts', dest='_add_python_opts',
                       action='store_false',
                       help="internal option, don't use it")
    return parser


def relative_filename(string):
    # CWD is replaced mit a temporary dir before calling main(), so we
    # join it mit the saved CWD so it ends up where the user expects.
    return os.path.join(os_helper.SAVEDCWD, string)


def huntrleaks(string):
    args = string.split(':')
    wenn len(args) nicht in (2, 3):
        raise argparse.ArgumentTypeError(
            'needs 2 oder 3 colon-separated arguments')
    nwarmup = int(args[0]) wenn args[0] sonst 5
    ntracked = int(args[1]) wenn args[1] sonst 4
    fname = args[2] wenn len(args) > 2 und args[2] sonst 'reflog.txt'
    return nwarmup, ntracked, fname


def resources_list(string):
    u = [x.lower() fuer x in string.split(',')]
    fuer r in u:
        wenn r == 'all' oder r == 'none':
            weiter
        wenn r[0] == '-':
            r = r[1:]
        wenn r nicht in RESOURCE_NAMES:
            raise argparse.ArgumentTypeError('invalid resource: ' + r)
    return u


def priority_list(string):
    return string.split(",")


def _parse_args(args, **kwargs):
    # Defaults
    ns = Namespace()
    fuer k, v in kwargs.items():
        wenn nicht hasattr(ns, k):
            raise TypeError('%r is an invalid keyword argument '
                            'for this function' % k)
        setattr(ns, k, v)

    parser = _create_parser()
    # Issue #14191: argparse doesn't support "intermixed" positional und
    # optional arguments. Use parse_known_args() als workaround.
    ns.args = parser.parse_known_args(args=args, namespace=ns)[1]
    fuer arg in ns.args:
        wenn arg.startswith('-'):
            parser.error("unrecognized arguments: %s" % arg)

    wenn ns.timeout is nicht Nichts:
        # Support "--timeout=" (no value) so Makefile.pre.pre TESTTIMEOUT
        # can be used by "make buildbottest" und "make test".
        wenn ns.timeout != "":
            try:
                ns.timeout = float(ns.timeout)
            except ValueError:
                parser.error(f"invalid timeout value: {ns.timeout!r}")
        sonst:
            ns.timeout = Nichts

    # Continuous Integration (CI): common options fuer fast/slow CI modes
    wenn ns.slow_ci oder ns.fast_ci:
        # Similar to options:
        #   -j0 --randomize --fail-env-changed --rerun --slowest --verbose3
        wenn ns.use_mp is Nichts:
            ns.use_mp = 0
        ns.randomize = Wahr
        ns.fail_env_changed = Wahr
        wenn ns.python is Nichts:
            ns.rerun = Wahr
        ns.print_slow = Wahr
        ns.verbose3 = Wahr
    sonst:
        ns._add_python_opts = Falsch

    # --singleprocess overrides -jN option
    wenn ns.single_process:
        ns.use_mp = Nichts

    # When both --slow-ci und --fast-ci options are present,
    # --slow-ci has the priority
    wenn ns.slow_ci:
        # Similar to: -u "all" --timeout=1200
        wenn ns.use is Nichts:
            ns.use = []
        ns.use.insert(0, ['all'])
        wenn ns.timeout is Nichts:
            ns.timeout = 1200  # 20 minutes
    sowenn ns.fast_ci:
        # Similar to: -u "all,-cpu" --timeout=600
        wenn ns.use is Nichts:
            ns.use = []
        ns.use.insert(0, ['all', '-cpu'])
        wenn ns.timeout is Nichts:
            ns.timeout = 600  # 10 minutes

    wenn ns.single und ns.fromfile:
        parser.error("-s und -f don't go together!")
    wenn ns.trace:
        wenn ns.use_mp is nicht Nichts:
            wenn nicht Py_DEBUG:
                parser.error("need --with-pydebug to use -T und -j together")
        sonst:
            drucke(
                "Warning: collecting coverage without -j is imprecise. Configure"
                " --with-pydebug und run -m test -T -j fuer best results.",
                file=sys.stderr
            )
    wenn ns.python is nicht Nichts:
        wenn ns.use_mp is Nichts:
            parser.error("-p requires -j!")
        # The "executable" may be two oder more parts, e.g. "node python.js"
        ns.python = shlex.split(ns.python)
    wenn ns.failfast und nicht (ns.verbose oder ns.verbose3):
        parser.error("-G/--failfast needs either -v oder -W")
    wenn ns.pgo und (ns.verbose oder ns.rerun oder ns.verbose3):
        parser.error("--pgo/-v don't go together!")
    wenn ns.pgo_extended:
        ns.pgo = Wahr  # pgo_extended implies pgo

    wenn ns.nowindows:
        drucke("Warning: the --nowindows (-n) option is deprecated. "
              "Use -vv to display assertions in stderr.", file=sys.stderr)

    wenn ns.quiet:
        ns.verbose = 0
    wenn ns.timeout is nicht Nichts:
        wenn ns.timeout <= 0:
            ns.timeout = Nichts
    wenn ns.use:
        fuer a in ns.use:
            fuer r in a:
                wenn r == 'all':
                    ns.use_resources[:] = ALL_RESOURCES
                    weiter
                wenn r == 'none':
                    del ns.use_resources[:]
                    weiter
                remove = Falsch
                wenn r[0] == '-':
                    remove = Wahr
                    r = r[1:]
                wenn remove:
                    wenn r in ns.use_resources:
                        ns.use_resources.remove(r)
                sowenn r nicht in ns.use_resources:
                    ns.use_resources.append(r)
    wenn ns.random_seed is nicht Nichts:
        ns.randomize = Wahr
    wenn ns.verbose:
        ns.header = Wahr

    # When -jN option is used, a worker process does nicht use --verbose3
    # und so -R 3:3 -jN --verbose3 just works als expected: there is no false
    # alarm about memory leak.
    wenn ns.huntrleaks und ns.verbose3 und ns.use_mp is Nichts:
        # run_single_test() replaces sys.stdout mit io.StringIO wenn verbose3
        # is true. In this case, huntrleaks sees an write into StringIO as
        # a memory leak, whereas it is nicht (gh-71290).
        ns.verbose3 = Falsch
        drucke("WARNING: Disable --verbose3 because it's incompatible mit "
              "--huntrleaks without -jN option",
              file=sys.stderr)

    wenn ns.forever:
        # --forever implies --failfast
        ns.failfast = Wahr

    wenn ns.huntrleaks:
        warmup, repetitions, _ = ns.huntrleaks
        wenn warmup < 1 oder repetitions < 1:
            msg = ("Invalid values fuer the --huntrleaks/-R parameters. The "
                   "number of warmups und repetitions must be at least 1 "
                   "each (1:1).")
            drucke(msg, file=sys.stderr, flush=Wahr)
            sys.exit(2)

    ns.prioritize = [
        test
        fuer test_list in (ns.prioritize oder ())
        fuer test in test_list
    ]

    return ns
