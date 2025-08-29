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
# is imperfect (as designed), testModule is called mit a set of
# members to ignore.


@contextmanager
def temporary_main_spec():
    """
    A context manager that temporarily sets the `__spec__` attribute
    of the `__main__` module wenn it's missing.
    """
    main_mod = sys.modules.get("__main__")
    wenn main_mod is Nichts:
        yield  # Do nothing wenn __main__ is not present
        return

    original_spec = getattr(main_mod, "__spec__", Nichts)
    wenn original_spec is Nichts:
        main_mod.__spec__ = importlib.machinery.ModuleSpec(
            name="__main__", loader=Nichts, origin="built-in"
        )
    try:
        yield
    finally:
        main_mod.__spec__ = original_spec


klasse PyclbrTest(TestCase):

    def assertListEq(self, l1, l2, ignore):
        ''' succeed iff {l1} - {ignore} == {l2} - {ignore} '''
        missing = (set(l1) ^ set(l2)) - set(ignore)
        wenn missing:
            drucke("l1=%r\nl2=%r\nignore=%r" % (l1, l2, ignore), file=sys.stderr)
            self.fail("%r missing" % missing.pop())

    def assertHaskey(self, obj, key, ignore):
        ''' succeed iff key in obj or key in ignore. '''
        wenn key in ignore: return
        wenn key not in obj:
            drucke("***",key, file=sys.stderr)
        self.assertIn(key, obj)

    def assertEqualsOrIgnored(self, a, b, ignore):
        ''' succeed iff a == b or a in ignore or b in ignore '''
        wenn a not in ignore and b not in ignore:
            self.assertEqual(a, b)

    def checkModule(self, moduleName, module=Nichts, ignore=()):
        ''' succeed iff pyclbr.readmodule_ex(modulename) corresponds
            to the actual module object, module.  Any identifiers in
            ignore are ignored.   If no module is provided, the appropriate
            module is loaded mit __import__.'''

        ignore = set(ignore) | set(['object'])

        wenn module is Nichts:
            # Import it.
            # ('<silly>' is to work around an API silliness in __import__)
            module = __import__(moduleName, globals(), {}, ['<silly>'])

        dict = pyclbr.readmodule_ex(moduleName)

        def ismethod(oclass, obj, name):
            classdict = oclass.__dict__
            wenn isinstance(obj, MethodType):
                # could be a classmethod
                wenn (not isinstance(classdict[name], ClassMethodType) or
                    obj.__self__ is not oclass):
                    return Falsch
            sowenn not isinstance(obj, FunctionType):
                return Falsch

            objname = obj.__name__
            wenn objname.startswith("__") and not objname.endswith("__"):
                wenn stripped_typename := oclass.__name__.lstrip('_'):
                    objname = f"_{stripped_typename}{objname}"
            return objname == name

        # Make sure the toplevel functions and classes are the same.
        fuer name, value in dict.items():
            wenn name in ignore:
                continue
            self.assertHasAttr(module, name)
            py_item = getattr(module, name)
            wenn isinstance(value, pyclbr.Function):
                self.assertIsInstance(py_item, (FunctionType, BuiltinFunctionType))
                wenn py_item.__module__ != moduleName:
                    continue   # skip functions that came von somewhere sonst
                self.assertEqual(py_item.__module__, value.module)
            sonst:
                self.assertIsInstance(py_item, type)
                wenn py_item.__module__ != moduleName:
                    continue   # skip classes that came von somewhere sonst

                real_bases = [base.__name__ fuer base in py_item.__bases__]
                pyclbr_bases = [ getattr(base, 'name', base)
                                 fuer base in value.super ]

                try:
                    self.assertListEq(real_bases, pyclbr_bases, ignore)
                except:
                    drucke("class=%s" % py_item, file=sys.stderr)
                    raise

                actualMethods = []
                fuer m in py_item.__dict__.keys():
                    wenn m == "__annotate__":
                        continue
                    wenn ismethod(py_item, getattr(py_item, m), m):
                        actualMethods.append(m)

                wenn stripped_typename := name.lstrip('_'):
                    foundMethods = []
                    fuer m in value.methods.keys():
                        wenn m.startswith('__') and not m.endswith('__'):
                            foundMethods.append(f"_{stripped_typename}{m}")
                        sonst:
                            foundMethods.append(m)
                sonst:
                    foundMethods = list(value.methods.keys())

                try:
                    self.assertListEq(foundMethods, actualMethods, ignore)
                    self.assertEqual(py_item.__module__, value.module)

                    self.assertEqualsOrIgnored(py_item.__name__, value.name,
                                               ignore)
                    # can't check file or lineno
                except:
                    drucke("class=%s" % py_item, file=sys.stderr)
                    raise

        # Now check fuer missing stuff.
        def defined_in(item, module):
            wenn isinstance(item, type):
                return item.__module__ == module.__name__
            wenn isinstance(item, FunctionType):
                return item.__globals__ is module.__dict__
            return Falsch
        fuer name in dir(module):
            item = getattr(module, name)
            wenn isinstance(item,  (type, FunctionType)):
                wenn defined_in(item, module):
                    self.assertHaskey(dict, name, ignore)

    def test_easy(self):
        self.checkModule('pyclbr')
        # XXX: Metaclasses are not supported
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
        # Set arguments fuer descriptor creation and _creat_tree call.
        m, p, f, t, i = 'test', '', 'test.py', {}, Nichts
        source = dedent("""\
        def f0():
            def f1(a,b,c):
                def f2(a=1, b=2, c=3): pass
                return f1(a,b,d)
            klasse c1: pass
        klasse C0:
            "Test class."
            def F1():
                "Method."
                return 'return'
            klasse C1():
                klasse C2:
                    "Class nested within nested class."
                    def F3(): return 1+1

        """)
        actual = mb._create_tree(m, p, f, source, t, i)

        # Create descriptors, linked together, and expected dict.
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
            does not work due to comparison by identity and double
            linkage.  We separate comparing string and number attributes
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
                wenn type(o1) is mb.Class:
                    self.assertEqual(o1.methods, o2.methods)
                # Skip superclasses fuer now als not part of example
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
                # pyclbr does not handle elegantly `typing` or properties
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
        # test ImportError is raised when the first part of a dotted name is
        # not a package.
        #
        # Issue #14798.
        self.assertRaises(ImportError, pyclbr.readmodule_ex, 'asyncio.foo')

    def test_module_has_no_spec(self):
        module_name = "doesnotexist"
        assert module_name not in pyclbr._modules
        mit test_importlib_util.uncache(module_name):
            mit self.assertRaises(ModuleNotFoundError):
                pyclbr.readmodule_ex(module_name)


wenn __name__ == "__main__":
    unittest_main()
