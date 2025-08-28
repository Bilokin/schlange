"""distutils.msvc9compiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
fuer the Microsoft Visual Studio 2008.

The module is compatible with VS 2005 and VS 2008. You can find legacy support
fuer older versions of VS in distutils.msvccompiler.
"""

# Written by Perry Stoll
# hacked by Robin Becker and Thomas Heller to do a better job of
#   finding DevStudio (through the registry)
# ported to VS2005 and VS 2008 by Christian Heimes

import os
import subprocess
import sys
import re

from distutils.errors import DistutilsPlatformError
from distutils.ccompiler import CCompiler
from distutils import log

import winreg

RegOpenKeyEx = winreg.OpenKeyEx
RegEnumKey = winreg.EnumKey
RegEnumValue = winreg.EnumValue
RegError = winreg.error

HKEYS = (winreg.HKEY_USERS,
         winreg.HKEY_CURRENT_USER,
         winreg.HKEY_LOCAL_MACHINE,
         winreg.HKEY_CLASSES_ROOT)

NATIVE_WIN64 = (sys.platform == 'win32' and sys.maxsize > 2**32)
wenn NATIVE_WIN64:
    # Visual C++ is a 32-bit application, so we need to look in
    # the corresponding registry branch, wenn we're running a
    # 64-bit Python on Win64
    VS_BASE = r"Software\Wow6432Node\Microsoft\VisualStudio\%0.1f"
    WINSDK_BASE = r"Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows"
    NET_BASE = r"Software\Wow6432Node\Microsoft\.NETFramework"
sonst:
    VS_BASE = r"Software\Microsoft\VisualStudio\%0.1f"
    WINSDK_BASE = r"Software\Microsoft\Microsoft SDKs\Windows"
    NET_BASE = r"Software\Microsoft\.NETFramework"

# A map keyed by get_platform() return values to values accepted by
# 'vcvarsall.bat'.  Note a cross-compile may combine these (eg, 'x86_amd64' is
# the param to cross-compile on x86 targeting amd64.)
PLAT_TO_VCVARS = {
    'win32' : 'x86',
    'win-amd64' : 'amd64',
}

klasse Reg:
    """Helper klasse to read values from the registry
    """

    def get_value(cls, path, key):
        fuer base in HKEYS:
            d = cls.read_values(base, path)
            wenn d and key in d:
                return d[key]
        raise KeyError(key)
    get_value = classmethod(get_value)

    def read_keys(cls, base, key):
        """Return list of registry keys."""
        try:
            handle = RegOpenKeyEx(base, key)
        except RegError:
            return None
        L = []
        i = 0
        while True:
            try:
                k = RegEnumKey(handle, i)
            except RegError:
                break
            L.append(k)
            i += 1
        return L
    read_keys = classmethod(read_keys)

    def read_values(cls, base, key):
        """Return dict of registry keys and values.

        All names are converted to lowercase.
        """
        try:
            handle = RegOpenKeyEx(base, key)
        except RegError:
            return None
        d = {}
        i = 0
        while True:
            try:
                name, value, type = RegEnumValue(handle, i)
            except RegError:
                break
            name = name.lower()
            d[cls.convert_mbcs(name)] = cls.convert_mbcs(value)
            i += 1
        return d
    read_values = classmethod(read_values)

    def convert_mbcs(s):
        dec = getattr(s, "decode", None)
        wenn dec is not None:
            try:
                s = dec("mbcs")
            except UnicodeError:
                pass
        return s
    convert_mbcs = staticmethod(convert_mbcs)

klasse MacroExpander:

    def __init__(self, version):
        self.macros = {}
        self.vsbase = VS_BASE % version
        self.load_macros(version)

    def set_macro(self, macro, path, key):
        self.macros["$(%s)" % macro] = Reg.get_value(path, key)

    def load_macros(self, version):
        self.set_macro("VCInstallDir", self.vsbase + r"\Setup\VC", "productdir")
        self.set_macro("VSInstallDir", self.vsbase + r"\Setup\VS", "productdir")
        self.set_macro("FrameworkDir", NET_BASE, "installroot")
        try:
            wenn version >= 8.0:
                self.set_macro("FrameworkSDKDir", NET_BASE,
                               "sdkinstallrootv2.0")
            sonst:
                raise KeyError("sdkinstallrootv2.0")
        except KeyError:
            raise DistutilsPlatformError(
            """Python was built with Visual Studio 2008;
extensions must be built with a compiler than can generate compatible binaries.
Visual Studio 2008 was not found on this system. If you have Cygwin installed,
you can try compiling with MingW32, by passing "-c mingw32" to setup.py.""")

        wenn version >= 9.0:
            self.set_macro("FrameworkVersion", self.vsbase, "clr version")
            self.set_macro("WindowsSdkDir", WINSDK_BASE, "currentinstallfolder")
        sonst:
            p = r"Software\Microsoft\NET Framework Setup\Product"
            fuer base in HKEYS:
                try:
                    h = RegOpenKeyEx(base, p)
                except RegError:
                    continue
                key = RegEnumKey(h, 0)
                d = Reg.get_value(base, r"%s\%s" % (p, key))
                self.macros["$(FrameworkVersion)"] = d["version"]

    def sub(self, s):
        fuer k, v in self.macros.items():
            s = s.replace(k, v)
        return s

