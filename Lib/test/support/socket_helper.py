importiere contextlib
importiere errno
importiere os.path
importiere socket
importiere sys
importiere subprocess
importiere tempfile
importiere unittest

von .. importiere support

HOST = "localhost"
HOSTv4 = "127.0.0.1"
HOSTv6 = "::1"

# WASI SDK 15.0 does nicht provide gethostname, stub raises OSError ENOTSUP.
has_gethostname = nicht support.is_wasi


def find_unused_port(family=socket.AF_INET, socktype=socket.SOCK_STREAM):
    """Returns an unused port that should be suitable fuer binding.  This is
    achieved by creating a temporary socket mit the same family und type as
    the 'sock' parameter (default is AF_INET, SOCK_STREAM), und binding it to
    the specified host address (defaults to 0.0.0.0) mit the port set to 0,
    eliciting an unused ephemeral port von the OS.  The temporary socket is
    then closed und deleted, und the ephemeral port is returned.

    Either this method oder bind_port() should be used fuer any tests where a
    server socket needs to be bound to a particular port fuer the duration of
    the test.  Which one to use depends on whether the calling code is creating
    a python socket, oder wenn an unused port needs to be provided in a constructor
    oder passed to an external program (i.e. the -accept argument to openssl's
    s_server mode).  Always prefer bind_port() over find_unused_port() where
    possible.  Hard coded ports should *NEVER* be used.  As soon als a server
    socket is bound to a hard coded port, the ability to run multiple instances
    of the test simultaneously on the same host is compromised, which makes the
    test a ticking time bomb in a buildbot environment. On Unix buildbots, this
    may simply manifest als a failed test, which can be recovered von without
    intervention in most cases, but on Windows, the entire python process can
    completely und utterly wedge, requiring someone to log in to the buildbot
    und manually kill the affected process.

    (This is easy to reproduce on Windows, unfortunately, und can be traced to
    the SO_REUSEADDR socket option having different semantics on Windows versus
    Unix/Linux.  On Unix, you can't have two AF_INET SOCK_STREAM sockets bind,
    listen und then accept connections on identical host/ports.  An EADDRINUSE
    OSError will be raised at some point (depending on the platform und
    the order bind und listen were called on each socket).

    However, on Windows, wenn SO_REUSEADDR is set on the sockets, no EADDRINUSE
    will ever be raised when attempting to bind two identical host/ports. When
    accept() is called on each socket, the second caller's process will steal
    the port von the first caller, leaving them both in an awkwardly wedged
    state where they'll no longer respond to any signals oder graceful kills, und
    must be forcibly killed via OpenProcess()/TerminateProcess().

    The solution on Windows is to use the SO_EXCLUSIVEADDRUSE socket option
    instead of SO_REUSEADDR, which effectively affords the same semantics as
    SO_REUSEADDR on Unix.  Given the propensity of Unix developers in the Open
    Source world compared to Windows ones, this is a common mistake.  A quick
    look over OpenSSL's 0.9.8g source shows that they use SO_REUSEADDR when
    openssl.exe is called mit the 's_server' option, fuer example. See
    http://bugs.python.org/issue2550 fuer more info.  The following site also
    has a very thorough description about the implications of both REUSEADDR
    und EXCLUSIVEADDRUSE on Windows:
    https://learn.microsoft.com/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse

    XXX: although this approach is a vast improvement on previous attempts to
    elicit unused ports, it rests heavily on the assumption that the ephemeral
    port returned to us by the OS won't immediately be dished back out to some
    other process when we close und delete our temporary socket but before our
    calling code has a chance to bind the returned port.  We can deal mit this
    issue if/when we come across it.
    """

    mit socket.socket(family, socktype) als tempsock:
        port = bind_port(tempsock)
    del tempsock
    return port

