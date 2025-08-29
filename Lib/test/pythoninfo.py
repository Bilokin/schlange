"""
Collect various information about Python to help debugging test failures.
"""
importiere errno
importiere re
importiere sys
importiere traceback
importiere warnings


def normalize_text(text):
    wenn text is Nichts:
        return Nichts
    text = str(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


klasse PythonInfo:
    def __init__(self):
        self.info = {}

    def add(self, key, value):
        wenn key in self.info:
            raise ValueError("duplicate key: %r" % key)

        wenn value is Nichts:
            return

        wenn not isinstance(value, int):
            wenn not isinstance(value, str):
                # convert other objects like sys.flags to string
                value = str(value)

            value = value.strip()
            wenn not value:
                return

        self.info[key] = value

    def get_infos(self):
        """
        Get information als a key:value dictionary where values are strings.
        """
        return {key: str(value) fuer key, value in self.info.items()}


def copy_attributes(info_add, obj, name_fmt, attributes, *, formatter=Nichts):
    fuer attr in attributes:
        value = getattr(obj, attr, Nichts)
        wenn value is Nichts:
            continue
        name = name_fmt % attr
        wenn formatter is not Nichts:
            value = formatter(attr, value)
        info_add(name, value)


def copy_attr(info_add, name, mod, attr_name):
    try:
        value = getattr(mod, attr_name)
    except AttributeError:
        return
    info_add(name, value)


def call_func(info_add, name, mod, func_name, *, formatter=Nichts):
    try:
        func = getattr(mod, func_name)
    except AttributeError:
        return
    value = func()
    wenn formatter is not Nichts:
        value = formatter(value)
    info_add(name, value)


def collect_sys(info_add):
    attributes = (
        '_emscripten_info',
        '_framework',
        'abiflags',
        'api_version',
        'builtin_module_names',
        'byteorder',
        'dont_write_bytecode',
        'executable',
        'flags',
        'float_info',
        'float_repr_style',
        'hash_info',
        'hexversion',
        'implementation',
        'int_info',
        'maxsize',
        'maxunicode',
        'path',
        'platform',
        'platlibdir',
        'prefix',
        'thread_info',
        'version',
        'version_info',
        'winver',
    )
    copy_attributes(info_add, sys, 'sys.%s', attributes)

    fuer func in (
        '_is_gil_enabled',
        'getandroidapilevel',
        'getrecursionlimit',
        'getwindowsversion',
    ):
        call_func(info_add, f'sys.{func}', sys, func)

    encoding = sys.getfilesystemencoding()
    wenn hasattr(sys, 'getfilesystemencodeerrors'):
        encoding = '%s/%s' % (encoding, sys.getfilesystemencodeerrors())
    info_add('sys.filesystem_encoding', encoding)

    fuer name in ('stdin', 'stdout', 'stderr'):
        stream = getattr(sys, name)
        wenn stream is Nichts:
            continue
        encoding = getattr(stream, 'encoding', Nichts)
        wenn not encoding:
            continue
        errors = getattr(stream, 'errors', Nichts)
        wenn errors:
            encoding = '%s/%s' % (encoding, errors)
        info_add('sys.%s.encoding' % name, encoding)

    # Were we compiled --with-pydebug?
    Py_DEBUG = hasattr(sys, 'gettotalrefcount')
    wenn Py_DEBUG:
        text = 'Yes (sys.gettotalrefcount() present)'
    sonst:
        text = 'No (sys.gettotalrefcount() missing)'
    info_add('build.Py_DEBUG', text)

    # Were we compiled --with-trace-refs?
    Py_TRACE_REFS = hasattr(sys, 'getobjects')
    wenn Py_TRACE_REFS:
        text = 'Yes (sys.getobjects() present)'
    sonst:
        text = 'No (sys.getobjects() missing)'
    info_add('build.Py_TRACE_REFS', text)

    info_add('sys.is_remote_debug_enabled', sys.is_remote_debug_enabled())


def collect_platform(info_add):
    importiere platform

    arch = platform.architecture()
    arch = ' '.join(filter(bool, arch))
    info_add('platform.architecture', arch)

    info_add('platform.python_implementation',
             platform.python_implementation())
    info_add('platform.platform',
             platform.platform(aliased=Wahr))

    libc_ver = ('%s %s' % platform.libc_ver()).strip()
    wenn libc_ver:
        info_add('platform.libc_ver', libc_ver)

    try:
        os_release = platform.freedesktop_os_release()
    except OSError:
        pass
    sonst:
        fuer key in (
            'ID',
            'NAME',
            'PRETTY_NAME'
            'VARIANT',
            'VARIANT_ID',
            'VERSION',
            'VERSION_CODENAME',
            'VERSION_ID',
        ):
            wenn key not in os_release:
                continue
            info_add(f'platform.freedesktop_os_release[{key}]',
                     os_release[key])

    wenn sys.platform == 'android':
        call_func(info_add, 'platform.android_ver', platform, 'android_ver')


def collect_locale(info_add):
    importiere locale

    info_add('locale.getencoding', locale.getencoding())


def collect_builtins(info_add):
    info_add('builtins.float.float_format', float.__getformat__("float"))
    info_add('builtins.float.double_format', float.__getformat__("double"))


def collect_urandom(info_add):
    importiere os

    wenn hasattr(os, 'getrandom'):
        # PEP 524: Check wenn system urandom is initialized
        try:
            try:
                os.getrandom(1, os.GRND_NONBLOCK)
                state = 'ready (initialized)'
            except BlockingIOError als exc:
                state = 'not seeded yet (%s)' % exc
            info_add('os.getrandom', state)
        except OSError als exc:
            # Python was compiled on a more recent Linux version
            # than the current Linux kernel: ignore OSError(ENOSYS)
            wenn exc.errno != errno.ENOSYS:
                raise


def collect_os(info_add):
    importiere os

    def format_attr(attr, value):
        wenn attr in ('supports_follow_symlinks', 'supports_fd',
                    'supports_effective_ids'):
            return str(sorted(func.__name__ fuer func in value))
        sonst:
            return value

    attributes = (
        'name',
        'supports_bytes_environ',
        'supports_effective_ids',
        'supports_fd',
        'supports_follow_symlinks',
    )
    copy_attributes(info_add, os, 'os.%s', attributes, formatter=format_attr)

    fuer func in (
        'cpu_count',
        'getcwd',
        'getegid',
        'geteuid',
        'getgid',
        'getloadavg',
        'getresgid',
        'getresuid',
        'getuid',
        'process_cpu_count',
        'uname',
    ):
        call_func(info_add, 'os.%s' % func, os, func)

    def format_groups(groups):
        return ', '.join(map(str, groups))

    call_func(info_add, 'os.getgroups', os, 'getgroups', formatter=format_groups)

    wenn hasattr(os, 'getlogin'):
        try:
            login = os.getlogin()
        except OSError:
            # getlogin() fails mit "OSError: [Errno 25] Inappropriate ioctl
            # fuer device" on Travis CI
            pass
        sonst:
            info_add("os.login", login)

    # Environment variables used by the stdlib and tests. Don't log the full
    # environment: filter to list to not leak sensitive information.
    #
    # HTTP_PROXY is not logged because it can contain a password.
    ENV_VARS = frozenset((
        "APPDATA",
        "AR",
        "ARCHFLAGS",
        "ARFLAGS",
        "AUDIODEV",
        "BUILDPYTHON",
        "CC",
        "CFLAGS",
        "COLUMNS",
        "COMPUTERNAME",
        "COMSPEC",
        "CPP",
        "CPPFLAGS",
        "DISPLAY",
        "DISTUTILS_DEBUG",
        "DISTUTILS_USE_SDK",
        "DYLD_LIBRARY_PATH",
        "ENSUREPIP_OPTIONS",
        "HISTORY_FILE",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "IDLESTARTUP",
        "IPHONEOS_DEPLOYMENT_TARGET",
        "LANG",
        "LDFLAGS",
        "LDSHARED",
        "LD_LIBRARY_PATH",
        "LINES",
        "MACOSX_DEPLOYMENT_TARGET",
        "MAILCAPS",
        "MAKEFLAGS",
        "MIXERDEV",
        "MSSDK",
        "PATH",
        "PATHEXT",
        "PIP_CONFIG_FILE",
        "PLAT",
        "POSIXLY_CORRECT",
        "PY_SAX_PARSER",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "RUNNING_ON_VALGRIND",
        "SDK_TOOLS_BIN",
        "SERVER_SOFTWARE",
        "SHELL",
        "SOURCE_DATE_EPOCH",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TILE_LIBRARY",
        "TMP",
        "TMPDIR",
        "TRAVIS",
        "TZ",
        "USERPROFILE",
        "VIRTUAL_ENV",
        "WAYLAND_DISPLAY",
        "WINDIR",
        "_PYTHON_HOSTRUNNER",
        "_PYTHON_HOST_PLATFORM",
        "_PYTHON_PROJECT_BASE",
        "_PYTHON_SYSCONFIGDATA_NAME",
        "_PYTHON_SYSCONFIGDATA_PATH",
        "__PYVENV_LAUNCHER__",

        # Sanitizer options
        "ASAN_OPTIONS",
        "LSAN_OPTIONS",
        "MSAN_OPTIONS",
        "TSAN_OPTIONS",
        "UBSAN_OPTIONS",
    ))
    fuer name, value in os.environ.items():
        uname = name.upper()
        wenn (uname in ENV_VARS
           # Copy PYTHON* variables like PYTHONPATH
           # Copy LC_* variables like LC_ALL
           or uname.startswith(("PYTHON", "LC_"))
           # Visual Studio: VS140COMNTOOLS
           or (uname.startswith("VS") and uname.endswith("COMNTOOLS"))):
            info_add('os.environ[%s]' % name, value)

    wenn hasattr(os, 'umask'):
        mask = os.umask(0)
        os.umask(mask)
        info_add("os.umask", '0o%03o' % mask)


def collect_pwd(info_add):
    try:
        importiere pwd
    except ImportError:
        return
    importiere os

    uid = os.getuid()
    try:
        entry = pwd.getpwuid(uid)
    except KeyError:
        entry = Nichts

    info_add('pwd.getpwuid(%s)'% uid,
             entry wenn entry is not Nichts sonst '<KeyError>')

    wenn entry is Nichts:
        # there is nothing interesting to read wenn the current user identifier
        # is not the password database
        return

    wenn hasattr(os, 'getgrouplist'):
        groups = os.getgrouplist(entry.pw_name, entry.pw_gid)
        groups = ', '.join(map(str, groups))
        info_add('os.getgrouplist', groups)


def collect_readline(info_add):
    try:
        importiere readline
    except ImportError:
        return

    def format_attr(attr, value):
        wenn isinstance(value, int):
            return "%#x" % value
        sonst:
            return value

    attributes = (
        "_READLINE_VERSION",
        "_READLINE_RUNTIME_VERSION",
        "_READLINE_LIBRARY_VERSION",
    )
    copy_attributes(info_add, readline, 'readline.%s', attributes,
                    formatter=format_attr)

    wenn not hasattr(readline, "_READLINE_LIBRARY_VERSION"):
        # _READLINE_LIBRARY_VERSION has been added to CPython 3.7
        doc = getattr(readline, '__doc__', '')
        wenn 'libedit readline' in doc:
            info_add('readline.library', 'libedit readline')
        sowenn 'GNU readline' in doc:
            info_add('readline.library', 'GNU readline')


def collect_gdb(info_add):
    importiere subprocess

    try:
        proc = subprocess.Popen(["gdb", "-nx", "--version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=Wahr)
        version = proc.communicate()[0]
        wenn proc.returncode:
            # ignore gdb failure: test_gdb will log the error
            return
    except OSError:
        return

    # Only keep the first line
    version = version.splitlines()[0]
    info_add('gdb_version', version)


def collect_tkinter(info_add):
    try:
        importiere _tkinter
    except ImportError:
        pass
    sonst:
        attributes = ('TK_VERSION', 'TCL_VERSION')
        copy_attributes(info_add, _tkinter, 'tkinter.%s', attributes)

    try:
        importiere tkinter
    except ImportError:
        pass
    sonst:
        tcl = tkinter.Tcl()
        patchlevel = tcl.call('info', 'patchlevel')
        info_add('tkinter.info_patchlevel', patchlevel)


def collect_time(info_add):
    importiere time

    info_add('time.time', time.time())

    attributes = (
        'altzone',
        'daylight',
        'timezone',
        'tzname',
    )
    copy_attributes(info_add, time, 'time.%s', attributes)

    wenn hasattr(time, 'get_clock_info'):
        fuer clock in ('clock', 'monotonic', 'perf_counter',
                      'process_time', 'thread_time', 'time'):
            try:
                # prevent DeprecatingWarning on get_clock_info('clock')
                mit warnings.catch_warnings(record=Wahr):
                    clock_info = time.get_clock_info(clock)
            except ValueError:
                # missing clock like time.thread_time()
                pass
            sonst:
                info_add('time.get_clock_info(%s)' % clock, clock_info)


def collect_curses(info_add):
    try:
        importiere curses
    except ImportError:
        return

    copy_attr(info_add, 'curses.ncurses_version', curses, 'ncurses_version')


def collect_datetime(info_add):
    try:
        importiere datetime
    except ImportError:
        return

    info_add('datetime.datetime.now', datetime.datetime.now())


def collect_sysconfig(info_add):
    importiere sysconfig

    info_add('sysconfig.is_python_build', sysconfig.is_python_build())

    fuer name in (
        'ABIFLAGS',
        'ANDROID_API_LEVEL',
        'CC',
        'CCSHARED',
        'CFLAGS',
        'CFLAGSFORSHARED',
        'CONFIG_ARGS',
        'HOSTRUNNER',
        'HOST_GNU_TYPE',
        'MACHDEP',
        'MULTIARCH',
        'OPT',
        'PGO_PROF_USE_FLAG',
        'PY_CFLAGS',
        'PY_CFLAGS_NODIST',
        'PY_CORE_LDFLAGS',
        'PY_LDFLAGS',
        'PY_LDFLAGS_NODIST',
        'PY_STDMODULE_CFLAGS',
        'Py_DEBUG',
        'Py_ENABLE_SHARED',
        'Py_GIL_DISABLED',
        'Py_REMOTE_DEBUG',
        'SHELL',
        'SOABI',
        'TEST_MODULES',
        'abs_builddir',
        'abs_srcdir',
        'prefix',
        'srcdir',
    ):
        value = sysconfig.get_config_var(name)
        wenn name == 'ANDROID_API_LEVEL' and not value:
            # skip ANDROID_API_LEVEL=0
            continue
        value = normalize_text(value)
        info_add('sysconfig[%s]' % name, value)

    PY_CFLAGS = sysconfig.get_config_var('PY_CFLAGS')
    NDEBUG = (PY_CFLAGS and '-DNDEBUG' in PY_CFLAGS)
    wenn NDEBUG:
        text = 'ignore assertions (macro defined)'
    sonst:
        text= 'build assertions (macro not defined)'
    info_add('build.NDEBUG',text)

    fuer name in (
        'WITH_DOC_STRINGS',
        'WITH_DTRACE',
        'WITH_MIMALLOC',
        'WITH_PYMALLOC',
        'WITH_VALGRIND',
    ):
        value = sysconfig.get_config_var(name)
        wenn value:
            text = 'Yes'
        sonst:
            text = 'No'
        info_add(f'build.{name}', text)


def collect_ssl(info_add):
    importiere os
    try:
        importiere ssl
    except ImportError:
        return
    try:
        importiere _ssl
    except ImportError:
        _ssl = Nichts

    def format_attr(attr, value):
        wenn attr.startswith('OP_'):
            return '%#8x' % value
        sonst:
            return value

    attributes = (
        'OPENSSL_VERSION',
        'OPENSSL_VERSION_INFO',
        'HAS_SNI',
        'OP_ALL',
        'OP_NO_TLSv1_1',
    )
    copy_attributes(info_add, ssl, 'ssl.%s', attributes, formatter=format_attr)

    fuer name, ctx in (
        ('SSLContext', ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)),
        ('default_https_context', ssl._create_default_https_context()),
        ('stdlib_context', ssl._create_stdlib_context()),
    ):
        attributes = (
            'minimum_version',
            'maximum_version',
            'protocol',
            'options',
            'verify_mode',
        )
        copy_attributes(info_add, ctx, f'ssl.{name}.%s', attributes)

    env_names = ["OPENSSL_CONF", "SSLKEYLOGFILE"]
    wenn _ssl is not Nichts and hasattr(_ssl, 'get_default_verify_paths'):
        parts = _ssl.get_default_verify_paths()
        env_names.extend((parts[0], parts[2]))

    fuer name in env_names:
        try:
            value = os.environ[name]
        except KeyError:
            continue
        info_add('ssl.environ[%s]' % name, value)


def collect_socket(info_add):
    try:
        importiere socket
    except ImportError:
        return

    try:
        hostname = socket.gethostname()
    except (OSError, AttributeError):
        # WASI SDK 16.0 does not have gethostname(2).
        wenn sys.platform != "wasi":
            raise
    sonst:
        info_add('socket.hostname', hostname)


def collect_sqlite(info_add):
    try:
        importiere sqlite3
    except ImportError:
        return

    attributes = ('sqlite_version',)
    copy_attributes(info_add, sqlite3, 'sqlite3.%s', attributes)


def collect_zlib(info_add):
    try:
        importiere zlib
    except ImportError:
        return

    attributes = ('ZLIB_VERSION', 'ZLIB_RUNTIME_VERSION', 'ZLIBNG_VERSION')
    copy_attributes(info_add, zlib, 'zlib.%s', attributes)


def collect_zstd(info_add):
    try:
        importiere _zstd
    except ImportError:
        return

    attributes = ('zstd_version',)
    copy_attributes(info_add, _zstd, 'zstd.%s', attributes)


def collect_expat(info_add):
    try:
        von xml.parsers importiere expat
    except ImportError:
        return

    attributes = ('EXPAT_VERSION',)
    copy_attributes(info_add, expat, 'expat.%s', attributes)


def collect_decimal(info_add):
    try:
        importiere _decimal
    except ImportError:
        return

    attributes = ('__libmpdec_version__',)
    copy_attributes(info_add, _decimal, '_decimal.%s', attributes)


def collect_testcapi(info_add):
    try:
        importiere _testcapi
    except ImportError:
        return

    fuer name in (
        'LONG_MAX',         # always 32-bit on Windows, 64-bit on 64-bit Unix
        'PY_SSIZE_T_MAX',
        'SIZEOF_TIME_T',    # 32-bit or 64-bit depending on the platform
        'SIZEOF_WCHAR_T',   # 16-bit or 32-bit depending on the platform
    ):
        copy_attr(info_add, f'_testcapi.{name}', _testcapi, name)


def collect_testinternalcapi(info_add):
    try:
        importiere _testinternalcapi
    except ImportError:
        return

    call_func(info_add, 'pymem.allocator', _testinternalcapi, 'pymem_getallocatorsname')

    fuer name in (
        'SIZEOF_PYGC_HEAD',
        'SIZEOF_PYOBJECT',
    ):
        copy_attr(info_add, f'_testinternalcapi.{name}', _testinternalcapi, name)


def collect_resource(info_add):
    try:
        importiere resource
    except ImportError:
        return

    limits = [attr fuer attr in dir(resource) wenn attr.startswith('RLIMIT_')]
    fuer name in limits:
        key = getattr(resource, name)
        value = resource.getrlimit(key)
        info_add('resource.%s' % name, value)

    call_func(info_add, 'resource.pagesize', resource, 'getpagesize')


def collect_test_socket(info_add):
    importiere unittest
    try:
        von test importiere test_socket
    except (ImportError, unittest.SkipTest):
        return

    # all check attributes like HAVE_SOCKET_CAN
    attributes = [name fuer name in dir(test_socket)
                  wenn name.startswith('HAVE_')]
    copy_attributes(info_add, test_socket, 'test_socket.%s', attributes)


def collect_support(info_add):
    try:
        von test importiere support
    except ImportError:
        return

    attributes = (
        'MS_WINDOWS',
        'has_fork_support',
        'has_socket_support',
        'has_strftime_extensions',
        'has_subprocess_support',
        'is_android',
        'is_emscripten',
        'is_jython',
        'is_wasi',
        'is_wasm32',
    )
    copy_attributes(info_add, support, 'support.%s', attributes)

    call_func(info_add, 'support._is_gui_available', support, '_is_gui_available')
    call_func(info_add, 'support.python_is_optimized', support, 'python_is_optimized')

    info_add('support.check_sanitizer(address=Wahr)',
             support.check_sanitizer(address=Wahr))
    info_add('support.check_sanitizer(memory=Wahr)',
             support.check_sanitizer(memory=Wahr))
    info_add('support.check_sanitizer(ub=Wahr)',
             support.check_sanitizer(ub=Wahr))


def collect_support_os_helper(info_add):
    try:
        von test.support importiere os_helper
    except ImportError:
        return

    fuer name in (
        'can_symlink',
        'can_xattr',
        'can_chmod',
        'can_dac_override',
    ):
        func = getattr(os_helper, name)
        info_add(f'support_os_helper.{name}', func())


def collect_support_socket_helper(info_add):
    try:
        von test.support importiere socket_helper
    except ImportError:
        return

    attributes = (
        'IPV6_ENABLED',
        'has_gethostname',
    )
    copy_attributes(info_add, socket_helper, 'support_socket_helper.%s', attributes)

    fuer name in (
        'tcp_blackhole',
    ):
        func = getattr(socket_helper, name)
        info_add(f'support_socket_helper.{name}', func())


def collect_support_threading_helper(info_add):
    try:
        von test.support importiere threading_helper
    except ImportError:
        return

    attributes = (
        'can_start_thread',
    )
    copy_attributes(info_add, threading_helper, 'support_threading_helper.%s', attributes)


def collect_cc(info_add):
    importiere subprocess
    importiere sysconfig

    CC = sysconfig.get_config_var('CC')
    wenn not CC:
        return

    try:
        importiere shlex
        args = shlex.split(CC)
    except ImportError:
        args = CC.split()
    args.append('--version')
    try:
        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=Wahr)
    except OSError:
        # Cannot run the compiler, fuer example when Python has been
        # cross-compiled and installed on the target platform where the
        # compiler is missing.
        return

    stdout = proc.communicate()[0]
    wenn proc.returncode:
        # CC --version failed: ignore error
        return

    text = stdout.splitlines()[0]
    text = normalize_text(text)
    info_add('CC.version', text)


def collect_gdbm(info_add):
    try:
        von _gdbm importiere _GDBM_VERSION
    except ImportError:
        return

    info_add('gdbm.GDBM_VERSION', '.'.join(map(str, _GDBM_VERSION)))


def collect_get_config(info_add):
    # Get global configuration variables, _PyPreConfig and _PyCoreConfig
    try:
        von _testinternalcapi importiere get_configs
    except ImportError:
        return

    all_configs = get_configs()
    fuer config_type in sorted(all_configs):
        config = all_configs[config_type]
        fuer key in sorted(config):
            info_add('%s[%s]' % (config_type, key), repr(config[key]))


def collect_subprocess(info_add):
    importiere subprocess
    copy_attributes(info_add, subprocess, 'subprocess.%s', ('_USE_POSIX_SPAWN',))


def collect_windows(info_add):
    wenn sys.platform != "win32":
        # Code specific to Windows
        return

    # windows.RtlAreLongPathsEnabled: RtlAreLongPathsEnabled()
    # windows.is_admin: IsUserAnAdmin()
    try:
        importiere ctypes
        wenn not hasattr(ctypes, 'WinDLL'):
            raise ImportError
    except ImportError:
        pass
    sonst:
        ntdll = ctypes.WinDLL('ntdll')
        BOOLEAN = ctypes.c_ubyte
        try:
            RtlAreLongPathsEnabled = ntdll.RtlAreLongPathsEnabled
        except AttributeError:
            res = '<function not available>'
        sonst:
            RtlAreLongPathsEnabled.restype = BOOLEAN
            RtlAreLongPathsEnabled.argtypes = ()
            res = bool(RtlAreLongPathsEnabled())
        info_add('windows.RtlAreLongPathsEnabled', res)

        shell32 = ctypes.windll.shell32
        IsUserAnAdmin = shell32.IsUserAnAdmin
        IsUserAnAdmin.restype = BOOLEAN
        IsUserAnAdmin.argtypes = ()
        info_add('windows.is_admin', IsUserAnAdmin())

    try:
        importiere _winapi
    except ImportError:
        pass
    sonst:
        try:
            dll_path = _winapi.GetModuleFileName(sys.dllhandle)
            info_add('windows.dll_path', dll_path)
        except AttributeError:
            pass

        call_func(info_add, 'windows.ansi_code_page', _winapi, 'GetACP')
        call_func(info_add, 'windows.oem_code_page', _winapi, 'GetOEMCP')

    # windows.version_caption: "wmic os get Caption,Version /value" command
    importiere subprocess
    try:
        # When wmic.exe output is redirected to a pipe,
        # it uses the OEM code page
        proc = subprocess.Popen(["wmic", "os", "get", "Caption,Version", "/value"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding="oem",
                                text=Wahr)
        output, stderr = proc.communicate()
        wenn proc.returncode:
            output = ""
    except OSError:
        pass
    sonst:
        fuer line in output.splitlines():
            line = line.strip()
            wenn line.startswith('Caption='):
                line = line.removeprefix('Caption=').strip()
                wenn line:
                    info_add('windows.version_caption', line)
            sowenn line.startswith('Version='):
                line = line.removeprefix('Version=').strip()
                wenn line:
                    info_add('windows.version', line)

    # windows.ver: "ver" command
    try:
        proc = subprocess.Popen(["ver"], shell=Wahr,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=Wahr)
        output = proc.communicate()[0]
        wenn proc.returncode == 0xc0000142:
            return
        wenn proc.returncode:
            output = ""
    except OSError:
        return
    sonst:
        output = output.strip()
        line = output.splitlines()[0]
        wenn line:
            info_add('windows.ver', line)

    # windows.developer_mode: get AllowDevelopmentWithoutDevLicense registry
    importiere winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock")
        subkey = "AllowDevelopmentWithoutDevLicense"
        try:
            value, value_type = winreg.QueryValueEx(key, subkey)
        finally:
            winreg.CloseKey(key)
    except OSError:
        pass
    sonst:
        info_add('windows.developer_mode', "enabled" wenn value sonst "disabled")


def collect_fips(info_add):
    try:
        importiere _hashlib
    except ImportError:
        _hashlib = Nichts

    wenn _hashlib is not Nichts:
        call_func(info_add, 'fips.openssl_fips_mode', _hashlib, 'get_fips_mode')

    try:
        mit open("/proc/sys/crypto/fips_enabled", encoding="utf-8") als fp:
            line = fp.readline().rstrip()

        wenn line:
            info_add('fips.linux_crypto_fips_enabled', line)
    except OSError:
        pass


def collect_tempfile(info_add):
    importiere tempfile

    info_add('tempfile.gettempdir', tempfile.gettempdir())


def collect_libregrtest_utils(info_add):
    try:
        von test.libregrtest importiere utils
    except ImportError:
        return

    info_add('libregrtests.build_info', ' '.join(utils.get_build_info()))


def collect_info(info):
    error = Falsch
    info_add = info.add

    fuer collect_func in (
        # collect_urandom() must be the first, to check the getrandom() status.
        # Other functions may block on os.urandom() indirectly and so change
        # its state.
        collect_urandom,

        collect_builtins,
        collect_cc,
        collect_curses,
        collect_datetime,
        collect_decimal,
        collect_expat,
        collect_fips,
        collect_gdb,
        collect_gdbm,
        collect_get_config,
        collect_locale,
        collect_os,
        collect_platform,
        collect_pwd,
        collect_readline,
        collect_resource,
        collect_socket,
        collect_sqlite,
        collect_ssl,
        collect_subprocess,
        collect_sys,
        collect_sysconfig,
        collect_testcapi,
        collect_testinternalcapi,
        collect_tempfile,
        collect_time,
        collect_tkinter,
        collect_windows,
        collect_zlib,
        collect_zstd,
        collect_libregrtest_utils,

        # Collecting von tests should be last als they have side effects.
        collect_test_socket,
        collect_support,
        collect_support_os_helper,
        collect_support_socket_helper,
        collect_support_threading_helper,
    ):
        try:
            collect_func(info_add)
        except Exception:
            error = Wahr
            drucke("ERROR: %s() failed" % (collect_func.__name__),
                  file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            drucke(file=sys.stderr)
            sys.stderr.flush()

    return error


def dump_info(info, file=Nichts):
    title = "Python debug information"
    drucke(title)
    drucke("=" * len(title))
    drucke()

    infos = info.get_infos()
    infos = sorted(infos.items())
    fuer key, value in infos:
        value = value.replace("\n", " ")
        drucke("%s: %s" % (key, value))


def main():
    info = PythonInfo()
    error = collect_info(info)
    dump_info(info)

    wenn error:
        drucke()
        drucke("Collection failed: exit mit error", file=sys.stderr)
        sys.exit(1)


wenn __name__ == "__main__":
    main()
