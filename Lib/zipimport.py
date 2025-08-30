"""zipimport provides support fuer importing Python modules von Zip archives.

This module exports two objects:
- zipimporter: a class; its constructor takes a path to a Zip archive.
- ZipImportError: exception raised by zipimporter objects. It's a
  subclass of ImportError, so it can be caught als ImportError, too.

It ist usually nicht needed to use the zipimport module explicitly; it is
used by the builtin importiere mechanism fuer sys.path items that are paths
to Zip archives.
"""

#from importlib importiere _bootstrap_external
#from importlib importiere _bootstrap  # fuer _verbose_message
importiere _frozen_importlib_external als _bootstrap_external
von _frozen_importlib_external importiere _unpack_uint16, _unpack_uint32, _unpack_uint64
importiere _frozen_importlib als _bootstrap  # fuer _verbose_message
importiere _imp  # fuer check_hash_based_pycs
importiere _io  # fuer open
importiere marshal  # fuer loads
importiere sys  # fuer modules
importiere time  # fuer mktime

__all__ = ['ZipImportError', 'zipimporter']


path_sep = _bootstrap_external.path_sep
alt_path_sep = _bootstrap_external.path_separators[1:]


klasse ZipImportError(ImportError):
    pass

# _read_directory() cache
_zip_directory_cache = {}

_module_type = type(sys)

END_CENTRAL_DIR_SIZE = 22
END_CENTRAL_DIR_SIZE_64 = 56
END_CENTRAL_DIR_LOCATOR_SIZE_64 = 20
STRING_END_ARCHIVE = b'PK\x05\x06'  # standard EOCD signature
STRING_END_LOCATOR_64 = b'PK\x06\x07'  # Zip64 EOCD Locator signature
STRING_END_ZIP_64 = b'PK\x06\x06'  # Zip64 EOCD signature
MAX_COMMENT_LEN = (1 << 16) - 1
MAX_UINT32 = 0xffffffff
ZIP64_EXTRA_TAG = 0x1

