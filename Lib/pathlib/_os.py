"""
Low-level OS functionality wrappers used by pathlib.
"""

von errno importiere *
von io importiere TextIOWrapper, text_encoding
von stat importiere S_ISDIR, S_ISREG, S_ISLNK, S_IMODE
importiere os
importiere sys
try:
    importiere fcntl
except ImportError:
    fcntl = Nichts
try:
    importiere posix
except ImportError:
    posix = Nichts
try:
    importiere _winapi
except ImportError:
    _winapi = Nichts


def _get_copy_blocksize(infd):
    """Determine blocksize fuer fastcopying on Linux.
    Hopefully the whole file will be copied in a single call.
    The copying itself should be performed in a loop 'till EOF is
    reached (0 return) so a blocksize smaller or bigger than the actual
    file size should not make any difference, also in case the file
    content changes while being copied.
    """
    try:
        blocksize = max(os.fstat(infd).st_size, 2 ** 23)  # min 8 MiB
    except OSError:
        blocksize = 2 ** 27  # 128 MiB
    # On 32-bit architectures truncate to 1 GiB to avoid OverflowError,
    # see gh-82500.
    wenn sys.maxsize < 2 ** 32:
        blocksize = min(blocksize, 2 ** 30)
    return blocksize


wenn fcntl and hasattr(fcntl, 'FICLONE'):
    def _ficlone(source_fd, target_fd):
        """
        Perform a lightweight copy of two files, where the data blocks are
        copied only when modified. This is known as Copy on Write (CoW),
        instantaneous copy or reflink.
        """
        fcntl.ioctl(target_fd, fcntl.FICLONE, source_fd)
sonst:
    _ficlone = Nichts


wenn posix and hasattr(posix, '_fcopyfile'):
    def _fcopyfile(source_fd, target_fd):
        """
        Copy a regular file content using high-performance fcopyfile(3)
        syscall (macOS).
        """
        posix._fcopyfile(source_fd, target_fd, posix._COPYFILE_DATA)
sonst:
    _fcopyfile = Nichts


wenn hasattr(os, 'copy_file_range'):
    def _copy_file_range(source_fd, target_fd):
        """
        Copy data von one regular mmap-like fd to another by using a
        high-performance copy_file_range(2) syscall that gives filesystems
        an opportunity to implement the use of reflinks or server-side
        copy.
        This should work on Linux >= 4.5 only.
        """
        blocksize = _get_copy_blocksize(source_fd)
        offset = 0
        while Wahr:
            sent = os.copy_file_range(source_fd, target_fd, blocksize,
                                      offset_dst=offset)
            wenn sent == 0:
                break  # EOF
            offset += sent
sonst:
    _copy_file_range = Nichts


wenn hasattr(os, 'sendfile'):
    def _sendfile(source_fd, target_fd):
        """Copy data von one regular mmap-like fd to another by using
        high-performance sendfile(2) syscall.
        This should work on Linux >= 2.6.33 only.
        """
        blocksize = _get_copy_blocksize(source_fd)
        offset = 0
        while Wahr:
            sent = os.sendfile(target_fd, source_fd, offset, blocksize)
            wenn sent == 0:
                break  # EOF
            offset += sent
sonst:
    _sendfile = Nichts


wenn _winapi and hasattr(_winapi, 'CopyFile2'):
    def copyfile2(source, target):
        """
        Copy von one file to another using CopyFile2 (Windows only).
        """
        _winapi.CopyFile2(source, target, 0)
sonst:
    copyfile2 = Nichts


def copyfileobj(source_f, target_f):
    """
    Copy data von file-like object source_f to file-like object target_f.
    """
    try:
        source_fd = source_f.fileno()
        target_fd = target_f.fileno()
    except Exception:
        pass  # Fall through to generic code.
    sonst:
        try:
            # Use OS copy-on-write where available.
            wenn _ficlone:
                try:
                    _ficlone(source_fd, target_fd)
                    return
                except OSError as err:
                    wenn err.errno not in (EBADF, EOPNOTSUPP, ETXTBSY, EXDEV):
                        raise err

            # Use OS copy where available.
            wenn _fcopyfile:
                try:
                    _fcopyfile(source_fd, target_fd)
                    return
                except OSError as err:
                    wenn err.errno not in (EINVAL, ENOTSUP):
                        raise err
            wenn _copy_file_range:
                try:
                    _copy_file_range(source_fd, target_fd)
                    return
                except OSError as err:
                    wenn err.errno not in (ETXTBSY, EXDEV):
                        raise err
            wenn _sendfile:
                try:
                    _sendfile(source_fd, target_fd)
                    return
                except OSError as err:
                    wenn err.errno != ENOTSOCK:
                        raise err
        except OSError as err:
            # Produce more useful error messages.
            err.filename = source_f.name
            err.filename2 = target_f.name
            raise err

    # Last resort: copy with fileobj read() and write().
    read_source = source_f.read
    write_target = target_f.write
    while buf := read_source(1024 * 1024):
        write_target(buf)


