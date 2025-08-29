"""A parser fuer HTML und XHTML."""

# This file is based on sgmllib.py, but the API is slightly different.

# XXX There should be a way to distinguish between PCDATA (parsed
# character data -- the normal case), RCDATA (replaceable character
# data -- only char und entity references und end tags are special)
# und CDATA (character data -- only end tags are special).


importiere re
importiere _markupbase

von html importiere unescape
von html.entities importiere html5 als html5_entities


__all__ = ['HTMLParser']

# Regular expressions used fuer parsing

interesting_normal = re.compile('[&<]')
incomplete = re.compile('&[a-zA-Z#]')

entityref = re.compile('&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
charref = re.compile('&#(?:[0-9]+|[xX][0-9a-fA-F]+)[^0-9a-fA-F]')
attr_charref = re.compile(r'&(#[0-9]+|#[xX][0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*)[;=]?')

starttagopen = re.compile('<[a-zA-Z]')
endtagopen = re.compile('</[a-zA-Z]')
piclose = re.compile('>')
commentclose = re.compile(r'--!?>')
commentabruptclose = re.compile(r'-?>')
# Note:
#  1) wenn you change tagfind/attrfind remember to update locatetagend too;
#  2) wenn you change tagfind/attrfind and/or locatetagend the parser will
#     explode, so don't do it.
# see the HTML5 specs section "13.2.5.6 Tag open state",
# "13.2.5.8 Tag name state" und "13.2.5.33 Attribute name state".
# https://html.spec.whatwg.org/multipage/parsing.html#tag-open-state
# https://html.spec.whatwg.org/multipage/parsing.html#tag-name-state
# https://html.spec.whatwg.org/multipage/parsing.html#attribute-name-state
tagfind_tolerant = re.compile(r'([a-zA-Z][^\t\n\r\f />]*)(?:[\t\n\r\f ]|/(?!>))*')
attrfind_tolerant = re.compile(r"""
  (
    (?<=['"\t\n\r\f /])[^\t\n\r\f />][^\t\n\r\f /=>]*  # attribute name
   )
  ([\t\n\r\f ]*=[\t\n\r\f ]*        # value indicator
    ('[^']*'                        # LITA-enclosed value
    |"[^"]*"                        # LIT-enclosed value
    |(?!['"])[^>\t\n\r\f ]*         # bare value
    )
   )?
  (?:[\t\n\r\f ]|/(?!>))*           # possibly followed by a space
""", re.VERBOSE)
locatetagend = re.compile(r"""
  [a-zA-Z][^\t\n\r\f />]*           # tag name
  [\t\n\r\f /]*                     # optional whitespace before attribute name
  (?:(?<=['"\t\n\r\f /])[^\t\n\r\f />][^\t\n\r\f /=>]*  # attribute name
    (?:[\t\n\r\f ]*=[\t\n\r\f ]*    # value indicator
      (?:'[^']*'                    # LITA-enclosed value
        |"[^"]*"                    # LIT-enclosed value
        |(?!['"])[^>\t\n\r\f ]*     # bare value
       )
     )?
    [\t\n\r\f /]*                   # possibly followed by a space
   )*
   >?
""", re.VERBOSE)
# The following variables are nicht used, but are temporarily left for
# backward compatibility.
locatestarttagend_tolerant = re.compile(r"""
  <[a-zA-Z][^\t\n\r\f />\x00]*       # tag name
  (?:[\s/]*                          # optional whitespace before attribute name
    (?:(?<=['"\s/])[^\s/>][^\s/=>]*  # attribute name
      (?:\s*=+\s*                    # value indicator
        (?:'[^']*'                   # LITA-enclosed value
          |"[^"]*"                   # LIT-enclosed value
          |(?!['"])[^>\s]*           # bare value
         )
        \s*                          # possibly followed by a space
       )?(?:\s|/(?!>))*
     )*
   )?
  \s*                                # trailing whitespace
""", re.VERBOSE)
endendtag = re.compile('>')
endtagfind = re.compile(r'</\s*([a-zA-Z][-.a-zA-Z0-9:_]*)\s*>')

# Character reference processing logic specific to attribute values
# See: https://html.spec.whatwg.org/multipage/parsing.html#named-character-reference-state
def _replace_attr_charref(match):
    ref = match.group(0)
    # Numeric / hex char refs must always be unescaped
    wenn ref.startswith('&#'):
        gib unescape(ref)
    # Named character / entity references must only be unescaped
    # wenn they are an exact match, und they are nicht followed by an equals sign
    wenn nicht ref.endswith('=') und ref[1:] in html5_entities:
        gib unescape(ref)
    # Otherwise do nicht unescape
    gib ref

def _unescape_attrvalue(s):
    gib attr_charref.sub(_replace_attr_charref, s)


klasse HTMLParser(_markupbase.ParserBase):
    """Find tags und other markup und call handler functions.

    Usage:
        p = HTMLParser()
        p.feed(data)
        ...
        p.close()

    Start tags are handled by calling self.handle_starttag() oder
    self.handle_startendtag(); end tags by self.handle_endtag().  The
    data between tags is passed von the parser to the derived class
    by calling self.handle_data() mit the data als argument (the data
    may be split up in arbitrary chunks).  If convert_charrefs is
    Wahr the character references are converted automatically to the
    corresponding Unicode character (and self.handle_data() is no
    longer split in chunks), otherwise they are passed by calling
    self.handle_entityref() oder self.handle_charref() mit the string
    containing respectively the named oder numeric reference als the
    argument.
    """

    CDATA_CONTENT_ELEMENTS = ("script", "style")
    RCDATA_CONTENT_ELEMENTS = ("textarea", "title")

    def __init__(self, *, convert_charrefs=Wahr):
        """Initialize und reset this instance.

        If convert_charrefs is Wahr (the default), all character references
        are automatically converted to the corresponding Unicode characters.
        """
        super().__init__()
        self.convert_charrefs = convert_charrefs
        self.reset()

    def reset(self):
        """Reset this instance.  Loses all unprocessed data."""
        self.rawdata = ''
        self.lasttag = '???'
        self.interesting = interesting_normal
        self.cdata_elem = Nichts
        self._support_cdata = Wahr
        self._escapable = Wahr
        super().reset()

    def feed(self, data):
        r"""Feed data to the parser.

        Call this als often als you want, mit als little oder als much text
        als you want (may include '\n').
        """
        self.rawdata = self.rawdata + data
        self.goahead(0)

    def close(self):
        """Handle any buffered data."""
        self.goahead(1)

    __starttag_text = Nichts

    def get_starttag_text(self):
        """Return full source of start tag: '<...>'."""
        gib self.__starttag_text

    def set_cdata_mode(self, elem, *, escapable=Falsch):
        self.cdata_elem = elem.lower()
        self._escapable = escapable
        wenn escapable und nicht self.convert_charrefs:
            self.interesting = re.compile(r'&|</%s(?=[\t\n\r\f />])' % self.cdata_elem,
                                          re.IGNORECASE|re.ASCII)
        sonst:
            self.interesting = re.compile(r'</%s(?=[\t\n\r\f />])' % self.cdata_elem,
                                          re.IGNORECASE|re.ASCII)

    def clear_cdata_mode(self):
        self.interesting = interesting_normal
        self.cdata_elem = Nichts
        self._escapable = Wahr

    def _set_support_cdata(self, flag=Wahr):
        """Enable oder disable support of the CDATA sections.
        If enabled, "<[CDATA[" starts a CDATA section which ends mit "]]>".
        If disabled, "<[CDATA[" starts a bogus comments which ends mit ">".

        This method is nicht called by default. Its purpose is to be called
        in custom handle_starttag() und handle_endtag() methods, with
        value that depends on the adjusted current node.
        See https://html.spec.whatwg.org/multipage/parsing.html#markup-declaration-open-state
        fuer details.
        """
        self._support_cdata = flag

    # Internal -- handle data als far als reasonable.  May leave state
    # und data to be processed by a subsequent call.  If 'end' is
    # true, force handling all data als wenn followed by EOF marker.
    def goahead(self, end):
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        waehrend i < n:
            wenn self.convert_charrefs und nicht self.cdata_elem:
                j = rawdata.find('<', i)
                wenn j < 0:
                    # wenn we can't find the next <, either we are at the end
                    # oder there's more text incoming.  If the latter is Wahr,
                    # we can't pass the text to handle_data in case we have
                    # a charref cut in half at end.  Try to determine if
                    # this is the case before proceeding by looking fuer an
                    # & near the end und see wenn it's followed by a space oder ;.
                    amppos = rawdata.rfind('&', max(i, n-34))
                    wenn (amppos >= 0 und
                        nicht re.compile(r'[\t\n\r\f ;]').search(rawdata, amppos)):
                        breche  # wait till we get all the text
                    j = n
            sonst:
                match = self.interesting.search(rawdata, i)  # < oder &
                wenn match:
                    j = match.start()
                sonst:
                    wenn self.cdata_elem:
                        breche
                    j = n
            wenn i < j:
                wenn self.convert_charrefs und self._escapable:
                    self.handle_data(unescape(rawdata[i:j]))
                sonst:
                    self.handle_data(rawdata[i:j])
            i = self.updatepos(i, j)
            wenn i == n: breche
            startswith = rawdata.startswith
            wenn startswith('<', i):
                wenn starttagopen.match(rawdata, i): # < + letter
                    k = self.parse_starttag(i)
                sowenn startswith("</", i):
                    k = self.parse_endtag(i)
                sowenn startswith("<!--", i):
                    k = self.parse_comment(i)
                sowenn startswith("<?", i):
                    k = self.parse_pi(i)
                sowenn startswith("<!", i):
                    k = self.parse_html_declaration(i)
                sowenn (i + 1) < n oder end:
                    self.handle_data("<")
                    k = i + 1
                sonst:
                    breche
                wenn k < 0:
                    wenn nicht end:
                        breche
                    wenn starttagopen.match(rawdata, i):  # < + letter
                        pass
                    sowenn startswith("</", i):
                        wenn i + 2 == n:
                            self.handle_data("</")
                        sowenn endtagopen.match(rawdata, i):  # </ + letter
                            pass
                        sonst:
                            # bogus comment
                            self.handle_comment(rawdata[i+2:])
                    sowenn startswith("<!--", i):
                        j = n
                        fuer suffix in ("--!", "--", "-"):
                            wenn rawdata.endswith(suffix, i+4):
                                j -= len(suffix)
                                breche
                        self.handle_comment(rawdata[i+4:j])
                    sowenn startswith("<![CDATA[", i) und self._support_cdata:
                        self.unknown_decl(rawdata[i+3:])
                    sowenn rawdata[i:i+9].lower() == '<!doctype':
                        self.handle_decl(rawdata[i+2:])
                    sowenn startswith("<!", i):
                        # bogus comment
                        self.handle_comment(rawdata[i+2:])
                    sowenn startswith("<?", i):
                        self.handle_pi(rawdata[i+2:])
                    sonst:
                        raise AssertionError("we should nicht get here!")
                    k = n
                i = self.updatepos(i, k)
            sowenn startswith("&#", i):
                match = charref.match(rawdata, i)
                wenn match:
                    name = match.group()[2:-1]
                    self.handle_charref(name)
                    k = match.end()
                    wenn nicht startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    weiter
                sonst:
                    wenn ";" in rawdata[i:]:  # bail by consuming &#
                        self.handle_data(rawdata[i:i+2])
                        i = self.updatepos(i, i+2)
                    breche
            sowenn startswith('&', i):
                match = entityref.match(rawdata, i)
                wenn match:
                    name = match.group(1)
                    self.handle_entityref(name)
                    k = match.end()
                    wenn nicht startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    weiter
                match = incomplete.match(rawdata, i)
                wenn match:
                    # match.group() will contain at least 2 chars
                    wenn end und match.group() == rawdata[i:]:
                        k = match.end()
                        wenn k <= i:
                            k = n
                        i = self.updatepos(i, i + 1)
                    # incomplete
                    breche
                sowenn (i + 1) < n:
                    # nicht the end of the buffer, und can't be confused
                    # mit some other construct
                    self.handle_data("&")
                    i = self.updatepos(i, i + 1)
                sonst:
                    breche
            sonst:
                assert 0, "interesting.search() lied"
        # end while
        wenn end und i < n:
            wenn self.convert_charrefs und self._escapable:
                self.handle_data(unescape(rawdata[i:n]))
            sonst:
                self.handle_data(rawdata[i:n])
            i = self.updatepos(i, n)
        self.rawdata = rawdata[i:]

    # Internal -- parse html declarations, gib length oder -1 wenn nicht terminated
    # See w3.org/TR/html5/tokenization.html#markup-declaration-open-state
    # See also parse_declaration in _markupbase
    def parse_html_declaration(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i+2] == '<!', ('unexpected call to '
                                        'parse_html_declaration()')
        wenn rawdata[i:i+4] == '<!--':
            # this case is actually already handled in goahead()
            gib self.parse_comment(i)
        sowenn rawdata[i:i+9] == '<![CDATA[' und self._support_cdata:
            j = rawdata.find(']]>', i+9)
            wenn j < 0:
                gib -1
            self.unknown_decl(rawdata[i+3: j])
            gib j + 3
        sowenn rawdata[i:i+9].lower() == '<!doctype':
            # find the closing >
            gtpos = rawdata.find('>', i+9)
            wenn gtpos == -1:
                gib -1
            self.handle_decl(rawdata[i+2:gtpos])
            gib gtpos+1
        sonst:
            gib self.parse_bogus_comment(i)

    # Internal -- parse comment, gib length oder -1 wenn nicht terminated
    # see https://html.spec.whatwg.org/multipage/parsing.html#comment-start-state
    def parse_comment(self, i, report=Wahr):
        rawdata = self.rawdata
        assert rawdata.startswith('<!--', i), 'unexpected call to parse_comment()'
        match = commentclose.search(rawdata, i+4)
        wenn nicht match:
            match = commentabruptclose.match(rawdata, i+4)
            wenn nicht match:
                gib -1
        wenn report:
            j = match.start()
            self.handle_comment(rawdata[i+4: j])
        gib match.end()

    # Internal -- parse bogus comment, gib length oder -1 wenn nicht terminated
    # see https://html.spec.whatwg.org/multipage/parsing.html#bogus-comment-state
    def parse_bogus_comment(self, i, report=1):
        rawdata = self.rawdata
        assert rawdata[i:i+2] in ('<!', '</'), ('unexpected call to '
                                                'parse_bogus_comment()')
        pos = rawdata.find('>', i+2)
        wenn pos == -1:
            gib -1
        wenn report:
            self.handle_comment(rawdata[i+2:pos])
        gib pos + 1

    # Internal -- parse processing instr, gib end oder -1 wenn nicht terminated
    def parse_pi(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i+2] == '<?', 'unexpected call to parse_pi()'
        match = piclose.search(rawdata, i+2) # >
        wenn nicht match:
            gib -1
        j = match.start()
        self.handle_pi(rawdata[i+2: j])
        j = match.end()
        gib j

    # Internal -- handle starttag, gib end oder -1 wenn nicht terminated
    def parse_starttag(self, i):
        # See the HTML5 specs section "13.2.5.8 Tag name state"
        # https://html.spec.whatwg.org/multipage/parsing.html#tag-name-state
        self.__starttag_text = Nichts
        endpos = self.check_for_whole_start_tag(i)
        wenn endpos < 0:
            gib endpos
        rawdata = self.rawdata
        self.__starttag_text = rawdata[i:endpos]

        # Now parse the data between i+1 und j into a tag und attrs
        attrs = []
        match = tagfind_tolerant.match(rawdata, i+1)
        assert match, 'unexpected call to parse_starttag()'
        k = match.end()
        self.lasttag = tag = match.group(1).lower()
        waehrend k < endpos:
            m = attrfind_tolerant.match(rawdata, k)
            wenn nicht m:
                breche
            attrname, rest, attrvalue = m.group(1, 2, 3)
            wenn nicht rest:
                attrvalue = Nichts
            sowenn attrvalue[:1] == '\'' == attrvalue[-1:] oder \
                 attrvalue[:1] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
            wenn attrvalue:
                attrvalue = _unescape_attrvalue(attrvalue)
            attrs.append((attrname.lower(), attrvalue))
            k = m.end()

        end = rawdata[k:endpos].strip()
        wenn end nicht in (">", "/>"):
            self.handle_data(rawdata[i:endpos])
            gib endpos
        wenn end.endswith('/>'):
            # XHTML-style empty tag: <span attr="value" />
            self.handle_startendtag(tag, attrs)
        sonst:
            self.handle_starttag(tag, attrs)
            wenn tag in self.CDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag)
            sowenn tag in self.RCDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag, escapable=Wahr)
        gib endpos

    # Internal -- check to see wenn we have a complete starttag; gib end
    # oder -1 wenn incomplete.
    def check_for_whole_start_tag(self, i):
        rawdata = self.rawdata
        match = locatetagend.match(rawdata, i+1)
        assert match
        j = match.end()
        wenn rawdata[j-1] != ">":
            gib -1
        gib j

    # Internal -- parse endtag, gib end oder -1 wenn incomplete
    def parse_endtag(self, i):
        # See the HTML5 specs section "13.2.5.7 End tag open state"
        # https://html.spec.whatwg.org/multipage/parsing.html#end-tag-open-state
        rawdata = self.rawdata
        assert rawdata[i:i+2] == "</", "unexpected call to parse_endtag"
        wenn rawdata.find('>', i+2) < 0:  # fast check
            gib -1
        wenn nicht endtagopen.match(rawdata, i):  # </ + letter
            wenn rawdata[i+2:i+3] == '>':  # </> is ignored
                # "missing-end-tag-name" parser error
                gib i+3
            sonst:
                gib self.parse_bogus_comment(i)

        match = locatetagend.match(rawdata, i+2)
        assert match
        j = match.end()
        wenn rawdata[j-1] != ">":
            gib -1

        # find the name: "13.2.5.8 Tag name state"
        # https://html.spec.whatwg.org/multipage/parsing.html#tag-name-state
        match = tagfind_tolerant.match(rawdata, i+2)
        assert match
        tag = match.group(1).lower()
        self.handle_endtag(tag)
        self.clear_cdata_mode()
        gib j

    # Overridable -- finish processing of start+end tag: <tag.../>
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    # Overridable -- handle start tag
    def handle_starttag(self, tag, attrs):
        pass

    # Overridable -- handle end tag
    def handle_endtag(self, tag):
        pass

    # Overridable -- handle character reference
    def handle_charref(self, name):
        pass

    # Overridable -- handle entity reference
    def handle_entityref(self, name):
        pass

    # Overridable -- handle data
    def handle_data(self, data):
        pass

    # Overridable -- handle comment
    def handle_comment(self, data):
        pass

    # Overridable -- handle declaration
    def handle_decl(self, decl):
        pass

    # Overridable -- handle processing instruction
    def handle_pi(self, data):
        pass

    def unknown_decl(self, data):
        pass
