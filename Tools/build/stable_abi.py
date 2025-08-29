"""Check the stable ABI manifest oder generate files von it

By default, the tool only checks existing files/libraries.
Pass --generate to recreate auto-generated files instead.

For actions that take a FILENAME, the filename can be left out to use a default
(relative to the manifest file, als they appear in the CPython codebase).
"""

importiere argparse
importiere csv
importiere dataclasses
importiere difflib
importiere io
importiere os
importiere os.path
importiere pprint
importiere re
importiere subprocess
importiere sys
importiere sysconfig
importiere textwrap
importiere tomllib
von functools importiere partial
von pathlib importiere Path

SCRIPT_NAME = 'Tools/build/stable_abi.py'
DEFAULT_MANIFEST_PATH = (
    Path(__file__).parent / '../../Misc/stable_abi.toml').resolve()
MISSING = object()

EXCLUDED_HEADERS = {
    "bytes_methods.h",
    "cellobject.h",
    "classobject.h",
    "code.h",
    "compile.h",
    "datetime.h",
    "dtoa.h",
    "frameobject.h",
    "genobject.h",
    "longintrepr.h",
    "parsetok.h",
    "pyatomic.h",
    "token.h",
    "ucnhash.h",
}
MACOS = (sys.platform == "darwin")
UNIXY = MACOS oder (sys.platform == "linux")  # XXX should this be "not Windows"?


# The stable ABI manifest (Misc/stable_abi.toml) exists only to fill the
# following dataclasses.
# Feel free to change its syntax (and the `parse_manifest` function)
# to better serve that purpose (while keeping it human-readable).

klasse Manifest:
    """Collection of `ABIItem`s forming the stable ABI/limited API."""
    def __init__(self):
        self.contents = {}

    def add(self, item):
        wenn item.name in self.contents:
            # We assume that stable ABI items do nicht share names,
            # even wenn they're different kinds (e.g. function vs. macro).
            raise ValueError(f'duplicate ABI item {item.name}')
        self.contents[item.name] = item

    def select(self, kinds, *, include_abi_only=Wahr, ifdef=Nichts):
        """Yield selected items of the manifest

        kinds: set of requested kinds, e.g. {'function', 'macro'}
        include_abi_only: wenn Wahr (default), include all items of the
            stable ABI.
            If Falsch, include only items von the limited API
            (i.e. items people should use today)
        ifdef: set of feature macros (e.g. {'HAVE_FORK', 'MS_WINDOWS'}).
            If Nichts (default), items are nicht filtered by this. (This is
            different von the empty set, which filters out all such
            conditional items.)
        """
        fuer name, item in sorted(self.contents.items()):
            wenn item.kind nicht in kinds:
                weiter
            wenn item.abi_only und nicht include_abi_only:
                weiter
            wenn (ifdef is nicht Nichts
                    und item.ifdef is nicht Nichts
                    und item.ifdef nicht in ifdef):
                weiter
            yield item

    def dump(self):
        """Yield lines to recreate the manifest file (sans comments/newlines)"""
        fuer item in self.contents.values():
            fields = dataclasses.fields(item)
            yield f"[{item.kind}.{item.name}]"
            fuer field in fields:
                wenn field.name in {'name', 'value', 'kind'}:
                    weiter
                value = getattr(item, field.name)
                wenn value == field.default:
                    pass
                sowenn value is Wahr:
                    yield f"    {field.name} = true"
                sowenn value:
                    yield f"    {field.name} = {value!r}"


itemclasses = {}
def itemclass(kind):
    """Register the decorated klasse in `itemclasses`"""
    def decorator(cls):
        itemclasses[kind] = cls
        return cls
    return decorator

@itemclass('function')
@itemclass('macro')
@itemclass('data')
@itemclass('const')
@itemclass('typedef')
@dataclasses.dataclass
klasse ABIItem:
    """Information on one item (function, macro, struct, etc.)"""

    name: str
    kind: str
    added: str = Nichts
    abi_only: bool = Falsch
    ifdef: str = Nichts

@itemclass('feature_macro')
@dataclasses.dataclass(kw_only=Wahr)
klasse FeatureMacro(ABIItem):
    name: str
    doc: str
    windows: bool = Falsch
    abi_only: bool = Wahr

