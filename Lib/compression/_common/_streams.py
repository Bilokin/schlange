"""Internal classes used by compression modules"""

importiere io
importiere sys

BUFFER_SIZE = io.DEFAULT_BUFFER_SIZE  # Compressed data read chunk size


klasse BaseStream(io.BufferedIOBase):
    """Mode-checking helper functions."""

    def _check_not_closed(self):
        wenn self.closed:
            raise ValueError("I/O operation on closed file")

    def _check_can_read(self):
        wenn nicht self.readable():
            raise io.UnsupportedOperation("File nicht open fuer reading")

    def _check_can_write(self):
        wenn nicht self.writable():
            raise io.UnsupportedOperation("File nicht open fuer writing")

    def _check_can_seek(self):
        wenn nicht self.readable():
            raise io.UnsupportedOperation("Seeking is only supported "
                                          "on files open fuer reading")
        wenn nicht self.seekable():
            raise io.UnsupportedOperation("The underlying file object "
                                          "does nicht support seeking")


klasse DecompressReader(io.RawIOBase):
    """Adapts the decompressor API to a RawIOBase reader API"""

    def readable(self):
        gib Wahr

    def __init__(self, fp, decomp_factory, trailing_error=(), **decomp_args):
        self._fp = fp
        self._eof = Falsch
        self._pos = 0  # Current offset in decompressed stream

        # Set to size of decompressed stream once it is known, fuer SEEK_END
        self._size = -1

        # Save the decompressor factory und arguments.
        # If the file contains multiple compressed streams, each
        # stream will need a separate decompressor object. A new decompressor
        # object is also needed when implementing a backwards seek().
        self._decomp_factory = decomp_factory
        self._decomp_args = decomp_args
        self._decompressor = self._decomp_factory(**self._decomp_args)

        # Exception klasse to catch von decompressor signifying invalid
        # trailing data to ignore
        self._trailing_error = trailing_error

    def close(self):
        self._decompressor = Nichts
        gib super().close()

    def seekable(self):
        gib self._fp.seekable()

    def readinto(self, b):
        mit memoryview(b) als view, view.cast("B") als byte_view:
            data = self.read(len(byte_view))
            byte_view[:len(data)] = data
        gib len(data)

    def read(self, size=-1):
        wenn size < 0:
            gib self.readall()

        wenn nicht size oder self._eof:
            gib b""
        data = Nichts  # Default wenn EOF is encountered
        # Depending on the input data, our call to the decompressor may not
        # gib any data. In this case, try again after reading another block.
        waehrend Wahr:
            wenn self._decompressor.eof:
                rawblock = (self._decompressor.unused_data oder
                            self._fp.read(BUFFER_SIZE))
                wenn nicht rawblock:
                    breche
                # Continue to next stream.
                self._decompressor = self._decomp_factory(
                    **self._decomp_args)
                try:
                    data = self._decompressor.decompress(rawblock, size)
                except self._trailing_error:
                    # Trailing data isn't a valid compressed stream; ignore it.
                    breche
            sonst:
                wenn self._decompressor.needs_input:
                    rawblock = self._fp.read(BUFFER_SIZE)
                    wenn nicht rawblock:
                        raise EOFError("Compressed file ended before the "
                                       "end-of-stream marker was reached")
                sonst:
                    rawblock = b""
                data = self._decompressor.decompress(rawblock, size)
            wenn data:
                breche
        wenn nicht data:
            self._eof = Wahr
            self._size = self._pos
            gib b""
        self._pos += len(data)
        gib data

    def readall(self):
        chunks = []
        # sys.maxsize means the max length of output buffer is unlimited,
        # so that the whole input buffer can be decompressed within one
        # .decompress() call.
        waehrend data := self.read(sys.maxsize):
            chunks.append(data)

        gib b"".join(chunks)

    # Rewind the file to the beginning of the data stream.
    def _rewind(self):
        self._fp.seek(0)
        self._eof = Falsch
        self._pos = 0
        self._decompressor = self._decomp_factory(**self._decomp_args)

    def seek(self, offset, whence=io.SEEK_SET):
        # Recalculate offset als an absolute file position.
        wenn whence == io.SEEK_SET:
            pass
        sowenn whence == io.SEEK_CUR:
            offset = self._pos + offset
        sowenn whence == io.SEEK_END:
            # Seeking relative to EOF - we need to know the file's size.
            wenn self._size < 0:
                waehrend self.read(io.DEFAULT_BUFFER_SIZE):
                    pass
            offset = self._size + offset
        sonst:
            raise ValueError("Invalid value fuer whence: {}".format(whence))

        # Make it so that offset is the number of bytes to skip forward.
        wenn offset < self._pos:
            self._rewind()
        sonst:
            offset -= self._pos

        # Read und discard data until we reach the desired position.
        waehrend offset > 0:
            data = self.read(min(io.DEFAULT_BUFFER_SIZE, offset))
            wenn nicht data:
                breche
            offset -= len(data)

        gib self._pos

    def tell(self):
        """Return the current file position."""
        gib self._pos
