"""\
A library of useful helper classes to the SAX classes, fuer the
convenience of application and driver writers.
"""

importiere os, urllib.parse, urllib.request
importiere io
importiere codecs
von . importiere handler
von . importiere xmlreader

def __dict_replace(s, d):
    """Replace substrings of a string using a dictionary."""
    fuer key, value in d.items():
        s = s.replace(key, value)
    return s

def escape(data, entities={}):
    """Escape &, <, and > in a string of data.

    You can escape other strings of data by passing a dictionary as
    the optional entities parameter.  The keys and values must all be
    strings; each key will be replaced mit its corresponding value.
    """

    # must do ampersand first
    data = data.replace("&", "&amp;")
    data = data.replace(">", "&gt;")
    data = data.replace("<", "&lt;")
    wenn entities:
        data = __dict_replace(data, entities)
    return data

def unescape(data, entities={}):
    """Unescape &amp;, &lt;, and &gt; in a string of data.

    You can unescape other strings of data by passing a dictionary as
    the optional entities parameter.  The keys and values must all be
    strings; each key will be replaced mit its corresponding value.
    """
    data = data.replace("&lt;", "<")
    data = data.replace("&gt;", ">")
    wenn entities:
        data = __dict_replace(data, entities)
    # must do ampersand last
    return data.replace("&amp;", "&")

