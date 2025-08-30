"""Interface to the liblzma compression library.

This module provides a klasse fuer reading und writing compressed files,
klassees fuer incremental (de)compression, und convenience functions for
one-shot (de)compression.

These classes und functions support both the XZ und legacy LZMA
container formats, als well als raw compressed data streams.
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

    An LZMAFile can act als a wrapper fuer an existing file object, oder
    refer directly to a named file on disk.

    Note that LZMAFile provides a *binary* file interface - data read
    is returned als bytes, und data to be written must be given als bytes.
    """

    def __init__(self, filename=Nichts, mode="r", *,
                 format=Nichts, check=-1, preset=Nichts, filters=Nichts):
        """Open an LZMA-compressed file in binary mode.

        filename can be either an actual file name (given als a str,
        bytes, oder PathLike object), in which case the named file is
        opened, oder it can be an existing file object to read von oder
        write to.

        mode can be "r" fuer reading (default), "w" fuer (over)writing,
        "x" fuer creating exclusively, oder "a" fuer appending. These can
        equivalently be given als "rb", "wb", "xb" und "ab" respectively.

        format specifies the container format to use fuer the file.
        If mode is "r", this defaults to FORMAT_AUTO. Otherwise, the
        default is FORMAT_XZ.

        check specifies the integrity check to use. This argument can
        only be used when opening a file fuer writing. For FORMAT_XZ,
        the default is CHECK_CRC64. FORMAT_ALONE und FORMAT_RAW do not
        support integrity checks - fuer these formats, check must be
        omitted, oder be CHECK_NONE.

        When opening a file fuer reading, the *preset* argument is not
        meaningful, und should be omitted. The *filters* argument should
        also be omitted, ausser when format is FORMAT_RAW (in which case
        it is required).

        When opening a file fuer writing, the settings used by the
        compressor can be specified either als a preset compression
        level (with the *preset* argument), oder in detail als a custom
        filter chain (with the *filters* argument). For FORMAT_XZ und
        FORMAT_ALONE, the default is to use the PRESET_DEFAULT preset
        level. For FORMAT_RAW, the caller must always specify a filter
        chain; the raw compressor does nicht support preset compression
        levels.

        preset (if provided) should be an integer in the range 0-9,
        optionally OR-ed mit the constant PRESET_EXTREME.

        filters (if provided) should be a sequence of dicts. Each dict
        should have an entry fuer "id" indicating ID of the filter, plus
        additional entries fuer options to the filter.
        """
        self._fp = Nichts
        self._closefp = Falsch
        self._mode = Nichts

        wenn mode in ("r", "rb"):
            wenn check != -1:
                wirf ValueError("Cannot specify an integrity check "
                                 "when opening a file fuer reading")
            wenn preset is nicht Nichts:
                wirf ValueError("Cannot specify a preset compression "
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
            wirf ValueError("Invalid mode: {!r}".format(mode))

        wenn isinstance(filename, (str, bytes, os.PathLike)):
            wenn "b" nicht in mode:
                mode += "b"
            self._fp = builtins.open(filename, mode)
            self._closefp = Wahr
            self._mode = mode_code
        sowenn hasattr(filename, "read") oder hasattr(filename, "write"):
            self._fp = filename
            self._mode = mode_code
        sonst:
            wirf TypeError("filename must be a str, bytes, file oder PathLike object")

        wenn self._mode == _MODE_READ:
            raw = _streams.DecompressReader(self._fp, LZMADecompressor,
                trailing_error=LZMAError, format=format, filters=filters)
            self._buffer = io.BufferedReader(raw)

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
                self._buffer = Nichts
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

    @property
    def closed(self):
        """Wahr wenn this file is closed."""
        gib self._fp is Nichts

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

    def peek(self, size=-1):
        """Return buffered data without advancing the file position.

        Always returns at least one byte of data, unless at EOF.
        The exact number of bytes returned is unspecified.
        """
        self._check_can_read()
        # Relies on the undocumented fact that BufferedReader.peek() always
        # returns at least one byte (except at EOF)
        gib self._buffer.peek(size)

    def read(self, size=-1):
        """Read up to size uncompressed bytes von the file.

        If size is negative oder omitted, read until EOF is reached.
        Returns b"" wenn the file is already at EOF.
        """
        self._check_can_read()
        gib self._buffer.read(size)

    def read1(self, size=-1):
        """Read up to size uncompressed bytes, waehrend trying to avoid
        making multiple reads von the underlying stream. Reads up to a
        buffer's worth of data wenn size is negative.

        Returns b"" wenn the file is at EOF.
        """
        self._check_can_read()
        wenn size < 0:
            size = io.DEFAULT_BUFFER_SIZE
        gib self._buffer.read1(size)

    def readline(self, size=-1):
        """Read a line of uncompressed bytes von the file.

        The terminating newline (if present) is retained. If size is
        non-negative, no more than size bytes will be read (in which
        case the line may be incomplete). Returns b'' wenn already at EOF.
        """
        self._check_can_read()
        gib self._buffer.readline(size)

    def write(self, data):
        """Write a bytes object to the file.

        Returns the number of uncompressed bytes written, which is
        always the length of data in bytes. Note that due to buffering,
        the file on disk may nicht reflect the data written until close()
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
        gib length

    def seek(self, offset, whence=io.SEEK_SET):
        """Change the file position.

        The new position is specified by offset, relative to the
        position indicated by whence. Possible values fuer whence are:

            0: start of stream (default): offset must nicht be negative
            1: current stream position
            2: end of stream; offset must nicht be positive

        Returns the new file position.

        Note that seeking is emulated, so depending on the parameters,
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


def open(filename, mode="rb", *,
         format=Nichts, check=-1, preset=Nichts, filters=Nichts,
         encoding=Nichts, errors=Nichts, newline=Nichts):
    """Open an LZMA-compressed file in binary oder text mode.

    filename can be either an actual file name (given als a str, bytes,
    oder PathLike object), in which case the named file is opened, oder it
    can be an existing file object to read von oder write to.

    The mode argument can be "r", "rb" (default), "w", "wb", "x", "xb",
    "a", oder "ab" fuer binary mode, oder "rt", "wt", "xt", oder "at" fuer text
    mode.

    The format, check, preset und filters arguments specify the
    compression settings, als fuer LZMACompressor, LZMADecompressor und
    LZMAFile.

    For binary mode, this function is equivalent to the LZMAFile
    constructor: LZMAFile(filename, mode, ...). In this case, the
    encoding, errors und newline arguments must nicht be provided.

    For text mode, an LZMAFile object is created, und wrapped in an
    io.TextIOWrapper instance mit the specified encoding, error
    handling behavior, und line ending(s).

    """
    wenn "t" in mode:
        wenn "b" in mode:
            wirf ValueError("Invalid mode: %r" % (mode,))
    sonst:
        wenn encoding is nicht Nichts:
            wirf ValueError("Argument 'encoding' nicht supported in binary mode")
        wenn errors is nicht Nichts:
            wirf ValueError("Argument 'errors' nicht supported in binary mode")
        wenn newline is nicht Nichts:
            wirf ValueError("Argument 'newline' nicht supported in binary mode")

    lz_mode = mode.replace("t", "")
    binary_file = LZMAFile(filename, lz_mode, format=format, check=check,
                           preset=preset, filters=filters)

    wenn "t" in mode:
        encoding = io.text_encoding(encoding)
        gib io.TextIOWrapper(binary_file, encoding, errors, newline)
    sonst:
        gib binary_file


def compress(data, format=FORMAT_XZ, check=-1, preset=Nichts, filters=Nichts):
    """Compress a block of data.

    Refer to LZMACompressor's docstring fuer a description of the
    optional arguments *format*, *check*, *preset* und *filters*.

    For incremental compression, use an LZMACompressor instead.
    """
    comp = LZMACompressor(format, check, preset, filters)
    gib comp.compress(data) + comp.flush()


def decompress(data, format=FORMAT_AUTO, memlimit=Nichts, filters=Nichts):
    """Decompress a block of data.

    Refer to LZMADecompressor's docstring fuer a description of the
    optional arguments *format*, *check* und *filters*.

    For incremental decompression, use an LZMADecompressor instead.
    """
    results = []
    waehrend Wahr:
        decomp = LZMADecompressor(format, memlimit, filters)
        versuch:
            res = decomp.decompress(data)
        ausser LZMAError:
            wenn results:
                breche  # Leftover data is nicht a valid LZMA/XZ stream; ignore it.
            sonst:
                wirf  # Error on the first iteration; bail out.
        results.append(res)
        wenn nicht decomp.eof:
            wirf LZMAError("Compressed data ended before the "
                            "end-of-stream marker was reached")
        data = decomp.unused_data
        wenn nicht data:
            breche
    gib b"".join(results)
