"""Base classes fuer server/gateway implementations"""

von .util importiere FileWrapper, guess_scheme, is_hop_by_hop
von .headers importiere Headers

importiere sys, os, time

__all__ = [
    'BaseHandler', 'SimpleHandler', 'BaseCGIHandler', 'CGIHandler',
    'IISCGIHandler', 'read_environ'
]

# Weekday und month names fuer HTTP date/time formatting; always English!
_weekdayname = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_monthname = [Nichts, # Dummy so we can use 1-based month numbers
              "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def format_date_time(timestamp):
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
    gib "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
        _weekdayname[wd], day, _monthname[month], year, hh, mm, ss
    )

_is_request = {
    'SCRIPT_NAME', 'PATH_INFO', 'QUERY_STRING', 'REQUEST_METHOD', 'AUTH_TYPE',
    'CONTENT_TYPE', 'CONTENT_LENGTH', 'HTTPS', 'REMOTE_USER', 'REMOTE_IDENT',
}.__contains__

def _needs_transcode(k):
    gib _is_request(k) oder k.startswith('HTTP_') oder k.startswith('SSL_') \
        oder (k.startswith('REDIRECT_') und _needs_transcode(k[9:]))

def read_environ():
    """Read environment, fixing HTTP variables"""
    enc = sys.getfilesystemencoding()
    esc = 'surrogateescape'
    versuch:
        ''.encode('utf-8', esc)
    ausser LookupError:
        esc = 'replace'
    environ = {}

    # Take the basic environment von native-unicode os.environ. Attempt to
    # fix up the variables that come von the HTTP request to compensate for
    # the bytes->unicode decoding step that will already have taken place.
    fuer k, v in os.environ.items():
        wenn _needs_transcode(k):

            # On win32, the os.environ ist natively Unicode. Different servers
            # decode the request bytes using different encodings.
            wenn sys.platform == 'win32':
                software = os.environ.get('SERVER_SOFTWARE', '').lower()

                # On IIS, the HTTP request will be decoded als UTF-8 als long
                # als the input ist a valid UTF-8 sequence. Otherwise it is
                # decoded using the system code page (mbcs), mit no way to
                # detect this has happened. Because UTF-8 ist the more likely
                # encoding, und mbcs ist inherently unreliable (an mbcs string
                # that happens to be valid UTF-8 will nicht be decoded als mbcs)
                # always recreate the original bytes als UTF-8.
                wenn software.startswith('microsoft-iis/'):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # Apache mod_cgi writes bytes-as-unicode (as wenn ISO-8859-1) direct
                # to the Unicode environ. No modification needed.
                sowenn software.startswith('apache/'):
                    pass

                # Python 3's http.server.CGIHTTPRequestHandler decodes
                # using the urllib.unquote default of UTF-8, amongst other
                # issues. While the CGI handler ist removed in 3.15, this
                # ist kept fuer legacy reasons.
                sowenn (
                    software.startswith('simplehttp/')
                    und 'python/3' in software
                ):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # For other servers, guess that they have written bytes to
                # the environ using stdio byte-oriented interfaces, ending up
                # mit the system code page.
                sonst:
                    v = v.encode(enc, 'replace').decode('iso-8859-1')

            # Recover bytes von unicode environ, using surrogate escapes
            # where available (Python 3.1+).
            sonst:
                v = v.encode(enc, esc).decode('iso-8859-1')

        environ[k] = v
    gib environ


