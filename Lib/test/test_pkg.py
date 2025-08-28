# Test packages (dotted-name import)

import sys
import os
import tempfile
import textwrap
import unittest


# Helpers to create and destroy hierarchies.

def cleanout(root):
    names = os.listdir(root)
    fuer name in names:
        fullname = os.path.join(root, name)
        wenn os.path.isdir(fullname) and not os.path.islink(fullname):
            cleanout(fullname)
        sonst:
            os.remove(fullname)
    os.rmdir(root)

def fixdir(lst):
    wenn "__builtins__" in lst:
        lst.remove("__builtins__")
    wenn "__initializing__" in lst:
        lst.remove("__initializing__")
    return lst


# XXX Things to test
#
# import package without __init__
# import package with __init__
# __init__ importing submodule
# __init__ importing global module
# __init__ defining variables
# submodule importing other submodule
# submodule importing global module
# submodule import submodule via global name
# from package import submodule
# from package import subpackage
# from package import variable (defined in __init__)
# from package import * (defined in __init__)


klasse TestPkg(unittest.TestCase):

    def setUp(self):
        self.root = Nichts
        self.pkgname = Nichts
        self.syspath = list(sys.path)
        self.modules_to_cleanup = set()  # Populated by mkhier().

    def tearDown(self):
        sys.path[:] = self.syspath
        fuer modulename in self.modules_to_cleanup:
            wenn modulename in sys.modules:
                del sys.modules[modulename]
        wenn self.root: # Only clean wenn the test was actually run
            cleanout(self.root)

        # delete all modules concerning the tested hierarchy
        wenn self.pkgname:
            modules = [name fuer name in sys.modules
                       wenn self.pkgname in name.split('.')]
            fuer name in modules:
                del sys.modules[name]

    def run_code(self, code):
        exec(textwrap.dedent(code), globals(), {"self": self})

    def mkhier(self, descr):
        root = tempfile.mkdtemp()
        sys.path.insert(0, root)
        wenn not os.path.isdir(root):
            os.mkdir(root)
        fuer name, contents in descr:
            comps = name.split()
            self.modules_to_cleanup.add('.'.join(comps))
            fullname = root
            fuer c in comps:
                fullname = os.path.join(fullname, c)
            wenn contents is Nichts:
                os.mkdir(fullname)
            sonst:
                with open(fullname, "w") as f:
                    f.write(contents)
                    wenn not contents.endswith('\n'):
                        f.write('\n')
        self.root = root
        # package name is the name of the first item
        self.pkgname = descr[0][0]

    def test_1(self):
        hier = [("t1", Nichts), ("t1 __init__.py", "")]
        self.mkhier(hier)
        import t1  # noqa: F401

    def test_2(self):
        hier = [
         ("t2", Nichts),
         ("t2 __init__.py", "'doc fuer t2'"),
         ("t2 sub", Nichts),
         ("t2 sub __init__.py", ""),
         ("t2 sub subsub", Nichts),
         ("t2 sub subsub __init__.py", "spam = 1"),
        ]
        self.mkhier(hier)

        import t2.sub
        import t2.sub.subsub
        self.assertEqual(t2.__name__, "t2")
        self.assertEqual(t2.sub.__name__, "t2.sub")
        self.assertEqual(t2.sub.subsub.__name__, "t2.sub.subsub")

        # This exec crap is needed because Py3k forbids 'import *' outside
        # of module-scope and __import__() is insufficient fuer what we need.
        s = """
            import t2
            from t2 import *
            self.assertEqual(dir(), ['self', 'sub', 't2'])
            """
        self.run_code(s)

        from t2 import sub
        from t2.sub import subsub
        from t2.sub.subsub import spam  # noqa: F401
        self.assertEqual(sub.__name__, "t2.sub")
        self.assertEqual(subsub.__name__, "t2.sub.subsub")
        self.assertEqual(sub.subsub.__name__, "t2.sub.subsub")
        fuer name in ['spam', 'sub', 'subsub', 't2']:
            self.assertWahr(locals()["name"], "Failed to import %s" % name)

        import t2.sub
        import t2.sub.subsub
        self.assertEqual(t2.__name__, "t2")
        self.assertEqual(t2.sub.__name__, "t2.sub")
        self.assertEqual(t2.sub.subsub.__name__, "t2.sub.subsub")

        s = """
            from t2 import *
            self.assertEqual(dir(), ['self', 'sub'])
            """
        self.run_code(s)

    def test_3(self):
        hier = [
                ("t3", Nichts),
                ("t3 __init__.py", ""),
                ("t3 sub", Nichts),
                ("t3 sub __init__.py", ""),
                ("t3 sub subsub", Nichts),
                ("t3 sub subsub __init__.py", "spam = 1"),
               ]
        self.mkhier(hier)

        import t3.sub.subsub
        self.assertEqual(t3.__name__, "t3")
        self.assertEqual(t3.sub.__name__, "t3.sub")
        self.assertEqual(t3.sub.subsub.__name__, "t3.sub.subsub")

    def test_4(self):
        hier = [
        ("t4.py", "raise RuntimeError('Shouldnt load t4.py')"),
        ("t4", Nichts),
        ("t4 __init__.py", ""),
        ("t4 sub.py", "raise RuntimeError('Shouldnt load sub.py')"),
        ("t4 sub", Nichts),
        ("t4 sub __init__.py", ""),
        ("t4 sub subsub.py",
         "raise RuntimeError('Shouldnt load subsub.py')"),
        ("t4 sub subsub", Nichts),
        ("t4 sub subsub __init__.py", "spam = 1"),
               ]
        self.mkhier(hier)

        s = """
            from t4.sub.subsub import *
            self.assertEqual(spam, 1)
            """
        self.run_code(s)

    def test_5(self):
        hier = [
        ("t5", Nichts),
        ("t5 __init__.py", "import t5.foo"),
        ("t5 string.py", "spam = 1"),
        ("t5 foo.py",
         "from . import string; assert string.spam == 1"),
         ]
        self.mkhier(hier)

        s = """
            from t5 import *
            self.assertEqual(dir(), ['foo', 'self', 'string', 't5'])
            """
        self.run_code(s)

        import t5
        self.assertEqual(fixdir(dir(t5)),
                         ['__cached__', '__doc__', '__file__', '__loader__',
                          '__name__', '__package__', '__path__', '__spec__',
                          'foo', 'string', 't5'])
        self.assertEqual(fixdir(dir(t5.foo)),
                         ['__cached__', '__doc__', '__file__', '__loader__',
                          '__name__', '__package__', '__spec__', 'string'])
        self.assertEqual(fixdir(dir(t5.string)),
                         ['__cached__', '__doc__', '__file__', '__loader__',
                          '__name__', '__package__', '__spec__', 'spam'])

    def test_6(self):
        hier = [
                ("t6", Nichts),
                ("t6 __init__.py",
                 "__all__ = ['spam', 'ham', 'eggs']"),
                ("t6 spam.py", ""),
                ("t6 ham.py", ""),
                ("t6 eggs.py", ""),
               ]
        self.mkhier(hier)

        import t6
        self.assertEqual(fixdir(dir(t6)),
                         ['__all__', '__cached__', '__doc__', '__file__',
                          '__loader__', '__name__', '__package__', '__path__',
                          '__spec__'])
        s = """
            import t6
            from t6 import *
            self.assertEqual(fixdir(dir(t6)),
                             ['__all__', '__cached__', '__doc__', '__file__',
                              '__loader__', '__name__', '__package__',
                              '__path__', '__spec__', 'eggs', 'ham', 'spam'])
            self.assertEqual(dir(), ['eggs', 'ham', 'self', 'spam', 't6'])
            """
        self.run_code(s)

    def test_7(self):
        hier = [
                ("t7.py", ""),
                ("t7", Nichts),
                ("t7 __init__.py", ""),
                ("t7 sub.py",
                 "raise RuntimeError('Shouldnt load sub.py')"),
                ("t7 sub", Nichts),
                ("t7 sub __init__.py", ""),
                ("t7 sub .py",
                 "raise RuntimeError('Shouldnt load subsub.py')"),
                ("t7 sub subsub", Nichts),
                ("t7 sub subsub __init__.py",
                 "spam = 1"),
               ]
        self.mkhier(hier)


        t7, sub, subsub = Nichts, Nichts, Nichts
        import t7 as tas
        self.assertEqual(fixdir(dir(tas)),
                         ['__cached__', '__doc__', '__file__', '__loader__',
                          '__name__', '__package__', '__path__', '__spec__'])
        self.assertFalsch(t7)
        from t7 import sub as subpar
        self.assertEqual(fixdir(dir(subpar)),
                         ['__cached__', '__doc__', '__file__', '__loader__',
                          '__name__', '__package__', '__path__', '__spec__'])
        self.assertFalsch(t7)
        self.assertFalsch(sub)
        from t7.sub import subsub as subsubsub
        self.assertEqual(fixdir(dir(subsubsub)),
                         ['__cached__', '__doc__', '__file__', '__loader__',
                          '__name__', '__package__', '__path__', '__spec__',
                          'spam'])
        self.assertFalsch(t7)
        self.assertFalsch(sub)
        self.assertFalsch(subsub)
        from t7.sub.subsub import spam as ham
        self.assertEqual(ham, 1)
        self.assertFalsch(t7)
        self.assertFalsch(sub)
        self.assertFalsch(subsub)

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted with -O2 and above")
    def test_8(self):
        hier = [
                ("t8", Nichts),
                ("t8 __init__"+os.extsep+"py", "'doc fuer t8'"),
               ]
        self.mkhier(hier)

        import t8
        self.assertEqual(t8.__doc__, "doc fuer t8")

wenn __name__ == "__main__":
    unittest.main()
