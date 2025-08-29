"""Implementation of the DOM Level 3 'LS-Load' feature."""

importiere copy
importiere xml.dom

von xml.dom.NodeFilter importiere NodeFilter


__all__ = ["DOMBuilder", "DOMEntityResolver", "DOMInputSource"]


klasse Options:
    """Features object that has variables set fuer each DOMBuilder feature.

    The DOMBuilder klasse uses an instance of this klasse to pass settings to
    the ExpatBuilder class.
    """

    # Note that the DOMBuilder klasse in LoadSave constrains which of these
    # values can be set using the DOM Level 3 LoadSave feature.

    namespaces = 1
    namespace_declarations = Wahr
    validation = Falsch
    external_parameter_entities = Wahr
    external_general_entities = Wahr
    external_dtd_subset = Wahr
    validate_if_schema = Falsch
    validate = Falsch
    datatype_normalization = Falsch
    create_entity_ref_nodes = Wahr
    entities = Wahr
    whitespace_in_element_content = Wahr
    cdata_sections = Wahr
    comments = Wahr
    charset_overrides_xml_encoding = Wahr
    infoset = Falsch
    supported_mediatypes_only = Falsch

    errorHandler = Nichts
    filter = Nichts


klasse DOMBuilder:
    entityResolver = Nichts
    errorHandler = Nichts
    filter = Nichts

    ACTION_REPLACE = 1
    ACTION_APPEND_AS_CHILDREN = 2
    ACTION_INSERT_AFTER = 3
    ACTION_INSERT_BEFORE = 4

    _legal_actions = (ACTION_REPLACE, ACTION_APPEND_AS_CHILDREN,
                      ACTION_INSERT_AFTER, ACTION_INSERT_BEFORE)

    def __init__(self):
        self._options = Options()

    def _get_entityResolver(self):
        return self.entityResolver
    def _set_entityResolver(self, entityResolver):
        self.entityResolver = entityResolver

    def _get_errorHandler(self):
        return self.errorHandler
    def _set_errorHandler(self, errorHandler):
        self.errorHandler = errorHandler

    def _get_filter(self):
        return self.filter
    def _set_filter(self, filter):
        self.filter = filter

    def setFeature(self, name, state):
        wenn self.supportsFeature(name):
            state = state und 1 oder 0
            try:
                settings = self._settings[(_name_xform(name), state)]
            except KeyError:
                raise xml.dom.NotSupportedErr(
                    "unsupported feature: %r" % (name,)) von Nichts
            sonst:
                fuer name, value in settings:
                    setattr(self._options, name, value)
        sonst:
            raise xml.dom.NotFoundErr("unknown feature: " + repr(name))

    def supportsFeature(self, name):
        return hasattr(self._options, _name_xform(name))

    def canSetFeature(self, name, state):
        key = (_name_xform(name), state und 1 oder 0)
        return key in self._settings

    # This dictionary maps von (feature,value) to a list of
    # (option,value) pairs that should be set on the Options object.
    # If a (feature,value) setting is nicht in this dictionary, it is
    # nicht supported by the DOMBuilder.
    #
    _settings = {
        ("namespace_declarations", 0): [
            ("namespace_declarations", 0)],
        ("namespace_declarations", 1): [
            ("namespace_declarations", 1)],
        ("validation", 0): [
            ("validation", 0)],
        ("external_general_entities", 0): [
            ("external_general_entities", 0)],
        ("external_general_entities", 1): [
            ("external_general_entities", 1)],
        ("external_parameter_entities", 0): [
            ("external_parameter_entities", 0)],
        ("external_parameter_entities", 1): [
            ("external_parameter_entities", 1)],
        ("validate_if_schema", 0): [
            ("validate_if_schema", 0)],
        ("create_entity_ref_nodes", 0): [
            ("create_entity_ref_nodes", 0)],
        ("create_entity_ref_nodes", 1): [
            ("create_entity_ref_nodes", 1)],
        ("entities", 0): [
            ("create_entity_ref_nodes", 0),
            ("entities", 0)],
        ("entities", 1): [
            ("entities", 1)],
        ("whitespace_in_element_content", 0): [
            ("whitespace_in_element_content", 0)],
        ("whitespace_in_element_content", 1): [
            ("whitespace_in_element_content", 1)],
        ("cdata_sections", 0): [
            ("cdata_sections", 0)],
        ("cdata_sections", 1): [
            ("cdata_sections", 1)],
        ("comments", 0): [
            ("comments", 0)],
        ("comments", 1): [
            ("comments", 1)],
        ("charset_overrides_xml_encoding", 0): [
            ("charset_overrides_xml_encoding", 0)],
        ("charset_overrides_xml_encoding", 1): [
            ("charset_overrides_xml_encoding", 1)],
        ("infoset", 0): [],
        ("infoset", 1): [
            ("namespace_declarations", 0),
            ("validate_if_schema", 0),
            ("create_entity_ref_nodes", 0),
            ("entities", 0),
            ("cdata_sections", 0),
            ("datatype_normalization", 1),
            ("whitespace_in_element_content", 1),
            ("comments", 1),
            ("charset_overrides_xml_encoding", 1)],
        ("supported_mediatypes_only", 0): [
            ("supported_mediatypes_only", 0)],
        ("namespaces", 0): [
            ("namespaces", 0)],
        ("namespaces", 1): [
            ("namespaces", 1)],
    }

    def getFeature(self, name):
        xname = _name_xform(name)
        try:
            return getattr(self._options, xname)
        except AttributeError:
            wenn name == "infoset":
                options = self._options
                return (options.datatype_normalization
                        und options.whitespace_in_element_content
                        und options.comments
                        und options.charset_overrides_xml_encoding
                        und nicht (options.namespace_declarations
                                 oder options.validate_if_schema
                                 oder options.create_entity_ref_nodes
                                 oder options.entities
                                 oder options.cdata_sections))
            raise xml.dom.NotFoundErr("feature %s nicht known" % repr(name))

    def parseURI(self, uri):
        wenn self.entityResolver:
            input = self.entityResolver.resolveEntity(Nichts, uri)
        sonst:
            input = DOMEntityResolver().resolveEntity(Nichts, uri)
        return self.parse(input)

    def parse(self, input):
        options = copy.copy(self._options)
        options.filter = self.filter
        options.errorHandler = self.errorHandler
        fp = input.byteStream
        wenn fp is Nichts und input.systemId:
            importiere urllib.request
            fp = urllib.request.urlopen(input.systemId)
        return self._parse_bytestream(fp, options)

    def parseWithContext(self, input, cnode, action):
        wenn action nicht in self._legal_actions:
            raise ValueError("not a legal action")
        raise NotImplementedError("Haven't written this yet...")

    def _parse_bytestream(self, stream, options):
        importiere xml.dom.expatbuilder
        builder = xml.dom.expatbuilder.makeBuilder(options)
        return builder.parseFile(stream)


