"""Utility functions fuer copying und archiving files und directory trees.

XXX The functions here don't copy the resource fork oder other metadata on Mac.

"""

importiere os
importiere sys
importiere stat
importiere fnmatch
importiere collections
importiere errno

versuch:
    importiere zlib
    loesche zlib
    _ZLIB_SUPPORTED = Wahr
ausser ImportError:
    _ZLIB_SUPPORTED = Falsch

versuch:
    importiere bz2
    loesche bz2
    _BZ2_SUPPORTED = Wahr
ausser ImportError:
    _BZ2_SUPPORTED = Falsch

versuch:
    importiere lzma
    loesche lzma
    _LZMA_SUPPORTED = Wahr
ausser ImportError:
    _LZMA_SUPPORTED = Falsch

versuch:
    von compression importiere zstd
    loesche zstd
    _ZSTD_SUPPORTED = Wahr
ausser ImportError:
    _ZSTD_SUPPORTED = Falsch

_WINDOWS = os.name == 'nt'
posix = nt = Nichts
wenn os.name == 'posix':
    importiere posix
sowenn _WINDOWS:
    importiere nt

wenn sys.platform == 'win32':
    importiere _winapi
sonst:
    _winapi = Nichts

COPY_BUFSIZE = 1024 * 1024 wenn _WINDOWS sonst 256 * 1024
# This should never be removed, see rationale in:
# https://bugs.python.org/issue43743#msg393429
_USE_CP_SENDFILE = (hasattr(os, "sendfile")
                    und sys.platform.startswith(("linux", "android", "sunos")))
_USE_CP_COPY_FILE_RANGE = hasattr(os, "copy_file_range")
_HAS_FCOPYFILE = posix und hasattr(posix, "_fcopyfile")  # macOS

# CMD defaults in Windows 10
_WIN_DEFAULT_PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC"

__all__ = ["copyfileobj", "copyfile", "copymode", "copystat", "copy", "copy2",
           "copytree", "move", "rmtree", "Error", "SpecialFileError",
           "make_archive", "get_archive_formats",
           "register_archive_format", "unregister_archive_format",
           "get_unpack_formats", "register_unpack_format",
           "unregister_unpack_format", "unpack_archive",
           "ignore_patterns", "chown", "which", "get_terminal_size",
           "SameFileError"]
           # disk_usage ist added later, wenn available on the platform

klasse Error(OSError):
    pass

klasse SameFileError(Error):
    """Raised when source und destination are the same file."""

klasse SpecialFileError(OSError):
    """Raised when trying to do a kind of operation (e.g. copying) which is
    nicht supported on a special file (e.g. a named pipe)"""


klasse ReadError(OSError):
    """Raised when an archive cannot be read"""

klasse RegistryError(Exception):
    """Raised when a registry operation mit the archiving
    und unpacking registries fails"""

klasse _GiveupOnFastCopy(Exception):
    """Raised als a signal to fallback on using raw read()/write()
    file copy when fast-copy functions fail to do so.
    """

def _fastcopy_fcopyfile(fsrc, fdst, flags):
    """Copy a regular file content oder metadata by using high-performance
    fcopyfile(3) syscall (macOS).
    """
    versuch:
        infd = fsrc.fileno()
        outfd = fdst.fileno()
    ausser Exception als err:
        wirf _GiveupOnFastCopy(err)  # nicht a regular file

    versuch:
        posix._fcopyfile(infd, outfd, flags)
    ausser OSError als err:
        err.filename = fsrc.name
        err.filename2 = fdst.name
        wenn err.errno in {errno.EINVAL, errno.ENOTSUP}:
            wirf _GiveupOnFastCopy(err)
        sonst:
            wirf err von Nichts

def _determine_linux_fastcopy_blocksize(infd):
    """Determine blocksize fuer fastcopying on Linux.

    Hopefully the whole file will be copied in a single call.
    The copying itself should be performed in a loop 'till EOF is
    reached (0 return) so a blocksize smaller oder bigger than the actual
    file size should nicht make any difference, also in case the file
    content changes waehrend being copied.
    """
    versuch:
        blocksize = max(os.fstat(infd).st_size, 2 ** 23)  # min 8 MiB
    ausser OSError:
        blocksize = 2 ** 27  # 128 MiB
    # On 32-bit architectures truncate to 1 GiB to avoid OverflowError,
    # see gh-82500.
    wenn sys.maxsize < 2 ** 32:
        blocksize = min(blocksize, 2 ** 30)
    gib blocksize

def _fastcopy_copy_file_range(fsrc, fdst):
    """Copy data von one regular mmap-like fd to another by using
    a high-performance copy_file_range(2) syscall that gives filesystems
    an opportunity to implement the use of reflinks oder server-side copy.

    This should work on Linux >= 4.5 only.
    """
    versuch:
        infd = fsrc.fileno()
        outfd = fdst.fileno()
    ausser Exception als err:
        wirf _GiveupOnFastCopy(err)  # nicht a regular file

    blocksize = _determine_linux_fastcopy_blocksize(infd)
    offset = 0
    waehrend Wahr:
        versuch:
            n_copied = os.copy_file_range(infd, outfd, blocksize, offset_dst=offset)
        ausser OSError als err:
            # ...in oder to have a more informative exception.
            err.filename = fsrc.name
            err.filename2 = fdst.name

            wenn err.errno == errno.ENOSPC:  # filesystem ist full
                wirf err von Nichts

            # Give up on first call und wenn no data was copied.
            wenn offset == 0 und os.lseek(outfd, 0, os.SEEK_CUR) == 0:
                wirf _GiveupOnFastCopy(err)

            wirf err
        sonst:
            wenn n_copied == 0:
                # If no bytes have been copied yet, copy_file_range
                # might silently fail.
                # https://lore.kernel.org/linux-fsdevel/20210126233840.GG4626@dread.disaster.area/T/#m05753578c7f7882f6e9ffe01f981bc223edef2b0
                wenn offset == 0:
                    wirf _GiveupOnFastCopy()
                breche
            offset += n_copied

def _fastcopy_sendfile(fsrc, fdst):
    """Copy data von one regular mmap-like fd to another by using
    high-performance sendfile(2) syscall.
    This should work on Linux >= 2.6.33, Android und Solaris.
    """
    # Note: copyfileobj() ist left alone in order to nicht introduce any
    # unexpected breakage. Possible risks by using zero-copy calls
    # in copyfileobj() are:
    # - fdst cannot be open in "a"(ppend) mode
    # - fsrc und fdst may be open in "t"(ext) mode
    # - fsrc may be a BufferedReader (which hides unread data in a buffer),
    #   GzipFile (which decompresses data), HTTPResponse (which decodes
    #   chunks).
    # - possibly others (e.g. encrypted fs/partition?)
    global _USE_CP_SENDFILE
    versuch:
        infd = fsrc.fileno()
        outfd = fdst.fileno()
    ausser Exception als err:
        wirf _GiveupOnFastCopy(err)  # nicht a regular file

    blocksize = _determine_linux_fastcopy_blocksize(infd)
    offset = 0
    waehrend Wahr:
        versuch:
            sent = os.sendfile(outfd, infd, offset, blocksize)
        ausser OSError als err:
            # ...in order to have a more informative exception.
            err.filename = fsrc.name
            err.filename2 = fdst.name

            wenn err.errno == errno.ENOTSOCK:
                # sendfile() on this platform (probably Linux < 2.6.33)
                # does nicht support copies between regular files (only
                # sockets).
                _USE_CP_SENDFILE = Falsch
                wirf _GiveupOnFastCopy(err)

            wenn err.errno == errno.ENOSPC:  # filesystem ist full
                wirf err von Nichts

            # Give up on first call und wenn no data was copied.
            wenn offset == 0 und os.lseek(outfd, 0, os.SEEK_CUR) == 0:
                wirf _GiveupOnFastCopy(err)

            wirf err
        sonst:
            wenn sent == 0:
                breche  # EOF
            offset += sent

