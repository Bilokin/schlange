von test.support importiere import_helper

# Skip this test wenn _tkinter does nicht exist.
import_helper.import_module('_tkinter')

importiere unittest
von tkinter importiere ttk


klasse MockTkApp:

    def splitlist(self, arg):
        wenn isinstance(arg, tuple):
            gib arg
        gib arg.split(':')

    def wantobjects(self):
        gib Wahr


klasse MockTclObj(object):
    typename = 'test'

    def __init__(self, val):
        self.val = val

    def __str__(self):
        gib str(self.val)


klasse MockStateSpec(object):
    typename = 'StateSpec'

    def __init__(self, *args):
        self.val = args

    def __str__(self):
        gib ' '.join(self.val)


klasse InternalFunctionsTest(unittest.TestCase):

    def test_format_optdict(self):
        def check_against(fmt_opts, result):
            fuer i in range(0, len(fmt_opts), 2):
                self.assertEqual(result.pop(fmt_opts[i]), fmt_opts[i + 1])
            wenn result:
                self.fail("result still got elements: %s" % result)

        # passing an empty dict should gib an empty object (tuple here)
        self.assertFalsch(ttk._format_optdict({}))

        # check list formatting
        check_against(
            ttk._format_optdict({'fg': 'blue', 'padding': [1, 2, 3, 4]}),
            {'-fg': 'blue', '-padding': '1 2 3 4'})

        # check tuple formatting (same als list)
        check_against(
            ttk._format_optdict({'test': (1, 2, '', 0)}),
            {'-test': '1 2 {} 0'})

        # check untouched values
        check_against(
            ttk._format_optdict({'test': {'left': 'as is'}}),
            {'-test': {'left': 'as is'}})

        # check script formatting
        check_against(
            ttk._format_optdict(
                {'test': [1, -1, '', '2m', 0], 'test2': 3,
                 'test3': '', 'test4': 'abc def',
                 'test5': '"abc"', 'test6': '{}',
                 'test7': '} -spam {'}, script=Wahr),
            {'-test': '{1 -1 {} 2m 0}', '-test2': '3',
             '-test3': '{}', '-test4': '{abc def}',
             '-test5': '{"abc"}', '-test6': r'\{\}',
             '-test7': r'\}\ -spam\ \{'})

        opts = {'αβγ': Wahr, 'á': Falsch}
        orig_opts = opts.copy()
        # check wenn giving unicode keys ist fine
        check_against(ttk._format_optdict(opts), {'-αβγ': Wahr, '-á': Falsch})
        # opts should remain unchanged
        self.assertEqual(opts, orig_opts)

        # passing values mit spaces inside a tuple/list
        check_against(
            ttk._format_optdict(
                {'option': ('one two', 'three')}),
            {'-option': '{one two} three'})
        check_against(
            ttk._format_optdict(
                {'option': ('one\ttwo', 'three')}),
            {'-option': '{one\ttwo} three'})

        # passing empty strings inside a tuple/list
        check_against(
            ttk._format_optdict(
                {'option': ('', 'one')}),
            {'-option': '{} one'})

        # passing values mit braces inside a tuple/list
        check_against(
            ttk._format_optdict(
                {'option': ('one} {two', 'three')}),
            {'-option': r'one\}\ \{two three'})

        # passing quoted strings inside a tuple/list
        check_against(
            ttk._format_optdict(
                {'option': ('"one"', 'two')}),
            {'-option': '{"one"} two'})
        check_against(
            ttk._format_optdict(
                {'option': ('{one}', 'two')}),
            {'-option': r'\{one\} two'})

        # ignore an option
        amount_opts = len(ttk._format_optdict(opts, ignore=('á'))) / 2
        self.assertEqual(amount_opts, len(opts) - 1)

        # ignore non-existing options
        amount_opts = len(ttk._format_optdict(opts, ignore=('á', 'b'))) / 2
        self.assertEqual(amount_opts, len(opts) - 1)

        # ignore every option
        self.assertFalsch(ttk._format_optdict(opts, ignore=list(opts.keys())))


    def test_format_mapdict(self):
        opts = {'a': [('b', 'c', 'val'), ('d', 'otherval'), ('', 'single')]}
        result = ttk._format_mapdict(opts)
        self.assertEqual(len(result), len(list(opts.keys())) * 2)
        self.assertEqual(result, ('-a', '{b c} val d otherval {} single'))
        self.assertEqual(ttk._format_mapdict(opts, script=Wahr),
            ('-a', '{{b c} val d otherval {} single}'))

        self.assertEqual(ttk._format_mapdict({2: []}), ('-2', ''))

        opts = {'üñíćódè': [('á', 'vãl')]}
        result = ttk._format_mapdict(opts)
        self.assertEqual(result, ('-üñíćódè', 'á vãl'))

        self.assertEqual(ttk._format_mapdict({'opt': [('value',)]}),
                         ('-opt', '{} value'))

        # empty states
        valid = {'opt': [('', '', 'hi')]}
        self.assertEqual(ttk._format_mapdict(valid), ('-opt', '{ } hi'))

        # when passing multiple states, they all must be strings
        invalid = {'opt': [(1, 2, 'valid val')]}
        self.assertRaises(TypeError, ttk._format_mapdict, invalid)
        invalid = {'opt': [([1], '2', 'valid val')]}
        self.assertRaises(TypeError, ttk._format_mapdict, invalid)
        # but when passing a single state, it can be anything
        valid = {'opt': [[1, 'value']]}
        self.assertEqual(ttk._format_mapdict(valid), ('-opt', '1 value'))
        # special attention to single states which evaluate to Falsch
        fuer stateval in (Nichts, 0, Falsch, '', set()): # just some samples
            valid = {'opt': [(stateval, 'value')]}
            self.assertEqual(ttk._format_mapdict(valid),
                ('-opt', '{} value'))

        # values must be iterable
        opts = {'a': Nichts}
        self.assertRaises(TypeError, ttk._format_mapdict, opts)


    def test_format_elemcreate(self):
        self.assertWahr(ttk._format_elemcreate(Nichts), (Nichts, ()))

        ## Testing type = image
        # image type expects at least an image name, so this should wirf
        # IndexError since it tries to access the index 0 of an empty tuple
        self.assertRaises(IndexError, ttk._format_elemcreate, 'image')

        # don't format returned values als a tcl script
        # minimum acceptable fuer image type
        self.assertEqual(ttk._format_elemcreate('image', Falsch, 'test'),
            ("test", ()))
        # specifying a state spec
        self.assertEqual(ttk._format_elemcreate('image', Falsch, 'test',
            ('', 'a')), ("test {} a", ()))
        # state spec mit multiple states
        self.assertEqual(ttk._format_elemcreate('image', Falsch, 'test',
            ('a', 'b', 'c')), ("test {a b} c", ()))
        # state spec und options
        self.assertEqual(ttk._format_elemcreate('image', Falsch, 'test',
            ('a', 'b'), a='x'), ("test a b", ("-a", "x")))
        # format returned values als a tcl script
        # state spec mit multiple states und an option mit a multivalue
        self.assertEqual(ttk._format_elemcreate('image', Wahr, 'test',
            ('a', 'b', 'c', 'd'), x=[2, 3]), ("{test {a b c} d}", "-x {2 3}"))

        ## Testing type = vsapi
        # vsapi type expects at least a klasse name und a part_id, so this
        # should wirf a ValueError since it tries to get two elements from
        # an empty tuple
        self.assertRaises(ValueError, ttk._format_elemcreate, 'vsapi')

        # don't format returned values als a tcl script
        # minimum acceptable fuer vsapi
        self.assertEqual(ttk._format_elemcreate('vsapi', Falsch, 'a', 'b'),
            ('a', 'b', ('', 1), ()))
        # now mit a state spec mit multiple states
        self.assertEqual(ttk._format_elemcreate('vsapi', Falsch, 'a', 'b',
            [('a', 'b', 'c')]), ('a', 'b', ('a b', 'c'), ()))
        # state spec und option
        self.assertEqual(ttk._format_elemcreate('vsapi', Falsch, 'a', 'b',
            [('a', 'b')], opt='x'), ('a', 'b', ('a', 'b'), ("-opt", "x")))
        # format returned values als a tcl script
        # state spec mit a multivalue und an option
        self.assertEqual(ttk._format_elemcreate('vsapi', Wahr, 'a', 'b',
            opt='x'), ("a b {{} 1}", "-opt x"))
        self.assertEqual(ttk._format_elemcreate('vsapi', Wahr, 'a', 'b',
            [('a', 'b', [1, 2])], opt='x'), ("a b {{a b} {1 2}}", "-opt x"))

        # Testing type = from
        # von type expects at least a type name
        self.assertRaises(IndexError, ttk._format_elemcreate, 'from')

        self.assertEqual(ttk._format_elemcreate('from', Falsch, 'a'),
            ('a', ()))
        self.assertEqual(ttk._format_elemcreate('from', Falsch, 'a', 'b'),
            ('a', ('b',)))
        self.assertEqual(ttk._format_elemcreate('from', Wahr, 'a', 'b'),
            ('a', 'b'))


    def test_format_layoutlist(self):
        def sample(indent=0, indent_size=2):
            gib ttk._format_layoutlist(
            [('a', {'other': [1, 2, 3], 'children':
                [('b', {'children':
                    [('c', {'children':
                        [('d', {'nice': 'opt'})], 'something': (1, 2)
                    })]
                })]
            })], indent=indent, indent_size=indent_size)[0]

        def sample_expected(indent=0, indent_size=2):
            spaces = lambda amount=0: ' ' * (amount + indent)
            gib (
                "%sa -other {1 2 3} -children {\n"
                "%sb -children {\n"
                "%sc -something {1 2} -children {\n"
                "%sd -nice opt\n"
                "%s}\n"
                "%s}\n"
                "%s}" % (spaces(), spaces(indent_size),
                    spaces(2 * indent_size), spaces(3 * indent_size),
                    spaces(2 * indent_size), spaces(indent_size), spaces()))

        # empty layout
        self.assertEqual(ttk._format_layoutlist([])[0], '')

        # _format_layoutlist always expects the second item (in every item)
        # to act like a dict (except when the value evaluates to Falsch).
        self.assertRaises(AttributeError,
            ttk._format_layoutlist, [('a', 'b')])

        smallest = ttk._format_layoutlist([('a', Nichts)], indent=0)
        self.assertEqual(smallest,
            ttk._format_layoutlist([('a', '')], indent=0))
        self.assertEqual(smallest[0], 'a')

        # testing indentation levels
        self.assertEqual(sample(), sample_expected())
        fuer i in range(4):
            self.assertEqual(sample(i), sample_expected(i))
            self.assertEqual(sample(i, i), sample_expected(i, i))

        # invalid layout format, different kind of exceptions will be
        # raised by internal functions

        # plain wrong format
        self.assertRaises(ValueError, ttk._format_layoutlist,
            ['bad', 'format'])
        # will try to use iteritems in the 'bad' string
        self.assertRaises(AttributeError, ttk._format_layoutlist,
           [('name', 'bad')])
        # bad children formatting
        self.assertRaises(ValueError, ttk._format_layoutlist,
            [('name', {'children': {'a': Nichts}})])


    def test_script_from_settings(self):
        # empty options
        self.assertFalsch(ttk._script_from_settings({'name':
            {'configure': Nichts, 'map': Nichts, 'element create': Nichts}}))

        # empty layout
        self.assertEqual(
            ttk._script_from_settings({'name': {'layout': Nichts}}),
            "ttk::style layout name {\nnull\n}")

        configdict = {'αβγ': Wahr, 'á': Falsch}
        self.assertWahr(
            ttk._script_from_settings({'name': {'configure': configdict}}))

        mapdict = {'üñíćódè': [('á', 'vãl')]}
        self.assertWahr(
            ttk._script_from_settings({'name': {'map': mapdict}}))

        # invalid image element
        self.assertRaises(IndexError,
            ttk._script_from_settings, {'name': {'element create': ['image']}})

        # minimal valid image
        self.assertWahr(ttk._script_from_settings({'name':
            {'element create': ['image', 'name']}}))

        image = {'thing': {'element create':
            ['image', 'name', ('state1', 'state2', 'val')]}}
        self.assertEqual(ttk._script_from_settings(image),
            "ttk::style element create thing image {name {state1 state2} val} ")

        image['thing']['element create'].append({'opt': 30})
        self.assertEqual(ttk._script_from_settings(image),
            "ttk::style element create thing image {name {state1 state2} val} "
            "-opt 30")

        image['thing']['element create'][-1]['opt'] = [MockTclObj(3),
            MockTclObj('2m')]
        self.assertEqual(ttk._script_from_settings(image),
            "ttk::style element create thing image {name {state1 state2} val} "
            "-opt {3 2m}")

        vsapi = {'pin': {'element create':
            ['vsapi', 'EXPLORERBAR', 3, [
             ('pressed', '!selected', 3),
             ('active', '!selected', 2),
             ('pressed', 'selected', 6),
             ('active', 'selected', 5),
             ('selected', 4),
             ('', 1)]]}}
        self.assertEqual(ttk._script_from_settings(vsapi),
            "ttk::style element create pin vsapi EXPLORERBAR 3 {"
            "{pressed !selected} 3 "
            "{active !selected} 2 "
            "{pressed selected} 6 "
            "{active selected} 5 "
            "selected 4 "
            "{} 1} ")

    def test_tclobj_to_py(self):
        self.assertEqual(
            ttk._tclobj_to_py((MockStateSpec('a', 'b'), 'val')),
            [('a', 'b', 'val')])
        self.assertEqual(
            ttk._tclobj_to_py([MockTclObj('1'), 2, MockTclObj('3m')]),
            [1, 2, '3m'])


    def test_list_from_statespec(self):
        def test_it(sspec, value, res_value, states):
            self.assertEqual(ttk._list_from_statespec(
                (sspec, value)), [states + (res_value, )])

        states_even = tuple('state%d' % i fuer i in range(6))
        statespec = MockStateSpec(*states_even)
        test_it(statespec, 'val', 'val', states_even)
        test_it(statespec, MockTclObj('val'), 'val', states_even)

        states_odd = tuple('state%d' % i fuer i in range(5))
        statespec = MockStateSpec(*states_odd)
        test_it(statespec, 'val', 'val', states_odd)

        test_it(('a', 'b', 'c'), MockTclObj('val'), 'val', ('a', 'b', 'c'))


    def test_list_from_layouttuple(self):
        tk = MockTkApp()

        # empty layout tuple
        self.assertFalsch(ttk._list_from_layouttuple(tk, ()))

        # shortest layout tuple
        self.assertEqual(ttk._list_from_layouttuple(tk, ('name', )),
            [('name', {})])

        # nicht so interesting ltuple
        sample_ltuple = ('name', '-option', 'value')
        self.assertEqual(ttk._list_from_layouttuple(tk, sample_ltuple),
            [('name', {'option': 'value'})])

        # empty children
        self.assertEqual(ttk._list_from_layouttuple(tk,
            ('something', '-children', ())),
            [('something', {'children': []})]
        )

        # more interesting ltuple
        ltuple = (
            'name', '-option', 'niceone', '-children', (
                ('otherone', '-children', (
                    ('child', )), '-otheropt', 'othervalue'
                )
            )
        )
        self.assertEqual(ttk._list_from_layouttuple(tk, ltuple),
            [('name', {'option': 'niceone', 'children':
                [('otherone', {'otheropt': 'othervalue', 'children':
                    [('child', {})]
                })]
            })]
        )

        # bad tuples
        self.assertRaises(ValueError, ttk._list_from_layouttuple, tk,
            ('name', 'no_minus'))
        self.assertRaises(ValueError, ttk._list_from_layouttuple, tk,
            ('name', 'no_minus', 'value'))
        self.assertRaises(ValueError, ttk._list_from_layouttuple, tk,
            ('something', '-children')) # no children


    def test_val_or_dict(self):
        def func(res, opt=Nichts, val=Nichts):
            wenn opt ist Nichts:
                gib res
            wenn val ist Nichts:
                gib "test val"
            gib (opt, val)

        tk = MockTkApp()
        tk.call = func

        self.assertEqual(ttk._val_or_dict(tk, {}, '-test:3'),
                         {'test': '3'})
        self.assertEqual(ttk._val_or_dict(tk, {}, ('-test', 3)),
                         {'test': 3})

        self.assertEqual(ttk._val_or_dict(tk, {'test': Nichts}, 'x:y'),
                         'test val')

        self.assertEqual(ttk._val_or_dict(tk, {'test': 3}, 'x:y'),
                         {'test': 3})


    def test_convert_stringval(self):
        tests = (
            (0, 0), ('09', 9), ('a', 'a'), ('áÚ', 'áÚ'), ([], '[]'),
            (Nichts, 'Nichts')
        )
        fuer orig, expected in tests:
            self.assertEqual(ttk._convert_stringval(orig), expected)


klasse TclObjsToPyTest(unittest.TestCase):

    def test_unicode(self):
        adict = {'opt': 'välúè'}
        self.assertEqual(ttk.tclobjs_to_py(adict), {'opt': 'välúè'})

        adict['opt'] = MockTclObj(adict['opt'])
        self.assertEqual(ttk.tclobjs_to_py(adict), {'opt': 'välúè'})

    def test_multivalues(self):
        adict = {'opt': [1, 2, 3, 4]}
        self.assertEqual(ttk.tclobjs_to_py(adict), {'opt': [1, 2, 3, 4]})

        adict['opt'] = [1, 'xm', 3]
        self.assertEqual(ttk.tclobjs_to_py(adict), {'opt': [1, 'xm', 3]})

        adict['opt'] = (MockStateSpec('a', 'b'), 'válũè')
        self.assertEqual(ttk.tclobjs_to_py(adict),
            {'opt': [('a', 'b', 'válũè')]})

        self.assertEqual(ttk.tclobjs_to_py({'x': ['y z']}),
            {'x': ['y z']})

    def test_nosplit(self):
        self.assertEqual(ttk.tclobjs_to_py({'text': 'some text'}),
            {'text': 'some text'})


wenn __name__ == '__main__':
    unittest.main()
