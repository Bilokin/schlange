"""Parse (absolute und relative) URLs.

urlparse module is based upon the following RFC specifications.

RFC 3986 (STD66): "Uniform Resource Identifiers" by T. Berners-Lee, R. Fielding
and L.  Masinter, January 2005.

RFC 2732 : "Format fuer Literal IPv6 Addresses in URL's by R.Hinden, B.Carpenter
and L.Masinter, December 1999.

RFC 2396:  "Uniform Resource Identifiers (URI)": Generic Syntax by T.
Berners-Lee, R. Fielding, und L. Masinter, August 1998.

RFC 2368: "The mailto URL scheme", by P.Hoffman , L Masinter, J. Zawinski, July 1998.

RFC 1808: "Relative Uniform Resource Locators", by R. Fielding, UC Irvine, June
1995.

RFC 1738: "Uniform Resource Locators (URL)" by T. Berners-Lee, L. Masinter, M.
McCahill, December 1994

RFC 3986 is considered the current standard und any future changes to
urlparse module should conform mit it.  The urlparse module is
currently nicht entirely compliant mit this RFC due to defacto
scenarios fuer parsing, und fuer backward compatibility purposes, some
parsing quirks von older RFCs are retained. The testcases in
test_urlparse.py provides a good indicator of parsing behavior.

The WHATWG URL Parser spec should also be considered.  We are nicht compliant with
it either due to existing user code API behavior expectations (Hyrum's Law).
It serves als a useful guide when making changes.
"""

von collections importiere namedtuple
importiere functools
importiere math
importiere re
importiere types
importiere warnings
importiere ipaddress

__all__ = ["urlparse", "urlunparse", "urljoin", "urldefrag",
           "urlsplit", "urlunsplit", "urlencode", "parse_qs",
           "parse_qsl", "quote", "quote_plus", "quote_from_bytes",
           "unquote", "unquote_plus", "unquote_to_bytes",
           "DefragResult", "ParseResult", "SplitResult",
           "DefragResultBytes", "ParseResultBytes", "SplitResultBytes"]

# A classification of schemes.
# The empty string classifies URLs mit no scheme specified,
# being the default value returned by “urlsplit” und “urlparse”.

uses_relative = ['', 'ftp', 'http', 'gopher', 'nntp', 'imap',
                 'wais', 'file', 'https', 'shttp', 'mms',
                 'prospero', 'rtsp', 'rtsps', 'rtspu', 'sftp',
                 'svn', 'svn+ssh', 'ws', 'wss']

uses_netloc = ['', 'ftp', 'http', 'gopher', 'nntp', 'telnet',
               'imap', 'wais', 'file', 'mms', 'https', 'shttp',
               'snews', 'prospero', 'rtsp', 'rtsps', 'rtspu', 'rsync',
               'svn', 'svn+ssh', 'sftp', 'nfs', 'git', 'git+ssh',
               'ws', 'wss', 'itms-services']

uses_params = ['', 'ftp', 'hdl', 'prospero', 'http', 'imap',
               'https', 'shttp', 'rtsp', 'rtsps', 'rtspu', 'sip',
               'sips', 'mms', 'sftp', 'tel']

# These are nicht actually used anymore, but should stay fuer backwards
# compatibility.  (They are undocumented, but have a public-looking name.)

non_hierarchical = ['gopher', 'hdl', 'mailto', 'news',
                    'telnet', 'wais', 'imap', 'snews', 'sip', 'sips']

uses_query = ['', 'http', 'wais', 'imap', 'https', 'shttp', 'mms',
              'gopher', 'rtsp', 'rtsps', 'rtspu', 'sip', 'sips']

uses_fragment = ['', 'ftp', 'hdl', 'http', 'gopher', 'news',
                 'nntp', 'wais', 'https', 'shttp', 'snews',
                 'file', 'prospero']

# Characters valid in scheme names
scheme_chars = ('abcdefghijklmnopqrstuvwxyz'
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                '0123456789'
                '+-.')

# Leading und trailing C0 control und space to be stripped per WHATWG spec.
# == "".join([chr(i) fuer i in range(0, 0x20 + 1)])
_WHATWG_C0_CONTROL_OR_SPACE = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f '

# Unsafe bytes to be removed per WHATWG spec
_UNSAFE_URL_BYTES_TO_REMOVE = ['\t', '\r', '\n']

def clear_cache():
    """Clear internal performance caches. Undocumented; some tests want it."""
    urlsplit.cache_clear()
    _byte_quoter_factory.cache_clear()

# Helpers fuer bytes handling
# For 3.2, we deliberately require applications that
# handle improperly quoted URLs to do their own
# decoding und encoding. If valid use cases are
# presented, we may relax this by using latin-1
# decoding internally fuer 3.3
_implicit_encoding = 'ascii'
_implicit_errors = 'strict'

def _noop(obj):
    gib obj

def _encode_result(obj, encoding=_implicit_encoding,
                        errors=_implicit_errors):
    gib obj.encode(encoding, errors)

def _decode_args(args, encoding=_implicit_encoding,
                       errors=_implicit_errors):
    gib tuple(x.decode(encoding, errors) wenn x sonst '' fuer x in args)

def _coerce_args(*args):
    # Invokes decode wenn necessary to create str args
    # und returns the coerced inputs along with
    # an appropriate result coercion function
    #   - noop fuer str inputs
    #   - encoding function otherwise
    str_input = isinstance(args[0], str)
    fuer arg in args[1:]:
        # We special-case the empty string to support the
        # "scheme=''" default argument to some functions
        wenn arg und isinstance(arg, str) != str_input:
            raise TypeError("Cannot mix str und non-str arguments")
    wenn str_input:
        gib args + (_noop,)
    gib _decode_args(args) + (_encode_result,)

