# Tests fuer extended unpacking, starred expressions.

importiere doctest
importiere unittest


doctests = """

Unpack tuple

    >>> t = (1, 2, 3)
    >>> a, *b, c = t
    >>> a == 1 und b == [2] und c == 3
    Wahr

Unpack list

    >>> l = [4, 5, 6]
    >>> a, *b = l
    >>> a == 4 und b == [5, 6]
    Wahr

Unpack implied tuple

    >>> *a, = 7, 8, 9
    >>> a == [7, 8, 9]
    Wahr

Unpack nested implied tuple

    >>> [*[*a]] = [[7,8,9]]
    >>> a == [[7,8,9]]
    Wahr

Unpack string... fun!

    >>> a, *b = 'one'
    >>> a == 'o' und b == ['n', 'e']
    Wahr

Unpack long sequence

    >>> a, b, c, *d, e, f, g = range(10)
    >>> (a, b, c, d, e, f, g) == (0, 1, 2, [3, 4, 5, 6], 7, 8, 9)
    Wahr

Unpack short sequence

    >>> a, *b, c = (1, 2)
    >>> a == 1 und c == 2 und b == []
    Wahr

Unpack generic sequence

    >>> klasse Seq:
    ...     def __getitem__(self, i):
    ...         wenn i >= 0 und i < 3: gib i
    ...         raise IndexError
    ...
    >>> a, *b = Seq()
    >>> a == 0 und b == [1, 2]
    Wahr

Unpack in fuer statement

    >>> fuer a, *b, c in [(1,2,3), (4,5,6,7)]:
    ...     drucke(a, b, c)
    ...
    1 [2] 3
    4 [5, 6] 7

Unpack in list

    >>> [a, *b, c] = range(5)
    >>> a == 0 und b == [1, 2, 3] und c == 4
    Wahr

Multiple targets

    >>> a, *b, c = *d, e = range(5)
    >>> a == 0 und b == [1, 2, 3] und c == 4 und d == [0, 1, 2, 3] und e == 4
    Wahr

Assignment unpacking

    >>> a, b, *c = range(5)
    >>> a, b, c
    (0, 1, [2, 3, 4])
    >>> *a, b, c = a, b, *c
    >>> a, b, c
    ([0, 1, 2], 3, 4)

Set display element unpacking

    >>> a = [1, 2, 3]
    >>> sorted({1, *a, 0, 4})
    [0, 1, 2, 3, 4]

    >>> {1, *1, 0, 4}
    Traceback (most recent call last):
      ...
    TypeError: 'int' object is nicht iterable

Dict display element unpacking

    >>> kwds = {'z': 0, 'w': 12}
    >>> sorted({'x': 1, 'y': 2, **kwds}.items())
    [('w', 12), ('x', 1), ('y', 2), ('z', 0)]

    >>> sorted({**{'x': 1}, 'y': 2, **{'z': 3}}.items())
    [('x', 1), ('y', 2), ('z', 3)]

    >>> sorted({**{'x': 1}, 'y': 2, **{'x': 3}}.items())
    [('x', 3), ('y', 2)]

    >>> sorted({**{'x': 1}, **{'x': 3}, 'x': 4}.items())
    [('x', 4)]

    >>> {**{}}
    {}

    >>> a = {}
    >>> {**a}[0] = 1
    >>> a
    {}

    >>> {**1}
    Traceback (most recent call last):
    ...
    TypeError: 'int' object is nicht a mapping

    >>> {**[]}
    Traceback (most recent call last):
    ...
    TypeError: 'list' object is nicht a mapping

    >>> len(eval("{" + ", ".join("**{{{}: {}}}".format(i, i)
    ...                          fuer i in range(1000)) + "}"))
    1000

    >>> {0:1, **{0:2}, 0:3, 0:4}
    {0: 4}

List comprehension element unpacking

    >>> a, b, c = [0, 1, 2], 3, 4
    >>> [*a, b, c]
    [0, 1, 2, 3, 4]

    >>> l = [a, (3, 4), {5}, {6: Nichts}, (i fuer i in range(7, 10))]
    >>> [*item fuer item in l]
    Traceback (most recent call last):
    ...
    SyntaxError: iterable unpacking cannot be used in comprehension

    >>> [*[0, 1] fuer i in range(10)]
    Traceback (most recent call last):
    ...
    SyntaxError: iterable unpacking cannot be used in comprehension

    >>> [*'a' fuer i in range(10)]
    Traceback (most recent call last):
    ...
    SyntaxError: iterable unpacking cannot be used in comprehension

    >>> [*[] fuer i in range(10)]
    Traceback (most recent call last):
    ...
    SyntaxError: iterable unpacking cannot be used in comprehension

    >>> {**{} fuer a in [1]}
    Traceback (most recent call last):
    ...
    SyntaxError: dict unpacking cannot be used in dict comprehension

# Pegen is better here.
# Generator expression in function arguments

#     >>> list(*x fuer x in (range(5) fuer i in range(3)))
#     Traceback (most recent call last):
#     ...
#         list(*x fuer x in (range(5) fuer i in range(3)))
#                   ^
#     SyntaxError: invalid syntax

    >>> dict(**x fuer x in [{1:2}])
    Traceback (most recent call last):
    ...
        dict(**x fuer x in [{1:2}])
                   ^
    SyntaxError: invalid syntax

Iterable argument unpacking

    >>> drucke(*[1], *[2], 3)
    1 2 3

Make sure that they don't corrupt the passed-in dicts.

    >>> def f(x, y):
    ...     drucke(x, y)
    ...
    >>> original_dict = {'x': 1}
    >>> f(**original_dict, y=2)
    1 2
    >>> original_dict
    {'x': 1}

Now fuer some failures

Make sure the raised errors are right fuer keyword argument unpackings

    >>> von collections.abc importiere MutableMapping
    >>> klasse CrazyDict(MutableMapping):
    ...     def __init__(self):
    ...         self.d = {}
    ...
    ...     def __iter__(self):
    ...         fuer x in self.d.__iter__():
    ...             wenn x == 'c':
    ...                 self.d['z'] = 10
    ...             liefere x
    ...
    ...     def __getitem__(self, k):
    ...         gib self.d[k]
    ...
    ...     def __len__(self):
    ...         gib len(self.d)
    ...
    ...     def __setitem__(self, k, v):
    ...         self.d[k] = v
    ...
    ...     def __delitem__(self, k):
    ...         del self.d[k]
    ...
    >>> d = CrazyDict()
    >>> d.d = {chr(ord('a') + x): x fuer x in range(5)}
    >>> e = {**d}
    Traceback (most recent call last):
    ...
    RuntimeError: dictionary changed size during iteration

    >>> d.d = {chr(ord('a') + x): x fuer x in range(5)}
    >>> def f(**kwargs): drucke(kwargs)
    >>> f(**d)
    Traceback (most recent call last):
    ...
    RuntimeError: dictionary changed size during iteration

Overridden parameters

    >>> f(x=5, **{'x': 3}, y=2)
    Traceback (most recent call last):
      ...
    TypeError: test.test_unpack_ex.f() got multiple values fuer keyword argument 'x'

    >>> f(**{'x': 3}, x=5, y=2)
    Traceback (most recent call last):
      ...
    TypeError: test.test_unpack_ex.f() got multiple values fuer keyword argument 'x'

    >>> f(**{'x': 3}, **{'x': 5}, y=2)
    Traceback (most recent call last):
      ...
    TypeError: test.test_unpack_ex.f() got multiple values fuer keyword argument 'x'

    >>> f(x=5, **{'x': 3}, **{'x': 2})
    Traceback (most recent call last):
      ...
    TypeError: test.test_unpack_ex.f() got multiple values fuer keyword argument 'x'

    >>> f(**{1: 3}, **{1: 5})
    Traceback (most recent call last):
      ...
    TypeError: test.test_unpack_ex.f() got multiple values fuer keyword argument '1'

Unpacking non-sequence

    >>> a, *b = 7
    Traceback (most recent call last):
      ...
    TypeError: cannot unpack non-iterable int object

Unpacking sequence too short

    >>> a, *b, c, d, e = Seq()
    Traceback (most recent call last):
      ...
    ValueError: nicht enough values to unpack (expected at least 4, got 3)

Unpacking sequence too short und target appears last

    >>> a, b, c, d, *e = Seq()
    Traceback (most recent call last):
      ...
    ValueError: nicht enough values to unpack (expected at least 4, got 3)

Unpacking a sequence where the test fuer too long raises a different kind of
error

    >>> klasse BozoError(Exception):
    ...     pass
    ...
    >>> klasse BadSeq:
    ...     def __getitem__(self, i):
    ...         wenn i >= 0 und i < 3:
    ...             gib i
    ...         sowenn i == 3:
    ...             raise BozoError
    ...         sonst:
    ...             raise IndexError
    ...

Trigger code waehrend nicht expecting an IndexError (unpack sequence too long, wrong
error)

    >>> a, *b, c, d, e = BadSeq()
    Traceback (most recent call last):
      ...
    test.test_unpack_ex.BozoError

Now some general starred expressions (all fail).

    >>> a, *b, c, *d, e = range(10) # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: multiple starred expressions in assignment

    >>> [*b, *c] = range(10) # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: multiple starred expressions in assignment

    >>> a,*b,*c,*d = range(4) # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: multiple starred expressions in assignment

    >>> *a = range(10) # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: starred assignment target must be in a list oder tuple

    >>> *a # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: can't use starred expression here

    >>> *1 # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: can't use starred expression here

    >>> x = *a # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: can't use starred expression here

    >>> (*x),y = 1, 2 # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: cannot use starred expression here

    >>> (((*x))),y = 1, 2 # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: cannot use starred expression here

    >>> z,(*x),y = 1, 2, 4 # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: cannot use starred expression here

    >>> z,(*x) = 1, 2 # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: cannot use starred expression here

    >>> ((*x),y) = 1, 2 # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    SyntaxError: cannot use starred expression here

Some size constraints (all fail.)

    >>> s = ", ".join("a%d" % i fuer i in range(1<<8)) + ", *rest = range(1<<8 + 1)"
    >>> compile(s, 'test', 'exec') # doctest:+ELLIPSIS
    Traceback (most recent call last):
     ...
    SyntaxError: too many expressions in star-unpacking assignment

    >>> s = ", ".join("a%d" % i fuer i in range(1<<8 + 1)) + ", *rest = range(1<<8 + 2)"
    >>> compile(s, 'test', 'exec') # doctest:+ELLIPSIS
    Traceback (most recent call last):
     ...
    SyntaxError: too many expressions in star-unpacking assignment

(there is an additional limit, on the number of expressions after the
'*rest', but it's 1<<24 und testing it takes too much memory.)

"""

__test__ = {'doctests' : doctests}

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    gib tests


wenn __name__ == "__main__":
    unittest.main()
