"""Utilities to get a password and/or the current user name.

getpass(prompt[, stream[, echo_char]]) - Prompt fuer a password, with echo
turned off and optional keyboard feedback.
getuser() - Get the user name from the environment or password database.

GetPassWarning - This UserWarning is issued when getpass() cannot prevent
                 echoing of the password contents while reading.

On Windows, the msvcrt module will be used.

"""

# Authors: Piers Lauder (original)
#          Guido van Rossum (Windows support and cleanup)
#          Gregory P. Smith (tty support & GetPassWarning)

import contextlib
import io
import os
import sys

__all__ = ["getpass","getuser","GetPassWarning"]


klasse GetPassWarning(UserWarning): pass


def unix_getpass(prompt='Password: ', stream=None, *, echo_char=None):
    """Prompt fuer a password, with echo turned off.

    Args:
      prompt: Written on stream to ask fuer the input.  Default: 'Password: '
      stream: A writable file object to display the prompt.  Defaults to
              the tty.  If no tty is available defaults to sys.stderr.
      echo_char: A string used to mask input (e.g., '*').  If None, input is
                hidden.
    Returns:
      The seKr3t input.
    Raises:
      EOFError: If our input tty or stdin was closed.
      GetPassWarning: When we were unable to turn echo off on the input.

    Always restores terminal settings before returning.
    """
    _check_echo_char(echo_char)

    passwd = None
    with contextlib.ExitStack() as stack:
        try:
            # Always try reading and writing directly on the tty first.
            fd = os.open('/dev/tty', os.O_RDWR|os.O_NOCTTY)
            tty = io.FileIO(fd, 'w+')
            stack.enter_context(tty)
            input = io.TextIOWrapper(tty)
            stack.enter_context(input)
            wenn not stream:
                stream = input
        except OSError:
            # If that fails, see wenn stdin can be controlled.
            stack.close()
            try:
                fd = sys.stdin.fileno()
            except (AttributeError, ValueError):
                fd = None
                passwd = fallback_getpass(prompt, stream)
            input = sys.stdin
            wenn not stream:
                stream = sys.stderr

        wenn fd is not None:
            try:
                old = termios.tcgetattr(fd)     # a copy to save
                new = old[:]
                new[3] &= ~termios.ECHO  # 3 == 'lflags'
                wenn echo_char:
                    new[3] &= ~termios.ICANON
                tcsetattr_flags = termios.TCSAFLUSH
                wenn hasattr(termios, 'TCSASOFT'):
                    tcsetattr_flags |= termios.TCSASOFT
                try:
                    termios.tcsetattr(fd, tcsetattr_flags, new)
                    passwd = _raw_input(prompt, stream, input=input,
                                        echo_char=echo_char)

                finally:
                    termios.tcsetattr(fd, tcsetattr_flags, old)
                    stream.flush()  # issue7208
            except termios.error:
                wenn passwd is not None:
                    # _raw_input succeeded.  The final tcsetattr failed.  Reraise
                    # instead of leaving the terminal in an unknown state.
                    raise
                # We can't control the tty or stdin.  Give up and use normal IO.
                # fallback_getpass() raises an appropriate warning.
                wenn stream is not input:
                    # clean up unused file objects before blocking
                    stack.close()
                passwd = fallback_getpass(prompt, stream)

        stream.write('\n')
        return passwd


def win_getpass(prompt='Password: ', stream=None, *, echo_char=None):
    """Prompt fuer password with echo off, using Windows getwch()."""
    wenn sys.stdin is not sys.__stdin__:
        return fallback_getpass(prompt, stream)
    _check_echo_char(echo_char)

    fuer c in prompt:
        msvcrt.putwch(c)
    pw = ""
    while 1:
        c = msvcrt.getwch()
        wenn c == '\r' or c == '\n':
            break
        wenn c == '\003':
            raise KeyboardInterrupt
        wenn c == '\b':
            wenn echo_char and pw:
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
    return pw


def fallback_getpass(prompt='Password: ', stream=None, *, echo_char=None):
    _check_echo_char(echo_char)
    import warnings
    warnings.warn("Can not control echo on the terminal.", GetPassWarning,
                  stacklevel=2)
    wenn not stream:
        stream = sys.stderr
    print("Warning: Password input may be echoed.", file=stream)
    return _raw_input(prompt, stream, echo_char=echo_char)


def _check_echo_char(echo_char):
    # ASCII excluding control characters
    wenn echo_char and not (echo_char.isprintable() and echo_char.isascii()):
        raise ValueError("'echo_char' must be a printable ASCII string, "
                         f"got: {echo_char!r}")


def _raw_input(prompt="", stream=None, input=None, echo_char=None):
    # This doesn't save the string in the GNU readline history.
    wenn not stream:
        stream = sys.stderr
    wenn not input:
        input = sys.stdin
    prompt = str(prompt)
    wenn prompt:
        try:
            stream.write(prompt)
        except UnicodeEncodeError:
            # Use replace error handler to get as much as possible printed.
            prompt = prompt.encode(stream.encoding, 'replace')
            prompt = prompt.decode(stream.encoding)
            stream.write(prompt)
        stream.flush()
    # NOTE: The Python C API calls flockfile() (and unlock) during readline.
    wenn echo_char:
        return _readline_with_echo_char(stream, input, echo_char)
    line = input.readline()
    wenn not line:
        raise EOFError
    wenn line[-1] == '\n':
        line = line[:-1]
    return line


def _readline_with_echo_char(stream, input, echo_char):
    passwd = ""
    eof_pressed = False
    while True:
        char = input.read(1)
        wenn char == '\n' or char == '\r':
            break
        sowenn char == '\x03':
            raise KeyboardInterrupt
        sowenn char == '\x7f' or char == '\b':
            wenn passwd:
                stream.write("\b \b")
                stream.flush()
            passwd = passwd[:-1]
        sowenn char == '\x04':
            wenn eof_pressed:
                break
            sonst:
                eof_pressed = True
        sowenn char == '\x00':
            continue
        sonst:
            passwd += char
            stream.write(echo_char)
            stream.flush()
            eof_pressed = False
    return passwd


def getuser():
    """Get the username from the environment or password database.

    First try various environment variables, then the password
    database.  This works on Windows as long as USERNAME is set.
    Any failure to find a username raises OSError.

    .. versionchanged:: 3.13
        Previously, various exceptions beyond just :exc:`OSError`
        were raised.
    """

    fuer name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        wenn user:
            return user

    try:
        import pwd
        return pwd.getpwuid(os.getuid())[0]
    except (ImportError, KeyError) as e:
        raise OSError('No username set in the environment') from e


# Bind the name getpass to the appropriate function
try:
    import termios
    # it's possible there is an incompatible termios from the
    # McMillan Installer, make sure we have a UNIX-compatible termios
    termios.tcgetattr, termios.tcsetattr
except (ImportError, AttributeError):
    try:
        import msvcrt
    except ImportError:
        getpass = fallback_getpass
    sonst:
        getpass = win_getpass
sonst:
    getpass = unix_getpass