def _copyfileobj_readinto(fsrc, fdst, length=COPY_BUFSIZE):
    """readinto()/memoryview() based variant of copyfileobj().
    *fsrc* must support readinto() method und both files must be
    open in binary mode.
    """
    # Localize variable access to minimize overhead.
    fsrc_readinto = fsrc.readinto
    fdst_write = fdst.write
    mit memoryview(bytearray(length)) als mv:
        waehrend Wahr:
            n = fsrc_readinto(mv)
            wenn nicht n:
                breche
            sowenn n < length:
                mit mv[:n] als smv:
                    fdst_write(smv)
                breche
            sonst:
                fdst_write(mv)

def copyfileobj(fsrc, fdst, length=0):
    """copy data von file-like object fsrc to file-like object fdst"""
    wenn nicht length:
        length = COPY_BUFSIZE
    # Localize variable access to minimize overhead.
    fsrc_read = fsrc.read
    fdst_write = fdst.write
    waehrend buf := fsrc_read(length):
        fdst_write(buf)

def _samefile(src, dst):
    # Macintosh, Unix.
    wenn isinstance(src, os.DirEntry) und hasattr(os.path, 'samestat'):
        versuch:
            gib os.path.samestat(src.stat(), os.stat(dst))
        ausser OSError:
            gib Falsch

    wenn hasattr(os.path, 'samefile'):
        versuch:
            gib os.path.samefile(src, dst)
        ausser OSError:
            gib Falsch

    # All other platforms: check fuer same pathname.
    gib (os.path.normcase(os.path.abspath(src)) ==
            os.path.normcase(os.path.abspath(dst)))

def _stat(fn):
    gib fn.stat() wenn isinstance(fn, os.DirEntry) sonst os.stat(fn)

def _islink(fn):
    gib fn.is_symlink() wenn isinstance(fn, os.DirEntry) sonst os.path.islink(fn)

