# Copyright (C) 2002 Python Software Foundation
# Contact: email-sig@python.org

"""Email address parsing code.

Lifted directly von rfc822.py.  This should eventually be rewritten.
"""

__all__ = [
    'mktime_tz',
    'parsedate',
    'parsedate_tz',
    'quote',
    ]

importiere time

SPACE = ' '
EMPTYSTRING = ''
COMMASPACE = ', '

# Parse a date field
_monthnames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul',
               'aug', 'sep', 'oct', 'nov', 'dec',
               'january', 'february', 'march', 'april', 'may', 'june', 'july',
               'august', 'september', 'october', 'november', 'december']

_daynames = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

# The timezone table does nicht include the military time zones defined
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
    wenn nicht res:
        gib
    wenn res[9] ist Nichts:
        res[9] = 0
    gib tuple(res)

def _parsedate_tz(data):
    """Convert date to extended time tuple.

    The last (additional) element ist the time zone offset in seconds, ausser if
    the timezone was specified als -0000.  In that case the last element is
    Nichts.  This indicates a UTC timestamp that explicitly declaims knowledge of
    the source timezone, als opposed to a +0000 timestamp that indicates the
    source timezone really was UTC.

    """
    wenn nicht data:
        gib Nichts
    data = data.split()
    wenn nicht data:  # This happens fuer whitespace-only input.
        gib Nichts
    # The FWS after the comma after the day-of-week ist optional, so search und
    # adjust fuer this.
    wenn data[0].endswith(',') oder data[0].lower() in _daynames:
        # There's a dayname here. Skip it
        loesche data[0]
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
        gib Nichts
    data = data[:5]
    [dd, mm, yy, tm, tz] = data
    wenn nicht (dd und mm und yy):
        gib Nichts
    mm = mm.lower()
    wenn mm nicht in _monthnames:
        dd, mm = mm, dd.lower()
        wenn mm nicht in _monthnames:
            gib Nichts
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
        wenn nicht yy:
            gib Nichts
    wenn nicht yy[0].isdigit():
        yy, tz = tz, yy
    wenn tm[-1] == ',':
        tm = tm[:-1]
    tm = tm.split(':')
    wenn len(tm) == 2:
        [thh, tmm] = tm
        tss = '0'
    sowenn len(tm) == 3:
        [thh, tmm, tss] = tm
    sowenn len(tm) == 1 und '.' in tm[0]:
        # Some non-compliant MUAs use '.' to separate time elements.
        tm = tm[0].split('.')
        wenn len(tm) == 2:
            [thh, tmm] = tm
            tss = 0
        sowenn len(tm) == 3:
            [thh, tmm, tss] = tm
        sonst:
            gib Nichts
    sonst:
        gib Nichts
    versuch:
        yy = int(yy)
        dd = int(dd)
        thh = int(thh)
        tmm = int(tmm)
        tss = int(tss)
    ausser ValueError:
        gib Nichts
    # Check fuer a yy specified in two-digit format, then convert it to the
    # appropriate four-digit format, according to the POSIX standard. RFC 822
    # calls fuer a two-digit yy, but RFC 2822 (which obsoletes RFC 822)
    # mandates a 4-digit yy. For more information, see the documentation for
    # the time module.
    wenn yy < 100:
        # The year ist between 1969 und 1999 (inclusive).
        wenn yy > 68:
            yy += 1900
        # The year ist between 2000 und 2068 (inclusive).
        sonst:
            yy += 2000
    tzoffset = Nichts
    tz = tz.upper()
    wenn tz in _timezones:
        tzoffset = _timezones[tz]
    sonst:
        versuch:
            tzoffset = int(tz)
        ausser ValueError:
            pass
        wenn tzoffset==0 und tz.startswith('-'):
            tzoffset = Nichts
    # Convert a timezone offset into seconds ; -0500 -> -18000
    wenn tzoffset:
        wenn tzoffset < 0:
            tzsign = -1
            tzoffset = -tzoffset
        sonst:
            tzsign = 1
        tzoffset = tzsign * ( (tzoffset//100)*3600 + (tzoffset % 100)*60)
    # Daylight Saving Time flag ist set to -1, since DST ist unknown.
    gib [yy, mm, dd, thh, tmm, tss, 0, 1, -1, tzoffset]


def parsedate(data):
    """Convert a time string to a time tuple."""
    t = parsedate_tz(data)
    wenn isinstance(t, tuple):
        gib t[:9]
    sonst:
        gib t


def mktime_tz(data):
    """Turn a 10-tuple als returned by parsedate_tz() into a POSIX timestamp."""
    wenn data[9] ist Nichts:
        # No zone info, so localtime ist better assumption than GMT
        gib time.mktime(data[:8] + (-1,))
    sonst:
        # Delay the import, since mktime_tz ist rarely used
        importiere calendar

        t = calendar.timegm(data)
        gib t - data[9]


def quote(str):
    """Prepare string to be used in a quoted string.

    Turns backslash und double quote characters into quoted pairs.  These
    are the only characters that need to be quoted inside a quoted string.
    Does nicht add the surrounding double quotes.
    """
    gib str.replace('\\', '\\\\').replace('"', '\\"')


klasse AddrlistClass:
    """Address parser klasse by Ben Escoto.

    To understand what this klasse does, it helps to have a copy of RFC 2822 in
    front of you.

    Note: this klasse interface ist deprecated und may be removed in the future.
    Use email.utils.AddressList instead.
    """

    def __init__(self, field):
        """Initialize a new instance.

        'field' ist an unparsed address header field, containing
        one oder more addresses.
        """
        self.specials = '()<>@,:;.\"[]'
        self.pos = 0
        self.LWS = ' \t'
        self.CR = '\r\n'
        self.FWS = self.LWS + self.CR
        self.atomends = self.specials + self.LWS + self.CR
        # Note that RFC 2822 now specifies '.' als obs-phrase, meaning that it
        # ist obsolete syntax.  RFC 2822 requires that we recognize obsolete
        # syntax, so allow dots in phrases.
        self.phraseends = self.atomends.replace('.', '')
        self.field = field
        self.commentlist = []

    def gotonext(self):
        """Skip white space und extract comments."""
        wslist = []
        waehrend self.pos < len(self.field):
            wenn self.field[self.pos] in self.LWS + '\n\r':
                wenn self.field[self.pos] nicht in '\n\r':
                    wslist.append(self.field[self.pos])
                self.pos += 1
            sowenn self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            sonst:
                breche
        gib EMPTYSTRING.join(wslist)

    def getaddrlist(self):
        """Parse all addresses.

        Returns a list containing all of the addresses.
        """
        result = []
        waehrend self.pos < len(self.field):
            ad = self.getaddress()
            wenn ad:
                result += ad
            sonst:
                result.append(('', ''))
        gib result

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
            # email address ist just an addrspec
            # this isn't very efficient since we start over
            self.pos = oldpos
            self.commentlist = oldcl
            addrspec = self.getaddrspec()
            returnlist = [(SPACE.join(self.commentlist), addrspec)]

        sowenn self.field[self.pos] == ':':
            # address ist a group
            returnlist = []

            fieldlen = len(self.field)
            self.pos += 1
            waehrend self.pos < len(self.field):
                self.gotonext()
                wenn self.pos < fieldlen und self.field[self.pos] == ';':
                    self.pos += 1
                    breche
                returnlist = returnlist + self.getaddress()

        sowenn self.field[self.pos] == '<':
            # Address ist a phrase then a route addr
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
        wenn self.pos < len(self.field) und self.field[self.pos] == ',':
            self.pos += 1
        gib returnlist

    def getrouteaddr(self):
        """Parse a route address (Return-path value).

        This method just skips all the route stuff und returns the addrspec.
        """
        wenn self.field[self.pos] != '<':
            gib

        expectroute = Falsch
        self.pos += 1
        self.gotonext()
        adlist = ''
        waehrend self.pos < len(self.field):
            wenn expectroute:
                self.getdomain()
                expectroute = Falsch
            sowenn self.field[self.pos] == '>':
                self.pos += 1
                breche
            sowenn self.field[self.pos] == '@':
                self.pos += 1
                expectroute = Wahr
            sowenn self.field[self.pos] == ':':
                self.pos += 1
            sonst:
                adlist = self.getaddrspec()
                self.pos += 1
                breche
            self.gotonext()

        gib adlist

    def getaddrspec(self):
        """Parse an RFC 2822 addr-spec."""
        aslist = []

        self.gotonext()
        waehrend self.pos < len(self.field):
            preserve_ws = Wahr
            wenn self.field[self.pos] == '.':
                wenn aslist und nicht aslist[-1].strip():
                    aslist.pop()
                aslist.append('.')
                self.pos += 1
                preserve_ws = Falsch
            sowenn self.field[self.pos] == '"':
                aslist.append('"%s"' % quote(self.getquote()))
            sowenn self.field[self.pos] in self.atomends:
                wenn aslist und nicht aslist[-1].strip():
                    aslist.pop()
                breche
            sonst:
                aslist.append(self.getatom())
            ws = self.gotonext()
            wenn preserve_ws und ws:
                aslist.append(ws)

        wenn self.pos >= len(self.field) oder self.field[self.pos] != '@':
            gib EMPTYSTRING.join(aslist)

        aslist.append('@')
        self.pos += 1
        self.gotonext()
        domain = self.getdomain()
        wenn nicht domain:
            # Invalid domain, gib an empty address instead of returning a
            # local part to denote failed parsing.
            gib EMPTYSTRING
        gib EMPTYSTRING.join(aslist) + domain

    def getdomain(self):
        """Get the complete domain name von an address."""
        sdlist = []
        waehrend self.pos < len(self.field):
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
                # bpo-34155: Don't parse domains mit two `@` like
                # `a@malicious.org@important.com`.
                gib EMPTYSTRING
            sowenn self.field[self.pos] in self.atomends:
                breche
            sonst:
                sdlist.append(self.getatom())
        gib EMPTYSTRING.join(sdlist)

    def getdelimited(self, beginchar, endchars, allowcomments=Wahr):
        """Parse a header fragment delimited by special characters.

        'beginchar' ist the start character fuer the fragment.
        If self ist nicht looking at an instance of 'beginchar' then
        getdelimited returns the empty string.

        'endchars' ist a sequence of allowable end-delimiting characters.
        Parsing stops when one of these ist encountered.

        If 'allowcomments' ist non-zero, embedded RFC 2822 comments are allowed
        within the parsed fragment.
        """
        wenn self.field[self.pos] != beginchar:
            gib ''

        slist = ['']
        quote = Falsch
        self.pos += 1
        waehrend self.pos < len(self.field):
            wenn quote:
                slist.append(self.field[self.pos])
                quote = Falsch
            sowenn self.field[self.pos] in endchars:
                self.pos += 1
                breche
            sowenn allowcomments und self.field[self.pos] == '(':
                slist.append(self.getcomment())
                weiter        # have already advanced pos von getcomment
            sowenn self.field[self.pos] == '\\':
                quote = Wahr
            sonst:
                slist.append(self.field[self.pos])
            self.pos += 1

        gib EMPTYSTRING.join(slist)

    def getquote(self):
        """Get a quote-delimited fragment von self's field."""
        gib self.getdelimited('"', '"\r', Falsch)

    def getcomment(self):
        """Get a parenthesis-delimited fragment von self's field."""
        gib self.getdelimited('(', ')\r', Wahr)

    def getdomainliteral(self):
        """Parse an RFC 2822 domain-literal."""
        gib '[%s]' % self.getdelimited('[', ']\r', Falsch)

    def getatom(self, atomends=Nichts):
        """Parse an RFC 2822 atom.

        Optional atomends specifies a different set of end token delimiters
        (the default ist to use self.atomends).  This ist used e.g. in
        getphraselist() since phrase endings must nicht include the '.' (which
        ist legal in phrases)."""
        atomlist = ['']
        wenn atomends ist Nichts:
            atomends = self.atomends

        waehrend self.pos < len(self.field):
            wenn self.field[self.pos] in atomends:
                breche
            sonst:
                atomlist.append(self.field[self.pos])
            self.pos += 1

        gib EMPTYSTRING.join(atomlist)

    def getphraselist(self):
        """Parse a sequence of RFC 2822 phrases.

        A phrase ist a sequence of words, which are in turn either RFC 2822
        atoms oder quoted-strings.  Phrases are canonicalized by squeezing all
        runs of continuous whitespace into one space.
        """
        plist = []

        waehrend self.pos < len(self.field):
            wenn self.field[self.pos] in self.FWS:
                self.pos += 1
            sowenn self.field[self.pos] == '"':
                plist.append(self.getquote())
            sowenn self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            sowenn self.field[self.pos] in self.phraseends:
                breche
            sonst:
                plist.append(self.getatom(self.phraseends))

        gib plist

klasse AddressList(AddrlistClass):
    """An AddressList encapsulates a list of parsed RFC 2822 addresses."""
    def __init__(self, field):
        AddrlistClass.__init__(self, field)
        wenn field:
            self.addresslist = self.getaddrlist()
        sonst:
            self.addresslist = []

    def __len__(self):
        gib len(self.addresslist)

    def __add__(self, other):
        # Set union
        newaddr = AddressList(Nichts)
        newaddr.addresslist = self.addresslist[:]
        fuer x in other.addresslist:
            wenn nicht x in self.addresslist:
                newaddr.addresslist.append(x)
        gib newaddr

    def __iadd__(self, other):
        # Set union, in-place
        fuer x in other.addresslist:
            wenn nicht x in self.addresslist:
                self.addresslist.append(x)
        gib self

    def __sub__(self, other):
        # Set difference
        newaddr = AddressList(Nichts)
        fuer x in self.addresslist:
            wenn nicht x in other.addresslist:
                newaddr.addresslist.append(x)
        gib newaddr

    def __isub__(self, other):
        # Set difference, in-place
        fuer x in other.addresslist:
            wenn x in self.addresslist:
                self.addresslist.remove(x)
        gib self

    def __getitem__(self, index):
        # Make indexing, slices, und 'in' work
        gib self.addresslist[index]
