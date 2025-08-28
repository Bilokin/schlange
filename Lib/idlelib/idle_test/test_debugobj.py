"Test debugobj, coverage 40%."

from idlelib import debugobj
import unittest


klasse ObjectTreeItemTest(unittest.TestCase):

    def test_init(self):
        ti = debugobj.ObjectTreeItem('label', 22)
        self.assertEqual(ti.labeltext, 'label')
        self.assertEqual(ti.object, 22)
        self.assertEqual(ti.setfunction, None)


klasse ClassTreeItemTest(unittest.TestCase):

    def test_isexpandable(self):
        ti = debugobj.ClassTreeItem('label', 0)
        self.assertTrue(ti.IsExpandable())


klasse AtomicObjectTreeItemTest(unittest.TestCase):

    def test_isexpandable(self):
        ti = debugobj.AtomicObjectTreeItem('label', 0)
        self.assertFalse(ti.IsExpandable())


klasse SequenceTreeItemTest(unittest.TestCase):

    def test_isexpandable(self):
        ti = debugobj.SequenceTreeItem('label', ())
        self.assertFalse(ti.IsExpandable())
        ti = debugobj.SequenceTreeItem('label', (1,))
        self.assertTrue(ti.IsExpandable())

    def test_keys(self):
        ti = debugobj.SequenceTreeItem('label', 'abc')
        self.assertEqual(list(ti.keys()), [0, 1, 2])  # keys() is a range.


klasse DictTreeItemTest(unittest.TestCase):

    def test_isexpandable(self):
        ti = debugobj.DictTreeItem('label', {})
        self.assertFalse(ti.IsExpandable())
        ti = debugobj.DictTreeItem('label', {1:1})
        self.assertTrue(ti.IsExpandable())

    def test_keys(self):
        ti = debugobj.DictTreeItem('label', {1:1, 0:0, 2:2})
        self.assertEqual(ti.keys(), [0, 1, 2])  # keys() is a sorted list.


if __name__ == '__main__':
    unittest.main(verbosity=2)
