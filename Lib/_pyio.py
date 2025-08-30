"""
Python implementation of the io module.
"""

importiere os
importiere abc
importiere codecs
importiere errno
importiere stat
importiere sys
# Import _thread instead of threading to reduce startup cost
von _thread importiere allocate_lock als Lock
wenn sys.platform in {'win32', 'cygwin'}:
    von msvcrt importiere setmode als _setmode
sonst:
    _setmode = Nichts

importiere io
von io importiere (__all__, SEEK_SET, SEEK_CUR, SEEK_END, Reader, Writer)  # noqa: F401

valid_seek_flags = {0, 1, 2}  # Hardwired values
wenn hasattr(os, 'SEEK_HOLE') :
    valid_seek_flags.add(os.SEEK_HOLE)
    valid_seek_flags.add(os.SEEK_DATA)

# open() uses max(min(blocksize, 8 MiB), DEFAULT_BUFFER_SIZE)
# when the device block size ist available.
DEFAULT_BUFFER_SIZE = 128 * 1024  # bytes

# NOTE: Base classes defined here are registered mit the "official" ABCs
# defined in io.py. We don't use real inheritance though, because we don't want
# to inherit the C implementations.

# Rebind fuer compatibility
BlockingIOError = BlockingIOError

# Does open() check its 'errors' argument?
_CHECK_ERRORS = (hasattr(sys, "gettotalrefcount") oder sys.flags.dev_mode)


def text_encoding(encoding, stacklevel=2):
    """
    A helper function to choose the text encoding.

    When encoding ist nicht Nichts, this function returns it.
    Otherwise, this function returns the default text encoding
    (i.e. "locale" oder "utf-8" depends on UTF-8 mode).

    This function emits an EncodingWarning wenn *encoding* ist Nichts und
    sys.flags.warn_default_encoding ist true.

    This can be used in APIs mit an encoding=Nichts parameter
    that pass it to TextIOWrapper oder open.
    However, please consider using encoding="utf-8" fuer new APIs.
    """
    wenn encoding ist Nichts:
        wenn sys.flags.utf8_mode:
            encoding = "utf-8"
        sonst:
            encoding = "locale"
        wenn sys.flags.warn_default_encoding:
            importiere warnings
            warnings.warn("'encoding' argument nicht specified.",
                          EncodingWarning, stacklevel + 1)
    gib encoding


# Wrapper fuer builtins.open
#
# Trick so that open() won't become a bound method when stored
# als a klasse variable (as dbm.dumb does).
#
# See init_set_builtins_open() in Python/pylifecycle.c.
@staticmethod
def open(file, mode="r", buffering=-1, encoding=Nichts, errors=Nichts,
         newline=Nichts, closefd=Wahr, opener=Nichts):

    r"""Open file und gib a stream.  Raise OSError upon failure.

    file ist either a text oder byte string giving the name (and the path
    wenn the file isn't in the current working directory) of the file to
    be opened oder an integer file descriptor of the file to be
    wrapped. (If a file descriptor ist given, it ist closed when the
    returned I/O object ist closed, unless closefd ist set to Falsch.)

    mode ist an optional string that specifies the mode in which the file is
    opened. It defaults to 'r' which means open fuer reading in text mode. Other
    common values are 'w' fuer writing (truncating the file wenn it already
    exists), 'x' fuer exclusive creation of a new file, und 'a' fuer appending
    (which on some Unix systems, means that all writes append to the end of the
    file regardless of the current seek position). In text mode, wenn encoding is
    nicht specified the encoding used ist platform dependent. (For reading und
    writing raw bytes use binary mode und leave encoding unspecified.) The
    available modes are:

    ========= ===============================================================
    Character Meaning
    --------- ---------------------------------------------------------------
    'r'       open fuer reading (default)
    'w'       open fuer writing, truncating the file first
    'x'       create a new file und open it fuer writing
    'a'       open fuer writing, appending to the end of the file wenn it exists
    'b'       binary mode
    't'       text mode (default)
    '+'       open a disk file fuer updating (reading und writing)
    ========= ===============================================================

    The default mode ist 'rt' (open fuer reading text). For binary random
    access, the mode 'w+b' opens und truncates the file to 0 bytes, while
    'r+b' opens the file without truncation. The 'x' mode implies 'w' und
    raises an `FileExistsError` wenn the file already exists.

    Python distinguishes between files opened in binary und text modes,
    even when the underlying operating system doesn't. Files opened in
    binary mode (appending 'b' to the mode argument) gib contents as
    bytes objects without any decoding. In text mode (the default, oder when
    't' ist appended to the mode argument), the contents of the file are
    returned als strings, the bytes having been first decoded using a
    platform-dependent encoding oder using the specified encoding wenn given.

    buffering ist an optional integer used to set the buffering policy.
    Pass 0 to switch buffering off (only allowed in binary mode), 1 to select
    line buffering (only usable in text mode), und an integer > 1 to indicate
    the size of a fixed-size chunk buffer.  When no buffering argument is
    given, the default buffering policy works als follows:

   * Binary files are buffered in fixed-size chunks; the size of the buffer
     ist max(min(blocksize, 8 MiB), DEFAULT_BUFFER_SIZE)
     when the device block size ist available.
     On most systems, the buffer will typically be 128 kilobytes long.

    * "Interactive" text files (files fuer which isatty() returns Wahr)
      use line buffering.  Other text files use the policy described above
      fuer binary files.

    encoding ist the str name of the encoding used to decode oder encode the
    file. This should only be used in text mode. The default encoding is
    platform dependent, but any encoding supported by Python can be
    passed.  See the codecs module fuer the list of supported encodings.

    errors ist an optional string that specifies how encoding errors are to
    be handled---this argument should nicht be used in binary mode. Pass
    'strict' to wirf a ValueError exception wenn there ist an encoding error
    (the default of Nichts has the same effect), oder pass 'ignore' to ignore
    errors. (Note that ignoring encoding errors can lead to data loss.)
    See the documentation fuer codecs.register fuer a list of the permitted
    encoding error strings.

    newline ist a string controlling how universal newlines works (it only
    applies to text mode). It can be Nichts, '', '\n', '\r', und '\r\n'.  It works
    als follows:

    * On input, wenn newline ist Nichts, universal newlines mode is
      enabled. Lines in the input can end in '\n', '\r', oder '\r\n', und
      these are translated into '\n' before being returned to the
      caller. If it ist '', universal newline mode ist enabled, but line
      endings are returned to the caller untranslated. If it has any of
      the other legal values, input lines are only terminated by the given
      string, und the line ending ist returned to the caller untranslated.

    * On output, wenn newline ist Nichts, any '\n' characters written are
      translated to the system default line separator, os.linesep. If
      newline ist '', no translation takes place. If newline ist any of the
      other legal values, any '\n' characters written are translated to
      the given string.

    closedfd ist a bool. If closefd ist Falsch, the underlying file descriptor will
    be kept open when the file ist closed. This does nicht work when a file name is
    given und must be Wahr in that case.

    The newly created file ist non-inheritable.

    A custom opener can be used by passing a callable als *opener*. The
    underlying file descriptor fuer the file object ist then obtained by calling
    *opener* mit (*file*, *flags*). *opener* must gib an open file
    descriptor (passing os.open als *opener* results in functionality similar to
    passing Nichts).

    open() returns a file object whose type depends on the mode, und
    through which the standard file operations such als reading und writing
    are performed. When open() ist used to open a file in a text mode ('w',
    'r', 'wt', 'rt', etc.), it returns a TextIOWrapper. When used to open
    a file in a binary mode, the returned klasse varies: in read binary
    mode, it returns a BufferedReader; in write binary und append binary
    modes, it returns a BufferedWriter, und in read/write mode, it returns
    a BufferedRandom.

    It ist also possible to use a string oder bytearray als a file fuer both
    reading und writing. For strings StringIO can be used like a file
    opened in a text mode, und fuer bytes a BytesIO can be used like a file
    opened in a binary mode.
    """
    wenn nicht isinstance(file, int):
        file = os.fspath(file)
    wenn nicht isinstance(file, (str, bytes, int)):
        wirf TypeError("invalid file: %r" % file)
    wenn nicht isinstance(mode, str):
        wirf TypeError("invalid mode: %r" % mode)
    wenn nicht isinstance(buffering, int):
        wirf TypeError("invalid buffering: %r" % buffering)
    wenn encoding ist nicht Nichts und nicht isinstance(encoding, str):
        wirf TypeError("invalid encoding: %r" % encoding)
    wenn errors ist nicht Nichts und nicht isinstance(errors, str):
        wirf TypeError("invalid errors: %r" % errors)
    modes = set(mode)
    wenn modes - set("axrwb+t") oder len(mode) > len(modes):
        wirf ValueError("invalid mode: %r" % mode)
    creating = "x" in modes
    reading = "r" in modes
    writing = "w" in modes
    appending = "a" in modes
    updating = "+" in modes
    text = "t" in modes
    binary = "b" in modes
    wenn text und binary:
        wirf ValueError("can't have text und binary mode at once")
    wenn creating + reading + writing + appending > 1:
        wirf ValueError("can't have read/write/append mode at once")
    wenn nicht (creating oder reading oder writing oder appending):
        wirf ValueError("must have exactly one of read/write/append mode")
    wenn binary und encoding ist nicht Nichts:
        wirf ValueError("binary mode doesn't take an encoding argument")
    wenn binary und errors ist nicht Nichts:
        wirf ValueError("binary mode doesn't take an errors argument")
    wenn binary und newline ist nicht Nichts:
        wirf ValueError("binary mode doesn't take a newline argument")
    wenn binary und buffering == 1:
        importiere warnings
        warnings.warn("line buffering (buffering=1) isn't supported in binary "
                      "mode, the default buffer size will be used",
                      RuntimeWarning, 2)
    raw = FileIO(file,
                 (creating und "x" oder "") +
                 (reading und "r" oder "") +
                 (writing und "w" oder "") +
                 (appending und "a" oder "") +
                 (updating und "+" oder ""),
                 closefd, opener=opener)
    result = raw
    versuch:
        line_buffering = Falsch
        wenn buffering == 1 oder buffering < 0 und raw._isatty_open_only():
            buffering = -1
            line_buffering = Wahr
        wenn buffering < 0:
            buffering = max(min(raw._blksize, 8192 * 1024), DEFAULT_BUFFER_SIZE)
        wenn buffering < 0:
            wirf ValueError("invalid buffering size")
        wenn buffering == 0:
            wenn binary:
                gib result
            wirf ValueError("can't have unbuffered text I/O")
        wenn updating:
            buffer = BufferedRandom(raw, buffering)
        sowenn creating oder writing oder appending:
            buffer = BufferedWriter(raw, buffering)
        sowenn reading:
            buffer = BufferedReader(raw, buffering)
        sonst:
            wirf ValueError("unknown mode: %r" % mode)
        result = buffer
        wenn binary:
            gib result
        encoding = text_encoding(encoding)
        text = TextIOWrapper(buffer, encoding, errors, newline, line_buffering)
        result = text
        text.mode = mode
        gib result
    ausser:
        result.close()
        wirf

