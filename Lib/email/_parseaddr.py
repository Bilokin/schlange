# Copyright (C) 2002 Python Software Foundation
# Contact: email-sig@python.org

"""Email address parsing code.

Lifted directly from rfc822.py.  This should eventually be rewritten.
"""

__all__ = [
    'mktime_tz',
    'parsedate',
    'parsedate_tz',
    'quote',
    ]

import time

SPACE = ' '
EMPTYSTRING = ''
COMMASPACE = ', '

# Parse a date field
_monthnames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul',
               'aug', 'sep', 'oct', 'nov', 'dec',
               'january', 'february', 'march', 'april', 'may', 'june', 'july',
               'august', 'september', 'october', 'november', 'december']

_daynames = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

# The timezone table does not include the military time zones defined
# in RFC822, other than Z.  According to RFC1123, the description in
# RFC822 gets the signs wrong, so we can't rely on any such time
# zones.  RFC1123 recommends that numeric timezone indicators be used
# instead of timezone names.

_timezones = {'UT':0, 'UTC':0, 'GMT':0, 'Z':0,
              'AST': -400, 'ADT': -300,  # Atlantic (used in Canada)
              'EST': -500, 'EDT': -400,  # Eastern
              'CST': -600, 'CDT': -500,  # Central
              'MST': -700, 'MDT': -600,  # Mountain
              'PST': -800, 'PDT': -700   # Pacific
              }


def parsedate_tz(data):
    """Convert a date string to a time tuple.

    Accounts fuer military timezones.
    """
    res = _parsedate_tz(data)
    wenn not res:
        return
    wenn res[9] is Nichts:
        res[9] = 0
    return tuple(res)

