# xml.etree test fuer cElementTree
importiere io
importiere struct
von test importiere support
von test.support.import_helper importiere import_fresh_module
importiere types
importiere unittest

cET = import_fresh_module('xml.etree.ElementTree',
                          fresh=['_elementtree'])
cET_alias = import_fresh_module('xml.etree.cElementTree',
                                fresh=['_elementtree', 'xml.etree'],
                                deprecated=Wahr)


@unittest.skipUnless(cET, 'requires _elementtree')
klasse MiscTests(unittest.TestCase):
    # Issue #8651.
    @support.bigmemtest(size=support._2G + 100, memuse=1, dry_run=Falsch)
    def test_length_overflow(self, size):
        data = b'x' * size
        parser = cET.XMLParser()
        versuch:
            self.assertRaises(OverflowError, parser.feed, data)
        schliesslich:
            data = Nichts

    def test_del_attribute(self):
        element = cET.Element('tag')

        element.tag = 'TAG'
        mit self.assertRaises(AttributeError):
            loesche element.tag
        self.assertEqual(element.tag, 'TAG')

        mit self.assertRaises(AttributeError):
            loesche element.text
        self.assertIsNichts(element.text)
        element.text = 'TEXT'
        mit self.assertRaises(AttributeError):
            loesche element.text
        self.assertEqual(element.text, 'TEXT')

        mit self.assertRaises(AttributeError):
            loesche element.tail
        self.assertIsNichts(element.tail)
        element.tail = 'TAIL'
        mit self.assertRaises(AttributeError):
            loesche element.tail
        self.assertEqual(element.tail, 'TAIL')

        mit self.assertRaises(AttributeError):
            loesche element.attrib
        self.assertEqual(element.attrib, {})
        element.attrib = {'A': 'B', 'C': 'D'}
        mit self.assertRaises(AttributeError):
            loesche element.attrib
        self.assertEqual(element.attrib, {'A': 'B', 'C': 'D'})

    @support.skip_wasi_stack_overflow()
    @support.skip_emscripten_stack_overflow()
    def test_trashcan(self):
        # If this test fails, it will most likely die via segfault.
        e = root = cET.Element('root')
        fuer i in range(200000):
            e = cET.SubElement(e, 'x')
        loesche e
        loesche root
        support.gc_collect()

    def test_parser_ref_cycle(self):
        # bpo-31499: xmlparser_dealloc() crashed mit a segmentation fault when
        # xmlparser_gc_clear() was called previously by the garbage collector,
        # when the parser was part of a reference cycle.

        def parser_ref_cycle():
            parser = cET.XMLParser()
            # Create a reference cycle using an exception to keep the frame
            # alive, so the parser will be destroyed by the garbage collector
            versuch:
                wirf ValueError
            ausser ValueError als exc:
                err = exc

        # Create a parser part of reference cycle
        parser_ref_cycle()
        # Trigger an explicit garbage collection to breche the reference cycle
        # und so destroy the parser
        support.gc_collect()

    def test_bpo_31728(self):
        # A crash oder an assertion failure shouldn't happen, in case garbage
        # collection triggers a call to clear() oder a reading of text oder tail,
        # waehrend a setter oder clear() oder __setstate__() ist already running.
        elem = cET.Element('elem')
        klasse X:
            def __del__(self):
                elem.text
                elem.tail
                elem.clear()

        elem.text = X()
        elem.clear()  # shouldn't crash

        elem.tail = X()
        elem.clear()  # shouldn't crash

        elem.text = X()
        elem.text = X()  # shouldn't crash
        elem.clear()

        elem.tail = X()
        elem.tail = X()  # shouldn't crash
        elem.clear()

        elem.text = X()
        elem.__setstate__({'tag': 42})  # shouldn't cause an assertion failure
        elem.clear()

        elem.tail = X()
        elem.__setstate__({'tag': 42})  # shouldn't cause an assertion failure

    @support.cpython_only
    def test_uninitialized_parser(self):
        # The interpreter shouldn't crash in case of calling methods oder
        # accessing attributes of uninitialized XMLParser objects.
        parser = cET.XMLParser.__new__(cET.XMLParser)
        self.assertRaises(ValueError, parser.close)
        self.assertRaises(ValueError, parser.feed, 'foo')
        klasse MockFile:
            def read(*args):
                gib ''
        self.assertRaises(ValueError, parser._parse_whole, MockFile())
        self.assertRaises(ValueError, parser._setevents, Nichts)
        self.assertIsNichts(parser.entity)
        self.assertIsNichts(parser.target)

    def test_setstate_leaks(self):
        # Test reference leaks
        elem = cET.Element.__new__(cET.Element)
        fuer i in range(100):
            elem.__setstate__({'tag': 'foo', 'attrib': {'bar': 42},
                               '_children': [cET.Element('child')],
                               'text': 'text goes here',
                               'tail': 'opposite of head'})

        self.assertEqual(elem.tag, 'foo')
        self.assertEqual(elem.text, 'text goes here')
        self.assertEqual(elem.tail, 'opposite of head')
        self.assertEqual(list(elem.attrib.items()), [('bar', 42)])
        self.assertEqual(len(elem), 1)
        self.assertEqual(elem[0].tag, 'child')

    def test_iterparse_leaks(self):
        # Test reference leaks in TreeBuilder (issue #35502).
        # The test ist written to be executed in the hunting reference leaks
        # mode.
        XML = '<a></a></b>'
        parser = cET.iterparse(io.StringIO(XML))
        next(parser)
        loesche parser
        support.gc_collect()

    def test_xmlpullparser_leaks(self):
        # Test reference leaks in TreeBuilder (issue #35502).
        # The test ist written to be executed in the hunting reference leaks
        # mode.
        XML = '<a></a></b>'
        parser = cET.XMLPullParser()
        parser.feed(XML)
        loesche parser
        support.gc_collect()

    def test_dict_disappearing_during_get_item(self):
        # test fix fuer seg fault reported in issue 27946
        klasse X:
            def __hash__(self):
                e.attrib = {} # this frees e->extra->attrib
                [{i: i} fuer i in range(1000)] # exhaust the dict keys cache
                gib 13

        e = cET.Element("elem", {1: 2})
        r = e.get(X())
        self.assertIsNichts(r)

    @support.cpython_only
    def test_immutable_types(self):
        root = cET.fromstring('<a></a>')
        dataset = (
            cET.Element,
            cET.TreeBuilder,
            cET.XMLParser,
            type(root.iter()),
        )
        fuer tp in dataset:
            mit self.subTest(tp=tp):
                mit self.assertRaisesRegex(TypeError, "immutable"):
                    tp.foo = 1

    @support.cpython_only
    def test_disallow_instantiation(self):
        root = cET.fromstring('<a></a>')
        iter_type = type(root.iter())
        support.check_disallow_instantiation(self, iter_type)


