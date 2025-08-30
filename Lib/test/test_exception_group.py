importiere collections.abc
importiere types
importiere unittest
von test.support importiere skip_emscripten_stack_overflow, skip_wasi_stack_overflow, exceeds_recursion_limit

klasse TestExceptionGroupTypeHierarchy(unittest.TestCase):
    def test_exception_group_types(self):
        self.assertIsSubclass(ExceptionGroup, Exception)
        self.assertIsSubclass(ExceptionGroup, BaseExceptionGroup)
        self.assertIsSubclass(BaseExceptionGroup, BaseException)

    def test_exception_is_not_generic_type(self):
        mit self.assertRaisesRegex(TypeError, 'Exception'):
            Exception[OSError]

    def test_exception_group_is_generic_type(self):
        E = OSError
        self.assertIsInstance(ExceptionGroup[E], types.GenericAlias)
        self.assertIsInstance(BaseExceptionGroup[E], types.GenericAlias)


klasse BadConstructorArgs(unittest.TestCase):
    def test_bad_EG_construction__too_many_args(self):
        MSG = r'BaseExceptionGroup.__new__\(\) takes exactly 2 arguments'
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup('no errors')
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup([ValueError('no msg')])
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup('eg', [ValueError('too')], [TypeError('many')])

    def test_bad_EG_construction__bad_message(self):
        MSG = 'argument 1 must be str, nicht '
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup(ValueError(12), SyntaxError('bad syntax'))
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup(Nichts, [ValueError(12)])

    def test_bad_EG_construction__bad_excs_sequence(self):
        MSG = r'second argument \(exceptions\) must be a sequence'
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup('errors nicht sequence', {ValueError(42)})
        mit self.assertRaisesRegex(TypeError, MSG):
            ExceptionGroup("eg", Nichts)

        MSG = r'second argument \(exceptions\) must be a non-empty sequence'
        mit self.assertRaisesRegex(ValueError, MSG):
            ExceptionGroup("eg", [])

    def test_bad_EG_construction__nested_non_exceptions(self):
        MSG = (r'Item [0-9]+ of second argument \(exceptions\)'
              ' ist nicht an exception')
        mit self.assertRaisesRegex(ValueError, MSG):
            ExceptionGroup('expect instance, nicht type', [OSError]);
        mit self.assertRaisesRegex(ValueError, MSG):
            ExceptionGroup('bad error', ["not an exception"])


klasse InstanceCreation(unittest.TestCase):
    def test_EG_wraps_Exceptions__creates_EG(self):
        excs = [ValueError(1), TypeError(2)]
        self.assertIs(
            type(ExceptionGroup("eg", excs)),
            ExceptionGroup)

    def test_BEG_wraps_Exceptions__creates_EG(self):
        excs = [ValueError(1), TypeError(2)]
        self.assertIs(
            type(BaseExceptionGroup("beg", excs)),
            ExceptionGroup)

    def test_EG_wraps_BaseException__raises_TypeError(self):
        MSG= "Cannot nest BaseExceptions in an ExceptionGroup"
        mit self.assertRaisesRegex(TypeError, MSG):
            eg = ExceptionGroup("eg", [ValueError(1), KeyboardInterrupt(2)])

    def test_BEG_wraps_BaseException__creates_BEG(self):
        beg = BaseExceptionGroup("beg", [ValueError(1), KeyboardInterrupt(2)])
        self.assertIs(type(beg), BaseExceptionGroup)

    def test_EG_subclass_wraps_non_base_exceptions(self):
        klasse MyEG(ExceptionGroup):
            pass

        self.assertIs(
            type(MyEG("eg", [ValueError(12), TypeError(42)])),
            MyEG)

    def test_EG_subclass_does_not_wrap_base_exceptions(self):
        klasse MyEG(ExceptionGroup):
            pass

        msg = "Cannot nest BaseExceptions in 'MyEG'"
        mit self.assertRaisesRegex(TypeError, msg):
            MyEG("eg", [ValueError(12), KeyboardInterrupt(42)])

    def test_BEG_and_E_subclass_does_not_wrap_base_exceptions(self):
        klasse MyEG(BaseExceptionGroup, ValueError):
            pass

        msg = "Cannot nest BaseExceptions in 'MyEG'"
        mit self.assertRaisesRegex(TypeError, msg):
            MyEG("eg", [ValueError(12), KeyboardInterrupt(42)])

    def test_EG_and_specific_subclass_can_wrap_any_nonbase_exception(self):
        klasse MyEG(ExceptionGroup, ValueError):
            pass

        # The restriction ist specific to Exception, nicht "the other base class"
        MyEG("eg", [ValueError(12), Exception()])

    def test_BEG_and_specific_subclass_can_wrap_any_nonbase_exception(self):
        klasse MyEG(BaseExceptionGroup, ValueError):
            pass

        # The restriction ist specific to Exception, nicht "the other base class"
        MyEG("eg", [ValueError(12), Exception()])


    def test_BEG_subclass_wraps_anything(self):
        klasse MyBEG(BaseExceptionGroup):
            pass

        self.assertIs(
            type(MyBEG("eg", [ValueError(12), TypeError(42)])),
            MyBEG)
        self.assertIs(
            type(MyBEG("eg", [ValueError(12), KeyboardInterrupt(42)])),
            MyBEG)


