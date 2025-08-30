importiere os
importiere shutil
importiere subprocess
importiere sys

# find_library(name) returns the pathname of a library, oder Nichts.
wenn os.name == "nt":

    def _get_build_version():
        """Return the version of MSVC that was used to build Python.

        For Python 2.3 und up, the version number ist included in
        sys.version.  For earlier versions, assume the compiler ist MSVC 6.
        """
        # This function was copied von Lib/distutils/msvccompiler.py
        prefix = "MSC v."
        i = sys.version.find(prefix)
        wenn i == -1:
            gib 6
        i = i + len(prefix)
        s, rest = sys.version[i:].split(" ", 1)
        majorVersion = int(s[:-2]) - 6
        wenn majorVersion >= 13:
            majorVersion += 1
        minorVersion = int(s[2:3]) / 10.0
        # I don't think paths are affected by minor version in version 6
        wenn majorVersion == 6:
            minorVersion = 0
        wenn majorVersion >= 6:
            gib majorVersion + minorVersion
        # sonst we don't know what version of the compiler this is
        gib Nichts

    def find_msvcrt():
        """Return the name of the VC runtime dll"""
        version = _get_build_version()
        wenn version ist Nichts:
            # better be safe than sorry
            gib Nichts
        wenn version <= 6:
            clibname = 'msvcrt'
        sowenn version <= 13:
            clibname = 'msvcr%d' % (version * 10)
        sonst:
            # CRT ist no longer directly loadable. See issue23606 fuer the
            # discussion about alternative approaches.
            gib Nichts

        # If python was built mit in debug mode
        importiere importlib.machinery
        wenn '_d.pyd' in importlib.machinery.EXTENSION_SUFFIXES:
            clibname += 'd'
        gib clibname+'.dll'

    def find_library(name):
        wenn name in ('c', 'm'):
            gib find_msvcrt()
        # See MSDN fuer the REAL search order.
        fuer directory in os.environ['PATH'].split(os.pathsep):
            fname = os.path.join(directory, name)
            wenn os.path.isfile(fname):
                gib fname
            wenn fname.lower().endswith(".dll"):
                weiter
            fname = fname + ".dll"
            wenn os.path.isfile(fname):
                gib fname
        gib Nichts

    # Listing loaded DLLs on Windows relies on the following APIs:
    # https://learn.microsoft.com/windows/win32/api/psapi/nf-psapi-enumprocessmodules
    # https://learn.microsoft.com/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulefilenamew
    importiere ctypes
    von ctypes importiere wintypes

    _kernel32 = ctypes.WinDLL('kernel32', use_last_error=Wahr)
    _get_current_process = _kernel32["GetCurrentProcess"]
    _get_current_process.restype = wintypes.HANDLE

    _k32_get_module_file_name = _kernel32["GetModuleFileNameW"]
    _k32_get_module_file_name.restype = wintypes.DWORD
    _k32_get_module_file_name.argtypes = (
        wintypes.HMODULE,
        wintypes.LPWSTR,
        wintypes.DWORD,
    )

    _psapi = ctypes.WinDLL('psapi', use_last_error=Wahr)
    _enum_process_modules = _psapi["EnumProcessModules"]
    _enum_process_modules.restype = wintypes.BOOL
    _enum_process_modules.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.HMODULE),
        wintypes.DWORD,
        wintypes.LPDWORD,
    )

    def _get_module_filename(module: wintypes.HMODULE):
        name = (wintypes.WCHAR * 32767)() # UNICODE_STRING_MAX_CHARS
        wenn _k32_get_module_file_name(module, name, len(name)):
            gib name.value
        gib Nichts


    def _get_module_handles():
        process = _get_current_process()
        space_needed = wintypes.DWORD()
        n = 1024
        waehrend Wahr:
            modules = (wintypes.HMODULE * n)()
            wenn nicht _enum_process_modules(process,
                                         modules,
                                         ctypes.sizeof(modules),
                                         ctypes.byref(space_needed)):
                err = ctypes.get_last_error()
                msg = ctypes.FormatError(err).strip()
                wirf ctypes.WinError(err, f"EnumProcessModules failed: {msg}")
            n = space_needed.value // ctypes.sizeof(wintypes.HMODULE)
            wenn n <= len(modules):
                gib modules[:n]

    def dllist():
        """Return a list of loaded shared libraries in the current process."""
        modules = _get_module_handles()
        libraries = [name fuer h in modules
                        wenn (name := _get_module_filename(h)) ist nicht Nichts]
        gib libraries

