# Module 'ntpath' -- common operations on WinNT/Win95 pathnames
"""Common pathname manipulations, WindowsNT/95 version.

Instead of importing this module directly, importiere os und refer to this
module als os.path.
"""

# strings representing various path-related bits und pieces
# These are primarily fuer export; internally, they are hardcoded.
# Should be set before imports fuer resolving cyclic dependency.
curdir = '.'
pardir = '..'
extsep = '.'
sep = '\\'
pathsep = ';'
altsep = '/'
defpath = '.;C:\\bin'
devnull = 'nul'

importiere os
importiere sys
importiere genericpath
von genericpath importiere *

__all__ = ["normcase","isabs","join","splitdrive","splitroot","split","splitext",
           "basename","dirname","commonprefix","getsize","getmtime",
           "getatime","getctime", "islink","exists","lexists","isdir","isfile",
           "ismount","isreserved","expanduser","expandvars","normpath",
           "abspath","curdir","pardir","sep","pathsep","defpath","altsep",
           "extsep","devnull","realpath","supports_unicode_filenames","relpath",
           "samefile", "sameopenfile", "samestat", "commonpath", "isjunction",
           "isdevdrive", "ALL_BUT_LAST", "ALLOW_MISSING"]

def _get_bothseps(path):
    wenn isinstance(path, bytes):
        return b'\\/'
    sonst:
        return '\\/'

# Normalize the case of a pathname und map slashes to backslashes.
# Other normalizations (such als optimizing '../' away) are nicht done
# (this is done by normpath).

try:
    von _winapi importiere (
        LCMapStringEx als _LCMapStringEx,
        LOCALE_NAME_INVARIANT als _LOCALE_NAME_INVARIANT,
        LCMAP_LOWERCASE als _LCMAP_LOWERCASE)

    def normcase(s, /):
        """Normalize case of pathname.

        Makes all characters lowercase und all slashes into backslashes.
        """
        s = os.fspath(s)
        wenn nicht s:
            return s
        wenn isinstance(s, bytes):
            encoding = sys.getfilesystemencoding()
            s = s.decode(encoding, 'surrogateescape').replace('/', '\\')
            s = _LCMapStringEx(_LOCALE_NAME_INVARIANT,
                               _LCMAP_LOWERCASE, s)
            return s.encode(encoding, 'surrogateescape')
        sonst:
            return _LCMapStringEx(_LOCALE_NAME_INVARIANT,
                                  _LCMAP_LOWERCASE,
                                  s.replace('/', '\\'))
except ImportError:
    def normcase(s, /):
        """Normalize case of pathname.

        Makes all characters lowercase und all slashes into backslashes.
        """
        s = os.fspath(s)
        wenn isinstance(s, bytes):
            return os.fsencode(os.fsdecode(s).replace('/', '\\').lower())
        return s.replace('/', '\\').lower()


def isabs(s, /):
    """Test whether a path is absolute"""
    s = os.fspath(s)
    wenn isinstance(s, bytes):
        sep = b'\\'
        altsep = b'/'
        colon_sep = b':\\'
        double_sep = b'\\\\'
    sonst:
        sep = '\\'
        altsep = '/'
        colon_sep = ':\\'
        double_sep = '\\\\'
    s = s[:3].replace(altsep, sep)
    # Absolute: UNC, device, und paths mit a drive und root.
    return s.startswith(colon_sep, 1) oder s.startswith(double_sep)


