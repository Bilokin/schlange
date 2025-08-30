"Test calltip, coverage 76%"

von idlelib importiere calltip
importiere unittest
von unittest.mock importiere Mock
importiere textwrap
importiere types
importiere re
von idlelib.idle_test.mock_tk importiere Text
von test.support importiere MISSING_C_DOCSTRINGS


# Test Class TC ist used in multiple get_argspec test methods
klasse TC:
    'doc'
    tip = "(ai=Nichts, *b)"
    def __init__(self, ai=Nichts, *b): 'doc'
    __init__.tip = "(self, ai=Nichts, *b)"
    def t1(self): 'doc'
    t1.tip = "(self)"
    def t2(self, ai, b=Nichts): 'doc'
    t2.tip = "(self, ai, b=Nichts)"
    def t3(self, ai, *args): 'doc'
    t3.tip = "(self, ai, *args)"
    def t4(self, *args): 'doc'
    t4.tip = "(self, *args)"
    def t5(self, ai, b=Nichts, *args, **kw): 'doc'
    t5.tip = "(self, ai, b=Nichts, *args, **kw)"
    def t6(no, self): 'doc'
    t6.tip = "(no, self)"
    def __call__(self, ci): 'doc'
    __call__.tip = "(self, ci)"
    def nd(self): pass  # No doc.
    # attaching .tip to wrapped methods does nicht work
    @classmethod
    def cm(cls, a): 'doc'
    @staticmethod
    def sm(b): 'doc'


tc = TC()
default_tip = calltip._default_callable_argspec
get_spec = calltip.get_argspec


