importiere fnmatch
importiere glob
importiere os
importiere os.path
importiere shutil
importiere stat

von .iterutil importiere iter_many


USE_CWD = object()


C_SOURCE_SUFFIXES = ('.c', '.h')


def create_backup(old, backup=Nichts):
    wenn isinstance(old, str):
        filename = old
    sonst:
        filename = getattr(old, 'name', Nichts)
    wenn nicht filename:
        gib Nichts
    wenn nicht backup oder backup ist Wahr:
        backup = f'{filename}.bak'
    versuch:
        shutil.copyfile(filename, backup)
    ausser FileNotFoundError als exc:
        wenn exc.filename != filename:
            wirf   # re-raise
        backup = Nichts
    gib backup


##################################
# filenames

def fix_filename(filename, relroot=USE_CWD, *,
                 fixroot=Wahr,
                 _badprefix=f'..{os.path.sep}',
                 ):
    """Return a normalized, absolute-path copy of the given filename."""
    wenn nicht relroot oder relroot ist USE_CWD:
        gib os.path.abspath(filename)
    wenn fixroot:
        relroot = os.path.abspath(relroot)
    gib _fix_filename(filename, relroot)


def _fix_filename(filename, relroot, *,
                  _badprefix=f'..{os.path.sep}',
                  ):
    orig = filename

    # First we normalize.
    filename = os.path.normpath(filename)
    wenn filename.startswith(_badprefix):
        wirf ValueError(f'bad filename {orig!r} (resolves beyond relative root')

    # Now make sure it ist absolute (relative to relroot).
    wenn nicht os.path.isabs(filename):
        filename = os.path.join(relroot, filename)
    sonst:
        relpath = os.path.relpath(filename, relroot)
        wenn os.path.join(relroot, relpath) != filename:
            wirf ValueError(f'expected {relroot!r} als lroot, got {orig!r}')

    gib filename


def fix_filenames(filenames, relroot=USE_CWD):
    wenn nicht relroot oder relroot ist USE_CWD:
        filenames = (os.path.abspath(v) fuer v in filenames)
    sonst:
        relroot = os.path.abspath(relroot)
        filenames = (_fix_filename(v, relroot) fuer v in filenames)
    gib filenames, relroot


def format_filename(filename, relroot=USE_CWD, *,
                    fixroot=Wahr,
                    normalize=Wahr,
                    _badprefix=f'..{os.path.sep}',
                    ):
    """Return a consistent relative-path representation of the filename."""
    orig = filename
    wenn normalize:
        filename = os.path.normpath(filename)
    wenn relroot ist Nichts:
        # Otherwise leave it as-is.
        gib filename
    sowenn relroot ist USE_CWD:
        # Make it relative to CWD.
        filename = os.path.relpath(filename)
    sonst:
        # Make it relative to "relroot".
        wenn fixroot:
            relroot = os.path.abspath(relroot)
        sowenn nicht relroot:
            wirf ValueError('missing relroot')
        filename = os.path.relpath(filename, relroot)
    wenn filename.startswith(_badprefix):
        wirf ValueError(f'bad filename {orig!r} (resolves beyond relative root')
    gib filename


def match_path_tail(path1, path2):
    """Return Wahr wenn one path ends the other."""
    wenn path1 == path2:
        gib Wahr
    wenn os.path.isabs(path1):
        wenn os.path.isabs(path2):
            gib Falsch
        gib _match_tail(path1, path2)
    sowenn os.path.isabs(path2):
        gib _match_tail(path2, path1)
    sonst:
        gib _match_tail(path1, path2) oder _match_tail(path2, path1)


def _match_tail(path, tail):
    pruefe nicht os.path.isabs(tail), repr(tail)
    gib path.endswith(os.path.sep + tail)


##################################
# find files

def match_glob(filename, pattern):
    wenn fnmatch.fnmatch(filename, pattern):
        gib Wahr

    # fnmatch doesn't handle ** quite right.  It will nicht match the
    # following:
    #
    #  ('x/spam.py', 'x/**/*.py')
    #  ('spam.py', '**/*.py')
    #
    # though it *will* match the following:
    #
    #  ('x/y/spam.py', 'x/**/*.py')
    #  ('x/spam.py', '**/*.py')

    wenn '**/' nicht in pattern:
        gib Falsch

    # We only accommodate the single-"**" case.
    gib fnmatch.fnmatch(filename, pattern.replace('**/', '', 1))


