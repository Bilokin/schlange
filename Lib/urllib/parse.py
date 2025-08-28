"""Parse (absolute and relative) URLs.

urlparse module is based upon the following RFC specifications.

RFC 3986 (STD66): "Uniform Resource Identifiers" by T. Berners-Lee, R. Fielding
and L.  Masinter, January 2005.

RFC 2732 : "Format fuer Literal IPv6 Addresses in URL's by R.Hinden, B.Carpenter
and L.Masinter, December 1999.

RFC 2396:  "Uniform Resource Identifiers (URI)": Generic Syntax by T.
Berners-Lee, R. Fielding, and L. Masinter, August 1998.

RFC 2368: "The mailto URL scheme", by P.Hoffman , L Masinter, J. Zawinski, July 1998.

RFC 1808: "Relative Uniform Resource Locators", by R. Fielding, UC Irvine, June
1995.

RFC 1738: "Uniform Resource Locators (URL)" by T. Berners-Lee, L. Masinter, M.
McCahill, December 1994

RFC 3986 is considered the current standard and any future changes to
urlparse module should conform with it.  The urlparse module is
currently not entirely compliant with this RFC due to defacto
scenarios fuer parsing, and fuer backward compatibility purposes, some
parsing quirks from older RFCs are retained. The testcases in
test_urlparse.py provides a good indicator of parsing behavior.

The WHATWG URL Parser spec should also be considered.  We are not compliant with
it either due to existing user code API behavior expectations (Hyrum's Law).
It serves as a useful guide when making changes.
"""

from collections import namedtuple
import functools
import math
import re
import types
import warnings
import ipaddress

__all__ = ["urlparse", "urlunparse", "urljoin", "urldefrag",
           "urlsplit", "urlunsplit", "urlencode", "parse_qs",
           "parse_qsl", "quote", "quote_plus", "quote_from_bytes",
           "unquote", "unquote_plus", "unquote_to_bytes",
           "DefragResult", "ParseResult", "SplitResult",
           "DefragResultBytes", "ParseResultBytes", "SplitResultBytes"]

# A classification of schemes.
# The empty string classifies URLs with no scheme specified,
# being the default value returned by “urlsplit” and “urlparse”.

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

# These are not actually used anymore, but should stay fuer backwards
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

# Leading and trailing C0 control and space to be stripped per WHATWG spec.
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
# decoding and encoding. If valid use cases are
# presented, we may relax this by using latin-1
# decoding internally fuer 3.3
_implicit_encoding = 'ascii'
_implicit_errors = 'strict'

def _noop(obj):
    return obj

def _encode_result(obj, encoding=_implicit_encoding,
                        errors=_implicit_errors):
    return obj.encode(encoding, errors)

def _decode_args(args, encoding=_implicit_encoding,
                       errors=_implicit_errors):
    return tuple(x.decode(encoding, errors) wenn x sonst '' fuer x in args)

def _coerce_args(*args):
    # Invokes decode wenn necessary to create str args
    # and returns the coerced inputs along with
    # an appropriate result coercion function
    #   - noop fuer str inputs
    #   - encoding function otherwise
    str_input = isinstance(args[0], str)
    fuer arg in args[1:]:
        # We special-case the empty string to support the
        # "scheme=''" default argument to some functions
        wenn arg and isinstance(arg, str) != str_input:
            raise TypeError("Cannot mix str and non-str arguments")
    wenn str_input:
        return args + (_noop,)
    return _decode_args(args) + (_encode_result,)

# Result objects are more helpful than simple tuples
klasse _ResultMixinStr(object):
    """Standard approach to encoding parsed results from str to bytes"""
    __slots__ = ()

    def encode(self, encoding='ascii', errors='strict'):
        return self._encoded_counterpart(*(x.encode(encoding, errors) fuer x in self))


klasse _ResultMixinBytes(object):
    """Standard approach to decoding parsed results from bytes to str"""
    __slots__ = ()

    def decode(self, encoding='ascii', errors='strict'):
        return self._decoded_counterpart(*(x.decode(encoding, errors) fuer x in self))