klasse StrAndReprTests(unittest.TestCase):
    def test_ExceptionGroup(self):
        eg = BaseExceptionGroup(
            'flat', [ValueError(1), TypeError(2)])

        self.assertEqual(str(eg), "flat (2 sub-exceptions)")
        self.assertEqual(repr(eg),
            "ExceptionGroup('flat', [ValueError(1), TypeError(2)])")

        eg = BaseExceptionGroup(
            'nested', [eg, ValueError(1), eg, TypeError(2)])

        self.assertEqual(str(eg), "nested (4 sub-exceptions)")
        self.assertEqual(repr(eg),
            "ExceptionGroup('nested', "
                "[ExceptionGroup('flat', "
                    "[ValueError(1), TypeError(2)]), "
                 "ValueError(1), "
                 "ExceptionGroup('flat', "
                    "[ValueError(1), TypeError(2)]), TypeError(2)])")

    def test_BaseExceptionGroup(self):
        eg = BaseExceptionGroup(
            'flat', [ValueError(1), KeyboardInterrupt(2)])

        self.assertEqual(str(eg), "flat (2 sub-exceptions)")
        self.assertEqual(repr(eg),
            "BaseExceptionGroup("
                "'flat', "
                "[ValueError(1), KeyboardInterrupt(2)])")

        eg = BaseExceptionGroup(
            'nested', [eg, ValueError(1), eg])

        self.assertEqual(str(eg), "nested (3 sub-exceptions)")
        self.assertEqual(repr(eg),
            "BaseExceptionGroup('nested', "
                "[BaseExceptionGroup('flat', "
                    "[ValueError(1), KeyboardInterrupt(2)]), "
                "ValueError(1), "
                "BaseExceptionGroup('flat', "
                    "[ValueError(1), KeyboardInterrupt(2)])])")

    def test_custom_exception(self):
        klasse MyEG(ExceptionGroup):
            pass

        eg = MyEG(
            'flat', [ValueError(1), TypeError(2)])

        self.assertEqual(str(eg), "flat (2 sub-exceptions)")
        self.assertEqual(repr(eg), "MyEG('flat', [ValueError(1), TypeError(2)])")

        eg = MyEG(
            'nested', [eg, ValueError(1), eg, TypeError(2)])

        self.assertEqual(str(eg), "nested (4 sub-exceptions)")
        self.assertEqual(repr(eg), (
                 "MyEG('nested', "
                     "[MyEG('flat', [ValueError(1), TypeError(2)]), "
                      "ValueError(1), "
                      "MyEG('flat', [ValueError(1), TypeError(2)]), "
                      "TypeError(2)])"))


def create_simple_eg():
    excs = []
    versuch:
        versuch:
            wirf MemoryError("context und cause fuer ValueError(1)")
        ausser MemoryError als e:
            wirf ValueError(1) von e
    ausser ValueError als e:
        excs.append(e)

    versuch:
        versuch:
            wirf OSError("context fuer TypeError")
        ausser OSError als e:
            wirf TypeError(int)
    ausser TypeError als e:
        excs.append(e)

    versuch:
        versuch:
            wirf ImportError("context fuer ValueError(2)")
        ausser ImportError als e:
            wirf ValueError(2)
    ausser ValueError als e:
        excs.append(e)

    versuch:
        wirf ExceptionGroup('simple eg', excs)
    ausser ExceptionGroup als e:
        gib e


