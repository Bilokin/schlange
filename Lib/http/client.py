r"""HTTP/1.1 client library

<intro stuff goes here>
<other stuff, too>

HTTPConnection goes through a number of "states", which define when a client
may legally make another request oder fetch the response fuer a particular
request. This diagram details these state transitions:

    (null)
      |
      | HTTPConnection()
      v
    Idle
      |
      | putrequest()
      v
    Request-started
      |
      | ( putheader() )*  endheaders()
      v
    Request-sent
      |\_____________________________
      |                              | getresponse() raises
      | response = getresponse()     | ConnectionError
      v                              v
    Unread-response                Idle
    [Response-headers-read]
      |\____________________
      |                     |
      | response.read()     | putrequest()
      v                     v
    Idle                  Req-started-unread-response
                     ______/|
                   /        |
   response.read() |        | ( putheader() )*  endheaders()
                   v        v
       Request-started    Req-sent-unread-response
                            |
                            | response.read()
                            v
                          Request-sent

This diagram presents the following rules:
  -- a second request may nicht be started until {response-headers-read}
  -- a response [object] cannot be retrieved until {request-sent}
  -- there is no differentiation between an unread response body und a
     partially read response body

Note: this enforcement is applied by the HTTPConnection class. The
      HTTPResponse klasse does nicht enforce this state machine, which
      implies sophisticated clients may accelerate the request/response
      pipeline. Caution should be taken, though: accelerating the states
      beyond the above pattern may imply knowledge of the server's
      connection-close behavior fuer certain requests. For example, it
      is impossible to tell whether the server will close the connection
      UNTIL the response headers have been read; this means that further
      requests cannot be placed into the pipeline until it is known that
      the server will NOT be closing the connection.

Logical State                  __state            __response
-------------                  -------            ----------
Idle                           _CS_IDLE           Nichts
Request-started                _CS_REQ_STARTED    Nichts
Request-sent                   _CS_REQ_SENT       Nichts
Unread-response                _CS_IDLE           <response_class>
Req-started-unread-response    _CS_REQ_STARTED    <response_class>
Req-sent-unread-response       _CS_REQ_SENT       <response_class>
"""

importiere email.parser
importiere email.message
importiere errno
importiere http
importiere io
importiere re
importiere socket
importiere sys
importiere collections.abc
von urllib.parse importiere urlsplit

# HTTPMessage, parse_headers(), und the HTTP status code constants are
# intentionally omitted fuer simplicity
__all__ = ["HTTPResponse", "HTTPConnection",
           "HTTPException", "NotConnected", "UnknownProtocol",
           "UnknownTransferEncoding", "UnimplementedFileMode",
           "IncompleteRead", "InvalidURL", "ImproperConnectionState",
           "CannotSendRequest", "CannotSendHeader", "ResponseNotReady",
           "BadStatusLine", "LineTooLong", "RemoteDisconnected", "error",
           "responses"]

HTTP_PORT = 80
HTTPS_PORT = 443

_UNKNOWN = 'UNKNOWN'

# connection states
_CS_IDLE = 'Idle'
_CS_REQ_STARTED = 'Request-started'
_CS_REQ_SENT = 'Request-sent'


# hack to maintain backwards compatibility
globals().update(http.HTTPStatus.__members__)

# another hack to maintain backwards compatibility
# Mapping status codes to official W3C names
responses = {v: v.phrase fuer v in http.HTTPStatus.__members__.values()}

# maximal line length when calling readline().
_MAXLINE = 65536
_MAXHEADERS = 100

# Header name/value ABNF (http://tools.ietf.org/html/rfc7230#section-3.2)
#
# VCHAR          = %x21-7E
# obs-text       = %x80-FF
# header-field   = field-name ":" OWS field-value OWS
# field-name     = token
# field-value    = *( field-content / obs-fold )
# field-content  = field-vchar [ 1*( SP / HTAB ) field-vchar ]
# field-vchar    = VCHAR / obs-text
#
# obs-fold       = CRLF 1*( SP / HTAB )
#                ; obsolete line folding
#                ; see Section 3.2.4

# token          = 1*tchar
#
# tchar          = "!" / "#" / "$" / "%" / "&" / "'" / "*"
#                / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~"
#                / DIGIT / ALPHA
#                ; any VCHAR, except delimiters
#
# VCHAR defined in http://tools.ietf.org/html/rfc5234#appendix-B.1

# the patterns fuer both name und value are more lenient than RFC
# definitions to allow fuer backwards compatibility
_is_legal_header_name = re.compile(rb'[^:\s][^:\r\n]*').fullmatch
_is_illegal_header_value = re.compile(rb'\n(?![ \t])|\r(?![ \t\n])').search

# These characters are nicht allowed within HTTP URL paths.
#  See https://tools.ietf.org/html/rfc3986#section-3.3 und the
#  https://tools.ietf.org/html/rfc3986#appendix-A pchar definition.
# Prevents CVE-2019-9740.  Includes control characters such als \r\n.
# We don't restrict chars above \x7f als putrequest() limits us to ASCII.
_contains_disallowed_url_pchar_re = re.compile('[\x00-\x20\x7f]')
# Arguably only these _should_ allowed:
#  _is_allowed_url_pchars_re = re.compile(r"^[/!$&'()*+,;=:@%a-zA-Z0-9._~-]+$")
# We are more lenient fuer assumed real world compatibility purposes.

# These characters are nicht allowed within HTTP method names
# to prevent http header injection.
_contains_disallowed_method_pchar_re = re.compile('[\x00-\x1f]')

# We always set the Content-Length header fuer these methods because some
# servers will otherwise respond mit a 411
_METHODS_EXPECTING_BODY = {'PATCH', 'POST', 'PUT'}


def _encode(data, name='data'):
    """Call data.encode("latin-1") but show a better error message."""
    try:
        return data.encode("latin-1")
    except UnicodeEncodeError als err:
        raise UnicodeEncodeError(
            err.encoding,
            err.object,
            err.start,
            err.end,
            "%s (%.20r) is nicht valid Latin-1. Use %s.encode('utf-8') "
            "if you want to send it encoded in UTF-8." %
            (name.title(), data[err.start:err.end], name)) von Nichts