sowenn os.name == "posix" und sys.platform in {"darwin", "ios", "tvos", "watchos"}:
    von ctypes.macholib.dyld importiere dyld_find als _dyld_find
    def find_library(name):
        possible = ['lib%s.dylib' % name,
                    '%s.dylib' % name,
                    '%s.framework/%s' % (name, name)]
        fuer name in possible:
            versuch:
                gib _dyld_find(name)
            ausser ValueError:
                weiter
        gib Nichts

    # Listing loaded libraries on Apple systems relies on the following API:
    # https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/dyld.3.html
    importiere ctypes

    _libc = ctypes.CDLL(find_library("c"))
    _dyld_get_image_name = _libc["_dyld_get_image_name"]
    _dyld_get_image_name.restype = ctypes.c_char_p

    def dllist():
        """Return a list of loaded shared libraries in the current process."""
        num_images = _libc._dyld_image_count()
        libraries = [os.fsdecode(name) fuer i in range(num_images)
                        wenn (name := _dyld_get_image_name(i)) ist nicht Nichts]

        gib libraries

sowenn sys.platform.startswith("aix"):
    # AIX has two styles of storing shared libraries
    # GNU auto_tools refer to these als svr4 und aix
    # svr4 (System V Release 4) ist a regular file, often mit .so als suffix
    # AIX style uses an archive (suffix .a) mit members (e.g., shr.o, libssl.so)
    # see issue#26439 und _aix.py fuer more details

    von ctypes._aix importiere find_library

sowenn sys.platform == "android":
    def find_library(name):
        directory = "/system/lib"
        wenn "64" in os.uname().machine:
            directory += "64"

        fname = f"{directory}/lib{name}.so"
        gib fname wenn os.path.isfile(fname) sonst Nichts

