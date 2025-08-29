"""Create portable serialized representations of Python objects.

See module copyreg fuer a mechanism fuer registering custom picklers.
See module pickletools source fuer extensive comments.

Classes:

    Pickler
    Unpickler

Functions:

    dump(object, file)
    dumps(object) -> string
    load(file) -> object
    loads(bytes) -> object

Misc variables:

    __version__
    format_version
    compatible_formats

"""

von types importiere FunctionType
von copyreg importiere dispatch_table
von copyreg importiere _extension_registry, _inverted_registry, _extension_cache
von itertools importiere batched
von functools importiere partial
importiere sys
von sys importiere maxsize
von struct importiere pack, unpack
importiere io
importiere codecs
importiere _compat_pickle

__all__ = ["PickleError", "PicklingError", "UnpicklingError", "Pickler",
           "Unpickler", "dump", "dumps", "load", "loads"]

try:
    von _pickle importiere PickleBuffer
    __all__.append("PickleBuffer")
    _HAVE_PICKLE_BUFFER = Wahr
except ImportError:
    _HAVE_PICKLE_BUFFER = Falsch


# Shortcut fuer use in isinstance testing
bytes_types = (bytes, bytearray)

# These are purely informational; no code uses these.
format_version = "5.0"                  # File format version we write
compatible_formats = ["1.0",            # Original protocol 0
                      "1.1",            # Protocol 0 mit INST added
                      "1.2",            # Original protocol 1
                      "1.3",            # Protocol 1 mit BINFLOAT added
                      "2.0",            # Protocol 2
                      "3.0",            # Protocol 3
                      "4.0",            # Protocol 4
                      "5.0",            # Protocol 5
                      ]                 # Old format versions we can read

# This is the highest protocol number we know how to read.
HIGHEST_PROTOCOL = 5

# The protocol we write by default.  May be less than HIGHEST_PROTOCOL.
# Only bump this wenn the oldest still supported version of Python already
# includes it.
DEFAULT_PROTOCOL = 5

klasse PickleError(Exception):
    """A common base klasse fuer the other pickling exceptions."""
    pass

klasse PicklingError(PickleError):
    """This exception is raised when an unpicklable object is passed to the
    dump() method.

    """
    pass

klasse UnpicklingError(PickleError):
    """This exception is raised when there is a problem unpickling an object,
    such als a security violation.

    Note that other exceptions may also be raised during unpickling, including
    (but nicht necessarily limited to) AttributeError, EOFError, ImportError,
    und IndexError.

    """
    pass

# An instance of _Stop is raised by Unpickler.load_stop() in response to
# the STOP opcode, passing the object that is the result of unpickling.
klasse _Stop(Exception):
    def __init__(self, value):
        self.value = value

# Pickle opcodes.  See pickletools.py fuer extensive docs.  The listing
# here is in kind-of alphabetical order of 1-character pickle code.
# pickletools groups them by purpose.

MARK           = b'('   # push special markobject on stack
STOP           = b'.'   # every pickle ends mit STOP
POP            = b'0'   # discard topmost stack item
POP_MARK       = b'1'   # discard stack top through topmost markobject
DUP            = b'2'   # duplicate top stack item
FLOAT          = b'F'   # push float object; decimal string argument
INT            = b'I'   # push integer oder bool; decimal string argument
BININT         = b'J'   # push four-byte signed int
BININT1        = b'K'   # push 1-byte unsigned int
LONG           = b'L'   # push long; decimal string argument
BININT2        = b'M'   # push 2-byte unsigned int
NONE           = b'N'   # push Nichts
PERSID         = b'P'   # push persistent object; id is taken von string arg
BINPERSID      = b'Q'   #  "       "         "  ;  "  "   "     "  stack
REDUCE         = b'R'   # apply callable to argtuple, both on stack
STRING         = b'S'   # push string; NL-terminated string argument
BINSTRING      = b'T'   # push string; counted binary string argument
SHORT_BINSTRING= b'U'   #  "     "   ;    "      "       "      " < 256 bytes
UNICODE        = b'V'   # push Unicode string; raw-unicode-escaped'd argument
BINUNICODE     = b'X'   #   "     "       "  ; counted UTF-8 string argument
APPEND         = b'a'   # append stack top to list below it
BUILD          = b'b'   # call __setstate__ oder __dict__.update()
GLOBAL         = b'c'   # push self.find_class(modname, name); 2 string args
DICT           = b'd'   # build a dict von stack items
EMPTY_DICT     = b'}'   # push empty dict
APPENDS        = b'e'   # extend list on stack by topmost stack slice
GET            = b'g'   # push item von memo on stack; index is string arg
BINGET         = b'h'   #   "    "    "    "   "   "  ;   "    " 1-byte arg
INST           = b'i'   # build & push klasse instance
LONG_BINGET    = b'j'   # push item von memo on stack; index is 4-byte arg
LIST           = b'l'   # build list von topmost stack items
EMPTY_LIST     = b']'   # push empty list
OBJ            = b'o'   # build & push klasse instance
PUT            = b'p'   # store stack top in memo; index is string arg
BINPUT         = b'q'   #   "     "    "   "   " ;   "    " 1-byte arg
LONG_BINPUT    = b'r'   #   "     "    "   "   " ;   "    " 4-byte arg
SETITEM        = b's'   # add key+value pair to dict
TUPLE          = b't'   # build tuple von topmost stack items
EMPTY_TUPLE    = b')'   # push empty tuple
SETITEMS       = b'u'   # modify dict by adding topmost key+value pairs
BINFLOAT       = b'G'   # push float; arg is 8-byte float encoding

TRUE           = b'I01\n'  # nicht an opcode; see INT docs in pickletools.py
FALSE          = b'I00\n'  # nicht an opcode; see INT docs in pickletools.py

# Protocol 2

PROTO          = b'\x80'  # identify pickle protocol
NEWOBJ         = b'\x81'  # build object by applying cls.__new__ to argtuple
EXT1           = b'\x82'  # push object von extension registry; 1-byte index
EXT2           = b'\x83'  # ditto, but 2-byte index
EXT4           = b'\x84'  # ditto, but 4-byte index
TUPLE1         = b'\x85'  # build 1-tuple von stack top
TUPLE2         = b'\x86'  # build 2-tuple von two topmost stack items
TUPLE3         = b'\x87'  # build 3-tuple von three topmost stack items
NEWTRUE        = b'\x88'  # push Wahr
NEWFALSE       = b'\x89'  # push Falsch
LONG1          = b'\x8a'  # push long von < 256 bytes
LONG4          = b'\x8b'  # push really big long

_tuplesize2code = [EMPTY_TUPLE, TUPLE1, TUPLE2, TUPLE3]

# Protocol 3 (Python 3.x)

BINBYTES       = b'B'   # push bytes; counted binary string argument
SHORT_BINBYTES = b'C'   #  "     "   ;    "      "       "      " < 256 bytes

# Protocol 4

SHORT_BINUNICODE = b'\x8c'  # push short string; UTF-8 length < 256 bytes
BINUNICODE8      = b'\x8d'  # push very long string
BINBYTES8        = b'\x8e'  # push very long bytes string
EMPTY_SET        = b'\x8f'  # push empty set on the stack
ADDITEMS         = b'\x90'  # modify set by adding topmost stack items
FROZENSET        = b'\x91'  # build frozenset von topmost stack items
NEWOBJ_EX        = b'\x92'  # like NEWOBJ but work mit keyword only arguments
STACK_GLOBAL     = b'\x93'  # same als GLOBAL but using names on the stacks
MEMOIZE          = b'\x94'  # store top of the stack in memo
FRAME            = b'\x95'  # indicate the beginning of a new frame

# Protocol 5

BYTEARRAY8       = b'\x96'  # push bytearray
NEXT_BUFFER      = b'\x97'  # push next out-of-band buffer
READONLY_BUFFER  = b'\x98'  # make top of stack readonly

__all__.extend(x fuer x in dir() wenn x.isupper() und nicht x.startswith('_'))


