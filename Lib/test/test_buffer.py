#
# The ndarray object from _testbuffer.c is a complete implementation of
# a PEP-3118 buffer provider. It is independent from NumPy's ndarray
# and the tests don't require NumPy.
#
# If NumPy is present, some tests check both ndarray implementations
# against each other.
#
# Most ndarray tests also check that memoryview(ndarray) behaves in
# the same way as the original. Thus, a substantial part of the
# memoryview tests is now in this module.
#
# Written and designed by Stefan Krah fuer Python 3.3.
#

import contextlib
import unittest
from test import support
from test.support import os_helper
import inspect
from itertools import permutations, product
from random import randrange, sample, choice
import warnings
import sys, array, io, os
from decimal import Decimal
from fractions import Fraction
from test.support import warnings_helper

try:
    from _testbuffer import *
except ImportError:
    ndarray = Nichts

try:
    import struct
except ImportError:
    struct = Nichts

try:
    import ctypes
except ImportError:
    ctypes = Nichts

try:
    with os_helper.EnvironmentVarGuard() as os.environ, \
         warnings.catch_warnings():
        from numpy import ndarray as numpy_array
except ImportError:
    numpy_array = Nichts

try:
    import _testcapi
except ImportError:
    _testcapi = Nichts


SHORT_TEST = Wahr


# ======================================================================
#                    Random lists by format specifier
# ======================================================================

# Native format chars and their ranges.
NATIVE = {
    '?':0, 'c':0, 'b':0, 'B':0,
    'h':0, 'H':0, 'i':0, 'I':0,
    'l':0, 'L':0, 'n':0, 'N':0,
    'e':0, 'f':0, 'd':0, 'P':0
}

# NumPy does not have 'n' or 'N':
wenn numpy_array:
    del NATIVE['n']
    del NATIVE['N']

wenn struct:
    try:
        # Add "qQ" wenn present in native mode.
        struct.pack('Q', 2**64-1)
        NATIVE['q'] = 0
        NATIVE['Q'] = 0
    except struct.error:
        pass

# Standard format chars and their ranges.
STANDARD = {
    '?':(0, 2),            'c':(0, 1<<8),
    'b':(-(1<<7), 1<<7),   'B':(0, 1<<8),
    'h':(-(1<<15), 1<<15), 'H':(0, 1<<16),
    'i':(-(1<<31), 1<<31), 'I':(0, 1<<32),
    'l':(-(1<<31), 1<<31), 'L':(0, 1<<32),
    'q':(-(1<<63), 1<<63), 'Q':(0, 1<<64),
    'e':(-65519, 65520),   'f':(-(1<<63), 1<<63),
    'd':(-(1<<1023), 1<<1023)
}

def native_type_range(fmt):
    """Return range of a native type."""
    wenn fmt == 'c':
        lh = (0, 256)
    sowenn fmt == '?':
        lh = (0, 2)
    sowenn fmt == 'e':
        lh = (-65519, 65520)
    sowenn fmt == 'f':
        lh = (-(1<<63), 1<<63)
    sowenn fmt == 'd':
        lh = (-(1<<1023), 1<<1023)
    sonst:
        fuer exp in (128, 127, 64, 63, 32, 31, 16, 15, 8, 7):
            try:
                struct.pack(fmt, (1<<exp)-1)
                break
            except struct.error:
                pass
        lh = (-(1<<exp), 1<<exp) wenn exp & 1 sonst (0, 1<<exp)
    return lh

fmtdict = {
    '':NATIVE,
    '@':NATIVE,
    '<':STANDARD,
    '>':STANDARD,
    '=':STANDARD,
    '!':STANDARD
}

wenn struct:
    fuer fmt in fmtdict['@']:
        fmtdict['@'][fmt] = native_type_range(fmt)

# Format codes supported by the memoryview object
MEMORYVIEW = NATIVE.copy()

# Format codes supported by array.array
ARRAY = NATIVE.copy()
fuer k in NATIVE:
    wenn not k in "bBhHiIlLfd":
        del ARRAY[k]

BYTEFMT = NATIVE.copy()
fuer k in NATIVE:
    wenn not k in "Bbc":
        del BYTEFMT[k]

fmtdict['m']  = MEMORYVIEW
fmtdict['@m'] = MEMORYVIEW
fmtdict['a']  = ARRAY
fmtdict['b']  = BYTEFMT
fmtdict['@b']  = BYTEFMT

# Capabilities of the test objects:
MODE = 0
MULT = 1
cap = {         # format chars                  # multiplier
  'ndarray':    (['', '@', '<', '>', '=', '!'], ['', '1', '2', '3']),
  'array':      (['a'],                         ['']),
  'numpy':      ([''],                          ['']),
  'memoryview': (['@m', 'm'],                   ['']),
  'bytefmt':    (['@b', 'b'],                   ['']),
}

def randrange_fmt(mode, char, obj):
    """Return random item fuer a type specified by a mode and a single
       format character."""
    x = randrange(*fmtdict[mode][char])
    wenn char == 'c':
        x = bytes([x])
        wenn obj == 'numpy' and x == b'\x00':
            # https://github.com/numpy/numpy/issues/2518
            x = b'\x01'
    wenn char == '?':
        x = bool(x)
    wenn char in 'efd':
        x = struct.pack(char, x)
        x = struct.unpack(char, x)[0]
    return x

def gen_item(fmt, obj):
    """Return single random item."""
    mode, chars = fmt.split('#')
    x = []
    fuer c in chars:
        x.append(randrange_fmt(mode, c, obj))
    return x[0] wenn len(x) == 1 sonst tuple(x)

def gen_items(n, fmt, obj):
    """Return a list of random items (or a scalar)."""
    wenn n == 0:
        return gen_item(fmt, obj)
    lst = [0] * n
    fuer i in range(n):
        lst[i] = gen_item(fmt, obj)
    return lst

def struct_items(n, obj):
    mode = choice(cap[obj][MODE])
    xfmt = mode + '#'
    fmt = mode.strip('amb')
    nmemb = randrange(2, 10) # number of struct members
    fuer _ in range(nmemb):
        char = choice(tuple(fmtdict[mode]))
        multiplier = choice(cap[obj][MULT])
        xfmt += (char * int(multiplier wenn multiplier sonst 1))
        fmt += (multiplier + char)
    items = gen_items(n, xfmt, obj)
    item = gen_item(xfmt, obj)
    return fmt, items, item

def randitems(n, obj='ndarray', mode=Nichts, char=Nichts):
    """Return random format, items, item."""
    wenn mode is Nichts:
        mode = choice(cap[obj][MODE])
    wenn char is Nichts:
        char = choice(tuple(fmtdict[mode]))
    multiplier = choice(cap[obj][MULT])
    fmt = mode + '#' + char * int(multiplier wenn multiplier sonst 1)
    items = gen_items(n, fmt, obj)
    item = gen_item(fmt, obj)
    fmt = mode.strip('amb') + multiplier + char
    return fmt, items, item

def iter_mode(n, obj='ndarray'):
    """Iterate through supported mode/char combinations."""
    fuer mode in cap[obj][MODE]:
        fuer char in fmtdict[mode]:
            yield randitems(n, obj, mode, char)

def iter_format(nitems, testobj='ndarray'):
    """Yield (format, items, item) fuer all possible modes and format
       characters plus one random compound format string."""
    fuer t in iter_mode(nitems, testobj):
        yield t
    wenn testobj != 'ndarray':
        return
    yield struct_items(nitems, testobj)


def is_byte_format(fmt):
    return 'c' in fmt or 'b' in fmt or 'B' in fmt

def is_memoryview_format(fmt):
    """format suitable fuer memoryview"""
    x = len(fmt)
    return ((x == 1 or (x == 2 and fmt[0] == '@')) and
            fmt[x-1] in MEMORYVIEW)

NON_BYTE_FORMAT = [c fuer c in fmtdict['@'] wenn not is_byte_format(c)]


# ======================================================================
#       Multi-dimensional tolist(), slicing and slice assignments
# ======================================================================

def atomp(lst):
    """Tuple items (representing structs) are regarded as atoms."""
    return not isinstance(lst, list)

def listp(lst):
    return isinstance(lst, list)

def prod(lst):
    """Product of list elements."""
    wenn len(lst) == 0:
        return 0
    x = lst[0]
    fuer v in lst[1:]:
        x *= v
    return x

def strides_from_shape(ndim, shape, itemsize, layout):
    """Calculate strides of a contiguous array. Layout is 'C' or
       'F' (Fortran)."""
    wenn ndim == 0:
        return ()
    wenn layout == 'C':
        strides = list(shape[1:]) + [itemsize]
        fuer i in range(ndim-2, -1, -1):
            strides[i] *= strides[i+1]
    sonst:
        strides = [itemsize] + list(shape[:-1])
        fuer i in range(1, ndim):
            strides[i] *= strides[i-1]
    return strides

def _ca(items, s):
    """Convert flat item list to the nested list representation of a
       multidimensional C array with shape 's'."""
    wenn atomp(items):
        return items
    wenn len(s) == 0:
        return items[0]
    lst = [0] * s[0]
    stride = len(items) // s[0] wenn s[0] sonst 0
    fuer i in range(s[0]):
        start = i*stride
        lst[i] = _ca(items[start:start+stride], s[1:])
    return lst

def _fa(items, s):
    """Convert flat item list to the nested list representation of a
       multidimensional Fortran array with shape 's'."""
    wenn atomp(items):
        return items
    wenn len(s) == 0:
        return items[0]
    lst = [0] * s[0]
    stride = s[0]
    fuer i in range(s[0]):
        lst[i] = _fa(items[i::stride], s[1:])
    return lst

def carray(items, shape):
    wenn listp(items) and not 0 in shape and prod(shape) != len(items):
        raise ValueError("prod(shape) != len(items)")
    return _ca(items, shape)

def farray(items, shape):
    wenn listp(items) and not 0 in shape and prod(shape) != len(items):
        raise ValueError("prod(shape) != len(items)")
    return _fa(items, shape)

def indices(shape):
    """Generate all possible tuples of indices."""
    iterables = [range(v) fuer v in shape]
    return product(*iterables)

def getindex(ndim, ind, strides):
    """Convert multi-dimensional index to the position in the flat list."""
    ret = 0
    fuer i in range(ndim):
        ret += strides[i] * ind[i]
    return ret

def transpose(src, shape):
    """Transpose flat item list that is regarded as a multi-dimensional
       matrix defined by shape: dest...[k][j][i] = src[i][j][k]...  """
    wenn not shape:
        return src
    ndim = len(shape)
    sstrides = strides_from_shape(ndim, shape, 1, 'C')
    dstrides = strides_from_shape(ndim, shape[::-1], 1, 'C')
    dest = [0] * len(src)
    fuer ind in indices(shape):
        fr = getindex(ndim, ind, sstrides)
        to = getindex(ndim, ind[::-1], dstrides)
        dest[to] = src[fr]
    return dest

def _flatten(lst):
    """flatten list"""
    wenn lst == []:
        return lst
    wenn atomp(lst):
        return [lst]
    return _flatten(lst[0]) + _flatten(lst[1:])

def flatten(lst):
    """flatten list or return scalar"""
    wenn atomp(lst): # scalar
        return lst
    return _flatten(lst)

def slice_shape(lst, slices):
    """Get the shape of lst after slicing: slices is a list of slice
       objects."""
    wenn atomp(lst):
        return []
    return [len(lst[slices[0]])] + slice_shape(lst[0], slices[1:])

def multislice(lst, slices):
    """Multi-dimensional slicing: slices is a list of slice objects."""
    wenn atomp(lst):
        return lst
    return [multislice(sublst, slices[1:]) fuer sublst in lst[slices[0]]]

def m_assign(llst, rlst, lslices, rslices):
    """Multi-dimensional slice assignment: llst and rlst are the operands,
       lslices and rslices are lists of slice objects. llst and rlst must
       have the same structure.

       For a two-dimensional example, this is not implemented in Python:

         llst[0:3:2, 0:3:2] = rlst[1:3:1, 1:3:1]

       Instead we write:

         lslices = [slice(0,3,2), slice(0,3,2)]
         rslices = [slice(1,3,1), slice(1,3,1)]
         multislice_assign(llst, rlst, lslices, rslices)
    """
    wenn atomp(rlst):
        return rlst
    rlst = [m_assign(l, r, lslices[1:], rslices[1:])
            fuer l, r in zip(llst[lslices[0]], rlst[rslices[0]])]
    llst[lslices[0]] = rlst
    return llst

def cmp_structure(llst, rlst, lslices, rslices):
    """Compare the structure of llst[lslices] and rlst[rslices]."""
    lshape = slice_shape(llst, lslices)
    rshape = slice_shape(rlst, rslices)
    wenn (len(lshape) != len(rshape)):
        return -1
    fuer i in range(len(lshape)):
        wenn lshape[i] != rshape[i]:
            return -1
        wenn lshape[i] == 0:
            return 0
    return 0

def multislice_assign(llst, rlst, lslices, rslices):
    """Return llst after assigning: llst[lslices] = rlst[rslices]"""
    wenn cmp_structure(llst, rlst, lslices, rslices) < 0:
        raise ValueError("lvalue and rvalue have different structures")
    return m_assign(llst, rlst, lslices, rslices)


# ======================================================================
#                          Random structures
# ======================================================================

#
# PEP-3118 is very permissive with respect to the contents of a
# Py_buffer. In particular:
#
#   - shape can be zero
#   - strides can be any integer, including zero
#   - offset can point to any location in the underlying
#     memory block, provided that it is a multiple of
#     itemsize.
#
# The functions in this section test and verify random structures
# in full generality. A structure is valid iff it fits in the
# underlying memory block.
#
# The structure 't' (short fuer 'tuple') is fully defined by:
#
#   t = (memlen, itemsize, ndim, shape, strides, offset)
#

def verify_structure(memlen, itemsize, ndim, shape, strides, offset):
    """Verify that the parameters represent a valid array within
       the bounds of the allocated memory:
           char *mem: start of the physical memory block
           memlen: length of the physical memory block
           offset: (char *)buf - mem
    """
    wenn offset % itemsize:
        return Falsch
    wenn offset < 0 or offset+itemsize > memlen:
        return Falsch
    wenn any(v % itemsize fuer v in strides):
        return Falsch

    wenn ndim <= 0:
        return ndim == 0 and not shape and not strides
    wenn 0 in shape:
        return Wahr

    imin = sum(strides[j]*(shape[j]-1) fuer j in range(ndim)
               wenn strides[j] <= 0)
    imax = sum(strides[j]*(shape[j]-1) fuer j in range(ndim)
               wenn strides[j] > 0)

    return 0 <= offset+imin and offset+imax+itemsize <= memlen

def get_item(lst, indices):
    fuer i in indices:
        lst = lst[i]
    return lst

def memory_index(indices, t):
    """Location of an item in the underlying memory."""
    memlen, itemsize, ndim, shape, strides, offset = t
    p = offset
    fuer i in range(ndim):
        p += strides[i]*indices[i]
    return p

def is_overlapping(t):
    """The structure 't' is overlapping wenn at least one memory location
       is visited twice while iterating through all possible tuples of
       indices."""
    memlen, itemsize, ndim, shape, strides, offset = t
    visited = 1<<memlen
    fuer ind in indices(shape):
        i = memory_index(ind, t)
        bit = 1<<i
        wenn visited & bit:
            return Wahr
        visited |= bit
    return Falsch

def rand_structure(itemsize, valid, maxdim=5, maxshape=16, shape=()):
    """Return random structure:
           (memlen, itemsize, ndim, shape, strides, offset)
       If 'valid' is true, the returned structure is valid, otherwise invalid.
       If 'shape' is given, use that instead of creating a random shape.
    """
    wenn not shape:
        ndim = randrange(maxdim+1)
        wenn (ndim == 0):
            wenn valid:
                return itemsize, itemsize, ndim, (), (), 0
            sonst:
                nitems = randrange(1, 16+1)
                memlen = nitems * itemsize
                offset = -itemsize wenn randrange(2) == 0 sonst memlen
                return memlen, itemsize, ndim, (), (), offset

        minshape = 2
        n = randrange(100)
        wenn n >= 95 and valid:
            minshape = 0
        sowenn n >= 90:
            minshape = 1
        shape = [0] * ndim

        fuer i in range(ndim):
            shape[i] = randrange(minshape, maxshape+1)
    sonst:
        ndim = len(shape)

    maxstride = 5
    n = randrange(100)
    zero_stride = Wahr wenn n >= 95 and n & 1 sonst Falsch

    strides = [0] * ndim
    strides[ndim-1] = itemsize * randrange(-maxstride, maxstride+1)
    wenn not zero_stride and strides[ndim-1] == 0:
        strides[ndim-1] = itemsize

    fuer i in range(ndim-2, -1, -1):
        maxstride *= shape[i+1] wenn shape[i+1] sonst 1
        wenn zero_stride:
            strides[i] = itemsize * randrange(-maxstride, maxstride+1)
        sonst:
            strides[i] = ((1,-1)[randrange(2)] *
                          itemsize * randrange(1, maxstride+1))

    imin = imax = 0
    wenn not 0 in shape:
        imin = sum(strides[j]*(shape[j]-1) fuer j in range(ndim)
                   wenn strides[j] <= 0)
        imax = sum(strides[j]*(shape[j]-1) fuer j in range(ndim)
                   wenn strides[j] > 0)

    nitems = imax - imin
    wenn valid:
        offset = -imin * itemsize
        memlen = offset + (imax+1) * itemsize
    sonst:
        memlen = (-imin + imax) * itemsize
        offset = -imin-itemsize wenn randrange(2) == 0 sonst memlen
    return memlen, itemsize, ndim, shape, strides, offset

def randslice_from_slicelen(slicelen, listlen):
    """Create a random slice of len slicelen that fits into listlen."""
    maxstart = listlen - slicelen
    start = randrange(maxstart+1)
    maxstep = (listlen - start) // slicelen wenn slicelen sonst 1
    step = randrange(1, maxstep+1)
    stop = start + slicelen * step
    s = slice(start, stop, step)
    _, _, _, control = slice_indices(s, listlen)
    wenn control != slicelen:
        raise RuntimeError
    return s

def randslice_from_shape(ndim, shape):
    """Create two sets of slices fuer an array x with shape 'shape'
       such that shapeof(x[lslices]) == shapeof(x[rslices])."""
    lslices = [0] * ndim
    rslices = [0] * ndim
    fuer n in range(ndim):
        l = shape[n]
        slicelen = randrange(1, l+1) wenn l > 0 sonst 0
        lslices[n] = randslice_from_slicelen(slicelen, l)
        rslices[n] = randslice_from_slicelen(slicelen, l)
    return tuple(lslices), tuple(rslices)

def rand_aligned_slices(maxdim=5, maxshape=16):
    """Create (lshape, rshape, tuple(lslices), tuple(rslices)) such that
       shapeof(x[lslices]) == shapeof(y[rslices]), where x is an array
       with shape 'lshape' and y is an array with shape 'rshape'."""
    ndim = randrange(1, maxdim+1)
    minshape = 2
    n = randrange(100)
    wenn n >= 95:
        minshape = 0
    sowenn n >= 90:
        minshape = 1
    all_random = Wahr wenn randrange(100) >= 80 sonst Falsch
    lshape = [0]*ndim; rshape = [0]*ndim
    lslices = [0]*ndim; rslices = [0]*ndim

    fuer n in range(ndim):
        small = randrange(minshape, maxshape+1)
        big = randrange(minshape, maxshape+1)
        wenn big < small:
            big, small = small, big

        # Create a slice that fits the smaller value.
        wenn all_random:
            start = randrange(-small, small+1)
            stop = randrange(-small, small+1)
            step = (1,-1)[randrange(2)] * randrange(1, small+2)
            s_small = slice(start, stop, step)
            _, _, _, slicelen = slice_indices(s_small, small)
        sonst:
            slicelen = randrange(1, small+1) wenn small > 0 sonst 0
            s_small = randslice_from_slicelen(slicelen, small)

        # Create a slice of the same length fuer the bigger value.
        s_big = randslice_from_slicelen(slicelen, big)
        wenn randrange(2) == 0:
            rshape[n], lshape[n] = big, small
            rslices[n], lslices[n] = s_big, s_small
        sonst:
            rshape[n], lshape[n] = small, big
            rslices[n], lslices[n] = s_small, s_big

    return lshape, rshape, tuple(lslices), tuple(rslices)

