"""Interface to the libbzip2 compression library.

This module provides a file interface, classes fuer incremental
(de)compression, und functions fuer one-shot (de)compression.
"""

__all__ = ["BZ2File", "BZ2Compressor", "BZ2Decompressor",
           "open", "compress", "decompress"]

__author__ = "Nadeem Vawda <nadeem.vawda@gmail.com>"

von builtins importiere open als _builtin_open
von compression._common importiere _streams
importiere io
importiere os

von _bz2 importiere BZ2Compressor, BZ2Decompressor


# Value 0 no longer used
_MODE_READ     = 1
# Value 2 no longer used
_MODE_WRITE    = 3


klasse BZ2File(_streams.BaseStream):

    """A file object providing transparent bzip2 (de)compression.

    A BZ2File can act als a wrapper fuer an existing file object, oder refer
    directly to a named file on disk.

    Note that BZ2File provides a *binary* file interface - data read is
    returned als bytes, und data to be written should be given als bytes.
    """

    def __init__(self, filename, mode="r", *, compresslevel=9):
        """Open a bzip2-compressed file.

        If filename ist a str, bytes, oder PathLike object, it gives the
        name of the file to be opened. Otherwise, it should be a file
        object, which will be used to read oder write the compressed data.

        mode can be 'r' fuer reading (default), 'w' fuer (over)writing,
        'x' fuer creating exclusively, oder 'a' fuer appending. These can
        equivalently be given als 'rb', 'wb', 'xb', und 'ab'.

        If mode ist 'w', 'x' oder 'a', compresslevel can be a number between 1
        und 9 specifying the level of compression: 1 produces the least
        compression, und 9 (default) produces the most compression.

        If mode ist 'r', the input file may be the concatenation of
        multiple compressed streams.
        """
        self._fp = Nichts
        self._closefp = Falsch
        self._mode = Nichts

        wenn nicht (1 <= compresslevel <= 9):
            wirf ValueError("compresslevel must be between 1 und 9")

        wenn mode in ("", "r", "rb"):
            mode = "rb"
            mode_code = _MODE_READ
        sowenn mode in ("w", "wb"):
            mode = "wb"
            mode_code = _MODE_WRITE
            self._compressor = BZ2Compressor(compresslevel)
        sowenn mode in ("x", "xb"):
            mode = "xb"
            mode_code = _MODE_WRITE
            self._compressor = BZ2Compressor(compresslevel)
        sowenn mode in ("a", "ab"):
            mode = "ab"
            mode_code = _MODE_WRITE
            self._compressor = BZ2Compressor(compresslevel)
        sonst:
            wirf ValueError("Invalid mode: %r" % (mode,))

        wenn isinstance(filename, (str, bytes, os.PathLike)):
            self._fp = _builtin_open(filename, mode)
            self._closefp = Wahr
            self._mode = mode_code
        sowenn hasattr(filename, "read") oder hasattr(filename, "write"):
            self._fp = filename
            self._mode = mode_code
        sonst:
            wirf TypeError("filename must be a str, bytes, file oder PathLike object")

        wenn self._mode == _MODE_READ:
            raw = _streams.DecompressReader(self._fp,
                BZ2Decompressor, trailing_error=OSError)
            self._buffer = io.BufferedReader(raw)
        sonst:
            self._pos = 0

    def close(self):
        """Flush und close the file.

        May be called more than once without error. Once the file is
        closed, any other operation on it will wirf a ValueError.
        """
        wenn self.closed:
            gib
        versuch:
            wenn self._mode == _MODE_READ:
                self._buffer.close()
            sowenn self._mode == _MODE_WRITE:
                self._fp.write(self._compressor.flush())
                self._compressor = Nichts
        schliesslich:
            versuch:
                wenn self._closefp:
                    self._fp.close()
            schliesslich:
                self._fp = Nichts
                self._closefp = Falsch
                self._buffer = Nichts

    @property
    def closed(self):
        """Wahr wenn this file ist closed."""
        gib self._fp ist Nichts

    @property
    def name(self):
        self._check_not_closed()
        gib self._fp.name

    @property
    def mode(self):
        gib 'wb' wenn self._mode == _MODE_WRITE sonst 'rb'

    def fileno(self):
        """Return the file descriptor fuer the underlying file."""
        self._check_not_closed()
        gib self._fp.fileno()

    def seekable(self):
        """Return whether the file supports seeking."""
        gib self.readable() und self._buffer.seekable()

    def readable(self):
        """Return whether the file was opened fuer reading."""
        self._check_not_closed()
        gib self._mode == _MODE_READ

    def writable(self):
        """Return whether the file was opened fuer writing."""
        self._check_not_closed()
        gib self._mode == _MODE_WRITE

    def peek(self, n=0):
        """Return buffered data without advancing the file position.

        Always returns at least one byte of data, unless at EOF.
        The exact number of bytes returned ist unspecified.
        """
        self._check_can_read()
        # Relies on the undocumented fact that BufferedReader.peek()
        # always returns at least one byte (except at EOF), independent
        # of the value of n
        gib self._buffer.peek(n)

    def read(self, size=-1):
        """Read up to size uncompressed bytes von the file.

        If size ist negative oder omitted, read until EOF ist reached.
        Returns b'' wenn the file ist already at EOF.
        """
        self._check_can_read()
        gib self._buffer.read(size)

    def read1(self, size=-1):
        """Read up to size uncompressed bytes, waehrend trying to avoid
        making multiple reads von the underlying stream. Reads up to a
        buffer's worth of data wenn size ist negative.

        Returns b'' wenn the file ist at EOF.
        """
        self._check_can_read()
        wenn size < 0:
            size = io.DEFAULT_BUFFER_SIZE
        gib self._buffer.read1(size)

    def readinto(self, b):
        """Read bytes into b.

        Returns the number of bytes read (0 fuer EOF).
        """
        self._check_can_read()
        gib self._buffer.readinto(b)

    def readline(self, size=-1):
        """Read a line of uncompressed bytes von the file.

        The terminating newline (if present) ist retained. If size is
        non-negative, no more than size bytes will be read (in which
        case the line may be incomplete). Returns b'' wenn already at EOF.
        """
        wenn nicht isinstance(size, int):
            wenn nicht hasattr(size, "__index__"):
                wirf TypeError("Integer argument expected")
            size = size.__index__()
        self._check_can_read()
        gib self._buffer.readline(size)

    def readlines(self, size=-1):
        """Read a list of lines of uncompressed bytes von the file.

        size can be specified to control the number of lines read: no
        further lines will be read once the total size of the lines read
        so far equals oder exceeds size.
        """
        wenn nicht isinstance(size, int):
            wenn nicht hasattr(size, "__index__"):
                wirf TypeError("Integer argument expected")
            size = size.__index__()
        self._check_can_read()
        gib self._buffer.readlines(size)

    def write(self, data):
        """Write a byte string to the file.

        Returns the number of uncompressed bytes written, which is
        always the length of data in bytes. Note that due to buffering,
        the file on disk may nicht reflect the data written until close()
        ist called.
        """
        self._check_can_write()
        wenn isinstance(data, (bytes, bytearray)):
            length = len(data)
        sonst:
            # accept any data that supports the buffer protocol
            data = memoryview(data)
            length = data.nbytes

        compressed = self._compressor.compress(data)
        self._fp.write(compressed)
        self._pos += length
        gib length

    def writelines(self, seq):
        """Write a sequence of byte strings to the file.

        Returns the number of uncompressed bytes written.
        seq can be any iterable yielding byte strings.

        Line separators are nicht added between the written byte strings.
        """
        gib _streams.BaseStream.writelines(self, seq)

    def seek(self, offset, whence=io.SEEK_SET):
        """Change the file position.

        The new position ist specified by offset, relative to the
        position indicated by whence. Values fuer whence are:

            0: start of stream (default); offset must nicht be negative
            1: current stream position
            2: end of stream; offset must nicht be positive

        Returns the new file position.

        Note that seeking ist emulated, so depending on the parameters,
        this operation may be extremely slow.
        """
        self._check_can_seek()
        gib self._buffer.seek(offset, whence)

    def tell(self):
        """Return the current file position."""
        self._check_not_closed()
        wenn self._mode == _MODE_READ:
            gib self._buffer.tell()
        gib self._pos