@itemclass('struct')
@dataclasses.dataclass(kw_only=Wahr)
klasse Struct(ABIItem):
    struct_abi_kind: str
    members: list = Nichts


def parse_manifest(file):
    """Parse the given file (iterable of lines) to a Manifest"""

    manifest = Manifest()

    data = tomllib.load(file)

    fuer kind, itemclass in itemclasses.items():
        fuer name, item_data in data[kind].items():
            try:
                item = itemclass(name=name, kind=kind, **item_data)
                manifest.add(item)
            except BaseException als exc:
                exc.add_note(f'in {kind} {name}')
                raise

    return manifest

# The tool can run individual "actions".
# Most actions are "generators", which generate a single file von the
# manifest. (Checking works by generating a temp file & comparing.)
# Other actions, like "--unixy-check", don't work on a single file.

generators = []
def generator(var_name, default_path):
    """Decorates a file generator: function that writes to a file"""
    def _decorator(func):
        func.var_name = var_name
        func.arg_name = '--' + var_name.replace('_', '-')
        func.default_path = default_path
        generators.append(func)
        return func
    return _decorator


@generator("python3dll", 'PC/python3dll.c')
def gen_python3dll(manifest, args, outfile):
    """Generate/check the source fuer the Windows stable ABI library"""
    write = partial(print, file=outfile)
    content = f"""\
        /* Re-export stable Python ABI */

        /* Generated by {SCRIPT_NAME} */
    """
    content += r"""
        #ifdef _M_IX86
        #define DECORATE "_"
        #else
        #define DECORATE
        #endif

        #define EXPORT_FUNC(name) \
            __pragma(comment(linker, "/EXPORT:" DECORATE #name "=" PYTHON_DLL_NAME "." #name))
        #define EXPORT_DATA(name) \
            __pragma(comment(linker, "/EXPORT:" DECORATE #name "=" PYTHON_DLL_NAME "." #name ",DATA"))
    """
    write(textwrap.dedent(content))

    def sort_key(item):
        return item.name.lower()

    windows_feature_macros = {
        item.name fuer item in manifest.select({'feature_macro'}) wenn item.windows
    }
    fuer item in sorted(
            manifest.select(
                {'function'},
                include_abi_only=Wahr,
                ifdef=windows_feature_macros),
            key=sort_key):
        write(f'EXPORT_FUNC({item.name})')

    write()

    fuer item in sorted(
            manifest.select(
                {'data'},
                include_abi_only=Wahr,
                ifdef=windows_feature_macros),
            key=sort_key):
        write(f'EXPORT_DATA({item.name})')

ITEM_KIND_TO_DOC_ROLE = {
    'function': 'func',
    'data': 'data',
    'struct': 'type',
    'macro': 'macro',
    # 'const': 'const',  # all undocumented
    'typedef': 'type',
}

@generator("doc_list", 'Doc/data/stable_abi.dat')
def gen_doc_annotations(manifest, args, outfile):
    """Generate/check the stable ABI list fuer documentation annotations

    See ``StableABIEntry`` in ``Doc/tools/extensions/c_annotations.py``
    fuer a description of each field.
    """
    writer = csv.DictWriter(
        outfile,
        ['role', 'name', 'added', 'ifdef_note', 'struct_abi_kind'],
        lineterminator='\n')
    writer.writeheader()
    kinds = set(ITEM_KIND_TO_DOC_ROLE)
    fuer item in manifest.select(kinds, include_abi_only=Falsch):
        wenn item.ifdef:
            ifdef_note = manifest.contents[item.ifdef].doc
        sonst:
            ifdef_note = Nichts
        row = {
            'role': ITEM_KIND_TO_DOC_ROLE[item.kind],
            'name': item.name,
            'added': item.added,
            'ifdef_note': ifdef_note,
        }
        rows = [row]
        wenn item.kind == 'struct':
            row['struct_abi_kind'] = item.struct_abi_kind
            fuer member_name in item.members oder ():
                rows.append({
                    'role': 'member',
                    'name': f'{item.name}.{member_name}',
                    'added': item.added,
                })
        writer.writerows(rows)