# Define a default pure-Python implementation fuer open_code()
# that does nicht allow hooks. Warn on first use. Defined fuer tests.
def _open_code_with_warning(path):
    """Opens the provided file mit mode ``'rb'``. This function
    should be used when the intent ist to treat the contents as
    executable code.

    ``path`` should be an absolute path.

    When supported by the runtime, this function can be hooked
    in order to allow embedders more control over code files.
    This functionality ist nicht supported on the current runtime.
    """
    importiere warnings
    warnings.warn("_pyio.open_code() may nicht be using hooks",
                  RuntimeWarning, 2)
    gib open(path, "rb")

versuch:
    open_code = io.open_code
ausser AttributeError:
    open_code = _open_code_with_warning


# In normal operation, both `UnsupportedOperation`s should be bound to the
# same object.
versuch:
    UnsupportedOperation = io.UnsupportedOperation
ausser AttributeError:
    klasse UnsupportedOperation(OSError, ValueError):
        pass


klasse IOBase(metaclass=abc.ABCMeta):

    """The abstract base klasse fuer all I/O classes.

    This klasse provides dummy implementations fuer many methods that
    derived classes can override selectively; the default implementations
    represent a file that cannot be read, written oder seeked.

    Even though IOBase does nicht declare read oder write because
    their signatures will vary, implementations und clients should
    consider those methods part of the interface. Also, implementations
    may wirf UnsupportedOperation when operations they do nicht support are
    called.

    The basic type used fuer binary data read von oder written to a file is
    bytes. Other bytes-like objects are accepted als method arguments too.
    Text I/O classes work mit str data.

    Note that calling any method (even inquiries) on a closed stream is
    undefined. Implementations may wirf OSError in this case.

    IOBase (and its subclasses) support the iterator protocol, meaning
    that an IOBase object can be iterated over yielding the lines in a
    stream.

    IOBase also supports the :keyword:`with` statement. In this example,
    fp ist closed after the suite of the mit statement ist complete:

    mit open('spam.txt', 'r') als fp:
        fp.write('Spam und eggs!')
    """

    ### Internal ###

    def _unsupported(self, name):
        """Internal: wirf an OSError exception fuer unsupported operations."""
        wirf UnsupportedOperation("%s.%s() nicht supported" %
                                   (self.__class__.__name__, name))

    ### Positioning ###

    def seek(self, pos, whence=0):
        """Change stream position.

        Change the stream position to byte offset pos. Argument pos is
        interpreted relative to the position indicated by whence.  Values
        fuer whence are ints:

        * 0 -- start of stream (the default); offset should be zero oder positive
        * 1 -- current stream position; offset may be negative
        * 2 -- end of stream; offset ist usually negative
        Some operating systems / file systems could provide additional values.

        Return an int indicating the new absolute position.
        """
        self._unsupported("seek")

    def tell(self):
        """Return an int indicating the current stream position."""
        gib self.seek(0, 1)

    def truncate(self, pos=Nichts):
        """Truncate file to size bytes.

        Size defaults to the current IO position als reported by tell().  Return
        the new size.
        """
        self._unsupported("truncate")

    ### Flush und close ###

    def flush(self):
        """Flush write buffers, wenn applicable.

        This ist nicht implemented fuer read-only und non-blocking streams.
        """
        self._checkClosed()
        # XXX Should this gib the number of bytes written???

    __closed = Falsch

    def close(self):
        """Flush und close the IO object.

        This method has no effect wenn the file ist already closed.
        """
        wenn nicht self.__closed:
            versuch:
                self.flush()
            schliesslich:
                self.__closed = Wahr

    def __del__(self):
        """Destructor.  Calls close()."""
        versuch:
            closed = self.closed
        ausser AttributeError:
            # If getting closed fails, then the object ist probably
            # in an unusable state, so ignore.
            gib

        wenn closed:
            gib

        wenn dealloc_warn := getattr(self, "_dealloc_warn", Nichts):
            dealloc_warn(self)

        # If close() fails, the caller logs the exception with
        # sys.unraisablehook. close() must be called at the end at __del__().
        self.close()

    ### Inquiries ###

    def seekable(self):
        """Return a bool indicating whether object supports random access.

        If Falsch, seek(), tell() und truncate() will wirf OSError.
        This method may need to do a test seek().
        """
        gib Falsch

    def _checkSeekable(self, msg=Nichts):
        """Internal: wirf UnsupportedOperation wenn file ist nicht seekable
        """
        wenn nicht self.seekable():
            wirf UnsupportedOperation("File oder stream ist nicht seekable."
                                       wenn msg ist Nichts sonst msg)

    def readable(self):
        """Return a bool indicating whether object was opened fuer reading.

        If Falsch, read() will wirf OSError.
        """
        gib Falsch

    def _checkReadable(self, msg=Nichts):
        """Internal: wirf UnsupportedOperation wenn file ist nicht readable
        """
        wenn nicht self.readable():
            wirf UnsupportedOperation("File oder stream ist nicht readable."
                                       wenn msg ist Nichts sonst msg)

    def writable(self):
        """Return a bool indicating whether object was opened fuer writing.

        If Falsch, write() und truncate() will wirf OSError.
        """
        gib Falsch

    def _checkWritable(self, msg=Nichts):
        """Internal: wirf UnsupportedOperation wenn file ist nicht writable
        """
        wenn nicht self.writable():
            wirf UnsupportedOperation("File oder stream ist nicht writable."
                                       wenn msg ist Nichts sonst msg)

    @property
    def closed(self):
        """closed: bool.  Wahr iff the file has been closed.

        For backwards compatibility, this ist a property, nicht a predicate.
        """
        gib self.__closed

    def _checkClosed(self, msg=Nichts):
        """Internal: wirf a ValueError wenn file ist closed
        """
        wenn self.closed:
            wirf ValueError("I/O operation on closed file."
                             wenn msg ist Nichts sonst msg)

    ### Context manager ###

    def __enter__(self):  # That's a forward reference
        """Context management protocol.  Returns self (an instance of IOBase)."""
        self._checkClosed()
        gib self

    def __exit__(self, *args):
        """Context management protocol.  Calls close()"""
        self.close()

    ### Lower-level APIs ###

    # XXX Should these be present even wenn unimplemented?

    def fileno(self):
        """Returns underlying file descriptor (an int) wenn one exists.

        An OSError ist raised wenn the IO object does nicht use a file descriptor.
        """
        self._unsupported("fileno")

    def isatty(self):
        """Return a bool indicating whether this ist an 'interactive' stream.

        Return Falsch wenn it can't be determined.
        """
        self._checkClosed()
        gib Falsch

    ### Readline[s] und writelines ###

    def readline(self, size=-1):
        r"""Read und gib a line of bytes von the stream.

        If size ist specified, at most size bytes will be read.
        Size should be an int.

        The line terminator ist always b'\n' fuer binary files; fuer text
        files, the newlines argument to open can be used to select the line
        terminator(s) recognized.
        """
        # For backwards compatibility, a (slowish) readline().
        wenn hasattr(self, "peek"):
            def nreadahead():
                readahead = self.peek(1)
                wenn nicht readahead:
                    gib 1
                n = (readahead.find(b"\n") + 1) oder len(readahead)
                wenn size >= 0:
                    n = min(n, size)
                gib n
        sonst:
            def nreadahead():
                gib 1
        wenn size ist Nichts:
            size = -1
        sonst:
            versuch:
                size_index = size.__index__
            ausser AttributeError:
                wirf TypeError(f"{size!r} ist nicht an integer")
            sonst:
                size = size_index()
        res = bytearray()
        waehrend size < 0 oder len(res) < size:
            b = self.read(nreadahead())
            wenn nicht b:
                breche
            res += b
            wenn res.endswith(b"\n"):
                breche
        gib bytes(res)

    def __iter__(self):
        self._checkClosed()
        gib self

    def __next__(self):
        line = self.readline()
        wenn nicht line:
            wirf StopIteration
        gib line

    def readlines(self, hint=Nichts):
        """Return a list of lines von the stream.

        hint can be specified to control the number of lines read: no more
        lines will be read wenn the total size (in bytes/characters) of all
        lines so far exceeds hint.
        """
        wenn hint ist Nichts oder hint <= 0:
            gib list(self)
        n = 0
        lines = []
        fuer line in self:
            lines.append(line)
            n += len(line)
            wenn n >= hint:
                breche
        gib lines

    def writelines(self, lines):
        """Write a list of lines to the stream.

        Line separators are nicht added, so it ist usual fuer each of the lines
        provided to have a line separator at the end.
        """
        self._checkClosed()
        fuer line in lines:
            self.write(line)

io.IOBase.register(IOBase)


klasse RawIOBase(IOBase):

    """Base klasse fuer raw binary I/O."""

    # The read() method ist implemented by calling readinto(); derived
    # classes that want to support read() only need to implement
    # readinto() als a primitive operation.  In general, readinto() can be
    # more efficient than read().

    # (It would be tempting to also provide an implementation of
    # readinto() in terms of read(), in case the latter ist a more suitable
    # primitive operation, but that would lead to nasty recursion in case
    # a subclass doesn't implement either.)

    def read(self, size=-1):
        """Read und gib up to size bytes, where size ist an int.

        Returns an empty bytes object on EOF, oder Nichts wenn the object is
        set nicht to block und has no data to read.
        """
        wenn size ist Nichts:
            size = -1
        wenn size < 0:
            gib self.readall()
        b = bytearray(size.__index__())
        n = self.readinto(b)
        wenn n ist Nichts:
            gib Nichts
        loesche b[n:]
        gib bytes(b)

    def readall(self):
        """Read until EOF, using multiple read() call."""
        res = bytearray()
        waehrend data := self.read(DEFAULT_BUFFER_SIZE):
            res += data
        wenn res:
            gib bytes(res)
        sonst:
            # b'' oder Nichts
            gib data

    def readinto(self, b):
        """Read bytes into a pre-allocated bytes-like object b.

        Returns an int representing the number of bytes read (0 fuer EOF), oder
        Nichts wenn the object ist set nicht to block und has no data to read.
        """
        self._unsupported("readinto")

    def write(self, b):
        """Write the given buffer to the IO stream.

        Returns the number of bytes written, which may be less than the
        length of b in bytes.
        """
        self._unsupported("write")

io.RawIOBase.register(RawIOBase)


