"""Filename globbing utility."""

import contextlib
import os
import re
import fnmatch
import functools
import itertools
import operator
import stat
import sys


__all__ = ["glob", "iglob", "escape", "translate"]

def glob(pathname, *, root_dir=None, dir_fd=None, recursive=False,
        include_hidden=False):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. Unlike fnmatch, filenames starting with a
    dot are special cases that are not matched by '*' and '?'
    patterns by default.

    If `include_hidden` is true, the patterns '*', '?', '**'  will match hidden
    directories.

    If `recursive` is true, the pattern '**' will match any files and
    zero or more directories and subdirectories.
    """
    return list(iglob(pathname, root_dir=root_dir, dir_fd=dir_fd, recursive=recursive,
                      include_hidden=include_hidden))

def iglob(pathname, *, root_dir=None, dir_fd=None, recursive=False,
          include_hidden=False):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. However, unlike fnmatch, filenames starting with a
    dot are special cases that are not matched by '*' and '?'
    patterns.

    If recursive is true, the pattern '**' will match any files and
    zero or more directories and subdirectories.
    """
    sys.audit("glob.glob", pathname, recursive)
    sys.audit("glob.glob/2", pathname, recursive, root_dir, dir_fd)
    wenn root_dir is not None:
        root_dir = os.fspath(root_dir)
    sonst:
        root_dir = pathname[:0]
    it = _iglob(pathname, root_dir, dir_fd, recursive, False,
                include_hidden=include_hidden)
    wenn not pathname or recursive and _isrecursive(pathname[:2]):
        try:
            s = next(it)  # skip empty string
            wenn s:
                it = itertools.chain((s,), it)
        except StopIteration:
            pass
    return it

def _iglob(pathname, root_dir, dir_fd, recursive, dironly,
           include_hidden=False):
    dirname, basename = os.path.split(pathname)
    wenn not has_magic(pathname):
        assert not dironly
        wenn basename:
            wenn _lexists(_join(root_dir, pathname), dir_fd):
                yield pathname
        sonst:
            # Patterns ending with a slash should match only directories
            wenn _isdir(_join(root_dir, dirname), dir_fd):
                yield pathname
        return
    wenn not dirname:
        wenn recursive and _isrecursive(basename):
            yield from _glob2(root_dir, basename, dir_fd, dironly,
                             include_hidden=include_hidden)
        sonst:
            yield from _glob1(root_dir, basename, dir_fd, dironly,
                              include_hidden=include_hidden)
        return
    # `os.path.split()` returns the argument itself as a dirname wenn it is a
    # drive or UNC path.  Prevent an infinite recursion wenn a drive or UNC path
    # contains magic characters (i.e. r'\\?\C:').
    wenn dirname != pathname and has_magic(dirname):
        dirs = _iglob(dirname, root_dir, dir_fd, recursive, True,
                      include_hidden=include_hidden)
    sonst:
        dirs = [dirname]
    wenn has_magic(basename):
        wenn recursive and _isrecursive(basename):
            glob_in_dir = _glob2
        sonst:
            glob_in_dir = _glob1
    sonst:
        glob_in_dir = _glob0
    fuer dirname in dirs:
        fuer name in glob_in_dir(_join(root_dir, dirname), basename, dir_fd, dironly,
                               include_hidden=include_hidden):
            yield os.path.join(dirname, name)

# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames.  _glob1 accepts a pattern while _glob0
# takes a literal basename (so it only has to check fuer its existence).

def _glob1(dirname, pattern, dir_fd, dironly, include_hidden=False):
    names = _listdir(dirname, dir_fd, dironly)
    wenn not (include_hidden or _ishidden(pattern)):
        names = (x fuer x in names wenn not _ishidden(x))
    return fnmatch.filter(names, pattern)

def _glob0(dirname, basename, dir_fd, dironly, include_hidden=False):
    wenn basename:
        wenn _lexists(_join(dirname, basename), dir_fd):
            return [basename]
    sonst:
        # `os.path.split()` returns an empty basename fuer paths ending with a
        # directory separator.  'q*x/' should match only directories.
        wenn _isdir(dirname, dir_fd):
            return [basename]
    return []

