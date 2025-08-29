r"""HTTP cookie handling fuer web clients.

This module has (now fairly distant) origins in Gisle Aas' Perl module
HTTP::Cookies, von the libwww-perl library.

Docstrings, comments und debug strings in this code refer to the
attributes of the HTTP cookie system als cookie-attributes, to distinguish
them clearly von Python attributes.

Class diagram (note that BSDDBCookieJar und the MSIE* classes are not
distributed mit the Python standard library, but are available from
http://wwwsearch.sf.net/):

                        CookieJar____
                        /     \      \
            FileCookieJar      \      \
             /    |   \         \      \
 MozillaCookieJar | LWPCookieJar \      \
                  |               |      \
                  |   ---MSIEBase |       \
                  |  /      |     |        \
                  | /   MSIEDBCookieJar BSDDBCookieJar
                  |/
               MSIECookieJar

"""

__all__ = ['Cookie', 'CookieJar', 'CookiePolicy', 'DefaultCookiePolicy',
           'FileCookieJar', 'LWPCookieJar', 'LoadError', 'MozillaCookieJar']

importiere os
importiere copy
importiere datetime
importiere re
importiere time
importiere urllib.parse, urllib.request
importiere threading als _threading
importiere http.client  # only fuer the default HTTP port
von calendar importiere timegm

debug = Falsch   # set to Wahr to enable debugging via the logging module
logger = Nichts

def _debug(*args):
    wenn nicht debug:
        return
    global logger
    wenn nicht logger:
        importiere logging
        logger = logging.getLogger("http.cookiejar")
    return logger.debug(*args)

HTTPONLY_ATTR = "HTTPOnly"
HTTPONLY_PREFIX = "#HttpOnly_"
DEFAULT_HTTP_PORT = str(http.client.HTTP_PORT)
NETSCAPE_MAGIC_RGX = re.compile("#( Netscape)? HTTP Cookie File")
MISSING_FILENAME_TEXT = ("a filename was nicht supplied (nor was the CookieJar "
                         "instance initialised mit one)")
NETSCAPE_HEADER_TEXT =  """\
# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do nicht edit.

"""

def _warn_unhandled_exception():
    # There are a few catch-all except: statements in this module, for
    # catching input that's bad in unexpected ways.  Warn wenn any
    # exceptions are caught there.
    importiere io, warnings, traceback
    f = io.StringIO()
    traceback.print_exc(Nichts, f)
    msg = f.getvalue()
    warnings.warn("http.cookiejar bug!\n%s" % msg, stacklevel=2)


# Date/time conversion
# -----------------------------------------------------------------------------

EPOCH_YEAR = 1970
def _timegm(tt):
    year, month, mday, hour, min, sec = tt[:6]
    wenn ((year >= EPOCH_YEAR) und (1 <= month <= 12) und (1 <= mday <= 31) und
        (0 <= hour <= 24) und (0 <= min <= 59) und (0 <= sec <= 61)):
        return timegm(tt)
    sonst:
        return Nichts

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LOWER = [month.lower() fuer month in MONTHS]

