importiere doctest
importiere unittest


doctests = """

Basic klasse construction.

    >>> klasse C:
    ...     def meth(self): drucke("Hello")
    ...
    >>> C.__class__ is type
    Wahr
    >>> a = C()
    >>> a.__class__ is C
    Wahr
    >>> a.meth()
    Hello
    >>>

Use *args notation fuer the bases.

    >>> klasse A: pass
    >>> klasse B: pass
    >>> bases = (A, B)
    >>> klasse C(*bases): pass
    >>> C.__bases__ == bases
    Wahr
    >>>

Use a trivial metaclass.

    >>> klasse M(type):
    ...     pass
    ...
    >>> klasse C(metaclass=M):
    ...    def meth(self): drucke("Hello")
    ...
    >>> C.__class__ is M
    Wahr
    >>> a = C()
    >>> a.__class__ is C
    Wahr
    >>> a.meth()
    Hello
    >>>

Use **kwds notation fuer the metaclass keyword.

    >>> kwds = {'metaclass': M}
    >>> klasse C(**kwds): pass
    ...
    >>> C.__class__ is M
    Wahr
    >>> a = C()
    >>> a.__class__ is C
    Wahr
    >>>

Use a metaclass mit a __prepare__ static method.

    >>> klasse M(type):
    ...    @staticmethod
    ...    def __prepare__(*args, **kwds):
    ...        drucke("Prepare called:", args, kwds)
    ...        gib dict()
    ...    def __new__(cls, name, bases, namespace, **kwds):
    ...        drucke("New called:", kwds)
    ...        gib type.__new__(cls, name, bases, namespace)
    ...    def __init__(cls, *args, **kwds):
    ...        pass
    ...
    >>> klasse C(metaclass=M):
    ...     def meth(self): drucke("Hello")
    ...
    Prepare called: ('C', ()) {}
    New called: {}
    >>>

Also pass another keyword.

    >>> klasse C(object, metaclass=M, other="haha"):
    ...     pass
    ...
    Prepare called: ('C', (<class 'object'>,)) {'other': 'haha'}
    New called: {'other': 'haha'}
    >>> C.__class__ is M
    Wahr
    >>> C.__bases__ == (object,)
    Wahr
    >>> a = C()
    >>> a.__class__ is C
    Wahr
    >>>

Check that build_class doesn't mutate the kwds dict.

    >>> kwds = {'metaclass': type}
    >>> klasse C(**kwds): pass
    ...
    >>> kwds == {'metaclass': type}
    Wahr
    >>>

Use various combinations of explicit keywords und **kwds.

    >>> bases = (object,)
    >>> kwds = {'metaclass': M, 'other': 'haha'}
    >>> klasse C(*bases, **kwds): pass
    ...
    Prepare called: ('C', (<class 'object'>,)) {'other': 'haha'}
    New called: {'other': 'haha'}
    >>> C.__class__ is M
    Wahr
    >>> C.__bases__ == (object,)
    Wahr
    >>> klasse B: pass
    >>> kwds = {'other': 'haha'}
    >>> klasse C(B, metaclass=M, *bases, **kwds): pass
    ...
    Prepare called: ('C', (<class 'test.test_metaclass.B'>, <class 'object'>)) {'other': 'haha'}
    New called: {'other': 'haha'}
    >>> C.__class__ is M
    Wahr
    >>> C.__bases__ == (B, object)
    Wahr
    >>>

Check fuer duplicate keywords.

    >>> klasse C(metaclass=type, metaclass=type): pass
    ...
    Traceback (most recent call last):
    [...]
    SyntaxError: keyword argument repeated: metaclass
    >>>

Another way.

    >>> kwds = {'metaclass': type}
    >>> klasse C(metaclass=type, **kwds): pass
    ...
    Traceback (most recent call last):
    [...]
    TypeError: __build_class__() got multiple values fuer keyword argument 'metaclass'
    >>>

Use a __prepare__ method that returns an instrumented dict.

    >>> klasse LoggingDict(dict):
    ...     def __setitem__(self, key, value):
    ...         drucke("d[%r] = %r" % (key, value))
    ...         dict.__setitem__(self, key, value)
    ...
    >>> klasse Meta(type):
    ...    @staticmethod
    ...    def __prepare__(name, bases):
    ...        gib LoggingDict()
    ...
    >>> klasse C(metaclass=Meta):
    ...     foo = 2+2
    ...     foo = 42
    ...     bar = 123
    ...
    d['__module__'] = 'test.test_metaclass'
    d['__qualname__'] = 'C'
    d['__firstlineno__'] = 1
    d['foo'] = 4
    d['foo'] = 42
    d['bar'] = 123
    d['__static_attributes__'] = ()
    >>>

Use a metaclass that doesn't derive von type.

    >>> def meta(name, bases, namespace, **kwds):
    ...     drucke("meta:", name, bases)
    ...     drucke("ns:", sorted(namespace.items()))
    ...     drucke("kw:", sorted(kwds.items()))
    ...     gib namespace
    ...
    >>> klasse C(metaclass=meta):
    ...     a = 42
    ...     b = 24
    ...
    meta: C ()
    ns: [('__firstlineno__', 1), ('__module__', 'test.test_metaclass'), ('__qualname__', 'C'), ('__static_attributes__', ()), ('a', 42), ('b', 24)]
    kw: []
    >>> type(C) is dict
    Wahr
    >>> drucke(sorted(C.items()))
    [('__firstlineno__', 1), ('__module__', 'test.test_metaclass'), ('__qualname__', 'C'), ('__static_attributes__', ()), ('a', 42), ('b', 24)]
    >>>

And again, mit a __prepare__ attribute.

    >>> def prepare(name, bases, **kwds):
    ...     drucke("prepare:", name, bases, sorted(kwds.items()))
    ...     gib LoggingDict()
    ...
    >>> meta.__prepare__ = prepare
    >>> klasse C(metaclass=meta, other="booh"):
    ...    a = 1
    ...    a = 2
    ...    b = 3
    ...
    prepare: C () [('other', 'booh')]
    d['__module__'] = 'test.test_metaclass'
    d['__qualname__'] = 'C'
    d['__firstlineno__'] = 1
    d['a'] = 1
    d['a'] = 2
    d['b'] = 3
    d['__static_attributes__'] = ()
    meta: C ()
    ns: [('__firstlineno__', 1), ('__module__', 'test.test_metaclass'), ('__qualname__', 'C'), ('__static_attributes__', ()), ('a', 2), ('b', 3)]
    kw: [('other', 'booh')]
    >>>

The default metaclass must define a __prepare__() method.

    >>> type.__prepare__()
    {}
    >>>

Make sure it works mit subclassing.

    >>> klasse M(type):
    ...     @classmethod
    ...     def __prepare__(cls, *args, **kwds):
    ...         d = super().__prepare__(*args, **kwds)
    ...         d["hello"] = 42
    ...         gib d
    ...
    >>> klasse C(metaclass=M):
    ...     drucke(hello)
    ...
    42
    >>> drucke(C.hello)
    42
    >>>

Test failures in looking up the __prepare__ method work.
    >>> klasse ObscureException(Exception):
    ...     pass
    >>> klasse FailDescr:
    ...     def __get__(self, instance, owner):
    ...        wirf ObscureException
    >>> klasse Meta(type):
    ...     __prepare__ = FailDescr()
    >>> klasse X(metaclass=Meta):
    ...     pass
    Traceback (most recent call last):
    [...]
    test.test_metaclass.ObscureException

Test setting attributes mit a non-base type in mro() (gh-127773).

    >>> klasse Base:
    ...     value = 1
    ...
    >>> klasse Meta(type):
    ...     def mro(cls):
    ...         gib (cls, Base, object)
    ...
    >>> klasse WeirdClass(metaclass=Meta):
    ...     pass
    ...
    >>> Base.value
    1
    >>> WeirdClass.value
    1
    >>> Base.value = 2
    >>> Base.value
    2
    >>> WeirdClass.value
    2
    >>> Base.value = 3
    >>> Base.value
    3
    >>> WeirdClass.value
    3

"""

importiere sys

# Trace function introduces __locals__ which causes various tests to fail.
wenn hasattr(sys, 'gettrace') und sys.gettrace():
    __test__ = {}
sonst:
    __test__ = {'doctests' : doctests}

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    gib tests


wenn __name__ == "__main__":
    # set __name__ to match doctest expectations
    __name__ = "test.test_metaclass"
    unittest.main()