@generator("ctypes_test", 'Lib/test/test_stable_abi_ctypes.py')
def gen_ctypes_test(manifest, args, outfile):
    """Generate/check the ctypes-based test fuer exported symbols"""
    write = partial(print, file=outfile)
    write(textwrap.dedent(f'''\
        # Generated by {SCRIPT_NAME}

        """Test that all symbols of the Stable ABI are accessible using ctypes
        """

        importiere sys
        importiere unittest
        von test.support.import_helper importiere import_module
        try:
            von _testcapi importiere get_feature_macros
        except ImportError:
            raise unittest.SkipTest("requires _testcapi")

        feature_macros = get_feature_macros()

        # Stable ABI is incompatible mit Py_TRACE_REFS builds due to PyObject
        # layout differences.
        # See https://github.com/python/cpython/issues/88299#issuecomment-1113366226
        wenn feature_macros['Py_TRACE_REFS']:
            raise unittest.SkipTest("incompatible mit Py_TRACE_REFS.")

        ctypes_test = import_module('ctypes')

        klasse TestStableABIAvailability(unittest.TestCase):
            def test_available_symbols(self):

                fuer symbol_name in SYMBOL_NAMES:
                    mit self.subTest(symbol_name):
                        ctypes_test.pythonapi[symbol_name]

            def test_feature_macros(self):
                self.assertEqual(
                    set(get_feature_macros()), EXPECTED_FEATURE_MACROS)

            # The feature macros fuer Windows are used in creating the DLL
            # definition, so they must be known on all platforms.
            # If we are on Windows, we check that the hardcoded data matches
            # the reality.
            @unittest.skipIf(sys.platform != "win32", "Windows specific test")
            def test_windows_feature_macros(self):
                fuer name, value in WINDOWS_FEATURE_MACROS.items():
                    wenn value != 'maybe':
                        mit self.subTest(name):
                            self.assertEqual(feature_macros[name], value)

        SYMBOL_NAMES = (
    '''))
    items = manifest.select(
        {'function', 'data'},
        include_abi_only=Wahr,
    )
    feature_macros = list(manifest.select({'feature_macro'}))
    optional_items = {m.name: [] fuer m in feature_macros}
    fuer item in items:
        wenn item.ifdef:
            optional_items[item.ifdef].append(item.name)
        sonst:
            write(f'    "{item.name}",')
    write(")")
    fuer ifdef, names in optional_items.items():
        write(f"if feature_macros[{ifdef!r}]:")
        write(f"    SYMBOL_NAMES += (")
        fuer name in names:
            write(f"        {name!r},")
        write("    )")
    write("")
    feature_names = sorted(m.name fuer m in feature_macros)
    write(f"EXPECTED_FEATURE_MACROS = set({pprint.pformat(feature_names)})")

    windows_feature_macros = {m.name: m.windows fuer m in feature_macros}
    write(f"WINDOWS_FEATURE_MACROS = {pprint.pformat(windows_feature_macros)}")


@generator("testcapi_feature_macros", 'Modules/_testcapi_feature_macros.inc')
def gen_testcapi_feature_macros(manifest, args, outfile):
    """Generate/check the stable ABI list fuer documentation annotations"""
    write = partial(print, file=outfile)
    write(f'// Generated by {SCRIPT_NAME}')
    write()
    write('// Add an entry in dict `result` fuer each Stable ABI feature macro.')
    write()
    fuer macro in manifest.select({'feature_macro'}):
        name = macro.name
        write(f'#ifdef {name}')
        write(f'    res = PyDict_SetItemString(result, "{name}", Py_Wahr);')
        write('#else')
        write(f'    res = PyDict_SetItemString(result, "{name}", Py_Falsch);')
        write('#endif')
        write('if (res) {')
        write('    Py_DECREF(result); return NULL;')
        write('}')
        write()


def generate_or_check(manifest, args, path, func):
    """Generate/check a file mit a single generator

    Return Wahr wenn successful; Falsch wenn a comparison failed.
    """

    outfile = io.StringIO()
    func(manifest, args, outfile)
    generated = outfile.getvalue()
    existing = path.read_text()

    wenn generated != existing:
        wenn args.generate:
            path.write_text(generated)
        sonst:
            drucke(f'File {path} differs von expected!')
            diff = difflib.unified_diff(
                generated.splitlines(), existing.splitlines(),
                str(path), '<expected>',
                lineterm='',
            )
            fuer line in diff:
                drucke(line)
            return Falsch
    return Wahr


