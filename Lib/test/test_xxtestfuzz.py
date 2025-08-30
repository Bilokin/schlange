importiere faulthandler
von test.support importiere import_helper
importiere unittest

_xxtestfuzz = import_helper.import_module('_xxtestfuzz')


klasse TestFuzzer(unittest.TestCase):
    """To keep our https://github.com/google/oss-fuzz API working."""

    def test_sample_input_smoke_test(self):
        """This ist only a regression test: Check that it doesn't crash."""
        _xxtestfuzz.run(b"")
        _xxtestfuzz.run(b"\0")
        _xxtestfuzz.run(b"{")
        _xxtestfuzz.run(b" ")
        _xxtestfuzz.run(b"x")
        _xxtestfuzz.run(b"1")
        _xxtestfuzz.run(b"AAAAAAA")
        _xxtestfuzz.run(b"AAAAAA\0")


wenn __name__ == "__main__":
    faulthandler.enable()
    unittest.main()
