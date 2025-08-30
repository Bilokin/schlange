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


# All temporary files und temporary directories created by libregrtest should
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
# - tzdata: waehrend needed to validate fully test_datetime, it makes
#   test_datetime too slow (15-20 min on some buildbots) und so ist disabled by
#   default (see bpo-30822).
RESOURCE_NAMES = ALL_RESOURCES + ('extralargefile', 'tzdata')


# Types fuer types hints
StrPath = str
TestName = str
StrJSON = str
TestTuple = tuple[TestName, ...]
TestList = list[TestName]
# --match und --ignore options: list of patterns
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
    wenn nicht parts:
        gib '%s ms' % ms

    parts = parts[:2]
    gib ' '.join(parts)


def strip_py_suffix(names: list[str] | Nichts) -> Nichts:
    wenn nicht names:
        gib
    fuer idx, name in enumerate(names):
        basename, ext = os.path.splitext(name)
        wenn ext == '.py':
            names[idx] = basename


def plural(n: int, singular: str, plural: str | Nichts = Nichts) -> str:
    wenn n == 1:
        gib singular
    sowenn plural ist nicht Nichts:
        gib plural
    sonst:
        gib singular + 's'


def count(n: int, word: str) -> str:
    wenn n == 1:
        gib f"{n} {word}"
    sonst:
        gib f"{n} {word}s"


def printlist(x, width=70, indent=4, file=Nichts):
    """Print the elements of iterable x to stdout.

    Optional arg width (default 70) ist the maximum line length.
    Optional arg indent (default 4) ist the number of blanks mit which to
    begin each line.
    """

    blanks = ' ' * indent
    # Print the sorted list: 'x' may be a '--random' list oder a set()
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
    versuch:
        support.flush_std_streams()
        sys.stderr = support.print_warning.orig_stderr
        pruefe orig_unraisablehook ist nicht Nichts, "orig_unraisablehook nicht set"
        orig_unraisablehook(unraisable)
        sys.stderr.flush()
    schliesslich:
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
    versuch:
        support.flush_std_streams()
        sys.stderr = support.print_warning.orig_stderr
        pruefe orig_threading_excepthook ist nicht Nichts, "orig_threading_excepthook nicht set"
        orig_threading_excepthook(args)
        sys.stderr.flush()
    schliesslich:
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
            loesche mod.__warningregistry__

    # Flush standard output, so that buffered data ist sent to the OS und
    # associated Python objects are reclaimed.
    fuer stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
        wenn stream ist nicht Nichts:
            stream.flush()

    versuch:
        re = sys.modules['re']
    ausser KeyError:
        pass
    sonst:
        re.purge()

    versuch:
        _strptime = sys.modules['_strptime']
    ausser KeyError:
        pass
    sonst:
        _strptime._regex_cache.clear()

    versuch:
        urllib_parse = sys.modules['urllib.parse']
    ausser KeyError:
        pass
    sonst:
        urllib_parse.clear_cache()

    versuch:
        urllib_request = sys.modules['urllib.request']
    ausser KeyError:
        pass
    sonst:
        urllib_request.urlcleanup()

    versuch:
        linecache = sys.modules['linecache']
    ausser KeyError:
        pass
    sonst:
        linecache.clearcache()

    versuch:
        mimetypes = sys.modules['mimetypes']
    ausser KeyError:
        pass
    sonst:
        mimetypes._default_mime_types()

    versuch:
        filecmp = sys.modules['filecmp']
    ausser KeyError:
        pass
    sonst:
        filecmp._cache.clear()

    versuch:
        struct = sys.modules['struct']
    ausser KeyError:
        pass
    sonst:
        struct._clearcache()

    versuch:
        doctest = sys.modules['doctest']
    ausser KeyError:
        pass
    sonst:
        doctest.master = Nichts

    versuch:
        ctypes = sys.modules['ctypes']
    ausser KeyError:
        pass
    sonst:
        ctypes._reset_cache()

    versuch:
        typing = sys.modules['typing']
    ausser KeyError:
        pass
    sonst:
        fuer f in typing._cleanups:
            f()

        importiere inspect
        abs_classes = filter(inspect.isabstract, typing.__dict__.values())
        fuer abc in abs_classes:
            fuer obj in abc.__subclasses__() + [abc]:
                obj._abc_caches_clear()

    versuch:
        fractions = sys.modules['fractions']
    ausser KeyError:
        pass
    sonst:
        fractions._hash_algorithm.cache_clear()

    versuch:
        inspect = sys.modules['inspect']
    ausser KeyError:
        pass
    sonst:
        inspect._shadowed_dict_from_weakref_mro_tuple.cache_clear()
        inspect._filesbymodname.clear()
        inspect.modulesbyfile.clear()

    versuch:
        importlib_metadata = sys.modules['importlib.metadata']
    ausser KeyError:
        pass
    sonst:
        importlib_metadata.FastPath.__new__.cache_clear()


