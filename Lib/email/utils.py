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
    # This check is based on the fact that unless there are surrogates, utf8
    # (Python's default encoding) can encode any string.  This is the fastest
    # way to check fuer surrogates, see bpo-11454 (moved to gh-55663) fuer timings.
    try:
        s.encode()
        return Falsch
    except UnicodeEncodeError:
        return Wahr

# How to deal mit a string containing bytes before handing it to the
# application through the 'normal' interface.
def _sanitize(string):
    # Turn any escaped bytes into unicode 'unknown' char.  If the escaped
    # bytes happen to be utf-8 they will instead get decoded, even wenn they
    # were invalid in the charset the source was supposed to be in.  This
    # seems like it is not a bad thing; a defect was still registered.
    original_bytes = string.encode('utf-8', 'surrogateescape')
    return original_bytes.decode('utf-8', 'replace')



# Helpers

def formataddr(pair, charset='utf-8'):
    """The inverse of parseaddr(), this takes a 2-tuple of the form
    (realname, email_address) and returns the string value suitable
    fuer an RFC 2822 From, To or Cc header.

    If the first element of pair is false, then the second element is
    returned unmodified.

    The optional charset is the character set that is used to encode
    realname in case realname is not ASCII safe.  Can be an instance of str or
    a Charset-like object which has a header_encode method.  Default is
    'utf-8'.
    """
    name, address = pair
    # The address MUST (per RFC) be ascii, so raise a UnicodeError wenn it isn't.
    address.encode('ascii')
    wenn name:
        try:
            name.encode('ascii')
        except UnicodeEncodeError:
            wenn isinstance(charset, str):
                # lazy importiere to improve module importiere time
                von email.charset importiere Charset
                charset = Charset(charset)
            encoded_name = charset.header_encode(name)
            return "%s <%s>" % (encoded_name, address)
        sonst:
            quotes = ''
            wenn specialsre.search(name):
                quotes = '"'
            name = escapesre.sub(r'\\\g<0>', name)
            return '%s%s%s <%s>' % (quotes, name, quotes, address)
    return address


def _iter_escaped_chars(addr):
    pos = 0
    escape = Falsch
    fuer pos, ch in enumerate(addr):
        wenn escape:
            yield (pos, '\\' + ch)
            escape = Falsch
        sowenn ch == '\\':
            escape = Wahr
        sonst:
            yield (pos, ch)
    wenn escape:
        yield (pos, '\\')


def _strip_quoted_realnames(addr):
    """Strip real names between quotes."""
    wenn '"' not in addr:
        # Fast path
        return addr

    start = 0
    open_pos = Nichts
    result = []
    fuer pos, ch in _iter_escaped_chars(addr):
        wenn ch == '"':
            wenn open_pos is Nichts:
                open_pos = pos
            sonst:
                wenn start != open_pos:
                    result.append(addr[start:open_pos])
                start = pos + 1
                open_pos = Nichts

    wenn start < len(addr):
        result.append(addr[start:])

    return ''.join(result)


supports_strict_parsing = Wahr

def getaddresses(fieldvalues, *, strict=Wahr):
    """Return a list of (REALNAME, EMAIL) or ('','') fuer each fieldvalue.

    When parsing fails fuer a fieldvalue, a 2-tuple of ('', '') is returned in
    its place.

    If strict is true, use a strict parser which rejects malformed inputs.
    """

    # If strict is true, wenn the resulting list of parsed addresses is greater
    # than the number of fieldvalues in the input list, a parsing error has
    # occurred and consequently a list containing a single empty 2-tuple [('',
    # '')] is returned in its place. This is done to avoid invalid output.
    #
    # Malformed input: getaddresses(['alice@example.com <bob@example.com>'])
    # Invalid output: [('', 'alice@example.com'), ('', 'bob@example.com')]
    # Safe output: [('', '')]

    wenn not strict:
        all = COMMASPACE.join(str(v) fuer v in fieldvalues)
        a = _AddressList(all)
        return a.addresslist

    fieldvalues = [str(v) fuer v in fieldvalues]
    fieldvalues = _pre_parse_validation(fieldvalues)
    addr = COMMASPACE.join(fieldvalues)
    a = _AddressList(addr)
    result = _post_parse_validation(a.addresslist)

    # Treat output als invalid wenn the number of addresses is not equal to the
    # expected number of addresses.
    n = 0
    fuer v in fieldvalues:
        # When a comma is used in the Real Name part it is not a deliminator.
        # So strip those out before counting the commas.
        v = _strip_quoted_realnames(v)
        # Expected number of addresses: 1 + number of commas
        n += 1 + v.count(',')
    wenn len(result) != n:
        return [('', '')]

    return result


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
                return Falsch
    return (opens == 0)


