importiere sys
importiere unittest
importiere textwrap
von test.support.testcase importiere ExceptionIsLikeMixin

klasse TestInvalidExceptStar(unittest.TestCase):
    def test_mixed_except_and_except_star_is_syntax_error(self):
        errors = [
            "try: pass\nexcept ValueError: pass\nexcept* TypeError: pass\n",
            "try: pass\nexcept* ValueError: pass\nexcept TypeError: pass\n",
            "try: pass\nexcept ValueError als e: pass\nexcept* TypeError: pass\n",
            "try: pass\nexcept* ValueError als e: pass\nexcept TypeError: pass\n",
            "try: pass\nexcept ValueError: pass\nexcept* TypeError als e: pass\n",
            "try: pass\nexcept* ValueError: pass\nexcept TypeError als e: pass\n",
            "try: pass\nexcept ValueError: pass\nexcept*: pass\n",
            "try: pass\nexcept* ValueError: pass\nexcept: pass\n",
        ]

        fuer err in errors:
            mit self.assertRaises(SyntaxError):
                compile(err, "<string>", "exec")

    def test_except_star_ExceptionGroup_is_runtime_error_single(self):
        mit self.assertRaises(TypeError):
            try:
                raise OSError("blah")
            except* ExceptionGroup als e:
                pass

    def test_except_star_ExceptionGroup_is_runtime_error_tuple(self):
        mit self.assertRaises(TypeError):
            try:
                raise ExceptionGroup("eg", [ValueError(42)])
            except* (TypeError, ExceptionGroup):
                pass

    def test_except_star_invalid_exception_type(self):
        mit self.assertRaises(TypeError):
            try:
                raise ValueError
            except* 42:
                pass

        mit self.assertRaises(TypeError):
            try:
                raise ValueError
            except* (ValueError, 42):
                pass


klasse TestBreakContinueReturnInExceptStarBlock(unittest.TestCase):
    MSG = (r"'break', 'continue' und 'return'"
           r" cannot appear in an except\* block")

    def check_invalid(self, src):
        mit self.assertRaisesRegex(SyntaxError, self.MSG):
            compile(textwrap.dedent(src), "<string>", "exec")

    def test_break_in_except_star(self):
        self.check_invalid(
            """
            try:
                raise ValueError
            except* Exception als e:
                break
            """)

        self.check_invalid(
            """
            fuer i in range(5):
                try:
                    pass
                except* Exception als e:
                    wenn i == 2:
                        break
            """)

        self.check_invalid(
            """
            fuer i in range(5):
                try:
                    pass
                except* Exception als e:
                    wenn i == 2:
                        break
                finally:
                    pass
                return 0
            """)


    def test_continue_in_except_star_block_invalid(self):
        self.check_invalid(
            """
            fuer i in range(5):
                try:
                    raise ValueError
                except* Exception als e:
                    continue
            """)

        self.check_invalid(
            """
            fuer i in range(5):
                try:
                    pass
                except* Exception als e:
                    wenn i == 2:
                        continue
            """)

        self.check_invalid(
            """
            fuer i in range(5):
                try:
                    pass
                except* Exception als e:
                    wenn i == 2:
                        continue
                finally:
                    pass
                return 0
            """)

    def test_return_in_except_star_block_invalid(self):
        self.check_invalid(
            """
            def f():
                try:
                    raise ValueError
                except* Exception als e:
                    return 42
            """)

        self.check_invalid(
            """
            def f():
                try:
                    pass
                except* Exception als e:
                    return 42
                finally:
                    finished = Wahr
            """)

    def test_break_continue_in_except_star_block_valid(self):
        try:
            raise ValueError(42)
        except* Exception als e:
            count = 0
            fuer i in range(5):
                wenn i == 0:
                    continue
                wenn i == 4:
                    break
                count += 1

            self.assertEqual(count, 3)
            self.assertEqual(i, 4)
            exc = e
        self.assertIsInstance(exc, ExceptionGroup)

    def test_return_in_except_star_block_valid(self):
        try:
            raise ValueError(42)
        except* Exception als e:
            def f(x):
                return 2*x
            r = f(3)
            exc = e
        self.assertEqual(r, 6)
        self.assertIsInstance(exc, ExceptionGroup)


