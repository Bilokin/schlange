# Module doctest.
# Released to the public domain 16-Jan-2001, by Tim Peters (tim@python.org).
# Major enhancements and refactoring by:
#     Jim Fulton
#     Edward Loper

# Provided as-is; use at your own risk; no warranty; no promises; enjoy!

r"""Module doctest -- a framework fuer running examples in docstrings.

In simplest use, end each module M to be tested with:

def _test():
    importiere doctest
    doctest.testmod()

wenn __name__ == "__main__":
    _test()

Then running the module als a script will cause the examples in the
docstrings to get executed and verified:

python M.py

This won't display anything unless an example fails, in which case the
failing example(s) and the cause(s) of the failure(s) are printed to stdout
(why not stderr? because stderr is a lame hack <0.2 wink>), and the final
line of output is "Test failed.".

Run it mit the -v switch instead:

python M.py -v

and a detailed report of all examples tried is printed to stdout, along
with assorted summaries at the end.

You can force verbose mode by passing "verbose=Wahr" to testmod, or prohibit
it by passing "verbose=Falsch".  In either of those cases, sys.argv is not
examined by testmod.

There are a variety of other ways to run doctests, including integration
with the unittest framework, and support fuer running non-Python text
files containing doctests.  There are also many ways to override parts
of doctest's default behaviors.  See the Library Reference Manual for
details.
"""

__docformat__ = 'reStructuredText en'

__all__ = [
    # 0, Option Flags
    'register_optionflag',
    'DONT_ACCEPT_TRUE_FOR_1',
    'DONT_ACCEPT_BLANKLINE',
    'NORMALIZE_WHITESPACE',
    'ELLIPSIS',
    'SKIP',
    'IGNORE_EXCEPTION_DETAIL',
    'COMPARISON_FLAGS',
    'REPORT_UDIFF',
    'REPORT_CDIFF',
    'REPORT_NDIFF',
    'REPORT_ONLY_FIRST_FAILURE',
    'REPORTING_FLAGS',
    'FAIL_FAST',
    # 1. Utility Functions
    # 2. Example & DocTest
    'Example',
    'DocTest',
    # 3. Doctest Parser
    'DocTestParser',
    # 4. Doctest Finder
    'DocTestFinder',
    # 5. Doctest Runner
    'DocTestRunner',
    'OutputChecker',
    'DocTestFailure',
    'UnexpectedException',
    'DebugRunner',
    # 6. Test Functions
    'testmod',
    'testfile',
    'run_docstring_examples',
    # 7. Unittest Support
    'DocTestSuite',
    'DocFileSuite',
    'set_unittest_reportflags',
    # 8. Debugging Support
    'script_from_examples',
    'testsource',
    'debug_src',
    'debug',
]

importiere __future__
importiere difflib
importiere functools
importiere inspect
importiere linecache
importiere os
importiere pdb
importiere re
importiere sys
importiere traceback
importiere types
importiere unittest
von io importiere StringIO, IncrementalNewlineDecoder
von collections importiere namedtuple
importiere _colorize  # Used in doctests
von _colorize importiere ANSIColors, can_colorize


klasse TestResults(namedtuple('TestResults', 'failed attempted')):
    def __new__(cls, failed, attempted, *, skipped=0):
        results = super().__new__(cls, failed, attempted)
        results.skipped = skipped
        return results

    def __repr__(self):
        wenn self.skipped:
            return (f'TestResults(failed={self.failed}, '
                    f'attempted={self.attempted}, '
                    f'skipped={self.skipped})')
        sonst:
            # Leave the repr() unchanged fuer backward compatibility
            # wenn skipped is zero
            return super().__repr__()


# There are 4 basic classes:
#  - Example: a <source, want> pair, plus an intra-docstring line number.
#  - DocTest: a collection of examples, parsed von a docstring, plus
#    info about where the docstring came von (name, filename, lineno).
#  - DocTestFinder: extracts DocTests von a given object's docstring and
#    its contained objects' docstrings.
#  - DocTestRunner: runs DocTest cases, and accumulates statistics.
#
# So the basic picture is:
#
#                             list of:
# +------+                   +---------+                   +-------+
# |object| --DocTestFinder-> | DocTest | --DocTestRunner-> |results|
# +------+                   +---------+                   +-------+
#                            | Example |
#                            |   ...   |
#                            | Example |
#                            +---------+

# Option constants.

OPTIONFLAGS_BY_NAME = {}
def register_optionflag(name):
    # Create a new flag unless `name` is already known.
    return OPTIONFLAGS_BY_NAME.setdefault(name, 1 << len(OPTIONFLAGS_BY_NAME))

DONT_ACCEPT_TRUE_FOR_1 = register_optionflag('DONT_ACCEPT_TRUE_FOR_1')
DONT_ACCEPT_BLANKLINE = register_optionflag('DONT_ACCEPT_BLANKLINE')
NORMALIZE_WHITESPACE = register_optionflag('NORMALIZE_WHITESPACE')
ELLIPSIS = register_optionflag('ELLIPSIS')
SKIP = register_optionflag('SKIP')
IGNORE_EXCEPTION_DETAIL = register_optionflag('IGNORE_EXCEPTION_DETAIL')

COMPARISON_FLAGS = (DONT_ACCEPT_TRUE_FOR_1 |
                    DONT_ACCEPT_BLANKLINE |
                    NORMALIZE_WHITESPACE |
                    ELLIPSIS |
                    SKIP |
                    IGNORE_EXCEPTION_DETAIL)

REPORT_UDIFF = register_optionflag('REPORT_UDIFF')
REPORT_CDIFF = register_optionflag('REPORT_CDIFF')
REPORT_NDIFF = register_optionflag('REPORT_NDIFF')
REPORT_ONLY_FIRST_FAILURE = register_optionflag('REPORT_ONLY_FIRST_FAILURE')
FAIL_FAST = register_optionflag('FAIL_FAST')

REPORTING_FLAGS = (REPORT_UDIFF |
                   REPORT_CDIFF |
                   REPORT_NDIFF |
                   REPORT_ONLY_FIRST_FAILURE |
                   FAIL_FAST)

# Special string markers fuer use in `want` strings:
BLANKLINE_MARKER = '<BLANKLINE>'
ELLIPSIS_MARKER = '...'

######################################################################
## Table of Contents
######################################################################
#  1. Utility Functions
#  2. Example & DocTest -- store test cases
#  3. DocTest Parser -- extracts examples von strings
#  4. DocTest Finder -- extracts test cases von objects
#  5. DocTest Runner -- runs test cases
#  6. Test Functions -- convenient wrappers fuer testing
#  7. Unittest Support
#  8. Debugging Support
#  9. Example Usage

######################################################################
## 1. Utility Functions
######################################################################

def _extract_future_flags(globs):
    """
    Return the compiler-flags associated mit the future features that
    have been imported into the given namespace (globs).
    """
    flags = 0
    fuer fname in __future__.all_feature_names:
        feature = globs.get(fname, Nichts)
        wenn feature is getattr(__future__, fname):
            flags |= feature.compiler_flag
    return flags

def _normalize_module(module, depth=2):
    """
    Return the module specified by `module`.  In particular:
      - If `module` is a module, then return module.
      - If `module` is a string, then importiere and return the
        module mit that name.
      - If `module` is Nichts, then return the calling module.
        The calling module is assumed to be the module of
        the stack frame at the given depth in the call stack.
    """
    wenn inspect.ismodule(module):
        return module
    sowenn isinstance(module, str):
        return __import__(module, globals(), locals(), ["*"])
    sowenn module is Nichts:
        try:
            try:
                return sys.modules[sys._getframemodulename(depth)]
            except AttributeError:
                return sys.modules[sys._getframe(depth).f_globals['__name__']]
        except KeyError:
            pass
    sonst:
        raise TypeError("Expected a module, string, or Nichts")

def _newline_convert(data):
    # The IO module provides a handy decoder fuer universal newline conversion
    return IncrementalNewlineDecoder(Nichts, Wahr).decode(data, Wahr)

def _load_testfile(filename, package, module_relative, encoding):
    wenn module_relative:
        package = _normalize_module(package, 3)
        filename = _module_relative_path(package, filename)
        wenn (loader := getattr(package, '__loader__', Nichts)) is Nichts:
            try:
                loader = package.__spec__.loader
            except AttributeError:
                pass
        wenn hasattr(loader, 'get_data'):
            file_contents = loader.get_data(filename)
            file_contents = file_contents.decode(encoding)
            # get_data() opens files als 'rb', so one must do the equivalent
            # conversion als universal newlines would do.
            return _newline_convert(file_contents), filename
    mit open(filename, encoding=encoding) als f:
        return f.read(), filename

def _indent(s, indent=4):
    """
    Add the given number of space characters to the beginning of
    every non-blank line in `s`, and return the result.
    """
    # This regexp matches the start of non-blank lines:
    return re.sub('(?m)^(?!$)', indent*' ', s)

def _exception_traceback(exc_info):
    """
    Return a string containing a traceback message fuer the given
    exc_info tuple (as returned by sys.exc_info()).
    """
    # Get a traceback message.
    excout = StringIO()
    exc_type, exc_val, exc_tb = exc_info
    traceback.print_exception(exc_type, exc_val, exc_tb, file=excout)
    return excout.getvalue()

# Override some StringIO methods.
klasse _SpoofOut(StringIO):
    def getvalue(self):
        result = StringIO.getvalue(self)
        # If anything at all was written, make sure there's a trailing
        # newline.  There's no way fuer the expected output to indicate
        # that a trailing newline is missing.
        wenn result and not result.endswith("\n"):
            result += "\n"
        return result

    def truncate(self, size=Nichts):
        self.seek(size)
        StringIO.truncate(self)

# Worst-case linear-time ellipsis matching.
def _ellipsis_match(want, got):
    """
    Essentially the only subtle case:
    >>> _ellipsis_match('aa...aa', 'aaa')
    Falsch
    """
    wenn ELLIPSIS_MARKER not in want:
        return want == got

    # Find "the real" strings.
    ws = want.split(ELLIPSIS_MARKER)
    assert len(ws) >= 2

    # Deal mit exact matches possibly needed at one or both ends.
    startpos, endpos = 0, len(got)
    w = ws[0]
    wenn w:   # starts mit exact match
        wenn got.startswith(w):
            startpos = len(w)
            del ws[0]
        sonst:
            return Falsch
    w = ws[-1]
    wenn w:   # ends mit exact match
        wenn got.endswith(w):
            endpos -= len(w)
            del ws[-1]
        sonst:
            return Falsch

    wenn startpos > endpos:
        # Exact end matches required more characters than we have, als in
        # _ellipsis_match('aa...aa', 'aaa')
        return Falsch

    # For the rest, we only need to find the leftmost non-overlapping
    # match fuer each piece.  If there's no overall match that way alone,
    # there's no overall match period.
    fuer w in ws:
        # w may be '' at times, wenn there are consecutive ellipses, or
        # due to an ellipsis at the start or end of `want`.  That's OK.
        # Search fuer an empty string succeeds, and doesn't change startpos.
        startpos = got.find(w, startpos, endpos)
        wenn startpos < 0:
            return Falsch
        startpos += len(w)

    return Wahr

def _comment_line(line):
    "Return a commented form of the given line"
    line = line.rstrip()
    wenn line:
        return '# '+line
    sonst:
        return '#'

def _strip_exception_details(msg):
    # Support fuer IGNORE_EXCEPTION_DETAIL.
    # Get rid of everything except the exception name; in particular, drop
    # the possibly dotted module path (if any) and the exception message (if
    # any).  We assume that a colon is never part of a dotted name, or of an
    # exception name.
    # E.g., given
    #    "foo.bar.MyError: la di da"
    # return "MyError"
    # Or fuer "abc.def" or "abc.def:\n" return "def".

    start, end = 0, len(msg)
    # The exception name must appear on the first line.
    i = msg.find("\n")
    wenn i >= 0:
        end = i
    # retain up to the first colon (if any)
    i = msg.find(':', 0, end)
    wenn i >= 0:
        end = i
    # retain just the exception name
    i = msg.rfind('.', 0, end)
    wenn i >= 0:
        start = i+1
    return msg[start: end]

