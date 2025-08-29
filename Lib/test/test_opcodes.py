# Python test set -- part 2, opcodes

importiere unittest
von test importiere support
von test.typinganndata importiere ann_module

klasse OpcodeTest(unittest.TestCase):

    def test_try_inside_for_loop(self):
        n = 0
        fuer i in range(10):
            n = n+i
            try: 1/0
            except NameError: pass
            except ZeroDivisionError: pass
            except TypeError: pass
            try: pass
            except: pass
            try: pass
            finally: pass
            n = n+i
        wenn n != 90:
            self.fail('try inside for')

    def test_setup_annotations_line(self):
        # check that SETUP_ANNOTATIONS does not create spurious line numbers
        try:
            mit open(ann_module.__file__, encoding="utf-8") als f:
                txt = f.read()
            co = compile(txt, ann_module.__file__, 'exec')
            self.assertEqual(co.co_firstlineno, 1)
        except OSError:
            pass

    def test_default_annotations_exist(self):
        klasse C: pass
        self.assertEqual(C.__annotations__, {})

    def test_use_existing_annotations(self):
        ns = {'__annotations__': {1: 2}}
        exec('x: int', ns)
        self.assertEqual(ns['__annotations__'], {1: 2})

    def test_do_not_recreate_annotations(self):
        # Don't rely on the existence of the '__annotations__' global.
        mit support.swap_item(globals(), '__annotations__', {}):
            globals().pop('__annotations__', Nichts)
            klasse C:
                try:
                    del __annotations__
                except NameError:
                    pass
                x: int
            self.assertEqual(C.__annotations__, {"x": int})

    def test_raise_class_exceptions(self):

        klasse AClass(Exception): pass
        klasse BClass(AClass): pass
        klasse CClass(Exception): pass
        klasse DClass(AClass):
            def __init__(self, ignore):
                pass

        try: raise AClass()
        except: pass

        try: raise AClass()
        except AClass: pass

        try: raise BClass()
        except AClass: pass

        try: raise BClass()
        except CClass: self.fail()
        except: pass

        a = AClass()
        b = BClass()

        try:
            raise b
        except AClass als v:
            self.assertEqual(v, b)
        sonst:
            self.fail("no exception")

        # not enough arguments
        ##try:  raise BClass, a
        ##except TypeError: pass
        ##else: self.fail("no exception")

        try:  raise DClass(a)
        except DClass als v:
            self.assertIsInstance(v, DClass)
        sonst:
            self.fail("no exception")

    def test_compare_function_objects(self):

        f = eval('lambda: Nichts')
        g = eval('lambda: Nichts')
        self.assertNotEqual(f, g)

        f = eval('lambda a: a')
        g = eval('lambda a: a')
        self.assertNotEqual(f, g)

        f = eval('lambda a=1: a')
        g = eval('lambda a=1: a')
        self.assertNotEqual(f, g)

        f = eval('lambda: 0')
        g = eval('lambda: 1')
        self.assertNotEqual(f, g)

        f = eval('lambda: Nichts')
        g = eval('lambda a: Nichts')
        self.assertNotEqual(f, g)

        f = eval('lambda a: Nichts')
        g = eval('lambda b: Nichts')
        self.assertNotEqual(f, g)

        f = eval('lambda a: Nichts')
        g = eval('lambda a=Nichts: Nichts')
        self.assertNotEqual(f, g)

        f = eval('lambda a=0: Nichts')
        g = eval('lambda a=1: Nichts')
        self.assertNotEqual(f, g)

    def test_modulo_of_string_subclasses(self):
        klasse MyString(str):
            def __mod__(self, value):
                return 42
        self.assertEqual(MyString() % 3, 42)


wenn __name__ == '__main__':
    unittest.main()