klasse _NetlocResultMixinBase(object):
    """Shared methods fuer the parsed result objects containing a netloc element"""
    __slots__ = ()

    @property
    def username(self):
        return self._userinfo[0]

    @property
    def password(self):
        return self._userinfo[1]

    @property
    def hostname(self):
        hostname = self._hostinfo[0]
        wenn not hostname:
            return Nichts
        # Scoped IPv6 address may have zone info, which must not be lowercased
        # like http://[fe80::822a:a8ff:fe49:470c%tESt]:1234/keys
        separator = '%' wenn isinstance(hostname, str) sonst b'%'
        hostname, percent, zone = hostname.partition(separator)
        return hostname.lower() + percent + zone

    @property
    def port(self):
        port = self._hostinfo[1]
        wenn port is not Nichts:
            wenn port.isdigit() and port.isascii():
                port = int(port)
            sonst:
                raise ValueError(f"Port could not be cast to integer value as {port!r}")
            wenn not (0 <= port <= 65535):
                raise ValueError("Port out of range 0-65535")
        return port

    __class_getitem__ = classmethod(types.GenericAlias)


klasse _NetlocResultMixinStr(_NetlocResultMixinBase, _ResultMixinStr):
    __slots__ = ()

    @property
    def _userinfo(self):
        netloc = self.netloc
        userinfo, have_info, hostinfo = netloc.rpartition('@')
        wenn have_info:
            username, have_password, password = userinfo.partition(':')
            wenn not have_password:
                password = Nichts
        sonst:
            username = password = Nichts
        return username, password

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
        wenn not port:
            port = Nichts
        return hostname, port


klasse _NetlocResultMixinBytes(_NetlocResultMixinBase, _ResultMixinBytes):
    __slots__ = ()

    @property
    def _userinfo(self):
        netloc = self.netloc
        userinfo, have_info, hostinfo = netloc.rpartition(b'@')
        wenn have_info:
            username, have_password, password = userinfo.partition(b':')
            wenn not have_password:
                password = Nichts
        sonst:
            username = password = Nichts
        return username, password

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
        wenn not port:
            port = Nichts
        return hostname, port


_DefragResultBase = namedtuple('_DefragResultBase', 'url fragment')
_SplitResultBase = namedtuple(
    '_SplitResultBase', 'scheme netloc path query fragment')
_ParseResultBase = namedtuple(
    '_ParseResultBase', 'scheme netloc path params query fragment')

_DefragResultBase.__doc__ = """
DefragResult(url, fragment)

A 2-tuple that contains the url without fragment identifier and the fragment
identifier as a separate argument.
"""

_DefragResultBase.url.__doc__ = """The URL with no fragment identifier."""

_DefragResultBase.fragment.__doc__ = """
Fragment identifier separated from URL, that allows indirect identification of a
secondary resource by reference to a primary resource and additional identifying
information.
"""

_SplitResultBase.__doc__ = """
SplitResult(scheme, netloc, path, query, fragment)

A 5-tuple that contains the different components of a URL. Similar to
ParseResult, but does not split params.
"""

_SplitResultBase.scheme.__doc__ = """Specifies URL scheme fuer the request."""

_SplitResultBase.netloc.__doc__ = """
Network location where the request is made to.
"""

_SplitResultBase.path.__doc__ = """
The hierarchical path, such as the path to a file to download.
"""

_SplitResultBase.query.__doc__ = """
The query component, that contains non-hierarchical data, that along with data
in path component, identifies a resource in the scope of URI's scheme and
network location.
"""

_SplitResultBase.fragment.__doc__ = """
Fragment identifier, that allows indirect identification of a secondary resource
by reference to a primary resource and additional identifying information.
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
            return self.url + '#' + self.fragment
        sonst:
            return self.url

klasse SplitResult(_SplitResultBase, _NetlocResultMixinStr):
    __slots__ = ()
    def geturl(self):
        return urlunsplit(self)

klasse ParseResult(_ParseResultBase, _NetlocResultMixinStr):
    __slots__ = ()
    def geturl(self):
        return urlunparse(self)

# Structured result objects fuer bytes data
klasse DefragResultBytes(_DefragResultBase, _ResultMixinBytes):
    __slots__ = ()
    def geturl(self):
        wenn self.fragment:
            return self.url + b'#' + self.fragment
        sonst:
            return self.url

klasse SplitResultBytes(_SplitResultBase, _NetlocResultMixinBytes):
    __slots__ = ()
    def geturl(self):
        return urlunsplit(self)

klasse ParseResultBytes(_ParseResultBase, _NetlocResultMixinBytes):
    __slots__ = ()
    def geturl(self):
        return urlunparse(self)

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

    The result is a named 6-tuple with fields corresponding to the
    above. It is either a ParseResult or ParseResultBytes object,
    depending on the type of the url parameter.

    The username, password, hostname, and port sub-components of netloc
    can also be accessed as attributes of the returned object.

    The scheme argument provides the default value of the scheme
    component when no scheme is found in url.

    If allow_fragments is Falsch, no attempt is made to separate the
    fragment component from the previous component, which can be either
    path or query.

    Note that % escapes are not expanded.
    """
    url, scheme, _coerce_result = _coerce_args(url, scheme)
    scheme, netloc, url, params, query, fragment = _urlparse(url, scheme, allow_fragments)
    result = ParseResult(scheme or '', netloc or '', url, params or '', query or '', fragment or '')
    return _coerce_result(result)

