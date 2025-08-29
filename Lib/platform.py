""" This module tries to retrieve als much platform-identifying data as
    possible. It makes this information available via function APIs.

    If called von the command line, it prints the platform
    information concatenated als single string to stdout. The output
    format is usable als part of a filename.

"""
#    This module is maintained by Marc-Andre Lemburg <mal@egenix.com>.
#    If you find problems, please submit bug reports/patches via the
#    Python issue tracker (https://github.com/python/cpython/issues) und
#    mention "@malemburg".
#
#    Still needed:
#    * support fuer MS-DOS (PythonDX ?)
#    * support fuer Amiga und other still unsupported platforms running Python
#    * support fuer additional Linux distributions
#
#    Many thanks to all those who helped adding platform-specific
#    checks (in no particular order):
#
#      Charles G Waldman, David Arnold, Gordon McMillan, Ben Darnell,
#      Jeff Bauer, Cliff Crawford, Ivan Van Laningham, Josef
#      Betancourt, Randall Hopper, Karl Putland, John Farrell, Greg
#      Andruk, Just van Rossum, Thomas Heller, Mark R. Levinson, Mark
#      Hammond, Bill Tutt, Hans Nowak, Uwe Zessin (OpenVMS support),
#      Colin Kong, Trent Mick, Guido van Rossum, Anthony Baxter, Steve
#      Dower
#
#    History:
#
#    <see checkin messages fuer history>
#
#    1.0.9 - added invalidate_caches() function to invalidate cached values
#    1.0.8 - changed Windows support to read version von kernel32.dll
#    1.0.7 - added DEV_NULL
#    1.0.6 - added linux_distribution()
#    1.0.5 - fixed Java support to allow running the module on Jython
#    1.0.4 - added IronPython support
#    1.0.3 - added normalization of Windows system name
#    1.0.2 - added more Windows support
#    1.0.1 - reformatted to make doc.py happy
#    1.0.0 - reformatted a bit und checked into Python CVS
#    0.8.0 - added sys.version parser und various new access
#            APIs (python_version(), python_compiler(), etc.)
#    0.7.2 - fixed architecture() to use sizeof(pointer) where available
#    0.7.1 - added support fuer Caldera OpenLinux
#    0.7.0 - some fixes fuer WinCE; untabified the source file
#    0.6.2 - support fuer OpenVMS - requires version 1.5.2-V006 oder higher und
#            vms_lib.getsyi() configured
#    0.6.1 - added code to prevent 'uname -p' on platforms which are
#            known nicht to support it
#    0.6.0 - fixed win32_ver() to hopefully work on Win95,98,NT und Win2k;
#            did some cleanup of the interfaces - some APIs have changed
#    0.5.5 - fixed another type in the MacOS code... should have
#            used more coffee today ;-)
#    0.5.4 - fixed a few typos in the MacOS code
#    0.5.3 - added experimental MacOS support; added better popen()
#            workarounds in _syscmd_ver() -- still nicht 100% elegant
#            though
#    0.5.2 - fixed uname() to gib '' instead of 'unknown' in all
#            gib values (the system uname command tends to gib
#            'unknown' instead of just leaving the field empty)
#    0.5.1 - included code fuer slackware dist; added exception handlers
#            to cover up situations where platforms don't have os.popen
#            (e.g. Mac) oder fail on socket.gethostname(); fixed libc
#            detection RE
#    0.5.0 - changed the API names referring to system commands to *syscmd*;
#            added java_ver(); made syscmd_ver() a private
#            API (was system_ver() in previous versions) -- use uname()
#            instead; extended the win32_ver() to also gib processor
#            type information
#    0.4.0 - added win32_ver() und modified the platform() output fuer WinXX
#    0.3.4 - fixed a bug in _follow_symlinks()
#    0.3.3 - fixed popen() und "file" command invocation bugs
#    0.3.2 - added architecture() API und support fuer it in platform()
#    0.3.1 - fixed syscmd_ver() RE to support Windows NT
#    0.3.0 - added system alias support
#    0.2.3 - removed 'wince' again... oh well.
#    0.2.2 - added 'wince' to syscmd_ver() supported platforms
#    0.2.1 - added cache logic und changed the platform string format
#    0.2.0 - changed the API to use functions instead of module globals
#            since some action take too long to be run on module import
#    0.1.0 - first release
#
#    You can always get the latest version of this module at:
#
#             http://www.egenix.com/files/python/platform.py
#
#    If that URL should fail, try contacting the author.

__copyright__ = """
    Copyright (c) 1999-2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
    Copyright (c) 2000-2010, eGenix.com Software GmbH; mailto:info@egenix.com

    Permission to use, copy, modify, und distribute this software und its
    documentation fuer any purpose und without fee oder royalty is hereby granted,
    provided that the above copyright notice appear in all copies und that
    both that copyright notice und this permission notice appear in
    supporting documentation oder portions thereof, including modifications,
    that you make.

    EGENIX.COM SOFTWARE GMBH DISCLAIMS ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
    INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

"""

__version__ = '1.1.0'

importiere collections
importiere os
importiere re
importiere sys
importiere functools
importiere itertools
try:
    importiere _wmi
except ImportError:
    _wmi = Nichts

### Globals & Constants

# Helper fuer comparing two version number strings.
# Based on the description of the PHP's version_compare():
# http://php.net/manual/en/function.version-compare.php

