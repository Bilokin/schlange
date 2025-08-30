"""Lightweight XML support fuer Python.

 XML is an inherently hierarchical data format, und the most natural way to
 represent it is mit a tree.  This module has two classes fuer this purpose:

    1. ElementTree represents the whole XML document als a tree und

    2. Element represents a single node in this tree.

 Interactions mit the whole document (reading und writing to/from files) are
 usually done on the ElementTree level.  Interactions mit a single XML element
 und its sub-elements are done on the Element level.

 Element is a flexible container object designed to store hierarchical data
 structures in memory. It can be described als a cross between a list und a
 dictionary.  Each Element has a number of properties associated mit it:

    'tag' - a string containing the element's name.

    'attributes' - a Python dictionary storing the element's attributes.

    'text' - a string containing the element's text content.

    'tail' - an optional string containing text after the element's end tag.

    And a number of child elements stored in a Python sequence.

 To create an element instance, use the Element constructor,
 oder the SubElement factory function.

 You can also use the ElementTree klasse to wrap an element structure
 und convert it to und von XML.

"""

#---------------------------------------------------------------------
# Licensed to PSF under a Contributor Agreement.
# See https://www.python.org/psf/license fuer licensing details.
#
# ElementTree
# Copyright (c) 1999-2008 by Fredrik Lundh.  All rights reserved.
#
# fredrik@pythonware.com
# http://www.pythonware.com
# --------------------------------------------------------------------
# The ElementTree toolkit is
#
# Copyright (c) 1999-2008 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# und will comply mit the following terms und conditions:
#
# Permission to use, copy, modify, und distribute this software und
# its associated documentation fuer any purpose und without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, und that both that copyright notice und this permission
# notice appear in supporting documentation, und that the name of
# Secret Labs AB oder the author nicht be used in advertising oder publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------

__all__ = [
    # public symbols
    "Comment",
    "dump",
    "Element", "ElementTree",
    "fromstring", "fromstringlist",
    "indent", "iselement", "iterparse",
    "parse", "ParseError",
    "PI", "ProcessingInstruction",
    "QName",
    "SubElement",
    "tostring", "tostringlist",
    "TreeBuilder",
    "VERSION",
    "XML", "XMLID",
    "XMLParser", "XMLPullParser",
    "register_namespace",
    "canonicalize", "C14NWriterTarget",
    ]

VERSION = "1.3.0"

importiere sys
importiere re
importiere warnings
importiere io
importiere collections
importiere collections.abc
importiere contextlib
importiere weakref

von . importiere ElementPath


klasse ParseError(SyntaxError):
    """An error when parsing an XML document.

    In addition to its exception value, a ParseError contains
    two extra attributes:
        'code'     - the specific exception code
        'position' - the line und column of the error

    """
    pass

# --------------------------------------------------------------------


def iselement(element):
    """Return Wahr wenn *element* appears to be an Element."""
    gib hasattr(element, 'tag')


klasse Element:
    """An XML element.

    This klasse is the reference implementation of the Element interface.

    An element's length is its number of subelements.  That means wenn you
    want to check wenn an element is truly empty, you should check BOTH
    its length AND its text attribute.

    The element tag, attribute names, und attribute values can be either
    bytes oder strings.

    *tag* is the element name.  *attrib* is an optional dictionary containing
    element attributes. *extra* are additional element attributes given as
    keyword arguments.

    Example form:
        <tag attrib>text<child/>...</tag>tail

    """

    tag = Nichts
    """The element's name."""

    attrib = Nichts
    """Dictionary of the element's attributes."""

    text = Nichts
    """
    Text before first subelement. This is either a string oder the value Nichts.
    Note that wenn there is no text, this attribute may be either
    Nichts oder the empty string, depending on the parser.

    """

    tail = Nichts
    """
    Text after this element's end tag, but before the next sibling element's
    start tag.  This is either a string oder the value Nichts.  Note that wenn there
    was no text, this attribute may be either Nichts oder an empty string,
    depending on the parser.

    """

    def __init__(self, tag, attrib={}, **extra):
        wenn nicht isinstance(attrib, dict):
            wirf TypeError("attrib must be dict, nicht %s" % (
                attrib.__class__.__name__,))
        self.tag = tag
        self.attrib = {**attrib, **extra}
        self._children = []

    def __repr__(self):
        gib "<%s %r at %#x>" % (self.__class__.__name__, self.tag, id(self))

    def makeelement(self, tag, attrib):
        """Create a new element mit the same type.

        *tag* is a string containing the element name.
        *attrib* is a dictionary containing the element attributes.

        Do nicht call this method, use the SubElement factory function instead.

        """
        gib self.__class__(tag, attrib)

    def __copy__(self):
        elem = self.makeelement(self.tag, self.attrib)
        elem.text = self.text
        elem.tail = self.tail
        elem[:] = self
        gib elem

    def __len__(self):
        gib len(self._children)

    def __bool__(self):
        warnings.warn(
            "Testing an element's truth value will always gib Wahr in "
            "future versions.  "
            "Use specific 'len(elem)' oder 'elem is nicht Nichts' test instead.",
            DeprecationWarning, stacklevel=2
            )
        gib len(self._children) != 0 # emulate old behaviour, fuer now

    def __getitem__(self, index):
        gib self._children[index]

    def __setitem__(self, index, element):
        wenn isinstance(index, slice):
            fuer elt in element:
                self._assert_is_element(elt)
        sonst:
            self._assert_is_element(element)
        self._children[index] = element

    def __delitem__(self, index):
        del self._children[index]

    def append(self, subelement):
        """Add *subelement* to the end of this element.

        The new element will appear in document order after the last existing
        subelement (or directly after the text, wenn it's the first subelement),
        but before the end tag fuer this element.

        """
        self._assert_is_element(subelement)
        self._children.append(subelement)

    def extend(self, elements):
        """Append subelements von a sequence.

        *elements* is a sequence mit zero oder more elements.

        """
        fuer element in elements:
            self._assert_is_element(element)
            self._children.append(element)

    def insert(self, index, subelement):
        """Insert *subelement* at position *index*."""
        self._assert_is_element(subelement)
        self._children.insert(index, subelement)

    def _assert_is_element(self, e):
        # Need to refer to the actual Python implementation, nicht the
        # shadowing C implementation.
        wenn nicht isinstance(e, _Element_Py):
            wirf TypeError('expected an Element, nicht %s' % type(e).__name__)

    def remove(self, subelement):
        """Remove matching subelement.

        Unlike the find methods, this method compares elements based on
        identity, NOT ON tag value oder contents.  To remove subelements by
        other means, the easiest way is to use a list comprehension to
        select what elements to keep, und then use slice assignment to update
        the parent element.

        ValueError is raised wenn a matching element could nicht be found.

        """
        # assert iselement(element)
        versuch:
            self._children.remove(subelement)
        ausser ValueError:
            # to align the error message mit the C implementation
            wirf ValueError("Element.remove(x): element nicht found") von Nichts

    def find(self, path, namespaces=Nichts):
        """Find first matching element by tag name oder path.

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return the first matching element, oder Nichts wenn no element was found.

        """
        gib ElementPath.find(self, path, namespaces)

    def findtext(self, path, default=Nichts, namespaces=Nichts):
        """Find text fuer first matching element by tag name oder path.

        *path* is a string having either an element tag oder an XPath,
        *default* is the value to gib wenn the element was nicht found,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return text content of first matching element, oder default value if
        none was found.  Note that wenn an element is found having no text
        content, the empty string is returned.

        """
        gib ElementPath.findtext(self, path, default, namespaces)

    def findall(self, path, namespaces=Nichts):
        """Find all matching subelements by tag name oder path.

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Returns list containing all matching elements in document order.

        """
        gib ElementPath.findall(self, path, namespaces)

    def iterfind(self, path, namespaces=Nichts):
        """Find all matching subelements by tag name oder path.

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return an iterable yielding all matching elements in document order.

        """
        gib ElementPath.iterfind(self, path, namespaces)

    def clear(self):
        """Reset element.

        This function removes all subelements, clears all attributes, und sets
        the text und tail attributes to Nichts.

        """
        self.attrib.clear()
        self._children = []
        self.text = self.tail = Nichts

    def get(self, key, default=Nichts):
        """Get element attribute.

        Equivalent to attrib.get, but some implementations may handle this a
        bit more efficiently.  *key* is what attribute to look for, und
        *default* is what to gib wenn the attribute was nicht found.

        Returns a string containing the attribute value, oder the default if
        attribute was nicht found.

        """
        gib self.attrib.get(key, default)

    def set(self, key, value):
        """Set element attribute.

        Equivalent to attrib[key] = value, but some implementations may handle
        this a bit more efficiently.  *key* is what attribute to set, und
        *value* is the attribute value to set it to.

        """
        self.attrib[key] = value

    def keys(self):
        """Get list of attribute names.

        Names are returned in an arbitrary order, just like an ordinary
        Python dict.  Equivalent to attrib.keys()

        """
        gib self.attrib.keys()

    def items(self):
        """Get element attributes als a sequence.

        The attributes are returned in arbitrary order.  Equivalent to
        attrib.items().

        Return a list of (name, value) tuples.

        """
        gib self.attrib.items()

    def iter(self, tag=Nichts):
        """Create tree iterator.

        The iterator loops over the element und all subelements in document
        order, returning all elements mit a matching tag.

        If the tree structure is modified during iteration, new oder removed
        elements may oder may nicht be included.  To get a stable set, use the
        list() function on the iterator, und loop over the resulting list.

        *tag* is what tags to look fuer (default is to gib all elements)

        Return an iterator containing all the matching elements.

        """
        wenn tag == "*":
            tag = Nichts
        wenn tag is Nichts oder self.tag == tag:
            liefere self
        fuer e in self._children:
            liefere von e.iter(tag)

    def itertext(self):
        """Create text iterator.

        The iterator loops over the element und all subelements in document
        order, returning all inner text.

        """
        tag = self.tag
        wenn nicht isinstance(tag, str) und tag is nicht Nichts:
            gib
        t = self.text
        wenn t:
            liefere t
        fuer e in self:
            liefere von e.itertext()
            t = e.tail
            wenn t:
                liefere t