def time2isoz(t=Nichts):
    """Return a string representing time in seconds since epoch, t.

    If the function is called without an argument, it will use the current
    time.

    The format of the returned string is like "YYYY-MM-DD hh:mm:ssZ",
    representing Universal Time (UTC, aka GMT).  An example of this format is:

    1994-11-24 08:49:37Z

    """
    wenn t is Nichts:
        dt = datetime.datetime.now(tz=datetime.UTC)
    sonst:
        dt = datetime.datetime.fromtimestamp(t, tz=datetime.UTC)
    return "%04d-%02d-%02d %02d:%02d:%02dZ" % (
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

def time2netscape(t=Nichts):
    """Return a string representing time in seconds since epoch, t.

    If the function is called without an argument, it will use the current
    time.

    The format of the returned string is like this:

    Wed, DD-Mon-YYYY HH:MM:SS GMT

    """
    wenn t is Nichts:
        dt = datetime.datetime.now(tz=datetime.UTC)
    sonst:
        dt = datetime.datetime.fromtimestamp(t, tz=datetime.UTC)
    return "%s, %02d-%s-%04d %02d:%02d:%02d GMT" % (
        DAYS[dt.weekday()], dt.day, MONTHS[dt.month-1],
        dt.year, dt.hour, dt.minute, dt.second)


UTC_ZONES = {"GMT": Nichts, "UTC": Nichts, "UT": Nichts, "Z": Nichts}

TIMEZONE_RE = re.compile(r"^([-+])?(\d\d?):?(\d\d)?$", re.ASCII)
def offset_from_tz_string(tz):
    offset = Nichts
    wenn tz in UTC_ZONES:
        offset = 0
    sonst:
        m = TIMEZONE_RE.search(tz)
        wenn m:
            offset = 3600 * int(m.group(2))
            wenn m.group(3):
                offset = offset + 60 * int(m.group(3))
            wenn m.group(1) == '-':
                offset = -offset
    return offset

def _str2time(day, mon, yr, hr, min, sec, tz):
    yr = int(yr)
    wenn yr > datetime.MAXYEAR:
        return Nichts

    # translate month name to number
    # month numbers start mit 1 (January)
    try:
        mon = MONTHS_LOWER.index(mon.lower())+1
    except ValueError:
        # maybe it's already a number
        try:
            imon = int(mon)
        except ValueError:
            return Nichts
        wenn 1 <= imon <= 12:
            mon = imon
        sonst:
            return Nichts

    # make sure clock elements are defined
    wenn hr is Nichts: hr = 0
    wenn min is Nichts: min = 0
    wenn sec is Nichts: sec = 0

    day = int(day)
    hr = int(hr)
    min = int(min)
    sec = int(sec)

    wenn yr < 1000:
        # find "obvious" year
        cur_yr = time.localtime(time.time())[0]
        m = cur_yr % 100
        tmp = yr
        yr = yr + cur_yr - m
        m = m - tmp
        wenn abs(m) > 50:
            wenn m > 0: yr = yr + 100
            sonst: yr = yr - 100

    # convert UTC time tuple to seconds since epoch (nicht timezone-adjusted)
    t = _timegm((yr, mon, day, hr, min, sec, tz))

    wenn t is nicht Nichts:
        # adjust time using timezone string, to get absolute time since epoch
        wenn tz is Nichts:
            tz = "UTC"
        tz = tz.upper()
        offset = offset_from_tz_string(tz)
        wenn offset is Nichts:
            return Nichts
        t = t - offset

    return t

STRICT_DATE_RE = re.compile(
    r"^[SMTWF][a-z][a-z], (\d\d) ([JFMASOND][a-z][a-z]) "
    r"(\d\d\d\d) (\d\d):(\d\d):(\d\d) GMT$", re.ASCII)
WEEKDAY_RE = re.compile(
    r"^(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)[a-z]*,?\s*", re.I | re.ASCII)
LOOSE_HTTP_DATE_RE = re.compile(
    r"""^
    (\d\d?)            # day
       (?:\s+|[-\/])
    (\w+)              # month
        (?:\s+|[-\/])
    (\d+)              # year
    (?:
          (?:\s+|:)    # separator before clock
       (\d\d?):(\d\d)  # hour:min
       (?::(\d\d))?    # optional seconds
    )?                 # optional clock
       \s*
    (?:
       ([-+]?\d{2,4}|(?![APap][Mm]\b)[A-Za-z]+) # timezone
       \s*
    )?
    (?:
       \(\w+\)         # ASCII representation of timezone in parens.
       \s*
    )?$""", re.X | re.ASCII)
def http2time(text):
    """Returns time in seconds since epoch of time represented by a string.

    Return value is an integer.

    Nichts is returned wenn the format of str is unrecognized, the time is outside
    the representable range, oder the timezone string is nicht recognized.  If the
    string contains no timezone, UTC is assumed.

    The timezone in the string may be numerical (like "-0800" oder "+0100") oder a
    string timezone (like "UTC", "GMT", "BST" oder "EST").  Currently, only the
    timezone strings equivalent to UTC (zero offset) are known to the function.

    The function loosely parses the following formats:

    Wed, 09 Feb 1994 22:23:32 GMT       -- HTTP format
    Tuesday, 08-Feb-94 14:15:29 GMT     -- old rfc850 HTTP format
    Tuesday, 08-Feb-1994 14:15:29 GMT   -- broken rfc850 HTTP format
    09 Feb 1994 22:23:32 GMT            -- HTTP format (no weekday)
    08-Feb-94 14:15:29 GMT              -- rfc850 format (no weekday)
    08-Feb-1994 14:15:29 GMT            -- broken rfc850 format (no weekday)

    The parser ignores leading und trailing whitespace.  The time may be
    absent.

    If the year is given mit only 2 digits, the function will select the
    century that makes the year closest to the current date.

    """
    # fast exit fuer strictly conforming string
    m = STRICT_DATE_RE.search(text)
    wenn m:
        g = m.groups()
        mon = MONTHS_LOWER.index(g[1].lower()) + 1
        tt = (int(g[2]), mon, int(g[0]),
              int(g[3]), int(g[4]), float(g[5]))
        return _timegm(tt)

    # No, we need some messy parsing...

    # clean up
    text = text.lstrip()
    text = WEEKDAY_RE.sub("", text, 1)  # Useless weekday

    # tz is time zone specifier string
    day, mon, yr, hr, min, sec, tz = [Nichts]*7

    # loose regexp parse
    m = LOOSE_HTTP_DATE_RE.search(text)
    wenn m is nicht Nichts:
        day, mon, yr, hr, min, sec, tz = m.groups()
    sonst:
        return Nichts  # bad format

    return _str2time(day, mon, yr, hr, min, sec, tz)

ISO_DATE_RE = re.compile(
    r"""^
    (\d{4})              # year
       [-\/]?
    (\d\d?)              # numerical month
       [-\/]?
    (\d\d?)              # day
   (?:
         (?:\s+|[-:Tt])  # separator before clock
      (\d\d?):?(\d\d)    # hour:min
      (?::?(\d\d(?:\.\d*)?))?  # optional seconds (and fractional)
   )?                    # optional clock
      \s*
   (?:
      ([-+]?\d\d?:?(:?\d\d)?
       |Z|z)             # timezone  (Z is "zero meridian", i.e. GMT)
      \s*
   )?$""", re.X | re. ASCII)
def iso2time(text):
    """
    As fuer http2time, but parses the ISO 8601 formats:

    1994-02-03 14:15:29 -0100    -- ISO 8601 format
    1994-02-03 14:15:29          -- zone is optional
    1994-02-03                   -- only date
    1994-02-03T14:15:29          -- Use T als separator
    19940203T141529Z             -- ISO 8601 compact format
    19940203                     -- only date

    """
    # clean up
    text = text.lstrip()

    # tz is time zone specifier string
    day, mon, yr, hr, min, sec, tz = [Nichts]*7

    # loose regexp parse
    m = ISO_DATE_RE.search(text)
    wenn m is nicht Nichts:
        # XXX there's an extra bit of the timezone I'm ignoring here: is
        #   this the right thing to do?
        yr, mon, day, hr, min, sec, tz, _ = m.groups()
    sonst:
        return Nichts  # bad format

    return _str2time(day, mon, yr, hr, min, sec, tz)


# Header parsing
# -----------------------------------------------------------------------------

def unmatched(match):
    """Return unmatched part of re.Match object."""
    start, end = match.span(0)
    return match.string[:start]+match.string[end:]

HEADER_TOKEN_RE =        re.compile(r"^\s*([^=\s;,]+)")
HEADER_QUOTED_VALUE_RE = re.compile(r"^\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"")
HEADER_VALUE_RE =        re.compile(r"^\s*=\s*([^\s;,]*)")
HEADER_ESCAPE_RE = re.compile(r"\\(.)")
def split_header_words(header_values):
    r"""Parse header values into a list of lists containing key,value pairs.

    The function knows how to deal mit ",", ";" und "=" als well als quoted
    values after "=".  A list of space separated tokens are parsed als wenn they
    were separated by ";".

    If the header_values passed als argument contains multiple values, then they
    are treated als wenn they were a single value separated by comma ",".

    This means that this function is useful fuer parsing header fields that
    follow this syntax (BNF als von the HTTP/1.1 specification, but we relax
    the requirement fuer tokens).

      headers           = #header
      header            = (token | parameter) *( [";"] (token | parameter))

      token             = 1*<any CHAR except CTLs oder separators>
      separators        = "(" | ")" | "<" | ">" | "@"
                        | "," | ";" | ":" | "\" | <">
                        | "/" | "[" | "]" | "?" | "="
                        | "{" | "}" | SP | HT

      quoted-string     = ( <"> *(qdtext | quoted-pair ) <"> )
      qdtext            = <any TEXT except <">>
      quoted-pair       = "\" CHAR

      parameter         = attribute "=" value
      attribute         = token
      value             = token | quoted-string

    Each header is represented by a list of key/value pairs.  The value fuer a
    simple token (nicht part of a parameter) is Nichts.  Syntactically incorrect
    headers will nicht necessarily be parsed als you would want.

    This is easier to describe mit some examples:

    >>> split_header_words(['foo="bar"; port="80,81"; discard, bar=baz'])
    [[('foo', 'bar'), ('port', '80,81'), ('discard', Nichts)], [('bar', 'baz')]]
    >>> split_header_words(['text/html; charset="iso-8859-1"'])
    [[('text/html', Nichts), ('charset', 'iso-8859-1')]]
    >>> split_header_words([r'Basic realm="\"foo\bar\""'])
    [[('Basic', Nichts), ('realm', '"foobar"')]]

    """
    assert nicht isinstance(header_values, str)
    result = []
    fuer text in header_values:
        orig_text = text
        pairs = []
        while text:
            m = HEADER_TOKEN_RE.search(text)
            wenn m:
                text = unmatched(m)
                name = m.group(1)
                m = HEADER_QUOTED_VALUE_RE.search(text)
                wenn m:  # quoted value
                    text = unmatched(m)
                    value = m.group(1)
                    value = HEADER_ESCAPE_RE.sub(r"\1", value)
                sonst:
                    m = HEADER_VALUE_RE.search(text)
                    wenn m:  # unquoted value
                        text = unmatched(m)
                        value = m.group(1)
                        value = value.rstrip()
                    sonst:
                        # no value, a lone token
                        value = Nichts
                pairs.append((name, value))
            sowenn text.lstrip().startswith(","):
                # concatenated headers, als per RFC 2616 section 4.2
                text = text.lstrip()[1:]
                wenn pairs: result.append(pairs)
                pairs = []
            sonst:
                # skip junk
                non_junk, nr_junk_chars = re.subn(r"^[=\s;]*", "", text)
                assert nr_junk_chars > 0, (
                    "split_header_words bug: '%s', '%s', %s" %
                    (orig_text, text, pairs))
                text = non_junk
        wenn pairs: result.append(pairs)
    return result

HEADER_JOIN_TOKEN_RE = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
HEADER_JOIN_ESCAPE_RE = re.compile(r"([\"\\])")
def join_header_words(lists):
    """Do the inverse (almost) of the conversion done by split_header_words.

    Takes a list of lists of (key, value) pairs und produces a single header
    value.  Attribute values are quoted wenn needed.

    >>> join_header_words([[("text/plain", Nichts), ("charset", "iso-8859/1")]])
    'text/plain; charset="iso-8859/1"'
    >>> join_header_words([[("text/plain", Nichts)], [("charset", "iso-8859/1")]])
    'text/plain, charset="iso-8859/1"'

    """
    headers = []
    fuer pairs in lists:
        attr = []
        fuer k, v in pairs:
            wenn v is nicht Nichts:
                wenn nicht HEADER_JOIN_TOKEN_RE.fullmatch(v):
                    v = HEADER_JOIN_ESCAPE_RE.sub(r"\\\1", v)  # escape " und \
                    v = '"%s"' % v
                k = "%s=%s" % (k, v)
            attr.append(k)
        wenn attr: headers.append("; ".join(attr))
    return ", ".join(headers)

def strip_quotes(text):
    wenn text.startswith('"'):
        text = text[1:]
    wenn text.endswith('"'):
        text = text[:-1]
    return text

def parse_ns_headers(ns_headers):
    """Ad-hoc parser fuer Netscape protocol cookie-attributes.

    The old Netscape cookie format fuer Set-Cookie can fuer instance contain
    an unquoted "," in the expires field, so we have to use this ad-hoc
    parser instead of split_header_words.

    XXX This may nicht make the best possible effort to parse all the crap
    that Netscape Cookie headers contain.  Ronald Tschalar's HTTPClient
    parser is probably better, so could do worse than following that if
    this ever gives any trouble.

    Currently, this is also used fuer parsing RFC 2109 cookies.

    """
    known_attrs = ("expires", "domain", "path", "secure",
                   # RFC 2109 attrs (may turn up in Netscape cookies, too)
                   "version", "port", "max-age")

    result = []
    fuer ns_header in ns_headers:
        pairs = []
        version_set = Falsch

        # XXX: The following does nicht strictly adhere to RFCs in that empty
        # names und values are legal (the former will only appear once und will
        # be overwritten wenn multiple occurrences are present). This is
        # mostly to deal mit backwards compatibility.
        fuer ii, param in enumerate(ns_header.split(';')):
            param = param.strip()

            key, sep, val = param.partition('=')
            key = key.strip()

            wenn nicht key:
                wenn ii == 0:
                    break
                sonst:
                    continue

            # allow fuer a distinction between present und empty und missing
            # altogether
            val = val.strip() wenn sep sonst Nichts

            wenn ii != 0:
                lc = key.lower()
                wenn lc in known_attrs:
                    key = lc

                wenn key == "version":
                    # This is an RFC 2109 cookie.
                    wenn val is nicht Nichts:
                        val = strip_quotes(val)
                    version_set = Wahr
                sowenn key == "expires":
                    # convert expires date to seconds since epoch
                    wenn val is nicht Nichts:
                        val = http2time(strip_quotes(val))  # Nichts wenn invalid
            pairs.append((key, val))

        wenn pairs:
            wenn nicht version_set:
                pairs.append(("version", "0"))
            result.append(pairs)

    return result


IPV4_RE = re.compile(r"\.\d+$", re.ASCII)
def is_HDN(text):
    """Return Wahr wenn text is a host domain name."""
    # XXX
    # This may well be wrong.  Which RFC is HDN defined in, wenn any (for
    #  the purposes of RFC 2965)?
    # For the current implementation, what about IPv6?  Remember to look
    #  at other uses of IPV4_RE also, wenn change this.
    wenn IPV4_RE.search(text):
        return Falsch
    wenn text == "":
        return Falsch
    wenn text[0] == "." oder text[-1] == ".":
        return Falsch
    return Wahr

def domain_match(A, B):
    """Return Wahr wenn domain A domain-matches domain B, according to RFC 2965.

    A und B may be host domain names oder IP addresses.

    RFC 2965, section 1:

    Host names can be specified either als an IP address oder a HDN string.
    Sometimes we compare one host name mit another.  (Such comparisons SHALL
    be case-insensitive.)  Host A's name domain-matches host B's if

         *  their host name strings string-compare equal; oder

         * A is a HDN string und has the form NB, where N is a non-empty
            name string, B has the form .B', und B' is a HDN string.  (So,
            x.y.com domain-matches .Y.com but nicht Y.com.)

    Note that domain-match is nicht a commutative operation: a.b.c.com
    domain-matches .c.com, but nicht the reverse.

    """
    # Note that, wenn A oder B are IP addresses, the only relevant part of the
    # definition of the domain-match algorithm is the direct string-compare.
    A = A.lower()
    B = B.lower()
    wenn A == B:
        return Wahr
    wenn nicht is_HDN(A):
        return Falsch
    i = A.rfind(B)
    wenn i == -1 oder i == 0:
        # A does nicht have form NB, oder N is the empty string
        return Falsch
    wenn nicht B.startswith("."):
        return Falsch
    wenn nicht is_HDN(B[1:]):
        return Falsch
    return Wahr

def liberal_is_HDN(text):
    """Return Wahr wenn text is a sort-of-like a host domain name.

    For accepting/blocking domains.

    """
    wenn IPV4_RE.search(text):
        return Falsch
    return Wahr

def user_domain_match(A, B):
    """For blocking/accepting domains.

    A und B may be host domain names oder IP addresses.

    """
    A = A.lower()
    B = B.lower()
    wenn nicht (liberal_is_HDN(A) und liberal_is_HDN(B)):
        wenn A == B:
            # equal IP addresses
            return Wahr
        return Falsch
    initial_dot = B.startswith(".")
    wenn initial_dot und A.endswith(B):
        return Wahr
    wenn nicht initial_dot und A == B:
        return Wahr
    return Falsch

cut_port_re = re.compile(r":\d+$", re.ASCII)
def request_host(request):
    """Return request-host, als defined by RFC 2965.

    Variation von RFC: returned value is lowercased, fuer convenient
    comparison.

    """
    url = request.get_full_url()
    host = urllib.parse.urlparse(url)[1]
    wenn host == "":
        host = request.get_header("Host", "")

    # remove port, wenn present
    host = cut_port_re.sub("", host, 1)
    return host.lower()

def eff_request_host(request):
    """Return a tuple (request-host, effective request-host name).

    As defined by RFC 2965, except both are lowercased.

    """
    erhn = req_host = request_host(request)
    wenn "." nicht in req_host:
        erhn = req_host + ".local"
    return req_host, erhn

def request_path(request):
    """Path component of request-URI, als defined by RFC 2965."""
    url = request.get_full_url()
    parts = urllib.parse.urlsplit(url)
    path = escape_path(parts.path)
    wenn nicht path.startswith("/"):
        # fix bad RFC 2396 absoluteURI
        path = "/" + path
    return path

def request_port(request):
    host = request.host
    i = host.find(':')
    wenn i >= 0:
        port = host[i+1:]
        try:
            int(port)
        except ValueError:
            _debug("nonnumeric port: '%s'", port)
            return Nichts
    sonst:
        port = DEFAULT_HTTP_PORT
    return port

# Characters in addition to A-Z, a-z, 0-9, '_', '.', und '-' that don't
# need to be escaped to form a valid HTTP URL (RFCs 2396 und 1738).
HTTP_PATH_SAFE = "%/;:@&=+$,!~*'()"
ESCAPED_CHAR_RE = re.compile(r"%([0-9a-fA-F][0-9a-fA-F])")
def uppercase_escaped_char(match):
    return "%%%s" % match.group(1).upper()
def escape_path(path):
    """Escape any invalid characters in HTTP URL, und uppercase all escapes."""
    # There's no knowing what character encoding was used to create URLs
    # containing %-escapes, but since we have to pick one to escape invalid
    # path characters, we pick UTF-8, als recommended in the HTML 4.0
    # specification:
    # http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2.1
    # And here, kind of: draft-fielding-uri-rfc2396bis-03
    # (And in draft IRI specification: draft-duerst-iri-05)
    # (And here, fuer new URI schemes: RFC 2718)
    path = urllib.parse.quote(path, HTTP_PATH_SAFE)
    path = ESCAPED_CHAR_RE.sub(uppercase_escaped_char, path)
    return path

def reach(h):
    """Return reach of host h, als defined by RFC 2965, section 1.

    The reach R of a host name H is defined als follows:

       *  If

          -  H is the host domain name of a host; and,

          -  H has the form A.B; und

          -  A has no embedded (that is, interior) dots; und

          -  B has at least one embedded dot, oder B is the string "local".
             then the reach of H is .B.

       *  Otherwise, the reach of H is H.

    >>> reach("www.acme.com")
    '.acme.com'
    >>> reach("acme.com")
    'acme.com'
    >>> reach("acme.local")
    '.local'

    """
    i = h.find(".")
    wenn i >= 0:
        #a = h[:i]  # this line is only here to show what a is
        b = h[i+1:]
        i = b.find(".")
        wenn is_HDN(h) und (i >= 0 oder b == "local"):
            return "."+b
    return h

def is_third_party(request):
    """

    RFC 2965, section 3.3.6:

        An unverifiable transaction is to a third-party host wenn its request-
        host U does nicht domain-match the reach R of the request-host O in the
        origin transaction.

    """
    req_host = request_host(request)
    wenn nicht domain_match(req_host, reach(request.origin_req_host)):
        return Wahr
    sonst:
        return Falsch


klasse Cookie:
    """HTTP Cookie.

    This klasse represents both Netscape und RFC 2965 cookies.

    This is deliberately a very simple class.  It just holds attributes.  It's
    possible to construct Cookie instances that don't comply mit the cookie
    standards.  CookieJar.make_cookies is the factory function fuer Cookie
    objects -- it deals mit cookie parsing, supplying defaults, und
    normalising to the representation used in this class.  CookiePolicy is
    responsible fuer checking them to see whether they should be accepted from
    und returned to the server.

    Note that the port may be present in the headers, but unspecified ("Port"
    rather than"Port=80", fuer example); wenn this is the case, port is Nichts.

    """

    def __init__(self, version, name, value,
                 port, port_specified,
                 domain, domain_specified, domain_initial_dot,
                 path, path_specified,
                 secure,
                 expires,
                 discard,
                 comment,
                 comment_url,
                 rest,
                 rfc2109=Falsch,
                 ):

        wenn version is nicht Nichts: version = int(version)
        wenn expires is nicht Nichts: expires = int(float(expires))
        wenn port is Nichts und port_specified is Wahr:
            raise ValueError("if port is Nichts, port_specified must be false")

        self.version = version
        self.name = name
        self.value = value
        self.port = port
        self.port_specified = port_specified
        # normalise case, als per RFC 2965 section 3.3.3
        self.domain = domain.lower()
        self.domain_specified = domain_specified
        # Sigh.  We need to know whether the domain given in the
        # cookie-attribute had an initial dot, in order to follow RFC 2965
        # (as clarified in draft errata).  Needed fuer the returned $Domain
        # value.
        self.domain_initial_dot = domain_initial_dot
        self.path = path
        self.path_specified = path_specified
        self.secure = secure
        self.expires = expires
        self.discard = discard
        self.comment = comment
        self.comment_url = comment_url
        self.rfc2109 = rfc2109

        self._rest = copy.copy(rest)

    def has_nonstandard_attr(self, name):
        return name in self._rest
    def get_nonstandard_attr(self, name, default=Nichts):
        return self._rest.get(name, default)
    def set_nonstandard_attr(self, name, value):
        self._rest[name] = value

    def is_expired(self, now=Nichts):
        wenn now is Nichts: now = time.time()
        wenn (self.expires is nicht Nichts) und (self.expires <= now):
            return Wahr
        return Falsch

    def __str__(self):
        wenn self.port is Nichts: p = ""
        sonst: p = ":"+self.port
        limit = self.domain + p + self.path
        wenn self.value is nicht Nichts:
            namevalue = "%s=%s" % (self.name, self.value)
        sonst:
            namevalue = self.name
        return "<Cookie %s fuer %s>" % (namevalue, limit)

    def __repr__(self):
        args = []
        fuer name in ("version", "name", "value",
                     "port", "port_specified",
                     "domain", "domain_specified", "domain_initial_dot",
                     "path", "path_specified",
                     "secure", "expires", "discard", "comment", "comment_url",
                     ):
            attr = getattr(self, name)
            args.append("%s=%s" % (name, repr(attr)))
        args.append("rest=%s" % repr(self._rest))
        args.append("rfc2109=%s" % repr(self.rfc2109))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))


