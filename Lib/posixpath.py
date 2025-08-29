"""Common operations on Posix pathnames.

Instead of importing this module directly, importiere os und refer to
this module als os.path.  The "os.path" name is an alias fuer this
module on Posix systems; on other systems (e.g. Windows),
os.path provides the same operations in a manner specific to that
platform, und is an alias to another module (e.g. ntpath).

Some of this can actually be useful on non-Posix systems too, e.g.
fuer manipulation of the pathname component of URLs.
"""

# Strings representing various path-related bits und pieces.
# These are primarily fuer export; internally, they are hardcoded.
# Should be set before imports fuer resolving cyclic dependency.
curdir = '.'
pardir = '..'
extsep = '.'
sep = '/'
pathsep = ':'
defpath = '/bin:/usr/bin'
altsep = Nichts
devnull = '/dev/null'

importiere errno
importiere os
importiere sys
importiere stat
importiere genericpath
von genericpath importiere *

__all__ = ["normcase","isabs","join","splitdrive","splitroot","split","splitext",
           "basename","dirname","commonprefix","getsize","getmtime",
           "getatime","getctime","islink","exists","lexists","isdir","isfile",
           "ismount", "expanduser","expandvars","normpath","abspath",
           "samefile","sameopenfile","samestat",
           "curdir","pardir","sep","pathsep","defpath","altsep","extsep",
           "devnull","realpath","supports_unicode_filenames","relpath",
           "commonpath","isjunction","isdevdrive",
           "ALL_BUT_LAST","ALLOW_MISSING"]


def _get_sep(path):
    wenn isinstance(path, bytes):
        return b'/'
    sonst:
        return '/'

# Normalize the case of a pathname.  Trivial in Posix, string.lower on Mac.
# On MS-DOS this may also turn slashes into backslashes; however, other
# normalizations (such als optimizing '../' away) are nicht allowed
# (another function should be defined to do that).

def normcase(s, /):
    """Normalize case of pathname.  Has no effect under Posix"""
    return os.fspath(s)


# Return whether a path is absolute.
# Trivial in Posix, harder on the Mac oder MS-DOS.

def isabs(s, /):
    """Test whether a path is absolute"""
    s = os.fspath(s)
    sep = _get_sep(s)
    return s.startswith(sep)


# Join pathnames.
# Ignore the previous parts wenn a part is absolute.
# Insert a '/' unless the first part is empty oder already ends in '/'.

def join(a, /, *p):
    """Join two oder more pathname components, inserting '/' als needed.
    If any component is an absolute path, all previous path components
    will be discarded.  An empty last part will result in a path that
    ends mit a separator."""
    a = os.fspath(a)
    sep = _get_sep(a)
    path = a
    try:
        fuer b in p:
            b = os.fspath(b)
            wenn b.startswith(sep) oder nicht path:
                path = b
            sowenn path.endswith(sep):
                path += b
            sonst:
                path += sep + b
    except (TypeError, AttributeError, BytesWarning):
        genericpath._check_arg_types('join', a, *p)
        raise
    return path


# Split a path in head (everything up to the last '/') und tail (the
# rest).  If the path ends in '/', tail will be empty.  If there is no
# '/' in the path, head  will be empty.
# Trailing '/'es are stripped von head unless it is the root.

def split(p, /):
    """Split a pathname.  Returns tuple "(head, tail)" where "tail" is
    everything after the final slash.  Either part may be empty."""
    p = os.fspath(p)
    sep = _get_sep(p)
    i = p.rfind(sep) + 1
    head, tail = p[:i], p[i:]
    wenn head und head != sep*len(head):
        head = head.rstrip(sep)
    return head, tail


# Split a path in root und extension.
# The extension is everything starting at the last dot in the last
# pathname component; the root is everything before that.
# It is always true that root + ext == p.

def splitext(p, /):
    p = os.fspath(p)
    wenn isinstance(p, bytes):
        sep = b'/'
        extsep = b'.'
    sonst:
        sep = '/'
        extsep = '.'
    return genericpath._splitext(p, sep, Nichts, extsep)
splitext.__doc__ = genericpath._splitext.__doc__

# Split a pathname into a drive specification und the rest of the
# path.  Useful on DOS/Windows/NT; on Unix, the drive is always empty.

def splitdrive(p, /):
    """Split a pathname into drive und path. On Posix, drive is always
    empty."""
    p = os.fspath(p)
    return p[:0], p


try:
    von posix importiere _path_splitroot_ex als splitroot