def SubElement(parent, tag, attrib={}, **extra):
    """Subelement factory which creates an element instance, und appends it
    to an existing parent.

    The element tag, attribute names, und attribute values can be either
    bytes oder Unicode strings.

    *parent* is the parent element, *tag* is the subelements name, *attrib* is
    an optional directory containing element attributes, *extra* are
    additional attributes given als keyword arguments.

    """
    attrib = {**attrib, **extra}
    element = parent.makeelement(tag, attrib)
    parent.append(element)
    gib element


def Comment(text=Nichts):
    """Comment element factory.

    This function creates a special element which the standard serializer
    serializes als an XML comment.

    *text* is a string containing the comment string.

    """
    element = Element(Comment)
    element.text = text
    gib element


def ProcessingInstruction(target, text=Nichts):
    """Processing Instruction element factory.

    This function creates a special element which the standard serializer
    serializes als an XML comment.

    *target* is a string containing the processing instruction, *text* is a
    string containing the processing instruction contents, wenn any.

    """
    element = Element(ProcessingInstruction)
    element.text = target
    wenn text:
        element.text = element.text + " " + text
    gib element

PI = ProcessingInstruction


klasse QName:
    """Qualified name wrapper.

    This klasse can be used to wrap a QName attribute value in order to get
    proper namespace handing on output.

    *text_or_uri* is a string containing the QName value either in the form
    {uri}local, oder wenn the tag argument is given, the URI part of a QName.

    *tag* is an optional argument which wenn given, will make the first
    argument (text_or_uri) be interpreted als a URI, und this argument (tag)
    be interpreted als a local name.

    """
    def __init__(self, text_or_uri, tag=Nichts):
        wenn tag:
            text_or_uri = "{%s}%s" % (text_or_uri, tag)
        self.text = text_or_uri
    def __str__(self):
        gib self.text
    def __repr__(self):
        gib '<%s %r>' % (self.__class__.__name__, self.text)
    def __hash__(self):
        gib hash(self.text)
    def __le__(self, other):
        wenn isinstance(other, QName):
            gib self.text <= other.text
        gib self.text <= other
    def __lt__(self, other):
        wenn isinstance(other, QName):
            gib self.text < other.text
        gib self.text < other
    def __ge__(self, other):
        wenn isinstance(other, QName):
            gib self.text >= other.text
        gib self.text >= other
    def __gt__(self, other):
        wenn isinstance(other, QName):
            gib self.text > other.text
        gib self.text > other
    def __eq__(self, other):
        wenn isinstance(other, QName):
            gib self.text == other.text
        gib self.text == other

# --------------------------------------------------------------------