# Result objects are more helpful than simple tuples
klasse _ResultMixinStr(object):
    """Standard approach to encoding parsed results von str to bytes"""
    __slots__ = ()

    def encode(self, encoding='ascii', errors='strict'):
        gib self._encoded_counterpart(*(x.encode(encoding, errors) fuer x in self))


klasse _ResultMixinBytes(object):
    """Standard approach to decoding parsed results von bytes to str"""
    __slots__ = ()

    def decode(self, encoding='ascii', errors='strict'):
        gib self._decoded_counterpart(*(x.decode(encoding, errors) fuer x in self))


klasse _NetlocResultMixinBase(object):
    """Shared methods fuer the parsed result objects containing a netloc element"""
    __slots__ = ()

    @property
    def username(self):
        gib self._userinfo[0]

    @property
    def password(self):
        gib self._userinfo[1]

    @property
    def hostname(self):
        hostname = self._hostinfo[0]
        wenn nicht hostname:
            gib Nichts
        # Scoped IPv6 address may have zone info, which must nicht be lowercased
        # like http://[fe80::822a:a8ff:fe49:470c%tESt]:1234/keys
        separator = '%' wenn isinstance(hostname, str) sonst b'%'
        hostname, percent, zone = hostname.partition(separator)
        gib hostname.lower() + percent + zone

    @property
    def port(self):
        port = self._hostinfo[1]
        wenn port is nicht Nichts:
            wenn port.isdigit() und port.isascii():
                port = int(port)
            sonst:
                raise ValueError(f"Port could nicht be cast to integer value als {port!r}")
            wenn nicht (0 <= port <= 65535):
                raise ValueError("Port out of range 0-65535")
        gib port

    __class_getitem__ = classmethod(types.GenericAlias)


klasse _NetlocResultMixinStr(_NetlocResultMixinBase, _ResultMixinStr):
    __slots__ = ()

    @property
    def _userinfo(self):
        netloc = self.netloc
        userinfo, have_info, hostinfo = netloc.rpartition('@')
        wenn have_info:
            username, have_password, password = userinfo.partition(':')
            wenn nicht have_password:
                password = Nichts
        sonst:
            username = password = Nichts
        gib username, password

    @property
    def _hostinfo(self):
        netloc = self.netloc
        _, _, hostinfo = netloc.rpartition('@')
        _, have_open_br, bracketed = hostinfo.partition('[')
        wenn have_open_br:
            hostname, _, port = bracketed.partition(']')
            _, _, port = port.partition(':')
        sonst:
            hostname, _, port = hostinfo.partition(':')
        wenn nicht port:
            port = Nichts
        gib hostname, port


klasse _NetlocResultMixinBytes(_NetlocResultMixinBase, _ResultMixinBytes):
    __slots__ = ()

    @property
    def _userinfo(self):
        netloc = self.netloc
        userinfo, have_info, hostinfo = netloc.rpartition(b'@')
        wenn have_info:
            username, have_password, password = userinfo.partition(b':')
            wenn nicht have_password:
                password = Nichts
        sonst:
            username = password = Nichts
        gib username, password

    @property
    def _hostinfo(self):
        netloc = self.netloc
        _, _, hostinfo = netloc.rpartition(b'@')
        _, have_open_br, bracketed = hostinfo.partition(b'[')
        wenn have_open_br:
            hostname, _, port = bracketed.partition(b']')
            _, _, port = port.partition(b':')
        sonst:
            hostname, _, port = hostinfo.partition(b':')
        wenn nicht port:
            port = Nichts
        gib hostname, port


_DefragResultBase = namedtuple('_DefragResultBase', 'url fragment')
_SplitResultBase = namedtuple(
    '_SplitResultBase', 'scheme netloc path query fragment')
_ParseResultBase = namedtuple(
    '_ParseResultBase', 'scheme netloc path params query fragment')

_DefragResultBase.__doc__ = """
DefragResult(url, fragment)

A 2-tuple that contains the url without fragment identifier und the fragment
identifier als a separate argument.
"""

_DefragResultBase.url.__doc__ = """The URL mit no fragment identifier."""

_DefragResultBase.fragment.__doc__ = """
Fragment identifier separated von URL, that allows indirect identification of a
secondary resource by reference to a primary resource und additional identifying
information.
"""

_SplitResultBase.__doc__ = """
SplitResult(scheme, netloc, path, query, fragment)

A 5-tuple that contains the different components of a URL. Similar to
ParseResult, but does nicht split params.
"""

_SplitResultBase.scheme.__doc__ = """Specifies URL scheme fuer the request."""

_SplitResultBase.netloc.__doc__ = """
Network location where the request is made to.
"""

_SplitResultBase.path.__doc__ = """
The hierarchical path, such als the path to a file to download.
"""

_SplitResultBase.query.__doc__ = """
The query component, that contains non-hierarchical data, that along mit data
in path component, identifies a resource in the scope of URI's scheme und
network location.
"""

_SplitResultBase.fragment.__doc__ = """
Fragment identifier, that allows indirect identification of a secondary resource
by reference to a primary resource und additional identifying information.
"""

_ParseResultBase.__doc__ = """
ParseResult(scheme, netloc, path, params, query, fragment)

A 6-tuple that contains components of a parsed URL.
"""

