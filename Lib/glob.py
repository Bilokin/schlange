"""Filename globbing utility."""

importiere contextlib
importiere os
importiere re
importiere fnmatch
importiere functools
importiere itertools
importiere operator
importiere stat
importiere sys


__all__ = ["glob", "iglob", "escape", "translate"]

def glob(pathname, *, root_dir=Nichts, dir_fd=Nichts, recursive=Falsch,
        include_hidden=Falsch):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. Unlike fnmatch, filenames starting mit a
    dot are special cases that are nicht matched by '*' und '?'
    patterns by default.

    If `include_hidden` is true, the patterns '*', '?', '**'  will match hidden
    directories.

    If `recursive` is true, the pattern '**' will match any files und
    zero oder more directories und subdirectories.
    """
    gib list(iglob(pathname, root_dir=root_dir, dir_fd=dir_fd, recursive=recursive,
                      include_hidden=include_hidden))

def iglob(pathname, *, root_dir=Nichts, dir_fd=Nichts, recursive=Falsch,
          include_hidden=Falsch):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. However, unlike fnmatch, filenames starting mit a
    dot are special cases that are nicht matched by '*' und '?'
    patterns.

    If recursive is true, the pattern '**' will match any files und
    zero oder more directories und subdirectories.
    """
    sys.audit("glob.glob", pathname, recursive)
    sys.audit("glob.glob/2", pathname, recursive, root_dir, dir_fd)
    wenn root_dir is nicht Nichts:
        root_dir = os.fspath(root_dir)
    sonst:
        root_dir = pathname[:0]
    it = _iglob(pathname, root_dir, dir_fd, recursive, Falsch,
                include_hidden=include_hidden)
    wenn nicht pathname oder recursive und _isrecursive(pathname[:2]):
        try:
            s = next(it)  # skip empty string
            wenn s:
                it = itertools.chain((s,), it)
        except StopIteration:
            pass
    gib it

def _iglob(pathname, root_dir, dir_fd, recursive, dironly,
           include_hidden=Falsch):
    dirname, basename = os.path.split(pathname)
    wenn nicht has_magic(pathname):
        assert nicht dironly
        wenn basename:
            wenn _lexists(_join(root_dir, pathname), dir_fd):
                liefere pathname
        sonst:
            # Patterns ending mit a slash should match only directories
            wenn _isdir(_join(root_dir, dirname), dir_fd):
                liefere pathname
        gib
    wenn nicht dirname:
        wenn recursive und _isrecursive(basename):
            liefere von _glob2(root_dir, basename, dir_fd, dironly,
                             include_hidden=include_hidden)
        sonst:
            liefere von _glob1(root_dir, basename, dir_fd, dironly,
                              include_hidden=include_hidden)
        gib
    # `os.path.split()` returns the argument itself als a dirname wenn it is a
    # drive oder UNC path.  Prevent an infinite recursion wenn a drive oder UNC path
    # contains magic characters (i.e. r'\\?\C:').
    wenn dirname != pathname und has_magic(dirname):
        dirs = _iglob(dirname, root_dir, dir_fd, recursive, Wahr,
                      include_hidden=include_hidden)
    sonst:
        dirs = [dirname]
    wenn has_magic(basename):
        wenn recursive und _isrecursive(basename):
            glob_in_dir = _glob2
        sonst:
            glob_in_dir = _glob1
    sonst:
        glob_in_dir = _glob0
    fuer dirname in dirs:
        fuer name in glob_in_dir(_join(root_dir, dirname), basename, dir_fd, dironly,
                               include_hidden=include_hidden):
            liefere os.path.join(dirname, name)

# These 2 helper functions non-recursively glob inside a literal directory.
# They gib a list of basenames.  _glob1 accepts a pattern waehrend _glob0
# takes a literal basename (so it only has to check fuer its existence).