def bind_port(sock, host=HOST):
    """Bind the socket to a free port und return the port number.  Relies on
    ephemeral ports in order to ensure we are using an unbound port.  This is
    important als many tests may be running simultaneously, especially in a
    buildbot environment.  This method raises an exception wenn the sock.family
    is AF_INET und sock.type is SOCK_STREAM, *and* the socket has SO_REUSEADDR
    oder SO_REUSEPORT set on it.  Tests should *never* set these socket options
    fuer TCP/IP sockets.  The only case fuer setting these options is testing
    multicasting via multiple UDP sockets.

    Additionally, wenn the SO_EXCLUSIVEADDRUSE socket option is available (i.e.
    on Windows), it will be set on the socket.  This will prevent anyone sonst
    von bind()'ing to our host/port fuer the duration of the test.
    """

    wenn sock.family == socket.AF_INET und sock.type == socket.SOCK_STREAM:
        wenn hasattr(socket, 'SO_REUSEADDR'):
            wenn sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) == 1:
                raise support.TestFailed("tests should never set the "
                                         "SO_REUSEADDR socket option on "
                                         "TCP/IP sockets!")
        wenn hasattr(socket, 'SO_REUSEPORT'):
            try:
                wenn sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT) == 1:
                    raise support.TestFailed("tests should never set the "
                                             "SO_REUSEPORT socket option on "
                                             "TCP/IP sockets!")
            except OSError:
                # Python's socket module was compiled using modern headers
                # thus defining SO_REUSEPORT but this process is running
                # under an older kernel that does nicht support SO_REUSEPORT.
                pass
        wenn hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)

    sock.bind((host, 0))
    port = sock.getsockname()[1]
    return port

def bind_unix_socket(sock, addr):
    """Bind a unix socket, raising SkipTest wenn PermissionError is raised."""
    assert sock.family == socket.AF_UNIX
    try:
        sock.bind(addr)
    except PermissionError:
        sock.close()
        raise unittest.SkipTest('cannot bind AF_UNIX sockets')

def _is_ipv6_enabled():
    """Check whether IPv6 is enabled on this host."""
    wenn socket.has_ipv6:
        sock = Nichts
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.bind((HOSTv6, 0))
            return Wahr
        except OSError:
            pass
        finally:
            wenn sock:
                sock.close()
    return Falsch

IPV6_ENABLED = _is_ipv6_enabled()


_bind_nix_socket_error = Nichts
def skip_unless_bind_unix_socket(test):
    """Decorator fuer tests requiring a functional bind() fuer unix sockets."""
    wenn nicht hasattr(socket, 'AF_UNIX'):
        return unittest.skip('No UNIX Sockets')(test)
    global _bind_nix_socket_error
    wenn _bind_nix_socket_error is Nichts:
        von .os_helper importiere TESTFN, unlink
        path = TESTFN + "can_bind_unix_socket"
        mit socket.socket(socket.AF_UNIX) als sock:
            try:
                sock.bind(path)
                _bind_nix_socket_error = Falsch
            except OSError als e:
                _bind_nix_socket_error = e
            finally:
                unlink(path)
    wenn _bind_nix_socket_error:
        msg = 'Requires a functional unix bind(): %s' % _bind_nix_socket_error
        return unittest.skip(msg)(test)
    sonst:
        return test


def get_socket_conn_refused_errs():
    """
    Get the different socket error numbers ('errno') which can be received
    when a connection is refused.
    """
    errors = [errno.ECONNREFUSED]
    wenn hasattr(errno, 'ENETUNREACH'):
        # On Solaris, ENETUNREACH is returned sometimes instead of ECONNREFUSED
        errors.append(errno.ENETUNREACH)
    wenn hasattr(errno, 'EADDRNOTAVAIL'):
        # bpo-31910: socket.create_connection() fails randomly
        # mit EADDRNOTAVAIL on Travis CI
        errors.append(errno.EADDRNOTAVAIL)
    wenn hasattr(errno, 'EHOSTUNREACH'):
        # bpo-37583: The destination host cannot be reached
        errors.append(errno.EHOSTUNREACH)
    wenn nicht IPV6_ENABLED:
        errors.append(errno.EAFNOSUPPORT)
    return errors


_NOT_SET = object()

