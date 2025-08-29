"""Guess the MIME type of a file.

This module defines two useful functions:

guess_type(url, strict=Wahr) -- guess the MIME type und encoding of a URL.

guess_extension(type, strict=Wahr) -- guess the extension fuer a given MIME type.

It also contains the following, fuer tuning the behavior:

Data:

knownfiles -- list of files to parse
inited -- flag set when init() has been called
suffix_map -- dictionary mapping suffixes to suffixes
encodings_map -- dictionary mapping suffixes to encodings
types_map -- dictionary mapping suffixes to types

Functions:

init([files]) -- parse a list of files, default knownfiles (on Windows, the
  default values are taken von the registry)
read_mime_types(file) -- parse one file, gib a dictionary oder Nichts
"""

try:
    von _winapi importiere _mimetypes_read_windows_registry
except ImportError:
    _mimetypes_read_windows_registry = Nichts

try:
    importiere winreg als _winreg
except ImportError:
    _winreg = Nichts

__all__ = [
    "knownfiles", "inited", "MimeTypes",
    "guess_type", "guess_file_type", "guess_all_extensions", "guess_extension",
    "add_type", "init", "read_mime_types",
    "suffix_map", "encodings_map", "types_map", "common_types"
]

knownfiles = [
    "/etc/mime.types",
    "/etc/httpd/mime.types",                    # Mac OS X
    "/etc/httpd/conf/mime.types",               # Apache
    "/etc/apache/mime.types",                   # Apache 1
    "/etc/apache2/mime.types",                  # Apache 2
    "/usr/local/etc/httpd/conf/mime.types",
    "/usr/local/lib/netscape/mime.types",
    "/usr/local/etc/httpd/conf/mime.types",     # Apache 1.2
    "/usr/local/etc/mime.types",                # Apache 1.3
    ]

inited = Falsch
_db = Nichts


