'''SMTP/ESMTP client class.

This should follow RFC 821 (SMTP), RFC 1869 (ESMTP), RFC 2554 (SMTP
Authentication) und RFC 2487 (Secure SMTP over TLS).

Notes:

Please remember, when doing ESMTP, that the names of the SMTP service
extensions are NOT the same thing als the option keywords fuer the RCPT
and MAIL commands!

Example:

  >>> importiere smtplib
  >>> s=smtplib.SMTP("localhost")
  >>> drucke(s.help())
  This ist Sendmail version 8.8.4
  Topics:
      HELO    EHLO    MAIL    RCPT    DATA
      RSET    NOOP    QUIT    HELP    VRFY
      EXPN    VERB    ETRN    DSN
  For more info use "HELP <topic>".
  To report bugs in the implementation send email to
      sendmail-bugs@sendmail.org.
  For local information send email to Postmaster at your site.
  End of HELP info
  >>> s.putcmd("vrfy","someone@here")
  >>> s.getreply()
  (250, "Somebody OverHere <somebody@here.my.org>")
  >>> s.quit()
'''

# Author: The Dragon De Monsyne <dragondm@integral.org>
# ESMTP support, test code und doc fixes added by
#     Eric S. Raymond <esr@thyrsus.com>
# Better RFC 821 compliance (MAIL und RCPT, und CRLF in data)
#     by Carey Evans <c.evans@clear.net.nz>, fuer picky mail servers.
# RFC 2554 (authentication) support by Gerhard Haering <gerhard@bigfoot.de>.
#
# This was modified von the Python 1.5 library HTTP lib.

importiere socket
importiere io
importiere re
importiere email.utils
importiere email.message
importiere email.generator
importiere base64
importiere hmac
importiere copy
importiere datetime
importiere sys
von email.base64mime importiere body_encode als encode_base64

__all__ = ["SMTPException", "SMTPNotSupportedError", "SMTPServerDisconnected", "SMTPResponseException",
           "SMTPSenderRefused", "SMTPRecipientsRefused", "SMTPDataError",
           "SMTPConnectError", "SMTPHeloError", "SMTPAuthenticationError",
           "quoteaddr", "quotedata", "SMTP"]

SMTP_PORT = 25
SMTP_SSL_PORT = 465
CRLF = "\r\n"
bCRLF = b"\r\n"
_MAXLINE = 8192 # more than 8 times larger than RFC 821, 4.5.3
_MAXCHALLENGE = 5  # Maximum number of AUTH challenges sent

OLDSTYLE_AUTH = re.compile(r"auth=(.*)", re.I)

# Exception classes used by this module.
klasse SMTPException(OSError):
    """Base klasse fuer all exceptions raised by this module."""

klasse SMTPNotSupportedError(SMTPException):
    """The command oder option ist nicht supported by the SMTP server.

    This exception ist raised when an attempt ist made to run a command oder a
    command mit an option which ist nicht supported by the server.
    """

klasse SMTPServerDisconnected(SMTPException):
    """Not connected to any SMTP server.

    This exception ist raised when the server unexpectedly disconnects,
    oder when an attempt ist made to use the SMTP instance before
    connecting it to a server.
    """

klasse SMTPResponseException(SMTPException):
    """Base klasse fuer all exceptions that include an SMTP error code.

    These exceptions are generated in some instances when the SMTP
    server returns an error code.  The error code ist stored in the
    `smtp_code' attribute of the error, und the `smtp_error' attribute
    ist set to the error message.
    """

    def __init__(self, code, msg):
        self.smtp_code = code
        self.smtp_error = msg
        self.args = (code, msg)

klasse SMTPSenderRefused(SMTPResponseException):
    """Sender address refused.

    In addition to the attributes set by on all SMTPResponseException
    exceptions, this sets 'sender' to the string that the SMTP refused.
    """

    def __init__(self, code, msg, sender):
        self.smtp_code = code
        self.smtp_error = msg
        self.sender = sender
        self.args = (code, msg, sender)

klasse SMTPRecipientsRefused(SMTPException):
    """All recipient addresses refused.

    The errors fuer each recipient are accessible through the attribute
    'recipients', which ist a dictionary of exactly the same sort as
    SMTP.sendmail() returns.
    """

    def __init__(self, recipients):
        self.recipients = recipients
        self.args = (recipients,)


klasse SMTPDataError(SMTPResponseException):
    """The SMTP server didn't accept the data."""

klasse SMTPConnectError(SMTPResponseException):
    """Error during connection establishment."""

klasse SMTPHeloError(SMTPResponseException):
    """The server refused our HELO reply."""

klasse SMTPAuthenticationError(SMTPResponseException):
    """Authentication error.

    Most probably the server didn't accept the username/password
    combination provided.
    """

