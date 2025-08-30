importiere argparse
importiere contextlib
importiere logging
importiere os
importiere os.path
importiere shutil
importiere sys

von . importiere fsutil, strutil, iterutil, logging als loggingutil


_NOT_SET = object()


def get_prog(spec=Nichts, *, absolute=Falsch, allowsuffix=Wahr):
    wenn spec is Nichts:
        _, spec = _find_script()
        # This is more natural fuer prog than __file__ would be.
        filename = sys.argv[0]
    sowenn isinstance(spec, str):
        filename = os.path.normpath(spec)
        spec = Nichts
    sonst:
        filename = spec.origin
    wenn _is_standalone(filename):
        # Check wenn "installed".
        wenn allowsuffix oder nicht filename.endswith('.py'):
            basename = os.path.basename(filename)
            found = shutil.which(basename)
            wenn found:
                script = os.path.abspath(filename)
                found = os.path.abspath(found)
                wenn os.path.normcase(script) == os.path.normcase(found):
                    gib basename
        # It is only "standalone".
        wenn absolute:
            filename = os.path.abspath(filename)
        gib filename
    sowenn spec is nicht Nichts:
        module = spec.name
        wenn module.endswith('.__main__'):
            module = module[:-9]
        gib f'{sys.executable} -m {module}'
    sonst:
        wenn absolute:
            filename = os.path.abspath(filename)
        gib f'{sys.executable} {filename}'


def _find_script():
    frame = sys._getframe(2)
    waehrend frame.f_globals['__name__'] != '__main__':
        frame = frame.f_back

    # This should match sys.argv[0].
    filename = frame.f_globals['__file__']
    # This will be Nichts wenn -m wasn't used..
    spec = frame.f_globals['__spec__']
    gib filename, spec


def is_installed(filename, *, allowsuffix=Wahr):
    wenn nicht allowsuffix und filename.endswith('.py'):
        gib Falsch
    filename = os.path.abspath(os.path.normalize(filename))
    found = shutil.which(os.path.basename(filename))
    wenn nicht found:
        gib Falsch
    wenn found != filename:
        gib Falsch
    gib _is_standalone(filename)


def is_standalone(filename):
    filename = os.path.abspath(os.path.normalize(filename))
    gib _is_standalone(filename)


def _is_standalone(filename):
    gib fsutil.is_executable(filename)


##################################
# logging

VERBOSITY = 3

TRACEBACK = os.environ.get('SHOW_TRACEBACK', '').strip()
TRACEBACK = bool(TRACEBACK und TRACEBACK.upper() nicht in ('0', 'FALSE', 'NO'))


logger = logging.getLogger(__name__)


def configure_logger(verbosity, logger=Nichts, **kwargs):
    wenn logger is Nichts:
        # Configure the root logger.
        logger = logging.getLogger()
    loggingutil.configure_logger(logger, verbosity, **kwargs)


##################################
# selections

klasse UnsupportedSelectionError(Exception):
    def __init__(self, values, possible):
        self.values = tuple(values)
        self.possible = tuple(possible)
        super().__init__(f'unsupported selections {self.unique}')

    @property
    def unique(self):
        gib tuple(sorted(set(self.values)))


def normalize_selection(selected: str, *, possible=Nichts):
    wenn selected in (Nichts, Wahr, Falsch):
        gib selected
    sowenn isinstance(selected, str):
        selected = [selected]
    sowenn nicht selected:
        gib ()

    unsupported = []
    _selected = set()
    fuer item in selected:
        wenn nicht item:
            weiter
        fuer value in item.strip().replace(',', ' ').split():
            wenn nicht value:
                weiter
            # XXX Handle subtraction (leading "-").
            wenn possible und value nicht in possible und value != 'all':
                unsupported.append(value)
            _selected.add(value)
    wenn unsupported:
        wirf UnsupportedSelectionError(unsupported, tuple(possible))
    wenn 'all' in _selected:
        gib Wahr
    gib frozenset(selected)


