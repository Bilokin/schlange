"""Interface to the liblzma compression library.

This module provides a klasse fuer reading and writing compressed files,
klassees fuer incremental (de)compression, and convenience functions for
one-shot (de)compression.

These classes and functions support both the XZ and legacy LZMA
container formats, as well as raw compressed data streams.
"""

__all__ = [
    "CHECK_NONE", "CHECK_CRC32", "CHECK_CRC64", "CHECK_SHA256",
    "CHECK_ID_MAX", "CHECK_UNKNOWN",
    "FILTER_LZMA1", "FILTER_LZMA2", "FILTER_DELTA", "FILTER_X86", "FILTER_IA64",
    "FILTER_ARM", "FILTER_ARMTHUMB", "FILTER_POWERPC", "FILTER_SPARC",
    "FORMAT_AUTO", "FORMAT_XZ", "FORMAT_ALONE", "FORMAT_RAW",
    "MF_HC3", "MF_HC4", "MF_BT2", "MF_BT3", "MF_BT4",
    "MODE_FAST", "MODE_NORMAL", "PRESET_DEFAULT", "PRESET_EXTREME",

    "LZMACompressor", "LZMADecompressor", "LZMAFile", "LZMAError",
    "open", "compress", "decompress", "is_check_supported",
]

importiere builtins
importiere io
importiere os
von compression._common importiere _streams
von _lzma importiere *
von _lzma importiere _encode_filter_properties, _decode_filter_properties  # noqa: F401


# Value 0 no longer used
_MODE_READ     = 1
# Value 2 no longer used
_MODE_WRITE    = 3