klasse _Framer:

    _FRAME_SIZE_MIN = 4
    _FRAME_SIZE_TARGET = 64 * 1024

    def __init__(self, file_write):
        self.file_write = file_write
        self.current_frame = Nichts

    def start_framing(self):
        self.current_frame = io.BytesIO()

    def end_framing(self):
        wenn self.current_frame und self.current_frame.tell() > 0:
            self.commit_frame(force=Wahr)
            self.current_frame = Nichts

    def commit_frame(self, force=Falsch):
        wenn self.current_frame:
            f = self.current_frame
            wenn f.tell() >= self._FRAME_SIZE_TARGET oder force:
                data = f.getbuffer()
                write = self.file_write
                wenn len(data) >= self._FRAME_SIZE_MIN:
                    # Issue a single call to the write method of the underlying
                    # file object fuer the frame opcode mit the size of the
                    # frame. The concatenation is expected to be less expensive
                    # than issuing an additional call to write.
                    write(FRAME + pack("<Q", len(data)))

                # Issue a separate call to write to append the frame
                # contents without concatenation to the above to avoid a
                # memory copy.
                write(data)

                # Start the new frame mit a new io.BytesIO instance so that
                # the file object can have delayed access to the previous frame
                # contents via an unreleased memoryview of the previous
                # io.BytesIO instance.
                self.current_frame = io.BytesIO()

    def write(self, data):
        wenn self.current_frame:
            gib self.current_frame.write(data)
        sonst:
            gib self.file_write(data)

    def write_large_bytes(self, header, payload):
        write = self.file_write
        wenn self.current_frame:
            # Terminate the current frame und flush it to the file.
            self.commit_frame(force=Wahr)

        # Perform direct write of the header und payload of the large binary
        # object. Be careful nicht to concatenate the header und the payload
        # prior to calling 'write' als we do nicht want to allocate a large
        # temporary bytes object.
        # We intentionally do nicht insert a protocol 4 frame opcode to make
        # it possible to optimize file.read calls in the loader.
        write(header)
        write(payload)


klasse _Unframer:

    def __init__(self, file_read, file_readline, file_tell=Nichts):
        self.file_read = file_read
        self.file_readline = file_readline
        self.current_frame = Nichts

    def readinto(self, buf):
        wenn self.current_frame:
            n = self.current_frame.readinto(buf)
            wenn n == 0 und len(buf) != 0:
                self.current_frame = Nichts
                n = len(buf)
                buf[:] = self.file_read(n)
                gib n
            wenn n < len(buf):
                raise UnpicklingError(
                    "pickle exhausted before end of frame")
            gib n
        sonst:
            n = len(buf)
            buf[:] = self.file_read(n)
            gib n

    def read(self, n):
        wenn self.current_frame:
            data = self.current_frame.read(n)
            wenn nicht data und n != 0:
                self.current_frame = Nichts
                gib self.file_read(n)
            wenn len(data) < n:
                raise UnpicklingError(
                    "pickle exhausted before end of frame")
            gib data
        sonst:
            gib self.file_read(n)

    def readline(self):
        wenn self.current_frame:
            data = self.current_frame.readline()
            wenn nicht data:
                self.current_frame = Nichts
                gib self.file_readline()
            wenn data[-1] != b'\n'[0]:
                raise UnpicklingError(
                    "pickle exhausted before end of frame")
            gib data
        sonst:
            gib self.file_readline()

    def load_frame(self, frame_size):
        wenn self.current_frame und self.current_frame.read() != b'':
            raise UnpicklingError(
                "beginning of a new frame before end of current frame")
        self.current_frame = io.BytesIO(self.file_read(frame_size))


# Tools used fuer pickling.

def _getattribute(obj, dotted_path):
    fuer subpath in dotted_path:
        obj = getattr(obj, subpath)
    gib obj

def whichmodule(obj, name):
    """Find the module an object belong to."""
    dotted_path = name.split('.')
    module_name = getattr(obj, '__module__', Nichts)
    wenn '<locals>' in dotted_path:
        raise PicklingError(f"Can't pickle local object {obj!r}")
    wenn module_name is Nichts:
        # Protect the iteration by using a list copy of sys.modules against dynamic
        # modules that trigger imports of other modules upon calls to getattr.
        fuer module_name, module in sys.modules.copy().items():
            wenn (module_name == '__main__'
                oder module_name == '__mp_main__'  # bpo-42406
                oder module is Nichts):
                weiter
            try:
                wenn _getattribute(module, dotted_path) is obj:
                    gib module_name
            except AttributeError:
                pass
        module_name = '__main__'

    try:
        __import__(module_name, level=0)
        module = sys.modules[module_name]
    except (ImportError, ValueError, KeyError) als exc:
        raise PicklingError(f"Can't pickle {obj!r}: {exc!s}")
    try:
        wenn _getattribute(module, dotted_path) is obj:
            gib module_name
    except AttributeError:
        raise PicklingError(f"Can't pickle {obj!r}: "
                            f"it's nicht found als {module_name}.{name}")

    raise PicklingError(
        f"Can't pickle {obj!r}: it's nicht the same object als {module_name}.{name}")

def encode_long(x):
    r"""Encode a long to a two's complement little-endian binary string.
    Note that 0 is a special case, returning an empty string, to save a
    byte in the LONG1 pickling context.

    >>> encode_long(0)
    b''
    >>> encode_long(255)
    b'\xff\x00'
    >>> encode_long(32767)
    b'\xff\x7f'
    >>> encode_long(-256)
    b'\x00\xff'
    >>> encode_long(-32768)
    b'\x00\x80'
    >>> encode_long(-128)
    b'\x80'
    >>> encode_long(127)
    b'\x7f'
    >>>
    """
    wenn x == 0:
        gib b''
    nbytes = (x.bit_length() >> 3) + 1
    result = x.to_bytes(nbytes, byteorder='little', signed=Wahr)
    wenn x < 0 und nbytes > 1:
        wenn result[-1] == 0xff und (result[-2] & 0x80) != 0:
            result = result[:-1]
    gib result

def decode_long(data):
    r"""Decode a long von a two's complement little-endian binary string.

    >>> decode_long(b'')
    0
    >>> decode_long(b"\xff\x00")
    255
    >>> decode_long(b"\xff\x7f")
    32767
    >>> decode_long(b"\x00\xff")
    -256
    >>> decode_long(b"\x00\x80")
    -32768
    >>> decode_long(b"\x80")
    -128
    >>> decode_long(b"\x7f")
    127
    """
    gib int.from_bytes(data, byteorder='little', signed=Wahr)

def _T(obj):
    cls = type(obj)
    module = cls.__module__
    wenn module in (Nichts, 'builtins', '__main__'):
        gib cls.__qualname__
    gib f'{module}.{cls.__qualname__}'


_NoValue = object()

# Pickling machinery