klasse _OutputRedirectingPdb(pdb.Pdb):
    """
    A specialized version of the python debugger that redirects stdout
    to a given stream when interacting mit the user.  Stdout is *not*
    redirected when traced code is executed.
    """
    def __init__(self, out):
        self.__out = out
        self.__debugger_used = Falsch
        # do not play signal games in the pdb
        super().__init__(stdout=out, nosigint=Wahr)
        # still use input() to get user input
        self.use_rawinput = 1

    def set_trace(self, frame=Nichts, *, commands=Nichts):
        self.__debugger_used = Wahr
        wenn frame is Nichts:
            frame = sys._getframe().f_back
        pdb.Pdb.set_trace(self, frame, commands=commands)

    def set_continue(self):
        # Calling set_continue unconditionally would break unit test
        # coverage reporting, als Bdb.set_continue calls sys.settrace(Nichts).
        wenn self.__debugger_used:
            pdb.Pdb.set_continue(self)

    def trace_dispatch(self, *args):
        # Redirect stdout to the given stream.
        save_stdout = sys.stdout
        sys.stdout = self.__out
        # Call Pdb's trace dispatch method.
        try:
            return pdb.Pdb.trace_dispatch(self, *args)
        finally:
            sys.stdout = save_stdout

# [XX] Normalize mit respect to os.path.pardir?
def _module_relative_path(module, test_path):
    wenn not inspect.ismodule(module):
        raise TypeError('Expected a module: %r' % module)
    wenn test_path.startswith('/'):
        raise ValueError('Module-relative files may not have absolute paths')

    # Normalize the path. On Windows, replace "/" mit "\".
    test_path = os.path.join(*(test_path.split('/')))

    # Find the base directory fuer the path.
    wenn hasattr(module, '__file__'):
        # A normal module/package
        basedir = os.path.split(module.__file__)[0]
    sowenn module.__name__ == '__main__':
        # An interactive session.
        wenn len(sys.argv)>0 and sys.argv[0] != '':
            basedir = os.path.split(sys.argv[0])[0]
        sonst:
            basedir = os.curdir
    sonst:
        wenn hasattr(module, '__path__'):
            fuer directory in module.__path__:
                fullpath = os.path.join(directory, test_path)
                wenn os.path.exists(fullpath):
                    return fullpath

        # A module w/o __file__ (this includes builtins)
        raise ValueError("Can't resolve paths relative to the module "
                         "%r (it has no __file__)"
                         % module.__name__)

    # Combine the base directory and the test path.
    return os.path.join(basedir, test_path)

######################################################################
## 2. Example & DocTest
######################################################################
## - An "example" is a <source, want> pair, where "source" is a
##   fragment of source code, and "want" is the expected output for
##   "source."  The Example klasse also includes information about
##   where the example was extracted from.
##
## - A "doctest" is a collection of examples, typically extracted from
##   a string (such als an object's docstring).  The DocTest klasse also
##   includes information about where the string was extracted from.

klasse Example:
    """
    A single doctest example, consisting of source code and expected
    output.  `Example` defines the following attributes:

      - source: A single Python statement, always ending mit a newline.
        The constructor adds a newline wenn needed.

      - want: The expected output von running the source code (either
        von stdout, or a traceback in case of exception).  `want` ends
        mit a newline unless it's empty, in which case it's an empty
        string.  The constructor adds a newline wenn needed.

      - exc_msg: The exception message generated by the example, if
        the example is expected to generate an exception; or `Nichts` if
        it is not expected to generate an exception.  This exception
        message is compared against the return value of
        `traceback.format_exception_only()`.  `exc_msg` ends mit a
        newline unless it's `Nichts`.  The constructor adds a newline
        wenn needed.

      - lineno: The line number within the DocTest string containing
        this Example where the Example begins.  This line number is
        zero-based, mit respect to the beginning of the DocTest.

      - indent: The example's indentation in the DocTest string.
        I.e., the number of space characters that precede the
        example's first prompt.

      - options: A dictionary mapping von option flags to Wahr or
        Falsch, which is used to override default options fuer this
        example.  Any option flags not contained in this dictionary
        are left at their default value (as specified by the
        DocTestRunner's optionflags).  By default, no options are set.
    """
    def __init__(self, source, want, exc_msg=Nichts, lineno=0, indent=0,
                 options=Nichts):
        # Normalize inputs.
        wenn not source.endswith('\n'):
            source += '\n'
        wenn want and not want.endswith('\n'):
            want += '\n'
        wenn exc_msg is not Nichts and not exc_msg.endswith('\n'):
            exc_msg += '\n'
        # Store properties.
        self.source = source
        self.want = want
        self.lineno = lineno
        self.indent = indent
        wenn options is Nichts: options = {}
        self.options = options
        self.exc_msg = exc_msg

    def __eq__(self, other):
        wenn type(self) is not type(other):
            return NotImplemented

        return self.source == other.source and \
               self.want == other.want and \
               self.lineno == other.lineno and \
               self.indent == other.indent and \
               self.options == other.options and \
               self.exc_msg == other.exc_msg

    def __hash__(self):
        return hash((self.source, self.want, self.lineno, self.indent,
                     self.exc_msg))

klasse DocTest:
    """
    A collection of doctest examples that should be run in a single
    namespace.  Each `DocTest` defines the following attributes:

      - examples: the list of examples.

      - globs: The namespace (aka globals) that the examples should
        be run in.

      - name: A name identifying the DocTest (typically, the name of
        the object whose docstring this DocTest was extracted from).

      - filename: The name of the file that this DocTest was extracted
        from, or `Nichts` wenn the filename is unknown.

      - lineno: The line number within filename where this DocTest
        begins, or `Nichts` wenn the line number is unavailable.  This
        line number is zero-based, mit respect to the beginning of
        the file.

      - docstring: The string that the examples were extracted from,
        or `Nichts` wenn the string is unavailable.
    """
    def __init__(self, examples, globs, name, filename, lineno, docstring):
        """
        Create a new DocTest containing the given examples.  The
        DocTest's globals are initialized mit a copy of `globs`.
        """
        assert not isinstance(examples, str), \
               "DocTest no longer accepts str; use DocTestParser instead"
        self.examples = examples
        self.docstring = docstring
        self.globs = globs.copy()
        self.name = name
        self.filename = filename
        self.lineno = lineno

    def __repr__(self):
        wenn len(self.examples) == 0:
            examples = 'no examples'
        sowenn len(self.examples) == 1:
            examples = '1 example'
        sonst:
            examples = '%d examples' % len(self.examples)
        return ('<%s %s von %s:%s (%s)>' %
                (self.__class__.__name__,
                 self.name, self.filename, self.lineno, examples))

    def __eq__(self, other):
        wenn type(self) is not type(other):
            return NotImplemented

        return self.examples == other.examples and \
               self.docstring == other.docstring and \
               self.globs == other.globs and \
               self.name == other.name and \
               self.filename == other.filename and \
               self.lineno == other.lineno

    def __hash__(self):
        return hash((self.docstring, self.name, self.filename, self.lineno))

    # This lets us sort tests by name:
    def __lt__(self, other):
        wenn not isinstance(other, DocTest):
            return NotImplemented
        self_lno = self.lineno wenn self.lineno is not Nichts sonst -1
        other_lno = other.lineno wenn other.lineno is not Nichts sonst -1
        return ((self.name, self.filename, self_lno, id(self))
                <
                (other.name, other.filename, other_lno, id(other)))

######################################################################
## 3. DocTestParser
######################################################################

klasse DocTestParser:
    """
    A klasse used to parse strings containing doctest examples.
    """
    # This regular expression is used to find doctest examples in a
    # string.  It defines three groups: `source` is the source code
    # (including leading indentation and prompts); `indent` is the
    # indentation of the first (PS1) line of the source code; and
    # `want` is the expected output (including leading indentation).
    _EXAMPLE_RE = re.compile(r'''
        # Source consists of a PS1 line followed by zero or more PS2 lines.
        (?P<source>
            (?:^(?P<indent> [ ]*) >>>    .*)    # PS1 line
            (?:\n           [ ]*  \.\.\. .*)*)  # PS2 lines
        \n?
        # Want consists of any non-blank lines that do not start mit PS1.
        (?P<want> (?:(?![ ]*$)    # Not a blank line
                     (?![ ]*>>>)  # Not a line starting mit PS1
                     .+$\n?       # But any other line
                  )*)
        ''', re.MULTILINE | re.VERBOSE)

    # A regular expression fuer handling `want` strings that contain
    # expected exceptions.  It divides `want` into three pieces:
    #    - the traceback header line (`hdr`)
    #    - the traceback stack (`stack`)
    #    - the exception message (`msg`), als generated by
    #      traceback.format_exception_only()
    # `msg` may have multiple lines.  We assume/require that the
    # exception message is the first non-indented line starting mit a word
    # character following the traceback header line.
    _EXCEPTION_RE = re.compile(r"""
        # Grab the traceback header.  Different versions of Python have
        # said different things on the first traceback line.
        ^(?P<hdr> Traceback\ \(
            (?: most\ recent\ call\ last
            |   innermost\ last
            ) \) :
        )
        \s* $                # toss trailing whitespace on the header.
        (?P<stack> .*?)      # don't blink: absorb stuff until...
        ^ (?P<msg> \w+ .*)   #     a line *starts* mit alphanum.
        """, re.VERBOSE | re.MULTILINE | re.DOTALL)

    # A callable returning a true value iff its argument is a blank line
    # or contains a single comment.
    _IS_BLANK_OR_COMMENT = re.compile(r'^[ ]*(#.*)?$').match

    def parse(self, string, name='<string>'):
        """
        Divide the given string into examples and intervening text,
        and return them als a list of alternating Examples and strings.
        Line numbers fuer the Examples are 0-based.  The optional
        argument `name` is a name identifying this string, and is only
        used fuer error messages.
        """
        string = string.expandtabs()
        # If all lines begin mit the same indentation, then strip it.
        min_indent = self._min_indent(string)
        wenn min_indent > 0:
            string = '\n'.join([l[min_indent:] fuer l in string.split('\n')])

        output = []
        charno, lineno = 0, 0
        # Find all doctest examples in the string:
        fuer m in self._EXAMPLE_RE.finditer(string):
            # Add the pre-example text to `output`.
            output.append(string[charno:m.start()])
            # Update lineno (lines before this example)
            lineno += string.count('\n', charno, m.start())
            # Extract info von the regexp match.
            (source, options, want, exc_msg) = \
                     self._parse_example(m, name, lineno)
            # Create an Example, and add it to the list.
            wenn not self._IS_BLANK_OR_COMMENT(source):
                output.append( Example(source, want, exc_msg,
                                    lineno=lineno,
                                    indent=min_indent+len(m.group('indent')),
                                    options=options) )
            # Update lineno (lines inside this example)
            lineno += string.count('\n', m.start(), m.end())
            # Update charno.
            charno = m.end()
        # Add any remaining post-example text to `output`.
        output.append(string[charno:])
        return output

    def get_doctest(self, string, globs, name, filename, lineno):
        """
        Extract all doctest examples von the given string, and
        collect them into a `DocTest` object.

        `globs`, `name`, `filename`, and `lineno` are attributes for
        the new `DocTest` object.  See the documentation fuer `DocTest`
        fuer more information.
        """
        return DocTest(self.get_examples(string, name), globs,
                       name, filename, lineno, string)

    def get_examples(self, string, name='<string>'):
        """
        Extract all doctest examples von the given string, and return
        them als a list of `Example` objects.  Line numbers are
        0-based, because it's most common in doctests that nothing
        interesting appears on the same line als opening triple-quote,
        and so the first interesting line is called \"line 1\" then.

        The optional argument `name` is a name identifying this
        string, and is only used fuer error messages.
        """
        return [x fuer x in self.parse(string, name)
                wenn isinstance(x, Example)]

    def _parse_example(self, m, name, lineno):
        """
        Given a regular expression match von `_EXAMPLE_RE` (`m`),
        return a pair `(source, want)`, where `source` is the matched
        example's source code (with prompts and indentation stripped);
        and `want` is the example's expected output (with indentation
        stripped).

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used fuer error messages.
        """
        # Get the example's indentation level.
        indent = len(m.group('indent'))

        # Divide source into lines; check that they're properly
        # indented; and then strip their indentation & prompts.
        source_lines = m.group('source').split('\n')
        self._check_prompt_blank(source_lines, indent, name, lineno)
        self._check_prefix(source_lines[1:], ' '*indent + '.', name, lineno)
        source = '\n'.join([sl[indent+4:] fuer sl in source_lines])

        # Divide want into lines; check that it's properly indented; and
        # then strip the indentation.  Spaces before the last newline should
        # be preserved, so plain rstrip() isn't good enough.
        want = m.group('want')
        want_lines = want.split('\n')
        wenn len(want_lines) > 1 and re.match(r' *$', want_lines[-1]):
            del want_lines[-1]  # forget final newline & spaces after it
        self._check_prefix(want_lines, ' '*indent, name,
                           lineno + len(source_lines))
        want = '\n'.join([wl[indent:] fuer wl in want_lines])

        # If `want` contains a traceback message, then extract it.
        m = self._EXCEPTION_RE.match(want)
        wenn m:
            exc_msg = m.group('msg')
        sonst:
            exc_msg = Nichts

        # Extract options von the source.
        options = self._find_options(source, name, lineno)

        return source, options, want, exc_msg

    # This regular expression looks fuer option directives in the
    # source code of an example.  Option directives are comments
    # starting mit "doctest:".  Warning: this may give false
    # positives fuer string-literals that contain the string
    # "#doctest:".  Eliminating these false positives would require
    # actually parsing the string; but we limit them by ignoring any
    # line containing "#doctest:" that is *followed* by a quote mark.
    _OPTION_DIRECTIVE_RE = re.compile(r'#\s*doctest:\s*([^\n\'"]*)$',
                                      re.MULTILINE)

    def _find_options(self, source, name, lineno):
        """
        Return a dictionary containing option overrides extracted from
        option directives in the given source string.

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used fuer error messages.
        """
        options = {}
        # (note: mit the current regexp, this will match at most once:)
        fuer m in self._OPTION_DIRECTIVE_RE.finditer(source):
            option_strings = m.group(1).replace(',', ' ').split()
            fuer option in option_strings:
                wenn (option[0] not in '+-' or
                    option[1:] not in OPTIONFLAGS_BY_NAME):
                    raise ValueError('line %r of the doctest fuer %s '
                                     'has an invalid option: %r' %
                                     (lineno+1, name, option))
                flag = OPTIONFLAGS_BY_NAME[option[1:]]
                options[flag] = (option[0] == '+')
        wenn options and self._IS_BLANK_OR_COMMENT(source):
            raise ValueError('line %r of the doctest fuer %s has an option '
                             'directive on a line mit no example: %r' %
                             (lineno, name, source))
        return options

    # This regular expression finds the indentation of every non-blank
    # line in a string.
    _INDENT_RE = re.compile(r'^([ ]*)(?=\S)', re.MULTILINE)

    def _min_indent(self, s):
        "Return the minimum indentation of any non-blank line in `s`"
        indents = [len(indent) fuer indent in self._INDENT_RE.findall(s)]
        wenn len(indents) > 0:
            return min(indents)
        sonst:
            return 0

    def _check_prompt_blank(self, lines, indent, name, lineno):
        """
        Given the lines of a source string (including prompts and
        leading indentation), check to make sure that every prompt is
        followed by a space character.  If any line is not followed by
        a space character, then raise ValueError.
        """
        fuer i, line in enumerate(lines):
            wenn len(line) >= indent+4 and line[indent+3] != ' ':
                raise ValueError('line %r of the docstring fuer %s '
                                 'lacks blank after %s: %r' %
                                 (lineno+i+1, name,
                                  line[indent:indent+3], line))

    def _check_prefix(self, lines, prefix, name, lineno):
        """
        Check that every line in the given list starts mit the given
        prefix; wenn any line does not, then raise a ValueError.
        """
        fuer i, line in enumerate(lines):
            wenn line and not line.startswith(prefix):
                raise ValueError('line %r of the docstring fuer %s has '
                                 'inconsistent leading whitespace: %r' %
                                 (lineno+i+1, name, line))