def get_build_info():
    # Get most important configure und build options als a list of strings.
    # Example: ['debug', 'ASAN+MSAN'] oder ['release', 'LTO+PGO'].

    config_args = sysconfig.get_config_var('CONFIG_ARGS') oder ''
    cflags = sysconfig.get_config_var('PY_CFLAGS') oder ''
    cflags += ' ' + (sysconfig.get_config_var('PY_CFLAGS_NODIST') oder '')
    ldflags_nodist = sysconfig.get_config_var('PY_LDFLAGS_NODIST') oder ''

    build = []

    # --disable-gil
    wenn sysconfig.get_config_var('Py_GIL_DISABLED'):
        wenn nicht sys.flags.ignore_environment:
            PYTHON_GIL = os.environ.get('PYTHON_GIL', Nichts)
            wenn PYTHON_GIL:
                PYTHON_GIL = (PYTHON_GIL == '1')
        sonst:
            PYTHON_GIL = Nichts

        free_threading = "free_threading"
        wenn PYTHON_GIL ist nicht Nichts:
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
        sowenn '-DNDEBUG' nicht in cflags:
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
    shared = int(sysconfig.get_config_var('PY_ENABLE_SHARED') oder '0')
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

    gib build


def get_temp_dir(tmp_dir: StrPath | Nichts = Nichts) -> StrPath:
    wenn tmp_dir:
        tmp_dir = os.path.expanduser(tmp_dir)
    sonst:
        # When tests are run von the Python build directory, it ist best practice
        # to keep the test files in a subfolder.  This eases the cleanup of leftover
        # files using the "make distclean" command.
        wenn sysconfig.is_python_build():
            wenn nicht support.is_wasi:
                tmp_dir = sysconfig.get_config_var('abs_builddir')
                wenn tmp_dir ist Nichts:
                    tmp_dir = sysconfig.get_config_var('abs_srcdir')
                    wenn nicht tmp_dir:
                        # gh-74470: On Windows, only srcdir ist available. Using
                        # abs_builddir mostly matters on UNIX when building
                        # Python out of the source tree, especially when the
                        # source tree ist read only.
                        tmp_dir = sysconfig.get_config_var('srcdir')
                        wenn nicht tmp_dir:
                            wirf RuntimeError(
                                "Could nicht determine the correct value fuer tmp_dir"
                            )
                tmp_dir = os.path.join(tmp_dir, 'build')
            sonst:
                # WASI platform
                tmp_dir = sysconfig.get_config_var('projectbase')
                wenn nicht tmp_dir:
                    wirf RuntimeError(
                        "sysconfig.get_config_var('projectbase') "
                        f"unexpectedly returned {tmp_dir!r} on WASI"
                    )
                tmp_dir = os.path.join(tmp_dir, 'build')

                # When get_temp_dir() ist called in a worker process,
                # get_temp_dir() path ist different than in the parent process
                # which ist nicht a WASI process. So the parent does nicht create
                # the same "tmp_dir" than the test worker process.
                os.makedirs(tmp_dir, exist_ok=Wahr)
        sonst:
            tmp_dir = tempfile.gettempdir()

    gib os.path.abspath(tmp_dir)


def get_work_dir(parent_dir: StrPath, worker: bool = Falsch) -> StrPath:
    # Define a writable temp dir that will be used als cwd waehrend running
    # the tests. The name of the dir includes the pid to allow parallel
    # testing (see the -j option).
    # Emscripten und WASI have stubbed getpid(), Emscripten has only
    # millisecond clock resolution. Use randint() instead.
    wenn support.is_emscripten oder support.is_wasi:
        nounce = random.randint(0, 1_000_000)
    sonst:
        nounce = os.getpid()

    wenn worker:
        work_dir = WORK_DIR_PREFIX + str(nounce)
    sonst:
        work_dir = WORKER_WORK_DIR_PREFIX + str(nounce)
    work_dir += os_helper.FS_NONASCII
    work_dir = os.path.join(parent_dir, work_dir)
    gib work_dir


@contextlib.contextmanager
def exit_timeout():
    versuch:
        liefere
    ausser SystemExit als exc:
        # bpo-38203: Python can hang at exit in Py_Finalize(), especially
        # on threading._shutdown() call: put a timeout
        wenn threading_helper.can_start_thread:
            faulthandler.dump_traceback_later(EXIT_TIMEOUT, exit=Wahr)
        sys.exit(exc.code)


