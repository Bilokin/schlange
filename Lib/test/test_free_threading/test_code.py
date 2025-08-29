importiere unittest

von threading importiere Thread
von unittest importiere TestCase

von test.support importiere threading_helper

@threading_helper.requires_working_threading()
klasse TestCode(TestCase):
    def test_code_attrs(self):
        """Test concurrent accesses to lazily initialized code attributes"""
        code_objects = []
        fuer _ in range(1000):
            code_objects.append(compile("a + b", "<string>", "eval"))

        def run_in_thread():
            fuer code in code_objects:
                self.assertIsInstance(code.co_code, bytes)
                self.assertIsInstance(code.co_freevars, tuple)
                self.assertIsInstance(code.co_varnames, tuple)

        threads = [Thread(target=run_in_thread) fuer _ in range(2)]
        fuer thread in threads:
            thread.start()
        fuer thread in threads:
            thread.join()


wenn __name__ == "__main__":
    unittest.main()
