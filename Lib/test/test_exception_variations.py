
importiere unittest

klasse ExceptTestCases(unittest.TestCase):
    def test_try_except_else_finally(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        try:
            raise Exception('nyaa!')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)
        self.assertFalsch(hit_else)

    def test_try_except_else_finally_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        try:
            pass
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_else)

    def test_try_except_finally(self):
        hit_except = Falsch
        hit_finally = Falsch

        try:
            raise Exception('yarr!')
        except:
            hit_except = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except_finally_no_exception(self):
        hit_except = Falsch
        hit_finally = Falsch

        try:
            pass
        except:
            hit_except = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except(self):
        hit_except = Falsch

        try:
            raise Exception('ahoy!')
        except:
            hit_except = Wahr

        self.assertWahr(hit_except)

    def test_try_except_no_exception(self):
        hit_except = Falsch

        try:
            pass
        except:
            hit_except = Wahr

        self.assertFalsch(hit_except)

    def test_try_except_else(self):
        hit_except = Falsch
        hit_else = Falsch

        try:
            raise Exception('foo!')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_else)
        self.assertWahr(hit_except)

    def test_try_except_else_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch

        try:
            pass
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_else)

    def test_try_finally_no_exception(self):
        hit_finally = Falsch

        try:
            pass
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_finally)

    def test_nested(self):
        hit_finally = Falsch
        hit_inner_except = Falsch
        hit_inner_finally = Falsch

        try:
            try:
                raise Exception('inner exception')
            except:
                hit_inner_except = Wahr
            finally:
                hit_inner_finally = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_inner_except)
        self.assertWahr(hit_inner_finally)
        self.assertWahr(hit_finally)

    def test_nested_else(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch

        try:
            try:
                pass
            except:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            raise Exception('outer exception')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)

    def test_nested_exception_in_except(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch

        try:
            try:
                raise Exception('inner exception')
            except:
                hit_inner_except = Wahr
                raise Exception('outer exception')
            sonst:
                hit_inner_else = Wahr
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_inner_except)
        self.assertFalsch(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)

    def test_nested_exception_in_else(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch

        try:
            try:
                pass
            except:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr
                raise Exception('outer exception')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)

    def test_nested_exception_in_finally_no_exception(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch
        hit_inner_finally = Falsch

        try:
            try:
                pass
            except:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr
            finally:
                hit_inner_finally = Wahr
                raise Exception('outer exception')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertWahr(hit_inner_finally)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)

    def test_nested_exception_in_finally_with_exception(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch
        hit_inner_finally = Falsch

        try:
            try:
                raise Exception('inner exception')
            except:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr
            finally:
                hit_inner_finally = Wahr
                raise Exception('outer exception')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr


        self.assertWahr(hit_inner_except)
        self.assertFalsch(hit_inner_else)
        self.assertWahr(hit_inner_finally)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)


klasse ExceptStarTestCases(unittest.TestCase):
    def test_try_except_else_finally(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        try:
            raise Exception('nyaa!')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)
        self.assertFalsch(hit_else)

    def test_try_except_else_finally_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        try:
            pass
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_else)

    def test_try_except_finally(self):
        hit_except = Falsch
        hit_finally = Falsch

        try:
            raise Exception('yarr!')
        except* BaseException:
            hit_except = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except_finally_no_exception(self):
        hit_except = Falsch
        hit_finally = Falsch

        try:
            pass
        except* BaseException:
            hit_except = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except(self):
        hit_except = Falsch

        try:
            raise Exception('ahoy!')
        except* BaseException:
            hit_except = Wahr

        self.assertWahr(hit_except)

    def test_try_except_no_exception(self):
        hit_except = Falsch

        try:
            pass
        except* BaseException:
            hit_except = Wahr

        self.assertFalsch(hit_except)

    def test_try_except_else(self):
        hit_except = Falsch
        hit_else = Falsch

        try:
            raise Exception('foo!')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_else)
        self.assertWahr(hit_except)

    def test_try_except_else_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch

        try:
            pass
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_else)

    def test_try_finally_no_exception(self):
        hit_finally = Falsch

        try:
            pass
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_finally)

    def test_nested(self):
        hit_finally = Falsch
        hit_inner_except = Falsch
        hit_inner_finally = Falsch

        try:
            try:
                raise Exception('inner exception')
            except* BaseException:
                hit_inner_except = Wahr
            finally:
                hit_inner_finally = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_inner_except)
        self.assertWahr(hit_inner_finally)
        self.assertWahr(hit_finally)

    def test_nested_else(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch

        try:
            try:
                pass
            except* BaseException:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            raise Exception('outer exception')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)

    def test_nested_mixed1(self):
        hit_except = Falsch
        hit_finally = Falsch
        hit_inner_except = Falsch
        hit_inner_finally = Falsch

        try:
            try:
                raise Exception('inner exception')
            except* BaseException:
                hit_inner_except = Wahr
            finally:
                hit_inner_finally = Wahr
        except:
            hit_except = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_inner_except)
        self.assertWahr(hit_inner_finally)
        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)

    def test_nested_mixed2(self):
        hit_except = Falsch
        hit_finally = Falsch
        hit_inner_except = Falsch
        hit_inner_finally = Falsch

        try:
            try:
                raise Exception('inner exception')
            except:
                hit_inner_except = Wahr
            finally:
                hit_inner_finally = Wahr
        except* BaseException:
            hit_except = Wahr
        finally:
            hit_finally = Wahr

        self.assertWahr(hit_inner_except)
        self.assertWahr(hit_inner_finally)
        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)


    def test_nested_else_mixed1(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch

        try:
            try:
                pass
            except* BaseException:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            raise Exception('outer exception')
        except:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)

    def test_nested_else_mixed2(self):
        hit_else = Falsch
        hit_finally = Falsch
        hit_except = Falsch
        hit_inner_except = Falsch
        hit_inner_else = Falsch

        try:
            try:
                pass
            except:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            raise Exception('outer exception')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        finally:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)


wenn __name__ == '__main__':
    unittest.main()