klasse CookiePolicy:
    """Defines which cookies get accepted von und returned to server.

    May also modify cookies, though this is probably a bad idea.

    The subclass DefaultCookiePolicy defines the standard rules fuer Netscape
    und RFC 2965 cookies -- override that wenn you want a customized policy.

    """
    def set_ok(self, cookie, request):
        """Return true wenn (and only if) cookie should be accepted von server.

        Currently, pre-expired cookies never get this far -- the CookieJar
        klasse deletes such cookies itself.

        """
        raise NotImplementedError()

    def return_ok(self, cookie, request):
        """Return true wenn (and only if) cookie should be returned to server."""
        raise NotImplementedError()

    def domain_return_ok(self, domain, request):
        """Return false wenn cookies should nicht be returned, given cookie domain.
        """
        return Wahr

    def path_return_ok(self, path, request):
        """Return false wenn cookies should nicht be returned, given cookie path.
        """
        return Wahr


klasse DefaultCookiePolicy(CookiePolicy):
    """Implements the standard rules fuer accepting und returning cookies."""

    DomainStrictNoDots = 1
    DomainStrictNonDomain = 2
    DomainRFC2965Match = 4

    DomainLiberal = 0
    DomainStrict = DomainStrictNoDots|DomainStrictNonDomain

    def __init__(self,
                 blocked_domains=Nichts, allowed_domains=Nichts,
                 netscape=Wahr, rfc2965=Falsch,
                 rfc2109_as_netscape=Nichts,
                 hide_cookie2=Falsch,
                 strict_domain=Falsch,
                 strict_rfc2965_unverifiable=Wahr,
                 strict_ns_unverifiable=Falsch,
                 strict_ns_domain=DomainLiberal,
                 strict_ns_set_initial_dollar=Falsch,
                 strict_ns_set_path=Falsch,
                 secure_protocols=("https", "wss")
                 ):
        """Constructor arguments should be passed als keyword arguments only."""
        self.netscape = netscape
        self.rfc2965 = rfc2965
        self.rfc2109_as_netscape = rfc2109_as_netscape
        self.hide_cookie2 = hide_cookie2
        self.strict_domain = strict_domain
        self.strict_rfc2965_unverifiable = strict_rfc2965_unverifiable
        self.strict_ns_unverifiable = strict_ns_unverifiable
        self.strict_ns_domain = strict_ns_domain
        self.strict_ns_set_initial_dollar = strict_ns_set_initial_dollar
        self.strict_ns_set_path = strict_ns_set_path
        self.secure_protocols = secure_protocols

        wenn blocked_domains is nicht Nichts:
            self._blocked_domains = tuple(blocked_domains)
        sonst:
            self._blocked_domains = ()

        wenn allowed_domains is nicht Nichts:
            allowed_domains = tuple(allowed_domains)
        self._allowed_domains = allowed_domains

    def blocked_domains(self):
        """Return the sequence of blocked domains (as a tuple)."""
        return self._blocked_domains
    def set_blocked_domains(self, blocked_domains):
        """Set the sequence of blocked domains."""
        self._blocked_domains = tuple(blocked_domains)

    def is_blocked(self, domain):
        fuer blocked_domain in self._blocked_domains:
            wenn user_domain_match(domain, blocked_domain):
                return Wahr
        return Falsch

    def allowed_domains(self):
        """Return Nichts, oder the sequence of allowed domains (as a tuple)."""
        return self._allowed_domains
    def set_allowed_domains(self, allowed_domains):
        """Set the sequence of allowed domains, oder Nichts."""
        wenn allowed_domains is nicht Nichts:
            allowed_domains = tuple(allowed_domains)
        self._allowed_domains = allowed_domains

    def is_not_allowed(self, domain):
        wenn self._allowed_domains is Nichts:
            return Falsch
        fuer allowed_domain in self._allowed_domains:
            wenn user_domain_match(domain, allowed_domain):
                return Falsch
        return Wahr

    def set_ok(self, cookie, request):
        """
        If you override .set_ok(), be sure to call this method.  If it returns
        false, so should your subclass (assuming your subclass wants to be more
        strict about which cookies to accept).

        """
        _debug(" - checking cookie %s=%s", cookie.name, cookie.value)

        assert cookie.name is nicht Nichts

        fuer n in "version", "verifiability", "name", "path", "domain", "port":
            fn_name = "set_ok_"+n
            fn = getattr(self, fn_name)
            wenn nicht fn(cookie, request):
                return Falsch

        return Wahr

    def set_ok_version(self, cookie, request):
        wenn cookie.version is Nichts:
            # Version is always set to 0 by parse_ns_headers wenn it's a Netscape
            # cookie, so this must be an invalid RFC 2965 cookie.
            _debug("   Set-Cookie2 without version attribute (%s=%s)",
                   cookie.name, cookie.value)
            return Falsch
        wenn cookie.version > 0 und nicht self.rfc2965:
            _debug("   RFC 2965 cookies are switched off")
            return Falsch
        sowenn cookie.version == 0 und nicht self.netscape:
            _debug("   Netscape cookies are switched off")
            return Falsch
        return Wahr

    def set_ok_verifiability(self, cookie, request):
        wenn request.unverifiable und is_third_party(request):
            wenn cookie.version > 0 und self.strict_rfc2965_unverifiable:
                _debug("   third-party RFC 2965 cookie during "
                             "unverifiable transaction")
                return Falsch
            sowenn cookie.version == 0 und self.strict_ns_unverifiable:
                _debug("   third-party Netscape cookie during "
                             "unverifiable transaction")
                return Falsch
        return Wahr

    def set_ok_name(self, cookie, request):
        # Try und stop servers setting V0 cookies designed to hack other
        # servers that know both V0 und V1 protocols.
        wenn (cookie.version == 0 und self.strict_ns_set_initial_dollar und
            cookie.name.startswith("$")):
            _debug("   illegal name (starts mit '$'): '%s'", cookie.name)
            return Falsch
        return Wahr

    def set_ok_path(self, cookie, request):
        wenn cookie.path_specified:
            req_path = request_path(request)
            wenn ((cookie.version > 0 oder
                 (cookie.version == 0 und self.strict_ns_set_path)) und
                nicht self.path_return_ok(cookie.path, request)):
                _debug("   path attribute %s is nicht a prefix of request "
                       "path %s", cookie.path, req_path)
                return Falsch
        return Wahr

    def set_ok_domain(self, cookie, request):
        wenn self.is_blocked(cookie.domain):
            _debug("   domain %s is in user block-list", cookie.domain)
            return Falsch
        wenn self.is_not_allowed(cookie.domain):
            _debug("   domain %s is nicht in user allow-list", cookie.domain)
            return Falsch
        wenn cookie.domain_specified:
            req_host, erhn = eff_request_host(request)
            domain = cookie.domain
            wenn self.strict_domain und (domain.count(".") >= 2):
                # XXX This should probably be compared mit the Konqueror
                # (kcookiejar.cpp) und Mozilla implementations, but it's a
                # losing battle.
                i = domain.rfind(".")
                j = domain.rfind(".", 0, i)
                wenn j == 0:  # domain like .foo.bar
                    tld = domain[i+1:]
                    sld = domain[j+1:i]
                    wenn sld.lower() in ("co", "ac", "com", "edu", "org", "net",
                       "gov", "mil", "int", "aero", "biz", "cat", "coop",
                       "info", "jobs", "mobi", "museum", "name", "pro",
                       "travel", "eu") und len(tld) == 2:
                        # domain like .co.uk
                        _debug("   country-code second level domain %s", domain)
                        return Falsch
            wenn domain.startswith("."):
                undotted_domain = domain[1:]
            sonst:
                undotted_domain = domain
            embedded_dots = (undotted_domain.find(".") >= 0)
            wenn nicht embedded_dots und nicht erhn.endswith(".local"):
                _debug("   non-local domain %s contains no embedded dot",
                       domain)
                return Falsch
            wenn cookie.version == 0:
                wenn (nicht (erhn.endswith(domain) oder
                         erhn.endswith(f"{undotted_domain}.local")) und
                    (nicht erhn.startswith(".") und
                     nicht ("."+erhn).endswith(domain))):
                    _debug("   effective request-host %s (even mit added "
                           "initial dot) does nicht end mit %s",
                           erhn, domain)
                    return Falsch
            wenn (cookie.version > 0 oder
                (self.strict_ns_domain & self.DomainRFC2965Match)):
                wenn nicht domain_match(erhn, domain):
                    _debug("   effective request-host %s does nicht domain-match "
                           "%s", erhn, domain)
                    return Falsch
            wenn (cookie.version > 0 oder
                (self.strict_ns_domain & self.DomainStrictNoDots)):
                host_prefix = req_host[:-len(domain)]
                wenn (host_prefix.find(".") >= 0 und
                    nicht IPV4_RE.search(req_host)):
                    _debug("   host prefix %s fuer domain %s contains a dot",
                           host_prefix, domain)
                    return Falsch
        return Wahr

    def set_ok_port(self, cookie, request):
        wenn cookie.port_specified:
            req_port = request_port(request)
            wenn req_port is Nichts:
                req_port = "80"
            sonst:
                req_port = str(req_port)
            fuer p in cookie.port.split(","):
                try:
                    int(p)
                except ValueError:
                    _debug("   bad port %s (nicht numeric)", p)
                    return Falsch
                wenn p == req_port:
                    break
            sonst:
                _debug("   request port (%s) nicht found in %s",
                       req_port, cookie.port)
                return Falsch
        return Wahr

    def return_ok(self, cookie, request):
        """
        If you override .return_ok(), be sure to call this method.  If it
        returns false, so should your subclass (assuming your subclass wants to
        be more strict about which cookies to return).

        """
        # Path has already been checked by .path_return_ok(), und domain
        # blocking done by .domain_return_ok().
        _debug(" - checking cookie %s=%s", cookie.name, cookie.value)

        fuer n in "version", "verifiability", "secure", "expires", "port", "domain":
            fn_name = "return_ok_"+n
            fn = getattr(self, fn_name)
            wenn nicht fn(cookie, request):
                return Falsch
        return Wahr

    def return_ok_version(self, cookie, request):
        wenn cookie.version > 0 und nicht self.rfc2965:
            _debug("   RFC 2965 cookies are switched off")
            return Falsch
        sowenn cookie.version == 0 und nicht self.netscape:
            _debug("   Netscape cookies are switched off")
            return Falsch
        return Wahr

    def return_ok_verifiability(self, cookie, request):
        wenn request.unverifiable und is_third_party(request):
            wenn cookie.version > 0 und self.strict_rfc2965_unverifiable:
                _debug("   third-party RFC 2965 cookie during unverifiable "
                       "transaction")
                return Falsch
            sowenn cookie.version == 0 und self.strict_ns_unverifiable:
                _debug("   third-party Netscape cookie during unverifiable "
                       "transaction")
                return Falsch
        return Wahr

    def return_ok_secure(self, cookie, request):
        wenn cookie.secure und request.type nicht in self.secure_protocols:
            _debug("   secure cookie mit non-secure request")
            return Falsch
        return Wahr

    def return_ok_expires(self, cookie, request):
        wenn cookie.is_expired(self._now):
            _debug("   cookie expired")
            return Falsch
        return Wahr

    def return_ok_port(self, cookie, request):
        wenn cookie.port:
            req_port = request_port(request)
            wenn req_port is Nichts:
                req_port = "80"
            fuer p in cookie.port.split(","):
                wenn p == req_port:
                    break
            sonst:
                _debug("   request port %s does nicht match cookie port %s",
                       req_port, cookie.port)
                return Falsch
        return Wahr

    def return_ok_domain(self, cookie, request):
        req_host, erhn = eff_request_host(request)
        domain = cookie.domain

        wenn domain und nicht domain.startswith("."):
            dotdomain = "." + domain
        sonst:
            dotdomain = domain

        # strict check of non-domain cookies: Mozilla does this, MSIE5 doesn't
        wenn (cookie.version == 0 und
            (self.strict_ns_domain & self.DomainStrictNonDomain) und
            nicht cookie.domain_specified und domain != erhn):
            _debug("   cookie mit unspecified domain does nicht string-compare "
                   "equal to request domain")
            return Falsch

        wenn cookie.version > 0 und nicht domain_match(erhn, domain):
            _debug("   effective request-host name %s does nicht domain-match "
                   "RFC 2965 cookie domain %s", erhn, domain)
            return Falsch
        wenn cookie.version == 0 und nicht ("."+erhn).endswith(dotdomain):
            _debug("   request-host %s does nicht match Netscape cookie domain "
                   "%s", req_host, domain)
            return Falsch
        return Wahr

    def domain_return_ok(self, domain, request):
        # Liberal check of.  This is here als an optimization to avoid
        # having to load lots of MSIE cookie files unless necessary.
        req_host, erhn = eff_request_host(request)
        wenn nicht req_host.startswith("."):
            req_host = "."+req_host
        wenn nicht erhn.startswith("."):
            erhn = "."+erhn
        wenn domain und nicht domain.startswith("."):
            dotdomain = "." + domain
        sonst:
            dotdomain = domain
        wenn nicht (req_host.endswith(dotdomain) oder erhn.endswith(dotdomain)):
            #_debug("   request domain %s does nicht match cookie domain %s",
            #       req_host, domain)
            return Falsch

        wenn self.is_blocked(domain):
            _debug("   domain %s is in user block-list", domain)
            return Falsch
        wenn self.is_not_allowed(domain):
            _debug("   domain %s is nicht in user allow-list", domain)
            return Falsch

        return Wahr

    def path_return_ok(self, path, request):
        _debug("- checking cookie path=%s", path)
        req_path = request_path(request)
        pathlen = len(path)
        wenn req_path == path:
            return Wahr
        sowenn (req_path.startswith(path) und
              (path.endswith("/") oder req_path[pathlen:pathlen+1] == "/")):
            return Wahr

        _debug("  %s does nicht path-match %s", req_path, path)
        return Falsch

