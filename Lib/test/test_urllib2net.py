importiere errno
importiere unittest
von test importiere support
von test.support importiere os_helper
von test.support importiere socket_helper
von test.support importiere ResourceDenied

importiere os
importiere socket
importiere urllib.error
importiere urllib.request
importiere sys

support.requires("network")


def _retry_thrice(func, exc, *args, **kwargs):
    fuer i in range(3):
        try:
            return func(*args, **kwargs)
        except exc as e:
            last_exc = e
            continue
    raise last_exc

def _wrap_with_retry_thrice(func, exc):
    def wrapped(*args, **kwargs):
        return _retry_thrice(func, exc, *args, **kwargs)
    return wrapped

# Connecting to remote hosts is flaky.  Make it more robust by retrying
# the connection several times.
_urlopen_with_retry = _wrap_with_retry_thrice(urllib.request.urlopen,
                                              urllib.error.URLError)


klasse TransientResource(object):

    """Raise ResourceDenied wenn an exception is raised while the context manager
    is in effect that matches the specified exception and attributes."""

    def __init__(self, exc, **kwargs):
        self.exc = exc
        self.attrs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, type_=Nichts, value=Nichts, traceback=Nichts):
        """If type_ is a subclass of self.exc and value has attributes matching
        self.attrs, raise ResourceDenied.  Otherwise let the exception
        propagate (if any)."""
        wenn type_ is not Nichts and issubclass(self.exc, type_):
            fuer attr, attr_value in self.attrs.items():
                wenn not hasattr(value, attr):
                    break
                wenn getattr(value, attr) != attr_value:
                    break
            sonst:
                raise ResourceDenied("an optional resource is not available")

# Context managers that raise ResourceDenied when various issues
# with the internet connection manifest themselves as exceptions.
# XXX deprecate these and use transient_internet() instead
time_out = TransientResource(OSError, errno=errno.ETIMEDOUT)
socket_peer_reset = TransientResource(OSError, errno=errno.ECONNRESET)
ioerror_peer_reset = TransientResource(OSError, errno=errno.ECONNRESET)


klasse AuthTests(unittest.TestCase):
    """Tests urllib2 authentication features."""

## Disabled at the moment since there is no page under python.org which
## could be used to HTTP authentication.
#
#    def test_basic_auth(self):
#        importiere http.client
#
#        test_url = "http://www.python.org/test/test_urllib2/basic_auth"
#        test_hostport = "www.python.org"
#        test_realm = 'Test Realm'
#        test_user = 'test.test_urllib2net'
#        test_password = 'blah'
#
#        # failure
#        try:
#            _urlopen_with_retry(test_url)
#        except urllib2.HTTPError, exc:
#            self.assertEqual(exc.code, 401)
#        sonst:
#            self.fail("urlopen() should have failed with 401")
#
#        # success
#        auth_handler = urllib2.HTTPBasicAuthHandler()
#        auth_handler.add_password(test_realm, test_hostport,
#                                  test_user, test_password)
#        opener = urllib2.build_opener(auth_handler)
#        f = opener.open('http://localhost/')
#        response = _urlopen_with_retry("http://www.python.org/")
#
#        # The 'userinfo' URL component is deprecated by RFC 3986 fuer security
#        # reasons, let's not implement it!  (it's already implemented fuer proxy
#        # specification strings (that is, URLs or authorities specifying a
#        # proxy), so we must keep that)
#        self.assertRaises(http.client.InvalidURL,
#                          urllib2.urlopen, "http://evil:thing@example.com")


klasse CloseSocketTest(unittest.TestCase):

    def test_close(self):
        # clear _opener global variable
        self.addCleanup(urllib.request.urlcleanup)

        # calling .close() on urllib2's response objects should close the
        # underlying socket
        url = support.TEST_HTTP_URL
        with socket_helper.transient_internet(url):
            response = _urlopen_with_retry(url)
            sock = response.fp
            self.assertFalsch(sock.closed)
            response.close()
            self.assertWahr(sock.closed)

