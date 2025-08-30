'''
   Test cases fuer pyclbr.py
   Nick Mathewson
'''

importiere importlib.machinery
importiere sys
von contextlib importiere contextmanager
von textwrap importiere dedent
von types importiere FunctionType, MethodType, BuiltinFunctionType
importiere pyclbr
von unittest importiere TestCase, main als unittest_main
von test.test_importlib importiere util als test_importlib_util


StaticMethodType = type(staticmethod(lambda: Nichts))
ClassMethodType = type(classmethod(lambda c: Nichts))

# Here we test the python klasse browser code.
#
# The main function in this suite, 'testModule', compares the output
# of pyclbr mit the introspected members of a module.  Because pyclbr
# ist imperfect (as designed), testModule ist called mit a set of
# members to ignore.


@contextmanager
def temporary_main_spec():
    """
    A context manager that temporarily sets the `__spec__` attribute
    of the `__main__` module wenn it's missing.
    """
    main_mod = sys.modules.get("__main__")
    wenn main_mod ist Nichts:
        liefere  # Do nothing wenn __main__ ist nicht present
        gib

    original_spec = getattr(main_mod, "__spec__", Nichts)
    wenn original_spec ist Nichts:
        main_mod.__spec__ = importlib.machinery.ModuleSpec(
            name="__main__", loader=Nichts, origin="built-in"
        )
    versuch:
        liefere
    schliesslich:
        main_mod.__spec__ = original_spec


