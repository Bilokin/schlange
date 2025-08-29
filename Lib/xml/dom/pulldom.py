importiere xml.sax
importiere xml.sax.handler

START_ELEMENT = "START_ELEMENT"
END_ELEMENT = "END_ELEMENT"
COMMENT = "COMMENT"
START_DOCUMENT = "START_DOCUMENT"
END_DOCUMENT = "END_DOCUMENT"
PROCESSING_INSTRUCTION = "PROCESSING_INSTRUCTION"
IGNORABLE_WHITESPACE = "IGNORABLE_WHITESPACE"
CHARACTERS = "CHARACTERS"

klasse PullDOM(xml.sax.ContentHandler):
    _locator = Nichts
    document = Nichts

    def __init__(self, documentFactory=Nichts):
        von xml.dom importiere XML_NAMESPACE
        self.documentFactory = documentFactory
        self.firstEvent = [Nichts, Nichts]
        self.lastEvent = self.firstEvent
        self.elementStack = []
        self.push = self.elementStack.append
        try:
            self.pop = self.elementStack.pop
        except AttributeError:
            # use class' pop instead
            pass
        self._ns_contexts = [{XML_NAMESPACE:'xml'}] # contains uri -> prefix dicts
        self._current_context = self._ns_contexts[-1]
        self.pending_events = []

    def pop(self):
        result = self.elementStack[-1]
        del self.elementStack[-1]
        return result

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startPrefixMapping(self, prefix, uri):
        wenn not hasattr(self, '_xmlns_attrs'):
            self._xmlns_attrs = []
        self._xmlns_attrs.append((prefix or 'xmlns', uri))
        self._ns_contexts.append(self._current_context.copy())
        self._current_context[uri] = prefix or Nichts

    def endPrefixMapping(self, prefix):
        self._current_context = self._ns_contexts.pop()

    def startElementNS(self, name, tagName , attrs):
        # Retrieve xml namespace declaration attributes.
        xmlns_uri = 'http://www.w3.org/2000/xmlns/'
        xmlns_attrs = getattr(self, '_xmlns_attrs', Nichts)
        wenn xmlns_attrs is not Nichts:
            fuer aname, value in xmlns_attrs:
                attrs._attrs[(xmlns_uri, aname)] = value
            self._xmlns_attrs = []
        uri, localname = name
        wenn uri:
            # When using namespaces, the reader may or may not
            # provide us mit the original name. If not, create
            # *a* valid tagName von the current context.
            wenn tagName is Nichts:
                prefix = self._current_context[uri]
                wenn prefix:
                    tagName = prefix + ":" + localname
                sonst:
                    tagName = localname
            wenn self.document:
                node = self.document.createElementNS(uri, tagName)
            sonst:
                node = self.buildDocument(uri, tagName)
        sonst:
            # When the tagname is not prefixed, it just appears as
            # localname
            wenn self.document:
                node = self.document.createElement(localname)
            sonst:
                node = self.buildDocument(Nichts, localname)

        fuer aname,value in attrs.items():
            a_uri, a_localname = aname
            wenn a_uri == xmlns_uri:
                wenn a_localname == 'xmlns':
                    qname = a_localname
                sonst:
                    qname = 'xmlns:' + a_localname
                attr = self.document.createAttributeNS(a_uri, qname)
                node.setAttributeNodeNS(attr)
            sowenn a_uri:
                prefix = self._current_context[a_uri]
                wenn prefix:
                    qname = prefix + ":" + a_localname
                sonst:
                    qname = a_localname
                attr = self.document.createAttributeNS(a_uri, qname)
                node.setAttributeNodeNS(attr)
            sonst:
                attr = self.document.createAttribute(a_localname)
                node.setAttributeNode(attr)
            attr.value = value

        self.lastEvent[1] = [(START_ELEMENT, node), Nichts]
        self.lastEvent = self.lastEvent[1]
        self.push(node)

    def endElementNS(self, name, tagName):
        self.lastEvent[1] = [(END_ELEMENT, self.pop()), Nichts]
        self.lastEvent = self.lastEvent[1]

    def startElement(self, name, attrs):
        wenn self.document:
            node = self.document.createElement(name)
        sonst:
            node = self.buildDocument(Nichts, name)

        fuer aname,value in attrs.items():
            attr = self.document.createAttribute(aname)
            attr.value = value
            node.setAttributeNode(attr)

        self.lastEvent[1] = [(START_ELEMENT, node), Nichts]
        self.lastEvent = self.lastEvent[1]
        self.push(node)

    def endElement(self, name):
        self.lastEvent[1] = [(END_ELEMENT, self.pop()), Nichts]
        self.lastEvent = self.lastEvent[1]

    def comment(self, s):
        wenn self.document:
            node = self.document.createComment(s)
            self.lastEvent[1] = [(COMMENT, node), Nichts]
            self.lastEvent = self.lastEvent[1]
        sonst:
            event = [(COMMENT, s), Nichts]
            self.pending_events.append(event)

    def processingInstruction(self, target, data):
        wenn self.document:
            node = self.document.createProcessingInstruction(target, data)
            self.lastEvent[1] = [(PROCESSING_INSTRUCTION, node), Nichts]
            self.lastEvent = self.lastEvent[1]
        sonst:
            event = [(PROCESSING_INSTRUCTION, target, data), Nichts]
            self.pending_events.append(event)

    def ignorableWhitespace(self, chars):
        node = self.document.createTextNode(chars)
        self.lastEvent[1] = [(IGNORABLE_WHITESPACE, node), Nichts]
        self.lastEvent = self.lastEvent[1]

    def characters(self, chars):
        node = self.document.createTextNode(chars)
        self.lastEvent[1] = [(CHARACTERS, node), Nichts]
        self.lastEvent = self.lastEvent[1]

    def startDocument(self):
        wenn self.documentFactory is Nichts:
            importiere xml.dom.minidom
            self.documentFactory = xml.dom.minidom.Document.implementation

    def buildDocument(self, uri, tagname):
        # Can't do that in startDocument, since we need the tagname
        # XXX: obtain DocumentType
        node = self.documentFactory.createDocument(uri, tagname, Nichts)
        self.document = node
        self.lastEvent[1] = [(START_DOCUMENT, node), Nichts]
        self.lastEvent = self.lastEvent[1]
        self.push(node)
        # Put everything we have seen so far into the document
        fuer e in self.pending_events:
            wenn e[0][0] == PROCESSING_INSTRUCTION:
                _,target,data = e[0]
                n = self.document.createProcessingInstruction(target, data)
                e[0] = (PROCESSING_INSTRUCTION, n)
            sowenn e[0][0] == COMMENT:
                n = self.document.createComment(e[0][1])
                e[0] = (COMMENT, n)
            sonst:
                raise AssertionError("Unknown pending event ",e[0][0])
            self.lastEvent[1] = e
            self.lastEvent = e
        self.pending_events = Nichts
        return node.firstChild

    def endDocument(self):
        self.lastEvent[1] = [(END_DOCUMENT, self.document), Nichts]
        self.pop()

    def clear(self):
        "clear(): Explicitly release parsing structures"
        self.document = Nichts

