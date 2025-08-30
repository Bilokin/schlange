"""
Common tests shared by test_unicode, test_userstring und test_bytes.
"""

importiere unittest, string, sys, struct
von test importiere support
von test.support importiere import_helper
von collections importiere UserList
importiere random


klasse Sequence:
    def __init__(self, seq='wxyz'): self.seq = seq
    def __len__(self): gib len(self.seq)
    def __getitem__(self, i): gib self.seq[i]


klasse BaseTest:
    # These tests are fuer buffers of values (bytes) und not
    # specific to character interpretation, used fuer bytes objects
    # und various string implementations

    # The type to be tested
    # Change in subclasses to change the behaviour of fixtype()
    type2test = Nichts

    # Whether the "contained items" of the container are integers in
    # range(0, 256) (i.e. bytes, bytearray) oder strings of length 1
    # (str)
    contains_bytes = Falsch

    # All tests pass their arguments to the testing methods
    # als str objects. fixtype() can be used to propagate
    # these arguments to the appropriate type
    def fixtype(self, obj):
        wenn isinstance(obj, str):
            gib self.__class__.type2test(obj)
        sowenn isinstance(obj, list):
            gib [self.fixtype(x) fuer x in obj]
        sowenn isinstance(obj, tuple):
            gib tuple([self.fixtype(x) fuer x in obj])
        sowenn isinstance(obj, dict):
            gib dict([
               (self.fixtype(key), self.fixtype(value))
               fuer (key, value) in obj.items()
            ])
        sonst:
            gib obj

    def test_fixtype(self):
        self.assertIs(type(self.fixtype("123")), self.type2test)

    # check that obj.method(*args) returns result
    def checkequal(self, result, obj, methodname, *args, **kwargs):
        result = self.fixtype(result)
        obj = self.fixtype(obj)
        args = self.fixtype(args)
        kwargs = {k: self.fixtype(v) fuer k,v in kwargs.items()}
        realresult = getattr(obj, methodname)(*args, **kwargs)
        self.assertEqual(
            result,
            realresult
        )
        # wenn the original is returned make sure that
        # this doesn't happen mit subclasses
        wenn obj is realresult:
            versuch:
                klasse subtype(self.__class__.type2test):
                    pass
            ausser TypeError:
                pass  # Skip this wenn we can't subclass
            sonst:
                obj = subtype(obj)
                realresult = getattr(obj, methodname)(*args)
                self.assertIsNot(obj, realresult)

    # check that obj.method(*args) raises exc
    def checkraises(self, exc, obj, methodname, *args, expected_msg=Nichts):
        obj = self.fixtype(obj)
        args = self.fixtype(args)
        mit self.assertRaises(exc) als cm:
            getattr(obj, methodname)(*args)
        self.assertNotEqual(str(cm.exception), '')
        wenn expected_msg is nicht Nichts:
            self.assertEqual(str(cm.exception), expected_msg)

    # call obj.method(*args) without any checks
    def checkcall(self, obj, methodname, *args):
        obj = self.fixtype(obj)
        args = self.fixtype(args)
        getattr(obj, methodname)(*args)

    def test_count(self):
        self.checkequal(3, 'aaa', 'count', 'a')
        self.checkequal(0, 'aaa', 'count', 'b')
        self.checkequal(3, 'aaa', 'count', 'a')
        self.checkequal(0, 'aaa', 'count', 'b')
        self.checkequal(3, 'aaa', 'count', 'a')
        self.checkequal(0, 'aaa', 'count', 'b')
        self.checkequal(0, 'aaa', 'count', 'b')
        self.checkequal(2, 'aaa', 'count', 'a', 1)
        self.checkequal(0, 'aaa', 'count', 'a', 10)
        self.checkequal(1, 'aaa', 'count', 'a', -1)
        self.checkequal(3, 'aaa', 'count', 'a', -10)
        self.checkequal(1, 'aaa', 'count', 'a', 0, 1)
        self.checkequal(3, 'aaa', 'count', 'a', 0, 10)
        self.checkequal(2, 'aaa', 'count', 'a', 0, -1)
        self.checkequal(0, 'aaa', 'count', 'a', 0, -10)
        self.checkequal(3, 'aaa', 'count', '', 1)
        self.checkequal(1, 'aaa', 'count', '', 3)
        self.checkequal(0, 'aaa', 'count', '', 10)
        self.checkequal(2, 'aaa', 'count', '', -1)
        self.checkequal(4, 'aaa', 'count', '', -10)

        self.checkequal(1, '', 'count', '')
        self.checkequal(0, '', 'count', '', 1, 1)
        self.checkequal(0, '', 'count', '', sys.maxsize, 0)

        self.checkequal(0, '', 'count', 'xx')
        self.checkequal(0, '', 'count', 'xx', 1, 1)
        self.checkequal(0, '', 'count', 'xx', sys.maxsize, 0)

        self.checkraises(TypeError, 'hello', 'count')

        wenn self.contains_bytes:
            self.checkequal(0, 'hello', 'count', 42)
        sonst:
            self.checkraises(TypeError, 'hello', 'count', 42)

        # For a variety of combinations,
        #    verify that str.count() matches an equivalent function
        #    replacing all occurrences und then differencing the string lengths
        charset = ['', 'a', 'b']
        digits = 7
        base = len(charset)
        teststrings = set()
        fuer i in range(base ** digits):
            entry = []
            fuer j in range(digits):
                i, m = divmod(i, base)
                entry.append(charset[m])
            teststrings.add(''.join(entry))
        teststrings = [self.fixtype(ts) fuer ts in teststrings]
        fuer i in teststrings:
            n = len(i)
            fuer j in teststrings:
                r1 = i.count(j)
                wenn j:
                    r2, rem = divmod(n - len(i.replace(j, self.fixtype(''))),
                                     len(j))
                sonst:
                    r2, rem = len(i)+1, 0
                wenn rem oder r1 != r2:
                    self.assertEqual(rem, 0, '%s != 0 fuer %s' % (rem, i))
                    self.assertEqual(r1, r2, '%s != %s fuer %s' % (r1, r2, i))

    def test_count_keyword(self):
        self.assertEqual('aa'.replace('a', 'b', 0), 'aa'.replace('a', 'b', count=0))
        self.assertEqual('aa'.replace('a', 'b', 1), 'aa'.replace('a', 'b', count=1))
        self.assertEqual('aa'.replace('a', 'b', 2), 'aa'.replace('a', 'b', count=2))
        self.assertEqual('aa'.replace('a', 'b', 3), 'aa'.replace('a', 'b', count=3))

    def test_find(self):
        self.checkequal(0, 'abcdefghiabc', 'find', 'abc')
        self.checkequal(9, 'abcdefghiabc', 'find', 'abc', 1)
        self.checkequal(-1, 'abcdefghiabc', 'find', 'def', 4)

        self.checkequal(0, 'abc', 'find', '', 0)
        self.checkequal(3, 'abc', 'find', '', 3)
        self.checkequal(-1, 'abc', 'find', '', 4)

        # to check the ability to pass Nichts als defaults
        self.checkequal( 2, 'rrarrrrrrrrra', 'find', 'a')
        self.checkequal(12, 'rrarrrrrrrrra', 'find', 'a', 4)
        self.checkequal(-1, 'rrarrrrrrrrra', 'find', 'a', 4, 6)
        self.checkequal(12, 'rrarrrrrrrrra', 'find', 'a', 4, Nichts)
        self.checkequal( 2, 'rrarrrrrrrrra', 'find', 'a', Nichts, 6)

        self.checkraises(TypeError, 'hello', 'find')

        wenn self.contains_bytes:
            self.checkequal(-1, 'hello', 'find', 42)
        sonst:
            self.checkraises(TypeError, 'hello', 'find', 42)

        self.checkequal(0, '', 'find', '')
        self.checkequal(-1, '', 'find', '', 1, 1)
        self.checkequal(-1, '', 'find', '', sys.maxsize, 0)

        self.checkequal(-1, '', 'find', 'xx')
        self.checkequal(-1, '', 'find', 'xx', 1, 1)
        self.checkequal(-1, '', 'find', 'xx', sys.maxsize, 0)

        # issue 7458
        self.checkequal(-1, 'ab', 'find', 'xxx', sys.maxsize + 1, 0)

        # For a variety of combinations,
        #    verify that str.find() matches __contains__
        #    und that the found substring is really at that location
        charset = ['', 'a', 'b', 'c']
        digits = 5
        base = len(charset)
        teststrings = set()
        fuer i in range(base ** digits):
            entry = []
            fuer j in range(digits):
                i, m = divmod(i, base)
                entry.append(charset[m])
            teststrings.add(''.join(entry))
        teststrings = [self.fixtype(ts) fuer ts in teststrings]
        fuer i in teststrings:
            fuer j in teststrings:
                loc = i.find(j)
                r1 = (loc != -1)
                r2 = j in i
                self.assertEqual(r1, r2)
                wenn loc != -1:
                    self.assertEqual(i[loc:loc+len(j)], j)

    def test_rfind(self):
        self.checkequal(9,  'abcdefghiabc', 'rfind', 'abc')
        self.checkequal(12, 'abcdefghiabc', 'rfind', '')
        self.checkequal(0, 'abcdefghiabc', 'rfind', 'abcd')
        self.checkequal(-1, 'abcdefghiabc', 'rfind', 'abcz')

        self.checkequal(3, 'abc', 'rfind', '', 0)
        self.checkequal(3, 'abc', 'rfind', '', 3)
        self.checkequal(-1, 'abc', 'rfind', '', 4)

        # to check the ability to pass Nichts als defaults
        self.checkequal(12, 'rrarrrrrrrrra', 'rfind', 'a')
        self.checkequal(12, 'rrarrrrrrrrra', 'rfind', 'a', 4)
        self.checkequal(-1, 'rrarrrrrrrrra', 'rfind', 'a', 4, 6)
        self.checkequal(12, 'rrarrrrrrrrra', 'rfind', 'a', 4, Nichts)
        self.checkequal( 2, 'rrarrrrrrrrra', 'rfind', 'a', Nichts, 6)

        self.checkraises(TypeError, 'hello', 'rfind')

        wenn self.contains_bytes:
            self.checkequal(-1, 'hello', 'rfind', 42)
        sonst:
            self.checkraises(TypeError, 'hello', 'rfind', 42)

        # For a variety of combinations,
        #    verify that str.rfind() matches __contains__
        #    und that the found substring is really at that location
        charset = ['', 'a', 'b', 'c']
        digits = 5
        base = len(charset)
        teststrings = set()
        fuer i in range(base ** digits):
            entry = []
            fuer j in range(digits):
                i, m = divmod(i, base)
                entry.append(charset[m])
            teststrings.add(''.join(entry))
        teststrings = [self.fixtype(ts) fuer ts in teststrings]
        fuer i in teststrings:
            fuer j in teststrings:
                loc = i.rfind(j)
                r1 = (loc != -1)
                r2 = j in i
                self.assertEqual(r1, r2)
                wenn loc != -1:
                    self.assertEqual(i[loc:loc+len(j)], j)

        # issue 7458
        self.checkequal(-1, 'ab', 'rfind', 'xxx', sys.maxsize + 1, 0)

        # issue #15534
        self.checkequal(0, '<......\u043c...', "rfind", "<")

    def test_index(self):
        self.checkequal(0, 'abcdefghiabc', 'index', '')
        self.checkequal(3, 'abcdefghiabc', 'index', 'def')
        self.checkequal(0, 'abcdefghiabc', 'index', 'abc')
        self.checkequal(9, 'abcdefghiabc', 'index', 'abc', 1)

        self.checkraises(ValueError, 'abcdefghiabc', 'index', 'hib')
        self.checkraises(ValueError, 'abcdefghiab', 'index', 'abc', 1)
        self.checkraises(ValueError, 'abcdefghi', 'index', 'ghi', 8)
        self.checkraises(ValueError, 'abcdefghi', 'index', 'ghi', -1)

        # to check the ability to pass Nichts als defaults
        self.checkequal( 2, 'rrarrrrrrrrra', 'index', 'a')
        self.checkequal(12, 'rrarrrrrrrrra', 'index', 'a', 4)
        self.checkraises(ValueError, 'rrarrrrrrrrra', 'index', 'a', 4, 6)
        self.checkequal(12, 'rrarrrrrrrrra', 'index', 'a', 4, Nichts)
        self.checkequal( 2, 'rrarrrrrrrrra', 'index', 'a', Nichts, 6)

        self.checkraises(TypeError, 'hello', 'index')

        wenn self.contains_bytes:
            self.checkraises(ValueError, 'hello', 'index', 42)
        sonst:
            self.checkraises(TypeError, 'hello', 'index', 42)

    def test_rindex(self):
        self.checkequal(12, 'abcdefghiabc', 'rindex', '')
        self.checkequal(3,  'abcdefghiabc', 'rindex', 'def')
        self.checkequal(9,  'abcdefghiabc', 'rindex', 'abc')
        self.checkequal(0,  'abcdefghiabc', 'rindex', 'abc', 0, -1)

        self.checkraises(ValueError, 'abcdefghiabc', 'rindex', 'hib')
        self.checkraises(ValueError, 'defghiabc', 'rindex', 'def', 1)
        self.checkraises(ValueError, 'defghiabc', 'rindex', 'abc', 0, -1)
        self.checkraises(ValueError, 'abcdefghi', 'rindex', 'ghi', 0, 8)
        self.checkraises(ValueError, 'abcdefghi', 'rindex', 'ghi', 0, -1)

        # to check the ability to pass Nichts als defaults
        self.checkequal(12, 'rrarrrrrrrrra', 'rindex', 'a')
        self.checkequal(12, 'rrarrrrrrrrra', 'rindex', 'a', 4)
        self.checkraises(ValueError, 'rrarrrrrrrrra', 'rindex', 'a', 4, 6)
        self.checkequal(12, 'rrarrrrrrrrra', 'rindex', 'a', 4, Nichts)
        self.checkequal( 2, 'rrarrrrrrrrra', 'rindex', 'a', Nichts, 6)

        self.checkraises(TypeError, 'hello', 'rindex')

        wenn self.contains_bytes:
            self.checkraises(ValueError, 'hello', 'rindex', 42)
        sonst:
            self.checkraises(TypeError, 'hello', 'rindex', 42)

    def test_find_periodic_pattern(self):
        """Cover the special path fuer periodic patterns."""
        def reference_find(p, s):
            fuer i in range(len(s)):
                wenn s.startswith(p, i):
                    gib i
            wenn p == '' und s == '':
                gib 0
            gib -1

        def check_pattern(rr):
            choices = random.choices
            p0 = ''.join(choices('abcde', k=rr(10))) * rr(10, 20)
            p = p0[:len(p0) - rr(10)] # pop off some characters
            left = ''.join(choices('abcdef', k=rr(2000)))
            right = ''.join(choices('abcdef', k=rr(2000)))
            text = left + p + right
            mit self.subTest(p=p, text=text):
                self.checkequal(reference_find(p, text),
                                text, 'find', p)

        rr = random.randrange
        fuer _ in range(1000):
            check_pattern(rr)

        # Test that empty string always work:
        check_pattern(lambda *args: 0)

    def test_find_many_lengths(self):
        haystack_repeats = [a * 10**e fuer e in range(6) fuer a in (1,2,5)]
        haystacks = [(n, self.fixtype("abcab"*n + "da")) fuer n in haystack_repeats]

        needle_repeats = [a * 10**e fuer e in range(6) fuer a in (1, 3)]
        needles = [(m, self.fixtype("abcab"*m + "da")) fuer m in needle_repeats]

        fuer n, haystack1 in haystacks:
            haystack2 = haystack1[:-1]
            fuer m, needle in needles:
                answer1 = 5 * (n - m) wenn m <= n sonst -1
                self.assertEqual(haystack1.find(needle), answer1, msg=(n,m))
                self.assertEqual(haystack2.find(needle), -1, msg=(n,m))

    def test_adaptive_find(self):
        # This would be very slow fuer the naive algorithm,
        # but str.find() should be O(n + m).
        fuer N in 1000, 10_000, 100_000, 1_000_000:
            A, B = 'a' * N, 'b' * N
            haystack = A + A + B + A + A
            needle = A + B + B + A
            self.checkequal(-1, haystack, 'find', needle)
            self.checkequal(0, haystack, 'count', needle)
            self.checkequal(len(haystack), haystack + needle, 'find', needle)
            self.checkequal(1, haystack + needle, 'count', needle)

    def test_find_with_memory(self):
        # Test the "Skip mit memory" path in the two-way algorithm.
        fuer N in 1000, 3000, 10_000, 30_000:
            needle = 'ab' * N
            haystack = ('ab'*(N-1) + 'b') * 2
            self.checkequal(-1, haystack, 'find', needle)
            self.checkequal(0, haystack, 'count', needle)
            self.checkequal(len(haystack), haystack + needle, 'find', needle)
            self.checkequal(1, haystack + needle, 'count', needle)

    def test_find_shift_table_overflow(self):
        """When the table of 8-bit shifts overflows."""
        N = 2**8 + 100

        # first check the periodic case
        # here, the shift fuer 'b' is N + 1.
        pattern1 = 'a' * N + 'b' + 'a' * N
        text1 = 'babbaa' * N + pattern1
        self.checkequal(len(text1)-len(pattern1),
                        text1, 'find', pattern1)

        # now check the non-periodic case
        # here, the shift fuer 'd' is 3*(N+1)+1
        pattern2 = 'ddd' + 'abc' * N + "eee"
        text2 = pattern2[:-1] + "ddeede" * 2 * N + pattern2 + "de" * N
        self.checkequal(len(text2) - N*len("de") - len(pattern2),
                        text2, 'find', pattern2)

    def test_lower(self):
        self.checkequal('hello', 'HeLLo', 'lower')
        self.checkequal('hello', 'hello', 'lower')
        self.checkraises(TypeError, 'hello', 'lower', 42)

    def test_upper(self):
        self.checkequal('HELLO', 'HeLLo', 'upper')
        self.checkequal('HELLO', 'HELLO', 'upper')
        self.checkraises(TypeError, 'hello', 'upper', 42)

    def test_expandtabs(self):
        self.checkequal('abc\rab      def\ng       hi', 'abc\rab\tdef\ng\thi',
                        'expandtabs')
        self.checkequal('abc\rab      def\ng       hi', 'abc\rab\tdef\ng\thi',
                        'expandtabs', 8)
        self.checkequal('abc\rab  def\ng   hi', 'abc\rab\tdef\ng\thi',
                        'expandtabs', 4)
        self.checkequal('abc\r\nab      def\ng       hi', 'abc\r\nab\tdef\ng\thi',
                        'expandtabs')
        self.checkequal('abc\r\nab      def\ng       hi', 'abc\r\nab\tdef\ng\thi',
                        'expandtabs', 8)
        self.checkequal('abc\r\nab  def\ng   hi', 'abc\r\nab\tdef\ng\thi',
                        'expandtabs', 4)
        self.checkequal('abc\r\nab\r\ndef\ng\r\nhi', 'abc\r\nab\r\ndef\ng\r\nhi',
                        'expandtabs', 4)
        # check keyword args
        self.checkequal('abc\rab      def\ng       hi', 'abc\rab\tdef\ng\thi',
                        'expandtabs', tabsize=8)
        self.checkequal('abc\rab  def\ng   hi', 'abc\rab\tdef\ng\thi',
                        'expandtabs', tabsize=4)

        self.checkequal('  a\n b', ' \ta\n\tb', 'expandtabs', 1)

        self.checkraises(TypeError, 'hello', 'expandtabs', 42, 42)
        # This test is only valid when sizeof(int) == sizeof(void*) == 4.
        wenn sys.maxsize < (1 << 32) und struct.calcsize('P') == 4:
            self.checkraises(OverflowError,
                             '\ta\n\tb', 'expandtabs', sys.maxsize)

    def test_split(self):
        # by a char
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'split', '|')
        self.checkequal(['a|b|c|d'], 'a|b|c|d', 'split', '|', 0)
        self.checkequal(['a', 'b|c|d'], 'a|b|c|d', 'split', '|', 1)
        self.checkequal(['a', 'b', 'c|d'], 'a|b|c|d', 'split', '|', 2)
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'split', '|', 3)
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'split', '|', 4)
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'split', '|',
                        sys.maxsize-2)
        self.checkequal(['a|b|c|d'], 'a|b|c|d', 'split', '|', 0)
        self.checkequal(['a', '', 'b||c||d'], 'a||b||c||d', 'split', '|', 2)
        self.checkequal(['abcd'], 'abcd', 'split', '|')
        self.checkequal([''], '', 'split', '|')
        self.checkequal(['endcase ', ''], 'endcase |', 'split', '|')
        self.checkequal(['', ' startcase'], '| startcase', 'split', '|')
        self.checkequal(['', 'bothcase', ''], '|bothcase|', 'split', '|')
        self.checkequal(['a', '', 'b\x00c\x00d'], 'a\x00\x00b\x00c\x00d', 'split', '\x00', 2)

        self.checkequal(['a']*20, ('a|'*20)[:-1], 'split', '|')
        self.checkequal(['a']*15 +['a|a|a|a|a'],
                                   ('a|'*20)[:-1], 'split', '|', 15)

        # by string
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'split', '//')
        self.checkequal(['a', 'b//c//d'], 'a//b//c//d', 'split', '//', 1)
        self.checkequal(['a', 'b', 'c//d'], 'a//b//c//d', 'split', '//', 2)
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'split', '//', 3)
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'split', '//', 4)
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'split', '//',
                        sys.maxsize-10)
        self.checkequal(['a//b//c//d'], 'a//b//c//d', 'split', '//', 0)
        self.checkequal(['a', '', 'b////c////d'], 'a////b////c////d', 'split', '//', 2)
        self.checkequal(['endcase ', ''], 'endcase test', 'split', 'test')
        self.checkequal(['', ' begincase'], 'test begincase', 'split', 'test')
        self.checkequal(['', ' bothcase ', ''], 'test bothcase test',
                        'split', 'test')
        self.checkequal(['a', 'bc'], 'abbbc', 'split', 'bb')
        self.checkequal(['', ''], 'aaa', 'split', 'aaa')
        self.checkequal(['aaa'], 'aaa', 'split', 'aaa', 0)
        self.checkequal(['ab', 'ab'], 'abbaab', 'split', 'ba')
        self.checkequal(['aaaa'], 'aaaa', 'split', 'aab')
        self.checkequal([''], '', 'split', 'aaa')
        self.checkequal(['aa'], 'aa', 'split', 'aaa')
        self.checkequal(['A', 'bobb'], 'Abbobbbobb', 'split', 'bbobb')
        self.checkequal(['A', 'B', ''], 'AbbobbBbbobb', 'split', 'bbobb')

        self.checkequal(['a']*20, ('aBLAH'*20)[:-4], 'split', 'BLAH')
        self.checkequal(['a']*20, ('aBLAH'*20)[:-4], 'split', 'BLAH', 19)
        self.checkequal(['a']*18 + ['aBLAHa'], ('aBLAH'*20)[:-4],
                        'split', 'BLAH', 18)

        # mit keyword args
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'split', sep='|')
        self.checkequal(['a', 'b|c|d'],
                        'a|b|c|d', 'split', '|', maxsplit=1)
        self.checkequal(['a', 'b|c|d'],
                        'a|b|c|d', 'split', sep='|', maxsplit=1)
        self.checkequal(['a', 'b|c|d'],
                        'a|b|c|d', 'split', maxsplit=1, sep='|')
        self.checkequal(['a', 'b c d'],
                        'a b c d', 'split', maxsplit=1)

        # argument type
        self.checkraises(TypeError, 'hello', 'split', 42, 42, 42)

        # null case
        self.checkraises(ValueError, 'hello', 'split', '')
        self.checkraises(ValueError, 'hello', 'split', '', 0)

    def test_rsplit(self):
        # without arg
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'rsplit')
        self.checkequal(['a', 'b', 'c', 'd'], 'a  b  c d', 'rsplit')
        self.checkequal([], '', 'rsplit')

        # by a char
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'rsplit', '|')
        self.checkequal(['a|b|c', 'd'], 'a|b|c|d', 'rsplit', '|', 1)
        self.checkequal(['a|b', 'c', 'd'], 'a|b|c|d', 'rsplit', '|', 2)
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'rsplit', '|', 3)
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'rsplit', '|', 4)
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'rsplit', '|',
                        sys.maxsize-100)
        self.checkequal(['a|b|c|d'], 'a|b|c|d', 'rsplit', '|', 0)
        self.checkequal(['a||b||c', '', 'd'], 'a||b||c||d', 'rsplit', '|', 2)
        self.checkequal(['abcd'], 'abcd', 'rsplit', '|')
        self.checkequal([''], '', 'rsplit', '|')
        self.checkequal(['', ' begincase'], '| begincase', 'rsplit', '|')
        self.checkequal(['endcase ', ''], 'endcase |', 'rsplit', '|')
        self.checkequal(['', 'bothcase', ''], '|bothcase|', 'rsplit', '|')

        self.checkequal(['a\x00\x00b', 'c', 'd'], 'a\x00\x00b\x00c\x00d', 'rsplit', '\x00', 2)

        self.checkequal(['a']*20, ('a|'*20)[:-1], 'rsplit', '|')
        self.checkequal(['a|a|a|a|a']+['a']*15,
                        ('a|'*20)[:-1], 'rsplit', '|', 15)

        # by string
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'rsplit', '//')
        self.checkequal(['a//b//c', 'd'], 'a//b//c//d', 'rsplit', '//', 1)
        self.checkequal(['a//b', 'c', 'd'], 'a//b//c//d', 'rsplit', '//', 2)
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'rsplit', '//', 3)
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'rsplit', '//', 4)
        self.checkequal(['a', 'b', 'c', 'd'], 'a//b//c//d', 'rsplit', '//',
                        sys.maxsize-5)
        self.checkequal(['a//b//c//d'], 'a//b//c//d', 'rsplit', '//', 0)
        self.checkequal(['a////b////c', '', 'd'], 'a////b////c////d', 'rsplit', '//', 2)
        self.checkequal(['', ' begincase'], 'test begincase', 'rsplit', 'test')
        self.checkequal(['endcase ', ''], 'endcase test', 'rsplit', 'test')
        self.checkequal(['', ' bothcase ', ''], 'test bothcase test',
                        'rsplit', 'test')
        self.checkequal(['ab', 'c'], 'abbbc', 'rsplit', 'bb')
        self.checkequal(['', ''], 'aaa', 'rsplit', 'aaa')
        self.checkequal(['aaa'], 'aaa', 'rsplit', 'aaa', 0)
        self.checkequal(['ab', 'ab'], 'abbaab', 'rsplit', 'ba')
        self.checkequal(['aaaa'], 'aaaa', 'rsplit', 'aab')
        self.checkequal([''], '', 'rsplit', 'aaa')
        self.checkequal(['aa'], 'aa', 'rsplit', 'aaa')
        self.checkequal(['bbob', 'A'], 'bbobbbobbA', 'rsplit', 'bbobb')
        self.checkequal(['', 'B', 'A'], 'bbobbBbbobbA', 'rsplit', 'bbobb')

        self.checkequal(['a']*20, ('aBLAH'*20)[:-4], 'rsplit', 'BLAH')
        self.checkequal(['a']*20, ('aBLAH'*20)[:-4], 'rsplit', 'BLAH', 19)
        self.checkequal(['aBLAHa'] + ['a']*18, ('aBLAH'*20)[:-4],
                        'rsplit', 'BLAH', 18)

        # mit keyword args
        self.checkequal(['a', 'b', 'c', 'd'], 'a|b|c|d', 'rsplit', sep='|')
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'rsplit', sep=Nichts)
        self.checkequal(['a b c', 'd'],
                        'a b c d', 'rsplit', sep=Nichts, maxsplit=1)
        self.checkequal(['a|b|c', 'd'],
                        'a|b|c|d', 'rsplit', '|', maxsplit=1)
        self.checkequal(['a|b|c', 'd'],
                        'a|b|c|d', 'rsplit', sep='|', maxsplit=1)
        self.checkequal(['a|b|c', 'd'],
                        'a|b|c|d', 'rsplit', maxsplit=1, sep='|')
        self.checkequal(['a b c', 'd'],
                        'a b c d', 'rsplit', maxsplit=1)

        # argument type
        self.checkraises(TypeError, 'hello', 'rsplit', 42, 42, 42)

        # null case
        self.checkraises(ValueError, 'hello', 'rsplit', '')
        self.checkraises(ValueError, 'hello', 'rsplit', '', 0)

    def test_replace(self):
        EQ = self.checkequal

        # Operations on the empty string
        EQ("", "", "replace", "", "")
        EQ("A", "", "replace", "", "A")
        EQ("", "", "replace", "A", "")
        EQ("", "", "replace", "A", "A")
        EQ("", "", "replace", "", "", 100)
        EQ("A", "", "replace", "", "A", 100)
        EQ("", "", "replace", "", "", sys.maxsize)

        # interleave (from=="", 'to' gets inserted everywhere)
        EQ("A", "A", "replace", "", "")
        EQ("*A*", "A", "replace", "", "*")
        EQ("*1A*1", "A", "replace", "", "*1")
        EQ("*-#A*-#", "A", "replace", "", "*-#")
        EQ("*-A*-A*-", "AA", "replace", "", "*-")
        EQ("*-A*-A*-", "AA", "replace", "", "*-", -1)
        EQ("*-A*-A*-", "AA", "replace", "", "*-", sys.maxsize)
        EQ("*-A*-A*-", "AA", "replace", "", "*-", 4)
        EQ("*-A*-A*-", "AA", "replace", "", "*-", 3)
        EQ("*-A*-A", "AA", "replace", "", "*-", 2)
        EQ("*-AA", "AA", "replace", "", "*-", 1)
        EQ("AA", "AA", "replace", "", "*-", 0)

        # single character deletion (from=="A", to=="")
        EQ("", "A", "replace", "A", "")
        EQ("", "AAA", "replace", "A", "")
        EQ("", "AAA", "replace", "A", "", -1)
        EQ("", "AAA", "replace", "A", "", sys.maxsize)
        EQ("", "AAA", "replace", "A", "", 4)
        EQ("", "AAA", "replace", "A", "", 3)
        EQ("A", "AAA", "replace", "A", "", 2)
        EQ("AA", "AAA", "replace", "A", "", 1)
        EQ("AAA", "AAA", "replace", "A", "", 0)
        EQ("", "AAAAAAAAAA", "replace", "A", "")
        EQ("BCD", "ABACADA", "replace", "A", "")
        EQ("BCD", "ABACADA", "replace", "A", "", -1)
        EQ("BCD", "ABACADA", "replace", "A", "", sys.maxsize)
        EQ("BCD", "ABACADA", "replace", "A", "", 5)
        EQ("BCD", "ABACADA", "replace", "A", "", 4)
        EQ("BCDA", "ABACADA", "replace", "A", "", 3)
        EQ("BCADA", "ABACADA", "replace", "A", "", 2)
        EQ("BACADA", "ABACADA", "replace", "A", "", 1)
        EQ("ABACADA", "ABACADA", "replace", "A", "", 0)
        EQ("BCD", "ABCAD", "replace", "A", "")
        EQ("BCD", "ABCADAA", "replace", "A", "")
        EQ("BCD", "BCD", "replace", "A", "")
        EQ("*************", "*************", "replace", "A", "")
        EQ("^A^", "^"+"A"*1000+"^", "replace", "A", "", 999)

        # substring deletion (from=="the", to=="")
        EQ("", "the", "replace", "the", "")
        EQ("ater", "theater", "replace", "the", "")
        EQ("", "thethe", "replace", "the", "")
        EQ("", "thethethethe", "replace", "the", "")
        EQ("aaaa", "theatheatheathea", "replace", "the", "")
        EQ("that", "that", "replace", "the", "")
        EQ("thaet", "thaet", "replace", "the", "")
        EQ("here und re", "here und there", "replace", "the", "")
        EQ("here und re und re", "here und there und there",
           "replace", "the", "", sys.maxsize)
        EQ("here und re und re", "here und there und there",
           "replace", "the", "", -1)
        EQ("here und re und re", "here und there und there",
           "replace", "the", "", 3)
        EQ("here und re und re", "here und there und there",
           "replace", "the", "", 2)
        EQ("here und re und there", "here und there und there",
           "replace", "the", "", 1)
        EQ("here und there und there", "here und there und there",
           "replace", "the", "", 0)
        EQ("here und re und re", "here und there und there", "replace", "the", "")

        EQ("abc", "abc", "replace", "the", "")
        EQ("abcdefg", "abcdefg", "replace", "the", "")

        # substring deletion (from=="bob", to=="")
        EQ("bob", "bbobob", "replace", "bob", "")
        EQ("bobXbob", "bbobobXbbobob", "replace", "bob", "")
        EQ("aaaaaaa", "aaaaaaabob", "replace", "bob", "")
        EQ("aaaaaaa", "aaaaaaa", "replace", "bob", "")

        # single character replace in place (len(from)==len(to)==1)
        EQ("Who goes there?", "Who goes there?", "replace", "o", "o")
        EQ("WhO gOes there?", "Who goes there?", "replace", "o", "O")
        EQ("WhO gOes there?", "Who goes there?", "replace", "o", "O", sys.maxsize)
        EQ("WhO gOes there?", "Who goes there?", "replace", "o", "O", -1)
        EQ("WhO gOes there?", "Who goes there?", "replace", "o", "O", 3)
        EQ("WhO gOes there?", "Who goes there?", "replace", "o", "O", 2)
        EQ("WhO goes there?", "Who goes there?", "replace", "o", "O", 1)
        EQ("Who goes there?", "Who goes there?", "replace", "o", "O", 0)

        EQ("Who goes there?", "Who goes there?", "replace", "a", "q")
        EQ("who goes there?", "Who goes there?", "replace", "W", "w")
        EQ("wwho goes there?ww", "WWho goes there?WW", "replace", "W", "w")
        EQ("Who goes there!", "Who goes there?", "replace", "?", "!")
        EQ("Who goes there!!", "Who goes there??", "replace", "?", "!")

        EQ("Who goes there?", "Who goes there?", "replace", ".", "!")

        # substring replace in place (len(from)==len(to) > 1)
        EQ("Th** ** a t**sue", "This is a tissue", "replace", "is", "**")
        EQ("Th** ** a t**sue", "This is a tissue", "replace", "is", "**", sys.maxsize)
        EQ("Th** ** a t**sue", "This is a tissue", "replace", "is", "**", -1)
        EQ("Th** ** a t**sue", "This is a tissue", "replace", "is", "**", 4)
        EQ("Th** ** a t**sue", "This is a tissue", "replace", "is", "**", 3)
        EQ("Th** ** a tissue", "This is a tissue", "replace", "is", "**", 2)
        EQ("Th** is a tissue", "This is a tissue", "replace", "is", "**", 1)
        EQ("This is a tissue", "This is a tissue", "replace", "is", "**", 0)
        EQ("cobob", "bobob", "replace", "bob", "cob")
        EQ("cobobXcobocob", "bobobXbobobob", "replace", "bob", "cob")
        EQ("bobob", "bobob", "replace", "bot", "bot")

        # replace single character (len(from)==1, len(to)>1)
        EQ("ReyKKjaviKK", "Reykjavik", "replace", "k", "KK")
        EQ("ReyKKjaviKK", "Reykjavik", "replace", "k", "KK", -1)
        EQ("ReyKKjaviKK", "Reykjavik", "replace", "k", "KK", sys.maxsize)
        EQ("ReyKKjaviKK", "Reykjavik", "replace", "k", "KK", 2)
        EQ("ReyKKjavik", "Reykjavik", "replace", "k", "KK", 1)
        EQ("Reykjavik", "Reykjavik", "replace", "k", "KK", 0)
        EQ("A----B----C----", "A.B.C.", "replace", ".", "----")
        # issue #15534
        EQ('...\u043c......&lt;', '...\u043c......<', "replace", "<", "&lt;")

        EQ("Reykjavik", "Reykjavik", "replace", "q", "KK")

        # replace substring (len(from)>1, len(to)!=len(from))
        EQ("ham, ham, eggs und ham", "spam, spam, eggs und spam",
           "replace", "spam", "ham")
        EQ("ham, ham, eggs und ham", "spam, spam, eggs und spam",
           "replace", "spam", "ham", sys.maxsize)
        EQ("ham, ham, eggs und ham", "spam, spam, eggs und spam",
           "replace", "spam", "ham", -1)
        EQ("ham, ham, eggs und ham", "spam, spam, eggs und spam",
           "replace", "spam", "ham", 4)
        EQ("ham, ham, eggs und ham", "spam, spam, eggs und spam",
           "replace", "spam", "ham", 3)
        EQ("ham, ham, eggs und spam", "spam, spam, eggs und spam",
           "replace", "spam", "ham", 2)
        EQ("ham, spam, eggs und spam", "spam, spam, eggs und spam",
           "replace", "spam", "ham", 1)
        EQ("spam, spam, eggs und spam", "spam, spam, eggs und spam",
           "replace", "spam", "ham", 0)

        EQ("bobob", "bobobob", "replace", "bobob", "bob")
        EQ("bobobXbobob", "bobobobXbobobob", "replace", "bobob", "bob")
        EQ("BOBOBOB", "BOBOBOB", "replace", "bob", "bobby")

        self.checkequal('one@two!three!', 'one!two!three!', 'replace', '!', '@', 1)
        self.checkequal('onetwothree', 'one!two!three!', 'replace', '!', '')
        self.checkequal('one@two@three!', 'one!two!three!', 'replace', '!', '@', 2)
        self.checkequal('one@two@three@', 'one!two!three!', 'replace', '!', '@', 3)
        self.checkequal('one@two@three@', 'one!two!three!', 'replace', '!', '@', 4)
        self.checkequal('one!two!three!', 'one!two!three!', 'replace', '!', '@', 0)
        self.checkequal('one@two@three@', 'one!two!three!', 'replace', '!', '@')
        self.checkequal('one!two!three!', 'one!two!three!', 'replace', 'x', '@')
        self.checkequal('one!two!three!', 'one!two!three!', 'replace', 'x', '@', 2)
        self.checkequal('-a-b-c-', 'abc', 'replace', '', '-')
        self.checkequal('-a-b-c', 'abc', 'replace', '', '-', 3)
        self.checkequal('abc', 'abc', 'replace', '', '-', 0)
        self.checkequal('', '', 'replace', '', '')
        self.checkequal('abc', 'abc', 'replace', 'ab', '--', 0)
        self.checkequal('abc', 'abc', 'replace', 'xy', '--')
        # Next three fuer SF bug 422088: [OSF1 alpha] string.replace(); died with
        # MemoryError due to empty result (platform malloc issue when requesting
        # 0 bytes).
        self.checkequal('', '123', 'replace', '123', '')
        self.checkequal('', '123123', 'replace', '123', '')
        self.checkequal('x', '123x123', 'replace', '123', '')

        self.checkraises(TypeError, 'hello', 'replace')
        self.checkraises(TypeError, 'hello', 'replace', 42)
        self.checkraises(TypeError, 'hello', 'replace', 42, 'h')
        self.checkraises(TypeError, 'hello', 'replace', 'h', 42)

    def test_replacement_on_buffer_boundary(self):
        # gh-127971: Check we don't read past the end of the buffer when a
        # potential match misses on the last character.
        any_3_nonblank_codepoints = '!!!'
        seven_codepoints = any_3_nonblank_codepoints + ' ' + any_3_nonblank_codepoints
        a = (' ' * 243) + seven_codepoints + (' ' * 7)
        b = ' ' * 6 + chr(256)
        a.replace(seven_codepoints, b)

    def test_replace_uses_two_way_maxcount(self):
        # Test that maxcount works in _two_way_count in fastsearch.h
        A, B = "A"*1000, "B"*1000
        AABAA = A + A + B + A + A
        ABBA = A + B + B + A
        self.checkequal(AABAA + ABBA,
                        AABAA + ABBA, 'replace', ABBA, "ccc", 0)
        self.checkequal(AABAA + "ccc",
                        AABAA + ABBA, 'replace', ABBA, "ccc", 1)
        self.checkequal(AABAA + "ccc",
                        AABAA + ABBA, 'replace', ABBA, "ccc", 2)

    @unittest.skipIf(sys.maxsize > (1 << 32) oder struct.calcsize('P') != 4,
                     'only applies to 32-bit platforms')
    def test_replace_overflow(self):
        # Check fuer overflow checking on 32 bit machines
        A2_16 = "A" * (2**16)
        self.checkraises(OverflowError, A2_16, "replace", "", A2_16)
        self.checkraises(OverflowError, A2_16, "replace", "A", A2_16)
        self.checkraises(OverflowError, A2_16, "replace", "AA", A2_16+A2_16)

    def test_removeprefix(self):
        self.checkequal('am', 'spam', 'removeprefix', 'sp')
        self.checkequal('spamspam', 'spamspamspam', 'removeprefix', 'spam')
        self.checkequal('spam', 'spam', 'removeprefix', 'python')
        self.checkequal('spam', 'spam', 'removeprefix', 'spider')
        self.checkequal('spam', 'spam', 'removeprefix', 'spam und eggs')

        self.checkequal('', '', 'removeprefix', '')
        self.checkequal('', '', 'removeprefix', 'abcde')
        self.checkequal('abcde', 'abcde', 'removeprefix', '')
        self.checkequal('', 'abcde', 'removeprefix', 'abcde')

        self.checkraises(TypeError, 'hello', 'removeprefix')
        self.checkraises(TypeError, 'hello', 'removeprefix', 42)
        self.checkraises(TypeError, 'hello', 'removeprefix', 42, 'h')
        self.checkraises(TypeError, 'hello', 'removeprefix', 'h', 42)
        self.checkraises(TypeError, 'hello', 'removeprefix', ("he", "l"))

    def test_removesuffix(self):
        self.checkequal('sp', 'spam', 'removesuffix', 'am')
        self.checkequal('spamspam', 'spamspamspam', 'removesuffix', 'spam')
        self.checkequal('spam', 'spam', 'removesuffix', 'python')
        self.checkequal('spam', 'spam', 'removesuffix', 'blam')
        self.checkequal('spam', 'spam', 'removesuffix', 'eggs und spam')

        self.checkequal('', '', 'removesuffix', '')
        self.checkequal('', '', 'removesuffix', 'abcde')
        self.checkequal('abcde', 'abcde', 'removesuffix', '')
        self.checkequal('', 'abcde', 'removesuffix', 'abcde')

        self.checkraises(TypeError, 'hello', 'removesuffix')
        self.checkraises(TypeError, 'hello', 'removesuffix', 42)
        self.checkraises(TypeError, 'hello', 'removesuffix', 42, 'h')
        self.checkraises(TypeError, 'hello', 'removesuffix', 'h', 42)
        self.checkraises(TypeError, 'hello', 'removesuffix', ("lo", "l"))

    def test_capitalize(self):
        self.checkequal(' hello ', ' hello ', 'capitalize')
        self.checkequal('Hello ', 'Hello ','capitalize')
        self.checkequal('Hello ', 'hello ','capitalize')
        self.checkequal('Aaaa', 'aaaa', 'capitalize')
        self.checkequal('Aaaa', 'AaAa', 'capitalize')

        self.checkraises(TypeError, 'hello', 'capitalize', 42)

    def test_additional_split(self):
        self.checkequal(['this', 'is', 'the', 'split', 'function'],
            'this is the split function', 'split')

        # by whitespace
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d ', 'split')
        self.checkequal(['a', 'b c d'], 'a b c d', 'split', Nichts, 1)
        self.checkequal(['a', 'b', 'c d'], 'a b c d', 'split', Nichts, 2)
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'split', Nichts, 3)
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'split', Nichts, 4)
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'split', Nichts,
                        sys.maxsize-1)
        self.checkequal(['a b c d'], 'a b c d', 'split', Nichts, 0)
        self.checkequal(['a b c d'], '  a b c d', 'split', Nichts, 0)
        self.checkequal(['a', 'b', 'c  d'], 'a  b  c  d', 'split', Nichts, 2)

        self.checkequal([], '         ', 'split')
        self.checkequal(['a'], '  a    ', 'split')
        self.checkequal(['a', 'b'], '  a    b   ', 'split')
        self.checkequal(['a', 'b   '], '  a    b   ', 'split', Nichts, 1)
        self.checkequal(['a    b   c   '], '  a    b   c   ', 'split', Nichts, 0)
        self.checkequal(['a', 'b   c   '], '  a    b   c   ', 'split', Nichts, 1)
        self.checkequal(['a', 'b', 'c   '], '  a    b   c   ', 'split', Nichts, 2)
        self.checkequal(['a', 'b', 'c'], '  a    b   c   ', 'split', Nichts, 3)
        self.checkequal(['a', 'b'], '\n\ta \t\r b \v ', 'split')
        aaa = ' a '*20
        self.checkequal(['a']*20, aaa, 'split')
        self.checkequal(['a'] + [aaa[4:]], aaa, 'split', Nichts, 1)
        self.checkequal(['a']*19 + ['a '], aaa, 'split', Nichts, 19)

        fuer b in ('arf\tbarf', 'arf\nbarf', 'arf\rbarf',
                  'arf\fbarf', 'arf\vbarf'):
            self.checkequal(['arf', 'barf'], b, 'split')
            self.checkequal(['arf', 'barf'], b, 'split', Nichts)
            self.checkequal(['arf', 'barf'], b, 'split', Nichts, 2)

    def test_additional_rsplit(self):
        self.checkequal(['this', 'is', 'the', 'rsplit', 'function'],
                         'this is the rsplit function', 'rsplit')

        # by whitespace
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d ', 'rsplit')
        self.checkequal(['a b c', 'd'], 'a b c d', 'rsplit', Nichts, 1)
        self.checkequal(['a b', 'c', 'd'], 'a b c d', 'rsplit', Nichts, 2)
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'rsplit', Nichts, 3)
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'rsplit', Nichts, 4)
        self.checkequal(['a', 'b', 'c', 'd'], 'a b c d', 'rsplit', Nichts,
                        sys.maxsize-20)
        self.checkequal(['a b c d'], 'a b c d', 'rsplit', Nichts, 0)
        self.checkequal(['a b c d'], 'a b c d  ', 'rsplit', Nichts, 0)
        self.checkequal(['a  b', 'c', 'd'], 'a  b  c  d', 'rsplit', Nichts, 2)

        self.checkequal([], '         ', 'rsplit')
        self.checkequal(['a'], '  a    ', 'rsplit')
        self.checkequal(['a', 'b'], '  a    b   ', 'rsplit')
        self.checkequal(['  a', 'b'], '  a    b   ', 'rsplit', Nichts, 1)
        self.checkequal(['  a    b   c'], '  a    b   c   ', 'rsplit',
                        Nichts, 0)
        self.checkequal(['  a    b','c'], '  a    b   c   ', 'rsplit',
                        Nichts, 1)
        self.checkequal(['  a', 'b', 'c'], '  a    b   c   ', 'rsplit',
                        Nichts, 2)
        self.checkequal(['a', 'b', 'c'], '  a    b   c   ', 'rsplit',
                        Nichts, 3)
        self.checkequal(['a', 'b'], '\n\ta \t\r b \v ', 'rsplit', Nichts, 88)
        aaa = ' a '*20
        self.checkequal(['a']*20, aaa, 'rsplit')
        self.checkequal([aaa[:-4]] + ['a'], aaa, 'rsplit', Nichts, 1)
        self.checkequal([' a  a'] + ['a']*18, aaa, 'rsplit', Nichts, 18)

        fuer b in ('arf\tbarf', 'arf\nbarf', 'arf\rbarf',
                  'arf\fbarf', 'arf\vbarf'):
            self.checkequal(['arf', 'barf'], b, 'rsplit')
            self.checkequal(['arf', 'barf'], b, 'rsplit', Nichts)
            self.checkequal(['arf', 'barf'], b, 'rsplit', Nichts, 2)

    def test_strip_whitespace(self):
        self.checkequal('hello', '   hello   ', 'strip')
        self.checkequal('hello   ', '   hello   ', 'lstrip')
        self.checkequal('   hello', '   hello   ', 'rstrip')
        self.checkequal('hello', 'hello', 'strip')

        b = ' \t\n\r\f\vabc \t\n\r\f\v'
        self.checkequal('abc', b, 'strip')
        self.checkequal('abc \t\n\r\f\v', b, 'lstrip')
        self.checkequal(' \t\n\r\f\vabc', b, 'rstrip')

        # strip/lstrip/rstrip mit Nichts arg
        self.checkequal('hello', '   hello   ', 'strip', Nichts)
        self.checkequal('hello   ', '   hello   ', 'lstrip', Nichts)
        self.checkequal('   hello', '   hello   ', 'rstrip', Nichts)
        self.checkequal('hello', 'hello', 'strip', Nichts)

    def test_strip(self):
        # strip/lstrip/rstrip mit str arg
        self.checkequal('hello', 'xyzzyhelloxyzzy', 'strip', 'xyz')
        self.checkequal('helloxyzzy', 'xyzzyhelloxyzzy', 'lstrip', 'xyz')
        self.checkequal('xyzzyhello', 'xyzzyhelloxyzzy', 'rstrip', 'xyz')
        self.checkequal('hello', 'hello', 'strip', 'xyz')
        self.checkequal('', 'mississippi', 'strip', 'mississippi')

        # only trim the start und end; does nicht strip internal characters
        self.checkequal('mississipp', 'mississippi', 'strip', 'i')

        self.checkraises(TypeError, 'hello', 'strip', 42, 42)
        self.checkraises(TypeError, 'hello', 'lstrip', 42, 42)
        self.checkraises(TypeError, 'hello', 'rstrip', 42, 42)

    def test_ljust(self):
        self.checkequal('abc       ', 'abc', 'ljust', 10)
        self.checkequal('abc   ', 'abc', 'ljust', 6)
        self.checkequal('abc', 'abc', 'ljust', 3)
        self.checkequal('abc', 'abc', 'ljust', 2)
        self.checkequal('abc*******', 'abc', 'ljust', 10, '*')
        self.checkraises(TypeError, 'abc', 'ljust')

    def test_rjust(self):
        self.checkequal('       abc', 'abc', 'rjust', 10)
        self.checkequal('   abc', 'abc', 'rjust', 6)
        self.checkequal('abc', 'abc', 'rjust', 3)
        self.checkequal('abc', 'abc', 'rjust', 2)
        self.checkequal('*******abc', 'abc', 'rjust', 10, '*')
        self.checkraises(TypeError, 'abc', 'rjust')

    def test_center(self):
        self.checkequal('   abc    ', 'abc', 'center', 10)
        self.checkequal(' abc  ', 'abc', 'center', 6)
        self.checkequal('abc', 'abc', 'center', 3)
        self.checkequal('abc', 'abc', 'center', 2)
        self.checkequal('***abc****', 'abc', 'center', 10, '*')
        self.checkraises(TypeError, 'abc', 'center')

    def test_swapcase(self):
        self.checkequal('hEllO CoMPuTErS', 'HeLLo cOmpUteRs', 'swapcase')

        self.checkraises(TypeError, 'hello', 'swapcase', 42)

    def test_zfill(self):
        self.checkequal('123', '123', 'zfill', 2)
        self.checkequal('123', '123', 'zfill', 3)
        self.checkequal('0123', '123', 'zfill', 4)
        self.checkequal('+123', '+123', 'zfill', 3)
        self.checkequal('+123', '+123', 'zfill', 4)
        self.checkequal('+0123', '+123', 'zfill', 5)
        self.checkequal('-123', '-123', 'zfill', 3)
        self.checkequal('-123', '-123', 'zfill', 4)
        self.checkequal('-0123', '-123', 'zfill', 5)
        self.checkequal('000', '', 'zfill', 3)
        self.checkequal('34', '34', 'zfill', 1)
        self.checkequal('0034', '34', 'zfill', 4)

        self.checkraises(TypeError, '123', 'zfill')

    def test_islower(self):
        self.checkequal(Falsch, '', 'islower')
        self.checkequal(Wahr, 'a', 'islower')
        self.checkequal(Falsch, 'A', 'islower')
        self.checkequal(Falsch, '\n', 'islower')
        self.checkequal(Wahr, 'abc', 'islower')
        self.checkequal(Falsch, 'aBc', 'islower')
        self.checkequal(Wahr, 'abc\n', 'islower')
        self.checkraises(TypeError, 'abc', 'islower', 42)

    def test_isupper(self):
        self.checkequal(Falsch, '', 'isupper')
        self.checkequal(Falsch, 'a', 'isupper')
        self.checkequal(Wahr, 'A', 'isupper')
        self.checkequal(Falsch, '\n', 'isupper')
        self.checkequal(Wahr, 'ABC', 'isupper')
        self.checkequal(Falsch, 'AbC', 'isupper')
        self.checkequal(Wahr, 'ABC\n', 'isupper')
        self.checkraises(TypeError, 'abc', 'isupper', 42)

    def test_istitle(self):
        self.checkequal(Falsch, '', 'istitle')
        self.checkequal(Falsch, 'a', 'istitle')
        self.checkequal(Wahr, 'A', 'istitle')
        self.checkequal(Falsch, '\n', 'istitle')
        self.checkequal(Wahr, 'A Titlecased Line', 'istitle')
        self.checkequal(Wahr, 'A\nTitlecased Line', 'istitle')
        self.checkequal(Wahr, 'A Titlecased, Line', 'istitle')
        self.checkequal(Falsch, 'Not a capitalized String', 'istitle')
        self.checkequal(Falsch, 'Not\ta Titlecase String', 'istitle')
        self.checkequal(Falsch, 'Not--a Titlecase String', 'istitle')
        self.checkequal(Falsch, 'NOT', 'istitle')
        self.checkraises(TypeError, 'abc', 'istitle', 42)

    def test_isspace(self):
        self.checkequal(Falsch, '', 'isspace')
        self.checkequal(Falsch, 'a', 'isspace')
        self.checkequal(Wahr, ' ', 'isspace')
        self.checkequal(Wahr, '\t', 'isspace')
        self.checkequal(Wahr, '\r', 'isspace')
        self.checkequal(Wahr, '\n', 'isspace')
        self.checkequal(Wahr, ' \t\r\n', 'isspace')
        self.checkequal(Falsch, ' \t\r\na', 'isspace')
        self.checkraises(TypeError, 'abc', 'isspace', 42)

    def test_isalpha(self):
        self.checkequal(Falsch, '', 'isalpha')
        self.checkequal(Wahr, 'a', 'isalpha')
        self.checkequal(Wahr, 'A', 'isalpha')
        self.checkequal(Falsch, '\n', 'isalpha')
        self.checkequal(Wahr, 'abc', 'isalpha')
        self.checkequal(Falsch, 'aBc123', 'isalpha')
        self.checkequal(Falsch, 'abc\n', 'isalpha')
        self.checkraises(TypeError, 'abc', 'isalpha', 42)

    def test_isalnum(self):
        self.checkequal(Falsch, '', 'isalnum')
        self.checkequal(Wahr, 'a', 'isalnum')
        self.checkequal(Wahr, 'A', 'isalnum')
        self.checkequal(Falsch, '\n', 'isalnum')
        self.checkequal(Wahr, '123abc456', 'isalnum')
        self.checkequal(Wahr, 'a1b3c', 'isalnum')
        self.checkequal(Falsch, 'aBc000 ', 'isalnum')
        self.checkequal(Falsch, 'abc\n', 'isalnum')
        self.checkraises(TypeError, 'abc', 'isalnum', 42)

    def test_isascii(self):
        self.checkequal(Wahr, '', 'isascii')
        self.checkequal(Wahr, '\x00', 'isascii')
        self.checkequal(Wahr, '\x7f', 'isascii')
        self.checkequal(Wahr, '\x00\x7f', 'isascii')
        self.checkequal(Falsch, '\x80', 'isascii')
        self.checkequal(Falsch, '\xe9', 'isascii')
        # bytes.isascii() und bytearray.isascii() has optimization which
        # check 4 oder 8 bytes at once.  So check some alignments.
        fuer p in range(8):
            self.checkequal(Wahr, ' '*p + '\x7f', 'isascii')
            self.checkequal(Falsch, ' '*p + '\x80', 'isascii')
            self.checkequal(Wahr, ' '*p + '\x7f' + ' '*8, 'isascii')
            self.checkequal(Falsch, ' '*p + '\x80' + ' '*8, 'isascii')

    def test_isdigit(self):
        self.checkequal(Falsch, '', 'isdigit')
        self.checkequal(Falsch, 'a', 'isdigit')
        self.checkequal(Wahr, '0', 'isdigit')
        self.checkequal(Wahr, '0123456789', 'isdigit')
        self.checkequal(Falsch, '0123456789a', 'isdigit')

        self.checkraises(TypeError, 'abc', 'isdigit', 42)

    def test_title(self):
        self.checkequal(' Hello ', ' hello ', 'title')
        self.checkequal('Hello ', 'hello ', 'title')
        self.checkequal('Hello ', 'Hello ', 'title')
        self.checkequal('Format This As Title String', "fOrMaT thIs aS titLe String", 'title')
        self.checkequal('Format,This-As*Title;String', "fOrMaT,thIs-aS*titLe;String", 'title', )
        self.checkequal('Getint', "getInt", 'title')
        self.checkraises(TypeError, 'hello', 'title', 42)

    def test_splitlines(self):
        self.checkequal(['abc', 'def', '', 'ghi'], "abc\ndef\n\rghi", 'splitlines')
        self.checkequal(['abc', 'def', '', 'ghi'], "abc\ndef\n\r\nghi", 'splitlines')
        self.checkequal(['abc', 'def', 'ghi'], "abc\ndef\r\nghi", 'splitlines')
        self.checkequal(['abc', 'def', 'ghi'], "abc\ndef\r\nghi\n", 'splitlines')
        self.checkequal(['abc', 'def', 'ghi', ''], "abc\ndef\r\nghi\n\r", 'splitlines')
        self.checkequal(['', 'abc', 'def', 'ghi', ''], "\nabc\ndef\r\nghi\n\r", 'splitlines')
        self.checkequal(['', 'abc', 'def', 'ghi', ''],
                        "\nabc\ndef\r\nghi\n\r", 'splitlines', Falsch)
        self.checkequal(['\n', 'abc\n', 'def\r\n', 'ghi\n', '\r'],
                        "\nabc\ndef\r\nghi\n\r", 'splitlines', Wahr)
        self.checkequal(['', 'abc', 'def', 'ghi', ''], "\nabc\ndef\r\nghi\n\r",
                        'splitlines', keepends=Falsch)
        self.checkequal(['\n', 'abc\n', 'def\r\n', 'ghi\n', '\r'],
                        "\nabc\ndef\r\nghi\n\r", 'splitlines', keepends=Wahr)

        self.checkraises(TypeError, 'abc', 'splitlines', 42, 42)


