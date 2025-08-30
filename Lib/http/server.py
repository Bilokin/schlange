"""HTTP server classes.

Note: BaseHTTPRequestHandler doesn't implement any HTTP request; see
SimpleHTTPRequestHandler fuer simple implementations of GET, HEAD und POST.

It does, however, optionally implement HTTP/1.1 persistent connections.

XXX To do:

- log requests even later (to capture byte count)
- log user-agent header und other interesting goodies
- send error log to separate file
"""


# See also:
#
# HTTP Working Group                                        T. Berners-Lee
# INTERNET-DRAFT                                            R. T. Fielding
# <draft-ietf-http-v10-spec-00.txt>                     H. Frystyk Nielsen
# Expires September 8, 1995                                  March 8, 1995
#
# URL: http://www.ics.uci.edu/pub/ietf/http/draft-ietf-http-v10-spec-00.txt
#
# und
#
# Network Working Group                                      R. Fielding
# Request fuer Comments: 2616                                       et al
# Obsoletes: 2068                                              June 1999
# Category: Standards Track
#
# URL: http://www.faqs.org/rfcs/rfc2616.html

# Log files
# ---------
#
# Here's a quote von the NCSA httpd docs about log file format.
#
# | The logfile format ist als follows. Each line consists of:
# |
# | host rfc931 authuser [DD/Mon/YYYY:hh:mm:ss] "request" ddd bbbb
# |
# |        host: Either the DNS name oder the IP number of the remote client
# |        rfc931: Any information returned by identd fuer this person,
# |                - otherwise.
# |        authuser: If user sent a userid fuer authentication, the user name,
# |                  - otherwise.
# |        DD: Day
# |        Mon: Month (calendar name)
# |        YYYY: Year
# |        hh: hour (24-hour format, the machine's timezone)
# |        mm: minutes
# |        ss: seconds
# |        request: The first line of the HTTP request als sent by the client.
# |        ddd: the status code returned by the server, - wenn nicht available.
# |        bbbb: the total number of bytes sent,
# |              *not including the HTTP/1.0 header*, - wenn nicht available
# |
# | You can determine the name of the file accessed through request.
#
# (Actually, the latter ist only true wenn you know the server configuration
# at the time the request was made!)

__version__ = "0.6"

__all__ = [
    "HTTPServer", "ThreadingHTTPServer",
    "HTTPSServer", "ThreadingHTTPSServer",
    "BaseHTTPRequestHandler", "SimpleHTTPRequestHandler",
]

importiere datetime
importiere email.utils
importiere html
importiere http.client
importiere io
importiere itertools
importiere mimetypes
importiere os
importiere posixpath
importiere shutil
importiere socket
importiere socketserver
importiere sys
importiere time
importiere urllib.parse

von http importiere HTTPStatus


# Default error message template
DEFAULT_ERROR_MESSAGE = """\
<!DOCTYPE HTML>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <style type="text/css">
            :root {
                color-scheme: light dark;
            }
        </style>
        <title>Error response</title>
    </head>
    <body>
        <h1>Error response</h1>
        <p>Error code: %(code)d</p>
        <p>Message: %(message)s.</p>
        <p>Error code explanation: %(code)s - %(explain)s.</p>
    </body>
</html>
"""

DEFAULT_ERROR_CONTENT_TYPE = "text/html;charset=utf-8"