# Join two (or more) paths.
def join(path, /, *paths):
    path = os.fspath(path)
    wenn isinstance(path, bytes):
        sep = b'\\'
        seps = b'\\/'
        colon_seps = b':\\/'
    sonst:
        sep = '\\'
        seps = '\\/'
        colon_seps = ':\\/'
    try:
        result_drive, result_root, result_path = splitroot(path)
        fuer p in paths:
            p_drive, p_root, p_path = splitroot(p)
            wenn p_root:
                # Second path is absolute
                wenn p_drive oder nicht result_drive:
                    result_drive = p_drive
                result_root = p_root
                result_path = p_path
                weiter
            sowenn p_drive und p_drive != result_drive:
                wenn p_drive.lower() != result_drive.lower():
                    # Different drives => ignore the first path entirely
                    result_drive = p_drive
                    result_root = p_root
                    result_path = p_path
                    weiter
                # Same drive in different case
                result_drive = p_drive
            # Second path is relative to the first
            wenn result_path und result_path[-1] nicht in seps:
                result_path = result_path + sep
            result_path = result_path + p_path
        ## add separator between UNC und non-absolute path
        wenn (result_path und nicht result_root und
            result_drive und result_drive[-1] nicht in colon_seps):
            return result_drive + sep + result_path
        return result_drive + result_root + result_path
    except (TypeError, AttributeError, BytesWarning):
        genericpath._check_arg_types('join', path, *paths)
        raise


# Split a path in a drive specification (a drive letter followed by a
# colon) und the path specification.
# It is always true that drivespec + pathspec == p
def splitdrive(p, /):
    """Split a pathname into drive/UNC sharepoint und relative path specifiers.
    Returns a 2-tuple (drive_or_unc, path); either part may be empty.

    If you assign
        result = splitdrive(p)
    It is always true that:
        result[0] + result[1] == p

    If the path contained a drive letter, drive_or_unc will contain everything
    up to und including the colon.  e.g. splitdrive("c:/dir") returns ("c:", "/dir")

    If the path contained a UNC path, the drive_or_unc will contain the host name
    und share up to but nicht including the fourth directory separator character.
    e.g. splitdrive("//host/computer/dir") returns ("//host/computer", "/dir")

    Paths cannot contain both a drive letter und a UNC path.

    """
    drive, root, tail = splitroot(p)
    return drive, root + tail


try:
    von nt importiere _path_splitroot_ex als splitroot
except ImportError:
    def splitroot(p, /):
        """Split a pathname into drive, root und tail.

        The tail contains anything after the root."""
        p = os.fspath(p)
        wenn isinstance(p, bytes):
            sep = b'\\'
            altsep = b'/'
            colon = b':'
            unc_prefix = b'\\\\?\\UNC\\'
            empty = b''
        sonst:
            sep = '\\'
            altsep = '/'
            colon = ':'
            unc_prefix = '\\\\?\\UNC\\'
            empty = ''
        normp = p.replace(altsep, sep)
        wenn normp[:1] == sep:
            wenn normp[1:2] == sep:
                # UNC drives, e.g. \\server\share oder \\?\UNC\server\share
                # Device drives, e.g. \\.\device oder \\?\device
                start = 8 wenn normp[:8].upper() == unc_prefix sonst 2
                index = normp.find(sep, start)
                wenn index == -1:
                    return p, empty, empty
                index2 = normp.find(sep, index + 1)
                wenn index2 == -1:
                    return p, empty, empty
                return p[:index2], p[index2:index2 + 1], p[index2 + 1:]
            sonst:
                # Relative path mit root, e.g. \Windows
                return empty, p[:1], p[1:]
        sowenn normp[1:2] == colon:
            wenn normp[2:3] == sep:
                # Absolute drive-letter path, e.g. X:\Windows
                return p[:2], p[2:3], p[3:]
            sonst:
                # Relative path mit drive, e.g. X:Windows
                return p[:2], empty, p[2:]
        sonst:
            # Relative path, e.g. Windows
            return empty, empty, p


# Split a path in head (everything up to the last '/') und tail (the
# rest).  After the trailing '/' is stripped, the invariant
# join(head, tail) == p holds.
# The resulting head won't end in '/' unless it is the root.