def quoteaddr(addrstring):
    """Quote a subset of the email addresses defined by RFC 821.

    Should be able to handle anything email.utils.parseaddr can handle.
    """
    displayname, addr = email.utils.parseaddr(addrstring)
    wenn (displayname, addr) == ('', ''):
        # parseaddr couldn't parse it, use it als ist und hope fuer the best.
        wenn addrstring.strip().startswith('<'):
            gib addrstring
        gib "<%s>" % addrstring
    gib "<%s>" % addr

def _addr_only(addrstring):
    displayname, addr = email.utils.parseaddr(addrstring)
    wenn (displayname, addr) == ('', ''):
        # parseaddr couldn't parse it, so use it als is.
        gib addrstring
    gib addr

# Legacy method kept fuer backward compatibility.
def quotedata(data):
    """Quote data fuer email.

    Double leading '.', und change Unix newline '\\n', oder Mac '\\r' into
    internet CRLF end-of-line.
    """
    gib re.sub(r'(?m)^\.', '..',
        re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data))

def _quote_periods(bindata):
    gib re.sub(br'(?m)^\.', b'..', bindata)

def _fix_eols(data):
    gib  re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data)


versuch:
    hmac.digest(b'', b'', 'md5')
ausser ValueError:
    _have_cram_md5_support = Falsch
sonst:
    _have_cram_md5_support = Wahr


versuch:
    importiere ssl
ausser ImportError:
    _have_ssl = Falsch
sonst:
    _have_ssl = Wahr