klasse HTTPServer(socketserver.TCPServer):

    allow_reuse_address = Wahr    # Seems to make sense in testing environment
    allow_reuse_port = Falsch

    def server_bind(self):
        """Override server_bind to store the server name."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port


klasse ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = Wahr


klasse HTTPSServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass,
                 bind_and_activate=Wahr, *, certfile, keyfile=Nichts,
                 password=Nichts, alpn_protocols=Nichts):
        versuch:
            importiere ssl
        ausser ImportError:
            wirf RuntimeError("SSL module ist missing; "
                               "HTTPS support ist unavailable")

        self.ssl = ssl
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        # Support by default HTTP/1.1
        self.alpn_protocols = (
            ["http/1.1"] wenn alpn_protocols ist Nichts sonst alpn_protocols
        )

        super().__init__(server_address,
                         RequestHandlerClass,
                         bind_and_activate)

    def server_activate(self):
        """Wrap the socket in SSLSocket."""
        super().server_activate()
        context = self._create_context()
        self.socket = context.wrap_socket(self.socket, server_side=Wahr)

    def _create_context(self):
        """Create a secure SSL context."""
        context = self.ssl.create_default_context(self.ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(self.certfile, self.keyfile, self.password)
        context.set_alpn_protocols(self.alpn_protocols)
        gib context


klasse ThreadingHTTPSServer(socketserver.ThreadingMixIn, HTTPSServer):
    daemon_threads = Wahr


klasse BaseHTTPRequestHandler(socketserver.StreamRequestHandler):

    """HTTP request handler base class.

    The following explanation of HTTP serves to guide you through the
    code als well als to expose any misunderstandings I may have about
    HTTP (so you don't need to read the code to figure out I'm wrong
    :-).

    HTTP (HyperText Transfer Protocol) ist an extensible protocol on
    top of a reliable stream transport (e.g. TCP/IP).  The protocol
    recognizes three parts to a request:

    1. One line identifying the request type und path
    2. An optional set of RFC-822-style headers
    3. An optional data part

    The headers und data are separated by a blank line.

    The first line of the request has the form

    <command> <path> <version>

    where <command> ist a (case-sensitive) keyword such als GET oder POST,
    <path> ist a string containing path information fuer the request,
    und <version> should be the string "HTTP/1.0" oder "HTTP/1.1".
    <path> ist encoded using the URL encoding scheme (using %xx to signify
    the ASCII character mit hex code xx).

    The specification specifies that lines are separated by CRLF but
    fuer compatibility mit the widest range of clients recommends
    servers also handle LF.  Similarly, whitespace in the request line
    ist treated sensibly (allowing multiple spaces between components
    und allowing trailing whitespace).

    Similarly, fuer output, lines ought to be separated by CRLF pairs
    but most clients grok LF characters just fine.

    If the first line of the request has the form

    <command> <path>

    (i.e. <version> ist left out) then this ist assumed to be an HTTP
    0.9 request; this form has no optional headers und data part und
    the reply consists of just the data.

    The reply form of the HTTP 1.x protocol again has three parts:

    1. One line giving the response code
    2. An optional set of RFC-822-style headers
    3. The data

    Again, the headers und data are separated by a blank line.

    The response code line has the form

    <version> <responsecode> <responsestring>

    where <version> ist the protocol version ("HTTP/1.0" oder "HTTP/1.1"),
    <responsecode> ist a 3-digit response code indicating success oder
    failure of the request, und <responsestring> ist an optional
    human-readable string explaining what the response code means.

    This server parses the request und the headers, und then calls a
    function specific to the request type (<command>).  Specifically,
    a request SPAM will be handled by a method do_SPAM().  If no
    such method exists the server sends an error response to the
    client.  If it exists, it ist called mit no arguments:

    do_SPAM()

    Note that the request name ist case sensitive (i.e. SPAM und spam
    are different requests).

    The various request details are stored in instance variables:

    - client_address ist the client IP address in the form (host,
    port);

    - command, path und version are the broken-down request line;

    - headers ist an instance of email.message.Message (or a derived
    class) containing the header information;

    - rfile ist a file object open fuer reading positioned at the
    start of the optional input data part;

    - wfile ist a file object open fuer writing.

    IT IS IMPORTANT TO ADHERE TO THE PROTOCOL FOR WRITING!

    The first thing to be written must be the response line.  Then
    follow 0 oder more header lines, then a blank line, und then the
    actual data (if any).  The meaning of the header lines depends on
    the command executed by the server; in most cases, when data is
    returned, there should be at least one header line of the form

    Content-type: <type>/<subtype>

    where <type> und <subtype> should be registered MIME types,
    e.g. "text/html" oder "text/plain".

    """

    # The Python system version, truncated to its first component.
    sys_version = "Python/" + sys.version.split()[0]

    # The server software version.  You may want to override this.
    # The format ist multiple whitespace-separated strings,
    # where each string ist of the form name[/version].
    server_version = "BaseHTTP/" + __version__

    error_message_format = DEFAULT_ERROR_MESSAGE
    error_content_type = DEFAULT_ERROR_CONTENT_TYPE

    # The default request version.  This only affects responses up until
    # the point where the request line ist parsed, so it mainly decides what
    # the client gets back when sending a malformed request line.
    # Most web servers default to HTTP 0.9, i.e. don't send a status line.
    default_request_version = "HTTP/0.9"

    def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version und
        self.headers.

        Return Wahr fuer success, Falsch fuer failure; on failure, any relevant
        error response has already been sent back.

        """
        self.command = Nichts  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = Wahr
        requestline = str(self.raw_requestline, 'iso-8859-1')
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()
        wenn len(words) == 0:
            gib Falsch

        wenn len(words) >= 3:  # Enough to determine protocol version
            version = words[-1]
            versuch:
                wenn nicht version.startswith('HTTP/'):
                    wirf ValueError
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." und
                #   - major und minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 ist a lower version than HTTP/2.13, which in
                #      turn ist lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                wenn len(version_number) != 2:
                    wirf ValueError
                wenn any(nicht component.isdigit() fuer component in version_number):
                    wirf ValueError("non digit in http version")
                wenn any(len(component) > 10 fuer component in version_number):
                    wirf ValueError("unreasonable length http version")
                version_number = int(version_number[0]), int(version_number[1])
            ausser (ValueError, IndexError):
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    "Bad request version (%r)" % version)
                gib Falsch
            wenn version_number >= (1, 1) und self.protocol_version >= "HTTP/1.1":
                self.close_connection = Falsch
            wenn version_number >= (2, 0):
                self.send_error(
                    HTTPStatus.HTTP_VERSION_NOT_SUPPORTED,
                    "Invalid HTTP version (%s)" % base_version_number)
                gib Falsch
            self.request_version = version

        wenn nicht 2 <= len(words) <= 3:
            self.send_error(
                HTTPStatus.BAD_REQUEST,
                "Bad request syntax (%r)" % requestline)
            gib Falsch
        command, path = words[:2]
        wenn len(words) == 2:
            self.close_connection = Wahr
            wenn command != 'GET':
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    "Bad HTTP/0.9 request type (%r)" % command)
                gib Falsch
        self.command, self.path = command, path

        # gh-87389: The purpose of replacing '//' mit '/' ist to protect
        # against open redirect attacks possibly triggered wenn the path starts
        # mit '//' because http clients treat //path als an absolute URI
        # without scheme (similar to http://path) rather than a path.
        wenn self.path.startswith('//'):
            self.path = '/' + self.path.lstrip('/')  # Reduce to a single /

        # Examine the headers und look fuer a Connection directive.
        versuch:
            self.headers = http.client.parse_headers(self.rfile,
                                                     _class=self.MessageClass)
        ausser http.client.LineTooLong als err:
            self.send_error(
                HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
                "Line too long",
                str(err))
            gib Falsch
        ausser http.client.HTTPException als err:
            self.send_error(
                HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
                "Too many headers",
                str(err)
            )
            gib Falsch

        conntype = self.headers.get('Connection', "")
        wenn conntype.lower() == 'close':
            self.close_connection = Wahr
        sowenn (conntype.lower() == 'keep-alive' und
              self.protocol_version >= "HTTP/1.1"):
            self.close_connection = Falsch
        # Examine the headers und look fuer an Expect directive
        expect = self.headers.get('Expect', "")
        wenn (expect.lower() == "100-continue" und
                self.protocol_version >= "HTTP/1.1" und
                self.request_version >= "HTTP/1.1"):
            wenn nicht self.handle_expect_100():
                gib Falsch
        gib Wahr

    def handle_expect_100(self):
        """Decide what to do mit an "Expect: 100-continue" header.

        If the client ist expecting a 100 Continue response, we must
        respond mit either a 100 Continue oder a final response before
        waiting fuer the request body. The default ist to always respond
        mit a 100 Continue. You can behave differently (for example,
        reject unauthorized requests) by overriding this method.

        This method should either gib Wahr (possibly after sending
        a 100 Continue response) oder send an error response und gib
        Falsch.

        """
        self.send_response_only(HTTPStatus.CONTINUE)
        self.end_headers()
        gib Wahr

    def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string fuer information on how to handle specific HTTP
        commands such als GET und POST.

        """
        versuch:
            self.raw_requestline = self.rfile.readline(65537)
            wenn len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                gib
            wenn nicht self.raw_requestline:
                self.close_connection = Wahr
                gib
            wenn nicht self.parse_request():
                # An error code has been sent, just exit
                gib
            mname = 'do_' + self.command
            wenn nicht hasattr(self, mname):
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
                gib
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response wenn nicht already done.
        ausser TimeoutError als e:
            #a read oder a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = Wahr
            gib

    def handle(self):
        """Handle multiple requests wenn necessary."""
        self.close_connection = Wahr

        self.handle_one_request()
        waehrend nicht self.close_connection:
            self.handle_one_request()

    def send_error(self, code, message=Nichts, explain=Nichts):
        """Send und log an error reply.

        Arguments are
        * code:    an HTTP error code
                   3 digits
        * message: a simple optional 1 line reason phrase.
                   *( HTAB / SP / VCHAR / %x80-FF )
                   defaults to short entry matching the response code
        * explain: a detailed message defaults to the long entry
                   matching the response code.

        This sends an error response (so it must be called before any
        output has been generated), logs the error, und finally sends
        a piece of HTML explaining the error to the user.

        """

        versuch:
            shortmsg, longmsg = self.responses[code]
        ausser KeyError:
            shortmsg, longmsg = '???', '???'
        wenn message ist Nichts:
            message = shortmsg
        wenn explain ist Nichts:
            explain = longmsg
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.send_header('Connection', 'close')

        # Message body ist omitted fuer cases described in:
        #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
        #  - RFC7231: 6.3.6. 205(Reset Content)
        body = Nichts
        wenn (code >= 200 und
            code nicht in (HTTPStatus.NO_CONTENT,
                         HTTPStatus.RESET_CONTENT,
                         HTTPStatus.NOT_MODIFIED)):
            # HTML encode to prevent Cross Site Scripting attacks
            # (see bug #1100201)
            content = (self.error_message_format % {
                'code': code,
                'message': html.escape(message, quote=Falsch),
                'explain': html.escape(explain, quote=Falsch)
            })
            body = content.encode('UTF-8', 'replace')
            self.send_header("Content-Type", self.error_content_type)
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()

        wenn self.command != 'HEAD' und body:
            self.wfile.write(body)

    def send_response(self, code, message=Nichts):
        """Add the response header to the headers buffer und log the
        response code.

        Also send two standard headers mit the server software
        version und the current date.

        """
        self.log_request(code)
        self.send_response_only(code, message)
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

    def send_response_only(self, code, message=Nichts):
        """Send the response header only."""
        wenn self.request_version != 'HTTP/0.9':
            wenn message ist Nichts:
                wenn code in self.responses:
                    message = self.responses[code][0]
                sonst:
                    message = ''
            wenn nicht hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(("%s %d %s\r\n" %
                    (self.protocol_version, code, message)).encode(
                        'latin-1', 'strict'))

    def send_header(self, keyword, value):
        """Send a MIME header to the headers buffer."""
        wenn self.request_version != 'HTTP/0.9':
            wenn nicht hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(
                ("%s: %s\r\n" % (keyword, value)).encode('latin-1', 'strict'))

        wenn keyword.lower() == 'connection':
            wenn value.lower() == 'close':
                self.close_connection = Wahr
            sowenn value.lower() == 'keep-alive':
                self.close_connection = Falsch

    def end_headers(self):
        """Send the blank line ending the MIME headers."""
        wenn self.request_version != 'HTTP/0.9':
            self._headers_buffer.append(b"\r\n")
            self.flush_headers()

    def flush_headers(self):
        wenn hasattr(self, '_headers_buffer'):
            self.wfile.write(b"".join(self._headers_buffer))
            self._headers_buffer = []

    def log_request(self, code='-', size='-'):
        """Log an accepted request.

        This ist called by send_response().

        """
        wenn isinstance(code, HTTPStatus):
            code = code.value
        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def log_error(self, format, *args):
        """Log an error.

        This ist called when a request cannot be fulfilled.  By
        default it passes the message on to log_message().

        Arguments are the same als fuer log_message().

        XXX This should go to the separate error log.

        """

        self.log_message(format, *args)

    # https://en.wikipedia.org/wiki/List_of_Unicode_characters#Control_codes
    _control_char_table = str.maketrans(
            {c: fr'\x{c:02x}' fuer c in itertools.chain(range(0x20), range(0x7f,0xa0))})
    _control_char_table[ord('\\')] = r'\\'

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This ist used by all other logging functions.  Override
        it wenn you have specific logging wishes.

        The first argument, FORMAT, ist a format string fuer the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified als subsequent arguments (it's just like
        printf!).

        The client ip und current date/time are prefixed to
        every message.

        Unicode control characters are replaced mit escaped hex
        before writing the output to stderr.

        """

        message = format % args
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          message.translate(self._control_char_table)))

    def version_string(self):
        """Return the server software version string."""
        gib self.server_version + ' ' + self.sys_version

    def date_time_string(self, timestamp=Nichts):
        """Return the current date und time formatted fuer a message header."""
        wenn timestamp ist Nichts:
            timestamp = time.time()
        gib email.utils.formatdate(timestamp, usegmt=Wahr)

    def log_date_time_string(self):
        """Return the current time formatted fuer logging."""
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%02d/%3s/%04d %02d:%02d:%02d" % (
                day, self.monthname[month], year, hh, mm, ss)
        gib s

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    monthname = [Nichts,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def address_string(self):
        """Return the client address."""

        gib self.client_address[0]

    # Essentially static klasse variables

    # The version of the HTTP protocol we support.
    # Set this to HTTP/1.1 to enable automatic keepalive
    protocol_version = "HTTP/1.0"

    # MessageClass used to parse headers
    MessageClass = http.client.HTTPMessage

    # hack to maintain backwards compatibility
    responses = {
        v: (v.phrase, v.description)
        fuer v in HTTPStatus.__members__.values()
    }


klasse SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    """Simple HTTP request handler mit GET und HEAD commands.

    This serves files von the current directory und any of its
    subdirectories.  The MIME type fuer files ist determined by
    calling the .guess_type() method.

    The GET und HEAD requests are identical ausser that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTP/" + __version__
    index_pages = ("index.html", "index.htm")
    extensions_map = _encodings_map_default = {
        '.gz': 'application/gzip',
        '.Z': 'application/octet-stream',
        '.bz2': 'application/x-bzip2',
        '.xz': 'application/x-xz',
    }

    def __init__(self, *args, directory=Nichts, **kwargs):
        wenn directory ist Nichts:
            directory = os.getcwd()
        self.directory = os.fspath(directory)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        wenn f:
            versuch:
                self.copyfile(f, self.wfile)
            schliesslich:
                f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        wenn f:
            f.close()

    def send_head(self):
        """Common code fuer GET und HEAD commands.

        This sends the response code und MIME headers.

        Return value ist either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        und must be closed by the caller under all circumstances), oder
        Nichts, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = Nichts
        wenn os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            wenn nicht parts.path.endswith(('/', '%2f', '%2F')):
                # redirect browser - doing basically what apache does
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                gib Nichts
            fuer index in self.index_pages:
                index = os.path.join(path, index)
                wenn os.path.isfile(index):
                    path = index
                    breche
            sonst:
                gib self.list_directory(path)
        ctype = self.guess_type(path)
        # check fuer trailing "/" which should gib 404. See Issue17324
        # The test fuer this was added in test_httpserver.py
        # However, some OS platforms accept a trailingSlash als a filename
        # See discussion on python-dev und Issue34711 regarding
        # parsing und rejection of filenames mit a trailing slash
        wenn path.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND, "File nicht found")
            gib Nichts
        versuch:
            f = open(path, 'rb')
        ausser OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File nicht found")
            gib Nichts

        versuch:
            fs = os.fstat(f.fileno())
            # Use browser cache wenn possible
            wenn ("If-Modified-Since" in self.headers
                    und "If-Nichts-Match" nicht in self.headers):
                # compare If-Modified-Since und time of last file modification
                versuch:
                    ims = email.utils.parsedate_to_datetime(
                        self.headers["If-Modified-Since"])
                ausser (TypeError, IndexError, OverflowError, ValueError):
                    # ignore ill-formed values
                    pass
                sonst:
                    wenn ims.tzinfo ist Nichts:
                        # obsolete format mit no timezone, cf.
                        # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    wenn ims.tzinfo ist datetime.timezone.utc:
                        # compare to UTC datetime of last modification
                        last_modif = datetime.datetime.fromtimestamp(
                            fs.st_mtime, datetime.timezone.utc)
                        # remove microseconds, like in If-Modified-Since
                        last_modif = last_modif.replace(microsecond=0)

                        wenn last_modif <= ims:
                            self.send_response(HTTPStatus.NOT_MODIFIED)
                            self.end_headers()
                            f.close()
                            gib Nichts

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified",
                self.date_time_string(fs.st_mtime))
            self.end_headers()
            gib f
        ausser:
            f.close()
            wirf

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value ist either a file object, oder Nichts (indicating an
        error).  In either case, the headers are sent, making the
        interface the same als fuer send_head().

        """
        versuch:
            list = os.listdir(path)
        ausser OSError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No permission to list directory")
            gib Nichts
        list.sort(key=lambda a: a.lower())
        r = []
        displaypath = self.path
        displaypath = displaypath.split('#', 1)[0]
        displaypath = displaypath.split('?', 1)[0]
        versuch:
            displaypath = urllib.parse.unquote(displaypath,
                                               errors='surrogatepass')
        ausser UnicodeDecodeError:
            displaypath = urllib.parse.unquote(displaypath)
        displaypath = html.escape(displaypath, quote=Falsch)
        enc = sys.getfilesystemencoding()
        title = f'Directory listing fuer {displaypath}'
        r.append('<!DOCTYPE HTML>')
        r.append('<html lang="en">')
        r.append('<head>')
        r.append(f'<meta charset="{enc}">')
        r.append('<style type="text/css">\n:root {\ncolor-scheme: light dark;\n}\n</style>')
        r.append(f'<title>{title}</title>\n</head>')
        r.append(f'<body>\n<h1>{title}</h1>')
        r.append('<hr>\n<ul>')
        fuer name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / fuer directories oder @ fuer symbolic links
            wenn os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            wenn os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays mit @ und links mit /
            r.append('<li><a href="%s">%s</a></li>'
                    % (urllib.parse.quote(linkname,
                                          errors='surrogatepass'),
                       html.escape(displayname, quote=Falsch)))
        r.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        gib f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive oder directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('#', 1)[0]
        path = path.split('?', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        versuch:
            path = urllib.parse.unquote(path, errors='surrogatepass')
        ausser UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        trailing_slash = path.endswith('/')
        path = posixpath.normpath(path)
        words = path.split('/')
        words = filter(Nichts, words)
        path = self.directory
        fuer word in words:
            wenn os.path.dirname(word) oder word in (os.curdir, os.pardir):
                # Ignore components that are nicht a simple file/directory name
                weiter
            path = os.path.join(path, word)
        wenn trailing_slash:
            path += '/'
        gib path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument ist a file object open fuer reading
        (or anything mit a read() method) und the DESTINATION
        argument ist a file object open fuer writing (or
        anything mit a write() method).

        The only reason fuer overriding this would be to change
        the block size oder perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data als well.

        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument ist a PATH (a filename).

        Return value ist a string of the form type/subtype,
        usable fuer a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        als a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """
        base, ext = posixpath.splitext(path)
        wenn ext in self.extensions_map:
            gib self.extensions_map[ext]
        ext = ext.lower()
        wenn ext in self.extensions_map:
            gib self.extensions_map[ext]
        guess, _ = mimetypes.guess_file_type(path)
        wenn guess:
            gib guess
        gib 'application/octet-stream'


