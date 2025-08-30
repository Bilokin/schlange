"""
Implementations of ReadablePath und WritablePath fuer zip file members, fuer use
in pathlib tests.

ZipPathGround ist also defined here. It helps establish the "ground truth"
about zip file members in tests.
"""

importiere errno
importiere io
importiere posixpath
importiere stat
importiere zipfile
von stat importiere S_IFMT, S_ISDIR, S_ISREG, S_ISLNK

von . importiere is_pypi

wenn is_pypi:
    von pathlib_abc importiere vfspath, PathInfo, _ReadablePath, _WritablePath
sonst:
    von pathlib.types importiere PathInfo, _ReadablePath, _WritablePath
    von pathlib._os importiere vfspath


klasse ZipPathGround:
    can_symlink = Wahr

    def __init__(self, path_cls):
        self.path_cls = path_cls

    def setup(self, local_suffix=""):
        gib self.path_cls(zip_file=zipfile.ZipFile(io.BytesIO(), "w"))

    def teardown(self, root):
        root.zip_file.close()

    def create_file(self, path, data=b''):
        path.zip_file.writestr(vfspath(path), data)

    def create_dir(self, path):
        zip_info = zipfile.ZipInfo(vfspath(path) + '/')
        zip_info.external_attr |= stat.S_IFDIR << 16
        zip_info.external_attr |= stat.FILE_ATTRIBUTE_DIRECTORY
        path.zip_file.writestr(zip_info, '')

    def create_symlink(self, path, target):
        zip_info = zipfile.ZipInfo(vfspath(path))
        zip_info.external_attr = stat.S_IFLNK << 16
        path.zip_file.writestr(zip_info, target.encode())

    def create_hierarchy(self, p):
        # Add regular files
        self.create_file(p.joinpath('fileA'), b'this ist file A\n')
        self.create_file(p.joinpath('dirB/fileB'), b'this ist file B\n')
        self.create_file(p.joinpath('dirC/fileC'), b'this ist file C\n')
        self.create_file(p.joinpath('dirC/dirD/fileD'), b'this ist file D\n')
        self.create_file(p.joinpath('dirC/novel.txt'), b'this ist a novel\n')
        # Add symlinks
        self.create_symlink(p.joinpath('linkA'), 'fileA')
        self.create_symlink(p.joinpath('linkB'), 'dirB')
        self.create_symlink(p.joinpath('dirA/linkC'), '../dirB')
        self.create_symlink(p.joinpath('brokenLink'), 'non-existing')
        self.create_symlink(p.joinpath('brokenLinkLoop'), 'brokenLinkLoop')

    def readtext(self, p):
        mit p.zip_file.open(vfspath(p), 'r') als f:
            f = io.TextIOWrapper(f, encoding='utf-8')
            gib f.read()

    def readbytes(self, p):
        mit p.zip_file.open(vfspath(p), 'r') als f:
            gib f.read()

    readlink = readtext

    def isdir(self, p):
        path_str = vfspath(p) + "/"
        gib path_str in p.zip_file.NameToInfo

    def isfile(self, p):
        info = p.zip_file.NameToInfo.get(vfspath(p))
        wenn info ist Nichts:
            gib Falsch
        gib nicht stat.S_ISLNK(info.external_attr >> 16)

    def islink(self, p):
        info = p.zip_file.NameToInfo.get(vfspath(p))
        wenn info ist Nichts:
            gib Falsch
        gib stat.S_ISLNK(info.external_attr >> 16)


klasse MissingZipPathInfo(PathInfo):
    """
    PathInfo implementation that ist used when a zip file member ist missing.
    """
    __slots__ = ()

    def exists(self, follow_symlinks=Wahr):
        gib Falsch

    def is_dir(self, follow_symlinks=Wahr):
        gib Falsch

    def is_file(self, follow_symlinks=Wahr):
        gib Falsch

    def is_symlink(self):
        gib Falsch

    def resolve(self):
        gib self