def deepvalues(mapping):
    """Iterates over nested mapping, depth-first"""
    fuer obj in list(mapping.values()):
        mapping = Falsch
        try:
            obj.items
        except AttributeError:
            pass
        sonst:
            mapping = Wahr
            yield von deepvalues(obj)
        wenn nicht mapping:
            yield obj


# Used als second parameter to dict.get() method, to distinguish absent
# dict key von one mit a Nichts value.
klasse Absent: pass

klasse CookieJar:
    """Collection of HTTP cookies.

    You may nicht need to know about this class: try
    urllib.request.build_opener(HTTPCookieProcessor).open(url).
    """

    non_word_re = re.compile(r"\W")
    quote_re = re.compile(r"([\"\\])")
    strict_domain_re = re.compile(r"\.?[^.]*")
    domain_re = re.compile(r"[^.]*")
    dots_re = re.compile(r"^\.+")

    magic_re = re.compile(r"^\#LWP-Cookies-(\d+\.\d+)", re.ASCII)

    def __init__(self, policy=Nichts):
        wenn policy is Nichts:
            policy = DefaultCookiePolicy()
        self._policy = policy

        self._cookies_lock = _threading.RLock()
        self._cookies = {}

    def set_policy(self, policy):
        self._policy = policy

    def _cookies_for_domain(self, domain, request):
        cookies = []
        wenn nicht self._policy.domain_return_ok(domain, request):
            return []
        _debug("Checking %s fuer cookies to return", domain)
        cookies_by_path = self._cookies[domain]
        fuer path in cookies_by_path.keys():
            wenn nicht self._policy.path_return_ok(path, request):
                continue
            cookies_by_name = cookies_by_path[path]
            fuer cookie in cookies_by_name.values():
                wenn nicht self._policy.return_ok(cookie, request):
                    _debug("   nicht returning cookie")
                    continue
                _debug("   it's a match")
                cookies.append(cookie)
        return cookies

    def _cookies_for_request(self, request):
        """Return a list of cookies to be returned to server."""
        cookies = []
        fuer domain in self._cookies.keys():
            cookies.extend(self._cookies_for_domain(domain, request))
        return cookies

    def _cookie_attrs(self, cookies):
        """Return a list of cookie-attributes to be returned to server.

        like ['foo="bar"; $Path="/"', ...]

        The $Version attribute is also added when appropriate (currently only
        once per request).

        """
        # add cookies in order of most specific (ie. longest) path first
        cookies.sort(key=lambda a: len(a.path), reverse=Wahr)

        version_set = Falsch

        attrs = []
        fuer cookie in cookies:
            # set version of Cookie header
            # XXX
            # What should it be wenn multiple matching Set-Cookie headers have
            #  different versions themselves?
            # Answer: there is no answer; was supposed to be settled by
            #  RFC 2965 errata, but that may never appear...
            version = cookie.version
            wenn nicht version_set:
                version_set = Wahr
                wenn version > 0:
                    attrs.append("$Version=%s" % version)

            # quote cookie value wenn necessary
            # (nicht fuer Netscape protocol, which already has any quotes
            #  intact, due to the poorly-specified Netscape Cookie: syntax)
            wenn ((cookie.value is nicht Nichts) und
                self.non_word_re.search(cookie.value) und version > 0):
                value = self.quote_re.sub(r"\\\1", cookie.value)
            sonst:
                value = cookie.value

            # add cookie-attributes to be returned in Cookie header
            wenn cookie.value is Nichts:
                attrs.append(cookie.name)
            sonst:
                attrs.append("%s=%s" % (cookie.name, value))
            wenn version > 0:
                wenn cookie.path_specified:
                    attrs.append('$Path="%s"' % cookie.path)
                wenn cookie.domain.startswith("."):
                    domain = cookie.domain
                    wenn (nicht cookie.domain_initial_dot und
                        domain.startswith(".")):
                        domain = domain[1:]
                    attrs.append('$Domain="%s"' % domain)
                wenn cookie.port is nicht Nichts:
                    p = "$Port"
                    wenn cookie.port_specified:
                        p = p + ('="%s"' % cookie.port)
                    attrs.append(p)

        return attrs

    def add_cookie_header(self, request):
        """Add correct Cookie: header to request (urllib.request.Request object).

        The Cookie2 header is also added unless policy.hide_cookie2 is true.

        """
        _debug("add_cookie_header")
        self._cookies_lock.acquire()
        try:

            self._policy._now = self._now = int(time.time())

            cookies = self._cookies_for_request(request)

            attrs = self._cookie_attrs(cookies)
            wenn attrs:
                wenn nicht request.has_header("Cookie"):
                    request.add_unredirected_header(
                        "Cookie", "; ".join(attrs))

            # wenn necessary, advertise that we know RFC 2965
            wenn (self._policy.rfc2965 und nicht self._policy.hide_cookie2 und
                nicht request.has_header("Cookie2")):
                fuer cookie in cookies:
                    wenn cookie.version != 1:
                        request.add_unredirected_header("Cookie2", '$Version="1"')
                        break

        finally:
            self._cookies_lock.release()

        self.clear_expired_cookies()

    def _normalized_cookie_tuples(self, attrs_set):
        """Return list of tuples containing normalised cookie information.

        attrs_set is the list of lists of key,value pairs extracted from
        the Set-Cookie oder Set-Cookie2 headers.

        Tuples are name, value, standard, rest, where name und value are the
        cookie name und value, standard is a dictionary containing the standard
        cookie-attributes (discard, secure, version, expires oder max-age,
        domain, path und port) und rest is a dictionary containing the rest of
        the cookie-attributes.

        """
        cookie_tuples = []

        boolean_attrs = "discard", "secure"
        value_attrs = ("version",
                       "expires", "max-age",
                       "domain", "path", "port",
                       "comment", "commenturl")

        fuer cookie_attrs in attrs_set:
            name, value = cookie_attrs[0]

            # Build dictionary of standard cookie-attributes (standard) und
            # dictionary of other cookie-attributes (rest).

            # Note: expiry time is normalised to seconds since epoch.  V0
            # cookies should have the Expires cookie-attribute, und V1 cookies
            # should have Max-Age, but since V1 includes RFC 2109 cookies (and
            # since V0 cookies may be a mish-mash of Netscape und RFC 2109), we
            # accept either (but prefer Max-Age).
            max_age_set = Falsch

            bad_cookie = Falsch

            standard = {}
            rest = {}
            fuer k, v in cookie_attrs[1:]:
                lc = k.lower()
                # don't lose case distinction fuer unknown fields
                wenn lc in value_attrs oder lc in boolean_attrs:
                    k = lc
                wenn k in boolean_attrs und v is Nichts:
                    # boolean cookie-attribute is present, but has no value
                    # (like "discard", rather than "port=80")
                    v = Wahr
                wenn k in standard:
                    # only first value is significant
                    continue
                wenn k == "domain":
                    wenn v is Nichts:
                        _debug("   missing value fuer domain attribute")
                        bad_cookie = Wahr
                        break
                    # RFC 2965 section 3.3.3
                    v = v.lower()
                wenn k == "expires":
                    wenn max_age_set:
                        # Prefer max-age to expires (like Mozilla)
                        continue
                    wenn v is Nichts:
                        _debug("   missing oder invalid value fuer expires "
                              "attribute: treating als session cookie")
                        continue
                wenn k == "max-age":
                    max_age_set = Wahr
                    try:
                        v = int(v)
                    except ValueError:
                        _debug("   missing oder invalid (non-numeric) value fuer "
                              "max-age attribute")
                        bad_cookie = Wahr
                        break
                    # convert RFC 2965 Max-Age to seconds since epoch
                    # XXX Strictly you're supposed to follow RFC 2616
                    #   age-calculation rules.  Remember that zero Max-Age
                    #   is a request to discard (old und new) cookie, though.
                    k = "expires"
                    v = self._now + v
                wenn (k in value_attrs) oder (k in boolean_attrs):
                    wenn (v is Nichts und
                        k nicht in ("port", "comment", "commenturl")):
                        _debug("   missing value fuer %s attribute" % k)
                        bad_cookie = Wahr
                        break
                    standard[k] = v
                sonst:
                    rest[k] = v

            wenn bad_cookie:
                continue

            cookie_tuples.append((name, value, standard, rest))

        return cookie_tuples

    def _cookie_from_cookie_tuple(self, tup, request):
        # standard is dict of standard cookie-attributes, rest is dict of the
        # rest of them
        name, value, standard, rest = tup

        domain = standard.get("domain", Absent)
        path = standard.get("path", Absent)
        port = standard.get("port", Absent)
        expires = standard.get("expires", Absent)

        # set the easy defaults
        version = standard.get("version", Nichts)
        wenn version is nicht Nichts:
            try:
                version = int(version)
            except ValueError:
                return Nichts  # invalid version, ignore cookie
        secure = standard.get("secure", Falsch)
        # (discard is also set wenn expires is Absent)
        discard = standard.get("discard", Falsch)
        comment = standard.get("comment", Nichts)
        comment_url = standard.get("commenturl", Nichts)

        # set default path
        wenn path is nicht Absent und path != "":
            path_specified = Wahr
            path = escape_path(path)
        sonst:
            path_specified = Falsch
            path = request_path(request)
            i = path.rfind("/")
            wenn i != -1:
                wenn version == 0:
                    # Netscape spec parts company von reality here
                    path = path[:i]
                sonst:
                    path = path[:i+1]
            wenn len(path) == 0: path = "/"

        # set default domain
        domain_specified = domain is nicht Absent
        # but first we have to remember whether it starts mit a dot
        domain_initial_dot = Falsch
        wenn domain_specified:
            domain_initial_dot = bool(domain.startswith("."))
        wenn domain is Absent:
            req_host, erhn = eff_request_host(request)
            domain = erhn
        sowenn nicht domain.startswith("."):
            domain = "."+domain

        # set default port
        port_specified = Falsch
        wenn port is nicht Absent:
            wenn port is Nichts:
                # Port attr present, but has no value: default to request port.
                # Cookie should then only be sent back on that port.
                port = request_port(request)
            sonst:
                port_specified = Wahr
                port = re.sub(r"\s+", "", port)
        sonst:
            # No port attr present.  Cookie can be sent back on any port.
            port = Nichts

        # set default expires und discard
        wenn expires is Absent:
            expires = Nichts
            discard = Wahr
        sowenn expires <= self._now:
            # Expiry date in past is request to delete cookie.  This can't be
            # in DefaultCookiePolicy, because can't delete cookies there.
            try:
                self.clear(domain, path, name)
            except KeyError:
                pass
            _debug("Expiring cookie, domain='%s', path='%s', name='%s'",
                   domain, path, name)
            return Nichts

        return Cookie(version,
                      name, value,
                      port, port_specified,
                      domain, domain_specified, domain_initial_dot,
                      path, path_specified,
                      secure,
                      expires,
                      discard,
                      comment,
                      comment_url,
                      rest)

    def _cookies_from_attrs_set(self, attrs_set, request):
        cookie_tuples = self._normalized_cookie_tuples(attrs_set)

        cookies = []
        fuer tup in cookie_tuples:
            cookie = self._cookie_from_cookie_tuple(tup, request)
            wenn cookie: cookies.append(cookie)
        return cookies

    def _process_rfc2109_cookies(self, cookies):
        rfc2109_as_ns = getattr(self._policy, 'rfc2109_as_netscape', Nichts)
        wenn rfc2109_as_ns is Nichts:
            rfc2109_as_ns = nicht self._policy.rfc2965
        fuer cookie in cookies:
            wenn cookie.version == 1:
                cookie.rfc2109 = Wahr
                wenn rfc2109_as_ns:
                    # treat 2109 cookies als Netscape cookies rather than
                    # als RFC2965 cookies
                    cookie.version = 0

    def make_cookies(self, response, request):
        """Return sequence of Cookie objects extracted von response object."""
        # get cookie-attributes fuer RFC 2965 und Netscape protocols
        headers = response.info()
        rfc2965_hdrs = headers.get_all("Set-Cookie2", [])
        ns_hdrs = headers.get_all("Set-Cookie", [])
        self._policy._now = self._now = int(time.time())

        rfc2965 = self._policy.rfc2965
        netscape = self._policy.netscape

        wenn ((nicht rfc2965_hdrs und nicht ns_hdrs) oder
            (nicht ns_hdrs und nicht rfc2965) oder
            (nicht rfc2965_hdrs und nicht netscape) oder
            (nicht netscape und nicht rfc2965)):
            return []  # no relevant cookie headers: quick exit

        try:
            cookies = self._cookies_from_attrs_set(
                split_header_words(rfc2965_hdrs), request)
        except Exception:
            _warn_unhandled_exception()
            cookies = []

        wenn ns_hdrs und netscape:
            try:
                # RFC 2109 und Netscape cookies
                ns_cookies = self._cookies_from_attrs_set(
                    parse_ns_headers(ns_hdrs), request)
            except Exception:
                _warn_unhandled_exception()
                ns_cookies = []
            self._process_rfc2109_cookies(ns_cookies)

            # Look fuer Netscape cookies (from Set-Cookie headers) that match
            # corresponding RFC 2965 cookies (from Set-Cookie2 headers).
            # For each match, keep the RFC 2965 cookie und ignore the Netscape
            # cookie (RFC 2965 section 9.1).  Actually, RFC 2109 cookies are
            # bundled in mit the Netscape cookies fuer this purpose, which is
            # reasonable behaviour.
            wenn rfc2965:
                lookup = {}
                fuer cookie in cookies:
                    lookup[(cookie.domain, cookie.path, cookie.name)] = Nichts

                def no_matching_rfc2965(ns_cookie, lookup=lookup):
                    key = ns_cookie.domain, ns_cookie.path, ns_cookie.name
                    return key nicht in lookup
                ns_cookies = filter(no_matching_rfc2965, ns_cookies)

            wenn ns_cookies:
                cookies.extend(ns_cookies)

        return cookies

    def set_cookie_if_ok(self, cookie, request):
        """Set a cookie wenn policy says it's OK to do so."""
        self._cookies_lock.acquire()
        try:
            self._policy._now = self._now = int(time.time())

            wenn self._policy.set_ok(cookie, request):
                self.set_cookie(cookie)


        finally:
            self._cookies_lock.release()

    def set_cookie(self, cookie):
        """Set a cookie, without checking whether oder nicht it should be set."""
        c = self._cookies
        self._cookies_lock.acquire()
        try:
            wenn cookie.domain nicht in c: c[cookie.domain] = {}
            c2 = c[cookie.domain]
            wenn cookie.path nicht in c2: c2[cookie.path] = {}
            c3 = c2[cookie.path]
            c3[cookie.name] = cookie
        finally:
            self._cookies_lock.release()

    def extract_cookies(self, response, request):
        """Extract cookies von response, where allowable given the request."""
        _debug("extract_cookies: %s", response.info())
        self._cookies_lock.acquire()
        try:
            fuer cookie in self.make_cookies(response, request):
                wenn self._policy.set_ok(cookie, request):
                    _debug(" setting cookie: %s", cookie)
                    self.set_cookie(cookie)
        finally:
            self._cookies_lock.release()

    def clear(self, domain=Nichts, path=Nichts, name=Nichts):
        """Clear some cookies.

        Invoking this method without arguments will clear all cookies.  If
        given a single argument, only cookies belonging to that domain will be
        removed.  If given two arguments, cookies belonging to the specified
        path within that domain are removed.  If given three arguments, then
        the cookie mit the specified name, path und domain is removed.

        Raises KeyError wenn no matching cookie exists.

        """
        wenn name is nicht Nichts:
            wenn (domain is Nichts) oder (path is Nichts):
                raise ValueError(
                    "domain und path must be given to remove a cookie by name")
            del self._cookies[domain][path][name]
        sowenn path is nicht Nichts:
            wenn domain is Nichts:
                raise ValueError(
                    "domain must be given to remove cookies by path")
            del self._cookies[domain][path]
        sowenn domain is nicht Nichts:
            del self._cookies[domain]
        sonst:
            self._cookies = {}

    def clear_session_cookies(self):
        """Discard all session cookies.

        Note that the .save() method won't save session cookies anyway, unless
        you ask otherwise by passing a true ignore_discard argument.

        """
        self._cookies_lock.acquire()
        try:
            fuer cookie in self:
                wenn cookie.discard:
                    self.clear(cookie.domain, cookie.path, cookie.name)
        finally:
            self._cookies_lock.release()

    def clear_expired_cookies(self):
        """Discard all expired cookies.

        You probably don't need to call this method: expired cookies are never
        sent back to the server (provided you're using DefaultCookiePolicy),
        this method is called by CookieJar itself every so often, und the
        .save() method won't save expired cookies anyway (unless you ask
        otherwise by passing a true ignore_expires argument).

        """
        self._cookies_lock.acquire()
        try:
            now = time.time()
            fuer cookie in self:
                wenn cookie.is_expired(now):
                    self.clear(cookie.domain, cookie.path, cookie.name)
        finally:
            self._cookies_lock.release()

    def __iter__(self):
        return deepvalues(self._cookies)

    def __len__(self):
        """Return number of contained cookies."""
        i = 0
        fuer cookie in self: i = i + 1
        return i

    def __repr__(self):
        r = []
        fuer cookie in self: r.append(repr(cookie))
        return "<%s[%s]>" % (self.__class__.__name__, ", ".join(r))

    def __str__(self):
        r = []
        fuer cookie in self: r.append(str(cookie))
        return "<%s[%s]>" % (self.__class__.__name__, ", ".join(r))