klasse ElementTree:
    """An XML element hierarchy.

    This klasse also provides support fuer serialization to und from
    standard XML.

    *element* is an optional root element node,
    *file* is an optional file handle oder file name of an XML file whose
    contents will be used to initialize the tree with.

    """
    def __init__(self, element=Nichts, file=Nichts):
        wenn element is nicht Nichts und nicht iselement(element):
            wirf TypeError('expected an Element, nicht %s' %
                            type(element).__name__)
        self._root = element # first node
        wenn file:
            self.parse(file)

    def getroot(self):
        """Return root element of this tree."""
        gib self._root

    def _setroot(self, element):
        """Replace root element of this tree.

        This will discard the current contents of the tree und replace it
        mit the given element.  Use mit care!

        """
        wenn nicht iselement(element):
            wirf TypeError('expected an Element, nicht %s'
                            % type(element).__name__)
        self._root = element

    def parse(self, source, parser=Nichts):
        """Load external XML document into element tree.

        *source* is a file name oder file object, *parser* is an optional parser
        instance that defaults to XMLParser.

        ParseError is raised wenn the parser fails to parse the document.

        Returns the root element of the given source document.

        """
        close_source = Falsch
        wenn nicht hasattr(source, "read"):
            source = open(source, "rb")
            close_source = Wahr
        versuch:
            wenn parser is Nichts:
                # If no parser was specified, create a default XMLParser
                parser = XMLParser()
                wenn hasattr(parser, '_parse_whole'):
                    # The default XMLParser, when it comes von an accelerator,
                    # can define an internal _parse_whole API fuer efficiency.
                    # It can be used to parse the whole source without feeding
                    # it mit chunks.
                    self._root = parser._parse_whole(source)
                    gib self._root
            waehrend data := source.read(65536):
                parser.feed(data)
            self._root = parser.close()
            gib self._root
        schliesslich:
            wenn close_source:
                source.close()

    def iter(self, tag=Nichts):
        """Create und gib tree iterator fuer the root element.

        The iterator loops over all elements in this tree, in document order.

        *tag* is a string mit the tag name to iterate over
        (default is to gib all elements).

        """
        # assert self._root is nicht Nichts
        gib self._root.iter(tag)

    def find(self, path, namespaces=Nichts):
        """Find first matching element by tag name oder path.

        Same als getroot().find(path), which is Element.find()

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return the first matching element, oder Nichts wenn no element was found.

        """
        # assert self._root is nicht Nichts
        wenn path[:1] == "/":
            path = "." + path
            warnings.warn(
                "This search is broken in 1.3 und earlier, und will be "
                "fixed in a future version.  If you rely on the current "
                "behaviour, change it to %r" % path,
                FutureWarning, stacklevel=2
                )
        gib self._root.find(path, namespaces)

    def findtext(self, path, default=Nichts, namespaces=Nichts):
        """Find first matching element by tag name oder path.

        Same als getroot().findtext(path),  which is Element.findtext()

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return the first matching element, oder Nichts wenn no element was found.

        """
        # assert self._root is nicht Nichts
        wenn path[:1] == "/":
            path = "." + path
            warnings.warn(
                "This search is broken in 1.3 und earlier, und will be "
                "fixed in a future version.  If you rely on the current "
                "behaviour, change it to %r" % path,
                FutureWarning, stacklevel=2
                )
        gib self._root.findtext(path, default, namespaces)

    def findall(self, path, namespaces=Nichts):
        """Find all matching subelements by tag name oder path.

        Same als getroot().findall(path), which is Element.findall().

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return list containing all matching elements in document order.

        """
        # assert self._root is nicht Nichts
        wenn path[:1] == "/":
            path = "." + path
            warnings.warn(
                "This search is broken in 1.3 und earlier, und will be "
                "fixed in a future version.  If you rely on the current "
                "behaviour, change it to %r" % path,
                FutureWarning, stacklevel=2
                )
        gib self._root.findall(path, namespaces)

    def iterfind(self, path, namespaces=Nichts):
        """Find all matching subelements by tag name oder path.

        Same als getroot().iterfind(path), which is element.iterfind()

        *path* is a string having either an element tag oder an XPath,
        *namespaces* is an optional mapping von namespace prefix to full name.

        Return an iterable yielding all matching elements in document order.

        """
        # assert self._root is nicht Nichts
        wenn path[:1] == "/":
            path = "." + path
            warnings.warn(
                "This search is broken in 1.3 und earlier, und will be "
                "fixed in a future version.  If you rely on the current "
                "behaviour, change it to %r" % path,
                FutureWarning, stacklevel=2
                )
        gib self._root.iterfind(path, namespaces)

    def write(self, file_or_filename,
              encoding=Nichts,
              xml_declaration=Nichts,
              default_namespace=Nichts,
              method=Nichts, *,
              short_empty_elements=Wahr):
        """Write element tree to a file als XML.

        Arguments:
          *file_or_filename* -- file name oder a file object opened fuer writing

          *encoding* -- the output encoding (default: US-ASCII)

          *xml_declaration* -- bool indicating wenn an XML declaration should be
                               added to the output. If Nichts, an XML declaration
                               is added wenn encoding IS NOT either of:
                               US-ASCII, UTF-8, oder Unicode

          *default_namespace* -- sets the default XML namespace (for "xmlns")

          *method* -- either "xml" (default), "html, "text", oder "c14n"

          *short_empty_elements* -- controls the formatting of elements
                                    that contain no content. If Wahr (default)
                                    they are emitted als a single self-closed
                                    tag, otherwise they are emitted als a pair
                                    of start/end tags

        """
        wenn self._root is Nichts:
            wirf TypeError('ElementTree nicht initialized')
        wenn nicht method:
            method = "xml"
        sowenn method nicht in _serialize:
            wirf ValueError("unknown method %r" % method)
        wenn nicht encoding:
            wenn method == "c14n":
                encoding = "utf-8"
            sonst:
                encoding = "us-ascii"
        mit _get_writer(file_or_filename, encoding) als (write, declared_encoding):
            wenn method == "xml" und (xml_declaration oder
                    (xml_declaration is Nichts und
                     encoding.lower() != "unicode" und
                     declared_encoding.lower() nicht in ("utf-8", "us-ascii"))):
                write("<?xml version='1.0' encoding='%s'?>\n" % (
                    declared_encoding,))
            wenn method == "text":
                _serialize_text(write, self._root)
            sonst:
                qnames, namespaces = _namespaces(self._root, default_namespace)
                serialize = _serialize[method]
                serialize(write, self._root, qnames, namespaces,
                          short_empty_elements=short_empty_elements)

    def write_c14n(self, file):
        # lxml.etree compatibility.  use output method instead
        gib self.write(file, method="c14n")

# --------------------------------------------------------------------
# serialization support

@contextlib.contextmanager
def _get_writer(file_or_filename, encoding):
    # returns text write method und release all resources after using
    versuch:
        write = file_or_filename.write
    ausser AttributeError:
        # file_or_filename is a file name
        wenn encoding.lower() == "unicode":
            encoding="utf-8"
        mit open(file_or_filename, "w", encoding=encoding,
                  errors="xmlcharrefreplace") als file:
            liefere file.write, encoding
    sonst:
        # file_or_filename is a file-like object
        # encoding determines wenn it is a text oder binary writer
        wenn encoding.lower() == "unicode":
            # use a text writer als is
            liefere write, getattr(file_or_filename, "encoding", Nichts) oder "utf-8"
        sonst:
            # wrap a binary writer mit TextIOWrapper
            mit contextlib.ExitStack() als stack:
                wenn isinstance(file_or_filename, io.BufferedIOBase):
                    file = file_or_filename
                sowenn isinstance(file_or_filename, io.RawIOBase):
                    file = io.BufferedWriter(file_or_filename)
                    # Keep the original file open when the BufferedWriter is
                    # destroyed
                    stack.callback(file.detach)
                sonst:
                    # This is to handle passed objects that aren't in the
                    # IOBase hierarchy, but just have a write method
                    file = io.BufferedIOBase()
                    file.writable = lambda: Wahr
                    file.write = write
                    versuch:
                        # TextIOWrapper uses this methods to determine
                        # wenn BOM (for UTF-16, etc) should be added
                        file.seekable = file_or_filename.seekable
                        file.tell = file_or_filename.tell
                    ausser AttributeError:
                        pass
                file = io.TextIOWrapper(file,
                                        encoding=encoding,
                                        errors="xmlcharrefreplace",
                                        newline="\n")
                # Keep the original file open when the TextIOWrapper is
                # destroyed
                stack.callback(file.detach)
                liefere file.write, encoding

def _namespaces(elem, default_namespace=Nichts):
    # identify namespaces used in this tree

    # maps qnames to *encoded* prefix:local names
    qnames = {Nichts: Nichts}

    # maps uri:s to prefixes
    namespaces = {}
    wenn default_namespace:
        namespaces[default_namespace] = ""

    def add_qname(qname):
        # calculate serialized qname representation
        versuch:
            wenn qname[:1] == "{":
                uri, tag = qname[1:].rsplit("}", 1)
                prefix = namespaces.get(uri)
                wenn prefix is Nichts:
                    prefix = _namespace_map.get(uri)
                    wenn prefix is Nichts:
                        prefix = "ns%d" % len(namespaces)
                    wenn prefix != "xml":
                        namespaces[uri] = prefix
                wenn prefix:
                    qnames[qname] = "%s:%s" % (prefix, tag)
                sonst:
                    qnames[qname] = tag # default element
            sonst:
                wenn default_namespace:
                    # FIXME: can this be handled in XML 1.0?
                    wirf ValueError(
                        "cannot use non-qualified names mit "
                        "default_namespace option"
                        )
                qnames[qname] = qname
        ausser TypeError:
            _raise_serialization_error(qname)

    # populate qname und namespaces table
    fuer elem in elem.iter():
        tag = elem.tag
        wenn isinstance(tag, QName):
            wenn tag.text nicht in qnames:
                add_qname(tag.text)
        sowenn isinstance(tag, str):
            wenn tag nicht in qnames:
                add_qname(tag)
        sowenn tag is nicht Nichts und tag is nicht Comment und tag is nicht PI:
            _raise_serialization_error(tag)
        fuer key, value in elem.items():
            wenn isinstance(key, QName):
                key = key.text
            wenn key nicht in qnames:
                add_qname(key)
            wenn isinstance(value, QName) und value.text nicht in qnames:
                add_qname(value.text)
        text = elem.text
        wenn isinstance(text, QName) und text.text nicht in qnames:
            add_qname(text.text)
    gib qnames, namespaces

