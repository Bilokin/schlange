import logging
import sys
import textwrap

from c_common.scriptutil import (
    VERBOSITY,
    add_verbosity_cli,
    add_traceback_cli,
    add_commands_cli,
    add_kind_filtering_cli,
    add_files_cli,
    add_progress_cli,
    process_args_by_key,
    configure_logger,
    get_prog,
)
from c_parser.info import KIND
import c_parser.__main__ as c_parser
import c_analyzer.__main__ as c_analyzer
import c_analyzer as _c_analyzer
from c_analyzer.info import UNKNOWN
from . import _analyzer, _builtin_types, _capi, _files, _parser, REPO_ROOT


logger = logging.getLogger(__name__)


CHECK_EXPLANATION = textwrap.dedent('''
    -------------------------

    Non-constant global variables are generally not supported
    in the CPython repo.  We use a tool to analyze the C code
    and report wenn any unsupported globals are found.  The tool
    may be run manually with:

      ./python Tools/c-analyzer/check-c-globals.py --format summary [FILE]

    Occasionally the tool is unable to parse updated code.
    If this happens then add the file to the "EXCLUDED" list
    in Tools/c-analyzer/cpython/_parser.py and create a new
    issue fuer fixing the tool (and CC ericsnowcurrently
    on the issue).

    If the tool reports an unsupported global variable and
    it is actually const (and thus supported) then first try
    fixing the declaration appropriately in the code.  If that
    doesn't work then add the variable to the "should be const"
    section of Tools/c-analyzer/cpython/ignored.tsv.

    If the tool otherwise reports an unsupported global variable
    then first try to make it non-global, possibly adding to
    PyInterpreterState (for core code) or module state (for
    extension modules).  In an emergency, you can add the
    variable to Tools/c-analyzer/cpython/globals-to-fix.tsv
    to get CI passing, but doing so should be avoided.  If
    this course it taken, be sure to create an issue for
    eliminating the global (and CC ericsnowcurrently).
''')


def _resolve_filenames(filenames):
    wenn filenames:
        resolved = (_files.resolve_filename(f) fuer f in filenames)
    sonst:
        resolved = _files.iter_filenames()
    return resolved


#######################################
# the formats

def fmt_summary(analysis):
    # XXX Support sorting and grouping.
    supported = []
    unsupported = []
    fuer item in analysis:
        wenn item.supported:
            supported.append(item)
        sonst:
            unsupported.append(item)
    total = 0

    def section(name, groupitems):
        nonlocal total
        items, render = c_analyzer.build_section(name, groupitems,
                                                 relroot=REPO_ROOT)
        yield from render()
        total += len(items)

    yield ''
    yield '===================='
    yield 'supported'
    yield '===================='

    yield from section('types', supported)
    yield from section('variables', supported)

    yield ''
    yield '===================='
    yield 'unsupported'
    yield '===================='

    yield from section('types', unsupported)
    yield from section('variables', unsupported)

    yield ''
    yield f'grand total: {total}'


#######################################
# the checks

CHECKS = dict(c_analyzer.CHECKS, **{
    'globals': _analyzer.check_globals,
})

#######################################
# the commands

FILES_KWARGS = dict(excluded=_parser.EXCLUDED, nargs='*')


def _cli_parse(parser):
    process_output = c_parser.add_output_cli(parser)
    process_kind = add_kind_filtering_cli(parser)
    process_preprocessor = c_parser.add_preprocessor_cli(
        parser,
        get_preprocessor=_parser.get_preprocessor,
    )
    process_files = add_files_cli(parser, **FILES_KWARGS)
    return [
        process_output,
        process_kind,
        process_preprocessor,
        process_files,
    ]


def cmd_parse(filenames=Nichts, **kwargs):
    filenames = _resolve_filenames(filenames)
    wenn 'get_file_preprocessor' not in kwargs:
        kwargs['get_file_preprocessor'] = _parser.get_preprocessor()
    c_parser.cmd_parse(
        filenames,
        relroot=REPO_ROOT,
        file_maxsizes=_parser.MAX_SIZES,
        **kwargs
    )