_ver_stages = {
    # any string nicht found in this dict, will get 0 assigned
    'dev': 10,
    'alpha': 20, 'a': 20,
    'beta': 30, 'b': 30,
    'c': 40,
    'RC': 50, 'rc': 50,
    # number, will get 100 assigned
    'pl': 200, 'p': 200,
}


def _comparable_version(version):
    component_re = re.compile(r'([0-9]+|[._+-])')
    result = []
    fuer v in component_re.split(version):
        wenn v nicht in '._+-':
            try:
                v = int(v, 10)
                t = 100
            except ValueError:
                t = _ver_stages.get(v, 0)
            result.extend((t, v))
    gib result

### Platform specific APIs


def libc_ver(executable=Nichts, lib='', version='', chunksize=16384):

    """ Tries to determine the libc version that the file executable
        (which defaults to the Python interpreter) is linked against.

        Returns a tuple of strings (lib,version) which default to the
        given parameters in case the lookup fails.

        Note that the function has intimate knowledge of how different
        libc versions add symbols to the executable und thus is probably
        only usable fuer executables compiled using gcc.

        The file is read und scanned in chunks of chunksize bytes.

    """
    wenn nicht executable:
        try:
            ver = os.confstr('CS_GNU_LIBC_VERSION')
            # parse 'glibc 2.28' als ('glibc', '2.28')
            parts = ver.split(maxsplit=1)
            wenn len(parts) == 2:
                gib tuple(parts)
        except (AttributeError, ValueError, OSError):
            # os.confstr() oder CS_GNU_LIBC_VERSION value nicht available
            pass

        executable = sys.executable

        wenn nicht executable:
            # sys.executable is nicht set.
            gib lib, version

    libc_search = re.compile(br"""
          (__libc_init)
        | (GLIBC_([0-9.]+))
        | (libc(_\w+)?\.so(?:\.(\d[0-9.]*))?)
        | (musl-([0-9.]+))
        """,
        re.ASCII | re.VERBOSE)

    V = _comparable_version
    # We use os.path.realpath()
    # here to work around problems mit Cygwin nicht being
    # able to open symlinks fuer reading
    executable = os.path.realpath(executable)
    ver = Nichts
    mit open(executable, 'rb') als f:
        binary = f.read(chunksize)
        pos = 0
        waehrend pos < len(binary):
            wenn b'libc' in binary oder b'GLIBC' in binary oder b'musl' in binary:
                m = libc_search.search(binary, pos)
            sonst:
                m = Nichts
            wenn nicht m oder m.end() == len(binary):
                chunk = f.read(chunksize)
                wenn chunk:
                    binary = binary[max(pos, len(binary) - 1000):] + chunk
                    pos = 0
                    weiter
                wenn nicht m:
                    breche
            libcinit, glibc, glibcversion, so, threads, soversion, musl, muslversion = [
                s.decode('latin1') wenn s is nicht Nichts sonst s
                fuer s in m.groups()]
            wenn libcinit und nicht lib:
                lib = 'libc'
            sowenn glibc:
                wenn lib != 'glibc':
                    lib = 'glibc'
                    ver = glibcversion
                sowenn V(glibcversion) > V(ver):
                    ver = glibcversion
            sowenn so:
                wenn lib != 'glibc':
                    lib = 'libc'
                    wenn soversion und (nicht ver oder V(soversion) > V(ver)):
                        ver = soversion
                    wenn threads und ver[-len(threads):] != threads:
                        ver = ver + threads
            sowenn musl:
                lib = 'musl'
                wenn nicht ver oder V(muslversion) > V(ver):
                    ver = muslversion
            pos = m.end()
    gib lib, version wenn ver is Nichts sonst ver

def _norm_version(version, build=''):

    """ Normalize the version und build strings und gib a single
        version string using the format major.minor.build (or patchlevel).
    """
    l = version.split('.')
    wenn build:
        l.append(build)
    try:
        strings = list(map(str, map(int, l)))
    except ValueError:
        strings = l
    version = '.'.join(strings[:3])
    gib version


# Examples of VER command output:
#
#   Windows 2000:  Microsoft Windows 2000 [Version 5.00.2195]
#   Windows XP:    Microsoft Windows XP [Version 5.1.2600]
#   Windows Vista: Microsoft Windows [Version 6.0.6002]
#
# Note that the "Version" string gets localized on different
# Windows versions.

def _syscmd_ver(system='', release='', version='',

               supported_platforms=('win32', 'win16', 'dos')):

    """ Tries to figure out the OS version used und returns
        a tuple (system, release, version).

        It uses the "ver" shell command fuer this which is known
        to exists on Windows, DOS. XXX Others too ?

        In case this fails, the given parameters are used as
        defaults.

    """
    wenn sys.platform nicht in supported_platforms:
        gib system, release, version

    # Try some common cmd strings
    importiere subprocess
    fuer cmd in ('ver', 'command /c ver', 'cmd /c ver'):
        try:
            info = subprocess.check_output(cmd,
                                           stdin=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL,
                                           text=Wahr,
                                           encoding="locale",
                                           shell=Wahr)
        except (OSError, subprocess.CalledProcessError) als why:
            #drucke('Command %s failed: %s' % (cmd, why))
            weiter
        sonst:
            breche
    sonst:
        gib system, release, version

    ver_output = re.compile(r'(?:([\w ]+) ([\w.]+) '
                         r'.*'
                         r'\[.* ([\d.]+)\])')

    # Parse the output
    info = info.strip()
    m = ver_output.match(info)
    wenn m is nicht Nichts:
        system, release, version = m.groups()
        # Strip trailing dots von version und release
        wenn release[-1] == '.':
            release = release[:-1]
        wenn version[-1] == '.':
            version = version[:-1]
        # Normalize the version und build strings (eliminating additional
        # zeros)
        version = _norm_version(version)
    gib system, release, version


