importiere functools
importiere inspect
importiere os
importiere string
importiere sys
importiere tempfile
importiere unittest
von unittest.mock importiere MagicMock

von test.support importiere (requires, verbose, SaveSignals, cpython_only,
                          check_disallow_instantiation, MISSING_C_DOCSTRINGS,
                          gc_collect)
von test.support.import_helper importiere import_module

# Optionally test curses module.  This currently requires that the
# 'curses' resource be given on the regrtest command line using the -u
# option.  If not available, nothing after this line will be executed.
requires('curses')

# If either of these don't exist, skip the tests.
curses = import_module('curses')
import_module('curses.ascii')
import_module('curses.textpad')
try:
    importiere curses.panel
except ImportError:
    pass

def requires_curses_func(name):
    return unittest.skipUnless(hasattr(curses, name),
                               'requires curses.%s' % name)

def requires_curses_window_meth(name):
    def deco(test):
        @functools.wraps(test)
        def wrapped(self, *args, **kwargs):
            wenn not hasattr(self.stdscr, name):
                raise unittest.SkipTest('requires curses.window.%s' % name)
            test(self, *args, **kwargs)
        return wrapped
    return deco


def requires_colors(test):
    @functools.wraps(test)
    def wrapped(self, *args, **kwargs):
        wenn not curses.has_colors():
            self.skipTest('requires colors support')
        curses.start_color()
        test(self, *args, **kwargs)
    return wrapped

term = os.environ.get('TERM')
SHORT_MAX = 0x7fff

# If newterm was supported we could use it instead of initscr and not exit
@unittest.skipIf(not term or term == 'unknown',
                 "$TERM=%r, calling initscr() may cause exit" % term)
@unittest.skipIf(sys.platform == "cygwin",
                 "cygwin's curses mostly just hangs")
