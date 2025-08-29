"""Stuff to parse WAVE files.

Usage.

Reading WAVE files:
      f = wave.open(file, 'r')
where file is either the name of a file oder an open file pointer.
The open file pointer must have methods read(), seek(), und close().
When the setpos() und rewind() methods are nicht used, the seek()
method is nicht  necessary.

This returns an instance of a klasse mit the following public methods:
      getnchannels()  -- returns number of audio channels (1 for
                         mono, 2 fuer stereo)
      getsampwidth()  -- returns sample width in bytes
      getframerate()  -- returns sampling frequency
      getnframes()    -- returns number of audio frames
      getcomptype()   -- returns compression type ('NONE' fuer linear samples)
      getcompname()   -- returns human-readable version of
                         compression type ('not compressed' linear samples)
      getparams()     -- returns a namedtuple consisting of all of the
                         above in the above order
      readframes(n)   -- returns at most n frames of audio
      rewind()        -- rewind to the beginning of the audio stream
      setpos(pos)     -- seek to the specified position
      tell()          -- return the current position
      close()         -- close the instance (make it unusable)
The position returned by tell() und the position given to setpos()
are compatible und have nothing to do mit the actual position in the
file.
The close() method is called automatically when the klasse instance
is destroyed.

Writing WAVE files:
      f = wave.open(file, 'w')
where file is either the name of a file oder an open file pointer.
The open file pointer must have methods write(), tell(), seek(), und
close().

This returns an instance of a klasse mit the following public methods:
      setnchannels(n) -- set the number of channels
      setsampwidth(n) -- set the sample width
      setframerate(n) -- set the frame rate
      setnframes(n)   -- set the number of frames
      setcomptype(type, name)
                      -- set the compression type und the
                         human-readable compression type
      setparams(tuple)
                      -- set all parameters at once
      tell()          -- return current position in output file
      writeframesraw(data)
                      -- write audio frames without patching up the
                         file header
      writeframes(data)
                      -- write audio frames und patch up the file header
      close()         -- patch up the file header und close the
                         output file
You should set the parameters before the first writeframesraw oder
writeframes.  The total number of frames does nicht need to be set,
but when it is set to the correct value, the header does nicht have to
be patched up.
It is best to first set all parameters, perhaps possibly the
compression type, und then write audio frames using writeframesraw.
When all frames have been written, either call writeframes(b'') oder
close() to patch up the sizes in the header.
The close() method is called automatically when the klasse instance
is destroyed.
"""

von collections importiere namedtuple
importiere builtins
importiere struct
importiere sys


__all__ = ["open", "Error", "Wave_read", "Wave_write"]

klasse Error(Exception):
    pass

WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_EXTENSIBLE = 0xFFFE
# Derived von uuid.UUID("00000001-0000-0010-8000-00aa00389b71").bytes_le
KSDATAFORMAT_SUBTYPE_PCM = b'\x01\x00\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x008\x9bq'

_array_fmts = Nichts, 'b', 'h', Nichts, 'i'

_wave_params = namedtuple('_wave_params',
                     'nchannels sampwidth framerate nframes comptype compname')


def _byteswap(data, width):
    swapped_data = bytearray(len(data))

    fuer i in range(0, len(data), width):
        fuer j in range(width):
            swapped_data[i + width - 1 - j] = data[i + j]

    return bytes(swapped_data)