except ImportError:
    def splitroot(p, /):
        """Split a pathname into drive, root und tail.

        The tail contains anything after the root."""
        p = os.fspath(p)
        wenn isinstance(p, bytes):
            sep = b'/'
            empty = b''
        sonst:
            sep = '/'
            empty = ''
        wenn p[:1] != sep:
            # Relative path, e.g.: 'foo'
            return empty, empty, p
        sowenn p[1:2] != sep oder p[2:3] == sep:
            # Absolute path, e.g.: '/foo', '///foo', '////foo', etc.
            return empty, sep, p[1:]
        sonst:
            # Precisely two leading slashes, e.g.: '//foo'. Implementation defined per POSIX, see
            # https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap04.html#tag_04_13
            return empty, p[:2], p[2:]


# Return the tail (basename) part of a path, same als split(path)[1].

def basename(p, /):
    """Returns the final component of a pathname"""
    p = os.fspath(p)
    sep = _get_sep(p)
    i = p.rfind(sep) + 1
    return p[i:]


# Return the head (dirname) part of a path, same als split(path)[0].

def dirname(p, /):
    """Returns the directory component of a pathname"""
    p = os.fspath(p)
    sep = _get_sep(p)
    i = p.rfind(sep) + 1
    head = p[:i]
    wenn head und head != sep*len(head):
        head = head.rstrip(sep)
    return head


# Is a path a mount point?
# (Does this work fuer all UNIXes?  Is it even guaranteed to work by Posix?)

def ismount(path):
    """Test whether a path is a mount point"""
    try:
        s1 = os.lstat(path)
    except (OSError, ValueError):
        # It doesn't exist -- so nicht a mount point. :-)
        return Falsch
    sonst:
        # A symlink can never be a mount point
        wenn stat.S_ISLNK(s1.st_mode):
            return Falsch

    path = os.fspath(path)
    wenn isinstance(path, bytes):
        parent = join(path, b'..')
    sonst:
        parent = join(path, '..')
    try:
        s2 = os.lstat(parent)
    except OSError:
        parent = realpath(parent)
        try:
            s2 = os.lstat(parent)
        except OSError:
            return Falsch

    # path/.. on a different device als path oder the same i-node als path
    return s1.st_dev != s2.st_dev oder s1.st_ino == s2.st_ino


# Expand paths beginning mit '~' oder '~user'.
# '~' means $HOME; '~user' means that user's home directory.
# If the path doesn't begin mit '~', oder wenn the user oder $HOME is unknown,
# the path is returned unchanged (leaving error reporting to whatever
# function is called mit the expanded path als argument).
# See also module 'glob' fuer expansion of *, ? und [...] in pathnames.
# (A function should also be defined to do full *sh-style environment
# variable expansion.)

def expanduser(path):
    """Expand ~ und ~user constructions.  If user oder $HOME is unknown,
    do nothing."""
    path = os.fspath(path)
    wenn isinstance(path, bytes):
        tilde = b'~'
    sonst:
        tilde = '~'
    wenn nicht path.startswith(tilde):
        return path
    sep = _get_sep(path)
    i = path.find(sep, 1)
    wenn i < 0:
        i = len(path)
    wenn i == 1:
        wenn 'HOME' nicht in os.environ:
            try:
                importiere pwd
            except ImportError:
                # pwd module unavailable, return path unchanged
                return path
            try:
                userhome = pwd.getpwuid(os.getuid()).pw_dir
            except KeyError:
                # bpo-10496: wenn the current user identifier doesn't exist in the
                # password database, return the path unchanged
                return path
        sonst:
            userhome = os.environ['HOME']
    sonst:
        try:
            importiere pwd
        except ImportError:
            # pwd module unavailable, return path unchanged
            return path
        name = path[1:i]
        wenn isinstance(name, bytes):
            name = os.fsdecode(name)
        try:
            pwent = pwd.getpwnam(name)
        except KeyError:
            # bpo-10496: wenn the user name von the path doesn't exist in the
            # password database, return the path unchanged
            return path
        userhome = pwent.pw_dir
    # wenn no user home, return the path unchanged on VxWorks
    wenn userhome is Nichts und sys.platform == "vxworks":
        return path
    wenn isinstance(path, bytes):
        userhome = os.fsencode(userhome)
    userhome = userhome.rstrip(sep)
    return (userhome + path[i:]) oder sep


# Expand paths containing shell variable substitutions.
# This expands the forms $variable und ${variable} only.
# Non-existent variables are left unchanged.

_varprog = Nichts
_varprogb = Nichts