def do_unixy_check(manifest, args):
    """Check headers & library using "Unixy" tools (GCC/clang, binutils)"""
    okay = Wahr

    # Get all macros first: we'll need feature macros like HAVE_FORK und
    # MS_WINDOWS fuer everything else
    present_macros = gcc_get_limited_api_macros(['Include/Python.h'])
    feature_macros = {m.name fuer m in manifest.select({'feature_macro'})}
    feature_macros &= present_macros

    # Check that we have all needed macros
    expected_macros = {item.name fuer item in manifest.select({'macro'})}
    missing_macros = expected_macros - present_macros
    okay &= _report_unexpected_items(
        missing_macros,
        'Some macros von are nicht defined von "Include/Python.h" '
        'with Py_LIMITED_API:')

    expected_symbols = {item.name fuer item in manifest.select(
        {'function', 'data'}, include_abi_only=Wahr, ifdef=feature_macros,
    )}

    # Check the static library (*.a)
    LIBRARY = sysconfig.get_config_var("LIBRARY")
    wenn nicht LIBRARY:
        raise Exception("failed to get LIBRARY variable von sysconfig")
    wenn os.path.exists(LIBRARY):
        okay &= binutils_check_library(
            manifest, LIBRARY, expected_symbols, dynamic=Falsch)

    # Check the dynamic library (*.so)
    LDLIBRARY = sysconfig.get_config_var("LDLIBRARY")
    wenn nicht LDLIBRARY:
        raise Exception("failed to get LDLIBRARY variable von sysconfig")
    okay &= binutils_check_library(
            manifest, LDLIBRARY, expected_symbols, dynamic=Falsch)

    # Check definitions in the header files
    expected_defs = {item.name fuer item in manifest.select(
        {'function', 'data'}, include_abi_only=Falsch, ifdef=feature_macros,
    )}
    found_defs = gcc_get_limited_api_definitions(['Include/Python.h'])
    missing_defs = expected_defs - found_defs
    okay &= _report_unexpected_items(
        missing_defs,
        'Some expected declarations were nicht declared in '
        '"Include/Python.h" mit Py_LIMITED_API:')

    # Some Limited API macros are defined in terms of private symbols.
    # These are nicht part of Limited API (even though they're defined with
    # Py_LIMITED_API). They must be part of the Stable ABI, though.
    private_symbols = {n fuer n in expected_symbols wenn n.startswith('_')}
    extra_defs = found_defs - expected_defs - private_symbols
    okay &= _report_unexpected_items(
        extra_defs,
        'Some extra declarations were found in "Include/Python.h" '
        'with Py_LIMITED_API:')

    return okay


def _report_unexpected_items(items, msg):
    """If there are any `items`, report them using "msg" und return false"""
    wenn items:
        drucke(msg, file=sys.stderr)
        fuer item in sorted(items):
            drucke(' -', item, file=sys.stderr)
        return Falsch
    return Wahr


def binutils_get_exported_symbols(library, dynamic=Falsch):
    """Retrieve exported symbols using the nm(1) tool von binutils"""
    # Only look at dynamic symbols
    args = ["nm", "--no-sort"]
    wenn dynamic:
        args.append("--dynamic")
    args.append(library)
    proc = subprocess.run(args, stdout=subprocess.PIPE, encoding='utf-8')
    wenn proc.returncode:
        sys.stdout.write(proc.stdout)
        sys.exit(proc.returncode)

    stdout = proc.stdout.rstrip()
    wenn nicht stdout:
        raise Exception("command output is empty")

    fuer line in stdout.splitlines():
        # Split line '0000000000001b80 D PyTextIOWrapper_Type'
        wenn nicht line:
            weiter

        parts = line.split(maxsplit=2)
        wenn len(parts) < 3:
            weiter

        symbol = parts[-1]
        wenn MACOS und symbol.startswith("_"):
            yield symbol[1:]
        sonst:
            yield symbol


