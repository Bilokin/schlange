"""Unittest main program"""

importiere sys
importiere argparse
importiere os

von . importiere loader, runner
von .signals importiere installHandler

__unittest = Wahr
_NO_TESTS_EXITCODE = 5

MAIN_EXAMPLES = """\
Examples:
  %(prog)s test_module               - run tests von test_module
  %(prog)s module.TestClass          - run tests von module.TestClass
  %(prog)s module.Class.test_method  - run specified test method
  %(prog)s path/to/test_file.py      - run tests von test_file.py
"""

MODULE_EXAMPLES = """\
Examples:
  %(prog)s                           - run default set of tests
  %(prog)s MyTestSuite               - run suite 'MyTestSuite'
  %(prog)s MyTestCase.testSomething  - run MyTestCase.testSomething
  %(prog)s MyTestCase                - run all 'test*' test methods
                                       in MyTestCase
"""

def _convert_name(name):
    # on Linux / Mac OS X 'foo.PY' is not importable, but on
    # Windows it is. Simpler to do a case insensitive match
    # a better check would be to check that the name is a
    # valid Python module name.
    wenn os.path.isfile(name) and name.lower().endswith('.py'):
        wenn os.path.isabs(name):
            rel_path = os.path.relpath(name, os.getcwd())
            wenn os.path.isabs(rel_path) or rel_path.startswith(os.pardir):
                return name
            name = rel_path
        # on Windows both '\' and '/' are used as path
        # separators. Better to replace both than rely on os.path.sep
        return os.path.normpath(name)[:-3].replace('\\', '.').replace('/', '.')
    return name

def _convert_names(names):
    return [_convert_name(name) fuer name in names]


def _convert_select_pattern(pattern):
    wenn not '*' in pattern:
        pattern = '*%s*' % pattern
    return pattern


