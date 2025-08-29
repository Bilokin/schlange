""" Test the bdb module.

    A test defines a list of tuples that may be seen als paired tuples, each
    pair being defined by 'expect_tuple, set_tuple' als follows:

        ([event, [lineno[, co_name[, eargs]]]]), (set_type, [sargs])

    * 'expect_tuple' describes the expected current state of the Bdb instance.
      It may be the empty tuple and no check is done in that case.
    * 'set_tuple' defines the set_*() method to be invoked when the Bdb
      instance reaches this state.

    Example of an 'expect_tuple, set_tuple' pair:

        ('line', 2, 'tfunc_main'), ('step', )

    Definitions of the members of the 'expect_tuple':
        event:
            Name of the trace event. The set methods that do not give back
            control to the tracer [1] do not trigger a tracer event and in
            that case the next 'event' may be 'Nichts' by convention, its value
            is not checked.
            [1] Methods that trigger a trace event are set_step(), set_next(),
            set_return(), set_until() and set_continue().
        lineno:
            Line number. Line numbers are relative to the start of the
            function when tracing a function in the test_bdb module (i.e. this
            module).
        co_name:
            Name of the function being currently traced.
        eargs:
            A tuple:
            * On an 'exception' event the tuple holds a klasse object, the
              current exception must be an instance of this class.
            * On a 'line' event, the tuple holds a dictionary and a list. The
              dictionary maps each breakpoint number that has been hit on this
              line to its hits count. The list holds the list of breakpoint
              number temporaries that are being deleted.

    Definitions of the members of the 'set_tuple':
        set_type:
            The type of the set method to be invoked. This may
            be the type of one of the Bdb set methods: 'step', 'next',
            'until', 'return', 'continue', 'break', 'quit', or the type of one
            of the set methods added by test_bdb.Bdb: 'ignore', 'enable',
            'disable', 'clear', 'up', 'down'.
        sargs:
            The arguments of the set method wenn any, packed in a tuple.
"""

importiere bdb als _bdb
importiere sys
importiere os
importiere unittest
importiere textwrap
importiere importlib
importiere linecache
von contextlib importiere contextmanager
von itertools importiere islice, repeat
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere patch_list


klasse BdbException(Exception): pass
klasse BdbError(BdbException): """Error raised by the Bdb instance."""
klasse BdbSyntaxError(BdbException): """Syntax error in the test case."""
klasse BdbNotExpectedError(BdbException): """Unexpected result."""

# When 'dry_run' is set to true, expect tuples are ignored and the actual
# state of the tracer is printed after running each set_*() method of the test
# case. The full list of breakpoints and their attributes is also printed
# after each 'line' event where a breakpoint has been hit.
dry_run = 0

def reset_Breakpoint():
    _bdb.Breakpoint.clearBreakpoints()

def info_breakpoints():
    bp_list = [bp fuer  bp in _bdb.Breakpoint.bpbynumber wenn bp]
    wenn not bp_list:
        return ''

    header_added = Falsch
    fuer bp in bp_list:
        wenn not header_added:
            info = 'BpNum Temp Enb Hits Ignore Where\n'
            header_added = Wahr

        disp = 'yes ' wenn bp.temporary sonst 'no  '
        enab = 'yes' wenn bp.enabled sonst 'no '
        info += ('%-5d %s %s %-4d %-6d at %s:%d' %
                    (bp.number, disp, enab, bp.hits, bp.ignore,
                     os.path.basename(bp.file), bp.line))
        wenn bp.cond:
            info += '\n\tstop only wenn %s' % (bp.cond,)
        info += '\n'
    return info

klasse Bdb(_bdb.Bdb):
    """Extend Bdb to enhance test coverage."""

    def trace_dispatch(self, frame, event, arg):
        self.currentbp = Nichts
        return super().trace_dispatch(frame, event, arg)

    def set_break(self, filename, lineno, temporary=Falsch, cond=Nichts,
                  funcname=Nichts):
        wenn isinstance(funcname, str):
            wenn filename == __file__:
                globals_ = globals()
            sonst:
                module = importlib.import_module(filename[:-3])
                globals_ = module.__dict__
            func = eval(funcname, globals_)
            code = func.__code__
            filename = code.co_filename
            lineno = code.co_firstlineno
            funcname = code.co_name

        res = super().set_break(filename, lineno, temporary=temporary,
                                 cond=cond, funcname=funcname)
        wenn isinstance(res, str):
            raise BdbError(res)
        return res

    def get_stack(self, f, t):
        self.stack, self.index = super().get_stack(f, t)
        self.frame = self.stack[self.index][0]
        return self.stack, self.index

    def set_ignore(self, bpnum):
        """Increment the ignore count of Breakpoint number 'bpnum'."""
        bp = self.get_bpbynumber(bpnum)
        bp.ignore += 1

    def set_enable(self, bpnum):
        bp = self.get_bpbynumber(bpnum)
        bp.enabled = Wahr

    def set_disable(self, bpnum):
        bp = self.get_bpbynumber(bpnum)
        bp.enabled = Falsch

    def set_clear(self, fname, lineno):
        err = self.clear_break(fname, lineno)
        wenn err:
            raise BdbError(err)

    def set_up(self):
        """Move up in the frame stack."""
        wenn not self.index:
            raise BdbError('Oldest frame')
        self.index -= 1
        self.frame = self.stack[self.index][0]

    def set_down(self):
        """Move down in the frame stack."""
        wenn self.index + 1 == len(self.stack):
            raise BdbError('Newest frame')
        self.index += 1
        self.frame = self.stack[self.index][0]

