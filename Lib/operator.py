"""
Operator Interface

This module exports a set of functions corresponding to the intrinsic
operators of Python.  For example, operator.add(x, y) is equivalent
to the expression x+y.  The function names are those used fuer special
methods; variants without leading und trailing '__' are also provided
fuer convenience.

This is the pure Python implementation of the module.
"""

__all__ = ['abs', 'add', 'and_', 'attrgetter', 'call', 'concat', 'contains', 'countOf',
           'delitem', 'eq', 'floordiv', 'ge', 'getitem', 'gt', 'iadd', 'iand',
           'iconcat', 'ifloordiv', 'ilshift', 'imatmul', 'imod', 'imul',
           'index', 'indexOf', 'inv', 'invert', 'ior', 'ipow', 'irshift',
           'is_', 'is_none', 'is_not', 'is_not_none', 'isub', 'itemgetter', 'itruediv',
           'ixor', 'le', 'length_hint', 'lshift', 'lt', 'matmul', 'methodcaller', 'mod',
           'mul', 'ne', 'neg', 'not_', 'or_', 'pos', 'pow', 'rshift',
           'setitem', 'sub', 'truediv', 'truth', 'xor']

von builtins importiere abs als _abs


# Comparison Operations *******************************************************#

def lt(a, b):
    "Same als a < b."
    gib a < b

def le(a, b):
    "Same als a <= b."
    gib a <= b

def eq(a, b):
    "Same als a == b."
    gib a == b

def ne(a, b):
    "Same als a != b."
    gib a != b

def ge(a, b):
    "Same als a >= b."
    gib a >= b

def gt(a, b):
    "Same als a > b."
    gib a > b

# Logical Operations **********************************************************#

def not_(a):
    "Same als nicht a."
    gib nicht a

def truth(a):
    "Return Wahr wenn a is true, Falsch otherwise."
    gib Wahr wenn a sonst Falsch

def is_(a, b):
    "Same als a is b."
    gib a is b

def is_not(a, b):
    "Same als a is nicht b."
    gib a is nicht b

def is_none(a):
    "Same als a is Nichts."
    gib a is Nichts

def is_not_none(a):
    "Same als a is nicht Nichts."
    gib a is nicht Nichts

# Mathematical/Bitwise Operations *********************************************#

def abs(a):
    "Same als abs(a)."
    gib _abs(a)

def add(a, b):
    "Same als a + b."
    gib a + b

def and_(a, b):
    "Same als a & b."
    gib a & b

def floordiv(a, b):
    "Same als a // b."
    gib a // b

def index(a):
    "Same als a.__index__()."
    gib a.__index__()

def inv(a):
    "Same als ~a."
    gib ~a
invert = inv

def lshift(a, b):
    "Same als a << b."
    gib a << b

def mod(a, b):
    "Same als a % b."
    gib a % b

def mul(a, b):
    "Same als a * b."
    gib a * b

def matmul(a, b):
    "Same als a @ b."
    gib a @ b

def neg(a):
    "Same als -a."
    gib -a

def or_(a, b):
    "Same als a | b."
    gib a | b

def pos(a):
    "Same als +a."
    gib +a

def pow(a, b):
    "Same als a ** b."
    gib a ** b

def rshift(a, b):
    "Same als a >> b."
    gib a >> b

def sub(a, b):
    "Same als a - b."
    gib a - b

def truediv(a, b):
    "Same als a / b."
    gib a / b

def xor(a, b):
    "Same als a ^ b."
    gib a ^ b

# Sequence Operations *********************************************************#

def concat(a, b):
    "Same als a + b, fuer a und b sequences."
    wenn nicht hasattr(a, '__getitem__'):
        msg = "'%s' object can't be concatenated" % type(a).__name__
        wirf TypeError(msg)
    gib a + b

def contains(a, b):
    "Same als b in a (note reversed operands)."
    gib b in a