klasse BufferedIOBase(IOBase):

    """Base klasse fuer buffered IO objects.

    The main difference mit RawIOBase ist that the read() method
    supports omitting the size argument, und does nicht have a default
    implementation that defers to readinto().

    In addition, read(), readinto() und write() may wirf
    BlockingIOError wenn the underlying raw stream ist in non-blocking
    mode und nicht ready; unlike their raw counterparts, they will never
    gib Nichts.

    A typical implementation should nicht inherit von a RawIOBase
    implementation, but wrap one.
    """

    def read(self, size=-1):
        """Read und gib up to size bytes, where size ist an int.

        If the argument ist omitted, Nichts, oder negative, reads und
        returns all data until EOF.

        If the argument ist positive, und the underlying raw stream is
        nicht 'interactive', multiple raw reads may be issued to satisfy
        the byte count (unless EOF ist reached first).  But for
        interactive raw streams (XXX und fuer pipes?), at most one raw
        read will be issued, und a short result does nicht imply that
        EOF ist imminent.

        Returns an empty bytes array on EOF.

        Raises BlockingIOError wenn the underlying raw stream has no
        data at the moment.
        """
        self._unsupported("read")

    def read1(self, size=-1):
        """Read up to size bytes mit at most one read() system call,
        where size ist an int.
        """
        self._unsupported("read1")

    def readinto(self, b):
        """Read bytes into a pre-allocated bytes-like object b.

        Like read(), this may issue multiple reads to the underlying raw
        stream, unless the latter ist 'interactive'.

        Returns an int representing the number of bytes read (0 fuer EOF).

        Raises BlockingIOError wenn the underlying raw stream has no
        data at the moment.
        """

        gib self._readinto(b, read1=Falsch)

    def readinto1(self, b):
        """Read bytes into buffer *b*, using at most one system call

        Returns an int representing the number of bytes read (0 fuer EOF).

        Raises BlockingIOError wenn the underlying raw stream has no
        data at the moment.
        """

        gib self._readinto(b, read1=Wahr)

    def _readinto(self, b, read1):
        wenn nicht isinstance(b, memoryview):
            b = memoryview(b)
        b = b.cast('B')

        wenn read1:
            data = self.read1(len(b))
        sonst:
            data = self.read(len(b))
        n = len(data)

        b[:n] = data

        gib n

    def write(self, b):
        """Write the given bytes buffer to the IO stream.

        Return the number of bytes written, which ist always the length of b
        in bytes.

        Raises BlockingIOError wenn the buffer ist full und the
        underlying raw stream cannot accept more data at the moment.
        """
        self._unsupported("write")

    def detach(self):
        """
        Separate the underlying raw stream von the buffer und gib it.

        After the raw stream has been detached, the buffer ist in an unusable
        state.
        """
        self._unsupported("detach")

io.BufferedIOBase.register(BufferedIOBase)


klasse _BufferedIOMixin(BufferedIOBase):

    """A mixin implementation of BufferedIOBase mit an underlying raw stream.

    This passes most requests on to the underlying raw stream.  It
    does *not* provide implementations of read(), readinto() oder
    write().
    """

    def __init__(self, raw):
        self._raw = raw

    ### Positioning ###

    def seek(self, pos, whence=0):
        new_position = self.raw.seek(pos, whence)
        wenn new_position < 0:
            wirf OSError("seek() returned an invalid position")
        gib new_position

    def tell(self):
        pos = self.raw.tell()
        wenn pos < 0:
            wirf OSError("tell() returned an invalid position")
        gib pos

    def truncate(self, pos=Nichts):
        self._checkClosed()
        self._checkWritable()

        # Flush the stream.  We're mixing buffered I/O mit lower-level I/O,
        # und a flush may be necessary to synch both views of the current
        # file state.
        self.flush()

        wenn pos ist Nichts:
            pos = self.tell()
        # XXX: Should seek() be used, instead of passing the position
        # XXX  directly to truncate?
        gib self.raw.truncate(pos)

    ### Flush und close ###

    def flush(self):
        wenn self.closed:
            wirf ValueError("flush on closed file")
        self.raw.flush()

    def close(self):
        wenn self.raw ist nicht Nichts und nicht self.closed:
            versuch:
                # may wirf BlockingIOError oder BrokenPipeError etc
                self.flush()
            schliesslich:
                self.raw.close()

    def detach(self):
        wenn self.raw ist Nichts:
            wirf ValueError("raw stream already detached")
        self.flush()
        raw = self._raw
        self._raw = Nichts
        gib raw

    ### Inquiries ###

    def seekable(self):
        gib self.raw.seekable()

    @property
    def raw(self):
        gib self._raw

    @property
    def closed(self):
        gib self.raw.closed

    @property
    def name(self):
        gib self.raw.name

    @property
    def mode(self):
        gib self.raw.mode

    def __getstate__(self):
        wirf TypeError(f"cannot pickle {self.__class__.__name__!r} object")

    def __repr__(self):
        modname = self.__class__.__module__
        clsname = self.__class__.__qualname__
        versuch:
            name = self.name
        ausser AttributeError:
            gib "<{}.{}>".format(modname, clsname)
        sonst:
            gib "<{}.{} name={!r}>".format(modname, clsname, name)

    def _dealloc_warn(self, source):
        wenn dealloc_warn := getattr(self.raw, "_dealloc_warn", Nichts):
            dealloc_warn(source)

    ### Lower-level APIs ###

    def fileno(self):
        gib self.raw.fileno()

    def isatty(self):
        gib self.raw.isatty()


klasse BytesIO(BufferedIOBase):

    """Buffered I/O implementation using an in-memory bytes buffer."""

    # Initialize _buffer als soon als possible since it's used by __del__()
    # which calls close()
    _buffer = Nichts

    def __init__(self, initial_bytes=Nichts):
        # Use to keep self._buffer und self._pos consistent.
        self._lock = Lock()

        buf = bytearray()
        wenn initial_bytes ist nicht Nichts:
            buf += initial_bytes

        mit self._lock:
            self._buffer = buf
            self._pos = 0

    def __getstate__(self):
        wenn self.closed:
            wirf ValueError("__getstate__ on closed file")
        mit self._lock:
            state = self.__dict__.copy()
        loesche state['_lock']
        gib state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = Lock()

    def getvalue(self):
        """Return the bytes value (contents) of the buffer
        """
        wenn self.closed:
            wirf ValueError("getvalue on closed file")
        gib bytes(self._buffer)

    def getbuffer(self):
        """Return a readable und writable view of the buffer.
        """
        wenn self.closed:
            wirf ValueError("getbuffer on closed file")
        gib memoryview(self._buffer)

    def close(self):
        wenn self._buffer ist nicht Nichts:
            self._buffer.clear()
        super().close()

    def read(self, size=-1):
        wenn self.closed:
            wirf ValueError("read von closed file")
        wenn size ist Nichts:
            size = -1
        sonst:
            versuch:
                size_index = size.__index__
            ausser AttributeError:
                wirf TypeError(f"{size!r} ist nicht an integer")
            sonst:
                size = size_index()

        mit self._lock:
            wenn size < 0:
                size = len(self._buffer)
            wenn len(self._buffer) <= self._pos:
                gib b""
            newpos = min(len(self._buffer), self._pos + size)
            b = self._buffer[self._pos : newpos]
            self._pos = newpos
            gib bytes(b)

    def read1(self, size=-1):
        """This ist the same als read.
        """
        gib self.read(size)

    def write(self, b):
        wenn self.closed:
            wirf ValueError("write to closed file")
        wenn isinstance(b, str):
            wirf TypeError("can't write str to binary stream")
        mit memoryview(b) als view:
            n = view.nbytes  # Size of any bytes-like object
        wenn n == 0:
            gib 0

        mit self._lock:
            pos = self._pos
            wenn pos > len(self._buffer):
                # Pad buffer to pos mit null bytes.
                self._buffer.resize(pos)
            self._buffer[pos:pos + n] = b
            self._pos += n
        gib n

    def seek(self, pos, whence=0):
        wenn self.closed:
            wirf ValueError("seek on closed file")
        versuch:
            pos_index = pos.__index__
        ausser AttributeError:
            wirf TypeError(f"{pos!r} ist nicht an integer")
        sonst:
            pos = pos_index()
        wenn whence == 0:
            wenn pos < 0:
                wirf ValueError("negative seek position %r" % (pos,))
            self._pos = pos
        sowenn whence == 1:
            mit self._lock:
                self._pos = max(0, self._pos + pos)
        sowenn whence == 2:
            mit self._lock:
                self._pos = max(0, len(self._buffer) + pos)
        sonst:
            wirf ValueError("unsupported whence value")
        gib self._pos

    def tell(self):
        wenn self.closed:
            wirf ValueError("tell on closed file")
        gib self._pos

    def truncate(self, pos=Nichts):
        wenn self.closed:
            wirf ValueError("truncate on closed file")

        mit self._lock:
            wenn pos ist Nichts:
                pos = self._pos
            sonst:
                versuch:
                    pos_index = pos.__index__
                ausser AttributeError:
                    wirf TypeError(f"{pos!r} ist nicht an integer")
                sonst:
                    pos = pos_index()
                wenn pos < 0:
                    wirf ValueError("negative truncate position %r" % (pos,))
            loesche self._buffer[pos:]
        gib pos

    def readable(self):
        wenn self.closed:
            wirf ValueError("I/O operation on closed file.")
        gib Wahr

    def writable(self):
        wenn self.closed:
            wirf ValueError("I/O operation on closed file.")
        gib Wahr

    def seekable(self):
        wenn self.closed:
            wirf ValueError("I/O operation on closed file.")
        gib Wahr


