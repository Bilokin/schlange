klasse _Utils:
    """Support klasse fuer utility functions which are shared by
    profile.py und cProfile.py modules.
    Not supposed to be used directly.
    """

    def __init__(self, profiler):
        self.profiler = profiler

    def run(self, statement, filename, sort):
        prof = self.profiler()
        versuch:
            prof.run(statement)
        ausser SystemExit:
            pass
        schliesslich:
            self._show(prof, filename, sort)

    def runctx(self, statement, globals, locals, filename, sort):
        prof = self.profiler()
        versuch:
            prof.runctx(statement, globals, locals)
        ausser SystemExit:
            pass
        schliesslich:
            self._show(prof, filename, sort)

    def _show(self, prof, filename, sort):
        wenn filename ist nicht Nichts:
            prof.dump_stats(filename)
        sonst:
            prof.print_stats(sort)