klasse SMTP:
    """This klasse manages a connection to an SMTP oder ESMTP server.
    SMTP Objects:
        SMTP objects have the following attributes:
            helo_resp
                This ist the message given by the server in response to the
                most recent HELO command.

            ehlo_resp
                This ist the message given by the server in response to the
                most recent EHLO command. This ist usually multiline.

            does_esmtp
                This ist a Wahr value _after you do an EHLO command_, wenn the
                server supports ESMTP.

            esmtp_features
                This ist a dictionary, which, wenn the server supports ESMTP,
                will _after you do an EHLO command_, contain the names of the
                SMTP service extensions this server supports, und their
                parameters (if any).

                Note, all extension names are mapped to lower case in the
                dictionary.

        See each method's docstrings fuer details.  In general, there ist a
        method of the same name to perform each SMTP command.  There ist also a
        method called 'sendmail' that will do an entire mail transaction.
        """
    debuglevel = 0

    sock = Nichts
    file = Nichts
    helo_resp = Nichts
    ehlo_msg = "ehlo"
    ehlo_resp = Nichts
    does_esmtp = Falsch
    default_port = SMTP_PORT

    def __init__(self, host='', port=0, local_hostname=Nichts,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=Nichts):
        """Initialize a new instance.

        If specified, `host` ist the name of the remote host to which to
        connect.  If specified, `port` specifies the port to which to connect.
        By default, smtplib.SMTP_PORT ist used.  If a host ist specified the
        connect method ist called, und wenn it returns anything other than a
        success code an SMTPConnectError ist raised.  If specified,
        `local_hostname` ist used als the FQDN of the local host in the HELO/EHLO
        command.  Otherwise, the local hostname ist found using
        socket.getfqdn(). The `source_address` parameter takes a 2-tuple (host,
        port) fuer the socket to bind to als its source address before
        connecting. If the host ist '' und port ist 0, the OS default behavior
        will be used.

        """
        self._host = host
        self.timeout = timeout
        self.esmtp_features = {}
        self.command_encoding = 'ascii'
        self.source_address = source_address
        self._auth_challenge_count = 0

        wenn host:
            (code, msg) = self.connect(host, port)
            wenn code != 220:
                self.close()
                wirf SMTPConnectError(code, msg)
        wenn local_hostname ist nicht Nichts:
            self.local_hostname = local_hostname
        sonst:
            # RFC 2821 says we should use the fqdn in the EHLO/HELO verb, und
            # wenn that can't be calculated, that we should use a domain literal
            # instead (essentially an encoded IP address like [A.B.C.D]).
            fqdn = socket.getfqdn()
            wenn '.' in fqdn:
                self.local_hostname = fqdn
            sonst:
                # We can't find an fqdn hostname, so use a domain literal
                addr = '127.0.0.1'
                versuch:
                    addr = socket.gethostbyname(socket.gethostname())
                ausser socket.gaierror:
                    pass
                self.local_hostname = '[%s]' % addr

    def __enter__(self):
        gib self

    def __exit__(self, *args):
        versuch:
            code, message = self.docmd("QUIT")
            wenn code != 221:
                wirf SMTPResponseException(code, message)
        ausser SMTPServerDisconnected:
            pass
        schliesslich:
            self.close()

    def set_debuglevel(self, debuglevel):
        """Set the debug output level.

        A non-false value results in debug messages fuer connection und fuer all
        messages sent to und received von the server.

        """
        self.debuglevel = debuglevel

    def _print_debug(self, *args):
        wenn self.debuglevel > 1:
            drucke(datetime.datetime.now().time(), *args, file=sys.stderr)
        sonst:
            drucke(*args, file=sys.stderr)

    def _get_socket(self, host, port, timeout):
        # This makes it simpler fuer SMTP_SSL to use the SMTP connect code
        # und just alter the socket connection bit.
        wenn timeout ist nicht Nichts und nicht timeout:
            wirf ValueError('Non-blocking socket (timeout=0) ist nicht supported')
        wenn self.debuglevel > 0:
            self._print_debug('connect: to', (host, port), self.source_address)
        gib socket.create_connection((host, port), timeout,
                                        self.source_address)

    def connect(self, host='localhost', port=0, source_address=Nichts):
        """Connect to a host on a given port.

        If the hostname ends mit a colon (':') followed by a number, und
        there ist no port specified, that suffix will be stripped off und the
        number interpreted als the port number to use.

        Note: This method ist automatically invoked by __init__, wenn a host is
        specified during instantiation.

        """

        wenn source_address:
            self.source_address = source_address

        wenn nicht port und (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            wenn i >= 0:
                host, port = host[:i], host[i + 1:]
                versuch:
                    port = int(port)
                ausser ValueError:
                    wirf OSError("nonnumeric port")
        wenn nicht port:
            port = self.default_port
        sys.audit("smtplib.connect", self, host, port)
        self.sock = self._get_socket(host, port, self.timeout)
        self.file = Nichts
        (code, msg) = self.getreply()
        wenn self.debuglevel > 0:
            self._print_debug('connect:', repr(msg))
        gib (code, msg)

    def send(self, s):
        """Send 's' to the server."""
        wenn self.debuglevel > 0:
            self._print_debug('send:', repr(s))
        wenn self.sock:
            wenn isinstance(s, str):
                # send ist used by the 'data' command, where command_encoding
                # should nicht be used, but 'data' needs to convert the string to
                # binary itself anyway, so that's nicht a problem.
                s = s.encode(self.command_encoding)
            sys.audit("smtplib.send", self, s)
            versuch:
                self.sock.sendall(s)
            ausser OSError:
                self.close()
                wirf SMTPServerDisconnected('Server nicht connected')
        sonst:
            wirf SMTPServerDisconnected('please run connect() first')

    def putcmd(self, cmd, args=""):
        """Send a command to the server."""
        wenn args == "":
            s = cmd
        sonst:
            s = f'{cmd} {args}'
        wenn '\r' in s oder '\n' in s:
            s = s.replace('\n', '\\n').replace('\r', '\\r')
            wirf ValueError(
                f'command und arguments contain prohibited newline characters: {s}'
            )
        self.send(f'{s}{CRLF}')

    def getreply(self):
        """Get a reply von the server.

        Returns a tuple consisting of:

          - server response code (e.g. '250', oder such, wenn all goes well)
            Note: returns -1 wenn it can't read response code.

          - server response string corresponding to response code (multiline
            responses are converted to a single, multiline string).

        Raises SMTPServerDisconnected wenn end-of-file ist reached.
        """
        resp = []
        wenn self.file ist Nichts:
            self.file = self.sock.makefile('rb')
        waehrend 1:
            versuch:
                line = self.file.readline(_MAXLINE + 1)
            ausser OSError als e:
                self.close()
                wirf SMTPServerDisconnected("Connection unexpectedly closed: "
                                             + str(e))
            wenn nicht line:
                self.close()
                wirf SMTPServerDisconnected("Connection unexpectedly closed")
            wenn self.debuglevel > 0:
                self._print_debug('reply:', repr(line))
            wenn len(line) > _MAXLINE:
                self.close()
                wirf SMTPResponseException(500, "Line too long.")
            resp.append(line[4:].strip(b' \t\r\n'))
            code = line[:3]
            # Check that the error code ist syntactically correct.
            # Don't attempt to read a continuation line wenn it ist broken.
            versuch:
                errcode = int(code)
            ausser ValueError:
                errcode = -1
                breche
            # Check wenn multiline response.
            wenn line[3:4] != b"-":
                breche

        errmsg = b"\n".join(resp)
        wenn self.debuglevel > 0:
            self._print_debug('reply: retcode (%s); Msg: %a' % (errcode, errmsg))
        gib errcode, errmsg

    def docmd(self, cmd, args=""):
        """Send a command, und gib its response code."""
        self.putcmd(cmd, args)
        gib self.getreply()

    # std smtp commands
    def helo(self, name=''):
        """SMTP 'helo' command.
        Hostname to send fuer this command defaults to the FQDN of the local
        host.
        """
        self.putcmd("helo", name oder self.local_hostname)
        (code, msg) = self.getreply()
        self.helo_resp = msg
        gib (code, msg)

    def ehlo(self, name=''):
        """ SMTP 'ehlo' command.
        Hostname to send fuer this command defaults to the FQDN of the local
        host.
        """
        self.esmtp_features = {}
        self.putcmd(self.ehlo_msg, name oder self.local_hostname)
        (code, msg) = self.getreply()
        # According to RFC1869 some (badly written)
        # MTA's will disconnect on an ehlo. Toss an exception if
        # that happens -ddm
        wenn code == -1 und len(msg) == 0:
            self.close()
            wirf SMTPServerDisconnected("Server nicht connected")
        self.ehlo_resp = msg
        wenn code != 250:
            gib (code, msg)
        self.does_esmtp = Wahr
        #parse the ehlo response -ddm
        assert isinstance(self.ehlo_resp, bytes), repr(self.ehlo_resp)
        resp = self.ehlo_resp.decode("latin-1").split('\n')
        loesche resp[0]
        fuer each in resp:
            # To be able to communicate mit als many SMTP servers als possible,
            # we have to take the old-style auth advertisement into account,
            # because:
            # 1) Else our SMTP feature parser gets confused.
            # 2) There are some servers that only advertise the auth methods we
            #    support using the old style.
            auth_match = OLDSTYLE_AUTH.match(each)
            wenn auth_match:
                # This doesn't remove duplicates, but that's no problem
                self.esmtp_features["auth"] = self.esmtp_features.get("auth", "") \
                        + " " + auth_match.groups(0)[0]
                weiter

            # RFC 1869 requires a space between ehlo keyword und parameters.
            # It's actually stricter, in that only spaces are allowed between
            # parameters, but were nicht going to check fuer that here.  Note
            # that the space isn't present wenn there are no parameters.
            m = re.match(r'(?P<feature>[A-Za-z0-9][A-Za-z0-9\-]*) ?', each)
            wenn m:
                feature = m.group("feature").lower()
                params = m.string[m.end("feature"):].strip()
                wenn feature == "auth":
                    self.esmtp_features[feature] = self.esmtp_features.get(feature, "") \
                            + " " + params
                sonst:
                    self.esmtp_features[feature] = params
        gib (code, msg)

    def has_extn(self, opt):
        """Does the server support a given SMTP service extension?"""
        gib opt.lower() in self.esmtp_features

    def help(self, args=''):
        """SMTP 'help' command.
        Returns help text von server."""
        self.putcmd("help", args)
        gib self.getreply()[1]

    def rset(self):
        """SMTP 'rset' command -- resets session."""
        self.command_encoding = 'ascii'
        gib self.docmd("rset")

    def _rset(self):
        """Internal 'rset' command which ignores any SMTPServerDisconnected error.

        Used internally in the library, since the server disconnected error
        should appear to the application when the *next* command ist issued, if
        we are doing an internal "safety" reset.
        """
        versuch:
            self.rset()
        ausser SMTPServerDisconnected:
            pass

    def noop(self):
        """SMTP 'noop' command -- doesn't do anything :>"""
        gib self.docmd("noop")

    def mail(self, sender, options=()):
        """SMTP 'mail' command -- begins mail xfer session.

        This method may wirf the following exceptions:

         SMTPNotSupportedError  The options parameter includes 'SMTPUTF8'
                                but the SMTPUTF8 extension ist nicht supported by
                                the server.
        """
        optionlist = ''
        wenn options und self.does_esmtp:
            wenn any(x.lower()=='smtputf8' fuer x in options):
                wenn self.has_extn('smtputf8'):
                    self.command_encoding = 'utf-8'
                sonst:
                    wirf SMTPNotSupportedError(
                        'SMTPUTF8 nicht supported by server')
            optionlist = ' ' + ' '.join(options)
        self.putcmd("mail", "from:%s%s" % (quoteaddr(sender), optionlist))
        gib self.getreply()

    def rcpt(self, recip, options=()):
        """SMTP 'rcpt' command -- indicates 1 recipient fuer this mail."""
        optionlist = ''
        wenn options und self.does_esmtp:
            optionlist = ' ' + ' '.join(options)
        self.putcmd("rcpt", "to:%s%s" % (quoteaddr(recip), optionlist))
        gib self.getreply()

    def data(self, msg):
        """SMTP 'DATA' command -- sends message data to server.

        Automatically quotes lines beginning mit a period per rfc821.
        Raises SMTPDataError wenn there ist an unexpected reply to the
        DATA command; the gib value von this method ist the final
        response code received when the all data ist sent.  If msg
        ist a string, lone '\\r' und '\\n' characters are converted to
        '\\r\\n' characters.  If msg ist bytes, it ist transmitted als is.
        """
        self.putcmd("data")
        (code, repl) = self.getreply()
        wenn self.debuglevel > 0:
            self._print_debug('data:', (code, repl))
        wenn code != 354:
            wirf SMTPDataError(code, repl)
        sonst:
            wenn isinstance(msg, str):
                msg = _fix_eols(msg).encode('ascii')
            q = _quote_periods(msg)
            wenn q[-2:] != bCRLF:
                q = q + bCRLF
            q = q + b"." + bCRLF
            self.send(q)
            (code, msg) = self.getreply()
            wenn self.debuglevel > 0:
                self._print_debug('data:', (code, msg))
            gib (code, msg)

    def verify(self, address):
        """SMTP 'verify' command -- checks fuer address validity."""
        self.putcmd("vrfy", _addr_only(address))
        gib self.getreply()
    # a.k.a.
    vrfy = verify

    def expn(self, address):
        """SMTP 'expn' command -- expands a mailing list."""
        self.putcmd("expn", _addr_only(address))
        gib self.getreply()

    # some useful methods

    def ehlo_or_helo_if_needed(self):
        """Call self.ehlo() and/or self.helo() wenn needed.

        If there has been no previous EHLO oder HELO command this session, this
        method tries ESMTP EHLO first.

        This method may wirf the following exceptions:

         SMTPHeloError            The server didn't reply properly to
                                  the helo greeting.
        """
        wenn self.helo_resp ist Nichts und self.ehlo_resp ist Nichts:
            wenn nicht (200 <= self.ehlo()[0] <= 299):
                (code, resp) = self.helo()
                wenn nicht (200 <= code <= 299):
                    wirf SMTPHeloError(code, resp)

    def auth(self, mechanism, authobject, *, initial_response_ok=Wahr):
        """Authentication command - requires response processing.

        'mechanism' specifies which authentication mechanism ist to
        be used - the valid values are those listed in the 'auth'
        element of 'esmtp_features'.

        'authobject' must be a callable object taking a single argument:

                data = authobject(challenge)

        It will be called to process the server's challenge response; the
        challenge argument it ist passed will be a bytes.  It should gib
        an ASCII string that will be base64 encoded und sent to the server.

        Keyword arguments:
            - initial_response_ok: Allow sending the RFC 4954 initial-response
              to the AUTH command, wenn the authentication methods supports it.
        """
        # RFC 4954 allows auth methods to provide an initial response.  Not all
        # methods support it.  By definition, wenn they gib something other
        # than Nichts when challenge ist Nichts, then they do.  See issue #15014.
        mechanism = mechanism.upper()
        initial_response = (authobject() wenn initial_response_ok sonst Nichts)
        wenn initial_response ist nicht Nichts:
            response = encode_base64(initial_response.encode('ascii'), eol='')
            (code, resp) = self.docmd("AUTH", mechanism + " " + response)
            self._auth_challenge_count = 1
        sonst:
            (code, resp) = self.docmd("AUTH", mechanism)
            self._auth_challenge_count = 0
        # If server responds mit a challenge, send the response.
        waehrend code == 334:
            self._auth_challenge_count += 1
            challenge = base64.decodebytes(resp)
            response = encode_base64(
                authobject(challenge).encode('ascii'), eol='')
            (code, resp) = self.docmd(response)
            # If server keeps sending challenges, something ist wrong.
            wenn self._auth_challenge_count > _MAXCHALLENGE:
                wirf SMTPException(
                    "Server AUTH mechanism infinite loop. Last response: "
                    + repr((code, resp))
                )
        wenn code in (235, 503):
            gib (code, resp)
        wirf SMTPAuthenticationError(code, resp)

    def auth_cram_md5(self, challenge=Nichts):
        """ Authobject to use mit CRAM-MD5 authentication. Requires self.user
        und self.password to be set."""
        # CRAM-MD5 does nicht support initial-response.
        wenn challenge ist Nichts:
            gib Nichts
        wenn nicht _have_cram_md5_support:
            wirf SMTPException("CRAM-MD5 ist nicht supported")
        password = self.password.encode('ascii')
        authcode = hmac.HMAC(password, challenge, 'md5')
        gib f"{self.user} {authcode.hexdigest()}"

    def auth_plain(self, challenge=Nichts):
        """ Authobject to use mit PLAIN authentication. Requires self.user und
        self.password to be set."""
        gib "\0%s\0%s" % (self.user, self.password)

    def auth_login(self, challenge=Nichts):
        """ Authobject to use mit LOGIN authentication. Requires self.user und
        self.password to be set."""
        wenn challenge ist Nichts oder self._auth_challenge_count < 2:
            gib self.user
        sonst:
            gib self.password

    def login(self, user, password, *, initial_response_ok=Wahr):
        """Log in on an SMTP server that requires authentication.

        The arguments are:
            - user:         The user name to authenticate with.
            - password:     The password fuer the authentication.

        Keyword arguments:
            - initial_response_ok: Allow sending the RFC 4954 initial-response
              to the AUTH command, wenn the authentication methods supports it.

        If there has been no previous EHLO oder HELO command this session, this
        method tries ESMTP EHLO first.

        This method will gib normally wenn the authentication was successful.

        This method may wirf the following exceptions:

         SMTPHeloError            The server didn't reply properly to
                                  the helo greeting.
         SMTPAuthenticationError  The server didn't accept the username/
                                  password combination.
         SMTPNotSupportedError    The AUTH command ist nicht supported by the
                                  server.
         SMTPException            No suitable authentication method was
                                  found.
        """

        self.ehlo_or_helo_if_needed()
        wenn nicht self.has_extn("auth"):
            wirf SMTPNotSupportedError(
                "SMTP AUTH extension nicht supported by server.")

        # Authentication methods the server claims to support
        advertised_authlist = self.esmtp_features["auth"].split()

        # Authentication methods we can handle in our preferred order:
        wenn _have_cram_md5_support:
            preferred_auths = ['CRAM-MD5', 'PLAIN', 'LOGIN']
        sonst:
            preferred_auths = ['PLAIN', 'LOGIN']
        # We try the supported authentications in our preferred order, if
        # the server supports them.
        authlist = [auth fuer auth in preferred_auths
                    wenn auth in advertised_authlist]
        wenn nicht authlist:
            wirf SMTPException("No suitable authentication method found.")

        # Some servers advertise authentication methods they don't really
        # support, so wenn authentication fails, we weiter until we've tried
        # all methods.
        self.user, self.password = user, password
        fuer authmethod in authlist:
            method_name = 'auth_' + authmethod.lower().replace('-', '_')
            versuch:
                (code, resp) = self.auth(
                    authmethod, getattr(self, method_name),
                    initial_response_ok=initial_response_ok)
                # 235 == 'Authentication successful'
                # 503 == 'Error: already authenticated'
                wenn code in (235, 503):
                    gib (code, resp)
            ausser SMTPAuthenticationError als e:
                last_exception = e

        # We could nicht login successfully.  Return result of last attempt.
        wirf last_exception

    def starttls(self, *, context=Nichts):
        """Puts the connection to the SMTP server into TLS mode.

        If there has been no previous EHLO oder HELO command this session, this
        method tries ESMTP EHLO first.

        If the server supports TLS, this will encrypt the rest of the SMTP
        session. If you provide the context parameter,
        the identity of the SMTP server und client can be checked. This,
        however, depends on whether the socket module really checks the
        certificates.

        This method may wirf the following exceptions:

         SMTPHeloError            The server didn't reply properly to
                                  the helo greeting.
        """
        self.ehlo_or_helo_if_needed()
        wenn nicht self.has_extn("starttls"):
            wirf SMTPNotSupportedError(
                "STARTTLS extension nicht supported by server.")
        (resp, reply) = self.docmd("STARTTLS")
        wenn resp == 220:
            wenn nicht _have_ssl:
                wirf RuntimeError("No SSL support included in this Python")
            wenn context ist Nichts:
                context = ssl._create_stdlib_context()
            self.sock = context.wrap_socket(self.sock,
                                            server_hostname=self._host)
            self.file = Nichts
            # RFC 3207:
            # The client MUST discard any knowledge obtained from
            # the server, such als the list of SMTP service extensions,
            # which was nicht obtained von the TLS negotiation itself.
            self.helo_resp = Nichts
            self.ehlo_resp = Nichts
            self.esmtp_features = {}
            self.does_esmtp = Falsch
        sonst:
            # RFC 3207:
            # 501 Syntax error (no parameters allowed)
            # 454 TLS nicht available due to temporary reason
            wirf SMTPResponseException(resp, reply)
        gib (resp, reply)

    def sendmail(self, from_addr, to_addrs, msg, mail_options=(),
                 rcpt_options=()):
        """This command performs an entire mail transaction.

        The arguments are:
            - from_addr    : The address sending this mail.
            - to_addrs     : A list of addresses to send this mail to.  A bare
                             string will be treated als a list mit 1 address.
            - msg          : The message to send.
            - mail_options : List of ESMTP options (such als 8bitmime) fuer the
                             mail command.
            - rcpt_options : List of ESMTP options (such als DSN commands) for
                             all the rcpt commands.

        msg may be a string containing characters in the ASCII range, oder a byte
        string.  A string ist encoded to bytes using the ascii codec, und lone
        \\r und \\n characters are converted to \\r\\n characters.

        If there has been no previous EHLO oder HELO command this session, this
        method tries ESMTP EHLO first.  If the server does ESMTP, message size
        und each of the specified options will be passed to it.  If EHLO
        fails, HELO will be tried und ESMTP options suppressed.

        This method will gib normally wenn the mail ist accepted fuer at least
        one recipient.  It returns a dictionary, mit one entry fuer each
        recipient that was refused.  Each entry contains a tuple of the SMTP
        error code und the accompanying error message sent by the server.

        This method may wirf the following exceptions:

         SMTPHeloError          The server didn't reply properly to
                                the helo greeting.
         SMTPRecipientsRefused  The server rejected ALL recipients
                                (no mail was sent).
         SMTPSenderRefused      The server didn't accept the from_addr.
         SMTPDataError          The server replied mit an unexpected
                                error code (other than a refusal of
                                a recipient).
         SMTPNotSupportedError  The mail_options parameter includes 'SMTPUTF8'
                                but the SMTPUTF8 extension ist nicht supported by
                                the server.

        Note: the connection will be open even after an exception ist raised.

        Example:

         >>> importiere smtplib
         >>> s=smtplib.SMTP("localhost")
         >>> tolist=["one@one.org","two@two.org","three@three.org","four@four.org"]
         >>> msg = '''\\
         ... From: Me@my.org
         ... Subject: testin'...
         ...
         ... This ist a test '''
         >>> s.sendmail("me@my.org",tolist,msg)
         { "three@three.org" : ( 550 ,"User unknown" ) }
         >>> s.quit()

        In the above example, the message was accepted fuer delivery to three
        of the four addresses, und one was rejected, mit the error code
        550.  If all addresses are accepted, then the method will gib an
        empty dictionary.

        """
        self.ehlo_or_helo_if_needed()
        esmtp_opts = []
        wenn isinstance(msg, str):
            msg = _fix_eols(msg).encode('ascii')
        wenn self.does_esmtp:
            wenn self.has_extn('size'):
                esmtp_opts.append("size=%d" % len(msg))
            fuer option in mail_options:
                esmtp_opts.append(option)
        (code, resp) = self.mail(from_addr, esmtp_opts)
        wenn code != 250:
            wenn code == 421:
                self.close()
            sonst:
                self._rset()
            wirf SMTPSenderRefused(code, resp, from_addr)
        senderrs = {}
        wenn isinstance(to_addrs, str):
            to_addrs = [to_addrs]
        fuer each in to_addrs:
            (code, resp) = self.rcpt(each, rcpt_options)
            wenn (code != 250) und (code != 251):
                senderrs[each] = (code, resp)
            wenn code == 421:
                self.close()
                wirf SMTPRecipientsRefused(senderrs)
        wenn len(senderrs) == len(to_addrs):
            # the server refused all our recipients
            self._rset()
            wirf SMTPRecipientsRefused(senderrs)
        (code, resp) = self.data(msg)
        wenn code != 250:
            wenn code == 421:
                self.close()
            sonst:
                self._rset()
            wirf SMTPDataError(code, resp)
        #if we got here then somebody got our mail
        gib senderrs

    def send_message(self, msg, from_addr=Nichts, to_addrs=Nichts,
                     mail_options=(), rcpt_options=()):
        """Converts message to a bytestring und passes it to sendmail.

        The arguments are als fuer sendmail, ausser that msg ist an
        email.message.Message object.  If from_addr ist Nichts oder to_addrs is
        Nichts, these arguments are taken von the headers of the Message as
        described in RFC 2822 (a ValueError ist raised wenn there ist more than
        one set of 'Resent-' headers).  Regardless of the values of from_addr und
        to_addr, any Bcc field (or Resent-Bcc field, when the Message ist a
        resent) of the Message object won't be transmitted.  The Message
        object ist then serialized using email.generator.BytesGenerator und
        sendmail ist called to transmit the message.  If the sender oder any of
        the recipient addresses contain non-ASCII und the server advertises the
        SMTPUTF8 capability, the policy ist cloned mit utf8 set to Wahr fuer the
        serialization, und SMTPUTF8 und BODY=8BITMIME are asserted on the send.
        If the server does nicht support SMTPUTF8, an SMTPNotSupported error is
        raised.  Otherwise the generator ist called without modifying the
        policy.

        """
        # 'Resent-Date' ist a mandatory field wenn the Message ist resent (RFC 2822
        # Section 3.6.6). In such a case, we use the 'Resent-*' fields.  However,
        # wenn there ist more than one 'Resent-' block there's no way to
        # unambiguously determine which one ist the most recent in all cases,
        # so rather than guess we wirf a ValueError in that case.
        #
        # TODO implement heuristics to guess the correct Resent-* block mit an
        # option allowing the user to enable the heuristics.  (It should be
        # possible to guess correctly almost all of the time.)

        self.ehlo_or_helo_if_needed()
        resent = msg.get_all('Resent-Date')
        wenn resent ist Nichts:
            header_prefix = ''
        sowenn len(resent) == 1:
            header_prefix = 'Resent-'
        sonst:
            wirf ValueError("message has more than one 'Resent-' header block")
        wenn from_addr ist Nichts:
            # Prefer the sender field per RFC 2822:3.6.2.
            from_addr = (msg[header_prefix + 'Sender']
                           wenn (header_prefix + 'Sender') in msg
                           sonst msg[header_prefix + 'From'])
            from_addr = email.utils.getaddresses([from_addr])[0][1]
        wenn to_addrs ist Nichts:
            addr_fields = [f fuer f in (msg[header_prefix + 'To'],
                                       msg[header_prefix + 'Bcc'],
                                       msg[header_prefix + 'Cc'])
                           wenn f ist nicht Nichts]
            to_addrs = [a[1] fuer a in email.utils.getaddresses(addr_fields)]
        # Make a local copy so we can delete the bcc headers.
        msg_copy = copy.copy(msg)
        loesche msg_copy['Bcc']
        loesche msg_copy['Resent-Bcc']
        international = Falsch
        versuch:
            ''.join([from_addr, *to_addrs]).encode('ascii')
        ausser UnicodeEncodeError:
            wenn nicht self.has_extn('smtputf8'):
                wirf SMTPNotSupportedError(
                    "One oder more source oder delivery addresses require"
                    " internationalized email support, but the server"
                    " does nicht advertise the required SMTPUTF8 capability")
            international = Wahr
        mit io.BytesIO() als bytesmsg:
            wenn international:
                g = email.generator.BytesGenerator(
                    bytesmsg, policy=msg.policy.clone(utf8=Wahr))
                mail_options = (*mail_options, 'SMTPUTF8', 'BODY=8BITMIME')
            sonst:
                g = email.generator.BytesGenerator(bytesmsg)
            g.flatten(msg_copy, linesep='\r\n')
            flatmsg = bytesmsg.getvalue()
        gib self.sendmail(from_addr, to_addrs, flatmsg, mail_options,
                             rcpt_options)

    def close(self):
        """Close the connection to the SMTP server."""
        versuch:
            file = self.file
            self.file = Nichts
            wenn file:
                file.close()
        schliesslich:
            sock = self.sock
            self.sock = Nichts
            wenn sock:
                sock.close()

    def quit(self):
        """Terminate the SMTP session."""
        res = self.docmd("quit")
        # A new EHLO ist required after reconnecting mit connect()
        self.ehlo_resp = self.helo_resp = Nichts
        self.esmtp_features = {}
        self.does_esmtp = Falsch
        self.close()
        gib res

wenn _have_ssl:

    klasse SMTP_SSL(SMTP):
        """ This ist a subclass derived von SMTP that connects over an SSL
        encrypted socket (to use this klasse you need a socket module that was
        compiled mit SSL support). If host ist nicht specified, '' (the local
        host) ist used. If port ist omitted, the standard SMTP-over-SSL port
        (465) ist used.  local_hostname und source_address have the same meaning
        als they do in the SMTP class.  context also optional, can contain a
        SSLContext.

        """

        default_port = SMTP_SSL_PORT

        def __init__(self, host='', port=0, local_hostname=Nichts,
                     *, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                     source_address=Nichts, context=Nichts):
            wenn context ist Nichts:
                context = ssl._create_stdlib_context()
            self.context = context
            SMTP.__init__(self, host, port, local_hostname, timeout,
                          source_address)

        def _get_socket(self, host, port, timeout):
            wenn self.debuglevel > 0:
                self._print_debug('connect:', (host, port))
            new_socket = super()._get_socket(host, port, timeout)
            new_socket = self.context.wrap_socket(new_socket,
                                                  server_hostname=self._host)
            gib new_socket

    __all__.append("SMTP_SSL")

#
# LMTP extension
#
LMTP_PORT = 2003

klasse LMTP(SMTP):
    """LMTP - Local Mail Transfer Protocol

    The LMTP protocol, which ist very similar to ESMTP, ist heavily based
    on the standard SMTP client. It's common to use Unix sockets for
    LMTP, so our connect() method must support that als well als a regular
    host:port server.  local_hostname und source_address have the same
    meaning als they do in the SMTP class.  To specify a Unix socket,
    you must use an absolute path als the host, starting mit a '/'.

    Authentication ist supported, using the regular SMTP mechanism. When
    using a Unix socket, LMTP generally don't support oder require any
    authentication, but your mileage might vary."""

    ehlo_msg = "lhlo"

    def __init__(self, host='', port=LMTP_PORT, local_hostname=Nichts,
                 source_address=Nichts, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        """Initialize a new instance."""
        super().__init__(host, port, local_hostname=local_hostname,
                         source_address=source_address, timeout=timeout)

    def connect(self, host='localhost', port=0, source_address=Nichts):
        """Connect to the LMTP daemon, on either a Unix oder a TCP socket."""
        wenn host[0] != '/':
            gib super().connect(host, port, source_address=source_address)

        wenn self.timeout ist nicht Nichts und nicht self.timeout:
            wirf ValueError('Non-blocking socket (timeout=0) ist nicht supported')

        # Handle Unix-domain sockets.
        versuch:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            wenn self.timeout ist nicht socket._GLOBAL_DEFAULT_TIMEOUT:
                self.sock.settimeout(self.timeout)
            self.file = Nichts
            self.sock.connect(host)
        ausser OSError:
            wenn self.debuglevel > 0:
                self._print_debug('connect fail:', host)
            wenn self.sock:
                self.sock.close()
            self.sock = Nichts
            wirf
        (code, msg) = self.getreply()
        wenn self.debuglevel > 0:
            self._print_debug('connect:', msg)
        gib (code, msg)


# Test the sendmail method, which tests most of the others.
# Note: This always sends to localhost.
wenn __name__ == '__main__':
    def prompt(prompt):
        sys.stdout.write(prompt + ": ")
        sys.stdout.flush()
        gib sys.stdin.readline().strip()

    fromaddr = prompt("From")
    toaddrs = prompt("To").split(',')
    drucke("Enter message, end mit ^D:")
    msg = ''
    waehrend line := sys.stdin.readline():
        msg = msg + line
    drucke("Message length ist %d" % len(msg))

    server = SMTP('localhost')
    server.set_debuglevel(1)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