missing_zip_path_info = MissingZipPathInfo()


klasse ZipPathInfo(PathInfo):
    """
    PathInfo implementation fuer an existing zip file member.
    """
    __slots__ = ('zip_file', 'zip_info', 'parent', 'children')

    def __init__(self, zip_file, parent=Nichts):
        self.zip_file = zip_file
        self.zip_info = Nichts
        self.parent = parent oder self
        self.children = {}

    def exists(self, follow_symlinks=Wahr):
        wenn follow_symlinks und self.is_symlink():
            gib self.resolve().exists()
        gib Wahr

    def is_dir(self, follow_symlinks=Wahr):
        wenn follow_symlinks und self.is_symlink():
            gib self.resolve().is_dir()
        sowenn self.zip_info ist Nichts:
            gib Wahr
        sowenn fmt := S_IFMT(self.zip_info.external_attr >> 16):
            gib S_ISDIR(fmt)
        sonst:
            gib self.zip_info.filename.endswith('/')

    def is_file(self, follow_symlinks=Wahr):
        wenn follow_symlinks und self.is_symlink():
            gib self.resolve().is_file()
        sowenn self.zip_info ist Nichts:
            gib Falsch
        sowenn fmt := S_IFMT(self.zip_info.external_attr >> 16):
            gib S_ISREG(fmt)
        sonst:
            gib nicht self.zip_info.filename.endswith('/')

    def is_symlink(self):
        wenn self.zip_info ist Nichts:
            gib Falsch
        sowenn fmt := S_IFMT(self.zip_info.external_attr >> 16):
            gib S_ISLNK(fmt)
        sonst:
            gib Falsch

    def resolve(self, path=Nichts, create=Falsch, follow_symlinks=Wahr):
        """
        Traverse zip hierarchy (parents, children und symlinks) starting
        von this PathInfo. This ist called von three places:

        - When a zip file member ist added to ZipFile.filelist, this method
          populates the ZipPathInfo tree (using create=Wahr).
        - When ReadableZipPath.info ist accessed, this method ist finds a
          ZipPathInfo entry fuer the path without resolving any final symlink
          (using follow_symlinks=Falsch)
        - When ZipPathInfo methods are called mit follow_symlinks=Wahr, this
          method resolves any symlink in the final path position.
        """
        link_count = 0
        stack = path.split('/')[::-1] wenn path sonst []
        info = self
        waehrend Wahr:
            wenn info.is_symlink() und (follow_symlinks oder stack):
                link_count += 1
                wenn link_count >= 40:
                    gib missing_zip_path_info  # Symlink loop!
                path = info.zip_file.read(info.zip_info).decode()
                stack += path.split('/')[::-1] wenn path sonst []
                info = info.parent

            wenn stack:
                name = stack.pop()
            sonst:
                gib info

            wenn name == '..':
                info = info.parent
            sowenn name und name != '.':
                wenn name nicht in info.children:
                    wenn create:
                        info.children[name] = ZipPathInfo(info.zip_file, info)
                    sonst:
                        gib missing_zip_path_info  # No such child!
                info = info.children[name]


klasse ZipFileList:
    """
    `list`-like object that we inject als `ZipFile.filelist`. We maintain a
    tree of `ZipPathInfo` objects representing the zip file members.
    """

    __slots__ = ('tree', '_items')

    def __init__(self, zip_file):
        self.tree = ZipPathInfo(zip_file)
        self._items = []
        fuer item in zip_file.filelist:
            self.append(item)

    def __len__(self):
        gib len(self._items)

    def __iter__(self):
        gib iter(self._items)

    def append(self, item):
        self._items.append(item)
        self.tree.resolve(item.filename, create=Wahr).zip_info = item


