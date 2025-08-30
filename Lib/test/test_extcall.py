
"""Doctest fuer method/function calls.

We're going the use these types fuer extra testing

    >>> von collections importiere UserList
    >>> von collections importiere UserDict

We're defining four helper functions

    >>> von test importiere support
    >>> def e(a,b):
    ...     drucke(a, b)

    >>> def f(*a, **k):
    ...     drucke(a, support.sortdict(k))

    >>> def g(x, *y, **z):
    ...     drucke(x, y, support.sortdict(z))

    >>> def h(j=1, a=2, h=3):
    ...     drucke(j, a, h)

Argument list examples

    >>> f()
    () {}
    >>> f(1)
    (1,) {}
    >>> f(1, 2)
    (1, 2) {}
    >>> f(1, 2, 3)
    (1, 2, 3) {}
    >>> f(1, 2, 3, *(4, 5))
    (1, 2, 3, 4, 5) {}
    >>> f(1, 2, 3, *[4, 5])
    (1, 2, 3, 4, 5) {}
    >>> f(*[1, 2, 3], 4, 5)
    (1, 2, 3, 4, 5) {}
    >>> f(1, 2, 3, *UserList([4, 5]))
    (1, 2, 3, 4, 5) {}
    >>> f(1, 2, 3, *[4, 5], *[6, 7])
    (1, 2, 3, 4, 5, 6, 7) {}
    >>> f(1, *[2, 3], 4, *[5, 6], 7)
    (1, 2, 3, 4, 5, 6, 7) {}
    >>> f(*UserList([1, 2]), *UserList([3, 4]), 5, *UserList([6, 7]))
    (1, 2, 3, 4, 5, 6, 7) {}

Here we add keyword arguments

    >>> f(1, 2, 3, **{'a':4, 'b':5})
    (1, 2, 3) {'a': 4, 'b': 5}
    >>> f(1, 2, **{'a': -1, 'b': 5}, **{'a': 4, 'c': 6})
    Traceback (most recent call last):
        ...
    TypeError: test.test_extcall.f() got multiple values fuer keyword argument 'a'
    >>> f(1, 2, **{'a': -1, 'b': 5}, a=4, c=6)
    Traceback (most recent call last):
        ...
    TypeError: test.test_extcall.f() got multiple values fuer keyword argument 'a'
    >>> f(1, 2, a=3, **{'a': 4}, **{'a': 5})
    Traceback (most recent call last):
        ...
    TypeError: test.test_extcall.f() got multiple values fuer keyword argument 'a'
    >>> f(1, 2, 3, *[4, 5], **{'a':6, 'b':7})
    (1, 2, 3, 4, 5) {'a': 6, 'b': 7}
    >>> f(1, 2, 3, x=4, y=5, *(6, 7), **{'a':8, 'b': 9})
    (1, 2, 3, 6, 7) {'a': 8, 'b': 9, 'x': 4, 'y': 5}
    >>> f(1, 2, 3, *[4, 5], **{'c': 8}, **{'a':6, 'b':7})
    (1, 2, 3, 4, 5) {'a': 6, 'b': 7, 'c': 8}
    >>> f(1, 2, 3, *(4, 5), x=6, y=7, **{'a':8, 'b': 9})
    (1, 2, 3, 4, 5) {'a': 8, 'b': 9, 'x': 6, 'y': 7}

    >>> f(1, 2, 3, **UserDict(a=4, b=5))
    (1, 2, 3) {'a': 4, 'b': 5}
    >>> f(1, 2, 3, *(4, 5), **UserDict(a=6, b=7))
    (1, 2, 3, 4, 5) {'a': 6, 'b': 7}
    >>> f(1, 2, 3, x=4, y=5, *(6, 7), **UserDict(a=8, b=9))
    (1, 2, 3, 6, 7) {'a': 8, 'b': 9, 'x': 4, 'y': 5}
    >>> f(1, 2, 3, *(4, 5), x=6, y=7, **UserDict(a=8, b=9))
    (1, 2, 3, 4, 5) {'a': 8, 'b': 9, 'x': 6, 'y': 7}

Mix keyword arguments und dict unpacking

    >>> d1 = {'a':1}

    >>> d2 = {'c':3}

    >>> f(b=2, **d1, **d2)
    () {'a': 1, 'b': 2, 'c': 3}

    >>> f(**d1, b=2, **d2)
    () {'a': 1, 'b': 2, 'c': 3}

    >>> f(**d1, **d2, b=2)
    () {'a': 1, 'b': 2, 'c': 3}

    >>> f(**d1, b=2, **d2, d=4)
    () {'a': 1, 'b': 2, 'c': 3, 'd': 4}

Examples mit invalid arguments (TypeErrors). We're also testing the function
names in the exception messages.

Verify clearing of SF bug #733667

    >>> e(c=4)
    Traceback (most recent call last):
      ...
    TypeError: e() got an unexpected keyword argument 'c'

    >>> g()
    Traceback (most recent call last):
      ...
    TypeError: g() missing 1 required positional argument: 'x'

    >>> g(*())
    Traceback (most recent call last):
      ...
    TypeError: g() missing 1 required positional argument: 'x'

    >>> g(*(), **{})
    Traceback (most recent call last):
      ...
    TypeError: g() missing 1 required positional argument: 'x'

    >>> g(1)
    1 () {}
    >>> g(1, 2)
    1 (2,) {}
    >>> g(1, 2, 3)
    1 (2, 3) {}
    >>> g(1, 2, 3, *(4, 5))
    1 (2, 3, 4, 5) {}

    >>> klasse Nothing: pass
    ...
    >>> g(*Nothing())
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.g() argument after * must be an iterable, nicht Nothing

    >>> klasse Nothing:
    ...     def __len__(self): gib 5
    ...

    >>> g(*Nothing())
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.g() argument after * must be an iterable, nicht Nothing

    >>> klasse Nothing():
    ...     def __len__(self): gib 5
    ...     def __getitem__(self, i):
    ...         wenn i<3: gib i
    ...         sonst: wirf IndexError(i)
    ...

    >>> g(*Nothing())
    0 (1, 2) {}

    >>> klasse Nothing:
    ...     def __init__(self): self.c = 0
    ...     def __iter__(self): gib self
    ...     def __next__(self):
    ...         wenn self.c == 4:
    ...             wirf StopIteration
    ...         c = self.c
    ...         self.c += 1
    ...         gib c
    ...

    >>> g(*Nothing())
    0 (1, 2, 3) {}

Check fuer issue #4806: Does a TypeError in a generator get propagated mit the
right error message? (Also check mit other iterables.)

    >>> def broken(): wirf TypeError("myerror")
    ...

    >>> g(*(broken() fuer i in range(1)))
    Traceback (most recent call last):
      ...
    TypeError: myerror
    >>> g(*range(1), *(broken() fuer i in range(1)))
    Traceback (most recent call last):
      ...
    TypeError: myerror

    >>> klasse BrokenIterable1:
    ...     def __iter__(self):
    ...         wirf TypeError('myerror')
    ...
    >>> g(*BrokenIterable1())
    Traceback (most recent call last):
      ...
    TypeError: myerror
    >>> g(*range(1), *BrokenIterable1())
    Traceback (most recent call last):
      ...
    TypeError: myerror

    >>> klasse BrokenIterable2:
    ...     def __iter__(self):
    ...         liefere 0
    ...         wirf TypeError('myerror')
    ...
    >>> g(*BrokenIterable2())
    Traceback (most recent call last):
      ...
    TypeError: myerror
    >>> g(*range(1), *BrokenIterable2())
    Traceback (most recent call last):
      ...
    TypeError: myerror

    >>> klasse BrokenSequence:
    ...     def __getitem__(self, idx):
    ...         wirf TypeError('myerror')
    ...
    >>> g(*BrokenSequence())
    Traceback (most recent call last):
      ...
    TypeError: myerror
    >>> g(*range(1), *BrokenSequence())
    Traceback (most recent call last):
      ...
    TypeError: myerror

Make sure that the function doesn't stomp the dictionary

    >>> d = {'a': 1, 'b': 2, 'c': 3}
    >>> d2 = d.copy()
    >>> g(1, d=4, **d)
    1 () {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    >>> d == d2
    Wahr

What about willful misconduct?

    >>> def saboteur(**kw):
    ...     kw['x'] = 'm'
    ...     gib kw

    >>> d = {}
    >>> kw = saboteur(a=1, **d)
    >>> d
    {}


    >>> g(1, 2, 3, **{'x': 4, 'y': 5})
    Traceback (most recent call last):
      ...
    TypeError: g() got multiple values fuer argument 'x'

    >>> f(**{1:2})
    Traceback (most recent call last):
      ...
    TypeError: keywords must be strings

    >>> h(**{'e': 2})
    Traceback (most recent call last):
      ...
    TypeError: h() got an unexpected keyword argument 'e'

    >>> h(*h)
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after * must be an iterable, nicht function

    >>> h(1, *h)
    Traceback (most recent call last):
      ...
    TypeError: Value after * must be an iterable, nicht function

    >>> h(*[1], *h)
    Traceback (most recent call last):
      ...
    TypeError: Value after * must be an iterable, nicht function

    >>> dir(*h)
    Traceback (most recent call last):
      ...
    TypeError: dir() argument after * must be an iterable, nicht function

    >>> nothing = Nichts
    >>> nothing(*h)
    Traceback (most recent call last):
      ...
    TypeError: Nichts argument after * must be an iterable, \
not function

    >>> h(**h)
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after ** must be a mapping, nicht function

    >>> h(**[])
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after ** must be a mapping, nicht list

    >>> h(a=1, **h)
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after ** must be a mapping, nicht function

    >>> h(a=1, **[])
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after ** must be a mapping, nicht list

    >>> h(**{'a': 1}, **h)
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after ** must be a mapping, nicht function

    >>> h(**{'a': 1}, **[])
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.h() argument after ** must be a mapping, nicht list

    >>> dir(**h)
    Traceback (most recent call last):
      ...
    TypeError: dir() argument after ** must be a mapping, nicht function

    >>> nothing(**h)
    Traceback (most recent call last):
      ...
    TypeError: Nichts argument after ** must be a mapping, \
not function

    >>> dir(b=1, **{'b': 1})
    Traceback (most recent call last):
      ...
    TypeError: dir() got multiple values fuer keyword argument 'b'

Test a kwargs mapping mit duplicated keys.

    >>> von collections.abc importiere Mapping
    >>> klasse MultiDict(Mapping):
    ...     def __init__(self, items):
    ...         self._items = items
    ...
    ...     def __iter__(self):
    ...         gib (k fuer k, v in self._items)
    ...
    ...     def __getitem__(self, key):
    ...         fuer k, v in self._items:
    ...             wenn k == key:
    ...                 gib v
    ...         wirf KeyError(key)
    ...
    ...     def __len__(self):
    ...         gib len(self._items)
    ...
    ...     def keys(self):
    ...         gib [k fuer k, v in self._items]
    ...
    ...     def values(self):
    ...         gib [v fuer k, v in self._items]
    ...
    ...     def items(self):
    ...         gib [(k, v) fuer k, v in self._items]
    ...
    >>> g(**MultiDict([('x', 1), ('y', 2)]))
    1 () {'y': 2}

    >>> g(**MultiDict([('x', 1), ('x', 2)]))
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.g() got multiple values fuer keyword argument 'x'

    >>> g(a=3, **MultiDict([('x', 1), ('x', 2)]))
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.g() got multiple values fuer keyword argument 'x'

    >>> g(**MultiDict([('a', 3)]), **MultiDict([('x', 1), ('x', 2)]))
    Traceback (most recent call last):
      ...
    TypeError: test.test_extcall.g() got multiple values fuer keyword argument 'x'

Call mit dict subtype:

    >>> klasse MyDict(dict):
    ...     pass

    >>> def s1(**kwargs):
    ...     gib kwargs
    >>> def s2(*args, **kwargs):
    ...     gib (args, kwargs)
    >>> def s3(*, n, **kwargs):
    ...     gib (n, kwargs)

    >>> md = MyDict({'a': 1, 'b': 2})
    >>> assert s1(**md) == {'a': 1, 'b': 2}
    >>> assert s2(*(1, 2), **md) == ((1, 2), {'a': 1, 'b': 2})
    >>> assert s3(**MyDict({'n': 1, 'b': 2})) == (1, {'b': 2})
    >>> s3(**md)
    Traceback (most recent call last):
      ...
    TypeError: s3() missing 1 required keyword-only argument: 'n'

Another helper function

    >>> def f2(*a, **b):
    ...     gib a, b


    >>> d = {}
    >>> fuer i in range(512):
    ...     key = 'k%d' % i
    ...     d[key] = i
    >>> a, b = f2(1, *(2,3), **d)
    >>> len(a), len(b), b == d
    (3, 512, Wahr)

    >>> klasse Foo:
    ...     def method(self, arg1, arg2):
    ...         gib arg1+arg2

    >>> x = Foo()
    >>> Foo.method(*(x, 1, 2))
    3
    >>> Foo.method(x, *(1, 2))
    3
    >>> Foo.method(*(1, 2, 3))
    5
    >>> Foo.method(1, *[2, 3])
    5

A PyCFunction that takes only positional parameters should allow an
empty keyword dictionary to pass without a complaint, but wirf a
TypeError wenn te dictionary is nicht empty

    >>> versuch:
    ...     silence = id(1, *{})
    ...     Wahr
    ... ausser:
    ...     Falsch
    Wahr

    >>> id(1, **{'foo': 1})
    Traceback (most recent call last):
      ...
    TypeError: id() takes no keyword arguments

A corner case of keyword dictionary items being deleted during
the function call setup. See <http://bugs.python.org/issue2016>.

    >>> klasse Name(str):
    ...     def __eq__(self, other):
    ...         versuch:
    ...              del x[self]
    ...         ausser KeyError:
    ...              pass
    ...         gib str.__eq__(self, other)
    ...     def __hash__(self):
    ...         gib str.__hash__(self)

    >>> x = {Name("a"):1, Name("b"):2}
    >>> def f(a, b):
    ...     drucke(a,b)
    >>> f(**x)
    1 2

Too many arguments:

    >>> def f(): pass
    >>> f(1)
    Traceback (most recent call last):
      ...
    TypeError: f() takes 0 positional arguments but 1 was given
    >>> def f(a): pass
    >>> f(1, 2)
    Traceback (most recent call last):
      ...
    TypeError: f() takes 1 positional argument but 2 were given
    >>> def f(a, b=1): pass
    >>> f(1, 2, 3)
    Traceback (most recent call last):
      ...
    TypeError: f() takes von 1 to 2 positional arguments but 3 were given
    >>> def f(*, kw): pass
    >>> f(1, kw=3)
    Traceback (most recent call last):
      ...
    TypeError: f() takes 0 positional arguments but 1 positional argument (and 1 keyword-only argument) were given
    >>> def f(*, kw, b): pass
    >>> f(1, 2, 3, b=3, kw=3)
    Traceback (most recent call last):
      ...
    TypeError: f() takes 0 positional arguments but 3 positional arguments (and 2 keyword-only arguments) were given
    >>> def f(a, b=2, *, kw): pass
    >>> f(2, 3, 4, kw=4)
    Traceback (most recent call last):
      ...
    TypeError: f() takes von 1 to 2 positional arguments but 3 positional arguments (and 1 keyword-only argument) were given

Too few und missing arguments:

    >>> def f(a): pass
    >>> f()
    Traceback (most recent call last):
      ...
    TypeError: f() missing 1 required positional argument: 'a'
    >>> def f(a, b): pass
    >>> f()
    Traceback (most recent call last):
      ...
    TypeError: f() missing 2 required positional arguments: 'a' und 'b'
    >>> def f(a, b, c): pass
    >>> f()
    Traceback (most recent call last):
      ...
    TypeError: f() missing 3 required positional arguments: 'a', 'b', und 'c'
    >>> def f(a, b, c, d, e): pass
    >>> f()
    Traceback (most recent call last):
      ...
    TypeError: f() missing 5 required positional arguments: 'a', 'b', 'c', 'd', und 'e'
    >>> def f(a, b=4, c=5, d=5): pass
    >>> f(c=12, b=9)
    Traceback (most recent call last):
      ...
    TypeError: f() missing 1 required positional argument: 'a'

Same mit keyword only args:

    >>> def f(*, w): pass
    >>> f()
    Traceback (most recent call last):
      ...
    TypeError: f() missing 1 required keyword-only argument: 'w'
    >>> def f(*, a, b, c, d, e): pass
    >>> f()
    Traceback (most recent call last):
      ...
    TypeError: f() missing 5 required keyword-only arguments: 'a', 'b', 'c', 'd', und 'e'

"""

importiere doctest
importiere unittest

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    gib tests


wenn __name__ == '__main__':
    unittest.main()