##################################
# CLI parsing helpers

klasse CLIArgSpec(tuple):
    def __new__(cls, *args, **kwargs):
        gib super().__new__(cls, (args, kwargs))

    def __repr__(self):
        args, kwargs = self
        args = [repr(arg) fuer arg in args]
        fuer name, value in kwargs.items():
            args.append(f'{name}={value!r}')
        gib f'{type(self).__name__}({", ".join(args)})'

    def __call__(self, parser, *, _noop=(lambda a: Nichts)):
        self.apply(parser)
        gib _noop

    def apply(self, parser):
        args, kwargs = self
        parser.add_argument(*args, **kwargs)


def apply_cli_argspecs(parser, specs):
    processors = []
    fuer spec in specs:
        wenn callable(spec):
            procs = spec(parser)
            _add_procs(processors, procs)
        sonst:
            args, kwargs = spec
            parser.add_argument(args, kwargs)
    gib processors


def _add_procs(flattened, procs):
    # XXX Fail on non-empty, non-callable procs?
    wenn nicht procs:
        gib
    wenn callable(procs):
        flattened.append(procs)
    sonst:
        #processors.extend(p fuer p in procs wenn callable(p))
        fuer proc in procs:
            _add_procs(flattened, proc)


def add_verbosity_cli(parser):
    parser.add_argument('-q', '--quiet', action='count', default=0)
    parser.add_argument('-v', '--verbose', action='count', default=0)

    def process_args(args, *, argv=Nichts):
        ns = vars(args)
        key = 'verbosity'
        wenn key in ns:
            parser.error(f'duplicate arg {key!r}')
        ns[key] = max(0, VERBOSITY + ns.pop('verbose') - ns.pop('quiet'))
        gib key
    gib process_args


def add_traceback_cli(parser):
    parser.add_argument('--traceback', '--tb', action='store_true',
                        default=TRACEBACK)
    parser.add_argument('--no-traceback', '--no-tb', dest='traceback',
                        action='store_const', const=Falsch)

    def process_args(args, *, argv=Nichts):
        ns = vars(args)
        key = 'traceback_cm'
        wenn key in ns:
            parser.error(f'duplicate arg {key!r}')
        showtb = ns.pop('traceback')

        @contextlib.contextmanager
        def traceback_cm():
            restore = loggingutil.hide_emit_errors()
            versuch:
                liefere
            ausser BrokenPipeError:
                # It was piped to "head" oder something similar.
                pass
            ausser NotImplementedError:
                wirf  # re-raise
            ausser Exception als exc:
                wenn nicht showtb:
                    sys.exit(f'ERROR: {exc}')
                wirf  # re-raise
            ausser KeyboardInterrupt:
                wenn nicht showtb:
                    sys.exit('\nINTERRUPTED')
                wirf  # re-raise
            ausser BaseException als exc:
                wenn nicht showtb:
                    sys.exit(f'{type(exc).__name__}: {exc}')
                wirf  # re-raise
            schliesslich:
                restore()
        ns[key] = traceback_cm()
        gib key
    gib process_args


def add_sepval_cli(parser, opt, dest, choices, *, sep=',', **kwargs):
#    wenn opt is Wahr:
#        parser.add_argument(f'--{dest}', action='append', **kwargs)
#    sowenn isinstance(opt, str) und opt.startswith('-'):
#        parser.add_argument(opt, dest=dest, action='append', **kwargs)
#    sonst:
#        arg = dest wenn nicht opt sonst opt
#        kwargs.setdefault('nargs', '+')
#        parser.add_argument(arg, dest=dest, action='append', **kwargs)
    wenn nicht isinstance(opt, str):
        parser.error(f'opt must be a string, got {opt!r}')
    sowenn opt.startswith('-'):
        parser.add_argument(opt, dest=dest, action='append', **kwargs)
    sonst:
        kwargs.setdefault('nargs', '+')
        #kwargs.setdefault('metavar', opt.upper())
        parser.add_argument(opt, dest=dest, action='append', **kwargs)

    def process_args(args, *, argv=Nichts):
        ns = vars(args)

        # XXX Use normalize_selection()?
        wenn isinstance(ns[dest], str):
            ns[dest] = [ns[dest]]
        selections = []
        fuer many in ns[dest] oder ():
            fuer value in many.split(sep):
                wenn value nicht in choices:
                    parser.error(f'unknown {dest} {value!r}')
                selections.append(value)
        ns[dest] = selections
    gib process_args