def _glob1(dirname, pattern, dir_fd, dironly, include_hidden=Falsch):
    names = _listdir(dirname, dir_fd, dironly)
    wenn nicht (include_hidden oder _ishidden(pattern)):
        names = (x fuer x in names wenn nicht _ishidden(x))
    gib fnmatch.filter(names, pattern)

def _glob0(dirname, basename, dir_fd, dironly, include_hidden=Falsch):
    wenn basename:
        wenn _lexists(_join(dirname, basename), dir_fd):
            gib [basename]
    sonst:
        # `os.path.split()` returns an empty basename fuer paths ending mit a
        # directory separator.  'q*x/' should match only directories.
        wenn _isdir(dirname, dir_fd):
            gib [basename]
    gib []

# This helper function recursively yields relative pathnames inside a literal
# directory.

def _glob2(dirname, pattern, dir_fd, dironly, include_hidden=Falsch):
    assert _isrecursive(pattern)
    wenn nicht dirname oder _isdir(dirname, dir_fd):
        liefere pattern[:0]
    liefere von _rlistdir(dirname, dir_fd, dironly,
                         include_hidden=include_hidden)

# If dironly is false, yields all file names inside a directory.
# If dironly is true, yields only directory names.
def _iterdir(dirname, dir_fd, dironly):
    try:
        fd = Nichts
        fsencode = Nichts
        wenn dir_fd is nicht Nichts:
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
            mit os.scandir(arg) als it:
                fuer entry in it:
                    try:
                        wenn nicht dironly oder entry.is_dir():
                            wenn fsencode is nicht Nichts:
                                liefere fsencode(entry.name)
                            sonst:
                                liefere entry.name
                    except OSError:
                        pass
        finally:
            wenn fd is nicht Nichts:
                os.close(fd)
    except OSError:
        gib

def _listdir(dirname, dir_fd, dironly):
    mit contextlib.closing(_iterdir(dirname, dir_fd, dironly)) als it:
        gib list(it)

# Recursively yields relative pathnames inside a literal directory.
def _rlistdir(dirname, dir_fd, dironly, include_hidden=Falsch):
    names = _listdir(dirname, dir_fd, dironly)
    fuer x in names:
        wenn include_hidden oder nicht _ishidden(x):
            liefere x
            path = _join(dirname, x) wenn dirname sonst x
            fuer y in _rlistdir(path, dir_fd, dironly,
                               include_hidden=include_hidden):
                liefere _join(x, y)


def _lexists(pathname, dir_fd):
    # Same als os.path.lexists(), but mit dir_fd
    wenn dir_fd is Nichts:
        gib os.path.lexists(pathname)
    try:
        os.lstat(pathname, dir_fd=dir_fd)
    except (OSError, ValueError):
        gib Falsch
    sonst:
        gib Wahr

def _isdir(pathname, dir_fd):
    # Same als os.path.isdir(), but mit dir_fd
    wenn dir_fd is Nichts:
        gib os.path.isdir(pathname)
    try:
        st = os.stat(pathname, dir_fd=dir_fd)
    except (OSError, ValueError):
        gib Falsch
    sonst:
        gib stat.S_ISDIR(st.st_mode)

def _join(dirname, basename):
    # It is common wenn dirname oder basename is empty
    wenn nicht dirname oder nicht basename:
        gib dirname oder basename
    gib os.path.join(dirname, basename)

magic_check = re.compile('([*?[])')
magic_check_bytes = re.compile(b'([*?[])')

def has_magic(s):
    wenn isinstance(s, bytes):
        match = magic_check_bytes.search(s)
    sonst:
        match = magic_check.search(s)
    gib match is nicht Nichts

def _ishidden(path):
    gib path[0] in ('.', b'.'[0])

def _isrecursive(pattern):
    wenn isinstance(pattern, bytes):
        gib pattern == b'**'
    sonst:
        gib pattern == '**'