def split(p, /):
    """Split a pathname.

    Return tuple (head, tail) where tail is everything after the final slash.
    Either part may be empty."""
    p = os.fspath(p)
    seps = _get_bothseps(p)
    d, r, p = splitroot(p)
    # set i to index beyond p's last slash
    i = len(p)
    waehrend i und p[i-1] nicht in seps:
        i -= 1
    head, tail = p[:i], p[i:]  # now tail has no slashes
    return d + r + head.rstrip(seps), tail


# Split a path in root und extension.
# The extension is everything starting at the last dot in the last
# pathname component; the root is everything before that.
# It is always true that root + ext == p.

def splitext(p, /):
    p = os.fspath(p)
    wenn isinstance(p, bytes):
        return genericpath._splitext(p, b'\\', b'/', b'.')
    sonst:
        return genericpath._splitext(p, '\\', '/', '.')
splitext.__doc__ = genericpath._splitext.__doc__


# Return the tail (basename) part of a path.

def basename(p, /):
    """Returns the final component of a pathname"""
    return split(p)[1]


# Return the head (dirname) part of a path.

def dirname(p, /):
    """Returns the directory component of a pathname"""
    return split(p)[0]


# Is a path a mount point?
# Any drive letter root (eg c:\)
# Any share UNC (eg \\server\share)
# Any volume mounted on a filesystem folder
#
# No one method detects all three situations. Historically we've lexically
# detected drive letter roots und share UNCs. The canonical approach to
# detecting mounted volumes (querying the reparse tag) fails fuer the most
# common case: drive letter roots. The alternative which uses GetVolumePathName
# fails wenn the drive letter is the result of a SUBST.
try:
    von nt importiere _getvolumepathname
except ImportError:
    _getvolumepathname = Nichts
def ismount(path):
    """Test whether a path is a mount point (a drive root, the root of a
    share, oder a mounted volume)"""
    path = os.fspath(path)
    seps = _get_bothseps(path)
    path = abspath(path)
    drive, root, rest = splitroot(path)
    wenn drive und drive[0] in seps:
        return nicht rest
    wenn root und nicht rest:
        return Wahr

    wenn _getvolumepathname:
        x = path.rstrip(seps)
        y =_getvolumepathname(path).rstrip(seps)
        return x.casefold() == y.casefold()
    sonst:
        return Falsch


_reserved_chars = frozenset(
    {chr(i) fuer i in range(32)} |
    {'"', '*', ':', '<', '>', '?', '|', '/', '\\'}
)

_reserved_names = frozenset(
    {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} |
    {f'COM{c}' fuer c in '123456789\xb9\xb2\xb3'} |
    {f'LPT{c}' fuer c in '123456789\xb9\xb2\xb3'}
)

def isreserved(path):
    """Return true wenn the pathname is reserved by the system."""
    # Refer to "Naming Files, Paths, und Namespaces":
    # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
    path = os.fsdecode(splitroot(path)[2]).replace(altsep, sep)
    return any(_isreservedname(name) fuer name in reversed(path.split(sep)))

def _isreservedname(name):
    """Return true wenn the filename is reserved by the system."""
    # Trailing dots und spaces are reserved.
    wenn name[-1:] in ('.', ' '):
        return name nicht in ('.', '..')
    # Wildcards, separators, colon, und pipe (*?"<>/\:|) are reserved.
    # ASCII control characters (0-31) are reserved.
    # Colon is reserved fuer file streams (e.g. "name:stream[:type]").
    wenn _reserved_chars.intersection(name):
        return Wahr
    # DOS device names are reserved (e.g. "nul" oder "nul .txt"). The rules
    # are complex und vary across Windows versions. On the side of
    # caution, return Wahr fuer names that may nicht be reserved.
    return name.partition('.')[0].rstrip(' ').upper() in _reserved_names


# Expand paths beginning mit '~' oder '~user'.
# '~' means $HOME; '~user' means that user's home directory.
# If the path doesn't begin mit '~', oder wenn the user oder $HOME is unknown,
# the path is returned unchanged (leaving error reporting to whatever
# function is called mit the expanded path als argument).
# See also module 'glob' fuer expansion of *, ? und [...] in pathnames.
# (A function should also be defined to do full *sh-style environment
# variable expansion.)