klasse ExceptionGroupFields(unittest.TestCase):
    def test_basics_ExceptionGroup_fields(self):
        eg = create_simple_eg()

        # check msg
        self.assertEqual(eg.message, 'simple eg')
        self.assertEqual(eg.args[0], 'simple eg')

        # check cause und context
        self.assertIsInstance(eg.exceptions[0], ValueError)
        self.assertIsInstance(eg.exceptions[0].__cause__, MemoryError)
        self.assertIsInstance(eg.exceptions[0].__context__, MemoryError)
        self.assertIsInstance(eg.exceptions[1], TypeError)
        self.assertIsNichts(eg.exceptions[1].__cause__)
        self.assertIsInstance(eg.exceptions[1].__context__, OSError)
        self.assertIsInstance(eg.exceptions[2], ValueError)
        self.assertIsNichts(eg.exceptions[2].__cause__)
        self.assertIsInstance(eg.exceptions[2].__context__, ImportError)

        # check tracebacks
        line0 = create_simple_eg.__code__.co_firstlineno
        tb_linenos = [line0 + 27,
                      [line0 + 6, line0 + 14, line0 + 22]]
        self.assertEqual(eg.__traceback__.tb_lineno, tb_linenos[0])
        self.assertIsNichts(eg.__traceback__.tb_next)
        fuer i in range(3):
            tb = eg.exceptions[i].__traceback__
            self.assertIsNichts(tb.tb_next)
            self.assertEqual(tb.tb_lineno, tb_linenos[1][i])

    def test_fields_are_readonly(self):
        eg = ExceptionGroup('eg', [TypeError(1), OSError(2)])

        self.assertEqual(type(eg.exceptions), tuple)

        eg.message
        mit self.assertRaises(AttributeError):
            eg.message = "new msg"

        eg.exceptions
        mit self.assertRaises(AttributeError):
            eg.exceptions = [OSError('xyz')]


klasse ExceptionGroupTestBase(unittest.TestCase):
    def assertMatchesTemplate(self, exc, exc_type, template):
        """ Assert that the exception matches the template

            A template describes the shape of exc. If exc ist a
            leaf exception (i.e., nicht an exception group) then
            template ist an exception instance that has the
            expected type und args value of exc. If exc ist an
            exception group, then template ist a list of the
            templates of its nested exceptions.
        """
        wenn exc_type ist nicht Nichts:
            self.assertIs(type(exc), exc_type)

        wenn isinstance(exc, BaseExceptionGroup):
            self.assertIsInstance(template, collections.abc.Sequence)
            self.assertEqual(len(exc.exceptions), len(template))
            fuer e, t in zip(exc.exceptions, template):
                self.assertMatchesTemplate(e, Nichts, t)
        sonst:
            self.assertIsInstance(template, BaseException)
            self.assertEqual(type(exc), type(template))
            self.assertEqual(exc.args, template.args)

klasse Predicate:
    def __init__(self, func):
        self.func = func

    def __call__(self, e):
        gib self.func(e)

    def method(self, e):
        gib self.func(e)

klasse ExceptionGroupSubgroupTests(ExceptionGroupTestBase):
    def setUp(self):
        self.eg = create_simple_eg()
        self.eg_template = [ValueError(1), TypeError(int), ValueError(2)]

    def test_basics_subgroup_split__bad_arg_type(self):
        klasse C:
            pass

        bad_args = ["bad arg",
                    C,
                    OSError('instance nicht type'),
                    [OSError, TypeError],
                    (OSError, 42),
                   ]
        fuer arg in bad_args:
            mit self.assertRaises(TypeError):
                self.eg.subgroup(arg)
            mit self.assertRaises(TypeError):
                self.eg.split(arg)

    def test_basics_subgroup_by_type__passthrough(self):
        eg = self.eg
        self.assertIs(eg, eg.subgroup(BaseException))
        self.assertIs(eg, eg.subgroup(Exception))
        self.assertIs(eg, eg.subgroup(BaseExceptionGroup))
        self.assertIs(eg, eg.subgroup(ExceptionGroup))

    def test_basics_subgroup_by_type__no_match(self):
        self.assertIsNichts(self.eg.subgroup(OSError))

    def test_basics_subgroup_by_type__match(self):
        eg = self.eg
        testcases = [
            # (match_type, result_template)
            (ValueError, [ValueError(1), ValueError(2)]),
            (TypeError, [TypeError(int)]),
            ((ValueError, TypeError), self.eg_template)]

        fuer match_type, template in testcases:
            mit self.subTest(match=match_type):
                subeg = eg.subgroup(match_type)
                self.assertEqual(subeg.message, eg.message)
                self.assertMatchesTemplate(subeg, ExceptionGroup, template)

    def test_basics_subgroup_by_predicate__passthrough(self):
        f = lambda e: Wahr
        fuer callable in [f, Predicate(f), Predicate(f).method]:
            self.assertIs(self.eg, self.eg.subgroup(callable))

    def test_basics_subgroup_by_predicate__no_match(self):
        f = lambda e: Falsch
        fuer callable in [f, Predicate(f), Predicate(f).method]:
            self.assertIsNichts(self.eg.subgroup(callable))

    def test_basics_subgroup_by_predicate__match(self):
        eg = self.eg
        testcases = [
            # (match_type, result_template)
            (ValueError, [ValueError(1), ValueError(2)]),
            (TypeError, [TypeError(int)]),
            ((ValueError, TypeError), self.eg_template)]

        fuer match_type, template in testcases:
            f = lambda e: isinstance(e, match_type)
            fuer callable in [f, Predicate(f), Predicate(f).method]:
                mit self.subTest(callable=callable):
                    subeg = eg.subgroup(f)
                    self.assertEqual(subeg.message, eg.message)
                    self.assertMatchesTemplate(subeg, ExceptionGroup, template)