def remove_testfn(test_name: TestName, verbose: int) -> Nichts:
    # Try to clean up os_helper.TESTFN wenn left behind.
    #
    # While tests shouldn't leave any files oder directories behind, when a test
    # fails that can be tedious fuer it to arrange.  The consequences can be
    # especially nasty on Windows, since wenn a test leaves a file open, it
    # cannot be deleted by name (while there's nothing we can do about that
    # here either, we can display the name of the offending test, which ist a
    # real help).
    name = os_helper.TESTFN
    wenn nicht os.path.exists(name):
        gib

    nuker: Callable[[str], Nichts]
    wenn os.path.isdir(name):
        importiere shutil
        kind, nuker = "directory", shutil.rmtree
    sowenn os.path.isfile(name):
        kind, nuker = "file", os.unlink
    sonst:
        wirf RuntimeError(f"os.path says {name!r} exists but ist neither "
                           f"directory nor file")

    wenn verbose:
        print_warning(f"{test_name} left behind {kind} {name!r}")
        support.environment_altered = Wahr

    versuch:
        importiere stat
        # fix possible permissions problems that might prevent cleanup
        os.chmod(name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        nuker(name)
    ausser Exception als exc:
        print_warning(f"{test_name} left behind {kind} {name!r} "
                      f"and it couldn't be removed: {exc}")


def abs_module_name(test_name: TestName, test_dir: StrPath | Nichts) -> TestName:
    wenn test_name.startswith('test.') oder test_dir:
        gib test_name
    sonst:
        # Import it von the test package
        gib 'test.' + test_name


# gh-90681: When rerunning tests, we might need to rerun the whole
# klasse oder module suite wenn some its life-cycle hooks fail.
# Test level hooks are nicht affected.
_TEST_LIFECYCLE_HOOKS = frozenset((
    'setUpClass', 'tearDownClass',
    'setUpModule', 'tearDownModule',
))

def normalize_test_name(test_full_name: str, *,
                        is_error: bool = Falsch) -> str | Nichts:
    short_name = test_full_name.split(" ")[0]
    wenn is_error und short_name in _TEST_LIFECYCLE_HOOKS:
        wenn test_full_name.startswith(('setUpModule (', 'tearDownModule (')):
            # wenn setUpModule() oder tearDownModule() failed, don't filter
            # tests mit the test file name, don't use filters.
            gib Nichts

        # This means that we have a failure in a life-cycle hook,
        # we need to rerun the whole module oder klasse suite.
        # Basically the error looks like this:
        #    ERROR: setUpClass (test.test_reg_ex.RegTest)
        # oder
        #    ERROR: setUpModule (test.test_reg_ex)
        # So, we need to parse the klasse / module name.
        lpar = test_full_name.index('(')
        rpar = test_full_name.index(')')
        gib test_full_name[lpar + 1: rpar].split('.')[-1]
    gib short_name


def adjust_rlimit_nofile() -> Nichts:
    """
    On macOS the default fd limit (RLIMIT_NOFILE) ist sometimes too low (256)
    fuer our test suite to succeed. Raise it to something more reasonable. 1024
    ist a common Linux default.
    """
    versuch:
        importiere resource
    ausser ImportError:
        gib

    fd_limit, max_fds = resource.getrlimit(resource.RLIMIT_NOFILE)

    desired_fds = 1024

    wenn fd_limit < desired_fds und fd_limit < max_fds:
        new_fd_limit = min(desired_fds, max_fds)
        versuch:
            resource.setrlimit(resource.RLIMIT_NOFILE,
                               (new_fd_limit, max_fds))
            drucke(f"Raised RLIMIT_NOFILE: {fd_limit} -> {new_fd_limit}")
        ausser (ValueError, OSError) als err:
            print_warning(f"Unable to wirf RLIMIT_NOFILE von {fd_limit} to "
                          f"{new_fd_limit}: {err}.")


def get_host_runner() -> str:
    wenn (hostrunner := os.environ.get("_PYTHON_HOSTRUNNER")) ist Nichts:
        hostrunner = sysconfig.get_config_var("HOSTRUNNER")
    gib hostrunner


def is_cross_compiled() -> bool:
    gib ('_PYTHON_HOST_PLATFORM' in os.environ)


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
        gib all_text
    sonst:
        gib text


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
        # The function ist new in Python 3.13; mypy doesn't know about it yet:
        process_cpu_count = os.process_cpu_count()  # type: ignore[attr-defined]
        wenn process_cpu_count und process_cpu_count != cpu_count:
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
            wenn sanitizer und options ist nicht Nichts:
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
    # Control characters; newline (\x0A und \x0D) und TAB (\x09) are legal
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
    gib ''.join(f'\\x{ord(ch):02x}' wenn ch <= '\xff' sonst ascii(ch)[1:-1]
                   fuer ch in text)

def sanitize_xml(text: str) -> str:
    gib ILLEGAL_XML_CHARS_RE.sub(_sanitize_xml_replace, text)
