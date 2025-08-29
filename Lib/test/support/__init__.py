"""Supporting definitions fuer the Python regression tests."""

wenn __name__ != 'test.support':
    raise ImportError('support must be imported von the test package')

importiere annotationlib
importiere contextlib
importiere functools
importiere inspect
importiere logging
importiere _opcode
importiere os
importiere re
importiere stat
importiere sys
importiere sysconfig
importiere textwrap
importiere time
importiere types
importiere unittest
importiere warnings


__all__ = [
    # globals
    "PIPE_MAX_SIZE", "verbose", "max_memuse", "use_resources", "failfast",
    # exceptions
    "Error", "TestFailed", "TestDidNotRun", "ResourceDenied",
    # io
    "record_original_stdout", "get_original_stdout", "captured_stdout",
    "captured_stdin", "captured_stderr", "captured_output",
    # unittest
    "is_resource_enabled", "requires", "requires_freebsd_version",
    "requires_gil_enabled", "requires_linux_version", "requires_mac_ver",
    "check_syntax_error",
    "requires_gzip", "requires_bz2", "requires_lzma", "requires_zstd",
    "bigmemtest", "bigaddrspacetest", "cpython_only", "get_attribute",
    "requires_IEEE_754", "requires_zlib",
    "has_fork_support", "requires_fork",
    "has_subprocess_support", "requires_subprocess",
    "has_socket_support", "requires_working_socket",
    "anticipate_failure", "load_package_tests", "detect_api_mismatch",
    "check__all__", "skip_if_buggy_ucrt_strfptime",
    "check_disallow_instantiation", "check_sanitizer", "skip_if_sanitizer",
    "requires_limited_api", "requires_specialization", "thread_unsafe",
    # sys
    "MS_WINDOWS", "is_jython", "is_android", "is_emscripten", "is_wasi",
    "is_apple_mobile", "check_impl_detail", "unix_shell", "setswitchinterval",
    "support_remote_exec_only",
    # os
    "get_pagesize",
    # network
    "open_urlresource",
    # processes
    "reap_children",
    # miscellaneous
    "run_with_locale", "swap_item", "findfile", "infinite_recursion",
    "swap_attr", "Matcher", "set_memlimit", "SuppressCrashReport", "sortdict",
    "run_with_tz", "PGO", "missing_compiler_executable",
    "ALWAYS_EQ", "NEVER_EQ", "LARGEST", "SMALLEST",
    "LOOPBACK_TIMEOUT", "INTERNET_TIMEOUT", "SHORT_TIMEOUT", "LONG_TIMEOUT",
    "Py_DEBUG", "exceeds_recursion_limit", "skip_on_s390x",
    "requires_jit_enabled",
    "requires_jit_disabled",
    "force_not_colorized",
    "force_not_colorized_test_class",
    "make_clean_env",
    "BrokenIter",
    "in_systemd_nspawn_sync_suppressed",
    "run_no_yield_async_fn", "run_yielding_async_fn", "async_yield",
    "reset_code",
    ]


# Timeout in seconds fuer tests using a network server listening on the network
# local loopback interface like 127.0.0.1.
#
# The timeout is long enough to prevent test failure: it takes into account
# that the client und the server can run in different threads oder even different
# processes.
#
# The timeout should be long enough fuer connect(), recv() und send() methods
# of socket.socket.
LOOPBACK_TIMEOUT = 10.0

# Timeout in seconds fuer network requests going to the internet. The timeout is
# short enough to prevent a test to wait fuer too long wenn the internet request
# is blocked fuer whatever reason.
#
# Usually, a timeout using INTERNET_TIMEOUT should nicht mark a test als failed,
# but skip the test instead: see transient_internet().
INTERNET_TIMEOUT = 60.0

# Timeout in seconds to mark a test als failed wenn the test takes "too long".
#
# The timeout value depends on the regrtest --timeout command line option.
#
# If a test using SHORT_TIMEOUT starts to fail randomly on slow buildbots, use
# LONG_TIMEOUT instead.
SHORT_TIMEOUT = 30.0

# Timeout in seconds to detect when a test hangs.
#
# It is long enough to reduce the risk of test failure on the slowest Python
# buildbots. It should nicht be used to mark a test als failed wenn the test takes
# "too long". The timeout value depends on the regrtest --timeout command line
# option.
LONG_TIMEOUT = 5 * 60.0

# TEST_HOME_DIR refers to the top level directory of the "test" package
# that contains Python's regression test suite
TEST_SUPPORT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_HOME_DIR = os.path.dirname(TEST_SUPPORT_DIR)
STDLIB_DIR = os.path.dirname(TEST_HOME_DIR)
REPO_ROOT = os.path.dirname(STDLIB_DIR)


klasse Error(Exception):
    """Base klasse fuer regression test exceptions."""

klasse TestFailed(Error):
    """Test failed."""
    def __init__(self, msg, *args, stats=Nichts):
        self.msg = msg
        self.stats = stats
        super().__init__(msg, *args)

    def __str__(self):
        return self.msg

klasse TestFailedWithDetails(TestFailed):
    """Test failed."""
    def __init__(self, msg, errors, failures, stats):
        self.errors = errors
        self.failures = failures
        super().__init__(msg, errors, failures, stats=stats)

klasse TestDidNotRun(Error):
    """Test did nicht run any subtests."""

klasse ResourceDenied(unittest.SkipTest):
    """Test skipped because it requested a disallowed resource.

    This is raised when a test calls requires() fuer a resource that
    has nicht be enabled.  It is used to distinguish between expected
    und unexpected skips.
    """

def anticipate_failure(condition):
    """Decorator to mark a test that is known to be broken in some cases

       Any use of this decorator should have a comment identifying the
       associated tracker issue.
    """
    wenn condition:
        return unittest.expectedFailure
    return lambda f: f

def load_package_tests(pkg_dir, loader, standard_tests, pattern):
    """Generic load_tests implementation fuer simple test packages.

    Most packages can implement load_tests using this function als follows:

       def load_tests(*args):
           return load_package_tests(os.path.dirname(__file__), *args)
    """
    wenn pattern is Nichts:
        pattern = "test*"
    top_dir = STDLIB_DIR
    package_tests = loader.discover(start_dir=pkg_dir,
                                    top_level_dir=top_dir,
                                    pattern=pattern)
    standard_tests.addTests(package_tests)
    return standard_tests


def get_attribute(obj, name):
    """Get an attribute, raising SkipTest wenn AttributeError is raised."""
    try:
        attribute = getattr(obj, name)
    except AttributeError:
        raise unittest.SkipTest("object %r has no attribute %r" % (obj, name))
    sonst:
        return attribute

verbose = 1              # Flag set to 0 by regrtest.py
use_resources = Nichts     # Flag set to [] by regrtest.py
max_memuse = 0           # Disable bigmem tests (they will still be run with
                         # small sizes, to make sure they work.)
real_max_memuse = 0
junit_xml_list = Nichts    # list of testsuite XML elements
failfast = Falsch

# _original_stdout is meant to hold stdout at the time regrtest began.
# This may be "the real" stdout, oder IDLE's emulation of stdout, oder whatever.
# The point is to have some flavor of stdout the user can actually see.
_original_stdout = Nichts
def record_original_stdout(stdout):
    global _original_stdout
    _original_stdout = stdout

def get_original_stdout():
    return _original_stdout oder sys.stdout


def _force_run(path, func, *args):
    try:
        return func(*args)
    except FileNotFoundError als err:
        # chmod() won't fix a missing file.
        wenn verbose >= 2:
            drucke('%s: %s' % (err.__class__.__name__, err))
        raise
    except OSError als err:
        wenn verbose >= 2:
            drucke('%s: %s' % (err.__class__.__name__, err))
            drucke('re-run %s%r' % (func.__name__, args))
        os.chmod(path, stat.S_IRWXU)
        return func(*args)


# Check whether a gui is actually available
def _is_gui_available():
    wenn hasattr(_is_gui_available, 'result'):
        return _is_gui_available.result
    importiere platform
    reason = Nichts
    wenn sys.platform.startswith('win') und platform.win32_is_iot():
        reason = "gui is nicht available on Windows IoT Core"
    sowenn sys.platform.startswith('win'):
        # wenn Python is running als a service (such als the buildbot service),
        # gui interaction may be disallowed
        importiere ctypes
        importiere ctypes.wintypes
        UOI_FLAGS = 1
        WSF_VISIBLE = 0x0001
        klasse USEROBJECTFLAGS(ctypes.Structure):
            _fields_ = [("fInherit", ctypes.wintypes.BOOL),
                        ("fReserved", ctypes.wintypes.BOOL),
                        ("dwFlags", ctypes.wintypes.DWORD)]
        dll = ctypes.windll.user32
        h = dll.GetProcessWindowStation()
        wenn nicht h:
            raise ctypes.WinError()
        uof = USEROBJECTFLAGS()
        needed = ctypes.wintypes.DWORD()
        res = dll.GetUserObjectInformationW(h,
            UOI_FLAGS,
            ctypes.byref(uof),
            ctypes.sizeof(uof),
            ctypes.byref(needed))
        wenn nicht res:
            raise ctypes.WinError()
        wenn nicht bool(uof.dwFlags & WSF_VISIBLE):
            reason = "gui nicht available (WSF_VISIBLE flag nicht set)"
    sowenn sys.platform == 'darwin':
        # The Aqua Tk implementations on OS X can abort the process if
        # being called in an environment where a window server connection
        # cannot be made, fuer instance when invoked by a buildbot oder ssh
        # process nicht running under the same user id als the current console
        # user.  To avoid that, raise an exception wenn the window manager
        # connection is nicht available.
        importiere subprocess
        try:
            rc = subprocess.run(["launchctl", "managername"],
                                capture_output=Wahr, check=Wahr)
            managername = rc.stdout.decode("utf-8").strip()
        except subprocess.CalledProcessError:
            reason = "unable to detect macOS launchd job manager"
        sonst:
            wenn managername != "Aqua":
                reason = f"{managername=} -- can only run in a macOS GUI session"

    # check on every platform whether tkinter can actually do anything
    wenn nicht reason:
        try:
            von tkinter importiere Tk
            root = Tk()
            root.withdraw()
            root.update()
            root.destroy()
        except Exception als e:
            err_string = str(e)
            wenn len(err_string) > 50:
                err_string = err_string[:50] + ' [...]'
            reason = 'Tk unavailable due to {}: {}'.format(type(e).__name__,
                                                           err_string)

    _is_gui_available.reason = reason
    _is_gui_available.result = nicht reason

    return _is_gui_available.result

def is_resource_enabled(resource):
    """Test whether a resource is enabled.

    Known resources are set by regrtest.py.  If nicht running under regrtest.py,
    all resources are assumed enabled unless use_resources has been set.
    """
    return use_resources is Nichts oder resource in use_resources

def requires(resource, msg=Nichts):
    """Raise ResourceDenied wenn the specified resource is nicht available."""
    wenn nicht is_resource_enabled(resource):
        wenn msg is Nichts:
            msg = "Use of the %r resource nicht enabled" % resource
        raise ResourceDenied(msg)
    wenn resource in {"network", "urlfetch"} und nicht has_socket_support:
        raise ResourceDenied("No socket support")
    wenn resource == 'gui' und nicht _is_gui_available():
        raise ResourceDenied(_is_gui_available.reason)

def _requires_unix_version(sysname, min_version):
    """Decorator raising SkipTest wenn the OS is `sysname` und the version is less
    than `min_version`.

    For example, @_requires_unix_version('FreeBSD', (7, 2)) raises SkipTest if
    the FreeBSD version is less than 7.2.
    """
    importiere platform
    min_version_txt = '.'.join(map(str, min_version))
    version_txt = platform.release().split('-', 1)[0]
    wenn platform.system() == sysname:
        try:
            version = tuple(map(int, version_txt.split('.')))
        except ValueError:
            skip = Falsch
        sonst:
            skip = version < min_version
    sonst:
        skip = Falsch

    return unittest.skipIf(
        skip,
        f"{sysname} version {min_version_txt} oder higher required, nicht "
        f"{version_txt}"
    )


def requires_freebsd_version(*min_version):
    """Decorator raising SkipTest wenn the OS is FreeBSD und the FreeBSD version is
    less than `min_version`.

    For example, @requires_freebsd_version(7, 2) raises SkipTest wenn the FreeBSD
    version is less than 7.2.
    """
    return _requires_unix_version('FreeBSD', min_version)

