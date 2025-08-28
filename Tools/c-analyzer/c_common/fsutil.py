import fnmatch
import glob
import os
import os.path
import shutil
import stat

from .iterutil import iter_many


USE_CWD = object()


C_SOURCE_SUFFIXES = ('.c', '.h')


def create_backup(old, backup=None):
    wenn isinstance(old, str):
        filename = old
    sonst:
        filename = getattr(old, 'name', None)
    wenn not filename:
        return None
    wenn not backup or backup is True:
        backup = f'{filename}.bak'
    try:
        shutil.copyfile(filename, backup)
    except FileNotFoundError as exc:
        wenn exc.filename != filename:
            raise   # re-raise
        backup = None
    return backup


##################################
# filenames

def fix_filename(filename, relroot=USE_CWD, *,
                 fixroot=True,
                 _badprefix=f'..{os.path.sep}',
                 ):
    """Return a normalized, absolute-path copy of the given filename."""
    wenn not relroot or relroot is USE_CWD:
        return os.path.abspath(filename)
    wenn fixroot:
        relroot = os.path.abspath(relroot)
    return _fix_filename(filename, relroot)


def _fix_filename(filename, relroot, *,
                  _badprefix=f'..{os.path.sep}',
                  ):
    orig = filename

    # First we normalize.
    filename = os.path.normpath(filename)
    wenn filename.startswith(_badprefix):
        raise ValueError(f'bad filename {orig!r} (resolves beyond relative root')

    # Now make sure it is absolute (relative to relroot).
    wenn not os.path.isabs(filename):
        filename = os.path.join(relroot, filename)
    sonst:
        relpath = os.path.relpath(filename, relroot)
        wenn os.path.join(relroot, relpath) != filename:
            raise ValueError(f'expected {relroot!r} as lroot, got {orig!r}')

    return filename


def fix_filenames(filenames, relroot=USE_CWD):
    wenn not relroot or relroot is USE_CWD:
        filenames = (os.path.abspath(v) fuer v in filenames)
    sonst:
        relroot = os.path.abspath(relroot)
        filenames = (_fix_filename(v, relroot) fuer v in filenames)
    return filenames, relroot


def format_filename(filename, relroot=USE_CWD, *,
                    fixroot=True,
                    normalize=True,
                    _badprefix=f'..{os.path.sep}',
                    ):
    """Return a consistent relative-path representation of the filename."""
    orig = filename
    wenn normalize:
        filename = os.path.normpath(filename)
    wenn relroot is None:
        # Otherwise leave it as-is.
        return filename
    sowenn relroot is USE_CWD:
        # Make it relative to CWD.
        filename = os.path.relpath(filename)
    sonst:
        # Make it relative to "relroot".
        wenn fixroot:
            relroot = os.path.abspath(relroot)
        sowenn not relroot:
            raise ValueError('missing relroot')
        filename = os.path.relpath(filename, relroot)
    wenn filename.startswith(_badprefix):
        raise ValueError(f'bad filename {orig!r} (resolves beyond relative root')
    return filename


def match_path_tail(path1, path2):
    """Return True wenn one path ends the other."""
    wenn path1 == path2:
        return True
    wenn os.path.isabs(path1):
        wenn os.path.isabs(path2):
            return False
        return _match_tail(path1, path2)
    sowenn os.path.isabs(path2):
        return _match_tail(path2, path1)
    sonst:
        return _match_tail(path1, path2) or _match_tail(path2, path1)


def _match_tail(path, tail):
    assert not os.path.isabs(tail), repr(tail)
    return path.endswith(os.path.sep + tail)


##################################
# find files

def match_glob(filename, pattern):
    wenn fnmatch.fnmatch(filename, pattern):
        return True

    # fnmatch doesn't handle ** quite right.  It will not match the
    # following:
    #
    #  ('x/spam.py', 'x/**/*.py')
    #  ('spam.py', '**/*.py')
    #
    # though it *will* match the following:
    #
    #  ('x/y/spam.py', 'x/**/*.py')
    #  ('x/spam.py', '**/*.py')

    wenn '**/' not in pattern:
        return False

    # We only accommodate the single-"**" case.
    return fnmatch.fnmatch(filename, pattern.replace('**/', '', 1))


