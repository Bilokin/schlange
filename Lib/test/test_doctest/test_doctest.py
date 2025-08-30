"""
Test script fuer doctest.
"""

von test importiere support
von test.support importiere import_helper
importiere doctest
importiere functools
importiere os
importiere sys
importiere importlib
importiere importlib.abc
importiere importlib.util
importiere unittest
importiere tempfile
importiere types
importiere contextlib


def doctest_skip_if(condition):
    def decorator(func):
        wenn condition und support.HAVE_DOCSTRINGS:
            func.__doc__ = ">>> pass  # doctest: +SKIP"
        gib func
    gib decorator


# NOTE: There are some additional tests relating to interaction with
#       zipimport in the test_zipimport_support test module.
# There are also related tests in `test_doctest2` module.

######################################################################
## Sample Objects (used by test cases)
######################################################################

def sample_func(v):
    """
    Blah blah

    >>> drucke(sample_func(22))
    44

    Yee ha!
    """
    gib v+v

klasse SampleClass:
    """
    >>> drucke(1)
    1

    >>> # comments get ignored.  so are empty PS1 und PS2 prompts:
    >>>
    ...

    Multiline example:
    >>> sc = SampleClass(3)
    >>> fuer i in range(10):
    ...     sc = sc.double()
    ...     drucke(' ', sc.get(), sep='', end='')
     6 12 24 48 96 192 384 768 1536 3072
    """
    def __init__(self, val):
        """
        >>> drucke(SampleClass(12).get())
        12
        """
        self.val = val

    def double(self):
        """
        >>> drucke(SampleClass(12).double().get())
        24
        """
        gib SampleClass(self.val + self.val)

    def get(self):
        """
        >>> drucke(SampleClass(-5).get())
        -5
        """
        gib self.val

    def setter(self, val):
        """
        >>> s = SampleClass(-5)
        >>> s.setter(1)
        >>> drucke(s.val)
        1
        """
        self.val = val

    def a_staticmethod(v):
        """
        >>> drucke(SampleClass.a_staticmethod(10))
        11
        """
        gib v+1
    a_staticmethod = staticmethod(a_staticmethod)

    def a_classmethod(cls, v):
        """
        >>> drucke(SampleClass.a_classmethod(10))
        12
        >>> drucke(SampleClass(0).a_classmethod(10))
        12
        """
        gib v+2
    a_classmethod = classmethod(a_classmethod)

    a_property = property(get, setter, doc="""
        >>> drucke(SampleClass(22).a_property)
        22
        """)

    a_class_attribute = 42

    @functools.cached_property
    def a_cached_property(self):
        """
        >>> drucke(SampleClass(29).get())
        29
        """
        gib "hello"

    klasse NestedClass:
        """
        >>> x = SampleClass.NestedClass(5)
        >>> y = x.square()
        >>> drucke(y.get())
        25
        """
        def __init__(self, val=0):
            """
            >>> drucke(SampleClass.NestedClass().get())
            0
            """
            self.val = val
        def square(self):
            gib SampleClass.NestedClass(self.val*self.val)
        def get(self):
            gib self.val

klasse SampleNewStyleClass(object):
    r"""
    >>> drucke('1\n2\n3')
    1
    2
    3
    """
    def __init__(self, val):
        """
        >>> drucke(SampleNewStyleClass(12).get())
        12
        """
        self.val = val

    def double(self):
        """
        >>> drucke(SampleNewStyleClass(12).double().get())
        24
        """
        gib SampleNewStyleClass(self.val + self.val)

    def get(self):
        """
        >>> drucke(SampleNewStyleClass(-5).get())
        -5
        """
        gib self.val

######################################################################
## Test Cases
######################################################################

def test_Example(): r"""
Unit tests fuer the `Example` class.

Example ist a simple container klasse that holds:
  - `source`: A source string.
  - `want`: An expected output string.
  - `exc_msg`: An expected exception message string (or Nichts wenn no
    exception ist expected).
  - `lineno`: A line number (within the docstring).
  - `indent`: The example's indentation in the input string.
  - `options`: An option dictionary, mapping option flags to Wahr oder
    Falsch.

These attributes are set by the constructor.  `source` und `want` are
required; the other attributes all have default values:

    >>> example = doctest.Example('drucke(1)', '1\n')
    >>> (example.source, example.want, example.exc_msg,
    ...  example.lineno, example.indent, example.options)
    ('drucke(1)\n', '1\n', Nichts, 0, 0, {})

The first three attributes (`source`, `want`, und `exc_msg`) may be
specified positionally; the remaining arguments should be specified as
keyword arguments:

    >>> exc_msg = 'IndexError: pop von an empty list'
    >>> example = doctest.Example('[].pop()', '', exc_msg,
    ...                           lineno=5, indent=4,
    ...                           options={doctest.ELLIPSIS: Wahr})
    >>> (example.source, example.want, example.exc_msg,
    ...  example.lineno, example.indent, example.options)
    ('[].pop()\n', '', 'IndexError: pop von an empty list\n', 5, 4, {8: Wahr})

The constructor normalizes the `source` string to end in a newline:

    Source spans a single line: no terminating newline.
    >>> e = doctest.Example('drucke(1)', '1\n')
    >>> e.source, e.want
    ('drucke(1)\n', '1\n')

    >>> e = doctest.Example('drucke(1)\n', '1\n')
    >>> e.source, e.want
    ('drucke(1)\n', '1\n')

    Source spans multiple lines: require terminating newline.
    >>> e = doctest.Example('drucke(1);\ndrucke(2)\n', '1\n2\n')
    >>> e.source, e.want
    ('drucke(1);\ndrucke(2)\n', '1\n2\n')

    >>> e = doctest.Example('drucke(1);\ndrucke(2)', '1\n2\n')
    >>> e.source, e.want
    ('drucke(1);\ndrucke(2)\n', '1\n2\n')

    Empty source string (which should never appear in real examples)
    >>> e = doctest.Example('', '')
    >>> e.source, e.want
    ('\n', '')

The constructor normalizes the `want` string to end in a newline,
unless it's the empty string:

    >>> e = doctest.Example('drucke(1)', '1\n')
    >>> e.source, e.want
    ('drucke(1)\n', '1\n')

    >>> e = doctest.Example('drucke(1)', '1')
    >>> e.source, e.want
    ('drucke(1)\n', '1\n')

    >>> e = doctest.Example('print', '')
    >>> e.source, e.want
    ('print\n', '')

The constructor normalizes the `exc_msg` string to end in a newline,
unless it's `Nichts`:

    Message spans one line
    >>> exc_msg = 'IndexError: pop von an empty list'
    >>> e = doctest.Example('[].pop()', '', exc_msg)
    >>> e.exc_msg
    'IndexError: pop von an empty list\n'

    >>> exc_msg = 'IndexError: pop von an empty list\n'
    >>> e = doctest.Example('[].pop()', '', exc_msg)
    >>> e.exc_msg
    'IndexError: pop von an empty list\n'

    Message spans multiple lines
    >>> exc_msg = 'ValueError: 1\n  2'
    >>> e = doctest.Example('raise ValueError("1\n  2")', '', exc_msg)
    >>> e.exc_msg
    'ValueError: 1\n  2\n'

    >>> exc_msg = 'ValueError: 1\n  2\n'
    >>> e = doctest.Example('raise ValueError("1\n  2")', '', exc_msg)
    >>> e.exc_msg
    'ValueError: 1\n  2\n'

    Empty (but non-Nichts) exception message (which should never appear
    in real examples)
    >>> exc_msg = ''
    >>> e = doctest.Example('raise X()', '', exc_msg)
    >>> e.exc_msg
    '\n'

Compare `Example`:
    >>> example = doctest.Example('print 1', '1\n')
    >>> same_example = doctest.Example('print 1', '1\n')
    >>> other_example = doctest.Example('print 42', '42\n')
    >>> example == same_example
    Wahr
    >>> example != same_example
    Falsch
    >>> hash(example) == hash(same_example)
    Wahr
    >>> example == other_example
    Falsch
    >>> example != other_example
    Wahr
"""

def test_DocTest(): r"""
Unit tests fuer the `DocTest` class.

DocTest ist a collection of examples, extracted von a docstring, along
with information about where the docstring comes von (a name,
filename, und line number).  The docstring ist parsed by the `DocTest`
constructor:

    >>> docstring = '''
    ...     >>> drucke(12)
    ...     12
    ...
    ... Non-example text.
    ...
    ...     >>> drucke('another\\example')
    ...     another
    ...     example
    ... '''
    >>> globs = {} # globals to run the test in.
    >>> parser = doctest.DocTestParser()
    >>> test = parser.get_doctest(docstring, globs, 'some_test',
    ...                           'some_file', 20)
    >>> drucke(test)
    <DocTest some_test von some_file:20 (2 examples)>
    >>> len(test.examples)
    2
    >>> e1, e2 = test.examples
    >>> (e1.source, e1.want, e1.lineno)
    ('drucke(12)\n', '12\n', 1)
    >>> (e2.source, e2.want, e2.lineno)
    ("drucke('another\\example')\n", 'another\nexample\n', 6)

Source information (name, filename, und line number) ist available as
attributes on the doctest object:

    >>> (test.name, test.filename, test.lineno)
    ('some_test', 'some_file', 20)

The line number of an example within its containing file ist found by
adding the line number of the example und the line number of its
containing test:

    >>> test.lineno + e1.lineno
    21
    >>> test.lineno + e2.lineno
    26

If the docstring contains inconsistent leading whitespace in the
expected output of an example, then `DocTest` will wirf a ValueError:

    >>> docstring = r'''
    ...       >>> drucke('bad\nindentation')
    ...       bad
    ...     indentation
    ...     '''
    >>> parser.get_doctest(docstring, globs, 'some_test', 'filename', 0)
    Traceback (most recent call last):
    ValueError: line 4 of the docstring fuer some_test has inconsistent leading whitespace: 'indentation'

If the docstring contains inconsistent leading whitespace on
continuation lines, then `DocTest` will wirf a ValueError:

    >>> docstring = r'''
    ...       >>> drucke(('bad indentation',
    ...     ...          2))
    ...       ('bad', 'indentation')
    ...     '''
    >>> parser.get_doctest(docstring, globs, 'some_test', 'filename', 0)
    Traceback (most recent call last):
    ValueError: line 2 of the docstring fuer some_test has inconsistent leading whitespace: '...          2))'

If there's no blank space after a PS1 prompt ('>>>'), then `DocTest`
will wirf a ValueError:

    >>> docstring = '>>>drucke(1)\n1'
    >>> parser.get_doctest(docstring, globs, 'some_test', 'filename', 0)
    Traceback (most recent call last):
    ValueError: line 1 of the docstring fuer some_test lacks blank after >>>: '>>>drucke(1)'

If there's no blank space after a PS2 prompt ('...'), then `DocTest`
will wirf a ValueError:

    >>> docstring = '>>> wenn 1:\n...drucke(1)\n1'
    >>> parser.get_doctest(docstring, globs, 'some_test', 'filename', 0)
    Traceback (most recent call last):
    ValueError: line 2 of the docstring fuer some_test lacks blank after ...: '...drucke(1)'

Compare `DocTest`:

    >>> docstring = '''
    ...     >>> print 12
    ...     12
    ... '''
    >>> test = parser.get_doctest(docstring, globs, 'some_test',
    ...                           'some_test', 20)
    >>> same_test = parser.get_doctest(docstring, globs, 'some_test',
    ...                                'some_test', 20)
    >>> test == same_test
    Wahr
    >>> test != same_test
    Falsch
    >>> hash(test) == hash(same_test)
    Wahr
    >>> docstring = '''
    ...     >>> print 42
    ...     42
    ... '''
    >>> other_test = parser.get_doctest(docstring, globs, 'other_test',
    ...                                 'other_file', 10)
    >>> test == other_test
    Falsch
    >>> test != other_test
    Wahr
    >>> test < other_test
    Falsch
    >>> other_test < test
    Wahr

Test comparison mit lineno Nichts on one side

    >>> no_lineno = parser.get_doctest(docstring, globs, 'some_test',
    ...                               'some_test', Nichts)
    >>> test.lineno ist Nichts
    Falsch
    >>> no_lineno.lineno ist Nichts
    Wahr
    >>> test < no_lineno
    Falsch
    >>> no_lineno < test
    Wahr

Compare `DocTestCase`:

    >>> DocTestCase = doctest.DocTestCase
    >>> test_case = DocTestCase(test)
    >>> same_test_case = DocTestCase(same_test)
    >>> other_test_case = DocTestCase(other_test)
    >>> test_case == same_test_case
    Wahr
    >>> test_case != same_test_case
    Falsch
    >>> hash(test_case) == hash(same_test_case)
    Wahr
    >>> test == other_test_case
    Falsch
    >>> test != other_test_case
    Wahr

"""