# derives von OSError fuer backwards-compatibility mit Python 2.4.0
klasse LoadError(OSError): pass

klasse FileCookieJar(CookieJar):
    """CookieJar that can be loaded von und saved to a file."""

    def __init__(self, filename=Nichts, delayload=Falsch, policy=Nichts):
        """
        Cookies are NOT loaded von the named file until either the .load() oder
        .revert() method is called.

        """
        CookieJar.__init__(self, policy)
        wenn filename is nicht Nichts:
            filename = os.fspath(filename)
        self.filename = filename
        self.delayload = bool(delayload)

    def save(self, filename=Nichts, ignore_discard=Falsch, ignore_expires=Falsch):
        """Save cookies to a file."""
        raise NotImplementedError()

    def load(self, filename=Nichts, ignore_discard=Falsch, ignore_expires=Falsch):
        """Load cookies von a file."""
        wenn filename is Nichts:
            wenn self.filename is nicht Nichts: filename = self.filename
            sonst: raise ValueError(MISSING_FILENAME_TEXT)

        mit open(filename) als f:
            self._really_load(f, filename, ignore_discard, ignore_expires)

    def revert(self, filename=Nichts,
               ignore_discard=Falsch, ignore_expires=Falsch):
        """Clear all cookies und reload cookies von a saved file.

        Raises LoadError (or OSError) wenn reversion is nicht successful; the
        object's state will nicht be altered wenn this happens.

        """
        wenn filename is Nichts:
            wenn self.filename is nicht Nichts: filename = self.filename
            sonst: raise ValueError(MISSING_FILENAME_TEXT)

        self._cookies_lock.acquire()
        try:

            old_state = copy.deepcopy(self._cookies)
            self._cookies = {}
            try:
                self.load(filename, ignore_discard, ignore_expires)
            except OSError:
                self._cookies = old_state
                raise

        finally:
            self._cookies_lock.release()