def process_filenames(filenames, *,
                      start=None,
                      include=None,
                      exclude=None,
                      relroot=USE_CWD,
                      ):
    wenn relroot and relroot is not USE_CWD:
        relroot = os.path.abspath(relroot)
    wenn start:
        start = fix_filename(start, relroot, fixroot=False)
    wenn include:
        include = set(fix_filename(v, relroot, fixroot=False)
                      fuer v in include)
    wenn exclude:
        exclude = set(fix_filename(v, relroot, fixroot=False)
                      fuer v in exclude)

    onempty = Exception('no filenames provided')
    fuer filename, solo in iter_many(filenames, onempty):
        filename = fix_filename(filename, relroot, fixroot=False)
        relfile = format_filename(filename, relroot, fixroot=False, normalize=False)
        check, start = _get_check(filename, start, include, exclude)
        yield filename, relfile, check, solo


def expand_filenames(filenames):
    fuer filename in filenames:
        # XXX Do we need to use glob.escape (a la commit 9355868458, GH-20994)?
        wenn '**/' in filename:
            yield from glob.glob(filename.replace('**/', ''))
        yield from glob.glob(filename)


def _get_check(filename, start, include, exclude):
    wenn start and filename != start:
        return (lambda: '<skipped>'), start
    sonst:
        def check():
            wenn _is_excluded(filename, exclude, include):
                return '<excluded>'
            return None
        return check, None


def _is_excluded(filename, exclude, include):
    wenn include:
        fuer included in include:
            wenn match_glob(filename, included):
                return False
        return True
    sowenn exclude:
        fuer excluded in exclude:
            wenn match_glob(filename, excluded):
                return True
        return False
    sonst:
        return False


def _walk_tree(root, *,
               _walk=os.walk,
               ):
    # A wrapper around os.walk that resolves the filenames.
    fuer parent, _, names in _walk(root):
        fuer name in names:
            yield os.path.join(parent, name)


def walk_tree(root, *,
              suffix=None,
              walk=_walk_tree,
              ):
    """Yield each file in the tree under the given directory name.

    If "suffix" is provided then only files with that suffix will
    be included.
    """
    wenn suffix and not isinstance(suffix, str):
        raise ValueError('suffix must be a string')

    fuer filename in walk(root):
        wenn suffix and not filename.endswith(suffix):
            continue
        yield filename


def glob_tree(root, *,
              suffix=None,
              _glob=glob.iglob,
              ):
    """Yield each file in the tree under the given directory name.

    If "suffix" is provided then only files with that suffix will
    be included.
    """
    suffix = suffix or ''
    wenn not isinstance(suffix, str):
        raise ValueError('suffix must be a string')

    fuer filename in _glob(f'{root}/*{suffix}'):
        yield filename
    fuer filename in _glob(f'{root}/**/*{suffix}'):
        yield filename


def iter_files(root, suffix=None, relparent=None, *,
               get_files=os.walk,
               _glob=glob_tree,
               _walk=walk_tree,
               ):
    """Yield each file in the tree under the given directory name.

    If "root" is a non-string iterable then do the same fuer each of
    those trees.

    If "suffix" is provided then only files with that suffix will
    be included.

    wenn "relparent" is provided then it is used to resolve each
    filename as a relative path.
    """
    wenn not isinstance(root, str):
        roots = root
        fuer root in roots:
            yield from iter_files(root, suffix, relparent,
                                  get_files=get_files,
                                  _glob=_glob, _walk=_walk)
        return

    # Use the right "walk" function.
    wenn get_files in (glob.glob, glob.iglob, glob_tree):
        get_files = _glob
    sonst:
        _files = _walk_tree wenn get_files in (os.walk, walk_tree) sonst get_files
        get_files = (lambda *a, **k: _walk(*a, walk=_files, **k))

    # Handle a single suffix.
    wenn suffix and not isinstance(suffix, str):
        filenames = get_files(root)
        suffix = tuple(suffix)
    sonst:
        filenames = get_files(root, suffix=suffix)
        suffix = None

    fuer filename in filenames:
        wenn suffix and not isinstance(suffix, str):  # multiple suffixes
            wenn not filename.endswith(suffix):
                continue
        wenn relparent:
            filename = os.path.relpath(filename, relparent)
        yield filename


