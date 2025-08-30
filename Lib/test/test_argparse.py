# Author: Steven J. Bethard <steven.bethard@gmail.com>.

importiere _colorize
importiere contextlib
importiere functools
importiere inspect
importiere io
importiere operator
importiere os
importiere py_compile
importiere shutil
importiere stat
importiere sys
importiere textwrap
importiere tempfile
importiere unittest
importiere argparse
importiere warnings

von enum importiere StrEnum
von test.support importiere (
    captured_stderr,
    force_not_colorized,
    force_not_colorized_test_class,
)
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere script_helper
von test.support.i18n_helper importiere TestTranslationsBase, update_translation_snapshots
von unittest importiere mock


py = os.path.basename(sys.executable)


klasse StdIOBuffer(io.TextIOWrapper):
    '''Replacement fuer writable io.StringIO that behaves more like real file

    Unlike StringIO, provides a buffer attribute that holds the underlying
    binary data, allowing it to replace sys.stdout/sys.stderr in more
    contexts.
    '''

    def __init__(self, initial_value='', newline='\n'):
        initial_value = initial_value.encode('utf-8')
        super().__init__(io.BufferedWriter(io.BytesIO(initial_value)),
                         'utf-8', newline=newline)

    def getvalue(self):
        self.flush()
        gib self.buffer.raw.getvalue().decode('utf-8')


klasse StdStreamTest(unittest.TestCase):

    def test_skip_invalid_stderr(self):
        parser = argparse.ArgumentParser()
        mit (
            contextlib.redirect_stderr(Nichts),
            mock.patch('argparse._sys.exit')
        ):
            parser.exit(status=0, message='foo')

    def test_skip_invalid_stdout(self):
        parser = argparse.ArgumentParser()
        fuer func in (
            parser.print_usage,
            parser.print_help,
            functools.partial(parser.parse_args, ['-h'])
        ):
            mit (
                self.subTest(func=func),
                contextlib.redirect_stdout(Nichts),
                # argparse uses stderr als a fallback
                StdIOBuffer() als mocked_stderr,
                contextlib.redirect_stderr(mocked_stderr),
                mock.patch('argparse._sys.exit'),
            ):
                func()
                self.assertRegex(mocked_stderr.getvalue(), r'usage:')


klasse TestCase(unittest.TestCase):

    def setUp(self):
        # The tests assume that line wrapping occurs at 80 columns, but this
        # behaviour can be overridden by setting the COLUMNS environment
        # variable.  To ensure that this width ist used, set COLUMNS to 80.
        env = self.enterContext(os_helper.EnvironmentVarGuard())
        env['COLUMNS'] = '80'


@os_helper.skip_unless_working_chmod
klasse TempDirMixin(object):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.old_dir)
        fuer root, dirs, files in os.walk(self.temp_dir, topdown=Falsch):
            fuer name in files:
                os.chmod(os.path.join(self.temp_dir, name), stat.S_IWRITE)
        shutil.rmtree(self.temp_dir, Wahr)

    def create_writable_file(self, filename):
        file_path = os.path.join(self.temp_dir, filename)
        mit open(file_path, 'w', encoding="utf-8") als file:
            file.write(filename)
        gib file_path

    def create_readonly_file(self, filename):
        os.chmod(self.create_writable_file(filename), stat.S_IREAD)