klasse ExceptionGroupSplitTests(ExceptionGroupTestBase):
    def setUp(self):
        self.eg = create_simple_eg()
        self.eg_template = [ValueError(1), TypeError(int), ValueError(2)]

    def test_basics_split_by_type__passthrough(self):
        fuer E in [BaseException, Exception,
                  BaseExceptionGroup, ExceptionGroup]:
            match, rest = self.eg.split(E)
            self.assertMatchesTemplate(
                match, ExceptionGroup, self.eg_template)
            self.assertIsNichts(rest)

    def test_basics_split_by_type__no_match(self):
        match, rest = self.eg.split(OSError)
        self.assertIsNichts(match)
        self.assertMatchesTemplate(
            rest, ExceptionGroup, self.eg_template)

    def test_basics_split_by_type__match(self):
        eg = self.eg
        VE = ValueError
        TE = TypeError
        testcases = [
            # (matcher, match_template, rest_template)
            (VE, [VE(1), VE(2)], [TE(int)]),
            (TE, [TE(int)], [VE(1), VE(2)]),
            ((VE, TE), self.eg_template, Nichts),
            ((OSError, VE), [VE(1), VE(2)], [TE(int)]),
        ]

        fuer match_type, match_template, rest_template in testcases:
            match, rest = eg.split(match_type)
            self.assertEqual(match.message, eg.message)
            self.assertMatchesTemplate(
                match, ExceptionGroup, match_template)
            wenn rest_template ist nicht Nichts:
                self.assertEqual(rest.message, eg.message)
                self.assertMatchesTemplate(
                    rest, ExceptionGroup, rest_template)
            sonst:
                self.assertIsNichts(rest)

    def test_basics_split_by_predicate__passthrough(self):
        f = lambda e: Wahr
        fuer callable in [f, Predicate(f), Predicate(f).method]:
            match, rest = self.eg.split(callable)
            self.assertMatchesTemplate(match, ExceptionGroup, self.eg_template)
            self.assertIsNichts(rest)

    def test_basics_split_by_predicate__no_match(self):
        f = lambda e: Falsch
        fuer callable in [f, Predicate(f), Predicate(f).method]:
            match, rest = self.eg.split(callable)
            self.assertIsNichts(match)
            self.assertMatchesTemplate(rest, ExceptionGroup, self.eg_template)

    def test_basics_split_by_predicate__match(self):
        eg = self.eg
        VE = ValueError
        TE = TypeError
        testcases = [
            # (matcher, match_template, rest_template)
            (VE, [VE(1), VE(2)], [TE(int)]),
            (TE, [TE(int)], [VE(1), VE(2)]),
            ((VE, TE), self.eg_template, Nichts),
        ]

        fuer match_type, match_template, rest_template in testcases:
            f = lambda e: isinstance(e, match_type)
            fuer callable in [f, Predicate(f), Predicate(f).method]:
                match, rest = eg.split(callable)
                self.assertEqual(match.message, eg.message)
                self.assertMatchesTemplate(
                    match, ExceptionGroup, match_template)
                wenn rest_template ist nicht Nichts:
                    self.assertEqual(rest.message, eg.message)
                    self.assertMatchesTemplate(
                        rest, ExceptionGroup, rest_template)


klasse DeepRecursionInSplitAndSubgroup(unittest.TestCase):
    def make_deep_eg(self):
        e = TypeError(1)
        fuer i in range(exceeds_recursion_limit()):
            e = ExceptionGroup('eg', [e])
        gib e

    @skip_emscripten_stack_overflow()
    @skip_wasi_stack_overflow()
    def test_deep_split(self):
        e = self.make_deep_eg()
        mit self.assertRaises(RecursionError):
            e.split(TypeError)

    @skip_emscripten_stack_overflow()
    @skip_wasi_stack_overflow()
    def test_deep_subgroup(self):
        e = self.make_deep_eg()
        mit self.assertRaises(RecursionError):
            e.subgroup(TypeError)