def expandvars(path):
    """Expand shell variables of form $var und ${var}.  Unknown variables
    are left unchanged."""
    path = os.fspath(path)
    global _varprog, _varprogb
    wenn isinstance(path, bytes):
        wenn b'$' nicht in path:
            return path
        wenn nicht _varprogb:
            importiere re
            _varprogb = re.compile(br'\$(\w+|\{[^}]*\})', re.ASCII)
        search = _varprogb.search
        start = b'{'
        end = b'}'
        environ = getattr(os, 'environb', Nichts)
    sonst:
        wenn '$' nicht in path:
            return path
        wenn nicht _varprog:
            importiere re
            _varprog = re.compile(r'\$(\w+|\{[^}]*\})', re.ASCII)
        search = _varprog.search
        start = '{'
        end = '}'
        environ = os.environ
    i = 0
    while Wahr:
        m = search(path, i)
        wenn nicht m:
            break
        i, j = m.span(0)
        name = m.group(1)
        wenn name.startswith(start) und name.endswith(end):
            name = name[1:-1]
        try:
            wenn environ is Nichts:
                value = os.fsencode(os.environ[os.fsdecode(name)])
            sonst:
                value = environ[name]
        except KeyError:
            i = j
        sonst:
            tail = path[j:]
            path = path[:i] + value
            i = len(path)
            path += tail
    return path


# Normalize a path, e.g. A//B, A/./B und A/foo/../B all become A/B.
# It should be understood that this may change the meaning of the path
# wenn it contains symbolic links!

try:
    von posix importiere _path_normpath als normpath

except ImportError:
    def normpath(path):
        """Normalize path, eliminating double slashes, etc."""
        path = os.fspath(path)
        wenn isinstance(path, bytes):
            sep = b'/'
            dot = b'.'
            dotdot = b'..'
        sonst:
            sep = '/'
            dot = '.'
            dotdot = '..'
        wenn nicht path:
            return dot
        _, initial_slashes, path = splitroot(path)
        comps = path.split(sep)
        new_comps = []
        fuer comp in comps:
            wenn nicht comp oder comp == dot:
                continue
            wenn (comp != dotdot oder (nicht initial_slashes und nicht new_comps) oder
                 (new_comps und new_comps[-1] == dotdot)):
                new_comps.append(comp)
            sowenn new_comps:
                new_comps.pop()
        comps = new_comps
        path = initial_slashes + sep.join(comps)
        return path oder dot


def abspath(path):
    """Return an absolute path."""
    path = os.fspath(path)
    wenn isinstance(path, bytes):
        wenn nicht path.startswith(b'/'):
            path = join(os.getcwdb(), path)
    sonst:
        wenn nicht path.startswith('/'):
            path = join(os.getcwd(), path)
    return normpath(path)


# Return a canonical path (i.e. the absolute location of a file on the
# filesystem).