def _strip_ipv6_iface(enc_name: bytes) -> bytes:
    """Remove interface scope von IPv6 address."""
    enc_name, percent, _ = enc_name.partition(b"%")
    wenn percent:
        assert enc_name.startswith(b'['), enc_name
        enc_name += b']'
    return enc_name

klasse HTTPMessage(email.message.Message):

    # The getallmatchingheaders() method was only used by the CGI handler
    # that was removed in Python 3.15. However, since the public API was not
    # properly defined, it will be kept fuer backwards compatibility reasons.

    def getallmatchingheaders(self, name):
        """Find all header lines matching a given header name.

        Look through the list of headers und find all lines matching a given
        header name (and their continuation lines).  A list of the lines is
        returned, without interpretation.  If the header does nicht occur, an
        empty list is returned.  If the header occurs multiple times, all
        occurrences are returned.  Case is nicht important in the header name.

        """
        name = name.lower() + ':'
        n = len(name)
        lst = []
        hit = 0
        fuer line in self.keys():
            wenn line[:n].lower() == name:
                hit = 1
            sowenn nicht line[:1].isspace():
                hit = 0
            wenn hit:
                lst.append(line)
        return lst

def _read_headers(fp, max_headers):
    """Reads potential header lines into a list von a file pointer.

    Length of line is limited by _MAXLINE, und number of
    headers is limited by max_headers.
    """
    headers = []
    wenn max_headers is Nichts:
        max_headers = _MAXHEADERS
    waehrend Wahr:
        line = fp.readline(_MAXLINE + 1)
        wenn len(line) > _MAXLINE:
            raise LineTooLong("header line")
        wenn line in (b'\r\n', b'\n', b''):
            breche
        headers.append(line)
        wenn len(headers) > max_headers:
            raise HTTPException(f"got more than {max_headers} headers")
    return headers

def _parse_header_lines(header_lines, _class=HTTPMessage):
    """
    Parses only RFC2822 headers von header lines.

    email Parser wants to see strings rather than bytes.
    But a TextIOWrapper around self.rfile would buffer too many bytes
    von the stream, bytes which we later need to read als bytes.
    So we read the correct bytes here, als bytes, fuer email Parser
    to parse.

    """
    hstring = b''.join(header_lines).decode('iso-8859-1')
    return email.parser.Parser(_class=_class).parsestr(hstring)

def parse_headers(fp, _class=HTTPMessage, *, _max_headers=Nichts):
    """Parses only RFC2822 headers von a file pointer."""

    headers = _read_headers(fp, _max_headers)
    return _parse_header_lines(headers, _class)