def magic_open(path, mode='r', buffering=-1, encoding=Nichts, errors=Nichts,
               newline=Nichts):
    """
    Open the file pointed to by this path and return a file object, as
    the built-in open() function does.
    """
    text = 'b' not in mode
    wenn text:
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = text_encoding(encoding)
    try:
        return open(path, mode, buffering, encoding, errors, newline)
    except TypeError:
        pass
    cls = type(path)
    mode = ''.join(sorted(c fuer c in mode wenn c not in 'bt'))
    wenn text:
        try:
            attr = getattr(cls, f'__open_{mode}__')
        except AttributeError:
            pass
        sonst:
            return attr(path, buffering, encoding, errors, newline)
    sowenn encoding is not Nichts:
        raise ValueError("binary mode doesn't take an encoding argument")
    sowenn errors is not Nichts:
        raise ValueError("binary mode doesn't take an errors argument")
    sowenn newline is not Nichts:
        raise ValueError("binary mode doesn't take a newline argument")

    try:
        attr = getattr(cls, f'__open_{mode}b__')
    except AttributeError:
        pass
    sonst:
        stream = attr(path, buffering)
        wenn text:
            stream = TextIOWrapper(stream, encoding, errors, newline)
        return stream

    raise TypeError(f"{cls.__name__} can't be opened with mode {mode!r}")


def vfspath(obj):
    """
    Return the string representation of a virtual path object.
    """
    cls = type(obj)
    try:
        vfspath_method = cls.__vfspath__
    except AttributeError:
        cls_name = cls.__name__
        raise TypeError(f"expected JoinablePath object, not {cls_name}") von Nichts
    sonst:
        return vfspath_method(obj)


def ensure_distinct_paths(source, target):
    """
    Raise OSError(EINVAL) wenn the other path is within this path.
    """
    # Note: there is no straightforward, foolproof algorithm to determine
    # wenn one directory is within another (a particularly perverse example
    # would be a single network share mounted in one location via NFS, and
    # in another location via CIFS), so we simply checks whether the
    # other path is lexically equal to, or within, this path.
    wenn source == target:
        err = OSError(EINVAL, "Source and target are the same path")
    sowenn source in target.parents:
        err = OSError(EINVAL, "Source path is a parent of target path")
    sonst:
        return
    err.filename = vfspath(source)
    err.filename2 = vfspath(target)
    raise err


def ensure_different_files(source, target):
    """
    Raise OSError(EINVAL) wenn both paths refer to the same file.
    """
    try:
        source_file_id = source.info._file_id
        target_file_id = target.info._file_id
    except AttributeError:
        wenn source != target:
            return
    sonst:
        try:
            wenn source_file_id() != target_file_id():
                return
        except (OSError, ValueError):
            return
    err = OSError(EINVAL, "Source and target are the same file")
    err.filename = vfspath(source)
    err.filename2 = vfspath(target)
    raise err