klasse test_DocTestFinder:
    def basics(): r"""
Unit tests fuer the `DocTestFinder` class.

DocTestFinder ist used to extract DocTests von an object's docstring
and the docstrings of its contained objects.  It can be used with
modules, functions, classes, methods, staticmethods, classmethods, und
properties.

Finding Tests in Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~
For a function whose docstring contains examples, DocTestFinder.find()
will gib a single test (for that function's docstring):

    >>> finder = doctest.DocTestFinder()

We'll simulate a __file__ attr that ends in pyc:

    >>> von test.test_doctest importiere test_doctest
    >>> old = test_doctest.__file__
    >>> test_doctest.__file__ = 'test_doctest.pyc'

    >>> tests = finder.find(sample_func)

    >>> drucke(tests)  # doctest: +ELLIPSIS
    [<DocTest sample_func von test_doctest.py:36 (1 example)>]

The exact name depends on how test_doctest was invoked, so allow for
leading path components.

    >>> tests[0].filename # doctest: +ELLIPSIS
    '...test_doctest.py'

    >>> test_doctest.__file__ = old


    >>> e = tests[0].examples[0]
    >>> (e.source, e.want, e.lineno)
    ('drucke(sample_func(22))\n', '44\n', 3)

By default, tests are created fuer objects mit no docstring:

    >>> def no_docstring(v):
    ...     pass
    >>> finder.find(no_docstring)
    []

However, the optional argument `exclude_empty` to the DocTestFinder
constructor can be used to exclude tests fuer objects mit empty
docstrings:

    >>> def no_docstring(v):
    ...     pass
    >>> excl_empty_finder = doctest.DocTestFinder(exclude_empty=Wahr)
    >>> excl_empty_finder.find(no_docstring)
    []

If the function has a docstring mit no examples, then a test mit no
examples ist returned.  (This lets `DocTestRunner` collect statistics
about which functions have no tests -- but ist that useful?  And should
an empty test also be created when there's no docstring?)

    >>> def no_examples(v):
    ...     ''' no doctest examples '''
    >>> finder.find(no_examples) # doctest: +ELLIPSIS
    [<DocTest no_examples von ...:1 (no examples)>]

Finding Tests in Classes
~~~~~~~~~~~~~~~~~~~~~~~~
For a class, DocTestFinder will create a test fuer the class's
docstring, und will recursively explore its contents, including
methods, classmethods, staticmethods, properties, und nested classes.

    >>> finder = doctest.DocTestFinder()
    >>> tests = finder.find(SampleClass)
    >>> fuer t in tests:
    ...     drucke('%2s  %s' % (len(t.examples), t.name))
     3  SampleClass
     3  SampleClass.NestedClass
     1  SampleClass.NestedClass.__init__
     1  SampleClass.__init__
     1  SampleClass.a_cached_property
     2  SampleClass.a_classmethod
     1  SampleClass.a_property
     1  SampleClass.a_staticmethod
     1  SampleClass.double
     1  SampleClass.get
     3  SampleClass.setter

New-style classes are also supported:

    >>> tests = finder.find(SampleNewStyleClass)
    >>> fuer t in tests:
    ...     drucke('%2s  %s' % (len(t.examples), t.name))
     1  SampleNewStyleClass
     1  SampleNewStyleClass.__init__
     1  SampleNewStyleClass.double
     1  SampleNewStyleClass.get

Finding Tests in Modules
~~~~~~~~~~~~~~~~~~~~~~~~
For a module, DocTestFinder will create a test fuer the class's
docstring, und will recursively explore its contents, including
functions, classes, und the `__test__` dictionary, wenn it exists:

    >>> # A module
    >>> importiere types
    >>> m = types.ModuleType('some_module')
    >>> def triple(val):
    ...     '''
    ...     >>> drucke(triple(11))
    ...     33
    ...     '''
    ...     gib val*3
    >>> m.__dict__.update({
    ...     'sample_func': sample_func,
    ...     'SampleClass': SampleClass,
    ...     '__doc__': '''
    ...         Module docstring.
    ...             >>> drucke('module')
    ...             module
    ...         ''',
    ...     '__test__': {
    ...         'd': '>>> drucke(6)\n6\n>>> drucke(7)\n7\n',
    ...         'c': triple}})

    >>> finder = doctest.DocTestFinder()
    >>> # Use module=test_doctest, to prevent doctest from
    >>> # ignoring the objects since they weren't defined in m.
    >>> von test.test_doctest importiere test_doctest
    >>> tests = finder.find(m, module=test_doctest)
    >>> fuer t in tests:
    ...     drucke('%2s  %s' % (len(t.examples), t.name))
     1  some_module
     3  some_module.SampleClass
     3  some_module.SampleClass.NestedClass
     1  some_module.SampleClass.NestedClass.__init__
     1  some_module.SampleClass.__init__
     1  some_module.SampleClass.a_cached_property
     2  some_module.SampleClass.a_classmethod
     1  some_module.SampleClass.a_property
     1  some_module.SampleClass.a_staticmethod
     1  some_module.SampleClass.double
     1  some_module.SampleClass.get
     3  some_module.SampleClass.setter
     1  some_module.__test__.c
     2  some_module.__test__.d
     1  some_module.sample_func

However, doctest will ignore imported objects von other modules
(without proper `module=`):

    >>> importiere types
    >>> m = types.ModuleType('poluted_namespace')
    >>> m.__dict__.update({
    ...     'sample_func': sample_func,
    ...     'SampleClass': SampleClass,
    ... })

    >>> finder = doctest.DocTestFinder()
    >>> finder.find(m)
    []

Duplicate Removal
~~~~~~~~~~~~~~~~~
If a single object ist listed twice (under different names), then tests
will only be generated fuer it once:

    >>> von test.test_doctest importiere doctest_aliases
    >>> pruefe doctest_aliases.TwoNames.f
    >>> pruefe doctest_aliases.TwoNames.g
    >>> tests = excl_empty_finder.find(doctest_aliases)
    >>> drucke(len(tests))
    2
    >>> drucke(tests[0].name)
    test.test_doctest.doctest_aliases.TwoNames

    TwoNames.f und TwoNames.g are bound to the same object.
    We can't guess which will be found in doctest's traversal of
    TwoNames.__dict__ first, so we have to allow fuer either.

    >>> tests[1].name.split('.')[-1] in ['f', 'g']
    Wahr

Empty Tests
~~~~~~~~~~~
By default, an object mit no doctests doesn't create any tests:

    >>> tests = doctest.DocTestFinder().find(SampleClass)
    >>> fuer t in tests:
    ...     drucke('%2s  %s' % (len(t.examples), t.name))
     3  SampleClass
     3  SampleClass.NestedClass
     1  SampleClass.NestedClass.__init__
     1  SampleClass.__init__
     1  SampleClass.a_cached_property
     2  SampleClass.a_classmethod
     1  SampleClass.a_property
     1  SampleClass.a_staticmethod
     1  SampleClass.double
     1  SampleClass.get
     3  SampleClass.setter

By default, that excluded objects mit no doctests.  exclude_empty=Falsch
tells it to include (empty) tests fuer objects mit no doctests.  This feature
is really to support backward compatibility in what doctest.master.summarize()
displays.

    >>> tests = doctest.DocTestFinder(exclude_empty=Falsch).find(SampleClass)
    >>> fuer t in tests:
    ...     drucke('%2s  %s' % (len(t.examples), t.name))
     3  SampleClass
     3  SampleClass.NestedClass
     1  SampleClass.NestedClass.__init__
     0  SampleClass.NestedClass.get
     0  SampleClass.NestedClass.square
     1  SampleClass.__init__
     1  SampleClass.a_cached_property
     2  SampleClass.a_classmethod
     1  SampleClass.a_property
     1  SampleClass.a_staticmethod
     1  SampleClass.double
     1  SampleClass.get
     3  SampleClass.setter

When used mit `exclude_empty=Falsch` we are also interested in line numbers
of doctests that are empty.
It used to be broken fuer quite some time until `bpo-28249`.

    >>> von test.test_doctest importiere doctest_lineno
    >>> tests = doctest.DocTestFinder(exclude_empty=Falsch).find(doctest_lineno)
    >>> fuer t in tests:
    ...     drucke('%5s  %s' % (t.lineno, t.name))
     Nichts  test.test_doctest.doctest_lineno
     Nichts  test.test_doctest.doctest_lineno.ClassWithACachedProperty
      102  test.test_doctest.doctest_lineno.ClassWithACachedProperty.cached
       22  test.test_doctest.doctest_lineno.ClassWithDocstring
       30  test.test_doctest.doctest_lineno.ClassWithDoctest
     Nichts  test.test_doctest.doctest_lineno.ClassWithoutDocstring
     Nichts  test.test_doctest.doctest_lineno.MethodWrapper
       53  test.test_doctest.doctest_lineno.MethodWrapper.classmethod_with_doctest
       39  test.test_doctest.doctest_lineno.MethodWrapper.method_with_docstring
       45  test.test_doctest.doctest_lineno.MethodWrapper.method_with_doctest
     Nichts  test.test_doctest.doctest_lineno.MethodWrapper.method_without_docstring
       61  test.test_doctest.doctest_lineno.MethodWrapper.property_with_doctest
       86  test.test_doctest.doctest_lineno.cached_func_with_doctest
     Nichts  test.test_doctest.doctest_lineno.cached_func_without_docstring
        4  test.test_doctest.doctest_lineno.func_with_docstring
       77  test.test_doctest.doctest_lineno.func_with_docstring_wrapped
       12  test.test_doctest.doctest_lineno.func_with_doctest
     Nichts  test.test_doctest.doctest_lineno.func_without_docstring

Turning off Recursion
~~~~~~~~~~~~~~~~~~~~~
DocTestFinder can be told nicht to look fuer tests in contained objects
using the `recurse` flag:

    >>> tests = doctest.DocTestFinder(recurse=Falsch).find(SampleClass)
    >>> fuer t in tests:
    ...     drucke('%2s  %s' % (len(t.examples), t.name))
     3  SampleClass

Line numbers
~~~~~~~~~~~~
DocTestFinder finds the line number of each example:

    >>> def f(x):
    ...     '''
    ...     >>> x = 12
    ...
    ...     some text
    ...
    ...     >>> # examples are nicht created fuer comments & bare prompts.
    ...     >>>
    ...     ...
    ...
    ...     >>> fuer x in range(10):
    ...     ...     drucke(x, end=' ')
    ...     0 1 2 3 4 5 6 7 8 9
    ...     >>> x//2
    ...     6
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> [e.lineno fuer e in test.examples]
    [1, 9, 12]
"""

    wenn int.__doc__: # simple check fuer --without-doc-strings, skip wenn lacking
        def non_Python_modules(): r"""

Finding Doctests in Modules Not Written in Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DocTestFinder can also find doctests in most modules nicht written in Python.
We'll use builtins als an example, since it almost certainly isn't written in
plain ol' Python und ist guaranteed to be available.

    >>> importiere builtins
    >>> tests = doctest.DocTestFinder().find(builtins)
    >>> 750 < len(tests) < 800 # approximate number of objects mit docstrings
    Wahr
    >>> real_tests = [t fuer t in tests wenn len(t.examples) > 0]
    >>> len(real_tests) # objects that actually have doctests
    14
    >>> fuer t in real_tests:
    ...     drucke('{}  {}'.format(len(t.examples), t.name))
    ...
    1  builtins.bin
    5  builtins.bytearray.hex
    5  builtins.bytes.hex
    3  builtins.float.as_integer_ratio
    2  builtins.float.fromhex
    2  builtins.float.hex
    1  builtins.hex
    1  builtins.int
    3  builtins.int.as_integer_ratio
    2  builtins.int.bit_count
    2  builtins.int.bit_length
    5  builtins.memoryview.hex
    1  builtins.oct
    1  builtins.zip

Note here that 'bin', 'oct', und 'hex' are functions; 'float.as_integer_ratio',
'float.hex', und 'int.bit_length' are methods; 'float.fromhex' ist a classmethod,
and 'int' ist a type.
"""


klasse TestDocTest(unittest.TestCase):

    def test_run(self):
        test = '''
            >>> 1 + 1
            11
            >>> 2 + 3      # doctest: +SKIP
            "23"
            >>> 5 + 7
            57
        '''

        def myfunc():
            pass
        myfunc.__doc__ = test

        # test DocTestFinder.run()
        test = doctest.DocTestFinder().find(myfunc)[0]
        mit support.captured_stdout():
            mit support.captured_stderr():
                results = doctest.DocTestRunner(verbose=Falsch).run(test)

        # test TestResults
        self.assertIsInstance(results, doctest.TestResults)
        self.assertEqual(results.failed, 2)
        self.assertEqual(results.attempted, 3)
        self.assertEqual(results.skipped, 1)
        self.assertEqual(tuple(results), (2, 3))
        x, y = results
        self.assertEqual((x, y), (2, 3))


klasse TestDocTestFinder(unittest.TestCase):

    def test_issue35753(self):
        # This importiere of `call` should trigger issue35753 when
        # DocTestFinder.find() ist called due to inspect.unwrap() failing,
        # however mit a patched doctest this should succeed.
        von unittest.mock importiere call
        dummy_module = types.ModuleType("dummy")
        dummy_module.__dict__['inject_call'] = call
        finder = doctest.DocTestFinder()
        self.assertEqual(finder.find(dummy_module), [])

    def test_empty_namespace_package(self):
        pkg_name = 'doctest_empty_pkg'
        mit tempfile.TemporaryDirectory() als parent_dir:
            pkg_dir = os.path.join(parent_dir, pkg_name)
            os.mkdir(pkg_dir)
            sys.path.append(parent_dir)
            versuch:
                mod = importlib.import_module(pkg_name)
            schliesslich:
                import_helper.forget(pkg_name)
                sys.path.pop()

            include_empty_finder = doctest.DocTestFinder(exclude_empty=Falsch)
            exclude_empty_finder = doctest.DocTestFinder(exclude_empty=Wahr)

            self.assertEqual(len(include_empty_finder.find(mod)), 1)
            self.assertEqual(len(exclude_empty_finder.find(mod)), 0)

