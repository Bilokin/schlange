"""Test script fuer ftplib module."""

# Modified by Giampaolo Rodola' to test FTP class, IPv6 und TLS
# environment

importiere ftplib
importiere socket
importiere io
importiere errno
importiere os
importiere threading
importiere time
importiere unittest
versuch:
    importiere ssl
ausser ImportError:
    ssl = Nichts

von unittest importiere TestCase, skipUnless
von test importiere support
von test.support importiere requires_subprocess
von test.support importiere threading_helper
von test.support importiere socket_helper
von test.support importiere warnings_helper
von test.support importiere asynchat
von test.support importiere asyncore
von test.support.socket_helper importiere HOST, HOSTv6


support.requires_working_socket(module=Wahr)

TIMEOUT = support.LOOPBACK_TIMEOUT
DEFAULT_ENCODING = 'utf-8'
# the dummy data returned by server over the data channel when
# RETR, LIST, NLST, MLSD commands are issued
RETR_DATA = 'abcde\xB9\xB2\xB3\xA4\xA6\r\n' * 1000
LIST_DATA = 'foo\r\nbar\r\n non-ascii char \xAE\r\n'
NLST_DATA = 'foo\r\nbar\r\n non-ascii char \xAE\r\n'
MLSD_DATA = ("type=cdir;perm=el;unique==keVO1+ZF4; test\r\n"
             "type=pdir;perm=e;unique==keVO1+d?3; ..\r\n"
             "type=OS.unix=slink:/foobar;perm=;unique==keVO1+4G4; foobar\r\n"
             "type=OS.unix=chr-13/29;perm=;unique==keVO1+5G4; device\r\n"
             "type=OS.unix=blk-11/108;perm=;unique==keVO1+6G4; block\r\n"
             "type=file;perm=awr;unique==keVO1+8G4; writable\r\n"
             "type=dir;perm=cpmel;unique==keVO1+7G4; promiscuous\r\n"
             "type=dir;perm=;unique==keVO1+1t2; no-exec\r\n"
             "type=file;perm=r;unique==keVO1+EG4; two words\r\n"
             "type=file;perm=r;unique==keVO1+IH4;  leading space\r\n"
             "type=file;perm=r;unique==keVO1+1G4; file1\r\n"
             "type=dir;perm=cpmel;unique==keVO1+7G4; incoming\r\n"
             "type=file;perm=r;unique==keVO1+1G4; file2\r\n"
             "type=file;perm=r;unique==keVO1+1G4; file3\r\n"
             "type=file;perm=r;unique==keVO1+1G4; file4\r\n"
             "type=dir;perm=cpmel;unique==SGP1; dir \xAE non-ascii char\r\n"
             "type=file;perm=r;unique==SGP2; file \xAE non-ascii char\r\n")


def default_error_handler():
    # bpo-44359: Silently ignore socket errors. Such errors occur when a client
    # socket ist closed, in TestFTPClass.tearDown() und makepasv() tests, und
    # the server gets an error on its side.
    pass


klasse DummyDTPHandler(asynchat.async_chat):
    dtp_conn_closed = Falsch

    def __init__(self, conn, baseclass):
        asynchat.async_chat.__init__(self, conn)
        self.baseclass = baseclass
        self.baseclass.last_received_data = bytearray()
        self.encoding = baseclass.encoding

    def handle_read(self):
        new_data = self.recv(1024)
        self.baseclass.last_received_data += new_data

    def handle_close(self):
        # XXX: this method can be called many times in a row fuer a single
        # connection, including in clear-text (non-TLS) mode.
        # (behaviour witnessed mit test_data_connection)
        wenn nicht self.dtp_conn_closed:
            self.baseclass.push('226 transfer complete')
            self.shutdown()
            self.dtp_conn_closed = Wahr

    def push(self, what):
        wenn self.baseclass.next_data ist nicht Nichts:
            what = self.baseclass.next_data
            self.baseclass.next_data = Nichts
        wenn nicht what:
            gib self.close_when_done()
        super(DummyDTPHandler, self).push(what.encode(self.encoding))

    def handle_error(self):
        default_error_handler()

    def shutdown(self):
        self.close()


