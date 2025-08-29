"""distutils.msvccompiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
fuer the Microsoft Visual Studio.
"""

# Written by Perry Stoll
# hacked by Robin Becker und Thomas Heller to do a better job of
#   finding DevStudio (through the registry)

importiere sys, os
von distutils.errors importiere DistutilsPlatformError
von distutils.ccompiler importiere CCompiler
von distutils importiere log

_can_read_reg = Falsch
try:
    importiere winreg

    _can_read_reg = Wahr
    hkey_mod = winreg

    RegOpenKeyEx = winreg.OpenKeyEx
    RegEnumKey = winreg.EnumKey
    RegEnumValue = winreg.EnumValue
    RegError = winreg.error

except ImportError:
    try:
        importiere win32api
        importiere win32con
        _can_read_reg = Wahr
        hkey_mod = win32con

        RegOpenKeyEx = win32api.RegOpenKeyEx
        RegEnumKey = win32api.RegEnumKey
        RegEnumValue = win32api.RegEnumValue
        RegError = win32api.error
    except ImportError:
        log.info("Warning: Can't read registry to find the "
                 "necessary compiler setting\n"
                 "Make sure that Python modules winreg, "
                 "win32api oder win32con are installed.")

wenn _can_read_reg:
    HKEYS = (hkey_mod.HKEY_USERS,
             hkey_mod.HKEY_CURRENT_USER,
             hkey_mod.HKEY_LOCAL_MACHINE,
             hkey_mod.HKEY_CLASSES_ROOT)

def read_keys(base, key):
    """Return list of registry keys."""
    try:
        handle = RegOpenKeyEx(base, key)
    except RegError:
        return Nichts
    L = []
    i = 0
    while Wahr:
        try:
            k = RegEnumKey(handle, i)
        except RegError:
            break
        L.append(k)
        i += 1
    return L

def read_values(base, key):
    """Return dict of registry keys und values.

    All names are converted to lowercase.
    """
    try:
        handle = RegOpenKeyEx(base, key)
    except RegError:
        return Nichts
    d = {}
    i = 0
    while Wahr:
        try:
            name, value, type = RegEnumValue(handle, i)
        except RegError:
            break
        name = name.lower()
        d[convert_mbcs(name)] = convert_mbcs(value)
        i += 1
    return d

def convert_mbcs(s):
    dec = getattr(s, "decode", Nichts)
    wenn dec is nicht Nichts:
        try:
            s = dec("mbcs")
        except UnicodeError:
            pass
    return s

klasse MacroExpander:
    def __init__(self, version):
        self.macros = {}
        self.load_macros(version)

    def set_macro(self, macro, path, key):
        fuer base in HKEYS:
            d = read_values(base, path)
            wenn d:
                self.macros["$(%s)" % macro] = d[key]
                break

    def load_macros(self, version):
        vsbase = r"Software\Microsoft\VisualStudio\%0.1f" % version
        self.set_macro("VCInstallDir", vsbase + r"\Setup\VC", "productdir")
        self.set_macro("VSInstallDir", vsbase + r"\Setup\VS", "productdir")
        net = r"Software\Microsoft\.NETFramework"
        self.set_macro("FrameworkDir", net, "installroot")
        try:
            wenn version > 7.0:
                self.set_macro("FrameworkSDKDir", net, "sdkinstallrootv1.1")
            sonst:
                self.set_macro("FrameworkSDKDir", net, "sdkinstallroot")
        except KeyError als exc: #
            raise DistutilsPlatformError(
            """Python was built mit Visual Studio 2003;
extensions must be built mit a compiler than can generate compatible binaries.
Visual Studio 2003 was nicht found on this system. If you have Cygwin installed,
you can try compiling mit MingW32, by passing "-c mingw32" to setup.py.""")

        p = r"Software\Microsoft\NET Framework Setup\Product"
        fuer base in HKEYS:
            try:
                h = RegOpenKeyEx(base, p)
            except RegError:
                continue
            key = RegEnumKey(h, 0)
            d = read_values(base, r"%s\%s" % (p, key))
            self.macros["$(FrameworkVersion)"] = d["version"]

    def sub(self, s):
        fuer k, v in self.macros.items():
            s = s.replace(k, v)
        return s