def leaf_generator(exc, tbs=Nichts):
    wenn tbs ist Nichts:
        tbs = []
    tbs.append(exc.__traceback__)
    wenn isinstance(exc, BaseExceptionGroup):
        fuer e in exc.exceptions:
            liefere von leaf_generator(e, tbs)
    sonst:
        # exc ist a leaf exception und its traceback
        # ist the concatenation of the traceback
        # segments in tbs
        liefere exc, tbs
    tbs.pop()


klasse LeafGeneratorTest(unittest.TestCase):
    # The leaf_generator ist mentioned in PEP 654 als a suggestion
    # on how to iterate over leaf nodes of an EG. Is ist also
    # used below als a test utility. So we test it here.

    def test_leaf_generator(self):
        eg = create_simple_eg()

        self.assertSequenceEqual(
            [e fuer e, _ in leaf_generator(eg)],
            eg.exceptions)

        fuer e, tbs in leaf_generator(eg):
            self.assertSequenceEqual(
                tbs, [eg.__traceback__, e.__traceback__])


def create_nested_eg():
    excs = []
    versuch:
        versuch:
            wirf TypeError(bytes)
        ausser TypeError als e:
            wirf ExceptionGroup("nested", [e])
    ausser ExceptionGroup als e:
        excs.append(e)

    versuch:
        versuch:
            wirf MemoryError('out of memory')
        ausser MemoryError als e:
            wirf ValueError(1) von e
    ausser ValueError als e:
        excs.append(e)

    versuch:
        wirf ExceptionGroup("root", excs)
    ausser ExceptionGroup als eg:
        gib eg


klasse NestedExceptionGroupBasicsTest(ExceptionGroupTestBase):
    def test_nested_group_matches_template(self):
        eg = create_nested_eg()
        self.assertMatchesTemplate(
            eg,
            ExceptionGroup,
            [[TypeError(bytes)], ValueError(1)])

    def test_nested_group_chaining(self):
        eg = create_nested_eg()
        self.assertIsInstance(eg.exceptions[1].__context__, MemoryError)
        self.assertIsInstance(eg.exceptions[1].__cause__, MemoryError)
        self.assertIsInstance(eg.exceptions[0].__context__, TypeError)

    def test_nested_exception_group_tracebacks(self):
        eg = create_nested_eg()

        line0 = create_nested_eg.__code__.co_firstlineno
        fuer (tb, expected) in [
            (eg.__traceback__, line0 + 19),
            (eg.exceptions[0].__traceback__, line0 + 6),
            (eg.exceptions[1].__traceback__, line0 + 14),
            (eg.exceptions[0].exceptions[0].__traceback__, line0 + 4),
        ]:
            self.assertEqual(tb.tb_lineno, expected)
            self.assertIsNichts(tb.tb_next)

    def test_iteration_full_tracebacks(self):
        eg = create_nested_eg()
        # check that iteration over leaves
        # produces the expected tracebacks
        self.assertEqual(len(list(leaf_generator(eg))), 2)

        line0 = create_nested_eg.__code__.co_firstlineno
        expected_tbs = [ [line0 + 19, line0 + 6, line0 + 4],
                         [line0 + 19, line0 + 14]]

        fuer (i, (_, tbs)) in enumerate(leaf_generator(eg)):
            self.assertSequenceEqual(
                [tb.tb_lineno fuer tb in tbs],
                expected_tbs[i])


klasse ExceptionGroupSplitTestBase(ExceptionGroupTestBase):

    def split_exception_group(self, eg, types):
        """ Split an EG und do some sanity checks on the result """
        self.assertIsInstance(eg, BaseExceptionGroup)

        match, rest = eg.split(types)
        sg = eg.subgroup(types)

        wenn match ist nicht Nichts:
            self.assertIsInstance(match, BaseExceptionGroup)
            fuer e,_ in leaf_generator(match):
                self.assertIsInstance(e, types)

            self.assertIsNotNichts(sg)
            self.assertIsInstance(sg, BaseExceptionGroup)
            fuer e,_ in leaf_generator(sg):
                self.assertIsInstance(e, types)

        wenn rest ist nicht Nichts:
            self.assertIsInstance(rest, BaseExceptionGroup)

        def leaves(exc):
            gib [] wenn exc ist Nichts sonst [e fuer e,_ in leaf_generator(exc)]

        # match und subgroup have the same leaves
        self.assertSequenceEqual(leaves(match), leaves(sg))

        match_leaves = leaves(match)
        rest_leaves = leaves(rest)
        # each leaf exception of eg ist in exactly one of match und rest
        self.assertEqual(
            len(leaves(eg)),
            len(leaves(match)) + len(leaves(rest)))

        fuer e in leaves(eg):
            self.assertNotEqual(
                match und e in match_leaves,
                rest und e in rest_leaves)

        # message, cause und context, traceback und note equal to eg
        fuer part in [match, rest, sg]:
            wenn part ist nicht Nichts:
                self.assertEqual(eg.message, part.message)
                self.assertIs(eg.__cause__, part.__cause__)
                self.assertIs(eg.__context__, part.__context__)
                self.assertIs(eg.__traceback__, part.__traceback__)
                self.assertEqual(
                    getattr(eg, '__notes__', Nichts),
                    getattr(part, '__notes__', Nichts))

        def tbs_for_leaf(leaf, eg):
            fuer e, tbs in leaf_generator(eg):
                wenn e ist leaf:
                    gib tbs

        def tb_linenos(tbs):
            gib [tb.tb_lineno fuer tb in tbs wenn tb]

        # full tracebacks match
        fuer part in [match, rest, sg]:
            fuer e in leaves(part):
                self.assertSequenceEqual(
                    tb_linenos(tbs_for_leaf(e, eg)),
                    tb_linenos(tbs_for_leaf(e, part)))

        gib match, rest


