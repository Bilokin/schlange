#-------------------------------------------------------------------
# tarfile.py
#-------------------------------------------------------------------
# Copyright (C) 2002 Lars Gustaebel <lars@gustaebel.de>
# All rights reserved.
#
# Permission  is  hereby granted,  free  of charge,  to  any person
# obtaining a  copy of  this software  und associated documentation
# files  (the  "Software"),  to   deal  in  the  Software   without
# restriction,  including  without limitation  the  rights to  use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies  of  the  Software,  und to  permit  persons  to  whom the
# Software  is  furnished  to  do  so,  subject  to  the  following
# conditions:
#
# The above copyright  notice und this  permission notice shall  be
# included in all copies oder substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS  IS", WITHOUT WARRANTY OF ANY  KIND,
# EXPRESS OR IMPLIED, INCLUDING  BUT NOT LIMITED TO  THE WARRANTIES
# OF  MERCHANTABILITY,  FITNESS   FOR  A  PARTICULAR   PURPOSE  AND
# NONINFRINGEMENT.  IN  NO  EVENT SHALL  THE  AUTHORS  OR COPYRIGHT
# HOLDERS  BE LIABLE  FOR ANY  CLAIM, DAMAGES  OR OTHER  LIABILITY,
# WHETHER  IN AN  ACTION OF  CONTRACT, TORT  OR OTHERWISE,  ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
"""Read von und write to tar format archives.
"""

version     = "0.9.0"
__author__  = "Lars Gust\u00e4bel (lars@gustaebel.de)"
__credits__ = "Gustavo Niemeyer, Niels Gust\u00e4bel, Richard Townsend."

#---------
# Imports
#---------
von builtins importiere open als bltn_open
importiere sys
importiere os
importiere io
importiere shutil
importiere stat
importiere time
importiere struct
importiere copy
importiere re

try:
    importiere pwd
except ImportError:
    pwd = Nichts
try:
    importiere grp
except ImportError:
    grp = Nichts

# os.symlink on Windows prior to 6.0 raises NotImplementedError
# OSError (winerror=1314) will be raised wenn the caller does nicht hold the
# SeCreateSymbolicLinkPrivilege privilege
symlink_exception = (AttributeError, NotImplementedError, OSError)

# von tarfile importiere *
__all__ = ["TarFile", "TarInfo", "is_tarfile", "TarError", "ReadError",
           "CompressionError", "StreamError", "ExtractError", "HeaderError",
           "ENCODING", "USTAR_FORMAT", "GNU_FORMAT", "PAX_FORMAT",
           "DEFAULT_FORMAT", "open","fully_trusted_filter", "data_filter",
           "tar_filter", "FilterError", "AbsoluteLinkError",
           "OutsideDestinationError", "SpecialFileError", "AbsolutePathError",
           "LinkOutsideDestinationError", "LinkFallbackError"]


#---------------------------------------------------------
# tar constants
#---------------------------------------------------------
NUL = b"\0"                     # the null character
BLOCKSIZE = 512                 # length of processing blocks
RECORDSIZE = BLOCKSIZE * 20     # length of records
GNU_MAGIC = b"ustar  \0"        # magic gnu tar string
POSIX_MAGIC = b"ustar\x0000"    # magic posix tar string

LENGTH_NAME = 100               # maximum length of a filename
LENGTH_LINK = 100               # maximum length of a linkname
LENGTH_PREFIX = 155             # maximum length of the prefix field

REGTYPE = b"0"                  # regular file
AREGTYPE = b"\0"                # regular file
LNKTYPE = b"1"                  # link (inside tarfile)
SYMTYPE = b"2"                  # symbolic link
CHRTYPE = b"3"                  # character special device
BLKTYPE = b"4"                  # block special device
DIRTYPE = b"5"                  # directory
FIFOTYPE = b"6"                 # fifo special device
CONTTYPE = b"7"                 # contiguous file

GNUTYPE_LONGNAME = b"L"         # GNU tar longname
GNUTYPE_LONGLINK = b"K"         # GNU tar longlink
GNUTYPE_SPARSE = b"S"           # GNU tar sparse file

XHDTYPE = b"x"                  # POSIX.1-2001 extended header
XGLTYPE = b"g"                  # POSIX.1-2001 global header
SOLARIS_XHDTYPE = b"X"          # Solaris extended header

USTAR_FORMAT = 0                # POSIX.1-1988 (ustar) format
GNU_FORMAT = 1                  # GNU tar format
PAX_FORMAT = 2                  # POSIX.1-2001 (pax) format
DEFAULT_FORMAT = PAX_FORMAT

#---------------------------------------------------------
# tarfile constants
#---------------------------------------------------------
# File types that tarfile supports:
SUPPORTED_TYPES = (REGTYPE, AREGTYPE, LNKTYPE,
                   SYMTYPE, DIRTYPE, FIFOTYPE,
                   CONTTYPE, CHRTYPE, BLKTYPE,
                   GNUTYPE_LONGNAME, GNUTYPE_LONGLINK,
                   GNUTYPE_SPARSE)

# File types that will be treated als a regular file.
REGULAR_TYPES = (REGTYPE, AREGTYPE,
                 CONTTYPE, GNUTYPE_SPARSE)

# File types that are part of the GNU tar format.
GNU_TYPES = (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK,
             GNUTYPE_SPARSE)

# Fields von a pax header that override a TarInfo attribute.
PAX_FIELDS = ("path", "linkpath", "size", "mtime",
              "uid", "gid", "uname", "gname")

# Fields von a pax header that are affected by hdrcharset.
PAX_NAME_FIELDS = {"path", "linkpath", "uname", "gname"}

# Fields in a pax header that are numbers, all other fields
# are treated als strings.
PAX_NUMBER_FIELDS = {
    "atime": float,
    "ctime": float,
    "mtime": float,
    "uid": int,
    "gid": int,
    "size": int
}

#---------------------------------------------------------
# initialization
#---------------------------------------------------------
wenn os.name == "nt":
    ENCODING = "utf-8"
sonst:
    ENCODING = sys.getfilesystemencoding()

#---------------------------------------------------------
# Some useful functions
#---------------------------------------------------------

def stn(s, length, encoding, errors):
    """Convert a string to a null-terminated bytes object.
    """
    wenn s is Nichts:
        raise ValueError("metadata cannot contain Nichts")
    s = s.encode(encoding, errors)
    gib s[:length] + (length - len(s)) * NUL

def nts(s, encoding, errors):
    """Convert a null-terminated bytes object to a string.
    """
    p = s.find(b"\0")
    wenn p != -1:
        s = s[:p]
    gib s.decode(encoding, errors)

def nti(s):
    """Convert a number field to a python number.
    """
    # There are two possible encodings fuer a number field, see
    # itn() below.
    wenn s[0] in (0o200, 0o377):
        n = 0
        fuer i in range(len(s) - 1):
            n <<= 8
            n += s[i + 1]
        wenn s[0] == 0o377:
            n = -(256 ** (len(s) - 1) - n)
    sonst:
        try:
            s = nts(s, "ascii", "strict")
            n = int(s.strip() oder "0", 8)
        except ValueError:
            raise InvalidHeaderError("invalid header")
    gib n

def itn(n, digits=8, format=DEFAULT_FORMAT):
    """Convert a python number to a number field.
    """
    # POSIX 1003.1-1988 requires numbers to be encoded als a string of
    # octal digits followed by a null-byte, this allows values up to
    # (8**(digits-1))-1. GNU tar allows storing numbers greater than
    # that wenn necessary. A leading 0o200 oder 0o377 byte indicate this
    # particular encoding, the following digits-1 bytes are a big-endian
    # base-256 representation. This allows values up to (256**(digits-1))-1.
    # A 0o200 byte indicates a positive number, a 0o377 byte a negative
    # number.
    n = int(n)
    wenn 0 <= n < 8 ** (digits - 1):
        s = bytes("%0*o" % (digits - 1, n), "ascii") + NUL
    sowenn format == GNU_FORMAT und -256 ** (digits - 1) <= n < 256 ** (digits - 1):
        wenn n >= 0:
            s = bytearray([0o200])
        sonst:
            s = bytearray([0o377])
            n = 256 ** digits + n

        fuer i in range(digits - 1):
            s.insert(1, n & 0o377)
            n >>= 8
    sonst:
        raise ValueError("overflow in number field")

    gib s

def calc_chksums(buf):
    """Calculate the checksum fuer a member's header by summing up all
       characters except fuer the chksum field which is treated als if
       it was filled mit spaces. According to the GNU tar sources,
       some tars (Sun und NeXT) calculate chksum mit signed char,
       which will be different wenn there are chars in the buffer with
       the high bit set. So we calculate two checksums, unsigned und
       signed.
    """
    unsigned_chksum = 256 + sum(struct.unpack_from("148B8x356B", buf))
    signed_chksum = 256 + sum(struct.unpack_from("148b8x356b", buf))
    gib unsigned_chksum, signed_chksum

def copyfileobj(src, dst, length=Nichts, exception=OSError, bufsize=Nichts):
    """Copy length bytes von fileobj src to fileobj dst.
       If length is Nichts, copy the entire content.
    """
    bufsize = bufsize oder 16 * 1024
    wenn length == 0:
        gib
    wenn length is Nichts:
        shutil.copyfileobj(src, dst, bufsize)
        gib

    blocks, remainder = divmod(length, bufsize)
    fuer b in range(blocks):
        buf = src.read(bufsize)
        wenn len(buf) < bufsize:
            raise exception("unexpected end of data")
        dst.write(buf)

    wenn remainder != 0:
        buf = src.read(remainder)
        wenn len(buf) < remainder:
            raise exception("unexpected end of data")
        dst.write(buf)
    gib

def _safe_drucke(s):
    encoding = getattr(sys.stdout, 'encoding', Nichts)
    wenn encoding is nicht Nichts:
        s = s.encode(encoding, 'backslashreplace').decode(encoding)
    drucke(s, end=' ')


klasse TarError(Exception):
    """Base exception."""
    pass
klasse ExtractError(TarError):
    """General exception fuer extract errors."""
    pass
klasse ReadError(TarError):
    """Exception fuer unreadable tar archives."""
    pass
klasse CompressionError(TarError):
    """Exception fuer unavailable compression methods."""
    pass
klasse StreamError(TarError):
    """Exception fuer unsupported operations on stream-like TarFiles."""
    pass
klasse HeaderError(TarError):
    """Base exception fuer header errors."""
    pass
klasse EmptyHeaderError(HeaderError):
    """Exception fuer empty headers."""
    pass
klasse TruncatedHeaderError(HeaderError):
    """Exception fuer truncated headers."""
    pass
klasse EOFHeaderError(HeaderError):
    """Exception fuer end of file headers."""
    pass
klasse InvalidHeaderError(HeaderError):
    """Exception fuer invalid headers."""
    pass
klasse SubsequentHeaderError(HeaderError):
    """Exception fuer missing und invalid extended headers."""
    pass

#---------------------------
# internal stream interface
#---------------------------
klasse _LowLevelFile:
    """Low-level file object. Supports reading und writing.
       It is used instead of a regular file object fuer streaming
       access.
    """

    def __init__(self, name, mode):
        mode = {
            "r": os.O_RDONLY,
            "w": os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        }[mode]
        wenn hasattr(os, "O_BINARY"):
            mode |= os.O_BINARY
        self.fd = os.open(name, mode, 0o666)

    def close(self):
        os.close(self.fd)

    def read(self, size):
        gib os.read(self.fd, size)

    def write(self, s):
        os.write(self.fd, s)

