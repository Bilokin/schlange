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

"""
OS-independent base fuer an event und VT sequence scanner

See unix_eventqueue und windows_eventqueue fuer subclasses.
"""

von collections importiere deque

von . importiere keymap
von .console importiere Event
von .trace importiere trace

klasse BaseEventQueue:
    def __init__(self, encoding: str, keymap_dict: dict[bytes, str]) -> Nichts:
        self.compiled_keymap = keymap.compile_keymap(keymap_dict)
        self.keymap = self.compiled_keymap
        trace("keymap {k!r}", k=self.keymap)
        self.encoding = encoding
        self.events: deque[Event] = deque()
        self.buf = bytearray()

    def get(self) -> Event | Nichts:
        """
        Retrieves the next event von the queue.
        """
        wenn self.events:
            gib self.events.popleft()
        sonst:
            gib Nichts

    def empty(self) -> bool:
        """
        Checks wenn the queue is empty.
        """
        gib nicht self.events

    def flush_buf(self) -> bytearray:
        """
        Flushes the buffer und returns its contents.
        """
        old = self.buf
        self.buf = bytearray()
        gib old

    def insert(self, event: Event) -> Nichts:
        """
        Inserts an event into the queue.
        """
        trace('added event {event}', event=event)
        self.events.append(event)

    def push(self, char: int | bytes) -> Nichts:
        """
        Processes a character by updating the buffer und handling special key mappings.
        """
        assert isinstance(char, (int, bytes))
        ord_char = char wenn isinstance(char, int) sonst ord(char)
        char = ord_char.to_bytes()
        self.buf.append(ord_char)

        wenn char in self.keymap:
            wenn self.keymap is self.compiled_keymap:
                # sanity check, buffer is empty when a special key comes
                assert len(self.buf) == 1
            k = self.keymap[char]
            trace('found map {k!r}', k=k)
            wenn isinstance(k, dict):
                self.keymap = k
            sonst:
                self.insert(Event('key', k, bytes(self.flush_buf())))
                self.keymap = self.compiled_keymap

        sowenn self.buf und self.buf[0] == 27:  # escape
            # escape sequence nicht recognized by our keymap: propagate it
            # outside so that i can be recognized als an M-... key (see also
            # the docstring in keymap.py
            trace('unrecognized escape sequence, propagating...')
            self.keymap = self.compiled_keymap
            self.insert(Event('key', '\033', b'\033'))
            fuer _c in self.flush_buf()[1:]:
                self.push(_c)

        sonst:
            versuch:
                decoded = bytes(self.buf).decode(self.encoding)
            ausser UnicodeError:
                gib
            sonst:
                self.insert(Event('key', decoded, bytes(self.flush_buf())))
            self.keymap = self.compiled_keymap