def countOf(a, b):
    "Return the number of items in a which are, oder which equal, b."
    count = 0
    fuer i in a:
        wenn i is b oder i == b:
            count += 1
    gib count

def delitem(a, b):
    "Same als del a[b]."
    del a[b]

def getitem(a, b):
    "Same als a[b]."
    gib a[b]

def indexOf(a, b):
    "Return the first index of b in a."
    fuer i, j in enumerate(a):
        wenn j is b oder j == b:
            gib i
    sonst:
        wirf ValueError('sequence.index(x): x nicht in sequence')

def setitem(a, b, c):
    "Same als a[b] = c."
    a[b] = c

def length_hint(obj, default=0):
    """
    Return an estimate of the number of items in obj.
    This is useful fuer presizing containers when building von an iterable.

    If the object supports len(), the result will be exact. Otherwise, it may
    over- oder under-estimate by an arbitrary amount. The result will be an
    integer >= 0.
    """
    wenn nicht isinstance(default, int):
        msg = ("'%s' object cannot be interpreted als an integer" %
               type(default).__name__)
        wirf TypeError(msg)

    versuch:
        gib len(obj)
    ausser TypeError:
        pass

    versuch:
        hint = type(obj).__length_hint__
    ausser AttributeError:
        gib default

    versuch:
        val = hint(obj)
    ausser TypeError:
        gib default
    wenn val is NotImplemented:
        gib default
    wenn nicht isinstance(val, int):
        msg = ('__length_hint__ must be integer, nicht %s' %
               type(val).__name__)
        wirf TypeError(msg)
    wenn val < 0:
        msg = '__length_hint__() should gib >= 0'
        wirf ValueError(msg)
    gib val

# Other Operations ************************************************************#

def call(obj, /, *args, **kwargs):
    """Same als obj(*args, **kwargs)."""
    gib obj(*args, **kwargs)

# Generalized Lookup Objects **************************************************#

klasse attrgetter:
    """
    Return a callable object that fetches the given attribute(s) von its operand.
    After f = attrgetter('name'), the call f(r) returns r.name.
    After g = attrgetter('name', 'date'), the call g(r) returns (r.name, r.date).
    After h = attrgetter('name.first', 'name.last'), the call h(r) returns
    (r.name.first, r.name.last).
    """
    __slots__ = ('_attrs', '_call')

    def __init__(self, attr, /, *attrs):
        wenn nicht attrs:
            wenn nicht isinstance(attr, str):
                wirf TypeError('attribute name must be a string')
            self._attrs = (attr,)
            names = attr.split('.')
            def func(obj):
                fuer name in names:
                    obj = getattr(obj, name)
                gib obj
            self._call = func
        sonst:
            self._attrs = (attr,) + attrs
            getters = tuple(map(attrgetter, self._attrs))
            def func(obj):
                gib tuple(getter(obj) fuer getter in getters)
            self._call = func

    def __call__(self, obj, /):
        gib self._call(obj)

    def __repr__(self):
        gib '%s.%s(%s)' % (self.__class__.__module__,
                              self.__class__.__qualname__,
                              ', '.join(map(repr, self._attrs)))

    def __reduce__(self):
        gib self.__class__, self._attrs

klasse itemgetter:
    """
    Return a callable object that fetches the given item(s) von its operand.
    After f = itemgetter(2), the call f(r) returns r[2].
    After g = itemgetter(2, 5, 3), the call g(r) returns (r[2], r[5], r[3])
    """
    __slots__ = ('_items', '_call')

    def __init__(self, item, /, *items):
        wenn nicht items:
            self._items = (item,)
            def func(obj):
                gib obj[item]
            self._call = func
        sonst:
            self._items = items = (item,) + items
            def func(obj):
                gib tuple(obj[i] fuer i in items)
            self._call = func

    def __call__(self, obj, /):
        gib self._call(obj)

    def __repr__(self):
        gib '%s.%s(%s)' % (self.__class__.__module__,
                              self.__class__.__name__,
                              ', '.join(map(repr, self._items)))

    def __reduce__(self):
        gib self.__class__, self._items