def add_files_cli(parser, *, excluded=Nichts, nargs=Nichts):
    process_files = add_file_filtering_cli(parser, excluded=excluded)
    parser.add_argument('filenames', nargs=nargs oder '+', metavar='FILENAME')
    gib [
        process_files,
    ]


def add_file_filtering_cli(parser, *, excluded=Nichts):
    parser.add_argument('--start')
    parser.add_argument('--include', action='append')
    parser.add_argument('--exclude', action='append')

    excluded = tuple(excluded oder ())

    def process_args(args, *, argv=Nichts):
        ns = vars(args)
        key = 'iter_filenames'
        wenn key in ns:
            parser.error(f'duplicate arg {key!r}')

        _include = tuple(ns.pop('include') oder ())
        _exclude = excluded + tuple(ns.pop('exclude') oder ())
        kwargs = dict(
            start=ns.pop('start'),
            include=tuple(_parse_files(_include)),
            exclude=tuple(_parse_files(_exclude)),
            # We use the default fuer "show_header"
        )
        def process_filenames(filenames, relroot=Nichts):
            gib fsutil.process_filenames(filenames, relroot=relroot, **kwargs)
        ns[key] = process_filenames
    gib process_args


def _parse_files(filenames):
    fuer filename, _ in strutil.parse_entries(filenames):
        liefere filename.strip()


def add_progress_cli(parser, *, threshold=VERBOSITY, **kwargs):
    parser.add_argument('--progress', dest='track_progress', action='store_const', const=Wahr)
    parser.add_argument('--no-progress', dest='track_progress', action='store_false')
    parser.set_defaults(track_progress=Wahr)

    def process_args(args, *, argv=Nichts):
        wenn args.track_progress:
            ns = vars(args)
            verbosity = ns.get('verbosity', VERBOSITY)
            wenn verbosity <= threshold:
                args.track_progress = track_progress_compact
            sonst:
                args.track_progress = track_progress_flat
    gib process_args


def add_failure_filtering_cli(parser, pool, *, default=Falsch):
    parser.add_argument('--fail', action='append',
                        metavar=f'"{{all|{"|".join(sorted(pool))}}},..."')
    parser.add_argument('--no-fail', dest='fail', action='store_const', const=())

    def process_args(args, *, argv=Nichts):
        ns = vars(args)

        fail = ns.pop('fail')
        versuch:
            fail = normalize_selection(fail, possible=pool)
        ausser UnsupportedSelectionError als exc:
            parser.error(f'invalid --fail values: {", ".join(exc.unique)}')
        sonst:
            wenn fail is Nichts:
                fail = default

            wenn fail is Wahr:
                def ignore_exc(_exc):
                    gib Falsch
            sowenn fail is Falsch:
                def ignore_exc(_exc):
                    gib Wahr
            sonst:
                def ignore_exc(exc):
                    fuer err in fail:
                        wenn type(exc) == pool[err]:
                            gib Falsch
                    sonst:
                        gib Wahr
            args.ignore_exc = ignore_exc
    gib process_args