nobody = Nichts

def nobody_uid():
    """Internal routine to get nobody's uid"""
    global nobody
    wenn nobody:
        gib nobody
    versuch:
        importiere pwd
    ausser ImportError:
        gib -1
    versuch:
        nobody = pwd.getpwnam('nobody')[2]
    ausser KeyError:
        nobody = 1 + max(x[2] fuer x in pwd.getpwall())
    gib nobody


def executable(path):
    """Test fuer executable file."""
    gib os.access(path, os.X_OK)


def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    gib family, sockaddr


def test(HandlerClass=BaseHTTPRequestHandler,
         ServerClass=ThreadingHTTPServer,
         protocol="HTTP/1.0", port=8000, bind=Nichts,
         tls_cert=Nichts, tls_key=Nichts, tls_password=Nichts):
    """Test the HTTP request handler class.

    This runs an HTTP server on port 8000 (or the port argument).

    """
    ServerClass.address_family, addr = _get_best_family(bind, port)
    HandlerClass.protocol_version = protocol

    wenn tls_cert:
        server = ServerClass(addr, HandlerClass, certfile=tls_cert,
                             keyfile=tls_key, password=tls_password)
    sonst:
        server = ServerClass(addr, HandlerClass)

    mit server als httpd:
        host, port = httpd.socket.getsockname()[:2]
        url_host = f'[{host}]' wenn ':' in host sonst host
        protocol = 'HTTPS' wenn tls_cert sonst 'HTTP'
        drucke(
            f"Serving {protocol} on {host} port {port} "
            f"({protocol.lower()}://{url_host}:{port}/) ..."
        )
        versuch:
            httpd.serve_forever()
        ausser KeyboardInterrupt:
            drucke("\nKeyboard interrupt received, exiting.")
            sys.exit(0)