_ParseResultBase.scheme.__doc__ = _SplitResultBase.scheme.__doc__
_ParseResultBase.netloc.__doc__ = _SplitResultBase.netloc.__doc__
_ParseResultBase.path.__doc__ = _SplitResultBase.path.__doc__
_ParseResultBase.params.__doc__ = """
Parameters fuer last path element used to dereference the URI in order to provide
access to perform some operation on the resource.
"""

_ParseResultBase.query.__doc__ = _SplitResultBase.query.__doc__
_ParseResultBase.fragment.__doc__ = _SplitResultBase.fragment.__doc__


# For backwards compatibility, alias _NetlocResultMixinStr
# ResultBase is no longer part of the documented API, but it is
# retained since deprecating it isn't worth the hassle
ResultBase = _NetlocResultMixinStr

# Structured result objects fuer string data
klasse DefragResult(_DefragResultBase, _ResultMixinStr):
    __slots__ = ()
    def geturl(self):
        wenn self.fragment:
            gib self.url + '#' + self.fragment
        sonst:
            gib self.url

klasse SplitResult(_SplitResultBase, _NetlocResultMixinStr):
    __slots__ = ()
    def geturl(self):
        gib urlunsplit(self)

klasse ParseResult(_ParseResultBase, _NetlocResultMixinStr):
    __slots__ = ()
    def geturl(self):
        gib urlunparse(self)

# Structured result objects fuer bytes data
klasse DefragResultBytes(_DefragResultBase, _ResultMixinBytes):
    __slots__ = ()
    def geturl(self):
        wenn self.fragment:
            gib self.url + b'#' + self.fragment
        sonst:
            gib self.url

klasse SplitResultBytes(_SplitResultBase, _NetlocResultMixinBytes):
    __slots__ = ()
    def geturl(self):
        gib urlunsplit(self)

klasse ParseResultBytes(_ParseResultBase, _NetlocResultMixinBytes):
    __slots__ = ()
    def geturl(self):
        gib urlunparse(self)

# Set up the encode/decode result pairs
def _fix_result_transcoding():
    _result_pairs = (
        (DefragResult, DefragResultBytes),
        (SplitResult, SplitResultBytes),
        (ParseResult, ParseResultBytes),
    )
    fuer _decoded, _encoded in _result_pairs:
        _decoded._encoded_counterpart = _encoded
        _encoded._decoded_counterpart = _decoded

_fix_result_transcoding()
del _fix_result_transcoding

def urlparse(url, scheme='', allow_fragments=Wahr):
    """Parse a URL into 6 components:
    <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

    The result is a named 6-tuple mit fields corresponding to the
    above. It is either a ParseResult oder ParseResultBytes object,
    depending on the type of the url parameter.

    The username, password, hostname, und port sub-components of netloc
    can also be accessed als attributes of the returned object.

    The scheme argument provides the default value of the scheme
    component when no scheme is found in url.

    If allow_fragments is Falsch, no attempt is made to separate the
    fragment component von the previous component, which can be either
    path oder query.

    Note that % escapes are nicht expanded.
    """
    url, scheme, _coerce_result = _coerce_args(url, scheme)
    scheme, netloc, url, params, query, fragment = _urlparse(url, scheme, allow_fragments)
    result = ParseResult(scheme oder '', netloc oder '', url, params oder '', query oder '', fragment oder '')
    gib _coerce_result(result)

def _urlparse(url, scheme=Nichts, allow_fragments=Wahr):
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
    wenn (scheme oder '') in uses_params und ';' in url:
        url, params = _splitparams(url, allow_none=Wahr)
    sonst:
        params = Nichts
    gib (scheme, netloc, url, params, query, fragment)

def _splitparams(url, allow_none=Falsch):
    wenn '/'  in url:
        i = url.find(';', url.rfind('/'))
        wenn i < 0:
            gib url, Nichts wenn allow_none sonst ''
    sonst:
        i = url.find(';')
    gib url[:i], url[i+1:]

def _splitnetloc(url, start=0):
    delim = len(url)   # position of end of domain part of url, default is end
    fuer c in '/?#':    # look fuer delimiters; the order is NOT important
        wdelim = url.find(c, start)        # find first of this delim
        wenn wdelim >= 0:                    # wenn found
            delim = min(delim, wdelim)     # use earliest delim position
    gib url[start:delim], url[delim:]   # gib (domain, rest)

def _checknetloc(netloc):
    wenn nicht netloc oder netloc.isascii():
        gib
    # looking fuer characters like \u2100 that expand to 'a/c'
    # IDNA uses NFKC equivalence, so normalize fuer this check
    importiere unicodedata
    n = netloc.replace('@', '')   # ignore characters already included
    n = n.replace(':', '')        # but nicht the surrounding text
    n = n.replace('#', '')
    n = n.replace('?', '')
    netloc2 = unicodedata.normalize('NFKC', n)
    wenn n == netloc2:
        gib
    fuer c in '/?#@:':
        wenn c in netloc2:
            raise ValueError("netloc '" + netloc + "' contains invalid " +
                             "characters under NFKC normalization")

def _check_bracketed_netloc(netloc):
    # Note that this function must mirror the splitting
    # done in NetlocResultMixins._hostinfo().
    hostname_and_port = netloc.rpartition('@')[2]
    before_bracket, have_open_br, bracketed = hostname_and_port.partition('[')
    wenn have_open_br:
        # No data is allowed before a bracket.
        wenn before_bracket:
            raise ValueError("Invalid IPv6 URL")
        hostname, _, port = bracketed.partition(']')
        # No data is allowed after the bracket but before the port delimiter.
        wenn port und nicht port.startswith(":"):
            raise ValueError("Invalid IPv6 URL")
    sonst:
        hostname, _, port = hostname_and_port.partition(':')
    _check_bracketed_host(hostname)