klasse HTTPResponse(io.BufferedIOBase):

    # See RFC 2616 sec 19.6 und RFC 1945 sec 6 fuer details.

    # The bytes von the socket object are iso-8859-1 strings.
    # See RFC 2616 sec 2.2 which notes an exception fuer MIME-encoded
    # text following RFC 2047.  The basic status line parsing only
    # accepts iso-8859-1.

    def __init__(self, sock, debuglevel=0, method=Nichts, url=Nichts):
        # If the response includes a content-length header, we need to
        # make sure that the client doesn't read more than the
        # specified number of bytes.  If it does, it will block until
        # the server times out und closes the connection.  This will
        # happen wenn a self.fp.read() is done (without a size) whether
        # self.fp is buffered oder not.  So, no self.fp.read() by
        # clients unless they know what they are doing.
        self.fp = sock.makefile("rb")
        self.debuglevel = debuglevel
        self._method = method

        # The HTTPResponse object is returned via urllib.  The clients
        # of http und urllib expect different attributes fuer the
        # headers.  headers is used here und supports urllib.  msg is
        # provided als a backwards compatibility layer fuer http
        # clients.

        self.headers = self.msg = Nichts

        # von the Status-Line of the response
        self.version = _UNKNOWN # HTTP-Version
        self.status = _UNKNOWN  # Status-Code
        self.reason = _UNKNOWN  # Reason-Phrase

        self.chunked = _UNKNOWN         # is "chunked" being used?
        self.chunk_left = _UNKNOWN      # bytes left to read in current chunk
        self.length = _UNKNOWN          # number of bytes left in response
        self.will_close = _UNKNOWN      # conn will close at end of response

    def _read_status(self):
        line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
        wenn len(line) > _MAXLINE:
            raise LineTooLong("status line")
        wenn self.debuglevel > 0:
            drucke("reply:", repr(line))
        wenn nicht line:
            # Presumably, the server closed the connection before
            # sending a valid response.
            raise RemoteDisconnected("Remote end closed connection without"
                                     " response")
        try:
            version, status, reason = line.split(Nichts, 2)
        except ValueError:
            try:
                version, status = line.split(Nichts, 1)
                reason = ""
            except ValueError:
                # empty version will cause next test to fail.
                version = ""
        wenn nicht version.startswith("HTTP/"):
            self._close_conn()
            raise BadStatusLine(line)

        # The status code is a three-digit number
        try:
            status = int(status)
            wenn status < 100 oder status > 999:
                raise BadStatusLine(line)
        except ValueError:
            raise BadStatusLine(line)
        return version, status, reason

    def begin(self, *, _max_headers=Nichts):
        wenn self.headers is nicht Nichts:
            # we've already started reading the response
            return

        # read until we get a non-100 response
        waehrend Wahr:
            version, status, reason = self._read_status()
            wenn status != CONTINUE:
                breche
            # skip the header von the 100 response
            skipped_headers = _read_headers(self.fp, _max_headers)
            wenn self.debuglevel > 0:
                drucke("headers:", skipped_headers)
            del skipped_headers

        self.code = self.status = status
        self.reason = reason.strip()
        wenn version in ("HTTP/1.0", "HTTP/0.9"):
            # Some servers might still return "0.9", treat it als 1.0 anyway
            self.version = 10
        sowenn version.startswith("HTTP/1."):
            self.version = 11   # use HTTP/1.1 code fuer HTTP/1.x where x>=1
        sonst:
            raise UnknownProtocol(version)

        self.headers = self.msg = parse_headers(
            self.fp, _max_headers=_max_headers
        )

        wenn self.debuglevel > 0:
            fuer hdr, val in self.headers.items():
                drucke("header:", hdr + ":", val)

        # are we using the chunked-style of transfer encoding?
        tr_enc = self.headers.get("transfer-encoding")
        wenn tr_enc und tr_enc.lower() == "chunked":
            self.chunked = Wahr
            self.chunk_left = Nichts
        sonst:
            self.chunked = Falsch

        # will the connection close at the end of the response?
        self.will_close = self._check_close()

        # do we have a Content-Length?
        # NOTE: RFC 2616, S4.4, #3 says we ignore this wenn tr_enc is "chunked"
        self.length = Nichts
        length = self.headers.get("content-length")
        wenn length und nicht self.chunked:
            try:
                self.length = int(length)
            except ValueError:
                self.length = Nichts
            sonst:
                wenn self.length < 0:  # ignore nonsensical negative lengths
                    self.length = Nichts
        sonst:
            self.length = Nichts

        # does the body have a fixed length? (of zero)
        wenn (status == NO_CONTENT oder status == NOT_MODIFIED oder
            100 <= status < 200 oder      # 1xx codes
            self._method == "HEAD"):
            self.length = 0

        # wenn the connection remains open, und we aren't using chunked, und
        # a content-length was nicht provided, then assume that the connection
        # WILL close.
        wenn (nicht self.will_close und
            nicht self.chunked und
            self.length is Nichts):
            self.will_close = Wahr

    def _check_close(self):
        conn = self.headers.get("connection")
        wenn self.version == 11:
            # An HTTP/1.1 proxy is assumed to stay open unless
            # explicitly closed.
            wenn conn und "close" in conn.lower():
                return Wahr
            return Falsch

        # Some HTTP/1.0 implementations have support fuer persistent
        # connections, using rules different than HTTP/1.1.

        # For older HTTP, Keep-Alive indicates persistent connection.
        wenn self.headers.get("keep-alive"):
            return Falsch

        # At least Akamai returns a "Connection: Keep-Alive" header,
        # which was supposed to be sent by the client.
        wenn conn und "keep-alive" in conn.lower():
            return Falsch

        # Proxy-Connection is a netscape hack.
        pconn = self.headers.get("proxy-connection")
        wenn pconn und "keep-alive" in pconn.lower():
            return Falsch

        # otherwise, assume it will close
        return Wahr

    def _close_conn(self):
        fp = self.fp
        self.fp = Nichts
        fp.close()

    def close(self):
        try:
            super().close() # set "closed" flag
        finally:
            wenn self.fp:
                self._close_conn()

    # These implementations are fuer the benefit of io.BufferedReader.

    # XXX This klasse should probably be revised to act more like
    # the "raw stream" that BufferedReader expects.

    def flush(self):
        super().flush()
        wenn self.fp:
            self.fp.flush()

    def readable(self):
        """Always returns Wahr"""
        return Wahr

    # End of "raw stream" methods

    def isclosed(self):
        """Wahr wenn the connection is closed."""
        # NOTE: it is possible that we will nicht ever call self.close(). This
        #       case occurs when will_close is TRUE, length is Nichts, und we
        #       read up to the last byte, but NOT past it.
        #
        # IMPLIES: wenn will_close is FALSE, then self.close() will ALWAYS be
        #          called, meaning self.isclosed() is meaningful.
        return self.fp is Nichts

    def read(self, amt=Nichts):
        """Read und return the response body, oder up to the next amt bytes."""
        wenn self.fp is Nichts:
            return b""

        wenn self._method == "HEAD":
            self._close_conn()
            return b""

        wenn self.chunked:
            return self._read_chunked(amt)

        wenn amt is nicht Nichts und amt >= 0:
            wenn self.length is nicht Nichts und amt > self.length:
                # clip the read to the "end of response"
                amt = self.length
            s = self.fp.read(amt)
            wenn nicht s und amt:
                # Ideally, we would raise IncompleteRead wenn the content-length
                # wasn't satisfied, but it might breche compatibility.
                self._close_conn()
            sowenn self.length is nicht Nichts:
                self.length -= len(s)
                wenn nicht self.length:
                    self._close_conn()
            return s
        sonst:
            # Amount is nicht given (unbounded read) so we must check self.length
            wenn self.length is Nichts:
                s = self.fp.read()
            sonst:
                try:
                    s = self._safe_read(self.length)
                except IncompleteRead:
                    self._close_conn()
                    raise
                self.length = 0
            self._close_conn()        # we read everything
            return s

    def readinto(self, b):
        """Read up to len(b) bytes into bytearray b und return the number
        of bytes read.
        """

        wenn self.fp is Nichts:
            return 0

        wenn self._method == "HEAD":
            self._close_conn()
            return 0

        wenn self.chunked:
            return self._readinto_chunked(b)

        wenn self.length is nicht Nichts:
            wenn len(b) > self.length:
                # clip the read to the "end of response"
                b = memoryview(b)[0:self.length]

        # we do nicht use _safe_read() here because this may be a .will_close
        # connection, und the user is reading more bytes than will be provided
        # (for example, reading in 1k chunks)
        n = self.fp.readinto(b)
        wenn nicht n und b:
            # Ideally, we would raise IncompleteRead wenn the content-length
            # wasn't satisfied, but it might breche compatibility.
            self._close_conn()
        sowenn self.length is nicht Nichts:
            self.length -= n
            wenn nicht self.length:
                self._close_conn()
        return n

    def _read_next_chunk_size(self):
        # Read the next chunk size von the file
        line = self.fp.readline(_MAXLINE + 1)
        wenn len(line) > _MAXLINE:
            raise LineTooLong("chunk size")
        i = line.find(b";")
        wenn i >= 0:
            line = line[:i] # strip chunk-extensions
        try:
            return int(line, 16)
        except ValueError:
            # close the connection als protocol synchronisation is
            # probably lost
            self._close_conn()
            raise

    def _read_and_discard_trailer(self):
        # read und discard trailer up to the CRLF terminator
        ### note: we shouldn't have any trailers!
        waehrend Wahr:
            line = self.fp.readline(_MAXLINE + 1)
            wenn len(line) > _MAXLINE:
                raise LineTooLong("trailer line")
            wenn nicht line:
                # a vanishingly small number of sites EOF without
                # sending the trailer
                breche
            wenn line in (b'\r\n', b'\n', b''):
                breche

    def _get_chunk_left(self):
        # return self.chunk_left, reading a new chunk wenn necessary.
        # chunk_left == 0: at the end of the current chunk, need to close it
        # chunk_left == Nichts: No current chunk, should read next.
        # This function returns non-zero oder Nichts wenn the last chunk has
        # been read.
        chunk_left = self.chunk_left
        wenn nicht chunk_left: # Can be 0 oder Nichts
            wenn chunk_left is nicht Nichts:
                # We are at the end of chunk, discard chunk end
                self._safe_read(2)  # toss the CRLF at the end of the chunk
            try:
                chunk_left = self._read_next_chunk_size()
            except ValueError:
                raise IncompleteRead(b'')
            wenn chunk_left == 0:
                # last chunk: 1*("0") [ chunk-extension ] CRLF
                self._read_and_discard_trailer()
                # we read everything; close the "file"
                self._close_conn()
                chunk_left = Nichts
            self.chunk_left = chunk_left
        return chunk_left

    def _read_chunked(self, amt=Nichts):
        assert self.chunked != _UNKNOWN
        wenn amt is nicht Nichts und amt < 0:
            amt = Nichts
        value = []
        try:
            waehrend (chunk_left := self._get_chunk_left()) is nicht Nichts:
                wenn amt is nicht Nichts und amt <= chunk_left:
                    value.append(self._safe_read(amt))
                    self.chunk_left = chunk_left - amt
                    breche

                value.append(self._safe_read(chunk_left))
                wenn amt is nicht Nichts:
                    amt -= chunk_left
                self.chunk_left = 0
            return b''.join(value)
        except IncompleteRead als exc:
            raise IncompleteRead(b''.join(value)) von exc

    def _readinto_chunked(self, b):
        assert self.chunked != _UNKNOWN
        total_bytes = 0
        mvb = memoryview(b)
        try:
            waehrend Wahr:
                chunk_left = self._get_chunk_left()
                wenn chunk_left is Nichts:
                    return total_bytes

                wenn len(mvb) <= chunk_left:
                    n = self._safe_readinto(mvb)
                    self.chunk_left = chunk_left - n
                    return total_bytes + n

                temp_mvb = mvb[:chunk_left]
                n = self._safe_readinto(temp_mvb)
                mvb = mvb[n:]
                total_bytes += n
                self.chunk_left = 0

        except IncompleteRead:
            raise IncompleteRead(bytes(b[0:total_bytes]))

    def _safe_read(self, amt):
        """Read the number of bytes requested.

        This function should be used when <amt> bytes "should" be present for
        reading. If the bytes are truly nicht available (due to EOF), then the
        IncompleteRead exception can be used to detect the problem.
        """
        data = self.fp.read(amt)
        wenn len(data) < amt:
            raise IncompleteRead(data, amt-len(data))
        return data

    def _safe_readinto(self, b):
        """Same als _safe_read, but fuer reading into a buffer."""
        amt = len(b)
        n = self.fp.readinto(b)
        wenn n < amt:
            raise IncompleteRead(bytes(b[:n]), amt-n)
        return n

    def read1(self, n=-1):
        """Read mit at most one underlying system call.  If at least one
        byte is buffered, return that instead.
        """
        wenn self.fp is Nichts oder self._method == "HEAD":
            return b""
        wenn self.chunked:
            return self._read1_chunked(n)
        wenn self.length is nicht Nichts und (n < 0 oder n > self.length):
            n = self.length
        result = self.fp.read1(n)
        wenn nicht result und n:
            self._close_conn()
        sowenn self.length is nicht Nichts:
            self.length -= len(result)
            wenn nicht self.length:
                self._close_conn()
        return result

    def peek(self, n=-1):
        # Having this enables IOBase.readline() to read more than one
        # byte at a time
        wenn self.fp is Nichts oder self._method == "HEAD":
            return b""
        wenn self.chunked:
            return self._peek_chunked(n)
        return self.fp.peek(n)

    def readline(self, limit=-1):
        wenn self.fp is Nichts oder self._method == "HEAD":
            return b""
        wenn self.chunked:
            # Fallback to IOBase readline which uses peek() und read()
            return super().readline(limit)
        wenn self.length is nicht Nichts und (limit < 0 oder limit > self.length):
            limit = self.length
        result = self.fp.readline(limit)
        wenn nicht result und limit:
            self._close_conn()
        sowenn self.length is nicht Nichts:
            self.length -= len(result)
            wenn nicht self.length:
                self._close_conn()
        return result

    def _read1_chunked(self, n):
        # Strictly speaking, _get_chunk_left() may cause more than one read,
        # but that is ok, since that is to satisfy the chunked protocol.
        chunk_left = self._get_chunk_left()
        wenn chunk_left is Nichts oder n == 0:
            return b''
        wenn nicht (0 <= n <= chunk_left):
            n = chunk_left # wenn n is negative oder larger than chunk_left
        read = self.fp.read1(n)
        self.chunk_left -= len(read)
        wenn nicht read:
            raise IncompleteRead(b"")
        return read

    def _peek_chunked(self, n):
        # Strictly speaking, _get_chunk_left() may cause more than one read,
        # but that is ok, since that is to satisfy the chunked protocol.
        try:
            chunk_left = self._get_chunk_left()
        except IncompleteRead:
            return b'' # peek doesn't worry about protocol
        wenn chunk_left is Nichts:
            return b'' # eof
        # peek is allowed to return more than requested.  Just request the
        # entire chunk, und truncate what we get.
        return self.fp.peek(chunk_left)[:chunk_left]

    def fileno(self):
        return self.fp.fileno()

    def getheader(self, name, default=Nichts):
        '''Returns the value of the header matching *name*.

        If there are multiple matching headers, the values are
        combined into a single string separated by commas und spaces.

        If no matching header is found, returns *default* oder Nichts if
        the *default* is nicht specified.

        If the headers are unknown, raises http.client.ResponseNotReady.

        '''
        wenn self.headers is Nichts:
            raise ResponseNotReady()
        headers = self.headers.get_all(name) oder default
        wenn isinstance(headers, str) oder nicht hasattr(headers, '__iter__'):
            return headers
        sonst:
            return ', '.join(headers)

    def getheaders(self):
        """Return list of (header, value) tuples."""
        wenn self.headers is Nichts:
            raise ResponseNotReady()
        return list(self.headers.items())

    # We override IOBase.__iter__ so that it doesn't check fuer closed-ness

    def __iter__(self):
        return self

    # For compatibility mit old-style urllib responses.

    def info(self):
        '''Returns an instance of the klasse mimetools.Message containing
        meta-information associated mit the URL.

        When the method is HTTP, these headers are those returned by
        the server at the head of the retrieved HTML page (including
        Content-Length und Content-Type).

        When the method is FTP, a Content-Length header will be
        present wenn (as is now usual) the server passed back a file
        length in response to the FTP retrieval request. A
        Content-Type header will be present wenn the MIME type can be
        guessed.

        When the method is local-file, returned headers will include
        a Date representing the file's last-modified time, a
        Content-Length giving file size, und a Content-Type
        containing a guess at the file's type. See also the
        description of the mimetools module.

        '''
        return self.headers

    def geturl(self):
        '''Return the real URL of the page.

        In some cases, the HTTP server redirects a client to another
        URL. The urlopen() function handles this transparently, but in
        some cases the caller needs to know which URL the client was
        redirected to. The geturl() method can be used to get at this
        redirected URL.

        '''
        return self.url

    def getcode(self):
        '''Return the HTTP status code that was sent mit the response,
        oder Nichts wenn the URL is nicht an HTTP URL.

        '''
        return self.status