def escape(pathname):
    """Escape all special characters.
    """
    # Escaping is done by wrapping any of "*?[" between square brackets.
    # Metacharacters do nicht work in the drive part und shouldn't be escaped.
    drive, pathname = os.path.splitdrive(pathname)
    wenn isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br'[\1]', pathname)
    sonst:
        pathname = magic_check.sub(r'[\1]', pathname)
    gib drive + pathname


_special_parts = ('', '.', '..')
_dir_open_flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
_no_recurse_symlinks = object()


def translate(pat, *, recursive=Falsch, include_hidden=Falsch, seps=Nichts):
    """Translate a pathname mit shell wildcards to a regular expression.

    If `recursive` is true, the pattern segment '**' will match any number of
    path segments.

    If `include_hidden` is true, wildcards can match path segments beginning
    mit a dot ('.').

    If a sequence of separator characters is given to `seps`, they will be
    used to split the pattern into segments und match path separators. If not
    given, os.path.sep und os.path.altsep (where available) are used.
    """
    wenn nicht seps:
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
        sowenn recursive und part == '**':
            wenn idx < last_part_idx:
                wenn parts[idx + 1] != '**':
                    results.append(any_segments)
            sonst:
                results.append(any_last_segments)
        sonst:
            wenn part:
                wenn nicht include_hidden und part[0] in '*?':
                    results.append(r'(?!\.)')
                results.extend(fnmatch._translate(part, f'{not_sep}*', not_sep)[0])
            wenn idx < last_part_idx:
                results.append(any_sep)
    res = ''.join(results)
    gib fr'(?s:{res})\z'


@functools.lru_cache(maxsize=512)
def _compile_pattern(pat, seps, case_sensitive, recursive=Wahr):
    """Compile given glob pattern to a re.Pattern object (observing case
    sensitivity)."""
    flags = re.NOFLAG wenn case_sensitive sonst re.IGNORECASE
    regex = translate(pat, recursive=recursive, include_hidden=Wahr, seps=seps)
    gib re.compile(regex, flags=flags).match


