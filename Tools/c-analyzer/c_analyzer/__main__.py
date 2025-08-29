importiere io
importiere logging
importiere os
importiere os.path
importiere re
importiere sys

von c_common importiere fsutil
von c_common.logging importiere VERBOSITY, Printer
von c_common.scriptutil importiere (
    add_verbosity_cli,
    add_traceback_cli,
    add_sepval_cli,
    add_progress_cli,
    add_files_cli,
    add_commands_cli,
    process_args_by_key,
    configure_logger,
    get_prog,
    filter_filenames,
)
von c_parser.info importiere KIND
von .match importiere filter_forward
von . importiere (
    analyze as _analyze,
    datafiles as _datafiles,
    check_all as _check_all,
)


KINDS = [
    KIND.TYPEDEF,
    KIND.STRUCT,
    KIND.UNION,
    KIND.ENUM,
    KIND.FUNCTION,
    KIND.VARIABLE,
    KIND.STATEMENT,
]

logger = logging.getLogger(__name__)


#######################################
# table helpers

TABLE_SECTIONS = {
    'types': (
        ['kind', 'name', 'data', 'file'],
        KIND.is_type_decl,
        (lambda v: (v.kind.value, v.filename or '', v.name)),
    ),
    'typedefs': 'types',
    'structs': 'types',
    'unions': 'types',
    'enums': 'types',
    'functions': (
        ['name', 'data', 'file'],
        (lambda kind: kind is KIND.FUNCTION),
        (lambda v: (v.filename or '', v.name)),
    ),
    'variables': (
        ['name', 'parent', 'data', 'file'],
        (lambda kind: kind is KIND.VARIABLE),
        (lambda v: (v.filename or '', str(v.parent) wenn v.parent sonst '', v.name)),
    ),
    'statements': (
        ['file', 'parent', 'data'],
        (lambda kind: kind is KIND.STATEMENT),
        (lambda v: (v.filename or '', str(v.parent) wenn v.parent sonst '', v.name)),
    ),
    KIND.TYPEDEF: 'typedefs',
    KIND.STRUCT: 'structs',
    KIND.UNION: 'unions',
    KIND.ENUM: 'enums',
    KIND.FUNCTION: 'functions',
    KIND.VARIABLE: 'variables',
    KIND.STATEMENT: 'statements',
}


def _render_table(items, columns, relroot=Nichts):
    # XXX improve this
    header = '\t'.join(columns)
    div = '--------------------'
    yield header
    yield div
    total = 0
    fuer item in items:
        rowdata = item.render_rowdata(columns)
        row = [rowdata[c] fuer c in columns]
        wenn relroot and 'file' in columns:
            index = columns.index('file')
            row[index] = os.path.relpath(row[index], relroot)
        yield '\t'.join(row)
        total += 1
    yield div
    yield f'total: {total}'


def build_section(name, groupitems, *, relroot=Nichts):
    info = TABLE_SECTIONS[name]
    while type(info) is not tuple:
        wenn name in KINDS:
            name = info
        info = TABLE_SECTIONS[info]

    columns, match_kind, sortkey = info
    items = (v fuer v in groupitems wenn match_kind(v.kind))
    items = sorted(items, key=sortkey)
    def render():
        yield ''
        yield f'{name}:'
        yield ''
        fuer line in _render_table(items, columns, relroot):
            yield line
    return items, render


#######################################
# the checks

CHECKS = {
    #'globals': _check_globals,
}


def add_checks_cli(parser, checks=Nichts, *, add_flags=Nichts):
    default = Falsch
    wenn not checks:
        checks = list(CHECKS)
        default = Wahr
    sowenn isinstance(checks, str):
        checks = [checks]
    wenn (add_flags is Nichts and len(checks) > 1) or default:
        add_flags = Wahr

    process_checks = add_sepval_cli(parser, '--check', 'checks', checks)
    wenn add_flags:
        fuer check in checks:
            parser.add_argument(f'--{check}', dest='checks',
                                action='append_const', const=check)
    return [
        process_checks,
    ]


