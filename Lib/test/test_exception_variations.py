
importiere unittest

klasse ExceptTestCases(unittest.TestCase):
    def test_try_except_else_finally(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        versuch:
            wirf Exception('nyaa!')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)
        self.assertFalsch(hit_else)

    def test_try_except_else_finally_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        versuch:
            pass
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_else)

    def test_try_except_finally(self):
        hit_except = Falsch
        hit_finally = Falsch

        versuch:
            wirf Exception('yarr!')
        ausser:
            hit_except = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except_finally_no_exception(self):
        hit_except = Falsch
        hit_finally = Falsch

        versuch:
            pass
        ausser:
            hit_except = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except(self):
        hit_except = Falsch

        versuch:
            wirf Exception('ahoy!')
        ausser:
            hit_except = Wahr

        self.assertWahr(hit_except)

    def test_try_except_no_exception(self):
        hit_except = Falsch

        versuch:
            pass
        ausser:
            hit_except = Wahr

        self.assertFalsch(hit_except)

    def test_try_except_else(self):
        hit_except = Falsch
        hit_else = Falsch

        versuch:
            wirf Exception('foo!')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_else)
        self.assertWahr(hit_except)

    def test_try_except_else_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch

        versuch:
            pass
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_else)

    def test_try_finally_no_exception(self):
        hit_finally = Falsch

        versuch:
            pass
        schliesslich:
            hit_finally = Wahr

        self.assertWahr(hit_finally)

    def test_nested(self):
        hit_finally = Falsch
        hit_inner_except = Falsch
        hit_inner_finally = Falsch

        versuch:
            versuch:
                wirf Exception('inner exception')
            ausser:
                hit_inner_except = Wahr
            schliesslich:
                hit_inner_finally = Wahr
        schliesslich:
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

        versuch:
            versuch:
                pass
            ausser:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            wirf Exception('outer exception')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            versuch:
                wirf Exception('inner exception')
            ausser:
                hit_inner_except = Wahr
                wirf Exception('outer exception')
            sonst:
                hit_inner_else = Wahr
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            versuch:
                pass
            ausser:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr
                wirf Exception('outer exception')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            versuch:
                pass
            ausser:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr
            schliesslich:
                hit_inner_finally = Wahr
                wirf Exception('outer exception')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            versuch:
                wirf Exception('inner exception')
            ausser:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr
            schliesslich:
                hit_inner_finally = Wahr
                wirf Exception('outer exception')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            wirf Exception('nyaa!')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)
        self.assertFalsch(hit_else)

    def test_try_except_else_finally_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch
        hit_finally = Falsch

        versuch:
            pass
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_else)

    def test_try_except_finally(self):
        hit_except = Falsch
        hit_finally = Falsch

        versuch:
            wirf Exception('yarr!')
        except* BaseException:
            hit_except = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertWahr(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except_finally_no_exception(self):
        hit_except = Falsch
        hit_finally = Falsch

        versuch:
            pass
        except* BaseException:
            hit_except = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_finally)

    def test_try_except(self):
        hit_except = Falsch

        versuch:
            wirf Exception('ahoy!')
        except* BaseException:
            hit_except = Wahr

        self.assertWahr(hit_except)

    def test_try_except_no_exception(self):
        hit_except = Falsch

        versuch:
            pass
        except* BaseException:
            hit_except = Wahr

        self.assertFalsch(hit_except)

    def test_try_except_else(self):
        hit_except = Falsch
        hit_else = Falsch

        versuch:
            wirf Exception('foo!')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_else)
        self.assertWahr(hit_except)

    def test_try_except_else_no_exception(self):
        hit_except = Falsch
        hit_else = Falsch

        versuch:
            pass
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr

        self.assertFalsch(hit_except)
        self.assertWahr(hit_else)

    def test_try_finally_no_exception(self):
        hit_finally = Falsch

        versuch:
            pass
        schliesslich:
            hit_finally = Wahr

        self.assertWahr(hit_finally)

    def test_nested(self):
        hit_finally = Falsch
        hit_inner_except = Falsch
        hit_inner_finally = Falsch

        versuch:
            versuch:
                wirf Exception('inner exception')
            except* BaseException:
                hit_inner_except = Wahr
            schliesslich:
                hit_inner_finally = Wahr
        schliesslich:
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

        versuch:
            versuch:
                pass
            except* BaseException:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            wirf Exception('outer exception')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            versuch:
                wirf Exception('inner exception')
            except* BaseException:
                hit_inner_except = Wahr
            schliesslich:
                hit_inner_finally = Wahr
        ausser:
            hit_except = Wahr
        schliesslich:
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

        versuch:
            versuch:
                wirf Exception('inner exception')
            ausser:
                hit_inner_except = Wahr
            schliesslich:
                hit_inner_finally = Wahr
        except* BaseException:
            hit_except = Wahr
        schliesslich:
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

        versuch:
            versuch:
                pass
            except* BaseException:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            wirf Exception('outer exception')
        ausser:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
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

        versuch:
            versuch:
                pass
            ausser:
                hit_inner_except = Wahr
            sonst:
                hit_inner_else = Wahr

            wirf Exception('outer exception')
        except* BaseException:
            hit_except = Wahr
        sonst:
            hit_else = Wahr
        schliesslich:
            hit_finally = Wahr

        self.assertFalsch(hit_inner_except)
        self.assertWahr(hit_inner_else)
        self.assertFalsch(hit_else)
        self.assertWahr(hit_finally)
        self.assertWahr(hit_except)


wenn __name__ == '__main__':
    unittest.main()