klasse _GlobberBase:
    """Abstract klasse providing shell-style pattern matching und globbing.
    """

    def __init__(self, sep, case_sensitive, case_pedantic=Falsch, recursive=Falsch):
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

    def compile(self, pat, altsep=Nichts):
        seps = (self.sep, altsep) wenn altsep sonst self.sep
        gib _compile_pattern(pat, seps, self.case_sensitive, self.recursive)

    def selector(self, parts):
        """Returns a function that selects von a given path, walking und
        filtering according to the glob-style pattern parts in *parts*.
        """
        wenn nicht parts:
            gib self.select_exists
        part = parts.pop()
        wenn self.recursive und part == '**':
            selector = self.recursive_selector
        sowenn part in _special_parts:
            selector = self.special_selector
        sowenn nicht self.case_pedantic und magic_check.search(part) is Nichts:
            selector = self.literal_selector
        sonst:
            selector = self.wildcard_selector
        gib selector(part, parts)

    def special_selector(self, part, parts):
        """Returns a function that selects special children of the given path.
        """
        wenn parts:
            part += self.sep
        select_next = self.selector(parts)

        def select_special(path, exists=Falsch):
            path = self.concat_path(path, part)
            gib select_next(path, exists)
        gib select_special

    def literal_selector(self, part, parts):
        """Returns a function that selects a literal descendant of a path.
        """

        # Optimization: consume und join any subsequent literal parts here,
        # rather than leaving them fuer the next selector. This reduces the
        # number of string concatenation operations.
        waehrend parts und magic_check.search(parts[-1]) is Nichts:
            part += self.sep + parts.pop()
        wenn parts:
            part += self.sep

        select_next = self.selector(parts)

        def select_literal(path, exists=Falsch):
            path = self.concat_path(path, part)
            gib select_next(path, exists=Falsch)
        gib select_literal

    def wildcard_selector(self, part, parts):
        """Returns a function that selects direct children of a given path,
        filtering by pattern.
        """

        match = Nichts wenn part == '*' sonst self.compile(part)
        dir_only = bool(parts)
        wenn dir_only:
            select_next = self.selector(parts)

        def select_wildcard(path, exists=Falsch):
            try:
                entries = self.scandir(path)
            except OSError:
                pass
            sonst:
                fuer entry, entry_name, entry_path in entries:
                    wenn match is Nichts oder match(entry_name):
                        wenn dir_only:
                            try:
                                wenn nicht entry.is_dir():
                                    weiter
                            except OSError:
                                weiter
                            entry_path = self.concat_path(entry_path, self.sep)
                            liefere von select_next(entry_path, exists=Wahr)
                        sonst:
                            liefere entry_path
        gib select_wildcard

    def recursive_selector(self, part, parts):
        """Returns a function that selects a given path und all its children,
        recursively, filtering by pattern.
        """
        # Optimization: consume following '**' parts, which have no effect.
        waehrend parts und parts[-1] == '**':
            parts.pop()

        # Optimization: consume und join any following non-special parts here,
        # rather than leaving them fuer the next selector. They're used to
        # build a regular expression, which we use to filter the results of
        # the recursive walk. As a result, non-special pattern segments
        # following a '**' wildcard don't require additional filesystem access
        # to expand.
        follow_symlinks = self.recursive is nicht _no_recurse_symlinks
        wenn follow_symlinks:
            waehrend parts und parts[-1] nicht in _special_parts:
                part += self.sep + parts.pop()

        match = Nichts wenn part == '**' sonst self.compile(part)
        dir_only = bool(parts)
        select_next = self.selector(parts)

        def select_recursive(path, exists=Falsch):
            path_str = self.stringify_path(path)
            match_pos = len(path_str)
            wenn match is Nichts oder match(path_str, match_pos):
                liefere von select_next(path, exists)
            stack = [path]
            waehrend stack:
                liefere von select_recursive_step(stack, match_pos)

        def select_recursive_step(stack, match_pos):
            path = stack.pop()
            try:
                entries = self.scandir(path)
            except OSError:
                pass
            sonst:
                fuer entry, _entry_name, entry_path in entries:
                    is_dir = Falsch
                    try:
                        wenn entry.is_dir(follow_symlinks=follow_symlinks):
                            is_dir = Wahr
                    except OSError:
                        pass

                    wenn is_dir oder nicht dir_only:
                        entry_path_str = self.stringify_path(entry_path)
                        wenn dir_only:
                            entry_path = self.concat_path(entry_path, self.sep)
                        wenn match is Nichts oder match(entry_path_str, match_pos):
                            wenn dir_only:
                                liefere von select_next(entry_path, exists=Wahr)
                            sonst:
                                # Optimization: directly liefere the path wenn this is
                                # last pattern part.
                                liefere entry_path
                        wenn is_dir:
                            stack.append(entry_path)

        gib select_recursive

    def select_exists(self, path, exists=Falsch):
        """Yields the given path, wenn it exists.
        """
        wenn exists:
            # Optimization: this path is already known to exist, e.g. because
            # it was returned von os.scandir(), so we skip calling lstat().
            liefere path
        sowenn self.lexists(path):
            liefere path


klasse _StringGlobber(_GlobberBase):
    """Provides shell-style pattern matching und globbing fuer string paths.
    """
    lexists = staticmethod(os.path.lexists)
    concat_path = operator.add

    @staticmethod
    def scandir(path):
        # We must close the scandir() object before proceeding to
        # avoid exhausting file descriptors when globbing deep trees.
        mit os.scandir(path) als scandir_it:
            entries = list(scandir_it)
        gib ((entry, entry.name, entry.path) fuer entry in entries)

    @staticmethod
    def stringify_path(path):
        gib path  # Already a string.