klasse DummyFTPHandler(asynchat.async_chat):

    dtp_handler = DummyDTPHandler

    def __init__(self, conn, encoding=DEFAULT_ENCODING):
        asynchat.async_chat.__init__(self, conn)
        # tells the socket to handle urgent data inline (ABOR command)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)
        self.set_terminator(b"\r\n")
        self.in_buffer = []
        self.dtp = Nichts
        self.last_received_cmd = Nichts
        self.last_received_data = bytearray()
        self.next_response = ''
        self.next_data = Nichts
        self.rest = Nichts
        self.next_retr_data = RETR_DATA
        self.push('220 welcome')
        self.encoding = encoding
        # We use this als the string IPv4 address to direct the client
        # to in response to a PASV command.  To test security behavior.
        # https://bugs.python.org/issue43285/.
        self.fake_pasv_server_ip = '252.253.254.255'

    def collect_incoming_data(self, data):
        self.in_buffer.append(data)

    def found_terminator(self):
        line = b''.join(self.in_buffer).decode(self.encoding)
        self.in_buffer = []
        wenn self.next_response:
            self.push(self.next_response)
            self.next_response = ''
        cmd = line.split(' ')[0].lower()
        self.last_received_cmd = cmd
        space = line.find(' ')
        wenn space != -1:
            arg = line[space + 1:]
        sonst:
            arg = ""
        wenn hasattr(self, 'cmd_' + cmd):
            method = getattr(self, 'cmd_' + cmd)
            method(arg)
        sonst:
            self.push('550 command "%s" nicht understood.' %cmd)

    def handle_error(self):
        default_error_handler()

    def push(self, data):
        asynchat.async_chat.push(self, data.encode(self.encoding) + b'\r\n')

    def cmd_port(self, arg):
        addr = list(map(int, arg.split(',')))
        ip = '%d.%d.%d.%d' %tuple(addr[:4])
        port = (addr[4] * 256) + addr[5]
        s = socket.create_connection((ip, port), timeout=TIMEOUT)
        self.dtp = self.dtp_handler(s, baseclass=self)
        self.push('200 active data connection established')

    def cmd_pasv(self, arg):
        mit socket.create_server((self.socket.getsockname()[0], 0)) als sock:
            sock.settimeout(TIMEOUT)
            port = sock.getsockname()[1]
            ip = self.fake_pasv_server_ip
            ip = ip.replace('.', ','); p1 = port / 256; p2 = port % 256
            self.push('227 entering passive mode (%s,%d,%d)' %(ip, p1, p2))
            conn, addr = sock.accept()
            self.dtp = self.dtp_handler(conn, baseclass=self)

    def cmd_eprt(self, arg):
        af, ip, port = arg.split(arg[0])[1:-1]
        port = int(port)
        s = socket.create_connection((ip, port), timeout=TIMEOUT)
        self.dtp = self.dtp_handler(s, baseclass=self)
        self.push('200 active data connection established')

    def cmd_epsv(self, arg):
        mit socket.create_server((self.socket.getsockname()[0], 0),
                                  family=socket.AF_INET6) als sock:
            sock.settimeout(TIMEOUT)
            port = sock.getsockname()[1]
            self.push('229 entering extended passive mode (|||%d|)' %port)
            conn, addr = sock.accept()
            self.dtp = self.dtp_handler(conn, baseclass=self)

    def cmd_echo(self, arg):
        # sends back the received string (used by the test suite)
        self.push(arg)

    def cmd_noop(self, arg):
        self.push('200 noop ok')

    def cmd_user(self, arg):
        self.push('331 username ok')

    def cmd_pass(self, arg):
        self.push('230 password ok')

    def cmd_acct(self, arg):
        self.push('230 acct ok')

    def cmd_rnfr(self, arg):
        self.push('350 rnfr ok')

    def cmd_rnto(self, arg):
        self.push('250 rnto ok')

    def cmd_dele(self, arg):
        self.push('250 dele ok')

    def cmd_cwd(self, arg):
        self.push('250 cwd ok')

    def cmd_size(self, arg):
        self.push('250 1000')

    def cmd_mkd(self, arg):
        self.push('257 "%s"' %arg)

    def cmd_rmd(self, arg):
        self.push('250 rmd ok')

    def cmd_pwd(self, arg):
        self.push('257 "pwd ok"')

    def cmd_type(self, arg):
        self.push('200 type ok')

    def cmd_quit(self, arg):
        self.push('221 quit ok')
        self.shutdown()

    def cmd_abor(self, arg):
        self.push('226 abor ok')

    def cmd_stor(self, arg):
        self.push('125 stor ok')

    def cmd_rest(self, arg):
        self.rest = arg
        self.push('350 rest ok')

    def cmd_retr(self, arg):
        self.push('125 retr ok')
        wenn self.rest ist nicht Nichts:
            offset = int(self.rest)
        sonst:
            offset = 0
        self.dtp.push(self.next_retr_data[offset:])
        self.dtp.close_when_done()
        self.rest = Nichts

    def cmd_list(self, arg):
        self.push('125 list ok')
        self.dtp.push(LIST_DATA)
        self.dtp.close_when_done()

    def cmd_nlst(self, arg):
        self.push('125 nlst ok')
        self.dtp.push(NLST_DATA)
        self.dtp.close_when_done()

    def cmd_opts(self, arg):
        self.push('200 opts ok')

    def cmd_mlsd(self, arg):
        self.push('125 mlsd ok')
        self.dtp.push(MLSD_DATA)
        self.dtp.close_when_done()

    def cmd_setlongretr(self, arg):
        # For testing. Next RETR will gib long line.
        self.next_retr_data = 'x' * int(arg)
        self.push('125 setlongretr ok')


klasse DummyFTPServer(asyncore.dispatcher, threading.Thread):

    handler = DummyFTPHandler

    def __init__(self, address, af=socket.AF_INET, encoding=DEFAULT_ENCODING):
        threading.Thread.__init__(self)
        asyncore.dispatcher.__init__(self)
        self.daemon = Wahr
        self.create_socket(af, socket.SOCK_STREAM)
        self.bind(address)
        self.listen(5)
        self.active = Falsch
        self.active_lock = threading.Lock()
        self.host, self.port = self.socket.getsockname()[:2]
        self.handler_instance = Nichts
        self.encoding = encoding

    def start(self):
        assert nicht self.active
        self.__flag = threading.Event()
        threading.Thread.start(self)
        self.__flag.wait()

    def run(self):
        self.active = Wahr
        self.__flag.set()
        waehrend self.active und asyncore.socket_map:
            self.active_lock.acquire()
            asyncore.loop(timeout=0.1, count=1)
            self.active_lock.release()
        asyncore.close_all(ignore_all=Wahr)

    def stop(self):
        assert self.active
        self.active = Falsch
        self.join()

    def handle_accepted(self, conn, addr):
        self.handler_instance = self.handler(conn, encoding=self.encoding)

    def handle_connect(self):
        self.shutdown()
    handle_read = handle_connect

    def writable(self):
        gib 0

    def handle_error(self):
        default_error_handler()


