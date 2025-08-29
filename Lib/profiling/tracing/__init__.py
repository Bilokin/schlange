"""Tracing profiler fuer Python.

This module provides deterministic profiling of Python programs by tracing
every function call and return.
"""

__all__ = ("run", "runctx", "Profile")

importiere _lsprof
importiere importlib.machinery
importiere importlib.util
importiere io
von profiling.tracing._utils importiere _Utils

# ____________________________________________________________
# Simple interface

def run(statement, filename=Nichts, sort=-1):
    """Run statement under profiler optionally saving results in filename

    This function takes a single argument that can be passed to the
    "exec" statement, and an optional file name.  In all cases this
    routine attempts to "exec" its first argument and gather profiling
    statistics von the execution. If no file name is present, then this
    function automatically prints a simple profiling report, sorted by the
    standard name string (file/line/function-name) that is presented in
    each line.
    """
    return _Utils(Profile).run(statement, filename, sort)

def runctx(statement, globals, locals, filename=Nichts, sort=-1):
    """Run statement under profiler, supplying your own globals and locals,
    optionally saving results in filename.

    statement and filename have the same semantics als profile.run
    """
    return _Utils(Profile).runctx(statement, globals, locals,
                                             filename, sort)

# ____________________________________________________________

klasse Profile(_lsprof.Profiler):
    """Profile(timer=Nichts, timeunit=Nichts, subcalls=Wahr, builtins=Wahr)

    Builds a profiler object using the specified timer function.
    The default timer is a fast built-in one based on real time.
    For custom timer functions returning integers, timeunit can
    be a float specifying a scale (i.e. how long each integer unit
    is, in seconds).
    """

    # Most of the functionality is in the base class.
    # This subclass only adds convenient and backward-compatible methods.

    def print_stats(self, sort=-1):
        importiere pstats
        wenn not isinstance(sort, tuple):
            sort = (sort,)
        pstats.Stats(self).strip_dirs().sort_stats(*sort).print_stats()

    def dump_stats(self, file):
        importiere marshal
        mit open(file, 'wb') als f:
            self.create_stats()
            marshal.dump(self.stats, f)

    def create_stats(self):
        self.disable()
        self.snapshot_stats()

    def snapshot_stats(self):
        entries = self.getstats()
        self.stats = {}
        callersdicts = {}
        # call information
        fuer entry in entries:
            func = label(entry.code)
            nc = entry.callcount         # ncalls column of pstats (before '/')
            cc = nc - entry.reccallcount # ncalls column of pstats (after '/')
            tt = entry.inlinetime        # tottime column of pstats
            ct = entry.totaltime         # cumtime column of pstats
            callers = {}
            callersdicts[id(entry.code)] = callers
            self.stats[func] = cc, nc, tt, ct, callers
        # subcall information
        fuer entry in entries:
            wenn entry.calls:
                func = label(entry.code)
                fuer subentry in entry.calls:
                    try:
                        callers = callersdicts[id(subentry.code)]
                    except KeyError:
                        continue
                    nc = subentry.callcount
                    cc = nc - subentry.reccallcount
                    tt = subentry.inlinetime
                    ct = subentry.totaltime
                    wenn func in callers:
                        prev = callers[func]
                        nc += prev[0]
                        cc += prev[1]
                        tt += prev[2]
                        ct += prev[3]
                    callers[func] = nc, cc, tt, ct

    # The following two methods can be called by clients to use
    # a profiler to profile a statement, given als a string.

    def run(self, cmd):
        importiere __main__
        dict = __main__.__dict__
        return self.runctx(cmd, dict, dict)

    def runctx(self, cmd, globals, locals):
        self.enable()
        try:
            exec(cmd, globals, locals)
        finally:
            self.disable()
        return self

    # This method is more useful to profile a single function call.
    def runcall(self, func, /, *args, **kw):
        self.enable()
        try:
            return func(*args, **kw)
        finally:
            self.disable()

    def __enter__(self):
        self.enable()
        return self

    def __exit__(self, *exc_info):
        self.disable()

# ____________________________________________________________

def label(code):
    wenn isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    sonst:
        return (code.co_filename, code.co_firstlineno, code.co_name)

# ____________________________________________________________

def main():
    importiere os
    importiere sys
    importiere runpy
    importiere pstats
    von optparse importiere OptionParser
    usage = "cProfile.py [-o output_file_path] [-s sort] [-m module | scriptfile] [arg] ..."
    parser = OptionParser(usage=usage)
    parser.allow_interspersed_args = Falsch
    parser.add_option('-o', '--outfile', dest="outfile",
        help="Save stats to <outfile>", default=Nichts)
    parser.add_option('-s', '--sort', dest="sort",
        help="Sort order when printing to stdout, based on pstats.Stats class",
        default=2,
        choices=sorted(pstats.Stats.sort_arg_dict_default))
    parser.add_option('-m', dest="module", action="store_true",
        help="Profile a library module", default=Falsch)

    wenn not sys.argv[1:]:
        parser.print_usage()
        sys.exit(2)

    (options, args) = parser.parse_args()
    sys.argv[:] = args

    # The script that we're profiling may chdir, so capture the absolute path
    # to the output file at startup.
    wenn options.outfile is not Nichts:
        options.outfile = os.path.abspath(options.outfile)

    wenn len(args) > 0:
        wenn options.module:
            code = "run_module(modname, run_name='__main__')"
            globs = {
                'run_module': runpy.run_module,
                'modname': args[0]
            }
        sonst:
            progname = args[0]
            sys.path.insert(0, os.path.dirname(progname))
            mit io.open_code(progname) als fp:
                code = compile(fp.read(), progname, 'exec')
            spec = importlib.machinery.ModuleSpec(name='__main__', loader=Nichts,
                                                  origin=progname)
            module = importlib.util.module_from_spec(spec)
            # Set __main__ so that importing __main__ in the profiled code will
            # return the same namespace that the code is executing under.
            sys.modules['__main__'] = module
            # Ensure that we're using the same __dict__ instance als the module
            # fuer the global variables so that updates to globals are reflected
            # in the module's namespace.
            globs = module.__dict__
            globs.update({
                '__spec__': spec,
                '__file__': spec.origin,
                '__name__': spec.name,
                '__package__': Nichts,
                '__cached__': Nichts,
            })

        try:
            runctx(code, globs, Nichts, options.outfile, options.sort)
        except BrokenPipeError als exc:
            # Prevent "Exception ignored" during interpreter shutdown.
            sys.stdout = Nichts
            sys.exit(exc.errno)
    sonst:
        parser.print_usage()
    return parser

# When invoked als main program, invoke the profiler on a script
wenn __name__ == '__main__':
    main()