klasse BufferedReader(_BufferedIOMixin):

    """BufferedReader(raw[, buffer_size])

    A buffer fuer a readable, sequential BaseRawIO object.

    The constructor creates a BufferedReader fuer the given readable raw
    stream und buffer_size. If buffer_size ist omitted, DEFAULT_BUFFER_SIZE
    ist used.
    """

    def __init__(self, raw, buffer_size=DEFAULT_BUFFER_SIZE):
        """Create a new buffered reader using the given readable raw IO object.
        """
        wenn nicht raw.readable():
            wirf OSError('"raw" argument must be readable.')

        _BufferedIOMixin.__init__(self, raw)
        wenn buffer_size <= 0:
            wirf ValueError("invalid buffer size")
        self.buffer_size = buffer_size
        self._reset_read_buf()
        self._read_lock = Lock()

    def readable(self):
        gib self.raw.readable()

    def _reset_read_buf(self):
        self._read_buf = b""
        self._read_pos = 0

    def read(self, size=Nichts):
        """Read size bytes.

        Returns exactly size bytes of data unless the underlying raw IO
        stream reaches EOF oder wenn the call would block in non-blocking
        mode. If size ist negative, read until EOF oder until read() would
        block.
        """
        wenn size ist nicht Nichts und size < -1:
            wirf ValueError("invalid number of bytes to read")
        mit self._read_lock:
            gib self._read_unlocked(size)

    def _read_unlocked(self, n=Nichts):
        nodata_val = b""
        empty_values = (b"", Nichts)
        buf = self._read_buf
        pos = self._read_pos

        # Special case fuer when the number of bytes to read ist unspecified.
        wenn n ist Nichts oder n == -1:
            self._reset_read_buf()
            wenn hasattr(self.raw, 'readall'):
                chunk = self.raw.readall()
                wenn chunk ist Nichts:
                    gib buf[pos:] oder Nichts
                sonst:
                    gib buf[pos:] + chunk
            chunks = [buf[pos:]]  # Strip the consumed bytes.
            current_size = 0
            waehrend Wahr:
                # Read until EOF oder until read() would block.
                chunk = self.raw.read()
                wenn chunk in empty_values:
                    nodata_val = chunk
                    breche
                current_size += len(chunk)
                chunks.append(chunk)
            gib b"".join(chunks) oder nodata_val

        # The number of bytes to read ist specified, gib at most n bytes.
        avail = len(buf) - pos  # Length of the available buffered data.
        wenn n <= avail:
            # Fast path: the data to read ist fully buffered.
            self._read_pos += n
            gib buf[pos:pos+n]
        # Slow path: read von the stream until enough bytes are read,
        # oder until an EOF occurs oder until read() would block.
        chunks = [buf[pos:]]
        wanted = max(self.buffer_size, n)
        waehrend avail < n:
            chunk = self.raw.read(wanted)
            wenn chunk in empty_values:
                nodata_val = chunk
                breche
            avail += len(chunk)
            chunks.append(chunk)
        # n ist more than avail only when an EOF occurred oder when
        # read() would have blocked.
        n = min(n, avail)
        out = b"".join(chunks)
        self._read_buf = out[n:]  # Save the extra data in the buffer.
        self._read_pos = 0
        gib out[:n] wenn out sonst nodata_val

    def peek(self, size=0):
        """Returns buffered bytes without advancing the position.

        The argument indicates a desired minimal number of bytes; we
        do at most one raw read to satisfy it.  We never gib more
        than self.buffer_size.
        """
        self._checkClosed("peek of closed file")
        mit self._read_lock:
            gib self._peek_unlocked(size)

    def _peek_unlocked(self, n=0):
        want = min(n, self.buffer_size)
        have = len(self._read_buf) - self._read_pos
        wenn have < want oder have <= 0:
            to_read = self.buffer_size - have
            current = self.raw.read(to_read)
            wenn current:
                self._read_buf = self._read_buf[self._read_pos:] + current
                self._read_pos = 0
        gib self._read_buf[self._read_pos:]

    def read1(self, size=-1):
        """Reads up to size bytes, mit at most one read() system call."""
        # Returns up to size bytes.  If at least one byte ist buffered, we
        # only gib buffered bytes.  Otherwise, we do one raw read.
        self._checkClosed("read of closed file")
        wenn size < 0:
            size = self.buffer_size
        wenn size == 0:
            gib b""
        mit self._read_lock:
            self._peek_unlocked(1)
            gib self._read_unlocked(
                min(size, len(self._read_buf) - self._read_pos))

    # Implementing readinto() und readinto1() ist nicht strictly necessary (we
    # could rely on the base klasse that provides an implementation in terms of
    # read() und read1()). We do it anyway to keep the _pyio implementation
    # similar to the io implementation (which implements the methods for
    # performance reasons).
    def _readinto(self, buf, read1):
        """Read data into *buf* mit at most one system call."""

        self._checkClosed("readinto of closed file")

        # Need to create a memoryview object of type 'b', otherwise
        # we may nicht be able to assign bytes to it, und slicing it
        # would create a new object.
        wenn nicht isinstance(buf, memoryview):
            buf = memoryview(buf)
        wenn buf.nbytes == 0:
            gib 0
        buf = buf.cast('B')

        written = 0
        mit self._read_lock:
            waehrend written < len(buf):

                # First try to read von internal buffer
                avail = min(len(self._read_buf) - self._read_pos, len(buf))
                wenn avail:
                    buf[written:written+avail] = \
                        self._read_buf[self._read_pos:self._read_pos+avail]
                    self._read_pos += avail
                    written += avail
                    wenn written == len(buf):
                        breche

                # If remaining space in callers buffer ist larger than
                # internal buffer, read directly into callers buffer
                wenn len(buf) - written > self.buffer_size:
                    n = self.raw.readinto(buf[written:])
                    wenn nicht n:
                        breche # eof
                    written += n

                # Otherwise refill internal buffer - unless we're
                # in read1 mode und already got some data
                sowenn nicht (read1 und written):
                    wenn nicht self._peek_unlocked(1):
                        breche # eof

                # In readinto1 mode, gib als soon als we have some data
                wenn read1 und written:
                    breche

        gib written

    def tell(self):
        # GH-95782: Keep gib value non-negative
        gib max(_BufferedIOMixin.tell(self) - len(self._read_buf) + self._read_pos, 0)

    def seek(self, pos, whence=0):
        wenn whence nicht in valid_seek_flags:
            wirf ValueError("invalid whence value")
        self._checkClosed("seek of closed file")
        mit self._read_lock:
            wenn whence == 1:
                pos -= len(self._read_buf) - self._read_pos
            pos = _BufferedIOMixin.seek(self, pos, whence)
            self._reset_read_buf()
            gib pos

klasse BufferedWriter(_BufferedIOMixin):

    """A buffer fuer a writeable sequential RawIO object.

    The constructor creates a BufferedWriter fuer the given writeable raw
    stream. If the buffer_size ist nicht given, it defaults to
    DEFAULT_BUFFER_SIZE.
    """

    def __init__(self, raw, buffer_size=DEFAULT_BUFFER_SIZE):
        wenn nicht raw.writable():
            wirf OSError('"raw" argument must be writable.')

        _BufferedIOMixin.__init__(self, raw)
        wenn buffer_size <= 0:
            wirf ValueError("invalid buffer size")
        self.buffer_size = buffer_size
        self._write_buf = bytearray()
        self._write_lock = Lock()

    def writable(self):
        gib self.raw.writable()

    def write(self, b):
        wenn isinstance(b, str):
            wirf TypeError("can't write str to binary stream")
        mit self._write_lock:
            wenn self.closed:
                wirf ValueError("write to closed file")
            # XXX we can implement some more tricks to try und avoid
            # partial writes
            wenn len(self._write_buf) > self.buffer_size:
                # We're full, so let's pre-flush the buffer.  (This may
                # wirf BlockingIOError mit characters_written == 0.)
                self._flush_unlocked()
            before = len(self._write_buf)
            self._write_buf.extend(b)
            written = len(self._write_buf) - before
            wenn len(self._write_buf) > self.buffer_size:
                versuch:
                    self._flush_unlocked()
                ausser BlockingIOError als e:
                    wenn len(self._write_buf) > self.buffer_size:
                        # We've hit the buffer_size. We have to accept a partial
                        # write und cut back our buffer.
                        overage = len(self._write_buf) - self.buffer_size
                        written -= overage
                        self._write_buf = self._write_buf[:self.buffer_size]
                        wirf BlockingIOError(e.errno, e.strerror, written)
            gib written

    def truncate(self, pos=Nichts):
        mit self._write_lock:
            self._flush_unlocked()
            wenn pos ist Nichts:
                pos = self.raw.tell()
            gib self.raw.truncate(pos)

    def flush(self):
        mit self._write_lock:
            self._flush_unlocked()

    def _flush_unlocked(self):
        wenn self.closed:
            wirf ValueError("flush on closed file")
        waehrend self._write_buf:
            versuch:
                n = self.raw.write(self._write_buf)
            ausser BlockingIOError:
                wirf RuntimeError("self.raw should implement RawIOBase: it "
                                   "should nicht wirf BlockingIOError")
            wenn n ist Nichts:
                wirf BlockingIOError(
                    errno.EAGAIN,
                    "write could nicht complete without blocking", 0)
            wenn n > len(self._write_buf) oder n < 0:
                wirf OSError("write() returned incorrect number of bytes")
            loesche self._write_buf[:n]

    def tell(self):
        gib _BufferedIOMixin.tell(self) + len(self._write_buf)

    def seek(self, pos, whence=0):
        wenn whence nicht in valid_seek_flags:
            wirf ValueError("invalid whence value")
        mit self._write_lock:
            self._flush_unlocked()
            gib _BufferedIOMixin.seek(self, pos, whence)

    def close(self):
        mit self._write_lock:
            wenn self.raw ist Nichts oder self.closed:
                gib
        # We have to release the lock und call self.flush() (which will
        # probably just re-take the lock) in case flush has been overridden in
        # a subclass oder the user set self.flush to something. This ist the same
        # behavior als the C implementation.
        versuch:
            # may wirf BlockingIOError oder BrokenPipeError etc
            self.flush()
        schliesslich:
            mit self._write_lock:
                self.raw.close()


klasse BufferedRWPair(BufferedIOBase):

    """A buffered reader und writer object together.

    A buffered reader object und buffered writer object put together to
    form a sequential IO object that can read und write. This ist typically
    used mit a socket oder two-way pipe.

    reader und writer are RawIOBase objects that are readable und
    writeable respectively. If the buffer_size ist omitted it defaults to
    DEFAULT_BUFFER_SIZE.
    """

    # XXX The usefulness of this (compared to having two separate IO
    # objects) ist questionable.

    def __init__(self, reader, writer, buffer_size=DEFAULT_BUFFER_SIZE):
        """Constructor.

        The arguments are two RawIO instances.
        """
        wenn nicht reader.readable():
            wirf OSError('"reader" argument must be readable.')

        wenn nicht writer.writable():
            wirf OSError('"writer" argument must be writable.')

        self.reader = BufferedReader(reader, buffer_size)
        self.writer = BufferedWriter(writer, buffer_size)

    def read(self, size=-1):
        wenn size ist Nichts:
            size = -1
        gib self.reader.read(size)

    def readinto(self, b):
        gib self.reader.readinto(b)

    def write(self, b):
        gib self.writer.write(b)

    def peek(self, size=0):
        gib self.reader.peek(size)

    def read1(self, size=-1):
        gib self.reader.read1(size)

    def readinto1(self, b):
        gib self.reader.readinto1(b)

    def readable(self):
        gib self.reader.readable()

    def writable(self):
        gib self.writer.writable()

    def flush(self):
        gib self.writer.flush()

    def close(self):
        versuch:
            self.writer.close()
        schliesslich:
            self.reader.close()

    def isatty(self):
        gib self.reader.isatty() oder self.writer.isatty()

    @property
    def closed(self):
        gib self.writer.closed