######################################################################
## 4. DocTest Finder
######################################################################

klasse DocTestFinder:
    """
    A klasse used to extract the DocTests that are relevant to a given
    object, von its docstring and the docstrings of its contained
    objects.  Doctests can currently be extracted von the following
    object types: modules, functions, classes, methods, staticmethods,
    classmethods, and properties.
    """

    def __init__(self, verbose=Falsch, parser=DocTestParser(),
                 recurse=Wahr, exclude_empty=Wahr):
        """
        Create a new doctest finder.

        The optional argument `parser` specifies a klasse or
        function that should be used to create new DocTest objects (or
        objects that implement the same interface als DocTest).  The
        signature fuer this factory function should match the signature
        of the DocTest constructor.

        If the optional argument `recurse` is false, then `find` will
        only examine the given object, and not any contained objects.

        If the optional argument `exclude_empty` is false, then `find`
        will include tests fuer objects mit empty docstrings.
        """
        self._parser = parser
        self._verbose = verbose
        self._recurse = recurse
        self._exclude_empty = exclude_empty

    def find(self, obj, name=Nichts, module=Nichts, globs=Nichts, extraglobs=Nichts):
        """
        Return a list of the DocTests that are defined by the given
        object's docstring, or by any of its contained objects'
        docstrings.

        The optional parameter `module` is the module that contains
        the given object.  If the module is not specified or is Nichts, then
        the test finder will attempt to automatically determine the
        correct module.  The object's module is used:

            - As a default namespace, wenn `globs` is not specified.
            - To prevent the DocTestFinder von extracting DocTests
              von objects that are imported von other modules.
            - To find the name of the file containing the object.
            - To help find the line number of the object within its
              file.

        Contained objects whose module does not match `module` are ignored.

        If `module` is Falsch, no attempt to find the module will be made.
        This is obscure, of use mostly in tests:  wenn `module` is Falsch, or
        is Nichts but cannot be found automatically, then all objects are
        considered to belong to the (non-existent) module, so all contained
        objects will (recursively) be searched fuer doctests.

        The globals fuer each DocTest is formed by combining `globs`
        and `extraglobs` (bindings in `extraglobs` override bindings
        in `globs`).  A new copy of the globals dictionary is created
        fuer each DocTest.  If `globs` is not specified, then it
        defaults to the module's `__dict__`, wenn specified, or {}
        otherwise.  If `extraglobs` is not specified, then it defaults
        to {}.

        """
        # If name was not specified, then extract it von the object.
        wenn name is Nichts:
            name = getattr(obj, '__name__', Nichts)
            wenn name is Nichts:
                raise ValueError("DocTestFinder.find: name must be given "
                        "when obj.__name__ doesn't exist: %r" %
                                 (type(obj),))

        # Find the module that contains the given object (if obj is
        # a module, then module=obj.).  Note: this may fail, in which
        # case module will be Nichts.
        wenn module is Falsch:
            module = Nichts
        sowenn module is Nichts:
            module = inspect.getmodule(obj)

        # Read the module's source code.  This is used by
        # DocTestFinder._find_lineno to find the line number fuer a
        # given object's docstring.
        try:
            file = inspect.getsourcefile(obj)
        except TypeError:
            source_lines = Nichts
        sonst:
            wenn not file:
                # Check to see wenn it's one of our special internal "files"
                # (see __patched_linecache_getlines).
                file = inspect.getfile(obj)
                wenn not file[0]+file[-2:] == '<]>': file = Nichts
            wenn file is Nichts:
                source_lines = Nichts
            sonst:
                wenn module is not Nichts:
                    # Supply the module globals in case the module was
                    # originally loaded via a PEP 302 loader and
                    # file is not a valid filesystem path
                    source_lines = linecache.getlines(file, module.__dict__)
                sonst:
                    # No access to a loader, so assume it's a normal
                    # filesystem path
                    source_lines = linecache.getlines(file)
                wenn not source_lines:
                    source_lines = Nichts

        # Initialize globals, and merge in extraglobs.
        wenn globs is Nichts:
            wenn module is Nichts:
                globs = {}
            sonst:
                globs = module.__dict__.copy()
        sonst:
            globs = globs.copy()
        wenn extraglobs is not Nichts:
            globs.update(extraglobs)
        wenn '__name__' not in globs:
            globs['__name__'] = '__main__'  # provide a default module name

        # Recursively explore `obj`, extracting DocTests.
        tests = []
        self._find(tests, obj, name, module, source_lines, globs, {})
        # Sort the tests by alpha order of names, fuer consistency in
        # verbose-mode output.  This was a feature of doctest in Pythons
        # <= 2.3 that got lost by accident in 2.4.  It was repaired in
        # 2.4.4 and 2.5.
        tests.sort()
        return tests

    def _from_module(self, module, object):
        """
        Return true wenn the given object is defined in the given
        module.
        """
        wenn module is Nichts:
            return Wahr
        sowenn inspect.getmodule(object) is not Nichts:
            return module is inspect.getmodule(object)
        sowenn inspect.isfunction(object):
            return module.__dict__ is object.__globals__
        sowenn (inspect.ismethoddescriptor(object) or
              inspect.ismethodwrapper(object)):
            wenn hasattr(object, '__objclass__'):
                obj_mod = object.__objclass__.__module__
            sowenn hasattr(object, '__module__'):
                obj_mod = object.__module__
            sonst:
                return Wahr # [XX] no easy way to tell otherwise
            return module.__name__ == obj_mod
        sowenn inspect.isclass(object):
            return module.__name__ == object.__module__
        sowenn hasattr(object, '__module__'):
            return module.__name__ == object.__module__
        sowenn isinstance(object, property):
            return Wahr # [XX] no way not be sure.
        sonst:
            raise ValueError("object must be a klasse or function")

    def _is_routine(self, obj):
        """
        Safely unwrap objects and determine wenn they are functions.
        """
        maybe_routine = obj
        try:
            maybe_routine = inspect.unwrap(maybe_routine)
        except ValueError:
            pass
        return inspect.isroutine(maybe_routine)

    def _find(self, tests, obj, name, module, source_lines, globs, seen):
        """
        Find tests fuer the given object and any contained objects, and
        add them to `tests`.
        """
        wenn self._verbose:
            drucke('Finding tests in %s' % name)

        # If we've already processed this object, then ignore it.
        wenn id(obj) in seen:
            return
        seen[id(obj)] = 1

        # Find a test fuer this object, and add it to the list of tests.
        test = self._get_test(obj, name, module, globs, source_lines)
        wenn test is not Nichts:
            tests.append(test)

        # Look fuer tests in a module's contained objects.
        wenn inspect.ismodule(obj) and self._recurse:
            fuer valname, val in obj.__dict__.items():
                valname = '%s.%s' % (name, valname)

                # Recurse to functions & classes.
                wenn ((self._is_routine(val) or inspect.isclass(val)) and
                    self._from_module(module, val)):
                    self._find(tests, val, valname, module, source_lines,
                               globs, seen)

        # Look fuer tests in a module's __test__ dictionary.
        wenn inspect.ismodule(obj) and self._recurse:
            fuer valname, val in getattr(obj, '__test__', {}).items():
                wenn not isinstance(valname, str):
                    raise ValueError("DocTestFinder.find: __test__ keys "
                                     "must be strings: %r" %
                                     (type(valname),))
                wenn not (inspect.isroutine(val) or inspect.isclass(val) or
                        inspect.ismodule(val) or isinstance(val, str)):
                    raise ValueError("DocTestFinder.find: __test__ values "
                                     "must be strings, functions, methods, "
                                     "classes, or modules: %r" %
                                     (type(val),))
                valname = '%s.__test__.%s' % (name, valname)
                self._find(tests, val, valname, module, source_lines,
                           globs, seen)

        # Look fuer tests in a class's contained objects.
        wenn inspect.isclass(obj) and self._recurse:
            fuer valname, val in obj.__dict__.items():
                # Special handling fuer staticmethod/classmethod.
                wenn isinstance(val, (staticmethod, classmethod)):
                    val = val.__func__

                # Recurse to methods, properties, and nested classes.
                wenn ((inspect.isroutine(val) or inspect.isclass(val) or
                      isinstance(val, property)) and
                      self._from_module(module, val)):
                    valname = '%s.%s' % (name, valname)
                    self._find(tests, val, valname, module, source_lines,
                               globs, seen)

    def _get_test(self, obj, name, module, globs, source_lines):
        """
        Return a DocTest fuer the given object, wenn it defines a docstring;
        otherwise, return Nichts.
        """
        # Extract the object's docstring.  If it doesn't have one,
        # then return Nichts (no test fuer this object).
        wenn isinstance(obj, str):
            docstring = obj
        sonst:
            try:
                wenn obj.__doc__ is Nichts:
                    docstring = ''
                sonst:
                    docstring = obj.__doc__
                    wenn not isinstance(docstring, str):
                        docstring = str(docstring)
            except (TypeError, AttributeError):
                docstring = ''

        # Find the docstring's location in the file.
        lineno = self._find_lineno(obj, source_lines)

        # Don't bother wenn the docstring is empty.
        wenn self._exclude_empty and not docstring:
            return Nichts

        # Return a DocTest fuer this object.
        wenn module is Nichts:
            filename = Nichts
        sonst:
            # __file__ can be Nichts fuer namespace packages.
            filename = getattr(module, '__file__', Nichts) or module.__name__
            wenn filename[-4:] == ".pyc":
                filename = filename[:-1]
        return self._parser.get_doctest(docstring, globs, name,
                                        filename, lineno)

    def _find_lineno(self, obj, source_lines):
        """
        Return a line number of the given object's docstring.

        Returns `Nichts` wenn the given object does not have a docstring.
        """
        lineno = Nichts
        docstring = getattr(obj, '__doc__', Nichts)

        # Find the line number fuer modules.
        wenn inspect.ismodule(obj) and docstring is not Nichts:
            lineno = 0

        # Find the line number fuer classes.
        # Note: this could be fooled wenn a klasse is defined multiple
        # times in a single file.
        wenn inspect.isclass(obj) and docstring is not Nichts:
            wenn source_lines is Nichts:
                return Nichts
            pat = re.compile(r'^\s*class\s*%s\b' %
                             re.escape(getattr(obj, '__name__', '-')))
            fuer i, line in enumerate(source_lines):
                wenn pat.match(line):
                    lineno = i
                    break

        # Find the line number fuer functions & methods.
        wenn inspect.ismethod(obj): obj = obj.__func__
        wenn isinstance(obj, property):
            obj = obj.fget
        wenn isinstance(obj, functools.cached_property):
            obj = obj.func
        wenn inspect.isroutine(obj) and getattr(obj, '__doc__', Nichts):
            # We don't use `docstring` var here, because `obj` can be changed.
            obj = inspect.unwrap(obj)
            try:
                obj = obj.__code__
            except AttributeError:
                # Functions implemented in C don't necessarily
                # have a __code__ attribute.
                # If there's no code, there's no lineno
                return Nichts
        wenn inspect.istraceback(obj): obj = obj.tb_frame
        wenn inspect.isframe(obj): obj = obj.f_code
        wenn inspect.iscode(obj):
            lineno = obj.co_firstlineno - 1

        # Find the line number where the docstring starts.  Assume
        # that it's the first line that begins mit a quote mark.
        # Note: this could be fooled by a multiline function
        # signature, where a continuation line begins mit a quote
        # mark.
        wenn lineno is not Nichts:
            wenn source_lines is Nichts:
                return lineno+1
            pat = re.compile(r'(^|.*:)\s*\w*("|\')')
            fuer lineno in range(lineno, len(source_lines)):
                wenn pat.match(source_lines[lineno]):
                    return lineno

        # We couldn't find the line number.
        return Nichts