klasse _Pickler:

    def __init__(self, file, protocol=Nichts, *, fix_imports=Wahr,
                 buffer_callback=Nichts):
        """This takes a binary file fuer writing a pickle data stream.

        The optional *protocol* argument tells the pickler to use the
        given protocol; supported protocols are 0, 1, 2, 3, 4 und 5.
        The default protocol is 5. It was introduced in Python 3.8, und
        is incompatible mit previous versions.

        Specifying a negative protocol version selects the highest
        protocol version supported.  The higher the protocol used, the
        more recent the version of Python needed to read the pickle
        produced.

        The *file* argument must have a write() method that accepts a
        single bytes argument. It can thus be a file object opened for
        binary writing, an io.BytesIO instance, oder any other custom
        object that meets this interface.

        If *fix_imports* is Wahr und *protocol* is less than 3, pickle
        will try to map the new Python 3 names to the old module names
        used in Python 2, so that the pickle data stream is readable
        mit Python 2.

        If *buffer_callback* is Nichts (the default), buffer views are
        serialized into *file* als part of the pickle stream.

        If *buffer_callback* is nicht Nichts, then it can be called any number
        of times mit a buffer view.  If the callback returns a false value
        (such als Nichts), the given buffer is out-of-band; otherwise the
        buffer is serialized in-band, i.e. inside the pickle stream.

        It is an error wenn *buffer_callback* is nicht Nichts und *protocol*
        is Nichts oder smaller than 5.
        """
        wenn protocol is Nichts:
            protocol = DEFAULT_PROTOCOL
        wenn protocol < 0:
            protocol = HIGHEST_PROTOCOL
        sowenn nicht 0 <= protocol <= HIGHEST_PROTOCOL:
            raise ValueError("pickle protocol must be <= %d" % HIGHEST_PROTOCOL)
        wenn buffer_callback is nicht Nichts und protocol < 5:
            raise ValueError("buffer_callback needs protocol >= 5")
        self._buffer_callback = buffer_callback
        try:
            self._file_write = file.write
        except AttributeError:
            raise TypeError("file must have a 'write' attribute")
        self.framer = _Framer(self._file_write)
        self.write = self.framer.write
        self._write_large_bytes = self.framer.write_large_bytes
        self.memo = {}
        self.proto = int(protocol)
        self.bin = protocol >= 1
        self.fast = 0
        self.fix_imports = fix_imports und protocol < 3

    def clear_memo(self):
        """Clears the pickler's "memo".

        The memo is the data structure that remembers which objects the
        pickler has already seen, so that shared oder recursive objects
        are pickled by reference und nicht by value.  This method is
        useful when re-using picklers.
        """
        self.memo.clear()

    def dump(self, obj):
        """Write a pickled representation of obj to the open file."""
        # Check whether Pickler was initialized correctly. This is
        # only needed to mimic the behavior of _pickle.Pickler.dump().
        wenn nicht hasattr(self, "_file_write"):
            raise PicklingError("Pickler.__init__() was nicht called by "
                                "%s.__init__()" % (self.__class__.__name__,))
        wenn self.proto >= 2:
            self.write(PROTO + pack("<B", self.proto))
        wenn self.proto >= 4:
            self.framer.start_framing()
        self.save(obj)
        self.write(STOP)
        self.framer.end_framing()

    def memoize(self, obj):
        """Store an object in the memo."""

        # The Pickler memo is a dictionary mapping object ids to 2-tuples
        # that contain the Unpickler memo key und the object being memoized.
        # The memo key is written to the pickle und will become
        # the key in the Unpickler's memo.  The object is stored in the
        # Pickler memo so that transient objects are kept alive during
        # pickling.

        # The use of the Unpickler memo length als the memo key is just a
        # convention.  The only requirement is that the memo values be unique.
        # But there appears no advantage to any other scheme, und this
        # scheme allows the Unpickler memo to be implemented als a plain (but
        # growable) array, indexed by memo key.
        wenn self.fast:
            gib
        assert id(obj) nicht in self.memo
        idx = len(self.memo)
        self.write(self.put(idx))
        self.memo[id(obj)] = idx, obj

    # Return a PUT (BINPUT, LONG_BINPUT) opcode string, mit argument i.
    def put(self, idx):
        wenn self.proto >= 4:
            gib MEMOIZE
        sowenn self.bin:
            wenn idx < 256:
                gib BINPUT + pack("<B", idx)
            sonst:
                gib LONG_BINPUT + pack("<I", idx)
        sonst:
            gib PUT + repr(idx).encode("ascii") + b'\n'

    # Return a GET (BINGET, LONG_BINGET) opcode string, mit argument i.
    def get(self, i):
        wenn self.bin:
            wenn i < 256:
                gib BINGET + pack("<B", i)
            sonst:
                gib LONG_BINGET + pack("<I", i)

        gib GET + repr(i).encode("ascii") + b'\n'

    def save(self, obj, save_persistent_id=Wahr):
        self.framer.commit_frame()

        # Check fuer persistent id (defined by a subclass)
        wenn save_persistent_id:
            pid = self.persistent_id(obj)
            wenn pid is nicht Nichts:
                self.save_pers(pid)
                gib

        # Check the memo
        x = self.memo.get(id(obj))
        wenn x is nicht Nichts:
            self.write(self.get(x[0]))
            gib

        rv = NotImplemented
        reduce = getattr(self, "reducer_override", _NoValue)
        wenn reduce is nicht _NoValue:
            rv = reduce(obj)

        wenn rv is NotImplemented:
            # Check the type dispatch table
            t = type(obj)
            f = self.dispatch.get(t)
            wenn f is nicht Nichts:
                f(self, obj)  # Call unbound method mit explicit self
                gib

            # Check private dispatch table wenn any, oder sonst
            # copyreg.dispatch_table
            reduce = getattr(self, 'dispatch_table', dispatch_table).get(t, _NoValue)
            wenn reduce is nicht _NoValue:
                rv = reduce(obj)
            sonst:
                # Check fuer a klasse mit a custom metaclass; treat als regular
                # class
                wenn issubclass(t, type):
                    self.save_global(obj)
                    gib

                # Check fuer a __reduce_ex__ method, fall back to __reduce__
                reduce = getattr(obj, "__reduce_ex__", _NoValue)
                wenn reduce is nicht _NoValue:
                    rv = reduce(self.proto)
                sonst:
                    reduce = getattr(obj, "__reduce__", _NoValue)
                    wenn reduce is nicht _NoValue:
                        rv = reduce()
                    sonst:
                        raise PicklingError(f"Can't pickle {_T(t)} object")

        # Check fuer string returned by reduce(), meaning "save als global"
        wenn isinstance(rv, str):
            self.save_global(obj, rv)
            gib

        try:
            # Assert that reduce() returned a tuple
            wenn nicht isinstance(rv, tuple):
                raise PicklingError(f'__reduce__ must gib a string oder tuple, nicht {_T(rv)}')

            # Assert that it returned an appropriately sized tuple
            l = len(rv)
            wenn nicht (2 <= l <= 6):
                raise PicklingError("tuple returned by __reduce__ "
                                    "must contain 2 through 6 elements")

            # Save the reduce() output und finally memoize the object
            self.save_reduce(obj=obj, *rv)
        except BaseException als exc:
            exc.add_note(f'when serializing {_T(obj)} object')
            raise

    def persistent_id(self, obj):
        # This exists so a subclass can override it
        gib Nichts

    def save_pers(self, pid):
        # Save a persistent id reference
        wenn self.bin:
            self.save(pid, save_persistent_id=Falsch)
            self.write(BINPERSID)
        sonst:
            try:
                self.write(PERSID + str(pid).encode("ascii") + b'\n')
            except UnicodeEncodeError:
                raise PicklingError(
                    "persistent IDs in protocol 0 must be ASCII strings")

    def save_reduce(self, func, args, state=Nichts, listitems=Nichts,
                    dictitems=Nichts, state_setter=Nichts, *, obj=Nichts):
        # This API is called by some subclasses

        wenn nicht callable(func):
            raise PicklingError(f"first item of the tuple returned by __reduce__ "
                                f"must be callable, nicht {_T(func)}")
        wenn nicht isinstance(args, tuple):
            raise PicklingError(f"second item of the tuple returned by __reduce__ "
                                f"must be a tuple, nicht {_T(args)}")

        save = self.save
        write = self.write

        func_name = getattr(func, "__name__", "")
        wenn self.proto >= 2 und func_name == "__newobj_ex__":
            cls, args, kwargs = args
            wenn nicht hasattr(cls, "__new__"):
                raise PicklingError("first argument to __newobj_ex__() has no __new__")
            wenn obj is nicht Nichts und cls is nicht obj.__class__:
                raise PicklingError(f"first argument to __newobj_ex__() "
                                    f"must be {obj.__class__!r}, nicht {cls!r}")
            wenn self.proto >= 4:
                try:
                    save(cls)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} class')
                    raise
                try:
                    save(args)
                    save(kwargs)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} __new__ arguments')
                    raise
                write(NEWOBJ_EX)
            sonst:
                func = partial(cls.__new__, cls, *args, **kwargs)
                try:
                    save(func)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} reconstructor')
                    raise
                save(())
                write(REDUCE)
        sowenn self.proto >= 2 und func_name == "__newobj__":
            # A __reduce__ implementation can direct protocol 2 oder newer to
            # use the more efficient NEWOBJ opcode, waehrend still
            # allowing protocol 0 und 1 to work normally.  For this to
            # work, the function returned by __reduce__ should be
            # called __newobj__, und its first argument should be a
            # class.  The implementation fuer __newobj__
            # should be als follows, although pickle has no way to
            # verify this:
            #
            # def __newobj__(cls, *args):
            #     gib cls.__new__(cls, *args)
            #
            # Protocols 0 und 1 will pickle a reference to __newobj__,
            # waehrend protocol 2 (and above) will pickle a reference to
            # cls, the remaining args tuple, und the NEWOBJ code,
            # which calls cls.__new__(cls, *args) at unpickling time
            # (see load_newobj below).  If __reduce__ returns a
            # three-tuple, the state von the third tuple item will be
            # pickled regardless of the protocol, calling __setstate__
            # at unpickling time (see load_build below).
            #
            # Note that no standard __newobj__ implementation exists;
            # you have to provide your own.  This is to enforce
            # compatibility mit Python 2.2 (pickles written using
            # protocol 0 oder 1 in Python 2.3 should be unpicklable by
            # Python 2.2).
            cls = args[0]
            wenn nicht hasattr(cls, "__new__"):
                raise PicklingError("first argument to __newobj__() has no __new__")
            wenn obj is nicht Nichts und cls is nicht obj.__class__:
                raise PicklingError(f"first argument to __newobj__() "
                                    f"must be {obj.__class__!r}, nicht {cls!r}")
            args = args[1:]
            try:
                save(cls)
            except BaseException als exc:
                exc.add_note(f'when serializing {_T(obj)} class')
                raise
            try:
                save(args)
            except BaseException als exc:
                exc.add_note(f'when serializing {_T(obj)} __new__ arguments')
                raise
            write(NEWOBJ)
        sonst:
            try:
                save(func)
            except BaseException als exc:
                exc.add_note(f'when serializing {_T(obj)} reconstructor')
                raise
            try:
                save(args)
            except BaseException als exc:
                exc.add_note(f'when serializing {_T(obj)} reconstructor arguments')
                raise
            write(REDUCE)

        wenn obj is nicht Nichts:
            # If the object is already in the memo, this means it is
            # recursive. In this case, throw away everything we put on the
            # stack, und fetch the object back von the memo.
            wenn id(obj) in self.memo:
                write(POP + self.get(self.memo[id(obj)][0]))
            sonst:
                self.memoize(obj)

        # More new special cases (that work mit older protocols as
        # well): when __reduce__ returns a tuple mit 4 oder 5 items,
        # the 4th und 5th item should be iterators that provide list
        # items und dict items (as (key, value) tuples), oder Nichts.

        wenn listitems is nicht Nichts:
            self._batch_appends(listitems, obj)

        wenn dictitems is nicht Nichts:
            self._batch_setitems(dictitems, obj)

        wenn state is nicht Nichts:
            wenn state_setter is Nichts:
                try:
                    save(state)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} state')
                    raise
                write(BUILD)
            sonst:
                # If a state_setter is specified, call it instead of load_build
                # to update obj's mit its previous state.
                # First, push state_setter und its tuple of expected arguments
                # (obj, state) onto the stack.
                try:
                    save(state_setter)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} state setter')
                    raise
                save(obj)  # simple BINGET opcode als obj is already memoized.
                try:
                    save(state)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} state')
                    raise
                write(TUPLE2)
                # Trigger a state_setter(obj, state) function call.
                write(REDUCE)
                # The purpose of state_setter is to carry-out an
                # inplace modification of obj. We do nicht care about what the
                # method might return, so its output is eventually removed from
                # the stack.
                write(POP)

    # Methods below this point are dispatched through the dispatch table

    dispatch = {}

    def save_none(self, obj):
        self.write(NONE)
    dispatch[type(Nichts)] = save_none

    def save_bool(self, obj):
        wenn self.proto >= 2:
            self.write(NEWTRUE wenn obj sonst NEWFALSE)
        sonst:
            self.write(TRUE wenn obj sonst FALSE)
    dispatch[bool] = save_bool

    def save_long(self, obj):
        wenn self.bin:
            # If the int is small enough to fit in a signed 4-byte 2's-comp
            # format, we can store it more efficiently than the general
            # case.
            # First one- und two-byte unsigned ints:
            wenn obj >= 0:
                wenn obj <= 0xff:
                    self.write(BININT1 + pack("<B", obj))
                    gib
                wenn obj <= 0xffff:
                    self.write(BININT2 + pack("<H", obj))
                    gib
            # Next check fuer 4-byte signed ints:
            wenn -0x80000000 <= obj <= 0x7fffffff:
                self.write(BININT + pack("<i", obj))
                gib
        wenn self.proto >= 2:
            encoded = encode_long(obj)
            n = len(encoded)
            wenn n < 256:
                self.write(LONG1 + pack("<B", n) + encoded)
            sonst:
                self.write(LONG4 + pack("<i", n) + encoded)
            gib
        wenn -0x80000000 <= obj <= 0x7fffffff:
            self.write(INT + repr(obj).encode("ascii") + b'\n')
        sonst:
            self.write(LONG + repr(obj).encode("ascii") + b'L\n')
    dispatch[int] = save_long

    def save_float(self, obj):
        wenn self.bin:
            self.write(BINFLOAT + pack('>d', obj))
        sonst:
            self.write(FLOAT + repr(obj).encode("ascii") + b'\n')
    dispatch[float] = save_float

    def _save_bytes_no_memo(self, obj):
        # helper fuer writing bytes objects fuer protocol >= 3
        # without memoizing them
        assert self.proto >= 3
        n = len(obj)
        wenn n <= 0xff:
            self.write(SHORT_BINBYTES + pack("<B", n) + obj)
        sowenn n > 0xffffffff und self.proto >= 4:
            self._write_large_bytes(BINBYTES8 + pack("<Q", n), obj)
        sowenn n >= self.framer._FRAME_SIZE_TARGET:
            self._write_large_bytes(BINBYTES + pack("<I", n), obj)
        sonst:
            self.write(BINBYTES + pack("<I", n) + obj)

    def save_bytes(self, obj):
        wenn self.proto < 3:
            wenn nicht obj: # bytes object is empty
                self.save_reduce(bytes, (), obj=obj)
            sonst:
                self.save_reduce(codecs.encode,
                                 (str(obj, 'latin1'), 'latin1'), obj=obj)
            gib
        self._save_bytes_no_memo(obj)
        self.memoize(obj)
    dispatch[bytes] = save_bytes

    def _save_bytearray_no_memo(self, obj):
        # helper fuer writing bytearray objects fuer protocol >= 5
        # without memoizing them
        assert self.proto >= 5
        n = len(obj)
        wenn n >= self.framer._FRAME_SIZE_TARGET:
            self._write_large_bytes(BYTEARRAY8 + pack("<Q", n), obj)
        sonst:
            self.write(BYTEARRAY8 + pack("<Q", n) + obj)

    def save_bytearray(self, obj):
        wenn self.proto < 5:
            wenn nicht obj:  # bytearray is empty
                self.save_reduce(bytearray, (), obj=obj)
            sonst:
                self.save_reduce(bytearray, (bytes(obj),), obj=obj)
            gib
        self._save_bytearray_no_memo(obj)
        self.memoize(obj)
    dispatch[bytearray] = save_bytearray

    wenn _HAVE_PICKLE_BUFFER:
        def save_picklebuffer(self, obj):
            wenn self.proto < 5:
                raise PicklingError("PickleBuffer can only be pickled mit "
                                    "protocol >= 5")
            mit obj.raw() als m:
                wenn nicht m.contiguous:
                    raise PicklingError("PickleBuffer can nicht be pickled when "
                                        "pointing to a non-contiguous buffer")
                in_band = Wahr
                wenn self._buffer_callback is nicht Nichts:
                    in_band = bool(self._buffer_callback(obj))
                wenn in_band:
                    # Write data in-band
                    # XXX The C implementation avoids a copy here
                    buf = m.tobytes()
                    in_memo = id(buf) in self.memo
                    wenn m.readonly:
                        wenn in_memo:
                            self._save_bytes_no_memo(buf)
                        sonst:
                            self.save_bytes(buf)
                    sonst:
                        wenn in_memo:
                            self._save_bytearray_no_memo(buf)
                        sonst:
                            self.save_bytearray(buf)
                sonst:
                    # Write data out-of-band
                    self.write(NEXT_BUFFER)
                    wenn m.readonly:
                        self.write(READONLY_BUFFER)

        dispatch[PickleBuffer] = save_picklebuffer

    def save_str(self, obj):
        wenn self.bin:
            encoded = obj.encode('utf-8', 'surrogatepass')
            n = len(encoded)
            wenn n <= 0xff und self.proto >= 4:
                self.write(SHORT_BINUNICODE + pack("<B", n) + encoded)
            sowenn n > 0xffffffff und self.proto >= 4:
                self._write_large_bytes(BINUNICODE8 + pack("<Q", n), encoded)
            sowenn n >= self.framer._FRAME_SIZE_TARGET:
                self._write_large_bytes(BINUNICODE + pack("<I", n), encoded)
            sonst:
                self.write(BINUNICODE + pack("<I", n) + encoded)
        sonst:
            # Escape what raw-unicode-escape doesn't, but memoize the original.
            tmp = obj.replace("\\", "\\u005c")
            tmp = tmp.replace("\0", "\\u0000")
            tmp = tmp.replace("\n", "\\u000a")
            tmp = tmp.replace("\r", "\\u000d")
            tmp = tmp.replace("\x1a", "\\u001a")  # EOF on DOS
            self.write(UNICODE + tmp.encode('raw-unicode-escape') + b'\n')
        self.memoize(obj)
    dispatch[str] = save_str

    def save_tuple(self, obj):
        wenn nicht obj: # tuple is empty
            wenn self.bin:
                self.write(EMPTY_TUPLE)
            sonst:
                self.write(MARK + TUPLE)
            gib

        n = len(obj)
        save = self.save
        memo = self.memo
        wenn n <= 3 und self.proto >= 2:
            fuer i, element in enumerate(obj):
                try:
                    save(element)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} item {i}')
                    raise
            # Subtle.  Same als in the big comment below.
            wenn id(obj) in memo:
                get = self.get(memo[id(obj)][0])
                self.write(POP * n + get)
            sonst:
                self.write(_tuplesize2code[n])
                self.memoize(obj)
            gib

        # proto 0 oder proto 1 und tuple isn't empty, oder proto > 1 und tuple
        # has more than 3 elements.
        write = self.write
        write(MARK)
        fuer i, element in enumerate(obj):
            try:
                save(element)
            except BaseException als exc:
                exc.add_note(f'when serializing {_T(obj)} item {i}')
                raise

        wenn id(obj) in memo:
            # Subtle.  d was nicht in memo when we entered save_tuple(), so
            # the process of saving the tuple's elements must have saved
            # the tuple itself:  the tuple is recursive.  The proper action
            # now is to throw away everything we put on the stack, und
            # simply GET the tuple (it's already constructed).  This check
            # could have been done in the "for element" loop instead, but
            # recursive tuples are a rare thing.
            get = self.get(memo[id(obj)][0])
            wenn self.bin:
                write(POP_MARK + get)
            sonst:   # proto 0 -- POP_MARK nicht available
                write(POP * (n+1) + get)
            gib

        # No recursion.
        write(TUPLE)
        self.memoize(obj)

    dispatch[tuple] = save_tuple

    def save_list(self, obj):
        wenn self.bin:
            self.write(EMPTY_LIST)
        sonst:   # proto 0 -- can't use EMPTY_LIST
            self.write(MARK + LIST)

        self.memoize(obj)
        self._batch_appends(obj, obj)

    dispatch[list] = save_list

    _BATCHSIZE = 1000

    def _batch_appends(self, items, obj):
        # Helper to batch up APPENDS sequences
        save = self.save
        write = self.write

        wenn nicht self.bin:
            fuer i, x in enumerate(items):
                try:
                    save(x)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} item {i}')
                    raise
                write(APPEND)
            gib

        start = 0
        fuer batch in batched(items, self._BATCHSIZE):
            batch_len = len(batch)
            wenn batch_len != 1:
                write(MARK)
                fuer i, x in enumerate(batch, start):
                    try:
                        save(x)
                    except BaseException als exc:
                        exc.add_note(f'when serializing {_T(obj)} item {i}')
                        raise
                write(APPENDS)
            sonst:
                try:
                    save(batch[0])
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} item {start}')
                    raise
                write(APPEND)
            start += batch_len

    def save_dict(self, obj):
        wenn self.bin:
            self.write(EMPTY_DICT)
        sonst:   # proto 0 -- can't use EMPTY_DICT
            self.write(MARK + DICT)

        self.memoize(obj)
        self._batch_setitems(obj.items(), obj)

    dispatch[dict] = save_dict

    def _batch_setitems(self, items, obj):
        # Helper to batch up SETITEMS sequences; proto >= 1 only
        save = self.save
        write = self.write

        wenn nicht self.bin:
            fuer k, v in items:
                save(k)
                try:
                    save(v)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} item {k!r}')
                    raise
                write(SETITEM)
            gib

        fuer batch in batched(items, self._BATCHSIZE):
            wenn len(batch) != 1:
                write(MARK)
                fuer k, v in batch:
                    save(k)
                    try:
                        save(v)
                    except BaseException als exc:
                        exc.add_note(f'when serializing {_T(obj)} item {k!r}')
                        raise
                write(SETITEMS)
            sonst:
                k, v = batch[0]
                save(k)
                try:
                    save(v)
                except BaseException als exc:
                    exc.add_note(f'when serializing {_T(obj)} item {k!r}')
                    raise
                write(SETITEM)

    def save_set(self, obj):
        save = self.save
        write = self.write

        wenn self.proto < 4:
            self.save_reduce(set, (list(obj),), obj=obj)
            gib

        write(EMPTY_SET)
        self.memoize(obj)

        fuer batch in batched(obj, self._BATCHSIZE):
            write(MARK)
            try:
                fuer item in batch:
                    save(item)
            except BaseException als exc:
                exc.add_note(f'when serializing {_T(obj)} element')
                raise
            write(ADDITEMS)
    dispatch[set] = save_set

    def save_frozenset(self, obj):
        save = self.save
        write = self.write

        wenn self.proto < 4:
            self.save_reduce(frozenset, (list(obj),), obj=obj)
            gib

        write(MARK)
        try:
            fuer item in obj:
                save(item)
        except BaseException als exc:
            exc.add_note(f'when serializing {_T(obj)} element')
            raise

        wenn id(obj) in self.memo:
            # If the object is already in the memo, this means it is
            # recursive. In this case, throw away everything we put on the
            # stack, und fetch the object back von the memo.
            write(POP_MARK + self.get(self.memo[id(obj)][0]))
            gib

        write(FROZENSET)
        self.memoize(obj)
    dispatch[frozenset] = save_frozenset

    def save_global(self, obj, name=Nichts):
        write = self.write
        memo = self.memo

        wenn name is Nichts:
            name = getattr(obj, '__qualname__', Nichts)
            wenn name is Nichts:
                name = obj.__name__

        module_name = whichmodule(obj, name)
        wenn self.proto >= 2:
            code = _extension_registry.get((module_name, name), _NoValue)
            wenn code is nicht _NoValue:
                wenn code <= 0xff:
                    data = pack("<B", code)
                    wenn data == b'\0':
                        # Should never happen in normal circumstances,
                        # since the type und the value of the code are
                        # checked in copyreg.add_extension().
                        raise RuntimeError("extension code 0 is out of range")
                    write(EXT1 + data)
                sowenn code <= 0xffff:
                    write(EXT2 + pack("<H", code))
                sonst:
                    write(EXT4 + pack("<i", code))
                gib

        wenn self.proto >= 4:
            self.save(module_name)
            self.save(name)
            write(STACK_GLOBAL)
        sowenn '.' in name:
            # In protocol < 4, objects mit multi-part __qualname__
            # are represented as
            # getattr(getattr(..., attrname1), attrname2).
            dotted_path = name.split('.')
            name = dotted_path.pop(0)
            save = self.save
            fuer attrname in dotted_path:
                save(getattr)
                wenn self.proto < 2:
                    write(MARK)
            self._save_toplevel_by_name(module_name, name)
            fuer attrname in dotted_path:
                save(attrname)
                wenn self.proto < 2:
                    write(TUPLE)
                sonst:
                    write(TUPLE2)
                write(REDUCE)
        sonst:
            self._save_toplevel_by_name(module_name, name)

        self.memoize(obj)

    def _save_toplevel_by_name(self, module_name, name):
        wenn self.proto >= 3:
            # Non-ASCII identifiers are supported only mit protocols >= 3.
            encoding = "utf-8"
        sonst:
            wenn self.fix_imports:
                r_name_mapping = _compat_pickle.REVERSE_NAME_MAPPING
                r_import_mapping = _compat_pickle.REVERSE_IMPORT_MAPPING
                wenn (module_name, name) in r_name_mapping:
                    module_name, name = r_name_mapping[(module_name, name)]
                sowenn module_name in r_import_mapping:
                    module_name = r_import_mapping[module_name]
            encoding = "ascii"
        try:
            self.write(GLOBAL + bytes(module_name, encoding) + b'\n')
        except UnicodeEncodeError:
            raise PicklingError(
                f"can't pickle module identifier {module_name!r} using "
                f"pickle protocol {self.proto}")
        try:
            self.write(bytes(name, encoding) + b'\n')
        except UnicodeEncodeError:
            raise PicklingError(
                f"can't pickle global identifier {name!r} using "
                f"pickle protocol {self.proto}")

    def save_type(self, obj):
        wenn obj is type(Nichts):
            gib self.save_reduce(type, (Nichts,), obj=obj)
        sowenn obj is type(NotImplemented):
            gib self.save_reduce(type, (NotImplemented,), obj=obj)
        sowenn obj is type(...):
            gib self.save_reduce(type, (...,), obj=obj)
        gib self.save_global(obj)

    dispatch[FunctionType] = save_global
    dispatch[type] = save_type


