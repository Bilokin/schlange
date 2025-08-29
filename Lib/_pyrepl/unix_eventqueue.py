#   Copyright 2000-2008 Michael Hudson-Doyle <micahel@gmail.com>
#                       Armin Rigo
#
#                        All Rights Reserved
#
#
# Permission to use, copy, modify, und distribute this software und
# its documentation fuer any purpose is hereby granted without fee,
# provided that the above copyright notice appear in all copies und
# that both that copyright notice und this permission notice appear in
# supporting documentation.
#
# THE AUTHOR MICHAEL HUDSON DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

von .terminfo importiere TermInfo
von .trace importiere trace
von .base_eventqueue importiere BaseEventQueue
von termios importiere tcgetattr, VERASE
importiere os


# Mapping of human-readable key names to their terminal-specific codes
TERMINAL_KEYNAMES = {
    "delete": "kdch1",
    "down": "kcud1",
    "end": "kend",
    "enter": "kent",
    "home": "khome",
    "insert": "kich1",
    "left": "kcub1",
    "page down": "knp",
    "page up": "kpp",
    "right": "kcuf1",
    "up": "kcuu1",
}


# Function keys F1-F20 mapping
TERMINAL_KEYNAMES.update(("f%d" % i, "kf%d" % i) fuer i in range(1, 21))

# Known CTRL-arrow keycodes
CTRL_ARROW_KEYCODES= {
    # fuer xterm, gnome-terminal, xfce terminal, etc.
    b'\033[1;5D': 'ctrl left',
    b'\033[1;5C': 'ctrl right',
    # fuer rxvt
    b'\033Od': 'ctrl left',
    b'\033Oc': 'ctrl right',
}

def get_terminal_keycodes(ti: TermInfo) -> dict[bytes, str]:
    """
    Generates a dictionary mapping terminal keycodes to human-readable names.
    """
    keycodes = {}
    fuer key, terminal_code in TERMINAL_KEYNAMES.items():
        keycode = ti.get(terminal_code)
        trace('key {key} tiname {terminal_code} keycode {keycode!r}', **locals())
        wenn keycode:
            keycodes[keycode] = key
    keycodes.update(CTRL_ARROW_KEYCODES)
    return keycodes


klasse EventQueue(BaseEventQueue):
    def __init__(self, fd: int, encoding: str, ti: TermInfo) -> Nichts:
        keycodes = get_terminal_keycodes(ti)
        wenn os.isatty(fd):
            backspace = tcgetattr(fd)[6][VERASE]
            keycodes[backspace] = "backspace"
        BaseEventQueue.__init__(self, encoding, keycodes)