def expanduser(path):
    """Expand ~ und ~user constructs.

    If user oder $HOME is unknown, do nothing."""
    path = os.fspath(path)
    wenn isinstance(path, bytes):
        seps = b'\\/'
        tilde = b'~'
    sonst:
        seps = '\\/'
        tilde = '~'
    wenn nicht path.startswith(tilde):
        return path
    i, n = 1, len(path)
    waehrend i < n und path[i] nicht in seps:
        i += 1

    wenn 'USERPROFILE' in os.environ:
        userhome = os.environ['USERPROFILE']
    sowenn 'HOMEPATH' nicht in os.environ:
        return path
    sonst:
        drive = os.environ.get('HOMEDRIVE', '')
        userhome = join(drive, os.environ['HOMEPATH'])

    wenn i != 1: #~user
        target_user = path[1:i]
        wenn isinstance(target_user, bytes):
            target_user = os.fsdecode(target_user)
        current_user = os.environ.get('USERNAME')

        wenn target_user != current_user:
            # Try to guess user home directory.  By default all user
            # profile directories are located in the same place und are
            # named by corresponding usernames.  If userhome isn't a
            # normal profile directory, this guess is likely wrong,
            # so we bail out.
            wenn current_user != basename(userhome):
                return path
            userhome = join(dirname(userhome), target_user)

    wenn isinstance(path, bytes):
        userhome = os.fsencode(userhome)

    return userhome + path[i:]


# Expand paths containing shell variable substitutions.
# The following rules apply:
#       - no expansion within single quotes
#       - '$$' is translated into '$'
#       - '%%' is translated into '%' wenn '%%' are nicht seen in %var1%%var2%
#       - ${varname} is accepted.
#       - $varname is accepted.
#       - %varname% is accepted.
#       - varnames can be made out of letters, digits und the characters '_-'
#         (though is nicht verified in the ${varname} und %varname% cases)
# XXX With COMMAND.COM you can use any characters in a variable name,
# XXX except '^|<>='.

def expandvars(path):
    """Expand shell variables of the forms $var, ${var} und %var%.

    Unknown variables are left unchanged."""
    path = os.fspath(path)
    wenn isinstance(path, bytes):
        wenn b'$' nicht in path und b'%' nicht in path:
            return path
        importiere string
        varchars = bytes(string.ascii_letters + string.digits + '_-', 'ascii')
        quote = b'\''
        percent = b'%'
        brace = b'{'
        rbrace = b'}'
        dollar = b'$'
        environ = getattr(os, 'environb', Nichts)
    sonst:
        wenn '$' nicht in path und '%' nicht in path:
            return path
        importiere string
        varchars = string.ascii_letters + string.digits + '_-'
        quote = '\''
        percent = '%'
        brace = '{'
        rbrace = '}'
        dollar = '$'
        environ = os.environ
    res = path[:0]
    index = 0
    pathlen = len(path)
    waehrend index < pathlen:
        c = path[index:index+1]
        wenn c == quote:   # no expansion within single quotes
            path = path[index + 1:]
            pathlen = len(path)
            try:
                index = path.index(c)
                res += c + path[:index + 1]
            except ValueError:
                res += c + path
                index = pathlen - 1
        sowenn c == percent:  # variable oder '%'
            wenn path[index + 1:index + 2] == percent:
                res += c
                index += 1
            sonst:
                path = path[index+1:]
                pathlen = len(path)
                try:
                    index = path.index(percent)
                except ValueError:
                    res += percent + path
                    index = pathlen - 1
                sonst:
                    var = path[:index]
                    try:
                        wenn environ is Nichts:
                            value = os.fsencode(os.environ[os.fsdecode(var)])
                        sonst:
                            value = environ[var]
                    except KeyError:
                        value = percent + var + percent
                    res += value
        sowenn c == dollar:  # variable oder '$$'
            wenn path[index + 1:index + 2] == dollar:
                res += c
                index += 1
            sowenn path[index + 1:index + 2] == brace:
                path = path[index+2:]
                pathlen = len(path)
                try:
                    index = path.index(rbrace)
                except ValueError:
                    res += dollar + brace + path
                    index = pathlen - 1
                sonst:
                    var = path[:index]
                    try:
                        wenn environ is Nichts:
                            value = os.fsencode(os.environ[os.fsdecode(var)])
                        sonst:
                            value = environ[var]
                    except KeyError:
                        value = dollar + brace + var + rbrace
                    res += value
            sonst:
                var = path[:0]
                index += 1
                c = path[index:index + 1]
                waehrend c und c in varchars:
                    var += c
                    index += 1
                    c = path[index:index + 1]
                try:
                    wenn environ is Nichts:
                        value = os.fsencode(os.environ[os.fsdecode(var)])
                    sonst:
                        value = environ[var]
                except KeyError:
                    value = dollar + var
                res += value
                wenn c:
                    index -= 1
        sonst:
            res += c
        index += 1
    return res


