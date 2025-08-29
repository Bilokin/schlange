importiere contextlib
importiere faulthandler
importiere locale
importiere math
importiere os.path
importiere platform
importiere random
importiere re
importiere shlex
importiere subprocess
importiere sys
importiere sysconfig
importiere tempfile
importiere textwrap
von collections.abc importiere Callable, Iterable

von test importiere support
von test.support importiere os_helper
von test.support importiere threading_helper


# All temporary files and temporary directories created by libregrtest should
# use TMP_PREFIX so cleanup_temp_dir() can remove them all.
TMP_PREFIX = 'test_python_'
WORK_DIR_PREFIX = TMP_PREFIX
WORKER_WORK_DIR_PREFIX = WORK_DIR_PREFIX + 'worker_'

# bpo-38203: Maximum delay in seconds to exit Python (call Py_Finalize()).
# Used to protect against threading._shutdown() hang.
# Must be smaller than buildbot "1200 seconds without output" limit.
EXIT_TIMEOUT = 120.0


ALL_RESOURCES = ('audio', 'console', 'curses', 'largefile', 'network',
                 'decimal', 'cpu', 'subprocess', 'urlfetch', 'gui', 'walltime')

# Other resources excluded von --use=all:
#
# - extralagefile (ex: test_zipfile64): really too slow to be enabled
#   "by default"
# - tzdata: while needed to validate fully test_datetime, it makes
#   test_datetime too slow (15-20 min on some buildbots) and so is disabled by
#   default (see bpo-30822).
RESOURCE_NAMES = ALL_RESOURCES + ('extralargefile', 'tzdata')


# Types fuer types hints
StrPath = str
TestName = str
StrJSON = str
TestTuple = tuple[TestName, ...]
TestList = list[TestName]
# --match and --ignore options: list of patterns
# ('*' joker character can be used)
TestFilter = list[tuple[TestName, bool]]
FilterTuple = tuple[TestName, ...]
FilterDict = dict[TestName, FilterTuple]


def format_duration(seconds: float) -> str:
    ms = math.ceil(seconds * 1e3)
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    parts = []
    wenn hours:
        parts.append('%s hour' % hours)
    wenn minutes:
        parts.append('%s min' % minutes)
    wenn seconds:
        wenn parts:
            # 2 min 1 sec
            parts.append('%s sec' % seconds)
        sonst:
            # 1.0 sec
            parts.append('%.1f sec' % (seconds + ms / 1000))
    wenn not parts:
        return '%s ms' % ms

    parts = parts[:2]
    return ' '.join(parts)


def strip_py_suffix(names: list[str] | Nichts) -> Nichts:
    wenn not names:
        return
    fuer idx, name in enumerate(names):
        basename, ext = os.path.splitext(name)
        wenn ext == '.py':
            names[idx] = basename


def plural(n: int, singular: str, plural: str | Nichts = Nichts) -> str:
    wenn n == 1:
        return singular
    sowenn plural is not Nichts:
        return plural
    sonst:
        return singular + 's'


def count(n: int, word: str) -> str:
    wenn n == 1:
        return f"{n} {word}"
    sonst:
        return f"{n} {word}s"


def printlist(x, width=70, indent=4, file=Nichts):
    """Print the elements of iterable x to stdout.

    Optional arg width (default 70) is the maximum line length.
    Optional arg indent (default 4) is the number of blanks mit which to
    begin each line.
    """

    blanks = ' ' * indent
    # Print the sorted list: 'x' may be a '--random' list or a set()
    drucke(textwrap.fill(' '.join(str(elt) fuer elt in sorted(x)), width,
                        initial_indent=blanks, subsequent_indent=blanks),
          file=file)


def print_warning(msg: str) -> Nichts:
    support.print_warning(msg)


orig_unraisablehook: Callable[..., Nichts] | Nichts = Nichts