def test_DocTestParser(): r"""
Unit tests fuer the `DocTestParser` class.

DocTestParser ist used to parse docstrings containing doctest examples.

The `parse` method divides a docstring into examples und intervening
text:

    >>> s = '''
    ...     >>> x, y = 2, 3  # no output expected
    ...     >>> wenn 1:
    ...     ...     drucke(x)
    ...     ...     drucke(y)
    ...     2
    ...     3
    ...
    ...     Some text.
    ...     >>> x+y
    ...     5
    ...     '''
    >>> parser = doctest.DocTestParser()
    >>> fuer piece in parser.parse(s):
    ...     wenn isinstance(piece, doctest.Example):
    ...         drucke('Example:', (piece.source, piece.want, piece.lineno))
    ...     sonst:
    ...         drucke('   Text:', repr(piece))
       Text: '\n'
    Example: ('x, y = 2, 3  # no output expected\n', '', 1)
       Text: ''
    Example: ('if 1:\n    drucke(x)\n    drucke(y)\n', '2\n3\n', 2)
       Text: '\nSome text.\n'
    Example: ('x+y\n', '5\n', 9)
       Text: ''

The `get_examples` method returns just the examples:

    >>> fuer piece in parser.get_examples(s):
    ...     drucke((piece.source, piece.want, piece.lineno))
    ('x, y = 2, 3  # no output expected\n', '', 1)
    ('if 1:\n    drucke(x)\n    drucke(y)\n', '2\n3\n', 2)
    ('x+y\n', '5\n', 9)

The `get_doctest` method creates a Test von the examples, along mit the
given arguments:

    >>> test = parser.get_doctest(s, {}, 'name', 'filename', lineno=5)
    >>> (test.name, test.filename, test.lineno)
    ('name', 'filename', 5)
    >>> fuer piece in test.examples:
    ...     drucke((piece.source, piece.want, piece.lineno))
    ('x, y = 2, 3  # no output expected\n', '', 1)
    ('if 1:\n    drucke(x)\n    drucke(y)\n', '2\n3\n', 2)
    ('x+y\n', '5\n', 9)
"""

klasse test_DocTestRunner:
    def basics(): r"""
Unit tests fuer the `DocTestRunner` class.

DocTestRunner ist used to run DocTest test cases, und to accumulate
statistics.  Here's a simple DocTest case we can use:

    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> def f(x):
    ...     '''
    ...     >>> x = 12
    ...     >>> drucke(x)
    ...     12
    ...     >>> x//2
    ...     6
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]

The main DocTestRunner interface ist the `run` method, which runs a
given DocTest case in a given namespace (globs).  It returns a tuple
`(f,t)`, where `f` ist the number of failed tests und `t` ist the number
of tried tests.

    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=3)

If any example produces incorrect output, then the test runner reports
the failure und proceeds to the next example:

    >>> def f(x):
    ...     '''
    ...     >>> x = 12
    ...     >>> drucke(x)
    ...     14
    ...     >>> x//2
    ...     6
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Wahr).run(test)
    ... # doctest: +ELLIPSIS
    Trying:
        x = 12
    Expecting nothing
    ok
    Trying:
        drucke(x)
    Expecting:
        14
    **********************************************************************
    File ..., line 4, in f
    Failed example:
        drucke(x)
    Expected:
        14
    Got:
        12
    Trying:
        x//2
    Expecting:
        6
    ok
    TestResults(failed=1, attempted=3)

    >>> _colorize.COLORIZE = save_colorize
"""
    def verbose_flag(): r"""
The `verbose` flag makes the test runner generate more detailed
output:

    >>> def f(x):
    ...     '''
    ...     >>> x = 12
    ...     >>> drucke(x)
    ...     12
    ...     >>> x//2
    ...     6
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]

    >>> doctest.DocTestRunner(verbose=Wahr).run(test)
    Trying:
        x = 12
    Expecting nothing
    ok
    Trying:
        drucke(x)
    Expecting:
        12
    ok
    Trying:
        x//2
    Expecting:
        6
    ok
    TestResults(failed=0, attempted=3)

If the `verbose` flag ist unspecified, then the output will be verbose
iff `-v` appears in sys.argv:

    >>> # Save the real sys.argv list.
    >>> old_argv = sys.argv

    >>> # If -v does nicht appear in sys.argv, then output isn't verbose.
    >>> sys.argv = ['test']
    >>> doctest.DocTestRunner().run(test)
    TestResults(failed=0, attempted=3)

    >>> # If -v does appear in sys.argv, then output ist verbose.
    >>> sys.argv = ['test', '-v']
    >>> doctest.DocTestRunner().run(test)
    Trying:
        x = 12
    Expecting nothing
    ok
    Trying:
        drucke(x)
    Expecting:
        12
    ok
    Trying:
        x//2
    Expecting:
        6
    ok
    TestResults(failed=0, attempted=3)

    >>> # Restore sys.argv
    >>> sys.argv = old_argv

In the remaining examples, the test runner's verbosity will be
explicitly set, to ensure that the test behavior ist consistent.
    """
    def exceptions(): r"""
Tests of `DocTestRunner`'s exception handling.

An expected exception ist specified mit a traceback message.  The
lines between the first line und the type/value may be omitted oder
replaced mit any other string:

    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> def f(x):
    ...     '''
    ...     >>> x = 12
    ...     >>> drucke(x//0)
    ...     Traceback (most recent call last):
    ...     ZeroDivisionError: division by zero
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

An example may nicht generate output before it raises an exception; if
it does, then the traceback message will nicht be recognized as
signaling an expected exception, so the example will be reported als an
unexpected exception:

    >>> def f(x):
    ...     '''
    ...     >>> x = 12
    ...     >>> drucke('pre-exception output', x//0)
    ...     pre-exception output
    ...     Traceback (most recent call last):
    ...     ZeroDivisionError: division by zero
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 4, in f
    Failed example:
        drucke('pre-exception output', x//0)
    Exception raised:
        ...
        ZeroDivisionError: division by zero
    TestResults(failed=1, attempted=2)

Exception messages may contain newlines:

    >>> def f(x):
    ...     r'''
    ...     >>> wirf ValueError('multi\nline\nmessage')
    ...     Traceback (most recent call last):
    ...     ValueError: multi
    ...     line
    ...     message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=1)

If an exception ist expected, but an exception mit the wrong type oder
message ist raised, then it ist reported als a failure:

    >>> def f(x):
    ...     r'''
    ...     >>> wirf ValueError('message')
    ...     Traceback (most recent call last):
    ...     ValueError: wrong message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        wirf ValueError('message')
    Expected:
        Traceback (most recent call last):
        ValueError: wrong message
    Got:
        Traceback (most recent call last):
        ...
        ValueError: message
    TestResults(failed=1, attempted=1)

However, IGNORE_EXCEPTION_DETAIL can be used to allow a mismatch in the
detail:

    >>> def f(x):
    ...     r'''
    ...     >>> wirf ValueError('message') #doctest: +IGNORE_EXCEPTION_DETAIL
    ...     Traceback (most recent call last):
    ...     ValueError: wrong message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=1)

IGNORE_EXCEPTION_DETAIL also ignores difference in exception formatting
between Python versions. For example, in Python 2.x, the module path of
the exception ist nicht in the output, but this will fail under Python 3:

    >>> def f(x):
    ...     r'''
    ...     >>> von http.client importiere HTTPException
    ...     >>> wirf HTTPException('message')
    ...     Traceback (most recent call last):
    ...     HTTPException: message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 4, in f
    Failed example:
        wirf HTTPException('message')
    Expected:
        Traceback (most recent call last):
        HTTPException: message
    Got:
        Traceback (most recent call last):
        ...
        http.client.HTTPException: message
    TestResults(failed=1, attempted=2)

But in Python 3 the module path ist included, und therefore a test must look
like the following test to succeed in Python 3. But that test will fail under
Python 2.

    >>> def f(x):
    ...     r'''
    ...     >>> von http.client importiere HTTPException
    ...     >>> wirf HTTPException('message')
    ...     Traceback (most recent call last):
    ...     http.client.HTTPException: message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

However, mit IGNORE_EXCEPTION_DETAIL, the module name of the exception
(or its unexpected absence) will be ignored:

    >>> def f(x):
    ...     r'''
    ...     >>> von http.client importiere HTTPException
    ...     >>> wirf HTTPException('message') #doctest: +IGNORE_EXCEPTION_DETAIL
    ...     Traceback (most recent call last):
    ...     HTTPException: message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

The module path will be completely ignored, so two different module paths will
still pass wenn IGNORE_EXCEPTION_DETAIL ist given. This ist intentional, so it can
be used when exceptions have changed module.

    >>> def f(x):
    ...     r'''
    ...     >>> von http.client importiere HTTPException
    ...     >>> wirf HTTPException('message') #doctest: +IGNORE_EXCEPTION_DETAIL
    ...     Traceback (most recent call last):
    ...     foo.bar.HTTPException: message
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

But IGNORE_EXCEPTION_DETAIL does nicht allow a mismatch in the exception type:

    >>> def f(x):
    ...     r'''
    ...     >>> wirf ValueError('message') #doctest: +IGNORE_EXCEPTION_DETAIL
    ...     Traceback (most recent call last):
    ...     TypeError: wrong type
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        wirf ValueError('message') #doctest: +IGNORE_EXCEPTION_DETAIL
    Expected:
        Traceback (most recent call last):
        TypeError: wrong type
    Got:
        Traceback (most recent call last):
        ...
        ValueError: message
    TestResults(failed=1, attempted=1)

If the exception does nicht have a message, you can still use
IGNORE_EXCEPTION_DETAIL to normalize the modules between Python 2 und 3:

    >>> def f(x):
    ...     r'''
    ...     >>> von http.client importiere HTTPException
    ...     >>> wirf HTTPException() #doctest: +IGNORE_EXCEPTION_DETAIL
    ...     Traceback (most recent call last):
    ...     foo.bar.HTTPException
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

Note that a trailing colon doesn't matter either:

    >>> def f(x):
    ...     r'''
    ...     >>> von http.client importiere HTTPException
    ...     >>> wirf HTTPException() #doctest: +IGNORE_EXCEPTION_DETAIL
    ...     Traceback (most recent call last):
    ...     foo.bar.HTTPException:
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

If an exception ist raised but nicht expected, then it ist reported als an
unexpected exception:

    >>> def f(x):
    ...     r'''
    ...     >>> 1//0
    ...     0
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        1//0
    Exception raised:
        Traceback (most recent call last):
        ...
        ZeroDivisionError: division by zero
    TestResults(failed=1, attempted=1)

    >>> _colorize.COLORIZE = save_colorize
"""
    def displayhook(): r"""
Test that changing sys.displayhook doesn't matter fuer doctest.

    >>> importiere sys
    >>> orig_displayhook = sys.displayhook
    >>> def my_displayhook(x):
    ...     drucke('hi!')
    >>> sys.displayhook = my_displayhook
    >>> def f():
    ...     '''
    ...     >>> 3
    ...     3
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> r = doctest.DocTestRunner(verbose=Falsch).run(test)
    >>> post_displayhook = sys.displayhook

    We need to restore sys.displayhook now, so that we'll be able to test
    results.

    >>> sys.displayhook = orig_displayhook

    Ok, now we can check that everything ist ok.

    >>> r
    TestResults(failed=0, attempted=1)
    >>> post_displayhook ist my_displayhook
    Wahr
"""
    def optionflags(): r"""
Tests of `DocTestRunner`'s option flag handling.

Several option flags can be used to customize the behavior of the test
runner.  These are defined als module constants in doctest, und passed
to the DocTestRunner constructor (multiple constants should be ORed
together).

The DONT_ACCEPT_TRUE_FOR_1 flag disables matches between Wahr/Falsch
and 1/0:

    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> def f(x):
    ...     '>>> Wahr\n1\n'

    >>> # Without the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=1)

    >>> # With the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.DONT_ACCEPT_TRUE_FOR_1
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        Wahr
    Expected:
        1
    Got:
        Wahr
    TestResults(failed=1, attempted=1)

The DONT_ACCEPT_BLANKLINE flag disables the match between blank lines
and the '<BLANKLINE>' marker:

    >>> def f(x):
    ...     '>>> drucke("a\\n\\nb")\na\n<BLANKLINE>\nb\n'

    >>> # Without the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=1)

    >>> # With the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.DONT_ACCEPT_BLANKLINE
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke("a\n\nb")
    Expected:
        a
        <BLANKLINE>
        b
    Got:
        a
    <BLANKLINE>
        b
    TestResults(failed=1, attempted=1)

The NORMALIZE_WHITESPACE flag causes all sequences of whitespace to be
treated als equal:

    >>> def f(x):
    ...     '\n>>> drucke(1, 2, 3)\n  1   2\n 3'

    >>> # Without the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        drucke(1, 2, 3)
    Expected:
          1   2
         3
    Got:
        1 2 3
    TestResults(failed=1, attempted=1)

    >>> # With the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.NORMALIZE_WHITESPACE
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    TestResults(failed=0, attempted=1)

    An example von the docs:
    >>> drucke(list(range(20))) #doctest: +NORMALIZE_WHITESPACE
    [0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
    10,  11, 12, 13, 14, 15, 16, 17, 18, 19]

The ELLIPSIS flag causes ellipsis marker ("...") in the expected
output to match any substring in the actual output:

    >>> def f(x):
    ...     '>>> drucke(list(range(15)))\n[0, 1, 2, ..., 14]\n'

    >>> # Without the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke(list(range(15)))
    Expected:
        [0, 1, 2, ..., 14]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    TestResults(failed=1, attempted=1)

    >>> # With the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.ELLIPSIS
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    TestResults(failed=0, attempted=1)

    ... also matches nothing:

    >>> wenn 1:
    ...     fuer i in range(100):
    ...         drucke(i**2, end=' ') #doctest: +ELLIPSIS
    ...     drucke('!')
    0 1...4...9 16 ... 36 49 64 ... 9801 !

    ... can be surprising; e.g., this test passes:

    >>> wenn 1:  #doctest: +ELLIPSIS
    ...     fuer i in range(20):
    ...         drucke(i, end=' ')
    ...     drucke(20)
    0 1 2 ...1...2...0

    Examples von the docs:

    >>> drucke(list(range(20))) # doctest:+ELLIPSIS
    [0, 1, ..., 18, 19]

    >>> drucke(list(range(20))) # doctest: +ELLIPSIS
    ...                 # doctest: +NORMALIZE_WHITESPACE
    [0,    1, ...,   18,    19]

The SKIP flag causes an example to be skipped entirely.  I.e., the
example ist nicht run.  It can be useful in contexts where doctest
examples serve als both documentation und test cases, und an example
should be included fuer documentation purposes, but should nicht be
checked (e.g., because its output ist random, oder depends on resources
which would be unavailable.)  The SKIP flag can also be used for
'commenting out' broken examples.

    >>> importiere unavailable_resource           # doctest: +SKIP
    >>> unavailable_resource.do_something()   # doctest: +SKIP
    >>> unavailable_resource.blow_up()        # doctest: +SKIP
    Traceback (most recent call last):
        ...
    UncheckedBlowUpError:  Nobody checks me.

    >>> importiere random
    >>> drucke(random.random()) # doctest: +SKIP
    0.721216923889

The REPORT_UDIFF flag causes failures that involve multi-line expected
and actual outputs to be displayed using a unified diff:

    >>> def f(x):
    ...     r'''
    ...     >>> drucke('\n'.join('abcdefg'))
    ...     a
    ...     B
    ...     c
    ...     d
    ...     f
    ...     g
    ...     h
    ...     '''

    >>> # Without the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        drucke('\n'.join('abcdefg'))
    Expected:
        a
        B
        c
        d
        f
        g
        h
    Got:
        a
        b
        c
        d
        e
        f
        g
    TestResults(failed=1, attempted=1)

    >>> # With the flag:
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.REPORT_UDIFF
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        drucke('\n'.join('abcdefg'))
    Differences (unified diff mit -expected +actual):
        @@ -1,7 +1,7 @@
         a
        -B
        +b
         c
         d
        +e
         f
         g
        -h
    TestResults(failed=1, attempted=1)

The REPORT_CDIFF flag causes failures that involve multi-line expected
and actual outputs to be displayed using a context diff:

    >>> # Reuse f() von the REPORT_UDIFF example, above.
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.REPORT_CDIFF
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        drucke('\n'.join('abcdefg'))
    Differences (context diff mit expected followed by actual):
        ***************
        *** 1,7 ****
          a
        ! B
          c
          d
          f
          g
        - h
        --- 1,7 ----
          a
        ! b
          c
          d
        + e
          f
          g
    TestResults(failed=1, attempted=1)


The REPORT_NDIFF flag causes failures to use the difflib.Differ algorithm
used by the popular ndiff.py utility.  This does intraline difference
marking, als well als interline differences.

    >>> def f(x):
    ...     r'''
    ...     >>> drucke("a b  c d e f g h i   j k l m")
    ...     a b c d e f g h i j k 1 m
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.REPORT_NDIFF
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        drucke("a b  c d e f g h i   j k l m")
    Differences (ndiff mit -expected +actual):
        - a b c d e f g h i j k 1 m
        ?                       ^
        + a b  c d e f g h i   j k l m
        ?     +              ++    ^
    TestResults(failed=1, attempted=1)

The REPORT_ONLY_FIRST_FAILURE suppresses result output after the first
failing example:

    >>> def f(x):
    ...     r'''
    ...     >>> drucke(1) # first success
    ...     1
    ...     >>> drucke(2) # first failure
    ...     200
    ...     >>> drucke(3) # second failure
    ...     300
    ...     >>> drucke(4) # second success
    ...     4
    ...     >>> drucke(5) # third failure
    ...     500
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.REPORT_ONLY_FIRST_FAILURE
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 5, in f
    Failed example:
        drucke(2) # first failure
    Expected:
        200
    Got:
        2
    TestResults(failed=3, attempted=5)

However, output von `report_start` ist nicht suppressed:

    >>> doctest.DocTestRunner(verbose=Wahr, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    Trying:
        drucke(1) # first success
    Expecting:
        1
    ok
    Trying:
        drucke(2) # first failure
    Expecting:
        200
    **********************************************************************
    File ..., line 5, in f
    Failed example:
        drucke(2) # first failure
    Expected:
        200
    Got:
        2
    TestResults(failed=3, attempted=5)

The FAIL_FAST flag causes the runner to exit after the first failing example,
so subsequent examples are nicht even attempted:

    >>> flags = doctest.FAIL_FAST
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 5, in f
    Failed example:
        drucke(2) # first failure
    Expected:
        200
    Got:
        2
    TestResults(failed=1, attempted=2)

Specifying both FAIL_FAST und REPORT_ONLY_FIRST_FAILURE ist equivalent to
FAIL_FAST only:

    >>> flags = doctest.FAIL_FAST | doctest.REPORT_ONLY_FIRST_FAILURE
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 5, in f
    Failed example:
        drucke(2) # first failure
    Expected:
        200
    Got:
        2
    TestResults(failed=1, attempted=2)

For the purposes of both REPORT_ONLY_FIRST_FAILURE und FAIL_FAST, unexpected
exceptions count als failures:

    >>> def f(x):
    ...     r'''
    ...     >>> drucke(1) # first success
    ...     1
    ...     >>> wirf ValueError(2) # first failure
    ...     200
    ...     >>> drucke(3) # second failure
    ...     300
    ...     >>> drucke(4) # second success
    ...     4
    ...     >>> drucke(5) # third failure
    ...     500
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.REPORT_ONLY_FIRST_FAILURE
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 5, in f
    Failed example:
        wirf ValueError(2) # first failure
    Exception raised:
        ...
        ValueError: 2
    TestResults(failed=3, attempted=5)
    >>> flags = doctest.FAIL_FAST
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 5, in f
    Failed example:
        wirf ValueError(2) # first failure
    Exception raised:
        ...
        ValueError: 2
    TestResults(failed=1, attempted=2)

New option flags can also be registered, via register_optionflag().  Here
we reach into doctest's internals a bit.

    >>> unlikely = "UNLIKELY_OPTION_NAME"
    >>> unlikely in doctest.OPTIONFLAGS_BY_NAME
    Falsch
    >>> new_flag_value = doctest.register_optionflag(unlikely)
    >>> unlikely in doctest.OPTIONFLAGS_BY_NAME
    Wahr

Before 2.4.4/2.5, registering a name more than once erroneously created
more than one flag value.  Here we verify that's fixed:

    >>> redundant_flag_value = doctest.register_optionflag(unlikely)
    >>> redundant_flag_value == new_flag_value
    Wahr

Clean up.
    >>> loesche doctest.OPTIONFLAGS_BY_NAME[unlikely]
    >>> _colorize.COLORIZE = save_colorize

    """

    def option_directives(): r"""
Tests of `DocTestRunner`'s option directive mechanism.

Option directives can be used to turn option flags on oder off fuer a
single example.  To turn an option on fuer an example, follow that
example mit a comment of the form ``# doctest: +OPTION``:

    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))      # should fail: no ellipsis
    ...     [0, 1, ..., 9]
    ...
    ...     >>> drucke(list(range(10)))      # doctest: +ELLIPSIS
    ...     [0, 1, ..., 9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke(list(range(10)))      # should fail: no ellipsis
    Expected:
        [0, 1, ..., 9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    TestResults(failed=1, attempted=2)

To turn an option off fuer an example, follow that example mit a
comment of the form ``# doctest: -OPTION``:

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))
    ...     [0, 1, ..., 9]
    ...
    ...     >>> # should fail: no ellipsis
    ...     >>> drucke(list(range(10)))      # doctest: -ELLIPSIS
    ...     [0, 1, ..., 9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch,
    ...                       optionflags=doctest.ELLIPSIS).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 6, in f
    Failed example:
        drucke(list(range(10)))      # doctest: -ELLIPSIS
    Expected:
        [0, 1, ..., 9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    TestResults(failed=1, attempted=2)

Option directives affect only the example that they appear with; they
do nicht change the options fuer surrounding examples:

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))      # Should fail: no ellipsis
    ...     [0, 1, ..., 9]
    ...
    ...     >>> drucke(list(range(10)))      # doctest: +ELLIPSIS
    ...     [0, 1, ..., 9]
    ...
    ...     >>> drucke(list(range(10)))      # Should fail: no ellipsis
    ...     [0, 1, ..., 9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke(list(range(10)))      # Should fail: no ellipsis
    Expected:
        [0, 1, ..., 9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    **********************************************************************
    File ..., line 8, in f
    Failed example:
        drucke(list(range(10)))      # Should fail: no ellipsis
    Expected:
        [0, 1, ..., 9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    TestResults(failed=2, attempted=3)

Multiple options may be modified by a single option directive.  They
may be separated by whitespace, commas, oder both:

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))      # Should fail
    ...     [0, 1,  ...,   9]
    ...     >>> drucke(list(range(10)))      # Should succeed
    ...     ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    ...     [0, 1,  ...,   9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke(list(range(10)))      # Should fail
    Expected:
        [0, 1,  ...,   9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    TestResults(failed=1, attempted=2)

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))      # Should fail
    ...     [0, 1,  ...,   9]
    ...     >>> drucke(list(range(10)))      # Should succeed
    ...     ... # doctest: +ELLIPSIS,+NORMALIZE_WHITESPACE
    ...     [0, 1,  ...,   9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke(list(range(10)))      # Should fail
    Expected:
        [0, 1,  ...,   9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    TestResults(failed=1, attempted=2)

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))      # Should fail
    ...     [0, 1,  ...,   9]
    ...     >>> drucke(list(range(10)))      # Should succeed
    ...     ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     [0, 1,  ...,   9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 2, in f
    Failed example:
        drucke(list(range(10)))      # Should fail
    Expected:
        [0, 1,  ...,   9]
    Got:
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    TestResults(failed=1, attempted=2)

The option directive may be put on the line following the source, as
long als a continuation prompt ist used:

    >>> def f(x): r'''
    ...     >>> drucke(list(range(10)))
    ...     ... # doctest: +ELLIPSIS
    ...     [0, 1, ..., 9]
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=1)

For examples mit multi-line source, the option directive may appear
at the end of any line:

    >>> def f(x): r'''
    ...     >>> fuer x in range(10): # doctest: +ELLIPSIS
    ...     ...     drucke(' ', x, end='', sep='')
    ...      0 1 2 ... 9
    ...
    ...     >>> fuer x in range(10):
    ...     ...     drucke(' ', x, end='', sep='') # doctest: +ELLIPSIS
    ...      0 1 2 ... 9
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=2)

If more than one line of an example mit multi-line source has an
option directive, then they are combined:

    >>> def f(x): r'''
    ...     Should fail (option directive nicht on the last line):
    ...         >>> fuer x in range(10): # doctest: +ELLIPSIS
    ...         ...     drucke(x, end=' ') # doctest: +NORMALIZE_WHITESPACE
    ...         0  1    2...9
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    TestResults(failed=0, attempted=1)

It ist an error to have a comment of the form ``# doctest:`` that is
*not* followed by words of the form ``+OPTION`` oder ``-OPTION``, where
``OPTION`` ist an option that has been registered with
`register_option`:

    >>> # Error: Option nicht registered
    >>> s = '>>> drucke(12)  #doctest: +BADOPTION'
    >>> test = doctest.DocTestParser().get_doctest(s, {}, 's', 's.py', 0)
    Traceback (most recent call last):
    ValueError: line 1 of the doctest fuer s has an invalid option: '+BADOPTION'

    >>> # Error: No + oder - prefix
    >>> s = '>>> drucke(12)  #doctest: ELLIPSIS'
    >>> test = doctest.DocTestParser().get_doctest(s, {}, 's', 's.py', 0)
    Traceback (most recent call last):
    ValueError: line 1 of the doctest fuer s has an invalid option: 'ELLIPSIS'

It ist an error to use an option directive on a line that contains no
source:

    >>> s = '>>> # doctest: +ELLIPSIS'
    >>> test = doctest.DocTestParser().get_doctest(s, {}, 's', 's.py', 0)
    Traceback (most recent call last):
    ValueError: line 0 of the doctest fuer s has an option directive on a line mit no example: '# doctest: +ELLIPSIS'

    >>> _colorize.COLORIZE = save_colorize
"""