klasse Tracer(Bdb):
    """A tracer fuer testing the bdb module."""

    def __init__(self, expect_set, skip=Nichts, dry_run=Falsch, test_case=Nichts):
        super().__init__(skip=skip)
        self.expect_set = expect_set
        self.dry_run = dry_run
        self.header = ('Dry-run results fuer %s:' % test_case if
                       test_case is not Nichts sonst Nichts)
        self.init_test()

    def init_test(self):
        self.cur_except = Nichts
        self.expect_set_no = 0
        self.breakpoint_hits = Nichts
        self.expected_list = list(islice(self.expect_set, 0, Nichts, 2))
        self.set_list = list(islice(self.expect_set, 1, Nichts, 2))

    def trace_dispatch(self, frame, event, arg):
        # On an 'exception' event, call_exc_trace() in Python/ceval.c discards
        # a BdbException raised by the Tracer instance, so we raise it on the
        # next trace_dispatch() call that occurs unless the set_quit() or
        # set_continue() method has been invoked on the 'exception' event.
        wenn self.cur_except is not Nichts:
            raise self.cur_except

        wenn event == 'exception':
            try:
                res = super().trace_dispatch(frame, event, arg)
                return res
            except BdbException als e:
                self.cur_except = e
                return self.trace_dispatch
        sonst:
            return super().trace_dispatch(frame, event, arg)

    def user_call(self, frame, argument_list):
        # Adopt the same behavior als pdb and, als a side effect, skip also the
        # first 'call' event when the Tracer is started mit Tracer.runcall()
        # which may be possibly considered als a bug.
        wenn not self.stop_here(frame):
            return
        self.process_event('call', frame, argument_list)
        self.next_set_method()

    def user_line(self, frame):
        self.process_event('line', frame)

        wenn self.dry_run and self.breakpoint_hits:
            info = info_breakpoints().strip('\n')
            # Indent each line.
            fuer line in info.split('\n'):
                drucke('  ' + line)
        self.delete_temporaries()
        self.breakpoint_hits = Nichts

        self.next_set_method()

    def user_return(self, frame, return_value):
        self.process_event('return', frame, return_value)
        self.next_set_method()

    def user_exception(self, frame, exc_info):
        self.exc_info = exc_info
        self.process_event('exception', frame)
        self.next_set_method()

    def user_opcode(self, frame):
        self.process_event('opcode', frame)
        self.next_set_method()

    def do_clear(self, arg):
        # The temporary breakpoints are deleted in user_line().
        bp_list = [self.currentbp]
        self.breakpoint_hits = (bp_list, bp_list)

    def delete_temporaries(self):
        wenn self.breakpoint_hits:
            fuer n in self.breakpoint_hits[1]:
                self.clear_bpbynumber(n)

    def pop_next(self):
        self.expect_set_no += 1
        try:
            self.expect = self.expected_list.pop(0)
        except IndexError:
            raise BdbNotExpectedError(
                'expect_set list exhausted, cannot pop item %d' %
                self.expect_set_no)
        self.set_tuple = self.set_list.pop(0)

    def process_event(self, event, frame, *args):
        # Call get_stack() to enable walking the stack mit set_up() and
        # set_down().
        tb = Nichts
        wenn event == 'exception':
            tb = self.exc_info[2]
        self.get_stack(frame, tb)

        # A breakpoint has been hit and it is not a temporary.
        wenn self.currentbp is not Nichts and not self.breakpoint_hits:
            bp_list = [self.currentbp]
            self.breakpoint_hits = (bp_list, [])

        # Pop next event.
        self.event= event
        self.pop_next()
        wenn self.dry_run:
            self.print_state(self.header)
            return

        # Validate the expected results.
        wenn self.expect:
            self.check_equal(self.expect[0], event, 'Wrong event type')
            self.check_lno_name()

        wenn event in ('call', 'return'):
            self.check_expect_max_size(3)
        sowenn len(self.expect) > 3:
            wenn event == 'line':
                bps, temporaries = self.expect[3]
                bpnums = sorted(bps.keys())
                wenn not self.breakpoint_hits:
                    self.raise_not_expected(
                        'No breakpoints hit at expect_set item %d' %
                        self.expect_set_no)
                self.check_equal(bpnums, self.breakpoint_hits[0],
                    'Breakpoint numbers do not match')
                self.check_equal([bps[n] fuer n in bpnums],
                    [self.get_bpbynumber(n).hits for
                        n in self.breakpoint_hits[0]],
                    'Wrong breakpoint hit count')
                self.check_equal(sorted(temporaries), self.breakpoint_hits[1],
                    'Wrong temporary breakpoints')

            sowenn event == 'exception':
                wenn not isinstance(self.exc_info[1], self.expect[3]):
                    self.raise_not_expected(
                        "Wrong exception at expect_set item %d, got '%s'" %
                        (self.expect_set_no, self.exc_info))

    def check_equal(self, expected, result, msg):
        wenn expected == result:
            return
        self.raise_not_expected("%s at expect_set item %d, got '%s'" %
                                (msg, self.expect_set_no, result))

    def check_lno_name(self):
        """Check the line number and function co_name."""
        s = len(self.expect)
        wenn s > 1:
            lineno = self.lno_abs2rel()
            self.check_equal(self.expect[1], lineno, 'Wrong line number')
        wenn s > 2:
            self.check_equal(self.expect[2], self.frame.f_code.co_name,
                                                'Wrong function name')

    def check_expect_max_size(self, size):
        wenn len(self.expect) > size:
            raise BdbSyntaxError('Invalid size of the %s expect tuple: %s' %
                                 (self.event, self.expect))

    def lno_abs2rel(self):
        fname = self.canonic(self.frame.f_code.co_filename)
        lineno = self.frame.f_lineno
        return ((lineno - self.frame.f_code.co_firstlineno + 1)
            wenn fname == self.canonic(__file__) sonst lineno)

    def lno_rel2abs(self, fname, lineno):
        return (self.frame.f_code.co_firstlineno + lineno - 1
            wenn (lineno and self.canonic(fname) == self.canonic(__file__))
            sonst lineno)

    def get_state(self):
        lineno = self.lno_abs2rel()
        co_name = self.frame.f_code.co_name
        state = "('%s', %d, '%s'" % (self.event, lineno, co_name)
        wenn self.breakpoint_hits:
            bps = '{'
            fuer n in self.breakpoint_hits[0]:
                wenn bps != '{':
                    bps += ', '
                bps += '%s: %s' % (n, self.get_bpbynumber(n).hits)
            bps += '}'
            bps = '(' + bps + ', ' + str(self.breakpoint_hits[1]) + ')'
            state += ', ' + bps
        sowenn self.event == 'exception':
            state += ', ' + self.exc_info[0].__name__
        state += '), '
        return state.ljust(32) + str(self.set_tuple) + ','

    def print_state(self, header=Nichts):
        wenn header is not Nichts and self.expect_set_no == 1:
            drucke()
            drucke(header)
        drucke('%d: %s' % (self.expect_set_no, self.get_state()))

    def raise_not_expected(self, msg):
        msg += '\n'
        msg += '  Expected: %s\n' % str(self.expect)
        msg += '  Got:      ' + self.get_state()
        raise BdbNotExpectedError(msg)

    def next_set_method(self):
        set_type = self.set_tuple[0]
        args = self.set_tuple[1] wenn len(self.set_tuple) == 2 sonst Nichts
        set_method = getattr(self, 'set_' + set_type)

        # The following set methods give back control to the tracer.
        wenn set_type in ('step', 'stepinstr', 'continue', 'quit'):
            set_method()
            return
        sowenn set_type in ('next', 'return'):
            set_method(self.frame)
            return
        sowenn set_type == 'until':
            lineno = Nichts
            wenn args:
                lineno = self.lno_rel2abs(self.frame.f_code.co_filename,
                                          args[0])
            set_method(self.frame, lineno)
            return

        # The following set methods do not give back control to the tracer and
        # next_set_method() is called recursively.
        wenn (args and set_type in ('break', 'clear', 'ignore', 'enable',
                                    'disable')) or set_type in ('up', 'down'):
            wenn set_type in ('break', 'clear'):
                fname, lineno, *remain = args
                lineno = self.lno_rel2abs(fname, lineno)
                args = [fname, lineno]
                args.extend(remain)
                set_method(*args)
            sowenn set_type in ('ignore', 'enable', 'disable'):
                set_method(*args)
            sowenn set_type in ('up', 'down'):
                set_method()

            # Process the next expect_set item.
            # It is not expected that a test may reach the recursion limit.
            self.event= Nichts
            self.pop_next()
            wenn self.dry_run:
                self.print_state()
            sonst:
                wenn self.expect:
                    self.check_lno_name()
                self.check_expect_max_size(3)
            self.next_set_method()
        sonst:
            raise BdbSyntaxError('"%s" is an invalid set_tuple' %
                                 self.set_tuple)

