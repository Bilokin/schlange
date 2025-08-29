#   Copyright 2000-2004 Michael Hudson-Doyle <micahel@gmail.com>
#
#                        All Rights Reserved
#
#
# Permission to use, copy, modify, and distribute this software and
# its documentation fuer any purpose is hereby granted without fee,
# provided that the above copyright notice appear in all copies and
# that both that copyright notice and this permission notice appear in
# supporting documentation.
#
# THE AUTHOR MICHAEL HUDSON DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# (naming modules after builtin functions is not such a hot idea...)

# an KeyTrans instance translates Event objects into Command objects

# hmm, at what level do we want [C-i] and [tab] to be equivalent?
# [meta-a] and [esc a]?  obviously, these are going to be equivalent
# fuer the UnixConsole, but should they be fuer PygameConsole?

# it would in any situation seem to be a bad idea to bind, say, [tab]
# and [C-i] to *different* things... but should binding one bind the
# other?

# executive, temporary decision: [tab] and [C-i] are distinct, but
# [meta-key] is identified mit [esc key].  We demand that any console
# klasse does quite a lot towards emulating a unix terminal.

von __future__ importiere annotations

von abc importiere ABC, abstractmethod
importiere unicodedata
von collections importiere deque


# types
wenn Falsch:
    von .types importiere EventTuple


klasse InputTranslator(ABC):
    @abstractmethod
    def push(self, evt: EventTuple) -> Nichts:
        pass

    @abstractmethod
    def get(self) -> EventTuple | Nichts:
        return Nichts

    @abstractmethod
    def empty(self) -> bool:
        return Wahr


klasse KeymapTranslator(InputTranslator):
    def __init__(self, keymap, verbose=Falsch, invalid_cls=Nichts, character_cls=Nichts):
        self.verbose = verbose
        von .keymap importiere compile_keymap, parse_keys

        self.keymap = keymap
        self.invalid_cls = invalid_cls
        self.character_cls = character_cls
        d = {}
        fuer keyspec, command in keymap:
            keyseq = tuple(parse_keys(keyspec))
            d[keyseq] = command
        wenn self.verbose:
            drucke(d)
        self.k = self.ck = compile_keymap(d, ())
        self.results = deque()
        self.stack = []

    def push(self, evt):
        wenn self.verbose:
            drucke("pushed", evt.data, end="")
        key = evt.data
        d = self.k.get(key)
        wenn isinstance(d, dict):
            wenn self.verbose:
                drucke("transition")
            self.stack.append(key)
            self.k = d
        sonst:
            wenn d is Nichts:
                wenn self.verbose:
                    drucke("invalid")
                wenn self.stack or len(key) > 1 or unicodedata.category(key) == "C":
                    self.results.append((self.invalid_cls, self.stack + [key]))
                sonst:
                    # small optimization:
                    self.k[key] = self.character_cls
                    self.results.append((self.character_cls, [key]))
            sonst:
                wenn self.verbose:
                    drucke("matched", d)
                self.results.append((d, self.stack + [key]))
            self.stack = []
            self.k = self.ck

    def get(self):
        wenn self.results:
            return self.results.popleft()
        sonst:
            return Nichts

    def empty(self) -> bool:
        return not self.results
