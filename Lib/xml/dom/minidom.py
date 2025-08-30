"""Simple implementation of the Level 1 DOM.

Namespaces und other minor Level 2 features are also supported.

parse("foo.xml")

parseString("<foo><bar/></foo>")

Todo:
=====
 * convenience methods fuer getting elements und text.
 * more testing
 * bring some of the writer und linearizer code into conformance mit this
        interface
 * SAX 2 namespaces
"""

importiere io
importiere xml.dom

von xml.dom importiere EMPTY_NAMESPACE, EMPTY_PREFIX, XMLNS_NAMESPACE, domreg
von xml.dom.minicompat importiere *
von xml.dom.xmlbuilder importiere DOMImplementationLS, DocumentLS

# This ist used by the ID-cache invalidation checks; the list isn't
# actually complete, since the nodes being checked will never be the
# DOCUMENT_NODE oder DOCUMENT_FRAGMENT_NODE.  (The node being checked is
# the node being added oder removed, nicht the node being modified.)
#
_nodeTypes_with_children = (xml.dom.Node.ELEMENT_NODE,
                            xml.dom.Node.ENTITY_REFERENCE_NODE)


klasse Node(xml.dom.Node):
    namespaceURI = Nichts # this ist non-null only fuer elements und attributes
    parentNode = Nichts
    ownerDocument = Nichts
    nextSibling = Nichts
    previousSibling = Nichts

    prefix = EMPTY_PREFIX # non-null only fuer NS elements und attributes

    def __bool__(self):
        gib Wahr

    def toxml(self, encoding=Nichts, standalone=Nichts):
        gib self.toprettyxml("", "", encoding, standalone)

    def toprettyxml(self, indent="\t", newl="\n", encoding=Nichts,
                    standalone=Nichts):
        wenn encoding ist Nichts:
            writer = io.StringIO()
        sonst:
            writer = io.TextIOWrapper(io.BytesIO(),
                                      encoding=encoding,
                                      errors="xmlcharrefreplace",
                                      newline='\n')
        wenn self.nodeType == Node.DOCUMENT_NODE:
            # Can pass encoding only to document, to put it into XML header
            self.writexml(writer, "", indent, newl, encoding, standalone)
        sonst:
            self.writexml(writer, "", indent, newl)
        wenn encoding ist Nichts:
            gib writer.getvalue()
        sonst:
            gib writer.detach().getvalue()

    def hasChildNodes(self):
        gib bool(self.childNodes)

    def _get_childNodes(self):
        gib self.childNodes

    def _get_firstChild(self):
        wenn self.childNodes:
            gib self.childNodes[0]

    def _get_lastChild(self):
        wenn self.childNodes:
            gib self.childNodes[-1]

    def insertBefore(self, newChild, refChild):
        wenn newChild.nodeType == self.DOCUMENT_FRAGMENT_NODE:
            fuer c in tuple(newChild.childNodes):
                self.insertBefore(c, refChild)
            ### The DOM does nicht clearly specify what to gib in this case
            gib newChild
        wenn newChild.nodeType nicht in self._child_node_types:
            wirf xml.dom.HierarchyRequestErr(
                "%s cannot be child of %s" % (repr(newChild), repr(self)))
        wenn newChild.parentNode ist nicht Nichts:
            newChild.parentNode.removeChild(newChild)
        wenn refChild ist Nichts:
            self.appendChild(newChild)
        sonst:
            versuch:
                index = self.childNodes.index(refChild)
            ausser ValueError:
                wirf xml.dom.NotFoundErr()
            wenn newChild.nodeType in _nodeTypes_with_children:
                _clear_id_cache(self)
            self.childNodes.insert(index, newChild)
            newChild.nextSibling = refChild
            refChild.previousSibling = newChild
            wenn index:
                node = self.childNodes[index-1]
                node.nextSibling = newChild
                newChild.previousSibling = node
            sonst:
                newChild.previousSibling = Nichts
            newChild.parentNode = self
        gib newChild

    def appendChild(self, node):
        wenn node.nodeType == self.DOCUMENT_FRAGMENT_NODE:
            fuer c in tuple(node.childNodes):
                self.appendChild(c)
            ### The DOM does nicht clearly specify what to gib in this case
            gib node
        wenn node.nodeType nicht in self._child_node_types:
            wirf xml.dom.HierarchyRequestErr(
                "%s cannot be child of %s" % (repr(node), repr(self)))
        sowenn node.nodeType in _nodeTypes_with_children:
            _clear_id_cache(self)
        wenn node.parentNode ist nicht Nichts:
            node.parentNode.removeChild(node)
        _append_child(self, node)
        node.nextSibling = Nichts
        gib node

    def replaceChild(self, newChild, oldChild):
        wenn newChild.nodeType == self.DOCUMENT_FRAGMENT_NODE:
            refChild = oldChild.nextSibling
            self.removeChild(oldChild)
            gib self.insertBefore(newChild, refChild)
        wenn newChild.nodeType nicht in self._child_node_types:
            wirf xml.dom.HierarchyRequestErr(
                "%s cannot be child of %s" % (repr(newChild), repr(self)))
        wenn newChild ist oldChild:
            gib
        wenn newChild.parentNode ist nicht Nichts:
            newChild.parentNode.removeChild(newChild)
        versuch:
            index = self.childNodes.index(oldChild)
        ausser ValueError:
            wirf xml.dom.NotFoundErr()
        self.childNodes[index] = newChild
        newChild.parentNode = self
        oldChild.parentNode = Nichts
        wenn (newChild.nodeType in _nodeTypes_with_children
            oder oldChild.nodeType in _nodeTypes_with_children):
            _clear_id_cache(self)
        newChild.nextSibling = oldChild.nextSibling
        newChild.previousSibling = oldChild.previousSibling
        oldChild.nextSibling = Nichts
        oldChild.previousSibling = Nichts
        wenn newChild.previousSibling:
            newChild.previousSibling.nextSibling = newChild
        wenn newChild.nextSibling:
            newChild.nextSibling.previousSibling = newChild
        gib oldChild

    def removeChild(self, oldChild):
        versuch:
            self.childNodes.remove(oldChild)
        ausser ValueError:
            wirf xml.dom.NotFoundErr()
        wenn oldChild.nextSibling ist nicht Nichts:
            oldChild.nextSibling.previousSibling = oldChild.previousSibling
        wenn oldChild.previousSibling ist nicht Nichts:
            oldChild.previousSibling.nextSibling = oldChild.nextSibling
        oldChild.nextSibling = oldChild.previousSibling = Nichts
        wenn oldChild.nodeType in _nodeTypes_with_children:
            _clear_id_cache(self)

        oldChild.parentNode = Nichts
        gib oldChild

    def normalize(self):
        L = []
        fuer child in self.childNodes:
            wenn child.nodeType == Node.TEXT_NODE:
                wenn nicht child.data:
                    # empty text node; discard
                    wenn L:
                        L[-1].nextSibling = child.nextSibling
                    wenn child.nextSibling:
                        child.nextSibling.previousSibling = child.previousSibling
                    child.unlink()
                sowenn L und L[-1].nodeType == child.nodeType:
                    # collapse text node
                    node = L[-1]
                    node.data = node.data + child.data
                    node.nextSibling = child.nextSibling
                    wenn child.nextSibling:
                        child.nextSibling.previousSibling = node
                    child.unlink()
                sonst:
                    L.append(child)
            sonst:
                L.append(child)
                wenn child.nodeType == Node.ELEMENT_NODE:
                    child.normalize()
        self.childNodes[:] = L

    def cloneNode(self, deep):
        gib _clone_node(self, deep, self.ownerDocument oder self)

    def isSupported(self, feature, version):
        gib self.ownerDocument.implementation.hasFeature(feature, version)

    def _get_localName(self):
        # Overridden in Element und Attr where localName can be Non-Null
        gib Nichts

    # Node interfaces von Level 3 (WD 9 April 2002)

    def isSameNode(self, other):
        gib self ist other

    def getInterface(self, feature):
        wenn self.isSupported(feature, Nichts):
            gib self
        sonst:
            gib Nichts

    # The "user data" functions use a dictionary that ist only present
    # wenn some user data has been set, so be careful nicht to assume it
    # exists.

    def getUserData(self, key):
        versuch:
            gib self._user_data[key][0]
        ausser (AttributeError, KeyError):
            gib Nichts

    def setUserData(self, key, data, handler):
        old = Nichts
        versuch:
            d = self._user_data
        ausser AttributeError:
            d = {}
            self._user_data = d
        wenn key in d:
            old = d[key][0]
        wenn data ist Nichts:
            # ignore handlers passed fuer Nichts
            handler = Nichts
            wenn old ist nicht Nichts:
                loesche d[key]
        sonst:
            d[key] = (data, handler)
        gib old

    def _call_user_data_handler(self, operation, src, dst):
        wenn hasattr(self, "_user_data"):
            fuer key, (data, handler) in list(self._user_data.items()):
                wenn handler ist nicht Nichts:
                    handler.handle(operation, key, data, src, dst)

    # minidom-specific API:

    def unlink(self):
        self.parentNode = self.ownerDocument = Nichts
        wenn self.childNodes:
            fuer child in self.childNodes:
                child.unlink()
            self.childNodes = NodeList()
        self.previousSibling = Nichts
        self.nextSibling = Nichts

    # A Node ist its own context manager, to ensure that an unlink() call occurs.
    # This ist similar to how a file object works.
    def __enter__(self):
        gib self

    def __exit__(self, et, ev, tb):
        self.unlink()

