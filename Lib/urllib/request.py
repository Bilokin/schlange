"""An extensible library fuer opening URLs using a variety of protocols

The simplest way to use this module is to call the urlopen function,
which accepts a string containing a URL or a Request object (described
below).  It opens the URL and returns the results as file-like
object; the returned object has some extra methods described below.

The OpenerDirector manages a collection of Handler objects that do
all the actual work.  Each Handler implements a particular protocol or
option.  The OpenerDirector is a composite object that invokes the
Handlers needed to open the requested URL.  For example, the
HTTPHandler performs HTTP GET and POST requests and deals with
non-error returns.  The HTTPRedirectHandler automatically deals with
HTTP 301, 302, 303, 307, and 308 redirect errors, and the
HTTPDigestAuthHandler deals with digest authentication.

urlopen(url, data=Nichts) -- Basic usage is the same as original
urllib.  pass the url and optionally data to post to an HTTP URL, and
get a file-like object back.  One difference is that you can also pass
a Request instance instead of URL.  Raises a URLError (subclass of
OSError); fuer HTTP errors, raises an HTTPError, which can also be
treated as a valid response.

build_opener -- Function that creates a new OpenerDirector instance.
Will install the default handlers.  Accepts one or more Handlers as
arguments, either instances or Handler classes that it will
instantiate.  If one of the argument is a subclass of the default
handler, the argument will be installed instead of the default.

install_opener -- Installs a new opener as the default opener.

objects of interest:

OpenerDirector -- Sets up the User Agent as the Python-urllib client and manages
the Handler classes, while dealing with requests and responses.

Request -- An object that encapsulates the state of a request.  The
state can be as simple as the URL.  It can also include extra HTTP
headers, e.g. a User-Agent.

BaseHandler --

internals:
BaseHandler and parent
_call_chain conventions

Example usage:

import urllib.request

# set up authentication info
authinfo = urllib.request.HTTPBasicAuthHandler()
authinfo.add_password(realm='PDQ Application',
                      uri='https://mahler:8092/site-updates.py',
                      user='klem',
                      passwd='geheim$parole')

proxy_support = urllib.request.ProxyHandler({"http" : "http://ahad-haam:3128"})

# build a new opener that adds authentication and caching FTP handlers
opener = urllib.request.build_opener(proxy_support, authinfo,
                                     urllib.request.CacheFTPHandler)

# install it
urllib.request.install_opener(opener)

f = urllib.request.urlopen('https://www.python.org/')
"""

# XXX issues:
# If an authentication error handler that tries to perform
# authentication fuer some reason but fails, how should the error be
# signalled?  The client needs to know the HTTP error code.  But if
# the handler knows that the problem was, e.g., that it didn't know
# that hash algo that requested in the challenge, it would be good to
# pass that information along to the client, too.
# ftp errors aren't handled cleanly
# check digest against correct (i.e. non-apache) implementation

# Possible extensions:
# complex proxies  XXX not sure what exactly was meant by this
# abstract factory fuer opener

import base64
import bisect
import contextlib
import email
import hashlib
import http.client
import io
import os
import re
import socket
import string
import sys
import time
import tempfile


from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.parse import (
    urlparse, urlsplit, urljoin, unwrap, quote, unquote,
    _splittype, _splithost, _splitport, _splituser, _splitpasswd,
    _splitattr, _splitvalue, _splittag,
    unquote_to_bytes, urlunparse)
from urllib.response import addinfourl, addclosehook

# check fuer SSL
try:
    import ssl  # noqa: F401
except ImportError:
    _have_ssl = Falsch
sonst:
    _have_ssl = Wahr

__all__ = [
    # Classes
    'Request', 'OpenerDirector', 'BaseHandler', 'HTTPDefaultErrorHandler',
    'HTTPRedirectHandler', 'HTTPCookieProcessor', 'ProxyHandler',
    'HTTPPasswordMgr', 'HTTPPasswordMgrWithDefaultRealm',
    'HTTPPasswordMgrWithPriorAuth', 'AbstractBasicAuthHandler',
    'HTTPBasicAuthHandler', 'ProxyBasicAuthHandler', 'AbstractDigestAuthHandler',
    'HTTPDigestAuthHandler', 'ProxyDigestAuthHandler', 'HTTPHandler',
    'FileHandler', 'FTPHandler', 'CacheFTPHandler', 'DataHandler',
    'UnknownHandler', 'HTTPErrorProcessor',
    # Functions
    'urlopen', 'install_opener', 'build_opener',
    'pathname2url', 'url2pathname', 'getproxies',
    # Legacy interface
    'urlretrieve', 'urlcleanup',
]

# used in User-Agent header sent
__version__ = '%d.%d' % sys.version_info[:2]

_opener = Nichts
def urlopen(url, data=Nichts, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
            *, context=Nichts):
    '''Open the URL url, which can be either a string or a Request object.

    *data* must be an object specifying additional data to be sent to
    the server, or Nichts wenn no such data is needed.  See Request for
    details.

    urllib.request module uses HTTP/1.1 and includes a "Connection:close"
    header in its HTTP requests.

    The optional *timeout* parameter specifies a timeout in seconds for
    blocking operations like the connection attempt (if not specified, the
    global default timeout setting will be used). This only works fuer HTTP,
    HTTPS and FTP connections.

    If *context* is specified, it must be a ssl.SSLContext instance describing
    the various SSL options. See HTTPSConnection fuer more details.


    This function always returns an object which can work as a
    context manager and has the properties url, headers, and status.
    See urllib.response.addinfourl fuer more detail on these properties.

    For HTTP and HTTPS URLs, this function returns a http.client.HTTPResponse
    object slightly modified. In addition to the three new methods above, the
    msg attribute contains the same information as the reason attribute ---
    the reason phrase returned by the server --- instead of the response
    headers as it is specified in the documentation fuer HTTPResponse.

    For FTP, file, and data URLs, this function returns a
    urllib.response.addinfourl object.

    Note that Nichts may be returned wenn no handler handles the request (though
    the default installed global OpenerDirector uses UnknownHandler to ensure
    this never happens).

    In addition, wenn proxy settings are detected (for example, when a *_proxy
    environment variable like http_proxy is set), ProxyHandler is default
    installed and makes sure the requests are handled through the proxy.

    '''
    global _opener
    wenn context:
        https_handler = HTTPSHandler(context=context)
        opener = build_opener(https_handler)
    sowenn _opener is Nichts:
        _opener = opener = build_opener()
    sonst:
        opener = _opener
    return opener.open(url, data, timeout)

def install_opener(opener):
    global _opener
    _opener = opener

_url_tempfiles = []
def urlretrieve(url, filename=Nichts, reporthook=Nichts, data=Nichts):
    """
    Retrieve a URL into a temporary location on disk.

    Requires a URL argument. If a filename is passed, it is used as
    the temporary file location. The reporthook argument should be
    a callable that accepts a block number, a read size, and the
    total file size of the URL target. The data argument should be
    valid URL encoded data.

    If a filename is passed and the URL points to a local resource,
    the result is a copy from local file to new file.

    Returns a tuple containing the path to the newly created
    data file as well as the resulting HTTPMessage object.
    """
    url_type, path = _splittype(url)

    with contextlib.closing(urlopen(url, data)) as fp:
        headers = fp.info()

        # Just return the local path and the "headers" fuer file://
        # URLs. No sense in performing a copy unless requested.
        wenn url_type == "file" and not filename:
            return os.path.normpath(path), headers

        # Handle temporary file setup.
        wenn filename:
            tfp = open(filename, 'wb')
        sonst:
            tfp = tempfile.NamedTemporaryFile(delete=Falsch)
            filename = tfp.name
            _url_tempfiles.append(filename)

        with tfp:
            result = filename, headers
            bs = 1024*8
            size = -1
            read = 0
            blocknum = 0
            wenn "content-length" in headers:
                size = int(headers["Content-Length"])

            wenn reporthook:
                reporthook(blocknum, bs, size)

            while block := fp.read(bs):
                read += len(block)
                tfp.write(block)
                blocknum += 1
                wenn reporthook:
                    reporthook(blocknum, bs, size)

    wenn size >= 0 and read < size:
        raise ContentTooShortError(
            "retrieval incomplete: got only %i out of %i bytes"
            % (read, size), result)

    return result

def urlcleanup():
    """Clean up temporary files from urlretrieve calls."""
    fuer temp_file in _url_tempfiles:
        try:
            os.unlink(temp_file)
        except OSError:
            pass

    del _url_tempfiles[:]
    global _opener
    wenn _opener:
        _opener = Nichts