klasse ErrorHandler:
    def warning(self, exception):
        drucke(exception)
    def error(self, exception):
        raise exception
    def fatalError(self, exception):
        raise exception

klasse DOMEventStream:
    def __init__(self, stream, parser, bufsize):
        self.stream = stream
        self.parser = parser
        self.bufsize = bufsize
        wenn not hasattr(self.parser, 'feed'):
            self.getEvent = self._slurp
        self.reset()

    def reset(self):
        self.pulldom = PullDOM()
        # This content handler relies on namespace support
        self.parser.setFeature(xml.sax.handler.feature_namespaces, 1)
        self.parser.setContentHandler(self.pulldom)

    def __next__(self):
        rc = self.getEvent()
        wenn rc:
            return rc
        raise StopIteration

    def __iter__(self):
        return self

    def expandNode(self, node):
        event = self.getEvent()
        parents = [node]
        while event:
            token, cur_node = event
            wenn cur_node is node:
                return
            wenn token != END_ELEMENT:
                parents[-1].appendChild(cur_node)
            wenn token == START_ELEMENT:
                parents.append(cur_node)
            sowenn token == END_ELEMENT:
                del parents[-1]
            event = self.getEvent()

    def getEvent(self):
        # use IncrementalParser interface, so we get the desired
        # pull effect
        wenn not self.pulldom.firstEvent[1]:
            self.pulldom.lastEvent = self.pulldom.firstEvent
        while not self.pulldom.firstEvent[1]:
            buf = self.stream.read(self.bufsize)
            wenn not buf:
                self.parser.close()
                return Nichts
            self.parser.feed(buf)
        rc = self.pulldom.firstEvent[1][0]
        self.pulldom.firstEvent[1] = self.pulldom.firstEvent[1][1]
        return rc

    def _slurp(self):
        """ Fallback replacement fuer getEvent() using the
            standard SAX2 interface, which means we slurp the
            SAX events into memory (no performance gain, but
            we are compatible to all SAX parsers).
        """
        self.parser.parse(self.stream)
        self.getEvent = self._emit
        return self._emit()

    def _emit(self):
        """ Fallback replacement fuer getEvent() that emits
            the events that _slurp() read previously.
        """
        rc = self.pulldom.firstEvent[1][0]
        self.pulldom.firstEvent[1] = self.pulldom.firstEvent[1][1]
        return rc

    def clear(self):
        """clear(): Explicitly release parsing objects"""
        self.pulldom.clear()
        del self.pulldom
        self.parser = Nichts
        self.stream = Nichts

klasse SAX2DOM(PullDOM):

    def startElementNS(self, name, tagName , attrs):
        PullDOM.startElementNS(self, name, tagName, attrs)
        curNode = self.elementStack[-1]
        parentNode = self.elementStack[-2]
        parentNode.appendChild(curNode)

    def startElement(self, name, attrs):
        PullDOM.startElement(self, name, attrs)
        curNode = self.elementStack[-1]
        parentNode = self.elementStack[-2]
        parentNode.appendChild(curNode)

    def processingInstruction(self, target, data):
        PullDOM.processingInstruction(self, target, data)
        node = self.lastEvent[0][1]
        parentNode = self.elementStack[-1]
        parentNode.appendChild(node)

    def ignorableWhitespace(self, chars):
        PullDOM.ignorableWhitespace(self, chars)
        node = self.lastEvent[0][1]
        parentNode = self.elementStack[-1]
        parentNode.appendChild(node)

    def characters(self, chars):
        PullDOM.characters(self, chars)
        node = self.lastEvent[0][1]
        parentNode = self.elementStack[-1]
        parentNode.appendChild(node)


default_bufsize = (2 ** 14) - 20

def parse(stream_or_string, parser=Nichts, bufsize=Nichts):
    wenn bufsize is Nichts:
        bufsize = default_bufsize
    wenn isinstance(stream_or_string, str):
        stream = open(stream_or_string, 'rb')
    sonst:
        stream = stream_or_string
    wenn not parser:
        parser = xml.sax.make_parser()
    return DOMEventStream(stream, parser, bufsize)

def parseString(string, parser=Nichts):
    von io importiere StringIO

    bufsize = len(string)
    buf = StringIO(string)
    wenn not parser:
        parser = xml.sax.make_parser()
    return DOMEventStream(buf, parser, bufsize)