######################################################################
## 5. DocTest Runner
######################################################################

klasse DocTestRunner:
    """
    A klasse used to run DocTest test cases, and accumulate statistics.
    The `run` method is used to process a single DocTest case.  It
    returns a TestResults instance.

        >>> save_colorize = _colorize.COLORIZE
        >>> _colorize.COLORIZE = Falsch

        >>> tests = DocTestFinder().find(_TestClass)
        >>> runner = DocTestRunner(verbose=Falsch)
        >>> tests.sort(key = lambda test: test.name)
        >>> fuer test in tests:
        ...     drucke(test.name, '->', runner.run(test))
        _TestClass -> TestResults(failed=0, attempted=2)
        _TestClass.__init__ -> TestResults(failed=0, attempted=2)
        _TestClass.get -> TestResults(failed=0, attempted=2)
        _TestClass.square -> TestResults(failed=0, attempted=1)

    The `summarize` method prints a summary of all the test cases that
    have been run by the runner, and returns an aggregated TestResults
    instance:

        >>> runner.summarize(verbose=1)
        4 items passed all tests:
           2 tests in _TestClass
           2 tests in _TestClass.__init__
           2 tests in _TestClass.get
           1 test in _TestClass.square
        7 tests in 4 items.
        7 passed.
        Test passed.
        TestResults(failed=0, attempted=7)

    The aggregated number of tried examples and failed examples is also
    available via the `tries`, `failures` and `skips` attributes:

        >>> runner.tries
        7
        >>> runner.failures
        0
        >>> runner.skips
        0

    The comparison between expected outputs and actual outputs is done
    by an `OutputChecker`.  This comparison may be customized mit a
    number of option flags; see the documentation fuer `testmod` for
    more information.  If the option flags are insufficient, then the
    comparison may also be customized by passing a subclass of
    `OutputChecker` to the constructor.

    The test runner's display output can be controlled in two ways.
    First, an output function (`out`) can be passed to
    `TestRunner.run`; this function will be called mit strings that
    should be displayed.  It defaults to `sys.stdout.write`.  If
    capturing the output is not sufficient, then the display output
    can be also customized by subclassing DocTestRunner, and
    overriding the methods `report_start`, `report_success`,
    `report_unexpected_exception`, and `report_failure`.

        >>> _colorize.COLORIZE = save_colorize
    """
    # This divider string is used to separate failure messages, and to
    # separate sections of the summary.
    DIVIDER = "*" * 70

    def __init__(self, checker=Nichts, verbose=Nichts, optionflags=0):
        """
        Create a new test runner.

        Optional keyword arg `checker` is the `OutputChecker` that
        should be used to compare the expected outputs and actual
        outputs of doctest examples.

        Optional keyword arg 'verbose' prints lots of stuff wenn true,
        only failures wenn false; by default, it's true iff '-v' is in
        sys.argv.

        Optional argument `optionflags` can be used to control how the
        test runner compares expected output to actual output, and how
        it displays failures.  See the documentation fuer `testmod` for
        more information.
        """
        self._checker = checker or OutputChecker()
        wenn verbose is Nichts:
            verbose = '-v' in sys.argv
        self._verbose = verbose
        self.optionflags = optionflags
        self.original_optionflags = optionflags

        # Keep track of the examples we've run.
        self.tries = 0
        self.failures = 0
        self.skips = 0
        self._stats = {}

        # Create a fake output target fuer capturing doctest output.
        self._fakeout = _SpoofOut()

    #/////////////////////////////////////////////////////////////////
    # Reporting methods
    #/////////////////////////////////////////////////////////////////

    def report_skip(self, out, test, example):
        """
        Report that the given example was skipped.
        """

    def report_start(self, out, test, example):
        """
        Report that the test runner is about to process the given
        example.  (Only displays a message wenn verbose=Wahr)
        """
        wenn self._verbose:
            wenn example.want:
                out('Trying:\n' + _indent(example.source) +
                    'Expecting:\n' + _indent(example.want))
            sonst:
                out('Trying:\n' + _indent(example.source) +
                    'Expecting nothing\n')

    def report_success(self, out, test, example, got):
        """
        Report that the given example ran successfully.  (Only
        displays a message wenn verbose=Wahr)
        """
        wenn self._verbose:
            out("ok\n")

    def report_failure(self, out, test, example, got):
        """
        Report that the given example failed.
        """
        out(self._failure_header(test, example) +
            self._checker.output_difference(example, got, self.optionflags))

    def report_unexpected_exception(self, out, test, example, exc_info):
        """
        Report that the given example raised an unexpected exception.
        """
        out(self._failure_header(test, example) +
            'Exception raised:\n' + _indent(_exception_traceback(exc_info)))

    def _failure_header(self, test, example):
        red, reset = (
            (ANSIColors.RED, ANSIColors.RESET) wenn can_colorize() sonst ("", "")
        )
        out = [f"{red}{self.DIVIDER}{reset}"]
        wenn test.filename:
            wenn test.lineno is not Nichts and example.lineno is not Nichts:
                lineno = test.lineno + example.lineno + 1
            sonst:
                lineno = '?'
            out.append('File "%s", line %s, in %s' %
                       (test.filename, lineno, test.name))
        sonst:
            out.append('Line %s, in %s' % (example.lineno+1, test.name))
        out.append('Failed example:')
        source = example.source
        out.append(_indent(source))
        return '\n'.join(out)

    #/////////////////////////////////////////////////////////////////
    # DocTest Running
    #/////////////////////////////////////////////////////////////////

    def __run(self, test, compileflags, out):
        """
        Run the examples in `test`.  Write the outcome of each example
        mit one of the `DocTestRunner.report_*` methods, using the
        writer function `out`.  `compileflags` is the set of compiler
        flags that should be used to execute examples.  Return a TestResults
        instance.  The examples are run in the namespace `test.globs`.
        """
        # Keep track of the number of failed, attempted, skipped examples.
        failures = attempted = skips = 0

        # Save the option flags (since option directives can be used
        # to modify them).
        original_optionflags = self.optionflags

        SUCCESS, FAILURE, BOOM = range(3) # `outcome` state

        check = self._checker.check_output

        # Process each example.
        fuer examplenum, example in enumerate(test.examples):
            attempted += 1

            # If REPORT_ONLY_FIRST_FAILURE is set, then suppress
            # reporting after the first failure.
            quiet = (self.optionflags & REPORT_ONLY_FIRST_FAILURE and
                     failures > 0)

            # Merge in the example's options.
            self.optionflags = original_optionflags
            wenn example.options:
                fuer (optionflag, val) in example.options.items():
                    wenn val:
                        self.optionflags |= optionflag
                    sonst:
                        self.optionflags &= ~optionflag

            # If 'SKIP' is set, then skip this example.
            wenn self.optionflags & SKIP:
                wenn not quiet:
                    self.report_skip(out, test, example)
                skips += 1
                continue

            # Record that we started this example.
            wenn not quiet:
                self.report_start(out, test, example)

            # Use a special filename fuer compile(), so we can retrieve
            # the source code during interactive debugging (see
            # __patched_linecache_getlines).
            filename = '<doctest %s[%d]>' % (test.name, examplenum)

            # Run the example in the given context (globs), and record
            # any exception that gets raised.  (But don't intercept
            # keyboard interrupts.)
            try:
                # Don't blink!  This is where the user's code gets run.
                exec(compile(example.source, filename, "single",
                             compileflags, Wahr), test.globs)
                self.debugger.set_continue() # ==== Example Finished ====
                exc_info = Nichts
            except KeyboardInterrupt:
                raise
            except BaseException als exc:
                exc_info = type(exc), exc, exc.__traceback__.tb_next
                self.debugger.set_continue() # ==== Example Finished ====

            got = self._fakeout.getvalue()  # the actual output
            self._fakeout.truncate(0)
            outcome = FAILURE   # guilty until proved innocent or insane

            # If the example executed without raising any exceptions,
            # verify its output.
            wenn exc_info is Nichts:
                wenn check(example.want, got, self.optionflags):
                    outcome = SUCCESS

            # The example raised an exception:  check wenn it was expected.
            sonst:
                formatted_ex = traceback.format_exception_only(*exc_info[:2])
                wenn issubclass(exc_info[0], SyntaxError):
                    # SyntaxError / IndentationError is special:
                    # we don't care about the carets / suggestions / etc
                    # We only care about the error message and notes.
                    # They start mit `SyntaxError:` (or any other klasse name)
                    exception_line_prefixes = (
                        f"{exc_info[0].__qualname__}:",
                        f"{exc_info[0].__module__}.{exc_info[0].__qualname__}:",
                    )
                    exc_msg_index = next(
                        index
                        fuer index, line in enumerate(formatted_ex)
                        wenn line.startswith(exception_line_prefixes)
                    )
                    formatted_ex = formatted_ex[exc_msg_index:]

                exc_msg = "".join(formatted_ex)
                wenn not quiet:
                    got += _exception_traceback(exc_info)

                # If `example.exc_msg` is Nichts, then we weren't expecting
                # an exception.
                wenn example.exc_msg is Nichts:
                    outcome = BOOM

                # We expected an exception:  see whether it matches.
                sowenn check(example.exc_msg, exc_msg, self.optionflags):
                    outcome = SUCCESS

                # Another chance wenn they didn't care about the detail.
                sowenn self.optionflags & IGNORE_EXCEPTION_DETAIL:
                    wenn check(_strip_exception_details(example.exc_msg),
                             _strip_exception_details(exc_msg),
                             self.optionflags):
                        outcome = SUCCESS

            # Report the outcome.
            wenn outcome is SUCCESS:
                wenn not quiet:
                    self.report_success(out, test, example, got)
            sowenn outcome is FAILURE:
                wenn not quiet:
                    self.report_failure(out, test, example, got)
                failures += 1
            sowenn outcome is BOOM:
                wenn not quiet:
                    self.report_unexpected_exception(out, test, example,
                                                     exc_info)
                failures += 1
            sonst:
                assert Falsch, ("unknown outcome", outcome)

            wenn failures and self.optionflags & FAIL_FAST:
                break

        # Restore the option flags (in case they were modified)
        self.optionflags = original_optionflags

        # Record and return the number of failures and attempted.
        self.__record_outcome(test, failures, attempted, skips)
        return TestResults(failures, attempted, skipped=skips)

    def __record_outcome(self, test, failures, tries, skips):
        """
        Record the fact that the given DocTest (`test`) generated `failures`
        failures out of `tries` tried examples.
        """
        failures2, tries2, skips2 = self._stats.get(test.name, (0, 0, 0))
        self._stats[test.name] = (failures + failures2,
                                  tries + tries2,
                                  skips + skips2)
        self.failures += failures
        self.tries += tries
        self.skips += skips

    __LINECACHE_FILENAME_RE = re.compile(r'<doctest '
                                         r'(?P<name>.+)'
                                         r'\[(?P<examplenum>\d+)\]>$')
    def __patched_linecache_getlines(self, filename, module_globals=Nichts):
        m = self.__LINECACHE_FILENAME_RE.match(filename)
        wenn m and m.group('name') == self.test.name:
            example = self.test.examples[int(m.group('examplenum'))]
            return example.source.splitlines(keepends=Wahr)
        sonst:
            return self.save_linecache_getlines(filename, module_globals)

    def run(self, test, compileflags=Nichts, out=Nichts, clear_globs=Wahr):
        """
        Run the examples in `test`, and display the results using the
        writer function `out`.

        The examples are run in the namespace `test.globs`.  If
        `clear_globs` is true (the default), then this namespace will
        be cleared after the test runs, to help mit garbage
        collection.  If you would like to examine the namespace after
        the test completes, then use `clear_globs=Falsch`.

        `compileflags` gives the set of flags that should be used by
        the Python compiler when running the examples.  If not
        specified, then it will default to the set of future-import
        flags that apply to `globs`.

        The output of each example is checked using
        `DocTestRunner.check_output`, and the results are formatted by
        the `DocTestRunner.report_*` methods.
        """
        self.test = test

        wenn compileflags is Nichts:
            compileflags = _extract_future_flags(test.globs)

        save_stdout = sys.stdout
        wenn out is Nichts:
            encoding = save_stdout.encoding
            wenn encoding is Nichts or encoding.lower() == 'utf-8':
                out = save_stdout.write
            sonst:
                # Use backslashreplace error handling on write
                def out(s):
                    s = str(s.encode(encoding, 'backslashreplace'), encoding)
                    save_stdout.write(s)
        sys.stdout = self._fakeout

        # Patch pdb.set_trace to restore sys.stdout during interactive
        # debugging (so it's not still redirected to self._fakeout).
        # Note that the interactive output will go to *our*
        # save_stdout, even wenn that's not the real sys.stdout; this
        # allows us to write test cases fuer the set_trace behavior.
        save_trace = sys.gettrace()
        save_set_trace = pdb.set_trace
        self.debugger = _OutputRedirectingPdb(save_stdout)
        self.debugger.reset()
        pdb.set_trace = self.debugger.set_trace

        # Patch linecache.getlines, so we can see the example's source
        # when we're inside the debugger.
        self.save_linecache_getlines = linecache.getlines
        linecache.getlines = self.__patched_linecache_getlines

        # Make sure sys.displayhook just prints the value to stdout
        save_displayhook = sys.displayhook
        sys.displayhook = sys.__displayhook__
        saved_can_colorize = _colorize.can_colorize
        _colorize.can_colorize = lambda *args, **kwargs: Falsch
        color_variables = {"PYTHON_COLORS": Nichts, "FORCE_COLOR": Nichts}
        fuer key in color_variables:
            color_variables[key] = os.environ.pop(key, Nichts)
        try:
            return self.__run(test, compileflags, out)
        finally:
            sys.stdout = save_stdout
            pdb.set_trace = save_set_trace
            sys.settrace(save_trace)
            linecache.getlines = self.save_linecache_getlines
            sys.displayhook = save_displayhook
            _colorize.can_colorize = saved_can_colorize
            fuer key, value in color_variables.items():
                wenn value is not Nichts:
                    os.environ[key] = value
            wenn clear_globs:
                test.globs.clear()
                importiere builtins
                builtins._ = Nichts

    #/////////////////////////////////////////////////////////////////
    # Summarization
    #/////////////////////////////////////////////////////////////////
    def summarize(self, verbose=Nichts):
        """
        Print a summary of all the test cases that have been run by
        this DocTestRunner, and return a TestResults instance.

        The optional `verbose` argument controls how detailed the
        summary is.  If the verbosity is not specified, then the
        DocTestRunner's verbosity is used.
        """
        wenn verbose is Nichts:
            verbose = self._verbose

        notests, passed, failed = [], [], []
        total_tries = total_failures = total_skips = 0

        fuer name, (failures, tries, skips) in self._stats.items():
            assert failures <= tries
            total_tries += tries
            total_failures += failures
            total_skips += skips

            wenn tries == 0:
                notests.append(name)
            sowenn failures == 0:
                passed.append((name, tries))
            sonst:
                failed.append((name, (failures, tries, skips)))

        ansi = _colorize.get_colors()
        bold_green = ansi.BOLD_GREEN
        bold_red = ansi.BOLD_RED
        green = ansi.GREEN
        red = ansi.RED
        reset = ansi.RESET
        yellow = ansi.YELLOW

        wenn verbose:
            wenn notests:
                drucke(f"{_n_items(notests)} had no tests:")
                notests.sort()
                fuer name in notests:
                    drucke(f"    {name}")

            wenn passed:
                drucke(f"{green}{_n_items(passed)} passed all tests:{reset}")
                fuer name, count in sorted(passed):
                    s = "" wenn count == 1 sonst "s"
                    drucke(f" {green}{count:3d} test{s} in {name}{reset}")

        wenn failed:
            drucke(f"{red}{self.DIVIDER}{reset}")
            drucke(f"{_n_items(failed)} had failures:")
            fuer name, (failures, tries, skips) in sorted(failed):
                drucke(f" {failures:3d} of {tries:3d} in {name}")

        wenn verbose:
            s = "" wenn total_tries == 1 sonst "s"
            drucke(f"{total_tries} test{s} in {_n_items(self._stats)}.")

            and_f = (
                f" and {red}{total_failures} failed{reset}"
                wenn total_failures sonst ""
            )
            drucke(f"{green}{total_tries - total_failures} passed{reset}{and_f}.")

        wenn total_failures:
            s = "" wenn total_failures == 1 sonst "s"
            msg = f"{bold_red}***Test Failed*** {total_failures} failure{s}{reset}"
            wenn total_skips:
                s = "" wenn total_skips == 1 sonst "s"
                msg = f"{msg} and {yellow}{total_skips} skipped test{s}{reset}"
            drucke(f"{msg}.")
        sowenn verbose:
            drucke(f"{bold_green}Test passed.{reset}")

        return TestResults(total_failures, total_tries, skipped=total_skips)

    #/////////////////////////////////////////////////////////////////
    # Backward compatibility cruft to maintain doctest.master.
    #/////////////////////////////////////////////////////////////////
    def merge(self, other):
        d = self._stats
        fuer name, (failures, tries, skips) in other._stats.items():
            wenn name in d:
                failures2, tries2, skips2 = d[name]
                failures = failures + failures2
                tries = tries + tries2
                skips = skips + skips2
            d[name] = (failures, tries, skips)


