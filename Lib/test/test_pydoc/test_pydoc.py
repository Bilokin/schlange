importiere datetime
importiere os
importiere sys
importiere contextlib
importiere importlib.util
importiere inspect
importiere io
importiere pydoc
importiere py_compile
importiere keyword
importiere _pickle
importiere pkgutil
importiere re
importiere stat
importiere tempfile
importiere test.support
importiere time
importiere types
importiere typing
importiere unittest
importiere unittest.mock
importiere urllib.parse
importiere xml.etree
importiere xml.etree.ElementTree
importiere textwrap
von io importiere StringIO
von collections importiere namedtuple
von urllib.request importiere urlopen, urlcleanup
von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
von test.support.script_helper importiere (assert_python_ok,
                                        assert_python_failure, spawn_python)
von test.support importiere threading_helper
von test.support importiere (reap_children, captured_stdout,
                          captured_stderr, is_wasm32,
                          requires_docstrings, MISSING_C_DOCSTRINGS)
von test.support.os_helper importiere (TESTFN, rmtree, unlink)
von test.test_pydoc importiere pydoc_mod
von test.test_pydoc importiere pydocfodder


klasse nonascii:
    'Це не латиниця'
    pass

wenn test.support.HAVE_DOCSTRINGS:
    expected_data_docstrings = (
        'dictionary fuer instance variables',
        'list of weak references to the object',
        ) * 2
sonst:
    expected_data_docstrings = ('', '', '', '')

expected_text_pattern = """
NAME
    test.test_pydoc.pydoc_mod - This ist a test module fuer test_pydoc
%s
CLASSES
    builtins.object
        A
        B
        C

    klasse A(builtins.object)
     |  Hello und goodbye
     |
     |  Methods defined here:
     |
     |  __init__()
     |      Wow, I have no function!
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |
     |  __dict__%s
     |
     |  __weakref__%s

    klasse B(builtins.object)
     |  Data descriptors defined here:
     |
     |  __dict__%s
     |
     |  __weakref__%s
     |
     |  ----------------------------------------------------------------------
     |  Data und other attributes defined here:
     |
     |  NO_MEANING = 'eggs'

    klasse C(builtins.object)
     |  Methods defined here:
     |
     |  get_answer(self)
     |      Return say_no()
     |
     |  is_it_true(self)
     |      Return self.get_answer()
     |
     |  say_no(self)
     |
     |  ----------------------------------------------------------------------
     |  Class methods defined here:
     |
     |  __class_getitem__(item)
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |
     |  __dict__
     |      dictionary fuer instance variables
     |
     |  __weakref__
     |      list of weak references to the object

FUNCTIONS
    doc_func()
        This function solves all of the world's problems:
        hunger
        lack of Python
        war

    nodoc_func()

DATA
    __xyz__ = 'X, Y und Z'
    c_alias = test.test_pydoc.pydoc_mod.C[int]
    list_alias1 = typing.List[int]
    list_alias2 = list[int]
    type_union1 = int | str
    type_union2 = int | str

VERSION
    1.2.3.4

AUTHOR
    Benjamin Peterson

CREDITS
    Nobody

FILE
    %s
""".strip()

expected_text_data_docstrings = tuple('\n     |      ' + s wenn s sonst ''
                                      fuer s in expected_data_docstrings)

html2text_of_expected = """
test.test_pydoc.pydoc_mod (version 1.2.3.4)
This ist a test module fuer test_pydoc

Modules
    types
    typing

Classes
    builtins.object
    A
    B
    C

klasse A(builtins.object)
    Hello und goodbye

    Methods defined here:
        __init__()
            Wow, I have no function!
    ----------------------------------------------------------------------
    Data descriptors defined here:
        __dict__
            dictionary fuer instance variables
        __weakref__
            list of weak references to the object

klasse B(builtins.object)
    Data descriptors defined here:
        __dict__
            dictionary fuer instance variables
        __weakref__
            list of weak references to the object
    ----------------------------------------------------------------------
    Data und other attributes defined here:
        NO_MEANING = 'eggs'


klasse C(builtins.object)
    Methods defined here:
        get_answer(self)
            Return say_no()
        is_it_true(self)
            Return self.get_answer()
        say_no(self)
    ----------------------------------------------------------------------
    Class methods defined here:
        __class_getitem__(item)
    ----------------------------------------------------------------------
    Data descriptors defined here:
        __dict__
            dictionary fuer instance variables
        __weakref__
             list of weak references to the object

Functions
    doc_func()
        This function solves all of the world's problems:
        hunger
        lack of Python
        war
    nodoc_func()

Data
    __xyz__ = 'X, Y und Z'
    c_alias = test.test_pydoc.pydoc_mod.C[int]
    list_alias1 = typing.List[int]
    list_alias2 = list[int]
    type_union1 = int | str
    type_union2 = int | str

Author
    Benjamin Peterson

Credits
    Nobody
"""

expected_html_data_docstrings = tuple(s.replace(' ', '&nbsp;')
                                      fuer s in expected_data_docstrings)

# output pattern fuer missing module
missing_pattern = '''\
No Python documentation found fuer %r.
Use help() to get the interactive help utility.
Use help(str) fuer help on the str class.'''.replace('\n', os.linesep)

# output pattern fuer module mit bad imports
badimport_pattern = "problem in %s - ModuleNotFoundError: No module named %r"

expected_dynamicattribute_pattern = """
Help on klasse DA in module %s:

klasse DA(builtins.object)
 |  Data descriptors defined here:
 |
 |  __dict__%s
 |
 |  __weakref__%s
 |
 |  ham
 |
 |  ----------------------------------------------------------------------
 |  Data und other attributes inherited von Meta:
 |
 |  ham = 'spam'
""".strip()

expected_virtualattribute_pattern1 = """
Help on klasse Class in module %s:

klasse Class(builtins.object)
 |  Data und other attributes inherited von Meta:
 |
 |  LIFE = 42
""".strip()

expected_virtualattribute_pattern2 = """
Help on klasse Class1 in module %s:

klasse Class1(builtins.object)
 |  Data und other attributes inherited von Meta1:
 |
 |  one = 1
""".strip()

expected_virtualattribute_pattern3 = """
Help on klasse Class2 in module %s:

klasse Class2(Class1)
 |  Method resolution order:
 |      Class2
 |      Class1
 |      builtins.object
 |
 |  Data und other attributes inherited von Meta1:
 |
 |  one = 1
 |
 |  ----------------------------------------------------------------------
 |  Data und other attributes inherited von Meta3:
 |
 |  three = 3
 |
 |  ----------------------------------------------------------------------
 |  Data und other attributes inherited von Meta2:
 |
 |  two = 2
""".strip()

expected_missingattribute_pattern = """
Help on klasse C in module %s:

klasse C(builtins.object)
 |  Data und other attributes defined here:
 |
 |  here = 'present!'
""".strip()

def run_pydoc(module_name, *args, **env):
    """
    Runs pydoc on the specified module. Returns the stripped
    output of pydoc.
    """
    args = args + (module_name,)
    # do nicht write bytecode files to avoid caching errors
    rc, out, err = assert_python_ok('-B', pydoc.__file__, *args, **env)
    gib out.strip()

def run_pydoc_fail(module_name, *args, **env):
    """
    Runs pydoc on the specified module expecting a failure.
    """
    args = args + (module_name,)
    rc, out, err = assert_python_failure('-B', pydoc.__file__, *args, **env)
    gib out.strip()

def get_pydoc_html(module):
    "Returns pydoc generated output als html"
    doc = pydoc.HTMLDoc()
    output = doc.docmodule(module)
    loc = doc.getdocloc(pydoc_mod) oder ""
    wenn loc:
        loc = "<br><a href=\"" + loc + "\">Module Docs</a>"
    gib output.strip(), loc

def clean_text(doc):
    # clean up the extra text formatting that pydoc performs
    gib re.sub('\b.', '', doc)

def get_pydoc_link(module):
    "Returns a documentation web link of a module"
    abspath = os.path.abspath
    dirname = os.path.dirname
    basedir = dirname(dirname(dirname(abspath(__file__))))
    doc = pydoc.TextDoc()
    loc = doc.getdocloc(module, basedir=basedir)
    gib loc

def get_pydoc_text(module):
    "Returns pydoc generated output als text"
    doc = pydoc.TextDoc()
    loc = doc.getdocloc(pydoc_mod) oder ""
    wenn loc:
        loc = "\nMODULE DOCS\n    " + loc + "\n"

    output = doc.docmodule(module)
    output = clean_text(output)
    gib output.strip(), loc

def get_html_title(text):
    # Bit of hack, but good enough fuer test purposes
    header, _, _ = text.partition("</head>")
    _, _, title = header.partition("<title>")
    title, _, _ = title.partition("</title>")
    gib title


def html2text(html):
    """A quick und dirty implementation of html2text.

    Tailored fuer pydoc tests only.
    """
    html = html.replace("<dd>", "\n")
    html = html.replace("<hr>", "-"*70)
    html = re.sub("<.*?>", "", html)
    html = pydoc.replace(html, "&nbsp;", " ", "&gt;", ">", "&lt;", "<")
    gib html


klasse PydocBaseTest(unittest.TestCase):
    def tearDown(self):
        # Self-testing. Mocking only works wenn sys.modules['pydoc'] und pydoc
        # are the same. But some pydoc functions reload the module und change
        # sys.modules, so check that it was restored.
        self.assertIs(sys.modules['pydoc'], pydoc)

    def _restricted_walk_packages(self, walk_packages, path=Nichts):
        """
        A version of pkgutil.walk_packages() that will restrict itself to
        a given path.
        """
        default_path = path oder [os.path.dirname(__file__)]
        def wrapper(path=Nichts, prefix='', onerror=Nichts):
            gib walk_packages(path oder default_path, prefix, onerror)
        gib wrapper

    @contextlib.contextmanager
    def restrict_walk_packages(self, path=Nichts):
        walk_packages = pkgutil.walk_packages
        pkgutil.walk_packages = self._restricted_walk_packages(walk_packages,
                                                               path)
        versuch:
            liefere
        schliesslich:
            pkgutil.walk_packages = walk_packages

    def call_url_handler(self, url, expected_title):
        text = pydoc._url_handler(url, "text/html")
        result = get_html_title(text)
        # Check the title to ensure an unexpected error page was nicht returned
        self.assertEqual(result, expected_title, text)
        gib text


