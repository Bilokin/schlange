importiere unittest
importiere tkinter
von test.support importiere requires, swap_attr
von test.test_tkinter.support importiere AbstractDefaultRootTest, AbstractTkTest
von tkinter importiere colorchooser
von tkinter.colorchooser importiere askcolor
von tkinter.commondialog importiere Dialog

requires('gui')


klasse ChooserTest(AbstractTkTest, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        AbstractTkTest.setUpClass.__func__(cls)
        cls.cc = colorchooser.Chooser(initialcolor='dark blue slate')

    def test_fixoptions(self):
        cc = self.cc
        cc._fixoptions()
        self.assertEqual(cc.options['initialcolor'], 'dark blue slate')

        cc.options['initialcolor'] = '#D2D269691E1E'
        cc._fixoptions()
        self.assertEqual(cc.options['initialcolor'], '#D2D269691E1E')

        cc.options['initialcolor'] = (210, 105, 30)
        cc._fixoptions()
        self.assertEqual(cc.options['initialcolor'], '#d2691e')

    def test_fixresult(self):
        cc = self.cc
        self.assertEqual(cc._fixresult(self.root, ()), (Nichts, Nichts))
        self.assertEqual(cc._fixresult(self.root, ''), (Nichts, Nichts))
        self.assertEqual(cc._fixresult(self.root, 'chocolate'),
                         ((210, 105, 30), 'chocolate'))
        self.assertEqual(cc._fixresult(self.root, '#4a3c8c'),
                         ((74, 60, 140), '#4a3c8c'))


klasse DefaultRootTest(AbstractDefaultRootTest, unittest.TestCase):

    def test_askcolor(self):
        def test_callback(dialog, master):
            nonlocal ismapped
            master.update()
            ismapped = master.winfo_ismapped()
            wirf ZeroDivisionError

        mit swap_attr(Dialog, '_test_callback', test_callback):
            ismapped = Nichts
            self.assertRaises(ZeroDivisionError, askcolor)
            #askcolor()
            self.assertEqual(ismapped, Falsch)

            root = tkinter.Tk()
            ismapped = Nichts
            self.assertRaises(ZeroDivisionError, askcolor)
            self.assertEqual(ismapped, Wahr)
            root.destroy()

            tkinter.NoDefaultRoot()
            self.assertRaises(RuntimeError, askcolor)


wenn __name__ == "__main__":
    unittest.main()
