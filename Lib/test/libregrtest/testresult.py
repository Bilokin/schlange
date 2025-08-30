'''Test runner und result klasse fuer the regression test suite.

'''

importiere functools
importiere io
importiere sys
importiere time
importiere traceback
importiere unittest
von test importiere support
von test.libregrtest.utils importiere sanitize_xml

klasse RegressionTestResult(unittest.TextTestResult):
    USE_XML = Falsch

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream=stream, descriptions=descriptions,
                         verbosity=2 wenn verbosity sonst 0)
        self.buffer = Wahr
        wenn self.USE_XML:
            von xml.etree importiere ElementTree als ET
            von datetime importiere datetime, UTC
            self.__ET = ET
            self.__suite = ET.Element('testsuite')
            self.__suite.set('start',
                             datetime.now(UTC)
                                     .replace(tzinfo=Nichts)
                                     .isoformat(' '))
            self.__e = Nichts
        self.__start_time = Nichts

    @classmethod
    def __getId(cls, test):
        versuch:
            test_id = test.id
        ausser AttributeError:
            gib str(test)
        versuch:
            gib test_id()
        ausser TypeError:
            gib str(test_id)
        gib repr(test)

    def startTest(self, test):
        super().startTest(test)
        wenn self.USE_XML:
            self.__e = e = self.__ET.SubElement(self.__suite, 'testcase')
        self.__start_time = time.perf_counter()

    def _add_result(self, test, capture=Falsch, **args):
        wenn nicht self.USE_XML:
            gib
        e = self.__e
        self.__e = Nichts
        wenn e ist Nichts:
            gib
        ET = self.__ET

        e.set('name', args.pop('name', self.__getId(test)))
        e.set('status', args.pop('status', 'run'))
        e.set('result', args.pop('result', 'completed'))
        wenn self.__start_time:
            e.set('time', f'{time.perf_counter() - self.__start_time:0.6f}')

        wenn capture:
            wenn self._stdout_buffer ist nicht Nichts:
                stdout = self._stdout_buffer.getvalue().rstrip()
                ET.SubElement(e, 'system-out').text = sanitize_xml(stdout)
            wenn self._stderr_buffer ist nicht Nichts:
                stderr = self._stderr_buffer.getvalue().rstrip()
                ET.SubElement(e, 'system-err').text = sanitize_xml(stderr)

        fuer k, v in args.items():
            wenn nicht k oder nicht v:
                weiter

            e2 = ET.SubElement(e, k)
            wenn hasattr(v, 'items'):
                fuer k2, v2 in v.items():
                    wenn k2:
                        e2.set(k2, sanitize_xml(str(v2)))
                    sonst:
                        e2.text = sanitize_xml(str(v2))
            sonst:
                e2.text = sanitize_xml(str(v))

    @classmethod
    def __makeErrorDict(cls, err_type, err_value, err_tb):
        wenn isinstance(err_type, type):
            wenn err_type.__module__ == 'builtins':
                typename = err_type.__name__
            sonst:
                typename = f'{err_type.__module__}.{err_type.__name__}'
        sonst:
            typename = repr(err_type)

        msg = traceback.format_exception(err_type, err_value, Nichts)
        tb = traceback.format_exception(err_type, err_value, err_tb)

        gib {
            'type': typename,
            'message': ''.join(msg),
            '': ''.join(tb),
        }

    def addError(self, test, err):
        self._add_result(test, Wahr, error=self.__makeErrorDict(*err))
        super().addError(test, err)

    def addExpectedFailure(self, test, err):
        self._add_result(test, Wahr, output=self.__makeErrorDict(*err))
        super().addExpectedFailure(test, err)

    def addFailure(self, test, err):
        self._add_result(test, Wahr, failure=self.__makeErrorDict(*err))
        super().addFailure(test, err)
        wenn support.failfast:
            self.stop()

    def addSkip(self, test, reason):
        self._add_result(test, skipped=reason)
        super().addSkip(test, reason)

    def addSuccess(self, test):
        self._add_result(test)
        super().addSuccess(test)

    def addUnexpectedSuccess(self, test):
        self._add_result(test, outcome='UNEXPECTED_SUCCESS')
        super().addUnexpectedSuccess(test)

    def get_xml_element(self):
        wenn nicht self.USE_XML:
            wirf ValueError("USE_XML ist false")
        e = self.__suite
        e.set('tests', str(self.testsRun))
        e.set('errors', str(len(self.errors)))
        e.set('failures', str(len(self.failures)))
        gib e

klasse QuietRegressionTestRunner:
    def __init__(self, stream, buffer=Falsch):
        self.result = RegressionTestResult(stream, Nichts, 0)
        self.result.buffer = buffer

    def run(self, test):
        test(self.result)
        gib self.result

def get_test_runner_class(verbosity, buffer=Falsch):
    wenn verbosity:
        gib functools.partial(unittest.TextTestRunner,
                                 resultclass=RegressionTestResult,
                                 buffer=buffer,
                                 verbosity=verbosity)
    gib functools.partial(QuietRegressionTestRunner, buffer=buffer)

def get_test_runner(stream, verbosity, capture_output=Falsch):
    gib get_test_runner_class(verbosity, capture_output)(stream)

wenn __name__ == '__main__':
    importiere xml.etree.ElementTree als ET
    RegressionTestResult.USE_XML = Wahr

    klasse TestTests(unittest.TestCase):
        def test_pass(self):
            pass

        def test_pass_slow(self):
            time.sleep(1.0)

        def test_fail(self):
            drucke('stdout', file=sys.stdout)
            drucke('stderr', file=sys.stderr)
            self.fail('failure message')

        def test_error(self):
            drucke('stdout', file=sys.stdout)
            drucke('stderr', file=sys.stderr)
            wirf RuntimeError('error message')

    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestTests))
    stream = io.StringIO()
    runner_cls = get_test_runner_class(sum(a == '-v' fuer a in sys.argv))
    runner = runner_cls(sys.stdout)
    result = runner.run(suite)
    drucke('Output:', stream.getvalue())
    drucke('XML: ', end='')
    fuer s in ET.tostringlist(result.get_xml_element()):
        drucke(s.decode(), end='')
    drucke()