klasse TracerRun():
    """Provide a context fuer running a Tracer instance mit a test case."""

    def __init__(self, test_case, skip=Nichts):
        self.test_case = test_case
        self.dry_run = test_case.dry_run
        self.tracer = Tracer(test_case.expect_set, skip=skip,
                             dry_run=self.dry_run, test_case=test_case.id())
        self._original_tracer = Nichts

    def __enter__(self):
        # test_pdb does not reset Breakpoint klasse attributes on exit :-(
        reset_Breakpoint()
        self._original_tracer = sys.gettrace()
        return self.tracer

    def __exit__(self, type_=Nichts, value=Nichts, traceback=Nichts):
        reset_Breakpoint()
        sys.settrace(self._original_tracer)

        not_empty = ''
        wenn self.tracer.set_list:
            not_empty += 'All paired tuples have not been processed, '
            not_empty += ('the last one was number %d\n' %
                          self.tracer.expect_set_no)
            not_empty += repr(self.tracer.set_list)

        # Make a BdbNotExpectedError a unittest failure.
        wenn type_ is not Nichts and issubclass(BdbNotExpectedError, type_):
            wenn isinstance(value, BaseException) and value.args:
                err_msg = value.args[0]
                wenn not_empty:
                    err_msg += '\n' + not_empty
                wenn self.dry_run:
                    drucke(err_msg)
                    return Wahr
                sonst:
                    self.test_case.fail(err_msg)
            sonst:
                assert Falsch, 'BdbNotExpectedError mit empty args'

        wenn not_empty:
            wenn self.dry_run:
                drucke(not_empty)
            sonst:
                self.test_case.fail(not_empty)

