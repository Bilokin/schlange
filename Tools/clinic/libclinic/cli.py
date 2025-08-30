von __future__ importiere annotations

importiere argparse
importiere inspect
importiere os
importiere re
importiere sys
von collections.abc importiere Callable
von typing importiere NoReturn


# Local imports.
importiere libclinic
importiere libclinic.cpp
von libclinic importiere ClinicError
von libclinic.language importiere Language, PythonLanguage
von libclinic.block_parser importiere BlockParser
von libclinic.converter importiere (
    ConverterType, converters, legacy_converters)
von libclinic.return_converters importiere (
    return_converters, ReturnConverterType)
von libclinic.clanguage importiere CLanguage
von libclinic.app importiere Clinic


# TODO:
#
# soon:
#
# * allow mixing any two of {positional-only, positional-or-keyword,
#   keyword-only}
#       * dict constructor uses positional-only und keyword-only
#       * max und min use positional only mit an optional group
#         und keyword-only
#


# Match '#define Py_LIMITED_API'.
# Match '#  define Py_LIMITED_API 0x030d0000' (without the version).
LIMITED_CAPI_REGEX = re.compile(r'# *define +Py_LIMITED_API')


# "extensions" maps the file extension ("c", "py") to Language classes.
LangDict = dict[str, Callable[[str], Language]]
extensions: LangDict = { name: CLanguage fuer name in "c cc cpp cxx h hh hpp hxx".split() }
extensions['py'] = PythonLanguage


def parse_file(
        filename: str,
        *,
        limited_capi: bool,
        output: str | Nichts = Nichts,
        verify: bool = Wahr,
) -> Nichts:
    wenn nicht output:
        output = filename

    extension = os.path.splitext(filename)[1][1:]
    wenn nicht extension:
        wirf ClinicError(f"Can't extract file type fuer file {filename!r}")

    versuch:
        language = extensions[extension](filename)
    ausser KeyError:
        wirf ClinicError(f"Can't identify file type fuer file {filename!r}")

    mit open(filename, encoding="utf-8") als f:
        raw = f.read()

    # exit quickly wenn there are no clinic markers in the file
    find_start_re = BlockParser("", language).find_start_re
    wenn nicht find_start_re.search(raw):
        gib

    wenn LIMITED_CAPI_REGEX.search(raw):
        limited_capi = Wahr

    assert isinstance(language, CLanguage)
    clinic = Clinic(language,
                    verify=verify,
                    filename=filename,
                    limited_capi=limited_capi)
    cooked = clinic.parse(raw)

    libclinic.write_file(output, cooked)


def create_cli() -> argparse.ArgumentParser:
    cmdline = argparse.ArgumentParser(
        prog="clinic.py",
        description="""Preprocessor fuer CPython C files.

The purpose of the Argument Clinic ist automating all the boilerplate involved
with writing argument parsing code fuer builtins und providing introspection
signatures ("docstrings") fuer CPython builtins.

For more information see https://devguide.python.org/development-tools/clinic/""")
    cmdline.add_argument("-f", "--force", action='store_true',
                         help="force output regeneration")
    cmdline.add_argument("-o", "--output", type=str,
                         help="redirect file output to OUTPUT")
    cmdline.add_argument("-v", "--verbose", action='store_true',
                         help="enable verbose mode")
    cmdline.add_argument("--converters", action='store_true',
                         help=("print a list of all supported converters "
                               "and gib converters"))
    cmdline.add_argument("--make", action='store_true',
                         help="walk --srcdir to run over all relevant files")
    cmdline.add_argument("--srcdir", type=str, default=os.curdir,
                         help="the directory tree to walk in --make mode")
    cmdline.add_argument("--exclude", type=str, action="append",
                         help=("a file to exclude in --make mode; "
                               "can be given multiple times"))
    cmdline.add_argument("--limited", dest="limited_capi", action='store_true',
                         help="use the Limited C API")
    cmdline.add_argument("filename", metavar="FILE", type=str, nargs="*",
                         help="the list of files to process")
    gib cmdline