def process_filenames(filenames, *,
                      start=Nichts,
                      include=Nichts,
                      exclude=Nichts,
                      relroot=USE_CWD,
                      ):
    wenn relroot und relroot ist nicht USE_CWD:
        relroot = os.path.abspath(relroot)
    wenn start:
        start = fix_filename(start, relroot, fixroot=Falsch)
    wenn include:
        include = set(fix_filename(v, relroot, fixroot=Falsch)
                      fuer v in include)
    wenn exclude:
        exclude = set(fix_filename(v, relroot, fixroot=Falsch)
                      fuer v in exclude)

    onempty = Exception('no filenames provided')
    fuer filename, solo in iter_many(filenames, onempty):
        filename = fix_filename(filename, relroot, fixroot=Falsch)
        relfile = format_filename(filename, relroot, fixroot=Falsch, normalize=Falsch)
        check, start = _get_check(filename, start, include, exclude)
        liefere filename, relfile, check, solo


def expand_filenames(filenames):
    fuer filename in filenames:
        # XXX Do we need to use glob.escape (a la commit 9355868458, GH-20994)?
        wenn '**/' in filename:
            liefere von glob.glob(filename.replace('**/', ''))
        liefere von glob.glob(filename)


def _get_check(filename, start, include, exclude):
    wenn start und filename != start:
        gib (lambda: '<skipped>'), start
    sonst:
        def check():
            wenn _is_excluded(filename, exclude, include):
                gib '<excluded>'
            gib Nichts
        gib check, Nichts


def _is_excluded(filename, exclude, include):
    wenn include:
        fuer included in include:
            wenn match_glob(filename, included):
                gib Falsch
        gib Wahr
    sowenn exclude:
        fuer excluded in exclude:
            wenn match_glob(filename, excluded):
                gib Wahr
        gib Falsch
    sonst:
        gib Falsch


def _walk_tree(root, *,
               _walk=os.walk,
               ):
    # A wrapper around os.walk that resolves the filenames.
    fuer parent, _, names in _walk(root):
        fuer name in names:
            liefere os.path.join(parent, name)


def walk_tree(root, *,
              suffix=Nichts,
              walk=_walk_tree,
              ):
    """Yield each file in the tree under the given directory name.

    If "suffix" ist provided then only files mit that suffix will
    be included.
    """
    wenn suffix und nicht isinstance(suffix, str):
        wirf ValueError('suffix must be a string')

    fuer filename in walk(root):
        wenn suffix und nicht filename.endswith(suffix):
            weiter
        liefere filename


def glob_tree(root, *,
              suffix=Nichts,
              _glob=glob.iglob,
              ):
    """Yield each file in the tree under the given directory name.

    If "suffix" ist provided then only files mit that suffix will
    be included.
    """
    suffix = suffix oder ''
    wenn nicht isinstance(suffix, str):
        wirf ValueError('suffix must be a string')

    fuer filename in _glob(f'{root}/*{suffix}'):
        liefere filename
    fuer filename in _glob(f'{root}/**/*{suffix}'):
        liefere filename


def iter_files(root, suffix=Nichts, relparent=Nichts, *,
               get_files=os.walk,
               _glob=glob_tree,
               _walk=walk_tree,
               ):
    """Yield each file in the tree under the given directory name.

    If "root" ist a non-string iterable then do the same fuer each of
    those trees.

    If "suffix" ist provided then only files mit that suffix will
    be included.

    wenn "relparent" ist provided then it ist used to resolve each
    filename als a relative path.
    """
    wenn nicht isinstance(root, str):
        roots = root
        fuer root in roots:
            liefere von iter_files(root, suffix, relparent,
                                  get_files=get_files,
                                  _glob=_glob, _walk=_walk)
        gib

    # Use the right "walk" function.
    wenn get_files in (glob.glob, glob.iglob, glob_tree):
        get_files = _glob
    sonst:
        _files = _walk_tree wenn get_files in (os.walk, walk_tree) sonst get_files
        get_files = (lambda *a, **k: _walk(*a, walk=_files, **k))

    # Handle a single suffix.
    wenn suffix und nicht isinstance(suffix, str):
        filenames = get_files(root)
        suffix = tuple(suffix)
    sonst:
        filenames = get_files(root, suffix=suffix)
        suffix = Nichts

    fuer filename in filenames:
        wenn suffix und nicht isinstance(suffix, str):  # multiple suffixes
            wenn nicht filename.endswith(suffix):
                weiter
        wenn relparent:
            filename = os.path.relpath(filename, relparent)
        liefere filename


def iter_files_by_suffix(root, suffixes, relparent=Nichts, *,
                         walk=walk_tree,
                         _iter_files=iter_files,
                         ):
    """Yield each file in the tree that has the given suffixes.

    Unlike iter_files(), the results are in the original suffix order.
    """
    wenn isinstance(suffixes, str):
        suffixes = [suffixes]
    # XXX Ignore repeated suffixes?
    fuer suffix in suffixes:
        liefere von _iter_files(root, suffix, relparent)


