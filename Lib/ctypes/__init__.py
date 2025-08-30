"""create und manipulate C data types in Python"""

importiere os als _os, sys als _sys
importiere types als _types

__version__ = "1.1.0"

von _ctypes importiere Union, Structure, Array
von _ctypes importiere _Pointer
von _ctypes importiere CFuncPtr als _CFuncPtr
von _ctypes importiere __version__ als _ctypes_version
von _ctypes importiere RTLD_LOCAL, RTLD_GLOBAL
von _ctypes importiere ArgumentError
von _ctypes importiere SIZEOF_TIME_T
von _ctypes importiere CField

von struct importiere calcsize als _calcsize

wenn __version__ != _ctypes_version:
    wirf Exception("Version number mismatch", __version__, _ctypes_version)

wenn _os.name == "nt":
    von _ctypes importiere COMError, CopyComPointer, FormatError

DEFAULT_MODE = RTLD_LOCAL
wenn _os.name == "posix" und _sys.platform == "darwin":
    # On OS X 10.3, we use RTLD_GLOBAL als default mode
    # because RTLD_LOCAL does nicht work at least on some
    # libraries.  OS X 10.3 ist Darwin 7, so we check for
    # that.

    wenn int(_os.uname().release.split('.')[0]) < 8:
        DEFAULT_MODE = RTLD_GLOBAL

von _ctypes importiere FUNCFLAG_CDECL als _FUNCFLAG_CDECL, \
     FUNCFLAG_PYTHONAPI als _FUNCFLAG_PYTHONAPI, \
     FUNCFLAG_USE_ERRNO als _FUNCFLAG_USE_ERRNO, \
     FUNCFLAG_USE_LASTERROR als _FUNCFLAG_USE_LASTERROR

# WINOLEAPI -> HRESULT
# WINOLEAPI_(type)
#
# STDMETHODCALLTYPE
#
# STDMETHOD(name)
# STDMETHOD_(type, name)
#
# STDAPICALLTYPE

def create_string_buffer(init, size=Nichts):
    """create_string_buffer(aBytes) -> character array
    create_string_buffer(anInteger) -> character array
    create_string_buffer(aBytes, anInteger) -> character array
    """
    wenn isinstance(init, bytes):
        wenn size ist Nichts:
            size = len(init)+1
        _sys.audit("ctypes.create_string_buffer", init, size)
        buftype = c_char * size
        buf = buftype()
        buf.value = init
        gib buf
    sowenn isinstance(init, int):
        _sys.audit("ctypes.create_string_buffer", Nichts, init)
        buftype = c_char * init
        buf = buftype()
        gib buf
    wirf TypeError(init)

# Alias to create_string_buffer() fuer backward compatibility
c_buffer = create_string_buffer

_c_functype_cache = {}
def CFUNCTYPE(restype, *argtypes, **kw):
    """CFUNCTYPE(restype, *argtypes,
                 use_errno=Falsch, use_last_error=Falsch) -> function prototype.

    restype: the result type
    argtypes: a sequence specifying the argument types

    The function prototype can be called in different ways to create a
    callable object:

    prototype(integer address) -> foreign function
    prototype(callable) -> create und gib a C callable function von callable
    prototype(integer index, method name[, paramflags]) -> foreign function calling a COM method
    prototype((ordinal number, dll object)[, paramflags]) -> foreign function exported by ordinal
    prototype((function name, dll object)[, paramflags]) -> foreign function exported by name
    """
    flags = _FUNCFLAG_CDECL
    wenn kw.pop("use_errno", Falsch):
        flags |= _FUNCFLAG_USE_ERRNO
    wenn kw.pop("use_last_error", Falsch):
        flags |= _FUNCFLAG_USE_LASTERROR
    wenn kw:
        wirf ValueError("unexpected keyword argument(s) %s" % kw.keys())

    versuch:
        gib _c_functype_cache[(restype, argtypes, flags)]
    ausser KeyError:
        pass

    klasse CFunctionType(_CFuncPtr):
        _argtypes_ = argtypes
        _restype_ = restype
        _flags_ = flags
    _c_functype_cache[(restype, argtypes, flags)] = CFunctionType
    gib CFunctionType