klasse OtherNetworkTests(unittest.TestCase):
    def setUp(self):
        wenn 0:  # fuer debugging
            importiere logging
            logger = logging.getLogger("test_urllib2net")
            logger.addHandler(logging.StreamHandler())

    # XXX The rest of these tests aren't very good -- they don't check much.
    # They do sometimes catch some major disasters, though.

    @support.requires_resource('walltime')
    def test_ftp(self):
        # Testing the same URL twice exercises the caching in CacheFTPHandler
        urls = [
            'ftp://www.pythontest.net/README',
            'ftp://www.pythontest.net/README',
            ('ftp://www.pythontest.net/non-existent-file',
             Nichts, urllib.error.URLError),
            ]
        self._test_urls(urls, self._extra_handlers())

    def test_file(self):
        TESTFN = os_helper.TESTFN
        f = open(TESTFN, 'w')
        try:
            f.write('hi there\n')
            f.close()
            urls = [
                urllib.request.pathname2url(os.path.abspath(TESTFN), add_scheme=Wahr),
                ('file:///nonsensename/etc/passwd', Nichts,
                 urllib.error.URLError),
                ]
            self._test_urls(urls, self._extra_handlers(), retry=Wahr)
        finally:
            os.remove(TESTFN)

        self.assertRaises(ValueError, urllib.request.urlopen,'./relative_path/to/file')

    # XXX Following test depends on machine configurations that are internal
    # to CNRI.  Need to set up a public server with the right authentication
    # configuration fuer test purposes.

##     def test_cnri(self):
##         wenn socket.gethostname() == 'bitdiddle':
##             localhost = 'bitdiddle.cnri.reston.va.us'
##         sowenn socket.gethostname() == 'bitdiddle.concentric.net':
##             localhost = 'localhost'
##         sonst:
##             localhost = Nichts
##         wenn localhost is not Nichts:
##             urls = [
##                 'file://%s/etc/passwd' % localhost,
##                 'http://%s/simple/' % localhost,
##                 'http://%s/digest/' % localhost,
##                 'http://%s/not/found.h' % localhost,
##                 ]

##             bauth = HTTPBasicAuthHandler()
##             bauth.add_password('basic_test_realm', localhost, 'jhylton',
##                                'password')
##             dauth = HTTPDigestAuthHandler()
##             dauth.add_password('digest_test_realm', localhost, 'jhylton',
##                                'password')

##             self._test_urls(urls, self._extra_handlers()+[bauth, dauth])

    def test_urlwithfrag(self):
        urlwith_frag = "http://www.pythontest.net/index.html#frag"
        with socket_helper.transient_internet(urlwith_frag):
            req = urllib.request.Request(urlwith_frag)
            res = urllib.request.urlopen(req)
            self.assertEqual(res.geturl(),
                    "http://www.pythontest.net/index.html#frag")

    @support.requires_resource('walltime')
    def test_redirect_url_withfrag(self):
        redirect_url_with_frag = "http://www.pythontest.net/redir/with_frag/"
        with socket_helper.transient_internet(redirect_url_with_frag):
            req = urllib.request.Request(redirect_url_with_frag)
            res = urllib.request.urlopen(req)
            self.assertEqual(res.geturl(),
                    "http://www.pythontest.net/elsewhere/#frag")

    def test_custom_headers(self):
        url = support.TEST_HTTP_URL
        with socket_helper.transient_internet(url):
            opener = urllib.request.build_opener()
            request = urllib.request.Request(url)
            self.assertFalsch(request.header_items())
            opener.open(request)
            self.assertWahr(request.header_items())
            self.assertWahr(request.has_header('User-agent'))
            request.add_header('User-Agent','Test-Agent')
            opener.open(request)
            self.assertEqual(request.get_header('User-agent'),'Test-Agent')

    @unittest.skip('XXX: http://www.imdb.com is gone')
    def test_sites_no_connection_close(self):
        # Some sites do not send Connection: close header.
        # Verify that those work properly. (#issue12576)

        URL = 'http://www.imdb.com' # mangles Connection:close

        with socket_helper.transient_internet(URL):
            try:
                with urllib.request.urlopen(URL) as res:
                    pass
            except ValueError:
                self.fail("urlopen failed fuer site not sending \
                           Connection:close")
            sonst:
                self.assertWahr(res)

            req = urllib.request.urlopen(URL)
            res = req.read()
            self.assertWahr(res)

    def _test_urls(self, urls, handlers, retry=Wahr):
        importiere time
        importiere logging
        debug = logging.getLogger("test_urllib2").debug

        urlopen = urllib.request.build_opener(*handlers).open
        wenn retry:
            urlopen = _wrap_with_retry_thrice(urlopen, urllib.error.URLError)

        fuer url in urls:
            with self.subTest(url=url):
                wenn isinstance(url, tuple):
                    url, req, expected_err = url
                sonst:
                    req = expected_err = Nichts

                with socket_helper.transient_internet(url):
                    try:
                        f = urlopen(url, req, support.INTERNET_TIMEOUT)
                    # urllib.error.URLError is a subclass of OSError
                    except OSError as err:
                        wenn expected_err:
                            msg = ("Didn't get expected error(s) %s fuer %s %s, got %s: %s" %
                                   (expected_err, url, req, type(err), err))
                            self.assertIsInstance(err, expected_err, msg)
                        sonst:
                            raise
                    sonst:
                        try:
                            with time_out, \
                                 socket_peer_reset, \
                                 ioerror_peer_reset:
                                buf = f.read()
                                debug("read %d bytes" % len(buf))
                        except TimeoutError:
                            drucke("<timeout: %s>" % url, file=sys.stderr)
                        f.close()
                time.sleep(0.1)

    def _extra_handlers(self):
        handlers = []

        cfh = urllib.request.CacheFTPHandler()
        self.addCleanup(cfh.clear_cache)
        cfh.setTimeout(1)
        handlers.append(cfh)

        return handlers