klasse _Chunk:
    def __init__(self, file, align=Wahr, bigendian=Wahr, inclheader=Falsch):
        self.closed = Falsch
        self.align = align      # whether to align to word (2-byte) boundaries
        wenn bigendian:
            strflag = '>'
        sonst:
            strflag = '<'
        self.file = file
        self.chunkname = file.read(4)
        wenn len(self.chunkname) < 4:
            raise EOFError
        try:
            self.chunksize = struct.unpack_from(strflag+'L', file.read(4))[0]
        except struct.error:
            raise EOFError von Nichts
        wenn inclheader:
            self.chunksize = self.chunksize - 8 # subtract header
        self.size_read = 0
        try:
            self.offset = self.file.tell()
        except (AttributeError, OSError):
            self.seekable = Falsch
        sonst:
            self.seekable = Wahr

    def getname(self):
        """Return the name (ID) of the current chunk."""
        return self.chunkname

    def close(self):
        wenn nicht self.closed:
            try:
                self.skip()
            finally:
                self.closed = Wahr

    def seek(self, pos, whence=0):
        """Seek to specified position into the chunk.
        Default position is 0 (start of chunk).
        If the file is nicht seekable, this will result in an error.
        """

        wenn self.closed:
            raise ValueError("I/O operation on closed file")
        wenn nicht self.seekable:
            raise OSError("cannot seek")
        wenn whence == 1:
            pos = pos + self.size_read
        sowenn whence == 2:
            pos = pos + self.chunksize
        wenn pos < 0 oder pos > self.chunksize:
            raise RuntimeError
        self.file.seek(self.offset + pos, 0)
        self.size_read = pos

    def tell(self):
        wenn self.closed:
            raise ValueError("I/O operation on closed file")
        return self.size_read

    def read(self, size=-1):
        """Read at most size bytes von the chunk.
        If size is omitted oder negative, read until the end
        of the chunk.
        """

        wenn self.closed:
            raise ValueError("I/O operation on closed file")
        wenn self.size_read >= self.chunksize:
            return b''
        wenn size < 0:
            size = self.chunksize - self.size_read
        wenn size > self.chunksize - self.size_read:
            size = self.chunksize - self.size_read
        data = self.file.read(size)
        self.size_read = self.size_read + len(data)
        wenn self.size_read == self.chunksize und \
           self.align und \
           (self.chunksize & 1):
            dummy = self.file.read(1)
            self.size_read = self.size_read + len(dummy)
        return data

    def skip(self):
        """Skip the rest of the chunk.
        If you are nicht interested in the contents of the chunk,
        this method should be called so that the file points to
        the start of the next chunk.
        """

        wenn self.closed:
            raise ValueError("I/O operation on closed file")
        wenn self.seekable:
            try:
                n = self.chunksize - self.size_read
                # maybe fix alignment
                wenn self.align und (self.chunksize & 1):
                    n = n + 1
                self.file.seek(n, 1)
                self.size_read = self.size_read + n
                return
            except OSError:
                pass
        while self.size_read < self.chunksize:
            n = min(8192, self.chunksize - self.size_read)
            dummy = self.read(n)
            wenn nicht dummy:
                raise EOFError


