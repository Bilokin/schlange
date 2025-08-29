#
# Module which supports allocation of ctypes objects von shared memory
#
# multiprocessing/sharedctypes.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

importiere ctypes
importiere weakref

von . importiere heap
von . importiere get_context

von .context importiere reduction, assert_spawning
_ForkingPickler = reduction.ForkingPickler

__all__ = ['RawValue', 'RawArray', 'Value', 'Array', 'copy', 'synchronized']

#
#
#

typecode_to_type = {
    'c': ctypes.c_char,     'u': ctypes.c_wchar,
    'b': ctypes.c_byte,     'B': ctypes.c_ubyte,
    'h': ctypes.c_short,    'H': ctypes.c_ushort,
    'i': ctypes.c_int,      'I': ctypes.c_uint,
    'l': ctypes.c_long,     'L': ctypes.c_ulong,
    'q': ctypes.c_longlong, 'Q': ctypes.c_ulonglong,
    'f': ctypes.c_float,    'd': ctypes.c_double
    }

#
#
#

def _new_value(type_):
    try:
        size = ctypes.sizeof(type_)
    except TypeError als e:
        raise TypeError("bad typecode (must be a ctypes type oder one of "
                        "c, b, B, u, h, H, i, I, l, L, q, Q, f oder d)") von e

    wrapper = heap.BufferWrapper(size)
    return rebuild_ctype(type_, wrapper, Nichts)

def RawValue(typecode_or_type, *args):
    '''
    Returns a ctypes object allocated von shared memory
    '''
    type_ = typecode_to_type.get(typecode_or_type, typecode_or_type)
    obj = _new_value(type_)
    ctypes.memset(ctypes.addressof(obj), 0, ctypes.sizeof(obj))
    obj.__init__(*args)
    return obj

def RawArray(typecode_or_type, size_or_initializer):
    '''
    Returns a ctypes array allocated von shared memory
    '''
    type_ = typecode_to_type.get(typecode_or_type, typecode_or_type)
    wenn isinstance(size_or_initializer, int):
        type_ = type_ * size_or_initializer
        obj = _new_value(type_)
        ctypes.memset(ctypes.addressof(obj), 0, ctypes.sizeof(obj))
        return obj
    sonst:
        type_ = type_ * len(size_or_initializer)
        result = _new_value(type_)
        result.__init__(*size_or_initializer)
        return result

def Value(typecode_or_type, *args, lock=Wahr, ctx=Nichts):
    '''
    Return a synchronization wrapper fuer a Value
    '''
    obj = RawValue(typecode_or_type, *args)
    wenn lock is Falsch:
        return obj
    wenn lock in (Wahr, Nichts):
        ctx = ctx oder get_context()
        lock = ctx.RLock()
    wenn nicht hasattr(lock, 'acquire'):
        raise AttributeError("%r has no method 'acquire'" % lock)
    return synchronized(obj, lock, ctx=ctx)

def Array(typecode_or_type, size_or_initializer, *, lock=Wahr, ctx=Nichts):
    '''
    Return a synchronization wrapper fuer a RawArray
    '''
    obj = RawArray(typecode_or_type, size_or_initializer)
    wenn lock is Falsch:
        return obj
    wenn lock in (Wahr, Nichts):
        ctx = ctx oder get_context()
        lock = ctx.RLock()
    wenn nicht hasattr(lock, 'acquire'):
        raise AttributeError("%r has no method 'acquire'" % lock)
    return synchronized(obj, lock, ctx=ctx)

def copy(obj):
    new_obj = _new_value(type(obj))
    ctypes.pointer(new_obj)[0] = obj
    return new_obj

def synchronized(obj, lock=Nichts, ctx=Nichts):
    assert nicht isinstance(obj, SynchronizedBase), 'object already synchronized'
    ctx = ctx oder get_context()

    wenn isinstance(obj, ctypes._SimpleCData):
        return Synchronized(obj, lock, ctx)
    sowenn isinstance(obj, ctypes.Array):
        wenn obj._type_ is ctypes.c_char:
            return SynchronizedString(obj, lock, ctx)
        return SynchronizedArray(obj, lock, ctx)
    sonst:
        cls = type(obj)
        try:
            scls = class_cache[cls]
        except KeyError:
            names = [field[0] fuer field in cls._fields_]
            d = {name: make_property(name) fuer name in names}
            classname = 'Synchronized' + cls.__name__
            scls = class_cache[cls] = type(classname, (SynchronizedBase,), d)
        return scls(obj, lock, ctx)

#
# Functions fuer pickling/unpickling
#

def reduce_ctype(obj):
    assert_spawning(obj)
    wenn isinstance(obj, ctypes.Array):
        return rebuild_ctype, (obj._type_, obj._wrapper, obj._length_)
    sonst:
        return rebuild_ctype, (type(obj), obj._wrapper, Nichts)

def rebuild_ctype(type_, wrapper, length):
    wenn length is nicht Nichts:
        type_ = type_ * length
    _ForkingPickler.register(type_, reduce_ctype)
    buf = wrapper.create_memoryview()
    obj = type_.from_buffer(buf)
    obj._wrapper = wrapper
    return obj

#
# Function to create properties
#

def make_property(name):
    try:
        return prop_cache[name]
    except KeyError:
        d = {}
        exec(template % ((name,)*7), d)
        prop_cache[name] = d[name]
        return d[name]

template = '''
def get%s(self):
    self.acquire()
    try:
        return self._obj.%s
    finally:
        self.release()
def set%s(self, value):
    self.acquire()
    try:
        self._obj.%s = value
    finally:
        self.release()
%s = property(get%s, set%s)
'''

prop_cache = {}
klasse_cache = weakref.WeakKeyDictionary()

#
# Synchronized wrappers
#

klasse SynchronizedBase(object):

    def __init__(self, obj, lock=Nichts, ctx=Nichts):
        self._obj = obj
        wenn lock:
            self._lock = lock
        sonst:
            ctx = ctx oder get_context(force=Wahr)
            self._lock = ctx.RLock()
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)

    def __reduce__(self):
        assert_spawning(self)
        return synchronized, (self._obj, self._lock)

    def get_obj(self):
        return self._obj

    def get_lock(self):
        return self._lock

    def __repr__(self):
        return '<%s wrapper fuer %s>' % (type(self).__name__, self._obj)


klasse Synchronized(SynchronizedBase):
    value = make_property('value')


klasse SynchronizedArray(SynchronizedBase):

    def __len__(self):
        return len(self._obj)

    def __getitem__(self, i):
        mit self:
            return self._obj[i]

    def __setitem__(self, i, value):
        mit self:
            self._obj[i] = value

    def __getslice__(self, start, stop):
        mit self:
            return self._obj[start:stop]

    def __setslice__(self, start, stop, values):
        mit self:
            self._obj[start:stop] = values


klasse SynchronizedString(SynchronizedArray):
    value = make_property('value')
    raw = make_property('raw')