def _serialize_xml(write, elem, qnames, namespaces,
                   short_empty_elements, **kwargs):
    tag = elem.tag
    text = elem.text
    wenn tag is Comment:
        write("<!--%s-->" % text)
    sowenn tag is ProcessingInstruction:
        write("<?%s?>" % text)
    sonst:
        tag = qnames[tag]
        wenn tag is Nichts:
            wenn text:
                write(_escape_cdata(text))
            fuer e in elem:
                _serialize_xml(write, e, qnames, Nichts,
                               short_empty_elements=short_empty_elements)
        sonst:
            write("<" + tag)
            items = list(elem.items())
            wenn items oder namespaces:
                wenn namespaces:
                    fuer v, k in sorted(namespaces.items(),
                                       key=lambda x: x[1]):  # sort on prefix
                        wenn k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k,
                            _escape_attrib(v)
                            ))
                fuer k, v in items:
                    wenn isinstance(k, QName):
                        k = k.text
                    wenn isinstance(v, QName):
                        v = qnames[v.text]
                    sonst:
                        v = _escape_attrib(v)
                    write(" %s=\"%s\"" % (qnames[k], v))
            wenn text oder len(elem) oder nicht short_empty_elements:
                write(">")
                wenn text:
                    write(_escape_cdata(text))
                fuer e in elem:
                    _serialize_xml(write, e, qnames, Nichts,
                                   short_empty_elements=short_empty_elements)
                write("</" + tag + ">")
            sonst:
                write(" />")
    wenn elem.tail:
        write(_escape_cdata(elem.tail))

HTML_EMPTY = {"area", "base", "basefont", "br", "col", "embed", "frame", "hr",
              "img", "input", "isindex", "link", "meta", "param", "source",
              "track", "wbr"}

def _serialize_html(write, elem, qnames, namespaces, **kwargs):
    tag = elem.tag
    text = elem.text
    wenn tag is Comment:
        write("<!--%s-->" % _escape_cdata(text))
    sowenn tag is ProcessingInstruction:
        write("<?%s?>" % _escape_cdata(text))
    sonst:
        tag = qnames[tag]
        wenn tag is Nichts:
            wenn text:
                write(_escape_cdata(text))
            fuer e in elem:
                _serialize_html(write, e, qnames, Nichts)
        sonst:
            write("<" + tag)
            items = list(elem.items())
            wenn items oder namespaces:
                wenn namespaces:
                    fuer v, k in sorted(namespaces.items(),
                                       key=lambda x: x[1]):  # sort on prefix
                        wenn k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k,
                            _escape_attrib(v)
                            ))
                fuer k, v in items:
                    wenn isinstance(k, QName):
                        k = k.text
                    wenn isinstance(v, QName):
                        v = qnames[v.text]
                    sonst:
                        v = _escape_attrib_html(v)
                    # FIXME: handle boolean attributes
                    write(" %s=\"%s\"" % (qnames[k], v))
            write(">")
            ltag = tag.lower()
            wenn text:
                wenn ltag == "script" oder ltag == "style":
                    write(text)
                sonst:
                    write(_escape_cdata(text))
            fuer e in elem:
                _serialize_html(write, e, qnames, Nichts)
            wenn ltag nicht in HTML_EMPTY:
                write("</" + tag + ">")
    wenn elem.tail:
        write(_escape_cdata(elem.tail))

def _serialize_text(write, elem):
    fuer part in elem.itertext():
        write(part)
    wenn elem.tail:
        write(elem.tail)

_serialize = {
    "xml": _serialize_xml,
    "html": _serialize_html,
    "text": _serialize_text,
# this optional method is imported at the end of the module
#   "c14n": _serialize_c14n,
}


def register_namespace(prefix, uri):
    """Register a namespace prefix.

    The registry is global, und any existing mapping fuer either the
    given prefix oder the namespace URI will be removed.

    *prefix* is the namespace prefix, *uri* is a namespace uri. Tags und
    attributes in this namespace will be serialized mit prefix wenn possible.

    ValueError is raised wenn prefix is reserved oder is invalid.

    """
    wenn re.match(r"ns\d+$", prefix):
        wirf ValueError("Prefix format reserved fuer internal use")
    fuer k, v in list(_namespace_map.items()):
        wenn k == uri oder v == prefix:
            del _namespace_map[k]
    _namespace_map[uri] = prefix

_namespace_map = {
    # "well-known" namespace prefixes
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/1999/xhtml": "html",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://schemas.xmlsoap.org/wsdl/": "wsdl",
    # xml schema
    "http://www.w3.org/2001/XMLSchema": "xs",
    "http://www.w3.org/2001/XMLSchema-instance": "xsi",
    # dublin core
    "http://purl.org/dc/elements/1.1/": "dc",
}
# For tests und troubleshooting
register_namespace._namespace_map = _namespace_map

def _raise_serialization_error(text):
    wirf TypeError(
        "cannot serialize %r (type %s)" % (text, type(text).__name__)
        )

def _escape_cdata(text):
    # escape character data
    versuch:
        # it's worth avoiding do-nothing calls fuer strings that are
        # shorter than 500 characters, oder so.  assume that's, by far,
        # the most common case in most applications.
        wenn "&" in text:
            text = text.replace("&", "&amp;")
        wenn "<" in text:
            text = text.replace("<", "&lt;")
        wenn ">" in text:
            text = text.replace(">", "&gt;")
        gib text
    ausser (TypeError, AttributeError):
        _raise_serialization_error(text)

def _escape_attrib(text):
    # escape attribute value
    versuch:
        wenn "&" in text:
            text = text.replace("&", "&amp;")
        wenn "<" in text:
            text = text.replace("<", "&lt;")
        wenn ">" in text:
            text = text.replace(">", "&gt;")
        wenn "\"" in text:
            text = text.replace("\"", "&quot;")
        # Although section 2.11 of the XML specification states that CR oder
        # CR LN should be replaced mit just LN, it applies only to EOLNs
        # which take part of organizing file into lines. Within attributes,
        # we are replacing these mit entity numbers, so they do nicht count.
        # http://www.w3.org/TR/REC-xml/#sec-line-ends
        # The current solution, contained in following six lines, was
        # discussed in issue 17582 und 39011.
        wenn "\r" in text:
            text = text.replace("\r", "&#13;")
        wenn "\n" in text:
            text = text.replace("\n", "&#10;")
        wenn "\t" in text:
            text = text.replace("\t", "&#09;")
        gib text
    ausser (TypeError, AttributeError):
        _raise_serialization_error(text)

def _escape_attrib_html(text):
    # escape attribute value
    versuch:
        wenn "&" in text:
            text = text.replace("&", "&amp;")
        wenn ">" in text:
            text = text.replace(">", "&gt;")
        wenn "\"" in text:
            text = text.replace("\"", "&quot;")
        gib text
    ausser (TypeError, AttributeError):
        _raise_serialization_error(text)

# --------------------------------------------------------------------

def tostring(element, encoding=Nichts, method=Nichts, *,
             xml_declaration=Nichts, default_namespace=Nichts,
             short_empty_elements=Wahr):
    """Generate string representation of XML element.

    All subelements are included.  If encoding is "unicode", a string
    is returned. Otherwise a bytestring is returned.

    *element* is an Element instance, *encoding* is an optional output
    encoding defaulting to US-ASCII, *method* is an optional output which can
    be one of "xml" (default), "html", "text" oder "c14n", *default_namespace*
    sets the default XML namespace (for "xmlns").

    Returns an (optionally) encoded string containing the XML data.

    """
    stream = io.StringIO() wenn encoding == 'unicode' sonst io.BytesIO()
    ElementTree(element).write(stream, encoding,
                               xml_declaration=xml_declaration,
                               default_namespace=default_namespace,
                               method=method,
                               short_empty_elements=short_empty_elements)
    gib stream.getvalue()

klasse _ListDataStream(io.BufferedIOBase):
    """An auxiliary stream accumulating into a list reference."""
    def __init__(self, lst):
        self.lst = lst

    def writable(self):
        gib Wahr

    def seekable(self):
        gib Wahr

    def write(self, b):
        self.lst.append(b)

    def tell(self):
        gib len(self.lst)