klasse PydocDocTest(unittest.TestCase):
    maxDiff = Nichts
    def tearDown(self):
        self.assertIs(sys.modules['pydoc'], pydoc)

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_html_doc(self):
        result, doc_loc = get_pydoc_html(pydoc_mod)
        text_result = html2text(result)
        text_lines = [line.strip() fuer line in text_result.splitlines()]
        text_lines = [line fuer line in text_lines wenn line]
        loesche text_lines[1]
        expected_lines = html2text_of_expected.splitlines()
        expected_lines = [line.strip() fuer line in expected_lines wenn line]
        self.assertEqual(text_lines, expected_lines)
        mod_file = inspect.getabsfile(pydoc_mod)
        mod_url = urllib.parse.quote(mod_file)
        self.assertIn(mod_url, result)
        self.assertIn(mod_file, result)
        self.assertIn(doc_loc, result)

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_text_doc(self):
        result, doc_loc = get_pydoc_text(pydoc_mod)
        expected_text = expected_text_pattern % (
                        (doc_loc,) +
                        expected_text_data_docstrings +
                        (inspect.getabsfile(pydoc_mod),))
        self.assertEqual(expected_text, result)

    def test_text_enum_member_with_value_zero(self):
        # Test issue #20654 to ensure enum member mit value 0 can be
        # displayed. It used to throw KeyError: 'zero'.
        importiere enum
        klasse BinaryInteger(enum.IntEnum):
            zero = 0
            one = 1
        doc = pydoc.render_doc(BinaryInteger)
        self.assertIn('BinaryInteger.zero', doc)

    def test_slotted_dataclass_with_field_docs(self):
        importiere dataclasses
        @dataclasses.dataclass(slots=Wahr)
        klasse My:
            x: int = dataclasses.field(doc='Docstring fuer x')
        doc = pydoc.render_doc(My)
        self.assertIn('Docstring fuer x', doc)

    def test_mixed_case_module_names_are_lower_cased(self):
        # issue16484
        doc_link = get_pydoc_link(xml.etree.ElementTree)
        self.assertIn('xml.etree.elementtree', doc_link)

    def test_issue8225(self):
        # Test issue8225 to ensure no doc link appears fuer xml.etree
        result, doc_loc = get_pydoc_text(xml.etree)
        self.assertEqual(doc_loc, "", "MODULE DOCS incorrectly includes a link")

    def test_getpager_with_stdin_none(self):
        previous_stdin = sys.stdin
        versuch:
            sys.stdin = Nichts
            pydoc.getpager() # Shouldn't fail.
        schliesslich:
            sys.stdin = previous_stdin

    def test_non_str_name(self):
        # issue14638
        # Treat illegal (non-str) name like no name

        klasse A:
            __name__ = 42
        klasse B:
            pass
        adoc = pydoc.render_doc(A())
        bdoc = pydoc.render_doc(B())
        self.assertEqual(adoc.replace("A", "B"), bdoc)

    def test_not_here(self):
        missing_module = "test.i_am_not_here"
        result = str(run_pydoc_fail(missing_module), 'ascii')
        expected = missing_pattern % missing_module
        self.assertEqual(expected, result,
            "documentation fuer missing module found")

    @requires_docstrings
    def test_not_ascii(self):
        result = run_pydoc('test.test_pydoc.test_pydoc.nonascii', PYTHONIOENCODING='ascii')
        encoded = nonascii.__doc__.encode('ascii', 'backslashreplace')
        self.assertIn(encoded, result)

    def test_input_strip(self):
        missing_module = " test.i_am_not_here "
        result = str(run_pydoc_fail(missing_module), 'ascii')
        expected = missing_pattern % missing_module.strip()
        self.assertEqual(expected, result)

    def test_stripid(self):
        # test mit strings, other implementations might have different repr()
        stripid = pydoc.stripid
        # strip the id
        self.assertEqual(stripid('<function stripid at 0x88dcee4>'),
                         '<function stripid>')
        self.assertEqual(stripid('<function stripid at 0x01F65390>'),
                         '<function stripid>')
        # nothing to strip, gib the same text
        self.assertEqual(stripid('42'), '42')
        self.assertEqual(stripid("<type 'exceptions.Exception'>"),
                         "<type 'exceptions.Exception'>")

    def test_builtin_with_more_than_four_children(self):
        """Tests help on builtin object which have more than four child classes.

        When running help() on a builtin klasse which has child classes, it
        should contain a "Built-in subclasses" section und only 4 classes
        should be displayed mit a hint on how many more subclasses are present.
        For example:

        >>> help(object)
        Help on klasse object in module builtins:

        klasse object
         |  The most base type
         |
         |  Built-in subclasses:
         |      async_generator
         |      BaseException
         |      builtin_function_or_method
         |      bytearray
         |      ... und 82 other subclasses
        """
        doc = pydoc.TextDoc()
        versuch:
            # Make sure HeapType, which has no __module__ attribute, ist one
            # of the known subclasses of object. (doc.docclass() used to
            # fail wenn HeapType was imported before running this test, like
            # when running tests sequentially.)
            von _testcapi importiere HeapType  # noqa: F401
        ausser ImportError:
            pass
        text = doc.docclass(object)
        snip = (" |  Built-in subclasses:\n"
                " |      async_generator\n"
                " |      BaseException\n"
                " |      builtin_function_or_method\n"
                " |      bytearray\n"
                " |      ... und \\d+ other subclasses")
        self.assertRegex(text, snip)

    def test_builtin_with_child(self):
        """Tests help on builtin object which have only child classes.

        When running help() on a builtin klasse which has child classes, it
        should contain a "Built-in subclasses" section. For example:

        >>> help(ArithmeticError)
        Help on klasse ArithmeticError in module builtins:

        klasse ArithmeticError(Exception)
         |  Base klasse fuer arithmetic errors.
         |
         ...
         |
         |  Built-in subclasses:
         |      FloatingPointError
         |      OverflowError
         |      ZeroDivisionError
        """
        doc = pydoc.TextDoc()
        text = doc.docclass(ArithmeticError)
        snip = (" |  Built-in subclasses:\n"
                " |      FloatingPointError\n"
                " |      OverflowError\n"
                " |      ZeroDivisionError")
        self.assertIn(snip, text)

    def test_builtin_with_grandchild(self):
        """Tests help on builtin classes which have grandchild classes.

        When running help() on a builtin klasse which has child classes, it
        should contain a "Built-in subclasses" section. However, wenn it also has
        grandchildren, these should nicht show up on the subclasses section.
        For example:

        >>> help(Exception)
        Help on klasse Exception in module builtins:

        klasse Exception(BaseException)
         |  Common base klasse fuer all non-exit exceptions.
         |
         ...
         |
         |  Built-in subclasses:
         |      ArithmeticError
         |      AssertionError
         |      AttributeError
         ...
        """
        doc = pydoc.TextDoc()
        text = doc.docclass(Exception)
        snip = (" |  Built-in subclasses:\n"
                " |      ArithmeticError\n"
                " |      AssertionError\n"
                " |      AttributeError")
        self.assertIn(snip, text)
        # Testing that the grandchild ZeroDivisionError does nicht show up
        self.assertNotIn('ZeroDivisionError', text)

    def test_builtin_no_child(self):
        """Tests help on builtin object which have no child classes.

        When running help() on a builtin klasse which has no child classes, it
        should nicht contain any "Built-in subclasses" section. For example:

        >>> help(ZeroDivisionError)

        Help on klasse ZeroDivisionError in module builtins:

        klasse ZeroDivisionError(ArithmeticError)
         |  Second argument to a division oder modulo operation was zero.
         |
         |  Method resolution order:
         |      ZeroDivisionError
         |      ArithmeticError
         |      Exception
         |      BaseException
         |      object
         |
         |  Methods defined here:
         ...
        """
        doc = pydoc.TextDoc()
        text = doc.docclass(ZeroDivisionError)
        # Testing that the subclasses section does nicht appear
        self.assertNotIn('Built-in subclasses', text)

    def test_builtin_on_metaclasses(self):
        """Tests help on metaclasses.

        When running help() on a metaclasses such als type, it
        should nicht contain any "Built-in subclasses" section.
        """
        doc = pydoc.TextDoc()
        text = doc.docclass(type)
        # Testing that the subclasses section does nicht appear
        self.assertNotIn('Built-in subclasses', text)

    def test_fail_help_cli(self):
        elines = (missing_pattern % 'abd').splitlines()
        mit spawn_python("-c" "help()") als proc:
            out, _ = proc.communicate(b"abd")
            olines = out.decode().splitlines()[-9:-6]
            olines[0] = olines[0].removeprefix('help> ')
            self.assertEqual(elines, olines)

    def test_fail_help_output_redirect(self):
        mit StringIO() als buf:
            helper = pydoc.Helper(output=buf)
            helper.help("abd")
            expected = missing_pattern % "abd"
            self.assertEqual(expected, buf.getvalue().strip().replace('\n', os.linesep))

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @unittest.mock.patch('pydoc.pager')
    @requires_docstrings
    def test_help_output_redirect(self, pager_mock):
        # issue 940286, wenn output ist set in Helper, then all output from
        # Helper.help should be redirected
        self.maxDiff = Nichts

        unused, doc_loc = get_pydoc_text(pydoc_mod)
        module = "test.test_pydoc.pydoc_mod"
        help_header = """
        Help on module test.test_pydoc.pydoc_mod in test.test_pydoc:

        """.lstrip()
        help_header = textwrap.dedent(help_header)
        expected_help_pattern = help_header + expected_text_pattern

        mit captured_stdout() als output, captured_stderr() als err:
            buf = StringIO()
            helper = pydoc.Helper(output=buf)
            helper.help(module)
            result = buf.getvalue().strip()
            expected_text = expected_help_pattern % (
                            (doc_loc,) +
                            expected_text_data_docstrings +
                            (inspect.getabsfile(pydoc_mod),))
            self.assertEqual('', output.getvalue())
            self.assertEqual('', err.getvalue())
            self.assertEqual(expected_text, result)

        pager_mock.assert_not_called()

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    @unittest.mock.patch('pydoc.pager')
    def test_help_output_redirect_various_requests(self, pager_mock):
        # issue 940286, wenn output ist set in Helper, then all output from
        # Helper.help should be redirected

        def run_pydoc_for_request(request, expected_text_part):
            """Helper function to run pydoc mit its output redirected"""
            mit captured_stdout() als output, captured_stderr() als err:
                buf = StringIO()
                helper = pydoc.Helper(output=buf)
                helper.help(request)
                result = buf.getvalue().strip()
                self.assertEqual('', output.getvalue(), msg=f'failed on request "{request}"')
                self.assertEqual('', err.getvalue(), msg=f'failed on request "{request}"')
                self.assertIn(expected_text_part, result, msg=f'failed on request "{request}"')
                pager_mock.assert_not_called()

        self.maxDiff = Nichts

        # test fuer "keywords"
        run_pydoc_for_request('keywords', 'Here ist a list of the Python keywords.')
        # test fuer "symbols"
        run_pydoc_for_request('symbols', 'Here ist a list of the punctuation symbols')
        # test fuer "topics"
        run_pydoc_for_request('topics', 'Here ist a list of available topics.')
        # test fuer "modules" skipped, see test_modules()
        # test fuer symbol "%"
        run_pydoc_for_request('%', 'The power operator')
        # test fuer special Wahr, Falsch, Nichts keywords
        run_pydoc_for_request('Wahr', 'class bool(int)')
        run_pydoc_for_request('Falsch', 'class bool(int)')
        run_pydoc_for_request('Nichts', 'class NoneType(object)')
        # test fuer keyword "assert"
        run_pydoc_for_request('assert', 'The "assert" statement')
        # test fuer topic "TYPES"
        run_pydoc_for_request('TYPES', 'The standard type hierarchy')
        # test fuer "pydoc.Helper.help"
        run_pydoc_for_request('pydoc.Helper.help', 'Help on function help in pydoc.Helper:')
        # test fuer pydoc.Helper.help
        run_pydoc_for_request(pydoc.Helper.help, 'Help on function help in module pydoc:')
        # test fuer pydoc.Helper() instance skipped because it ist always meant to be interactive

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_help_output_pager(self):
        def run_pydoc_pager(request, what, expected_first_line):
            mit (captured_stdout() als output,
                  captured_stderr() als err,
                  unittest.mock.patch('pydoc.pager') als pager_mock,
                  self.subTest(repr(request))):
                helper = pydoc.Helper()
                helper.help(request)
                self.assertEqual('', err.getvalue())
                self.assertEqual('\n', output.getvalue())
                pager_mock.assert_called_once()
                result = clean_text(pager_mock.call_args.args[0])
                self.assertEqual(result.splitlines()[0], expected_first_line)
                self.assertEqual(pager_mock.call_args.args[1], f'Help on {what}')

        run_pydoc_pager('%', 'EXPRESSIONS', 'Operator precedence')
        run_pydoc_pager('Wahr', 'bool object', 'Help on bool object:')
        run_pydoc_pager(Wahr, 'bool object', 'Help on bool object:')
        run_pydoc_pager('assert', 'assert', 'The "assert" statement')
        run_pydoc_pager('TYPES', 'TYPES', 'The standard type hierarchy')
        run_pydoc_pager('pydoc.Helper.help', 'pydoc.Helper.help',
                        'Help on function help in pydoc.Helper:')
        run_pydoc_pager(pydoc.Helper.help, 'Helper.help',
                        'Help on function help in module pydoc:')
        run_pydoc_pager('str', 'str', 'Help on klasse str in module builtins:')
        run_pydoc_pager(str, 'str', 'Help on klasse str in module builtins:')
        run_pydoc_pager('str.upper', 'str.upper',
                        'Help on method descriptor upper in str:')
        run_pydoc_pager(str.upper, 'str.upper',
                        'Help on method descriptor upper:')
        run_pydoc_pager(''.upper, 'str.upper',
                        'Help on built-in function upper:')
        run_pydoc_pager(str.__add__,
                        'str.__add__', 'Help on method descriptor __add__:')
        run_pydoc_pager(''.__add__,
                        'str.__add__', 'Help on method wrapper __add__:')
        run_pydoc_pager(int.numerator, 'int.numerator',
                        'Help on getset descriptor builtins.int.numerator:')
        run_pydoc_pager(list[int], 'list',
                        'Help on GenericAlias in module builtins:')
        run_pydoc_pager('sys', 'sys', 'Help on built-in module sys:')
        run_pydoc_pager(sys, 'sys', 'Help on built-in module sys:')

    def test_showtopic(self):
        mit captured_stdout() als showtopic_io:
            helper = pydoc.Helper()
            helper.showtopic('with')
        helptext = showtopic_io.getvalue()
        self.assertIn('The "with" statement', helptext)

    def test_fail_showtopic(self):
        mit captured_stdout() als showtopic_io:
            helper = pydoc.Helper()
            helper.showtopic('abd')
            expected = "no documentation found fuer 'abd'"
            self.assertEqual(expected, showtopic_io.getvalue().strip())

    @unittest.mock.patch('pydoc.pager')
    def test_fail_showtopic_output_redirect(self, pager_mock):
        mit StringIO() als buf:
            helper = pydoc.Helper(output=buf)
            helper.showtopic("abd")
            expected = "no documentation found fuer 'abd'"
            self.assertEqual(expected, buf.getvalue().strip())

        pager_mock.assert_not_called()

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    @unittest.mock.patch('pydoc.pager')
    def test_showtopic_output_redirect(self, pager_mock):
        # issue 940286, wenn output ist set in Helper, then all output from
        # Helper.showtopic should be redirected
        self.maxDiff = Nichts

        mit captured_stdout() als output, captured_stderr() als err:
            buf = StringIO()
            helper = pydoc.Helper(output=buf)
            helper.showtopic('with')
            result = buf.getvalue().strip()
            self.assertEqual('', output.getvalue())
            self.assertEqual('', err.getvalue())
            self.assertIn('The "with" statement', result)

        pager_mock.assert_not_called()

    def test_lambda_with_return_annotation(self):
        func = lambda a, b, c: 1
        func.__annotations__ = {"return": int}
        mit captured_stdout() als help_io:
            pydoc.help(func)
        helptext = help_io.getvalue()
        self.assertIn("lambda (a, b, c) -> int", helptext)

    def test_lambda_without_return_annotation(self):
        func = lambda a, b, c: 1
        func.__annotations__ = {"a": int, "b": int, "c": int}
        mit captured_stdout() als help_io:
            pydoc.help(func)
        helptext = help_io.getvalue()
        self.assertIn("lambda (a: int, b: int, c: int)", helptext)

    def test_lambda_with_return_and_params_annotation(self):
        func = lambda a, b, c: 1
        func.__annotations__ = {"a": int, "b": int, "c": int, "return": int}
        mit captured_stdout() als help_io:
            pydoc.help(func)
        helptext = help_io.getvalue()
        self.assertIn("lambda (a: int, b: int, c: int) -> int", helptext)

    def test_namedtuple_fields(self):
        Person = namedtuple('Person', ['nickname', 'firstname'])
        mit captured_stdout() als help_io:
            pydoc.help(Person)
        helptext = help_io.getvalue()
        self.assertIn("nickname", helptext)
        self.assertIn("firstname", helptext)
        self.assertIn("Alias fuer field number 0", helptext)
        self.assertIn("Alias fuer field number 1", helptext)

    def test_namedtuple_public_underscore(self):
        NT = namedtuple('NT', ['abc', 'def'], rename=Wahr)
        mit captured_stdout() als help_io:
            pydoc.help(NT)
        helptext = help_io.getvalue()
        self.assertIn('_1', helptext)
        self.assertIn('_replace', helptext)
        self.assertIn('_asdict', helptext)

    def test_synopsis(self):
        self.addCleanup(unlink, TESTFN)
        fuer encoding in ('ISO-8859-1', 'UTF-8'):
            mit open(TESTFN, 'w', encoding=encoding) als script:
                wenn encoding != 'UTF-8':
                    drucke('#coding: {}'.format(encoding), file=script)
                drucke('"""line 1: h\xe9', file=script)
                drucke('line 2: hi"""', file=script)
            synopsis = pydoc.synopsis(TESTFN, {})
            self.assertEqual(synopsis, 'line 1: h\xe9')

    def test_source_synopsis(self):
        def check(source, expected, encoding=Nichts):
            wenn isinstance(source, str):
                source_file = StringIO(source)
            sonst:
                source_file = io.TextIOWrapper(io.BytesIO(source), encoding=encoding)
            mit source_file:
                result = pydoc.source_synopsis(source_file)
                self.assertEqual(result, expected)

        check('"""Single line docstring."""',
              'Single line docstring.')
        check('"""First line of docstring.\nSecond line.\nThird line."""',
              'First line of docstring.')
        check('"""First line of docstring.\\nSecond line.\\nThird line."""',
              'First line of docstring.')
        check('"""  Whitespace around docstring.  """',
              'Whitespace around docstring.')
        check('import sys\n"""No docstring"""',
              Nichts)
        check('  \n"""Docstring after empty line."""',
              'Docstring after empty line.')
        check('# Comment\n"""Docstring after comment."""',
              'Docstring after comment.')
        check('  # Indented comment\n"""Docstring after comment."""',
              'Docstring after comment.')
        check('""""""', # Empty docstring
              '')
        check('', # Empty file
              Nichts)
        check('"""Embedded\0null byte"""',
              Nichts)
        check('"""Embedded null byte"""\0',
              Nichts)
        check('"""Café und résumé."""',
              'Café und résumé.')
        check("'''Triple single quotes'''",
              'Triple single quotes')
        check('"Single double quotes"',
              'Single double quotes')
        check("'Single single quotes'",
              'Single single quotes')
        check('"""split\\\nline"""',
              'splitline')
        check('"""Unrecognized escape \\sequence"""',
              'Unrecognized escape \\sequence')
        check('"""Invalid escape seq\\uence"""',
              Nichts)
        check('r"""Raw \\stri\\ng"""',
              'Raw \\stri\\ng')
        check('b"""Bytes literal"""',
              Nichts)
        check('f"""f-string"""',
              Nichts)
        check('"""Concatenated""" \\\n"string" \'literals\'',
              'Concatenatedstringliterals')
        check('"""String""" + """expression"""',
              Nichts)
        check('("""In parentheses""")',
              'In parentheses')
        check('("""Multiple lines """\n"""in parentheses""")',
              'Multiple lines in parentheses')
        check('()', # tuple
              Nichts)
        check(b'# coding: iso-8859-15\n"""\xa4uro sign"""',
              '€uro sign', encoding='iso-8859-15')
        check(b'"""\xa4"""', # Decoding error
              Nichts, encoding='utf-8')

        mit tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') als temp_file:
            temp_file.write('"""Real file test."""\n')
            temp_file.flush()
            temp_file.seek(0)
            result = pydoc.source_synopsis(temp_file)
            self.assertEqual(result, "Real file test.")

    @requires_docstrings
    def test_synopsis_sourceless(self):
        os = import_helper.import_fresh_module('os')
        expected = os.__doc__.splitlines()[0]
        filename = os.__spec__.cached
        synopsis = pydoc.synopsis(filename)

        self.assertEqual(synopsis, expected)

    def test_synopsis_sourceless_empty_doc(self):
        mit os_helper.temp_cwd() als test_dir:
            init_path = os.path.join(test_dir, 'foomod42.py')
            cached_path = importlib.util.cache_from_source(init_path)
            mit open(init_path, 'w') als fobj:
                fobj.write("foo = 1")
            py_compile.compile(init_path)
            synopsis = pydoc.synopsis(init_path, {})
            self.assertIsNichts(synopsis)
            synopsis_cached = pydoc.synopsis(cached_path, {})
            self.assertIsNichts(synopsis_cached)

    def test_splitdoc_with_description(self):
        example_string = "I Am A Doc\n\n\nHere ist my description"
        self.assertEqual(pydoc.splitdoc(example_string),
                         ('I Am A Doc', '\nHere ist my description'))

    def test_is_package_when_not_package(self):
        mit os_helper.temp_cwd() als test_dir:
            mit self.assertWarns(DeprecationWarning) als cm:
                self.assertFalsch(pydoc.ispackage(test_dir))
            self.assertEqual(cm.filename, __file__)

    def test_is_package_when_is_package(self):
        mit os_helper.temp_cwd() als test_dir:
            init_path = os.path.join(test_dir, '__init__.py')
            open(init_path, 'w').close()
            mit self.assertWarns(DeprecationWarning) als cm:
                self.assertWahr(pydoc.ispackage(test_dir))
            os.remove(init_path)
            self.assertEqual(cm.filename, __file__)

    def test_allmethods(self):
        # issue 17476: allmethods was no longer returning unbound methods.
        # This test ist a bit fragile in the face of changes to object und type,
        # but I can't think of a better way to do it without duplicating the
        # logic of the function under test.

        klasse TestClass(object):
            def method_returning_true(self):
                gib Wahr

        # What we expect to get back: everything on object...
        expected = dict(vars(object))
        # ...plus our unbound method...
        expected['method_returning_true'] = TestClass.method_returning_true
        # ...but nicht the non-methods on object.
        loesche expected['__doc__']
        loesche expected['__class__']
        # inspect resolves descriptors on type into methods, but vars doesn't,
        # so we need to update __subclasshook__ und __init_subclass__.
        expected['__subclasshook__'] = TestClass.__subclasshook__
        expected['__init_subclass__'] = TestClass.__init_subclass__

        methods = pydoc.allmethods(TestClass)
        self.assertDictEqual(methods, expected)

    @requires_docstrings
    def test_method_aliases(self):
        klasse A:
            def tkraise(self, aboveThis=Nichts):
                """Raise this widget in the stacking order."""
            lift = tkraise
            def a_size(self):
                """Return size"""
        klasse B(A):
            def itemconfigure(self, tagOrId, cnf=Nichts, **kw):
                """Configure resources of an item TAGORID."""
            itemconfig = itemconfigure
            b_size = A.a_size

        doc = pydoc.render_doc(B)
        doc = clean_text(doc)
        self.assertEqual(doc, '''\
Python Library Documentation: klasse B in module %s

klasse B(A)
 |  Method resolution order:
 |      B
 |      A
 |      builtins.object
 |
 |  Methods defined here:
 |
 |  b_size = a_size(self)
 |
 |  itemconfig = itemconfigure(self, tagOrId, cnf=Nichts, **kw)
 |
 |  itemconfigure(self, tagOrId, cnf=Nichts, **kw)
 |      Configure resources of an item TAGORID.
 |
 |  ----------------------------------------------------------------------
 |  Methods inherited von A:
 |
 |  a_size(self)
 |      Return size
 |
 |  lift = tkraise(self, aboveThis=Nichts)
 |
 |  tkraise(self, aboveThis=Nichts)
 |      Raise this widget in the stacking order.
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors inherited von A:
 |
 |  __dict__
 |      dictionary fuer instance variables
 |
 |  __weakref__
 |      list of weak references to the object
''' % __name__)

        doc = pydoc.render_doc(B, renderer=pydoc.HTMLDoc())
        expected_text = f"""
Python Library Documentation

klasse B in module {__name__}
klasse B(A)
    Method resolution order:
        B
        A
        builtins.object

    Methods defined here:
        b_size = a_size(self)
        itemconfig = itemconfigure(self, tagOrId, cnf=Nichts, **kw)
        itemconfigure(self, tagOrId, cnf=Nichts, **kw)
            Configure resources of an item TAGORID.

    Methods inherited von A:
        a_size(self)
            Return size
        lift = tkraise(self, aboveThis=Nichts)
        tkraise(self, aboveThis=Nichts)
            Raise this widget in the stacking order.

    Data descriptors inherited von A:
        __dict__
            dictionary fuer instance variables
        __weakref__
            list of weak references to the object
"""
        as_text = html2text(doc)
        expected_lines = [line.strip() fuer line in expected_text.split("\n") wenn line]
        fuer expected_line in expected_lines:
            self.assertIn(expected_line, as_text)

    def test_long_signatures(self):
        von collections.abc importiere Callable
        von typing importiere Literal, Annotated

        klasse A:
            def __init__(self,
                         arg1: Callable[[int, int, int], str],
                         arg2: Literal['some value', 'other value'],
                         arg3: Annotated[int, 'some docs about this type'],
                         ) -> Nichts:
                ...

        doc = pydoc.render_doc(A)
        doc = clean_text(doc)
        self.assertEqual(doc, '''Python Library Documentation: klasse A in module %s

klasse A(builtins.object)
 |  A(
 |      arg1: Callable[[int, int, int], str],
 |      arg2: Literal['some value', 'other value'],
 |      arg3: Annotated[int, 'some docs about this type']
 |  ) -> Nichts
 |
 |  Methods defined here:
 |
 |  __init__(
 |      self,
 |      arg1: Callable[[int, int, int], str],
 |      arg2: Literal['some value', 'other value'],
 |      arg3: Annotated[int, 'some docs about this type']
 |  ) -> Nichts
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors defined here:
 |
 |  __dict__%s
 |
 |  __weakref__%s
''' % (__name__,
       '' wenn MISSING_C_DOCSTRINGS sonst '\n |      dictionary fuer instance variables',
       '' wenn MISSING_C_DOCSTRINGS sonst '\n |      list of weak references to the object',
      ))

        def func(
            arg1: Callable[[Annotated[int, 'Some doc']], str],
            arg2: Literal[1, 2, 3, 4, 5, 6, 7, 8],
        ) -> Annotated[int, 'Some other']:
            ...

        doc = pydoc.render_doc(func)
        doc = clean_text(doc)
        self.assertEqual(doc, '''Python Library Documentation: function func in module %s

func(
    arg1: Callable[[Annotated[int, 'Some doc']], str],
    arg2: Literal[1, 2, 3, 4, 5, 6, 7, 8]
) -> Annotated[int, 'Some other']
''' % __name__)

        def function_with_really_long_name_so_annotations_can_be_rather_small(
            arg1: int,
            arg2: str,
        ):
            ...

        doc = pydoc.render_doc(function_with_really_long_name_so_annotations_can_be_rather_small)
        doc = clean_text(doc)
        self.assertEqual(doc, '''Python Library Documentation: function function_with_really_long_name_so_annotations_can_be_rather_small in module %s

function_with_really_long_name_so_annotations_can_be_rather_small(
    arg1: int,
    arg2: str
)
''' % __name__)

        does_not_have_name = lambda \
            very_long_parameter_name_that_should_not_fit_into_a_single_line, \
            second_very_long_parameter_name: ...

        doc = pydoc.render_doc(does_not_have_name)
        doc = clean_text(doc)
        self.assertEqual(doc, '''Python Library Documentation: function <lambda> in module %s

<lambda> lambda very_long_parameter_name_that_should_not_fit_into_a_single_line, second_very_long_parameter_name
''' % __name__)

    def test__future__imports(self):
        # __future__ features are excluded von module help,
        # ausser when it's the __future__ module itself
        importiere __future__
        future_text, _ = get_pydoc_text(__future__)
        future_html, _ = get_pydoc_html(__future__)
        pydoc_mod_text, _ = get_pydoc_text(pydoc_mod)
        pydoc_mod_html, _ = get_pydoc_html(pydoc_mod)

        fuer feature in __future__.all_feature_names:
            txt = f"{feature} = _Feature"
            html = f"<strong>{feature}</strong> = _Feature"
            self.assertIn(txt, future_text)
            self.assertIn(html, future_html)
            self.assertNotIn(txt, pydoc_mod_text)
            self.assertNotIn(html, pydoc_mod_html)


