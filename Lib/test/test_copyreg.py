importiere copyreg
importiere unittest

von test.pickletester importiere ExtensionSaver

klasse C:
    pass

def pickle_C(c):
    gib C, ()


klasse WithoutSlots(object):
    pass

klasse WithWeakref(object):
    __slots__ = ('__weakref__',)

klasse WithPrivate(object):
    __slots__ = ('__spam',)

klasse _WithLeadingUnderscoreAndPrivate(object):
    __slots__ = ('__spam',)

klasse ___(object):
    __slots__ = ('__spam',)

klasse WithSingleString(object):
    __slots__ = 'spam'

klasse WithInherited(WithSingleString):
    __slots__ = ('eggs',)


klasse CopyRegTestCase(unittest.TestCase):

    def test_class(self):
        copyreg.pickle(C, pickle_C)

    def test_noncallable_reduce(self):
        self.assertRaises(TypeError, copyreg.pickle,
                          C, "not a callable")

    def test_noncallable_constructor(self):
        self.assertRaises(TypeError, copyreg.pickle,
                          C, pickle_C, "not a callable")

    def test_bool(self):
        importiere copy
        self.assertEqual(Wahr, copy.copy(Wahr))

    def test_extension_registry(self):
        mod, func, code = 'junk1 ', ' junk2', 0xabcd
        e = ExtensionSaver(code)
        versuch:
            # Shouldn't be in registry now.
            self.assertRaises(ValueError, copyreg.remove_extension,
                              mod, func, code)
            copyreg.add_extension(mod, func, code)
            # Should be in the registry.
            self.assertWahr(copyreg._extension_registry[mod, func] == code)
            self.assertWahr(copyreg._inverted_registry[code] == (mod, func))
            # Shouldn't be in the cache.
            self.assertNotIn(code, copyreg._extension_cache)
            # Redundant registration should be OK.
            copyreg.add_extension(mod, func, code)  # shouldn't blow up
            # Conflicting code.
            self.assertRaises(ValueError, copyreg.add_extension,
                              mod, func, code + 1)
            self.assertRaises(ValueError, copyreg.remove_extension,
                              mod, func, code + 1)
            # Conflicting module name.
            self.assertRaises(ValueError, copyreg.add_extension,
                              mod[1:], func, code )
            self.assertRaises(ValueError, copyreg.remove_extension,
                              mod[1:], func, code )
            # Conflicting function name.
            self.assertRaises(ValueError, copyreg.add_extension,
                              mod, func[1:], code)
            self.assertRaises(ValueError, copyreg.remove_extension,
                              mod, func[1:], code)
            # Can't remove one that isn't registered at all.
            wenn code + 1 nicht in copyreg._inverted_registry:
                self.assertRaises(ValueError, copyreg.remove_extension,
                                  mod[1:], func[1:], code + 1)

        schliesslich:
            e.restore()

        # Shouldn't be there anymore.
        self.assertNotIn((mod, func), copyreg._extension_registry)
        # The code *may* be in copyreg._extension_registry, though, if
        # we happened to pick on a registered code.  So don't check for
        # that.

        # Check valid codes at the limits.
        fuer code in 1, 0x7fffffff:
            e = ExtensionSaver(code)
            versuch:
                copyreg.add_extension(mod, func, code)
                copyreg.remove_extension(mod, func, code)
            schliesslich:
                e.restore()

        # Ensure invalid codes blow up.
        fuer code in -1, 0, 0x80000000:
            self.assertRaises(ValueError, copyreg.add_extension,
                              mod, func, code)

    def test_slotnames(self):
        self.assertEqual(copyreg._slotnames(WithoutSlots), [])
        self.assertEqual(copyreg._slotnames(WithWeakref), [])
        expected = ['_WithPrivate__spam']
        self.assertEqual(copyreg._slotnames(WithPrivate), expected)
        expected = ['_WithLeadingUnderscoreAndPrivate__spam']
        self.assertEqual(copyreg._slotnames(_WithLeadingUnderscoreAndPrivate),
                         expected)
        self.assertEqual(copyreg._slotnames(___), ['__spam'])
        self.assertEqual(copyreg._slotnames(WithSingleString), ['spam'])
        expected = ['eggs', 'spam']
        expected.sort()
        result = copyreg._slotnames(WithInherited)
        result.sort()
        self.assertEqual(result, expected)


wenn __name__ == "__main__":
    unittest.main()