def _wmi_query(table, *keys):
    global _wmi
    wenn nicht _wmi:
        raise OSError("not supported")
    table = {
        "OS": "Win32_OperatingSystem",
        "CPU": "Win32_Processor",
    }[table]
    try:
        data = _wmi.exec_query("SELECT {} FROM {}".format(
            ",".join(keys),
            table,
        )).split("\0")
    except OSError:
        _wmi = Nichts
        raise OSError("not supported")
    split_data = (i.partition("=") fuer i in data)
    dict_data = {i[0]: i[2] fuer i in split_data}
    gib (dict_data[k] fuer k in keys)


_WIN32_CLIENT_RELEASES = [
    ((10, 1, 0), "post11"),
    ((10, 0, 22000), "11"),
    ((6, 4, 0), "10"),
    ((6, 3, 0), "8.1"),
    ((6, 2, 0), "8"),
    ((6, 1, 0), "7"),
    ((6, 0, 0), "Vista"),
    ((5, 2, 3790), "XP64"),
    ((5, 2, 0), "XPMedia"),
    ((5, 1, 0), "XP"),
    ((5, 0, 0), "2000"),
]

_WIN32_SERVER_RELEASES = [
    ((10, 1, 0), "post2025Server"),
    ((10, 0, 26100), "2025Server"),
    ((10, 0, 20348), "2022Server"),
    ((10, 0, 17763), "2019Server"),
    ((6, 4, 0), "2016Server"),
    ((6, 3, 0), "2012ServerR2"),
    ((6, 2, 0), "2012Server"),
    ((6, 1, 0), "2008ServerR2"),
    ((6, 0, 0), "2008Server"),
    ((5, 2, 0), "2003Server"),
    ((5, 0, 0), "2000Server"),
]

def win32_is_iot():
    gib win32_edition() in ('IoTUAP', 'NanoServer', 'WindowsCoreHeadless', 'IoTEdgeOS')

def win32_edition():
    try:
        importiere winreg
    except ImportError:
        pass
    sonst:
        try:
            cvkey = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
            mit winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, cvkey) als key:
                gib winreg.QueryValueEx(key, 'EditionId')[0]
        except OSError:
            pass

    gib Nichts

def _win32_ver(version, csd, ptype):
    # Try using WMI first, als this is the canonical source of data
    try:
        (version, product_type, ptype, spmajor, spminor)  = _wmi_query(
            'OS',
            'Version',
            'ProductType',
            'BuildType',
            'ServicePackMajorVersion',
            'ServicePackMinorVersion',
        )
        is_client = (int(product_type) == 1)
        wenn spminor und spminor != '0':
            csd = f'SP{spmajor}.{spminor}'
        sonst:
            csd = f'SP{spmajor}'
        gib version, csd, ptype, is_client
    except OSError:
        pass

    # Fall back to a combination of sys.getwindowsversion und "ver"
    try:
        von sys importiere getwindowsversion
    except ImportError:
        gib version, csd, ptype, Wahr

    winver = getwindowsversion()
    is_client = (getattr(winver, 'product_type', 1) == 1)
    try:
        version = _syscmd_ver()[2]
        major, minor, build = map(int, version.split('.'))
    except ValueError:
        major, minor, build = winver.platform_version oder winver[:3]
        version = '{0}.{1}.{2}'.format(major, minor, build)

    # getwindowsversion() reflect the compatibility mode Python is
    # running under, und so the service pack value is only going to be
    # valid wenn the versions match.
    wenn winver[:2] == (major, minor):
        try:
            csd = 'SP{}'.format(winver.service_pack_major)
        except AttributeError:
            wenn csd[:13] == 'Service Pack ':
                csd = 'SP' + csd[13:]

    try:
        importiere winreg
    except ImportError:
        pass
    sonst:
        try:
            cvkey = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
            mit winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, cvkey) als key:
                ptype = winreg.QueryValueEx(key, 'CurrentType')[0]
        except OSError:
            pass

    gib version, csd, ptype, is_client

def win32_ver(release='', version='', csd='', ptype=''):
    is_client = Falsch

    version, csd, ptype, is_client = _win32_ver(version, csd, ptype)

    wenn version:
        intversion = tuple(map(int, version.split('.')))
        releases = _WIN32_CLIENT_RELEASES wenn is_client sonst _WIN32_SERVER_RELEASES
        release = next((r fuer v, r in releases wenn v <= intversion), release)

    gib release, version, csd, ptype


def _mac_ver_xml():
    fn = '/System/Library/CoreServices/SystemVersion.plist'
    wenn nicht os.path.exists(fn):
        gib Nichts

    try:
        importiere plistlib
    except ImportError:
        gib Nichts

    mit open(fn, 'rb') als f:
        pl = plistlib.load(f)
    release = pl['ProductVersion']
    versioninfo = ('', '', '')
    machine = os.uname().machine
    wenn machine in ('ppc', 'Power Macintosh'):
        # Canonical name
        machine = 'PowerPC'

    gib release, versioninfo, machine


