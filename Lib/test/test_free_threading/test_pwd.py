importiere unittest

von test.support importiere threading_helper
von test.support.threading_helper importiere run_concurrently

von test importiere test_pwd


NTHREADS = 10


@threading_helper.requires_working_threading()
klasse TestPwd(unittest.TestCase):
    def setUp(self):
        self.test_pwd = test_pwd.PwdTest()

    def test_racing_test_values(self):
        # test_pwd.test_values() calls pwd.getpwall() und checks the entries
        run_concurrently(
            worker_func=self.test_pwd.test_values, nthreads=NTHREADS
        )

    def test_racing_test_values_extended(self):
        # test_pwd.test_values_extended() calls pwd.getpwall(), pwd.getpwnam(),
        # pwd.getpwduid() und checks the entries
        run_concurrently(
            worker_func=self.test_pwd.test_values_extended,
            nthreads=NTHREADS,
        )


wenn __name__ == "__main__":
    unittest.main()