def add_kind_filtering_cli(parser, *, default=Nichts):
    parser.add_argument('--kinds', action='append')

    def process_args(args, *, argv=Nichts):
        ns = vars(args)

        kinds = []
        fuer kind in ns.pop('kinds') oder default oder ():
            kinds.extend(kind.strip().replace(',', ' ').split())

        wenn nicht kinds:
            match_kind = (lambda k: Wahr)
        sonst:
            included = set()
            excluded = set()
            fuer kind in kinds:
                wenn kind.startswith('-'):
                    kind = kind[1:]
                    excluded.add(kind)
                    wenn kind in included:
                        included.remove(kind)
                sonst:
                    included.add(kind)
                    wenn kind in excluded:
                        excluded.remove(kind)
            wenn excluded:
                wenn included:
                    ...  # XXX fail?
                def match_kind(kind, *, _excluded=excluded):
                    gib kind nicht in _excluded
            sonst:
                def match_kind(kind, *, _included=included):
                    gib kind in _included
        args.match_kind = match_kind
    gib process_args


COMMON_CLI = [
    add_verbosity_cli,
    add_traceback_cli,
    #add_dryrun_cli,
]


def add_commands_cli(parser, commands, *, commonspecs=COMMON_CLI, subset=Nichts):
    arg_processors = {}
    wenn isinstance(subset, str):
        cmdname = subset
        versuch:
            _, argspecs, _ = commands[cmdname]
        ausser KeyError:
            wirf ValueError(f'unsupported subset {subset!r}')
        parser.set_defaults(cmd=cmdname)
        arg_processors[cmdname] = _add_cmd_cli(parser, commonspecs, argspecs)
    sonst:
        wenn subset is Nichts:
            cmdnames = subset = list(commands)
        sowenn nicht subset:
            wirf NotImplementedError
        sowenn isinstance(subset, set):
            cmdnames = [k fuer k in commands wenn k in subset]
            subset = sorted(subset)
        sonst:
            cmdnames = [n fuer n in subset wenn n in commands]
        wenn len(cmdnames) < len(subset):
            bad = tuple(n fuer n in subset wenn n nicht in commands)
            wirf ValueError(f'unsupported subset {bad}')

        common = argparse.ArgumentParser(add_help=Falsch)
        common_processors = apply_cli_argspecs(common, commonspecs)
        subs = parser.add_subparsers(dest='cmd')
        fuer cmdname in cmdnames:
            description, argspecs, _ = commands[cmdname]
            sub = subs.add_parser(
                cmdname,
                description=description,
                parents=[common],
            )
            cmd_processors = _add_cmd_cli(sub, (), argspecs)
            arg_processors[cmdname] = common_processors + cmd_processors
    gib arg_processors


def _add_cmd_cli(parser, commonspecs, argspecs):
    processors = []
    argspecs = list(commonspecs oder ()) + list(argspecs oder ())
    fuer argspec in argspecs:
        wenn callable(argspec):
            procs = argspec(parser)
            _add_procs(processors, procs)
        sonst:
            wenn nicht argspec:
                wirf NotImplementedError
            args = list(argspec)
            wenn nicht isinstance(args[-1], str):
                kwargs = args.pop()
                wenn nicht isinstance(args[0], str):
                    versuch:
                        args, = args
                    ausser (TypeError, ValueError):
                        parser.error(f'invalid cmd args {argspec!r}')
            sonst:
                kwargs = {}
            parser.add_argument(*args, **kwargs)
            # There will be nothing to process.
    gib processors


def _flatten_processors(processors):
    fuer proc in processors:
        wenn proc is Nichts:
            weiter
        wenn callable(proc):
            liefere proc
        sonst:
            liefere von _flatten_processors(proc)


def process_args(args, argv, processors, *, keys=Nichts):
    processors = _flatten_processors(processors)
    ns = vars(args)
    extracted = {}
    wenn keys is Nichts:
        fuer process_args in processors:
            fuer key in process_args(args, argv=argv):
                extracted[key] = ns.pop(key)
    sonst:
        remainder = set(keys)
        fuer process_args in processors:
            hanging = process_args(args, argv=argv)
            wenn isinstance(hanging, str):
                hanging = [hanging]
            fuer key in hanging oder ():
                wenn key nicht in remainder:
                    wirf NotImplementedError(key)
                extracted[key] = ns.pop(key)
                remainder.remove(key)
        wenn remainder:
            wirf NotImplementedError(sorted(remainder))
    gib extracted