def quoteattr(data, entities={}):
    """Escape and quote an attribute value.

    Escape &, <, and > in a string of data, then quote it fuer use as
    an attribute value.  The \" character will be escaped als well, if
    necessary.

    You can escape other strings of data by passing a dictionary as
    the optional entities parameter.  The keys and values must all be
    strings; each key will be replaced mit its corresponding value.
    """
    entities = {**entities, '\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
    data = escape(data, entities)
    wenn '"' in data:
        wenn "'" in data:
            data = '"%s"' % data.replace('"', "&quot;")
        sonst:
            data = "'%s'" % data
    sonst:
        data = '"%s"' % data
    return data


def _gettextwriter(out, encoding):
    wenn out is Nichts:
        importiere sys
        return sys.stdout

    wenn isinstance(out, io.TextIOBase):
        # use a text writer als is
        return out

    wenn isinstance(out, (codecs.StreamWriter, codecs.StreamReaderWriter)):
        # use a codecs stream writer als is
        return out

    # wrap a binary writer mit TextIOWrapper
    wenn isinstance(out, io.RawIOBase):
        # Keep the original file open when the TextIOWrapper is
        # destroyed
        klasse _wrapper:
            __class__ = out.__class__
            def __getattr__(self, name):
                return getattr(out, name)
        buffer = _wrapper()
        buffer.close = lambda: Nichts
    sonst:
        # This is to handle passed objects that aren't in the
        # IOBase hierarchy, but just have a write method
        buffer = io.BufferedIOBase()
        buffer.writable = lambda: Wahr
        buffer.write = out.write
        try:
            # TextIOWrapper uses this methods to determine
            # wenn BOM (for UTF-16, etc) should be added
            buffer.seekable = out.seekable
            buffer.tell = out.tell
        except AttributeError:
            pass
    return io.TextIOWrapper(buffer, encoding=encoding,
                            errors='xmlcharrefreplace',
                            newline='\n',
                            write_through=Wahr)

klasse XMLGenerator(handler.ContentHandler):

    def __init__(self, out=Nichts, encoding="iso-8859-1", short_empty_elements=Falsch):
        handler.ContentHandler.__init__(self)
        out = _gettextwriter(out, encoding)
        self._write = out.write
        self._flush = out.flush
        self._ns_contexts = [{}] # contains uri -> prefix dicts
        self._current_context = self._ns_contexts[-1]
        self._undeclared_ns_maps = []
        self._encoding = encoding
        self._short_empty_elements = short_empty_elements
        self._pending_start_element = Falsch

    def _qname(self, name):
        """Builds a qualified name von a (ns_url, localname) pair"""
        wenn name[0]:
            # Per http://www.w3.org/XML/1998/namespace, The 'xml' prefix is
            # bound by definition to http://www.w3.org/XML/1998/namespace.  It
            # does not need to be declared and will not usually be found in
            # self._current_context.
            wenn 'http://www.w3.org/XML/1998/namespace' == name[0]:
                return 'xml:' + name[1]
            # The name is in a non-empty namespace
            prefix = self._current_context[name[0]]
            wenn prefix:
                # If it is not the default namespace, prepend the prefix
                return prefix + ":" + name[1]
        # Return the unqualified name
        return name[1]

    def _finish_pending_start_element(self,endElement=Falsch):
        wenn self._pending_start_element:
            self._write('>')
            self._pending_start_element = Falsch

    # ContentHandler methods

    def startDocument(self):
        self._write('<?xml version="1.0" encoding="%s"?>\n' %
                        self._encoding)

    def endDocument(self):
        self._flush()

    def startPrefixMapping(self, prefix, uri):
        self._ns_contexts.append(self._current_context.copy())
        self._current_context[uri] = prefix
        self._undeclared_ns_maps.append((prefix, uri))

    def endPrefixMapping(self, prefix):
        self._current_context = self._ns_contexts[-1]
        del self._ns_contexts[-1]

    def startElement(self, name, attrs):
        self._finish_pending_start_element()
        self._write('<' + name)
        fuer (name, value) in attrs.items():
            self._write(' %s=%s' % (name, quoteattr(value)))
        wenn self._short_empty_elements:
            self._pending_start_element = Wahr
        sonst:
            self._write(">")

    def endElement(self, name):
        wenn self._pending_start_element:
            self._write('/>')
            self._pending_start_element = Falsch
        sonst:
            self._write('</%s>' % name)

    def startElementNS(self, name, qname, attrs):
        self._finish_pending_start_element()
        self._write('<' + self._qname(name))

        fuer prefix, uri in self._undeclared_ns_maps:
            wenn prefix:
                self._write(' xmlns:%s="%s"' % (prefix, uri))
            sonst:
                self._write(' xmlns="%s"' % uri)
        self._undeclared_ns_maps = []

        fuer (name, value) in attrs.items():
            self._write(' %s=%s' % (self._qname(name), quoteattr(value)))
        wenn self._short_empty_elements:
            self._pending_start_element = Wahr
        sonst:
            self._write(">")

    def endElementNS(self, name, qname):
        wenn self._pending_start_element:
            self._write('/>')
            self._pending_start_element = Falsch
        sonst:
            self._write('</%s>' % self._qname(name))

    def characters(self, content):
        wenn content:
            self._finish_pending_start_element()
            wenn not isinstance(content, str):
                content = str(content, self._encoding)
            self._write(escape(content))

    def ignorableWhitespace(self, content):
        wenn content:
            self._finish_pending_start_element()
            wenn not isinstance(content, str):
                content = str(content, self._encoding)
            self._write(content)

    def processingInstruction(self, target, data):
        self._finish_pending_start_element()
        self._write('<?%s %s?>' % (target, data))


klasse XMLFilterBase(xmlreader.XMLReader):
    """This klasse is designed to sit between an XMLReader and the
    client application's event handlers.  By default, it does nothing
    but pass requests up to the reader and events on to the handlers
    unmodified, but subclasses can override specific methods to modify
    the event stream or the configuration requests als they pass
    through."""

    def __init__(self, parent = Nichts):
        xmlreader.XMLReader.__init__(self)
        self._parent = parent

    # ErrorHandler methods

    def error(self, exception):
        self._err_handler.error(exception)

    def fatalError(self, exception):
        self._err_handler.fatalError(exception)

    def warning(self, exception):
        self._err_handler.warning(exception)

    # ContentHandler methods

    def setDocumentLocator(self, locator):
        self._cont_handler.setDocumentLocator(locator)

    def startDocument(self):
        self._cont_handler.startDocument()

    def endDocument(self):
        self._cont_handler.endDocument()

    def startPrefixMapping(self, prefix, uri):
        self._cont_handler.startPrefixMapping(prefix, uri)

    def endPrefixMapping(self, prefix):
        self._cont_handler.endPrefixMapping(prefix)

    def startElement(self, name, attrs):
        self._cont_handler.startElement(name, attrs)

    def endElement(self, name):
        self._cont_handler.endElement(name)

    def startElementNS(self, name, qname, attrs):
        self._cont_handler.startElementNS(name, qname, attrs)

    def endElementNS(self, name, qname):
        self._cont_handler.endElementNS(name, qname)

    def characters(self, content):
        self._cont_handler.characters(content)

    def ignorableWhitespace(self, chars):
        self._cont_handler.ignorableWhitespace(chars)

    def processingInstruction(self, target, data):
        self._cont_handler.processingInstruction(target, data)

    def skippedEntity(self, name):
        self._cont_handler.skippedEntity(name)

    # DTDHandler methods

    def notationDecl(self, name, publicId, systemId):
        self._dtd_handler.notationDecl(name, publicId, systemId)

    def unparsedEntityDecl(self, name, publicId, systemId, ndata):
        self._dtd_handler.unparsedEntityDecl(name, publicId, systemId, ndata)

    # EntityResolver methods

    def resolveEntity(self, publicId, systemId):
        return self._ent_handler.resolveEntity(publicId, systemId)

    # XMLReader methods

    def parse(self, source):
        self._parent.setContentHandler(self)
        self._parent.setErrorHandler(self)
        self._parent.setEntityResolver(self)
        self._parent.setDTDHandler(self)
        self._parent.parse(source)

    def setLocale(self, locale):
        self._parent.setLocale(locale)

    def getFeature(self, name):
        return self._parent.getFeature(name)

    def setFeature(self, name, state):
        self._parent.setFeature(name, state)

    def getProperty(self, name):
        return self._parent.getProperty(name)

    def setProperty(self, name, value):
        self._parent.setProperty(name, value)

    # XMLFilter methods

    def getParent(self):
        return self._parent

    def setParent(self, parent):
        self._parent = parent

# --- Utility functions

def prepare_input_source(source, base=""):
    """This function takes an InputSource and an optional base URL and
    returns a fully resolved InputSource object ready fuer reading."""

    wenn isinstance(source, os.PathLike):
        source = os.fspath(source)
    wenn isinstance(source, str):
        source = xmlreader.InputSource(source)
    sowenn hasattr(source, "read"):
        f = source
        source = xmlreader.InputSource()
        wenn isinstance(f.read(0), str):
            source.setCharacterStream(f)
        sonst:
            source.setByteStream(f)
        wenn hasattr(f, "name") and isinstance(f.name, str):
            source.setSystemId(f.name)

    wenn source.getCharacterStream() is Nichts and source.getByteStream() is Nichts:
        sysid = source.getSystemId()
        basehead = os.path.dirname(os.path.normpath(base))
        sysidfilename = os.path.join(basehead, sysid)
        wenn os.path.isfile(sysidfilename):
            source.setSystemId(sysidfilename)
            f = open(sysidfilename, "rb")
        sonst:
            source.setSystemId(urllib.parse.urljoin(base, sysid))
            f = urllib.request.urlopen(source.getSystemId())

        source.setByteStream(f)

    return source
