von unittest importiere mock
von test importiere support
von test.support importiere socket_helper
von test.test_httpservers importiere NoLogRequestHandler
von unittest importiere TestCase
von wsgiref.util importiere setup_testing_defaults
von wsgiref.headers importiere Headers
von wsgiref.handlers importiere BaseHandler, BaseCGIHandler, SimpleHandler
von wsgiref importiere util
von wsgiref.validate importiere validator
von wsgiref.simple_server importiere WSGIServer, WSGIRequestHandler
von wsgiref.simple_server importiere make_server
von http.client importiere HTTPConnection
von io importiere StringIO, BytesIO, BufferedReader
von socketserver importiere BaseServer
von platform importiere python_implementation

importiere os
importiere re
importiere signal
importiere sys
importiere threading
importiere unittest


klasse MockServer(WSGIServer):
    """Non-socket HTTP server"""

    def __init__(self, server_address, RequestHandlerClass):
        BaseServer.__init__(self, server_address, RequestHandlerClass)
        self.server_bind()

    def server_bind(self):
        host, port = self.server_address
        self.server_name = host
        self.server_port = port
        self.setup_environ()


klasse MockHandler(WSGIRequestHandler):
    """Non-socket HTTP handler"""
    def setup(self):
        self.connection = self.request
        self.rfile, self.wfile = self.connection

    def finish(self):
        pass


def hello_app(environ,start_response):
    start_response("200 OK", [
        ('Content-Type','text/plain'),
        ('Date','Mon, 05 Jun 2006 18:49:54 GMT')
    ])
    gib [b"Hello, world!"]


def header_app(environ, start_response):
    start_response("200 OK", [
        ('Content-Type', 'text/plain'),
        ('Date', 'Mon, 05 Jun 2006 18:49:54 GMT')
    ])
    gib [';'.join([
        environ['HTTP_X_TEST_HEADER'], environ['QUERY_STRING'],
        environ['PATH_INFO']
    ]).encode('iso-8859-1')]


def run_amock(app=hello_app, data=b"GET / HTTP/1.0\n\n"):
    server = make_server("", 80, app, MockServer, MockHandler)
    inp = BufferedReader(BytesIO(data))
    out = BytesIO()
    olderr = sys.stderr
    err = sys.stderr = StringIO()

    versuch:
        server.finish_request((inp, out), ("127.0.0.1",8888))
    schliesslich:
        sys.stderr = olderr

    gib out.getvalue(), err.getvalue()


def compare_generic_iter(make_it, match):
    """Utility to compare a generic iterator mit an iterable

    This tests the iterator using iter()/next().
    'make_it' must be a function returning a fresh
    iterator to be tested (since this may test the iterator twice)."""

    it = make_it()
    wenn nicht iter(it) ist it:
        wirf AssertionError
    fuer item in match:
        wenn nicht next(it) == item:
            wirf AssertionError
    versuch:
        next(it)
    ausser StopIteration:
        pass
    sonst:
        wirf AssertionError("Too many items von .__next__()", it)