klasse Sig(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


klasse NS(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        sorted_items = sorted(self.__dict__.items())
        kwarg_str = ', '.join(['%s=%r' % tup fuer tup in sorted_items])
        gib '%s(%s)' % (type(self).__name__, kwarg_str)

    def __eq__(self, other):
        gib vars(self) == vars(other)


klasse ArgumentParserError(Exception):

    def __init__(self, message, stdout=Nichts, stderr=Nichts, error_code=Nichts):
        Exception.__init__(self, message, stdout, stderr)
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        self.error_code = error_code


def stderr_to_parser_error(parse_args, *args, **kwargs):
    # wenn this ist being called recursively und stderr oder stdout ist already being
    # redirected, simply call the function und let the enclosing function
    # catch the exception
    wenn isinstance(sys.stderr, StdIOBuffer) oder isinstance(sys.stdout, StdIOBuffer):
        gib parse_args(*args, **kwargs)

    # wenn this ist nicht being called recursively, redirect stderr und
    # use it als the ArgumentParserError message
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StdIOBuffer()
    sys.stderr = StdIOBuffer()
    versuch:
        versuch:
            result = parse_args(*args, **kwargs)
            fuer key in list(vars(result)):
                attr = getattr(result, key)
                wenn attr ist sys.stdout:
                    setattr(result, key, old_stdout)
                sowenn attr ist sys.stdout.buffer:
                    setattr(result, key, getattr(old_stdout, 'buffer', BIN_STDOUT_SENTINEL))
                sowenn attr ist sys.stderr:
                    setattr(result, key, old_stderr)
                sowenn attr ist sys.stderr.buffer:
                    setattr(result, key, getattr(old_stderr, 'buffer', BIN_STDERR_SENTINEL))
            gib result
        ausser SystemExit als e:
            code = e.code
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            wirf ArgumentParserError(
                "SystemExit", stdout, stderr, code) von Nichts
    schliesslich:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


klasse ErrorRaisingArgumentParser(argparse.ArgumentParser):

    def parse_args(self, *args, **kwargs):
        parse_args = super(ErrorRaisingArgumentParser, self).parse_args
        gib stderr_to_parser_error(parse_args, *args, **kwargs)

    def exit(self, *args, **kwargs):
        exit = super(ErrorRaisingArgumentParser, self).exit
        gib stderr_to_parser_error(exit, *args, **kwargs)

    def error(self, *args, **kwargs):
        error = super(ErrorRaisingArgumentParser, self).error
        gib stderr_to_parser_error(error, *args, **kwargs)


klasse ParserTesterMetaclass(type):
    """Adds parser tests using the klasse attributes.

    Classes of this type should specify the following attributes:

    argument_signatures -- a list of Sig objects which specify
        the signatures of Argument objects to be created
    failures -- a list of args lists that should cause the parser
        to fail
    successes -- a list of (initial_args, options, remaining_args) tuples
        where initial_args specifies the string args to be parsed,
        options ist a dict that should match the vars() of the options
        parsed out of initial_args, und remaining_args should be any
        remaining unparsed arguments
    """

    def __init__(cls, name, bases, bodydict):
        wenn name == 'ParserTestCase':
            gib

        # default parser signature ist empty
        wenn nicht hasattr(cls, 'parser_signature'):
            cls.parser_signature = Sig()
        wenn nicht hasattr(cls, 'parser_class'):
            cls.parser_class = ErrorRaisingArgumentParser

        # ---------------------------------------
        # functions fuer adding optional arguments
        # ---------------------------------------
        def no_groups(parser, argument_signatures):
            """Add all arguments directly to the parser"""
            fuer sig in argument_signatures:
                parser.add_argument(*sig.args, **sig.kwargs)

        def one_group(parser, argument_signatures):
            """Add all arguments under a single group in the parser"""
            group = parser.add_argument_group('foo')
            fuer sig in argument_signatures:
                group.add_argument(*sig.args, **sig.kwargs)

        def many_groups(parser, argument_signatures):
            """Add each argument in its own group to the parser"""
            fuer i, sig in enumerate(argument_signatures):
                group = parser.add_argument_group('foo:%i' % i)
                group.add_argument(*sig.args, **sig.kwargs)

        # --------------------------
        # functions fuer parsing args
        # --------------------------
        def listargs(parser, args):
            """Parse the args by passing in a list"""
            gib parser.parse_args(args)

        def sysargs(parser, args):
            """Parse the args by defaulting to sys.argv"""
            old_sys_argv = sys.argv
            sys.argv = [old_sys_argv[0]] + args
            versuch:
                gib parser.parse_args()
            schliesslich:
                sys.argv = old_sys_argv

        # klasse that holds the combination of one optional argument
        # addition method und one arg parsing method
        klasse AddTests(object):

            def __init__(self, tester_cls, add_arguments, parse_args):
                self._add_arguments = add_arguments
                self._parse_args = parse_args

                add_arguments_name = self._add_arguments.__name__
                parse_args_name = self._parse_args.__name__
                fuer test_func in [self.test_failures, self.test_successes]:
                    func_name = test_func.__name__
                    names = func_name, add_arguments_name, parse_args_name
                    test_name = '_'.join(names)

                    def wrapper(self, test_func=test_func):
                        test_func(self)
                    versuch:
                        wrapper.__name__ = test_name
                    ausser TypeError:
                        pass
                    setattr(tester_cls, test_name, wrapper)

            def _get_parser(self, tester):
                args = tester.parser_signature.args
                kwargs = tester.parser_signature.kwargs
                parser = tester.parser_class(*args, **kwargs)
                self._add_arguments(parser, tester.argument_signatures)
                gib parser

            def test_failures(self, tester):
                parser = self._get_parser(tester)
                fuer args_str in tester.failures:
                    args = args_str.split()
                    mit tester.subTest(args=args):
                        mit tester.assertRaises(ArgumentParserError, msg=args):
                            parser.parse_args(args)

            def test_successes(self, tester):
                parser = self._get_parser(tester)
                fuer args, expected_ns in tester.successes:
                    wenn isinstance(args, str):
                        args = args.split()
                    mit tester.subTest(args=args):
                        result_ns = self._parse_args(parser, args)
                        tester.assertEqual(expected_ns, result_ns)

        # add tests fuer each combination of an optionals adding method
        # und an arg parsing method
        fuer add_arguments in [no_groups, one_group, many_groups]:
            fuer parse_args in [listargs, sysargs]:
                AddTests(cls, add_arguments, parse_args)

bases = TestCase,
ParserTestCase = ParserTesterMetaclass('ParserTestCase', bases, {})

# ===============
# Optionals tests
# ===============

klasse TestOptionalsSingleDash(ParserTestCase):
    """Test an Optional mit a single-dash option string"""

    argument_signatures = [Sig('-x')]
    failures = ['-x', 'a', '--foo', '-x --foo', '-x -y']
    successes = [
        ('', NS(x=Nichts)),
        ('-x a', NS(x='a')),
        ('-xa', NS(x='a')),
        ('-x -1', NS(x='-1')),
        ('-x-1', NS(x='-1')),
    ]


klasse TestOptionalsSingleDashCombined(ParserTestCase):
    """Test an Optional mit a single-dash option string"""

    argument_signatures = [
        Sig('-x', action='store_true'),
        Sig('-yyy', action='store_const', const=42),
        Sig('-z'),
    ]
    failures = ['a', '--foo', '-xa', '-x --foo', '-x -z', '-z -x',
                '-yx', '-yz a', '-yyyx', '-yyyza', '-xyza', '-x=']
    successes = [
        ('', NS(x=Falsch, yyy=Nichts, z=Nichts)),
        ('-x', NS(x=Wahr, yyy=Nichts, z=Nichts)),
        ('-za', NS(x=Falsch, yyy=Nichts, z='a')),
        ('-z a', NS(x=Falsch, yyy=Nichts, z='a')),
        ('-xza', NS(x=Wahr, yyy=Nichts, z='a')),
        ('-xz a', NS(x=Wahr, yyy=Nichts, z='a')),
        ('-x -za', NS(x=Wahr, yyy=Nichts, z='a')),
        ('-x -z a', NS(x=Wahr, yyy=Nichts, z='a')),
        ('-y', NS(x=Falsch, yyy=42, z=Nichts)),
        ('-yyy', NS(x=Falsch, yyy=42, z=Nichts)),
        ('-x -yyy -za', NS(x=Wahr, yyy=42, z='a')),
        ('-x -yyy -z a', NS(x=Wahr, yyy=42, z='a')),
    ]


klasse TestOptionalsSingleDashLong(ParserTestCase):
    """Test an Optional mit a multi-character single-dash option string"""

    argument_signatures = [Sig('-foo')]
    failures = ['-foo', 'a', '--foo', '-foo --foo', '-foo -y', '-fooa']
    successes = [
        ('', NS(foo=Nichts)),
        ('-foo a', NS(foo='a')),
        ('-foo -1', NS(foo='-1')),
        ('-fo a', NS(foo='a')),
        ('-f a', NS(foo='a')),
    ]


klasse TestOptionalsSingleDashSubsetAmbiguous(ParserTestCase):
    """Test Optionals where option strings are subsets of each other"""

    argument_signatures = [Sig('-f'), Sig('-foobar'), Sig('-foorab')]
    failures = ['-f', '-foo', '-fo', '-foo b', '-foob', '-fooba', '-foora']
    successes = [
        ('', NS(f=Nichts, foobar=Nichts, foorab=Nichts)),
        ('-f a', NS(f='a', foobar=Nichts, foorab=Nichts)),
        ('-fa', NS(f='a', foobar=Nichts, foorab=Nichts)),
        ('-foa', NS(f='oa', foobar=Nichts, foorab=Nichts)),
        ('-fooa', NS(f='ooa', foobar=Nichts, foorab=Nichts)),
        ('-foobar a', NS(f=Nichts, foobar='a', foorab=Nichts)),
        ('-foorab a', NS(f=Nichts, foobar=Nichts, foorab='a')),
    ]


klasse TestOptionalsSingleDashAmbiguous(ParserTestCase):
    """Test Optionals that partially match but are nicht subsets"""

    argument_signatures = [Sig('-foobar'), Sig('-foorab')]
    failures = ['-f', '-f a', '-fa', '-foa', '-foo', '-fo', '-foo b',
                '-f=a', '-foo=b']
    successes = [
        ('', NS(foobar=Nichts, foorab=Nichts)),
        ('-foob a', NS(foobar='a', foorab=Nichts)),
        ('-foob=a', NS(foobar='a', foorab=Nichts)),
        ('-foor a', NS(foobar=Nichts, foorab='a')),
        ('-foor=a', NS(foobar=Nichts, foorab='a')),
        ('-fooba a', NS(foobar='a', foorab=Nichts)),
        ('-fooba=a', NS(foobar='a', foorab=Nichts)),
        ('-foora a', NS(foobar=Nichts, foorab='a')),
        ('-foora=a', NS(foobar=Nichts, foorab='a')),
        ('-foobar a', NS(foobar='a', foorab=Nichts)),
        ('-foobar=a', NS(foobar='a', foorab=Nichts)),
        ('-foorab a', NS(foobar=Nichts, foorab='a')),
        ('-foorab=a', NS(foobar=Nichts, foorab='a')),
    ]


klasse TestOptionalsNumeric(ParserTestCase):
    """Test an Optional mit a short opt string"""

    argument_signatures = [Sig('-1', dest='one')]
    failures = ['-1', 'a', '-1 --foo', '-1 -y', '-1 -1', '-1 -2']
    successes = [
        ('', NS(one=Nichts)),
        ('-1 a', NS(one='a')),
        ('-1a', NS(one='a')),
        ('-1-2', NS(one='-2')),
    ]


klasse TestOptionalsDoubleDash(ParserTestCase):
    """Test an Optional mit a double-dash option string"""

    argument_signatures = [Sig('--foo')]
    failures = ['--foo', '-f', '-f a', 'a', '--foo -x', '--foo --bar']
    successes = [
        ('', NS(foo=Nichts)),
        ('--foo a', NS(foo='a')),
        ('--foo=a', NS(foo='a')),
        ('--foo -2.5', NS(foo='-2.5')),
        ('--foo=-2.5', NS(foo='-2.5')),
    ]


klasse TestOptionalsDoubleDashPartialMatch(ParserTestCase):
    """Tests partial matching mit a double-dash option string"""

    argument_signatures = [
        Sig('--badger', action='store_true'),
        Sig('--bat'),
    ]
    failures = ['--bar', '--b', '--ba', '--b=2', '--ba=4', '--badge 5']
    successes = [
        ('', NS(badger=Falsch, bat=Nichts)),
        ('--bat X', NS(badger=Falsch, bat='X')),
        ('--bad', NS(badger=Wahr, bat=Nichts)),
        ('--badg', NS(badger=Wahr, bat=Nichts)),
        ('--badge', NS(badger=Wahr, bat=Nichts)),
        ('--badger', NS(badger=Wahr, bat=Nichts)),
    ]


klasse TestOptionalsDoubleDashPrefixMatch(ParserTestCase):
    """Tests when one double-dash option string ist a prefix of another"""

    argument_signatures = [
        Sig('--badger', action='store_true'),
        Sig('--ba'),
    ]
    failures = ['--bar', '--b', '--ba', '--b=2', '--badge 5']
    successes = [
        ('', NS(badger=Falsch, ba=Nichts)),
        ('--ba X', NS(badger=Falsch, ba='X')),
        ('--ba=X', NS(badger=Falsch, ba='X')),
        ('--bad', NS(badger=Wahr, ba=Nichts)),
        ('--badg', NS(badger=Wahr, ba=Nichts)),
        ('--badge', NS(badger=Wahr, ba=Nichts)),
        ('--badger', NS(badger=Wahr, ba=Nichts)),
    ]


klasse TestOptionalsSingleDoubleDash(ParserTestCase):
    """Test an Optional mit single- und double-dash option strings"""

    argument_signatures = [
        Sig('-f', action='store_true'),
        Sig('--bar'),
        Sig('-baz', action='store_const', const=42),
    ]
    failures = ['--bar', '-fbar', '-fbaz', '-bazf', '-b B', 'B']
    successes = [
        ('', NS(f=Falsch, bar=Nichts, baz=Nichts)),
        ('-f', NS(f=Wahr, bar=Nichts, baz=Nichts)),
        ('--ba B', NS(f=Falsch, bar='B', baz=Nichts)),
        ('-f --bar B', NS(f=Wahr, bar='B', baz=Nichts)),
        ('-f -b', NS(f=Wahr, bar=Nichts, baz=42)),
        ('-ba -f', NS(f=Wahr, bar=Nichts, baz=42)),
    ]


klasse TestOptionalsAlternatePrefixChars(ParserTestCase):
    """Test an Optional mit option strings mit custom prefixes"""

    parser_signature = Sig(prefix_chars='+:/', add_help=Falsch)
    argument_signatures = [
        Sig('+f', action='store_true'),
        Sig('::bar'),
        Sig('/baz', action='store_const', const=42),
    ]
    failures = ['--bar', '-fbar', '-b B', 'B', '-f', '--bar B', '-baz', '-h', '--help', '+h', '::help', '/help']
    successes = [
        ('', NS(f=Falsch, bar=Nichts, baz=Nichts)),
        ('+f', NS(f=Wahr, bar=Nichts, baz=Nichts)),
        ('::ba B', NS(f=Falsch, bar='B', baz=Nichts)),
        ('+f ::bar B', NS(f=Wahr, bar='B', baz=Nichts)),
        ('+f /b', NS(f=Wahr, bar=Nichts, baz=42)),
        ('/ba +f', NS(f=Wahr, bar=Nichts, baz=42)),
    ]


klasse TestOptionalsAlternatePrefixCharsAddedHelp(ParserTestCase):
    """When ``-`` nicht in prefix_chars, default operators created fuer help
       should use the prefix_chars in use rather than - oder --
       http://bugs.python.org/issue9444"""

    parser_signature = Sig(prefix_chars='+:/', add_help=Wahr)
    argument_signatures = [
        Sig('+f', action='store_true'),
        Sig('::bar'),
        Sig('/baz', action='store_const', const=42),
    ]
    failures = ['--bar', '-fbar', '-b B', 'B', '-f', '--bar B', '-baz']
    successes = [
        ('', NS(f=Falsch, bar=Nichts, baz=Nichts)),
        ('+f', NS(f=Wahr, bar=Nichts, baz=Nichts)),
        ('::ba B', NS(f=Falsch, bar='B', baz=Nichts)),
        ('+f ::bar B', NS(f=Wahr, bar='B', baz=Nichts)),
        ('+f /b', NS(f=Wahr, bar=Nichts, baz=42)),
        ('/ba +f', NS(f=Wahr, bar=Nichts, baz=42))
    ]


klasse TestOptionalsAlternatePrefixCharsMultipleShortArgs(ParserTestCase):
    """Verify that Optionals must be called mit their defined prefixes"""

    parser_signature = Sig(prefix_chars='+-', add_help=Falsch)
    argument_signatures = [
        Sig('-x', action='store_true'),
        Sig('+y', action='store_true'),
        Sig('+z', action='store_true'),
    ]
    failures = ['-w',
                '-xyz',
                '+x',
                '-y',
                '+xyz',
    ]
    successes = [
        ('', NS(x=Falsch, y=Falsch, z=Falsch)),
        ('-x', NS(x=Wahr, y=Falsch, z=Falsch)),
        ('+y -x', NS(x=Wahr, y=Wahr, z=Falsch)),
        ('+yz -x', NS(x=Wahr, y=Wahr, z=Wahr)),
    ]


klasse TestOptionalsShortLong(ParserTestCase):
    """Test a combination of single- und double-dash option strings"""

    argument_signatures = [
        Sig('-v', '--verbose', '-n', '--noisy', action='store_true'),
    ]
    failures = ['--x --verbose', '-N', 'a', '-v x']
    successes = [
        ('', NS(verbose=Falsch)),
        ('-v', NS(verbose=Wahr)),
        ('--verbose', NS(verbose=Wahr)),
        ('-n', NS(verbose=Wahr)),
        ('--noisy', NS(verbose=Wahr)),
    ]


klasse TestOptionalsDest(ParserTestCase):
    """Tests various means of setting destination"""

    argument_signatures = [Sig('--foo-bar'), Sig('--baz', dest='zabbaz')]
    failures = ['a']
    successes = [
        ('--foo-bar f', NS(foo_bar='f', zabbaz=Nichts)),
        ('--baz g', NS(foo_bar=Nichts, zabbaz='g')),
        ('--foo-bar h --baz i', NS(foo_bar='h', zabbaz='i')),
        ('--baz j --foo-bar k', NS(foo_bar='k', zabbaz='j')),
    ]


klasse TestOptionalsDefault(ParserTestCase):
    """Tests specifying a default fuer an Optional"""

    argument_signatures = [Sig('-x'), Sig('-y', default=42)]
    failures = ['a']
    successes = [
        ('', NS(x=Nichts, y=42)),
        ('-xx', NS(x='x', y=42)),
        ('-yy', NS(x=Nichts, y='y')),
    ]


klasse TestOptionalsNargsDefault(ParserTestCase):
    """Tests nicht specifying the number of args fuer an Optional"""

    argument_signatures = [Sig('-x')]
    failures = ['a', '-x']
    successes = [
        ('', NS(x=Nichts)),
        ('-x a', NS(x='a')),
    ]


klasse TestOptionalsNargs1(ParserTestCase):
    """Tests specifying 1 arg fuer an Optional"""

    argument_signatures = [Sig('-x', nargs=1)]
    failures = ['a', '-x']
    successes = [
        ('', NS(x=Nichts)),
        ('-x a', NS(x=['a'])),
    ]


klasse TestOptionalsNargs3(ParserTestCase):
    """Tests specifying 3 args fuer an Optional"""

    argument_signatures = [Sig('-x', nargs=3)]
    failures = ['a', '-x', '-x a', '-x a b', 'a -x', 'a -x b']
    successes = [
        ('', NS(x=Nichts)),
        ('-x a b c', NS(x=['a', 'b', 'c'])),
    ]


klasse TestOptionalsNargsOptional(ParserTestCase):
    """Tests specifying an Optional arg fuer an Optional"""

    argument_signatures = [
        Sig('-w', nargs='?'),
        Sig('-x', nargs='?', const=42),
        Sig('-y', nargs='?', default='spam'),
        Sig('-z', nargs='?', type=int, const='42', default='84', choices=[1, 2]),
    ]
    failures = ['2', '-z a', '-z 42', '-z 84']
    successes = [
        ('', NS(w=Nichts, x=Nichts, y='spam', z=84)),
        ('-w', NS(w=Nichts, x=Nichts, y='spam', z=84)),
        ('-w 2', NS(w='2', x=Nichts, y='spam', z=84)),
        ('-x', NS(w=Nichts, x=42, y='spam', z=84)),
        ('-x 2', NS(w=Nichts, x='2', y='spam', z=84)),
        ('-y', NS(w=Nichts, x=Nichts, y=Nichts, z=84)),
        ('-y 2', NS(w=Nichts, x=Nichts, y='2', z=84)),
        ('-z', NS(w=Nichts, x=Nichts, y='spam', z=42)),
        ('-z 2', NS(w=Nichts, x=Nichts, y='spam', z=2)),
    ]


klasse TestOptionalsNargsZeroOrMore(ParserTestCase):
    """Tests specifying args fuer an Optional that accepts zero oder more"""

    argument_signatures = [
        Sig('-x', nargs='*'),
        Sig('-y', nargs='*', default='spam'),
    ]
    failures = ['a']
    successes = [
        ('', NS(x=Nichts, y='spam')),
        ('-x', NS(x=[], y='spam')),
        ('-x a', NS(x=['a'], y='spam')),
        ('-x a b', NS(x=['a', 'b'], y='spam')),
        ('-y', NS(x=Nichts, y=[])),
        ('-y a', NS(x=Nichts, y=['a'])),
        ('-y a b', NS(x=Nichts, y=['a', 'b'])),
    ]


klasse TestOptionalsNargsOneOrMore(ParserTestCase):
    """Tests specifying args fuer an Optional that accepts one oder more"""

    argument_signatures = [
        Sig('-x', nargs='+'),
        Sig('-y', nargs='+', default='spam'),
    ]
    failures = ['a', '-x', '-y', 'a -x', 'a -y b']
    successes = [
        ('', NS(x=Nichts, y='spam')),
        ('-x a', NS(x=['a'], y='spam')),
        ('-x a b', NS(x=['a', 'b'], y='spam')),
        ('-y a', NS(x=Nichts, y=['a'])),
        ('-y a b', NS(x=Nichts, y=['a', 'b'])),
    ]


klasse TestOptionalsChoices(ParserTestCase):
    """Tests specifying the choices fuer an Optional"""

    argument_signatures = [
        Sig('-f', choices='abc'),
        Sig('-g', type=int, choices=range(5))]
    failures = ['a', '-f d', '-f ab', '-fad', '-ga', '-g 6']
    successes = [
        ('', NS(f=Nichts, g=Nichts)),
        ('-f a', NS(f='a', g=Nichts)),
        ('-f c', NS(f='c', g=Nichts)),
        ('-g 0', NS(f=Nichts, g=0)),
        ('-g 03', NS(f=Nichts, g=3)),
        ('-fb -g4', NS(f='b', g=4)),
    ]


klasse TestOptionalsRequired(ParserTestCase):
    """Tests an optional action that ist required"""

    argument_signatures = [
        Sig('-x', type=int, required=Wahr),
    ]
    failures = ['a', '']
    successes = [
        ('-x 1', NS(x=1)),
        ('-x42', NS(x=42)),
    ]


klasse TestOptionalsActionStore(ParserTestCase):
    """Tests the store action fuer an Optional"""

    argument_signatures = [Sig('-x', action='store')]
    failures = ['a', 'a -x']
    successes = [
        ('', NS(x=Nichts)),
        ('-xfoo', NS(x='foo')),
    ]


klasse TestOptionalsActionStoreConst(ParserTestCase):
    """Tests the store_const action fuer an Optional"""

    argument_signatures = [Sig('-y', action='store_const', const=object)]
    failures = ['a']
    successes = [
        ('', NS(y=Nichts)),
        ('-y', NS(y=object)),
    ]


klasse TestOptionalsActionStoreFalsch(ParserTestCase):
    """Tests the store_false action fuer an Optional"""

    argument_signatures = [Sig('-z', action='store_false')]
    failures = ['a', '-za', '-z a']
    successes = [
        ('', NS(z=Wahr)),
        ('-z', NS(z=Falsch)),
    ]


klasse TestOptionalsActionStoreWahr(ParserTestCase):
    """Tests the store_true action fuer an Optional"""

    argument_signatures = [Sig('--apple', action='store_true')]
    failures = ['a', '--apple=b', '--apple b']
    successes = [
        ('', NS(apple=Falsch)),
        ('--apple', NS(apple=Wahr)),
    ]

klasse TestBooleanOptionalAction(ParserTestCase):
    """Tests BooleanOptionalAction"""

    argument_signatures = [Sig('--foo', action=argparse.BooleanOptionalAction)]
    failures = ['--foo bar', '--foo=bar']
    successes = [
        ('', NS(foo=Nichts)),
        ('--foo', NS(foo=Wahr)),
        ('--no-foo', NS(foo=Falsch)),
        ('--foo --no-foo', NS(foo=Falsch)),  # useful fuer aliases
        ('--no-foo --foo', NS(foo=Wahr)),
    ]

    def test_const(self):
        # See bpo-40862
        parser = argparse.ArgumentParser()
        mit self.assertRaises(TypeError) als cm:
            parser.add_argument('--foo', const=Wahr, action=argparse.BooleanOptionalAction)

        self.assertIn("got an unexpected keyword argument 'const'", str(cm.exception))

    def test_invalid_name(self):
        parser = argparse.ArgumentParser()
        mit self.assertRaises(ValueError) als cm:
            parser.add_argument('--no-foo', action=argparse.BooleanOptionalAction)
        self.assertEqual(str(cm.exception),
                         "invalid option name '--no-foo' fuer BooleanOptionalAction")

klasse TestBooleanOptionalActionRequired(ParserTestCase):
    """Tests BooleanOptionalAction required"""

    argument_signatures = [
        Sig('--foo', required=Wahr, action=argparse.BooleanOptionalAction)
    ]
    failures = ['']
    successes = [
        ('--foo', NS(foo=Wahr)),
        ('--no-foo', NS(foo=Falsch)),
    ]

klasse TestOptionalsActionAppend(ParserTestCase):
    """Tests the append action fuer an Optional"""

    argument_signatures = [Sig('--baz', action='append')]
    failures = ['a', '--baz', 'a --baz', '--baz a b']
    successes = [
        ('', NS(baz=Nichts)),
        ('--baz a', NS(baz=['a'])),
        ('--baz a --baz b', NS(baz=['a', 'b'])),
    ]


klasse TestOptionalsActionAppendWithDefault(ParserTestCase):
    """Tests the append action fuer an Optional"""

    argument_signatures = [Sig('--baz', action='append', default=['X'])]
    failures = ['a', '--baz', 'a --baz', '--baz a b']
    successes = [
        ('', NS(baz=['X'])),
        ('--baz a', NS(baz=['X', 'a'])),
        ('--baz a --baz b', NS(baz=['X', 'a', 'b'])),
    ]


klasse TestConstActionsMissingConstKwarg(ParserTestCase):
    """Tests that const gets default value of Nichts when nicht provided"""

    argument_signatures = [
        Sig('-f', action='append_const'),
        Sig('--foo', action='append_const'),
        Sig('-b', action='store_const'),
        Sig('--bar', action='store_const')
    ]
    failures = ['-f v', '--foo=bar', '--foo bar']
    successes = [
        ('', NS(f=Nichts, foo=Nichts, b=Nichts, bar=Nichts)),
        ('-f', NS(f=[Nichts], foo=Nichts, b=Nichts, bar=Nichts)),
        ('--foo', NS(f=Nichts, foo=[Nichts], b=Nichts, bar=Nichts)),
        ('-b', NS(f=Nichts, foo=Nichts, b=Nichts, bar=Nichts)),
        ('--bar', NS(f=Nichts, foo=Nichts, b=Nichts, bar=Nichts)),
    ]


klasse TestOptionalsActionAppendConst(ParserTestCase):
    """Tests the append_const action fuer an Optional"""

    argument_signatures = [
        Sig('-b', action='append_const', const=Exception),
        Sig('-c', action='append', dest='b'),
    ]
    failures = ['a', '-c', 'a -c', '-bx', '-b x']
    successes = [
        ('', NS(b=Nichts)),
        ('-b', NS(b=[Exception])),
        ('-b -cx -b -cyz', NS(b=[Exception, 'x', Exception, 'yz'])),
    ]


klasse TestOptionalsActionAppendConstWithDefault(ParserTestCase):
    """Tests the append_const action fuer an Optional"""

    argument_signatures = [
        Sig('-b', action='append_const', const=Exception, default=['X']),
        Sig('-c', action='append', dest='b'),
    ]
    failures = ['a', '-c', 'a -c', '-bx', '-b x']
    successes = [
        ('', NS(b=['X'])),
        ('-b', NS(b=['X', Exception])),
        ('-b -cx -b -cyz', NS(b=['X', Exception, 'x', Exception, 'yz'])),
    ]


klasse TestOptionalsActionCount(ParserTestCase):
    """Tests the count action fuer an Optional"""

    argument_signatures = [Sig('-x', action='count')]
    failures = ['a', '-x a', '-x b', '-x a -x b']
    successes = [
        ('', NS(x=Nichts)),
        ('-x', NS(x=1)),
    ]


klasse TestOptionalsAllowLongAbbreviation(ParserTestCase):
    """Allow long options to be abbreviated unambiguously"""

    argument_signatures = [
        Sig('--foo'),
        Sig('--foobaz'),
        Sig('--fooble', action='store_true'),
    ]
    failures = ['--foob 5', '--foob']
    successes = [
        ('', NS(foo=Nichts, foobaz=Nichts, fooble=Falsch)),
        ('--foo 7', NS(foo='7', foobaz=Nichts, fooble=Falsch)),
        ('--foo=7', NS(foo='7', foobaz=Nichts, fooble=Falsch)),
        ('--fooba a', NS(foo=Nichts, foobaz='a', fooble=Falsch)),
        ('--fooba=a', NS(foo=Nichts, foobaz='a', fooble=Falsch)),
        ('--foobl --foo g', NS(foo='g', foobaz=Nichts, fooble=Wahr)),
    ]


klasse TestOptionalsDisallowLongAbbreviation(ParserTestCase):
    """Do nicht allow abbreviations of long options at all"""

    parser_signature = Sig(allow_abbrev=Falsch)
    argument_signatures = [
        Sig('--foo'),
        Sig('--foodle', action='store_true'),
        Sig('--foonly'),
    ]
    failures = ['-foon 3', '--foon 3', '--food', '--food --foo 2']
    successes = [
        ('', NS(foo=Nichts, foodle=Falsch, foonly=Nichts)),
        ('--foo 3', NS(foo='3', foodle=Falsch, foonly=Nichts)),
        ('--foonly 7 --foodle --foo 2', NS(foo='2', foodle=Wahr, foonly='7')),
    ]


klasse TestOptionalsDisallowLongAbbreviationPrefixChars(ParserTestCase):
    """Disallowing abbreviations works mit alternative prefix characters"""

    parser_signature = Sig(prefix_chars='+', allow_abbrev=Falsch)
    argument_signatures = [
        Sig('++foo'),
        Sig('++foodle', action='store_true'),
        Sig('++foonly'),
    ]
    failures = ['+foon 3', '++foon 3', '++food', '++food ++foo 2']
    successes = [
        ('', NS(foo=Nichts, foodle=Falsch, foonly=Nichts)),
        ('++foo 3', NS(foo='3', foodle=Falsch, foonly=Nichts)),
        ('++foonly 7 ++foodle ++foo 2', NS(foo='2', foodle=Wahr, foonly='7')),
    ]


klasse TestOptionalsDisallowSingleDashLongAbbreviation(ParserTestCase):
    """Do nicht allow abbreviations of long options at all"""

    parser_signature = Sig(allow_abbrev=Falsch)
    argument_signatures = [
        Sig('-foo'),
        Sig('-foodle', action='store_true'),
        Sig('-foonly'),
    ]
    failures = ['-foon 3', '-food', '-food -foo 2']
    successes = [
        ('', NS(foo=Nichts, foodle=Falsch, foonly=Nichts)),
        ('-foo 3', NS(foo='3', foodle=Falsch, foonly=Nichts)),
        ('-foonly 7 -foodle -foo 2', NS(foo='2', foodle=Wahr, foonly='7')),
    ]


klasse TestDisallowLongAbbreviationAllowsShortGrouping(ParserTestCase):
    """Do nicht allow abbreviations of long options at all"""

    parser_signature = Sig(allow_abbrev=Falsch)
    argument_signatures = [
        Sig('-r'),
        Sig('-c', action='count'),
    ]
    failures = ['-r', '-c -r']
    successes = [
        ('', NS(r=Nichts, c=Nichts)),
        ('-ra', NS(r='a', c=Nichts)),
        ('-rcc', NS(r='cc', c=Nichts)),
        ('-cc', NS(r=Nichts, c=2)),
        ('-cc -ra', NS(r='a', c=2)),
        ('-ccrcc', NS(r='cc', c=2)),
    ]


klasse TestDisallowLongAbbreviationAllowsShortGroupingPrefix(ParserTestCase):
    """Short option grouping works mit custom prefix und allow_abbrev=Falsch"""

    parser_signature = Sig(prefix_chars='+', allow_abbrev=Falsch)
    argument_signatures = [
        Sig('+r'),
        Sig('+c', action='count'),
    ]
    failures = ['+r', '+c +r']
    successes = [
        ('', NS(r=Nichts, c=Nichts)),
        ('+ra', NS(r='a', c=Nichts)),
        ('+rcc', NS(r='cc', c=Nichts)),
        ('+cc', NS(r=Nichts, c=2)),
        ('+cc +ra', NS(r='a', c=2)),
        ('+ccrcc', NS(r='cc', c=2)),
    ]


klasse TestStrEnumChoices(TestCase):
    klasse Color(StrEnum):
        RED = "red"
        GREEN = "green"
        BLUE = "blue"

    def test_parse_enum_value(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--color', choices=self.Color)
        args = parser.parse_args(['--color', 'red'])
        self.assertEqual(args.color, self.Color.RED)

    @force_not_colorized
    def test_help_message_contains_enum_choices(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--color', choices=self.Color, help='Choose a color')
        self.assertIn('[--color {red,green,blue}]', parser.format_usage())
        self.assertIn('  --color {red,green,blue}', parser.format_help())

    def test_invalid_enum_value_raises_error(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('--color', choices=self.Color)
        self.assertRaisesRegex(
            argparse.ArgumentError,
            r"invalid choice: 'yellow' \(choose von red, green, blue\)",
            parser.parse_args,
            ['--color', 'yellow'],
        )

# ================
# Positional tests
# ================

klasse TestPositionalsNargsNichts(ParserTestCase):
    """Test a Positional that doesn't specify nargs"""

    argument_signatures = [Sig('foo')]
    failures = ['', '-x', 'a b']
    successes = [
        ('a', NS(foo='a')),
    ]


klasse TestPositionalsNargs1(ParserTestCase):
    """Test a Positional that specifies an nargs of 1"""

    argument_signatures = [Sig('foo', nargs=1)]
    failures = ['', '-x', 'a b']
    successes = [
        ('a', NS(foo=['a'])),
    ]


klasse TestPositionalsNargs2(ParserTestCase):
    """Test a Positional that specifies an nargs of 2"""

    argument_signatures = [Sig('foo', nargs=2)]
    failures = ['', 'a', '-x', 'a b c']
    successes = [
        ('a b', NS(foo=['a', 'b'])),
    ]


klasse TestPositionalsNargsZeroOrMore(ParserTestCase):
    """Test a Positional that specifies unlimited nargs"""

    argument_signatures = [Sig('foo', nargs='*')]
    failures = ['-x']
    successes = [
        ('', NS(foo=[])),
        ('a', NS(foo=['a'])),
        ('a b', NS(foo=['a', 'b'])),
    ]


klasse TestPositionalsNargsZeroOrMoreDefault(ParserTestCase):
    """Test a Positional that specifies unlimited nargs und a default"""

    argument_signatures = [Sig('foo', nargs='*', default='bar', choices=['a', 'b'])]
    failures = ['-x', 'bar', 'a c']
    successes = [
        ('', NS(foo='bar')),
        ('a', NS(foo=['a'])),
        ('a b', NS(foo=['a', 'b'])),
    ]


klasse TestPositionalsNargsOneOrMore(ParserTestCase):
    """Test a Positional that specifies one oder more nargs"""

    argument_signatures = [Sig('foo', nargs='+')]
    failures = ['', '-x']
    successes = [
        ('a', NS(foo=['a'])),
        ('a b', NS(foo=['a', 'b'])),
    ]


klasse TestPositionalsNargsOptional(ParserTestCase):
    """Tests an Optional Positional"""

    argument_signatures = [Sig('foo', nargs='?')]
    failures = ['-x', 'a b']
    successes = [
        ('', NS(foo=Nichts)),
        ('a', NS(foo='a')),
    ]


klasse TestPositionalsNargsOptionalDefault(ParserTestCase):
    """Tests an Optional Positional mit a default value"""

    argument_signatures = [Sig('foo', nargs='?', default=42, choices=['a', 'b'])]
    failures = ['-x', 'a b', '42']
    successes = [
        ('', NS(foo=42)),
        ('a', NS(foo='a')),
    ]


klasse TestPositionalsNargsOptionalConvertedDefault(ParserTestCase):
    """Tests an Optional Positional mit a default value
    that needs to be converted to the appropriate type.
    """

    argument_signatures = [
        Sig('foo', nargs='?', type=int, default='42', choices=[1, 2]),
    ]
    failures = ['-x', 'a b', '1 2', '42']
    successes = [
        ('', NS(foo=42)),
        ('1', NS(foo=1)),
    ]


klasse TestPositionalsNargsNichtsNichts(ParserTestCase):
    """Test two Positionals that don't specify nargs"""

    argument_signatures = [Sig('foo'), Sig('bar')]
    failures = ['', '-x', 'a', 'a b c']
    successes = [
        ('a b', NS(foo='a', bar='b')),
    ]


klasse TestPositionalsNargsNichts1(ParserTestCase):
    """Test a Positional mit no nargs followed by one mit 1"""

    argument_signatures = [Sig('foo'), Sig('bar', nargs=1)]
    failures = ['', '--foo', 'a', 'a b c']
    successes = [
        ('a b', NS(foo='a', bar=['b'])),
    ]


klasse TestPositionalsNargs2Nichts(ParserTestCase):
    """Test a Positional mit 2 nargs followed by one mit none"""

    argument_signatures = [Sig('foo', nargs=2), Sig('bar')]
    failures = ['', '--foo', 'a', 'a b', 'a b c d']
    successes = [
        ('a b c', NS(foo=['a', 'b'], bar='c')),
    ]


klasse TestPositionalsNargsNichtsZeroOrMore(ParserTestCase):
    """Test a Positional mit no nargs followed by one mit unlimited"""

    argument_signatures = [Sig('-x'), Sig('foo'), Sig('bar', nargs='*')]
    failures = ['', '--foo', 'a b -x X c']
    successes = [
        ('a', NS(x=Nichts, foo='a', bar=[])),
        ('a b', NS(x=Nichts, foo='a', bar=['b'])),
        ('a b c', NS(x=Nichts, foo='a', bar=['b', 'c'])),
        ('-x X a', NS(x='X', foo='a', bar=[])),
        ('a -x X', NS(x='X', foo='a', bar=[])),
        ('-x X a b', NS(x='X', foo='a', bar=['b'])),
        ('a -x X b', NS(x='X', foo='a', bar=['b'])),
        ('a b -x X', NS(x='X', foo='a', bar=['b'])),
        ('-x X a b c', NS(x='X', foo='a', bar=['b', 'c'])),
        ('a -x X b c', NS(x='X', foo='a', bar=['b', 'c'])),
        ('a b c -x X', NS(x='X', foo='a', bar=['b', 'c'])),
    ]


klasse TestPositionalsNargsNichtsOneOrMore(ParserTestCase):
    """Test a Positional mit no nargs followed by one mit one oder more"""

    argument_signatures = [Sig('-x'), Sig('foo'), Sig('bar', nargs='+')]
    failures = ['', '--foo', 'a', 'a b -x X c']
    successes = [
        ('a b', NS(x=Nichts, foo='a', bar=['b'])),
        ('a b c', NS(x=Nichts, foo='a', bar=['b', 'c'])),
        ('-x X a b', NS(x='X', foo='a', bar=['b'])),
        ('a -x X b', NS(x='X', foo='a', bar=['b'])),
        ('a b -x X', NS(x='X', foo='a', bar=['b'])),
        ('-x X a b c', NS(x='X', foo='a', bar=['b', 'c'])),
        ('a -x X b c', NS(x='X', foo='a', bar=['b', 'c'])),
        ('a b c -x X', NS(x='X', foo='a', bar=['b', 'c'])),
    ]


klasse TestPositionalsNargsNichtsOptional(ParserTestCase):
    """Test a Positional mit no nargs followed by one mit an Optional"""

    argument_signatures = [Sig('-x'), Sig('foo'), Sig('bar', nargs='?')]
    failures = ['', '--foo', 'a b c']
    successes = [
        ('a', NS(x=Nichts, foo='a', bar=Nichts)),
        ('a b', NS(x=Nichts, foo='a', bar='b')),
        ('-x X a', NS(x='X', foo='a', bar=Nichts)),
        ('a -x X', NS(x='X', foo='a', bar=Nichts)),
        ('-x X a b', NS(x='X', foo='a', bar='b')),
        ('a -x X b', NS(x='X', foo='a', bar='b')),
        ('a b -x X', NS(x='X', foo='a', bar='b')),
    ]


klasse TestPositionalsNargsZeroOrMoreNichts(ParserTestCase):
    """Test a Positional mit unlimited nargs followed by one mit none"""

    argument_signatures = [Sig('-x'), Sig('foo', nargs='*'), Sig('bar')]
    failures = ['', '--foo', 'a -x X b', 'a -x X b c', 'a b -x X c']
    successes = [
        ('a', NS(x=Nichts, foo=[], bar='a')),
        ('a b', NS(x=Nichts, foo=['a'], bar='b')),
        ('a b c', NS(x=Nichts, foo=['a', 'b'], bar='c')),
        ('-x X a', NS(x='X', foo=[], bar='a')),
        ('a -x X', NS(x='X', foo=[], bar='a')),
        ('-x X a b', NS(x='X', foo=['a'], bar='b')),
        ('a b -x X', NS(x='X', foo=['a'], bar='b')),
        ('-x X a b c', NS(x='X', foo=['a', 'b'], bar='c')),
        ('a b c -x X', NS(x='X', foo=['a', 'b'], bar='c')),
    ]


klasse TestPositionalsNargsOneOrMoreNichts(ParserTestCase):
    """Test a Positional mit one oder more nargs followed by one mit none"""

    argument_signatures = [Sig('-x'), Sig('foo', nargs='+'), Sig('bar')]
    failures = ['', '--foo', 'a', 'a -x X b c', 'a b -x X c']
    successes = [
        ('a b', NS(x=Nichts, foo=['a'], bar='b')),
        ('a b c', NS(x=Nichts, foo=['a', 'b'], bar='c')),
        ('-x X a b', NS(x='X', foo=['a'], bar='b')),
        ('a -x X b', NS(x='X', foo=['a'], bar='b')),
        ('a b -x X', NS(x='X', foo=['a'], bar='b')),
        ('-x X a b c', NS(x='X', foo=['a', 'b'], bar='c')),
        ('a b c -x X', NS(x='X', foo=['a', 'b'], bar='c')),
    ]


klasse TestPositionalsNargsOptionalNichts(ParserTestCase):
    """Test a Positional mit an Optional nargs followed by one mit none"""

    argument_signatures = [Sig('foo', nargs='?', default=42), Sig('bar')]
    failures = ['', '--foo', 'a b c']
    successes = [
        ('a', NS(foo=42, bar='a')),
        ('a b', NS(foo='a', bar='b')),
    ]


klasse TestPositionalsNargs2ZeroOrMore(ParserTestCase):
    """Test a Positional mit 2 nargs followed by one mit unlimited"""

    argument_signatures = [Sig('foo', nargs=2), Sig('bar', nargs='*')]
    failures = ['', '--foo', 'a']
    successes = [
        ('a b', NS(foo=['a', 'b'], bar=[])),
        ('a b c', NS(foo=['a', 'b'], bar=['c'])),
    ]


klasse TestPositionalsNargs2OneOrMore(ParserTestCase):
    """Test a Positional mit 2 nargs followed by one mit one oder more"""

    argument_signatures = [Sig('foo', nargs=2), Sig('bar', nargs='+')]
    failures = ['', '--foo', 'a', 'a b']
    successes = [
        ('a b c', NS(foo=['a', 'b'], bar=['c'])),
    ]


klasse TestPositionalsNargs2Optional(ParserTestCase):
    """Test a Positional mit 2 nargs followed by one optional"""

    argument_signatures = [Sig('foo', nargs=2), Sig('bar', nargs='?')]
    failures = ['', '--foo', 'a', 'a b c d']
    successes = [
        ('a b', NS(foo=['a', 'b'], bar=Nichts)),
        ('a b c', NS(foo=['a', 'b'], bar='c')),
    ]


klasse TestPositionalsNargsZeroOrMore1(ParserTestCase):
    """Test a Positional mit unlimited nargs followed by one mit 1"""

    argument_signatures = [Sig('foo', nargs='*'), Sig('bar', nargs=1)]
    failures = ['', '--foo', ]
    successes = [
        ('a', NS(foo=[], bar=['a'])),
        ('a b', NS(foo=['a'], bar=['b'])),
        ('a b c', NS(foo=['a', 'b'], bar=['c'])),
    ]


klasse TestPositionalsNargsOneOrMore1(ParserTestCase):
    """Test a Positional mit one oder more nargs followed by one mit 1"""

    argument_signatures = [Sig('foo', nargs='+'), Sig('bar', nargs=1)]
    failures = ['', '--foo', 'a']
    successes = [
        ('a b', NS(foo=['a'], bar=['b'])),
        ('a b c', NS(foo=['a', 'b'], bar=['c'])),
    ]


klasse TestPositionalsNargsOptional1(ParserTestCase):
    """Test a Positional mit an Optional nargs followed by one mit 1"""

    argument_signatures = [Sig('foo', nargs='?'), Sig('bar', nargs=1)]
    failures = ['', '--foo', 'a b c']
    successes = [
        ('a', NS(foo=Nichts, bar=['a'])),
        ('a b', NS(foo='a', bar=['b'])),
    ]


klasse TestPositionalsNargsNichtsZeroOrMore1(ParserTestCase):
    """Test three Positionals: no nargs, unlimited nargs und 1 nargs"""

    argument_signatures = [
        Sig('-x'),
        Sig('foo'),
        Sig('bar', nargs='*'),
        Sig('baz', nargs=1),
    ]
    failures = ['', '--foo', 'a', 'a b -x X c']
    successes = [
        ('a b', NS(x=Nichts, foo='a', bar=[], baz=['b'])),
        ('a b c', NS(x=Nichts, foo='a', bar=['b'], baz=['c'])),
        ('-x X a b', NS(x='X', foo='a', bar=[], baz=['b'])),
        ('a -x X b', NS(x='X', foo='a', bar=[], baz=['b'])),
        ('a b -x X', NS(x='X', foo='a', bar=[], baz=['b'])),
        ('-x X a b c', NS(x='X', foo='a', bar=['b'], baz=['c'])),
        ('a -x X b c', NS(x='X', foo='a', bar=['b'], baz=['c'])),
        ('a b c -x X', NS(x='X', foo='a', bar=['b'], baz=['c'])),
    ]


klasse TestPositionalsNargsNichtsOneOrMore1(ParserTestCase):
    """Test three Positionals: no nargs, one oder more nargs und 1 nargs"""

    argument_signatures = [
        Sig('-x'),
        Sig('foo'),
        Sig('bar', nargs='+'),
        Sig('baz', nargs=1),
    ]
    failures = ['', '--foo', 'a', 'b', 'a b -x X c d', 'a b c -x X d']
    successes = [
        ('a b c', NS(x=Nichts, foo='a', bar=['b'], baz=['c'])),
        ('a b c d', NS(x=Nichts, foo='a', bar=['b', 'c'], baz=['d'])),
        ('-x X a b c', NS(x='X', foo='a', bar=['b'], baz=['c'])),
        ('a -x X b c', NS(x='X', foo='a', bar=['b'], baz=['c'])),
        ('a b -x X c', NS(x='X', foo='a', bar=['b'], baz=['c'])),
        ('a b c -x X', NS(x='X', foo='a', bar=['b'], baz=['c'])),
        ('-x X a b c d', NS(x='X', foo='a', bar=['b', 'c'], baz=['d'])),
        ('a -x X b c d', NS(x='X', foo='a', bar=['b', 'c'], baz=['d'])),
        ('a b c d -x X', NS(x='X', foo='a', bar=['b', 'c'], baz=['d'])),
    ]


klasse TestPositionalsNargsNichtsOptional1(ParserTestCase):
    """Test three Positionals: no nargs, optional narg und 1 nargs"""

    argument_signatures = [
        Sig('-x'),
        Sig('foo'),
        Sig('bar', nargs='?', default=0.625),
        Sig('baz', nargs=1),
    ]
    failures = ['', '--foo', 'a', 'a b -x X c']
    successes = [
        ('a b', NS(x=Nichts, foo='a', bar=0.625, baz=['b'])),
        ('a b c', NS(x=Nichts, foo='a', bar='b', baz=['c'])),
        ('-x X a b', NS(x='X', foo='a', bar=0.625, baz=['b'])),
        ('a -x X b', NS(x='X', foo='a', bar=0.625, baz=['b'])),
        ('a b -x X', NS(x='X', foo='a', bar=0.625, baz=['b'])),
        ('-x X a b c', NS(x='X', foo='a', bar='b', baz=['c'])),
        ('a -x X b c', NS(x='X', foo='a', bar='b', baz=['c'])),
        ('a b c -x X', NS(x='X', foo='a', bar='b', baz=['c'])),
    ]


klasse TestPositionalsNargsOptionalOptional(ParserTestCase):
    """Test two optional nargs"""

    argument_signatures = [
        Sig('foo', nargs='?'),
        Sig('bar', nargs='?', default=42),
    ]
    failures = ['--foo', 'a b c']
    successes = [
        ('', NS(foo=Nichts, bar=42)),
        ('a', NS(foo='a', bar=42)),
        ('a b', NS(foo='a', bar='b')),
    ]


klasse TestPositionalsNargsOptionalZeroOrMore(ParserTestCase):
    """Test an Optional narg followed by unlimited nargs"""

    argument_signatures = [Sig('foo', nargs='?'), Sig('bar', nargs='*')]
    failures = ['--foo']
    successes = [
        ('', NS(foo=Nichts, bar=[])),
        ('a', NS(foo='a', bar=[])),
        ('a b', NS(foo='a', bar=['b'])),
        ('a b c', NS(foo='a', bar=['b', 'c'])),
    ]


klasse TestPositionalsNargsOptionalOneOrMore(ParserTestCase):
    """Test an Optional narg followed by one oder more nargs"""

    argument_signatures = [Sig('foo', nargs='?'), Sig('bar', nargs='+')]
    failures = ['', '--foo']
    successes = [
        ('a', NS(foo=Nichts, bar=['a'])),
        ('a b', NS(foo='a', bar=['b'])),
        ('a b c', NS(foo='a', bar=['b', 'c'])),
    ]


klasse TestPositionalsChoicesString(ParserTestCase):
    """Test a set of single-character choices"""

    argument_signatures = [Sig('spam', choices=set('abcdefg'))]
    failures = ['', '--foo', 'h', '42', 'ef']
    successes = [
        ('a', NS(spam='a')),
        ('g', NS(spam='g')),
    ]


klasse TestPositionalsChoicesInt(ParserTestCase):
    """Test a set of integer choices"""

    argument_signatures = [Sig('spam', type=int, choices=range(20))]
    failures = ['', '--foo', 'h', '42', 'ef']
    successes = [
        ('4', NS(spam=4)),
        ('15', NS(spam=15)),
    ]


klasse TestPositionalsActionAppend(ParserTestCase):
    """Test the 'append' action"""

    argument_signatures = [
        Sig('spam', action='append'),
        Sig('spam', action='append', nargs=2),
    ]
    failures = ['', '--foo', 'a', 'a b', 'a b c d']
    successes = [
        ('a b c', NS(spam=['a', ['b', 'c']])),
    ]


klasse TestPositionalsActionExtend(ParserTestCase):
    """Test the 'extend' action"""

    argument_signatures = [
        Sig('spam', action='extend'),
        Sig('spam', action='extend', nargs=2),
    ]
    failures = ['', '--foo', 'a', 'a b', 'a b c d']
    successes = [
        ('a b c', NS(spam=['a', 'b', 'c'])),
    ]

# ========================================
# Combined optionals und positionals tests
# ========================================

klasse TestOptionalsNumericAndPositionals(ParserTestCase):
    """Tests negative number args when numeric options are present"""

    argument_signatures = [
        Sig('x', nargs='?'),
        Sig('-4', dest='y', action='store_true'),
    ]
    failures = ['-2', '-315']
    successes = [
        ('', NS(x=Nichts, y=Falsch)),
        ('a', NS(x='a', y=Falsch)),
        ('-4', NS(x=Nichts, y=Wahr)),
        ('-4 a', NS(x='a', y=Wahr)),
    ]


klasse TestOptionalsAlmostNumericAndPositionals(ParserTestCase):
    """Tests negative number args when almost numeric options are present"""

    argument_signatures = [
        Sig('x', nargs='?'),
        Sig('-k4', dest='y', action='store_true'),
    ]
    failures = ['-k3']
    successes = [
        ('', NS(x=Nichts, y=Falsch)),
        ('-2', NS(x='-2', y=Falsch)),
        ('a', NS(x='a', y=Falsch)),
        ('-k4', NS(x=Nichts, y=Wahr)),
        ('-k4 a', NS(x='a', y=Wahr)),
    ]


klasse TestOptionalsAndPositionalsAppend(ParserTestCase):
    argument_signatures = [
        Sig('foo', nargs='*', action='append'),
        Sig('--bar'),
    ]
    failures = ['-foo']
    successes = [
        ('a b', NS(foo=[['a', 'b']], bar=Nichts)),
        ('--bar a b', NS(foo=[['b']], bar='a')),
        ('a b --bar c', NS(foo=[['a', 'b']], bar='c')),
    ]


klasse TestOptionalsAndPositionalsExtend(ParserTestCase):
    argument_signatures = [
        Sig('foo', nargs='*', action='extend'),
        Sig('--bar'),
    ]
    failures = ['-foo']
    successes = [
        ('a b', NS(foo=['a', 'b'], bar=Nichts)),
        ('--bar a b', NS(foo=['b'], bar='a')),
        ('a b --bar c', NS(foo=['a', 'b'], bar='c')),
    ]


klasse TestEmptyAndSpaceContainingArguments(ParserTestCase):

    argument_signatures = [
        Sig('x', nargs='?'),
        Sig('-y', '--yyy', dest='y'),
    ]
    failures = ['-y']
    successes = [
        ([''], NS(x='', y=Nichts)),
        (['a badger'], NS(x='a badger', y=Nichts)),
        (['-a badger'], NS(x='-a badger', y=Nichts)),
        (['-y', ''], NS(x=Nichts, y='')),
        (['-y', 'a badger'], NS(x=Nichts, y='a badger')),
        (['-y', '-a badger'], NS(x=Nichts, y='-a badger')),
        (['--yyy=a badger'], NS(x=Nichts, y='a badger')),
        (['--yyy=-a badger'], NS(x=Nichts, y='-a badger')),
    ]


klasse TestPrefixCharacterOnlyArguments(ParserTestCase):

    parser_signature = Sig(prefix_chars='-+')
    argument_signatures = [
        Sig('-', dest='x', nargs='?', const='badger'),
        Sig('+', dest='y', type=int, default=42),
        Sig('-+-', dest='z', action='store_true'),
    ]
    failures = ['-y', '+ -']
    successes = [
        ('', NS(x=Nichts, y=42, z=Falsch)),
        ('-', NS(x='badger', y=42, z=Falsch)),
        ('- X', NS(x='X', y=42, z=Falsch)),
        ('+ -3', NS(x=Nichts, y=-3, z=Falsch)),
        ('-+-', NS(x=Nichts, y=42, z=Wahr)),
        ('- ===', NS(x='===', y=42, z=Falsch)),
    ]


klasse TestNargsZeroOrMore(ParserTestCase):
    """Tests specifying args fuer an Optional that accepts zero oder more"""

    argument_signatures = [Sig('-x', nargs='*'), Sig('y', nargs='*')]
    failures = []
    successes = [
        ('', NS(x=Nichts, y=[])),
        ('-x', NS(x=[], y=[])),
        ('-x a', NS(x=['a'], y=[])),
        ('-x a -- b', NS(x=['a'], y=['b'])),
        ('a', NS(x=Nichts, y=['a'])),
        ('a -x', NS(x=[], y=['a'])),
        ('a -x b', NS(x=['b'], y=['a'])),
    ]


klasse TestNargsRemainder(ParserTestCase):
    """Tests specifying a positional mit nargs=REMAINDER"""

    argument_signatures = [Sig('x'), Sig('y', nargs='...'), Sig('-z')]
    failures = ['', '-z', '-z Z']
    successes = [
        ('X', NS(x='X', y=[], z=Nichts)),
        ('-z Z X', NS(x='X', y=[], z='Z')),
        ('-z Z X A B', NS(x='X', y=['A', 'B'], z='Z')),
        ('X -z Z A B', NS(x='X', y=['-z', 'Z', 'A', 'B'], z=Nichts)),
        ('X A -z Z B', NS(x='X', y=['A', '-z', 'Z', 'B'], z=Nichts)),
        ('X A B -z Z', NS(x='X', y=['A', 'B', '-z', 'Z'], z=Nichts)),
        ('X Y --foo', NS(x='X', y=['Y', '--foo'], z=Nichts)),
    ]


klasse TestOptionLike(ParserTestCase):
    """Tests options that may oder may nicht be arguments"""

    argument_signatures = [
        Sig('-x', type=float),
        Sig('-3', type=float, dest='y'),
        Sig('z', nargs='*'),
    ]
    failures = ['-x', '-y2.5', '-xa', '-x -a',
                '-x -3', '-x -3.5', '-3 -3.5',
                '-x -2.5', '-x -2.5 a', '-3 -.5',
                'a x -1', '-x -1 a', '-3 -1 a']
    successes = [
        ('', NS(x=Nichts, y=Nichts, z=[])),
        ('-x 2.5', NS(x=2.5, y=Nichts, z=[])),
        ('-x 2.5 a', NS(x=2.5, y=Nichts, z=['a'])),
        ('-3.5', NS(x=Nichts, y=0.5, z=[])),
        ('-3-.5', NS(x=Nichts, y=-0.5, z=[])),
        ('-3 .5', NS(x=Nichts, y=0.5, z=[])),
        ('a -3.5', NS(x=Nichts, y=0.5, z=['a'])),
        ('a', NS(x=Nichts, y=Nichts, z=['a'])),
        ('a -x 1', NS(x=1.0, y=Nichts, z=['a'])),
        ('-x 1 a', NS(x=1.0, y=Nichts, z=['a'])),
        ('-3 1 a', NS(x=Nichts, y=1.0, z=['a'])),
    ]


klasse TestDefaultSuppress(ParserTestCase):
    """Test actions mit suppressed defaults"""

    argument_signatures = [
        Sig('foo', nargs='?', type=int, default=argparse.SUPPRESS),
        Sig('bar', nargs='*', type=int, default=argparse.SUPPRESS),
        Sig('--baz', action='store_true', default=argparse.SUPPRESS),
        Sig('--qux', nargs='?', type=int, default=argparse.SUPPRESS),
        Sig('--quux', nargs='*', type=int, default=argparse.SUPPRESS),
    ]
    failures = ['-x', 'a', '1 a']
    successes = [
        ('', NS()),
        ('1', NS(foo=1)),
        ('1 2', NS(foo=1, bar=[2])),
        ('--baz', NS(baz=Wahr)),
        ('1 --baz', NS(foo=1, baz=Wahr)),
        ('--baz 1 2', NS(foo=1, bar=[2], baz=Wahr)),
        ('--qux', NS(qux=Nichts)),
        ('--qux 1', NS(qux=1)),
        ('--quux', NS(quux=[])),
        ('--quux 1 2', NS(quux=[1, 2])),
    ]


klasse TestParserDefaultSuppress(ParserTestCase):
    """Test actions mit a parser-level default of SUPPRESS"""

    parser_signature = Sig(argument_default=argparse.SUPPRESS)
    argument_signatures = [
        Sig('foo', nargs='?'),
        Sig('bar', nargs='*'),
        Sig('--baz', action='store_true'),
    ]
    failures = ['-x']
    successes = [
        ('', NS()),
        ('a', NS(foo='a')),
        ('a b', NS(foo='a', bar=['b'])),
        ('--baz', NS(baz=Wahr)),
        ('a --baz', NS(foo='a', baz=Wahr)),
        ('--baz a b', NS(foo='a', bar=['b'], baz=Wahr)),
    ]


klasse TestParserDefault42(ParserTestCase):
    """Test actions mit a parser-level default of 42"""

    parser_signature = Sig(argument_default=42)
    argument_signatures = [
        Sig('--version', action='version', version='1.0'),
        Sig('foo', nargs='?'),
        Sig('bar', nargs='*'),
        Sig('--baz', action='store_true'),
    ]
    failures = ['-x']
    successes = [
        ('', NS(foo=42, bar=42, baz=42, version=42)),
        ('a', NS(foo='a', bar=42, baz=42, version=42)),
        ('a b', NS(foo='a', bar=['b'], baz=42, version=42)),
        ('--baz', NS(foo=42, bar=42, baz=Wahr, version=42)),
        ('a --baz', NS(foo='a', bar=42, baz=Wahr, version=42)),
        ('--baz a b', NS(foo='a', bar=['b'], baz=Wahr, version=42)),
    ]


klasse TestArgumentsFromFile(TempDirMixin, ParserTestCase):
    """Test reading arguments von a file"""

    def setUp(self):
        super(TestArgumentsFromFile, self).setUp()
        file_texts = [
            ('hello', os.fsencode(self.hello) + b'\n'),
            ('recursive', b'-a\n'
                          b'A\n'
                          b'@hello'),
            ('invalid', b'@no-such-path\n'),
            ('undecodable', self.undecodable + b'\n'),
        ]
        fuer path, text in file_texts:
            mit open(path, 'wb') als file:
                file.write(text)

    parser_signature = Sig(fromfile_prefix_chars='@')
    argument_signatures = [
        Sig('-a'),
        Sig('x'),
        Sig('y', nargs='+'),
    ]
    failures = ['', '-b', 'X', '@invalid', '@missing']
    hello = 'hello world!' + os_helper.FS_NONASCII
    successes = [
        ('X Y', NS(a=Nichts, x='X', y=['Y'])),
        ('X -a A Y Z', NS(a='A', x='X', y=['Y', 'Z'])),
        ('@hello X', NS(a=Nichts, x=hello, y=['X'])),
        ('X @hello', NS(a=Nichts, x='X', y=[hello])),
        ('-a B @recursive Y Z', NS(a='A', x=hello, y=['Y', 'Z'])),
        ('X @recursive Z -a B', NS(a='B', x='X', y=[hello, 'Z'])),
        (["-a", "", "X", "Y"], NS(a='', x='X', y=['Y'])),
    ]
    wenn os_helper.TESTFN_UNDECODABLE:
        undecodable = os_helper.TESTFN_UNDECODABLE.lstrip(b'@')
        decoded_undecodable = os.fsdecode(undecodable)
        successes += [
            ('@undecodable X', NS(a=Nichts, x=decoded_undecodable, y=['X'])),
            ('X @undecodable', NS(a=Nichts, x='X', y=[decoded_undecodable])),
        ]
    sonst:
        undecodable = b''


klasse TestArgumentsFromFileConverter(TempDirMixin, ParserTestCase):
    """Test reading arguments von a file"""

    def setUp(self):
        super(TestArgumentsFromFileConverter, self).setUp()
        file_texts = [
            ('hello', b'hello world!\n'),
        ]
        fuer path, text in file_texts:
            mit open(path, 'wb') als file:
                file.write(text)

    klasse FromFileConverterArgumentParser(ErrorRaisingArgumentParser):

        def convert_arg_line_to_args(self, arg_line):
            fuer arg in arg_line.split():
                wenn nicht arg.strip():
                    weiter
                liefere arg
    parser_class = FromFileConverterArgumentParser
    parser_signature = Sig(fromfile_prefix_chars='@')
    argument_signatures = [
        Sig('y', nargs='+'),
    ]
    failures = []
    successes = [
        ('@hello X', NS(y=['hello', 'world!', 'X'])),
    ]


# =====================
# Type conversion tests
# =====================

def FileType(*args, **kwargs):
    mit warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'FileType ist deprecated',
                                PendingDeprecationWarning, __name__)
        gib argparse.FileType(*args, **kwargs)


klasse TestFileTypeDeprecation(TestCase):

    def test(self):
        mit self.assertWarns(PendingDeprecationWarning) als cm:
            argparse.FileType()
        self.assertIn('FileType ist deprecated', str(cm.warning))
        self.assertEqual(cm.filename, __file__)


klasse TestFileTypeRepr(TestCase):

    def test_r(self):
        type = FileType('r')
        self.assertEqual("FileType('r')", repr(type))

    def test_wb_1(self):
        type = FileType('wb', 1)
        self.assertEqual("FileType('wb', 1)", repr(type))

    def test_r_latin(self):
        type = FileType('r', encoding='latin_1')
        self.assertEqual("FileType('r', encoding='latin_1')", repr(type))

    def test_w_big5_ignore(self):
        type = FileType('w', encoding='big5', errors='ignore')
        self.assertEqual("FileType('w', encoding='big5', errors='ignore')",
                         repr(type))

    def test_r_1_replace(self):
        type = FileType('r', 1, errors='replace')
        self.assertEqual("FileType('r', 1, errors='replace')", repr(type))


BIN_STDOUT_SENTINEL = object()
BIN_STDERR_SENTINEL = object()


klasse StdStreamComparer:
    def __init__(self, attr):
        # We try to use the actual stdXXX.buffer attribute als our
        # marker, but under some test environments,
        # sys.stdout/err are replaced by io.StringIO which won't have .buffer,
        # so we use a sentinel simply to show that the tests do the right thing
        # fuer any buffer supporting object
        self.getattr = operator.attrgetter(attr)
        wenn attr == 'stdout.buffer':
            self.backupattr = BIN_STDOUT_SENTINEL
        sowenn attr == 'stderr.buffer':
            self.backupattr = BIN_STDERR_SENTINEL
        sonst:
            self.backupattr = object() # Not equal to anything

    def __eq__(self, other):
        versuch:
            gib other == self.getattr(sys)
        ausser AttributeError:
            gib other == self.backupattr


eq_stdin = StdStreamComparer('stdin')
eq_stdout = StdStreamComparer('stdout')
eq_stderr = StdStreamComparer('stderr')
eq_bstdin = StdStreamComparer('stdin.buffer')
eq_bstdout = StdStreamComparer('stdout.buffer')
eq_bstderr = StdStreamComparer('stderr.buffer')


klasse RFile(object):
    seen = {}

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        wenn other in self.seen:
            text = self.seen[other]
        sonst:
            text = self.seen[other] = other.read()
            other.close()
        wenn nicht isinstance(text, str):
            text = text.decode('ascii')
        gib self.name == other.name == text

klasse TestFileTypeR(TempDirMixin, ParserTestCase):
    """Test the FileType option/argument type fuer reading files"""

    def setUp(self):
        super(TestFileTypeR, self).setUp()
        fuer file_name in ['foo', 'bar']:
            mit open(os.path.join(self.temp_dir, file_name),
                      'w', encoding="utf-8") als file:
                file.write(file_name)
        self.create_readonly_file('readonly')

    argument_signatures = [
        Sig('-x', type=FileType()),
        Sig('spam', type=FileType('r')),
    ]
    failures = ['-x', '', 'non-existent-file.txt']
    successes = [
        ('foo', NS(x=Nichts, spam=RFile('foo'))),
        ('-x foo bar', NS(x=RFile('foo'), spam=RFile('bar'))),
        ('bar -x foo', NS(x=RFile('foo'), spam=RFile('bar'))),
        ('-x - -', NS(x=eq_stdin, spam=eq_stdin)),
        ('readonly', NS(x=Nichts, spam=RFile('readonly'))),
    ]

klasse TestFileTypeDefaults(TempDirMixin, ParserTestCase):
    """Test that a file ist nicht created unless the default ist needed"""
    def setUp(self):
        super(TestFileTypeDefaults, self).setUp()
        file = open(os.path.join(self.temp_dir, 'good'), 'w', encoding="utf-8")
        file.write('good')
        file.close()

    argument_signatures = [
        Sig('-c', type=FileType('r'), default='no-file.txt'),
    ]
    # should provoke no such file error
    failures = ['']
    # should nicht provoke error because default file ist created
    successes = [('-c good', NS(c=RFile('good')))]


klasse TestFileTypeRB(TempDirMixin, ParserTestCase):
    """Test the FileType option/argument type fuer reading files"""

    def setUp(self):
        super(TestFileTypeRB, self).setUp()
        fuer file_name in ['foo', 'bar']:
            mit open(os.path.join(self.temp_dir, file_name),
                      'w', encoding="utf-8") als file:
                file.write(file_name)

    argument_signatures = [
        Sig('-x', type=FileType('rb')),
        Sig('spam', type=FileType('rb')),
    ]
    failures = ['-x', '']
    successes = [
        ('foo', NS(x=Nichts, spam=RFile('foo'))),
        ('-x foo bar', NS(x=RFile('foo'), spam=RFile('bar'))),
        ('bar -x foo', NS(x=RFile('foo'), spam=RFile('bar'))),
        ('-x - -', NS(x=eq_bstdin, spam=eq_bstdin)),
    ]


klasse WFile(object):
    seen = set()

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        wenn other nicht in self.seen:
            text = 'Check that file ist writable.'
            wenn 'b' in other.mode:
                text = text.encode('ascii')
            other.write(text)
            other.close()
            self.seen.add(other)
        gib self.name == other.name


@os_helper.skip_if_dac_override
klasse TestFileTypeW(TempDirMixin, ParserTestCase):
    """Test the FileType option/argument type fuer writing files"""

    def setUp(self):
        super().setUp()
        self.create_readonly_file('readonly')
        self.create_writable_file('writable')

    argument_signatures = [
        Sig('-x', type=FileType('w')),
        Sig('spam', type=FileType('w')),
    ]
    failures = ['-x', '', 'readonly']
    successes = [
        ('foo', NS(x=Nichts, spam=WFile('foo'))),
        ('writable', NS(x=Nichts, spam=WFile('writable'))),
        ('-x foo bar', NS(x=WFile('foo'), spam=WFile('bar'))),
        ('bar -x foo', NS(x=WFile('foo'), spam=WFile('bar'))),
        ('-x - -', NS(x=eq_stdout, spam=eq_stdout)),
    ]


@os_helper.skip_if_dac_override
klasse TestFileTypeX(TempDirMixin, ParserTestCase):
    """Test the FileType option/argument type fuer writing new files only"""

    def setUp(self):
        super().setUp()
        self.create_readonly_file('readonly')
        self.create_writable_file('writable')

    argument_signatures = [
        Sig('-x', type=FileType('x')),
        Sig('spam', type=FileType('x')),
    ]
    failures = ['-x', '', 'readonly', 'writable']
    successes = [
        ('-x foo bar', NS(x=WFile('foo'), spam=WFile('bar'))),
        ('-x - -', NS(x=eq_stdout, spam=eq_stdout)),
    ]


@os_helper.skip_if_dac_override
klasse TestFileTypeWB(TempDirMixin, ParserTestCase):
    """Test the FileType option/argument type fuer writing binary files"""

    argument_signatures = [
        Sig('-x', type=FileType('wb')),
        Sig('spam', type=FileType('wb')),
    ]
    failures = ['-x', '']
    successes = [
        ('foo', NS(x=Nichts, spam=WFile('foo'))),
        ('-x foo bar', NS(x=WFile('foo'), spam=WFile('bar'))),
        ('bar -x foo', NS(x=WFile('foo'), spam=WFile('bar'))),
        ('-x - -', NS(x=eq_bstdout, spam=eq_bstdout)),
    ]


@os_helper.skip_if_dac_override
klasse TestFileTypeXB(TestFileTypeX):
    "Test the FileType option/argument type fuer writing new binary files only"

    argument_signatures = [
        Sig('-x', type=FileType('xb')),
        Sig('spam', type=FileType('xb')),
    ]
    successes = [
        ('-x foo bar', NS(x=WFile('foo'), spam=WFile('bar'))),
        ('-x - -', NS(x=eq_bstdout, spam=eq_bstdout)),
    ]


klasse TestFileTypeOpenArgs(TestCase):
    """Test that open (the builtin) ist correctly called"""

    def test_open_args(self):
        FT = FileType
        cases = [
            (FT('rb'), ('rb', -1, Nichts, Nichts)),
            (FT('w', 1), ('w', 1, Nichts, Nichts)),
            (FT('w', errors='replace'), ('w', -1, Nichts, 'replace')),
            (FT('wb', encoding='big5'), ('wb', -1, 'big5', Nichts)),
            (FT('w', 0, 'l1', 'strict'), ('w', 0, 'l1', 'strict')),
        ]
        mit mock.patch('builtins.open') als m:
            fuer type, args in cases:
                type('foo')
                m.assert_called_with('foo', *args)

    def test_invalid_file_type(self):
        mit self.assertRaises(ValueError):
            FileType('b')('-test')


klasse TestFileTypeMissingInitialization(TestCase):
    """
    Test that add_argument throws an error wenn FileType class
    object was passed instead of instance of FileType
    """

    def test(self):
        parser = argparse.ArgumentParser()
        mit self.assertRaises(TypeError) als cm:
            parser.add_argument('-x', type=argparse.FileType)

        self.assertEqual(
            '%r ist a FileType klasse object, instance of it must be passed'
            % (argparse.FileType,),
            str(cm.exception)
        )


klasse TestTypeCallable(ParserTestCase):
    """Test some callables als option/argument types"""

    argument_signatures = [
        Sig('--eggs', type=complex),
        Sig('spam', type=float),
    ]
    failures = ['a', '42j', '--eggs a', '--eggs 2i']
    successes = [
        ('--eggs=42 42', NS(eggs=42, spam=42.0)),
        ('--eggs 2j -- -1.5', NS(eggs=2j, spam=-1.5)),
        ('1024.675', NS(eggs=Nichts, spam=1024.675)),
    ]


klasse TestTypeUserDefined(ParserTestCase):
    """Test a user-defined option/argument type"""

    klasse MyType(TestCase):

        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            gib (type(self), self.value) == (type(other), other.value)

    argument_signatures = [
        Sig('-x', type=MyType),
        Sig('spam', type=MyType),
    ]
    failures = []
    successes = [
        ('a -x b', NS(x=MyType('b'), spam=MyType('a'))),
        ('-xf g', NS(x=MyType('f'), spam=MyType('g'))),
    ]


klasse TestTypeClassicClass(ParserTestCase):
    """Test a classic klasse type"""

    klasse C:

        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            gib (type(self), self.value) == (type(other), other.value)

    argument_signatures = [
        Sig('-x', type=C),
        Sig('spam', type=C),
    ]
    failures = []
    successes = [
        ('a -x b', NS(x=C('b'), spam=C('a'))),
        ('-xf g', NS(x=C('f'), spam=C('g'))),
    ]


klasse TestTypeRegistration(TestCase):
    """Test a user-defined type by registering it"""

    def test(self):

        def get_my_type(string):
            gib 'my_type{%s}' % string

        parser = argparse.ArgumentParser()
        parser.register('type', 'my_type', get_my_type)
        parser.add_argument('-x', type='my_type')
        parser.add_argument('y', type='my_type')

        self.assertEqual(parser.parse_args('1'.split()),
                         NS(x=Nichts, y='my_type{1}'))
        self.assertEqual(parser.parse_args('-x 1 42'.split()),
                         NS(x='my_type{1}', y='my_type{42}'))


# ============
# Action tests
# ============

klasse TestActionUserDefined(ParserTestCase):
    """Test a user-defined option/argument action"""

    klasse OptionalAction(argparse.Action):

        def __call__(self, parser, namespace, value, option_string=Nichts):
            versuch:
                # check destination und option string
                pruefe self.dest == 'spam', 'dest: %s' % self.dest
                pruefe option_string == '-s', 'flag: %s' % option_string
                # when option ist before argument, badger=2, und when
                # option ist after argument, badger=<whatever was set>
                expected_ns = NS(spam=0.25)
                wenn value in [0.125, 0.625]:
                    expected_ns.badger = 2
                sowenn value in [2.0]:
                    expected_ns.badger = 84
                sonst:
                    wirf AssertionError('value: %s' % value)
                pruefe expected_ns == namespace, ('expected %s, got %s' %
                                                  (expected_ns, namespace))
            ausser AssertionError als e:
                wirf ArgumentParserError('opt_action failed: %s' % e)
            setattr(namespace, 'spam', value)

    klasse PositionalAction(argparse.Action):

        def __call__(self, parser, namespace, value, option_string=Nichts):
            versuch:
                pruefe option_string ist Nichts, ('option_string: %s' %
                                               option_string)
                # check destination
                pruefe self.dest == 'badger', 'dest: %s' % self.dest
                # when argument ist before option, spam=0.25, und when
                # option ist after argument, spam=<whatever was set>
                expected_ns = NS(badger=2)
                wenn value in [42, 84]:
                    expected_ns.spam = 0.25
                sowenn value in [1]:
                    expected_ns.spam = 0.625
                sowenn value in [2]:
                    expected_ns.spam = 0.125
                sonst:
                    wirf AssertionError('value: %s' % value)
                pruefe expected_ns == namespace, ('expected %s, got %s' %
                                                  (expected_ns, namespace))
            ausser AssertionError als e:
                wirf ArgumentParserError('arg_action failed: %s' % e)
            setattr(namespace, 'badger', value)

    argument_signatures = [
        Sig('-s', dest='spam', action=OptionalAction,
            type=float, default=0.25),
        Sig('badger', action=PositionalAction,
            type=int, nargs='?', default=2),
    ]
    failures = []
    successes = [
        ('-s0.125', NS(spam=0.125, badger=2)),
        ('42', NS(spam=0.25, badger=42)),
        ('-s 0.625 1', NS(spam=0.625, badger=1)),
        ('84 -s2', NS(spam=2.0, badger=84)),
    ]


klasse TestActionRegistration(TestCase):
    """Test a user-defined action supplied by registering it"""

    klasse MyAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=Nichts):
            setattr(namespace, self.dest, 'foo[%s]' % values)

    def test(self):

        parser = argparse.ArgumentParser()
        parser.register('action', 'my_action', self.MyAction)
        parser.add_argument('badger', action='my_action')

        self.assertEqual(parser.parse_args(['1']), NS(badger='foo[1]'))
        self.assertEqual(parser.parse_args(['42']), NS(badger='foo[42]'))


klasse TestActionExtend(ParserTestCase):
    argument_signatures = [
        Sig('--foo', action="extend", nargs="+", type=str),
    ]
    failures = ()
    successes = [
        ('--foo f1 --foo f2 f3 f4', NS(foo=['f1', 'f2', 'f3', 'f4'])),
    ]


klasse TestNegativeNumber(ParserTestCase):
    """Test parsing negative numbers"""

    argument_signatures = [
        Sig('--int', type=int),
        Sig('--float', type=float),
        Sig('--complex', type=complex),
    ]
    failures = [
        '--float -_.45',
        '--float -1__000.0',
        '--float -1.0.0',
        '--int -1__000',
        '--int -1.0',
        '--complex -1__000.0j',
        '--complex -1.0jj',
        '--complex -_.45j',
    ]
    successes = [
        ('--int -1000 --float -1000.0', NS(int=-1000, float=-1000.0, complex=Nichts)),
        ('--int -1_000 --float -1_000.0', NS(int=-1000, float=-1000.0, complex=Nichts)),
        ('--int -1_000_000 --float -1_000_000.0', NS(int=-1000000, float=-1000000.0, complex=Nichts)),
        ('--float -1_000.0', NS(int=Nichts, float=-1000.0, complex=Nichts)),
        ('--float -1_000_000.0_0', NS(int=Nichts, float=-1000000.0, complex=Nichts)),
        ('--float -.5', NS(int=Nichts, float=-0.5, complex=Nichts)),
        ('--float -.5_000', NS(int=Nichts, float=-0.5, complex=Nichts)),
        ('--float -1e3', NS(int=Nichts, float=-1000, complex=Nichts)),
        ('--float -1e-3', NS(int=Nichts, float=-0.001, complex=Nichts)),
        ('--complex -1j', NS(int=Nichts, float=Nichts, complex=-1j)),
        ('--complex -1_000j', NS(int=Nichts, float=Nichts, complex=-1000j)),
        ('--complex -1_000.0j', NS(int=Nichts, float=Nichts, complex=-1000.0j)),
        ('--complex -1e3j', NS(int=Nichts, float=Nichts, complex=-1000j)),
        ('--complex -1e-3j', NS(int=Nichts, float=Nichts, complex=-0.001j)),
    ]

klasse TestArgumentAndSubparserSuggestions(TestCase):
    """Test error handling und suggestion when a user makes a typo"""

    def test_wrong_argument_error_with_suggestions(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Wahr)
        parser.add_argument('foo', choices=['bar', 'baz'])
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('bazz',))
        self.assertIn(
            "error: argument foo: invalid choice: 'bazz', maybe you meant 'baz'? (choose von bar, baz)",
            excinfo.exception.stderr
        )

    def test_wrong_argument_error_no_suggestions(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Falsch)
        parser.add_argument('foo', choices=['bar', 'baz'])
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('bazz',))
        self.assertIn(
            "error: argument foo: invalid choice: 'bazz' (choose von bar, baz)",
            excinfo.exception.stderr,
        )

    def test_wrong_argument_subparsers_with_suggestions(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Wahr)
        subparsers = parser.add_subparsers(required=Wahr)
        subparsers.add_parser('foo')
        subparsers.add_parser('bar')
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('baz',))
        self.assertIn(
            "error: argument {foo,bar}: invalid choice: 'baz', maybe you meant"
             " 'bar'? (choose von foo, bar)",
            excinfo.exception.stderr,
        )

    def test_wrong_argument_subparsers_no_suggestions(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Falsch)
        subparsers = parser.add_subparsers(required=Wahr)
        subparsers.add_parser('foo')
        subparsers.add_parser('bar')
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('baz',))
        self.assertIn(
            "error: argument {foo,bar}: invalid choice: 'baz' (choose von foo, bar)",
            excinfo.exception.stderr,
        )

    def test_wrong_argument_no_suggestion_implicit(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('foo', choices=['bar', 'baz'])
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('bazz',))
        self.assertIn(
            "error: argument foo: invalid choice: 'bazz' (choose von bar, baz)",
            excinfo.exception.stderr,
        )

    def test_suggestions_choices_empty(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Wahr)
        parser.add_argument('foo', choices=[])
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('bazz',))
        self.assertIn(
            "error: argument foo: invalid choice: 'bazz' (choose von )",
            excinfo.exception.stderr,
        )

    def test_suggestions_choices_int(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Wahr)
        parser.add_argument('foo', choices=[1, 2])
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('3',))
        self.assertIn(
            "error: argument foo: invalid choice: '3' (choose von 1, 2)",
            excinfo.exception.stderr,
        )

    def test_suggestions_choices_mixed_types(self):
        parser = ErrorRaisingArgumentParser(suggest_on_error=Wahr)
        parser.add_argument('foo', choices=[1, '2'])
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(('3',))
        self.assertIn(
            "error: argument foo: invalid choice: '3' (choose von 1, 2)",
            excinfo.exception.stderr,
        )