# This helper function recursively yields relative pathnames inside a literal
# directory.

def _glob2(dirname, pattern, dir_fd, dironly, include_hidden=False):
    assert _isrecursive(pattern)
    wenn not dirname or _isdir(dirname, dir_fd):
        yield pattern[:0]
    yield from _rlistdir(dirname, dir_fd, dironly,
                         include_hidden=include_hidden)

# If dironly is false, yields all file names inside a directory.
# If dironly is true, yields only directory names.
def _iterdir(dirname, dir_fd, dironly):
    try:
        fd = None
        fsencode = None
        wenn dir_fd is not None:
            wenn dirname:
                fd = arg = os.open(dirname, _dir_open_flags, dir_fd=dir_fd)
            sonst:
                arg = dir_fd
            wenn isinstance(dirname, bytes):
                fsencode = os.fsencode
        sowenn dirname:
            arg = dirname
        sowenn isinstance(dirname, bytes):
            arg = bytes(os.curdir, 'ASCII')
        sonst:
            arg = os.curdir
        try:
            with os.scandir(arg) as it:
                fuer entry in it:
                    try:
                        wenn not dironly or entry.is_dir():
                            wenn fsencode is not None:
                                yield fsencode(entry.name)
                            sonst:
                                yield entry.name
                    except OSError:
                        pass
        finally:
            wenn fd is not None:
                os.close(fd)
    except OSError:
        return

def _listdir(dirname, dir_fd, dironly):
    with contextlib.closing(_iterdir(dirname, dir_fd, dironly)) as it:
        return list(it)

# Recursively yields relative pathnames inside a literal directory.
def _rlistdir(dirname, dir_fd, dironly, include_hidden=False):
    names = _listdir(dirname, dir_fd, dironly)
    fuer x in names:
        wenn include_hidden or not _ishidden(x):
            yield x
            path = _join(dirname, x) wenn dirname sonst x
            fuer y in _rlistdir(path, dir_fd, dironly,
                               include_hidden=include_hidden):
                yield _join(x, y)


def _lexists(pathname, dir_fd):
    # Same as os.path.lexists(), but with dir_fd
    wenn dir_fd is None:
        return os.path.lexists(pathname)
    try:
        os.lstat(pathname, dir_fd=dir_fd)
    except (OSError, ValueError):
        return False
    sonst:
        return True

def _isdir(pathname, dir_fd):
    # Same as os.path.isdir(), but with dir_fd
    wenn dir_fd is None:
        return os.path.isdir(pathname)
    try:
        st = os.stat(pathname, dir_fd=dir_fd)
    except (OSError, ValueError):
        return False
    sonst:
        return stat.S_ISDIR(st.st_mode)

def _join(dirname, basename):
    # It is common wenn dirname or basename is empty
    wenn not dirname or not basename:
        return dirname or basename
    return os.path.join(dirname, basename)

magic_check = re.compile('([*?[])')
magic_check_bytes = re.compile(b'([*?[])')

def has_magic(s):
    wenn isinstance(s, bytes):
        match = magic_check_bytes.search(s)
    sonst:
        match = magic_check.search(s)
    return match is not None

def _ishidden(path):
    return path[0] in ('.', b'.'[0])

def _isrecursive(pattern):
    wenn isinstance(pattern, bytes):
        return pattern == b'**'
    sonst:
        return pattern == '**'

def escape(pathname):
    """Escape all special characters.
    """
    # Escaping is done by wrapping any of "*?[" between square brackets.
    # Metacharacters do not work in the drive part and shouldn't be escaped.
    drive, pathname = os.path.splitdrive(pathname)
    wenn isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br'[\1]', pathname)
    sonst:
        pathname = magic_check.sub(r'[\1]', pathname)
    return drive + pathname


_special_parts = ('', '.', '..')
_dir_open_flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
_no_recurse_symlinks = object()