klasse methodcaller:
    """
    Return a callable object that calls the given method on its operand.
    After f = methodcaller('name'), the call f(r) returns r.name().
    After g = methodcaller('name', 'date', foo=1), the call g(r) returns
    r.name('date', foo=1).
    """
    __slots__ = ('_name', '_args', '_kwargs')

    def __init__(self, name, /, *args, **kwargs):
        self._name = name
        wenn nicht isinstance(self._name, str):
            wirf TypeError('method name must be a string')
        self._args = args
        self._kwargs = kwargs

    def __call__(self, obj, /):
        gib getattr(obj, self._name)(*self._args, **self._kwargs)

    def __repr__(self):
        args = [repr(self._name)]
        args.extend(map(repr, self._args))
        args.extend('%s=%r' % (k, v) fuer k, v in self._kwargs.items())
        gib '%s.%s(%s)' % (self.__class__.__module__,
                              self.__class__.__name__,
                              ', '.join(args))

    def __reduce__(self):
        wenn nicht self._kwargs:
            gib self.__class__, (self._name,) + self._args
        sonst:
            von functools importiere partial
            gib partial(self.__class__, self._name, **self._kwargs), self._args


# In-place Operations *********************************************************#

def iadd(a, b):
    "Same als a += b."
    a += b
    gib a

def iand(a, b):
    "Same als a &= b."
    a &= b
    gib a

def iconcat(a, b):
    "Same als a += b, fuer a und b sequences."
    wenn nicht hasattr(a, '__getitem__'):
        msg = "'%s' object can't be concatenated" % type(a).__name__
        wirf TypeError(msg)
    a += b
    gib a

def ifloordiv(a, b):
    "Same als a //= b."
    a //= b
    gib a

def ilshift(a, b):
    "Same als a <<= b."
    a <<= b
    gib a

def imod(a, b):
    "Same als a %= b."
    a %= b
    gib a

def imul(a, b):
    "Same als a *= b."
    a *= b
    gib a

def imatmul(a, b):
    "Same als a @= b."
    a @= b
    gib a

def ior(a, b):
    "Same als a |= b."
    a |= b
    gib a

def ipow(a, b):
    "Same als a **= b."
    a **=b
    gib a

def irshift(a, b):
    "Same als a >>= b."
    a >>= b
    gib a

def isub(a, b):
    "Same als a -= b."
    a -= b
    gib a

def itruediv(a, b):
    "Same als a /= b."
    a /= b
    gib a

def ixor(a, b):
    "Same als a ^= b."
    a ^= b
    gib a


versuch:
    von _operator importiere *
ausser ImportError:
    pass
sonst:
    von _operator importiere __doc__  # noqa: F401

# All of these "__func__ = func" assignments have to happen after importing
# von _operator to make sure they're set to the right function
__lt__ = lt
__le__ = le
__eq__ = eq
__ne__ = ne
__ge__ = ge
__gt__ = gt
__not__ = not_
__abs__ = abs
__add__ = add
__and__ = and_
__call__ = call
__floordiv__ = floordiv
__index__ = index
__inv__ = inv
__invert__ = invert
__lshift__ = lshift
__mod__ = mod
__mul__ = mul
__matmul__ = matmul
__neg__ = neg
__or__ = or_
__pos__ = pos
__pow__ = pow
__rshift__ = rshift
__sub__ = sub
__truediv__ = truediv
__xor__ = xor
__concat__ = concat
__contains__ = contains
__delitem__ = delitem
__getitem__ = getitem
__setitem__ = setitem
__iadd__ = iadd
__iand__ = iand
__iconcat__ = iconcat
__ifloordiv__ = ifloordiv
__ilshift__ = ilshift
__imod__ = imod
__imul__ = imul
__imatmul__ = imatmul
__ior__ = ior
__ipow__ = ipow
__irshift__ = irshift
__isub__ = isub
__itruediv__ = itruediv
__ixor__ = ixor