# Unpickling machinery

klasse _Unpickler:

    def __init__(self, file, *, fix_imports=Wahr,
                 encoding="ASCII", errors="strict", buffers=Nichts):
        """This takes a binary file fuer reading a pickle data stream.

        The protocol version of the pickle is detected automatically, so
        no proto argument is needed.

        The argument *file* must have two methods, a read() method that
        takes an integer argument, und a readline() method that requires
        no arguments.  Both methods should gib bytes.  Thus *file*
        can be a binary file object opened fuer reading, an io.BytesIO
        object, oder any other custom object that meets this interface.

        The file-like object must have two methods, a read() method
        that takes an integer argument, und a readline() method that
        requires no arguments.  Both methods should gib bytes.
        Thus file-like object can be a binary file object opened for
        reading, a BytesIO object, oder any other custom object that
        meets this interface.

        If *buffers* is nicht Nichts, it should be an iterable of buffer-enabled
        objects that is consumed each time the pickle stream references
        an out-of-band buffer view.  Such buffers have been given in order
        to the *buffer_callback* of a Pickler object.

        If *buffers* is Nichts (the default), then the buffers are taken
        von the pickle stream, assuming they are serialized there.
        It is an error fuer *buffers* to be Nichts wenn the pickle stream
        was produced mit a non-Nichts *buffer_callback*.

        Other optional arguments are *fix_imports*, *encoding* und
        *errors*, which are used to control compatibility support for
        pickle stream generated by Python 2.  If *fix_imports* is Wahr,
        pickle will try to map the old Python 2 names to the new names
        used in Python 3.  The *encoding* und *errors* tell pickle how
        to decode 8-bit string instances pickled by Python 2; these
        default to 'ASCII' und 'strict', respectively. *encoding* can be
        'bytes' to read these 8-bit string instances als bytes objects.
        """
        self._buffers = iter(buffers) wenn buffers is nicht Nichts sonst Nichts
        self._file_readline = file.readline
        self._file_read = file.read
        self.memo = {}
        self.encoding = encoding
        self.errors = errors
        self.proto = 0
        self.fix_imports = fix_imports

    def load(self):
        """Read a pickled object representation von the open file.

        Return the reconstituted object hierarchy specified in the file.
        """
        # Check whether Unpickler was initialized correctly. This is
        # only needed to mimic the behavior of _pickle.Unpickler.dump().
        wenn nicht hasattr(self, "_file_read"):
            raise UnpicklingError("Unpickler.__init__() was nicht called by "
                                  "%s.__init__()" % (self.__class__.__name__,))
        self._unframer = _Unframer(self._file_read, self._file_readline)
        self.read = self._unframer.read
        self.readinto = self._unframer.readinto
        self.readline = self._unframer.readline
        self.metastack = []
        self.stack = []
        self.append = self.stack.append
        self.proto = 0
        read = self.read
        dispatch = self.dispatch
        try:
            waehrend Wahr:
                key = read(1)
                wenn nicht key:
                    raise EOFError
                assert isinstance(key, bytes_types)
                dispatch[key[0]](self)
        except _Stop als stopinst:
            gib stopinst.value

    # Return a list of items pushed in the stack after last MARK instruction.
    def pop_mark(self):
        items = self.stack
        self.stack = self.metastack.pop()
        self.append = self.stack.append
        gib items

    def persistent_load(self, pid):
        raise UnpicklingError("unsupported persistent id encountered")

    dispatch = {}

    def load_proto(self):
        proto = self.read(1)[0]
        wenn nicht 0 <= proto <= HIGHEST_PROTOCOL:
            raise ValueError("unsupported pickle protocol: %d" % proto)
        self.proto = proto
    dispatch[PROTO[0]] = load_proto

    def load_frame(self):
        frame_size, = unpack('<Q', self.read(8))
        wenn frame_size > sys.maxsize:
            raise ValueError("frame size > sys.maxsize: %d" % frame_size)
        self._unframer.load_frame(frame_size)
    dispatch[FRAME[0]] = load_frame

    def load_persid(self):
        try:
            pid = self.readline()[:-1].decode("ascii")
        except UnicodeDecodeError:
            raise UnpicklingError(
                "persistent IDs in protocol 0 must be ASCII strings")
        self.append(self.persistent_load(pid))
    dispatch[PERSID[0]] = load_persid

    def load_binpersid(self):
        pid = self.stack.pop()
        self.append(self.persistent_load(pid))
    dispatch[BINPERSID[0]] = load_binpersid

    def load_none(self):
        self.append(Nichts)
    dispatch[NONE[0]] = load_none

    def load_false(self):
        self.append(Falsch)
    dispatch[NEWFALSE[0]] = load_false

    def load_true(self):
        self.append(Wahr)
    dispatch[NEWTRUE[0]] = load_true

    def load_int(self):
        data = self.readline()
        wenn data == FALSE[1:]:
            val = Falsch
        sowenn data == TRUE[1:]:
            val = Wahr
        sonst:
            val = int(data)
        self.append(val)
    dispatch[INT[0]] = load_int

    def load_binint(self):
        self.append(unpack('<i', self.read(4))[0])
    dispatch[BININT[0]] = load_binint

    def load_binint1(self):
        self.append(self.read(1)[0])
    dispatch[BININT1[0]] = load_binint1

    def load_binint2(self):
        self.append(unpack('<H', self.read(2))[0])
    dispatch[BININT2[0]] = load_binint2

    def load_long(self):
        val = self.readline()[:-1]
        wenn val und val[-1] == b'L'[0]:
            val = val[:-1]
        self.append(int(val))
    dispatch[LONG[0]] = load_long

    def load_long1(self):
        n = self.read(1)[0]
        data = self.read(n)
        self.append(decode_long(data))
    dispatch[LONG1[0]] = load_long1

    def load_long4(self):
        n, = unpack('<i', self.read(4))
        wenn n < 0:
            # Corrupt oder hostile pickle -- we never write one like this
            raise UnpicklingError("LONG pickle has negative byte count")
        data = self.read(n)
        self.append(decode_long(data))
    dispatch[LONG4[0]] = load_long4

    def load_float(self):
        self.append(float(self.readline()[:-1]))
    dispatch[FLOAT[0]] = load_float

    def load_binfloat(self):
        self.append(unpack('>d', self.read(8))[0])
    dispatch[BINFLOAT[0]] = load_binfloat

    def _decode_string(self, value):
        # Used to allow strings von Python 2 to be decoded either as
        # bytes oder Unicode strings.  This should be used only mit the
        # STRING, BINSTRING und SHORT_BINSTRING opcodes.
        wenn self.encoding == "bytes":
            gib value
        sonst:
            gib value.decode(self.encoding, self.errors)

    def load_string(self):
        data = self.readline()[:-1]
        # Strip outermost quotes
        wenn len(data) >= 2 und data[0] == data[-1] und data[0] in b'"\'':
            data = data[1:-1]
        sonst:
            raise UnpicklingError("the STRING opcode argument must be quoted")
        self.append(self._decode_string(codecs.escape_decode(data)[0]))
    dispatch[STRING[0]] = load_string

    def load_binstring(self):
        # Deprecated BINSTRING uses signed 32-bit length
        len, = unpack('<i', self.read(4))
        wenn len < 0:
            raise UnpicklingError("BINSTRING pickle has negative byte count")
        data = self.read(len)
        self.append(self._decode_string(data))
    dispatch[BINSTRING[0]] = load_binstring

    def load_binbytes(self):
        len, = unpack('<I', self.read(4))
        wenn len > maxsize:
            raise UnpicklingError("BINBYTES exceeds system's maximum size "
                                  "of %d bytes" % maxsize)
        self.append(self.read(len))
    dispatch[BINBYTES[0]] = load_binbytes

    def load_unicode(self):
        self.append(str(self.readline()[:-1], 'raw-unicode-escape'))
    dispatch[UNICODE[0]] = load_unicode

    def load_binunicode(self):
        len, = unpack('<I', self.read(4))
        wenn len > maxsize:
            raise UnpicklingError("BINUNICODE exceeds system's maximum size "
                                  "of %d bytes" % maxsize)
        self.append(str(self.read(len), 'utf-8', 'surrogatepass'))
    dispatch[BINUNICODE[0]] = load_binunicode

    def load_binunicode8(self):
        len, = unpack('<Q', self.read(8))
        wenn len > maxsize:
            raise UnpicklingError("BINUNICODE8 exceeds system's maximum size "
                                  "of %d bytes" % maxsize)
        self.append(str(self.read(len), 'utf-8', 'surrogatepass'))
    dispatch[BINUNICODE8[0]] = load_binunicode8

    def load_binbytes8(self):
        len, = unpack('<Q', self.read(8))
        wenn len > maxsize:
            raise UnpicklingError("BINBYTES8 exceeds system's maximum size "
                                  "of %d bytes" % maxsize)
        self.append(self.read(len))
    dispatch[BINBYTES8[0]] = load_binbytes8

    def load_bytearray8(self):
        len, = unpack('<Q', self.read(8))
        wenn len > maxsize:
            raise UnpicklingError("BYTEARRAY8 exceeds system's maximum size "
                                  "of %d bytes" % maxsize)
        b = bytearray(len)
        self.readinto(b)
        self.append(b)
    dispatch[BYTEARRAY8[0]] = load_bytearray8

    def load_next_buffer(self):
        wenn self._buffers is Nichts:
            raise UnpicklingError("pickle stream refers to out-of-band data "
                                  "but no *buffers* argument was given")
        try:
            buf = next(self._buffers)
        except StopIteration:
            raise UnpicklingError("not enough out-of-band buffers")
        self.append(buf)
    dispatch[NEXT_BUFFER[0]] = load_next_buffer

    def load_readonly_buffer(self):
        buf = self.stack[-1]
        mit memoryview(buf) als m:
            wenn nicht m.readonly:
                self.stack[-1] = m.toreadonly()
    dispatch[READONLY_BUFFER[0]] = load_readonly_buffer

    def load_short_binstring(self):
        len = self.read(1)[0]
        data = self.read(len)
        self.append(self._decode_string(data))
    dispatch[SHORT_BINSTRING[0]] = load_short_binstring

    def load_short_binbytes(self):
        len = self.read(1)[0]
        self.append(self.read(len))
    dispatch[SHORT_BINBYTES[0]] = load_short_binbytes

    def load_short_binunicode(self):
        len = self.read(1)[0]
        self.append(str(self.read(len), 'utf-8', 'surrogatepass'))
    dispatch[SHORT_BINUNICODE[0]] = load_short_binunicode

    def load_tuple(self):
        items = self.pop_mark()
        self.append(tuple(items))
    dispatch[TUPLE[0]] = load_tuple

    def load_empty_tuple(self):
        self.append(())
    dispatch[EMPTY_TUPLE[0]] = load_empty_tuple

    def load_tuple1(self):
        self.stack[-1] = (self.stack[-1],)
    dispatch[TUPLE1[0]] = load_tuple1

    def load_tuple2(self):
        self.stack[-2:] = [(self.stack[-2], self.stack[-1])]
    dispatch[TUPLE2[0]] = load_tuple2

    def load_tuple3(self):
        self.stack[-3:] = [(self.stack[-3], self.stack[-2], self.stack[-1])]
    dispatch[TUPLE3[0]] = load_tuple3

    def load_empty_list(self):
        self.append([])
    dispatch[EMPTY_LIST[0]] = load_empty_list

    def load_empty_dictionary(self):
        self.append({})
    dispatch[EMPTY_DICT[0]] = load_empty_dictionary

    def load_empty_set(self):
        self.append(set())
    dispatch[EMPTY_SET[0]] = load_empty_set

    def load_frozenset(self):
        items = self.pop_mark()
        self.append(frozenset(items))
    dispatch[FROZENSET[0]] = load_frozenset

    def load_list(self):
        items = self.pop_mark()
        self.append(items)
    dispatch[LIST[0]] = load_list

    def load_dict(self):
        items = self.pop_mark()
        d = {items[i]: items[i+1]
             fuer i in range(0, len(items), 2)}
        self.append(d)
    dispatch[DICT[0]] = load_dict

    # INST und OBJ differ only in how they get a klasse object.  It's not
    # only sensible to do the rest in a common routine, the two routines
    # previously diverged und grew different bugs.
    # klass is the klasse to instantiate, und k points to the topmost mark
    # object, following which are the arguments fuer klass.__init__.
    def _instantiate(self, klass, args):
        wenn (args oder nicht isinstance(klass, type) oder
            hasattr(klass, "__getinitargs__")):
            try:
                value = klass(*args)
            except TypeError als err:
                raise TypeError("in constructor fuer %s: %s" %
                                (klass.__name__, str(err)), err.__traceback__)
        sonst:
            value = klass.__new__(klass)
        self.append(value)

    def load_inst(self):
        module = self.readline()[:-1].decode("ascii")
        name = self.readline()[:-1].decode("ascii")
        klass = self.find_class(module, name)
        self._instantiate(klass, self.pop_mark())
    dispatch[INST[0]] = load_inst

    def load_obj(self):
        # Stack is ... markobject classobject arg1 arg2 ...
        args = self.pop_mark()
        cls = args.pop(0)
        self._instantiate(cls, args)
    dispatch[OBJ[0]] = load_obj

    def load_newobj(self):
        args = self.stack.pop()
        cls = self.stack.pop()
        obj = cls.__new__(cls, *args)
        self.append(obj)
    dispatch[NEWOBJ[0]] = load_newobj

    def load_newobj_ex(self):
        kwargs = self.stack.pop()
        args = self.stack.pop()
        cls = self.stack.pop()
        obj = cls.__new__(cls, *args, **kwargs)
        self.append(obj)
    dispatch[NEWOBJ_EX[0]] = load_newobj_ex

    def load_global(self):
        module = self.readline()[:-1].decode("utf-8")
        name = self.readline()[:-1].decode("utf-8")
        klass = self.find_class(module, name)
        self.append(klass)
    dispatch[GLOBAL[0]] = load_global

    def load_stack_global(self):
        name = self.stack.pop()
        module = self.stack.pop()
        wenn type(name) is nicht str oder type(module) is nicht str:
            raise UnpicklingError("STACK_GLOBAL requires str")
        self.append(self.find_class(module, name))
    dispatch[STACK_GLOBAL[0]] = load_stack_global

    def load_ext1(self):
        code = self.read(1)[0]
        self.get_extension(code)
    dispatch[EXT1[0]] = load_ext1

    def load_ext2(self):
        code, = unpack('<H', self.read(2))
        self.get_extension(code)
    dispatch[EXT2[0]] = load_ext2

    def load_ext4(self):
        code, = unpack('<i', self.read(4))
        self.get_extension(code)
    dispatch[EXT4[0]] = load_ext4

    def get_extension(self, code):
        obj = _extension_cache.get(code, _NoValue)
        wenn obj is nicht _NoValue:
            self.append(obj)
            gib
        key = _inverted_registry.get(code)
        wenn nicht key:
            wenn code <= 0: # note that 0 is forbidden
                # Corrupt oder hostile pickle.
                raise UnpicklingError("EXT specifies code <= 0")
            raise ValueError("unregistered extension code %d" % code)
        obj = self.find_class(*key)
        _extension_cache[code] = obj
        self.append(obj)

    def find_class(self, module, name):
        # Subclasses may override this.
        sys.audit('pickle.find_class', module, name)
        wenn self.proto < 3 und self.fix_imports:
            wenn (module, name) in _compat_pickle.NAME_MAPPING:
                module, name = _compat_pickle.NAME_MAPPING[(module, name)]
            sowenn module in _compat_pickle.IMPORT_MAPPING:
                module = _compat_pickle.IMPORT_MAPPING[module]
        __import__(module, level=0)
        wenn self.proto >= 4 und '.' in name:
            dotted_path = name.split('.')
            try:
                gib _getattribute(sys.modules[module], dotted_path)
            except AttributeError:
                raise AttributeError(
                    f"Can't resolve path {name!r} on module {module!r}")
        sonst:
            gib getattr(sys.modules[module], name)

    def load_reduce(self):
        stack = self.stack
        args = stack.pop()
        func = stack[-1]
        stack[-1] = func(*args)
    dispatch[REDUCE[0]] = load_reduce

    def load_pop(self):
        wenn self.stack:
            del self.stack[-1]
        sonst:
            self.pop_mark()
    dispatch[POP[0]] = load_pop

    def load_pop_mark(self):
        self.pop_mark()
    dispatch[POP_MARK[0]] = load_pop_mark

    def load_dup(self):
        self.append(self.stack[-1])
    dispatch[DUP[0]] = load_dup

    def load_get(self):
        i = int(self.readline()[:-1])
        try:
            self.append(self.memo[i])
        except KeyError:
            msg = f'Memo value nicht found at index {i}'
            raise UnpicklingError(msg) von Nichts
    dispatch[GET[0]] = load_get

    def load_binget(self):
        i = self.read(1)[0]
        try:
            self.append(self.memo[i])
        except KeyError als exc:
            msg = f'Memo value nicht found at index {i}'
            raise UnpicklingError(msg) von Nichts
    dispatch[BINGET[0]] = load_binget

    def load_long_binget(self):
        i, = unpack('<I', self.read(4))
        try:
            self.append(self.memo[i])
        except KeyError als exc:
            msg = f'Memo value nicht found at index {i}'
            raise UnpicklingError(msg) von Nichts
    dispatch[LONG_BINGET[0]] = load_long_binget

    def load_put(self):
        i = int(self.readline()[:-1])
        wenn i < 0:
            raise ValueError("negative PUT argument")
        self.memo[i] = self.stack[-1]
    dispatch[PUT[0]] = load_put

    def load_binput(self):
        i = self.read(1)[0]
        wenn i < 0:
            raise ValueError("negative BINPUT argument")
        self.memo[i] = self.stack[-1]
    dispatch[BINPUT[0]] = load_binput

    def load_long_binput(self):
        i, = unpack('<I', self.read(4))
        wenn i > maxsize:
            raise ValueError("negative LONG_BINPUT argument")
        self.memo[i] = self.stack[-1]
    dispatch[LONG_BINPUT[0]] = load_long_binput

    def load_memoize(self):
        memo = self.memo
        memo[len(memo)] = self.stack[-1]
    dispatch[MEMOIZE[0]] = load_memoize

    def load_append(self):
        stack = self.stack
        value = stack.pop()
        list = stack[-1]
        list.append(value)
    dispatch[APPEND[0]] = load_append

    def load_appends(self):
        items = self.pop_mark()
        list_obj = self.stack[-1]
        try:
            extend = list_obj.extend
        except AttributeError:
            pass
        sonst:
            extend(items)
            gib
        # Even wenn the PEP 307 requires extend() und append() methods,
        # fall back on append() wenn the object has no extend() method
        # fuer backward compatibility.
        append = list_obj.append
        fuer item in items:
            append(item)
    dispatch[APPENDS[0]] = load_appends

    def load_setitem(self):
        stack = self.stack
        value = stack.pop()
        key = stack.pop()
        dict = stack[-1]
        dict[key] = value
    dispatch[SETITEM[0]] = load_setitem

    def load_setitems(self):
        items = self.pop_mark()
        dict = self.stack[-1]
        fuer i in range(0, len(items), 2):
            dict[items[i]] = items[i + 1]
    dispatch[SETITEMS[0]] = load_setitems

    def load_additems(self):
        items = self.pop_mark()
        set_obj = self.stack[-1]
        wenn isinstance(set_obj, set):
            set_obj.update(items)
        sonst:
            add = set_obj.add
            fuer item in items:
                add(item)
    dispatch[ADDITEMS[0]] = load_additems

    def load_build(self):
        stack = self.stack
        state = stack.pop()
        inst = stack[-1]
        setstate = getattr(inst, "__setstate__", _NoValue)
        wenn setstate is nicht _NoValue:
            setstate(state)
            gib
        slotstate = Nichts
        wenn isinstance(state, tuple) und len(state) == 2:
            state, slotstate = state
        wenn state:
            inst_dict = inst.__dict__
            intern = sys.intern
            fuer k, v in state.items():
                wenn type(k) is str:
                    inst_dict[intern(k)] = v
                sonst:
                    inst_dict[k] = v
        wenn slotstate:
            fuer k, v in slotstate.items():
                setattr(inst, k, v)
    dispatch[BUILD[0]] = load_build

    def load_mark(self):
        self.metastack.append(self.stack)
        self.stack = []
        self.append = self.stack.append
    dispatch[MARK[0]] = load_mark

    def load_stop(self):
        value = self.stack.pop()
        raise _Stop(value)
    dispatch[STOP[0]] = load_stop