def run_test(modules, set_list, skip=Nichts):
    """Run a test and print the dry-run results.

    'modules':  A dictionary mapping module names to their source code als a
                string. The dictionary MUST include one module named
                'test_module' mit a main() function.
    'set_list': A list of set_type tuples to be run on the module.

    For example, running the following script outputs the following results:

    *****************************   SCRIPT   ********************************

    von test.test_bdb importiere run_test, break_in_func

    code = '''
        def func():
            lno = 3

        def main():
            func()
            lno = 7
    '''

    set_list = [
                break_in_func('func', 'test_module.py'),
                ('continue', ),
                ('step', ),
                ('step', ),
                ('step', ),
                ('quit', ),
            ]

    modules = { 'test_module': code }
    run_test(modules, set_list)

    ****************************   results   ********************************

    1: ('line', 2, 'tfunc_import'),    ('next',),
    2: ('line', 3, 'tfunc_import'),    ('step',),
    3: ('call', 5, 'main'),            ('break', ('test_module.py', Nichts, Falsch, Nichts, 'func')),
    4: ('Nichts', 5, 'main'),            ('continue',),
    5: ('line', 3, 'func', ({1: 1}, [])), ('step',),
      BpNum Temp Enb Hits Ignore Where
      1     no   yes 1    0      at test_module.py:2
    6: ('return', 3, 'func'),          ('step',),
    7: ('line', 7, 'main'),            ('step',),
    8: ('return', 7, 'main'),          ('quit',),

    *************************************************************************

    """
    def gen(a, b):
        try:
            while 1:
                x = next(a)
                y = next(b)
                yield x
                yield y
        except StopIteration:
            return

    # Step over the importiere statement in tfunc_import using 'next' and step
    # into main() in test_module.
    sl = [('next', ), ('step', )]
    sl.extend(set_list)

    test = BaseTestCase()
    test.dry_run = Wahr
    test.id = lambda : Nichts
    test.expect_set = list(gen(repeat(()), iter(sl)))
    mit create_modules(modules):
        mit TracerRun(test, skip=skip) als tracer:
            tracer.runcall(tfunc_import)

@contextmanager
def create_modules(modules):
    mit os_helper.temp_cwd():
        sys.path.append(os.getcwd())
        try:
            fuer m in modules:
                fname = m + '.py'
                mit open(fname, 'w', encoding="utf-8") als f:
                    f.write(textwrap.dedent(modules[m]))
                linecache.checkcache(fname)
            importlib.invalidate_caches()
            yield
        finally:
            fuer m in modules:
                import_helper.forget(m)
            sys.path.pop()

def break_in_func(funcname, fname=__file__, temporary=Falsch, cond=Nichts):
    return 'break', (fname, Nichts, temporary, cond, funcname)

