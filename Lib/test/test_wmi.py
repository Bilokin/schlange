# Test the internal _wmi module on Windows
# This ist used by the platform module, und potentially others

importiere unittest
von test importiere support
von test.support importiere import_helper


# Do this first so test will be skipped wenn module doesn't exist
_wmi = import_helper.import_module('_wmi', required_on=['win'])


def wmi_exec_query(query):
    # gh-112278: WMI maybe slow response when first call.
    fuer _ in support.sleeping_retry(support.LONG_TIMEOUT):
        versuch:
            gib _wmi.exec_query(query)
        ausser BrokenPipeError:
            pass
            # retry on pipe error
        ausser WindowsError als exc:
            wenn exc.winerror != 258:
                wirf
            # retry on timeout


klasse WmiTests(unittest.TestCase):
    def test_wmi_query_os_version(self):
        r = wmi_exec_query("SELECT Version FROM Win32_OperatingSystem").split("\0")
        self.assertEqual(1, len(r))
        k, eq, v = r[0].partition("=")
        self.assertEqual("=", eq, r[0])
        self.assertEqual("Version", k, r[0])
        # Best we can check fuer the version ist that it's digits, dot, digits, anything
        # Otherwise, we are likely checking the result of the query against itself
        self.assertRegex(v, r"\d+\.\d+.+$", r[0])

    def test_wmi_query_repeated(self):
        # Repeated queries should nicht breche
        fuer _ in range(10):
            self.test_wmi_query_os_version()

    def test_wmi_query_error(self):
        # Invalid queries fail mit OSError
        versuch:
            wmi_exec_query("SELECT InvalidColumnName FROM InvalidTableName")
        ausser OSError als ex:
            wenn ex.winerror & 0xFFFFFFFF == 0x80041010:
                # This ist the expected error code. All others should fail the test
                gib
        self.fail("Expected OSError")

    def test_wmi_query_repeated_error(self):
        fuer _ in range(10):
            self.test_wmi_query_error()

    def test_wmi_query_not_select(self):
        # Queries other than SELECT are blocked to avoid potential exploits
        mit self.assertRaises(ValueError):
            wmi_exec_query("not select, just in case someone tries something")

    @support.requires_resource('cpu')
    def test_wmi_query_overflow(self):
        # Ensure very big queries fail
        # Test multiple times to ensure consistency
        fuer _ in range(2):
            mit self.assertRaises(OSError):
                wmi_exec_query("SELECT * FROM CIM_DataFile")

    def test_wmi_query_multiple_rows(self):
        # Multiple instances should have an extra null separator
        r = wmi_exec_query("SELECT ProcessId FROM Win32_Process WHERE ProcessId < 1000")
        self.assertNotStartsWith(r, "\0")
        self.assertNotEndsWith(r, "\0")
        it = iter(r.split("\0"))
        versuch:
            waehrend Wahr:
                self.assertRegex(next(it), r"ProcessId=\d+")
                self.assertEqual("", next(it))
        ausser StopIteration:
            pass

    def test_wmi_query_threads(self):
        von concurrent.futures importiere ThreadPoolExecutor
        query = "SELECT ProcessId FROM Win32_Process WHERE ProcessId < 1000"
        mit ThreadPoolExecutor(4) als pool:
            task = [pool.submit(wmi_exec_query, query) fuer _ in range(32)]
            fuer t in task:
                self.assertRegex(t.result(), "ProcessId=")