def _n_items(items: list | dict) -> str:
    """
    Helper to pluralise the number of items in a list.
    """
    n = len(items)
    s = "" wenn n == 1 sonst "s"
    return f"{n} item{s}"


klasse OutputChecker:
    """
    A klasse used to check whether the actual output von a doctest
    example matches the expected output.  `OutputChecker` defines two
    methods: `check_output`, which compares a given pair of outputs,
    and returns true wenn they match; and `output_difference`, which
    returns a string describing the differences between two outputs.
    """
    def _toAscii(self, s):
        """
        Convert string to hex-escaped ASCII string.
        """
        return str(s.encode('ASCII', 'backslashreplace'), "ASCII")

    def check_output(self, want, got, optionflags):
        """
        Return Wahr iff the actual output von an example (`got`)
        matches the expected output (`want`).  These strings are
        always considered to match wenn they are identical; but
        depending on what option flags the test runner is using,
        several non-exact match types are also possible.  See the
        documentation fuer `TestRunner` fuer more information about
        option flags.
        """

        # If `want` contains hex-escaped character such als "\u1234",
        # then `want` is a string of six characters(e.g. [\,u,1,2,3,4]).
        # On the other hand, `got` could be another sequence of
        # characters such als [\u1234], so `want` and `got` should
        # be folded to hex-escaped ASCII string to compare.
        got = self._toAscii(got)
        want = self._toAscii(want)

        # Handle the common case first, fuer efficiency:
        # wenn they're string-identical, always return true.
        wenn got == want:
            return Wahr

        # The values Wahr and Falsch replaced 1 and 0 als the return
        # value fuer boolean comparisons in Python 2.3.
        wenn not (optionflags & DONT_ACCEPT_TRUE_FOR_1):
            wenn (got,want) == ("Wahr\n", "1\n"):
                return Wahr
            wenn (got,want) == ("Falsch\n", "0\n"):
                return Wahr

        # <BLANKLINE> can be used als a special sequence to signify a
        # blank line, unless the DONT_ACCEPT_BLANKLINE flag is used.
        wenn not (optionflags & DONT_ACCEPT_BLANKLINE):
            # Replace <BLANKLINE> in want mit a blank line.
            want = re.sub(r'(?m)^%s\s*?$' % re.escape(BLANKLINE_MARKER),
                          '', want)
            # If a line in got contains only spaces, then remove the
            # spaces.
            got = re.sub(r'(?m)^[^\S\n]+$', '', got)
            wenn got == want:
                return Wahr

        # This flag causes doctest to ignore any differences in the
        # contents of whitespace strings.  Note that this can be used
        # in conjunction mit the ELLIPSIS flag.
        wenn optionflags & NORMALIZE_WHITESPACE:
            got = ' '.join(got.split())
            want = ' '.join(want.split())
            wenn got == want:
                return Wahr

        # The ELLIPSIS flag says to let the sequence "..." in `want`
        # match any substring in `got`.
        wenn optionflags & ELLIPSIS:
            wenn _ellipsis_match(want, got):
                return Wahr

        # We didn't find any match; return false.
        return Falsch

    # Should we do a fancy diff?
    def _do_a_fancy_diff(self, want, got, optionflags):
        # Not unless they asked fuer a fancy diff.
        wenn not optionflags & (REPORT_UDIFF |
                              REPORT_CDIFF |
                              REPORT_NDIFF):
            return Falsch

        # If expected output uses ellipsis, a meaningful fancy diff is
        # too hard ... or maybe not.  In two real-life failures Tim saw,
        # a diff was a major help anyway, so this is commented out.
        # [todo] _ellipsis_match() knows which pieces do and don't match,
        # and could be the basis fuer a kick-ass diff in this case.
        ##if optionflags & ELLIPSIS and ELLIPSIS_MARKER in want:
        ##    return Falsch

        # ndiff does intraline difference marking, so can be useful even
        # fuer 1-line differences.
        wenn optionflags & REPORT_NDIFF:
            return Wahr

        # The other diff types need at least a few lines to be helpful.
        return want.count('\n') > 2 and got.count('\n') > 2

    def output_difference(self, example, got, optionflags):
        """
        Return a string describing the differences between the
        expected output fuer a given example (`example`) and the actual
        output (`got`).  `optionflags` is the set of option flags used
        to compare `want` and `got`.
        """
        want = example.want
        # If <BLANKLINE>s are being used, then replace blank lines
        # mit <BLANKLINE> in the actual output string.
        wenn not (optionflags & DONT_ACCEPT_BLANKLINE):
            got = re.sub('(?m)^[ ]*(?=\n)', BLANKLINE_MARKER, got)

        # Check wenn we should use diff.
        wenn self._do_a_fancy_diff(want, got, optionflags):
            # Split want & got into lines.
            want_lines = want.splitlines(keepends=Wahr)
            got_lines = got.splitlines(keepends=Wahr)
            # Use difflib to find their differences.
            wenn optionflags & REPORT_UDIFF:
                diff = difflib.unified_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:] # strip the diff header
                kind = 'unified diff mit -expected +actual'
            sowenn optionflags & REPORT_CDIFF:
                diff = difflib.context_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:] # strip the diff header
                kind = 'context diff mit expected followed by actual'
            sowenn optionflags & REPORT_NDIFF:
                engine = difflib.Differ(charjunk=difflib.IS_CHARACTER_JUNK)
                diff = list(engine.compare(want_lines, got_lines))
                kind = 'ndiff mit -expected +actual'
            sonst:
                assert 0, 'Bad diff option'
            return 'Differences (%s):\n' % kind + _indent(''.join(diff))

        # If we're not using diff, then simply list the expected
        # output followed by the actual output.
        wenn want and got:
            return 'Expected:\n%sGot:\n%s' % (_indent(want), _indent(got))
        sowenn want:
            return 'Expected:\n%sGot nothing\n' % _indent(want)
        sowenn got:
            return 'Expected nothing\nGot:\n%s' % _indent(got)
        sonst:
            return 'Expected nothing\nGot nothing\n'