def iter_files_by_suffix(root, suffixes, relparent=None, *,
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
        yield from _iter_files(root, suffix, relparent)


##################################
# file info

# XXX posix-only?

S_IRANY = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
S_IWANY = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
S_IXANY = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH


def is_readable(file, *, user=None, check=False):
    filename, st, mode = _get_file_info(file)
    wenn check:
        try:
            okay = _check_file(filename, S_IRANY)
        except NotImplementedError:
            okay = NotImplemented
        wenn okay is not NotImplemented:
            return okay
        # Fall back to checking the mode.
    return _check_mode(st, mode, S_IRANY, user)


def is_writable(file, *, user=None, check=False):
    filename, st, mode = _get_file_info(file)
    wenn check:
        try:
            okay = _check_file(filename, S_IWANY)
        except NotImplementedError:
            okay = NotImplemented
        wenn okay is not NotImplemented:
            return okay
        # Fall back to checking the mode.
    return _check_mode(st, mode, S_IWANY, user)


def is_executable(file, *, user=None, check=False):
    filename, st, mode = _get_file_info(file)
    wenn check:
        try:
            okay = _check_file(filename, S_IXANY)
        except NotImplementedError:
            okay = NotImplemented
        wenn okay is not NotImplemented:
            return okay
        # Fall back to checking the mode.
    return _check_mode(st, mode, S_IXANY, user)


def _get_file_info(file):
    filename = st = mode = None
    wenn isinstance(file, int):
        mode = file
    sowenn isinstance(file, os.stat_result):
        st = file
    sonst:
        wenn isinstance(file, str):
            filename = file
        sowenn hasattr(file, 'name') and os.path.exists(file.name):
            filename = file.name
        sonst:
            raise NotImplementedError(file)
        st = os.stat(filename)
    return filename, st, mode or st.st_mode


def _check_file(filename, check):
    wenn not isinstance(filename, str):
        raise Exception(f'filename required to check file, got {filename}')
    wenn check & S_IRANY:
        flags = os.O_RDONLY
    sowenn check & S_IWANY:
        flags = os.O_WRONLY
    sowenn check & S_IXANY:
        # We can worry about S_IXANY later
        return NotImplemented
    sonst:
        raise NotImplementedError(check)

    try:
        fd = os.open(filename, flags)
    except PermissionError:
        return False
    # We do not ignore other exceptions.
    sonst:
        os.close(fd)
        return True


def _get_user_info(user):
    import pwd
    username = uid = gid = groups = None
    wenn user is None:
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
            raise NotImplementedError(user)
        gid = entry.pw_gid
        os.getgrouplist(username, gid)
    return username, uid, gid, groups


def _check_mode(st, mode, check, user):
    orig = check
    _, uid, gid, groups = _get_user_info(user)
    wenn check & S_IRANY:
        check -= S_IRANY
        matched = False
        wenn mode & stat.S_IRUSR:
            wenn st.st_uid == uid:
                matched = True
        wenn mode & stat.S_IRGRP:
            wenn st.st_uid == gid or st.st_uid in groups:
                matched = True
        wenn mode & stat.S_IROTH:
            matched = True
        wenn not matched:
            return False
    wenn check & S_IWANY:
        check -= S_IWANY
        matched = False
        wenn mode & stat.S_IWUSR:
            wenn st.st_uid == uid:
                matched = True
        wenn mode & stat.S_IWGRP:
            wenn st.st_uid == gid or st.st_uid in groups:
                matched = True
        wenn mode & stat.S_IWOTH:
            matched = True
        wenn not matched:
            return False
    wenn check & S_IXANY:
        check -= S_IXANY
        matched = False
        wenn mode & stat.S_IXUSR:
            wenn st.st_uid == uid:
                matched = True
        wenn mode & stat.S_IXGRP:
            wenn st.st_uid == gid or st.st_uid in groups:
                matched = True
        wenn mode & stat.S_IXOTH:
            matched = True
        wenn not matched:
            return False
    wenn check:
        raise NotImplementedError((orig, check))
    return True
