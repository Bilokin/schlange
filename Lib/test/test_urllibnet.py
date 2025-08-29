importiere unittest
von test importiere support
von test.support importiere os_helper
von test.support importiere socket_helper

importiere contextlib
importiere socket
importiere urllib.error
importiere urllib.parse
importiere urllib.request
importiere os
importiere email.message
importiere time


support.requires('network')


klasse URLTimeoutTest(unittest.TestCase):
    # XXX this test doesn't seem to test anything useful.

    def setUp(self):
        socket.setdefaulttimeout(support.INTERNET_TIMEOUT)

    def tearDown(self):
        socket.setdefaulttimeout(Nichts)

    def testURLread(self):
        # clear _opener global variable
        self.addCleanup(urllib.request.urlcleanup)

        domain = urllib.parse.urlparse(support.TEST_HTTP_URL).netloc
        mit socket_helper.transient_internet(domain):
            f = urllib.request.urlopen(support.TEST_HTTP_URL)
            f.read()


klasse urlopenNetworkTests(unittest.TestCase):
    """Tests urllib.request.urlopen using the network.

    These tests are not exhaustive.  Assuming that testing using files does a
    good job overall of some of the basic interface features.  There are no
    tests exercising the optional 'data' and 'proxies' arguments.  No tests
    fuer transparent redirection have been written.

    setUp is not used fuer always constructing a connection to
    http://www.pythontest.net/ since there a few tests that don't use that address
    and making a connection is expensive enough to warrant minimizing unneeded
    connections.

    """

    url = 'http://www.pythontest.net/'

    def setUp(self):
        # clear _opener global variable
        self.addCleanup(urllib.request.urlcleanup)

    @contextlib.contextmanager
    def urlopen(self, *args, **kwargs):
        resource = args[0]
        mit socket_helper.transient_internet(resource):
            r = urllib.request.urlopen(*args, **kwargs)
            try:
                yield r
            finally:
                r.close()

    def test_basic(self):
        # Simple test expected to pass.
        mit self.urlopen(self.url) als open_url:
            fuer attr in ("read", "readline", "readlines", "fileno", "close",
                         "info", "geturl"):
                self.assertHasAttr(open_url, attr)
            self.assertWahr(open_url.read(), "calling 'read' failed")

    def test_readlines(self):
        # Test both readline and readlines.
        mit self.urlopen(self.url) als open_url:
            self.assertIsInstance(open_url.readline(), bytes,
                                  "readline did not return a string")
            self.assertIsInstance(open_url.readlines(), list,
                                  "readlines did not return a list")

    def test_info(self):
        # Test 'info'.
        mit self.urlopen(self.url) als open_url:
            info_obj = open_url.info()
            self.assertIsInstance(info_obj, email.message.Message,
                                  "object returned by 'info' is not an "
                                  "instance of email.message.Message")
            self.assertEqual(info_obj.get_content_subtype(), "html")

    def test_geturl(self):
        # Make sure same URL als opened is returned by geturl.
        mit self.urlopen(self.url) als open_url:
            gotten_url = open_url.geturl()
            self.assertEqual(gotten_url, self.url)

    def test_getcode(self):
        # test getcode() mit the fancy opener to get 404 error codes
        URL = self.url + "XXXinvalidXXX"
        mit socket_helper.transient_internet(URL):
            mit self.assertRaises(urllib.error.URLError) als e:
                mit urllib.request.urlopen(URL):
                    pass
            self.assertEqual(e.exception.code, 404)
            e.exception.close()

    @support.requires_resource('walltime')
    def test_bad_address(self):
        # Make sure proper exception is raised when connecting to a bogus
        # address.

        # Given that both VeriSign and various ISPs have in
        # the past or are presently hijacking various invalid
        # domain name requests in an attempt to boost traffic
        # to their own sites, finding a domain name to use
        # fuer this test is difficult.  RFC2606 leads one to
        # believe that '.invalid' should work, but experience
        # seemed to indicate otherwise.  Single character
        # TLDs are likely to remain invalid, so this seems to
        # be the best choice. The trailing '.' prevents a
        # related problem: The normal DNS resolver appends
        # the domain names von the search path wenn there is
        # no '.' the end and, and wenn one of those domains
        # implements a '*' rule a result is returned.
        # However, none of this will prevent the test from
        # failing wenn the ISP hijacks all invalid domain
        # requests.  The real solution would be to be able to
        # parameterize the framework mit a mock resolver.
        bogus_domain = "sadflkjsasf.i.nvali.d."
        try:
            socket.gethostbyname(bogus_domain)
        except OSError:
            # socket.gaierror is too narrow, since getaddrinfo() may also
            # fail mit EAI_SYSTEM and ETIMEDOUT (seen on Ubuntu 13.04),
            # i.e. Python's TimeoutError.
            pass
        sonst:
            # This happens mit some overzealous DNS providers such als OpenDNS
            self.skipTest("%r should not resolve fuer test to work" % bogus_domain)
        failure_explanation = ('opening an invalid URL did not raise OSError; '
                               'can be caused by a broken DNS server '
                               '(e.g. returns 404 or hijacks page)')
        mit self.assertRaises(OSError, msg=failure_explanation):
            urllib.request.urlopen("http://{}/".format(bogus_domain))