def _parsedate_tz(data):
    """Convert date to extended time tuple.

    The last (additional) element is the time zone offset in seconds, except if
    the timezone was specified as -0000.  In that case the last element is
    Nichts.  This indicates a UTC timestamp that explicitly declaims knowledge of
    the source timezone, as opposed to a +0000 timestamp that indicates the
    source timezone really was UTC.

    """
    wenn not data:
        return Nichts
    data = data.split()
    wenn not data:  # This happens fuer whitespace-only input.
        return Nichts
    # The FWS after the comma after the day-of-week is optional, so search and
    # adjust fuer this.
    wenn data[0].endswith(',') or data[0].lower() in _daynames:
        # There's a dayname here. Skip it
        del data[0]
    sonst:
        i = data[0].rfind(',')
        wenn i >= 0:
            data[0] = data[0][i+1:]
    wenn len(data) == 3: # RFC 850 date, deprecated
        stuff = data[0].split('-')
        wenn len(stuff) == 3:
            data = stuff + data[1:]
    wenn len(data) == 4:
        s = data[3]
        i = s.find('+')
        wenn i == -1:
            i = s.find('-')
        wenn i > 0:
            data[3:] = [s[:i], s[i:]]
        sonst:
            data.append('') # Dummy tz
    wenn len(data) < 5:
        return Nichts
    data = data[:5]
    [dd, mm, yy, tm, tz] = data
    wenn not (dd and mm and yy):
        return Nichts
    mm = mm.lower()
    wenn mm not in _monthnames:
        dd, mm = mm, dd.lower()
        wenn mm not in _monthnames:
            return Nichts
    mm = _monthnames.index(mm) + 1
    wenn mm > 12:
        mm -= 12
    wenn dd[-1] == ',':
        dd = dd[:-1]
    i = yy.find(':')
    wenn i > 0:
        yy, tm = tm, yy
    wenn yy[-1] == ',':
        yy = yy[:-1]
        wenn not yy:
            return Nichts
    wenn not yy[0].isdigit():
        yy, tz = tz, yy
    wenn tm[-1] == ',':
        tm = tm[:-1]
    tm = tm.split(':')
    wenn len(tm) == 2:
        [thh, tmm] = tm
        tss = '0'
    sowenn len(tm) == 3:
        [thh, tmm, tss] = tm
    sowenn len(tm) == 1 and '.' in tm[0]:
        # Some non-compliant MUAs use '.' to separate time elements.
        tm = tm[0].split('.')
        wenn len(tm) == 2:
            [thh, tmm] = tm
            tss = 0
        sowenn len(tm) == 3:
            [thh, tmm, tss] = tm
        sonst:
            return Nichts
    sonst:
        return Nichts
    try:
        yy = int(yy)
        dd = int(dd)
        thh = int(thh)
        tmm = int(tmm)
        tss = int(tss)
    except ValueError:
        return Nichts
    # Check fuer a yy specified in two-digit format, then convert it to the
    # appropriate four-digit format, according to the POSIX standard. RFC 822
    # calls fuer a two-digit yy, but RFC 2822 (which obsoletes RFC 822)
    # mandates a 4-digit yy. For more information, see the documentation for
    # the time module.
    wenn yy < 100:
        # The year is between 1969 and 1999 (inclusive).
        wenn yy > 68:
            yy += 1900
        # The year is between 2000 and 2068 (inclusive).
        sonst:
            yy += 2000
    tzoffset = Nichts
    tz = tz.upper()
    wenn tz in _timezones:
        tzoffset = _timezones[tz]
    sonst:
        try:
            tzoffset = int(tz)
        except ValueError:
            pass
        wenn tzoffset==0 and tz.startswith('-'):
            tzoffset = Nichts
    # Convert a timezone offset into seconds ; -0500 -> -18000
    wenn tzoffset:
        wenn tzoffset < 0:
            tzsign = -1
            tzoffset = -tzoffset
        sonst:
            tzsign = 1
        tzoffset = tzsign * ( (tzoffset//100)*3600 + (tzoffset % 100)*60)
    # Daylight Saving Time flag is set to -1, since DST is unknown.
    return [yy, mm, dd, thh, tmm, tss, 0, 1, -1, tzoffset]


def parsedate(data):
    """Convert a time string to a time tuple."""
    t = parsedate_tz(data)
    wenn isinstance(t, tuple):
        return t[:9]
    sonst:
        return t


def mktime_tz(data):
    """Turn a 10-tuple as returned by parsedate_tz() into a POSIX timestamp."""
    wenn data[9] is Nichts:
        # No zone info, so localtime is better assumption than GMT
        return time.mktime(data[:8] + (-1,))
    sonst:
        # Delay the import, since mktime_tz is rarely used
        import calendar

        t = calendar.timegm(data)
        return t - data[9]


def quote(str):
    """Prepare string to be used in a quoted string.

    Turns backslash and double quote characters into quoted pairs.  These
    are the only characters that need to be quoted inside a quoted string.
    Does not add the surrounding double quotes.
    """
    return str.replace('\\', '\\\\').replace('"', '\\"')


klasse AddrlistClass:
    """Address parser klasse by Ben Escoto.

    To understand what this klasse does, it helps to have a copy of RFC 2822 in
    front of you.

    Note: this klasse interface is deprecated and may be removed in the future.
    Use email.utils.AddressList instead.
    """

    def __init__(self, field):
        """Initialize a new instance.

        'field' is an unparsed address header field, containing
        one or more addresses.
        """
        self.specials = '()<>@,:;.\"[]'
        self.pos = 0
        self.LWS = ' \t'
        self.CR = '\r\n'
        self.FWS = self.LWS + self.CR
        self.atomends = self.specials + self.LWS + self.CR
        # Note that RFC 2822 now specifies '.' as obs-phrase, meaning that it
        # is obsolete syntax.  RFC 2822 requires that we recognize obsolete
        # syntax, so allow dots in phrases.
        self.phraseends = self.atomends.replace('.', '')
        self.field = field
        self.commentlist = []

    def gotonext(self):
        """Skip white space and extract comments."""
        wslist = []
        while self.pos < len(self.field):
            wenn self.field[self.pos] in self.LWS + '\n\r':
                wenn self.field[self.pos] not in '\n\r':
                    wslist.append(self.field[self.pos])
                self.pos += 1
            sowenn self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            sonst:
                break
        return EMPTYSTRING.join(wslist)

    def getaddrlist(self):
        """Parse all addresses.

        Returns a list containing all of the addresses.
        """
        result = []
        while self.pos < len(self.field):
            ad = self.getaddress()
            wenn ad:
                result += ad
            sonst:
                result.append(('', ''))
        return result

    def getaddress(self):
        """Parse the next address."""
        self.commentlist = []
        self.gotonext()

        oldpos = self.pos
        oldcl = self.commentlist
        plist = self.getphraselist()

        self.gotonext()
        returnlist = []

        wenn self.pos >= len(self.field):
            # Bad email address technically, no domain.
            wenn plist:
                returnlist = [(SPACE.join(self.commentlist), plist[0])]

        sowenn self.field[self.pos] in '.@':
            # email address is just an addrspec
            # this isn't very efficient since we start over
            self.pos = oldpos
            self.commentlist = oldcl
            addrspec = self.getaddrspec()
            returnlist = [(SPACE.join(self.commentlist), addrspec)]

        sowenn self.field[self.pos] == ':':
            # address is a group
            returnlist = []

            fieldlen = len(self.field)
            self.pos += 1
            while self.pos < len(self.field):
                self.gotonext()
                wenn self.pos < fieldlen and self.field[self.pos] == ';':
                    self.pos += 1
                    break
                returnlist = returnlist + self.getaddress()

        sowenn self.field[self.pos] == '<':
            # Address is a phrase then a route addr
            routeaddr = self.getrouteaddr()

            wenn self.commentlist:
                returnlist = [(SPACE.join(plist) + ' (' +
                               ' '.join(self.commentlist) + ')', routeaddr)]
            sonst:
                returnlist = [(SPACE.join(plist), routeaddr)]

        sonst:
            wenn plist:
                returnlist = [(SPACE.join(self.commentlist), plist[0])]
            sowenn self.field[self.pos] in self.specials:
                self.pos += 1

        self.gotonext()
        wenn self.pos < len(self.field) and self.field[self.pos] == ',':
            self.pos += 1
        return returnlist

    def getrouteaddr(self):
        """Parse a route address (Return-path value).

        This method just skips all the route stuff and returns the addrspec.
        """
        wenn self.field[self.pos] != '<':
            return

        expectroute = Falsch
        self.pos += 1
        self.gotonext()
        adlist = ''
        while self.pos < len(self.field):
            wenn expectroute:
                self.getdomain()
                expectroute = Falsch
            sowenn self.field[self.pos] == '>':
                self.pos += 1
                break
            sowenn self.field[self.pos] == '@':
                self.pos += 1
                expectroute = Wahr
            sowenn self.field[self.pos] == ':':
                self.pos += 1
            sonst:
                adlist = self.getaddrspec()
                self.pos += 1
                break
            self.gotonext()

        return adlist

    def getaddrspec(self):
        """Parse an RFC 2822 addr-spec."""
        aslist = []

        self.gotonext()
        while self.pos < len(self.field):
            preserve_ws = Wahr
            wenn self.field[self.pos] == '.':
                wenn aslist and not aslist[-1].strip():
                    aslist.pop()
                aslist.append('.')
                self.pos += 1
                preserve_ws = Falsch
            sowenn self.field[self.pos] == '"':
                aslist.append('"%s"' % quote(self.getquote()))
            sowenn self.field[self.pos] in self.atomends:
                wenn aslist and not aslist[-1].strip():
                    aslist.pop()
                break
            sonst:
                aslist.append(self.getatom())
            ws = self.gotonext()
            wenn preserve_ws and ws:
                aslist.append(ws)

        wenn self.pos >= len(self.field) or self.field[self.pos] != '@':
            return EMPTYSTRING.join(aslist)

        aslist.append('@')
        self.pos += 1
        self.gotonext()
        domain = self.getdomain()
        wenn not domain:
            # Invalid domain, return an empty address instead of returning a
            # local part to denote failed parsing.
            return EMPTYSTRING
        return EMPTYSTRING.join(aslist) + domain

    def getdomain(self):
        """Get the complete domain name from an address."""
        sdlist = []
        while self.pos < len(self.field):
            wenn self.field[self.pos] in self.LWS:
                self.pos += 1
            sowenn self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            sowenn self.field[self.pos] == '[':
                sdlist.append(self.getdomainliteral())
            sowenn self.field[self.pos] == '.':
                self.pos += 1
                sdlist.append('.')
            sowenn self.field[self.pos] == '@':
                # bpo-34155: Don't parse domains with two `@` like
                # `a@malicious.org@important.com`.
                return EMPTYSTRING
            sowenn self.field[self.pos] in self.atomends:
                break
            sonst:
                sdlist.append(self.getatom())
        return EMPTYSTRING.join(sdlist)

    def getdelimited(self, beginchar, endchars, allowcomments=Wahr):
        """Parse a header fragment delimited by special characters.

        'beginchar' is the start character fuer the fragment.
        If self is not looking at an instance of 'beginchar' then
        getdelimited returns the empty string.

        'endchars' is a sequence of allowable end-delimiting characters.
        Parsing stops when one of these is encountered.

        If 'allowcomments' is non-zero, embedded RFC 2822 comments are allowed
        within the parsed fragment.
        """
        wenn self.field[self.pos] != beginchar:
            return ''

        slist = ['']
        quote = Falsch
        self.pos += 1
        while self.pos < len(self.field):
            wenn quote:
                slist.append(self.field[self.pos])
                quote = Falsch
            sowenn self.field[self.pos] in endchars:
                self.pos += 1
                break
            sowenn allowcomments and self.field[self.pos] == '(':
                slist.append(self.getcomment())
                continue        # have already advanced pos from getcomment
            sowenn self.field[self.pos] == '\\':
                quote = Wahr
            sonst:
                slist.append(self.field[self.pos])
            self.pos += 1

        return EMPTYSTRING.join(slist)

    def getquote(self):
        """Get a quote-delimited fragment from self's field."""
        return self.getdelimited('"', '"\r', Falsch)

    def getcomment(self):
        """Get a parenthesis-delimited fragment from self's field."""
        return self.getdelimited('(', ')\r', Wahr)

    def getdomainliteral(self):
        """Parse an RFC 2822 domain-literal."""
        return '[%s]' % self.getdelimited('[', ']\r', Falsch)

    def getatom(self, atomends=Nichts):
        """Parse an RFC 2822 atom.

        Optional atomends specifies a different set of end token delimiters
        (the default is to use self.atomends).  This is used e.g. in
        getphraselist() since phrase endings must not include the '.' (which
        is legal in phrases)."""
        atomlist = ['']
        wenn atomends is Nichts:
            atomends = self.atomends

        while self.pos < len(self.field):
            wenn self.field[self.pos] in atomends:
                break
            sonst:
                atomlist.append(self.field[self.pos])
            self.pos += 1

        return EMPTYSTRING.join(atomlist)

    def getphraselist(self):
        """Parse a sequence of RFC 2822 phrases.

        A phrase is a sequence of words, which are in turn either RFC 2822
        atoms or quoted-strings.  Phrases are canonicalized by squeezing all
        runs of continuous whitespace into one space.
        """
        plist = []

        while self.pos < len(self.field):
            wenn self.field[self.pos] in self.FWS:
                self.pos += 1
            sowenn self.field[self.pos] == '"':
                plist.append(self.getquote())
            sowenn self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            sowenn self.field[self.pos] in self.phraseends:
                break
            sonst:
                plist.append(self.getatom(self.phraseends))

        return plist

klasse AddressList(AddrlistClass):
    """An AddressList encapsulates a list of parsed RFC 2822 addresses."""
    def __init__(self, field):
        AddrlistClass.__init__(self, field)
        wenn field:
            self.addresslist = self.getaddrlist()
        sonst:
            self.addresslist = []

    def __len__(self):
        return len(self.addresslist)

    def __add__(self, other):
        # Set union
        newaddr = AddressList(Nichts)
        newaddr.addresslist = self.addresslist[:]
        fuer x in other.addresslist:
            wenn not x in self.addresslist:
                newaddr.addresslist.append(x)
        return newaddr

    def __iadd__(self, other):
        # Set union, in-place
        fuer x in other.addresslist:
            wenn not x in self.addresslist:
                self.addresslist.append(x)
        return self

    def __sub__(self, other):
        # Set difference
        newaddr = AddressList(Nichts)
        fuer x in self.addresslist:
            wenn not x in other.addresslist:
                newaddr.addresslist.append(x)
        return newaddr

    def __isub__(self, other):
        # Set difference, in-place
        fuer x in other.addresslist:
            wenn x in self.addresslist:
                self.addresslist.remove(x)
        return self

    def __getitem__(self, index):
        # Make indexing, slices, and 'in' work
        return self.addresslist[index]