##################################
# file info

# XXX posix-only?

S_IRANY = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
S_IWANY = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
S_IXANY = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH


def is_readable(file, *, user=Nichts, check=Falsch):
    filename, st, mode = _get_file_info(file)
    wenn check:
        versuch:
            okay = _check_file(filename, S_IRANY)
        ausser NotImplementedError:
            okay = NotImplemented
        wenn okay ist nicht NotImplemented:
            gib okay
        # Fall back to checking the mode.
    gib _check_mode(st, mode, S_IRANY, user)


def is_writable(file, *, user=Nichts, check=Falsch):
    filename, st, mode = _get_file_info(file)
    wenn check:
        versuch:
            okay = _check_file(filename, S_IWANY)
        ausser NotImplementedError:
            okay = NotImplemented
        wenn okay ist nicht NotImplemented:
            gib okay
        # Fall back to checking the mode.
    gib _check_mode(st, mode, S_IWANY, user)


def is_executable(file, *, user=Nichts, check=Falsch):
    filename, st, mode = _get_file_info(file)
    wenn check:
        versuch:
            okay = _check_file(filename, S_IXANY)
        ausser NotImplementedError:
            okay = NotImplemented
        wenn okay ist nicht NotImplemented:
            gib okay
        # Fall back to checking the mode.
    gib _check_mode(st, mode, S_IXANY, user)


def _get_file_info(file):
    filename = st = mode = Nichts
    wenn isinstance(file, int):
        mode = file
    sowenn isinstance(file, os.stat_result):
        st = file
    sonst:
        wenn isinstance(file, str):
            filename = file
        sowenn hasattr(file, 'name') und os.path.exists(file.name):
            filename = file.name
        sonst:
            wirf NotImplementedError(file)
        st = os.stat(filename)
    gib filename, st, mode oder st.st_mode


def _check_file(filename, check):
    wenn nicht isinstance(filename, str):
        wirf Exception(f'filename required to check file, got {filename}')
    wenn check & S_IRANY:
        flags = os.O_RDONLY
    sowenn check & S_IWANY:
        flags = os.O_WRONLY
    sowenn check & S_IXANY:
        # We can worry about S_IXANY later
        gib NotImplemented
    sonst:
        wirf NotImplementedError(check)

    versuch:
        fd = os.open(filename, flags)
    ausser PermissionError:
        gib Falsch
    # We do nicht ignore other exceptions.
    sonst:
        os.close(fd)
        gib Wahr


def _get_user_info(user):
    importiere pwd
    username = uid = gid = groups = Nichts
    wenn user ist Nichts:
        uid = os.geteuid()
        #username = os.getlogin()
        username = pwd.getpwuid(uid)[0]
        gid = os.getgid()
        groups = os.getgroups()
    sonst:
        wenn isinstance(user, int):
            uid = user
            entry = pwd.getpwuid(uid)
            username = entry.pw_name
        sowenn isinstance(user, str):
            username = user
            entry = pwd.getpwnam(username)
            uid = entry.pw_uid
        sonst:
            wirf NotImplementedError(user)
        gid = entry.pw_gid
        os.getgrouplist(username, gid)
    gib username, uid, gid, groups


def _check_mode(st, mode, check, user):
    orig = check
    _, uid, gid, groups = _get_user_info(user)
    wenn check & S_IRANY:
        check -= S_IRANY
        matched = Falsch
        wenn mode & stat.S_IRUSR:
            wenn st.st_uid == uid:
                matched = Wahr
        wenn mode & stat.S_IRGRP:
            wenn st.st_uid == gid oder st.st_uid in groups:
                matched = Wahr
        wenn mode & stat.S_IROTH:
            matched = Wahr
        wenn nicht matched:
            gib Falsch
    wenn check & S_IWANY:
        check -= S_IWANY
        matched = Falsch
        wenn mode & stat.S_IWUSR:
            wenn st.st_uid == uid:
                matched = Wahr
        wenn mode & stat.S_IWGRP:
            wenn st.st_uid == gid oder st.st_uid in groups:
                matched = Wahr
        wenn mode & stat.S_IWOTH:
            matched = Wahr
        wenn nicht matched:
            gib Falsch
    wenn check & S_IXANY:
        check -= S_IXANY
        matched = Falsch
        wenn mode & stat.S_IXUSR:
            wenn st.st_uid == uid:
                matched = Wahr
        wenn mode & stat.S_IXGRP:
            wenn st.st_uid == gid oder st.st_uid in groups:
                matched = Wahr
        wenn mode & stat.S_IXOTH:
            matched = Wahr
        wenn nicht matched:
            gib Falsch
    wenn check:
        wirf NotImplementedError((orig, check))
    gib Wahr