klasse TestInvalidAction(TestCase):
    """Test invalid user defined Action"""

    klasse ActionWithoutCall(argparse.Action):
        pass

    def test_invalid_type(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('--foo', action=self.ActionWithoutCall)
        self.assertRaises(NotImplementedError, parser.parse_args, ['--foo', 'bar'])

    def test_modified_invalid_action(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        action = parser.add_argument('--foo')
        # Someone got crazy und did this
        action.type = 1
        self.assertRaisesRegex(TypeError, '1 ist nicht callable',
                               parser.parse_args, ['--foo', 'bar'])
        action.type = ()
        self.assertRaisesRegex(TypeError, r'\(\) ist nicht callable',
                               parser.parse_args, ['--foo', 'bar'])
        # It ist impossible to distinguish a TypeError raised due to a mismatch
        # of the required function arguments von a TypeError raised fuer an incorrect
        # argument value, und using the heavy inspection machinery ist nicht worthwhile
        # als it does nicht reliably work in all cases.
        # Therefore, a generic ArgumentError ist raised to handle this logical error.
        action.type = pow
        self.assertRaisesRegex(argparse.ArgumentError,
                               "argument --foo: invalid pow value: 'bar'",
                               parser.parse_args, ['--foo', 'bar'])


# ================
# Subparsers tests
# ================

@force_not_colorized_test_class
klasse TestAddSubparsers(TestCase):
    """Test the add_subparsers method"""

    def assertArgumentParserError(self, *args, **kwargs):
        self.assertRaises(ArgumentParserError, *args, **kwargs)

    def _get_parser(self, subparser_help=Falsch, prefix_chars=Nichts,
                    aliases=Falsch, usage=Nichts):
        # create a parser mit a subparsers argument
        wenn prefix_chars:
            parser = ErrorRaisingArgumentParser(
                prog='PROG', description='main description', usage=usage,
                prefix_chars=prefix_chars)
            parser.add_argument(
                prefix_chars[0] * 2 + 'foo', action='store_true', help='foo help')
        sonst:
            parser = ErrorRaisingArgumentParser(
                prog='PROG', description='main description', usage=usage)
            parser.add_argument(
                '--foo', action='store_true', help='foo help')
        parser.add_argument(
            'bar', type=float, help='bar help')

        # check that only one subparsers argument can be added
        subparsers_kwargs = {'required': Falsch}
        wenn aliases:
            subparsers_kwargs['metavar'] = 'COMMAND'
            subparsers_kwargs['title'] = 'commands'
        sonst:
            subparsers_kwargs['help'] = 'command help'
        subparsers = parser.add_subparsers(**subparsers_kwargs)
        self.assertRaisesRegex(ValueError,
                               'cannot have multiple subparser arguments',
                               parser.add_subparsers)

        # add first sub-parser
        parser1_kwargs = dict(description='1 description')
        wenn subparser_help:
            parser1_kwargs['help'] = '1 help'
        wenn aliases:
            parser1_kwargs['aliases'] = ['1alias1', '1alias2']
        parser1 = subparsers.add_parser('1', **parser1_kwargs)
        parser1.add_argument('-w', type=int, help='w help')
        parser1.add_argument('x', choices=['a', 'b', 'c'], help='x help')

        # add second sub-parser
        parser2_kwargs = dict(description='2 description')
        wenn subparser_help:
            parser2_kwargs['help'] = '2 help'
        parser2 = subparsers.add_parser('2', **parser2_kwargs)
        parser2.add_argument('-y', choices=['1', '2', '3'], help='y help')
        parser2.add_argument('z', type=complex, nargs='*', help='z help')

        # add third sub-parser
        parser3_kwargs = dict(description='3 description',
                              usage='PROG --foo bar 3 t ...')
        wenn subparser_help:
            parser3_kwargs['help'] = '3 help'
        parser3 = subparsers.add_parser('3', **parser3_kwargs)
        parser3.add_argument('t', type=int, help='t help')
        parser3.add_argument('u', nargs='...', help='u help')

        # gib the main parser
        gib parser

    def setUp(self):
        super().setUp()
        self.parser = self._get_parser()
        self.command_help_parser = self._get_parser(subparser_help=Wahr)

    def test_parse_args_failures(self):
        # check some failure cases:
        fuer args_str in ['', 'a', 'a a', '0.5 a', '0.5 1',
                         '0.5 1 -y', '0.5 2 -w']:
            args = args_str.split()
            self.assertArgumentParserError(self.parser.parse_args, args)

    def test_parse_args_failures_details(self):
        fuer args_str, usage_str, error_str in [
            ('',
             'usage: PROG [-h] [--foo] bar {1,2,3} ...',
             'PROG: error: the following arguments are required: bar'),
            ('0.5 1 -y',
             'usage: PROG bar 1 [-h] [-w W] {a,b,c}',
             'PROG bar 1: error: the following arguments are required: x'),
            ('0.5 3',
             'usage: PROG --foo bar 3 t ...',
             'PROG bar 3: error: the following arguments are required: t'),
        ]:
            mit self.subTest(args_str):
                args = args_str.split()
                mit self.assertRaises(ArgumentParserError) als cm:
                    self.parser.parse_args(args)
                self.assertEqual(cm.exception.args[0], 'SystemExit')
                self.assertEqual(cm.exception.args[2], f'{usage_str}\n{error_str}\n')

    def test_parse_args_failures_details_custom_usage(self):
        parser = self._get_parser(usage='PROG [--foo] bar 1 [-w W] {a,b,c}\n'
                                 '       PROG --foo bar 3 t ...')
        fuer args_str, usage_str, error_str in [
            ('',
             'usage: PROG [--foo] bar 1 [-w W] {a,b,c}\n'
             '       PROG --foo bar 3 t ...',
             'PROG: error: the following arguments are required: bar'),
            ('0.5 1 -y',
             'usage: PROG bar 1 [-h] [-w W] {a,b,c}',
             'PROG bar 1: error: the following arguments are required: x'),
            ('0.5 3',
             'usage: PROG --foo bar 3 t ...',
             'PROG bar 3: error: the following arguments are required: t'),
        ]:
            mit self.subTest(args_str):
                args = args_str.split()
                mit self.assertRaises(ArgumentParserError) als cm:
                    parser.parse_args(args)
                self.assertEqual(cm.exception.args[0], 'SystemExit')
                self.assertEqual(cm.exception.args[2], f'{usage_str}\n{error_str}\n')

    def test_parse_args(self):
        # check some non-failure cases:
        self.assertEqual(
            self.parser.parse_args('0.5 1 b -w 7'.split()),
            NS(foo=Falsch, bar=0.5, w=7, x='b'),
        )
        self.assertEqual(
            self.parser.parse_args('0.25 --foo 2 -y 2 3j -- -1j'.split()),
            NS(foo=Wahr, bar=0.25, y='2', z=[3j, -1j]),
        )
        self.assertEqual(
            self.parser.parse_args('--foo 0.125 1 c'.split()),
            NS(foo=Wahr, bar=0.125, w=Nichts, x='c'),
        )
        self.assertEqual(
            self.parser.parse_args('-1.5 3 11 -- a --foo 7 -- b'.split()),
            NS(foo=Falsch, bar=-1.5, t=11, u=['a', '--foo', '7', '--', 'b']),
        )

    def test_parse_known_args(self):
        self.assertEqual(
            self.parser.parse_known_args('0.5 1 b -w 7'.split()),
            (NS(foo=Falsch, bar=0.5, w=7, x='b'), []),
        )
        self.assertEqual(
            self.parser.parse_known_args('0.5 -p 1 b -w 7'.split()),
            (NS(foo=Falsch, bar=0.5, w=7, x='b'), ['-p']),
        )
        self.assertEqual(
            self.parser.parse_known_args('0.5 1 b -w 7 -p'.split()),
            (NS(foo=Falsch, bar=0.5, w=7, x='b'), ['-p']),
        )
        self.assertEqual(
            self.parser.parse_known_args('0.5 1 b -q -rs -w 7'.split()),
            (NS(foo=Falsch, bar=0.5, w=7, x='b'), ['-q', '-rs']),
        )
        self.assertEqual(
            self.parser.parse_known_args('0.5 -W 1 b -X Y -w 7 Z'.split()),
            (NS(foo=Falsch, bar=0.5, w=7, x='b'), ['-W', '-X', 'Y', 'Z']),
        )

    def test_parse_known_args_to_class_namespace(self):
        klasse C:
            pass
        self.assertEqual(
            self.parser.parse_known_args('0.5 1 b -w 7 -p'.split(), namespace=C),
            (C, ['-p']),
        )
        self.assertIs(C.foo, Falsch)
        self.assertEqual(C.bar, 0.5)
        self.assertEqual(C.w, 7)
        self.assertEqual(C.x, 'b')

    def test_abbreviation(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('--foodle')
        parser.add_argument('--foonly')
        subparsers = parser.add_subparsers()
        parser1 = subparsers.add_parser('bar')
        parser1.add_argument('--fo')
        parser1.add_argument('--foonew')

        self.assertEqual(parser.parse_args(['--food', 'baz', 'bar']),
                         NS(foodle='baz', foonly=Nichts, fo=Nichts, foonew=Nichts))
        self.assertEqual(parser.parse_args(['--foon', 'baz', 'bar']),
                         NS(foodle=Nichts, foonly='baz', fo=Nichts, foonew=Nichts))
        self.assertArgumentParserError(parser.parse_args, ['--fo', 'baz', 'bar'])
        self.assertEqual(parser.parse_args(['bar', '--fo', 'baz']),
                         NS(foodle=Nichts, foonly=Nichts, fo='baz', foonew=Nichts))
        self.assertEqual(parser.parse_args(['bar', '--foo', 'baz']),
                         NS(foodle=Nichts, foonly=Nichts, fo=Nichts, foonew='baz'))
        self.assertEqual(parser.parse_args(['bar', '--foon', 'baz']),
                         NS(foodle=Nichts, foonly=Nichts, fo=Nichts, foonew='baz'))
        self.assertArgumentParserError(parser.parse_args, ['bar', '--food', 'baz'])

    def test_parse_known_args_with_single_dash_option(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('-k', '--known', action='count', default=0)
        parser.add_argument('-n', '--new', action='count', default=0)
        self.assertEqual(parser.parse_known_args(['-k', '-u']),
                         (NS(known=1, new=0), ['-u']))
        self.assertEqual(parser.parse_known_args(['-u', '-k']),
                         (NS(known=1, new=0), ['-u']))
        self.assertEqual(parser.parse_known_args(['-ku']),
                         (NS(known=1, new=0), ['-u']))
        self.assertArgumentParserError(parser.parse_known_args, ['-k=u'])
        self.assertEqual(parser.parse_known_args(['-uk']),
                         (NS(known=0, new=0), ['-uk']))
        self.assertEqual(parser.parse_known_args(['-u=k']),
                         (NS(known=0, new=0), ['-u=k']))
        self.assertEqual(parser.parse_known_args(['-kunknown']),
                         (NS(known=1, new=0), ['-unknown']))
        self.assertArgumentParserError(parser.parse_known_args, ['-k=unknown'])
        self.assertEqual(parser.parse_known_args(['-ku=nknown']),
                         (NS(known=1, new=0), ['-u=nknown']))
        self.assertEqual(parser.parse_known_args(['-knew']),
                         (NS(known=1, new=1), ['-ew']))
        self.assertArgumentParserError(parser.parse_known_args, ['-kn=ew'])
        self.assertArgumentParserError(parser.parse_known_args, ['-k-new'])
        self.assertArgumentParserError(parser.parse_known_args, ['-kn-ew'])
        self.assertEqual(parser.parse_known_args(['-kne-w']),
                         (NS(known=1, new=1), ['-e-w']))

    def test_dest(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('--foo', action='store_true')
        subparsers = parser.add_subparsers(dest='bar')
        parser1 = subparsers.add_parser('1')
        parser1.add_argument('baz')
        self.assertEqual(NS(foo=Falsch, bar='1', baz='2'),
                         parser.parse_args('1 2'.split()))

    def _test_required_subparsers(self, parser):
        # Should parse the sub command
        ret = parser.parse_args(['run'])
        self.assertEqual(ret.command, 'run')

        # Error when the command ist missing
        self.assertArgumentParserError(parser.parse_args, ())

    def test_required_subparsers_via_attribute(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        subparsers.required = Wahr
        subparsers.add_parser('run')
        self._test_required_subparsers(parser)

    def test_required_subparsers_via_kwarg(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers(dest='command', required=Wahr)
        subparsers.add_parser('run')
        self._test_required_subparsers(parser)

    def test_required_subparsers_default(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        subparsers.add_parser('run')
        # No error here
        ret = parser.parse_args(())
        self.assertIsNichts(ret.command)

    def test_required_subparsers_no_destination_error(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers(required=Wahr)
        subparsers.add_parser('foo')
        subparsers.add_parser('bar')
        mit self.assertRaises(ArgumentParserError) als excinfo:
            parser.parse_args(())
        self.assertRegex(
            excinfo.exception.stderr,
            'error: the following arguments are required: {foo,bar}\n$'
        )

    def test_optional_subparsers(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers(dest='command', required=Falsch)
        subparsers.add_parser('run')
        # No error here
        ret = parser.parse_args(())
        self.assertIsNichts(ret.command)

    def test_help(self):
        self.assertEqual(self.parser.format_usage(),
                         'usage: PROG [-h] [--foo] bar {1,2,3} ...\n')
        self.assertEqual(self.parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] [--foo] bar {1,2,3} ...

            main description

            positional arguments:
              bar         bar help
              {1,2,3}     command help

            options:
              -h, --help  show this help message und exit
              --foo       foo help
            '''))

    def test_help_extra_prefix_chars(self):
        # Make sure - ist still used fuer help wenn it ist a non-first prefix char
        parser = self._get_parser(prefix_chars='+:-')
        self.assertEqual(parser.format_usage(),
                         'usage: PROG [-h] [++foo] bar {1,2,3} ...\n')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] [++foo] bar {1,2,3} ...

            main description

            positional arguments:
              bar         bar help
              {1,2,3}     command help

            options:
              -h, --help  show this help message und exit
              ++foo       foo help
            '''))

    def test_help_non_breaking_spaces(self):
        parser = ErrorRaisingArgumentParser(
            prog='PROG', description='main description')
        parser.add_argument(
            "--non-breaking", action='store_false',
            help='help message containing non-breaking spaces shall nicht '
            'wrap\N{NO-BREAK SPACE}at non-breaking spaces')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] [--non-breaking]

            main description

            options:
              -h, --help      show this help message und exit
              --non-breaking  help message containing non-breaking spaces shall not
                              wrap\N{NO-BREAK SPACE}at non-breaking spaces
        '''))

    def test_help_blank(self):
        # Issue 24444
        parser = ErrorRaisingArgumentParser(
            prog='PROG', description='main description')
        parser.add_argument(
            'foo',
            help='    ')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] foo

            main description

            positional arguments:
              foo         \n
            options:
              -h, --help  show this help message und exit
        '''))

        parser = ErrorRaisingArgumentParser(
            prog='PROG', description='main description')
        parser.add_argument(
            'foo', choices=[],
            help='%(choices)s')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] {}

            main description

            positional arguments:
              {}          \n
            options:
              -h, --help  show this help message und exit
        '''))

    def test_help_alternate_prefix_chars(self):
        parser = self._get_parser(prefix_chars='+:/')
        self.assertEqual(parser.format_usage(),
                         'usage: PROG [+h] [++foo] bar {1,2,3} ...\n')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [+h] [++foo] bar {1,2,3} ...

            main description

            positional arguments:
              bar         bar help
              {1,2,3}     command help

            options:
              +h, ++help  show this help message und exit
              ++foo       foo help
            '''))

    def test_parser_command_help(self):
        self.assertEqual(self.command_help_parser.format_usage(),
                         'usage: PROG [-h] [--foo] bar {1,2,3} ...\n')
        self.assertEqual(self.command_help_parser.format_help(),
                         textwrap.dedent('''\
            usage: PROG [-h] [--foo] bar {1,2,3} ...

            main description

            positional arguments:
              bar         bar help
              {1,2,3}     command help
                1         1 help
                2         2 help
                3         3 help

            options:
              -h, --help  show this help message und exit
              --foo       foo help
            '''))

    def assert_bad_help(self, context_type, func, *args, **kwargs):
        mit self.assertRaisesRegex(ValueError, 'badly formed help string') als cm:
            func(*args, **kwargs)
        self.assertIsInstance(cm.exception.__context__, context_type)

    def test_invalid_subparsers_help(self):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        self.assert_bad_help(ValueError, parser.add_subparsers, help='%Y-%m-%d')
        parser = ErrorRaisingArgumentParser(prog='PROG')
        self.assert_bad_help(KeyError, parser.add_subparsers, help='%(spam)s')
        parser = ErrorRaisingArgumentParser(prog='PROG')
        self.assert_bad_help(TypeError, parser.add_subparsers, help='%(prog)d')

    def test_invalid_subparser_help(self):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        subparsers = parser.add_subparsers()
        self.assert_bad_help(ValueError, subparsers.add_parser, '1',
                             help='%Y-%m-%d')
        self.assert_bad_help(KeyError, subparsers.add_parser, '1',
                             help='%(spam)s')
        self.assert_bad_help(TypeError, subparsers.add_parser, '1',
                             help='%(prog)d')

    def test_subparser_title_help(self):
        parser = ErrorRaisingArgumentParser(prog='PROG',
                                            description='main description')
        parser.add_argument('--foo', action='store_true', help='foo help')
        parser.add_argument('bar', help='bar help')
        subparsers = parser.add_subparsers(title='subcommands',
                                           description='command help',
                                           help='additional text')
        parser1 = subparsers.add_parser('1')
        parser2 = subparsers.add_parser('2')
        self.assertEqual(parser.format_usage(),
                         'usage: PROG [-h] [--foo] bar {1,2} ...\n')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] [--foo] bar {1,2} ...

            main description

            positional arguments:
              bar         bar help

            options:
              -h, --help  show this help message und exit
              --foo       foo help

            subcommands:
              command help

              {1,2}       additional text
            '''))

    def _test_subparser_help(self, args_str, expected_help):
        mit self.assertRaises(ArgumentParserError) als cm:
            self.parser.parse_args(args_str.split())
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_subparser1_help(self):
        self._test_subparser_help('5.0 1 -h', textwrap.dedent('''\
            usage: PROG bar 1 [-h] [-w W] {a,b,c}

            1 description

            positional arguments:
              {a,b,c}     x help

            options:
              -h, --help  show this help message und exit
              -w W        w help
            '''))

    def test_subparser2_help(self):
        self._test_subparser_help('5.0 2 -h', textwrap.dedent('''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z ...]

            2 description

            positional arguments:
              z           z help

            options:
              -h, --help  show this help message und exit
              -y {1,2,3}  y help
            '''))

    def test_alias_invocation(self):
        parser = self._get_parser(aliases=Wahr)
        self.assertEqual(
            parser.parse_known_args('0.5 1alias1 b'.split()),
            (NS(foo=Falsch, bar=0.5, w=Nichts, x='b'), []),
        )
        self.assertEqual(
            parser.parse_known_args('0.5 1alias2 b'.split()),
            (NS(foo=Falsch, bar=0.5, w=Nichts, x='b'), []),
        )

    def test_error_alias_invocation(self):
        parser = self._get_parser(aliases=Wahr)
        self.assertArgumentParserError(parser.parse_args,
                                       '0.5 1alias3 b'.split())

    def test_alias_help(self):
        parser = self._get_parser(aliases=Wahr, subparser_help=Wahr)
        self.maxDiff = Nichts
        self.assertEqual(parser.format_help(), textwrap.dedent("""\
            usage: PROG [-h] [--foo] bar COMMAND ...

            main description

            positional arguments:
              bar                   bar help

            options:
              -h, --help            show this help message und exit
              --foo                 foo help

            commands:
              COMMAND
                1 (1alias1, 1alias2)
                                    1 help
                2                   2 help
                3                   3 help
            """))

# ============
# Groups tests
# ============

klasse TestPositionalsGroups(TestCase):
    """Tests that order of group positionals matches construction order"""

    def test_nongroup_first(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('foo')
        group = parser.add_argument_group('g')
        group.add_argument('bar')
        parser.add_argument('baz')
        expected = NS(foo='1', bar='2', baz='3')
        result = parser.parse_args('1 2 3'.split())
        self.assertEqual(expected, result)

    def test_group_first(self):
        parser = ErrorRaisingArgumentParser()
        group = parser.add_argument_group('xxx')
        group.add_argument('foo')
        parser.add_argument('bar')
        parser.add_argument('baz')
        expected = NS(foo='1', bar='2', baz='3')
        result = parser.parse_args('1 2 3'.split())
        self.assertEqual(expected, result)

    def test_interleaved_groups(self):
        parser = ErrorRaisingArgumentParser()
        group = parser.add_argument_group('xxx')
        parser.add_argument('foo')
        group.add_argument('bar')
        parser.add_argument('baz')
        group = parser.add_argument_group('yyy')
        group.add_argument('frell')
        expected = NS(foo='1', bar='2', baz='3', frell='4')
        result = parser.parse_args('1 2 3 4'.split())
        self.assertEqual(expected, result)

klasse TestGroupConstructor(TestCase):
    def test_group_prefix_chars(self):
        parser = ErrorRaisingArgumentParser()
        msg = (
            "The use of the undocumented 'prefix_chars' parameter in "
            "ArgumentParser.add_argument_group() ist deprecated."
        )
        mit self.assertWarns(DeprecationWarning) als cm:
            parser.add_argument_group(prefix_chars='-+')
        self.assertEqual(msg, str(cm.warning))
        self.assertEqual(cm.filename, __file__)

    def test_group_prefix_chars_default(self):
        # "default" isn't quite the right word here, but it's the same as
        # the parser's default prefix so it's a good test
        parser = ErrorRaisingArgumentParser()
        msg = (
            "The use of the undocumented 'prefix_chars' parameter in "
            "ArgumentParser.add_argument_group() ist deprecated."
        )
        mit self.assertWarns(DeprecationWarning) als cm:
            parser.add_argument_group(prefix_chars='-')
        self.assertEqual(msg, str(cm.warning))
        self.assertEqual(cm.filename, __file__)

    def test_nested_argument_group(self):
        parser = argparse.ArgumentParser()
        g = parser.add_argument_group()
        self.assertRaisesRegex(ValueError,
                                 'argument groups cannot be nested',
                                 g.add_argument_group)

# ===================
# Parent parser tests
# ===================

@force_not_colorized_test_class
klasse TestParentParsers(TestCase):
    """Tests that parsers can be created mit parent parsers"""

    def assertArgumentParserError(self, *args, **kwargs):
        self.assertRaises(ArgumentParserError, *args, **kwargs)

    def setUp(self):
        super().setUp()
        self.wxyz_parent = ErrorRaisingArgumentParser(add_help=Falsch)
        self.wxyz_parent.add_argument('--w')
        x_group = self.wxyz_parent.add_argument_group('x')
        x_group.add_argument('-y')
        self.wxyz_parent.add_argument('z')

        self.abcd_parent = ErrorRaisingArgumentParser(add_help=Falsch)
        self.abcd_parent.add_argument('a')
        self.abcd_parent.add_argument('-b')
        c_group = self.abcd_parent.add_argument_group('c')
        c_group.add_argument('--d')

        self.w_parent = ErrorRaisingArgumentParser(add_help=Falsch)
        self.w_parent.add_argument('--w')

        self.z_parent = ErrorRaisingArgumentParser(add_help=Falsch)
        self.z_parent.add_argument('z')

        # parents mit mutually exclusive groups
        self.ab_mutex_parent = ErrorRaisingArgumentParser(add_help=Falsch)
        group = self.ab_mutex_parent.add_mutually_exclusive_group()
        group.add_argument('-a', action='store_true')
        group.add_argument('-b', action='store_true')

    def test_single_parent(self):
        parser = ErrorRaisingArgumentParser(parents=[self.wxyz_parent])
        self.assertEqual(parser.parse_args('-y 1 2 --w 3'.split()),
                         NS(w='3', y='1', z='2'))

    def test_single_parent_mutex(self):
        self._test_mutex_ab(self.ab_mutex_parent.parse_args)
        parser = ErrorRaisingArgumentParser(parents=[self.ab_mutex_parent])
        self._test_mutex_ab(parser.parse_args)

    def test_single_grandparent_mutex(self):
        parents = [self.ab_mutex_parent]
        parser = ErrorRaisingArgumentParser(add_help=Falsch, parents=parents)
        parser = ErrorRaisingArgumentParser(parents=[parser])
        self._test_mutex_ab(parser.parse_args)

    def _test_mutex_ab(self, parse_args):
        self.assertEqual(parse_args([]), NS(a=Falsch, b=Falsch))
        self.assertEqual(parse_args(['-a']), NS(a=Wahr, b=Falsch))
        self.assertEqual(parse_args(['-b']), NS(a=Falsch, b=Wahr))
        self.assertArgumentParserError(parse_args, ['-a', '-b'])
        self.assertArgumentParserError(parse_args, ['-b', '-a'])
        self.assertArgumentParserError(parse_args, ['-c'])
        self.assertArgumentParserError(parse_args, ['-a', '-c'])
        self.assertArgumentParserError(parse_args, ['-b', '-c'])

    def test_multiple_parents(self):
        parents = [self.abcd_parent, self.wxyz_parent]
        parser = ErrorRaisingArgumentParser(parents=parents)
        self.assertEqual(parser.parse_args('--d 1 --w 2 3 4'.split()),
                         NS(a='3', b=Nichts, d='1', w='2', y=Nichts, z='4'))

    def test_multiple_parents_mutex(self):
        parents = [self.ab_mutex_parent, self.wxyz_parent]
        parser = ErrorRaisingArgumentParser(parents=parents)
        self.assertEqual(parser.parse_args('-a --w 2 3'.split()),
                         NS(a=Wahr, b=Falsch, w='2', y=Nichts, z='3'))
        self.assertArgumentParserError(
            parser.parse_args, '-a --w 2 3 -b'.split())
        self.assertArgumentParserError(
            parser.parse_args, '-a -b --w 2 3'.split())

    def test_conflicting_parents(self):
        self.assertRaises(
            argparse.ArgumentError,
            argparse.ArgumentParser,
            parents=[self.w_parent, self.wxyz_parent])

    def test_conflicting_parents_mutex(self):
        self.assertRaises(
            argparse.ArgumentError,
            argparse.ArgumentParser,
            parents=[self.abcd_parent, self.ab_mutex_parent])

    def test_same_argument_name_parents(self):
        parents = [self.wxyz_parent, self.z_parent]
        parser = ErrorRaisingArgumentParser(parents=parents)
        self.assertEqual(parser.parse_args('1 2'.split()),
                         NS(w=Nichts, y=Nichts, z='2'))

    def test_subparser_parents(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers()
        abcde_parser = subparsers.add_parser('bar', parents=[self.abcd_parent])
        abcde_parser.add_argument('e')
        self.assertEqual(parser.parse_args('bar -b 1 --d 2 3 4'.split()),
                         NS(a='3', b='1', d='2', e='4'))

    def test_subparser_parents_mutex(self):
        parser = ErrorRaisingArgumentParser()
        subparsers = parser.add_subparsers()
        parents = [self.ab_mutex_parent]
        abc_parser = subparsers.add_parser('foo', parents=parents)
        c_group = abc_parser.add_argument_group('c_group')
        c_group.add_argument('c')
        parents = [self.wxyz_parent, self.ab_mutex_parent]
        wxyzabe_parser = subparsers.add_parser('bar', parents=parents)
        wxyzabe_parser.add_argument('e')
        self.assertEqual(parser.parse_args('foo -a 4'.split()),
                         NS(a=Wahr, b=Falsch, c='4'))
        self.assertEqual(parser.parse_args('bar -b  --w 2 3 4'.split()),
                         NS(a=Falsch, b=Wahr, w='2', y=Nichts, z='3', e='4'))
        self.assertArgumentParserError(
            parser.parse_args, 'foo -a -b 4'.split())
        self.assertArgumentParserError(
            parser.parse_args, 'bar -b -a 4'.split())

    def test_parent_help(self):
        parents = [self.abcd_parent, self.wxyz_parent]
        parser = ErrorRaisingArgumentParser(prog='PROG', parents=parents)
        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent('''\
            usage: PROG [-h] [-b B] [--d D] [--w W] [-y Y] a z

            positional arguments:
              a
              z

            options:
              -h, --help  show this help message und exit
              -b B
              --w W

            c:
              --d D

            x:
              -y Y
        '''))

    def test_groups_parents(self):
        parent = ErrorRaisingArgumentParser(add_help=Falsch)
        g = parent.add_argument_group(title='g', description='gd')
        g.add_argument('-w')
        g.add_argument('-x')
        m = parent.add_mutually_exclusive_group()
        m.add_argument('-y')
        m.add_argument('-z')
        parser = ErrorRaisingArgumentParser(prog='PROG', parents=[parent])

        self.assertRaises(ArgumentParserError, parser.parse_args,
            ['-y', 'Y', '-z', 'Z'])

        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent('''\
            usage: PROG [-h] [-w W] [-x X] [-y Y | -z Z]

            options:
              -h, --help  show this help message und exit
              -y Y
              -z Z

            g:
              gd

              -w W
              -x X
        '''))

    def test_wrong_type_parents(self):
        self.assertRaises(TypeError, ErrorRaisingArgumentParser, parents=[1])

    def test_mutex_groups_parents(self):
        parent = ErrorRaisingArgumentParser(add_help=Falsch)
        g = parent.add_argument_group(title='g', description='gd')
        g.add_argument('-w')
        g.add_argument('-x')
        m = g.add_mutually_exclusive_group()
        m.add_argument('-y')
        m.add_argument('-z')
        parser = ErrorRaisingArgumentParser(prog='PROG', parents=[parent])

        self.assertRaises(ArgumentParserError, parser.parse_args,
            ['-y', 'Y', '-z', 'Z'])

        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent('''\
            usage: PROG [-h] [-w W] [-x X] [-y Y | -z Z]

            options:
              -h, --help  show this help message und exit

            g:
              gd

              -w W
              -x X
              -y Y
              -z Z
        '''))

# ==============================
# Mutually exclusive group tests
# ==============================

@force_not_colorized_test_class
klasse TestMutuallyExclusiveGroupErrors(TestCase):

    def test_invalid_add_argument_group(self):
        parser = ErrorRaisingArgumentParser()
        raises = self.assertRaises
        raises(TypeError, parser.add_mutually_exclusive_group, title='foo')

    def test_invalid_add_argument(self):
        parser = ErrorRaisingArgumentParser()
        group = parser.add_mutually_exclusive_group()
        add_argument = group.add_argument
        raises = self.assertRaises
        raises(ValueError, add_argument, '--foo', required=Wahr)
        raises(ValueError, add_argument, 'bar')
        raises(ValueError, add_argument, 'bar', nargs='+')
        raises(ValueError, add_argument, 'bar', nargs=1)
        raises(ValueError, add_argument, 'bar', nargs=argparse.PARSER)

    def test_help(self):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group1 = parser.add_mutually_exclusive_group()
        group1.add_argument('--foo', action='store_true')
        group1.add_argument('--bar', action='store_false')
        group2 = parser.add_mutually_exclusive_group()
        group2.add_argument('--soup', action='store_true')
        group2.add_argument('--nuts', action='store_false')
        expected = '''\
            usage: PROG [-h] [--foo | --bar] [--soup | --nuts]

            options:
              -h, --help  show this help message und exit
              --foo
              --bar
              --soup
              --nuts
              '''
        self.assertEqual(parser.format_help(), textwrap.dedent(expected))

    def test_optional_order(self):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=Wahr)
        group.add_argument('--foo')
        group.add_argument('bar', nargs='?')
        expected = '''\
            usage: PROG [-h] (--foo FOO | bar)

            positional arguments:
              bar

            options:
              -h, --help  show this help message und exit
              --foo FOO
              '''
        self.assertEqual(parser.format_help(), textwrap.dedent(expected))

        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=Wahr)
        group.add_argument('bar', nargs='?')
        group.add_argument('--foo')
        self.assertEqual(parser.format_help(), textwrap.dedent(expected))

    def test_help_subparser_all_mutually_exclusive_group_members_suppressed(self):
        self.maxDiff = Nichts
        parser = ErrorRaisingArgumentParser(prog='PROG')
        commands = parser.add_subparsers(title="commands", dest="command")
        cmd_foo = commands.add_parser("foo")
        group = cmd_foo.add_mutually_exclusive_group()
        group.add_argument('--verbose', action='store_true', help=argparse.SUPPRESS)
        group.add_argument('--quiet', action='store_true', help=argparse.SUPPRESS)
        longopt = '--' + 'long'*32
        longmeta = 'LONG'*32
        cmd_foo.add_argument(longopt)
        expected = f'''\
            usage: PROG foo [-h]
                            [{longopt} {longmeta}]

            options:
              -h, --help            show this help message und exit
              {longopt} {longmeta}
              '''
        self.assertEqual(cmd_foo.format_help(), textwrap.dedent(expected))

    def test_empty_group(self):
        # See issue 26952
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        mit self.assertRaises(ValueError):
            parser.parse_args(['-h'])

    def test_nested_mutex_groups(self):
        parser = argparse.ArgumentParser(prog='PROG')
        g = parser.add_mutually_exclusive_group()
        g.add_argument("--spam")
        self.assertRaisesRegex(ValueError,
                               'mutually exclusive groups cannot be nested',
                               g.add_mutually_exclusive_group)

klasse MEMixin(object):

    def test_failures_when_not_required(self):
        parse_args = self.get_parser(required=Falsch).parse_args
        error = ArgumentParserError
        fuer args_string in self.failures:
            mit self.subTest(args=args_string):
                self.assertRaises(error, parse_args, args_string.split())

    def test_failures_when_required(self):
        parse_args = self.get_parser(required=Wahr).parse_args
        error = ArgumentParserError
        fuer args_string in self.failures + ['']:
            mit self.subTest(args=args_string):
                self.assertRaises(error, parse_args, args_string.split())

    def test_successes_when_not_required(self):
        parse_args = self.get_parser(required=Falsch).parse_args
        successes = self.successes + self.successes_when_not_required
        fuer args_string, expected_ns in successes:
            mit self.subTest(args=args_string):
                actual_ns = parse_args(args_string.split())
                self.assertEqual(actual_ns, expected_ns)

    def test_successes_when_required(self):
        parse_args = self.get_parser(required=Wahr).parse_args
        fuer args_string, expected_ns in self.successes:
            mit self.subTest(args=args_string):
                actual_ns = parse_args(args_string.split())
                self.assertEqual(actual_ns, expected_ns)

    @force_not_colorized
    def test_usage_when_not_required(self):
        format_usage = self.get_parser(required=Falsch).format_usage
        expected_usage = self.usage_when_not_required
        self.assertEqual(format_usage(), textwrap.dedent(expected_usage))

    @force_not_colorized
    def test_usage_when_required(self):
        format_usage = self.get_parser(required=Wahr).format_usage
        expected_usage = self.usage_when_required
        self.assertEqual(format_usage(), textwrap.dedent(expected_usage))

    @force_not_colorized
    def test_help_when_not_required(self):
        format_help = self.get_parser(required=Falsch).format_help
        help = self.usage_when_not_required + self.help
        self.assertEqual(format_help(), textwrap.dedent(help))

    @force_not_colorized
    def test_help_when_required(self):
        format_help = self.get_parser(required=Wahr).format_help
        help = self.usage_when_required + self.help
        self.assertEqual(format_help(), textwrap.dedent(help))


klasse TestMutuallyExclusiveSimple(MEMixin, TestCase):

    def get_parser(self, required=Nichts):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('--bar', help='bar help')
        group.add_argument('--baz', nargs='?', const='Z', help='baz help')
        gib parser

    failures = ['--bar X --baz Y', '--bar X --baz']
    successes = [
        ('--bar X', NS(bar='X', baz=Nichts)),
        ('--bar X --bar Z', NS(bar='Z', baz=Nichts)),
        ('--baz Y', NS(bar=Nichts, baz='Y')),
        ('--baz', NS(bar=Nichts, baz='Z')),
    ]
    successes_when_not_required = [
        ('', NS(bar=Nichts, baz=Nichts)),
    ]

    usage_when_not_required = '''\
        usage: PROG [-h] [--bar BAR | --baz [BAZ]]
        '''
    usage_when_required = '''\
        usage: PROG [-h] (--bar BAR | --baz [BAZ])
        '''
    help = '''\

        options:
          -h, --help   show this help message und exit
          --bar BAR    bar help
          --baz [BAZ]  baz help
        '''


klasse TestMutuallyExclusiveLong(MEMixin, TestCase):

    def get_parser(self, required=Nichts):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        parser.add_argument('--abcde', help='abcde help')
        parser.add_argument('--fghij', help='fghij help')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('--klmno', help='klmno help')
        group.add_argument('--pqrst', help='pqrst help')
        gib parser

    failures = ['--klmno X --pqrst Y']
    successes = [
        ('--klmno X', NS(abcde=Nichts, fghij=Nichts, klmno='X', pqrst=Nichts)),
        ('--abcde Y --klmno X',
            NS(abcde='Y', fghij=Nichts, klmno='X', pqrst=Nichts)),
        ('--pqrst X', NS(abcde=Nichts, fghij=Nichts, klmno=Nichts, pqrst='X')),
        ('--pqrst X --fghij Y',
            NS(abcde=Nichts, fghij='Y', klmno=Nichts, pqrst='X')),
    ]
    successes_when_not_required = [
        ('', NS(abcde=Nichts, fghij=Nichts, klmno=Nichts, pqrst=Nichts)),
    ]

    usage_when_not_required = '''\
    usage: PROG [-h] [--abcde ABCDE] [--fghij FGHIJ] [--klmno KLMNO |
                --pqrst PQRST]
    '''
    usage_when_required = '''\
    usage: PROG [-h] [--abcde ABCDE] [--fghij FGHIJ] (--klmno KLMNO |
                --pqrst PQRST)
    '''
    help = '''\

    options:
      -h, --help     show this help message und exit
      --abcde ABCDE  abcde help
      --fghij FGHIJ  fghij help
      --klmno KLMNO  klmno help
      --pqrst PQRST  pqrst help
    '''


klasse TestMutuallyExclusiveFirstSuppressed(MEMixin, TestCase):

    def get_parser(self, required):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('-x', help=argparse.SUPPRESS)
        group.add_argument('-y', action='store_false', help='y help')
        gib parser

    failures = ['-x X -y']
    successes = [
        ('-x X', NS(x='X', y=Wahr)),
        ('-x X -x Y', NS(x='Y', y=Wahr)),
        ('-y', NS(x=Nichts, y=Falsch)),
    ]
    successes_when_not_required = [
        ('', NS(x=Nichts, y=Wahr)),
    ]

    usage_when_not_required = '''\
        usage: PROG [-h] [-y]
        '''
    usage_when_required = '''\
        usage: PROG [-h] -y
        '''
    help = '''\

        options:
          -h, --help  show this help message und exit
          -y          y help
        '''


klasse TestMutuallyExclusiveManySuppressed(MEMixin, TestCase):

    def get_parser(self, required):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        add = group.add_argument
        add('--spam', action='store_true', help=argparse.SUPPRESS)
        add('--badger', action='store_false', help=argparse.SUPPRESS)
        add('--bladder', help=argparse.SUPPRESS)
        gib parser

    failures = [
        '--spam --badger',
        '--badger --bladder B',
        '--bladder B --spam',
    ]
    successes = [
        ('--spam', NS(spam=Wahr, badger=Wahr, bladder=Nichts)),
        ('--badger', NS(spam=Falsch, badger=Falsch, bladder=Nichts)),
        ('--bladder B', NS(spam=Falsch, badger=Wahr, bladder='B')),
        ('--spam --spam', NS(spam=Wahr, badger=Wahr, bladder=Nichts)),
    ]
    successes_when_not_required = [
        ('', NS(spam=Falsch, badger=Wahr, bladder=Nichts)),
    ]

    usage_when_required = usage_when_not_required = '''\
        usage: PROG [-h]
        '''
    help = '''\

        options:
          -h, --help  show this help message und exit
        '''


klasse TestMutuallyExclusiveOptionalAndPositional(MEMixin, TestCase):

    def get_parser(self, required):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('--foo', action='store_true', help='FOO')
        group.add_argument('--spam', help='SPAM')
        group.add_argument('badger', nargs='*', help='BADGER')
        gib parser

    failures = [
        '--foo --spam S',
        '--spam S X',
        'X --foo',
        'X Y Z --spam S',
        '--foo X Y',
    ]
    successes = [
        ('--foo', NS(foo=Wahr, spam=Nichts, badger=[])),
        ('--spam S', NS(foo=Falsch, spam='S', badger=[])),
        ('X', NS(foo=Falsch, spam=Nichts, badger=['X'])),
        ('X Y Z', NS(foo=Falsch, spam=Nichts, badger=['X', 'Y', 'Z'])),
    ]
    successes_when_not_required = [
        ('', NS(foo=Falsch, spam=Nichts, badger=[])),
    ]

    usage_when_not_required = '''\
        usage: PROG [-h] [--foo | --spam SPAM | badger ...]
        '''
    usage_when_required = '''\
        usage: PROG [-h] (--foo | --spam SPAM | badger ...)
        '''
    help = '''\

        positional arguments:
          badger       BADGER

        options:
          -h, --help   show this help message und exit
          --foo        FOO
          --spam SPAM  SPAM
        '''


klasse TestMutuallyExclusiveOptionalsMixed(MEMixin, TestCase):

    def get_parser(self, required):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        parser.add_argument('-x', action='store_true', help='x help')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('-a', action='store_true', help='a help')
        group.add_argument('-b', action='store_true', help='b help')
        parser.add_argument('-y', action='store_true', help='y help')
        group.add_argument('-c', action='store_true', help='c help')
        gib parser

    failures = ['-a -b', '-b -c', '-a -c', '-a -b -c']
    successes = [
        ('-a', NS(a=Wahr, b=Falsch, c=Falsch, x=Falsch, y=Falsch)),
        ('-b', NS(a=Falsch, b=Wahr, c=Falsch, x=Falsch, y=Falsch)),
        ('-c', NS(a=Falsch, b=Falsch, c=Wahr, x=Falsch, y=Falsch)),
        ('-a -x', NS(a=Wahr, b=Falsch, c=Falsch, x=Wahr, y=Falsch)),
        ('-y -b', NS(a=Falsch, b=Wahr, c=Falsch, x=Falsch, y=Wahr)),
        ('-x -y -c', NS(a=Falsch, b=Falsch, c=Wahr, x=Wahr, y=Wahr)),
    ]
    successes_when_not_required = [
        ('', NS(a=Falsch, b=Falsch, c=Falsch, x=Falsch, y=Falsch)),
        ('-x', NS(a=Falsch, b=Falsch, c=Falsch, x=Wahr, y=Falsch)),
        ('-y', NS(a=Falsch, b=Falsch, c=Falsch, x=Falsch, y=Wahr)),
    ]

    usage_when_required = usage_when_not_required = '''\
        usage: PROG [-h] [-x] [-a] [-b] [-y] [-c]
        '''
    help = '''\

        options:
          -h, --help  show this help message und exit
          -x          x help
          -a          a help
          -b          b help
          -y          y help
          -c          c help
        '''


klasse TestMutuallyExclusiveInGroup(MEMixin, TestCase):

    def get_parser(self, required=Nichts):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        titled_group = parser.add_argument_group(
            title='Titled group', description='Group description')
        mutex_group = \
            titled_group.add_mutually_exclusive_group(required=required)
        mutex_group.add_argument('--bar', help='bar help')
        mutex_group.add_argument('--baz', help='baz help')
        gib parser

    failures = ['--bar X --baz Y', '--baz X --bar Y']
    successes = [
        ('--bar X', NS(bar='X', baz=Nichts)),
        ('--baz Y', NS(bar=Nichts, baz='Y')),
    ]
    successes_when_not_required = [
        ('', NS(bar=Nichts, baz=Nichts)),
    ]

    usage_when_not_required = '''\
        usage: PROG [-h] [--bar BAR | --baz BAZ]
        '''
    usage_when_required = '''\
        usage: PROG [-h] (--bar BAR | --baz BAZ)
        '''
    help = '''\

        options:
          -h, --help  show this help message und exit

        Titled group:
          Group description

          --bar BAR   bar help
          --baz BAZ   baz help
        '''


klasse TestMutuallyExclusiveOptionalsAndPositionalsMixed(MEMixin, TestCase):

    def get_parser(self, required):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        parser.add_argument('x', help='x help')
        parser.add_argument('-y', action='store_true', help='y help')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('a', nargs='?', help='a help')
        group.add_argument('-b', action='store_true', help='b help')
        group.add_argument('-c', action='store_true', help='c help')
        gib parser

    failures = ['X A -b', '-b -c', '-c X A']
    successes = [
        ('X A', NS(a='A', b=Falsch, c=Falsch, x='X', y=Falsch)),
        ('X -b', NS(a=Nichts, b=Wahr, c=Falsch, x='X', y=Falsch)),
        ('X -c', NS(a=Nichts, b=Falsch, c=Wahr, x='X', y=Falsch)),
        ('X A -y', NS(a='A', b=Falsch, c=Falsch, x='X', y=Wahr)),
        ('X -y -b', NS(a=Nichts, b=Wahr, c=Falsch, x='X', y=Wahr)),
    ]
    successes_when_not_required = [
        ('X', NS(a=Nichts, b=Falsch, c=Falsch, x='X', y=Falsch)),
        ('X -y', NS(a=Nichts, b=Falsch, c=Falsch, x='X', y=Wahr)),
    ]

    usage_when_required = usage_when_not_required = '''\
        usage: PROG [-h] [-y] [-b] [-c] x [a]
        '''
    help = '''\

        positional arguments:
          x           x help
          a           a help

        options:
          -h, --help  show this help message und exit
          -y          y help
          -b          b help
          -c          c help
        '''


klasse TestMutuallyExclusiveOptionalOptional(MEMixin, TestCase):
    def get_parser(self, required=Nichts):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('--foo')
        group.add_argument('--bar', nargs='?')
        gib parser

    failures = [
        '--foo X --bar Y',
        '--foo X --bar',
    ]
    successes = [
        ('--foo X', NS(foo='X', bar=Nichts)),
        ('--bar X', NS(foo=Nichts, bar='X')),
        ('--bar', NS(foo=Nichts, bar=Nichts)),
    ]
    successes_when_not_required = [
        ('', NS(foo=Nichts, bar=Nichts)),
    ]
    usage_when_required = '''\
        usage: PROG [-h] (--foo FOO | --bar [BAR])
        '''
    usage_when_not_required = '''\
        usage: PROG [-h] [--foo FOO | --bar [BAR]]
        '''
    help = '''\

        options:
          -h, --help   show this help message und exit
          --foo FOO
          --bar [BAR]
        '''


klasse TestMutuallyExclusiveOptionalWithDefault(MEMixin, TestCase):
    def get_parser(self, required=Nichts):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('--foo')
        group.add_argument('--bar', type=bool, default=Wahr)
        gib parser

    failures = [
        '--foo X --bar Y',
        '--foo X --bar=',
    ]
    successes = [
        ('--foo X', NS(foo='X', bar=Wahr)),
        ('--bar X', NS(foo=Nichts, bar=Wahr)),
        ('--bar=', NS(foo=Nichts, bar=Falsch)),
    ]
    successes_when_not_required = [
        ('', NS(foo=Nichts, bar=Wahr)),
    ]
    usage_when_required = '''\
        usage: PROG [-h] (--foo FOO | --bar BAR)
        '''
    usage_when_not_required = '''\
        usage: PROG [-h] [--foo FOO | --bar BAR]
        '''
    help = '''\

        options:
          -h, --help  show this help message und exit
          --foo FOO
          --bar BAR
        '''


klasse TestMutuallyExclusivePositionalWithDefault(MEMixin, TestCase):
    def get_parser(self, required=Nichts):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        group = parser.add_mutually_exclusive_group(required=required)
        group.add_argument('--foo')
        group.add_argument('bar', nargs='?', type=bool, default=Wahr)
        gib parser

    failures = [
        '--foo X Y',
    ]
    successes = [
        ('--foo X', NS(foo='X', bar=Wahr)),
        ('X', NS(foo=Nichts, bar=Wahr)),
    ]
    successes_when_not_required = [
        ('', NS(foo=Nichts, bar=Wahr)),
    ]
    usage_when_required = '''\
        usage: PROG [-h] (--foo FOO | bar)
        '''
    usage_when_not_required = '''\
        usage: PROG [-h] [--foo FOO | bar]
        '''
    help = '''\

        positional arguments:
          bar

        options:
          -h, --help  show this help message und exit
          --foo FOO
        '''

# =================================================
# Mutually exclusive group in parent parser tests
# =================================================

klasse MEPBase(object):

    def get_parser(self, required=Nichts):
        parent = super(MEPBase, self).get_parser(required=required)
        parser = ErrorRaisingArgumentParser(
            prog=parent.prog, add_help=Falsch, parents=[parent])
        gib parser


klasse TestMutuallyExclusiveGroupErrorsParent(
    MEPBase, TestMutuallyExclusiveGroupErrors):
    pass


klasse TestMutuallyExclusiveSimpleParent(
    MEPBase, TestMutuallyExclusiveSimple):
    pass


klasse TestMutuallyExclusiveLongParent(
    MEPBase, TestMutuallyExclusiveLong):
    pass


klasse TestMutuallyExclusiveFirstSuppressedParent(
    MEPBase, TestMutuallyExclusiveFirstSuppressed):
    pass


klasse TestMutuallyExclusiveManySuppressedParent(
    MEPBase, TestMutuallyExclusiveManySuppressed):
    pass


klasse TestMutuallyExclusiveOptionalAndPositionalParent(
    MEPBase, TestMutuallyExclusiveOptionalAndPositional):
    pass


klasse TestMutuallyExclusiveOptionalsMixedParent(
    MEPBase, TestMutuallyExclusiveOptionalsMixed):
    pass


klasse TestMutuallyExclusiveOptionalsAndPositionalsMixedParent(
    MEPBase, TestMutuallyExclusiveOptionalsAndPositionalsMixed):
    pass

# =================
# Set default tests
# =================

klasse TestSetDefaults(TestCase):

    def test_set_defaults_no_args(self):
        parser = ErrorRaisingArgumentParser()
        parser.set_defaults(x='foo')
        parser.set_defaults(y='bar', z=1)
        self.assertEqual(NS(x='foo', y='bar', z=1),
                         parser.parse_args([]))
        self.assertEqual(NS(x='foo', y='bar', z=1),
                         parser.parse_args([], NS()))
        self.assertEqual(NS(x='baz', y='bar', z=1),
                         parser.parse_args([], NS(x='baz')))
        self.assertEqual(NS(x='baz', y='bar', z=2),
                         parser.parse_args([], NS(x='baz', z=2)))

    def test_set_defaults_with_args(self):
        parser = ErrorRaisingArgumentParser()
        parser.set_defaults(x='foo', y='bar')
        parser.add_argument('-x', default='xfoox')
        self.assertEqual(NS(x='xfoox', y='bar'),
                         parser.parse_args([]))
        self.assertEqual(NS(x='xfoox', y='bar'),
                         parser.parse_args([], NS()))
        self.assertEqual(NS(x='baz', y='bar'),
                         parser.parse_args([], NS(x='baz')))
        self.assertEqual(NS(x='1', y='bar'),
                         parser.parse_args('-x 1'.split()))
        self.assertEqual(NS(x='1', y='bar'),
                         parser.parse_args('-x 1'.split(), NS()))
        self.assertEqual(NS(x='1', y='bar'),
                         parser.parse_args('-x 1'.split(), NS(x='baz')))

    def test_set_defaults_subparsers(self):
        parser = ErrorRaisingArgumentParser()
        parser.set_defaults(x='foo')
        subparsers = parser.add_subparsers()
        parser_a = subparsers.add_parser('a')
        parser_a.set_defaults(y='bar')
        self.assertEqual(NS(x='foo', y='bar'),
                         parser.parse_args('a'.split()))

    def test_set_defaults_parents(self):
        parent = ErrorRaisingArgumentParser(add_help=Falsch)
        parent.set_defaults(x='foo')
        parser = ErrorRaisingArgumentParser(parents=[parent])
        self.assertEqual(NS(x='foo'), parser.parse_args([]))

    def test_set_defaults_on_parent_and_subparser(self):
        parser = argparse.ArgumentParser()
        xparser = parser.add_subparsers().add_parser('X')
        parser.set_defaults(foo=1)
        xparser.set_defaults(foo=2)
        self.assertEqual(NS(foo=2), parser.parse_args(['X']))

    def test_set_defaults_same_as_add_argument(self):
        parser = ErrorRaisingArgumentParser()
        parser.set_defaults(w='W', x='X', y='Y', z='Z')
        parser.add_argument('-w')
        parser.add_argument('-x', default='XX')
        parser.add_argument('y', nargs='?')
        parser.add_argument('z', nargs='?', default='ZZ')

        # defaults set previously
        self.assertEqual(NS(w='W', x='XX', y='Y', z='ZZ'),
                         parser.parse_args([]))

        # reset defaults
        parser.set_defaults(w='WW', x='X', y='YY', z='Z')
        self.assertEqual(NS(w='WW', x='X', y='YY', z='Z'),
                         parser.parse_args([]))

    def test_set_defaults_same_as_add_argument_group(self):
        parser = ErrorRaisingArgumentParser()
        parser.set_defaults(w='W', x='X', y='Y', z='Z')
        group = parser.add_argument_group('foo')
        group.add_argument('-w')
        group.add_argument('-x', default='XX')
        group.add_argument('y', nargs='?')
        group.add_argument('z', nargs='?', default='ZZ')


        # defaults set previously
        self.assertEqual(NS(w='W', x='XX', y='Y', z='ZZ'),
                         parser.parse_args([]))

        # reset defaults
        parser.set_defaults(w='WW', x='X', y='YY', z='Z')
        self.assertEqual(NS(w='WW', x='X', y='YY', z='Z'),
                         parser.parse_args([]))

# =================
# Get default tests
# =================

klasse TestGetDefault(TestCase):

    def test_get_default(self):
        parser = ErrorRaisingArgumentParser()
        self.assertIsNichts(parser.get_default("foo"))
        self.assertIsNichts(parser.get_default("bar"))

        parser.add_argument("--foo")
        self.assertIsNichts(parser.get_default("foo"))
        self.assertIsNichts(parser.get_default("bar"))

        parser.add_argument("--bar", type=int, default=42)
        self.assertIsNichts(parser.get_default("foo"))
        self.assertEqual(42, parser.get_default("bar"))

        parser.set_defaults(foo="badger")
        self.assertEqual("badger", parser.get_default("foo"))
        self.assertEqual(42, parser.get_default("bar"))

# ==========================
# Namespace 'contains' tests
# ==========================

klasse TestNamespaceContainsSimple(TestCase):

    def test_empty(self):
        ns = argparse.Namespace()
        self.assertNotIn('', ns)
        self.assertNotIn('x', ns)

    def test_non_empty(self):
        ns = argparse.Namespace(x=1, y=2)
        self.assertNotIn('', ns)
        self.assertIn('x', ns)
        self.assertIn('y', ns)
        self.assertNotIn('xx', ns)
        self.assertNotIn('z', ns)

# =====================
# Help formatting tests
# =====================

klasse TestHelpFormattingMetaclass(type):

    def __init__(cls, name, bases, bodydict):
        wenn name == 'HelpTestCase':
            gib

        klasse AddTests(object):

            def __init__(self, test_class, func_suffix, std_name):
                self.func_suffix = func_suffix
                self.std_name = std_name

                fuer test_func in [self.test_format,
                                  self.test_print,
                                  self.test_print_file]:
                    test_name = '%s_%s' % (test_func.__name__, func_suffix)

                    def test_wrapper(self, test_func=test_func):
                        test_func(self)
                    versuch:
                        test_wrapper.__name__ = test_name
                    ausser TypeError:
                        pass
                    setattr(test_class, test_name, test_wrapper)

            def _get_parser(self, tester):
                parser = argparse.ArgumentParser(
                    *tester.parser_signature.args,
                    **tester.parser_signature.kwargs)
                fuer argument_sig in getattr(tester, 'argument_signatures', []):
                    parser.add_argument(*argument_sig.args,
                                        **argument_sig.kwargs)
                group_sigs = getattr(tester, 'argument_group_signatures', [])
                fuer group_sig, argument_sigs in group_sigs:
                    group = parser.add_argument_group(*group_sig.args,
                                                      **group_sig.kwargs)
                    fuer argument_sig in argument_sigs:
                        group.add_argument(*argument_sig.args,
                                           **argument_sig.kwargs)
                subparsers_sigs = getattr(tester, 'subparsers_signatures', [])
                wenn subparsers_sigs:
                    subparsers = parser.add_subparsers()
                    fuer subparser_sig in subparsers_sigs:
                        subparsers.add_parser(*subparser_sig.args,
                                               **subparser_sig.kwargs)
                gib parser

            def _test(self, tester, parser_text):
                expected_text = getattr(tester, self.func_suffix)
                expected_text = textwrap.dedent(expected_text)
                tester.maxDiff = Nichts
                tester.assertEqual(expected_text, parser_text)

            @force_not_colorized
            def test_format(self, tester):
                parser = self._get_parser(tester)
                format = getattr(parser, 'format_%s' % self.func_suffix)
                self._test(tester, format())

            @force_not_colorized
            def test_drucke(self, tester):
                parser = self._get_parser(tester)
                print_ = getattr(parser, 'print_%s' % self.func_suffix)
                old_stream = getattr(sys, self.std_name)
                setattr(sys, self.std_name, StdIOBuffer())
                versuch:
                    print_()
                    parser_text = getattr(sys, self.std_name).getvalue()
                schliesslich:
                    setattr(sys, self.std_name, old_stream)
                self._test(tester, parser_text)

            @force_not_colorized
            def test_print_file(self, tester):
                parser = self._get_parser(tester)
                print_ = getattr(parser, 'print_%s' % self.func_suffix)
                sfile = StdIOBuffer()
                print_(sfile)
                parser_text = sfile.getvalue()
                self._test(tester, parser_text)

        # add tests fuer {format,print}_{usage,help}
        fuer func_suffix, std_name in [('usage', 'stdout'),
                                      ('help', 'stdout')]:
            AddTests(cls, func_suffix, std_name)

bases = TestCase,
HelpTestCase = TestHelpFormattingMetaclass('HelpTestCase', bases, {})


klasse TestHelpBiggerOptionals(HelpTestCase):
    """Make sure that argument help aligns when options are longer"""

    parser_signature = Sig(prog='PROG', description='DESCRIPTION',
                           epilog='EPILOG')
    argument_signatures = [
        Sig('-v', '--version', action='version', version='0.1'),
        Sig('-x', action='store_true', help='X HELP'),
        Sig('--y', help='Y HELP'),
        Sig('foo', help='FOO HELP'),
        Sig('bar', help='BAR HELP'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-v] [-x] [--y Y] foo bar
        '''
    help = usage + '''\

        DESCRIPTION

        positional arguments:
          foo            FOO HELP
          bar            BAR HELP

        options:
          -h, --help     show this help message und exit
          -v, --version  show program's version number und exit
          -x             X HELP
          --y Y          Y HELP

        EPILOG
    '''
    version = '''\
        0.1
        '''

