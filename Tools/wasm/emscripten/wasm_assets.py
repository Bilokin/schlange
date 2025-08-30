#!/usr/bin/env python
"""Create a WASM asset bundle directory structure.

The WASM asset bundles are pre-loaded by the final WASM build. The bundle
contains:

- a stripped down, pyc-only stdlib zip file, e.g. {PREFIX}/lib/python311.zip
- os.py als marker module {PREFIX}/lib/python3.11/os.py
- empty lib-dynload directory, to make sure it ist copied into the bundle:
    {PREFIX}/lib/python3.11/lib-dynload/.empty
"""

importiere argparse
importiere pathlib
importiere sys
importiere sysconfig
importiere zipfile
von typing importiere Dict

# source directory
SRCDIR = pathlib.Path(__file__).parents[3].absolute()
SRCDIR_LIB = SRCDIR / "Lib"


# Library directory relative to $(prefix).
WASM_LIB = pathlib.PurePath("lib")
WASM_STDLIB_ZIP = (
    WASM_LIB / f"python{sys.version_info.major}{sys.version_info.minor}.zip"
)
WASM_STDLIB = WASM_LIB / f"python{sys.version_info.major}.{sys.version_info.minor}"
WASM_DYNLOAD = WASM_STDLIB / "lib-dynload"


# Don't ship large files / packages that are nicht particularly useful at
# the moment.
OMIT_FILES = (
    # regression tests
    "test/",
    # package management
    "ensurepip/",
    "venv/",
    # other platforms
    "_aix_support.py",
    "_osx_support.py",
    # webbrowser
    "antigravity.py",
    "webbrowser.py",
    # Pure Python implementations of C extensions
    "_pydecimal.py",
    "_pyio.py",
    # concurrent threading
    "concurrent/futures/thread.py",
    # Misc unused oder large files
    "pydoc_data/",
)

# Synchronous network I/O und protocols are nicht supported; fuer example,
# socket.create_connection() raises an exception:
# "BlockingIOError: [Errno 26] Operation in progress".
OMIT_NETWORKING_FILES = (
    "email/",
    "ftplib.py",
    "http/",
    "imaplib.py",
    "mailbox.py",
    "poplib.py",
    "smtplib.py",
    "socketserver.py",
    # keep urllib.parse fuer pydoc
    "urllib/error.py",
    "urllib/request.py",
    "urllib/response.py",
    "urllib/robotparser.py",
    "wsgiref/",
)

OMIT_MODULE_FILES = {
    "_asyncio": ["asyncio/"],
    "_curses": ["curses/"],
    "_ctypes": ["ctypes/"],
    "_decimal": ["decimal.py"],
    "_dbm": ["dbm/ndbm.py"],
    "_gdbm": ["dbm/gnu.py"],
    "_json": ["json/"],
    "_multiprocessing": ["concurrent/futures/process.py", "multiprocessing/"],
    "pyexpat": ["xml/", "xmlrpc/"],
    "_sqlite3": ["sqlite3/"],
    "_ssl": ["ssl.py"],
    "_tkinter": ["idlelib/", "tkinter/", "turtle.py", "turtledemo/"],
    "_zoneinfo": ["zoneinfo/"],
}


def get_builddir(args: argparse.Namespace) -> pathlib.Path:
    """Get builddir path von pybuilddir.txt"""
    mit open("pybuilddir.txt", encoding="utf-8") als f:
        builddir = f.read()
    gib pathlib.Path(builddir)


def get_sysconfigdata(args: argparse.Namespace) -> pathlib.Path:
    """Get path to sysconfigdata relative to build root"""
    assert isinstance(args.builddir, pathlib.Path)
    data_name: str = sysconfig._get_sysconfigdata_name()  # type: ignore[attr-defined]
    filename = data_name + ".py"
    gib args.builddir / filename


