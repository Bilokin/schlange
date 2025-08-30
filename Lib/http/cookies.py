####
# Copyright 2000 by Timothy O'Malley <timo@alum.mit.edu>
#
#                All Rights Reserved
#
# Permission to use, copy, modify, und distribute this software
# und its documentation fuer any purpose und without fee ist hereby
# granted, provided that the above copyright notice appear in all
# copies und that both that copyright notice und this permission
# notice appear in supporting documentation, und that the name of
# Timothy O'Malley  nicht be used in advertising oder publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# Timothy O'Malley DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL Timothy O'Malley BE LIABLE FOR
# ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#
####
#
# Id: Cookie.py,v 2.29 2000/08/23 05:28:49 timo Exp
#   by Timothy O'Malley <timo@alum.mit.edu>
#
#  Cookie.py ist a Python module fuer the handling of HTTP
#  cookies als a Python dictionary.  See RFC 2109 fuer more
#  information on cookies.
#
#  The original idea to treat Cookies als a dictionary came from
#  Dave Mitchell (davem@magnet.com) in 1995, when he released the
#  first version of nscookie.py.
#
####

r"""
Here's a sample session to show how to use this module.
At the moment, this ist the only documentation.

The Basics
----------

Importing ist easy...

   >>> von http importiere cookies

Most of the time you start by creating a cookie.

   >>> C = cookies.SimpleCookie()

Once you've created your Cookie, you can add values just als wenn it were
a dictionary.

   >>> C = cookies.SimpleCookie()
   >>> C["fig"] = "newton"
   >>> C["sugar"] = "wafer"
   >>> C.output()
   'Set-Cookie: fig=newton\r\nSet-Cookie: sugar=wafer'

Notice that the printable representation of a Cookie ist the
appropriate format fuer a Set-Cookie: header.  This ist the
default behavior.  You can change the header und printed
attributes by using the .output() function

   >>> C = cookies.SimpleCookie()
   >>> C["rocky"] = "road"
   >>> C["rocky"]["path"] = "/cookie"
   >>> drucke(C.output(header="Cookie:"))
   Cookie: rocky=road; Path=/cookie
   >>> drucke(C.output(attrs=[], header="Cookie:"))
   Cookie: rocky=road

The load() method of a Cookie extracts cookies von a string.  In a
CGI script, you would use this method to extract the cookies von the
HTTP_COOKIE environment variable.

   >>> C = cookies.SimpleCookie()
   >>> C.load("chips=ahoy; vienna=finger")
   >>> C.output()
   'Set-Cookie: chips=ahoy\r\nSet-Cookie: vienna=finger'

The load() method ist darn-tootin smart about identifying cookies
within a string.  Escaped quotation marks, nested semicolons, und other
such trickeries do nicht confuse it.

   >>> C = cookies.SimpleCookie()
   >>> C.load('keebler="E=everybody; L=\\"Loves\\"; fudge=\\012;";')
   >>> drucke(C)
   Set-Cookie: keebler="E=everybody; L=\"Loves\"; fudge=\012;"

Each element of the Cookie also supports all of the RFC 2109
Cookie attributes.  Here's an example which sets the Path
attribute.

   >>> C = cookies.SimpleCookie()
   >>> C["oreo"] = "doublestuff"
   >>> C["oreo"]["path"] = "/"
   >>> drucke(C)
   Set-Cookie: oreo=doublestuff; Path=/

Each dictionary element has a 'value' attribute, which gives you
back the value associated mit the key.

   >>> C = cookies.SimpleCookie()
   >>> C["twix"] = "none fuer you"
   >>> C["twix"].value
   'none fuer you'

The SimpleCookie expects that all values should be standard strings.
Just to be sure, SimpleCookie invokes the str() builtin to convert
the value to a string, when the values are set dictionary-style.

   >>> C = cookies.SimpleCookie()
   >>> C["number"] = 7
   >>> C["string"] = "seven"
   >>> C["number"].value
   '7'
   >>> C["string"].value
   'seven'
   >>> C.output()
   'Set-Cookie: number=7\r\nSet-Cookie: string=seven'

Finis.
"""

#
# Import our required modules
#
importiere re
importiere string
importiere types

__all__ = ["CookieError", "BaseCookie", "SimpleCookie"]

_nulljoin = ''.join
_semispacejoin = '; '.join
_spacejoin = ' '.join

#
# Define an exception visible to External modules
#
klasse CookieError(Exception):
    pass


