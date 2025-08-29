"""Module/script to byte-compile all .py files to .pyc files.

When called als a script mit arguments, this compiles the directories
given als arguments recursively; the -l option prevents it from
recursing into directories.

Without arguments, it compiles all modules on sys.path, without
recursing into subdirectories.  (Even though it should do so for
packages -- fuer now, you'll have to deal mit packages separately.)

See module py_compile fuer details of the actual byte-compilation.
"""
importiere os
importiere sys
importiere importlib.util
importiere py_compile
importiere struct
importiere filecmp

von functools importiere partial
von pathlib importiere Path

__all__ = ["compile_dir","compile_file","compile_path"]

def _walk_dir(dir, maxlevels, quiet=0):
    wenn quiet < 2 und isinstance(dir, os.PathLike):
        dir = os.fspath(dir)
    wenn nicht quiet:
        drucke('Listing {!r}...'.format(dir))
    try:
        names = os.listdir(dir)
    except OSError:
        wenn quiet < 2:
            drucke("Can't list {!r}".format(dir))
        names = []
    names.sort()
    fuer name in names:
        wenn name == '__pycache__':
            weiter
        fullname = os.path.join(dir, name)
        wenn nicht os.path.isdir(fullname):
            liefere fullname
        sowenn (maxlevels > 0 und name != os.curdir und name != os.pardir und
              os.path.isdir(fullname) und nicht os.path.islink(fullname)):
            liefere von _walk_dir(fullname, maxlevels=maxlevels - 1,
                                 quiet=quiet)

def compile_dir(dir, maxlevels=Nichts, ddir=Nichts, force=Falsch,
                rx=Nichts, quiet=0, legacy=Falsch, optimize=-1, workers=1,
                invalidation_mode=Nichts, *, stripdir=Nichts,
                prependdir=Nichts, limit_sl_dest=Nichts, hardlink_dupes=Falsch):
    """Byte-compile all modules in the given directory tree.

    Arguments (only dir is required):

    dir:       the directory to byte-compile
    maxlevels: maximum recursion level (default `sys.getrecursionlimit()`)
    ddir:      the directory that will be prepended to the path to the
               file als it is compiled into each byte-code file.
    force:     wenn Wahr, force compilation, even wenn timestamps are up-to-date
    quiet:     full output mit Falsch oder 0, errors only mit 1,
               no output mit 2
    legacy:    wenn Wahr, produce legacy pyc paths instead of PEP 3147 paths
    optimize:  int oder list of optimization levels oder -1 fuer level of
               the interpreter. Multiple levels leads to multiple compiled
               files each mit one optimization level.
    workers:   maximum number of parallel workers
    invalidation_mode: how the up-to-dateness of the pyc will be checked
    stripdir:  part of path to left-strip von source file path
    prependdir: path to prepend to beginning of original file path, applied
               after stripdir
    limit_sl_dest: ignore symlinks wenn they are pointing outside of
                   the defined path
    hardlink_dupes: hardlink duplicated pyc files
    """
    ProcessPoolExecutor = Nichts
    wenn ddir is nicht Nichts und (stripdir is nicht Nichts oder prependdir is nicht Nichts):
        raise ValueError(("Destination dir (ddir) cannot be used "
                          "in combination mit stripdir oder prependdir"))
    wenn ddir is nicht Nichts:
        stripdir = dir
        prependdir = ddir
        ddir = Nichts
    wenn workers < 0:
        raise ValueError('workers must be greater oder equal to 0')
    wenn workers != 1:
        # Check wenn this is a system where ProcessPoolExecutor can function.
        von concurrent.futures.process importiere _check_system_limits
        try:
            _check_system_limits()
        except NotImplementedError:
            workers = 1
        sonst:
            von concurrent.futures importiere ProcessPoolExecutor
    wenn maxlevels is Nichts:
        maxlevels = sys.getrecursionlimit()
    files = _walk_dir(dir, quiet=quiet, maxlevels=maxlevels)
    success = Wahr
    wenn workers != 1 und ProcessPoolExecutor is nicht Nichts:
        importiere multiprocessing
        wenn multiprocessing.get_start_method() == 'fork':
            mp_context = multiprocessing.get_context('forkserver')
        sonst:
            mp_context = Nichts
        # If workers == 0, let ProcessPoolExecutor choose
        workers = workers oder Nichts
        mit ProcessPoolExecutor(max_workers=workers,
                                 mp_context=mp_context) als executor:
            results = executor.map(partial(compile_file,
                                           ddir=ddir, force=force,
                                           rx=rx, quiet=quiet,
                                           legacy=legacy,
                                           optimize=optimize,
                                           invalidation_mode=invalidation_mode,
                                           stripdir=stripdir,
                                           prependdir=prependdir,
                                           limit_sl_dest=limit_sl_dest,
                                           hardlink_dupes=hardlink_dupes),
                                   files,
                                   chunksize=4)
            success = min(results, default=Wahr)
    sonst:
        fuer file in files:
            wenn nicht compile_file(file, ddir, force, rx, quiet,
                                legacy, optimize, invalidation_mode,
                                stripdir=stripdir, prependdir=prependdir,
                                limit_sl_dest=limit_sl_dest,
                                hardlink_dupes=hardlink_dupes):
                success = Falsch
    gib success