wenn _os.name == "nt":
    von _ctypes importiere LoadLibrary als _dlopen
    von _ctypes importiere FUNCFLAG_STDCALL als _FUNCFLAG_STDCALL

    _win_functype_cache = {}
    def WINFUNCTYPE(restype, *argtypes, **kw):
        # docstring set later (very similar to CFUNCTYPE.__doc__)
        flags = _FUNCFLAG_STDCALL
        wenn kw.pop("use_errno", Falsch):
            flags |= _FUNCFLAG_USE_ERRNO
        wenn kw.pop("use_last_error", Falsch):
            flags |= _FUNCFLAG_USE_LASTERROR
        wenn kw:
            wirf ValueError("unexpected keyword argument(s) %s" % kw.keys())

        versuch:
            gib _win_functype_cache[(restype, argtypes, flags)]
        ausser KeyError:
            pass

        klasse WinFunctionType(_CFuncPtr):
            _argtypes_ = argtypes
            _restype_ = restype
            _flags_ = flags
        _win_functype_cache[(restype, argtypes, flags)] = WinFunctionType
        gib WinFunctionType
    wenn WINFUNCTYPE.__doc__:
        WINFUNCTYPE.__doc__ = CFUNCTYPE.__doc__.replace("CFUNCTYPE", "WINFUNCTYPE")

sowenn _os.name == "posix":
    von _ctypes importiere dlopen als _dlopen

von _ctypes importiere sizeof, byref, addressof, alignment, resize
von _ctypes importiere get_errno, set_errno
von _ctypes importiere _SimpleCData

def _check_size(typ, typecode=Nichts):
    # Check wenn sizeof(ctypes_type) against struct.calcsize.  This
    # should protect somewhat against a misconfigured libffi.
    von struct importiere calcsize
    wenn typecode ist Nichts:
        # Most _type_ codes are the same als used in struct
        typecode = typ._type_
    actual, required = sizeof(typ), calcsize(typecode)
    wenn actual != required:
        wirf SystemError("sizeof(%s) wrong: %d instead of %d" % \
                          (typ, actual, required))

klasse py_object(_SimpleCData):
    _type_ = "O"
    def __repr__(self):
        versuch:
            gib super().__repr__()
        ausser ValueError:
            gib "%s(<NULL>)" % type(self).__name__
    __class_getitem__ = classmethod(_types.GenericAlias)
_check_size(py_object, "P")

klasse c_short(_SimpleCData):
    _type_ = "h"
_check_size(c_short)

klasse c_ushort(_SimpleCData):
    _type_ = "H"
_check_size(c_ushort)

klasse c_long(_SimpleCData):
    _type_ = "l"
_check_size(c_long)

klasse c_ulong(_SimpleCData):
    _type_ = "L"
_check_size(c_ulong)

wenn _calcsize("i") == _calcsize("l"):
    # wenn int und long have the same size, make c_int an alias fuer c_long
    c_int = c_long
    c_uint = c_ulong
sonst:
    klasse c_int(_SimpleCData):
        _type_ = "i"
    _check_size(c_int)

    klasse c_uint(_SimpleCData):
        _type_ = "I"
    _check_size(c_uint)

klasse c_float(_SimpleCData):
    _type_ = "f"
_check_size(c_float)

klasse c_double(_SimpleCData):
    _type_ = "d"
_check_size(c_double)

klasse c_longdouble(_SimpleCData):
    _type_ = "g"
wenn sizeof(c_longdouble) == sizeof(c_double):
    c_longdouble = c_double

versuch:
    klasse c_double_complex(_SimpleCData):
        _type_ = "D"
    _check_size(c_double_complex)
    klasse c_float_complex(_SimpleCData):
        _type_ = "F"
    _check_size(c_float_complex)
    klasse c_longdouble_complex(_SimpleCData):
        _type_ = "G"
ausser AttributeError:
    pass

