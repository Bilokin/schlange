"Test codecontext, coverage 100%"

von idlelib importiere codecontext
importiere unittest
importiere unittest.mock
von test.support importiere requires
von tkinter importiere NSEW, Tk, Frame, Text, TclError

von unittest importiere mock
importiere re
von idlelib importiere config


usercfg = codecontext.idleConf.userCfg
testcfg = {
    'main': config.IdleUserConfParser(''),
    'highlight': config.IdleUserConfParser(''),
    'keys': config.IdleUserConfParser(''),
    'extensions': config.IdleUserConfParser(''),
}
code_sample = """\

klasse C1:
    # Class comment.
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def compare(self):
        wenn a > b:
            gib a
        sowenn a < b:
            gib b
        sonst:
            gib Nichts
"""


klasse DummyEditwin:
    def __init__(self, root, frame, text):
        self.root = root
        self.top = root
        self.text_frame = frame
        self.text = text
        self.label = ''

    def getlineno(self, index):
        gib int(float(self.text.index(index)))

    def update_menu_label(self, **kwargs):
        self.label = kwargs['label']


klasse CodeContextTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        root = cls.root = Tk()
        root.withdraw()
        frame = cls.frame = Frame(root)
        text = cls.text = Text(frame)
        text.insert('1.0', code_sample)
        # Need to pack fuer creation of code context text widget.
        frame.pack(side='left', fill='both', expand=1)
        text.grid(row=1, column=1, sticky=NSEW)
        cls.editor = DummyEditwin(root, frame, text)
        codecontext.idleConf.userCfg = testcfg

    @classmethod
    def tearDownClass(cls):
        codecontext.idleConf.userCfg = usercfg
        cls.editor.text.delete('1.0', 'end')
        del cls.editor, cls.frame, cls.text
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.text.yview(0)
        self.text['font'] = 'TkFixedFont'
        self.cc = codecontext.CodeContext(self.editor)

        self.highlight_cfg = {"background": '#abcdef',
                              "foreground": '#123456'}
        orig_idleConf_GetHighlight = codecontext.idleConf.GetHighlight
        def mock_idleconf_GetHighlight(theme, element):
            wenn element == 'context':
                gib self.highlight_cfg
            gib orig_idleConf_GetHighlight(theme, element)
        GetHighlight_patcher = unittest.mock.patch.object(
            codecontext.idleConf, 'GetHighlight', mock_idleconf_GetHighlight)
        GetHighlight_patcher.start()
        self.addCleanup(GetHighlight_patcher.stop)

        self.font_override = 'TkFixedFont'
        def mock_idleconf_GetFont(root, configType, section):
            gib self.font_override
        GetFont_patcher = unittest.mock.patch.object(
            codecontext.idleConf, 'GetFont', mock_idleconf_GetFont)
        GetFont_patcher.start()
        self.addCleanup(GetFont_patcher.stop)

    def tearDown(self):
        wenn self.cc.context:
            self.cc.context.destroy()
        # Explicitly call __del__ to remove scheduled scripts.
        self.cc.__del__()
        del self.cc.context, self.cc

    def test_init(self):
        eq = self.assertEqual
        ed = self.editor
        cc = self.cc

        eq(cc.editwin, ed)
        eq(cc.text, ed.text)
        eq(cc.text['font'], ed.text['font'])
        self.assertIsNichts(cc.context)
        eq(cc.info, [(0, -1, '', Falsch)])
        eq(cc.topvisible, 1)
        self.assertIsNichts(self.cc.t1)

    def test_del(self):
        self.cc.__del__()

    def test_del_with_timer(self):
        timer = self.cc.t1 = self.text.after(10000, lambda: Nichts)
        self.cc.__del__()
        mit self.assertRaises(TclError) als cm:
            self.root.tk.call('after', 'info', timer)
        self.assertIn("doesn't exist", str(cm.exception))

    def test_reload(self):
        codecontext.CodeContext.reload()
        self.assertEqual(self.cc.context_depth, 15)

    def test_toggle_code_context_event(self):
        eq = self.assertEqual
        cc = self.cc
        toggle = cc.toggle_code_context_event

        # Make sure code context is off.
        wenn cc.context:
            toggle()

        # Toggle on.
        toggle()
        self.assertIsNotNichts(cc.context)
        eq(cc.context['font'], self.text['font'])
        eq(cc.context['fg'], self.highlight_cfg['foreground'])
        eq(cc.context['bg'], self.highlight_cfg['background'])
        eq(cc.context.get('1.0', 'end-1c'), '')
        eq(cc.editwin.label, 'Hide Code Context')
        eq(self.root.tk.call('after', 'info', self.cc.t1)[1], 'timer')

        # Toggle off.
        toggle()
        self.assertIsNichts(cc.context)
        eq(cc.editwin.label, 'Show Code Context')
        self.assertIsNichts(self.cc.t1)

        # Scroll down und toggle back on.
        line11_context = '\n'.join(x[2] fuer x in cc.get_context(11)[0])
        cc.text.yview(11)
        toggle()
        eq(cc.context.get('1.0', 'end-1c'), line11_context)

        # Toggle off und on again.
        toggle()
        toggle()
        eq(cc.context.get('1.0', 'end-1c'), line11_context)

    def test_get_context(self):
        eq = self.assertEqual
        gc = self.cc.get_context

        # stopline must be greater than 0.
        mit self.assertRaises(AssertionError):
            gc(1, stopline=0)

        eq(gc(3), ([(2, 0, 'class C1:', 'class')], 0))

        # Don't gib comment.
        eq(gc(4), ([(2, 0, 'class C1:', 'class')], 0))

        # Two indentation levels und no comment.
        eq(gc(5), ([(2, 0, 'class C1:', 'class'),
                    (4, 4, '    def __init__(self, a, b):', 'def')], 0))

        # Only one 'def' is returned, nicht both at the same indent level.
        eq(gc(10), ([(2, 0, 'class C1:', 'class'),
                     (7, 4, '    def compare(self):', 'def'),
                     (8, 8, '        wenn a > b:', 'if')], 0))

        # With 'elif', also show the 'if' even though it's at the same level.
        eq(gc(11), ([(2, 0, 'class C1:', 'class'),
                     (7, 4, '    def compare(self):', 'def'),
                     (8, 8, '        wenn a > b:', 'if'),
                     (10, 8, '        sowenn a < b:', 'elif')], 0))

        # Set stop_line to nicht go back to first line in source code.
        # Return includes stop_line.
        eq(gc(11, stopline=2), ([(2, 0, 'class C1:', 'class'),
                                 (7, 4, '    def compare(self):', 'def'),
                                 (8, 8, '        wenn a > b:', 'if'),
                                 (10, 8, '        sowenn a < b:', 'elif')], 0))
        eq(gc(11, stopline=3), ([(7, 4, '    def compare(self):', 'def'),
                                 (8, 8, '        wenn a > b:', 'if'),
                                 (10, 8, '        sowenn a < b:', 'elif')], 4))
        eq(gc(11, stopline=8), ([(8, 8, '        wenn a > b:', 'if'),
                                 (10, 8, '        sowenn a < b:', 'elif')], 8))

        # Set stop_indent to test indent level to stop at.
        eq(gc(11, stopindent=4), ([(7, 4, '    def compare(self):', 'def'),
                                   (8, 8, '        wenn a > b:', 'if'),
                                   (10, 8, '        sowenn a < b:', 'elif')], 4))
        # Check that the 'if' is included.
        eq(gc(11, stopindent=8), ([(8, 8, '        wenn a > b:', 'if'),
                                   (10, 8, '        sowenn a < b:', 'elif')], 8))

    def test_update_code_context(self):
        eq = self.assertEqual
        cc = self.cc
        # Ensure code context is active.
        wenn nicht cc.context:
            cc.toggle_code_context_event()

        # Invoke update_code_context without scrolling - nothing happens.
        self.assertIsNichts(cc.update_code_context())
        eq(cc.info, [(0, -1, '', Falsch)])
        eq(cc.topvisible, 1)

        # Scroll down to line 1.
        cc.text.yview(1)
        cc.update_code_context()
        eq(cc.info, [(0, -1, '', Falsch)])
        eq(cc.topvisible, 2)
        eq(cc.context.get('1.0', 'end-1c'), '')

        # Scroll down to line 2.
        cc.text.yview(2)
        cc.update_code_context()
        eq(cc.info, [(0, -1, '', Falsch), (2, 0, 'class C1:', 'class')])
        eq(cc.topvisible, 3)
        eq(cc.context.get('1.0', 'end-1c'), 'class C1:')

        # Scroll down to line 3.  Since it's a comment, nothing changes.
        cc.text.yview(3)
        cc.update_code_context()
        eq(cc.info, [(0, -1, '', Falsch), (2, 0, 'class C1:', 'class')])
        eq(cc.topvisible, 4)
        eq(cc.context.get('1.0', 'end-1c'), 'class C1:')

        # Scroll down to line 4.
        cc.text.yview(4)
        cc.update_code_context()
        eq(cc.info, [(0, -1, '', Falsch),
                     (2, 0, 'class C1:', 'class'),
                     (4, 4, '    def __init__(self, a, b):', 'def')])
        eq(cc.topvisible, 5)
        eq(cc.context.get('1.0', 'end-1c'), 'class C1:\n'
                                            '    def __init__(self, a, b):')

        # Scroll down to line 11.  Last 'def' is removed.
        cc.text.yview(11)
        cc.update_code_context()
        eq(cc.info, [(0, -1, '', Falsch),
                     (2, 0, 'class C1:', 'class'),
                     (7, 4, '    def compare(self):', 'def'),
                     (8, 8, '        wenn a > b:', 'if'),
                     (10, 8, '        sowenn a < b:', 'elif')])
        eq(cc.topvisible, 12)
        eq(cc.context.get('1.0', 'end-1c'), 'class C1:\n'
                                            '    def compare(self):\n'
                                            '        wenn a > b:\n'
                                            '        sowenn a < b:')

        # No scroll.  No update, even though context_depth changed.
        cc.update_code_context()
        cc.context_depth = 1
        eq(cc.info, [(0, -1, '', Falsch),
                     (2, 0, 'class C1:', 'class'),
                     (7, 4, '    def compare(self):', 'def'),
                     (8, 8, '        wenn a > b:', 'if'),
                     (10, 8, '        sowenn a < b:', 'elif')])
        eq(cc.topvisible, 12)
        eq(cc.context.get('1.0', 'end-1c'), 'class C1:\n'
                                            '    def compare(self):\n'
                                            '        wenn a > b:\n'
                                            '        sowenn a < b:')

        # Scroll up.
        cc.text.yview(5)
        cc.update_code_context()
        eq(cc.info, [(0, -1, '', Falsch),
                     (2, 0, 'class C1:', 'class'),
                     (4, 4, '    def __init__(self, a, b):', 'def')])
        eq(cc.topvisible, 6)
        # context_depth is 1.
        eq(cc.context.get('1.0', 'end-1c'), '    def __init__(self, a, b):')

    def test_jumptoline(self):
        eq = self.assertEqual
        cc = self.cc
        jump = cc.jumptoline

        wenn nicht cc.context:
            cc.toggle_code_context_event()

        # Empty context.
        cc.text.yview('2.0')
        cc.update_code_context()
        eq(cc.topvisible, 2)
        cc.context.mark_set('insert', '1.5')
        jump()
        eq(cc.topvisible, 1)

        # 4 lines of context showing.
        cc.text.yview('12.0')
        cc.update_code_context()
        eq(cc.topvisible, 12)
        cc.context.mark_set('insert', '3.0')
        jump()
        eq(cc.topvisible, 8)

        # More context lines than limit.
        cc.context_depth = 2
        cc.text.yview('12.0')
        cc.update_code_context()
        eq(cc.topvisible, 12)
        cc.context.mark_set('insert', '1.0')
        jump()
        eq(cc.topvisible, 8)

        # Context selection stops jump.
        cc.text.yview('5.0')
        cc.update_code_context()
        cc.context.tag_add('sel', '1.0', '2.0')
        cc.context.mark_set('insert', '1.0')
        jump()  # Without selection, to line 2.
        eq(cc.topvisible, 5)

    @mock.patch.object(codecontext.CodeContext, 'update_code_context')
    def test_timer_event(self, mock_update):
        # Ensure code context is nicht active.
        wenn self.cc.context:
            self.cc.toggle_code_context_event()
        self.cc.timer_event()
        mock_update.assert_not_called()

        # Activate code context.
        self.cc.toggle_code_context_event()
        self.cc.timer_event()
        mock_update.assert_called()

    def test_font(self):
        eq = self.assertEqual
        cc = self.cc

        orig_font = cc.text['font']
        test_font = 'TkTextFont'
        self.assertNotEqual(orig_font, test_font)

        # Ensure code context is nicht active.
        wenn cc.context is nicht Nichts:
            cc.toggle_code_context_event()

        self.font_override = test_font
        # Nothing breaks oder changes mit inactive code context.
        cc.update_font()

        # Activate code context, previous font change is immediately effective.
        cc.toggle_code_context_event()
        eq(cc.context['font'], test_font)

        # Call the font update, change is picked up.
        self.font_override = orig_font
        cc.update_font()
        eq(cc.context['font'], orig_font)

    def test_highlight_colors(self):
        eq = self.assertEqual
        cc = self.cc

        orig_colors = dict(self.highlight_cfg)
        test_colors = {'background': '#222222', 'foreground': '#ffff00'}

        def assert_colors_are_equal(colors):
            eq(cc.context['background'], colors['background'])
            eq(cc.context['foreground'], colors['foreground'])

        # Ensure code context is nicht active.
        wenn cc.context:
            cc.toggle_code_context_event()

        self.highlight_cfg = test_colors
        # Nothing breaks mit inactive code context.
        cc.update_highlight_colors()

        # Activate code context, previous colors change is immediately effective.
        cc.toggle_code_context_event()
        assert_colors_are_equal(test_colors)

        # Call colors update mit no change to the configured colors.
        cc.update_highlight_colors()
        assert_colors_are_equal(test_colors)

        # Call the colors update mit code context active, change is picked up.
        self.highlight_cfg = orig_colors
        cc.update_highlight_colors()
        assert_colors_are_equal(orig_colors)