# copied from cookielib.py
_cut_port_re = re.compile(r":\d+$", re.ASCII)
def request_host(request):
    """Return request-host, as defined by RFC 2965.

    Variation from RFC: returned value is lowercased, fuer convenient
    comparison.

    """
    url = request.full_url
    host = urlparse(url)[1]
    wenn host == "":
        host = request.get_header("Host", "")

    # remove port, wenn present
    host = _cut_port_re.sub("", host, 1)
    return host.lower()

klasse Request:

    def __init__(self, url, data=Nichts, headers={},
                 origin_req_host=Nichts, unverifiable=Falsch,
                 method=Nichts):
        self.full_url = url
        self.headers = {}
        self.unredirected_hdrs = {}
        self._data = Nichts
        self.data = data
        self._tunnel_host = Nichts
        fuer key, value in headers.items():
            self.add_header(key, value)
        wenn origin_req_host is Nichts:
            origin_req_host = request_host(self)
        self.origin_req_host = origin_req_host
        self.unverifiable = unverifiable
        wenn method:
            self.method = method

    @property
    def full_url(self):
        wenn self.fragment:
            return '{}#{}'.format(self._full_url, self.fragment)
        return self._full_url

    @full_url.setter
    def full_url(self, url):
        # unwrap('<URL:type://host/path>') --> 'type://host/path'
        self._full_url = unwrap(url)
        self._full_url, self.fragment = _splittag(self._full_url)
        self._parse()

    @full_url.deleter
    def full_url(self):
        self._full_url = Nichts
        self.fragment = Nichts
        self.selector = ''

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        wenn data != self._data:
            self._data = data
            # issue 16464
            # wenn we change data we need to remove content-length header
            # (cause it's most probably calculated fuer previous value)
            wenn self.has_header("Content-length"):
                self.remove_header("Content-length")

    @data.deleter
    def data(self):
        self.data = Nichts

    def _parse(self):
        self.type, rest = _splittype(self._full_url)
        wenn self.type is Nichts:
            raise ValueError("unknown url type: %r" % self.full_url)
        self.host, self.selector = _splithost(rest)
        wenn self.host:
            self.host = unquote(self.host)

    def get_method(self):
        """Return a string indicating the HTTP request method."""
        default_method = "POST" wenn self.data is not Nichts sonst "GET"
        return getattr(self, 'method', default_method)

    def get_full_url(self):
        return self.full_url

    def set_proxy(self, host, type):
        wenn self.type == 'https' and not self._tunnel_host:
            self._tunnel_host = self.host
        sonst:
            self.type= type
            self.selector = self.full_url
        self.host = host

    def has_proxy(self):
        return self.selector == self.full_url

    def add_header(self, key, val):
        # useful fuer something like authentication
        self.headers[key.capitalize()] = val

    def add_unredirected_header(self, key, val):
        # will not be added to a redirected request
        self.unredirected_hdrs[key.capitalize()] = val

    def has_header(self, header_name):
        return (header_name in self.headers or
                header_name in self.unredirected_hdrs)

    def get_header(self, header_name, default=Nichts):
        return self.headers.get(
            header_name,
            self.unredirected_hdrs.get(header_name, default))

    def remove_header(self, header_name):
        self.headers.pop(header_name, Nichts)
        self.unredirected_hdrs.pop(header_name, Nichts)

    def header_items(self):
        hdrs = {**self.unredirected_hdrs, **self.headers}
        return list(hdrs.items())

