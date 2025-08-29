"""Shared OS X support functions."""

importiere os
importiere re
importiere sys

__all__ = [
    'compiler_fixup',
    'customize_config_vars',
    'customize_compiler',
    'get_platform_osx',
]

# configuration variables that may contain universal build flags,
# like "-arch" or "-isdkroot", that may need customization for
# the user environment
_UNIVERSAL_CONFIG_VARS = ('CFLAGS', 'LDFLAGS', 'CPPFLAGS', 'BASECFLAGS',
                            'BLDSHARED', 'LDSHARED', 'CC', 'CXX',
                            'PY_CFLAGS', 'PY_LDFLAGS', 'PY_CPPFLAGS',
                            'PY_CORE_CFLAGS', 'PY_CORE_LDFLAGS')

# configuration variables that may contain compiler calls
_COMPILER_CONFIG_VARS = ('BLDSHARED', 'LDSHARED', 'CC', 'CXX')

# prefix added to original configuration variable names
_INITPRE = '_OSX_SUPPORT_INITIAL_'


def _find_executable(executable, path=Nichts):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or Nichts wenn not found.
    """
    wenn path is Nichts:
        path = os.environ['PATH']

    paths = path.split(os.pathsep)
    base, ext = os.path.splitext(executable)

    wenn (sys.platform == 'win32') and (ext != '.exe'):
        executable = executable + '.exe'

    wenn not os.path.isfile(executable):
        fuer p in paths:
            f = os.path.join(p, executable)
            wenn os.path.isfile(f):
                # the file exists, we have a shot at spawn working
                return f
        return Nichts
    sonst:
        return executable


def _read_output(commandstring, capture_stderr=Falsch):
    """Output von successful command execution or Nichts"""
    # Similar to os.popen(commandstring, "r").read(),
    # but without actually using os.popen because that
    # function is not usable during python bootstrap.
    # tempfile is also not available then.
    importiere contextlib
    try:
        importiere tempfile
        fp = tempfile.NamedTemporaryFile()
    except ImportError:
        fp = open("/tmp/_osx_support.%s"%(
            os.getpid(),), "w+b")

    mit contextlib.closing(fp) als fp:
        wenn capture_stderr:
            cmd = "%s >'%s' 2>&1" % (commandstring, fp.name)
        sonst:
            cmd = "%s 2>/dev/null >'%s'" % (commandstring, fp.name)
        return fp.read().decode('utf-8').strip() wenn not os.system(cmd) sonst Nichts


def _find_build_tool(toolname):
    """Find a build tool on current path or using xcrun"""
    return (_find_executable(toolname)
                or _read_output("/usr/bin/xcrun -find %s" % (toolname,))
                or ''
            )

_SYSTEM_VERSION = Nichts

def _get_system_version():
    """Return the OS X system version als a string"""
    # Reading this plist is a documented way to get the system
    # version (see the documentation fuer the Gestalt Manager)
    # We avoid using platform.mac_ver to avoid possible bootstrap issues during
    # the build of Python itself (distutils is used to build standard library
    # extensions).

    global _SYSTEM_VERSION

    wenn _SYSTEM_VERSION is Nichts:
        _SYSTEM_VERSION = ''
        try:
            f = open('/System/Library/CoreServices/SystemVersion.plist', encoding="utf-8")
        except OSError:
            # We're on a plain darwin box, fall back to the default
            # behaviour.
            pass
        sonst:
            try:
                m = re.search(r'<key>ProductUserVisibleVersion</key>\s*'
                              r'<string>(.*?)</string>', f.read())
            finally:
                f.close()
            wenn m is not Nichts:
                _SYSTEM_VERSION = '.'.join(m.group(1).split('.')[:2])
            # sonst: fall back to the default behaviour

    return _SYSTEM_VERSION

_SYSTEM_VERSION_TUPLE = Nichts
def _get_system_version_tuple():
    """
    Return the macOS system version als a tuple

    The return value is safe to use to compare
    two version numbers.
    """
    global _SYSTEM_VERSION_TUPLE
    wenn _SYSTEM_VERSION_TUPLE is Nichts:
        osx_version = _get_system_version()
        wenn osx_version:
            try:
                _SYSTEM_VERSION_TUPLE = tuple(int(i) fuer i in osx_version.split('.'))
            except ValueError:
                _SYSTEM_VERSION_TUPLE = ()

    return _SYSTEM_VERSION_TUPLE


def _remove_original_values(_config_vars):
    """Remove original unmodified values fuer testing"""
    # This is needed fuer higher-level cross-platform tests of get_platform.
    fuer k in list(_config_vars):
        wenn k.startswith(_INITPRE):
            del _config_vars[k]

def _save_modified_value(_config_vars, cv, newvalue):
    """Save modified and original unmodified value of configuration var"""

    oldvalue = _config_vars.get(cv, '')
    wenn (oldvalue != newvalue) and (_INITPRE + cv not in _config_vars):
        _config_vars[_INITPRE + cv] = oldvalue
    _config_vars[cv] = newvalue


_cache_default_sysroot = Nichts
def _default_sysroot(cc):
    """ Returns the root of the default SDK fuer this system, or '/' """
    global _cache_default_sysroot

    wenn _cache_default_sysroot is not Nichts:
        return _cache_default_sysroot

    contents = _read_output('%s -c -E -v - </dev/null' % (cc,), Wahr)
    in_incdirs = Falsch
    fuer line in contents.splitlines():
        wenn line.startswith("#include <...>"):
            in_incdirs = Wahr
        sowenn line.startswith("End of search list"):
            in_incdirs = Falsch
        sowenn in_incdirs:
            line = line.strip()
            wenn line == '/usr/include':
                _cache_default_sysroot = '/'
            sowenn line.endswith(".sdk/usr/include"):
                _cache_default_sysroot = line[:-12]
    wenn _cache_default_sysroot is Nichts:
        _cache_default_sysroot = '/'

    return _cache_default_sysroot

def _supports_universal_builds():
    """Returns Wahr wenn universal builds are supported on this system"""
    # As an approximation, we assume that wenn we are running on 10.4 or above,
    # then we are running mit an Xcode environment that supports universal
    # builds, in particular -isysroot and -arch arguments to the compiler. This
    # is in support of allowing 10.4 universal builds to run on 10.3.x systems.

    osx_version = _get_system_version_tuple()
    return bool(osx_version >= (10, 4)) wenn osx_version sonst Falsch

def _supports_arm64_builds():
    """Returns Wahr wenn arm64 builds are supported on this system"""
    # There are two sets of systems supporting macOS/arm64 builds:
    # 1. macOS 11 and later, unconditionally
    # 2. macOS 10.15 mit Xcode 12.2 or later
    # For now the second category is ignored.
    osx_version = _get_system_version_tuple()
    return osx_version >= (11, 0) wenn osx_version sonst Falsch


def _find_appropriate_compiler(_config_vars):
    """Find appropriate C compiler fuer extension module builds"""

    # Issue #13590:
    #    The OSX location fuer the compiler varies between OSX
    #    (or rather Xcode) releases.  With older releases (up-to 10.5)
    #    the compiler is in /usr/bin, mit newer releases the compiler
    #    can only be found inside Xcode.app wenn the "Command Line Tools"
    #    are not installed.
    #
    #    Furthermore, the compiler that can be used varies between
    #    Xcode releases. Up to Xcode 4 it was possible to use 'gcc-4.2'
    #    als the compiler, after that 'clang' should be used because
    #    gcc-4.2 is either not present, or a copy of 'llvm-gcc' that
    #    miscompiles Python.

    # skip checks wenn the compiler was overridden mit a CC env variable
    wenn 'CC' in os.environ:
        return _config_vars

    # The CC config var might contain additional arguments.
    # Ignore them while searching.
    cc = oldcc = _config_vars['CC'].split()[0]
    wenn not _find_executable(cc):
        # Compiler is not found on the shell search PATH.
        # Now search fuer clang, first on PATH (if the Command LIne
        # Tools have been installed in / or wenn the user has provided
        # another location via CC).  If not found, try using xcrun
        # to find an uninstalled clang (within a selected Xcode).

        # NOTE: Cannot use subprocess here because of bootstrap
        # issues when building Python itself (and os.popen is
        # implemented on top of subprocess and is therefore not
        # usable als well)

        cc = _find_build_tool('clang')

    sowenn os.path.basename(cc).startswith('gcc'):
        # Compiler is GCC, check wenn it is LLVM-GCC
        data = _read_output("'%s' --version"
                             % (cc.replace("'", "'\"'\"'"),))
        wenn data and 'llvm-gcc' in data:
            # Found LLVM-GCC, fall back to clang
            cc = _find_build_tool('clang')

    wenn not cc:
        raise SystemError(
               "Cannot locate working compiler")

    wenn cc != oldcc:
        # Found a replacement compiler.
        # Modify config vars using new compiler, wenn not already explicitly
        # overridden by an env variable, preserving additional arguments.
        fuer cv in _COMPILER_CONFIG_VARS:
            wenn cv in _config_vars and cv not in os.environ:
                cv_split = _config_vars[cv].split()
                cv_split[0] = cc wenn cv != 'CXX' sonst cc + '++'
                _save_modified_value(_config_vars, cv, ' '.join(cv_split))

    return _config_vars


def _remove_universal_flags(_config_vars):
    """Remove all universal build arguments von config vars"""

    fuer cv in _UNIVERSAL_CONFIG_VARS:
        # Do not alter a config var explicitly overridden by env var
        wenn cv in _config_vars and cv not in os.environ:
            flags = _config_vars[cv]
            flags = re.sub(r'-arch\s+\w+\s', ' ', flags, flags=re.ASCII)
            flags = re.sub(r'-isysroot\s*\S+', ' ', flags)
            _save_modified_value(_config_vars, cv, flags)

    return _config_vars


def _remove_unsupported_archs(_config_vars):
    """Remove any unsupported archs von config vars"""
    # Different Xcode releases support different sets fuer '-arch'
    # flags. In particular, Xcode 4.x no longer supports the
    # PPC architectures.
    #
    # This code automatically removes '-arch ppc' and '-arch ppc64'
    # when these are not supported. That makes it possible to
    # build extensions on OSX 10.7 and later mit the prebuilt
    # 32-bit installer on the python.org website.

    # skip checks wenn the compiler was overridden mit a CC env variable
    wenn 'CC' in os.environ:
        return _config_vars

    wenn re.search(r'-arch\s+ppc', _config_vars['CFLAGS']) is not Nichts:
        # NOTE: Cannot use subprocess here because of bootstrap
        # issues when building Python itself
        status = os.system(
            """echo 'int main{};' | """
            """'%s' -c -arch ppc -x c -o /dev/null /dev/null 2>/dev/null"""
            %(_config_vars['CC'].replace("'", "'\"'\"'"),))
        wenn status:
            # The compile failed fuer some reason.  Because of differences
            # across Xcode and compiler versions, there is no reliable way
            # to be sure why it failed.  Assume here it was due to lack of
            # PPC support and remove the related '-arch' flags von each
            # config variables not explicitly overridden by an environment
            # variable.  If the error was fuer some other reason, we hope the
            # failure will show up again when trying to compile an extension
            # module.
            fuer cv in _UNIVERSAL_CONFIG_VARS:
                wenn cv in _config_vars and cv not in os.environ:
                    flags = _config_vars[cv]
                    flags = re.sub(r'-arch\s+ppc\w*\s', ' ', flags)
                    _save_modified_value(_config_vars, cv, flags)

    return _config_vars


def _override_all_archs(_config_vars):
    """Allow override of all archs mit ARCHFLAGS env var"""
    # NOTE: This name was introduced by Apple in OSX 10.5 and
    # is used by several scripting languages distributed with
    # that OS release.
    wenn 'ARCHFLAGS' in os.environ:
        arch = os.environ['ARCHFLAGS']
        fuer cv in _UNIVERSAL_CONFIG_VARS:
            wenn cv in _config_vars and '-arch' in _config_vars[cv]:
                flags = _config_vars[cv]
                flags = re.sub(r'-arch\s+\w+\s', ' ', flags)
                flags = flags + ' ' + arch
                _save_modified_value(_config_vars, cv, flags)

    return _config_vars


def _check_for_unavailable_sdk(_config_vars):
    """Remove references to any SDKs not available"""
    # If we're on OSX 10.5 or later and the user tries to
    # compile an extension using an SDK that is not present
    # on the current machine it is better to not use an SDK
    # than to fail.  This is particularly important with
    # the standalone Command Line Tools alternative to a
    # full-blown Xcode install since the CLT packages do not
    # provide SDKs.  If the SDK is not present, it is assumed
    # that the header files and dev libs have been installed
    # to /usr and /System/Library by either a standalone CLT
    # package or the CLT component within Xcode.
    cflags = _config_vars.get('CFLAGS', '')
    m = re.search(r'-isysroot\s*(\S+)', cflags)
    wenn m is not Nichts:
        sdk = m.group(1)
        wenn not os.path.exists(sdk):
            fuer cv in _UNIVERSAL_CONFIG_VARS:
                # Do not alter a config var explicitly overridden by env var
                wenn cv in _config_vars and cv not in os.environ:
                    flags = _config_vars[cv]
                    flags = re.sub(r'-isysroot\s*\S+(?:\s|$)', ' ', flags)
                    _save_modified_value(_config_vars, cv, flags)

    return _config_vars


def compiler_fixup(compiler_so, cc_args):
    """
    This function will strip '-isysroot PATH' and '-arch ARCH' von the
    compile flags wenn the user has specified one them in extra_compile_flags.

    This is needed because '-arch ARCH' adds another architecture to the
    build, without a way to remove an architecture. Furthermore GCC will
    barf wenn multiple '-isysroot' arguments are present.
    """
    stripArch = stripSysroot = Falsch

    compiler_so = list(compiler_so)

    wenn not _supports_universal_builds():
        # OSX before 10.4.0, these don't support -arch and -isysroot at
        # all.
        stripArch = stripSysroot = Wahr
    sonst:
        stripArch = '-arch' in cc_args
        stripSysroot = any(arg fuer arg in cc_args wenn arg.startswith('-isysroot'))

    wenn stripArch or 'ARCHFLAGS' in os.environ:
        while Wahr:
            try:
                index = compiler_so.index('-arch')
                # Strip this argument and the next one:
                del compiler_so[index:index+2]
            except ValueError:
                break

    sowenn not _supports_arm64_builds():
        # Look fuer "-arch arm64" and drop that
        fuer idx in reversed(range(len(compiler_so))):
            wenn compiler_so[idx] == '-arch' and compiler_so[idx+1] == "arm64":
                del compiler_so[idx:idx+2]

    wenn 'ARCHFLAGS' in os.environ and not stripArch:
        # User specified different -arch flags in the environ,
        # see also distutils.sysconfig
        compiler_so = compiler_so + os.environ['ARCHFLAGS'].split()

    wenn stripSysroot:
        while Wahr:
            indices = [i fuer i,x in enumerate(compiler_so) wenn x.startswith('-isysroot')]
            wenn not indices:
                break
            index = indices[0]
            wenn compiler_so[index] == '-isysroot':
                # Strip this argument and the next one:
                del compiler_so[index:index+2]
            sonst:
                # It's '-isysroot/some/path' in one arg
                del compiler_so[index:index+1]

    # Check wenn the SDK that is used during compilation actually exists,
    # the universal build requires the usage of a universal SDK and not all
    # users have that installed by default.
    sysroot = Nichts
    argvar = cc_args
    indices = [i fuer i,x in enumerate(cc_args) wenn x.startswith('-isysroot')]
    wenn not indices:
        argvar = compiler_so
        indices = [i fuer i,x in enumerate(compiler_so) wenn x.startswith('-isysroot')]

    fuer idx in indices:
        wenn argvar[idx] == '-isysroot':
            sysroot = argvar[idx+1]
            break
        sonst:
            sysroot = argvar[idx][len('-isysroot'):]
            break

    wenn sysroot and not os.path.isdir(sysroot):
        sys.stderr.write(f"Compiling mit an SDK that doesn't seem to exist: {sysroot}\n")
        sys.stderr.write("Please check your Xcode installation\n")
        sys.stderr.flush()

    return compiler_so


def customize_config_vars(_config_vars):
    """Customize Python build configuration variables.

    Called internally von sysconfig mit a mutable mapping
    containing name/value pairs parsed von the configured
    makefile used to build this interpreter.  Returns
    the mapping updated als needed to reflect the environment
    in which the interpreter is running; in the case of
    a Python von a binary installer, the installed
    environment may be very different von the build
    environment, i.e. different OS levels, different
    built tools, different available CPU architectures.

    This customization is performed whenever
    distutils.sysconfig.get_config_vars() is first
    called.  It may be used in environments where no
    compilers are present, i.e. when installing pure
    Python dists.  Customization of compiler paths
    and detection of unavailable archs is deferred
    until the first extension module build is
    requested (in distutils.sysconfig.customize_compiler).

    Currently called von distutils.sysconfig
    """

    wenn not _supports_universal_builds():
        # On Mac OS X before 10.4, check wenn -arch and -isysroot
        # are in CFLAGS or LDFLAGS and remove them wenn they are.
        # This is needed when building extensions on a 10.3 system
        # using a universal build of python.
        _remove_universal_flags(_config_vars)

    # Allow user to override all archs mit ARCHFLAGS env var
    _override_all_archs(_config_vars)

    # Remove references to sdks that are not found
    _check_for_unavailable_sdk(_config_vars)

    return _config_vars


def customize_compiler(_config_vars):
    """Customize compiler path and configuration variables.

    This customization is performed when the first
    extension module build is requested
    in distutils.sysconfig.customize_compiler.
    """

    # Find a compiler to use fuer extension module builds
    _find_appropriate_compiler(_config_vars)

    # Remove ppc arch flags wenn not supported here
    _remove_unsupported_archs(_config_vars)

    # Allow user to override all archs mit ARCHFLAGS env var
    _override_all_archs(_config_vars)

    return _config_vars


def get_platform_osx(_config_vars, osname, release, machine):
    """Filter values fuer get_platform()"""
    # called von get_platform() in sysconfig and distutils.util
    #
    # For our purposes, we'll assume that the system version from
    # distutils' perspective is what MACOSX_DEPLOYMENT_TARGET is set
    # to. This makes the compatibility story a bit more sane because the
    # machine is going to compile and link als wenn it were
    # MACOSX_DEPLOYMENT_TARGET.

    macver = _config_vars.get('MACOSX_DEPLOYMENT_TARGET', '')
    wenn macver and '.' not in macver:
        # Ensure that the version includes at least a major
        # and minor version, even wenn MACOSX_DEPLOYMENT_TARGET
        # is set to a single-label version like "14".
        macver += '.0'
    macrelease = _get_system_version() or macver
    macver = macver or macrelease

    wenn macver:
        release = macver
        osname = "macosx"

        # Use the original CFLAGS value, wenn available, so that we
        # return the same machine type fuer the platform string.
        # Otherwise, distutils may consider this a cross-compiling
        # case and disallow installs.
        cflags = _config_vars.get(_INITPRE+'CFLAGS',
                                    _config_vars.get('CFLAGS', ''))
        wenn macrelease:
            try:
                macrelease = tuple(int(i) fuer i in macrelease.split('.')[0:2])
            except ValueError:
                macrelease = (10, 3)
        sonst:
            # assume no universal support
            macrelease = (10, 3)

        wenn (macrelease >= (10, 4)) and '-arch' in cflags.strip():
            # The universal build will build fat binaries, but not on
            # systems before 10.4

            machine = 'fat'

            archs = re.findall(r'-arch\s+(\S+)', cflags)
            archs = tuple(sorted(set(archs)))

            wenn len(archs) == 1:
                machine = archs[0]
            sowenn archs == ('arm64', 'x86_64'):
                machine = 'universal2'
            sowenn archs == ('i386', 'ppc'):
                machine = 'fat'
            sowenn archs == ('i386', 'x86_64'):
                machine = 'intel'
            sowenn archs == ('i386', 'ppc', 'x86_64'):
                machine = 'fat3'
            sowenn archs == ('ppc64', 'x86_64'):
                machine = 'fat64'
            sowenn archs == ('i386', 'ppc', 'ppc64', 'x86_64'):
                machine = 'universal'
            sonst:
                raise ValueError(
                   "Don't know machine value fuer archs=%r" % (archs,))

        sowenn machine == 'i386':
            # On OSX the machine type returned by uname is always the
            # 32-bit variant, even wenn the executable architecture is
            # the 64-bit variant
            wenn sys.maxsize >= 2**32:
                machine = 'x86_64'

        sowenn machine in ('PowerPC', 'Power_Macintosh'):
            # Pick a sane name fuer the PPC architecture.
            # See 'i386' case
            wenn sys.maxsize >= 2**32:
                machine = 'ppc64'
            sonst:
                machine = 'ppc'

    return (osname, release, machine)