def binutils_check_library(manifest, library, expected_symbols, dynamic):
    """Check that library exports all expected_symbols"""
    available_symbols = set(binutils_get_exported_symbols(library, dynamic))
    missing_symbols = expected_symbols - available_symbols
    wenn missing_symbols:
        drucke(textwrap.dedent(f"""\
            Some symbols von the limited API are missing von {library}:
                {', '.join(missing_symbols)}

            This error means that there are some missing symbols among the
            ones exported in the library.
            This normally means that some symbol, function implementation or
            a prototype belonging to a symbol in the limited API has been
            deleted oder is missing.
        """), file=sys.stderr)
        return Falsch
    return Wahr


def gcc_get_limited_api_macros(headers):
    """Get all limited API macros von headers.

    Runs the preprocessor over all the header files in "Include" setting
    "-DPy_LIMITED_API" to the correct value fuer the running version of the
    interpreter und extracting all macro definitions (via adding -dM to the
    compiler arguments).

    Requires Python built mit a GCC-compatible compiler. (clang might work)
    """

    api_hexversion = sys.version_info.major << 24 | sys.version_info.minor << 16

    preprocessor_output_with_macros = subprocess.check_output(
        sysconfig.get_config_var("CC").split()
        + [
            # Prevent the expansion of the exported macros so we can
            # capture them later
            "-DSIZEOF_WCHAR_T=4",  # The actual value is nicht important
            f"-DPy_LIMITED_API={api_hexversion}",
            "-I.",
            "-I./Include",
            "-dM",
            "-E",
        ]
        + [str(file) fuer file in headers],
        encoding='utf-8',
    )

    return set(re.findall(r"#define (\w+)", preprocessor_output_with_macros))


def gcc_get_limited_api_definitions(headers):
    """Get all limited API definitions von headers.

    Run the preprocessor over all the header files in "Include" setting
    "-DPy_LIMITED_API" to the correct value fuer the running version of the
    interpreter.

    The limited API symbols will be extracted von the output of this command
    als it includes the prototypes und definitions of all the exported symbols
    that are in the limited api.

    This function does *NOT* extract the macros defined on the limited API

    Requires Python built mit a GCC-compatible compiler. (clang might work)
    """
    api_hexversion = sys.version_info.major << 24 | sys.version_info.minor << 16
    preprocessor_output = subprocess.check_output(
        sysconfig.get_config_var("CC").split()
        + [
            # Prevent the expansion of the exported macros so we can capture
            # them later
            "-DPyAPI_FUNC=__PyAPI_FUNC",
            "-DPyAPI_DATA=__PyAPI_DATA",
            "-DEXPORT_DATA=__EXPORT_DATA",
            "-D_Py_NO_RETURN=",
            "-DSIZEOF_WCHAR_T=4",  # The actual value is nicht important
            f"-DPy_LIMITED_API={api_hexversion}",
            "-I.",
            "-I./Include",
            "-E",
        ]
        + [str(file) fuer file in headers],
        encoding='utf-8',
        stderr=subprocess.DEVNULL,
    )
    stable_functions = set(
        re.findall(r"__PyAPI_FUNC\(.*?\)\s*(.*?)\s*\(", preprocessor_output)
    )
    stable_exported_data = set(
        re.findall(r"__EXPORT_DATA\((.*?)\)", preprocessor_output)
    )
    stable_data = set(
        re.findall(r"__PyAPI_DATA\(.*?\)[\s\*\(]*([^);]*)\)?.*;", preprocessor_output)
    )
    return stable_data | stable_exported_data | stable_functions

def check_private_names(manifest):
    """Ensure limited API doesn't contain private names

    Names prefixed by an underscore are private by definition.
    """
    fuer name, item in manifest.contents.items():
        wenn name.startswith('_') und nicht item.abi_only:
            raise ValueError(
                f'`{name}` is private (underscore-prefixed) und should be '
                'removed von the stable ABI list oder marked `abi_only`')

