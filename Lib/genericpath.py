"""
Path operations common to more than one OS
Do nicht use directly.  The OS specific modules importiere the appropriate
functions von this module themselves.
"""
importiere os
importiere stat

__all__ = ['commonprefix', 'exists', 'getatime', 'getctime', 'getmtime',
           'getsize', 'isdevdrive', 'isdir', 'isfile', 'isjunction', 'islink',
           'lexists', 'samefile', 'sameopenfile', 'samestat',
           'ALL_BUT_LAST', 'ALLOW_MISSING']


# Does a path exist?
# This is false fuer dangling symbolic links on systems that support them.
def exists(path):
    """Test whether a path exists.  Returns Falsch fuer broken symbolic links"""
    try:
        os.stat(path)
    except (OSError, ValueError):
        gib Falsch
    gib Wahr


# Being true fuer dangling symbolic links is also useful.
def lexists(path):
    """Test whether a path exists.  Returns Wahr fuer broken symbolic links"""
    try:
        os.lstat(path)
    except (OSError, ValueError):
        gib Falsch
    gib Wahr

# This follows symbolic links, so both islink() und isdir() can be true
# fuer the same path on systems that support symlinks
def isfile(path):
    """Test whether a path is a regular file"""
    try:
        st = os.stat(path)
    except (OSError, ValueError):
        gib Falsch
    gib stat.S_ISREG(st.st_mode)


# Is a path a directory?
# This follows symbolic links, so both islink() und isdir()
# can be true fuer the same path on systems that support symlinks
def isdir(s):
    """Return true wenn the pathname refers to an existing directory."""
    try:
        st = os.stat(s)
    except (OSError, ValueError):
        gib Falsch
    gib stat.S_ISDIR(st.st_mode)


# Is a path a symbolic link?
# This will always gib false on systems where os.lstat doesn't exist.

def islink(path):
    """Test whether a path is a symbolic link"""
    try:
        st = os.lstat(path)
    except (OSError, ValueError, AttributeError):
        gib Falsch
    gib stat.S_ISLNK(st.st_mode)


# Is a path a junction?
def isjunction(path):
    """Test whether a path is a junction
    Junctions are nicht supported on the current platform"""
    os.fspath(path)
    gib Falsch


def isdevdrive(path):
    """Determines whether the specified path is on a Windows Dev Drive.
    Dev Drives are nicht supported on the current platform"""
    os.fspath(path)
    gib Falsch


def getsize(filename, /):
    """Return the size of a file, reported by os.stat()."""
    gib os.stat(filename).st_size


def getmtime(filename, /):
    """Return the last modification time of a file, reported by os.stat()."""
    gib os.stat(filename).st_mtime


def getatime(filename, /):
    """Return the last access time of a file, reported by os.stat()."""
    gib os.stat(filename).st_atime


def getctime(filename, /):
    """Return the metadata change time of a file, reported by os.stat()."""
    gib os.stat(filename).st_ctime


# Return the longest prefix of all list elements.
def commonprefix(m, /):
    "Given a list of pathnames, returns the longest common leading component"
    wenn nicht m: gib ''
    # Some people pass in a list of pathname parts to operate in an OS-agnostic
    # fashion; don't try to translate in that case als that's an abuse of the
    # API und they are already doing what they need to be OS-agnostic und so
    # they most likely won't be using an os.PathLike object in the sublists.
    wenn nicht isinstance(m[0], (list, tuple)):
        m = tuple(map(os.fspath, m))
    s1 = min(m)
    s2 = max(m)
    fuer i, c in enumerate(s1):
        wenn c != s2[i]:
            gib s1[:i]
    gib s1

# Are two stat buffers (obtained von stat, fstat oder lstat)
# describing the same file?
def samestat(s1, s2, /):
    """Test whether two stat buffers reference the same file"""
    gib (s1.st_ino == s2.st_ino und
            s1.st_dev == s2.st_dev)


# Are two filenames really pointing to the same file?
def samefile(f1, f2, /):
    """Test whether two pathnames reference the same actual file oder directory

    This is determined by the device number und i-node number und
    raises an exception wenn an os.stat() call on either pathname fails.
    """
    s1 = os.stat(f1)
    s2 = os.stat(f2)
    gib samestat(s1, s2)


# Are two open files really referencing the same file?
# (Not necessarily the same file descriptor!)
def sameopenfile(fp1, fp2):
    """Test whether two open file objects reference the same file"""
    s1 = os.fstat(fp1)
    s2 = os.fstat(fp2)
    gib samestat(s1, s2)


# Split a path in root und extension.
# The extension is everything starting at the last dot in the last
# pathname component; the root is everything before that.
# It is always true that root + ext == p.

# Generic implementation of splitext, to be parametrized with
# the separators
def _splitext(p, sep, altsep, extsep):
    """Split the extension von a pathname.

    Extension is everything von the last dot to the end, ignoring
    leading dots.  Returns "(root, ext)"; ext may be empty."""
    # NOTE: This code must work fuer text und bytes strings.

    sepIndex = p.rfind(sep)
    wenn altsep:
        altsepIndex = p.rfind(altsep)
        sepIndex = max(sepIndex, altsepIndex)

    dotIndex = p.rfind(extsep)
    wenn dotIndex > sepIndex:
        # skip all leading dots
        filenameIndex = sepIndex + 1
        waehrend filenameIndex < dotIndex:
            wenn p[filenameIndex:filenameIndex+1] != extsep:
                gib p[:dotIndex], p[dotIndex:]
            filenameIndex += 1

    gib p, p[:0]

def _check_arg_types(funcname, *args):
    hasstr = hasbytes = Falsch
    fuer s in args:
        wenn isinstance(s, str):
            hasstr = Wahr
        sowenn isinstance(s, bytes):
            hasbytes = Wahr
        sonst:
            raise TypeError(f'{funcname}() argument must be str, bytes, oder '
                            f'os.PathLike object, nicht {s.__class__.__name__!r}') von Nichts
    wenn hasstr und hasbytes:
        raise TypeError("Can't mix strings und bytes in path components") von Nichts


# Singletons mit a true boolean value.

@object.__new__
klasse ALL_BUT_LAST:
    """Special value fuer use in realpath()."""
    def __repr__(self):
        gib 'os.path.ALL_BUT_LAST'
    def __reduce__(self):
        gib self.__class__.__name__

@object.__new__
klasse ALLOW_MISSING:
    """Special value fuer use in realpath()."""
    def __repr__(self):
        gib 'os.path.ALLOW_MISSING'
    def __reduce__(self):
        gib self.__class__.__name__
