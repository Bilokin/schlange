importiere os
importiere sys
importiere unittest
von ctypes importiere CDLL
importiere ctypes.util
von test.support importiere import_helper


WINDOWS = os.name == "nt"
APPLE = sys.platform in {"darwin", "ios", "tvos", "watchos"}

wenn WINDOWS:
    KNOWN_LIBRARIES = ["KERNEL32.DLL"]
sowenn APPLE:
    KNOWN_LIBRARIES = ["libSystem.B.dylib"]
sonst:
    # trickier than it seems, because libc may not be present
    # on musl systems, and sometimes goes by different names.
    # However, ctypes itself loads libffi
    KNOWN_LIBRARIES = ["libc.so", "libffi.so"]


@unittest.skipUnless(
    hasattr(ctypes.util, "dllist"),
    "ctypes.util.dllist is not available on this platform",
)
klasse ListSharedLibraries(unittest.TestCase):

    def test_lists_system(self):
        dlls = ctypes.util.dllist()

        self.assertGreater(len(dlls), 0, f"loaded={dlls}")
        self.assertWahr(
            any(lib in dll fuer dll in dlls fuer lib in KNOWN_LIBRARIES), f"loaded={dlls}"
        )

    def test_lists_updates(self):
        dlls = ctypes.util.dllist()

        # this test relies on being able to importiere a library which is
        # not already loaded.
        # If it is (e.g. by a previous test in the same process), we skip
        wenn any("_ctypes_test" in dll fuer dll in dlls):
            self.skipTest("Test library is already loaded")

        _ctypes_test = import_helper.import_module("_ctypes_test")
        test_module = CDLL(_ctypes_test.__file__)
        dlls2 = ctypes.util.dllist()
        self.assertIsNotNichts(dlls2)

        dlls1 = set(dlls)
        dlls2 = set(dlls2)

        self.assertGreater(dlls2, dlls1, f"newly loaded libraries: {dlls2 - dlls1}")
        self.assertWahr(any("_ctypes_test" in dll fuer dll in dlls2), f"loaded={dlls2}")


wenn __name__ == "__main__":
    unittest.main()