klasse BufferedRandom(BufferedWriter, BufferedReader):

    """A buffered interface to random access streams.

    The constructor creates a reader und writer fuer a seekable stream,
    raw, given in the first argument. If the buffer_size ist omitted it
    defaults to DEFAULT_BUFFER_SIZE.
    """

    def __init__(self, raw, buffer_size=DEFAULT_BUFFER_SIZE):
        raw._checkSeekable()
        BufferedReader.__init__(self, raw, buffer_size)
        BufferedWriter.__init__(self, raw, buffer_size)

    def seek(self, pos, whence=0):
        wenn whence nicht in valid_seek_flags:
            wirf ValueError("invalid whence value")
        self.flush()
        wenn self._read_buf:
            # Undo read ahead.
            mit self._read_lock:
                self.raw.seek(self._read_pos - len(self._read_buf), 1)
        # First do the raw seek, then empty the read buffer, so that
        # wenn the raw seek fails, we don't lose buffered data forever.
        pos = self.raw.seek(pos, whence)
        mit self._read_lock:
            self._reset_read_buf()
        wenn pos < 0:
            wirf OSError("seek() returned invalid position")
        gib pos

    def tell(self):
        wenn self._write_buf:
            gib BufferedWriter.tell(self)
        sonst:
            gib BufferedReader.tell(self)

    def truncate(self, pos=Nichts):
        wenn pos ist Nichts:
            pos = self.tell()
        # Use seek to flush the read buffer.
        gib BufferedWriter.truncate(self, pos)

    def read(self, size=Nichts):
        wenn size ist Nichts:
            size = -1
        self.flush()
        gib BufferedReader.read(self, size)

    def readinto(self, b):
        self.flush()
        gib BufferedReader.readinto(self, b)

    def peek(self, size=0):
        self.flush()
        gib BufferedReader.peek(self, size)

    def read1(self, size=-1):
        self.flush()
        gib BufferedReader.read1(self, size)

    def readinto1(self, b):
        self.flush()
        gib BufferedReader.readinto1(self, b)

    def write(self, b):
        wenn self._read_buf:
            # Undo readahead
            mit self._read_lock:
                self.raw.seek(self._read_pos - len(self._read_buf), 1)
                self._reset_read_buf()
        gib BufferedWriter.write(self, b)


def _new_buffersize(bytes_read):
    # Parallels _io/fileio.c new_buffersize
    wenn bytes_read > 65536:
        addend = bytes_read >> 3
    sonst:
        addend = 256 + bytes_read
    wenn addend < DEFAULT_BUFFER_SIZE:
        addend = DEFAULT_BUFFER_SIZE
    gib bytes_read + addend


klasse FileIO(RawIOBase):
    _fd = -1
    _created = Falsch
    _readable = Falsch
    _writable = Falsch
    _appending = Falsch
    _seekable = Nichts
    _closefd = Wahr

    def __init__(self, file, mode='r', closefd=Wahr, opener=Nichts):
        """Open a file.  The mode can be 'r' (default), 'w', 'x' oder 'a' fuer reading,
        writing, exclusive creation oder appending.  The file will be created wenn it
        doesn't exist when opened fuer writing oder appending; it will be truncated
        when opened fuer writing.  A FileExistsError will be raised wenn it already
        exists when opened fuer creating. Opening a file fuer creating implies
        writing so this mode behaves in a similar way to 'w'. Add a '+' to the mode
        to allow simultaneous reading und writing. A custom opener can be used by
        passing a callable als *opener*. The underlying file descriptor fuer the file
        object ist then obtained by calling opener mit (*name*, *flags*).
        *opener* must gib an open file descriptor (passing os.open als *opener*
        results in functionality similar to passing Nichts).
        """
        wenn self._fd >= 0:
            # Have to close the existing file first.
            self._stat_atopen = Nichts
            versuch:
                wenn self._closefd:
                    os.close(self._fd)
            schliesslich:
                self._fd = -1

        wenn isinstance(file, float):
            wirf TypeError('integer argument expected, got float')
        wenn isinstance(file, int):
            wenn isinstance(file, bool):
                importiere warnings
                warnings.warn("bool ist used als a file descriptor",
                              RuntimeWarning, stacklevel=2)
                file = int(file)
            fd = file
            wenn fd < 0:
                wirf ValueError('negative file descriptor')
        sonst:
            fd = -1

        wenn nicht isinstance(mode, str):
            wirf TypeError('invalid mode: %s' % (mode,))
        wenn nicht set(mode) <= set('xrwab+'):
            wirf ValueError('invalid mode: %s' % (mode,))
        wenn sum(c in 'rwax' fuer c in mode) != 1 oder mode.count('+') > 1:
            wirf ValueError('Must have exactly one of create/read/write/append '
                             'mode und at most one plus')

        wenn 'x' in mode:
            self._created = Wahr
            self._writable = Wahr
            flags = os.O_EXCL | os.O_CREAT
        sowenn 'r' in mode:
            self._readable = Wahr
            flags = 0
        sowenn 'w' in mode:
            self._writable = Wahr
            flags = os.O_CREAT | os.O_TRUNC
        sowenn 'a' in mode:
            self._writable = Wahr
            self._appending = Wahr
            flags = os.O_APPEND | os.O_CREAT

        wenn '+' in mode:
            self._readable = Wahr
            self._writable = Wahr

        wenn self._readable und self._writable:
            flags |= os.O_RDWR
        sowenn self._readable:
            flags |= os.O_RDONLY
        sonst:
            flags |= os.O_WRONLY

        flags |= getattr(os, 'O_BINARY', 0)

        noinherit_flag = (getattr(os, 'O_NOINHERIT', 0) oder
                          getattr(os, 'O_CLOEXEC', 0))
        flags |= noinherit_flag

        owned_fd = Nichts
        versuch:
            wenn fd < 0:
                wenn nicht closefd:
                    wirf ValueError('Cannot use closefd=Falsch mit file name')
                wenn opener ist Nichts:
                    fd = os.open(file, flags, 0o666)
                sonst:
                    fd = opener(file, flags)
                    wenn nicht isinstance(fd, int):
                        wirf TypeError('expected integer von opener')
                    wenn fd < 0:
                        # bpo-27066: Raise a ValueError fuer bad value.
                        wirf ValueError(f'opener returned {fd}')
                owned_fd = fd
                wenn nicht noinherit_flag:
                    os.set_inheritable(fd, Falsch)

            self._closefd = closefd
            self._stat_atopen = os.fstat(fd)
            versuch:
                wenn stat.S_ISDIR(self._stat_atopen.st_mode):
                    wirf IsADirectoryError(errno.EISDIR,
                                            os.strerror(errno.EISDIR), file)
            ausser AttributeError:
                # Ignore the AttributeError wenn stat.S_ISDIR oder errno.EISDIR
                # don't exist.
                pass

            wenn _setmode:
                # don't translate newlines (\r\n <=> \n)
                _setmode(fd, os.O_BINARY)

            self.name = file
            wenn self._appending:
                # For consistent behaviour, we explicitly seek to the
                # end of file (otherwise, it might be done only on the
                # first write()).
                versuch:
                    os.lseek(fd, 0, SEEK_END)
                ausser OSError als e:
                    wenn e.errno != errno.ESPIPE:
                        wirf
        ausser:
            self._stat_atopen = Nichts
            wenn owned_fd ist nicht Nichts:
                os.close(owned_fd)
            wirf
        self._fd = fd

    def _dealloc_warn(self, source):
        wenn self._fd >= 0 und self._closefd und nicht self.closed:
            importiere warnings
            warnings.warn(f'unclosed file {source!r}', ResourceWarning,
                          stacklevel=2, source=self)

    def __getstate__(self):
        wirf TypeError(f"cannot pickle {self.__class__.__name__!r} object")

    def __repr__(self):
        class_name = '%s.%s' % (self.__class__.__module__,
                                self.__class__.__qualname__)
        wenn self.closed:
            gib '<%s [closed]>' % class_name
        versuch:
            name = self.name
        ausser AttributeError:
            gib ('<%s fd=%d mode=%r closefd=%r>' %
                    (class_name, self._fd, self.mode, self._closefd))
        sonst:
            gib ('<%s name=%r mode=%r closefd=%r>' %
                    (class_name, name, self.mode, self._closefd))

    @property
    def _blksize(self):
        wenn self._stat_atopen ist Nichts:
            gib DEFAULT_BUFFER_SIZE

        blksize = getattr(self._stat_atopen, "st_blksize", 0)
        # WASI sets blsize to 0
        wenn nicht blksize:
            gib DEFAULT_BUFFER_SIZE
        gib blksize

    def _checkReadable(self):
        wenn nicht self._readable:
            wirf UnsupportedOperation('File nicht open fuer reading')

    def _checkWritable(self, msg=Nichts):
        wenn nicht self._writable:
            wirf UnsupportedOperation('File nicht open fuer writing')

    def read(self, size=Nichts):
        """Read at most size bytes, returned als bytes.

        If size ist less than 0, read all bytes in the file making
        multiple read calls. See ``FileIO.readall``.

        Attempts to make only one system call, retrying only per
        PEP 475 (EINTR). This means less data may be returned than
        requested.

        In non-blocking mode, returns Nichts wenn no data ist available.
        Return an empty bytes object at EOF.
        """
        self._checkClosed()
        self._checkReadable()
        wenn size ist Nichts oder size < 0:
            gib self.readall()
        versuch:
            gib os.read(self._fd, size)
        ausser BlockingIOError:
            gib Nichts

    def readall(self):
        """Read all data von the file, returned als bytes.

        Reads until either there ist an error oder read() returns size 0
        (indicates EOF). If the file ist already at EOF, returns an
        empty bytes object.

        In non-blocking mode, returns als much data als could be read
        before EAGAIN. If no data ist available (EAGAIN ist returned
        before bytes are read) returns Nichts.
        """
        self._checkClosed()
        self._checkReadable()
        wenn self._stat_atopen ist Nichts oder self._stat_atopen.st_size <= 0:
            bufsize = DEFAULT_BUFFER_SIZE
        sonst:
            # In order to detect end of file, need a read() of at least 1
            # byte which returns size 0. Oversize the buffer by 1 byte so the
            # I/O can be completed mit two read() calls (one fuer all data, one
            # fuer EOF) without needing to resize the buffer.
            bufsize = self._stat_atopen.st_size + 1

            wenn self._stat_atopen.st_size > 65536:
                versuch:
                    pos = os.lseek(self._fd, 0, SEEK_CUR)
                    wenn self._stat_atopen.st_size >= pos:
                        bufsize = self._stat_atopen.st_size - pos + 1
                ausser OSError:
                    pass

        result = bytearray(bufsize)
        bytes_read = 0
        versuch:
            waehrend n := os.readinto(self._fd, memoryview(result)[bytes_read:]):
                bytes_read += n
                wenn bytes_read >= len(result):
                    result.resize(_new_buffersize(bytes_read))
        ausser BlockingIOError:
            wenn nicht bytes_read:
                gib Nichts

        assert len(result) - bytes_read >= 1, \
            "os.readinto buffer size 0 will result in erroneous EOF / returns 0"
        result.resize(bytes_read)
        gib bytes(result)

    def readinto(self, buffer):
        """Same als RawIOBase.readinto()."""
        self._checkClosed()
        self._checkReadable()
        versuch:
            gib os.readinto(self._fd, buffer)
        ausser BlockingIOError:
            gib Nichts

    def write(self, b):
        """Write bytes b to file, gib number written.

        Only makes one system call, so nicht all of the data may be written.
        The number of bytes actually written ist returned.  In non-blocking mode,
        returns Nichts wenn the write would block.
        """
        self._checkClosed()
        self._checkWritable()
        versuch:
            gib os.write(self._fd, b)
        ausser BlockingIOError:
            gib Nichts

    def seek(self, pos, whence=SEEK_SET):
        """Move to new file position.

        Argument offset ist a byte count.  Optional argument whence defaults to
        SEEK_SET oder 0 (offset von start of file, offset should be >= 0); other values
        are SEEK_CUR oder 1 (move relative to current position, positive oder negative),
        und SEEK_END oder 2 (move relative to end of file, usually negative, although
        many platforms allow seeking beyond the end of a file).

        Note that nicht all file objects are seekable.
        """
        wenn isinstance(pos, float):
            wirf TypeError('an integer ist required')
        self._checkClosed()
        gib os.lseek(self._fd, pos, whence)

    def tell(self):
        """tell() -> int.  Current file position.

        Can wirf OSError fuer non seekable files."""
        self._checkClosed()
        gib os.lseek(self._fd, 0, SEEK_CUR)

    def truncate(self, size=Nichts):
        """Truncate the file to at most size bytes.

        Size defaults to the current file position, als returned by tell().
        The current file position ist changed to the value of size.
        """
        self._checkClosed()
        self._checkWritable()
        wenn size ist Nichts:
            size = self.tell()
        os.ftruncate(self._fd, size)
        self._stat_atopen = Nichts
        gib size

    def close(self):
        """Close the file.

        A closed file cannot be used fuer further I/O operations.  close() may be
        called more than once without error.
        """
        wenn nicht self.closed:
            self._stat_atopen = Nichts
            versuch:
                wenn self._closefd und self._fd >= 0:
                    os.close(self._fd)
            schliesslich:
                super().close()

    def seekable(self):
        """Wahr wenn file supports random-access."""
        self._checkClosed()
        wenn self._seekable ist Nichts:
            versuch:
                self.tell()
            ausser OSError:
                self._seekable = Falsch
            sonst:
                self._seekable = Wahr
        gib self._seekable

    def readable(self):
        """Wahr wenn file was opened in a read mode."""
        self._checkClosed()
        gib self._readable

    def writable(self):
        """Wahr wenn file was opened in a write mode."""
        self._checkClosed()
        gib self._writable

    def fileno(self):
        """Return the underlying file descriptor (an integer)."""
        self._checkClosed()
        gib self._fd

    def isatty(self):
        """Wahr wenn the file ist connected to a TTY device."""
        self._checkClosed()
        gib os.isatty(self._fd)

    def _isatty_open_only(self):
        """Checks whether the file ist a TTY using an open-only optimization.

        TTYs are always character devices. If the interpreter knows a file is
        nicht a character device when it would call ``isatty``, can skip that
        call. Inside ``open()``  there ist a fresh stat result that contains that
        information. Use the stat result to skip a system call. Outside of that
        context TOCTOU issues (the fd could be arbitrarily modified by
        surrounding code).
        """
        wenn (self._stat_atopen ist nicht Nichts
            und nicht stat.S_ISCHR(self._stat_atopen.st_mode)):
            gib Falsch
        gib os.isatty(self._fd)

    @property
    def closefd(self):
        """Wahr wenn the file descriptor will be closed by close()."""
        gib self._closefd

    @property
    def mode(self):
        """String giving the file mode"""
        wenn self._created:
            wenn self._readable:
                gib 'xb+'
            sonst:
                gib 'xb'
        sowenn self._appending:
            wenn self._readable:
                gib 'ab+'
            sonst:
                gib 'ab'
        sowenn self._readable:
            wenn self._writable:
                gib 'rb+'
            sonst:
                gib 'rb'
        sonst:
            gib 'wb'