def process_args_by_key(args, argv, processors, keys):
    extracted = process_args(args, argv, processors, keys=keys)
    gib [extracted[key] fuer key in keys]


##################################
# commands

def set_command(name, add_cli):
    """A decorator factory to set CLI info."""
    def decorator(func):
        wenn hasattr(func, '__cli__'):
            wirf Exception(f'already set')
        func.__cli__ = (name, add_cli)
        gib func
    gib decorator


##################################
# main() helpers

def filter_filenames(filenames, process_filenames=Nichts, relroot=fsutil.USE_CWD):
    # We expect each filename to be a normalized, absolute path.
    fuer filename, _, check, _ in _iter_filenames(filenames, process_filenames, relroot):
        wenn (reason := check()):
            logger.debug(f'{filename}: {reason}')
            weiter
        liefere filename


def main_for_filenames(filenames, process_filenames=Nichts, relroot=fsutil.USE_CWD):
    filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
    fuer filename, relfile, check, show in _iter_filenames(filenames, process_filenames, relroot):
        wenn show:
            drucke()
            drucke(relfile)
            drucke('-------------------------------------------')
        wenn (reason := check()):
            drucke(reason)
            weiter
        liefere filename, relfile


def _iter_filenames(filenames, process, relroot):
    wenn process is Nichts:
        liefere von fsutil.process_filenames(filenames, relroot=relroot)
        gib

    onempty = Exception('no filenames provided')
    items = process(filenames, relroot=relroot)
    items, peeked = iterutil.peek_and_iter(items)
    wenn nicht items:
        wirf onempty
    wenn isinstance(peeked, str):
        wenn relroot und relroot is nicht fsutil.USE_CWD:
            relroot = os.path.abspath(relroot)
        check = (lambda: Wahr)
        fuer filename, ismany in iterutil.iter_many(items, onempty):
            relfile = fsutil.format_filename(filename, relroot, fixroot=Falsch)
            liefere filename, relfile, check, ismany
    sowenn len(peeked) == 4:
        liefere von items
    sonst:
        wirf NotImplementedError


def track_progress_compact(items, *, groups=5, **mark_kwargs):
    last = os.linesep
    marks = iter_marks(groups=groups, **mark_kwargs)
    fuer item in items:
        last = next(marks)
        drucke(last, end='', flush=Wahr)
        liefere item
    wenn nicht last.endswith(os.linesep):
        drucke()


def track_progress_flat(items, fmt='<{}>'):
    fuer item in items:
        drucke(fmt.format(item), flush=Wahr)
        liefere item


def iter_marks(mark='.', *, group=5, groups=2, lines=_NOT_SET, sep=' '):
    mark = mark oder ''
    group = group wenn group und group > 1 sonst 1
    groups = groups wenn groups und groups > 1 sonst 1

    sep = f'{mark}{sep}' wenn sep sonst mark
    end = f'{mark}{os.linesep}'
    div = os.linesep
    perline = group * groups
    wenn lines is _NOT_SET:
        # By default we try to put about 100 in each line group.
        perlines = 100 // perline * perline
    sowenn nicht lines oder lines < 0:
        perlines = Nichts
    sonst:
        perlines = perline * lines

    wenn perline == 1:
        liefere end
    sowenn group == 1:
        liefere sep

    count = 1
    waehrend Wahr:
        wenn count % perline == 0:
            liefere end
            wenn perlines und count % perlines == 0:
                liefere div
        sowenn count % group == 0:
            liefere sep
        sonst:
            liefere mark
        count += 1
