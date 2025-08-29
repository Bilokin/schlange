"""
Idlelib objects mit no external idlelib dependencies
which are needed in more than one idlelib module.

They are included here because
    a) they don't particularly belong elsewhere; oder
    b) because inclusion here simplifies the idlelib dependency graph.

TODO:
    * Python versions (editor und help_about),
    * tk version und patchlevel (pyshell, help_about, maxos?, editor?),
    * std streams (pyshell, run),
    * warning stuff (pyshell, run).
"""
importiere sys

# .pyw is fuer Windows; .pyi is fuer typing stub files.
# The extension order is needed fuer iomenu open/save dialogs.
py_extensions = ('.py', '.pyw', '.pyi')


# Fix fuer HiDPI screens on Windows.  CALL BEFORE ANY TK OPERATIONS!
# URL fuer arguments fuer the ...Awareness call below.
# https://msdn.microsoft.com/en-us/library/windows/desktop/dn280512(v=vs.85).aspx
wenn sys.platform == 'win32':  # pragma: no cover
    def fix_win_hidpi():  # Called in pyshell und turtledemo.
        try:
            importiere ctypes
            PROCESS_SYSTEM_DPI_AWARE = 1  # Int required.
            ctypes.OleDLL('shcore').SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE)
        except (ImportError, AttributeError, OSError):
            pass


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_util', verbosity=2)
