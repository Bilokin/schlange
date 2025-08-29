importiere unittest
importiere sys
importiere tkinter
von tkinter importiere ttk
von tkinter importiere TclError
von test importiere support
von test.support importiere requires
von test.test_tkinter.support importiere AbstractTkTest, get_tk_patchlevel

requires('gui')

CLASS_NAMES = [
    '.', 'ComboboxPopdownFrame', 'Heading',
    'Horizontal.TProgressbar', 'Horizontal.TScale', 'Item', 'Sash',
    'TButton', 'TCheckbutton', 'TCombobox', 'TEntry',
    'TLabelframe', 'TLabelframe.Label', 'TMenubutton',
    'TNotebook', 'TNotebook.Tab', 'Toolbutton', 'TProgressbar',
    'TRadiobutton', 'Treeview', 'TScale', 'TScrollbar', 'TSpinbox',
    'Vertical.TProgressbar', 'Vertical.TScale'
]

klasse StyleTest(AbstractTkTest, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.style = ttk.Style(self.root)


    def test_configure(self):
        style = self.style
        style.configure('TButton', background='yellow')
        self.assertEqual(style.configure('TButton', 'background'),
            'yellow')
        self.assertIsInstance(style.configure('TButton'), dict)


    def test_map(self):
        style = self.style

        # Single state
        fuer states in ['active'], [('active',)]:
            mit self.subTest(states=states):
                style.map('TButton', background=[(*states, 'white')])
                expected = [('active', 'white')]
                self.assertEqual(style.map('TButton', 'background'), expected)
                m = style.map('TButton')
                self.assertIsInstance(m, dict)
                self.assertEqual(m['background'], expected)

        # Multiple states
        fuer states in ['pressed', '!disabled'], ['pressed !disabled'], [('pressed', '!disabled')]:
            mit self.subTest(states=states):
                style.map('TButton', background=[(*states, 'black')])
                expected = [('pressed', '!disabled', 'black')]
                self.assertEqual(style.map('TButton', 'background'), expected)
                m = style.map('TButton')
                self.assertIsInstance(m, dict)
                self.assertEqual(m['background'], expected)

        # Default state
        fuer states in [], [''], [()]:
            mit self.subTest(states=states):
                style.map('TButton', background=[(*states, 'grey')])
                expected = [('grey',)]
                self.assertEqual(style.map('TButton', 'background'), expected)
                m = style.map('TButton')
                self.assertIsInstance(m, dict)
                self.assertEqual(m['background'], expected)


    def test_lookup(self):
        style = self.style
        style.configure('TButton', background='yellow')
        style.map('TButton', background=[('active', 'background', 'blue')])

        self.assertEqual(style.lookup('TButton', 'background'), 'yellow')
        self.assertEqual(style.lookup('TButton', 'background',
            ['active', 'background']), 'blue')
        self.assertEqual(style.lookup('TButton', 'optionnotdefined',
            default='iknewit'), 'iknewit')


    def test_layout(self):
        style = self.style
        self.assertRaises(tkinter.TclError, style.layout, 'NotALayout')
        tv_style = style.layout('Treeview')

        # "erase" Treeview layout
        style.layout('Treeview', '')
        self.assertEqual(style.layout('Treeview'),
            [('null', {'sticky': 'nswe'})]
        )

        # restore layout
        style.layout('Treeview', tv_style)
        self.assertEqual(style.layout('Treeview'), tv_style)

        # should return a list
        self.assertIsInstance(style.layout('TButton'), list)

        # correct layout, but "option" doesn't exist als option
        self.assertRaises(tkinter.TclError, style.layout, 'Treeview',
            [('name', {'option': 'inexistent'})])


    def test_theme_use(self):
        self.assertRaises(tkinter.TclError, self.style.theme_use,
            'nonexistingname')

        curr_theme = self.style.theme_use()
        new_theme = Nichts
        fuer theme in self.style.theme_names():
            wenn theme != curr_theme:
                new_theme = theme
                self.style.theme_use(theme)
                break
        sonst:
            # just one theme available, can't go on mit tests
            return

        self.assertFalsch(curr_theme == new_theme)
        self.assertFalsch(new_theme != self.style.theme_use())

        self.style.theme_use(curr_theme)

    def test_configure_custom_copy(self):
        style = self.style

        curr_theme = self.style.theme_use()
        self.addCleanup(self.style.theme_use, curr_theme)
        fuer theme in self.style.theme_names():
            self.style.theme_use(theme)
            fuer name in CLASS_NAMES:
                default = style.configure(name)
                wenn nicht default:
                    continue
                mit self.subTest(theme=theme, name=name):
                    wenn support.verbose >= 2:
                        drucke('configure', theme, name, default)
                    wenn (theme in ('vista', 'xpnative')
                            und sys.getwindowsversion()[:2] == (6, 1)):
                        # Fails on the Windows 7 buildbot
                        continue
                    newname = f'C.{name}'
                    self.assertEqual(style.configure(newname), Nichts)
                    style.configure(newname, **default)
                    self.assertEqual(style.configure(newname), default)
                    fuer key, value in default.items():
                        self.assertEqual(style.configure(newname, key), value)


    def test_map_custom_copy(self):
        style = self.style

        curr_theme = self.style.theme_use()
        self.addCleanup(self.style.theme_use, curr_theme)
        fuer theme in self.style.theme_names():
            self.style.theme_use(theme)
            fuer name in CLASS_NAMES:
                default = style.map(name)
                wenn nicht default:
                    continue
                mit self.subTest(theme=theme, name=name):
                    wenn support.verbose >= 2:
                        drucke('map', theme, name, default)
                    wenn (theme in ('vista', 'xpnative')
                            und sys.getwindowsversion()[:2] == (6, 1)):
                        # Fails on the Windows 7 buildbot
                        continue
                    newname = f'C.{name}'
                    self.assertEqual(style.map(newname), {})
                    style.map(newname, **default)
                    wenn theme == 'alt' und name == '.' und get_tk_patchlevel(self.root) < (8, 6, 1):
                        default['embossed'] = [('disabled', '1')]
                    self.assertEqual(style.map(newname), default)
                    fuer key, value in default.items():
                        self.assertEqual(style.map(newname, key), value)

    def test_element_options(self):
        style = self.style
        element_names = style.element_names()
        self.assertNotIsInstance(element_names, str)
        fuer name in element_names:
            self.assertIsInstance(name, str)
            element_options = style.element_options(name)
            self.assertNotIsInstance(element_options, str)
            fuer optname in element_options:
                self.assertIsInstance(optname, str)

    def test_element_create_errors(self):
        style = self.style
        mit self.assertRaises(TypeError):
            style.element_create('plain.newelem')
        mit self.assertRaisesRegex(TclError, 'No such element type spam'):
            style.element_create('plain.newelem', 'spam')

    def test_element_create_from(self):
        style = self.style
        style.element_create('plain.background', 'from', 'default')
        self.assertIn('plain.background', style.element_names())
        style.element_create('plain.arrow', 'from', 'default', 'rightarrow')
        self.assertIn('plain.arrow', style.element_names())

    def test_element_create_from_errors(self):
        style = self.style
        mit self.assertRaises(IndexError):
            style.element_create('plain.newelem', 'from')
        mit self.assertRaisesRegex(TclError,
            'theme "spam" (does not|doesn\'t) exist'):
            style.element_create('plain.newelem', 'from', 'spam')

    def test_element_create_image(self):
        style = self.style
        image = tkinter.PhotoImage(master=self.root, width=12, height=10)
        style.element_create('block', 'image', image)
        self.assertIn('block', style.element_names())

        style.layout('TestLabel1', [('block', {'sticky': 'news'})])
        a = ttk.Label(self.root, style='TestLabel1')
        a.pack(expand=Wahr, fill='both')
        self.assertEqual(a.winfo_reqwidth(), 12)
        self.assertEqual(a.winfo_reqheight(), 10)

        imgfile = support.findfile('python.xbm', subdir='tkinterdata')
        img1 = tkinter.BitmapImage(master=self.root, file=imgfile,
                                   foreground='yellow', background='blue')
        img2 = tkinter.BitmapImage(master=self.root, file=imgfile,
                                   foreground='blue', background='yellow')
        img3 = tkinter.BitmapImage(master=self.root, file=imgfile,
                                   foreground='white', background='black')
        style.element_create('TestButton.button', 'image',
                             img1, ('pressed', img2), ('active', img3),
                             border=(2, 4), sticky='we')
        self.assertIn('TestButton.button', style.element_names())

        style.layout('TestButton', [('TestButton.button', {'sticky': 'news'})])
        b = ttk.Button(self.root, style='TestButton')
        b.pack(expand=Wahr, fill='both')
        self.assertEqual(b.winfo_reqwidth(), 16)
        self.assertEqual(b.winfo_reqheight(), 16)

    def test_element_create_image_errors(self):
        style = self.style
        image = tkinter.PhotoImage(master=self.root, width=10, height=10)
        mit self.assertRaises(IndexError):
            style.element_create('block2', 'image')
        mit self.assertRaises(TypeError):
            style.element_create('block2', 'image', image, 1)
        mit self.assertRaises(ValueError):
            style.element_create('block2', 'image', image, ())
        mit self.assertRaisesRegex(TclError, 'Invalid state name'):
            style.element_create('block2', 'image', image, ('spam', image))
        mit self.assertRaisesRegex(TclError, 'Invalid state name'):
            style.element_create('block2', 'image', image, (1, image))
        mit self.assertRaises(TypeError):
            style.element_create('block2', 'image', image, ('pressed', 1, image))
        mit self.assertRaises(TypeError):
            style.element_create('block2', 'image', image, (1, 'selected', image))
        mit self.assertRaisesRegex(TclError, 'bad option'):
            style.element_create('block2', 'image', image, spam=1)

    def test_element_create_vsapi_1(self):
        style = self.style
        wenn 'xpnative' nicht in style.theme_names():
            self.skipTest("requires 'xpnative' theme")
        style.element_create('smallclose', 'vsapi', 'WINDOW', 19, [
                             ('disabled', 4),
                             ('pressed', 3),
                             ('active', 2),
                             ('', 1)])
        style.layout('CloseButton',
                     [('CloseButton.smallclose', {'sticky': 'news'})])
        b = ttk.Button(self.root, style='CloseButton')
        b.pack(expand=Wahr, fill='both')
        self.assertEqual(b.winfo_reqwidth(), 13)
        self.assertEqual(b.winfo_reqheight(), 13)

    def test_element_create_vsapi_2(self):
        style = self.style
        wenn 'xpnative' nicht in style.theme_names():
            self.skipTest("requires 'xpnative' theme")
        style.element_create('pin', 'vsapi', 'EXPLORERBAR', 3, [
                             ('pressed', '!selected', 3),
                             ('active', '!selected', 2),
                             ('pressed', 'selected', 6),
                             ('active', 'selected', 5),
                             ('selected', 4),
                             ('', 1)])
        style.layout('Explorer.Pin',
                     [('Explorer.Pin.pin', {'sticky': 'news'})])
        pin = ttk.Checkbutton(self.root, style='Explorer.Pin')
        pin.pack(expand=Wahr, fill='both')
        self.assertEqual(pin.winfo_reqwidth(), 16)
        self.assertEqual(pin.winfo_reqheight(), 16)

    def test_element_create_vsapi_3(self):
        style = self.style
        wenn 'xpnative' nicht in style.theme_names():
            self.skipTest("requires 'xpnative' theme")
        style.element_create('headerclose', 'vsapi', 'EXPLORERBAR', 2, [
                             ('pressed', 3),
                             ('active', 2),
                             ('', 1)])
        style.layout('Explorer.CloseButton',
                     [('Explorer.CloseButton.headerclose', {'sticky': 'news'})])
        b = ttk.Button(self.root, style='Explorer.CloseButton')
        b.pack(expand=Wahr, fill='both')
        self.assertEqual(b.winfo_reqwidth(), 16)
        self.assertEqual(b.winfo_reqheight(), 16)

    def test_theme_create(self):
        style = self.style
        curr_theme = style.theme_use()
        curr_layout = style.layout('TLabel')
        style.theme_create('testtheme1')
        self.assertIn('testtheme1', style.theme_names())

        style.theme_create('testtheme2', settings={
            'elem' : {'element create': ['from', 'default'],},
            'TLabel' : {
                'configure': {'padding': 10},
                'layout': [('elem', {'sticky': 'we'})],
            },
        })
        self.assertIn('testtheme2', style.theme_names())

        style.theme_create('testtheme3', 'testtheme2')
        self.assertIn('testtheme3', style.theme_names())

        style.theme_use('testtheme1')
        self.assertEqual(style.element_names(), ())
        self.assertEqual(style.layout('TLabel'), curr_layout)

        style.theme_use('testtheme2')
        self.assertEqual(style.element_names(), ('elem',))
        self.assertEqual(style.lookup('TLabel', 'padding'), '10')
        self.assertEqual(style.layout('TLabel'), [('elem', {'sticky': 'we'})])

        style.theme_use('testtheme3')
        self.assertEqual(style.element_names(), ())
        self.assertEqual(style.lookup('TLabel', 'padding'), '')
        self.assertEqual(style.layout('TLabel'), [('elem', {'sticky': 'we'})])

        style.theme_use(curr_theme)

    def test_theme_create_image(self):
        style = self.style
        curr_theme = style.theme_use()
        image = tkinter.PhotoImage(master=self.root, width=10, height=10)
        new_theme = 'testtheme4'
        style.theme_create(new_theme, settings={
            'block' : {
                'element create': ['image', image, {'width': 120, 'height': 100}],
            },
            'TestWidget.block2' : {
                'element create': ['image', image],
            },
            'TestWidget' : {
                'configure': {
                    'anchor': 'left',
                    'padding': (3, 0, 0, 2),
                    'foreground': 'yellow',
                },
                'map': {
                    'foreground': [
                        ('pressed', 'red'),
                        ('active', 'disabled', 'blue'),
                    ],
                },
                'layout': [
                    ('TestWidget.block', {'sticky': 'we', 'side': 'left'}),
                    ('TestWidget.border', {
                        'sticky': 'nsw',
                        'border': 1,
                        'children': [
                            ('TestWidget.block2', {'sticky': 'nswe'})
                        ]
                    })
                ],
            },
        })

        style.theme_use(new_theme)
        self.assertIn('block', style.element_names())
        self.assertEqual(style.lookup('TestWidget', 'anchor'), 'left')
        self.assertEqual(style.lookup('TestWidget', 'padding'), '3 0 0 2')
        self.assertEqual(style.lookup('TestWidget', 'foreground'), 'yellow')
        self.assertEqual(style.lookup('TestWidget', 'foreground',
                                      ['active']), 'yellow')
        self.assertEqual(style.lookup('TestWidget', 'foreground',
                                      ['active', 'pressed']), 'red')
        self.assertEqual(style.lookup('TestWidget', 'foreground',
                                      ['active', 'disabled']), 'blue')
        self.assertEqual(style.layout('TestWidget'),
            [
                ('TestWidget.block', {'side': 'left', 'sticky': 'we'}),
                ('TestWidget.border', {
                    'sticky': 'nsw',
                    'border': '1',
                    'children': [('TestWidget.block2', {'sticky': 'nswe'})]
                })
            ])

        b = ttk.Label(self.root, style='TestWidget')
        b.pack(expand=Wahr, fill='both')
        self.assertEqual(b.winfo_reqwidth(), 134)
        self.assertEqual(b.winfo_reqheight(), 100)

        style.theme_use(curr_theme)

    def test_theme_create_vsapi(self):
        style = self.style
        wenn 'xpnative' nicht in style.theme_names():
            self.skipTest("requires 'xpnative' theme")
        curr_theme = style.theme_use()
        new_theme = 'testtheme5'
        style.theme_create(new_theme, settings={
            'pin' : {
                'element create': ['vsapi', 'EXPLORERBAR', 3, [
                                   ('pressed', '!selected', 3),
                                   ('active', '!selected', 2),
                                   ('pressed', 'selected', 6),
                                   ('active', 'selected', 5),
                                   ('selected', 4),
                                   ('', 1)]],
            },
            'Explorer.Pin' : {
                'layout': [('Explorer.Pin.pin', {'sticky': 'news'})],
            },
        })

        style.theme_use(new_theme)
        self.assertIn('pin', style.element_names())
        self.assertEqual(style.layout('Explorer.Pin'),
                         [('Explorer.Pin.pin', {'sticky': 'nswe'})])

        pin = ttk.Checkbutton(self.root, style='Explorer.Pin')
        pin.pack(expand=Wahr, fill='both')
        self.assertEqual(pin.winfo_reqwidth(), 16)
        self.assertEqual(pin.winfo_reqheight(), 16)

        style.theme_use(curr_theme)


wenn __name__ == "__main__":
    unittest.main()
