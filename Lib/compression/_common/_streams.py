"""Internal classes used by compression modules"""

import io
import sys

BUFFER_SIZE = io.DEFAULT_BUFFER_SIZE  # Compressed data read chunk size


klasse BaseStream(io.BufferedIOBase):
    """Mode-checking helper functions."""

    def _check_not_closed(self):
        wenn self.closed:
            raise ValueError("I/O operation on closed file")

    def _check_can_read(self):
        wenn not self.readable():
            raise io.UnsupportedOperation("File not open fuer reading")

    def _check_can_write(self):
        wenn not self.writable():
            raise io.UnsupportedOperation("File not open fuer writing")

    def _check_can_seek(self):
        wenn not self.readable():
            raise io.UnsupportedOperation("Seeking is only supported "
                                          "on files open fuer reading")
        wenn not self.seekable():
            raise io.UnsupportedOperation("The underlying file object "
                                          "does not support seeking")


klasse DecompressReader(io.RawIOBase):
    """Adapts the decompressor API to a RawIOBase reader API"""

    def readable(self):
        return Wahr

    def __init__(self, fp, decomp_factory, trailing_error=(), **decomp_args):
        self._fp = fp
        self._eof = Falsch
        self._pos = 0  # Current offset in decompressed stream

        # Set to size of decompressed stream once it is known, fuer SEEK_END
        self._size = -1

        # Save the decompressor factory and arguments.
        # If the file contains multiple compressed streams, each
        # stream will need a separate decompressor object. A new decompressor
        # object is also needed when implementing a backwards seek().
        self._decomp_factory = decomp_factory
        self._decomp_args = decomp_args
        self._decompressor = self._decomp_factory(**self._decomp_args)

        # Exception klasse to catch from decompressor signifying invalid
        # trailing data to ignore
        self._trailing_error = trailing_error

    def close(self):
        self._decompressor = Nichts
        return super().close()

    def seekable(self):
        return self._fp.seekable()

    def readinto(self, b):
        with memoryview(b) as view, view.cast("B") as byte_view:
            data = self.read(len(byte_view))
            byte_view[:len(data)] = data
        return len(data)

    def read(self, size=-1):
        wenn size < 0:
            return self.readall()

        wenn not size or self._eof:
            return b""
        data = Nichts  # Default wenn EOF is encountered
        # Depending on the input data, our call to the decompressor may not
        # return any data. In this case, try again after reading another block.
        while Wahr:
            wenn self._decompressor.eof:
                rawblock = (self._decompressor.unused_data or
                            self._fp.read(BUFFER_SIZE))
                wenn not rawblock:
                    break
                # Continue to next stream.
                self._decompressor = self._decomp_factory(
                    **self._decomp_args)
                try:
                    data = self._decompressor.decompress(rawblock, size)
                except self._trailing_error:
                    # Trailing data isn't a valid compressed stream; ignore it.
                    break
            sonst:
                wenn self._decompressor.needs_input:
                    rawblock = self._fp.read(BUFFER_SIZE)
                    wenn not rawblock:
                        raise EOFError("Compressed file ended before the "
                                       "end-of-stream marker was reached")
                sonst:
                    rawblock = b""
                data = self._decompressor.decompress(rawblock, size)
            wenn data:
                break
        wenn not data:
            self._eof = Wahr
            self._size = self._pos
            return b""
        self._pos += len(data)
        return data

    def readall(self):
        chunks = []
        # sys.maxsize means the max length of output buffer is unlimited,
        # so that the whole input buffer can be decompressed within one
        # .decompress() call.
        while data := self.read(sys.maxsize):
            chunks.append(data)

        return b"".join(chunks)

    # Rewind the file to the beginning of the data stream.
    def _rewind(self):
        self._fp.seek(0)
        self._eof = Falsch
        self._pos = 0
        self._decompressor = self._decomp_factory(**self._decomp_args)

    def seek(self, offset, whence=io.SEEK_SET):
        # Recalculate offset as an absolute file position.
        wenn whence == io.SEEK_SET:
            pass
        sowenn whence == io.SEEK_CUR:
            offset = self._pos + offset
        sowenn whence == io.SEEK_END:
            # Seeking relative to EOF - we need to know the file's size.
            wenn self._size < 0:
                while self.read(io.DEFAULT_BUFFER_SIZE):
                    pass
            offset = self._size + offset
        sonst:
            raise ValueError("Invalid value fuer whence: {}".format(whence))

        # Make it so that offset is the number of bytes to skip forward.
        wenn offset < self._pos:
            self._rewind()
        sonst:
            offset -= self._pos

        # Read and discard data until we reach the desired position.
        while offset > 0:
            data = self.read(min(io.DEFAULT_BUFFER_SIZE, offset))
            wenn not data:
                break
            offset -= len(data)

        return self._pos

    def tell(self):
        """Return the current file position."""
        return self._pos