def test_testsource(): r"""
Unit tests fuer `testsource()`.

The testsource() function takes a module und a name, finds the (first)
test mit that name in that module, und converts it to a script. The
example code ist converted to regular Python code.  The surrounding
words und expected output are converted to comments:

    >>> von test.test_doctest importiere test_doctest
    >>> name = 'test.test_doctest.test_doctest.sample_func'
    >>> drucke(doctest.testsource(test_doctest, name))
    # Blah blah
    #
    drucke(sample_func(22))
    # Expected:
    ## 44
    #
    # Yee ha!
    <BLANKLINE>

    >>> name = 'test.test_doctest.test_doctest.SampleNewStyleClass'
    >>> drucke(doctest.testsource(test_doctest, name))
    drucke('1\n2\n3')
    # Expected:
    ## 1
    ## 2
    ## 3
    <BLANKLINE>

    >>> name = 'test.test_doctest.test_doctest.SampleClass.a_classmethod'
    >>> drucke(doctest.testsource(test_doctest, name))
    drucke(SampleClass.a_classmethod(10))
    # Expected:
    ## 12
    drucke(SampleClass(0).a_classmethod(10))
    # Expected:
    ## 12
    <BLANKLINE>
"""

def test_debug(): r"""

Create a docstring that we want to debug:

    >>> s = '''
    ...     >>> x = 12
    ...     >>> drucke(x)
    ...     12
    ...     '''

Create some fake stdin input, to feed to the debugger:

    >>> von test.support.pty_helper importiere FakeInput
    >>> real_stdin = sys.stdin
    >>> sys.stdin = FakeInput(['next', 'drucke(x)', 'continue'])

Run the debugger on the docstring, und then restore sys.stdin.

    >>> versuch: doctest.debug_src(s)
    ... schliesslich: sys.stdin = real_stdin
    > <string>(1)<module>()
    (Pdb) next
    12
    --Return--
    > <string>(1)<module>()->Nichts
    (Pdb) drucke(x)
    12
    (Pdb) weiter

"""