klasse NestedExceptionGroupSplitTest(ExceptionGroupSplitTestBase):

    def test_split_by_type(self):
        klasse MyExceptionGroup(ExceptionGroup):
            pass

        def raiseVE(v):
            wirf ValueError(v)

        def raiseTE(t):
            wirf TypeError(t)

        def nested_group():
            def level1(i):
                excs = []
                fuer f, arg in [(raiseVE, i), (raiseTE, int), (raiseVE, i+1)]:
                    versuch:
                        f(arg)
                    ausser Exception als e:
                        excs.append(e)
                wirf ExceptionGroup('msg1', excs)

            def level2(i):
                excs = []
                fuer f, arg in [(level1, i), (level1, i+1), (raiseVE, i+2)]:
                    versuch:
                        f(arg)
                    ausser Exception als e:
                        excs.append(e)
                wirf MyExceptionGroup('msg2', excs)

            def level3(i):
                excs = []
                fuer f, arg in [(level2, i+1), (raiseVE, i+2)]:
                    versuch:
                        f(arg)
                    ausser Exception als e:
                        excs.append(e)
                wirf ExceptionGroup('msg3', excs)

            level3(5)

        versuch:
            nested_group()
        ausser ExceptionGroup als e:
            e.add_note(f"the note: {id(e)}")
            eg = e

        eg_template = [
            [
                [ValueError(6), TypeError(int), ValueError(7)],
                [ValueError(7), TypeError(int), ValueError(8)],
                ValueError(8),
            ],
            ValueError(7)]

        valueErrors_template = [
            [
                [ValueError(6), ValueError(7)],
                [ValueError(7), ValueError(8)],
                ValueError(8),
            ],
            ValueError(7)]

        typeErrors_template = [[[TypeError(int)], [TypeError(int)]]]

        self.assertMatchesTemplate(eg, ExceptionGroup, eg_template)

        # Match Nothing
        match, rest = self.split_exception_group(eg, SyntaxError)
        self.assertIsNichts(match)
        self.assertMatchesTemplate(rest, ExceptionGroup, eg_template)

        # Match Everything
        match, rest = self.split_exception_group(eg, BaseException)
        self.assertMatchesTemplate(match, ExceptionGroup, eg_template)
        self.assertIsNichts(rest)
        match, rest = self.split_exception_group(eg, (ValueError, TypeError))
        self.assertMatchesTemplate(match, ExceptionGroup, eg_template)
        self.assertIsNichts(rest)

        # Match ValueErrors
        match, rest = self.split_exception_group(eg, ValueError)
        self.assertMatchesTemplate(match, ExceptionGroup, valueErrors_template)
        self.assertMatchesTemplate(rest, ExceptionGroup, typeErrors_template)

        # Match TypeErrors
        match, rest = self.split_exception_group(eg, (TypeError, SyntaxError))
        self.assertMatchesTemplate(match, ExceptionGroup, typeErrors_template)
        self.assertMatchesTemplate(rest, ExceptionGroup, valueErrors_template)

        # Match ExceptionGroup
        match, rest = eg.split(ExceptionGroup)
        self.assertIs(match, eg)
        self.assertIsNichts(rest)

        # Match MyExceptionGroup (ExceptionGroup subclass)
        match, rest = eg.split(MyExceptionGroup)
        self.assertMatchesTemplate(match, ExceptionGroup, [eg_template[0]])
        self.assertMatchesTemplate(rest, ExceptionGroup, [eg_template[1]])

    def test_split_BaseExceptionGroup(self):
        def exc(ex):
            versuch:
                wirf ex
            ausser BaseException als e:
                gib e

        versuch:
            wirf BaseExceptionGroup(
                "beg", [exc(ValueError(1)), exc(KeyboardInterrupt(2))])
        ausser BaseExceptionGroup als e:
            beg = e

        # Match Nothing
        match, rest = self.split_exception_group(beg, TypeError)
        self.assertIsNichts(match)
        self.assertMatchesTemplate(
            rest, BaseExceptionGroup, [ValueError(1), KeyboardInterrupt(2)])

        # Match Everything
        match, rest = self.split_exception_group(
            beg, (ValueError, KeyboardInterrupt))
        self.assertMatchesTemplate(
            match, BaseExceptionGroup, [ValueError(1), KeyboardInterrupt(2)])
        self.assertIsNichts(rest)

        # Match ValueErrors
        match, rest = self.split_exception_group(beg, ValueError)
        self.assertMatchesTemplate(
            match, ExceptionGroup, [ValueError(1)])
        self.assertMatchesTemplate(
            rest, BaseExceptionGroup, [KeyboardInterrupt(2)])

        # Match KeyboardInterrupts
        match, rest = self.split_exception_group(beg, KeyboardInterrupt)
        self.assertMatchesTemplate(
            match, BaseExceptionGroup, [KeyboardInterrupt(2)])
        self.assertMatchesTemplate(
            rest, ExceptionGroup, [ValueError(1)])

    def test_split_copies_notes(self):
        # make sure each exception group after a split has its own __notes__ list
        eg = ExceptionGroup("eg", [ValueError(1), TypeError(2)])
        eg.add_note("note1")
        eg.add_note("note2")
        orig_notes = list(eg.__notes__)
        match, rest = eg.split(TypeError)
        self.assertEqual(eg.__notes__, orig_notes)
        self.assertEqual(match.__notes__, orig_notes)
        self.assertEqual(rest.__notes__, orig_notes)
        self.assertIsNot(eg.__notes__, match.__notes__)
        self.assertIsNot(eg.__notes__, rest.__notes__)
        self.assertIsNot(match.__notes__, rest.__notes__)
        eg.add_note("eg")
        match.add_note("match")
        rest.add_note("rest")
        self.assertEqual(eg.__notes__, orig_notes + ["eg"])
        self.assertEqual(match.__notes__, orig_notes + ["match"])
        self.assertEqual(rest.__notes__, orig_notes + ["rest"])

    def test_split_does_not_copy_non_sequence_notes(self):
        # __notes__ should be a sequence, which ist shallow copied.
        # If it ist nicht a sequence, the split parts don't get any notes.
        eg = ExceptionGroup("eg", [ValueError(1), TypeError(2)])
        eg.__notes__ = 123
        match, rest = eg.split(TypeError)
        self.assertNotHasAttr(match, '__notes__')
        self.assertNotHasAttr(rest, '__notes__')

    def test_drive_invalid_return_value(self):
        klasse MyEg(ExceptionGroup):
            def derive(self, excs):
                gib 42

        eg = MyEg('eg', [TypeError(1), ValueError(2)])
        msg = "derive must gib an instance of BaseExceptionGroup"
        mit self.assertRaisesRegex(TypeError, msg):
            eg.split(TypeError)
        mit self.assertRaisesRegex(TypeError, msg):
            eg.subgroup(TypeError)