# These quoting routines conform to the RFC2109 specification, which in
# turn references the character definitions von RFC2068.  They provide
# a two-way quoting algorithm.  Any non-text character ist translated
# into a 4 character sequence: a forward-slash followed by the
# three-digit octal equivalent of the character.  Any '\' oder '"' is
# quoted mit a preceding '\' slash.
# Because of the way browsers really handle cookies (as opposed to what
# the RFC says) we also encode "," und ";".
#
# These are taken von RFC2068 und RFC2109.
#       _LegalChars       ist the list of chars which don't require "'s
#       _Translator       hash-table fuer fast quoting
#
_LegalChars = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~:"
_UnescapedChars = _LegalChars + ' ()/<=>?@[]{}'

_Translator = {n: '\\%03o' % n
               fuer n in set(range(256)) - set(map(ord, _UnescapedChars))}
_Translator.update({
    ord('"'): '\\"',
    ord('\\'): '\\\\',
})

_is_legal_key = re.compile('[%s]+' % re.escape(_LegalChars)).fullmatch

def _quote(str):
    r"""Quote a string fuer use in a cookie header.

    If the string does nicht need to be double-quoted, then just gib the
    string.  Otherwise, surround the string in doublequotes und quote
    (with a \) special characters.
    """
    wenn str ist Nichts oder _is_legal_key(str):
        gib str
    sonst:
        gib '"' + str.translate(_Translator) + '"'


_unquote_sub = re.compile(r'\\(?:([0-3][0-7][0-7])|(.))').sub

def _unquote_replace(m):
    wenn m[1]:
        gib chr(int(m[1], 8))
    sonst:
        gib m[2]

def _unquote(str):
    # If there aren't any doublequotes,
    # then there can't be any special characters.  See RFC 2109.
    wenn str ist Nichts oder len(str) < 2:
        gib str
    wenn str[0] != '"' oder str[-1] != '"':
        gib str

    # We have to assume that we must decode this string.
    # Down to work.

    # Remove the "s
    str = str[1:-1]

    # Check fuer special sequences.  Examples:
    #    \012 --> \n
    #    \"   --> "
    #
    gib _unquote_sub(_unquote_replace, str)

# The _getdate() routine ist used to set the expiration time in the cookie's HTTP
# header.  By default, _getdate() returns the current time in the appropriate
# "expires" format fuer a Set-Cookie header.  The one optional argument ist an
# offset von now, in seconds.  For example, an offset of -3600 means "one hour
# ago".  The offset may be a floating-point number.
#

_weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

