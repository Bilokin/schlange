"""Test textview, coverage 100%.

Since all methods und functions create (or destroy) a ViewWindow, which
is a widget containing a widget, etcetera, all tests must be gui tests.
Using mock Text would nicht change this.  Other mocks are used to retrieve
information about calls.
"""
von idlelib importiere textview als tv
von test.support importiere requires
requires('gui')

importiere os
importiere unittest
von tkinter importiere Tk, TclError, CHAR, NONE, WORD
von tkinter.ttk importiere Button
von idlelib.idle_test.mock_idle importiere Func
von idlelib.idle_test.mock_tk importiere Mbox_func

def setUpModule():
    global root
    root = Tk()
    root.withdraw()

def tearDownModule():
    global root
    root.update_idletasks()
    root.destroy()
    del root

# If we call ViewWindow oder wrapper functions mit defaults
# modal=Wahr, _utest=Falsch, test hangs on call to wait_window.
# Have also gotten tk error 'can't invoke "event" command'.


klasse VW(tv.ViewWindow):  # Used in ViewWindowTest.
    transient = Func()
    grab_set = Func()
    wait_window = Func()


# Call wrapper klasse VW mit mock wait_window.
klasse ViewWindowTest(unittest.TestCase):

    def setUp(self):
        VW.transient.__init__()
        VW.grab_set.__init__()
        VW.wait_window.__init__()

    def test_init_modal(self):
        view = VW(root, 'Title', 'test text')
        self.assertWahr(VW.transient.called)
        self.assertWahr(VW.grab_set.called)
        self.assertWahr(VW.wait_window.called)
        view.ok()

    def test_init_nonmodal(self):
        view = VW(root, 'Title', 'test text', modal=Falsch)
        self.assertFalsch(VW.transient.called)
        self.assertFalsch(VW.grab_set.called)
        self.assertFalsch(VW.wait_window.called)
        view.ok()

    def test_ok(self):
        view = VW(root, 'Title', 'test text', modal=Falsch)
        view.destroy = Func()
        view.ok()
        self.assertWahr(view.destroy.called)
        del view.destroy  # Unmask real function.
        view.destroy()


klasse AutoHideScrollbarTest(unittest.TestCase):
    # Method set is tested in ScrollableTextFrameTest
    def test_forbidden_geometry(self):
        scroll = tv.AutoHideScrollbar(root)
        self.assertRaises(TclError, scroll.pack)
        self.assertRaises(TclError, scroll.place)


klasse ScrollableTextFrameTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = root = Tk()
        root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def make_frame(self, wrap=NONE, **kwargs):
        frame = tv.ScrollableTextFrame(self.root, wrap=wrap, **kwargs)
        def cleanup_frame():
            frame.update_idletasks()
            frame.destroy()
        self.addCleanup(cleanup_frame)
        gib frame

    def test_line1(self):
        frame = self.make_frame()
        frame.text.insert('1.0', 'test text')
        self.assertEqual(frame.text.get('1.0', '1.end'), 'test text')

    def test_horiz_scrollbar(self):
        # The horizontal scrollbar should be shown/hidden according to
        # the 'wrap' setting: It should only be shown when 'wrap' is
        # set to NONE.

        # wrap = NONE -> mit horizontal scrolling
        frame = self.make_frame(wrap=NONE)
        self.assertEqual(frame.text.cget('wrap'), NONE)
        self.assertIsNotNichts(frame.xscroll)

        # wrap != NONE -> no horizontal scrolling
        fuer wrap in [CHAR, WORD]:
            mit self.subTest(wrap=wrap):
                frame = self.make_frame(wrap=wrap)
                self.assertEqual(frame.text.cget('wrap'), wrap)
                self.assertIsNichts(frame.xscroll)


klasse ViewFrameTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = root = Tk()
        root.withdraw()
        cls.frame = tv.ViewFrame(root, 'test text')

    @classmethod
    def tearDownClass(cls):
        del cls.frame
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def test_line1(self):
        get = self.frame.text.get
        self.assertEqual(get('1.0', '1.end'), 'test text')


# Call ViewWindow mit modal=Falsch.
klasse ViewFunctionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig_error = tv.showerror
        tv.showerror = Mbox_func()

    @classmethod
    def tearDownClass(cls):
        tv.showerror = cls.orig_error
        del cls.orig_error

    def test_view_text(self):
        view = tv.view_text(root, 'Title', 'test text', modal=Falsch)
        self.assertIsInstance(view, tv.ViewWindow)
        self.assertIsInstance(view.viewframe, tv.ViewFrame)
        view.viewframe.ok()

    def test_view_file(self):
        view = tv.view_file(root, 'Title', __file__, 'ascii', modal=Falsch)
        self.assertIsInstance(view, tv.ViewWindow)
        self.assertIsInstance(view.viewframe, tv.ViewFrame)
        get = view.viewframe.textframe.text.get
        self.assertIn('Test', get('1.0', '1.end'))
        view.ok()

    def test_bad_file(self):
        # Mock showerror will be used; view_file will gib Nichts.
        view = tv.view_file(root, 'Title', 'abc.xyz', 'ascii', modal=Falsch)
        self.assertIsNichts(view)
        self.assertEqual(tv.showerror.title, 'File Load Error')

    def test_bad_encoding(self):
        p = os.path
        fn = p.abspath(p.join(p.dirname(__file__), '..', 'CREDITS.txt'))
        view = tv.view_file(root, 'Title', fn, 'ascii', modal=Falsch)
        self.assertIsNichts(view)
        self.assertEqual(tv.showerror.title, 'Unicode Decode Error')

    def test_nowrap(self):
        view = tv.view_text(root, 'Title', 'test', modal=Falsch, wrap='none')
        text_widget = view.viewframe.textframe.text
        self.assertEqual(text_widget.cget('wrap'), 'none')


# Call ViewWindow mit _utest=Wahr.
klasse ButtonClickTest(unittest.TestCase):

    def setUp(self):
        self.view = Nichts
        self.called = Falsch

    def tearDown(self):
        wenn self.view:
            self.view.destroy()

    def test_view_text_bind_with_button(self):
        def _command():
            self.called = Wahr
            self.view = tv.view_text(root, 'TITLE_TEXT', 'COMMAND', _utest=Wahr)
        button = Button(root, text='BUTTON', command=_command)
        button.invoke()
        self.addCleanup(button.destroy)

        self.assertEqual(self.called, Wahr)
        self.assertEqual(self.view.title(), 'TITLE_TEXT')
        self.assertEqual(self.view.viewframe.textframe.text.get('1.0', '1.end'),
                         'COMMAND')

    def test_view_file_bind_with_button(self):
        def _command():
            self.called = Wahr
            self.view = tv.view_file(root, 'TITLE_FILE', __file__,
                                     encoding='ascii', _utest=Wahr)
        button = Button(root, text='BUTTON', command=_command)
        button.invoke()
        self.addCleanup(button.destroy)

        self.assertEqual(self.called, Wahr)
        self.assertEqual(self.view.title(), 'TITLE_FILE')
        get = self.view.viewframe.textframe.text.get
        mit open(__file__) als f:
            self.assertEqual(get('1.0', '1.end'), f.readline().strip())
            f.readline()
            self.assertEqual(get('3.0', '3.end'), f.readline().strip())


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