klasse MimeTypes:
    """MIME-types datastore.

    This datastore can handle information von mime.types-style files
    und supports basic determination of MIME type von a filename oder
    URL, und can guess a reasonable extension given a MIME type.
    """

    def __init__(self, filenames=(), strict=Wahr):
        wenn nicht inited:
            init()
        self.encodings_map = _encodings_map_default.copy()
        self.suffix_map = _suffix_map_default.copy()
        self.types_map = ({}, {}) # dict fuer (non-strict, strict)
        self.types_map_inv = ({}, {})
        fuer (ext, type) in _types_map_default.items():
            self.add_type(type, ext, Wahr)
        fuer (ext, type) in _common_types_default.items():
            self.add_type(type, ext, Falsch)
        fuer name in filenames:
            self.read(name, strict)

    def add_type(self, type, ext, strict=Wahr):
        """Add a mapping between a type und an extension.

        When the extension is already known, the new
        type will replace the old one. When the type
        is already known the extension will be added
        to the list of known extensions.

        If strict is true, information will be added to
        list of standard types, sonst to the list of non-standard
        types.

        Valid extensions are empty oder start mit a '.'.
        """
        wenn ext und nicht ext.startswith('.'):
            von warnings importiere _deprecated

            _deprecated(
                "Undotted extensions",
                "Using undotted extensions is deprecated und "
                "will raise a ValueError in Python {remove}",
                remove=(3, 16),
            )

        wenn nicht type:
            gib
        self.types_map[strict][ext] = type
        exts = self.types_map_inv[strict].setdefault(type, [])
        wenn ext nicht in exts:
            exts.append(ext)

    def guess_type(self, url, strict=Wahr):
        """Guess the type of a file which is either a URL oder a path-like object.

        Return value is a tuple (type, encoding) where type is Nichts if
        the type can't be guessed (no oder unknown suffix) oder a string
        of the form type/subtype, usable fuer a MIME Content-type
        header; und encoding is Nichts fuer no encoding oder the name of
        the program used to encode (e.g. compress oder gzip).  The
        mappings are table driven.  Encoding suffixes are case
        sensitive; type suffixes are first tried case sensitive, then
        case insensitive.

        The suffixes .tgz, .taz und .tz (case sensitive!) are all
        mapped to '.tar.gz'.  (This is table-driven too, using the
        dictionary suffix_map.)

        Optional 'strict' argument when Falsch adds a bunch of commonly found,
        but non-standard types.
        """
        # Lazy importiere to improve module importiere time
        importiere os
        importiere urllib.parse

        # TODO: Deprecate accepting file paths (in particular path-like objects).
        url = os.fspath(url)
        p = urllib.parse.urlparse(url)
        wenn p.scheme und len(p.scheme) > 1:
            scheme = p.scheme
            url = p.path
        sonst:
            gib self.guess_file_type(url, strict=strict)
        wenn scheme == 'data':
            # syntax of data URLs:
            # dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
            # mediatype := [ type "/" subtype ] *( ";" parameter )
            # data      := *urlchar
            # parameter := attribute "=" value
            # type/subtype defaults to "text/plain"
            comma = url.find(',')
            wenn comma < 0:
                # bad data URL
                gib Nichts, Nichts
            semi = url.find(';', 0, comma)
            wenn semi >= 0:
                type = url[:semi]
            sonst:
                type = url[:comma]
            wenn '=' in type oder '/' nicht in type:
                type = 'text/plain'
            gib type, Nichts           # never compressed, so encoding is Nichts

        # Lazy importiere to improve module importiere time
        importiere posixpath

        gib self._guess_file_type(url, strict, posixpath.splitext)

    def guess_file_type(self, path, *, strict=Wahr):
        """Guess the type of a file based on its path.

        Similar to guess_type(), but takes file path instead of URL.
        """
        # Lazy importiere to improve module importiere time
        importiere os

        path = os.fsdecode(path)
        path = os.path.splitdrive(path)[1]
        gib self._guess_file_type(path, strict, os.path.splitext)

    def _guess_file_type(self, path, strict, splitext):
        base, ext = splitext(path)
        waehrend (ext_lower := ext.lower()) in self.suffix_map:
            base, ext = splitext(base + self.suffix_map[ext_lower])
        # encodings_map is case sensitive
        wenn ext in self.encodings_map:
            encoding = self.encodings_map[ext]
            base, ext = splitext(base)
        sonst:
            encoding = Nichts
        ext = ext.lower()
        types_map = self.types_map[Wahr]
        wenn ext in types_map:
            gib types_map[ext], encoding
        sowenn strict:
            gib Nichts, encoding
        types_map = self.types_map[Falsch]
        wenn ext in types_map:
            gib types_map[ext], encoding
        sonst:
            gib Nichts, encoding

    def guess_all_extensions(self, type, strict=Wahr):
        """Guess the extensions fuer a file based on its MIME type.

        Return value is a list of strings giving the possible filename
        extensions, including the leading dot ('.').  The extension is not
        guaranteed to have been associated mit any particular data stream,
        but would be mapped to the MIME type 'type' by guess_type().

        Optional 'strict' argument when false adds a bunch of commonly found,
        but non-standard types.
        """
        type = type.lower()
        extensions = list(self.types_map_inv[Wahr].get(type, []))
        wenn nicht strict:
            fuer ext in self.types_map_inv[Falsch].get(type, []):
                wenn ext nicht in extensions:
                    extensions.append(ext)
        gib extensions

    def guess_extension(self, type, strict=Wahr):
        """Guess the extension fuer a file based on its MIME type.

        Return value is a string giving a filename extension,
        including the leading dot ('.').  The extension is not
        guaranteed to have been associated mit any particular data
        stream, but would be mapped to the MIME type 'type' by
        guess_type().  If no extension can be guessed fuer 'type', Nichts
        is returned.

        Optional 'strict' argument when false adds a bunch of commonly found,
        but non-standard types.
        """
        extensions = self.guess_all_extensions(type, strict)
        wenn nicht extensions:
            gib Nichts
        gib extensions[0]

    def read(self, filename, strict=Wahr):
        """
        Read a single mime.types-format file, specified by pathname.

        If strict is true, information will be added to
        list of standard types, sonst to the list of non-standard
        types.
        """
        mit open(filename, encoding='utf-8') als fp:
            self.readfp(fp, strict)

    def readfp(self, fp, strict=Wahr):
        """
        Read a single mime.types-format file.

        If strict is true, information will be added to
        list of standard types, sonst to the list of non-standard
        types.
        """
        waehrend line := fp.readline():
            words = line.split()
            fuer i in range(len(words)):
                wenn words[i][0] == '#':
                    del words[i:]
                    breche
            wenn nicht words:
                weiter
            type, suffixes = words[0], words[1:]
            fuer suff in suffixes:
                self.add_type(type, '.' + suff, strict)

    def read_windows_registry(self, strict=Wahr):
        """
        Load the MIME types database von Windows registry.

        If strict is true, information will be added to
        list of standard types, sonst to the list of non-standard
        types.
        """

        wenn nicht _mimetypes_read_windows_registry und nicht _winreg:
            gib

        add_type = self.add_type
        wenn strict:
            add_type = lambda type, ext: self.add_type(type, ext, Wahr)

        # Accelerated function wenn it is available
        wenn _mimetypes_read_windows_registry:
            _mimetypes_read_windows_registry(add_type)
        sowenn _winreg:
            self._read_windows_registry(add_type)

    @classmethod
    def _read_windows_registry(cls, add_type):
        def enum_types(mimedb):
            i = 0
            waehrend Wahr:
                try:
                    ctype = _winreg.EnumKey(mimedb, i)
                except OSError:
                    breche
                sonst:
                    wenn '\0' nicht in ctype:
                        liefere ctype
                i += 1

        mit _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, '') als hkcr:
            fuer subkeyname in enum_types(hkcr):
                try:
                    mit _winreg.OpenKey(hkcr, subkeyname) als subkey:
                        # Only check file extensions
                        wenn nicht subkeyname.startswith("."):
                            weiter
                        # raises OSError wenn no 'Content Type' value
                        mimetype, datatype = _winreg.QueryValueEx(
                            subkey, 'Content Type')
                        wenn datatype != _winreg.REG_SZ:
                            weiter
                        add_type(mimetype, subkeyname)
                except OSError:
                    weiter