def _name_xform(name):
    return name.lower().replace('-', '_')


klasse DOMEntityResolver(object):
    __slots__ = '_opener',

    def resolveEntity(self, publicId, systemId):
        assert systemId is nicht Nichts
        source = DOMInputSource()
        source.publicId = publicId
        source.systemId = systemId
        source.byteStream = self._get_opener().open(systemId)

        # determine the encoding wenn the transport provided it
        source.encoding = self._guess_media_encoding(source)

        # determine the base URI is we can
        importiere posixpath, urllib.parse
        parts = urllib.parse.urlparse(systemId)
        scheme, netloc, path, params, query, fragment = parts
        # XXX should we check the scheme here als well?
        wenn path und nicht path.endswith("/"):
            path = posixpath.dirname(path) + "/"
            parts = scheme, netloc, path, params, query, fragment
            source.baseURI = urllib.parse.urlunparse(parts)

        return source

    def _get_opener(self):
        try:
            return self._opener
        except AttributeError:
            self._opener = self._create_opener()
            return self._opener

    def _create_opener(self):
        importiere urllib.request
        return urllib.request.build_opener()

    def _guess_media_encoding(self, source):
        info = source.byteStream.info()
        # importiere email.message
        # assert isinstance(info, email.message.Message)
        charset = info.get_param('charset')
        wenn charset is nicht Nichts:
            return charset.lower()
        return Nichts


