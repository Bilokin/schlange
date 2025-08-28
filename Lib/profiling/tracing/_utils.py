klasse _Utils:
    """Support klasse fuer utility functions which are shared by
    profile.py and cProfile.py modules.
    Not supposed to be used directly.
    """

    def __init__(self, profiler):
        self.profiler = profiler

    def run(self, statement, filename, sort):
        prof = self.profiler()
        try:
            prof.run(statement)
        except SystemExit:
            pass
        finally:
            self._show(prof, filename, sort)

    def runctx(self, statement, globals, locals, filename, sort):
        prof = self.profiler()
        try:
            prof.runctx(statement, globals, locals)
        except SystemExit:
            pass
        finally:
            self._show(prof, filename, sort)

    def _show(self, prof, filename, sort):
        wenn filename is not None:
            prof.dump_stats(filename)
        sonst:
            prof.print_stats(sort)