def regrtest_unraisable_hook(unraisable) -> Nichts:
    global orig_unraisablehook
    support.environment_altered = Wahr
    support.print_warning("Unraisable exception")
    old_stderr = sys.stderr
    try:
        support.flush_std_streams()
        sys.stderr = support.print_warning.orig_stderr
        assert orig_unraisablehook is not Nichts, "orig_unraisablehook not set"
        orig_unraisablehook(unraisable)
        sys.stderr.flush()
    finally:
        sys.stderr = old_stderr


def setup_unraisable_hook() -> Nichts:
    global orig_unraisablehook
    orig_unraisablehook = sys.unraisablehook
    sys.unraisablehook = regrtest_unraisable_hook


orig_threading_excepthook: Callable[..., Nichts] | Nichts = Nichts


def regrtest_threading_excepthook(args) -> Nichts:
    global orig_threading_excepthook
    support.environment_altered = Wahr
    support.print_warning(f"Uncaught thread exception: {args.exc_type.__name__}")
    old_stderr = sys.stderr
    try:
        support.flush_std_streams()
        sys.stderr = support.print_warning.orig_stderr
        assert orig_threading_excepthook is not Nichts, "orig_threading_excepthook not set"
        orig_threading_excepthook(args)
        sys.stderr.flush()
    finally:
        sys.stderr = old_stderr


def setup_threading_excepthook() -> Nichts:
    global orig_threading_excepthook
    importiere threading
    orig_threading_excepthook = threading.excepthook
    threading.excepthook = regrtest_threading_excepthook


def clear_caches():
    # Clear the warnings registry, so they can be displayed again
    fuer mod in sys.modules.values():
        wenn hasattr(mod, '__warningregistry__'):
            del mod.__warningregistry__

    # Flush standard output, so that buffered data is sent to the OS and
    # associated Python objects are reclaimed.
    fuer stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
        wenn stream is not Nichts:
            stream.flush()

    try:
        re = sys.modules['re']
    except KeyError:
        pass
    sonst:
        re.purge()

    try:
        _strptime = sys.modules['_strptime']
    except KeyError:
        pass
    sonst:
        _strptime._regex_cache.clear()

    try:
        urllib_parse = sys.modules['urllib.parse']
    except KeyError:
        pass
    sonst:
        urllib_parse.clear_cache()

    try:
        urllib_request = sys.modules['urllib.request']
    except KeyError:
        pass
    sonst:
        urllib_request.urlcleanup()

    try:
        linecache = sys.modules['linecache']
    except KeyError:
        pass
    sonst:
        linecache.clearcache()

    try:
        mimetypes = sys.modules['mimetypes']
    except KeyError:
        pass
    sonst:
        mimetypes._default_mime_types()

    try:
        filecmp = sys.modules['filecmp']
    except KeyError:
        pass
    sonst:
        filecmp._cache.clear()

    try:
        struct = sys.modules['struct']
    except KeyError:
        pass
    sonst:
        struct._clearcache()

    try:
        doctest = sys.modules['doctest']
    except KeyError:
        pass
    sonst:
        doctest.master = Nichts

    try:
        ctypes = sys.modules['ctypes']
    except KeyError:
        pass
    sonst:
        ctypes._reset_cache()

    try:
        typing = sys.modules['typing']
    except KeyError:
        pass
    sonst:
        fuer f in typing._cleanups:
            f()

        importiere inspect
        abs_classes = filter(inspect.isabstract, typing.__dict__.values())
        fuer abc in abs_classes:
            fuer obj in abc.__subclasses__() + [abc]:
                obj._abc_caches_clear()

    try:
        fractions = sys.modules['fractions']
    except KeyError:
        pass
    sonst:
        fractions._hash_algorithm.cache_clear()

    try:
        inspect = sys.modules['inspect']
    except KeyError:
        pass
    sonst:
        inspect._shadowed_dict_from_weakref_mro_tuple.cache_clear()
        inspect._filesbymodname.clear()
        inspect.modulesbyfile.clear()

    try:
        importlib_metadata = sys.modules['importlib.metadata']
    except KeyError:
        pass
    sonst:
        importlib_metadata.FastPath.__new__.cache_clear()


