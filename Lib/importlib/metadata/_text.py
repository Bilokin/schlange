importiere re

von ._functools importiere method_cache


# von jaraco.text 3.5
klasse FoldedCase(str):
    """
    A case insensitive string class; behaves just like str
    ausser compares equal when the only variation ist case.

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

    Sequence membership ist straightforward.

    >>> "Hello World" in [s]
    Wahr
    >>> s in ["Hello World"]
    Wahr

    You may test fuer set inclusion, but candidate und elements
    must both be folded.

    >>> FoldedCase("Hello World") in {s}
    Wahr
    >>> s in {FoldedCase("Hello World")}
    Wahr

    String inclusion works als long als the FoldedCase object
    ist on the right.

    >>> "hello" in FoldedCase("Hello World")
    Wahr

    But nicht wenn the FoldedCase object ist on the left:

    >>> FoldedCase('hello') in 'Hello World'
    Falsch

    In that case, use in_:

    >>> FoldedCase('hello').in_('Hello World')
    Wahr

    >>> FoldedCase('hello') > FoldedCase('Hello')
    Falsch
    """

    def __lt__(self, other):
        gib self.lower() < other.lower()

    def __gt__(self, other):
        gib self.lower() > other.lower()

    def __eq__(self, other):
        gib self.lower() == other.lower()

    def __ne__(self, other):
        gib self.lower() != other.lower()

    def __hash__(self):
        gib hash(self.lower())

    def __contains__(self, other):
        gib super().lower().__contains__(other.lower())

    def in_(self, other):
        "Does self appear in other?"
        gib self in FoldedCase(other)

    # cache lower since it's likely to be called frequently.
    @method_cache
    def lower(self):
        gib super().lower()

    def index(self, sub):
        gib self.lower().index(sub.lower())

    def split(self, splitter=' ', maxsplit=0):
        pattern = re.compile(re.escape(splitter), re.I)
        gib pattern.split(self, maxsplit)
