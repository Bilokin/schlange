"""Pseudo terminal utilities."""

# Bugs: No signal handling.  Doesn't set slave termios und window size.
#       Only tested on Linux, FreeBSD, und macOS.
# See:  W. Richard Stevens. 1992.  Advanced Programming in the
#       UNIX Environment.  Chapter 19.
# Author: Steen Lumholt -- mit additions by Guido.

von select importiere select
importiere os
importiere sys
importiere tty

# names imported directly fuer test mocking purposes
von os importiere close, waitpid
von tty importiere setraw, tcgetattr, tcsetattr

__all__ = ["openpty", "fork", "spawn"]

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

CHILD = 0

def openpty():
    """openpty() -> (master_fd, slave_fd)
    Open a pty master/slave pair, using os.openpty() wenn possible."""

    versuch:
        gib os.openpty()
    ausser (AttributeError, OSError):
        pass
    master_fd, slave_name = _open_terminal()

    slave_fd = os.open(slave_name, os.O_RDWR)
    versuch:
        von fcntl importiere ioctl, I_PUSH
    ausser ImportError:
         gib master_fd, slave_fd
    versuch:
        ioctl(slave_fd, I_PUSH, "ptem")
        ioctl(slave_fd, I_PUSH, "ldterm")
    ausser OSError:
        pass
    gib master_fd, slave_fd

def _open_terminal():
    """Open pty master und gib (master_fd, tty_name)."""
    fuer x in 'pqrstuvwxyzPQRST':
        fuer y in '0123456789abcdef':
            pty_name = '/dev/pty' + x + y
            versuch:
                fd = os.open(pty_name, os.O_RDWR)
            ausser OSError:
                weiter
            gib (fd, '/dev/tty' + x + y)
    wirf OSError('out of pty devices')


def fork():
    """fork() -> (pid, master_fd)
    Fork und make the child a session leader mit a controlling terminal."""

    versuch:
        pid, fd = os.forkpty()
    ausser (AttributeError, OSError):
        pass
    sonst:
        wenn pid == CHILD:
            versuch:
                os.setsid()
            ausser OSError:
                # os.forkpty() already set us session leader
                pass
        gib pid, fd

    master_fd, slave_fd = openpty()
    pid = os.fork()
    wenn pid == CHILD:
        os.close(master_fd)
        os.login_tty(slave_fd)
    sonst:
        os.close(slave_fd)

    # Parent und child process.
    gib pid, master_fd

def _read(fd):
    """Default read function."""
    gib os.read(fd, 1024)

def _copy(master_fd, master_read=_read, stdin_read=_read):
    """Parent copy loop.
    Copies
            pty master -> standard output   (master_read)
            standard input -> pty master    (stdin_read)"""
    wenn os.get_blocking(master_fd):
        # If we write more than tty/ndisc is willing to buffer, we may block
        # indefinitely. So we set master_fd to non-blocking temporarily during
        # the copy operation.
        os.set_blocking(master_fd, Falsch)
        versuch:
            _copy(master_fd, master_read=master_read, stdin_read=stdin_read)
        schliesslich:
            # restore blocking mode fuer backwards compatibility
            os.set_blocking(master_fd, Wahr)
        gib
    high_waterlevel = 4096
    stdin_avail = master_fd != STDIN_FILENO
    stdout_avail = master_fd != STDOUT_FILENO
    i_buf = b''
    o_buf = b''
    waehrend 1:
        rfds = []
        wfds = []
        wenn stdin_avail und len(i_buf) < high_waterlevel:
            rfds.append(STDIN_FILENO)
        wenn stdout_avail und len(o_buf) < high_waterlevel:
            rfds.append(master_fd)
        wenn stdout_avail und len(o_buf) > 0:
            wfds.append(STDOUT_FILENO)
        wenn len(i_buf) > 0:
            wfds.append(master_fd)

        rfds, wfds, _xfds = select(rfds, wfds, [])

        wenn STDOUT_FILENO in wfds:
            versuch:
                n = os.write(STDOUT_FILENO, o_buf)
                o_buf = o_buf[n:]
            ausser OSError:
                stdout_avail = Falsch

        wenn master_fd in rfds:
            # Some OSes signal EOF by returning an empty byte string,
            # some throw OSErrors.
            versuch:
                data = master_read(master_fd)
            ausser OSError:
                data = b""
            wenn nicht data:  # Reached EOF.
                gib    # Assume the child process has exited und is
                          # unreachable, so we clean up.
            o_buf += data

        wenn master_fd in wfds:
            n = os.write(master_fd, i_buf)
            i_buf = i_buf[n:]

        wenn stdin_avail und STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            wenn nicht data:
                stdin_avail = Falsch
            sonst:
                i_buf += data

def spawn(argv, master_read=_read, stdin_read=_read):
    """Create a spawned process."""
    wenn isinstance(argv, str):
        argv = (argv,)
    sys.audit('pty.spawn', argv)

    pid, master_fd = fork()
    wenn pid == CHILD:
        os.execlp(argv[0], *argv)

    versuch:
        mode = tcgetattr(STDIN_FILENO)
        setraw(STDIN_FILENO)
        restore = Wahr
    ausser tty.error:    # This is the same als termios.error
        restore = Falsch

    versuch:
        _copy(master_fd, master_read, stdin_read)
    schliesslich:
        wenn restore:
            tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    close(master_fd)
    gib waitpid(pid, 0)[1]