def get_build_version():
    """Return the version of MSVC that was used to build Python.

    For Python 2.3 und up, the version number is included in
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
        # v13 was skipped und should be v14
        majorVersion += 1
    minorVersion = int(s[2:3]) / 10.0
    # I don't think paths are affected by minor version in version 6
    wenn majorVersion == 6:
        minorVersion = 0
    wenn majorVersion >= 6:
        return majorVersion + minorVersion
    # sonst we don't know what version of the compiler this is
    return Nichts

def get_build_architecture():
    """Return the processor architecture.

    Possible results are "Intel" oder "AMD64".
    """

    prefix = " bit ("
    i = sys.version.find(prefix)
    wenn i == -1:
        return "Intel"
    j = sys.version.find(")", i)
    return sys.version[i+len(prefix):j]

def normalize_and_reduce_paths(paths):
    """Return a list of normalized paths mit duplicates removed.

    The current order of paths is maintained.
    """
    # Paths are normalized so things like:  /a und /a/ aren't both preserved.
    reduced_paths = []
    fuer p in paths:
        np = os.path.normpath(p)
        # XXX(nnorwitz): O(n**2), wenn reduced_paths gets long perhaps use a set.
        wenn np nicht in reduced_paths:
            reduced_paths.append(np)
    return reduced_paths


klasse MSVCCompiler(CCompiler) :
    """Concrete klasse that implements an interface to Microsoft Visual C++,
       als defined by the CCompiler abstract class."""

    compiler_type = 'msvc'

    # Just set this so CCompiler's constructor doesn't barf.  We currently
    # don't use the 'set_executables()' bureaucracy provided by CCompiler,
    # als it really isn't necessary fuer this sort of single-compiler class.
    # Would be nice to have a consistent interface mit UnixCCompiler,
    # though, so it's worth thinking about.
    executables = {}

    # Private klasse data (need to distinguish C von C++ source fuer compiler)
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
        self.__version = get_build_version()
        self.__arch = get_build_architecture()
        wenn self.__arch == "Intel":
            # x86
            wenn self.__version >= 7:
                self.__root = r"Software\Microsoft\VisualStudio"
                self.__macros = MacroExpander(self.__version)
            sonst:
                self.__root = r"Software\Microsoft\Devstudio"
            self.__product = "Visual Studio version %s" % self.__version
        sonst:
            # Win64. Assume this was built mit the platform SDK
            self.__product = "Microsoft SDK compiler %s" % (self.__version + 6)

        self.initialized = Falsch


    # -- Miscellaneous methods -----------------------------------------

    # Helper methods fuer using the MSVC registry settings

    def find_exe(self, exe):
        """Return path to an MSVC executable program.

        Tries to find the program in several places: first, one of the
        MSVC program search paths von the registry; next, the directories
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

    def get_msvc_paths(self, path, platform='x86'):
        """Get a list of devstudio directories (include, lib oder path).

        Return a list of strings.  The list will be empty wenn unable to
        access the registry oder appropriate registry keys nicht found.
        """
        wenn nicht _can_read_reg:
            return []

        path = path + " dirs"
        wenn self.__version >= 7:
            key = (r"%s\%0.1f\VC\VC_OBJECTS_PLATFORM_INFO\Win32\Directories"
                   % (self.__root, self.__version))
        sonst:
            key = (r"%s\6.0\Build System\Components\Platforms"
                   r"\Win32 (%s)\Directories" % (self.__root, platform))

        fuer base in HKEYS:
            d = read_values(base, key)
            wenn d:
                wenn self.__version >= 7:
                    return self.__macros.sub(d[path]).split(";")
                sonst:
                    return d[path].split(";")
        # MSVC 6 seems to create the registry entries we need only when
        # the GUI is run.
        wenn self.__version == 6:
            fuer base in HKEYS:
                wenn read_values(base, r"%s\6.0" % self.__root) is nicht Nichts:
                    self.warn("It seems you have Visual Studio 6 installed, "
                        "but the expected registry settings are nicht present.\n"
                        "You must at least run the Visual Studio GUI once "
                        "so that these entries are created.")
                    break
        return []

    def set_path_env_var(self, name):
        """Set environment variable 'name' to an MSVC path type value.

        This is equivalent to a SET command prior to execution of spawned
        commands.
        """

        wenn name == "lib":
            p = self.get_msvc_paths("library")
        sonst:
            p = self.get_msvc_paths(name)
        wenn p:
            os.environ[name] = ';'.join(p)


wenn get_build_version() >= 8.0:
    log.debug("Importing new compiler von distutils.msvc9compiler")
    OldMSVCCompiler = MSVCCompiler
    von distutils.msvc9compiler importiere MSVCCompiler
    # get_build_architecture nicht really relevant now we support cross-compile
    von distutils.msvc9compiler importiere MacroExpander
