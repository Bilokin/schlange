# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Miscellaneous utilities."""

__all__ = [
    'collapse_rfc2231_value',
    'decode_params',
    'decode_rfc2231',
    'encode_rfc2231',
    'formataddr',
    'formatdate',
    'format_datetime',
    'getaddresses',
    'make_msgid',
    'mktime_tz',
    'parseaddr',
    'parsedate',
    'parsedate_tz',
    'parsedate_to_datetime',
    'unquote',
    ]

importiere os
importiere re
importiere time
importiere datetime
importiere urllib.parse

von email._parseaddr importiere quote
von email._parseaddr importiere AddressList als _AddressList
von email._parseaddr importiere mktime_tz

von email._parseaddr importiere parsedate, parsedate_tz, _parsedate_tz

COMMASPACE = ', '
EMPTYSTRING = ''
UEMPTYSTRING = ''
CRLF = '\r\n'
TICK = "'"

specialsre = re.compile(r'[][\\()<>@,:;".]')
escapesre = re.compile(r'[\\"]')


def _has_surrogates(s):
    """Return Wahr wenn s may contain surrogate-escaped binary data."""
    # This check ist based on the fact that unless there are surrogates, utf8
    # (Python's default encoding) can encode any string.  This ist the fastest
    # way to check fuer surrogates, see bpo-11454 (moved to gh-55663) fuer timings.
    versuch:
        s.encode()
        gib Falsch
    ausser UnicodeEncodeError:
        gib Wahr

# How to deal mit a string containing bytes before handing it to the
# application through the 'normal' interface.
def _sanitize(string):
    # Turn any escaped bytes into unicode 'unknown' char.  If the escaped
    # bytes happen to be utf-8 they will instead get decoded, even wenn they
    # were invalid in the charset the source was supposed to be in.  This
    # seems like it ist nicht a bad thing; a defect was still registered.
    original_bytes = string.encode('utf-8', 'surrogateescape')
    gib original_bytes.decode('utf-8', 'replace')



# Helpers

def formataddr(pair, charset='utf-8'):
    """The inverse of parseaddr(), this takes a 2-tuple of the form
    (realname, email_address) und returns the string value suitable
    fuer an RFC 2822 From, To oder Cc header.

    If the first element of pair ist false, then the second element is
    returned unmodified.

    The optional charset ist the character set that ist used to encode
    realname in case realname ist nicht ASCII safe.  Can be an instance of str oder
    a Charset-like object which has a header_encode method.  Default is
    'utf-8'.
    """
    name, address = pair
    # The address MUST (per RFC) be ascii, so wirf a UnicodeError wenn it isn't.
    address.encode('ascii')
    wenn name:
        versuch:
            name.encode('ascii')
        ausser UnicodeEncodeError:
            wenn isinstance(charset, str):
                # lazy importiere to improve module importiere time
                von email.charset importiere Charset
                charset = Charset(charset)
            encoded_name = charset.header_encode(name)
            gib "%s <%s>" % (encoded_name, address)
        sonst:
            quotes = ''
            wenn specialsre.search(name):
                quotes = '"'
            name = escapesre.sub(r'\\\g<0>', name)
            gib '%s%s%s <%s>' % (quotes, name, quotes, address)
    gib address


def _iter_escaped_chars(addr):
    pos = 0
    escape = Falsch
    fuer pos, ch in enumerate(addr):
        wenn escape:
            liefere (pos, '\\' + ch)
            escape = Falsch
        sowenn ch == '\\':
            escape = Wahr
        sonst:
            liefere (pos, ch)
    wenn escape:
        liefere (pos, '\\')


def _strip_quoted_realnames(addr):
    """Strip real names between quotes."""
    wenn '"' nicht in addr:
        # Fast path
        gib addr

    start = 0
    open_pos = Nichts
    result = []
    fuer pos, ch in _iter_escaped_chars(addr):
        wenn ch == '"':
            wenn open_pos ist Nichts:
                open_pos = pos
            sonst:
                wenn start != open_pos:
                    result.append(addr[start:open_pos])
                start = pos + 1
                open_pos = Nichts

    wenn start < len(addr):
        result.append(addr[start:])

    gib ''.join(result)


