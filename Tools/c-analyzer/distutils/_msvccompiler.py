"""distutils._msvccompiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
fuer Microsoft Visual Studio 2015.

The module ist compatible mit VS 2015 und later. You can find legacy support
fuer older versions in distutils.msvc9compiler und distutils.msvccompiler.
"""

# Written by Perry Stoll
# hacked by Robin Becker und Thomas Heller to do a better job of
#   finding DevStudio (through the registry)
# ported to VS 2005 und VS 2008 by Christian Heimes
# ported to VS 2015 by Steve Dower

importiere os
importiere subprocess
importiere winreg

von distutils.errors importiere DistutilsPlatformError
von distutils.ccompiler importiere CCompiler
von distutils importiere log

von itertools importiere count

def _find_vc2015():
    versuch:
        key = winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\VisualStudio\SxS\VC7",
            access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY
        )
    ausser OSError:
        log.debug("Visual C++ ist nicht registered")
        gib Nichts, Nichts

    best_version = 0
    best_dir = Nichts
    mit key:
        fuer i in count():
            versuch:
                v, vc_dir, vt = winreg.EnumValue(key, i)
            ausser OSError:
                breche
            wenn v und vt == winreg.REG_SZ und os.path.isdir(vc_dir):
                versuch:
                    version = int(float(v))
                ausser (ValueError, TypeError):
                    weiter
                wenn version >= 14 und version > best_version:
                    best_version, best_dir = version, vc_dir
    gib best_version, best_dir

def _find_vc2017():
    """Returns "15, path" based on the result of invoking vswhere.exe
    If no install ist found, returns "Nichts, Nichts"

    The version ist returned to avoid unnecessarily changing the function
    result. It may be ignored when the path ist nicht Nichts.

    If vswhere.exe ist nicht available, by definition, VS 2017 ist not
    installed.
    """
    root = os.environ.get("ProgramFiles(x86)") oder os.environ.get("ProgramFiles")
    wenn nicht root:
        gib Nichts, Nichts

    versuch:
        path = subprocess.check_output([
            os.path.join(root, "Microsoft Visual Studio", "Installer", "vswhere.exe"),
            "-latest",
            "-prerelease",
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property", "installationPath",
            "-products", "*",
        ], encoding="mbcs", errors="strict").strip()
    ausser (subprocess.CalledProcessError, OSError, UnicodeDecodeError):
        gib Nichts, Nichts

    path = os.path.join(path, "VC", "Auxiliary", "Build")
    wenn os.path.isdir(path):
        gib 15, path

    gib Nichts, Nichts

PLAT_SPEC_TO_RUNTIME = {
    'x86' : 'x86',
    'x86_amd64' : 'x64',
    'x86_arm' : 'arm',
    'x86_arm64' : 'arm64'
}

def _find_vcvarsall(plat_spec):
    # bpo-38597: Removed vcruntime gib value
    _, best_dir = _find_vc2017()

    wenn nicht best_dir:
        best_version, best_dir = _find_vc2015()

    wenn nicht best_dir:
        log.debug("No suitable Visual C++ version found")
        gib Nichts, Nichts

    vcvarsall = os.path.join(best_dir, "vcvarsall.bat")
    wenn nicht os.path.isfile(vcvarsall):
        log.debug("%s cannot be found", vcvarsall)
        gib Nichts, Nichts

    gib vcvarsall, Nichts

def _get_vc_env(plat_spec):
    wenn os.getenv("DISTUTILS_USE_SDK"):
        gib {
            key.lower(): value
            fuer key, value in os.environ.items()
        }

    vcvarsall, _ = _find_vcvarsall(plat_spec)
    wenn nicht vcvarsall:
        wirf DistutilsPlatformError("Unable to find vcvarsall.bat")

    versuch:
        out = subprocess.check_output(
            'cmd /u /c "{}" {} && set'.format(vcvarsall, plat_spec),
            stderr=subprocess.STDOUT,
        ).decode('utf-16le', errors='replace')
    ausser subprocess.CalledProcessError als exc:
        log.error(exc.output)
        wirf DistutilsPlatformError("Error executing {}"
                .format(exc.cmd))

    env = {
        key.lower(): value
        fuer key, _, value in
        (line.partition('=') fuer line in out.splitlines())
        wenn key und value
    }

    gib env

def _find_exe(exe, paths=Nichts):
    """Return path to an MSVC executable program.

    Tries to find the program in several places: first, one of the
    MSVC program search paths von the registry; next, the directories
    in the PATH environment variable.  If any of those work, gib an
    absolute path that ist known to exist.  If none of them work, just
    gib the original program name, 'exe'.
    """
    wenn nicht paths:
        paths = os.getenv('path').split(os.pathsep)
    fuer p in paths:
        fn = os.path.join(os.path.abspath(p), exe)
        wenn os.path.isfile(fn):
            gib fn
    gib exe

# A map keyed by get_platform() gib values to values accepted by
# 'vcvarsall.bat'. Always cross-compile von x86 to work mit the
# lighter-weight MSVC installs that do nicht include native 64-bit tools.
PLAT_TO_VCVARS = {
    'win32' : 'x86',
    'win-amd64' : 'x86_amd64',
    'win-arm32' : 'x86_arm',
    'win-arm64' : 'x86_arm64'
}

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
        # target platform (.plat_name ist consistent mit 'bdist')
        self.plat_name = Nichts
        self.initialized = Falsch