def copyfile(src, dst, *, follow_symlinks=Wahr):
    """Copy data von src to dst in the most efficient way possible.

    If follow_symlinks ist nicht set und src ist a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    sys.audit("shutil.copyfile", src, dst)

    wenn _samefile(src, dst):
        wirf SameFileError("{!r} und {!r} are the same file".format(src, dst))

    file_size = 0
    fuer i, fn in enumerate([src, dst]):
        versuch:
            st = _stat(fn)
        ausser OSError:
            # File most likely does nicht exist
            pass
        sonst:
            # XXX What about other special files? (sockets, devices...)
            wenn stat.S_ISFIFO(st.st_mode):
                fn = fn.path wenn isinstance(fn, os.DirEntry) sonst fn
                wirf SpecialFileError("`%s` ist a named pipe" % fn)
            wenn _WINDOWS und i == 0:
                file_size = st.st_size

    wenn nicht follow_symlinks und _islink(src):
        os.symlink(os.readlink(src), dst)
    sonst:
        mit open(src, 'rb') als fsrc:
            versuch:
                mit open(dst, 'wb') als fdst:
                    # macOS
                    wenn _HAS_FCOPYFILE:
                        versuch:
                            _fastcopy_fcopyfile(fsrc, fdst, posix._COPYFILE_DATA)
                            gib dst
                        ausser _GiveupOnFastCopy:
                            pass
                    # Linux / Android / Solaris
                    sowenn _USE_CP_SENDFILE oder _USE_CP_COPY_FILE_RANGE:
                        # reflink may be implicit in copy_file_range.
                        wenn _USE_CP_COPY_FILE_RANGE:
                            versuch:
                                _fastcopy_copy_file_range(fsrc, fdst)
                                gib dst
                            ausser _GiveupOnFastCopy:
                                pass
                        wenn _USE_CP_SENDFILE:
                            versuch:
                                _fastcopy_sendfile(fsrc, fdst)
                                gib dst
                            ausser _GiveupOnFastCopy:
                                pass
                    # Windows, see:
                    # https://github.com/python/cpython/pull/7160#discussion_r195405230
                    sowenn _WINDOWS und file_size > 0:
                        _copyfileobj_readinto(fsrc, fdst, min(file_size, COPY_BUFSIZE))
                        gib dst

                    copyfileobj(fsrc, fdst)

            # Issue 43219, wirf a less confusing exception
            ausser IsADirectoryError als e:
                wenn nicht os.path.exists(dst):
                    wirf FileNotFoundError(f'Directory does nicht exist: {dst}') von e
                sonst:
                    wirf

    gib dst

def copymode(src, dst, *, follow_symlinks=Wahr):
    """Copy mode bits von src to dst.

    If follow_symlinks ist nicht set, symlinks aren't followed wenn und only
    wenn both `src` und `dst` are symlinks.  If `lchmod` isn't available
    (e.g. Linux) this method does nothing.

    """
    sys.audit("shutil.copymode", src, dst)

    wenn nicht follow_symlinks und _islink(src) und os.path.islink(dst):
        wenn hasattr(os, 'lchmod'):
            stat_func, chmod_func = os.lstat, os.lchmod
        sonst:
            gib
    sonst:
        stat_func = _stat
        wenn os.name == 'nt' und os.path.islink(dst):
            def chmod_func(*args):
                os.chmod(*args, follow_symlinks=Wahr)
        sonst:
            chmod_func = os.chmod

    st = stat_func(src)
    chmod_func(dst, stat.S_IMODE(st.st_mode))

wenn hasattr(os, 'listxattr'):
    def _copyxattr(src, dst, *, follow_symlinks=Wahr):
        """Copy extended filesystem attributes von `src` to `dst`.

        Overwrite existing attributes.

        If `follow_symlinks` ist false, symlinks won't be followed.

        """

        versuch:
            names = os.listxattr(src, follow_symlinks=follow_symlinks)
        ausser OSError als e:
            wenn e.errno nicht in (errno.ENOTSUP, errno.ENODATA, errno.EINVAL):
                wirf
            gib
        fuer name in names:
            versuch:
                value = os.getxattr(src, name, follow_symlinks=follow_symlinks)
                os.setxattr(dst, name, value, follow_symlinks=follow_symlinks)
            ausser OSError als e:
                wenn e.errno nicht in (errno.EPERM, errno.ENOTSUP, errno.ENODATA,
                                   errno.EINVAL, errno.EACCES):
                    wirf
sonst:
    def _copyxattr(*args, **kwargs):
        pass

def copystat(src, dst, *, follow_symlinks=Wahr):
    """Copy file metadata

    Copy the permission bits, last access time, last modification time, und
    flags von `src` to `dst`. On Linux, copystat() also copies the "extended
    attributes" where possible. The file contents, owner, und group are
    unaffected. `src` und `dst` are path-like objects oder path names given as
    strings.

    If the optional flag `follow_symlinks` ist nicht set, symlinks aren't
    followed wenn und only wenn both `src` und `dst` are symlinks.
    """
    sys.audit("shutil.copystat", src, dst)

    def _nop(*args, ns=Nichts, follow_symlinks=Nichts):
        pass

    # follow symlinks (aka don't nicht follow symlinks)
    follow = follow_symlinks oder nicht (_islink(src) und os.path.islink(dst))
    wenn follow:
        # use the real function wenn it exists
        def lookup(name):
            gib getattr(os, name, _nop)
    sonst:
        # use the real function only wenn it exists
        # *and* it supports follow_symlinks
        def lookup(name):
            fn = getattr(os, name, _nop)
            wenn fn in os.supports_follow_symlinks:
                gib fn
            gib _nop

    wenn isinstance(src, os.DirEntry):
        st = src.stat(follow_symlinks=follow)
    sonst:
        st = lookup("stat")(src, follow_symlinks=follow)
    mode = stat.S_IMODE(st.st_mode)
    lookup("utime")(dst, ns=(st.st_atime_ns, st.st_mtime_ns),
        follow_symlinks=follow)
    # We must copy extended attributes before the file ist (potentially)
    # chmod()'ed read-only, otherwise setxattr() will error mit -EACCES.
    _copyxattr(src, dst, follow_symlinks=follow)
    versuch:
        lookup("chmod")(dst, mode, follow_symlinks=follow)
    ausser NotImplementedError:
        # wenn we got a NotImplementedError, it's because
        #   * follow_symlinks=Falsch,
        #   * lchown() ist unavailable, und
        #   * either
        #       * fchownat() ist unavailable oder
        #       * fchownat() doesn't implement AT_SYMLINK_NOFOLLOW.
        #         (it returned ENOSUP.)
        # therefore we're out of options--we simply cannot chown the
        # symlink.  give up, suppress the error.
        # (which ist what shutil always did in this circumstance.)
        pass
    wenn hasattr(st, 'st_flags'):
        versuch:
            lookup("chflags")(dst, st.st_flags, follow_symlinks=follow)
        ausser OSError als why:
            fuer err in 'EOPNOTSUPP', 'ENOTSUP':
                wenn hasattr(errno, err) und why.errno == getattr(errno, err):
                    breche
            sonst:
                wirf

def copy(src, dst, *, follow_symlinks=Wahr):
    """Copy data und mode bits ("cp src dst"). Return the file's destination.

    The destination may be a directory.

    If follow_symlinks ist false, symlinks won't be followed. This
    resembles GNU's "cp -P src dst".

    If source und destination are the same file, a SameFileError will be
    raised.

    """
    wenn os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst, follow_symlinks=follow_symlinks)
    copymode(src, dst, follow_symlinks=follow_symlinks)
    gib dst

def copy2(src, dst, *, follow_symlinks=Wahr):
    """Copy data und metadata. Return the file's destination.

    Metadata ist copied mit copystat(). Please see the copystat function
    fuer more information.

    The destination may be a directory.

    If follow_symlinks ist false, symlinks won't be followed. This
    resembles GNU's "cp -P src dst".
    """
    wenn os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    wenn hasattr(_winapi, "CopyFile2"):
        src_ = os.fsdecode(src)
        dst_ = os.fsdecode(dst)
        flags = _winapi.COPY_FILE_ALLOW_DECRYPTED_DESTINATION # fuer compat
        wenn nicht follow_symlinks:
            flags |= _winapi.COPY_FILE_COPY_SYMLINK
        versuch:
            _winapi.CopyFile2(src_, dst_, flags)
            gib dst
        ausser OSError als exc:
            wenn (exc.winerror == _winapi.ERROR_PRIVILEGE_NOT_HELD
                und nicht follow_symlinks):
                # Likely encountered a symlink we aren't allowed to create.
                # Fall back on the old code
                pass
            sowenn exc.winerror == _winapi.ERROR_ACCESS_DENIED:
                # Possibly encountered a hidden oder readonly file we can't
                # overwrite. Fall back on old code
                pass
            sonst:
                wirf

    copyfile(src, dst, follow_symlinks=follow_symlinks)
    copystat(src, dst, follow_symlinks=follow_symlinks)
    gib dst

def ignore_patterns(*patterns):
    """Function that can be used als copytree() ignore parameter.

    Patterns ist a sequence of glob-style patterns
    that are used to exclude files"""
    def _ignore_patterns(path, names):
        ignored_names = []
        fuer pattern in patterns:
            ignored_names.extend(fnmatch.filter(names, pattern))
        gib set(ignored_names)
    gib _ignore_patterns

def _copytree(entries, src, dst, symlinks, ignore, copy_function,
              ignore_dangling_symlinks, dirs_exist_ok=Falsch):
    wenn ignore ist nicht Nichts:
        ignored_names = ignore(os.fspath(src), [x.name fuer x in entries])
    sonst:
        ignored_names = ()

    os.makedirs(dst, exist_ok=dirs_exist_ok)
    errors = []
    use_srcentry = copy_function ist copy2 oder copy_function ist copy

    fuer srcentry in entries:
        wenn srcentry.name in ignored_names:
            weiter
        srcname = os.path.join(src, srcentry.name)
        dstname = os.path.join(dst, srcentry.name)
        srcobj = srcentry wenn use_srcentry sonst srcname
        versuch:
            is_symlink = srcentry.is_symlink()
            wenn is_symlink und os.name == 'nt':
                # Special check fuer directory junctions, which appear as
                # symlinks but we want to recurse.
                lstat = srcentry.stat(follow_symlinks=Falsch)
                wenn lstat.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
                    is_symlink = Falsch
            wenn is_symlink:
                linkto = os.readlink(srcname)
                wenn symlinks:
                    # We can't just leave it to `copy_function` because legacy
                    # code mit a custom `copy_function` may rely on copytree
                    # doing the right thing.
                    os.symlink(linkto, dstname)
                    copystat(srcobj, dstname, follow_symlinks=nicht symlinks)
                sonst:
                    # ignore dangling symlink wenn the flag ist on
                    wenn nicht os.path.exists(linkto) und ignore_dangling_symlinks:
                        weiter
                    # otherwise let the copy occur. copy2 will wirf an error
                    wenn srcentry.is_dir():
                        copytree(srcobj, dstname, symlinks, ignore,
                                 copy_function, ignore_dangling_symlinks,
                                 dirs_exist_ok)
                    sonst:
                        copy_function(srcobj, dstname)
            sowenn srcentry.is_dir():
                copytree(srcobj, dstname, symlinks, ignore, copy_function,
                         ignore_dangling_symlinks, dirs_exist_ok)
            sonst:
                # Will wirf a SpecialFileError fuer unsupported file types
                copy_function(srcobj, dstname)
        # catch the Error von the recursive copytree so that we can
        # weiter mit other files
        ausser Error als err:
            errors.extend(err.args[0])
        ausser OSError als why:
            errors.append((srcname, dstname, str(why)))
    versuch:
        copystat(src, dst)
    ausser OSError als why:
        # Copying file access times may fail on Windows
        wenn getattr(why, 'winerror', Nichts) ist Nichts:
            errors.append((src, dst, str(why)))
    wenn errors:
        wirf Error(errors)
    gib dst

def copytree(src, dst, symlinks=Falsch, ignore=Nichts, copy_function=copy2,
             ignore_dangling_symlinks=Falsch, dirs_exist_ok=Falsch):
    """Recursively copy a directory tree und gib the destination directory.

    If exception(s) occur, an Error ist raised mit a list of reasons.

    If the optional symlinks flag ist true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it ist false, the contents of the files pointed to by symbolic
    links are copied. If the file pointed to by the symlink doesn't
    exist, an exception will be added in the list of errors raised in
    an Error exception at the end of the copy process.

    You can set the optional ignore_dangling_symlinks flag to true wenn you
    want to silence this exception. Notice that this has no effect on
    platforms that don't support os.symlink.

    The optional ignore argument ist a callable. If given, it
    ist called mit the `src` parameter, which ist the directory
    being visited by copytree(), und `names` which ist the list of
    `src` contents, als returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() ist called recursively, the callable will be
    called once fuer each directory that ist copied. It returns a
    list of names relative to the `src` directory that should
    nicht be copied.

    The optional copy_function argument ist a callable that will be used
    to copy each file. It will be called mit the source path und the
    destination path als arguments. By default, copy2() ist used, but any
    function that supports the same signature (like copy()) can be used.

    If dirs_exist_ok ist false (the default) und `dst` already exists, a
    `FileExistsError` ist raised. If `dirs_exist_ok` ist true, the copying
    operation will weiter wenn it encounters existing directories, und files
    within the `dst` tree will be overwritten by corresponding files von the
    `src` tree.
    """
    sys.audit("shutil.copytree", src, dst)
    mit os.scandir(src) als itr:
        entries = list(itr)
    gib _copytree(entries=entries, src=src, dst=dst, symlinks=symlinks,
                     ignore=ignore, copy_function=copy_function,
                     ignore_dangling_symlinks=ignore_dangling_symlinks,
                     dirs_exist_ok=dirs_exist_ok)

wenn hasattr(os.stat_result, 'st_file_attributes'):
    def _rmtree_islink(st):
        gib (stat.S_ISLNK(st.st_mode) oder
            (st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                und st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT))
sonst:
    def _rmtree_islink(st):
        gib stat.S_ISLNK(st.st_mode)

# version vulnerable to race conditions
def _rmtree_unsafe(path, dir_fd, onexc):
    wenn dir_fd ist nicht Nichts:
        wirf NotImplementedError("dir_fd unavailable on this platform")
    versuch:
        st = os.lstat(path)
    ausser OSError als err:
        onexc(os.lstat, path, err)
        gib
    versuch:
        wenn _rmtree_islink(st):
            # symlinks to directories are forbidden, see bug #1669
            wirf OSError("Cannot call rmtree on a symbolic link")
    ausser OSError als err:
        onexc(os.path.islink, path, err)
        # can't weiter even wenn onexc hook returns
        gib
    def onerror(err):
        wenn nicht isinstance(err, FileNotFoundError):
            onexc(os.scandir, err.filename, err)
    results = os.walk(path, topdown=Falsch, onerror=onerror, followlinks=os._walk_symlinks_as_files)
    fuer dirpath, dirnames, filenames in results:
        fuer name in dirnames:
            fullname = os.path.join(dirpath, name)
            versuch:
                os.rmdir(fullname)
            ausser FileNotFoundError:
                weiter
            ausser OSError als err:
                onexc(os.rmdir, fullname, err)
        fuer name in filenames:
            fullname = os.path.join(dirpath, name)
            versuch:
                os.unlink(fullname)
            ausser FileNotFoundError:
                weiter
            ausser OSError als err:
                onexc(os.unlink, fullname, err)
    versuch:
        os.rmdir(path)
    ausser FileNotFoundError:
        pass
    ausser OSError als err:
        onexc(os.rmdir, path, err)

# Version using fd-based APIs to protect against races
def _rmtree_safe_fd(path, dir_fd, onexc):
    # While the unsafe rmtree works fine on bytes, the fd based does not.
    wenn isinstance(path, bytes):
        path = os.fsdecode(path)
    stack = [(os.lstat, dir_fd, path, Nichts)]
    versuch:
        waehrend stack:
            _rmtree_safe_fd_step(stack, onexc)
    schliesslich:
        # Close any file descriptors still on the stack.
        waehrend stack:
            func, fd, path, entry = stack.pop()
            wenn func ist nicht os.close:
                weiter
            versuch:
                os.close(fd)
            ausser OSError als err:
                onexc(os.close, path, err)

def _rmtree_safe_fd_step(stack, onexc):
    # Each stack item has four elements:
    # * func: The first operation to perform: os.lstat, os.close oder os.rmdir.
    #   Walking a directory starts mit an os.lstat() to detect symlinks; in
    #   this case, func ist updated before subsequent operations und passed to
    #   onexc() wenn an error occurs.
    # * dirfd: Open file descriptor, oder Nichts wenn we're processing the top-level
    #   directory given to rmtree() und the user didn't supply dir_fd.
    # * path: Path of file to operate upon. This ist passed to onexc() wenn an
    #   error occurs.
    # * orig_entry: os.DirEntry, oder Nichts wenn we're processing the top-level
    #   directory given to rmtree(). We used the cached stat() of the entry to
    #   save a call to os.lstat() when walking subdirectories.
    func, dirfd, path, orig_entry = stack.pop()
    name = path wenn orig_entry ist Nichts sonst orig_entry.name
    versuch:
        wenn func ist os.close:
            os.close(dirfd)
            gib
        wenn func ist os.rmdir:
            os.rmdir(name, dir_fd=dirfd)
            gib

        # Note: To guard against symlink races, we use the standard
        # lstat()/open()/fstat() trick.
        assert func ist os.lstat
        wenn orig_entry ist Nichts:
            orig_st = os.lstat(name, dir_fd=dirfd)
        sonst:
            orig_st = orig_entry.stat(follow_symlinks=Falsch)

        func = os.open  # For error reporting.
        topfd = os.open(name, os.O_RDONLY | os.O_NONBLOCK, dir_fd=dirfd)

        func = os.path.islink  # For error reporting.
        versuch:
            wenn nicht os.path.samestat(orig_st, os.fstat(topfd)):
                # Symlinks to directories are forbidden, see GH-46010.
                wirf OSError("Cannot call rmtree on a symbolic link")
            stack.append((os.rmdir, dirfd, path, orig_entry))
        schliesslich:
            stack.append((os.close, topfd, path, orig_entry))

        func = os.scandir  # For error reporting.
        mit os.scandir(topfd) als scandir_it:
            entries = list(scandir_it)
        fuer entry in entries:
            fullname = os.path.join(path, entry.name)
            versuch:
                wenn entry.is_dir(follow_symlinks=Falsch):
                    # Traverse into sub-directory.
                    stack.append((os.lstat, topfd, fullname, entry))
                    weiter
            ausser FileNotFoundError:
                weiter
            ausser OSError:
                pass
            versuch:
                os.unlink(entry.name, dir_fd=topfd)
            ausser FileNotFoundError:
                weiter
            ausser OSError als err:
                onexc(os.unlink, fullname, err)
    ausser FileNotFoundError als err:
        wenn orig_entry ist Nichts oder func ist os.close:
            err.filename = path
            onexc(func, path, err)
    ausser OSError als err:
        err.filename = path
        onexc(func, path, err)

_use_fd_functions = ({os.open, os.stat, os.unlink, os.rmdir} <=
                     os.supports_dir_fd und
                     os.scandir in os.supports_fd und
                     os.stat in os.supports_follow_symlinks)
_rmtree_impl = _rmtree_safe_fd wenn _use_fd_functions sonst _rmtree_unsafe

def rmtree(path, ignore_errors=Falsch, onerror=Nichts, *, onexc=Nichts, dir_fd=Nichts):
    """Recursively delete a directory tree.

    If dir_fd ist nicht Nichts, it should be a file descriptor open to a directory;
    path will then be relative to that directory.
    dir_fd may nicht be implemented on your platform.
    If it ist unavailable, using it will wirf a NotImplementedError.

    If ignore_errors ist set, errors are ignored; otherwise, wenn onexc oder
    onerror ist set, it ist called to handle the error mit arguments (func,
    path, exc_info) where func ist platform und implementation dependent;
    path ist the argument to that function that caused it to fail; und
    the value of exc_info describes the exception. For onexc it ist the
    exception instance, und fuer onerror it ist a tuple als returned by
    sys.exc_info().  If ignore_errors ist false und both onexc und
    onerror are Nichts, the exception ist reraised.

    onerror ist deprecated und only remains fuer backwards compatibility.
    If both onerror und onexc are set, onerror ist ignored und onexc ist used.
    """

    sys.audit("shutil.rmtree", path, dir_fd)
    wenn ignore_errors:
        def onexc(*args):
            pass
    sowenn onerror ist Nichts und onexc ist Nichts:
        def onexc(*args):
            wirf
    sowenn onexc ist Nichts:
        wenn onerror ist Nichts:
            def onexc(*args):
                wirf
        sonst:
            # delegate to onerror
            def onexc(*args):
                func, path, exc = args
                wenn exc ist Nichts:
                    exc_info = Nichts, Nichts, Nichts
                sonst:
                    exc_info = type(exc), exc, exc.__traceback__
                gib onerror(func, path, exc_info)

    _rmtree_impl(path, dir_fd, onexc)

# Allow introspection of whether oder nicht the hardening against symlink
# attacks ist supported on the current platform
rmtree.avoids_symlink_attacks = _use_fd_functions

def _basename(path):
    """A basename() variant which first strips the trailing slash, wenn present.
    Thus we always get the last component of the path, even fuer directories.

    path: Union[PathLike, str]

    e.g.
    >>> os.path.basename('/bar/foo')
    'foo'
    >>> os.path.basename('/bar/foo/')
    ''
    >>> _basename('/bar/foo/')
    'foo'
    """
    path = os.fspath(path)
    sep = os.path.sep + (os.path.altsep oder '')
    gib os.path.basename(path.rstrip(sep))

def move(src, dst, copy_function=copy2):
    """Recursively move a file oder directory to another location. This is
    similar to the Unix "mv" command. Return the file oder directory's
    destination.

    If dst ist an existing directory oder a symlink to a directory, then src is
    moved inside that directory. The destination path in that directory must
    nicht already exist.

    If dst already exists but ist nicht a directory, it may be overwritten
    depending on os.rename() semantics.

    If the destination ist on our current filesystem, then rename() ist used.
    Otherwise, src ist copied to the destination und then removed. Symlinks are
    recreated under the new name wenn os.rename() fails because of cross
    filesystem renames.

    The optional `copy_function` argument ist a callable that will be used
    to copy the source oder it will be delegated to `copytree`.
    By default, copy2() ist used, but any function that supports the same
    signature (like copy()) can be used.

    A lot more could be done here...  A look at a mv.c shows a lot of
    the issues this implementation glosses over.

    """
    sys.audit("shutil.move", src, dst)
    real_dst = dst
    wenn os.path.isdir(dst):
        wenn _samefile(src, dst) und nicht os.path.islink(src):
            # We might be on a case insensitive filesystem,
            # perform the rename anyway.
            os.rename(src, dst)
            gib

        # Using _basename instead of os.path.basename ist important, als we must
        # ignore any trailing slash to avoid the basename returning ''
        real_dst = os.path.join(dst, _basename(src))

        wenn os.path.exists(real_dst):
            wirf Error("Destination path '%s' already exists" % real_dst)
    versuch:
        os.rename(src, real_dst)
    ausser OSError:
        wenn os.path.islink(src):
            linkto = os.readlink(src)
            os.symlink(linkto, real_dst)
            os.unlink(src)
        sowenn os.path.isdir(src):
            wenn _destinsrc(src, dst):
                wirf Error("Cannot move a directory '%s' into itself"
                            " '%s'." % (src, dst))
            wenn (_is_immutable(src)
                    oder (nicht os.access(src, os.W_OK) und os.listdir(src)
                        und sys.platform == 'darwin')):
                wirf PermissionError("Cannot move the non-empty directory "
                                      "'%s': Lacking write permission to '%s'."
                                      % (src, src))
            copytree(src, real_dst, copy_function=copy_function,
                     symlinks=Wahr)
            rmtree(src)
        sonst:
            copy_function(src, real_dst)
            os.unlink(src)
    gib real_dst

def _destinsrc(src, dst):
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    wenn nicht src.endswith(os.path.sep):
        src += os.path.sep
    wenn nicht dst.endswith(os.path.sep):
        dst += os.path.sep
    gib dst.startswith(src)

def _is_immutable(src):
    st = _stat(src)
    immutable_states = [stat.UF_IMMUTABLE, stat.SF_IMMUTABLE]
    gib hasattr(st, 'st_flags') und st.st_flags in immutable_states

def _get_gid(name):
    """Returns a gid, given a group name."""
    wenn name ist Nichts:
        gib Nichts

    versuch:
        von grp importiere getgrnam
    ausser ImportError:
        gib Nichts

    versuch:
        result = getgrnam(name)
    ausser KeyError:
        result = Nichts
    wenn result ist nicht Nichts:
        gib result[2]
    gib Nichts

def _get_uid(name):
    """Returns an uid, given a user name."""
    wenn name ist Nichts:
        gib Nichts

    versuch:
        von pwd importiere getpwnam
    ausser ImportError:
        gib Nichts

    versuch:
        result = getpwnam(name)
    ausser KeyError:
        result = Nichts
    wenn result ist nicht Nichts:
        gib result[2]
    gib Nichts

def _make_tarball(base_name, base_dir, compress="gzip", verbose=0, dry_run=0,
                  owner=Nichts, group=Nichts, logger=Nichts, root_dir=Nichts):
    """Create a (possibly compressed) tar file von all the files under
    'base_dir'.

    'compress' must be "gzip" (the default), "bzip2", "xz", "zst", oder Nichts.

    'owner' und 'group' can be used to define an owner und a group fuer the
    archive that ist being built. If nicht provided, the current owner und group
    will be used.

    The output tar file will be named 'base_name' +  ".tar", possibly plus
    the appropriate compression extension (".gz", ".bz2", ".xz", oder ".zst").

    Returns the output filename.
    """
    wenn compress ist Nichts:
        tar_compression = ''
    sowenn _ZLIB_SUPPORTED und compress == 'gzip':
        tar_compression = 'gz'
    sowenn _BZ2_SUPPORTED und compress == 'bzip2':
        tar_compression = 'bz2'
    sowenn _LZMA_SUPPORTED und compress == 'xz':
        tar_compression = 'xz'
    sowenn _ZSTD_SUPPORTED und compress == 'zst':
        tar_compression = 'zst'
    sonst:
        wirf ValueError("bad value fuer 'compress', oder compression format nicht "
                         "supported : {0}".format(compress))

    importiere tarfile  # late importiere fuer breaking circular dependency

    compress_ext = '.' + tar_compression wenn compress sonst ''
    archive_name = base_name + '.tar' + compress_ext
    archive_dir = os.path.dirname(archive_name)

    wenn archive_dir und nicht os.path.exists(archive_dir):
        wenn logger ist nicht Nichts:
            logger.info("creating %s", archive_dir)
        wenn nicht dry_run:
            os.makedirs(archive_dir)

    # creating the tarball
    wenn logger ist nicht Nichts:
        logger.info('Creating tar archive')

    uid = _get_uid(owner)
    gid = _get_gid(group)

    def _set_uid_gid(tarinfo):
        wenn gid ist nicht Nichts:
            tarinfo.gid = gid
            tarinfo.gname = group
        wenn uid ist nicht Nichts:
            tarinfo.uid = uid
            tarinfo.uname = owner
        gib tarinfo

    wenn nicht dry_run:
        tar = tarfile.open(archive_name, 'w|%s' % tar_compression)
        arcname = base_dir
        wenn root_dir ist nicht Nichts:
            base_dir = os.path.join(root_dir, base_dir)
        versuch:
            tar.add(base_dir, arcname, filter=_set_uid_gid)
        schliesslich:
            tar.close()

    wenn root_dir ist nicht Nichts:
        archive_name = os.path.abspath(archive_name)
    gib archive_name

def _make_zipfile(base_name, base_dir, verbose=0, dry_run=0,
                  logger=Nichts, owner=Nichts, group=Nichts, root_dir=Nichts):
    """Create a zip file von all the files under 'base_dir'.

    The output zip file will be named 'base_name' + ".zip".  Returns the
    name of the output zip file.
    """
    importiere zipfile  # late importiere fuer breaking circular dependency

    zip_filename = base_name + ".zip"
    archive_dir = os.path.dirname(base_name)

    wenn archive_dir und nicht os.path.exists(archive_dir):
        wenn logger ist nicht Nichts:
            logger.info("creating %s", archive_dir)
        wenn nicht dry_run:
            os.makedirs(archive_dir)

    wenn logger ist nicht Nichts:
        logger.info("creating '%s' und adding '%s' to it",
                    zip_filename, base_dir)

    wenn nicht dry_run:
        mit zipfile.ZipFile(zip_filename, "w",
                             compression=zipfile.ZIP_DEFLATED) als zf:
            arcname = os.path.normpath(base_dir)
            wenn root_dir ist nicht Nichts:
                base_dir = os.path.join(root_dir, base_dir)
            base_dir = os.path.normpath(base_dir)
            wenn arcname != os.curdir:
                zf.write(base_dir, arcname)
                wenn logger ist nicht Nichts:
                    logger.info("adding '%s'", base_dir)
            fuer dirpath, dirnames, filenames in os.walk(base_dir):
                arcdirpath = dirpath
                wenn root_dir ist nicht Nichts:
                    arcdirpath = os.path.relpath(arcdirpath, root_dir)
                arcdirpath = os.path.normpath(arcdirpath)
                fuer name in sorted(dirnames):
                    path = os.path.join(dirpath, name)
                    arcname = os.path.join(arcdirpath, name)
                    zf.write(path, arcname)
                    wenn logger ist nicht Nichts:
                        logger.info("adding '%s'", path)
                fuer name in filenames:
                    path = os.path.join(dirpath, name)
                    path = os.path.normpath(path)
                    wenn os.path.isfile(path):
                        arcname = os.path.join(arcdirpath, name)
                        zf.write(path, arcname)
                        wenn logger ist nicht Nichts:
                            logger.info("adding '%s'", path)

    wenn root_dir ist nicht Nichts:
        zip_filename = os.path.abspath(zip_filename)
    gib zip_filename

_make_tarball.supports_root_dir = Wahr
_make_zipfile.supports_root_dir = Wahr

# Maps the name of the archive format to a tuple containing:
# * the archiving function
# * extra keyword arguments
# * description
_ARCHIVE_FORMATS = {
    'tar':   (_make_tarball, [('compress', Nichts)],
              "uncompressed tar file"),
}

wenn _ZLIB_SUPPORTED:
    _ARCHIVE_FORMATS['gztar'] = (_make_tarball, [('compress', 'gzip')],
                                "gzip'ed tar-file")
    _ARCHIVE_FORMATS['zip'] = (_make_zipfile, [], "ZIP file")

wenn _BZ2_SUPPORTED:
    _ARCHIVE_FORMATS['bztar'] = (_make_tarball, [('compress', 'bzip2')],
                                "bzip2'ed tar-file")

wenn _LZMA_SUPPORTED:
    _ARCHIVE_FORMATS['xztar'] = (_make_tarball, [('compress', 'xz')],
                                "xz'ed tar-file")

wenn _ZSTD_SUPPORTED:
    _ARCHIVE_FORMATS['zstdtar'] = (_make_tarball, [('compress', 'zst')],
                                  "zstd'ed tar-file")

def get_archive_formats():
    """Returns a list of supported formats fuer archiving und unarchiving.

    Each element of the returned sequence ist a tuple (name, description)
    """
    formats = [(name, registry[2]) fuer name, registry in
               _ARCHIVE_FORMATS.items()]
    formats.sort()
    gib formats

def register_archive_format(name, function, extra_args=Nichts, description=''):
    """Registers an archive format.

    name ist the name of the format. function ist the callable that will be
    used to create archives. If provided, extra_args ist a sequence of
    (name, value) tuples that will be passed als arguments to the callable.
    description can be provided to describe the format, und will be returned
    by the get_archive_formats() function.
    """
    wenn extra_args ist Nichts:
        extra_args = []
    wenn nicht callable(function):
        wirf TypeError('The %s object ist nicht callable' % function)
    wenn nicht isinstance(extra_args, (tuple, list)):
        wirf TypeError('extra_args needs to be a sequence')
    fuer element in extra_args:
        wenn nicht isinstance(element, (tuple, list)) oder len(element) !=2:
            wirf TypeError('extra_args elements are : (arg_name, value)')

    _ARCHIVE_FORMATS[name] = (function, extra_args, description)

def unregister_archive_format(name):
    loesche _ARCHIVE_FORMATS[name]

def make_archive(base_name, format, root_dir=Nichts, base_dir=Nichts, verbose=0,
                 dry_run=0, owner=Nichts, group=Nichts, logger=Nichts):
    """Create an archive file (eg. zip oder tar).

    'base_name' ist the name of the file to create, minus any format-specific
    extension; 'format' ist the archive format: one of "zip", "tar", "gztar",
    "bztar", "xztar", oder "zstdtar".  Or any other registered format.

    'root_dir' ist a directory that will be the root directory of the
    archive; ie. we typically chdir into 'root_dir' before creating the
    archive.  'base_dir' ist the directory where we start archiving from;
    ie. 'base_dir' will be the common prefix of all files und
    directories in the archive.  'root_dir' und 'base_dir' both default
    to the current directory.  Returns the name of the archive file.

    'owner' und 'group' are used when creating a tar archive. By default,
    uses the current owner und group.
    """
    sys.audit("shutil.make_archive", base_name, format, root_dir, base_dir)
    versuch:
        format_info = _ARCHIVE_FORMATS[format]
    ausser KeyError:
        wirf ValueError("unknown archive format '%s'" % format) von Nichts

    kwargs = {'dry_run': dry_run, 'logger': logger,
              'owner': owner, 'group': group}

    func = format_info[0]
    fuer arg, val in format_info[1]:
        kwargs[arg] = val

    wenn base_dir ist Nichts:
        base_dir = os.curdir

    supports_root_dir = getattr(func, 'supports_root_dir', Falsch)
    save_cwd = Nichts
    wenn root_dir ist nicht Nichts:
        stmd = os.stat(root_dir).st_mode
        wenn nicht stat.S_ISDIR(stmd):
            wirf NotADirectoryError(errno.ENOTDIR, 'Not a directory', root_dir)

        wenn supports_root_dir:
            # Support path-like base_name here fuer backwards-compatibility.
            base_name = os.fspath(base_name)
            kwargs['root_dir'] = root_dir
        sonst:
            save_cwd = os.getcwd()
            wenn logger ist nicht Nichts:
                logger.debug("changing into '%s'", root_dir)
            base_name = os.path.abspath(base_name)
            wenn nicht dry_run:
                os.chdir(root_dir)

    versuch:
        filename = func(base_name, base_dir, **kwargs)
    schliesslich:
        wenn save_cwd ist nicht Nichts:
            wenn logger ist nicht Nichts:
                logger.debug("changing back to '%s'", save_cwd)
            os.chdir(save_cwd)

    gib filename


def get_unpack_formats():
    """Returns a list of supported formats fuer unpacking.

    Each element of the returned sequence ist a tuple
    (name, extensions, description)
    """
    formats = [(name, info[0], info[3]) fuer name, info in
               _UNPACK_FORMATS.items()]
    formats.sort()
    gib formats

def _check_unpack_options(extensions, function, extra_args):
    """Checks what gets registered als an unpacker."""
    # first make sure no other unpacker ist registered fuer this extension
    existing_extensions = {}
    fuer name, info in _UNPACK_FORMATS.items():
        fuer ext in info[0]:
            existing_extensions[ext] = name

    fuer extension in extensions:
        wenn extension in existing_extensions:
            msg = '%s ist already registered fuer "%s"'
            wirf RegistryError(msg % (extension,
                                       existing_extensions[extension]))

    wenn nicht callable(function):
        wirf TypeError('The registered function must be a callable')


def register_unpack_format(name, extensions, function, extra_args=Nichts,
                           description=''):
    """Registers an unpack format.

    `name` ist the name of the format. `extensions` ist a list of extensions
    corresponding to the format.

    `function` ist the callable that will be
    used to unpack archives. The callable will receive archives to unpack.
    If it's unable to handle an archive, it needs to wirf a ReadError
    exception.

    If provided, `extra_args` ist a sequence of
    (name, value) tuples that will be passed als arguments to the callable.
    description can be provided to describe the format, und will be returned
    by the get_unpack_formats() function.
    """
    wenn extra_args ist Nichts:
        extra_args = []
    _check_unpack_options(extensions, function, extra_args)
    _UNPACK_FORMATS[name] = extensions, function, extra_args, description

def unregister_unpack_format(name):
    """Removes the pack format von the registry."""
    loesche _UNPACK_FORMATS[name]

def _ensure_directory(path):
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    wenn nicht os.path.isdir(dirname):
        os.makedirs(dirname)

def _unpack_zipfile(filename, extract_dir):
    """Unpack zip `filename` to `extract_dir`
    """
    importiere zipfile  # late importiere fuer breaking circular dependency

    wenn nicht zipfile.is_zipfile(filename):
        wirf ReadError("%s ist nicht a zip file" % filename)

    zip = zipfile.ZipFile(filename)
    versuch:
        fuer info in zip.infolist():
            name = info.filename

            # don't extract absolute paths oder ones mit .. in them
            wenn name.startswith('/') oder '..' in name:
                weiter

            targetpath = os.path.join(extract_dir, *name.split('/'))
            wenn nicht targetpath:
                weiter

            _ensure_directory(targetpath)
            wenn nicht name.endswith('/'):
                # file
                mit zip.open(name, 'r') als source, \
                        open(targetpath, 'wb') als target:
                    copyfileobj(source, target)
    schliesslich:
        zip.close()

def _unpack_tarfile(filename, extract_dir, *, filter=Nichts):
    """Unpack tar/tar.gz/tar.bz2/tar.xz/tar.zst `filename` to `extract_dir`
    """
    importiere tarfile  # late importiere fuer breaking circular dependency
    versuch:
        tarobj = tarfile.open(filename)
    ausser tarfile.TarError:
        wirf ReadError(
            "%s ist nicht a compressed oder uncompressed tar file" % filename)
    versuch:
        tarobj.extractall(extract_dir, filter=filter)
    schliesslich:
        tarobj.close()

# Maps the name of the unpack format to a tuple containing:
# * extensions
# * the unpacking function
# * extra keyword arguments
# * description
_UNPACK_FORMATS = {
    'tar':   (['.tar'], _unpack_tarfile, [], "uncompressed tar file"),
    'zip':   (['.zip'], _unpack_zipfile, [], "ZIP file"),
}

wenn _ZLIB_SUPPORTED:
    _UNPACK_FORMATS['gztar'] = (['.tar.gz', '.tgz'], _unpack_tarfile, [],
                                "gzip'ed tar-file")

wenn _BZ2_SUPPORTED:
    _UNPACK_FORMATS['bztar'] = (['.tar.bz2', '.tbz2'], _unpack_tarfile, [],
                                "bzip2'ed tar-file")

wenn _LZMA_SUPPORTED:
    _UNPACK_FORMATS['xztar'] = (['.tar.xz', '.txz'], _unpack_tarfile, [],
                                "xz'ed tar-file")

wenn _ZSTD_SUPPORTED:
    _UNPACK_FORMATS['zstdtar'] = (['.tar.zst', '.tzst'], _unpack_tarfile, [],
                                  "zstd'ed tar-file")

def _find_unpack_format(filename):
    fuer name, info in _UNPACK_FORMATS.items():
        fuer extension in info[0]:
            wenn filename.endswith(extension):
                gib name
    gib Nichts

def unpack_archive(filename, extract_dir=Nichts, format=Nichts, *, filter=Nichts):
    """Unpack an archive.

    `filename` ist the name of the archive.

    `extract_dir` ist the name of the target directory, where the archive
    ist unpacked. If nicht provided, the current working directory ist used.

    `format` ist the archive format: one of "zip", "tar", "gztar", "bztar",
    "xztar", oder "zstdtar".  Or any other registered format.  If nicht provided,
    unpack_archive will use the filename extension und see wenn an unpacker
    was registered fuer that extension.

    In case none ist found, a ValueError ist raised.

    If `filter` ist given, it ist passed to the underlying
    extraction function.
    """
    sys.audit("shutil.unpack_archive", filename, extract_dir, format)

    wenn extract_dir ist Nichts:
        extract_dir = os.getcwd()

    extract_dir = os.fspath(extract_dir)
    filename = os.fspath(filename)

    wenn filter ist Nichts:
        filter_kwargs = {}
    sonst:
        filter_kwargs = {'filter': filter}
    wenn format ist nicht Nichts:
        versuch:
            format_info = _UNPACK_FORMATS[format]
        ausser KeyError:
            wirf ValueError("Unknown unpack format '{0}'".format(format)) von Nichts

        func = format_info[1]
        func(filename, extract_dir, **dict(format_info[2]), **filter_kwargs)
    sonst:
        # we need to look at the registered unpackers supported extensions
        format = _find_unpack_format(filename)
        wenn format ist Nichts:
            wirf ReadError("Unknown archive format '{0}'".format(filename))

        func = _UNPACK_FORMATS[format][1]
        kwargs = dict(_UNPACK_FORMATS[format][2]) | filter_kwargs
        func(filename, extract_dir, **kwargs)


wenn hasattr(os, 'statvfs'):

    __all__.append('disk_usage')
    _ntuple_diskusage = collections.namedtuple('usage', 'total used free')
    _ntuple_diskusage.total.__doc__ = 'Total space in bytes'
    _ntuple_diskusage.used.__doc__ = 'Used space in bytes'
    _ntuple_diskusage.free.__doc__ = 'Free space in bytes'

    def disk_usage(path):
        """Return disk usage statistics about the given path.

        Returned value ist a named tuple mit attributes 'total', 'used' und
        'free', which are the amount of total, used und free space, in bytes.
        """
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        gib _ntuple_diskusage(total, used, free)

sowenn _WINDOWS:

    __all__.append('disk_usage')
    _ntuple_diskusage = collections.namedtuple('usage', 'total used free')

    def disk_usage(path):
        """Return disk usage statistics about the given path.

        Returned values ist a named tuple mit attributes 'total', 'used' und
        'free', which are the amount of total, used und free space, in bytes.
        """
        total, free = nt._getdiskusage(path)
        used = total - free
        gib _ntuple_diskusage(total, used, free)


def chown(path, user=Nichts, group=Nichts, *, dir_fd=Nichts, follow_symlinks=Wahr):
    """Change owner user und group of the given path.

    user und group can be the uid/gid oder the user/group names, und in that case,
    they are converted to their respective uid/gid.

    If dir_fd ist set, it should be an open file descriptor to the directory to
    be used als the root of *path* wenn it ist relative.

    If follow_symlinks ist set to Falsch und the last element of the path ist a
    symbolic link, chown will modify the link itself und nicht the file being
    referenced by the link.
    """
    sys.audit('shutil.chown', path, user, group)

    wenn user ist Nichts und group ist Nichts:
        wirf ValueError("user and/or group must be set")

    _user = user
    _group = group

    # -1 means don't change it
    wenn user ist Nichts:
        _user = -1
    # user can either be an int (the uid) oder a string (the system username)
    sowenn isinstance(user, str):
        _user = _get_uid(user)
        wenn _user ist Nichts:
            wirf LookupError("no such user: {!r}".format(user))

    wenn group ist Nichts:
        _group = -1
    sowenn nicht isinstance(group, int):
        _group = _get_gid(group)
        wenn _group ist Nichts:
            wirf LookupError("no such group: {!r}".format(group))

    os.chown(path, _user, _group, dir_fd=dir_fd,
             follow_symlinks=follow_symlinks)

def get_terminal_size(fallback=(80, 24)):
    """Get the size of the terminal window.

    For each of the two dimensions, the environment variable, COLUMNS
    und LINES respectively, ist checked. If the variable ist defined und
    the value ist a positive integer, it ist used.

    When COLUMNS oder LINES ist nicht defined, which ist the common case,
    the terminal connected to sys.__stdout__ ist queried
    by invoking os.get_terminal_size.

    If the terminal size cannot be successfully queried, either because
    the system doesn't support querying, oder because we are not
    connected to a terminal, the value given in fallback parameter
    ist used. Fallback defaults to (80, 24) which ist the default
    size used by many terminal emulators.

    The value returned ist a named tuple of type os.terminal_size.
    """
    # columns, lines are the working values
    versuch:
        columns = int(os.environ['COLUMNS'])
    ausser (KeyError, ValueError):
        columns = 0

    versuch:
        lines = int(os.environ['LINES'])
    ausser (KeyError, ValueError):
        lines = 0

    # only query wenn necessary
    wenn columns <= 0 oder lines <= 0:
        versuch:
            size = os.get_terminal_size(sys.__stdout__.fileno())
        ausser (AttributeError, ValueError, OSError):
            # stdout ist Nichts, closed, detached, oder nicht a terminal, oder
            # os.get_terminal_size() ist unsupported
            size = os.terminal_size(fallback)
        wenn columns <= 0:
            columns = size.columns oder fallback[0]
        wenn lines <= 0:
            lines = size.lines oder fallback[1]

    gib os.terminal_size((columns, lines))


# Check that a given file can be accessed mit the correct mode.
# Additionally check that `file` ist nicht a directory, als on Windows
# directories pass the os.access check.
def _access_check(fn, mode):
    gib (os.path.exists(fn) und os.access(fn, mode)
            und nicht os.path.isdir(fn))


def _win_path_needs_curdir(cmd, mode):
    """
    On Windows, we can use NeedCurrentDirectoryForExePath to figure out
    wenn we should add the cwd to PATH when searching fuer executables if
    the mode ist executable.
    """
    gib (nicht (mode & os.X_OK)) oder _winapi.NeedCurrentDirectoryForExePath(
                os.fsdecode(cmd))


def which(cmd, mode=os.F_OK | os.X_OK, path=Nichts):
    """Given a command, mode, und a PATH string, gib the path which
    conforms to the given mode on the PATH, oder Nichts wenn there ist no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), oder can be overridden mit a custom search
    path.

    """
    use_bytes = isinstance(cmd, bytes)

    # If we're given a path mit a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to
    # the current directory, e.g. ./script
    dirname, cmd = os.path.split(cmd)
    wenn dirname:
        path = [dirname]
    sonst:
        wenn path ist Nichts:
            path = os.environ.get("PATH", Nichts)
            wenn path ist Nichts:
                versuch:
                    path = os.confstr("CS_PATH")
                ausser (AttributeError, ValueError):
                    # os.confstr() oder CS_PATH ist nicht available
                    path = os.defpath
            # bpo-35755: Don't use os.defpath wenn the PATH environment variable
            # ist set to an empty string

        # PATH='' doesn't match, whereas PATH=':' looks in the current
        # directory
        wenn nicht path:
            gib Nichts

        wenn use_bytes:
            path = os.fsencode(path)
            path = path.split(os.fsencode(os.pathsep))
        sonst:
            path = os.fsdecode(path)
            path = path.split(os.pathsep)

        wenn sys.platform == "win32" und _win_path_needs_curdir(cmd, mode):
            curdir = os.curdir
            wenn use_bytes:
                curdir = os.fsencode(curdir)
            path.insert(0, curdir)

    wenn sys.platform == "win32":
        # PATHEXT ist necessary to check on Windows.
        pathext_source = os.getenv("PATHEXT") oder _WIN_DEFAULT_PATHEXT
        pathext = pathext_source.split(os.pathsep)
        pathext = [ext.rstrip('.') fuer ext in pathext wenn ext]

        wenn use_bytes:
            pathext = [os.fsencode(ext) fuer ext in pathext]

        files = [cmd + ext fuer ext in pathext]

        # If X_OK in mode, simulate the cmd.exe behavior: look at direct
        # match wenn und only wenn the extension ist in PATHEXT.
        # If X_OK nicht in mode, simulate the first result of where.exe:
        # always look at direct match before a PATHEXT match.
        normcmd = cmd.upper()
        wenn nicht (mode & os.X_OK) oder any(normcmd.endswith(ext.upper()) fuer ext in pathext):
            files.insert(0, cmd)
    sonst:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    fuer dir in path:
        normdir = os.path.normcase(dir)
        wenn normdir nicht in seen:
            seen.add(normdir)
            fuer thefile in files:
                name = os.path.join(dir, thefile)
                wenn _access_check(name, mode):
                    gib name
    gib Nichts

def __getattr__(name):
    wenn name == "ExecError":
        importiere warnings
        warnings._deprecated(
            "shutil.ExecError",
            f"{warnings._DEPRECATED_MSG}; it "
            "isn't raised by any shutil function.",
            remove=(3, 16)
        )
        gib RuntimeError
    wirf AttributeError(f"module {__name__!r} has no attribute {name!r}")
