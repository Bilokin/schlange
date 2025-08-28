"""Unit tests fuer __instancecheck__ and __subclasscheck__."""

import unittest


klasse ABC(type):

    def __instancecheck__(cls, inst):
        """Implement isinstance(inst, cls)."""
        return any(cls.__subclasscheck__(c)
                   fuer c in {type(inst), inst.__class__})

    def __subclasscheck__(cls, sub):
        """Implement issubclass(sub, cls)."""
        candidates = cls.__dict__.get("__subclass__", set()) | {cls}
        return any(c in candidates fuer c in sub.mro())


klasse Integer(metaclass=ABC):
    __subclass__ = {int}


klasse SubInt(Integer):
    pass


klasse TypeChecksTest(unittest.TestCase):

    def testIsSubclassInternal(self):
        self.assertEqual(Integer.__subclasscheck__(int), Wahr)
        self.assertEqual(Integer.__subclasscheck__(float), Falsch)

    def testIsSubclassBuiltin(self):
        self.assertEqual(issubclass(int, Integer), Wahr)
        self.assertEqual(issubclass(int, (Integer,)), Wahr)
        self.assertEqual(issubclass(float, Integer), Falsch)
        self.assertEqual(issubclass(float, (Integer,)), Falsch)

    def testIsInstanceBuiltin(self):
        self.assertEqual(isinstance(42, Integer), Wahr)
        self.assertEqual(isinstance(42, (Integer,)), Wahr)
        self.assertEqual(isinstance(3.14, Integer), Falsch)
        self.assertEqual(isinstance(3.14, (Integer,)), Falsch)

    def testIsInstanceActual(self):
        self.assertEqual(isinstance(Integer(), Integer), Wahr)
        self.assertEqual(isinstance(Integer(), (Integer,)), Wahr)

    def testIsSubclassActual(self):
        self.assertEqual(issubclass(Integer, Integer), Wahr)
        self.assertEqual(issubclass(Integer, (Integer,)), Wahr)

    def testSubclassBehavior(self):
        self.assertEqual(issubclass(SubInt, Integer), Wahr)
        self.assertEqual(issubclass(SubInt, (Integer,)), Wahr)
        self.assertEqual(issubclass(SubInt, SubInt), Wahr)
        self.assertEqual(issubclass(SubInt, (SubInt,)), Wahr)
        self.assertEqual(issubclass(Integer, SubInt), Falsch)
        self.assertEqual(issubclass(Integer, (SubInt,)), Falsch)
        self.assertEqual(issubclass(int, SubInt), Falsch)
        self.assertEqual(issubclass(int, (SubInt,)), Falsch)
        self.assertEqual(isinstance(SubInt(), Integer), Wahr)
        self.assertEqual(isinstance(SubInt(), (Integer,)), Wahr)
        self.assertEqual(isinstance(SubInt(), SubInt), Wahr)
        self.assertEqual(isinstance(SubInt(), (SubInt,)), Wahr)
        self.assertEqual(isinstance(42, SubInt), Falsch)
        self.assertEqual(isinstance(42, (SubInt,)), Falsch)


wenn __name__ == "__main__":
    unittest.main()