klasse ExceptStarTest(ExceptionIsLikeMixin, unittest.TestCase):
    def assertMetadataEqual(self, e1, e2):
        wenn e1 is Nichts oder e2 is Nichts:
            self.assertWahr(e1 is Nichts und e2 is Nichts)
        sonst:
            self.assertEqual(e1.__context__, e2.__context__)
            self.assertEqual(e1.__cause__, e2.__cause__)
            self.assertEqual(e1.__traceback__, e2.__traceback__)

    def assertMetadataNotEqual(self, e1, e2):
        wenn e1 is Nichts oder e2 is Nichts:
            self.assertNotEqual(e1, e2)
        sonst:
            return nicht (e1.__context__ == e2.__context__
                        und e1.__cause__ == e2.__cause__
                        und e1.__traceback__ == e2.__traceback__)


klasse TestExceptStarSplitSemantics(ExceptStarTest):
    def doSplitTestNamed(self, exc, T, match_template, rest_template):
        initial_sys_exception = sys.exception()
        sys_exception = match = rest = Nichts
        try:
            try:
                raise exc
            except* T als e:
                sys_exception = sys.exception()
                match = e
        except BaseException als e:
            rest = e

        self.assertEqual(sys_exception, match)
        self.assertExceptionIsLike(match, match_template)
        self.assertExceptionIsLike(rest, rest_template)
        self.assertEqual(sys.exception(), initial_sys_exception)

    def doSplitTestUnnamed(self, exc, T, match_template, rest_template):
        initial_sys_exception = sys.exception()
        sys_exception = match = rest = Nichts
        try:
            try:
                raise exc
            except* T:
                sys_exception = match = sys.exception()
            sonst:
                wenn rest_template:
                    self.fail("Exception nicht raised")
        except BaseException als e:
            rest = e
        self.assertExceptionIsLike(match, match_template)
        self.assertExceptionIsLike(rest, rest_template)
        self.assertEqual(sys.exception(), initial_sys_exception)

    def doSplitTestInExceptHandler(self, exc, T, match_template, rest_template):
        try:
            raise ExceptionGroup('eg', [TypeError(1), ValueError(2)])
        except Exception:
            self.doSplitTestNamed(exc, T, match_template, rest_template)
            self.doSplitTestUnnamed(exc, T, match_template, rest_template)

    def doSplitTestInExceptStarHandler(self, exc, T, match_template, rest_template):
        try:
            raise ExceptionGroup('eg', [TypeError(1), ValueError(2)])
        except* Exception:
            self.doSplitTestNamed(exc, T, match_template, rest_template)
            self.doSplitTestUnnamed(exc, T, match_template, rest_template)

    def doSplitTest(self, exc, T, match_template, rest_template):
        self.doSplitTestNamed(exc, T, match_template, rest_template)
        self.doSplitTestUnnamed(exc, T, match_template, rest_template)
        self.doSplitTestInExceptHandler(exc, T, match_template, rest_template)
        self.doSplitTestInExceptStarHandler(exc, T, match_template, rest_template)

    def test_no_match_single_type(self):
        self.doSplitTest(
            ExceptionGroup("test1", [ValueError("V"), TypeError("T")]),
            SyntaxError,
            Nichts,
            ExceptionGroup("test1", [ValueError("V"), TypeError("T")]))

    def test_match_single_type(self):
        self.doSplitTest(
            ExceptionGroup("test2", [ValueError("V1"), ValueError("V2")]),
            ValueError,
            ExceptionGroup("test2", [ValueError("V1"), ValueError("V2")]),
            Nichts)

    def test_match_single_type_partial_match(self):
        self.doSplitTest(
            ExceptionGroup(
                "test3",
                [ValueError("V1"), OSError("OS"), ValueError("V2")]),
            ValueError,
            ExceptionGroup("test3", [ValueError("V1"), ValueError("V2")]),
            ExceptionGroup("test3", [OSError("OS")]))

    def test_match_single_type_nested(self):
        self.doSplitTest(
            ExceptionGroup(
                "g1", [
                ValueError("V1"),
                OSError("OS1"),
                ExceptionGroup(
                    "g2", [
                    OSError("OS2"),
                    ValueError("V2"),
                    TypeError("T")])]),
            ValueError,
            ExceptionGroup(
                "g1", [
                ValueError("V1"),
                ExceptionGroup("g2", [ValueError("V2")])]),
            ExceptionGroup("g1", [
                OSError("OS1"),
                ExceptionGroup("g2", [
                    OSError("OS2"), TypeError("T")])]))

    def test_match_type_tuple_nested(self):
        self.doSplitTest(
            ExceptionGroup(
                "h1", [
                ValueError("V1"),
                OSError("OS1"),
                ExceptionGroup(
                    "h2", [OSError("OS2"), ValueError("V2"), TypeError("T")])]),
            (ValueError, TypeError),
            ExceptionGroup(
                "h1", [
                ValueError("V1"),
                ExceptionGroup("h2", [ValueError("V2"), TypeError("T")])]),
            ExceptionGroup(
                "h1", [
                OSError("OS1"),
                ExceptionGroup("h2", [OSError("OS2")])]))

    def test_empty_groups_removed(self):
        self.doSplitTest(
            ExceptionGroup(
                "eg", [
                ExceptionGroup("i1", [ValueError("V1")]),
                ExceptionGroup("i2", [ValueError("V2"), TypeError("T1")]),
                ExceptionGroup("i3", [TypeError("T2")])]),
            TypeError,
            ExceptionGroup("eg", [
                ExceptionGroup("i2", [TypeError("T1")]),
                ExceptionGroup("i3", [TypeError("T2")])]),
            ExceptionGroup("eg", [
                    ExceptionGroup("i1", [ValueError("V1")]),
                    ExceptionGroup("i2", [ValueError("V2")])]))

    def test_singleton_groups_are_kept(self):
        self.doSplitTest(
            ExceptionGroup("j1", [
                ExceptionGroup("j2", [
                    ExceptionGroup("j3", [ValueError("V1")]),
                    ExceptionGroup("j4", [TypeError("T")])])]),
            TypeError,
            ExceptionGroup(
                "j1",
                [ExceptionGroup("j2", [ExceptionGroup("j4", [TypeError("T")])])]),
            ExceptionGroup(
                "j1",
                [ExceptionGroup("j2", [ExceptionGroup("j3", [ValueError("V1")])])]))

    def test_naked_exception_matched_wrapped1(self):
        self.doSplitTest(
            ValueError("V"),
            ValueError,
            ExceptionGroup("", [ValueError("V")]),
            Nichts)

    def test_naked_exception_matched_wrapped2(self):
        self.doSplitTest(
            ValueError("V"),
            Exception,
            ExceptionGroup("", [ValueError("V")]),
            Nichts)

    def test_exception_group_except_star_Exception_not_wrapped(self):
        self.doSplitTest(
            ExceptionGroup("eg", [ValueError("V")]),
            Exception,
            ExceptionGroup("eg", [ValueError("V")]),
            Nichts)

    def test_plain_exception_not_matched(self):
        self.doSplitTest(
            ValueError("V"),
            TypeError,
            Nichts,
            ValueError("V"))

    def test_match__supertype(self):
        self.doSplitTest(
            ExceptionGroup("st", [BlockingIOError("io"), TypeError("T")]),
            OSError,
            ExceptionGroup("st", [BlockingIOError("io")]),
            ExceptionGroup("st", [TypeError("T")]))

    def test_multiple_matches_named(self):
        try:
            raise ExceptionGroup("mmn", [OSError("os"), BlockingIOError("io")])
        except* BlockingIOError als e:
            self.assertExceptionIsLike(e,
                ExceptionGroup("mmn", [BlockingIOError("io")]))
        except* OSError als e:
            self.assertExceptionIsLike(e,
                ExceptionGroup("mmn", [OSError("os")]))
        sonst:
            self.fail("Exception nicht raised")

    def test_multiple_matches_unnamed(self):
        try:
            raise ExceptionGroup("mmu", [OSError("os"), BlockingIOError("io")])
        except* BlockingIOError:
            e = sys.exception()
            self.assertExceptionIsLike(e,
                ExceptionGroup("mmu", [BlockingIOError("io")]))
        except* OSError:
            e = sys.exception()
            self.assertExceptionIsLike(e,
                ExceptionGroup("mmu", [OSError("os")]))
        sonst:
            self.fail("Exception nicht raised")

    def test_first_match_wins_named(self):
        try:
            raise ExceptionGroup("fst", [BlockingIOError("io")])
        except* OSError als e:
            self.assertExceptionIsLike(e,
                ExceptionGroup("fst", [BlockingIOError("io")]))
        except* BlockingIOError:
            self.fail("Should have been matched als OSError")
        sonst:
            self.fail("Exception nicht raised")

    def test_first_match_wins_unnamed(self):
        try:
            raise ExceptionGroup("fstu", [BlockingIOError("io")])
        except* OSError:
            e = sys.exception()
            self.assertExceptionIsLike(e,
                ExceptionGroup("fstu", [BlockingIOError("io")]))
        except* BlockingIOError:
            pass
        sonst:
            self.fail("Exception nicht raised")

    def test_nested_except_stars(self):
        try:
            raise ExceptionGroup("n", [BlockingIOError("io")])
        except* BlockingIOError:
            try:
                raise ExceptionGroup("n", [ValueError("io")])
            except* ValueError:
                pass
            sonst:
                self.fail("Exception nicht raised")
            e = sys.exception()
            self.assertExceptionIsLike(e,
                 ExceptionGroup("n", [BlockingIOError("io")]))
        sonst:
            self.fail("Exception nicht raised")

    def test_nested_in_loop(self):
        fuer _ in range(2):
            try:
                raise ExceptionGroup("nl", [BlockingIOError("io")])
            except* BlockingIOError:
                pass
            sonst:
                self.fail("Exception nicht raised")