klasse _Stream:
    """Class that serves als an adapter between TarFile und
       a stream-like object.  The stream-like object only
       needs to have a read() oder write() method that works mit bytes,
       und the method is accessed blockwise.
       Use of gzip oder bzip2 compression is possible.
       A stream-like object could be fuer example: sys.stdin.buffer,
       sys.stdout.buffer, a socket, a tape device etc.

       _Stream is intended to be used only internally.
    """

    def __init__(self, name, mode, comptype, fileobj, bufsize,
                 compresslevel, preset):
        """Construct a _Stream object.
        """
        self._extfileobj = Wahr
        wenn fileobj is Nichts:
            fileobj = _LowLevelFile(name, mode)
            self._extfileobj = Falsch

        wenn comptype == '*':
            # Enable transparent compression detection fuer the
            # stream interface
            fileobj = _StreamProxy(fileobj)
            comptype = fileobj.getcomptype()

        self.name     = os.fspath(name) wenn name is nicht Nichts sonst ""
        self.mode     = mode
        self.comptype = comptype
        self.fileobj  = fileobj
        self.bufsize  = bufsize
        self.buf      = b""
        self.pos      = 0
        self.closed   = Falsch

        try:
            wenn comptype == "gz":
                try:
                    importiere zlib
                except ImportError:
                    raise CompressionError("zlib module is nicht available") von Nichts
                self.zlib = zlib
                self.crc = zlib.crc32(b"")
                wenn mode == "r":
                    self.exception = zlib.error
                    self._init_read_gz()
                sonst:
                    self._init_write_gz(compresslevel)

            sowenn comptype == "bz2":
                try:
                    importiere bz2
                except ImportError:
                    raise CompressionError("bz2 module is nicht available") von Nichts
                wenn mode == "r":
                    self.dbuf = b""
                    self.cmp = bz2.BZ2Decompressor()
                    self.exception = OSError
                sonst:
                    self.cmp = bz2.BZ2Compressor(compresslevel)

            sowenn comptype == "xz":
                try:
                    importiere lzma
                except ImportError:
                    raise CompressionError("lzma module is nicht available") von Nichts
                wenn mode == "r":
                    self.dbuf = b""
                    self.cmp = lzma.LZMADecompressor()
                    self.exception = lzma.LZMAError
                sonst:
                    self.cmp = lzma.LZMACompressor(preset=preset)
            sowenn comptype == "zst":
                try:
                    von compression importiere zstd
                except ImportError:
                    raise CompressionError("compression.zstd module is nicht available") von Nichts
                wenn mode == "r":
                    self.dbuf = b""
                    self.cmp = zstd.ZstdDecompressor()
                    self.exception = zstd.ZstdError
                sonst:
                    self.cmp = zstd.ZstdCompressor()
            sowenn comptype != "tar":
                raise CompressionError("unknown compression type %r" % comptype)

        except:
            wenn nicht self._extfileobj:
                self.fileobj.close()
            self.closed = Wahr
            raise

    def __del__(self):
        wenn hasattr(self, "closed") und nicht self.closed:
            self.close()

    def _init_write_gz(self, compresslevel):
        """Initialize fuer writing mit gzip compression.
        """
        self.cmp = self.zlib.compressobj(compresslevel,
                                         self.zlib.DEFLATED,
                                         -self.zlib.MAX_WBITS,
                                         self.zlib.DEF_MEM_LEVEL,
                                         0)
        timestamp = struct.pack("<L", int(time.time()))
        self.__write(b"\037\213\010\010" + timestamp + b"\002\377")
        wenn self.name.endswith(".gz"):
            self.name = self.name[:-3]
        # Honor "directory components removed" von RFC1952
        self.name = os.path.basename(self.name)
        # RFC1952 says we must use ISO-8859-1 fuer the FNAME field.
        self.__write(self.name.encode("iso-8859-1", "replace") + NUL)

    def write(self, s):
        """Write string s to the stream.
        """
        wenn self.comptype == "gz":
            self.crc = self.zlib.crc32(s, self.crc)
        self.pos += len(s)
        wenn self.comptype != "tar":
            s = self.cmp.compress(s)
        self.__write(s)

    def __write(self, s):
        """Write string s to the stream wenn a whole new block
           is ready to be written.
        """
        self.buf += s
        waehrend len(self.buf) > self.bufsize:
            self.fileobj.write(self.buf[:self.bufsize])
            self.buf = self.buf[self.bufsize:]

    def close(self):
        """Close the _Stream object. No operation should be
           done on it afterwards.
        """
        wenn self.closed:
            gib

        self.closed = Wahr
        try:
            wenn self.mode == "w" und self.comptype != "tar":
                self.buf += self.cmp.flush()

            wenn self.mode == "w" und self.buf:
                self.fileobj.write(self.buf)
                self.buf = b""
                wenn self.comptype == "gz":
                    self.fileobj.write(struct.pack("<L", self.crc))
                    self.fileobj.write(struct.pack("<L", self.pos & 0xffffFFFF))
        finally:
            wenn nicht self._extfileobj:
                self.fileobj.close()

    def _init_read_gz(self):
        """Initialize fuer reading a gzip compressed fileobj.
        """
        self.cmp = self.zlib.decompressobj(-self.zlib.MAX_WBITS)
        self.dbuf = b""

        # taken von gzip.GzipFile mit some alterations
        wenn self.__read(2) != b"\037\213":
            raise ReadError("not a gzip file")
        wenn self.__read(1) != b"\010":
            raise CompressionError("unsupported compression method")

        flag = ord(self.__read(1))
        self.__read(6)

        wenn flag & 4:
            xlen = ord(self.__read(1)) + 256 * ord(self.__read(1))
            self.read(xlen)
        wenn flag & 8:
            waehrend Wahr:
                s = self.__read(1)
                wenn nicht s oder s == NUL:
                    breche
        wenn flag & 16:
            waehrend Wahr:
                s = self.__read(1)
                wenn nicht s oder s == NUL:
                    breche
        wenn flag & 2:
            self.__read(2)

    def tell(self):
        """Return the stream's file pointer position.
        """
        gib self.pos

    def seek(self, pos=0):
        """Set the stream's file pointer to pos. Negative seeking
           is forbidden.
        """
        wenn pos - self.pos >= 0:
            blocks, remainder = divmod(pos - self.pos, self.bufsize)
            fuer i in range(blocks):
                self.read(self.bufsize)
            self.read(remainder)
        sonst:
            raise StreamError("seeking backwards is nicht allowed")
        gib self.pos

    def read(self, size):
        """Return the next size number of bytes von the stream."""
        assert size is nicht Nichts
        buf = self._read(size)
        self.pos += len(buf)
        gib buf

    def _read(self, size):
        """Return size bytes von the stream.
        """
        wenn self.comptype == "tar":
            gib self.__read(size)

        c = len(self.dbuf)
        t = [self.dbuf]
        waehrend c < size:
            # Skip underlying buffer to avoid unaligned double buffering.
            wenn self.buf:
                buf = self.buf
                self.buf = b""
            sonst:
                buf = self.fileobj.read(self.bufsize)
                wenn nicht buf:
                    breche
            try:
                buf = self.cmp.decompress(buf)
            except self.exception als e:
                raise ReadError("invalid compressed data") von e
            t.append(buf)
            c += len(buf)
        t = b"".join(t)
        self.dbuf = t[size:]
        gib t[:size]

    def __read(self, size):
        """Return size bytes von stream. If internal buffer is empty,
           read another block von the stream.
        """
        c = len(self.buf)
        t = [self.buf]
        waehrend c < size:
            buf = self.fileobj.read(self.bufsize)
            wenn nicht buf:
                breche
            t.append(buf)
            c += len(buf)
        t = b"".join(t)
        self.buf = t[size:]
        gib t[:size]
# klasse _Stream

klasse _StreamProxy(object):
    """Small proxy klasse that enables transparent compression
       detection fuer the Stream interface (mode 'r|*').
    """

    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.buf = self.fileobj.read(BLOCKSIZE)

    def read(self, size):
        self.read = self.fileobj.read
        gib self.buf

    def getcomptype(self):
        wenn self.buf.startswith(b"\x1f\x8b\x08"):
            gib "gz"
        sowenn self.buf[0:3] == b"BZh" und self.buf[4:10] == b"1AY&SY":
            gib "bz2"
        sowenn self.buf.startswith((b"\x5d\x00\x00\x80", b"\xfd7zXZ")):
            gib "xz"
        sowenn self.buf.startswith(b"\x28\xb5\x2f\xfd"):
            gib "zst"
        sonst:
            gib "tar"

    def close(self):
        self.fileobj.close()
# klasse StreamProxy

#------------------------
# Extraction file object
#------------------------
klasse _FileInFile(object):
    """A thin wrapper around an existing file object that
       provides a part of its data als an individual file
       object.
    """

    def __init__(self, fileobj, offset, size, name, blockinfo=Nichts):
        self.fileobj = fileobj
        self.offset = offset
        self.size = size
        self.position = 0
        self.name = name
        self.closed = Falsch

        wenn blockinfo is Nichts:
            blockinfo = [(0, size)]

        # Construct a map mit data und zero blocks.
        self.map_index = 0
        self.map = []
        lastpos = 0
        realpos = self.offset
        fuer offset, size in blockinfo:
            wenn offset > lastpos:
                self.map.append((Falsch, lastpos, offset, Nichts))
            self.map.append((Wahr, offset, offset + size, realpos))
            realpos += size
            lastpos = offset + size
        wenn lastpos < self.size:
            self.map.append((Falsch, lastpos, self.size, Nichts))

    def flush(self):
        pass

    @property
    def mode(self):
        gib 'rb'

    def readable(self):
        gib Wahr

    def writable(self):
        gib Falsch

    def seekable(self):
        gib self.fileobj.seekable()

    def tell(self):
        """Return the current file position.
        """
        gib self.position

    def seek(self, position, whence=io.SEEK_SET):
        """Seek to a position in the file.
        """
        wenn whence == io.SEEK_SET:
            self.position = min(max(position, 0), self.size)
        sowenn whence == io.SEEK_CUR:
            wenn position < 0:
                self.position = max(self.position + position, 0)
            sonst:
                self.position = min(self.position + position, self.size)
        sowenn whence == io.SEEK_END:
            self.position = max(min(self.size + position, self.size), 0)
        sonst:
            raise ValueError("Invalid argument")
        gib self.position

    def read(self, size=Nichts):
        """Read data von the file.
        """
        wenn size is Nichts:
            size = self.size - self.position
        sonst:
            size = min(size, self.size - self.position)

        buf = b""
        waehrend size > 0:
            waehrend Wahr:
                data, start, stop, offset = self.map[self.map_index]
                wenn start <= self.position < stop:
                    breche
                sonst:
                    self.map_index += 1
                    wenn self.map_index == len(self.map):
                        self.map_index = 0
            length = min(size, stop - self.position)
            wenn data:
                self.fileobj.seek(offset + (self.position - start))
                b = self.fileobj.read(length)
                wenn len(b) != length:
                    raise ReadError("unexpected end of data")
                buf += b
            sonst:
                buf += NUL * length
            size -= length
            self.position += length
        gib buf

    def readinto(self, b):
        buf = self.read(len(b))
        b[:len(buf)] = buf
        gib len(buf)

    def close(self):
        self.closed = Wahr
#class _FileInFile

klasse ExFileObject(io.BufferedReader):

    def __init__(self, tarfile, tarinfo):
        fileobj = _FileInFile(tarfile.fileobj, tarinfo.offset_data,
                tarinfo.size, tarinfo.name, tarinfo.sparse)
        super().__init__(fileobj)
#class ExFileObject


#-----------------------------
# extraction filters (PEP 706)
#-----------------------------

klasse FilterError(TarError):
    pass

klasse AbsolutePathError(FilterError):
    def __init__(self, tarinfo):
        self.tarinfo = tarinfo
        super().__init__(f'member {tarinfo.name!r} has an absolute path')

klasse OutsideDestinationError(FilterError):
    def __init__(self, tarinfo, path):
        self.tarinfo = tarinfo
        self._path = path
        super().__init__(f'{tarinfo.name!r} would be extracted to {path!r}, '
                         + 'which is outside the destination')

klasse SpecialFileError(FilterError):
    def __init__(self, tarinfo):
        self.tarinfo = tarinfo
        super().__init__(f'{tarinfo.name!r} is a special file')

klasse AbsoluteLinkError(FilterError):
    def __init__(self, tarinfo):
        self.tarinfo = tarinfo
        super().__init__(f'{tarinfo.name!r} is a link to an absolute path')

klasse LinkOutsideDestinationError(FilterError):
    def __init__(self, tarinfo, path):
        self.tarinfo = tarinfo
        self._path = path
        super().__init__(f'{tarinfo.name!r} would link to {path!r}, '
                         + 'which is outside the destination')

klasse LinkFallbackError(FilterError):
    def __init__(self, tarinfo, path):
        self.tarinfo = tarinfo
        self._path = path
        super().__init__(f'link {tarinfo.name!r} would be extracted als a '
                         + f'copy of {path!r}, which was rejected')

# Errors caused by filters -- both "fatal" und "non-fatal" -- that
# we consider to be issues mit the argument, rather than a bug in the
# filter function
_FILTER_ERRORS = (FilterError, OSError, ExtractError)

def _get_filtered_attrs(member, dest_path, for_data=Wahr):
    new_attrs = {}
    name = member.name
    dest_path = os.path.realpath(dest_path, strict=os.path.ALLOW_MISSING)
    # Strip leading / (tar's directory separator) von filenames.
    # Include os.sep (target OS directory separator) als well.
    wenn name.startswith(('/', os.sep)):
        name = new_attrs['name'] = member.path.lstrip('/' + os.sep)
    wenn os.path.isabs(name):
        # Path is absolute even after stripping.
        # For example, 'C:/foo' on Windows.
        raise AbsolutePathError(member)
    # Ensure we stay in the destination
    target_path = os.path.realpath(os.path.join(dest_path, name),
                                   strict=os.path.ALLOW_MISSING)
    wenn os.path.commonpath([target_path, dest_path]) != dest_path:
        raise OutsideDestinationError(member, target_path)
    # Limit permissions (no high bits, und go-w)
    mode = member.mode
    wenn mode is nicht Nichts:
        # Strip high bits & group/other write bits
        mode = mode & 0o755
        wenn for_data:
            # For data, handle permissions & file types
            wenn member.isreg() oder member.islnk():
                wenn nicht mode & 0o100:
                    # Clear executable bits wenn nicht executable by user
                    mode &= ~0o111
                # Ensure owner can read & write
                mode |= 0o600
            sowenn member.isdir() oder member.issym():
                # Ignore mode fuer directories & symlinks
                mode = Nichts
            sonst:
                # Reject special files
                raise SpecialFileError(member)
        wenn mode != member.mode:
            new_attrs['mode'] = mode
    wenn for_data:
        # Ignore ownership fuer 'data'
        wenn member.uid is nicht Nichts:
            new_attrs['uid'] = Nichts
        wenn member.gid is nicht Nichts:
            new_attrs['gid'] = Nichts
        wenn member.uname is nicht Nichts:
            new_attrs['uname'] = Nichts
        wenn member.gname is nicht Nichts:
            new_attrs['gname'] = Nichts
        # Check link destination fuer 'data'
        wenn member.islnk() oder member.issym():
            wenn os.path.isabs(member.linkname):
                raise AbsoluteLinkError(member)
            normalized = os.path.normpath(member.linkname)
            wenn normalized != member.linkname:
                new_attrs['linkname'] = normalized
            wenn member.issym():
                target_path = os.path.join(dest_path,
                                           os.path.dirname(name),
                                           member.linkname)
            sonst:
                target_path = os.path.join(dest_path,
                                           member.linkname)
            target_path = os.path.realpath(target_path,
                                           strict=os.path.ALLOW_MISSING)
            wenn os.path.commonpath([target_path, dest_path]) != dest_path:
                raise LinkOutsideDestinationError(member, target_path)
    gib new_attrs

