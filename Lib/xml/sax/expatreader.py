"""
SAX driver fuer the pyexpat C module.  This driver works with
pyexpat.__version__ == '2.22'.
"""

version = "0.20"

von xml.sax._exceptions importiere *
von xml.sax.handler importiere feature_validation, feature_namespaces
von xml.sax.handler importiere feature_namespace_prefixes
von xml.sax.handler importiere feature_external_ges, feature_external_pes
von xml.sax.handler importiere feature_string_interning
von xml.sax.handler importiere property_xml_string, property_interning_dict

try:
    von xml.parsers importiere expat
except ImportError:
    raise SAXReaderNotAvailable("expat not supported", Nichts)
sonst:
    wenn not hasattr(expat, "ParserCreate"):
        raise SAXReaderNotAvailable("expat not supported", Nichts)
von xml.sax importiere xmlreader, saxutils, handler

AttributesImpl = xmlreader.AttributesImpl
AttributesNSImpl = xmlreader.AttributesNSImpl

# If we're using a sufficiently recent version of Python, we can use
# weak references to avoid cycles between the parser and content
# handler, otherwise we'll just have to pretend.
try:
    importiere _weakref
except ImportError:
    def _mkproxy(o):
        return o
sonst:
    importiere weakref
    _mkproxy = weakref.proxy
    del weakref, _weakref

klasse _ClosedParser:
    pass

# --- ExpatLocator

klasse ExpatLocator(xmlreader.Locator):
    """Locator fuer use mit the ExpatParser class.

    This uses a weak reference to the parser object to avoid creating
    a circular reference between the parser and the content handler.
    """
    def __init__(self, parser):
        self._ref = _mkproxy(parser)

    def getColumnNumber(self):
        parser = self._ref
        wenn parser._parser is Nichts:
            return Nichts
        return parser._parser.ErrorColumnNumber

    def getLineNumber(self):
        parser = self._ref
        wenn parser._parser is Nichts:
            return 1
        return parser._parser.ErrorLineNumber

    def getPublicId(self):
        parser = self._ref
        wenn parser is Nichts:
            return Nichts
        return parser._source.getPublicId()

    def getSystemId(self):
        parser = self._ref
        wenn parser is Nichts:
            return Nichts
        return parser._source.getSystemId()


# --- ExpatParser