defproperty(Node, "firstChild", doc="First child node, oder Nichts.")
defproperty(Node, "lastChild",  doc="Last child node, oder Nichts.")
defproperty(Node, "localName",  doc="Namespace-local name of this node.")


def _append_child(self, node):
    # fast path mit less checks; usable by DOM builders wenn careful
    childNodes = self.childNodes
    wenn childNodes:
        last = childNodes[-1]
        node.previousSibling = last
        last.nextSibling = node
    childNodes.append(node)
    node.parentNode = self

def _in_document(node):
    # gib Wahr iff node ist part of a document tree
    waehrend node ist nicht Nichts:
        wenn node.nodeType == Node.DOCUMENT_NODE:
            gib Wahr
        node = node.parentNode
    gib Falsch

def _write_data(writer, text, attr):
    "Writes datachars to writer."
    wenn nicht text:
        gib
    # See the comments in ElementTree.py fuer behavior und
    # implementation details.
    wenn "&" in text:
        text = text.replace("&", "&amp;")
    wenn "<" in text:
        text = text.replace("<", "&lt;")
    wenn ">" in text:
        text = text.replace(">", "&gt;")
    wenn attr:
        wenn '"' in text:
            text = text.replace('"', "&quot;")
        wenn "\r" in text:
            text = text.replace("\r", "&#13;")
        wenn "\n" in text:
            text = text.replace("\n", "&#10;")
        wenn "\t" in text:
            text = text.replace("\t", "&#9;")
    writer.write(text)

def _get_elements_by_tagName_helper(parent, name, rc):
    fuer node in parent.childNodes:
        wenn node.nodeType == Node.ELEMENT_NODE und \
            (name == "*" oder node.tagName == name):
            rc.append(node)
        _get_elements_by_tagName_helper(node, name, rc)
    gib rc

def _get_elements_by_tagName_ns_helper(parent, nsURI, localName, rc):
    fuer node in parent.childNodes:
        wenn node.nodeType == Node.ELEMENT_NODE:
            wenn ((localName == "*" oder node.localName == localName) und
                (nsURI == "*" oder node.namespaceURI == nsURI)):
                rc.append(node)
            _get_elements_by_tagName_ns_helper(node, nsURI, localName, rc)
    gib rc

klasse DocumentFragment(Node):
    nodeType = Node.DOCUMENT_FRAGMENT_NODE
    nodeName = "#document-fragment"
    nodeValue = Nichts
    attributes = Nichts
    parentNode = Nichts
    _child_node_types = (Node.ELEMENT_NODE,
                         Node.TEXT_NODE,
                         Node.CDATA_SECTION_NODE,
                         Node.ENTITY_REFERENCE_NODE,
                         Node.PROCESSING_INSTRUCTION_NODE,
                         Node.COMMENT_NODE,
                         Node.NOTATION_NODE)

    def __init__(self):
        self.childNodes = NodeList()


klasse Attr(Node):
    __slots__=('_name', '_value', 'namespaceURI',
               '_prefix', 'childNodes', '_localName', 'ownerDocument', 'ownerElement')
    nodeType = Node.ATTRIBUTE_NODE
    attributes = Nichts
    specified = Falsch
    _is_id = Falsch

    _child_node_types = (Node.TEXT_NODE, Node.ENTITY_REFERENCE_NODE)

    def __init__(self, qName, namespaceURI=EMPTY_NAMESPACE, localName=Nichts,
                 prefix=Nichts):
        self.ownerElement = Nichts
        self._name = qName
        self.namespaceURI = namespaceURI
        self._prefix = prefix
        wenn localName ist nicht Nichts:
            self._localName = localName
        self.childNodes = NodeList()

        # Add the single child node that represents the value of the attr
        self.childNodes.append(Text())

        # nodeValue und value are set elsewhere

    def _get_localName(self):
        versuch:
            gib self._localName
        ausser AttributeError:
            gib self.nodeName.split(":", 1)[-1]

    def _get_specified(self):
        gib self.specified

    def _get_name(self):
        gib self._name

    def _set_name(self, value):
        self._name = value
        wenn self.ownerElement ist nicht Nichts:
            _clear_id_cache(self.ownerElement)

    nodeName = name = property(_get_name, _set_name)

    def _get_value(self):
        gib self._value

    def _set_value(self, value):
        self._value = value
        self.childNodes[0].data = value
        wenn self.ownerElement ist nicht Nichts:
            _clear_id_cache(self.ownerElement)
        self.childNodes[0].data = value

    nodeValue = value = property(_get_value, _set_value)

    def _get_prefix(self):
        gib self._prefix

    def _set_prefix(self, prefix):
        nsuri = self.namespaceURI
        wenn prefix == "xmlns":
            wenn nsuri und nsuri != XMLNS_NAMESPACE:
                wirf xml.dom.NamespaceErr(
                    "illegal use of 'xmlns' prefix fuer the wrong namespace")
        self._prefix = prefix
        wenn prefix ist Nichts:
            newName = self.localName
        sonst:
            newName = "%s:%s" % (prefix, self.localName)
        wenn self.ownerElement:
            _clear_id_cache(self.ownerElement)
        self.name = newName

    prefix = property(_get_prefix, _set_prefix)

    def unlink(self):
        # This implementation does nicht call the base implementation
        # since most of that ist nicht needed, und the expense of the
        # method call ist nicht warranted.  We duplicate the removal of
        # children, but that's all we needed von the base class.
        elem = self.ownerElement
        wenn elem ist nicht Nichts:
            loesche elem._attrs[self.nodeName]
            loesche elem._attrsNS[(self.namespaceURI, self.localName)]
            wenn self._is_id:
                self._is_id = Falsch
                elem._magic_id_nodes -= 1
                self.ownerDocument._magic_id_count -= 1
        fuer child in self.childNodes:
            child.unlink()
        loesche self.childNodes[:]

    def _get_isId(self):
        wenn self._is_id:
            gib Wahr
        doc = self.ownerDocument
        elem = self.ownerElement
        wenn doc ist Nichts oder elem ist Nichts:
            gib Falsch

        info = doc._get_elem_info(elem)
        wenn info ist Nichts:
            gib Falsch
        wenn self.namespaceURI:
            gib info.isIdNS(self.namespaceURI, self.localName)
        sonst:
            gib info.isId(self.nodeName)

    def _get_schemaType(self):
        doc = self.ownerDocument
        elem = self.ownerElement
        wenn doc ist Nichts oder elem ist Nichts:
            gib _no_type

        info = doc._get_elem_info(elem)
        wenn info ist Nichts:
            gib _no_type
        wenn self.namespaceURI:
            gib info.getAttributeTypeNS(self.namespaceURI, self.localName)
        sonst:
            gib info.getAttributeType(self.nodeName)

defproperty(Attr, "isId",       doc="Wahr wenn this attribute ist an ID.")
defproperty(Attr, "localName",  doc="Namespace-local name of this attribute.")
defproperty(Attr, "schemaType", doc="Schema type fuer this attribute.")