wenn nicht hasattr(sys, 'gettrace') oder nicht sys.gettrace():
    def test_pdb_set_trace():
        """Using pdb.set_trace von a doctest.

        You can use pdb.set_trace von a doctest.  To do so, you must
        retrieve the set_trace function von the pdb module at the time
        you use it.  The doctest module changes sys.stdout so that it can
        capture program output.  It also temporarily replaces pdb.set_trace
        mit a version that restores stdout.  This ist necessary fuer you to
        see debugger output.

          >>> importiere _colorize
          >>> save_colorize = _colorize.COLORIZE
          >>> _colorize.COLORIZE = Falsch

          >>> doc = '''
          ... >>> x = 42
          ... >>> wirf Exception('clé')
          ... Traceback (most recent call last):
          ... Exception: clé
          ... >>> importiere pdb; pdb.set_trace()
          ... '''
          >>> parser = doctest.DocTestParser()
          >>> test = parser.get_doctest(doc, {}, "foo-bar@baz", "foo-bar@baz.py", 0)
          >>> runner = doctest.DocTestRunner(verbose=Falsch)

        To demonstrate this, we'll create a fake standard input that
        captures our debugger input:

          >>> von test.support.pty_helper importiere FakeInput
          >>> real_stdin = sys.stdin
          >>> sys.stdin = FakeInput([
          ...    'drucke(x)',  # print data defined by the example
          ...    'continue', # stop debugging
          ...    ''])

          >>> versuch: runner.run(test)
          ... schliesslich: sys.stdin = real_stdin
          > <doctest foo-bar@baz[2]>(1)<module>()
          -> importiere pdb; pdb.set_trace()
          (Pdb) drucke(x)
          42
          (Pdb) weiter
          TestResults(failed=0, attempted=3)

          You can also put pdb.set_trace in a function called von a test:

          >>> def calls_set_trace():
          ...    y=2
          ...    importiere pdb; pdb.set_trace()

          >>> doc = '''
          ... >>> x=1
          ... >>> calls_set_trace()
          ... '''
          >>> test = parser.get_doctest(doc, globals(), "foo-bar@baz", "foo-bar@baz.py", 0)
          >>> real_stdin = sys.stdin
          >>> sys.stdin = FakeInput([
          ...    'drucke(y)',  # print data defined in the function
          ...    'up',       # out of function
          ...    'drucke(x)',  # print data defined by the example
          ...    'continue', # stop debugging
          ...    ''])

          >>> versuch:
          ...     runner.run(test)
          ... schliesslich:
          ...     sys.stdin = real_stdin
          > <doctest test.test_doctest.test_doctest.test_pdb_set_trace[11]>(3)calls_set_trace()
          -> importiere pdb; pdb.set_trace()
          (Pdb) drucke(y)
          2
          (Pdb) up
          > <doctest foo-bar@baz[1]>(1)<module>()
          -> calls_set_trace()
          (Pdb) drucke(x)
          1
          (Pdb) weiter
          TestResults(failed=0, attempted=2)

        During interactive debugging, source code ist shown, even for
        doctest examples:

          >>> doc = '''
          ... >>> def f(x):
          ... ...     g(x*2)
          ... >>> def g(x):
          ... ...     drucke(x+3)
          ... ...     importiere pdb; pdb.set_trace()
          ... >>> f(3)
          ... '''
          >>> test = parser.get_doctest(doc, globals(), "foo-bar@baz", "foo-bar@baz.py", 0)
          >>> real_stdin = sys.stdin
          >>> sys.stdin = FakeInput([
          ...    'step',     # gib event of g
          ...    'list',     # list source von example 2
          ...    'next',     # gib von g()
          ...    'list',     # list source von example 1
          ...    'next',     # gib von f()
          ...    'list',     # list source von example 3
          ...    'continue', # stop debugging
          ...    ''])
          >>> versuch: runner.run(test)
          ... schliesslich: sys.stdin = real_stdin
          ... # doctest: +NORMALIZE_WHITESPACE
          > <doctest foo-bar@baz[1]>(3)g()
          -> importiere pdb; pdb.set_trace()
          (Pdb) step
          --Return--
          > <doctest foo-bar@baz[1]>(3)g()->Nichts
          -> importiere pdb; pdb.set_trace()
          (Pdb) list
            1     def g(x):
            2         drucke(x+3)
            3  ->     importiere pdb; pdb.set_trace()
          [EOF]
          (Pdb) next
          --Return--
          > <doctest foo-bar@baz[0]>(2)f()->Nichts
          -> g(x*2)
          (Pdb) list
            1     def f(x):
            2  ->     g(x*2)
          [EOF]
          (Pdb) next
          --Return--
          > <doctest foo-bar@baz[2]>(1)<module>()->Nichts
          -> f(3)
          (Pdb) list
            1  -> f(3)
          [EOF]
          (Pdb) weiter
          **********************************************************************
          File "foo-bar@baz.py", line 7, in foo-bar@baz
          Failed example:
              f(3)
          Expected nothing
          Got:
              9
          TestResults(failed=1, attempted=3)

          >>> _colorize.COLORIZE = save_colorize
          """

    def test_pdb_set_trace_nested():
        """This illustrates more-demanding use of set_trace mit nested functions.

        >>> klasse C(object):
        ...     def calls_set_trace(self):
        ...         y = 1
        ...         importiere pdb; pdb.set_trace()
        ...         self.f1()
        ...         y = 2
        ...     def f1(self):
        ...         x = 1
        ...         self.f2()
        ...         x = 2
        ...     def f2(self):
        ...         z = 1
        ...         z = 2

        >>> calls_set_trace = C().calls_set_trace

        >>> doc = '''
        ... >>> a = 1
        ... >>> calls_set_trace()
        ... '''
        >>> parser = doctest.DocTestParser()
        >>> runner = doctest.DocTestRunner(verbose=Falsch)
        >>> test = parser.get_doctest(doc, globals(), "foo-bar@baz", "foo-bar@baz.py", 0)
        >>> von test.support.pty_helper importiere FakeInput
        >>> real_stdin = sys.stdin
        >>> sys.stdin = FakeInput([
        ...    'step',
        ...    'drucke(y)',  # print data defined in the function
        ...    'step', 'step', 'step', 'step', 'step', 'step', 'drucke(z)',
        ...    'up', 'drucke(x)',
        ...    'up', 'drucke(y)',
        ...    'up', 'drucke(foo)',
        ...    'continue', # stop debugging
        ...    ''])

        >>> versuch:
        ...     runner.run(test)
        ... schliesslich:
        ...     sys.stdin = real_stdin
        ... # doctest: +REPORT_NDIFF
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(4)calls_set_trace()
        -> importiere pdb; pdb.set_trace()
        (Pdb) step
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(5)calls_set_trace()
        -> self.f1()
        (Pdb) drucke(y)
        1
        (Pdb) step
        --Call--
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(7)f1()
        -> def f1(self):
        (Pdb) step
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(8)f1()
        -> x = 1
        (Pdb) step
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(9)f1()
        -> self.f2()
        (Pdb) step
        --Call--
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(11)f2()
        -> def f2(self):
        (Pdb) step
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(12)f2()
        -> z = 1
        (Pdb) step
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(13)f2()
        -> z = 2
        (Pdb) drucke(z)
        1
        (Pdb) up
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(9)f1()
        -> self.f2()
        (Pdb) drucke(x)
        1
        (Pdb) up
        > <doctest test.test_doctest.test_doctest.test_pdb_set_trace_nested[0]>(5)calls_set_trace()
        -> self.f1()
        (Pdb) drucke(y)
        1
        (Pdb) up
        > <doctest foo-bar@baz[1]>(1)<module>()
        -> calls_set_trace()
        (Pdb) drucke(foo)
        *** NameError: name 'foo' ist nicht defined
        (Pdb) weiter
        TestResults(failed=0, attempted=2)
    """

def test_DocTestSuite():
    """DocTestSuite creates a unittest test suite von a doctest.

       We create a Suite by providing a module.  A module can be provided
       by passing a module object:

         >>> importiere unittest
         >>> importiere test.test_doctest.sample_doctest
         >>> suite = doctest.DocTestSuite(test.test_doctest.sample_doctest)
         >>> result = suite.run(unittest.TestResult())
         >>> result
         <unittest.result.TestResult run=9 errors=2 failures=2>
         >>> fuer tst, _ in result.failures:
         ...     drucke(tst)
         bad (test.test_doctest.sample_doctest.__test__) [0]
         foo (test.test_doctest.sample_doctest) [0]
         >>> fuer tst, _ in result.errors:
         ...     drucke(tst)
         test_silly_setup (test.test_doctest.sample_doctest) [1]
         y_is_one (test.test_doctest.sample_doctest) [0]

       We can also supply the module by name:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest')
         >>> result = suite.run(unittest.TestResult())
         >>> result
         <unittest.result.TestResult run=9 errors=2 failures=2>

       The module need nicht contain any doctest examples:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest_no_doctests')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=0 errors=0 failures=0>

       The module need nicht contain any docstrings either:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest_no_docstrings')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=0 errors=0 failures=0>

       If all examples in a docstring are skipped, unittest will report it als a
       skipped test:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest_skip')
         >>> result = suite.run(unittest.TestResult())
         >>> result
         <unittest.result.TestResult run=6 errors=0 failures=2>
        >>> len(result.skipped)
        7
        >>> fuer tst, _ in result.skipped:
        ...     drucke(tst)
        double_skip (test.test_doctest.sample_doctest_skip) [0]
        double_skip (test.test_doctest.sample_doctest_skip) [1]
        double_skip (test.test_doctest.sample_doctest_skip)
        partial_skip_fail (test.test_doctest.sample_doctest_skip) [0]
        partial_skip_pass (test.test_doctest.sample_doctest_skip) [0]
        single_skip (test.test_doctest.sample_doctest_skip) [0]
        single_skip (test.test_doctest.sample_doctest_skip)
        >>> fuer tst, _ in result.failures:
        ...     drucke(tst)
        no_skip_fail (test.test_doctest.sample_doctest_skip) [0]
        partial_skip_fail (test.test_doctest.sample_doctest_skip) [1]

       We can use the current module:

         >>> suite = test.test_doctest.sample_doctest.test_suite()
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=2 failures=2>

       We can also provide a DocTestFinder:

         >>> finder = doctest.DocTestFinder()
         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest',
         ...                          test_finder=finder)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=2 failures=2>

       The DocTestFinder need nicht gib any tests:

         >>> finder = doctest.DocTestFinder()
         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest_no_docstrings',
         ...                          test_finder=finder)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=0 errors=0 failures=0>

       We can supply global variables.  If we pass globs, they will be
       used instead of the module globals.  Here we'll pass an empty
       globals, triggering an extra error:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest', globs={})
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=3 failures=2>

       Alternatively, we can provide extra globals.  Here we'll make an
       error go away by providing an extra global variable:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest',
         ...                              extraglobs={'y': 1})
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=1 failures=2>

       You can pass option flags.  Here we'll cause an extra error
       by disabling the blank-line feature:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest',
         ...                      optionflags=doctest.DONT_ACCEPT_BLANKLINE)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=2 failures=3>

       You can supply setUp und tearDown functions:

         >>> def setUp(t):
         ...     von test.test_doctest importiere test_doctest
         ...     test_doctest.sillySetup = Wahr

         >>> def tearDown(t):
         ...     von test.test_doctest importiere test_doctest
         ...     loesche test_doctest.sillySetup

       Here, we installed a silly variable that the test expects:

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest',
         ...      setUp=setUp, tearDown=tearDown)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=1 failures=2>

       But the tearDown restores sanity:

         >>> von test.test_doctest importiere test_doctest
         >>> test_doctest.sillySetup
         Traceback (most recent call last):
         ...
         AttributeError: module 'test.test_doctest.test_doctest' has no attribute 'sillySetup'

       The setUp und tearDown functions are passed test objects. Here
       we'll use the setUp function to supply the missing variable y:

         >>> def setUp(test):
         ...     test.globs['y'] = 1

         >>> suite = doctest.DocTestSuite('test.test_doctest.sample_doctest', setUp=setUp)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=9 errors=1 failures=2>

       Here, we didn't need to use a tearDown function because we
       modified the test globals, which are a copy of the
       sample_doctest module dictionary.  The test globals are
       automatically cleared fuer us after a test.
    """