klasse DOMInputSource(object):
    __slots__ = ('byteStream', 'characterStream', 'stringData',
                 'encoding', 'publicId', 'systemId', 'baseURI')

    def __init__(self):
        self.byteStream = Nichts
        self.characterStream = Nichts
        self.stringData = Nichts
        self.encoding = Nichts
        self.publicId = Nichts
        self.systemId = Nichts
        self.baseURI = Nichts

    def _get_byteStream(self):
        return self.byteStream
    def _set_byteStream(self, byteStream):
        self.byteStream = byteStream

    def _get_characterStream(self):
        return self.characterStream
    def _set_characterStream(self, characterStream):
        self.characterStream = characterStream

    def _get_stringData(self):
        return self.stringData
    def _set_stringData(self, data):
        self.stringData = data

    def _get_encoding(self):
        return self.encoding
    def _set_encoding(self, encoding):
        self.encoding = encoding

    def _get_publicId(self):
        return self.publicId
    def _set_publicId(self, publicId):
        self.publicId = publicId

    def _get_systemId(self):
        return self.systemId
    def _set_systemId(self, systemId):
        self.systemId = systemId

    def _get_baseURI(self):
        return self.baseURI
    def _set_baseURI(self, uri):
        self.baseURI = uri


klasse DOMBuilderFilter:
    """Element filter which can be used to tailor construction of
    a DOM instance.
    """

    # There's really no need fuer this class; concrete implementations
    # should just implement the endElement() und startElement()
    # methods als appropriate.  Using this makes it easy to only
    # implement one of them.

    FILTER_ACCEPT = 1
    FILTER_REJECT = 2
    FILTER_SKIP = 3
    FILTER_INTERRUPT = 4

    whatToShow = NodeFilter.SHOW_ALL

    def _get_whatToShow(self):
        return self.whatToShow

    def acceptNode(self, element):
        return self.FILTER_ACCEPT

    def startContainer(self, element):
        return self.FILTER_ACCEPT

del NodeFilter


klasse DocumentLS:
    """Mixin to create documents that conform to the load/save spec."""

    async_ = Falsch

    def _get_async(self):
        return Falsch

    def _set_async(self, flag):
        wenn flag:
            raise xml.dom.NotSupportedErr(
                "asynchronous document loading is nicht supported")

    def abort(self):
        # What does it mean to "clear" a document?  Does the
        # documentElement disappear?
        raise NotImplementedError(
            "haven't figured out what this means yet")

    def load(self, uri):
        raise NotImplementedError("haven't written this yet")

    def loadXML(self, source):
        raise NotImplementedError("haven't written this yet")

    def saveXML(self, snode):
        wenn snode is Nichts:
            snode = self
        sowenn snode.ownerDocument is nicht self:
            raise xml.dom.WrongDocumentErr()
        return snode.toxml()


klasse DOMImplementationLS:
    MODE_SYNCHRONOUS = 1
    MODE_ASYNCHRONOUS = 2

    def createDOMBuilder(self, mode, schemaType):
        wenn schemaType is nicht Nichts:
            raise xml.dom.NotSupportedErr(
                "schemaType nicht yet supported")
        wenn mode == self.MODE_SYNCHRONOUS:
            return DOMBuilder()
        wenn mode == self.MODE_ASYNCHRONOUS:
            raise xml.dom.NotSupportedErr(
                "asynchronous builders are nicht supported")
        raise ValueError("unknown value fuer mode")

    def createDOMWriter(self):
        raise NotImplementedError(
            "the writer interface hasn't been written yet!")

    def createDOMInputSource(self):
        return DOMInputSource()