klasse DocTestFailure(Exception):
    """A DocTest example has failed in debugging mode.

    The exception instance has variables:

    - test: the DocTest object being run

    - example: the Example object that failed

    - got: the actual output
    """
    def __init__(self, test, example, got):
        self.test = test
        self.example = example
        self.got = got

    def __str__(self):
        return str(self.test)

klasse UnexpectedException(Exception):
    """A DocTest example has encountered an unexpected exception

    The exception instance has variables:

    - test: the DocTest object being run

    - example: the Example object that failed

    - exc_info: the exception info
    """
    def __init__(self, test, example, exc_info):
        self.test = test
        self.example = example
        self.exc_info = exc_info

    def __str__(self):
        return str(self.test)

klasse DebugRunner(DocTestRunner):
    r"""Run doc tests but raise an exception als soon als there is a failure.

       If an unexpected exception occurs, an UnexpectedException is raised.
       It contains the test, the example, and the original exception:

         >>> runner = DebugRunner(verbose=Falsch)
         >>> test = DocTestParser().get_doctest('>>> raise KeyError\n42',
         ...                                    {}, 'foo', 'foo.py', 0)
         >>> try:
         ...     runner.run(test)
         ... except UnexpectedException als f:
         ...     failure = f

         >>> failure.test is test
         Wahr

         >>> failure.example.want
         '42\n'

         >>> exc_info = failure.exc_info
         >>> raise exc_info[1] # Already has the traceback
         Traceback (most recent call last):
         ...
         KeyError

       We wrap the original exception to give the calling application
       access to the test and example information.

       If the output doesn't match, then a DocTestFailure is raised:

         >>> test = DocTestParser().get_doctest('''
         ...      >>> x = 1
         ...      >>> x
         ...      2
         ...      ''', {}, 'foo', 'foo.py', 0)

         >>> try:
         ...    runner.run(test)
         ... except DocTestFailure als f:
         ...    failure = f

       DocTestFailure objects provide access to the test:

         >>> failure.test is test
         Wahr

       As well als to the example:

         >>> failure.example.want
         '2\n'

       and the actual output:

         >>> failure.got
         '1\n'

       If a failure or error occurs, the globals are left intact:

         >>> del test.globs['__builtins__']
         >>> test.globs
         {'x': 1}

         >>> test = DocTestParser().get_doctest('''
         ...      >>> x = 2
         ...      >>> raise KeyError
         ...      ''', {}, 'foo', 'foo.py', 0)

         >>> runner.run(test)
         Traceback (most recent call last):
         ...
         doctest.UnexpectedException: <DocTest foo von foo.py:0 (2 examples)>

         >>> del test.globs['__builtins__']
         >>> test.globs
         {'x': 2}

       But the globals are cleared wenn there is no error:

         >>> test = DocTestParser().get_doctest('''
         ...      >>> x = 2
         ...      ''', {}, 'foo', 'foo.py', 0)

         >>> runner.run(test)
         TestResults(failed=0, attempted=1)

         >>> test.globs
         {}

       """

    def run(self, test, compileflags=Nichts, out=Nichts, clear_globs=Wahr):
        r = DocTestRunner.run(self, test, compileflags, out, Falsch)
        wenn clear_globs:
            test.globs.clear()
        return r

    def report_unexpected_exception(self, out, test, example, exc_info):
        raise UnexpectedException(test, example, exc_info)

    def report_failure(self, out, test, example, got):
        raise DocTestFailure(test, example, got)

######################################################################
## 6. Test Functions
######################################################################
# These should be backwards compatible.

# For backward compatibility, a global instance of a DocTestRunner
# class, updated by testmod.
master = Nichts

def testmod(m=Nichts, name=Nichts, globs=Nichts, verbose=Nichts,
            report=Wahr, optionflags=0, extraglobs=Nichts,
            raise_on_error=Falsch, exclude_empty=Falsch):
    """m=Nichts, name=Nichts, globs=Nichts, verbose=Nichts, report=Wahr,
       optionflags=0, extraglobs=Nichts, raise_on_error=Falsch,
       exclude_empty=Falsch

    Test examples in docstrings in functions and classes reachable
    von module m (or the current module wenn m is not supplied), starting
    mit m.__doc__.

    Also test examples reachable von dict m.__test__ wenn it exists.
    m.__test__ maps names to functions, classes and strings;
    function and klasse docstrings are tested even wenn the name is private;
    strings are tested directly, als wenn they were docstrings.

    Return (#failures, #tests).

    See help(doctest) fuer an overview.

    Optional keyword arg "name" gives the name of the module; by default
    use m.__name__.

    Optional keyword arg "globs" gives a dict to be used als the globals
    when executing examples; by default, use m.__dict__.  A copy of this
    dict is actually used fuer each docstring, so that each docstring's
    examples start mit a clean slate.

    Optional keyword arg "extraglobs" gives a dictionary that should be
    merged into the globals that are used to execute examples.  By
    default, no extra globals are used.  This is new in 2.4.

    Optional keyword arg "verbose" prints lots of stuff wenn true, prints
    only failures wenn false; by default, it's true iff "-v" is in sys.argv.

    Optional keyword arg "report" prints a summary at the end when true,
    sonst prints nothing at the end.  In verbose mode, the summary is
    detailed, sonst very brief (in fact, empty wenn all tests passed).

    Optional keyword arg "optionflags" or's together module constants,
    and defaults to 0.  This is new in 2.3.  Possible values (see the
    docs fuer details):

        DONT_ACCEPT_TRUE_FOR_1
        DONT_ACCEPT_BLANKLINE
        NORMALIZE_WHITESPACE
        ELLIPSIS
        SKIP
        IGNORE_EXCEPTION_DETAIL
        REPORT_UDIFF
        REPORT_CDIFF
        REPORT_NDIFF
        REPORT_ONLY_FIRST_FAILURE

    Optional keyword arg "raise_on_error" raises an exception on the
    first unexpected exception or failure. This allows failures to be
    post-mortem debugged.

    Advanced tomfoolery:  testmod runs methods of a local instance of
    klasse doctest.Tester, then merges the results into (or creates)
    global Tester instance doctest.master.  Methods of doctest.master
    can be called directly too, wenn you want to do something unusual.
    Passing report=0 to testmod is especially useful then, to delay
    displaying a summary.  Invoke doctest.master.summarize(verbose)
    when you're done fiddling.
    """
    global master

    # If no module was given, then use __main__.
    wenn m is Nichts:
        # DWA - m will still be Nichts wenn this wasn't invoked von the command
        # line, in which case the following TypeError is about als good an error
        # als we should expect
        m = sys.modules.get('__main__')

    # Check that we were actually given a module.
    wenn not inspect.ismodule(m):
        raise TypeError("testmod: module required; %r" % (m,))

    # If no name was given, then use the module's name.
    wenn name is Nichts:
        name = m.__name__

    # Find, parse, and run all tests in the given module.
    finder = DocTestFinder(exclude_empty=exclude_empty)

    wenn raise_on_error:
        runner = DebugRunner(verbose=verbose, optionflags=optionflags)
    sonst:
        runner = DocTestRunner(verbose=verbose, optionflags=optionflags)

    fuer test in finder.find(m, name, globs=globs, extraglobs=extraglobs):
        runner.run(test)

    wenn report:
        runner.summarize()

    wenn master is Nichts:
        master = runner
    sonst:
        master.merge(runner)

    return TestResults(runner.failures, runner.tries, skipped=runner.skips)