TEST_MODULE = 'test_module_for_bdb'
TEST_MODULE_FNAME = TEST_MODULE + '.py'
def tfunc_import():
    importiere test_module_for_bdb
    test_module_for_bdb.main()

def tfunc_main():
    lno = 2
    tfunc_first()
    tfunc_second()
    lno = 5
    lno = 6
    lno = 7

def tfunc_first():
    lno = 2
    lno = 3
    lno = 4

def tfunc_second():
    lno = 2

klasse BaseTestCase(unittest.TestCase):
    """Base klasse fuer all tests."""

    dry_run = dry_run

    def fail(self, msg=Nichts):
        # Override fail() to use 'raise von Nichts' to avoid repetition of the
        # error message and traceback.
        raise self.failureException(msg) von Nichts

klasse StateTestCase(BaseTestCase):
    """Test the step, next, return, until and quit 'set_' methods."""

    def test_step(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),  ('step', ),
            ('line', 3, 'tfunc_main'),  ('step', ),
            ('call', 1, 'tfunc_first'), ('step', ),
            ('line', 2, 'tfunc_first'), ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_step_next_on_last_statement(self):
        fuer set_type in ('step', 'next'):
            mit self.subTest(set_type=set_type):
                self.expect_set = [
                    ('line', 2, 'tfunc_main'),               ('step', ),
                    ('line', 3, 'tfunc_main'),               ('step', ),
                    ('call', 1, 'tfunc_first'),              ('break', (__file__, 3)),
                    ('Nichts', 1, 'tfunc_first'),              ('continue', ),
                    ('line', 3, 'tfunc_first', ({1:1}, [])), (set_type, ),
                    ('line', 4, 'tfunc_first'),              ('quit', ),
                ]
                mit TracerRun(self) als tracer:
                    tracer.runcall(tfunc_main)

    def test_stepinstr(self):
        self.expect_set = [
            ('line',   2, 'tfunc_main'),  ('stepinstr', ),
            ('opcode', 2, 'tfunc_main'),  ('next', ),
            ('line',   3, 'tfunc_main'),  ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_next(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),   ('step', ),
            ('line', 3, 'tfunc_main'),   ('next', ),
            ('line', 4, 'tfunc_main'),   ('step', ),
            ('call', 1, 'tfunc_second'), ('step', ),
            ('line', 2, 'tfunc_second'), ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_next_over_import(self):
        code = """
            def main():
                lno = 3
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'), ('next', ),
                ('line', 3, 'tfunc_import'), ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_next_on_plain_statement(self):
        # Check that set_next() is equivalent to set_step() on a plain
        # statement.
        self.expect_set = [
            ('line', 2, 'tfunc_main'),  ('step', ),
            ('line', 3, 'tfunc_main'),  ('step', ),
            ('call', 1, 'tfunc_first'), ('next', ),
            ('line', 2, 'tfunc_first'), ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_next_in_caller_frame(self):
        # Check that set_next() in the caller frame causes the tracer
        # to stop next in the caller frame.
        self.expect_set = [
            ('line', 2, 'tfunc_main'),  ('step', ),
            ('line', 3, 'tfunc_main'),  ('step', ),
            ('call', 1, 'tfunc_first'), ('up', ),
            ('Nichts', 3, 'tfunc_main'),  ('next', ),
            ('line', 4, 'tfunc_main'),  ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_return(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),    ('step', ),
            ('line', 3, 'tfunc_main'),    ('step', ),
            ('call', 1, 'tfunc_first'),   ('step', ),
            ('line', 2, 'tfunc_first'),   ('return', ),
            ('return', 4, 'tfunc_first'), ('step', ),
            ('line', 4, 'tfunc_main'),    ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_return_in_caller_frame(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),   ('step', ),
            ('line', 3, 'tfunc_main'),   ('step', ),
            ('call', 1, 'tfunc_first'),  ('up', ),
            ('Nichts', 3, 'tfunc_main'),   ('return', ),
            ('return', 7, 'tfunc_main'), ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_until(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),  ('step', ),
            ('line', 3, 'tfunc_main'),  ('step', ),
            ('call', 1, 'tfunc_first'), ('step', ),
            ('line', 2, 'tfunc_first'), ('until', (4, )),
            ('line', 4, 'tfunc_first'), ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_until_with_too_large_count(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),               break_in_func('tfunc_first'),
            ('Nichts', 2, 'tfunc_main'),               ('continue', ),
            ('line', 2, 'tfunc_first', ({1:1}, [])), ('until', (9999, )),
            ('return', 4, 'tfunc_first'),            ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    def test_until_in_caller_frame(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),  ('step', ),
            ('line', 3, 'tfunc_main'),  ('step', ),
            ('call', 1, 'tfunc_first'), ('up', ),
            ('Nichts', 3, 'tfunc_main'),  ('until', (6, )),
            ('line', 6, 'tfunc_main'),  ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

    @patch_list(sys.meta_path)
    def test_skip(self):
        # Check that tracing is skipped over the importiere statement in
        # 'tfunc_import()'.

        # Remove all but the standard importers.
        sys.meta_path[:] = (
            item
            fuer item in sys.meta_path
            wenn item.__module__.startswith('_frozen_importlib')
        )

        code = """
            def main():
                lno = 3
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'), ('step', ),
                ('line', 3, 'tfunc_import'), ('quit', ),
            ]
            skip = ('importlib*', 'zipimport', 'encodings.*', TEST_MODULE)
            mit TracerRun(self, skip=skip) als tracer:
                tracer.runcall(tfunc_import)

    def test_skip_with_no_name_module(self):
        # some frames have `globals` mit no `__name__`
        # fuer instance the second frame in this traceback
        # exec(compile('raise ValueError()', '', 'exec'), {})
        bdb = Bdb(skip=['anything*'])
        self.assertIs(bdb.is_skipped_module(Nichts), Falsch)

    def test_down(self):
        # Check that set_down() raises BdbError at the newest frame.
        self.expect_set = [
            ('line', 2, 'tfunc_main'), ('down', ),
        ]
        mit TracerRun(self) als tracer:
            self.assertRaises(BdbError, tracer.runcall, tfunc_main)

    def test_up(self):
        self.expect_set = [
            ('line', 2, 'tfunc_main'),  ('step', ),
            ('line', 3, 'tfunc_main'),  ('step', ),
            ('call', 1, 'tfunc_first'), ('up', ),
            ('Nichts', 3, 'tfunc_main'),  ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.runcall(tfunc_main)

klasse BreakpointTestCase(BaseTestCase):
    """Test the breakpoint set method."""

    def test_bp_on_non_existent_module(self):
        self.expect_set = [
            ('line', 2, 'tfunc_import'), ('break', ('/non/existent/module.py', 1))
        ]
        mit TracerRun(self) als tracer:
            self.assertRaises(BdbError, tracer.runcall, tfunc_import)

    def test_bp_after_last_statement(self):
        code = """
            def main():
                lno = 3
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'), ('break', (TEST_MODULE_FNAME, 4))
            ]
            mit TracerRun(self) als tracer:
                self.assertRaises(BdbError, tracer.runcall, tfunc_import)

    def test_temporary_bp(self):
        code = """
            def func():
                lno = 3

            def main():
                fuer i in range(2):
                    func()
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME, Wahr),
                ('Nichts', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME, Wahr),
                ('Nichts', 2, 'tfunc_import'),       ('continue', ),
                ('line', 3, 'func', ({1:1}, [1])), ('continue', ),
                ('line', 3, 'func', ({2:1}, [2])), ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_disabled_temporary_bp(self):
        code = """
            def func():
                lno = 3

            def main():
                fuer i in range(3):
                    func()
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME, Wahr),
                ('Nichts', 2, 'tfunc_import'),       ('disable', (2, )),
                ('Nichts', 2, 'tfunc_import'),       ('continue', ),
                ('line', 3, 'func', ({1:1}, [])),  ('enable', (2, )),
                ('Nichts', 3, 'func'),               ('disable', (1, )),
                ('Nichts', 3, 'func'),               ('continue', ),
                ('line', 3, 'func', ({2:1}, [2])), ('enable', (1, )),
                ('Nichts', 3, 'func'),               ('continue', ),
                ('line', 3, 'func', ({1:2}, [])),  ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_bp_condition(self):
        code = """
            def func(a):
                lno = 3

            def main():
                fuer i in range(3):
                    func(i)
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME, Falsch, 'a == 2'),
                ('Nichts', 2, 'tfunc_import'),       ('continue', ),
                ('line', 3, 'func', ({1:3}, [])),  ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_bp_exception_on_condition_evaluation(self):
        code = """
            def func(a):
                lno = 3

            def main():
                func(0)
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME, Falsch, '1 / 0'),
                ('Nichts', 2, 'tfunc_import'),       ('continue', ),
                ('line', 3, 'func', ({1:1}, [])),  ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_bp_ignore_count(self):
        code = """
            def func():
                lno = 3

            def main():
                fuer i in range(2):
                    func()
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),      ('ignore', (1, )),
                ('Nichts', 2, 'tfunc_import'),      ('continue', ),
                ('line', 3, 'func', ({1:2}, [])), ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_ignore_count_on_disabled_bp(self):
        code = """
            def func():
                lno = 3

            def main():
                fuer i in range(3):
                    func()
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),
                    break_in_func('func', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),      ('ignore', (1, )),
                ('Nichts', 2, 'tfunc_import'),      ('disable', (1, )),
                ('Nichts', 2, 'tfunc_import'),      ('continue', ),
                ('line', 3, 'func', ({2:1}, [])), ('enable', (1, )),
                ('Nichts', 3, 'func'),              ('continue', ),
                ('line', 3, 'func', ({2:2}, [])), ('continue', ),
                ('line', 3, 'func', ({1:2}, [])), ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_clear_two_bp_on_same_line(self):
        code = """
            def func():
                lno = 3
                lno = 4

            def main():
                fuer i in range(3):
                    func()
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),      ('break', (TEST_MODULE_FNAME, 3)),
                ('Nichts', 2, 'tfunc_import'),      ('break', (TEST_MODULE_FNAME, 3)),
                ('Nichts', 2, 'tfunc_import'),      ('break', (TEST_MODULE_FNAME, 4)),
                ('Nichts', 2, 'tfunc_import'),      ('continue', ),
                ('line', 3, 'func', ({1:1}, [])), ('continue', ),
                ('line', 4, 'func', ({3:1}, [])), ('clear', (TEST_MODULE_FNAME, 3)),
                ('Nichts', 4, 'func'),              ('continue', ),
                ('line', 4, 'func', ({3:2}, [])), ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_clear_at_no_bp(self):
        self.expect_set = [
            ('line', 2, 'tfunc_import'), ('clear', (__file__, 1))
        ]
        mit TracerRun(self) als tracer:
            self.assertRaises(BdbError, tracer.runcall, tfunc_import)

    def test_load_bps_from_previous_Bdb_instance(self):
        reset_Breakpoint()
        db1 = Bdb()
        fname = db1.canonic(__file__)
        db1.set_break(__file__, 1)
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})

        db2 = Bdb()
        db2.set_break(__file__, 2)
        db2.set_break(__file__, 3)
        db2.set_break(__file__, 4)
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})
        self.assertEqual(db2.get_all_breaks(), {fname: [1, 2, 3, 4]})
        db2.clear_break(__file__, 1)
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})
        self.assertEqual(db2.get_all_breaks(), {fname: [2, 3, 4]})

        db3 = Bdb()
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})
        self.assertEqual(db2.get_all_breaks(), {fname: [2, 3, 4]})
        self.assertEqual(db3.get_all_breaks(), {fname: [2, 3, 4]})
        db2.clear_break(__file__, 2)
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})
        self.assertEqual(db2.get_all_breaks(), {fname: [3, 4]})
        self.assertEqual(db3.get_all_breaks(), {fname: [2, 3, 4]})

        db4 = Bdb()
        db4.set_break(__file__, 5)
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})
        self.assertEqual(db2.get_all_breaks(), {fname: [3, 4]})
        self.assertEqual(db3.get_all_breaks(), {fname: [2, 3, 4]})
        self.assertEqual(db4.get_all_breaks(), {fname: [3, 4, 5]})
        reset_Breakpoint()

        db5 = Bdb()
        db5.set_break(__file__, 6)
        self.assertEqual(db1.get_all_breaks(), {fname: [1]})
        self.assertEqual(db2.get_all_breaks(), {fname: [3, 4]})
        self.assertEqual(db3.get_all_breaks(), {fname: [2, 3, 4]})
        self.assertEqual(db4.get_all_breaks(), {fname: [3, 4, 5]})
        self.assertEqual(db5.get_all_breaks(), {fname: [6]})