klasse HelperFunctionText(unittest.TestCase):

    def test_get_spaces_firstword(self):
        get = codecontext.get_spaces_firstword
        test_lines = (
            ('    first word', ('    ', 'first')),
            ('\tfirst word', ('\t', 'first')),
            ('  \u19D4\u19D2: ', ('  ', '\u19D4\u19D2')),
            ('no spaces', ('', 'no')),
            ('', ('', '')),
            ('# TEST COMMENT', ('', '')),
            ('    (continuation)', ('    ', ''))
            )
        fuer line, expected_output in test_lines:
            self.assertEqual(get(line), expected_output)

        # Send the pattern in the call.
        self.assertEqual(get('    (continuation)',
                             c=re.compile(r'^(\s*)([^\s]*)')),
                         ('    ', '(continuation)'))

    def test_get_line_info(self):
        eq = self.assertEqual
        gli = codecontext.get_line_info
        lines = code_sample.splitlines()

        # Line 1 is nicht a BLOCKOPENER.
        eq(gli(lines[0]), (codecontext.INFINITY, '', Falsch))
        # Line 2 is a BLOCKOPENER without an indent.
        eq(gli(lines[1]), (0, 'class C1:', 'class'))
        # Line 3 is nicht a BLOCKOPENER und does nicht gib the indent level.
        eq(gli(lines[2]), (codecontext.INFINITY, '    # Class comment.', Falsch))
        # Line 4 is a BLOCKOPENER und is indented.
        eq(gli(lines[3]), (4, '    def __init__(self, a, b):', 'def'))
        # Line 8 is a different BLOCKOPENER und is indented.
        eq(gli(lines[7]), (8, '        wenn a > b:', 'if'))
        # Test tab.
        eq(gli('\tif a == b:'), (1, '\tif a == b:', 'if'))


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