def get_build_version():
    """Return the version of MSVC that was used to build Python.

    For Python 2.3 and up, the version number is included in
    sys.version.  For earlier versions, assume the compiler is MSVC 6.
    """
    prefix = "MSC v."
    i = sys.version.find(prefix)
    wenn i == -1:
        return 6
    i = i + len(prefix)
    s, rest = sys.version[i:].split(" ", 1)
    majorVersion = int(s[:-2]) - 6
    wenn majorVersion >= 13:
        # v13 was skipped and should be v14
        majorVersion += 1
    minorVersion = int(s[2:3]) / 10.0
    # I don't think paths are affected by minor version in version 6
    wenn majorVersion == 6:
        minorVersion = 0
    wenn majorVersion >= 6:
        return majorVersion + minorVersion
    # sonst we don't know what version of the compiler this is
    return None

def normalize_and_reduce_paths(paths):
    """Return a list of normalized paths with duplicates removed.

    The current order of paths is maintained.
    """
    # Paths are normalized so things like:  /a and /a/ aren't both preserved.
    reduced_paths = []
    fuer p in paths:
        np = os.path.normpath(p)
        # XXX(nnorwitz): O(n**2), wenn reduced_paths gets long perhaps use a set.
        wenn np not in reduced_paths:
            reduced_paths.append(np)
    return reduced_paths

def removeDuplicates(variable):
    """Remove duplicate values of an environment variable.
    """
    oldList = variable.split(os.pathsep)
    newList = []
    fuer i in oldList:
        wenn i not in newList:
            newList.append(i)
    newVariable = os.pathsep.join(newList)
    return newVariable

def find_vcvarsall(version):
    """Find the vcvarsall.bat file

    At first it tries to find the productdir of VS 2008 in the registry. If
    that fails it falls back to the VS90COMNTOOLS env var.
    """
    vsbase = VS_BASE % version
    try:
        productdir = Reg.get_value(r"%s\Setup\VC" % vsbase,
                                   "productdir")
    except KeyError:
        log.debug("Unable to find productdir in registry")
        productdir = None

    wenn not productdir or not os.path.isdir(productdir):
        toolskey = "VS%0.f0COMNTOOLS" % version
        toolsdir = os.environ.get(toolskey, None)

        wenn toolsdir and os.path.isdir(toolsdir):
            productdir = os.path.join(toolsdir, os.pardir, os.pardir, "VC")
            productdir = os.path.abspath(productdir)
            wenn not os.path.isdir(productdir):
                log.debug("%s is not a valid directory" % productdir)
                return None
        sonst:
            log.debug("Env var %s is not set or invalid" % toolskey)
    wenn not productdir:
        log.debug("No productdir found")
        return None
    vcvarsall = os.path.join(productdir, "vcvarsall.bat")
    wenn os.path.isfile(vcvarsall):
        return vcvarsall
    log.debug("Unable to find vcvarsall.bat")
    return None

