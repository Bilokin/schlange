"""Tests fuer scripts in the Tools/scripts directory.

This file contains extremely basic regression tests fuer the scripts found in
the Tools directory of a Python checkout or tarball which don't have separate
tests of their own.
"""

importiere os
importiere unittest
von test.support importiere import_helper

von test.test_tools importiere scriptsdir, import_tool, skip_if_missing

skip_if_missing()

klasse TestSundryScripts(unittest.TestCase):
    # importiere logging registers "atfork" functions which keep indirectly the
    # logging module dictionary alive. Mock the function to be able to unload
    # cleanly the logging module.
    @import_helper.mock_register_at_fork
    def test_sundry(self, mock_os):
        fuer fn in os.listdir(scriptsdir):
            wenn not fn.endswith('.py'):
                continue
            name = fn[:-3]
            import_tool(name)


wenn __name__ == '__main__':
    unittest.main()