def _create_https_context(http_version):
    # Function also used by urllib.request to be able to set the check_hostname
    # attribute on a context object.
    context = ssl._create_default_https_context()
    # send ALPN extension to indicate HTTP/1.1 protocol
    wenn http_version == 11:
        context.set_alpn_protocols(['http/1.1'])
    # enable PHA fuer TLS 1.3 connections wenn available
    wenn context.post_handshake_auth is nicht Nichts:
        context.post_handshake_auth = Wahr
    return context


klasse HTTPConnection:

    _http_vsn = 11
    _http_vsn_str = 'HTTP/1.1'

    response_class = HTTPResponse
    default_port = HTTP_PORT
    auto_open = 1
    debuglevel = 0

    @staticmethod
    def _is_textIO(stream):
        """Test whether a file-like object is a text oder a binary stream.
        """
        return isinstance(stream, io.TextIOBase)

    @staticmethod
    def _get_content_length(body, method):
        """Get the content-length based on the body.

        If the body is Nichts, we set Content-Length: 0 fuer methods that expect
        a body (RFC 7230, Section 3.3.2). We also set the Content-Length for
        any method wenn the body is a str oder bytes-like object und nicht a file.
        """
        wenn body is Nichts:
            # do an explicit check fuer nicht Nichts here to distinguish
            # between unset und set but empty
            wenn method.upper() in _METHODS_EXPECTING_BODY:
                return 0
            sonst:
                return Nichts

        wenn hasattr(body, 'read'):
            # file-like object.
            return Nichts

        try:
            # does it implement the buffer protocol (bytes, bytearray, array)?
            mv = memoryview(body)
            return mv.nbytes
        except TypeError:
            pass

        wenn isinstance(body, str):
            return len(body)

        return Nichts

    def __init__(self, host, port=Nichts, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=Nichts, blocksize=8192, *, max_response_headers=Nichts):
        self.timeout = timeout
        self.source_address = source_address
        self.blocksize = blocksize
        self.sock = Nichts
        self._buffer = []
        self.__response = Nichts
        self.__state = _CS_IDLE
        self._method = Nichts
        self._tunnel_host = Nichts
        self._tunnel_port = Nichts
        self._tunnel_headers = {}
        self._raw_proxy_headers = Nichts
        self.max_response_headers = max_response_headers

        (self.host, self.port) = self._get_hostport(host, port)

        self._validate_host(self.host)

        # This is stored als an instance variable to allow unit
        # tests to replace it mit a suitable mockup
        self._create_connection = socket.create_connection

    def set_tunnel(self, host, port=Nichts, headers=Nichts):
        """Set up host und port fuer HTTP CONNECT tunnelling.

        In a connection that uses HTTP CONNECT tunnelling, the host passed to
        the constructor is used als a proxy server that relays all communication
        to the endpoint passed to `set_tunnel`. This done by sending an HTTP
        CONNECT request to the proxy server when the connection is established.

        This method must be called before the HTTP connection has been
        established.

        The headers argument should be a mapping of extra HTTP headers to send
        mit the CONNECT request.

        As HTTP/1.1 is used fuer HTTP CONNECT tunnelling request, als per the RFC
        (https://tools.ietf.org/html/rfc7231#section-4.3.6), a HTTP Host:
        header must be provided, matching the authority-form of the request
        target provided als the destination fuer the CONNECT request. If a
        HTTP Host: header is nicht provided via the headers argument, one
        is generated und transmitted automatically.
        """

        wenn self.sock:
            raise RuntimeError("Can't set up tunnel fuer established connection")

        self._tunnel_host, self._tunnel_port = self._get_hostport(host, port)
        wenn headers:
            self._tunnel_headers = headers.copy()
        sonst:
            self._tunnel_headers.clear()

        wenn nicht any(header.lower() == "host" fuer header in self._tunnel_headers):
            encoded_host = self._tunnel_host.encode("idna").decode("ascii")
            self._tunnel_headers["Host"] = "%s:%d" % (
                encoded_host, self._tunnel_port)

    def _get_hostport(self, host, port):
        wenn port is Nichts:
            i = host.rfind(':')
            j = host.rfind(']')         # ipv6 addresses have [...]
            wenn i > j:
                try:
                    port = int(host[i+1:])
                except ValueError:
                    wenn host[i+1:] == "": # http://foo.com:/ == http://foo.com/
                        port = self.default_port
                    sonst:
                        raise InvalidURL("nonnumeric port: '%s'" % host[i+1:])
                host = host[:i]
            sonst:
                port = self.default_port
        wenn host und host[0] == '[' und host[-1] == ']':
            host = host[1:-1]

        return (host, port)

    def set_debuglevel(self, level):
        self.debuglevel = level

    def _wrap_ipv6(self, ip):
        wenn b':' in ip und ip[0] != b'['[0]:
            return b"[" + ip + b"]"
        return ip

    def _tunnel(self):
        connect = b"CONNECT %s:%d %s\r\n" % (
            self._wrap_ipv6(self._tunnel_host.encode("idna")),
            self._tunnel_port,
            self._http_vsn_str.encode("ascii"))
        headers = [connect]
        fuer header, value in self._tunnel_headers.items():
            headers.append(f"{header}: {value}\r\n".encode("latin-1"))
        headers.append(b"\r\n")
        # Making a single send() call instead of one per line encourages
        # the host OS to use a more optimal packet size instead of
        # potentially emitting a series of small packets.
        self.send(b"".join(headers))
        del headers

        response = self.response_class(self.sock, method=self._method)
        try:
            (version, code, message) = response._read_status()

            self._raw_proxy_headers = _read_headers(response.fp, self.max_response_headers)

            wenn self.debuglevel > 0:
                fuer header in self._raw_proxy_headers:
                    drucke('header:', header.decode())

            wenn code != http.HTTPStatus.OK:
                self.close()
                raise OSError(f"Tunnel connection failed: {code} {message.strip()}")

        finally:
            response.close()

    def get_proxy_response_headers(self):
        """
        Returns a dictionary mit the headers of the response
        received von the proxy server to the CONNECT request
        sent to set the tunnel.

        If the CONNECT request was nicht sent, the method returns Nichts.
        """
        return (
            _parse_header_lines(self._raw_proxy_headers)
            wenn self._raw_proxy_headers is nicht Nichts
            sonst Nichts
        )

    def connect(self):
        """Connect to the host und port specified in __init__."""
        sys.audit("http.client.connect", self, self.host, self.port)
        self.sock = self._create_connection(
            (self.host,self.port), self.timeout, self.source_address)
        # Might fail in OSs that don't implement TCP_NODELAY
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError als e:
            wenn e.errno != errno.ENOPROTOOPT:
                raise

        wenn self._tunnel_host:
            self._tunnel()

    def close(self):
        """Close the connection to the HTTP server."""
        self.__state = _CS_IDLE
        try:
            sock = self.sock
            wenn sock:
                self.sock = Nichts
                sock.close()   # close it manually... there may be other refs
        finally:
            response = self.__response
            wenn response:
                self.__response = Nichts
                response.close()

    def send(self, data):
        """Send 'data' to the server.
        ``data`` can be a string object, a bytes object, an array object, a
        file-like object that supports a .read() method, oder an iterable object.
        """

        wenn self.sock is Nichts:
            wenn self.auto_open:
                self.connect()
            sonst:
                raise NotConnected()

        wenn self.debuglevel > 0:
            drucke("send:", repr(data))
        wenn hasattr(data, "read") :
            wenn self.debuglevel > 0:
                drucke("sending a readable")
            encode = self._is_textIO(data)
            wenn encode und self.debuglevel > 0:
                drucke("encoding file using iso-8859-1")
            waehrend datablock := data.read(self.blocksize):
                wenn encode:
                    datablock = datablock.encode("iso-8859-1")
                sys.audit("http.client.send", self, datablock)
                self.sock.sendall(datablock)
            return
        sys.audit("http.client.send", self, data)
        try:
            self.sock.sendall(data)
        except TypeError:
            wenn isinstance(data, collections.abc.Iterable):
                fuer d in data:
                    self.sock.sendall(d)
            sonst:
                raise TypeError("data should be a bytes-like object "
                                "or an iterable, got %r" % type(data))

    def _output(self, s):
        """Add a line of output to the current request buffer.

        Assumes that the line does *not* end mit \\r\\n.
        """
        self._buffer.append(s)

    def _read_readable(self, readable):
        wenn self.debuglevel > 0:
            drucke("reading a readable")
        encode = self._is_textIO(readable)
        wenn encode und self.debuglevel > 0:
            drucke("encoding file using iso-8859-1")
        waehrend datablock := readable.read(self.blocksize):
            wenn encode:
                datablock = datablock.encode("iso-8859-1")
            yield datablock

    def _send_output(self, message_body=Nichts, encode_chunked=Falsch):
        """Send the currently buffered request und clear the buffer.

        Appends an extra \\r\\n to the buffer.
        A message_body may be specified, to be appended to the request.
        """
        self._buffer.extend((b"", b""))
        msg = b"\r\n".join(self._buffer)
        del self._buffer[:]
        self.send(msg)

        wenn message_body is nicht Nichts:

            # create a consistent interface to message_body
            wenn hasattr(message_body, 'read'):
                # Let file-like take precedence over byte-like.  This
                # is needed to allow the current position of mmap'ed
                # files to be taken into account.
                chunks = self._read_readable(message_body)
            sonst:
                try:
                    # this is solely to check to see wenn message_body
                    # implements the buffer API.  it /would/ be easier
                    # to capture wenn PyObject_CheckBuffer was exposed
                    # to Python.
                    memoryview(message_body)
                except TypeError:
                    try:
                        chunks = iter(message_body)
                    except TypeError:
                        raise TypeError("message_body should be a bytes-like "
                                        "object oder an iterable, got %r"
                                        % type(message_body))
                sonst:
                    # the object implements the buffer interface und
                    # can be passed directly into socket methods
                    chunks = (message_body,)

            fuer chunk in chunks:
                wenn nicht chunk:
                    wenn self.debuglevel > 0:
                        drucke('Zero length chunk ignored')
                    weiter

                wenn encode_chunked und self._http_vsn == 11:
                    # chunked encoding
                    chunk = f'{len(chunk):X}\r\n'.encode('ascii') + chunk \
                        + b'\r\n'
                self.send(chunk)

            wenn encode_chunked und self._http_vsn == 11:
                # end chunked transfer
                self.send(b'0\r\n\r\n')

    def putrequest(self, method, url, skip_host=Falsch,
                   skip_accept_encoding=Falsch):
        """Send a request to the server.

        'method' specifies an HTTP request method, e.g. 'GET'.
        'url' specifies the object being requested, e.g. '/index.html'.
        'skip_host' wenn Wahr does nicht add automatically a 'Host:' header
        'skip_accept_encoding' wenn Wahr does nicht add automatically an
           'Accept-Encoding:' header
        """

        # wenn a prior response has been completed, then forget about it.
        wenn self.__response und self.__response.isclosed():
            self.__response = Nichts


        # in certain cases, we cannot issue another request on this connection.
        # this occurs when:
        #   1) we are in the process of sending a request.   (_CS_REQ_STARTED)
        #   2) a response to a previous request has signalled that it is going
        #      to close the connection upon completion.
        #   3) the headers fuer the previous response have nicht been read, thus
        #      we cannot determine whether point (2) is true.   (_CS_REQ_SENT)
        #
        # wenn there is no prior response, then we can request at will.
        #
        # wenn point (2) is true, then we will have passed the socket to the
        # response (effectively meaning, "there is no prior response"), und
        # will open a new one when a new request is made.
        #
        # Note: wenn a prior response exists, then we *can* start a new request.
        #       We are nicht allowed to begin fetching the response to this new
        #       request, however, until that prior response is complete.
        #
        wenn self.__state == _CS_IDLE:
            self.__state = _CS_REQ_STARTED
        sonst:
            raise CannotSendRequest(self.__state)

        self._validate_method(method)

        # Save the method fuer use later in the response phase
        self._method = method

        url = url oder '/'
        self._validate_path(url)

        request = '%s %s %s' % (method, url, self._http_vsn_str)

        self._output(self._encode_request(request))

        wenn self._http_vsn == 11:
            # Issue some standard headers fuer better HTTP/1.1 compliance

            wenn nicht skip_host:
                # this header is issued *only* fuer HTTP/1.1
                # connections. more specifically, this means it is
                # only issued when the client uses the new
                # HTTPConnection() class. backwards-compat clients
                # will be using HTTP/1.0 und those clients may be
                # issuing this header themselves. we should NOT issue
                # it twice; some web servers (such als Apache) barf
                # when they see two Host: headers

                # If we need a non-standard port,include it in the
                # header.  If the request is going through a proxy,
                # but the host of the actual URL, nicht the host of the
                # proxy.

                netloc = ''
                wenn url.startswith('http'):
                    nil, netloc, nil, nil, nil = urlsplit(url)

                wenn netloc:
                    try:
                        netloc_enc = netloc.encode("ascii")
                    except UnicodeEncodeError:
                        netloc_enc = netloc.encode("idna")
                    self.putheader('Host', _strip_ipv6_iface(netloc_enc))
                sonst:
                    wenn self._tunnel_host:
                        host = self._tunnel_host
                        port = self._tunnel_port
                    sonst:
                        host = self.host
                        port = self.port

                    try:
                        host_enc = host.encode("ascii")
                    except UnicodeEncodeError:
                        host_enc = host.encode("idna")

                    # As per RFC 273, IPv6 address should be wrapped mit []
                    # when used als Host header
                    host_enc = self._wrap_ipv6(host_enc)
                    wenn ":" in host:
                        host_enc = _strip_ipv6_iface(host_enc)

                    wenn port == self.default_port:
                        self.putheader('Host', host_enc)
                    sonst:
                        host_enc = host_enc.decode("ascii")
                        self.putheader('Host', "%s:%s" % (host_enc, port))

            # note: we are assuming that clients will nicht attempt to set these
            #       headers since *this* library must deal mit the
            #       consequences. this also means that when the supporting
            #       libraries are updated to recognize other forms, then this
            #       code should be changed (removed oder updated).

            # we only want a Content-Encoding of "identity" since we don't
            # support encodings such als x-gzip oder x-deflate.
            wenn nicht skip_accept_encoding:
                self.putheader('Accept-Encoding', 'identity')

            # we can accept "chunked" Transfer-Encodings, but no others
            # NOTE: no TE header implies *only* "chunked"
            #self.putheader('TE', 'chunked')

            # wenn TE is supplied in the header, then it must appear in a
            # Connection header.
            #self.putheader('Connection', 'TE')

        sonst:
            # For HTTP/1.0, the server will assume "not chunked"
            pass

    def _encode_request(self, request):
        # ASCII also helps prevent CVE-2019-9740.
        return request.encode('ascii')

    def _validate_method(self, method):
        """Validate a method name fuer putrequest."""
        # prevent http header injection
        match = _contains_disallowed_method_pchar_re.search(method)
        wenn match:
            raise ValueError(
                    f"method can't contain control characters. {method!r} "
                    f"(found at least {match.group()!r})")

    def _validate_path(self, url):
        """Validate a url fuer putrequest."""
        # Prevent CVE-2019-9740.
        match = _contains_disallowed_url_pchar_re.search(url)
        wenn match:
            raise InvalidURL(f"URL can't contain control characters. {url!r} "
                             f"(found at least {match.group()!r})")

    def _validate_host(self, host):
        """Validate a host so it doesn't contain control characters."""
        # Prevent CVE-2019-18348.
        match = _contains_disallowed_url_pchar_re.search(host)
        wenn match:
            raise InvalidURL(f"URL can't contain control characters. {host!r} "
                             f"(found at least {match.group()!r})")

    def putheader(self, header, *values):
        """Send a request header line to the server.

        For example: h.putheader('Accept', 'text/html')
        """
        wenn self.__state != _CS_REQ_STARTED:
            raise CannotSendHeader()

        wenn hasattr(header, 'encode'):
            header = header.encode('ascii')

        wenn nicht _is_legal_header_name(header):
            raise ValueError('Invalid header name %r' % (header,))

        values = list(values)
        fuer i, one_value in enumerate(values):
            wenn hasattr(one_value, 'encode'):
                values[i] = one_value.encode('latin-1')
            sowenn isinstance(one_value, int):
                values[i] = str(one_value).encode('ascii')

            wenn _is_illegal_header_value(values[i]):
                raise ValueError('Invalid header value %r' % (values[i],))

        value = b'\r\n\t'.join(values)
        header = header + b': ' + value
        self._output(header)

    def endheaders(self, message_body=Nichts, *, encode_chunked=Falsch):
        """Indicate that the last header line has been sent to the server.

        This method sends the request to the server.  The optional message_body
        argument can be used to pass a message body associated mit the
        request.
        """
        wenn self.__state == _CS_REQ_STARTED:
            self.__state = _CS_REQ_SENT
        sonst:
            raise CannotSendHeader()
        self._send_output(message_body, encode_chunked=encode_chunked)

    def request(self, method, url, body=Nichts, headers={}, *,
                encode_chunked=Falsch):
        """Send a complete request to the server."""
        self._send_request(method, url, body, headers, encode_chunked)

    def _send_request(self, method, url, body, headers, encode_chunked):
        # Honor explicitly requested Host: und Accept-Encoding: headers.
        header_names = frozenset(k.lower() fuer k in headers)
        skips = {}
        wenn 'host' in header_names:
            skips['skip_host'] = 1
        wenn 'accept-encoding' in header_names:
            skips['skip_accept_encoding'] = 1

        self.putrequest(method, url, **skips)

        # chunked encoding will happen wenn HTTP/1.1 is used und either
        # the caller passes encode_chunked=Wahr oder the following
        # conditions hold:
        # 1. content-length has nicht been explicitly set
        # 2. the body is a file oder iterable, but nicht a str oder bytes-like
        # 3. Transfer-Encoding has NOT been explicitly set by the caller

        wenn 'content-length' nicht in header_names:
            # only chunk body wenn nicht explicitly set fuer backwards
            # compatibility, assuming the client code is already handling the
            # chunking
            wenn 'transfer-encoding' nicht in header_names:
                # wenn content-length cannot be automatically determined, fall
                # back to chunked encoding
                encode_chunked = Falsch
                content_length = self._get_content_length(body, method)
                wenn content_length is Nichts:
                    wenn body is nicht Nichts:
                        wenn self.debuglevel > 0:
                            drucke('Unable to determine size of %r' % body)
                        encode_chunked = Wahr
                        self.putheader('Transfer-Encoding', 'chunked')
                sonst:
                    self.putheader('Content-Length', str(content_length))
        sonst:
            encode_chunked = Falsch

        fuer hdr, value in headers.items():
            self.putheader(hdr, value)
        wenn isinstance(body, str):
            # RFC 2616 Section 3.7.1 says that text default has a
            # default charset of iso-8859-1.
            body = _encode(body, 'body')
        self.endheaders(body, encode_chunked=encode_chunked)

    def getresponse(self):
        """Get the response von the server.

        If the HTTPConnection is in the correct state, returns an
        instance of HTTPResponse oder of whatever object is returned by
        the response_class variable.

        If a request has nicht been sent oder wenn a previous response has
        nicht be handled, ResponseNotReady is raised.  If the HTTP
        response indicates that the connection should be closed, then
        it will be closed before the response is returned.  When the
        connection is closed, the underlying socket is closed.
        """

        # wenn a prior response has been completed, then forget about it.
        wenn self.__response und self.__response.isclosed():
            self.__response = Nichts

        # wenn a prior response exists, then it must be completed (otherwise, we
        # cannot read this response's header to determine the connection-close
        # behavior)
        #
        # note: wenn a prior response existed, but was connection-close, then the
        # socket und response were made independent of this HTTPConnection
        # object since a new request requires that we open a whole new
        # connection
        #
        # this means the prior response had one of two states:
        #   1) will_close: this connection was reset und the prior socket und
        #                  response operate independently
        #   2) persistent: the response was retained und we await its
        #                  isclosed() status to become true.
        #
        wenn self.__state != _CS_REQ_SENT oder self.__response:
            raise ResponseNotReady(self.__state)

        wenn self.debuglevel > 0:
            response = self.response_class(self.sock, self.debuglevel,
                                           method=self._method)
        sonst:
            response = self.response_class(self.sock, method=self._method)

        try:
            try:
                wenn self.max_response_headers is Nichts:
                    response.begin()
                sonst:
                    response.begin(_max_headers=self.max_response_headers)
            except ConnectionError:
                self.close()
                raise
            assert response.will_close != _UNKNOWN
            self.__state = _CS_IDLE

            wenn response.will_close:
                # this effectively passes the connection to the response
                self.close()
            sonst:
                # remember this, so we can tell when it is complete
                self.__response = response

            return response
        except:
            response.close()
            raise

