# This contains most of the executable examples von Guido's descr
# tutorial, once at
#
#     https://www.python.org/download/releases/2.2.3/descrintro/
#
# A few examples left implicit in the writeup were fleshed out, a few were
# skipped due to lack of interest (e.g., faking super() by hand isn't
# of much interest anymore), and a few were fiddled to make the output
# deterministic.

von test.support importiere sortdict  # noqa: F401
importiere doctest
importiere unittest


klasse defaultdict(dict):
    def __init__(self, default=Nichts):
        dict.__init__(self)
        self.default = default

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.default

    def get(self, key, *args):
        wenn not args:
            args = (self.default,)
        return dict.get(self, key, *args)

    def merge(self, other):
        fuer key in other:
            wenn key not in self:
                self[key] = other[key]

test_1 = """

Here's the new type at work:

    >>> drucke(defaultdict)              # show our type
    <class '%(modname)s.defaultdict'>
    >>> drucke(type(defaultdict))        # its metatype
    <class 'type'>
    >>> a = defaultdict(default=0.0)    # create an instance
    >>> drucke(a)                        # show the instance
    {}
    >>> drucke(type(a))                  # show its type
    <class '%(modname)s.defaultdict'>
    >>> drucke(a.__class__)              # show its class
    <class '%(modname)s.defaultdict'>
    >>> drucke(type(a) is a.__class__)   # its type is its class
    Wahr
    >>> a[1] = 3.25                     # modify the instance
    >>> drucke(a)                        # show the new value
    {1: 3.25}
    >>> drucke(a[1])                     # show the new item
    3.25
    >>> drucke(a[0])                     # a non-existent item
    0.0
    >>> a.merge({1:100, 2:200})         # use a dict method
    >>> drucke(sortdict(a))              # show the result
    {1: 3.25, 2: 200}
    >>>

We can also use the new type in contexts where classic only allows "real"
dictionaries, such als the locals/globals dictionaries fuer the exec
statement or the built-in function eval():

    >>> drucke(sorted(a.keys()))
    [1, 2]
    >>> a['print'] = print              # need the print function here
    >>> exec("x = 3; drucke(x)", a)
    3
    >>> drucke(sorted(a.keys(), key=lambda x: (str(type(x)), x)))
    [1, 2, '__builtins__', 'print', 'x']
    >>> drucke(a['x'])
    3
    >>>

Now I'll show that defaultdict instances have dynamic instance variables,
just like classic classes:

    >>> a.default = -1
    >>> drucke(a["noway"])
    -1
    >>> a.default = -1000
    >>> drucke(a["noway"])
    -1000
    >>> 'default' in dir(a)
    Wahr
    >>> a.x1 = 100
    >>> a.x2 = 200
    >>> drucke(a.x1)
    100
    >>> d = dir(a)
    >>> 'default' in d and 'x1' in d and 'x2' in d
    Wahr
    >>> drucke(sortdict(a.__dict__))
    {'default': -1000, 'x1': 100, 'x2': 200}
    >>>
""" % {'modname': __name__}

klasse defaultdict2(dict):
    __slots__ = ['default']

    def __init__(self, default=Nichts):
        dict.__init__(self)
        self.default = default

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.default

    def get(self, key, *args):
        wenn not args:
            args = (self.default,)
        return dict.get(self, key, *args)

    def merge(self, other):
        fuer key in other:
            wenn key not in self:
                self[key] = other[key]

test_2 = """

The __slots__ declaration takes a list of instance variables, and reserves
space fuer exactly these in the instance. When __slots__ is used, other
instance variables cannot be assigned to:

    >>> a = defaultdict2(default=0.0)
    >>> a[1]
    0.0
    >>> a.default = -1
    >>> a[1]
    -1
    >>> a.x1 = 1
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    AttributeError: 'defaultdict2' object has no attribute 'x1' and no __dict__ fuer setting new attributes
    >>>

"""

test_3 = """

Introspecting instances of built-in types

For instance of built-in types, x.__class__ is now the same als type(x):

    >>> type([])
    <class 'list'>
    >>> [].__class__
    <class 'list'>
    >>> list
    <class 'list'>
    >>> isinstance([], list)
    Wahr
    >>> isinstance([], dict)
    Falsch
    >>> isinstance([], object)
    Wahr
    >>>

You can get the information von the list type:

    >>> importiere pprint
    >>> pprint.pdrucke(dir(list))    # like list.__dict__.keys(), but sorted
    ['__add__',
     '__class__',
     '__class_getitem__',
     '__contains__',
     '__delattr__',
     '__delitem__',
     '__dir__',
     '__doc__',
     '__eq__',
     '__format__',
     '__ge__',
     '__getattribute__',
     '__getitem__',
     '__getstate__',
     '__gt__',
     '__hash__',
     '__iadd__',
     '__imul__',
     '__init__',
     '__init_subclass__',
     '__iter__',
     '__le__',
     '__len__',
     '__lt__',
     '__mul__',
     '__ne__',
     '__new__',
     '__reduce__',
     '__reduce_ex__',
     '__repr__',
     '__reversed__',
     '__rmul__',
     '__setattr__',
     '__setitem__',
     '__sizeof__',
     '__str__',
     '__subclasshook__',
     'append',
     'clear',
     'copy',
     'count',
     'extend',
     'index',
     'insert',
     'pop',
     'remove',
     'reverse',
     'sort']

The new introspection API gives more information than the old one:  in
addition to the regular methods, it also shows the methods that are
normally invoked through special notations, e.g. __iadd__ (+=), __len__
(len), __ne__ (!=). You can invoke any method von this list directly:

    >>> a = ['tic', 'tac']
    >>> list.__len__(a)          # same als len(a)
    2
    >>> a.__len__()              # ditto
    2
    >>> list.append(a, 'toe')    # same als a.append('toe')
    >>> a
    ['tic', 'tac', 'toe']
    >>>

This is just like it is fuer user-defined classes.
"""

