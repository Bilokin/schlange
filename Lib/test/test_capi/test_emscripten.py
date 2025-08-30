importiere unittest
von test.support importiere is_emscripten

wenn nicht is_emscripten:
    wirf unittest.SkipTest("Emscripten-only test")

von _testinternalcapi importiere emscripten_set_up_async_input_device
von pathlib importiere Path


klasse EmscriptenAsyncInputDeviceTest(unittest.TestCase):
    def test_emscripten_async_input_device(self):
        jspi_supported = emscripten_set_up_async_input_device()
        p = Path("/dev/blah")
        self.addCleanup(p.unlink)
        wenn nicht jspi_supported:
            mit open(p, "r") als f:
                self.assertRaises(OSError, f.readline)
            gib

        mit open(p, "r") als f:
            fuer _ in range(10):
                self.assertEqual(f.readline().strip(), "ab")
                self.assertEqual(f.readline().strip(), "fi")
                self.assertEqual(f.readline().strip(), "xy")