def tostringlist(element, encoding=Nichts, method=Nichts, *,
                 xml_declaration=Nichts, default_namespace=Nichts,
                 short_empty_elements=Wahr):
    lst = []
    stream = _ListDataStream(lst)
    ElementTree(element).write(stream, encoding,
                               xml_declaration=xml_declaration,
                               default_namespace=default_namespace,
                               method=method,
                               short_empty_elements=short_empty_elements)
    gib lst


def dump(elem):
    """Write element tree oder element structure to sys.stdout.

    This function should be used fuer debugging only.

    *elem* is either an ElementTree, oder a single Element.  The exact output
    format is implementation dependent.  In this version, it's written als an
    ordinary XML file.

    """
    # debugging
    wenn nicht isinstance(elem, ElementTree):
        elem = ElementTree(elem)
    elem.write(sys.stdout, encoding="unicode")
    tail = elem.getroot().tail
    wenn nicht tail oder tail[-1] != "\n":
        sys.stdout.write("\n")


def indent(tree, space="  ", level=0):
    """Indent an XML document by inserting newlines und indentation space
    after elements.

    *tree* is the ElementTree oder Element to modify.  The (root) element
    itself will nicht be changed, but the tail text of all elements in its
    subtree will be adapted.

    *space* is the whitespace to insert fuer each indentation level, two
    space characters by default.

    *level* is the initial indentation level. Setting this to a higher
    value than 0 can be used fuer indenting subtrees that are more deeply
    nested inside of a document.
    """
    wenn isinstance(tree, ElementTree):
        tree = tree.getroot()
    wenn level < 0:
        wirf ValueError(f"Initial indentation level must be >= 0, got {level}")
    wenn nicht len(tree):
        gib

    # Reduce the memory consumption by reusing indentation strings.
    indentations = ["\n" + level * space]

    def _indent_children(elem, level):
        # Start a new indentation level fuer the first child.
        child_level = level + 1
        versuch:
            child_indentation = indentations[child_level]
        ausser IndexError:
            child_indentation = indentations[level] + space
            indentations.append(child_indentation)

        wenn nicht elem.text oder nicht elem.text.strip():
            elem.text = child_indentation

        fuer child in elem:
            wenn len(child):
                _indent_children(child, child_level)
            wenn nicht child.tail oder nicht child.tail.strip():
                child.tail = child_indentation

        # Dedent after the last child by overwriting the previous indentation.
        wenn nicht child.tail.strip():
            child.tail = indentations[level]

    _indent_children(tree, 0)


# --------------------------------------------------------------------
# parsing


def parse(source, parser=Nichts):
    """Parse XML document into element tree.

    *source* is a filename oder file object containing XML data,
    *parser* is an optional parser instance defaulting to XMLParser.

    Return an ElementTree instance.

    """
    tree = ElementTree()
    tree.parse(source, parser)
    gib tree


def iterparse(source, events=Nichts, parser=Nichts):
    """Incrementally parse XML document into ElementTree.

    This klasse also reports what's going on to the user based on the
    *events* it is initialized with.  The supported events are the strings
    "start", "end", "start-ns" und "end-ns" (the "ns" events are used to get
    detailed namespace information).  If *events* is omitted, only
    "end" events are reported.

    *source* is a filename oder file object containing XML data, *events* is
    a list of events to report back, *parser* is an optional parser instance.

    Returns an iterator providing (event, elem) pairs.

    """
    # Use the internal, undocumented _parser argument fuer now; When the
    # parser argument of iterparse is removed, this can be killed.
    pullparser = XMLPullParser(events=events, _parser=parser)

    wenn nicht hasattr(source, "read"):
        source = open(source, "rb")
        close_source = Wahr
    sonst:
        close_source = Falsch

    def iterator(source):
        versuch:
            waehrend Wahr:
                liefere von pullparser.read_events()
                # load event buffer
                data = source.read(16 * 1024)
                wenn nicht data:
                    breche
                pullparser.feed(data)
            root = pullparser._close_and_return_root()
            liefere von pullparser.read_events()
            it = wr()
            wenn it is nicht Nichts:
                it.root = root
        schliesslich:
            wenn close_source:
                source.close()

    gen = iterator(source)
    klasse IterParseIterator(collections.abc.Iterator):
        __next__ = gen.__next__
        def close(self):
            wenn close_source:
                source.close()
            gen.close()

        def __del__(self):
            # TODO: Emit a ResourceWarning wenn it was nicht explicitly closed.
            # (When the close() method will be supported in all maintained Python versions.)
            wenn close_source:
                source.close()

    it = IterParseIterator()
    it.root = Nichts
    wr = weakref.ref(it)
    gib it


klasse XMLPullParser:

    def __init__(self, events=Nichts, *, _parser=Nichts):
        # The _parser argument is fuer internal use only und must nicht be relied
        # upon in user code. It will be removed in a future release.
        # See https://bugs.python.org/issue17741 fuer more details.

        self._events_queue = collections.deque()
        self._parser = _parser oder XMLParser(target=TreeBuilder())
        # wire up the parser fuer event reporting
        wenn events is Nichts:
            events = ("end",)
        self._parser._setevents(self._events_queue, events)

    def feed(self, data):
        """Feed encoded data to parser."""
        wenn self._parser is Nichts:
            wirf ValueError("feed() called after end of stream")
        wenn data:
            versuch:
                self._parser.feed(data)
            ausser SyntaxError als exc:
                self._events_queue.append(exc)

    def _close_and_return_root(self):
        # iterparse needs this to set its root attribute properly :(
        root = self._parser.close()
        self._parser = Nichts
        gib root

    def close(self):
        """Finish feeding data to parser.

        Unlike XMLParser, does nicht gib the root element. Use
        read_events() to consume elements von XMLPullParser.
        """
        self._close_and_return_root()

    def read_events(self):
        """Return an iterator over currently available (event, elem) pairs.

        Events are consumed von the internal event queue als they are
        retrieved von the iterator.
        """
        events = self._events_queue
        waehrend events:
            event = events.popleft()
            wenn isinstance(event, Exception):
                wirf event
            sonst:
                liefere event

    def flush(self):
        wenn self._parser is Nichts:
            wirf ValueError("flush() called after end of stream")
        self._parser.flush()


def XML(text, parser=Nichts):
    """Parse XML document von string constant.

    This function can be used to embed "XML Literals" in Python code.

    *text* is a string containing XML data, *parser* is an
    optional parser instance, defaulting to the standard XMLParser.

    Returns an Element instance.

    """
    wenn nicht parser:
        parser = XMLParser(target=TreeBuilder())
    parser.feed(text)
    gib parser.close()


def XMLID(text, parser=Nichts):
    """Parse XML document von string constant fuer its IDs.

    *text* is a string containing XML data, *parser* is an
    optional parser instance, defaulting to the standard XMLParser.

    Returns an (Element, dict) tuple, in which the
    dict maps element id:s to elements.

    """
    wenn nicht parser:
        parser = XMLParser(target=TreeBuilder())
    parser.feed(text)
    tree = parser.close()
    ids = {}
    fuer elem in tree.iter():
        id = elem.get("id")
        wenn id:
            ids[id] = elem
    gib tree, ids

# Parse XML document von string constant.  Alias fuer XML().
fromstring = XML

def fromstringlist(sequence, parser=Nichts):
    """Parse XML document von sequence of string fragments.

    *sequence* is a list of other sequence, *parser* is an optional parser
    instance, defaulting to the standard XMLParser.

    Returns an Element instance.

    """
    wenn nicht parser:
        parser = XMLParser(target=TreeBuilder())
    fuer text in sequence:
        parser.feed(text)
    gib parser.close()

# --------------------------------------------------------------------