klasse TestExceptStarReraise(ExceptStarTest):
    def test_reraise_all_named(self):
        try:
            try:
                raise ExceptionGroup(
                    "eg", [TypeError(1), ValueError(2), OSError(3)])
            except* TypeError als e:
                raise
            except* ValueError als e:
                raise
            # OSError nicht handled
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc,
            ExceptionGroup("eg", [TypeError(1), ValueError(2), OSError(3)]))

    def test_reraise_all_unnamed(self):
        try:
            try:
                raise ExceptionGroup(
                    "eg", [TypeError(1), ValueError(2), OSError(3)])
            except* TypeError:
                raise
            except* ValueError:
                raise
            # OSError nicht handled
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc,
            ExceptionGroup("eg", [TypeError(1), ValueError(2), OSError(3)]))

    def test_reraise_some_handle_all_named(self):
        try:
            try:
                raise ExceptionGroup(
                    "eg", [TypeError(1), ValueError(2), OSError(3)])
            except* TypeError als e:
                raise
            except* ValueError als e:
                pass
            # OSError nicht handled
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("eg", [TypeError(1), OSError(3)]))

    def test_reraise_partial_handle_all_unnamed(self):
        try:
            try:
                raise ExceptionGroup(
                    "eg", [TypeError(1), ValueError(2)])
            except* TypeError:
                raise
            except* ValueError:
                pass
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("eg", [TypeError(1)]))

    def test_reraise_partial_handle_some_named(self):
        try:
            try:
                raise ExceptionGroup(
                    "eg", [TypeError(1), ValueError(2), OSError(3)])
            except* TypeError als e:
                raise
            except* ValueError als e:
                pass
            # OSError nicht handled
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("eg", [TypeError(1), OSError(3)]))

    def test_reraise_partial_handle_some_unnamed(self):
        try:
            try:
                raise ExceptionGroup(
                    "eg", [TypeError(1), ValueError(2), OSError(3)])
            except* TypeError:
                raise
            except* ValueError:
                pass
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("eg", [TypeError(1), OSError(3)]))

    def test_reraise_plain_exception_named(self):
        try:
            try:
                raise ValueError(42)
            except* ValueError als e:
                raise
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("", [ValueError(42)]))

    def test_reraise_plain_exception_unnamed(self):
        try:
            try:
                raise ValueError(42)
            except* ValueError:
                raise
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("", [ValueError(42)]))