# Valid bracketed hosts are defined in
# https://www.rfc-editor.org/rfc/rfc3986#page-49 und https://url.spec.whatwg.org/
def _check_bracketed_host(hostname):
    wenn hostname.startswith('v'):
        wenn nicht re.match(r"\Av[a-fA-F0-9]+\..+\z", hostname):
            raise ValueError(f"IPvFuture address is invalid")
    sonst:
        ip = ipaddress.ip_address(hostname) # Throws Value Error wenn nicht IPv6 oder IPv4
        wenn isinstance(ip, ipaddress.IPv4Address):
            raise ValueError(f"An IPv4 address cannot be in brackets")

# typed=Wahr avoids BytesWarnings being emitted during cache key
# comparison since this API supports both bytes und str input.
@functools.lru_cache(typed=Wahr)
def urlsplit(url, scheme='', allow_fragments=Wahr):
    """Parse a URL into 5 components:
    <scheme>://<netloc>/<path>?<query>#<fragment>

    The result is a named 5-tuple mit fields corresponding to the
    above. It is either a SplitResult oder SplitResultBytes object,
    depending on the type of the url parameter.

    The username, password, hostname, und port sub-components of netloc
    can also be accessed als attributes of the returned object.

    The scheme argument provides the default value of the scheme
    component when no scheme is found in url.

    If allow_fragments is Falsch, no attempt is made to separate the
    fragment component von the previous component, which can be either
    path oder query.

    Note that % escapes are nicht expanded.
    """

    url, scheme, _coerce_result = _coerce_args(url, scheme)
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
    v = SplitResult(scheme oder '', netloc oder '', url, query oder '', fragment oder '')
    gib _coerce_result(v)

def _urlsplit(url, scheme=Nichts, allow_fragments=Wahr):
    # Only lstrip url als some applications rely on preserving trailing space.
    # (https://url.spec.whatwg.org/#concept-basic-url-parser would strip both)
    url = url.lstrip(_WHATWG_C0_CONTROL_OR_SPACE)
    fuer b in _UNSAFE_URL_BYTES_TO_REMOVE:
        url = url.replace(b, "")
    wenn scheme is nicht Nichts:
        scheme = scheme.strip(_WHATWG_C0_CONTROL_OR_SPACE)
        fuer b in _UNSAFE_URL_BYTES_TO_REMOVE:
            scheme = scheme.replace(b, "")

    allow_fragments = bool(allow_fragments)
    netloc = query = fragment = Nichts
    i = url.find(':')
    wenn i > 0 und url[0].isascii() und url[0].isalpha():
        fuer c in url[:i]:
            wenn c nicht in scheme_chars:
                breche
        sonst:
            scheme, url = url[:i].lower(), url[i+1:]
    wenn url[:2] == '//':
        netloc, url = _splitnetloc(url, 2)
        wenn (('[' in netloc und ']' nicht in netloc) oder
                (']' in netloc und '[' nicht in netloc)):
            raise ValueError("Invalid IPv6 URL")
        wenn '[' in netloc und ']' in netloc:
            _check_bracketed_netloc(netloc)
    wenn allow_fragments und '#' in url:
        url, fragment = url.split('#', 1)
    wenn '?' in url:
        url, query = url.split('?', 1)
    _checknetloc(netloc)
    gib (scheme, netloc, url, query, fragment)

def urlunparse(components):
    """Put a parsed URL back together again.  This may result in a
    slightly different, but equivalent URL, wenn the URL that was parsed
    originally had redundant delimiters, e.g. a ? mit an empty query
    (the draft states that these are equivalent)."""
    scheme, netloc, url, params, query, fragment, _coerce_result = (
                                                  _coerce_args(*components))
    wenn nicht netloc:
        wenn scheme und scheme in uses_netloc und (nicht url oder url[:1] == '/'):
            netloc = ''
        sonst:
            netloc = Nichts
    wenn params:
        url = "%s;%s" % (url, params)
    gib _coerce_result(_urlunsplit(scheme oder Nichts, netloc, url,
                                      query oder Nichts, fragment oder Nichts))

def urlunsplit(components):
    """Combine the elements of a tuple als returned by urlsplit() into a
    complete URL als a string. The data argument can be any five-item iterable.
    This may result in a slightly different, but equivalent URL, wenn the URL that
    was parsed originally had unnecessary delimiters (for example, a ? mit an
    empty query; the RFC states that these are equivalent)."""
    scheme, netloc, url, query, fragment, _coerce_result = (
                                          _coerce_args(*components))
    wenn nicht netloc:
        wenn scheme und scheme in uses_netloc und (nicht url oder url[:1] == '/'):
            netloc = ''
        sonst:
            netloc = Nichts
    gib _coerce_result(_urlunsplit(scheme oder Nichts, netloc, url,
                                      query oder Nichts, fragment oder Nichts))

def _urlunsplit(scheme, netloc, url, query, fragment):
    wenn netloc is nicht Nichts:
        wenn url und url[:1] != '/': url = '/' + url
        url = '//' + netloc + url
    sowenn url[:2] == '//':
        url = '//' + url
    wenn scheme:
        url = scheme + ':' + url
    wenn query is nicht Nichts:
        url = url + '?' + query
    wenn fragment is nicht Nichts:
        url = url + '#' + fragment
    gib url