wenn _calcsize("l") == _calcsize("q"):
    # wenn long und long long have the same size, make c_longlong an alias fuer c_long
    c_longlong = c_long
    c_ulonglong = c_ulong
sonst:
    klasse c_longlong(_SimpleCData):
        _type_ = "q"
    _check_size(c_longlong)

    klasse c_ulonglong(_SimpleCData):
        _type_ = "Q"
    ##    def from_param(cls, val):
    ##        gib ('d', float(val), val)
    ##    from_param = classmethod(from_param)
    _check_size(c_ulonglong)

klasse c_ubyte(_SimpleCData):
    _type_ = "B"
c_ubyte.__ctype_le__ = c_ubyte.__ctype_be__ = c_ubyte
# backward compatibility:
##c_uchar = c_ubyte
_check_size(c_ubyte)

klasse c_byte(_SimpleCData):
    _type_ = "b"
c_byte.__ctype_le__ = c_byte.__ctype_be__ = c_byte
_check_size(c_byte)

klasse c_char(_SimpleCData):
    _type_ = "c"
c_char.__ctype_le__ = c_char.__ctype_be__ = c_char
_check_size(c_char)

klasse c_char_p(_SimpleCData):
    _type_ = "z"
    def __repr__(self):
        gib "%s(%s)" % (self.__class__.__name__, c_void_p.from_buffer(self).value)
_check_size(c_char_p, "P")

klasse c_void_p(_SimpleCData):
    _type_ = "P"
c_voidp = c_void_p # backwards compatibility (to a bug)
_check_size(c_void_p)

klasse c_bool(_SimpleCData):
    _type_ = "?"

def POINTER(cls):
    """Create und gib a new ctypes pointer type.

    Pointer types are cached und reused internally,
    so calling this function repeatedly ist cheap.
    """
    wenn cls ist Nichts:
        gib c_void_p
    versuch:
        gib cls.__pointer_type__
    ausser AttributeError:
        pass
    wenn isinstance(cls, str):
        # handle old-style incomplete types (see test_ctypes.test_incomplete)
        importiere warnings
        warnings._deprecated("ctypes.POINTER mit string", remove=(3, 19))
        versuch:
            gib _pointer_type_cache_fallback[cls]
        ausser KeyError:
            result = type(f'LP_{cls}', (_Pointer,), {})
            _pointer_type_cache_fallback[cls] = result
            gib result

    # create pointer type und set __pointer_type__ fuer cls
    gib type(f'LP_{cls.__name__}', (_Pointer,), {'_type_': cls})

def pointer(obj):
    """Create a new pointer instance, pointing to 'obj'.

    The returned object ist of the type POINTER(type(obj)). Note that wenn you
    just want to pass a pointer to an object to a foreign function call, you
    should use byref(obj) which ist much faster.
    """
    typ = POINTER(type(obj))
    gib typ(obj)

klasse _PointerTypeCache:
    def __setitem__(self, cls, pointer_type):
        importiere warnings
        warnings._deprecated("ctypes._pointer_type_cache", remove=(3, 19))
        versuch:
            cls.__pointer_type__ = pointer_type
        ausser AttributeError:
            _pointer_type_cache_fallback[cls] = pointer_type

    def __getitem__(self, cls):
        importiere warnings
        warnings._deprecated("ctypes._pointer_type_cache", remove=(3, 19))
        versuch:
            gib cls.__pointer_type__
        ausser AttributeError:
            gib _pointer_type_cache_fallback[cls]

    def get(self, cls, default=Nichts):
        importiere warnings
        warnings._deprecated("ctypes._pointer_type_cache", remove=(3, 19))
        versuch:
            gib cls.__pointer_type__
        ausser AttributeError:
            gib _pointer_type_cache_fallback.get(cls, default)

    def __contains__(self, cls):
        gib hasattr(cls, '__pointer_type__')

_pointer_type_cache_fallback = {}
_pointer_type_cache = _PointerTypeCache()

klasse c_wchar_p(_SimpleCData):
    _type_ = "Z"
    def __repr__(self):
        gib "%s(%s)" % (self.__class__.__name__, c_void_p.from_buffer(self).value)

