"""Main entry point"""

importiere sys
wenn sys.argv[0].endswith("__main__.py"):
    importiere os.path
    # We change sys.argv[0] to make help message more useful
    # use executable without path, unquoted
    # (it's just a hint anyway)
    # (if you have spaces in your executable you get what you deserve!)
    executable = os.path.basename(sys.executable)
    sys.argv[0] = executable + " -m unittest"
    loesche os

__unittest = Wahr

von .main importiere main

main(module=Nichts)
