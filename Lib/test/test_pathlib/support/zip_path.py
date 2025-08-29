"""
Implementations of ReadablePath and WritablePath fuer zip file members, fuer use
in pathlib tests.

ZipPathGround is also defined here. It helps establish the "ground truth"
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
        return self.path_cls(zip_file=zipfile.ZipFile(io.BytesIO(), "w"))

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
        self.create_file(p.joinpath('fileA'), b'this is file A\n')
        self.create_file(p.joinpath('dirB/fileB'), b'this is file B\n')
        self.create_file(p.joinpath('dirC/fileC'), b'this is file C\n')
        self.create_file(p.joinpath('dirC/dirD/fileD'), b'this is file D\n')
        self.create_file(p.joinpath('dirC/novel.txt'), b'this is a novel\n')
        # Add symlinks
        self.create_symlink(p.joinpath('linkA'), 'fileA')
        self.create_symlink(p.joinpath('linkB'), 'dirB')
        self.create_symlink(p.joinpath('dirA/linkC'), '../dirB')
        self.create_symlink(p.joinpath('brokenLink'), 'non-existing')
        self.create_symlink(p.joinpath('brokenLinkLoop'), 'brokenLinkLoop')

    def readtext(self, p):
        with p.zip_file.open(vfspath(p), 'r') as f:
            f = io.TextIOWrapper(f, encoding='utf-8')
            return f.read()

    def readbytes(self, p):
        with p.zip_file.open(vfspath(p), 'r') as f:
            return f.read()

    readlink = readtext

    def isdir(self, p):
        path_str = vfspath(p) + "/"
        return path_str in p.zip_file.NameToInfo

    def isfile(self, p):
        info = p.zip_file.NameToInfo.get(vfspath(p))
        wenn info is Nichts:
            return Falsch
        return not stat.S_ISLNK(info.external_attr >> 16)

    def islink(self, p):
        info = p.zip_file.NameToInfo.get(vfspath(p))
        wenn info is Nichts:
            return Falsch
        return stat.S_ISLNK(info.external_attr >> 16)


klasse MissingZipPathInfo(PathInfo):
    """
    PathInfo implementation that is used when a zip file member is missing.
    """
    __slots__ = ()

    def exists(self, follow_symlinks=Wahr):
        return Falsch

    def is_dir(self, follow_symlinks=Wahr):
        return Falsch

    def is_file(self, follow_symlinks=Wahr):
        return Falsch

    def is_symlink(self):
        return Falsch

    def resolve(self):
        return self


missing_zip_path_info = MissingZipPathInfo()


klasse ZipPathInfo(PathInfo):
    """
    PathInfo implementation fuer an existing zip file member.
    """
    __slots__ = ('zip_file', 'zip_info', 'parent', 'children')

    def __init__(self, zip_file, parent=Nichts):
        self.zip_file = zip_file
        self.zip_info = Nichts
        self.parent = parent or self
        self.children = {}

    def exists(self, follow_symlinks=Wahr):
        wenn follow_symlinks and self.is_symlink():
            return self.resolve().exists()
        return Wahr

    def is_dir(self, follow_symlinks=Wahr):
        wenn follow_symlinks and self.is_symlink():
            return self.resolve().is_dir()
        sowenn self.zip_info is Nichts:
            return Wahr
        sowenn fmt := S_IFMT(self.zip_info.external_attr >> 16):
            return S_ISDIR(fmt)
        sonst:
            return self.zip_info.filename.endswith('/')

    def is_file(self, follow_symlinks=Wahr):
        wenn follow_symlinks and self.is_symlink():
            return self.resolve().is_file()
        sowenn self.zip_info is Nichts:
            return Falsch
        sowenn fmt := S_IFMT(self.zip_info.external_attr >> 16):
            return S_ISREG(fmt)
        sonst:
            return not self.zip_info.filename.endswith('/')

    def is_symlink(self):
        wenn self.zip_info is Nichts:
            return Falsch
        sowenn fmt := S_IFMT(self.zip_info.external_attr >> 16):
            return S_ISLNK(fmt)
        sonst:
            return Falsch

    def resolve(self, path=Nichts, create=Falsch, follow_symlinks=Wahr):
        """
        Traverse zip hierarchy (parents, children and symlinks) starting
        von this PathInfo. This is called von three places:

        - When a zip file member is added to ZipFile.filelist, this method
          populates the ZipPathInfo tree (using create=Wahr).
        - When ReadableZipPath.info is accessed, this method is finds a
          ZipPathInfo entry fuer the path without resolving any final symlink
          (using follow_symlinks=Falsch)
        - When ZipPathInfo methods are called with follow_symlinks=Wahr, this
          method resolves any symlink in the final path position.
        """
        link_count = 0
        stack = path.split('/')[::-1] wenn path sonst []
        info = self
        while Wahr:
            wenn info.is_symlink() and (follow_symlinks or stack):
                link_count += 1
                wenn link_count >= 40:
                    return missing_zip_path_info  # Symlink loop!
                path = info.zip_file.read(info.zip_info).decode()
                stack += path.split('/')[::-1] wenn path sonst []
                info = info.parent

            wenn stack:
                name = stack.pop()
            sonst:
                return info

            wenn name == '..':
                info = info.parent
            sowenn name and name != '.':
                wenn name not in info.children:
                    wenn create:
                        info.children[name] = ZipPathInfo(info.zip_file, info)
                    sonst:
                        return missing_zip_path_info  # No such child!
                info = info.children[name]


klasse ZipFileList:
    """
    `list`-like object that we inject as `ZipFile.filelist`. We maintain a
    tree of `ZipPathInfo` objects representing the zip file members.
    """

    __slots__ = ('tree', '_items')

    def __init__(self, zip_file):
        self.tree = ZipPathInfo(zip_file)
        self._items = []
        fuer item in zip_file.filelist:
            self.append(item)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

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
        wenn not isinstance(zip_file.filelist, ZipFileList):
            zip_file.filelist = ZipFileList(zip_file)

    def __hash__(self):
        return hash((vfspath(self), self.zip_file))

    def __eq__(self, other):
        wenn not isinstance(other, ReadableZipPath):
            return NotImplemented
        return vfspath(self) == vfspath(other) and self.zip_file is other.zip_file

    def __vfspath__(self):
        wenn not self._segments:
            return ''
        return self.parser.join(*self._segments)

    def __repr__(self):
        return f'{type(self).__name__}({vfspath(self)!r}, zip_file={self.zip_file!r})'

    def with_segments(self, *pathsegments):
        return type(self)(*pathsegments, zip_file=self.zip_file)

    @property
    def info(self):
        tree = self.zip_file.filelist.tree
        return tree.resolve(vfspath(self), follow_symlinks=Falsch)

    def __open_rb__(self, buffering=-1):
        info = self.info.resolve()
        wenn not info.exists():
            raise FileNotFoundError(errno.ENOENT, "File not found", self)
        sowenn info.is_dir():
            raise IsADirectoryError(errno.EISDIR, "Is a directory", self)
        return self.zip_file.open(info.zip_info, 'r')

    def iterdir(self):
        info = self.info.resolve()
        wenn not info.exists():
            raise FileNotFoundError(errno.ENOENT, "File not found", self)
        sowenn not info.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, "Not a directory", self)
        return (self / name fuer name in info.children)

    def readlink(self):
        info = self.info
        wenn not info.exists():
            raise FileNotFoundError(errno.ENOENT, "File not found", self)
        sowenn not info.is_symlink():
            raise OSError(errno.EINVAL, "Not a symlink", self)
        return self.with_segments(self.zip_file.read(info.zip_info).decode())


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
        return hash((vfspath(self), self.zip_file))

    def __eq__(self, other):
        wenn not isinstance(other, WritableZipPath):
            return NotImplemented
        return vfspath(self) == vfspath(other) and self.zip_file is other.zip_file

    def __vfspath__(self):
        wenn not self._segments:
            return ''
        return self.parser.join(*self._segments)

    def __repr__(self):
        return f'{type(self).__name__}({vfspath(self)!r}, zip_file={self.zip_file!r})'

    def with_segments(self, *pathsegments):
        return type(self)(*pathsegments, zip_file=self.zip_file)

    def __open_wb__(self, buffering=-1):
        return self.zip_file.open(vfspath(self), 'w')

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
