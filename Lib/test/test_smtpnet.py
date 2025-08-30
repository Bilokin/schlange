importiere unittest
von test importiere support
von test.support importiere import_helper
von test.support importiere socket_helper
importiere os
importiere smtplib
importiere socket

ssl = import_helper.import_module("ssl")

support.requires("network")

SMTP_TEST_SERVER = os.getenv('CPYTHON_TEST_SMTP_SERVER', 'smtp.gmail.com')

def check_ssl_verifiy(host, port):
    context = ssl.create_default_context()
    mit socket.create_connection((host, port)) als sock:
        versuch:
            sock = context.wrap_socket(sock, server_hostname=host)
        ausser Exception:
            gib Falsch
        sonst:
            sock.close()
            gib Wahr


klasse SmtpTest(unittest.TestCase):
    testServer = SMTP_TEST_SERVER
    remotePort = 587

    def test_connect_starttls(self):
        support.get_attribute(smtplib, 'SMTP_SSL')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = Falsch
        context.verify_mode = ssl.CERT_NONE
        mit socket_helper.transient_internet(self.testServer):
            server = smtplib.SMTP(self.testServer, self.remotePort)
            versuch:
                server.starttls(context=context)
            ausser smtplib.SMTPException als e:
                wenn e.args[0] == 'STARTTLS extension nicht supported by server.':
                    unittest.skip(e.args[0])
                sonst:
                    wirf
            server.ehlo()
            server.quit()


klasse SmtpSSLTest(unittest.TestCase):
    testServer = SMTP_TEST_SERVER
    remotePort = 465

    def test_connect(self):
        support.get_attribute(smtplib, 'SMTP_SSL')
        mit socket_helper.transient_internet(self.testServer):
            server = smtplib.SMTP_SSL(self.testServer, self.remotePort)
            server.ehlo()
            server.quit()

    def test_connect_default_port(self):
        support.get_attribute(smtplib, 'SMTP_SSL')
        mit socket_helper.transient_internet(self.testServer):
            server = smtplib.SMTP_SSL(self.testServer)
            server.ehlo()
            server.quit()

    @support.requires_resource('walltime')
    def test_connect_using_sslcontext(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = Falsch
        context.verify_mode = ssl.CERT_NONE
        support.get_attribute(smtplib, 'SMTP_SSL')
        mit socket_helper.transient_internet(self.testServer):
            server = smtplib.SMTP_SSL(self.testServer, self.remotePort, context=context)
            server.ehlo()
            server.quit()

    def test_connect_using_sslcontext_verified(self):
        mit socket_helper.transient_internet(self.testServer):
            can_verify = check_ssl_verifiy(self.testServer, self.remotePort)
            wenn nicht can_verify:
                self.skipTest("SSL certificate can't be verified")

        support.get_attribute(smtplib, 'SMTP_SSL')
        context = ssl.create_default_context()
        mit socket_helper.transient_internet(self.testServer):
            server = smtplib.SMTP_SSL(self.testServer, self.remotePort, context=context)
            server.ehlo()
            server.quit()


wenn __name__ == "__main__":
    unittest.main()