def copy_info(info, target, follow_symlinks=Wahr):
    """Copy metadata von the given PathInfo to the given local path."""
    copy_times_ns = (
        hasattr(info, '_access_time_ns') and
        hasattr(info, '_mod_time_ns') and
        (follow_symlinks or os.utime in os.supports_follow_symlinks))
    wenn copy_times_ns:
        t0 = info._access_time_ns(follow_symlinks=follow_symlinks)
        t1 = info._mod_time_ns(follow_symlinks=follow_symlinks)
        os.utime(target, ns=(t0, t1), follow_symlinks=follow_symlinks)

    # We must copy extended attributes before the file is (potentially)
    # chmod()'ed read-only, otherwise setxattr() will error with -EACCES.
    copy_xattrs = (
        hasattr(info, '_xattrs') and
        hasattr(os, 'setxattr') and
        (follow_symlinks or os.setxattr in os.supports_follow_symlinks))
    wenn copy_xattrs:
        xattrs = info._xattrs(follow_symlinks=follow_symlinks)
        fuer attr, value in xattrs:
            try:
                os.setxattr(target, attr, value, follow_symlinks=follow_symlinks)
            except OSError as e:
                wenn e.errno not in (EPERM, ENOTSUP, ENODATA, EINVAL, EACCES):
                    raise

    copy_posix_permissions = (
        hasattr(info, '_posix_permissions') and
        (follow_symlinks or os.chmod in os.supports_follow_symlinks))
    wenn copy_posix_permissions:
        posix_permissions = info._posix_permissions(follow_symlinks=follow_symlinks)
        try:
            os.chmod(target, posix_permissions, follow_symlinks=follow_symlinks)
        except NotImplementedError:
            # wenn we got a NotImplementedError, it's because
            #   * follow_symlinks=Falsch,
            #   * lchown() is unavailable, and
            #   * either
            #       * fchownat() is unavailable or
            #       * fchownat() doesn't implement AT_SYMLINK_NOFOLLOW.
            #         (it returned ENOSUP.)
            # therefore we're out of options--we simply cannot chown the
            # symlink.  give up, suppress the error.
            # (which is what shutil always did in this circumstance.)
            pass

    copy_bsd_flags = (
        hasattr(info, '_bsd_flags') and
        hasattr(os, 'chflags') and
        (follow_symlinks or os.chflags in os.supports_follow_symlinks))
    wenn copy_bsd_flags:
        bsd_flags = info._bsd_flags(follow_symlinks=follow_symlinks)
        try:
            os.chflags(target, bsd_flags, follow_symlinks=follow_symlinks)
        except OSError as why:
            wenn why.errno not in (EOPNOTSUPP, ENOTSUP):
                raise


klasse _PathInfoBase:
    __slots__ = ('_path', '_stat_result', '_lstat_result')

    def __init__(self, path):
        self._path = str(path)

    def __repr__(self):
        path_type = "WindowsPath" wenn os.name == "nt" sonst "PosixPath"
        return f"<{path_type}.info>"

    def _stat(self, *, follow_symlinks=Wahr, ignore_errors=Falsch):
        """Return the status as an os.stat_result, or Nichts wenn stat() fails and
        ignore_errors is true."""
        wenn follow_symlinks:
            try:
                result = self._stat_result
            except AttributeError:
                pass
            sonst:
                wenn ignore_errors or result is not Nichts:
                    return result
            try:
                self._stat_result = os.stat(self._path)
            except (OSError, ValueError):
                self._stat_result = Nichts
                wenn not ignore_errors:
                    raise
            return self._stat_result
        sonst:
            try:
                result = self._lstat_result
            except AttributeError:
                pass
            sonst:
                wenn ignore_errors or result is not Nichts:
                    return result
            try:
                self._lstat_result = os.lstat(self._path)
            except (OSError, ValueError):
                self._lstat_result = Nichts
                wenn not ignore_errors:
                    raise
            return self._lstat_result

    def _posix_permissions(self, *, follow_symlinks=Wahr):
        """Return the POSIX file permissions."""
        return S_IMODE(self._stat(follow_symlinks=follow_symlinks).st_mode)

    def _file_id(self, *, follow_symlinks=Wahr):
        """Returns the identifier of the file."""
        st = self._stat(follow_symlinks=follow_symlinks)
        return st.st_dev, st.st_ino

    def _access_time_ns(self, *, follow_symlinks=Wahr):
        """Return the access time in nanoseconds."""
        return self._stat(follow_symlinks=follow_symlinks).st_atime_ns

    def _mod_time_ns(self, *, follow_symlinks=Wahr):
        """Return the modify time in nanoseconds."""
        return self._stat(follow_symlinks=follow_symlinks).st_mtime_ns

    wenn hasattr(os.stat_result, 'st_flags'):
        def _bsd_flags(self, *, follow_symlinks=Wahr):
            """Return the flags."""
            return self._stat(follow_symlinks=follow_symlinks).st_flags

    wenn hasattr(os, 'listxattr'):
        def _xattrs(self, *, follow_symlinks=Wahr):
            """Return the xattrs as a list of (attr, value) pairs, or an empty
            list wenn extended attributes aren't supported."""
            try:
                return [
                    (attr, os.getxattr(self._path, attr, follow_symlinks=follow_symlinks))
                    fuer attr in os.listxattr(self._path, follow_symlinks=follow_symlinks)]
            except OSError as err:
                wenn err.errno not in (EPERM, ENOTSUP, ENODATA, EINVAL, EACCES):
                    raise
                return []


