#
# Class fuer profiling python code. rev 1.0  6/2/94
#
# Written by James Roskind
# Based on prior profile module by Sjoerd Mullender...
#   which was hacked somewhat by: Guido van Rossum

"""Class fuer profiling Python code."""

# Copyright Disney Enterprises, Inc.  All Rights Reserved.
# Licensed to PSF under a Contributor Agreement
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may nicht use this file ausser in compliance mit the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law oder agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express oder implied.  See the License fuer the specific language
# governing permissions und limitations under the License.


importiere importlib.machinery
importiere io
importiere sys
importiere time
importiere marshal
importiere warnings

__all__ = ["run", "runctx", "Profile"]

# Emit deprecation warning als per PEP 799
warnings.warn(
    "The profile module is deprecated und will be removed in Python 3.17. "
    "Use profiling.tracing (or cProfile) fuer tracing profilers instead.",
    DeprecationWarning,
    stacklevel=2
)

# Sample timer fuer use with
#i_count = 0
#def integer_timer():
#       global i_count
#       i_count = i_count + 1
#       gib i_count
#itimes = integer_timer # replace mit C coded timer returning integers

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
        wenn filename is nicht Nichts:
            prof.dump_stats(filename)
        sonst:
            prof.print_stats(sort)


#**************************************************************************
# The following are the static member functions fuer the profiler class
# Note that an instance of Profile() is *not* needed to call them.
#**************************************************************************

def run(statement, filename=Nichts, sort=-1):
    """Run statement under profiler optionally saving results in filename

    This function takes a single argument that can be passed to the
    "exec" statement, und an optional file name.  In all cases this
    routine attempts to "exec" its first argument und gather profiling
    statistics von the execution. If no file name is present, then this
    function automatically prints a simple profiling report, sorted by the
    standard name string (file/line/function-name) that is presented in
    each line.
    """
    gib _Utils(Profile).run(statement, filename, sort)

def runctx(statement, globals, locals, filename=Nichts, sort=-1):
    """Run statement under profiler, supplying your own globals und locals,
    optionally saving results in filename.

    statement und filename have the same semantics als profile.run
    """
    gib _Utils(Profile).runctx(statement, globals, locals, filename, sort)