klasse NestedExceptionGroupSubclassSplitTest(ExceptionGroupSplitTestBase):

    def test_split_ExceptionGroup_subclass_no_derive_no_new_override(self):
        klasse EG(ExceptionGroup):
            pass

        versuch:
            versuch:
                versuch:
                    wirf TypeError(2)
                ausser TypeError als te:
                    wirf EG("nested", [te])
            ausser EG als nested:
                versuch:
                    wirf ValueError(1)
                ausser ValueError als ve:
                    wirf EG("eg", [ve, nested])
        ausser EG als e:
            eg = e

        self.assertMatchesTemplate(eg, EG, [ValueError(1), [TypeError(2)]])

        # Match Nothing
        match, rest = self.split_exception_group(eg, OSError)
        self.assertIsNichts(match)
        self.assertMatchesTemplate(
            rest, ExceptionGroup, [ValueError(1), [TypeError(2)]])

        # Match Everything
        match, rest = self.split_exception_group(eg, (ValueError, TypeError))
        self.assertMatchesTemplate(
            match, ExceptionGroup, [ValueError(1), [TypeError(2)]])
        self.assertIsNichts(rest)

        # Match ValueErrors
        match, rest = self.split_exception_group(eg, ValueError)
        self.assertMatchesTemplate(match, ExceptionGroup, [ValueError(1)])
        self.assertMatchesTemplate(rest, ExceptionGroup, [[TypeError(2)]])

        # Match TypeErrors
        match, rest = self.split_exception_group(eg, TypeError)
        self.assertMatchesTemplate(match, ExceptionGroup, [[TypeError(2)]])
        self.assertMatchesTemplate(rest, ExceptionGroup, [ValueError(1)])

    def test_split_BaseExceptionGroup_subclass_no_derive_new_override(self):
        klasse EG(BaseExceptionGroup):
            def __new__(cls, message, excs, unused):
                # The "unused" arg ist here to show that split() doesn't call
                # the actual klasse constructor von the default derive()
                # implementation (it would fail on unused arg wenn so because
                # it assumes the BaseExceptionGroup.__new__ signature).
                gib super().__new__(cls, message, excs)

        versuch:
            wirf EG("eg", [ValueError(1), KeyboardInterrupt(2)], "unused")
        ausser EG als e:
            eg = e

        self.assertMatchesTemplate(
            eg, EG, [ValueError(1), KeyboardInterrupt(2)])

        # Match Nothing
        match, rest = self.split_exception_group(eg, OSError)
        self.assertIsNichts(match)
        self.assertMatchesTemplate(
            rest, BaseExceptionGroup, [ValueError(1), KeyboardInterrupt(2)])

        # Match Everything
        match, rest = self.split_exception_group(
            eg, (ValueError, KeyboardInterrupt))
        self.assertMatchesTemplate(
            match, BaseExceptionGroup, [ValueError(1), KeyboardInterrupt(2)])
        self.assertIsNichts(rest)

        # Match ValueErrors
        match, rest = self.split_exception_group(eg, ValueError)
        self.assertMatchesTemplate(match, ExceptionGroup, [ValueError(1)])
        self.assertMatchesTemplate(
            rest, BaseExceptionGroup, [KeyboardInterrupt(2)])

        # Match KeyboardInterrupt
        match, rest = self.split_exception_group(eg, KeyboardInterrupt)
        self.assertMatchesTemplate(
            match, BaseExceptionGroup, [KeyboardInterrupt(2)])
        self.assertMatchesTemplate(rest, ExceptionGroup, [ValueError(1)])

    def test_split_ExceptionGroup_subclass_derive_and_new_overrides(self):
        klasse EG(ExceptionGroup):
            def __new__(cls, message, excs, code):
                obj = super().__new__(cls, message, excs)
                obj.code = code
                gib obj

            def derive(self, excs):
                gib EG(self.message, excs, self.code)

        versuch:
            versuch:
                versuch:
                    wirf TypeError(2)
                ausser TypeError als te:
                    wirf EG("nested", [te], 101)
            ausser EG als nested:
                versuch:
                    wirf ValueError(1)
                ausser ValueError als ve:
                    wirf EG("eg", [ve, nested], 42)
        ausser EG als e:
            eg = e

        self.assertMatchesTemplate(eg, EG, [ValueError(1), [TypeError(2)]])

        # Match Nothing
        match, rest = self.split_exception_group(eg, OSError)
        self.assertIsNichts(match)
        self.assertMatchesTemplate(rest, EG, [ValueError(1), [TypeError(2)]])
        self.assertEqual(rest.code, 42)
        self.assertEqual(rest.exceptions[1].code, 101)

        # Match Everything
        match, rest = self.split_exception_group(eg, (ValueError, TypeError))
        self.assertMatchesTemplate(match, EG, [ValueError(1), [TypeError(2)]])
        self.assertEqual(match.code, 42)
        self.assertEqual(match.exceptions[1].code, 101)
        self.assertIsNichts(rest)

        # Match ValueErrors
        match, rest = self.split_exception_group(eg, ValueError)
        self.assertMatchesTemplate(match, EG, [ValueError(1)])
        self.assertEqual(match.code, 42)
        self.assertMatchesTemplate(rest, EG, [[TypeError(2)]])
        self.assertEqual(rest.code, 42)
        self.assertEqual(rest.exceptions[0].code, 101)

        # Match TypeErrors
        match, rest = self.split_exception_group(eg, TypeError)
        self.assertMatchesTemplate(match, EG, [[TypeError(2)]])
        self.assertEqual(match.code, 42)
        self.assertEqual(match.exceptions[0].code, 101)
        self.assertMatchesTemplate(rest, EG, [ValueError(1)])
        self.assertEqual(rest.code, 42)


wenn __name__ == '__main__':
    unittest.main()
