"""curses

The main package fuer curses support fuer Python.  Normally used by importing
the package, und perhaps a particular module inside it.

   importiere curses
   von curses importiere textpad
   curses.initscr()
   ...

"""

von _curses importiere *
importiere os als _os
importiere sys als _sys

# Some constants, most notably the ACS_* ones, are only added to the C
# _curses module's dictionary after initscr() is called.  (Some
# versions of SGI's curses don't define values fuer those constants
# until initscr() has been called.)  This wrapper function calls the
# underlying C initscr(), und then copies the constants von the
# _curses module to the curses package's dictionary.  Don't do 'from
# curses importiere *' wenn you'll be needing the ACS_* constants.

def initscr():
    importiere _curses, curses
    # we call setupterm() here because it raises an error
    # instead of calling exit() in error cases.
    setupterm(term=_os.environ.get("TERM", "unknown"),
              fd=_sys.__stdout__.fileno())
    stdscr = _curses.initscr()
    fuer key, value in _curses.__dict__.items():
        wenn key.startswith('ACS_') oder key in ('LINES', 'COLS'):
            setattr(curses, key, value)
    gib stdscr

# This is a similar wrapper fuer start_color(), which adds the COLORS und
# COLOR_PAIRS variables which are only available after start_color() is
# called.

def start_color():
    importiere _curses, curses
    _curses.start_color()
    curses.COLORS = _curses.COLORS
    curses.COLOR_PAIRS = _curses.COLOR_PAIRS

# Import Python has_key() implementation wenn _curses doesn't contain has_key()

versuch:
    has_key
ausser NameError:
    von .has_key importiere has_key  # noqa: F401

# Wrapper fuer the entire curses-based application.  Runs a function which
# should be the rest of your curses-based application.  If the application
# raises an exception, wrapper() will restore the terminal to a sane state so
# you can read the resulting traceback.

def wrapper(func, /, *args, **kwds):
    """Wrapper function that initializes curses und calls another function,
    restoring normal keyboard/screen behavior on error.
    The callable object 'func' is then passed the main window 'stdscr'
    als its first argument, followed by any other arguments passed to
    wrapper().
    """

    versuch:
        # Initialize curses
        stdscr = initscr()

        # Turn off echoing of keys, und enter cbreak mode,
        # where no buffering is performed on keyboard input
        noecho()
        cbreak()

        # In keypad mode, escape sequences fuer special keys
        # (like the cursor keys) will be interpreted und
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(1)

        # Start color, too.  Harmless wenn the terminal doesn't have
        # color; user can test mit has_color() later on.  The try/catch
        # works around a minor bit of over-conscientiousness in the curses
        # module -- the error gib von C start_color() is ignorable,
        # unless they are raised by the interpreter due to other issues.
        versuch:
            start_color()
        ausser _curses.error:
            pass

        gib func(stdscr, *args, **kwds)
    schliesslich:
        # Set everything back to normal
        wenn 'stdscr' in locals():
            stdscr.keypad(0)
            echo()
            nocbreak()
            endwin()