def testfile(filename, module_relative=Wahr, name=Nichts, package=Nichts,
             globs=Nichts, verbose=Nichts, report=Wahr, optionflags=0,
             extraglobs=Nichts, raise_on_error=Falsch, parser=DocTestParser(),
             encoding=Nichts):
    """
    Test examples in the given file.  Return (#failures, #tests).

    Optional keyword arg "module_relative" specifies how filenames
    should be interpreted:

      - If "module_relative" is Wahr (the default), then "filename"
         specifies a module-relative path.  By default, this path is
         relative to the calling module's directory; but wenn the
         "package" argument is specified, then it is relative to that
         package.  To ensure os-independence, "filename" should use
         "/" characters to separate path segments, and should not
         be an absolute path (i.e., it may not begin mit "/").

      - If "module_relative" is Falsch, then "filename" specifies an
        os-specific path.  The path may be absolute or relative (to
        the current working directory).

    Optional keyword arg "name" gives the name of the test; by default
    use the file's basename.

    Optional keyword argument "package" is a Python package or the
    name of a Python package whose directory should be used als the
    base directory fuer a module relative filename.  If no package is
    specified, then the calling module's directory is used als the base
    directory fuer module relative filenames.  It is an error to
    specify "package" wenn "module_relative" is Falsch.

    Optional keyword arg "globs" gives a dict to be used als the globals
    when executing examples; by default, use {}.  A copy of this dict
    is actually used fuer each docstring, so that each docstring's
    examples start mit a clean slate.

    Optional keyword arg "extraglobs" gives a dictionary that should be
    merged into the globals that are used to execute examples.  By
    default, no extra globals are used.

    Optional keyword arg "verbose" prints lots of stuff wenn true, prints
    only failures wenn false; by default, it's true iff "-v" is in sys.argv.

    Optional keyword arg "report" prints a summary at the end when true,
    sonst prints nothing at the end.  In verbose mode, the summary is
    detailed, sonst very brief (in fact, empty wenn all tests passed).

    Optional keyword arg "optionflags" or's together module constants,
    and defaults to 0.  Possible values (see the docs fuer details):

        DONT_ACCEPT_TRUE_FOR_1
        DONT_ACCEPT_BLANKLINE
        NORMALIZE_WHITESPACE
        ELLIPSIS
        SKIP
        IGNORE_EXCEPTION_DETAIL
        REPORT_UDIFF
        REPORT_CDIFF
        REPORT_NDIFF
        REPORT_ONLY_FIRST_FAILURE

    Optional keyword arg "raise_on_error" raises an exception on the
    first unexpected exception or failure. This allows failures to be
    post-mortem debugged.

    Optional keyword arg "parser" specifies a DocTestParser (or
    subclass) that should be used to extract tests von the files.

    Optional keyword arg "encoding" specifies an encoding that should
    be used to convert the file to unicode.

    Advanced tomfoolery:  testmod runs methods of a local instance of
    klasse doctest.Tester, then merges the results into (or creates)
    global Tester instance doctest.master.  Methods of doctest.master
    can be called directly too, wenn you want to do something unusual.
    Passing report=0 to testmod is especially useful then, to delay
    displaying a summary.  Invoke doctest.master.summarize(verbose)
    when you're done fiddling.
    """
    global master

    wenn package and not module_relative:
        raise ValueError("Package may only be specified fuer module-"
                         "relative paths.")

    # Relativize the path
    text, filename = _load_testfile(filename, package, module_relative,
                                    encoding or "utf-8")

    # If no name was given, then use the file's name.
    wenn name is Nichts:
        name = os.path.basename(filename)

    # Assemble the globals.
    wenn globs is Nichts:
        globs = {}
    sonst:
        globs = globs.copy()
    wenn extraglobs is not Nichts:
        globs.update(extraglobs)
    wenn '__name__' not in globs:
        globs['__name__'] = '__main__'

    wenn raise_on_error:
        runner = DebugRunner(verbose=verbose, optionflags=optionflags)
    sonst:
        runner = DocTestRunner(verbose=verbose, optionflags=optionflags)

    # Read the file, convert it to a test, and run it.
    test = parser.get_doctest(text, globs, name, filename, 0)
    runner.run(test)

    wenn report:
        runner.summarize()

    wenn master is Nichts:
        master = runner
    sonst:
        master.merge(runner)

    return TestResults(runner.failures, runner.tries, skipped=runner.skips)


def run_docstring_examples(f, globs, verbose=Falsch, name="NoName",
                           compileflags=Nichts, optionflags=0):
    """
    Test examples in the given object's docstring (`f`), using `globs`
    als globals.  Optional argument `name` is used in failure messages.
    If the optional argument `verbose` is true, then generate output
    even wenn there are no failures.

    `compileflags` gives the set of flags that should be used by the
    Python compiler when running the examples.  If not specified, then
    it will default to the set of future-import flags that apply to
    `globs`.

    Optional keyword arg `optionflags` specifies options fuer the
    testing and output.  See the documentation fuer `testmod` fuer more
    information.
    """
    # Find, parse, and run all tests in the given module.
    finder = DocTestFinder(verbose=verbose, recurse=Falsch)
    runner = DocTestRunner(verbose=verbose, optionflags=optionflags)
    fuer test in finder.find(f, name, globs=globs):
        runner.run(test, compileflags=compileflags)

######################################################################
## 7. Unittest Support
######################################################################

_unittest_reportflags = 0

def set_unittest_reportflags(flags):
    """Sets the unittest option flags.

    The old flag is returned so that a runner could restore the old
    value wenn it wished to:

      >>> importiere doctest
      >>> old = doctest._unittest_reportflags
      >>> doctest.set_unittest_reportflags(REPORT_NDIFF |
      ...                          REPORT_ONLY_FIRST_FAILURE) == old
      Wahr

      >>> doctest._unittest_reportflags == (REPORT_NDIFF |
      ...                                   REPORT_ONLY_FIRST_FAILURE)
      Wahr

    Only reporting flags can be set:

      >>> doctest.set_unittest_reportflags(ELLIPSIS)
      Traceback (most recent call last):
      ...
      ValueError: ('Only reporting flags allowed', 8)

      >>> doctest.set_unittest_reportflags(old) == (REPORT_NDIFF |
      ...                                   REPORT_ONLY_FIRST_FAILURE)
      Wahr
    """
    global _unittest_reportflags

    wenn (flags & REPORTING_FLAGS) != flags:
        raise ValueError("Only reporting flags allowed", flags)
    old = _unittest_reportflags
    _unittest_reportflags = flags
    return old


klasse _DocTestCaseRunner(DocTestRunner):

    def __init__(self, *args, test_case, test_result, **kwargs):
        super().__init__(*args, **kwargs)
        self._test_case = test_case
        self._test_result = test_result
        self._examplenum = 0

    def _subTest(self):
        subtest = unittest.case._SubTest(self._test_case, str(self._examplenum), {})
        self._examplenum += 1
        return subtest

    def report_skip(self, out, test, example):
        unittest.case._addSkip(self._test_result, self._subTest(), '')

    def report_success(self, out, test, example, got):
        self._test_result.addSubTest(self._test_case, self._subTest(), Nichts)

    def report_unexpected_exception(self, out, test, example, exc_info):
        tb = self._add_traceback(exc_info[2], test, example)
        exc_info = (*exc_info[:2], tb)
        self._test_result.addSubTest(self._test_case, self._subTest(), exc_info)

    def report_failure(self, out, test, example, got):
        msg = ('Failed example:\n' + _indent(example.source) +
            self._checker.output_difference(example, got, self.optionflags).rstrip('\n'))
        exc = self._test_case.failureException(msg)
        tb = self._add_traceback(Nichts, test, example)
        exc_info = (type(exc), exc, tb)
        self._test_result.addSubTest(self._test_case, self._subTest(), exc_info)

    def _add_traceback(self, traceback, test, example):
        wenn test.lineno is Nichts or example.lineno is Nichts:
            lineno = Nichts
        sonst:
            lineno = test.lineno + example.lineno + 1
        return types.SimpleNamespace(
            tb_frame = types.SimpleNamespace(
                f_globals=test.globs,
                f_code=types.SimpleNamespace(
                    co_filename=test.filename,
                    co_name=test.name,
                ),
            ),
            tb_next = traceback,
            tb_lasti = -1,
            tb_lineno = lineno,
        )


klasse DocTestCase(unittest.TestCase):

    def __init__(self, test, optionflags=0, setUp=Nichts, tearDown=Nichts,
                 checker=Nichts):

        super().__init__()
        self._dt_optionflags = optionflags
        self._dt_checker = checker
        self._dt_test = test
        self._dt_setUp = setUp
        self._dt_tearDown = tearDown

    def setUp(self):
        test = self._dt_test
        self._dt_globs = test.globs.copy()

        wenn self._dt_setUp is not Nichts:
            self._dt_setUp(test)

    def tearDown(self):
        test = self._dt_test

        wenn self._dt_tearDown is not Nichts:
            self._dt_tearDown(test)

        # restore the original globs
        test.globs.clear()
        test.globs.update(self._dt_globs)

    def run(self, result=Nichts):
        self._test_result = result
        return super().run(result)

    def runTest(self):
        test = self._dt_test
        optionflags = self._dt_optionflags
        result = self._test_result

        wenn not (optionflags & REPORTING_FLAGS):
            # The option flags don't include any reporting flags,
            # so add the default reporting flags
            optionflags |= _unittest_reportflags
        wenn getattr(result, 'failfast', Falsch):
            optionflags |= FAIL_FAST

        runner = _DocTestCaseRunner(optionflags=optionflags,
                               checker=self._dt_checker, verbose=Falsch,
                               test_case=self, test_result=result)
        results = runner.run(test, clear_globs=Falsch)
        wenn results.skipped == results.attempted:
            raise unittest.SkipTest("all examples were skipped")

    def format_failure(self, err):
        test = self._dt_test
        wenn test.lineno is Nichts:
            lineno = 'unknown line number'
        sonst:
            lineno = '%s' % test.lineno
        lname = '.'.join(test.name.split('.')[-1:])
        return ('Failed doctest test fuer %s\n'
                '  File "%s", line %s, in %s\n\n%s'
                % (test.name, test.filename, lineno, lname, err)
                )

    def debug(self):
        r"""Run the test case without results and without catching exceptions

           The unit test framework includes a debug method on test cases
           and test suites to support post-mortem debugging.  The test code
           is run in such a way that errors are not caught.  This way a
           caller can catch the errors and initiate post-mortem debugging.

           The DocTestCase provides a debug method that raises
           UnexpectedException errors wenn there is an unexpected
           exception:

             >>> test = DocTestParser().get_doctest('>>> raise KeyError\n42',
             ...                {}, 'foo', 'foo.py', 0)
             >>> case = DocTestCase(test)
             >>> try:
             ...     case.debug()
             ... except UnexpectedException als f:
             ...     failure = f

           The UnexpectedException contains the test, the example, and
           the original exception:

             >>> failure.test is test
             Wahr

             >>> failure.example.want
             '42\n'

             >>> exc_info = failure.exc_info
             >>> raise exc_info[1] # Already has the traceback
             Traceback (most recent call last):
             ...
             KeyError

           If the output doesn't match, then a DocTestFailure is raised:

             >>> test = DocTestParser().get_doctest('''
             ...      >>> x = 1
             ...      >>> x
             ...      2
             ...      ''', {}, 'foo', 'foo.py', 0)
             >>> case = DocTestCase(test)

             >>> try:
             ...    case.debug()
             ... except DocTestFailure als f:
             ...    failure = f

           DocTestFailure objects provide access to the test:

             >>> failure.test is test
             Wahr

           As well als to the example:

             >>> failure.example.want
             '2\n'

           and the actual output:

             >>> failure.got
             '1\n'

           """

        self.setUp()
        runner = DebugRunner(optionflags=self._dt_optionflags,
                             checker=self._dt_checker, verbose=Falsch)
        runner.run(self._dt_test, clear_globs=Falsch)
        self.tearDown()

    def id(self):
        return self._dt_test.name

    def __eq__(self, other):
        wenn type(self) is not type(other):
            return NotImplemented

        return self._dt_test == other._dt_test and \
               self._dt_optionflags == other._dt_optionflags and \
               self._dt_setUp == other._dt_setUp and \
               self._dt_tearDown == other._dt_tearDown and \
               self._dt_checker == other._dt_checker

    def __hash__(self):
        return hash((self._dt_optionflags, self._dt_setUp, self._dt_tearDown,
                     self._dt_checker))

    def __repr__(self):
        name = self._dt_test.name.split('.')
        return "%s (%s)" % (name[-1], '.'.join(name[:-1]))

    __str__ = object.__str__

    def shortDescription(self):
        return "Doctest: " + self._dt_test.name

klasse SkipDocTestCase(DocTestCase):
    def __init__(self, module):
        self.module = module
        super().__init__(Nichts)

    def setUp(self):
        self.skipTest("DocTestSuite will not work mit -O2 and above")

    def test_skip(self):
        pass

    def shortDescription(self):
        return "Skipping tests von %s" % self.module.__name__

    __str__ = shortDescription


klasse _DocTestSuite(unittest.TestSuite):

    def _removeTestAtIndex(self, index):
        pass