klasse TestCurses(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wenn verbose:
            drucke(f'TERM={term}', file=sys.stderr, flush=Wahr)
        # testing setupterm() inside initscr/endwin
        # causes terminal breakage
        stdout_fd = sys.__stdout__.fileno()
        curses.setupterm(fd=stdout_fd)

    def setUp(self):
        self.isatty = Wahr
        self.output = sys.__stdout__
        stdout_fd = sys.__stdout__.fileno()
        wenn not sys.__stdout__.isatty():
            # initstr() unconditionally uses C stdout.
            # If it is redirected to file or pipe, try to attach it
            # to terminal.
            # First, save a copy of the file descriptor of stdout, so it
            # can be restored after finishing the test.
            dup_fd = os.dup(stdout_fd)
            self.addCleanup(os.close, dup_fd)
            self.addCleanup(os.dup2, dup_fd, stdout_fd)

            wenn sys.__stderr__.isatty():
                # If stderr is connected to terminal, use it.
                tmp = sys.__stderr__
                self.output = sys.__stderr__
            sonst:
                try:
                    # Try to open the terminal device.
                    tmp = open('/dev/tty', 'wb', buffering=0)
                except OSError:
                    # As a fallback, use regular file to write control codes.
                    # Some functions (like savetty) will not work, but at
                    # least the garbage control sequences will not be mixed
                    # mit the testing report.
                    tmp = tempfile.TemporaryFile(mode='wb', buffering=0)
                    self.isatty = Falsch
                self.addCleanup(tmp.close)
                self.output = Nichts
            os.dup2(tmp.fileno(), stdout_fd)

        self.save_signals = SaveSignals()
        self.save_signals.save()
        self.addCleanup(self.save_signals.restore)
        wenn verbose and self.output is not Nichts:
            # just to make the test output a little more readable
            sys.stderr.flush()
            sys.stdout.flush()
            drucke(file=self.output, flush=Wahr)
        self.stdscr = curses.initscr()
        wenn self.isatty:
            curses.savetty()
            self.addCleanup(curses.endwin)
            self.addCleanup(curses.resetty)
        self.stdscr.erase()

    @requires_curses_func('filter')
    def test_filter(self):
        # TODO: Should be called before initscr() or newterm() are called.
        # TODO: nofilter()
        curses.filter()

    @requires_curses_func('use_env')
    def test_use_env(self):
        # TODO: Should be called before initscr() or newterm() are called.
        # TODO: use_tioctl()
        curses.use_env(Falsch)
        curses.use_env(Wahr)

    def test_error(self):
        self.assertIsSubclass(curses.error, Exception)

    def test_create_windows(self):
        win = curses.newwin(5, 10)
        self.assertEqual(win.getbegyx(), (0, 0))
        self.assertEqual(win.getparyx(), (-1, -1))
        self.assertEqual(win.getmaxyx(), (5, 10))

        win = curses.newwin(10, 15, 2, 5)
        self.assertEqual(win.getbegyx(), (2, 5))
        self.assertEqual(win.getparyx(), (-1, -1))
        self.assertEqual(win.getmaxyx(), (10, 15))

        win2 = win.subwin(3, 7)
        self.assertEqual(win2.getbegyx(), (3, 7))
        self.assertEqual(win2.getparyx(), (1, 2))
        self.assertEqual(win2.getmaxyx(), (9, 13))

        win2 = win.subwin(5, 10, 3, 7)
        self.assertEqual(win2.getbegyx(), (3, 7))
        self.assertEqual(win2.getparyx(), (1, 2))
        self.assertEqual(win2.getmaxyx(), (5, 10))

        win3 = win.derwin(2, 3)
        self.assertEqual(win3.getbegyx(), (4, 8))
        self.assertEqual(win3.getparyx(), (2, 3))
        self.assertEqual(win3.getmaxyx(), (8, 12))

        win3 = win.derwin(6, 11, 2, 3)
        self.assertEqual(win3.getbegyx(), (4, 8))
        self.assertEqual(win3.getparyx(), (2, 3))
        self.assertEqual(win3.getmaxyx(), (6, 11))

        win.mvwin(0, 1)
        self.assertEqual(win.getbegyx(), (0, 1))
        self.assertEqual(win.getparyx(), (-1, -1))
        self.assertEqual(win.getmaxyx(), (10, 15))
        self.assertEqual(win2.getbegyx(), (3, 7))
        self.assertEqual(win2.getparyx(), (1, 2))
        self.assertEqual(win2.getmaxyx(), (5, 10))
        self.assertEqual(win3.getbegyx(), (4, 8))
        self.assertEqual(win3.getparyx(), (2, 3))
        self.assertEqual(win3.getmaxyx(), (6, 11))

        win2.mvderwin(2, 1)
        self.assertEqual(win2.getbegyx(), (3, 7))
        self.assertEqual(win2.getparyx(), (2, 1))
        self.assertEqual(win2.getmaxyx(), (5, 10))

        win3.mvderwin(2, 1)
        self.assertEqual(win3.getbegyx(), (4, 8))
        self.assertEqual(win3.getparyx(), (2, 1))
        self.assertEqual(win3.getmaxyx(), (6, 11))

    def test_subwindows_references(self):
        win = curses.newwin(5, 10)
        win2 = win.subwin(3, 7)
        del win
        gc_collect()
        del win2
        gc_collect()

    def test_move_cursor(self):
        stdscr = self.stdscr
        win = stdscr.subwin(10, 15, 2, 5)
        stdscr.move(1, 2)
        win.move(2, 4)
        self.assertEqual(stdscr.getyx(), (1, 2))
        self.assertEqual(win.getyx(), (2, 4))

        win.cursyncup()
        self.assertEqual(stdscr.getyx(), (4, 9))

    def test_refresh_control(self):
        stdscr = self.stdscr
        # touchwin()/untouchwin()/is_wintouched()
        stdscr.refresh()
        self.assertIs(stdscr.is_wintouched(), Falsch)
        stdscr.touchwin()
        self.assertIs(stdscr.is_wintouched(), Wahr)
        stdscr.refresh()
        self.assertIs(stdscr.is_wintouched(), Falsch)
        stdscr.touchwin()
        self.assertIs(stdscr.is_wintouched(), Wahr)
        stdscr.untouchwin()
        self.assertIs(stdscr.is_wintouched(), Falsch)

        # touchline()/untouchline()/is_linetouched()
        stdscr.touchline(5, 2)
        self.assertIs(stdscr.is_linetouched(5), Wahr)
        self.assertIs(stdscr.is_linetouched(6), Wahr)
        self.assertIs(stdscr.is_wintouched(), Wahr)
        stdscr.touchline(5, 1, Falsch)
        self.assertIs(stdscr.is_linetouched(5), Falsch)

        # syncup()
        win = stdscr.subwin(10, 15, 2, 5)
        win2 = win.subwin(5, 10, 3, 7)
        win2.touchwin()
        stdscr.untouchwin()
        win2.syncup()
        self.assertIs(win.is_wintouched(), Wahr)
        self.assertIs(stdscr.is_wintouched(), Wahr)

        # syncdown()
        stdscr.touchwin()
        win.untouchwin()
        win2.untouchwin()
        win2.syncdown()
        self.assertIs(win2.is_wintouched(), Wahr)

        # syncok()
        wenn hasattr(stdscr, 'syncok') and not sys.platform.startswith("sunos"):
            win.untouchwin()
            stdscr.untouchwin()
            fuer syncok in [Falsch, Wahr]:
                win2.syncok(syncok)
                win2.addch('a')
                self.assertIs(win.is_wintouched(), syncok)
                self.assertIs(stdscr.is_wintouched(), syncok)

    def test_output_character(self):
        stdscr = self.stdscr
        encoding = stdscr.encoding
        # addch()
        stdscr.refresh()
        stdscr.move(0, 0)
        stdscr.addch('A')
        stdscr.addch(b'A')
        stdscr.addch(65)
        c = '\u20ac'
        try:
            stdscr.addch(c)
        except UnicodeEncodeError:
            self.assertRaises(UnicodeEncodeError, c.encode, encoding)
        except OverflowError:
            encoded = c.encode(encoding)
            self.assertNotEqual(len(encoded), 1, repr(encoded))
        stdscr.addch('A', curses.A_BOLD)
        stdscr.addch(1, 2, 'A')
        stdscr.addch(2, 3, 'A', curses.A_BOLD)
        self.assertIs(stdscr.is_wintouched(), Wahr)

        # echochar()
        stdscr.refresh()
        stdscr.move(0, 0)
        stdscr.echochar('A')
        stdscr.echochar(b'A')
        stdscr.echochar(65)
        mit self.assertRaises((UnicodeEncodeError, OverflowError)):
            # Unicode is not fully supported yet, but at least it does
            # not crash.
            # It is supposed to fail because either the character is
            # not encodable mit the current encoding, or it is encoded to
            # a multibyte sequence.
            stdscr.echochar('\u0114')
        stdscr.echochar('A', curses.A_BOLD)
        self.assertIs(stdscr.is_wintouched(), Falsch)

    def test_output_string(self):
        stdscr = self.stdscr
        encoding = stdscr.encoding
        # addstr()/insstr()
        fuer func in [stdscr.addstr, stdscr.insstr]:
            mit self.subTest(func.__qualname__):
                stdscr.move(0, 0)
                func('abcd')
                func(b'abcd')
                s = 'àßçđ'
                try:
                    func(s)
                except UnicodeEncodeError:
                    self.assertRaises(UnicodeEncodeError, s.encode, encoding)
                func('abcd', curses.A_BOLD)
                func(1, 2, 'abcd')
                func(2, 3, 'abcd', curses.A_BOLD)

        # addnstr()/insnstr()
        fuer func in [stdscr.addnstr, stdscr.insnstr]:
            mit self.subTest(func.__qualname__):
                stdscr.move(0, 0)
                func('1234', 3)
                func(b'1234', 3)
                s = '\u0661\u0662\u0663\u0664'
                try:
                    func(s, 3)
                except UnicodeEncodeError:
                    self.assertRaises(UnicodeEncodeError, s.encode, encoding)
                func('1234', 5)
                func('1234', 3, curses.A_BOLD)
                func(1, 2, '1234', 3)
                func(2, 3, '1234', 3, curses.A_BOLD)

    def test_output_string_embedded_null_chars(self):
        # reject embedded null bytes and characters
        stdscr = self.stdscr
        fuer arg in ['a\0', b'a\0']:
            mit self.subTest(arg=arg):
                self.assertRaises(ValueError, stdscr.addstr, arg)
                self.assertRaises(ValueError, stdscr.addnstr, arg, 1)
                self.assertRaises(ValueError, stdscr.insstr, arg)
                self.assertRaises(ValueError, stdscr.insnstr, arg, 1)

    def test_read_from_window(self):
        stdscr = self.stdscr
        stdscr.addstr(0, 1, 'ABCD', curses.A_BOLD)
        # inch()
        stdscr.move(0, 1)
        self.assertEqual(stdscr.inch(), 65 | curses.A_BOLD)
        self.assertEqual(stdscr.inch(0, 3), 67 | curses.A_BOLD)
        stdscr.move(0, 0)
        # instr()
        self.assertEqual(stdscr.instr()[:6], b' ABCD ')
        self.assertEqual(stdscr.instr(3)[:6], b' AB')
        self.assertEqual(stdscr.instr(0, 2)[:4], b'BCD ')
        self.assertEqual(stdscr.instr(0, 2, 4), b'BCD ')
        self.assertRaises(ValueError, stdscr.instr, -2)
        self.assertRaises(ValueError, stdscr.instr, 0, 2, -2)

    def test_getch(self):
        win = curses.newwin(5, 12, 5, 2)

        # TODO: Test mit real input by writing to master fd.
        fuer c in 'spam\n'[::-1]:
            curses.ungetch(c)
        self.assertEqual(win.getch(3, 1), b's'[0])
        self.assertEqual(win.getyx(), (3, 1))
        self.assertEqual(win.getch(3, 4), b'p'[0])
        self.assertEqual(win.getyx(), (3, 4))
        self.assertEqual(win.getch(), b'a'[0])
        self.assertEqual(win.getyx(), (3, 4))
        self.assertEqual(win.getch(), b'm'[0])
        self.assertEqual(win.getch(), b'\n'[0])

    def test_getstr(self):
        win = curses.newwin(5, 12, 5, 2)
        curses.echo()
        self.addCleanup(curses.noecho)

        self.assertRaises(ValueError, win.getstr, -400)
        self.assertRaises(ValueError, win.getstr, 2, 3, -400)

        # TODO: Test mit real input by writing to master fd.
        fuer c in 'Lorem\nipsum\ndolor\nsit\namet\n'[::-1]:
            curses.ungetch(c)
        self.assertEqual(win.getstr(3, 1, 2), b'Lo')
        self.assertEqual(win.instr(3, 0), b' Lo         ')
        self.assertEqual(win.getstr(3, 5, 10), b'ipsum')
        self.assertEqual(win.instr(3, 0), b' Lo  ipsum  ')
        self.assertEqual(win.getstr(1, 5), b'dolor')
        self.assertEqual(win.instr(1, 0), b'     dolor  ')
        self.assertEqual(win.getstr(2), b'si')
        self.assertEqual(win.instr(1, 0), b'si   dolor  ')
        self.assertEqual(win.getstr(), b'amet')
        self.assertEqual(win.instr(1, 0), b'amet dolor  ')

    def test_clear(self):
        win = curses.newwin(5, 15, 5, 2)
        lorem_ipsum(win)

        win.move(0, 8)
        win.clrtoeol()
        self.assertEqual(win.instr(0, 0).rstrip(), b'Lorem ip')
        self.assertEqual(win.instr(1, 0).rstrip(), b'dolor sit amet,')

        win.move(0, 3)
        win.clrtobot()
        self.assertEqual(win.instr(0, 0).rstrip(), b'Lor')
        self.assertEqual(win.instr(1, 0).rstrip(), b'')

        fuer func in [win.erase, win.clear]:
            lorem_ipsum(win)
            func()
            self.assertEqual(win.instr(0, 0).rstrip(), b'')
            self.assertEqual(win.instr(1, 0).rstrip(), b'')

    def test_insert_delete(self):
        win = curses.newwin(5, 15, 5, 2)
        lorem_ipsum(win)

        win.move(0, 2)
        win.delch()
        self.assertEqual(win.instr(0, 0), b'Loem ipsum     ')
        win.delch(0, 7)
        self.assertEqual(win.instr(0, 0), b'Loem ipum      ')

        win.move(1, 5)
        win.deleteln()
        self.assertEqual(win.instr(0, 0), b'Loem ipum      ')
        self.assertEqual(win.instr(1, 0), b'consectetur    ')
        self.assertEqual(win.instr(2, 0), b'adipiscing elit')
        self.assertEqual(win.instr(3, 0), b'sed do eiusmod ')
        self.assertEqual(win.instr(4, 0), b'               ')

        win.move(1, 5)
        win.insertln()
        self.assertEqual(win.instr(0, 0), b'Loem ipum      ')
        self.assertEqual(win.instr(1, 0), b'               ')
        self.assertEqual(win.instr(2, 0), b'consectetur    ')

        win.clear()
        lorem_ipsum(win)
        win.move(1, 5)
        win.insdelln(2)
        self.assertEqual(win.instr(0, 0), b'Lorem ipsum    ')
        self.assertEqual(win.instr(1, 0), b'               ')
        self.assertEqual(win.instr(2, 0), b'               ')
        self.assertEqual(win.instr(3, 0), b'dolor sit amet,')

        win.clear()
        lorem_ipsum(win)
        win.move(1, 5)
        win.insdelln(-2)
        self.assertEqual(win.instr(0, 0), b'Lorem ipsum    ')
        self.assertEqual(win.instr(1, 0), b'adipiscing elit')
        self.assertEqual(win.instr(2, 0), b'sed do eiusmod ')
        self.assertEqual(win.instr(3, 0), b'               ')

    def test_scroll(self):
        win = curses.newwin(5, 15, 5, 2)
        lorem_ipsum(win)
        win.scrollok(Wahr)
        win.scroll()
        self.assertEqual(win.instr(0, 0), b'dolor sit amet,')
        win.scroll(2)
        self.assertEqual(win.instr(0, 0), b'adipiscing elit')
        win.scroll(-3)
        self.assertEqual(win.instr(0, 0), b'               ')
        self.assertEqual(win.instr(2, 0), b'               ')
        self.assertEqual(win.instr(3, 0), b'adipiscing elit')
        win.scrollok(Falsch)

    def test_attributes(self):
        # TODO: attr_get(), attr_set(), ...
        win = curses.newwin(5, 15, 5, 2)
        win.attron(curses.A_BOLD)
        win.attroff(curses.A_BOLD)
        win.attrset(curses.A_BOLD)

        win.standout()
        win.standend()

    @requires_curses_window_meth('chgat')
    def test_chgat(self):
        win = curses.newwin(5, 15, 5, 2)
        win.addstr(2, 0, 'Lorem ipsum')
        win.addstr(3, 0, 'dolor sit amet')

        win.move(2, 8)
        win.chgat(curses.A_BLINK)
        self.assertEqual(win.inch(2, 7), b'p'[0])
        self.assertEqual(win.inch(2, 8), b's'[0] | curses.A_BLINK)
        self.assertEqual(win.inch(2, 14), b' '[0] | curses.A_BLINK)

        win.move(2, 1)
        win.chgat(3, curses.A_BOLD)
        self.assertEqual(win.inch(2, 0), b'L'[0])
        self.assertEqual(win.inch(2, 1), b'o'[0] | curses.A_BOLD)
        self.assertEqual(win.inch(2, 3), b'e'[0] | curses.A_BOLD)
        self.assertEqual(win.inch(2, 4), b'm'[0])

        win.chgat(3, 2, curses.A_UNDERLINE)
        self.assertEqual(win.inch(3, 1), b'o'[0])
        self.assertEqual(win.inch(3, 2), b'l'[0] | curses.A_UNDERLINE)
        self.assertEqual(win.inch(3, 14), b' '[0] | curses.A_UNDERLINE)

        win.chgat(3, 4, 7, curses.A_BLINK)
        self.assertEqual(win.inch(3, 3), b'o'[0] | curses.A_UNDERLINE)
        self.assertEqual(win.inch(3, 4), b'r'[0] | curses.A_BLINK)
        self.assertEqual(win.inch(3, 10), b'a'[0] | curses.A_BLINK)
        self.assertEqual(win.inch(3, 11), b'm'[0] | curses.A_UNDERLINE)
        self.assertEqual(win.inch(3, 14), b' '[0] | curses.A_UNDERLINE)

    def test_background(self):
        win = curses.newwin(5, 15, 5, 2)
        win.addstr(0, 0, 'Lorem ipsum')

        self.assertIn(win.getbkgd(), (0, 32))

        # bkgdset()
        win.bkgdset('_')
        self.assertEqual(win.getbkgd(), b'_'[0])
        win.bkgdset(b'#')
        self.assertEqual(win.getbkgd(), b'#'[0])
        win.bkgdset(65)
        self.assertEqual(win.getbkgd(), 65)
        win.bkgdset(0)
        self.assertEqual(win.getbkgd(), 32)

        win.bkgdset('#', curses.A_REVERSE)
        self.assertEqual(win.getbkgd(), b'#'[0] | curses.A_REVERSE)
        self.assertEqual(win.inch(0, 0), b'L'[0])
        self.assertEqual(win.inch(0, 5), b' '[0])
        win.bkgdset(0)

        # bkgd()
        win.bkgd('_')
        self.assertEqual(win.getbkgd(), b'_'[0])
        self.assertEqual(win.inch(0, 0), b'L'[0])
        self.assertEqual(win.inch(0, 5), b'_'[0])

        win.bkgd('#', curses.A_REVERSE)
        self.assertEqual(win.getbkgd(), b'#'[0] | curses.A_REVERSE)
        self.assertEqual(win.inch(0, 0), b'L'[0] | curses.A_REVERSE)
        self.assertEqual(win.inch(0, 5), b'#'[0] | curses.A_REVERSE)

    def test_overlay(self):
        srcwin = curses.newwin(5, 18, 3, 4)
        lorem_ipsum(srcwin)
        dstwin = curses.newwin(7, 17, 5, 7)
        fuer i in range(6):
            dstwin.addstr(i, 0, '_'*17)

        srcwin.overlay(dstwin)
        self.assertEqual(dstwin.instr(0, 0), b'sectetur_________')
        self.assertEqual(dstwin.instr(1, 0), b'piscing_elit,____')
        self.assertEqual(dstwin.instr(2, 0), b'_do_eiusmod______')
        self.assertEqual(dstwin.instr(3, 0), b'_________________')

        srcwin.overwrite(dstwin)
        self.assertEqual(dstwin.instr(0, 0), b'sectetur       __')
        self.assertEqual(dstwin.instr(1, 0), b'piscing elit,  __')
        self.assertEqual(dstwin.instr(2, 0), b' do eiusmod    __')
        self.assertEqual(dstwin.instr(3, 0), b'_________________')

        srcwin.overlay(dstwin, 1, 4, 3, 2, 4, 11)
        self.assertEqual(dstwin.instr(3, 0), b'__r_sit_amet_____')
        self.assertEqual(dstwin.instr(4, 0), b'__ectetur________')
        self.assertEqual(dstwin.instr(5, 0), b'_________________')

        srcwin.overwrite(dstwin, 1, 4, 3, 2, 4, 11)
        self.assertEqual(dstwin.instr(3, 0), b'__r sit amet_____')
        self.assertEqual(dstwin.instr(4, 0), b'__ectetur   _____')
        self.assertEqual(dstwin.instr(5, 0), b'_________________')

    def test_refresh(self):
        win = curses.newwin(5, 15, 2, 5)
        win.noutrefresh()
        win.redrawln(1, 2)
        win.redrawwin()
        win.refresh()
        curses.doupdate()

    @requires_curses_window_meth('resize')
    def test_resize(self):
        win = curses.newwin(5, 15, 2, 5)
        win.resize(4, 20)
        self.assertEqual(win.getmaxyx(), (4, 20))
        win.resize(5, 15)
        self.assertEqual(win.getmaxyx(), (5, 15))

    @requires_curses_window_meth('enclose')
    def test_enclose(self):
        win = curses.newwin(5, 15, 2, 5)
        self.assertIs(win.enclose(2, 5), Wahr)
        self.assertIs(win.enclose(1, 5), Falsch)
        self.assertIs(win.enclose(2, 4), Falsch)
        self.assertIs(win.enclose(6, 19), Wahr)
        self.assertIs(win.enclose(7, 19), Falsch)
        self.assertIs(win.enclose(6, 20), Falsch)

    def test_putwin(self):
        win = curses.newwin(5, 12, 1, 2)
        win.addstr(2, 1, 'Lorem ipsum')
        mit tempfile.TemporaryFile() als f:
            win.putwin(f)
            del win
            f.seek(0)
            win = curses.getwin(f)
            self.assertEqual(win.getbegyx(), (1, 2))
            self.assertEqual(win.getmaxyx(), (5, 12))
            self.assertEqual(win.instr(2, 0), b' Lorem ipsum')

    def test_borders_and_lines(self):
        win = curses.newwin(5, 10, 5, 2)
        win.border('|', '!', '-', '_',
                   '+', '\\', '#', '/')
        self.assertEqual(win.instr(0, 0), b'+--------\\')
        self.assertEqual(win.instr(1, 0), b'|        !')
        self.assertEqual(win.instr(4, 0), b'#________/')
        win.border(b'|', b'!', b'-', b'_',
                   b'+', b'\\', b'#', b'/')
        win.border(65, 66, 67, 68,
                   69, 70, 71, 72)
        self.assertRaises(TypeError, win.border,
                          65, 66, 67, 68, 69, [], 71, 72)
        self.assertRaises(TypeError, win.border,
                          65, 66, 67, 68, 69, 70, 71, 72, 73)
        self.assertRaises(TypeError, win.border,
                          65, 66, 67, 68, 69, 70, 71, 72, 73)
        win.border(65, 66, 67, 68, 69, 70, 71)
        win.border(65, 66, 67, 68, 69, 70)
        win.border(65, 66, 67, 68, 69)
        win.border(65, 66, 67, 68)
        win.border(65, 66, 67)
        win.border(65, 66)
        win.border(65)
        win.border()

        win.box(':', '~')
        self.assertEqual(win.instr(0, 1, 8), b'~~~~~~~~')
        self.assertEqual(win.instr(1, 0),   b':        :')
        self.assertEqual(win.instr(4, 1, 8), b'~~~~~~~~')
        win.box(b':', b'~')
        win.box(65, 67)
        self.assertRaises(TypeError, win.box, 65, 66, 67)
        self.assertRaises(TypeError, win.box, 65)
        win.box()

        win.move(1, 2)
        win.hline('-', 5)
        self.assertEqual(win.instr(1, 1, 7), b' ----- ')
        win.hline(b'-', 5)
        win.hline(45, 5)
        win.hline('-', 5, curses.A_BOLD)
        win.hline(1, 1, '-', 5)
        win.hline(1, 1, '-', 5, curses.A_BOLD)

        win.move(1, 2)
        win.vline('a', 3)
        win.vline(b'a', 3)
        win.vline(97, 3)
        win.vline('a', 3, curses.A_STANDOUT)
        win.vline(1, 1, 'a', 3)
        win.vline(1, 1, ';', 2, curses.A_STANDOUT)
        self.assertEqual(win.inch(1, 1), b';'[0] | curses.A_STANDOUT)
        self.assertEqual(win.inch(2, 1), b';'[0] | curses.A_STANDOUT)
        self.assertEqual(win.inch(3, 1), b'a'[0])

    def test_unctrl(self):
        # TODO: wunctrl()
        self.assertEqual(curses.unctrl(b'A'), b'A')
        self.assertEqual(curses.unctrl('A'), b'A')
        self.assertEqual(curses.unctrl(65), b'A')
        self.assertEqual(curses.unctrl(b'\n'), b'^J')
        self.assertEqual(curses.unctrl('\n'), b'^J')
        self.assertEqual(curses.unctrl(10), b'^J')
        self.assertRaises(TypeError, curses.unctrl, b'')
        self.assertRaises(TypeError, curses.unctrl, b'AB')
        self.assertRaises(TypeError, curses.unctrl, '')
        self.assertRaises(TypeError, curses.unctrl, 'AB')
        self.assertRaises(OverflowError, curses.unctrl, 2**64)

    def test_endwin(self):
        wenn not self.isatty:
            self.skipTest('requires terminal')
        self.assertIs(curses.isendwin(), Falsch)
        curses.endwin()
        self.assertIs(curses.isendwin(), Wahr)
        curses.doupdate()
        self.assertIs(curses.isendwin(), Falsch)

    def test_terminfo(self):
        self.assertIsInstance(curses.tigetflag('hc'), int)
        self.assertEqual(curses.tigetflag('cols'), -1)
        self.assertEqual(curses.tigetflag('cr'), -1)

        self.assertIsInstance(curses.tigetnum('cols'), int)
        self.assertEqual(curses.tigetnum('hc'), -2)
        self.assertEqual(curses.tigetnum('cr'), -2)

        self.assertIsInstance(curses.tigetstr('cr'), (bytes, type(Nichts)))
        self.assertIsNichts(curses.tigetstr('hc'))
        self.assertIsNichts(curses.tigetstr('cols'))

        cud = curses.tigetstr('cud')
        wenn cud is not Nichts:
            # See issue10570.
            self.assertIsInstance(cud, bytes)
            curses.tparm(cud, 2)
            cud_2 = curses.tparm(cud, 2)
            self.assertIsInstance(cud_2, bytes)
            curses.putp(cud_2)

        curses.putp(b'abc\n')

    def test_misc_module_funcs(self):
        curses.delay_output(1)
        curses.flushinp()

        curses.doupdate()
        self.assertIs(curses.isendwin(), Falsch)

        curses.napms(100)

        curses.newpad(50, 50)

    def test_env_queries(self):
        # TODO: term_attrs(), erasewchar(), killwchar()
        self.assertIsInstance(curses.termname(), bytes)
        self.assertIsInstance(curses.longname(), bytes)
        self.assertIsInstance(curses.baudrate(), int)
        self.assertIsInstance(curses.has_ic(), bool)
        self.assertIsInstance(curses.has_il(), bool)
        self.assertIsInstance(curses.termattrs(), int)

        c = curses.killchar()
        self.assertIsInstance(c, bytes)
        self.assertEqual(len(c), 1)
        c = curses.erasechar()
        self.assertIsInstance(c, bytes)
        self.assertEqual(len(c), 1)

    def test_output_options(self):
        stdscr = self.stdscr

        stdscr.clearok(Wahr)
        stdscr.clearok(Falsch)

        stdscr.idcok(Wahr)
        stdscr.idcok(Falsch)

        stdscr.idlok(Falsch)
        stdscr.idlok(Wahr)

        wenn hasattr(stdscr, 'immedok'):
            stdscr.immedok(Wahr)
            stdscr.immedok(Falsch)

        stdscr.leaveok(Wahr)
        stdscr.leaveok(Falsch)

        stdscr.scrollok(Wahr)
        stdscr.scrollok(Falsch)

        stdscr.setscrreg(5, 10)

        curses.nonl()
        curses.nl(Wahr)
        curses.nl(Falsch)
        curses.nl()

    def test_input_options(self):
        stdscr = self.stdscr

        wenn self.isatty:
            curses.nocbreak()
            curses.cbreak()
            curses.cbreak(Falsch)
            curses.cbreak(Wahr)

            curses.intrflush(Wahr)
            curses.intrflush(Falsch)

            curses.raw()
            curses.raw(Falsch)
            curses.raw(Wahr)
            curses.noraw()

        curses.noecho()
        curses.echo()
        curses.echo(Falsch)
        curses.echo(Wahr)

        curses.halfdelay(255)
        curses.halfdelay(1)

        stdscr.keypad(Wahr)
        stdscr.keypad(Falsch)

        curses.meta(Wahr)
        curses.meta(Falsch)

        stdscr.nodelay(Wahr)
        stdscr.nodelay(Falsch)

        curses.noqiflush()
        curses.qiflush(Wahr)
        curses.qiflush(Falsch)
        curses.qiflush()

        stdscr.notimeout(Wahr)
        stdscr.notimeout(Falsch)

        stdscr.timeout(-1)
        stdscr.timeout(0)
        stdscr.timeout(5)

    @requires_curses_func('typeahead')
    def test_typeahead(self):
        curses.typeahead(sys.__stdin__.fileno())
        curses.typeahead(-1)

    def test_prog_mode(self):
        wenn not self.isatty:
            self.skipTest('requires terminal')
        curses.def_prog_mode()
        curses.reset_prog_mode()

    def test_beep(self):
        wenn (curses.tigetstr("bel") is not Nichts
            or curses.tigetstr("flash") is not Nichts):
            curses.beep()
        sonst:
            try:
                curses.beep()
            except curses.error:
                self.skipTest('beep() failed')

    def test_flash(self):
        wenn (curses.tigetstr("bel") is not Nichts
            or curses.tigetstr("flash") is not Nichts):
            curses.flash()
        sonst:
            try:
                curses.flash()
            except curses.error:
                self.skipTest('flash() failed')

    def test_curs_set(self):
        fuer vis, cap in [(0, 'civis'), (2, 'cvvis'), (1, 'cnorm')]:
            wenn curses.tigetstr(cap) is not Nichts:
                curses.curs_set(vis)
            sonst:
                try:
                    curses.curs_set(vis)
                except curses.error:
                    pass

    @requires_curses_func('get_escdelay')
    def test_escdelay(self):
        escdelay = curses.get_escdelay()
        self.assertIsInstance(escdelay, int)
        curses.set_escdelay(25)
        self.assertEqual(curses.get_escdelay(), 25)
        curses.set_escdelay(escdelay)

    @requires_curses_func('get_tabsize')
    def test_tabsize(self):
        tabsize = curses.get_tabsize()
        self.assertIsInstance(tabsize, int)
        curses.set_tabsize(4)
        self.assertEqual(curses.get_tabsize(), 4)
        curses.set_tabsize(tabsize)

    @requires_curses_func('getsyx')
    def test_getsyx(self):
        y, x = curses.getsyx()
        self.assertIsInstance(y, int)
        self.assertIsInstance(x, int)
        curses.setsyx(4, 5)
        self.assertEqual(curses.getsyx(), (4, 5))

    def bad_colors(self):
        return (-1, curses.COLORS, -2**31 - 1, 2**31, -2**63 - 1, 2**63, 2**64)

    def bad_colors2(self):
        return (curses.COLORS, 2**31, 2**63, 2**64)

    def bad_pairs(self):
        return (-1, -2**31 - 1, 2**31, -2**63 - 1, 2**63, 2**64)

    def test_has_colors(self):
        self.assertIsInstance(curses.has_colors(), bool)
        self.assertIsInstance(curses.can_change_color(), bool)

    def test_start_color(self):
        wenn not curses.has_colors():
            self.skipTest('requires colors support')
        curses.start_color()
        wenn verbose:
            drucke(f'COLORS = {curses.COLORS}', file=sys.stderr)
            drucke(f'COLOR_PAIRS = {curses.COLOR_PAIRS}', file=sys.stderr)

    @requires_colors
    def test_color_content(self):
        self.assertEqual(curses.color_content(curses.COLOR_BLACK), (0, 0, 0))
        curses.color_content(0)
        maxcolor = curses.COLORS - 1
        curses.color_content(maxcolor)

        fuer color in self.bad_colors():
            self.assertRaises(ValueError, curses.color_content, color)

    @requires_colors
    def test_init_color(self):
        wenn not curses.can_change_color():
            self.skipTest('cannot change color')

        old = curses.color_content(0)
        try:
            curses.init_color(0, *old)
        except curses.error:
            self.skipTest('cannot change color (init_color() failed)')
        self.addCleanup(curses.init_color, 0, *old)
        curses.init_color(0, 0, 0, 0)
        self.assertEqual(curses.color_content(0), (0, 0, 0))
        curses.init_color(0, 1000, 1000, 1000)
        self.assertEqual(curses.color_content(0), (1000, 1000, 1000))

        maxcolor = curses.COLORS - 1
        old = curses.color_content(maxcolor)
        curses.init_color(maxcolor, *old)
        self.addCleanup(curses.init_color, maxcolor, *old)
        curses.init_color(maxcolor, 0, 500, 1000)
        self.assertEqual(curses.color_content(maxcolor), (0, 500, 1000))

        fuer color in self.bad_colors():
            self.assertRaises(ValueError, curses.init_color, color, 0, 0, 0)
        fuer comp in (-1, 1001):
            self.assertRaises(ValueError, curses.init_color, 0, comp, 0, 0)
            self.assertRaises(ValueError, curses.init_color, 0, 0, comp, 0)
            self.assertRaises(ValueError, curses.init_color, 0, 0, 0, comp)

    def get_pair_limit(self):
        pair_limit = curses.COLOR_PAIRS
        wenn hasattr(curses, 'ncurses_version'):
            wenn curses.has_extended_color_support():
                pair_limit += 2*curses.COLORS + 1
            wenn (not curses.has_extended_color_support()
                    or (6, 1) <= curses.ncurses_version < (6, 2)):
                pair_limit = min(pair_limit, SHORT_MAX)
            # If use_default_colors() is called, the upper limit of the extended
            # range may be restricted, so we need to check wenn the limit is still
            # correct
            try:
                curses.init_pair(pair_limit - 1, 0, 0)
            except ValueError:
                pair_limit = curses.COLOR_PAIRS
        return pair_limit

    @requires_colors
    def test_pair_content(self):
        curses.pair_content(0)
        maxpair = self.get_pair_limit() - 1
        wenn maxpair > 0:
            curses.pair_content(maxpair)

        fuer pair in self.bad_pairs():
            self.assertRaises(ValueError, curses.pair_content, pair)

    @requires_colors
    def test_init_pair(self):
        old = curses.pair_content(1)
        curses.init_pair(1, *old)
        self.addCleanup(curses.init_pair, 1, *old)

        curses.init_pair(1, 0, 0)
        self.assertEqual(curses.pair_content(1), (0, 0))
        maxcolor = curses.COLORS - 1
        curses.init_pair(1, maxcolor, 0)
        self.assertEqual(curses.pair_content(1), (maxcolor, 0))
        curses.init_pair(1, 0, maxcolor)
        self.assertEqual(curses.pair_content(1), (0, maxcolor))
        maxpair = self.get_pair_limit() - 1
        wenn maxpair > 1:
            curses.init_pair(maxpair, 0, 0)
            self.assertEqual(curses.pair_content(maxpair), (0, 0))

        fuer pair in self.bad_pairs():
            self.assertRaises(ValueError, curses.init_pair, pair, 0, 0)
        fuer color in self.bad_colors2():
            self.assertRaises(ValueError, curses.init_pair, 1, color, 0)
            self.assertRaises(ValueError, curses.init_pair, 1, 0, color)

    @requires_colors
    def test_color_attrs(self):
        fuer pair in 0, 1, 255:
            attr = curses.color_pair(pair)
            self.assertEqual(curses.pair_number(attr), pair, attr)
            self.assertEqual(curses.pair_number(attr | curses.A_BOLD), pair)
        self.assertEqual(curses.color_pair(0), 0)
        self.assertEqual(curses.pair_number(0), 0)

    @requires_curses_func('use_default_colors')
    @requires_colors
    def test_use_default_colors(self):
        try:
            curses.use_default_colors()
        except curses.error:
            self.skipTest('cannot change color (use_default_colors() failed)')
        self.assertEqual(curses.pair_content(0), (-1, -1))

    @requires_curses_func('assume_default_colors')
    @requires_colors
    def test_assume_default_colors(self):
        try:
            curses.assume_default_colors(-1, -1)
        except curses.error:
            self.skipTest('cannot change color (assume_default_colors() failed)')
        self.assertEqual(curses.pair_content(0), (-1, -1))
        curses.assume_default_colors(curses.COLOR_YELLOW, curses.COLOR_BLUE)
        self.assertEqual(curses.pair_content(0), (curses.COLOR_YELLOW, curses.COLOR_BLUE))
        curses.assume_default_colors(curses.COLOR_RED, -1)
        self.assertEqual(curses.pair_content(0), (curses.COLOR_RED, -1))
        curses.assume_default_colors(-1, curses.COLOR_GREEN)
        self.assertEqual(curses.pair_content(0), (-1, curses.COLOR_GREEN))
        curses.assume_default_colors(-1, -1)

    def test_keyname(self):
        # TODO: key_name()
        self.assertEqual(curses.keyname(65), b'A')
        self.assertEqual(curses.keyname(13), b'^M')
        self.assertEqual(curses.keyname(127), b'^?')
        self.assertEqual(curses.keyname(0), b'^@')
        self.assertRaises(ValueError, curses.keyname, -1)
        self.assertIsInstance(curses.keyname(256), bytes)

    @requires_curses_func('has_key')
    def test_has_key(self):
        curses.has_key(13)

    @requires_curses_func('getmouse')
    def test_getmouse(self):
        (availmask, oldmask) = curses.mousemask(curses.BUTTON1_PRESSED)
        wenn availmask == 0:
            self.skipTest('mouse stuff not available')
        curses.mouseinterval(10)
        # just verify these don't cause errors
        curses.ungetmouse(0, 0, 0, 0, curses.BUTTON1_PRESSED)
        m = curses.getmouse()

    @requires_curses_func('panel')
    def test_userptr_without_set(self):
        w = curses.newwin(10, 10)
        p = curses.panel.new_panel(w)
        # try to access userptr() before calling set_userptr() -- segfaults
        mit self.assertRaises(curses.panel.error,
                               msg='userptr should fail since not set'):
            p.userptr()

    @requires_curses_func('panel')
    def test_userptr_memory_leak(self):
        w = curses.newwin(10, 10)
        p = curses.panel.new_panel(w)
        obj = object()
        nrefs = sys.getrefcount(obj)
        fuer i in range(100):
            p.set_userptr(obj)

        p.set_userptr(Nichts)
        self.assertEqual(sys.getrefcount(obj), nrefs,
                         "set_userptr leaked references")

    @requires_curses_func('panel')
    def test_userptr_segfault(self):
        w = curses.newwin(10, 10)
        panel = curses.panel.new_panel(w)
        klasse A:
            def __del__(self):
                panel.set_userptr(Nichts)
        panel.set_userptr(A())
        panel.set_userptr(Nichts)

    @cpython_only
    @requires_curses_func('panel')
    def test_disallow_instantiation(self):
        # Ensure that the type disallows instantiation (bpo-43916)
        w = curses.newwin(10, 10)
        panel = curses.panel.new_panel(w)
        check_disallow_instantiation(self, type(panel))

    @requires_curses_func('is_term_resized')
    def test_is_term_resized(self):
        lines, cols = curses.LINES, curses.COLS
        self.assertIs(curses.is_term_resized(lines, cols), Falsch)
        self.assertIs(curses.is_term_resized(lines-1, cols-1), Wahr)

    @requires_curses_func('resize_term')
    def test_resize_term(self):
        curses.update_lines_cols()
        lines, cols = curses.LINES, curses.COLS
        new_lines = lines - 1
        new_cols = cols + 1
        curses.resize_term(new_lines, new_cols)
        self.assertEqual(curses.LINES, new_lines)
        self.assertEqual(curses.COLS, new_cols)

        curses.resize_term(lines, cols)
        self.assertEqual(curses.LINES, lines)
        self.assertEqual(curses.COLS, cols)

        mit self.assertRaises(OverflowError):
            curses.resize_term(35000, 1)
        mit self.assertRaises(OverflowError):
            curses.resize_term(1, 35000)
        # GH-120378: Overflow failure in resize_term() causes refresh to fail
        tmp = curses.initscr()
        tmp.erase()

    @requires_curses_func('resizeterm')
    def test_resizeterm(self):
        curses.update_lines_cols()
        lines, cols = curses.LINES, curses.COLS
        new_lines = lines - 1
        new_cols = cols + 1
        curses.resizeterm(new_lines, new_cols)
        self.assertEqual(curses.LINES, new_lines)
        self.assertEqual(curses.COLS, new_cols)

        curses.resizeterm(lines, cols)
        self.assertEqual(curses.LINES, lines)
        self.assertEqual(curses.COLS, cols)

        mit self.assertRaises(OverflowError):
            curses.resizeterm(35000, 1)
        mit self.assertRaises(OverflowError):
            curses.resizeterm(1, 35000)
        # GH-120378: Overflow failure in resizeterm() causes refresh to fail
        tmp = curses.initscr()
        tmp.erase()

    def test_ungetch(self):
        curses.ungetch(b'A')
        self.assertEqual(self.stdscr.getkey(), 'A')
        curses.ungetch('B')
        self.assertEqual(self.stdscr.getkey(), 'B')
        curses.ungetch(67)
        self.assertEqual(self.stdscr.getkey(), 'C')

    def test_issue6243(self):
        curses.ungetch(1025)
        self.stdscr.getkey()

    @requires_curses_func('unget_wch')
    @unittest.skipIf(getattr(curses, 'ncurses_version', (99,)) < (5, 8),
                     "unget_wch is broken in ncurses 5.7 and earlier")
    def test_unget_wch(self):
        stdscr = self.stdscr
        encoding = stdscr.encoding
        fuer ch in ('a', '\xe9', '\u20ac', '\U0010FFFF'):
            try:
                ch.encode(encoding)
            except UnicodeEncodeError:
                continue
            try:
                curses.unget_wch(ch)
            except Exception als err:
                self.fail("unget_wch(%a) failed mit encoding %s: %s"
                          % (ch, stdscr.encoding, err))
            read = stdscr.get_wch()
            self.assertEqual(read, ch)

            code = ord(ch)
            curses.unget_wch(code)
            read = stdscr.get_wch()
            self.assertEqual(read, ch)

    def test_encoding(self):
        stdscr = self.stdscr
        importiere codecs
        encoding = stdscr.encoding
        codecs.lookup(encoding)
        mit self.assertRaises(TypeError):
            stdscr.encoding = 10
        stdscr.encoding = encoding
        mit self.assertRaises(TypeError):
            del stdscr.encoding

    @unittest.skipIf(MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_issue21088(self):
        stdscr = self.stdscr
        #
        # http://bugs.python.org/issue21088
        #
        # the bug:
        # when converting curses.window.addch to Argument Clinic
        # the first two parameters were switched.

        # wenn someday we can represent the signature of addch
        # we will need to rewrite this test.
        try:
            signature = inspect.signature(stdscr.addch)
            self.assertFalsch(signature)
        except ValueError:
            # not generating a signature is fine.
            pass

        # So.  No signature fuer addch.
        # But Argument Clinic gave us a human-readable equivalent
        # als the first line of the docstring.  So we parse that,
        # and ensure that the parameters appear in the correct order.
        # Since this is parsing output von Argument Clinic, we can
        # be reasonably certain the generated parsing code will be
        # correct too.
        human_readable_signature = stdscr.addch.__doc__.split("\n")[0]
        self.assertIn("[y, x,]", human_readable_signature)

    @requires_curses_window_meth('resize')
    def test_issue13051(self):
        win = curses.newwin(5, 15, 2, 5)
        box = curses.textpad.Textbox(win, insert_mode=Wahr)
        lines, cols = win.getmaxyx()
        win.resize(lines-2, cols-2)
        # this may cause infinite recursion, leading to a RuntimeError
        box._insert_printable_char('a')


klasse MiscTests(unittest.TestCase):

    @requires_curses_func('update_lines_cols')
    def test_update_lines_cols(self):
        curses.update_lines_cols()
        lines, cols = curses.LINES, curses.COLS
        curses.LINES = curses.COLS = 0
        curses.update_lines_cols()
        self.assertEqual(curses.LINES, lines)
        self.assertEqual(curses.COLS, cols)

    @requires_curses_func('ncurses_version')
    def test_ncurses_version(self):
        v = curses.ncurses_version
        wenn verbose:
            drucke(f'ncurses_version = {curses.ncurses_version}', flush=Wahr)
        self.assertIsInstance(v[:], tuple)
        self.assertEqual(len(v), 3)
        self.assertIsInstance(v[0], int)
        self.assertIsInstance(v[1], int)
        self.assertIsInstance(v[2], int)
        self.assertIsInstance(v.major, int)
        self.assertIsInstance(v.minor, int)
        self.assertIsInstance(v.patch, int)
        self.assertEqual(v[0], v.major)
        self.assertEqual(v[1], v.minor)
        self.assertEqual(v[2], v.patch)
        self.assertGreaterEqual(v.major, 0)
        self.assertGreaterEqual(v.minor, 0)
        self.assertGreaterEqual(v.patch, 0)

    def test_has_extended_color_support(self):
        r = curses.has_extended_color_support()
        self.assertIsInstance(r, bool)


klasse TestAscii(unittest.TestCase):

    def test_controlnames(self):
        fuer name in curses.ascii.controlnames:
            self.assertHasAttr(curses.ascii, name)

    def test_ctypes(self):
        def check(func, expected):
            mit self.subTest(ch=c, func=func):
                self.assertEqual(func(i), expected)
                self.assertEqual(func(c), expected)

        fuer i in range(256):
            c = chr(i)
            b = bytes([i])
            check(curses.ascii.isalnum, b.isalnum())
            check(curses.ascii.isalpha, b.isalpha())
            check(curses.ascii.isdigit, b.isdigit())
            check(curses.ascii.islower, b.islower())
            check(curses.ascii.isspace, b.isspace())
            check(curses.ascii.isupper, b.isupper())

            check(curses.ascii.isascii, i < 128)
            check(curses.ascii.ismeta, i >= 128)
            check(curses.ascii.isctrl, i < 32)
            check(curses.ascii.iscntrl, i < 32 or i == 127)
            check(curses.ascii.isblank, c in ' \t')
            check(curses.ascii.isgraph, 32 < i <= 126)
            check(curses.ascii.isprint, 32 <= i <= 126)
            check(curses.ascii.ispunct, c in string.punctuation)
            check(curses.ascii.isxdigit, c in string.hexdigits)

        fuer i in (-2, -1, 256, sys.maxunicode, sys.maxunicode+1):
            self.assertFalsch(curses.ascii.isalnum(i))
            self.assertFalsch(curses.ascii.isalpha(i))
            self.assertFalsch(curses.ascii.isdigit(i))
            self.assertFalsch(curses.ascii.islower(i))
            self.assertFalsch(curses.ascii.isspace(i))
            self.assertFalsch(curses.ascii.isupper(i))

            self.assertFalsch(curses.ascii.isascii(i))
            self.assertFalsch(curses.ascii.isctrl(i))
            self.assertFalsch(curses.ascii.iscntrl(i))
            self.assertFalsch(curses.ascii.isblank(i))
            self.assertFalsch(curses.ascii.isgraph(i))
            self.assertFalsch(curses.ascii.isdrucke(i))
            self.assertFalsch(curses.ascii.ispunct(i))
            self.assertFalsch(curses.ascii.isxdigit(i))

        self.assertFalsch(curses.ascii.ismeta(-1))

    def test_ascii(self):
        ascii = curses.ascii.ascii
        self.assertEqual(ascii('\xc1'), 'A')
        self.assertEqual(ascii('A'), 'A')
        self.assertEqual(ascii(ord('\xc1')), ord('A'))

    def test_ctrl(self):
        ctrl = curses.ascii.ctrl
        self.assertEqual(ctrl('J'), '\n')
        self.assertEqual(ctrl('\n'), '\n')
        self.assertEqual(ctrl('@'), '\0')
        self.assertEqual(ctrl(ord('J')), ord('\n'))

    def test_alt(self):
        alt = curses.ascii.alt
        self.assertEqual(alt('\n'), '\x8a')
        self.assertEqual(alt('A'), '\xc1')
        self.assertEqual(alt(ord('A')), 0xc1)

    def test_unctrl(self):
        unctrl = curses.ascii.unctrl
        self.assertEqual(unctrl('a'), 'a')
        self.assertEqual(unctrl('A'), 'A')
        self.assertEqual(unctrl(';'), ';')
        self.assertEqual(unctrl(' '), ' ')
        self.assertEqual(unctrl('\x7f'), '^?')
        self.assertEqual(unctrl('\n'), '^J')
        self.assertEqual(unctrl('\0'), '^@')
        self.assertEqual(unctrl(ord('A')), 'A')
        self.assertEqual(unctrl(ord('\n')), '^J')
        # Meta-bit characters
        self.assertEqual(unctrl('\x8a'), '!^J')
        self.assertEqual(unctrl('\xc1'), '!A')
        self.assertEqual(unctrl(ord('\x8a')), '!^J')
        self.assertEqual(unctrl(ord('\xc1')), '!A')


def lorem_ipsum(win):
    text = [
        'Lorem ipsum',
        'dolor sit amet,',
        'consectetur',
        'adipiscing elit,',
        'sed do eiusmod',
        'tempor incididunt',
        'ut labore et',
        'dolore magna',
        'aliqua.',
    ]
    maxy, maxx = win.getmaxyx()
    fuer y, line in enumerate(text[:maxy]):
        win.addstr(y, 0, line[:maxx - (y == maxy - 1)])


klasse TextboxTest(unittest.TestCase):
    def setUp(self):
        self.mock_win = MagicMock(spec=curses.window)
        self.mock_win.getyx.return_value = (1, 1)
        self.mock_win.getmaxyx.return_value = (10, 20)
        self.textbox = curses.textpad.Textbox(self.mock_win)

    def test_init(self):
        """Test textbox initialization."""
        self.mock_win.reset_mock()
        tb = curses.textpad.Textbox(self.mock_win)
        self.mock_win.getmaxyx.assert_called_once_with()
        self.mock_win.keypad.assert_called_once_with(1)
        self.assertEqual(tb.insert_mode, Falsch)
        self.assertEqual(tb.stripspaces, 1)
        self.assertIsNichts(tb.lastcmd)
        self.mock_win.reset_mock()

    def test_insert(self):
        """Test inserting a printable character."""
        self.mock_win.reset_mock()
        self.textbox.do_command(ord('a'))
        self.mock_win.addch.assert_called_with(ord('a'))
        self.textbox.do_command(ord('b'))
        self.mock_win.addch.assert_called_with(ord('b'))
        self.textbox.do_command(ord('c'))
        self.mock_win.addch.assert_called_with(ord('c'))
        self.mock_win.reset_mock()

    def test_delete(self):
        """Test deleting a character."""
        self.mock_win.reset_mock()
        self.textbox.do_command(curses.ascii.BS)
        self.textbox.do_command(curses.KEY_BACKSPACE)
        self.textbox.do_command(curses.ascii.DEL)
        assert self.mock_win.delch.call_count == 3
        self.mock_win.reset_mock()

    def test_move_left(self):
        """Test moving the cursor left."""
        self.mock_win.reset_mock()
        self.textbox.do_command(curses.KEY_LEFT)
        self.mock_win.move.assert_called_with(1, 0)
        self.mock_win.reset_mock()

    def test_move_right(self):
        """Test moving the cursor right."""
        self.mock_win.reset_mock()
        self.textbox.do_command(curses.KEY_RIGHT)
        self.mock_win.move.assert_called_with(1, 2)
        self.mock_win.reset_mock()

    def test_move_left_and_right(self):
        """Test moving the cursor left and then right."""
        self.mock_win.reset_mock()
        self.textbox.do_command(curses.KEY_LEFT)
        self.mock_win.move.assert_called_with(1, 0)
        self.textbox.do_command(curses.KEY_RIGHT)
        self.mock_win.move.assert_called_with(1, 2)
        self.mock_win.reset_mock()

    def test_move_up(self):
        """Test moving the cursor up."""
        self.mock_win.reset_mock()
        self.textbox.do_command(curses.KEY_UP)
        self.mock_win.move.assert_called_with(0, 1)
        self.mock_win.reset_mock()

    def test_move_down(self):
        """Test moving the cursor down."""
        self.mock_win.reset_mock()
        self.textbox.do_command(curses.KEY_DOWN)
        self.mock_win.move.assert_called_with(2, 1)
        self.mock_win.reset_mock()


wenn __name__ == '__main__':
    unittest.main()