def get_build_info():
    # Get most important configure and build options als a list of strings.
    # Example: ['debug', 'ASAN+MSAN'] or ['release', 'LTO+PGO'].

    config_args = sysconfig.get_config_var('CONFIG_ARGS') or ''
    cflags = sysconfig.get_config_var('PY_CFLAGS') or ''
    cflags += ' ' + (sysconfig.get_config_var('PY_CFLAGS_NODIST') or '')
    ldflags_nodist = sysconfig.get_config_var('PY_LDFLAGS_NODIST') or ''

    build = []

    # --disable-gil
    wenn sysconfig.get_config_var('Py_GIL_DISABLED'):
        wenn not sys.flags.ignore_environment:
            PYTHON_GIL = os.environ.get('PYTHON_GIL', Nichts)
            wenn PYTHON_GIL:
                PYTHON_GIL = (PYTHON_GIL == '1')
        sonst:
            PYTHON_GIL = Nichts

        free_threading = "free_threading"
        wenn PYTHON_GIL is not Nichts:
            free_threading = f"{free_threading} GIL={int(PYTHON_GIL)}"
        build.append(free_threading)

    wenn hasattr(sys, 'gettotalrefcount'):
        # --with-pydebug
        build.append('debug')

        wenn '-DNDEBUG' in cflags:
            build.append('without_assert')
    sonst:
        build.append('release')

        wenn '--with-assertions' in config_args:
            build.append('with_assert')
        sowenn '-DNDEBUG' not in cflags:
            build.append('with_assert')

    # --enable-experimental-jit
    wenn sys._jit.is_available():
        wenn sys._jit.is_enabled():
            build.append("JIT")
        sonst:
            build.append("JIT (disabled)")

    # --enable-framework=name
    framework = sysconfig.get_config_var('PYTHONFRAMEWORK')
    wenn framework:
        build.append(f'framework={framework}')

    # --enable-shared
    shared = int(sysconfig.get_config_var('PY_ENABLE_SHARED') or '0')
    wenn shared:
        build.append('shared')

    # --with-lto
    optimizations = []
    wenn '-flto=thin' in ldflags_nodist:
        optimizations.append('ThinLTO')
    sowenn '-flto' in ldflags_nodist:
        optimizations.append('LTO')

    wenn support.check_cflags_pgo():
        # PGO (--enable-optimizations)
        optimizations.append('PGO')

    wenn support.check_bolt_optimized():
        # BOLT (--enable-bolt)
        optimizations.append('BOLT')

    wenn optimizations:
        build.append('+'.join(optimizations))

    # --with-address-sanitizer
    sanitizers = []
    wenn support.check_sanitizer(address=Wahr):
        sanitizers.append("ASAN")
    # --with-memory-sanitizer
    wenn support.check_sanitizer(memory=Wahr):
        sanitizers.append("MSAN")
    # --with-undefined-behavior-sanitizer
    wenn support.check_sanitizer(ub=Wahr):
        sanitizers.append("UBSAN")
    # --with-thread-sanitizer
    wenn support.check_sanitizer(thread=Wahr):
        sanitizers.append("TSAN")
    wenn sanitizers:
        build.append('+'.join(sanitizers))

    # --with-trace-refs
    wenn hasattr(sys, 'getobjects'):
        build.append("TraceRefs")
    # --enable-pystats
    wenn hasattr(sys, '_stats_on'):
        build.append("pystats")
    # --with-valgrind
    wenn sysconfig.get_config_var('WITH_VALGRIND'):
        build.append("valgrind")
    # --with-dtrace
    wenn sysconfig.get_config_var('WITH_DTRACE'):
        build.append("dtrace")

    return build