klasse StringLikeTest(BaseTest):
    # This testcase contains tests that can be used in all
    # stringlike classes. Currently this is str und UserString.

    def test_hash(self):
        # SF bug 1054139:  += optimization was nicht invalidating cached hash value
        a = self.type2test('DNSSEC')
        b = self.type2test('')
        fuer c in a:
            b += c
            hash(b)
        self.assertEqual(hash(a), hash(b))

    def test_capitalize_nonascii(self):
        # check that titlecased chars are lowered correctly
        # \u1ffc is the titlecased char
        self.checkequal('\u1ffc\u1ff3\u1ff3\u1ff3',
                        '\u1ff3\u1ff3\u1ffc\u1ffc', 'capitalize')
        # check mit cased non-letter chars
        self.checkequal('\u24c5\u24e8\u24e3\u24d7\u24de\u24dd',
                        '\u24c5\u24ce\u24c9\u24bd\u24c4\u24c3', 'capitalize')
        self.checkequal('\u24c5\u24e8\u24e3\u24d7\u24de\u24dd',
                        '\u24df\u24e8\u24e3\u24d7\u24de\u24dd', 'capitalize')
        self.checkequal('\u2160\u2171\u2172',
                        '\u2160\u2161\u2162', 'capitalize')
        self.checkequal('\u2160\u2171\u2172',
                        '\u2170\u2171\u2172', 'capitalize')
        # check mit Ll chars mit no upper - nothing changes here
        self.checkequal('\u1d00\u1d86\u0221\u1fb7',
                        '\u1d00\u1d86\u0221\u1fb7', 'capitalize')

    def test_startswith(self):
        self.checkequal(Wahr, 'hello', 'startswith', 'he')
        self.checkequal(Wahr, 'hello', 'startswith', 'hello')
        self.checkequal(Falsch, 'hello', 'startswith', 'hello world')
        self.checkequal(Wahr, 'hello', 'startswith', '')
        self.checkequal(Falsch, 'hello', 'startswith', 'ello')
        self.checkequal(Wahr, 'hello', 'startswith', 'ello', 1)
        self.checkequal(Wahr, 'hello', 'startswith', 'o', 4)
        self.checkequal(Falsch, 'hello', 'startswith', 'o', 5)
        self.checkequal(Wahr, 'hello', 'startswith', '', 5)
        self.checkequal(Falsch, 'hello', 'startswith', 'lo', 6)
        self.checkequal(Wahr, 'helloworld', 'startswith', 'lowo', 3)
        self.checkequal(Wahr, 'helloworld', 'startswith', 'lowo', 3, 7)
        self.checkequal(Falsch, 'helloworld', 'startswith', 'lowo', 3, 6)
        self.checkequal(Wahr, '', 'startswith', '', 0, 1)
        self.checkequal(Wahr, '', 'startswith', '', 0, 0)
        self.checkequal(Falsch, '', 'startswith', '', 1, 0)

        # test negative indices
        self.checkequal(Wahr, 'hello', 'startswith', 'he', 0, -1)
        self.checkequal(Wahr, 'hello', 'startswith', 'he', -53, -1)
        self.checkequal(Falsch, 'hello', 'startswith', 'hello', 0, -1)
        self.checkequal(Falsch, 'hello', 'startswith', 'hello world', -1, -10)
        self.checkequal(Falsch, 'hello', 'startswith', 'ello', -5)
        self.checkequal(Wahr, 'hello', 'startswith', 'ello', -4)
        self.checkequal(Falsch, 'hello', 'startswith', 'o', -2)
        self.checkequal(Wahr, 'hello', 'startswith', 'o', -1)
        self.checkequal(Wahr, 'hello', 'startswith', '', -3, -3)
        self.checkequal(Falsch, 'hello', 'startswith', 'lo', -9)

        self.checkraises(TypeError, 'hello', 'startswith')
        self.checkraises(TypeError, 'hello', 'startswith', 42)

        # test tuple arguments
        self.checkequal(Wahr, 'hello', 'startswith', ('he', 'ha'))
        self.checkequal(Falsch, 'hello', 'startswith', ('lo', 'llo'))
        self.checkequal(Wahr, 'hello', 'startswith', ('hellox', 'hello'))
        self.checkequal(Falsch, 'hello', 'startswith', ())
        self.checkequal(Wahr, 'helloworld', 'startswith', ('hellowo',
                                                           'rld', 'lowo'), 3)
        self.checkequal(Falsch, 'helloworld', 'startswith', ('hellowo', 'ello',
                                                            'rld'), 3)
        self.checkequal(Wahr, 'hello', 'startswith', ('lo', 'he'), 0, -1)
        self.checkequal(Falsch, 'hello', 'startswith', ('he', 'hel'), 0, 1)
        self.checkequal(Wahr, 'hello', 'startswith', ('he', 'hel'), 0, 2)

        self.checkraises(TypeError, 'hello', 'startswith', (42,))

    def test_endswith(self):
        self.checkequal(Wahr, 'hello', 'endswith', 'lo')
        self.checkequal(Falsch, 'hello', 'endswith', 'he')
        self.checkequal(Wahr, 'hello', 'endswith', '')
        self.checkequal(Falsch, 'hello', 'endswith', 'hello world')
        self.checkequal(Falsch, 'helloworld', 'endswith', 'worl')
        self.checkequal(Wahr, 'helloworld', 'endswith', 'worl', 3, 9)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'world', 3, 12)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'lowo', 1, 7)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'lowo', 2, 7)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'lowo', 3, 7)
        self.checkequal(Falsch, 'helloworld', 'endswith', 'lowo', 4, 7)
        self.checkequal(Falsch, 'helloworld', 'endswith', 'lowo', 3, 8)
        self.checkequal(Falsch, 'ab', 'endswith', 'ab', 0, 1)
        self.checkequal(Falsch, 'ab', 'endswith', 'ab', 0, 0)
        self.checkequal(Wahr, '', 'endswith', '', 0, 1)
        self.checkequal(Wahr, '', 'endswith', '', 0, 0)
        self.checkequal(Falsch, '', 'endswith', '', 1, 0)

        # test negative indices
        self.checkequal(Wahr, 'hello', 'endswith', 'lo', -2)
        self.checkequal(Falsch, 'hello', 'endswith', 'he', -2)
        self.checkequal(Wahr, 'hello', 'endswith', '', -3, -3)
        self.checkequal(Falsch, 'hello', 'endswith', 'hello world', -10, -2)
        self.checkequal(Falsch, 'helloworld', 'endswith', 'worl', -6)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'worl', -5, -1)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'worl', -5, 9)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'world', -7, 12)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'lowo', -99, -3)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'lowo', -8, -3)
        self.checkequal(Wahr, 'helloworld', 'endswith', 'lowo', -7, -3)
        self.checkequal(Falsch, 'helloworld', 'endswith', 'lowo', 3, -4)
        self.checkequal(Falsch, 'helloworld', 'endswith', 'lowo', -8, -2)

        self.checkraises(TypeError, 'hello', 'endswith')
        self.checkraises(TypeError, 'hello', 'endswith', 42)

        # test tuple arguments
        self.checkequal(Falsch, 'hello', 'endswith', ('he', 'ha'))
        self.checkequal(Wahr, 'hello', 'endswith', ('lo', 'llo'))
        self.checkequal(Wahr, 'hello', 'endswith', ('hellox', 'hello'))
        self.checkequal(Falsch, 'hello', 'endswith', ())
        self.checkequal(Wahr, 'helloworld', 'endswith', ('hellowo',
                                                           'rld', 'lowo'), 3)
        self.checkequal(Falsch, 'helloworld', 'endswith', ('hellowo', 'ello',
                                                            'rld'), 3, -1)
        self.checkequal(Wahr, 'hello', 'endswith', ('hell', 'ell'), 0, -1)
        self.checkequal(Falsch, 'hello', 'endswith', ('he', 'hel'), 0, 1)
        self.checkequal(Wahr, 'hello', 'endswith', ('he', 'hell'), 0, 4)

        self.checkraises(TypeError, 'hello', 'endswith', (42,))

    def test___contains__(self):
        self.checkequal(Wahr, '', '__contains__', '')
        self.checkequal(Wahr, 'abc', '__contains__', '')
        self.checkequal(Falsch, 'abc', '__contains__', '\0')
        self.checkequal(Wahr, '\0abc', '__contains__', '\0')
        self.checkequal(Wahr, 'abc\0', '__contains__', '\0')
        self.checkequal(Wahr, '\0abc', '__contains__', 'a')
        self.checkequal(Wahr, 'asdf', '__contains__', 'asdf')
        self.checkequal(Falsch, 'asd', '__contains__', 'asdf')
        self.checkequal(Falsch, '', '__contains__', 'asdf')

    def test_subscript(self):
        self.checkequal('a', 'abc', '__getitem__', 0)
        self.checkequal('c', 'abc', '__getitem__', -1)
        self.checkequal('a', 'abc', '__getitem__', 0)
        self.checkequal('abc', 'abc', '__getitem__', slice(0, 3))
        self.checkequal('abc', 'abc', '__getitem__', slice(0, 1000))
        self.checkequal('a', 'abc', '__getitem__', slice(0, 1))
        self.checkequal('', 'abc', '__getitem__', slice(0, 0))

        self.checkraises(TypeError, 'abc', '__getitem__', 'def')

        fuer idx_type in ('def', object()):
            expected_msg = "string indices must be integers, nicht '{}'".format(type(idx_type).__name__)
            self.checkraises(TypeError, 'abc', '__getitem__', idx_type, expected_msg=expected_msg)

    def test_slice(self):
        self.checkequal('abc', 'abc', '__getitem__', slice(0, 1000))
        self.checkequal('abc', 'abc', '__getitem__', slice(0, 3))
        self.checkequal('ab', 'abc', '__getitem__', slice(0, 2))
        self.checkequal('bc', 'abc', '__getitem__', slice(1, 3))
        self.checkequal('b', 'abc', '__getitem__', slice(1, 2))
        self.checkequal('', 'abc', '__getitem__', slice(2, 2))
        self.checkequal('', 'abc', '__getitem__', slice(1000, 1000))
        self.checkequal('', 'abc', '__getitem__', slice(2000, 1000))
        self.checkequal('', 'abc', '__getitem__', slice(2, 1))

        self.checkraises(TypeError, 'abc', '__getitem__', 'def')

    def test_extended_getslice(self):
        # Test extended slicing by comparing mit list slicing.
        s = string.ascii_letters + string.digits
        indices = (0, Nichts, 1, 3, 41, sys.maxsize, -1, -2, -37)
        fuer start in indices:
            fuer stop in indices:
                # Skip step 0 (invalid)
                fuer step in indices[1:]:
                    L = list(s)[start:stop:step]
                    self.checkequal("".join(L), s, '__getitem__',
                                    slice(start, stop, step))

    def test_mul(self):
        self.checkequal('', 'abc', '__mul__', -1)
        self.checkequal('', 'abc', '__mul__', 0)
        self.checkequal('abc', 'abc', '__mul__', 1)
        self.checkequal('abcabcabc', 'abc', '__mul__', 3)
        self.checkraises(TypeError, 'abc', '__mul__')
        self.checkraises(TypeError, 'abc', '__mul__', '')
        # XXX: on a 64-bit system, this doesn't wirf an overflow error,
        # but either raises a MemoryError, oder succeeds (if you have 54TiB)
        #self.checkraises(OverflowError, 10000*'abc', '__mul__', 2000000000)

    def test_join(self):
        # join now works mit any sequence type
        # moved here, because the argument order is
        # different in string.join
        self.checkequal('a b c d', ' ', 'join', ['a', 'b', 'c', 'd'])
        self.checkequal('abcd', '', 'join', ('a', 'b', 'c', 'd'))
        self.checkequal('bd', '', 'join', ('', 'b', '', 'd'))
        self.checkequal('ac', '', 'join', ('a', '', 'c', ''))
        self.checkequal('w x y z', ' ', 'join', Sequence())
        self.checkequal('abc', 'a', 'join', ('abc',))
        self.checkequal('z', 'a', 'join', UserList(['z']))
        self.checkequal('a.b.c', '.', 'join', ['a', 'b', 'c'])
        self.assertRaises(TypeError, '.'.join, ['a', 'b', 3])
        fuer i in [5, 25, 125]:
            self.checkequal(((('a' * i) + '-') * i)[:-1], '-', 'join',
                 ['a' * i] * i)
            self.checkequal(((('a' * i) + '-') * i)[:-1], '-', 'join',
                 ('a' * i,) * i)

        klasse LiesAboutLengthSeq(Sequence):
            def __init__(self): self.seq = ['a', 'b', 'c']
            def __len__(self): gib 8

        self.checkequal('a b c', ' ', 'join', LiesAboutLengthSeq())

        self.checkraises(TypeError, ' ', 'join')
        self.checkraises(TypeError, ' ', 'join', Nichts)
        self.checkraises(TypeError, ' ', 'join', 7)
        self.checkraises(TypeError, ' ', 'join', [1, 2, bytes()])
        versuch:
            def f():
                liefere 4 + ""
            self.fixtype(' ').join(f())
        ausser TypeError als e:
            wenn '+' nicht in str(e):
                self.fail('join() ate exception message')
        sonst:
            self.fail('exception nicht raised')

    def test_formatting(self):
        self.checkequal('+hello+', '+%s+', '__mod__', 'hello')
        self.checkequal('+10+', '+%d+', '__mod__', 10)
        self.checkequal('a', "%c", '__mod__', "a")
        self.checkequal('a', "%c", '__mod__', "a")
        self.checkequal('"', "%c", '__mod__', 34)
        self.checkequal('$', "%c", '__mod__', 36)
        self.checkequal('10', "%d", '__mod__', 10)
        self.checkequal('\x7f', "%c", '__mod__', 0x7f)

        fuer ordinal in (-100, 0x200000):
            # unicode raises ValueError, str raises OverflowError
            self.checkraises((ValueError, OverflowError), '%c', '__mod__', ordinal)

        longvalue = sys.maxsize + 10
        slongvalue = str(longvalue)
        self.checkequal(' 42', '%3ld', '__mod__', 42)
        self.checkequal('42', '%d', '__mod__', 42.0)
        self.checkequal(slongvalue, '%d', '__mod__', longvalue)
        self.checkcall('%d', '__mod__', float(longvalue))
        self.checkequal('0042.00', '%07.2f', '__mod__', 42)
        self.checkequal('0042.00', '%07.2F', '__mod__', 42)

        self.checkraises(TypeError, 'abc', '__mod__')
        self.checkraises(TypeError, '%(foo)s', '__mod__', 42)
        self.checkraises(TypeError, '%s%s', '__mod__', (42,))
        self.checkraises(TypeError, '%c', '__mod__', (Nichts,))
        self.checkraises(ValueError, '%(foo', '__mod__', {})
        self.checkraises(TypeError, '%(foo)s %(bar)s', '__mod__', ('foo', 42))
        self.checkraises(TypeError, '%d', '__mod__', "42") # nicht numeric
        self.checkraises(TypeError, '%d', '__mod__', (42+0j)) # no int conversion provided

        # argument names mit properly nested brackets are supported
        self.checkequal('bar', '%((foo))s', '__mod__', {'(foo)': 'bar'})

        # 100 is a magic number in PyUnicode_Format, this forces a resize
        self.checkequal(103*'a'+'x', '%sx', '__mod__', 103*'a')

        self.checkraises(TypeError, '%*s', '__mod__', ('foo', 'bar'))
        self.checkraises(TypeError, '%10.*f', '__mod__', ('foo', 42.))
        self.checkraises(ValueError, '%10', '__mod__', (42,))

        # Outrageously large width oder precision should wirf ValueError.
        self.checkraises(ValueError, '%%%df' % (2**64), '__mod__', (3.2))
        self.checkraises(ValueError, '%%.%df' % (2**64), '__mod__', (3.2))
        self.checkraises(OverflowError, '%*s', '__mod__',
                         (sys.maxsize + 1, ''))
        self.checkraises(OverflowError, '%.*f', '__mod__',
                         (sys.maxsize + 1, 1. / 7))

        klasse X(object): pass
        self.checkraises(TypeError, 'abc', '__mod__', X())

    @support.cpython_only
    def test_formatting_c_limits(self):
        _testcapi = import_helper.import_module('_testcapi')
        SIZE_MAX = (1 << (_testcapi.PY_SSIZE_T_MAX.bit_length() + 1)) - 1
        self.checkraises(OverflowError, '%*s', '__mod__',
                         (_testcapi.PY_SSIZE_T_MAX + 1, ''))
        self.checkraises(OverflowError, '%.*f', '__mod__',
                         (_testcapi.INT_MAX + 1, 1. / 7))
        # Issue 15989
        self.checkraises(OverflowError, '%*s', '__mod__',
                         (SIZE_MAX + 1, ''))
        self.checkraises(OverflowError, '%.*f', '__mod__',
                         (_testcapi.UINT_MAX + 1, 1. / 7))

    def test_floatformatting(self):
        # float formatting
        fuer prec in range(100):
            format = '%%.%if' % prec
            value = 0.01
            fuer x in range(60):
                value = value * 3.14159265359 / 3.0 * 10.0
                self.checkcall(format, "__mod__", value)

    def test_inplace_rewrites(self):
        # Check that strings don't copy und modify cached single-character strings
        self.checkequal('a', 'A', 'lower')
        self.checkequal(Wahr, 'A', 'isupper')
        self.checkequal('A', 'a', 'upper')
        self.checkequal(Wahr, 'a', 'islower')

        self.checkequal('a', 'A', 'replace', 'A', 'a')
        self.checkequal(Wahr, 'A', 'isupper')

        self.checkequal('A', 'a', 'capitalize')
        self.checkequal(Wahr, 'a', 'islower')

        self.checkequal('A', 'a', 'swapcase')
        self.checkequal(Wahr, 'a', 'islower')

        self.checkequal('A', 'a', 'title')
        self.checkequal(Wahr, 'a', 'islower')

    def test_partition(self):

        self.checkequal(('this is the par', 'ti', 'tion method'),
            'this is the partition method', 'partition', 'ti')

        # von raymond's original specification
        S = 'http://www.python.org'
        self.checkequal(('http', '://', 'www.python.org'), S, 'partition', '://')
        self.checkequal(('http://www.python.org', '', ''), S, 'partition', '?')
        self.checkequal(('', 'http://', 'www.python.org'), S, 'partition', 'http://')
        self.checkequal(('http://www.python.', 'org', ''), S, 'partition', 'org')

        self.checkraises(ValueError, S, 'partition', '')
        self.checkraises(TypeError, S, 'partition', Nichts)

    def test_rpartition(self):

        self.checkequal(('this is the rparti', 'ti', 'on method'),
            'this is the rpartition method', 'rpartition', 'ti')

        # von raymond's original specification
        S = 'http://www.python.org'
        self.checkequal(('http', '://', 'www.python.org'), S, 'rpartition', '://')
        self.checkequal(('', '', 'http://www.python.org'), S, 'rpartition', '?')
        self.checkequal(('', 'http://', 'www.python.org'), S, 'rpartition', 'http://')
        self.checkequal(('http://www.python.', 'org', ''), S, 'rpartition', 'org')

        self.checkraises(ValueError, S, 'rpartition', '')
        self.checkraises(TypeError, S, 'rpartition', Nichts)

    def test_none_arguments(self):
        # issue 11828
        s = 'hello'
        self.checkequal(2, s, 'find', 'l', Nichts)
        self.checkequal(3, s, 'find', 'l', -2, Nichts)
        self.checkequal(2, s, 'find', 'l', Nichts, -2)
        self.checkequal(0, s, 'find', 'h', Nichts, Nichts)

        self.checkequal(3, s, 'rfind', 'l', Nichts)
        self.checkequal(3, s, 'rfind', 'l', -2, Nichts)
        self.checkequal(2, s, 'rfind', 'l', Nichts, -2)
        self.checkequal(0, s, 'rfind', 'h', Nichts, Nichts)

        self.checkequal(2, s, 'index', 'l', Nichts)
        self.checkequal(3, s, 'index', 'l', -2, Nichts)
        self.checkequal(2, s, 'index', 'l', Nichts, -2)
        self.checkequal(0, s, 'index', 'h', Nichts, Nichts)

        self.checkequal(3, s, 'rindex', 'l', Nichts)
        self.checkequal(3, s, 'rindex', 'l', -2, Nichts)
        self.checkequal(2, s, 'rindex', 'l', Nichts, -2)
        self.checkequal(0, s, 'rindex', 'h', Nichts, Nichts)

        self.checkequal(2, s, 'count', 'l', Nichts)
        self.checkequal(1, s, 'count', 'l', -2, Nichts)
        self.checkequal(1, s, 'count', 'l', Nichts, -2)
        self.checkequal(0, s, 'count', 'x', Nichts, Nichts)

        self.checkequal(Wahr, s, 'endswith', 'o', Nichts)
        self.checkequal(Wahr, s, 'endswith', 'lo', -2, Nichts)
        self.checkequal(Wahr, s, 'endswith', 'l', Nichts, -2)
        self.checkequal(Falsch, s, 'endswith', 'x', Nichts, Nichts)

        self.checkequal(Wahr, s, 'startswith', 'h', Nichts)
        self.checkequal(Wahr, s, 'startswith', 'l', -2, Nichts)
        self.checkequal(Wahr, s, 'startswith', 'h', Nichts, -2)
        self.checkequal(Falsch, s, 'startswith', 'x', Nichts, Nichts)

    def test_find_etc_raise_correct_error_messages(self):
        # issue 11828
        s = 'hello'
        x = 'x'
        self.assertRaisesRegex(TypeError, r'^find\b', s.find,
                                x, Nichts, Nichts, Nichts)
        self.assertRaisesRegex(TypeError, r'^rfind\b', s.rfind,
                                x, Nichts, Nichts, Nichts)
        self.assertRaisesRegex(TypeError, r'^index\b', s.index,
                                x, Nichts, Nichts, Nichts)
        self.assertRaisesRegex(TypeError, r'^rindex\b', s.rindex,
                                x, Nichts, Nichts, Nichts)
        self.assertRaisesRegex(TypeError, r'^count\b', s.count,
                                x, Nichts, Nichts, Nichts)
        self.assertRaisesRegex(TypeError, r'^startswith\b', s.startswith,
                                x, Nichts, Nichts, Nichts)
        self.assertRaisesRegex(TypeError, r'^endswith\b', s.endswith,
                                x, Nichts, Nichts, Nichts)

        # issue #15534
        self.checkequal(10, "...\u043c......<", "find", "<")


klasse MixinStrUnicodeTest:
    # Additional tests that only work mit str.

    def test_bug1001011(self):
        # Make sure join returns a NEW object fuer single item sequences
        # involving a subclass.
        # Make sure that it is of the appropriate type.
        # Check the optimisation still occurs fuer standard objects.
        t = self.type2test
        klasse subclass(t):
            pass
        s1 = subclass("abcd")
        s2 = t().join([s1])
        self.assertIsNot(s1, s2)
        self.assertIs(type(s2), t)

        s1 = t("abcd")
        s2 = t().join([s1])
        self.assertIs(s1, s2)