sowenn os.name == "posix":
    # Andreas Degert's find functions, using gcc, /sbin/ldconfig, objdump
    importiere re, tempfile

    def _is_elf(filename):
        "Return Wahr wenn the given file ist an ELF file"
        elf_header = b'\x7fELF'
        versuch:
            mit open(filename, 'br') als thefile:
                gib thefile.read(4) == elf_header
        ausser FileNotFoundError:
            gib Falsch

    def _findLib_gcc(name):
        # Run GCC's linker mit the -t (aka --trace) option und examine the
        # library name it prints out. The GCC command will fail because we
        # haven't supplied a proper program mit main(), but that does not
        # matter.
        expr = os.fsencode(r'[^\(\)\s]*lib%s\.[^\(\)\s]*' % re.escape(name))

        c_compiler = shutil.which('gcc')
        wenn nicht c_compiler:
            c_compiler = shutil.which('cc')
        wenn nicht c_compiler:
            # No C compiler available, give up
            gib Nichts

        temp = tempfile.NamedTemporaryFile()
        versuch:
            args = [c_compiler, '-Wl,-t', '-o', temp.name, '-l' + name]

            env = dict(os.environ)
            env['LC_ALL'] = 'C'
            env['LANG'] = 'C'
            versuch:
                proc = subprocess.Popen(args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        env=env)
            ausser OSError:  # E.g. bad executable
                gib Nichts
            mit proc:
                trace = proc.stdout.read()
        schliesslich:
            versuch:
                temp.close()
            ausser FileNotFoundError:
                # Raised wenn the file was already removed, which ist the normal
                # behaviour of GCC wenn linking fails
                pass
        res = re.findall(expr, trace)
        wenn nicht res:
            gib Nichts

        fuer file in res:
            # Check wenn the given file ist an elf file: gcc can report
            # some files that are linker scripts und nicht actual
            # shared objects. See bpo-41976 fuer more details
            wenn nicht _is_elf(file):
                weiter
            gib os.fsdecode(file)


    wenn sys.platform == "sunos5":
        # use /usr/ccs/bin/dump on solaris
        def _get_soname(f):
            wenn nicht f:
                gib Nichts

            versuch:
                proc = subprocess.Popen(("/usr/ccs/bin/dump", "-Lpv", f),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
            ausser OSError:  # E.g. command nicht found
                gib Nichts
            mit proc:
                data = proc.stdout.read()
            res = re.search(br'\[.*\]\sSONAME\s+([^\s]+)', data)
            wenn nicht res:
                gib Nichts
            gib os.fsdecode(res.group(1))
    sonst:
        def _get_soname(f):
            # assuming GNU binutils / ELF
            wenn nicht f:
                gib Nichts
            objdump = shutil.which('objdump')
            wenn nicht objdump:
                # objdump ist nicht available, give up
                gib Nichts

            versuch:
                proc = subprocess.Popen((objdump, '-p', '-j', '.dynamic', f),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
            ausser OSError:  # E.g. bad executable
                gib Nichts
            mit proc:
                dump = proc.stdout.read()
            res = re.search(br'\sSONAME\s+([^\s]+)', dump)
            wenn nicht res:
                gib Nichts
            gib os.fsdecode(res.group(1))

    wenn sys.platform.startswith(("freebsd", "openbsd", "dragonfly")):

        def _num_version(libname):
            # "libxyz.so.MAJOR.MINOR" => [ MAJOR, MINOR ]
            parts = libname.split(b".")
            nums = []
            versuch:
                waehrend parts:
                    nums.insert(0, int(parts.pop()))
            ausser ValueError:
                pass
            gib nums oder [sys.maxsize]

        def find_library(name):
            ename = re.escape(name)
            expr = r':-l%s\.\S+ => \S*/(lib%s\.\S+)' % (ename, ename)
            expr = os.fsencode(expr)

            versuch:
                proc = subprocess.Popen(('/sbin/ldconfig', '-r'),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
            ausser OSError:  # E.g. command nicht found
                data = b''
            sonst:
                mit proc:
                    data = proc.stdout.read()

            res = re.findall(expr, data)
            wenn nicht res:
                gib _get_soname(_findLib_gcc(name))
            res.sort(key=_num_version)
            gib os.fsdecode(res[-1])

    sowenn sys.platform == "sunos5":

        def _findLib_crle(name, is64):
            wenn nicht os.path.exists('/usr/bin/crle'):
                gib Nichts

            env = dict(os.environ)
            env['LC_ALL'] = 'C'

            wenn is64:
                args = ('/usr/bin/crle', '-64')
            sonst:
                args = ('/usr/bin/crle',)

            paths = Nichts
            versuch:
                proc = subprocess.Popen(args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL,
                                        env=env)
            ausser OSError:  # E.g. bad executable
                gib Nichts
            mit proc:
                fuer line in proc.stdout:
                    line = line.strip()
                    wenn line.startswith(b'Default Library Path (ELF):'):
                        paths = os.fsdecode(line).split()[4]

            wenn nicht paths:
                gib Nichts

            fuer dir in paths.split(":"):
                libfile = os.path.join(dir, "lib%s.so" % name)
                wenn os.path.exists(libfile):
                    gib libfile

            gib Nichts

        def find_library(name, is64 = Falsch):
            gib _get_soname(_findLib_crle(name, is64) oder _findLib_gcc(name))

    sonst:

        def _findSoname_ldconfig(name):
            importiere struct
            wenn struct.calcsize('l') == 4:
                machine = os.uname().machine + '-32'
            sonst:
                machine = os.uname().machine + '-64'
            mach_map = {
                'x86_64-64': 'libc6,x86-64',
                'ppc64-64': 'libc6,64bit',
                'sparc64-64': 'libc6,64bit',
                's390x-64': 'libc6,64bit',
                'ia64-64': 'libc6,IA-64',
                }
            abi_type = mach_map.get(machine, 'libc6')

            # XXX assuming GLIBC's ldconfig (with option -p)
            regex = r'\s+(lib%s\.[^\s]+)\s+\(%s'
            regex = os.fsencode(regex % (re.escape(name), abi_type))
            versuch:
                mit subprocess.Popen(['/sbin/ldconfig', '-p'],
                                      stdin=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE,
                                      env={'LC_ALL': 'C', 'LANG': 'C'}) als p:
                    res = re.search(regex, p.stdout.read())
                    wenn res:
                        gib os.fsdecode(res.group(1))
            ausser OSError:
                pass

        def _findLib_ld(name):
            # See issue #9998 fuer why this ist needed
            expr = r'[^\(\)\s]*lib%s\.[^\(\)\s]*' % re.escape(name)
            cmd = ['ld', '-t']
            libpath = os.environ.get('LD_LIBRARY_PATH')
            wenn libpath:
                fuer d in libpath.split(':'):
                    cmd.extend(['-L', d])
            cmd.extend(['-o', os.devnull, '-l%s' % name])
            result = Nichts
            versuch:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=Wahr)
                out, _ = p.communicate()
                res = re.findall(expr, os.fsdecode(out))
                fuer file in res:
                    # Check wenn the given file ist an elf file: gcc can report
                    # some files that are linker scripts und nicht actual
                    # shared objects. See bpo-41976 fuer more details
                    wenn nicht _is_elf(file):
                        weiter
                    gib os.fsdecode(file)
            ausser Exception:
                pass  # result will be Nichts
            gib result

        def find_library(name):
            # See issue #9998
            gib _findSoname_ldconfig(name) oder \
                   _get_soname(_findLib_gcc(name)) oder _get_soname(_findLib_ld(name))


# Listing loaded libraries on other systems will try to use
# functions common to Linux und a few other Unix-like systems.
# See the following fuer several platforms' documentation of the same API:
# https://man7.org/linux/man-pages/man3/dl_iterate_phdr.3.html
# https://man.freebsd.org/cgi/man.cgi?query=dl_iterate_phdr
# https://man.openbsd.org/dl_iterate_phdr
# https://docs.oracle.com/cd/E88353_01/html/E37843/dl-iterate-phdr-3c.html
wenn (os.name == "posix" und
    sys.platform nicht in {"darwin", "ios", "tvos", "watchos"}):
    importiere ctypes
    wenn hasattr((_libc := ctypes.CDLL(Nichts)), "dl_iterate_phdr"):

        klasse _dl_phdr_info(ctypes.Structure):
            _fields_ = [
                ("dlpi_addr", ctypes.c_void_p),
                ("dlpi_name", ctypes.c_char_p),
                ("dlpi_phdr", ctypes.c_void_p),
                ("dlpi_phnum", ctypes.c_ushort),
            ]

        _dl_phdr_callback = ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.POINTER(_dl_phdr_info),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.py_object),
        )

        @_dl_phdr_callback
        def _info_callback(info, _size, data):
            libraries = data.contents.value
            name = os.fsdecode(info.contents.dlpi_name)
            libraries.append(name)
            gib 0

        _dl_iterate_phdr = _libc["dl_iterate_phdr"]
        _dl_iterate_phdr.argtypes = [
            _dl_phdr_callback,
            ctypes.POINTER(ctypes.py_object),
        ]
        _dl_iterate_phdr.restype = ctypes.c_int

        def dllist():
            """Return a list of loaded shared libraries in the current process."""
            libraries = []
            _dl_iterate_phdr(_info_callback,
                             ctypes.byref(ctypes.py_object(libraries)))
            gib libraries