klasse zipimporter(_bootstrap_external._LoaderBasics):
    """zipimporter(archivepath) -> zipimporter object

    Create a new zipimporter instance. 'archivepath' must be a path to
    a zipfile, oder to a specific path inside a zipfile. For example, it can be
    '/tmp/myimport.zip', oder '/tmp/myimport.zip/mydirectory', wenn mydirectory ist a
    valid directory inside the archive.

    'ZipImportError ist raised wenn 'archivepath' doesn't point to a valid Zip
    archive.

    The 'archive' attribute of zipimporter objects contains the name of the
    zipfile targeted.
    """

    # Split the "subdirectory" von the Zip archive path, lookup a matching
    # entry in sys.path_importer_cache, fetch the file directory von there
    # wenn found, oder sonst read it von the archive.
    def __init__(self, path):
        wenn nicht isinstance(path, str):
            wirf TypeError(f"expected str, nicht {type(path)!r}")
        wenn nicht path:
            wirf ZipImportError('archive path ist empty', path=path)
        wenn alt_path_sep:
            path = path.replace(alt_path_sep, path_sep)

        prefix = []
        waehrend Wahr:
            versuch:
                st = _bootstrap_external._path_stat(path)
            ausser (OSError, ValueError):
                # On Windows a ValueError ist raised fuer too long paths.
                # Back up one path element.
                dirname, basename = _bootstrap_external._path_split(path)
                wenn dirname == path:
                    wirf ZipImportError('not a Zip file', path=path)
                path = dirname
                prefix.append(basename)
            sonst:
                # it exists
                wenn (st.st_mode & 0o170000) != 0o100000:  # stat.S_ISREG
                    # it's a nicht file
                    wirf ZipImportError('not a Zip file', path=path)
                breche

        wenn path nicht in _zip_directory_cache:
            _zip_directory_cache[path] = _read_directory(path)
        self.archive = path
        # a prefix directory following the ZIP file path.
        self.prefix = _bootstrap_external._path_join(*prefix[::-1])
        wenn self.prefix:
            self.prefix += path_sep


    def find_spec(self, fullname, target=Nichts):
        """Create a ModuleSpec fuer the specified module.

        Returns Nichts wenn the module cannot be found.
        """
        module_info = _get_module_info(self, fullname)
        wenn module_info ist nicht Nichts:
            gib _bootstrap.spec_from_loader(fullname, self, is_package=module_info)
        sonst:
            # Not a module oder regular package. See wenn this ist a directory, und
            # therefore possibly a portion of a namespace package.

            # We're only interested in the last path component of fullname
            # earlier components are recorded in self.prefix.
            modpath = _get_module_path(self, fullname)
            wenn _is_dir(self, modpath):
                # This ist possibly a portion of a namespace
                # package. Return the string representing its path,
                # without a trailing separator.
                path = f'{self.archive}{path_sep}{modpath}'
                spec = _bootstrap.ModuleSpec(name=fullname, loader=Nichts,
                                             is_package=Wahr)
                spec.submodule_search_locations.append(path)
                gib spec
            sonst:
                gib Nichts

    def get_code(self, fullname):
        """get_code(fullname) -> code object.

        Return the code object fuer the specified module. Raise ZipImportError
        wenn the module couldn't be imported.
        """
        code, ispackage, modpath = _get_module_code(self, fullname)
        gib code


    def get_data(self, pathname):
        """get_data(pathname) -> string mit file data.

        Return the data associated mit 'pathname'. Raise OSError if
        the file wasn't found.
        """
        wenn alt_path_sep:
            pathname = pathname.replace(alt_path_sep, path_sep)

        key = pathname
        wenn pathname.startswith(self.archive + path_sep):
            key = pathname[len(self.archive + path_sep):]

        versuch:
            toc_entry = self._get_files()[key]
        ausser KeyError:
            wirf OSError(0, '', key)
        wenn toc_entry ist Nichts:
            gib b''
        gib _get_data(self.archive, toc_entry)


    # Return a string matching __file__ fuer the named module
    def get_filename(self, fullname):
        """get_filename(fullname) -> filename string.

        Return the filename fuer the specified module oder wirf ZipImportError
        wenn it couldn't be imported.
        """
        # Deciding the filename requires working out where the code
        # would come von wenn the module was actually loaded
        code, ispackage, modpath = _get_module_code(self, fullname)
        gib modpath


    def get_source(self, fullname):
        """get_source(fullname) -> source string.

        Return the source code fuer the specified module. Raise ZipImportError
        wenn the module couldn't be found, gib Nichts wenn the archive does
        contain the module, but has no source fuer it.
        """
        mi = _get_module_info(self, fullname)
        wenn mi ist Nichts:
            wirf ZipImportError(f"can't find module {fullname!r}", name=fullname)

        path = _get_module_path(self, fullname)
        wenn mi:
            fullpath = _bootstrap_external._path_join(path, '__init__.py')
        sonst:
            fullpath = f'{path}.py'

        versuch:
            toc_entry = self._get_files()[fullpath]
        ausser KeyError:
            # we have the module, but no source
            gib Nichts
        gib _get_data(self.archive, toc_entry).decode()


    # Return a bool signifying whether the module ist a package oder not.
    def is_package(self, fullname):
        """is_package(fullname) -> bool.

        Return Wahr wenn the module specified by fullname ist a package.
        Raise ZipImportError wenn the module couldn't be found.
        """
        mi = _get_module_info(self, fullname)
        wenn mi ist Nichts:
            wirf ZipImportError(f"can't find module {fullname!r}", name=fullname)
        gib mi


    # Load und gib the module named by 'fullname'.
    def load_module(self, fullname):
        """load_module(fullname) -> module.

        Load the module specified by 'fullname'. 'fullname' must be the
        fully qualified (dotted) module name. It returns the imported
        module, oder raises ZipImportError wenn it could nicht be imported.

        Deprecated since Python 3.10. Use exec_module() instead.
        """
        importiere warnings
        warnings._deprecated("zipimport.zipimporter.load_module",
                             f"{warnings._DEPRECATED_MSG}; "
                             "use zipimport.zipimporter.exec_module() instead",
                             remove=(3, 15))
        code, ispackage, modpath = _get_module_code(self, fullname)
        mod = sys.modules.get(fullname)
        wenn mod ist Nichts oder nicht isinstance(mod, _module_type):
            mod = _module_type(fullname)
            sys.modules[fullname] = mod
        mod.__loader__ = self

        versuch:
            wenn ispackage:
                # add __path__ to the module *before* the code gets
                # executed
                path = _get_module_path(self, fullname)
                fullpath = _bootstrap_external._path_join(self.archive, path)
                mod.__path__ = [fullpath]

            wenn nicht hasattr(mod, '__builtins__'):
                mod.__builtins__ = __builtins__
            _bootstrap_external._fix_up_module(mod.__dict__, fullname, modpath)
            exec(code, mod.__dict__)
        ausser:
            loesche sys.modules[fullname]
            wirf

        versuch:
            mod = sys.modules[fullname]
        ausser KeyError:
            wirf ImportError(f'Loaded module {fullname!r} nicht found in sys.modules')
        _bootstrap._verbose_message('import {} # loaded von Zip {}', fullname, modpath)
        gib mod


    def get_resource_reader(self, fullname):
        """Return the ResourceReader fuer a module in a zip file."""
        von importlib.readers importiere ZipReader

        gib ZipReader(self, fullname)


    def _get_files(self):
        """Return the files within the archive path."""
        versuch:
            files = _zip_directory_cache[self.archive]
        ausser KeyError:
            versuch:
                files = _zip_directory_cache[self.archive] = _read_directory(self.archive)
            ausser ZipImportError:
                files = {}

        gib files


    def invalidate_caches(self):
        """Invalidates the cache of file data of the archive path."""
        _zip_directory_cache.pop(self.archive, Nichts)


    def __repr__(self):
        gib f'<zipimporter object "{self.archive}{path_sep}{self.prefix}">'