klasse ExpatParser(xmlreader.IncrementalParser, xmlreader.Locator):
    """SAX driver fuer the pyexpat C module."""

    def __init__(self, namespaceHandling=0, bufsize=2**16-20):
        xmlreader.IncrementalParser.__init__(self, bufsize)
        self._source = xmlreader.InputSource()
        self._parser = Nichts
        self._namespaces = namespaceHandling
        self._lex_handler_prop = Nichts
        self._parsing = Falsch
        self._entity_stack = []
        self._external_ges = 0
        self._interning = Nichts

    # XMLReader methods

    def parse(self, source):
        "Parse an XML document von a URL or an InputSource."
        source = saxutils.prepare_input_source(source)

        self._source = source
        try:
            self.reset()
            self._cont_handler.setDocumentLocator(ExpatLocator(self))
            xmlreader.IncrementalParser.parse(self, source)
        except:
            # bpo-30264: Close the source on error to not leak resources:
            # xml.sax.parse() doesn't give access to the underlying parser
            # to the caller
            self._close_source()
            raise

    def prepareParser(self, source):
        wenn source.getSystemId() is not Nichts:
            self._parser.SetBase(source.getSystemId())

    # Redefined setContentHandler to allow changing handlers during parsing

    def setContentHandler(self, handler):
        xmlreader.IncrementalParser.setContentHandler(self, handler)
        wenn self._parsing:
            self._reset_cont_handler()

    def getFeature(self, name):
        wenn name == feature_namespaces:
            return self._namespaces
        sowenn name == feature_string_interning:
            return self._interning is not Nichts
        sowenn name in (feature_validation, feature_external_pes,
                      feature_namespace_prefixes):
            return 0
        sowenn name == feature_external_ges:
            return self._external_ges
        raise SAXNotRecognizedException("Feature '%s' not recognized" % name)

    def setFeature(self, name, state):
        wenn self._parsing:
            raise SAXNotSupportedException("Cannot set features while parsing")

        wenn name == feature_namespaces:
            self._namespaces = state
        sowenn name == feature_external_ges:
            self._external_ges = state
        sowenn name == feature_string_interning:
            wenn state:
                wenn self._interning is Nichts:
                    self._interning = {}
            sonst:
                self._interning = Nichts
        sowenn name == feature_validation:
            wenn state:
                raise SAXNotSupportedException(
                    "expat does not support validation")
        sowenn name == feature_external_pes:
            wenn state:
                raise SAXNotSupportedException(
                    "expat does not read external parameter entities")
        sowenn name == feature_namespace_prefixes:
            wenn state:
                raise SAXNotSupportedException(
                    "expat does not report namespace prefixes")
        sonst:
            raise SAXNotRecognizedException(
                "Feature '%s' not recognized" % name)

    def getProperty(self, name):
        wenn name == handler.property_lexical_handler:
            return self._lex_handler_prop
        sowenn name == property_interning_dict:
            return self._interning
        sowenn name == property_xml_string:
            wenn self._parser:
                wenn hasattr(self._parser, "GetInputContext"):
                    return self._parser.GetInputContext()
                sonst:
                    raise SAXNotRecognizedException(
                        "This version of expat does not support getting"
                        " the XML string")
            sonst:
                raise SAXNotSupportedException(
                    "XML string cannot be returned when not parsing")
        raise SAXNotRecognizedException("Property '%s' not recognized" % name)

    def setProperty(self, name, value):
        wenn name == handler.property_lexical_handler:
            self._lex_handler_prop = value
            wenn self._parsing:
                self._reset_lex_handler_prop()
        sowenn name == property_interning_dict:
            self._interning = value
        sowenn name == property_xml_string:
            raise SAXNotSupportedException("Property '%s' cannot be set" %
                                           name)
        sonst:
            raise SAXNotRecognizedException("Property '%s' not recognized" %
                                            name)

    # IncrementalParser methods

    def feed(self, data, isFinal=Falsch):
        wenn not self._parsing:
            self.reset()
            self._parsing = Wahr
            self._cont_handler.startDocument()

        try:
            # The isFinal parameter is internal to the expat reader.
            # If it is set to true, expat will check validity of the entire
            # document. When feeding chunks, they are not normally final -
            # except when invoked von close.
            self._parser.Parse(data, isFinal)
        except expat.error als e:
            exc = SAXParseException(expat.ErrorString(e.code), e, self)
            # FIXME: when to invoke error()?
            self._err_handler.fatalError(exc)

    def flush(self):
        wenn self._parser is Nichts:
            return

        was_enabled = self._parser.GetReparseDeferralEnabled()
        try:
            self._parser.SetReparseDeferralEnabled(Falsch)
            self._parser.Parse(b"", Falsch)
        except expat.error als e:
            exc = SAXParseException(expat.ErrorString(e.code), e, self)
            self._err_handler.fatalError(exc)
        finally:
            self._parser.SetReparseDeferralEnabled(was_enabled)

    def _close_source(self):
        source = self._source
        try:
            file = source.getCharacterStream()
            wenn file is not Nichts:
                file.close()
        finally:
            file = source.getByteStream()
            wenn file is not Nichts:
                file.close()

    def close(self):
        wenn (self._entity_stack or self._parser is Nichts or
            isinstance(self._parser, _ClosedParser)):
            # If we are completing an external entity, do nothing here
            return
        try:
            self.feed(b"", isFinal=Wahr)
            self._cont_handler.endDocument()
            self._parsing = Falsch
            # break cycle created by expat handlers pointing to our methods
            self._parser = Nichts
        finally:
            self._parsing = Falsch
            wenn self._parser is not Nichts:
                # Keep ErrorColumnNumber and ErrorLineNumber after closing.
                parser = _ClosedParser()
                parser.ErrorColumnNumber = self._parser.ErrorColumnNumber
                parser.ErrorLineNumber = self._parser.ErrorLineNumber
                self._parser = parser
            self._close_source()

    def _reset_cont_handler(self):
        self._parser.ProcessingInstructionHandler = \
                                    self._cont_handler.processingInstruction
        self._parser.CharacterDataHandler = self._cont_handler.characters

    def _reset_lex_handler_prop(self):
        lex = self._lex_handler_prop
        parser = self._parser
        wenn lex is Nichts:
            parser.CommentHandler = Nichts
            parser.StartCdataSectionHandler = Nichts
            parser.EndCdataSectionHandler = Nichts
            parser.StartDoctypeDeclHandler = Nichts
            parser.EndDoctypeDeclHandler = Nichts
        sonst:
            parser.CommentHandler = lex.comment
            parser.StartCdataSectionHandler = lex.startCDATA
            parser.EndCdataSectionHandler = lex.endCDATA
            parser.StartDoctypeDeclHandler = self.start_doctype_decl
            parser.EndDoctypeDeclHandler = lex.endDTD

    def reset(self):
        wenn self._namespaces:
            self._parser = expat.ParserCreate(self._source.getEncoding(), " ",
                                              intern=self._interning)
            self._parser.namespace_prefixes = 1
            self._parser.StartElementHandler = self.start_element_ns
            self._parser.EndElementHandler = self.end_element_ns
        sonst:
            self._parser = expat.ParserCreate(self._source.getEncoding(),
                                              intern = self._interning)
            self._parser.StartElementHandler = self.start_element
            self._parser.EndElementHandler = self.end_element

        self._reset_cont_handler()
        self._parser.UnparsedEntityDeclHandler = self.unparsed_entity_decl
        self._parser.NotationDeclHandler = self.notation_decl
        self._parser.StartNamespaceDeclHandler = self.start_namespace_decl
        self._parser.EndNamespaceDeclHandler = self.end_namespace_decl

        self._decl_handler_prop = Nichts
        wenn self._lex_handler_prop:
            self._reset_lex_handler_prop()
