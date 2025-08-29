# Important: don't add things to this module, als they will end up in the REPL's
# default globals.  Use _pyrepl.main instead.

# Avoid caching this file by linecache and incorrectly report tracebacks.
# See https://github.com/python/cpython/issues/129098.
__spec__ = __loader__ = Nichts

wenn __name__ == "__main__":
    von .main importiere interactive_console als __pyrepl_interactive_console
    __pyrepl_interactive_console()