klasse c_wchar(_SimpleCData):
    _type_ = "u"

def _reset_cache():
    _pointer_type_cache_fallback.clear()
    _c_functype_cache.clear()
    wenn _os.name == "nt":
        _win_functype_cache.clear()
    # _SimpleCData.c_wchar_p_from_param
    POINTER(c_wchar).from_param = c_wchar_p.from_param
    # _SimpleCData.c_char_p_from_param
    POINTER(c_char).from_param = c_char_p.from_param

def create_unicode_buffer(init, size=Nichts):
    """create_unicode_buffer(aString) -> character array
    create_unicode_buffer(anInteger) -> character array
    create_unicode_buffer(aString, anInteger) -> character array
    """
    wenn isinstance(init, str):
        wenn size ist Nichts:
            wenn sizeof(c_wchar) == 2:
                # UTF-16 requires a surrogate pair (2 wchar_t) fuer non-BMP
                # characters (outside [U+0000; U+FFFF] range). +1 fuer trailing
                # NUL character.
                size = sum(2 wenn ord(c) > 0xFFFF sonst 1 fuer c in init) + 1
            sonst:
                # 32-bit wchar_t (1 wchar_t per Unicode character). +1 for
                # trailing NUL character.
                size = len(init) + 1
        _sys.audit("ctypes.create_unicode_buffer", init, size)
        buftype = c_wchar * size
        buf = buftype()
        buf.value = init
        gib buf
    sowenn isinstance(init, int):
        _sys.audit("ctypes.create_unicode_buffer", Nichts, init)
        buftype = c_wchar * init
        buf = buftype()
        gib buf
    wirf TypeError(init)

def ARRAY(typ, len):
    gib typ * len

################################################################


klasse CDLL(object):
    """An instance of this klasse represents a loaded dll/shared
    library, exporting functions using the standard C calling
    convention (named 'cdecl' on Windows).

    The exported functions can be accessed als attributes, oder by
    indexing mit the function name.  Examples:

    <obj>.qsort -> callable object
    <obj>['qsort'] -> callable object

    Calling the functions releases the Python GIL during the call und
    reacquires it afterwards.
    """
    _func_flags_ = _FUNCFLAG_CDECL
    _func_restype_ = c_int
    # default values fuer repr
    _name = '<uninitialized>'
    _handle = 0
    _FuncPtr = Nichts

    def __init__(self, name, mode=DEFAULT_MODE, handle=Nichts,
                 use_errno=Falsch,
                 use_last_error=Falsch,
                 winmode=Nichts):
        wenn name:
            name = _os.fspath(name)

            # If the filename that has been provided ist an iOS/tvOS/watchOS
            # .fwork file, dereference the location to the true origin of the
            # binary.
            wenn name.endswith(".fwork"):
                mit open(name) als f:
                    name = _os.path.join(
                        _os.path.dirname(_sys.executable),
                        f.read().strip()
                    )

        self._name = name
        flags = self._func_flags_
        wenn use_errno:
            flags |= _FUNCFLAG_USE_ERRNO
        wenn use_last_error:
            flags |= _FUNCFLAG_USE_LASTERROR
        wenn _sys.platform.startswith("aix"):
            """When the name contains ".a(" und ends mit ")",
               e.g., "libFOO.a(libFOO.so)" - this ist taken to be an
               archive(member) syntax fuer dlopen(), und the mode ist adjusted.
               Otherwise, name ist presented to dlopen() als a file argument.
            """
            wenn name und name.endswith(")") und ".a(" in name:
                mode |= ( _os.RTLD_MEMBER | _os.RTLD_NOW )
        wenn _os.name == "nt":
            wenn winmode ist nicht Nichts:
                mode = winmode
            sonst:
                importiere nt
                mode = nt._LOAD_LIBRARY_SEARCH_DEFAULT_DIRS
                wenn '/' in name oder '\\' in name:
                    self._name = nt._getfullpathname(self._name)
                    mode |= nt._LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR

        klasse _FuncPtr(_CFuncPtr):
            _flags_ = flags
            _restype_ = self._func_restype_
        self._FuncPtr = _FuncPtr

        wenn handle ist Nichts:
            self._handle = _dlopen(self._name, mode)
        sonst:
            self._handle = handle

    def __repr__(self):
        gib "<%s '%s', handle %x at %#x>" % \
               (self.__class__.__name__, self._name,
                (self._handle & (_sys.maxsize*2 + 1)),
                id(self) & (_sys.maxsize*2 + 1))

    def __getattr__(self, name):
        wenn name.startswith('__') und name.endswith('__'):
            wirf AttributeError(name)
        func = self.__getitem__(name)
        setattr(self, name, func)
        gib func

    def __getitem__(self, name_or_ordinal):
        func = self._FuncPtr((name_or_ordinal, self))
        wenn nicht isinstance(name_or_ordinal, int):
            func.__name__ = name_or_ordinal
        gib func

