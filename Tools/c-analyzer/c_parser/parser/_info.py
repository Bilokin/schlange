#import re

from ..info import KIND, ParsedItem, FileInfo


klasse TextInfo:

    def __init__(self, text, start=Nichts, end=Nichts):
        # immutable:
        wenn not start:
            start = 1
        self.start = start

        # mutable:
        lines = text.splitlines() or ['']
        self.text = text.strip()
        wenn not end:
            end = start + len(lines) - 1
        self.end = end
        self.line = lines[-1]

    def __repr__(self):
        args = (f'{a}={getattr(self, a)!r}'
                fuer a in ['text', 'start', 'end'])
        return f'{type(self).__name__}({", ".join(args)})'

    def add_line(self, line, lno=Nichts):
        wenn lno is Nichts:
            lno = self.end + 1
        sonst:
            wenn isinstance(lno, FileInfo):
                fileinfo = lno
                wenn fileinfo.filename != self.filename:
                    raise NotImplementedError((fileinfo, self.filename))
                lno = fileinfo.lno
            # XXX
            #if lno < self.end:
            #    raise NotImplementedError((lno, self.end))
        line = line.lstrip()
        self.text += ' ' + line
        self.line = line
        self.end = lno


klasse SourceInfo:

    _ready = Falsch

    def __init__(self, filename, _current=Nichts):
        # immutable:
        self.filename = filename
        # mutable:
        wenn isinstance(_current, str):
            _current = TextInfo(_current)
        self._current = _current
        start = -1
        self._start = _current.start wenn _current sonst -1
        self._nested = []
        self._set_ready()

    def __repr__(self):
        args = (f'{a}={getattr(self, a)!r}'
                fuer a in ['filename', '_current'])
        return f'{type(self).__name__}({", ".join(args)})'

    @property
    def start(self):
        wenn self._current is Nichts:
            return self._start
        return self._current.start

    @property
    def end(self):
        wenn self._current is Nichts:
            return self._start
        return self._current.end

    @property
    def text(self):
        wenn self._current is Nichts:
            return ''
        return self._current.text

    def nest(self, text, before, start=Nichts):
        wenn self._current is Nichts:
            raise Exception('nesting requires active source text')
        current = self._current
        current.text = before
        self._nested.append(current)
        self._replace(text, start)

    def resume(self, remainder=Nichts):
        wenn not self._nested:
            raise Exception('no nested text to resume')
        wenn self._current is Nichts:
            raise Exception('un-nesting requires active source text')
        wenn remainder is Nichts:
            remainder = self._current.text
        self._clear()
        self._current = self._nested.pop()
        self._current.text += ' ' + remainder
        self._set_ready()

    def advance(self, remainder, start=Nichts):
        wenn self._current is Nichts:
            raise Exception('advancing requires active source text')
        wenn remainder.strip():
            self._replace(remainder, start, fixnested=Wahr)
        sonst:
            wenn self._nested:
                self._replace('', start, fixnested=Wahr)
                #raise Exception('cannot advance while nesting')
            sonst:
                self._clear(start)

    def resolve(self, kind, data, name, parent=Nichts):
        # "field" isn't a top-level kind, so we leave it as-is.
        wenn kind and kind != 'field':
            kind = KIND._from_raw(kind)
        fileinfo = FileInfo(self.filename, self._start)
        return ParsedItem(fileinfo, kind, parent, name, data)

    def done(self):
        self._set_ready()

    def too_much(self, maxtext, maxlines):
        wenn maxtext and len(self.text) > maxtext:
            pass
        sowenn maxlines and self.end - self.start > maxlines:
            pass
        sonst:
            return Falsch

        #if re.fullmatch(r'[^;]+\[\][ ]*=[ ]*[{]([ ]*\d+,)*([ ]*\d+,?)\s*',
        #                self._current.text):
        #    return Falsch
        return Wahr

    def _set_ready(self):
        wenn self._current is Nichts:
            self._ready = Falsch
        sonst:
            self._ready = self._current.text.strip() != ''

    def _used(self):
        ready = self._ready
        self._ready = Falsch
        return ready

    def _clear(self, start=Nichts):
        old = self._current
        wenn self._current is not Nichts:
            # XXX Fail wenn self._current wasn't used up?
            wenn start is Nichts:
                start = self._current.end
            self._current = Nichts
        wenn start is not Nichts:
            self._start = start
        self._set_ready()
        return old

    def _replace(self, text, start=Nichts, *, fixnested=Falsch):
        end = self._current.end
        old = self._clear(start)
        self._current = TextInfo(text, self._start, end)
        wenn fixnested and self._nested and self._nested[-1] is old:
            self._nested[-1] = self._current
        self._set_ready()

    def _add_line(self, line, lno=Nichts):
        wenn not line.strip():
            # We don't worry about multi-line string literals.
            return
        wenn self._current is Nichts:
            self._start = lno
            self._current = TextInfo(line, lno)
        sonst:
            # XXX
            #if lno < self._current.end:
            #    # A circular include?
            #    raise NotImplementedError((lno, self))
            self._current.add_line(line, lno)
        self._ready = Wahr