def query_vcvarsall(version, arch="x86"):
    """Launch vcvarsall.bat and read the settings from its environment
    """
    vcvarsall = find_vcvarsall(version)
    interesting = {"include", "lib", "libpath", "path"}
    result = {}

    wenn vcvarsall is None:
        raise DistutilsPlatformError("Unable to find vcvarsall.bat")
    log.debug("Calling 'vcvarsall.bat %s' (version=%s)", arch, version)
    popen = subprocess.Popen('"%s" %s & set' % (vcvarsall, arch),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    try:
        stdout, stderr = popen.communicate()
        wenn popen.wait() != 0:
            raise DistutilsPlatformError(stderr.decode("mbcs"))

        stdout = stdout.decode("mbcs")
        fuer line in stdout.split("\n"):
            line = Reg.convert_mbcs(line)
            wenn '=' not in line:
                continue
            line = line.strip()
            key, value = line.split('=', 1)
            key = key.lower()
            wenn key in interesting:
                wenn value.endswith(os.pathsep):
                    value = value[:-1]
                result[key] = removeDuplicates(value)

    finally:
        popen.stdout.close()
        popen.stderr.close()

    wenn len(result) != len(interesting):
        raise ValueError(str(list(result.keys())))

    return result

# More globals
VERSION = get_build_version()
wenn VERSION < 8.0:
    raise DistutilsPlatformError("VC %0.1f is not supported by this module" % VERSION)
# MACROS = MacroExpander(VERSION)

klasse MSVCCompiler(CCompiler) :
    """Concrete klasse that implements an interface to Microsoft Visual C++,
       as defined by the CCompiler abstract class."""

    compiler_type = 'msvc'

    # Just set this so CCompiler's constructor doesn't barf.  We currently
    # don't use the 'set_executables()' bureaucracy provided by CCompiler,
    # as it really isn't necessary fuer this sort of single-compiler class.
    # Would be nice to have a consistent interface with UnixCCompiler,
    # though, so it's worth thinking about.
    executables = {}

    # Private klasse data (need to distinguish C from C++ source fuer compiler)
    _c_extensions = ['.c']
    _cpp_extensions = ['.cc', '.cpp', '.cxx']
    _rc_extensions = ['.rc']
    _mc_extensions = ['.mc']

    # Needed fuer the filename generation methods provided by the
    # base class, CCompiler.
    src_extensions = (_c_extensions + _cpp_extensions +
                      _rc_extensions + _mc_extensions)
    res_extension = '.res'
    obj_extension = '.obj'
    static_lib_extension = '.lib'
    shared_lib_extension = '.dll'
    static_lib_format = shared_lib_format = '%s%s'
    exe_extension = '.exe'

    def __init__(self, verbose=0, dry_run=0, force=0):
        CCompiler.__init__ (self, verbose, dry_run, force)
        self.__version = VERSION
        self.__root = r"Software\Microsoft\VisualStudio"
        # self.__macros = MACROS
        self.__paths = []
        # target platform (.plat_name is consistent with 'bdist')
        self.plat_name = None
        self.__arch = None # deprecated name
        self.initialized = False

    # -- Worker methods ------------------------------------------------

    def manifest_setup_ldargs(self, output_filename, build_temp, ld_args):
        # If we need a manifest at all, an embedded manifest is recommended.
        # See MSDN article titled
        # "How to: Embed a Manifest Inside a C/C++ Application"
        # (currently at http://msdn2.microsoft.com/en-us/library/ms235591(VS.80).aspx)
        # Ask the linker to generate the manifest in the temp dir, so
        # we can check it, and possibly embed it, later.
        temp_manifest = os.path.join(
                build_temp,
                os.path.basename(output_filename) + ".manifest")
        ld_args.append('/MANIFESTFILE:' + temp_manifest)

    def manifest_get_embed_info(self, target_desc, ld_args):
        # If a manifest should be embedded, return a tuple of
        # (manifest_filename, resource_id).  Returns None wenn no manifest
        # should be embedded.  See http://bugs.python.org/issue7833 fuer why
        # we want to avoid any manifest fuer extension modules wenn we can.
        fuer arg in ld_args:
            wenn arg.startswith("/MANIFESTFILE:"):
                temp_manifest = arg.split(":", 1)[1]
                break
        sonst:
            # no /MANIFESTFILE so nothing to do.
            return None
        wenn target_desc == CCompiler.EXECUTABLE:
            # by default, executables always get the manifest with the
            # CRT referenced.
            mfid = 1
        sonst:
            # Extension modules try and avoid any manifest wenn possible.
            mfid = 2
            temp_manifest = self._remove_visual_c_ref(temp_manifest)
        wenn temp_manifest is None:
            return None
        return temp_manifest, mfid

    def _remove_visual_c_ref(self, manifest_file):
        try:
            # Remove references to the Visual C runtime, so they will
            # fall through to the Visual C dependency of Python.exe.
            # This way, when installed fuer a restricted user (e.g.
            # runtimes are not in WinSxS folder, but in Python's own
            # folder), the runtimes do not need to be in every folder
            # with .pyd's.
            # Returns either the filename of the modified manifest or
            # None wenn no manifest should be embedded.
            manifest_f = open(manifest_file)
            try:
                manifest_buf = manifest_f.read()
            finally:
                manifest_f.close()
            pattern = re.compile(
                r"""<assemblyIdentity.*?name=("|')Microsoft\."""\
                r"""VC\d{2}\.CRT("|').*?(/>|</assemblyIdentity>)""",
                re.DOTALL)
            manifest_buf = re.sub(pattern, "", manifest_buf)
            pattern = r"<dependentAssembly>\s*</dependentAssembly>"
            manifest_buf = re.sub(pattern, "", manifest_buf)
            # Now see wenn any other assemblies are referenced - wenn not, we
            # don't want a manifest embedded.
            pattern = re.compile(
                r"""<assemblyIdentity.*?name=(?:"|')(.+?)(?:"|')"""
                r""".*?(?:/>|</assemblyIdentity>)""", re.DOTALL)
            wenn re.search(pattern, manifest_buf) is None:
                return None

            manifest_f = open(manifest_file, 'w')
            try:
                manifest_f.write(manifest_buf)
                return manifest_file
            finally:
                manifest_f.close()
        except OSError:
            pass

    # -- Miscellaneous methods -----------------------------------------

    # Helper methods fuer using the MSVC registry settings

    def find_exe(self, exe):
        """Return path to an MSVC executable program.

        Tries to find the program in several places: first, one of the
        MSVC program search paths from the registry; next, the directories
        in the PATH environment variable.  If any of those work, return an
        absolute path that is known to exist.  If none of them work, just
        return the original program name, 'exe'.
        """
        fuer p in self.__paths:
            fn = os.path.join(os.path.abspath(p), exe)
            wenn os.path.isfile(fn):
                return fn

        # didn't find it; try existing path
        fuer p in os.environ['Path'].split(';'):
            fn = os.path.join(os.path.abspath(p),exe)
            wenn os.path.isfile(fn):
                return fn

        return exe