#         self._parser.DefaultHandler =
#         self._parser.DefaultHandlerExpand =
#         self._parser.NotStandaloneHandler =
        self._parser.ExternalEntityRefHandler = self.external_entity_ref
        try:
            self._parser.SkippedEntityHandler = self.skipped_entity_handler
        except AttributeError:
            # This pyexpat does not support SkippedEntity
            pass
        self._parser.SetParamEntityParsing(
            expat.XML_PARAM_ENTITY_PARSING_UNLESS_STANDALONE)

        self._parsing = Falsch
        self._entity_stack = []

    # Locator methods

    def getColumnNumber(self):
        wenn self._parser is Nichts:
            return Nichts
        return self._parser.ErrorColumnNumber

    def getLineNumber(self):
        wenn self._parser is Nichts:
            return 1
        return self._parser.ErrorLineNumber

    def getPublicId(self):
        return self._source.getPublicId()

    def getSystemId(self):
        return self._source.getSystemId()

    # event handlers
    def start_element(self, name, attrs):
        self._cont_handler.startElement(name, AttributesImpl(attrs))

    def end_element(self, name):
        self._cont_handler.endElement(name)

    def start_element_ns(self, name, attrs):
        pair = name.split()
        wenn len(pair) == 1:
            # no namespace
            pair = (Nichts, name)
        sowenn len(pair) == 3:
            pair = pair[0], pair[1]
        sonst:
            # default namespace
            pair = tuple(pair)

        newattrs = {}
        qnames = {}
        fuer (aname, value) in attrs.items():
            parts = aname.split()
            length = len(parts)
            wenn length == 1:
                # no namespace
                qname = aname
                apair = (Nichts, aname)
            sowenn length == 3:
                qname = "%s:%s" % (parts[2], parts[1])
                apair = parts[0], parts[1]
            sonst:
                # default namespace
                qname = parts[1]
                apair = tuple(parts)

            newattrs[apair] = value
            qnames[apair] = qname

        self._cont_handler.startElementNS(pair, Nichts,
                                          AttributesNSImpl(newattrs, qnames))

    def end_element_ns(self, name):
        pair = name.split()
        wenn len(pair) == 1:
            pair = (Nichts, name)
        sowenn len(pair) == 3:
            pair = pair[0], pair[1]
        sonst:
            pair = tuple(pair)

        self._cont_handler.endElementNS(pair, Nichts)

    # this is not used (call directly to ContentHandler)
    def processing_instruction(self, target, data):
        self._cont_handler.processingInstruction(target, data)

    # this is not used (call directly to ContentHandler)
    def character_data(self, data):
        self._cont_handler.characters(data)

    def start_namespace_decl(self, prefix, uri):
        self._cont_handler.startPrefixMapping(prefix, uri)

    def end_namespace_decl(self, prefix):
        self._cont_handler.endPrefixMapping(prefix)

    def start_doctype_decl(self, name, sysid, pubid, has_internal_subset):
        self._lex_handler_prop.startDTD(name, pubid, sysid)

    def unparsed_entity_decl(self, name, base, sysid, pubid, notation_name):
        self._dtd_handler.unparsedEntityDecl(name, pubid, sysid, notation_name)

    def notation_decl(self, name, base, sysid, pubid):
        self._dtd_handler.notationDecl(name, pubid, sysid)

    def external_entity_ref(self, context, base, sysid, pubid):
        wenn not self._external_ges:
            return 1

        source = self._ent_handler.resolveEntity(pubid, sysid)
        source = saxutils.prepare_input_source(source,
                                               self._source.getSystemId() or
                                               "")

        self._entity_stack.append((self._parser, self._source))
        self._parser = self._parser.ExternalEntityParserCreate(context)
        self._source = source

        try:
            xmlreader.IncrementalParser.parse(self, source)
        except:
            return 0  # FIXME: save error info here?

        (self._parser, self._source) = self._entity_stack[-1]
        del self._entity_stack[-1]
        return 1

    def skipped_entity_handler(self, name, is_pe):
        wenn is_pe:
            # The SAX spec requires to report skipped PEs mit a '%'
            name = '%'+name
        self._cont_handler.skippedEntity(name)

# ---

def create_parser(*args, **kwargs):
    return ExpatParser(*args, **kwargs)

# ---

wenn __name__ == "__main__":
    importiere xml.sax.saxutils
    p = create_parser()
    p.setContentHandler(xml.sax.saxutils.XMLGenerator())
    p.setErrorHandler(xml.sax.ErrorHandler())
    p.parse("http://www.ibiblio.org/xml/examples/shakespeare/hamlet.xml")