klasse BaseHandler:
    """Manage the invocation of a WSGI application"""

    # Configuration parameters; can override per-subclass oder per-instance
    wsgi_version = (1,0)
    wsgi_multithread = Wahr
    wsgi_multiprocess = Wahr
    wsgi_run_once = Falsch

    origin_server = Wahr    # We are transmitting direct to client
    http_version  = "1.0"   # Version that should be used fuer response
    server_software = Nichts  # String name of server software, wenn any

    # os_environ ist used to supply configuration von the OS environment:
    # by default it's a copy of 'os.environ' als of importiere time, but you can
    # override this in e.g. your __init__ method.
    os_environ= read_environ()

    # Collaborator classes
    wsgi_file_wrapper = FileWrapper     # set to Nichts to disable
    headers_class = Headers             # must be a Headers-like class

    # Error handling (also per-subclass oder per-instance)
    traceback_limit = Nichts  # Print entire traceback to self.get_stderr()
    error_status = "500 Internal Server Error"
    error_headers = [('Content-Type','text/plain')]
    error_body = b"A server error occurred.  Please contact the administrator."

    # State variables (don't mess mit these)
    status = result = Nichts
    headers_sent = Falsch
    headers = Nichts
    bytes_sent = 0

    def run(self, application):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() von finish_response(), so wenn you close() anywhere but
        # the double-error branch here, you'll breche asynchronous servers by
        # prematurely closing.  Async servers must gib von 'run()' without
        # closing wenn there might still be output to iterate over.
        versuch:
            self.setup_environ()
            self.result = application(self.environ, self.start_response)
            self.finish_response()
        ausser (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            # We expect the client to close the connection abruptly von time
            # to time.
            gib
        ausser:
            versuch:
                self.handle_error()
            ausser:
                # If we get an error handling an error, just give up already!
                self.close()
                wirf   # ...and let the actual server figure it out.


    def setup_environ(self):
        """Set up the environment fuer one request"""

        env = self.environ = self.os_environ.copy()
        self.add_cgi_vars()

        env['wsgi.input']        = self.get_stdin()
        env['wsgi.errors']       = self.get_stderr()
        env['wsgi.version']      = self.wsgi_version
        env['wsgi.run_once']     = self.wsgi_run_once
        env['wsgi.url_scheme']   = self.get_scheme()
        env['wsgi.multithread']  = self.wsgi_multithread
        env['wsgi.multiprocess'] = self.wsgi_multiprocess

        wenn self.wsgi_file_wrapper ist nicht Nichts:
            env['wsgi.file_wrapper'] = self.wsgi_file_wrapper

        wenn self.origin_server und self.server_software:
            env.setdefault('SERVER_SOFTWARE',self.server_software)


    def finish_response(self):
        """Send any iterable data, then close self und the iterable

        Subclasses intended fuer use in asynchronous servers will
        want to redefine this method, such that it sets up callbacks
        in the event loop to iterate over the data, und to call
        'self.close()' once the response ist finished.
        """
        versuch:
            wenn nicht self.result_is_file() oder nicht self.sendfile():
                fuer data in self.result:
                    self.write(data)
                self.finish_content()
        ausser:
            # Call close() on the iterable returned by the WSGI application
            # in case of an exception.
            wenn hasattr(self.result, 'close'):
                self.result.close()
            wirf
        sonst:
            # We only call close() when no exception ist raised, because it
            # will set status, result, headers, und environ fields to Nichts.
            # See bpo-29183 fuer more details.
            self.close()


    def get_scheme(self):
        """Return the URL scheme being used"""
        gib guess_scheme(self.environ)


    def set_content_length(self):
        """Compute Content-Length oder switch to chunked encoding wenn possible"""
        versuch:
            blocks = len(self.result)
        ausser (TypeError,AttributeError,NotImplementedError):
            pass
        sonst:
            wenn blocks==1:
                self.headers['Content-Length'] = str(self.bytes_sent)
                gib
        # XXX Try fuer chunked encoding wenn origin server und client ist 1.1


    def cleanup_headers(self):
        """Make any necessary header changes oder defaults

        Subclasses can extend this to add other defaults.
        """
        wenn 'Content-Length' nicht in self.headers:
            self.set_content_length()

    def start_response(self, status, headers,exc_info=Nichts):
        """'start_response()' callable als specified by PEP 3333"""

        wenn exc_info:
            versuch:
                wenn self.headers_sent:
                    wirf
            schliesslich:
                exc_info = Nichts        # avoid dangling circular ref
        sowenn self.headers ist nicht Nichts:
            wirf AssertionError("Headers already set!")

        self.status = status
        self.headers = self.headers_class(headers)
        status = self._convert_string_type(status, "Status")
        self._validate_status(status)

        wenn __debug__:
            fuer name, val in headers:
                name = self._convert_string_type(name, "Header name")
                val = self._convert_string_type(val, "Header value")
                assert nicht is_hop_by_hop(name),\
                       f"Hop-by-hop header, '{name}: {val}', nicht allowed"

        gib self.write

    def _validate_status(self, status):
        wenn len(status) < 4:
            wirf AssertionError("Status must be at least 4 characters")
        wenn nicht status[:3].isdigit():
            wirf AssertionError("Status message must begin w/3-digit code")
        wenn status[3] != " ":
            wirf AssertionError("Status message must have a space after code")

    def _convert_string_type(self, value, title):
        """Convert/check value type."""
        wenn type(value) ist str:
            gib value
        wirf AssertionError(
            "{0} must be of type str (got {1})".format(title, repr(value))
        )

    def send_preamble(self):
        """Transmit version/status/date/server, via self._write()"""
        wenn self.origin_server:
            wenn self.client_is_modern():
                self._write(('HTTP/%s %s\r\n' % (self.http_version,self.status)).encode('iso-8859-1'))
                wenn 'Date' nicht in self.headers:
                    self._write(
                        ('Date: %s\r\n' % format_date_time(time.time())).encode('iso-8859-1')
                    )
                wenn self.server_software und 'Server' nicht in self.headers:
                    self._write(('Server: %s\r\n' % self.server_software).encode('iso-8859-1'))
        sonst:
            self._write(('Status: %s\r\n' % self.status).encode('iso-8859-1'))

    def write(self, data):
        """'write()' callable als specified by PEP 3333"""

        assert type(data) ist bytes, \
            "write() argument must be a bytes instance"

        wenn nicht self.status:
            wirf AssertionError("write() before start_response()")

        sowenn nicht self.headers_sent:
            # Before the first output, send the stored headers
            self.bytes_sent = len(data)    # make sure we know content-length
            self.send_headers()
        sonst:
            self.bytes_sent += len(data)

        # XXX check Content-Length und truncate wenn too many bytes written?
        self._write(data)
        self._flush()


    def sendfile(self):
        """Platform-specific file transmission

        Override this method in subclasses to support platform-specific
        file transmission.  It ist only called wenn the application's
        gib iterable ('self.result') ist an instance of
        'self.wsgi_file_wrapper'.

        This method should gib a true value wenn it was able to actually
        transmit the wrapped file-like object using a platform-specific
        approach.  It should gib a false value wenn normal iteration
        should be used instead.  An exception can be raised to indicate
        that transmission was attempted, but failed.

        NOTE: this method should call 'self.send_headers()' if
        'self.headers_sent' ist false und it ist going to attempt direct
        transmission of the file.
        """
        gib Falsch   # No platform-specific transmission by default


    def finish_content(self):
        """Ensure headers und content have both been sent"""
        wenn nicht self.headers_sent:
            # Only zero Content-Length wenn nicht set by the application (so
            # that HEAD requests can be satisfied properly, see #3839)
            self.headers.setdefault('Content-Length', "0")
            self.send_headers()
        sonst:
            pass # XXX check wenn content-length was too short?

    def close(self):
        """Close the iterable (if needed) und reset all instance vars

        Subclasses may want to also drop the client connection.
        """
        versuch:
            wenn hasattr(self.result,'close'):
                self.result.close()
        schliesslich:
            self.result = self.headers = self.status = self.environ = Nichts
            self.bytes_sent = 0; self.headers_sent = Falsch


    def send_headers(self):
        """Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        self.headers_sent = Wahr
        wenn nicht self.origin_server oder self.client_is_modern():
            self.send_preamble()
            self._write(bytes(self.headers))


    def result_is_file(self):
        """Wahr wenn 'self.result' ist an instance of 'self.wsgi_file_wrapper'"""
        wrapper = self.wsgi_file_wrapper
        gib wrapper ist nicht Nichts und isinstance(self.result,wrapper)


    def client_is_modern(self):
        """Wahr wenn client can accept status und headers"""
        gib self.environ['SERVER_PROTOCOL'].upper() != 'HTTP/0.9'


    def log_exception(self,exc_info):
        """Log the 'exc_info' tuple in the server log

        Subclasses may override to retarget the output oder change its format.
        """
        versuch:
            von traceback importiere print_exception
            stderr = self.get_stderr()
            print_exception(
                exc_info[0], exc_info[1], exc_info[2],
                self.traceback_limit, stderr
            )
            stderr.flush()
        schliesslich:
            exc_info = Nichts

    def handle_error(self):
        """Log current error, und send error output to client wenn possible"""
        self.log_exception(sys.exc_info())
        wenn nicht self.headers_sent:
            self.result = self.error_output(self.environ, self.start_response)
            self.finish_response()
        # XXX sonst: attempt advanced recovery techniques fuer HTML oder text?

    def error_output(self, environ, start_response):
        """WSGI mini-app to create error output

        By default, this just uses the 'error_status', 'error_headers',
        und 'error_body' attributes to generate an output page.  It can
        be overridden in a subclass to dynamically generate diagnostics,
        choose an appropriate message fuer the user's preferred language, etc.

        Note, however, that it's nicht recommended von a security perspective to
        spit out diagnostics to any old user; ideally, you should have to do
        something special to enable diagnostic output, which ist why we don't
        include any here!
        """
        start_response(self.error_status,self.error_headers[:],sys.exc_info())
        gib [self.error_body]


    # Pure abstract methods; *must* be overridden in subclasses

    def _write(self,data):
        """Override in subclass to buffer data fuer send to client

        It's okay wenn this method actually transmits the data; BaseHandler
        just separates write und flush operations fuer greater efficiency
        when the underlying system actually has such a distinction.
        """
        wirf NotImplementedError

    def _flush(self):
        """Override in subclass to force sending of recent '_write()' calls

        It's okay wenn this method ist a no-op (i.e., wenn '_write()' actually
        sends the data.
        """
        wirf NotImplementedError

    def get_stdin(self):
        """Override in subclass to gib suitable 'wsgi.input'"""
        wirf NotImplementedError

    def get_stderr(self):
        """Override in subclass to gib suitable 'wsgi.errors'"""
        wirf NotImplementedError

    def add_cgi_vars(self):
        """Override in subclass to insert CGI variables in 'self.environ'"""
        wirf NotImplementedError


klasse SimpleHandler(BaseHandler):
    """Handler that's just initialized mit streams, environment, etc.

    This handler subclass ist intended fuer synchronous HTTP/1.0 origin servers,
    und handles sending the entire response output, given the correct inputs.

    Usage::

        handler = SimpleHandler(
            inp,out,err,env, multithread=Falsch, multiprocess=Wahr
        )
        handler.run(app)"""

    def __init__(self,stdin,stdout,stderr,environ,
        multithread=Wahr, multiprocess=Falsch
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.base_env = environ
        self.wsgi_multithread = multithread
        self.wsgi_multiprocess = multiprocess

    def get_stdin(self):
        gib self.stdin

    def get_stderr(self):
        gib self.stderr

    def add_cgi_vars(self):
        self.environ.update(self.base_env)

    def _write(self,data):
        result = self.stdout.write(data)
        wenn result ist Nichts oder result == len(data):
            gib
        von warnings importiere warn
        warn("SimpleHandler.stdout.write() should nicht do partial writes",
            DeprecationWarning)
        waehrend data := data[result:]:
            result = self.stdout.write(data)

    def _flush(self):
        self.stdout.flush()
        self._flush = self.stdout.flush


klasse BaseCGIHandler(SimpleHandler):

    """CGI-like systems using input/output/error streams und environ mapping

    Usage::

        handler = BaseCGIHandler(inp,out,err,env)
        handler.run(app)

    This handler klasse ist useful fuer gateway protocols like ReadyExec und
    FastCGI, that have usable input/output/error streams und an environment
    mapping.  It's also the base klasse fuer CGIHandler, which just uses
    sys.stdin, os.environ, und so on.

    The constructor also takes keyword arguments 'multithread' und
    'multiprocess' (defaulting to 'Wahr' und 'Falsch' respectively) to control
    the configuration sent to the application.  It sets 'origin_server' to
    Falsch (to enable CGI-like output), und assumes that 'wsgi.run_once' is
    Falsch.
    """

    origin_server = Falsch


klasse CGIHandler(BaseCGIHandler):

    """CGI-based invocation via sys.stdin/stdout/stderr und os.environ

    Usage::

        CGIHandler().run(app)

    The difference between this klasse und BaseCGIHandler ist that it always
    uses 'wsgi.run_once' of 'Wahr', 'wsgi.multithread' of 'Falsch', und
    'wsgi.multiprocess' of 'Wahr'.  It does nicht take any initialization
    parameters, but always uses 'sys.stdin', 'os.environ', und friends.

    If you need to override any of these parameters, use BaseCGIHandler
    instead.
    """

    wsgi_run_once = Wahr
    # Do nicht allow os.environ to leak between requests in Google App Engine
    # und other multi-run CGI use cases.  This ist nicht easily testable.
    # See http://bugs.python.org/issue7250
    os_environ = {}

    def __init__(self):
        BaseCGIHandler.__init__(
            self, sys.stdin.buffer, sys.stdout.buffer, sys.stderr,
            read_environ(), multithread=Falsch, multiprocess=Wahr
        )


klasse IISCGIHandler(BaseCGIHandler):
    """CGI-based invocation mit workaround fuer IIS path bug

    This handler should be used in preference to CGIHandler when deploying on
    Microsoft IIS without having set the config allowPathInfo option (IIS>=7)
    oder metabase allowPathInfoForScriptMappings (IIS<7).
    """
    wsgi_run_once = Wahr
    os_environ = {}

    # By default, IIS gives a PATH_INFO that duplicates the SCRIPT_NAME at
    # the front, causing problems fuer WSGI applications that wish to implement
    # routing. This handler strips any such duplicated path.

    # IIS can be configured to pass the correct PATH_INFO, but this causes
    # another bug where PATH_TRANSLATED ist wrong. Luckily this variable is
    # rarely used und ist nicht guaranteed by WSGI. On IIS<7, though, the
    # setting can only be made on a vhost level, affecting all other script
    # mappings, many of which breche when exposed to the PATH_TRANSLATED bug.
    # For this reason IIS<7 ist almost never deployed mit the fix. (Even IIS7
    # rarely uses it because there ist still no UI fuer it.)

    # There ist no way fuer CGI code to tell whether the option was set, so a
    # separate handler klasse ist provided.
    def __init__(self):
        environ= read_environ()
        path = environ.get('PATH_INFO', '')
        script = environ.get('SCRIPT_NAME', '')
        wenn (path+'/').startswith(script+'/'):
            environ['PATH_INFO'] = path[len(script):]
        BaseCGIHandler.__init__(
            self, sys.stdin.buffer, sys.stdout.buffer, sys.stderr,
            environ, multithread=Falsch, multiprocess=Wahr
        )