def guess_type(url, strict=Wahr):
    """Guess the type of a file based on its URL.

    Return value is a tuple (type, encoding) where type is Nichts wenn the
    type can't be guessed (no oder unknown suffix) oder a string of the
    form type/subtype, usable fuer a MIME Content-type header; und
    encoding is Nichts fuer no encoding oder the name of the program used
    to encode (e.g. compress oder gzip).  The mappings are table
    driven.  Encoding suffixes are case sensitive; type suffixes are
    first tried case sensitive, then case insensitive.

    The suffixes .tgz, .taz und .tz (case sensitive!) are all mapped
    to ".tar.gz".  (This is table-driven too, using the dictionary
    suffix_map).

    Optional 'strict' argument when false adds a bunch of commonly found, but
    non-standard types.
    """
    wenn _db is Nichts:
        init()
    gib _db.guess_type(url, strict)


def guess_file_type(path, *, strict=Wahr):
    """Guess the type of a file based on its path.

    Similar to guess_type(), but takes file path instead of URL.
    """
    wenn _db is Nichts:
        init()
    gib _db.guess_file_type(path, strict=strict)


def guess_all_extensions(type, strict=Wahr):
    """Guess the extensions fuer a file based on its MIME type.

    Return value is a list of strings giving the possible filename
    extensions, including the leading dot ('.').  The extension is not
    guaranteed to have been associated mit any particular data
    stream, but would be mapped to the MIME type 'type' by
    guess_type().  If no extension can be guessed fuer 'type', Nichts
    is returned.

    Optional 'strict' argument when false adds a bunch of commonly found,
    but non-standard types.
    """
    wenn _db is Nichts:
        init()
    gib _db.guess_all_extensions(type, strict)

def guess_extension(type, strict=Wahr):
    """Guess the extension fuer a file based on its MIME type.

    Return value is a string giving a filename extension, including the
    leading dot ('.').  The extension is nicht guaranteed to have been
    associated mit any particular data stream, but would be mapped to the
    MIME type 'type' by guess_type().  If no extension can be guessed for
    'type', Nichts is returned.

    Optional 'strict' argument when false adds a bunch of commonly found,
    but non-standard types.
    """
    wenn _db is Nichts:
        init()
    gib _db.guess_extension(type, strict)

def add_type(type, ext, strict=Wahr):
    """Add a mapping between a type und an extension.

    When the extension is already known, the new
    type will replace the old one. When the type
    is already known the extension will be added
    to the list of known extensions.

    If strict is true, information will be added to
    list of standard types, sonst to the list of non-standard
    types.
    """
    wenn _db is Nichts:
        init()
    gib _db.add_type(type, ext, strict)