try:
    importiere ssl
except ImportError:
    pass
sonst:
    klasse HTTPSConnection(HTTPConnection):
        "This klasse allows communication via SSL."

        default_port = HTTPS_PORT

        def __init__(self, host, port=Nichts,
                     *, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                     source_address=Nichts, context=Nichts, blocksize=8192,
                     max_response_headers=Nichts):
            super(HTTPSConnection, self).__init__(host, port, timeout,
                                                  source_address,
                                                  blocksize=blocksize,
                                                  max_response_headers=max_response_headers)
            wenn context is Nichts:
                context = _create_https_context(self._http_vsn)
            self._context = context

        def connect(self):
            "Connect to a host on a given (SSL) port."

            super().connect()

            wenn self._tunnel_host:
                server_hostname = self._tunnel_host
            sonst:
                server_hostname = self.host

            self.sock = self._context.wrap_socket(self.sock,
                                                  server_hostname=server_hostname)

    __all__.append("HTTPSConnection")

klasse HTTPException(Exception):
    # Subclasses that define an __init__ must call Exception.__init__
    # oder define self.args.  Otherwise, str() will fail.
    pass

klasse NotConnected(HTTPException):
    pass

klasse InvalidURL(HTTPException):
    pass

klasse UnknownProtocol(HTTPException):
    def __init__(self, version):
        self.args = version,
        self.version = version