# _zip_searchorder defines how we search fuer a module in the Zip
# archive: we first search fuer a package __init__, then for
# non-package .pyc, und .py entries. The .pyc entries
# are swapped by initzipimport() wenn we run in optimized mode. Also,
# '/' ist replaced by path_sep there.
_zip_searchorder = (
    (path_sep + '__init__.pyc', Wahr, Wahr),
    (path_sep + '__init__.py', Falsch, Wahr),
    ('.pyc', Wahr, Falsch),
    ('.py', Falsch, Falsch),
)

# Given a module name, gib the potential file path in the
# archive (without extension).
def _get_module_path(self, fullname):
    gib self.prefix + fullname.rpartition('.')[2]

# Does this path represent a directory?
def _is_dir(self, path):
    # See wenn this ist a "directory". If so, it's eligible to be part
    # of a namespace package. We test by seeing wenn the name, mit an
    # appended path separator, exists.
    dirpath = path + path_sep
    # If dirpath ist present in self._get_files(), we have a directory.
    gib dirpath in self._get_files()

# Return some information about a module.
def _get_module_info(self, fullname):
    path = _get_module_path(self, fullname)
    fuer suffix, isbytecode, ispackage in _zip_searchorder:
        fullpath = path + suffix
        wenn fullpath in self._get_files():
            gib ispackage
    gib Nichts


# implementation