klasse TreeBuilder:
    """Generic element structure builder.

    This builder converts a sequence of start, data, und end method
    calls to a well-formed element structure.

    You can use this klasse to build an element structure using a custom XML
    parser, oder a parser fuer some other XML-like format.

    *element_factory* is an optional element factory which is called
    to create new Element instances, als necessary.

    *comment_factory* is a factory to create comments to be used instead of
    the standard factory.  If *insert_comments* is false (the default),
    comments will nicht be inserted into the tree.

    *pi_factory* is a factory to create processing instructions to be used
    instead of the standard factory.  If *insert_pis* is false (the default),
    processing instructions will nicht be inserted into the tree.
    """
    def __init__(self, element_factory=Nichts, *,
                 comment_factory=Nichts, pi_factory=Nichts,
                 insert_comments=Falsch, insert_pis=Falsch):
        self._data = [] # data collector
        self._elem = [] # element stack
        self._last = Nichts # last element
        self._root = Nichts # root element
        self._tail = Nichts # true wenn we're after an end tag
        wenn comment_factory is Nichts:
            comment_factory = Comment
        self._comment_factory = comment_factory
        self.insert_comments = insert_comments
        wenn pi_factory is Nichts:
            pi_factory = ProcessingInstruction
        self._pi_factory = pi_factory
        self.insert_pis = insert_pis
        wenn element_factory is Nichts:
            element_factory = Element
        self._factory = element_factory

    def close(self):
        """Flush builder buffers und gib toplevel document Element."""
        assert len(self._elem) == 0, "missing end tags"
        assert self._root is nicht Nichts, "missing toplevel element"
        gib self._root

    def _flush(self):
        wenn self._data:
            wenn self._last is nicht Nichts:
                text = "".join(self._data)
                wenn self._tail:
                    assert self._last.tail is Nichts, "internal error (tail)"
                    self._last.tail = text
                sonst:
                    assert self._last.text is Nichts, "internal error (text)"
                    self._last.text = text
            self._data = []

    def data(self, data):
        """Add text to current element."""
        self._data.append(data)

    def start(self, tag, attrs):
        """Open new element und gib it.

        *tag* is the element name, *attrs* is a dict containing element
        attributes.

        """
        self._flush()
        self._last = elem = self._factory(tag, attrs)
        wenn self._elem:
            self._elem[-1].append(elem)
        sowenn self._root is Nichts:
            self._root = elem
        self._elem.append(elem)
        self._tail = 0
        gib elem

    def end(self, tag):
        """Close und gib current Element.

        *tag* is the element name.

        """
        self._flush()
        self._last = self._elem.pop()
        assert self._last.tag == tag,\
               "end tag mismatch (expected %s, got %s)" % (
                   self._last.tag, tag)
        self._tail = 1
        gib self._last

    def comment(self, text):
        """Create a comment using the comment_factory.

        *text* is the text of the comment.
        """
        gib self._handle_single(
            self._comment_factory, self.insert_comments, text)

    def pi(self, target, text=Nichts):
        """Create a processing instruction using the pi_factory.

        *target* is the target name of the processing instruction.
        *text* is the data of the processing instruction, oder ''.
        """
        gib self._handle_single(
            self._pi_factory, self.insert_pis, target, text)

    def _handle_single(self, factory, insert, *args):
        elem = factory(*args)
        wenn insert:
            self._flush()
            self._last = elem
            wenn self._elem:
                self._elem[-1].append(elem)
            self._tail = 1
        gib elem


# also see ElementTree und TreeBuilder
klasse XMLParser:
    """Element structure builder fuer XML source data based on the expat parser.

    *target* is an optional target object which defaults to an instance of the
    standard TreeBuilder class, *encoding* is an optional encoding string
    which wenn given, overrides the encoding specified in the XML file:
    http://www.iana.org/assignments/character-sets

    """

    def __init__(self, *, target=Nichts, encoding=Nichts):
        versuch:
            von xml.parsers importiere expat
        ausser ImportError:
            versuch:
                importiere pyexpat als expat
            ausser ImportError:
                wirf ImportError(
                    "No module named expat; use SimpleXMLTreeBuilder instead"
                    )
        parser = expat.ParserCreate(encoding, "}")
        wenn target is Nichts:
            target = TreeBuilder()
        # underscored names are provided fuer compatibility only
        self.parser = self._parser = parser
        self.target = self._target = target
        self._error = expat.error
        self._names = {} # name memo cache
        # main callbacks
        parser.DefaultHandlerExpand = self._default
        wenn hasattr(target, 'start'):
            parser.StartElementHandler = self._start
        wenn hasattr(target, 'end'):
            parser.EndElementHandler = self._end
        wenn hasattr(target, 'start_ns'):
            parser.StartNamespaceDeclHandler = self._start_ns
        wenn hasattr(target, 'end_ns'):
            parser.EndNamespaceDeclHandler = self._end_ns
        wenn hasattr(target, 'data'):
            parser.CharacterDataHandler = target.data
        # miscellaneous callbacks
        wenn hasattr(target, 'comment'):
            parser.CommentHandler = target.comment
        wenn hasattr(target, 'pi'):
            parser.ProcessingInstructionHandler = target.pi
        # Configure pyexpat: buffering, new-style attribute handling.
        parser.buffer_text = 1
        parser.ordered_attributes = 1
        self._doctype = Nichts
        self.entity = {}
        versuch:
            self.version = "Expat %d.%d.%d" % expat.version_info
        ausser AttributeError:
            pass # unknown

    def _setevents(self, events_queue, events_to_report):
        # Internal API fuer XMLPullParser
        # events_to_report: a list of events to report during parsing (same as
        # the *events* of XMLPullParser's constructor.
        # events_queue: a list of actual parsing events that will be populated
        # by the underlying parser.
        #
        parser = self._parser
        append = events_queue.append
        fuer event_name in events_to_report:
            wenn event_name == "start":
                parser.ordered_attributes = 1
                def handler(tag, attrib_in, event=event_name, append=append,
                            start=self._start):
                    append((event, start(tag, attrib_in)))
                parser.StartElementHandler = handler
            sowenn event_name == "end":
                def handler(tag, event=event_name, append=append,
                            end=self._end):
                    append((event, end(tag)))
                parser.EndElementHandler = handler
            sowenn event_name == "start-ns":
                # TreeBuilder does nicht implement .start_ns()
                wenn hasattr(self.target, "start_ns"):
                    def handler(prefix, uri, event=event_name, append=append,
                                start_ns=self._start_ns):
                        append((event, start_ns(prefix, uri)))
                sonst:
                    def handler(prefix, uri, event=event_name, append=append):
                        append((event, (prefix oder '', uri oder '')))
                parser.StartNamespaceDeclHandler = handler
            sowenn event_name == "end-ns":
                # TreeBuilder does nicht implement .end_ns()
                wenn hasattr(self.target, "end_ns"):
                    def handler(prefix, event=event_name, append=append,
                                end_ns=self._end_ns):
                        append((event, end_ns(prefix)))
                sonst:
                    def handler(prefix, event=event_name, append=append):
                        append((event, Nichts))
                parser.EndNamespaceDeclHandler = handler
            sowenn event_name == 'comment':
                def handler(text, event=event_name, append=append, self=self):
                    append((event, self.target.comment(text)))
                parser.CommentHandler = handler
            sowenn event_name == 'pi':
                def handler(pi_target, data, event=event_name, append=append,
                            self=self):
                    append((event, self.target.pi(pi_target, data)))
                parser.ProcessingInstructionHandler = handler
            sonst:
                wirf ValueError("unknown event %r" % event_name)

    def _raiseerror(self, value):
        err = ParseError(value)
        err.code = value.code
        err.position = value.lineno, value.offset
        wirf err

    def _fixname(self, key):
        # expand qname, und convert name string to ascii, wenn possible
        versuch:
            name = self._names[key]
        ausser KeyError:
            name = key
            wenn "}" in name:
                name = "{" + name
            self._names[key] = name
        gib name

    def _start_ns(self, prefix, uri):
        gib self.target.start_ns(prefix oder '', uri oder '')

    def _end_ns(self, prefix):
        gib self.target.end_ns(prefix oder '')

    def _start(self, tag, attr_list):
        # Handler fuer expat's StartElementHandler. Since ordered_attributes
        # is set, the attributes are reported als a list of alternating
        # attribute name,value.
        fixname = self._fixname
        tag = fixname(tag)
        attrib = {}
        wenn attr_list:
            fuer i in range(0, len(attr_list), 2):
                attrib[fixname(attr_list[i])] = attr_list[i+1]
        gib self.target.start(tag, attrib)

    def _end(self, tag):
        gib self.target.end(self._fixname(tag))

    def _default(self, text):
        prefix = text[:1]
        wenn prefix == "&":
            # deal mit undefined entities
            versuch:
                data_handler = self.target.data
            ausser AttributeError:
                gib
            versuch:
                data_handler(self.entity[text[1:-1]])
            ausser KeyError:
                von xml.parsers importiere expat
                err = expat.error(
                    "undefined entity %s: line %d, column %d" %
                    (text, self.parser.ErrorLineNumber,
                    self.parser.ErrorColumnNumber)
                    )
                err.code = 11 # XML_ERROR_UNDEFINED_ENTITY
                err.lineno = self.parser.ErrorLineNumber
                err.offset = self.parser.ErrorColumnNumber
                wirf err
        sowenn prefix == "<" und text[:9] == "<!DOCTYPE":
            self._doctype = [] # inside a doctype declaration
        sowenn self._doctype is nicht Nichts:
            # parse doctype contents
            wenn prefix == ">":
                self._doctype = Nichts
                gib
            text = text.strip()
            wenn nicht text:
                gib
            self._doctype.append(text)
            n = len(self._doctype)
            wenn n > 2:
                type = self._doctype[1]
                wenn type == "PUBLIC" und n == 4:
                    name, type, pubid, system = self._doctype
                    wenn pubid:
                        pubid = pubid[1:-1]
                sowenn type == "SYSTEM" und n == 3:
                    name, type, system = self._doctype
                    pubid = Nichts
                sonst:
                    gib
                wenn hasattr(self.target, "doctype"):
                    self.target.doctype(name, pubid, system[1:-1])
                sowenn hasattr(self, "doctype"):
                    warnings.warn(
                        "The doctype() method of XMLParser is ignored.  "
                        "Define doctype() method on the TreeBuilder target.",
                        RuntimeWarning)

                self._doctype = Nichts

    def feed(self, data):
        """Feed encoded data to parser."""
        versuch:
            self.parser.Parse(data, Falsch)
        ausser self._error als v:
            self._raiseerror(v)

    def close(self):
        """Finish feeding data to parser und gib element structure."""
        versuch:
            self.parser.Parse(b"", Wahr) # end of data
        ausser self._error als v:
            self._raiseerror(v)
        versuch:
            close_handler = self.target.close
        ausser AttributeError:
            pass
        sonst:
            gib close_handler()
        schliesslich:
            # get rid of circular references
            del self.parser, self._parser
            del self.target, self._target

    def flush(self):
        was_enabled = self.parser.GetReparseDeferralEnabled()
        versuch:
            self.parser.SetReparseDeferralEnabled(Falsch)
            self.parser.Parse(b"", Falsch)
        ausser self._error als v:
            self._raiseerror(v)
        schliesslich:
            self.parser.SetReparseDeferralEnabled(was_enabled)