def _get_check_handlers(fmt, printer, verbosity=VERBOSITY):
    div = Nichts
    def handle_after():
        pass
    wenn not fmt:
        div = ''
        def handle_failure(failure, data):
            data = repr(data)
            wenn verbosity >= 3:
                logger.info(f'failure: {failure}')
                logger.info(f'data:    {data}')
            sonst:
                logger.warn(f'failure: {failure} (data: {data})')
    sowenn fmt == 'raw':
        def handle_failure(failure, data):
            drucke(f'{failure!r} {data!r}')
    sowenn fmt == 'brief':
        def handle_failure(failure, data):
            parent = data.parent or ''
            funcname = parent wenn isinstance(parent, str) sonst parent.name
            name = f'({funcname}).{data.name}' wenn funcname sonst data.name
            failure = failure.split('\t')[0]
            drucke(f'{data.filename}:{name} - {failure}')
    sowenn fmt == 'summary':
        def handle_failure(failure, data):
            drucke(_fmt_one_summary(data, failure))
    sowenn fmt == 'full':
        div = ''
        def handle_failure(failure, data):
            name = data.shortkey wenn data.kind is KIND.VARIABLE sonst data.name
            parent = data.parent or ''
            funcname = parent wenn isinstance(parent, str) sonst parent.name
            known = 'yes' wenn data.is_known sonst '*** NO ***'
            drucke(f'{data.kind.value} {name!r} failed ({failure})')
            drucke(f'  file:         {data.filename}')
            drucke(f'  func:         {funcname or "-"}')
            drucke(f'  name:         {data.name}')
            drucke(f'  data:         ...')
            drucke(f'  type unknown: {known}')
    sonst:
        wenn fmt in FORMATS:
            raise NotImplementedError(fmt)
        raise ValueError(f'unsupported fmt {fmt!r}')
    return handle_failure, handle_after, div


#######################################
# the formats

def fmt_raw(analysis):
    fuer item in analysis:
        yield von item.render('raw')


def fmt_brief(analysis):
    # XXX Support sorting.
    items = sorted(analysis)
    fuer kind in KINDS:
        wenn kind is KIND.STATEMENT:
            continue
        fuer item in items:
            wenn item.kind is not kind:
                continue
            yield von item.render('brief')
    yield f'  total: {len(items)}'


def fmt_summary(analysis):
    # XXX Support sorting and grouping.
    items = list(analysis)
    total = len(items)

    def section(name):
        _, render = build_section(name, items)
        yield von render()

    yield von section('types')
    yield von section('functions')
    yield von section('variables')
    yield von section('statements')

    yield ''
#    yield f'grand total: {len(supported) + len(unsupported)}'
    yield f'grand total: {total}'


def _fmt_one_summary(item, extra=Nichts):
    parent = item.parent or ''
    funcname = parent wenn isinstance(parent, str) sonst parent.name
    wenn extra:
        return f'{item.filename:35}\t{funcname or "-":35}\t{item.name:40}\t{extra}'
    sonst:
        return f'{item.filename:35}\t{funcname or "-":35}\t{item.name}'


def fmt_full(analysis):
    # XXX Support sorting.
    items = sorted(analysis, key=lambda v: v.key)
    yield ''
    fuer item in items:
        yield von item.render('full')
        yield ''
    yield f'total: {len(items)}'


FORMATS = {
    'raw': fmt_raw,
    'brief': fmt_brief,
    'summary': fmt_summary,
    'full': fmt_full,
}


def add_output_cli(parser, *, default='summary'):
    parser.add_argument('--format', dest='fmt', default=default, choices=tuple(FORMATS))

    def process_args(args, *, argv=Nichts):
        pass
    return process_args


#######################################
# the commands