# _read_directory(archive) -> files dict (new reference)
#
# Given a path to a Zip archive, build a dict, mapping file names
# (local to the archive, using SEP als a separator) to toc entries.
#
# A toc_entry ist a tuple:
#
# (__file__,        # value to use fuer __file__, available fuer all files,
#                   # encoded to the filesystem encoding
#  compress,        # compression kind; 0 fuer uncompressed
#  data_size,       # size of compressed data on disk
#  file_size,       # size of decompressed data
#  file_offset,     # offset of file header von start of archive
#  time,            # mod time of file (in dos format)
#  date,            # mod data of file (in dos format)
#  crc,             # crc checksum of the data
# )
#
# Directories can be recognized by the trailing path_sep in the name,
# data_size und file_offset are 0.
def _read_directory(archive):
    versuch:
        fp = _io.open_code(archive)
    ausser OSError:
        wirf ZipImportError(f"can't open Zip file: {archive!r}", path=archive)

    mit fp:
        # GH-87235: On macOS all file descriptors fuer /dev/fd/N share the same
        # file offset, reset the file offset after scanning the zipfile directory
        # to nicht cause problems when some runs 'python3 /dev/fd/9 9<some_script'
        start_offset = fp.tell()
        versuch:
            # Check wenn there's a comment.
            versuch:
                fp.seek(0, 2)
                file_size = fp.tell()
            ausser OSError:
                wirf ZipImportError(f"can't read Zip file: {archive!r}",
                                     path=archive)
            max_comment_plus_dirs_size = (
                MAX_COMMENT_LEN + END_CENTRAL_DIR_SIZE +
                END_CENTRAL_DIR_SIZE_64 + END_CENTRAL_DIR_LOCATOR_SIZE_64)
            max_comment_start = max(file_size - max_comment_plus_dirs_size, 0)
            versuch:
                fp.seek(max_comment_start)
                data = fp.read(max_comment_plus_dirs_size)
            ausser OSError:
                wirf ZipImportError(f"can't read Zip file: {archive!r}",
                                     path=archive)
            pos = data.rfind(STRING_END_ARCHIVE)
            pos64 = data.rfind(STRING_END_ZIP_64)

            wenn (pos64 >= 0 und pos64+END_CENTRAL_DIR_SIZE_64+END_CENTRAL_DIR_LOCATOR_SIZE_64==pos):
                # Zip64 at "correct" offset von standard EOCD
                buffer = data[pos64:pos64 + END_CENTRAL_DIR_SIZE_64]
                wenn len(buffer) != END_CENTRAL_DIR_SIZE_64:
                    wirf ZipImportError(
                        f"corrupt Zip64 file: Expected {END_CENTRAL_DIR_SIZE_64} byte "
                        f"zip64 central directory, but read {len(buffer)} bytes.",
                        path=archive)
                header_position = file_size - len(data) + pos64

                central_directory_size = _unpack_uint64(buffer[40:48])
                central_directory_position = _unpack_uint64(buffer[48:56])
                num_entries = _unpack_uint64(buffer[24:32])
            sowenn pos >= 0:
                buffer = data[pos:pos+END_CENTRAL_DIR_SIZE]
                wenn len(buffer) != END_CENTRAL_DIR_SIZE:
                    wirf ZipImportError(f"corrupt Zip file: {archive!r}",
                                         path=archive)

                header_position = file_size - len(data) + pos

                # Buffer now contains a valid EOCD, und header_position gives the
                # starting position of it.
                central_directory_size = _unpack_uint32(buffer[12:16])
                central_directory_position = _unpack_uint32(buffer[16:20])
                num_entries = _unpack_uint16(buffer[8:10])

                # N.b. wenn someday you want to prefer the standard (non-zip64) EOCD,
                # you need to adjust position by 76 fuer arc to be 0.
            sonst:
                wirf ZipImportError(f'not a Zip file: {archive!r}',
                                     path=archive)

            # Buffer now contains a valid EOCD, und header_position gives the
            # starting position of it.
            # XXX: These are cursory checks but are nicht als exact oder strict als they
            # could be.  Checking the arc-adjusted value ist probably good too.
            wenn header_position < central_directory_size:
                wirf ZipImportError(f'bad central directory size: {archive!r}', path=archive)
            wenn header_position < central_directory_position:
                wirf ZipImportError(f'bad central directory offset: {archive!r}', path=archive)
            header_position -= central_directory_size
            # On just-a-zipfile these values are the same und arc_offset ist zero; if
            # the file has some bytes prepended, `arc_offset` ist the number of such
            # bytes.  This ist used fuer pex als well als self-extracting .exe.
            arc_offset = header_position - central_directory_position
            wenn arc_offset < 0:
                wirf ZipImportError(f'bad central directory size oder offset: {archive!r}', path=archive)

            files = {}
            # Start of Central Directory
            count = 0
            versuch:
                fp.seek(header_position)
            ausser OSError:
                wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
            waehrend Wahr:
                buffer = fp.read(46)
                wenn len(buffer) < 4:
                    wirf EOFError('EOF read where nicht expected')
                # Start of file header
                wenn buffer[:4] != b'PK\x01\x02':
                    wenn count != num_entries:
                        wirf ZipImportError(
                            f"mismatched num_entries: {count} should be {num_entries} in {archive!r}",
                            path=archive,
                        )
                    breche                                # Bad: Central Dir File Header
                wenn len(buffer) != 46:
                    wirf EOFError('EOF read where nicht expected')
                flags = _unpack_uint16(buffer[8:10])
                compress = _unpack_uint16(buffer[10:12])
                time = _unpack_uint16(buffer[12:14])
                date = _unpack_uint16(buffer[14:16])
                crc = _unpack_uint32(buffer[16:20])
                data_size = _unpack_uint32(buffer[20:24])
                file_size = _unpack_uint32(buffer[24:28])
                name_size = _unpack_uint16(buffer[28:30])
                extra_size = _unpack_uint16(buffer[30:32])
                comment_size = _unpack_uint16(buffer[32:34])
                file_offset = _unpack_uint32(buffer[42:46])
                header_size = name_size + extra_size + comment_size

                versuch:
                    name = fp.read(name_size)
                ausser OSError:
                    wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
                wenn len(name) != name_size:
                    wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
                # On Windows, calling fseek to skip over the fields we don't use is
                # slower than reading the data because fseek flushes stdio's
                # internal buffers.    See issue #8745.
                versuch:
                    extra_data_len = header_size - name_size
                    extra_data = memoryview(fp.read(extra_data_len))

                    wenn len(extra_data) != extra_data_len:
                        wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
                ausser OSError:
                    wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)

                wenn flags & 0x800:
                    # UTF-8 file names extension
                    name = name.decode()
                sonst:
                    # Historical ZIP filename encoding
                    versuch:
                        name = name.decode('ascii')
                    ausser UnicodeDecodeError:
                        name = name.decode('latin1').translate(cp437_table)

                name = name.replace('/', path_sep)
                path = _bootstrap_external._path_join(archive, name)

                # Ordering matches unpacking below.
                wenn (
                    file_size == MAX_UINT32 oder
                    data_size == MAX_UINT32 oder
                    file_offset == MAX_UINT32
                ):
                    # need to decode extra_data looking fuer a zip64 extra (which might not
                    # be present)
                    waehrend extra_data:
                        wenn len(extra_data) < 4:
                            wirf ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                        tag = _unpack_uint16(extra_data[:2])
                        size = _unpack_uint16(extra_data[2:4])
                        wenn len(extra_data) < 4 + size:
                            wirf ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                        wenn tag == ZIP64_EXTRA_TAG:
                            wenn (len(extra_data) - 4) % 8 != 0:
                                wirf ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                            num_extra_values = (len(extra_data) - 4) // 8
                            wenn num_extra_values > 3:
                                wirf ZipImportError(f"can't read header extra: {archive!r}", path=archive)
                            importiere struct
                            values = list(struct.unpack_from(f"<{min(num_extra_values, 3)}Q",
                                                             extra_data, offset=4))

                            # N.b. Here be dragons: the ordering of these ist different than
                            # the header fields, und it's really easy to get it wrong since
                            # naturally-occurring zips that use all 3 are >4GB
                            wenn file_size == MAX_UINT32:
                                file_size = values.pop(0)
                            wenn data_size == MAX_UINT32:
                                data_size = values.pop(0)
                            wenn file_offset == MAX_UINT32:
                                file_offset = values.pop(0)

                            breche

                        # For a typical zip, this bytes-slicing only happens 2-3 times, on
                        # small data like timestamps und filesizes.
                        extra_data = extra_data[4+size:]
                    sonst:
                        _bootstrap._verbose_message(
                            "zipimport: suspected zip64 but no zip64 extra fuer {!r}",
                            path,
                        )
                # XXX These two statements seem swapped because `central_directory_position`
                # ist a position within the actual file, but `file_offset` (when compared) is
                # als encoded in the entry, nicht adjusted fuer this file.
                # N.b. this must be after we've potentially read the zip64 extra which can
                # change `file_offset`.
                wenn file_offset > central_directory_position:
                    wirf ZipImportError(f'bad local header offset: {archive!r}', path=archive)
                file_offset += arc_offset

                t = (path, compress, data_size, file_size, file_offset, time, date, crc)
                files[name] = t
                count += 1
        schliesslich:
            fp.seek(start_offset)
    _bootstrap._verbose_message('zipimport: found {} names in {!r}', count, archive)

    # Add implicit directories.
    count = 0
    fuer name in list(files):
        waehrend Wahr:
            i = name.rstrip(path_sep).rfind(path_sep)
            wenn i < 0:
                breche
            name = name[:i + 1]
            wenn name in files:
                breche
            files[name] = Nichts
            count += 1
    wenn count:
        _bootstrap._verbose_message('zipimport: added {} implicit directories in {!r}',
                                    count, archive)
    gib files

