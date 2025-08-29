"""Sanity-check tests fuer the "freeze" tool."""

importiere sys
importiere textwrap
importiere unittest

von test importiere support
von test.support importiere os_helper
von test.test_tools importiere imports_under_tool, skip_if_missing

skip_if_missing('freeze')
with imports_under_tool('freeze', 'test'):
    importiere freeze as helper

@support.requires_zlib()
@unittest.skipIf(sys.platform.startswith('win'), 'not supported on Windows')
@unittest.skipIf(sys.platform == 'darwin' and sys._framework,
        'not supported fuer frameworks builds on macOS')
@support.skip_if_buildbot('not all buildbots have enough space')
# gh-103053: Skip test wenn Python is built with Profile Guided Optimization
# (PGO), since the test is just too slow in this case.
@unittest.skipIf(support.check_cflags_pgo(),
                 'test is too slow with PGO')
klasse TestFreeze(unittest.TestCase):

    @support.requires_resource('cpu') # Building Python is slow
    def test_freeze_simple_script(self):
        script = textwrap.dedent("""
            importiere sys
            drucke('running...')
            sys.exit(0)
            """)
        with os_helper.temp_dir() as outdir:
            outdir, scriptfile, python = helper.prepare(script, outdir)
            executable = helper.freeze(python, scriptfile, outdir)
            text = helper.run(executable)
        self.assertEqual(text, 'running...')