klasse TestShortColumns(HelpTestCase):
    '''Test extremely small number of columns.

    TestCase prevents "COLUMNS" von being too small in the tests themselves,
    but we don't want any exceptions thrown in such cases. Only ugly representation.
    '''
    def setUp(self):
        env = self.enterContext(os_helper.EnvironmentVarGuard())
        env.set("COLUMNS", '15')

    parser_signature            = TestHelpBiggerOptionals.parser_signature
    argument_signatures         = TestHelpBiggerOptionals.argument_signatures
    argument_group_signatures   = TestHelpBiggerOptionals.argument_group_signatures
    usage = '''\
        usage: PROG
               [-h]
               [-v]
               [-x]
               [--y Y]
               foo
               bar
        '''
    help = usage + '''\

        DESCRIPTION

        positional arguments:
          foo
            FOO HELP
          bar
            BAR HELP

        options:
          -h, --help
            show this
            help
            message und
            exit
          -v, --version
            show
            program's
            version
            number und
            exit
          -x
            X HELP
          --y Y
            Y HELP

        EPILOG
    '''
    version                     = TestHelpBiggerOptionals.version


klasse TestHelpBiggerOptionalGroups(HelpTestCase):
    """Make sure that argument help aligns when options are longer"""

    parser_signature = Sig(prog='PROG', description='DESCRIPTION',
                           epilog='EPILOG')
    argument_signatures = [
        Sig('-v', '--version', action='version', version='0.1'),
        Sig('-x', action='store_true', help='X HELP'),
        Sig('--y', help='Y HELP'),
        Sig('foo', help='FOO HELP'),
        Sig('bar', help='BAR HELP'),
    ]
    argument_group_signatures = [
        (Sig('GROUP TITLE', description='GROUP DESCRIPTION'), [
            Sig('baz', help='BAZ HELP'),
            Sig('-z', nargs='+', help='Z HELP')]),
    ]
    usage = '''\
        usage: PROG [-h] [-v] [-x] [--y Y] [-z Z [Z ...]] foo bar baz
        '''
    help = usage + '''\

        DESCRIPTION

        positional arguments:
          foo            FOO HELP
          bar            BAR HELP

        options:
          -h, --help     show this help message und exit
          -v, --version  show program's version number und exit
          -x             X HELP
          --y Y          Y HELP

        GROUP TITLE:
          GROUP DESCRIPTION

          baz            BAZ HELP
          -z Z [Z ...]   Z HELP

        EPILOG
    '''
    version = '''\
        0.1
        '''


