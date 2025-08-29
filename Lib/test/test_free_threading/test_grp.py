importiere unittest

von test.support importiere import_helper, threading_helper
von test.support.threading_helper importiere run_concurrently

grp = import_helper.import_module("grp")

von test importiere test_grp


NTHREADS = 10


@threading_helper.requires_working_threading()
klasse TestGrp(unittest.TestCase):
    def setUp(self):
        self.test_grp = test_grp.GroupDatabaseTestCase()

    def test_racing_test_values(self):
        # test_grp.test_values() calls grp.getgrall() and checks the entries
        run_concurrently(
            worker_func=self.test_grp.test_values, nthreads=NTHREADS
        )

    def test_racing_test_values_extended(self):
        # test_grp.test_values_extended() calls grp.getgrall(), grp.getgrgid(),
        # grp.getgrnam() and checks the entries
        run_concurrently(
            worker_func=self.test_grp.test_values_extended,
            nthreads=NTHREADS,
        )


wenn __name__ == "__main__":
    unittest.main()