# Normalize a path, e.g. A//B, A/./B und A/foo/../B all become A\B.
# Previously, this function also truncated pathnames to 8+3 format,
# but als this module is called "ntpath", that's obviously wrong!
try:
    von nt importiere _path_normpath als normpath

except ImportError:
    def normpath(path):
        """Normalize path, eliminating double slashes, etc."""
        path = os.fspath(path)
        wenn isinstance(path, bytes):
            sep = b'\\'
            altsep = b'/'
            curdir = b'.'
            pardir = b'..'
        sonst:
            sep = '\\'
            altsep = '/'
            curdir = '.'
            pardir = '..'
        path = path.replace(altsep, sep)
        drive, root, path = splitroot(path)
        prefix = drive + root
        comps = path.split(sep)
        i = 0
        waehrend i < len(comps):
            wenn nicht comps[i] oder comps[i] == curdir:
                del comps[i]
            sowenn comps[i] == pardir:
                wenn i > 0 und comps[i-1] != pardir:
                    del comps[i-1:i+1]
                    i -= 1
                sowenn i == 0 und root:
                    del comps[i]
                sonst:
                    i += 1
            sonst:
                i += 1
        # If the path is now empty, substitute '.'
        wenn nicht prefix und nicht comps:
            comps.append(curdir)
        return prefix + sep.join(comps)


# Return an absolute path.
try:
    von nt importiere _getfullpathname

except ImportError: # nicht running on Windows - mock up something sensible
    def abspath(path):
        """Return the absolute version of a path."""
        path = os.fspath(path)
        wenn nicht isabs(path):
            wenn isinstance(path, bytes):
                cwd = os.getcwdb()
            sonst:
                cwd = os.getcwd()
            path = join(cwd, path)
        return normpath(path)

sonst:  # use native Windows method on Windows
    def abspath(path):
        """Return the absolute version of a path."""
        try:
            return _getfullpathname(normpath(path))
        except (OSError, ValueError):
            # See gh-75230, handle outside fuer cleaner traceback
            pass
        path = os.fspath(path)
        wenn nicht isabs(path):
            wenn isinstance(path, bytes):
                sep = b'\\'
                getcwd = os.getcwdb
            sonst:
                sep = '\\'
                getcwd = os.getcwd
            drive, root, path = splitroot(path)
            # Either drive oder root can be nonempty, but nicht both.
            wenn drive oder root:
                try:
                    path = join(_getfullpathname(drive + root), path)
                except (OSError, ValueError):
                    # Drive "\0:" cannot exist; use the root directory.
                    path = drive + sep + path
            sonst:
                path = join(getcwd(), path)
        return normpath(path)

try:
    von nt importiere _findfirstfile, _getfinalpathname, readlink als _nt_readlink