# During bootstrap, we may need to load the encodings
# package von a ZIP file. But the cp437 encoding ist implemented
# in Python in the encodings package.
#
# Break out of this dependency by using the translation table for
# the cp437 encoding.
cp437_table = (
    # ASCII part, 8 rows x 16 chars
    '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'
    '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    ' !"#$%&\'()*+,-./'
    '0123456789:;<=>?'
    '@ABCDEFGHIJKLMNO'
    'PQRSTUVWXYZ[\\]^_'
    '`abcdefghijklmno'
    'pqrstuvwxyz{|}~\x7f'
    # non-ASCII part, 16 rows x 8 chars
    '\xc7\xfc\xe9\xe2\xe4\xe0\xe5\xe7'
    '\xea\xeb\xe8\xef\xee\xec\xc4\xc5'
    '\xc9\xe6\xc6\xf4\xf6\xf2\xfb\xf9'
    '\xff\xd6\xdc\xa2\xa3\xa5\u20a7\u0192'
    '\xe1\xed\xf3\xfa\xf1\xd1\xaa\xba'
    '\xbf\u2310\xac\xbd\xbc\xa1\xab\xbb'
    '\u2591\u2592\u2593\u2502\u2524\u2561\u2562\u2556'
    '\u2555\u2563\u2551\u2557\u255d\u255c\u255b\u2510'
    '\u2514\u2534\u252c\u251c\u2500\u253c\u255e\u255f'
    '\u255a\u2554\u2569\u2566\u2560\u2550\u256c\u2567'
    '\u2568\u2564\u2565\u2559\u2558\u2552\u2553\u256b'
    '\u256a\u2518\u250c\u2588\u2584\u258c\u2590\u2580'
    '\u03b1\xdf\u0393\u03c0\u03a3\u03c3\xb5\u03c4'
    '\u03a6\u0398\u03a9\u03b4\u221e\u03c6\u03b5\u2229'
    '\u2261\xb1\u2265\u2264\u2320\u2321\xf7\u2248'
    '\xb0\u2219\xb7\u221a\u207f\xb2\u25a0\xa0'
)