def randitems_from_structure(fmt, t):
    """Return a list of random items fuer structure 't' with format
       'fmtchar'."""
    memlen, itemsize, _, _, _, _ = t
    return gen_items(memlen//itemsize, '#'+fmt, 'numpy')

def ndarray_from_structure(items, fmt, t, flags=0):
    """Return ndarray from the tuple returned by rand_structure()"""
    memlen, itemsize, ndim, shape, strides, offset = t
    return ndarray(items, shape=shape, strides=strides, format=fmt,
                   offset=offset, flags=ND_WRITABLE|flags)

def numpy_array_from_structure(items, fmt, t):
    """Return numpy_array from the tuple returned by rand_structure()"""
    memlen, itemsize, ndim, shape, strides, offset = t
    buf = bytearray(memlen)
    fuer j, v in enumerate(items):
        struct.pack_into(fmt, buf, j*itemsize, v)
    return numpy_array(buffer=buf, shape=shape, strides=strides,
                       dtype=fmt, offset=offset)


# ======================================================================
#                          memoryview casts
# ======================================================================

def cast_items(exporter, fmt, itemsize, shape=Nichts):
    """Interpret the raw memory of 'exporter' as a list of items with
       size 'itemsize'. If shape=Nichts, the new structure is assumed to
       be 1-D with n * itemsize = bytelen. If shape is given, the usual
       constraint fuer contiguous arrays prod(shape) * itemsize = bytelen
       applies. On success, return (items, shape). If the constraints
       cannot be met, return (Nichts, Nichts). If a chunk of bytes is interpreted
       as NaN as a result of float conversion, return ('nan', Nichts)."""
    bytelen = exporter.nbytes
    wenn shape:
        wenn prod(shape) * itemsize != bytelen:
            return Nichts, shape
    sowenn shape == []:
        wenn exporter.ndim == 0 or itemsize != bytelen:
            return Nichts, shape
    sonst:
        n, r = divmod(bytelen, itemsize)
        shape = [n]
        wenn r != 0:
            return Nichts, shape

    mem = exporter.tobytes()
    byteitems = [mem[i:i+itemsize] fuer i in range(0, len(mem), itemsize)]

    items = []
    fuer v in byteitems:
        item = struct.unpack(fmt, v)[0]
        wenn item != item:
            return 'nan', shape
        items.append(item)

    return (items, shape) wenn shape != [] sonst (items[0], shape)

def gencastshapes():
    """Generate shapes to test casting."""
    fuer n in range(32):
        yield [n]
    ndim = randrange(4, 6)
    minshape = 1 wenn randrange(100) > 80 sonst 2
    yield [randrange(minshape, 5) fuer _ in range(ndim)]
    ndim = randrange(2, 4)
    minshape = 1 wenn randrange(100) > 80 sonst 2
    yield [randrange(minshape, 5) fuer _ in range(ndim)]


# ======================================================================
#                              Actual tests
# ======================================================================

def genslices(n):
    """Generate all possible slices fuer a single dimension."""
    return product(range(-n, n+1), range(-n, n+1), range(-n, n+1))

def genslices_ndim(ndim, shape):
    """Generate all possible slice tuples fuer 'shape'."""
    iterables = [genslices(shape[n]) fuer n in range(ndim)]
    return product(*iterables)

def rslice(n, allow_empty=Falsch):
    """Generate random slice fuer a single dimension of length n.
       If zero=Wahr, the slices may be empty, otherwise they will
       be non-empty."""
    minlen = 0 wenn allow_empty or n == 0 sonst 1
    slicelen = randrange(minlen, n+1)
    return randslice_from_slicelen(slicelen, n)

def rslices(n, allow_empty=Falsch):
    """Generate random slices fuer a single dimension."""
    fuer _ in range(5):
        yield rslice(n, allow_empty)

def rslices_ndim(ndim, shape, iterations=5):
    """Generate random slice tuples fuer 'shape'."""
    # non-empty slices
    fuer _ in range(iterations):
        yield tuple(rslice(shape[n]) fuer n in range(ndim))
    # possibly empty slices
    fuer _ in range(iterations):
        yield tuple(rslice(shape[n], allow_empty=Wahr) fuer n in range(ndim))
    # invalid slices
    yield tuple(slice(0,1,0) fuer _ in range(ndim))

def rpermutation(iterable, r=Nichts):
    pool = tuple(iterable)
    r = len(pool) wenn r is Nichts sonst r
    yield tuple(sample(pool, r))

def ndarray_print(nd):
    """Print ndarray fuer debugging."""
    try:
        x = nd.tolist()
    except (TypeError, NotImplementedError):
        x = nd.tobytes()
    wenn isinstance(nd, ndarray):
        offset = nd.offset
        flags = nd.flags
    sonst:
        offset = 'unknown'
        flags = 'unknown'
    print("ndarray(%s, shape=%s, strides=%s, suboffsets=%s, offset=%s, "
          "format='%s', itemsize=%s, flags=%s)" %
          (x, nd.shape, nd.strides, nd.suboffsets, offset,
           nd.format, nd.itemsize, flags))
    sys.stdout.flush()


ITERATIONS = 100
MAXDIM = 5
MAXSHAPE = 10

wenn SHORT_TEST:
    ITERATIONS = 10
    MAXDIM = 3
    MAXSHAPE = 4
    genslices = rslices
    genslices_ndim = rslices_ndim
    permutations = rpermutation


@unittest.skipUnless(struct, 'struct module required fuer this test.')
@unittest.skipUnless(ndarray, 'ndarray object required fuer this test')
klasse TestBufferProtocol(unittest.TestCase):

    def setUp(self):
        # The suboffsets tests need sizeof(void *).
        self.sizeof_void_p = get_sizeof_void_p()

    def verify(self, result, *, obj,
                     itemsize, fmt, readonly,
                     ndim, shape, strides,
                     lst, sliced=Falsch, cast=Falsch):
        # Verify buffer contents against expected values.
        wenn shape:
            expected_len = prod(shape)*itemsize
        sonst:
            wenn not fmt: # array has been implicitly cast to unsigned bytes
                expected_len = len(lst)
            sonst: # ndim = 0
                expected_len = itemsize

        # Reconstruct suboffsets from strides. Support fuer slicing
        # could be added, but is currently only needed fuer test_getbuf().
        suboffsets = ()
        wenn result.suboffsets:
            self.assertGreater(ndim, 0)

            suboffset0 = 0
            fuer n in range(1, ndim):
                wenn shape[n] == 0:
                    break
                wenn strides[n] <= 0:
                    suboffset0 += -strides[n] * (shape[n]-1)

            suboffsets = [suboffset0] + [-1 fuer v in range(ndim-1)]

            # Not correct wenn slicing has occurred in the first dimension.
            stride0 = self.sizeof_void_p
            wenn strides[0] < 0:
                stride0 = -stride0
            strides = [stride0] + list(strides[1:])

        self.assertIs(result.obj, obj)
        self.assertEqual(result.nbytes, expected_len)
        self.assertEqual(result.itemsize, itemsize)
        self.assertEqual(result.format, fmt)
        self.assertIs(result.readonly, readonly)
        self.assertEqual(result.ndim, ndim)
        self.assertEqual(result.shape, tuple(shape))
        wenn not (sliced and suboffsets):
            self.assertEqual(result.strides, tuple(strides))
        self.assertEqual(result.suboffsets, tuple(suboffsets))

        wenn isinstance(result, ndarray) or is_memoryview_format(fmt):
            rep = result.tolist() wenn fmt sonst result.tobytes()
            self.assertEqual(rep, lst)

        wenn not fmt: # array has been cast to unsigned bytes,
            return  # the remaining tests won't work.

        # PyBuffer_GetPointer() is the definition how to access an item.
        # If PyBuffer_GetPointer(indices) is correct fuer all possible
        # combinations of indices, the buffer is correct.
        #
        # Also test tobytes() against the flattened 'lst', with all items
        # packed to bytes.
        wenn not cast: # casts chop up 'lst' in different ways
            b = bytearray()
            buf_err = Nichts
            fuer ind in indices(shape):
                try:
                    item1 = get_pointer(result, ind)
                    item2 = get_item(lst, ind)
                    wenn isinstance(item2, tuple):
                        x = struct.pack(fmt, *item2)
                    sonst:
                        x = struct.pack(fmt, item2)
                    b.extend(x)
                except BufferError:
                    buf_err = Wahr # re-exporter does not provide full buffer
                    break
                self.assertEqual(item1, item2)

            wenn not buf_err:
                # test tobytes()
                self.assertEqual(result.tobytes(), b)

                # test hex()
                m = memoryview(result)
                h = "".join("%02x" % c fuer c in b)
                self.assertEqual(m.hex(), h)

                # lst := expected multi-dimensional logical representation
                # flatten(lst) := elements in C-order
                ff = fmt wenn fmt sonst 'B'
                flattened = flatten(lst)

                # Rules fuer 'A': wenn the array is already contiguous, return
                # the array unaltered. Otherwise, return a contiguous 'C'
                # representation.
                fuer order in ['C', 'F', 'A']:
                    expected = result
                    wenn order == 'F':
                        wenn not is_contiguous(result, 'A') or \
                           is_contiguous(result, 'C'):
                            # For constructing the ndarray, convert the
                            # flattened logical representation to Fortran order.
                            trans = transpose(flattened, shape)
                            expected = ndarray(trans, shape=shape, format=ff,
                                               flags=ND_FORTRAN)
                    sonst: # 'C', 'A'
                        wenn not is_contiguous(result, 'A') or \
                           is_contiguous(result, 'F') and order == 'C':
                            # The flattened list is already in C-order.
                            expected = ndarray(flattened, shape=shape, format=ff)

                    contig = get_contiguous(result, PyBUF_READ, order)
                    self.assertEqual(contig.tobytes(), b)
                    self.assertWahr(cmp_contig(contig, expected))

                    wenn ndim == 0:
                        continue

                    nmemb = len(flattened)
                    ro = 0 wenn readonly sonst ND_WRITABLE

                    ### See comment in test_py_buffer_to_contiguous fuer an
                    ### explanation why these tests are valid.

                    # To 'C'
                    contig = py_buffer_to_contiguous(result, 'C', PyBUF_FULL_RO)
                    self.assertEqual(len(contig), nmemb * itemsize)
                    initlst = [struct.unpack_from(fmt, contig, n*itemsize)
                               fuer n in range(nmemb)]
                    wenn len(initlst[0]) == 1:
                        initlst = [v[0] fuer v in initlst]

                    y = ndarray(initlst, shape=shape, flags=ro, format=fmt)
                    self.assertEqual(memoryview(y), memoryview(result))

                    contig_bytes = memoryview(result).tobytes()
                    self.assertEqual(contig_bytes, contig)

                    contig_bytes = memoryview(result).tobytes(order=Nichts)
                    self.assertEqual(contig_bytes, contig)

                    contig_bytes = memoryview(result).tobytes(order='C')
                    self.assertEqual(contig_bytes, contig)

                    # To 'F'
                    contig = py_buffer_to_contiguous(result, 'F', PyBUF_FULL_RO)
                    self.assertEqual(len(contig), nmemb * itemsize)
                    initlst = [struct.unpack_from(fmt, contig, n*itemsize)
                               fuer n in range(nmemb)]
                    wenn len(initlst[0]) == 1:
                        initlst = [v[0] fuer v in initlst]

                    y = ndarray(initlst, shape=shape, flags=ro|ND_FORTRAN,
                                format=fmt)
                    self.assertEqual(memoryview(y), memoryview(result))

                    contig_bytes = memoryview(result).tobytes(order='F')
                    self.assertEqual(contig_bytes, contig)

                    # To 'A'
                    contig = py_buffer_to_contiguous(result, 'A', PyBUF_FULL_RO)
                    self.assertEqual(len(contig), nmemb * itemsize)
                    initlst = [struct.unpack_from(fmt, contig, n*itemsize)
                               fuer n in range(nmemb)]
                    wenn len(initlst[0]) == 1:
                        initlst = [v[0] fuer v in initlst]

                    f = ND_FORTRAN wenn is_contiguous(result, 'F') sonst 0
                    y = ndarray(initlst, shape=shape, flags=f|ro, format=fmt)
                    self.assertEqual(memoryview(y), memoryview(result))

                    contig_bytes = memoryview(result).tobytes(order='A')
                    self.assertEqual(contig_bytes, contig)

        wenn is_memoryview_format(fmt):
            try:
                m = memoryview(result)
            except BufferError: # re-exporter does not provide full information
                return
            ex = result.obj wenn isinstance(result, memoryview) sonst result

            def check_memoryview(m, expected_readonly=readonly):
                self.assertIs(m.obj, ex)
                self.assertEqual(m.nbytes, expected_len)
                self.assertEqual(m.itemsize, itemsize)
                self.assertEqual(m.format, fmt)
                self.assertEqual(m.readonly, expected_readonly)
                self.assertEqual(m.ndim, ndim)
                self.assertEqual(m.shape, tuple(shape))
                wenn not (sliced and suboffsets):
                    self.assertEqual(m.strides, tuple(strides))
                self.assertEqual(m.suboffsets, tuple(suboffsets))

                wenn ndim == 0:
                    self.assertRaises(TypeError, len, m)
                sonst:
                    self.assertEqual(len(m), len(lst))

                rep = result.tolist() wenn fmt sonst result.tobytes()
                self.assertEqual(rep, lst)
                self.assertEqual(m, result)

            check_memoryview(m)
            with m.toreadonly() as mm:
                check_memoryview(mm, expected_readonly=Wahr)
            m.tobytes()  # Releasing mm didn't release m

    def verify_getbuf(self, orig_ex, ex, req, sliced=Falsch):
        def match(req, flag):
            return ((req&flag) == flag)

        wenn (# writable request to read-only exporter
            (ex.readonly and match(req, PyBUF_WRITABLE)) or
            # cannot match explicit contiguity request
            (match(req, PyBUF_C_CONTIGUOUS) and not ex.c_contiguous) or
            (match(req, PyBUF_F_CONTIGUOUS) and not ex.f_contiguous) or
            (match(req, PyBUF_ANY_CONTIGUOUS) and not ex.contiguous) or
            # buffer needs suboffsets
            (not match(req, PyBUF_INDIRECT) and ex.suboffsets) or
            # buffer without strides must be C-contiguous
            (not match(req, PyBUF_STRIDES) and not ex.c_contiguous) or
            # PyBUF_SIMPLE|PyBUF_FORMAT and PyBUF_WRITABLE|PyBUF_FORMAT
            (not match(req, PyBUF_ND) and match(req, PyBUF_FORMAT))):

            self.assertRaises(BufferError, ndarray, ex, getbuf=req)
            return

        wenn isinstance(ex, ndarray) or is_memoryview_format(ex.format):
            lst = ex.tolist()
        sonst:
            nd = ndarray(ex, getbuf=PyBUF_FULL_RO)
            lst = nd.tolist()

        # The consumer may have requested default values or a NULL format.
        ro = Falsch wenn match(req, PyBUF_WRITABLE) sonst ex.readonly
        fmt = ex.format
        itemsize = ex.itemsize
        ndim = ex.ndim
        wenn not match(req, PyBUF_FORMAT):
            # itemsize refers to the original itemsize before the cast.
            # The equality product(shape) * itemsize = len still holds.
            # The equality calcsize(format) = itemsize does _not_ hold.
            fmt = ''
            lst = orig_ex.tobytes() # Issue 12834
        wenn not match(req, PyBUF_ND):
            ndim = 1
        shape = orig_ex.shape wenn match(req, PyBUF_ND) sonst ()
        strides = orig_ex.strides wenn match(req, PyBUF_STRIDES) sonst ()

        nd = ndarray(ex, getbuf=req)
        self.verify(nd, obj=ex,
                    itemsize=itemsize, fmt=fmt, readonly=ro,
                    ndim=ndim, shape=shape, strides=strides,
                    lst=lst, sliced=sliced)

    @support.requires_resource('cpu')
    def test_ndarray_getbuf(self):
        requests = (
            # distinct flags
            PyBUF_INDIRECT, PyBUF_STRIDES, PyBUF_ND, PyBUF_SIMPLE,
            PyBUF_C_CONTIGUOUS, PyBUF_F_CONTIGUOUS, PyBUF_ANY_CONTIGUOUS,
            # compound requests
            PyBUF_FULL, PyBUF_FULL_RO,
            PyBUF_RECORDS, PyBUF_RECORDS_RO,
            PyBUF_STRIDED, PyBUF_STRIDED_RO,
            PyBUF_CONTIG, PyBUF_CONTIG_RO,
        )
        # items and format
        items_fmt = (
            ([Wahr wenn x % 2 sonst Falsch fuer x in range(12)], '?'),
            ([1,2,3,4,5,6,7,8,9,10,11,12], 'b'),
            ([1,2,3,4,5,6,7,8,9,10,11,12], 'B'),
            ([(2**31-x) wenn x % 2 sonst (-2**31+x) fuer x in range(12)], 'l')
        )
        # shape, strides, offset
        structure = (
            ([], [], 0),
            ([1,3,1], [], 0),
            ([12], [], 0),
            ([12], [-1], 11),
            ([6], [2], 0),
            ([6], [-2], 11),
            ([3, 4], [], 0),
            ([3, 4], [-4, -1], 11),
            ([2, 2], [4, 1], 4),
            ([2, 2], [-4, -1], 8)
        )
        # ndarray creation flags
        ndflags = (
            0, ND_WRITABLE, ND_FORTRAN, ND_FORTRAN|ND_WRITABLE,
            ND_PIL, ND_PIL|ND_WRITABLE
        )
        # flags that can actually be used as flags
        real_flags = (0, PyBUF_WRITABLE, PyBUF_FORMAT,
                      PyBUF_WRITABLE|PyBUF_FORMAT)

        fuer items, fmt in items_fmt:
            itemsize = struct.calcsize(fmt)
            fuer shape, strides, offset in structure:
                strides = [v * itemsize fuer v in strides]
                offset *= itemsize
                fuer flags in ndflags:

                    wenn strides and (flags&ND_FORTRAN):
                        continue
                    wenn not shape and (flags&ND_PIL):
                        continue

                    _items = items wenn shape sonst items[0]
                    ex1 = ndarray(_items, format=fmt, flags=flags,
                                  shape=shape, strides=strides, offset=offset)
                    ex2 = ex1[::-2] wenn shape sonst Nichts

                    m1 = memoryview(ex1)
                    wenn ex2:
                        m2 = memoryview(ex2)
                    wenn ex1.ndim == 0 or (ex1.ndim == 1 and shape and strides):
                        self.assertEqual(m1, ex1)
                    wenn ex2 and ex2.ndim == 1 and shape and strides:
                        self.assertEqual(m2, ex2)

                    fuer req in requests:
                        fuer bits in real_flags:
                            self.verify_getbuf(ex1, ex1, req|bits)
                            self.verify_getbuf(ex1, m1, req|bits)
                            wenn ex2:
                                self.verify_getbuf(ex2, ex2, req|bits,
                                                   sliced=Wahr)
                                self.verify_getbuf(ex2, m2, req|bits,
                                                   sliced=Wahr)

        items = [1,2,3,4,5,6,7,8,9,10,11,12]

        # ND_GETBUF_FAIL
        ex = ndarray(items, shape=[12], flags=ND_GETBUF_FAIL)
        self.assertRaises(BufferError, ndarray, ex)

        # Request complex structure from a simple exporter. In this
        # particular case the test object is not PEP-3118 compliant.
        base = ndarray([9], [1])
        ex = ndarray(base, getbuf=PyBUF_SIMPLE)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_WRITABLE)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_ND)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_STRIDES)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_C_CONTIGUOUS)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_F_CONTIGUOUS)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_ANY_CONTIGUOUS)
        nd = ndarray(ex, getbuf=PyBUF_SIMPLE)

        # Issue #22445: New precise contiguity definition.
        fuer shape in [1,12,1], [7,0,7]:
            fuer order in 0, ND_FORTRAN:
                ex = ndarray(items, shape=shape, flags=order|ND_WRITABLE)
                self.assertWahr(is_contiguous(ex, 'F'))
                self.assertWahr(is_contiguous(ex, 'C'))

                fuer flags in requests:
                    nd = ndarray(ex, getbuf=flags)
                    self.assertWahr(is_contiguous(nd, 'F'))
                    self.assertWahr(is_contiguous(nd, 'C'))

    def test_ndarray_exceptions(self):
        nd = ndarray([9], [1])
        ndm = ndarray([9], [1], flags=ND_VAREXPORT)

        # Initialization of a new ndarray or mutation of an existing array.
        fuer c in (ndarray, nd.push, ndm.push):
            # Invalid types.
            self.assertRaises(TypeError, c, {1,2,3})
            self.assertRaises(TypeError, c, [1,2,'3'])
            self.assertRaises(TypeError, c, [1,2,(3,4)])
            self.assertRaises(TypeError, c, [1,2,3], shape={3})
            self.assertRaises(TypeError, c, [1,2,3], shape=[3], strides={1})
            self.assertRaises(TypeError, c, [1,2,3], shape=[3], offset=[])
            self.assertRaises(TypeError, c, [1], shape=[1], format={})
            self.assertRaises(TypeError, c, [1], shape=[1], flags={})
            self.assertRaises(TypeError, c, [1], shape=[1], getbuf={})

            # ND_FORTRAN flag is only valid without strides.
            self.assertRaises(TypeError, c, [1], shape=[1], strides=[1],
                              flags=ND_FORTRAN)

            # ND_PIL flag is only valid with ndim > 0.
            self.assertRaises(TypeError, c, [1], shape=[], flags=ND_PIL)

            # Invalid items.
            self.assertRaises(ValueError, c, [], shape=[1])
            self.assertRaises(ValueError, c, ['XXX'], shape=[1], format="L")
            # Invalid combination of items and format.
            self.assertRaises(struct.error, c, [1000], shape=[1], format="B")
            self.assertRaises(ValueError, c, [1,(2,3)], shape=[2], format="B")
            self.assertRaises(ValueError, c, [1,2,3], shape=[3], format="QL")

            # Invalid ndim.
            n = ND_MAX_NDIM+1
            self.assertRaises(ValueError, c, [1]*n, shape=[1]*n)

            # Invalid shape.
            self.assertRaises(ValueError, c, [1], shape=[-1])
            self.assertRaises(ValueError, c, [1,2,3], shape=['3'])
            self.assertRaises(OverflowError, c, [1], shape=[2**128])
            # prod(shape) * itemsize != len(items)
            self.assertRaises(ValueError, c, [1,2,3,4,5], shape=[2,2], offset=3)

            # Invalid strides.
            self.assertRaises(ValueError, c, [1,2,3], shape=[3], strides=['1'])
            self.assertRaises(OverflowError, c, [1], shape=[1],
                              strides=[2**128])

            # Invalid combination of strides and shape.
            self.assertRaises(ValueError, c, [1,2], shape=[2,1], strides=[1])
            # Invalid combination of strides and format.
            self.assertRaises(ValueError, c, [1,2,3,4], shape=[2], strides=[3],
                              format="L")

            # Invalid offset.
            self.assertRaises(ValueError, c, [1,2,3], shape=[3], offset=4)
            self.assertRaises(ValueError, c, [1,2,3], shape=[1], offset=3,
                              format="L")

            # Invalid format.
            self.assertRaises(ValueError, c, [1,2,3], shape=[3], format="")
            self.assertRaises(struct.error, c, [(1,2,3)], shape=[1],
                              format="@#$")

            # Striding out of the memory bounds.
            items = [1,2,3,4,5,6,7,8,9,10]
            self.assertRaises(ValueError, c, items, shape=[2,3],
                              strides=[-3, -2], offset=5)

            # Constructing consumer: format argument invalid.
            self.assertRaises(TypeError, c, bytearray(), format="Q")

            # Constructing original base object: getbuf argument invalid.
            self.assertRaises(TypeError, c, [1], shape=[1], getbuf=PyBUF_FULL)

            # Shape argument is mandatory fuer original base objects.
            self.assertRaises(TypeError, c, [1])


        # PyBUF_WRITABLE request to read-only provider.
        self.assertRaises(BufferError, ndarray, b'123', getbuf=PyBUF_WRITABLE)

        # ND_VAREXPORT can only be specified during construction.
        nd = ndarray([9], [1], flags=ND_VAREXPORT)
        self.assertRaises(ValueError, nd.push, [1], [1], flags=ND_VAREXPORT)

        # Invalid operation fuer consumers: push/pop
        nd = ndarray(b'123')
        self.assertRaises(BufferError, nd.push, [1], [1])
        self.assertRaises(BufferError, nd.pop)

        # ND_VAREXPORT not set: push/pop fail with exported buffers
        nd = ndarray([9], [1])
        nd.push([1], [1])
        m = memoryview(nd)
        self.assertRaises(BufferError, nd.push, [1], [1])
        self.assertRaises(BufferError, nd.pop)
        m.release()
        nd.pop()

        # Single remaining buffer: pop fails
        self.assertRaises(BufferError, nd.pop)
        del nd

        # get_pointer()
        self.assertRaises(TypeError, get_pointer, {}, [1,2,3])
        self.assertRaises(TypeError, get_pointer, b'123', {})

        nd = ndarray(list(range(100)), shape=[1]*100)
        self.assertRaises(ValueError, get_pointer, nd, [5])

        nd = ndarray(list(range(12)), shape=[3,4])
        self.assertRaises(ValueError, get_pointer, nd, [2,3,4])
        self.assertRaises(ValueError, get_pointer, nd, [3,3])
        self.assertRaises(ValueError, get_pointer, nd, [-3,3])
        self.assertRaises(OverflowError, get_pointer, nd, [1<<64,3])

        # tolist() needs format
        ex = ndarray([1,2,3], shape=[3], format='L')
        nd = ndarray(ex, getbuf=PyBUF_SIMPLE)
        self.assertRaises(ValueError, nd.tolist)

        # memoryview_from_buffer()
        ex1 = ndarray([1,2,3], shape=[3], format='L')
        ex2 = ndarray(ex1)
        nd = ndarray(ex2)
        self.assertRaises(TypeError, nd.memoryview_from_buffer)

        nd = ndarray([(1,)*200], shape=[1], format='L'*200)
        self.assertRaises(TypeError, nd.memoryview_from_buffer)

        n = ND_MAX_NDIM
        nd = ndarray(list(range(n)), shape=[1]*n)
        self.assertRaises(ValueError, nd.memoryview_from_buffer)

        # get_contiguous()
        nd = ndarray([1], shape=[1])
        self.assertRaises(TypeError, get_contiguous, 1, 2, 3, 4, 5)
        self.assertRaises(TypeError, get_contiguous, nd, "xyz", 'C')
        self.assertRaises(OverflowError, get_contiguous, nd, 2**64, 'C')
        self.assertRaises(TypeError, get_contiguous, nd, PyBUF_READ, 961)
        self.assertRaises(UnicodeEncodeError, get_contiguous, nd, PyBUF_READ,
                          '\u2007')
        self.assertRaises(ValueError, get_contiguous, nd, PyBUF_READ, 'Z')
        self.assertRaises(ValueError, get_contiguous, nd, 255, 'A')

        # cmp_contig()
        nd = ndarray([1], shape=[1])
        self.assertRaises(TypeError, cmp_contig, 1, 2, 3, 4, 5)
        self.assertRaises(TypeError, cmp_contig, {}, nd)
        self.assertRaises(TypeError, cmp_contig, nd, {})

        # is_contiguous()
        nd = ndarray([1], shape=[1])
        self.assertRaises(TypeError, is_contiguous, 1, 2, 3, 4, 5)
        self.assertRaises(TypeError, is_contiguous, {}, 'A')
        self.assertRaises(TypeError, is_contiguous, nd, 201)

    def test_ndarray_linked_list(self):
        fuer perm in permutations(range(5)):
            m = [0]*5
            nd = ndarray([1,2,3], shape=[3], flags=ND_VAREXPORT)
            m[0] = memoryview(nd)

            fuer i in range(1, 5):
                nd.push([1,2,3], shape=[3])
                m[i] = memoryview(nd)

            fuer i in range(5):
                m[perm[i]].release()

            self.assertRaises(BufferError, nd.pop)
            del nd

    def test_ndarray_format_scalar(self):
        # ndim = 0: scalar
        fuer fmt, scalar, _ in iter_format(0):
            itemsize = struct.calcsize(fmt)
            nd = ndarray(scalar, shape=(), format=fmt)
            self.verify(nd, obj=Nichts,
                        itemsize=itemsize, fmt=fmt, readonly=Wahr,
                        ndim=0, shape=(), strides=(),
                        lst=scalar)

    def test_ndarray_format_shape(self):
        # ndim = 1, shape = [n]
        nitems =  randrange(1, 10)
        fuer fmt, items, _ in iter_format(nitems):
            itemsize = struct.calcsize(fmt)
            fuer flags in (0, ND_PIL):
                nd = ndarray(items, shape=[nitems], format=fmt, flags=flags)
                self.verify(nd, obj=Nichts,
                            itemsize=itemsize, fmt=fmt, readonly=Wahr,
                            ndim=1, shape=(nitems,), strides=(itemsize,),
                            lst=items)

    def test_ndarray_format_strides(self):
        # ndim = 1, strides
        nitems = randrange(1, 30)
        fuer fmt, items, _ in iter_format(nitems):
            itemsize = struct.calcsize(fmt)
            fuer step in range(-5, 5):
                wenn step == 0:
                    continue

                shape = [len(items[::step])]
                strides = [step*itemsize]
                offset = itemsize*(nitems-1) wenn step < 0 sonst 0

                fuer flags in (0, ND_PIL):
                    nd = ndarray(items, shape=shape, strides=strides,
                                 format=fmt, offset=offset, flags=flags)
                    self.verify(nd, obj=Nichts,
                                itemsize=itemsize, fmt=fmt, readonly=Wahr,
                                ndim=1, shape=shape, strides=strides,
                                lst=items[::step])

    def test_ndarray_fortran(self):
        items = [1,2,3,4,5,6,7,8,9,10,11,12]
        ex = ndarray(items, shape=(3, 4), strides=(1, 3))
        nd = ndarray(ex, getbuf=PyBUF_F_CONTIGUOUS|PyBUF_FORMAT)
        self.assertEqual(nd.tolist(), farray(items, (3, 4)))

    def test_ndarray_multidim(self):
        fuer ndim in range(5):
            shape_t = [randrange(2, 10) fuer _ in range(ndim)]
            nitems = prod(shape_t)
            fuer shape in permutations(shape_t):

                fmt, items, _ = randitems(nitems)
                itemsize = struct.calcsize(fmt)

                fuer flags in (0, ND_PIL):
                    wenn ndim == 0 and flags == ND_PIL:
                        continue

                    # C array
                    nd = ndarray(items, shape=shape, format=fmt, flags=flags)

                    strides = strides_from_shape(ndim, shape, itemsize, 'C')
                    lst = carray(items, shape)
                    self.verify(nd, obj=Nichts,
                                itemsize=itemsize, fmt=fmt, readonly=Wahr,
                                ndim=ndim, shape=shape, strides=strides,
                                lst=lst)

                    wenn is_memoryview_format(fmt):
                        # memoryview: reconstruct strides
                        ex = ndarray(items, shape=shape, format=fmt)
                        nd = ndarray(ex, getbuf=PyBUF_CONTIG_RO|PyBUF_FORMAT)
                        self.assertWahr(nd.strides == ())
                        mv = nd.memoryview_from_buffer()
                        self.verify(mv, obj=Nichts,
                                    itemsize=itemsize, fmt=fmt, readonly=Wahr,
                                    ndim=ndim, shape=shape, strides=strides,
                                    lst=lst)

                    # Fortran array
                    nd = ndarray(items, shape=shape, format=fmt,
                                 flags=flags|ND_FORTRAN)

                    strides = strides_from_shape(ndim, shape, itemsize, 'F')
                    lst = farray(items, shape)
                    self.verify(nd, obj=Nichts,
                                itemsize=itemsize, fmt=fmt, readonly=Wahr,
                                ndim=ndim, shape=shape, strides=strides,
                                lst=lst)

    def test_ndarray_index_invalid(self):
        # not writable
        nd = ndarray([1], shape=[1])
        self.assertRaises(TypeError, nd.__setitem__, 1, 8)
        mv = memoryview(nd)
        self.assertEqual(mv, nd)
        self.assertRaises(TypeError, mv.__setitem__, 1, 8)

        # cannot be deleted
        nd = ndarray([1], shape=[1], flags=ND_WRITABLE)
        self.assertRaises(TypeError, nd.__delitem__, 1)
        mv = memoryview(nd)
        self.assertEqual(mv, nd)
        self.assertRaises(TypeError, mv.__delitem__, 1)

        # overflow
        nd = ndarray([1], shape=[1], flags=ND_WRITABLE)
        self.assertRaises(OverflowError, nd.__getitem__, 1<<64)
        self.assertRaises(OverflowError, nd.__setitem__, 1<<64, 8)
        mv = memoryview(nd)
        self.assertEqual(mv, nd)
        self.assertRaises(IndexError, mv.__getitem__, 1<<64)
        self.assertRaises(IndexError, mv.__setitem__, 1<<64, 8)

        # format
        items = [1,2,3,4,5,6,7,8]
        nd = ndarray(items, shape=[len(items)], format="B", flags=ND_WRITABLE)
        self.assertRaises(struct.error, nd.__setitem__, 2, 300)
        self.assertRaises(ValueError, nd.__setitem__, 1, (100, 200))
        mv = memoryview(nd)
        self.assertEqual(mv, nd)
        self.assertRaises(ValueError, mv.__setitem__, 2, 300)
        self.assertRaises(TypeError, mv.__setitem__, 1, (100, 200))

        items = [(1,2), (3,4), (5,6)]
        nd = ndarray(items, shape=[len(items)], format="LQ", flags=ND_WRITABLE)
        self.assertRaises(ValueError, nd.__setitem__, 2, 300)
        self.assertRaises(struct.error, nd.__setitem__, 1, (b'\x001', 200))

    def test_ndarray_index_scalar(self):
        # scalar
        nd = ndarray(1, shape=(), flags=ND_WRITABLE)
        mv = memoryview(nd)
        self.assertEqual(mv, nd)

        x = nd[()];  self.assertEqual(x, 1)
        x = nd[...]; self.assertEqual(x.tolist(), nd.tolist())

        x = mv[()];  self.assertEqual(x, 1)
        x = mv[...]; self.assertEqual(x.tolist(), nd.tolist())

        self.assertRaises(TypeError, nd.__getitem__, 0)
        self.assertRaises(TypeError, mv.__getitem__, 0)
        self.assertRaises(TypeError, nd.__setitem__, 0, 8)
        self.assertRaises(TypeError, mv.__setitem__, 0, 8)

        self.assertEqual(nd.tolist(), 1)
        self.assertEqual(mv.tolist(), 1)

        nd[()] = 9; self.assertEqual(nd.tolist(), 9)
        mv[()] = 9; self.assertEqual(mv.tolist(), 9)

        nd[...] = 5; self.assertEqual(nd.tolist(), 5)
        mv[...] = 5; self.assertEqual(mv.tolist(), 5)

    def test_ndarray_index_null_strides(self):
        ex = ndarray(list(range(2*4)), shape=[2, 4], flags=ND_WRITABLE)
        nd = ndarray(ex, getbuf=PyBUF_CONTIG)

        # Sub-views are only possible fuer full exporters.
        self.assertRaises(BufferError, nd.__getitem__, 1)
        # Same fuer slices.
        self.assertRaises(BufferError, nd.__getitem__, slice(3,5,1))

    def test_ndarray_index_getitem_single(self):
        # getitem
        fuer fmt, items, _ in iter_format(5):
            nd = ndarray(items, shape=[5], format=fmt)
            fuer i in range(-5, 5):
                self.assertEqual(nd[i], items[i])

            self.assertRaises(IndexError, nd.__getitem__, -6)
            self.assertRaises(IndexError, nd.__getitem__, 5)

            wenn is_memoryview_format(fmt):
                mv = memoryview(nd)
                self.assertEqual(mv, nd)
                fuer i in range(-5, 5):
                    self.assertEqual(mv[i], items[i])

                self.assertRaises(IndexError, mv.__getitem__, -6)
                self.assertRaises(IndexError, mv.__getitem__, 5)

        # getitem with null strides
        fuer fmt, items, _ in iter_format(5):
            ex = ndarray(items, shape=[5], flags=ND_WRITABLE, format=fmt)
            nd = ndarray(ex, getbuf=PyBUF_CONTIG|PyBUF_FORMAT)

            fuer i in range(-5, 5):
                self.assertEqual(nd[i], items[i])

            wenn is_memoryview_format(fmt):
                mv = nd.memoryview_from_buffer()
                self.assertIs(mv.__eq__(nd), NotImplemented)
                fuer i in range(-5, 5):
                    self.assertEqual(mv[i], items[i])

        # getitem with null format
        items = [1,2,3,4,5]
        ex = ndarray(items, shape=[5])
        nd = ndarray(ex, getbuf=PyBUF_CONTIG_RO)
        fuer i in range(-5, 5):
            self.assertEqual(nd[i], items[i])

        # getitem with null shape/strides/format
        items = [1,2,3,4,5]
        ex = ndarray(items, shape=[5])
        nd = ndarray(ex, getbuf=PyBUF_SIMPLE)

        fuer i in range(-5, 5):
            self.assertEqual(nd[i], items[i])

    def test_ndarray_index_setitem_single(self):
        # assign single value
        fuer fmt, items, single_item in iter_format(5):
            nd = ndarray(items, shape=[5], format=fmt, flags=ND_WRITABLE)
            fuer i in range(5):
                items[i] = single_item
                nd[i] = single_item
            self.assertEqual(nd.tolist(), items)

            self.assertRaises(IndexError, nd.__setitem__, -6, single_item)
            self.assertRaises(IndexError, nd.__setitem__, 5, single_item)

            wenn not is_memoryview_format(fmt):
                continue

            nd = ndarray(items, shape=[5], format=fmt, flags=ND_WRITABLE)
            mv = memoryview(nd)
            self.assertEqual(mv, nd)
            fuer i in range(5):
                items[i] = single_item
                mv[i] = single_item
            self.assertEqual(mv.tolist(), items)

            self.assertRaises(IndexError, mv.__setitem__, -6, single_item)
            self.assertRaises(IndexError, mv.__setitem__, 5, single_item)


        # assign single value: lobject = robject
        fuer fmt, items, single_item in iter_format(5):
            nd = ndarray(items, shape=[5], format=fmt, flags=ND_WRITABLE)
            fuer i in range(-5, 4):
                items[i] = items[i+1]
                nd[i] = nd[i+1]
            self.assertEqual(nd.tolist(), items)

            wenn not is_memoryview_format(fmt):
                continue

            nd = ndarray(items, shape=[5], format=fmt, flags=ND_WRITABLE)
            mv = memoryview(nd)
            self.assertEqual(mv, nd)
            fuer i in range(-5, 4):
                items[i] = items[i+1]
                mv[i] = mv[i+1]
            self.assertEqual(mv.tolist(), items)

    def test_ndarray_index_getitem_multidim(self):
        shape_t = (2, 3, 5)
        nitems = prod(shape_t)
        fuer shape in permutations(shape_t):

            fmt, items, _ = randitems(nitems)

            fuer flags in (0, ND_PIL):
                # C array
                nd = ndarray(items, shape=shape, format=fmt, flags=flags)
                lst = carray(items, shape)

                fuer i in range(-shape[0], shape[0]):
                    self.assertEqual(lst[i], nd[i].tolist())
                    fuer j in range(-shape[1], shape[1]):
                        self.assertEqual(lst[i][j], nd[i][j].tolist())
                        fuer k in range(-shape[2], shape[2]):
                            self.assertEqual(lst[i][j][k], nd[i][j][k])

                # Fortran array
                nd = ndarray(items, shape=shape, format=fmt,
                             flags=flags|ND_FORTRAN)
                lst = farray(items, shape)

                fuer i in range(-shape[0], shape[0]):
                    self.assertEqual(lst[i], nd[i].tolist())
                    fuer j in range(-shape[1], shape[1]):
                        self.assertEqual(lst[i][j], nd[i][j].tolist())
                        fuer k in range(shape[2], shape[2]):
                            self.assertEqual(lst[i][j][k], nd[i][j][k])

    def test_ndarray_sequence(self):
        nd = ndarray(1, shape=())
        self.assertRaises(TypeError, eval, "1 in nd", locals())
        mv = memoryview(nd)
        self.assertEqual(mv, nd)
        self.assertRaises(TypeError, eval, "1 in mv", locals())

        fuer fmt, items, _ in iter_format(5):
            nd = ndarray(items, shape=[5], format=fmt)
            fuer i, v in enumerate(nd):
                self.assertEqual(v, items[i])
                self.assertWahr(v in nd)

            wenn is_memoryview_format(fmt):
                mv = memoryview(nd)
                fuer i, v in enumerate(mv):
                    self.assertEqual(v, items[i])
                    self.assertWahr(v in mv)

    def test_ndarray_slice_invalid(self):
        items = [1,2,3,4,5,6,7,8]

        # rvalue is not an exporter
        xl = ndarray(items, shape=[8], flags=ND_WRITABLE)
        ml = memoryview(xl)
        self.assertRaises(TypeError, xl.__setitem__, slice(0,8,1), items)
        self.assertRaises(TypeError, ml.__setitem__, slice(0,8,1), items)

        # rvalue is not a full exporter
        xl = ndarray(items, shape=[8], flags=ND_WRITABLE)
        ex = ndarray(items, shape=[8], flags=ND_WRITABLE)
        xr = ndarray(ex, getbuf=PyBUF_ND)
        self.assertRaises(BufferError, xl.__setitem__, slice(0,8,1), xr)

        # zero step
        nd = ndarray(items, shape=[8], format="L", flags=ND_WRITABLE)
        mv = memoryview(nd)
        self.assertRaises(ValueError, nd.__getitem__, slice(0,1,0))
        self.assertRaises(ValueError, mv.__getitem__, slice(0,1,0))

        nd = ndarray(items, shape=[2,4], format="L", flags=ND_WRITABLE)
        mv = memoryview(nd)

        self.assertRaises(ValueError, nd.__getitem__,
                          (slice(0,1,1), slice(0,1,0)))
        self.assertRaises(ValueError, nd.__getitem__,
                          (slice(0,1,0), slice(0,1,1)))
        self.assertRaises(TypeError, nd.__getitem__, "@%$")
        self.assertRaises(TypeError, nd.__getitem__, ("@%$", slice(0,1,1)))
        self.assertRaises(TypeError, nd.__getitem__, (slice(0,1,1), {}))

        # memoryview: not implemented
        self.assertRaises(NotImplementedError, mv.__getitem__,
                          (slice(0,1,1), slice(0,1,0)))
        self.assertRaises(TypeError, mv.__getitem__, "@%$")

        # differing format
        xl = ndarray(items, shape=[8], format="B", flags=ND_WRITABLE)
        xr = ndarray(items, shape=[8], format="b")
        ml = memoryview(xl)
        mr = memoryview(xr)
        self.assertRaises(ValueError, xl.__setitem__, slice(0,1,1), xr[7:8])
        self.assertEqual(xl.tolist(), items)
        self.assertRaises(ValueError, ml.__setitem__, slice(0,1,1), mr[7:8])
        self.assertEqual(ml.tolist(), items)

        # differing itemsize
        xl = ndarray(items, shape=[8], format="B", flags=ND_WRITABLE)
        yr = ndarray(items, shape=[8], format="L")
        ml = memoryview(xl)
        mr = memoryview(xr)
        self.assertRaises(ValueError, xl.__setitem__, slice(0,1,1), xr[7:8])
        self.assertEqual(xl.tolist(), items)
        self.assertRaises(ValueError, ml.__setitem__, slice(0,1,1), mr[7:8])
        self.assertEqual(ml.tolist(), items)

        # differing ndim
        xl = ndarray(items, shape=[2, 4], format="b", flags=ND_WRITABLE)
        xr = ndarray(items, shape=[8], format="b")
        ml = memoryview(xl)
        mr = memoryview(xr)
        self.assertRaises(ValueError, xl.__setitem__, slice(0,1,1), xr[7:8])
        self.assertEqual(xl.tolist(), [[1,2,3,4], [5,6,7,8]])
        self.assertRaises(NotImplementedError, ml.__setitem__, slice(0,1,1),
                          mr[7:8])

        # differing shape
        xl = ndarray(items, shape=[8], format="b", flags=ND_WRITABLE)
        xr = ndarray(items, shape=[8], format="b")
        ml = memoryview(xl)
        mr = memoryview(xr)
        self.assertRaises(ValueError, xl.__setitem__, slice(0,2,1), xr[7:8])
        self.assertEqual(xl.tolist(), items)
        self.assertRaises(ValueError, ml.__setitem__, slice(0,2,1), mr[7:8])
        self.assertEqual(ml.tolist(), items)

        # _testbuffer.c module functions
        self.assertRaises(TypeError, slice_indices, slice(0,1,2), {})
        self.assertRaises(TypeError, slice_indices, "###########", 1)
        self.assertRaises(ValueError, slice_indices, slice(0,1,0), 4)

        x = ndarray(items, shape=[8], format="b", flags=ND_PIL)
        self.assertRaises(TypeError, x.add_suboffsets)

        ex = ndarray(items, shape=[8], format="B")
        x = ndarray(ex, getbuf=PyBUF_SIMPLE)
        self.assertRaises(TypeError, x.add_suboffsets)

    def test_ndarray_slice_zero_shape(self):
        items = [1,2,3,4,5,6,7,8,9,10,11,12]

        x = ndarray(items, shape=[12], format="L", flags=ND_WRITABLE)
        y = ndarray(items, shape=[12], format="L")
        x[4:4] = y[9:9]
        self.assertEqual(x.tolist(), items)

        ml = memoryview(x)
        mr = memoryview(y)
        self.assertEqual(ml, x)
        self.assertEqual(ml, y)
        ml[4:4] = mr[9:9]
        self.assertEqual(ml.tolist(), items)

        x = ndarray(items, shape=[3, 4], format="L", flags=ND_WRITABLE)
        y = ndarray(items, shape=[4, 3], format="L")
        x[1:2, 2:2] = y[1:2, 3:3]
        self.assertEqual(x.tolist(), carray(items, [3, 4]))

    def test_ndarray_slice_multidim(self):
        shape_t = (2, 3, 5)
        ndim = len(shape_t)
        nitems = prod(shape_t)
        fuer shape in permutations(shape_t):

            fmt, items, _ = randitems(nitems)
            itemsize = struct.calcsize(fmt)

            fuer flags in (0, ND_PIL):
                nd = ndarray(items, shape=shape, format=fmt, flags=flags)
                lst = carray(items, shape)

                fuer slices in rslices_ndim(ndim, shape):

                    listerr = Nichts
                    try:
                        sliced = multislice(lst, slices)
                    except Exception as e:
                        listerr = e.__class__

                    nderr = Nichts
                    try:
                        ndsliced = nd[slices]
                    except Exception as e:
                        nderr = e.__class__

                    wenn nderr or listerr:
                        self.assertIs(nderr, listerr)
                    sonst:
                        self.assertEqual(ndsliced.tolist(), sliced)

    def test_ndarray_slice_redundant_suboffsets(self):
        shape_t = (2, 3, 5, 2)
        ndim = len(shape_t)
        nitems = prod(shape_t)
        fuer shape in permutations(shape_t):

            fmt, items, _ = randitems(nitems)
            itemsize = struct.calcsize(fmt)

            nd = ndarray(items, shape=shape, format=fmt)
            nd.add_suboffsets()
            ex = ndarray(items, shape=shape, format=fmt)
            ex.add_suboffsets()
            mv = memoryview(ex)
            lst = carray(items, shape)

            fuer slices in rslices_ndim(ndim, shape):

                listerr = Nichts
                try:
                    sliced = multislice(lst, slices)
                except Exception as e:
                    listerr = e.__class__

                nderr = Nichts
                try:
                    ndsliced = nd[slices]
                except Exception as e:
                    nderr = e.__class__

                wenn nderr or listerr:
                    self.assertIs(nderr, listerr)
                sonst:
                    self.assertEqual(ndsliced.tolist(), sliced)

    def test_ndarray_slice_assign_single(self):
        fuer fmt, items, _ in iter_format(5):
            fuer lslice in genslices(5):
                fuer rslice in genslices(5):
                    fuer flags in (0, ND_PIL):

                        f = flags|ND_WRITABLE
                        nd = ndarray(items, shape=[5], format=fmt, flags=f)
                        ex = ndarray(items, shape=[5], format=fmt, flags=f)
                        mv = memoryview(ex)

                        lsterr = Nichts
                        diff_structure = Nichts
                        lst = items[:]
                        try:
                            lval = lst[lslice]
                            rval = lst[rslice]
                            lst[lslice] = lst[rslice]
                            diff_structure = len(lval) != len(rval)
                        except Exception as e:
                            lsterr = e.__class__

                        nderr = Nichts
                        try:
                            nd[lslice] = nd[rslice]
                        except Exception as e:
                            nderr = e.__class__

                        wenn diff_structure: # ndarray cannot change shape
                            self.assertIs(nderr, ValueError)
                        sonst:
                            self.assertEqual(nd.tolist(), lst)
                            self.assertIs(nderr, lsterr)

                        wenn not is_memoryview_format(fmt):
                            continue

                        mverr = Nichts
                        try:
                            mv[lslice] = mv[rslice]
                        except Exception as e:
                            mverr = e.__class__

                        wenn diff_structure: # memoryview cannot change shape
                            self.assertIs(mverr, ValueError)
                        sonst:
                            self.assertEqual(mv.tolist(), lst)
                            self.assertEqual(mv, nd)
                            self.assertIs(mverr, lsterr)
                            self.verify(mv, obj=ex,
                              itemsize=nd.itemsize, fmt=fmt, readonly=Falsch,
                              ndim=nd.ndim, shape=nd.shape, strides=nd.strides,
                              lst=nd.tolist())

    def test_ndarray_slice_assign_multidim(self):
        shape_t = (2, 3, 5)
        ndim = len(shape_t)
        nitems = prod(shape_t)
        fuer shape in permutations(shape_t):

            fmt, items, _ = randitems(nitems)

            fuer flags in (0, ND_PIL):
                fuer _ in range(ITERATIONS):
                    lslices, rslices = randslice_from_shape(ndim, shape)

                    nd = ndarray(items, shape=shape, format=fmt,
                                 flags=flags|ND_WRITABLE)
                    lst = carray(items, shape)

                    listerr = Nichts
                    try:
                        result = multislice_assign(lst, lst, lslices, rslices)
                    except Exception as e:
                        listerr = e.__class__

                    nderr = Nichts
                    try:
                        nd[lslices] = nd[rslices]
                    except Exception as e:
                        nderr = e.__class__

                    wenn nderr or listerr:
                        self.assertIs(nderr, listerr)
                    sonst:
                        self.assertEqual(nd.tolist(), result)

    def test_ndarray_random(self):
        # construction of valid arrays
        fuer _ in range(ITERATIONS):
            fuer fmt in fmtdict['@']:
                itemsize = struct.calcsize(fmt)

                t = rand_structure(itemsize, Wahr, maxdim=MAXDIM,
                                   maxshape=MAXSHAPE)
                self.assertWahr(verify_structure(*t))
                items = randitems_from_structure(fmt, t)

                x = ndarray_from_structure(items, fmt, t)
                xlist = x.tolist()

                mv = memoryview(x)
                wenn is_memoryview_format(fmt):
                    mvlist = mv.tolist()
                    self.assertEqual(mvlist, xlist)

                wenn t[2] > 0:
                    # ndim > 0: test against suboffsets representation.
                    y = ndarray_from_structure(items, fmt, t, flags=ND_PIL)
                    ylist = y.tolist()
                    self.assertEqual(xlist, ylist)

                    mv = memoryview(y)
                    wenn is_memoryview_format(fmt):
                        self.assertEqual(mv, y)
                        mvlist = mv.tolist()
                        self.assertEqual(mvlist, ylist)

                wenn numpy_array:
                    shape = t[3]
                    wenn 0 in shape:
                        continue # https://github.com/numpy/numpy/issues/2503
                    z = numpy_array_from_structure(items, fmt, t)
                    self.verify(x, obj=Nichts,
                                itemsize=z.itemsize, fmt=fmt, readonly=Falsch,
                                ndim=z.ndim, shape=z.shape, strides=z.strides,
                                lst=z.tolist())

    def test_ndarray_random_invalid(self):
        # exceptions during construction of invalid arrays
        fuer _ in range(ITERATIONS):
            fuer fmt in fmtdict['@']:
                itemsize = struct.calcsize(fmt)

                t = rand_structure(itemsize, Falsch, maxdim=MAXDIM,
                                   maxshape=MAXSHAPE)
                self.assertFalsch(verify_structure(*t))
                items = randitems_from_structure(fmt, t)

                nderr = Falsch
                try:
                    x = ndarray_from_structure(items, fmt, t)
                except Exception as e:
                    nderr = e.__class__
                self.assertWahr(nderr)

                wenn numpy_array:
                    numpy_err = Falsch
                    try:
                        y = numpy_array_from_structure(items, fmt, t)
                    except Exception as e:
                        numpy_err = e.__class__

                    wenn 0: # https://github.com/numpy/numpy/issues/2503
                        self.assertWahr(numpy_err)

    def test_ndarray_random_slice_assign(self):
        # valid slice assignments
        fuer _ in range(ITERATIONS):
            fuer fmt in fmtdict['@']:
                itemsize = struct.calcsize(fmt)

                lshape, rshape, lslices, rslices = \
                    rand_aligned_slices(maxdim=MAXDIM, maxshape=MAXSHAPE)
                tl = rand_structure(itemsize, Wahr, shape=lshape)
                tr = rand_structure(itemsize, Wahr, shape=rshape)
                self.assertWahr(verify_structure(*tl))
                self.assertWahr(verify_structure(*tr))
                litems = randitems_from_structure(fmt, tl)
                ritems = randitems_from_structure(fmt, tr)

                xl = ndarray_from_structure(litems, fmt, tl)
                xr = ndarray_from_structure(ritems, fmt, tr)
                xl[lslices] = xr[rslices]
                xllist = xl.tolist()
                xrlist = xr.tolist()

                ml = memoryview(xl)
                mr = memoryview(xr)
                self.assertEqual(ml.tolist(), xllist)
                self.assertEqual(mr.tolist(), xrlist)

                wenn tl[2] > 0 and tr[2] > 0:
                    # ndim > 0: test against suboffsets representation.
                    yl = ndarray_from_structure(litems, fmt, tl, flags=ND_PIL)
                    yr = ndarray_from_structure(ritems, fmt, tr, flags=ND_PIL)
                    yl[lslices] = yr[rslices]
                    yllist = yl.tolist()
                    yrlist = yr.tolist()
                    self.assertEqual(xllist, yllist)
                    self.assertEqual(xrlist, yrlist)

                    ml = memoryview(yl)
                    mr = memoryview(yr)
                    self.assertEqual(ml.tolist(), yllist)
                    self.assertEqual(mr.tolist(), yrlist)

                wenn numpy_array:
                    wenn 0 in lshape or 0 in rshape:
                        continue # https://github.com/numpy/numpy/issues/2503

                    zl = numpy_array_from_structure(litems, fmt, tl)
                    zr = numpy_array_from_structure(ritems, fmt, tr)
                    zl[lslices] = zr[rslices]

                    wenn not is_overlapping(tl) and not is_overlapping(tr):
                        # Slice assignment of overlapping structures
                        # is undefined in NumPy.
                        self.verify(xl, obj=Nichts,
                                    itemsize=zl.itemsize, fmt=fmt, readonly=Falsch,
                                    ndim=zl.ndim, shape=zl.shape,
                                    strides=zl.strides, lst=zl.tolist())

                    self.verify(xr, obj=Nichts,
                                itemsize=zr.itemsize, fmt=fmt, readonly=Falsch,
                                ndim=zr.ndim, shape=zr.shape,
                                strides=zr.strides, lst=zr.tolist())

    def test_ndarray_re_export(self):
        items = [1,2,3,4,5,6,7,8,9,10,11,12]

        nd = ndarray(items, shape=[3,4], flags=ND_PIL)
        ex = ndarray(nd)

        self.assertWahr(ex.flags & ND_PIL)
        self.assertIs(ex.obj, nd)
        self.assertEqual(ex.suboffsets, (0, -1))
        self.assertFalsch(ex.c_contiguous)
        self.assertFalsch(ex.f_contiguous)
        self.assertFalsch(ex.contiguous)

    def test_ndarray_zero_shape(self):
        # zeros in shape
        fuer flags in (0, ND_PIL):
            nd = ndarray([1,2,3], shape=[0], flags=flags)
            mv = memoryview(nd)
            self.assertEqual(mv, nd)
            self.assertEqual(nd.tolist(), [])
            self.assertEqual(mv.tolist(), [])

            nd = ndarray([1,2,3], shape=[0,3,3], flags=flags)
            self.assertEqual(nd.tolist(), [])

            nd = ndarray([1,2,3], shape=[3,0,3], flags=flags)
            self.assertEqual(nd.tolist(), [[], [], []])

            nd = ndarray([1,2,3], shape=[3,3,0], flags=flags)
            self.assertEqual(nd.tolist(),
                             [[[], [], []], [[], [], []], [[], [], []]])

    def test_ndarray_zero_strides(self):
        # zero strides
        fuer flags in (0, ND_PIL):
            nd = ndarray([1], shape=[5], strides=[0], flags=flags)
            mv = memoryview(nd)
            self.assertEqual(mv, nd)
            self.assertEqual(nd.tolist(), [1, 1, 1, 1, 1])
            self.assertEqual(mv.tolist(), [1, 1, 1, 1, 1])

    def test_ndarray_offset(self):
        nd = ndarray(list(range(20)), shape=[3], offset=7)
        self.assertEqual(nd.offset, 7)
        self.assertEqual(nd.tolist(), [7,8,9])

    def test_ndarray_memoryview_from_buffer(self):
        fuer flags in (0, ND_PIL):
            nd = ndarray(list(range(3)), shape=[3], flags=flags)
            m = nd.memoryview_from_buffer()
            self.assertEqual(m, nd)

    def test_ndarray_get_pointer(self):
        fuer flags in (0, ND_PIL):
            nd = ndarray(list(range(3)), shape=[3], flags=flags)
            fuer i in range(3):
                self.assertEqual(nd[i], get_pointer(nd, [i]))

    def test_ndarray_tolist_null_strides(self):
        ex = ndarray(list(range(20)), shape=[2,2,5])

        nd = ndarray(ex, getbuf=PyBUF_ND|PyBUF_FORMAT)
        self.assertEqual(nd.tolist(), ex.tolist())

        m = memoryview(ex)
        self.assertEqual(m.tolist(), ex.tolist())

    def test_ndarray_cmp_contig(self):

        self.assertFalsch(cmp_contig(b"123", b"456"))

        x = ndarray(list(range(12)), shape=[3,4])
        y = ndarray(list(range(12)), shape=[4,3])
        self.assertFalsch(cmp_contig(x, y))

        x = ndarray([1], shape=[1], format="B")
        self.assertWahr(cmp_contig(x, b'\x01'))
        self.assertWahr(cmp_contig(b'\x01', x))

    def test_ndarray_hash(self):

        a = array.array('L', [1,2,3])
        nd = ndarray(a)
        self.assertRaises(ValueError, hash, nd)

        # one-dimensional
        b = bytes(list(range(12)))

        nd = ndarray(list(range(12)), shape=[12])
        self.assertEqual(hash(nd), hash(b))

        # C-contiguous
        nd = ndarray(list(range(12)), shape=[3,4])
        self.assertEqual(hash(nd), hash(b))

        nd = ndarray(list(range(12)), shape=[3,2,2])
        self.assertEqual(hash(nd), hash(b))

        # Fortran contiguous
        b = bytes(transpose(list(range(12)), shape=[4,3]))
        nd = ndarray(list(range(12)), shape=[3,4], flags=ND_FORTRAN)
        self.assertEqual(hash(nd), hash(b))

        b = bytes(transpose(list(range(12)), shape=[2,3,2]))
        nd = ndarray(list(range(12)), shape=[2,3,2], flags=ND_FORTRAN)
        self.assertEqual(hash(nd), hash(b))

        # suboffsets
        b = bytes(list(range(12)))
        nd = ndarray(list(range(12)), shape=[2,2,3], flags=ND_PIL)
        self.assertEqual(hash(nd), hash(b))

        # non-byte formats
        nd = ndarray(list(range(12)), shape=[2,2,3], format='L')
        self.assertEqual(hash(nd), hash(nd.tobytes()))

    def test_py_buffer_to_contiguous(self):

        # The requests are used in _testbuffer.c:py_buffer_to_contiguous
        # to generate buffers without full information fuer testing.
        requests = (
            # distinct flags
            PyBUF_INDIRECT, PyBUF_STRIDES, PyBUF_ND, PyBUF_SIMPLE,
            # compound requests
            PyBUF_FULL, PyBUF_FULL_RO,
            PyBUF_RECORDS, PyBUF_RECORDS_RO,
            PyBUF_STRIDED, PyBUF_STRIDED_RO,
            PyBUF_CONTIG, PyBUF_CONTIG_RO,
        )

        # no buffer interface
        self.assertRaises(TypeError, py_buffer_to_contiguous, {}, 'F',
                          PyBUF_FULL_RO)

        # scalar, read-only request
        nd = ndarray(9, shape=(), format="L", flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            fuer request in requests:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, nd.tobytes())

        # zeros in shape
        nd = ndarray([1], shape=[0], format="L", flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            fuer request in requests:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, b'')

        nd = ndarray(list(range(8)), shape=[2, 0, 7], format="L",
                     flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            fuer request in requests:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, b'')

        ### One-dimensional arrays are trivial, since Fortran and C order
        ### are the same.

        # one-dimensional
        fuer f in [0, ND_FORTRAN]:
            nd = ndarray([1], shape=[1], format="h", flags=f|ND_WRITABLE)
            ndbytes = nd.tobytes()
            fuer order in ['C', 'F', 'A']:
                fuer request in requests:
                    b = py_buffer_to_contiguous(nd, order, request)
                    self.assertEqual(b, ndbytes)

            nd = ndarray([1, 2, 3], shape=[3], format="b", flags=f|ND_WRITABLE)
            ndbytes = nd.tobytes()
            fuer order in ['C', 'F', 'A']:
                fuer request in requests:
                    b = py_buffer_to_contiguous(nd, order, request)
                    self.assertEqual(b, ndbytes)

        # one-dimensional, non-contiguous input
        nd = ndarray([1, 2, 3], shape=[2], strides=[2], flags=ND_WRITABLE)
        ndbytes = nd.tobytes()
        fuer order in ['C', 'F', 'A']:
            fuer request in [PyBUF_STRIDES, PyBUF_FULL]:
                b = py_buffer_to_contiguous(nd, order, request)
                self.assertEqual(b, ndbytes)

        nd = nd[::-1]
        ndbytes = nd.tobytes()
        fuer order in ['C', 'F', 'A']:
            fuer request in requests:
                try:
                    b = py_buffer_to_contiguous(nd, order, request)
                except BufferError:
                    continue
                self.assertEqual(b, ndbytes)

        ###
        ### Multi-dimensional arrays:
        ###
        ### The goal here is to preserve the logical representation of the
        ### input array but change the physical representation wenn necessary.
        ###
        ### _testbuffer example:
        ### ====================
        ###
        ###    C input array:
        ###    --------------
        ###       >>> nd = ndarray(list(range(12)), shape=[3, 4])
        ###       >>> nd.tolist()
        ###       [[0, 1, 2, 3],
        ###        [4, 5, 6, 7],
        ###        [8, 9, 10, 11]]
        ###
        ###    Fortran output:
        ###    ---------------
        ###       >>> py_buffer_to_contiguous(nd, 'F', PyBUF_FULL_RO)
        ###       >>> b'\x00\x04\x08\x01\x05\t\x02\x06\n\x03\x07\x0b'
        ###
        ###    The return value corresponds to this input list for
        ###    _testbuffer's ndarray:
        ###       >>> nd = ndarray([0,4,8,1,5,9,2,6,10,3,7,11], shape=[3,4],
        ###                        flags=ND_FORTRAN)
        ###       >>> nd.tolist()
        ###       [[0, 1, 2, 3],
        ###        [4, 5, 6, 7],
        ###        [8, 9, 10, 11]]
        ###
        ###    The logical array is the same, but the values in memory are now
        ###    in Fortran order.
        ###
        ### NumPy example:
        ### ==============
        ###    _testbuffer's ndarray takes lists to initialize the memory.
        ###    Here's the same sequence in NumPy:
        ###
        ###    C input:
        ###    --------
        ###       >>> nd = ndarray(buffer=bytearray(list(range(12))),
        ###                        shape=[3, 4], dtype='B')
        ###       >>> nd
        ###       array([[ 0,  1,  2,  3],
        ###              [ 4,  5,  6,  7],
        ###              [ 8,  9, 10, 11]], dtype=uint8)
        ###
        ###    Fortran output:
        ###    ---------------
        ###       >>> fortran_buf = nd.tobytes(order='F')
        ###       >>> fortran_buf
        ###       b'\x00\x04\x08\x01\x05\t\x02\x06\n\x03\x07\x0b'
        ###
        ###       >>> nd = ndarray(buffer=fortran_buf, shape=[3, 4],
        ###                        dtype='B', order='F')
        ###
        ###       >>> nd
        ###       array([[ 0,  1,  2,  3],
        ###              [ 4,  5,  6,  7],
        ###              [ 8,  9, 10, 11]], dtype=uint8)
        ###

        # multi-dimensional, contiguous input
        lst = list(range(12))
        fuer f in [0, ND_FORTRAN]:
            nd = ndarray(lst, shape=[3, 4], flags=f|ND_WRITABLE)
            wenn numpy_array:
                na = numpy_array(buffer=bytearray(lst),
                                 shape=[3, 4], dtype='B',
                                 order='C' wenn f == 0 sonst 'F')

            # 'C' request
            wenn f == ND_FORTRAN: # 'F' to 'C'
                x = ndarray(transpose(lst, [4, 3]), shape=[3, 4],
                            flags=ND_WRITABLE)
                expected = x.tobytes()
            sonst:
                expected = nd.tobytes()
            fuer request in requests:
                try:
                    b = py_buffer_to_contiguous(nd, 'C', request)
                except BufferError:
                    continue

                self.assertEqual(b, expected)

                # Check that output can be used as the basis fuer constructing
                # a C array that is logically identical to the input array.
                y = ndarray([v fuer v in b], shape=[3, 4], flags=ND_WRITABLE)
                self.assertEqual(memoryview(y), memoryview(nd))

                wenn numpy_array:
                    self.assertEqual(b, na.tobytes(order='C'))

            # 'F' request
            wenn f == 0: # 'C' to 'F'
                x = ndarray(transpose(lst, [3, 4]), shape=[4, 3],
                            flags=ND_WRITABLE)
            sonst:
                x = ndarray(lst, shape=[3, 4], flags=ND_WRITABLE)
            expected = x.tobytes()
            fuer request in [PyBUF_FULL, PyBUF_FULL_RO, PyBUF_INDIRECT,
                            PyBUF_STRIDES, PyBUF_ND]:
                try:
                    b = py_buffer_to_contiguous(nd, 'F', request)
                except BufferError:
                    continue
                self.assertEqual(b, expected)

                # Check that output can be used as the basis fuer constructing
                # a Fortran array that is logically identical to the input array.
                y = ndarray([v fuer v in b], shape=[3, 4], flags=ND_FORTRAN|ND_WRITABLE)
                self.assertEqual(memoryview(y), memoryview(nd))

                wenn numpy_array:
                    self.assertEqual(b, na.tobytes(order='F'))

            # 'A' request
            wenn f == ND_FORTRAN:
                x = ndarray(lst, shape=[3, 4], flags=ND_WRITABLE)
                expected = x.tobytes()
            sonst:
                expected = nd.tobytes()
            fuer request in [PyBUF_FULL, PyBUF_FULL_RO, PyBUF_INDIRECT,
                            PyBUF_STRIDES, PyBUF_ND]:
                try:
                    b = py_buffer_to_contiguous(nd, 'A', request)
                except BufferError:
                    continue

                self.assertEqual(b, expected)

                # Check that output can be used as the basis fuer constructing
                # an array with order=f that is logically identical to the input
                # array.
                y = ndarray([v fuer v in b], shape=[3, 4], flags=f|ND_WRITABLE)
                self.assertEqual(memoryview(y), memoryview(nd))

                wenn numpy_array:
                    self.assertEqual(b, na.tobytes(order='A'))

        # multi-dimensional, non-contiguous input
        nd = ndarray(list(range(12)), shape=[3, 4], flags=ND_WRITABLE|ND_PIL)

        # 'C'
        b = py_buffer_to_contiguous(nd, 'C', PyBUF_FULL_RO)
        self.assertEqual(b, nd.tobytes())
        y = ndarray([v fuer v in b], shape=[3, 4], flags=ND_WRITABLE)
        self.assertEqual(memoryview(y), memoryview(nd))

        # 'F'
        b = py_buffer_to_contiguous(nd, 'F', PyBUF_FULL_RO)
        x = ndarray(transpose(lst, [3, 4]), shape=[4, 3], flags=ND_WRITABLE)
        self.assertEqual(b, x.tobytes())
        y = ndarray([v fuer v in b], shape=[3, 4], flags=ND_FORTRAN|ND_WRITABLE)
        self.assertEqual(memoryview(y), memoryview(nd))

        # 'A'
        b = py_buffer_to_contiguous(nd, 'A', PyBUF_FULL_RO)
        self.assertEqual(b, nd.tobytes())
        y = ndarray([v fuer v in b], shape=[3, 4], flags=ND_WRITABLE)
        self.assertEqual(memoryview(y), memoryview(nd))

    def test_memoryview_construction(self):

        items_shape = [(9, []), ([1,2,3], [3]), (list(range(2*3*5)), [2,3,5])]

        # NumPy style, C-contiguous:
        fuer items, shape in items_shape:

            # From PEP-3118 compliant exporter:
            ex = ndarray(items, shape=shape)
            m = memoryview(ex)
            self.assertWahr(m.c_contiguous)
            self.assertWahr(m.contiguous)

            ndim = len(shape)
            strides = strides_from_shape(ndim, shape, 1, 'C')
            lst = carray(items, shape)

            self.verify(m, obj=ex,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=strides,
                        lst=lst)

            # From memoryview:
            m2 = memoryview(m)
            self.verify(m2, obj=ex,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=strides,
                        lst=lst)

            # PyMemoryView_FromBuffer(): no strides
            nd = ndarray(ex, getbuf=PyBUF_CONTIG_RO|PyBUF_FORMAT)
            self.assertEqual(nd.strides, ())
            m = nd.memoryview_from_buffer()
            self.verify(m, obj=Nichts,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=strides,
                        lst=lst)

            # PyMemoryView_FromBuffer(): no format, shape, strides
            nd = ndarray(ex, getbuf=PyBUF_SIMPLE)
            self.assertEqual(nd.format, '')
            self.assertEqual(nd.shape, ())
            self.assertEqual(nd.strides, ())
            m = nd.memoryview_from_buffer()

            lst = [items] wenn ndim == 0 sonst items
            self.verify(m, obj=Nichts,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=1, shape=[ex.nbytes], strides=(1,),
                        lst=lst)

        # NumPy style, Fortran contiguous:
        fuer items, shape in items_shape:

            # From PEP-3118 compliant exporter:
            ex = ndarray(items, shape=shape, flags=ND_FORTRAN)
            m = memoryview(ex)
            self.assertWahr(m.f_contiguous)
            self.assertWahr(m.contiguous)

            ndim = len(shape)
            strides = strides_from_shape(ndim, shape, 1, 'F')
            lst = farray(items, shape)

            self.verify(m, obj=ex,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=strides,
                        lst=lst)

            # From memoryview:
            m2 = memoryview(m)
            self.verify(m2, obj=ex,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=strides,
                        lst=lst)

        # PIL style:
        fuer items, shape in items_shape[1:]:

            # From PEP-3118 compliant exporter:
            ex = ndarray(items, shape=shape, flags=ND_PIL)
            m = memoryview(ex)

            ndim = len(shape)
            lst = carray(items, shape)

            self.verify(m, obj=ex,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=ex.strides,
                        lst=lst)

            # From memoryview:
            m2 = memoryview(m)
            self.verify(m2, obj=ex,
                        itemsize=1, fmt='B', readonly=Wahr,
                        ndim=ndim, shape=shape, strides=ex.strides,
                        lst=lst)

        # Invalid number of arguments:
        self.assertRaises(TypeError, memoryview, b'9', 'x')
        # Not a buffer provider:
        self.assertRaises(TypeError, memoryview, {})
        # Non-compliant buffer provider:
        ex = ndarray([1,2,3], shape=[3])
        nd = ndarray(ex, getbuf=PyBUF_SIMPLE)
        self.assertRaises(BufferError, memoryview, nd)
        nd = ndarray(ex, getbuf=PyBUF_CONTIG_RO|PyBUF_FORMAT)
        self.assertRaises(BufferError, memoryview, nd)

        # ndim > 64
        nd = ndarray([1]*128, shape=[1]*128, format='L')
        self.assertRaises(ValueError, memoryview, nd)
        self.assertRaises(ValueError, nd.memoryview_from_buffer)
        self.assertRaises(ValueError, get_contiguous, nd, PyBUF_READ, 'C')
        self.assertRaises(ValueError, get_contiguous, nd, PyBUF_READ, 'F')
        self.assertRaises(ValueError, get_contiguous, nd[::-1], PyBUF_READ, 'C')

    def test_memoryview_cast_zero_shape(self):
        # Casts are undefined wenn buffer is multidimensional and shape
        # contains zeros. These arrays are regarded as C-contiguous by
        # Numpy and PyBuffer_GetContiguous(), so they are not caught by
        # the test fuer C-contiguity in memory_cast().
        items = [1,2,3]
        fuer shape in ([0,3,3], [3,0,3], [0,3,3]):
            ex = ndarray(items, shape=shape)
            self.assertWahr(ex.c_contiguous)
            msrc = memoryview(ex)
            self.assertRaises(TypeError, msrc.cast, 'c')
        # Monodimensional empty view can be cast (issue #19014).
        fuer fmt, _, _ in iter_format(1, 'memoryview'):
            msrc = memoryview(b'')
            m = msrc.cast(fmt)
            self.assertEqual(m.tobytes(), b'')
            self.assertEqual(m.tolist(), [])

    check_sizeof = support.check_sizeof

    def test_memoryview_sizeof(self):
        check = self.check_sizeof
        vsize = support.calcvobjsize
        base_struct = 'Pnin 2P2n2i5P P'
        per_dim = '3n'

        items = list(range(8))
        check(memoryview(b''), vsize(base_struct + 1 * per_dim))
        a = ndarray(items, shape=[2, 4], format="b")
        check(memoryview(a), vsize(base_struct + 2 * per_dim))
        a = ndarray(items, shape=[2, 2, 2], format="b")
        check(memoryview(a), vsize(base_struct + 3 * per_dim))

    def test_memoryview_struct_module(self):

        klasse INT(object):
            def __init__(self, val):
                self.val = val
            def __int__(self):
                return self.val

        klasse IDX(object):
            def __init__(self, val):
                self.val = val
            def __index__(self):
                return self.val

        def f(): return 7

        values = [INT(9), IDX(9),
                  2.2+3j, Decimal("-21.1"), 12.2, Fraction(5, 2),
                  [1,2,3], {4,5,6}, {7:8}, (), (9,),
                  Wahr, Falsch, Nichts, Ellipsis,
                  b'a', b'abc', bytearray(b'a'), bytearray(b'abc'),
                  'a', 'abc', r'a', r'abc',
                  f, lambda x: x]

        fuer fmt, items, item in iter_format(10, 'memoryview'):
            ex = ndarray(items, shape=[10], format=fmt, flags=ND_WRITABLE)
            nd = ndarray(items, shape=[10], format=fmt, flags=ND_WRITABLE)
            m = memoryview(ex)

            struct.pack_into(fmt, nd, 0, item)
            m[0] = item
            self.assertEqual(m[0], nd[0])

            itemsize = struct.calcsize(fmt)
            wenn 'P' in fmt:
                continue

            fuer v in values:
                struct_err = Nichts
                try:
                    struct.pack_into(fmt, nd, itemsize, v)
                except struct.error:
                    struct_err = struct.error

                mv_err = Nichts
                try:
                    m[1] = v
                except (TypeError, ValueError) as e:
                    mv_err = e.__class__

                wenn struct_err or mv_err:
                    self.assertIsNot(struct_err, Nichts)
                    self.assertIsNot(mv_err, Nichts)
                sonst:
                    self.assertEqual(m[1], nd[1])

    def test_memoryview_cast_zero_strides(self):
        # Casts are undefined wenn strides contains zeros. These arrays are
        # (sometimes!) regarded as C-contiguous by Numpy, but not by
        # PyBuffer_GetContiguous().
        ex = ndarray([1,2,3], shape=[3], strides=[0])
        self.assertFalsch(ex.c_contiguous)
        msrc = memoryview(ex)
        self.assertRaises(TypeError, msrc.cast, 'c')

    def test_memoryview_cast_invalid(self):
        # invalid format
        fuer sfmt in NON_BYTE_FORMAT:
            sformat = '@' + sfmt wenn randrange(2) sonst sfmt
            ssize = struct.calcsize(sformat)
            fuer dfmt in NON_BYTE_FORMAT:
                dformat = '@' + dfmt wenn randrange(2) sonst dfmt
                dsize = struct.calcsize(dformat)
                ex = ndarray(list(range(32)), shape=[32//ssize], format=sformat)
                msrc = memoryview(ex)
                self.assertRaises(TypeError, msrc.cast, dfmt, [32//dsize])

        fuer sfmt, sitems, _ in iter_format(1):
            ex = ndarray(sitems, shape=[1], format=sfmt)
            msrc = memoryview(ex)
            fuer dfmt, _, _ in iter_format(1):
                wenn not is_memoryview_format(dfmt):
                    self.assertRaises(ValueError, msrc.cast, dfmt,
                                      [32//dsize])
                sonst:
                    wenn not is_byte_format(sfmt) and not is_byte_format(dfmt):
                        self.assertRaises(TypeError, msrc.cast, dfmt,
                                          [32//dsize])

        # invalid shape
        size_h = struct.calcsize('h')
        size_d = struct.calcsize('d')
        ex = ndarray(list(range(2*2*size_d)), shape=[2,2,size_d], format='h')
        msrc = memoryview(ex)
        self.assertRaises(TypeError, msrc.cast, shape=[2,2,size_h], format='d')

        ex = ndarray(list(range(120)), shape=[1,2,3,4,5])
        m = memoryview(ex)

        # incorrect number of args
        self.assertRaises(TypeError, m.cast)
        self.assertRaises(TypeError, m.cast, 1, 2, 3)

        # incorrect dest format type
        self.assertRaises(TypeError, m.cast, {})

        # incorrect dest format
        self.assertRaises(ValueError, m.cast, "X")
        self.assertRaises(ValueError, m.cast, "@X")
        self.assertRaises(ValueError, m.cast, "@XY")

        # dest format not implemented
        self.assertRaises(ValueError, m.cast, "=B")
        self.assertRaises(ValueError, m.cast, "!L")
        self.assertRaises(ValueError, m.cast, "<P")
        self.assertRaises(ValueError, m.cast, ">l")
        self.assertRaises(ValueError, m.cast, "BI")
        self.assertRaises(ValueError, m.cast, "xBI")

        # src format not implemented
        ex = ndarray([(1,2), (3,4)], shape=[2], format="II")
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__getitem__, 0)
        self.assertRaises(NotImplementedError, m.__setitem__, 0, 8)
        self.assertRaises(NotImplementedError, m.tolist)

        # incorrect shape type
        ex = ndarray(list(range(120)), shape=[1,2,3,4,5])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "B", shape={})

        # incorrect shape elements
        ex = ndarray(list(range(120)), shape=[2*3*4*5])
        m = memoryview(ex)
        self.assertRaises(OverflowError, m.cast, "B", shape=[2**64])
        self.assertRaises(ValueError, m.cast, "B", shape=[-1])
        self.assertRaises(ValueError, m.cast, "B", shape=[2,3,4,5,6,7,-1])
        self.assertRaises(ValueError, m.cast, "B", shape=[2,3,4,5,6,7,0])
        self.assertRaises(TypeError, m.cast, "B", shape=[2,3,4,5,6,7,'x'])

        # N-D -> N-D cast
        ex = ndarray(list([9 fuer _ in range(3*5*7*11)]), shape=[3,5,7,11])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "I", shape=[2,3,4,5])

        # cast with ndim > 64
        nd = ndarray(list(range(128)), shape=[128], format='I')
        m = memoryview(nd)
        self.assertRaises(ValueError, m.cast, 'I', [1]*128)

        # view->len not a multiple of itemsize
        ex = ndarray(list([9 fuer _ in range(3*5*7*11)]), shape=[3*5*7*11])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "I", shape=[2,3,4,5])

        # product(shape) * itemsize != buffer size
        ex = ndarray(list([9 fuer _ in range(3*5*7*11)]), shape=[3*5*7*11])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "B", shape=[2,3,4,5])

        # product(shape) * itemsize overflow
        nd = ndarray(list(range(128)), shape=[128], format='I')
        m1 = memoryview(nd)
        nd = ndarray(list(range(128)), shape=[128], format='B')
        m2 = memoryview(nd)
        wenn sys.maxsize == 2**63-1:
            self.assertRaises(TypeError, m1.cast, 'B',
                              [7, 7, 73, 127, 337, 92737, 649657])
            self.assertRaises(ValueError, m1.cast, 'B',
                              [2**20, 2**20, 2**10, 2**10, 2**3])
            self.assertRaises(ValueError, m2.cast, 'I',
                              [2**20, 2**20, 2**10, 2**10, 2**1])
        sonst:
            self.assertRaises(TypeError, m1.cast, 'B',
                              [1, 2147483647])
            self.assertRaises(ValueError, m1.cast, 'B',
                              [2**10, 2**10, 2**5, 2**5, 2**1])
            self.assertRaises(ValueError, m2.cast, 'I',
                              [2**10, 2**10, 2**5, 2**3, 2**1])

    def test_memoryview_cast(self):
        bytespec = (
          ('B', lambda ex: list(ex.tobytes())),
          ('b', lambda ex: [x-256 wenn x > 127 sonst x fuer x in list(ex.tobytes())]),
          ('c', lambda ex: [bytes(chr(x), 'latin-1') fuer x in list(ex.tobytes())]),
        )

        def iter_roundtrip(ex, m, items, fmt):
            srcsize = struct.calcsize(fmt)
            fuer bytefmt, to_bytelist in bytespec:

                m2 = m.cast(bytefmt)
                lst = to_bytelist(ex)
                self.verify(m2, obj=ex,
                            itemsize=1, fmt=bytefmt, readonly=Falsch,
                            ndim=1, shape=[31*srcsize], strides=(1,),
                            lst=lst, cast=Wahr)

                m3 = m2.cast(fmt)
                self.assertEqual(m3, ex)
                lst = ex.tolist()
                self.verify(m3, obj=ex,
                            itemsize=srcsize, fmt=fmt, readonly=Falsch,
                            ndim=1, shape=[31], strides=(srcsize,),
                            lst=lst, cast=Wahr)

        # cast from ndim = 0 to ndim = 1
        srcsize = struct.calcsize('I')
        ex = ndarray(9, shape=[], format='I')
        destitems, destshape = cast_items(ex, 'B', 1)
        m = memoryview(ex)
        m2 = m.cast('B')
        self.verify(m2, obj=ex,
                    itemsize=1, fmt='B', readonly=Wahr,
                    ndim=1, shape=destshape, strides=(1,),
                    lst=destitems, cast=Wahr)

        # cast from ndim = 1 to ndim = 0
        destsize = struct.calcsize('I')
        ex = ndarray([9]*destsize, shape=[destsize], format='B')
        destitems, destshape = cast_items(ex, 'I', destsize, shape=[])
        m = memoryview(ex)
        m2 = m.cast('I', shape=[])
        self.verify(m2, obj=ex,
                    itemsize=destsize, fmt='I', readonly=Wahr,
                    ndim=0, shape=(), strides=(),
                    lst=destitems, cast=Wahr)

        # array.array: roundtrip to/from bytes
        fuer fmt, items, _ in iter_format(31, 'array'):
            ex = array.array(fmt, items)
            m = memoryview(ex)
            iter_roundtrip(ex, m, items, fmt)

        # ndarray: roundtrip to/from bytes
        fuer fmt, items, _ in iter_format(31, 'memoryview'):
            ex = ndarray(items, shape=[31], format=fmt, flags=ND_WRITABLE)
            m = memoryview(ex)
            iter_roundtrip(ex, m, items, fmt)

    @support.requires_resource('cpu')
    def test_memoryview_cast_1D_ND(self):
        # Cast between C-contiguous buffers. At least one buffer must
        # be 1D, at least one format must be 'c', 'b' or 'B'.
        fuer _tshape in gencastshapes():
            fuer char in fmtdict['@']:
                # Casts to _Bool are undefined wenn the source contains values
                # other than 0 or 1.
                wenn char == "?":
                    continue
                tfmt = ('', '@')[randrange(2)] + char
                tsize = struct.calcsize(tfmt)
                n = prod(_tshape) * tsize
                obj = 'memoryview' wenn is_byte_format(tfmt) sonst 'bytefmt'
                fuer fmt, items, _ in iter_format(n, obj):
                    size = struct.calcsize(fmt)
                    shape = [n] wenn n > 0 sonst []
                    tshape = _tshape + [size]

                    ex = ndarray(items, shape=shape, format=fmt)
                    m = memoryview(ex)

                    titems, tshape = cast_items(ex, tfmt, tsize, shape=tshape)

                    wenn titems is Nichts:
                        self.assertRaises(TypeError, m.cast, tfmt, tshape)
                        continue
                    wenn titems == 'nan':
                        continue # NaNs in lists are a recipe fuer trouble.

                    # 1D -> ND
                    nd = ndarray(titems, shape=tshape, format=tfmt)

                    m2 = m.cast(tfmt, shape=tshape)
                    ndim = len(tshape)
                    strides = nd.strides
                    lst = nd.tolist()
                    self.verify(m2, obj=ex,
                                itemsize=tsize, fmt=tfmt, readonly=Wahr,
                                ndim=ndim, shape=tshape, strides=strides,
                                lst=lst, cast=Wahr)

                    # ND -> 1D
                    m3 = m2.cast(fmt)
                    m4 = m2.cast(fmt, shape=shape)
                    ndim = len(shape)
                    strides = ex.strides
                    lst = ex.tolist()

                    self.verify(m3, obj=ex,
                                itemsize=size, fmt=fmt, readonly=Wahr,
                                ndim=ndim, shape=shape, strides=strides,
                                lst=lst, cast=Wahr)

                    self.verify(m4, obj=ex,
                                itemsize=size, fmt=fmt, readonly=Wahr,
                                ndim=ndim, shape=shape, strides=strides,
                                lst=lst, cast=Wahr)

        wenn ctypes:
            # format: "T{>l:x:>d:y:}"
            klasse BEPoint(ctypes.BigEndianStructure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_double)]
            point = BEPoint(100, 200.1)
            m1 = memoryview(point)
            m2 = m1.cast('B')
            self.assertEqual(m2.obj, point)
            self.assertEqual(m2.itemsize, 1)
            self.assertIs(m2.readonly, Falsch)
            self.assertEqual(m2.ndim, 1)
            self.assertEqual(m2.shape, (m2.nbytes,))
            self.assertEqual(m2.strides, (1,))
            self.assertEqual(m2.suboffsets, ())

            x = ctypes.c_double(1.2)
            m1 = memoryview(x)
            m2 = m1.cast('c')
            self.assertEqual(m2.obj, x)
            self.assertEqual(m2.itemsize, 1)
            self.assertIs(m2.readonly, Falsch)
            self.assertEqual(m2.ndim, 1)
            self.assertEqual(m2.shape, (m2.nbytes,))
            self.assertEqual(m2.strides, (1,))
            self.assertEqual(m2.suboffsets, ())

    def test_memoryview_tolist(self):

        # Most tolist() tests are in self.verify() etc.

        a = array.array('h', list(range(-6, 6)))
        m = memoryview(a)
        self.assertEqual(m, a)
        self.assertEqual(m.tolist(), a.tolist())

        a = a[2::3]
        m = m[2::3]
        self.assertEqual(m, a)
        self.assertEqual(m.tolist(), a.tolist())

        ex = ndarray(list(range(2*3*5*7*11)), shape=[11,2,7,3,5], format='L')
        m = memoryview(ex)
        self.assertEqual(m.tolist(), ex.tolist())

        ex = ndarray([(2, 5), (7, 11)], shape=[2], format='lh')
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.tolist)

        ex = ndarray([b'12345'], shape=[1], format="s")
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.tolist)

        ex = ndarray([b"a",b"b",b"c",b"d",b"e",b"f"], shape=[2,3], format='s')
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.tolist)

    def test_memoryview_repr(self):
        m = memoryview(bytearray(9))
        r = m.__repr__()
        self.assertStartsWith(r, "<memory")

        m.release()
        r = m.__repr__()
        self.assertStartsWith(r, "<released")

    def test_memoryview_sequence(self):

        fuer fmt in ('d', 'f'):
            inf = float(3e400)
            ex = array.array(fmt, [1.0, inf, 3.0])
            m = memoryview(ex)
            self.assertIn(1.0, m)
            self.assertIn(5e700, m)
            self.assertIn(3.0, m)

        ex = ndarray(9.0, [], format='f')
        m = memoryview(ex)
        self.assertRaises(TypeError, eval, "9.0 in m", locals())

    @contextlib.contextmanager
    def assert_out_of_bounds_error(self, dim):
        with self.assertRaises(IndexError) as cm:
            yield
        self.assertEqual(str(cm.exception),
                         "index out of bounds on dimension %d" % (dim,))

    def test_memoryview_index(self):

        # ndim = 0
        ex = ndarray(12.5, shape=[], format='d')
        m = memoryview(ex)
        self.assertEqual(m[()], 12.5)
        self.assertEqual(m[...], m)
        self.assertEqual(m[...], ex)
        self.assertRaises(TypeError, m.__getitem__, 0)

        ex = ndarray((1,2,3), shape=[], format='iii')
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__getitem__, ())

        # range
        ex = ndarray(list(range(7)), shape=[7], flags=ND_WRITABLE)
        m = memoryview(ex)

        self.assertRaises(IndexError, m.__getitem__, 2**64)
        self.assertRaises(TypeError, m.__getitem__, 2.0)
        self.assertRaises(TypeError, m.__getitem__, 0.0)

        # out of bounds
        self.assertRaises(IndexError, m.__getitem__, -8)
        self.assertRaises(IndexError, m.__getitem__, 8)

        # multi-dimensional
        ex = ndarray(list(range(12)), shape=[3,4], flags=ND_WRITABLE)
        m = memoryview(ex)

        self.assertEqual(m[0, 0], 0)
        self.assertEqual(m[2, 0], 8)
        self.assertEqual(m[2, 3], 11)
        self.assertEqual(m[-1, -1], 11)
        self.assertEqual(m[-3, -4], 0)

        # out of bounds
        fuer index in (3, -4):
            with self.assert_out_of_bounds_error(dim=1):
                m[index, 0]
        fuer index in (4, -5):
            with self.assert_out_of_bounds_error(dim=2):
                m[0, index]
        self.assertRaises(IndexError, m.__getitem__, (2**64, 0))
        self.assertRaises(IndexError, m.__getitem__, (0, 2**64))

        self.assertRaises(TypeError, m.__getitem__, (0, 0, 0))
        self.assertRaises(TypeError, m.__getitem__, (0.0, 0.0))

        # Not implemented: multidimensional sub-views
        self.assertRaises(NotImplementedError, m.__getitem__, ())
        self.assertRaises(NotImplementedError, m.__getitem__, 0)

    def test_memoryview_assign(self):

        # ndim = 0
        ex = ndarray(12.5, shape=[], format='f', flags=ND_WRITABLE)
        m = memoryview(ex)
        m[()] = 22.5
        self.assertEqual(m[()], 22.5)
        m[...] = 23.5
        self.assertEqual(m[()], 23.5)
        self.assertRaises(TypeError, m.__setitem__, 0, 24.7)

        # read-only
        ex = ndarray(list(range(7)), shape=[7])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.__setitem__, 2, 10)

        # range
        ex = ndarray(list(range(7)), shape=[7], flags=ND_WRITABLE)
        m = memoryview(ex)

        self.assertRaises(IndexError, m.__setitem__, 2**64, 9)
        self.assertRaises(TypeError, m.__setitem__, 2.0, 10)
        self.assertRaises(TypeError, m.__setitem__, 0.0, 11)

        # out of bounds
        self.assertRaises(IndexError, m.__setitem__, -8, 20)
        self.assertRaises(IndexError, m.__setitem__, 8, 25)

        # pack_single() success:
        fuer fmt in fmtdict['@']:
            wenn fmt == 'c' or fmt == '?':
                continue
            ex = ndarray([1,2,3], shape=[3], format=fmt, flags=ND_WRITABLE)
            m = memoryview(ex)
            i = randrange(-3, 3)
            m[i] = 8
            self.assertEqual(m[i], 8)
            self.assertEqual(m[i], ex[i])

        ex = ndarray([b'1', b'2', b'3'], shape=[3], format='c',
                     flags=ND_WRITABLE)
        m = memoryview(ex)
        m[2] = b'9'
        self.assertEqual(m[2], b'9')

        ex = ndarray([Wahr, Falsch, Wahr], shape=[3], format='?',
                     flags=ND_WRITABLE)
        m = memoryview(ex)
        m[1] = Wahr
        self.assertIs(m[1], Wahr)

        # pack_single() exceptions:
        nd = ndarray([b'x'], shape=[1], format='c', flags=ND_WRITABLE)
        m = memoryview(nd)
        self.assertRaises(TypeError, m.__setitem__, 0, 100)

        ex = ndarray(list(range(120)), shape=[1,2,3,4,5], flags=ND_WRITABLE)
        m1 = memoryview(ex)

        fuer fmt, _range in fmtdict['@'].items():
            wenn (fmt == '?'): # PyObject_IsWahr() accepts anything
                continue
            wenn fmt == 'c': # special case tested above
                continue
            m2 = m1.cast(fmt)
            lo, hi = _range
            wenn fmt == 'd' or fmt == 'f':
                lo, hi = -2**1024, 2**1024
            wenn fmt != 'P': # PyLong_AsVoidPtr() accepts negative numbers
                self.assertRaises(ValueError, m2.__setitem__, 0, lo-1)
                self.assertRaises(TypeError, m2.__setitem__, 0, "xyz")
            self.assertRaises(ValueError, m2.__setitem__, 0, hi)

        # invalid item
        m2 = m1.cast('c')
        self.assertRaises(ValueError, m2.__setitem__, 0, b'\xff\xff')

        # format not implemented
        ex = ndarray(list(range(1)), shape=[1], format="xL", flags=ND_WRITABLE)
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__setitem__, 0, 1)

        ex = ndarray([b'12345'], shape=[1], format="s", flags=ND_WRITABLE)
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__setitem__, 0, 1)

        # multi-dimensional
        ex = ndarray(list(range(12)), shape=[3,4], flags=ND_WRITABLE)
        m = memoryview(ex)
        m[0,1] = 42
        self.assertEqual(ex[0][1], 42)
        m[-1,-1] = 43
        self.assertEqual(ex[2][3], 43)
        # errors
        fuer index in (3, -4):
            with self.assert_out_of_bounds_error(dim=1):
                m[index, 0] = 0
        fuer index in (4, -5):
            with self.assert_out_of_bounds_error(dim=2):
                m[0, index] = 0
        self.assertRaises(IndexError, m.__setitem__, (2**64, 0), 0)
        self.assertRaises(IndexError, m.__setitem__, (0, 2**64), 0)

        self.assertRaises(TypeError, m.__setitem__, (0, 0, 0), 0)
        self.assertRaises(TypeError, m.__setitem__, (0.0, 0.0), 0)

        # Not implemented: multidimensional sub-views
        self.assertRaises(NotImplementedError, m.__setitem__, 0, [2, 3])

    def test_memoryview_slice(self):

        ex = ndarray(list(range(12)), shape=[12], flags=ND_WRITABLE)
        m = memoryview(ex)

        # zero step
        self.assertRaises(ValueError, m.__getitem__, slice(0,2,0))
        self.assertRaises(ValueError, m.__setitem__, slice(0,2,0),
                          bytearray([1,2]))

        # 0-dim slicing (identity function)
        self.assertRaises(NotImplementedError, m.__getitem__, ())

        # multidimensional slices
        ex = ndarray(list(range(12)), shape=[12], flags=ND_WRITABLE)
        m = memoryview(ex)

        self.assertRaises(NotImplementedError, m.__getitem__,
                          (slice(0,2,1), slice(0,2,1)))
        self.assertRaises(NotImplementedError, m.__setitem__,
                          (slice(0,2,1), slice(0,2,1)), bytearray([1,2]))

        # invalid slice tuple
        self.assertRaises(TypeError, m.__getitem__, (slice(0,2,1), {}))
        self.assertRaises(TypeError, m.__setitem__, (slice(0,2,1), {}),
                          bytearray([1,2]))

        # rvalue is not an exporter
        self.assertRaises(TypeError, m.__setitem__, slice(0,1,1), [1])

        # non-contiguous slice assignment
        fuer flags in (0, ND_PIL):
            ex1 = ndarray(list(range(12)), shape=[12], strides=[-1], offset=11,
                          flags=ND_WRITABLE|flags)
            ex2 = ndarray(list(range(24)), shape=[12], strides=[2], flags=flags)
            m1 = memoryview(ex1)
            m2 = memoryview(ex2)

            ex1[2:5] = ex1[2:5]
            m1[2:5] = m2[2:5]

            self.assertEqual(m1, ex1)
            self.assertEqual(m2, ex2)

            ex1[1:3][::-1] = ex2[0:2][::1]
            m1[1:3][::-1] = m2[0:2][::1]

            self.assertEqual(m1, ex1)
            self.assertEqual(m2, ex2)

            ex1[4:1:-2][::-1] = ex1[1:4:2][::1]
            m1[4:1:-2][::-1] = m1[1:4:2][::1]

            self.assertEqual(m1, ex1)
            self.assertEqual(m2, ex2)

    def test_memoryview_array(self):

        def cmptest(testcase, a, b, m, singleitem):
            fuer i, _ in enumerate(a):
                ai = a[i]
                mi = m[i]
                testcase.assertEqual(ai, mi)
                a[i] = singleitem
                wenn singleitem != ai:
                    testcase.assertNotEqual(a, m)
                    testcase.assertNotEqual(a, b)
                sonst:
                    testcase.assertEqual(a, m)
                    testcase.assertEqual(a, b)
                m[i] = singleitem
                testcase.assertEqual(a, m)
                testcase.assertEqual(b, m)
                a[i] = ai
                m[i] = mi

        fuer n in range(1, 5):
            fuer fmt, items, singleitem in iter_format(n, 'array'):
                fuer lslice in genslices(n):
                    fuer rslice in genslices(n):

                        a = array.array(fmt, items)
                        b = array.array(fmt, items)
                        m = memoryview(b)

                        self.assertEqual(m, a)
                        self.assertEqual(m.tolist(), a.tolist())
                        self.assertEqual(m.tobytes(), a.tobytes())
                        self.assertEqual(len(m), len(a))

                        cmptest(self, a, b, m, singleitem)

                        array_err = Nichts
                        have_resize = Nichts
                        try:
                            al = a[lslice]
                            ar = a[rslice]
                            a[lslice] = a[rslice]
                            have_resize = len(al) != len(ar)
                        except Exception as e:
                            array_err = e.__class__

                        m_err = Nichts
                        try:
                            m[lslice] = m[rslice]
                        except Exception as e:
                            m_err = e.__class__

                        wenn have_resize: # memoryview cannot change shape
                            self.assertIs(m_err, ValueError)
                        sowenn m_err or array_err:
                            self.assertIs(m_err, array_err)
                        sonst:
                            self.assertEqual(m, a)
                            self.assertEqual(m.tolist(), a.tolist())
                            self.assertEqual(m.tobytes(), a.tobytes())
                            cmptest(self, a, b, m, singleitem)

    def test_memoryview_compare_special_cases(self):

        a = array.array('L', [1, 2, 3])
        b = array.array('L', [1, 2, 7])

        # Ordering comparisons raise:
        v = memoryview(a)
        w = memoryview(b)
        fuer attr in ('__lt__', '__le__', '__gt__', '__ge__'):
            self.assertIs(getattr(v, attr)(w), NotImplemented)
            self.assertIs(getattr(a, attr)(v), NotImplemented)

        # Released views compare equal to themselves:
        v = memoryview(a)
        v.release()
        self.assertEqual(v, v)
        self.assertNotEqual(v, a)
        self.assertNotEqual(a, v)

        v = memoryview(a)
        w = memoryview(a)
        w.release()
        self.assertNotEqual(v, w)
        self.assertNotEqual(w, v)

        # Operand does not implement the buffer protocol:
        v = memoryview(a)
        self.assertNotEqual(v, [1, 2, 3])

        # NaNs
        nd = ndarray([(0, 0)], shape=[1], format='l x d x', flags=ND_WRITABLE)
        nd[0] = (-1, float('nan'))
        self.assertNotEqual(memoryview(nd), nd)

        # Some ctypes format strings are unknown to the struct module.
        wenn ctypes:
            # format: "T{>l:x:>l:y:}"
            klasse BEPoint(ctypes.BigEndianStructure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            point = BEPoint(100, 200)
            a = memoryview(point)
            b = memoryview(point)
            self.assertNotEqual(a, b)
            self.assertNotEqual(a, point)
            self.assertNotEqual(point, a)
            self.assertRaises(NotImplementedError, a.tolist)

    @warnings_helper.ignore_warnings(category=DeprecationWarning)  # gh-80480 array('u')
    def test_memoryview_compare_special_cases_deprecated_u_type_code(self):

        # Depends on issue #15625: the struct module does not understand 'u'.
        a = array.array('u', 'xyz')
        v = memoryview(a)
        self.assertNotEqual(a, v)
        self.assertNotEqual(v, a)

    def test_memoryview_compare_ndim_zero(self):

        nd1 = ndarray(1729, shape=[], format='@L')
        nd2 = ndarray(1729, shape=[], format='L', flags=ND_WRITABLE)
        v = memoryview(nd1)
        w = memoryview(nd2)
        self.assertEqual(v, w)
        self.assertEqual(w, v)
        self.assertEqual(v, nd2)
        self.assertEqual(nd2, v)
        self.assertEqual(w, nd1)
        self.assertEqual(nd1, w)

        self.assertFalsch(v.__ne__(w))
        self.assertFalsch(w.__ne__(v))

        w[()] = 1728
        self.assertNotEqual(v, w)
        self.assertNotEqual(w, v)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(nd2, v)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(nd1, w)

        self.assertFalsch(v.__eq__(w))
        self.assertFalsch(w.__eq__(v))

        nd = ndarray(list(range(12)), shape=[12], flags=ND_WRITABLE|ND_PIL)
        ex = ndarray(list(range(12)), shape=[12], flags=ND_WRITABLE|ND_PIL)
        m = memoryview(ex)

        self.assertEqual(m, nd)
        m[9] = 100
        self.assertNotEqual(m, nd)

        # struct module: equal
        nd1 = ndarray((1729, 1.2, b'12345'), shape=[], format='Lf5s')
        nd2 = ndarray((1729, 1.2, b'12345'), shape=[], format='hf5s',
                      flags=ND_WRITABLE)
        v = memoryview(nd1)
        w = memoryview(nd2)
        self.assertEqual(v, w)
        self.assertEqual(w, v)
        self.assertEqual(v, nd2)
        self.assertEqual(nd2, v)
        self.assertEqual(w, nd1)
        self.assertEqual(nd1, w)

        # struct module: not equal
        nd1 = ndarray((1729, 1.2, b'12345'), shape=[], format='Lf5s')
        nd2 = ndarray((-1729, 1.2, b'12345'), shape=[], format='hf5s',
                      flags=ND_WRITABLE)
        v = memoryview(nd1)
        w = memoryview(nd2)
        self.assertNotEqual(v, w)
        self.assertNotEqual(w, v)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(nd2, v)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(nd1, w)
        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)

    def test_memoryview_compare_ndim_one(self):

        # contiguous
        nd1 = ndarray([-529, 576, -625, 676, -729], shape=[5], format='@h')
        nd2 = ndarray([-529, 576, -625, 676, 729], shape=[5], format='@h')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # contiguous, struct module
        nd1 = ndarray([-529, 576, -625, 676, -729], shape=[5], format='<i')
        nd2 = ndarray([-529, 576, -625, 676, 729], shape=[5], format='>h')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # non-contiguous
        nd1 = ndarray([-529, -625, -729], shape=[3], format='@h')
        nd2 = ndarray([-529, 576, -625, 676, -729], shape=[5], format='@h')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd2[::2])
        self.assertEqual(w[::2], nd1)
        self.assertEqual(v, w[::2])
        self.assertEqual(v[::-1], w[::-2])

        # non-contiguous, struct module
        nd1 = ndarray([-529, -625, -729], shape=[3], format='!h')
        nd2 = ndarray([-529, 576, -625, 676, -729], shape=[5], format='<l')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd2[::2])
        self.assertEqual(w[::2], nd1)
        self.assertEqual(v, w[::2])
        self.assertEqual(v[::-1], w[::-2])

        # non-contiguous, suboffsets
        nd1 = ndarray([-529, -625, -729], shape=[3], format='@h')
        nd2 = ndarray([-529, 576, -625, 676, -729], shape=[5], format='@h',
                      flags=ND_PIL)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd2[::2])
        self.assertEqual(w[::2], nd1)
        self.assertEqual(v, w[::2])
        self.assertEqual(v[::-1], w[::-2])

        # non-contiguous, suboffsets, struct module
        nd1 = ndarray([-529, -625, -729], shape=[3], format='h  0c')
        nd2 = ndarray([-529, 576, -625, 676, -729], shape=[5], format='>  h',
                      flags=ND_PIL)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd2[::2])
        self.assertEqual(w[::2], nd1)
        self.assertEqual(v, w[::2])
        self.assertEqual(v[::-1], w[::-2])

    def test_memoryview_compare_zero_shape(self):

        # zeros in shape
        nd1 = ndarray([900, 961], shape=[0], format='@h')
        nd2 = ndarray([-900, -961], shape=[0], format='@h')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

        # zeros in shape, struct module
        nd1 = ndarray([900, 961], shape=[0], format='= h0c')
        nd2 = ndarray([-900, -961], shape=[0], format='@   i')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

    def test_memoryview_compare_zero_strides(self):

        # zero strides
        nd1 = ndarray([900, 900, 900, 900], shape=[4], format='@L')
        nd2 = ndarray([900], shape=[4], strides=[0], format='L')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

        # zero strides, struct module
        nd1 = ndarray([(900, 900)]*4, shape=[4], format='@ Li')
        nd2 = ndarray([(900, 900)], shape=[4], strides=[0], format='!L  h')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

    def test_memoryview_compare_random_formats(self):

        # random single character native formats
        n = 10
        fuer char in fmtdict['@m']:
            fmt, items, singleitem = randitems(n, 'memoryview', '@', char)
            fuer flags in (0, ND_PIL):
                nd = ndarray(items, shape=[n], format=fmt, flags=flags)
                m = memoryview(nd)
                self.assertEqual(m, nd)

                nd = nd[::-3]
                m = memoryview(nd)
                self.assertEqual(m, nd)

        # random formats
        n = 10
        fuer _ in range(100):
            fmt, items, singleitem = randitems(n)
            fuer flags in (0, ND_PIL):
                nd = ndarray(items, shape=[n], format=fmt, flags=flags)
                m = memoryview(nd)
                self.assertEqual(m, nd)

                nd = nd[::-3]
                m = memoryview(nd)
                self.assertEqual(m, nd)

    def test_memoryview_compare_multidim_c(self):

        # C-contiguous, different values
        nd1 = ndarray(list(range(-15, 15)), shape=[3, 2, 5], format='@h')
        nd2 = ndarray(list(range(0, 30)), shape=[3, 2, 5], format='@h')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # C-contiguous, different values, struct module
        nd1 = ndarray([(0, 1, 2)]*30, shape=[3, 2, 5], format='=f q xxL')
        nd2 = ndarray([(-1.2, 1, 2)]*30, shape=[3, 2, 5], format='< f 2Q')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # C-contiguous, different shape
        nd1 = ndarray(list(range(30)), shape=[2, 3, 5], format='L')
        nd2 = ndarray(list(range(30)), shape=[3, 2, 5], format='L')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # C-contiguous, different shape, struct module
        nd1 = ndarray([(0, 1, 2)]*21, shape=[3, 7], format='! b B xL')
        nd2 = ndarray([(0, 1, 2)]*21, shape=[7, 3], format='= Qx l xxL')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # C-contiguous, different format, struct module
        nd1 = ndarray(list(range(30)), shape=[2, 3, 5], format='L')
        nd2 = ndarray(list(range(30)), shape=[2, 3, 5], format='l')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

    def test_memoryview_compare_multidim_fortran(self):

        # Fortran-contiguous, different values
        nd1 = ndarray(list(range(-15, 15)), shape=[5, 2, 3], format='@h',
                      flags=ND_FORTRAN)
        nd2 = ndarray(list(range(0, 30)), shape=[5, 2, 3], format='@h',
                      flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # Fortran-contiguous, different values, struct module
        nd1 = ndarray([(2**64-1, -1)]*6, shape=[2, 3], format='=Qq',
                      flags=ND_FORTRAN)
        nd2 = ndarray([(-1, 2**64-1)]*6, shape=[2, 3], format='=qQ',
                      flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # Fortran-contiguous, different shape
        nd1 = ndarray(list(range(-15, 15)), shape=[2, 3, 5], format='l',
                      flags=ND_FORTRAN)
        nd2 = ndarray(list(range(-15, 15)), shape=[3, 2, 5], format='l',
                      flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # Fortran-contiguous, different shape, struct module
        nd1 = ndarray(list(range(-15, 15)), shape=[2, 3, 5], format='0ll',
                      flags=ND_FORTRAN)
        nd2 = ndarray(list(range(-15, 15)), shape=[3, 2, 5], format='l',
                      flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # Fortran-contiguous, different format, struct module
        nd1 = ndarray(list(range(30)), shape=[5, 2, 3], format='@h',
                      flags=ND_FORTRAN)
        nd2 = ndarray(list(range(30)), shape=[5, 2, 3], format='@b',
                      flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

    def test_memoryview_compare_multidim_mixed(self):

        # mixed C/Fortran contiguous
        lst1 = list(range(-15, 15))
        lst2 = transpose(lst1, [3, 2, 5])
        nd1 = ndarray(lst1, shape=[3, 2, 5], format='@l')
        nd2 = ndarray(lst2, shape=[3, 2, 5], format='l', flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, w)

        # mixed C/Fortran contiguous, struct module
        lst1 = [(-3.3, -22, b'x')]*30
        lst1[5] = (-2.2, -22, b'x')
        lst2 = transpose(lst1, [3, 2, 5])
        nd1 = ndarray(lst1, shape=[3, 2, 5], format='d b c')
        nd2 = ndarray(lst2, shape=[3, 2, 5], format='d h c', flags=ND_FORTRAN)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, w)

        # different values, non-contiguous
        ex1 = ndarray(list(range(40)), shape=[5, 8], format='@I')
        nd1 = ex1[3:1:-1, ::-2]
        ex2 = ndarray(list(range(40)), shape=[5, 8], format='I')
        nd2 = ex2[1:3:1, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # same values, non-contiguous, struct module
        ex1 = ndarray([(2**31-1, -2**31)]*22, shape=[11, 2], format='=ii')
        nd1 = ex1[3:1:-1, ::-2]
        ex2 = ndarray([(2**31-1, -2**31)]*22, shape=[11, 2], format='>ii')
        nd2 = ex2[1:3:1, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

        # different shape
        ex1 = ndarray(list(range(30)), shape=[2, 3, 5], format='b')
        nd1 = ex1[1:3:, ::-2]
        nd2 = ndarray(list(range(30)), shape=[3, 2, 5], format='b')
        nd2 = ex2[1:3:, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # different shape, struct module
        ex1 = ndarray(list(range(30)), shape=[2, 3, 5], format='B')
        nd1 = ex1[1:3:, ::-2]
        nd2 = ndarray(list(range(30)), shape=[3, 2, 5], format='b')
        nd2 = ex2[1:3:, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # different format, struct module
        ex1 = ndarray([(2, b'123')]*30, shape=[5, 3, 2], format='b3s')
        nd1 = ex1[1:3:, ::-2]
        nd2 = ndarray([(2, b'123')]*30, shape=[5, 3, 2], format='i3s')
        nd2 = ex2[1:3:, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

    def test_memoryview_compare_multidim_zero_shape(self):

        # zeros in shape
        nd1 = ndarray(list(range(30)), shape=[0, 3, 2], format='i')
        nd2 = ndarray(list(range(30)), shape=[5, 0, 2], format='@i')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # zeros in shape, struct module
        nd1 = ndarray(list(range(30)), shape=[0, 3, 2], format='i')
        nd2 = ndarray(list(range(30)), shape=[5, 0, 2], format='@i')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

    def test_memoryview_compare_multidim_zero_strides(self):

        # zero strides
        nd1 = ndarray([900]*80, shape=[4, 5, 4], format='@L')
        nd2 = ndarray([900], shape=[4, 5, 4], strides=[0, 0, 0], format='L')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)
        self.assertEqual(v.tolist(), w.tolist())

        # zero strides, struct module
        nd1 = ndarray([(1, 2)]*10, shape=[2, 5], format='=lQ')
        nd2 = ndarray([(1, 2)], shape=[2, 5], strides=[0, 0], format='<lQ')
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

    def test_memoryview_compare_multidim_suboffsets(self):

        # suboffsets
        ex1 = ndarray(list(range(40)), shape=[5, 8], format='@I')
        nd1 = ex1[3:1:-1, ::-2]
        ex2 = ndarray(list(range(40)), shape=[5, 8], format='I', flags=ND_PIL)
        nd2 = ex2[1:3:1, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # suboffsets, struct module
        ex1 = ndarray([(2**64-1, -1)]*40, shape=[5, 8], format='=Qq',
                      flags=ND_WRITABLE)
        ex1[2][7] = (1, -2)
        nd1 = ex1[3:1:-1, ::-2]

        ex2 = ndarray([(2**64-1, -1)]*40, shape=[5, 8], format='>Qq',
                      flags=ND_PIL|ND_WRITABLE)
        ex2[2][7] = (1, -2)
        nd2 = ex2[1:3:1, ::-2]

        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

        # suboffsets, different shape
        ex1 = ndarray(list(range(30)), shape=[2, 3, 5], format='b',
                      flags=ND_PIL)
        nd1 = ex1[1:3:, ::-2]
        nd2 = ndarray(list(range(30)), shape=[3, 2, 5], format='b')
        nd2 = ex2[1:3:, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # suboffsets, different shape, struct module
        ex1 = ndarray([(2**8-1, -1)]*40, shape=[2, 3, 5], format='Bb',
                      flags=ND_PIL|ND_WRITABLE)
        nd1 = ex1[1:2:, ::-2]

        ex2 = ndarray([(2**8-1, -1)]*40, shape=[3, 2, 5], format='Bb')
        nd2 = ex2[1:2:, ::-2]

        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # suboffsets, different format
        ex1 = ndarray(list(range(30)), shape=[5, 3, 2], format='i', flags=ND_PIL)
        nd1 = ex1[1:3:, ::-2]
        ex2 = ndarray(list(range(30)), shape=[5, 3, 2], format='@I', flags=ND_PIL)
        nd2 = ex2[1:3:, ::-2]
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, nd2)
        self.assertEqual(w, nd1)
        self.assertEqual(v, w)

        # suboffsets, different format, struct module
        ex1 = ndarray([(b'hello', b'', 1)]*27, shape=[3, 3, 3], format='5s0sP',
                      flags=ND_PIL|ND_WRITABLE)
        ex1[1][2][2] = (b'sushi', b'', 1)
        nd1 = ex1[1:3:, ::-2]

        ex2 = ndarray([(b'hello', b'', 1)]*27, shape=[3, 3, 3], format='5s0sP',
                      flags=ND_PIL|ND_WRITABLE)
        ex1[1][2][2] = (b'sushi', b'', 1)
        nd2 = ex2[1:3:, ::-2]

        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertNotEqual(v, nd2)
        self.assertNotEqual(w, nd1)
        self.assertNotEqual(v, w)

        # initialize mixed C/Fortran + suboffsets
        lst1 = list(range(-15, 15))
        lst2 = transpose(lst1, [3, 2, 5])
        nd1 = ndarray(lst1, shape=[3, 2, 5], format='@l', flags=ND_PIL)
        nd2 = ndarray(lst2, shape=[3, 2, 5], format='l', flags=ND_FORTRAN|ND_PIL)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, w)

        # initialize mixed C/Fortran + suboffsets, struct module
        lst1 = [(b'sashimi', b'sliced', 20.05)]*30
        lst1[11] = (b'ramen', b'spicy', 9.45)
        lst2 = transpose(lst1, [3, 2, 5])

        nd1 = ndarray(lst1, shape=[3, 2, 5], format='< 10p 9p d', flags=ND_PIL)
        nd2 = ndarray(lst2, shape=[3, 2, 5], format='> 10p 9p d',
                      flags=ND_FORTRAN|ND_PIL)
        v = memoryview(nd1)
        w = memoryview(nd2)

        self.assertEqual(v, nd1)
        self.assertEqual(w, nd2)
        self.assertEqual(v, w)

    def test_memoryview_compare_not_equal(self):

        # items not equal
        fuer byteorder in ['=', '<', '>', '!']:
            x = ndarray([2**63]*120, shape=[3,5,2,2,2], format=byteorder+'Q')
            y = ndarray([2**63]*120, shape=[3,5,2,2,2], format=byteorder+'Q',
                        flags=ND_WRITABLE|ND_FORTRAN)
            y[2][3][1][1][1] = 1
            a = memoryview(x)
            b = memoryview(y)
            self.assertEqual(a, x)
            self.assertEqual(b, y)
            self.assertNotEqual(a, b)
            self.assertNotEqual(a, y)
            self.assertNotEqual(b, x)

            x = ndarray([(2**63, 2**31, 2**15)]*120, shape=[3,5,2,2,2],
                        format=byteorder+'QLH')
            y = ndarray([(2**63, 2**31, 2**15)]*120, shape=[3,5,2,2,2],
                        format=byteorder+'QLH', flags=ND_WRITABLE|ND_FORTRAN)
            y[2][3][1][1][1] = (1, 1, 1)
            a = memoryview(x)
            b = memoryview(y)
            self.assertEqual(a, x)
            self.assertEqual(b, y)
            self.assertNotEqual(a, b)
            self.assertNotEqual(a, y)
            self.assertNotEqual(b, x)

    def test_memoryview_check_released(self):

        a = array.array('d', [1.1, 2.2, 3.3])

        m = memoryview(a)
        m.release()

        # PyMemoryView_FromObject()
        self.assertRaises(ValueError, memoryview, m)
        # memoryview.cast()
        self.assertRaises(ValueError, m.cast, 'c')
        # memoryview.__iter__()
        self.assertRaises(ValueError, m.__iter__)
        # getbuffer()
        self.assertRaises(ValueError, ndarray, m)
        # memoryview.tolist()
        self.assertRaises(ValueError, m.tolist)
        # memoryview.tobytes()
        self.assertRaises(ValueError, m.tobytes)
        # sequence
        self.assertRaises(ValueError, eval, "1.0 in m", locals())
        # subscript
        self.assertRaises(ValueError, m.__getitem__, 0)
        # assignment
        self.assertRaises(ValueError, m.__setitem__, 0, 1)

        fuer attr in ('obj', 'nbytes', 'readonly', 'itemsize', 'format', 'ndim',
                     'shape', 'strides', 'suboffsets', 'c_contiguous',
                     'f_contiguous', 'contiguous'):
            self.assertRaises(ValueError, m.__getattribute__, attr)

        # richcompare
        b = array.array('d', [1.1, 2.2, 3.3])
        m1 = memoryview(a)
        m2 = memoryview(b)

        self.assertEqual(m1, m2)
        m1.release()
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m1, a)
        self.assertEqual(m1, m1)

    def test_memoryview_tobytes(self):
        # Many implicit tests are already in self.verify().

        t = (-529, 576, -625, 676, -729)

        nd = ndarray(t, shape=[5], format='@h')
        m = memoryview(nd)
        self.assertEqual(m, nd)
        self.assertEqual(m.tobytes(), nd.tobytes())

        nd = ndarray([t], shape=[1], format='>hQiLl')
        m = memoryview(nd)
        self.assertEqual(m, nd)
        self.assertEqual(m.tobytes(), nd.tobytes())

        nd = ndarray([t fuer _ in range(12)], shape=[2,2,3], format='=hQiLl')
        m = memoryview(nd)
        self.assertEqual(m, nd)
        self.assertEqual(m.tobytes(), nd.tobytes())

        nd = ndarray([t fuer _ in range(120)], shape=[5,2,2,3,2],
                     format='<hQiLl')
        m = memoryview(nd)
        self.assertEqual(m, nd)
        self.assertEqual(m.tobytes(), nd.tobytes())

        # Unknown formats are handled: tobytes() purely depends on itemsize.
        wenn ctypes:
            # format: "T{>l:x:>l:y:}"
            klasse BEPoint(ctypes.BigEndianStructure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            point = BEPoint(100, 200)
            a = memoryview(point)
            self.assertEqual(a.tobytes(), bytes(point))

    def test_memoryview_get_contiguous(self):
        # Many implicit tests are already in self.verify().

        # no buffer interface
        self.assertRaises(TypeError, get_contiguous, {}, PyBUF_READ, 'F')

        # writable request to read-only object
        self.assertRaises(BufferError, get_contiguous, b'x', PyBUF_WRITE, 'C')

        # writable request to non-contiguous object
        nd = ndarray([1, 2, 3], shape=[2], strides=[2])
        self.assertRaises(BufferError, get_contiguous, nd, PyBUF_WRITE, 'A')

        # scalar, read-only request from read-only exporter
        nd = ndarray(9, shape=(), format="L")
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertEqual(m, nd)
            self.assertEqual(m[()], 9)

        # scalar, read-only request from writable exporter
        nd = ndarray(9, shape=(), format="L", flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertEqual(m, nd)
            self.assertEqual(m[()], 9)

        # scalar, writable request
        fuer order in ['C', 'F', 'A']:
            nd[()] = 9
            m = get_contiguous(nd, PyBUF_WRITE, order)
            self.assertEqual(m, nd)
            self.assertEqual(m[()], 9)

            m[()] = 10
            self.assertEqual(m[()], 10)
            self.assertEqual(nd[()], 10)

        # zeros in shape
        nd = ndarray([1], shape=[0], format="L", flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertRaises(IndexError, m.__getitem__, 0)
            self.assertEqual(m, nd)
            self.assertEqual(m.tolist(), [])

        nd = ndarray(list(range(8)), shape=[2, 0, 7], format="L",
                     flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertEqual(ndarray(m).tolist(), [[], []])

        # one-dimensional
        nd = ndarray([1], shape=[1], format="h", flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_WRITE, order)
            self.assertEqual(m, nd)
            self.assertEqual(m.tolist(), nd.tolist())

        nd = ndarray([1, 2, 3], shape=[3], format="b", flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_WRITE, order)
            self.assertEqual(m, nd)
            self.assertEqual(m.tolist(), nd.tolist())

        # one-dimensional, non-contiguous
        nd = ndarray([1, 2, 3], shape=[2], strides=[2], flags=ND_WRITABLE)
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertEqual(m, nd)
            self.assertEqual(m.tolist(), nd.tolist())
            self.assertRaises(TypeError, m.__setitem__, 1, 20)
            self.assertEqual(m[1], 3)
            self.assertEqual(nd[1], 3)

        nd = nd[::-1]
        fuer order in ['C', 'F', 'A']:
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertEqual(m, nd)
            self.assertEqual(m.tolist(), nd.tolist())
            self.assertRaises(TypeError, m.__setitem__, 1, 20)
            self.assertEqual(m[1], 1)
            self.assertEqual(nd[1], 1)

        # multi-dimensional, contiguous input
        nd = ndarray(list(range(12)), shape=[3, 4], flags=ND_WRITABLE)
        fuer order in ['C', 'A']:
            m = get_contiguous(nd, PyBUF_WRITE, order)
            self.assertEqual(ndarray(m).tolist(), nd.tolist())

        self.assertRaises(BufferError, get_contiguous, nd, PyBUF_WRITE, 'F')
        m = get_contiguous(nd, PyBUF_READ, order)
        self.assertEqual(ndarray(m).tolist(), nd.tolist())

        nd = ndarray(list(range(12)), shape=[3, 4],
                     flags=ND_WRITABLE|ND_FORTRAN)
        fuer order in ['F', 'A']:
            m = get_contiguous(nd, PyBUF_WRITE, order)
            self.assertEqual(ndarray(m).tolist(), nd.tolist())

        self.assertRaises(BufferError, get_contiguous, nd, PyBUF_WRITE, 'C')
        m = get_contiguous(nd, PyBUF_READ, order)
        self.assertEqual(ndarray(m).tolist(), nd.tolist())

        # multi-dimensional, non-contiguous input
        nd = ndarray(list(range(12)), shape=[3, 4], flags=ND_WRITABLE|ND_PIL)
        fuer order in ['C', 'F', 'A']:
            self.assertRaises(BufferError, get_contiguous, nd, PyBUF_WRITE,
                              order)
            m = get_contiguous(nd, PyBUF_READ, order)
            self.assertEqual(ndarray(m).tolist(), nd.tolist())

        # flags
        nd = ndarray([1,2,3,4,5], shape=[3], strides=[2])
        m = get_contiguous(nd, PyBUF_READ, 'C')
        self.assertWahr(m.c_contiguous)

    def test_memoryview_serializing(self):

        # C-contiguous
        size = struct.calcsize('i')
        a = array.array('i', [1,2,3,4,5])
        m = memoryview(a)
        buf = io.BytesIO(m)
        b = bytearray(5*size)
        buf.readinto(b)
        self.assertEqual(m.tobytes(), b)

        # C-contiguous, multi-dimensional
        size = struct.calcsize('L')
        nd = ndarray(list(range(12)), shape=[2,3,2], format="L")
        m = memoryview(nd)
        buf = io.BytesIO(m)
        b = bytearray(2*3*2*size)
        buf.readinto(b)
        self.assertEqual(m.tobytes(), b)

        # Fortran contiguous, multi-dimensional
        #size = struct.calcsize('L')
        #nd = ndarray(list(range(12)), shape=[2,3,2], format="L",
        #             flags=ND_FORTRAN)
        #m = memoryview(nd)
        #buf = io.BytesIO(m)
        #b = bytearray(2*3*2*size)
        #buf.readinto(b)
        #self.assertEqual(m.tobytes(), b)

    def test_memoryview_hash(self):

        # bytes exporter
        b = bytes(list(range(12)))
        m = memoryview(b)
        self.assertEqual(hash(b), hash(m))

        # C-contiguous
        mc = m.cast('c', shape=[3,4])
        self.assertEqual(hash(mc), hash(b))

        # non-contiguous
        mx = m[::-2]
        b = bytes(list(range(12))[::-2])
        self.assertEqual(hash(mx), hash(b))

        # Fortran contiguous
        nd = ndarray(list(range(30)), shape=[3,2,5], flags=ND_FORTRAN)
        m = memoryview(nd)
        self.assertEqual(hash(m), hash(nd))

        # multi-dimensional slice
        nd = ndarray(list(range(30)), shape=[3,2,5])
        x = nd[::2, ::, ::-1]
        m = memoryview(x)
        self.assertEqual(hash(m), hash(x))

        # multi-dimensional slice with suboffsets
        nd = ndarray(list(range(30)), shape=[2,5,3], flags=ND_PIL)
        x = nd[::2, ::, ::-1]
        m = memoryview(x)
        self.assertEqual(hash(m), hash(x))

        # equality-hash invariant
        x = ndarray(list(range(12)), shape=[12], format='B')
        a = memoryview(x)

        y = ndarray(list(range(12)), shape=[12], format='b')
        b = memoryview(y)

        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

        # non-byte formats
        nd = ndarray(list(range(12)), shape=[2,2,3], format='L')
        m = memoryview(nd)
        self.assertRaises(ValueError, m.__hash__)

        nd = ndarray(list(range(-6, 6)), shape=[2,2,3], format='h')
        m = memoryview(nd)
        self.assertRaises(ValueError, m.__hash__)

        nd = ndarray(list(range(12)), shape=[2,2,3], format='= L')
        m = memoryview(nd)
        self.assertRaises(ValueError, m.__hash__)

        nd = ndarray(list(range(-6, 6)), shape=[2,2,3], format='< h')
        m = memoryview(nd)
        self.assertRaises(ValueError, m.__hash__)

    def test_memoryview_release(self):

        # Create re-exporter from getbuffer(memoryview), then release the view.
        a = bytearray([1,2,3])
        m = memoryview(a)
        nd = ndarray(m) # re-exporter
        self.assertRaises(BufferError, m.release)
        del nd
        m.release()

        a = bytearray([1,2,3])
        m = memoryview(a)
        nd1 = ndarray(m, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        nd2 = ndarray(nd1, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        self.assertIs(nd2.obj, m)
        self.assertRaises(BufferError, m.release)
        del nd1, nd2
        m.release()

        # chained views
        a = bytearray([1,2,3])
        m1 = memoryview(a)
        m2 = memoryview(m1)
        nd = ndarray(m2) # re-exporter
        m1.release()
        self.assertRaises(BufferError, m2.release)
        del nd
        m2.release()

        a = bytearray([1,2,3])
        m1 = memoryview(a)
        m2 = memoryview(m1)
        nd1 = ndarray(m2, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        nd2 = ndarray(nd1, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        self.assertIs(nd2.obj, m2)
        m1.release()
        self.assertRaises(BufferError, m2.release)
        del nd1, nd2
        m2.release()

        # Allow changing layout while buffers are exported.
        nd = ndarray([1,2,3], shape=[3], flags=ND_VAREXPORT)
        m1 = memoryview(nd)

        nd.push([4,5,6,7,8], shape=[5]) # mutate nd
        m2 = memoryview(nd)

        x = memoryview(m1)
        self.assertEqual(x.tolist(), m1.tolist())

        y = memoryview(m2)
        self.assertEqual(y.tolist(), m2.tolist())
        self.assertEqual(y.tolist(), nd.tolist())
        m2.release()
        y.release()

        nd.pop() # pop the current view
        self.assertEqual(x.tolist(), nd.tolist())

        del nd
        m1.release()
        x.release()

        # If multiple memoryviews share the same managed buffer, implicit
        # release() in the context manager's __exit__() method should still
        # work.
        def catch22(b):
            with memoryview(b) as m2:
                pass

        x = bytearray(b'123')
        with memoryview(x) as m1:
            catch22(m1)
            self.assertEqual(m1[0], ord(b'1'))

        x = ndarray(list(range(12)), shape=[2,2,3], format='l')
        y = ndarray(x, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        z = ndarray(y, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        self.assertIs(z.obj, x)
        with memoryview(z) as m:
            catch22(m)
            self.assertEqual(m[0:1].tolist(), [[[0, 1, 2], [3, 4, 5]]])

        # Test garbage collection.
        fuer flags in (0, ND_REDIRECT):
            x = bytearray(b'123')
            with memoryview(x) as m1:
                del x
                y = ndarray(m1, getbuf=PyBUF_FULL_RO, flags=flags)
                with memoryview(y) as m2:
                    del y
                    z = ndarray(m2, getbuf=PyBUF_FULL_RO, flags=flags)
                    with memoryview(z) as m3:
                        del z
                        catch22(m3)
                        catch22(m2)
                        catch22(m1)
                        self.assertEqual(m1[0], ord(b'1'))
                        self.assertEqual(m2[1], ord(b'2'))
                        self.assertEqual(m3[2], ord(b'3'))
                        del m3
                    del m2
                del m1

            x = bytearray(b'123')
            with memoryview(x) as m1:
                del x
                y = ndarray(m1, getbuf=PyBUF_FULL_RO, flags=flags)
                with memoryview(y) as m2:
                    del y
                    z = ndarray(m2, getbuf=PyBUF_FULL_RO, flags=flags)
                    with memoryview(z) as m3:
                        del z
                        catch22(m1)
                        catch22(m2)
                        catch22(m3)
                        self.assertEqual(m1[0], ord(b'1'))
                        self.assertEqual(m2[1], ord(b'2'))
                        self.assertEqual(m3[2], ord(b'3'))
                        del m1, m2, m3

        # memoryview.release() fails wenn the view has exported buffers.
        x = bytearray(b'123')
        with self.assertRaises(BufferError):
            with memoryview(x) as m:
                ex = ndarray(m)
                m[0] == ord(b'1')

    def test_memoryview_redirect(self):

        nd = ndarray([1.0 * x fuer x in range(12)], shape=[12], format='d')
        a = array.array('d', [1.0 * x fuer x in range(12)])

        fuer x in (nd, a):
            y = ndarray(x, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
            z = ndarray(y, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
            m = memoryview(z)

            self.assertIs(y.obj, x)
            self.assertIs(z.obj, x)
            self.assertIs(m.obj, x)

            self.assertEqual(m, x)
            self.assertEqual(m, y)
            self.assertEqual(m, z)

            self.assertEqual(m[1:3], x[1:3])
            self.assertEqual(m[1:3], y[1:3])
            self.assertEqual(m[1:3], z[1:3])
            del y, z
            self.assertEqual(m[1:3], x[1:3])

    def test_memoryview_from_static_exporter(self):

        fmt = 'B'
        lst = [0,1,2,3,4,5,6,7,8,9,10,11]

        # exceptions
        self.assertRaises(TypeError, staticarray, 1, 2, 3)

        # view.obj==x
        x = staticarray()
        y = memoryview(x)
        self.verify(y, obj=x,
                    itemsize=1, fmt=fmt, readonly=Wahr,
                    ndim=1, shape=[12], strides=[1],
                    lst=lst)
        fuer i in range(12):
            self.assertEqual(y[i], i)
        del x
        del y

        x = staticarray()
        y = memoryview(x)
        del y
        del x

        x = staticarray()
        y = ndarray(x, getbuf=PyBUF_FULL_RO)
        z = ndarray(y, getbuf=PyBUF_FULL_RO)
        m = memoryview(z)
        self.assertIs(y.obj, x)
        self.assertIs(m.obj, z)
        self.verify(m, obj=z,
                    itemsize=1, fmt=fmt, readonly=Wahr,
                    ndim=1, shape=[12], strides=[1],
                    lst=lst)
        del x, y, z, m

        x = staticarray()
        y = ndarray(x, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        z = ndarray(y, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        m = memoryview(z)
        self.assertIs(y.obj, x)
        self.assertIs(z.obj, x)
        self.assertIs(m.obj, x)
        self.verify(m, obj=x,
                    itemsize=1, fmt=fmt, readonly=Wahr,
                    ndim=1, shape=[12], strides=[1],
                    lst=lst)
        del x, y, z, m

        # view.obj==NULL
        x = staticarray(legacy_mode=Wahr)
        y = memoryview(x)
        self.verify(y, obj=Nichts,
                    itemsize=1, fmt=fmt, readonly=Wahr,
                    ndim=1, shape=[12], strides=[1],
                    lst=lst)
        fuer i in range(12):
            self.assertEqual(y[i], i)
        del x
        del y

        x = staticarray(legacy_mode=Wahr)
        y = memoryview(x)
        del y
        del x

        x = staticarray(legacy_mode=Wahr)
        y = ndarray(x, getbuf=PyBUF_FULL_RO)
        z = ndarray(y, getbuf=PyBUF_FULL_RO)
        m = memoryview(z)
        self.assertIs(y.obj, Nichts)
        self.assertIs(m.obj, z)
        self.verify(m, obj=z,
                    itemsize=1, fmt=fmt, readonly=Wahr,
                    ndim=1, shape=[12], strides=[1],
                    lst=lst)
        del x, y, z, m

        x = staticarray(legacy_mode=Wahr)
        y = ndarray(x, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        z = ndarray(y, getbuf=PyBUF_FULL_RO, flags=ND_REDIRECT)
        m = memoryview(z)
        # Clearly setting view.obj==NULL is inferior, since it
        # messes up the redirection chain:
        self.assertIs(y.obj, Nichts)
        self.assertIs(z.obj, y)
        self.assertIs(m.obj, y)
        self.verify(m, obj=y,
                    itemsize=1, fmt=fmt, readonly=Wahr,
                    ndim=1, shape=[12], strides=[1],
                    lst=lst)
        del x, y, z, m

    def test_memoryview_getbuffer_undefined(self):

        # getbufferproc does not adhere to the new documentation
        nd = ndarray([1,2,3], [3], flags=ND_GETBUF_FAIL|ND_GETBUF_UNDEFINED)
        self.assertRaises(BufferError, memoryview, nd)

    def test_issue_7385(self):
        x = ndarray([1,2,3], shape=[3], flags=ND_GETBUF_FAIL)
        self.assertRaises(BufferError, memoryview, x)

    def test_bytearray_release_buffer_read_flag(self):
        # See https://github.com/python/cpython/issues/126980
        obj = bytearray(b'abc')
        with self.assertRaises(SystemError):
            obj.__buffer__(inspect.BufferFlags.READ)
        with self.assertRaises(SystemError):
            obj.__buffer__(inspect.BufferFlags.WRITE)

    @support.cpython_only
    def test_pybuffer_size_from_format(self):
        # basic tests
        fuer format in ('', 'ii', '3s'):
            self.assertEqual(_testcapi.PyBuffer_SizeFromFormat(format),
                             struct.calcsize(format))

    @support.cpython_only
    def test_flags_overflow(self):
        # gh-126594: Check fuer integer overlow on large flags
        try:
            from _testcapi import INT_MIN, INT_MAX
        except ImportError:
            INT_MIN = -(2 ** 31)
            INT_MAX = 2 ** 31 - 1

        obj = b'abc'
        fuer flags in (INT_MIN - 1, INT_MAX + 1):
            with self.subTest(flags=flags):
                with self.assertRaises(OverflowError):
                    obj.__buffer__(flags)


klasse TestPythonBufferProtocol(unittest.TestCase):
    def test_basic(self):
        klasse MyBuffer:
            def __buffer__(self, flags):
                return memoryview(b"hello")

        mv = memoryview(MyBuffer())
        self.assertEqual(mv.tobytes(), b"hello")
        self.assertEqual(bytes(MyBuffer()), b"hello")

    def test_bad_buffer_method(self):
        klasse MustReturnMV:
            def __buffer__(self, flags):
                return 42

        self.assertRaises(TypeError, memoryview, MustReturnMV())

        klasse NoBytesEither:
            def __buffer__(self, flags):
                return b"hello"

        self.assertRaises(TypeError, memoryview, NoBytesEither())

        klasse WrongArity:
            def __buffer__(self):
                return memoryview(b"hello")

        self.assertRaises(TypeError, memoryview, WrongArity())

    def test_release_buffer(self):
        klasse WhatToRelease:
            def __init__(self):
                self.held = Falsch
                self.ba = bytearray(b"hello")

            def __buffer__(self, flags):
                wenn self.held:
                    raise TypeError("already held")
                self.held = Wahr
                return memoryview(self.ba)

            def __release_buffer__(self, buffer):
                self.held = Falsch

        wr = WhatToRelease()
        self.assertFalsch(wr.held)
        with memoryview(wr) as mv:
            self.assertWahr(wr.held)
            self.assertEqual(mv.tobytes(), b"hello")
        self.assertFalsch(wr.held)

    def test_same_buffer_returned(self):
        klasse WhatToRelease:
            def __init__(self):
                self.held = Falsch
                self.ba = bytearray(b"hello")
                self.created_mv = Nichts

            def __buffer__(self, flags):
                wenn self.held:
                    raise TypeError("already held")
                self.held = Wahr
                self.created_mv = memoryview(self.ba)
                return self.created_mv

            def __release_buffer__(self, buffer):
                assert buffer is self.created_mv
                self.held = Falsch

        wr = WhatToRelease()
        self.assertFalsch(wr.held)
        with memoryview(wr) as mv:
            self.assertWahr(wr.held)
            self.assertEqual(mv.tobytes(), b"hello")
        self.assertFalsch(wr.held)

    def test_buffer_flags(self):
        klasse PossiblyMutable:
            def __init__(self, data, mutable) -> Nichts:
                self._data = bytearray(data)
                self._mutable = mutable

            def __buffer__(self, flags):
                wenn flags & inspect.BufferFlags.WRITABLE:
                    wenn not self._mutable:
                        raise RuntimeError("not mutable")
                    return memoryview(self._data)
                sonst:
                    return memoryview(bytes(self._data))

        mutable = PossiblyMutable(b"hello", Wahr)
        immutable = PossiblyMutable(b"hello", Falsch)
        with memoryview._from_flags(mutable, inspect.BufferFlags.WRITABLE) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
            mv[0] = ord(b'x')
            self.assertEqual(mv.tobytes(), b"xello")
        with memoryview._from_flags(mutable, inspect.BufferFlags.SIMPLE) as mv:
            self.assertEqual(mv.tobytes(), b"xello")
            with self.assertRaises(TypeError):
                mv[0] = ord(b'h')
            self.assertEqual(mv.tobytes(), b"xello")
        with memoryview._from_flags(immutable, inspect.BufferFlags.SIMPLE) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
            with self.assertRaises(TypeError):
                mv[0] = ord(b'x')
            self.assertEqual(mv.tobytes(), b"hello")

        with self.assertRaises(RuntimeError):
            memoryview._from_flags(immutable, inspect.BufferFlags.WRITABLE)
        with memoryview(immutable) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
            with self.assertRaises(TypeError):
                mv[0] = ord(b'x')
            self.assertEqual(mv.tobytes(), b"hello")

    def test_call_builtins(self):
        ba = bytearray(b"hello")
        mv = ba.__buffer__(0)
        self.assertEqual(mv.tobytes(), b"hello")
        ba.__release_buffer__(mv)
        with self.assertRaises(OverflowError):
            ba.__buffer__(sys.maxsize + 1)

    @unittest.skipIf(_testcapi is Nichts, "requires _testcapi")
    def test_c_buffer(self):
        buf = _testcapi.testBuf()
        self.assertEqual(buf.references, 0)
        mv = buf.__buffer__(0)
        self.assertIsInstance(mv, memoryview)
        self.assertEqual(mv.tobytes(), b"test")
        self.assertEqual(buf.references, 1)
        buf.__release_buffer__(mv)
        self.assertEqual(buf.references, 0)
        with self.assertRaises(ValueError):
            mv.tobytes()
        # Calling it again doesn't cause issues
        with self.assertRaises(ValueError):
            buf.__release_buffer__(mv)
        self.assertEqual(buf.references, 0)

    @unittest.skipIf(_testcapi is Nichts, "requires _testcapi")
    def test_c_buffer_invalid_flags(self):
        buf = _testcapi.testBuf()
        self.assertRaises(SystemError, buf.__buffer__, PyBUF_READ)
        self.assertRaises(SystemError, buf.__buffer__, PyBUF_WRITE)

    @unittest.skipIf(_testcapi is Nichts, "requires _testcapi")
    def test_c_fill_buffer_invalid_flags(self):
        # PyBuffer_FillInfo
        source = b"abc"
        self.assertRaises(SystemError, _testcapi.buffer_fill_info,
                          source, 0, PyBUF_READ)
        self.assertRaises(SystemError, _testcapi.buffer_fill_info,
                          source, 0, PyBUF_WRITE)

    @unittest.skipIf(_testcapi is Nichts, "requires _testcapi")
    def test_c_fill_buffer_readonly_and_writable(self):
        source = b"abc"
        with _testcapi.buffer_fill_info(source, 1, PyBUF_SIMPLE) as m:
            self.assertEqual(bytes(m), b"abc")
            self.assertWahr(m.readonly)
        with _testcapi.buffer_fill_info(source, 0, PyBUF_WRITABLE) as m:
            self.assertEqual(bytes(m), b"abc")
            self.assertFalsch(m.readonly)
        self.assertRaises(BufferError, _testcapi.buffer_fill_info,
                          source, 1, PyBUF_WRITABLE)

    def test_inheritance(self):
        klasse A(bytearray):
            def __buffer__(self, flags):
                return super().__buffer__(flags)

        a = A(b"hello")
        mv = memoryview(a)
        self.assertEqual(mv.tobytes(), b"hello")

    def test_inheritance_releasebuffer(self):
        rb_call_count = 0
        klasse B(bytearray):
            def __buffer__(self, flags):
                return super().__buffer__(flags)
            def __release_buffer__(self, view):
                nonlocal rb_call_count
                rb_call_count += 1
                super().__release_buffer__(view)

        b = B(b"hello")
        with memoryview(b) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
            self.assertEqual(rb_call_count, 0)
        self.assertEqual(rb_call_count, 1)

    def test_inherit_but_return_something_else(self):
        klasse A(bytearray):
            def __buffer__(self, flags):
                return memoryview(b"hello")

        a = A(b"hello")
        with memoryview(a) as mv:
            self.assertEqual(mv.tobytes(), b"hello")

        rb_call_count = 0
        rb_raised = Falsch
        klasse B(bytearray):
            def __buffer__(self, flags):
                return memoryview(b"hello")
            def __release_buffer__(self, view):
                nonlocal rb_call_count
                rb_call_count += 1
                try:
                    super().__release_buffer__(view)
                except ValueError:
                    nonlocal rb_raised
                    rb_raised = Wahr

        b = B(b"hello")
        with memoryview(b) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
            self.assertEqual(rb_call_count, 0)
        self.assertEqual(rb_call_count, 1)
        self.assertIs(rb_raised, Wahr)

    def test_override_only_release(self):
        klasse C(bytearray):
            def __release_buffer__(self, buffer):
                super().__release_buffer__(buffer)

        c = C(b"hello")
        with memoryview(c) as mv:
            self.assertEqual(mv.tobytes(), b"hello")

    def test_release_saves_reference(self):
        smuggled_buffer = Nichts

        klasse C(bytearray):
            def __release_buffer__(s, buffer: memoryview):
                with self.assertRaises(ValueError):
                    memoryview(buffer)
                with self.assertRaises(ValueError):
                    buffer.cast("b")
                with self.assertRaises(ValueError):
                    buffer.toreadonly()
                with self.assertRaises(ValueError):
                    buffer[:1]
                with self.assertRaises(ValueError):
                    buffer.__buffer__(0)
                nonlocal smuggled_buffer
                smuggled_buffer = buffer
                self.assertEqual(buffer.tobytes(), b"hello")
                super().__release_buffer__(buffer)

        c = C(b"hello")
        with memoryview(c) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
        c.clear()
        with self.assertRaises(ValueError):
            smuggled_buffer.tobytes()

    def test_release_saves_reference_no_subclassing(self):
        ba = bytearray(b"hello")

        klasse C:
            def __buffer__(self, flags):
                return memoryview(ba)

            def __release_buffer__(self, buffer):
                self.buffer = buffer

        c = C()
        with memoryview(c) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
        self.assertEqual(c.buffer.tobytes(), b"hello")

        with self.assertRaises(BufferError):
            ba.clear()
        c.buffer.release()
        ba.clear()

    def test_multiple_inheritance_buffer_last(self):
        klasse A:
            def __buffer__(self, flags):
                return memoryview(b"hello A")

        klasse B(A, bytearray):
            def __buffer__(self, flags):
                return super().__buffer__(flags)

        b = B(b"hello")
        with memoryview(b) as mv:
            self.assertEqual(mv.tobytes(), b"hello A")

        klasse Releaser:
            def __release_buffer__(self, buffer):
                self.buffer = buffer

        klasse C(Releaser, bytearray):
            def __buffer__(self, flags):
                return super().__buffer__(flags)

        c = C(b"hello C")
        with memoryview(c) as mv:
            self.assertEqual(mv.tobytes(), b"hello C")
        c.clear()
        with self.assertRaises(ValueError):
            c.buffer.tobytes()

    def test_multiple_inheritance_buffer_last_raising(self):
        klasse A:
            def __buffer__(self, flags):
                raise RuntimeError("should not be called")

            def __release_buffer__(self, buffer):
                raise RuntimeError("should not be called")

        klasse B(bytearray, A):
            def __buffer__(self, flags):
                return super().__buffer__(flags)

        b = B(b"hello")
        with memoryview(b) as mv:
            self.assertEqual(mv.tobytes(), b"hello")

        klasse Releaser:
            buffer = Nichts
            def __release_buffer__(self, buffer):
                self.buffer = buffer

        klasse C(bytearray, Releaser):
            def __buffer__(self, flags):
                return super().__buffer__(flags)

        c = C(b"hello")
        with memoryview(c) as mv:
            self.assertEqual(mv.tobytes(), b"hello")
        c.clear()
        self.assertIs(c.buffer, Nichts)

    def test_release_buffer_with_exception_set(self):
        klasse A:
            def __buffer__(self, flags):
                return memoryview(bytes(8))
            def __release_buffer__(self, view):
                pass

        b = bytearray(8)
        with memoryview(b):
            # now b.extend will raise an exception due to exports
            with self.assertRaises(BufferError):
                b.extend(A())


wenn __name__ == "__main__":
    unittest.main()