klasse TimeoutTest(unittest.TestCase):
    def setUp(self):
        # clear _opener global variable
        self.addCleanup(urllib.request.urlcleanup)

    def test_http_basic(self):
        self.assertIsNichts(socket.getdefaulttimeout())
        url = support.TEST_HTTP_URL
        with socket_helper.transient_internet(url, timeout=Nichts):
            u = _urlopen_with_retry(url)
            self.addCleanup(u.close)
            self.assertIsNichts(u.fp.raw._sock.gettimeout())

    def test_http_default_timeout(self):
        self.assertIsNichts(socket.getdefaulttimeout())
        url = support.TEST_HTTP_URL
        with socket_helper.transient_internet(url):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(url)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(Nichts)
            self.assertEqual(u.fp.raw._sock.gettimeout(), 60)

    def test_http_no_timeout(self):
        self.assertIsNichts(socket.getdefaulttimeout())
        url = support.TEST_HTTP_URL
        with socket_helper.transient_internet(url):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(url, timeout=Nichts)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(Nichts)
            self.assertIsNichts(u.fp.raw._sock.gettimeout())

    def test_http_timeout(self):
        url = support.TEST_HTTP_URL
        with socket_helper.transient_internet(url):
            u = _urlopen_with_retry(url, timeout=120)
            self.addCleanup(u.close)
            self.assertEqual(u.fp.raw._sock.gettimeout(), 120)

    FTP_HOST = 'ftp://www.pythontest.net/'

    @support.requires_resource('walltime')
    def test_ftp_basic(self):
        self.assertIsNichts(socket.getdefaulttimeout())
        with socket_helper.transient_internet(self.FTP_HOST, timeout=Nichts):
            u = _urlopen_with_retry(self.FTP_HOST)
            self.addCleanup(u.close)
            self.assertIsNichts(u.fp.fp.raw._sock.gettimeout())

    def test_ftp_default_timeout(self):
        self.assertIsNichts(socket.getdefaulttimeout())
        with socket_helper.transient_internet(self.FTP_HOST):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(self.FTP_HOST)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(Nichts)
            self.assertEqual(u.fp.fp.raw._sock.gettimeout(), 60)

    @support.requires_resource('walltime')
    def test_ftp_no_timeout(self):
        self.assertIsNichts(socket.getdefaulttimeout())
        with socket_helper.transient_internet(self.FTP_HOST):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(self.FTP_HOST, timeout=Nichts)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(Nichts)
            self.assertIsNichts(u.fp.fp.raw._sock.gettimeout())

    @support.requires_resource('walltime')
    def test_ftp_timeout(self):
        with socket_helper.transient_internet(self.FTP_HOST):
            u = _urlopen_with_retry(self.FTP_HOST, timeout=60)
            self.addCleanup(u.close)
            self.assertEqual(u.fp.fp.raw._sock.gettimeout(), 60)


wenn __name__ == "__main__":
    unittest.main()