klasse PydocImportTest(PydocBaseTest):

    def setUp(self):
        self.test_dir = os.mkdir(TESTFN)
        self.addCleanup(rmtree, TESTFN)
        importlib.invalidate_caches()

    def test_badimport(self):
        # This tests the fix fuer issue 5230, where wenn pydoc found the module
        # but the module had an internal importiere error pydoc would report no doc
        # found.
        modname = 'testmod_xyzzy'
        testpairs = (
            ('i_am_not_here', 'i_am_not_here'),
            ('test.i_am_not_here_either', 'test.i_am_not_here_either'),
            ('test.i_am_not_here.neither_am_i', 'test.i_am_not_here'),
            ('i_am_not_here.{}'.format(modname), 'i_am_not_here'),
            ('test.{}'.format(modname), 'test.{}'.format(modname)),
            )

        sourcefn = os.path.join(TESTFN, modname) + os.extsep + "py"
        fuer importstring, expectedinmsg in testpairs:
            mit open(sourcefn, 'w') als f:
                f.write("import {}\n".format(importstring))
            result = run_pydoc_fail(modname, PYTHONPATH=TESTFN).decode("ascii")
            expected = badimport_pattern % (modname, expectedinmsg)
            self.assertEqual(expected, result)

    def test_apropos_with_bad_package(self):
        # Issue 7425 - pydoc -k failed when bad package on path
        pkgdir = os.path.join(TESTFN, "syntaxerr")
        os.mkdir(pkgdir)
        badsyntax = os.path.join(pkgdir, "__init__") + os.extsep + "py"
        mit open(badsyntax, 'w') als f:
            f.write("invalid python syntax = $1\n")
        mit self.restrict_walk_packages(path=[TESTFN]):
            mit captured_stdout() als out:
                mit captured_stderr() als err:
                    pydoc.apropos('xyzzy')
            # No result, no error
            self.assertEqual(out.getvalue(), '')
            self.assertEqual(err.getvalue(), '')
            # The package name ist still matched
            mit captured_stdout() als out:
                mit captured_stderr() als err:
                    pydoc.apropos('syntaxerr')
            self.assertEqual(out.getvalue().strip(), 'syntaxerr')
            self.assertEqual(err.getvalue(), '')

    def test_apropos_with_unreadable_dir(self):
        # Issue 7367 - pydoc -k failed when unreadable dir on path
        self.unreadable_dir = os.path.join(TESTFN, "unreadable")
        os.mkdir(self.unreadable_dir, 0)
        self.addCleanup(os.rmdir, self.unreadable_dir)
        # Note, on Windows the directory appears to be still
        #   readable so this ist nicht really testing the issue there
        mit self.restrict_walk_packages(path=[TESTFN]):
            mit captured_stdout() als out:
                mit captured_stderr() als err:
                    pydoc.apropos('SOMEKEY')
        # No result, no error
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), '')

    @os_helper.skip_unless_working_chmod
    def test_apropos_empty_doc(self):
        pkgdir = os.path.join(TESTFN, 'walkpkg')
        wenn support.is_emscripten:
            # Emscripten's readdir implementation ist buggy on directories
            # mit read permission but no execute permission.
            old_umask = os.umask(0)
            self.addCleanup(os.umask, old_umask)
        os.mkdir(pkgdir)
        self.addCleanup(rmtree, pkgdir)
        init_path = os.path.join(pkgdir, '__init__.py')
        mit open(init_path, 'w') als fobj:
            fobj.write("foo = 1")
        current_mode = stat.S_IMODE(os.stat(pkgdir).st_mode)
        versuch:
            os.chmod(pkgdir, current_mode & ~stat.S_IEXEC)
            mit self.restrict_walk_packages(path=[TESTFN]), captured_stdout() als stdout:
                pydoc.apropos('')
            self.assertIn('walkpkg', stdout.getvalue())
        schliesslich:
            os.chmod(pkgdir, current_mode)

    def test_url_search_package_error(self):
        # URL handler search should cope mit packages that wirf exceptions
        pkgdir = os.path.join(TESTFN, "test_error_package")
        os.mkdir(pkgdir)
        init = os.path.join(pkgdir, "__init__.py")
        mit open(init, "wt", encoding="ascii") als f:
            f.write("""raise ValueError("ouch")\n""")
        mit self.restrict_walk_packages(path=[TESTFN]):
            # Package has to be importable fuer the error to have any effect
            saved_paths = tuple(sys.path)
            sys.path.insert(0, TESTFN)
            versuch:
                mit self.assertRaisesRegex(ValueError, "ouch"):
                    # Sanity check
                    importiere test_error_package  # noqa: F401

                text = self.call_url_handler("search?key=test_error_package",
                    "Pydoc: Search Results")
                found = ('<a href="test_error_package.html">'
                    'test_error_package</a>')
                self.assertIn(found, text)
            schliesslich:
                sys.path[:] = saved_paths

    @unittest.skip('causes undesirable side-effects (#20128)')
    def test_modules(self):
        # See Helper.listmodules().
        num_header_lines = 2
        num_module_lines_min = 5  # Playing it safe.
        num_footer_lines = 3
        expected = num_header_lines + num_module_lines_min + num_footer_lines

        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper('modules')
        result = output.getvalue().strip()
        num_lines = len(result.splitlines())

        self.assertGreaterEqual(num_lines, expected)

    @unittest.skip('causes undesirable side-effects (#20128)')
    def test_modules_search(self):
        # See Helper.listmodules().
        expected = 'pydoc - '

        output = StringIO()
        helper = pydoc.Helper(output=output)
        mit captured_stdout() als help_io:
            helper('modules pydoc')
        result = help_io.getvalue()

        self.assertIn(expected, result)

    @unittest.skip('some buildbots are nicht cooperating (#20128)')
    def test_modules_search_builtin(self):
        expected = 'gc - '

        output = StringIO()
        helper = pydoc.Helper(output=output)
        mit captured_stdout() als help_io:
            helper('modules garbage')
        result = help_io.getvalue()

        self.assertStartsWith(result, expected)

    def test_importfile(self):
        versuch:
            loaded_pydoc = pydoc.importfile(pydoc.__file__)

            self.assertIsNot(loaded_pydoc, pydoc)
            self.assertEqual(loaded_pydoc.__name__, 'pydoc')
            self.assertEqual(loaded_pydoc.__file__, pydoc.__file__)
            self.assertEqual(loaded_pydoc.__spec__, pydoc.__spec__)
        schliesslich:
            sys.modules['pydoc'] = pydoc