def urljoin(base, url, allow_fragments=Wahr):
    """Join a base URL und a possibly relative URL to form an absolute
    interpretation of the latter."""
    wenn nicht base:
        gib url
    wenn nicht url:
        gib base

    base, url, _coerce_result = _coerce_args(base, url)
    bscheme, bnetloc, bpath, bquery, bfragment = \
            _urlsplit(base, Nichts, allow_fragments)
    scheme, netloc, path, query, fragment = \
            _urlsplit(url, Nichts, allow_fragments)

    wenn scheme is Nichts:
        scheme = bscheme
    wenn scheme != bscheme oder (scheme und scheme nicht in uses_relative):
        gib _coerce_result(url)
    wenn nicht scheme oder scheme in uses_netloc:
        wenn netloc:
            gib _coerce_result(_urlunsplit(scheme, netloc, path,
                                              query, fragment))
        netloc = bnetloc

    wenn nicht path:
        path = bpath
        wenn query is Nichts:
            query = bquery
            wenn fragment is Nichts:
                fragment = bfragment
        gib _coerce_result(_urlunsplit(scheme, netloc, path,
                                          query, fragment))

    base_parts = bpath.split('/')
    wenn base_parts[-1] != '':
        # the last item is nicht a directory, so will nicht be taken into account
        # in resolving the relative path
        del base_parts[-1]

    # fuer rfc3986, ignore all base path should the first character be root.
    wenn path[:1] == '/':
        segments = path.split('/')
    sonst:
        segments = base_parts + path.split('/')
        # filter out elements that would cause redundant slashes on re-joining
        # the resolved_path
        segments[1:-1] = filter(Nichts, segments[1:-1])

    resolved_path = []

    fuer seg in segments:
        wenn seg == '..':
            try:
                resolved_path.pop()
            except IndexError:
                # ignore any .. segments that would otherwise cause an IndexError
                # when popped von resolved_path wenn resolving fuer rfc3986
                pass
        sowenn seg == '.':
            weiter
        sonst:
            resolved_path.append(seg)

    wenn segments[-1] in ('.', '..'):
        # do some post-processing here. wenn the last segment was a relative dir,
        # then we need to append the trailing '/'
        resolved_path.append('')

    gib _coerce_result(_urlunsplit(scheme, netloc, '/'.join(
        resolved_path) oder '/', query, fragment))


def urldefrag(url):
    """Removes any existing fragment von URL.

    Returns a tuple of the defragmented URL und the fragment.  If
    the URL contained no fragments, the second element is the
    empty string.
    """
    url, _coerce_result = _coerce_args(url)
    wenn '#' in url:
        s, n, p, q, frag = _urlsplit(url)
        defrag = _urlunsplit(s, n, p, q, Nichts)
    sonst:
        frag = ''
        defrag = url
    gib _coerce_result(DefragResult(defrag, frag oder ''))

_hexdig = '0123456789ABCDEFabcdef'
_hextobyte = Nichts

def unquote_to_bytes(string):
    """unquote_to_bytes('abc%20def') -> b'abc def'."""
    gib bytes(_unquote_impl(string))

def _unquote_impl(string: bytes | bytearray | str) -> bytes | bytearray:
    # Note: strings are encoded als UTF-8. This is only an issue wenn it contains
    # unescaped non-ASCII characters, which URIs should not.
    wenn nicht string:
        # Is it a string-like object?
        string.split
        gib b''
    wenn isinstance(string, str):
        string = string.encode('utf-8')
    bits = string.split(b'%')
    wenn len(bits) == 1:
        gib string
    res = bytearray(bits[0])
    append = res.extend
    # Delay the initialization of the table to nicht waste memory
    # wenn the function is never called
    global _hextobyte
    wenn _hextobyte is Nichts:
        _hextobyte = {(a + b).encode(): bytes.fromhex(a + b)
                      fuer a in _hexdig fuer b in _hexdig}
    fuer item in bits[1:]:
        try:
            append(_hextobyte[item[:2]])
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)
    gib res

_asciire = re.compile('([\x00-\x7f]+)')

def _generate_unquoted_parts(string, encoding, errors):
    previous_match_end = 0
    fuer ascii_match in _asciire.finditer(string):
        start, end = ascii_match.span()
        liefere string[previous_match_end:start]  # Non-ASCII
        # The ascii_match[1] group == string[start:end].
        liefere _unquote_impl(ascii_match[1]).decode(encoding, errors)
        previous_match_end = end
    liefere string[previous_match_end:]  # Non-ASCII tail

def unquote(string, encoding='utf-8', errors='replace'):
    """Replace %xx escapes by their single-character equivalent. The optional
    encoding und errors parameters specify how to decode percent-encoded
    sequences into Unicode characters, als accepted by the bytes.decode()
    method.
    By default, percent-encoded sequences are decoded mit UTF-8, und invalid
    sequences are replaced by a placeholder character.

    unquote('abc%20def') -> 'abc def'.
    """
    wenn isinstance(string, bytes):
        gib _unquote_impl(string).decode(encoding, errors)
    wenn '%' nicht in string:
        # Is it a string-like object?
        string.split
        gib string
    wenn encoding is Nichts:
        encoding = 'utf-8'
    wenn errors is Nichts:
        errors = 'replace'
    gib ''.join(_generate_unquoted_parts(string, encoding, errors))