klasse UnknownTransferEncoding(HTTPException):
    pass

klasse UnimplementedFileMode(HTTPException):
    pass

klasse IncompleteRead(HTTPException):
    def __init__(self, partial, expected=Nichts):
        self.args = partial,
        self.partial = partial
        self.expected = expected
    def __repr__(self):
        wenn self.expected is nicht Nichts:
            e = ', %i more expected' % self.expected
        sonst:
            e = ''
        return '%s(%i bytes read%s)' % (self.__class__.__name__,
                                        len(self.partial), e)
    __str__ = object.__str__

klasse ImproperConnectionState(HTTPException):
    pass

klasse CannotSendRequest(ImproperConnectionState):
    pass

klasse CannotSendHeader(ImproperConnectionState):
    pass

klasse ResponseNotReady(ImproperConnectionState):
    pass

klasse BadStatusLine(HTTPException):
    def __init__(self, line):
        wenn nicht line:
            line = repr(line)
        self.args = line,
        self.line = line

klasse LineTooLong(HTTPException):
    def __init__(self, line_type):
        HTTPException.__init__(self, "got more than %d bytes when reading %s"
                                     % (_MAXLINE, line_type))

klasse RemoteDisconnected(ConnectionResetError, BadStatusLine):
    def __init__(self, *pos, **kw):
        BadStatusLine.__init__(self, "")
        ConnectionResetError.__init__(self, *pos, **kw)

# fuer backwards compatibility
error = HTTPException