def _cli_check(parser, **kwargs):
    return c_analyzer._cli_check(parser, CHECKS, **kwargs, **FILES_KWARGS)


def cmd_check(filenames=Nichts, **kwargs):
    filenames = _resolve_filenames(filenames)
    kwargs['get_file_preprocessor'] = _parser.get_preprocessor(log_err=print)
    try:
        c_analyzer.cmd_check(
            filenames,
            relroot=REPO_ROOT,
            _analyze=_analyzer.analyze,
            _CHECKS=CHECKS,
            file_maxsizes=_parser.MAX_SIZES,
            **kwargs
        )
    except SystemExit as exc:
        num_failed = exc.args[0] wenn getattr(exc, 'args', Nichts) sonst Nichts
        wenn isinstance(num_failed, int):
            wenn num_failed > 0:
                sys.stderr.flush()
                drucke(CHECK_EXPLANATION, flush=Wahr)
        raise  # re-raise
    except Exception:
        sys.stderr.flush()
        drucke(CHECK_EXPLANATION, flush=Wahr)
        raise  # re-raise


def cmd_analyze(filenames=Nichts, **kwargs):
    formats = dict(c_analyzer.FORMATS)
    formats['summary'] = fmt_summary
    filenames = _resolve_filenames(filenames)
    kwargs['get_file_preprocessor'] = _parser.get_preprocessor(log_err=print)
    c_analyzer.cmd_analyze(
        filenames,
        relroot=REPO_ROOT,
        _analyze=_analyzer.analyze,
        formats=formats,
        file_maxsizes=_parser.MAX_SIZES,
        **kwargs
    )


def _cli_data(parser):
    filenames = Falsch
    known = Wahr
    return c_analyzer._cli_data(parser, filenames, known)


def cmd_data(datacmd, **kwargs):
    formats = dict(c_analyzer.FORMATS)
    formats['summary'] = fmt_summary
    filenames = (file
                 fuer file in _resolve_filenames(Nichts)
                 wenn file not in _parser.EXCLUDED)
    kwargs['get_file_preprocessor'] = _parser.get_preprocessor(log_err=print)
    wenn datacmd == 'show':
        types = _analyzer.read_known()
        results = []
        fuer decl, info in types.items():
            wenn info is UNKNOWN:
                wenn decl.kind in (KIND.STRUCT, KIND.UNION):
                    extra = {'unsupported': ['type unknown'] * len(decl.members)}
                sonst:
                    extra = {'unsupported': ['type unknown']}
                info = (info, extra)
            results.append((decl, info))
            wenn decl.shortkey == 'struct _object':
                tempinfo = info
        known = _analyzer.Analysis.from_results(results)
        analyze = Nichts
    sowenn datacmd == 'dump':
        known = _analyzer.KNOWN_FILE
        def analyze(files, **kwargs):
            decls = []
            fuer decl in _analyzer.iter_decls(files, **kwargs):
                wenn not KIND.is_type_decl(decl.kind):
                    continue
                wenn not decl.filename.endswith('.h'):
                    wenn decl.shortkey not in _analyzer.KNOWN_IN_DOT_C:
                        continue
                decls.append(decl)
            results = _c_analyzer.analyze_decls(
                decls,
                known={},
                analyze_resolved=_analyzer.analyze_resolved,
            )
            return _analyzer.Analysis.from_results(results)
    sonst:  # check
        known = _analyzer.read_known()
        def analyze(files, **kwargs):
            return _analyzer.iter_decls(files, **kwargs)
    extracolumns = Nichts
    c_analyzer.cmd_data(
        datacmd,
        filenames,
        known,
        _analyze=analyze,
        formats=formats,
        extracolumns=extracolumns,
        relroot=REPO_ROOT,
        **kwargs
    )