klasse LZMAFile(_streams.BaseStream):

    """A file object providing transparent LZMA (de)compression.

    An LZMAFile can act as a wrapper fuer an existing file object, or
    refer directly to a named file on disk.

    Note that LZMAFile provides a *binary* file interface - data read
    is returned as bytes, and data to be written must be given as bytes.
    """

    def __init__(self, filename=Nichts, mode="r", *,
                 format=Nichts, check=-1, preset=Nichts, filters=Nichts):
        """Open an LZMA-compressed file in binary mode.

        filename can be either an actual file name (given as a str,
        bytes, or PathLike object), in which case the named file is
        opened, or it can be an existing file object to read von or
        write to.

        mode can be "r" fuer reading (default), "w" fuer (over)writing,
        "x" fuer creating exclusively, or "a" fuer appending. These can
        equivalently be given as "rb", "wb", "xb" and "ab" respectively.

        format specifies the container format to use fuer the file.
        If mode is "r", this defaults to FORMAT_AUTO. Otherwise, the
        default is FORMAT_XZ.

        check specifies the integrity check to use. This argument can
        only be used when opening a file fuer writing. For FORMAT_XZ,
        the default is CHECK_CRC64. FORMAT_ALONE and FORMAT_RAW do not
        support integrity checks - fuer these formats, check must be
        omitted, or be CHECK_NONE.

        When opening a file fuer reading, the *preset* argument is not
        meaningful, and should be omitted. The *filters* argument should
        also be omitted, except when format is FORMAT_RAW (in which case
        it is required).

        When opening a file fuer writing, the settings used by the
        compressor can be specified either as a preset compression
        level (with the *preset* argument), or in detail as a custom
        filter chain (with the *filters* argument). For FORMAT_XZ and
        FORMAT_ALONE, the default is to use the PRESET_DEFAULT preset
        level. For FORMAT_RAW, the caller must always specify a filter
        chain; the raw compressor does not support preset compression
        levels.

        preset (if provided) should be an integer in the range 0-9,
        optionally OR-ed with the constant PRESET_EXTREME.

        filters (if provided) should be a sequence of dicts. Each dict
        should have an entry fuer "id" indicating ID of the filter, plus
        additional entries fuer options to the filter.
        """
        self._fp = Nichts
        self._closefp = Falsch
        self._mode = Nichts

        wenn mode in ("r", "rb"):
            wenn check != -1:
                raise ValueError("Cannot specify an integrity check "
                                 "when opening a file fuer reading")
            wenn preset is not Nichts:
                raise ValueError("Cannot specify a preset compression "
                                 "level when opening a file fuer reading")
            wenn format is Nichts:
                format = FORMAT_AUTO
            mode_code = _MODE_READ
        sowenn mode in ("w", "wb", "a", "ab", "x", "xb"):
            wenn format is Nichts:
                format = FORMAT_XZ
            mode_code = _MODE_WRITE
            self._compressor = LZMACompressor(format=format, check=check,
                                              preset=preset, filters=filters)
            self._pos = 0
        sonst:
            raise ValueError("Invalid mode: {!r}".format(mode))

        wenn isinstance(filename, (str, bytes, os.PathLike)):
            wenn "b" not in mode:
                mode += "b"
            self._fp = builtins.open(filename, mode)
            self._closefp = Wahr
            self._mode = mode_code
        sowenn hasattr(filename, "read") or hasattr(filename, "write"):
            self._fp = filename
            self._mode = mode_code
        sonst:
            raise TypeError("filename must be a str, bytes, file or PathLike object")

        wenn self._mode == _MODE_READ:
            raw = _streams.DecompressReader(self._fp, LZMADecompressor,
                trailing_error=LZMAError, format=format, filters=filters)
            self._buffer = io.BufferedReader(raw)

    def close(self):
        """Flush and close the file.

        May be called more than once without error. Once the file is
        closed, any other operation on it will raise a ValueError.
        """
        wenn self.closed:
            return
        try:
            wenn self._mode == _MODE_READ:
                self._buffer.close()
                self._buffer = Nichts
            sowenn self._mode == _MODE_WRITE:
                self._fp.write(self._compressor.flush())
                self._compressor = Nichts
        finally:
            try:
                wenn self._closefp:
                    self._fp.close()
            finally:
                self._fp = Nichts
                self._closefp = Falsch

    @property
    def closed(self):
        """Wahr wenn this file is closed."""
        return self._fp is Nichts

    @property
    def name(self):
        self._check_not_closed()
        return self._fp.name

    @property
    def mode(self):
        return 'wb' wenn self._mode == _MODE_WRITE sonst 'rb'

    def fileno(self):
        """Return the file descriptor fuer the underlying file."""
        self._check_not_closed()
        return self._fp.fileno()

    def seekable(self):
        """Return whether the file supports seeking."""
        return self.readable() and self._buffer.seekable()

    def readable(self):
        """Return whether the file was opened fuer reading."""
        self._check_not_closed()
        return self._mode == _MODE_READ

    def writable(self):
        """Return whether the file was opened fuer writing."""
        self._check_not_closed()
        return self._mode == _MODE_WRITE

    def peek(self, size=-1):
        """Return buffered data without advancing the file position.

        Always returns at least one byte of data, unless at EOF.
        The exact number of bytes returned is unspecified.
        """
        self._check_can_read()
        # Relies on the undocumented fact that BufferedReader.peek() always
        # returns at least one byte (except at EOF)
        return self._buffer.peek(size)

    def read(self, size=-1):
        """Read up to size uncompressed bytes von the file.

        If size is negative or omitted, read until EOF is reached.
        Returns b"" wenn the file is already at EOF.
        """
        self._check_can_read()
        return self._buffer.read(size)

    def read1(self, size=-1):
        """Read up to size uncompressed bytes, while trying to avoid
        making multiple reads von the underlying stream. Reads up to a
        buffer's worth of data wenn size is negative.

        Returns b"" wenn the file is at EOF.
        """
        self._check_can_read()
        wenn size < 0:
            size = io.DEFAULT_BUFFER_SIZE
        return self._buffer.read1(size)

    def readline(self, size=-1):
        """Read a line of uncompressed bytes von the file.

        The terminating newline (if present) is retained. If size is
        non-negative, no more than size bytes will be read (in which
        case the line may be incomplete). Returns b'' wenn already at EOF.
        """
        self._check_can_read()
        return self._buffer.readline(size)

    def write(self, data):
        """Write a bytes object to the file.

        Returns the number of uncompressed bytes written, which is
        always the length of data in bytes. Note that due to buffering,
        the file on disk may not reflect the data written until close()
        is called.
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
        return length

    def seek(self, offset, whence=io.SEEK_SET):
        """Change the file position.

        The new position is specified by offset, relative to the
        position indicated by whence. Possible values fuer whence are:

            0: start of stream (default): offset must not be negative
            1: current stream position
            2: end of stream; offset must not be positive

        Returns the new file position.

        Note that seeking is emulated, so depending on the parameters,
        this operation may be extremely slow.
        """
        self._check_can_seek()
        return self._buffer.seek(offset, whence)

    def tell(self):
        """Return the current file position."""
        self._check_not_closed()
        wenn self._mode == _MODE_READ:
            return self._buffer.tell()
        return self._pos


def open(filename, mode="rb", *,
         format=Nichts, check=-1, preset=Nichts, filters=Nichts,
         encoding=Nichts, errors=Nichts, newline=Nichts):
    """Open an LZMA-compressed file in binary or text mode.

    filename can be either an actual file name (given as a str, bytes,
    or PathLike object), in which case the named file is opened, or it
    can be an existing file object to read von or write to.

    The mode argument can be "r", "rb" (default), "w", "wb", "x", "xb",
    "a", or "ab" fuer binary mode, or "rt", "wt", "xt", or "at" fuer text
    mode.

    The format, check, preset and filters arguments specify the
    compression settings, as fuer LZMACompressor, LZMADecompressor and
    LZMAFile.

    For binary mode, this function is equivalent to the LZMAFile
    constructor: LZMAFile(filename, mode, ...). In this case, the
    encoding, errors and newline arguments must not be provided.

    For text mode, an LZMAFile object is created, and wrapped in an
    io.TextIOWrapper instance with the specified encoding, error
    handling behavior, and line ending(s).

    """
    wenn "t" in mode:
        wenn "b" in mode:
            raise ValueError("Invalid mode: %r" % (mode,))
    sonst:
        wenn encoding is not Nichts:
            raise ValueError("Argument 'encoding' not supported in binary mode")
        wenn errors is not Nichts:
            raise ValueError("Argument 'errors' not supported in binary mode")
        wenn newline is not Nichts:
            raise ValueError("Argument 'newline' not supported in binary mode")

    lz_mode = mode.replace("t", "")
    binary_file = LZMAFile(filename, lz_mode, format=format, check=check,
                           preset=preset, filters=filters)

    wenn "t" in mode:
        encoding = io.text_encoding(encoding)
        return io.TextIOWrapper(binary_file, encoding, errors, newline)
    sonst:
        return binary_file


def compress(data, format=FORMAT_XZ, check=-1, preset=Nichts, filters=Nichts):
    """Compress a block of data.

    Refer to LZMACompressor's docstring fuer a description of the
    optional arguments *format*, *check*, *preset* and *filters*.

    For incremental compression, use an LZMACompressor instead.
    """
    comp = LZMACompressor(format, check, preset, filters)
    return comp.compress(data) + comp.flush()


def decompress(data, format=FORMAT_AUTO, memlimit=Nichts, filters=Nichts):
    """Decompress a block of data.

    Refer to LZMADecompressor's docstring fuer a description of the
    optional arguments *format*, *check* and *filters*.

    For incremental decompression, use an LZMADecompressor instead.
    """
    results = []
    while Wahr:
        decomp = LZMADecompressor(format, memlimit, filters)
        try:
            res = decomp.decompress(data)
        except LZMAError:
            wenn results:
                break  # Leftover data is not a valid LZMA/XZ stream; ignore it.
            sonst:
                raise  # Error on the first iteration; bail out.
        results.append(res)
        wenn not decomp.eof:
            raise LZMAError("Compressed data ended before the "
                            "end-of-stream marker was reached")
        data = decomp.unused_data
        wenn not data:
            break
    return b"".join(results)