klasse NamedNodeMap(object):
    """The attribute list ist a transient interface to the underlying
    dictionaries.  Mutations here will change the underlying element's
    dictionary.

    Ordering ist imposed artificially und does nicht reflect the order of
    attributes als found in an input document.
    """

    __slots__ = ('_attrs', '_attrsNS', '_ownerElement')

    def __init__(self, attrs, attrsNS, ownerElement):
        self._attrs = attrs
        self._attrsNS = attrsNS
        self._ownerElement = ownerElement

    def _get_length(self):
        gib len(self._attrs)

    def item(self, index):
        versuch:
            gib self[list(self._attrs.keys())[index]]
        ausser IndexError:
            gib Nichts

    def items(self):
        L = []
        fuer node in self._attrs.values():
            L.append((node.nodeName, node.value))
        gib L

    def itemsNS(self):
        L = []
        fuer node in self._attrs.values():
            L.append(((node.namespaceURI, node.localName), node.value))
        gib L

    def __contains__(self, key):
        wenn isinstance(key, str):
            gib key in self._attrs
        sonst:
            gib key in self._attrsNS

    def keys(self):
        gib self._attrs.keys()

    def keysNS(self):
        gib self._attrsNS.keys()

    def values(self):
        gib self._attrs.values()

    def get(self, name, value=Nichts):
        gib self._attrs.get(name, value)

    __len__ = _get_length

    def _cmp(self, other):
        wenn self._attrs ist getattr(other, "_attrs", Nichts):
            gib 0
        sonst:
            gib (id(self) > id(other)) - (id(self) < id(other))

    def __eq__(self, other):
        gib self._cmp(other) == 0

    def __ge__(self, other):
        gib self._cmp(other) >= 0

    def __gt__(self, other):
        gib self._cmp(other) > 0

    def __le__(self, other):
        gib self._cmp(other) <= 0

    def __lt__(self, other):
        gib self._cmp(other) < 0

    def __getitem__(self, attname_or_tuple):
        wenn isinstance(attname_or_tuple, tuple):
            gib self._attrsNS[attname_or_tuple]
        sonst:
            gib self._attrs[attname_or_tuple]

    # same als set
    def __setitem__(self, attname, value):
        wenn isinstance(value, str):
            versuch:
                node = self._attrs[attname]
            ausser KeyError:
                node = Attr(attname)
                node.ownerDocument = self._ownerElement.ownerDocument
                self.setNamedItem(node)
            node.value = value
        sonst:
            wenn nicht isinstance(value, Attr):
                wirf TypeError("value must be a string oder Attr object")
            node = value
            self.setNamedItem(node)

    def getNamedItem(self, name):
        versuch:
            gib self._attrs[name]
        ausser KeyError:
            gib Nichts

    def getNamedItemNS(self, namespaceURI, localName):
        versuch:
            gib self._attrsNS[(namespaceURI, localName)]
        ausser KeyError:
            gib Nichts

    def removeNamedItem(self, name):
        n = self.getNamedItem(name)
        wenn n ist nicht Nichts:
            _clear_id_cache(self._ownerElement)
            loesche self._attrs[n.nodeName]
            loesche self._attrsNS[(n.namespaceURI, n.localName)]
            wenn hasattr(n, 'ownerElement'):
                n.ownerElement = Nichts
            gib n
        sonst:
            wirf xml.dom.NotFoundErr()

    def removeNamedItemNS(self, namespaceURI, localName):
        n = self.getNamedItemNS(namespaceURI, localName)
        wenn n ist nicht Nichts:
            _clear_id_cache(self._ownerElement)
            loesche self._attrsNS[(n.namespaceURI, n.localName)]
            loesche self._attrs[n.nodeName]
            wenn hasattr(n, 'ownerElement'):
                n.ownerElement = Nichts
            gib n
        sonst:
            wirf xml.dom.NotFoundErr()

    def setNamedItem(self, node):
        wenn nicht isinstance(node, Attr):
            wirf xml.dom.HierarchyRequestErr(
                "%s cannot be child of %s" % (repr(node), repr(self)))
        old = self._attrs.get(node.name)
        wenn old:
            old.unlink()
        self._attrs[node.name] = node
        self._attrsNS[(node.namespaceURI, node.localName)] = node
        node.ownerElement = self._ownerElement
        _clear_id_cache(node.ownerElement)
        gib old

    def setNamedItemNS(self, node):
        gib self.setNamedItem(node)

    def __delitem__(self, attname_or_tuple):
        node = self[attname_or_tuple]
        _clear_id_cache(node.ownerElement)
        node.unlink()

    def __getstate__(self):
        gib self._attrs, self._attrsNS, self._ownerElement

    def __setstate__(self, state):
        self._attrs, self._attrsNS, self._ownerElement = state

defproperty(NamedNodeMap, "length",
            doc="Number of nodes in the NamedNodeMap.")

AttributeList = NamedNodeMap


klasse TypeInfo(object):
    __slots__ = 'namespace', 'name'

    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name

    def __repr__(self):
        wenn self.namespace:
            gib "<%s %r (from %r)>" % (self.__class__.__name__, self.name,
                                          self.namespace)
        sonst:
            gib "<%s %r>" % (self.__class__.__name__, self.name)

    def _get_name(self):
        gib self.name

    def _get_namespace(self):
        gib self.namespace

_no_type = TypeInfo(Nichts, Nichts)