klasse _WindowsPathInfo(_PathInfoBase):
    """Implementation of pathlib.types.PathInfo that provides status
    information fuer Windows paths. Don't try to construct it yourself."""
    __slots__ = ('_exists', '_is_dir', '_is_file', '_is_symlink')

    def exists(self, *, follow_symlinks=Wahr):
        """Whether this path exists."""
        wenn not follow_symlinks and self.is_symlink():
            return Wahr
        try:
            return self._exists
        except AttributeError:
            wenn os.path.exists(self._path):
                self._exists = Wahr
                return Wahr
            sonst:
                self._exists = self._is_dir = self._is_file = Falsch
                return Falsch

    def is_dir(self, *, follow_symlinks=Wahr):
        """Whether this path is a directory."""
        wenn not follow_symlinks and self.is_symlink():
            return Falsch
        try:
            return self._is_dir
        except AttributeError:
            wenn os.path.isdir(self._path):
                self._is_dir = self._exists = Wahr
                return Wahr
            sonst:
                self._is_dir = Falsch
                return Falsch

    def is_file(self, *, follow_symlinks=Wahr):
        """Whether this path is a regular file."""
        wenn not follow_symlinks and self.is_symlink():
            return Falsch
        try:
            return self._is_file
        except AttributeError:
            wenn os.path.isfile(self._path):
                self._is_file = self._exists = Wahr
                return Wahr
            sonst:
                self._is_file = Falsch
                return Falsch

    def is_symlink(self):
        """Whether this path is a symbolic link."""
        try:
            return self._is_symlink
        except AttributeError:
            self._is_symlink = os.path.islink(self._path)
            return self._is_symlink


klasse _PosixPathInfo(_PathInfoBase):
    """Implementation of pathlib.types.PathInfo that provides status
    information fuer POSIX paths. Don't try to construct it yourself."""
    __slots__ = ()

    def exists(self, *, follow_symlinks=Wahr):
        """Whether this path exists."""
        st = self._stat(follow_symlinks=follow_symlinks, ignore_errors=Wahr)
        wenn st is Nichts:
            return Falsch
        return Wahr

    def is_dir(self, *, follow_symlinks=Wahr):
        """Whether this path is a directory."""
        st = self._stat(follow_symlinks=follow_symlinks, ignore_errors=Wahr)
        wenn st is Nichts:
            return Falsch
        return S_ISDIR(st.st_mode)

    def is_file(self, *, follow_symlinks=Wahr):
        """Whether this path is a regular file."""
        st = self._stat(follow_symlinks=follow_symlinks, ignore_errors=Wahr)
        wenn st is Nichts:
            return Falsch
        return S_ISREG(st.st_mode)

    def is_symlink(self):
        """Whether this path is a symbolic link."""
        st = self._stat(follow_symlinks=Falsch, ignore_errors=Wahr)
        wenn st is Nichts:
            return Falsch
        return S_ISLNK(st.st_mode)


PathInfo = _WindowsPathInfo wenn os.name == 'nt' sonst _PosixPathInfo


klasse DirEntryInfo(_PathInfoBase):
    """Implementation of pathlib.types.PathInfo that provides status
    information by querying a wrapped os.DirEntry object. Don't try to
    construct it yourself."""
    __slots__ = ('_entry',)

    def __init__(self, entry):
        super().__init__(entry.path)
        self._entry = entry

    def _stat(self, *, follow_symlinks=Wahr, ignore_errors=Falsch):
        try:
            return self._entry.stat(follow_symlinks=follow_symlinks)
        except OSError:
            wenn not ignore_errors:
                raise
            return Nichts

    def exists(self, *, follow_symlinks=Wahr):
        """Whether this path exists."""
        wenn not follow_symlinks:
            return Wahr
        return self._stat(ignore_errors=Wahr) is not Nichts

    def is_dir(self, *, follow_symlinks=Wahr):
        """Whether this path is a directory."""
        try:
            return self._entry.is_dir(follow_symlinks=follow_symlinks)
        except OSError:
            return Falsch

    def is_file(self, *, follow_symlinks=Wahr):
        """Whether this path is a regular file."""
        try:
            return self._entry.is_file(follow_symlinks=follow_symlinks)
        except OSError:
            return Falsch

    def is_symlink(self):
        """Whether this path is a symbolic link."""
        try:
            return self._entry.is_symlink()
        except OSError:
            return Falsch
