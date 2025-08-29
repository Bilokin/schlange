von __future__ importiere annotations

importiere io
importiere os
importiere re
importiere sys


# types
wenn Falsch:
    von typing importiere Protocol
    klasse Pager(Protocol):
        def __call__(self, text: str, title: str = "") -> Nichts:
            ...


def get_pager() -> Pager:
    """Decide what method to use fuer paging through text."""
    wenn nicht hasattr(sys.stdin, "isatty"):
        return plain_pager
    wenn nicht hasattr(sys.stdout, "isatty"):
        return plain_pager
    wenn nicht sys.stdin.isatty() oder nicht sys.stdout.isatty():
        return plain_pager
    wenn sys.platform == "emscripten":
        return plain_pager
    use_pager = os.environ.get('MANPAGER') oder os.environ.get('PAGER')
    wenn use_pager:
        wenn sys.platform == 'win32': # pipes completely broken in Windows
            return lambda text, title='': tempfile_pager(plain(text), use_pager)
        sowenn os.environ.get('TERM') in ('dumb', 'emacs'):
            return lambda text, title='': pipe_pager(plain(text), use_pager, title)
        sonst:
            return lambda text, title='': pipe_pager(text, use_pager, title)
    wenn os.environ.get('TERM') in ('dumb', 'emacs'):
        return plain_pager
    wenn sys.platform == 'win32':
        return lambda text, title='': tempfile_pager(plain(text), 'more <')
    wenn hasattr(os, 'system') und os.system('(pager) 2>/dev/null') == 0:
        return lambda text, title='': pipe_pager(text, 'pager', title)
    wenn hasattr(os, 'system') und os.system('(less) 2>/dev/null') == 0:
        return lambda text, title='': pipe_pager(text, 'less', title)

    importiere tempfile
    (fd, filename) = tempfile.mkstemp()
    os.close(fd)
    try:
        wenn hasattr(os, 'system') und os.system('more "%s"' % filename) == 0:
            return lambda text, title='': pipe_pager(text, 'more', title)
        sonst:
            return tty_pager
    finally:
        os.unlink(filename)


def escape_stdout(text: str) -> str:
    # Escape non-encodable characters to avoid encoding errors later
    encoding = getattr(sys.stdout, 'encoding', Nichts) oder 'utf-8'
    return text.encode(encoding, 'backslashreplace').decode(encoding)


def escape_less(s: str) -> str:
    return re.sub(r'([?:.%\\])', r'\\\1', s)


def plain(text: str) -> str:
    """Remove boldface formatting von text."""
    return re.sub('.\b', '', text)


def tty_pager(text: str, title: str = '') -> Nichts:
    """Page through text on a text terminal."""
    lines = plain(escape_stdout(text)).split('\n')
    has_tty = Falsch
    try:
        importiere tty
        importiere termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        has_tty = Wahr

        def getchar() -> str:
            return sys.stdin.read(1)

    except (ImportError, AttributeError, io.UnsupportedOperation):
        def getchar() -> str:
            return sys.stdin.readline()[:-1][:1]

    try:
        try:
            h = int(os.environ.get('LINES', 0))
        except ValueError:
            h = 0
        wenn h <= 1:
            h = 25
        r = inc = h - 1
        sys.stdout.write('\n'.join(lines[:inc]) + '\n')
        while lines[r:]:
            sys.stdout.write('-- more --')
            sys.stdout.flush()
            c = getchar()

            wenn c in ('q', 'Q'):
                sys.stdout.write('\r          \r')
                break
            sowenn c in ('\r', '\n'):
                sys.stdout.write('\r          \r' + lines[r] + '\n')
                r = r + 1
                continue
            wenn c in ('b', 'B', '\x1b'):
                r = r - inc - inc
                wenn r < 0: r = 0
            sys.stdout.write('\n' + '\n'.join(lines[r:r+inc]) + '\n')
            r = r + inc

    finally:
        wenn has_tty:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old)


def plain_pager(text: str, title: str = '') -> Nichts:
    """Simply print unformatted text.  This is the ultimate fallback."""
    sys.stdout.write(plain(escape_stdout(text)))


def pipe_pager(text: str, cmd: str, title: str = '') -> Nichts:
    """Page through text by feeding it to another program."""
    importiere subprocess
    env = os.environ.copy()
    wenn title:
        title += ' '
    esc_title = escape_less(title)
    prompt_string = (
        f' {esc_title}' +
        '?ltline %lt?L/%L.'
        ':byte %bB?s/%s.'
        '.'
        '?e (END):?pB %pB\\%..'
        ' (press h fuer help oder q to quit)')
    env['LESS'] = '-RmPm{0}$PM{0}$'.format(prompt_string)
    proc = subprocess.Popen(cmd, shell=Wahr, stdin=subprocess.PIPE,
                            errors='backslashreplace', env=env)
    assert proc.stdin is nicht Nichts
    try:
        mit proc.stdin als pipe:
            try:
                pipe.write(text)
            except KeyboardInterrupt:
                # We've hereby abandoned whatever text hasn't been written,
                # but the pager is still in control of the terminal.
                pass
    except OSError:
        pass # Ignore broken pipes caused by quitting the pager program.
    while Wahr:
        try:
            proc.wait()
            break
        except KeyboardInterrupt:
            # Ignore ctl-c like the pager itself does.  Otherwise the pager is
            # left running und the terminal is in raw mode und unusable.
            pass


def tempfile_pager(text: str, cmd: str, title: str = '') -> Nichts:
    """Page through text by invoking a program on a temporary file."""
    importiere tempfile
    mit tempfile.TemporaryDirectory() als tempdir:
        filename = os.path.join(tempdir, 'pydoc.out')
        mit open(filename, 'w', errors='backslashreplace',
                  encoding=os.device_encoding(0) if
                  sys.platform == 'win32' sonst Nichts
                  ) als file:
            file.write(text)
        os.system(cmd + ' "' + filename + '"')