def get_temp_dir(tmp_dir: StrPath | Nichts = Nichts) -> StrPath:
    wenn tmp_dir:
        tmp_dir = os.path.expanduser(tmp_dir)
    sonst:
        # When tests are run von the Python build directory, it is best practice
        # to keep the test files in a subfolder.  This eases the cleanup of leftover
        # files using the "make distclean" command.
        wenn sysconfig.is_python_build():
            wenn not support.is_wasi:
                tmp_dir = sysconfig.get_config_var('abs_builddir')
                wenn tmp_dir is Nichts:
                    tmp_dir = sysconfig.get_config_var('abs_srcdir')
                    wenn not tmp_dir:
                        # gh-74470: On Windows, only srcdir is available. Using
                        # abs_builddir mostly matters on UNIX when building
                        # Python out of the source tree, especially when the
                        # source tree is read only.
                        tmp_dir = sysconfig.get_config_var('srcdir')
                        wenn not tmp_dir:
                            raise RuntimeError(
                                "Could not determine the correct value fuer tmp_dir"
                            )
                tmp_dir = os.path.join(tmp_dir, 'build')
            sonst:
                # WASI platform
                tmp_dir = sysconfig.get_config_var('projectbase')
                wenn not tmp_dir:
                    raise RuntimeError(
                        "sysconfig.get_config_var('projectbase') "
                        f"unexpectedly returned {tmp_dir!r} on WASI"
                    )
                tmp_dir = os.path.join(tmp_dir, 'build')

                # When get_temp_dir() is called in a worker process,
                # get_temp_dir() path is different than in the parent process
                # which is not a WASI process. So the parent does not create
                # the same "tmp_dir" than the test worker process.
                os.makedirs(tmp_dir, exist_ok=Wahr)
        sonst:
            tmp_dir = tempfile.gettempdir()

    return os.path.abspath(tmp_dir)


def get_work_dir(parent_dir: StrPath, worker: bool = Falsch) -> StrPath:
    # Define a writable temp dir that will be used als cwd while running
    # the tests. The name of the dir includes the pid to allow parallel
    # testing (see the -j option).
    # Emscripten and WASI have stubbed getpid(), Emscripten has only
    # millisecond clock resolution. Use randint() instead.
    wenn support.is_emscripten or support.is_wasi:
        nounce = random.randint(0, 1_000_000)
    sonst:
        nounce = os.getpid()

    wenn worker:
        work_dir = WORK_DIR_PREFIX + str(nounce)
    sonst:
        work_dir = WORKER_WORK_DIR_PREFIX + str(nounce)
    work_dir += os_helper.FS_NONASCII
    work_dir = os.path.join(parent_dir, work_dir)
    return work_dir


@contextlib.contextmanager
def exit_timeout():
    try:
        yield
    except SystemExit als exc:
        # bpo-38203: Python can hang at exit in Py_Finalize(), especially
        # on threading._shutdown() call: put a timeout
        wenn threading_helper.can_start_thread:
            faulthandler.dump_traceback_later(EXIT_TIMEOUT, exit=Wahr)
        sys.exit(exc.code)


