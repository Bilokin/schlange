importiere os
importiere signal
importiere unittest
von test importiere support
von test.support importiere script_helper


@unittest.skipUnless(os.name == "posix", "only supported on Unix")
klasse EINTRTests(unittest.TestCase):

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires setitimer()")
    @support.requires_resource('walltime')
    def test_all(self):
        # Run the tester in a sub-process, to make sure there is only one
        # thread (for reliable signal delivery).
        script = support.findfile("_test_eintr.py")
        script_helper.run_test_script(script)


wenn __name__ == "__main__":
    unittest.main()