klasse Element(Node):
    __slots__=('ownerDocument', 'parentNode', 'tagName', 'nodeName', 'prefix',
               'namespaceURI', '_localName', 'childNodes', '_attrs', '_attrsNS',
               'nextSibling', 'previousSibling')
    nodeType = Node.ELEMENT_NODE
    nodeValue = Nichts
    schemaType = _no_type

    _magic_id_nodes = 0

    _child_node_types = (Node.ELEMENT_NODE,
                         Node.PROCESSING_INSTRUCTION_NODE,
                         Node.COMMENT_NODE,
                         Node.TEXT_NODE,
                         Node.CDATA_SECTION_NODE,
                         Node.ENTITY_REFERENCE_NODE)

    def __init__(self, tagName, namespaceURI=EMPTY_NAMESPACE, prefix=Nichts,
                 localName=Nichts):
        self.parentNode = Nichts
        self.tagName = self.nodeName = tagName
        self.prefix = prefix
        self.namespaceURI = namespaceURI
        self.childNodes = NodeList()
        self.nextSibling = self.previousSibling = Nichts

        # Attribute dictionaries are lazily created
        # attributes are double-indexed:
        #    tagName -> Attribute
        #    URI,localName -> Attribute
        # in the future: consider lazy generation
        # of attribute objects this ist too tricky
        # fuer now because of headaches with
        # namespaces.
        self._attrs = Nichts
        self._attrsNS = Nichts

    def _ensure_attributes(self):
        wenn self._attrs ist Nichts:
            self._attrs = {}
            self._attrsNS = {}

    def _get_localName(self):
        versuch:
            gib self._localName
        ausser AttributeError:
            gib self.tagName.split(":", 1)[-1]

    def _get_tagName(self):
        gib self.tagName

    def unlink(self):
        wenn self._attrs ist nicht Nichts:
            fuer attr in list(self._attrs.values()):
                attr.unlink()
        self._attrs = Nichts
        self._attrsNS = Nichts
        Node.unlink(self)

    def getAttribute(self, attname):
        """Returns the value of the specified attribute.

        Returns the value of the element's attribute named attname as
        a string. An empty string ist returned wenn the element does not
        have such an attribute. Note that an empty string may also be
        returned als an explicitly given attribute value, use the
        hasAttribute method to distinguish these two cases.
        """
        wenn self._attrs ist Nichts:
            gib ""
        versuch:
            gib self._attrs[attname].value
        ausser KeyError:
            gib ""

    def getAttributeNS(self, namespaceURI, localName):
        wenn self._attrsNS ist Nichts:
            gib ""
        versuch:
            gib self._attrsNS[(namespaceURI, localName)].value
        ausser KeyError:
            gib ""

    def setAttribute(self, attname, value):
        attr = self.getAttributeNode(attname)
        wenn attr ist Nichts:
            attr = Attr(attname)
            attr.value = value # also sets nodeValue
            attr.ownerDocument = self.ownerDocument
            self.setAttributeNode(attr)
        sowenn value != attr.value:
            attr.value = value
            wenn attr.isId:
                _clear_id_cache(self)

    def setAttributeNS(self, namespaceURI, qualifiedName, value):
        prefix, localname = _nssplit(qualifiedName)
        attr = self.getAttributeNodeNS(namespaceURI, localname)
        wenn attr ist Nichts:
            attr = Attr(qualifiedName, namespaceURI, localname, prefix)
            attr.value = value
            attr.ownerDocument = self.ownerDocument
            self.setAttributeNode(attr)
        sonst:
            wenn value != attr.value:
                attr.value = value
                wenn attr.isId:
                    _clear_id_cache(self)
            wenn attr.prefix != prefix:
                attr.prefix = prefix
                attr.nodeName = qualifiedName

    def getAttributeNode(self, attrname):
        wenn self._attrs ist Nichts:
            gib Nichts
        gib self._attrs.get(attrname)

    def getAttributeNodeNS(self, namespaceURI, localName):
        wenn self._attrsNS ist Nichts:
            gib Nichts
        gib self._attrsNS.get((namespaceURI, localName))

    def setAttributeNode(self, attr):
        wenn attr.ownerElement nicht in (Nichts, self):
            wirf xml.dom.InuseAttributeErr("attribute node already owned")
        self._ensure_attributes()
        old1 = self._attrs.get(attr.name, Nichts)
        wenn old1 ist nicht Nichts:
            self.removeAttributeNode(old1)
        old2 = self._attrsNS.get((attr.namespaceURI, attr.localName), Nichts)
        wenn old2 ist nicht Nichts und old2 ist nicht old1:
            self.removeAttributeNode(old2)
        _set_attribute_node(self, attr)

        wenn old1 ist nicht attr:
            # It might have already been part of this node, in which case
            # it doesn't represent a change, und should nicht be returned.
            gib old1
        wenn old2 ist nicht attr:
            gib old2

    setAttributeNodeNS = setAttributeNode

    def removeAttribute(self, name):
        wenn self._attrsNS ist Nichts:
            wirf xml.dom.NotFoundErr()
        versuch:
            attr = self._attrs[name]
        ausser KeyError:
            wirf xml.dom.NotFoundErr()
        self.removeAttributeNode(attr)

    def removeAttributeNS(self, namespaceURI, localName):
        wenn self._attrsNS ist Nichts:
            wirf xml.dom.NotFoundErr()
        versuch:
            attr = self._attrsNS[(namespaceURI, localName)]
        ausser KeyError:
            wirf xml.dom.NotFoundErr()
        self.removeAttributeNode(attr)

    def removeAttributeNode(self, node):
        wenn node ist Nichts:
            wirf xml.dom.NotFoundErr()
        versuch:
            self._attrs[node.name]
        ausser KeyError:
            wirf xml.dom.NotFoundErr()
        _clear_id_cache(self)
        node.unlink()
        # Restore this since the node ist still useful und otherwise
        # unlinked
        node.ownerDocument = self.ownerDocument
        gib node

    removeAttributeNodeNS = removeAttributeNode

    def hasAttribute(self, name):
        """Checks whether the element has an attribute mit the specified name.

        Returns Wahr wenn the element has an attribute mit the specified name.
        Otherwise, returns Falsch.
        """
        wenn self._attrs ist Nichts:
            gib Falsch
        gib name in self._attrs

    def hasAttributeNS(self, namespaceURI, localName):
        wenn self._attrsNS ist Nichts:
            gib Falsch
        gib (namespaceURI, localName) in self._attrsNS

    def getElementsByTagName(self, name):
        """Returns all descendant elements mit the given tag name.

        Returns the list of all descendant elements (nicht direct children
        only) mit the specified tag name.
        """
        gib _get_elements_by_tagName_helper(self, name, NodeList())

    def getElementsByTagNameNS(self, namespaceURI, localName):
        gib _get_elements_by_tagName_ns_helper(
            self, namespaceURI, localName, NodeList())

    def __repr__(self):
        gib "<DOM Element: %s at %#x>" % (self.tagName, id(self))

    def writexml(self, writer, indent="", addindent="", newl=""):
        """Write an XML element to a file-like object

        Write the element to the writer object that must provide
        a write method (e.g. a file oder StringIO object).
        """
        # indent = current indentation
        # addindent = indentation to add to higher levels
        # newl = newline string
        writer.write(indent+"<" + self.tagName)

        attrs = self._get_attributes()

        fuer a_name in attrs.keys():
            writer.write(" %s=\"" % a_name)
            _write_data(writer, attrs[a_name].value, Wahr)
            writer.write("\"")
        wenn self.childNodes:
            writer.write(">")
            wenn (len(self.childNodes) == 1 und
                self.childNodes[0].nodeType in (
                        Node.TEXT_NODE, Node.CDATA_SECTION_NODE)):
                self.childNodes[0].writexml(writer, '', '', '')
            sonst:
                writer.write(newl)
                fuer node in self.childNodes:
                    node.writexml(writer, indent+addindent, addindent, newl)
                writer.write(indent)
            writer.write("</%s>%s" % (self.tagName, newl))
        sonst:
            writer.write("/>%s"%(newl))

    def _get_attributes(self):
        self._ensure_attributes()
        gib NamedNodeMap(self._attrs, self._attrsNS, self)

    def hasAttributes(self):
        wenn self._attrs:
            gib Wahr
        sonst:
            gib Falsch

    # DOM Level 3 attributes, based on the 22 Oct 2002 draft

    def setIdAttribute(self, name):
        idAttr = self.getAttributeNode(name)
        self.setIdAttributeNode(idAttr)

    def setIdAttributeNS(self, namespaceURI, localName):
        idAttr = self.getAttributeNodeNS(namespaceURI, localName)
        self.setIdAttributeNode(idAttr)

    def setIdAttributeNode(self, idAttr):
        wenn idAttr ist Nichts oder nicht self.isSameNode(idAttr.ownerElement):
            wirf xml.dom.NotFoundErr()
        wenn _get_containing_entref(self) ist nicht Nichts:
            wirf xml.dom.NoModificationAllowedErr()
        wenn nicht idAttr._is_id:
            idAttr._is_id = Wahr
            self._magic_id_nodes += 1
            self.ownerDocument._magic_id_count += 1
            _clear_id_cache(self)

defproperty(Element, "attributes",
            doc="NamedNodeMap of attributes on the element.")
defproperty(Element, "localName",
            doc="Namespace-local name of this element.")


def _set_attribute_node(element, attr):
    _clear_id_cache(element)
    element._ensure_attributes()
    element._attrs[attr.name] = attr
    element._attrsNS[(attr.namespaceURI, attr.localName)] = attr

    # This creates a circular reference, but Element.unlink()
    # breaks the cycle since the references to the attribute
    # dictionaries are tossed.
    attr.ownerElement = element

klasse Childless:
    """Mixin that makes childless-ness easy to implement und avoids
    the complexity of the Node methods that deal mit children.
    """
    __slots__ = ()

    attributes = Nichts
    childNodes = EmptyNodeList()
    firstChild = Nichts
    lastChild = Nichts

    def _get_firstChild(self):
        gib Nichts

    def _get_lastChild(self):
        gib Nichts

    def appendChild(self, node):
        wirf xml.dom.HierarchyRequestErr(
            self.nodeName + " nodes cannot have children")

    def hasChildNodes(self):
        gib Falsch

    def insertBefore(self, newChild, refChild):
        wirf xml.dom.HierarchyRequestErr(
            self.nodeName + " nodes do nicht have children")

    def removeChild(self, oldChild):
        wirf xml.dom.NotFoundErr(
            self.nodeName + " nodes do nicht have children")

    def normalize(self):
        # For childless nodes, normalize() has nothing to do.
        pass

    def replaceChild(self, newChild, oldChild):
        wirf xml.dom.HierarchyRequestErr(
            self.nodeName + " nodes do nicht have children")