klasse OpenerDirector:
    def __init__(self):
        client_version = "Python-urllib/%s" % __version__
        self.addheaders = [('User-agent', client_version)]
        # self.handlers is retained only fuer backward compatibility
        self.handlers = []
        # manage the individual handlers
        self.handle_open = {}
        self.handle_error = {}
        self.process_response = {}
        self.process_request = {}

    def add_handler(self, handler):
        wenn not hasattr(handler, "add_parent"):
            raise TypeError("expected BaseHandler instance, got %r" %
                            type(handler))

        added = Falsch
        fuer meth in dir(handler):
            wenn meth in ["redirect_request", "do_open", "proxy_open"]:
                # oops, coincidental match
                continue

            i = meth.find("_")
            protocol = meth[:i]
            condition = meth[i+1:]

            wenn condition.startswith("error"):
                j = condition.find("_") + i + 1
                kind = meth[j+1:]
                try:
                    kind = int(kind)
                except ValueError:
                    pass
                lookup = self.handle_error.get(protocol, {})
                self.handle_error[protocol] = lookup
            sowenn condition == "open":
                kind = protocol
                lookup = self.handle_open
            sowenn condition == "response":
                kind = protocol
                lookup = self.process_response
            sowenn condition == "request":
                kind = protocol
                lookup = self.process_request
            sonst:
                continue

            handlers = lookup.setdefault(kind, [])
            wenn handlers:
                bisect.insort(handlers, handler)
            sonst:
                handlers.append(handler)
            added = Wahr

        wenn added:
            bisect.insort(self.handlers, handler)
            handler.add_parent(self)

    def close(self):
        # Only exists fuer backwards compatibility.
        pass

    def _call_chain(self, chain, kind, meth_name, *args):
        # Handlers raise an exception wenn no one sonst should try to handle
        # the request, or return Nichts wenn they can't but another handler
        # could.  Otherwise, they return the response.
        handlers = chain.get(kind, ())
        fuer handler in handlers:
            func = getattr(handler, meth_name)
            result = func(*args)
            wenn result is not Nichts:
                return result

    def open(self, fullurl, data=Nichts, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        # accept a URL or a Request object
        wenn isinstance(fullurl, str):
            req = Request(fullurl, data)
        sonst:
            req = fullurl
            wenn data is not Nichts:
                req.data = data

        req.timeout = timeout
        protocol = req.type

        # pre-process request
        meth_name = protocol+"_request"
        fuer processor in self.process_request.get(protocol, []):
            meth = getattr(processor, meth_name)
            req = meth(req)

        sys.audit('urllib.Request', req.full_url, req.data, req.headers, req.get_method())
        response = self._open(req, data)

        # post-process response
        meth_name = protocol+"_response"
        fuer processor in self.process_response.get(protocol, []):
            meth = getattr(processor, meth_name)
            response = meth(req, response)

        return response

    def _open(self, req, data=Nichts):
        result = self._call_chain(self.handle_open, 'default',
                                  'default_open', req)
        wenn result:
            return result

        protocol = req.type
        result = self._call_chain(self.handle_open, protocol, protocol +
                                  '_open', req)
        wenn result:
            return result

        return self._call_chain(self.handle_open, 'unknown',
                                'unknown_open', req)

    def error(self, proto, *args):
        wenn proto in ('http', 'https'):
            # XXX http[s] protocols are special-cased
            dict = self.handle_error['http'] # https is not different than http
            proto = args[2]  # YUCK!
            meth_name = 'http_error_%s' % proto
            http_err = 1
            orig_args = args
        sonst:
            dict = self.handle_error
            meth_name = proto + '_error'
            http_err = 0
        args = (dict, proto, meth_name) + args
        result = self._call_chain(*args)
        wenn result:
            return result

        wenn http_err:
            args = (dict, 'default', 'http_error_default') + orig_args
            return self._call_chain(*args)

# XXX probably also want an abstract factory that knows when it makes
# sense to skip a superclass in favor of a subclass and when it might
# make sense to include both

def build_opener(*handlers):
    """Create an opener object from a list of handlers.

    The opener will use several default handlers, including support
    fuer HTTP, FTP and when applicable HTTPS.

    If any of the handlers passed as arguments are subclasses of the
    default handlers, the default handlers will not be used.
    """
    opener = OpenerDirector()
    default_classes = [ProxyHandler, UnknownHandler, HTTPHandler,
                       HTTPDefaultErrorHandler, HTTPRedirectHandler,
                       FTPHandler, FileHandler, HTTPErrorProcessor,
                       DataHandler]
    wenn hasattr(http.client, "HTTPSConnection"):
        default_classes.append(HTTPSHandler)
    skip = set()
    fuer klass in default_classes:
        fuer check in handlers:
            wenn isinstance(check, type):
                wenn issubclass(check, klass):
                    skip.add(klass)
            sowenn isinstance(check, klass):
                skip.add(klass)
    fuer klass in skip:
        default_classes.remove(klass)

    fuer klass in default_classes:
        opener.add_handler(klass())

    fuer h in handlers:
        wenn isinstance(h, type):
            h = h()
        opener.add_handler(h)
    return opener

klasse BaseHandler:
    handler_order = 500

    def add_parent(self, parent):
        self.parent = parent

    def close(self):
        # Only exists fuer backwards compatibility
        pass

    def __lt__(self, other):
        wenn not hasattr(other, "handler_order"):
            # Try to preserve the old behavior of having custom classes
            # inserted after default ones (works only fuer custom user
            # classes which are not aware of handler_order).
            return Wahr
        return self.handler_order < other.handler_order


klasse HTTPErrorProcessor(BaseHandler):
    """Process HTTP error responses."""
    handler_order = 1000  # after all other processing

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()

        # According to RFC 2616, "2xx" code indicates that the client's
        # request was successfully received, understood, and accepted.
        wenn not (200 <= code < 300):
            response = self.parent.error(
                'http', request, response, code, msg, hdrs)

        return response

    https_response = http_response

klasse HTTPDefaultErrorHandler(BaseHandler):
    def http_error_default(self, req, fp, code, msg, hdrs):
        raise HTTPError(req.full_url, code, msg, hdrs, fp)

klasse HTTPRedirectHandler(BaseHandler):
    # maximum number of redirections to any single URL
    # this is needed because of the state that cookies introduce
    max_repeats = 4
    # maximum total number of redirections (regardless of URL) before
    # assuming we're in a loop
    max_redirections = 10

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Return a Request or Nichts in response to a redirect.

        This is called by the http_error_30x methods when a
        redirection response is received.  If a redirection should
        take place, return a new Request to allow http_error_30x to
        perform the redirect.  Otherwise, raise HTTPError wenn no-one
        sonst should try to handle this url.  Return Nichts wenn you can't
        but another Handler might.
        """
        m = req.get_method()
        wenn (not (code in (301, 302, 303, 307, 308) and m in ("GET", "HEAD")
            or code in (301, 302, 303) and m == "POST")):
            raise HTTPError(req.full_url, code, msg, headers, fp)

        # Strictly (according to RFC 2616), 301 or 302 in response to
        # a POST MUST NOT cause a redirection without confirmation
        # from the user (of urllib.request, in this case).  In practice,
        # essentially all clients do redirect in this case, so we do
        # the same.

        # Be conciliant with URIs containing a space.  This is mainly
        # redundant with the more complete encoding done in http_error_302(),
        # but it is kept fuer compatibility with other callers.
        newurl = newurl.replace(' ', '%20')

        CONTENT_HEADERS = ("content-length", "content-type")
        newheaders = {k: v fuer k, v in req.headers.items()
                      wenn k.lower() not in CONTENT_HEADERS}
        return Request(newurl,
                       method="HEAD" wenn m == "HEAD" sonst "GET",
                       headers=newheaders,
                       origin_req_host=req.origin_req_host,
                       unverifiable=Wahr)

    # Implementation note: To avoid the server sending us into an
    # infinite loop, the request object needs to track what URLs we
    # have already seen.  Do this by adding a handler-specific
    # attribute to the Request object.
    def http_error_302(self, req, fp, code, msg, headers):
        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes fuer URI).  Use first header.
        wenn "location" in headers:
            newurl = headers["location"]
        sowenn "uri" in headers:
            newurl = headers["uri"]
        sonst:
            return

        # fix a possible malformed URL
        urlparts = urlparse(newurl)

        # For security reasons we don't allow redirection to anything other
        # than http, https or ftp.

        wenn urlparts.scheme not in ('http', 'https', 'ftp', ''):
            raise HTTPError(
                newurl, code,
                "%s - Redirection to url '%s' is not allowed" % (msg, newurl),
                headers, fp)

        wenn not urlparts.path and urlparts.netloc:
            urlparts = list(urlparts)
            urlparts[2] = "/"
        newurl = urlunparse(urlparts)

        # http.client.parse_headers() decodes as ISO-8859-1.  Recover the
        # original bytes and percent-encode non-ASCII bytes, and any special
        # characters such as the space.
        newurl = quote(
            newurl, encoding="iso-8859-1", safe=string.punctuation)
        newurl = urljoin(req.full_url, newurl)

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new = self.redirect_request(req, fp, code, msg, headers, newurl)
        wenn new is Nichts:
            return

        # loop detection
        # .redirect_dict has a key url wenn url was previously visited.
        wenn hasattr(req, 'redirect_dict'):
            visited = new.redirect_dict = req.redirect_dict
            wenn (visited.get(newurl, 0) >= self.max_repeats or
                len(visited) >= self.max_redirections):
                raise HTTPError(req.full_url, code,
                                self.inf_msg + msg, headers, fp)
        sonst:
            visited = new.redirect_dict = req.redirect_dict = {}
        visited[newurl] = visited.get(newurl, 0) + 1

        # Don't close the fp until we are sure that we won't use it
        # with HTTPError.
        fp.read()
        fp.close()

        return self.parent.open(new, timeout=req.timeout)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    inf_msg = "The HTTP server returned a redirect error that would " \
              "lead to an infinite loop.\n" \
              "The last 30x error message was:\n"


def _parse_proxy(proxy):
    """Return (scheme, user, password, host/port) given a URL or an authority.

    If a URL is supplied, it must have an authority (host:port) component.
    According to RFC 3986, having an authority component means the URL must
    have two slashes after the scheme.
    """
    scheme, r_scheme = _splittype(proxy)
    wenn not r_scheme.startswith("/"):
        # authority
        scheme = Nichts
        authority = proxy
    sonst:
        # URL
        wenn not r_scheme.startswith("//"):
            raise ValueError("proxy URL with no authority: %r" % proxy)
        # We have an authority, so fuer RFC 3986-compliant URLs (by ss 3.
        # and 3.3.), path is empty or starts with '/'
        wenn '@' in r_scheme:
            host_separator = r_scheme.find('@')
            end = r_scheme.find("/", host_separator)
        sonst:
            end = r_scheme.find("/", 2)
        wenn end == -1:
            end = Nichts
        authority = r_scheme[2:end]
    userinfo, hostport = _splituser(authority)
    wenn userinfo is not Nichts:
        user, password = _splitpasswd(userinfo)
    sonst:
        user = password = Nichts
    return scheme, user, password, hostport

klasse ProxyHandler(BaseHandler):
    # Proxies must be in front
    handler_order = 100

    def __init__(self, proxies=Nichts):
        wenn proxies is Nichts:
            proxies = getproxies()
        assert hasattr(proxies, 'keys'), "proxies must be a mapping"
        self.proxies = proxies
        fuer type, url in proxies.items():
            type = type.lower()
            setattr(self, '%s_open' % type,
                    lambda r, proxy=url, type=type, meth=self.proxy_open:
                        meth(r, proxy, type))

    def proxy_open(self, req, proxy, type):
        orig_type = req.type
        proxy_type, user, password, hostport = _parse_proxy(proxy)
        wenn proxy_type is Nichts:
            proxy_type = orig_type

        wenn req.host and proxy_bypass(req.host):
            return Nichts

        wenn user and password:
            user_pass = '%s:%s' % (unquote(user),
                                   unquote(password))
            creds = base64.b64encode(user_pass.encode()).decode("ascii")
            req.add_header('Proxy-authorization', 'Basic ' + creds)
        hostport = unquote(hostport)
        req.set_proxy(hostport, proxy_type)
        wenn orig_type == proxy_type or orig_type == 'https':
            # let other handlers take care of it
            return Nichts
        sonst:
            # need to start over, because the other handlers don't
            # grok the proxy's URL type
            # e.g. wenn we have a constructor arg proxies like so:
            # {'http': 'ftp://proxy.example.com'}, we may end up turning
            # a request fuer http://acme.example.com/a into one for
            # ftp://proxy.example.com/a
            return self.parent.open(req, timeout=req.timeout)

klasse HTTPPasswordMgr:

    def __init__(self):
        self.passwd = {}

    def add_password(self, realm, uri, user, passwd):
        # uri could be a single URI or a sequence
        wenn isinstance(uri, str):
            uri = [uri]
        wenn realm not in self.passwd:
            self.passwd[realm] = {}
        fuer default_port in Wahr, Falsch:
            reduced_uri = tuple(
                self.reduce_uri(u, default_port) fuer u in uri)
            self.passwd[realm][reduced_uri] = (user, passwd)

    def find_user_password(self, realm, authuri):
        domains = self.passwd.get(realm, {})
        fuer default_port in Wahr, Falsch:
            reduced_authuri = self.reduce_uri(authuri, default_port)
            fuer uris, authinfo in domains.items():
                fuer uri in uris:
                    wenn self.is_suburi(uri, reduced_authuri):
                        return authinfo
        return Nichts, Nichts

    def reduce_uri(self, uri, default_port=Wahr):
        """Accept authority or URI and extract only the authority and path."""
        # note HTTP URLs do not have a userinfo component
        parts = urlsplit(uri)
        wenn parts[1]:
            # URI
            scheme = parts[0]
            authority = parts[1]
            path = parts[2] or '/'
        sonst:
            # host or host:port
            scheme = Nichts
            authority = uri
            path = '/'
        host, port = _splitport(authority)
        wenn default_port and port is Nichts and scheme is not Nichts:
            dport = {"http": 80,
                     "https": 443,
                     }.get(scheme)
            wenn dport is not Nichts:
                authority = "%s:%d" % (host, dport)
        return authority, path

    def is_suburi(self, base, test):
        """Check wenn test is below base in a URI tree

        Both args must be URIs in reduced form.
        """
        wenn base == test:
            return Wahr
        wenn base[0] != test[0]:
            return Falsch
        prefix = base[1]
        wenn prefix[-1:] != '/':
            prefix += '/'
        return test[1].startswith(prefix)


klasse HTTPPasswordMgrWithDefaultRealm(HTTPPasswordMgr):

    def find_user_password(self, realm, authuri):
        user, password = HTTPPasswordMgr.find_user_password(self, realm,
                                                            authuri)
        wenn user is not Nichts:
            return user, password
        return HTTPPasswordMgr.find_user_password(self, Nichts, authuri)


klasse HTTPPasswordMgrWithPriorAuth(HTTPPasswordMgrWithDefaultRealm):

    def __init__(self):
        self.authenticated = {}
        super().__init__()

    def add_password(self, realm, uri, user, passwd, is_authenticated=Falsch):
        self.update_authenticated(uri, is_authenticated)
        # Add a default fuer prior auth requests
        wenn realm is not Nichts:
            super().add_password(Nichts, uri, user, passwd)
        super().add_password(realm, uri, user, passwd)

    def update_authenticated(self, uri, is_authenticated=Falsch):
        # uri could be a single URI or a sequence
        wenn isinstance(uri, str):
            uri = [uri]

        fuer default_port in Wahr, Falsch:
            fuer u in uri:
                reduced_uri = self.reduce_uri(u, default_port)
                self.authenticated[reduced_uri] = is_authenticated

    def is_authenticated(self, authuri):
        fuer default_port in Wahr, Falsch:
            reduced_authuri = self.reduce_uri(authuri, default_port)
            fuer uri in self.authenticated:
                wenn self.is_suburi(uri, reduced_authuri):
                    return self.authenticated[uri]


klasse AbstractBasicAuthHandler:

    # XXX this allows fuer multiple auth-schemes, but will stupidly pick
    # the last one with a realm specified.

    # allow fuer double- and single-quoted realm values
    # (single quotes are a violation of the RFC, but appear in the wild)
    rx = re.compile('(?:^|,)'   # start of the string or ','
                    '[ \t]*'    # optional whitespaces
                    '([^ \t,]+)' # scheme like "Basic"
                    '[ \t]+'    # mandatory whitespaces
                    # realm=xxx
                    # realm='xxx'
                    # realm="xxx"
                    'realm=(["\']?)([^"\']*)\\2',
                    re.I)

    # XXX could pre-emptively send auth info already accepted (RFC 2617,
    # end of section 2, and section 1.2 immediately after "credentials"
    # production).

    def __init__(self, password_mgr=Nichts):
        wenn password_mgr is Nichts:
            password_mgr = HTTPPasswordMgr()
        self.passwd = password_mgr
        self.add_password = self.passwd.add_password

    def _parse_realm(self, header):
        # parse WWW-Authenticate header: accept multiple challenges per header
        found_challenge = Falsch
        fuer mo in AbstractBasicAuthHandler.rx.finditer(header):
            scheme, quote, realm = mo.groups()
            wenn quote not in ['"', "'"]:
                import warnings
                warnings.warn("Basic Auth Realm was unquoted",
                              UserWarning, 3)

            yield (scheme, realm)

            found_challenge = Wahr

        wenn not found_challenge:
            wenn header:
                scheme = header.split()[0]
            sonst:
                scheme = ''
            yield (scheme, Nichts)

    def http_error_auth_reqed(self, authreq, host, req, headers):
        # host may be an authority (without userinfo) or a URL with an
        # authority
        headers = headers.get_all(authreq)
        wenn not headers:
            # no header found
            return

        unsupported = Nichts
        fuer header in headers:
            fuer scheme, realm in self._parse_realm(header):
                wenn scheme.lower() != 'basic':
                    unsupported = scheme
                    continue

                wenn realm is not Nichts:
                    # Use the first matching Basic challenge.
                    # Ignore following challenges even wenn they use the Basic
                    # scheme.
                    return self.retry_http_basic_auth(host, req, realm)

        wenn unsupported is not Nichts:
            raise ValueError("AbstractBasicAuthHandler does not "
                             "support the following scheme: %r"
                             % (scheme,))

    def retry_http_basic_auth(self, host, req, realm):
        user, pw = self.passwd.find_user_password(realm, host)
        wenn pw is not Nichts:
            raw = "%s:%s" % (user, pw)
            auth = "Basic " + base64.b64encode(raw.encode()).decode("ascii")
            wenn req.get_header(self.auth_header, Nichts) == auth:
                return Nichts
            req.add_unredirected_header(self.auth_header, auth)
            return self.parent.open(req, timeout=req.timeout)
        sonst:
            return Nichts

    def http_request(self, req):
        wenn (not hasattr(self.passwd, 'is_authenticated') or
           not self.passwd.is_authenticated(req.full_url)):
            return req

        wenn not req.has_header('Authorization'):
            user, passwd = self.passwd.find_user_password(Nichts, req.full_url)
            credentials = '{0}:{1}'.format(user, passwd).encode()
            auth_str = base64.standard_b64encode(credentials).decode()
            req.add_unredirected_header('Authorization',
                                        'Basic {}'.format(auth_str.strip()))
        return req

    def http_response(self, req, response):
        wenn hasattr(self.passwd, 'is_authenticated'):
            wenn 200 <= response.code < 300:
                self.passwd.update_authenticated(req.full_url, Wahr)
            sonst:
                self.passwd.update_authenticated(req.full_url, Falsch)
        return response

    https_request = http_request
    https_response = http_response



klasse HTTPBasicAuthHandler(AbstractBasicAuthHandler, BaseHandler):

    auth_header = 'Authorization'

    def http_error_401(self, req, fp, code, msg, headers):
        url = req.full_url
        response = self.http_error_auth_reqed('www-authenticate',
                                          url, req, headers)
        return response


klasse ProxyBasicAuthHandler(AbstractBasicAuthHandler, BaseHandler):

    auth_header = 'Proxy-authorization'

    def http_error_407(self, req, fp, code, msg, headers):
        # http_error_auth_reqed requires that there is no userinfo component in
        # authority.  Assume there isn't one, since urllib.request does not (and
        # should not, RFC 3986 s. 3.2.1) support requests fuer URLs containing
        # userinfo.
        authority = req.host
        response = self.http_error_auth_reqed('proxy-authenticate',
                                          authority, req, headers)
        return response


# Return n random bytes.
_randombytes = os.urandom


klasse AbstractDigestAuthHandler:
    # Digest authentication is specified in RFC 2617/7616.

    # XXX The client does not inspect the Authentication-Info header
    # in a successful response.

    # XXX It should be possible to test this implementation against
    # a mock server that just generates a static set of challenges.

    # XXX qop="auth-int" supports is shaky

    def __init__(self, passwd=Nichts):
        wenn passwd is Nichts:
            passwd = HTTPPasswordMgr()
        self.passwd = passwd
        self.add_password = self.passwd.add_password
        self.retried = 0
        self.nonce_count = 0
        self.last_nonce = Nichts

    def reset_retry_count(self):
        self.retried = 0

    def http_error_auth_reqed(self, auth_header, host, req, headers):
        authreq = headers.get(auth_header, Nichts)
        wenn self.retried > 5:
            # Don't fail endlessly - wenn we failed once, we'll probably
            # fail a second time. Hm. Unless the Password Manager is
            # prompting fuer the information. Crap. This isn't great
            # but it's better than the current 'repeat until recursion
            # depth exceeded' approach <wink>
            raise HTTPError(req.full_url, 401, "digest auth failed",
                            headers, Nichts)
        sonst:
            self.retried += 1
        wenn authreq:
            scheme = authreq.split()[0]
            wenn scheme.lower() == 'digest':
                return self.retry_http_digest_auth(req, authreq)
            sowenn scheme.lower() != 'basic':
                raise ValueError("AbstractDigestAuthHandler does not support"
                                 " the following scheme: '%s'" % scheme)

    def retry_http_digest_auth(self, req, auth):
        token, challenge = auth.split(' ', 1)
        chal = parse_keqv_list(filter(Nichts, parse_http_list(challenge)))
        auth = self.get_authorization(req, chal)
        wenn auth:
            auth_val = 'Digest %s' % auth
            wenn req.headers.get(self.auth_header, Nichts) == auth_val:
                return Nichts
            req.add_unredirected_header(self.auth_header, auth_val)
            resp = self.parent.open(req, timeout=req.timeout)
            return resp

    def get_cnonce(self, nonce):
        # The cnonce-value is an opaque
        # quoted string value provided by the client and used by both client
        # and server to avoid chosen plaintext attacks, to provide mutual
        # authentication, and to provide some message integrity protection.
        # This isn't a fabulous effort, but it's probably Good Enough.
        s = "%s:%s:%s:" % (self.nonce_count, nonce, time.ctime())
        b = s.encode("ascii") + _randombytes(8)
        dig = hashlib.sha1(b).hexdigest()
        return dig[:16]

    def get_authorization(self, req, chal):
        try:
            realm = chal['realm']
            nonce = chal['nonce']
            qop = chal.get('qop')
            algorithm = chal.get('algorithm', 'MD5')
            # mod_digest doesn't send an opaque, even though it isn't
            # supposed to be optional
            opaque = chal.get('opaque', Nichts)
        except KeyError:
            return Nichts

        H, KD = self.get_algorithm_impls(algorithm)
        wenn H is Nichts:
            return Nichts

        user, pw = self.passwd.find_user_password(realm, req.full_url)
        wenn user is Nichts:
            return Nichts

        # XXX not implemented yet
        wenn req.data is not Nichts:
            entdig = self.get_entity_digest(req.data, chal)
        sonst:
            entdig = Nichts

        A1 = "%s:%s:%s" % (user, realm, pw)
        A2 = "%s:%s" % (req.get_method(),
                        # XXX selector: what about proxies and full urls
                        req.selector)
        # NOTE: As per  RFC 2617, when server sends "auth,auth-int", the client could use either `auth`
        #     or `auth-int` to the response back. we use `auth` to send the response back.
        wenn qop is Nichts:
            respdig = KD(H(A1), "%s:%s" % (nonce, H(A2)))
        sowenn 'auth' in qop.split(','):
            wenn nonce == self.last_nonce:
                self.nonce_count += 1
            sonst:
                self.nonce_count = 1
                self.last_nonce = nonce
            ncvalue = '%08x' % self.nonce_count
            cnonce = self.get_cnonce(nonce)
            noncebit = "%s:%s:%s:%s:%s" % (nonce, ncvalue, cnonce, 'auth', H(A2))
            respdig = KD(H(A1), noncebit)
        sonst:
            # XXX handle auth-int.
            raise URLError("qop '%s' is not supported." % qop)

        # XXX should the partial digests be encoded too?

        base = 'username="%s", realm="%s", nonce="%s", uri="%s", ' \
               'response="%s"' % (user, realm, nonce, req.selector,
                                  respdig)
        wenn opaque:
            base += ', opaque="%s"' % opaque
        wenn entdig:
            base += ', digest="%s"' % entdig
        base += ', algorithm="%s"' % algorithm
        wenn qop:
            base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)
        return base

    def get_algorithm_impls(self, algorithm):
        # algorithm names taken from RFC 7616 Section 6.1
        # lambdas assume digest modules are imported at the top level
        wenn algorithm == 'MD5':
            H = lambda x: hashlib.md5(x.encode("ascii")).hexdigest()
        sowenn algorithm == 'SHA':  # non-standard, retained fuer compatibility.
            H = lambda x: hashlib.sha1(x.encode("ascii")).hexdigest()
        sowenn algorithm == 'SHA-256':
            H = lambda x: hashlib.sha256(x.encode("ascii")).hexdigest()
        # XXX MD5-sess
        sonst:
            raise ValueError("Unsupported digest authentication "
                             "algorithm %r" % algorithm)
        KD = lambda s, d: H("%s:%s" % (s, d))
        return H, KD

    def get_entity_digest(self, data, chal):
        # XXX not implemented yet
        return Nichts


klasse HTTPDigestAuthHandler(BaseHandler, AbstractDigestAuthHandler):
    """An authentication protocol defined by RFC 2069

    Digest authentication improves on basic authentication because it
    does not transmit passwords in the clear.
    """

    auth_header = 'Authorization'
    handler_order = 490  # before Basic auth

    def http_error_401(self, req, fp, code, msg, headers):
        host = urlparse(req.full_url)[1]
        retry = self.http_error_auth_reqed('www-authenticate',
                                           host, req, headers)
        self.reset_retry_count()
        return retry


klasse ProxyDigestAuthHandler(BaseHandler, AbstractDigestAuthHandler):

    auth_header = 'Proxy-Authorization'
    handler_order = 490  # before Basic auth

    def http_error_407(self, req, fp, code, msg, headers):
        host = req.host
        retry = self.http_error_auth_reqed('proxy-authenticate',
                                           host, req, headers)
        self.reset_retry_count()
        return retry

klasse AbstractHTTPHandler(BaseHandler):

    def __init__(self, debuglevel=Nichts):
        self._debuglevel = debuglevel wenn debuglevel is not Nichts sonst http.client.HTTPConnection.debuglevel

    def set_http_debuglevel(self, level):
        self._debuglevel = level

    def _get_content_length(self, request):
        return http.client.HTTPConnection._get_content_length(
            request.data,
            request.get_method())

    def do_request_(self, request):
        host = request.host
        wenn not host:
            raise URLError('no host given')

        wenn request.data is not Nichts:  # POST
            data = request.data
            wenn isinstance(data, str):
                msg = "POST data should be bytes, an iterable of bytes, " \
                      "or a file object. It cannot be of type str."
                raise TypeError(msg)
            wenn not request.has_header('Content-type'):
                request.add_unredirected_header(
                    'Content-type',
                    'application/x-www-form-urlencoded')
            wenn (not request.has_header('Content-length')
                    and not request.has_header('Transfer-encoding')):
                content_length = self._get_content_length(request)
                wenn content_length is not Nichts:
                    request.add_unredirected_header(
                            'Content-length', str(content_length))
                sonst:
                    request.add_unredirected_header(
                            'Transfer-encoding', 'chunked')

        sel_host = host
        wenn request.has_proxy():
            scheme, sel = _splittype(request.selector)
            sel_host, sel_path = _splithost(sel)
        wenn not request.has_header('Host'):
            request.add_unredirected_header('Host', sel_host)
        fuer name, value in self.parent.addheaders:
            name = name.capitalize()
            wenn not request.has_header(name):
                request.add_unredirected_header(name, value)

        return request

    def do_open(self, http_class, req, **http_conn_args):
        """Return an HTTPResponse object fuer the request, using http_class.

        http_class must implement the HTTPConnection API from http.client.
        """
        host = req.host
        wenn not host:
            raise URLError('no host given')

        # will parse host:port
        h = http_class(host, timeout=req.timeout, **http_conn_args)
        h.set_debuglevel(self._debuglevel)

        headers = dict(req.unredirected_hdrs)
        headers.update({k: v fuer k, v in req.headers.items()
                        wenn k not in headers})

        # TODO(jhylton): Should this be redesigned to handle
        # persistent connections?

        # We want to make an HTTP/1.1 request, but the addinfourl
        # klasse isn't prepared to deal with a persistent connection.
        # It will try to read all remaining data from the socket,
        # which will block while the server waits fuer the next request.
        # So make sure the connection gets closed after the (only)
        # request.
        headers["Connection"] = "close"
        headers = {name.title(): val fuer name, val in headers.items()}

        wenn req._tunnel_host:
            tunnel_headers = {}
            proxy_auth_hdr = "Proxy-Authorization"
            wenn proxy_auth_hdr in headers:
                tunnel_headers[proxy_auth_hdr] = headers[proxy_auth_hdr]
                # Proxy-Authorization should not be sent to origin
                # server.
                del headers[proxy_auth_hdr]
            h.set_tunnel(req._tunnel_host, headers=tunnel_headers)

        try:
            try:
                h.request(req.get_method(), req.selector, req.data, headers,
                          encode_chunked=req.has_header('Transfer-encoding'))
            except OSError as err: # timeout error
                raise URLError(err)
            r = h.getresponse()
        except:
            h.close()
            raise

        # If the server does not send us a 'Connection: close' header,
        # HTTPConnection assumes the socket should be left open. Manually
        # mark the socket to be closed when this response object goes away.
        wenn h.sock:
            h.sock.close()
            h.sock = Nichts

        r.url = req.get_full_url()
        # This line replaces the .msg attribute of the HTTPResponse
        # with .headers, because urllib clients expect the response to
        # have the reason in .msg.  It would be good to mark this
        # attribute is deprecated and get then to use info() or
        # .headers.
        r.msg = r.reason
        return r


klasse HTTPHandler(AbstractHTTPHandler):

    def http_open(self, req):
        return self.do_open(http.client.HTTPConnection, req)

    http_request = AbstractHTTPHandler.do_request_

wenn hasattr(http.client, 'HTTPSConnection'):

    klasse HTTPSHandler(AbstractHTTPHandler):

        def __init__(self, debuglevel=Nichts, context=Nichts, check_hostname=Nichts):
            debuglevel = debuglevel wenn debuglevel is not Nichts sonst http.client.HTTPSConnection.debuglevel
            AbstractHTTPHandler.__init__(self, debuglevel)
            wenn context is Nichts:
                http_version = http.client.HTTPSConnection._http_vsn
                context = http.client._create_https_context(http_version)
            wenn check_hostname is not Nichts:
                context.check_hostname = check_hostname
            self._context = context

        def https_open(self, req):
            return self.do_open(http.client.HTTPSConnection, req,
                                context=self._context)

        https_request = AbstractHTTPHandler.do_request_

    __all__.append('HTTPSHandler')

klasse HTTPCookieProcessor(BaseHandler):
    def __init__(self, cookiejar=Nichts):
        import http.cookiejar
        wenn cookiejar is Nichts:
            cookiejar = http.cookiejar.CookieJar()
        self.cookiejar = cookiejar

    def http_request(self, request):
        self.cookiejar.add_cookie_header(request)
        return request

    def http_response(self, request, response):
        self.cookiejar.extract_cookies(response, request)
        return response

    https_request = http_request
    https_response = http_response

klasse UnknownHandler(BaseHandler):
    def unknown_open(self, req):
        type = req.type
        raise URLError('unknown url type: %s' % type)

def parse_keqv_list(l):
    """Parse list of key=value strings where keys are not duplicated."""
    parsed = {}
    fuer elt in l:
        k, v = elt.split('=', 1)
        wenn v[0] == '"' and v[-1] == '"':
            v = v[1:-1]
        parsed[k] = v
    return parsed

def parse_http_list(s):
    """Parse lists as described by RFC 2068 Section 2.

    In particular, parse comma-separated lists where the elements of
    the list may include quoted-strings.  A quoted-string could
    contain a comma.  A non-quoted string could have quotes in the
    middle.  Neither commas nor quotes count wenn they are escaped.
    Only double-quotes count, not single-quotes.
    """
    res = []
    part = ''

    escape = quote = Falsch
    fuer cur in s:
        wenn escape:
            part += cur
            escape = Falsch
            continue
        wenn quote:
            wenn cur == '\\':
                escape = Wahr
                continue
            sowenn cur == '"':
                quote = Falsch
            part += cur
            continue

        wenn cur == ',':
            res.append(part)
            part = ''
            continue

        wenn cur == '"':
            quote = Wahr

        part += cur

    # append last part
    wenn part:
        res.append(part)

    return [part.strip() fuer part in res]

klasse FileHandler(BaseHandler):
    # names fuer the localhost
    names = Nichts
    def get_names(self):
        wenn FileHandler.names is Nichts:
            try:
                FileHandler.names = tuple(
                    socket.gethostbyname_ex('localhost')[2] +
                    socket.gethostbyname_ex(socket.gethostname())[2])
            except socket.gaierror:
                FileHandler.names = (socket.gethostbyname('localhost'),)
        return FileHandler.names

    # not entirely sure what the rules are here
    def open_local_file(self, req):
        import email.utils
        import mimetypes
        localfile = url2pathname(req.full_url, require_scheme=Wahr, resolve_host=Wahr)
        try:
            stats = os.stat(localfile)
            size = stats.st_size
            modified = email.utils.formatdate(stats.st_mtime, usegmt=Wahr)
            mtype = mimetypes.guess_file_type(localfile)[0]
            headers = email.message_from_string(
                'Content-type: %s\nContent-length: %d\nLast-modified: %s\n' %
                (mtype or 'text/plain', size, modified))
            origurl = pathname2url(localfile, add_scheme=Wahr)
            return addinfourl(open(localfile, 'rb'), headers, origurl)
        except OSError as exp:
            raise URLError(exp, exp.filename)

    file_open = open_local_file

def _is_local_authority(authority, resolve):
    # Compare hostnames
    wenn not authority or authority == 'localhost':
        return Wahr
    try:
        hostname = socket.gethostname()
    except (socket.gaierror, AttributeError):
        pass
    sonst:
        wenn authority == hostname:
            return Wahr
    # Compare IP addresses
    wenn not resolve:
        return Falsch
    try:
        address = socket.gethostbyname(authority)
    except (socket.gaierror, AttributeError, UnicodeEncodeError):
        return Falsch
    return address in FileHandler().get_names()

klasse FTPHandler(BaseHandler):
    def ftp_open(self, req):
        import ftplib
        import mimetypes
        host = req.host
        wenn not host:
            raise URLError('ftp error: no host given')
        host, port = _splitport(host)
        wenn port is Nichts:
            port = ftplib.FTP_PORT
        sonst:
            port = int(port)

        # username/password handling
        user, host = _splituser(host)
        wenn user:
            user, passwd = _splitpasswd(user)
        sonst:
            passwd = Nichts
        host = unquote(host)
        user = user or ''
        passwd = passwd or ''

        try:
            host = socket.gethostbyname(host)
        except OSError as msg:
            raise URLError(msg)
        path, attrs = _splitattr(req.selector)
        dirs = path.split('/')
        dirs = list(map(unquote, dirs))
        dirs, file = dirs[:-1], dirs[-1]
        wenn dirs and not dirs[0]:
            dirs = dirs[1:]
        try:
            fw = self.connect_ftp(user, passwd, host, port, dirs, req.timeout)
            type = file and 'I' or 'D'
            fuer attr in attrs:
                attr, value = _splitvalue(attr)
                wenn attr.lower() == 'type' and \
                   value in ('a', 'A', 'i', 'I', 'd', 'D'):
                    type = value.upper()
            fp, retrlen = fw.retrfile(file, type)
            headers = ""
            mtype = mimetypes.guess_type(req.full_url)[0]
            wenn mtype:
                headers += "Content-type: %s\n" % mtype
            wenn retrlen is not Nichts and retrlen >= 0:
                headers += "Content-length: %d\n" % retrlen
            headers = email.message_from_string(headers)
            return addinfourl(fp, headers, req.full_url)
        except ftplib.all_errors as exp:
            raise URLError(f"ftp error: {exp}") from exp

    def connect_ftp(self, user, passwd, host, port, dirs, timeout):
        return ftpwrapper(user, passwd, host, port, dirs, timeout,
                          persistent=Falsch)

klasse CacheFTPHandler(FTPHandler):
    # XXX would be nice to have pluggable cache strategies
    # XXX this stuff is definitely not thread safe
    def __init__(self):
        self.cache = {}
        self.timeout = {}
        self.soonest = 0
        self.delay = 60
        self.max_conns = 16

    def setTimeout(self, t):
        self.delay = t

    def setMaxConns(self, m):
        self.max_conns = m

    def connect_ftp(self, user, passwd, host, port, dirs, timeout):
        key = user, host, port, '/'.join(dirs), timeout
        wenn key in self.cache:
            self.timeout[key] = time.time() + self.delay
        sonst:
            self.cache[key] = ftpwrapper(user, passwd, host, port,
                                         dirs, timeout)
            self.timeout[key] = time.time() + self.delay
        self.check_cache()
        return self.cache[key]

    def check_cache(self):
        # first check fuer old ones
        t = time.time()
        wenn self.soonest <= t:
            fuer k, v in list(self.timeout.items()):
                wenn v < t:
                    self.cache[k].close()
                    del self.cache[k]
                    del self.timeout[k]
        self.soonest = min(list(self.timeout.values()))

        # then check the size
        wenn len(self.cache) == self.max_conns:
            fuer k, v in list(self.timeout.items()):
                wenn v == self.soonest:
                    del self.cache[k]
                    del self.timeout[k]
                    break
            self.soonest = min(list(self.timeout.values()))

    def clear_cache(self):
        fuer conn in self.cache.values():
            conn.close()
        self.cache.clear()
        self.timeout.clear()

klasse DataHandler(BaseHandler):
    def data_open(self, req):
        # data URLs as specified in RFC 2397.
        #
        # ignores POSTed data
        #
        # syntax:
        # dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
        # mediatype := [ type "/" subtype ] *( ";" parameter )
        # data      := *urlchar
        # parameter := attribute "=" value
        url = req.full_url

        scheme, data = url.split(":",1)
        mediatype, data = data.split(",",1)

        # even base64 encoded data URLs might be quoted so unquote in any case:
        data = unquote_to_bytes(data)
        wenn mediatype.endswith(";base64"):
            data = base64.decodebytes(data)
            mediatype = mediatype[:-7]

        wenn not mediatype:
            mediatype = "text/plain;charset=US-ASCII"

        headers = email.message_from_string("Content-type: %s\nContent-length: %d\n" %
            (mediatype, len(data)))

        return addinfourl(io.BytesIO(data), headers, url)


# Code moved from the old urllib module

def url2pathname(url, *, require_scheme=Falsch, resolve_host=Falsch):
    """Convert the given file URL to a local file system path.

    The 'file:' scheme prefix must be omitted unless *require_scheme*
    is set to true.

    The URL authority may be resolved with gethostbyname() if
    *resolve_host* is set to true.
    """
    wenn not require_scheme:
        url = 'file:' + url
    scheme, authority, url = urlsplit(url)[:3]  # Discard query and fragment.
    wenn scheme != 'file':
        raise URLError("URL is missing a 'file:' scheme")
    wenn os.name == 'nt':
        wenn authority[1:2] == ':':
            # e.g. file://c:/file.txt
            url = authority + url
        sowenn not _is_local_authority(authority, resolve_host):
            # e.g. file://server/share/file.txt
            url = '//' + authority + url
        sowenn url[:3] == '///':
            # e.g. file://///server/share/file.txt
            url = url[1:]
        sonst:
            wenn url[:1] == '/' and url[2:3] in (':', '|'):
                # Skip past extra slash before DOS drive in URL path.
                url = url[1:]
            wenn url[1:2] == '|':
                # Older URLs use a pipe after a drive letter
                url = url[:1] + ':' + url[2:]
        url = url.replace('/', '\\')
    sowenn not _is_local_authority(authority, resolve_host):
        raise URLError("file:// scheme is supported only on localhost")
    encoding = sys.getfilesystemencoding()
    errors = sys.getfilesystemencodeerrors()
    return unquote(url, encoding=encoding, errors=errors)


def pathname2url(pathname, *, add_scheme=Falsch):
    """Convert the given local file system path to a file URL.

    The 'file:' scheme prefix is omitted unless *add_scheme*
    is set to true.
    """
    wenn os.name == 'nt':
        pathname = pathname.replace('\\', '/')
    encoding = sys.getfilesystemencoding()
    errors = sys.getfilesystemencodeerrors()
    scheme = 'file:' wenn add_scheme sonst ''
    drive, root, tail = os.path.splitroot(pathname)
    wenn drive:
        # First, clean up some special forms. We are going to sacrifice the
        # additional information anyway
        wenn drive[:4] == '//?/':
            drive = drive[4:]
            wenn drive[:4].upper() == 'UNC/':
                drive = '//' + drive[4:]
        wenn drive[1:] == ':':
            # DOS drive specified. Add three slashes to the start, producing
            # an authority section with a zero-length authority, and a path
            # section starting with a single slash.
            drive = '///' + drive
        drive = quote(drive, encoding=encoding, errors=errors, safe='/:')
    sowenn root:
        # Add explicitly empty authority to absolute path. If the path
        # starts with exactly one slash then this change is mostly
        # cosmetic, but wenn it begins with two or more slashes then this
        # avoids interpreting the path as a URL authority.
        root = '//' + root
    tail = quote(tail, encoding=encoding, errors=errors)
    return scheme + drive + root + tail


# Utility functions

_localhost = Nichts
def localhost():
    """Return the IP address of the magic hostname 'localhost'."""
    global _localhost
    wenn _localhost is Nichts:
        _localhost = socket.gethostbyname('localhost')
    return _localhost

_thishost = Nichts
def thishost():
    """Return the IP addresses of the current host."""
    global _thishost
    wenn _thishost is Nichts:
        try:
            _thishost = tuple(socket.gethostbyname_ex(socket.gethostname())[2])
        except socket.gaierror:
            _thishost = tuple(socket.gethostbyname_ex('localhost')[2])
    return _thishost

_ftperrors = Nichts
def ftperrors():
    """Return the set of errors raised by the FTP class."""
    global _ftperrors
    wenn _ftperrors is Nichts:
        import ftplib
        _ftperrors = ftplib.all_errors
    return _ftperrors

_noheaders = Nichts
def noheaders():
    """Return an empty email Message object."""
    global _noheaders
    wenn _noheaders is Nichts:
        _noheaders = email.message_from_string("")
    return _noheaders


# Utility classes

klasse ftpwrapper:
    """Class used by open_ftp() fuer cache of open FTP connections."""

    def __init__(self, user, passwd, host, port, dirs, timeout=Nichts,
                 persistent=Wahr):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.dirs = dirs
        self.timeout = timeout
        self.refcount = 0
        self.keepalive = persistent
        try:
            self.init()
        except:
            self.close()
            raise

    def init(self):
        import ftplib
        self.busy = 0
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.host, self.port, self.timeout)
        self.ftp.login(self.user, self.passwd)
        _target = '/'.join(self.dirs)
        self.ftp.cwd(_target)

    def retrfile(self, file, type):
        import ftplib
        self.endtransfer()
        wenn type in ('d', 'D'): cmd = 'TYPE A'; isdir = 1
        sonst: cmd = 'TYPE ' + type; isdir = 0
        try:
            self.ftp.voidcmd(cmd)
        except ftplib.all_errors:
            self.init()
            self.ftp.voidcmd(cmd)
        conn = Nichts
        wenn file and not isdir:
            # Try to retrieve as a file
            try:
                cmd = 'RETR ' + file
                conn, retrlen = self.ftp.ntransfercmd(cmd)
            except ftplib.error_perm as reason:
                wenn str(reason)[:3] != '550':
                    raise URLError(f'ftp error: {reason}') from reason
        wenn not conn:
            # Set transfer mode to ASCII!
            self.ftp.voidcmd('TYPE A')
            # Try a directory listing. Verify that directory exists.
            wenn file:
                pwd = self.ftp.pwd()
                try:
                    try:
                        self.ftp.cwd(file)
                    except ftplib.error_perm as reason:
                        raise URLError('ftp error: %r' % reason) from reason
                finally:
                    self.ftp.cwd(pwd)
                cmd = 'LIST ' + file
            sonst:
                cmd = 'LIST'
            conn, retrlen = self.ftp.ntransfercmd(cmd)
        self.busy = 1

        ftpobj = addclosehook(conn.makefile('rb'), self.file_close)
        self.refcount += 1
        conn.close()
        # Pass back both a suitably decorated object and a retrieval length
        return (ftpobj, retrlen)

    def endtransfer(self):
        wenn not self.busy:
            return
        self.busy = 0
        try:
            self.ftp.voidresp()
        except ftperrors():
            pass

    def close(self):
        self.keepalive = Falsch
        wenn self.refcount <= 0:
            self.real_close()

    def file_close(self):
        self.endtransfer()
        self.refcount -= 1
        wenn self.refcount <= 0 and not self.keepalive:
            self.real_close()

    def real_close(self):
        self.endtransfer()
        try:
            self.ftp.close()
        except ftperrors():
            pass

# Proxy handling
def getproxies_environment():
    """Return a dictionary of scheme -> proxy server URL mappings.

    Scan the environment fuer variables named <scheme>_proxy;
    this seems to be the standard convention.
    """
    # in order to prefer lowercase variables, process environment in
    # two passes: first matches any, second pass matches lowercase only

    # select only environment variables which end in (after making lowercase) _proxy
    proxies = {}
    environment = []
    fuer name in os.environ:
        # fast screen underscore position before more expensive case-folding
        wenn len(name) > 5 and name[-6] == "_" and name[-5:].lower() == "proxy":
            value = os.environ[name]
            proxy_name = name[:-6].lower()
            environment.append((name, value, proxy_name))
            wenn value:
                proxies[proxy_name] = value
    # CVE-2016-1000110 - If we are running as CGI script, forget HTTP_PROXY
    # (non-all-lowercase) as it may be set from the web server by a "Proxy:"
    # header from the client
    # If "proxy" is lowercase, it will still be used thanks to the next block
    wenn 'REQUEST_METHOD' in os.environ:
        proxies.pop('http', Nichts)
    fuer name, value, proxy_name in environment:
        # not case-folded, checking here fuer lower-case env vars only
        wenn name[-6:] == '_proxy':
            wenn value:
                proxies[proxy_name] = value
            sonst:
                proxies.pop(proxy_name, Nichts)
    return proxies

def proxy_bypass_environment(host, proxies=Nichts):
    """Test wenn proxies should not be used fuer a particular host.

    Checks the proxy dict fuer the value of no_proxy, which should
    be a list of comma separated DNS suffixes, or '*' fuer all hosts.

    """
    wenn proxies is Nichts:
        proxies = getproxies_environment()
    # don't bypass, wenn no_proxy isn't specified
    try:
        no_proxy = proxies['no']
    except KeyError:
        return Falsch
    # '*' is special case fuer always bypass
    wenn no_proxy == '*':
        return Wahr
    host = host.lower()
    # strip port off host
    hostonly, port = _splitport(host)
    # check wenn the host ends with any of the DNS suffixes
    fuer name in no_proxy.split(','):
        name = name.strip()
        wenn name:
            name = name.lstrip('.')  # ignore leading dots
            name = name.lower()
            wenn hostonly == name or host == name:
                return Wahr
            name = '.' + name
            wenn hostonly.endswith(name) or host.endswith(name):
                return Wahr
    # otherwise, don't bypass
    return Falsch


# This code tests an OSX specific data structure but is testable on all
# platforms
def _proxy_bypass_macosx_sysconf(host, proxy_settings):
    """
    Return Wahr iff this host shouldn't be accessed using a proxy

    This function uses the MacOSX framework SystemConfiguration
    to fetch the proxy information.

    proxy_settings come from _scproxy._get_proxy_settings or get mocked ie:
    { 'exclude_simple': bool,
      'exceptions': ['foo.bar', '*.bar.com', '127.0.0.1', '10.1', '10.0/16']
    }
    """
    from fnmatch import fnmatch
    from ipaddress import AddressValueError, IPv4Address

    hostonly, port = _splitport(host)

    def ip2num(ipAddr):
        parts = ipAddr.split('.')
        parts = list(map(int, parts))
        wenn len(parts) != 4:
            parts = (parts + [0, 0, 0, 0])[:4]
        return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]

    # Check fuer simple host names:
    wenn '.' not in host:
        wenn proxy_settings['exclude_simple']:
            return Wahr

    hostIP = Nichts
    try:
        hostIP = int(IPv4Address(hostonly))
    except AddressValueError:
        pass

    fuer value in proxy_settings.get('exceptions', ()):
        # Items in the list are strings like these: *.local, 169.254/16
        wenn not value: continue

        m = re.match(r"(\d+(?:\.\d+)*)(/\d+)?", value)
        wenn m is not Nichts and hostIP is not Nichts:
            base = ip2num(m.group(1))
            mask = m.group(2)
            wenn mask is Nichts:
                mask = 8 * (m.group(1).count('.') + 1)
            sonst:
                mask = int(mask[1:])

            wenn mask < 0 or mask > 32:
                # System libraries ignore invalid prefix lengths
                continue

            mask = 32 - mask

            wenn (hostIP >> mask) == (base >> mask):
                return Wahr

        sowenn fnmatch(host, value):
            return Wahr

    return Falsch


# Same as _proxy_bypass_macosx_sysconf, testable on all platforms
def _proxy_bypass_winreg_override(host, override):
    """Return Wahr wenn the host should bypass the proxy server.

    The proxy override list is obtained from the Windows
    Internet settings proxy override registry value.

    An example of a proxy override value is:
    "www.example.com;*.example.net; 192.168.0.1"
    """
    from fnmatch import fnmatch

    host, _ = _splitport(host)
    proxy_override = override.split(';')
    fuer test in proxy_override:
        test = test.strip()
        # "<local>" should bypass the proxy server fuer all intranet addresses
        wenn test == '<local>':
            wenn '.' not in host:
                return Wahr
        sowenn fnmatch(host, test):
            return Wahr
    return Falsch


wenn sys.platform == 'darwin':
    from _scproxy import _get_proxy_settings, _get_proxies

    def proxy_bypass_macosx_sysconf(host):
        proxy_settings = _get_proxy_settings()
        return _proxy_bypass_macosx_sysconf(host, proxy_settings)

    def getproxies_macosx_sysconf():
        """Return a dictionary of scheme -> proxy server URL mappings.

        This function uses the MacOSX framework SystemConfiguration
        to fetch the proxy information.
        """
        return _get_proxies()



    def proxy_bypass(host):
        """Return Wahr, wenn host should be bypassed.

        Checks proxy settings gathered from the environment, wenn specified,
        or from the MacOSX framework SystemConfiguration.

        """
        proxies = getproxies_environment()
        wenn proxies:
            return proxy_bypass_environment(host, proxies)
        sonst:
            return proxy_bypass_macosx_sysconf(host)

    def getproxies():
        return getproxies_environment() or getproxies_macosx_sysconf()


sowenn os.name == 'nt':
    def getproxies_registry():
        """Return a dictionary of scheme -> proxy server URL mappings.

        Win32 uses the registry to store proxies.

        """
        proxies = {}
        try:
            import winreg
        except ImportError:
            # Std module, so should be around - but you never know!
            return proxies
        try:
            internetSettings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
            proxyEnable = winreg.QueryValueEx(internetSettings,
                                               'ProxyEnable')[0]
            wenn proxyEnable:
                # Returned as Unicode but problems wenn not converted to ASCII
                proxyServer = str(winreg.QueryValueEx(internetSettings,
                                                       'ProxyServer')[0])
                wenn '=' not in proxyServer and ';' not in proxyServer:
                    # Use one setting fuer all protocols.
                    proxyServer = 'http={0};https={0};ftp={0}'.format(proxyServer)
                fuer p in proxyServer.split(';'):
                    protocol, address = p.split('=', 1)
                    # See wenn address has a type:// prefix
                    wenn not re.match('(?:[^/:]+)://', address):
                        # Add type:// prefix to address without specifying type
                        wenn protocol in ('http', 'https', 'ftp'):
                            # The default proxy type of Windows is HTTP
                            address = 'http://' + address
                        sowenn protocol == 'socks':
                            address = 'socks://' + address
                    proxies[protocol] = address
                # Use SOCKS proxy fuer HTTP(S) protocols
                wenn proxies.get('socks'):
                    # The default SOCKS proxy type of Windows is SOCKS4
                    address = re.sub(r'^socks://', 'socks4://', proxies['socks'])
                    proxies['http'] = proxies.get('http') or address
                    proxies['https'] = proxies.get('https') or address
            internetSettings.Close()
        except (OSError, ValueError, TypeError):
            # Either registry key not found etc, or the value in an
            # unexpected format.
            # proxies already set up to be empty so nothing to do
            pass
        return proxies

    def getproxies():
        """Return a dictionary of scheme -> proxy server URL mappings.

        Returns settings gathered from the environment, wenn specified,
        or the registry.

        """
        return getproxies_environment() or getproxies_registry()

    def proxy_bypass_registry(host):
        try:
            import winreg
        except ImportError:
            # Std modules, so should be around - but you never know!
            return Falsch
        try:
            internetSettings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
            proxyEnable = winreg.QueryValueEx(internetSettings,
                                               'ProxyEnable')[0]
            proxyOverride = str(winreg.QueryValueEx(internetSettings,
                                                     'ProxyOverride')[0])
            # ^^^^ Returned as Unicode but problems wenn not converted to ASCII
        except OSError:
            return Falsch
        wenn not proxyEnable or not proxyOverride:
            return Falsch
        return _proxy_bypass_winreg_override(host, proxyOverride)

    def proxy_bypass(host):
        """Return Wahr, wenn host should be bypassed.

        Checks proxy settings gathered from the environment, wenn specified,
        or the registry.

        """
        proxies = getproxies_environment()
        wenn proxies:
            return proxy_bypass_environment(host, proxies)
        sonst:
            return proxy_bypass_registry(host)

sonst:
    # By default use environment variables
    getproxies = getproxies_environment
    proxy_bypass = proxy_bypass_environment