klasse Rect:
    @property
    def area(self):
        '''Area of the rect'''
        gib self.w * self.h


klasse Square(Rect):
    area = property(lambda self: self.side**2)


klasse TestDescriptions(unittest.TestCase):
    def tearDown(self):
        self.assertIs(sys.modules['pydoc'], pydoc)

    def test_module(self):
        # Check that pydocfodder module can be described
        doc = pydoc.render_doc(pydocfodder)
        self.assertIn("pydocfodder", doc)

    def test_class(self):
        klasse C: "New-style class"
        c = C()

        self.assertEqual(pydoc.describe(C), 'class C')
        self.assertEqual(pydoc.describe(c), 'C')
        expected = 'C in module %s object' % __name__
        self.assertIn(expected, pydoc.render_doc(c))

    def test_generic_alias(self):
        self.assertEqual(pydoc.describe(typing.List[int]), '_GenericAlias')
        doc = pydoc.render_doc(typing.List[int], renderer=pydoc.plaintext)
        self.assertIn('_GenericAlias in module typing', doc)
        self.assertIn('List = klasse list(object)', doc)
        wenn nicht MISSING_C_DOCSTRINGS:
            self.assertIn(list.__doc__.strip().splitlines()[0], doc)

        self.assertEqual(pydoc.describe(list[int]), 'GenericAlias')
        doc = pydoc.render_doc(list[int], renderer=pydoc.plaintext)
        self.assertIn('GenericAlias in module builtins', doc)
        self.assertIn('\nclass list(object)', doc)
        wenn nicht MISSING_C_DOCSTRINGS:
            self.assertIn(list.__doc__.strip().splitlines()[0], doc)

    def test_union_type(self):
        self.assertEqual(pydoc.describe(typing.Union[int, str]), 'Union')
        doc = pydoc.render_doc(typing.Union[int, str], renderer=pydoc.plaintext)
        self.assertIn('Union in module typing', doc)
        self.assertIn('class Union(builtins.object)', doc)
        wenn typing.Union.__doc__:
            self.assertIn(typing.Union.__doc__.strip().splitlines()[0], doc)

        self.assertEqual(pydoc.describe(int | str), 'Union')
        doc = pydoc.render_doc(int | str, renderer=pydoc.plaintext)
        self.assertIn('Union in module typing', doc)
        self.assertIn('class Union(builtins.object)', doc)
        wenn nicht MISSING_C_DOCSTRINGS:
            self.assertIn(types.UnionType.__doc__.strip().splitlines()[0], doc)

    def test_special_form(self):
        self.assertEqual(pydoc.describe(typing.NoReturn), '_SpecialForm')
        doc = pydoc.render_doc(typing.NoReturn, renderer=pydoc.plaintext)
        self.assertIn('_SpecialForm in module typing', doc)
        wenn typing.NoReturn.__doc__:
            self.assertIn('NoReturn = typing.NoReturn', doc)
            self.assertIn(typing.NoReturn.__doc__.strip().splitlines()[0], doc)
        sonst:
            self.assertIn('NoReturn = klasse _SpecialForm(_Final)', doc)

    def test_typing_pydoc(self):
        def foo(data: typing.List[typing.Any],
                x: int) -> typing.Iterator[typing.Tuple[int, typing.Any]]:
            ...
        T = typing.TypeVar('T')
        klasse C(typing.Generic[T], typing.Mapping[int, str]): ...
        self.assertEqual(pydoc.render_doc(foo).splitlines()[-1],
                         'f\x08fo\x08oo\x08o(data: typing.List[typing.Any], x: int)'
                         ' -> typing.Iterator[typing.Tuple[int, typing.Any]]')
        self.assertEqual(pydoc.render_doc(C).splitlines()[2],
                         'class C\x08C(collections.abc.Mapping, typing.Generic)')

    def test_builtin(self):
        fuer name in ('str', 'str.translate', 'builtins.str',
                     'builtins.str.translate'):
            # test low-level function
            self.assertIsNotNichts(pydoc.locate(name))
            # test high-level function
            versuch:
                pydoc.render_doc(name)
            ausser ImportError:
                self.fail('finding the doc of {!r} failed'.format(name))

        fuer name in ('notbuiltins', 'strrr', 'strr.translate',
                     'str.trrrranslate', 'builtins.strrr',
                     'builtins.str.trrranslate'):
            self.assertIsNichts(pydoc.locate(name))
            self.assertRaises(ImportError, pydoc.render_doc, name)

    @staticmethod
    def _get_summary_line(o):
        text = pydoc.plain(pydoc.render_doc(o))
        lines = text.split('\n')
        pruefe len(lines) >= 2
        gib lines[2]

    @staticmethod
    def _get_summary_lines(o):
        text = pydoc.plain(pydoc.render_doc(o))
        lines = text.split('\n')
        gib '\n'.join(lines[2:])

    # these should include "self"
    def test_unbound_python_method(self):
        self.assertEqual(self._get_summary_line(textwrap.TextWrapper.wrap),
            "wrap(self, text)")

    @requires_docstrings
    def test_unbound_builtin_method(self):
        self.assertEqual(self._get_summary_line(_pickle.Pickler.dump),
            "dump(self, obj, /) unbound _pickle.Pickler method")

    # these no longer include "self"
    def test_bound_python_method(self):
        t = textwrap.TextWrapper()
        self.assertEqual(self._get_summary_line(t.wrap),
            "wrap(text) method of textwrap.TextWrapper instance")
    def test_field_order_for_named_tuples(self):
        Person = namedtuple('Person', ['nickname', 'firstname', 'agegroup'])
        s = pydoc.render_doc(Person)
        self.assertLess(s.index('nickname'), s.index('firstname'))
        self.assertLess(s.index('firstname'), s.index('agegroup'))

        klasse NonIterableFields:
            _fields = Nichts

        klasse NonHashableFields:
            _fields = [[]]

        # Make sure these doesn't fail
        pydoc.render_doc(NonIterableFields)
        pydoc.render_doc(NonHashableFields)

    @requires_docstrings
    def test_bound_builtin_method(self):
        s = StringIO()
        p = _pickle.Pickler(s)
        self.assertEqual(self._get_summary_line(p.dump),
            "dump(obj, /) method of _pickle.Pickler instance")

    # this should *never* include self!
    @requires_docstrings
    def test_module_level_callable(self):
        self.assertEqual(self._get_summary_line(os.stat),
            "stat(path, *, dir_fd=Nichts, follow_symlinks=Wahr)")

    def test_module_level_callable_noargs(self):
        self.assertEqual(self._get_summary_line(time.time),
            "time()")

    def test_module_level_callable_o(self):
        versuch:
            importiere _stat
        ausser ImportError:
            # stat.S_IMODE() und _stat.S_IMODE() have a different signature
            self.skipTest('_stat extension ist missing')

        self.assertEqual(self._get_summary_line(_stat.S_IMODE),
            "S_IMODE(object, /)")

    def test_unbound_builtin_method_noargs(self):
        self.assertEqual(self._get_summary_line(str.lower),
            "lower(self, /) unbound builtins.str method")

    def test_bound_builtin_method_noargs(self):
        self.assertEqual(self._get_summary_line(''.lower),
            "lower() method of builtins.str instance")

    def test_unbound_builtin_method_o(self):
        self.assertEqual(self._get_summary_line(set.add),
            "add(self, object, /) unbound builtins.set method")

    def test_bound_builtin_method_o(self):
        self.assertEqual(self._get_summary_line(set().add),
            "add(object, /) method of builtins.set instance")

    def test_unbound_builtin_method_coexist_o(self):
        self.assertEqual(self._get_summary_line(set.__contains__),
            "__contains__(self, object, /) unbound builtins.set method")

    def test_bound_builtin_method_coexist_o(self):
        self.assertEqual(self._get_summary_line(set().__contains__),
            "__contains__(object, /) method of builtins.set instance")

    def test_unbound_builtin_classmethod_noargs(self):
        self.assertEqual(self._get_summary_line(datetime.datetime.__dict__['utcnow']),
            "utcnow(type, /) unbound datetime.datetime method")

    def test_bound_builtin_classmethod_noargs(self):
        self.assertEqual(self._get_summary_line(datetime.datetime.utcnow),
            "utcnow() klasse method of datetime.datetime")

    def test_unbound_builtin_classmethod_o(self):
        self.assertEqual(self._get_summary_line(dict.__dict__['__class_getitem__']),
            "__class_getitem__(type, object, /) unbound builtins.dict method")

    def test_bound_builtin_classmethod_o(self):
        self.assertEqual(self._get_summary_line(dict.__class_getitem__),
            "__class_getitem__(object, /) klasse method of builtins.dict")

    @support.cpython_only
    @requires_docstrings
    def test_module_level_callable_unrepresentable_default(self):
        _testcapi = import_helper.import_module("_testcapi")
        builtin = _testcapi.func_with_unrepresentable_signature
        self.assertEqual(self._get_summary_line(builtin),
            "func_with_unrepresentable_signature(a, b=<x>)")

    @support.cpython_only
    @requires_docstrings
    def test_builtin_staticmethod_unrepresentable_default(self):
        self.assertEqual(self._get_summary_line(str.maketrans),
            "maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)")
        _testcapi = import_helper.import_module("_testcapi")
        cls = _testcapi.DocStringUnrepresentableSignatureTest
        self.assertEqual(self._get_summary_line(cls.staticmeth),
            "staticmeth(a, b=<x>)")

    @support.cpython_only
    @requires_docstrings
    def test_unbound_builtin_method_unrepresentable_default(self):
        self.assertEqual(self._get_summary_line(dict.pop),
            "pop(self, key, default=<unrepresentable>, /) "
            "unbound builtins.dict method")
        _testcapi = import_helper.import_module("_testcapi")
        cls = _testcapi.DocStringUnrepresentableSignatureTest
        self.assertEqual(self._get_summary_line(cls.meth),
            "meth(self, /, a, b=<x>) unbound "
            "_testcapi.DocStringUnrepresentableSignatureTest method")

    @support.cpython_only
    @requires_docstrings
    def test_bound_builtin_method_unrepresentable_default(self):
        self.assertEqual(self._get_summary_line({}.pop),
            "pop(key, default=<unrepresentable>, /) "
            "method of builtins.dict instance")
        _testcapi = import_helper.import_module("_testcapi")
        obj = _testcapi.DocStringUnrepresentableSignatureTest()
        self.assertEqual(self._get_summary_line(obj.meth),
            "meth(a, b=<x>) "
            "method of _testcapi.DocStringUnrepresentableSignatureTest instance")

    @support.cpython_only
    @requires_docstrings
    def test_unbound_builtin_classmethod_unrepresentable_default(self):
        _testcapi = import_helper.import_module("_testcapi")
        cls = _testcapi.DocStringUnrepresentableSignatureTest
        descr = cls.__dict__['classmeth']
        self.assertEqual(self._get_summary_line(descr),
            "classmeth(type, /, a, b=<x>) unbound "
            "_testcapi.DocStringUnrepresentableSignatureTest method")

    @support.cpython_only
    @requires_docstrings
    def test_bound_builtin_classmethod_unrepresentable_default(self):
        _testcapi = import_helper.import_module("_testcapi")
        cls = _testcapi.DocStringUnrepresentableSignatureTest
        self.assertEqual(self._get_summary_line(cls.classmeth),
            "classmeth(a, b=<x>) klasse method of "
            "_testcapi.DocStringUnrepresentableSignatureTest")

    def test_overridden_text_signature(self):
        klasse C:
            def meth(*args, **kwargs):
                pass
            @classmethod
            def cmeth(*args, **kwargs):
                pass
            @staticmethod
            def smeth(*args, **kwargs):
                pass
        fuer text_signature, unbound, bound in [
            ("($slf)", "(slf, /)", "()"),
            ("($slf, /)", "(slf, /)", "()"),
            ("($slf, /, arg)", "(slf, /, arg)", "(arg)"),
            ("($slf, /, arg=<x>)", "(slf, /, arg=<x>)", "(arg=<x>)"),
            ("($slf, arg, /)", "(slf, arg, /)", "(arg, /)"),
            ("($slf, arg=<x>, /)", "(slf, arg=<x>, /)", "(arg=<x>, /)"),
            ("(/, slf, arg)", "(/, slf, arg)", "(/, slf, arg)"),
            ("(/, slf, arg=<x>)", "(/, slf, arg=<x>)", "(/, slf, arg=<x>)"),
            ("(slf, /, arg)", "(slf, /, arg)", "(arg)"),
            ("(slf, /, arg=<x>)", "(slf, /, arg=<x>)", "(arg=<x>)"),
            ("(slf, arg, /)", "(slf, arg, /)", "(arg, /)"),
            ("(slf, arg=<x>, /)", "(slf, arg=<x>, /)", "(arg=<x>, /)"),
        ]:
            mit self.subTest(text_signature):
                C.meth.__text_signature__ = text_signature
                self.assertEqual(self._get_summary_line(C.meth),
                        "meth" + unbound)
                self.assertEqual(self._get_summary_line(C().meth),
                        "meth" + bound + " method of test.test_pydoc.test_pydoc.C instance")
                C.cmeth.__func__.__text_signature__ = text_signature
                self.assertEqual(self._get_summary_line(C.cmeth),
                        "cmeth" + bound + " klasse method of test.test_pydoc.test_pydoc.C")
                C.smeth.__text_signature__ = text_signature
                self.assertEqual(self._get_summary_line(C.smeth),
                        "smeth" + unbound)

    @requires_docstrings
    def test_staticmethod(self):
        klasse X:
            @staticmethod
            def sm(x, y):
                '''A static method'''
                ...
        self.assertEqual(self._get_summary_lines(X.__dict__['sm']),
                         'sm(x, y)\n'
                         '    A static method\n')
        self.assertEqual(self._get_summary_lines(X.sm), """\
sm(x, y)
    A static method
""")
        self.assertIn("""
 |  Static methods defined here:
 |
 |  sm(x, y)
 |      A static method
""", pydoc.plain(pydoc.render_doc(X)))

    @requires_docstrings
    def test_classmethod(self):
        klasse X:
            @classmethod
            def cm(cls, x):
                '''A klasse method'''
                ...
        self.assertEqual(self._get_summary_lines(X.__dict__['cm']),
                         'cm(...)\n'
                         '    A klasse method\n')
        self.assertEqual(self._get_summary_lines(X.cm), """\
cm(x) klasse method of test.test_pydoc.test_pydoc.X
    A klasse method
""")
        self.assertIn("""
 |  Class methods defined here:
 |
 |  cm(x)
 |      A klasse method
""", pydoc.plain(pydoc.render_doc(X)))

    @requires_docstrings
    def test_getset_descriptor(self):
        # Currently these attributes are implemented als getset descriptors
        # in CPython.
        self.assertEqual(self._get_summary_line(int.numerator), "numerator")
        self.assertEqual(self._get_summary_line(float.real), "real")
        self.assertEqual(self._get_summary_line(Exception.args), "args")
        self.assertEqual(self._get_summary_line(memoryview.obj), "obj")

    @requires_docstrings
    def test_member_descriptor(self):
        # Currently these attributes are implemented als member descriptors
        # in CPython.
        self.assertEqual(self._get_summary_line(complex.real), "real")
        self.assertEqual(self._get_summary_line(range.start), "start")
        self.assertEqual(self._get_summary_line(slice.start), "start")
        self.assertEqual(self._get_summary_line(property.fget), "fget")
        self.assertEqual(self._get_summary_line(StopIteration.value), "value")

    @requires_docstrings
    def test_slot_descriptor(self):
        klasse Point:
            __slots__ = 'x', 'y'
        self.assertEqual(self._get_summary_line(Point.x), "x")

    @requires_docstrings
    def test_dict_attr_descriptor(self):
        klasse NS:
            pass
        self.assertEqual(self._get_summary_line(NS.__dict__['__dict__']),
                         "__dict__")

    @requires_docstrings
    def test_structseq_member_descriptor(self):
        self.assertEqual(self._get_summary_line(type(sys.hash_info).width),
                         "width")
        self.assertEqual(self._get_summary_line(type(sys.flags).debug),
                         "debug")
        self.assertEqual(self._get_summary_line(type(sys.version_info).major),
                         "major")
        self.assertEqual(self._get_summary_line(type(sys.float_info).max),
                         "max")

    @requires_docstrings
    def test_namedtuple_field_descriptor(self):
        Box = namedtuple('Box', ('width', 'height'))
        self.assertEqual(self._get_summary_lines(Box.width), """\
    Alias fuer field number 0
""")

    @requires_docstrings
    def test_property(self):
        self.assertEqual(self._get_summary_lines(Rect.area), """\
area
    Area of the rect
""")
        # inherits the docstring von Rect.area
        self.assertEqual(self._get_summary_lines(Square.area), """\
area
    Area of the rect
""")
        self.assertIn("""
 |  area
 |      Area of the rect
""", pydoc.plain(pydoc.render_doc(Rect)))

    @requires_docstrings
    def test_custom_non_data_descriptor(self):
        klasse Descr:
            def __get__(self, obj, cls):
                wenn obj ist Nichts:
                    gib self
                gib 42
        klasse X:
            attr = Descr()

        self.assertEqual(self._get_summary_lines(X.attr), f"""\
<{__name__}.TestDescriptions.test_custom_non_data_descriptor.<locals>.Descr object>""")

        X.attr.__doc__ = 'Custom descriptor'
        self.assertEqual(self._get_summary_lines(X.attr), f"""\
<{__name__}.TestDescriptions.test_custom_non_data_descriptor.<locals>.Descr object>
    Custom descriptor
""")

        X.attr.__name__ = 'foo'
        self.assertEqual(self._get_summary_lines(X.attr), """\
foo(...)
    Custom descriptor
""")

    @requires_docstrings
    def test_custom_data_descriptor(self):
        klasse Descr:
            def __get__(self, obj, cls):
                wenn obj ist Nichts:
                    gib self
                gib 42
            def __set__(self, obj, cls):
                1/0
        klasse X:
            attr = Descr()

        self.assertEqual(self._get_summary_lines(X.attr), "")

        X.attr.__doc__ = 'Custom descriptor'
        self.assertEqual(self._get_summary_lines(X.attr), """\
    Custom descriptor
""")

        X.attr.__name__ = 'foo'
        self.assertEqual(self._get_summary_lines(X.attr), """\
foo
    Custom descriptor
""")

    def test_async_annotation(self):
        async def coro_function(ign) -> int:
            gib 1

        text = pydoc.plain(pydoc.plaintext.document(coro_function))
        self.assertIn('async coro_function', text)

        html = pydoc.HTMLDoc().document(coro_function)
        self.assertIn(
            'async <a name="-coro_function"><strong>coro_function',
            html)

    def test_async_generator_annotation(self):
        async def an_async_generator():
            liefere 1

        text = pydoc.plain(pydoc.plaintext.document(an_async_generator))
        self.assertIn('async an_async_generator', text)

        html = pydoc.HTMLDoc().document(an_async_generator)
        self.assertIn(
            'async <a name="-an_async_generator"><strong>an_async_generator',
            html)

    @requires_docstrings
    def test_html_for_https_links(self):
        def a_fn_with_https_link():
            """a link https://localhost/"""
            pass

        html = pydoc.HTMLDoc().document(a_fn_with_https_link)
        self.assertIn(
            '<a href="https://localhost/">https://localhost/</a>',
            html
        )

    def test_module_none(self):
        # Issue #128772
        von test.test_pydoc importiere module_none
        pydoc.render_doc(module_none)