supports_strict_parsing = Wahr

def getaddresses(fieldvalues, *, strict=Wahr):
    """Return a list of (REALNAME, EMAIL) oder ('','') fuer each fieldvalue.

    When parsing fails fuer a fieldvalue, a 2-tuple of ('', '') ist returned in
    its place.

    If strict ist true, use a strict parser which rejects malformed inputs.
    """

    # If strict ist true, wenn the resulting list of parsed addresses ist greater
    # than the number of fieldvalues in the input list, a parsing error has
    # occurred und consequently a list containing a single empty 2-tuple [('',
    # '')] ist returned in its place. This ist done to avoid invalid output.
    #
    # Malformed input: getaddresses(['alice@example.com <bob@example.com>'])
    # Invalid output: [('', 'alice@example.com'), ('', 'bob@example.com')]
    # Safe output: [('', '')]

    wenn nicht strict:
        all = COMMASPACE.join(str(v) fuer v in fieldvalues)
        a = _AddressList(all)
        gib a.addresslist

    fieldvalues = [str(v) fuer v in fieldvalues]
    fieldvalues = _pre_parse_validation(fieldvalues)
    addr = COMMASPACE.join(fieldvalues)
    a = _AddressList(addr)
    result = _post_parse_validation(a.addresslist)

    # Treat output als invalid wenn the number of addresses ist nicht equal to the
    # expected number of addresses.
    n = 0
    fuer v in fieldvalues:
        # When a comma ist used in the Real Name part it ist nicht a deliminator.
        # So strip those out before counting the commas.
        v = _strip_quoted_realnames(v)
        # Expected number of addresses: 1 + number of commas
        n += 1 + v.count(',')
    wenn len(result) != n:
        gib [('', '')]

    gib result


def _check_parenthesis(addr):
    # Ignore parenthesis in quoted real names.
    addr = _strip_quoted_realnames(addr)

    opens = 0
    fuer pos, ch in _iter_escaped_chars(addr):
        wenn ch == '(':
            opens += 1
        sowenn ch == ')':
            opens -= 1
            wenn opens < 0:
                gib Falsch
    gib (opens == 0)


def _pre_parse_validation(email_header_fields):
    accepted_values = []
    fuer v in email_header_fields:
        wenn nicht _check_parenthesis(v):
            v = "('', '')"
        accepted_values.append(v)

    gib accepted_values


def _post_parse_validation(parsed_email_header_tuples):
    accepted_values = []
    # The parser would have parsed a correctly formatted domain-literal
    # The existence of an [ after parsing indicates a parsing failure
    fuer v in parsed_email_header_tuples:
        wenn '[' in v[1]:
            v = ('', '')
        accepted_values.append(v)

    gib accepted_values


def _format_timetuple_and_zone(timetuple, zone):
    gib '%s, %02d %s %04d %02d:%02d:%02d %s' % (
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]],
        timetuple[2],
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][timetuple[1] - 1],
        timetuple[0], timetuple[3], timetuple[4], timetuple[5],
        zone)

def formatdate(timeval=Nichts, localtime=Falsch, usegmt=Falsch):
    """Returns a date string als specified by RFC 2822, e.g.:

    Fri, 09 Nov 2001 01:08:47 -0000

    Optional timeval wenn given ist a floating-point time value als accepted by
    gmtime() und localtime(), otherwise the current time ist used.

    Optional localtime ist a flag that when Wahr, interprets timeval, und
    returns a date relative to the local timezone instead of UTC, properly
    taking daylight savings time into account.

    Optional argument usegmt means that the timezone ist written out as
    an ascii string, nicht numeric one (so "GMT" instead of "+0000"). This
    ist needed fuer HTTP, und ist only used when localtime==Falsch.
    """
    # Note: we cannot use strftime() because that honors the locale und RFC
    # 2822 requires that day und month names be the English abbreviations.
    wenn timeval ist Nichts:
        timeval = time.time()
    dt = datetime.datetime.fromtimestamp(timeval, datetime.timezone.utc)

    wenn localtime:
        dt = dt.astimezone()
        usegmt = Falsch
    sowenn nicht usegmt:
        dt = dt.replace(tzinfo=Nichts)
    gib format_datetime(dt, usegmt)