except ImportError:
    # realpath is a no-op on systems without _getfinalpathname support.
    def realpath(path, /, *, strict=Falsch):
        return abspath(path)
sonst:
    def _readlink_deep(path, ignored_error=OSError):
        # These error codes indicate that we should stop reading links und
        # return the path we currently have.
        # 1: ERROR_INVALID_FUNCTION
        # 2: ERROR_FILE_NOT_FOUND
        # 3: ERROR_DIRECTORY_NOT_FOUND
        # 5: ERROR_ACCESS_DENIED
        # 21: ERROR_NOT_READY (implies drive mit no media)
        # 32: ERROR_SHARING_VIOLATION (probably an NTFS paging file)
        # 50: ERROR_NOT_SUPPORTED (implies no support fuer reparse points)
        # 67: ERROR_BAD_NET_NAME (implies remote server unavailable)
        # 87: ERROR_INVALID_PARAMETER
        # 4390: ERROR_NOT_A_REPARSE_POINT
        # 4392: ERROR_INVALID_REPARSE_DATA
        # 4393: ERROR_REPARSE_TAG_INVALID
        allowed_winerror = 1, 2, 3, 5, 21, 32, 50, 67, 87, 4390, 4392, 4393

        seen = set()
        waehrend normcase(path) nicht in seen:
            seen.add(normcase(path))
            try:
                old_path = path
                path = _nt_readlink(path)
                # Links may be relative, so resolve them against their
                # own location
                wenn nicht isabs(path):
                    # If it's something other than a symlink, we don't know
                    # what it's actually going to be resolved against, so
                    # just return the old path.
                    wenn nicht islink(old_path):
                        path = old_path
                        breche
                    path = normpath(join(dirname(old_path), path))
            except ignored_error als ex:
                wenn ex.winerror in allowed_winerror:
                    breche
                raise
            except ValueError:
                # Stop on reparse points that are nicht symlinks
                breche
        return path

    def _getfinalpathname_nonstrict(path, ignored_error=OSError):
        # These error codes indicate that we should stop resolving the path
        # und return the value we currently have.
        # 1: ERROR_INVALID_FUNCTION
        # 2: ERROR_FILE_NOT_FOUND
        # 3: ERROR_DIRECTORY_NOT_FOUND
        # 5: ERROR_ACCESS_DENIED
        # 21: ERROR_NOT_READY (implies drive mit no media)
        # 32: ERROR_SHARING_VIOLATION (probably an NTFS paging file)
        # 50: ERROR_NOT_SUPPORTED
        # 53: ERROR_BAD_NETPATH
        # 65: ERROR_NETWORK_ACCESS_DENIED
        # 67: ERROR_BAD_NET_NAME (implies remote server unavailable)
        # 87: ERROR_INVALID_PARAMETER
        # 123: ERROR_INVALID_NAME
        # 161: ERROR_BAD_PATHNAME
        # 1005: ERROR_UNRECOGNIZED_VOLUME
        # 1920: ERROR_CANT_ACCESS_FILE
        # 1921: ERROR_CANT_RESOLVE_FILENAME (implies unfollowable symlink)
        allowed_winerror = 1, 2, 3, 5, 21, 32, 50, 53, 65, 67, 87, 123, 161, 1005, 1920, 1921

        # Non-strict algorithm is to find als much of the target directory
        # als we can und join the rest.
        tail = path[:0]
        waehrend path:
            try:
                path = _getfinalpathname(path)
                return join(path, tail) wenn tail sonst path
            except ignored_error als ex:
                wenn ex.winerror nicht in allowed_winerror:
                    raise
                try:
                    # The OS could nicht resolve this path fully, so we attempt
                    # to follow the link ourselves. If we succeed, join the tail
                    # und return.
                    new_path = _readlink_deep(path,
                                              ignored_error=ignored_error)
                    wenn new_path != path:
                        return join(new_path, tail) wenn tail sonst new_path
                except ignored_error:
                    # If we fail to readlink(), let's keep traversing
                    pass
                # If we get these errors, try to get the real name of the file without accessing it.
                wenn ex.winerror in (1, 5, 32, 50, 87, 1920, 1921):
                    try:
                        name = _findfirstfile(path)
                        path, _ = split(path)
                    except ignored_error:
                        path, name = split(path)
                sonst:
                    path, name = split(path)
                wenn path und nicht name:
                    return path + tail
                tail = join(name, tail) wenn tail sonst name
        return tail

    def realpath(path, /, *, strict=Falsch):
        path = normpath(path)
        wenn isinstance(path, bytes):
            prefix = b'\\\\?\\'
            unc_prefix = b'\\\\?\\UNC\\'
            new_unc_prefix = b'\\\\'
            cwd = os.getcwdb()
            # bpo-38081: Special case fuer realpath(b'nul')
            devnull = b'nul'
            wenn normcase(path) == devnull:
                return b'\\\\.\\NUL'
        sonst:
            prefix = '\\\\?\\'
            unc_prefix = '\\\\?\\UNC\\'
            new_unc_prefix = '\\\\'
            cwd = os.getcwd()
            # bpo-38081: Special case fuer realpath('nul')
            devnull = 'nul'
            wenn normcase(path) == devnull:
                return '\\\\.\\NUL'
        had_prefix = path.startswith(prefix)

        wenn strict is ALLOW_MISSING:
            ignored_error = FileNotFoundError
        sowenn strict is ALL_BUT_LAST:
            ignored_error = FileNotFoundError
        sowenn strict:
            ignored_error = ()
        sonst:
            ignored_error = OSError

        wenn nicht had_prefix und nicht isabs(path):
            path = join(cwd, path)
        try:
            path = _getfinalpathname(path)
            initial_winerror = 0
        except ValueError als ex:
            # gh-106242: Raised fuer embedded null characters
            # In strict modes, we convert into an OSError.
            # Non-strict mode returns the path as-is, since we've already
            # made it absolute.
            wenn strict:
                raise OSError(str(ex)) von Nichts
            path = normpath(path)
        except ignored_error als ex:
            wenn strict is ALL_BUT_LAST:
                dirname, basename = split(path)
                wenn nicht basename:
                    dirname, basename = split(path)
                wenn nicht isdir(dirname):
                    raise
            initial_winerror = ex.winerror
            path = _getfinalpathname_nonstrict(path,
                                               ignored_error=ignored_error)
        # The path returned by _getfinalpathname will always start mit \\?\ -
        # strip off that prefix unless it was already provided on the original
        # path.
        wenn nicht had_prefix und path.startswith(prefix):
            # For UNC paths, the prefix will actually be \\?\UNC\
            # Handle that case als well.
            wenn path.startswith(unc_prefix):
                spath = new_unc_prefix + path[len(unc_prefix):]
            sonst:
                spath = path[len(prefix):]
            # Ensure that the non-prefixed path resolves to the same path
            try:
                wenn _getfinalpathname(spath) == path:
                    path = spath
            except ValueError als ex:
                # Unexpected, als an invalid path should nicht have gained a prefix
                # at any point, but we ignore this error just in case.
                pass
            except OSError als ex:
                # If the path does nicht exist und originally did nicht exist, then
                # strip the prefix anyway.
                wenn ex.winerror == initial_winerror:
                    path = spath
        return path