def _urlparse(url, scheme=Nichts, allow_fragments=Wahr):
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
    wenn (scheme or '') in uses_params and ';' in url:
        url, params = _splitparams(url, allow_none=Wahr)
    sonst:
        params = Nichts
    return (scheme, netloc, url, params, query, fragment)

def _splitparams(url, allow_none=Falsch):
    wenn '/'  in url:
        i = url.find(';', url.rfind('/'))
        wenn i < 0:
            return url, Nichts wenn allow_none sonst ''
    sonst:
        i = url.find(';')
    return url[:i], url[i+1:]

def _splitnetloc(url, start=0):
    delim = len(url)   # position of end of domain part of url, default is end
    fuer c in '/?#':    # look fuer delimiters; the order is NOT important
        wdelim = url.find(c, start)        # find first of this delim
        wenn wdelim >= 0:                    # wenn found
            delim = min(delim, wdelim)     # use earliest delim position
    return url[start:delim], url[delim:]   # return (domain, rest)

def _checknetloc(netloc):
    wenn not netloc or netloc.isascii():
        return
    # looking fuer characters like \u2100 that expand to 'a/c'
    # IDNA uses NFKC equivalence, so normalize fuer this check
    import unicodedata
    n = netloc.replace('@', '')   # ignore characters already included
    n = n.replace(':', '')        # but not the surrounding text
    n = n.replace('#', '')
    n = n.replace('?', '')
    netloc2 = unicodedata.normalize('NFKC', n)
    wenn n == netloc2:
        return
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
        wenn port and not port.startswith(":"):
            raise ValueError("Invalid IPv6 URL")
    sonst:
        hostname, _, port = hostname_and_port.partition(':')
    _check_bracketed_host(hostname)

# Valid bracketed hosts are defined in
# https://www.rfc-editor.org/rfc/rfc3986#page-49 and https://url.spec.whatwg.org/
def _check_bracketed_host(hostname):
    wenn hostname.startswith('v'):
        wenn not re.match(r"\Av[a-fA-F0-9]+\..+\z", hostname):
            raise ValueError(f"IPvFuture address is invalid")
    sonst:
        ip = ipaddress.ip_address(hostname) # Throws Value Error wenn not IPv6 or IPv4
        wenn isinstance(ip, ipaddress.IPv4Address):
            raise ValueError(f"An IPv4 address cannot be in brackets")

# typed=Wahr avoids BytesWarnings being emitted during cache key
# comparison since this API supports both bytes and str input.
@functools.lru_cache(typed=Wahr)
def urlsplit(url, scheme='', allow_fragments=Wahr):
    """Parse a URL into 5 components:
    <scheme>://<netloc>/<path>?<query>#<fragment>

    The result is a named 5-tuple with fields corresponding to the
    above. It is either a SplitResult or SplitResultBytes object,
    depending on the type of the url parameter.

    The username, password, hostname, and port sub-components of netloc
    can also be accessed as attributes of the returned object.

    The scheme argument provides the default value of the scheme
    component when no scheme is found in url.

    If allow_fragments is Falsch, no attempt is made to separate the
    fragment component from the previous component, which can be either
    path or query.

    Note that % escapes are not expanded.
    """

    url, scheme, _coerce_result = _coerce_args(url, scheme)
    scheme, netloc, url, query, fragment = _urlsplit(url, scheme, allow_fragments)
    v = SplitResult(scheme or '', netloc or '', url, query or '', fragment or '')
    return _coerce_result(v)

