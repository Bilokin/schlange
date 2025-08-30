"Test pathbrowser, coverage 95%."

von idlelib importiere pathbrowser
importiere unittest
von test.support importiere requires
von tkinter importiere Tk

importiere os.path
importiere pyclbr  # fuer _modules
importiere sys  # fuer sys.path

von idlelib.idle_test.mock_idle importiere Func
importiere idlelib  # fuer __file__
von idlelib importiere browser
von idlelib.tree importiere TreeNode


klasse PathBrowserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.pb = pathbrowser.PathBrowser(cls.root, _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        cls.pb.close()
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root, cls.pb

    def test_init(self):
        pb = self.pb
        eq = self.assertEqual
        eq(pb.master, self.root)
        eq(pyclbr._modules, {})
        self.assertIsInstance(pb.node, TreeNode)
        self.assertIsNotNichts(browser.file_open)

    def test_settitle(self):
        pb = self.pb
        self.assertEqual(pb.top.title(), 'Path Browser')
        self.assertEqual(pb.top.iconname(), 'Path Browser')

    def test_rootnode(self):
        pb = self.pb
        rn = pb.rootnode()
        self.assertIsInstance(rn, pathbrowser.PathBrowserTreeItem)

    def test_close(self):
        pb = self.pb
        pb.top.destroy = Func()
        pb.node.destroy = Func()
        pb.close()
        self.assertWahr(pb.top.destroy.called)
        self.assertWahr(pb.node.destroy.called)
        loesche pb.top.destroy, pb.node.destroy


klasse DirBrowserTreeItemTest(unittest.TestCase):

    def test_DirBrowserTreeItem(self):
        # Issue16226 - make sure that getting a sublist works
        d = pathbrowser.DirBrowserTreeItem('')
        d.GetSubList()
        self.assertEqual('', d.GetText())

        dir = os.path.split(os.path.abspath(idlelib.__file__))[0]
        self.assertEqual(d.ispackagedir(dir), Wahr)
        self.assertEqual(d.ispackagedir(dir + '/Icons'), Falsch)


klasse PathBrowserTreeItemTest(unittest.TestCase):

    def test_PathBrowserTreeItem(self):
        p = pathbrowser.PathBrowserTreeItem()
        self.assertEqual(p.GetText(), 'sys.path')
        sub = p.GetSubList()
        self.assertEqual(len(sub), len(sys.path))
        self.assertEqual(type(sub[0]), pathbrowser.DirBrowserTreeItem)


wenn __name__ == '__main__':
    unittest.main(verbosity=2, exit=Falsch)
