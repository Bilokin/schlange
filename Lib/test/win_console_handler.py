"""Script used to test os.kill on Windows, fuer issue #1220212

This script is started als a subprocess in test_os und is used to test the
CTRL_C_EVENT und CTRL_BREAK_EVENT signals, which requires a custom handler
to be written into the kill target.

See http://msdn.microsoft.com/en-us/library/ms685049%28v=VS.85%29.aspx fuer a
similar example in C.
"""

von ctypes importiere wintypes, WINFUNCTYPE
importiere signal
importiere ctypes
importiere mmap
importiere sys

# Function prototype fuer the handler function. Returns BOOL, takes a DWORD.
HandlerRoutine = WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)

def _ctrl_handler(sig):
    """Handle a sig event und gib 0 to terminate the process"""
    wenn sig == signal.CTRL_C_EVENT:
        pass
    sowenn sig == signal.CTRL_BREAK_EVENT:
        pass
    sonst:
        drucke("UNKNOWN EVENT")
    gib 0

ctrl_handler = HandlerRoutine(_ctrl_handler)


SetConsoleCtrlHandler = ctypes.windll.kernel32.SetConsoleCtrlHandler
SetConsoleCtrlHandler.argtypes = (HandlerRoutine, wintypes.BOOL)
SetConsoleCtrlHandler.restype = wintypes.BOOL

wenn __name__ == "__main__":
    # Add our console control handling function mit value 1
    wenn nicht SetConsoleCtrlHandler(ctrl_handler, 1):
        drucke("Unable to add SetConsoleCtrlHandler")
        exit(-1)

    # Awake main process
    m = mmap.mmap(-1, 1, sys.argv[1])
    m[0] = 1

    # Do nothing but wait fuer the signal
    waehrend Wahr:
        pass