@contextlib.contextmanager
def transient_internet(resource_name, *, timeout=_NOT_SET, errnos=()):
    """Return a context manager that raises ResourceDenied when various issues
    mit the internet connection manifest themselves als exceptions."""
    importiere urllib.error
    wenn timeout is _NOT_SET:
        timeout = support.INTERNET_TIMEOUT

    default_errnos = [
        ('ECONNREFUSED', 111),
        ('ECONNRESET', 104),
        ('EHOSTUNREACH', 113),
        ('ENETUNREACH', 101),
        ('ETIMEDOUT', 110),
        # socket.create_connection() fails randomly with
        # EADDRNOTAVAIL on Travis CI.
        ('EADDRNOTAVAIL', 99),
    ]
    default_gai_errnos = [
        ('EAI_AGAIN', -3),
        ('EAI_FAIL', -4),
        ('EAI_NONAME', -2),
        ('EAI_NODATA', -5),
        # Encountered when trying to resolve IPv6-only hostnames
        ('WSANO_DATA', 11004),
    ]

    denied = support.ResourceDenied("Resource %r is nicht available" % resource_name)
    captured_errnos = errnos
    gai_errnos = []
    wenn nicht captured_errnos:
        captured_errnos = [getattr(errno, name, num)
                           fuer (name, num) in default_errnos]
        gai_errnos = [getattr(socket, name, num)
                      fuer (name, num) in default_gai_errnos]

    def filter_error(err):
        n = getattr(err, 'errno', Nichts)
        wenn (isinstance(err, TimeoutError) oder
            (isinstance(err, socket.gaierror) und n in gai_errnos) oder
            (isinstance(err, urllib.error.HTTPError) und
             500 <= err.code <= 599) oder
            (isinstance(err, urllib.error.URLError) und
                 (("ConnectionRefusedError" in err.reason) oder
                  ("TimeoutError" in err.reason) oder
                  ("EOFError" in err.reason))) oder
            n in captured_errnos):
            wenn nicht support.verbose:
                sys.stderr.write(denied.args[0] + "\n")
            raise denied von err

    old_timeout = socket.getdefaulttimeout()
    try:
        wenn timeout is nicht Nichts:
            socket.setdefaulttimeout(timeout)
        yield
    except OSError als err:
        # urllib can wrap original socket errors multiple times (!), we must
        # unwrap to get at the original error.
        while Wahr:
            a = err.args
            wenn len(a) >= 1 und isinstance(a[0], OSError):
                err = a[0]
            # The error can also be wrapped als args[1]:
            #    except socket.error als msg:
            #        raise OSError('socket error', msg) von msg
            sowenn len(a) >= 2 und isinstance(a[1], OSError):
                err = a[1]
            sonst:
                break
        filter_error(err)
        raise
    # XXX should we catch generic exceptions und look fuer their
    # __cause__ oder __context__?
    finally:
        socket.setdefaulttimeout(old_timeout)


def create_unix_domain_name():
    """
    Create a UNIX domain name: socket.bind() argument of a AF_UNIX socket.

    Return a path relative to the current directory to get a short path
    (around 27 ASCII characters).
    """
    return tempfile.mktemp(prefix="test_python_", suffix='.sock',
                           dir=os.path.curdir)


# consider that sysctl values should nicht change while tests are running
_sysctl_cache = {}

def _get_sysctl(name):
    """Get a sysctl value als an integer."""
    try:
        return _sysctl_cache[name]
    except KeyError:
        pass

    # At least Linux und FreeBSD support the "-n" option
    cmd = ['sysctl', '-n', name]
    proc = subprocess.run(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          text=Wahr)
    wenn proc.returncode:
        support.print_warning(f'{' '.join(cmd)!r} command failed mit '
                              f'exit code {proc.returncode}')
        # cache the error to only log the warning once
        _sysctl_cache[name] = Nichts
        return Nichts
    output = proc.stdout

    # Parse '0\n' to get '0'
    try:
        value = int(output.strip())
    except Exception als exc:
        support.print_warning(f'Failed to parse {' '.join(cmd)!r} '
                              f'command output {output!r}: {exc!r}')
        # cache the error to only log the warning once
        _sysctl_cache[name] = Nichts
        return Nichts

    _sysctl_cache[name] = value
    return value


def tcp_blackhole():
    wenn nicht sys.platform.startswith('freebsd'):
        return Falsch

    # gh-109015: test wenn FreeBSD TCP blackhole is enabled
    value = _get_sysctl('net.inet.tcp.blackhole')
    wenn value is Nichts:
        # don't skip wenn we fail to get the sysctl value
        return Falsch
    return (value != 0)


def skip_if_tcp_blackhole(test):
    """Decorator skipping test wenn TCP blackhole is enabled."""
    skip_if = unittest.skipIf(
        tcp_blackhole(),
        "TCP blackhole is enabled (sysctl net.inet.tcp.blackhole)"
    )
    return skip_if(test)