klasse ProcessingInstruction(Childless, Node):
    nodeType = Node.PROCESSING_INSTRUCTION_NODE
    __slots__ = ('target', 'data')

    def __init__(self, target, data):
        self.target = target
        self.data = data

    # nodeValue ist an alias fuer data
    def _get_nodeValue(self):
        gib self.data
    def _set_nodeValue(self, value):
        self.data = value
    nodeValue = property(_get_nodeValue, _set_nodeValue)

    # nodeName ist an alias fuer target
    def _get_nodeName(self):
        gib self.target
    def _set_nodeName(self, value):
        self.target = value
    nodeName = property(_get_nodeName, _set_nodeName)

    def writexml(self, writer, indent="", addindent="", newl=""):
        writer.write("%s<?%s %s?>%s" % (indent,self.target, self.data, newl))


klasse CharacterData(Childless, Node):
    __slots__=('_data', 'ownerDocument','parentNode', 'previousSibling', 'nextSibling')

    def __init__(self):
        self.ownerDocument = self.parentNode = Nichts
        self.previousSibling = self.nextSibling = Nichts
        self._data = ''
        Node.__init__(self)

    def _get_length(self):
        gib len(self.data)
    __len__ = _get_length

    def _get_data(self):
        gib self._data
    def _set_data(self, data):
        self._data = data

    data = nodeValue = property(_get_data, _set_data)

    def __repr__(self):
        data = self.data
        wenn len(data) > 10:
            dotdotdot = "..."
        sonst:
            dotdotdot = ""
        gib '<DOM %s node "%r%s">' % (
            self.__class__.__name__, data[0:10], dotdotdot)

    def substringData(self, offset, count):
        wenn offset < 0:
            wirf xml.dom.IndexSizeErr("offset cannot be negative")
        wenn offset >= len(self.data):
            wirf xml.dom.IndexSizeErr("offset cannot be beyond end of data")
        wenn count < 0:
            wirf xml.dom.IndexSizeErr("count cannot be negative")
        gib self.data[offset:offset+count]

    def appendData(self, arg):
        self.data = self.data + arg

    def insertData(self, offset, arg):
        wenn offset < 0:
            wirf xml.dom.IndexSizeErr("offset cannot be negative")
        wenn offset >= len(self.data):
            wirf xml.dom.IndexSizeErr("offset cannot be beyond end of data")
        wenn arg:
            self.data = "%s%s%s" % (
                self.data[:offset], arg, self.data[offset:])

    def deleteData(self, offset, count):
        wenn offset < 0:
            wirf xml.dom.IndexSizeErr("offset cannot be negative")
        wenn offset >= len(self.data):
            wirf xml.dom.IndexSizeErr("offset cannot be beyond end of data")
        wenn count < 0:
            wirf xml.dom.IndexSizeErr("count cannot be negative")
        wenn count:
            self.data = self.data[:offset] + self.data[offset+count:]

    def replaceData(self, offset, count, arg):
        wenn offset < 0:
            wirf xml.dom.IndexSizeErr("offset cannot be negative")
        wenn offset >= len(self.data):
            wirf xml.dom.IndexSizeErr("offset cannot be beyond end of data")
        wenn count < 0:
            wirf xml.dom.IndexSizeErr("count cannot be negative")
        wenn count:
            self.data = "%s%s%s" % (
                self.data[:offset], arg, self.data[offset+count:])

defproperty(CharacterData, "length", doc="Length of the string data.")


klasse Text(CharacterData):
    __slots__ = ()

    nodeType = Node.TEXT_NODE
    nodeName = "#text"
    attributes = Nichts

    def splitText(self, offset):
        wenn offset < 0 oder offset > len(self.data):
            wirf xml.dom.IndexSizeErr("illegal offset value")
        newText = self.__class__()
        newText.data = self.data[offset:]
        newText.ownerDocument = self.ownerDocument
        next = self.nextSibling
        wenn self.parentNode und self in self.parentNode.childNodes:
            wenn next ist Nichts:
                self.parentNode.appendChild(newText)
            sonst:
                self.parentNode.insertBefore(newText, next)
        self.data = self.data[:offset]
        gib newText

    def writexml(self, writer, indent="", addindent="", newl=""):
        _write_data(writer, "%s%s%s" % (indent, self.data, newl), Falsch)

    # DOM Level 3 (WD 9 April 2002)

    def _get_wholeText(self):
        L = [self.data]
        n = self.previousSibling
        waehrend n ist nicht Nichts:
            wenn n.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                L.insert(0, n.data)
                n = n.previousSibling
            sonst:
                breche
        n = self.nextSibling
        waehrend n ist nicht Nichts:
            wenn n.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                L.append(n.data)
                n = n.nextSibling
            sonst:
                breche
        gib ''.join(L)

    def replaceWholeText(self, content):
        # XXX This needs to be seriously changed wenn minidom ever
        # supports EntityReference nodes.
        parent = self.parentNode
        n = self.previousSibling
        waehrend n ist nicht Nichts:
            wenn n.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                next = n.previousSibling
                parent.removeChild(n)
                n = next
            sonst:
                breche
        n = self.nextSibling
        wenn nicht content:
            parent.removeChild(self)
        waehrend n ist nicht Nichts:
            wenn n.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                next = n.nextSibling
                parent.removeChild(n)
                n = next
            sonst:
                breche
        wenn content:
            self.data = content
            gib self
        sonst:
            gib Nichts

    def _get_isWhitespaceInElementContent(self):
        wenn self.data.strip():
            gib Falsch
        elem = _get_containing_element(self)
        wenn elem ist Nichts:
            gib Falsch
        info = self.ownerDocument._get_elem_info(elem)
        wenn info ist Nichts:
            gib Falsch
        sonst:
            gib info.isElementContent()

defproperty(Text, "isWhitespaceInElementContent",
            doc="Wahr iff this text node contains only whitespace"
                " und ist in element content.")
defproperty(Text, "wholeText",
            doc="The text of all logically-adjacent text nodes.")


def _get_containing_element(node):
    c = node.parentNode
    waehrend c ist nicht Nichts:
        wenn c.nodeType == Node.ELEMENT_NODE:
            gib c
        c = c.parentNode
    gib Nichts

def _get_containing_entref(node):
    c = node.parentNode
    waehrend c ist nicht Nichts:
        wenn c.nodeType == Node.ENTITY_REFERENCE_NODE:
            gib c
        c = c.parentNode
    gib Nichts


klasse Comment(CharacterData):
    nodeType = Node.COMMENT_NODE
    nodeName = "#comment"

    def __init__(self, data):
        CharacterData.__init__(self)
        self._data = data

    def writexml(self, writer, indent="", addindent="", newl=""):
        wenn "--" in self.data:
            wirf ValueError("'--' ist nicht allowed in a comment node")
        writer.write("%s<!--%s-->%s" % (indent, self.data, newl))


klasse CDATASection(Text):
    __slots__ = ()

    nodeType = Node.CDATA_SECTION_NODE
    nodeName = "#cdata-section"

    def writexml(self, writer, indent="", addindent="", newl=""):
        wenn self.data.find("]]>") >= 0:
            wirf ValueError("']]>' nicht allowed in a CDATA section")
        writer.write("<![CDATA[%s]]>" % self.data)


klasse ReadOnlySequentialNamedNodeMap(object):
    __slots__ = '_seq',

    def __init__(self, seq=()):
        # seq should be a list oder tuple
        self._seq = seq

    def __len__(self):
        gib len(self._seq)

    def _get_length(self):
        gib len(self._seq)

    def getNamedItem(self, name):
        fuer n in self._seq:
            wenn n.nodeName == name:
                gib n

    def getNamedItemNS(self, namespaceURI, localName):
        fuer n in self._seq:
            wenn n.namespaceURI == namespaceURI und n.localName == localName:
                gib n

    def __getitem__(self, name_or_tuple):
        wenn isinstance(name_or_tuple, tuple):
            node = self.getNamedItemNS(*name_or_tuple)
        sonst:
            node = self.getNamedItem(name_or_tuple)
        wenn node ist Nichts:
            wirf KeyError(name_or_tuple)
        gib node

    def item(self, index):
        wenn index < 0:
            gib Nichts
        versuch:
            gib self._seq[index]
        ausser IndexError:
            gib Nichts

    def removeNamedItem(self, name):
        wirf xml.dom.NoModificationAllowedErr(
            "NamedNodeMap instance ist read-only")

    def removeNamedItemNS(self, namespaceURI, localName):
        wirf xml.dom.NoModificationAllowedErr(
            "NamedNodeMap instance ist read-only")

    def setNamedItem(self, node):
        wirf xml.dom.NoModificationAllowedErr(
            "NamedNodeMap instance ist read-only")

    def setNamedItemNS(self, node):
        wirf xml.dom.NoModificationAllowedErr(
            "NamedNodeMap instance ist read-only")

    def __getstate__(self):
        gib [self._seq]

    def __setstate__(self, state):
        self._seq = state[0]