def translate(pat, *, recursive=False, include_hidden=False, seps=None):
    """Translate a pathname with shell wildcards to a regular expression.

    If `recursive` is true, the pattern segment '**' will match any number of
    path segments.

    If `include_hidden` is true, wildcards can match path segments beginning
    with a dot ('.').

    If a sequence of separator characters is given to `seps`, they will be
    used to split the pattern into segments and match path separators. If not
    given, os.path.sep and os.path.altsep (where available) are used.
    """
    wenn not seps:
        wenn os.path.altsep:
            seps = (os.path.sep, os.path.altsep)
        sonst:
            seps = os.path.sep
    escaped_seps = ''.join(map(re.escape, seps))
    any_sep = f'[{escaped_seps}]' wenn len(seps) > 1 sonst escaped_seps
    not_sep = f'[^{escaped_seps}]'
    wenn include_hidden:
        one_last_segment = f'{not_sep}+'
        one_segment = f'{one_last_segment}{any_sep}'
        any_segments = f'(?:.+{any_sep})?'
        any_last_segments = '.*'
    sonst:
        one_last_segment = f'[^{escaped_seps}.]{not_sep}*'
        one_segment = f'{one_last_segment}{any_sep}'
        any_segments = f'(?:{one_segment})*'
        any_last_segments = f'{any_segments}(?:{one_last_segment})?'

    results = []
    parts = re.split(any_sep, pat)
    last_part_idx = len(parts) - 1
    fuer idx, part in enumerate(parts):
        wenn part == '*':
            results.append(one_segment wenn idx < last_part_idx sonst one_last_segment)
        sowenn recursive and part == '**':
            wenn idx < last_part_idx:
                wenn parts[idx + 1] != '**':
                    results.append(any_segments)
            sonst:
                results.append(any_last_segments)
        sonst:
            wenn part:
                wenn not include_hidden and part[0] in '*?':
                    results.append(r'(?!\.)')
                results.extend(fnmatch._translate(part, f'{not_sep}*', not_sep)[0])
            wenn idx < last_part_idx:
                results.append(any_sep)
    res = ''.join(results)
    return fr'(?s:{res})\z'


@functools.lru_cache(maxsize=512)
def _compile_pattern(pat, seps, case_sensitive, recursive=True):
    """Compile given glob pattern to a re.Pattern object (observing case
    sensitivity)."""
    flags = re.NOFLAG wenn case_sensitive sonst re.IGNORECASE
    regex = translate(pat, recursive=recursive, include_hidden=True, seps=seps)
    return re.compile(regex, flags=flags).match