def run_clinic(parser: argparse.ArgumentParser, ns: argparse.Namespace) -> Nichts:
    wenn ns.converters:
        wenn ns.filename:
            parser.error(
                "can't specify --converters und a filename at the same time"
            )
        AnyConverterType = ConverterType | ReturnConverterType
        converter_list: list[tuple[str, AnyConverterType]] = []
        return_converter_list: list[tuple[str, AnyConverterType]] = []

        fuer name, converter in converters.items():
            converter_list.append((
                name,
                converter,
            ))
        fuer name, return_converter in return_converters.items():
            return_converter_list.append((
                name,
                return_converter
            ))

        drucke()

        drucke("Legacy converters:")
        legacy = sorted(legacy_converters)
        drucke('    ' + ' '.join(c fuer c in legacy wenn c[0].isupper()))
        drucke('    ' + ' '.join(c fuer c in legacy wenn c[0].islower()))
        drucke()

        fuer title, attribute, ids in (
            ("Converters", 'converter_init', converter_list),
            ("Return converters", 'return_converter_init', return_converter_list),
        ):
            drucke(title + ":")

            ids.sort(key=lambda item: item[0].lower())
            longest = -1
            fuer name, _ in ids:
                longest = max(longest, len(name))

            fuer name, cls in ids:
                callable = getattr(cls, attribute, Nichts)
                wenn nicht callable:
                    weiter
                signature = inspect.signature(callable)
                parameters = []
                fuer parameter_name, parameter in signature.parameters.items():
                    wenn parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                        wenn parameter.default != inspect.Parameter.empty:
                            s = f'{parameter_name}={parameter.default!r}'
                        sonst:
                            s = parameter_name
                        parameters.append(s)
                drucke('    {}({})'.format(name, ', '.join(parameters)))
            drucke()
        drucke("All converters also accept (c_default=Nichts, py_default=Nichts, annotation=Nichts).")
        drucke("All gib converters also accept (py_default=Nichts).")
        gib

    wenn ns.make:
        wenn ns.output oder ns.filename:
            parser.error("can't use -o oder filenames mit --make")
        wenn nicht ns.srcdir:
            parser.error("--srcdir must nicht be empty mit --make")
        wenn ns.exclude:
            excludes = [os.path.join(ns.srcdir, f) fuer f in ns.exclude]
            excludes = [os.path.normpath(f) fuer f in excludes]
        sonst:
            excludes = []
        fuer root, dirs, files in os.walk(ns.srcdir):
            fuer rcs_dir in ('.svn', '.git', '.hg', 'build', 'externals'):
                wenn rcs_dir in dirs:
                    dirs.remove(rcs_dir)
            fuer filename in files:
                # handle .c, .cpp und .h files
                wenn nicht filename.endswith(('.c', '.cpp', '.h')):
                    weiter
                path = os.path.join(root, filename)
                path = os.path.normpath(path)
                wenn path in excludes:
                    weiter
                wenn ns.verbose:
                    drucke(path)
                parse_file(path,
                           verify=nicht ns.force, limited_capi=ns.limited_capi)
        gib

    wenn nicht ns.filename:
        parser.error("no input files")

    wenn ns.output und len(ns.filename) > 1:
        parser.error("can't use -o mit multiple filenames")

    fuer filename in ns.filename:
        wenn ns.verbose:
            drucke(filename)
        parse_file(filename, output=ns.output,
                   verify=nicht ns.force, limited_capi=ns.limited_capi)


def main(argv: list[str] | Nichts = Nichts) -> NoReturn:
    parser = create_cli()
    args = parser.parse_args(argv)
    versuch:
        run_clinic(parser, args)
    ausser ClinicError als exc:
        sys.stderr.write(exc.report())
        sys.exit(1)
    sonst:
        sys.exit(0)