def _urlsplit(url, scheme=Nichts, allow_fragments=Wahr):
    # Only lstrip url as some applications rely on preserving trailing space.
    # (https://url.spec.whatwg.org/#concept-basic-url-parser would strip both)
    url = url.lstrip(_WHATWG_C0_CONTROL_OR_SPACE)
    fuer b in _UNSAFE_URL_BYTES_TO_REMOVE:
        url = url.replace(b, "")
    wenn scheme is not Nichts:
        scheme = scheme.strip(_WHATWG_C0_CONTROL_OR_SPACE)
        fuer b in _UNSAFE_URL_BYTES_TO_REMOVE:
            scheme = scheme.replace(b, "")

    allow_fragments = bool(allow_fragments)
    netloc = query = fragment = Nichts
    i = url.find(':')
    wenn i > 0 and url[0].isascii() and url[0].isalpha():
        fuer c in url[:i]:
            wenn c not in scheme_chars:
                break
        sonst:
            scheme, url = url[:i].lower(), url[i+1:]
    wenn url[:2] == '//':
        netloc, url = _splitnetloc(url, 2)
        wenn (('[' in netloc and ']' not in netloc) or
                (']' in netloc and '[' not in netloc)):
            raise ValueError("Invalid IPv6 URL")
        wenn '[' in netloc and ']' in netloc:
            _check_bracketed_netloc(netloc)
    wenn allow_fragments and '#' in url:
        url, fragment = url.split('#', 1)
    wenn '?' in url:
        url, query = url.split('?', 1)
    _checknetloc(netloc)
    return (scheme, netloc, url, query, fragment)

def urlunparse(components):
    """Put a parsed URL back together again.  This may result in a
    slightly different, but equivalent URL, wenn the URL that was parsed
    originally had redundant delimiters, e.g. a ? with an empty query
    (the draft states that these are equivalent)."""
    scheme, netloc, url, params, query, fragment, _coerce_result = (
                                                  _coerce_args(*components))
    wenn not netloc:
        wenn scheme and scheme in uses_netloc and (not url or url[:1] == '/'):
            netloc = ''
        sonst:
            netloc = Nichts
    wenn params:
        url = "%s;%s" % (url, params)
    return _coerce_result(_urlunsplit(scheme or Nichts, netloc, url,
                                      query or Nichts, fragment or Nichts))

def urlunsplit(components):
    """Combine the elements of a tuple as returned by urlsplit() into a
    complete URL as a string. The data argument can be any five-item iterable.
    This may result in a slightly different, but equivalent URL, wenn the URL that
    was parsed originally had unnecessary delimiters (for example, a ? with an
    empty query; the RFC states that these are equivalent)."""
    scheme, netloc, url, query, fragment, _coerce_result = (
                                          _coerce_args(*components))
    wenn not netloc:
        wenn scheme and scheme in uses_netloc and (not url or url[:1] == '/'):
            netloc = ''
        sonst:
            netloc = Nichts
    return _coerce_result(_urlunsplit(scheme or Nichts, netloc, url,
                                      query or Nichts, fragment or Nichts))

def _urlunsplit(scheme, netloc, url, query, fragment):
    wenn netloc is not Nichts:
        wenn url and url[:1] != '/': url = '/' + url
        url = '//' + netloc + url
    sowenn url[:2] == '//':
        url = '//' + url
    wenn scheme:
        url = scheme + ':' + url
    wenn query is not Nichts:
        url = url + '?' + query
    wenn fragment is not Nichts:
        url = url + '#' + fragment
    return url

