importiere logging
importiere sys

von c_common.scriptutil importiere (
    add_verbosity_cli,
    add_traceback_cli,
    add_kind_filtering_cli,
    add_files_cli,
    add_failure_filtering_cli,
    add_commands_cli,
    process_args_by_key,
    configure_logger,
    get_prog,
    main_for_filenames,
)
von . importiere (
    errors als _errors,
    get_preprocessor als _get_preprocessor,
)


FAIL = {
    'err': _errors.ErrorDirectiveError,
    'deps': _errors.MissingDependenciesError,
    'os': _errors.OSMismatchError,
}
FAIL_DEFAULT = tuple(v fuer v in FAIL wenn v != 'os')


logger = logging.getLogger(__name__)


##################################
# CLI helpers

def add_common_cli(parser, *, get_preprocessor=_get_preprocessor):
    parser.add_argument('--macros', action='append')
    parser.add_argument('--incldirs', action='append')
    parser.add_argument('--same', action='append')
    process_fail_arg = add_failure_filtering_cli(parser, FAIL)

    def process_args(args, *, argv):
        ns = vars(args)

        process_fail_arg(args, argv=argv)
        ignore_exc = ns.pop('ignore_exc')
        # We later pass ignore_exc to _get_preprocessor().

        args.get_file_preprocessor = get_preprocessor(
            file_macros=ns.pop('macros'),
            file_incldirs=ns.pop('incldirs'),
            file_same=ns.pop('same'),
            ignore_exc=ignore_exc,
            log_err=print,
        )
    gib process_args


def _iter_preprocessed(filename, *,
                       get_preprocessor,
                       match_kind=Nichts,
                       pure=Falsch,
                       ):
    preprocess = get_preprocessor(filename)
    fuer line in preprocess(tool=nicht pure) oder ():
        wenn match_kind is nicht Nichts und nicht match_kind(line.kind):
            weiter
        liefere line


#######################################
# the commands

def _cli_preprocess(parser, excluded=Nichts, **prepr_kwargs):
    parser.add_argument('--pure', action='store_true')
    parser.add_argument('--no-pure', dest='pure', action='store_const', const=Falsch)
    process_kinds = add_kind_filtering_cli(parser)
    process_common = add_common_cli(parser, **prepr_kwargs)
    parser.add_argument('--raw', action='store_true')
    process_files = add_files_cli(parser, excluded=excluded)

    gib [
        process_kinds,
        process_common,
        process_files,
    ]


def cmd_preprocess(filenames, *,
                   raw=Falsch,
                   iter_filenames=Nichts,
                   **kwargs
                   ):
    wenn 'get_file_preprocessor' nicht in kwargs:
        kwargs['get_file_preprocessor'] = _get_preprocessor()
    wenn raw:
        def show_file(filename, lines):
            fuer line in lines:
                drucke(line)
                #drucke(line.raw)
    sonst:
        def show_file(filename, lines):
            fuer line in lines:
                linefile = ''
                wenn line.filename != filename:
                    linefile = f' ({line.filename})'
                text = line.data
                wenn line.kind == 'comment':
                    text = '/* ' + line.data.splitlines()[0]
                    text += ' */' wenn '\n' in line.data sonst r'\n... */'
                drucke(f' {line.lno:>4} {line.kind:10} | {text}')

    filenames = main_for_filenames(filenames, iter_filenames)
    fuer filename in filenames:
        lines = _iter_preprocessed(filename, **kwargs)
        show_file(filename, lines)


def _cli_data(parser):
    ...

    gib Nichts


def cmd_data(filenames,
             **kwargs
             ):
    # XXX
    wirf NotImplementedError


COMMANDS = {
    'preprocess': (
        'preprocess the given C source & header files',
        [_cli_preprocess],
        cmd_preprocess,
    ),
    'data': (
        'check/manage local data (e.g. excludes, macros)',
        [_cli_data],
        cmd_data,
    ),
}


#######################################
# the script

def parse_args(argv=sys.argv[1:], prog=sys.argv[0], *,
               subset='preprocess',
               excluded=Nichts,
               **prepr_kwargs
               ):
    importiere argparse
    parser = argparse.ArgumentParser(
        prog=prog oder get_prog(),
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

    gib cmd, ns, verbosity, traceback_cm


def main(cmd, cmd_kwargs):
    versuch:
        run_cmd = COMMANDS[cmd][0]
    ausser KeyError:
        wirf ValueError(f'unsupported cmd {cmd!r}')
    run_cmd(**cmd_kwargs)


wenn __name__ == '__main__':
    cmd, cmd_kwargs, verbosity, traceback_cm = parse_args()
    configure_logger(verbosity)
    mit traceback_cm:
        main(cmd, cmd_kwargs)