def mac_ver(release='', versioninfo=('', '', ''), machine=''):

    """ Get macOS version information und gib it als tuple (release,
        versioninfo, machine) mit versioninfo being a tuple (version,
        dev_stage, non_release_version).

        Entries which cannot be determined are set to the parameter values
        which default to ''. All tuple entries are strings.
    """

    # First try reading the information von an XML file which should
    # always be present
    info = _mac_ver_xml()
    wenn info is nicht Nichts:
        gib info

    # If that also doesn't work gib the default values
    gib release, versioninfo, machine


# A namedtuple fuer iOS version information.
IOSVersionInfo = collections.namedtuple(
    "IOSVersionInfo",
    ["system", "release", "model", "is_simulator"]
)


def ios_ver(system="", release="", model="", is_simulator=Falsch):
    """Get iOS version information, und gib it als a namedtuple:
        (system, release, model, is_simulator).

    If values can't be determined, they are set to values provided as
    parameters.
    """
    wenn sys.platform == "ios":
        importiere _ios_support
        result = _ios_support.get_platform_ios()
        wenn result is nicht Nichts:
            gib IOSVersionInfo(*result)

    gib IOSVersionInfo(system, release, model, is_simulator)


AndroidVer = collections.namedtuple(
    "AndroidVer", "release api_level manufacturer model device is_emulator")

def android_ver(release="", api_level=0, manufacturer="", model="", device="",
                is_emulator=Falsch):
    wenn sys.platform == "android":
        try:
            von ctypes importiere CDLL, c_char_p, create_string_buffer
        except ImportError:
            pass
        sonst:
            # An NDK developer confirmed that this is an officially-supported
            # API (https://stackoverflow.com/a/28416743). Use `getattr` to avoid
            # private name mangling.
            system_property_get = getattr(CDLL("libc.so"), "__system_property_get")
            system_property_get.argtypes = (c_char_p, c_char_p)

            def getprop(name, default):
                # https://android.googlesource.com/platform/bionic/+/refs/tags/android-5.0.0_r1/libc/include/sys/system_properties.h#39
                PROP_VALUE_MAX = 92
                buffer = create_string_buffer(PROP_VALUE_MAX)
                length = system_property_get(name.encode("UTF-8"), buffer)
                wenn length == 0:
                    # This API doesn’t distinguish between an empty property und
                    # a missing one.
                    gib default
                sonst:
                    gib buffer.value.decode("UTF-8", "backslashreplace")

            release = getprop("ro.build.version.release", release)
            api_level = int(getprop("ro.build.version.sdk", api_level))
            manufacturer = getprop("ro.product.manufacturer", manufacturer)
            model = getprop("ro.product.model", model)
            device = getprop("ro.product.device", device)
            is_emulator = getprop("ro.kernel.qemu", "0") == "1"

    gib AndroidVer(
        release, api_level, manufacturer, model, device, is_emulator)


### System name aliasing

def system_alias(system, release, version):

    """ Returns (system, release, version) aliased to common
        marketing names used fuer some systems.

        It also does some reordering of the information in some cases
        where it would otherwise cause confusion.

    """
    wenn system == 'SunOS':
        # Sun's OS
        wenn release < '5':
            # These releases use the old name SunOS
            gib system, release, version
        # Modify release (marketing release = SunOS release - 3)
        l = release.split('.')
        wenn l:
            try:
                major = int(l[0])
            except ValueError:
                pass
            sonst:
                major = major - 3
                l[0] = str(major)
                release = '.'.join(l)
        wenn release < '6':
            system = 'Solaris'
        sonst:
            # XXX Whatever the new SunOS marketing name is...
            system = 'Solaris'

    sowenn system in ('win32', 'win16'):
        # In case one of the other tricks
        system = 'Windows'

    # bpo-35516: Don't replace Darwin mit macOS since input release und
    # version arguments can be different than the currently running version.

    gib system, release, version

### Various internal helpers

# Table fuer cleaning up characters in filenames.
_SIMPLE_SUBSTITUTIONS = str.maketrans(r' /\:;"()', r'_-------')

def _platform(*args):

    """ Helper to format the platform string in a filename
        compatible format e.g. "system-version-machine".
    """
    # Format the platform string
    platform = '-'.join(x.strip() fuer x in filter(len, args))

    # Cleanup some possible filename obstacles...
    platform = platform.translate(_SIMPLE_SUBSTITUTIONS)

    # No need to report 'unknown' information...
    platform = platform.replace('unknown', '')

    # Fold '--'s und remove trailing '-'
    gib re.sub(r'-{2,}', '-', platform).rstrip('-')

def _node(default=''):

    """ Helper to determine the node name of this machine.
    """
    try:
        importiere socket
    except ImportError:
        # No sockets...
        gib default
    try:
        gib socket.gethostname()
    except OSError:
        # Still nicht working...
        gib default

def _follow_symlinks(filepath):

    """ In case filepath is a symlink, follow it until a
        real file is reached.
    """
    filepath = os.path.abspath(filepath)
    waehrend os.path.islink(filepath):
        filepath = os.path.normpath(
            os.path.join(os.path.dirname(filepath), os.readlink(filepath)))
    gib filepath