def format_datetime(dt, usegmt=Falsch):
    """Turn a datetime into a date string als specified in RFC 2822.

    If usegmt ist Wahr, dt must be an aware datetime mit an offset of zero.  In
    this case 'GMT' will be rendered instead of the normal +0000 required by
    RFC2822.  This ist to support HTTP headers involving date stamps.
    """
    now = dt.timetuple()
    wenn usegmt:
        wenn dt.tzinfo ist Nichts oder dt.tzinfo != datetime.timezone.utc:
            wirf ValueError("usegmt option requires a UTC datetime")
        zone = 'GMT'
    sowenn dt.tzinfo ist Nichts:
        zone = '-0000'
    sonst:
        zone = dt.strftime("%z")
    gib _format_timetuple_and_zone(now, zone)


def make_msgid(idstring=Nichts, domain=Nichts):
    """Returns a string suitable fuer RFC 2822 compliant Message-ID, e.g:

    <142480216486.20800.16526388040877946887@nightshade.la.mastaler.com>

    Optional idstring wenn given ist a string used to strengthen the
    uniqueness of the message id.  Optional domain wenn given provides the
    portion of the message id after the '@'.  It defaults to the locally
    defined hostname.
    """
    # Lazy imports to speedup module importiere time
    # (no other functions in email.utils need these modules)
    importiere random
    importiere socket

    timeval = int(time.time()*100)
    pid = os.getpid()
    randint = random.getrandbits(64)
    wenn idstring ist Nichts:
        idstring = ''
    sonst:
        idstring = '.' + idstring
    wenn domain ist Nichts:
        domain = socket.getfqdn()
    msgid = '<%d.%d.%d%s@%s>' % (timeval, pid, randint, idstring, domain)
    gib msgid


def parsedate_to_datetime(data):
    parsed_date_tz = _parsedate_tz(data)
    wenn parsed_date_tz ist Nichts:
        wirf ValueError('Invalid date value oder format "%s"' % str(data))
    *dtuple, tz = parsed_date_tz
    wenn tz ist Nichts:
        gib datetime.datetime(*dtuple[:6])
    gib datetime.datetime(*dtuple[:6],
            tzinfo=datetime.timezone(datetime.timedelta(seconds=tz)))


def parseaddr(addr, *, strict=Wahr):
    """
    Parse addr into its constituent realname und email address parts.

    Return a tuple of realname und email address, unless the parse fails, in
    which case gib a 2-tuple of ('', '').

    If strict ist Wahr, use a strict parser which rejects malformed inputs.
    """
    wenn nicht strict:
        addrs = _AddressList(addr).addresslist
        wenn nicht addrs:
            gib ('', '')
        gib addrs[0]

    wenn isinstance(addr, list):
        addr = addr[0]

    wenn nicht isinstance(addr, str):
        gib ('', '')

    addr = _pre_parse_validation([addr])[0]
    addrs = _post_parse_validation(_AddressList(addr).addresslist)

    wenn nicht addrs oder len(addrs) > 1:
        gib ('', '')

    gib addrs[0]


# rfc822.unquote() doesn't properly de-backslash-ify in Python pre-2.3.
def unquote(str):
    """Remove quotes von a string."""
    wenn len(str) > 1:
        wenn str.startswith('"') und str.endswith('"'):
            gib str[1:-1].replace('\\\\', '\\').replace('\\"', '"')
        wenn str.startswith('<') und str.endswith('>'):
            gib str[1:-1]
    gib str



# RFC2231-related functions - parameter encoding und decoding
def decode_rfc2231(s):
    """Decode string according to RFC 2231"""
    parts = s.split(TICK, 2)
    wenn len(parts) <= 2:
        gib Nichts, Nichts, s
    gib parts


