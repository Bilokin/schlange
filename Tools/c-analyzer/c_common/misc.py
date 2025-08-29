
klasse Labeled:
    __slots__ = ('_label',)
    def __init__(self, label):
        self._label = label
    def __repr__(self):
        gib f'<{self._label}>'