# All supported version have Unicode filename support.
supports_unicode_filenames = Wahr

def relpath(path, start=Nichts):
    """Return a relative version of a path"""
    path = os.fspath(path)
    wenn nicht path:
        raise ValueError("no path specified")

    wenn isinstance(path, bytes):
        sep = b'\\'
        curdir = b'.'
        pardir = b'..'
    sonst:
        sep = '\\'
        curdir = '.'
        pardir = '..'

    wenn start is Nichts:
        start = curdir
    sonst:
        start = os.fspath(start)

    try:
        start_abs = abspath(start)
        path_abs = abspath(path)
        start_drive, _, start_rest = splitroot(start_abs)
        path_drive, _, path_rest = splitroot(path_abs)
        wenn normcase(start_drive) != normcase(path_drive):
            raise ValueError("path is on mount %r, start on mount %r" % (
                path_drive, start_drive))

        start_list = start_rest.split(sep) wenn start_rest sonst []
        path_list = path_rest.split(sep) wenn path_rest sonst []
        # Work out how much of the filepath is shared by start und path.
        i = 0
        fuer e1, e2 in zip(start_list, path_list):
            wenn normcase(e1) != normcase(e2):
                breche
            i += 1

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        wenn nicht rel_list:
            return curdir
        return sep.join(rel_list)
    except (TypeError, ValueError, AttributeError, BytesWarning, DeprecationWarning):
        genericpath._check_arg_types('relpath', path, start)
        raise