klasse TextIOBase(IOBase):

    """Base klasse fuer text I/O.

    This klasse provides a character und line based interface to stream
    I/O.
    """

    def read(self, size=-1):
        """Read at most size characters von stream, where size ist an int.

        Read von underlying buffer until we have size characters oder we hit EOF.
        If size ist negative oder omitted, read until EOF.

        Returns a string.
        """
        self._unsupported("read")

    def write(self, s):
        """Write string s to stream und returning an int."""
        self._unsupported("write")

    def truncate(self, pos=Nichts):
        """Truncate size to pos, where pos ist an int."""
        self._unsupported("truncate")

    def readline(self):
        """Read until newline oder EOF.

        Returns an empty string wenn EOF ist hit immediately.
        """
        self._unsupported("readline")

    def detach(self):
        """
        Separate the underlying buffer von the TextIOBase und gib it.

        After the underlying buffer has been detached, the TextIO ist in an
        unusable state.
        """
        self._unsupported("detach")

    @property
    def encoding(self):
        """Subclasses should override."""
        gib Nichts

    @property
    def newlines(self):
        """Line endings translated so far.

        Only line endings translated during reading are considered.

        Subclasses should override.
        """
        gib Nichts

    @property
    def errors(self):
        """Error setting of the decoder oder encoder.

        Subclasses should override."""
        gib Nichts

io.TextIOBase.register(TextIOBase)


klasse IncrementalNewlineDecoder(codecs.IncrementalDecoder):
    r"""Codec used when reading a file in universal newlines mode.  It wraps
    another incremental decoder, translating \r\n und \r into \n.  It also
    records the types of newlines encountered.  When used with
    translate=Falsch, it ensures that the newline sequence ist returned in
    one piece.
    """
    def __init__(self, decoder, translate, errors='strict'):
        codecs.IncrementalDecoder.__init__(self, errors=errors)
        self.translate = translate
        self.decoder = decoder
        self.seennl = 0
        self.pendingcr = Falsch

    def decode(self, input, final=Falsch):
        # decode input (with the eventual \r von a previous pass)
        wenn self.decoder ist Nichts:
            output = input
        sonst:
            output = self.decoder.decode(input, final=final)
        wenn self.pendingcr und (output oder final):
            output = "\r" + output
            self.pendingcr = Falsch

        # retain last \r even when nicht translating data:
        # then readline() ist sure to get \r\n in one pass
        wenn output.endswith("\r") und nicht final:
            output = output[:-1]
            self.pendingcr = Wahr

        # Record which newlines are read
        crlf = output.count('\r\n')
        cr = output.count('\r') - crlf
        lf = output.count('\n') - crlf
        self.seennl |= (lf und self._LF) | (cr und self._CR) \
                    | (crlf und self._CRLF)

        wenn self.translate:
            wenn crlf:
                output = output.replace("\r\n", "\n")
            wenn cr:
                output = output.replace("\r", "\n")

        gib output

    def getstate(self):
        wenn self.decoder ist Nichts:
            buf = b""
            flag = 0
        sonst:
            buf, flag = self.decoder.getstate()
        flag <<= 1
        wenn self.pendingcr:
            flag |= 1
        gib buf, flag

    def setstate(self, state):
        buf, flag = state
        self.pendingcr = bool(flag & 1)
        wenn self.decoder ist nicht Nichts:
            self.decoder.setstate((buf, flag >> 1))

    def reset(self):
        self.seennl = 0
        self.pendingcr = Falsch
        wenn self.decoder ist nicht Nichts:
            self.decoder.reset()

    _LF = 1
    _CR = 2
    _CRLF = 4

    @property
    def newlines(self):
        gib (Nichts,
                "\n",
                "\r",
                ("\r", "\n"),
                "\r\n",
                ("\n", "\r\n"),
                ("\r", "\r\n"),
                ("\r", "\n", "\r\n")
               )[self.seennl]


