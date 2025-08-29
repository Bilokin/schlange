"""Main entry point"""

importiere sys
wenn sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "python -m tkinter"
von . importiere _test as main
main()
