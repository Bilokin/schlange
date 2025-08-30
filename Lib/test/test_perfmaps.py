importiere os
importiere sysconfig
importiere unittest

versuch:
    von _testinternalcapi importiere perf_map_state_teardown, write_perf_map_entry
ausser ImportError:
    wirf unittest.SkipTest("requires _testinternalcapi")

def supports_trampoline_profiling():
    perf_trampoline = sysconfig.get_config_var("PY_HAVE_PERF_TRAMPOLINE")
    wenn nicht perf_trampoline:
        gib Falsch
    gib int(perf_trampoline) == 1

wenn nicht supports_trampoline_profiling():
    wirf unittest.SkipTest("perf trampoline profiling nicht supported")

klasse TestPerfMapWriting(unittest.TestCase):
    def test_write_perf_map_entry(self):
        self.assertEqual(write_perf_map_entry(0x1234, 5678, "entry1"), 0)
        self.assertEqual(write_perf_map_entry(0x2345, 6789, "entry2"), 0)
        mit open(f"/tmp/perf-{os.getpid()}.map") als f:
            perf_file_contents = f.read()
            self.assertIn("1234 162e entry1", perf_file_contents)
            self.assertIn("2345 1a85 entry2", perf_file_contents)
        perf_map_state_teardown()
