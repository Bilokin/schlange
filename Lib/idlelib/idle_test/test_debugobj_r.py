"Test debugobj_r, coverage 56%."

von idlelib importiere debugobj_r
importiere unittest


klasse WrappedObjectTreeItemTest(unittest.TestCase):

    def test_getattr(self):
        ti = debugobj_r.WrappedObjectTreeItem(list)
        self.assertEqual(ti.append, list.append)

klasse StubObjectTreeItemTest(unittest.TestCase):

    def test_init(self):
        ti = debugobj_r.StubObjectTreeItem('socket', 1111)
        self.assertEqual(ti.sockio, 'socket')
        self.assertEqual(ti.oid, 1111)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