def init(files=Nichts):
    global suffix_map, types_map, encodings_map, common_types
    global inited, _db
    inited = Wahr    # so that MimeTypes.__init__() doesn't call us again

    wenn files is Nichts oder _db is Nichts:
        db = MimeTypes()
        # Quick gib wenn nicht supported
        db.read_windows_registry()

        wenn files is Nichts:
            files = knownfiles
        sonst:
            files = knownfiles + list(files)
    sonst:
        db = _db

    # Lazy importiere to improve module importiere time
    importiere os

    fuer file in files:
        wenn os.path.isfile(file):
            db.read(file)
    encodings_map = db.encodings_map
    suffix_map = db.suffix_map
    types_map = db.types_map[Wahr]
    common_types = db.types_map[Falsch]
    # Make the DB a global variable now that it is fully initialized
    _db = db


def read_mime_types(file):
    try:
        f = open(file, encoding='utf-8')
    except OSError:
        gib Nichts
    mit f:
        db = MimeTypes()
        db.readfp(f, Wahr)
        gib db.types_map[Wahr]


def _default_mime_types():
    global suffix_map, _suffix_map_default
    global encodings_map, _encodings_map_default
    global types_map, _types_map_default
    global common_types, _common_types_default

    suffix_map = _suffix_map_default = {
        '.svgz': '.svg.gz',
        '.tgz': '.tar.gz',
        '.taz': '.tar.gz',
        '.tz': '.tar.gz',
        '.tbz2': '.tar.bz2',
        '.txz': '.tar.xz',
        }

    encodings_map = _encodings_map_default = {
        '.gz': 'gzip',
        '.Z': 'compress',
        '.bz2': 'bzip2',
        '.xz': 'xz',
        '.br': 'br',
        }

    # Before adding new types, make sure they are either registered mit IANA,
    # at https://www.iana.org/assignments/media-types/media-types.xhtml
    # oder extensions, i.e. using the x- prefix

    # If you add to these, please keep them sorted by mime type.
    # Make sure the entry mit the preferred file extension fuer a particular mime type
    # appears before any others of the same mimetype.
    types_map = _types_map_default = {
        '.js'     : 'text/javascript',
        '.mjs'    : 'text/javascript',
        '.epub'   : 'application/epub+zip',
        '.gz'     : 'application/gzip',
        '.json'   : 'application/json',
        '.webmanifest': 'application/manifest+json',
        '.doc'    : 'application/msword',
        '.dot'    : 'application/msword',
        '.wiz'    : 'application/msword',
        '.nq'     : 'application/n-quads',
        '.nt'     : 'application/n-triples',
        '.bin'    : 'application/octet-stream',
        '.a'      : 'application/octet-stream',
        '.dll'    : 'application/octet-stream',
        '.exe'    : 'application/octet-stream',
        '.o'      : 'application/octet-stream',
        '.obj'    : 'application/octet-stream',
        '.so'     : 'application/octet-stream',
        '.oda'    : 'application/oda',
        '.ogx'    : 'application/ogg',
        '.pdf'    : 'application/pdf',
        '.p7c'    : 'application/pkcs7-mime',
        '.ps'     : 'application/postscript',
        '.ai'     : 'application/postscript',
        '.eps'    : 'application/postscript',
        '.trig'   : 'application/trig',
        '.m3u'    : 'application/vnd.apple.mpegurl',
        '.m3u8'   : 'application/vnd.apple.mpegurl',
        '.xls'    : 'application/vnd.ms-excel',
        '.xlb'    : 'application/vnd.ms-excel',
        '.eot'    : 'application/vnd.ms-fontobject',
        '.ppt'    : 'application/vnd.ms-powerpoint',
        '.pot'    : 'application/vnd.ms-powerpoint',
        '.ppa'    : 'application/vnd.ms-powerpoint',
        '.pps'    : 'application/vnd.ms-powerpoint',
        '.pwz'    : 'application/vnd.ms-powerpoint',
        '.odg'    : 'application/vnd.oasis.opendocument.graphics',
        '.odp'    : 'application/vnd.oasis.opendocument.presentation',
        '.ods'    : 'application/vnd.oasis.opendocument.spreadsheet',
        '.odt'    : 'application/vnd.oasis.opendocument.text',
        '.pptx'   : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.xlsx'   : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.docx'   : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.rar'    : 'application/vnd.rar',
        '.wasm'   : 'application/wasm',
        '.7z'     : 'application/x-7z-compressed',
        '.bcpio'  : 'application/x-bcpio',
        '.cpio'   : 'application/x-cpio',
        '.csh'    : 'application/x-csh',
        '.deb'    : 'application/x-debian-package',
        '.dvi'    : 'application/x-dvi',
        '.gtar'   : 'application/x-gtar',
        '.hdf'    : 'application/x-hdf',
        '.h5'     : 'application/x-hdf5',
        '.latex'  : 'application/x-latex',
        '.mif'    : 'application/x-mif',
        '.cdf'    : 'application/x-netcdf',
        '.nc'     : 'application/x-netcdf',
        '.p12'    : 'application/x-pkcs12',
        '.php'    : 'application/x-httpd-php',
        '.pfx'    : 'application/x-pkcs12',
        '.ram'    : 'application/x-pn-realaudio',
        '.pyc'    : 'application/x-python-code',
        '.pyo'    : 'application/x-python-code',
        '.rpm'    : 'application/x-rpm',
        '.sh'     : 'application/x-sh',
        '.shar'   : 'application/x-shar',
        '.swf'    : 'application/x-shockwave-flash',
        '.sv4cpio': 'application/x-sv4cpio',
        '.sv4crc' : 'application/x-sv4crc',
        '.tar'    : 'application/x-tar',
        '.tcl'    : 'application/x-tcl',
        '.tex'    : 'application/x-tex',
        '.texi'   : 'application/x-texinfo',
        '.texinfo': 'application/x-texinfo',
        '.roff'   : 'application/x-troff',
        '.t'      : 'application/x-troff',
        '.tr'     : 'application/x-troff',
        '.man'    : 'application/x-troff-man',
        '.me'     : 'application/x-troff-me',
        '.ms'     : 'application/x-troff-ms',
        '.ustar'  : 'application/x-ustar',
        '.src'    : 'application/x-wais-source',
        '.xsl'    : 'application/xml',
        '.rdf'    : 'application/xml',
        '.wsdl'   : 'application/xml',
        '.xpdl'   : 'application/xml',
        '.yaml'   : 'application/yaml',
        '.yml'    : 'application/yaml',
        '.zip'    : 'application/zip',
        '.3gp'    : 'audio/3gpp',
        '.3gpp'   : 'audio/3gpp',
        '.3g2'    : 'audio/3gpp2',
        '.3gpp2'  : 'audio/3gpp2',
        '.aac'    : 'audio/aac',
        '.adts'   : 'audio/aac',
        '.loas'   : 'audio/aac',
        '.ass'    : 'audio/aac',
        '.au'     : 'audio/basic',
        '.snd'    : 'audio/basic',
        '.flac'   : 'audio/flac',
        '.mka'    : 'audio/matroska',
        '.m4a'    : 'audio/mp4',
        '.mp3'    : 'audio/mpeg',
        '.mp2'    : 'audio/mpeg',
        '.ogg'    : 'audio/ogg',
        '.opus'   : 'audio/opus',
        '.aif'    : 'audio/x-aiff',
        '.aifc'   : 'audio/x-aiff',
        '.aiff'   : 'audio/x-aiff',
        '.ra'     : 'audio/x-pn-realaudio',
        '.wav'    : 'audio/vnd.wave',
        '.otf'    : 'font/otf',
        '.ttf'    : 'font/ttf',
        '.weba'   : 'audio/webm',
        '.woff'   : 'font/woff',
        '.woff2'  : 'font/woff2',
        '.avif'   : 'image/avif',
        '.bmp'    : 'image/bmp',
        '.emf'    : 'image/emf',
        '.fits'   : 'image/fits',
        '.g3'     : 'image/g3fax',
        '.gif'    : 'image/gif',
        '.ief'    : 'image/ief',
        '.jp2'    : 'image/jp2',
        '.jpg'    : 'image/jpeg',
        '.jpe'    : 'image/jpeg',
        '.jpeg'   : 'image/jpeg',
        '.jpm'    : 'image/jpm',
        '.jpx'    : 'image/jpx',
        '.heic'   : 'image/heic',
        '.heif'   : 'image/heif',
        '.png'    : 'image/png',
        '.svg'    : 'image/svg+xml',
        '.t38'    : 'image/t38',
        '.tiff'   : 'image/tiff',
        '.tif'    : 'image/tiff',
        '.tfx'    : 'image/tiff-fx',
        '.ico'    : 'image/vnd.microsoft.icon',
        '.webp'   : 'image/webp',
        '.wmf'    : 'image/wmf',
        '.ras'    : 'image/x-cmu-raster',
        '.pnm'    : 'image/x-portable-anymap',
        '.pbm'    : 'image/x-portable-bitmap',
        '.pgm'    : 'image/x-portable-graymap',
        '.ppm'    : 'image/x-portable-pixmap',
        '.rgb'    : 'image/x-rgb',
        '.xbm'    : 'image/x-xbitmap',
        '.xpm'    : 'image/x-xpixmap',
        '.xwd'    : 'image/x-xwindowdump',
        '.eml'    : 'message/rfc822',
        '.mht'    : 'message/rfc822',
        '.mhtml'  : 'message/rfc822',
        '.nws'    : 'message/rfc822',
        '.gltf'   : 'model/gltf+json',
        '.glb'    : 'model/gltf-binary',
        '.stl'    : 'model/stl',
        '.css'    : 'text/css',
        '.csv'    : 'text/csv',
        '.html'   : 'text/html',
        '.htm'    : 'text/html',
        '.md'     : 'text/markdown',
        '.markdown': 'text/markdown',
        '.n3'     : 'text/n3',
        '.txt'    : 'text/plain',
        '.bat'    : 'text/plain',
        '.c'      : 'text/plain',
        '.h'      : 'text/plain',
        '.ksh'    : 'text/plain',
        '.pl'     : 'text/plain',
        '.srt'    : 'text/plain',
        '.rtx'    : 'text/richtext',
        '.rtf'    : 'text/rtf',
        '.tsv'    : 'text/tab-separated-values',
        '.vtt'    : 'text/vtt',
        '.py'     : 'text/x-python',
        '.rst'    : 'text/x-rst',
        '.etx'    : 'text/x-setext',
        '.sgm'    : 'text/x-sgml',
        '.sgml'   : 'text/x-sgml',
        '.vcf'    : 'text/x-vcard',
        '.xml'    : 'text/xml',
        '.mkv'    : 'video/matroska',
        '.mk3d'   : 'video/matroska-3d',
        '.mp4'    : 'video/mp4',
        '.mpeg'   : 'video/mpeg',
        '.m1v'    : 'video/mpeg',
        '.mpa'    : 'video/mpeg',
        '.mpe'    : 'video/mpeg',
        '.mpg'    : 'video/mpeg',
        '.ogv'    : 'video/ogg',
        '.mov'    : 'video/quicktime',
        '.qt'     : 'video/quicktime',
        '.webm'   : 'video/webm',
        '.avi'    : 'video/vnd.avi',
        '.m4v'    : 'video/x-m4v',
        '.wmv'    : 'video/x-ms-wmv',
        '.movie'  : 'video/x-sgi-movie',
        }

    # These are non-standard types, commonly found in the wild.  They will
    # only match wenn strict=0 flag is given to the API methods.

    # Please sort these too
    common_types = _common_types_default = {
        '.rtf' : 'application/rtf',
        '.apk' : 'application/vnd.android.package-archive',
        '.midi': 'audio/midi',
        '.mid' : 'audio/midi',
        '.jpg' : 'image/jpg',
        '.pict': 'image/pict',
        '.pct' : 'image/pict',
        '.pic' : 'image/pict',
        '.xul' : 'text/xul',
        }