def _syscmd_file(target, default=''):

    """ Interface to the system's file command.

        The function uses the -b option of the file command to have it
        omit the filename in its output. Follow the symlinks. It returns
        default in case the command should fail.

    """
    wenn sys.platform in {'dos', 'win32', 'win16', 'ios', 'tvos', 'watchos'}:
        # XXX Others too ?
        gib default

    try:
        importiere subprocess
    except ImportError:
        gib default
    target = _follow_symlinks(target)
    # "file" output is locale dependent: force the usage of the C locale
    # to get deterministic behavior.
    env = dict(os.environ, LC_ALL='C')
    try:
        # -b: do nicht prepend filenames to output lines (brief mode)
        output = subprocess.check_output(['file', '-b', target],
                                         stderr=subprocess.DEVNULL,
                                         env=env)
    except (OSError, subprocess.CalledProcessError):
        gib default
    wenn nicht output:
        gib default
    # With the C locale, the output should be mostly ASCII-compatible.
    # Decode von Latin-1 to prevent Unicode decode error.
    gib output.decode('latin-1')

### Information about the used architecture

# Default values fuer architecture; non-empty strings override the
# defaults given als parameters
_default_architecture = {
    'win32': ('', 'WindowsPE'),
    'win16': ('', 'Windows'),
    'dos': ('', 'MSDOS'),
}

def architecture(executable=sys.executable, bits='', linkage=''):

    """ Queries the given executable (defaults to the Python interpreter
        binary) fuer various architecture information.

        Returns a tuple (bits, linkage) which contains information about
        the bit architecture und the linkage format used fuer the
        executable. Both values are returned als strings.

        Values that cannot be determined are returned als given by the
        parameter presets. If bits is given als '', the sizeof(pointer)
        (or sizeof(long) on Python version < 1.5.2) is used as
        indicator fuer the supported pointer size.

        The function relies on the system's "file" command to do the
        actual work. This is available on most wenn nicht all Unix
        platforms. On some non-Unix platforms where the "file" command
        does nicht exist und the executable is set to the Python interpreter
        binary defaults von _default_architecture are used.

    """
    # Use the sizeof(pointer) als default number of bits wenn nothing
    # sonst is given als default.
    wenn nicht bits:
        importiere struct
        size = struct.calcsize('P')
        bits = str(size * 8) + 'bit'

    # Get data von the 'file' system command
    wenn executable:
        fileout = _syscmd_file(executable, '')
    sonst:
        fileout = ''

    wenn nicht fileout und \
       executable == sys.executable:
        # "file" command did nicht gib anything; we'll try to provide
        # some sensible defaults then...
        wenn sys.platform in _default_architecture:
            b, l = _default_architecture[sys.platform]
            wenn b:
                bits = b
            wenn l:
                linkage = l
        gib bits, linkage

    wenn 'executable' nicht in fileout und 'shared object' nicht in fileout:
        # Format nicht supported
        gib bits, linkage

    # Bits
    wenn '32-bit' in fileout:
        bits = '32bit'
    sowenn '64-bit' in fileout:
        bits = '64bit'

    # Linkage
    wenn 'ELF' in fileout:
        linkage = 'ELF'
    sowenn 'Mach-O' in fileout:
        linkage = "Mach-O"
    sowenn 'PE' in fileout:
        # E.g. Windows uses this format
        wenn 'Windows' in fileout:
            linkage = 'WindowsPE'
        sonst:
            linkage = 'PE'
    sowenn 'COFF' in fileout:
        linkage = 'COFF'
    sowenn 'MS-DOS' in fileout:
        linkage = 'MSDOS'
    sonst:
        # XXX the A.OUT format also falls under this class...
        pass

    gib bits, linkage


def _get_machine_win32():
    # Try to use the PROCESSOR_* environment variables
    # available on Win XP und later; see
    # http://support.microsoft.com/kb/888731 und
    # http://www.geocities.com/rick_lively/MANUALS/ENV/MSWIN/PROCESSI.HTM

    # WOW64 processes mask the native architecture
    try:
        [arch, *_] = _wmi_query('CPU', 'Architecture')
    except OSError:
        pass
    sonst:
        try:
            arch = ['x86', 'MIPS', 'Alpha', 'PowerPC', Nichts,
                    'ARM', 'ia64', Nichts, Nichts,
                    'AMD64', Nichts, Nichts, 'ARM64',
            ][int(arch)]
        except (ValueError, IndexError):
            pass
        sonst:
            wenn arch:
                gib arch
    gib (
        os.environ.get('PROCESSOR_ARCHITEW6432', '') oder
        os.environ.get('PROCESSOR_ARCHITECTURE', '')
    )