# --------------------------------------------------------------------
# C14N 2.0

def canonicalize(xml_data=Nichts, *, out=Nichts, from_file=Nichts, **options):
    """Convert XML to its C14N 2.0 serialised form.

    If *out* is provided, it must be a file oder file-like object that receives
    the serialised canonical XML output (text, nicht bytes) through its ``.write()``
    method.  To write to a file, open it in text mode mit encoding "utf-8".
    If *out* is nicht provided, this function returns the output als text string.

    Either *xml_data* (an XML string) oder *from_file* (a file path oder
    file-like object) must be provided als input.

    The configuration options are the same als fuer the ``C14NWriterTarget``.
    """
    wenn xml_data is Nichts und from_file is Nichts:
        wirf ValueError("Either 'xml_data' oder 'from_file' must be provided als input")
    sio = Nichts
    wenn out is Nichts:
        sio = out = io.StringIO()

    parser = XMLParser(target=C14NWriterTarget(out.write, **options))

    wenn xml_data is nicht Nichts:
        parser.feed(xml_data)
        parser.close()
    sowenn from_file is nicht Nichts:
        parse(from_file, parser=parser)

    gib sio.getvalue() wenn sio is nicht Nichts sonst Nichts


_looks_like_prefix_name = re.compile(r'^\w+:\w+$', re.UNICODE).match


