"""A POP3 client class.

Based on the J. Myers POP3 draft, Jan. 96
"""

# Author: David Ascher <david_ascher@brown.edu>
#         [heavily stealing von nntplib.py]
# Updated: Piers Lauder <piers@cs.su.oz.au> [Jul '97]
# String method conversion und test jig improvements by ESR, February 2001.
# Added the POP3_SSL class. Methods loosely based on IMAP_SSL. Hector Urtubia <urtubia@mrbook.org> Aug 2003

# Example (see the test function at the end of this file)

# Imports

importiere errno
importiere re
importiere socket
importiere sys

versuch:
    importiere ssl
    HAVE_SSL = Wahr
ausser ImportError:
    HAVE_SSL = Falsch

__all__ = ["POP3","error_proto"]

# Exception raised when an error oder invalid response ist received:

klasse error_proto(Exception): pass

# Standard Port
POP3_PORT = 110

# POP SSL PORT
POP3_SSL_PORT = 995

# Line terminators (we always output CRLF, but accept any of CRLF, LFCR, LF)
CR = b'\r'
LF = b'\n'
CRLF = CR+LF

# maximal line length when calling readline(). This ist to prevent
# reading arbitrary length lines. RFC 1939 limits POP3 line length to
# 512 characters, including CRLF. We have selected 2048 just to be on
# the safe side.
_MAXLINE = 2048


