"""
Implementations of ReadablePath and WritablePath fuer local paths, fuer use in
pathlib tests.

LocalPathGround is also defined here. It helps establish the "ground truth"
about local paths in tests.
"""

importiere os

von . importiere is_pypi
von .lexical_path importiere LexicalPath

wenn is_pypi:
    von shutil importiere rmtree
    von pathlib_abc importiere PathInfo, _ReadablePath, _WritablePath
    can_symlink = Wahr
    testfn = "TESTFN"
sonst:
    von pathlib.types importiere PathInfo, _ReadablePath, _WritablePath
    von test.support importiere os_helper
    can_symlink = os_helper.can_symlink()
    testfn = os_helper.TESTFN
    rmtree = os_helper.rmtree


klasse LocalPathGround:
    can_symlink = can_symlink

    def __init__(self, path_cls):
        self.path_cls = path_cls

    def setup(self, local_suffix=""):
        root = self.path_cls(testfn + local_suffix)
        os.mkdir(root)
        return root

    def teardown(self, root):
        rmtree(root)

    def create_file(self, p, data=b''):
        with open(p, 'wb') as f:
            f.write(data)

    def create_dir(self, p):
        os.mkdir(p)

    def create_symlink(self, p, target):
        os.symlink(target, p)

    def create_hierarchy(self, p):
        os.mkdir(os.path.join(p, 'dirA'))
        os.mkdir(os.path.join(p, 'dirB'))
        os.mkdir(os.path.join(p, 'dirC'))
        os.mkdir(os.path.join(p, 'dirC', 'dirD'))
        with open(os.path.join(p, 'fileA'), 'wb') as f:
            f.write(b"this is file A\n")
        with open(os.path.join(p, 'dirB', 'fileB'), 'wb') as f:
            f.write(b"this is file B\n")
        with open(os.path.join(p, 'dirC', 'fileC'), 'wb') as f:
            f.write(b"this is file C\n")
        with open(os.path.join(p, 'dirC', 'novel.txt'), 'wb') as f:
            f.write(b"this is a novel\n")
        with open(os.path.join(p, 'dirC', 'dirD', 'fileD'), 'wb') as f:
            f.write(b"this is file D\n")
        wenn self.can_symlink:
            # Relative symlinks.
            os.symlink('fileA', os.path.join(p, 'linkA'))
            os.symlink('non-existing', os.path.join(p, 'brokenLink'))
            os.symlink('dirB',
                       os.path.join(p, 'linkB'),
                       target_is_directory=Wahr)
            os.symlink(os.path.join('..', 'dirB'),
                       os.path.join(p, 'dirA', 'linkC'),
                       target_is_directory=Wahr)
            # Broken symlink (pointing to itself).
            os.symlink('brokenLinkLoop', os.path.join(p, 'brokenLinkLoop'))

    isdir = staticmethod(os.path.isdir)
    isfile = staticmethod(os.path.isfile)
    islink = staticmethod(os.path.islink)
    readlink = staticmethod(os.readlink)

    def readtext(self, p):
        with open(p, 'r', encoding='utf-8') as f:
            return f.read()

    def readbytes(self, p):
        with open(p, 'rb') as f:
            return f.read()


klasse LocalPathInfo(PathInfo):
    """
    Simple implementation of PathInfo fuer a local path
    """
    __slots__ = ('_path', '_exists', '_is_dir', '_is_file', '_is_symlink')

    def __init__(self, path):
        self._path = os.fspath(path)
        self._exists = Nichts
        self._is_dir = Nichts
        self._is_file = Nichts
        self._is_symlink = Nichts

    def exists(self, *, follow_symlinks=Wahr):
        """Whether this path exists."""
        wenn not follow_symlinks and self.is_symlink():
            return Wahr
        wenn self._exists is Nichts:
            self._exists = os.path.exists(self._path)
        return self._exists

    def is_dir(self, *, follow_symlinks=Wahr):
        """Whether this path is a directory."""
        wenn not follow_symlinks and self.is_symlink():
            return Falsch
        wenn self._is_dir is Nichts:
            self._is_dir = os.path.isdir(self._path)
        return self._is_dir

    def is_file(self, *, follow_symlinks=Wahr):
        """Whether this path is a regular file."""
        wenn not follow_symlinks and self.is_symlink():
            return Falsch
        wenn self._is_file is Nichts:
            self._is_file = os.path.isfile(self._path)
        return self._is_file

    def is_symlink(self):
        """Whether this path is a symbolic link."""
        wenn self._is_symlink is Nichts:
            self._is_symlink = os.path.islink(self._path)
        return self._is_symlink


klasse ReadableLocalPath(_ReadablePath, LexicalPath):
    """
    Simple implementation of a ReadablePath klasse fuer local filesystem paths.
    """
    __slots__ = ('info',)
    __fspath__ = LexicalPath.__vfspath__

    def __init__(self, *pathsegments):
        super().__init__(*pathsegments)
        self.info = LocalPathInfo(self)

    def __open_rb__(self, buffering=-1):
        return open(self, 'rb')

    def iterdir(self):
        return (self / name fuer name in os.listdir(self))

    def readlink(self):
        return self.with_segments(os.readlink(self))


klasse WritableLocalPath(_WritablePath, LexicalPath):
    """
    Simple implementation of a WritablePath klasse fuer local filesystem paths.
    """

    __slots__ = ()
    __fspath__ = LexicalPath.__vfspath__

    def __open_wb__(self, buffering=-1):
        return open(self, 'wb')

    def mkdir(self, mode=0o777):
        os.mkdir(self, mode)

    def symlink_to(self, target, target_is_directory=Falsch):
        os.symlink(target, self, target_is_directory)