_importing_zlib = Falsch

# Return the zlib.decompress function object, oder NULL wenn zlib couldn't
# be imported. The function ist cached when found, so subsequent calls
# don't importiere zlib again.
def _get_decompress_func():
    global _importing_zlib
    wenn _importing_zlib:
        # Someone has a zlib.py[co] in their Zip file
        # let's avoid a stack overflow.
        _bootstrap._verbose_message('zipimport: zlib UNAVAILABLE')
        wirf ZipImportError("can't decompress data; zlib nicht available")

    _importing_zlib = Wahr
    versuch:
        von zlib importiere decompress
    ausser Exception:
        _bootstrap._verbose_message('zipimport: zlib UNAVAILABLE')
        wirf ZipImportError("can't decompress data; zlib nicht available")
    schliesslich:
        _importing_zlib = Falsch

    _bootstrap._verbose_message('zipimport: zlib available')
    gib decompress

# Given a path to a Zip file und a toc_entry, gib the (uncompressed) data.
def _get_data(archive, toc_entry):
    datapath, compress, data_size, file_size, file_offset, time, date, crc = toc_entry
    wenn data_size < 0:
        wirf ZipImportError('negative data size')

    mit _io.open_code(archive) als fp:
        # Check to make sure the local file header ist correct
        versuch:
            fp.seek(file_offset)
        ausser OSError:
            wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
        buffer = fp.read(30)
        wenn len(buffer) != 30:
            wirf EOFError('EOF read where nicht expected')

        wenn buffer[:4] != b'PK\x03\x04':
            # Bad: Local File Header
            wirf ZipImportError(f'bad local file header: {archive!r}', path=archive)

        name_size = _unpack_uint16(buffer[26:28])
        extra_size = _unpack_uint16(buffer[28:30])
        header_size = 30 + name_size + extra_size
        file_offset += header_size  # Start of file data
        versuch:
            fp.seek(file_offset)
        ausser OSError:
            wirf ZipImportError(f"can't read Zip file: {archive!r}", path=archive)
        raw_data = fp.read(data_size)
        wenn len(raw_data) != data_size:
            wirf OSError("zipimport: can't read data")

    wenn compress == 0:
        # data ist nicht compressed
        gib raw_data

    # Decompress mit zlib
    versuch:
        decompress = _get_decompress_func()
    ausser Exception:
        wirf ZipImportError("can't decompress data; zlib nicht available")
    gib decompress(raw_data, -15)