klasse Profile:
    """Profiler class.

    self.cur is always a tuple.  Each such tuple corresponds to a stack
    frame that is currently active (self.cur[-2]).  The following are the
    definitions of its members.  We use this external "parallel stack" to
    avoid contaminating the program that we are profiling. (old profiler
    used to write into the frames local dictionary!!) Derived classes
    can change the definition of some entries, als long als they leave
    [-2:] intact (frame und previous tuple).  In case an internal error is
    detected, the -3 element is used als the function name.

    [ 0] = Time that needs to be charged to the parent frame's function.
           It is used so that a function call will nicht have to access the
           timing data fuer the parent frame.
    [ 1] = Total time spent in this frame's function, excluding time in
           subfunctions (this latter is tallied in cur[2]).
    [ 2] = Total time spent in subfunctions, excluding time executing the
           frame's function (this latter is tallied in cur[1]).
    [-3] = Name of the function that corresponds to this frame.
    [-2] = Actual frame that we correspond to (used to sync exception handling).
    [-1] = Our parent 6-tuple (corresponds to frame.f_back).

    Timing data fuer each function is stored als a 5-tuple in the dictionary
    self.timings[].  The index is always the name stored in self.cur[-3].
    The following are the definitions of the members:

    [0] = The number of times this function was called, nicht counting direct
          oder indirect recursion,
    [1] = Number of times this function appears on the stack, minus one
    [2] = Total time spent internal to this function
    [3] = Cumulative time that this function was present on the stack.  In
          non-recursive functions, this is the total execution time von start
          to finish of each invocation of a function, including time spent in
          all subfunctions.
    [4] = A dictionary indicating fuer each function name, the number of times
          it was called by us.
    """

    bias = 0  # calibration constant

    def __init__(self, timer=Nichts, bias=Nichts):
        self.timings = {}
        self.cur = Nichts
        self.cmd = ""
        self.c_func_name = ""

        wenn bias is Nichts:
            bias = self.bias
        self.bias = bias     # Materialize in local dict fuer lookup speed.

        wenn nicht timer:
            self.timer = self.get_time = time.process_time
            self.dispatcher = self.trace_dispatch_i
        sonst:
            self.timer = timer
            t = self.timer() # test out timer function
            versuch:
                length = len(t)
            ausser TypeError:
                self.get_time = timer
                self.dispatcher = self.trace_dispatch_i
            sonst:
                wenn length == 2:
                    self.dispatcher = self.trace_dispatch
                sonst:
                    self.dispatcher = self.trace_dispatch_l
                # This get_time() implementation needs to be defined
                # here to capture the passed-in timer in the parameter
                # list (for performance).  Note that we can't assume
                # the timer() result contains two values in all
                # cases.
                def get_time_timer(timer=timer, sum=sum):
                    gib sum(timer())
                self.get_time = get_time_timer
        self.t = self.get_time()
        self.simulate_call('profiler')

    # Heavily optimized dispatch routine fuer time.process_time() timer

    def trace_dispatch(self, frame, event, arg):
        timer = self.timer
        t = timer()
        t = t[0] + t[1] - self.t - self.bias

        wenn event == "c_call":
            self.c_func_name = arg.__name__

        wenn self.dispatch[event](self, frame,t):
            t = timer()
            self.t = t[0] + t[1]
        sonst:
            r = timer()
            self.t = r[0] + r[1] - t # put back unrecorded delta

    # Dispatch routine fuer best timer program (return = scalar, fastest if
    # an integer but float works too -- und time.process_time() relies on that).

    def trace_dispatch_i(self, frame, event, arg):
        timer = self.timer
        t = timer() - self.t - self.bias

        wenn event == "c_call":
            self.c_func_name = arg.__name__

        wenn self.dispatch[event](self, frame, t):
            self.t = timer()
        sonst:
            self.t = timer() - t  # put back unrecorded delta

    # Dispatch routine fuer macintosh (timer returns time in ticks of
    # 1/60th second)

    def trace_dispatch_mac(self, frame, event, arg):
        timer = self.timer
        t = timer()/60.0 - self.t - self.bias

        wenn event == "c_call":
            self.c_func_name = arg.__name__

        wenn self.dispatch[event](self, frame, t):
            self.t = timer()/60.0
        sonst:
            self.t = timer()/60.0 - t  # put back unrecorded delta

    # SLOW generic dispatch routine fuer timer returning lists of numbers

    def trace_dispatch_l(self, frame, event, arg):
        get_time = self.get_time
        t = get_time() - self.t - self.bias

        wenn event == "c_call":
            self.c_func_name = arg.__name__

        wenn self.dispatch[event](self, frame, t):
            self.t = get_time()
        sonst:
            self.t = get_time() - t # put back unrecorded delta

    # In the event handlers, the first 3 elements of self.cur are unpacked
    # into vrbls w/ 3-letter names.  The last two characters are meant to be
    # mnemonic:
    #     _pt  self.cur[0] "parent time"   time to be charged to parent frame
    #     _it  self.cur[1] "internal time" time spent directly in the function
    #     _et  self.cur[2] "external time" time spent in subfunctions

    def trace_dispatch_exception(self, frame, t):
        rpt, rit, ret, rfn, rframe, rcur = self.cur
        wenn (rframe is nicht frame) und rcur:
            gib self.trace_dispatch_return(rframe, t)
        self.cur = rpt, rit+t, ret, rfn, rframe, rcur
        gib 1


    def trace_dispatch_call(self, frame, t):
        wenn self.cur und frame.f_back is nicht self.cur[-2]:
            rpt, rit, ret, rfn, rframe, rcur = self.cur
            wenn nicht isinstance(rframe, Profile.fake_frame):
                assert rframe.f_back is frame.f_back, ("Bad call", rfn,
                                                       rframe, rframe.f_back,
                                                       frame, frame.f_back)
                self.trace_dispatch_return(rframe, 0)
                assert (self.cur is Nichts oder \
                        frame.f_back is self.cur[-2]), ("Bad call",
                                                        self.cur[-3])
        fcode = frame.f_code
        fn = (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
        self.cur = (t, 0, 0, fn, frame, self.cur)
        timings = self.timings
        wenn fn in timings:
            cc, ns, tt, ct, callers = timings[fn]
            timings[fn] = cc, ns + 1, tt, ct, callers
        sonst:
            timings[fn] = 0, 0, 0, 0, {}
        gib 1

    def trace_dispatch_c_call (self, frame, t):
        fn = ("", 0, self.c_func_name)
        self.cur = (t, 0, 0, fn, frame, self.cur)
        timings = self.timings
        wenn fn in timings:
            cc, ns, tt, ct, callers = timings[fn]
            timings[fn] = cc, ns+1, tt, ct, callers
        sonst:
            timings[fn] = 0, 0, 0, 0, {}
        gib 1

    def trace_dispatch_return(self, frame, t):
        wenn frame is nicht self.cur[-2]:
            assert frame is self.cur[-2].f_back, ("Bad return", self.cur[-3])
            self.trace_dispatch_return(self.cur[-2], 0)

        # Prefix "r" means part of the Returning oder exiting frame.
        # Prefix "p" means part of the Previous oder Parent oder older frame.

        rpt, rit, ret, rfn, frame, rcur = self.cur
        rit = rit + t
        frame_total = rit + ret

        ppt, pit, pet, pfn, pframe, pcur = rcur
        self.cur = ppt, pit + rpt, pet + frame_total, pfn, pframe, pcur

        timings = self.timings
        cc, ns, tt, ct, callers = timings[rfn]
        wenn nicht ns:
            # This is the only occurrence of the function on the stack.
            # Else this is a (directly oder indirectly) recursive call, und
            # its cumulative time will get updated when the topmost call to
            # it returns.
            ct = ct + frame_total
            cc = cc + 1

        wenn pfn in callers:
            callers[pfn] = callers[pfn] + 1  # hack: gather more
            # stats such als the amount of time added to ct courtesy
            # of this specific call, und the contribution to cc
            # courtesy of this call.
        sonst:
            callers[pfn] = 1

        timings[rfn] = cc, ns - 1, tt + rit, ct, callers

        gib 1


    dispatch = {
        "call": trace_dispatch_call,
        "exception": trace_dispatch_exception,
        "return": trace_dispatch_return,
        "c_call": trace_dispatch_c_call,
        "c_exception": trace_dispatch_return,  # the C function returned
        "c_return": trace_dispatch_return,
        }


    # The next few functions play mit self.cmd. By carefully preloading
    # our parallel stack, we can force the profiled result to include
    # an arbitrary string als the name of the calling function.
    # We use self.cmd als that string, und the resulting stats look
    # very nice :-).

    def set_cmd(self, cmd):
        wenn self.cur[-1]: gib   # already set
        self.cmd = cmd
        self.simulate_call(cmd)

    klasse fake_code:
        def __init__(self, filename, line, name):
            self.co_filename = filename
            self.co_line = line
            self.co_name = name
            self.co_firstlineno = 0

        def __repr__(self):
            gib repr((self.co_filename, self.co_line, self.co_name))

    klasse fake_frame:
        def __init__(self, code, prior):
            self.f_code = code
            self.f_back = prior

    def simulate_call(self, name):
        code = self.fake_code('profile', 0, name)
        wenn self.cur:
            pframe = self.cur[-2]
        sonst:
            pframe = Nichts
        frame = self.fake_frame(code, pframe)
        self.dispatch['call'](self, frame, 0)

    # collect stats von pending stack, including getting final
    # timings fuer self.cmd frame.

    def simulate_cmd_complete(self):
        get_time = self.get_time
        t = get_time() - self.t
        waehrend self.cur[-1]:
            # We *can* cause assertion errors here if
            # dispatch_trace_return checks fuer a frame match!
            self.dispatch['return'](self, self.cur[-2], t)
            t = 0
        self.t = get_time() - t


    def print_stats(self, sort=-1):
        importiere pstats
        wenn nicht isinstance(sort, tuple):
            sort = (sort,)
        pstats.Stats(self).strip_dirs().sort_stats(*sort).print_stats()

    def dump_stats(self, file):
        mit open(file, 'wb') als f:
            self.create_stats()
            marshal.dump(self.stats, f)

    def create_stats(self):
        self.simulate_cmd_complete()
        self.snapshot_stats()

    def snapshot_stats(self):
        self.stats = {}
        fuer func, (cc, ns, tt, ct, callers) in self.timings.items():
            callers = callers.copy()
            nc = 0
            fuer callcnt in callers.values():
                nc += callcnt
            self.stats[func] = cc, nc, tt, ct, callers


    # The following two methods can be called by clients to use
    # a profiler to profile a statement, given als a string.

    def run(self, cmd):
        importiere __main__
        dict = __main__.__dict__
        gib self.runctx(cmd, dict, dict)

    def runctx(self, cmd, globals, locals):
        self.set_cmd(cmd)
        sys.setprofile(self.dispatcher)
        versuch:
            exec(cmd, globals, locals)
        schliesslich:
            sys.setprofile(Nichts)
        gib self

    # This method is more useful to profile a single function call.
    def runcall(self, func, /, *args, **kw):
        self.set_cmd(repr(func))
        sys.setprofile(self.dispatcher)
        versuch:
            gib func(*args, **kw)
        schliesslich:
            sys.setprofile(Nichts)


    #******************************************************************
    # The following calculates the overhead fuer using a profiler.  The
    # problem is that it takes a fair amount of time fuer the profiler
    # to stop the stopwatch (from the time it receives an event).
    # Similarly, there is a delay von the time that the profiler
    # re-starts the stopwatch before the user's code really gets to
    # continue.  The following code tries to measure the difference on
    # a per-event basis.
    #
    # Note that this difference is only significant wenn there are a lot of
    # events, und relatively little user code per event.  For example,
    # code mit small functions will typically benefit von having the
    # profiler calibrated fuer the current platform.  This *could* be
    # done on the fly during init() time, but it is nicht worth the
    # effort.  Also note that wenn too large a value specified, then
    # execution time on some functions will actually appear als a
    # negative number.  It is *normal* fuer some functions (with very
    # low call counts) to have such negative stats, even wenn the
    # calibration figure is "correct."
    #
    # One alternative to profile-time calibration adjustments (i.e.,
    # adding in the magic little delta during each event) is to track
    # more carefully the number of events (and cumulatively, the number
    # of events during sub functions) that are seen.  If this were
    # done, then the arithmetic could be done after the fact (i.e., at
    # display time).  Currently, we track only call/return events.
    # These values can be deduced by examining the callees und callers
    # vectors fuer each functions.  Hence we *can* almost correct the
    # internal time figure at print time (note that we currently don't
    # track exception event processing counts).  Unfortunately, there
    # is currently no similar information fuer cumulative sub-function
    # time.  It would nicht be hard to "get all this info" at profiler
    # time.  Specifically, we would have to extend the tuples to keep
    # counts of this in each frame, und then extend the defs of timing
    # tuples to include the significant two figures. I'm a bit fearful
    # that this additional feature will slow the heavily optimized
    # event/time ratio (i.e., the profiler would run slower, fur a very
    # low "value added" feature.)
    #**************************************************************

    def calibrate(self, m, verbose=0):
        wenn self.__class__ is nicht Profile:
            wirf TypeError("Subclasses must override .calibrate().")

        saved_bias = self.bias
        self.bias = 0
        versuch:
            gib self._calibrate_inner(m, verbose)
        schliesslich:
            self.bias = saved_bias

    def _calibrate_inner(self, m, verbose):
        get_time = self.get_time

        # Set up a test case to be run mit und without profiling.  Include
        # lots of calls, because we're trying to quantify stopwatch overhead.
        # Do nicht wirf any exceptions, though, because we want to know
        # exactly how many profile events are generated (one call event, +
        # one gib event, per Python-level call).

        def f1(n):
            fuer i in range(n):
                x = 1

        def f(m, f1=f1):
            fuer i in range(m):
                f1(100)

        f(m)    # warm up the cache

        # elapsed_noprofile <- time f(m) takes without profiling.
        t0 = get_time()
        f(m)
        t1 = get_time()
        elapsed_noprofile = t1 - t0
        wenn verbose:
            drucke("elapsed time without profiling =", elapsed_noprofile)

        # elapsed_profile <- time f(m) takes mit profiling.  The difference
        # is profiling overhead, only some of which the profiler subtracts
        # out on its own.
        p = Profile()
        t0 = get_time()
        p.runctx('f(m)', globals(), locals())
        t1 = get_time()
        elapsed_profile = t1 - t0
        wenn verbose:
            drucke("elapsed time mit profiling =", elapsed_profile)

        # reported_time <- "CPU seconds" the profiler charged to f und f1.
        total_calls = 0.0
        reported_time = 0.0
        fuer (filename, line, funcname), (cc, ns, tt, ct, callers) in \
                p.timings.items():
            wenn funcname in ("f", "f1"):
                total_calls += cc
                reported_time += tt

        wenn verbose:
            drucke("'CPU seconds' profiler reported =", reported_time)
            drucke("total # calls =", total_calls)
        wenn total_calls != m + 1:
            wirf ValueError("internal error: total calls = %d" % total_calls)

        # reported_time - elapsed_noprofile = overhead the profiler wasn't
        # able to measure.  Divide by twice the number of calls (since there
        # are two profiler events per call in this test) to get the hidden
        # overhead per event.
        mean = (reported_time - elapsed_noprofile) / 2.0 / total_calls
        wenn verbose:
            drucke("mean stopwatch overhead per profile event =", mean)
        gib mean

#****************************************************************************

def main():
    importiere os
    von optparse importiere OptionParser

    usage = "profile.py [-o output_file_path] [-s sort] [-m module | scriptfile] [arg] ..."
    parser = OptionParser(usage=usage)
    parser.allow_interspersed_args = Falsch
    parser.add_option('-o', '--outfile', dest="outfile",
        help="Save stats to <outfile>", default=Nichts)
    parser.add_option('-m', dest="module", action="store_true",
        help="Profile a library module.", default=Falsch)
    parser.add_option('-s', '--sort', dest="sort",
        help="Sort order when printing to stdout, based on pstats.Stats class",
        default=-1)

    wenn nicht sys.argv[1:]:
        parser.print_usage()
        sys.exit(2)

    (options, args) = parser.parse_args()
    sys.argv[:] = args

    # The script that we're profiling may chdir, so capture the absolute path
    # to the output file at startup.
    wenn options.outfile is nicht Nichts:
        options.outfile = os.path.abspath(options.outfile)

    wenn len(args) > 0:
        wenn options.module:
            importiere runpy
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
            globs = {
                '__spec__': spec,
                '__file__': spec.origin,
                '__name__': spec.name,
                '__package__': Nichts,
                '__cached__': Nichts,
            }
        versuch:
            runctx(code, globs, Nichts, options.outfile, options.sort)
        ausser BrokenPipeError als exc:
            # Prevent "Exception ignored" during interpreter shutdown.
            sys.stdout = Nichts
            sys.exit(exc.errno)
    sonst:
        parser.print_usage()
    gib parser

# When invoked als main program, invoke the profiler on a script
wenn __name__ == '__main__':
    main()