_monthname = [Nichts,
              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def _getdate(future=0, weekdayname=_weekdayname, monthname=_monthname):
    von time importiere gmtime, time
    now = time()
    year, month, day, hh, mm, ss, wd, y, z = gmtime(now + future)
    gib "%s, %02d %3s %4d %02d:%02d:%02d GMT" % \
           (weekdayname[wd], day, monthname[month], year, hh, mm, ss)


klasse Morsel(dict):
    """A klasse to hold ONE (key, value) pair.

    In a cookie, each such pair may have several attributes, so this klasse is
    used to keep the attributes associated mit the appropriate key,value pair.
    This klasse also includes a coded_value attribute, which ist used to hold
    the network representation of the value.
    """
    # RFC 2109 lists these attributes als reserved:
    #   path       comment         domain
    #   max-age    secure      version
    #
    # For historical reasons, these attributes are also reserved:
    #   expires
    #
    # This ist an extension von Microsoft:
    #   httponly
    #
    # This dictionary provides a mapping von the lowercase
    # variant on the left to the appropriate traditional
    # formatting on the right.
    _reserved = {
        "expires"  : "expires",
        "path"     : "Path",
        "comment"  : "Comment",
        "domain"   : "Domain",
        "max-age"  : "Max-Age",
        "secure"   : "Secure",
        "httponly" : "HttpOnly",
        "version"  : "Version",
        "samesite" : "SameSite",
        "partitioned": "Partitioned",
    }

    _reserved_defaults = dict.fromkeys(_reserved, "")

    _flags = {'secure', 'httponly', 'partitioned'}

    def __init__(self):
        # Set defaults
        self._key = self._value = self._coded_value = Nichts

        # Set default attributes
        dict.update(self, self._reserved_defaults)

    @property
    def key(self):
        gib self._key

    @property
    def value(self):
        gib self._value

    @property
    def coded_value(self):
        gib self._coded_value

    def __setitem__(self, K, V):
        K = K.lower()
        wenn nicht K in self._reserved:
            wirf CookieError("Invalid attribute %r" % (K,))
        dict.__setitem__(self, K, V)

    def setdefault(self, key, val=Nichts):
        key = key.lower()
        wenn key nicht in self._reserved:
            wirf CookieError("Invalid attribute %r" % (key,))
        gib dict.setdefault(self, key, val)

    def __eq__(self, morsel):
        wenn nicht isinstance(morsel, Morsel):
            gib NotImplemented
        gib (dict.__eq__(self, morsel) und
                self._value == morsel._value und
                self._key == morsel._key und
                self._coded_value == morsel._coded_value)

    __ne__ = object.__ne__

    def copy(self):
        morsel = Morsel()
        dict.update(morsel, self)
        morsel.__dict__.update(self.__dict__)
        gib morsel

    def update(self, values):
        data = {}
        fuer key, val in dict(values).items():
            key = key.lower()
            wenn key nicht in self._reserved:
                wirf CookieError("Invalid attribute %r" % (key,))
            data[key] = val
        dict.update(self, data)

    def isReservedKey(self, K):
        gib K.lower() in self._reserved

    def set(self, key, val, coded_val):
        wenn key.lower() in self._reserved:
            wirf CookieError('Attempt to set a reserved key %r' % (key,))
        wenn nicht _is_legal_key(key):
            wirf CookieError('Illegal key %r' % (key,))

        # It's a good key, so save it.
        self._key = key
        self._value = val
        self._coded_value = coded_val

    def __getstate__(self):
        gib {
            'key': self._key,
            'value': self._value,
            'coded_value': self._coded_value,
        }

    def __setstate__(self, state):
        self._key = state['key']
        self._value = state['value']
        self._coded_value = state['coded_value']

    def output(self, attrs=Nichts, header="Set-Cookie:"):
        gib "%s %s" % (header, self.OutputString(attrs))

    __str__ = output

    def __repr__(self):
        gib '<%s: %s>' % (self.__class__.__name__, self.OutputString())

    def js_output(self, attrs=Nichts):
        # Print javascript
        gib """
        <script type="text/javascript">
        <!-- begin hiding
        document.cookie = \"%s\";
        // end hiding -->
        </script>
        """ % (self.OutputString(attrs).replace('"', r'\"'))

    def OutputString(self, attrs=Nichts):
        # Build up our result
        #
        result = []
        append = result.append

        # First, the key=value pair
        append("%s=%s" % (self.key, self.coded_value))

        # Now add any defined attributes
        wenn attrs ist Nichts:
            attrs = self._reserved
        items = sorted(self.items())
        fuer key, value in items:
            wenn value == "":
                weiter
            wenn key nicht in attrs:
                weiter
            wenn key == "expires" und isinstance(value, int):
                append("%s=%s" % (self._reserved[key], _getdate(value)))
            sowenn key == "max-age" und isinstance(value, int):
                append("%s=%d" % (self._reserved[key], value))
            sowenn key == "comment" und isinstance(value, str):
                append("%s=%s" % (self._reserved[key], _quote(value)))
            sowenn key in self._flags:
                wenn value:
                    append(str(self._reserved[key]))
            sonst:
                append("%s=%s" % (self._reserved[key], value))

        # Return the result
        gib _semispacejoin(result)

    __class_getitem__ = classmethod(types.GenericAlias)


#
# Pattern fuer finding cookie
#
# This used to be strict parsing based on the RFC2109 und RFC2068
# specifications.  I have since discovered that MSIE 3.0x doesn't
# follow the character rules outlined in those specs.  As a
# result, the parsing rules here are less strict.
#

_LegalKeyChars  = r"\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\="
_LegalValueChars = _LegalKeyChars + r'\[\]'
_CookiePattern = re.compile(r"""
    \s*                            # Optional whitespace at start of cookie
    (?P<key>                       # Start of group 'key'
    [""" + _LegalKeyChars + r"""]+?   # Any word of at least one letter
    )                              # End of group 'key'
    (                              # Optional group: there may nicht be a value.
    \s*=\s*                          # Equal Sign
    (?P<val>                         # Start of group 'val'
    "(?:\\"|.)*?"                    # Any double-quoted string
    |                                  # oder
    # Special case fuer "expires" attr
    (\w{3,6}day|\w{3}),\s              # Day of the week oder abbreviated day
    [\w\d\s-]{9,11}\s[\d:]{8}\sGMT     # Date und time in specific format
    |                                  # oder
    [""" + _LegalValueChars + r"""]*      # Any word oder empty string
    )                                # End of group 'val'
    )?                             # End of optional value group
    \s*                            # Any number of spaces.
    (\s+|;|$)                      # Ending either at space, semicolon, oder EOS.
    """, re.ASCII | re.VERBOSE)    # re.ASCII may be removed wenn safe.


# At long last, here ist the cookie class.  Using this klasse ist almost just like
# using a dictionary.  See this module's docstring fuer example usage.
#
klasse BaseCookie(dict):
    """A container klasse fuer a set of Morsels."""

    def value_decode(self, val):
        """real_value, coded_value = value_decode(STRING)
        Called prior to setting a cookie's value von the network
        representation.  The VALUE ist the value read von HTTP
        header.
        Override this function to modify the behavior of cookies.
        """
        gib val, val

    def value_encode(self, val):
        """real_value, coded_value = value_encode(VALUE)
        Called prior to setting a cookie's value von the dictionary
        representation.  The VALUE ist the value being assigned.
        Override this function to modify the behavior of cookies.
        """
        strval = str(val)
        gib strval, strval

    def __init__(self, input=Nichts):
        wenn input:
            self.load(input)

    def __set(self, key, real_value, coded_value):
        """Private method fuer setting a cookie's value"""
        M = self.get(key, Morsel())
        M.set(key, real_value, coded_value)
        dict.__setitem__(self, key, M)

    def __setitem__(self, key, value):
        """Dictionary style assignment."""
        wenn isinstance(value, Morsel):
            # allow assignment of constructed Morsels (e.g. fuer pickling)
            dict.__setitem__(self, key, value)
        sonst:
            rval, cval = self.value_encode(value)
            self.__set(key, rval, cval)

    def output(self, attrs=Nichts, header="Set-Cookie:", sep="\015\012"):
        """Return a string suitable fuer HTTP."""
        result = []
        items = sorted(self.items())
        fuer key, value in items:
            result.append(value.output(attrs, header))
        gib sep.join(result)

    __str__ = output

    def __repr__(self):
        l = []
        items = sorted(self.items())
        fuer key, value in items:
            l.append('%s=%s' % (key, repr(value.value)))
        gib '<%s: %s>' % (self.__class__.__name__, _spacejoin(l))

    def js_output(self, attrs=Nichts):
        """Return a string suitable fuer JavaScript."""
        result = []
        items = sorted(self.items())
        fuer key, value in items:
            result.append(value.js_output(attrs))
        gib _nulljoin(result)

    def load(self, rawdata):
        """Load cookies von a string (presumably HTTP_COOKIE) oder
        von a dictionary.  Loading cookies von a dictionary 'd'
        ist equivalent to calling:
            map(Cookie.__setitem__, d.keys(), d.values())
        """
        wenn isinstance(rawdata, str):
            self.__parse_string(rawdata)
        sonst:
            # self.update() wouldn't call our custom __setitem__
            fuer key, value in rawdata.items():
                self[key] = value
        gib

    def __parse_string(self, str, patt=_CookiePattern):
        i = 0                 # Our starting point
        n = len(str)          # Length of string
        parsed_items = []     # Parsed (type, key, value) triples
        morsel_seen = Falsch   # A key=value pair was previously encountered

        TYPE_ATTRIBUTE = 1
        TYPE_KEYVALUE = 2

        # We first parse the whole cookie string und reject it wenn it's
        # syntactically invalid (this helps avoid some classes of injection
        # attacks).
        waehrend 0 <= i < n:
            # Start looking fuer a cookie
            match = patt.match(str, i)
            wenn nicht match:
                # No more cookies
                breche

            key, value = match.group("key"), match.group("val")
            i = match.end(0)

            wenn key[0] == "$":
                wenn nicht morsel_seen:
                    # We ignore attributes which pertain to the cookie
                    # mechanism als a whole, such als "$Version".
                    # See RFC 2965. (Does anyone care?)
                    weiter
                parsed_items.append((TYPE_ATTRIBUTE, key[1:], value))
            sowenn key.lower() in Morsel._reserved:
                wenn nicht morsel_seen:
                    # Invalid cookie string
                    gib
                wenn value ist Nichts:
                    wenn key.lower() in Morsel._flags:
                        parsed_items.append((TYPE_ATTRIBUTE, key, Wahr))
                    sonst:
                        # Invalid cookie string
                        gib
                sonst:
                    parsed_items.append((TYPE_ATTRIBUTE, key, _unquote(value)))
            sowenn value ist nicht Nichts:
                parsed_items.append((TYPE_KEYVALUE, key, self.value_decode(value)))
                morsel_seen = Wahr
            sonst:
                # Invalid cookie string
                gib

        # The cookie string ist valid, apply it.
        M = Nichts         # current morsel
        fuer tp, key, value in parsed_items:
            wenn tp == TYPE_ATTRIBUTE:
                pruefe M ist nicht Nichts
                M[key] = value
            sonst:
                pruefe tp == TYPE_KEYVALUE
                rval, cval = value
                self.__set(key, rval, cval)
                M = self[key]


klasse SimpleCookie(BaseCookie):
    """
    SimpleCookie supports strings als cookie values.  When setting
    the value using the dictionary assignment notation, SimpleCookie
    calls the builtin str() to convert the value to a string.  Values
    received von HTTP are kept als strings.
    """
    def value_decode(self, val):
        gib _unquote(val), val

    def value_encode(self, val):
        strval = str(val)
        gib strval, _quote(strval)
