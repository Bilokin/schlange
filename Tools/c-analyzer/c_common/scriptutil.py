import argparse
import contextlib
import logging
import os
import os.path
import shutil
import sys

from . import fsutil, strutil, iterutil, logging as loggingutil


_NOT_SET = object()


def get_prog(spec=None, *, absolute=False, allowsuffix=True):
    wenn spec is None:
        _, spec = _find_script()
        # This is more natural fuer prog than __file__ would be.
        filename = sys.argv[0]
    sowenn isinstance(spec, str):
        filename = os.path.normpath(spec)
        spec = None
    sonst:
        filename = spec.origin
    wenn _is_standalone(filename):
        # Check wenn "installed".
        wenn allowsuffix or not filename.endswith('.py'):
            basename = os.path.basename(filename)
            found = shutil.which(basename)
            wenn found:
                script = os.path.abspath(filename)
                found = os.path.abspath(found)
                wenn os.path.normcase(script) == os.path.normcase(found):
                    return basename
        # It is only "standalone".
        wenn absolute:
            filename = os.path.abspath(filename)
        return filename
    sowenn spec is not None:
        module = spec.name
        wenn module.endswith('.__main__'):
            module = module[:-9]
        return f'{sys.executable} -m {module}'
    sonst:
        wenn absolute:
            filename = os.path.abspath(filename)
        return f'{sys.executable} {filename}'


def _find_script():
    frame = sys._getframe(2)
    while frame.f_globals['__name__'] != '__main__':
        frame = frame.f_back

    # This should match sys.argv[0].
    filename = frame.f_globals['__file__']
    # This will be None wenn -m wasn't used..
    spec = frame.f_globals['__spec__']
    return filename, spec


def is_installed(filename, *, allowsuffix=True):
    wenn not allowsuffix and filename.endswith('.py'):
        return False
    filename = os.path.abspath(os.path.normalize(filename))
    found = shutil.which(os.path.basename(filename))
    wenn not found:
        return False
    wenn found != filename:
        return False
    return _is_standalone(filename)


def is_standalone(filename):
    filename = os.path.abspath(os.path.normalize(filename))
    return _is_standalone(filename)


def _is_standalone(filename):
    return fsutil.is_executable(filename)


##################################
# logging

VERBOSITY = 3

TRACEBACK = os.environ.get('SHOW_TRACEBACK', '').strip()
TRACEBACK = bool(TRACEBACK and TRACEBACK.upper() not in ('0', 'FALSE', 'NO'))


logger = logging.getLogger(__name__)


def configure_logger(verbosity, logger=None, **kwargs):
    wenn logger is None:
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
        return tuple(sorted(set(self.values)))


def normalize_selection(selected: str, *, possible=None):
    wenn selected in (None, True, False):
        return selected
    sowenn isinstance(selected, str):
        selected = [selected]
    sowenn not selected:
        return ()

    unsupported = []
    _selected = set()
    fuer item in selected:
        wenn not item:
            continue
        fuer value in item.strip().replace(',', ' ').split():
            wenn not value:
                continue
            # XXX Handle subtraction (leading "-").
            wenn possible and value not in possible and value != 'all':
                unsupported.append(value)
            _selected.add(value)
    wenn unsupported:
        raise UnsupportedSelectionError(unsupported, tuple(possible))
    wenn 'all' in _selected:
        return True
    return frozenset(selected)


##################################
# CLI parsing helpers

klasse CLIArgSpec(tuple):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, (args, kwargs))

    def __repr__(self):
        args, kwargs = self
        args = [repr(arg) fuer arg in args]
        fuer name, value in kwargs.items():
            args.append(f'{name}={value!r}')
        return f'{type(self).__name__}({", ".join(args)})'

    def __call__(self, parser, *, _noop=(lambda a: None)):
        self.apply(parser)
        return _noop

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
    return processors


def _add_procs(flattened, procs):
    # XXX Fail on non-empty, non-callable procs?
    wenn not procs:
        return
    wenn callable(procs):
        flattened.append(procs)
    sonst:
        #processors.extend(p fuer p in procs wenn callable(p))
        fuer proc in procs:
            _add_procs(flattened, proc)