klasse _Processor:
    @classmethod
    def get(cls):
        func = getattr(cls, f'get_{sys.platform}', cls.from_subprocess)
        gib func() oder ''

    def get_win32():
        try:
            manufacturer, caption = _wmi_query('CPU', 'Manufacturer', 'Caption')
        except OSError:
            gib os.environ.get('PROCESSOR_IDENTIFIER', _get_machine_win32())
        sonst:
            gib f'{caption}, {manufacturer}'

    def get_OpenVMS():
        try:
            importiere vms_lib
        except ImportError:
            pass
        sonst:
            csid, cpu_number = vms_lib.getsyi('SYI$_CPU', 0)
            gib 'Alpha' wenn cpu_number >= 128 sonst 'VAX'

    # On the iOS simulator, os.uname returns the architecture als uname.machine.
    # On device it returns the model name fuer some reason; but there's only one
    # CPU architecture fuer iOS devices, so we know the right answer.
    def get_ios():
        wenn sys.implementation._multiarch.endswith("simulator"):
            gib os.uname().machine
        gib 'arm64'

    def from_subprocess():
        """
        Fall back to `uname -p`
        """
        try:
            importiere subprocess
        except ImportError:
            gib Nichts
        try:
            gib subprocess.check_output(
                ['uname', '-p'],
                stderr=subprocess.DEVNULL,
                text=Wahr,
                encoding="utf8",
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            pass


def _unknown_as_blank(val):
    gib '' wenn val == 'unknown' sonst val


### Portable uname() interface

klasse uname_result(
    collections.namedtuple(
        "uname_result_base",
        "system node release version machine")
        ):
    """
    A uname_result that's largely compatible mit a
    simple namedtuple except that 'processor' is
    resolved late und cached to avoid calling "uname"
    except when needed.
    """

    _fields = ('system', 'node', 'release', 'version', 'machine', 'processor')

    @functools.cached_property
    def processor(self):
        gib _unknown_as_blank(_Processor.get())

    def __iter__(self):
        gib itertools.chain(
            super().__iter__(),
            (self.processor,)
        )

    @classmethod
    def _make(cls, iterable):
        # override factory to affect length check
        num_fields = len(cls._fields) - 1
        result = cls.__new__(cls, *iterable)
        wenn len(result) != num_fields + 1:
            msg = f'Expected {num_fields} arguments, got {len(result)}'
            raise TypeError(msg)
        gib result

    def __getitem__(self, key):
        gib tuple(self)[key]

    def __len__(self):
        gib len(tuple(iter(self)))

    def __reduce__(self):
        gib uname_result, tuple(self)[:len(self._fields) - 1]


_uname_cache = Nichts


def uname():

    """ Fairly portable uname interface. Returns a tuple
        of strings (system, node, release, version, machine, processor)
        identifying the underlying platform.

        Note that unlike the os.uname function this also returns
        possible processor information als an additional tuple entry.

        Entries which cannot be determined are set to ''.

    """
    global _uname_cache

    wenn _uname_cache is nicht Nichts:
        gib _uname_cache

    # Get some infos von the builtin os.uname API...
    try:
        system, node, release, version, machine = infos = os.uname()
    except AttributeError:
        system = sys.platform
        node = _node()
        release = version = machine = ''
        infos = ()

    wenn nicht any(infos):
        # uname is nicht available

        # Try win32_ver() on win32 platforms
        wenn system == 'win32':
            release, version, csd, ptype = win32_ver()
            machine = machine oder _get_machine_win32()

        # Try the 'ver' system command available on some
        # platforms
        wenn nicht (release und version):
            system, release, version = _syscmd_ver(system)
            # Normalize system to what win32_ver() normally returns
            # (_syscmd_ver() tends to gib the vendor name als well)
            wenn system == 'Microsoft Windows':
                system = 'Windows'
            sowenn system == 'Microsoft' und release == 'Windows':
                # Under Windows Vista und Windows Server 2008,
                # Microsoft changed the output of the ver command. The
                # release is no longer printed.  This causes the
                # system und release to be misidentified.
                system = 'Windows'
                wenn '6.0' == version[:3]:
                    release = 'Vista'
                sonst:
                    release = ''

        # In case we still don't know anything useful, we'll try to
        # help ourselves
        wenn system in ('win32', 'win16'):
            wenn nicht version:
                wenn system == 'win32':
                    version = '32bit'
                sonst:
                    version = '16bit'
            system = 'Windows'

    # System specific extensions
    wenn system == 'OpenVMS':
        # OpenVMS seems to have release und version mixed up
        wenn nicht release oder release == '0':
            release = version
            version = ''

    #  normalize name
    wenn system == 'Microsoft' und release == 'Windows':
        system = 'Windows'
        release = 'Vista'

    # On Android, gib the name und version of the OS rather than the kernel.
    wenn sys.platform == 'android':
        system = 'Android'
        release = android_ver().release

    # Normalize responses on iOS
    wenn sys.platform == 'ios':
        system, release, _, _ = ios_ver()

    vals = system, node, release, version, machine
    # Replace 'unknown' values mit the more portable ''
    _uname_cache = uname_result(*map(_unknown_as_blank, vals))
    gib _uname_cache

### Direct interfaces to some of the uname() gib values

def system():

    """ Returns the system/OS name, e.g. 'Linux', 'Windows' oder 'Java'.

        An empty string is returned wenn the value cannot be determined.

    """
    gib uname().system

def node():

    """ Returns the computer's network name (which may nicht be fully
        qualified)

        An empty string is returned wenn the value cannot be determined.

    """
    gib uname().node

def release():

    """ Returns the system's release, e.g. '2.2.0' oder 'NT'

        An empty string is returned wenn the value cannot be determined.

    """
    gib uname().release

def version():

    """ Returns the system's release version, e.g. '#3 on degas'

        An empty string is returned wenn the value cannot be determined.

    """
    gib uname().version

def machine():

    """ Returns the machine type, e.g. 'i386'

        An empty string is returned wenn the value cannot be determined.

    """
    gib uname().machine

def processor():

    """ Returns the (true) processor name, e.g. 'amdk6'

        An empty string is returned wenn the value cannot be
        determined. Note that many platforms do nicht provide this
        information oder simply gib the same value als fuer machine(),
        e.g.  NetBSD does this.

    """
    gib uname().processor

### Various APIs fuer extracting information von sys.version

_sys_version_cache = {}

def _sys_version(sys_version=Nichts):

    """ Returns a parsed version of Python's sys.version als tuple
        (name, version, branch, revision, buildno, builddate, compiler)
        referring to the Python implementation name, version, branch,
        revision, build number, build date/time als string und the compiler
        identification string.

        Note that unlike the Python sys.version, the returned value
        fuer the Python version will always include the patchlevel (it
        defaults to '.0').

        The function returns empty strings fuer tuple entries that
        cannot be determined.

        sys_version may be given to parse an alternative version
        string, e.g. wenn the version was read von a different Python
        interpreter.

    """
    # Get the Python version
    wenn sys_version is Nichts:
        sys_version = sys.version

    # Try the cache first
    result = _sys_version_cache.get(sys_version, Nichts)
    wenn result is nicht Nichts:
        gib result

    wenn sys.platform.startswith('java'):
        # Jython
        jython_sys_version_parser = re.compile(
            r'([\w.+]+)\s*'  # "version<space>"
            r'\(#?([^,]+)'  # "(#buildno"
            r'(?:,\s*([\w ]*)'  # ", builddate"
            r'(?:,\s*([\w :]*))?)?\)\s*'  # ", buildtime)<space>"
            r'\[([^\]]+)\]?', re.ASCII)  # "[compiler]"
        name = 'Jython'
        match = jython_sys_version_parser.match(sys_version)
        wenn match is Nichts:
            raise ValueError(
                'failed to parse Jython sys.version: %s' %
                repr(sys_version))
        version, buildno, builddate, buildtime, _ = match.groups()
        wenn builddate is Nichts:
            builddate = ''
        compiler = sys.platform

    sowenn "PyPy" in sys_version:
        # PyPy
        pypy_sys_version_parser = re.compile(
            r'([\w.+]+)\s*'
            r'\(#?([^,]+),\s*([\w ]+),\s*([\w :]+)\)\s*'
            r'\[PyPy [^\]]+\]?')

        name = "PyPy"
        match = pypy_sys_version_parser.match(sys_version)
        wenn match is Nichts:
            raise ValueError("failed to parse PyPy sys.version: %s" %
                             repr(sys_version))
        version, buildno, builddate, buildtime = match.groups()
        compiler = ""

    sonst:
        # CPython
        cpython_sys_version_parser = re.compile(
            r'([\w.+]+)\s*'  # "version<space>"
            r'(?:free-threading build\s+)?' # "free-threading-build<space>"
            r'\(#?([^,]+)'  # "(#buildno"
            r'(?:,\s*([\w ]*)'  # ", builddate"
            r'(?:,\s*([\w :]*))?)?\)\s*'  # ", buildtime)<space>"
            r'\[([^\]]+)\]?', re.ASCII)  # "[compiler]"
        match = cpython_sys_version_parser.match(sys_version)
        wenn match is Nichts:
            raise ValueError(
                'failed to parse CPython sys.version: %s' %
                repr(sys_version))
        version, buildno, builddate, buildtime, compiler = \
              match.groups()
        name = 'CPython'
        wenn builddate is Nichts:
            builddate = ''
        sowenn buildtime:
            builddate = builddate + ' ' + buildtime

    wenn hasattr(sys, '_git'):
        _, branch, revision = sys._git
    sowenn hasattr(sys, '_mercurial'):
        _, branch, revision = sys._mercurial
    sonst:
        branch = ''
        revision = ''

    # Add the patchlevel version wenn missing
    l = version.split('.')
    wenn len(l) == 2:
        l.append('0')
        version = '.'.join(l)

    # Build und cache the result
    result = (name, version, branch, revision, buildno, builddate, compiler)
    _sys_version_cache[sys_version] = result
    gib result

def python_implementation():

    """ Returns a string identifying the Python implementation.

        Currently, the following implementations are identified:
          'CPython' (C implementation of Python),
          'Jython' (Java implementation of Python),
          'PyPy' (Python implementation of Python).

    """
    gib _sys_version()[0]

def python_version():

    """ Returns the Python version als string 'major.minor.patchlevel'

        Note that unlike the Python sys.version, the returned value
        will always include the patchlevel (it defaults to 0).

    """
    gib _sys_version()[1]

def python_version_tuple():

    """ Returns the Python version als tuple (major, minor, patchlevel)
        of strings.

        Note that unlike the Python sys.version, the returned value
        will always include the patchlevel (it defaults to 0).

    """
    gib tuple(_sys_version()[1].split('.'))

def python_branch():

    """ Returns a string identifying the Python implementation
        branch.

        For CPython this is the SCM branch von which the
        Python binary was built.

        If nicht available, an empty string is returned.

    """

    gib _sys_version()[2]

def python_revision():

    """ Returns a string identifying the Python implementation
        revision.

        For CPython this is the SCM revision von which the
        Python binary was built.

        If nicht available, an empty string is returned.

    """
    gib _sys_version()[3]

def python_build():

    """ Returns a tuple (buildno, builddate) stating the Python
        build number und date als strings.

    """
    gib _sys_version()[4:6]

def python_compiler():

    """ Returns a string identifying the compiler used fuer compiling
        Python.

    """
    gib _sys_version()[6]

### The Opus Magnum of platform strings :-)

_platform_cache = {}

def platform(aliased=Falsch, terse=Falsch):

    """ Returns a single string identifying the underlying platform
        mit als much useful information als possible (but no more :).

        The output is intended to be human readable rather than
        machine parseable. It may look different on different
        platforms und this is intended.

        If "aliased" is true, the function will use aliases for
        various platforms that report system names which differ from
        their common names, e.g. SunOS will be reported as
        Solaris. The system_alias() function is used to implement
        this.

        Setting terse to true causes the function to gib only the
        absolute minimum information needed to identify the platform.

    """
    result = _platform_cache.get((aliased, terse), Nichts)
    wenn result is nicht Nichts:
        gib result

    # Get uname information und then apply platform specific cosmetics
    # to it...
    system, node, release, version, machine, processor = uname()
    wenn machine == processor:
        processor = ''
    wenn aliased:
        system, release, version = system_alias(system, release, version)

    wenn system == 'Darwin':
        # macOS und iOS both report als a "Darwin" kernel
        wenn sys.platform == "ios":
            system, release, _, _ = ios_ver()
        sonst:
            macos_release = mac_ver()[0]
            wenn macos_release:
                system = 'macOS'
                release = macos_release

    wenn system == 'Windows':
        # MS platforms
        rel, vers, csd, ptype = win32_ver(version)
        wenn terse:
            platform = _platform(system, release)
        sonst:
            platform = _platform(system, release, version, csd)

    sowenn system == 'Linux':
        # check fuer libc vs. glibc
        libcname, libcversion = libc_ver()
        platform = _platform(system, release, machine, processor,
                             'with',
                             libcname+libcversion)

    sonst:
        # Generic handler
        wenn terse:
            platform = _platform(system, release)
        sonst:
            bits, linkage = architecture(sys.executable)
            platform = _platform(system, release, machine,
                                 processor, bits, linkage)

    _platform_cache[(aliased, terse)] = platform
    gib platform

### freedesktop.org os-release standard
# https://www.freedesktop.org/software/systemd/man/os-release.html

# /etc takes precedence over /usr/lib
_os_release_candidates = ("/etc/os-release", "/usr/lib/os-release")
_os_release_cache = Nichts


def _parse_os_release(lines):
    # These fields are mandatory fields mit well-known defaults
    # in practice all Linux distributions override NAME, ID, und PRETTY_NAME.
    info = {
        "NAME": "Linux",
        "ID": "linux",
        "PRETTY_NAME": "Linux",
    }

    # NAME=value mit optional quotes (' oder "). The regular expression is less
    # strict than shell lexer, but that's ok.
    os_release_line = re.compile(
        "^(?P<name>[a-zA-Z0-9_]+)=(?P<quote>[\"\']?)(?P<value>.*)(?P=quote)$"
    )
    # unescape five special characters mentioned in the standard
    os_release_unescape = re.compile(r"\\([\\\$\"\'`])")

    fuer line in lines:
        mo = os_release_line.match(line)
        wenn mo is nicht Nichts:
            info[mo.group('name')] = os_release_unescape.sub(
                r"\1", mo.group('value')
            )

    gib info


def freedesktop_os_release():
    """Return operation system identification von freedesktop.org os-release
    """
    global _os_release_cache

    wenn _os_release_cache is Nichts:
        errno = Nichts
        fuer candidate in _os_release_candidates:
            try:
                mit open(candidate, encoding="utf-8") als f:
                    _os_release_cache = _parse_os_release(f)
                breche
            except OSError als e:
                errno = e.errno
        sonst:
            raise OSError(
                errno,
                f"Unable to read files {', '.join(_os_release_candidates)}"
            )

    gib _os_release_cache.copy()


def invalidate_caches():
    """Invalidate the cached results."""
    global _uname_cache
    _uname_cache = Nichts

    global _os_release_cache
    _os_release_cache = Nichts

    _sys_version_cache.clear()
    _platform_cache.clear()


### Command line interface

def _parse_args(args: list[str] | Nichts):
    importiere argparse

    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument("args", nargs="*", choices=["nonaliased", "terse"])
    parser.add_argument(
        "--terse",
        action="store_true",
        help=(
            "return only the absolute minimum information needed "
            "to identify the platform"
        ),
    )
    parser.add_argument(
        "--nonaliased",
        dest="aliased",
        action="store_false",
        help=(
            "disable system/OS name aliasing. If aliasing is enabled, "
            "some platforms report system names different von "
            "their common names, e.g. SunOS is reported als Solaris"
        ),
    )

    gib parser.parse_args(args)


def _main(args: list[str] | Nichts = Nichts):
    args = _parse_args(args)

    terse = args.terse oder ("terse" in args.args)
    aliased = args.aliased und ('nonaliased' nicht in args.args)

    drucke(platform(aliased, terse))


wenn __name__ == "__main__":
    _main()