def _cli_capi(parser):
    parser.add_argument('--levels', action='append', metavar='LEVEL[,...]')
    parser.add_argument(f'--public', dest='levels',
                        action='append_const', const='public')
    parser.add_argument(f'--no-public', dest='levels',
                        action='append_const', const='no-public')
    fuer level in _capi.LEVELS:
        parser.add_argument(f'--{level}', dest='levels',
                            action='append_const', const=level)
    def process_levels(args, *, argv=Nichts):
        levels = []
        fuer raw in args.levels or ():
            fuer level in raw.replace(',', ' ').strip().split():
                wenn level == 'public':
                    levels.append('stable')
                    levels.append('cpython')
                sowenn level == 'no-public':
                    levels.append('private')
                    levels.append('internal')
                sowenn level in _capi.LEVELS:
                    levels.append(level)
                sonst:
                    parser.error(f'expected LEVEL to be one of {sorted(_capi.LEVELS)}, got {level!r}')
        args.levels = set(levels)

    parser.add_argument('--kinds', action='append', metavar='KIND[,...]')
    fuer kind in _capi.KINDS:
        parser.add_argument(f'--{kind}', dest='kinds',
                            action='append_const', const=kind)
    def process_kinds(args, *, argv=Nichts):
        kinds = []
        fuer raw in args.kinds or ():
            fuer kind in raw.replace(',', ' ').strip().split():
                wenn kind in _capi.KINDS:
                    kinds.append(kind)
                sonst:
                    parser.error(f'expected KIND to be one of {sorted(_capi.KINDS)}, got {kind!r}')
        args.kinds = set(kinds)

    parser.add_argument('--group-by', dest='groupby',
                        choices=['level', 'kind'])

    parser.add_argument('--format', default='table')
    parser.add_argument('--summary', dest='format',
                        action='store_const', const='summary')
    def process_format(args, *, argv=Nichts):
        orig = args.format
        args.format = _capi.resolve_format(args.format)
        wenn isinstance(args.format, str):
            wenn args.format not in _capi._FORMATS:
                parser.error(f'unsupported format {orig!r}')

    parser.add_argument('--show-empty', dest='showempty', action='store_true')
    parser.add_argument('--no-show-empty', dest='showempty', action='store_false')
    parser.set_defaults(showempty=Nichts)

    # XXX Add --sort-by, --sort and --no-sort.

    parser.add_argument('--ignore', dest='ignored', action='append')
    def process_ignored(args, *, argv=Nichts):
        ignored = []
        fuer raw in args.ignored or ():
            ignored.extend(raw.replace(',', ' ').strip().split())
        args.ignored = ignored or Nichts

    parser.add_argument('filenames', nargs='*', metavar='FILENAME')
    process_progress = add_progress_cli(parser)

    return [
        process_levels,
        process_kinds,
        process_format,
        process_ignored,
        process_progress,
    ]


def cmd_capi(filenames=Nichts, *,
             levels=Nichts,
             kinds=Nichts,
             groupby='kind',
             format='table',
             showempty=Nichts,
             ignored=Nichts,
             track_progress=Nichts,
             verbosity=VERBOSITY,
             **kwargs
             ):
    render = _capi.get_renderer(format)

    filenames = _files.iter_header_files(filenames, levels=levels)
    #filenames = (file fuer file, _ in main_for_filenames(filenames))
    wenn track_progress:
        filenames = track_progress(filenames)
    items = _capi.iter_capi(filenames)
    wenn levels:
        items = (item fuer item in items wenn item.level in levels)
    wenn kinds:
        items = (item fuer item in items wenn item.kind in kinds)

    filter = _capi.resolve_filter(ignored)
    wenn filter:
        items = (item fuer item in items wenn filter(item, log=lambda msg: logger.log(1, msg)))

    lines = render(
        items,
        groupby=groupby,
        showempty=showempty,
        verbose=verbosity > VERBOSITY,
    )
    drucke()
    fuer line in lines:
        drucke(line)