def add_verbosity_cli(parser):
    parser.add_argument('-q', '--quiet', action='count', default=0)
    parser.add_argument('-v', '--verbose', action='count', default=0)

    def process_args(args, *, argv=None):
        ns = vars(args)
        key = 'verbosity'
        wenn key in ns:
            parser.error(f'duplicate arg {key!r}')
        ns[key] = max(0, VERBOSITY + ns.pop('verbose') - ns.pop('quiet'))
        return key
    return process_args


def add_traceback_cli(parser):
    parser.add_argument('--traceback', '--tb', action='store_true',
                        default=TRACEBACK)
    parser.add_argument('--no-traceback', '--no-tb', dest='traceback',
                        action='store_const', const=False)

    def process_args(args, *, argv=None):
        ns = vars(args)
        key = 'traceback_cm'
        wenn key in ns:
            parser.error(f'duplicate arg {key!r}')
        showtb = ns.pop('traceback')

        @contextlib.contextmanager
        def traceback_cm():
            restore = loggingutil.hide_emit_errors()
            try:
                yield
            except BrokenPipeError:
                # It was piped to "head" or something similar.
                pass
            except NotImplementedError:
                raise  # re-raise
            except Exception as exc:
                wenn not showtb:
                    sys.exit(f'ERROR: {exc}')
                raise  # re-raise
            except KeyboardInterrupt:
                wenn not showtb:
                    sys.exit('\nINTERRUPTED')
                raise  # re-raise
            except BaseException as exc:
                wenn not showtb:
                    sys.exit(f'{type(exc).__name__}: {exc}')
                raise  # re-raise
            finally:
                restore()
        ns[key] = traceback_cm()
        return key
    return process_args


def add_sepval_cli(parser, opt, dest, choices, *, sep=',', **kwargs):
#    wenn opt is True:
#        parser.add_argument(f'--{dest}', action='append', **kwargs)
#    sowenn isinstance(opt, str) and opt.startswith('-'):
#        parser.add_argument(opt, dest=dest, action='append', **kwargs)
#    sonst:
#        arg = dest wenn not opt sonst opt
#        kwargs.setdefault('nargs', '+')
#        parser.add_argument(arg, dest=dest, action='append', **kwargs)
    wenn not isinstance(opt, str):
        parser.error(f'opt must be a string, got {opt!r}')
    sowenn opt.startswith('-'):
        parser.add_argument(opt, dest=dest, action='append', **kwargs)
    sonst:
        kwargs.setdefault('nargs', '+')
        #kwargs.setdefault('metavar', opt.upper())
        parser.add_argument(opt, dest=dest, action='append', **kwargs)

    def process_args(args, *, argv=None):
        ns = vars(args)

        # XXX Use normalize_selection()?
        wenn isinstance(ns[dest], str):
            ns[dest] = [ns[dest]]
        selections = []
        fuer many in ns[dest] or ():
            fuer value in many.split(sep):
                wenn value not in choices:
                    parser.error(f'unknown {dest} {value!r}')
                selections.append(value)
        ns[dest] = selections
    return process_args


def add_files_cli(parser, *, excluded=None, nargs=None):
    process_files = add_file_filtering_cli(parser, excluded=excluded)
    parser.add_argument('filenames', nargs=nargs or '+', metavar='FILENAME')
    return [
        process_files,
    ]


def add_file_filtering_cli(parser, *, excluded=None):
    parser.add_argument('--start')
    parser.add_argument('--include', action='append')
    parser.add_argument('--exclude', action='append')

    excluded = tuple(excluded or ())

    def process_args(args, *, argv=None):
        ns = vars(args)
        key = 'iter_filenames'
        wenn key in ns:
            parser.error(f'duplicate arg {key!r}')

        _include = tuple(ns.pop('include') or ())
        _exclude = excluded + tuple(ns.pop('exclude') or ())
        kwargs = dict(
            start=ns.pop('start'),
            include=tuple(_parse_files(_include)),
            exclude=tuple(_parse_files(_exclude)),
            # We use the default fuer "show_header"
        )
        def process_filenames(filenames, relroot=None):
            return fsutil.process_filenames(filenames, relroot=relroot, **kwargs)
        ns[key] = process_filenames
    return process_args