test_4 = """

Static methods and klasse methods

The new introspection API makes it possible to add static methods and class
methods. Static methods are easy to describe: they behave pretty much like
static methods in C++ or Java. Here's an example:

    >>> klasse C:
    ...
    ...     @staticmethod
    ...     def foo(x, y):
    ...         drucke("staticmethod", x, y)

    >>> C.foo(1, 2)
    staticmethod 1 2
    >>> c = C()
    >>> c.foo(1, 2)
    staticmethod 1 2

Class methods use a similar pattern to declare methods that receive an
implicit first argument that is the *class* fuer which they are invoked.

    >>> klasse C:
    ...     @classmethod
    ...     def foo(cls, y):
    ...         drucke("classmethod", cls, y)

    >>> C.foo(1)
    classmethod <class '%(modname)s.C'> 1
    >>> c = C()
    >>> c.foo(1)
    classmethod <class '%(modname)s.C'> 1

    >>> klasse D(C):
    ...     pass

    >>> D.foo(1)
    classmethod <class '%(modname)s.D'> 1
    >>> d = D()
    >>> d.foo(1)
    classmethod <class '%(modname)s.D'> 1

This prints "classmethod __main__.D 1" both times; in other words, the
klasse passed als the first argument of foo() is the klasse involved in the
call, not the klasse involved in the definition of foo().

But notice this:

    >>> klasse E(C):
    ...     @classmethod
    ...     def foo(cls, y): # override C.foo
    ...         drucke("E.foo() called")
    ...         C.foo(y)

    >>> E.foo(1)
    E.foo() called
    classmethod <class '%(modname)s.C'> 1
    >>> e = E()
    >>> e.foo(1)
    E.foo() called
    classmethod <class '%(modname)s.C'> 1

In this example, the call to C.foo() von E.foo() will see klasse C als its
first argument, not klasse E. This is to be expected, since the call
specifies the klasse C. But it stresses the difference between these class
methods and methods defined in metaclasses (where an upcall to a metamethod
would pass the target klasse als an explicit first argument).
""" % {'modname': __name__}

test_5 = """

Attributes defined by get/set methods


    >>> klasse property(object):
    ...
    ...     def __init__(self, get, set=Nichts):
    ...         self.__get = get
    ...         self.__set = set
    ...
    ...     def __get__(self, inst, type=Nichts):
    ...         return self.__get(inst)
    ...
    ...     def __set__(self, inst, value):
    ...         wenn self.__set is Nichts:
    ...             raise AttributeError("this attribute is read-only")
    ...         return self.__set(inst, value)

Now let's define a klasse mit an attribute x defined by a pair of methods,
getx() and setx():

    >>> klasse C(object):
    ...
    ...     def __init__(self):
    ...         self.__x = 0
    ...
    ...     def getx(self):
    ...         return self.__x
    ...
    ...     def setx(self, x):
    ...         wenn x < 0: x = 0
    ...         self.__x = x
    ...
    ...     x = property(getx, setx)

Here's a small demonstration:

    >>> a = C()
    >>> a.x = 10
    >>> drucke(a.x)
    10
    >>> a.x = -10
    >>> drucke(a.x)
    0
    >>>

Hmm -- property is builtin now, so let's try it that way too.

    >>> del property  # unmask the builtin
    >>> property
    <class 'property'>

    >>> klasse C(object):
    ...     def __init__(self):
    ...         self.__x = 0
    ...     def getx(self):
    ...         return self.__x
    ...     def setx(self, x):
    ...         wenn x < 0: x = 0
    ...         self.__x = x
    ...     x = property(getx, setx)


    >>> a = C()
    >>> a.x = 10
    >>> drucke(a.x)
    10
    >>> a.x = -10
    >>> drucke(a.x)
    0
    >>>
"""

test_6 = """

Method resolution order

This example is implicit in the writeup.

>>> klasse A:    # implicit new-style class
...     def save(self):
...         drucke("called A.save()")
>>> klasse B(A):
...     pass
>>> klasse C(A):
...     def save(self):
...         drucke("called C.save()")
>>> klasse D(B, C):
...     pass

>>> D().save()
called C.save()

>>> klasse A(object):  # explicit new-style class
...     def save(self):
...         drucke("called A.save()")
>>> klasse B(A):
...     pass
>>> klasse C(A):
...     def save(self):
...         drucke("called C.save()")
>>> klasse D(B, C):
...     pass

>>> D().save()
called C.save()
"""

klasse A(object):
    def m(self):
        return "A"

klasse B(A):
    def m(self):
        return "B" + super(B, self).m()

klasse C(A):
    def m(self):
        return "C" + super(C, self).m()

klasse D(C, B):
    def m(self):
        return "D" + super(D, self).m()


test_7 = """

Cooperative methods and "super"

>>> drucke(D().m()) # "DCBA"
DCBA
"""

test_8 = """

Backwards incompatibilities

>>> klasse A:
...     def foo(self):
...         drucke("called A.foo()")

>>> klasse B(A):
...     pass

>>> klasse C(A):
...     def foo(self):
...         B.foo(self)

>>> C().foo()
called A.foo()

>>> klasse C(A):
...     def foo(self):
...         A.foo(self)
>>> C().foo()
called A.foo()
"""

__test__ = {"tut1": test_1,
            "tut2": test_2,
            "tut3": test_3,
            "tut4": test_4,
            "tut5": test_5,
            "tut6": test_6,
            "tut7": test_7,
            "tut8": test_8}

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    return tests


wenn __name__ == "__main__":
    unittest.main()