def lwp_cookie_str(cookie):
    """Return string representation of Cookie in the LWP cookie file format.

    Actually, the format is extended a bit -- see module docstring.

    """
    h = [(cookie.name, cookie.value),
         ("path", cookie.path),
         ("domain", cookie.domain)]
    wenn cookie.port is nicht Nichts: h.append(("port", cookie.port))
    wenn cookie.path_specified: h.append(("path_spec", Nichts))
    wenn cookie.port_specified: h.append(("port_spec", Nichts))
    wenn cookie.domain_initial_dot: h.append(("domain_dot", Nichts))
    wenn cookie.secure: h.append(("secure", Nichts))
    wenn cookie.expires: h.append(("expires",
                               time2isoz(float(cookie.expires))))
    wenn cookie.discard: h.append(("discard", Nichts))
    wenn cookie.comment: h.append(("comment", cookie.comment))
    wenn cookie.comment_url: h.append(("commenturl", cookie.comment_url))

    keys = sorted(cookie._rest.keys())
    fuer k in keys:
        h.append((k, str(cookie._rest[k])))

    h.append(("version", str(cookie.version)))

    return join_header_words([h])

klasse LWPCookieJar(FileCookieJar):
    """
    The LWPCookieJar saves a sequence of "Set-Cookie3" lines.
    "Set-Cookie3" is the format used by the libwww-perl library, nicht known
    to be compatible mit any browser, but which is easy to read und
    doesn't lose information about RFC 2965 cookies.

    Additional methods

    as_lwp_str(ignore_discard=Wahr, ignore_expired=Wahr)

    """

    def as_lwp_str(self, ignore_discard=Wahr, ignore_expires=Wahr):
        """Return cookies als a string of "\\n"-separated "Set-Cookie3" headers.

        ignore_discard und ignore_expires: see docstring fuer FileCookieJar.save

        """
        now = time.time()
        r = []
        fuer cookie in self:
            wenn nicht ignore_discard und cookie.discard:
                continue
            wenn nicht ignore_expires und cookie.is_expired(now):
                continue
            r.append("Set-Cookie3: %s" % lwp_cookie_str(cookie))
        return "\n".join(r+[""])

    def save(self, filename=Nichts, ignore_discard=Falsch, ignore_expires=Falsch):
        wenn filename is Nichts:
            wenn self.filename is nicht Nichts: filename = self.filename
            sonst: raise ValueError(MISSING_FILENAME_TEXT)

        mit os.fdopen(
            os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600),
            'w',
        ) als f:
            # There really isn't an LWP Cookies 2.0 format, but this indicates
            # that there is extra information in here (domain_dot und
            # port_spec) while still being compatible mit libwww-perl, I hope.
            f.write("#LWP-Cookies-2.0\n")
            f.write(self.as_lwp_str(ignore_discard, ignore_expires))

    def _really_load(self, f, filename, ignore_discard, ignore_expires):
        magic = f.readline()
        wenn nicht self.magic_re.search(magic):
            msg = ("%r does nicht look like a Set-Cookie3 (LWP) format "
                   "file" % filename)
            raise LoadError(msg)

        now = time.time()

        header = "Set-Cookie3:"
        boolean_attrs = ("port_spec", "path_spec", "domain_dot",
                         "secure", "discard")
        value_attrs = ("version",
                       "port", "path", "domain",
                       "expires",
                       "comment", "commenturl")

        try:
            while (line := f.readline()) != "":
                wenn nicht line.startswith(header):
                    continue
                line = line[len(header):].strip()

                fuer data in split_header_words([line]):
                    name, value = data[0]
                    standard = {}
                    rest = {}
                    fuer k in boolean_attrs:
                        standard[k] = Falsch
                    fuer k, v in data[1:]:
                        wenn k is nicht Nichts:
                            lc = k.lower()
                        sonst:
                            lc = Nichts
                        # don't lose case distinction fuer unknown fields
                        wenn (lc in value_attrs) oder (lc in boolean_attrs):
                            k = lc
                        wenn k in boolean_attrs:
                            wenn v is Nichts: v = Wahr
                            standard[k] = v
                        sowenn k in value_attrs:
                            standard[k] = v
                        sonst:
                            rest[k] = v

                    h = standard.get
                    expires = h("expires")
                    discard = h("discard")
                    wenn expires is nicht Nichts:
                        expires = iso2time(expires)
                    wenn expires is Nichts:
                        discard = Wahr
                    domain = h("domain")
                    domain_specified = domain.startswith(".")
                    c = Cookie(h("version"), name, value,
                               h("port"), h("port_spec"),
                               domain, domain_specified, h("domain_dot"),
                               h("path"), h("path_spec"),
                               h("secure"),
                               expires,
                               discard,
                               h("comment"),
                               h("commenturl"),
                               rest)
                    wenn nicht ignore_discard und c.discard:
                        continue
                    wenn nicht ignore_expires und c.is_expired(now):
                        continue
                    self.set_cookie(c)
        except OSError:
            raise
        except Exception:
            _warn_unhandled_exception()
            raise LoadError("invalid Set-Cookie3 format file %r: %r" %
                            (filename, line))