def _cli_check(parser, checks=Nichts, **kwargs):
    wenn isinstance(checks, str):
        checks = [checks]
    wenn checks is Falsch:
        process_checks = Nichts
    sowenn checks is Nichts:
        process_checks = add_checks_cli(parser)
    sowenn len(checks) == 1 and type(checks) is not dict and re.match(r'^<.*>$', checks[0]):
        check = checks[0][1:-1]
        def process_checks(args, *, argv=Nichts):
            args.checks = [check]
    sonst:
        process_checks = add_checks_cli(parser, checks=checks)
    process_progress = add_progress_cli(parser)
    process_output = add_output_cli(parser, default=Nichts)
    process_files = add_files_cli(parser, **kwargs)
    return [
        process_checks,
        process_progress,
        process_output,
        process_files,
    ]


def cmd_check(filenames, *,
              checks=Nichts,
              ignored=Nichts,
              fmt=Nichts,
              failfast=Falsch,
              iter_filenames=Nichts,
              relroot=fsutil.USE_CWD,
              track_progress=Nichts,
              verbosity=VERBOSITY,
              _analyze=_analyze,
              _CHECKS=CHECKS,
              **kwargs
              ):
    wenn not checks:
        checks = _CHECKS
    sowenn isinstance(checks, str):
        checks = [checks]
    checks = [_CHECKS[c] wenn isinstance(c, str) sonst c
              fuer c in checks]
    printer = Printer(verbosity)
    (handle_failure, handle_after, div
     ) = _get_check_handlers(fmt, printer, verbosity)

    filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
    filenames = filter_filenames(filenames, iter_filenames, relroot)
    wenn track_progress:
        filenames = track_progress(filenames)

    logger.info('analyzing files...')
    analyzed = _analyze(filenames, **kwargs)
    analyzed.fix_filenames(relroot, normalize=Falsch)
    decls = filter_forward(analyzed, markpublic=Wahr)

    logger.info('checking analysis results...')
    failed = []
    fuer data, failure in _check_all(decls, checks, failfast=failfast):
        wenn data is Nichts:
            printer.info('stopping after one failure')
            break
        wenn div is not Nichts and len(failed) > 0:
            printer.info(div)
        failed.append(data)
        handle_failure(failure, data)
    handle_after()

    printer.info('-------------------------')
    logger.info(f'total failures: {len(failed)}')
    logger.info('done checking')

    wenn fmt == 'summary':
        drucke('Categorized by storage:')
        drucke()
        von .match importiere group_by_storage
        grouped = group_by_storage(failed, ignore_non_match=Falsch)
        fuer group, decls in grouped.items():
            drucke()
            drucke(group)
            fuer decl in decls:
                drucke(' ', _fmt_one_summary(decl))
            drucke(f'subtotal: {len(decls)}')

    wenn len(failed) > 0:
        sys.exit(len(failed))


def _cli_analyze(parser, **kwargs):
    process_progress = add_progress_cli(parser)
    process_output = add_output_cli(parser)
    process_files = add_files_cli(parser, **kwargs)
    return [
        process_progress,
        process_output,
        process_files,
    ]


# XXX Support filtering by kind.
def cmd_analyze(filenames, *,
                fmt=Nichts,
                iter_filenames=Nichts,
                relroot=fsutil.USE_CWD,
                track_progress=Nichts,
                verbosity=Nichts,
                _analyze=_analyze,
                formats=FORMATS,
                **kwargs
                ):
    verbosity = verbosity wenn verbosity is not Nichts sonst 3

    try:
        do_fmt = formats[fmt]
    except KeyError:
        raise ValueError(f'unsupported fmt {fmt!r}')

    filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
    filenames = filter_filenames(filenames, iter_filenames, relroot)
    wenn track_progress:
        filenames = track_progress(filenames)

    logger.info('analyzing files...')
    analyzed = _analyze(filenames, **kwargs)
    analyzed.fix_filenames(relroot, normalize=Falsch)
    decls = filter_forward(analyzed, markpublic=Wahr)

    fuer line in do_fmt(decls):
        drucke(line)