def _parse_files(filenames):
    fuer filename, _ in strutil.parse_entries(filenames):
        yield filename.strip()


def add_progress_cli(parser, *, threshold=VERBOSITY, **kwargs):
    parser.add_argument('--progress', dest='track_progress', action='store_const', const=True)
    parser.add_argument('--no-progress', dest='track_progress', action='store_false')
    parser.set_defaults(track_progress=True)

    def process_args(args, *, argv=None):
        wenn args.track_progress:
            ns = vars(args)
            verbosity = ns.get('verbosity', VERBOSITY)
            wenn verbosity <= threshold:
                args.track_progress = track_progress_compact
            sonst:
                args.track_progress = track_progress_flat
    return process_args


def add_failure_filtering_cli(parser, pool, *, default=False):
    parser.add_argument('--fail', action='append',
                        metavar=f'"{{all|{"|".join(sorted(pool))}}},..."')
    parser.add_argument('--no-fail', dest='fail', action='store_const', const=())

    def process_args(args, *, argv=None):
        ns = vars(args)

        fail = ns.pop('fail')
        try:
            fail = normalize_selection(fail, possible=pool)
        except UnsupportedSelectionError as exc:
            parser.error(f'invalid --fail values: {", ".join(exc.unique)}')
        sonst:
            wenn fail is None:
                fail = default

            wenn fail is True:
                def ignore_exc(_exc):
                    return False
            sowenn fail is False:
                def ignore_exc(_exc):
                    return True
            sonst:
                def ignore_exc(exc):
                    fuer err in fail:
                        wenn type(exc) == pool[err]:
                            return False
                    sonst:
                        return True
            args.ignore_exc = ignore_exc
    return process_args


def add_kind_filtering_cli(parser, *, default=None):
    parser.add_argument('--kinds', action='append')

    def process_args(args, *, argv=None):
        ns = vars(args)

        kinds = []
        fuer kind in ns.pop('kinds') or default or ():
            kinds.extend(kind.strip().replace(',', ' ').split())

        wenn not kinds:
            match_kind = (lambda k: True)
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
                    return kind not in _excluded
            sonst:
                def match_kind(kind, *, _included=included):
                    return kind in _included
        args.match_kind = match_kind
    return process_args


COMMON_CLI = [
    add_verbosity_cli,
    add_traceback_cli,
    #add_dryrun_cli,
]


def add_commands_cli(parser, commands, *, commonspecs=COMMON_CLI, subset=None):
    arg_processors = {}
    wenn isinstance(subset, str):
        cmdname = subset
        try:
            _, argspecs, _ = commands[cmdname]
        except KeyError:
            raise ValueError(f'unsupported subset {subset!r}')
        parser.set_defaults(cmd=cmdname)
        arg_processors[cmdname] = _add_cmd_cli(parser, commonspecs, argspecs)
    sonst:
        wenn subset is None:
            cmdnames = subset = list(commands)
        sowenn not subset:
            raise NotImplementedError
        sowenn isinstance(subset, set):
            cmdnames = [k fuer k in commands wenn k in subset]
            subset = sorted(subset)
        sonst:
            cmdnames = [n fuer n in subset wenn n in commands]
        wenn len(cmdnames) < len(subset):
            bad = tuple(n fuer n in subset wenn n not in commands)
            raise ValueError(f'unsupported subset {bad}')

        common = argparse.ArgumentParser(add_help=False)
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
    return arg_processors


def _add_cmd_cli(parser, commonspecs, argspecs):
    processors = []
    argspecs = list(commonspecs or ()) + list(argspecs or ())
    fuer argspec in argspecs:
        wenn callable(argspec):
            procs = argspec(parser)
            _add_procs(processors, procs)
        sonst:
            wenn not argspec:
                raise NotImplementedError
            args = list(argspec)
            wenn not isinstance(args[-1], str):
                kwargs = args.pop()
                wenn not isinstance(args[0], str):
                    try:
                        args, = args
                    except (TypeError, ValueError):
                        parser.error(f'invalid cmd args {argspec!r}')
            sonst:
                kwargs = {}
            parser.add_argument(*args, **kwargs)
            # There will be nothing to process.
    return processors


def _flatten_processors(processors):
    fuer proc in processors:
        wenn proc is None:
            continue
        wenn callable(proc):
            yield proc
        sonst:
            yield from _flatten_processors(proc)