klasse IntegrationTests(TestCase):

    def check_hello(self, out, has_length=Wahr):
        pyver = (python_implementation() + "/" +
                sys.version.split()[0])
        self.assertEqual(out,
            ("HTTP/1.0 200 OK\r\n"
            "Server: WSGIServer/0.2 " + pyver +"\r\n"
            "Content-Type: text/plain\r\n"
            "Date: Mon, 05 Jun 2006 18:49:54 GMT\r\n" +
            (has_length und  "Content-Length: 13\r\n" oder "") +
            "\r\n"
            "Hello, world!").encode("iso-8859-1")
        )

    def test_plain_hello(self):
        out, err = run_amock()
        self.check_hello(out)

    def test_environ(self):
        request = (
            b"GET /p%61th/?query=test HTTP/1.0\n"
            b"X-Test-Header: Python test \n"
            b"X-Test-Header: Python test 2\n"
            b"Content-Length: 0\n\n"
        )
        out, err = run_amock(header_app, request)
        self.assertEqual(
            out.splitlines()[-1],
            b"Python test,Python test 2;query=test;/path/"
        )

    def test_request_length(self):
        out, err = run_amock(data=b"GET " + (b"x" * 65537) + b" HTTP/1.0\n\n")
        self.assertEqual(out.splitlines()[0],
                         b"HTTP/1.0 414 URI Too Long")

    def test_validated_hello(self):
        out, err = run_amock(validator(hello_app))
        # the middleware doesn't support len(), so content-length isn't there
        self.check_hello(out, has_length=Falsch)

    def test_simple_validation_error(self):
        def bad_app(environ,start_response):
            start_response("200 OK", ('Content-Type','text/plain'))
            gib ["Hello, world!"]
        out, err = run_amock(validator(bad_app))
        self.assertEndsWith(out,
            b"A server error occurred.  Please contact the administrator."
        )
        self.assertEqual(
            err.splitlines()[-2],
            "AssertionError: Headers (('Content-Type', 'text/plain')) must"
            " be of type list: <class 'tuple'>"
        )

    def test_status_validation_errors(self):
        def create_bad_app(status):
            def bad_app(environ, start_response):
                start_response(status, [("Content-Type", "text/plain; charset=utf-8")])
                gib [b"Hello, world!"]
            gib bad_app

        tests = [
            ('200', 'AssertionError: Status must be at least 4 characters'),
            ('20X OK', 'AssertionError: Status message must begin w/3-digit code'),
            ('200OK', 'AssertionError: Status message must have a space after code'),
        ]

        fuer status, exc_message in tests:
            mit self.subTest(status=status):
                out, err = run_amock(create_bad_app(status))
                self.assertEndsWith(out,
                    b"A server error occurred.  Please contact the administrator."
                )
                self.assertEqual(err.splitlines()[-2], exc_message)

    def test_wsgi_input(self):
        def bad_app(e,s):
            e["wsgi.input"].read()
            s("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
            gib [b"data"]
        out, err = run_amock(validator(bad_app))
        self.assertEndsWith(out,
            b"A server error occurred.  Please contact the administrator."
        )
        self.assertEqual(
            err.splitlines()[-2], "AssertionError"
        )

    def test_bytes_validation(self):
        def app(e, s):
            s("200 OK", [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Date", "Wed, 24 Dec 2008 13:29:32 GMT"),
                ])
            gib [b"data"]
        out, err = run_amock(validator(app))
        self.assertEndsWith(err, '"GET / HTTP/1.0" 200 4\n')
        ver = sys.version.split()[0].encode('ascii')
        py  = python_implementation().encode('ascii')
        pyver = py + b"/" + ver
        self.assertEqual(
                b"HTTP/1.0 200 OK\r\n"
                b"Server: WSGIServer/0.2 "+ pyver + b"\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n"
                b"Date: Wed, 24 Dec 2008 13:29:32 GMT\r\n"
                b"\r\n"
                b"data",
                out)

    def test_cp1252_url(self):
        def app(e, s):
            s("200 OK", [
                ("Content-Type", "text/plain"),
                ("Date", "Wed, 24 Dec 2008 13:29:32 GMT"),
                ])
            # PEP3333 says environ variables are decoded als latin1.
            # Encode als latin1 to get original bytes
            gib [e["PATH_INFO"].encode("latin1")]

        out, err = run_amock(
            validator(app), data=b"GET /\x80%80 HTTP/1.0")
        self.assertEqual(
            [
                b"HTTP/1.0 200 OK",
                mock.ANY,
                b"Content-Type: text/plain",
                b"Date: Wed, 24 Dec 2008 13:29:32 GMT",
                b"",
                b"/\x80\x80",
            ],
            out.splitlines())

    def test_interrupted_write(self):
        # BaseHandler._write() und _flush() have to write all data, even if
        # it takes multiple send() calls.  Test this by interrupting a send()
        # call mit a Unix signal.
        pthread_kill = support.get_attribute(signal, "pthread_kill")

        def app(environ, start_response):
            start_response("200 OK", [])
            gib [b'\0' * support.SOCK_MAX_SIZE]

        klasse WsgiHandler(NoLogRequestHandler, WSGIRequestHandler):
            pass

        server = make_server(socket_helper.HOST, 0, app, handler_class=WsgiHandler)
        self.addCleanup(server.server_close)
        interrupted = threading.Event()

        def signal_handler(signum, frame):
            interrupted.set()

        original = signal.signal(signal.SIGUSR1, signal_handler)
        self.addCleanup(signal.signal, signal.SIGUSR1, original)
        received = Nichts
        main_thread = threading.get_ident()

        def run_client():
            http = HTTPConnection(*server.server_address)
            http.request("GET", "/")
            mit http.getresponse() als response:
                response.read(100)
                # The main thread should now be blocking in a send() system
                # call.  But in theory, it could get interrupted by other
                # signals, und then retried.  So keep sending the signal in a
                # loop, in case an earlier signal happens to be delivered at
                # an inconvenient moment.
                waehrend Wahr:
                    pthread_kill(main_thread, signal.SIGUSR1)
                    wenn interrupted.wait(timeout=float(1)):
                        breche
                nonlocal received
                received = len(response.read())
            http.close()

        background = threading.Thread(target=run_client)
        background.start()
        server.handle_request()
        background.join()
        self.assertEqual(received, support.SOCK_MAX_SIZE - 100)


klasse UtilityTests(TestCase):

    def checkShift(self,sn_in,pi_in,part,sn_out,pi_out):
        env = {'SCRIPT_NAME':sn_in,'PATH_INFO':pi_in}
        util.setup_testing_defaults(env)
        self.assertEqual(util.shift_path_info(env),part)
        self.assertEqual(env['PATH_INFO'],pi_out)
        self.assertEqual(env['SCRIPT_NAME'],sn_out)
        gib env

    def checkDefault(self, key, value, alt=Nichts):
        # Check defaulting when empty
        env = {}
        util.setup_testing_defaults(env)
        wenn isinstance(value, StringIO):
            self.assertIsInstance(env[key], StringIO)
        sowenn isinstance(value,BytesIO):
            self.assertIsInstance(env[key],BytesIO)
        sonst:
            self.assertEqual(env[key], value)

        # Check existing value
        env = {key:alt}
        util.setup_testing_defaults(env)
        self.assertIs(env[key], alt)

    def checkCrossDefault(self,key,value,**kw):
        util.setup_testing_defaults(kw)
        self.assertEqual(kw[key],value)

    def checkAppURI(self,uri,**kw):
        util.setup_testing_defaults(kw)
        self.assertEqual(util.application_uri(kw),uri)

    def checkReqURI(self,uri,query=1,**kw):
        util.setup_testing_defaults(kw)
        self.assertEqual(util.request_uri(kw,query),uri)

    def checkFW(self,text,size,match):

        def make_it(text=text,size=size):
            gib util.FileWrapper(StringIO(text),size)

        compare_generic_iter(make_it,match)

        it = make_it()
        self.assertFalsch(it.filelike.closed)

        fuer item in it:
            pass

        self.assertFalsch(it.filelike.closed)

        it.close()
        self.assertWahr(it.filelike.closed)

    def testSimpleShifts(self):
        self.checkShift('','/', '', '/', '')
        self.checkShift('','/x', 'x', '/x', '')
        self.checkShift('/','', Nichts, '/', '')
        self.checkShift('/a','/x/y', 'x', '/a/x', '/y')
        self.checkShift('/a','/x/',  'x', '/a/x', '/')

    def testNormalizedShifts(self):
        self.checkShift('/a/b', '/../y', '..', '/a', '/y')
        self.checkShift('', '/../y', '..', '', '/y')
        self.checkShift('/a/b', '//y', 'y', '/a/b/y', '')
        self.checkShift('/a/b', '//y/', 'y', '/a/b/y', '/')
        self.checkShift('/a/b', '/./y', 'y', '/a/b/y', '')
        self.checkShift('/a/b', '/./y/', 'y', '/a/b/y', '/')
        self.checkShift('/a/b', '///./..//y/.//', '..', '/a', '/y/')
        self.checkShift('/a/b', '///', '', '/a/b/', '')
        self.checkShift('/a/b', '/.//', '', '/a/b/', '')
        self.checkShift('/a/b', '/x//', 'x', '/a/b/x', '/')
        self.checkShift('/a/b', '/.', Nichts, '/a/b', '')

    def testDefaults(self):
        fuer key, value in [
            ('SERVER_NAME','127.0.0.1'),
            ('SERVER_PORT', '80'),
            ('SERVER_PROTOCOL','HTTP/1.0'),
            ('HTTP_HOST','127.0.0.1'),
            ('REQUEST_METHOD','GET'),
            ('SCRIPT_NAME',''),
            ('PATH_INFO','/'),
            ('wsgi.version', (1,0)),
            ('wsgi.run_once', 0),
            ('wsgi.multithread', 0),
            ('wsgi.multiprocess', 0),
            ('wsgi.input', BytesIO()),
            ('wsgi.errors', StringIO()),
            ('wsgi.url_scheme','http'),
        ]:
            self.checkDefault(key,value)

    def testCrossDefaults(self):
        self.checkCrossDefault('HTTP_HOST',"foo.bar",SERVER_NAME="foo.bar")
        self.checkCrossDefault('wsgi.url_scheme',"https",HTTPS="on")
        self.checkCrossDefault('wsgi.url_scheme',"https",HTTPS="1")
        self.checkCrossDefault('wsgi.url_scheme',"https",HTTPS="yes")
        self.checkCrossDefault('wsgi.url_scheme',"http",HTTPS="foo")
        self.checkCrossDefault('SERVER_PORT',"80",HTTPS="foo")
        self.checkCrossDefault('SERVER_PORT',"443",HTTPS="on")

    def testGuessScheme(self):
        self.assertEqual(util.guess_scheme({}), "http")
        self.assertEqual(util.guess_scheme({'HTTPS':"foo"}), "http")
        self.assertEqual(util.guess_scheme({'HTTPS':"on"}), "https")
        self.assertEqual(util.guess_scheme({'HTTPS':"yes"}), "https")
        self.assertEqual(util.guess_scheme({'HTTPS':"1"}), "https")

    def testAppURIs(self):
        self.checkAppURI("http://127.0.0.1/")
        self.checkAppURI("http://127.0.0.1/spam", SCRIPT_NAME="/spam")
        self.checkAppURI("http://127.0.0.1/sp%E4m", SCRIPT_NAME="/sp\xe4m")
        self.checkAppURI("http://spam.example.com:2071/",
            HTTP_HOST="spam.example.com:2071", SERVER_PORT="2071")
        self.checkAppURI("http://spam.example.com/",
            SERVER_NAME="spam.example.com")
        self.checkAppURI("http://127.0.0.1/",
            HTTP_HOST="127.0.0.1", SERVER_NAME="spam.example.com")
        self.checkAppURI("https://127.0.0.1/", HTTPS="on")
        self.checkAppURI("http://127.0.0.1:8000/", SERVER_PORT="8000",
            HTTP_HOST=Nichts)

    def testReqURIs(self):
        self.checkReqURI("http://127.0.0.1/")
        self.checkReqURI("http://127.0.0.1/spam", SCRIPT_NAME="/spam")
        self.checkReqURI("http://127.0.0.1/sp%E4m", SCRIPT_NAME="/sp\xe4m")
        self.checkReqURI("http://127.0.0.1/spammity/spam",
            SCRIPT_NAME="/spammity", PATH_INFO="/spam")
        self.checkReqURI("http://127.0.0.1/spammity/sp%E4m",
            SCRIPT_NAME="/spammity", PATH_INFO="/sp\xe4m")
        self.checkReqURI("http://127.0.0.1/spammity/spam;ham",
            SCRIPT_NAME="/spammity", PATH_INFO="/spam;ham")
        self.checkReqURI("http://127.0.0.1/spammity/spam;cookie=1234,5678",
            SCRIPT_NAME="/spammity", PATH_INFO="/spam;cookie=1234,5678")
        self.checkReqURI("http://127.0.0.1/spammity/spam?say=ni",
            SCRIPT_NAME="/spammity", PATH_INFO="/spam",QUERY_STRING="say=ni")
        self.checkReqURI("http://127.0.0.1/spammity/spam?s%E4y=ni",
            SCRIPT_NAME="/spammity", PATH_INFO="/spam",QUERY_STRING="s%E4y=ni")
        self.checkReqURI("http://127.0.0.1/spammity/spam", 0,
            SCRIPT_NAME="/spammity", PATH_INFO="/spam",QUERY_STRING="say=ni")

    def testFileWrapper(self):
        self.checkFW("xyz"*50, 120, ["xyz"*40,"xyz"*10])

    def testHopByHop(self):
        fuer hop in (
            "Connection Keep-Alive Proxy-Authenticate Proxy-Authorization "
            "TE Trailers Transfer-Encoding Upgrade"
        ).split():
            fuer alt in hop, hop.title(), hop.upper(), hop.lower():
                self.assertWahr(util.is_hop_by_hop(alt))

        # Not comprehensive, just a few random header names
        fuer hop in (
            "Accept Cache-Control Date Pragma Trailer Via Warning"
        ).split():
            fuer alt in hop, hop.title(), hop.upper(), hop.lower():
                self.assertFalsch(util.is_hop_by_hop(alt))

klasse HeaderTests(TestCase):

    def testMappingInterface(self):
        test = [('x','y')]
        self.assertEqual(len(Headers()), 0)
        self.assertEqual(len(Headers([])),0)
        self.assertEqual(len(Headers(test[:])),1)
        self.assertEqual(Headers(test[:]).keys(), ['x'])
        self.assertEqual(Headers(test[:]).values(), ['y'])
        self.assertEqual(Headers(test[:]).items(), test)
        self.assertIsNot(Headers(test).items(), test)  # must be copy!

        h = Headers()
        loesche h['foo']   # should nicht wirf an error

        h['Foo'] = 'bar'
        fuer m in h.__contains__, h.get, h.get_all, h.__getitem__:
            self.assertWahr(m('foo'))
            self.assertWahr(m('Foo'))
            self.assertWahr(m('FOO'))
            self.assertFalsch(m('bar'))

        self.assertEqual(h['foo'],'bar')
        h['foo'] = 'baz'
        self.assertEqual(h['FOO'],'baz')
        self.assertEqual(h.get_all('foo'),['baz'])

        self.assertEqual(h.get("foo","whee"), "baz")
        self.assertEqual(h.get("zoo","whee"), "whee")
        self.assertEqual(h.setdefault("foo","whee"), "baz")
        self.assertEqual(h.setdefault("zoo","whee"), "whee")
        self.assertEqual(h["foo"],"baz")
        self.assertEqual(h["zoo"],"whee")

    def testRequireList(self):
        self.assertRaises(TypeError, Headers, "foo")

    def testExtras(self):
        h = Headers()
        self.assertEqual(str(h),'\r\n')

        h.add_header('foo','bar',baz="spam")
        self.assertEqual(h['foo'], 'bar; baz="spam"')
        self.assertEqual(str(h),'foo: bar; baz="spam"\r\n\r\n')

        h.add_header('Foo','bar',cheese=Nichts)
        self.assertEqual(h.get_all('foo'),
            ['bar; baz="spam"', 'bar; cheese'])

        self.assertEqual(str(h),
            'foo: bar; baz="spam"\r\n'
            'Foo: bar; cheese\r\n'
            '\r\n'
        )

klasse ErrorHandler(BaseCGIHandler):
    """Simple handler subclass fuer testing BaseHandler"""

    # BaseHandler records the OS environment at importiere time, but envvars
    # might have been changed later by other tests, which trips up
    # HandlerTests.testEnviron().
    os_environ = dict(os.environ.items())

    def __init__(self,**kw):
        setup_testing_defaults(kw)
        BaseCGIHandler.__init__(
            self, BytesIO(), BytesIO(), StringIO(), kw,
            multithread=Wahr, multiprocess=Wahr
        )

klasse TestHandler(ErrorHandler):
    """Simple handler subclass fuer testing BaseHandler, w/error passthru"""

    def handle_error(self):
        wirf   # fuer testing, we want to see what's happening


klasse HandlerTests(TestCase):
    # testEnviron() can produce long error message
    maxDiff = 80 * 50

    def testEnviron(self):
        os_environ = {
            # very basic environment
            'HOME': '/my/home',
            'PATH': '/my/path',
            'LANG': 'fr_FR.UTF-8',

            # set some WSGI variables
            'SCRIPT_NAME': 'test_script_name',
            'SERVER_NAME': 'test_server_name',
        }

        mit support.swap_attr(TestHandler, 'os_environ', os_environ):
            # override X und HOME variables
            handler = TestHandler(X="Y", HOME="/override/home")
            handler.setup_environ()

        # Check that wsgi_xxx attributes are copied to wsgi.xxx variables
        # of handler.environ
        fuer attr in ('version', 'multithread', 'multiprocess', 'run_once',
                     'file_wrapper'):
            self.assertEqual(getattr(handler, 'wsgi_' + attr),
                             handler.environ['wsgi.' + attr])

        # Test handler.environ als a dict
        expected = {}
        setup_testing_defaults(expected)
        # Handler inherits os_environ variables which are nicht overridden
        # by SimpleHandler.add_cgi_vars() (SimpleHandler.base_env)
        fuer key, value in os_environ.items():
            wenn key nicht in expected:
                expected[key] = value
        expected.update({
            # X doesn't exist in os_environ
            "X": "Y",
            # HOME ist overridden by TestHandler
            'HOME': "/override/home",

            # overridden by setup_testing_defaults()
            "SCRIPT_NAME": "",
            "SERVER_NAME": "127.0.0.1",

            # set by BaseHandler.setup_environ()
            'wsgi.input': handler.get_stdin(),
            'wsgi.errors': handler.get_stderr(),
            'wsgi.version': (1, 0),
            'wsgi.run_once': Falsch,
            'wsgi.url_scheme': 'http',
            'wsgi.multithread': Wahr,
            'wsgi.multiprocess': Wahr,
            'wsgi.file_wrapper': util.FileWrapper,
        })
        self.assertDictEqual(handler.environ, expected)

    def testCGIEnviron(self):
        h = BaseCGIHandler(Nichts,Nichts,Nichts,{})
        h.setup_environ()
        fuer key in 'wsgi.url_scheme', 'wsgi.input', 'wsgi.errors':
            self.assertIn(key, h.environ)

    def testScheme(self):
        h=TestHandler(HTTPS="on"); h.setup_environ()
        self.assertEqual(h.environ['wsgi.url_scheme'],'https')
        h=TestHandler(); h.setup_environ()
        self.assertEqual(h.environ['wsgi.url_scheme'],'http')

    def testAbstractMethods(self):
        h = BaseHandler()
        fuer name in [
            '_flush','get_stdin','get_stderr','add_cgi_vars'
        ]:
            self.assertRaises(NotImplementedError, getattr(h,name))
        self.assertRaises(NotImplementedError, h._write, "test")

    def testContentLength(self):
        # Demo one reason iteration ist better than write()...  ;)

        def trivial_app1(e,s):
            s('200 OK',[])
            gib [e['wsgi.url_scheme'].encode('iso-8859-1')]

        def trivial_app2(e,s):
            s('200 OK',[])(e['wsgi.url_scheme'].encode('iso-8859-1'))
            gib []

        def trivial_app3(e,s):
            s('200 OK',[])
            gib ['\u0442\u0435\u0441\u0442'.encode("utf-8")]

        def trivial_app4(e,s):
            # Simulate a response to a HEAD request
            s('200 OK',[('Content-Length', '12345')])
            gib []

        h = TestHandler()
        h.run(trivial_app1)
        self.assertEqual(h.stdout.getvalue(),
            ("Status: 200 OK\r\n"
            "Content-Length: 4\r\n"
            "\r\n"
            "http").encode("iso-8859-1"))

        h = TestHandler()
        h.run(trivial_app2)
        self.assertEqual(h.stdout.getvalue(),
            ("Status: 200 OK\r\n"
            "\r\n"
            "http").encode("iso-8859-1"))

        h = TestHandler()
        h.run(trivial_app3)
        self.assertEqual(h.stdout.getvalue(),
            b'Status: 200 OK\r\n'
            b'Content-Length: 8\r\n'
            b'\r\n'
            b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')

        h = TestHandler()
        h.run(trivial_app4)
        self.assertEqual(h.stdout.getvalue(),
            b'Status: 200 OK\r\n'
            b'Content-Length: 12345\r\n'
            b'\r\n')

    def testBasicErrorOutput(self):

        def non_error_app(e,s):
            s('200 OK',[])
            gib []

        def error_app(e,s):
            wirf AssertionError("This should be caught by handler")

        h = ErrorHandler()
        h.run(non_error_app)
        self.assertEqual(h.stdout.getvalue(),
            ("Status: 200 OK\r\n"
            "Content-Length: 0\r\n"
            "\r\n").encode("iso-8859-1"))
        self.assertEqual(h.stderr.getvalue(),"")

        h = ErrorHandler()
        h.run(error_app)
        self.assertEqual(h.stdout.getvalue(),
            ("Status: %s\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: %d\r\n"
            "\r\n" % (h.error_status,len(h.error_body))).encode('iso-8859-1')
            + h.error_body)

        self.assertIn("AssertionError", h.stderr.getvalue())

    def testErrorAfterOutput(self):
        MSG = b"Some output has been sent"
        def error_app(e,s):
            s("200 OK",[])(MSG)
            wirf AssertionError("This should be caught by handler")

        h = ErrorHandler()
        h.run(error_app)
        self.assertEqual(h.stdout.getvalue(),
            ("Status: 200 OK\r\n"
            "\r\n".encode("iso-8859-1")+MSG))
        self.assertIn("AssertionError", h.stderr.getvalue())

    def testHeaderFormats(self):

        def non_error_app(e,s):
            s('200 OK',[])
            gib []

        stdpat = (
            r"HTTP/%s 200 OK\r\n"
            r"Date: \w{3}, [ 0123]\d \w{3} \d{4} \d\d:\d\d:\d\d GMT\r\n"
            r"%s" r"Content-Length: 0\r\n" r"\r\n"
        )
        shortpat = (
            "Status: 200 OK\r\n" "Content-Length: 0\r\n" "\r\n"
        ).encode("iso-8859-1")

        fuer ssw in "FooBar/1.0", Nichts:
            sw = ssw und "Server: %s\r\n" % ssw oder ""

            fuer version in "1.0", "1.1":
                fuer proto in "HTTP/0.9", "HTTP/1.0", "HTTP/1.1":

                    h = TestHandler(SERVER_PROTOCOL=proto)
                    h.origin_server = Falsch
                    h.http_version = version
                    h.server_software = ssw
                    h.run(non_error_app)
                    self.assertEqual(shortpat,h.stdout.getvalue())

                    h = TestHandler(SERVER_PROTOCOL=proto)
                    h.origin_server = Wahr
                    h.http_version = version
                    h.server_software = ssw
                    h.run(non_error_app)
                    wenn proto=="HTTP/0.9":
                        self.assertEqual(h.stdout.getvalue(),b"")
                    sonst:
                        self.assertWahr(
                            re.match((stdpat%(version,sw)).encode("iso-8859-1"),
                                h.stdout.getvalue()),
                            ((stdpat%(version,sw)).encode("iso-8859-1"),
                                h.stdout.getvalue())
                        )

    def testBytesData(self):
        def app(e, s):
            s("200 OK", [
                ("Content-Type", "text/plain; charset=utf-8"),
                ])
            gib [b"data"]

        h = TestHandler()
        h.run(app)
        self.assertEqual(b"Status: 200 OK\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"Content-Length: 4\r\n"
            b"\r\n"
            b"data",
            h.stdout.getvalue())

    def testCloseOnError(self):
        side_effects = {'close_called': Falsch}
        MSG = b"Some output has been sent"
        def error_app(e,s):
            s("200 OK",[])(MSG)
            klasse CrashyIterable(object):
                def __iter__(self):
                    waehrend Wahr:
                        liefere b'blah'
                        wirf AssertionError("This should be caught by handler")
                def close(self):
                    side_effects['close_called'] = Wahr
            gib CrashyIterable()

        h = ErrorHandler()
        h.run(error_app)
        self.assertEqual(side_effects['close_called'], Wahr)

    def testPartialWrite(self):
        written = bytearray()

        klasse PartialWriter:
            def write(self, b):
                partial = b[:7]
                written.extend(partial)
                gib len(partial)

            def flush(self):
                pass

        environ = {"SERVER_PROTOCOL": "HTTP/1.0"}
        h = SimpleHandler(BytesIO(), PartialWriter(), sys.stderr, environ)
        msg = "should nicht do partial writes"
        mit self.assertWarnsRegex(DeprecationWarning, msg):
            h.run(hello_app)
        self.assertEqual(b"HTTP/1.0 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Date: Mon, 05 Jun 2006 18:49:54 GMT\r\n"
            b"Content-Length: 13\r\n"
            b"\r\n"
            b"Hello, world!",
            written)

    def testClientConnectionTerminations(self):
        environ = {"SERVER_PROTOCOL": "HTTP/1.0"}
        fuer exception in (
            ConnectionAbortedError,
            BrokenPipeError,
            ConnectionResetError,
        ):
            mit self.subTest(exception=exception):
                klasse AbortingWriter:
                    def write(self, b):
                        wirf exception

                stderr = StringIO()
                h = SimpleHandler(BytesIO(), AbortingWriter(), stderr, environ)
                h.run(hello_app)

                self.assertFalsch(stderr.getvalue())

    def testDontResetInternalStateOnException(self):
        klasse CustomException(ValueError):
            pass

        # We are raising CustomException here to trigger an exception
        # during the execution of SimpleHandler.finish_response(), so
        # we can easily test that the internal state of the handler is
        # preserved in case of an exception.
        klasse AbortingWriter:
            def write(self, b):
                wirf CustomException

        stderr = StringIO()
        environ = {"SERVER_PROTOCOL": "HTTP/1.0"}
        h = SimpleHandler(BytesIO(), AbortingWriter(), stderr, environ)
        h.run(hello_app)

        self.assertIn("CustomException", stderr.getvalue())

        # Test that the internal state of the handler ist preserved.
        self.assertIsNotNichts(h.result)
        self.assertIsNotNichts(h.headers)
        self.assertIsNotNichts(h.status)
        self.assertIsNotNichts(h.environ)


wenn __name__ == "__main__":
    unittest.main()