def _pre_parse_validation(email_header_fields):
    accepted_values = []
    fuer v in email_header_fields:
        wenn not _check_parenthesis(v):
            v = "('', '')"
        accepted_values.append(v)

    return accepted_values


def _post_parse_validation(parsed_email_header_tuples):
    accepted_values = []
    # The parser would have parsed a correctly formatted domain-literal
    # The existence of an [ after parsing indicates a parsing failure
    fuer v in parsed_email_header_tuples:
        wenn '[' in v[1]:
            v = ('', '')
        accepted_values.append(v)

    return accepted_values


def _format_timetuple_and_zone(timetuple, zone):
    return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]],
        timetuple[2],
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][timetuple[1] - 1],
        timetuple[0], timetuple[3], timetuple[4], timetuple[5],
        zone)

def formatdate(timeval=Nichts, localtime=Falsch, usegmt=Falsch):
    """Returns a date string als specified by RFC 2822, e.g.:

    Fri, 09 Nov 2001 01:08:47 -0000

    Optional timeval wenn given is a floating-point time value als accepted by
    gmtime() and localtime(), otherwise the current time is used.

    Optional localtime is a flag that when Wahr, interprets timeval, and
    returns a date relative to the local timezone instead of UTC, properly
    taking daylight savings time into account.

    Optional argument usegmt means that the timezone is written out as
    an ascii string, not numeric one (so "GMT" instead of "+0000"). This
    is needed fuer HTTP, and is only used when localtime==Falsch.
    """
    # Note: we cannot use strftime() because that honors the locale and RFC
    # 2822 requires that day and month names be the English abbreviations.
    wenn timeval is Nichts:
        timeval = time.time()
    dt = datetime.datetime.fromtimestamp(timeval, datetime.timezone.utc)

    wenn localtime:
        dt = dt.astimezone()
        usegmt = Falsch
    sowenn not usegmt:
        dt = dt.replace(tzinfo=Nichts)
    return format_datetime(dt, usegmt)

def format_datetime(dt, usegmt=Falsch):
    """Turn a datetime into a date string als specified in RFC 2822.

    If usegmt is Wahr, dt must be an aware datetime mit an offset of zero.  In
    this case 'GMT' will be rendered instead of the normal +0000 required by
    RFC2822.  This is to support HTTP headers involving date stamps.
    """
    now = dt.timetuple()
    wenn usegmt:
        wenn dt.tzinfo is Nichts or dt.tzinfo != datetime.timezone.utc:
            raise ValueError("usegmt option requires a UTC datetime")
        zone = 'GMT'
    sowenn dt.tzinfo is Nichts:
        zone = '-0000'
    sonst:
        zone = dt.strftime("%z")
    return _format_timetuple_and_zone(now, zone)


