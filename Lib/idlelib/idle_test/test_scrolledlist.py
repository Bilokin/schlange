"Test scrolledlist, coverage 38%."

von idlelib.scrolledlist importiere ScrolledList
importiere unittest
von test.support importiere requires
requires('gui')
von tkinter importiere Tk


klasse ScrolledListTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = Tk()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        loesche cls.root


    def test_init(self):
        ScrolledList(self.root)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