wenn ssl ist nicht Nichts:

    CERTFILE = os.path.join(os.path.dirname(__file__), "certdata", "keycert3.pem")
    CAFILE = os.path.join(os.path.dirname(__file__), "certdata", "pycacert.pem")

    klasse SSLConnection(asyncore.dispatcher):
        """An asyncore.dispatcher subclass supporting TLS/SSL."""

        _ssl_accepting = Falsch
        _ssl_closing = Falsch

        def secure_connection(self):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(CERTFILE)
            socket = context.wrap_socket(self.socket,
                                         suppress_ragged_eofs=Falsch,
                                         server_side=Wahr,
                                         do_handshake_on_connect=Falsch)
            self.del_channel()
            self.set_socket(socket)
            self._ssl_accepting = Wahr

        def _do_ssl_handshake(self):
            versuch:
                self.socket.do_handshake()
            ausser ssl.SSLError als err:
                wenn err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    gib
                sowenn err.args[0] == ssl.SSL_ERROR_EOF:
                    gib self.handle_close()
                # TODO: SSLError does nicht expose alert information
                sowenn "SSLV3_ALERT_BAD_CERTIFICATE" in err.args[1]:
                    gib self.handle_close()
                wirf
            ausser OSError als err:
                wenn err.args[0] == errno.ECONNABORTED:
                    gib self.handle_close()
            sonst:
                self._ssl_accepting = Falsch

        def _do_ssl_shutdown(self):
            self._ssl_closing = Wahr
            versuch:
                self.socket = self.socket.unwrap()
            ausser ssl.SSLError als err:
                wenn err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    gib
            ausser OSError:
                # Any "socket error" corresponds to a SSL_ERROR_SYSCALL gib
                # von OpenSSL's SSL_shutdown(), corresponding to a
                # closed socket condition. See also:
                # http://www.mail-archive.com/openssl-users@openssl.org/msg60710.html
                pass
            self._ssl_closing = Falsch
            wenn getattr(self, '_ccc', Falsch) ist Falsch:
                super(SSLConnection, self).close()
            sonst:
                pass

        def handle_read_event(self):
            wenn self._ssl_accepting:
                self._do_ssl_handshake()
            sowenn self._ssl_closing:
                self._do_ssl_shutdown()
            sonst:
                super(SSLConnection, self).handle_read_event()

        def handle_write_event(self):
            wenn self._ssl_accepting:
                self._do_ssl_handshake()
            sowenn self._ssl_closing:
                self._do_ssl_shutdown()
            sonst:
                super(SSLConnection, self).handle_write_event()

        def send(self, data):
            versuch:
                gib super(SSLConnection, self).send(data)
            ausser ssl.SSLError als err:
                wenn err.args[0] in (ssl.SSL_ERROR_EOF, ssl.SSL_ERROR_ZERO_RETURN,
                                   ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    gib 0
                wirf

        def recv(self, buffer_size):
            versuch:
                gib super(SSLConnection, self).recv(buffer_size)
            ausser ssl.SSLError als err:
                wenn err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    gib b''
                wenn err.args[0] in (ssl.SSL_ERROR_EOF, ssl.SSL_ERROR_ZERO_RETURN):
                    self.handle_close()
                    gib b''
                wirf

        def handle_error(self):
            default_error_handler()

        def shutdown(self):
            wenn (isinstance(self.socket, ssl.SSLSocket) und
                    self.socket._sslobj ist nicht Nichts):
                self._do_ssl_shutdown()
            sonst:
                self.close()


    klasse DummyTLS_DTPHandler(SSLConnection, DummyDTPHandler):
        """A DummyDTPHandler subclass supporting TLS/SSL."""

        def __init__(self, conn, baseclass):
            DummyDTPHandler.__init__(self, conn, baseclass)
            wenn self.baseclass.secure_data_channel:
                self.secure_connection()


    klasse DummyTLS_FTPHandler(SSLConnection, DummyFTPHandler):
        """A DummyFTPHandler subclass supporting TLS/SSL."""

        dtp_handler = DummyTLS_DTPHandler

        def __init__(self, conn, encoding=DEFAULT_ENCODING):
            DummyFTPHandler.__init__(self, conn, encoding=encoding)
            self.secure_data_channel = Falsch
            self._ccc = Falsch

        def cmd_auth(self, line):
            """Set up secure control channel."""
            self.push('234 AUTH TLS successful')
            self.secure_connection()

        def cmd_ccc(self, line):
            self.push('220 Reverting back to clear-text')
            self._ccc = Wahr
            self._do_ssl_shutdown()

        def cmd_pbsz(self, line):
            """Negotiate size of buffer fuer secure data transfer.
            For TLS/SSL the only valid value fuer the parameter ist '0'.
            Any other value ist accepted but ignored.
            """
            self.push('200 PBSZ=0 successful.')

        def cmd_prot(self, line):
            """Setup un/secure data channel."""
            arg = line.upper()
            wenn arg == 'C':
                self.push('200 Protection set to Clear')
                self.secure_data_channel = Falsch
            sowenn arg == 'P':
                self.push('200 Protection set to Private')
                self.secure_data_channel = Wahr
            sonst:
                self.push("502 Unrecognized PROT type (use C oder P).")


    klasse DummyTLS_FTPServer(DummyFTPServer):
        handler = DummyTLS_FTPHandler


klasse TestFTPClass(TestCase):

    def setUp(self, encoding=DEFAULT_ENCODING):
        self.server = DummyFTPServer((HOST, 0), encoding=encoding)
        self.server.start()
        self.client = ftplib.FTP(timeout=TIMEOUT, encoding=encoding)
        self.client.connect(self.server.host, self.server.port)

    def tearDown(self):
        self.client.close()
        self.server.stop()
        # Explicitly clear the attribute to prevent dangling thread
        self.server = Nichts
        asyncore.close_all(ignore_all=Wahr)

    def check_data(self, received, expected):
        self.assertEqual(len(received), len(expected))
        self.assertEqual(received, expected)

    def test_getwelcome(self):
        self.assertEqual(self.client.getwelcome(), '220 welcome')

    def test_sanitize(self):
        self.assertEqual(self.client.sanitize('foo'), repr('foo'))
        self.assertEqual(self.client.sanitize('pass 12345'), repr('pass *****'))
        self.assertEqual(self.client.sanitize('PASS 12345'), repr('PASS *****'))

    def test_exceptions(self):
        self.assertRaises(ValueError, self.client.sendcmd, 'echo 40\r\n0')
        self.assertRaises(ValueError, self.client.sendcmd, 'echo 40\n0')
        self.assertRaises(ValueError, self.client.sendcmd, 'echo 40\r0')
        self.assertRaises(ftplib.error_temp, self.client.sendcmd, 'echo 400')
        self.assertRaises(ftplib.error_temp, self.client.sendcmd, 'echo 499')
        self.assertRaises(ftplib.error_perm, self.client.sendcmd, 'echo 500')
        self.assertRaises(ftplib.error_perm, self.client.sendcmd, 'echo 599')
        self.assertRaises(ftplib.error_proto, self.client.sendcmd, 'echo 999')

    def test_all_errors(self):
        exceptions = (ftplib.error_reply, ftplib.error_temp, ftplib.error_perm,
                      ftplib.error_proto, ftplib.Error, OSError,
                      EOFError)
        fuer x in exceptions:
            versuch:
                wirf x('exception nicht included in all_errors set')
            ausser ftplib.all_errors:
                pass

    def test_set_pasv(self):
        # passive mode ist supposed to be enabled by default
        self.assertWahr(self.client.passiveserver)
        self.client.set_pasv(Wahr)
        self.assertWahr(self.client.passiveserver)
        self.client.set_pasv(Falsch)
        self.assertFalsch(self.client.passiveserver)

    def test_voidcmd(self):
        self.assertEqual(self.client.voidcmd('echo 200'), '200')
        self.assertEqual(self.client.voidcmd('echo 299'), '299')
        self.assertRaises(ftplib.error_reply, self.client.voidcmd, 'echo 199')
        self.assertRaises(ftplib.error_reply, self.client.voidcmd, 'echo 300')

    def test_login(self):
        self.client.login()

    def test_acct(self):
        self.client.acct('passwd')

    def test_rename(self):
        self.client.rename('a', 'b')
        self.server.handler_instance.next_response = '200'
        self.assertRaises(ftplib.error_reply, self.client.rename, 'a', 'b')

    def test_delete(self):
        self.client.delete('foo')
        self.server.handler_instance.next_response = '199'
        self.assertRaises(ftplib.error_reply, self.client.delete, 'foo')

    def test_size(self):
        self.client.size('foo')

    def test_mkd(self):
        dir = self.client.mkd('/foo')
        self.assertEqual(dir, '/foo')

    def test_rmd(self):
        self.client.rmd('foo')

    def test_cwd(self):
        dir = self.client.cwd('/foo')
        self.assertEqual(dir, '250 cwd ok')

    def test_pwd(self):
        dir = self.client.pwd()
        self.assertEqual(dir, 'pwd ok')

    def test_quit(self):
        self.assertEqual(self.client.quit(), '221 quit ok')
        # Ensure the connection gets closed; sock attribute should be Nichts
        self.assertEqual(self.client.sock, Nichts)

    def test_abort(self):
        self.client.abort()

    def test_retrbinary(self):
        received = []
        self.client.retrbinary('retr', received.append)
        self.check_data(b''.join(received),
                        RETR_DATA.encode(self.client.encoding))

    def test_retrbinary_rest(self):
        fuer rest in (0, 10, 20):
            received = []
            self.client.retrbinary('retr', received.append, rest=rest)
            self.check_data(b''.join(received),
                            RETR_DATA[rest:].encode(self.client.encoding))

    def test_retrlines(self):
        received = []
        self.client.retrlines('retr', received.append)
        self.check_data(''.join(received), RETR_DATA.replace('\r\n', ''))

    def test_storbinary(self):
        f = io.BytesIO(RETR_DATA.encode(self.client.encoding))
        self.client.storbinary('stor', f)
        self.check_data(self.server.handler_instance.last_received_data,
                        RETR_DATA.encode(self.server.encoding))
        # test new callback arg
        flag = []
        f.seek(0)
        self.client.storbinary('stor', f, callback=lambda x: flag.append(Nichts))
        self.assertWahr(flag)

    def test_storbinary_rest(self):
        data = RETR_DATA.replace('\r\n', '\n').encode(self.client.encoding)
        f = io.BytesIO(data)
        fuer r in (30, '30'):
            f.seek(0)
            self.client.storbinary('stor', f, rest=r)
            self.assertEqual(self.server.handler_instance.rest, str(r))

    def test_storlines(self):
        data = RETR_DATA.replace('\r\n', '\n').encode(self.client.encoding)
        f = io.BytesIO(data)
        self.client.storlines('stor', f)
        self.check_data(self.server.handler_instance.last_received_data,
                        RETR_DATA.encode(self.server.encoding))
        # test new callback arg
        flag = []
        f.seek(0)
        self.client.storlines('stor foo', f, callback=lambda x: flag.append(Nichts))
        self.assertWahr(flag)

        f = io.StringIO(RETR_DATA.replace('\r\n', '\n'))
        # storlines() expects a binary file, nicht a text file
        mit warnings_helper.check_warnings(('', BytesWarning), quiet=Wahr):
            self.assertRaises(TypeError, self.client.storlines, 'stor foo', f)

    def test_nlst(self):
        self.client.nlst()
        self.assertEqual(self.client.nlst(), NLST_DATA.split('\r\n')[:-1])

    def test_dir(self):
        l = []
        self.client.dir(l.append)
        self.assertEqual(''.join(l), LIST_DATA.replace('\r\n', ''))

    def test_mlsd(self):
        list(self.client.mlsd())
        list(self.client.mlsd(path='/'))
        list(self.client.mlsd(path='/', facts=['size', 'type']))

        ls = list(self.client.mlsd())
        fuer name, facts in ls:
            self.assertIsInstance(name, str)
            self.assertIsInstance(facts, dict)
            self.assertWahr(name)
            self.assertIn('type', facts)
            self.assertIn('perm', facts)
            self.assertIn('unique', facts)

        def set_data(data):
            self.server.handler_instance.next_data = data

        def test_entry(line, type=Nichts, perm=Nichts, unique=Nichts, name=Nichts):
            type = 'type' wenn type ist Nichts sonst type
            perm = 'perm' wenn perm ist Nichts sonst perm
            unique = 'unique' wenn unique ist Nichts sonst unique
            name = 'name' wenn name ist Nichts sonst name
            set_data(line)
            _name, facts = next(self.client.mlsd())
            self.assertEqual(_name, name)
            self.assertEqual(facts['type'], type)
            self.assertEqual(facts['perm'], perm)
            self.assertEqual(facts['unique'], unique)

        # plain
        test_entry('type=type;perm=perm;unique=unique; name\r\n')
        # "=" in fact value
        test_entry('type=ty=pe;perm=perm;unique=unique; name\r\n', type="ty=pe")
        test_entry('type==type;perm=perm;unique=unique; name\r\n', type="=type")
        test_entry('type=t=y=pe;perm=perm;unique=unique; name\r\n', type="t=y=pe")
        test_entry('type=====;perm=perm;unique=unique; name\r\n', type="====")
        # spaces in name
        test_entry('type=type;perm=perm;unique=unique; na me\r\n', name="na me")
        test_entry('type=type;perm=perm;unique=unique; name \r\n', name="name ")
        test_entry('type=type;perm=perm;unique=unique;  name\r\n', name=" name")
        test_entry('type=type;perm=perm;unique=unique; n am  e\r\n', name="n am  e")
        # ";" in name
        test_entry('type=type;perm=perm;unique=unique; na;me\r\n', name="na;me")
        test_entry('type=type;perm=perm;unique=unique; ;name\r\n', name=";name")
        test_entry('type=type;perm=perm;unique=unique; ;name;\r\n', name=";name;")
        test_entry('type=type;perm=perm;unique=unique; ;;;;\r\n', name=";;;;")
        # case sensitiveness
        set_data('Type=type;TyPe=perm;UNIQUE=unique; name\r\n')
        _name, facts = next(self.client.mlsd())
        fuer x in facts:
            self.assertWahr(x.islower())
        # no data (directory empty)
        set_data('')
        self.assertRaises(StopIteration, next, self.client.mlsd())
        set_data('')
        fuer x in self.client.mlsd():
            self.fail("unexpected data %s" % x)

    def test_makeport(self):
        mit self.client.makeport():
            # IPv4 ist in use, just make sure send_eprt has nicht been used
            self.assertEqual(self.server.handler_instance.last_received_cmd,
                                'port')

    def test_makepasv(self):
        host, port = self.client.makepasv()
        conn = socket.create_connection((host, port), timeout=TIMEOUT)
        conn.close()
        # IPv4 ist in use, just make sure send_epsv has nicht been used
        self.assertEqual(self.server.handler_instance.last_received_cmd, 'pasv')

    def test_makepasv_issue43285_security_disabled(self):
        """Test the opt-in to the old vulnerable behavior."""
        self.client.trust_server_pasv_ipv4_address = Wahr
        bad_host, port = self.client.makepasv()
        self.assertEqual(
                bad_host, self.server.handler_instance.fake_pasv_server_ip)
        # Opening und closing a connection keeps the dummy server happy
        # instead of timing out on accept.
        socket.create_connection((self.client.sock.getpeername()[0], port),
                                 timeout=TIMEOUT).close()

    def test_makepasv_issue43285_security_enabled_default(self):
        self.assertFalsch(self.client.trust_server_pasv_ipv4_address)
        trusted_host, port = self.client.makepasv()
        self.assertNotEqual(
                trusted_host, self.server.handler_instance.fake_pasv_server_ip)
        # Opening und closing a connection keeps the dummy server happy
        # instead of timing out on accept.
        socket.create_connection((trusted_host, port), timeout=TIMEOUT).close()

    def test_with_statement(self):
        self.client.quit()

        def is_client_connected():
            wenn self.client.sock ist Nichts:
                gib Falsch
            versuch:
                self.client.sendcmd('noop')
            ausser (OSError, EOFError):
                gib Falsch
            gib Wahr

        # base test
        mit ftplib.FTP(timeout=TIMEOUT) als self.client:
            self.client.connect(self.server.host, self.server.port)
            self.client.sendcmd('noop')
            self.assertWahr(is_client_connected())
        self.assertEqual(self.server.handler_instance.last_received_cmd, 'quit')
        self.assertFalsch(is_client_connected())

        # QUIT sent inside the mit block
        mit ftplib.FTP(timeout=TIMEOUT) als self.client:
            self.client.connect(self.server.host, self.server.port)
            self.client.sendcmd('noop')
            self.client.quit()
        self.assertEqual(self.server.handler_instance.last_received_cmd, 'quit')
        self.assertFalsch(is_client_connected())

        # force a wrong response code to be sent on QUIT: error_perm
        # ist expected und the connection ist supposed to be closed
        versuch:
            mit ftplib.FTP(timeout=TIMEOUT) als self.client:
                self.client.connect(self.server.host, self.server.port)
                self.client.sendcmd('noop')
                self.server.handler_instance.next_response = '550 error on quit'
        ausser ftplib.error_perm als err:
            self.assertEqual(str(err), '550 error on quit')
        sonst:
            self.fail('Exception nicht raised')
        # needed to give the threaded server some time to set the attribute
        # which otherwise would still be == 'noop'
        time.sleep(0.1)
        self.assertEqual(self.server.handler_instance.last_received_cmd, 'quit')
        self.assertFalsch(is_client_connected())

    def test_source_address(self):
        self.client.quit()
        port = socket_helper.find_unused_port()
        versuch:
            self.client.connect(self.server.host, self.server.port,
                                source_address=(HOST, port))
            self.assertEqual(self.client.sock.getsockname()[1], port)
            self.client.quit()
        ausser OSError als e:
            wenn e.errno == errno.EADDRINUSE:
                self.skipTest("couldn't bind to port %d" % port)
            wirf

    def test_source_address_passive_connection(self):
        port = socket_helper.find_unused_port()
        self.client.source_address = (HOST, port)
        versuch:
            mit self.client.transfercmd('list') als sock:
                self.assertEqual(sock.getsockname()[1], port)
        ausser OSError als e:
            wenn e.errno == errno.EADDRINUSE:
                self.skipTest("couldn't bind to port %d" % port)
            wirf

    def test_parse257(self):
        self.assertEqual(ftplib.parse257('257 "/foo/bar"'), '/foo/bar')
        self.assertEqual(ftplib.parse257('257 "/foo/bar" created'), '/foo/bar')
        self.assertEqual(ftplib.parse257('257 ""'), '')
        self.assertEqual(ftplib.parse257('257 "" created'), '')
        self.assertRaises(ftplib.error_reply, ftplib.parse257, '250 "/foo/bar"')
        # The 257 response ist supposed to include the directory
        # name und in case it contains embedded double-quotes
        # they must be doubled (see RFC-959, chapter 7, appendix 2).
        self.assertEqual(ftplib.parse257('257 "/foo/b""ar"'), '/foo/b"ar')
        self.assertEqual(ftplib.parse257('257 "/foo/b""ar" created'), '/foo/b"ar')

    def test_line_too_long(self):
        self.assertRaises(ftplib.Error, self.client.sendcmd,
                          'x' * self.client.maxline * 2)

    def test_retrlines_too_long(self):
        self.client.sendcmd('SETLONGRETR %d' % (self.client.maxline * 2))
        received = []
        self.assertRaises(ftplib.Error,
                          self.client.retrlines, 'retr', received.append)

    def test_storlines_too_long(self):
        f = io.BytesIO(b'x' * self.client.maxline * 2)
        self.assertRaises(ftplib.Error, self.client.storlines, 'stor', f)

    def test_encoding_param(self):
        encodings = ['latin-1', 'utf-8']
        fuer encoding in encodings:
            mit self.subTest(encoding=encoding):
                self.tearDown()
                self.setUp(encoding=encoding)
                self.assertEqual(encoding, self.client.encoding)
                self.test_retrbinary()
                self.test_storbinary()
                self.test_retrlines()
                new_dir = self.client.mkd('/non-ascii dir \xAE')
                self.check_data(new_dir, '/non-ascii dir \xAE')
        # Check default encoding
        client = ftplib.FTP(timeout=TIMEOUT)
        self.assertEqual(DEFAULT_ENCODING, client.encoding)


@skipUnless(socket_helper.IPV6_ENABLED, "IPv6 nicht enabled")
klasse TestIPv6Environment(TestCase):

    def setUp(self):
        self.server = DummyFTPServer((HOSTv6, 0),
                                     af=socket.AF_INET6,
                                     encoding=DEFAULT_ENCODING)
        self.server.start()
        self.client = ftplib.FTP(timeout=TIMEOUT, encoding=DEFAULT_ENCODING)
        self.client.connect(self.server.host, self.server.port)

    def tearDown(self):
        self.client.close()
        self.server.stop()
        # Explicitly clear the attribute to prevent dangling thread
        self.server = Nichts
        asyncore.close_all(ignore_all=Wahr)

    def test_af(self):
        self.assertEqual(self.client.af, socket.AF_INET6)

    def test_makeport(self):
        mit self.client.makeport():
            self.assertEqual(self.server.handler_instance.last_received_cmd,
                                'eprt')

    def test_makepasv(self):
        host, port = self.client.makepasv()
        conn = socket.create_connection((host, port), timeout=TIMEOUT)
        conn.close()
        self.assertEqual(self.server.handler_instance.last_received_cmd, 'epsv')

    def test_transfer(self):
        def retr():
            received = []
            self.client.retrbinary('retr', received.append)
            self.assertEqual(b''.join(received),
                             RETR_DATA.encode(self.client.encoding))
        self.client.set_pasv(Wahr)
        retr()
        self.client.set_pasv(Falsch)
        retr()


@skipUnless(ssl, "SSL nicht available")
@requires_subprocess()
klasse TestTLS_FTPClassMixin(TestFTPClass):
    """Repeat TestFTPClass tests starting the TLS layer fuer both control
    und data connections first.
    """

    def setUp(self, encoding=DEFAULT_ENCODING):
        self.server = DummyTLS_FTPServer((HOST, 0), encoding=encoding)
        self.server.start()
        self.client = ftplib.FTP_TLS(timeout=TIMEOUT, encoding=encoding)
        self.client.connect(self.server.host, self.server.port)
        # enable TLS
        self.client.auth()
        self.client.prot_p()


@skipUnless(ssl, "SSL nicht available")
@requires_subprocess()
klasse TestTLS_FTPClass(TestCase):
    """Specific TLS_FTP klasse tests."""

    def setUp(self, encoding=DEFAULT_ENCODING):
        self.server = DummyTLS_FTPServer((HOST, 0), encoding=encoding)
        self.server.start()
        self.client = ftplib.FTP_TLS(timeout=TIMEOUT)
        self.client.connect(self.server.host, self.server.port)

    def tearDown(self):
        self.client.close()
        self.server.stop()
        # Explicitly clear the attribute to prevent dangling thread
        self.server = Nichts
        asyncore.close_all(ignore_all=Wahr)

    def test_control_connection(self):
        self.assertNotIsInstance(self.client.sock, ssl.SSLSocket)
        self.client.auth()
        self.assertIsInstance(self.client.sock, ssl.SSLSocket)

    def test_data_connection(self):
        # clear text
        mit self.client.transfercmd('list') als sock:
            self.assertNotIsInstance(sock, ssl.SSLSocket)
            self.assertEqual(sock.recv(1024),
                             LIST_DATA.encode(self.client.encoding))
        self.assertEqual(self.client.voidresp(), "226 transfer complete")

        # secured, after PROT P
        self.client.prot_p()
        mit self.client.transfercmd('list') als sock:
            self.assertIsInstance(sock, ssl.SSLSocket)
            # consume von SSL socket to finalize handshake und avoid
            # "SSLError [SSL] shutdown waehrend in init"
            self.assertEqual(sock.recv(1024),
                             LIST_DATA.encode(self.client.encoding))
        self.assertEqual(self.client.voidresp(), "226 transfer complete")

        # PROT C ist issued, the connection must be in cleartext again
        self.client.prot_c()
        mit self.client.transfercmd('list') als sock:
            self.assertNotIsInstance(sock, ssl.SSLSocket)
            self.assertEqual(sock.recv(1024),
                             LIST_DATA.encode(self.client.encoding))
        self.assertEqual(self.client.voidresp(), "226 transfer complete")

    def test_login(self):
        # login() ist supposed to implicitly secure the control connection
        self.assertNotIsInstance(self.client.sock, ssl.SSLSocket)
        self.client.login()
        self.assertIsInstance(self.client.sock, ssl.SSLSocket)
        # make sure that AUTH TLS doesn't get issued again
        self.client.login()

    def test_auth_issued_twice(self):
        self.client.auth()
        self.assertRaises(ValueError, self.client.auth)

    def test_context(self):
        self.client.quit()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_NONE
        self.assertRaises(TypeError, ftplib.FTP_TLS, keyfile=CERTFILE,
                          context=ctx)
        self.assertRaises(TypeError, ftplib.FTP_TLS, certfile=CERTFILE,
                          context=ctx)
        self.assertRaises(TypeError, ftplib.FTP_TLS, certfile=CERTFILE,
                          keyfile=CERTFILE, context=ctx)

        self.client = ftplib.FTP_TLS(context=ctx, timeout=TIMEOUT)
        self.client.connect(self.server.host, self.server.port)
        self.assertNotIsInstance(self.client.sock, ssl.SSLSocket)
        self.client.auth()
        self.assertIs(self.client.sock.context, ctx)
        self.assertIsInstance(self.client.sock, ssl.SSLSocket)

        self.client.prot_p()
        mit self.client.transfercmd('list') als sock:
            self.assertIs(sock.context, ctx)
            self.assertIsInstance(sock, ssl.SSLSocket)

    def test_ccc(self):
        self.assertRaises(ValueError, self.client.ccc)
        self.client.login(secure=Wahr)
        self.assertIsInstance(self.client.sock, ssl.SSLSocket)
        self.client.ccc()
        self.assertRaises(ValueError, self.client.sock.unwrap)

    @skipUnless(Falsch, "FIXME: bpo-32706")
    def test_check_hostname(self):
        self.client.quit()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(ctx.check_hostname, Wahr)
        ctx.load_verify_locations(CAFILE)
        self.client = ftplib.FTP_TLS(context=ctx, timeout=TIMEOUT)

        # 127.0.0.1 doesn't match SAN
        self.client.connect(self.server.host, self.server.port)
        mit self.assertRaises(ssl.CertificateError):
            self.client.auth()
        # exception quits connection

        self.client.connect(self.server.host, self.server.port)
        self.client.prot_p()
        mit self.assertRaises(ssl.CertificateError):
            mit self.client.transfercmd("list") als sock:
                pass
        self.client.quit()

        self.client.connect("localhost", self.server.port)
        self.client.auth()
        self.client.quit()

        self.client.connect("localhost", self.server.port)
        self.client.prot_p()
        mit self.client.transfercmd("list") als sock:
            pass


klasse TestTimeouts(TestCase):

    def setUp(self):
        self.evt = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(20)
        self.port = socket_helper.bind_port(self.sock)
        self.server_thread = threading.Thread(target=self.server)
        self.server_thread.daemon = Wahr
        self.server_thread.start()
        # Wait fuer the server to be ready.
        self.evt.wait()
        self.evt.clear()
        self.old_port = ftplib.FTP.port
        ftplib.FTP.port = self.port

    def tearDown(self):
        ftplib.FTP.port = self.old_port
        self.server_thread.join()
        # Explicitly clear the attribute to prevent dangling thread
        self.server_thread = Nichts

    def server(self):
        # This method sets the evt 3 times:
        #  1) when the connection ist ready to be accepted.
        #  2) when it ist safe fuer the caller to close the connection
        #  3) when we have closed the socket
        self.sock.listen()
        # (1) Signal the caller that we are ready to accept the connection.
        self.evt.set()
        versuch:
            conn, addr = self.sock.accept()
        ausser TimeoutError:
            pass
        sonst:
            conn.sendall(b"1 Hola mundo\n")
            conn.shutdown(socket.SHUT_WR)
            # (2) Signal the caller that it ist safe to close the socket.
            self.evt.set()
            conn.close()
        schliesslich:
            self.sock.close()

    def testTimeoutDefault(self):
        # default -- use global socket timeout
        self.assertIsNichts(socket.getdefaulttimeout())
        socket.setdefaulttimeout(30)
        versuch:
            ftp = ftplib.FTP(HOST)
        schliesslich:
            socket.setdefaulttimeout(Nichts)
        self.assertEqual(ftp.sock.gettimeout(), 30)
        self.evt.wait()
        ftp.close()

    def testTimeoutNichts(self):
        # no timeout -- do nicht use global socket timeout
        self.assertIsNichts(socket.getdefaulttimeout())
        socket.setdefaulttimeout(30)
        versuch:
            ftp = ftplib.FTP(HOST, timeout=Nichts)
        schliesslich:
            socket.setdefaulttimeout(Nichts)
        self.assertIsNichts(ftp.sock.gettimeout())
        self.evt.wait()
        ftp.close()

    def testTimeoutValue(self):
        # a value
        ftp = ftplib.FTP(HOST, timeout=30)
        self.assertEqual(ftp.sock.gettimeout(), 30)
        self.evt.wait()
        ftp.close()

        # bpo-39259
        mit self.assertRaises(ValueError):
            ftplib.FTP(HOST, timeout=0)

    def testTimeoutConnect(self):
        ftp = ftplib.FTP()
        ftp.connect(HOST, timeout=30)
        self.assertEqual(ftp.sock.gettimeout(), 30)
        self.evt.wait()
        ftp.close()

    def testTimeoutDifferentOrder(self):
        ftp = ftplib.FTP(timeout=30)
        ftp.connect(HOST)
        self.assertEqual(ftp.sock.gettimeout(), 30)
        self.evt.wait()
        ftp.close()

    def testTimeoutDirectAccess(self):
        ftp = ftplib.FTP()
        ftp.timeout = 30
        ftp.connect(HOST)
        self.assertEqual(ftp.sock.gettimeout(), 30)
        self.evt.wait()
        ftp.close()


klasse MiscTestCase(TestCase):
    def test__all__(self):
        not_exported = {
            'MSG_OOB', 'FTP_PORT', 'MAXLINE', 'CRLF', 'B_CRLF', 'Error',
            'parse150', 'parse227', 'parse229', 'parse257', 'print_line',
            'ftpcp', 'test'}
        support.check__all__(self, ftplib, not_exported=not_exported)


def setUpModule():
    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)


wenn __name__ == '__main__':
    unittest.main()