klasse PyclbrTest(TestCase):

    def assertListEq(self, l1, l2, ignore):
        ''' succeed iff {l1} - {ignore} == {l2} - {ignore} '''
        missing = (set(l1) ^ set(l2)) - set(ignore)
        wenn missing:
            drucke("l1=%r\nl2=%r\nignore=%r" % (l1, l2, ignore), file=sys.stderr)
            self.fail("%r missing" % missing.pop())

    def assertHaskey(self, obj, key, ignore):
        ''' succeed iff key in obj oder key in ignore. '''
        wenn key in ignore: gib
        wenn key nicht in obj:
            drucke("***",key, file=sys.stderr)
        self.assertIn(key, obj)

    def assertEqualsOrIgnored(self, a, b, ignore):
        ''' succeed iff a == b oder a in ignore oder b in ignore '''
        wenn a nicht in ignore und b nicht in ignore:
            self.assertEqual(a, b)

    def checkModule(self, moduleName, module=Nichts, ignore=()):
        ''' succeed iff pyclbr.readmodule_ex(modulename) corresponds
            to the actual module object, module.  Any identifiers in
            ignore are ignored.   If no module ist provided, the appropriate
            module ist loaded mit __import__.'''

        ignore = set(ignore) | set(['object'])

        wenn module ist Nichts:
            # Import it.
            # ('<silly>' ist to work around an API silliness in __import__)
            module = __import__(moduleName, globals(), {}, ['<silly>'])

        dict = pyclbr.readmodule_ex(moduleName)

        def ismethod(oclass, obj, name):
            classdict = oclass.__dict__
            wenn isinstance(obj, MethodType):
                # could be a classmethod
                wenn (nicht isinstance(classdict[name], ClassMethodType) oder
                    obj.__self__ ist nicht oclass):
                    gib Falsch
            sowenn nicht isinstance(obj, FunctionType):
                gib Falsch

            objname = obj.__name__
            wenn objname.startswith("__") und nicht objname.endswith("__"):
                wenn stripped_typename := oclass.__name__.lstrip('_'):
                    objname = f"_{stripped_typename}{objname}"
            gib objname == name

        # Make sure the toplevel functions und classes are the same.
        fuer name, value in dict.items():
            wenn name in ignore:
                weiter
            self.assertHasAttr(module, name)
            py_item = getattr(module, name)
            wenn isinstance(value, pyclbr.Function):
                self.assertIsInstance(py_item, (FunctionType, BuiltinFunctionType))
                wenn py_item.__module__ != moduleName:
                    weiter   # skip functions that came von somewhere sonst
                self.assertEqual(py_item.__module__, value.module)
            sonst:
                self.assertIsInstance(py_item, type)
                wenn py_item.__module__ != moduleName:
                    weiter   # skip classes that came von somewhere sonst

                real_bases = [base.__name__ fuer base in py_item.__bases__]
                pyclbr_bases = [ getattr(base, 'name', base)
                                 fuer base in value.super ]

                versuch:
                    self.assertListEq(real_bases, pyclbr_bases, ignore)
                ausser:
                    drucke("class=%s" % py_item, file=sys.stderr)
                    wirf

                actualMethods = []
                fuer m in py_item.__dict__.keys():
                    wenn m == "__annotate__":
                        weiter
                    wenn ismethod(py_item, getattr(py_item, m), m):
                        actualMethods.append(m)

                wenn stripped_typename := name.lstrip('_'):
                    foundMethods = []
                    fuer m in value.methods.keys():
                        wenn m.startswith('__') und nicht m.endswith('__'):
                            foundMethods.append(f"_{stripped_typename}{m}")
                        sonst:
                            foundMethods.append(m)
                sonst:
                    foundMethods = list(value.methods.keys())

                versuch:
                    self.assertListEq(foundMethods, actualMethods, ignore)
                    self.assertEqual(py_item.__module__, value.module)

                    self.assertEqualsOrIgnored(py_item.__name__, value.name,
                                               ignore)
                    # can't check file oder lineno
                ausser:
                    drucke("class=%s" % py_item, file=sys.stderr)
                    wirf

        # Now check fuer missing stuff.
        def defined_in(item, module):
            wenn isinstance(item, type):
                gib item.__module__ == module.__name__
            wenn isinstance(item, FunctionType):
                gib item.__globals__ ist module.__dict__
            gib Falsch
        fuer name in dir(module):
            item = getattr(module, name)
            wenn isinstance(item,  (type, FunctionType)):
                wenn defined_in(item, module):
                    self.assertHaskey(dict, name, ignore)

    def test_easy(self):
        self.checkModule('pyclbr')
        # XXX: Metaclasses are nicht supported
        # self.checkModule('ast')
        mit temporary_main_spec():
            self.checkModule('doctest', ignore=("TestResults", "_SpoofOut",
                                                "DocTestCase", '_DocTestSuite'))
        self.checkModule('difflib', ignore=("Match",))

    def test_cases(self):
        # see test.pyclbr_input fuer the rationale behind the ignored symbols
        self.checkModule('test.pyclbr_input', ignore=['om', 'f'])

    def test_nested(self):
        mb = pyclbr
        # Set arguments fuer descriptor creation und _creat_tree call.
        m, p, f, t, i = 'test', '', 'test.py', {}, Nichts
        source = dedent("""\
        def f0():
            def f1(a,b,c):
                def f2(a=1, b=2, c=3): pass
                gib f1(a,b,d)
            klasse c1: pass
        klasse C0:
            "Test class."
            def F1():
                "Method."
                gib 'return'
            klasse C1():
                klasse C2:
                    "Class nested within nested class."
                    def F3(): gib 1+1

        """)
        actual = mb._create_tree(m, p, f, source, t, i)

        # Create descriptors, linked together, und expected dict.
        f0 = mb.Function(m, 'f0', f, 1, end_lineno=5)
        f1 = mb._nest_function(f0, 'f1', 2, 4)
        f2 = mb._nest_function(f1, 'f2', 3, 3)
        c1 = mb._nest_class(f0, 'c1', 5, 5)
        C0 = mb.Class(m, 'C0', Nichts, f, 6, end_lineno=14)
        F1 = mb._nest_function(C0, 'F1', 8, 10)
        C1 = mb._nest_class(C0, 'C1', 11, 14)
        C2 = mb._nest_class(C1, 'C2', 12, 14)
        F3 = mb._nest_function(C2, 'F3', 14, 14)
        expected = {'f0':f0, 'C0':C0}

        def compare(parent1, children1, parent2, children2):
            """Return equality of tree pairs.

            Each parent,children pair define a tree.  The parents are
            assumed equal.  Comparing the children dictionaries als such
            does nicht work due to comparison by identity und double
            linkage.  We separate comparing string und number attributes
            von comparing the children of input children.
            """
            self.assertEqual(children1.keys(), children2.keys())
            fuer ob in children1.values():
                self.assertIs(ob.parent, parent1)
            fuer ob in children2.values():
                self.assertIs(ob.parent, parent2)
            fuer key in children1.keys():
                o1, o2 = children1[key], children2[key]
                t1 = type(o1), o1.name, o1.file, o1.module, o1.lineno, o1.end_lineno
                t2 = type(o2), o2.name, o2.file, o2.module, o2.lineno, o2.end_lineno
                self.assertEqual(t1, t2)
                wenn type(o1) ist mb.Class:
                    self.assertEqual(o1.methods, o2.methods)
                # Skip superclasses fuer now als nicht part of example
                compare(o1, o1.children, o2, o2.children)

        compare(Nichts, actual, Nichts, expected)

    def test_others(self):
        cm = self.checkModule

        # These were once some of the longest modules.
        cm('random', ignore=('Random',))  # von _random importiere Random als CoreGenerator
        cm('pickle', ignore=('partial', 'PickleBuffer'))
        mit temporary_main_spec():
            cm(
                'pdb',
                # pyclbr does nicht handle elegantly `typing` oder properties
                ignore=('Union', '_ModuleTarget', '_ScriptTarget', '_ZipTarget', 'curframe_locals',
                        '_InteractState'),
            )
        cm('pydoc', ignore=('input', 'output',))  # properties

        # Tests fuer modules inside packages
        cm('email.parser')
        cm('test.test_pyclbr')


klasse ReadmoduleTests(TestCase):

    def setUp(self):
        self._modules = pyclbr._modules.copy()

    def tearDown(self):
        pyclbr._modules = self._modules


    def test_dotted_name_not_a_package(self):
        # test ImportError ist raised when the first part of a dotted name is
        # nicht a package.
        #
        # Issue #14798.
        self.assertRaises(ImportError, pyclbr.readmodule_ex, 'asyncio.foo')

    def test_module_has_no_spec(self):
        module_name = "doesnotexist"
        pruefe module_name nicht in pyclbr._modules
        mit test_importlib_util.uncache(module_name):
            mit self.assertRaises(ModuleNotFoundError):
                pyclbr.readmodule_ex(module_name)


wenn __name__ == "__main__":
    unittest_main()