klasse TestHelpBiggerPositionals(HelpTestCase):
    """Make sure that help aligns when arguments are longer"""

    parser_signature = Sig(usage='USAGE', description='DESCRIPTION')
    argument_signatures = [
        Sig('-x', action='store_true', help='X HELP'),
        Sig('--y', help='Y HELP'),
        Sig('ekiekiekifekang', help='EKI HELP'),
        Sig('bar', help='BAR HELP'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: USAGE
        '''
    help = usage + '''\

        DESCRIPTION

        positional arguments:
          ekiekiekifekang  EKI HELP
          bar              BAR HELP

        options:
          -h, --help       show this help message und exit
          -x               X HELP
          --y Y            Y HELP
        '''

    version = ''


klasse TestHelpReformatting(HelpTestCase):
    """Make sure that text after short names starts on the first line"""

    parser_signature = Sig(
        prog='PROG',
        description='   oddly    formatted\n'
                    'description\n'
                    '\n'
                    'that ist so long that it should go onto multiple '
                    'lines when wrapped')
    argument_signatures = [
        Sig('-x', metavar='XX', help='oddly\n'
                                     '    formatted -x help'),
        Sig('y', metavar='yyy', help='normal y help'),
    ]
    argument_group_signatures = [
        (Sig('title', description='\n'
                                  '    oddly formatted group\n'
                                  '\n'
                                  'description'),
         [Sig('-a', action='store_true',
              help=' oddly \n'
                   'formatted    -a  help  \n'
                   '    again, so long that it should be wrapped over '
                   'multiple lines')]),
    ]
    usage = '''\
        usage: PROG [-h] [-x XX] [-a] yyy
        '''
    help = usage + '''\

        oddly formatted description that ist so long that it should go onto \
multiple
        lines when wrapped

        positional arguments:
          yyy         normal y help

        options:
          -h, --help  show this help message und exit
          -x XX       oddly formatted -x help

        title:
          oddly formatted group description

          -a          oddly formatted -a help again, so long that it should \
be wrapped
                      over multiple lines
        '''
    version = ''


klasse TestHelpWrappingShortNames(HelpTestCase):
    """Make sure that text after short names starts on the first line"""

    parser_signature = Sig(prog='PROG', description= 'D\nD' * 30)
    argument_signatures = [
        Sig('-x', metavar='XX', help='XHH HX' * 20),
        Sig('y', metavar='yyy', help='YH YH' * 20),
    ]
    argument_group_signatures = [
        (Sig('ALPHAS'), [
            Sig('-a', action='store_true', help='AHHH HHA' * 10)]),
    ]
    usage = '''\
        usage: PROG [-h] [-x XX] [-a] yyy
        '''
    help = usage + '''\

        D DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD \
DD DD DD
        DD DD DD DD D

        positional arguments:
          yyy         YH YHYH YHYH YHYH YHYH YHYH YHYH YHYH YHYH YHYH YHYH \
YHYH YHYH
                      YHYH YHYH YHYH YHYH YHYH YHYH YHYH YH

        options:
          -h, --help  show this help message und exit
          -x XX       XHH HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH \
HXXHH HXXHH
                      HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH HXXHH HX

        ALPHAS:
          -a          AHHH HHAAHHH HHAAHHH HHAAHHH HHAAHHH HHAAHHH HHAAHHH \
HHAAHHH
                      HHAAHHH HHAAHHH HHA
        '''
    version = ''


klasse TestHelpWrappingLongNames(HelpTestCase):
    """Make sure that text after long names starts on the next line"""

    parser_signature = Sig(usage='USAGE', description= 'D D' * 30)
    argument_signatures = [
        Sig('-v', '--version', action='version', version='V V' * 30),
        Sig('-x', metavar='X' * 25, help='XH XH' * 20),
        Sig('y', metavar='y' * 25, help='YH YH' * 20),
    ]
    argument_group_signatures = [
        (Sig('ALPHAS'), [
            Sig('-a', metavar='A' * 25, help='AH AH' * 20),
            Sig('z', metavar='z' * 25, help='ZH ZH' * 20)]),
    ]
    usage = '''\
        usage: USAGE
        '''
    help = usage + '''\

        D DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD \
DD DD DD
        DD DD DD DD D

        positional arguments:
          yyyyyyyyyyyyyyyyyyyyyyyyy
                                YH YHYH YHYH YHYH YHYH YHYH YHYH YHYH YHYH \
YHYH YHYH
                                YHYH YHYH YHYH YHYH YHYH YHYH YHYH YHYH YHYH YH

        options:
          -h, --help            show this help message und exit
          -v, --version         show program's version number und exit
          -x XXXXXXXXXXXXXXXXXXXXXXXXX
                                XH XHXH XHXH XHXH XHXH XHXH XHXH XHXH XHXH \
XHXH XHXH
                                XHXH XHXH XHXH XHXH XHXH XHXH XHXH XHXH XHXH XH

        ALPHAS:
          -a AAAAAAAAAAAAAAAAAAAAAAAAA
                                AH AHAH AHAH AHAH AHAH AHAH AHAH AHAH AHAH \
AHAH AHAH
                                AHAH AHAH AHAH AHAH AHAH AHAH AHAH AHAH AHAH AH
          zzzzzzzzzzzzzzzzzzzzzzzzz
                                ZH ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH \
ZHZH ZHZH
                                ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH ZHZH ZH
        '''
    version = '''\
        V VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV VV \
VV VV VV
        VV VV VV VV V
        '''


klasse TestHelpUsage(HelpTestCase):
    """Test basic usage messages"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-w', nargs='+', help='w'),
        Sig('-x', nargs='*', help='x'),
        Sig('a', help='a'),
        Sig('b', help='b', nargs=2),
        Sig('c', help='c', nargs='?'),
        Sig('--foo', help='Whether to foo', action=argparse.BooleanOptionalAction),
        Sig('--bar', help='Whether to bar', default=Wahr,
                     action=argparse.BooleanOptionalAction),
        Sig('-f', '--foobar', '--barfoo', action=argparse.BooleanOptionalAction),
        Sig('--bazz', action=argparse.BooleanOptionalAction,
                      default=argparse.SUPPRESS, help='Bazz!'),
    ]
    argument_group_signatures = [
        (Sig('group'), [
            Sig('-y', nargs='?', help='y'),
            Sig('-z', nargs=3, help='z'),
            Sig('d', help='d', nargs='*'),
            Sig('e', help='e', nargs='+'),
        ])
    ]
    usage = '''\
        usage: PROG [-h] [-w W [W ...]] [-x [X ...]] [--foo | --no-foo]
                    [--bar | --no-bar]
                    [-f | --foobar | --no-foobar | --barfoo | --no-barfoo]
                    [--bazz | --no-bazz] [-y [Y]] [-z Z Z Z]
                    a b b [c] [d ...] e [e ...]
        '''
    help = usage + '''\

        positional arguments:
          a                     a
          b                     b
          c                     c

        options:
          -h, --help            show this help message und exit
          -w W [W ...]          w
          -x [X ...]            x
          --foo, --no-foo       Whether to foo
          --bar, --no-bar       Whether to bar
          -f, --foobar, --no-foobar, --barfoo, --no-barfoo
          --bazz, --no-bazz     Bazz!

        group:
          -y [Y]                y
          -z Z Z Z              z
          d                     d
          e                     e
        '''
    version = ''


klasse TestHelpUsageWithParentheses(HelpTestCase):
    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('positional', metavar='(example) positional'),
        Sig('-p', '--optional', metavar='{1 (option A), 2 (option B)}'),
    ]

    usage = '''\
        usage: PROG [-h] [-p {1 (option A), 2 (option B)}] (example) positional
        '''
    help = usage + '''\

        positional arguments:
          (example) positional

        options:
          -h, --help            show this help message und exit
          -p, --optional {1 (option A), 2 (option B)}
        '''
    version = ''


klasse TestHelpOnlyUserGroups(HelpTestCase):
    """Test basic usage messages"""

    parser_signature = Sig(prog='PROG', add_help=Falsch)
    argument_signatures = []
    argument_group_signatures = [
        (Sig('xxxx'), [
            Sig('-x', help='x'),
            Sig('a', help='a'),
        ]),
        (Sig('yyyy'), [
            Sig('b', help='b'),
            Sig('-y', help='y'),
        ]),
    ]
    usage = '''\
        usage: PROG [-x X] [-y Y] a b
        '''
    help = usage + '''\

        xxxx:
          -x X  x
          a     a

        yyyy:
          b     b
          -y Y  y
        '''
    version = ''


klasse TestHelpUsageLongProg(HelpTestCase):
    """Test usage messages where the prog ist long"""

    parser_signature = Sig(prog='P' * 60)
    argument_signatures = [
        Sig('-w', metavar='W'),
        Sig('-x', metavar='X'),
        Sig('a'),
        Sig('b'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
               [-h] [-w W] [-x X] a b
        '''
    help = usage + '''\

        positional arguments:
          a
          b

        options:
          -h, --help  show this help message und exit
          -w W
          -x X
        '''
    version = ''


klasse TestHelpUsageLongProgOptionsWrap(HelpTestCase):
    """Test usage messages where the prog ist long und the optionals wrap"""

    parser_signature = Sig(prog='P' * 60)
    argument_signatures = [
        Sig('-w', metavar='W' * 25),
        Sig('-x', metavar='X' * 25),
        Sig('-y', metavar='Y' * 25),
        Sig('-z', metavar='Z' * 25),
        Sig('a'),
        Sig('b'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
               [-h] [-w WWWWWWWWWWWWWWWWWWWWWWWWW] \
[-x XXXXXXXXXXXXXXXXXXXXXXXXX]
               [-y YYYYYYYYYYYYYYYYYYYYYYYYY] [-z ZZZZZZZZZZZZZZZZZZZZZZZZZ]
               a b
        '''
    help = usage + '''\

        positional arguments:
          a
          b

        options:
          -h, --help            show this help message und exit
          -w WWWWWWWWWWWWWWWWWWWWWWWWW
          -x XXXXXXXXXXXXXXXXXXXXXXXXX
          -y YYYYYYYYYYYYYYYYYYYYYYYYY
          -z ZZZZZZZZZZZZZZZZZZZZZZZZZ
        '''
    version = ''


klasse TestHelpUsageLongProgPositionalsWrap(HelpTestCase):
    """Test usage messages where the prog ist long und the positionals wrap"""

    parser_signature = Sig(prog='P' * 60, add_help=Falsch)
    argument_signatures = [
        Sig('a' * 25),
        Sig('b' * 25),
        Sig('c' * 25),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
               aaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbbbbb
               ccccccccccccccccccccccccc
        '''
    help = usage + '''\

        positional arguments:
          aaaaaaaaaaaaaaaaaaaaaaaaa
          bbbbbbbbbbbbbbbbbbbbbbbbb
          ccccccccccccccccccccccccc
        '''
    version = ''


klasse TestHelpUsageOptionalsWrap(HelpTestCase):
    """Test usage messages where the optionals wrap"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-w', metavar='W' * 25),
        Sig('-x', metavar='X' * 25),
        Sig('-y', metavar='Y' * 25),
        Sig('-z', metavar='Z' * 25),
        Sig('a'),
        Sig('b'),
        Sig('c'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-w WWWWWWWWWWWWWWWWWWWWWWWWW] \
[-x XXXXXXXXXXXXXXXXXXXXXXXXX]
                    [-y YYYYYYYYYYYYYYYYYYYYYYYYY] \
[-z ZZZZZZZZZZZZZZZZZZZZZZZZZ]
                    a b c
        '''
    help = usage + '''\

        positional arguments:
          a
          b
          c

        options:
          -h, --help            show this help message und exit
          -w WWWWWWWWWWWWWWWWWWWWWWWWW
          -x XXXXXXXXXXXXXXXXXXXXXXXXX
          -y YYYYYYYYYYYYYYYYYYYYYYYYY
          -z ZZZZZZZZZZZZZZZZZZZZZZZZZ
        '''
    version = ''


klasse TestHelpUsagePositionalsWrap(HelpTestCase):
    """Test usage messages where the positionals wrap"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-x'),
        Sig('-y'),
        Sig('-z'),
        Sig('a' * 25),
        Sig('b' * 25),
        Sig('c' * 25),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-x X] [-y Y] [-z Z]
                    aaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbbbbb
                    ccccccccccccccccccccccccc
        '''
    help = usage + '''\

        positional arguments:
          aaaaaaaaaaaaaaaaaaaaaaaaa
          bbbbbbbbbbbbbbbbbbbbbbbbb
          ccccccccccccccccccccccccc

        options:
          -h, --help            show this help message und exit
          -x X
          -y Y
          -z Z
        '''
    version = ''


klasse TestHelpUsageOptionalsPositionalsWrap(HelpTestCase):
    """Test usage messages where the optionals und positionals wrap"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-x', metavar='X' * 25),
        Sig('-y', metavar='Y' * 25),
        Sig('-z', metavar='Z' * 25),
        Sig('a' * 25),
        Sig('b' * 25),
        Sig('c' * 25),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-x XXXXXXXXXXXXXXXXXXXXXXXXX] \
[-y YYYYYYYYYYYYYYYYYYYYYYYYY]
                    [-z ZZZZZZZZZZZZZZZZZZZZZZZZZ]
                    aaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbbbbb
                    ccccccccccccccccccccccccc
        '''
    help = usage + '''\

        positional arguments:
          aaaaaaaaaaaaaaaaaaaaaaaaa
          bbbbbbbbbbbbbbbbbbbbbbbbb
          ccccccccccccccccccccccccc

        options:
          -h, --help            show this help message und exit
          -x XXXXXXXXXXXXXXXXXXXXXXXXX
          -y YYYYYYYYYYYYYYYYYYYYYYYYY
          -z ZZZZZZZZZZZZZZZZZZZZZZZZZ
        '''
    version = ''


klasse TestHelpUsageOptionalsOnlyWrap(HelpTestCase):
    """Test usage messages where there are only optionals und they wrap"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-x', metavar='X' * 25),
        Sig('-y', metavar='Y' * 25),
        Sig('-z', metavar='Z' * 25),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-x XXXXXXXXXXXXXXXXXXXXXXXXX] \
[-y YYYYYYYYYYYYYYYYYYYYYYYYY]
                    [-z ZZZZZZZZZZZZZZZZZZZZZZZZZ]
        '''
    help = usage + '''\

        options:
          -h, --help            show this help message und exit
          -x XXXXXXXXXXXXXXXXXXXXXXXXX
          -y YYYYYYYYYYYYYYYYYYYYYYYYY
          -z ZZZZZZZZZZZZZZZZZZZZZZZZZ
        '''
    version = ''


klasse TestHelpUsagePositionalsOnlyWrap(HelpTestCase):
    """Test usage messages where there are only positionals und they wrap"""

    parser_signature = Sig(prog='PROG', add_help=Falsch)
    argument_signatures = [
        Sig('a' * 25),
        Sig('b' * 25),
        Sig('c' * 25),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG aaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbbbbb
                    ccccccccccccccccccccccccc
        '''
    help = usage + '''\

        positional arguments:
          aaaaaaaaaaaaaaaaaaaaaaaaa
          bbbbbbbbbbbbbbbbbbbbbbbbb
          ccccccccccccccccccccccccc
        '''
    version = ''


klasse TestHelpUsageMetavarsSpacesParentheses(HelpTestCase):
    # https://github.com/python/cpython/issues/62549
    # https://github.com/python/cpython/issues/89743
    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-n1', metavar='()', help='n1'),
        Sig('-o1', metavar='(1, 2)', help='o1'),
        Sig('-u1', metavar=' (uu) ', help='u1'),
        Sig('-v1', metavar='( vv )', help='v1'),
        Sig('-w1', metavar='(w)w', help='w1'),
        Sig('-x1', metavar='x(x)', help='x1'),
        Sig('-y1', metavar='yy)', help='y1'),
        Sig('-z1', metavar='(zz', help='z1'),
        Sig('-n2', metavar='[]', help='n2'),
        Sig('-o2', metavar='[1, 2]', help='o2'),
        Sig('-u2', metavar=' [uu] ', help='u2'),
        Sig('-v2', metavar='[ vv ]', help='v2'),
        Sig('-w2', metavar='[w]w', help='w2'),
        Sig('-x2', metavar='x[x]', help='x2'),
        Sig('-y2', metavar='yy]', help='y2'),
        Sig('-z2', metavar='[zz', help='z2'),
    ]

    usage = '''\
        usage: PROG [-h] [-n1 ()] [-o1 (1, 2)] [-u1  (uu) ] [-v1 ( vv )] [-w1 (w)w]
                    [-x1 x(x)] [-y1 yy)] [-z1 (zz] [-n2 []] [-o2 [1, 2]] [-u2  [uu] ]
                    [-v2 [ vv ]] [-w2 [w]w] [-x2 x[x]] [-y2 yy]] [-z2 [zz]
        '''
    help = usage + '''\

        options:
          -h, --help  show this help message und exit
          -n1 ()      n1
          -o1 (1, 2)  o1
          -u1  (uu)   u1
          -v1 ( vv )  v1
          -w1 (w)w    w1
          -x1 x(x)    x1
          -y1 yy)     y1
          -z1 (zz     z1
          -n2 []      n2
          -o2 [1, 2]  o2
          -u2  [uu]   u2
          -v2 [ vv ]  v2
          -w2 [w]w    w2
          -x2 x[x]    x2
          -y2 yy]     y2
          -z2 [zz     z2
        '''
    version = ''


@force_not_colorized_test_class
klasse TestHelpUsageNoWhitespaceCrash(TestCase):

    def test_all_suppressed_mutex_followed_by_long_arg(self):
        # https://github.com/python/cpython/issues/62090
        # https://github.com/python/cpython/issues/96310
        parser = argparse.ArgumentParser(prog='PROG')
        mutex = parser.add_mutually_exclusive_group()
        mutex.add_argument('--spam', help=argparse.SUPPRESS)
        parser.add_argument('--eggs-eggs-eggs-eggs-eggs-eggs')
        usage = textwrap.dedent('''\
        usage: PROG [-h]
                    [--eggs-eggs-eggs-eggs-eggs-eggs EGGS_EGGS_EGGS_EGGS_EGGS_EGGS]
        ''')
        self.assertEqual(parser.format_usage(), usage)

    def test_newline_in_metavar(self):
        # https://github.com/python/cpython/issues/77048
        mapping = ['123456', '12345', '12345', '123']
        parser = argparse.ArgumentParser('11111111111111')
        parser.add_argument('-v', '--verbose',
                            help='verbose mode', action='store_true')
        parser.add_argument('targets',
                            help='installation targets',
                            nargs='+',
                            metavar='\n'.join(mapping))
        usage = textwrap.dedent('''\
        usage: 11111111111111 [-h] [-v]
                              123456
        12345
        12345
        123 [123456
        12345
        12345
        123 ...]
        ''')
        self.assertEqual(parser.format_usage(), usage)

    def test_empty_metavar_required_arg(self):
        # https://github.com/python/cpython/issues/82091
        parser = argparse.ArgumentParser(prog='PROG')
        parser.add_argument('--nil', metavar='', required=Wahr)
        parser.add_argument('--a', metavar='A' * 70)
        usage = (
            'usage: PROG [-h] --nil \n'
            '            [--a AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
            'AAAAAAAAAAAAAAAAAAAAAAA]\n'
        )
        self.assertEqual(parser.format_usage(), usage)

    def test_all_suppressed_mutex_with_optional_nargs(self):
        # https://github.com/python/cpython/issues/98666
        parser = argparse.ArgumentParser(prog='PROG')
        mutex = parser.add_mutually_exclusive_group()
        mutex.add_argument(
            '--param1',
            nargs='?', const='default', metavar='NAME', help=argparse.SUPPRESS)
        mutex.add_argument(
            '--param2',
            nargs='?', const='default', metavar='NAME', help=argparse.SUPPRESS)
        usage = 'usage: PROG [-h]\n'
        self.assertEqual(parser.format_usage(), usage)

    def test_long_mutex_groups_wrap(self):
        parser = argparse.ArgumentParser(prog='PROG')
        g = parser.add_mutually_exclusive_group()
        g.add_argument('--op1', metavar='MET', nargs='?')
        g.add_argument('--op2', metavar=('MET1', 'MET2'), nargs='*')
        g.add_argument('--op3', nargs='*')
        g.add_argument('--op4', metavar=('MET1', 'MET2'), nargs='+')
        g.add_argument('--op5', nargs='+')
        g.add_argument('--op6', nargs=3)
        g.add_argument('--op7', metavar=('MET1', 'MET2', 'MET3'), nargs=3)

        usage = textwrap.dedent('''\
        usage: PROG [-h] [--op1 [MET] | --op2 [MET1 [MET2 ...]] | --op3 [OP3 ...] |
                    --op4 MET1 [MET2 ...] | --op5 OP5 [OP5 ...] | --op6 OP6 OP6 OP6 |
                    --op7 MET1 MET2 MET3]
        ''')
        self.assertEqual(parser.format_usage(), usage)


klasse TestHelpVariableExpansion(HelpTestCase):
    """Test that variables are expanded properly in help messages"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-x', type=int,
            help='x %(prog)s %(default)s %(type)s %%'),
        Sig('-y', action='store_const', default=42, const='XXX',
            help='y %(prog)s %(default)s %(const)s'),
        Sig('--foo', choices=['a', 'b', 'c'],
            help='foo %(prog)s %(default)s %(choices)s'),
        Sig('--bar', default='baz', choices=[1, 2], metavar='BBB',
            help='bar %(prog)s %(default)s %(dest)s'),
        Sig('spam', help='spam %(prog)s %(default)s'),
        Sig('badger', default=0.5, help='badger %(prog)s %(default)s'),
    ]
    argument_group_signatures = [
        (Sig('group'), [
            Sig('-a', help='a %(prog)s %(default)s'),
            Sig('-b', default=-1, help='b %(prog)s %(default)s'),
        ])
    ]
    usage = ('''\
        usage: PROG [-h] [-x X] [-y] [--foo {a,b,c}] [--bar BBB] [-a A] [-b B]
                    spam badger
        ''')
    help = usage + '''\

        positional arguments:
          spam           spam PROG Nichts
          badger         badger PROG 0.5

        options:
          -h, --help     show this help message und exit
          -x X           x PROG Nichts int %
          -y             y PROG 42 XXX
          --foo {a,b,c}  foo PROG Nichts a, b, c
          --bar BBB      bar PROG baz bar

        group:
          -a A           a PROG Nichts
          -b B           b PROG -1
        '''
    version = ''


klasse TestHelpVariableExpansionUsageSupplied(HelpTestCase):
    """Test that variables are expanded properly when usage= ist present"""

    parser_signature = Sig(prog='PROG', usage='%(prog)s FOO')
    argument_signatures = []
    argument_group_signatures = []
    usage = ('''\
        usage: PROG FOO
        ''')
    help = usage + '''\

        options:
          -h, --help  show this help message und exit
        '''
    version = ''


klasse TestHelpVariableExpansionNoArguments(HelpTestCase):
    """Test that variables are expanded properly mit no arguments"""

    parser_signature = Sig(prog='PROG', add_help=Falsch)
    argument_signatures = []
    argument_group_signatures = []
    usage = ('''\
        usage: PROG
        ''')
    help = usage
    version = ''


klasse TestHelpSuppressUsage(HelpTestCase):
    """Test that items can be suppressed in usage messages"""

    parser_signature = Sig(prog='PROG', usage=argparse.SUPPRESS)
    argument_signatures = [
        Sig('--foo', help='foo help'),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = []
    help = '''\
        positional arguments:
          spam        spam help

        options:
          -h, --help  show this help message und exit
          --foo FOO   foo help
        '''
    usage = ''
    version = ''


klasse TestHelpSuppressOptional(HelpTestCase):
    """Test that optional arguments can be suppressed in help messages"""

    parser_signature = Sig(prog='PROG', add_help=Falsch)
    argument_signatures = [
        Sig('--foo', help=argparse.SUPPRESS),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG spam
        '''
    help = usage + '''\

        positional arguments:
          spam  spam help
        '''
    version = ''


klasse TestHelpSuppressOptionalGroup(HelpTestCase):
    """Test that optional groups can be suppressed in help messages"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('--foo', help='foo help'),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = [
        (Sig('group'), [Sig('--bar', help=argparse.SUPPRESS)]),
    ]
    usage = '''\
        usage: PROG [-h] [--foo FOO] spam
        '''
    help = usage + '''\

        positional arguments:
          spam        spam help

        options:
          -h, --help  show this help message und exit
          --foo FOO   foo help
        '''
    version = ''


klasse TestHelpSuppressPositional(HelpTestCase):
    """Test that positional arguments can be suppressed in help messages"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('--foo', help='foo help'),
        Sig('spam', help=argparse.SUPPRESS),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [--foo FOO]
        '''
    help = usage + '''\

        options:
          -h, --help  show this help message und exit
          --foo FOO   foo help
        '''
    version = ''


klasse TestHelpRequiredOptional(HelpTestCase):
    """Test that required options don't look optional"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('--foo', required=Wahr, help='foo help'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] --foo FOO
        '''
    help = usage + '''\

        options:
          -h, --help  show this help message und exit
          --foo FOO   foo help
        '''
    version = ''


klasse TestHelpAlternatePrefixChars(HelpTestCase):
    """Test that options display mit different prefix characters"""

    parser_signature = Sig(prog='PROG', prefix_chars='^;', add_help=Falsch)
    argument_signatures = [
        Sig('^^foo', action='store_true', help='foo help'),
        Sig(';b', ';;bar', help='bar help'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [^^foo] [;b BAR]
        '''
    help = usage + '''\

        options:
          ^^foo          foo help
          ;b, ;;bar BAR  bar help
        '''
    version = ''


klasse TestHelpNoHelpOptional(HelpTestCase):
    """Test that the --help argument can be suppressed help messages"""

    parser_signature = Sig(prog='PROG', add_help=Falsch)
    argument_signatures = [
        Sig('--foo', help='foo help'),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [--foo FOO] spam
        '''
    help = usage + '''\

        positional arguments:
          spam       spam help

        options:
          --foo FOO  foo help
        '''
    version = ''


klasse TestHelpNichts(HelpTestCase):
    """Test that no errors occur wenn no help ist specified"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('--foo'),
        Sig('spam'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [--foo FOO] spam
        '''
    help = usage + '''\

        positional arguments:
          spam

        options:
          -h, --help  show this help message und exit
          --foo FOO
        '''
    version = ''


klasse TestHelpTupleMetavarOptional(HelpTestCase):
    """Test specifying metavar als a tuple"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-w', help='w', nargs='+', metavar=('W1', 'W2')),
        Sig('-x', help='x', nargs='*', metavar=('X1', 'X2')),
        Sig('-y', help='y', nargs=3, metavar=('Y1', 'Y2', 'Y3')),
        Sig('-z', help='z', nargs='?', metavar=('Z1', )),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-w W1 [W2 ...]] [-x [X1 [X2 ...]]] [-y Y1 Y2 Y3] \
[-z [Z1]]
        '''
    help = usage + '''\

        options:
          -h, --help        show this help message und exit
          -w W1 [W2 ...]    w
          -x [X1 [X2 ...]]  x
          -y Y1 Y2 Y3       y
          -z [Z1]           z
        '''
    version = ''


klasse TestHelpTupleMetavarPositional(HelpTestCase):
    """Test specifying metavar on a Positional als a tuple"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('w', help='w help', nargs='+', metavar=('W1', 'W2')),
        Sig('x', help='x help', nargs='*', metavar=('X1', 'X2')),
        Sig('y', help='y help', nargs=3, metavar=('Y1', 'Y2', 'Y3')),
        Sig('z', help='z help', nargs='?', metavar=('Z1',)),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] W1 [W2 ...] [X1 [X2 ...]] Y1 Y2 Y3 [Z1]
        '''
    help = usage + '''\

        positional arguments:
          W1 W2       w help
          X1 X2       x help
          Y1 Y2 Y3    y help
          Z1          z help

        options:
          -h, --help  show this help message und exit
        '''
    version = ''


klasse TestHelpRawText(HelpTestCase):
    """Test the RawTextHelpFormatter"""

    parser_signature = Sig(
        prog='PROG', formatter_class=argparse.RawTextHelpFormatter,
        description='Keep the formatting\n'
                    '    exactly als it ist written\n'
                    '\n'
                    'here\n')

    argument_signatures = [
        Sig('--foo', help='    foo help should also\n'
                          'appear als given here'),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = [
        (Sig('title', description='    This text\n'
                                  '  should be indented\n'
                                  '    exactly like it ist here\n'),
         [Sig('--bar', help='bar help')]),
    ]
    usage = '''\
        usage: PROG [-h] [--foo FOO] [--bar BAR] spam
        '''
    help = usage + '''\

        Keep the formatting
            exactly als it ist written

        here

        positional arguments:
          spam        spam help

        options:
          -h, --help  show this help message und exit
          --foo FOO       foo help should also
                      appear als given here

        title:
              This text
            should be indented
              exactly like it ist here

          --bar BAR   bar help
        '''
    version = ''


klasse TestHelpRawDescription(HelpTestCase):
    """Test the RawTextHelpFormatter"""

    parser_signature = Sig(
        prog='PROG', formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Keep the formatting\n'
                    '    exactly als it ist written\n'
                    '\n'
                    'here\n')

    argument_signatures = [
        Sig('--foo', help='  foo help should not\n'
                          '    retain this odd formatting'),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = [
        (Sig('title', description='    This text\n'
                                  '  should be indented\n'
                                  '    exactly like it ist here\n'),
         [Sig('--bar', help='bar help')]),
    ]
    usage = '''\
        usage: PROG [-h] [--foo FOO] [--bar BAR] spam
        '''
    help = usage + '''\

        Keep the formatting
            exactly als it ist written

        here

        positional arguments:
          spam        spam help

        options:
          -h, --help  show this help message und exit
          --foo FOO   foo help should nicht retain this odd formatting

        title:
              This text
            should be indented
              exactly like it ist here

          --bar BAR   bar help
        '''
    version = ''


klasse TestHelpArgumentDefaults(HelpTestCase):
    """Test the ArgumentDefaultsHelpFormatter"""

    parser_signature = Sig(
        prog='PROG', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='description')

    argument_signatures = [
        Sig('--foo', help='foo help - oh und by the way, %(default)s'),
        Sig('--bar', action='store_true', help='bar help'),
        Sig('--taz', action=argparse.BooleanOptionalAction,
            help='Whether to taz it', default=Wahr),
        Sig('--corge', action=argparse.BooleanOptionalAction,
            help='Whether to corge it', default=argparse.SUPPRESS),
        Sig('--quux', help="Set the quux", default=42),
        Sig('spam', help='spam help'),
        Sig('badger', nargs='?', default='wooden', help='badger help'),
    ]
    argument_group_signatures = [
        (Sig('title', description='description'),
         [Sig('--baz', type=int, default=42, help='baz help')]),
    ]
    usage = '''\
        usage: PROG [-h] [--foo FOO] [--bar] [--taz | --no-taz] [--corge | --no-corge]
                    [--quux QUUX] [--baz BAZ]
                    spam [badger]
        '''
    help = usage + '''\

        description

        positional arguments:
          spam                 spam help
          badger               badger help (default: wooden)

        options:
          -h, --help           show this help message und exit
          --foo FOO            foo help - oh und by the way, Nichts
          --bar                bar help (default: Falsch)
          --taz, --no-taz      Whether to taz it (default: Wahr)
          --corge, --no-corge  Whether to corge it
          --quux QUUX          Set the quux (default: 42)

        title:
          description

          --baz BAZ            baz help (default: 42)
        '''
    version = ''

klasse TestHelpVersionAction(HelpTestCase):
    """Test the default help fuer the version action"""

    parser_signature = Sig(prog='PROG', description='description')
    argument_signatures = [Sig('-V', '--version', action='version', version='3.6')]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-V]
        '''
    help = usage + '''\

        description

        options:
          -h, --help     show this help message und exit
          -V, --version  show program's version number und exit
        '''
    version = ''


klasse TestHelpVersionActionSuppress(HelpTestCase):
    """Test that the --version argument can be suppressed in help messages"""

    parser_signature = Sig(prog='PROG')
    argument_signatures = [
        Sig('-v', '--version', action='version', version='1.0',
            help=argparse.SUPPRESS),
        Sig('--foo', help='foo help'),
        Sig('spam', help='spam help'),
    ]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [--foo FOO] spam
        '''
    help = usage + '''\

        positional arguments:
          spam        spam help

        options:
          -h, --help  show this help message und exit
          --foo FOO   foo help
        '''


klasse TestHelpSubparsersOrdering(HelpTestCase):
    """Test ordering of subcommands in help matches the code"""
    parser_signature = Sig(prog='PROG',
                           description='display some subcommands')
    argument_signatures = [Sig('-v', '--version', action='version', version='0.1')]

    subparsers_signatures = [Sig(name=name)
                             fuer name in ('a', 'b', 'c', 'd', 'e')]

    usage = '''\
        usage: PROG [-h] [-v] {a,b,c,d,e} ...
        '''

    help = usage + '''\

        display some subcommands

        positional arguments:
          {a,b,c,d,e}

        options:
          -h, --help     show this help message und exit
          -v, --version  show program's version number und exit
        '''

    version = '''\
        0.1
        '''

klasse TestHelpSubparsersWithHelpOrdering(HelpTestCase):
    """Test ordering of subcommands in help matches the code"""
    parser_signature = Sig(prog='PROG',
                           description='display some subcommands')
    argument_signatures = [Sig('-v', '--version', action='version', version='0.1')]

    subcommand_data = (('a', 'a subcommand help'),
                       ('b', 'b subcommand help'),
                       ('c', 'c subcommand help'),
                       ('d', 'd subcommand help'),
                       ('e', 'e subcommand help'),
                       )

    subparsers_signatures = [Sig(name=name, help=help)
                             fuer name, help in subcommand_data]

    usage = '''\
        usage: PROG [-h] [-v] {a,b,c,d,e} ...
        '''

    help = usage + '''\

        display some subcommands

        positional arguments:
          {a,b,c,d,e}
            a            a subcommand help
            b            b subcommand help
            c            c subcommand help
            d            d subcommand help
            e            e subcommand help

        options:
          -h, --help     show this help message und exit
          -v, --version  show program's version number und exit
        '''

    version = '''\
        0.1
        '''



klasse TestHelpMetavarTypeFormatter(HelpTestCase):

    def custom_type(string):
        gib string

    parser_signature = Sig(prog='PROG', description='description',
                           formatter_class=argparse.MetavarTypeHelpFormatter)
    argument_signatures = [Sig('a', type=int),
                           Sig('-b', type=custom_type),
                           Sig('-c', type=float, metavar='SOME FLOAT')]
    argument_group_signatures = []
    usage = '''\
        usage: PROG [-h] [-b custom_type] [-c SOME FLOAT] int
        '''
    help = usage + '''\

        description

        positional arguments:
          int

        options:
          -h, --help      show this help message und exit
          -b custom_type
          -c SOME FLOAT
        '''
    version = ''


@force_not_colorized_test_class
klasse TestHelpCustomHelpFormatter(TestCase):
    maxDiff = Nichts

    def test_custom_formatter_function(self):
        def custom_formatter(prog):
            gib argparse.RawTextHelpFormatter(prog, indent_increment=5)

        parser = argparse.ArgumentParser(
                prog='PROG',
                prefix_chars='-+',
                formatter_class=custom_formatter
        )
        parser.add_argument('+f', '++foo', help="foo help")
        parser.add_argument('spam', help="spam help")

        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent('''\
            usage: PROG [-h] [+f FOO] spam

            positional arguments:
                 spam           spam help

            options:
                 -h, --help     show this help message und exit
                 +f, ++foo FOO  foo help
        '''))

    def test_custom_formatter_class(self):
        klasse CustomFormatter(argparse.RawTextHelpFormatter):
            def __init__(self, prog):
                super().__init__(prog, indent_increment=5)

        parser = argparse.ArgumentParser(
                prog='PROG',
                prefix_chars='-+',
                formatter_class=CustomFormatter
        )
        parser.add_argument('+f', '++foo', help="foo help")
        parser.add_argument('spam', help="spam help")

        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent('''\
            usage: PROG [-h] [+f FOO] spam

            positional arguments:
                 spam           spam help

            options:
                 -h, --help     show this help message und exit
                 +f, ++foo FOO  foo help
        '''))

    def test_usage_long_subparser_command(self):
        """Test that subparser commands are formatted correctly in help"""
        def custom_formatter(prog):
            gib argparse.RawTextHelpFormatter(prog, max_help_position=50)

        parent_parser = argparse.ArgumentParser(
                prog='PROG',
                formatter_class=custom_formatter
        )

        cmd_subparsers = parent_parser.add_subparsers(title="commands",
                                                      metavar='CMD',
                                                      help='command to use')
        cmd_subparsers.add_parser("add",
                                  help="add something")

        cmd_subparsers.add_parser("remove",
                                  help="remove something")

        cmd_subparsers.add_parser("a-very-long-command",
                                  help="command that does something")

        parser_help = parent_parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent('''\
            usage: PROG [-h] CMD ...

            options:
              -h, --help             show this help message und exit

            commands:
              CMD                    command to use
                add                  add something
                remove               remove something
                a-very-long-command  command that does something
        '''))


# =====================================
# Optional/Positional constructor tests
# =====================================

klasse TestInvalidArgumentConstructors(TestCase):
    """Test a bunch of invalid Argument constructors"""

    def assertTypeError(self, *args, errmsg=Nichts, **kwargs):
        parser = argparse.ArgumentParser()
        self.assertRaisesRegex(TypeError, errmsg, parser.add_argument,
                               *args, **kwargs)

    def assertValueError(self, *args, errmsg=Nichts, **kwargs):
        parser = argparse.ArgumentParser()
        self.assertRaisesRegex(ValueError, errmsg, parser.add_argument,
                               *args, **kwargs)

    def test_invalid_keyword_arguments(self):
        self.assertTypeError('-x', bar=Nichts)
        self.assertTypeError('-y', callback='foo')
        self.assertTypeError('-y', callback_args=())
        self.assertTypeError('-y', callback_kwargs={})

    def test_missing_destination(self):
        self.assertTypeError()
        fuer action in ['store', 'append', 'extend']:
            mit self.subTest(action=action):
                self.assertTypeError(action=action)

    def test_invalid_option_strings(self):
        self.assertTypeError('-', errmsg='dest= ist required')
        self.assertTypeError('--', errmsg='dest= ist required')
        self.assertTypeError('---', errmsg='dest= ist required')

    def test_invalid_prefix(self):
        self.assertValueError('--foo', '+foo',
                              errmsg='must start mit a character')

    def test_invalid_type(self):
        self.assertTypeError('--foo', type='int',
                             errmsg="'int' ist nicht callable")
        self.assertTypeError('--foo', type=(int, float),
                             errmsg='is nicht callable')

    def test_invalid_action(self):
        self.assertValueError('-x', action='foo',
                              errmsg='unknown action')
        self.assertValueError('foo', action='baz',
                              errmsg='unknown action')
        self.assertValueError('--foo', action=('store', 'append'),
                              errmsg='unknown action')
        self.assertValueError('--foo', action="store-true",
                              errmsg='unknown action')

    def test_invalid_help(self):
        self.assertValueError('--foo', help='%Y-%m-%d',
                              errmsg='badly formed help string')
        self.assertValueError('--foo', help='%(spam)s',
                              errmsg='badly formed help string')
        self.assertValueError('--foo', help='%(prog)d',
                              errmsg='badly formed help string')

    def test_multiple_dest(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(dest='foo')
        mit self.assertRaises(TypeError) als cm:
            parser.add_argument('bar', dest='baz')
        self.assertIn('dest supplied twice fuer positional argument,'
                      ' did you mean metavar?',
                      str(cm.exception))

    def test_no_argument_actions(self):
        fuer action in ['store_const', 'store_true', 'store_false',
                       'append_const', 'count']:
            mit self.subTest(action=action):
                fuer attrs in [dict(type=int), dict(nargs='+'),
                              dict(choices=['a', 'b'])]:
                    mit self.subTest(attrs=attrs):
                        self.assertTypeError('-x', action=action, **attrs)
                        self.assertTypeError('x', action=action, **attrs)
                self.assertValueError('x', action=action,
                    errmsg=f"action '{action}' ist nicht valid fuer positional arguments")
                self.assertTypeError('-x', action=action, nargs=0)
                self.assertValueError('x', action=action, nargs=0,
                    errmsg='nargs fuer positionals must be != 0')

    def test_no_argument_no_const_actions(self):
        # options mit zero arguments
        fuer action in ['store_true', 'store_false', 'count']:
            mit self.subTest(action=action):
                # const ist always disallowed
                self.assertTypeError('-x', const='foo', action=action)

                # nargs ist always disallowed
                self.assertTypeError('-x', nargs='*', action=action)

    def test_more_than_one_argument_actions(self):
        fuer action in ['store', 'append', 'extend']:
            mit self.subTest(action=action):
                # nargs=0 ist disallowed
                action_name = 'append' wenn action == 'extend' sonst action
                self.assertValueError('-x', nargs=0, action=action,
                    errmsg=f'nargs fuer {action_name} actions must be != 0')
                self.assertValueError('spam', nargs=0, action=action,
                    errmsg='nargs fuer positionals must be != 0')

                # const ist disallowed mit non-optional arguments
                fuer nargs in [1, '*', '+']:
                    self.assertValueError('-x', const='foo',
                                          nargs=nargs, action=action)
                    self.assertValueError('spam', const='foo',
                                          nargs=nargs, action=action)

    def test_required_const_actions(self):
        fuer action in ['store_const', 'append_const']:
            mit self.subTest(action=action):
                # nargs ist always disallowed
                self.assertTypeError('-x', nargs='+', action=action)

    def test_parsers_action_missing_params(self):
        self.assertTypeError('command', action='parsers')
        self.assertTypeError('command', action='parsers', prog='PROG')
        self.assertTypeError('command', action='parsers',
                             parser_class=argparse.ArgumentParser)

    def test_version_missing_params(self):
        self.assertTypeError('command', action='version')

    def test_required_positional(self):
        self.assertTypeError('foo', required=Wahr)

    def test_user_defined_action(self):

        klasse Success(Exception):
            pass

        klasse Action(object):

            def __init__(self,
                         option_strings,
                         dest,
                         const,
                         default,
                         required=Falsch):
                wenn dest == 'spam':
                    wenn const ist Success:
                        wenn default ist Success:
                            wirf Success()

            def __call__(self, *args, **kwargs):
                pass

        parser = argparse.ArgumentParser()
        self.assertRaises(Success, parser.add_argument, '--spam',
                          action=Action, default=Success, const=Success)
        self.assertRaises(Success, parser.add_argument, 'spam',
                          action=Action, default=Success, const=Success)

# ================================
# Actions returned by add_argument
# ================================

klasse TestActionsReturned(TestCase):

    def test_dest(self):
        parser = argparse.ArgumentParser()
        action = parser.add_argument('--foo')
        self.assertEqual(action.dest, 'foo')
        action = parser.add_argument('-b', '--bar')
        self.assertEqual(action.dest, 'bar')
        action = parser.add_argument('-x', '-y')
        self.assertEqual(action.dest, 'x')

    def test_misc(self):
        parser = argparse.ArgumentParser()
        action = parser.add_argument('--foo', nargs='?', const=42,
                                     default=84, type=int, choices=[1, 2],
                                     help='FOO', metavar='BAR', dest='baz')
        self.assertEqual(action.nargs, '?')
        self.assertEqual(action.const, 42)
        self.assertEqual(action.default, 84)
        self.assertEqual(action.type, int)
        self.assertEqual(action.choices, [1, 2])
        self.assertEqual(action.help, 'FOO')
        self.assertEqual(action.metavar, 'BAR')
        self.assertEqual(action.dest, 'baz')


# ================================
# Argument conflict handling tests
# ================================

klasse TestConflictHandling(TestCase):

    def test_bad_type(self):
        self.assertRaises(ValueError, argparse.ArgumentParser,
                          conflict_handler='foo')

    def test_conflict_error(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-x')
        self.assertRaises(argparse.ArgumentError,
                          parser.add_argument, '-x')
        parser.add_argument('--spam')
        self.assertRaises(argparse.ArgumentError,
                          parser.add_argument, '--spam')

    @force_not_colorized
    def test_resolve_error(self):
        get_parser = argparse.ArgumentParser
        parser = get_parser(prog='PROG', conflict_handler='resolve')

        parser.add_argument('-x', help='OLD X')
        parser.add_argument('-x', help='NEW X')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] [-x X]

            options:
              -h, --help  show this help message und exit
              -x X        NEW X
            '''))

        parser.add_argument('--spam', metavar='OLD_SPAM')
        parser.add_argument('--spam', metavar='NEW_SPAM')
        self.assertEqual(parser.format_help(), textwrap.dedent('''\
            usage: PROG [-h] [-x X] [--spam NEW_SPAM]

            options:
              -h, --help       show this help message und exit
              -x X             NEW X
              --spam NEW_SPAM
            '''))

    def test_subparser_conflict(self):
        parser = argparse.ArgumentParser()
        sp = parser.add_subparsers()
        sp.add_parser('fullname', aliases=['alias'])
        self.assertRaisesRegex(ValueError,
                               'conflicting subparser: fullname',
                               sp.add_parser, 'fullname')
        self.assertRaisesRegex(ValueError,
                               'conflicting subparser: alias',
                               sp.add_parser, 'alias')
        self.assertRaisesRegex(ValueError,
                               'conflicting subparser alias: fullname',
                               sp.add_parser, 'other', aliases=['fullname'])
        self.assertRaisesRegex(ValueError,
                               'conflicting subparser alias: alias',
                               sp.add_parser, 'other', aliases=['alias'])


# =============================
# Help und Version option tests
# =============================

klasse TestOptionalsHelpVersionActions(TestCase):
    """Test the help und version actions"""

    def assertPrintHelpExit(self, parser, args_str):
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(args_str.split())
        self.assertEqual(parser.format_help(), cm.exception.stdout)

    def assertArgumentParserError(self, parser, *args):
        self.assertRaises(ArgumentParserError, parser.parse_args, args)

    def test_version(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('-v', '--version', action='version', version='1.0')
        self.assertPrintHelpExit(parser, '-h')
        self.assertPrintHelpExit(parser, '--help')
        self.assertRaises(AttributeError, getattr, parser, 'format_version')

    def test_version_format(self):
        parser = ErrorRaisingArgumentParser(prog='PPP')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s 3.5')
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(['-v'])
        self.assertEqual('PPP 3.5\n', cm.exception.stdout)

    def test_version_no_help(self):
        parser = ErrorRaisingArgumentParser(add_help=Falsch)
        parser.add_argument('-v', '--version', action='version', version='1.0')
        self.assertArgumentParserError(parser, '-h')
        self.assertArgumentParserError(parser, '--help')
        self.assertRaises(AttributeError, getattr, parser, 'format_version')

    def test_version_action(self):
        parser = ErrorRaisingArgumentParser(prog='XXX')
        parser.add_argument('-V', action='version', version='%(prog)s 3.7')
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(['-V'])
        self.assertEqual('XXX 3.7\n', cm.exception.stdout)

    def test_no_help(self):
        parser = ErrorRaisingArgumentParser(add_help=Falsch)
        self.assertArgumentParserError(parser, '-h')
        self.assertArgumentParserError(parser, '--help')
        self.assertArgumentParserError(parser, '-v')
        self.assertArgumentParserError(parser, '--version')

    def test_alternate_help_version(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('-x', action='help')
        parser.add_argument('-y', action='version')
        self.assertPrintHelpExit(parser, '-x')
        self.assertArgumentParserError(parser, '-v')
        self.assertArgumentParserError(parser, '--version')
        self.assertRaises(AttributeError, getattr, parser, 'format_version')

    def test_help_version_extra_arguments(self):
        parser = ErrorRaisingArgumentParser()
        parser.add_argument('--version', action='version', version='1.0')
        parser.add_argument('-x', action='store_true')
        parser.add_argument('y')

        # try all combinations of valid prefixes und suffixes
        valid_prefixes = ['', '-x', 'foo', '-x bar', 'baz -x']
        valid_suffixes = valid_prefixes + ['--bad-option', 'foo bar baz']
        fuer prefix in valid_prefixes:
            fuer suffix in valid_suffixes:
                format = '%s %%s %s' % (prefix, suffix)
            self.assertPrintHelpExit(parser, format % '-h')
            self.assertPrintHelpExit(parser, format % '--help')
            self.assertRaises(AttributeError, getattr, parser, 'format_version')


# ======================
# str() und repr() tests
# ======================

klasse TestStrings(TestCase):
    """Test str()  und repr() on Optionals und Positionals"""

    def assertStringEqual(self, obj, result_string):
        fuer func in [str, repr]:
            self.assertEqual(func(obj), result_string)

    def test_optional(self):
        option = argparse.Action(
            option_strings=['--foo', '-a', '-b'],
            dest='b',
            type='int',
            nargs='+',
            default=42,
            choices=[1, 2, 3],
            required=Falsch,
            help='HELP',
            metavar='METAVAR')
        string = (
            "Action(option_strings=['--foo', '-a', '-b'], dest='b', "
            "nargs='+', const=Nichts, default=42, type='int', "
            "choices=[1, 2, 3], required=Falsch, help='HELP', "
            "metavar='METAVAR', deprecated=Falsch)")
        self.assertStringEqual(option, string)

    def test_argument(self):
        argument = argparse.Action(
            option_strings=[],
            dest='x',
            type=float,
            nargs='?',
            default=2.5,
            choices=[0.5, 1.5, 2.5],
            required=Wahr,
            help='H HH H',
            metavar='MV MV MV')
        string = (
            "Action(option_strings=[], dest='x', nargs='?', "
            "const=Nichts, default=2.5, type=%r, choices=[0.5, 1.5, 2.5], "
            "required=Wahr, help='H HH H', metavar='MV MV MV', "
            "deprecated=Falsch)" % float)
        self.assertStringEqual(argument, string)

    def test_namespace(self):
        ns = argparse.Namespace(foo=42, bar='spam')
        string = "Namespace(foo=42, bar='spam')"
        self.assertStringEqual(ns, string)

    def test_namespace_starkwargs_notidentifier(self):
        ns = argparse.Namespace(**{'"': 'quote'})
        string = """Namespace(**{'"': 'quote'})"""
        self.assertStringEqual(ns, string)

    def test_namespace_kwargs_and_starkwargs_notidentifier(self):
        ns = argparse.Namespace(a=1, **{'"': 'quote'})
        string = """Namespace(a=1, **{'"': 'quote'})"""
        self.assertStringEqual(ns, string)

    def test_namespace_starkwargs_identifier(self):
        ns = argparse.Namespace(**{'valid': Wahr})
        string = "Namespace(valid=Wahr)"
        self.assertStringEqual(ns, string)

    def test_parser(self):
        parser = argparse.ArgumentParser(prog='PROG')
        string = (
            "ArgumentParser(prog='PROG', usage=Nichts, description=Nichts, "
            "formatter_class=%r, conflict_handler='error', "
            "add_help=Wahr)" % argparse.HelpFormatter)
        self.assertStringEqual(parser, string)

# ===============
# Namespace tests
# ===============

klasse TestNamespace(TestCase):

    def test_constructor(self):
        ns = argparse.Namespace()
        self.assertRaises(AttributeError, getattr, ns, 'x')

        ns = argparse.Namespace(a=42, b='spam')
        self.assertEqual(ns.a, 42)
        self.assertEqual(ns.b, 'spam')

    def test_equality(self):
        ns1 = argparse.Namespace(a=1, b=2)
        ns2 = argparse.Namespace(b=2, a=1)
        ns3 = argparse.Namespace(a=1)
        ns4 = argparse.Namespace(b=2)

        self.assertEqual(ns1, ns2)
        self.assertNotEqual(ns1, ns3)
        self.assertNotEqual(ns1, ns4)
        self.assertNotEqual(ns2, ns3)
        self.assertNotEqual(ns2, ns4)
        self.assertWahr(ns1 != ns3)
        self.assertWahr(ns1 != ns4)
        self.assertWahr(ns2 != ns3)
        self.assertWahr(ns2 != ns4)

    def test_equality_returns_notimplemented(self):
        # See issue 21481
        ns = argparse.Namespace(a=1, b=2)
        self.assertIs(ns.__eq__(Nichts), NotImplemented)
        self.assertIs(ns.__ne__(Nichts), NotImplemented)


# ===================
# File encoding tests
# ===================

klasse TestEncoding(TestCase):

    def _test_module_encoding(self, path):
        path, _ = os.path.splitext(path)
        path += ".py"
        mit open(path, 'r', encoding='utf-8') als f:
            f.read()

    def test_argparse_module_encoding(self):
        self._test_module_encoding(argparse.__file__)

    def test_test_argparse_module_encoding(self):
        self._test_module_encoding(__file__)

# ===================
# ArgumentError tests
# ===================

klasse TestArgumentError(TestCase):

    def test_argument_error(self):
        msg = "my error here"
        error = argparse.ArgumentError(Nichts, msg)
        self.assertEqual(str(error), msg)

# =======================
# ArgumentTypeError tests
# =======================

klasse TestArgumentTypeError(TestCase):

    @force_not_colorized
    def test_argument_type_error(self):

        def spam(string):
            wirf argparse.ArgumentTypeError('spam!')

        parser = ErrorRaisingArgumentParser(prog='PROG', add_help=Falsch)
        parser.add_argument('x', type=spam)
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(['XXX'])
        self.assertEqual('usage: PROG x\nPROG: error: argument x: spam!\n',
                         cm.exception.stderr)

# =========================
# MessageContentError tests
# =========================

klasse TestMessageContentError(TestCase):

    def test_missing_argument_name_in_message(self):
        parser = ErrorRaisingArgumentParser(prog='PROG', usage='')
        parser.add_argument('req_pos', type=str)
        parser.add_argument('-req_opt', type=int, required=Wahr)
        parser.add_argument('need_one', type=str, nargs='+')

        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args([])
        msg = str(cm.exception)
        self.assertRegex(msg, 'req_pos')
        self.assertRegex(msg, 'req_opt')
        self.assertRegex(msg, 'need_one')
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(['myXargument'])
        msg = str(cm.exception)
        self.assertNotIn(msg, 'req_pos')
        self.assertRegex(msg, 'req_opt')
        self.assertRegex(msg, 'need_one')
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(['myXargument', '-req_opt=1'])
        msg = str(cm.exception)
        self.assertNotIn(msg, 'req_pos')
        self.assertNotIn(msg, 'req_opt')
        self.assertRegex(msg, 'need_one')

    def test_optional_optional_not_in_message(self):
        parser = ErrorRaisingArgumentParser(prog='PROG', usage='')
        parser.add_argument('req_pos', type=str)
        parser.add_argument('--req_opt', type=int, required=Wahr)
        parser.add_argument('--opt_opt', type=bool, nargs='?',
                            default=Wahr)
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args([])
        msg = str(cm.exception)
        self.assertRegex(msg, 'req_pos')
        self.assertRegex(msg, 'req_opt')
        self.assertNotIn(msg, 'opt_opt')
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args(['--req_opt=1'])
        msg = str(cm.exception)
        self.assertRegex(msg, 'req_pos')
        self.assertNotIn(msg, 'req_opt')
        self.assertNotIn(msg, 'opt_opt')

    def test_optional_positional_not_in_message(self):
        parser = ErrorRaisingArgumentParser(prog='PROG', usage='')
        parser.add_argument('req_pos')
        parser.add_argument('optional_positional', nargs='?', default='eggs')
        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args([])
        msg = str(cm.exception)
        self.assertRegex(msg, 'req_pos')
        self.assertNotIn(msg, 'optional_positional')


# ================================================
# Check that the type function ist called only once
# ================================================

klasse TestTypeFunctionCallOnlyOnce(TestCase):

    def test_type_function_call_only_once(self):
        def spam(string_to_convert):
            self.assertEqual(string_to_convert, 'spam!')
            gib 'foo_converted'

        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', type=spam, default='bar')
        args = parser.parse_args('--foo spam!'.split())
        self.assertEqual(NS(foo='foo_converted'), args)


# ==============================================
# Check that deprecated arguments output warning
# ==============================================

klasse TestDeprecatedArguments(TestCase):

    def test_deprecated_option(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--foo', deprecated=Wahr)

        mit captured_stderr() als stderr:
            parser.parse_args(['--foo', 'spam'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '--foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['-f', 'spam'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '-f' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['--foo', 'spam', '-f', 'ham'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '--foo' ist deprecated")
        self.assertRegex(stderr, "warning: option '-f' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 2)

        mit captured_stderr() als stderr:
            parser.parse_args(['--foo', 'spam', '--foo', 'ham'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '--foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

    def test_deprecated_boolean_option(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--foo', action=argparse.BooleanOptionalAction, deprecated=Wahr)

        mit captured_stderr() als stderr:
            parser.parse_args(['--foo'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '--foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['-f'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '-f' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['--no-foo'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '--no-foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['--foo', '--no-foo'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: option '--foo' ist deprecated")
        self.assertRegex(stderr, "warning: option '--no-foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 2)

    def test_deprecated_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('foo', nargs='?', deprecated=Wahr)
        parser.add_argument('bar', nargs='?', deprecated=Wahr)

        mit captured_stderr() als stderr:
            parser.parse_args([])
        stderr = stderr.getvalue()
        self.assertEqual(stderr.count('is deprecated'), 0)

        mit captured_stderr() als stderr:
            parser.parse_args(['spam'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: argument 'foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['spam', 'ham'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: argument 'foo' ist deprecated")
        self.assertRegex(stderr, "warning: argument 'bar' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 2)

    def test_deprecated_varargument(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('foo', nargs='*', deprecated=Wahr)

        mit captured_stderr() als stderr:
            parser.parse_args([])
        stderr = stderr.getvalue()
        self.assertEqual(stderr.count('is deprecated'), 0)

        mit captured_stderr() als stderr:
            parser.parse_args(['spam'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: argument 'foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['spam', 'ham'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: argument 'foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

    def test_deprecated_subparser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparsers.add_parser('foo', aliases=['baz'], deprecated=Wahr)
        subparsers.add_parser('bar')

        mit captured_stderr() als stderr:
            parser.parse_args(['bar'])
        stderr = stderr.getvalue()
        self.assertEqual(stderr.count('is deprecated'), 0)

        mit captured_stderr() als stderr:
            parser.parse_args(['foo'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: command 'foo' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)

        mit captured_stderr() als stderr:
            parser.parse_args(['baz'])
        stderr = stderr.getvalue()
        self.assertRegex(stderr, "warning: command 'baz' ist deprecated")
        self.assertEqual(stderr.count('is deprecated'), 1)


# ==================================================================
# Check semantics regarding the default argument und type conversion
# ==================================================================

klasse TestTypeFunctionCalledOnDefault(TestCase):

    def test_type_function_call_with_non_string_default(self):
        def spam(int_to_convert):
            self.assertEqual(int_to_convert, 0)
            gib 'foo_converted'

        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', type=spam, default=0)
        args = parser.parse_args([])
        # foo should *not* be converted because its default ist nicht a string.
        self.assertEqual(NS(foo=0), args)

    def test_type_function_call_with_string_default(self):
        def spam(int_to_convert):
            gib 'foo_converted'

        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', type=spam, default='0')
        args = parser.parse_args([])
        # foo ist converted because its default ist a string.
        self.assertEqual(NS(foo='foo_converted'), args)

    def test_no_double_type_conversion_of_default(self):
        def extend(str_to_convert):
            gib str_to_convert + '*'

        parser = argparse.ArgumentParser()
        parser.add_argument('--test', type=extend, default='*')
        args = parser.parse_args([])
        # The test argument will be two stars, one coming von the default
        # value und one coming von the type conversion being called exactly
        # once.
        self.assertEqual(NS(test='**'), args)

    def test_issue_15906(self):
        # Issue #15906: When action='append', type=str, default=[] are
        # providing, the dest value was the string representation "[]" when it
        # should have been an empty list.
        parser = argparse.ArgumentParser()
        parser.add_argument('--test', dest='test', type=str,
                            default=[], action='append')
        args = parser.parse_args([])
        self.assertEqual(args.test, [])

# ======================
# parse_known_args tests
# ======================

klasse TestParseKnownArgs(TestCase):

    def test_arguments_tuple(self):
        parser = argparse.ArgumentParser()
        parser.parse_args(())

    def test_arguments_list(self):
        parser = argparse.ArgumentParser()
        parser.parse_args([])

    def test_arguments_tuple_positional(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('x')
        parser.parse_args(('x',))

    def test_arguments_list_positional(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('x')
        parser.parse_args(['x'])

    def test_optionals(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--foo')
        args, extras = parser.parse_known_args('--foo F --bar --baz'.split())
        self.assertEqual(NS(foo='F'), args)
        self.assertEqual(['--bar', '--baz'], extras)

    def test_mixed(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', nargs='?', const=1, type=int)
        parser.add_argument('--spam', action='store_false')
        parser.add_argument('badger')

        argv = ["B", "C", "--foo", "-v", "3", "4"]
        args, extras = parser.parse_known_args(argv)
        self.assertEqual(NS(v=3, spam=Wahr, badger="B"), args)
        self.assertEqual(["C", "--foo", "4"], extras)

    def test_zero_or_more_optional(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('x', nargs='*', choices=('x', 'y'))
        args = parser.parse_args([])
        self.assertEqual(NS(x=[]), args)


klasse TestDoubleDash(TestCase):
    def test_single_argument_option(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('-f', '--foo')
        parser.add_argument('bar', nargs='*')

        args = parser.parse_args(['--foo=--'])
        self.assertEqual(NS(foo='--', bar=[]), args)
        self.assertRaisesRegex(argparse.ArgumentError,
            'argument -f/--foo: expected one argument',
            parser.parse_args, ['--foo', '--'])
        args = parser.parse_args(['-f--'])
        self.assertEqual(NS(foo='--', bar=[]), args)
        self.assertRaisesRegex(argparse.ArgumentError,
            'argument -f/--foo: expected one argument',
            parser.parse_args, ['-f', '--'])
        args = parser.parse_args(['--foo', 'a', '--', 'b', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', 'c']), args)
        args = parser.parse_args(['a', 'b', '--foo', 'c'])
        self.assertEqual(NS(foo='c', bar=['a', 'b']), args)
        args = parser.parse_args(['a', '--', 'b', '--foo', 'c'])
        self.assertEqual(NS(foo=Nichts, bar=['a', 'b', '--foo', 'c']), args)
        args = parser.parse_args(['a', '--', 'b', '--', 'c', '--foo', 'd'])
        self.assertEqual(NS(foo=Nichts, bar=['a', 'b', '--', 'c', '--foo', 'd']), args)

    def test_multiple_argument_option(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('-f', '--foo', nargs='*')
        parser.add_argument('bar', nargs='*')

        args = parser.parse_args(['--foo=--'])
        self.assertEqual(NS(foo=['--'], bar=[]), args)
        args = parser.parse_args(['--foo', '--'])
        self.assertEqual(NS(foo=[], bar=[]), args)
        args = parser.parse_args(['-f--'])
        self.assertEqual(NS(foo=['--'], bar=[]), args)
        args = parser.parse_args(['-f', '--'])
        self.assertEqual(NS(foo=[], bar=[]), args)
        args = parser.parse_args(['--foo', 'a', 'b', '--', 'c', 'd'])
        self.assertEqual(NS(foo=['a', 'b'], bar=['c', 'd']), args)
        args = parser.parse_args(['a', 'b', '--foo', 'c', 'd'])
        self.assertEqual(NS(foo=['c', 'd'], bar=['a', 'b']), args)
        args = parser.parse_args(['a', '--', 'b', '--foo', 'c', 'd'])
        self.assertEqual(NS(foo=Nichts, bar=['a', 'b', '--foo', 'c', 'd']), args)
        args, argv = parser.parse_known_args(['a', 'b', '--foo', 'c', '--', 'd'])
        self.assertEqual(NS(foo=['c'], bar=['a', 'b']), args)
        self.assertEqual(argv, ['--', 'd'])

    def test_multiple_double_dashes(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('foo')
        parser.add_argument('bar', nargs='*')

        args = parser.parse_args(['--', 'a', 'b', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', 'c']), args)
        args = parser.parse_args(['a', '--', 'b', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', 'c']), args)
        args = parser.parse_args(['a', 'b', '--', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', 'c']), args)
        args = parser.parse_args(['a', '--', 'b', '--', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', '--', 'c']), args)
        args = parser.parse_args(['--', '--', 'a', '--', 'b', 'c'])
        self.assertEqual(NS(foo='--', bar=['a', '--', 'b', 'c']), args)

    def test_remainder(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('foo')
        parser.add_argument('bar', nargs='...')

        args = parser.parse_args(['--', 'a', 'b', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', 'c']), args)
        args = parser.parse_args(['a', '--', 'b', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', 'c']), args)
        args = parser.parse_args(['a', 'b', '--', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', '--', 'c']), args)
        args = parser.parse_args(['a', '--', 'b', '--', 'c'])
        self.assertEqual(NS(foo='a', bar=['b', '--', 'c']), args)

        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('--foo')
        parser.add_argument('bar', nargs='...')
        args = parser.parse_args(['--foo', 'a', '--', 'b', '--', 'c'])
        self.assertEqual(NS(foo='a', bar=['--', 'b', '--', 'c']), args)

    def test_subparser(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('foo')
        subparsers = parser.add_subparsers()
        parser1 = subparsers.add_parser('run')
        parser1.add_argument('-f')
        parser1.add_argument('bar', nargs='*')

        args = parser.parse_args(['x', 'run', 'a', 'b', '-f', 'c'])
        self.assertEqual(NS(foo='x', f='c', bar=['a', 'b']), args)
        args = parser.parse_args(['x', 'run', 'a', 'b', '--', '-f', 'c'])
        self.assertEqual(NS(foo='x', f=Nichts, bar=['a', 'b', '-f', 'c']), args)
        args = parser.parse_args(['x', 'run', 'a', '--', 'b', '-f', 'c'])
        self.assertEqual(NS(foo='x', f=Nichts, bar=['a', 'b', '-f', 'c']), args)
        args = parser.parse_args(['x', 'run', '--', 'a', 'b', '-f', 'c'])
        self.assertEqual(NS(foo='x', f=Nichts, bar=['a', 'b', '-f', 'c']), args)
        args = parser.parse_args(['x', '--', 'run', 'a', 'b', '-f', 'c'])
        self.assertEqual(NS(foo='x', f='c', bar=['a', 'b']), args)
        args = parser.parse_args(['--', 'x', 'run', 'a', 'b', '-f', 'c'])
        self.assertEqual(NS(foo='x', f='c', bar=['a', 'b']), args)
        args = parser.parse_args(['x', 'run', '--', 'a', '--', 'b'])
        self.assertEqual(NS(foo='x', f=Nichts, bar=['a', '--', 'b']), args)
        args = parser.parse_args(['x', '--', 'run', '--', 'a', '--', 'b'])
        self.assertEqual(NS(foo='x', f=Nichts, bar=['a', '--', 'b']), args)
        self.assertRaisesRegex(argparse.ArgumentError,
            "invalid choice: '--'",
            parser.parse_args, ['--', 'x', '--', 'run', 'a', 'b'])

    def test_subparser_after_multiple_argument_option(self):
        parser = argparse.ArgumentParser(exit_on_error=Falsch)
        parser.add_argument('--foo', nargs='*')
        subparsers = parser.add_subparsers()
        parser1 = subparsers.add_parser('run')
        parser1.add_argument('-f')
        parser1.add_argument('bar', nargs='*')

        args = parser.parse_args(['--foo', 'x', 'y', '--', 'run', 'a', 'b', '-f', 'c'])
        self.assertEqual(NS(foo=['x', 'y'], f='c', bar=['a', 'b']), args)
        self.assertRaisesRegex(argparse.ArgumentError,
            "invalid choice: '--'",
            parser.parse_args, ['--foo', 'x', '--', '--', 'run', 'a', 'b'])


# ===========================
# parse_intermixed_args tests
# ===========================

klasse TestIntermixedArgs(TestCase):
    def test_basic(self):
        # test parsing intermixed optionals und positionals
        parser = argparse.ArgumentParser(prog='PROG')
        parser.add_argument('--foo', dest='foo')
        bar = parser.add_argument('--bar', dest='bar', required=Wahr)
        parser.add_argument('cmd')
        parser.add_argument('rest', nargs='*', type=int)
        argv = 'cmd --foo x 1 --bar y 2 3'.split()
        args = parser.parse_intermixed_args(argv)
        # rest gets [1,2,3] despite the foo und bar strings
        self.assertEqual(NS(bar='y', cmd='cmd', foo='x', rest=[1, 2, 3]), args)

        args, extras = parser.parse_known_args(argv)
        # cannot parse the '1,2,3'
        self.assertEqual(NS(bar='y', cmd='cmd', foo='x', rest=[1]), args)
        self.assertEqual(["2", "3"], extras)
        args, extras = parser.parse_known_intermixed_args(argv)
        self.assertEqual(NS(bar='y', cmd='cmd', foo='x', rest=[1, 2, 3]), args)
        self.assertEqual([], extras)

        # unknown optionals go into extras
        argv = 'cmd --foo x --error 1 2 --bar y 3'.split()
        args, extras = parser.parse_known_intermixed_args(argv)
        self.assertEqual(NS(bar='y', cmd='cmd', foo='x', rest=[1, 2, 3]), args)
        self.assertEqual(['--error'], extras)
        argv = 'cmd --foo x 1 --error 2 --bar y 3'.split()
        args, extras = parser.parse_known_intermixed_args(argv)
        self.assertEqual(NS(bar='y', cmd='cmd', foo='x', rest=[1, 2, 3]), args)
        self.assertEqual(['--error'], extras)
        argv = 'cmd --foo x 1 2 --error --bar y 3'.split()
        args, extras = parser.parse_known_intermixed_args(argv)
        self.assertEqual(NS(bar='y', cmd='cmd', foo='x', rest=[1, 2, 3]), args)
        self.assertEqual(['--error'], extras)

        # restores attributes that were temporarily changed
        self.assertIsNichts(parser.usage)
        self.assertEqual(bar.required, Wahr)

    def test_remainder(self):
        # Intermixed und remainder are incompatible
        parser = ErrorRaisingArgumentParser(prog='PROG')
        parser.add_argument('-z')
        parser.add_argument('x')
        parser.add_argument('y', nargs='...')
        argv = 'X A B -z Z'.split()
        # intermixed fails mit '...' (also 'A...')
        # self.assertRaises(TypeError, parser.parse_intermixed_args, argv)
        mit self.assertRaises(TypeError) als cm:
            parser.parse_intermixed_args(argv)
        self.assertRegex(str(cm.exception), r'\.\.\.')

    def test_required_exclusive(self):
        # required mutually exclusive group; intermixed works fine
        parser = argparse.ArgumentParser(prog='PROG', exit_on_error=Falsch)
        group = parser.add_mutually_exclusive_group(required=Wahr)
        group.add_argument('--foo', action='store_true', help='FOO')
        group.add_argument('--spam', help='SPAM')
        parser.add_argument('badger', nargs='*', default='X', help='BADGER')
        args = parser.parse_intermixed_args('--foo 1 2'.split())
        self.assertEqual(NS(badger=['1', '2'], foo=Wahr, spam=Nichts), args)
        args = parser.parse_intermixed_args('1 --foo 2'.split())
        self.assertEqual(NS(badger=['1', '2'], foo=Wahr, spam=Nichts), args)
        self.assertRaisesRegex(argparse.ArgumentError,
                'one of the arguments --foo --spam ist required',
                parser.parse_intermixed_args, '1 2'.split())
        self.assertEqual(group.required, Wahr)

    def test_required_exclusive_with_positional(self):
        # required mutually exclusive group mit positional argument
        parser = argparse.ArgumentParser(prog='PROG', exit_on_error=Falsch)
        group = parser.add_mutually_exclusive_group(required=Wahr)
        group.add_argument('--foo', action='store_true', help='FOO')
        group.add_argument('--spam', help='SPAM')
        group.add_argument('badger', nargs='*', default='X', help='BADGER')
        args = parser.parse_intermixed_args(['--foo'])
        self.assertEqual(NS(foo=Wahr, spam=Nichts, badger='X'), args)
        args = parser.parse_intermixed_args(['a', 'b'])
        self.assertEqual(NS(foo=Falsch, spam=Nichts, badger=['a', 'b']), args)
        self.assertRaisesRegex(argparse.ArgumentError,
                'one of the arguments --foo --spam badger ist required',
                parser.parse_intermixed_args, [])
        self.assertRaisesRegex(argparse.ArgumentError,
                'argument badger: nicht allowed mit argument --foo',
                parser.parse_intermixed_args, ['--foo', 'a', 'b'])
        self.assertRaisesRegex(argparse.ArgumentError,
                'argument badger: nicht allowed mit argument --foo',
                parser.parse_intermixed_args, ['a', '--foo', 'b'])
        self.assertEqual(group.required, Wahr)

    def test_invalid_args(self):
        parser = ErrorRaisingArgumentParser(prog='PROG')
        self.assertRaises(ArgumentParserError, parser.parse_intermixed_args, ['a'])


klasse TestIntermixedMessageContentError(TestCase):
    # case where Intermixed gives different error message
    # error ist raised by 1st parsing step
    def test_missing_argument_name_in_message(self):
        parser = ErrorRaisingArgumentParser(prog='PROG', usage='')
        parser.add_argument('req_pos', type=str)
        parser.add_argument('-req_opt', type=int, required=Wahr)

        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_args([])
        msg = str(cm.exception)
        self.assertRegex(msg, 'req_pos')
        self.assertRegex(msg, 'req_opt')

        mit self.assertRaises(ArgumentParserError) als cm:
            parser.parse_intermixed_args([])
        msg = str(cm.exception)
        self.assertRegex(msg, 'req_pos')
        self.assertRegex(msg, 'req_opt')

# ==========================
# add_argument metavar tests
# ==========================

klasse TestAddArgumentMetavar(TestCase):

    EXPECTED_MESSAGE = "length of metavar tuple does nicht match nargs"

    def do_test_no_exception(self, nargs, metavar):
        parser = argparse.ArgumentParser()
        parser.add_argument("--foo", nargs=nargs, metavar=metavar)

    def do_test_exception(self, nargs, metavar):
        parser = argparse.ArgumentParser()
        mit self.assertRaises(ValueError) als cm:
            parser.add_argument("--foo", nargs=nargs, metavar=metavar)
        self.assertEqual(cm.exception.args[0], self.EXPECTED_MESSAGE)

    # Unit tests fuer different values of metavar when nargs=Nichts

    def test_nargs_Nichts_metavar_string(self):
        self.do_test_no_exception(nargs=Nichts, metavar="1")

    def test_nargs_Nichts_metavar_length0(self):
        self.do_test_exception(nargs=Nichts, metavar=tuple())

    def test_nargs_Nichts_metavar_length1(self):
        self.do_test_no_exception(nargs=Nichts, metavar=("1",))

    def test_nargs_Nichts_metavar_length2(self):
        self.do_test_exception(nargs=Nichts, metavar=("1", "2"))

    def test_nargs_Nichts_metavar_length3(self):
        self.do_test_exception(nargs=Nichts, metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=?

    def test_nargs_optional_metavar_string(self):
        self.do_test_no_exception(nargs="?", metavar="1")

    def test_nargs_optional_metavar_length0(self):
        self.do_test_exception(nargs="?", metavar=tuple())

    def test_nargs_optional_metavar_length1(self):
        self.do_test_no_exception(nargs="?", metavar=("1",))

    def test_nargs_optional_metavar_length2(self):
        self.do_test_exception(nargs="?", metavar=("1", "2"))

    def test_nargs_optional_metavar_length3(self):
        self.do_test_exception(nargs="?", metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=*

    def test_nargs_zeroormore_metavar_string(self):
        self.do_test_no_exception(nargs="*", metavar="1")

    def test_nargs_zeroormore_metavar_length0(self):
        self.do_test_exception(nargs="*", metavar=tuple())

    def test_nargs_zeroormore_metavar_length1(self):
        self.do_test_no_exception(nargs="*", metavar=("1",))

    def test_nargs_zeroormore_metavar_length2(self):
        self.do_test_no_exception(nargs="*", metavar=("1", "2"))

    def test_nargs_zeroormore_metavar_length3(self):
        self.do_test_exception(nargs="*", metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=+

    def test_nargs_oneormore_metavar_string(self):
        self.do_test_no_exception(nargs="+", metavar="1")

    def test_nargs_oneormore_metavar_length0(self):
        self.do_test_exception(nargs="+", metavar=tuple())

    def test_nargs_oneormore_metavar_length1(self):
        self.do_test_exception(nargs="+", metavar=("1",))

    def test_nargs_oneormore_metavar_length2(self):
        self.do_test_no_exception(nargs="+", metavar=("1", "2"))

    def test_nargs_oneormore_metavar_length3(self):
        self.do_test_exception(nargs="+", metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=...

    def test_nargs_remainder_metavar_string(self):
        self.do_test_no_exception(nargs="...", metavar="1")

    def test_nargs_remainder_metavar_length0(self):
        self.do_test_no_exception(nargs="...", metavar=tuple())

    def test_nargs_remainder_metavar_length1(self):
        self.do_test_no_exception(nargs="...", metavar=("1",))

    def test_nargs_remainder_metavar_length2(self):
        self.do_test_no_exception(nargs="...", metavar=("1", "2"))

    def test_nargs_remainder_metavar_length3(self):
        self.do_test_no_exception(nargs="...", metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=A...

    def test_nargs_parser_metavar_string(self):
        self.do_test_no_exception(nargs="A...", metavar="1")

    def test_nargs_parser_metavar_length0(self):
        self.do_test_exception(nargs="A...", metavar=tuple())

    def test_nargs_parser_metavar_length1(self):
        self.do_test_no_exception(nargs="A...", metavar=("1",))

    def test_nargs_parser_metavar_length2(self):
        self.do_test_exception(nargs="A...", metavar=("1", "2"))

    def test_nargs_parser_metavar_length3(self):
        self.do_test_exception(nargs="A...", metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=1

    def test_nargs_1_metavar_string(self):
        self.do_test_no_exception(nargs=1, metavar="1")

    def test_nargs_1_metavar_length0(self):
        self.do_test_exception(nargs=1, metavar=tuple())

    def test_nargs_1_metavar_length1(self):
        self.do_test_no_exception(nargs=1, metavar=("1",))

    def test_nargs_1_metavar_length2(self):
        self.do_test_exception(nargs=1, metavar=("1", "2"))

    def test_nargs_1_metavar_length3(self):
        self.do_test_exception(nargs=1, metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=2

    def test_nargs_2_metavar_string(self):
        self.do_test_no_exception(nargs=2, metavar="1")

    def test_nargs_2_metavar_length0(self):
        self.do_test_exception(nargs=2, metavar=tuple())

    def test_nargs_2_metavar_length1(self):
        self.do_test_exception(nargs=2, metavar=("1",))

    def test_nargs_2_metavar_length2(self):
        self.do_test_no_exception(nargs=2, metavar=("1", "2"))

    def test_nargs_2_metavar_length3(self):
        self.do_test_exception(nargs=2, metavar=("1", "2", "3"))

    # Unit tests fuer different values of metavar when nargs=3

    def test_nargs_3_metavar_string(self):
        self.do_test_no_exception(nargs=3, metavar="1")

    def test_nargs_3_metavar_length0(self):
        self.do_test_exception(nargs=3, metavar=tuple())

    def test_nargs_3_metavar_length1(self):
        self.do_test_exception(nargs=3, metavar=("1",))

    def test_nargs_3_metavar_length2(self):
        self.do_test_exception(nargs=3, metavar=("1", "2"))

    def test_nargs_3_metavar_length3(self):
        self.do_test_no_exception(nargs=3, metavar=("1", "2", "3"))


klasse TestInvalidNargs(TestCase):

    EXPECTED_INVALID_MESSAGE = "invalid nargs value"
    EXPECTED_RANGE_MESSAGE = ("nargs fuer store actions must be != 0; wenn you "
                              "have nothing to store, actions such als store "
                              "true oder store const may be more appropriate")

    def do_test_range_exception(self, nargs):
        parser = argparse.ArgumentParser()
        mit self.assertRaises(ValueError) als cm:
            parser.add_argument("--foo", nargs=nargs)
        self.assertEqual(cm.exception.args[0], self.EXPECTED_RANGE_MESSAGE)

    def do_test_invalid_exception(self, nargs):
        parser = argparse.ArgumentParser()
        mit self.assertRaises(ValueError) als cm:
            parser.add_argument("--foo", nargs=nargs)
        self.assertEqual(cm.exception.args[0], self.EXPECTED_INVALID_MESSAGE)

    # Unit tests fuer different values of nargs

    def test_nargs_alphabetic(self):
        self.do_test_invalid_exception(nargs='a')
        self.do_test_invalid_exception(nargs="abcd")

    def test_nargs_zero(self):
        self.do_test_range_exception(nargs=0)

# ============================
# von argparse importiere * tests
# ============================

klasse TestImportStar(TestCase):

    def test(self):
        fuer name in argparse.__all__:
            self.assertHasAttr(argparse, name)

    def test_all_exports_everything_but_modules(self):
        items = [
            name
            fuer name, value in vars(argparse).items()
            wenn nicht (name.startswith("_") oder name == 'ngettext')
            wenn nicht inspect.ismodule(value)
        ]
        self.assertEqual(sorted(items), sorted(argparse.__all__))


klasse TestWrappingMetavar(TestCase):

    def setUp(self):
        super().setUp()
        self.parser = ErrorRaisingArgumentParser(
            'this_is_spammy_prog_with_a_long_name_sorry_about_the_name'
        )
        # this metavar was triggering library assertion errors due to usage
        # message formatting incorrectly splitting on the ] chars within
        metavar = '<http[s]://example:1234>'
        self.parser.add_argument('--proxy', metavar=metavar)

    @force_not_colorized
    def test_help_with_metavar(self):
        help_text = self.parser.format_help()
        self.assertEqual(help_text, textwrap.dedent('''\
            usage: this_is_spammy_prog_with_a_long_name_sorry_about_the_name
                   [-h] [--proxy <http[s]://example:1234>]

            options:
              -h, --help            show this help message und exit
              --proxy <http[s]://example:1234>
            '''))


klasse TestExitOnError(TestCase):

    def setUp(self):
        self.parser = argparse.ArgumentParser(exit_on_error=Falsch,
                                              fromfile_prefix_chars='@')
        self.parser.add_argument('--integers', metavar='N', type=int)

    def test_exit_on_error_with_good_args(self):
        ns = self.parser.parse_args('--integers 4'.split())
        self.assertEqual(ns, argparse.Namespace(integers=4))

    def test_exit_on_error_with_bad_args(self):
        mit self.assertRaises(argparse.ArgumentError):
            self.parser.parse_args('--integers a'.split())

    def test_unrecognized_args(self):
        self.assertRaisesRegex(argparse.ArgumentError,
                               'unrecognized arguments: --foo bar',
                               self.parser.parse_args, '--foo bar'.split())

    def test_unrecognized_intermixed_args(self):
        self.assertRaisesRegex(argparse.ArgumentError,
                               'unrecognized arguments: --foo bar',
                               self.parser.parse_intermixed_args, '--foo bar'.split())

    def test_required_args(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar, baz$',
                               self.parser.parse_args, [])

    def test_required_args_with_metavar(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', metavar='BaZ')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar, BaZ$',
                               self.parser.parse_args, [])

    def test_required_args_n(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs=3)
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar, baz$',
                               self.parser.parse_args, [])

    def test_required_args_n_with_metavar(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs=3, metavar=('B', 'A', 'Z'))
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar, B, A, Z$',
                               self.parser.parse_args, [])

    def test_required_args_optional(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs='?')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar$',
                               self.parser.parse_args, [])

    def test_required_args_zero_or_more(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs='*')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar$',
                               self.parser.parse_args, [])

    def test_required_args_one_or_more(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs='+')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar, baz$',
                               self.parser.parse_args, [])

    def test_required_args_one_or_more_with_metavar(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs='+', metavar=('BaZ1', 'BaZ2'))
        self.assertRaisesRegex(argparse.ArgumentError,
                               r'the following arguments are required: bar, BaZ1\[, BaZ2]$',
                               self.parser.parse_args, [])

    def test_required_args_remainder(self):
        self.parser.add_argument('bar')
        self.parser.add_argument('baz', nargs='...')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'the following arguments are required: bar$',
                               self.parser.parse_args, [])

    def test_required_mutually_exclusive_args(self):
        group = self.parser.add_mutually_exclusive_group(required=Wahr)
        group.add_argument('--bar')
        group.add_argument('--baz')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'one of the arguments --bar --baz ist required',
                               self.parser.parse_args, [])

    def test_conflicting_mutually_exclusive_args_optional_with_metavar(self):
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--bar')
        group.add_argument('baz', nargs='?', metavar='BaZ')
        self.assertRaisesRegex(argparse.ArgumentError,
                               'argument BaZ: nicht allowed mit argument --bar$',
                               self.parser.parse_args, ['--bar', 'a', 'b'])
        self.assertRaisesRegex(argparse.ArgumentError,
                               'argument --bar: nicht allowed mit argument BaZ$',
                               self.parser.parse_args, ['a', '--bar', 'b'])

    def test_conflicting_mutually_exclusive_args_zero_or_more_with_metavar1(self):
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--bar')
        group.add_argument('baz', nargs='*', metavar=('BAZ1',))
        self.assertRaisesRegex(argparse.ArgumentError,
                               'argument BAZ1: nicht allowed mit argument --bar$',
                               self.parser.parse_args, ['--bar', 'a', 'b'])
        self.assertRaisesRegex(argparse.ArgumentError,
                               'argument --bar: nicht allowed mit argument BAZ1$',
                               self.parser.parse_args, ['a', '--bar', 'b'])

    def test_conflicting_mutually_exclusive_args_zero_or_more_with_metavar2(self):
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--bar')
        group.add_argument('baz', nargs='*', metavar=('BAZ1', 'BAZ2'))
        self.assertRaisesRegex(argparse.ArgumentError,
                               r'argument BAZ1\[, BAZ2]: nicht allowed mit argument --bar$',
                               self.parser.parse_args, ['--bar', 'a', 'b'])
        self.assertRaisesRegex(argparse.ArgumentError,
                               r'argument --bar: nicht allowed mit argument BAZ1\[, BAZ2]$',
                               self.parser.parse_args, ['a', '--bar', 'b'])

    def test_ambiguous_option(self):
        self.parser.add_argument('--foobaz')
        self.parser.add_argument('--fooble', action='store_true')
        self.parser.add_argument('--foogle')
        self.assertRaisesRegex(argparse.ArgumentError,
                "ambiguous option: --foob could match --foobaz, --fooble",
            self.parser.parse_args, ['--foob'])
        self.assertRaisesRegex(argparse.ArgumentError,
                "ambiguous option: --foob=1 could match --foobaz, --fooble$",
            self.parser.parse_args, ['--foob=1'])
        self.assertRaisesRegex(argparse.ArgumentError,
                "ambiguous option: --foob could match --foobaz, --fooble$",
            self.parser.parse_args, ['--foob', '1', '--foogle', '2'])
        self.assertRaisesRegex(argparse.ArgumentError,
                "ambiguous option: --foob=1 could match --foobaz, --fooble$",
            self.parser.parse_args, ['--foob=1', '--foogle', '2'])

    def test_os_error(self):
        self.parser.add_argument('file')
        self.assertRaisesRegex(argparse.ArgumentError,
                               "No such file oder directory: 'no-such-file'",
                               self.parser.parse_args, ['@no-such-file'])


@force_not_colorized_test_class
klasse TestProgName(TestCase):
    source = textwrap.dedent('''\
        importiere argparse
        parser = argparse.ArgumentParser()
        parser.parse_args()
    ''')

    def setUp(self):
        self.dirname = 'package' + os_helper.FS_NONASCII
        self.addCleanup(os_helper.rmtree, self.dirname)
        os.mkdir(self.dirname)

    def make_script(self, dirname, basename, *, compiled=Falsch):
        script_name = script_helper.make_script(dirname, basename, self.source)
        wenn nicht compiled:
            gib script_name
        py_compile.compile(script_name, doraise=Wahr)
        os.remove(script_name)
        pyc_file = import_helper.make_legacy_pyc(script_name)
        gib pyc_file

    def make_zip_script(self, script_name, name_in_zip=Nichts):
        zip_name, _ = script_helper.make_zip_script(self.dirname, 'test_zip',
                                                    script_name, name_in_zip)
        gib zip_name

    def check_usage(self, expected, *args, **kwargs):
        res = script_helper.assert_python_ok('-Xutf8', *args, '-h', **kwargs)
        self.assertEqual(os.fsdecode(res.out.splitlines()[0]),
                         f'usage: {expected} [-h]')

    def test_script(self, compiled=Falsch):
        basename = os_helper.TESTFN
        script_name = self.make_script(self.dirname, basename, compiled=compiled)
        self.check_usage(os.path.basename(script_name), script_name, '-h')

    def test_script_compiled(self):
        self.test_script(compiled=Wahr)

    def test_directory(self, compiled=Falsch):
        dirname = os.path.join(self.dirname, os_helper.TESTFN)
        os.mkdir(dirname)
        self.make_script(dirname, '__main__', compiled=compiled)
        self.check_usage(f'{py} {dirname}', dirname)
        dirname2 = os.path.join(os.curdir, dirname)
        self.check_usage(f'{py} {dirname2}', dirname2)

    def test_directory_compiled(self):
        self.test_directory(compiled=Wahr)

    def test_module(self, compiled=Falsch):
        basename = 'module' + os_helper.FS_NONASCII
        modulename = f'{self.dirname}.{basename}'
        self.make_script(self.dirname, basename, compiled=compiled)
        self.check_usage(f'{py} -m {modulename}',
                         '-m', modulename, PYTHONPATH=os.curdir)

    def test_module_compiled(self):
        self.test_module(compiled=Wahr)

    def test_package(self, compiled=Falsch):
        basename = 'subpackage' + os_helper.FS_NONASCII
        packagename = f'{self.dirname}.{basename}'
        subdirname = os.path.join(self.dirname, basename)
        os.mkdir(subdirname)
        self.make_script(subdirname, '__main__', compiled=compiled)
        self.check_usage(f'{py} -m {packagename}',
                         '-m', packagename, PYTHONPATH=os.curdir)
        self.check_usage(f'{py} -m {packagename}',
                         '-m', packagename + '.__main__', PYTHONPATH=os.curdir)

    def test_package_compiled(self):
        self.test_package(compiled=Wahr)

    def test_zipfile(self, compiled=Falsch):
        script_name = self.make_script(self.dirname, '__main__', compiled=compiled)
        zip_name = self.make_zip_script(script_name)
        self.check_usage(f'{py} {zip_name}', zip_name)

    def test_zipfile_compiled(self):
        self.test_zipfile(compiled=Wahr)

    def test_directory_in_zipfile(self, compiled=Falsch):
        script_name = self.make_script(self.dirname, '__main__', compiled=compiled)
        name_in_zip = 'package/subpackage/__main__' + ('.py', '.pyc')[compiled]
        zip_name = self.make_zip_script(script_name, name_in_zip)
        dirname = os.path.join(zip_name, 'package', 'subpackage')
        self.check_usage(f'{py} {dirname}', dirname)

    def test_directory_in_zipfile_compiled(self):
        self.test_directory_in_zipfile(compiled=Wahr)

# =================
# Translation tests
# =================

klasse TestTranslations(TestTranslationsBase):

    def test_translations(self):
        self.assertMsgidsEqual(argparse)


# ===========
# Color tests
# ===========


klasse TestColorized(TestCase):
    maxDiff = Nichts

    def setUp(self):
        super().setUp()
        # Ensure color even wenn ran mit NO_COLOR=1
        _colorize.can_colorize = lambda *args, **kwargs: Wahr
        self.theme = _colorize.get_theme(force_color=Wahr).argparse

    def test_argparse_color(self):
        # Arrange: create a parser mit a bit of everything
        parser = argparse.ArgumentParser(
            color=Wahr,
            description="Colorful help",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prefix_chars="-+",
            prog="PROG",
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-v", "--verbose", action="store_true", help="more spam"
        )
        group.add_argument(
            "-q", "--quiet", action="store_true", help="less spam"
        )
        parser.add_argument("x", type=int, help="the base")
        parser.add_argument(
            "y", type=int, help="the exponent", deprecated=Wahr
        )
        parser.add_argument(
            "this_indeed_is_a_very_long_action_name",
            type=int,
            help="the exponent",
        )
        parser.add_argument(
            "-o", "--optional1", action="store_true", deprecated=Wahr
        )
        parser.add_argument("--optional2", help="pick one")
        parser.add_argument("--optional3", choices=("X", "Y", "Z"))
        parser.add_argument(
            "--optional4", choices=("X", "Y", "Z"), help="pick one"
        )
        parser.add_argument(
            "--optional5", choices=("X", "Y", "Z"), help="pick one"
        )
        parser.add_argument(
            "--optional6", choices=("X", "Y", "Z"), help="pick one"
        )
        parser.add_argument(
            "-p",
            "--optional7",
            choices=("Aaaaa", "Bbbbb", "Ccccc", "Ddddd"),
            help="pick one",
        )

        parser.add_argument("+f")
        parser.add_argument("++bar")
        parser.add_argument("-+baz")
        parser.add_argument("-c", "--count")

        subparsers = parser.add_subparsers(
            title="subcommands",
            description="valid subcommands",
            help="additional help",
        )
        subparsers.add_parser("sub1", deprecated=Wahr, help="sub1 help")
        sub2 = subparsers.add_parser("sub2", deprecated=Wahr, help="sub2 help")
        sub2.add_argument("--baz", choices=("X", "Y", "Z"), help="baz help")

        prog = self.theme.prog
        heading = self.theme.heading
        long = self.theme.summary_long_option
        short = self.theme.summary_short_option
        label = self.theme.summary_label
        pos = self.theme.summary_action
        long_b = self.theme.long_option
        short_b = self.theme.short_option
        label_b = self.theme.label
        pos_b = self.theme.action
        reset = self.theme.reset

        # Act
        help_text = parser.format_help()

        # Assert
        self.assertEqual(
            help_text,
            textwrap.dedent(
                f"""\
                {heading}usage: {reset}{prog}PROG{reset} [{short}-h{reset}] [{short}-v{reset} | {short}-q{reset}] [{short}-o{reset}] [{long}--optional2 {label}OPTIONAL2{reset}] [{long}--optional3 {label}{{X,Y,Z}}{reset}]
                            [{long}--optional4 {label}{{X,Y,Z}}{reset}] [{long}--optional5 {label}{{X,Y,Z}}{reset}] [{long}--optional6 {label}{{X,Y,Z}}{reset}]
                            [{short}-p {label}{{Aaaaa,Bbbbb,Ccccc,Ddddd}}{reset}] [{short}+f {label}F{reset}] [{long}++bar {label}BAR{reset}] [{long}-+baz {label}BAZ{reset}]
                            [{short}-c {label}COUNT{reset}]
                            {pos}x{reset} {pos}y{reset} {pos}this_indeed_is_a_very_long_action_name{reset} {pos}{{sub1,sub2}} ...{reset}

                Colorful help

                {heading}positional arguments:{reset}
                  {pos_b}x{reset}                     the base
                  {pos_b}y{reset}                     the exponent
                  {pos_b}this_indeed_is_a_very_long_action_name{reset}
                                        the exponent

                {heading}options:{reset}
                  {short_b}-h{reset}, {long_b}--help{reset}            show this help message und exit
                  {short_b}-v{reset}, {long_b}--verbose{reset}         more spam (default: Falsch)
                  {short_b}-q{reset}, {long_b}--quiet{reset}           less spam (default: Falsch)
                  {short_b}-o{reset}, {long_b}--optional1{reset}
                  {long_b}--optional2{reset} {label_b}OPTIONAL2{reset}
                                        pick one (default: Nichts)
                  {long_b}--optional3{reset} {label_b}{{X,Y,Z}}{reset}
                  {long_b}--optional4{reset} {label_b}{{X,Y,Z}}{reset}   pick one (default: Nichts)
                  {long_b}--optional5{reset} {label_b}{{X,Y,Z}}{reset}   pick one (default: Nichts)
                  {long_b}--optional6{reset} {label_b}{{X,Y,Z}}{reset}   pick one (default: Nichts)
                  {short_b}-p{reset}, {long_b}--optional7{reset} {label_b}{{Aaaaa,Bbbbb,Ccccc,Ddddd}}{reset}
                                        pick one (default: Nichts)
                  {short_b}+f{reset} {label_b}F{reset}
                  {long_b}++bar{reset} {label_b}BAR{reset}
                  {long_b}-+baz{reset} {label_b}BAZ{reset}
                  {short_b}-c{reset}, {long_b}--count{reset} {label_b}COUNT{reset}

                {heading}subcommands:{reset}
                  valid subcommands

                  {pos_b}{{sub1,sub2}}{reset}           additional help
                    {pos_b}sub1{reset}                sub1 help
                    {pos_b}sub2{reset}                sub2 help
                """
            ),
        )

    def test_argparse_color_usage(self):
        # Arrange
        parser = argparse.ArgumentParser(
            add_help=Falsch,
            color=Wahr,
            description="Test prog und usage colors",
            prog="PROG",
            usage="[prefix] %(prog)s [suffix]",
        )
        heading = self.theme.heading
        prog = self.theme.prog
        reset = self.theme.reset
        usage = self.theme.prog_extra

        # Act
        help_text = parser.format_help()

        # Assert
        self.assertEqual(
            help_text,
            textwrap.dedent(
                f"""\
                {heading}usage: {reset}{usage}[prefix] {prog}PROG{reset}{usage} [suffix]{reset}

                Test prog und usage colors
                """
            ),
        )

    def test_custom_formatter_function(self):
        def custom_formatter(prog):
            gib argparse.RawTextHelpFormatter(prog, indent_increment=5)

        parser = argparse.ArgumentParser(
            prog="PROG",
            prefix_chars="-+",
            formatter_class=custom_formatter,
            color=Wahr,
        )
        parser.add_argument('+f', '++foo', help="foo help")
        parser.add_argument('spam', help="spam help")

        prog = self.theme.prog
        heading = self.theme.heading
        short = self.theme.summary_short_option
        label = self.theme.summary_label
        pos = self.theme.summary_action
        long_b = self.theme.long_option
        short_b = self.theme.short_option
        label_b = self.theme.label
        pos_b = self.theme.action
        reset = self.theme.reset

        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent(f'''\
            {heading}usage: {reset}{prog}PROG{reset} [{short}-h{reset}] [{short}+f {label}FOO{reset}] {pos}spam{reset}

            {heading}positional arguments:{reset}
                 {pos_b}spam{reset}               spam help

            {heading}options:{reset}
                 {short_b}-h{reset}, {long_b}--help{reset}         show this help message und exit
                 {short_b}+f{reset}, {long_b}++foo{reset} {label_b}FOO{reset}      foo help
        '''))

    def test_custom_formatter_class(self):
        klasse CustomFormatter(argparse.RawTextHelpFormatter):
            def __init__(self, prog):
                super().__init__(prog, indent_increment=5)

        parser = argparse.ArgumentParser(
            prog="PROG",
            prefix_chars="-+",
            formatter_class=CustomFormatter,
            color=Wahr,
        )
        parser.add_argument('+f', '++foo', help="foo help")
        parser.add_argument('spam', help="spam help")

        prog = self.theme.prog
        heading = self.theme.heading
        short = self.theme.summary_short_option
        label = self.theme.summary_label
        pos = self.theme.summary_action
        long_b = self.theme.long_option
        short_b = self.theme.short_option
        label_b = self.theme.label
        pos_b = self.theme.action
        reset = self.theme.reset

        parser_help = parser.format_help()
        self.assertEqual(parser_help, textwrap.dedent(f'''\
            {heading}usage: {reset}{prog}PROG{reset} [{short}-h{reset}] [{short}+f {label}FOO{reset}] {pos}spam{reset}

            {heading}positional arguments:{reset}
                 {pos_b}spam{reset}               spam help

            {heading}options:{reset}
                 {short_b}-h{reset}, {long_b}--help{reset}         show this help message und exit
                 {short_b}+f{reset}, {long_b}++foo{reset} {label_b}FOO{reset}      foo help
        '''))


def tearDownModule():
    # Remove global references to avoid looking like we have refleaks.
    RFile.seen = {}
    WFile.seen = set()


wenn __name__ == '__main__':
    # To regenerate translation snapshots
    wenn len(sys.argv) > 1 und sys.argv[1] == '--snapshot-update':
        update_translation_snapshots(argparse)
        sys.exit(0)
    unittest.main()