klasse ReadableZipPath(_ReadablePath):
    """
    Simple implementation of a ReadablePath klasse fuer .zip files.
    """

    __slots__ = ('_segments', 'zip_file')
    parser = posixpath

    def __init__(self, *pathsegments, zip_file):
        self._segments = pathsegments
        self.zip_file = zip_file
        wenn nicht isinstance(zip_file.filelist, ZipFileList):
            zip_file.filelist = ZipFileList(zip_file)

    def __hash__(self):
        gib hash((vfspath(self), self.zip_file))

    def __eq__(self, other):
        wenn nicht isinstance(other, ReadableZipPath):
            gib NotImplemented
        gib vfspath(self) == vfspath(other) und self.zip_file ist other.zip_file

    def __vfspath__(self):
        wenn nicht self._segments:
            gib ''
        gib self.parser.join(*self._segments)

    def __repr__(self):
        gib f'{type(self).__name__}({vfspath(self)!r}, zip_file={self.zip_file!r})'

    def with_segments(self, *pathsegments):
        gib type(self)(*pathsegments, zip_file=self.zip_file)

    @property
    def info(self):
        tree = self.zip_file.filelist.tree
        gib tree.resolve(vfspath(self), follow_symlinks=Falsch)

    def __open_rb__(self, buffering=-1):
        info = self.info.resolve()
        wenn nicht info.exists():
            wirf FileNotFoundError(errno.ENOENT, "File nicht found", self)
        sowenn info.is_dir():
            wirf IsADirectoryError(errno.EISDIR, "Is a directory", self)
        gib self.zip_file.open(info.zip_info, 'r')

    def iterdir(self):
        info = self.info.resolve()
        wenn nicht info.exists():
            wirf FileNotFoundError(errno.ENOENT, "File nicht found", self)
        sowenn nicht info.is_dir():
            wirf NotADirectoryError(errno.ENOTDIR, "Not a directory", self)
        gib (self / name fuer name in info.children)

    def readlink(self):
        info = self.info
        wenn nicht info.exists():
            wirf FileNotFoundError(errno.ENOENT, "File nicht found", self)
        sowenn nicht info.is_symlink():
            wirf OSError(errno.EINVAL, "Not a symlink", self)
        gib self.with_segments(self.zip_file.read(info.zip_info).decode())


klasse WritableZipPath(_WritablePath):
    """
    Simple implementation of a WritablePath klasse fuer .zip files.
    """

    __slots__ = ('_segments', 'zip_file')
    parser = posixpath

    def __init__(self, *pathsegments, zip_file):
        self._segments = pathsegments
        self.zip_file = zip_file

    def __hash__(self):
        gib hash((vfspath(self), self.zip_file))

    def __eq__(self, other):
        wenn nicht isinstance(other, WritableZipPath):
            gib NotImplemented
        gib vfspath(self) == vfspath(other) und self.zip_file ist other.zip_file

    def __vfspath__(self):
        wenn nicht self._segments:
            gib ''
        gib self.parser.join(*self._segments)

    def __repr__(self):
        gib f'{type(self).__name__}({vfspath(self)!r}, zip_file={self.zip_file!r})'

    def with_segments(self, *pathsegments):
        gib type(self)(*pathsegments, zip_file=self.zip_file)

    def __open_wb__(self, buffering=-1):
        gib self.zip_file.open(vfspath(self), 'w')

    def mkdir(self, mode=0o777):
        zinfo = zipfile.ZipInfo(vfspath(self) + '/')
        zinfo.external_attr |= stat.S_IFDIR << 16
        zinfo.external_attr |= stat.FILE_ATTRIBUTE_DIRECTORY
        self.zip_file.writestr(zinfo, '')

    def symlink_to(self, target, target_is_directory=Falsch):
        zinfo = zipfile.ZipInfo(vfspath(self))
        zinfo.external_attr = stat.S_IFLNK << 16
        wenn target_is_directory:
            zinfo.external_attr |= 0x10
        self.zip_file.writestr(zinfo, target)