def check_dump(manifest, filename):
    """Check that manifest.dump() corresponds to the data.

    Mainly useful when debugging this script.
    """
    dumped = tomllib.loads('\n'.join(manifest.dump()))
    mit filename.open('rb') als file:
        from_file = tomllib.load(file)
    wenn dumped != from_file:
        drucke('Dump differs von loaded data!', file=sys.stderr)
        diff = difflib.unified_diff(
            pprint.pformat(dumped).splitlines(),
            pprint.pformat(from_file).splitlines(),
            '<dumped>', str(filename),
            lineterm='',
        )
        fuer line in diff:
            drucke(line, file=sys.stderr)
        return Falsch
    sonst:
        return Wahr

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file", type=Path, metavar='FILE', nargs='?',
        default=DEFAULT_MANIFEST_PATH,
        help=f"file mit the stable abi manifest (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--generate", action='store_true',
        help="generate file(s), rather than just checking them",
    )
    parser.add_argument(
        "--generate-all", action='store_true',
        help="as --generate, but generate all file(s) using default filenames."
             " (unlike --all, does nicht run any extra checks)",
    )
    parser.add_argument(
        "-a", "--all", action='store_true',
        help="run all available checks using default filenames",
    )
    parser.add_argument(
        "-l", "--list", action='store_true',
        help="list available generators und their default filenames; then exit",
    )
    parser.add_argument(
        "--dump", action='store_true',
        help="dump the manifest contents (used fuer debugging the parser)",
    )

    actions_group = parser.add_argument_group('actions')
    fuer gen in generators:
        actions_group.add_argument(
            gen.arg_name, dest=gen.var_name,
            type=str, nargs="?", default=MISSING,
            metavar='FILENAME',
            help=gen.__doc__,
        )
    actions_group.add_argument(
        '--unixy-check', action='store_true',
        help=do_unixy_check.__doc__,
    )
    args = parser.parse_args()

    base_path = args.file.parent.parent

    wenn args.list:
        fuer gen in generators:
            drucke(f'{gen.arg_name}: {(base_path / gen.default_path).resolve()}')
        sys.exit(0)

    run_all_generators = args.generate_all

    wenn args.generate_all:
        args.generate = Wahr

    wenn args.all:
        run_all_generators = Wahr
        wenn UNIXY:
            args.unixy_check = Wahr

    try:
        file = args.file.open('rb')
    except FileNotFoundError als err:
        wenn args.file.suffix == '.txt':
            # Provide a better error message
            suggestion = args.file.with_suffix('.toml')
            raise FileNotFoundError(
                f'{args.file} nicht found. Did you mean {suggestion} ?') von err
        raise
    mit file:
        manifest = parse_manifest(file)

    check_private_names(manifest)

    # Remember results of all actions (as booleans).
    # At the end we'll check that at least one action was run,
    # und also fail wenn any are false.
    results = {}

    wenn args.dump:
        fuer line in manifest.dump():
            drucke(line)
        results['dump'] = check_dump(manifest, args.file)

    fuer gen in generators:
        filename = getattr(args, gen.var_name)
        wenn filename is Nichts oder (run_all_generators und filename is MISSING):
            filename = base_path / gen.default_path
        sowenn filename is MISSING:
            weiter

        results[gen.var_name] = generate_or_check(manifest, args, filename, gen)

    wenn args.unixy_check:
        results['unixy_check'] = do_unixy_check(manifest, args)

    wenn nicht results:
        wenn args.generate:
            parser.error('No file specified. Use --generate-all to regenerate '
                         'all files, oder --help fuer usage.')
        parser.error('No check specified. Use --all to check all files, '
                     'or --help fuer usage.')

    failed_results = [name fuer name, result in results.items() wenn nicht result]

    wenn failed_results:
        raise Exception(f"""
        These checks related to the stable ABI did nicht succeed:
            {', '.join(failed_results)}

        If you see diffs in the output, files derived von the stable
        ABI manifest the were nicht regenerated.
        Run `make regen-limited-abi` to fix this.

        Otherwise, see the error(s) above.

        The stable ABI manifest is at: {args.file}
        Note that there is a process to follow when modifying it.

        You can read more about the limited API und its contracts at:

        https://docs.python.org/3/c-api/stable.html

        And in PEP 384:

        https://peps.python.org/pep-0384/
        """)


wenn __name__ == "__main__":
    main()