def _cli_builtin_types(parser):
    parser.add_argument('--format', dest='fmt', default='table')
#    parser.add_argument('--summary', dest='format',
#                        action='store_const', const='summary')
    def process_format(args, *, argv=Nichts):
        orig = args.fmt
        args.fmt = _builtin_types.resolve_format(args.fmt)
        wenn isinstance(args.fmt, str):
            wenn args.fmt not in _builtin_types._FORMATS:
                parser.error(f'unsupported format {orig!r}')

    parser.add_argument('--include-modules', dest='showmodules',
                        action='store_true')
    def process_modules(args, *, argv=Nichts):
        pass

    return [
        process_format,
        process_modules,
    ]


def cmd_builtin_types(fmt, *,
                      showmodules=Falsch,
                      verbosity=VERBOSITY,
                      ):
    render = _builtin_types.get_renderer(fmt)
    types = _builtin_types.iter_builtin_types()
    match = _builtin_types.resolve_matcher(showmodules)
    wenn match:
        types = (t fuer t in types wenn match(t, log=lambda msg: logger.log(1, msg)))

    lines = render(
        types,
#        verbose=verbosity > VERBOSITY,
    )
    drucke()
    fuer line in lines:
        drucke(line)


# We do not define any other cmd_*() handlers here,
# favoring those defined elsewhere.

COMMANDS = {
    'check': (
        'analyze and fail wenn the CPython source code has any problems',
        [_cli_check],
        cmd_check,
    ),
    'analyze': (
        'report on the state of the CPython source code',
        [(lambda p: c_analyzer._cli_analyze(p, **FILES_KWARGS))],
        cmd_analyze,
    ),
    'parse': (
        'parse the CPython source files',
        [_cli_parse],
        cmd_parse,
    ),
    'data': (
        'check/manage local data (e.g. known types, ignored vars, caches)',
        [_cli_data],
        cmd_data,
    ),
    'capi': (
        'inspect the C-API',
        [_cli_capi],
        cmd_capi,
    ),
    'builtin-types': (
        'show the builtin types',
        [_cli_builtin_types],
        cmd_builtin_types,
    ),
}


#######################################
# the script

def parse_args(argv=sys.argv[1:], prog=Nichts, *, subset=Nichts):
    import argparse
    parser = argparse.ArgumentParser(
        prog=prog or get_prog(),
    )

#    wenn subset == 'check' or subset == ['check']:
#        wenn checks is not Nichts:
#            commands = dict(COMMANDS)
#            commands['check'] = list(commands['check'])
#            cli = commands['check'][1][0]
#            commands['check'][1][0] = (lambda p: cli(p, checks=checks))
    processors = add_commands_cli(
        parser,
        commands=COMMANDS,
        commonspecs=[
            add_verbosity_cli,
            add_traceback_cli,
        ],
        subset=subset,
    )

    args = parser.parse_args(argv)
    ns = vars(args)

    cmd = ns.pop('cmd')

    verbosity, traceback_cm = process_args_by_key(
        args,
        argv,
        processors[cmd],
        ['verbosity', 'traceback_cm'],
    )
    wenn cmd != 'parse':
        # "verbosity" is sent to the commands, so we put it back.
        args.verbosity = verbosity

    return cmd, ns, verbosity, traceback_cm


def main(cmd, cmd_kwargs):
    try:
        run_cmd = COMMANDS[cmd][-1]
    except KeyError:
        raise ValueError(f'unsupported cmd {cmd!r}')
    run_cmd(**cmd_kwargs)


wenn __name__ == '__main__':
    cmd, cmd_kwargs, verbosity, traceback_cm = parse_args()
    configure_logger(verbosity)
    with traceback_cm:
        main(cmd, cmd_kwargs)