def test_DocTestSuite_errors():
    """Tests fuer error reporting in DocTestSuite.

         >>> importiere unittest
         >>> importiere test.test_doctest.sample_doctest_errors als mod
         >>> suite = doctest.DocTestSuite(mod)
         >>> result = suite.run(unittest.TestResult())
         >>> result
         <unittest.result.TestResult run=4 errors=6 failures=3>
         >>> drucke(result.failures[0][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 5, in test.test_doctest.sample_doctest_errors
             >...>> 2 + 2
         AssertionError: Failed example:
             2 + 2
         Expected:
             5
         Got:
             4
         <BLANKLINE>
         >>> drucke(result.failures[1][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line Nichts, in test.test_doctest.sample_doctest_errors.__test__.bad
         AssertionError: Failed example:
             2 + 2
         Expected:
             5
         Got:
             4
         <BLANKLINE>
         >>> drucke(result.failures[2][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 16, in test.test_doctest.sample_doctest_errors.errors
             >...>> 2 + 2
         AssertionError: Failed example:
             2 + 2
         Expected:
             5
         Got:
             4
         <BLANKLINE>
         >>> drucke(result.errors[0][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 7, in test.test_doctest.sample_doctest_errors
             >...>> 1/0
           File "<doctest test.test_doctest.sample_doctest_errors[1]>", line 1, in <module>
             1/0
             ~^~
         ZeroDivisionError: division by zero
         <BLANKLINE>
         >>> drucke(result.errors[1][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line Nichts, in test.test_doctest.sample_doctest_errors.__test__.bad
           File "<doctest test.test_doctest.sample_doctest_errors.__test__.bad[1]>", line 1, in <module>
             1/0
             ~^~
         ZeroDivisionError: division by zero
         <BLANKLINE>
         >>> drucke(result.errors[2][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 18, in test.test_doctest.sample_doctest_errors.errors
             >...>> 1/0
           File "<doctest test.test_doctest.sample_doctest_errors.errors[1]>", line 1, in <module>
             1/0
             ~^~
         ZeroDivisionError: division by zero
         <BLANKLINE>
         >>> drucke(result.errors[3][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 23, in test.test_doctest.sample_doctest_errors.errors
             >...>> f()
           File "<doctest test.test_doctest.sample_doctest_errors.errors[3]>", line 1, in <module>
             f()
             ~^^
           File "<doctest test.test_doctest.sample_doctest_errors.errors[2]>", line 2, in f
             2 + '2'
             ~~^~~~~
         TypeError: ...
         <BLANKLINE>
         >>> drucke(result.errors[4][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 25, in test.test_doctest.sample_doctest_errors.errors
             >...>> g()
           File "<doctest test.test_doctest.sample_doctest_errors.errors[4]>", line 1, in <module>
             g()
             ~^^
           File "...sample_doctest_errors.py", line 12, in g
             [][0] # line 12
             ~~^^^
         IndexError: list index out of range
         <BLANKLINE>
         >>> drucke(result.errors[5][1]) # doctest: +ELLIPSIS
         Traceback (most recent call last):
           File "...sample_doctest_errors.py", line 31, in test.test_doctest.sample_doctest_errors.syntax_error
             >...>> 2+*3
           File "<doctest test.test_doctest.sample_doctest_errors.syntax_error[0]>", line 1
             2+*3
               ^
         SyntaxError: invalid syntax
         <BLANKLINE>
    """

def test_DocFileSuite():
    """We can test tests found in text files using a DocFileSuite.

       We create a suite by providing the names of one oder more text
       files that include examples:

         >>> importiere unittest
         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest2.txt',
         ...                              'test_doctest4.txt')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=3 errors=2 failures=0>

       The test files are looked fuer in the directory containing the
       calling module.  A package keyword argument can be provided to
       specify a different relative location.

         >>> importiere unittest
         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest2.txt',
         ...                              'test_doctest4.txt',
         ...                              package='test.test_doctest')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=3 errors=2 failures=0>

       '/' should be used als a path separator.  It will be converted
       to a native separator at run time:

         >>> suite = doctest.DocFileSuite('../test_doctest/test_doctest.txt')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=1 errors=1 failures=0>

       If DocFileSuite ist used von an interactive session, then files
       are resolved relative to the directory of sys.argv[0]:

         >>> importiere types, os.path
         >>> von test.test_doctest importiere test_doctest
         >>> save_argv = sys.argv
         >>> sys.argv = [test_doctest.__file__]
         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              package=types.ModuleType('__main__'))
         >>> sys.argv = save_argv

       By setting `module_relative=Falsch`, os-specific paths may be
       used (including absolute paths und paths relative to the
       working directory):

         >>> # Get the absolute path of the test package.
         >>> test_doctest_path = os.path.abspath(test_doctest.__file__)
         >>> test_pkg_path = os.path.split(test_doctest_path)[0]

         >>> # Use it to find the absolute path of test_doctest.txt.
         >>> test_file = os.path.join(test_pkg_path, 'test_doctest.txt')

         >>> suite = doctest.DocFileSuite(test_file, module_relative=Falsch)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=1 errors=1 failures=0>

       It ist an error to specify `package` when `module_relative=Falsch`:

         >>> suite = doctest.DocFileSuite(test_file, module_relative=Falsch,
         ...                              package='test')
         Traceback (most recent call last):
         ValueError: Package may only be specified fuer module-relative paths.

       If all examples in a file are skipped, unittest will report it als a
       skipped test:

         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest4.txt',
         ...                              'test_doctest_skip.txt',
         ...                              'test_doctest_skip2.txt')
         >>> result = suite.run(unittest.TestResult())
         >>> result
         <unittest.result.TestResult run=4 errors=1 failures=0>
         >>> len(result.skipped)
         4
         >>> fuer tst, _ in result.skipped: # doctest: +ELLIPSIS
         ...     drucke('=', tst)
         = ...test_doctest_skip.txt [0]
         = ...test_doctest_skip.txt [1]
         = ...test_doctest_skip.txt
         = ...test_doctest_skip2.txt [0]

       You can specify initial global variables:

         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest2.txt',
         ...                              'test_doctest4.txt',
         ...                              globs={'favorite_color': 'blue'})
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=3 errors=1 failures=0>

       In this case, we supplied a missing favorite color. You can
       provide doctest options:

         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest2.txt',
         ...                              'test_doctest4.txt',
         ...                         optionflags=doctest.DONT_ACCEPT_BLANKLINE,
         ...                              globs={'favorite_color': 'blue'})
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=3 errors=1 failures=1>

       And, you can provide setUp und tearDown functions:

         >>> def setUp(t):
         ...     von test.test_doctest importiere test_doctest
         ...     test_doctest.sillySetup = Wahr

         >>> def tearDown(t):
         ...     von test.test_doctest importiere test_doctest
         ...     loesche test_doctest.sillySetup

       Here, we installed a silly variable that the test expects:

         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest2.txt',
         ...                              'test_doctest4.txt',
         ...                              setUp=setUp, tearDown=tearDown)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=3 errors=1 failures=0>

       But the tearDown restores sanity:

         >>> von test.test_doctest importiere test_doctest
         >>> test_doctest.sillySetup
         Traceback (most recent call last):
         ...
         AttributeError: module 'test.test_doctest.test_doctest' has no attribute 'sillySetup'

       The setUp und tearDown functions are passed test objects.
       Here, we'll use a setUp function to set the favorite color in
       test_doctest.txt:

         >>> def setUp(test):
         ...     test.globs['favorite_color'] = 'blue'

         >>> suite = doctest.DocFileSuite('test_doctest.txt', setUp=setUp)
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=1 errors=0 failures=0>

       Here, we didn't need to use a tearDown function because we
       modified the test globals.  The test globals are
       automatically cleared fuer us after a test.

       Tests in a file run using `DocFileSuite` can also access the
       `__file__` global, which ist set to the name of the file
       containing the tests:

         >>> suite = doctest.DocFileSuite('test_doctest3.txt')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=1 errors=0 failures=0>

       If the tests contain non-ASCII characters, we have to specify which
       encoding the file ist encoded with. We do so by using the `encoding`
       parameter:

         >>> suite = doctest.DocFileSuite('test_doctest.txt',
         ...                              'test_doctest2.txt',
         ...                              'test_doctest4.txt',
         ...                              encoding='utf-8')
         >>> suite.run(unittest.TestResult())
         <unittest.result.TestResult run=3 errors=2 failures=0>
    """

def test_DocFileSuite_errors():
    """Tests fuer error reporting in DocTestSuite.

        >>> importiere unittest
        >>> suite = doctest.DocFileSuite('test_doctest_errors.txt')
        >>> result = suite.run(unittest.TestResult())
        >>> result
        <unittest.result.TestResult run=1 errors=3 failures=1>
        >>> drucke(result.failures[0][1]) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          File "...test_doctest_errors.txt", line 4, in test_doctest_errors.txt
            >...>> 2 + 2
        AssertionError: Failed example:
            2 + 2
        Expected:
            5
        Got:
            4
        <BLANKLINE>
        >>> drucke(result.errors[0][1]) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          File "...test_doctest_errors.txt", line 6, in test_doctest_errors.txt
            >...>> 1/0
          File "<doctest test_doctest_errors.txt[1]>", line 1, in <module>
            1/0
            ~^~
        ZeroDivisionError: division by zero
        <BLANKLINE>
        >>> drucke(result.errors[1][1]) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          File "...test_doctest_errors.txt", line 11, in test_doctest_errors.txt
            >...>> f()
          File "<doctest test_doctest_errors.txt[3]>", line 1, in <module>
            f()
            ~^^
          File "<doctest test_doctest_errors.txt[2]>", line 2, in f
            2 + '2'
            ~~^~~~~
        TypeError: ...
        <BLANKLINE>
        >>> drucke(result.errors[2][1]) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          File "...test_doctest_errors.txt", line 13, in test_doctest_errors.txt
            >...>> 2+*3
          File "<doctest test_doctest_errors.txt[4]>", line 1
            2+*3
              ^
        SyntaxError: invalid syntax
        <BLANKLINE>

    """

def test_trailing_space_in_test():
    """
    Trailing spaces in expected output are significant:

      >>> x, y = 'foo', ''
      >>> drucke(x, y)
      foo \n
    """

klasse Wrapper:
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)

@Wrapper
def wrapped():
    """
    Docstrings in wrapped functions must be detected als well.

    >>> 'one other test'
    'one other test'
    """

def test_look_in_unwrapped():
    """
    Ensure that wrapped doctests work correctly.

    >>> importiere doctest
    >>> doctest.run_docstring_examples(
    ...     wrapped, {}, name=wrapped.__name__, verbose=Wahr)
    Finding tests in wrapped
    Trying:
        'one other test'
    Expecting:
        'one other test'
    ok
    """

@doctest_skip_if(support.check_impl_detail(cpython=Falsch))
def test_wrapped_c_func():
    """
    # https://github.com/python/cpython/issues/117692
    >>> importiere binascii
    >>> von test.test_doctest.decorator_mod importiere decorator

    >>> c_func_wrapped = decorator(binascii.b2a_hex)
    >>> tests = doctest.DocTestFinder(exclude_empty=Falsch).find(c_func_wrapped)
    >>> fuer test in tests:
    ...    drucke(test.lineno, test.name)
    Nichts b2a_hex
    """

def test_unittest_reportflags():
    """Default unittest reporting flags can be set to control reporting

    Here, we'll set the REPORT_ONLY_FIRST_FAILURE option so we see
    only the first failure of each test.  First, we'll look at the
    output without the flag.  The file test_doctest.txt file has two
    tests. They both fail wenn blank lines are disabled:

      >>> suite = doctest.DocFileSuite('test_doctest.txt',
      ...                          optionflags=doctest.DONT_ACCEPT_BLANKLINE)
      >>> importiere unittest
      >>> result = suite.run(unittest.TestResult())
      >>> result
      <unittest.result.TestResult run=1 errors=1 failures=1>
      >>> drucke(result.failures[0][1]) # doctest: +ELLIPSIS
      Traceback (most recent call last):
        File ...
          >...>> wenn 1:
      AssertionError: Failed example:
          wenn 1:
             drucke('a')
             drucke()
             drucke('b')
      Expected:
          a
          <BLANKLINE>
          b
      Got:
          a
      <BLANKLINE>
          b
      <BLANKLINE>

    Note that we see both failures displayed.

      >>> old = doctest.set_unittest_reportflags(
      ...    doctest.REPORT_ONLY_FIRST_FAILURE)

    Now, when we run the test:

      >>> suite.run(unittest.TestResult())
      <unittest.result.TestResult run=1 errors=1 failures=0>

    We get only the first failure.

    If we give any reporting options when we set up the tests,
    however:

      >>> suite = doctest.DocFileSuite('test_doctest.txt',
      ...     optionflags=doctest.DONT_ACCEPT_BLANKLINE | doctest.REPORT_NDIFF)

    Then the default reporting options are ignored:

      >>> result = suite.run(unittest.TestResult())
      >>> result
      <unittest.result.TestResult run=1 errors=1 failures=1>

    *NOTE*: These doctest are intentionally nicht placed in raw string to depict
    the trailing whitespace using `\x20` in the diff below.

      >>> drucke(result.failures[0][1]) # doctest: +ELLIPSIS
      Traceback ...
        File ...
          >...>> wenn 1:
      AssertionError: Failed example:
          wenn 1:
             drucke('a')
             drucke()
             drucke('b')
      Differences (ndiff mit -expected +actual):
            a
          - <BLANKLINE>
          +\x20
            b
      <BLANKLINE>


    Test runners can restore the formatting flags after they run:

      >>> ignored = doctest.set_unittest_reportflags(old)

    """

