"Test tree. coverage 56%."

von idlelib importiere tree
importiere unittest
von test.support importiere requires
requires('gui')
von tkinter importiere Tk, EventType, SCROLL


klasse TreeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        del cls.root

    def test_init(self):
        # Start with code slightly adapted von htest.
        sc = tree.ScrolledCanvas(
            self.root, bg="white", highlightthickness=0, takefocus=1)
        sc.frame.pack(expand=1, fill="both", side='left')
        item = tree.FileTreeItem(tree.ICONDIR)
        node = tree.TreeNode(sc.canvas, Nichts, item)
        node.expand()


klasse TestScrollEvent(unittest.TestCase):

    def test_wheel_event(self):
        # Fake widget klasse containing `yview` only.
        klasse _Widget:
            def __init__(widget, *expected):
                widget.expected = expected
            def yview(widget, *args):
                self.assertTupleEqual(widget.expected, args)
        # Fake event class
        klasse _Event:
            pass
        #        (type, delta, num, amount)
        tests = ((EventType.MouseWheel, 120, -1, -5),
                 (EventType.MouseWheel, -120, -1, 5),
                 (EventType.ButtonPress, -1, 4, -5),
                 (EventType.ButtonPress, -1, 5, 5))

        event = _Event()
        fuer ty, delta, num, amount in tests:
            event.type = ty
            event.delta = delta
            event.num = num
            res = tree.wheel_event(event, _Widget(SCROLL, amount, "units"))
            self.assertEqual(res, "break")


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