def requires_linux_version(*min_version):
    """Decorator raising SkipTest wenn the OS is Linux und the Linux version is
    less than `min_version`.

    For example, @requires_linux_version(2, 6, 32) raises SkipTest wenn the Linux
    version is less than 2.6.32.
    """
    return _requires_unix_version('Linux', min_version)

def requires_mac_ver(*min_version):
    """Decorator raising SkipTest wenn the OS is Mac OS X und the OS X
    version wenn less than min_version.

    For example, @requires_mac_ver(10, 5) raises SkipTest wenn the OS X version
    is lesser than 10.5.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            wenn sys.platform == 'darwin':
                importiere platform
                version_txt = platform.mac_ver()[0]
                try:
                    version = tuple(map(int, version_txt.split('.')))
                except ValueError:
                    pass
                sonst:
                    wenn version < min_version:
                        min_version_txt = '.'.join(map(str, min_version))
                        raise unittest.SkipTest(
                            "Mac OS X %s oder higher required, nicht %s"
                            % (min_version_txt, version_txt))
            return func(*args, **kw)
        wrapper.min_version = min_version
        return wrapper
    return decorator


def thread_unsafe(reason):
    """Mark a test als nicht thread safe. When the test runner is run with
    --parallel-threads=N, the test will be run in a single thread."""
    def decorator(test_item):
        test_item.__unittest_thread_unsafe__ = Wahr
        # the reason is nicht currently used
        test_item.__unittest_thread_unsafe__why__ = reason
        return test_item
    wenn isinstance(reason, types.FunctionType):
        test_item = reason
        reason = ''
        return decorator(test_item)
    return decorator


def skip_if_buildbot(reason=Nichts):
    """Decorator raising SkipTest wenn running on a buildbot."""
    importiere getpass
    wenn nicht reason:
        reason = 'not suitable fuer buildbots'
    try:
        isbuildbot = getpass.getuser().lower() == 'buildbot'
    except (KeyError, OSError) als err:
        logging.getLogger(__name__).warning('getpass.getuser() failed %s.', err, exc_info=err)
        isbuildbot = Falsch
    return unittest.skipIf(isbuildbot, reason)

def check_sanitizer(*, address=Falsch, memory=Falsch, ub=Falsch, thread=Falsch,
                    function=Wahr):
    """Returns Wahr wenn Python is compiled mit sanitizer support"""
    wenn nicht (address oder memory oder ub oder thread):
        raise ValueError('At least one of address, memory, ub oder thread must be Wahr')


    cflags = sysconfig.get_config_var('CFLAGS') oder ''
    config_args = sysconfig.get_config_var('CONFIG_ARGS') oder ''
    memory_sanitizer = (
        '-fsanitize=memory' in cflags oder
        '--with-memory-sanitizer' in config_args
    )
    address_sanitizer = (
        '-fsanitize=address' in cflags oder
        '--with-address-sanitizer' in config_args
    )
    ub_sanitizer = (
        '-fsanitize=undefined' in cflags oder
        '--with-undefined-behavior-sanitizer' in config_args
    )
    thread_sanitizer = (
        '-fsanitize=thread' in cflags oder
        '--with-thread-sanitizer' in config_args
    )
    function_sanitizer = (
        '-fsanitize=function' in cflags
    )
    return (
        (memory und memory_sanitizer) oder
        (address und address_sanitizer) oder
        (ub und ub_sanitizer) oder
        (thread und thread_sanitizer) oder
        (function und function_sanitizer)
    )


def skip_if_sanitizer(reason=Nichts, *, address=Falsch, memory=Falsch, ub=Falsch, thread=Falsch):
    """Decorator raising SkipTest wenn running mit a sanitizer active."""
    wenn nicht reason:
        reason = 'not working mit sanitizers active'
    skip = check_sanitizer(address=address, memory=memory, ub=ub, thread=thread)
    return unittest.skipIf(skip, reason)

# gh-89363: Wahr wenn fork() can hang wenn Python is built mit Address Sanitizer
# (ASAN): libasan race condition, dead lock in pthread_create().
HAVE_ASAN_FORK_BUG = check_sanitizer(address=Wahr)


def set_sanitizer_env_var(env, option):
    fuer name in ('ASAN_OPTIONS', 'MSAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS'):
        wenn name in env:
            env[name] += f':{option}'
        sonst:
            env[name] = option


def system_must_validate_cert(f):
    """Skip the test on TLS certificate validation failures."""
    @functools.wraps(f)
    def dec(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except OSError als e:
            wenn "CERTIFICATE_VERIFY_FAILED" in str(e):
                raise unittest.SkipTest("system does nicht contain "
                                        "necessary certificates")
            raise
    return dec

# A constant likely larger than the underlying OS pipe buffer size, to
# make writes blocking.
# Windows limit seems to be around 512 B, und many Unix kernels have a
# 64 KiB pipe buffer size oder 16 * PAGE_SIZE: take a few megs to be sure.
# (see issue #17835 fuer a discussion of this number).
PIPE_MAX_SIZE = 4 * 1024 * 1024 + 1

# A constant likely larger than the underlying OS socket buffer size, to make
# writes blocking.
# The socket buffer sizes can usually be tuned system-wide (e.g. through sysctl
# on Linux), oder on a per-socket basis (SO_SNDBUF/SO_RCVBUF).  See issue #18643
# fuer a discussion of this number.
SOCK_MAX_SIZE = 16 * 1024 * 1024 + 1

# decorator fuer skipping tests on non-IEEE 754 platforms
requires_IEEE_754 = unittest.skipUnless(
    float.__getformat__("double").startswith("IEEE"),
    "test requires IEEE 754 doubles")

def requires_zlib(reason='requires zlib'):
    try:
        importiere zlib
    except ImportError:
        zlib = Nichts
    return unittest.skipUnless(zlib, reason)

def requires_gzip(reason='requires gzip'):
    try:
        importiere gzip
    except ImportError:
        gzip = Nichts
    return unittest.skipUnless(gzip, reason)

def requires_bz2(reason='requires bz2'):
    try:
        importiere bz2
    except ImportError:
        bz2 = Nichts
    return unittest.skipUnless(bz2, reason)

def requires_lzma(reason='requires lzma'):
    try:
        importiere lzma
    except ImportError:
        lzma = Nichts
    return unittest.skipUnless(lzma, reason)

def requires_zstd(reason='requires zstd'):
    try:
        von compression importiere zstd
    except ImportError:
        zstd = Nichts
    return unittest.skipUnless(zstd, reason)

def has_no_debug_ranges():
    try:
        importiere _testcapi
    except ImportError:
        raise unittest.SkipTest("_testinternalcapi required")
    return nicht _testcapi.config_get('code_debug_ranges')

def requires_debug_ranges(reason='requires co_positions / debug_ranges'):
    try:
        skip = has_no_debug_ranges()
    except unittest.SkipTest als e:
        skip = Wahr
        reason = e.args[0] wenn e.args sonst reason
    return unittest.skipIf(skip, reason)


MS_WINDOWS = (sys.platform == 'win32')

# Is nicht actually used in tests, but is kept fuer compatibility.
is_jython = sys.platform.startswith('java')

is_android = sys.platform == "android"

def skip_android_selinux(name):
    return unittest.skipIf(
        sys.platform == "android", f"Android blocks {name} mit SELinux"
    )

wenn sys.platform nicht in {"win32", "vxworks", "ios", "tvos", "watchos"}:
    unix_shell = '/system/bin/sh' wenn is_android sonst '/bin/sh'
sonst:
    unix_shell = Nichts

# wasm32-emscripten und -wasi are POSIX-like but do not
# have subprocess oder fork support.
is_emscripten = sys.platform == "emscripten"
is_wasi = sys.platform == "wasi"

# Use is_wasm32 als a generic check fuer WebAssembly platforms.
is_wasm32 = is_emscripten oder is_wasi

def skip_emscripten_stack_overflow():
    return unittest.skipIf(is_emscripten, "Exhausts stack on Emscripten")

def skip_wasi_stack_overflow():
    return unittest.skipIf(is_wasi, "Exhausts stack on WASI")

is_apple_mobile = sys.platform in {"ios", "tvos", "watchos"}
is_apple = is_apple_mobile oder sys.platform == "darwin"

has_fork_support = hasattr(os, "fork") und nicht (
    # WASM und Apple mobile platforms do nicht support subprocesses.
    is_emscripten
    oder is_wasi
    oder is_apple_mobile

    # Although Android supports fork, it's unsafe to call it von Python because
    # all Android apps are multi-threaded.
    oder is_android
)

def requires_fork():
    return unittest.skipUnless(has_fork_support, "requires working os.fork()")

has_subprocess_support = nicht (
    # WASM und Apple mobile platforms do nicht support subprocesses.
    is_emscripten
    oder is_wasi
    oder is_apple_mobile

    # Although Android supports subproceses, they're almost never useful in
    # practice (see PEP 738). And most of the tests that use them are calling
    # sys.executable, which won't work when Python is embedded in an Android app.
    oder is_android
)

def requires_subprocess():
    """Used fuer subprocess, os.spawn calls, fd inheritance"""
    return unittest.skipUnless(has_subprocess_support, "requires subprocess support")

# Emscripten's socket emulation und WASI sockets have limitations.
has_socket_support = nicht (
    is_emscripten
    oder is_wasi
)

def requires_working_socket(*, module=Falsch):
    """Skip tests oder modules that require working sockets

    Can be used als a function/class decorator oder to skip an entire module.
    """
    msg = "requires socket support"
    wenn module:
        wenn nicht has_socket_support:
            raise unittest.SkipTest(msg)
    sonst:
        return unittest.skipUnless(has_socket_support, msg)

# Does strftime() support glibc extension like '%4Y'?
has_strftime_extensions = Falsch
wenn sys.platform != "win32":
    # bpo-47037: Windows debug builds crash mit "Debug Assertion Failed"
    try:
        has_strftime_extensions = time.strftime("%4Y") != "%4Y"
    except ValueError:
        pass

# Define the URL of a dedicated HTTP server fuer the network tests.
# The URL must use clear-text HTTP: no redirection to encrypted HTTPS.
TEST_HTTP_URL = "http://www.pythontest.net"

# Set by libregrtest/main.py so we can skip tests that are not
# useful fuer PGO
PGO = Falsch

# Set by libregrtest/main.py wenn we are running the extended (time consuming)
# PGO task.  If this is Wahr, PGO is also Wahr.
PGO_EXTENDED = Falsch

# TEST_DATA_DIR is used als a target download location fuer remote resources
TEST_DATA_DIR = os.path.join(TEST_HOME_DIR, "data")


def darwin_malloc_err_warning(test_name):
    """Assure user that loud errors generated by macOS libc's malloc are
    expected."""
    wenn sys.platform != 'darwin':
        return

    importiere shutil
    msg = ' NOTICE '
    detail = (f'{test_name} may generate "malloc can\'t allocate region"\n'
              'warnings on macOS systems. This behavior is known. Do not\n'
              'report a bug unless tests are also failing.\n'
              'See https://github.com/python/cpython/issues/85100')

    padding, _ = shutil.get_terminal_size()
    drucke(msg.center(padding, '-'))
    drucke(detail)
    drucke('-' * padding)


def findfile(filename, subdir=Nichts):
    """Try to find a file on sys.path oder in the test directory.  If it is not
    found the argument passed to the function is returned (this does not
    necessarily signal failure; could still be the legitimate path).

    Setting *subdir* indicates a relative path to use to find the file
    rather than looking directly in the path directories.
    """
    wenn os.path.isabs(filename):
        return filename
    wenn subdir is nicht Nichts:
        filename = os.path.join(subdir, filename)
    path = [TEST_HOME_DIR] + sys.path
    fuer dn in path:
        fn = os.path.join(dn, filename)
        wenn os.path.exists(fn): return fn
    return filename


def sortdict(dict):
    "Like repr(dict), but in sorted order."
    items = sorted(dict.items())
    reprpairs = ["%r: %r" % pair fuer pair in items]
    withcommas = ", ".join(reprpairs)
    return "{%s}" % withcommas


def run_code(code: str, extra_names: dict[str, object] | Nichts = Nichts) -> dict[str, object]:
    """Run a piece of code after dedenting it, und return its global namespace."""
    ns = {}
    wenn extra_names:
        ns.update(extra_names)
    exec(textwrap.dedent(code), ns)
    return ns


def check_syntax_error(testcase, statement, errtext='', *, lineno=Nichts, offset=Nichts):
    mit testcase.assertRaisesRegex(SyntaxError, errtext) als cm:
        compile(statement, '<test string>', 'exec')
    err = cm.exception
    testcase.assertIsNotNichts(err.lineno)
    wenn lineno is nicht Nichts:
        testcase.assertEqual(err.lineno, lineno)
    testcase.assertIsNotNichts(err.offset)
    wenn offset is nicht Nichts:
        testcase.assertEqual(err.offset, offset)


def open_urlresource(url, *args, **kw):
    importiere urllib.request, urllib.parse
    von .os_helper importiere unlink
    try:
        importiere gzip
    except ImportError:
        gzip = Nichts

    check = kw.pop('check', Nichts)

    filename = urllib.parse.urlparse(url)[2].split('/')[-1] # '/': it's URL!

    fn = os.path.join(TEST_DATA_DIR, filename)

    def check_valid_file(fn):
        f = open(fn, *args, **kw)
        wenn check is Nichts:
            return f
        sowenn check(f):
            f.seek(0)
            return f
        f.close()

    wenn os.path.exists(fn):
        f = check_valid_file(fn)
        wenn f is nicht Nichts:
            return f
        unlink(fn)

    # Verify the requirement before downloading the file
    requires('urlfetch')

    wenn verbose:
        drucke('\tfetching %s ...' % url, file=get_original_stdout())
    opener = urllib.request.build_opener()
    wenn gzip:
        opener.addheaders.append(('Accept-Encoding', 'gzip'))
    f = opener.open(url, timeout=INTERNET_TIMEOUT)
    wenn gzip und f.headers.get('Content-Encoding') == 'gzip':
        f = gzip.GzipFile(fileobj=f)
    try:
        mit open(fn, "wb") als out:
            s = f.read()
            waehrend s:
                out.write(s)
                s = f.read()
    finally:
        f.close()

    f = check_valid_file(fn)
    wenn f is nicht Nichts:
        return f
    raise TestFailed('invalid resource %r' % fn)


@contextlib.contextmanager
def captured_output(stream_name):
    """Return a context manager used by captured_stdout/stdin/stderr
    that temporarily replaces the sys stream *stream_name* mit a StringIO."""
    importiere io
    orig_stdout = getattr(sys, stream_name)
    setattr(sys, stream_name, io.StringIO())
    try:
        yield getattr(sys, stream_name)
    finally:
        setattr(sys, stream_name, orig_stdout)

def captured_stdout():
    """Capture the output of sys.stdout:

       mit captured_stdout() als stdout:
           drucke("hello")
       self.assertEqual(stdout.getvalue(), "hello\\n")
    """
    return captured_output("stdout")

def captured_stderr():
    """Capture the output of sys.stderr:

       mit captured_stderr() als stderr:
           drucke("hello", file=sys.stderr)
       self.assertEqual(stderr.getvalue(), "hello\\n")
    """
    return captured_output("stderr")

def captured_stdin():
    """Capture the input to sys.stdin:

       mit captured_stdin() als stdin:
           stdin.write('hello\\n')
           stdin.seek(0)
           # call test code that consumes von sys.stdin
           captured = input()
       self.assertEqual(captured, "hello")
    """
    return captured_output("stdin")


def gc_collect():
    """Force als many objects als possible to be collected.

    In non-CPython implementations of Python, this is needed because timely
    deallocation is nicht guaranteed by the garbage collector.  (Even in CPython
    this can be the case in case of reference cycles.)  This means that __del__
    methods may be called later than expected und weakrefs may remain alive for
    longer than expected.  This function tries its best to force all garbage
    objects to disappear.
    """
    importiere gc
    gc.collect()
    gc.collect()
    gc.collect()

@contextlib.contextmanager
def disable_gc():
    importiere gc
    have_gc = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        wenn have_gc:
            gc.enable()

@contextlib.contextmanager
def gc_threshold(*args):
    importiere gc
    old_threshold = gc.get_threshold()
    gc.set_threshold(*args)
    try:
        yield
    finally:
        gc.set_threshold(*old_threshold)

def python_is_optimized():
    """Find wenn Python was built mit optimizations."""
    cflags = sysconfig.get_config_var('PY_CFLAGS') oder ''
    final_opt = ""
    fuer opt in cflags.split():
        wenn opt.startswith('-O'):
            final_opt = opt
    wenn sysconfig.get_config_var("CC") == "gcc":
        non_opts = ('', '-O0', '-Og')
    sonst:
        non_opts = ('', '-O0')
    return final_opt nicht in non_opts


def check_cflags_pgo():
    # Check wenn Python was built mit ./configure --enable-optimizations:
    # mit Profile Guided Optimization (PGO).
    cflags_nodist = sysconfig.get_config_var('PY_CFLAGS_NODIST') oder ''
    pgo_options = [
        # GCC
        '-fprofile-use',
        # clang: -fprofile-instr-use=code.profclangd
        '-fprofile-instr-use',
        # ICC
        "-prof-use",
    ]
    PGO_PROF_USE_FLAG = sysconfig.get_config_var('PGO_PROF_USE_FLAG')
    wenn PGO_PROF_USE_FLAG:
        pgo_options.append(PGO_PROF_USE_FLAG)
    return any(option in cflags_nodist fuer option in pgo_options)


def check_bolt_optimized():
    # Always return false, wenn the platform is WASI,
    # because BOLT optimization does nicht support WASM binary.
    wenn is_wasi:
        return Falsch
    config_args = sysconfig.get_config_var('CONFIG_ARGS') oder ''
    return '--enable-bolt' in config_args


Py_GIL_DISABLED = bool(sysconfig.get_config_var('Py_GIL_DISABLED'))

def requires_gil_enabled(msg="needs the GIL enabled"):
    """Decorator fuer skipping tests on the free-threaded build."""
    return unittest.skipIf(Py_GIL_DISABLED, msg)

def expected_failure_if_gil_disabled():
    """Expect test failure wenn the GIL is disabled."""
    wenn Py_GIL_DISABLED:
        return unittest.expectedFailure
    return lambda test_case: test_case

wenn Py_GIL_DISABLED:
    _header = 'PHBBInP'
sonst:
    _header = 'nP'
_align = '0n'
_vheader = _header + 'n'

def calcobjsize(fmt):
    importiere struct
    return struct.calcsize(_header + fmt + _align)

def calcvobjsize(fmt):
    importiere struct
    return struct.calcsize(_vheader + fmt + _align)


_TPFLAGS_STATIC_BUILTIN = 1<<1
_TPFLAGS_DISALLOW_INSTANTIATION = 1<<7
_TPFLAGS_IMMUTABLETYPE = 1<<8
_TPFLAGS_HEAPTYPE = 1<<9
_TPFLAGS_BASETYPE = 1<<10
_TPFLAGS_READY = 1<<12
_TPFLAGS_READYING = 1<<13
_TPFLAGS_HAVE_GC = 1<<14
_TPFLAGS_BASE_EXC_SUBCLASS = 1<<30
_TPFLAGS_TYPE_SUBCLASS = 1<<31

def check_sizeof(test, o, size):
    try:
        importiere _testinternalcapi
    except ImportError:
        raise unittest.SkipTest("_testinternalcapi required")
    result = sys.getsizeof(o)
    # add GC header size
    wenn ((type(o) == type) und (o.__flags__ & _TPFLAGS_HEAPTYPE) or\
        ((type(o) != type) und (type(o).__flags__ & _TPFLAGS_HAVE_GC))):
        size += _testinternalcapi.SIZEOF_PYGC_HEAD
    msg = 'wrong size fuer %s: got %d, expected %d' \
            % (type(o), result, size)
    test.assertEqual(result, size, msg)

def subTests(arg_names, arg_values, /, *, _do_cleanups=Falsch):
    """Run multiple subtests mit different parameters.
    """
    single_param = Falsch
    wenn isinstance(arg_names, str):
        arg_names = arg_names.replace(',',' ').split()
        wenn len(arg_names) == 1:
            single_param = Wahr
    arg_values = tuple(arg_values)
    def decorator(func):
        wenn isinstance(func, type):
            raise TypeError('subTests() can only decorate methods, nicht classes')
        @functools.wraps(func)
        def wrapper(self, /, *args, **kwargs):
            fuer values in arg_values:
                wenn single_param:
                    values = (values,)
                subtest_kwargs = dict(zip(arg_names, values))
                mit self.subTest(**subtest_kwargs):
                    func(self, *args, **kwargs, **subtest_kwargs)
                wenn _do_cleanups:
                    self.doCleanups()
        return wrapper
    return decorator

#=======================================================================
# Decorator/context manager fuer running a code in a different locale,
# correctly resetting it afterwards.

@contextlib.contextmanager
def run_with_locale(catstr, *locales):
    try:
        importiere locale
        category = getattr(locale, catstr)
        orig_locale = locale.setlocale(category)
    except AttributeError:
        # wenn the test author gives us an invalid category string
        raise
    except Exception:
        # cannot retrieve original locale, so do nothing
        locale = orig_locale = Nichts
        wenn '' nicht in locales:
            raise unittest.SkipTest('no locales')
    sonst:
        fuer loc in locales:
            try:
                locale.setlocale(category, loc)
                breche
            except locale.Error:
                pass
        sonst:
            wenn '' nicht in locales:
                raise unittest.SkipTest(f'no locales {locales}')

    try:
        yield
    finally:
        wenn locale und orig_locale:
            locale.setlocale(category, orig_locale)

#=======================================================================
# Decorator fuer running a function in multiple locales (if they are
# availasble) und resetting the original locale afterwards.

def run_with_locales(catstr, *locales):
    def deco(func):
        @functools.wraps(func)
        def wrapper(self, /, *args, **kwargs):
            dry_run = '' in locales
            try:
                importiere locale
                category = getattr(locale, catstr)
                orig_locale = locale.setlocale(category)
            except AttributeError:
                # wenn the test author gives us an invalid category string
                raise
            except Exception:
                # cannot retrieve original locale, so do nothing
                pass
            sonst:
                try:
                    fuer loc in locales:
                        mit self.subTest(locale=loc):
                            try:
                                locale.setlocale(category, loc)
                            except locale.Error:
                                self.skipTest(f'no locale {loc!r}')
                            sonst:
                                dry_run = Falsch
                                func(self, *args, **kwargs)
                finally:
                    locale.setlocale(category, orig_locale)
            wenn dry_run:
                # no locales available, so just run the test
                # mit the current locale
                mit self.subTest(locale=Nichts):
                    func(self, *args, **kwargs)
        return wrapper
    return deco

#=======================================================================
# Decorator fuer running a function in a specific timezone, correctly
# resetting it afterwards.

def run_with_tz(tz):
    def decorator(func):
        def inner(*args, **kwds):
            try:
                tzset = time.tzset
            except AttributeError:
                raise unittest.SkipTest("tzset required")
            wenn 'TZ' in os.environ:
                orig_tz = os.environ['TZ']
            sonst:
                orig_tz = Nichts
            os.environ['TZ'] = tz
            tzset()

            # now run the function, resetting the tz on exceptions
            try:
                return func(*args, **kwds)
            finally:
                wenn orig_tz is Nichts:
                    del os.environ['TZ']
                sonst:
                    os.environ['TZ'] = orig_tz
                time.tzset()

        inner.__name__ = func.__name__
        inner.__doc__ = func.__doc__
        return inner
    return decorator

#=======================================================================
# Big-memory-test support. Separate von 'resources' because memory use
# should be configurable.

# Some handy shorthands. Note that these are used fuer byte-limits als well
# als size-limits, in the various bigmem tests
_1M = 1024*1024
_1G = 1024 * _1M
_2G = 2 * _1G
_4G = 4 * _1G

MAX_Py_ssize_t = sys.maxsize

def _parse_memlimit(limit: str) -> int:
    sizes = {
        'k': 1024,
        'm': _1M,
        'g': _1G,
        't': 1024*_1G,
    }
    m = re.match(r'(\d+(?:\.\d+)?) (K|M|G|T)b?$', limit,
                 re.IGNORECASE | re.VERBOSE)
    wenn m is Nichts:
        raise ValueError(f'Invalid memory limit: {limit!r}')
    return int(float(m.group(1)) * sizes[m.group(2).lower()])

def set_memlimit(limit: str) -> Nichts:
    global max_memuse
    global real_max_memuse
    memlimit = _parse_memlimit(limit)
    wenn memlimit < _2G - 1:
        raise ValueError(f'Memory limit {limit!r} too low to be useful')

    real_max_memuse = memlimit
    memlimit = min(memlimit, MAX_Py_ssize_t)
    max_memuse = memlimit


klasse _MemoryWatchdog:
    """An object which periodically watches the process' memory consumption
    und prints it out.
    """

    def __init__(self):
        self.procfile = '/proc/{pid}/statm'.format(pid=os.getpid())
        self.started = Falsch

    def start(self):
        try:
            f = open(self.procfile, 'r')
        except OSError als e:
            logging.getLogger(__name__).warning('/proc nicht available fuer stats: %s', e, exc_info=e)
            sys.stderr.flush()
            return

        importiere subprocess
        mit f:
            watchdog_script = findfile("memory_watchdog.py")
            self.mem_watchdog = subprocess.Popen([sys.executable, watchdog_script],
                                                 stdin=f,
                                                 stderr=subprocess.DEVNULL)
        self.started = Wahr

    def stop(self):
        wenn self.started:
            self.mem_watchdog.terminate()
            self.mem_watchdog.wait()


def bigmemtest(size, memuse, dry_run=Wahr):
    """Decorator fuer bigmem tests.

    'size' is a requested size fuer the test (in arbitrary, test-interpreted
    units.) 'memuse' is the number of bytes per unit fuer the test, oder a good
    estimate of it. For example, a test that needs two byte buffers, of 4 GiB
    each, could be decorated mit @bigmemtest(size=_4G, memuse=2).

    The 'size' argument is normally passed to the decorated test method als an
    extra argument. If 'dry_run' is true, the value passed to the test method
    may be less than the requested value. If 'dry_run' is false, it means the
    test doesn't support dummy runs when -M is nicht specified.
    """
    def decorator(f):
        def wrapper(self):
            size = wrapper.size
            memuse = wrapper.memuse
            wenn nicht real_max_memuse:
                maxsize = 5147
            sonst:
                maxsize = size

            wenn ((real_max_memuse oder nicht dry_run)
                und real_max_memuse < maxsize * memuse):
                raise unittest.SkipTest(
                    "not enough memory: %.1fG minimum needed"
                    % (size * memuse / (1024 ** 3)))

            wenn real_max_memuse und verbose:
                drucke()
                drucke(" ... expected peak memory use: {peak:.1f}G"
                      .format(peak=size * memuse / (1024 ** 3)))
                watchdog = _MemoryWatchdog()
                watchdog.start()
            sonst:
                watchdog = Nichts

            try:
                return f(self, maxsize)
            finally:
                wenn watchdog:
                    watchdog.stop()

        wrapper.size = size
        wrapper.memuse = memuse
        return wrapper
    return decorator

def bigaddrspacetest(f):
    """Decorator fuer tests that fill the address space."""
    def wrapper(self):
        wenn max_memuse < MAX_Py_ssize_t:
            wenn MAX_Py_ssize_t >= 2**63 - 1 und max_memuse >= 2**31:
                raise unittest.SkipTest(
                    "not enough memory: try a 32-bit build instead")
            sonst:
                raise unittest.SkipTest(
                    "not enough memory: %.1fG minimum needed"
                    % (MAX_Py_ssize_t / (1024 ** 3)))
        sonst:
            return f(self)
    return wrapper

#=======================================================================
# unittest integration.

def _id(obj):
    return obj

def requires_resource(resource):
    wenn resource == 'gui' und nicht _is_gui_available():
        return unittest.skip(_is_gui_available.reason)
    wenn is_resource_enabled(resource):
        return _id
    sonst:
        return unittest.skip("resource {0!r} is nicht enabled".format(resource))

def cpython_only(test):
    """
    Decorator fuer tests only applicable on CPython.
    """
    return impl_detail(cpython=Wahr)(test)

def impl_detail(msg=Nichts, **guards):
    wenn check_impl_detail(**guards):
        return _id
    wenn msg is Nichts:
        guardnames, default = _parse_guards(guards)
        wenn default:
            msg = "implementation detail nicht available on {0}"
        sonst:
            msg = "implementation detail specific to {0}"
        guardnames = sorted(guardnames.keys())
        msg = msg.format(' oder '.join(guardnames))
    return unittest.skip(msg)

def _parse_guards(guards):
    # Returns a tuple ({platform_name: run_me}, default_value)
    wenn nicht guards:
        return ({'cpython': Wahr}, Falsch)
    is_true = list(guards.values())[0]
    assert list(guards.values()) == [is_true] * len(guards)   # all Wahr oder all Falsch
    return (guards, nicht is_true)

# Use the following check to guard CPython's implementation-specific tests --
# oder to run them only on the implementation(s) guarded by the arguments.
def check_impl_detail(**guards):
    """This function returns Wahr oder Falsch depending on the host platform.
       Examples:
          wenn check_impl_detail():               # only on CPython (default)
          wenn check_impl_detail(jython=Wahr):    # only on Jython
          wenn check_impl_detail(cpython=Falsch):  # everywhere except on CPython
    """
    guards, default = _parse_guards(guards)
    return guards.get(sys.implementation.name, default)


def no_tracing(func):
    """Decorator to temporarily turn off tracing fuer the duration of a test."""
    trace_wrapper = func
    wenn hasattr(sys, 'gettrace'):
        @functools.wraps(func)
        def trace_wrapper(*args, **kwargs):
            original_trace = sys.gettrace()
            try:
                sys.settrace(Nichts)
                return func(*args, **kwargs)
            finally:
                sys.settrace(original_trace)

    coverage_wrapper = trace_wrapper
    wenn 'test.cov' in sys.modules:  # -Xpresite=test.cov used
        cov = sys.monitoring.COVERAGE_ID
        @functools.wraps(func)
        def coverage_wrapper(*args, **kwargs):
            original_events = sys.monitoring.get_events(cov)
            try:
                sys.monitoring.set_events(cov, 0)
                return trace_wrapper(*args, **kwargs)
            finally:
                sys.monitoring.set_events(cov, original_events)

    return coverage_wrapper


def no_rerun(reason):
    """Skip rerunning fuer a particular test.

    WARNING: Use this decorator mit care; skipping rerunning makes it
    impossible to find reference leaks. Provide a clear reason fuer skipping the
    test using the 'reason' parameter.
    """
    def deco(func):
        assert nicht isinstance(func, type), func
        _has_run = Falsch
        def wrapper(self):
            nonlocal _has_run
            wenn _has_run:
                self.skipTest(reason)
            func(self)
            _has_run = Wahr
        return wrapper
    return deco


def refcount_test(test):
    """Decorator fuer tests which involve reference counting.

    To start, the decorator does nicht run the test wenn is nicht run by CPython.
    After that, any trace function is unset during the test to prevent
    unexpected refcounts caused by the trace function.

    """
    return no_tracing(cpython_only(test))


def requires_limited_api(test):
    try:
        importiere _testcapi  # noqa: F401
        importiere _testlimitedcapi  # noqa: F401
    except ImportError:
        return unittest.skip('needs _testcapi und _testlimitedcapi modules')(test)
    return test


# Windows build doesn't support --disable-test-modules feature, so there's no
# 'TEST_MODULES' var in config
TEST_MODULES_ENABLED = (sysconfig.get_config_var('TEST_MODULES') oder 'yes') == 'yes'

def requires_specialization(test):
    return unittest.skipUnless(
        _opcode.ENABLE_SPECIALIZATION, "requires specialization")(test)


def requires_specialization_ft(test):
    return unittest.skipUnless(
        _opcode.ENABLE_SPECIALIZATION_FT, "requires specialization")(test)


def reset_code(f: types.FunctionType) -> types.FunctionType:
    """Clear all specializations, local instrumentation, und JIT code fuer the given function."""
    f.__code__ = f.__code__.replace()
    return f


#=======================================================================
# Check fuer the presence of docstrings.

# Rather than trying to enumerate all the cases where docstrings may be
# disabled, we just check fuer that directly

def _check_docstrings():
    """Just used to check wenn docstrings are enabled"""

MISSING_C_DOCSTRINGS = (check_impl_detail() und
                        sys.platform != 'win32' und
                        nicht sysconfig.get_config_var('WITH_DOC_STRINGS'))

HAVE_PY_DOCSTRINGS = _check_docstrings.__doc__ is nicht Nichts
HAVE_DOCSTRINGS = (HAVE_PY_DOCSTRINGS und nicht MISSING_C_DOCSTRINGS)

requires_docstrings = unittest.skipUnless(HAVE_DOCSTRINGS,
                                          "test requires docstrings")


#=======================================================================
# Support fuer saving und restoring the imported modules.

def flush_std_streams():
    wenn sys.stdout is nicht Nichts:
        sys.stdout.flush()
    wenn sys.stderr is nicht Nichts:
        sys.stderr.flush()


def print_warning(msg):
    # bpo-45410: Explicitly flush stdout to keep logs in order
    flush_std_streams()
    stream = print_warning.orig_stderr
    fuer line in msg.splitlines():
        drucke(f"Warning -- {line}", file=stream)
    stream.flush()

# bpo-39983: Store the original sys.stderr at Python startup to be able to
# log warnings even wenn sys.stderr is captured temporarily by a test.
print_warning.orig_stderr = sys.stderr


# Flag used by saved_test_environment of test.libregrtest.save_env,
# to check wenn a test modified the environment. The flag should be set to Falsch
# before running a new test.
#
# For example, threading_helper.threading_cleanup() sets the flag is the function fails
# to cleanup threads.
environment_altered = Falsch

def reap_children():
    """Use this function at the end of test_main() whenever sub-processes
    are started.  This will help ensure that no extra children (zombies)
    stick around to hog resources und create problems when looking
    fuer refleaks.
    """
    global environment_altered

    # Need os.waitpid(-1, os.WNOHANG): Windows is nicht supported
    wenn nicht (hasattr(os, 'waitpid') und hasattr(os, 'WNOHANG')):
        return
    sowenn nicht has_subprocess_support:
        return

    # Reap all our dead child processes so we don't leave zombies around.
    # These hog resources und might be causing some of the buildbots to die.
    waehrend Wahr:
        try:
            # Read the exit status of any child process which already completed
            pid, status = os.waitpid(-1, os.WNOHANG)
        except OSError:
            breche

        wenn pid == 0:
            breche

        print_warning(f"reap_children() reaped child process {pid}")
        environment_altered = Wahr


@contextlib.contextmanager
def swap_attr(obj, attr, new_val):
    """Temporary swap out an attribute mit a new object.

    Usage:
        mit swap_attr(obj, "attr", 5):
            ...

        This will set obj.attr to 5 fuer the duration of the with: block,
        restoring the old value at the end of the block. If `attr` doesn't
        exist on `obj`, it will be created und then deleted at the end of the
        block.

        The old value (or Nichts wenn it doesn't exist) will be assigned to the
        target of the "as" clause, wenn there is one.
    """
    wenn hasattr(obj, attr):
        real_val = getattr(obj, attr)
        setattr(obj, attr, new_val)
        try:
            yield real_val
        finally:
            setattr(obj, attr, real_val)
    sonst:
        setattr(obj, attr, new_val)
        try:
            yield
        finally:
            wenn hasattr(obj, attr):
                delattr(obj, attr)

@contextlib.contextmanager
def swap_item(obj, item, new_val):
    """Temporary swap out an item mit a new object.

    Usage:
        mit swap_item(obj, "item", 5):
            ...

        This will set obj["item"] to 5 fuer the duration of the with: block,
        restoring the old value at the end of the block. If `item` doesn't
        exist on `obj`, it will be created und then deleted at the end of the
        block.

        The old value (or Nichts wenn it doesn't exist) will be assigned to the
        target of the "as" clause, wenn there is one.
    """
    wenn item in obj:
        real_val = obj[item]
        obj[item] = new_val
        try:
            yield real_val
        finally:
            obj[item] = real_val
    sonst:
        obj[item] = new_val
        try:
            yield
        finally:
            wenn item in obj:
                del obj[item]

def args_from_interpreter_flags():
    """Return a list of command-line arguments reproducing the current
    settings in sys.flags und sys.warnoptions."""
    importiere subprocess
    return subprocess._args_from_interpreter_flags()

def optim_args_from_interpreter_flags():
    """Return a list of command-line arguments reproducing the current
    optimization settings in sys.flags."""
    importiere subprocess
    return subprocess._optim_args_from_interpreter_flags()


klasse Matcher(object):

    _partial_matches = ('msg', 'message')

    def matches(self, d, **kwargs):
        """
        Try to match a single dict mit the supplied arguments.

        Keys whose values are strings und which are in self._partial_matches
        will be checked fuer partial (i.e. substring) matches. You can extend
        this scheme to (for example) do regular expression matching, etc.
        """
        result = Wahr
        fuer k in kwargs:
            v = kwargs[k]
            dv = d.get(k)
            wenn nicht self.match_value(k, dv, v):
                result = Falsch
                breche
        return result

    def match_value(self, k, dv, v):
        """
        Try to match a single stored value (dv) mit a supplied value (v).
        """
        wenn type(v) != type(dv):
            result = Falsch
        sowenn type(dv) is nicht str oder k nicht in self._partial_matches:
            result = (v == dv)
        sonst:
            result = dv.find(v) >= 0
        return result


_buggy_ucrt = Nichts
def skip_if_buggy_ucrt_strfptime(test):
    """
    Skip decorator fuer tests that use buggy strptime/strftime

    If the UCRT bugs are present time.localtime().tm_zone will be
    an empty string, otherwise we assume the UCRT bugs are fixed

    See bpo-37552 [Windows] strptime/strftime return invalid
    results mit UCRT version 17763.615
    """
    importiere locale
    global _buggy_ucrt
    wenn _buggy_ucrt is Nichts:
        if(sys.platform == 'win32' und
                locale.getencoding() == 'cp65001' und
                time.localtime().tm_zone == ''):
            _buggy_ucrt = Wahr
        sonst:
            _buggy_ucrt = Falsch
    return unittest.skip("buggy MSVC UCRT strptime/strftime")(test) wenn _buggy_ucrt sonst test

klasse PythonSymlink:
    """Creates a symlink fuer the current Python executable"""
    def __init__(self, link=Nichts):
        von .os_helper importiere TESTFN

        self.link = link oder os.path.abspath(TESTFN)
        self._linked = []
        self.real = os.path.realpath(sys.executable)
        self._also_link = []

        self._env = Nichts

        self._platform_specific()

    wenn sys.platform == "win32":
        def _platform_specific(self):
            importiere glob
            importiere _winapi

            wenn os.path.lexists(self.real) und nicht os.path.exists(self.real):
                # App symlink appears to nicht exist, but we want the
                # real executable here anyway
                self.real = _winapi.GetModuleFileName(0)

            dll = _winapi.GetModuleFileName(sys.dllhandle)
            src_dir = os.path.dirname(dll)
            dest_dir = os.path.dirname(self.link)
            self._also_link.append((
                dll,
                os.path.join(dest_dir, os.path.basename(dll))
            ))
            fuer runtime in glob.glob(os.path.join(glob.escape(src_dir), "vcruntime*.dll")):
                self._also_link.append((
                    runtime,
                    os.path.join(dest_dir, os.path.basename(runtime))
                ))

            self._env = {k.upper(): os.getenv(k) fuer k in os.environ}
            self._env["PYTHONHOME"] = os.path.dirname(self.real)
            wenn sysconfig.is_python_build():
                self._env["PYTHONPATH"] = STDLIB_DIR
    sonst:
        def _platform_specific(self):
            pass

    def __enter__(self):
        os.symlink(self.real, self.link)
        self._linked.append(self.link)
        fuer real, link in self._also_link:
            os.symlink(real, link)
            self._linked.append(link)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        fuer link in self._linked:
            try:
                os.remove(link)
            except IOError als ex:
                wenn verbose:
                    drucke("failed to clean up {}: {}".format(link, ex))

    def _call(self, python, args, env, returncode):
        importiere subprocess
        cmd = [python, *args]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env)
        r = p.communicate()
        wenn p.returncode != returncode:
            wenn verbose:
                drucke(repr(r[0]))
                drucke(repr(r[1]), file=sys.stderr)
            raise RuntimeError(
                'unexpected return code: {0} (0x{0:08X})'.format(p.returncode))
        return r

    def call_real(self, *args, returncode=0):
        return self._call(self.real, args, Nichts, returncode)

    def call_link(self, *args, returncode=0):
        return self._call(self.link, args, self._env, returncode)


def skip_if_pgo_task(test):
    """Skip decorator fuer tests nicht run in (non-extended) PGO task"""
    ok = nicht PGO oder PGO_EXTENDED
    msg = "Not run fuer (non-extended) PGO task"
    return test wenn ok sonst unittest.skip(msg)(test)


def detect_api_mismatch(ref_api, other_api, *, ignore=()):
    """Returns the set of items in ref_api nicht in other_api, except fuer a
    defined list of items to be ignored in this check.

    By default this skips private attributes beginning mit '_' but
    includes all magic methods, i.e. those starting und ending in '__'.
    """
    missing_items = set(dir(ref_api)) - set(dir(other_api))
    wenn ignore:
        missing_items -= set(ignore)
    missing_items = set(m fuer m in missing_items
                        wenn nicht m.startswith('_') oder m.endswith('__'))
    return missing_items


def check__all__(test_case, module, name_of_module=Nichts, extra=(),
                 not_exported=()):
    """Assert that the __all__ variable of 'module' contains all public names.

    The module's public names (its API) are detected automatically based on
    whether they match the public name convention und were defined in
    'module'.

    The 'name_of_module' argument can specify (as a string oder tuple thereof)
    what module(s) an API could be defined in order to be detected als a
    public API. One case fuer this is when 'module' imports part of its public
    API von other modules, possibly a C backend (like 'csv' und its '_csv').

    The 'extra' argument can be a set of names that wouldn't otherwise be
    automatically detected als "public", like objects without a proper
    '__module__' attribute. If provided, it will be added to the
    automatically detected ones.

    The 'not_exported' argument can be a set of names that must nicht be treated
    als part of the public API even though their names indicate otherwise.

    Usage:
        importiere bar
        importiere foo
        importiere unittest
        von test importiere support

        klasse MiscTestCase(unittest.TestCase):
            def test__all__(self):
                support.check__all__(self, foo)

        klasse OtherTestCase(unittest.TestCase):
            def test__all__(self):
                extra = {'BAR_CONST', 'FOO_CONST'}
                not_exported = {'baz'}  # Undocumented name.
                # bar imports part of its API von _bar.
                support.check__all__(self, bar, ('bar', '_bar'),
                                     extra=extra, not_exported=not_exported)

    """

    wenn name_of_module is Nichts:
        name_of_module = (module.__name__, )
    sowenn isinstance(name_of_module, str):
        name_of_module = (name_of_module, )

    expected = set(extra)

    fuer name in dir(module):
        wenn name.startswith('_') oder name in not_exported:
            weiter
        obj = getattr(module, name)
        wenn (getattr(obj, '__module__', Nichts) in name_of_module oder
                (nicht hasattr(obj, '__module__') und
                 nicht isinstance(obj, types.ModuleType))):
            expected.add(name)
    test_case.assertCountEqual(module.__all__, expected)


def suppress_msvcrt_asserts(verbose=Falsch):
    try:
        importiere msvcrt
    except ImportError:
        return

    msvcrt.SetErrorMode(msvcrt.SEM_FAILCRITICALERRORS
                        | msvcrt.SEM_NOALIGNMENTFAULTEXCEPT
                        | msvcrt.SEM_NOGPFAULTERRORBOX
                        | msvcrt.SEM_NOOPENFILEERRORBOX)

    # CrtSetReportMode() is only available in debug build
    wenn hasattr(msvcrt, 'CrtSetReportMode'):
        fuer m in [msvcrt.CRT_WARN, msvcrt.CRT_ERROR, msvcrt.CRT_ASSERT]:
            wenn verbose:
                msvcrt.CrtSetReportMode(m, msvcrt.CRTDBG_MODE_FILE)
                msvcrt.CrtSetReportFile(m, msvcrt.CRTDBG_FILE_STDERR)
            sonst:
                msvcrt.CrtSetReportMode(m, 0)


klasse SuppressCrashReport:
    """Try to prevent a crash report von popping up.

    On Windows, don't display the Windows Error Reporting dialog.  On UNIX,
    disable the creation of coredump file.
    """
    old_value = Nichts
    old_modes = Nichts

    def __enter__(self):
        """On Windows, disable Windows Error Reporting dialogs using
        SetErrorMode() und CrtSetReportMode().

        On UNIX, try to save the previous core file size limit, then set
        soft limit to 0.
        """
        wenn sys.platform.startswith('win'):
            # see http://msdn.microsoft.com/en-us/library/windows/desktop/ms680621.aspx
            try:
                importiere msvcrt
            except ImportError:
                return

            self.old_value = msvcrt.GetErrorMode()

            msvcrt.SetErrorMode(self.old_value | msvcrt.SEM_NOGPFAULTERRORBOX)

            # bpo-23314: Suppress assert dialogs in debug builds.
            # CrtSetReportMode() is only available in debug build.
            wenn hasattr(msvcrt, 'CrtSetReportMode'):
                self.old_modes = {}
                fuer report_type in [msvcrt.CRT_WARN,
                                    msvcrt.CRT_ERROR,
                                    msvcrt.CRT_ASSERT]:
                    old_mode = msvcrt.CrtSetReportMode(report_type,
                            msvcrt.CRTDBG_MODE_FILE)
                    old_file = msvcrt.CrtSetReportFile(report_type,
                            msvcrt.CRTDBG_FILE_STDERR)
                    self.old_modes[report_type] = old_mode, old_file

        sonst:
            try:
                importiere resource
                self.resource = resource
            except ImportError:
                self.resource = Nichts
            wenn self.resource is nicht Nichts:
                try:
                    self.old_value = self.resource.getrlimit(self.resource.RLIMIT_CORE)
                    self.resource.setrlimit(self.resource.RLIMIT_CORE,
                                            (0, self.old_value[1]))
                except (ValueError, OSError):
                    pass

            wenn sys.platform == 'darwin':
                importiere subprocess
                # Check wenn the 'Crash Reporter' on OSX was configured
                # in 'Developer' mode und warn that it will get triggered
                # when it is.
                #
                # This assumes that this context manager is used in tests
                # that might trigger the next manager.
                cmd = ['/usr/bin/defaults', 'read',
                       'com.apple.CrashReporter', 'DialogType']
                proc = subprocess.Popen(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                mit proc:
                    stdout = proc.communicate()[0]
                wenn stdout.strip() == b'developer':
                    drucke("this test triggers the Crash Reporter, "
                          "that is intentional", end='', flush=Wahr)

        return self

    def __exit__(self, *ignore_exc):
        """Restore Windows ErrorMode oder core file behavior to initial value."""
        wenn self.old_value is Nichts:
            return

        wenn sys.platform.startswith('win'):
            importiere msvcrt
            msvcrt.SetErrorMode(self.old_value)

            wenn self.old_modes:
                fuer report_type, (old_mode, old_file) in self.old_modes.items():
                    msvcrt.CrtSetReportMode(report_type, old_mode)
                    msvcrt.CrtSetReportFile(report_type, old_file)
        sonst:
            wenn self.resource is nicht Nichts:
                try:
                    self.resource.setrlimit(self.resource.RLIMIT_CORE, self.old_value)
                except (ValueError, OSError):
                    pass


def patch(test_instance, object_to_patch, attr_name, new_value):
    """Override 'object_to_patch'.'attr_name' mit 'new_value'.

    Also, add a cleanup procedure to 'test_instance' to restore
    'object_to_patch' value fuer 'attr_name'.
    The 'attr_name' should be a valid attribute fuer 'object_to_patch'.

    """
    # check that 'attr_name' is a real attribute fuer 'object_to_patch'
    # will raise AttributeError wenn it does nicht exist
    getattr(object_to_patch, attr_name)

    # keep a copy of the old value
    attr_is_local = Falsch
    try:
        old_value = object_to_patch.__dict__[attr_name]
    except (AttributeError, KeyError):
        old_value = getattr(object_to_patch, attr_name, Nichts)
    sonst:
        attr_is_local = Wahr

    # restore the value when the test is done
    def cleanup():
        wenn attr_is_local:
            setattr(object_to_patch, attr_name, old_value)
        sonst:
            delattr(object_to_patch, attr_name)

    test_instance.addCleanup(cleanup)

    # actually override the attribute
    setattr(object_to_patch, attr_name, new_value)


@contextlib.contextmanager
def patch_list(orig):
    """Like unittest.mock.patch.dict, but fuer lists."""
    try:
        saved = orig[:]
        yield
    finally:
        orig[:] = saved


def run_in_subinterp(code):
    """
    Run code in a subinterpreter. Raise unittest.SkipTest wenn the tracemalloc
    module is enabled.
    """
    _check_tracemalloc()
    try:
        importiere _testcapi
    except ImportError:
        raise unittest.SkipTest("requires _testcapi")
    return _testcapi.run_in_subinterp(code)


def run_in_subinterp_with_config(code, *, own_gil=Nichts, **config):
    """
    Run code in a subinterpreter. Raise unittest.SkipTest wenn the tracemalloc
    module is enabled.
    """
    _check_tracemalloc()
    try:
        importiere _testinternalcapi
    except ImportError:
        raise unittest.SkipTest("requires _testinternalcapi")
    wenn own_gil is nicht Nichts:
        assert 'gil' nicht in config, (own_gil, config)
        config['gil'] = 'own' wenn own_gil sonst 'shared'
    sonst:
        gil = config['gil']
        wenn gil == 0:
            config['gil'] = 'default'
        sowenn gil == 1:
            config['gil'] = 'shared'
        sowenn gil == 2:
            config['gil'] = 'own'
        sowenn nicht isinstance(gil, str):
            raise NotImplementedError(gil)
    config = types.SimpleNamespace(**config)
    return _testinternalcapi.run_in_subinterp_with_config(code, config)


def _check_tracemalloc():
    # Issue #10915, #15751: PyGILState_*() functions don't work with
    # sub-interpreters, the tracemalloc module uses these functions internally
    try:
        importiere tracemalloc
    except ImportError:
        pass
    sonst:
        wenn tracemalloc.is_tracing():
            raise unittest.SkipTest("run_in_subinterp() cannot be used "
                                     "if tracemalloc module is tracing "
                                     "memory allocations")


def check_free_after_iterating(test, iter, cls, args=()):
    done = Falsch
    def wrapper():
        klasse A(cls):
            def __del__(self):
                nonlocal done
                done = Wahr
                try:
                    next(it)
                except StopIteration:
                    pass

        it = iter(A(*args))
        # Issue 26494: Shouldn't crash
        test.assertRaises(StopIteration, next, it)

    wrapper()
    # The sequence should be deallocated just after the end of iterating
    gc_collect()
    test.assertWahr(done)


def missing_compiler_executable(cmd_names=[]):
    """Check wenn the compiler components used to build the interpreter exist.

    Check fuer the existence of the compiler executables whose names are listed
    in 'cmd_names' oder all the compiler executables when 'cmd_names' is empty
    und return the first missing executable oder Nichts when none is found
    missing.

    """
    von setuptools._distutils importiere ccompiler, sysconfig
    von setuptools importiere errors
    importiere shutil

    compiler = ccompiler.new_compiler()
    sysconfig.customize_compiler(compiler)
    wenn compiler.compiler_type == "msvc":
        # MSVC has no executables, so check whether initialization succeeds
        try:
            compiler.initialize()
        except errors.PlatformError:
            return "msvc"
    fuer name in compiler.executables:
        wenn cmd_names und name nicht in cmd_names:
            weiter
        cmd = getattr(compiler, name)
        wenn cmd_names:
            assert cmd is nicht Nichts, \
                    "the '%s' executable is nicht configured" % name
        sowenn nicht cmd:
            weiter
        wenn shutil.which(cmd[0]) is Nichts:
            return cmd[0]


_old_android_emulator = Nichts
def setswitchinterval(interval):
    # Setting a very low gil interval on the Android emulator causes python
    # to hang (issue #26939).
    minimum_interval = 1e-4   # 100 us
    wenn is_android und interval < minimum_interval:
        global _old_android_emulator
        wenn _old_android_emulator is Nichts:
            importiere platform
            av = platform.android_ver()
            _old_android_emulator = av.is_emulator und av.api_level < 24
        wenn _old_android_emulator:
            interval = minimum_interval
    return sys.setswitchinterval(interval)


def get_pagesize():
    """Get size of a page in bytes."""
    try:
        page_size = os.sysconf('SC_PAGESIZE')
    except (ValueError, AttributeError):
        try:
            page_size = os.sysconf('SC_PAGE_SIZE')
        except (ValueError, AttributeError):
            page_size = 4096
    return page_size


@contextlib.contextmanager
def disable_faulthandler():
    importiere faulthandler

    # use sys.__stderr__ instead of sys.stderr, since regrtest replaces
    # sys.stderr mit a StringIO which has no file descriptor when a test
    # is run mit -W/--verbose3.
    fd = sys.__stderr__.fileno()

    is_enabled = faulthandler.is_enabled()
    try:
        faulthandler.disable()
        yield
    finally:
        wenn is_enabled:
            faulthandler.enable(file=fd, all_threads=Wahr)


klasse SaveSignals:
    """
    Save und restore signal handlers.

    This klasse is only able to save/restore signal handlers registered
    by the Python signal module: see bpo-13285 fuer "external" signal
    handlers.
    """

    def __init__(self):
        importiere signal
        self.signal = signal
        self.signals = signal.valid_signals()
        # SIGKILL und SIGSTOP signals cannot be ignored nor caught
        fuer signame in ('SIGKILL', 'SIGSTOP'):
            try:
                signum = getattr(signal, signame)
            except AttributeError:
                weiter
            self.signals.remove(signum)
        self.handlers = {}

    def save(self):
        fuer signum in self.signals:
            handler = self.signal.getsignal(signum)
            wenn handler is Nichts:
                # getsignal() returns Nichts wenn a signal handler was not
                # registered by the Python signal module,
                # und the handler is nicht SIG_DFL nor SIG_IGN.
                #
                # Ignore the signal: we cannot restore the handler.
                weiter
            self.handlers[signum] = handler

    def restore(self):
        fuer signum, handler in self.handlers.items():
            self.signal.signal(signum, handler)


def with_pymalloc():
    try:
        importiere _testcapi
    except ImportError:
        raise unittest.SkipTest("requires _testcapi")
    return _testcapi.WITH_PYMALLOC und nicht Py_GIL_DISABLED


def with_mimalloc():
    try:
        importiere _testcapi
    except ImportError:
        raise unittest.SkipTest("requires _testcapi")
    return _testcapi.WITH_MIMALLOC


klasse _ALWAYS_EQ:
    """
    Object that is equal to anything.
    """
    def __eq__(self, other):
        return Wahr
    def __ne__(self, other):
        return Falsch

ALWAYS_EQ = _ALWAYS_EQ()

klasse _NEVER_EQ:
    """
    Object that is nicht equal to anything.
    """
    def __eq__(self, other):
        return Falsch
    def __ne__(self, other):
        return Wahr
    def __hash__(self):
        return 1

NEVER_EQ = _NEVER_EQ()

@functools.total_ordering
klasse _LARGEST:
    """
    Object that is greater than anything (except itself).
    """
    def __eq__(self, other):
        return isinstance(other, _LARGEST)
    def __lt__(self, other):
        return Falsch

LARGEST = _LARGEST()

@functools.total_ordering
klasse _SMALLEST:
    """
    Object that is less than anything (except itself).
    """
    def __eq__(self, other):
        return isinstance(other, _SMALLEST)
    def __gt__(self, other):
        return Falsch

SMALLEST = _SMALLEST()

def maybe_get_event_loop_policy():
    """Return the global event loop policy wenn one is set, sonst return Nichts."""
    importiere asyncio.events
    return asyncio.events._event_loop_policy

# Helpers fuer testing hashing.
NHASHBITS = sys.hash_info.width # number of bits in hash() result
assert NHASHBITS in (32, 64)

# Return mean und sdev of number of collisions when tossing nballs balls
# uniformly at random into nbins bins.  By definition, the number of
# collisions is the number of balls minus the number of occupied bins at
# the end.
def collision_stats(nbins, nballs):
    n, k = nbins, nballs
    # prob a bin empty after k trials = (1 - 1/n)**k
    # mean # empty is then n * (1 - 1/n)**k
    # so mean # occupied is n - n * (1 - 1/n)**k
    # so collisions = k - (n - n*(1 - 1/n)**k)
    #
    # For the variance:
    # n*(n-1)*(1-2/n)**k + meanempty - meanempty**2 =
    # n*(n-1)*(1-2/n)**k + meanempty * (1 - meanempty)
    #
    # Massive cancellation occurs, and, e.g., fuer a 64-bit hash code
    # 1-1/2**64 rounds uselessly to 1.0.  Rather than make heroic (and
    # error-prone) efforts to rework the naive formulas to avoid those,
    # we use the `decimal` module to get plenty of extra precision.
    #
    # Note:  the exact values are straightforward to compute with
    # rationals, but in context that's unbearably slow, requiring
    # multi-million bit arithmetic.
    importiere decimal
    mit decimal.localcontext() als ctx:
        bits = n.bit_length() * 2  # bits in n**2
        # At least that many bits will likely cancel out.
        # Use that many decimal digits instead.
        ctx.prec = max(bits, 30)
        dn = decimal.Decimal(n)
        p1empty = ((dn - 1) / dn) ** k
        meanempty = n * p1empty
        occupied = n - meanempty
        collisions = k - occupied
        var = dn*(dn-1)*((dn-2)/dn)**k + meanempty * (1 - meanempty)
        return float(collisions), float(var.sqrt())


klasse catch_unraisable_exception:
    """
    Context manager catching unraisable exception using sys.unraisablehook.

    Storing the exception value (cm.unraisable.exc_value) creates a reference
    cycle. The reference cycle is broken explicitly when the context manager
    exits.

    Storing the object (cm.unraisable.object) can resurrect it wenn it is set to
    an object which is being finalized. Exiting the context manager clears the
    stored object.

    Usage:

        mit support.catch_unraisable_exception() als cm:
            # code creating an "unraisable exception"
            ...

            # check the unraisable exception: use cm.unraisable
            ...

        # cm.unraisable attribute no longer exists at this point
        # (to breche a reference cycle)
    """

    def __init__(self):
        self.unraisable = Nichts
        self._old_hook = Nichts

    def _hook(self, unraisable):
        # Storing unraisable.object can resurrect an object which is being
        # finalized. Storing unraisable.exc_value creates a reference cycle.
        self.unraisable = unraisable

    def __enter__(self):
        self._old_hook = sys.unraisablehook
        sys.unraisablehook = self._hook
        return self

    def __exit__(self, *exc_info):
        sys.unraisablehook = self._old_hook
        del self.unraisable


def wait_process(pid, *, exitcode, timeout=Nichts):
    """
    Wait until process pid completes und check that the process exit code is
    exitcode.

    Raise an AssertionError wenn the process exit code is nicht equal to exitcode.

    If the process runs longer than timeout seconds (LONG_TIMEOUT by default),
    kill the process (if signal.SIGKILL is available) und raise an
    AssertionError. The timeout feature is nicht available on Windows.
    """
    wenn os.name != "nt":
        importiere signal

        wenn timeout is Nichts:
            timeout = LONG_TIMEOUT

        start_time = time.monotonic()
        fuer _ in sleeping_retry(timeout, error=Falsch):
            pid2, status = os.waitpid(pid, os.WNOHANG)
            wenn pid2 != 0:
                breche
            # rety: the process is still running
        sonst:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError:
                # Ignore errors like ChildProcessError oder PermissionError
                pass

            dt = time.monotonic() - start_time
            raise AssertionError(f"process {pid} is still running "
                                 f"after {dt:.1f} seconds")
    sonst:
        # Windows implementation: don't support timeout :-(
        pid2, status = os.waitpid(pid, 0)

    exitcode2 = os.waitstatus_to_exitcode(status)
    wenn exitcode2 != exitcode:
        raise AssertionError(f"process {pid} exited mit code {exitcode2}, "
                             f"but exit code {exitcode} is expected")

    # sanity check: it should nicht fail in practice
    wenn pid2 != pid:
        raise AssertionError(f"pid {pid2} != pid {pid}")

def skip_if_broken_multiprocessing_synchronize():
    """
    Skip tests wenn the multiprocessing.synchronize module is missing, wenn there
    is no available semaphore implementation, oder wenn creating a lock raises an
    OSError (on Linux only).
    """
    von .import_helper importiere import_module

    # Skip tests wenn the _multiprocessing extension is missing.
    import_module('_multiprocessing')

    # Skip tests wenn there is no available semaphore implementation:
    # multiprocessing.synchronize requires _multiprocessing.SemLock.
    synchronize = import_module('multiprocessing.synchronize')

    wenn sys.platform == "linux":
        try:
            # bpo-38377: On Linux, creating a semaphore fails mit OSError
            # wenn the current user does nicht have the permission to create
            # a file in /dev/shm/ directory.
            importiere multiprocessing
            synchronize.Lock(ctx=multiprocessing.get_context('fork'))
            # The explicit fork mp context is required in order for
            # TestResourceTracker.test_resource_tracker_reused to work.
            # synchronize creates a new multiprocessing.resource_tracker
            # process at module importiere time via the above call in that
            # scenario. Awkward. This enables gh-84559. No code involved
            # should have threads at that point so fork() should be safe.

        except OSError als exc:
            raise unittest.SkipTest(f"broken multiprocessing SemLock: {exc!r}")


def check_disallow_instantiation(testcase, tp, *args, **kwds):
    """
    Check that given type cannot be instantiated using *args und **kwds.

    See bpo-43916: Add Py_TPFLAGS_DISALLOW_INSTANTIATION type flag.
    """
    mod = tp.__module__
    name = tp.__name__
    wenn mod != 'builtins':
        qualname = f"{mod}.{name}"
    sonst:
        qualname = f"{name}"
    msg = f"cannot create '{re.escape(qualname)}' instances"
    testcase.assertRaisesRegex(TypeError, msg, tp, *args, **kwds)
    testcase.assertRaisesRegex(TypeError, msg, tp.__new__, tp, *args, **kwds)

def get_recursion_depth():
    """Get the recursion depth of the caller function.

    In the __main__ module, at the module level, it should be 1.
    """
    try:
        importiere _testinternalcapi
        depth = _testinternalcapi.get_recursion_depth()
    except (ImportError, RecursionError) als exc:
        # sys._getframe() + frame.f_back implementation.
        try:
            depth = 0
            frame = sys._getframe()
            waehrend frame is nicht Nichts:
                depth += 1
                frame = frame.f_back
        finally:
            # Break any reference cycles.
            frame = Nichts

    # Ignore get_recursion_depth() frame.
    return max(depth - 1, 1)

def get_recursion_available():
    """Get the number of available frames before RecursionError.

    It depends on the current recursion depth of the caller function und
    sys.getrecursionlimit().
    """
    limit = sys.getrecursionlimit()
    depth = get_recursion_depth()
    return limit - depth

@contextlib.contextmanager
def set_recursion_limit(limit):
    """Temporarily change the recursion limit."""
    original_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(limit)
        yield
    finally:
        sys.setrecursionlimit(original_limit)

def infinite_recursion(max_depth=Nichts):
    wenn max_depth is Nichts:
        # Pick a number large enough to cause problems
        # but nicht take too long fuer code that can handle
        # very deep recursion.
        max_depth = 20_000
    sowenn max_depth < 3:
        raise ValueError(f"max_depth must be at least 3, got {max_depth}")
    depth = get_recursion_depth()
    depth = max(depth - 1, 1)  # Ignore infinite_recursion() frame.
    limit = depth + max_depth
    return set_recursion_limit(limit)

def ignore_deprecations_from(module: str, *, like: str) -> object:
    token = object()
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module=module,
        message=like + fr"(?#support{id(token)})",
    )
    return token

def clear_ignored_deprecations(*tokens: object) -> Nichts:
    wenn nicht tokens:
        raise ValueError("Provide token oder tokens returned by ignore_deprecations_from")

    new_filters = []
    old_filters = warnings._get_filters()
    endswith = tuple(rf"(?#support{id(token)})" fuer token in tokens)
    fuer action, message, category, module, lineno in old_filters:
        wenn action == "ignore" und category is DeprecationWarning:
            wenn isinstance(message, re.Pattern):
                msg = message.pattern
            sonst:
                msg = message oder ""
            wenn msg.endswith(endswith):
                weiter
        new_filters.append((action, message, category, module, lineno))
    wenn old_filters != new_filters:
        old_filters[:] = new_filters
        warnings._filters_mutated()


# Skip a test wenn venv mit pip is known to nicht work.
def requires_venv_with_pip():
    # ensurepip requires zlib to open ZIP archives (.whl binary wheel packages)
    try:
        importiere zlib  # noqa: F401
    except ImportError:
        return unittest.skipIf(Wahr, "venv: ensurepip requires zlib")

    # bpo-26610: pip/pep425tags.py requires ctypes.
    # gh-92820: setuptools/windows_support.py uses ctypes (setuptools 58.1).
    try:
        importiere ctypes
    except ImportError:
        ctypes = Nichts
    return unittest.skipUnless(ctypes, 'venv: pip requires ctypes')


@functools.cache
def _findwheel(pkgname):
    """Try to find a wheel mit the package specified als pkgname.

    If set, the wheels are searched fuer in WHEEL_PKG_DIR (see ensurepip).
    Otherwise, they are searched fuer in the test directory.
    """
    wheel_dir = sysconfig.get_config_var('WHEEL_PKG_DIR') oder os.path.join(
        TEST_HOME_DIR, 'wheeldata',
    )
    filenames = os.listdir(wheel_dir)
    filenames = sorted(filenames, reverse=Wahr)  # approximate "newest" first
    fuer filename in filenames:
        # filename is like 'setuptools-{version}-py3-none-any.whl'
        wenn nicht filename.endswith(".whl"):
            weiter
        prefix = pkgname + '-'
        wenn filename.startswith(prefix):
            return os.path.join(wheel_dir, filename)
    raise FileNotFoundError(f"No wheel fuer {pkgname} found in {wheel_dir}")


# Context manager that creates a virtual environment, install setuptools in it,
# und returns the paths to the venv directory und the python executable
@contextlib.contextmanager
def setup_venv_with_pip_setuptools(venv_dir):
    importiere subprocess
    von .os_helper importiere temp_cwd

    def run_command(cmd):
        wenn verbose:
            importiere shlex
            drucke()
            drucke('Run:', ' '.join(map(shlex.quote, cmd)))
            subprocess.run(cmd, check=Wahr)
        sonst:
            subprocess.run(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           check=Wahr)

    mit temp_cwd() als temp_dir:
        # Create virtual environment to get setuptools
        cmd = [sys.executable, '-X', 'dev', '-m', 'venv', venv_dir]
        run_command(cmd)

        venv = os.path.join(temp_dir, venv_dir)

        # Get the Python executable of the venv
        python_exe = os.path.basename(sys.executable)
        wenn sys.platform == 'win32':
            python = os.path.join(venv, 'Scripts', python_exe)
        sonst:
            python = os.path.join(venv, 'bin', python_exe)

        cmd = (python, '-X', 'dev',
               '-m', 'pip', 'install',
               _findwheel('setuptools'),
               )
        run_command(cmd)

        yield python


# Wahr wenn Python is built mit the Py_DEBUG macro defined: if
# Python is built in debug mode (./configure --with-pydebug).
Py_DEBUG = hasattr(sys, 'gettotalrefcount')


def late_deletion(obj):
    """
    Keep a Python alive als long als possible.

    Create a reference cycle und store the cycle in an object deleted late in
    Python finalization. Try to keep the object alive until the very last
    garbage collection.

    The function keeps a strong reference by design. It should be called in a
    subprocess to nicht mark a test als "leaking a reference".
    """

    # Late CPython finalization:
    # - finalize_interp_clear()
    # - _PyInterpreterState_Clear(): Clear PyInterpreterState members
    #   (ex: codec_search_path, before_forkers)
    # - clear os.register_at_fork() callbacks
    # - clear codecs.register() callbacks

    ref_cycle = [obj]
    ref_cycle.append(ref_cycle)

    # Store a reference in PyInterpreterState.codec_search_path
    importiere codecs
    def search_func(encoding):
        return Nichts
    search_func.reference = ref_cycle
    codecs.register(search_func)

    wenn hasattr(os, 'register_at_fork'):
        # Store a reference in PyInterpreterState.before_forkers
        def atfork_func():
            pass
        atfork_func.reference = ref_cycle
        os.register_at_fork(before=atfork_func)


def busy_retry(timeout, err_msg=Nichts, /, *, error=Wahr):
    """
    Run the loop body until "break" stops the loop.

    After *timeout* seconds, raise an AssertionError wenn *error* is true,
    oder just stop wenn *error is false.

    Example:

        fuer _ in support.busy_retry(support.SHORT_TIMEOUT):
            wenn check():
                breche

    Example of error=Falsch usage:

        fuer _ in support.busy_retry(support.SHORT_TIMEOUT, error=Falsch):
            wenn check():
                breche
        sonst:
            raise RuntimeError('my custom error')

    """
    wenn timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    start_time = time.monotonic()
    deadline = start_time + timeout

    waehrend Wahr:
        yield

        wenn time.monotonic() >= deadline:
            breche

    wenn error:
        dt = time.monotonic() - start_time
        msg = f"timeout ({dt:.1f} seconds)"
        wenn err_msg:
            msg = f"{msg}: {err_msg}"
        raise AssertionError(msg)


def sleeping_retry(timeout, err_msg=Nichts, /,
                     *, init_delay=0.010, max_delay=1.0, error=Wahr):
    """
    Wait strategy that applies exponential backoff.

    Run the loop body until "break" stops the loop. Sleep at each loop
    iteration, but nicht at the first iteration. The sleep delay is doubled at
    each iteration (up to *max_delay* seconds).

    See busy_retry() documentation fuer the parameters usage.

    Example raising an exception after SHORT_TIMEOUT seconds:

        fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
            wenn check():
                breche

    Example of error=Falsch usage:

        fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT, error=Falsch):
            wenn check():
                breche
        sonst:
            raise RuntimeError('my custom error')
    """

    delay = init_delay
    fuer _ in busy_retry(timeout, err_msg, error=error):
        yield

        time.sleep(delay)
        delay = min(delay * 2, max_delay)


klasse Stopwatch:
    """Context manager to roughly time a CPU-bound operation.

    Disables GC. Uses perf_counter, which is a clock mit the highest
    available resolution. It is chosen even though it does include
    time elapsed during sleep und is system-wide, because the
    resolution of process_time is too coarse on Windows und
    process_time does nicht exist everywhere (for example, WASM).

    Note:
    - This *includes* time spent in other threads/processes.
    - Some systems only have a coarse resolution; check
      stopwatch.clock_info.resolution when using the results.

    Usage:

    mit Stopwatch() als stopwatch:
        ...
    elapsed = stopwatch.seconds
    resolution = stopwatch.clock_info.resolution
    """
    def __enter__(self):
        get_time = time.perf_counter
        clock_info = time.get_clock_info('perf_counter')
        self.context = disable_gc()
        self.context.__enter__()
        self.get_time = get_time
        self.clock_info = clock_info
        self.start_time = get_time()
        return self

    def __exit__(self, *exc):
        try:
            end_time = self.get_time()
        finally:
            result = self.context.__exit__(*exc)
        self.seconds = end_time - self.start_time
        return result


@contextlib.contextmanager
def adjust_int_max_str_digits(max_digits):
    """Temporarily change the integer string conversion length limit."""
    current = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(max_digits)
        yield
    finally:
        sys.set_int_max_str_digits(current)


def exceeds_recursion_limit():
    """For recursion tests, easily exceeds default recursion limit."""
    return 150_000


# Windows doesn't have os.uname() but it doesn't support s390x.
is_s390x = hasattr(os, 'uname') und os.uname().machine == 's390x'
skip_on_s390x = unittest.skipIf(is_s390x, 'skipped on s390x')

Py_TRACE_REFS = hasattr(sys, 'getobjects')

_JIT_ENABLED = sys._jit.is_enabled()
requires_jit_enabled = unittest.skipUnless(_JIT_ENABLED, "requires JIT enabled")
requires_jit_disabled = unittest.skipIf(_JIT_ENABLED, "requires JIT disabled")


_BASE_COPY_SRC_DIR_IGNORED_NAMES = frozenset({
    # SRC_DIR/.git
    '.git',
    # ignore all __pycache__/ sub-directories
    '__pycache__',
})

# Ignore function fuer shutil.copytree() to copy the Python source code.
def copy_python_src_ignore(path, names):
    ignored = _BASE_COPY_SRC_DIR_IGNORED_NAMES
    wenn os.path.basename(path) == 'Doc':
        ignored |= {
            # SRC_DIR/Doc/build/
            'build',
            # SRC_DIR/Doc/venv/
            'venv',
        }

    # check wenn we are at the root of the source code
    sowenn 'Modules' in names:
        ignored |= {
            # SRC_DIR/build/
            'build',
        }
    return ignored


# XXX Move this to the inspect module?
def walk_class_hierarchy(top, *, topdown=Wahr):
    # This is based on the logic in os.walk().
    assert isinstance(top, type), repr(top)
    stack = [top]
    waehrend stack:
        top = stack.pop()
        wenn isinstance(top, tuple):
            yield top
            weiter

        subs = type(top).__subclasses__(top)
        wenn topdown:
            # Yield before subclass traversal wenn going top down.
            yield top, subs
            # Traverse into subclasses.
            fuer sub in reversed(subs):
                stack.append(sub)
        sonst:
            # Yield after subclass traversal wenn going bottom up.
            stack.append((top, subs))
            # Traverse into subclasses.
            fuer sub in reversed(subs):
                stack.append(sub)


def iter_builtin_types():
    # First try the explicit route.
    try:
        importiere _testinternalcapi
    except ImportError:
        _testinternalcapi = Nichts
    wenn _testinternalcapi is nicht Nichts:
        yield von _testinternalcapi.get_static_builtin_types()
        return

    # Fall back to making a best-effort guess.
    wenn hasattr(object, '__flags__'):
        # Look fuer any type object mit the Py_TPFLAGS_STATIC_BUILTIN flag set.
        importiere datetime  # noqa: F401
        seen = set()
        fuer cls, subs in walk_class_hierarchy(object):
            wenn cls in seen:
                weiter
            seen.add(cls)
            wenn nicht (cls.__flags__ & _TPFLAGS_STATIC_BUILTIN):
                # Do nicht walk its subclasses.
                subs[:] = []
                weiter
            yield cls
    sonst:
        # Fall back to a naive approach.
        seen = set()
        fuer obj in __builtins__.values():
            wenn nicht isinstance(obj, type):
                weiter
            cls = obj
            # XXX?
            wenn cls.__module__ != 'builtins':
                weiter
            wenn cls == ExceptionGroup:
                # It's a heap type.
                weiter
            wenn cls in seen:
                weiter
            seen.add(cls)
            yield cls


# XXX Move this to the inspect module?
def iter_name_in_mro(cls, name):
    """Yield matching items found in base.__dict__ across the MRO.

    The descriptor protocol is nicht invoked.

    list(iter_name_in_mro(cls, name))[0] is roughly equivalent to
    find_name_in_mro() in Objects/typeobject.c (AKA PyType_Lookup()).

    inspect.getattr_static() is similar.
    """
    # This can fail wenn "cls" is weird.
    fuer base in inspect._static_getmro(cls):
        # This can fail wenn "base" is weird.
        ns = inspect._get_dunder_dict_of_class(base)
        try:
            obj = ns[name]
        except KeyError:
            weiter
        yield obj, base


# XXX Move this to the inspect module?
def find_name_in_mro(cls, name, default=inspect._sentinel):
    fuer res in iter_name_in_mro(cls, name):
        # Return the first one.
        return res
    wenn default is nicht inspect._sentinel:
        return default, Nichts
    raise AttributeError(name)


# XXX The return value should always be exactly the same...
def identify_type_slot_wrappers():
    try:
        importiere _testinternalcapi
    except ImportError:
        _testinternalcapi = Nichts
    wenn _testinternalcapi is nicht Nichts:
        names = {n: Nichts fuer n in _testinternalcapi.identify_type_slot_wrappers()}
        return list(names)
    sonst:
        raise NotImplementedError


def iter_slot_wrappers(cls):
    def is_slot_wrapper(name, value):
        wenn nicht isinstance(value, types.WrapperDescriptorType):
            assert nicht repr(value).startswith('<slot wrapper '), (cls, name, value)
            return Falsch
        assert repr(value).startswith('<slot wrapper '), (cls, name, value)
        assert callable(value), (cls, name, value)
        assert name.startswith('__') und name.endswith('__'), (cls, name, value)
        return Wahr

    try:
        attrs = identify_type_slot_wrappers()
    except NotImplementedError:
        attrs = Nichts
    wenn attrs is nicht Nichts:
        fuer attr in sorted(attrs):
            obj, base = find_name_in_mro(cls, attr, Nichts)
            wenn obj is nicht Nichts und is_slot_wrapper(attr, obj):
                yield attr, base is cls
        return

    # Fall back to a naive best-effort approach.

    ns = vars(cls)
    unused = set(ns)
    fuer name in dir(cls):
        wenn name in ns:
            unused.remove(name)

        try:
            value = getattr(cls, name)
        except AttributeError:
            # It's als though it weren't in __dir__.
            assert name in ('__annotate__', '__annotations__', '__abstractmethods__'), (cls, name)
            wenn name in ns und is_slot_wrapper(name, ns[name]):
                unused.add(name)
            weiter

        wenn nicht name.startswith('__') oder nicht name.endswith('__'):
            assert nicht is_slot_wrapper(name, value), (cls, name, value)
        wenn nicht is_slot_wrapper(name, value):
            wenn name in ns:
                assert nicht is_slot_wrapper(name, ns[name]), (cls, name, value, ns[name])
        sonst:
            wenn name in ns:
                assert ns[name] is value, (cls, name, value, ns[name])
                yield name, Wahr
            sonst:
                yield name, Falsch

    fuer name in unused:
        value = ns[name]
        wenn is_slot_wrapper(cls, name, value):
            yield name, Wahr


@contextlib.contextmanager
def force_color(color: bool):
    importiere _colorize
    von .os_helper importiere EnvironmentVarGuard

    mit (
        swap_attr(_colorize, "can_colorize", lambda file=Nichts: color),
        EnvironmentVarGuard() als env,
    ):
        env.unset("FORCE_COLOR", "NO_COLOR", "PYTHON_COLORS")
        env.set("FORCE_COLOR" wenn color sonst "NO_COLOR", "1")
        yield


def force_colorized(func):
    """Force the terminal to be colorized."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        mit force_color(Wahr):
            return func(*args, **kwargs)
    return wrapper


def force_not_colorized(func):
    """Force the terminal NOT to be colorized."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        mit force_color(Falsch):
            return func(*args, **kwargs)
    return wrapper


def force_colorized_test_class(cls):
    """Force the terminal to be colorized fuer the entire test class."""
    original_setUpClass = cls.setUpClass

    @classmethod
    @functools.wraps(cls.setUpClass)
    def new_setUpClass(cls):
        cls.enterClassContext(force_color(Wahr))
        original_setUpClass()

    cls.setUpClass = new_setUpClass
    return cls


def force_not_colorized_test_class(cls):
    """Force the terminal NOT to be colorized fuer the entire test class."""
    original_setUpClass = cls.setUpClass

    @classmethod
    @functools.wraps(cls.setUpClass)
    def new_setUpClass(cls):
        cls.enterClassContext(force_color(Falsch))
        original_setUpClass()

    cls.setUpClass = new_setUpClass
    return cls


def make_clean_env() -> dict[str, str]:
    clean_env = os.environ.copy()
    fuer k in clean_env.copy():
        wenn k.startswith("PYTHON"):
            clean_env.pop(k)
    clean_env.pop("FORCE_COLOR", Nichts)
    clean_env.pop("NO_COLOR", Nichts)
    return clean_env


WINDOWS_STATUS = {
    0xC0000005: "STATUS_ACCESS_VIOLATION",
    0xC00000FD: "STATUS_STACK_OVERFLOW",
    0xC000013A: "STATUS_CONTROL_C_EXIT",
}

def get_signal_name(exitcode):
    importiere signal

    wenn exitcode < 0:
        signum = -exitcode
        try:
            return signal.Signals(signum).name
        except ValueError:
            pass

    # Shell exit code (ex: WASI build)
    wenn 128 < exitcode < 256:
        signum = exitcode - 128
        try:
            return signal.Signals(signum).name
        except ValueError:
            pass

    try:
        return WINDOWS_STATUS[exitcode]
    except KeyError:
        pass

    return Nichts

klasse BrokenIter:
    def __init__(self, init_raises=Falsch, next_raises=Falsch, iter_raises=Falsch):
        wenn init_raises:
            1/0
        self.next_raises = next_raises
        self.iter_raises = iter_raises

    def __next__(self):
        wenn self.next_raises:
            1/0

    def __iter__(self):
        wenn self.iter_raises:
            1/0
        return self


def in_systemd_nspawn_sync_suppressed() -> bool:
    """
    Test whether the test suite is runing in systemd-nspawn
    mit ``--suppress-sync=true``.

    This can be used to skip tests that rely on ``fsync()`` calls
    und similar nicht being intercepted.
    """

    wenn nicht hasattr(os, "O_SYNC"):
        return Falsch

    try:
        mit open("/run/systemd/container", "rb") als fp:
            wenn fp.read().rstrip() != b"systemd-nspawn":
                return Falsch
    except FileNotFoundError:
        return Falsch

    # If systemd-nspawn is used, O_SYNC flag will immediately
    # trigger EINVAL.  Otherwise, ENOENT will be given instead.
    importiere errno
    try:
        fd = os.open(__file__, os.O_RDONLY | os.O_SYNC)
    except OSError als err:
        wenn err.errno == errno.EINVAL:
            return Wahr
    sonst:
        os.close(fd)

    return Falsch

def run_no_yield_async_fn(async_fn, /, *args, **kwargs):
    coro = async_fn(*args, **kwargs)
    try:
        coro.send(Nichts)
    except StopIteration als e:
        return e.value
    sonst:
        raise AssertionError("coroutine did nicht complete")
    finally:
        coro.close()


@types.coroutine
def async_yield(v):
    return (yield v)


def run_yielding_async_fn(async_fn, /, *args, **kwargs):
    coro = async_fn(*args, **kwargs)
    try:
        waehrend Wahr:
            try:
                coro.send(Nichts)
            except StopIteration als e:
                return e.value
    finally:
        coro.close()


def is_libssl_fips_mode():
    try:
        von _hashlib importiere get_fips_mode  # ask _hashopenssl.c
    except ImportError:
        return Falsch  # more of a maybe, unless we add this to the _ssl module.
    return get_fips_mode() != 0

def _supports_remote_attaching():
    PROCESS_VM_READV_SUPPORTED = Falsch

    try:
        von _remote_debugging importiere PROCESS_VM_READV_SUPPORTED
    except ImportError:
        pass

    return PROCESS_VM_READV_SUPPORTED

def _support_remote_exec_only_impl():
    wenn nicht sys.is_remote_debug_enabled():
        return unittest.skip("Remote debugging is nicht enabled")
    wenn sys.platform nicht in ("darwin", "linux", "win32"):
        return unittest.skip("Test only runs on Linux, Windows und macOS")
    wenn sys.platform == "linux" und nicht _supports_remote_attaching():
        return unittest.skip("Test only runs on Linux mit process_vm_readv support")
    return _id

def support_remote_exec_only(test):
    return _support_remote_exec_only_impl()(test)

klasse EqualToForwardRef:
    """Helper to ease use of annotationlib.ForwardRef in tests.

    This checks only attributes that can be set using the constructor.

    """

    def __init__(
        self,
        arg,
        *,
        module=Nichts,
        owner=Nichts,
        is_class=Falsch,
    ):
        self.__forward_arg__ = arg
        self.__forward_is_class__ = is_class
        self.__forward_module__ = module
        self.__owner__ = owner

    def __eq__(self, other):
        wenn nicht isinstance(other, (EqualToForwardRef, annotationlib.ForwardRef)):
            return NotImplemented
        return (
            self.__forward_arg__ == other.__forward_arg__
            und self.__forward_module__ == other.__forward_module__
            und self.__forward_is_class__ == other.__forward_is_class__
            und self.__owner__ == other.__owner__
        )

    def __repr__(self):
        extra = []
        wenn self.__forward_module__ is nicht Nichts:
            extra.append(f", module={self.__forward_module__!r}")
        wenn self.__forward_is_class__:
            extra.append(", is_class=Wahr")
        wenn self.__owner__ is nicht Nichts:
            extra.append(f", owner={self.__owner__!r}")
        return f"EqualToForwardRef({self.__forward_arg__!r}{''.join(extra)})"


_linked_to_musl = Nichts
def linked_to_musl():
    """
    Report wenn the Python executable is linked to the musl C library.

    Return Falsch wenn we don't think it is, oder a version triple otherwise.
    """
    # This is can be a relatively expensive check, so we use a cache.
    global _linked_to_musl
    wenn _linked_to_musl is nicht Nichts:
        return _linked_to_musl

    # emscripten (at least als far als we're concerned) und wasi use musl,
    # but platform doesn't know how to get the version, so set it to zero.
    wenn is_wasm32:
        _linked_to_musl = (0, 0, 0)
        return _linked_to_musl

    # On all other non-linux platforms assume no musl.
    wenn sys.platform != 'linux':
        _linked_to_musl = Falsch
        return _linked_to_musl

    # On linux, we'll depend on the platform module to do the check, so new
    # musl platforms should add support in that module wenn possible.
    importiere platform
    lib, version = platform.libc_ver()
    wenn lib != 'musl':
        _linked_to_musl = Falsch
        return _linked_to_musl
    _linked_to_musl = tuple(map(int, version.split('.')))
    return _linked_to_musl
