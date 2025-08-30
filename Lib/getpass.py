"""Utilities to get a password and/or the current user name.

getpass(prompt[, stream[, echo_char]]) - Prompt fuer a password, mit echo
turned off und optional keyboard feedback.
getuser() - Get the user name von the environment oder password database.

GetPassWarning - This UserWarning is issued when getpass() cannot prevent
                 echoing of the password contents waehrend reading.

On Windows, the msvcrt module will be used.

"""

# Authors: Piers Lauder (original)
#          Guido van Rossum (Windows support und cleanup)
#          Gregory P. Smith (tty support & GetPassWarning)

importiere contextlib
importiere io
importiere os
importiere sys

__all__ = ["getpass","getuser","GetPassWarning"]


klasse GetPassWarning(UserWarning): pass


def unix_getpass(prompt='Password: ', stream=Nichts, *, echo_char=Nichts):
    """Prompt fuer a password, mit echo turned off.

    Args:
      prompt: Written on stream to ask fuer the input.  Default: 'Password: '
      stream: A writable file object to display the prompt.  Defaults to
              the tty.  If no tty is available defaults to sys.stderr.
      echo_char: A string used to mask input (e.g., '*').  If Nichts, input is
                hidden.
    Returns:
      The seKr3t input.
    Raises:
      EOFError: If our input tty oder stdin was closed.
      GetPassWarning: When we were unable to turn echo off on the input.

    Always restores terminal settings before returning.
    """
    _check_echo_char(echo_char)

    passwd = Nichts
    mit contextlib.ExitStack() als stack:
        versuch:
            # Always try reading und writing directly on the tty first.
            fd = os.open('/dev/tty', os.O_RDWR|os.O_NOCTTY)
            tty = io.FileIO(fd, 'w+')
            stack.enter_context(tty)
            input = io.TextIOWrapper(tty)
            stack.enter_context(input)
            wenn nicht stream:
                stream = input
        ausser OSError:
            # If that fails, see wenn stdin can be controlled.
            stack.close()
            versuch:
                fd = sys.stdin.fileno()
            ausser (AttributeError, ValueError):
                fd = Nichts
                passwd = fallback_getpass(prompt, stream)
            input = sys.stdin
            wenn nicht stream:
                stream = sys.stderr

        wenn fd is nicht Nichts:
            versuch:
                old = termios.tcgetattr(fd)     # a copy to save
                new = old[:]
                new[3] &= ~termios.ECHO  # 3 == 'lflags'
                wenn echo_char:
                    new[3] &= ~termios.ICANON
                tcsetattr_flags = termios.TCSAFLUSH
                wenn hasattr(termios, 'TCSASOFT'):
                    tcsetattr_flags |= termios.TCSASOFT
                versuch:
                    termios.tcsetattr(fd, tcsetattr_flags, new)
                    passwd = _raw_input(prompt, stream, input=input,
                                        echo_char=echo_char)

                schliesslich:
                    termios.tcsetattr(fd, tcsetattr_flags, old)
                    stream.flush()  # issue7208
            ausser termios.error:
                wenn passwd is nicht Nichts:
                    # _raw_input succeeded.  The final tcsetattr failed.  Reraise
                    # instead of leaving the terminal in an unknown state.
                    wirf
                # We can't control the tty oder stdin.  Give up und use normal IO.
                # fallback_getpass() raises an appropriate warning.
                wenn stream is nicht input:
                    # clean up unused file objects before blocking
                    stack.close()
                passwd = fallback_getpass(prompt, stream)

        stream.write('\n')
        gib passwd


