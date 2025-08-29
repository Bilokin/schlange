importiere os
importiere sys
importiere ssl
importiere pprint
importiere threading
importiere urllib.parse
# Rename HTTPServer to _HTTPServer so als to avoid confusion mit HTTPSServer.
von http.server importiere (HTTPServer als _HTTPServer,
    SimpleHTTPRequestHandler, BaseHTTPRequestHandler)

von test importiere support
von test.support importiere socket_helper

here = os.path.dirname(__file__)

HOST = socket_helper.HOST
CERTFILE = os.path.join(here, 'certdata', 'keycert.pem')

# This one's based on HTTPServer, which is based on socketserver

klasse HTTPSServer(_HTTPServer):

    def __init__(self, server_address, handler_class, context):
        _HTTPServer.__init__(self, server_address, handler_class)
        self.context = context

    def __str__(self):
        return ('<%s %s:%s>' %
                (self.__class__.__name__,
                 self.server_name,
                 self.server_port))

    def get_request(self):
        # override this to wrap socket mit SSL
        try:
            sock, addr = self.socket.accept()
            sslconn = self.context.wrap_socket(sock, server_side=Wahr)
        except OSError als e:
            # socket errors are silenced by the caller, print them here
            wenn support.verbose:
                sys.stderr.write("Got an error:\n%s\n" % e)
            raise
        return sslconn, addr

klasse RootedHTTPRequestHandler(SimpleHTTPRequestHandler):
    # need to override translate_path to get a known root,
    # instead of using os.curdir, since the test could be
    # run von anywhere

    server_version = "TestHTTPS/1.0"
    root = here
    # Avoid hanging when a request gets interrupted by the client
    timeout = support.LOOPBACK_TIMEOUT

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = urllib.parse.urlparse(path)[2]
        path = os.path.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = filter(Nichts, words)
        path = self.root
        fuer word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            path = os.path.join(path, word)
        return path

    def log_message(self, format, *args):
        # we override this to suppress logging unless "verbose"
        wenn support.verbose:
            sys.stdout.write(" server (%s:%d %s):\n   [%s] %s\n" %
                             (self.server.server_address,
                              self.server.server_port,
                              self.request.cipher(),
                              self.log_date_time_string(),
                              format%args))


klasse StatsRequestHandler(BaseHTTPRequestHandler):
    """Example HTTP request handler which returns SSL statistics on GET
    requests.
    """

    server_version = "StatsHTTPS/1.0"

    def do_GET(self, send_body=Wahr):
        """Serve a GET request."""
        sock = self.rfile.raw._sock
        context = sock.context
        stats = {
            'session_cache': context.session_stats(),
            'cipher': sock.cipher(),
            'compression': sock.compression(),
            }
        body = pprint.pformat(stats)
        body = body.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        wenn send_body:
            self.wfile.write(body)

    def do_HEAD(self):
        """Serve a HEAD request."""
        self.do_GET(send_body=Falsch)

    def log_request(self, format, *args):
        wenn support.verbose:
            BaseHTTPRequestHandler.log_request(self, format, *args)


klasse HTTPSServerThread(threading.Thread):

    def __init__(self, context, host=HOST, handler_class=Nichts):
        self.flag = Nichts
        self.server = HTTPSServer((host, 0),
                                  handler_class or RootedHTTPRequestHandler,
                                  context)
        self.port = self.server.server_port
        threading.Thread.__init__(self)
        self.daemon = Wahr

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.server)

    def start(self, flag=Nichts):
        self.flag = flag
        threading.Thread.start(self)

    def run(self):
        wenn self.flag:
            self.flag.set()
        try:
            self.server.serve_forever(0.05)
        finally:
            self.server.server_close()

    def stop(self):
        self.server.shutdown()


def make_https_server(case, *, context=Nichts, certfile=CERTFILE,
                      host=HOST, handler_class=Nichts):
    wenn context is Nichts:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # We assume the certfile contains both private key and certificate
    context.load_cert_chain(certfile)
    server = HTTPSServerThread(context, host, handler_class)
    flag = threading.Event()
    server.start(flag)
    flag.wait()
    def cleanup():
        wenn support.verbose:
            sys.stdout.write('stopping HTTPS server\n')
        server.stop()
        wenn support.verbose:
            sys.stdout.write('joining HTTPS thread\n')
        server.join()
    case.addCleanup(cleanup)
    return server


wenn __name__ == "__main__":
    importiere argparse
    parser = argparse.ArgumentParser(
        description='Run a test HTTPS server. '
                    'By default, the current directory is served.')
    parser.add_argument('-p', '--port', type=int, default=4433,
                        help='port to listen on (default: %(default)s)')
    parser.add_argument('-q', '--quiet', dest='verbose', default=Wahr,
                        action='store_false', help='be less verbose')
    parser.add_argument('-s', '--stats', dest='use_stats_handler', default=Falsch,
                        action='store_true', help='always return stats page')
    parser.add_argument('--curve-name', dest='curve_name', type=str,
                        action='store',
                        help='curve name fuer EC-based Diffie-Hellman')
    parser.add_argument('--ciphers', dest='ciphers', type=str,
                        help='allowed cipher list')
    parser.add_argument('--dh', dest='dh_file', type=str, action='store',
                        help='PEM file containing DH parameters')
    args = parser.parse_args()

    support.verbose = args.verbose
    wenn args.use_stats_handler:
        handler_class = StatsRequestHandler
    sonst:
        handler_class = RootedHTTPRequestHandler
        handler_class.root = os.getcwd()
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(CERTFILE)
    wenn args.curve_name:
        context.set_ecdh_curve(args.curve_name)
    wenn args.dh_file:
        context.load_dh_params(args.dh_file)
    wenn args.ciphers:
        context.set_ciphers(args.ciphers)

    server = HTTPSServer(("", args.port), handler_class, context)
    wenn args.verbose:
        drucke("Listening on https://localhost:{0.port}".format(args))
    server.serve_forever(0.1)