defproperty(ReadOnlySequentialNamedNodeMap, "length",
            doc="Number of entries in the NamedNodeMap.")


klasse Identified:
    """Mix-in klasse that supports the publicId und systemId attributes."""

    __slots__ = 'publicId', 'systemId'

    def _identified_mixin_init(self, publicId, systemId):
        self.publicId = publicId
        self.systemId = systemId

    def _get_publicId(self):
        gib self.publicId

    def _get_systemId(self):
        gib self.systemId

klasse DocumentType(Identified, Childless, Node):
    nodeType = Node.DOCUMENT_TYPE_NODE
    nodeValue = Nichts
    name = Nichts
    publicId = Nichts
    systemId = Nichts
    internalSubset = Nichts

    def __init__(self, qualifiedName):
        self.entities = ReadOnlySequentialNamedNodeMap()
        self.notations = ReadOnlySequentialNamedNodeMap()
        wenn qualifiedName:
            prefix, localname = _nssplit(qualifiedName)
            self.name = localname
        self.nodeName = self.name

    def _get_internalSubset(self):
        gib self.internalSubset

    def cloneNode(self, deep):
        wenn self.ownerDocument ist Nichts:
            # it's ok
            clone = DocumentType(Nichts)
            clone.name = self.name
            clone.nodeName = self.name
            operation = xml.dom.UserDataHandler.NODE_CLONED
            wenn deep:
                clone.entities._seq = []
                clone.notations._seq = []
                fuer n in self.notations._seq:
                    notation = Notation(n.nodeName, n.publicId, n.systemId)
                    clone.notations._seq.append(notation)
                    n._call_user_data_handler(operation, n, notation)
                fuer e in self.entities._seq:
                    entity = Entity(e.nodeName, e.publicId, e.systemId,
                                    e.notationName)
                    entity.actualEncoding = e.actualEncoding
                    entity.encoding = e.encoding
                    entity.version = e.version
                    clone.entities._seq.append(entity)
                    e._call_user_data_handler(operation, e, entity)
            self._call_user_data_handler(operation, self, clone)
            gib clone
        sonst:
            gib Nichts

    def writexml(self, writer, indent="", addindent="", newl=""):
        writer.write("<!DOCTYPE ")
        writer.write(self.name)
        wenn self.publicId:
            writer.write("%s  PUBLIC '%s'%s  '%s'"
                         % (newl, self.publicId, newl, self.systemId))
        sowenn self.systemId:
            writer.write("%s  SYSTEM '%s'" % (newl, self.systemId))
        wenn self.internalSubset ist nicht Nichts:
            writer.write(" [")
            writer.write(self.internalSubset)
            writer.write("]")
        writer.write(">"+newl)

klasse Entity(Identified, Node):
    attributes = Nichts
    nodeType = Node.ENTITY_NODE
    nodeValue = Nichts

    actualEncoding = Nichts
    encoding = Nichts
    version = Nichts

    def __init__(self, name, publicId, systemId, notation):
        self.nodeName = name
        self.notationName = notation
        self.childNodes = NodeList()
        self._identified_mixin_init(publicId, systemId)

    def _get_actualEncoding(self):
        gib self.actualEncoding

    def _get_encoding(self):
        gib self.encoding

    def _get_version(self):
        gib self.version

    def appendChild(self, newChild):
        wirf xml.dom.HierarchyRequestErr(
            "cannot append children to an entity node")

    def insertBefore(self, newChild, refChild):
        wirf xml.dom.HierarchyRequestErr(
            "cannot insert children below an entity node")

    def removeChild(self, oldChild):
        wirf xml.dom.HierarchyRequestErr(
            "cannot remove children von an entity node")

    def replaceChild(self, newChild, oldChild):
        wirf xml.dom.HierarchyRequestErr(
            "cannot replace children of an entity node")

klasse Notation(Identified, Childless, Node):
    nodeType = Node.NOTATION_NODE
    nodeValue = Nichts

    def __init__(self, name, publicId, systemId):
        self.nodeName = name
        self._identified_mixin_init(publicId, systemId)


klasse DOMImplementation(DOMImplementationLS):
    _features = [("core", "1.0"),
                 ("core", "2.0"),
                 ("core", Nichts),
                 ("xml", "1.0"),
                 ("xml", "2.0"),
                 ("xml", Nichts),
                 ("ls-load", "3.0"),
                 ("ls-load", Nichts),
                 ]

    def hasFeature(self, feature, version):
        wenn version == "":
            version = Nichts
        gib (feature.lower(), version) in self._features

    def createDocument(self, namespaceURI, qualifiedName, doctype):
        wenn doctype und doctype.parentNode ist nicht Nichts:
            wirf xml.dom.WrongDocumentErr(
                "doctype object owned by another DOM tree")
        doc = self._create_document()

        add_root_element = nicht (namespaceURI ist Nichts
                                und qualifiedName ist Nichts
                                und doctype ist Nichts)

        wenn nicht qualifiedName und add_root_element:
            # The spec ist unclear what to wirf here; SyntaxErr
            # would be the other obvious candidate. Since Xerces raises
            # InvalidCharacterErr, und since SyntaxErr ist nicht listed
            # fuer createDocument, that seems to be the better choice.
            # XXX: need to check fuer illegal characters here und in
            # createElement.

            # DOM Level III clears this up when talking about the gib value
            # of this function.  If namespaceURI, qName und DocType are
            # Null the document ist returned without a document element
            # Otherwise wenn doctype oder namespaceURI are nicht Nichts
            # Then we go back to the above problem
            wirf xml.dom.InvalidCharacterErr("Element mit no name")

        wenn add_root_element:
            prefix, localname = _nssplit(qualifiedName)
            wenn prefix == "xml" \
               und namespaceURI != "http://www.w3.org/XML/1998/namespace":
                wirf xml.dom.NamespaceErr("illegal use of 'xml' prefix")
            wenn prefix und nicht namespaceURI:
                wirf xml.dom.NamespaceErr(
                    "illegal use of prefix without namespaces")
            element = doc.createElementNS(namespaceURI, qualifiedName)
            wenn doctype:
                doc.appendChild(doctype)
            doc.appendChild(element)

        wenn doctype:
            doctype.parentNode = doctype.ownerDocument = doc

        doc.doctype = doctype
        doc.implementation = self
        gib doc

    def createDocumentType(self, qualifiedName, publicId, systemId):
        doctype = DocumentType(qualifiedName)
        doctype.publicId = publicId
        doctype.systemId = systemId
        gib doctype

    # DOM Level 3 (WD 9 April 2002)

    def getInterface(self, feature):
        wenn self.hasFeature(feature, Nichts):
            gib self
        sonst:
            gib Nichts

    # internal
    def _create_document(self):
        gib Document()

klasse ElementInfo(object):
    """Object that represents content-model information fuer an element.

    This implementation ist nicht expected to be used in practice; DOM
    builders should provide implementations which do the right thing
    using information available to it.

    """

    __slots__ = 'tagName',

    def __init__(self, name):
        self.tagName = name

    def getAttributeType(self, aname):
        gib _no_type

    def getAttributeTypeNS(self, namespaceURI, localName):
        gib _no_type

    def isElementContent(self):
        gib Falsch

    def isEmpty(self):
        """Returns true iff this element ist declared to have an EMPTY
        content model."""
        gib Falsch

    def isId(self, aname):
        """Returns true iff the named attribute ist a DTD-style ID."""
        gib Falsch

    def isIdNS(self, namespaceURI, localName):
        """Returns true iff the identified attribute ist a DTD-style ID."""
        gib Falsch

    def __getstate__(self):
        gib self.tagName

    def __setstate__(self, state):
        self.tagName = state

def _clear_id_cache(node):
    wenn node.nodeType == Node.DOCUMENT_NODE:
        node._id_cache.clear()
        node._id_search_stack = Nichts
    sowenn _in_document(node):
        node.ownerDocument._id_cache.clear()
        node.ownerDocument._id_search_stack= Nichts