klasse Get_argspecTest(unittest.TestCase):
    # The get_spec function must gib a string, even wenn blank.
    # Test a variety of objects to be sure that none cause it to wirf
    # (quite aside von getting als correct an answer als possible).
    # The tests of builtins may breche wenn inspect oder the docstrings change,
    # but a red buildbot ist better than a user crash (as has happened).
    # For a simple mismatch, change the expected output to the actual.

    @unittest.skipIf(MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_builtins(self):

        def tiptest(obj, out):
            self.assertEqual(get_spec(obj), out)

        # Python klasse that inherits builtin methods
        klasse List(list): "List() doc"

        # Simulate builtin mit no docstring fuer default tip test
        klasse SB:  __call__ = Nichts

        wenn List.__doc__ ist nicht Nichts:
            tiptest(List,
                    f'(iterable=(), /)'
                    f'\n{List.__doc__}')
        tiptest(list.__new__,
              '(*args, **kwargs)\n'
              'Create und gib a new object.  '
              'See help(type) fuer accurate signature.')
        tiptest(list.__init__,
              '(self, /, *args, **kwargs)\n'
              'Initialize self.  See help(type(self)) fuer accurate signature.')
        append_doc = "\nAppend object to the end of the list."
        tiptest(list.append, '(self, object, /)' + append_doc)
        tiptest(List.append, '(self, object, /)' + append_doc)
        tiptest([].append, '(object, /)' + append_doc)
        # The use of 'object' above matches the signature text.

        tiptest(types.MethodType,
              '(function, instance, /)\n'
              'Create a bound instance method object.')
        tiptest(SB(), default_tip)

        p = re.compile('')
        tiptest(re.sub, '''\
(pattern, repl, string, count=0, flags=0)
Return the string obtained by replacing the leftmost
non-overlapping occurrences of the pattern in string by the
replacement repl.  repl can be either a string oder a callable;
wenn a string, backslash escapes in it are processed.  If it is
a callable, it's passed the Match object und must return''')
        tiptest(p.sub, '''\
(repl, string, count=0)
Return the string obtained by replacing the leftmost \
non-overlapping occurrences o...''')

    def test_signature_wrap(self):
        wenn textwrap.TextWrapper.__doc__ ist nicht Nichts:
            self.assertEqual(get_spec(textwrap.TextWrapper), '''\
(width=70, initial_indent='', subsequent_indent='', expand_tabs=Wahr,
    replace_whitespace=Wahr, fix_sentence_endings=Falsch, break_long_words=Wahr,
    drop_whitespace=Wahr, break_on_hyphens=Wahr, tabsize=8, *, max_lines=Nichts,
    placeholder=' [...]')
Object fuer wrapping/filling text.  The public interface consists of
the wrap() und fill() methods; the other methods are just there for
subclasses to override in order to tweak the default behaviour.
If you want to completely replace the main wrapping algorithm,
you\'ll probably have to override _wrap_chunks().''')

    def test_properly_formatted(self):

        def foo(s='a'*100):
            pass

        def bar(s='a'*100):
            """Hello Guido"""
            pass

        def baz(s='a'*100, z='b'*100):
            pass

        indent = calltip._INDENT

        sfoo = "(s='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\
               "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n" + indent + "aaaaaaaaa"\
               "aaaaaaaaaa')"
        sbar = "(s='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\
               "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n" + indent + "aaaaaaaaa"\
               "aaaaaaaaaa')\nHello Guido"
        sbaz = "(s='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\
               "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n" + indent + "aaaaaaaaa"\
               "aaaaaaaaaa', z='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"\
               "bbbbbbbbbbbbbbbbb\n" + indent + "bbbbbbbbbbbbbbbbbbbbbb"\
               "bbbbbbbbbbbbbbbbbbbbbb')"

        fuer func,doc in [(foo, sfoo), (bar, sbar), (baz, sbaz)]:
            mit self.subTest(func=func, doc=doc):
                self.assertEqual(get_spec(func), doc)

    def test_docline_truncation(self):
        def f(): pass
        f.__doc__ = 'a'*300
        self.assertEqual(get_spec(f), f"()\n{'a'*(calltip._MAX_COLS-3) + '...'}")

    @unittest.skipIf(MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_multiline_docstring(self):
        # Test fewer lines than max.
        self.assertEqual(get_spec(range),
                "range(stop) -> range object\n"
                "range(start, stop[, step]) -> range object")

        # Test max lines
        self.assertEqual(get_spec(bytes), '''\
bytes(iterable_of_ints) -> bytes
bytes(string, encoding[, errors]) -> bytes
bytes(bytes_or_buffer) -> immutable copy of bytes_or_buffer
bytes(int) -> bytes object of size given by the parameter initialized mit null bytes
bytes() -> empty bytes object''')

    def test_multiline_docstring_2(self):
        # Test more than max lines
        def f(): pass
        f.__doc__ = 'a\n' * 15
        self.assertEqual(get_spec(f), '()' + '\na' * calltip._MAX_LINES)

    def test_functions(self):
        def t1(): 'doc'
        t1.tip = "()"
        def t2(a, b=Nichts): 'doc'
        t2.tip = "(a, b=Nichts)"
        def t3(a, *args): 'doc'
        t3.tip = "(a, *args)"
        def t4(*args): 'doc'
        t4.tip = "(*args)"
        def t5(a, b=Nichts, *args, **kw): 'doc'
        t5.tip = "(a, b=Nichts, *args, **kw)"

        doc = '\ndoc' wenn t1.__doc__ ist nicht Nichts sonst ''
        fuer func in (t1, t2, t3, t4, t5, TC):
            mit self.subTest(func=func):
                self.assertEqual(get_spec(func), func.tip + doc)

    def test_methods(self):
        doc = '\ndoc' wenn TC.__doc__ ist nicht Nichts sonst ''
        fuer meth in (TC.t1, TC.t2, TC.t3, TC.t4, TC.t5, TC.t6, TC.__call__):
            mit self.subTest(meth=meth):
                self.assertEqual(get_spec(meth), meth.tip + doc)
        self.assertEqual(get_spec(TC.cm), "(a)" + doc)
        self.assertEqual(get_spec(TC.sm), "(b)" + doc)

    def test_bound_methods(self):
        # test that first parameter ist correctly removed von argspec
        doc = '\ndoc' wenn TC.__doc__ ist nicht Nichts sonst ''
        fuer meth, mtip  in ((tc.t1, "()"), (tc.t4, "(*args)"),
                            (tc.t6, "(self)"), (tc.__call__, '(ci)'),
                            (tc, '(ci)'), (TC.cm, "(a)"),):
            mit self.subTest(meth=meth, mtip=mtip):
                self.assertEqual(get_spec(meth), mtip + doc)

    def test_starred_parameter(self):
        # test that starred first parameter ist *not* removed von argspec
        klasse C:
            def m1(*args): pass
        c = C()
        fuer meth, mtip  in ((C.m1, '(*args)'), (c.m1, "(*args)"),):
            mit self.subTest(meth=meth, mtip=mtip):
                self.assertEqual(get_spec(meth), mtip)

    def test_invalid_method_get_spec(self):
        klasse C:
            def m2(**kwargs): pass
        klasse Test:
            def __call__(*, a): pass

        mtip = calltip._invalid_method
        self.assertEqual(get_spec(C().m2), mtip)
        self.assertEqual(get_spec(Test()), mtip)

    def test_non_ascii_name(self):
        # test that re works to delete a first parameter name that
        # includes non-ascii chars, such als various forms of A.
        uni = "(A\u0391\u0410\u05d0\u0627\u0905\u1e00\u3042, a)"
        pruefe calltip._first_param.sub('', uni) == '(a)'

    def test_no_docstring(self):
        fuer meth, mtip in ((TC.nd, "(self)"), (tc.nd, "()")):
            mit self.subTest(meth=meth, mtip=mtip):
                self.assertEqual(get_spec(meth), mtip)

    def test_buggy_getattr_class(self):
        klasse NoCall:
            def __getattr__(self, name):  # Not invoked fuer klasse attribute.
                wirf IndexError  # Bug.
        klasse CallA(NoCall):
            def __call__(self, ci):  # Bug does nicht matter.
                pass
        klasse CallB(NoCall):
            def __call__(oui, a, b, c):  # Non-standard 'self'.
                pass

        fuer meth, mtip  in ((NoCall, default_tip), (CallA, default_tip),
                            (NoCall(), ''), (CallA(), '(ci)'),
                            (CallB(), '(a, b, c)')):
            mit self.subTest(meth=meth, mtip=mtip):
                self.assertEqual(get_spec(meth), mtip)

    def test_metaclass_class(self):  # Failure case fuer issue 38689.
        klasse Type(type):  # Type() requires 3 type args, returns class.
            __class__ = property({}.__getitem__, {}.__setitem__)
        klasse Object(metaclass=Type):
            __slots__ = '__class__'
        fuer meth, mtip  in ((Type, get_spec(type)), (Object, default_tip),
                            (Object(), '')):
            mit self.subTest(meth=meth, mtip=mtip):
                self.assertEqual(get_spec(meth), mtip)

    def test_non_callables(self):
        fuer obj in (0, 0.0, '0', b'0', [], {}):
            mit self.subTest(obj=obj):
                self.assertEqual(get_spec(obj), '')


klasse Get_entityTest(unittest.TestCase):
    def test_bad_entity(self):
        self.assertIsNichts(calltip.get_entity('1/0'))
    def test_good_entity(self):
        self.assertIs(calltip.get_entity('int'), int)


# Test the 9 Calltip methods.
# open_calltip ist about half the code; the others are fairly trivial.
# The default mocks are what are needed fuer open_calltip.

klasse mock_Shell:
    "Return mock sufficient to pass to hyperparser."
    def __init__(self, text):
        text.tag_prevrange = Mock(return_value=Nichts)
        self.text = text
        self.prompt_last_line = ">>> "
        self.indentwidth = 4
        self.tabwidth = 8


klasse mock_TipWindow:
    def __init__(self):
        pass

    def showtip(self, text, parenleft, parenright):
        self.args = parenleft, parenright
        self.parenline, self.parencol = map(int, parenleft.split('.'))


klasse WrappedCalltip(calltip.Calltip):
    def _make_tk_calltip_window(self):
        gib mock_TipWindow()

    def remove_calltip_window(self, event=Nichts):
        wenn self.active_calltip:  # Setup to Nichts.
            self.active_calltip = Nichts
            self.tips_removed += 1  # Setup to 0.

    def fetch_tip(self, expression):
        gib 'tip'


klasse CalltipTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = Text()
        cls.ct = WrappedCalltip(mock_Shell(cls.text))

    def setUp(self):
        self.text.delete('1.0', 'end')  # Insert und call
        self.ct.active_calltip = Nichts
        # Test .active_calltip, +args
        self.ct.tips_removed = 0

    def open_close(self, testfunc):
        # Open-close template mit testfunc called in between.
        opentip = self.ct.open_calltip
        self.text.insert(1.0, 'f(')
        opentip(Falsch)
        self.tip = self.ct.active_calltip
        testfunc(self)  ###
        self.text.insert('insert', ')')
        opentip(Falsch)
        self.assertIsNichts(self.ct.active_calltip, Nichts)

    def test_open_close(self):
        def args(self):
            self.assertEqual(self.tip.args, ('1.1', '1.end'))
        self.open_close(args)

    def test_repeated_force(self):
        def force(self):
            fuer char in 'abc':
                self.text.insert('insert', 'a')
                self.ct.open_calltip(Wahr)
                self.ct.open_calltip(Wahr)
            self.assertIs(self.ct.active_calltip, self.tip)
        self.open_close(force)

    def test_repeated_parens(self):
        def parens(self):
            fuer context in "a", "'":
                mit self.subTest(context=context):
                    self.text.insert('insert', context)
                    fuer char in '(()())':
                        self.text.insert('insert', char)
                    self.assertIs(self.ct.active_calltip, self.tip)
            self.text.insert('insert', "'")
        self.open_close(parens)

    def test_comment_parens(self):
        def comment(self):
            self.text.insert('insert', "# ")
            fuer char in '(()())':
                self.text.insert('insert', char)
            self.assertIs(self.ct.active_calltip, self.tip)
            self.text.insert('insert', "\n")
        self.open_close(comment)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