klasse PydocFodderTest(unittest.TestCase):
    def tearDown(self):
        self.assertIs(sys.modules['pydoc'], pydoc)

    def getsection(self, text, beginline, endline):
        lines = text.splitlines()
        beginindex, endindex = 0, Nichts
        wenn beginline ist nicht Nichts:
            beginindex = lines.index(beginline)
        wenn endline ist nicht Nichts:
            endindex = lines.index(endline, beginindex)
        gib lines[beginindex:endindex]

    def test_text_doc_routines_in_class(self, cls=pydocfodder.B):
        doc = pydoc.TextDoc()
        result = doc.docclass(cls)
        result = clean_text(result)
        where = 'defined here' wenn cls ist pydocfodder.B sonst 'inherited von B'
        lines = self.getsection(result, f' |  Methods {where}:', ' |  ' + '-'*70)
        self.assertIn(' |  A_method_alias = A_method(self)', lines)
        self.assertIn(' |  B_method_alias = B_method(self)', lines)
        self.assertIn(' |  A_staticmethod(x, y) von test.test_pydoc.pydocfodder.A', lines)
        self.assertIn(' |  A_staticmethod_alias = A_staticmethod(x, y)', lines)
        self.assertIn(' |  global_func(x, y) von test.test_pydoc.pydocfodder', lines)
        self.assertIn(' |  global_func_alias = global_func(x, y)', lines)
        self.assertIn(' |  global_func2_alias = global_func2(x, y) von test.test_pydoc.pydocfodder', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn(' |  count(self, value, /) von builtins.list', lines)
            self.assertIn(' |  list_count = count(self, value, /)', lines)
            self.assertIn(' |  __repr__(self, /) von builtins.object', lines)
            self.assertIn(' |  object_repr = __repr__(self, /)', lines)
        sonst:
            self.assertIn(' |  count(self, object, /) von builtins.list', lines)
            self.assertIn(' |  list_count = count(self, object, /)', lines)
            self.assertIn(' |  __repr__(...) von builtins.object', lines)
            self.assertIn(' |  object_repr = __repr__(...)', lines)

        lines = self.getsection(result, f' |  Static methods {where}:', ' |  ' + '-'*70)
        self.assertIn(' |  A_classmethod_ref = A_classmethod(x) klasse method of test.test_pydoc.pydocfodder.A', lines)
        note = '' wenn cls ist pydocfodder.B sonst ' klasse method of test.test_pydoc.pydocfodder.B'
        self.assertIn(' |  B_classmethod_ref = B_classmethod(x)' + note, lines)
        self.assertIn(' |  A_method_ref = A_method() method of test.test_pydoc.pydocfodder.A instance', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn(' |  get(key, default=Nichts, /) method of builtins.dict instance', lines)
            self.assertIn(' |  dict_get = get(key, default=Nichts, /) method of builtins.dict instance', lines)
        sonst:
            self.assertIn(' |  get(...) method of builtins.dict instance', lines)
            self.assertIn(' |  dict_get = get(...) method of builtins.dict instance', lines)

        lines = self.getsection(result, f' |  Class methods {where}:', ' |  ' + '-'*70)
        self.assertIn(' |  B_classmethod(x)', lines)
        self.assertIn(' |  B_classmethod_alias = B_classmethod(x)', lines)

    def test_html_doc_routines_in_class(self, cls=pydocfodder.B):
        doc = pydoc.HTMLDoc()
        result = doc.docclass(cls)
        result = html2text(result)
        where = 'defined here' wenn cls ist pydocfodder.B sonst 'inherited von B'
        lines = self.getsection(result, f'Methods {where}:', '-'*70)
        self.assertIn('A_method_alias = A_method(self)', lines)
        self.assertIn('B_method_alias = B_method(self)', lines)
        self.assertIn('A_staticmethod(x, y) von test.test_pydoc.pydocfodder.A', lines)
        self.assertIn('A_staticmethod_alias = A_staticmethod(x, y)', lines)
        self.assertIn('global_func(x, y) von test.test_pydoc.pydocfodder', lines)
        self.assertIn('global_func_alias = global_func(x, y)', lines)
        self.assertIn('global_func2_alias = global_func2(x, y) von test.test_pydoc.pydocfodder', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn('count(self, value, /) von builtins.list', lines)
            self.assertIn('list_count = count(self, value, /)', lines)
            self.assertIn('__repr__(self, /) von builtins.object', lines)
            self.assertIn('object_repr = __repr__(self, /)', lines)
        sonst:
            self.assertIn('count(self, object, /) von builtins.list', lines)
            self.assertIn('list_count = count(self, object, /)', lines)
            self.assertIn('__repr__(...) von builtins.object', lines)
            self.assertIn('object_repr = __repr__(...)', lines)

        lines = self.getsection(result, f'Static methods {where}:', '-'*70)
        self.assertIn('A_classmethod_ref = A_classmethod(x) klasse method of test.test_pydoc.pydocfodder.A', lines)
        note = '' wenn cls ist pydocfodder.B sonst ' klasse method of test.test_pydoc.pydocfodder.B'
        self.assertIn('B_classmethod_ref = B_classmethod(x)' + note, lines)
        self.assertIn('A_method_ref = A_method() method of test.test_pydoc.pydocfodder.A instance', lines)

        lines = self.getsection(result, f'Class methods {where}:', '-'*70)
        self.assertIn('B_classmethod(x)', lines)
        self.assertIn('B_classmethod_alias = B_classmethod(x)', lines)

    def test_text_doc_inherited_routines_in_class(self):
        self.test_text_doc_routines_in_class(pydocfodder.D)

    def test_html_doc_inherited_routines_in_class(self):
        self.test_html_doc_routines_in_class(pydocfodder.D)

    def test_text_doc_routines_in_module(self):
        doc = pydoc.TextDoc()
        result = doc.docmodule(pydocfodder)
        result = clean_text(result)
        lines = self.getsection(result, 'FUNCTIONS', 'FILE')
        # function alias
        self.assertIn('    global_func_alias = global_func(x, y)', lines)
        self.assertIn('    A_staticmethod(x, y)', lines)
        self.assertIn('    A_staticmethod_alias = A_staticmethod(x, y)', lines)
        # bound klasse methods
        self.assertIn('    A_classmethod(x) klasse method of A', lines)
        self.assertIn('    A_classmethod2 = A_classmethod(x) klasse method of A', lines)
        self.assertIn('    A_classmethod3 = A_classmethod(x) klasse method of B', lines)
        # bound methods
        self.assertIn('    A_method() method of A instance', lines)
        self.assertIn('    A_method2 = A_method() method of A instance', lines)
        self.assertIn('    A_method3 = A_method() method of B instance', lines)
        self.assertIn('    A_staticmethod_ref = A_staticmethod(x, y)', lines)
        self.assertIn('    A_staticmethod_ref2 = A_staticmethod(y) method of B instance', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn('    get(key, default=Nichts, /) method of builtins.dict instance', lines)
            self.assertIn('    dict_get = get(key, default=Nichts, /) method of builtins.dict instance', lines)
        sonst:
            self.assertIn('    get(...) method of builtins.dict instance', lines)
            self.assertIn('    dict_get = get(...) method of builtins.dict instance', lines)

        # unbound methods
        self.assertIn('    B_method(self)', lines)
        self.assertIn('    B_method2 = B_method(self)', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn('    count(self, value, /) unbound builtins.list method', lines)
            self.assertIn('    list_count = count(self, value, /) unbound builtins.list method', lines)
            self.assertIn('    __repr__(self, /) unbound builtins.object method', lines)
            self.assertIn('    object_repr = __repr__(self, /) unbound builtins.object method', lines)
        sonst:
            self.assertIn('    count(self, object, /) unbound builtins.list method', lines)
            self.assertIn('    list_count = count(self, object, /) unbound builtins.list method', lines)
            self.assertIn('    __repr__(...) unbound builtins.object method', lines)
            self.assertIn('    object_repr = __repr__(...) unbound builtins.object method', lines)


    def test_html_doc_routines_in_module(self):
        doc = pydoc.HTMLDoc()
        result = doc.docmodule(pydocfodder)
        result = html2text(result)
        lines = self.getsection(result, ' Functions', Nichts)
        # function alias
        self.assertIn(' global_func_alias = global_func(x, y)', lines)
        self.assertIn(' A_staticmethod(x, y)', lines)
        self.assertIn(' A_staticmethod_alias = A_staticmethod(x, y)', lines)
        # bound klasse methods
        self.assertIn('A_classmethod(x) klasse method of A', lines)
        self.assertIn(' A_classmethod2 = A_classmethod(x) klasse method of A', lines)
        self.assertIn(' A_classmethod3 = A_classmethod(x) klasse method of B', lines)
        # bound methods
        self.assertIn(' A_method() method of A instance', lines)
        self.assertIn(' A_method2 = A_method() method of A instance', lines)
        self.assertIn(' A_method3 = A_method() method of B instance', lines)
        self.assertIn(' A_staticmethod_ref = A_staticmethod(x, y)', lines)
        self.assertIn(' A_staticmethod_ref2 = A_staticmethod(y) method of B instance', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn(' get(key, default=Nichts, /) method of builtins.dict instance', lines)
            self.assertIn(' dict_get = get(key, default=Nichts, /) method of builtins.dict instance', lines)
        sonst:
            self.assertIn(' get(...) method of builtins.dict instance', lines)
            self.assertIn(' dict_get = get(...) method of builtins.dict instance', lines)
        # unbound methods
        self.assertIn(' B_method(self)', lines)
        self.assertIn(' B_method2 = B_method(self)', lines)
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn(' count(self, value, /) unbound builtins.list method', lines)
            self.assertIn(' list_count = count(self, value, /) unbound builtins.list method', lines)
            self.assertIn(' __repr__(self, /) unbound builtins.object method', lines)
            self.assertIn(' object_repr = __repr__(self, /) unbound builtins.object method', lines)
        sonst:
            self.assertIn(' count(self, object, /) unbound builtins.list method', lines)
            self.assertIn(' list_count = count(self, object, /) unbound builtins.list method', lines)
            self.assertIn(' __repr__(...) unbound builtins.object method', lines)
            self.assertIn(' object_repr = __repr__(...) unbound builtins.object method', lines)


@unittest.skipIf(
    is_wasm32,
    "Socket server nicht available on Emscripten/WASI."
)
klasse PydocServerTest(unittest.TestCase):
    """Tests fuer pydoc._start_server"""
    def tearDown(self):
        self.assertIs(sys.modules['pydoc'], pydoc)

    def test_server(self):
        # Minimal test that starts the server, checks that it works, then stops
        # it und checks its cleanup.
        def my_url_handler(url, content_type):
            text = 'the URL sent was: (%s, %s)' % (url, content_type)
            gib text

        serverthread = pydoc._start_server(
            my_url_handler,
            hostname='localhost',
            port=0,
            )
        self.assertEqual(serverthread.error, Nichts)
        self.assertWahr(serverthread.serving)
        self.addCleanup(
            lambda: serverthread.stop() wenn serverthread.serving sonst Nichts
            )
        self.assertIn('localhost', serverthread.url)

        self.addCleanup(urlcleanup)
        self.assertEqual(
            b'the URL sent was: (/test, text/html)',
            urlopen(urllib.parse.urljoin(serverthread.url, '/test')).read(),
            )
        self.assertEqual(
            b'the URL sent was: (/test.css, text/css)',
            urlopen(urllib.parse.urljoin(serverthread.url, '/test.css')).read(),
            )

        serverthread.stop()
        self.assertFalsch(serverthread.serving)
        self.assertIsNichts(serverthread.docserver)
        self.assertIsNichts(serverthread.url)


klasse PydocUrlHandlerTest(PydocBaseTest):
    """Tests fuer pydoc._url_handler"""

    def test_content_type_err(self):
        f = pydoc._url_handler
        self.assertRaises(TypeError, f, 'A', '')
        self.assertRaises(TypeError, f, 'B', 'foobar')

    def test_url_requests(self):
        # Test fuer the correct title in the html pages returned.
        # This tests the different parts of the URL handler without
        # getting too picky about the exact html.
        requests = [
            ("", "Pydoc: Index of Modules"),
            ("get?key=", "Pydoc: Index of Modules"),
            ("index", "Pydoc: Index of Modules"),
            ("topics", "Pydoc: Topics"),
            ("keywords", "Pydoc: Keywords"),
            ("pydoc", "Pydoc: module pydoc"),
            ("get?key=pydoc", "Pydoc: module pydoc"),
            ("search?key=pydoc", "Pydoc: Search Results"),
            ("topic?key=def", "Pydoc: KEYWORD def"),
            ("topic?key=STRINGS", "Pydoc: TOPIC STRINGS"),
            ("foobar", "Pydoc: Error - foobar"),
            ]

        self.assertIs(sys.modules['pydoc'], pydoc)
        versuch:
            mit self.restrict_walk_packages():
                fuer url, title in requests:
                    self.call_url_handler(url, title)
        schliesslich:
            # Some requests reload the module und change sys.modules.
            sys.modules['pydoc'] = pydoc


klasse TestHelper(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual(sorted(pydoc.Helper.keywords),
                         sorted(keyword.kwlist))


klasse PydocWithMetaClasses(unittest.TestCase):
    def tearDown(self):
        self.assertIs(sys.modules['pydoc'], pydoc)

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_DynamicClassAttribute(self):
        klasse Meta(type):
            def __getattr__(self, name):
                wenn name == 'ham':
                    gib 'spam'
                gib super().__getattr__(name)
        klasse DA(metaclass=Meta):
            @types.DynamicClassAttribute
            def ham(self):
                gib 'eggs'
        expected_text_data_docstrings = tuple('\n |      ' + s wenn s sonst ''
                                      fuer s in expected_data_docstrings)
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(DA)
        expected_text = expected_dynamicattribute_pattern % (
                (__name__,) + expected_text_data_docstrings[:2])
        result = output.getvalue().strip()
        self.assertEqual(expected_text, result)

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_virtualClassAttributeWithOneMeta(self):
        klasse Meta(type):
            def __dir__(cls):
                gib ['__class__', '__module__', '__name__', 'LIFE']
            def __getattr__(self, name):
                wenn name =='LIFE':
                    gib 42
                gib super().__getattr(name)
        klasse Class(metaclass=Meta):
            pass
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(Class)
        expected_text = expected_virtualattribute_pattern1 % __name__
        result = output.getvalue().strip()
        self.assertEqual(expected_text, result)

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_virtualClassAttributeWithTwoMeta(self):
        klasse Meta1(type):
            def __dir__(cls):
                gib ['__class__', '__module__', '__name__', 'one']
            def __getattr__(self, name):
                wenn name =='one':
                    gib 1
                gib super().__getattr__(name)
        klasse Meta2(type):
            def __dir__(cls):
                gib ['__class__', '__module__', '__name__', 'two']
            def __getattr__(self, name):
                wenn name =='two':
                    gib 2
                gib super().__getattr__(name)
        klasse Meta3(Meta1, Meta2):
            def __dir__(cls):
                gib list(sorted(set(
                    ['__class__', '__module__', '__name__', 'three'] +
                    Meta1.__dir__(cls) + Meta2.__dir__(cls))))
            def __getattr__(self, name):
                wenn name =='three':
                    gib 3
                gib super().__getattr__(name)
        klasse Class1(metaclass=Meta1):
            pass
        klasse Class2(Class1, metaclass=Meta3):
            pass
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(Class1)
        expected_text1 = expected_virtualattribute_pattern2 % __name__
        result1 = output.getvalue().strip()
        self.assertEqual(expected_text1, result1)
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(Class2)
        expected_text2 = expected_virtualattribute_pattern3 % __name__
        result2 = output.getvalue().strip()
        self.assertEqual(expected_text2, result2)

    @unittest.skipIf(hasattr(sys, 'gettrace') und sys.gettrace(),
                     'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_buggy_dir(self):
        klasse M(type):
            def __dir__(cls):
                gib ['__class__', '__name__', 'missing', 'here']
        klasse C(metaclass=M):
            here = 'present!'
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(C)
        expected_text = expected_missingattribute_pattern % __name__
        result = output.getvalue().strip()
        self.assertEqual(expected_text, result)

    def test_resolve_false(self):
        # Issue #23008: pydoc enum.{,Int}Enum failed
        # because bool(enum.Enum) ist Falsch.
        mit captured_stdout() als help_io:
            pydoc.help('enum.Enum')
        helptext = help_io.getvalue()
        self.assertIn('class Enum', helptext)


klasse TestInternalUtilities(unittest.TestCase):

    def setUp(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.argv0dir = tmpdir.name
        self.argv0 = os.path.join(tmpdir.name, "nonexistent")
        self.addCleanup(tmpdir.cleanup)
        self.abs_curdir = abs_curdir = os.getcwd()
        self.curdir_spellings = ["", os.curdir, abs_curdir]

    def _get_revised_path(self, given_path, argv0=Nichts):
        # Checking that pydoc.cli() actually calls pydoc._get_revised_path()
        # ist handled via code review (at least fuer now).
        wenn argv0 ist Nichts:
            argv0 = self.argv0
        gib pydoc._get_revised_path(given_path, argv0)

    def _get_starting_path(self):
        # Get a copy of sys.path without the current directory.
        clean_path = sys.path.copy()
        fuer spelling in self.curdir_spellings:
            fuer __ in range(clean_path.count(spelling)):
                clean_path.remove(spelling)
        gib clean_path

    def test_sys_path_adjustment_adds_missing_curdir(self):
        clean_path = self._get_starting_path()
        expected_path = [self.abs_curdir] + clean_path
        self.assertEqual(self._get_revised_path(clean_path), expected_path)

    def test_sys_path_adjustment_removes_argv0_dir(self):
        clean_path = self._get_starting_path()
        expected_path = [self.abs_curdir] + clean_path
        leading_argv0dir = [self.argv0dir] + clean_path
        self.assertEqual(self._get_revised_path(leading_argv0dir), expected_path)
        trailing_argv0dir = clean_path + [self.argv0dir]
        self.assertEqual(self._get_revised_path(trailing_argv0dir), expected_path)

    def test_sys_path_adjustment_protects_pydoc_dir(self):
        def _get_revised_path(given_path):
            gib self._get_revised_path(given_path, argv0=pydoc.__file__)
        clean_path = self._get_starting_path()
        leading_argv0dir = [self.argv0dir] + clean_path
        expected_path = [self.abs_curdir] + leading_argv0dir
        self.assertEqual(_get_revised_path(leading_argv0dir), expected_path)
        trailing_argv0dir = clean_path + [self.argv0dir]
        expected_path = [self.abs_curdir] + trailing_argv0dir
        self.assertEqual(_get_revised_path(trailing_argv0dir), expected_path)

    def test_sys_path_adjustment_when_curdir_already_included(self):
        clean_path = self._get_starting_path()
        fuer spelling in self.curdir_spellings:
            mit self.subTest(curdir_spelling=spelling):
                # If curdir ist already present, no alterations are made at all
                leading_curdir = [spelling] + clean_path
                self.assertIsNichts(self._get_revised_path(leading_curdir))
                trailing_curdir = clean_path + [spelling]
                self.assertIsNichts(self._get_revised_path(trailing_curdir))
                leading_argv0dir = [self.argv0dir] + leading_curdir
                self.assertIsNichts(self._get_revised_path(leading_argv0dir))
                trailing_argv0dir = trailing_curdir + [self.argv0dir]
                self.assertIsNichts(self._get_revised_path(trailing_argv0dir))


def setUpModule():
    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)
    unittest.addModuleCleanup(reap_children)


wenn __name__ == "__main__":
    unittest.main()