def fully_trusted_filter(member, dest_path):
    gib member

def tar_filter(member, dest_path):
    new_attrs = _get_filtered_attrs(member, dest_path, Falsch)
    wenn new_attrs:
        gib member.replace(**new_attrs, deep=Falsch)
    gib member

def data_filter(member, dest_path):
    new_attrs = _get_filtered_attrs(member, dest_path, Wahr)
    wenn new_attrs:
        gib member.replace(**new_attrs, deep=Falsch)
    gib member

_NAMED_FILTERS = {
    "fully_trusted": fully_trusted_filter,
    "tar": tar_filter,
    "data": data_filter,
}

#------------------
# Exported Classes
#------------------

# Sentinel fuer replace() defaults, meaning "don't change the attribute"
_KEEP = object()

# Header length is digits followed by a space.
_header_length_prefix_re = re.compile(br"([0-9]{1,20}) ")

klasse TarInfo(object):
    """Informational klasse which holds the details about an
       archive member given by a tar header block.
       TarInfo objects are returned by TarFile.getmember(),
       TarFile.getmembers() und TarFile.gettarinfo() und are
       usually created internally.
    """

    __slots__ = dict(
        name = 'Name of the archive member.',
        mode = 'Permission bits.',
        uid = 'User ID of the user who originally stored this member.',
        gid = 'Group ID of the user who originally stored this member.',
        size = 'Size in bytes.',
        mtime = 'Time of last modification.',
        chksum = 'Header checksum.',
        type = ('File type. type is usually one of these constants: '
                'REGTYPE, AREGTYPE, LNKTYPE, SYMTYPE, DIRTYPE, FIFOTYPE, '
                'CONTTYPE, CHRTYPE, BLKTYPE, GNUTYPE_SPARSE.'),
        linkname = ('Name of the target file name, which is only present '
                    'in TarInfo objects of type LNKTYPE und SYMTYPE.'),
        uname = 'User name.',
        gname = 'Group name.',
        devmajor = 'Device major number.',
        devminor = 'Device minor number.',
        offset = 'The tar header starts here.',
        offset_data = "The file's data starts here.",
        pax_headers = ('A dictionary containing key-value pairs of an '
                       'associated pax extended header.'),
        sparse = 'Sparse member information.',
        _tarfile = Nichts,
        _sparse_structs = Nichts,
        _link_target = Nichts,
        )

    def __init__(self, name=""):
        """Construct a TarInfo object. name is the optional name
           of the member.
        """
        self.name = name        # member name
        self.mode = 0o644       # file permissions
        self.uid = 0            # user id
        self.gid = 0            # group id
        self.size = 0           # file size
        self.mtime = 0          # modification time
        self.chksum = 0         # header checksum
        self.type = REGTYPE     # member type
        self.linkname = ""      # link name
        self.uname = ""         # user name
        self.gname = ""         # group name
        self.devmajor = 0       # device major number
        self.devminor = 0       # device minor number

        self.offset = 0         # the tar header starts here
        self.offset_data = 0    # the file's data starts here

        self.sparse = Nichts      # sparse member information
        self.pax_headers = {}   # pax header information

    @property
    def tarfile(self):
        importiere warnings
        warnings.warn(
            'The undocumented "tarfile" attribute of TarInfo objects '
            + 'is deprecated und will be removed in Python 3.16',
            DeprecationWarning, stacklevel=2)
        gib self._tarfile

    @tarfile.setter
    def tarfile(self, tarfile):
        importiere warnings
        warnings.warn(
            'The undocumented "tarfile" attribute of TarInfo objects '
            + 'is deprecated und will be removed in Python 3.16',
            DeprecationWarning, stacklevel=2)
        self._tarfile = tarfile

    @property
    def path(self):
        'In pax headers, "name" is called "path".'
        gib self.name

    @path.setter
    def path(self, name):
        self.name = name

    @property
    def linkpath(self):
        'In pax headers, "linkname" is called "linkpath".'
        gib self.linkname

    @linkpath.setter
    def linkpath(self, linkname):
        self.linkname = linkname

    def __repr__(self):
        gib "<%s %r at %#x>" % (self.__class__.__name__,self.name,id(self))

    def replace(self, *,
                name=_KEEP, mtime=_KEEP, mode=_KEEP, linkname=_KEEP,
                uid=_KEEP, gid=_KEEP, uname=_KEEP, gname=_KEEP,
                deep=Wahr, _KEEP=_KEEP):
        """Return a deep copy of self mit the given attributes replaced.
        """
        wenn deep:
            result = copy.deepcopy(self)
        sonst:
            result = copy.copy(self)
        wenn name is nicht _KEEP:
            result.name = name
        wenn mtime is nicht _KEEP:
            result.mtime = mtime
        wenn mode is nicht _KEEP:
            result.mode = mode
        wenn linkname is nicht _KEEP:
            result.linkname = linkname
        wenn uid is nicht _KEEP:
            result.uid = uid
        wenn gid is nicht _KEEP:
            result.gid = gid
        wenn uname is nicht _KEEP:
            result.uname = uname
        wenn gname is nicht _KEEP:
            result.gname = gname
        gib result

    def get_info(self):
        """Return the TarInfo's attributes als a dictionary.
        """
        wenn self.mode is Nichts:
            mode = Nichts
        sonst:
            mode = self.mode & 0o7777
        info = {
            "name":     self.name,
            "mode":     mode,
            "uid":      self.uid,
            "gid":      self.gid,
            "size":     self.size,
            "mtime":    self.mtime,
            "chksum":   self.chksum,
            "type":     self.type,
            "linkname": self.linkname,
            "uname":    self.uname,
            "gname":    self.gname,
            "devmajor": self.devmajor,
            "devminor": self.devminor
        }

        wenn info["type"] == DIRTYPE und nicht info["name"].endswith("/"):
            info["name"] += "/"

        gib info

    def tobuf(self, format=DEFAULT_FORMAT, encoding=ENCODING, errors="surrogateescape"):
        """Return a tar header als a string of 512 byte blocks.
        """
        info = self.get_info()
        fuer name, value in info.items():
            wenn value is Nichts:
                raise ValueError("%s may nicht be Nichts" % name)

        wenn format == USTAR_FORMAT:
            gib self.create_ustar_header(info, encoding, errors)
        sowenn format == GNU_FORMAT:
            gib self.create_gnu_header(info, encoding, errors)
        sowenn format == PAX_FORMAT:
            gib self.create_pax_header(info, encoding)
        sonst:
            raise ValueError("invalid format")

    def create_ustar_header(self, info, encoding, errors):
        """Return the object als a ustar header block.
        """
        info["magic"] = POSIX_MAGIC

        wenn len(info["linkname"].encode(encoding, errors)) > LENGTH_LINK:
            raise ValueError("linkname is too long")

        wenn len(info["name"].encode(encoding, errors)) > LENGTH_NAME:
            info["prefix"], info["name"] = self._posix_split_name(info["name"], encoding, errors)

        gib self._create_header(info, USTAR_FORMAT, encoding, errors)

    def create_gnu_header(self, info, encoding, errors):
        """Return the object als a GNU header block sequence.
        """
        info["magic"] = GNU_MAGIC

        buf = b""
        wenn len(info["linkname"].encode(encoding, errors)) > LENGTH_LINK:
            buf += self._create_gnu_long_header(info["linkname"], GNUTYPE_LONGLINK, encoding, errors)

        wenn len(info["name"].encode(encoding, errors)) > LENGTH_NAME:
            buf += self._create_gnu_long_header(info["name"], GNUTYPE_LONGNAME, encoding, errors)

        gib buf + self._create_header(info, GNU_FORMAT, encoding, errors)

    def create_pax_header(self, info, encoding):
        """Return the object als a ustar header block. If it cannot be
           represented this way, prepend a pax extended header sequence
           mit supplement information.
        """
        info["magic"] = POSIX_MAGIC
        pax_headers = self.pax_headers.copy()

        # Test string fields fuer values that exceed the field length oder cannot
        # be represented in ASCII encoding.
        fuer name, hname, length in (
                ("name", "path", LENGTH_NAME), ("linkname", "linkpath", LENGTH_LINK),
                ("uname", "uname", 32), ("gname", "gname", 32)):

            wenn hname in pax_headers:
                # The pax header has priority.
                weiter

            # Try to encode the string als ASCII.
            try:
                info[name].encode("ascii", "strict")
            except UnicodeEncodeError:
                pax_headers[hname] = info[name]
                weiter

            wenn len(info[name]) > length:
                pax_headers[hname] = info[name]

        # Test number fields fuer values that exceed the field limit oder values
        # that like to be stored als float.
        fuer name, digits in (("uid", 8), ("gid", 8), ("size", 12), ("mtime", 12)):
            needs_pax = Falsch

            val = info[name]
            val_is_float = isinstance(val, float)
            val_int = round(val) wenn val_is_float sonst val
            wenn nicht 0 <= val_int < 8 ** (digits - 1):
                # Avoid overflow.
                info[name] = 0
                needs_pax = Wahr
            sowenn val_is_float:
                # Put rounded value in ustar header, und full
                # precision value in pax header.
                info[name] = val_int
                needs_pax = Wahr

            # The existing pax header has priority.
            wenn needs_pax und name nicht in pax_headers:
                pax_headers[name] = str(val)

        # Create a pax extended header wenn necessary.
        wenn pax_headers:
            buf = self._create_pax_generic_header(pax_headers, XHDTYPE, encoding)
        sonst:
            buf = b""

        gib buf + self._create_header(info, USTAR_FORMAT, "ascii", "replace")

    @classmethod
    def create_pax_global_header(cls, pax_headers):
        """Return the object als a pax global header block sequence.
        """
        gib cls._create_pax_generic_header(pax_headers, XGLTYPE, "utf-8")

    def _posix_split_name(self, name, encoding, errors):
        """Split a name longer than 100 chars into a prefix
           und a name part.
        """
        components = name.split("/")
        fuer i in range(1, len(components)):
            prefix = "/".join(components[:i])
            name = "/".join(components[i:])
            wenn len(prefix.encode(encoding, errors)) <= LENGTH_PREFIX und \
                    len(name.encode(encoding, errors)) <= LENGTH_NAME:
                breche
        sonst:
            raise ValueError("name is too long")

        gib prefix, name

    @staticmethod
    def _create_header(info, format, encoding, errors):
        """Return a header block. info is a dictionary mit file
           information, format must be one of the *_FORMAT constants.
        """
        has_device_fields = info.get("type") in (CHRTYPE, BLKTYPE)
        wenn has_device_fields:
            devmajor = itn(info.get("devmajor", 0), 8, format)
            devminor = itn(info.get("devminor", 0), 8, format)
        sonst:
            devmajor = stn("", 8, encoding, errors)
            devminor = stn("", 8, encoding, errors)

        # Nichts values in metadata should cause ValueError.
        # itn()/stn() do this fuer all fields except type.
        filetype = info.get("type", REGTYPE)
        wenn filetype is Nichts:
            raise ValueError("TarInfo.type must nicht be Nichts")

        parts = [
            stn(info.get("name", ""), 100, encoding, errors),
            itn(info.get("mode", 0) & 0o7777, 8, format),
            itn(info.get("uid", 0), 8, format),
            itn(info.get("gid", 0), 8, format),
            itn(info.get("size", 0), 12, format),
            itn(info.get("mtime", 0), 12, format),
            b"        ", # checksum field
            filetype,
            stn(info.get("linkname", ""), 100, encoding, errors),
            info.get("magic", POSIX_MAGIC),
            stn(info.get("uname", ""), 32, encoding, errors),
            stn(info.get("gname", ""), 32, encoding, errors),
            devmajor,
            devminor,
            stn(info.get("prefix", ""), 155, encoding, errors)
        ]

        buf = struct.pack("%ds" % BLOCKSIZE, b"".join(parts))
        chksum = calc_chksums(buf[-BLOCKSIZE:])[0]
        buf = buf[:-364] + bytes("%06o\0" % chksum, "ascii") + buf[-357:]
        gib buf

    @staticmethod
    def _create_payload(payload):
        """Return the string payload filled mit zero bytes
           up to the next 512 byte border.
        """
        blocks, remainder = divmod(len(payload), BLOCKSIZE)
        wenn remainder > 0:
            payload += (BLOCKSIZE - remainder) * NUL
        gib payload

    @classmethod
    def _create_gnu_long_header(cls, name, type, encoding, errors):
        """Return a GNUTYPE_LONGNAME oder GNUTYPE_LONGLINK sequence
           fuer name.
        """
        name = name.encode(encoding, errors) + NUL

        info = {}
        info["name"] = "././@LongLink"
        info["type"] = type
        info["size"] = len(name)
        info["magic"] = GNU_MAGIC

        # create extended header + name blocks.
        gib cls._create_header(info, USTAR_FORMAT, encoding, errors) + \
                cls._create_payload(name)

    @classmethod
    def _create_pax_generic_header(cls, pax_headers, type, encoding):
        """Return a POSIX.1-2008 extended oder global header sequence
           that contains a list of keyword, value pairs. The values
           must be strings.
        """
        # Check wenn one of the fields contains surrogate characters und thereby
        # forces hdrcharset=BINARY, see _proc_pax() fuer more information.
        binary = Falsch
        fuer keyword, value in pax_headers.items():
            try:
                value.encode("utf-8", "strict")
            except UnicodeEncodeError:
                binary = Wahr
                breche

        records = b""
        wenn binary:
            # Put the hdrcharset field at the beginning of the header.
            records += b"21 hdrcharset=BINARY\n"

        fuer keyword, value in pax_headers.items():
            keyword = keyword.encode("utf-8")
            wenn binary:
                # Try to restore the original byte representation of 'value'.
                # Needless to say, that the encoding must match the string.
                value = value.encode(encoding, "surrogateescape")
            sonst:
                value = value.encode("utf-8")

            l = len(keyword) + len(value) + 3   # ' ' + '=' + '\n'
            n = p = 0
            waehrend Wahr:
                n = l + len(str(p))
                wenn n == p:
                    breche
                p = n
            records += bytes(str(p), "ascii") + b" " + keyword + b"=" + value + b"\n"

        # We use a hardcoded "././@PaxHeader" name like star does
        # instead of the one that POSIX recommends.
        info = {}
        info["name"] = "././@PaxHeader"
        info["type"] = type
        info["size"] = len(records)
        info["magic"] = POSIX_MAGIC

        # Create pax header + record blocks.
        gib cls._create_header(info, USTAR_FORMAT, "ascii", "replace") + \
                cls._create_payload(records)

    @classmethod
    def frombuf(cls, buf, encoding, errors):
        """Construct a TarInfo object von a 512 byte bytes object.
        """
        wenn len(buf) == 0:
            raise EmptyHeaderError("empty header")
        wenn len(buf) != BLOCKSIZE:
            raise TruncatedHeaderError("truncated header")
        wenn buf.count(NUL) == BLOCKSIZE:
            raise EOFHeaderError("end of file header")

        chksum = nti(buf[148:156])
        wenn chksum nicht in calc_chksums(buf):
            raise InvalidHeaderError("bad checksum")

        obj = cls()
        obj.name = nts(buf[0:100], encoding, errors)
        obj.mode = nti(buf[100:108])
        obj.uid = nti(buf[108:116])
        obj.gid = nti(buf[116:124])
        obj.size = nti(buf[124:136])
        obj.mtime = nti(buf[136:148])
        obj.chksum = chksum
        obj.type = buf[156:157]
        obj.linkname = nts(buf[157:257], encoding, errors)
        obj.uname = nts(buf[265:297], encoding, errors)
        obj.gname = nts(buf[297:329], encoding, errors)
        obj.devmajor = nti(buf[329:337])
        obj.devminor = nti(buf[337:345])
        prefix = nts(buf[345:500], encoding, errors)

        # Old V7 tar format represents a directory als a regular
        # file mit a trailing slash.
        wenn obj.type == AREGTYPE und obj.name.endswith("/"):
            obj.type = DIRTYPE

        # The old GNU sparse format occupies some of the unused
        # space in the buffer fuer up to 4 sparse structures.
        # Save them fuer later processing in _proc_sparse().
        wenn obj.type == GNUTYPE_SPARSE:
            pos = 386
            structs = []
            fuer i in range(4):
                try:
                    offset = nti(buf[pos:pos + 12])
                    numbytes = nti(buf[pos + 12:pos + 24])
                except ValueError:
                    breche
                structs.append((offset, numbytes))
                pos += 24
            isextended = bool(buf[482])
            origsize = nti(buf[483:495])
            obj._sparse_structs = (structs, isextended, origsize)

        # Remove redundant slashes von directories.
        wenn obj.isdir():
            obj.name = obj.name.rstrip("/")

        # Reconstruct a ustar longname.
        wenn prefix und obj.type nicht in GNU_TYPES:
            obj.name = prefix + "/" + obj.name
        gib obj

    @classmethod
    def fromtarfile(cls, tarfile):
        """Return the next TarInfo object von TarFile object
           tarfile.
        """
        buf = tarfile.fileobj.read(BLOCKSIZE)
        obj = cls.frombuf(buf, tarfile.encoding, tarfile.errors)
        obj.offset = tarfile.fileobj.tell() - BLOCKSIZE
        gib obj._proc_member(tarfile)

    #--------------------------------------------------------------------------
    # The following are methods that are called depending on the type of a
    # member. The entry point is _proc_member() which can be overridden in a
    # subclass to add custom _proc_*() methods. A _proc_*() method MUST
    # implement the following
    # operations:
    # 1. Set self.offset_data to the position where the data blocks begin,
    #    wenn there is data that follows.
    # 2. Set tarfile.offset to the position where the next member's header will
    #    begin.
    # 3. Return self oder another valid TarInfo object.
    def _proc_member(self, tarfile):
        """Choose the right processing method depending on
           the type und call it.
        """
        wenn self.type in (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK):
            gib self._proc_gnulong(tarfile)
        sowenn self.type == GNUTYPE_SPARSE:
            gib self._proc_sparse(tarfile)
        sowenn self.type in (XHDTYPE, XGLTYPE, SOLARIS_XHDTYPE):
            gib self._proc_pax(tarfile)
        sonst:
            gib self._proc_builtin(tarfile)

    def _proc_builtin(self, tarfile):
        """Process a builtin type oder an unknown type which
           will be treated als a regular file.
        """
        self.offset_data = tarfile.fileobj.tell()
        offset = self.offset_data
        wenn self.isreg() oder self.type nicht in SUPPORTED_TYPES:
            # Skip the following data blocks.
            offset += self._block(self.size)
        tarfile.offset = offset

        # Patch the TarInfo object mit saved global
        # header information.
        self._apply_pax_info(tarfile.pax_headers, tarfile.encoding, tarfile.errors)

        # Remove redundant slashes von directories. This is to be consistent
        # mit frombuf().
        wenn self.isdir():
            self.name = self.name.rstrip("/")

        gib self

    def _proc_gnulong(self, tarfile):
        """Process the blocks that hold a GNU longname
           oder longlink member.
        """
        buf = tarfile.fileobj.read(self._block(self.size))

        # Fetch the next header und process it.
        try:
            next = self.fromtarfile(tarfile)
        except HeaderError als e:
            raise SubsequentHeaderError(str(e)) von Nichts

        # Patch the TarInfo object von the next header with
        # the longname information.
        next.offset = self.offset
        wenn self.type == GNUTYPE_LONGNAME:
            next.name = nts(buf, tarfile.encoding, tarfile.errors)
        sowenn self.type == GNUTYPE_LONGLINK:
            next.linkname = nts(buf, tarfile.encoding, tarfile.errors)

        # Remove redundant slashes von directories. This is to be consistent
        # mit frombuf().
        wenn next.isdir():
            next.name = next.name.removesuffix("/")

        gib next

    def _proc_sparse(self, tarfile):
        """Process a GNU sparse header plus extra headers.
        """
        # We already collected some sparse structures in frombuf().
        structs, isextended, origsize = self._sparse_structs
        del self._sparse_structs

        # Collect sparse structures von extended header blocks.
        waehrend isextended:
            buf = tarfile.fileobj.read(BLOCKSIZE)
            pos = 0
            fuer i in range(21):
                try:
                    offset = nti(buf[pos:pos + 12])
                    numbytes = nti(buf[pos + 12:pos + 24])
                except ValueError:
                    breche
                wenn offset und numbytes:
                    structs.append((offset, numbytes))
                pos += 24
            isextended = bool(buf[504])
        self.sparse = structs

        self.offset_data = tarfile.fileobj.tell()
        tarfile.offset = self.offset_data + self._block(self.size)
        self.size = origsize
        gib self

    def _proc_pax(self, tarfile):
        """Process an extended oder global header als described in
           POSIX.1-2008.
        """
        # Read the header information.
        buf = tarfile.fileobj.read(self._block(self.size))

        # A pax header stores supplemental information fuer either
        # the following file (extended) oder all following files
        # (global).
        wenn self.type == XGLTYPE:
            pax_headers = tarfile.pax_headers
        sonst:
            pax_headers = tarfile.pax_headers.copy()

        # Parse pax header information. A record looks like that:
        # "%d %s=%s\n" % (length, keyword, value). length is the size
        # of the complete record including the length field itself und
        # the newline.
        pos = 0
        encoding = Nichts
        raw_headers = []
        waehrend len(buf) > pos und buf[pos] != 0x00:
            wenn nicht (match := _header_length_prefix_re.match(buf, pos)):
                raise InvalidHeaderError("invalid header")
            try:
                length = int(match.group(1))
            except ValueError:
                raise InvalidHeaderError("invalid header")
            # Headers must be at least 5 bytes, shortest being '5 x=\n'.
            # Value is allowed to be empty.
            wenn length < 5:
                raise InvalidHeaderError("invalid header")
            wenn pos + length > len(buf):
                raise InvalidHeaderError("invalid header")

            header_value_end_offset = match.start(1) + length - 1  # Last byte of the header
            keyword_and_value = buf[match.end(1) + 1:header_value_end_offset]
            raw_keyword, equals, raw_value = keyword_and_value.partition(b"=")

            # Check the framing of the header. The last character must be '\n' (0x0A)
            wenn nicht raw_keyword oder equals != b"=" oder buf[header_value_end_offset] != 0x0A:
                raise InvalidHeaderError("invalid header")
            raw_headers.append((length, raw_keyword, raw_value))

            # Check wenn the pax header contains a hdrcharset field. This tells us
            # the encoding of the path, linkpath, uname und gname fields. Normally,
            # these fields are UTF-8 encoded but since POSIX.1-2008 tar
            # implementations are allowed to store them als raw binary strings if
            # the translation to UTF-8 fails. For the time being, we don't care about
            # anything other than "BINARY". The only other value that is currently
            # allowed by the standard is "ISO-IR 10646 2000 UTF-8" in other words UTF-8.
            # Note that we only follow the initial 'hdrcharset' setting to preserve
            # the initial behavior of the 'tarfile' module.
            wenn raw_keyword == b"hdrcharset" und encoding is Nichts:
                wenn raw_value == b"BINARY":
                    encoding = tarfile.encoding
                sonst:  # This branch ensures only the first 'hdrcharset' header is used.
                    encoding = "utf-8"

            pos += length

        # If no explicit hdrcharset is set, we use UTF-8 als a default.
        wenn encoding is Nichts:
            encoding = "utf-8"

        # After parsing the raw headers we can decode them to text.
        fuer length, raw_keyword, raw_value in raw_headers:
            # Normally, we could just use "utf-8" als the encoding und "strict"
            # als the error handler, but we better nicht take the risk. For
            # example, GNU tar <= 1.23 is known to store filenames it cannot
            # translate to UTF-8 als raw strings (unfortunately without a
            # hdrcharset=BINARY header).
            # We first try the strict standard encoding, und wenn that fails we
            # fall back on the user's encoding und error handler.
            keyword = self._decode_pax_field(raw_keyword, "utf-8", "utf-8",
                    tarfile.errors)
            wenn keyword in PAX_NAME_FIELDS:
                value = self._decode_pax_field(raw_value, encoding, tarfile.encoding,
                        tarfile.errors)
            sonst:
                value = self._decode_pax_field(raw_value, "utf-8", "utf-8",
                        tarfile.errors)

            pax_headers[keyword] = value

        # Fetch the next header.
        try:
            next = self.fromtarfile(tarfile)
        except HeaderError als e:
            raise SubsequentHeaderError(str(e)) von Nichts

        # Process GNU sparse information.
        wenn "GNU.sparse.map" in pax_headers:
            # GNU extended sparse format version 0.1.
            self._proc_gnusparse_01(next, pax_headers)

        sowenn "GNU.sparse.size" in pax_headers:
            # GNU extended sparse format version 0.0.
            self._proc_gnusparse_00(next, raw_headers)

        sowenn pax_headers.get("GNU.sparse.major") == "1" und pax_headers.get("GNU.sparse.minor") == "0":
            # GNU extended sparse format version 1.0.
            self._proc_gnusparse_10(next, pax_headers, tarfile)

        wenn self.type in (XHDTYPE, SOLARIS_XHDTYPE):
            # Patch the TarInfo object mit the extended header info.
            next._apply_pax_info(pax_headers, tarfile.encoding, tarfile.errors)
            next.offset = self.offset

            wenn "size" in pax_headers:
                # If the extended header replaces the size field,
                # we need to recalculate the offset where the next
                # header starts.
                offset = next.offset_data
                wenn next.isreg() oder next.type nicht in SUPPORTED_TYPES:
                    offset += next._block(next.size)
                tarfile.offset = offset

        gib next

    def _proc_gnusparse_00(self, next, raw_headers):
        """Process a GNU tar extended sparse header, version 0.0.
        """
        offsets = []
        numbytes = []
        fuer _, keyword, value in raw_headers:
            wenn keyword == b"GNU.sparse.offset":
                try:
                    offsets.append(int(value.decode()))
                except ValueError:
                    raise InvalidHeaderError("invalid header")

            sowenn keyword == b"GNU.sparse.numbytes":
                try:
                    numbytes.append(int(value.decode()))
                except ValueError:
                    raise InvalidHeaderError("invalid header")

        next.sparse = list(zip(offsets, numbytes))

    def _proc_gnusparse_01(self, next, pax_headers):
        """Process a GNU tar extended sparse header, version 0.1.
        """
        sparse = [int(x) fuer x in pax_headers["GNU.sparse.map"].split(",")]
        next.sparse = list(zip(sparse[::2], sparse[1::2]))

    def _proc_gnusparse_10(self, next, pax_headers, tarfile):
        """Process a GNU tar extended sparse header, version 1.0.
        """
        fields = Nichts
        sparse = []
        buf = tarfile.fileobj.read(BLOCKSIZE)
        fields, buf = buf.split(b"\n", 1)
        fields = int(fields)
        waehrend len(sparse) < fields * 2:
            wenn b"\n" nicht in buf:
                buf += tarfile.fileobj.read(BLOCKSIZE)
            number, buf = buf.split(b"\n", 1)
            sparse.append(int(number))
        next.offset_data = tarfile.fileobj.tell()
        next.sparse = list(zip(sparse[::2], sparse[1::2]))

    def _apply_pax_info(self, pax_headers, encoding, errors):
        """Replace fields mit supplemental information von a previous
           pax extended oder global header.
        """
        fuer keyword, value in pax_headers.items():
            wenn keyword == "GNU.sparse.name":
                setattr(self, "path", value)
            sowenn keyword == "GNU.sparse.size":
                setattr(self, "size", int(value))
            sowenn keyword == "GNU.sparse.realsize":
                setattr(self, "size", int(value))
            sowenn keyword in PAX_FIELDS:
                wenn keyword in PAX_NUMBER_FIELDS:
                    try:
                        value = PAX_NUMBER_FIELDS[keyword](value)
                    except ValueError:
                        value = 0
                wenn keyword == "path":
                    value = value.rstrip("/")
                setattr(self, keyword, value)

        self.pax_headers = pax_headers.copy()

    def _decode_pax_field(self, value, encoding, fallback_encoding, fallback_errors):
        """Decode a single field von a pax record.
        """
        try:
            gib value.decode(encoding, "strict")
        except UnicodeDecodeError:
            gib value.decode(fallback_encoding, fallback_errors)

    def _block(self, count):
        """Round up a byte count by BLOCKSIZE und gib it,
           e.g. _block(834) => 1024.
        """
        # Only non-negative offsets are allowed
        wenn count < 0:
            raise InvalidHeaderError("invalid offset")
        blocks, remainder = divmod(count, BLOCKSIZE)
        wenn remainder:
            blocks += 1
        gib blocks * BLOCKSIZE

    def isreg(self):
        'Return Wahr wenn the Tarinfo object is a regular file.'
        gib self.type in REGULAR_TYPES

    def isfile(self):
        'Return Wahr wenn the Tarinfo object is a regular file.'
        gib self.isreg()

    def isdir(self):
        'Return Wahr wenn it is a directory.'
        gib self.type == DIRTYPE

    def issym(self):
        'Return Wahr wenn it is a symbolic link.'
        gib self.type == SYMTYPE

    def islnk(self):
        'Return Wahr wenn it is a hard link.'
        gib self.type == LNKTYPE

    def ischr(self):
        'Return Wahr wenn it is a character device.'
        gib self.type == CHRTYPE

    def isblk(self):
        'Return Wahr wenn it is a block device.'
        gib self.type == BLKTYPE

    def isfifo(self):
        'Return Wahr wenn it is a FIFO.'
        gib self.type == FIFOTYPE

    def issparse(self):
        gib self.sparse is nicht Nichts

    def isdev(self):
        'Return Wahr wenn it is one of character device, block device oder FIFO.'
        gib self.type in (CHRTYPE, BLKTYPE, FIFOTYPE)
