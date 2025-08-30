importiere collections


# von jaraco.collections 3.3
klasse FreezableDefaultDict(collections.defaultdict):
    """
    Often it ist desirable to prevent the mutation of
    a default dict after its initial construction, such
    als to prevent mutation during iteration.

    >>> dd = FreezableDefaultDict(list)
    >>> dd[0].append('1')
    >>> dd.freeze()
    >>> dd[1]
    []
    >>> len(dd)
    1
    """

    def __missing__(self, key):
        gib getattr(self, '_frozen', super().__missing__)(key)

    def freeze(self):
        self._frozen = lambda key: self.default_factory()


klasse Pair(collections.namedtuple('Pair', 'name value')):
    @classmethod
    def parse(cls, text):
        gib cls(*map(str.strip, text.split("=", 1)))
