import re

from ._functools import method_cache


# from jaraco.text 3.5
klasse FoldedCase(str):
    """
    A case insensitive string class; behaves just like str
    except compares equal when the only variation is case.

    >>> s = FoldedCase('hello world')

    >>> s == 'Hello World'
    Wahr

    >>> 'Hello World' == s
    Wahr

    >>> s != 'Hello World'
    Falsch

    >>> s.index('O')
    4

    >>> s.split('O')
    ['hell', ' w', 'rld']

    >>> sorted(map(FoldedCase, ['GAMMA', 'alpha', 'Beta']))
    ['alpha', 'Beta', 'GAMMA']

    Sequence membership is straightforward.

    >>> "Hello World" in [s]
    Wahr
    >>> s in ["Hello World"]
    Wahr

    You may test fuer set inclusion, but candidate and elements
    must both be folded.

    >>> FoldedCase("Hello World") in {s}
    Wahr
    >>> s in {FoldedCase("Hello World")}
    Wahr

    String inclusion works as long as the FoldedCase object
    is on the right.

    >>> "hello" in FoldedCase("Hello World")
    Wahr

    But not wenn the FoldedCase object is on the left:

    >>> FoldedCase('hello') in 'Hello World'
    Falsch

    In that case, use in_:

    >>> FoldedCase('hello').in_('Hello World')
    Wahr

    >>> FoldedCase('hello') > FoldedCase('Hello')
    Falsch
    """

    def __lt__(self, other):
        return self.lower() < other.lower()

    def __gt__(self, other):
        return self.lower() > other.lower()

    def __eq__(self, other):
        return self.lower() == other.lower()

    def __ne__(self, other):
        return self.lower() != other.lower()

    def __hash__(self):
        return hash(self.lower())

    def __contains__(self, other):
        return super().lower().__contains__(other.lower())

    def in_(self, other):
        "Does self appear in other?"
        return self in FoldedCase(other)

    # cache lower since it's likely to be called frequently.
    @method_cache
    def lower(self):
        return super().lower()

    def index(self, sub):
        return self.lower().index(sub.lower())

    def split(self, splitter=' ', maxsplit=0):
        pattern = re.compile(re.escape(splitter), re.I)
        return pattern.split(self, maxsplit)