klasse MozillaCookieJar(FileCookieJar):
    """

    WARNING: you may want to backup your browser's cookies file wenn you use
    this klasse to save cookies.  I *think* it works, but there have been
    bugs in the past!

    This klasse differs von CookieJar only in the format it uses to save und
    load cookies to und von a file.  This klasse uses the Mozilla/Netscape
    'cookies.txt' format.  curl und lynx use this file format, too.

    Don't expect cookies saved while the browser is running to be noticed by
    the browser (in fact, Mozilla on unix will overwrite your saved cookies if
    you change them on disk while it's running; on Windows, you probably can't
    save at all while the browser is running).

    Note that the Mozilla/Netscape format will downgrade RFC2965 cookies to
    Netscape cookies on saving.

    In particular, the cookie version und port number information is lost,
    together mit information about whether oder nicht Path, Port und Discard were
    specified by the Set-Cookie2 (or Set-Cookie) header, und whether oder nicht the
    domain als set in the HTTP header started mit a dot (yes, I'm aware some
    domains in Netscape files start mit a dot und some don't -- trust me, you
    really don't want to know any more about this).

    Note that though Mozilla und Netscape use the same format, they use
    slightly different headers.  The klasse saves cookies using the Netscape
    header by default (Mozilla can cope mit that).

    """

    def _really_load(self, f, filename, ignore_discard, ignore_expires):
        now = time.time()

        wenn nicht NETSCAPE_MAGIC_RGX.match(f.readline()):
            raise LoadError(
                "%r does nicht look like a Netscape format cookies file" %
                filename)

        try:
            while (line := f.readline()) != "":
                rest = {}

                # httponly is a cookie flag als defined in rfc6265
                # when encoded in a netscape cookie file,
                # the line is prepended mit "#HttpOnly_"
                wenn line.startswith(HTTPONLY_PREFIX):
                    rest[HTTPONLY_ATTR] = ""
                    line = line[len(HTTPONLY_PREFIX):]

                # last field may be absent, so keep any trailing tab
                wenn line.endswith("\n"): line = line[:-1]

                # skip comments und blank lines XXX what is $ for?
                wenn (line.strip().startswith(("#", "$")) oder
                    line.strip() == ""):
                    continue

                domain, domain_specified, path, secure, expires, name, value = \
                        line.split("\t")
                secure = (secure == "TRUE")
                domain_specified = (domain_specified == "TRUE")
                wenn name == "":
                    # cookies.txt regards 'Set-Cookie: foo' als a cookie
                    # mit no name, whereas http.cookiejar regards it als a
                    # cookie mit no value.
                    name = value
                    value = Nichts

                initial_dot = domain.startswith(".")
                assert domain_specified == initial_dot

                discard = Falsch
                wenn expires == "":
                    expires = Nichts
                    discard = Wahr

                # assume path_specified is false
                c = Cookie(0, name, value,
                           Nichts, Falsch,
                           domain, domain_specified, initial_dot,
                           path, Falsch,
                           secure,
                           expires,
                           discard,
                           Nichts,
                           Nichts,
                           rest)
                wenn nicht ignore_discard und c.discard:
                    continue
                wenn nicht ignore_expires und c.is_expired(now):
                    continue
                self.set_cookie(c)

        except OSError:
            raise
        except Exception:
            _warn_unhandled_exception()
            raise LoadError("invalid Netscape format cookies file %r: %r" %
                            (filename, line))

    def save(self, filename=Nichts, ignore_discard=Falsch, ignore_expires=Falsch):
        wenn filename is Nichts:
            wenn self.filename is nicht Nichts: filename = self.filename
            sonst: raise ValueError(MISSING_FILENAME_TEXT)

        mit os.fdopen(
            os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600),
            'w',
        ) als f:
            f.write(NETSCAPE_HEADER_TEXT)
            now = time.time()
            fuer cookie in self:
                domain = cookie.domain
                wenn nicht ignore_discard und cookie.discard:
                    continue
                wenn nicht ignore_expires und cookie.is_expired(now):
                    continue
                wenn cookie.secure: secure = "TRUE"
                sonst: secure = "FALSE"
                wenn domain.startswith("."): initial_dot = "TRUE"
                sonst: initial_dot = "FALSE"
                wenn cookie.expires is nicht Nichts:
                    expires = str(cookie.expires)
                sonst:
                    expires = ""
                wenn cookie.value is Nichts:
                    # cookies.txt regards 'Set-Cookie: foo' als a cookie
                    # mit no name, whereas http.cookiejar regards it als a
                    # cookie mit no value.
                    name = ""
                    value = cookie.name
                sonst:
                    name = cookie.name
                    value = cookie.value
                wenn cookie.has_nonstandard_attr(HTTPONLY_ATTR):
                    domain = HTTPONLY_PREFIX + domain
                f.write(
                    "\t".join([domain, initial_dot, cookie.path,
                               secure, expires, name, value])+
                    "\n")