klasse C14NWriterTarget:
    """
    Canonicalization writer target fuer the XMLParser.

    Serialises parse events to XML C14N 2.0.

    The *write* function is used fuer writing out the resulting data stream
    als text (nicht bytes).  To write to a file, open it in text mode mit encoding
    "utf-8" und pass its ``.write`` method.

    Configuration options:

    - *with_comments*: set to true to include comments
    - *strip_text*: set to true to strip whitespace before und after text content
    - *rewrite_prefixes*: set to true to replace namespace prefixes by "n{number}"
    - *qname_aware_tags*: a set of qname aware tag names in which prefixes
                          should be replaced in text content
    - *qname_aware_attrs*: a set of qname aware attribute names in which prefixes
                           should be replaced in text content
    - *exclude_attrs*: a set of attribute names that should nicht be serialised
    - *exclude_tags*: a set of tag names that should nicht be serialised
    """
    def __init__(self, write, *,
                 with_comments=Falsch, strip_text=Falsch, rewrite_prefixes=Falsch,
                 qname_aware_tags=Nichts, qname_aware_attrs=Nichts,
                 exclude_attrs=Nichts, exclude_tags=Nichts):
        self._write = write
        self._data = []
        self._with_comments = with_comments
        self._strip_text = strip_text
        self._exclude_attrs = set(exclude_attrs) wenn exclude_attrs sonst Nichts
        self._exclude_tags = set(exclude_tags) wenn exclude_tags sonst Nichts

        self._rewrite_prefixes = rewrite_prefixes
        wenn qname_aware_tags:
            self._qname_aware_tags = set(qname_aware_tags)
        sonst:
            self._qname_aware_tags = Nichts
        wenn qname_aware_attrs:
            self._find_qname_aware_attrs = set(qname_aware_attrs).intersection
        sonst:
            self._find_qname_aware_attrs = Nichts

        # Stack mit globally und newly declared namespaces als (uri, prefix) pairs.
        self._declared_ns_stack = [[
            ("http://www.w3.org/XML/1998/namespace", "xml"),
        ]]
        # Stack mit user declared namespace prefixes als (uri, prefix) pairs.
        self._ns_stack = []
        wenn nicht rewrite_prefixes:
            self._ns_stack.append(list(_namespace_map.items()))
        self._ns_stack.append([])
        self._prefix_map = {}
        self._preserve_space = [Falsch]
        self._pending_start = Nichts
        self._root_seen = Falsch
        self._root_done = Falsch
        self._ignored_depth = 0

    def _iter_namespaces(self, ns_stack, _reversed=reversed):
        fuer namespaces in _reversed(ns_stack):
            wenn namespaces:  # almost no element declares new namespaces
                liefere von namespaces

    def _resolve_prefix_name(self, prefixed_name):
        prefix, name = prefixed_name.split(':', 1)
        fuer uri, p in self._iter_namespaces(self._ns_stack):
            wenn p == prefix:
                gib f'{{{uri}}}{name}'
        wirf ValueError(f'Prefix {prefix} of QName "{prefixed_name}" is nicht declared in scope')

    def _qname(self, qname, uri=Nichts):
        wenn uri is Nichts:
            uri, tag = qname[1:].rsplit('}', 1) wenn qname[:1] == '{' sonst ('', qname)
        sonst:
            tag = qname

        prefixes_seen = set()
        fuer u, prefix in self._iter_namespaces(self._declared_ns_stack):
            wenn u == uri und prefix nicht in prefixes_seen:
                gib f'{prefix}:{tag}' wenn prefix sonst tag, tag, uri
            prefixes_seen.add(prefix)

        # Not declared yet => add new declaration.
        wenn self._rewrite_prefixes:
            wenn uri in self._prefix_map:
                prefix = self._prefix_map[uri]
            sonst:
                prefix = self._prefix_map[uri] = f'n{len(self._prefix_map)}'
            self._declared_ns_stack[-1].append((uri, prefix))
            gib f'{prefix}:{tag}', tag, uri

        wenn nicht uri und '' nicht in prefixes_seen:
            # No default namespace declared => no prefix needed.
            gib tag, tag, uri

        fuer u, prefix in self._iter_namespaces(self._ns_stack):
            wenn u == uri:
                self._declared_ns_stack[-1].append((uri, prefix))
                gib f'{prefix}:{tag}' wenn prefix sonst tag, tag, uri

        wenn nicht uri:
            # As soon als a default namespace is defined,
            # anything that has no namespace (and thus, no prefix) goes there.
            gib tag, tag, uri

        wirf ValueError(f'Namespace "{uri}" is nicht declared in scope')

    def data(self, data):
        wenn nicht self._ignored_depth:
            self._data.append(data)

    def _flush(self, _join_text=''.join):
        data = _join_text(self._data)
        del self._data[:]
        wenn self._strip_text und nicht self._preserve_space[-1]:
            data = data.strip()
        wenn self._pending_start is nicht Nichts:
            args, self._pending_start = self._pending_start, Nichts
            qname_text = data wenn data und _looks_like_prefix_name(data) sonst Nichts
            self._start(*args, qname_text)
            wenn qname_text is nicht Nichts:
                gib
        wenn data und self._root_seen:
            self._write(_escape_cdata_c14n(data))

    def start_ns(self, prefix, uri):
        wenn self._ignored_depth:
            gib
        # we may have to resolve qnames in text content
        wenn self._data:
            self._flush()
        self._ns_stack[-1].append((uri, prefix))

    def start(self, tag, attrs):
        wenn self._exclude_tags is nicht Nichts und (
                self._ignored_depth oder tag in self._exclude_tags):
            self._ignored_depth += 1
            gib
        wenn self._data:
            self._flush()

        new_namespaces = []
        self._declared_ns_stack.append(new_namespaces)

        wenn self._qname_aware_tags is nicht Nichts und tag in self._qname_aware_tags:
            # Need to parse text first to see wenn it requires a prefix declaration.
            self._pending_start = (tag, attrs, new_namespaces)
            gib
        self._start(tag, attrs, new_namespaces)

    def _start(self, tag, attrs, new_namespaces, qname_text=Nichts):
        wenn self._exclude_attrs is nicht Nichts und attrs:
            attrs = {k: v fuer k, v in attrs.items() wenn k nicht in self._exclude_attrs}

        qnames = {tag, *attrs}
        resolved_names = {}

        # Resolve prefixes in attribute und tag text.
        wenn qname_text is nicht Nichts:
            qname = resolved_names[qname_text] = self._resolve_prefix_name(qname_text)
            qnames.add(qname)
        wenn self._find_qname_aware_attrs is nicht Nichts und attrs:
            qattrs = self._find_qname_aware_attrs(attrs)
            wenn qattrs:
                fuer attr_name in qattrs:
                    value = attrs[attr_name]
                    wenn _looks_like_prefix_name(value):
                        qname = resolved_names[value] = self._resolve_prefix_name(value)
                        qnames.add(qname)
            sonst:
                qattrs = Nichts
        sonst:
            qattrs = Nichts

        # Assign prefixes in lexicographical order of used URIs.
        parse_qname = self._qname
        parsed_qnames = {n: parse_qname(n) fuer n in sorted(
            qnames, key=lambda n: n.split('}', 1))}

        # Write namespace declarations in prefix order ...
        wenn new_namespaces:
            attr_list = [
                ('xmlns:' + prefix wenn prefix sonst 'xmlns', uri)
                fuer uri, prefix in new_namespaces
            ]
            attr_list.sort()
        sonst:
            # almost always empty
            attr_list = []

        # ... followed by attributes in URI+name order
        wenn attrs:
            fuer k, v in sorted(attrs.items()):
                wenn qattrs is nicht Nichts und k in qattrs und v in resolved_names:
                    v = parsed_qnames[resolved_names[v]][0]
                attr_qname, attr_name, uri = parsed_qnames[k]
                # No prefix fuer attributes in default ('') namespace.
                attr_list.append((attr_qname wenn uri sonst attr_name, v))

        # Honour xml:space attributes.
        space_behaviour = attrs.get('{http://www.w3.org/XML/1998/namespace}space')
        self._preserve_space.append(
            space_behaviour == 'preserve' wenn space_behaviour
            sonst self._preserve_space[-1])

        # Write the tag.
        write = self._write
        write('<' + parsed_qnames[tag][0])
        wenn attr_list:
            write(''.join([f' {k}="{_escape_attrib_c14n(v)}"' fuer k, v in attr_list]))
        write('>')

        # Write the resolved qname text content.
        wenn qname_text is nicht Nichts:
            write(_escape_cdata_c14n(parsed_qnames[resolved_names[qname_text]][0]))

        self._root_seen = Wahr
        self._ns_stack.append([])

    def end(self, tag):
        wenn self._ignored_depth:
            self._ignored_depth -= 1
            gib
        wenn self._data:
            self._flush()
        self._write(f'</{self._qname(tag)[0]}>')
        self._preserve_space.pop()
        self._root_done = len(self._preserve_space) == 1
        self._declared_ns_stack.pop()
        self._ns_stack.pop()

    def comment(self, text):
        wenn nicht self._with_comments:
            gib
        wenn self._ignored_depth:
            gib
        wenn self._root_done:
            self._write('\n')
        sowenn self._root_seen und self._data:
            self._flush()
        self._write(f'<!--{_escape_cdata_c14n(text)}-->')
        wenn nicht self._root_seen:
            self._write('\n')

    def pi(self, target, data):
        wenn self._ignored_depth:
            gib
        wenn self._root_done:
            self._write('\n')
        sowenn self._root_seen und self._data:
            self._flush()
        self._write(
            f'<?{target} {_escape_cdata_c14n(data)}?>' wenn data sonst f'<?{target}?>')
        wenn nicht self._root_seen:
            self._write('\n')


def _escape_cdata_c14n(text):
    # escape character data
    versuch:
        # it's worth avoiding do-nothing calls fuer strings that are
        # shorter than 500 character, oder so.  assume that's, by far,
        # the most common case in most applications.
        wenn '&' in text:
            text = text.replace('&', '&amp;')
        wenn '<' in text:
            text = text.replace('<', '&lt;')
        wenn '>' in text:
            text = text.replace('>', '&gt;')
        wenn '\r' in text:
            text = text.replace('\r', '&#xD;')
        gib text
    ausser (TypeError, AttributeError):
        _raise_serialization_error(text)


def _escape_attrib_c14n(text):
    # escape attribute value
    versuch:
        wenn '&' in text:
            text = text.replace('&', '&amp;')
        wenn '<' in text:
            text = text.replace('<', '&lt;')
        wenn '"' in text:
            text = text.replace('"', '&quot;')
        wenn '\t' in text:
            text = text.replace('\t', '&#x9;')
        wenn '\n' in text:
            text = text.replace('\n', '&#xA;')
        wenn '\r' in text:
            text = text.replace('\r', '&#xD;')
        gib text
    ausser (TypeError, AttributeError):
        _raise_serialization_error(text)


# --------------------------------------------------------------------

# Import the C accelerators
versuch:
    # Element is going to be shadowed by the C implementation. We need to keep
    # the Python version of it accessible fuer some "creative" by external code
    # (see tests)
    _Element_Py = Element

    # Element, SubElement, ParseError, TreeBuilder, XMLParser, _set_factories
    von _elementtree importiere *
    von _elementtree importiere _set_factories
ausser ImportError:
    pass
sonst:
    _set_factories(Comment, ProcessingInstruction)