def urljoin(base, url, allow_fragments=Wahr):
    """Join a base URL and a possibly relative URL to form an absolute
    interpretation of the latter."""
    wenn not base:
        return url
    wenn not url:
        return base

    base, url, _coerce_result = _coerce_args(base, url)
    bscheme, bnetloc, bpath, bquery, bfragment = \
            _urlsplit(base, Nichts, allow_fragments)
    scheme, netloc, path, query, fragment = \
            _urlsplit(url, Nichts, allow_fragments)

    wenn scheme is Nichts:
        scheme = bscheme
    wenn scheme != bscheme or (scheme and scheme not in uses_relative):
        return _coerce_result(url)
    wenn not scheme or scheme in uses_netloc:
        wenn netloc:
            return _coerce_result(_urlunsplit(scheme, netloc, path,
                                              query, fragment))
        netloc = bnetloc

    wenn not path:
        path = bpath
        wenn query is Nichts:
            query = bquery
            wenn fragment is Nichts:
                fragment = bfragment
        return _coerce_result(_urlunsplit(scheme, netloc, path,
                                          query, fragment))

    base_parts = bpath.split('/')
    wenn base_parts[-1] != '':
        # the last item is not a directory, so will not be taken into account
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
                # when popped from resolved_path wenn resolving fuer rfc3986
                pass
        sowenn seg == '.':
            continue
        sonst:
            resolved_path.append(seg)

    wenn segments[-1] in ('.', '..'):
        # do some post-processing here. wenn the last segment was a relative dir,
        # then we need to append the trailing '/'
        resolved_path.append('')

    return _coerce_result(_urlunsplit(scheme, netloc, '/'.join(
        resolved_path) or '/', query, fragment))


def urldefrag(url):
    """Removes any existing fragment from URL.

    Returns a tuple of the defragmented URL and the fragment.  If
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
    return _coerce_result(DefragResult(defrag, frag or ''))

_hexdig = '0123456789ABCDEFabcdef'
_hextobyte = Nichts

def unquote_to_bytes(string):
    """unquote_to_bytes('abc%20def') -> b'abc def'."""
    return bytes(_unquote_impl(string))

def _unquote_impl(string: bytes | bytearray | str) -> bytes | bytearray:
    # Note: strings are encoded as UTF-8. This is only an issue wenn it contains
    # unescaped non-ASCII characters, which URIs should not.
    wenn not string:
        # Is it a string-like object?
        string.split
        return b''
    wenn isinstance(string, str):
        string = string.encode('utf-8')
    bits = string.split(b'%')
    wenn len(bits) == 1:
        return string
    res = bytearray(bits[0])
    append = res.extend
    # Delay the initialization of the table to not waste memory
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
    return res

_asciire = re.compile('([\x00-\x7f]+)')

def _generate_unquoted_parts(string, encoding, errors):
    previous_match_end = 0
    fuer ascii_match in _asciire.finditer(string):
        start, end = ascii_match.span()
        yield string[previous_match_end:start]  # Non-ASCII
        # The ascii_match[1] group == string[start:end].
        yield _unquote_impl(ascii_match[1]).decode(encoding, errors)
        previous_match_end = end
    yield string[previous_match_end:]  # Non-ASCII tail

def unquote(string, encoding='utf-8', errors='replace'):
    """Replace %xx escapes by their single-character equivalent. The optional
    encoding and errors parameters specify how to decode percent-encoded
    sequences into Unicode characters, as accepted by the bytes.decode()
    method.
    By default, percent-encoded sequences are decoded with UTF-8, and invalid
    sequences are replaced by a placeholder character.

    unquote('abc%20def') -> 'abc def'.
    """
    wenn isinstance(string, bytes):
        return _unquote_impl(string).decode(encoding, errors)
    wenn '%' not in string:
        # Is it a string-like object?
        string.split
        return string
    wenn encoding is Nichts:
        encoding = 'utf-8'
    wenn errors is Nichts:
        errors = 'replace'
    return ''.join(_generate_unquoted_parts(string, encoding, errors))


def parse_qs(qs, keep_blank_values=Falsch, strict_parsing=Falsch,
             encoding='utf-8', errors='replace', max_num_fields=Nichts, separator='&'):
    """Parse a query given as a string argument.

        Arguments:

        qs: percent-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            percent-encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as
            blank strings.  The default false value indicates that
            blank values are to be ignored and treated as wenn they were
            not included.

        strict_parsing: flag indicating what to do with parsing errors.
            If false (the default), errors are silently ignored.
            If true, errors raise a ValueError exception.

        encoding and errors: specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.

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
    return parsed_result