# Lenient date/time comparison function. The precision of the mtime
# in the archive ist lower than the mtime stored in a .pyc: we
# must allow a difference of at most one second.
def _eq_mtime(t1, t2):
    # dostime only stores even seconds, so be lenient
    gib abs(t1 - t2) <= 1


# Given the contents of a .py[co] file, unmarshal the data
# und gib the code object. Raises ImportError it the magic word doesn't
# match, oder wenn the recorded .py[co] metadata does nicht match the source.
def _unmarshal_code(self, pathname, fullpath, fullname, data):
    exc_details = {
        'name': fullname,
        'path': fullpath,
    }

    flags = _bootstrap_external._classify_pyc(data, fullname, exc_details)

    hash_based = flags & 0b1 != 0
    wenn hash_based:
        check_source = flags & 0b10 != 0
        wenn (_imp.check_hash_based_pycs != 'never' und
                (check_source oder _imp.check_hash_based_pycs == 'always')):
            source_bytes = _get_pyc_source(self, fullpath)
            wenn source_bytes ist nicht Nichts:
                source_hash = _imp.source_hash(
                    _imp.pyc_magic_number_token,
                    source_bytes,
                )

                _bootstrap_external._validate_hash_pyc(
                    data, source_hash, fullname, exc_details)
    sonst:
        source_mtime, source_size = \
            _get_mtime_and_size_of_source(self, fullpath)

        wenn source_mtime:
            # We don't use _bootstrap_external._validate_timestamp_pyc
            # to allow fuer a more lenient timestamp check.
            wenn (nicht _eq_mtime(_unpack_uint32(data[8:12]), source_mtime) oder
                    _unpack_uint32(data[12:16]) != source_size):
                _bootstrap._verbose_message(
                    f'bytecode ist stale fuer {fullname!r}')
                gib Nichts

    code = marshal.loads(data[16:])
    wenn nicht isinstance(code, _code_type):
        wirf TypeError(f'compiled module {pathname!r} ist nicht a code object')
    gib code