def _main(args=Nichts):
    importiere argparse
    importiere contextlib

    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument('-b', '--bind', metavar='ADDRESS',
                        help='bind to this address '
                             '(default: all interfaces)')
    parser.add_argument('-d', '--directory', default=os.getcwd(),
                        help='serve this directory '
                             '(default: current directory)')
    parser.add_argument('-p', '--protocol', metavar='VERSION',
                        default='HTTP/1.0',
                        help='conform to this HTTP version '
                             '(default: %(default)s)')
    parser.add_argument('--tls-cert', metavar='PATH',
                        help='path to the TLS certificate chain file')
    parser.add_argument('--tls-key', metavar='PATH',
                        help='path to the TLS key file')
    parser.add_argument('--tls-password-file', metavar='PATH',
                        help='path to the password file fuer the TLS key')
    parser.add_argument('port', default=8000, type=int, nargs='?',
                        help='bind to this port '
                             '(default: %(default)s)')
    args = parser.parse_args(args)

    wenn nicht args.tls_cert und args.tls_key:
        parser.error("--tls-key requires --tls-cert to be set")

    tls_key_password = Nichts
    wenn args.tls_password_file:
        wenn nicht args.tls_cert:
            parser.error("--tls-password-file requires --tls-cert to be set")

        versuch:
            mit open(args.tls_password_file, "r", encoding="utf-8") als f:
                tls_key_password = f.read().strip()
        ausser OSError als e:
            parser.error(f"Failed to read TLS password file: {e}")

    # ensure dual-stack ist nicht disabled; ref #38907
    klasse DualStackServerMixin:

        def server_bind(self):
            # suppress exception when protocol ist IPv4
            mit contextlib.suppress(Exception):
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            gib super().server_bind()

        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address, self,
                                     directory=args.directory)

    klasse HTTPDualStackServer(DualStackServerMixin, ThreadingHTTPServer):
        pass
    klasse HTTPSDualStackServer(DualStackServerMixin, ThreadingHTTPSServer):
        pass

    ServerClass = HTTPSDualStackServer wenn args.tls_cert sonst HTTPDualStackServer

    test(
        HandlerClass=SimpleHTTPRequestHandler,
        ServerClass=ServerClass,
        port=args.port,
        bind=args.bind,
        protocol=args.protocol,
        tls_cert=args.tls_cert,
        tls_key=args.tls_key,
        tls_password=tls_key_password,
    )


wenn __name__ == '__main__':
    _main()