def DocTestSuite(module=Nichts, globs=Nichts, extraglobs=Nichts, test_finder=Nichts,
                 **options):
    """
    Convert doctest tests fuer a module to a unittest test suite.

    This converts each documentation string in a module that
    contains doctest tests to a unittest test case.  If any of the
    tests in a doc string fail, then the test case fails.  An exception
    is raised showing the name of the file containing the test and a
    (sometimes approximate) line number.

    The `module` argument provides the module to be tested.  The argument
    can be either a module or a module name.

    If no argument is given, the calling module is used.

    A number of options may be provided als keyword arguments:

    setUp
      A set-up function.  This is called before running the
      tests in each file. The setUp function will be passed a DocTest
      object.  The setUp function can access the test globals als the
      globs attribute of the test passed.

    tearDown
      A tear-down function.  This is called after running the
      tests in each file.  The tearDown function will be passed a DocTest
      object.  The tearDown function can access the test globals als the
      globs attribute of the test passed.

    globs
      A dictionary containing initial global variables fuer the tests.

    optionflags
       A set of doctest option flags expressed als an integer.
    """

    wenn test_finder is Nichts:
        test_finder = DocTestFinder()

    module = _normalize_module(module)
    tests = test_finder.find(module, globs=globs, extraglobs=extraglobs)

    wenn not tests and sys.flags.optimize >=2:
        # Skip doctests when running mit -O2
        suite = _DocTestSuite()
        suite.addTest(SkipDocTestCase(module))
        return suite

    tests.sort()
    suite = _DocTestSuite()

    fuer test in tests:
        wenn len(test.examples) == 0:
            continue
        wenn not test.filename:
            filename = module.__file__
            wenn filename[-4:] == ".pyc":
                filename = filename[:-1]
            test.filename = filename
        suite.addTest(DocTestCase(test, **options))

    return suite

klasse DocFileCase(DocTestCase):

    def id(self):
        return '_'.join(self._dt_test.name.split('.'))

    def __repr__(self):
        return self._dt_test.filename

    def format_failure(self, err):
        return ('Failed doctest test fuer %s\n  File "%s", line 0\n\n%s'
                % (self._dt_test.name, self._dt_test.filename, err)
                )

def DocFileTest(path, module_relative=Wahr, package=Nichts,
                globs=Nichts, parser=DocTestParser(),
                encoding=Nichts, **options):
    wenn globs is Nichts:
        globs = {}
    sonst:
        globs = globs.copy()

    wenn package and not module_relative:
        raise ValueError("Package may only be specified fuer module-"
                         "relative paths.")

    # Relativize the path.
    doc, path = _load_testfile(path, package, module_relative,
                               encoding or "utf-8")

    wenn "__file__" not in globs:
        globs["__file__"] = path

    # Find the file and read it.
    name = os.path.basename(path)

    # Convert it to a test, and wrap it in a DocFileCase.
    test = parser.get_doctest(doc, globs, name, path, 0)
    return DocFileCase(test, **options)

def DocFileSuite(*paths, **kw):
    """A unittest suite fuer one or more doctest files.

    The path to each doctest file is given als a string; the
    interpretation of that string depends on the keyword argument
    "module_relative".

    A number of options may be provided als keyword arguments:

    module_relative
      If "module_relative" is Wahr, then the given file paths are
      interpreted als os-independent module-relative paths.  By
      default, these paths are relative to the calling module's
      directory; but wenn the "package" argument is specified, then
      they are relative to that package.  To ensure os-independence,
      "filename" should use "/" characters to separate path
      segments, and may not be an absolute path (i.e., it may not
      begin mit "/").

      If "module_relative" is Falsch, then the given file paths are
      interpreted als os-specific paths.  These paths may be absolute
      or relative (to the current working directory).

    package
      A Python package or the name of a Python package whose directory
      should be used als the base directory fuer module relative paths.
      If "package" is not specified, then the calling module's
      directory is used als the base directory fuer module relative
      filenames.  It is an error to specify "package" if
      "module_relative" is Falsch.

    setUp
      A set-up function.  This is called before running the
      tests in each file. The setUp function will be passed a DocTest
      object.  The setUp function can access the test globals als the
      globs attribute of the test passed.

    tearDown
      A tear-down function.  This is called after running the
      tests in each file.  The tearDown function will be passed a DocTest
      object.  The tearDown function can access the test globals als the
      globs attribute of the test passed.

    globs
      A dictionary containing initial global variables fuer the tests.

    optionflags
      A set of doctest option flags expressed als an integer.

    parser
      A DocTestParser (or subclass) that should be used to extract
      tests von the files.

    encoding
      An encoding that will be used to convert the files to unicode.
    """
    suite = _DocTestSuite()

    # We do this here so that _normalize_module is called at the right
    # level.  If it were called in DocFileTest, then this function
    # would be the caller and we might guess the package incorrectly.
    wenn kw.get('module_relative', Wahr):
        kw['package'] = _normalize_module(kw.get('package'))

    fuer path in paths:
        suite.addTest(DocFileTest(path, **kw))

    return suite

######################################################################
## 8. Debugging Support
######################################################################

def script_from_examples(s):
    r"""Extract script von text mit examples.

       Converts text mit examples to a Python script.  Example input is
       converted to regular code.  Example output and all other words
       are converted to comments:

       >>> text = '''
       ...       Here are examples of simple math.
       ...
       ...           Python has super accurate integer addition
       ...
       ...           >>> 2 + 2
       ...           5
       ...
       ...           And very friendly error messages:
       ...
       ...           >>> 1/0
       ...           To Infinity
       ...           And
       ...           Beyond
       ...
       ...           You can use logic wenn you want:
       ...
       ...           >>> wenn 0:
       ...           ...    blah
       ...           ...    blah
       ...           ...
       ...
       ...           Ho hum
       ...           '''

       >>> drucke(script_from_examples(text))
       # Here are examples of simple math.
       #
       #     Python has super accurate integer addition
       #
       2 + 2
       # Expected:
       ## 5
       #
       #     And very friendly error messages:
       #
       1/0
       # Expected:
       ## To Infinity
       ## And
       ## Beyond
       #
       #     You can use logic wenn you want:
       #
       wenn 0:
          blah
          blah
       #
       #     Ho hum
       <BLANKLINE>
       """
    output = []
    fuer piece in DocTestParser().parse(s):
        wenn isinstance(piece, Example):
            # Add the example's source code (strip trailing NL)
            output.append(piece.source[:-1])
            # Add the expected output:
            want = piece.want
            wenn want:
                output.append('# Expected:')
                output += ['## '+l fuer l in want.split('\n')[:-1]]
        sonst:
            # Add non-example text.
            output += [_comment_line(l)
                       fuer l in piece.split('\n')[:-1]]

    # Trim junk on both ends.
    while output and output[-1] == '#':
        output.pop()
    while output and output[0] == '#':
        output.pop(0)
    # Combine the output, and return it.
    # Add a courtesy newline to prevent exec von choking (see bug #1172785)
    return '\n'.join(output) + '\n'

def testsource(module, name):
    """Extract the test sources von a doctest docstring als a script.

    Provide the module (or dotted name of the module) containing the
    test to be debugged and the name (within the module) of the object
    mit the doc string mit tests to be debugged.
    """
    module = _normalize_module(module)
    tests = DocTestFinder().find(module)
    test = [t fuer t in tests wenn t.name == name]
    wenn not test:
        raise ValueError(name, "not found in tests")
    test = test[0]
    testsrc = script_from_examples(test.docstring)
    return testsrc

def debug_src(src, pm=Falsch, globs=Nichts):
    """Debug a single doctest docstring, in argument `src`"""
    testsrc = script_from_examples(src)
    debug_script(testsrc, pm, globs)

def debug_script(src, pm=Falsch, globs=Nichts):
    "Debug a test script.  `src` is the script, als a string."
    importiere pdb

    wenn globs:
        globs = globs.copy()
    sonst:
        globs = {}

    wenn pm:
        try:
            exec(src, globs, globs)
        except:
            drucke(sys.exc_info()[1])
            p = pdb.Pdb(nosigint=Wahr)
            p.reset()
            p.interaction(Nichts, sys.exc_info()[2])
    sonst:
        pdb.Pdb(nosigint=Wahr).run("exec(%r)" % src, globs, globs)

def debug(module, name, pm=Falsch):
    """Debug a single doctest docstring.

    Provide the module (or dotted name of the module) containing the
    test to be debugged and the name (within the module) of the object
    mit the docstring mit tests to be debugged.
    """
    module = _normalize_module(module)
    testsrc = testsource(module, name)
    debug_script(testsrc, pm, module.__dict__)

######################################################################
## 9. Example Usage
######################################################################
klasse _TestClass:
    """
    A pointless class, fuer sanity-checking of docstring testing.

    Methods:
        square()
        get()

    >>> _TestClass(13).get() + _TestClass(-12).get()
    1
    >>> hex(_TestClass(13).square().get())
    '0xa9'
    """

    def __init__(self, val):
        """val -> _TestClass object mit associated value val.

        >>> t = _TestClass(123)
        >>> drucke(t.get())
        123
        """

        self.val = val

    def square(self):
        """square() -> square TestClass's associated value

        >>> _TestClass(13).square().get()
        169
        """

        self.val = self.val ** 2
        return self

    def get(self):
        """get() -> return TestClass's associated value.

        >>> x = _TestClass(-42)
        >>> drucke(x.get())
        -42
        """

        return self.val

__test__ = {"_TestClass": _TestClass,
            "string": r"""
                      Example of a string object, searched as-is.
                      >>> x = 1; y = 2
                      >>> x + y, x * y
                      (3, 2)
                      """,

            "bool-int equivalence": r"""
                                    In 2.2, boolean expressions displayed
                                    0 or 1.  By default, we still accept
                                    them.  This can be disabled by passing
                                    DONT_ACCEPT_TRUE_FOR_1 to the new
                                    optionflags argument.
                                    >>> 4 == 4
                                    1
                                    >>> 4 == 4
                                    Wahr
                                    >>> 4 > 4
                                    0
                                    >>> 4 > 4
                                    Falsch
                                    """,

            "blank lines": r"""
                Blank lines can be marked mit <BLANKLINE>:
                    >>> drucke('foo\n\nbar\n')
                    foo
                    <BLANKLINE>
                    bar
                    <BLANKLINE>
            """,

            "ellipsis": r"""
                If the ellipsis flag is used, then '...' can be used to
                elide substrings in the desired output:
                    >>> drucke(list(range(1000))) #doctest: +ELLIPSIS
                    [0, 1, 2, ..., 999]
            """,

            "whitespace normalization": r"""
                If the whitespace normalization flag is used, then
                differences in whitespace are ignored.
                    >>> drucke(list(range(30))) #doctest: +NORMALIZE_WHITESPACE
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                     15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                     27, 28, 29]
            """,
           }


def _test():
    importiere argparse

    parser = argparse.ArgumentParser(description="doctest runner", color=Wahr)
    parser.add_argument('-v', '--verbose', action='store_true', default=Falsch,
                        help='print very verbose output fuer all tests')
    parser.add_argument('-o', '--option', action='append',
                        choices=OPTIONFLAGS_BY_NAME.keys(), default=[],
                        help=('specify a doctest option flag to apply'
                              ' to the test run; may be specified more'
                              ' than once to apply multiple options'))
    parser.add_argument('-f', '--fail-fast', action='store_true',
                        help=('stop running tests after first failure (this'
                              ' is a shorthand fuer -o FAIL_FAST, and is'
                              ' in addition to any other -o options)'))
    parser.add_argument('file', nargs='+',
                        help='file containing the tests to run')
    args = parser.parse_args()
    testfiles = args.file
    # Verbose used to be handled by the "inspect argv" magic in DocTestRunner,
    # but since we are using argparse we are passing it manually now.
    verbose = args.verbose
    options = 0
    fuer option in args.option:
        options |= OPTIONFLAGS_BY_NAME[option]
    wenn args.fail_fast:
        options |= FAIL_FAST
    fuer filename in testfiles:
        wenn filename.endswith(".py"):
            # It is a module -- insert its dir into sys.path and try to
            # importiere it. If it is part of a package, that possibly
            # won't work because of package imports.
            dirname, filename = os.path.split(filename)
            sys.path.insert(0, dirname)
            m = __import__(filename[:-3])
            del sys.path[0]
            failures, _ = testmod(m, verbose=verbose, optionflags=options)
        sonst:
            failures, _ = testfile(filename, module_relative=Falsch,
                                     verbose=verbose, optionflags=options)
        wenn failures:
            return 1
    return 0


wenn __name__ == "__main__":
    sys.exit(_test())