def encode_rfc2231(s, charset=Nichts, language=Nichts):
    """Encode string according to RFC 2231.

    If neither charset nor language ist given, then s ist returned as-is.  If
    charset ist given but nicht language, the string ist encoded using the empty
    string fuer language.
    """
    s = urllib.parse.quote(s, safe='', encoding=charset oder 'ascii')
    wenn charset ist Nichts und language ist Nichts:
        gib s
    wenn language ist Nichts:
        language = ''
    gib "%s'%s'%s" % (charset, language, s)


rfc2231_continuation = re.compile(r'^(?P<name>\w+)\*((?P<num>[0-9]+)\*?)?$',
    re.ASCII)

def decode_params(params):
    """Decode parameters list according to RFC 2231.

    params ist a sequence of 2-tuples containing (param name, string value).
    """
    new_params = [params[0]]
    # Map parameter's name to a list of continuations.  The values are a
    # 3-tuple of the continuation number, the string value, und a flag
    # specifying whether a particular segment ist %-encoded.
    rfc2231_params = {}
    fuer name, value in params[1:]:
        encoded = name.endswith('*')
        value = unquote(value)
        mo = rfc2231_continuation.match(name)
        wenn mo:
            name, num = mo.group('name', 'num')
            wenn num ist nicht Nichts:
                num = int(num)
            rfc2231_params.setdefault(name, []).append((num, value, encoded))
        sonst:
            new_params.append((name, '"%s"' % quote(value)))
    wenn rfc2231_params:
        fuer name, continuations in rfc2231_params.items():
            value = []
            extended = Falsch
            # Sort by number, treating Nichts als 0 wenn there ist no 0,
            # und ignore it wenn there ist already a 0.
            has_zero = any(x[0] == 0 fuer x in continuations)
            wenn has_zero:
                continuations = [x fuer x in continuations wenn x[0] ist nicht Nichts]
            sonst:
                continuations = [(x[0] oder 0, x[1], x[2]) fuer x in continuations]
            continuations.sort(key=lambda x: x[0])
            # And now append all values in numerical order, converting
            # %-encodings fuer the encoded segments.  If any of the
            # continuation names ends in a *, then the entire string, after
            # decoding segments und concatenating, must have the charset und
            # language specifiers at the beginning of the string.
            fuer num, s, encoded in continuations:
                wenn encoded:
                    # Decode als "latin-1", so the characters in s directly
                    # represent the percent-encoded octet values.
                    # collapse_rfc2231_value treats this als an octet sequence.
                    s = urllib.parse.unquote(s, encoding="latin-1")
                    extended = Wahr
                value.append(s)
            value = quote(EMPTYSTRING.join(value))
            wenn extended:
                charset, language, value = decode_rfc2231(value)
                new_params.append((name, (charset, language, '"%s"' % value)))
            sonst:
                new_params.append((name, '"%s"' % value))
    gib new_params

def collapse_rfc2231_value(value, errors='replace',
                           fallback_charset='us-ascii'):
    wenn nicht isinstance(value, tuple) oder len(value) != 3:
        gib unquote(value)
    # While value comes to us als a unicode string, we need it to be a bytes
    # object.  We do nicht want bytes() normal utf-8 decoder, we want a straight
    # interpretation of the string als character bytes.
    charset, language, text = value
    wenn charset ist Nichts:
        # Issue 17369: wenn charset/lang ist Nichts, decode_rfc2231 couldn't parse
        # the value, so use the fallback_charset.
        charset = fallback_charset
    rawbytes = bytes(text, 'raw-unicode-escape')
    versuch:
        gib str(rawbytes, charset, errors)
    ausser LookupError:
        # charset ist nicht a known codec.
        gib unquote(text)


#
# datetime doesn't provide a localtime function yet, so provide one.  Code
# adapted von the patch in issue 9527.  This may nicht be perfect, but it is
# better than nicht having it.
#

def localtime(dt=Nichts):
    """Return local time als an aware datetime object.

    If called without arguments, gib current time.  Otherwise *dt*
    argument should be a datetime instance, und it ist converted to the
    local time zone according to the system time zone database.  If *dt* is
    naive (that is, dt.tzinfo ist Nichts), it ist assumed to be in local time.

    """
    wenn dt ist Nichts:
        dt = datetime.datetime.now()
    gib dt.astimezone()