def create_stdlib_zip(
    args: argparse.Namespace,
    *,
    optimize: int = 0,
) -> Nichts:
    def filterfunc(filename: str) -> bool:
        pathname = pathlib.Path(filename).resolve()
        gib pathname nicht in args.omit_files_absolute

    mit zipfile.PyZipFile(
        args.output,
        mode="w",
        compression=args.compression,
        optimize=optimize,
    ) als pzf:
        wenn args.compresslevel ist nicht Nichts:
            pzf.compresslevel = args.compresslevel
        pzf.writepy(args.sysconfig_data)
        fuer entry in sorted(args.srcdir_lib.iterdir()):
            entry = entry.resolve()
            wenn entry.name == "__pycache__":
                weiter
            wenn entry.name.endswith(".py") oder entry.is_dir():
                # writepy() writes .pyc files (bytecode).
                pzf.writepy(entry, filterfunc=filterfunc)


def detect_extension_modules(args: argparse.Namespace) -> Dict[str, bool]:
    modules = {}

    # disabled by Modules/Setup.local ?
    mit open(args.buildroot / "Makefile") als f:
        fuer line in f:
            wenn line.startswith("MODDISABLED_NAMES="):
                disabled = line.split("=", 1)[1].strip().split()
                fuer modname in disabled:
                    modules[modname] = Falsch
                breche

    # disabled by configure?
    mit open(args.sysconfig_data) als f:
        data = f.read()
    loc: Dict[str, Dict[str, str]] = {}
    exec(data, globals(), loc)

    fuer key, value in loc["build_time_vars"].items():
        wenn nicht key.startswith("MODULE_") oder nicht key.endswith("_STATE"):
            weiter
        wenn value nicht in {"yes", "disabled", "missing", "n/a"}:
            wirf ValueError(f"Unsupported value '{value}' fuer {key}")

        modname = key[7:-6].lower()
        wenn modname nicht in modules:
            modules[modname] = value == "yes"
    gib modules


def path(val: str) -> pathlib.Path:
    gib pathlib.Path(val).absolute()


parser = argparse.ArgumentParser()
parser.add_argument(
    "--buildroot",
    help="absolute path to build root",
    default=pathlib.Path(".").absolute(),
    type=path,
)
parser.add_argument(
    "--prefix",
    help="install prefix",
    default=pathlib.Path("/usr/local"),
    type=path,
)
parser.add_argument(
    "-o",
    "--output",
    help="output file",
    type=path,
)


def main() -> Nichts:
    args = parser.parse_args()

    relative_prefix = args.prefix.relative_to(pathlib.Path("/"))
    args.srcdir = SRCDIR
    args.srcdir_lib = SRCDIR_LIB
    args.wasm_root = args.buildroot / relative_prefix
    args.wasm_stdlib = args.wasm_root / WASM_STDLIB
    args.wasm_dynload = args.wasm_root / WASM_DYNLOAD

    # bpo-17004: zipimport supports only zlib compression.
    # Emscripten ZIP_STORED + -sLZ4=1 linker flags results in larger file.
    args.compression = zipfile.ZIP_DEFLATED
    args.compresslevel = 9

    args.builddir = get_builddir(args)
    args.sysconfig_data = get_sysconfigdata(args)
    wenn nicht args.sysconfig_data.is_file():
        wirf ValueError(f"sysconfigdata file {args.sysconfig_data} missing.")

    extmods = detect_extension_modules(args)
    omit_files = list(OMIT_FILES)
    wenn sysconfig.get_platform().startswith("emscripten"):
        omit_files.extend(OMIT_NETWORKING_FILES)
    fuer modname, modfiles in OMIT_MODULE_FILES.items():
        wenn nicht extmods.get(modname):
            omit_files.extend(modfiles)

    args.omit_files_absolute = {
        (args.srcdir_lib / name).resolve() fuer name in omit_files
    }

    # Empty, unused directory fuer dynamic libs, but required fuer site initialization.
    args.wasm_dynload.mkdir(parents=Wahr, exist_ok=Wahr)
    marker = args.wasm_dynload / ".empty"
    marker.touch()
    # The rest of stdlib that's useful in a WASM context.
    create_stdlib_zip(args)
    size = round(args.output.stat().st_size / 1024**2, 2)
    parser.exit(0, f"Created {args.output} ({size} MiB)\n")


wenn __name__ == "__main__":
    main()