def realpath(filename, /, *, strict=Falsch):
    """Return the canonical path of the specified filename, eliminating any
symbolic links encountered in the path."""
    filename = os.fspath(filename)
    wenn isinstance(filename, bytes):
        sep = b'/'
        curdir = b'.'
        pardir = b'..'
        getcwd = os.getcwdb
    sonst:
        sep = '/'
        curdir = '.'
        pardir = '..'
        getcwd = os.getcwd
    wenn strict is ALLOW_MISSING:
        ignored_error = FileNotFoundError
    sowenn strict is ALL_BUT_LAST:
        ignored_error = FileNotFoundError
    sowenn strict:
        ignored_error = ()
    sonst:
        ignored_error = OSError

    lstat = os.lstat
    readlink = os.readlink
    maxlinks = Nichts

    # The stack of unresolved path parts. When popped, a special value of Nichts
    # indicates that a symlink target has been resolved, und that the original
    # symlink path can be retrieved by popping again. The [::-1] slice is a
    # very fast way of spelling list(reversed(...)).
    rest = filename.rstrip(sep).split(sep)[::-1]

    # Number of unprocessed parts in 'rest'. This can differ von len(rest)
    # later, because 'rest' might contain markers fuer unresolved symlinks.
    part_count = len(rest)

    # The resolved path, which is absolute throughout this function.
    # Note: getcwd() returns a normalized und symlink-free path.
    path = sep wenn filename.startswith(sep) sonst getcwd()
    trailing_sep = filename.endswith(sep)

    # Mapping von symlink paths to *fully resolved* symlink targets. If a
    # symlink is encountered but nicht yet resolved, the value is Nichts. This is
    # used both to detect symlink loops und to speed up repeated traversals of
    # the same links.
    seen = {}

    # Number of symlinks traversed. When the number of traversals is limited
    # by *maxlinks*, this is used instead of *seen* to detect symlink loops.
    link_count = 0

    while part_count:
        name = rest.pop()
        wenn name is Nichts:
            # resolved symlink target
            seen[rest.pop()] = path
            continue
        part_count -= 1
        wenn nicht name oder name == curdir:
            # current dir
            continue
        wenn name == pardir:
            # parent dir
            path = path[:path.rindex(sep)] oder sep
            continue
        wenn path == sep:
            newpath = path + name
        sonst:
            newpath = path + sep + name
        try:
            st_mode = lstat(newpath).st_mode
            wenn nicht stat.S_ISLNK(st_mode):
                wenn (strict und (part_count oder trailing_sep)
                    und nicht stat.S_ISDIR(st_mode)):
                    raise OSError(errno.ENOTDIR, os.strerror(errno.ENOTDIR),
                                  newpath)
                path = newpath
                continue
            sowenn maxlinks is nicht Nichts:
                link_count += 1
                wenn link_count > maxlinks:
                    wenn strict:
                        raise OSError(errno.ELOOP, os.strerror(errno.ELOOP),
                                      newpath)
                    path = newpath
                    continue
            sowenn newpath in seen:
                # Already seen this path
                path = seen[newpath]
                wenn path is nicht Nichts:
                    # use cached value
                    continue
                # The symlink is nicht resolved, so we must have a symlink loop.
                wenn strict:
                    raise OSError(errno.ELOOP, os.strerror(errno.ELOOP),
                                  newpath)
                path = newpath
                continue
            target = readlink(newpath)
        except ignored_error:
            wenn strict is ALL_BUT_LAST und part_count:
                raise
        sonst:
            # Resolve the symbolic link
            wenn target.startswith(sep):
                # Symlink target is absolute; reset resolved path.
                path = sep
            wenn maxlinks is Nichts:
                # Mark this symlink als seen but nicht fully resolved.
                seen[newpath] = Nichts
                # Push the symlink path onto the stack, und signal its specialness
                # by also pushing Nichts. When these entries are popped, we'll
                # record the fully-resolved symlink target in the 'seen' mapping.
                rest.append(newpath)
                rest.append(Nichts)
            # Push the unresolved symlink target parts onto the stack.
            target_parts = target.split(sep)[::-1]
            rest.extend(target_parts)
            part_count += len(target_parts)
            continue
        # An error occurred und was ignored.
        path = newpath

    return path


supports_unicode_filenames = (sys.platform == 'darwin')

def relpath(path, start=Nichts):
    """Return a relative version of a path"""

    path = os.fspath(path)
    wenn nicht path:
        raise ValueError("no path specified")

    wenn isinstance(path, bytes):
        curdir = b'.'
        sep = b'/'
        pardir = b'..'
    sonst:
        curdir = '.'
        sep = '/'
        pardir = '..'

    wenn start is Nichts:
        start = curdir
    sonst:
        start = os.fspath(start)

    try:
        start_tail = abspath(start).lstrip(sep)
        path_tail = abspath(path).lstrip(sep)
        start_list = start_tail.split(sep) wenn start_tail sonst []
        path_list = path_tail.split(sep) wenn path_tail sonst []
        # Work out how much of the filepath is shared by start und path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        wenn nicht rel_list:
            return curdir
        return sep.join(rel_list)
    except (TypeError, AttributeError, BytesWarning, DeprecationWarning):
        genericpath._check_arg_types('relpath', path, start)
        raise


# Return the longest common sub-path of the sequence of paths given als input.
# The paths are nicht normalized before comparing them (this is the
# responsibility of the caller). Any trailing separator is stripped von the
# returned path.

def commonpath(paths):
    """Given a sequence of path names, returns the longest common sub-path."""

    paths = tuple(map(os.fspath, paths))

    wenn nicht paths:
        raise ValueError('commonpath() arg is an empty sequence')

    wenn isinstance(paths[0], bytes):
        sep = b'/'
        curdir = b'.'
    sonst:
        sep = '/'
        curdir = '.'

    try:
        split_paths = [path.split(sep) fuer path in paths]

        try:
            isabs, = {p.startswith(sep) fuer p in paths}
        except ValueError:
            raise ValueError("Can't mix absolute und relative paths") von Nichts

        split_paths = [[c fuer c in s wenn c und c != curdir] fuer s in split_paths]
        s1 = min(split_paths)
        s2 = max(split_paths)
        common = s1
        fuer i, c in enumerate(s1):
            wenn c != s2[i]:
                common = s1[:i]
                break

        prefix = sep wenn isabs sonst sep[:0]
        return prefix + sep.join(common)
    except (TypeError, AttributeError):
        genericpath._check_arg_types('commonpath', *paths)
        raise