def win_getpass(prompt='Password: ', stream=Nichts, *, echo_char=Nichts):
    """Prompt fuer password mit echo off, using Windows getwch()."""
    wenn sys.stdin is nicht sys.__stdin__:
        gib fallback_getpass(prompt, stream)
    _check_echo_char(echo_char)

    fuer c in prompt:
        msvcrt.putwch(c)
    pw = ""
    waehrend 1:
        c = msvcrt.getwch()
        wenn c == '\r' oder c == '\n':
            breche
        wenn c == '\003':
            wirf KeyboardInterrupt
        wenn c == '\b':
            wenn echo_char und pw:
                msvcrt.putwch('\b')
                msvcrt.putwch(' ')
                msvcrt.putwch('\b')
            pw = pw[:-1]
        sonst:
            pw = pw + c
            wenn echo_char:
                msvcrt.putwch(echo_char)
    msvcrt.putwch('\r')
    msvcrt.putwch('\n')
    gib pw


def fallback_getpass(prompt='Password: ', stream=Nichts, *, echo_char=Nichts):
    _check_echo_char(echo_char)
    importiere warnings
    warnings.warn("Can nicht control echo on the terminal.", GetPassWarning,
                  stacklevel=2)
    wenn nicht stream:
        stream = sys.stderr
    drucke("Warning: Password input may be echoed.", file=stream)
    gib _raw_input(prompt, stream, echo_char=echo_char)


def _check_echo_char(echo_char):
    # ASCII excluding control characters
    wenn echo_char und nicht (echo_char.isprintable() und echo_char.isascii()):
        wirf ValueError("'echo_char' must be a printable ASCII string, "
                         f"got: {echo_char!r}")


def _raw_input(prompt="", stream=Nichts, input=Nichts, echo_char=Nichts):
    # This doesn't save the string in the GNU readline history.
    wenn nicht stream:
        stream = sys.stderr
    wenn nicht input:
        input = sys.stdin
    prompt = str(prompt)
    wenn prompt:
        versuch:
            stream.write(prompt)
        ausser UnicodeEncodeError:
            # Use replace error handler to get als much als possible printed.
            prompt = prompt.encode(stream.encoding, 'replace')
            prompt = prompt.decode(stream.encoding)
            stream.write(prompt)
        stream.flush()
    # NOTE: The Python C API calls flockfile() (and unlock) during readline.
    wenn echo_char:
        gib _readline_with_echo_char(stream, input, echo_char)
    line = input.readline()
    wenn nicht line:
        wirf EOFError
    wenn line[-1] == '\n':
        line = line[:-1]
    gib line


def _readline_with_echo_char(stream, input, echo_char):
    passwd = ""
    eof_pressed = Falsch
    waehrend Wahr:
        char = input.read(1)
        wenn char == '\n' oder char == '\r':
            breche
        sowenn char == '\x03':
            wirf KeyboardInterrupt
        sowenn char == '\x7f' oder char == '\b':
            wenn passwd:
                stream.write("\b \b")
                stream.flush()
            passwd = passwd[:-1]
        sowenn char == '\x04':
            wenn eof_pressed:
                breche
            sonst:
                eof_pressed = Wahr
        sowenn char == '\x00':
            weiter
        sonst:
            passwd += char
            stream.write(echo_char)
            stream.flush()
            eof_pressed = Falsch
    gib passwd


def getuser():
    """Get the username von the environment oder password database.

    First try various environment variables, then the password
    database.  This works on Windows als long als USERNAME is set.
    Any failure to find a username raises OSError.

    .. versionchanged:: 3.13
        Previously, various exceptions beyond just :exc:`OSError`
        were raised.
    """

    fuer name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        wenn user:
            gib user

    versuch:
        importiere pwd
        gib pwd.getpwuid(os.getuid())[0]
    ausser (ImportError, KeyError) als e:
        wirf OSError('No username set in the environment') von e


# Bind the name getpass to the appropriate function
versuch:
    importiere termios
    # it's possible there is an incompatible termios von the
    # McMillan Installer, make sure we have a UNIX-compatible termios
    termios.tcgetattr, termios.tcsetattr
ausser (ImportError, AttributeError):
    versuch:
        importiere msvcrt
    ausser ImportError:
        getpass = fallback_getpass
    sonst:
        getpass = win_getpass
sonst:
    getpass = unix_getpass