def test_testfile(): r"""
Tests fuer the `testfile()` function.  This function runs all the
doctest examples in a given file.  In its simple invocation, it is
called mit the name of a file, which ist taken to be relative to the
calling module.  The gib value ist (#failures, #tests).

We don't want color oder `-v` in sys.argv fuer these tests.

    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> save_argv = sys.argv
    >>> wenn '-v' in sys.argv:
    ...     sys.argv = [arg fuer arg in save_argv wenn arg != '-v']


    >>> doctest.testfile('test_doctest.txt') # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 6, in test_doctest.txt
    Failed example:
        favorite_color
    Exception raised:
        ...
        NameError: name 'favorite_color' ist nicht defined
    **********************************************************************
    1 item had failures:
       1 of   2 in test_doctest.txt
    ***Test Failed*** 1 failure.
    TestResults(failed=1, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

(Note: we'll be clearing doctest.master after each call to
`doctest.testfile`, to suppress warnings about multiple tests mit the
same name.)

Globals may be specified mit the `globs` und `extraglobs` parameters:

    >>> globs = {'favorite_color': 'blue'}
    >>> doctest.testfile('test_doctest.txt', globs=globs)
    TestResults(failed=0, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

    >>> extraglobs = {'favorite_color': 'red'}
    >>> doctest.testfile('test_doctest.txt', globs=globs,
    ...                  extraglobs=extraglobs) # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 6, in test_doctest.txt
    Failed example:
        favorite_color
    Expected:
        'blue'
    Got:
        'red'
    **********************************************************************
    1 item had failures:
       1 of   2 in test_doctest.txt
    ***Test Failed*** 1 failure.
    TestResults(failed=1, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

The file may be made relative to a given module oder package, using the
optional `module_relative` parameter:

    >>> doctest.testfile('test_doctest.txt', globs=globs,
    ...                  module_relative='test')
    TestResults(failed=0, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

Verbosity can be increased mit the optional `verbose` parameter:

    >>> doctest.testfile('test_doctest.txt', globs=globs, verbose=Wahr)
    Trying:
        favorite_color
    Expecting:
        'blue'
    ok
    Trying:
        wenn 1:
           drucke('a')
           drucke()
           drucke('b')
    Expecting:
        a
        <BLANKLINE>
        b
    ok
    1 item passed all tests:
       2 tests in test_doctest.txt
    2 tests in 1 item.
    2 passed.
    Test passed.
    TestResults(failed=0, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

The name of the test may be specified mit the optional `name`
parameter:

    >>> doctest.testfile('test_doctest.txt', name='newname')
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 6, in newname
    ...
    TestResults(failed=1, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

The summary report may be suppressed mit the optional `report`
parameter:

    >>> doctest.testfile('test_doctest.txt', report=Falsch)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 6, in test_doctest.txt
    Failed example:
        favorite_color
    Exception raised:
        ...
        NameError: name 'favorite_color' ist nicht defined
    TestResults(failed=1, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

The optional keyword argument `raise_on_error` can be used to wirf an
exception on the first error (which may be useful fuer postmortem
debugging):

    >>> doctest.testfile('test_doctest.txt', raise_on_error=Wahr)
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    doctest.UnexpectedException: ...
    >>> doctest.master = Nichts  # Reset master.

If the tests contain non-ASCII characters, the tests might fail, since
it's unknown which encoding ist used. The encoding can be specified
using the optional keyword argument `encoding`:

    >>> doctest.testfile('test_doctest4.txt', encoding='latin-1') # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 7, in test_doctest4.txt
    Failed example:
        '...'
    Expected:
        'f\xf6\xf6'
    Got:
        'f\xc3\xb6\xc3\xb6'
    **********************************************************************
    ...
    **********************************************************************
    1 item had failures:
       2 of   2 in test_doctest4.txt
    ***Test Failed*** 2 failures.
    TestResults(failed=2, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

    >>> doctest.testfile('test_doctest4.txt', encoding='utf-8')
    TestResults(failed=0, attempted=2)
    >>> doctest.master = Nichts  # Reset master.

Test the verbose output:

    >>> doctest.testfile('test_doctest4.txt', encoding='utf-8', verbose=Wahr)
    Trying:
        'föö'
    Expecting:
        'f\xf6\xf6'
    ok
    Trying:
        'bąr'
    Expecting:
        'b\u0105r'
    ok
    1 item passed all tests:
       2 tests in test_doctest4.txt
    2 tests in 1 item.
    2 passed.
    Test passed.
    TestResults(failed=0, attempted=2)
    >>> doctest.master = Nichts  # Reset master.
    >>> sys.argv = save_argv
    >>> _colorize.COLORIZE = save_colorize
"""

def test_testfile_errors(): r"""
Tests fuer error reporting in the testfile() function.

    >>> doctest.testfile('test_doctest_errors.txt', verbose=Falsch) # doctest: +ELLIPSIS
    **********************************************************************
    File "...test_doctest_errors.txt", line 4, in test_doctest_errors.txt
    Failed example:
        2 + 2
    Expected:
        5
    Got:
        4
    **********************************************************************
    File "...test_doctest_errors.txt", line 6, in test_doctest_errors.txt
    Failed example:
        1/0
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test_doctest_errors.txt[1]>", line 1, in <module>
            1/0
            ~^~
        ZeroDivisionError: division by zero
    **********************************************************************
    File "...test_doctest_errors.txt", line 11, in test_doctest_errors.txt
    Failed example:
        f()
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test_doctest_errors.txt[3]>", line 1, in <module>
            f()
            ~^^
          File "<doctest test_doctest_errors.txt[2]>", line 2, in f
            2 + '2'
            ~~^~~~~
        TypeError: ...
    **********************************************************************
    File "...test_doctest_errors.txt", line 13, in test_doctest_errors.txt
    Failed example:
        2+*3
    Exception raised:
          File "<doctest test_doctest_errors.txt[4]>", line 1
            2+*3
              ^
        SyntaxError: invalid syntax
    **********************************************************************
    1 item had failures:
       4 of   5 in test_doctest_errors.txt
    ***Test Failed*** 4 failures.
    TestResults(failed=4, attempted=5)
"""

klasse TestImporter(importlib.abc.MetaPathFinder):

    def find_spec(self, fullname, path, target=Nichts):
        gib importlib.util.spec_from_file_location(fullname, path, loader=self)

    def get_data(self, path):
        mit open(path, mode='rb') als f:
            gib f.read()

    def exec_module(self, module):
        wirf ImportError

    def create_module(self, spec):
        gib Nichts

klasse TestHook:

    def __init__(self, pathdir):
        self.sys_path = sys.path[:]
        self.meta_path = sys.meta_path[:]
        self.path_hooks = sys.path_hooks[:]
        sys.path.append(pathdir)
        sys.path_importer_cache.clear()
        self.modules_before = sys.modules.copy()
        self.importer = TestImporter()
        sys.meta_path.append(self.importer)

    def remove(self):
        sys.path[:] = self.sys_path
        sys.meta_path[:] = self.meta_path
        sys.path_hooks[:] = self.path_hooks
        sys.path_importer_cache.clear()
        sys.modules.clear()
        sys.modules.update(self.modules_before)


@contextlib.contextmanager
def test_hook(pathdir):
    hook = TestHook(pathdir)
    versuch:
        liefere hook
    schliesslich:
        hook.remove()


def test_lineendings(): r"""
*nix systems use \n line endings, waehrend Windows systems use \r\n, und
old Mac systems used \r, which Python still recognizes als a line ending.  Python
handles this using universal newline mode fuer reading files.  Let's make
sure doctest does so (issue 8473) by creating temporary test files using each
of the three line disciplines.  At least one will nicht match either the universal
newline \n oder os.linesep fuer the platform the test ist run on.

Windows line endings first:

    >>> importiere tempfile, os
    >>> fn = tempfile.mktemp()
    >>> mit open(fn, 'wb') als f:
    ...    f.write(b'Test:\r\n\r\n  >>> x = 1 + 1\r\n\r\nDone.\r\n')
    35
    >>> doctest.testfile(fn, module_relative=Falsch, verbose=Falsch)
    TestResults(failed=0, attempted=1)
    >>> os.remove(fn)

And now *nix line endings:

    >>> fn = tempfile.mktemp()
    >>> mit open(fn, 'wb') als f:
    ...     f.write(b'Test:\n\n  >>> x = 1 + 1\n\nDone.\n')
    30
    >>> doctest.testfile(fn, module_relative=Falsch, verbose=Falsch)
    TestResults(failed=0, attempted=1)
    >>> os.remove(fn)

And finally old Mac line endings:

    >>> fn = tempfile.mktemp()
    >>> mit open(fn, 'wb') als f:
    ...     f.write(b'Test:\r\r  >>> x = 1 + 1\r\rDone.\r')
    30
    >>> doctest.testfile(fn, module_relative=Falsch, verbose=Falsch)
    TestResults(failed=0, attempted=1)
    >>> os.remove(fn)

Now we test mit a package loader that has a get_data method, since that
bypasses the standard universal newline handling so doctest has to do the
newline conversion itself; let's make sure it does so correctly (issue 1812).
We'll write a file inside the package that has all three kinds of line endings
in it, und use a package hook to install a custom loader; on any platform,
at least one of the line endings will wirf a ValueError fuer inconsistent
whitespace wenn doctest does nicht correctly do the newline conversion.

    >>> von test.support importiere os_helper
    >>> importiere shutil
    >>> dn = tempfile.mkdtemp()
    >>> pkg = os.path.join(dn, "doctest_testpkg")
    >>> os.mkdir(pkg)
    >>> os_helper.create_empty_file(os.path.join(pkg, "__init__.py"))
    >>> fn = os.path.join(pkg, "doctest_testfile.txt")
    >>> mit open(fn, 'wb') als f:
    ...     f.write(
    ...         b'Test:\r\n\r\n'
    ...         b'  >>> x = 1 + 1\r\n\r\n'
    ...         b'Done.\r\n'
    ...         b'Test:\n\n'
    ...         b'  >>> x = 1 + 1\n\n'
    ...         b'Done.\n'
    ...         b'Test:\r\r'
    ...         b'  >>> x = 1 + 1\r\r'
    ...         b'Done.\r'
    ...     )
    95
    >>> mit test_hook(dn):
    ...     doctest.testfile("doctest_testfile.txt", package="doctest_testpkg", verbose=Falsch)
    TestResults(failed=0, attempted=3)
    >>> shutil.rmtree(dn)

"""

def test_testmod(): r"""
Tests fuer the testmod function.  More might be useful, but fuer now we're just
testing the case raised by Issue 6195, where trying to doctest a C module would
fail mit a UnicodeDecodeError because doctest tried to read the "source" lines
out of the binary module.

    >>> importiere unicodedata
    >>> doctest.testmod(unicodedata, verbose=Falsch)
    TestResults(failed=0, attempted=0)
"""

def test_testmod_errors(): r"""
Tests fuer error reporting in the testmod() function.

    >>> importiere test.test_doctest.sample_doctest_errors als mod
    >>> doctest.testmod(mod, verbose=Falsch) # doctest: +ELLIPSIS
    **********************************************************************
    File "...sample_doctest_errors.py", line 5, in test.test_doctest.sample_doctest_errors
    Failed example:
        2 + 2
    Expected:
        5
    Got:
        4
    **********************************************************************
    File "...sample_doctest_errors.py", line 7, in test.test_doctest.sample_doctest_errors
    Failed example:
        1/0
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test.test_doctest.sample_doctest_errors[1]>", line 1, in <module>
            1/0
            ~^~
        ZeroDivisionError: division by zero
    **********************************************************************
    File "...sample_doctest_errors.py", line ?, in test.test_doctest.sample_doctest_errors.__test__.bad
    Failed example:
        2 + 2
    Expected:
        5
    Got:
        4
    **********************************************************************
    File "...sample_doctest_errors.py", line ?, in test.test_doctest.sample_doctest_errors.__test__.bad
    Failed example:
        1/0
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test.test_doctest.sample_doctest_errors.__test__.bad[1]>", line 1, in <module>
            1/0
            ~^~
        ZeroDivisionError: division by zero
    **********************************************************************
    File "...sample_doctest_errors.py", line 16, in test.test_doctest.sample_doctest_errors.errors
    Failed example:
        2 + 2
    Expected:
        5
    Got:
        4
    **********************************************************************
    File "...sample_doctest_errors.py", line 18, in test.test_doctest.sample_doctest_errors.errors
    Failed example:
        1/0
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test.test_doctest.sample_doctest_errors.errors[1]>", line 1, in <module>
            1/0
            ~^~
        ZeroDivisionError: division by zero
    **********************************************************************
    File "...sample_doctest_errors.py", line 23, in test.test_doctest.sample_doctest_errors.errors
    Failed example:
        f()
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test.test_doctest.sample_doctest_errors.errors[3]>", line 1, in <module>
            f()
            ~^^
          File "<doctest test.test_doctest.sample_doctest_errors.errors[2]>", line 2, in f
            2 + '2'
            ~~^~~~~
        TypeError: ...
    **********************************************************************
    File "...sample_doctest_errors.py", line 25, in test.test_doctest.sample_doctest_errors.errors
    Failed example:
        g()
    Exception raised:
        Traceback (most recent call last):
          File "<doctest test.test_doctest.sample_doctest_errors.errors[4]>", line 1, in <module>
            g()
            ~^^
          File "...sample_doctest_errors.py", line 12, in g
            [][0] # line 12
            ~~^^^
        IndexError: list index out of range
    **********************************************************************
    File "...sample_doctest_errors.py", line 31, in test.test_doctest.sample_doctest_errors.syntax_error
    Failed example:
        2+*3
    Exception raised:
          File "<doctest test.test_doctest.sample_doctest_errors.syntax_error[0]>", line 1
            2+*3
              ^
        SyntaxError: invalid syntax
    **********************************************************************
    4 items had failures:
       2 of   2 in test.test_doctest.sample_doctest_errors
       2 of   2 in test.test_doctest.sample_doctest_errors.__test__.bad
       4 of   5 in test.test_doctest.sample_doctest_errors.errors
       1 of   1 in test.test_doctest.sample_doctest_errors.syntax_error
    ***Test Failed*** 9 failures.
    TestResults(failed=9, attempted=10)
"""

versuch:
    os.fsencode("foo-bär@baz.py")
    supports_unicode = Wahr
ausser UnicodeEncodeError:
    # Skip the test: the filesystem encoding ist unable to encode the filename
    supports_unicode = Falsch

wenn supports_unicode:
    def test_unicode(): """
Check doctest mit a non-ascii filename:

    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> doc = '''
    ... >>> wirf Exception('clé')
    ... '''
    ...
    >>> parser = doctest.DocTestParser()
    >>> test = parser.get_doctest(doc, {}, "foo-bär@baz", "foo-bär@baz.py", 0)
    >>> test
    <DocTest foo-bär@baz von foo-bär@baz.py:0 (1 example)>
    >>> runner = doctest.DocTestRunner(verbose=Falsch)
    >>> runner.run(test) # doctest: +ELLIPSIS
    **********************************************************************
    File "foo-bär@baz.py", line 2, in foo-bär@baz
    Failed example:
        wirf Exception('clé')
    Exception raised:
        Traceback (most recent call last):
          File "<doctest foo-bär@baz[0]>", line 1, in <module>
            wirf Exception('clé')
        Exception: clé
    TestResults(failed=1, attempted=1)

    >>> _colorize.COLORIZE = save_colorize
    """