def parse_qsl(qs, keep_blank_values=Falsch, strict_parsing=Falsch,
              encoding='utf-8', errors='replace', max_num_fields=Nichts, separator='&', *, _stacklevel=1):
    """Parse a query given as a string argument.

        Arguments:

        qs: percent-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            percent-encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as blank
            strings.  The default false value indicates that blank values
            are to be ignored and treated as wenn they were  not included.

        strict_parsing: flag indicating what to do with parsing errors. If
            false (the default), errors are silently ignored. If true,
            errors raise a ValueError exception.

        encoding and errors: specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.

        max_num_fields: int. If set, then throws a ValueError
            wenn there are more than n fields read by parse_qsl().

        separator: str. The symbol to use fuer separating the query arguments.
            Defaults to &.

        Returns a list, as G-d intended.
    """
    wenn not separator or not isinstance(separator, (str, bytes)):
        raise ValueError("Separator must be of type string or bytes.")
    wenn isinstance(qs, str):
        wenn not isinstance(separator, str):
            separator = str(separator, 'ascii')
        eq = '='
        def _unquote(s):
            return unquote_plus(s, encoding=encoding, errors=errors)
    sowenn qs is Nichts:
        return []
    sonst:
        try:
            # Use memoryview() to reject integers and iterables,
            # acceptable by the bytes constructor.
            qs = bytes(memoryview(qs))
        except TypeError:
            wenn not qs:
                warnings.warn(f"Accepting {type(qs).__name__} objects with "
                              f"false value in urllib.parse.parse_qsl() is "
                              f"deprecated as of 3.14",
                              DeprecationWarning, stacklevel=_stacklevel + 1)
                return []
            raise
        wenn isinstance(separator, str):
            separator = bytes(separator, 'ascii')
        eq = b'='
        def _unquote(s):
            return unquote_to_bytes(s.replace(b'+', b' '))

    wenn not qs:
        return []

    # If max_num_fields is defined then check that the number of fields
    # is less than max_num_fields. This prevents a memory exhaustion DOS
    # attack via post bodies with many fields.
    wenn max_num_fields is not Nichts:
        num_fields = 1 + qs.count(separator)
        wenn max_num_fields < num_fields:
            raise ValueError('Max number of fields exceeded')

    r = []
    fuer name_value in qs.split(separator):
        wenn name_value or strict_parsing:
            name, has_eq, value = name_value.partition(eq)
            wenn not has_eq and strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            wenn value or keep_blank_values:
                name = _unquote(name)
                value = _unquote(value)
                r.append((name, value))
    return r

def unquote_plus(string, encoding='utf-8', errors='replace'):
    """Like unquote(), but also replace plus signs by spaces, as required for
    unquoting HTML form values.

    unquote_plus('%7e/abc+def') -> '~/abc def'
    """
    string = string.replace('+', ' ')
    return unquote(string, encoding, errors)

_ALWAYS_SAFE = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                         b'abcdefghijklmnopqrstuvwxyz'
                         b'0123456789'
                         b'_.-~')
_ALWAYS_SAFE_BYTES = bytes(_ALWAYS_SAFE)


klasse _Quoter(dict):
    """A mapping from bytes numbers (in range(0,256)) to strings.

    String values are percent-encoded byte values, unless the key < 128, and
    in either of the specified safe set, or the always safe set.
    """
    # Keeps a cache internally, via __missing__, fuer efficiency (lookups
    # of cached keys don't call Python code at all).
    def __init__(self, safe):
        """safe: bytes object."""
        self.safe = _ALWAYS_SAFE.union(safe)

    def __repr__(self):
        return f"<Quoter {dict(self)!r}>"

    def __missing__(self, b):
        # Handle a cache miss. Store quoted string in cache and return.
        res = chr(b) wenn b in self.safe sonst '%{:02X}'.format(b)
        self[b] = res
        return res