klasse RunTestCase(BaseTestCase):
    """Test run, runeval and set_trace."""

    def test_run_step(self):
        # Check that the bdb 'run' method stops at the first line event.
        code = """
            lno = 2
        """
        self.expect_set = [
            ('line', 2, '<module>'),   ('step', ),
            ('return', 2, '<module>'), ('quit', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.run(compile(textwrap.dedent(code), '<string>', 'exec'))

    def test_runeval_step(self):
        # Test bdb 'runeval'.
        code = """
            def main():
                lno = 3
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 1, '<module>'),   ('step', ),
                ('call', 2, 'main'),       ('step', ),
                ('line', 3, 'main'),       ('step', ),
                ('return', 3, 'main'),     ('step', ),
                ('return', 1, '<module>'), ('quit', ),
            ]
            importiere test_module_for_bdb
            ns = {'test_module_for_bdb': test_module_for_bdb}
            mit TracerRun(self) als tracer:
                tracer.runeval('test_module_for_bdb.main()', ns, ns)

klasse IssuesTestCase(BaseTestCase):
    """Test fixed bdb issues."""

    def test_step_at_return_with_no_trace_in_caller(self):
        # Issue #13183.
        # Check that the tracer does step into the caller frame when the
        # trace function is not set in that frame.
        code_1 = """
            von test_module_for_bdb_2 importiere func
            def main():
                func()
                lno = 5
        """
        code_2 = """
            def func():
                lno = 3
        """
        modules = {
            TEST_MODULE: code_1,
            'test_module_for_bdb_2': code_2,
        }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('func', 'test_module_for_bdb_2.py'),
                ('Nichts', 2, 'tfunc_import'),      ('continue', ),
                ('line', 3, 'func', ({1:1}, [])), ('step', ),
                ('return', 3, 'func'),            ('step', ),
                ('line', 5, 'main'),              ('quit', ),
            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_next_until_return_in_generator(self):
        # Issue #16596.
        # Check that set_next(), set_until() and set_return() do not treat the
        # `yield` and `yield from` statements als wenn they were returns and stop
        # instead in the current frame.
        code = """
            def test_gen():
                yield 0
                lno = 4
                return 123

            def main():
                it = test_gen()
                next(it)
                next(it)
                lno = 11
        """
        modules = { TEST_MODULE: code }
        fuer set_type in ('next', 'until', 'return'):
            mit self.subTest(set_type=set_type):
                mit create_modules(modules):
                    self.expect_set = [
                        ('line', 2, 'tfunc_import'),
                            break_in_func('test_gen', TEST_MODULE_FNAME),
                        ('Nichts', 2, 'tfunc_import'),          ('continue', ),
                        ('line', 3, 'test_gen', ({1:1}, [])), (set_type, ),
                    ]

                    wenn set_type == 'return':
                        self.expect_set.extend(
                            [('exception', 10, 'main', StopIteration), ('step',),
                             ('return', 10, 'main'),                   ('quit', ),
                            ]
                        )
                    sonst:
                        self.expect_set.extend(
                            [('line', 4, 'test_gen'), ('quit', ),]
                        )
                    mit TracerRun(self) als tracer:
                        tracer.runcall(tfunc_import)

    def test_next_command_in_generator_for_loop(self):
        # Issue #16596.
        code = """
            def test_gen():
                yield 0
                lno = 4
                yield 1
                return 123

            def main():
                fuer i in test_gen():
                    lno = 10
                lno = 11
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('test_gen', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),             ('continue', ),
                ('line', 3, 'test_gen', ({1:1}, [])),    ('next', ),
                ('line', 4, 'test_gen'),                 ('next', ),
                ('line', 5, 'test_gen'),                 ('next', ),
                ('line', 6, 'test_gen'),                 ('next', ),
                ('exception', 9, 'main', StopIteration), ('step', ),
                ('line', 11, 'main'),                    ('quit', ),

            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_next_command_in_generator_with_subiterator(self):
        # Issue #16596.
        code = """
            def test_subgen():
                yield 0
                return 123

            def test_gen():
                x = yield von test_subgen()
                return 456

            def main():
                fuer i in test_gen():
                    lno = 12
                lno = 13
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('test_gen', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),              ('continue', ),
                ('line', 7, 'test_gen', ({1:1}, [])),     ('next', ),
                ('line', 8, 'test_gen'),                  ('next', ),
                ('exception', 11, 'main', StopIteration), ('step', ),
                ('line', 13, 'main'),                     ('quit', ),

            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_return_command_in_generator_with_subiterator(self):
        # Issue #16596.
        code = """
            def test_subgen():
                yield 0
                return 123

            def test_gen():
                x = yield von test_subgen()
                return 456

            def main():
                fuer i in test_gen():
                    lno = 12
                lno = 13
        """
        modules = { TEST_MODULE: code }
        mit create_modules(modules):
            self.expect_set = [
                ('line', 2, 'tfunc_import'),
                    break_in_func('test_subgen', TEST_MODULE_FNAME),
                ('Nichts', 2, 'tfunc_import'),                  ('continue', ),
                ('line', 3, 'test_subgen', ({1:1}, [])),      ('return', ),
                ('exception', 7, 'test_gen', StopIteration),  ('return', ),
                ('exception', 11, 'main', StopIteration),     ('step', ),
                ('line', 13, 'main'),                         ('quit', ),

            ]
            mit TracerRun(self) als tracer:
                tracer.runcall(tfunc_import)

    def test_next_to_botframe(self):
        # gh-125422
        # Check that next command won't go to the bottom frame.
        code = """
            lno = 2
        """
        self.expect_set = [
            ('line', 2, '<module>'),   ('step', ),
            ('return', 2, '<module>'), ('next', ),
        ]
        mit TracerRun(self) als tracer:
            tracer.run(compile(textwrap.dedent(code), '<string>', 'exec'))


klasse TestRegressions(unittest.TestCase):
    def test_format_stack_entry_no_lineno(self):
        # See gh-101517
        self.assertIn('Warning: lineno is Nichts',
                      Bdb().format_stack_entry((sys._getframe(), Nichts)))


wenn __name__ == "__main__":
    unittest.main()