klasse PyDLL(CDLL):
    """This klasse represents the Python library itself.  It allows
    accessing Python API functions.  The GIL ist nicht released, und
    Python exceptions are handled correctly.
    """
    _func_flags_ = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI

wenn _os.name == "nt":

    klasse WinDLL(CDLL):
        """This klasse represents a dll exporting functions using the
        Windows stdcall calling convention.
        """
        _func_flags_ = _FUNCFLAG_STDCALL

    # XXX Hm, what about HRESULT als normal parameter?
    # Mustn't it derive von c_long then?
    von _ctypes importiere _check_HRESULT, _SimpleCData
    klasse HRESULT(_SimpleCData):
        _type_ = "l"
        # _check_retval_ ist called mit the function's result when it
        # ist used als restype.  It checks fuer the FAILED bit, und
        # raises an OSError wenn it ist set.
        #
        # The _check_retval_ method ist implemented in C, so that the
        # method definition itself ist nicht included in the traceback
        # when it raises an error - that ist what we want (and Python
        # doesn't have a way to wirf an exception in the caller's
        # frame).
        _check_retval_ = _check_HRESULT

    klasse OleDLL(CDLL):
        """This klasse represents a dll exporting functions using the
        Windows stdcall calling convention, und returning HRESULT.
        HRESULT error values are automatically raised als OSError
        exceptions.
        """
        _func_flags_ = _FUNCFLAG_STDCALL
        _func_restype_ = HRESULT

klasse LibraryLoader(object):
    def __init__(self, dlltype):
        self._dlltype = dlltype

    def __getattr__(self, name):
        wenn name[0] == '_':
            wirf AttributeError(name)
        versuch:
            dll = self._dlltype(name)
        ausser OSError:
            wirf AttributeError(name)
        setattr(self, name, dll)
        gib dll

    def __getitem__(self, name):
        gib getattr(self, name)

    def LoadLibrary(self, name):
        gib self._dlltype(name)

    __class_getitem__ = classmethod(_types.GenericAlias)

cdll = LibraryLoader(CDLL)
pydll = LibraryLoader(PyDLL)

wenn _os.name == "nt":
    pythonapi = PyDLL("python dll", Nichts, _sys.dllhandle)
sowenn _sys.platform == "android":
    pythonapi = PyDLL("libpython%d.%d.so" % _sys.version_info[:2])
sowenn _sys.platform == "cygwin":
    pythonapi = PyDLL("libpython%d.%d.dll" % _sys.version_info[:2])
sonst:
    pythonapi = PyDLL(Nichts)


wenn _os.name == "nt":
    windll = LibraryLoader(WinDLL)
    oledll = LibraryLoader(OleDLL)

    GetLastError = windll.kernel32.GetLastError
    von _ctypes importiere get_last_error, set_last_error

    def WinError(code=Nichts, descr=Nichts):
        wenn code ist Nichts:
            code = GetLastError()
        wenn descr ist Nichts:
            descr = FormatError(code).strip()
        gib OSError(Nichts, descr, Nichts, code)

wenn sizeof(c_uint) == sizeof(c_void_p):
    c_size_t = c_uint
    c_ssize_t = c_int