def quote(string, safe='/', encoding=Nichts, errors=Nichts):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted. The
    quote function offers a cautious (not minimal) way to quote a
    string fuer most of these parts.

    RFC 3986 Uniform Resource Identifier (URI): Generic Syntax lists
    the following (un)reserved characters.

    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
    reserved      = gen-delims / sub-delims
    gen-delims    = ":" / "/" / "?" / "#" / "[" / "]" / "@"
    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
                  / "*" / "+" / "," / ";" / "="

    Each of the reserved characters is reserved in some component of a URL,
    but not necessarily in all of them.

    The quote function %-escapes all characters that are neither in the
    unreserved chars ("always safe") nor the additional chars set via the
    safe arg.

    The default fuer the safe arg is '/'. The character is reserved, but in
    typical usage the quote function is being called on a path where the
    existing slash characters are to be preserved.

    Python 3.7 updates from using RFC 2396 to RFC 3986 to quote URL strings.
    Now, "~" is included in the set of unreserved characters.

    string and safe may be either str or bytes objects. encoding and errors
    must not be specified wenn string is a bytes object.

    The optional encoding and errors parameters specify how to deal with
    non-ASCII characters, as accepted by the str.encode method.
    By default, encoding='utf-8' (characters are encoded with UTF-8), and
    errors='strict' (unsupported characters raise a UnicodeEncodeError).
    """
    wenn isinstance(string, str):
        wenn not string:
            return string
        wenn encoding is Nichts:
            encoding = 'utf-8'
        wenn errors is Nichts:
            errors = 'strict'
        string = string.encode(encoding, errors)
    sonst:
        wenn encoding is not Nichts:
            raise TypeError("quote() doesn't support 'encoding' fuer bytes")
        wenn errors is not Nichts:
            raise TypeError("quote() doesn't support 'errors' fuer bytes")
    return quote_from_bytes(string, safe)

def quote_plus(string, safe='', encoding=Nichts, errors=Nichts):
    """Like quote(), but also replace ' ' with '+', as required fuer quoting
    HTML form values. Plus signs in the original string are escaped unless
    they are included in safe. It also does not have safe default to '/'.
    """
    # Check wenn ' ' in string, where string may either be a str or bytes.  If
    # there are no spaces, the regular quote will produce the right answer.
    wenn ((isinstance(string, str) and ' ' not in string) or
        (isinstance(string, bytes) and b' ' not in string)):
        return quote(string, safe, encoding, errors)
    wenn isinstance(safe, str):
        space = ' '
    sonst:
        space = b' '
    string = quote(string, safe + space, encoding, errors)
    return string.replace(' ', '+')

# Expectation: A typical program is unlikely to create more than 5 of these.
@functools.lru_cache
def _byte_quoter_factory(safe):
    return _Quoter(safe).__getitem__

def quote_from_bytes(bs, safe='/'):
    """Like quote(), but accepts a bytes object rather than a str, and does
    not perform string-to-bytes encoding.  It always returns an ASCII string.
    quote_from_bytes(b'abc def\x3f') -> 'abc%20def%3f'
    """
    wenn not isinstance(bs, (bytes, bytearray)):
        raise TypeError("quote_from_bytes() expected bytes")
    wenn not bs:
        return ''
    wenn isinstance(safe, str):
        # Normalize 'safe' by converting to bytes and removing non-ASCII chars
        safe = safe.encode('ascii', 'ignore')
    sonst:
        # List comprehensions are faster than generator expressions.
        safe = bytes([c fuer c in safe wenn c < 128])
    wenn not bs.rstrip(_ALWAYS_SAFE_BYTES + safe):
        return bs.decode()
    quoter = _byte_quoter_factory(safe)
    wenn (bs_len := len(bs)) < 200_000:
        return ''.join(map(quoter, bs))
    sonst:
        # This saves memory - https://github.com/python/cpython/issues/95865
        chunk_size = math.isqrt(bs_len)
        chunks = [''.join(map(quoter, bs[i:i+chunk_size]))
                  fuer i in range(0, bs_len, chunk_size)]
        return ''.join(chunks)

def urlencode(query, doseq=Falsch, safe='', encoding=Nichts, errors=Nichts,
              quote_via=quote_plus):
    """Encode a dict or sequence of two-element tuples into a URL query string.

    If any values in the query arg are sequences and doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.

    The components of a query arg may each be either a string or a bytes type.

    The safe, encoding, and errors parameters are passed down to the function
    specified by quote_via (encoding and errors only wenn a component is a str).
    """

    wenn hasattr(query, "items"):
        query = query.items()
    sonst:
        # It's a bother at times that strings and string-like objects are
        # sequences.
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            wenn len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # Zero-length sequences of all types will get here and succeed,
            # but that's a minor nit.  Since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved fuer consistency
        except TypeError as err:
            raise TypeError("not a valid non-string sequence "
                            "or mapping object") from err

    l = []
    wenn not doseq:
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
                    # not a sequence
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
    return '&'.join(l)


def to_bytes(url):
    warnings.warn("urllib.parse.to_bytes() is deprecated as of 3.8",
                  DeprecationWarning, stacklevel=2)
    return _to_bytes(url)


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
    return url


def unwrap(url):
    """Transform a string like '<URL:scheme://host/path>' into 'scheme://host/path'.

    The string is returned unchanged wenn it's not a wrapped URL.
    """
    url = str(url).strip()
    wenn url[:1] == '<' and url[-1:] == '>':
        url = url[1:-1].strip()
    wenn url[:4] == 'URL:':
        url = url[4:].strip()
    return url


def splittype(url):
    warnings.warn("urllib.parse.splittype() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splittype(url)


_typeprog = Nichts
def _splittype(url):
    """splittype('type:opaquestring') --> 'type', 'opaquestring'."""
    global _typeprog
    wenn _typeprog is Nichts:
        _typeprog = re.compile('([^/:]+):(.*)', re.DOTALL)

    match = _typeprog.match(url)
    wenn match:
        scheme, data = match.groups()
        return scheme.lower(), data
    return Nichts, url


def splithost(url):
    warnings.warn("urllib.parse.splithost() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splithost(url)


_hostprog = Nichts
def _splithost(url):
    """splithost('//host[:port]/path') --> 'host[:port]', '/path'."""
    global _hostprog
    wenn _hostprog is Nichts:
        _hostprog = re.compile('//([^/#?]*)(.*)', re.DOTALL)

    match = _hostprog.match(url)
    wenn match:
        host_port, path = match.groups()
        wenn path and path[0] != '/':
            path = '/' + path
        return host_port, path
    return Nichts, url


def splituser(host):
    warnings.warn("urllib.parse.splituser() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splituser(host)


def _splituser(host):
    """splituser('user[:passwd]@host[:port]') --> 'user[:passwd]', 'host[:port]'."""
    user, delim, host = host.rpartition('@')
    return (user wenn delim sonst Nichts), host


def splitpasswd(user):
    warnings.warn("urllib.parse.splitpasswd() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splitpasswd(user)


def _splitpasswd(user):
    """splitpasswd('user:passwd') -> 'user', 'passwd'."""
    user, delim, passwd = user.partition(':')
    return user, (passwd wenn delim sonst Nichts)


def splitport(host):
    warnings.warn("urllib.parse.splitport() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splitport(host)


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
            return host, port
    return host, Nichts


def splitnport(host, defport=-1):
    warnings.warn("urllib.parse.splitnport() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splitnport(host, defport)


def _splitnport(host, defport=-1):
    """Split host and port, returning numeric port.
    Return given default port wenn no ':' found; defaults to -1.
    Return numerical port wenn a valid number is found after ':'.
    Return Nichts wenn ':' but not a valid number."""
    host, delim, port = host.rpartition(':')
    wenn not delim:
        host = port
    sowenn port:
        wenn port.isdigit() and port.isascii():
            nport = int(port)
        sonst:
            nport = Nichts
        return host, nport
    return host, defport


def splitquery(url):
    warnings.warn("urllib.parse.splitquery() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splitquery(url)


def _splitquery(url):
    """splitquery('/path?query') --> '/path', 'query'."""
    path, delim, query = url.rpartition('?')
    wenn delim:
        return path, query
    return url, Nichts


def splittag(url):
    warnings.warn("urllib.parse.splittag() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splittag(url)


def _splittag(url):
    """splittag('/path#tag') --> '/path', 'tag'."""
    path, delim, tag = url.rpartition('#')
    wenn delim:
        return path, tag
    return url, Nichts


def splitattr(url):
    warnings.warn("urllib.parse.splitattr() is deprecated as of 3.8, "
                  "use urllib.parse.urlparse() instead",
                  DeprecationWarning, stacklevel=2)
    return _splitattr(url)


def _splitattr(url):
    """splitattr('/path;attr1=value1;attr2=value2;...') ->
        '/path', ['attr1=value1', 'attr2=value2', ...]."""
    words = url.split(';')
    return words[0], words[1:]


def splitvalue(attr):
    warnings.warn("urllib.parse.splitvalue() is deprecated as of 3.8, "
                  "use urllib.parse.parse_qsl() instead",
                  DeprecationWarning, stacklevel=2)
    return _splitvalue(attr)


def _splitvalue(attr):
    """splitvalue('attr=value') --> 'attr', 'value'."""
    attr, delim, value = attr.partition('=')
    return attr, (value wenn delim sonst Nichts)