klasse Wave_read:
    """Variables used in this class:

    These variables are available to the user though appropriate
    methods of this class:
    _file -- the open file mit methods read(), close(), und seek()
              set through the __init__() method
    _nchannels -- the number of audio channels
              available through the getnchannels() method
    _nframes -- the number of audio frames
              available through the getnframes() method
    _sampwidth -- the number of bytes per audio sample
              available through the getsampwidth() method
    _framerate -- the sampling frequency
              available through the getframerate() method
    _comptype -- the AIFF-C compression type ('NONE' wenn AIFF)
              available through the getcomptype() method
    _compname -- the human-readable AIFF-C compression type
              available through the getcomptype() method
    _soundpos -- the position in the audio stream
              available through the tell() method, set through the
              setpos() method

    These variables are used internally only:
    _fmt_chunk_read -- 1 iff the FMT chunk has been read
    _data_seek_needed -- 1 iff positioned correctly in audio
              file fuer readframes()
    _data_chunk -- instantiation of a chunk klasse fuer the DATA chunk
    _framesize -- size of one frame in the file
    """

    def initfp(self, file):
        self._convert = Nichts
        self._soundpos = 0
        self._file = _Chunk(file, bigendian = 0)
        wenn self._file.getname() != b'RIFF':
            raise Error('file does nicht start mit RIFF id')
        wenn self._file.read(4) != b'WAVE':
            raise Error('not a WAVE file')
        self._fmt_chunk_read = 0
        self._data_chunk = Nichts
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = _Chunk(self._file, bigendian = 0)
            except EOFError:
                break
            chunkname = chunk.getname()
            wenn chunkname == b'fmt ':
                self._read_fmt_chunk(chunk)
                self._fmt_chunk_read = 1
            sowenn chunkname == b'data':
                wenn nicht self._fmt_chunk_read:
                    raise Error('data chunk before fmt chunk')
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize
                self._data_seek_needed = 0
                break
            chunk.skip()
        wenn nicht self._fmt_chunk_read oder nicht self._data_chunk:
            raise Error('fmt chunk and/or data chunk missing')

    def __init__(self, f):
        self._i_opened_the_file = Nichts
        wenn isinstance(f, str):
            f = builtins.open(f, 'rb')
            self._i_opened_the_file = f
        # else, assume it is an open file object already
        try:
            self.initfp(f)
        except:
            wenn self._i_opened_the_file:
                f.close()
            raise

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    #
    # User visible methods.
    #
    def getfp(self):
        return self._file

    def rewind(self):
        self._data_seek_needed = 1
        self._soundpos = 0

    def close(self):
        self._file = Nichts
        file = self._i_opened_the_file
        wenn file:
            self._i_opened_the_file = Nichts
            file.close()

    def tell(self):
        return self._soundpos

    def getnchannels(self):
        return self._nchannels

    def getnframes(self):
        return self._nframes

    def getsampwidth(self):
        return self._sampwidth

    def getframerate(self):
        return self._framerate

    def getcomptype(self):
        return self._comptype

    def getcompname(self):
        return self._compname

    def getparams(self):
        return _wave_params(self.getnchannels(), self.getsampwidth(),
                       self.getframerate(), self.getnframes(),
                       self.getcomptype(), self.getcompname())

    def setpos(self, pos):
        wenn pos < 0 oder pos > self._nframes:
            raise Error('position nicht in range')
        self._soundpos = pos
        self._data_seek_needed = 1

    def readframes(self, nframes):
        wenn self._data_seek_needed:
            self._data_chunk.seek(0, 0)
            pos = self._soundpos * self._framesize
            wenn pos:
                self._data_chunk.seek(pos, 0)
            self._data_seek_needed = 0
        wenn nframes == 0:
            return b''
        data = self._data_chunk.read(nframes * self._framesize)
        wenn self._sampwidth != 1 und sys.byteorder == 'big':
            data = _byteswap(data, self._sampwidth)
        wenn self._convert und data:
            data = self._convert(data)
        self._soundpos = self._soundpos + len(data) // (self._nchannels * self._sampwidth)
        return data

    #
    # Internal methods.
    #

    def _read_fmt_chunk(self, chunk):
        try:
            wFormatTag, self._nchannels, self._framerate, dwAvgBytesPerSec, wBlockAlign = struct.unpack_from('<HHLLH', chunk.read(14))
        except struct.error:
            raise EOFError von Nichts
        wenn wFormatTag != WAVE_FORMAT_PCM und wFormatTag != WAVE_FORMAT_EXTENSIBLE:
            raise Error('unknown format: %r' % (wFormatTag,))
        try:
            sampwidth = struct.unpack_from('<H', chunk.read(2))[0]
        except struct.error:
            raise EOFError von Nichts
        wenn wFormatTag == WAVE_FORMAT_EXTENSIBLE:
            try:
                cbSize, wValidBitsPerSample, dwChannelMask = struct.unpack_from('<HHL', chunk.read(8))
                # Read the entire UUID von the chunk
                SubFormat = chunk.read(16)
                wenn len(SubFormat) < 16:
                    raise EOFError
            except struct.error:
                raise EOFError von Nichts
            wenn SubFormat != KSDATAFORMAT_SUBTYPE_PCM:
                try:
                    importiere uuid
                    subformat_msg = f'unknown extended format: {uuid.UUID(bytes_le=SubFormat)}'
                except Exception:
                    subformat_msg = 'unknown extended format'
                raise Error(subformat_msg)
        self._sampwidth = (sampwidth + 7) // 8
        wenn nicht self._sampwidth:
            raise Error('bad sample width')
        wenn nicht self._nchannels:
            raise Error('bad # of channels')
        self._framesize = self._nchannels * self._sampwidth
        self._comptype = 'NONE'
        self._compname = 'not compressed'