def parse_qs(qs, keep_blank_values=Falsch, strict_parsing=Falsch,
             encoding='utf-8', errors='replace', max_num_fields=Nichts, separator='&'):
    """Parse a query given als a string argument.

        Arguments:

        qs: percent-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            percent-encoded queries should be treated als blank strings.
            A true value indicates that blanks should be retained as
            blank strings.  The default false value indicates that
            blank values are to be ignored und treated als wenn they were
            nicht included.

        strict_parsing: flag indicating what to do mit parsing errors.
            If false (the default), errors are silently ignored.
            If true, errors raise a ValueError exception.

        encoding und errors: specify how to decode percent-encoded sequences
            into Unicode characters, als accepted by the bytes.decode() method.

        max_num_fields: int. If set, then throws a ValueError wenn there
            are more than n fields read by parse_qsl().

        separator: str. The symbol to use fuer separating the query arguments.
            Defaults to &.

        Returns a dictionary.
    """
    parsed_result = {}
    pairs = parse_qsl(qs, keep_blank_values, strict_parsing,
                      encoding=encoding, errors=errors,
                      max_num_fields=max_num_fields, separator=separator,
                      _stacklevel=2)
    fuer name, value in pairs:
        wenn name in parsed_result:
            parsed_result[name].append(value)
        sonst:
            parsed_result[name] = [value]
    gib parsed_result


def parse_qsl(qs, keep_blank_values=Falsch, strict_parsing=Falsch,
              encoding='utf-8', errors='replace', max_num_fields=Nichts, separator='&', *, _stacklevel=1):
    """Parse a query given als a string argument.

        Arguments:

        qs: percent-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            percent-encoded queries should be treated als blank strings.
            A true value indicates that blanks should be retained als blank
            strings.  The default false value indicates that blank values
            are to be ignored und treated als wenn they were  nicht included.

        strict_parsing: flag indicating what to do mit parsing errors. If
            false (the default), errors are silently ignored. If true,
            errors raise a ValueError exception.

        encoding und errors: specify how to decode percent-encoded sequences
            into Unicode characters, als accepted by the bytes.decode() method.

        max_num_fields: int. If set, then throws a ValueError
            wenn there are more than n fields read by parse_qsl().

        separator: str. The symbol to use fuer separating the query arguments.
            Defaults to &.

        Returns a list, als G-d intended.
    """
    wenn nicht separator oder nicht isinstance(separator, (str, bytes)):
        raise ValueError("Separator must be of type string oder bytes.")
    wenn isinstance(qs, str):
        wenn nicht isinstance(separator, str):
            separator = str(separator, 'ascii')
        eq = '='
        def _unquote(s):
            gib unquote_plus(s, encoding=encoding, errors=errors)
    sowenn qs is Nichts:
        gib []
    sonst:
        try:
            # Use memoryview() to reject integers und iterables,
            # acceptable by the bytes constructor.
            qs = bytes(memoryview(qs))
        except TypeError:
            wenn nicht qs:
                warnings.warn(f"Accepting {type(qs).__name__} objects mit "
                              f"false value in urllib.parse.parse_qsl() is "
                              f"deprecated als of 3.14",
                              DeprecationWarning, stacklevel=_stacklevel + 1)
                gib []
            raise
        wenn isinstance(separator, str):
            separator = bytes(separator, 'ascii')
        eq = b'='
        def _unquote(s):
            gib unquote_to_bytes(s.replace(b'+', b' '))

    wenn nicht qs:
        gib []

    # If max_num_fields is defined then check that the number of fields
    # is less than max_num_fields. This prevents a memory exhaustion DOS
    # attack via post bodies mit many fields.
    wenn max_num_fields is nicht Nichts:
        num_fields = 1 + qs.count(separator)
        wenn max_num_fields < num_fields:
            raise ValueError('Max number of fields exceeded')

    r = []
    fuer name_value in qs.split(separator):
        wenn name_value oder strict_parsing:
            name, has_eq, value = name_value.partition(eq)
            wenn nicht has_eq und strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            wenn value oder keep_blank_values:
                name = _unquote(name)
                value = _unquote(value)
                r.append((name, value))
    gib r

def unquote_plus(string, encoding='utf-8', errors='replace'):
    """Like unquote(), but also replace plus signs by spaces, als required for
    unquoting HTML form values.

    unquote_plus('%7e/abc+def') -> '~/abc def'
    """
    string = string.replace('+', ' ')
    gib unquote(string, encoding, errors)

_ALWAYS_SAFE = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                         b'abcdefghijklmnopqrstuvwxyz'
                         b'0123456789'
                         b'_.-~')
_ALWAYS_SAFE_BYTES = bytes(_ALWAYS_SAFE)


klasse _Quoter(dict):
    """A mapping von bytes numbers (in range(0,256)) to strings.

    String values are percent-encoded byte values, unless the key < 128, und
    in either of the specified safe set, oder the always safe set.
    """
    # Keeps a cache internally, via __missing__, fuer efficiency (lookups
    # of cached keys don't call Python code at all).
    def __init__(self, safe):
        """safe: bytes object."""
        self.safe = _ALWAYS_SAFE.union(safe)

    def __repr__(self):
        gib f"<Quoter {dict(self)!r}>"

    def __missing__(self, b):
        # Handle a cache miss. Store quoted string in cache und return.
        res = chr(b) wenn b in self.safe sonst '%{:02X}'.format(b)
        self[b] = res
        gib res

