"""Shared support fuer scanning document type declarations in HTML und XHTML.

This module is used als a foundation fuer the html.parser module.  It has no
documented public API und should nicht be used directly.

"""

importiere re

_declname_match = re.compile(r'[a-zA-Z][-_.a-zA-Z0-9]*\s*').match
_declstringlit_match = re.compile(r'(\'[^\']*\'|"[^"]*")\s*').match
_commentclose = re.compile(r'--\s*>')
_markedsectionclose = re.compile(r']\s*]\s*>')

# An analysis of the MS-Word extensions is available at
# http://web.archive.org/web/20060321153828/http://www.planetpublish.com/xmlarena/xap/Thursday/WordtoXML.pdf

_msmarkedsectionclose = re.compile(r']\s*>')

del re


klasse ParserBase:
    """Parser base klasse which provides some common support methods used
    by the SGML/HTML und XHTML parsers."""

    def __init__(self):
        wenn self.__class__ is ParserBase:
            raise RuntimeError(
                "_markupbase.ParserBase must be subclassed")

    def reset(self):
        self.lineno = 1
        self.offset = 0

    def getpos(self):
        """Return current line number und offset."""
        gib self.lineno, self.offset

    # Internal -- update line number und offset.  This should be
    # called fuer each piece of data exactly once, in order -- in other
    # words the concatenation of all the input strings to this
    # function should be exactly the entire input.
    def updatepos(self, i, j):
        wenn i >= j:
            gib j
        rawdata = self.rawdata
        nlines = rawdata.count("\n", i, j)
        wenn nlines:
            self.lineno = self.lineno + nlines
            pos = rawdata.rindex("\n", i, j) # Should nicht fail
            self.offset = j-(pos+1)
        sonst:
            self.offset = self.offset + j-i
        gib j

    _decl_otherchars = ''

    # Internal -- parse declaration (for use by subclasses).
    def parse_declaration(self, i):
        # This is some sort of declaration; in "HTML as
        # deployed," this should only be the document type
        # declaration ("<!DOCTYPE html...>").
        # ISO 8879:1986, however, has more complex
        # declaration syntax fuer elements in <!...>, including:
        # --comment--
        # [marked section]
        # name in the following list: ENTITY, DOCTYPE, ELEMENT,
        # ATTLIST, NOTATION, SHORTREF, USEMAP,
        # LINKTYPE, LINK, IDLINK, USELINK, SYSTEM
        rawdata = self.rawdata
        j = i + 2
        assert rawdata[i:j] == "<!", "unexpected call to parse_declaration"
        wenn rawdata[j:j+1] == ">":
            # the empty comment <!>
            gib j + 1
        wenn rawdata[j:j+1] in ("-", ""):
            # Start of comment followed by buffer boundary,
            # oder just a buffer boundary.
            gib -1
        # A simple, practical version could look like: ((name|stringlit) S*) + '>'
        n = len(rawdata)
        wenn rawdata[j:j+2] == '--': #comment
            # Locate --.*-- als the body of the comment
            gib self.parse_comment(i)
        sowenn rawdata[j] == '[': #marked section
            # Locate [statusWord [...arbitrary SGML...]] als the body of the marked section
            # Where statusWord is one of TEMP, CDATA, IGNORE, INCLUDE, RCDATA
            # Note that this is extended by Microsoft Office "Save als Web" function
            # to include [if...] und [endif].
            gib self.parse_marked_section(i)
        sonst: #all other declaration elements
            decltype, j = self._scan_name(j, i)
        wenn j < 0:
            gib j
        wenn decltype == "doctype":
            self._decl_otherchars = ''
        waehrend j < n:
            c = rawdata[j]
            wenn c == ">":
                # end of declaration syntax
                data = rawdata[i+2:j]
                wenn decltype == "doctype":
                    self.handle_decl(data)
                sonst:
                    # According to the HTML5 specs sections "8.2.4.44 Bogus
                    # comment state" und "8.2.4.45 Markup declaration open
                    # state", a comment token should be emitted.
                    # Calling unknown_decl provides more flexibility though.
                    self.unknown_decl(data)
                gib j + 1
            wenn c in "\"'":
                m = _declstringlit_match(rawdata, j)
                wenn nicht m:
                    gib -1 # incomplete
                j = m.end()
            sowenn c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                name, j = self._scan_name(j, i)
            sowenn c in self._decl_otherchars:
                j = j + 1
            sowenn c == "[":
                # this could be handled in a separate doctype parser
                wenn decltype == "doctype":
                    j = self._parse_doctype_subset(j + 1, i)
                sowenn decltype in {"attlist", "linktype", "link", "element"}:
                    # must tolerate []'d groups in a content model in an element declaration
                    # also in data attribute specifications of attlist declaration
                    # also link type declaration subsets in linktype declarations
                    # also link attribute specification lists in link declarations
                    raise AssertionError("unsupported '[' char in %s declaration" % decltype)
                sonst:
                    raise AssertionError("unexpected '[' char in declaration")
            sonst:
                raise AssertionError("unexpected %r char in declaration" % rawdata[j])
            wenn j < 0:
                gib j
        gib -1 # incomplete

    # Internal -- parse a marked section
    # Override this to handle MS-word extension syntax <![if word]>content<![endif]>
    def parse_marked_section(self, i, report=1):
        rawdata= self.rawdata
        assert rawdata[i:i+3] == '<![', "unexpected call to parse_marked_section()"
        sectName, j = self._scan_name( i+3, i )
        wenn j < 0:
            gib j
        wenn sectName in {"temp", "cdata", "ignore", "include", "rcdata"}:
            # look fuer standard ]]> ending
            match= _markedsectionclose.search(rawdata, i+3)
        sowenn sectName in {"if", "else", "endif"}:
            # look fuer MS Office ]> ending
            match= _msmarkedsectionclose.search(rawdata, i+3)
        sonst:
            raise AssertionError(
                'unknown status keyword %r in marked section' % rawdata[i+3:j]
            )
        wenn nicht match:
            gib -1
        wenn report:
            j = match.start(0)
            self.unknown_decl(rawdata[i+3: j])
        gib match.end(0)

    # Internal -- parse comment, gib length oder -1 wenn nicht terminated
    def parse_comment(self, i, report=1):
        rawdata = self.rawdata
        wenn rawdata[i:i+4] != '<!--':
            raise AssertionError('unexpected call to parse_comment()')
        match = _commentclose.search(rawdata, i+4)
        wenn nicht match:
            gib -1
        wenn report:
            j = match.start(0)
            self.handle_comment(rawdata[i+4: j])
        gib match.end(0)

    # Internal -- scan past the internal subset in a <!DOCTYPE declaration,
    # returning the index just past any whitespace following the trailing ']'.
    def _parse_doctype_subset(self, i, declstartpos):
        rawdata = self.rawdata
        n = len(rawdata)
        j = i
        waehrend j < n:
            c = rawdata[j]
            wenn c == "<":
                s = rawdata[j:j+2]
                wenn s == "<":
                    # end of buffer; incomplete
                    gib -1
                wenn s != "<!":
                    self.updatepos(declstartpos, j + 1)
                    raise AssertionError(
                        "unexpected char in internal subset (in %r)" % s
                    )
                wenn (j + 2) == n:
                    # end of buffer; incomplete
                    gib -1
                wenn (j + 4) > n:
                    # end of buffer; incomplete
                    gib -1
                wenn rawdata[j:j+4] == "<!--":
                    j = self.parse_comment(j, report=0)
                    wenn j < 0:
                        gib j
                    weiter
                name, j = self._scan_name(j + 2, declstartpos)
                wenn j == -1:
                    gib -1
                wenn name nicht in {"attlist", "element", "entity", "notation"}:
                    self.updatepos(declstartpos, j + 2)
                    raise AssertionError(
                        "unknown declaration %r in internal subset" % name
                    )
                # handle the individual names
                meth = getattr(self, "_parse_doctype_" + name)
                j = meth(j, declstartpos)
                wenn j < 0:
                    gib j
            sowenn c == "%":
                # parameter entity reference
                wenn (j + 1) == n:
                    # end of buffer; incomplete
                    gib -1
                s, j = self._scan_name(j + 1, declstartpos)
                wenn j < 0:
                    gib j
                wenn rawdata[j] == ";":
                    j = j + 1
            sowenn c == "]":
                j = j + 1
                waehrend j < n und rawdata[j].isspace():
                    j = j + 1
                wenn j < n:
                    wenn rawdata[j] == ">":
                        gib j
                    self.updatepos(declstartpos, j)
                    raise AssertionError("unexpected char after internal subset")
                sonst:
                    gib -1
            sowenn c.isspace():
                j = j + 1
            sonst:
                self.updatepos(declstartpos, j)
                raise AssertionError("unexpected char %r in internal subset" % c)
        # end of buffer reached
        gib -1

    # Internal -- scan past <!ELEMENT declarations
    def _parse_doctype_element(self, i, declstartpos):
        name, j = self._scan_name(i, declstartpos)
        wenn j == -1:
            gib -1
        # style content model; just skip until '>'
        rawdata = self.rawdata
        wenn '>' in rawdata[j:]:
            gib rawdata.find(">", j) + 1
        gib -1

    # Internal -- scan past <!ATTLIST declarations
    def _parse_doctype_attlist(self, i, declstartpos):
        rawdata = self.rawdata
        name, j = self._scan_name(i, declstartpos)
        c = rawdata[j:j+1]
        wenn c == "":
            gib -1
        wenn c == ">":
            gib j + 1
        waehrend 1:
            # scan a series of attribute descriptions; simplified:
            #   name type [value] [#constraint]
            name, j = self._scan_name(j, declstartpos)
            wenn j < 0:
                gib j
            c = rawdata[j:j+1]
            wenn c == "":
                gib -1
            wenn c == "(":
                # an enumerated type; look fuer ')'
                wenn ")" in rawdata[j:]:
                    j = rawdata.find(")", j) + 1
                sonst:
                    gib -1
                waehrend rawdata[j:j+1].isspace():
                    j = j + 1
                wenn nicht rawdata[j:]:
                    # end of buffer, incomplete
                    gib -1
            sonst:
                name, j = self._scan_name(j, declstartpos)
            c = rawdata[j:j+1]
            wenn nicht c:
                gib -1
            wenn c in "'\"":
                m = _declstringlit_match(rawdata, j)
                wenn m:
                    j = m.end()
                sonst:
                    gib -1
                c = rawdata[j:j+1]
                wenn nicht c:
                    gib -1
            wenn c == "#":
                wenn rawdata[j:] == "#":
                    # end of buffer
                    gib -1
                name, j = self._scan_name(j + 1, declstartpos)
                wenn j < 0:
                    gib j
                c = rawdata[j:j+1]
                wenn nicht c:
                    gib -1
            wenn c == '>':
                # all done
                gib j + 1

    # Internal -- scan past <!NOTATION declarations
    def _parse_doctype_notation(self, i, declstartpos):
        name, j = self._scan_name(i, declstartpos)
        wenn j < 0:
            gib j
        rawdata = self.rawdata
        waehrend 1:
            c = rawdata[j:j+1]
            wenn nicht c:
                # end of buffer; incomplete
                gib -1
            wenn c == '>':
                gib j + 1
            wenn c in "'\"":
                m = _declstringlit_match(rawdata, j)
                wenn nicht m:
                    gib -1
                j = m.end()
            sonst:
                name, j = self._scan_name(j, declstartpos)
                wenn j < 0:
                    gib j

    # Internal -- scan past <!ENTITY declarations
    def _parse_doctype_entity(self, i, declstartpos):
        rawdata = self.rawdata
        wenn rawdata[i:i+1] == "%":
            j = i + 1
            waehrend 1:
                c = rawdata[j:j+1]
                wenn nicht c:
                    gib -1
                wenn c.isspace():
                    j = j + 1
                sonst:
                    breche
        sonst:
            j = i
        name, j = self._scan_name(j, declstartpos)
        wenn j < 0:
            gib j
        waehrend 1:
            c = self.rawdata[j:j+1]
            wenn nicht c:
                gib -1
            wenn c in "'\"":
                m = _declstringlit_match(rawdata, j)
                wenn m:
                    j = m.end()
                sonst:
                    gib -1    # incomplete
            sowenn c == ">":
                gib j + 1
            sonst:
                name, j = self._scan_name(j, declstartpos)
                wenn j < 0:
                    gib j

    # Internal -- scan a name token und the new position und the token, oder
    # gib -1 wenn we've reached the end of the buffer.
    def _scan_name(self, i, declstartpos):
        rawdata = self.rawdata
        n = len(rawdata)
        wenn i == n:
            gib Nichts, -1
        m = _declname_match(rawdata, i)
        wenn m:
            s = m.group()
            name = s.strip()
            wenn (i + len(s)) == n:
                gib Nichts, -1  # end of buffer
            gib name.lower(), m.end()
        sonst:
            self.updatepos(declstartpos, i)
            raise AssertionError(
                "expected name token at %r" % rawdata[declstartpos:declstartpos+20]
            )

    # To be overridden -- handlers fuer unknown objects
    def unknown_decl(self, data):
        pass