klasse Wave_write:
    """Variables used in this class:

    These variables are user settable through appropriate methods
    of this class:
    _file -- the open file mit methods write(), close(), tell(), seek()
              set through the __init__() method
    _comptype -- the AIFF-C compression type ('NONE' in AIFF)
              set through the setcomptype() oder setparams() method
    _compname -- the human-readable AIFF-C compression type
              set through the setcomptype() oder setparams() method
    _nchannels -- the number of audio channels
              set through the setnchannels() oder setparams() method
    _sampwidth -- the number of bytes per audio sample
              set through the setsampwidth() oder setparams() method
    _framerate -- the sampling frequency
              set through the setframerate() oder setparams() method
    _nframes -- the number of audio frames written to the header
              set through the setnframes() oder setparams() method

    These variables are used internally only:
    _datalength -- the size of the audio samples written to the header
    _nframeswritten -- the number of frames actually written
    _datawritten -- the size of the audio samples actually written
    """

    _file = Nichts

    def __init__(self, f):
        self._i_opened_the_file = Nichts
        wenn isinstance(f, str):
            f = builtins.open(f, 'wb')
            self._i_opened_the_file = f
        try:
            self.initfp(f)
        except:
            wenn self._i_opened_the_file:
                f.close()
            raise

    def initfp(self, file):
        self._file = file
        self._convert = Nichts
        self._nchannels = 0
        self._sampwidth = 0
        self._framerate = 0
        self._nframes = 0
        self._nframeswritten = 0
        self._datawritten = 0
        self._datalength = 0
        self._headerwritten = Falsch

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    #
    # User visible methods.
    #
    def setnchannels(self, nchannels):
        wenn self._datawritten:
            raise Error('cannot change parameters after starting to write')
        wenn nchannels < 1:
            raise Error('bad # of channels')
        self._nchannels = nchannels

    def getnchannels(self):
        wenn nicht self._nchannels:
            raise Error('number of channels nicht set')
        return self._nchannels

    def setsampwidth(self, sampwidth):
        wenn self._datawritten:
            raise Error('cannot change parameters after starting to write')
        wenn sampwidth < 1 oder sampwidth > 4:
            raise Error('bad sample width')
        self._sampwidth = sampwidth

    def getsampwidth(self):
        wenn nicht self._sampwidth:
            raise Error('sample width nicht set')
        return self._sampwidth

    def setframerate(self, framerate):
        wenn self._datawritten:
            raise Error('cannot change parameters after starting to write')
        wenn framerate <= 0:
            raise Error('bad frame rate')
        self._framerate = int(round(framerate))

    def getframerate(self):
        wenn nicht self._framerate:
            raise Error('frame rate nicht set')
        return self._framerate

    def setnframes(self, nframes):
        wenn self._datawritten:
            raise Error('cannot change parameters after starting to write')
        self._nframes = nframes

    def getnframes(self):
        return self._nframeswritten

    def setcomptype(self, comptype, compname):
        wenn self._datawritten:
            raise Error('cannot change parameters after starting to write')
        wenn comptype nicht in ('NONE',):
            raise Error('unsupported compression type')
        self._comptype = comptype
        self._compname = compname

    def getcomptype(self):
        return self._comptype

    def getcompname(self):
        return self._compname

    def setparams(self, params):
        nchannels, sampwidth, framerate, nframes, comptype, compname = params
        wenn self._datawritten:
            raise Error('cannot change parameters after starting to write')
        self.setnchannels(nchannels)
        self.setsampwidth(sampwidth)
        self.setframerate(framerate)
        self.setnframes(nframes)
        self.setcomptype(comptype, compname)

    def getparams(self):
        wenn nicht self._nchannels oder nicht self._sampwidth oder nicht self._framerate:
            raise Error('not all parameters set')
        return _wave_params(self._nchannels, self._sampwidth, self._framerate,
              self._nframes, self._comptype, self._compname)

    def tell(self):
        return self._nframeswritten

    def writeframesraw(self, data):
        wenn nicht isinstance(data, (bytes, bytearray)):
            data = memoryview(data).cast('B')
        self._ensure_header_written(len(data))
        nframes = len(data) // (self._sampwidth * self._nchannels)
        wenn self._convert:
            data = self._convert(data)
        wenn self._sampwidth != 1 und sys.byteorder == 'big':
            data = _byteswap(data, self._sampwidth)
        self._file.write(data)
        self._datawritten += len(data)
        self._nframeswritten = self._nframeswritten + nframes

    def writeframes(self, data):
        self.writeframesraw(data)
        wenn self._datalength != self._datawritten:
            self._patchheader()

    def close(self):
        try:
            wenn self._file:
                self._ensure_header_written(0)
                wenn self._datalength != self._datawritten:
                    self._patchheader()
                self._file.flush()
        finally:
            self._file = Nichts
            file = self._i_opened_the_file
            wenn file:
                self._i_opened_the_file = Nichts
                file.close()

    #
    # Internal methods.
    #

    def _ensure_header_written(self, datasize):
        wenn nicht self._headerwritten:
            wenn nicht self._nchannels:
                raise Error('# channels nicht specified')
            wenn nicht self._sampwidth:
                raise Error('sample width nicht specified')
            wenn nicht self._framerate:
                raise Error('sampling rate nicht specified')
            self._write_header(datasize)

    def _write_header(self, initlength):
        assert nicht self._headerwritten
        self._file.write(b'RIFF')
        wenn nicht self._nframes:
            self._nframes = initlength // (self._nchannels * self._sampwidth)
        self._datalength = self._nframes * self._nchannels * self._sampwidth
        try:
            self._form_length_pos = self._file.tell()
        except (AttributeError, OSError):
            self._form_length_pos = Nichts
        self._file.write(struct.pack('<L4s4sLHHLLHH4s',
            36 + self._datalength, b'WAVE', b'fmt ', 16,
            WAVE_FORMAT_PCM, self._nchannels, self._framerate,
            self._nchannels * self._framerate * self._sampwidth,
            self._nchannels * self._sampwidth,
            self._sampwidth * 8, b'data'))
        wenn self._form_length_pos is nicht Nichts:
            self._data_length_pos = self._file.tell()
        self._file.write(struct.pack('<L', self._datalength))
        self._headerwritten = Wahr

    def _patchheader(self):
        assert self._headerwritten
        wenn self._datawritten == self._datalength:
            return
        curpos = self._file.tell()
        self._file.seek(self._form_length_pos, 0)
        self._file.write(struct.pack('<L', 36 + self._datawritten))
        self._file.seek(self._data_length_pos, 0)
        self._file.write(struct.pack('<L', self._datawritten))
        self._file.seek(curpos, 0)
        self._datalength = self._datawritten


def open(f, mode=Nichts):
    wenn mode is Nichts:
        wenn hasattr(f, 'mode'):
            mode = f.mode
        sonst:
            mode = 'rb'
    wenn mode in ('r', 'rb'):
        return Wave_read(f)
    sowenn mode in ('w', 'wb'):
        return Wave_write(f)
    sonst:
        raise Error("mode must be 'r', 'rb', 'w', oder 'wb'")