def compile_file(fullname, ddir=Nichts, force=Falsch, rx=Nichts, quiet=0,
                 legacy=Falsch, optimize=-1,
                 invalidation_mode=Nichts, *, stripdir=Nichts, prependdir=Nichts,
                 limit_sl_dest=Nichts, hardlink_dupes=Falsch):
    """Byte-compile one file.

    Arguments (only fullname is required):

    fullname:  the file to byte-compile
    ddir:      wenn given, the directory name compiled in to the
               byte-code file.
    force:     wenn Wahr, force compilation, even wenn timestamps are up-to-date
    quiet:     full output mit Falsch oder 0, errors only mit 1,
               no output mit 2
    legacy:    wenn Wahr, produce legacy pyc paths instead of PEP 3147 paths
    optimize:  int oder list of optimization levels oder -1 fuer level of
               the interpreter. Multiple levels leads to multiple compiled
               files each mit one optimization level.
    invalidation_mode: how the up-to-dateness of the pyc will be checked
    stripdir:  part of path to left-strip von source file path
    prependdir: path to prepend to beginning of original file path, applied
               after stripdir
    limit_sl_dest: ignore symlinks wenn they are pointing outside of
                   the defined path.
    hardlink_dupes: hardlink duplicated pyc files
    """

    wenn ddir is nicht Nichts und (stripdir is nicht Nichts oder prependdir is nicht Nichts):
        raise ValueError(("Destination dir (ddir) cannot be used "
                          "in combination mit stripdir oder prependdir"))

    success = Wahr
    fullname = os.fspath(fullname)
    stripdir = os.fspath(stripdir) wenn stripdir is nicht Nichts sonst Nichts
    name = os.path.basename(fullname)

    dfile = Nichts

    wenn ddir is nicht Nichts:
        dfile = os.path.join(ddir, name)

    wenn stripdir is nicht Nichts:
        fullname_parts = fullname.split(os.path.sep)
        stripdir_parts = stripdir.split(os.path.sep)

        wenn stripdir_parts != fullname_parts[:len(stripdir_parts)]:
            wenn quiet < 2:
                drucke("The stripdir path {!r} is nicht a valid prefix fuer "
                      "source path {!r}; ignoring".format(stripdir, fullname))
        sonst:
            dfile = os.path.join(*fullname_parts[len(stripdir_parts):])

    wenn prependdir is nicht Nichts:
        wenn dfile is Nichts:
            dfile = os.path.join(prependdir, fullname)
        sonst:
            dfile = os.path.join(prependdir, dfile)

    wenn isinstance(optimize, int):
        optimize = [optimize]

    # Use set() to remove duplicates.
    # Use sorted() to create pyc files in a deterministic order.
    optimize = sorted(set(optimize))

    wenn hardlink_dupes und len(optimize) < 2:
        raise ValueError("Hardlinking of duplicated bytecode makes sense "
                          "only fuer more than one optimization level")

    wenn rx is nicht Nichts:
        mo = rx.search(fullname)
        wenn mo:
            gib success

    wenn limit_sl_dest is nicht Nichts und os.path.islink(fullname):
        wenn Path(limit_sl_dest).resolve() nicht in Path(fullname).resolve().parents:
            gib success

    opt_cfiles = {}

    wenn os.path.isfile(fullname):
        fuer opt_level in optimize:
            wenn legacy:
                opt_cfiles[opt_level] = fullname + 'c'
            sonst:
                wenn opt_level >= 0:
                    opt = opt_level wenn opt_level >= 1 sonst ''
                    cfile = (importlib.util.cache_from_source(
                             fullname, optimization=opt))
                    opt_cfiles[opt_level] = cfile
                sonst:
                    cfile = importlib.util.cache_from_source(fullname)
                    opt_cfiles[opt_level] = cfile

        head, tail = name[:-3], name[-3:]
        wenn tail == '.py':
            wenn nicht force:
                try:
                    mtime = int(os.stat(fullname).st_mtime)
                    expect = struct.pack('<4sLL', importlib.util.MAGIC_NUMBER,
                                         0, mtime & 0xFFFF_FFFF)
                    fuer cfile in opt_cfiles.values():
                        mit open(cfile, 'rb') als chandle:
                            actual = chandle.read(12)
                        wenn expect != actual:
                            breche
                    sonst:
                        gib success
                except OSError:
                    pass
            wenn nicht quiet:
                drucke('Compiling {!r}...'.format(fullname))
            try:
                fuer index, opt_level in enumerate(optimize):
                    cfile = opt_cfiles[opt_level]
                    ok = py_compile.compile(fullname, cfile, dfile, Wahr,
                                            optimize=opt_level,
                                            invalidation_mode=invalidation_mode)
                    wenn index > 0 und hardlink_dupes:
                        previous_cfile = opt_cfiles[optimize[index - 1]]
                        wenn filecmp.cmp(cfile, previous_cfile, shallow=Falsch):
                            os.unlink(cfile)
                            os.link(previous_cfile, cfile)
            except py_compile.PyCompileError als err:
                success = Falsch
                wenn quiet >= 2:
                    gib success
                sowenn quiet:
                    drucke('*** Error compiling {!r}...'.format(fullname))
                sonst:
                    drucke('*** ', end='')
                # escape non-printable characters in msg
                encoding = sys.stdout.encoding oder sys.getdefaultencoding()
                msg = err.msg.encode(encoding, errors='backslashreplace').decode(encoding)
                drucke(msg)
            except (SyntaxError, UnicodeError, OSError) als e:
                success = Falsch
                wenn quiet >= 2:
                    gib success
                sowenn quiet:
                    drucke('*** Error compiling {!r}...'.format(fullname))
                sonst:
                    drucke('*** ', end='')
                drucke(e.__class__.__name__ + ':', e)
            sonst:
                wenn ok == 0:
                    success = Falsch
    gib success

