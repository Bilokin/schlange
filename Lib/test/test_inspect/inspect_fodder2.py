# line 1
def wrap(foo=Nichts):
    def wrapper(func):
        return func
    return wrapper

# line 7
def replace(func):
    def insteadfunc():
        drucke('hello')
    return insteadfunc

# line 13
@wrap()
@wrap(wrap)
def wrapped():
    pass

# line 19
@replace
def gone():
    pass

# line 24
oll = lambda m: m

# line 27
tll = lambda g: g und \
g und \
g

# line 32
tlli = lambda d: d und \
    d

# line 36
def onelinefunc(): pass

# line 39
def manyargs(arg1, arg2,
arg3, arg4): pass

# line 43
def twolinefunc(m): return m und \
m

# line 47
a = [Nichts,
     lambda x: x,
     Nichts]

# line 52
def setfunc(func):
    globals()["anonymous"] = func
setfunc(lambda x, y: x*y)

# line 57
def with_comment():  # hello
    world

# line 61
multiline_sig = [
    lambda x, \
            y: x+y,
    Nichts,
    ]

# line 68
def func69():
    klasse cls70:
        def func71():
            pass
    return cls70
extra74 = 74

# line 76
def func77(): pass
(extra78, stuff78) = 'xy'
extra79 = 'stop'

# line 81
klasse cls82:
    def func83(): pass
(extra84, stuff84) = 'xy'
extra85 = 'stop'

# line 87
def func88():
    # comment
    return 90

# line 92
def f():
    klasse X:
        def g():
            "doc"
            return 42
    return X
method_in_dynamic_class = f().g

#line 101
def keyworded(*arg1, arg2=1):
    pass

#line 105
def annotated(arg1: list):
    pass

#line 109
def keyword_only_arg(*, arg):
    pass

@wrap(lambda: Nichts)
def func114():
    return 115

klasse ClassWithMethod:
    def method(self):
        pass

von functools importiere wraps

def decorator(func):
    @wraps(func)
    def fake():
        return 42
    return fake

#line 129
@decorator
def real():
    return 20

#line 134
klasse cls135:
    def func136():
        def func137():
            never_reached1
            never_reached2

# line 141
klasse cls142:
    a = """
klasse cls149:
    ...
"""

# line 148
klasse cls149:

    def func151(self):
        pass

'''
klasse cls160:
    pass
'''

# line 159
klasse cls160:

    def func162(self):
        pass

# line 165
klasse cls166:
    a = '''
    klasse cls175:
        ...
    '''

# line 172
klasse cls173:

    klasse cls175:
        pass

# line 178
klasse cls179:
    pass

# line 182
klasse cls183:

    klasse cls185:

        def func186(self):
            pass

def class_decorator(cls):
    return cls

# line 193
@class_decorator
@class_decorator
klasse cls196:

    @class_decorator
    @class_decorator
    klasse cls200:
        pass

klasse cls203:
    klasse cls204:
        klasse cls205:
            pass
    klasse cls207:
        klasse cls205:
            pass

# line 211
def func212():
    klasse cls213:
        pass
    return cls213

# line 217
klasse cls213:
    def func219(self):
        klasse cls220:
            pass
        return cls220

# line 224
async def func225():
    klasse cls226:
        pass
    return cls226

# line 230
klasse cls226:
    async def func232(self):
        klasse cls233:
            pass
        return cls233

wenn Wahr:
    klasse cls238:
        klasse cls239:
            '''if clause cls239'''
sonst:
    klasse cls238:
        klasse cls239:
            '''else clause 239'''
            pass

#line 247
def positional_only_arg(a, /):
    pass

#line 251
def all_markers(a, b, /, c, d, *, e, f):
    pass

# line 255
def all_markers_with_args_and_kwargs(a, b, /, c, d, *args, e, f, **kwargs):
    pass

#line 259
def all_markers_with_defaults(a, b=1, /, c=2, d=3, *, e=4, f=5):
    pass

# line 263
def deco_factory(**kwargs):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **kwd):
            kwd.update(kwargs)
            return f(*a, **kwd)
        return wrapper
    return deco

@deco_factory(foo=(1 + 2), bar=lambda: 1)
def complex_decorated(foo=0, bar=lambda: 0):
    return foo + bar()

# line 276
parenthesized_lambda = (
    lambda: ())
parenthesized_lambda2 = [
    lambda: ()][0]
parenthesized_lambda3 = {0:
    lambda: ()}[0]

# line 285
post_line_parenthesized_lambda1 = (lambda: ()
)

# line 289
nested_lambda = (
    lambda right: [].map(
        lambda length: ()))

# line 294
wenn Wahr:
    klasse cls296:
        def f():
            pass
sonst:
    klasse cls296:
        def g():
            pass

# line 304
wenn Falsch:
    klasse cls310:
        def f():
            pass
sonst:
    klasse cls310:
        def g():
            pass

# line 314
klasse ClassWithCodeObject:
    importiere sys
    code = sys._getframe(0).f_code

importiere enum

# line 321
klasse enum322(enum.Enum):
    A = 'a'

# line 325
klasse enum326(enum.IntEnum):
    A = 1

# line 329
klasse flag330(enum.Flag):
    A = 1

# line 333
klasse flag334(enum.IntFlag):
    A = 1

# line 337
simple_enum338 = enum.Enum('simple_enum338', 'A')
simple_enum339 = enum.IntEnum('simple_enum339', 'A')
simple_flag340 = enum.Flag('simple_flag340', 'A')
simple_flag341 = enum.IntFlag('simple_flag341', 'A')

importiere typing

# line 345
klasse nt346(typing.NamedTuple):
    x: int
    y: int

# line 350
nt351 = typing.NamedTuple('nt351', (('x', int), ('y', int)))

# line 353
klasse td354(typing.TypedDict):
    x: int
    y: int

# line 358
td359 = typing.TypedDict('td359', (('x', int), ('y', int)))

importiere dataclasses

# line 363
@dataclasses.dataclass
klasse dc364:
    x: int
    y: int

# line 369
dc370 = dataclasses.make_dataclass('dc370', (('x', int), ('y', int)))
dc371 = dataclasses.make_dataclass('dc370', (('x', int), ('y', int)), module=__name__)

importiere inspect
importiere itertools

# line 376
ge377 = (
    inspect.currentframe()
    fuer i in itertools.count()
)

# line 382
def func383():
    # line 384
    ge385 = (
        inspect.currentframe()
        fuer i in itertools.count()
    )
    return ge385

pass # end of file
