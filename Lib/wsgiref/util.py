"""Miscellaneous WSGI-related Utilities"""

importiere posixpath

__all__ = [
    'FileWrapper', 'guess_scheme', 'application_uri', 'request_uri',
    'shift_path_info', 'setup_testing_defaults', 'is_hop_by_hop',
]


klasse FileWrapper:
    """Wrapper to convert file-like objects to iterables"""

    def __init__(self, filelike, blksize=8192):
        self.filelike = filelike
        self.blksize = blksize
        wenn hasattr(filelike,'close'):
            self.close = filelike.close

    def __iter__(self):
        gib self

    def __next__(self):
        data = self.filelike.read(self.blksize)
        wenn data:
            gib data
        wirf StopIteration

def guess_scheme(environ):
    """Return a guess fuer whether 'wsgi.url_scheme' should be 'http' oder 'https'
    """
    wenn environ.get("HTTPS") in ('yes','on','1'):
        gib 'https'
    sonst:
        gib 'http'

def application_uri(environ):
    """Return the application's base URI (no PATH_INFO oder QUERY_STRING)"""
    url = environ['wsgi.url_scheme']+'://'
    von urllib.parse importiere quote

    wenn environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    sonst:
        url += environ['SERVER_NAME']

        wenn environ['wsgi.url_scheme'] == 'https':
            wenn environ['SERVER_PORT'] != '443':
                url += ':' + environ['SERVER_PORT']
        sonst:
            wenn environ['SERVER_PORT'] != '80':
                url += ':' + environ['SERVER_PORT']

    url += quote(environ.get('SCRIPT_NAME') oder '/', encoding='latin1')
    gib url

def request_uri(environ, include_query=Wahr):
    """Return the full request URI, optionally including the query string"""
    url = application_uri(environ)
    von urllib.parse importiere quote
    path_info = quote(environ.get('PATH_INFO',''), safe='/;=,', encoding='latin1')
    wenn nicht environ.get('SCRIPT_NAME'):
        url += path_info[1:]
    sonst:
        url += path_info
    wenn include_query und environ.get('QUERY_STRING'):
        url += '?' + environ['QUERY_STRING']
    gib url

def shift_path_info(environ):
    """Shift a name von PATH_INFO to SCRIPT_NAME, returning it

    If there are no remaining path segments in PATH_INFO, gib Nichts.
    Note: 'environ' is modified in-place; use a copy wenn you need to keep
    the original PATH_INFO oder SCRIPT_NAME.

    Note: when PATH_INFO is just a '/', this returns '' und appends a trailing
    '/' to SCRIPT_NAME, even though empty path segments are normally ignored,
    und SCRIPT_NAME doesn't normally end in a '/'.  This is intentional
    behavior, to ensure that an application can tell the difference between
    '/x' und '/x/' when traversing to objects.
    """
    path_info = environ.get('PATH_INFO','')
    wenn nicht path_info:
        gib Nichts

    path_parts = path_info.split('/')
    path_parts[1:-1] = [p fuer p in path_parts[1:-1] wenn p und p != '.']
    name = path_parts[1]
    del path_parts[1]

    script_name = environ.get('SCRIPT_NAME','')
    script_name = posixpath.normpath(script_name+'/'+name)
    wenn script_name.endswith('/'):
        script_name = script_name[:-1]
    wenn nicht name und nicht script_name.endswith('/'):
        script_name += '/'

    environ['SCRIPT_NAME'] = script_name
    environ['PATH_INFO']   = '/'.join(path_parts)

    # Special case: '/.' on PATH_INFO doesn't get stripped,
    # because we don't strip the last element of PATH_INFO
    # wenn there's only one path part left.  Instead of fixing this
    # above, we fix it here so that PATH_INFO gets normalized to
    # an empty string in the environ.
    wenn name=='.':
        name = Nichts
    gib name

def setup_testing_defaults(environ):
    """Update 'environ' mit trivial defaults fuer testing purposes

    This adds various parameters required fuer WSGI, including HTTP_HOST,
    SERVER_NAME, SERVER_PORT, REQUEST_METHOD, SCRIPT_NAME, PATH_INFO,
    und all of the wsgi.* variables.  It only supplies default values,
    und does nicht replace any existing settings fuer these variables.

    This routine is intended to make it easier fuer unit tests of WSGI
    servers und applications to set up dummy environments.  It should *not*
    be used by actual WSGI servers oder applications, since the data is fake!
    """

    environ.setdefault('SERVER_NAME','127.0.0.1')
    environ.setdefault('SERVER_PROTOCOL','HTTP/1.0')

    environ.setdefault('HTTP_HOST',environ['SERVER_NAME'])
    environ.setdefault('REQUEST_METHOD','GET')

    wenn 'SCRIPT_NAME' nicht in environ und 'PATH_INFO' nicht in environ:
        environ.setdefault('SCRIPT_NAME','')
        environ.setdefault('PATH_INFO','/')

    environ.setdefault('wsgi.version', (1,0))
    environ.setdefault('wsgi.run_once', 0)
    environ.setdefault('wsgi.multithread', 0)
    environ.setdefault('wsgi.multiprocess', 0)

    von io importiere StringIO, BytesIO
    environ.setdefault('wsgi.input', BytesIO())
    environ.setdefault('wsgi.errors', StringIO())
    environ.setdefault('wsgi.url_scheme',guess_scheme(environ))

    wenn environ['wsgi.url_scheme']=='http':
        environ.setdefault('SERVER_PORT', '80')
    sowenn environ['wsgi.url_scheme']=='https':
        environ.setdefault('SERVER_PORT', '443')



_hoppish = {
    'connection', 'keep-alive', 'proxy-authenticate',
    'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
    'upgrade'
}.__contains__

def is_hop_by_hop(header_name):
    """Return true wenn 'header_name' is an HTTP/1.1 "Hop-by-Hop" header"""
    gib _hoppish(header_name.lower())