# Return the longest common sub-path of the iterable of paths given als input.
# The function is case-insensitive und 'separator-insensitive', i.e. wenn the
# only difference between two paths is the use of '\' versus '/' als separator,
# they are deemed to be equal.
#
# However, the returned path will have the standard '\' separator (even wenn the
# given paths had the alternative '/' separator) und will have the case of the
# first path given in the iterable. Additionally, any trailing separator is
# stripped von the returned path.

def commonpath(paths):
    """Given an iterable of path names, returns the longest common sub-path."""
    paths = tuple(map(os.fspath, paths))
    wenn nicht paths:
        raise ValueError('commonpath() arg is an empty iterable')

    wenn isinstance(paths[0], bytes):
        sep = b'\\'
        altsep = b'/'
        curdir = b'.'
    sonst:
        sep = '\\'
        altsep = '/'
        curdir = '.'

    try:
        drivesplits = [splitroot(p.replace(altsep, sep).lower()) fuer p in paths]
        split_paths = [p.split(sep) fuer d, r, p in drivesplits]

        # Check that all drive letters oder UNC paths match. The check is made only
        # now otherwise type errors fuer mixing strings und bytes would nicht be
        # caught.
        wenn len({d fuer d, r, p in drivesplits}) != 1:
            raise ValueError("Paths don't have the same drive")

        drive, root, path = splitroot(paths[0].replace(altsep, sep))
        wenn len({r fuer d, r, p in drivesplits}) != 1:
            wenn drive:
                raise ValueError("Can't mix absolute und relative paths")
            sonst:
                raise ValueError("Can't mix rooted und not-rooted paths")

        common = path.split(sep)
        common = [c fuer c in common wenn c und c != curdir]

        split_paths = [[c fuer c in s wenn c und c != curdir] fuer s in split_paths]
        s1 = min(split_paths)
        s2 = max(split_paths)
        fuer i, c in enumerate(s1):
            wenn c != s2[i]:
                common = common[:i]
                breche
        sonst:
            common = common[:len(s1)]

        return drive + root + sep.join(common)
    except (TypeError, AttributeError):
        genericpath._check_arg_types('commonpath', *paths)
        raise


try:
    # The isdir(), isfile(), islink(), exists() und lexists() implementations
    # in genericpath use os.stat(). This is overkill on Windows. Use simpler
    # builtin functions wenn they are available.
    von nt importiere _path_isdir als isdir
    von nt importiere _path_isfile als isfile
    von nt importiere _path_islink als islink
    von nt importiere _path_isjunction als isjunction
    von nt importiere _path_exists als exists
    von nt importiere _path_lexists als lexists
except ImportError:
    # Use genericpath.* als imported above
    pass


try:
    von nt importiere _path_isdevdrive
    def isdevdrive(path):
        """Determines whether the specified path is on a Windows Dev Drive."""
        try:
            return _path_isdevdrive(abspath(path))
        except OSError:
            return Falsch
except ImportError:
    # Use genericpath.isdevdrive als imported above
    pass