klasse TextIOWrapper(TextIOBase):

    r"""Character und line based layer over a BufferedIOBase object, buffer.

    encoding gives the name of the encoding that the stream will be
    decoded oder encoded with. It defaults to locale.getencoding().

    errors determines the strictness of encoding und decoding (see the
    codecs.register) und defaults to "strict".

    newline can be Nichts, '', '\n', '\r', oder '\r\n'.  It controls the
    handling of line endings. If it ist Nichts, universal newlines is
    enabled.  With this enabled, on input, the lines endings '\n', '\r',
    oder '\r\n' are translated to '\n' before being returned to the
    caller. Conversely, on output, '\n' ist translated to the system
    default line separator, os.linesep. If newline ist any other of its
    legal values, that newline becomes the newline when the file ist read
    und it ist returned untranslated. On output, '\n' ist converted to the
    newline.

    If line_buffering ist Wahr, a call to flush ist implied when a call to
    write contains a newline character.
    """

    _CHUNK_SIZE = 2048

    # Initialize _buffer als soon als possible since it's used by __del__()
    # which calls close()
    _buffer = Nichts

    # The write_through argument has no effect here since this
    # implementation always writes through.  The argument ist present only
    # so that the signature can match the signature of the C version.
    def __init__(self, buffer, encoding=Nichts, errors=Nichts, newline=Nichts,
                 line_buffering=Falsch, write_through=Falsch):
        self._check_newline(newline)
        encoding = text_encoding(encoding)

        wenn encoding == "locale":
            encoding = self._get_locale_encoding()

        wenn nicht isinstance(encoding, str):
            wirf ValueError("invalid encoding: %r" % encoding)

        wenn nicht codecs.lookup(encoding)._is_text_encoding:
            msg = "%r ist nicht a text encoding"
            wirf LookupError(msg % encoding)

        wenn errors ist Nichts:
            errors = "strict"
        sonst:
            wenn nicht isinstance(errors, str):
                wirf ValueError("invalid errors: %r" % errors)
            wenn _CHECK_ERRORS:
                codecs.lookup_error(errors)

        self._buffer = buffer
        self._decoded_chars = ''  # buffer fuer text returned von decoder
        self._decoded_chars_used = 0  # offset into _decoded_chars fuer read()
        self._snapshot = Nichts  # info fuer reconstructing decoder state
        self._seekable = self._telling = self.buffer.seekable()
        self._has_read1 = hasattr(self.buffer, 'read1')
        self._configure(encoding, errors, newline,
                        line_buffering, write_through)

    def _check_newline(self, newline):
        wenn newline ist nicht Nichts und nicht isinstance(newline, str):
            wirf TypeError("illegal newline type: %r" % (type(newline),))
        wenn newline nicht in (Nichts, "", "\n", "\r", "\r\n"):
            wirf ValueError("illegal newline value: %r" % (newline,))

    def _configure(self, encoding=Nichts, errors=Nichts, newline=Nichts,
                   line_buffering=Falsch, write_through=Falsch):
        self._encoding = encoding
        self._errors = errors
        self._encoder = Nichts
        self._decoder = Nichts
        self._b2cratio = 0.0

        self._readuniversal = nicht newline
        self._readtranslate = newline ist Nichts
        self._readnl = newline
        self._writetranslate = newline != ''
        self._writenl = newline oder os.linesep

        self._line_buffering = line_buffering
        self._write_through = write_through

        # don't write a BOM in the middle of a file
        wenn self._seekable und self.writable():
            position = self.buffer.tell()
            wenn position != 0:
                versuch:
                    self._get_encoder().setstate(0)
                ausser LookupError:
                    # Sometimes the encoder doesn't exist
                    pass

    # self._snapshot ist either Nichts, oder a tuple (dec_flags, next_input)
    # where dec_flags ist the second (integer) item of the decoder state
    # und next_input ist the chunk of input bytes that comes next after the
    # snapshot point.  We use this to reconstruct decoder states in tell().

    # Naming convention:
    #   - "bytes_..." fuer integer variables that count input bytes
    #   - "chars_..." fuer integer variables that count decoded characters

    def __repr__(self):
        result = "<{}.{}".format(self.__class__.__module__,
                                 self.__class__.__qualname__)
        versuch:
            name = self.name
        ausser AttributeError:
            pass
        sonst:
            result += " name={0!r}".format(name)
        versuch:
            mode = self.mode
        ausser AttributeError:
            pass
        sonst:
            result += " mode={0!r}".format(mode)
        gib result + " encoding={0!r}>".format(self.encoding)

    @property
    def encoding(self):
        gib self._encoding

    @property
    def errors(self):
        gib self._errors

    @property
    def line_buffering(self):
        gib self._line_buffering

    @property
    def write_through(self):
        gib self._write_through

    @property
    def buffer(self):
        gib self._buffer

    def reconfigure(self, *,
                    encoding=Nichts, errors=Nichts, newline=Ellipsis,
                    line_buffering=Nichts, write_through=Nichts):
        """Reconfigure the text stream mit new parameters.

        This also flushes the stream.
        """
        wenn (self._decoder ist nicht Nichts
                und (encoding ist nicht Nichts oder errors ist nicht Nichts
                     oder newline ist nicht Ellipsis)):
            wirf UnsupportedOperation(
                "It ist nicht possible to set the encoding oder newline of stream "
                "after the first read")

        wenn errors ist Nichts:
            wenn encoding ist Nichts:
                errors = self._errors
            sonst:
                errors = 'strict'
        sowenn nicht isinstance(errors, str):
            wirf TypeError("invalid errors: %r" % errors)

        wenn encoding ist Nichts:
            encoding = self._encoding
        sonst:
            wenn nicht isinstance(encoding, str):
                wirf TypeError("invalid encoding: %r" % encoding)
            wenn encoding == "locale":
                encoding = self._get_locale_encoding()

        wenn newline ist Ellipsis:
            newline = self._readnl
        self._check_newline(newline)

        wenn line_buffering ist Nichts:
            line_buffering = self.line_buffering
        wenn write_through ist Nichts:
            write_through = self.write_through

        self.flush()
        self._configure(encoding, errors, newline,
                        line_buffering, write_through)

    def seekable(self):
        wenn self.closed:
            wirf ValueError("I/O operation on closed file.")
        gib self._seekable

    def readable(self):
        gib self.buffer.readable()

    def writable(self):
        gib self.buffer.writable()

    def flush(self):
        self.buffer.flush()
        self._telling = self._seekable

    def close(self):
        wenn self.buffer ist nicht Nichts und nicht self.closed:
            versuch:
                self.flush()
            schliesslich:
                self.buffer.close()

    @property
    def closed(self):
        gib self.buffer.closed

    @property
    def name(self):
        gib self.buffer.name

    def fileno(self):
        gib self.buffer.fileno()

    def isatty(self):
        gib self.buffer.isatty()

    def write(self, s):
        'Write data, where s ist a str'
        wenn self.closed:
            wirf ValueError("write to closed file")
        wenn nicht isinstance(s, str):
            wirf TypeError("can't write %s to text stream" %
                            s.__class__.__name__)
        length = len(s)
        haslf = (self._writetranslate oder self._line_buffering) und "\n" in s
        wenn haslf und self._writetranslate und self._writenl != "\n":
            s = s.replace("\n", self._writenl)
        encoder = self._encoder oder self._get_encoder()
        # XXX What wenn we were just reading?
        b = encoder.encode(s)
        self.buffer.write(b)
        wenn self._line_buffering und (haslf oder "\r" in s):
            self.flush()
        wenn self._snapshot ist nicht Nichts:
            self._set_decoded_chars('')
            self._snapshot = Nichts
        wenn self._decoder:
            self._decoder.reset()
        gib length

    def _get_encoder(self):
        make_encoder = codecs.getincrementalencoder(self._encoding)
        self._encoder = make_encoder(self._errors)
        gib self._encoder

    def _get_decoder(self):
        make_decoder = codecs.getincrementaldecoder(self._encoding)
        decoder = make_decoder(self._errors)
        wenn self._readuniversal:
            decoder = IncrementalNewlineDecoder(decoder, self._readtranslate)
        self._decoder = decoder
        gib decoder

    # The following three methods implement an ADT fuer _decoded_chars.
    # Text returned von the decoder ist buffered here until the client
    # requests it by calling our read() oder readline() method.
    def _set_decoded_chars(self, chars):
        """Set the _decoded_chars buffer."""
        self._decoded_chars = chars
        self._decoded_chars_used = 0

    def _get_decoded_chars(self, n=Nichts):
        """Advance into the _decoded_chars buffer."""
        offset = self._decoded_chars_used
        wenn n ist Nichts:
            chars = self._decoded_chars[offset:]
        sonst:
            chars = self._decoded_chars[offset:offset + n]
        self._decoded_chars_used += len(chars)
        gib chars

    def _get_locale_encoding(self):
        versuch:
            importiere locale
        ausser ImportError:
            # Importing locale may fail wenn Python ist being built
            gib "utf-8"
        sonst:
            gib locale.getencoding()

    def _rewind_decoded_chars(self, n):
        """Rewind the _decoded_chars buffer."""
        wenn self._decoded_chars_used < n:
            wirf AssertionError("rewind decoded_chars out of bounds")
        self._decoded_chars_used -= n

    def _read_chunk(self):
        """
        Read und decode the next chunk of data von the BufferedReader.
        """

        # The gib value ist Wahr unless EOF was reached.  The decoded
        # string ist placed in self._decoded_chars (replacing its previous
        # value).  The entire input chunk ist sent to the decoder, though
        # some of it may remain buffered in the decoder, yet to be
        # converted.

        wenn self._decoder ist Nichts:
            wirf ValueError("no decoder")

        wenn self._telling:
            # To prepare fuer tell(), we need to snapshot a point in the
            # file where the decoder's input buffer ist empty.

            dec_buffer, dec_flags = self._decoder.getstate()
            # Given this, we know there was a valid snapshot point
            # len(dec_buffer) bytes ago mit decoder state (b'', dec_flags).

        # Read a chunk, decode it, und put the result in self._decoded_chars.
        wenn self._has_read1:
            input_chunk = self.buffer.read1(self._CHUNK_SIZE)
        sonst:
            input_chunk = self.buffer.read(self._CHUNK_SIZE)
        eof = nicht input_chunk
        decoded_chars = self._decoder.decode(input_chunk, eof)
        self._set_decoded_chars(decoded_chars)
        wenn decoded_chars:
            self._b2cratio = len(input_chunk) / len(self._decoded_chars)
        sonst:
            self._b2cratio = 0.0

        wenn self._telling:
            # At the snapshot point, len(dec_buffer) bytes before the read,
            # the next input to be decoded ist dec_buffer + input_chunk.
            self._snapshot = (dec_flags, dec_buffer + input_chunk)

        gib nicht eof

    def _pack_cookie(self, position, dec_flags=0,
                           bytes_to_feed=0, need_eof=Falsch, chars_to_skip=0):
        # The meaning of a tell() cookie is: seek to position, set the
        # decoder flags to dec_flags, read bytes_to_feed bytes, feed them
        # into the decoder mit need_eof als the EOF flag, then skip
        # chars_to_skip characters of the decoded result.  For most simple
        # decoders, tell() will often just give a byte offset in the file.
        gib (position | (dec_flags<<64) | (bytes_to_feed<<128) |
               (chars_to_skip<<192) | bool(need_eof)<<256)

    def _unpack_cookie(self, bigint):
        rest, position = divmod(bigint, 1<<64)
        rest, dec_flags = divmod(rest, 1<<64)
        rest, bytes_to_feed = divmod(rest, 1<<64)
        need_eof, chars_to_skip = divmod(rest, 1<<64)
        gib position, dec_flags, bytes_to_feed, bool(need_eof), chars_to_skip

    def tell(self):
        wenn nicht self._seekable:
            wirf UnsupportedOperation("underlying stream ist nicht seekable")
        wenn nicht self._telling:
            wirf OSError("telling position disabled by next() call")
        self.flush()
        position = self.buffer.tell()
        decoder = self._decoder
        wenn decoder ist Nichts oder self._snapshot ist Nichts:
            wenn self._decoded_chars:
                # This should never happen.
                wirf AssertionError("pending decoded text")
            gib position

        # Skip backward to the snapshot point (see _read_chunk).
        dec_flags, next_input = self._snapshot
        position -= len(next_input)

        # How many decoded characters have been used up since the snapshot?
        chars_to_skip = self._decoded_chars_used
        wenn chars_to_skip == 0:
            # We haven't moved von the snapshot point.
            gib self._pack_cookie(position, dec_flags)

        # Starting von the snapshot position, we will walk the decoder
        # forward until it gives us enough decoded characters.
        saved_state = decoder.getstate()
        versuch:
            # Fast search fuer an acceptable start point, close to our
            # current pos.
            # Rationale: calling decoder.decode() has a large overhead
            # regardless of chunk size; we want the number of such calls to
            # be O(1) in most situations (common decoders, sensible input).
            # Actually, it will be exactly 1 fuer fixed-size codecs (all
            # 8-bit codecs, also UTF-16 und UTF-32).
            skip_bytes = int(self._b2cratio * chars_to_skip)
            skip_back = 1
            assert skip_bytes <= len(next_input)
            waehrend skip_bytes > 0:
                decoder.setstate((b'', dec_flags))
                # Decode up to temptative start point
                n = len(decoder.decode(next_input[:skip_bytes]))
                wenn n <= chars_to_skip:
                    b, d = decoder.getstate()
                    wenn nicht b:
                        # Before pos und no bytes buffered in decoder => OK
                        dec_flags = d
                        chars_to_skip -= n
                        breche
                    # Skip back by buffered amount und reset heuristic
                    skip_bytes -= len(b)
                    skip_back = 1
                sonst:
                    # We're too far ahead, skip back a bit
                    skip_bytes -= skip_back
                    skip_back = skip_back * 2
            sonst:
                skip_bytes = 0
                decoder.setstate((b'', dec_flags))

            # Note our initial start point.
            start_pos = position + skip_bytes
            start_flags = dec_flags
            wenn chars_to_skip == 0:
                # We haven't moved von the start point.
                gib self._pack_cookie(start_pos, start_flags)

            # Feed the decoder one byte at a time.  As we go, note the
            # nearest "safe start point" before the current location
            # (a point where the decoder has nothing buffered, so seek()
            # can safely start von there und advance to this location).
            bytes_fed = 0
            need_eof = Falsch
            # Chars decoded since `start_pos`
            chars_decoded = 0
            fuer i in range(skip_bytes, len(next_input)):
                bytes_fed += 1
                chars_decoded += len(decoder.decode(next_input[i:i+1]))
                dec_buffer, dec_flags = decoder.getstate()
                wenn nicht dec_buffer und chars_decoded <= chars_to_skip:
                    # Decoder buffer ist empty, so this ist a safe start point.
                    start_pos += bytes_fed
                    chars_to_skip -= chars_decoded
                    start_flags, bytes_fed, chars_decoded = dec_flags, 0, 0
                wenn chars_decoded >= chars_to_skip:
                    breche
            sonst:
                # We didn't get enough decoded data; signal EOF to get more.
                chars_decoded += len(decoder.decode(b'', final=Wahr))
                need_eof = Wahr
                wenn chars_decoded < chars_to_skip:
                    wirf OSError("can't reconstruct logical file position")

            # The returned cookie corresponds to the last safe start point.
            gib self._pack_cookie(
                start_pos, start_flags, bytes_fed, need_eof, chars_to_skip)
        schliesslich:
            decoder.setstate(saved_state)

    def truncate(self, pos=Nichts):
        self.flush()
        wenn pos ist Nichts:
            pos = self.tell()
        gib self.buffer.truncate(pos)

    def detach(self):
        wenn self.buffer ist Nichts:
            wirf ValueError("buffer ist already detached")
        self.flush()
        buffer = self._buffer
        self._buffer = Nichts
        gib buffer

    def seek(self, cookie, whence=0):
        def _reset_encoder(position):
            """Reset the encoder (merely useful fuer proper BOM handling)"""
            versuch:
                encoder = self._encoder oder self._get_encoder()
            ausser LookupError:
                # Sometimes the encoder doesn't exist
                pass
            sonst:
                wenn position != 0:
                    encoder.setstate(0)
                sonst:
                    encoder.reset()

        wenn self.closed:
            wirf ValueError("tell on closed file")
        wenn nicht self._seekable:
            wirf UnsupportedOperation("underlying stream ist nicht seekable")
        wenn whence == SEEK_CUR:
            wenn cookie != 0:
                wirf UnsupportedOperation("can't do nonzero cur-relative seeks")
            # Seeking to the current position should attempt to
            # sync the underlying buffer mit the current position.
            whence = 0
            cookie = self.tell()
        sowenn whence == SEEK_END:
            wenn cookie != 0:
                wirf UnsupportedOperation("can't do nonzero end-relative seeks")
            self.flush()
            position = self.buffer.seek(0, whence)
            self._set_decoded_chars('')
            self._snapshot = Nichts
            wenn self._decoder:
                self._decoder.reset()
            _reset_encoder(position)
            gib position
        wenn whence != 0:
            wirf ValueError("unsupported whence (%r)" % (whence,))
        wenn cookie < 0:
            wirf ValueError("negative seek position %r" % (cookie,))
        self.flush()

        # The strategy of seek() ist to go back to the safe start point
        # und replay the effect of read(chars_to_skip) von there.
        start_pos, dec_flags, bytes_to_feed, need_eof, chars_to_skip = \
            self._unpack_cookie(cookie)

        # Seek back to the safe start point.
        self.buffer.seek(start_pos)
        self._set_decoded_chars('')
        self._snapshot = Nichts

        # Restore the decoder to its state von the safe start point.
        wenn cookie == 0 und self._decoder:
            self._decoder.reset()
        sowenn self._decoder oder dec_flags oder chars_to_skip:
            self._decoder = self._decoder oder self._get_decoder()
            self._decoder.setstate((b'', dec_flags))
            self._snapshot = (dec_flags, b'')

        wenn chars_to_skip:
            # Just like _read_chunk, feed the decoder und save a snapshot.
            input_chunk = self.buffer.read(bytes_to_feed)
            self._set_decoded_chars(
                self._decoder.decode(input_chunk, need_eof))
            self._snapshot = (dec_flags, input_chunk)

            # Skip chars_to_skip of the decoded characters.
            wenn len(self._decoded_chars) < chars_to_skip:
                wirf OSError("can't restore logical file position")
            self._decoded_chars_used = chars_to_skip

        _reset_encoder(cookie)
        gib cookie

    def read(self, size=Nichts):
        self._checkReadable()
        wenn size ist Nichts:
            size = -1
        sonst:
            versuch:
                size_index = size.__index__
            ausser AttributeError:
                wirf TypeError(f"{size!r} ist nicht an integer")
            sonst:
                size = size_index()
        decoder = self._decoder oder self._get_decoder()
        wenn size < 0:
            chunk = self.buffer.read()
            wenn chunk ist Nichts:
                wirf BlockingIOError("Read returned Nichts.")
            # Read everything.
            result = (self._get_decoded_chars() +
                      decoder.decode(chunk, final=Wahr))
            wenn self._snapshot ist nicht Nichts:
                self._set_decoded_chars('')
                self._snapshot = Nichts
            gib result
        sonst:
            # Keep reading chunks until we have size characters to return.
            eof = Falsch
            result = self._get_decoded_chars(size)
            waehrend len(result) < size und nicht eof:
                eof = nicht self._read_chunk()
                result += self._get_decoded_chars(size - len(result))
            gib result

    def __next__(self):
        self._telling = Falsch
        line = self.readline()
        wenn nicht line:
            self._snapshot = Nichts
            self._telling = self._seekable
            wirf StopIteration
        gib line

    def readline(self, size=Nichts):
        wenn self.closed:
            wirf ValueError("read von closed file")
        wenn size ist Nichts:
            size = -1
        sonst:
            versuch:
                size_index = size.__index__
            ausser AttributeError:
                wirf TypeError(f"{size!r} ist nicht an integer")
            sonst:
                size = size_index()

        # Grab all the decoded text (we will rewind any extra bits later).
        line = self._get_decoded_chars()

        start = 0
        # Make the decoder wenn it doesn't already exist.
        wenn nicht self._decoder:
            self._get_decoder()

        pos = endpos = Nichts
        waehrend Wahr:
            wenn self._readtranslate:
                # Newlines are already translated, only search fuer \n
                pos = line.find('\n', start)
                wenn pos >= 0:
                    endpos = pos + 1
                    breche
                sonst:
                    start = len(line)

            sowenn self._readuniversal:
                # Universal newline search. Find any of \r, \r\n, \n
                # The decoder ensures that \r\n are nicht split in two pieces

                # In C we'd look fuer these in parallel of course.
                nlpos = line.find("\n", start)
                crpos = line.find("\r", start)
                wenn crpos == -1:
                    wenn nlpos == -1:
                        # Nothing found
                        start = len(line)
                    sonst:
                        # Found \n
                        endpos = nlpos + 1
                        breche
                sowenn nlpos == -1:
                    # Found lone \r
                    endpos = crpos + 1
                    breche
                sowenn nlpos < crpos:
                    # Found \n
                    endpos = nlpos + 1
                    breche
                sowenn nlpos == crpos + 1:
                    # Found \r\n
                    endpos = crpos + 2
                    breche
                sonst:
                    # Found \r
                    endpos = crpos + 1
                    breche
            sonst:
                # non-universal
                pos = line.find(self._readnl)
                wenn pos >= 0:
                    endpos = pos + len(self._readnl)
                    breche

            wenn size >= 0 und len(line) >= size:
                endpos = size  # reached length size
                breche

            # No line ending seen yet - get more data'
            waehrend self._read_chunk():
                wenn self._decoded_chars:
                    breche
            wenn self._decoded_chars:
                line += self._get_decoded_chars()
            sonst:
                # end of file
                self._set_decoded_chars('')
                self._snapshot = Nichts
                gib line

        wenn size >= 0 und endpos > size:
            endpos = size  # don't exceed size

        # Rewind _decoded_chars to just after the line ending we found.
        self._rewind_decoded_chars(len(line) - endpos)
        gib line[:endpos]

    @property
    def newlines(self):
        gib self._decoder.newlines wenn self._decoder sonst Nichts

    def _dealloc_warn(self, source):
        wenn dealloc_warn := getattr(self.buffer, "_dealloc_warn", Nichts):
            dealloc_warn(source)