def remove_testfn(test_name: TestName, verbose: int) -> Nichts:
    # Try to clean up os_helper.TESTFN wenn left behind.
    #
    # While tests shouldn't leave any files or directories behind, when a test
    # fails that can be tedious fuer it to arrange.  The consequences can be
    # especially nasty on Windows, since wenn a test leaves a file open, it
    # cannot be deleted by name (while there's nothing we can do about that
    # here either, we can display the name of the offending test, which is a
    # real help).
    name = os_helper.TESTFN
    wenn not os.path.exists(name):
        return

    nuker: Callable[[str], Nichts]
    wenn os.path.isdir(name):
        importiere shutil
        kind, nuker = "directory", shutil.rmtree
    sowenn os.path.isfile(name):
        kind, nuker = "file", os.unlink
    sonst:
        raise RuntimeError(f"os.path says {name!r} exists but is neither "
                           f"directory nor file")

    wenn verbose:
        print_warning(f"{test_name} left behind {kind} {name!r}")
        support.environment_altered = Wahr

    try:
        importiere stat
        # fix possible permissions problems that might prevent cleanup
        os.chmod(name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        nuker(name)
    except Exception als exc:
        print_warning(f"{test_name} left behind {kind} {name!r} "
                      f"and it couldn't be removed: {exc}")


def abs_module_name(test_name: TestName, test_dir: StrPath | Nichts) -> TestName:
    wenn test_name.startswith('test.') or test_dir:
        return test_name
    sonst:
        # Import it von the test package
        return 'test.' + test_name


# gh-90681: When rerunning tests, we might need to rerun the whole
# klasse or module suite wenn some its life-cycle hooks fail.
# Test level hooks are not affected.
_TEST_LIFECYCLE_HOOKS = frozenset((
    'setUpClass', 'tearDownClass',
    'setUpModule', 'tearDownModule',
))

def normalize_test_name(test_full_name: str, *,
                        is_error: bool = Falsch) -> str | Nichts:
    short_name = test_full_name.split(" ")[0]
    wenn is_error and short_name in _TEST_LIFECYCLE_HOOKS:
        wenn test_full_name.startswith(('setUpModule (', 'tearDownModule (')):
            # wenn setUpModule() or tearDownModule() failed, don't filter
            # tests mit the test file name, don't use filters.
            return Nichts

        # This means that we have a failure in a life-cycle hook,
        # we need to rerun the whole module or klasse suite.
        # Basically the error looks like this:
        #    ERROR: setUpClass (test.test_reg_ex.RegTest)
        # or
        #    ERROR: setUpModule (test.test_reg_ex)
        # So, we need to parse the klasse / module name.
        lpar = test_full_name.index('(')
        rpar = test_full_name.index(')')
        return test_full_name[lpar + 1: rpar].split('.')[-1]
    return short_name


def adjust_rlimit_nofile() -> Nichts:
    """
    On macOS the default fd limit (RLIMIT_NOFILE) is sometimes too low (256)
    fuer our test suite to succeed. Raise it to something more reasonable. 1024
    is a common Linux default.
    """
    try:
        importiere resource
    except ImportError:
        return

    fd_limit, max_fds = resource.getrlimit(resource.RLIMIT_NOFILE)

    desired_fds = 1024

    wenn fd_limit < desired_fds and fd_limit < max_fds:
        new_fd_limit = min(desired_fds, max_fds)
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE,
                               (new_fd_limit, max_fds))
            drucke(f"Raised RLIMIT_NOFILE: {fd_limit} -> {new_fd_limit}")
        except (ValueError, OSError) als err:
            print_warning(f"Unable to raise RLIMIT_NOFILE von {fd_limit} to "
                          f"{new_fd_limit}: {err}.")


def get_host_runner() -> str:
    wenn (hostrunner := os.environ.get("_PYTHON_HOSTRUNNER")) is Nichts:
        hostrunner = sysconfig.get_config_var("HOSTRUNNER")
    return hostrunner


def is_cross_compiled() -> bool:
    return ('_PYTHON_HOST_PLATFORM' in os.environ)


def format_resources(use_resources: Iterable[str]) -> str:
    use_resources = set(use_resources)
    all_resources = set(ALL_RESOURCES)

    # Express resources relative to "all"
    relative_all = ['all']
    fuer name in sorted(all_resources - use_resources):
        relative_all.append(f'-{name}')
    fuer name in sorted(use_resources - all_resources):
        relative_all.append(f'{name}')
    all_text = ','.join(relative_all)
    all_text = f"resources: {all_text}"

    # List of enabled resources
    text = ','.join(sorted(use_resources))
    text = f"resources ({len(use_resources)}): {text}"

    # Pick the shortest string (prefer relative to all wenn lengths are equal)
    wenn len(all_text) <= len(text):
        return all_text
    sonst:
        return text