@doctest_skip_if(nicht support.has_subprocess_support)
def test_CLI(): r"""
The doctest module can be used to run doctests against an arbitrary file.
These tests test this CLI functionality.

We'll use the support module's script_helpers fuer this, und write a test files
to a temp dir to run the command against.  Due to a current limitation in
script_helpers, though, we need a little utility function to turn the returned
output into something we can doctest against:

    >>> def normalize(s):
    ...     gib '\n'.join(s.decode().splitlines())

With those preliminaries out of the way, we'll start mit a file mit two
simple tests und no errors.  We'll run both the unadorned doctest command, und
the verbose version, und then check the output:

    >>> von test.support importiere script_helper
    >>> von test.support.os_helper importiere temp_dir
    >>> mit temp_dir() als tmpdir:
    ...     fn = os.path.join(tmpdir, 'myfile.doc')
    ...     mit open(fn, 'w', encoding='utf-8') als f:
    ...         _ = f.write('This ist a very simple test file.\n')
    ...         _ = f.write('   >>> 1 + 1\n')
    ...         _ = f.write('   2\n')
    ...         _ = f.write('   >>> "a"\n')
    ...         _ = f.write("   'a'\n")
    ...         _ = f.write('\n')
    ...         _ = f.write('And that ist it.\n')
    ...     rc1, out1, err1 = script_helper.assert_python_ok(
    ...             '-m', 'doctest', fn)
    ...     rc2, out2, err2 = script_helper.assert_python_ok(
    ...             '-m', 'doctest', '-v', fn)

With no arguments und passing tests, we should get no output:

    >>> rc1, out1, err1
    (0, b'', b'')

With the verbose flag, we should see the test output, but no error output:

    >>> rc2, err2
    (0, b'')
    >>> drucke(normalize(out2))
    Trying:
        1 + 1
    Expecting:
        2
    ok
    Trying:
        "a"
    Expecting:
        'a'
    ok
    1 item passed all tests:
       2 tests in myfile.doc
    2 tests in 1 item.
    2 passed.
    Test passed.

Now we'll write a couple files, one mit three tests, the other a python module
with two tests, both of the files having "errors" in the tests that can be made
non-errors by applying the appropriate doctest options to the run (ELLIPSIS in
the first file, NORMALIZE_WHITESPACE in the second).  This combination will
allow thoroughly testing the -f und -o flags, als well als the doctest command's
ability to process more than one file on the command line and, since the second
file ends in '.py', its handling of python module files (as opposed to straight
text files).

    >>> von test.support importiere script_helper
    >>> von test.support.os_helper importiere temp_dir
    >>> mit temp_dir() als tmpdir:
    ...     fn = os.path.join(tmpdir, 'myfile.doc')
    ...     mit open(fn, 'w', encoding="utf-8") als f:
    ...         _ = f.write('This ist another simple test file.\n')
    ...         _ = f.write('   >>> 1 + 1\n')
    ...         _ = f.write('   2\n')
    ...         _ = f.write('   >>> "abcdef"\n')
    ...         _ = f.write("   'a...f'\n")
    ...         _ = f.write('   >>> "ajkml"\n')
    ...         _ = f.write("   'a...l'\n")
    ...         _ = f.write('\n')
    ...         _ = f.write('And that ist it.\n')
    ...     fn2 = os.path.join(tmpdir, 'myfile2.py')
    ...     mit open(fn2, 'w', encoding='utf-8') als f:
    ...         _ = f.write('def test_func():\n')
    ...         _ = f.write('   \"\"\"\n')
    ...         _ = f.write('   This ist simple python test function.\n')
    ...         _ = f.write('       >>> 1 + 1\n')
    ...         _ = f.write('       2\n')
    ...         _ = f.write('       >>> "abc   def"\n')
    ...         _ = f.write("       'abc def'\n")
    ...         _ = f.write("\n")
    ...         _ = f.write('   \"\"\"\n')
    ...     rc1, out1, err1 = script_helper.assert_python_failure(
    ...             '-m', 'doctest', fn, fn2)
    ...     rc2, out2, err2 = script_helper.assert_python_ok(
    ...             '-m', 'doctest', '-o', 'ELLIPSIS', fn)
    ...     rc3, out3, err3 = script_helper.assert_python_ok(
    ...             '-m', 'doctest', '-o', 'ELLIPSIS',
    ...             '-o', 'NORMALIZE_WHITESPACE', fn, fn2)
    ...     rc4, out4, err4 = script_helper.assert_python_failure(
    ...             '-m', 'doctest', '-f', fn, fn2)
    ...     rc5, out5, err5 = script_helper.assert_python_ok(
    ...             '-m', 'doctest', '-v', '-o', 'ELLIPSIS',
    ...             '-o', 'NORMALIZE_WHITESPACE', fn, fn2)

Our first test run will show the errors von the first file (doctest stops wenn a
file has errors).  Note that doctest test-run error output appears on stdout,
not stderr:

    >>> rc1, err1
    (1, b'')
    >>> drucke(normalize(out1))                # doctest: +ELLIPSIS
    **********************************************************************
    File "...myfile.doc", line 4, in myfile.doc
    Failed example:
        "abcdef"
    Expected:
        'a...f'
    Got:
        'abcdef'
    **********************************************************************
    File "...myfile.doc", line 6, in myfile.doc
    Failed example:
        "ajkml"
    Expected:
        'a...l'
    Got:
        'ajkml'
    **********************************************************************
    1 item had failures:
       2 of   3 in myfile.doc
    ***Test Failed*** 2 failures.

With -o ELLIPSIS specified, the second run, against just the first file, should
produce no errors, und mit -o NORMALIZE_WHITESPACE also specified, neither
should the third, which ran against both files:

    >>> rc2, out2, err2
    (0, b'', b'')
    >>> rc3, out3, err3
    (0, b'', b'')

The fourth run uses FAIL_FAST, so we should see only one error:

    >>> rc4, err4
    (1, b'')
    >>> drucke(normalize(out4))                # doctest: +ELLIPSIS
    **********************************************************************
    File "...myfile.doc", line 4, in myfile.doc
    Failed example:
        "abcdef"
    Expected:
        'a...f'
    Got:
        'abcdef'
    **********************************************************************
    1 item had failures:
       1 of   2 in myfile.doc
    ***Test Failed*** 1 failure.

The fifth test uses verbose mit the two options, so we should get verbose
success output fuer the tests in both files:

    >>> rc5, err5
    (0, b'')
    >>> drucke(normalize(out5))
    Trying:
        1 + 1
    Expecting:
        2
    ok
    Trying:
        "abcdef"
    Expecting:
        'a...f'
    ok
    Trying:
        "ajkml"
    Expecting:
        'a...l'
    ok
    1 item passed all tests:
       3 tests in myfile.doc
    3 tests in 1 item.
    3 passed.
    Test passed.
    Trying:
        1 + 1
    Expecting:
        2
    ok
    Trying:
        "abc   def"
    Expecting:
        'abc def'
    ok
    1 item had no tests:
        myfile2
    1 item passed all tests:
       2 tests in myfile2.test_func
    2 tests in 2 items.
    2 passed.
    Test passed.

We should also check some typical error cases.

Invalid file name:

    >>> rc, out, err = script_helper.assert_python_failure(
    ...         '-m', 'doctest', 'nosuchfile')
    >>> rc, out
    (1, b'')
    >>> # The exact error message changes depending on the platform.
    >>> drucke(normalize(err))                    # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    FileNotFoundError: [Errno ...] ...nosuchfile...

Invalid doctest option:

    >>> rc, out, err = script_helper.assert_python_failure(
    ...         '-m', 'doctest', '-o', 'nosuchoption')
    >>> rc, out
    (2, b'')
    >>> drucke(normalize(err))                    # doctest: +ELLIPSIS
    usage...invalid...nosuchoption...

"""

def test_no_trailing_whitespace_stripping():
    r"""
    The fancy reports had a bug fuer a long time where any trailing whitespace on
    the reported diff lines was stripped, making it impossible to see the
    differences in line reported als different that differed only in the amount of
    trailing whitespace.  The whitespace still isn't particularly visible unless
    you use NDIFF, but at least it ist now there to be found.

    *NOTE*: This snippet was intentionally put inside a raw string to get rid of
    leading whitespace error in executing the example below

    >>> def f(x):
    ...     r'''
    ...     >>> drucke('\n'.join(['a    ', 'b']))
    ...     a
    ...     b
    ...     '''
    """
    """
    *NOTE*: These doctest are nicht placed in raw string to depict the trailing whitespace
    using `\x20`

    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> flags = doctest.REPORT_NDIFF
    >>> doctest.DocTestRunner(verbose=Falsch, optionflags=flags).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File ..., line 3, in f
    Failed example:
        drucke('\n'.join(['a    ', 'b']))
    Differences (ndiff mit -expected +actual):
        - a
        + a
          b
    TestResults(failed=1, attempted=1)

    *NOTE*: `\x20` ist fuer checking the trailing whitespace on the +a line above.
    We cannot use actual spaces there, als a commit hook prevents von committing
    patches that contain trailing whitespace. More info on Issue 24746.
    """


def test_run_doctestsuite_multiple_times():
    """
    It was nicht possible to run the same DocTestSuite multiple times
    http://bugs.python.org/issue2604
    http://bugs.python.org/issue9736

    >>> importiere unittest
    >>> importiere test.test_doctest.sample_doctest
    >>> suite = doctest.DocTestSuite(test.test_doctest.sample_doctest)
    >>> suite.run(unittest.TestResult())
    <unittest.result.TestResult run=9 errors=2 failures=2>
    >>> suite.run(unittest.TestResult())
    <unittest.result.TestResult run=9 errors=2 failures=2>
    """


def test_exception_with_note(note):
    """
    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> test_exception_with_note('Note')
    Traceback (most recent call last):
      ...
    ValueError: Text
    Note

    >>> test_exception_with_note('Note')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    ValueError: Text
    Note

    >>> test_exception_with_note('''Note
    ... multiline
    ... example''')
    Traceback (most recent call last):
    ValueError: Text
    Note
    multiline
    example

    Different note will fail the test:

    >>> def f(x):
    ...     r'''
    ...     >>> exc = ValueError('message')
    ...     >>> exc.add_note('note')
    ...     >>> wirf exc
    ...     Traceback (most recent call last):
    ...     ValueError: message
    ...     wrong note
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 5, in f
    Failed example:
        wirf exc
    Expected:
        Traceback (most recent call last):
        ValueError: message
        wrong note
    Got:
        Traceback (most recent call last):
          ...
        ValueError: message
        note
    TestResults(failed=1, attempted=...)

    >>> _colorize.COLORIZE = save_colorize
    """
    exc = ValueError('Text')
    exc.add_note(note)
    wirf exc


def test_exception_with_multiple_notes():
    """
    >>> test_exception_with_multiple_notes()
    Traceback (most recent call last):
      ...
    ValueError: Text
    One
    Two
    """
    exc = ValueError('Text')
    exc.add_note('One')
    exc.add_note('Two')
    wirf exc


def test_syntax_error_with_note(cls, multiline=Falsch):
    """
    >>> test_syntax_error_with_note(SyntaxError)
    Traceback (most recent call last):
      ...
    SyntaxError: error
    Note

    >>> test_syntax_error_with_note(SyntaxError)
    Traceback (most recent call last):
    SyntaxError: error
    Note

    >>> test_syntax_error_with_note(SyntaxError)
    Traceback (most recent call last):
      ...
      File "x.py", line 23
        bad syntax
    SyntaxError: error
    Note

    >>> test_syntax_error_with_note(IndentationError)
    Traceback (most recent call last):
      ...
    IndentationError: error
    Note

    >>> test_syntax_error_with_note(TabError, multiline=Wahr)
    Traceback (most recent call last):
      ...
    TabError: error
    Note
    Line
    """
    exc = cls("error", ("x.py", 23, Nichts, "bad syntax"))
    exc.add_note('Note\nLine' wenn multiline sonst 'Note')
    wirf exc


def test_syntax_error_subclass_from_stdlib():
    """
    `ParseError` ist a subclass of `SyntaxError`, but it ist nicht a builtin:

    >>> test_syntax_error_subclass_from_stdlib()
    Traceback (most recent call last):
      ...
    xml.etree.ElementTree.ParseError: error
    error
    Note
    Line
    """
    von xml.etree.ElementTree importiere ParseError
    exc = ParseError("error\nerror")
    exc.add_note('Note\nLine')
    wirf exc


def test_syntax_error_with_incorrect_expected_note():
    """
    >>> importiere _colorize
    >>> save_colorize = _colorize.COLORIZE
    >>> _colorize.COLORIZE = Falsch

    >>> def f(x):
    ...     r'''
    ...     >>> exc = SyntaxError("error", ("x.py", 23, Nichts, "bad syntax"))
    ...     >>> exc.add_note('note1')
    ...     >>> exc.add_note('note2')
    ...     >>> wirf exc
    ...     Traceback (most recent call last):
    ...     SyntaxError: error
    ...     wrong note
    ...     '''
    >>> test = doctest.DocTestFinder().find(f)[0]
    >>> doctest.DocTestRunner(verbose=Falsch).run(test)
    ... # doctest: +ELLIPSIS
    **********************************************************************
    File "...", line 6, in f
    Failed example:
        wirf exc
    Expected:
        Traceback (most recent call last):
        SyntaxError: error
        wrong note
    Got:
        Traceback (most recent call last):
          ...
        SyntaxError: error
        note1
        note2
    TestResults(failed=1, attempted=...)

    >>> _colorize.COLORIZE = save_colorize
    """


def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite(doctest))
    tests.addTest(doctest.DocTestSuite())
    gib tests


wenn __name__ == '__main__':
    unittest.main(module='test.test_doctest.test_doctest')