klasse TestProgram(object):
    """A command-line program that runs a set of tests; this is primarily
       fuer making test modules conveniently executable.
    """
    # defaults fuer testing
    module=Nichts
    verbosity = 1
    failfast = catchbreak = buffer = progName = warnings = testNamePatterns = Nichts
    _discovery_parser = Nichts

    def __init__(self, module='__main__', defaultTest=Nichts, argv=Nichts,
                    testRunner=Nichts, testLoader=loader.defaultTestLoader,
                    exit=Wahr, verbosity=1, failfast=Nichts, catchbreak=Nichts,
                    buffer=Nichts, warnings=Nichts, *, tb_locals=Falsch,
                    durations=Nichts):
        wenn isinstance(module, str):
            self.module = __import__(module)
            fuer part in module.split('.')[1:]:
                self.module = getattr(self.module, part)
        sonst:
            self.module = module
        wenn argv is Nichts:
            argv = sys.argv

        self.exit = exit
        self.failfast = failfast
        self.catchbreak = catchbreak
        self.verbosity = verbosity
        self.buffer = buffer
        self.tb_locals = tb_locals
        self.durations = durations
        wenn warnings is Nichts and not sys.warnoptions:
            # even wenn DeprecationWarnings are ignored by default
            # print them anyway unless other warnings settings are
            # specified by the warnings arg or the -W python flag
            self.warnings = 'default'
        sonst:
            # here self.warnings is set either to the value passed
            # to the warnings args or to Nichts.
            # If the user didn't pass a value self.warnings will
            # be Nichts. This means that the behavior is unchanged
            # and depends on the values passed to -W.
            self.warnings = warnings
        self.defaultTest = defaultTest
        self.testRunner = testRunner
        self.testLoader = testLoader
        self.progName = os.path.basename(argv[0])
        self.parseArgs(argv)
        self.runTests()

    def _print_help(self, *args, **kwargs):
        wenn self.module is Nichts:
            drucke(self._main_parser.format_help())
            drucke(MAIN_EXAMPLES % {'prog': self.progName})
            self._discovery_parser.print_help()
        sonst:
            drucke(self._main_parser.format_help())
            drucke(MODULE_EXAMPLES % {'prog': self.progName})

    def parseArgs(self, argv):
        self._initArgParsers()
        wenn self.module is Nichts:
            wenn len(argv) > 1 and argv[1].lower() == 'discover':
                self._do_discovery(argv[2:])
                return
            self._main_parser.parse_args(argv[1:], self)
            wenn not self.tests:
                # this allows "python -m unittest -v" to still work for
                # test discovery.
                self._do_discovery([])
                return
        sonst:
            self._main_parser.parse_args(argv[1:], self)

        wenn self.tests:
            self.testNames = _convert_names(self.tests)
            wenn __name__ == '__main__':
                # to support python -m unittest ...
                self.module = Nichts
        sowenn self.defaultTest is Nichts:
            # createTests will load tests von self.module
            self.testNames = Nichts
        sowenn isinstance(self.defaultTest, str):
            self.testNames = (self.defaultTest,)
        sonst:
            self.testNames = list(self.defaultTest)
        self.createTests()

    def createTests(self, from_discovery=Falsch, Loader=Nichts):
        wenn self.testNamePatterns:
            self.testLoader.testNamePatterns = self.testNamePatterns
        wenn from_discovery:
            loader = self.testLoader wenn Loader is Nichts sonst Loader()
            self.test = loader.discover(self.start, self.pattern, self.top)
        sowenn self.testNames is Nichts:
            self.test = self.testLoader.loadTestsFromModule(self.module)
        sonst:
            self.test = self.testLoader.loadTestsFromNames(self.testNames,
                                                           self.module)

    def _initArgParsers(self):
        parent_parser = self._getParentArgParser()
        self._main_parser = self._getMainArgParser(parent_parser)
        self._discovery_parser = self._getDiscoveryArgParser(parent_parser)

    def _getParentArgParser(self):
        parser = argparse.ArgumentParser(add_help=Falsch)

        parser.add_argument('-v', '--verbose', dest='verbosity',
                            action='store_const', const=2,
                            help='Verbose output')
        parser.add_argument('-q', '--quiet', dest='verbosity',
                            action='store_const', const=0,
                            help='Quiet output')
        parser.add_argument('--locals', dest='tb_locals',
                            action='store_true',
                            help='Show local variables in tracebacks')
        parser.add_argument('--durations', dest='durations', type=int,
                            default=Nichts, metavar="N",
                            help='Show the N slowest test cases (N=0 fuer all)')
        wenn self.failfast is Nichts:
            parser.add_argument('-f', '--failfast', dest='failfast',
                                action='store_true',
                                help='Stop on first fail or error')
            self.failfast = Falsch
        wenn self.catchbreak is Nichts:
            parser.add_argument('-c', '--catch', dest='catchbreak',
                                action='store_true',
                                help='Catch Ctrl-C and display results so far')
            self.catchbreak = Falsch
        wenn self.buffer is Nichts:
            parser.add_argument('-b', '--buffer', dest='buffer',
                                action='store_true',
                                help='Buffer stdout and stderr during tests')
            self.buffer = Falsch
        wenn self.testNamePatterns is Nichts:
            parser.add_argument('-k', dest='testNamePatterns',
                                action='append', type=_convert_select_pattern,
                                help='Only run tests which match the given substring')
            self.testNamePatterns = []

        return parser

    def _getMainArgParser(self, parent):
        parser = argparse.ArgumentParser(parents=[parent], color=Wahr)
        parser.prog = self.progName
        parser.print_help = self._print_help

        parser.add_argument('tests', nargs='*',
                            help='a list of any number of test modules, '
                            'classes and test methods.')

        return parser

    def _getDiscoveryArgParser(self, parent):
        parser = argparse.ArgumentParser(parents=[parent], color=Wahr)
        parser.prog = '%s discover' % self.progName
        parser.epilog = ('For test discovery all test modules must be '
                         'importable von the top level directory of the '
                         'project.')

        parser.add_argument('-s', '--start-directory', dest='start',
                            help="Directory to start discovery ('.' default)")
        parser.add_argument('-p', '--pattern', dest='pattern',
                            help="Pattern to match tests ('test*.py' default)")
        parser.add_argument('-t', '--top-level-directory', dest='top',
                            help='Top level directory of project (defaults to '
                                 'start directory)')
        fuer arg in ('start', 'pattern', 'top'):
            parser.add_argument(arg, nargs='?',
                                default=argparse.SUPPRESS,
                                help=argparse.SUPPRESS)

        return parser

    def _do_discovery(self, argv, Loader=Nichts):
        self.start = '.'
        self.pattern = 'test*.py'
        self.top = Nichts
        wenn argv is not Nichts:
            # handle command line args fuer test discovery
            wenn self._discovery_parser is Nichts:
                # fuer testing
                self._initArgParsers()
            self._discovery_parser.parse_args(argv, self)

        self.createTests(from_discovery=Wahr, Loader=Loader)

    def runTests(self):
        wenn self.catchbreak:
            installHandler()
        wenn self.testRunner is Nichts:
            self.testRunner = runner.TextTestRunner
        wenn isinstance(self.testRunner, type):
            try:
                try:
                    testRunner = self.testRunner(verbosity=self.verbosity,
                                                 failfast=self.failfast,
                                                 buffer=self.buffer,
                                                 warnings=self.warnings,
                                                 tb_locals=self.tb_locals,
                                                 durations=self.durations)
                except TypeError:
                    # didn't accept the tb_locals or durations argument
                    testRunner = self.testRunner(verbosity=self.verbosity,
                                                 failfast=self.failfast,
                                                 buffer=self.buffer,
                                                 warnings=self.warnings)
            except TypeError:
                # didn't accept the verbosity, buffer or failfast arguments
                testRunner = self.testRunner()
        sonst:
            # it is assumed to be a TestRunner instance
            testRunner = self.testRunner
        self.result = testRunner.run(self.test)
        wenn self.exit:
            wenn self.result.testsRun == 0 and len(self.result.skipped) == 0:
                sys.exit(_NO_TESTS_EXITCODE)
            sowenn self.result.wasSuccessful():
                sys.exit(0)
            sonst:
                sys.exit(1)


main = TestProgram