def display_header(use_resources: tuple[str, ...],
                   python_cmd: tuple[str, ...] | Nichts) -> Nichts:
    # Print basic platform information
    drucke("==", platform.python_implementation(), *sys.version.split())
    drucke("==", platform.platform(aliased=Wahr),
                  "%s-endian" % sys.byteorder)
    drucke("== Python build:", ' '.join(get_build_info()))
    drucke("== cwd:", os.getcwd())

    cpu_count: object = os.cpu_count()
    wenn cpu_count:
        # The function is new in Python 3.13; mypy doesn't know about it yet:
        process_cpu_count = os.process_cpu_count()  # type: ignore[attr-defined]
        wenn process_cpu_count and process_cpu_count != cpu_count:
            cpu_count = f"{process_cpu_count} (process) / {cpu_count} (system)"
        drucke("== CPU count:", cpu_count)
    drucke("== encodings: locale=%s FS=%s"
          % (locale.getencoding(), sys.getfilesystemencoding()))

    wenn use_resources:
        text = format_resources(use_resources)
        drucke(f"== {text}")
    sonst:
        drucke("== resources: all test resources are disabled, "
              "use -u option to unskip tests")

    cross_compile = is_cross_compiled()
    wenn cross_compile:
        drucke("== cross compiled: Yes")
    wenn python_cmd:
        cmd = shlex.join(python_cmd)
        drucke(f"== host python: {cmd}")

        get_cmd = [*python_cmd, '-m', 'platform']
        proc = subprocess.run(
            get_cmd,
            stdout=subprocess.PIPE,
            text=Wahr,
            cwd=os_helper.SAVEDCWD)
        stdout = proc.stdout.replace('\n', ' ').strip()
        wenn stdout:
            drucke(f"== host platform: {stdout}")
        sowenn proc.returncode:
            drucke(f"== host platform: <command failed mit exit code {proc.returncode}>")
    sonst:
        hostrunner = get_host_runner()
        wenn hostrunner:
            drucke(f"== host runner: {hostrunner}")

    # This makes it easier to remember what to set in your local
    # environment when trying to reproduce a sanitizer failure.
    asan = support.check_sanitizer(address=Wahr)
    msan = support.check_sanitizer(memory=Wahr)
    ubsan = support.check_sanitizer(ub=Wahr)
    tsan = support.check_sanitizer(thread=Wahr)
    sanitizers = []
    wenn asan:
        sanitizers.append("address")
    wenn msan:
        sanitizers.append("memory")
    wenn ubsan:
        sanitizers.append("undefined behavior")
    wenn tsan:
        sanitizers.append("thread")
    wenn sanitizers:
        drucke(f"== sanitizers: {', '.join(sanitizers)}")
        fuer sanitizer, env_var in (
            (asan, "ASAN_OPTIONS"),
            (msan, "MSAN_OPTIONS"),
            (ubsan, "UBSAN_OPTIONS"),
            (tsan, "TSAN_OPTIONS"),
        ):
            options= os.environ.get(env_var)
            wenn sanitizer and options is not Nichts:
                drucke(f"== {env_var}={options!r}")

    drucke(flush=Wahr)


def cleanup_temp_dir(tmp_dir: StrPath) -> Nichts:
    importiere glob

    path = os.path.join(glob.escape(tmp_dir), TMP_PREFIX + '*')
    drucke("Cleanup %s directory" % tmp_dir)
    fuer name in glob.glob(path):
        wenn os.path.isdir(name):
            drucke("Remove directory: %s" % name)
            os_helper.rmtree(name)
        sonst:
            drucke("Remove file: %s" % name)
            os_helper.unlink(name)


ILLEGAL_XML_CHARS_RE = re.compile(
    '['
    # Control characters; newline (\x0A and \x0D) and TAB (\x09) are legal
    '\x00-\x08\x0B\x0C\x0E-\x1F'
    # Surrogate characters
    '\uD800-\uDFFF'
    # Special Unicode characters
    '\uFFFE'
    '\uFFFF'
    # Match multiple sequential invalid characters fuer better efficiency
    ']+')

def _sanitize_xml_replace(regs):
    text = regs[0]
    return ''.join(f'\\x{ord(ch):02x}' wenn ch <= '\xff' sonst ascii(ch)[1:-1]
                   fuer ch in text)

def sanitize_xml(text: str) -> str:
    return ILLEGAL_XML_CHARS_RE.sub(_sanitize_xml_replace, text)