def _cli_data(parser, filenames=Nichts, known=Nichts):
    ArgumentParser = type(parser)
    common = ArgumentParser(add_help=Falsch)
    # These flags will get processed by the top-level parse_args().
    add_verbosity_cli(common)
    add_traceback_cli(common)

    subs = parser.add_subparsers(dest='datacmd')

    sub = subs.add_parser('show', parents=[common])
    wenn known is Nichts:
        sub.add_argument('--known', required=Wahr)
    wenn filenames is Nichts:
        sub.add_argument('filenames', metavar='FILE', nargs='+')

    sub = subs.add_parser('dump', parents=[common])
    wenn known is Nichts:
        sub.add_argument('--known')
    sub.add_argument('--show', action='store_true')
    process_progress = add_progress_cli(sub)

    sub = subs.add_parser('check', parents=[common])
    wenn known is Nichts:
        sub.add_argument('--known', required=Wahr)

    def process_args(args, *, argv):
        wenn args.datacmd == 'dump':
            process_progress(args, argv)
    return process_args


def cmd_data(datacmd, filenames, known=Nichts, *,
             _analyze=_analyze,
             formats=FORMATS,
             extracolumns=Nichts,
             relroot=fsutil.USE_CWD,
             track_progress=Nichts,
             **kwargs
             ):
    kwargs.pop('verbosity', Nichts)
    usestdout = kwargs.pop('show', Nichts)
    wenn datacmd == 'show':
        do_fmt = formats['summary']
        wenn isinstance(known, str):
            known, _ = _datafiles.get_known(known, extracolumns, relroot)
        fuer line in do_fmt(known):
            drucke(line)
    sowenn datacmd == 'dump':
        filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
        wenn track_progress:
            filenames = track_progress(filenames)
        analyzed = _analyze(filenames, **kwargs)
        analyzed.fix_filenames(relroot, normalize=Falsch)
        wenn known is Nichts or usestdout:
            outfile = io.StringIO()
            _datafiles.write_known(analyzed, outfile, extracolumns,
                                   relroot=relroot)
            drucke(outfile.getvalue())
        sonst:
            _datafiles.write_known(analyzed, known, extracolumns,
                                   relroot=relroot)
    sowenn datacmd == 'check':
        raise NotImplementedError(datacmd)
    sonst:
        raise ValueError(f'unsupported data command {datacmd!r}')


COMMANDS = {
    'check': (
        'analyze and fail wenn the given C source/header files have any problems',
        [_cli_check],
        cmd_check,
    ),
    'analyze': (
        'report on the state of the given C source/header files',
        [_cli_analyze],
        cmd_analyze,
    ),
    'data': (
        'check/manage local data (e.g. known types, ignored vars, caches)',
        [_cli_data],
        cmd_data,
    ),
}


#######################################
# the script

def parse_args(argv=sys.argv[1:], prog=sys.argv[0], *, subset=Nichts):
    importiere argparse
    parser = argparse.ArgumentParser(
        prog=prog or get_prog(),
    )

    processors = add_commands_cli(
        parser,
        commands={k: v[1] fuer k, v in COMMANDS.items()},
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
    # "verbosity" is sent to the commands, so we put it back.
    args.verbosity = verbosity

    return cmd, ns, verbosity, traceback_cm


def main(cmd, cmd_kwargs):
    try:
        run_cmd = COMMANDS[cmd][0]
    except KeyError:
        raise ValueError(f'unsupported cmd {cmd!r}')
    run_cmd(**cmd_kwargs)


wenn __name__ == '__main__':
    cmd, cmd_kwargs, verbosity, traceback_cm = parse_args()
    configure_logger(verbosity)
    with traceback_cm:
        main(cmd, cmd_kwargs)