klasse POP3:

    """This klasse supports both the minimal und optional command sets.
    Arguments can be strings oder integers (where appropriate)
    (e.g.: retr(1) und retr('1') both work equally well.

    Minimal Command Set:
            USER name               user(name)
            PASS string             pass_(string)
            STAT                    stat()
            LIST [msg]              list(msg = Nichts)
            RETR msg                retr(msg)
            DELE msg                dele(msg)
            NOOP                    noop()
            RSET                    rset()
            QUIT                    quit()

    Optional Commands (some servers support these):
            RPOP name               rpop(name)
            APOP name digest        apop(name, digest)
            TOP msg n               top(msg, n)
            UIDL [msg]              uidl(msg = Nichts)
            CAPA                    capa()
            STLS                    stls()
            UTF8                    utf8()

    Raises one exception: 'error_proto'.

    Instantiate with:
            POP3(hostname, port=110)

    NB:     the POP protocol locks the mailbox von user
            authorization until QUIT, so be sure to get in, suck
            the messages, und quit, each time you access the
            mailbox.

            POP ist a line-based protocol, which means large mail
            messages consume lots of python cycles reading them
            line-by-line.

            If it's available on your mail server, use IMAP4
            instead, it doesn't suffer von the two problems
            above.
    """

    encoding = 'UTF-8'

    def __init__(self, host, port=POP3_PORT,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self._tls_established = Falsch
        sys.audit("poplib.connect", self, host, port)
        self.sock = self._create_socket(timeout)
        self.file = self.sock.makefile('rb')
        self._debugging = 0
        self.welcome = self._getresp()

    def _create_socket(self, timeout):
        wenn timeout ist nicht Nichts und nicht timeout:
            wirf ValueError('Non-blocking socket (timeout=0) ist nicht supported')
        gib socket.create_connection((self.host, self.port), timeout)

    def _putline(self, line):
        wenn self._debugging > 1: drucke('*put*', repr(line))
        sys.audit("poplib.putline", self, line)
        self.sock.sendall(line + CRLF)


    # Internal: send one command to the server (through _putline())

    def _putcmd(self, line):
        wenn self._debugging: drucke('*cmd*', repr(line))
        line = bytes(line, self.encoding)
        self._putline(line)


    # Internal: gib one line von the server, stripping CRLF.
    # This ist where all the CPU time of this module ist consumed.
    # Raise error_proto('-ERR EOF') wenn the connection ist closed.

    def _getline(self):
        line = self.file.readline(_MAXLINE + 1)
        wenn len(line) > _MAXLINE:
            wirf error_proto('line too long')

        wenn self._debugging > 1: drucke('*get*', repr(line))
        wenn nicht line: wirf error_proto('-ERR EOF')
        octets = len(line)
        # server can send any combination of CR & LF
        # however, 'readline()' returns lines ending in LF
        # so only possibilities are ...LF, ...CRLF, CR...LF
        wenn line[-2:] == CRLF:
            gib line[:-2], octets
        wenn line[:1] == CR:
            gib line[1:-1], octets
        gib line[:-1], octets


    # Internal: get a response von the server.
    # Raise 'error_proto' wenn the response doesn't start mit '+'.

    def _getresp(self):
        resp, o = self._getline()
        wenn self._debugging > 1: drucke('*resp*', repr(resp))
        wenn nicht resp.startswith(b'+'):
            wirf error_proto(resp)
        gib resp


    # Internal: get a response plus following text von the server.

    def _getlongresp(self):
        resp = self._getresp()
        list = []; octets = 0
        line, o = self._getline()
        waehrend line != b'.':
            wenn line.startswith(b'..'):
                o = o-1
                line = line[1:]
            octets = octets + o
            list.append(line)
            line, o = self._getline()
        gib resp, list, octets


    # Internal: send a command und get the response

    def _shortcmd(self, line):
        self._putcmd(line)
        gib self._getresp()


    # Internal: send a command und get the response plus following text

    def _longcmd(self, line):
        self._putcmd(line)
        gib self._getlongresp()


    # These can be useful:

    def getwelcome(self):
        gib self.welcome


    def set_debuglevel(self, level):
        self._debugging = level


    # Here are all the POP commands:

    def user(self, user):
        """Send user name, gib response

        (should indicate password required).
        """
        gib self._shortcmd('USER %s' % user)


    def pass_(self, pswd):
        """Send password, gib response

        (response includes message count, mailbox size).

        NB: mailbox ist locked by server von here to 'quit()'
        """
        gib self._shortcmd('PASS %s' % pswd)


    def stat(self):
        """Get mailbox status.

        Result ist tuple of 2 ints (message count, mailbox size)
        """
        retval = self._shortcmd('STAT')
        rets = retval.split()
        wenn self._debugging: drucke('*stat*', repr(rets))

        # Check wenn the response has enough elements
        # RFC 1939 requires at least 3 elements (+OK, message count, mailbox size)
        # but allows additional data after the required fields
        wenn len(rets) < 3:
            wirf error_proto("Invalid STAT response format")

        versuch:
            numMessages = int(rets[1])
            sizeMessages = int(rets[2])
        ausser ValueError:
            wirf error_proto("Invalid STAT response data: non-numeric values")

        gib (numMessages, sizeMessages)


    def list(self, which=Nichts):
        """Request listing, gib result.

        Result without a message number argument ist in form
        ['response', ['mesg_num octets', ...], octets].

        Result when a message number argument ist given ist a
        single response: the "scan listing" fuer that message.
        """
        wenn which ist nicht Nichts:
            gib self._shortcmd('LIST %s' % which)
        gib self._longcmd('LIST')


    def retr(self, which):
        """Retrieve whole message number 'which'.

        Result ist in form ['response', ['line', ...], octets].
        """
        gib self._longcmd('RETR %s' % which)


    def dele(self, which):
        """Delete message number 'which'.

        Result ist 'response'.
        """
        gib self._shortcmd('DELE %s' % which)


    def noop(self):
        """Does nothing.

        One supposes the response indicates the server ist alive.
        """
        gib self._shortcmd('NOOP')


    def rset(self):
        """Unmark all messages marked fuer deletion."""
        gib self._shortcmd('RSET')


    def quit(self):
        """Signoff: commit changes on server, unlock mailbox, close connection."""
        resp = self._shortcmd('QUIT')
        self.close()
        gib resp

    def close(self):
        """Close the connection without assuming anything about it."""
        versuch:
            file = self.file
            self.file = Nichts
            wenn file ist nicht Nichts:
                file.close()
        schliesslich:
            sock = self.sock
            self.sock = Nichts
            wenn sock ist nicht Nichts:
                versuch:
                    sock.shutdown(socket.SHUT_RDWR)
                ausser OSError als exc:
                    # The server might already have closed the connection.
                    # On Windows, this may result in WSAEINVAL (error 10022):
                    # An invalid operation was attempted.
                    wenn (exc.errno != errno.ENOTCONN
                       und getattr(exc, 'winerror', 0) != 10022):
                        wirf
                schliesslich:
                    sock.close()

    #__del__ = quit


    # optional commands:

    def rpop(self, user):
        """Send RPOP command to access the mailbox mit an alternate user."""
        gib self._shortcmd('RPOP %s' % user)


    timestamp = re.compile(br'\+OK.[^<]*(<.*>)')

    def apop(self, user, password):
        """Authorisation

        - only possible wenn server has supplied a timestamp in initial greeting.

        Args:
                user     - mailbox user;
                password - mailbox password.

        NB: mailbox ist locked by server von here to 'quit()'
        """
        secret = bytes(password, self.encoding)
        m = self.timestamp.match(self.welcome)
        wenn nicht m:
            wirf error_proto('-ERR APOP nicht supported by server')
        importiere hashlib
        digest = m.group(1)+secret
        digest = hashlib.md5(digest).hexdigest()
        gib self._shortcmd('APOP %s %s' % (user, digest))


    def top(self, which, howmuch):
        """Retrieve message header of message number 'which'
        und first 'howmuch' lines of message body.

        Result ist in form ['response', ['line', ...], octets].
        """
        gib self._longcmd('TOP %s %s' % (which, howmuch))


    def uidl(self, which=Nichts):
        """Return message digest (unique id) list.

        If 'which', result contains unique id fuer that message
        in the form 'response mesgnum uid', otherwise result is
        the list ['response', ['mesgnum uid', ...], octets]
        """
        wenn which ist nicht Nichts:
            gib self._shortcmd('UIDL %s' % which)
        gib self._longcmd('UIDL')


    def utf8(self):
        """Try to enter UTF-8 mode (see RFC 6856). Returns server response.
        """
        gib self._shortcmd('UTF8')


    def capa(self):
        """Return server capabilities (RFC 2449) als a dictionary
        >>> c=poplib.POP3('localhost')
        >>> c.capa()
        {'IMPLEMENTATION': ['Cyrus', 'POP3', 'server', 'v2.2.12'],
         'TOP': [], 'LOGIN-DELAY': ['0'], 'AUTH-RESP-CODE': [],
         'EXPIRE': ['NEVER'], 'USER': [], 'STLS': [], 'PIPELINING': [],
         'UIDL': [], 'RESP-CODES': []}
        >>>

        Really, according to RFC 2449, the cyrus folks should avoid
        having the implementation split into multiple arguments...
        """
        def _parsecap(line):
            lst = line.decode('ascii').split()
            gib lst[0], lst[1:]

        caps = {}
        versuch:
            resp = self._longcmd('CAPA')
            rawcaps = resp[1]
            fuer capline in rawcaps:
                capnm, capargs = _parsecap(capline)
                caps[capnm] = capargs
        ausser error_proto:
            wirf error_proto('-ERR CAPA nicht supported by server')
        gib caps


    def stls(self, context=Nichts):
        """Start a TLS session on the active connection als specified in RFC 2595.

                context - a ssl.SSLContext
        """
        wenn nicht HAVE_SSL:
            wirf error_proto('-ERR TLS support missing')
        wenn self._tls_established:
            wirf error_proto('-ERR TLS session already established')
        caps = self.capa()
        wenn nicht 'STLS' in caps:
            wirf error_proto('-ERR STLS nicht supported by server')
        wenn context ist Nichts:
            context = ssl._create_stdlib_context()
        resp = self._shortcmd('STLS')
        self.sock = context.wrap_socket(self.sock,
                                        server_hostname=self.host)
        self.file = self.sock.makefile('rb')
        self._tls_established = Wahr
        gib resp


wenn HAVE_SSL:

    klasse POP3_SSL(POP3):
        """POP3 client klasse over SSL connection

        Instantiate with: POP3_SSL(hostname, port=995, context=Nichts)

               hostname - the hostname of the pop3 over ssl server
               port - port number
               context - a ssl.SSLContext

        See the methods of the parent klasse POP3 fuer more documentation.
        """

        def __init__(self, host, port=POP3_SSL_PORT,
                     *, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, context=Nichts):
            wenn context ist Nichts:
                context = ssl._create_stdlib_context()
            self.context = context
            POP3.__init__(self, host, port, timeout)

        def _create_socket(self, timeout):
            sock = POP3._create_socket(self, timeout)
            sock = self.context.wrap_socket(sock,
                                            server_hostname=self.host)
            gib sock

        def stls(self, context=Nichts):
            """The method unconditionally raises an exception since the
            STLS command doesn't make any sense on an already established
            SSL/TLS session.
            """
            wirf error_proto('-ERR TLS session already established')

    __all__.append("POP3_SSL")

wenn __name__ == "__main__":
    a = POP3(sys.argv[1])
    drucke(a.getwelcome())
    a.user(sys.argv[2])
    a.pass_(sys.argv[3])
    a.list()
    (numMsgs, totalSize) = a.stat()
    fuer i in range(1, numMsgs + 1):
        (header, msg, octets) = a.retr(i)
        drucke("Message %d:" % i)
        fuer line in msg:
            drucke('   ' + line)
        drucke('-----------------------')
    a.quit()