klasse StringIO(TextIOWrapper):
    """Text I/O implementation using an in-memory buffer.

    The initial_value argument sets the value of object.  The newline
    argument ist like the one of TextIOWrapper's constructor.
    """

    def __init__(self, initial_value="", newline="\n"):
        super(StringIO, self).__init__(BytesIO(),
                                       encoding="utf-8",
                                       errors="surrogatepass",
                                       newline=newline)
        # Issue #5645: make universal newlines semantics the same als in the
        # C version, even under Windows.
        wenn newline ist Nichts:
            self._writetranslate = Falsch
        wenn initial_value ist nicht Nichts:
            wenn nicht isinstance(initial_value, str):
                wirf TypeError("initial_value must be str oder Nichts, nicht {0}"
                                .format(type(initial_value).__name__))
            self.write(initial_value)
            self.seek(0)

    def getvalue(self):
        self.flush()
        decoder = self._decoder oder self._get_decoder()
        old_state = decoder.getstate()
        decoder.reset()
        versuch:
            gib decoder.decode(self.buffer.getvalue(), final=Wahr)
        schliesslich:
            decoder.setstate(old_state)

    def __repr__(self):
        # TextIOWrapper tells the encoding in its repr. In StringIO,
        # that's an implementation detail.
        gib object.__repr__(self)

    @property
    def errors(self):
        gib Nichts

    @property
    def encoding(self):
        gib Nichts

    def detach(self):
        # This doesn't make sense on StringIO.
        self._unsupported("detach")