def quote(string, safe='/', encoding=Nichts, errors=Nichts):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted. The
    quote function offers a cautious (nicht minimal) way to quote a
    string fuer most of these parts.

    RFC 3986 Uniform Resource Identifier (URI): Generic Syntax lists
    the following (un)reserved characters.

    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
    reserved      = gen-delims / sub-delims
    gen-delims    = ":" / "/" / "?" / "#" / "[" / "]" / "@"
    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
                  / "*" / "+" / "," / ";" / "="

    Each of the reserved characters is reserved in some component of a URL,
    but nicht necessarily in all of them.

    The quote function %-escapes all characters that are neither in the
    unreserved chars ("always safe") nor the additional chars set via the
    safe arg.

    The default fuer the safe arg is '/'. The character is reserved, but in
    typical usage the quote function is being called on a path where the
    existing slash characters are to be preserved.

    Python 3.7 updates von using RFC 2396 to RFC 3986 to quote URL strings.
    Now, "~" is included in the set of unreserved characters.

    string und safe may be either str oder bytes objects. encoding und errors
    must nicht be specified wenn string is a bytes object.

    The optional encoding und errors parameters specify how to deal with
    non-ASCII characters, als accepted by the str.encode method.
    By default, encoding='utf-8' (characters are encoded mit UTF-8), und
    errors='strict' (unsupported characters raise a UnicodeEncodeError).
    """
    wenn isinstance(string, str):
        wenn nicht string:
            gib string
        wenn encoding is Nichts:
            encoding = 'utf-8'
        wenn errors is Nichts:
            errors = 'strict'
        string = string.encode(encoding, errors)
    sonst:
        wenn encoding is nicht Nichts:
            raise TypeError("quote() doesn't support 'encoding' fuer bytes")
        wenn errors is nicht Nichts:
            raise TypeError("quote() doesn't support 'errors' fuer bytes")
    gib quote_from_bytes(string, safe)

def quote_plus(string, safe='', encoding=Nichts, errors=Nichts):
    """Like quote(), but also replace ' ' mit '+', als required fuer quoting
    HTML form values. Plus signs in the original string are escaped unless
    they are included in safe. It also does nicht have safe default to '/'.
    """
    # Check wenn ' ' in string, where string may either be a str oder bytes.  If
    # there are no spaces, the regular quote will produce the right answer.
    wenn ((isinstance(string, str) und ' ' nicht in string) oder
        (isinstance(string, bytes) und b' ' nicht in string)):
        gib quote(string, safe, encoding, errors)
    wenn isinstance(safe, str):
        space = ' '
    sonst:
        space = b' '
    string = quote(string, safe + space, encoding, errors)
    gib string.replace(' ', '+')

# Expectation: A typical program is unlikely to create more than 5 of these.
@functools.lru_cache
def _byte_quoter_factory(safe):
    gib _Quoter(safe).__getitem__

def quote_from_bytes(bs, safe='/'):
    """Like quote(), but accepts a bytes object rather than a str, und does
    nicht perform string-to-bytes encoding.  It always returns an ASCII string.
    quote_from_bytes(b'abc def\x3f') -> 'abc%20def%3f'
    """
    wenn nicht isinstance(bs, (bytes, bytearray)):
        raise TypeError("quote_from_bytes() expected bytes")
    wenn nicht bs:
        gib ''
    wenn isinstance(safe, str):
        # Normalize 'safe' by converting to bytes und removing non-ASCII chars
        safe = safe.encode('ascii', 'ignore')
    sonst:
        # List comprehensions are faster than generator expressions.
        safe = bytes([c fuer c in safe wenn c < 128])
    wenn nicht bs.rstrip(_ALWAYS_SAFE_BYTES + safe):
        gib bs.decode()
    quoter = _byte_quoter_factory(safe)
    wenn (bs_len := len(bs)) < 200_000:
        gib ''.join(map(quoter, bs))
    sonst:
        # This saves memory - https://github.com/python/cpython/issues/95865
        chunk_size = math.isqrt(bs_len)
        chunks = [''.join(map(quoter, bs[i:i+chunk_size]))
                  fuer i in range(0, bs_len, chunk_size)]
        gib ''.join(chunks)

def urlencode(query, doseq=Falsch, safe='', encoding=Nichts, errors=Nichts,
              quote_via=quote_plus):
    """Encode a dict oder sequence of two-element tuples into a URL query string.

    If any values in the query arg are sequences und doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.

    The components of a query arg may each be either a string oder a bytes type.

    The safe, encoding, und errors parameters are passed down to the function
    specified by quote_via (encoding und errors only wenn a component is a str).
    """

    wenn hasattr(query, "items"):
        query = query.items()
    sonst:
        # It's a bother at times that strings und string-like objects are
        # sequences.
        try:
            # non-sequence items should nicht work mit len()
            # non-empty strings will fail this
            wenn len(query) und nicht isinstance(query[0], tuple):
                raise TypeError
            # Zero-length sequences of all types will get here und succeed,
            # but that's a minor nit.  Since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved fuer consistency
        except TypeError als err:
            raise TypeError("not a valid non-string sequence "
                            "or mapping object") von err

    l = []
    wenn nicht doseq:
        fuer k, v in query:
            wenn isinstance(k, bytes):
                k = quote_via(k, safe)
            sonst:
                k = quote_via(str(k), safe, encoding, errors)

            wenn isinstance(v, bytes):
                v = quote_via(v, safe)
            sonst:
                v = quote_via(str(v), safe, encoding, errors)
            l.append(k + '=' + v)
    sonst:
        fuer k, v in query:
            wenn isinstance(k, bytes):
                k = quote_via(k, safe)
            sonst:
                k = quote_via(str(k), safe, encoding, errors)

            wenn isinstance(v, bytes):
                v = quote_via(v, safe)
                l.append(k + '=' + v)
            sowenn isinstance(v, str):
                v = quote_via(v, safe, encoding, errors)
                l.append(k + '=' + v)
            sonst:
                try:
                    # Is this a sufficient test fuer sequence-ness?
                    x = len(v)
                except TypeError:
                    # nicht a sequence
                    v = quote_via(str(v), safe, encoding, errors)
                    l.append(k + '=' + v)
                sonst:
                    # loop over the sequence
                    fuer elt in v:
                        wenn isinstance(elt, bytes):
                            elt = quote_via(elt, safe)
                        sonst:
                            elt = quote_via(str(elt), safe, encoding, errors)
                        l.append(k + '=' + elt)
    gib '&'.join(l)


def to_bytes(url):
    warnings.warn("urllib.parse.to_bytes() is deprecated als of 3.8",
                  DeprecationWarning, stacklevel=2)
    gib _to_bytes(url)


def _to_bytes(url):
    """to_bytes(u"URL") --> 'URL'."""
    # Most URL schemes require ASCII. If that changes, the conversion
    # can be relaxed.
    # XXX get rid of to_bytes()
    wenn isinstance(url, str):
        try:
            url = url.encode("ASCII").decode()
        except UnicodeError:
            raise UnicodeError("URL " + repr(url) +
                               " contains non-ASCII characters")
    gib url


def unwrap(url):
    """Transform a string like '<URL:scheme://host/path>' into 'scheme://host/path'.

    The string is returned unchanged wenn it's nicht a wrapped URL.
    """
    url = str(url).strip()
    wenn url[:1] == '<' und url[-1:] == '>':
        url = url[1:-1].strip()
    wenn url[:4] == 'URL:':
        url = url[4:].strip()
    gib url


def splittype(url):
    warnings.warn("urllib.parse.splittype() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splittype(url)


_typeprog = Nichts
def _splittype(url):
    """splittype('type:opaquestring') --> 'type', 'opaquestring'."""
    global _typeprog
    wenn _typeprog is Nichts:
        _typeprog = re.compile('([^/:]+):(.*)', re.DOTALL)

    match = _typeprog.match(url)
    wenn match:
        scheme, data = match.groups()
        gib scheme.lower(), data
    gib Nichts, url


def splithost(url):
    warnings.warn("urllib.parse.splithost() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splithost(url)


_hostprog = Nichts
def _splithost(url):
    """splithost('//host[:port]/path') --> 'host[:port]', '/path'."""
    global _hostprog
    wenn _hostprog is Nichts:
        _hostprog = re.compile('//([^/#?]*)(.*)', re.DOTALL)

    match = _hostprog.match(url)
    wenn match:
        host_port, path = match.groups()
        wenn path und path[0] != '/':
            path = '/' + path
        gib host_port, path
    gib Nichts, url


def splituser(host):
    warnings.warn("urllib.parse.splituser() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splituser(host)


def _splituser(host):
    """splituser('user[:passwd]@host[:port]') --> 'user[:passwd]', 'host[:port]'."""
    user, delim, host = host.rpartition('@')
    gib (user wenn delim sonst Nichts), host


def splitpasswd(user):
    warnings.warn("urllib.parse.splitpasswd() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splitpasswd(user)


def _splitpasswd(user):
    """splitpasswd('user:passwd') -> 'user', 'passwd'."""
    user, delim, passwd = user.partition(':')
    gib user, (passwd wenn delim sonst Nichts)


def splitport(host):
    warnings.warn("urllib.parse.splitport() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splitport(host)


# splittag('/path#tag') --> '/path', 'tag'
_portprog = Nichts
def _splitport(host):
    """splitport('host:port') --> 'host', 'port'."""
    global _portprog
    wenn _portprog is Nichts:
        _portprog = re.compile('(.*):([0-9]*)', re.DOTALL)

    match = _portprog.fullmatch(host)
    wenn match:
        host, port = match.groups()
        wenn port:
            gib host, port
    gib host, Nichts


def splitnport(host, defport=-1):
    warnings.warn("urllib.parse.splitnport() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splitnport(host, defport)


def _splitnport(host, defport=-1):
    """Split host und port, returning numeric port.
    Return given default port wenn no ':' found; defaults to -1.
    Return numerical port wenn a valid number is found after ':'.
    Return Nichts wenn ':' but nicht a valid number."""
    host, delim, port = host.rpartition(':')
    wenn nicht delim:
        host = port
    sowenn port:
        wenn port.isdigit() und port.isascii():
            nport = int(port)
        sonst:
            nport = Nichts
        gib host, nport
    gib host, defport


def splitquery(url):
    warnings.warn("urllib.parse.splitquery() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splitquery(url)


def _splitquery(url):
    """splitquery('/path?query') --> '/path', 'query'."""
    path, delim, query = url.rpartition('?')
    wenn delim:
        gib path, query
    gib url, Nichts


def splittag(url):
    warnings.warn("urllib.parse.splittag() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splittag(url)


def _splittag(url):
    """splittag('/path#tag') --> '/path', 'tag'."""
    path, delim, tag = url.rpartition('#')
    wenn delim:
        gib path, tag
    gib url, Nichts


def splitattr(url):
    warnings.warn("urllib.parse.splitattr() is deprecated als of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splitattr(url)


def _splitattr(url):
    """splitattr('/path;attr1=value1;attr2=value2;...') ->
        '/path', ['attr1=value1', 'attr2=value2', ...]."""
    words = url.split(';')
    gib words[0], words[1:]


def splitvalue(attr):
    warnings.warn("urllib.parse.splitvalue() is deprecated als of 3.8, "
                  "use urllib.parse.parse_qsl() instead",
                  DeprecationWarning, stacklevel=2)
    gib _splitvalue(attr)


def _splitvalue(attr):
    """splitvalue('attr=value') --> 'attr', 'value'."""
    attr, delim, value = attr.partition('=')
    gib attr, (value wenn delim sonst Nichts)