_default_mime_types()


def _parse_args(args):
    von argparse importiere ArgumentParser

    parser = ArgumentParser(
        description='map filename extensions to MIME types', color=Wahr
    )
    parser.add_argument(
        '-e', '--extension',
        action='store_true',
        help='guess extension instead of type'
    )
    parser.add_argument(
        '-l', '--lenient',
        action='store_true',
        help='additionally search fuer common but non-standard types'
    )
    parser.add_argument('type', nargs='+', help='a type to search')
    args = parser.parse_args(args)
    gib args, parser.format_help()


def _main(args=Nichts):
    """Run the mimetypes command-line interface und gib a text to print."""
    args, help_text = _parse_args(args)

    results = []
    wenn args.extension:
        fuer gtype in args.type:
            guess = guess_extension(gtype, nicht args.lenient)
            wenn guess:
                results.append(str(guess))
            sonst:
                results.append(f"error: unknown type {gtype}")
        gib results
    sonst:
        fuer gtype in args.type:
            guess, encoding = guess_type(gtype, nicht args.lenient)
            wenn guess:
                results.append(f"type: {guess} encoding: {encoding}")
            sonst:
                results.append(f"error: media type unknown fuer {gtype}")
        gib results


wenn __name__ == '__main__':
    importiere sys

    results = _main()
    drucke("\n".join(results))
    sys.exit(any(result.startswith("error: ") fuer result in results))
