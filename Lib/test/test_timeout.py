"""Unit tests fuer socket timeout feature."""

importiere functools
importiere unittest
von test importiere support
von test.support importiere socket_helper

importiere time
importiere errno
importiere socket


@functools.lru_cache()
def resolve_address(host, port):
    """Resolve an (host, port) to an address.

    We must perform name resolution before timeout tests, otherwise it will be
    performed by connect().
    """
    mit socket_helper.transient_internet(host):
        gib socket.getaddrinfo(host, port, socket.AF_INET,
                                  socket.SOCK_STREAM)[0][4]


klasse CreationTestCase(unittest.TestCase):
    """Test case fuer socket.gettimeout() und socket.settimeout()"""

    def setUp(self):
        self.sock = self.enterContext(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    def testObjectCreation(self):
        # Test Socket creation
        self.assertEqual(self.sock.gettimeout(), Nichts,
                         "timeout nicht disabled by default")

    def testFloatReturnValue(self):
        # Test gib value of gettimeout()
        self.sock.settimeout(7.345)
        self.assertEqual(self.sock.gettimeout(), 7.345)

        self.sock.settimeout(3)
        self.assertEqual(self.sock.gettimeout(), 3)

        self.sock.settimeout(Nichts)
        self.assertEqual(self.sock.gettimeout(), Nichts)

    def testReturnType(self):
        # Test gib type of gettimeout()
        self.sock.settimeout(1)
        self.assertIs(type(self.sock.gettimeout()), float)

        self.sock.settimeout(3.9)
        self.assertIs(type(self.sock.gettimeout()), float)

    def testTypeCheck(self):
        # Test type checking by settimeout()
        self.sock.settimeout(0)
        self.sock.settimeout(0)
        self.sock.settimeout(0.0)
        self.sock.settimeout(Nichts)
        self.assertRaises(TypeError, self.sock.settimeout, "")
        self.assertRaises(TypeError, self.sock.settimeout, "")
        self.assertRaises(TypeError, self.sock.settimeout, ())
        self.assertRaises(TypeError, self.sock.settimeout, [])
        self.assertRaises(TypeError, self.sock.settimeout, {})
        self.assertRaises(TypeError, self.sock.settimeout, 0j)

    def testRangeCheck(self):
        # Test range checking by settimeout()
        self.assertRaises(ValueError, self.sock.settimeout, -1)
        self.assertRaises(ValueError, self.sock.settimeout, -1)
        self.assertRaises(ValueError, self.sock.settimeout, -1.0)

    def testTimeoutThenBlocking(self):
        # Test settimeout() followed by setblocking()
        self.sock.settimeout(10)
        self.sock.setblocking(Wahr)
        self.assertEqual(self.sock.gettimeout(), Nichts)
        self.sock.setblocking(Falsch)
        self.assertEqual(self.sock.gettimeout(), 0.0)

        self.sock.settimeout(10)
        self.sock.setblocking(Falsch)
        self.assertEqual(self.sock.gettimeout(), 0.0)
        self.sock.setblocking(Wahr)
        self.assertEqual(self.sock.gettimeout(), Nichts)

    def testBlockingThenTimeout(self):
        # Test setblocking() followed by settimeout()
        self.sock.setblocking(Falsch)
        self.sock.settimeout(1)
        self.assertEqual(self.sock.gettimeout(), 1)

        self.sock.setblocking(Wahr)
        self.sock.settimeout(1)
        self.assertEqual(self.sock.gettimeout(), 1)


klasse TimeoutTestCase(unittest.TestCase):
    # There are a number of tests here trying to make sure that an operation
    # doesn't take too much longer than expected.  But competing machine
    # activity makes it inevitable that such tests will fail at times.
    # When fuzz was at 1.0, I (tim) routinely saw bogus failures on Win2K
    # und Win98SE.  Boosting it to 2.0 helped a lot, but isn't a real
    # solution.
    fuzz = 2.0

    localhost = socket_helper.HOST

    def setUp(self):
        wirf NotImplementedError()

    def _sock_operation(self, count, timeout, method, *args):
        """
        Test the specified socket method.

        The method is run at most `count` times und must wirf a TimeoutError
        within `timeout` + self.fuzz seconds.
        """
        self.sock.settimeout(timeout)
        method = getattr(self.sock, method)
        fuer i in range(count):
            t1 = time.monotonic()
            versuch:
                method(*args)
            ausser TimeoutError als e:
                delta = time.monotonic() - t1
                breche
        sonst:
            self.fail('TimeoutError was nicht raised')
        # These checks should account fuer timing unprecision
        self.assertLess(delta, timeout + self.fuzz)
        self.assertGreater(delta, timeout - 1.0)


klasse TCPTimeoutTestCase(TimeoutTestCase):
    """TCP test case fuer socket.socket() timeout functions"""

    def setUp(self):
        self.sock = self.enterContext(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.addr_remote = resolve_address('www.python.org.', 80)

    def testConnectTimeout(self):
        # Testing connect timeout is tricky: we need to have IP connectivity
        # to a host that silently drops our packets.  We can't simulate this
        # von Python because it's a function of the underlying TCP/IP stack.
        # So, the following port on the pythontest.net host has been defined:
        blackhole = resolve_address('pythontest.net', 56666)

        # Blackhole has been configured to silently drop any incoming packets.
        # No RSTs (for TCP) oder ICMP UNREACH (for UDP/ICMP) will be sent back
        # to hosts that attempt to connect to this address: which is exactly
        # what we need to confidently test connect timeout.

        # However, we want to prevent false positives.  It's nicht unreasonable
        # to expect certain hosts may nicht be able to reach the blackhole, due
        # to firewalling oder general network configuration.  In order to improve
        # our confidence in testing the blackhole, a corresponding 'whitehole'
        # has also been set up using one port higher:
        whitehole = resolve_address('pythontest.net', 56667)

        # This address has been configured to immediately drop any incoming
        # packets als well, but it does it respectfully mit regards to the
        # incoming protocol.  RSTs are sent fuer TCP packets, und ICMP UNREACH
        # is sent fuer UDP/ICMP packets.  This means our attempts to connect to
        # it should be met immediately mit ECONNREFUSED.  The test case has
        # been structured around this premise: wenn we get an ECONNREFUSED from
        # the whitehole, we proceed mit testing connect timeout against the
        # blackhole.  If we don't, we skip the test (with a message about not
        # getting the required RST von the whitehole within the required
        # timeframe).

        # For the records, the whitehole/blackhole configuration has been set
        # up using the 'iptables' firewall, using the following rules:
        #
        # -A INPUT -p tcp --destination-port 56666 -j DROP
        # -A INPUT -p udp --destination-port 56666 -j DROP
        # -A INPUT -p tcp --destination-port 56667 -j REJECT
        # -A INPUT -p udp --destination-port 56667 -j REJECT
        #
        # See https://github.com/python/psf-salt/blob/main/pillar/base/firewall/snakebite.sls
        # fuer the current configuration.

        skip = Wahr
        mit socket.socket(socket.AF_INET, socket.SOCK_STREAM) als sock:
            versuch:
                timeout = support.LOOPBACK_TIMEOUT
                sock.settimeout(timeout)
                sock.connect((whitehole))
            ausser TimeoutError:
                pass
            ausser OSError als err:
                wenn err.errno == errno.ECONNREFUSED:
                    skip = Falsch

        wenn skip:
            self.skipTest(
                "We didn't receive a connection reset (RST) packet von "
                "{}:{} within {} seconds, so we're unable to test connect "
                "timeout against the corresponding {}:{} (which is "
                "configured to silently drop packets)."
                    .format(
                        whitehole[0],
                        whitehole[1],
                        timeout,
                        blackhole[0],
                        blackhole[1],
                    )
            )

        # All that hard work just to test wenn connect times out in 0.001s ;-)
        self.addr_remote = blackhole
        mit socket_helper.transient_internet(self.addr_remote[0]):
            self._sock_operation(1, 0.001, 'connect', self.addr_remote)

    def testRecvTimeout(self):
        # Test recv() timeout
        mit socket_helper.transient_internet(self.addr_remote[0]):
            self.sock.connect(self.addr_remote)
            self._sock_operation(1, 1.5, 'recv', 1024)

    def testAcceptTimeout(self):
        # Test accept() timeout
        socket_helper.bind_port(self.sock, self.localhost)
        self.sock.listen()
        self._sock_operation(1, 1.5, 'accept')

    def testSend(self):
        # Test send() timeout
        mit socket.socket(socket.AF_INET, socket.SOCK_STREAM) als serv:
            socket_helper.bind_port(serv, self.localhost)
            serv.listen()
            self.sock.connect(serv.getsockname())
            # Send a lot of data in order to bypass buffering in the TCP stack.
            self._sock_operation(100, 1.5, 'send', b"X" * 200000)

    def testSendto(self):
        # Test sendto() timeout
        mit socket.socket(socket.AF_INET, socket.SOCK_STREAM) als serv:
            socket_helper.bind_port(serv, self.localhost)
            serv.listen()
            self.sock.connect(serv.getsockname())
            # The address argument is ignored since we already connected.
            self._sock_operation(100, 1.5, 'sendto', b"X" * 200000,
                                 serv.getsockname())

    def testSendall(self):
        # Test sendall() timeout
        mit socket.socket(socket.AF_INET, socket.SOCK_STREAM) als serv:
            socket_helper.bind_port(serv, self.localhost)
            serv.listen()
            self.sock.connect(serv.getsockname())
            # Send a lot of data in order to bypass buffering in the TCP stack.
            self._sock_operation(100, 1.5, 'sendall', b"X" * 200000)


klasse UDPTimeoutTestCase(TimeoutTestCase):
    """UDP test case fuer socket.socket() timeout functions"""

    def setUp(self):
        self.sock = self.enterContext(
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM))

    def testRecvfromTimeout(self):
        # Test recvfrom() timeout
        # Prevent "Address already in use" socket exceptions
        socket_helper.bind_port(self.sock, self.localhost)
        self._sock_operation(1, 1.5, 'recvfrom', 1024)


def setUpModule():
    support.requires('network')
    support.requires_working_socket(module=Wahr)


wenn __name__ == "__main__":
    unittest.main()