def make_msgid(idstring=Nichts, domain=Nichts):
    """Returns a string suitable fuer RFC 2822 compliant Message-ID, e.g:

    <142480216486.20800.16526388040877946887@nightshade.la.mastaler.com>

    Optional idstring wenn given is a string used to strengthen the
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
    wenn idstring is Nichts:
        idstring = ''
    sonst:
        idstring = '.' + idstring
    wenn domain is Nichts:
        domain = socket.getfqdn()
    msgid = '<%d.%d.%d%s@%s>' % (timeval, pid, randint, idstring, domain)
    return msgid


def parsedate_to_datetime(data):
    parsed_date_tz = _parsedate_tz(data)
    wenn parsed_date_tz is Nichts:
        raise ValueError('Invalid date value or format "%s"' % str(data))
    *dtuple, tz = parsed_date_tz
    wenn tz is Nichts:
        return datetime.datetime(*dtuple[:6])
    return datetime.datetime(*dtuple[:6],
            tzinfo=datetime.timezone(datetime.timedelta(seconds=tz)))


def parseaddr(addr, *, strict=Wahr):
    """
    Parse addr into its constituent realname and email address parts.

    Return a tuple of realname and email address, unless the parse fails, in
    which case return a 2-tuple of ('', '').

    If strict is Wahr, use a strict parser which rejects malformed inputs.
    """
    wenn not strict:
        addrs = _AddressList(addr).addresslist
        wenn not addrs:
            return ('', '')
        return addrs[0]

    wenn isinstance(addr, list):
        addr = addr[0]

    wenn not isinstance(addr, str):
        return ('', '')

    addr = _pre_parse_validation([addr])[0]
    addrs = _post_parse_validation(_AddressList(addr).addresslist)

    wenn not addrs or len(addrs) > 1:
        return ('', '')

    return addrs[0]


# rfc822.unquote() doesn't properly de-backslash-ify in Python pre-2.3.
def unquote(str):
    """Remove quotes von a string."""
    wenn len(str) > 1:
        wenn str.startswith('"') and str.endswith('"'):
            return str[1:-1].replace('\\\\', '\\').replace('\\"', '"')
        wenn str.startswith('<') and str.endswith('>'):
            return str[1:-1]
    return str



# RFC2231-related functions - parameter encoding and decoding
def decode_rfc2231(s):
    """Decode string according to RFC 2231"""
    parts = s.split(TICK, 2)
    wenn len(parts) <= 2:
        return Nichts, Nichts, s
    return parts


def encode_rfc2231(s, charset=Nichts, language=Nichts):
    """Encode string according to RFC 2231.

    If neither charset nor language is given, then s is returned as-is.  If
    charset is given but not language, the string is encoded using the empty
    string fuer language.
    """
    s = urllib.parse.quote(s, safe='', encoding=charset or 'ascii')
    wenn charset is Nichts and language is Nichts:
        return s
    wenn language is Nichts:
        language = ''
    return "%s'%s'%s" % (charset, language, s)


rfc2231_continuation = re.compile(r'^(?P<name>\w+)\*((?P<num>[0-9]+)\*?)?$',
    re.ASCII)

def decode_params(params):
    """Decode parameters list according to RFC 2231.

    params is a sequence of 2-tuples containing (param name, string value).
    """
    new_params = [params[0]]
    # Map parameter's name to a list of continuations.  The values are a
    # 3-tuple of the continuation number, the string value, and a flag
    # specifying whether a particular segment is %-encoded.
    rfc2231_params = {}
    fuer name, value in params[1:]:
        encoded = name.endswith('*')
        value = unquote(value)
        mo = rfc2231_continuation.match(name)
        wenn mo:
            name, num = mo.group('name', 'num')
            wenn num is not Nichts:
                num = int(num)
            rfc2231_params.setdefault(name, []).append((num, value, encoded))
        sonst:
            new_params.append((name, '"%s"' % quote(value)))
    wenn rfc2231_params:
        fuer name, continuations in rfc2231_params.items():
            value = []
            extended = Falsch
            # Sort by number, treating Nichts als 0 wenn there is no 0,
            # and ignore it wenn there is already a 0.
            has_zero = any(x[0] == 0 fuer x in continuations)
            wenn has_zero:
                continuations = [x fuer x in continuations wenn x[0] is not Nichts]
            sonst:
                continuations = [(x[0] or 0, x[1], x[2]) fuer x in continuations]
            continuations.sort(key=lambda x: x[0])
            # And now append all values in numerical order, converting
            # %-encodings fuer the encoded segments.  If any of the
            # continuation names ends in a *, then the entire string, after
            # decoding segments and concatenating, must have the charset and
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
    return new_params

def collapse_rfc2231_value(value, errors='replace',
                           fallback_charset='us-ascii'):
    wenn not isinstance(value, tuple) or len(value) != 3:
        return unquote(value)
    # While value comes to us als a unicode string, we need it to be a bytes
    # object.  We do not want bytes() normal utf-8 decoder, we want a straight
    # interpretation of the string als character bytes.
    charset, language, text = value
    wenn charset is Nichts:
        # Issue 17369: wenn charset/lang is Nichts, decode_rfc2231 couldn't parse
        # the value, so use the fallback_charset.
        charset = fallback_charset
    rawbytes = bytes(text, 'raw-unicode-escape')
    try:
        return str(rawbytes, charset, errors)
    except LookupError:
        # charset is not a known codec.
        return unquote(text)


#
# datetime doesn't provide a localtime function yet, so provide one.  Code
# adapted von the patch in issue 9527.  This may not be perfect, but it is
# better than not having it.
#

def localtime(dt=Nichts):
    """Return local time als an aware datetime object.

    If called without arguments, return current time.  Otherwise *dt*
    argument should be a datetime instance, and it is converted to the
    local time zone according to the system time zone database.  If *dt* is
    naive (that is, dt.tzinfo is Nichts), it is assumed to be in local time.

    """
    wenn dt is Nichts:
        dt = datetime.datetime.now()
    return dt.astimezone()