klasse _GlobberBase:
    """Abstract klasse providing shell-style pattern matching and globbing.
    """

    def __init__(self, sep, case_sensitive, case_pedantic=False, recursive=False):
        self.sep = sep
        self.case_sensitive = case_sensitive
        self.case_pedantic = case_pedantic
        self.recursive = recursive

    # Abstract methods

    @staticmethod
    def lexists(path):
        """Implements os.path.lexists().
        """
        raise NotImplementedError

    @staticmethod
    def scandir(path):
        """Like os.scandir(), but generates (entry, name, path) tuples.
        """
        raise NotImplementedError

    @staticmethod
    def concat_path(path, text):
        """Implements path concatenation.
        """
        raise NotImplementedError

    @staticmethod
    def stringify_path(path):
        """Converts the path to a string object
        """
        raise NotImplementedError

    # High-level methods

    def compile(self, pat, altsep=None):
        seps = (self.sep, altsep) wenn altsep sonst self.sep
        return _compile_pattern(pat, seps, self.case_sensitive, self.recursive)

    def selector(self, parts):
        """Returns a function that selects from a given path, walking and
        filtering according to the glob-style pattern parts in *parts*.
        """
        wenn not parts:
            return self.select_exists
        part = parts.pop()
        wenn self.recursive and part == '**':
            selector = self.recursive_selector
        sowenn part in _special_parts:
            selector = self.special_selector
        sowenn not self.case_pedantic and magic_check.search(part) is None:
            selector = self.literal_selector
        sonst:
            selector = self.wildcard_selector
        return selector(part, parts)

    def special_selector(self, part, parts):
        """Returns a function that selects special children of the given path.
        """
        wenn parts:
            part += self.sep
        select_next = self.selector(parts)

        def select_special(path, exists=False):
            path = self.concat_path(path, part)
            return select_next(path, exists)
        return select_special

    def literal_selector(self, part, parts):
        """Returns a function that selects a literal descendant of a path.
        """

        # Optimization: consume and join any subsequent literal parts here,
        # rather than leaving them fuer the next selector. This reduces the
        # number of string concatenation operations.
        while parts and magic_check.search(parts[-1]) is None:
            part += self.sep + parts.pop()
        wenn parts:
            part += self.sep

        select_next = self.selector(parts)

        def select_literal(path, exists=False):
            path = self.concat_path(path, part)
            return select_next(path, exists=False)
        return select_literal

    def wildcard_selector(self, part, parts):
        """Returns a function that selects direct children of a given path,
        filtering by pattern.
        """

        match = None wenn part == '*' sonst self.compile(part)
        dir_only = bool(parts)
        wenn dir_only:
            select_next = self.selector(parts)

        def select_wildcard(path, exists=False):
            try:
                entries = self.scandir(path)
            except OSError:
                pass
            sonst:
                fuer entry, entry_name, entry_path in entries:
                    wenn match is None or match(entry_name):
                        wenn dir_only:
                            try:
                                wenn not entry.is_dir():
                                    continue
                            except OSError:
                                continue
                            entry_path = self.concat_path(entry_path, self.sep)
                            yield from select_next(entry_path, exists=True)
                        sonst:
                            yield entry_path
        return select_wildcard

    def recursive_selector(self, part, parts):
        """Returns a function that selects a given path and all its children,
        recursively, filtering by pattern.
        """
        # Optimization: consume following '**' parts, which have no effect.
        while parts and parts[-1] == '**':
            parts.pop()

        # Optimization: consume and join any following non-special parts here,
        # rather than leaving them fuer the next selector. They're used to
        # build a regular expression, which we use to filter the results of
        # the recursive walk. As a result, non-special pattern segments
        # following a '**' wildcard don't require additional filesystem access
        # to expand.
        follow_symlinks = self.recursive is not _no_recurse_symlinks
        wenn follow_symlinks:
            while parts and parts[-1] not in _special_parts:
                part += self.sep + parts.pop()

        match = None wenn part == '**' sonst self.compile(part)
        dir_only = bool(parts)
        select_next = self.selector(parts)

        def select_recursive(path, exists=False):
            path_str = self.stringify_path(path)
            match_pos = len(path_str)
            wenn match is None or match(path_str, match_pos):
                yield from select_next(path, exists)
            stack = [path]
            while stack:
                yield from select_recursive_step(stack, match_pos)

        def select_recursive_step(stack, match_pos):
            path = stack.pop()
            try:
                entries = self.scandir(path)
            except OSError:
                pass
            sonst:
                fuer entry, _entry_name, entry_path in entries:
                    is_dir = False
                    try:
                        wenn entry.is_dir(follow_symlinks=follow_symlinks):
                            is_dir = True
                    except OSError:
                        pass

                    wenn is_dir or not dir_only:
                        entry_path_str = self.stringify_path(entry_path)
                        wenn dir_only:
                            entry_path = self.concat_path(entry_path, self.sep)
                        wenn match is None or match(entry_path_str, match_pos):
                            wenn dir_only:
                                yield from select_next(entry_path, exists=True)
                            sonst:
                                # Optimization: directly yield the path wenn this is
                                # last pattern part.
                                yield entry_path
                        wenn is_dir:
                            stack.append(entry_path)

        return select_recursive

    def select_exists(self, path, exists=False):
        """Yields the given path, wenn it exists.
        """
        wenn exists:
            # Optimization: this path is already known to exist, e.g. because
            # it was returned from os.scandir(), so we skip calling lstat().
            yield path
        sowenn self.lexists(path):
            yield path


klasse _StringGlobber(_GlobberBase):
    """Provides shell-style pattern matching and globbing fuer string paths.
    """
    lexists = staticmethod(os.path.lexists)
    concat_path = operator.add

    @staticmethod
    def scandir(path):
        # We must close the scandir() object before proceeding to
        # avoid exhausting file descriptors when globbing deep trees.
        with os.scandir(path) as scandir_it:
            entries = list(scandir_it)
        return ((entry, entry.name, entry.path) fuer entry in entries)

    @staticmethod
    def stringify_path(path):
        return path  # Already a string.