# Shorthands

def _dump(obj, file, protocol=Nichts, *, fix_imports=Wahr, buffer_callback=Nichts):
    _Pickler(file, protocol, fix_imports=fix_imports,
             buffer_callback=buffer_callback).dump(obj)

def _dumps(obj, protocol=Nichts, *, fix_imports=Wahr, buffer_callback=Nichts):
    f = io.BytesIO()
    _Pickler(f, protocol, fix_imports=fix_imports,
             buffer_callback=buffer_callback).dump(obj)
    res = f.getvalue()
    assert isinstance(res, bytes_types)
    gib res

def _load(file, *, fix_imports=Wahr, encoding="ASCII", errors="strict",
          buffers=Nichts):
    gib _Unpickler(file, fix_imports=fix_imports, buffers=buffers,
                     encoding=encoding, errors=errors).load()

def _loads(s, /, *, fix_imports=Wahr, encoding="ASCII", errors="strict",
           buffers=Nichts):
    wenn isinstance(s, str):
        raise TypeError("Can't load pickle von unicode string")
    file = io.BytesIO(s)
    gib _Unpickler(file, fix_imports=fix_imports, buffers=buffers,
                      encoding=encoding, errors=errors).load()

# Use the faster _pickle wenn possible
try:
    von _pickle importiere (
        PickleError,
        PicklingError,
        UnpicklingError,
        Pickler,
        Unpickler,
        dump,
        dumps,
        load,
        loads
    )
except ImportError:
    Pickler, Unpickler = _Pickler, _Unpickler
    dump, dumps, load, loads = _dump, _dumps, _load, _loads


def _main(args=Nichts):
    importiere argparse
    importiere pprint
    parser = argparse.ArgumentParser(
        description='display contents of the pickle files',
        color=Wahr,
    )
    parser.add_argument(
        'pickle_file',
        nargs='+', help='the pickle file')
    args = parser.parse_args(args)
    fuer fn in args.pickle_file:
        wenn fn == '-':
            obj = load(sys.stdin.buffer)
        sonst:
            mit open(fn, 'rb') als f:
                obj = load(f)
        pprint.pdrucke(obj)


wenn __name__ == "__main__":
    _main()