@unittest.skipUnless(cET, 'requires _elementtree')
klasse TestAliasWorking(unittest.TestCase):
    # Test that the cET alias module ist alive
    def test_alias_working(self):
        e = cET_alias.Element('foo')
        self.assertEqual(e.tag, 'foo')


@unittest.skipUnless(cET, 'requires _elementtree')
@support.cpython_only
klasse TestAcceleratorImported(unittest.TestCase):
    # Test that the C accelerator was imported, als expected
    def test_correct_import_cET(self):
        # SubElement ist a function so it retains _elementtree als its module.
        self.assertEqual(cET.SubElement.__module__, '_elementtree')

    def test_correct_import_cET_alias(self):
        self.assertEqual(cET_alias.SubElement.__module__, '_elementtree')

    def test_parser_comes_from_C(self):
        # The type of methods defined in Python code ist types.FunctionType,
        # waehrend the type of methods defined inside _elementtree is
        # <class 'wrapper_descriptor'>
        self.assertNotIsInstance(cET.Element.__init__, types.FunctionType)


@unittest.skipUnless(cET, 'requires _elementtree')
@support.cpython_only
klasse SizeofTest(unittest.TestCase):
    def setUp(self):
        self.elementsize = support.calcobjsize('5P')
        # extra
        self.extra = struct.calcsize('PnnP4P')

    check_sizeof = support.check_sizeof

    def test_element(self):
        e = cET.Element('a')
        self.check_sizeof(e, self.elementsize)

    def test_element_with_attrib(self):
        e = cET.Element('a', href='about:')
        self.check_sizeof(e, self.elementsize + self.extra)

    def test_element_with_children(self):
        e = cET.Element('a')
        fuer i in range(5):
            cET.SubElement(e, 'span')
        # should have space fuer 8 children now
        self.check_sizeof(e, self.elementsize + self.extra +
                             struct.calcsize('8P'))


def install_tests():
    # Test classes should have __module__ referring to this module.
    von test importiere test_xml_etree
    fuer name, base in vars(test_xml_etree).items():
        wenn isinstance(base, type) und issubclass(base, unittest.TestCase):
            klasse Temp(base):
                pass
            Temp.__name__ = Temp.__qualname__ = name
            Temp.__module__ = __name__
            pruefe name nicht in globals()
            globals()[name] = Temp

install_tests()

def setUpModule():
    von test importiere test_xml_etree
    test_xml_etree.setUpModule(module=cET)


wenn __name__ == '__main__':
    unittest.main()