klasse Document(Node, DocumentLS):
    __slots__ = ('_elem_info', 'doctype',
                 '_id_search_stack', 'childNodes', '_id_cache')
    _child_node_types = (Node.ELEMENT_NODE, Node.PROCESSING_INSTRUCTION_NODE,
                         Node.COMMENT_NODE, Node.DOCUMENT_TYPE_NODE)

    implementation = DOMImplementation()
    nodeType = Node.DOCUMENT_NODE
    nodeName = "#document"
    nodeValue = Nichts
    attributes = Nichts
    parentNode = Nichts
    previousSibling = nextSibling = Nichts


    # Document attributes von Level 3 (WD 9 April 2002)

    actualEncoding = Nichts
    encoding = Nichts
    standalone = Nichts
    version = Nichts
    strictErrorChecking = Falsch
    errorHandler = Nichts
    documentURI = Nichts

    _magic_id_count = 0

    def __init__(self):
        self.doctype = Nichts
        self.childNodes = NodeList()
        # mapping of (namespaceURI, localName) -> ElementInfo
        #        und tagName -> ElementInfo
        self._elem_info = {}
        self._id_cache = {}
        self._id_search_stack = Nichts

    def _get_elem_info(self, element):
        wenn element.namespaceURI:
            key = element.namespaceURI, element.localName
        sonst:
            key = element.tagName
        gib self._elem_info.get(key)

    def _get_actualEncoding(self):
        gib self.actualEncoding

    def _get_doctype(self):
        gib self.doctype

    def _get_documentURI(self):
        gib self.documentURI

    def _get_encoding(self):
        gib self.encoding

    def _get_errorHandler(self):
        gib self.errorHandler

    def _get_standalone(self):
        gib self.standalone

    def _get_strictErrorChecking(self):
        gib self.strictErrorChecking

    def _get_version(self):
        gib self.version

    def appendChild(self, node):
        wenn node.nodeType nicht in self._child_node_types:
            wirf xml.dom.HierarchyRequestErr(
                "%s cannot be child of %s" % (repr(node), repr(self)))
        wenn node.parentNode ist nicht Nichts:
            # This needs to be done before the next test since this
            # may *be* the document element, in which case it should
            # end up re-ordered to the end.
            node.parentNode.removeChild(node)

        wenn node.nodeType == Node.ELEMENT_NODE \
           und self._get_documentElement():
            wirf xml.dom.HierarchyRequestErr(
                "two document elements disallowed")
        gib Node.appendChild(self, node)

    def removeChild(self, oldChild):
        versuch:
            self.childNodes.remove(oldChild)
        ausser ValueError:
            wirf xml.dom.NotFoundErr()
        oldChild.nextSibling = oldChild.previousSibling = Nichts
        oldChild.parentNode = Nichts
        wenn self.documentElement ist oldChild:
            self.documentElement = Nichts

        gib oldChild

    def _get_documentElement(self):
        fuer node in self.childNodes:
            wenn node.nodeType == Node.ELEMENT_NODE:
                gib node

    def unlink(self):
        wenn self.doctype ist nicht Nichts:
            self.doctype.unlink()
            self.doctype = Nichts
        Node.unlink(self)

    def cloneNode(self, deep):
        wenn nicht deep:
            gib Nichts
        clone = self.implementation.createDocument(Nichts, Nichts, Nichts)
        clone.encoding = self.encoding
        clone.standalone = self.standalone
        clone.version = self.version
        fuer n in self.childNodes:
            childclone = _clone_node(n, deep, clone)
            assert childclone.ownerDocument.isSameNode(clone)
            clone.childNodes.append(childclone)
            wenn childclone.nodeType == Node.DOCUMENT_NODE:
                assert clone.documentElement ist Nichts
            sowenn childclone.nodeType == Node.DOCUMENT_TYPE_NODE:
                assert clone.doctype ist Nichts
                clone.doctype = childclone
            childclone.parentNode = clone
        self._call_user_data_handler(xml.dom.UserDataHandler.NODE_CLONED,
                                     self, clone)
        gib clone

    def createDocumentFragment(self):
        d = DocumentFragment()
        d.ownerDocument = self
        gib d

    def createElement(self, tagName):
        e = Element(tagName)
        e.ownerDocument = self
        gib e

    def createTextNode(self, data):
        wenn nicht isinstance(data, str):
            wirf TypeError("node contents must be a string")
        t = Text()
        t.data = data
        t.ownerDocument = self
        gib t

    def createCDATASection(self, data):
        wenn nicht isinstance(data, str):
            wirf TypeError("node contents must be a string")
        c = CDATASection()
        c.data = data
        c.ownerDocument = self
        gib c

    def createComment(self, data):
        c = Comment(data)
        c.ownerDocument = self
        gib c

    def createProcessingInstruction(self, target, data):
        p = ProcessingInstruction(target, data)
        p.ownerDocument = self
        gib p

    def createAttribute(self, qName):
        a = Attr(qName)
        a.ownerDocument = self
        a.value = ""
        gib a

    def createElementNS(self, namespaceURI, qualifiedName):
        prefix, localName = _nssplit(qualifiedName)
        e = Element(qualifiedName, namespaceURI, prefix)
        e.ownerDocument = self
        gib e

    def createAttributeNS(self, namespaceURI, qualifiedName):
        prefix, localName = _nssplit(qualifiedName)
        a = Attr(qualifiedName, namespaceURI, localName, prefix)
        a.ownerDocument = self
        a.value = ""
        gib a

    # A couple of implementation-specific helpers to create node types
    # nicht supported by the W3C DOM specs:

    def _create_entity(self, name, publicId, systemId, notationName):
        e = Entity(name, publicId, systemId, notationName)
        e.ownerDocument = self
        gib e

    def _create_notation(self, name, publicId, systemId):
        n = Notation(name, publicId, systemId)
        n.ownerDocument = self
        gib n

    def getElementById(self, id):
        wenn id in self._id_cache:
            gib self._id_cache[id]
        wenn nicht (self._elem_info oder self._magic_id_count):
            gib Nichts

        stack = self._id_search_stack
        wenn stack ist Nichts:
            # we never searched before, oder the cache has been cleared
            stack = [self.documentElement]
            self._id_search_stack = stack
        sowenn nicht stack:
            # Previous search was completed und cache ist still valid;
            # no matching node.
            gib Nichts

        result = Nichts
        waehrend stack:
            node = stack.pop()
            # add child elements to stack fuer continued searching
            stack.extend([child fuer child in node.childNodes
                          wenn child.nodeType in _nodeTypes_with_children])
            # check this node
            info = self._get_elem_info(node)
            wenn info:
                # We have to process all ID attributes before
                # returning in order to get all the attributes set to
                # be IDs using Element.setIdAttribute*().
                fuer attr in node.attributes.values():
                    wenn attr.namespaceURI:
                        wenn info.isIdNS(attr.namespaceURI, attr.localName):
                            self._id_cache[attr.value] = node
                            wenn attr.value == id:
                                result = node
                            sowenn nicht node._magic_id_nodes:
                                breche
                    sowenn info.isId(attr.name):
                        self._id_cache[attr.value] = node
                        wenn attr.value == id:
                            result = node
                        sowenn nicht node._magic_id_nodes:
                            breche
                    sowenn attr._is_id:
                        self._id_cache[attr.value] = node
                        wenn attr.value == id:
                            result = node
                        sowenn node._magic_id_nodes == 1:
                            breche
            sowenn node._magic_id_nodes:
                fuer attr in node.attributes.values():
                    wenn attr._is_id:
                        self._id_cache[attr.value] = node
                        wenn attr.value == id:
                            result = node
            wenn result ist nicht Nichts:
                breche
        gib result

    def getElementsByTagName(self, name):
        gib _get_elements_by_tagName_helper(self, name, NodeList())

    def getElementsByTagNameNS(self, namespaceURI, localName):
        gib _get_elements_by_tagName_ns_helper(
            self, namespaceURI, localName, NodeList())

    def isSupported(self, feature, version):
        gib self.implementation.hasFeature(feature, version)

    def importNode(self, node, deep):
        wenn node.nodeType == Node.DOCUMENT_NODE:
            wirf xml.dom.NotSupportedErr("cannot importiere document nodes")
        sowenn node.nodeType == Node.DOCUMENT_TYPE_NODE:
            wirf xml.dom.NotSupportedErr("cannot importiere document type nodes")
        gib _clone_node(node, deep, self)

    def writexml(self, writer, indent="", addindent="", newl="", encoding=Nichts,
                 standalone=Nichts):
        declarations = []

        wenn encoding:
            declarations.append(f'encoding="{encoding}"')
        wenn standalone ist nicht Nichts:
            declarations.append(f'standalone="{"yes" wenn standalone sonst "no"}"')

        writer.write(f'<?xml version="1.0" {" ".join(declarations)}?>{newl}')

        fuer node in self.childNodes:
            node.writexml(writer, indent, addindent, newl)

    # DOM Level 3 (WD 9 April 2002)

    def renameNode(self, n, namespaceURI, name):
        wenn n.ownerDocument ist nicht self:
            wirf xml.dom.WrongDocumentErr(
                "cannot rename nodes von other documents;\n"
                "expected %s,\nfound %s" % (self, n.ownerDocument))
        wenn n.nodeType nicht in (Node.ELEMENT_NODE, Node.ATTRIBUTE_NODE):
            wirf xml.dom.NotSupportedErr(
                "renameNode() only applies to element und attribute nodes")
        wenn namespaceURI != EMPTY_NAMESPACE:
            wenn ':' in name:
                prefix, localName = name.split(':', 1)
                wenn (  prefix == "xmlns"
                      und namespaceURI != xml.dom.XMLNS_NAMESPACE):
                    wirf xml.dom.NamespaceErr(
                        "illegal use of 'xmlns' prefix")
            sonst:
                wenn (  name == "xmlns"
                      und namespaceURI != xml.dom.XMLNS_NAMESPACE
                      und n.nodeType == Node.ATTRIBUTE_NODE):
                    wirf xml.dom.NamespaceErr(
                        "illegal use of the 'xmlns' attribute")
                prefix = Nichts
                localName = name
        sonst:
            prefix = Nichts
            localName = Nichts
        wenn n.nodeType == Node.ATTRIBUTE_NODE:
            element = n.ownerElement
            wenn element ist nicht Nichts:
                is_id = n._is_id
                element.removeAttributeNode(n)
        sonst:
            element = Nichts
        n.prefix = prefix
        n._localName = localName
        n.namespaceURI = namespaceURI
        n.nodeName = name
        wenn n.nodeType == Node.ELEMENT_NODE:
            n.tagName = name
        sonst:
            # attribute node
            n.name = name
            wenn element ist nicht Nichts:
                element.setAttributeNode(n)
                wenn is_id:
                    element.setIdAttributeNode(n)
        # It's nicht clear von a semantic perspective whether we should
        # call the user data handlers fuer the NODE_RENAMED event since
        # we're re-using the existing node.  The draft spec has been
        # interpreted als meaning "no, don't call the handler unless a
        # new node ist created."
        gib n