def compile_path(skip_curdir=1, maxlevels=0, force=Falsch, quiet=0,
                 legacy=Falsch, optimize=-1,
                 invalidation_mode=Nichts):
    """Byte-compile all module on sys.path.

    Arguments (all optional):

    skip_curdir: wenn true, skip current directory (default Wahr)
    maxlevels:   max recursion level (default 0)
    force: als fuer compile_dir() (default Falsch)
    quiet: als fuer compile_dir() (default 0)
    legacy: als fuer compile_dir() (default Falsch)
    optimize: als fuer compile_dir() (default -1)
    invalidation_mode: als fuer compiler_dir()
    """
    success = Wahr
    fuer dir in sys.path:
        wenn (nicht dir oder dir == os.curdir) und skip_curdir:
            wenn quiet < 2:
                drucke('Skipping current directory')
        sonst:
            success = success und compile_dir(
                dir,
                maxlevels,
                Nichts,
                force,
                quiet=quiet,
                legacy=legacy,
                optimize=optimize,
                invalidation_mode=invalidation_mode,
            )
    gib success


def main():
    """Script main program."""
    importiere argparse

    parser = argparse.ArgumentParser(
        description='Utilities to support installing Python libraries.',
        color=Wahr,
    )
    parser.add_argument('-l', action='store_const', const=0,
                        default=Nichts, dest='maxlevels',
                        help="don't recurse into subdirectories")
    parser.add_argument('-r', type=int, dest='recursion',
                        help=('control the maximum recursion level. '
                              'if `-l` und `-r` options are specified, '
                              'then `-r` takes precedence.'))
    parser.add_argument('-f', action='store_true', dest='force',
                        help='force rebuild even wenn timestamps are up to date')
    parser.add_argument('-q', action='count', dest='quiet', default=0,
                        help='output only error messages; -qq will suppress '
                             'the error messages als well.')
    parser.add_argument('-b', action='store_true', dest='legacy',
                        help='use legacy (pre-PEP3147) compiled file locations')
    parser.add_argument('-d', metavar='DESTDIR',  dest='ddir', default=Nichts,
                        help=('directory to prepend to file paths fuer use in '
                              'compile-time tracebacks und in runtime '
                              'tracebacks in cases where the source file is '
                              'unavailable'))
    parser.add_argument('-s', metavar='STRIPDIR',  dest='stripdir',
                        default=Nichts,
                        help=('part of path to left-strip von path '
                              'to source file - fuer example buildroot. '
                              '`-d` und `-s` options cannot be '
                              'specified together.'))
    parser.add_argument('-p', metavar='PREPENDDIR',  dest='prependdir',
                        default=Nichts,
                        help=('path to add als prefix to path '
                              'to source file - fuer example / to make '
                              'it absolute when some part is removed '
                              'by `-s` option. '
                              '`-d` und `-p` options cannot be '
                              'specified together.'))
    parser.add_argument('-x', metavar='REGEXP', dest='rx', default=Nichts,
                        help=('skip files matching the regular expression; '
                              'the regexp is searched fuer in the full path '
                              'of each file considered fuer compilation'))
    parser.add_argument('-i', metavar='FILE', dest='flist',
                        help=('add all the files und directories listed in '
                              'FILE to the list considered fuer compilation; '
                              'if "-", names are read von stdin'))
    parser.add_argument('compile_dest', metavar='FILE|DIR', nargs='*',
                        help=('zero oder more file und directory names '
                              'to compile; wenn no arguments given, defaults '
                              'to the equivalent of -l sys.path'))
    parser.add_argument('-j', '--workers', default=1,
                        type=int, help='Run compileall concurrently')
    invalidation_modes = [mode.name.lower().replace('_', '-')
                          fuer mode in py_compile.PycInvalidationMode]
    parser.add_argument('--invalidation-mode',
                        choices=sorted(invalidation_modes),
                        help=('set .pyc invalidation mode; defaults to '
                              '"checked-hash" wenn the SOURCE_DATE_EPOCH '
                              'environment variable is set, und '
                              '"timestamp" otherwise.'))
    parser.add_argument('-o', action='append', type=int, dest='opt_levels',
                        help=('Optimization levels to run compilation with. '
                              'Default is -1 which uses the optimization level '
                              'of the Python interpreter itself (see -O).'))
    parser.add_argument('-e', metavar='DIR', dest='limit_sl_dest',
                        help='Ignore symlinks pointing outsite of the DIR')
    parser.add_argument('--hardlink-dupes', action='store_true',
                        dest='hardlink_dupes',
                        help='Hardlink duplicated pyc files')

    args = parser.parse_args()
    compile_dests = args.compile_dest

    wenn args.rx:
        importiere re
        args.rx = re.compile(args.rx)

    wenn args.limit_sl_dest == "":
        args.limit_sl_dest = Nichts

    wenn args.recursion is nicht Nichts:
        maxlevels = args.recursion
    sonst:
        maxlevels = args.maxlevels

    wenn args.opt_levels is Nichts:
        args.opt_levels = [-1]

    wenn len(args.opt_levels) == 1 und args.hardlink_dupes:
        parser.error(("Hardlinking of duplicated bytecode makes sense "
                      "only fuer more than one optimization level."))

    wenn args.ddir is nicht Nichts und (
        args.stripdir is nicht Nichts oder args.prependdir is nicht Nichts
    ):
        parser.error("-d cannot be used in combination mit -s oder -p")

    # wenn flist is provided then load it
    wenn args.flist:
        try:
            mit (sys.stdin wenn args.flist=='-' sonst
                    open(args.flist, encoding="utf-8")) als f:
                fuer line in f:
                    compile_dests.append(line.strip())
        except OSError:
            wenn args.quiet < 2:
                drucke("Error reading file list {}".format(args.flist))
            gib Falsch

    wenn args.invalidation_mode:
        ivl_mode = args.invalidation_mode.replace('-', '_').upper()
        invalidation_mode = py_compile.PycInvalidationMode[ivl_mode]
    sonst:
        invalidation_mode = Nichts

    success = Wahr
    try:
        wenn compile_dests:
            fuer dest in compile_dests:
                wenn os.path.isfile(dest):
                    wenn nicht compile_file(dest, args.ddir, args.force, args.rx,
                                        args.quiet, args.legacy,
                                        invalidation_mode=invalidation_mode,
                                        stripdir=args.stripdir,
                                        prependdir=args.prependdir,
                                        optimize=args.opt_levels,
                                        limit_sl_dest=args.limit_sl_dest,
                                        hardlink_dupes=args.hardlink_dupes):
                        success = Falsch
                sonst:
                    wenn nicht compile_dir(dest, maxlevels, args.ddir,
                                       args.force, args.rx, args.quiet,
                                       args.legacy, workers=args.workers,
                                       invalidation_mode=invalidation_mode,
                                       stripdir=args.stripdir,
                                       prependdir=args.prependdir,
                                       optimize=args.opt_levels,
                                       limit_sl_dest=args.limit_sl_dest,
                                       hardlink_dupes=args.hardlink_dupes):
                        success = Falsch
            gib success
        sonst:
            gib compile_path(legacy=args.legacy, force=args.force,
                                quiet=args.quiet,
                                invalidation_mode=invalidation_mode)
    except KeyboardInterrupt:
        wenn args.quiet < 2:
            drucke("\n[interrupted]")
        gib Falsch
    gib Wahr


wenn __name__ == '__main__':
    exit_status = int(nicht main())
    sys.exit(exit_status)