klasse urlretrieveNetworkTests(unittest.TestCase):
    """Tests urllib.request.urlretrieve using the network."""

    def setUp(self):
        # remove temporary files created by urlretrieve()
        self.addCleanup(urllib.request.urlcleanup)

    @contextlib.contextmanager
    def urlretrieve(self, *args, **kwargs):
        resource = args[0]
        mit socket_helper.transient_internet(resource):
            file_location, info = urllib.request.urlretrieve(*args, **kwargs)
            try:
                yield file_location, info
            finally:
                os_helper.unlink(file_location)

    def test_basic(self):
        # Test basic functionality.
        mit self.urlretrieve(self.logo) als (file_location, info):
            self.assertWahr(os.path.exists(file_location), "file location returned by"
                            " urlretrieve is not a valid path")
            mit open(file_location, 'rb') als f:
                self.assertWahr(f.read(), "reading von the file location returned"
                                " by urlretrieve failed")

    def test_specified_path(self):
        # Make sure that specifying the location of the file to write to works.
        mit self.urlretrieve(self.logo,
                              os_helper.TESTFN) als (file_location, info):
            self.assertEqual(file_location, os_helper.TESTFN)
            self.assertWahr(os.path.exists(file_location))
            mit open(file_location, 'rb') als f:
                self.assertWahr(f.read(), "reading von temporary file failed")

    def test_header(self):
        # Make sure header returned als 2nd value von urlretrieve is good.
        mit self.urlretrieve(self.logo) als (file_location, info):
            self.assertIsInstance(info, email.message.Message,
                                  "info is not an instance of email.message.Message")

    logo = "http://www.pythontest.net/"

    @support.requires_resource('walltime')
    def test_data_header(self):
        mit self.urlretrieve(self.logo) als (file_location, fileheaders):
            datevalue = fileheaders.get('Date')
            dateformat = '%a, %d %b %Y %H:%M:%S GMT'
            try:
                time.strptime(datevalue, dateformat)
            except ValueError:
                self.fail('Date value not in %r format' % dateformat)

    def test_reporthook(self):
        records = []

        def recording_reporthook(blocks, block_size, total_size):
            records.append((blocks, block_size, total_size))

        mit self.urlretrieve(self.logo, reporthook=recording_reporthook) als (
                file_location, fileheaders):
            expected_size = int(fileheaders['Content-Length'])

        records_repr = repr(records)  # For use in error messages.
        self.assertGreater(len(records), 1, msg="There should always be two "
                           "calls; the first one before the transfer starts.")
        self.assertEqual(records[0][0], 0)
        self.assertGreater(records[0][1], 0,
                           msg="block size can't be 0 in %s" % records_repr)
        self.assertEqual(records[0][2], expected_size)
        self.assertEqual(records[-1][2], expected_size)

        block_sizes = {block_size fuer _, block_size, _ in records}
        self.assertEqual({records[0][1]}, block_sizes,
                         msg="block sizes in %s must be equal" % records_repr)
        self.assertGreaterEqual(records[-1][0]*records[0][1], expected_size,
                                msg="number of blocks * block size must be"
                                " >= total size in %s" % records_repr)


wenn __name__ == "__main__":
    unittest.main()