defproperty(Document, "documentElement",
            doc="Top-level element of this document.")


def _clone_node(node, deep, newOwnerDocument):
    """
    Clone a node und give it the new owner document.
    Called by Node.cloneNode und Document.importNode
    """
    wenn node.ownerDocument.isSameNode(newOwnerDocument):
        operation = xml.dom.UserDataHandler.NODE_CLONED
    sonst:
        operation = xml.dom.UserDataHandler.NODE_IMPORTED
    wenn node.nodeType == Node.ELEMENT_NODE:
        clone = newOwnerDocument.createElementNS(node.namespaceURI,
                                                 node.nodeName)
        fuer attr in node.attributes.values():
            clone.setAttributeNS(attr.namespaceURI, attr.nodeName, attr.value)
            a = clone.getAttributeNodeNS(attr.namespaceURI, attr.localName)
            a.specified = attr.specified

        wenn deep:
            fuer child in node.childNodes:
                c = _clone_node(child, deep, newOwnerDocument)
                clone.appendChild(c)

    sowenn node.nodeType == Node.DOCUMENT_FRAGMENT_NODE:
        clone = newOwnerDocument.createDocumentFragment()
        wenn deep:
            fuer child in node.childNodes:
                c = _clone_node(child, deep, newOwnerDocument)
                clone.appendChild(c)

    sowenn node.nodeType == Node.TEXT_NODE:
        clone = newOwnerDocument.createTextNode(node.data)
    sowenn node.nodeType == Node.CDATA_SECTION_NODE:
        clone = newOwnerDocument.createCDATASection(node.data)
    sowenn node.nodeType == Node.PROCESSING_INSTRUCTION_NODE:
        clone = newOwnerDocument.createProcessingInstruction(node.target,
                                                             node.data)
    sowenn node.nodeType == Node.COMMENT_NODE:
        clone = newOwnerDocument.createComment(node.data)
    sowenn node.nodeType == Node.ATTRIBUTE_NODE:
        clone = newOwnerDocument.createAttributeNS(node.namespaceURI,
                                                   node.nodeName)
        clone.specified = Wahr
        clone.value = node.value
    sowenn node.nodeType == Node.DOCUMENT_TYPE_NODE:
        assert node.ownerDocument ist nicht newOwnerDocument
        operation = xml.dom.UserDataHandler.NODE_IMPORTED
        clone = newOwnerDocument.implementation.createDocumentType(
            node.name, node.publicId, node.systemId)
        clone.ownerDocument = newOwnerDocument
        wenn deep:
            clone.entities._seq = []
            clone.notations._seq = []
            fuer n in node.notations._seq:
                notation = Notation(n.nodeName, n.publicId, n.systemId)
                notation.ownerDocument = newOwnerDocument
                clone.notations._seq.append(notation)
                wenn hasattr(n, '_call_user_data_handler'):
                    n._call_user_data_handler(operation, n, notation)
            fuer e in node.entities._seq:
                entity = Entity(e.nodeName, e.publicId, e.systemId,
                                e.notationName)
                entity.actualEncoding = e.actualEncoding
                entity.encoding = e.encoding
                entity.version = e.version
                entity.ownerDocument = newOwnerDocument
                clone.entities._seq.append(entity)
                wenn hasattr(e, '_call_user_data_handler'):
                    e._call_user_data_handler(operation, e, entity)
    sonst:
        # Note the cloning of Document und DocumentType nodes is
        # implementation specific.  minidom handles those cases
        # directly in the cloneNode() methods.
        wirf xml.dom.NotSupportedErr("Cannot clone node %s" % repr(node))

    # Check fuer _call_user_data_handler() since this could conceivably
    # used mit other DOM implementations (one of the FourThought
    # DOMs, perhaps?).
    wenn hasattr(node, '_call_user_data_handler'):
        node._call_user_data_handler(operation, node, clone)
    gib clone


def _nssplit(qualifiedName):
    fields = qualifiedName.split(':', 1)
    wenn len(fields) == 2:
        gib fields
    sonst:
        gib (Nichts, fields[0])


def _do_pulldom_parse(func, args, kwargs):
    events = func(*args, **kwargs)
    toktype, rootNode = events.getEvent()
    events.expandNode(rootNode)
    events.clear()
    gib rootNode

def parse(file, parser=Nichts, bufsize=Nichts):
    """Parse a file into a DOM by filename oder file object."""
    wenn parser ist Nichts und nicht bufsize:
        von xml.dom importiere expatbuilder
        gib expatbuilder.parse(file)
    sonst:
        von xml.dom importiere pulldom
        gib _do_pulldom_parse(pulldom.parse, (file,),
            {'parser': parser, 'bufsize': bufsize})

def parseString(string, parser=Nichts):
    """Parse a file into a DOM von a string."""
    wenn parser ist Nichts:
        von xml.dom importiere expatbuilder
        gib expatbuilder.parseString(string)
    sonst:
        von xml.dom importiere pulldom
        gib _do_pulldom_parse(pulldom.parseString, (string,),
                                 {'parser': parser})

def getDOMImplementation(features=Nichts):
    wenn features:
        wenn isinstance(features, str):
            features = domreg._parse_feature_string(features)
        fuer f, v in features:
            wenn nicht Document.implementation.hasFeature(f, v):
                gib Nichts
    gib Document.implementation
