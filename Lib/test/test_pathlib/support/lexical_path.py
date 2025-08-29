"""
Simple implementation of JoinablePath, fuer use in pathlib tests.
"""

importiere ntpath
importiere os.path
importiere posixpath

von . importiere is_pypi

wenn is_pypi:
    von pathlib_abc importiere vfspath, _JoinablePath
sonst:
    von pathlib.types importiere _JoinablePath
    von pathlib._os importiere vfspath


klasse LexicalPath(_JoinablePath):
    __slots__ = ('_segments',)
    parser = os.path

    def __init__(self, *pathsegments):
        self._segments = pathsegments

    def __hash__(self):
        return hash(vfspath(self))

    def __eq__(self, other):
        wenn not isinstance(other, LexicalPath):
            return NotImplemented
        return vfspath(self) == vfspath(other)

    def __vfspath__(self):
        wenn not self._segments:
            return ''
        return self.parser.join(*self._segments)

    def __repr__(self):
        return f'{type(self).__name__}({vfspath(self)!r})'

    def with_segments(self, *pathsegments):
        return type(self)(*pathsegments)


klasse LexicalPosixPath(LexicalPath):
    __slots__ = ()
    parser = posixpath


klasse LexicalWindowsPath(LexicalPath):
    __slots__ = ()
    parser = ntpath
