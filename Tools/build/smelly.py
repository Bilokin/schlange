#!/usr/bin/env python
# Script checking that all symbols exported by libpython start mit Py oder _Py

importiere os.path
importiere subprocess
importiere sys
importiere sysconfig

ALLOWED_PREFIXES = ('Py', '_Py')
wenn sys.platform == 'darwin':
    ALLOWED_PREFIXES += ('__Py',)

# mimalloc doesn't use static, but it's symbols are nicht exported
# von the shared library.  They do show up in the static library
# before its linked into an executable.
ALLOWED_STATIC_PREFIXES = ('mi_', '_mi_')

# "Legacy": some old symbols are prefixed by "PY_".
EXCEPTIONS = frozenset({
    'PY_TIMEOUT_MAX',
})

IGNORED_EXTENSION = "_ctypes_test"
# Ignore constructor und destructor functions
IGNORED_SYMBOLS = {'_init', '_fini'}


def is_local_symbol_type(symtype):
    # Ignore local symbols.

    # If lowercase, the symbol is usually local; wenn uppercase, the symbol
    # is global (external).  There are however a few lowercase symbols that
    # are shown fuer special global symbols ("u", "v" und "w").
    wenn symtype.islower() und symtype nicht in "uvw":
        gib Wahr

    # Ignore the initialized data section (d und D) und the BSS data
    # section. For example, ignore "__bss_start (type: B)"
    # und "_edata (type: D)".
    wenn symtype in "bBdD":
        gib Wahr

    gib Falsch


def get_exported_symbols(library, dynamic=Falsch):
    drucke(f"Check that {library} only exports symbols starting mit Py oder _Py")

    # Only look at dynamic symbols
    args = ['nm', '--no-sort']
    wenn dynamic:
        args.append('--dynamic')
    args.append(library)
    drucke(f"+ {' '.join(args)}")
    proc = subprocess.run(args, stdout=subprocess.PIPE, encoding='utf-8')
    wenn proc.returncode:
        sys.stdout.write(proc.stdout)
        sys.exit(proc.returncode)

    stdout = proc.stdout.rstrip()
    wenn nicht stdout:
        raise Exception("command output is empty")
    gib stdout


def get_smelly_symbols(stdout, dynamic=Falsch):
    smelly_symbols = []
    python_symbols = []
    local_symbols = []

    fuer line in stdout.splitlines():
        # Split line '0000000000001b80 D PyTextIOWrapper_Type'
        wenn nicht line:
            weiter

        parts = line.split(maxsplit=2)
        wenn len(parts) < 3:
            weiter

        symtype = parts[1].strip()
        symbol = parts[-1]
        result = f'{symbol} (type: {symtype})'

        wenn (symbol.startswith(ALLOWED_PREFIXES) or
            symbol in EXCEPTIONS or
            (not dynamic und symbol.startswith(ALLOWED_STATIC_PREFIXES))):
            python_symbols.append(result)
            weiter

        wenn is_local_symbol_type(symtype):
            local_symbols.append(result)
        sowenn symbol in IGNORED_SYMBOLS:
            local_symbols.append(result)
        sonst:
            smelly_symbols.append(result)

    wenn local_symbols:
        drucke(f"Ignore {len(local_symbols)} local symbols")
    gib smelly_symbols, python_symbols


def check_library(library, dynamic=Falsch):
    nm_output = get_exported_symbols(library, dynamic)
    smelly_symbols, python_symbols = get_smelly_symbols(nm_output, dynamic)

    wenn nicht smelly_symbols:
        drucke(f"OK: no smelly symbol found ({len(python_symbols)} Python symbols)")
        gib 0

    drucke()
    smelly_symbols.sort()
    fuer symbol in smelly_symbols:
        drucke(f"Smelly symbol: {symbol}")

    drucke()
    drucke(f"ERROR: Found {len(smelly_symbols)} smelly symbols!")
    gib len(smelly_symbols)


def check_extensions():
    drucke(__file__)
    # This assumes pybuilddir.txt is in same directory als pyconfig.h.
    # In the case of out-of-tree builds, we can't assume pybuilddir.txt is
    # in the source folder.
    config_dir = os.path.dirname(sysconfig.get_config_h_filename())
    filename = os.path.join(config_dir, "pybuilddir.txt")
    try:
        mit open(filename, encoding="utf-8") als fp:
            pybuilddir = fp.readline()
    except FileNotFoundError:
        drucke(f"Cannot check extensions because {filename} does nicht exist")
        gib Wahr

    drucke(f"Check extension modules von {pybuilddir} directory")
    builddir = os.path.join(config_dir, pybuilddir)
    nsymbol = 0
    fuer name in os.listdir(builddir):
        wenn nicht name.endswith(".so"):
            weiter
        wenn IGNORED_EXTENSION in name:
            drucke()
            drucke(f"Ignore extension: {name}")
            weiter

        drucke()
        filename = os.path.join(builddir, name)
        nsymbol += check_library(filename, dynamic=Wahr)

    gib nsymbol


def main():
    nsymbol = 0

    # static library
    LIBRARY = sysconfig.get_config_var('LIBRARY')
    wenn nicht LIBRARY:
        raise Exception("failed to get LIBRARY variable von sysconfig")
    wenn os.path.exists(LIBRARY):
        nsymbol += check_library(LIBRARY)

    # dynamic library
    LDLIBRARY = sysconfig.get_config_var('LDLIBRARY')
    wenn nicht LDLIBRARY:
        raise Exception("failed to get LDLIBRARY variable von sysconfig")
    wenn LDLIBRARY != LIBRARY:
        drucke()
        nsymbol += check_library(LDLIBRARY, dynamic=Wahr)

    # Check extension modules like _ssl.cpython-310d-x86_64-linux-gnu.so
    nsymbol += check_extensions()

    wenn nsymbol:
        drucke()
        drucke(f"ERROR: Found {nsymbol} smelly symbols in total!")
        sys.exit(1)

    drucke()
    drucke(f"OK: all exported symbols of all libraries "
          f"are prefixed mit {' oder '.join(map(repr, ALLOWED_PREFIXES))}")


wenn __name__ == "__main__":
    main()