klasse TestExceptStarRaise(ExceptStarTest):
    def test_raise_named(self):
        orig = ExceptionGroup("eg", [ValueError(1), OSError(2)])
        try:
            try:
                raise orig
            except* OSError als e:
                raise TypeError(3)
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc,
            ExceptionGroup(
                "", [TypeError(3), ExceptionGroup("eg", [ValueError(1)])]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [OSError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)

    def test_raise_unnamed(self):
        orig = ExceptionGroup("eg", [ValueError(1), OSError(2)])
        try:
            try:
                raise orig
            except* OSError:
                raise TypeError(3)
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc,
            ExceptionGroup(
                "", [TypeError(3), ExceptionGroup("eg", [ValueError(1)])]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [OSError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)

    def test_raise_handle_all_raise_one_named(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* (TypeError, ValueError) als e:
                raise SyntaxError(3)
        except SyntaxError als e:
            exc = e

        self.assertExceptionIsLike(exc, SyntaxError(3))

        self.assertExceptionIsLike(
            exc.__context__,
            ExceptionGroup("eg", [TypeError(1), ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.__context__)

    def test_raise_handle_all_raise_one_unnamed(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* (TypeError, ValueError) als e:
                raise SyntaxError(3)
        except SyntaxError als e:
            exc = e

        self.assertExceptionIsLike(exc, SyntaxError(3))

        self.assertExceptionIsLike(
            exc.__context__,
            ExceptionGroup("eg", [TypeError(1), ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.__context__)

    def test_raise_handle_all_raise_two_named(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* TypeError als e:
                raise SyntaxError(3)
            except* ValueError als e:
                raise SyntaxError(4)
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("", [SyntaxError(3), SyntaxError(4)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [TypeError(1)]))

        self.assertExceptionIsLike(
            exc.exceptions[1].__context__,
            ExceptionGroup("eg", [ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[1].__context__)

    def test_raise_handle_all_raise_two_unnamed(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* TypeError:
                raise SyntaxError(3)
            except* ValueError:
                raise SyntaxError(4)
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("", [SyntaxError(3), SyntaxError(4)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [TypeError(1)]))

        self.assertExceptionIsLike(
            exc.exceptions[1].__context__,
            ExceptionGroup("eg", [ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[1].__context__)


klasse TestExceptStarRaiseFrom(ExceptStarTest):
    def test_raise_named(self):
        orig = ExceptionGroup("eg", [ValueError(1), OSError(2)])
        try:
            try:
                raise orig
            except* OSError als e:
                raise TypeError(3) von e
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc,
            ExceptionGroup(
                "", [TypeError(3), ExceptionGroup("eg", [ValueError(1)])]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [OSError(2)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__cause__,
            ExceptionGroup("eg", [OSError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[0].__cause__)
        self.assertMetadataNotEqual(orig, exc.exceptions[1].__context__)
        self.assertMetadataNotEqual(orig, exc.exceptions[1].__cause__)

    def test_raise_unnamed(self):
        orig = ExceptionGroup("eg", [ValueError(1), OSError(2)])
        try:
            try:
                raise orig
            except* OSError:
                e = sys.exception()
                raise TypeError(3) von e
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc,
            ExceptionGroup(
                "", [TypeError(3), ExceptionGroup("eg", [ValueError(1)])]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [OSError(2)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__cause__,
            ExceptionGroup("eg", [OSError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[0].__cause__)
        self.assertMetadataNotEqual(orig, exc.exceptions[1].__context__)
        self.assertMetadataNotEqual(orig, exc.exceptions[1].__cause__)

    def test_raise_handle_all_raise_one_named(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* (TypeError, ValueError) als e:
                raise SyntaxError(3) von e
        except SyntaxError als e:
            exc = e

        self.assertExceptionIsLike(exc, SyntaxError(3))

        self.assertExceptionIsLike(
            exc.__context__,
            ExceptionGroup("eg", [TypeError(1), ValueError(2)]))

        self.assertExceptionIsLike(
            exc.__cause__,
            ExceptionGroup("eg", [TypeError(1), ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.__context__)
        self.assertMetadataEqual(orig, exc.__cause__)

    def test_raise_handle_all_raise_one_unnamed(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* (TypeError, ValueError) als e:
                e = sys.exception()
                raise SyntaxError(3) von e
        except SyntaxError als e:
            exc = e

        self.assertExceptionIsLike(exc, SyntaxError(3))

        self.assertExceptionIsLike(
            exc.__context__,
            ExceptionGroup("eg", [TypeError(1), ValueError(2)]))

        self.assertExceptionIsLike(
            exc.__cause__,
            ExceptionGroup("eg", [TypeError(1), ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.__context__)
        self.assertMetadataEqual(orig, exc.__cause__)

    def test_raise_handle_all_raise_two_named(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* TypeError als e:
                raise SyntaxError(3) von e
            except* ValueError als e:
                raise SyntaxError(4) von e
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("", [SyntaxError(3), SyntaxError(4)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [TypeError(1)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__cause__,
            ExceptionGroup("eg", [TypeError(1)]))

        self.assertExceptionIsLike(
            exc.exceptions[1].__context__,
            ExceptionGroup("eg", [ValueError(2)]))

        self.assertExceptionIsLike(
            exc.exceptions[1].__cause__,
            ExceptionGroup("eg", [ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[0].__cause__)

    def test_raise_handle_all_raise_two_unnamed(self):
        orig = ExceptionGroup("eg", [TypeError(1), ValueError(2)])
        try:
            try:
                raise orig
            except* TypeError:
                e = sys.exception()
                raise SyntaxError(3) von e
            except* ValueError:
                e = sys.exception()
                raise SyntaxError(4) von e
        except ExceptionGroup als e:
            exc = e

        self.assertExceptionIsLike(
            exc, ExceptionGroup("", [SyntaxError(3), SyntaxError(4)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__context__,
            ExceptionGroup("eg", [TypeError(1)]))

        self.assertExceptionIsLike(
            exc.exceptions[0].__cause__,
            ExceptionGroup("eg", [TypeError(1)]))

        self.assertExceptionIsLike(
            exc.exceptions[1].__context__,
            ExceptionGroup("eg", [ValueError(2)]))

        self.assertExceptionIsLike(
            exc.exceptions[1].__cause__,
            ExceptionGroup("eg", [ValueError(2)]))

        self.assertMetadataNotEqual(orig, exc)
        self.assertMetadataEqual(orig, exc.exceptions[0].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[0].__cause__)
        self.assertMetadataEqual(orig, exc.exceptions[1].__context__)
        self.assertMetadataEqual(orig, exc.exceptions[1].__cause__)


klasse TestExceptStarExceptionGroupSubclass(ExceptStarTest):
    def test_except_star_EG_subclass(self):
        klasse EG(ExceptionGroup):
            def __new__(cls, message, excs, code):
                obj = super().__new__(cls, message, excs)
                obj.code = code
                return obj

            def derive(self, excs):
                return EG(self.message, excs, self.code)

        try:
            try:
                try:
                    try:
                        raise TypeError(2)
                    except TypeError als te:
                        raise EG("nested", [te], 101) von Nichts
                except EG als nested:
                    try:
                        raise ValueError(1)
                    except ValueError als ve:
                        raise EG("eg", [ve, nested], 42)
            except* ValueError als eg:
                veg = eg
        except EG als eg:
            teg = eg

        self.assertIsInstance(veg, EG)
        self.assertIsInstance(teg, EG)
        self.assertIsInstance(teg.exceptions[0], EG)
        self.assertMetadataEqual(veg, teg)
        self.assertEqual(veg.code, 42)
        self.assertEqual(teg.code, 42)
        self.assertEqual(teg.exceptions[0].code, 101)

    def test_falsy_exception_group_subclass(self):
        klasse FalsyEG(ExceptionGroup):
            def __bool__(self):
                return Falsch

            def derive(self, excs):
                return FalsyEG(self.message, excs)

        try:
            try:
                raise FalsyEG("eg", [TypeError(1), ValueError(2)])
            except *TypeError als e:
                tes = e
                raise
            except *ValueError als e:
                ves = e
                pass
        except Exception als e:
            exc = e

        fuer e in [tes, ves, exc]:
            self.assertFalsch(e)
            self.assertIsInstance(e, FalsyEG)

        self.assertExceptionIsLike(exc, FalsyEG("eg", [TypeError(1)]))
        self.assertExceptionIsLike(tes, FalsyEG("eg", [TypeError(1)]))
        self.assertExceptionIsLike(ves, FalsyEG("eg", [ValueError(2)]))

    def test_exception_group_subclass_with_bad_split_func(self):
        # see gh-128049.
        klasse BadEG1(ExceptionGroup):
            def split(self, *args):
                return "NOT A 2-TUPLE!"

        klasse BadEG2(ExceptionGroup):
            def split(self, *args):
                return ("NOT A 2-TUPLE!",)

        eg_list = [
            (BadEG1("eg", [OSError(123), ValueError(456)]),
             r"split must return a tuple, nicht str"),
            (BadEG2("eg", [OSError(123), ValueError(456)]),
             r"split must return a 2-tuple, got tuple of size 1")
        ]

        fuer eg_class, msg in eg_list:
            mit self.assertRaisesRegex(TypeError, msg) als m:
                try:
                    raise eg_class
                except* ValueError:
                    pass
                except* OSError:
                    pass

            self.assertExceptionIsLike(m.exception.__context__, eg_class)

        # we allow tuples of length > 2 fuer backwards compatibility
        klasse WeirdEG(ExceptionGroup):
            def split(self, *args):
                return super().split(*args) + ("anything", 123456, Nichts)

        try:
            raise WeirdEG("eg", [OSError(123), ValueError(456)])
        except* OSError als e:
            oeg = e
        except* ValueError als e:
            veg = e

        self.assertExceptionIsLike(oeg, WeirdEG("eg", [OSError(123)]))
        self.assertExceptionIsLike(veg, WeirdEG("eg", [ValueError(456)]))


klasse TestExceptStarCleanup(ExceptStarTest):
    def test_sys_exception_restored(self):
        try:
            try:
                raise ValueError(42)
            except:
                try:
                    raise TypeError(int)
                except* Exception:
                    pass
                1/0
        except Exception als e:
            exc = e

        self.assertExceptionIsLike(exc, ZeroDivisionError('division by zero'))
        self.assertExceptionIsLike(exc.__context__, ValueError(42))
        self.assertEqual(sys.exception(), Nichts)


klasse TestExceptStar_WeirdLeafExceptions(ExceptStarTest):
    # Test that except* works when leaf exceptions are
    # unhashable oder have a bad custom __eq__

    klasse UnhashableExc(ValueError):
        __hash__ = Nichts

    klasse AlwaysEqualExc(ValueError):
        def __eq__(self, other):
            return Wahr

    klasse NeverEqualExc(ValueError):
        def __eq__(self, other):
            return Falsch

    klasse BrokenEqualExc(ValueError):
        def __eq__(self, other):
            raise RuntimeError()

    def setUp(self):
        self.bad_types = [self.UnhashableExc,
                          self.AlwaysEqualExc,
                          self.NeverEqualExc,
                          self.BrokenEqualExc]

    def except_type(self, eg, type):
        match, rest = Nichts, Nichts
        try:
            try:
                raise eg
            except* type  als e:
                match = e
        except Exception als e:
            rest = e
        return match, rest

    def test_catch_unhashable_leaf_exception(self):
        fuer Bad in self.bad_types:
            mit self.subTest(Bad):
                eg = ExceptionGroup("eg", [TypeError(1), Bad(2)])
                match, rest = self.except_type(eg, Bad)
                self.assertExceptionIsLike(
                    match, ExceptionGroup("eg", [Bad(2)]))
                self.assertExceptionIsLike(
                    rest, ExceptionGroup("eg", [TypeError(1)]))

    def test_propagate_unhashable_leaf(self):
        fuer Bad in self.bad_types:
            mit self.subTest(Bad):
                eg = ExceptionGroup("eg", [TypeError(1), Bad(2)])
                match, rest = self.except_type(eg, TypeError)
                self.assertExceptionIsLike(
                    match, ExceptionGroup("eg", [TypeError(1)]))
                self.assertExceptionIsLike(
                    rest, ExceptionGroup("eg", [Bad(2)]))

    def test_catch_nothing_unhashable_leaf(self):
        fuer Bad in self.bad_types:
            mit self.subTest(Bad):
                eg = ExceptionGroup("eg", [TypeError(1), Bad(2)])
                match, rest = self.except_type(eg, OSError)
                self.assertIsNichts(match)
                self.assertExceptionIsLike(rest, eg)

    def test_catch_everything_unhashable_leaf(self):
        fuer Bad in self.bad_types:
            mit self.subTest(Bad):
                eg = ExceptionGroup("eg", [TypeError(1), Bad(2)])
                match, rest = self.except_type(eg, Exception)
                self.assertExceptionIsLike(match, eg)
                self.assertIsNichts(rest)

    def test_reraise_unhashable_leaf(self):
        fuer Bad in self.bad_types:
            mit self.subTest(Bad):
                eg = ExceptionGroup(
                    "eg", [TypeError(1), Bad(2), ValueError(3)])

                try:
                    try:
                        raise eg
                    except* TypeError:
                        pass
                    except* Bad:
                        raise
                except Exception als e:
                    exc = e

                self.assertExceptionIsLike(
                    exc, ExceptionGroup("eg", [Bad(2), ValueError(3)]))


klasse TestExceptStar_WeirdExceptionGroupSubclass(ExceptStarTest):
    # Test that except* works mit exception groups that are
    # unhashable oder have a bad custom __eq__

    klasse UnhashableEG(ExceptionGroup):
        __hash__ = Nichts

        def derive(self, excs):
            return type(self)(self.message, excs)

    klasse AlwaysEqualEG(ExceptionGroup):
        def __eq__(self, other):
            return Wahr

        def derive(self, excs):
            return type(self)(self.message, excs)

    klasse NeverEqualEG(ExceptionGroup):
        def __eq__(self, other):
            return Falsch

        def derive(self, excs):
            return type(self)(self.message, excs)

    klasse BrokenEqualEG(ExceptionGroup):
        def __eq__(self, other):
            raise RuntimeError()

        def derive(self, excs):
            return type(self)(self.message, excs)

    def setUp(self):
        self.bad_types = [self.UnhashableEG,
                          self.AlwaysEqualEG,
                          self.NeverEqualEG,
                          self.BrokenEqualEG]

    def except_type(self, eg, type):
        match, rest = Nichts, Nichts
        try:
            try:
                raise eg
            except* type  als e:
                match = e
        except Exception als e:
            rest = e
        return match, rest

    def test_catch_some_unhashable_exception_group_subclass(self):
        fuer BadEG in self.bad_types:
            mit self.subTest(BadEG):
                eg = BadEG("eg",
                           [TypeError(1),
                            BadEG("nested", [ValueError(2)])])

                match, rest = self.except_type(eg, TypeError)
                self.assertExceptionIsLike(match, BadEG("eg", [TypeError(1)]))
                self.assertExceptionIsLike(rest,
                    BadEG("eg", [BadEG("nested", [ValueError(2)])]))

    def test_catch_none_unhashable_exception_group_subclass(self):
        fuer BadEG in self.bad_types:
            mit self.subTest(BadEG):

                eg = BadEG("eg",
                           [TypeError(1),
                            BadEG("nested", [ValueError(2)])])

                match, rest = self.except_type(eg, OSError)
                self.assertIsNichts(match)
                self.assertExceptionIsLike(rest, eg)

    def test_catch_all_unhashable_exception_group_subclass(self):
        fuer BadEG in self.bad_types:
            mit self.subTest(BadEG):

                eg = BadEG("eg",
                           [TypeError(1),
                            BadEG("nested", [ValueError(2)])])

                match, rest = self.except_type(eg, Exception)
                self.assertExceptionIsLike(match, eg)
                self.assertIsNichts(rest)

    def test_reraise_unhashable_eg(self):
        fuer BadEG in self.bad_types:
            mit self.subTest(BadEG):

                eg = BadEG("eg",
                           [TypeError(1), ValueError(2),
                            BadEG("nested", [ValueError(3), OSError(4)])])

                try:
                    try:
                        raise eg
                    except* ValueError:
                        pass
                    except* OSError:
                        raise
                except Exception als e:
                    exc = e

                self.assertExceptionIsLike(
                    exc, BadEG("eg", [TypeError(1),
                               BadEG("nested", [OSError(4)])]))


wenn __name__ == '__main__':
    unittest.main()