# klasse TarInfo

klasse TarFile(object):
    """The TarFile Class provides an interface to tar archives.
    """

    debug = 0                   # May be set von 0 (no msgs) to 3 (all msgs)

    dereference = Falsch         # If true, add content of linked file to the
                                # tar file, sonst the link.

    ignore_zeros = Falsch        # If true, skips empty oder invalid blocks und
                                # continues processing.

    errorlevel = 1              # If 0, fatal errors only appear in debug
                                # messages (if debug >= 0). If > 0, errors
                                # are passed to the caller als exceptions.

    format = DEFAULT_FORMAT     # The format to use when creating an archive.

    encoding = ENCODING         # Encoding fuer 8-bit character strings.

    errors = Nichts               # Error handler fuer unicode conversion.

    tarinfo = TarInfo           # The default TarInfo klasse to use.

    fileobject = ExFileObject   # The file-object fuer extractfile().

    extraction_filter = Nichts    # The default filter fuer extraction.

    def __init__(self, name=Nichts, mode="r", fileobj=Nichts, format=Nichts,
            tarinfo=Nichts, dereference=Nichts, ignore_zeros=Nichts, encoding=Nichts,
            errors="surrogateescape", pax_headers=Nichts, debug=Nichts,
            errorlevel=Nichts, copybufsize=Nichts, stream=Falsch):
        """Open an (uncompressed) tar archive 'name'. 'mode' is either 'r' to
           read von an existing archive, 'a' to append data to an existing
           file oder 'w' to create a new file overwriting an existing one. 'mode'
           defaults to 'r'.
           If 'fileobj' is given, it is used fuer reading oder writing data. If it
           can be determined, 'mode' is overridden by 'fileobj's mode.
           'fileobj' is nicht closed, when TarFile is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb", "x": "xb"}
        wenn mode nicht in modes:
            raise ValueError("mode must be 'r', 'a', 'w' oder 'x'")
        self.mode = mode
        self._mode = modes[mode]

        wenn nicht fileobj:
            wenn self.mode == "a" und nicht os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = Falsch
        sonst:
            wenn (name is Nichts und hasattr(fileobj, "name") und
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            wenn hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = Wahr
        self.name = os.path.abspath(name) wenn name sonst Nichts
        self.fileobj = fileobj

        self.stream = stream

        # Init attributes.
        wenn format is nicht Nichts:
            self.format = format
        wenn tarinfo is nicht Nichts:
            self.tarinfo = tarinfo
        wenn dereference is nicht Nichts:
            self.dereference = dereference
        wenn ignore_zeros is nicht Nichts:
            self.ignore_zeros = ignore_zeros
        wenn encoding is nicht Nichts:
            self.encoding = encoding
        self.errors = errors

        wenn pax_headers is nicht Nichts und self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        sonst:
            self.pax_headers = {}

        wenn debug is nicht Nichts:
            self.debug = debug
        wenn errorlevel is nicht Nichts:
            self.errorlevel = errorlevel

        # Init datastructures.
        self.copybufsize = copybufsize
        self.closed = Falsch
        self.members = []       # list of members als TarInfo objects
        self._loaded = Falsch    # flag wenn all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added
        self._unames = {}       # Cached mappings of uid -> uname
        self._gnames = {}       # Cached mappings of gid -> gname

        try:
            wenn self.mode == "r":
                self.firstmember = Nichts
                self.firstmember = self.next()

            wenn self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                waehrend Wahr:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        breche
                    except HeaderError als e:
                        raise ReadError(str(e)) von Nichts

            wenn self.mode in ("a", "w", "x"):
                self._loaded = Wahr

                wenn self.pax_headers:
                    buf = self.tarinfo.create_pax_global_header(self.pax_headers.copy())
                    self.fileobj.write(buf)
                    self.offset += len(buf)
        except:
            wenn nicht self._extfileobj:
                self.fileobj.close()
            self.closed = Wahr
            raise

    #--------------------------------------------------------------------------
    # Below are the classmethods which act als alternate constructors to the
    # TarFile class. The open() method is the only one that is needed for
    # public use; it is the "super"-constructor und is able to select an
    # adequate "sub"-constructor fuer a particular compression using the mapping
    # von OPEN_METH.
    #
    # This concept allows one to subclass TarFile without losing the comfort of
    # the super-constructor. A sub-constructor is registered und made available
    # by adding it to the mapping in OPEN_METH.

    @classmethod
    def open(cls, name=Nichts, mode="r", fileobj=Nichts, bufsize=RECORDSIZE, **kwargs):
        """Open a tar archive fuer reading, writing oder appending. Return
           an appropriate TarFile class.

           mode:
           'r' oder 'r:*' open fuer reading mit transparent compression
           'r:'         open fuer reading exclusively uncompressed
           'r:gz'       open fuer reading mit gzip compression
           'r:bz2'      open fuer reading mit bzip2 compression
           'r:xz'       open fuer reading mit lzma compression
           'r:zst'      open fuer reading mit zstd compression
           'a' oder 'a:'  open fuer appending, creating the file wenn necessary
           'w' oder 'w:'  open fuer writing without compression
           'w:gz'       open fuer writing mit gzip compression
           'w:bz2'      open fuer writing mit bzip2 compression
           'w:xz'       open fuer writing mit lzma compression
           'w:zst'      open fuer writing mit zstd compression

           'x' oder 'x:'  create a tarfile exclusively without compression, raise
                        an exception wenn the file is already created
           'x:gz'       create a gzip compressed tarfile, raise an exception
                        wenn the file is already created
           'x:bz2'      create a bzip2 compressed tarfile, raise an exception
                        wenn the file is already created
           'x:xz'       create an lzma compressed tarfile, raise an exception
                        wenn the file is already created
           'x:zst'      create a zstd compressed tarfile, raise an exception
                        wenn the file is already created

           'r|*'        open a stream of tar blocks mit transparent compression
           'r|'         open an uncompressed stream of tar blocks fuer reading
           'r|gz'       open a gzip compressed stream of tar blocks
           'r|bz2'      open a bzip2 compressed stream of tar blocks
           'r|xz'       open an lzma compressed stream of tar blocks
           'r|zst'      open a zstd compressed stream of tar blocks
           'w|'         open an uncompressed stream fuer writing
           'w|gz'       open a gzip compressed stream fuer writing
           'w|bz2'      open a bzip2 compressed stream fuer writing
           'w|xz'       open an lzma compressed stream fuer writing
           'w|zst'      open a zstd compressed stream fuer writing
        """

        wenn nicht name und nicht fileobj:
            raise ValueError("nothing to open")

        wenn mode in ("r", "r:*"):
            # Find out which *open() is appropriate fuer opening the file.
            def not_compressed(comptype):
                gib cls.OPEN_METH[comptype] == 'taropen'
            error_msgs = []
            fuer comptype in sorted(cls.OPEN_METH, key=not_compressed):
                func = getattr(cls, cls.OPEN_METH[comptype])
                wenn fileobj is nicht Nichts:
                    saved_pos = fileobj.tell()
                try:
                    gib func(name, "r", fileobj, **kwargs)
                except (ReadError, CompressionError) als e:
                    error_msgs.append(f'- method {comptype}: {e!r}')
                    wenn fileobj is nicht Nichts:
                        fileobj.seek(saved_pos)
                    weiter
            error_msgs_summary = '\n'.join(error_msgs)
            raise ReadError(f"file could nicht be opened successfully:\n{error_msgs_summary}")

        sowenn ":" in mode:
            filemode, comptype = mode.split(":", 1)
            filemode = filemode oder "r"
            comptype = comptype oder "tar"

            # Select the *open() function according to
            # given compression.
            wenn comptype in cls.OPEN_METH:
                func = getattr(cls, cls.OPEN_METH[comptype])
            sonst:
                raise CompressionError("unknown compression type %r" % comptype)
            gib func(name, filemode, fileobj, **kwargs)

        sowenn "|" in mode:
            filemode, comptype = mode.split("|", 1)
            filemode = filemode oder "r"
            comptype = comptype oder "tar"

            wenn filemode nicht in ("r", "w"):
                raise ValueError("mode must be 'r' oder 'w'")
            wenn "compresslevel" in kwargs und comptype nicht in ("gz", "bz2"):
                raise ValueError(
                    "compresslevel is only valid fuer w|gz und w|bz2 modes"
                )
            wenn "preset" in kwargs und comptype nicht in ("xz",):
                raise ValueError("preset is only valid fuer w|xz mode")

            compresslevel = kwargs.pop("compresslevel", 6)
            preset = kwargs.pop("preset", Nichts)
            stream = _Stream(name, filemode, comptype, fileobj, bufsize,
                             compresslevel, preset)
            try:
                t = cls(name, filemode, stream, **kwargs)
            except:
                stream.close()
                raise
            t._extfileobj = Falsch
            gib t

        sowenn mode in ("a", "w", "x"):
            gib cls.taropen(name, mode, fileobj, **kwargs)

        raise ValueError("undiscernible mode")

    @classmethod
    def taropen(cls, name, mode="r", fileobj=Nichts, **kwargs):
        """Open uncompressed tar archive name fuer reading oder writing.
        """
        wenn mode nicht in ("r", "a", "w", "x"):
            raise ValueError("mode must be 'r', 'a', 'w' oder 'x'")
        gib cls(name, mode, fileobj, **kwargs)

    @classmethod
    def gzopen(cls, name, mode="r", fileobj=Nichts, compresslevel=6, **kwargs):
        """Open gzip compressed tar archive name fuer reading oder writing.
           Appending is nicht allowed.
        """
        wenn mode nicht in ("r", "w", "x"):
            raise ValueError("mode must be 'r', 'w' oder 'x'")

        try:
            von gzip importiere GzipFile
        except ImportError:
            raise CompressionError("gzip module is nicht available") von Nichts

        try:
            fileobj = GzipFile(name, mode + "b", compresslevel, fileobj)
        except OSError als e:
            wenn fileobj is nicht Nichts und mode == 'r':
                raise ReadError("not a gzip file") von e
            raise

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except OSError als e:
            fileobj.close()
            wenn mode == 'r':
                raise ReadError("not a gzip file") von e
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = Falsch
        gib t

    @classmethod
    def bz2open(cls, name, mode="r", fileobj=Nichts, compresslevel=9, **kwargs):
        """Open bzip2 compressed tar archive name fuer reading oder writing.
           Appending is nicht allowed.
        """
        wenn mode nicht in ("r", "w", "x"):
            raise ValueError("mode must be 'r', 'w' oder 'x'")

        try:
            von bz2 importiere BZ2File
        except ImportError:
            raise CompressionError("bz2 module is nicht available") von Nichts

        fileobj = BZ2File(fileobj oder name, mode, compresslevel=compresslevel)

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (OSError, EOFError) als e:
            fileobj.close()
            wenn mode == 'r':
                raise ReadError("not a bzip2 file") von e
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = Falsch
        gib t

    @classmethod
    def xzopen(cls, name, mode="r", fileobj=Nichts, preset=Nichts, **kwargs):
        """Open lzma compressed tar archive name fuer reading oder writing.
           Appending is nicht allowed.
        """
        wenn mode nicht in ("r", "w", "x"):
            raise ValueError("mode must be 'r', 'w' oder 'x'")

        try:
            von lzma importiere LZMAFile, LZMAError
        except ImportError:
            raise CompressionError("lzma module is nicht available") von Nichts

        fileobj = LZMAFile(fileobj oder name, mode, preset=preset)

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (LZMAError, EOFError) als e:
            fileobj.close()
            wenn mode == 'r':
                raise ReadError("not an lzma file") von e
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = Falsch
        gib t

    @classmethod
    def zstopen(cls, name, mode="r", fileobj=Nichts, level=Nichts, options=Nichts,
                zstd_dict=Nichts, **kwargs):
        """Open zstd compressed tar archive name fuer reading oder writing.
           Appending is nicht allowed.
        """
        wenn mode nicht in ("r", "w", "x"):
            raise ValueError("mode must be 'r', 'w' oder 'x'")

        try:
            von compression.zstd importiere ZstdFile, ZstdError
        except ImportError:
            raise CompressionError("compression.zstd module is nicht available") von Nichts

        fileobj = ZstdFile(
            fileobj oder name,
            mode,
            level=level,
            options=options,
            zstd_dict=zstd_dict
        )

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (ZstdError, EOFError) als e:
            fileobj.close()
            wenn mode == 'r':
                raise ReadError("not a zstd file") von e
            raise
        except Exception:
            fileobj.close()
            raise
        t._extfileobj = Falsch
        gib t

    # All *open() methods are registered here.
    OPEN_METH = {
        "tar": "taropen",   # uncompressed tar
        "gz":  "gzopen",    # gzip compressed tar
        "bz2": "bz2open",   # bzip2 compressed tar
        "xz":  "xzopen",    # lzma compressed tar
        "zst": "zstopen",   # zstd compressed tar
    }

    #--------------------------------------------------------------------------
    # The public methods which TarFile provides:

    def close(self):
        """Close the TarFile. In write-mode, two finishing zero blocks are
           appended to the archive.
        """
        wenn self.closed:
            gib

        self.closed = Wahr
        try:
            wenn self.mode in ("a", "w", "x"):
                self.fileobj.write(NUL * (BLOCKSIZE * 2))
                self.offset += (BLOCKSIZE * 2)
                # fill up the end mit zero-blocks
                # (like option -b20 fuer tar does)
                blocks, remainder = divmod(self.offset, RECORDSIZE)
                wenn remainder > 0:
                    self.fileobj.write(NUL * (RECORDSIZE - remainder))
        finally:
            wenn nicht self._extfileobj:
                self.fileobj.close()

    def getmember(self, name):
        """Return a TarInfo object fuer member 'name'. If 'name' can nicht be
           found in the archive, KeyError is raised. If a member occurs more
           than once in the archive, its last occurrence is assumed to be the
           most up-to-date version.
        """
        tarinfo = self._getmember(name.rstrip('/'))
        wenn tarinfo is Nichts:
            raise KeyError("filename %r nicht found" % name)
        gib tarinfo

    def getmembers(self):
        """Return the members of the archive als a list of TarInfo objects. The
           list has the same order als the members in the archive.
        """
        self._check()
        wenn nicht self._loaded:    # wenn we want to obtain a list of
            self._load()        # all members, we first have to
                                # scan the whole archive.
        gib self.members

    def getnames(self):
        """Return the members of the archive als a list of their names. It has
           the same order als the list returned by getmembers().
        """
        gib [tarinfo.name fuer tarinfo in self.getmembers()]

    def gettarinfo(self, name=Nichts, arcname=Nichts, fileobj=Nichts):
        """Create a TarInfo object von the result of os.stat oder equivalent
           on an existing file. The file is either named by 'name', oder
           specified als a file object 'fileobj' mit a file descriptor. If
           given, 'arcname' specifies an alternative name fuer the file in the
           archive, otherwise, the name is taken von the 'name' attribute of
           'fileobj', oder the 'name' argument. The name should be a text
           string.
        """
        self._check("awx")

        # When fileobj is given, replace name by
        # fileobj's real name.
        wenn fileobj is nicht Nichts:
            name = fileobj.name

        # Building the name of the member in the archive.
        # Backward slashes are converted to forward slashes,
        # Absolute paths are turned to relative paths.
        wenn arcname is Nichts:
            arcname = name
        drv, arcname = os.path.splitdrive(arcname)
        arcname = arcname.replace(os.sep, "/")
        arcname = arcname.lstrip("/")

        # Now, fill the TarInfo object with
        # information specific fuer the file.
        tarinfo = self.tarinfo()
        tarinfo._tarfile = self  # To be removed in 3.16.

        # Use os.stat oder os.lstat, depending on wenn symlinks shall be resolved.
        wenn fileobj is Nichts:
            wenn nicht self.dereference:
                statres = os.lstat(name)
            sonst:
                statres = os.stat(name)
        sonst:
            statres = os.fstat(fileobj.fileno())
        linkname = ""

        stmd = statres.st_mode
        wenn stat.S_ISREG(stmd):
            inode = (statres.st_ino, statres.st_dev)
            wenn nicht self.dereference und statres.st_nlink > 1 und \
                    inode in self.inodes und arcname != self.inodes[inode]:
                # Is it a hardlink to an already
                # archived file?
                type = LNKTYPE
                linkname = self.inodes[inode]
            sonst:
                # The inode is added only wenn its valid.
                # For win32 it is always 0.
                type = REGTYPE
                wenn inode[0]:
                    self.inodes[inode] = arcname
        sowenn stat.S_ISDIR(stmd):
            type = DIRTYPE
        sowenn stat.S_ISFIFO(stmd):
            type = FIFOTYPE
        sowenn stat.S_ISLNK(stmd):
            type = SYMTYPE
            linkname = os.readlink(name)
        sowenn stat.S_ISCHR(stmd):
            type = CHRTYPE
        sowenn stat.S_ISBLK(stmd):
            type = BLKTYPE
        sonst:
            gib Nichts

        # Fill the TarInfo object mit all
        # information we can get.
        tarinfo.name = arcname
        tarinfo.mode = stmd
        tarinfo.uid = statres.st_uid
        tarinfo.gid = statres.st_gid
        wenn type == REGTYPE:
            tarinfo.size = statres.st_size
        sonst:
            tarinfo.size = 0
        tarinfo.mtime = statres.st_mtime
        tarinfo.type = type
        tarinfo.linkname = linkname

        # Calls to pwd.getpwuid() und grp.getgrgid() tend to be expensive. To
        # speed things up, cache the resolved usernames und group names.
        wenn pwd:
            wenn tarinfo.uid nicht in self._unames:
                try:
                    self._unames[tarinfo.uid] = pwd.getpwuid(tarinfo.uid)[0]
                except KeyError:
                    self._unames[tarinfo.uid] = ''
            tarinfo.uname = self._unames[tarinfo.uid]
        wenn grp:
            wenn tarinfo.gid nicht in self._gnames:
                try:
                    self._gnames[tarinfo.gid] = grp.getgrgid(tarinfo.gid)[0]
                except KeyError:
                    self._gnames[tarinfo.gid] = ''
            tarinfo.gname = self._gnames[tarinfo.gid]

        wenn type in (CHRTYPE, BLKTYPE):
            wenn hasattr(os, "major") und hasattr(os, "minor"):
                tarinfo.devmajor = os.major(statres.st_rdev)
                tarinfo.devminor = os.minor(statres.st_rdev)
        gib tarinfo

    def list(self, verbose=Wahr, *, members=Nichts):
        """Print a table of contents to sys.stdout. If 'verbose' is Falsch, only
           the names of the members are printed. If it is Wahr, an 'ls -l'-like
           output is produced. 'members' is optional und must be a subset of the
           list returned by getmembers().
        """
        # Convert tarinfo type to stat type.
        type2mode = {REGTYPE: stat.S_IFREG, SYMTYPE: stat.S_IFLNK,
                     FIFOTYPE: stat.S_IFIFO, CHRTYPE: stat.S_IFCHR,
                     DIRTYPE: stat.S_IFDIR, BLKTYPE: stat.S_IFBLK}
        self._check()

        wenn members is Nichts:
            members = self
        fuer tarinfo in members:
            wenn verbose:
                wenn tarinfo.mode is Nichts:
                    _safe_drucke("??????????")
                sonst:
                    modetype = type2mode.get(tarinfo.type, 0)
                    _safe_drucke(stat.filemode(modetype | tarinfo.mode))
                _safe_drucke("%s/%s" % (tarinfo.uname oder tarinfo.uid,
                                       tarinfo.gname oder tarinfo.gid))
                wenn tarinfo.ischr() oder tarinfo.isblk():
                    _safe_drucke("%10s" %
                            ("%d,%d" % (tarinfo.devmajor, tarinfo.devminor)))
                sonst:
                    _safe_drucke("%10d" % tarinfo.size)
                wenn tarinfo.mtime is Nichts:
                    _safe_drucke("????-??-?? ??:??:??")
                sonst:
                    _safe_drucke("%d-%02d-%02d %02d:%02d:%02d" \
                                % time.localtime(tarinfo.mtime)[:6])

            _safe_drucke(tarinfo.name + ("/" wenn tarinfo.isdir() sonst ""))

            wenn verbose:
                wenn tarinfo.issym():
                    _safe_drucke("-> " + tarinfo.linkname)
                wenn tarinfo.islnk():
                    _safe_drucke("link to " + tarinfo.linkname)
            drucke()

    def add(self, name, arcname=Nichts, recursive=Wahr, *, filter=Nichts):
        """Add the file 'name' to the archive. 'name' may be any type of file
           (directory, fifo, symbolic link, etc.). If given, 'arcname'
           specifies an alternative name fuer the file in the archive.
           Directories are added recursively by default. This can be avoided by
           setting 'recursive' to Falsch. 'filter' is a function
           that expects a TarInfo object argument und returns the changed
           TarInfo object, wenn it returns Nichts the TarInfo object will be
           excluded von the archive.
        """
        self._check("awx")

        wenn arcname is Nichts:
            arcname = name

        # Skip wenn somebody tries to archive the archive...
        wenn self.name is nicht Nichts und os.path.abspath(name) == self.name:
            self._dbg(2, "tarfile: Skipped %r" % name)
            gib

        self._dbg(1, name)

        # Create a TarInfo object von the file.
        tarinfo = self.gettarinfo(name, arcname)

        wenn tarinfo is Nichts:
            self._dbg(1, "tarfile: Unsupported type %r" % name)
            gib

        # Change oder exclude the TarInfo object.
        wenn filter is nicht Nichts:
            tarinfo = filter(tarinfo)
            wenn tarinfo is Nichts:
                self._dbg(2, "tarfile: Excluded %r" % name)
                gib

        # Append the tar header und data to the archive.
        wenn tarinfo.isreg():
            mit bltn_open(name, "rb") als f:
                self.addfile(tarinfo, f)

        sowenn tarinfo.isdir():
            self.addfile(tarinfo)
            wenn recursive:
                fuer f in sorted(os.listdir(name)):
                    self.add(os.path.join(name, f), os.path.join(arcname, f),
                            recursive, filter=filter)

        sonst:
            self.addfile(tarinfo)

    def addfile(self, tarinfo, fileobj=Nichts):
        """Add the TarInfo object 'tarinfo' to the archive. If 'tarinfo' represents
           a non zero-size regular file, the 'fileobj' argument should be a binary file,
           und tarinfo.size bytes are read von it und added to the archive.
           You can create TarInfo objects directly, oder by using gettarinfo().
        """
        self._check("awx")

        wenn fileobj is Nichts und tarinfo.isreg() und tarinfo.size != 0:
            raise ValueError("fileobj nicht provided fuer non zero-size regular file")

        tarinfo = copy.copy(tarinfo)

        buf = tarinfo.tobuf(self.format, self.encoding, self.errors)
        self.fileobj.write(buf)
        self.offset += len(buf)
        bufsize=self.copybufsize
        # If there's data to follow, append it.
        wenn fileobj is nicht Nichts:
            copyfileobj(fileobj, self.fileobj, tarinfo.size, bufsize=bufsize)
            blocks, remainder = divmod(tarinfo.size, BLOCKSIZE)
            wenn remainder > 0:
                self.fileobj.write(NUL * (BLOCKSIZE - remainder))
                blocks += 1
            self.offset += blocks * BLOCKSIZE

        self.members.append(tarinfo)

    def _get_filter_function(self, filter):
        wenn filter is Nichts:
            filter = self.extraction_filter
            wenn filter is Nichts:
                gib data_filter
            wenn isinstance(filter, str):
                raise TypeError(
                    'String names are nicht supported fuer '
                    + 'TarFile.extraction_filter. Use a function such als '
                    + 'tarfile.data_filter directly.')
            gib filter
        wenn callable(filter):
            gib filter
        try:
            gib _NAMED_FILTERS[filter]
        except KeyError:
            raise ValueError(f"filter {filter!r} nicht found") von Nichts

    def extractall(self, path=".", members=Nichts, *, numeric_owner=Falsch,
                   filter=Nichts):
        """Extract all members von the archive to the current working
           directory und set owner, modification time und permissions on
           directories afterwards. 'path' specifies a different directory
           to extract to. 'members' is optional und must be a subset of the
           list returned by getmembers(). If 'numeric_owner' is Wahr, only
           the numbers fuer user/group names are used und nicht the names.

           The 'filter' function will be called on each member just
           before extraction.
           It can gib a changed TarInfo oder Nichts to skip the member.
           String names of common filters are accepted.
        """
        directories = []

        filter_function = self._get_filter_function(filter)
        wenn members is Nichts:
            members = self

        fuer member in members:
            tarinfo, unfiltered = self._get_extract_tarinfo(
                member, filter_function, path)
            wenn tarinfo is Nichts:
                weiter
            wenn tarinfo.isdir():
                # For directories, delay setting attributes until later,
                # since permissions can interfere mit extraction und
                # extracting contents can reset mtime.
                directories.append(unfiltered)
            self._extract_one(tarinfo, path, set_attrs=nicht tarinfo.isdir(),
                              numeric_owner=numeric_owner,
                              filter_function=filter_function)

        # Reverse sort directories.
        directories.sort(key=lambda a: a.name, reverse=Wahr)


        # Set correct owner, mtime und filemode on directories.
        fuer unfiltered in directories:
            try:
                # Need to re-apply any filter, to take the *current* filesystem
                # state into account.
                try:
                    tarinfo = filter_function(unfiltered, path)
                except _FILTER_ERRORS als exc:
                    self._log_no_directory_fixup(unfiltered, repr(exc))
                    weiter
                wenn tarinfo is Nichts:
                    self._log_no_directory_fixup(unfiltered,
                                                 'excluded by filter')
                    weiter
                dirpath = os.path.join(path, tarinfo.name)
                try:
                    lstat = os.lstat(dirpath)
                except FileNotFoundError:
                    self._log_no_directory_fixup(tarinfo, 'missing')
                    weiter
                wenn nicht stat.S_ISDIR(lstat.st_mode):
                    # This is no longer a directory; presumably a later
                    # member overwrote the entry.
                    self._log_no_directory_fixup(tarinfo, 'not a directory')
                    weiter
                self.chown(tarinfo, dirpath, numeric_owner=numeric_owner)
                self.utime(tarinfo, dirpath)
                self.chmod(tarinfo, dirpath)
            except ExtractError als e:
                self._handle_nonfatal_error(e)

    def _log_no_directory_fixup(self, member, reason):
        self._dbg(2, "tarfile: Not fixing up directory %r (%s)" %
                  (member.name, reason))

    def extract(self, member, path="", set_attrs=Wahr, *, numeric_owner=Falsch,
                filter=Nichts):
        """Extract a member von the archive to the current working directory,
           using its full name. Its file information is extracted als accurately
           als possible. 'member' may be a filename oder a TarInfo object. You can
           specify a different directory using 'path'. File attributes (owner,
           mtime, mode) are set unless 'set_attrs' is Falsch. If 'numeric_owner'
           is Wahr, only the numbers fuer user/group names are used und not
           the names.

           The 'filter' function will be called before extraction.
           It can gib a changed TarInfo oder Nichts to skip the member.
           String names of common filters are accepted.
        """
        filter_function = self._get_filter_function(filter)
        tarinfo, unfiltered = self._get_extract_tarinfo(
            member, filter_function, path)
        wenn tarinfo is nicht Nichts:
            self._extract_one(tarinfo, path, set_attrs, numeric_owner)

    def _get_extract_tarinfo(self, member, filter_function, path):
        """Get (filtered, unfiltered) TarInfos von *member*

        *member* might be a string.

        Return (Nichts, Nichts) wenn nicht found.
        """

        wenn isinstance(member, str):
            unfiltered = self.getmember(member)
        sonst:
            unfiltered = member

        filtered = Nichts
        try:
            filtered = filter_function(unfiltered, path)
        except (OSError, UnicodeEncodeError, FilterError) als e:
            self._handle_fatal_error(e)
        except ExtractError als e:
            self._handle_nonfatal_error(e)
        wenn filtered is Nichts:
            self._dbg(2, "tarfile: Excluded %r" % unfiltered.name)
            gib Nichts, Nichts

        # Prepare the link target fuer makelink().
        wenn filtered.islnk():
            filtered = copy.copy(filtered)
            filtered._link_target = os.path.join(path, filtered.linkname)
        gib filtered, unfiltered

    def _extract_one(self, tarinfo, path, set_attrs, numeric_owner,
                     filter_function=Nichts):
        """Extract von filtered tarinfo to disk.

           filter_function is only used when extracting a *different*
           member (e.g. als fallback to creating a symlink)
        """
        self._check("r")

        try:
            self._extract_member(tarinfo, os.path.join(path, tarinfo.name),
                                 set_attrs=set_attrs,
                                 numeric_owner=numeric_owner,
                                 filter_function=filter_function,
                                 extraction_root=path)
        except (OSError, UnicodeEncodeError) als e:
            self._handle_fatal_error(e)
        except ExtractError als e:
            self._handle_nonfatal_error(e)

    def _handle_nonfatal_error(self, e):
        """Handle non-fatal error (ExtractError) according to errorlevel"""
        wenn self.errorlevel > 1:
            raise
        sonst:
            self._dbg(1, "tarfile: %s" % e)

    def _handle_fatal_error(self, e):
        """Handle "fatal" error according to self.errorlevel"""
        wenn self.errorlevel > 0:
            raise
        sowenn isinstance(e, OSError):
            wenn e.filename is Nichts:
                self._dbg(1, "tarfile: %s" % e.strerror)
            sonst:
                self._dbg(1, "tarfile: %s %r" % (e.strerror, e.filename))
        sonst:
            self._dbg(1, "tarfile: %s %s" % (type(e).__name__, e))

    def extractfile(self, member):
        """Extract a member von the archive als a file object. 'member' may be
           a filename oder a TarInfo object. If 'member' is a regular file oder
           a link, an io.BufferedReader object is returned. For all other
           existing members, Nichts is returned. If 'member' does nicht appear
           in the archive, KeyError is raised.
        """
        self._check("r")

        wenn isinstance(member, str):
            tarinfo = self.getmember(member)
        sonst:
            tarinfo = member

        wenn tarinfo.isreg() oder tarinfo.type nicht in SUPPORTED_TYPES:
            # Members mit unknown types are treated als regular files.
            gib self.fileobject(self, tarinfo)

        sowenn tarinfo.islnk() oder tarinfo.issym():
            wenn isinstance(self.fileobj, _Stream):
                # A small but ugly workaround fuer the case that someone tries
                # to extract a (sym)link als a file-object von a non-seekable
                # stream of tar blocks.
                raise StreamError("cannot extract (sym)link als file object")
            sonst:
                # A (sym)link's file object is its target's file object.
                gib self.extractfile(self._find_link_target(tarinfo))
        sonst:
            # If there's no data associated mit the member (directory, chrdev,
            # blkdev, etc.), gib Nichts instead of a file object.
            gib Nichts

    def _extract_member(self, tarinfo, targetpath, set_attrs=Wahr,
                        numeric_owner=Falsch, *, filter_function=Nichts,
                        extraction_root=Nichts):
        """Extract the filtered TarInfo object tarinfo to a physical
           file called targetpath.

           filter_function is only used when extracting a *different*
           member (e.g. als fallback to creating a symlink)
        """
        # Fetch the TarInfo object fuer the given name
        # und build the destination pathname, replacing
        # forward slashes to platform specific separators.
        targetpath = targetpath.rstrip("/")
        targetpath = targetpath.replace("/", os.sep)

        # Create all upper directories.
        upperdirs = os.path.dirname(targetpath)
        wenn upperdirs und nicht os.path.exists(upperdirs):
            # Create directories that are nicht part of the archive with
            # default permissions.
            os.makedirs(upperdirs, exist_ok=Wahr)

        wenn tarinfo.islnk() oder tarinfo.issym():
            self._dbg(1, "%s -> %s" % (tarinfo.name, tarinfo.linkname))
        sonst:
            self._dbg(1, tarinfo.name)

        wenn tarinfo.isreg():
            self.makefile(tarinfo, targetpath)
        sowenn tarinfo.isdir():
            self.makedir(tarinfo, targetpath)
        sowenn tarinfo.isfifo():
            self.makefifo(tarinfo, targetpath)
        sowenn tarinfo.ischr() oder tarinfo.isblk():
            self.makedev(tarinfo, targetpath)
        sowenn tarinfo.islnk() oder tarinfo.issym():
            self.makelink_with_filter(
                tarinfo, targetpath,
                filter_function=filter_function,
                extraction_root=extraction_root)
        sowenn tarinfo.type nicht in SUPPORTED_TYPES:
            self.makeunknown(tarinfo, targetpath)
        sonst:
            self.makefile(tarinfo, targetpath)

        wenn set_attrs:
            self.chown(tarinfo, targetpath, numeric_owner)
            wenn nicht tarinfo.issym():
                self.chmod(tarinfo, targetpath)
                self.utime(tarinfo, targetpath)

    #--------------------------------------------------------------------------
    # Below are the different file methods. They are called via
    # _extract_member() when extract() is called. They can be replaced in a
    # subclass to implement other functionality.

    def makedir(self, tarinfo, targetpath):
        """Make a directory called targetpath.
        """
        try:
            wenn tarinfo.mode is Nichts:
                # Use the system's default mode
                os.mkdir(targetpath)
            sonst:
                # Use a safe mode fuer the directory, the real mode is set
                # later in _extract_member().
                os.mkdir(targetpath, 0o700)
        except FileExistsError:
            wenn nicht os.path.isdir(targetpath):
                raise

    def makefile(self, tarinfo, targetpath):
        """Make a file called targetpath.
        """
        source = self.fileobj
        source.seek(tarinfo.offset_data)
        bufsize = self.copybufsize
        mit bltn_open(targetpath, "wb") als target:
            wenn tarinfo.sparse is nicht Nichts:
                fuer offset, size in tarinfo.sparse:
                    target.seek(offset)
                    copyfileobj(source, target, size, ReadError, bufsize)
                target.seek(tarinfo.size)
                target.truncate()
            sonst:
                copyfileobj(source, target, tarinfo.size, ReadError, bufsize)

    def makeunknown(self, tarinfo, targetpath):
        """Make a file von a TarInfo object mit an unknown type
           at targetpath.
        """
        self.makefile(tarinfo, targetpath)
        self._dbg(1, "tarfile: Unknown file type %r, " \
                     "extracted als regular file." % tarinfo.type)

    def makefifo(self, tarinfo, targetpath):
        """Make a fifo called targetpath.
        """
        wenn hasattr(os, "mkfifo"):
            os.mkfifo(targetpath)
        sonst:
            raise ExtractError("fifo nicht supported by system")

    def makedev(self, tarinfo, targetpath):
        """Make a character oder block device called targetpath.
        """
        wenn nicht hasattr(os, "mknod") oder nicht hasattr(os, "makedev"):
            raise ExtractError("special devices nicht supported by system")

        mode = tarinfo.mode
        wenn mode is Nichts:
            # Use mknod's default
            mode = 0o600
        wenn tarinfo.isblk():
            mode |= stat.S_IFBLK
        sonst:
            mode |= stat.S_IFCHR

        os.mknod(targetpath, mode,
                 os.makedev(tarinfo.devmajor, tarinfo.devminor))

    def makelink(self, tarinfo, targetpath):
        gib self.makelink_with_filter(tarinfo, targetpath, Nichts, Nichts)

    def makelink_with_filter(self, tarinfo, targetpath,
                             filter_function, extraction_root):
        """Make a (symbolic) link called targetpath. If it cannot be created
          (platform limitation), we try to make a copy of the referenced file
          instead of a link.

          filter_function is only used when extracting a *different*
          member (e.g. als fallback to creating a link).
        """
        keyerror_to_extracterror = Falsch
        try:
            # For systems that support symbolic und hard links.
            wenn tarinfo.issym():
                wenn os.path.lexists(targetpath):
                    # Avoid FileExistsError on following os.symlink.
                    os.unlink(targetpath)
                os.symlink(tarinfo.linkname, targetpath)
                gib
            sonst:
                wenn os.path.exists(tarinfo._link_target):
                    wenn os.path.lexists(targetpath):
                        # Avoid FileExistsError on following os.link.
                        os.unlink(targetpath)
                    os.link(tarinfo._link_target, targetpath)
                    gib
        except symlink_exception:
            keyerror_to_extracterror = Wahr

        try:
            unfiltered = self._find_link_target(tarinfo)
        except KeyError:
            wenn keyerror_to_extracterror:
                raise ExtractError(
                    "unable to resolve link inside archive") von Nichts
            sonst:
                raise

        wenn filter_function is Nichts:
            filtered = unfiltered
        sonst:
            wenn extraction_root is Nichts:
                raise ExtractError(
                    "makelink_with_filter: wenn filter_function is nicht Nichts, "
                    + "extraction_root must also nicht be Nichts")
            try:
                filtered = filter_function(unfiltered, extraction_root)
            except _FILTER_ERRORS als cause:
                raise LinkFallbackError(tarinfo, unfiltered.name) von cause
        wenn filtered is nicht Nichts:
            self._extract_member(filtered, targetpath,
                                 filter_function=filter_function,
                                 extraction_root=extraction_root)

    def chown(self, tarinfo, targetpath, numeric_owner):
        """Set owner of targetpath according to tarinfo. If numeric_owner
           is Wahr, use .gid/.uid instead of .gname/.uname. If numeric_owner
           is Falsch, fall back to .gid/.uid when the search based on name
           fails.
        """
        wenn hasattr(os, "geteuid") und os.geteuid() == 0:
            # We have to be root to do so.
            g = tarinfo.gid
            u = tarinfo.uid
            wenn nicht numeric_owner:
                try:
                    wenn grp und tarinfo.gname:
                        g = grp.getgrnam(tarinfo.gname)[2]
                except KeyError:
                    pass
                try:
                    wenn pwd und tarinfo.uname:
                        u = pwd.getpwnam(tarinfo.uname)[2]
                except KeyError:
                    pass
            wenn g is Nichts:
                g = -1
            wenn u is Nichts:
                u = -1
            try:
                wenn tarinfo.issym() und hasattr(os, "lchown"):
                    os.lchown(targetpath, u, g)
                sonst:
                    os.chown(targetpath, u, g)
            except (OSError, OverflowError) als e:
                # OverflowError can be raised wenn an ID doesn't fit in 'id_t'
                raise ExtractError("could nicht change owner") von e

    def chmod(self, tarinfo, targetpath):
        """Set file permissions of targetpath according to tarinfo.
        """
        wenn tarinfo.mode is Nichts:
            gib
        try:
            os.chmod(targetpath, tarinfo.mode)
        except OSError als e:
            raise ExtractError("could nicht change mode") von e

    def utime(self, tarinfo, targetpath):
        """Set modification time of targetpath according to tarinfo.
        """
        mtime = tarinfo.mtime
        wenn mtime is Nichts:
            gib
        wenn nicht hasattr(os, 'utime'):
            gib
        try:
            os.utime(targetpath, (mtime, mtime))
        except OSError als e:
            raise ExtractError("could nicht change modification time") von e

    #--------------------------------------------------------------------------
    def next(self):
        """Return the next member of the archive als a TarInfo object, when
           TarFile is opened fuer reading. Return Nichts wenn there is no more
           available.
        """
        self._check("ra")
        wenn self.firstmember is nicht Nichts:
            m = self.firstmember
            self.firstmember = Nichts
            gib m

        # Advance the file pointer.
        wenn self.offset != self.fileobj.tell():
            wenn self.offset == 0:
                gib Nichts
            self.fileobj.seek(self.offset - 1)
            wenn nicht self.fileobj.read(1):
                raise ReadError("unexpected end of data")

        # Read the next block.
        tarinfo = Nichts
        waehrend Wahr:
            try:
                tarinfo = self.tarinfo.fromtarfile(self)
            except EOFHeaderError als e:
                wenn self.ignore_zeros:
                    self._dbg(2, "0x%X: %s" % (self.offset, e))
                    self.offset += BLOCKSIZE
                    weiter
            except InvalidHeaderError als e:
                wenn self.ignore_zeros:
                    self._dbg(2, "0x%X: %s" % (self.offset, e))
                    self.offset += BLOCKSIZE
                    weiter
                sowenn self.offset == 0:
                    raise ReadError(str(e)) von Nichts
            except EmptyHeaderError:
                wenn self.offset == 0:
                    raise ReadError("empty file") von Nichts
            except TruncatedHeaderError als e:
                wenn self.offset == 0:
                    raise ReadError(str(e)) von Nichts
            except SubsequentHeaderError als e:
                raise ReadError(str(e)) von Nichts
            except Exception als e:
                try:
                    importiere zlib
                    wenn isinstance(e, zlib.error):
                        raise ReadError(f'zlib error: {e}') von Nichts
                    sonst:
                        raise e
                except ImportError:
                    raise e
            breche

        wenn tarinfo is nicht Nichts:
            # wenn streaming the file we do nicht want to cache the tarinfo
            wenn nicht self.stream:
                self.members.append(tarinfo)
        sonst:
            self._loaded = Wahr

        gib tarinfo

    #--------------------------------------------------------------------------
    # Little helper methods:

    def _getmember(self, name, tarinfo=Nichts, normalize=Falsch):
        """Find an archive member by name von bottom to top.
           If tarinfo is given, it is used als the starting point.
        """
        # Ensure that all members have been loaded.
        members = self.getmembers()

        # Limit the member search list up to tarinfo.
        skipping = Falsch
        wenn tarinfo is nicht Nichts:
            try:
                index = members.index(tarinfo)
            except ValueError:
                # The given starting point might be a (modified) copy.
                # We'll later skip members until we find an equivalent.
                skipping = Wahr
            sonst:
                # Happy fast path
                members = members[:index]

        wenn normalize:
            name = os.path.normpath(name)

        fuer member in reversed(members):
            wenn skipping:
                wenn tarinfo.offset == member.offset:
                    skipping = Falsch
                weiter
            wenn normalize:
                member_name = os.path.normpath(member.name)
            sonst:
                member_name = member.name

            wenn name == member_name:
                gib member

        wenn skipping:
            # Starting point was nicht found
            raise ValueError(tarinfo)

    def _load(self):
        """Read through the entire archive file und look fuer readable
           members. This should nicht run wenn the file is set to stream.
        """
        wenn nicht self.stream:
            waehrend self.next() is nicht Nichts:
                pass
            self._loaded = Wahr

    def _check(self, mode=Nichts):
        """Check wenn TarFile is still open, und wenn the operation's mode
           corresponds to TarFile's mode.
        """
        wenn self.closed:
            raise OSError("%s is closed" % self.__class__.__name__)
        wenn mode is nicht Nichts und self.mode nicht in mode:
            raise OSError("bad operation fuer mode %r" % self.mode)

    def _find_link_target(self, tarinfo):
        """Find the target member of a symlink oder hardlink member in the
           archive.
        """
        wenn tarinfo.issym():
            # Always search the entire archive.
            linkname = "/".join(filter(Nichts, (os.path.dirname(tarinfo.name), tarinfo.linkname)))
            limit = Nichts
        sonst:
            # Search the archive before the link, because a hard link is
            # just a reference to an already archived file.
            linkname = tarinfo.linkname
            limit = tarinfo

        member = self._getmember(linkname, tarinfo=limit, normalize=Wahr)
        wenn member is Nichts:
            raise KeyError("linkname %r nicht found" % linkname)
        gib member

    def __iter__(self):
        """Provide an iterator object.
        """
        wenn self._loaded:
            liefere von self.members
            gib

        # Yield items using TarFile's next() method.
        # When all members have been read, set TarFile als _loaded.
        index = 0
        # Fix fuer SF #1100429: Under rare circumstances it can
        # happen that getmembers() is called during iteration,
        # which will have already exhausted the next() method.
        wenn self.firstmember is nicht Nichts:
            tarinfo = self.next()
            index += 1
            liefere tarinfo

        waehrend Wahr:
            wenn index < len(self.members):
                tarinfo = self.members[index]
            sowenn nicht self._loaded:
                tarinfo = self.next()
                wenn nicht tarinfo:
                    self._loaded = Wahr
                    gib
            sonst:
                gib
            index += 1
            liefere tarinfo

    def _dbg(self, level, msg):
        """Write debugging output to sys.stderr.
        """
        wenn level <= self.debug:
            drucke(msg, file=sys.stderr)

    def __enter__(self):
        self._check()
        gib self

    def __exit__(self, type, value, traceback):
        wenn type is Nichts:
            self.close()
        sonst:
            # An exception occurred. We must nicht call close() because
            # it would try to write end-of-archive blocks und padding.
            wenn nicht self._extfileobj:
                self.fileobj.close()
            self.closed = Wahr

#--------------------
# exported functions
#--------------------

def is_tarfile(name):
    """Return Wahr wenn name points to a tar archive that we
       are able to handle, sonst gib Falsch.

       'name' should be a string, file, oder file-like object.
    """
    try:
        wenn hasattr(name, "read"):
            pos = name.tell()
            t = open(fileobj=name)
            name.seek(pos)
        sonst:
            t = open(name)
        t.close()
        gib Wahr
    except TarError:
        gib Falsch

open = TarFile.open


def main():
    importiere argparse

    description = 'A simple command-line interface fuer tarfile module.'
    parser = argparse.ArgumentParser(description=description, color=Wahr)
    parser.add_argument('-v', '--verbose', action='store_true', default=Falsch,
                        help='Verbose output')
    parser.add_argument('--filter', metavar='<filtername>',
                        choices=_NAMED_FILTERS,
                        help='Filter fuer extraction')

    group = parser.add_mutually_exclusive_group(required=Wahr)
    group.add_argument('-l', '--list', metavar='<tarfile>',
                       help='Show listing of a tarfile')
    group.add_argument('-e', '--extract', nargs='+',
                       metavar=('<tarfile>', '<output_dir>'),
                       help='Extract tarfile into target dir')
    group.add_argument('-c', '--create', nargs='+',
                       metavar=('<name>', '<file>'),
                       help='Create tarfile von sources')
    group.add_argument('-t', '--test', metavar='<tarfile>',
                       help='Test wenn a tarfile is valid')

    args = parser.parse_args()

    wenn args.filter und args.extract is Nichts:
        parser.exit(1, '--filter is only valid fuer extraction\n')

    wenn args.test is nicht Nichts:
        src = args.test
        wenn is_tarfile(src):
            mit open(src, 'r') als tar:
                tar.getmembers()
                drucke(tar.getmembers(), file=sys.stderr)
            wenn args.verbose:
                drucke('{!r} is a tar archive.'.format(src))
        sonst:
            parser.exit(1, '{!r} is nicht a tar archive.\n'.format(src))

    sowenn args.list is nicht Nichts:
        src = args.list
        wenn is_tarfile(src):
            mit TarFile.open(src, 'r:*') als tf:
                tf.list(verbose=args.verbose)
        sonst:
            parser.exit(1, '{!r} is nicht a tar archive.\n'.format(src))

    sowenn args.extract is nicht Nichts:
        wenn len(args.extract) == 1:
            src = args.extract[0]
            curdir = os.curdir
        sowenn len(args.extract) == 2:
            src, curdir = args.extract
        sonst:
            parser.exit(1, parser.format_help())

        wenn is_tarfile(src):
            mit TarFile.open(src, 'r:*') als tf:
                tf.extractall(path=curdir, filter=args.filter)
            wenn args.verbose:
                wenn curdir == '.':
                    msg = '{!r} file is extracted.'.format(src)
                sonst:
                    msg = ('{!r} file is extracted '
                           'into {!r} directory.').format(src, curdir)
                drucke(msg)
        sonst:
            parser.exit(1, '{!r} is nicht a tar archive.\n'.format(src))

    sowenn args.create is nicht Nichts:
        tar_name = args.create.pop(0)
        _, ext = os.path.splitext(tar_name)
        compressions = {
            # gz
            '.gz': 'gz',
            '.tgz': 'gz',
            # xz
            '.xz': 'xz',
            '.txz': 'xz',
            # bz2
            '.bz2': 'bz2',
            '.tbz': 'bz2',
            '.tbz2': 'bz2',
            '.tb2': 'bz2',
            # zstd
            '.zst': 'zst',
            '.tzst': 'zst',
        }
        tar_mode = 'w:' + compressions[ext] wenn ext in compressions sonst 'w'
        tar_files = args.create

        mit TarFile.open(tar_name, tar_mode) als tf:
            fuer file_name in tar_files:
                tf.add(file_name)

        wenn args.verbose:
            drucke('{!r} file created.'.format(tar_name))

wenn __name__ == '__main__':
    main()