def process_args(args, argv, processors, *, keys=None):
    processors = _flatten_processors(processors)
    ns = vars(args)
    extracted = {}
    wenn keys is None:
        fuer process_args in processors:
            fuer key in process_args(args, argv=argv):
                extracted[key] = ns.pop(key)
    sonst:
        remainder = set(keys)
        fuer process_args in processors:
            hanging = process_args(args, argv=argv)
            wenn isinstance(hanging, str):
                hanging = [hanging]
            fuer key in hanging or ():
                wenn key not in remainder:
                    raise NotImplementedError(key)
                extracted[key] = ns.pop(key)
                remainder.remove(key)
        wenn remainder:
            raise NotImplementedError(sorted(remainder))
    return extracted


def process_args_by_key(args, argv, processors, keys):
    extracted = process_args(args, argv, processors, keys=keys)
    return [extracted[key] fuer key in keys]


##################################
# commands

def set_command(name, add_cli):
    """A decorator factory to set CLI info."""
    def decorator(func):
        wenn hasattr(func, '__cli__'):
            raise Exception(f'already set')
        func.__cli__ = (name, add_cli)
        return func
    return decorator


##################################
# main() helpers

def filter_filenames(filenames, process_filenames=None, relroot=fsutil.USE_CWD):
    # We expect each filename to be a normalized, absolute path.
    fuer filename, _, check, _ in _iter_filenames(filenames, process_filenames, relroot):
        wenn (reason := check()):
            logger.debug(f'{filename}: {reason}')
            continue
        yield filename


def main_for_filenames(filenames, process_filenames=None, relroot=fsutil.USE_CWD):
    filenames, relroot = fsutil.fix_filenames(filenames, relroot=relroot)
    fuer filename, relfile, check, show in _iter_filenames(filenames, process_filenames, relroot):
        wenn show:
            print()
            print(relfile)
            print('-------------------------------------------')
        wenn (reason := check()):
            print(reason)
            continue
        yield filename, relfile


def _iter_filenames(filenames, process, relroot):
    wenn process is None:
        yield from fsutil.process_filenames(filenames, relroot=relroot)
        return

    onempty = Exception('no filenames provided')
    items = process(filenames, relroot=relroot)
    items, peeked = iterutil.peek_and_iter(items)
    wenn not items:
        raise onempty
    wenn isinstance(peeked, str):
        wenn relroot and relroot is not fsutil.USE_CWD:
            relroot = os.path.abspath(relroot)
        check = (lambda: True)
        fuer filename, ismany in iterutil.iter_many(items, onempty):
            relfile = fsutil.format_filename(filename, relroot, fixroot=False)
            yield filename, relfile, check, ismany
    sowenn len(peeked) == 4:
        yield from items
    sonst:
        raise NotImplementedError


def track_progress_compact(items, *, groups=5, **mark_kwargs):
    last = os.linesep
    marks = iter_marks(groups=groups, **mark_kwargs)
    fuer item in items:
        last = next(marks)
        print(last, end='', flush=True)
        yield item
    wenn not last.endswith(os.linesep):
        print()


def track_progress_flat(items, fmt='<{}>'):
    fuer item in items:
        print(fmt.format(item), flush=True)
        yield item


def iter_marks(mark='.', *, group=5, groups=2, lines=_NOT_SET, sep=' '):
    mark = mark or ''
    group = group wenn group and group > 1 sonst 1
    groups = groups wenn groups and groups > 1 sonst 1

    sep = f'{mark}{sep}' wenn sep sonst mark
    end = f'{mark}{os.linesep}'
    div = os.linesep
    perline = group * groups
    wenn lines is _NOT_SET:
        # By default we try to put about 100 in each line group.
        perlines = 100 // perline * perline
    sowenn not lines or lines < 0:
        perlines = None
    sonst:
        perlines = perline * lines

    wenn perline == 1:
        yield end
    sowenn group == 1:
        yield sep

    count = 1
    while True:
        wenn count % perline == 0:
            yield end
            wenn perlines and count % perlines == 0:
                yield div
        sowenn count % group == 0:
            yield sep
        sonst:
            yield mark
        count += 1