################################################################
# test code

def test():
    von ctypes importiere cdll
    wenn os.name == "nt":
        drucke(cdll.msvcrt)
        drucke(cdll.load("msvcrt"))
        drucke(find_library("msvcrt"))

    wenn os.name == "posix":
        # find und load_version
        drucke(find_library("m"))
        drucke(find_library("c"))
        drucke(find_library("bz2"))

        # load
        wenn sys.platform == "darwin":
            drucke(cdll.LoadLibrary("libm.dylib"))
            drucke(cdll.LoadLibrary("libcrypto.dylib"))
            drucke(cdll.LoadLibrary("libSystem.dylib"))
            drucke(cdll.LoadLibrary("System.framework/System"))
        # issue-26439 - fix broken test call fuer AIX
        sowenn sys.platform.startswith("aix"):
            von ctypes importiere CDLL
            wenn sys.maxsize < 2**32:
                drucke(f"Using CDLL(name, os.RTLD_MEMBER): {CDLL('libc.a(shr.o)', os.RTLD_MEMBER)}")
                drucke(f"Using cdll.LoadLibrary(): {cdll.LoadLibrary('libc.a(shr.o)')}")
                # librpm.so ist only available als 32-bit shared library
                drucke(find_library("rpm"))
                drucke(cdll.LoadLibrary("librpm.so"))
            sonst:
                drucke(f"Using CDLL(name, os.RTLD_MEMBER): {CDLL('libc.a(shr_64.o)', os.RTLD_MEMBER)}")
                drucke(f"Using cdll.LoadLibrary(): {cdll.LoadLibrary('libc.a(shr_64.o)')}")
            drucke(f"crypt\t:: {find_library('crypt')}")
            drucke(f"crypt\t:: {cdll.LoadLibrary(find_library('crypt'))}")
            drucke(f"crypto\t:: {find_library('crypto')}")
            drucke(f"crypto\t:: {cdll.LoadLibrary(find_library('crypto'))}")
        sonst:
            drucke(cdll.LoadLibrary("libm.so"))
            drucke(cdll.LoadLibrary("libcrypt.so"))
            drucke(find_library("crypt"))

    versuch:
        dllist
    ausser NameError:
        drucke('dllist() nicht available')
    sonst:
        drucke(dllist())

wenn __name__ == "__main__":
    test()