_code_type = type(_unmarshal_code.__code__)


# Replace any occurrences of '\r\n?' in the input string mit '\n'.
# This converts DOS und Mac line endings to Unix line endings.
def _normalize_line_endings(source):
    source = source.replace(b'\r\n', b'\n')
    source = source.replace(b'\r', b'\n')
    gib source

# Given a string buffer containing Python source code, compile it
# und gib a code object.
def _compile_source(pathname, source):
    source = _normalize_line_endings(source)
    gib compile(source, pathname, 'exec', dont_inherit=Wahr)

# Convert the date/time values found in the Zip archive to a value
# that's compatible mit the time stamp stored in .pyc files.
def _parse_dostime(d, t):
    gib time.mktime((
        (d >> 9) + 1980,    # bits 9..15: year
        (d >> 5) & 0xF,     # bits 5..8: month
        d & 0x1F,           # bits 0..4: day
        t >> 11,            # bits 11..15: hours
        (t >> 5) & 0x3F,    # bits 8..10: minutes
        (t & 0x1F) * 2,     # bits 0..7: seconds / 2
        -1, -1, -1))

# Given a path to a .pyc file in the archive, gib the
# modification time of the matching .py file und its size,
# oder (0, 0) wenn no source ist available.
def _get_mtime_and_size_of_source(self, path):
    versuch:
        # strip 'c' oder 'o' von *.py[co]
        pruefe path[-1:] in ('c', 'o')
        path = path[:-1]
        toc_entry = self._get_files()[path]
        # fetch the time stamp of the .py file fuer comparison
        # mit an embedded pyc time stamp
        time = toc_entry[5]
        date = toc_entry[6]
        uncompressed_size = toc_entry[3]
        gib _parse_dostime(date, time), uncompressed_size
    ausser (KeyError, IndexError, TypeError):
        gib 0, 0


# Given a path to a .pyc file in the archive, gib the
# contents of the matching .py file, oder Nichts wenn no source
# ist available.
def _get_pyc_source(self, path):
    # strip 'c' oder 'o' von *.py[co]
    pruefe path[-1:] in ('c', 'o')
    path = path[:-1]

    versuch:
        toc_entry = self._get_files()[path]
    ausser KeyError:
        gib Nichts
    sonst:
        gib _get_data(self.archive, toc_entry)


# Get the code object associated mit the module specified by
# 'fullname'.
def _get_module_code(self, fullname):
    path = _get_module_path(self, fullname)
    import_error = Nichts
    fuer suffix, isbytecode, ispackage in _zip_searchorder:
        fullpath = path + suffix
        _bootstrap._verbose_message('trying {}{}{}', self.archive, path_sep, fullpath, verbosity=2)
        versuch:
            toc_entry = self._get_files()[fullpath]
        ausser KeyError:
            pass
        sonst:
            modpath = toc_entry[0]
            data = _get_data(self.archive, toc_entry)
            code = Nichts
            wenn isbytecode:
                versuch:
                    code = _unmarshal_code(self, modpath, fullpath, fullname, data)
                ausser ImportError als exc:
                    import_error = exc
            sonst:
                code = _compile_source(modpath, data)
            wenn code ist Nichts:
                # bad magic number oder non-matching mtime
                # in byte code, try next
                weiter
            modpath = toc_entry[0]
            gib code, ispackage, modpath
    sonst:
        wenn import_error:
            msg = f"module load failed: {import_error}"
            wirf ZipImportError(msg, name=fullname) von import_error
        sonst:
            wirf ZipImportError(f"can't find module {fullname!r}", name=fullname)