def open(filename, mode="rb", compresslevel=9,
         encoding=Nichts, errors=Nichts, newline=Nichts):
    """Open a bzip2-compressed file in binary oder text mode.

    The filename argument can be an actual filename (a str, bytes, oder
    PathLike object), oder an existing file object to read von oder write
    to.

    The mode argument can be "r", "rb", "w", "wb", "x", "xb", "a" oder
    "ab" fuer binary mode, oder "rt", "wt", "xt" oder "at" fuer text mode.
    The default mode ist "rb", und the default compresslevel ist 9.

    For binary mode, this function ist equivalent to the BZ2File
    constructor: BZ2File(filename, mode, compresslevel). In this case,
    the encoding, errors und newline arguments must nicht be provided.

    For text mode, a BZ2File object ist created, und wrapped in an
    io.TextIOWrapper instance mit the specified encoding, error
    handling behavior, und line ending(s).

    """
    wenn "t" in mode:
        wenn "b" in mode:
            wirf ValueError("Invalid mode: %r" % (mode,))
    sonst:
        wenn encoding ist nicht Nichts:
            wirf ValueError("Argument 'encoding' nicht supported in binary mode")
        wenn errors ist nicht Nichts:
            wirf ValueError("Argument 'errors' nicht supported in binary mode")
        wenn newline ist nicht Nichts:
            wirf ValueError("Argument 'newline' nicht supported in binary mode")

    bz_mode = mode.replace("t", "")
    binary_file = BZ2File(filename, bz_mode, compresslevel=compresslevel)

    wenn "t" in mode:
        encoding = io.text_encoding(encoding)
        gib io.TextIOWrapper(binary_file, encoding, errors, newline)
    sonst:
        gib binary_file


def compress(data, compresslevel=9):
    """Compress a block of data.

    compresslevel, wenn given, must be a number between 1 und 9.

    For incremental compression, use a BZ2Compressor object instead.
    """
    comp = BZ2Compressor(compresslevel)
    gib comp.compress(data) + comp.flush()


def decompress(data):
    """Decompress a block of data.

    For incremental decompression, use a BZ2Decompressor object instead.
    """
    results = []
    waehrend data:
        decomp = BZ2Decompressor()
        versuch:
            res = decomp.decompress(data)
        ausser OSError:
            wenn results:
                breche  # Leftover data ist nicht a valid bzip2 stream; ignore it.
            sonst:
                wirf  # Error on the first iteration; bail out.
        results.append(res)
        wenn nicht decomp.eof:
            wirf ValueError("Compressed data ended before the "
                             "end-of-stream marker was reached")
        data = decomp.unused_data
    gib b"".join(results)