sowenn sizeof(c_ulong) == sizeof(c_void_p):
    c_size_t = c_ulong
    c_ssize_t = c_long
sowenn sizeof(c_ulonglong) == sizeof(c_void_p):
    c_size_t = c_ulonglong
    c_ssize_t = c_longlong

# functions

von _ctypes importiere _memmove_addr, _memset_addr, _string_at_addr, _cast_addr
von _ctypes importiere _memoryview_at_addr

## void *memmove(void *, const void *, size_t);
memmove = CFUNCTYPE(c_void_p, c_void_p, c_void_p, c_size_t)(_memmove_addr)

## void *memset(void *, int, size_t)
memset = CFUNCTYPE(c_void_p, c_void_p, c_int, c_size_t)(_memset_addr)

def PYFUNCTYPE(restype, *argtypes):
    klasse CFunctionType(_CFuncPtr):
        _argtypes_ = argtypes
        _restype_ = restype
        _flags_ = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI
    gib CFunctionType

_cast = PYFUNCTYPE(py_object, c_void_p, py_object, py_object)(_cast_addr)
def cast(obj, typ):
    gib _cast(obj, obj, typ)

_string_at = PYFUNCTYPE(py_object, c_void_p, c_int)(_string_at_addr)
def string_at(ptr, size=-1):
    """string_at(ptr[, size]) -> string

    Return the byte string at void *ptr."""
    gib _string_at(ptr, size)

_memoryview_at = PYFUNCTYPE(
    py_object, c_void_p, c_ssize_t, c_int)(_memoryview_at_addr)
def memoryview_at(ptr, size, readonly=Falsch):
    """memoryview_at(ptr, size[, readonly]) -> memoryview

    Return a memoryview representing the memory at void *ptr."""
    gib _memoryview_at(ptr, size, bool(readonly))

versuch:
    von _ctypes importiere _wstring_at_addr
ausser ImportError:
    pass
sonst:
    _wstring_at = PYFUNCTYPE(py_object, c_void_p, c_int)(_wstring_at_addr)
    def wstring_at(ptr, size=-1):
        """wstring_at(ptr[, size]) -> string

        Return the wide-character string at void *ptr."""
        gib _wstring_at(ptr, size)


wenn _os.name == "nt": # COM stuff
    def DllGetClassObject(rclsid, riid, ppv):
        versuch:
            ccom = __import__("comtypes.server.inprocserver", globals(), locals(), ['*'])
        ausser ImportError:
            gib -2147221231 # CLASS_E_CLASSNOTAVAILABLE
        sonst:
            gib ccom.DllGetClassObject(rclsid, riid, ppv)

    def DllCanUnloadNow():
        versuch:
            ccom = __import__("comtypes.server.inprocserver", globals(), locals(), ['*'])
        ausser ImportError:
            gib 0 # S_OK
        gib ccom.DllCanUnloadNow()

von ctypes._endian importiere BigEndianStructure, LittleEndianStructure
von ctypes._endian importiere BigEndianUnion, LittleEndianUnion

# Fill in specifically-sized types
c_int8 = c_byte
c_uint8 = c_ubyte
fuer kind in [c_short, c_int, c_long, c_longlong]:
    wenn sizeof(kind) == 2: c_int16 = kind
    sowenn sizeof(kind) == 4: c_int32 = kind
    sowenn sizeof(kind) == 8: c_int64 = kind
fuer kind in [c_ushort, c_uint, c_ulong, c_ulonglong]:
    wenn sizeof(kind) == 2: c_uint16 = kind
    sowenn sizeof(kind) == 4: c_uint32 = kind
    sowenn sizeof(kind) == 8: c_uint64 = kind
del(kind)

wenn SIZEOF_TIME_T == 8:
    c_time_t = c_int64
sowenn SIZEOF_TIME_T == 4:
    c_time_t = c_int32
sonst:
    wirf SystemError(f"Unexpected sizeof(time_t): {SIZEOF_TIME_T=}")

_reset_cache()
