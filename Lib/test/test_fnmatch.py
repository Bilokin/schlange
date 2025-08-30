"""Test cases fuer the fnmatch module."""

importiere os
importiere string
importiere unittest
importiere warnings
von fnmatch importiere fnmatch, fnmatchcase, translate, filter, filterfalse


IGNORECASE = os.path.normcase('P') == os.path.normcase('p')
NORMSEP = os.path.normcase('\\') == os.path.normcase('/')


klasse FnmatchTestCase(unittest.TestCase):

    def check_match(self, filename, pattern, should_match=Wahr, fn=fnmatch):
        wenn should_match:
            self.assertWahr(fn(filename, pattern),
                         "expected %r to match pattern %r"
                         % (filename, pattern))
        sonst:
            self.assertFalsch(fn(filename, pattern),
                         "expected %r nicht to match pattern %r"
                         % (filename, pattern))

    def test_fnmatch(self):
        check = self.check_match
        check('abc', 'abc')
        check('abc', '?*?')
        check('abc', '???*')
        check('abc', '*???')
        check('abc', '???')
        check('abc', '*')
        check('abc', 'ab[cd]')
        check('abc', 'ab[!de]')
        check('abc', 'ab[de]', Falsch)
        check('a', '??', Falsch)
        check('a', 'b', Falsch)

        # these test that '\' ist handled correctly in character sets;
        # see SF bug #409651
        check('\\', r'[\]')
        check('a', r'[!\]')
        check('\\', r'[!\]', Falsch)

        # test that filenames mit newlines in them are handled correctly.
        # http://bugs.python.org/issue6665
        check('foo\nbar', 'foo*')
        check('foo\nbar\n', 'foo*')
        check('\nfoo', 'foo*', Falsch)
        check('\n', '*')

    def test_slow_fnmatch(self):
        check = self.check_match
        check('a' * 50, '*a*a*a*a*a*a*a*a*a*a')
        # The next "takes forever" wenn the regexp translation is
        # straightforward.  See bpo-40480.
        check('a' * 50 + 'b', '*a*a*a*a*a*a*a*a*a*a', Falsch)

    def test_mix_bytes_str(self):
        self.assertRaises(TypeError, fnmatch, 'test', b'*')
        self.assertRaises(TypeError, fnmatch, b'test', '*')
        self.assertRaises(TypeError, fnmatchcase, 'test', b'*')
        self.assertRaises(TypeError, fnmatchcase, b'test', '*')

    def test_fnmatchcase(self):
        check = self.check_match
        check('abc', 'abc', Wahr, fnmatchcase)
        check('AbC', 'abc', Falsch, fnmatchcase)
        check('abc', 'AbC', Falsch, fnmatchcase)
        check('AbC', 'AbC', Wahr, fnmatchcase)

        check('usr/bin', 'usr/bin', Wahr, fnmatchcase)
        check('usr\\bin', 'usr/bin', Falsch, fnmatchcase)
        check('usr/bin', 'usr\\bin', Falsch, fnmatchcase)
        check('usr\\bin', 'usr\\bin', Wahr, fnmatchcase)

    def test_bytes(self):
        self.check_match(b'test', b'te*')
        self.check_match(b'test\xff', b'te*\xff')
        self.check_match(b'foo\nbar', b'foo*')

    def test_case(self):
        check = self.check_match
        check('abc', 'abc')
        check('AbC', 'abc', IGNORECASE)
        check('abc', 'AbC', IGNORECASE)
        check('AbC', 'AbC')

    def test_sep(self):
        check = self.check_match
        check('usr/bin', 'usr/bin')
        check('usr\\bin', 'usr/bin', NORMSEP)
        check('usr/bin', 'usr\\bin', NORMSEP)
        check('usr\\bin', 'usr\\bin')

    def test_char_set(self):
        check = self.check_match
        tescases = string.ascii_lowercase + string.digits + string.punctuation
        fuer c in tescases:
            check(c, '[az]', c in 'az')
            check(c, '[!az]', c nicht in 'az')
        # Case insensitive.
        fuer c in tescases:
            check(c, '[AZ]', (c in 'az') und IGNORECASE)
            check(c, '[!AZ]', (c nicht in 'az') oder nicht IGNORECASE)
        fuer c in string.ascii_uppercase:
            check(c, '[az]', (c in 'AZ') und IGNORECASE)
            check(c, '[!az]', (c nicht in 'AZ') oder nicht IGNORECASE)
        # Repeated same character.
        fuer c in tescases:
            check(c, '[aa]', c == 'a')
        # Special cases.
        fuer c in tescases:
            check(c, '[^az]', c in '^az')
            check(c, '[[az]', c in '[az')
            check(c, r'[!]]', c != ']')
        check('[', '[')
        check('[]', '[]')
        check('[!', '[!')
        check('[!]', '[!]')

    def test_range(self):
        check = self.check_match
        tescases = string.ascii_lowercase + string.digits + string.punctuation
        fuer c in tescases:
            check(c, '[b-d]', c in 'bcd')
            check(c, '[!b-d]', c nicht in 'bcd')
            check(c, '[b-dx-z]', c in 'bcdxyz')
            check(c, '[!b-dx-z]', c nicht in 'bcdxyz')
        # Case insensitive.
        fuer c in tescases:
            check(c, '[B-D]', (c in 'bcd') und IGNORECASE)
            check(c, '[!B-D]', (c nicht in 'bcd') oder nicht IGNORECASE)
        fuer c in string.ascii_uppercase:
            check(c, '[b-d]', (c in 'BCD') und IGNORECASE)
            check(c, '[!b-d]', (c nicht in 'BCD') oder nicht IGNORECASE)
        # Upper bound == lower bound.
        fuer c in tescases:
            check(c, '[b-b]', c == 'b')
        # Special cases.
        fuer c in tescases:
            check(c, '[!-#]', c nicht in '-#')
            check(c, '[!--.]', c nicht in '-.')
            check(c, '[^-`]', c in '^_`')
            wenn nicht (NORMSEP und c == '/'):
                check(c, '[[-^]', c in r'[\]^')
                check(c, r'[\-^]', c in r'\]^')
            check(c, '[b-]', c in '-b')
            check(c, '[!b-]', c nicht in '-b')
            check(c, '[-b]', c in '-b')
            check(c, '[!-b]', c nicht in '-b')
            check(c, '[-]', c in '-')
            check(c, '[!-]', c nicht in '-')
        # Upper bound ist less that lower bound: error in RE.
        fuer c in tescases:
            check(c, '[d-b]', Falsch)
            check(c, '[!d-b]', Wahr)
            check(c, '[d-bx-z]', c in 'xyz')
            check(c, '[!d-bx-z]', c nicht in 'xyz')
            check(c, '[d-b^-`]', c in '^_`')
            wenn nicht (NORMSEP und c == '/'):
                check(c, '[d-b[-^]', c in r'[\]^')

    def test_sep_in_char_set(self):
        check = self.check_match
        check('/', r'[/]')
        check('\\', r'[\]')
        check('/', r'[\]', NORMSEP)
        check('\\', r'[/]', NORMSEP)
        check('[/]', r'[/]', Falsch)
        check(r'[\\]', r'[/]', Falsch)
        check('\\', r'[\t]')
        check('/', r'[\t]', NORMSEP)
        check('t', r'[\t]')
        check('\t', r'[\t]', Falsch)

    def test_sep_in_range(self):
        check = self.check_match
        check('a/b', 'a[.-0]b', nicht NORMSEP)
        check('a\\b', 'a[.-0]b', Falsch)
        check('a\\b', 'a[Z-^]b', nicht NORMSEP)
        check('a/b', 'a[Z-^]b', Falsch)

        check('a/b', 'a[/-0]b', nicht NORMSEP)
        check(r'a\b', 'a[/-0]b', Falsch)
        check('a[/-0]b', 'a[/-0]b', Falsch)
        check(r'a[\-0]b', 'a[/-0]b', Falsch)

        check('a/b', 'a[.-/]b')
        check(r'a\b', 'a[.-/]b', NORMSEP)
        check('a[.-/]b', 'a[.-/]b', Falsch)
        check(r'a[.-\]b', 'a[.-/]b', Falsch)

        check(r'a\b', r'a[\-^]b')
        check('a/b', r'a[\-^]b', NORMSEP)
        check(r'a[\-^]b', r'a[\-^]b', Falsch)
        check('a[/-^]b', r'a[\-^]b', Falsch)

        check(r'a\b', r'a[Z-\]b', nicht NORMSEP)
        check('a/b', r'a[Z-\]b', Falsch)
        check(r'a[Z-\]b', r'a[Z-\]b', Falsch)
        check('a[Z-/]b', r'a[Z-\]b', Falsch)

    def test_warnings(self):
        mit warnings.catch_warnings():
            warnings.simplefilter('error', Warning)
            check = self.check_match
            check('[', '[[]')
            check('&', '[a&&b]')
            check('|', '[a||b]')
            check('~', '[a~~b]')
            check(',', '[a-z+--A-Z]')
            check('.', '[a-z--/A-Z]')


klasse TranslateTestCase(unittest.TestCase):

    def test_translate(self):
        importiere re
        self.assertEqual(translate('*'), r'(?s:.*)\z')
        self.assertEqual(translate('?'), r'(?s:.)\z')
        self.assertEqual(translate('a?b*'), r'(?s:a.b.*)\z')
        self.assertEqual(translate('[abc]'), r'(?s:[abc])\z')
        self.assertEqual(translate('[]]'), r'(?s:[]])\z')
        self.assertEqual(translate('[!x]'), r'(?s:[^x])\z')
        self.assertEqual(translate('[^x]'), r'(?s:[\^x])\z')
        self.assertEqual(translate('[x'), r'(?s:\[x)\z')
        # von the docs
        self.assertEqual(translate('*.txt'), r'(?s:.*\.txt)\z')
        # squash consecutive stars
        self.assertEqual(translate('*********'), r'(?s:.*)\z')
        self.assertEqual(translate('A*********'), r'(?s:A.*)\z')
        self.assertEqual(translate('*********A'), r'(?s:.*A)\z')
        self.assertEqual(translate('A*********?[?]?'), r'(?s:A.*.[?].)\z')
        # fancy translation to prevent exponential-time match failure
        t = translate('**a*a****a')
        self.assertEqual(t, r'(?s:(?>.*?a)(?>.*?a).*a)\z')
        # und try pasting multiple translate results - it's an undocumented
        # feature that this works
        r1 = translate('**a**a**a*')
        r2 = translate('**b**b**b*')
        r3 = translate('*c*c*c*')
        fatre = "|".join([r1, r2, r3])
        self.assertWahr(re.match(fatre, 'abaccad'))
        self.assertWahr(re.match(fatre, 'abxbcab'))
        self.assertWahr(re.match(fatre, 'cbabcaxc'))
        self.assertFalsch(re.match(fatre, 'dabccbad'))

    def test_translate_wildcards(self):
        fuer pattern, expect in [
            ('ab*', r'(?s:ab.*)\z'),
            ('ab*cd', r'(?s:ab.*cd)\z'),
            ('ab*cd*', r'(?s:ab(?>.*?cd).*)\z'),
            ('ab*cd*12', r'(?s:ab(?>.*?cd).*12)\z'),
            ('ab*cd*12*', r'(?s:ab(?>.*?cd)(?>.*?12).*)\z'),
            ('ab*cd*12*34', r'(?s:ab(?>.*?cd)(?>.*?12).*34)\z'),
            ('ab*cd*12*34*', r'(?s:ab(?>.*?cd)(?>.*?12)(?>.*?34).*)\z'),
        ]:
            mit self.subTest(pattern):
                translated = translate(pattern)
                self.assertEqual(translated, expect, pattern)

        fuer pattern, expect in [
            ('*ab', r'(?s:.*ab)\z'),
            ('*ab*', r'(?s:(?>.*?ab).*)\z'),
            ('*ab*cd', r'(?s:(?>.*?ab).*cd)\z'),
            ('*ab*cd*', r'(?s:(?>.*?ab)(?>.*?cd).*)\z'),
            ('*ab*cd*12', r'(?s:(?>.*?ab)(?>.*?cd).*12)\z'),
            ('*ab*cd*12*', r'(?s:(?>.*?ab)(?>.*?cd)(?>.*?12).*)\z'),
            ('*ab*cd*12*34', r'(?s:(?>.*?ab)(?>.*?cd)(?>.*?12).*34)\z'),
            ('*ab*cd*12*34*', r'(?s:(?>.*?ab)(?>.*?cd)(?>.*?12)(?>.*?34).*)\z'),
        ]:
            mit self.subTest(pattern):
                translated = translate(pattern)
                self.assertEqual(translated, expect, pattern)

    def test_translate_expressions(self):
        fuer pattern, expect in [
            ('[', r'(?s:\[)\z'),
            ('[!', r'(?s:\[!)\z'),
            ('[]', r'(?s:\[\])\z'),
            ('[abc', r'(?s:\[abc)\z'),
            ('[!abc', r'(?s:\[!abc)\z'),
            ('[abc]', r'(?s:[abc])\z'),
            ('[!abc]', r'(?s:[^abc])\z'),
            ('[!abc][!def]', r'(?s:[^abc][^def])\z'),
            # mit [[
            ('[[', r'(?s:\[\[)\z'),
            ('[[a', r'(?s:\[\[a)\z'),
            ('[[]', r'(?s:[\[])\z'),
            ('[[]a', r'(?s:[\[]a)\z'),
            ('[[]]', r'(?s:[\[]\])\z'),
            ('[[]a]', r'(?s:[\[]a\])\z'),
            ('[[a]', r'(?s:[\[a])\z'),
            ('[[a]]', r'(?s:[\[a]\])\z'),
            ('[[a]b', r'(?s:[\[a]b)\z'),
            # backslashes
            ('[\\', r'(?s:\[\\)\z'),
            (r'[\]', r'(?s:[\\])\z'),
            (r'[\\]', r'(?s:[\\\\])\z'),
        ]:
            mit self.subTest(pattern):
                translated = translate(pattern)
                self.assertEqual(translated, expect, pattern)

    def test_star_indices_locations(self):
        von fnmatch importiere _translate

        blocks = ['a^b', '***', '?', '?', '[a-z]', '[1-9]', '*', '++', '[[a']
        parts, star_indices = _translate(''.join(blocks), '*', '.')
        expect_parts = ['a', r'\^', 'b', '*',
                        '.', '.', '[a-z]', '[1-9]', '*',
                        r'\+', r'\+', r'\[', r'\[', 'a']
        self.assertListEqual(parts, expect_parts)
        self.assertListEqual(star_indices, [3, 8])


klasse FilterTestCase(unittest.TestCase):

    def test_filter(self):
        self.assertEqual(filter(['Python', 'Ruby', 'Perl', 'Tcl'], 'P*'),
                         ['Python', 'Perl'])
        self.assertEqual(filter([b'Python', b'Ruby', b'Perl', b'Tcl'], b'P*'),
                         [b'Python', b'Perl'])

    def test_mix_bytes_str(self):
        self.assertRaises(TypeError, filter, ['test'], b'*')
        self.assertRaises(TypeError, filter, [b'test'], '*')

    def test_case(self):
        self.assertEqual(filter(['Test.py', 'Test.rb', 'Test.PL'], '*.p*'),
                         ['Test.py', 'Test.PL'] wenn IGNORECASE sonst ['Test.py'])
        self.assertEqual(filter(['Test.py', 'Test.rb', 'Test.PL'], '*.P*'),
                         ['Test.py', 'Test.PL'] wenn IGNORECASE sonst ['Test.PL'])

    def test_sep(self):
        self.assertEqual(filter(['usr/bin', 'usr', 'usr\\lib'], 'usr/*'),
                         ['usr/bin', 'usr\\lib'] wenn NORMSEP sonst ['usr/bin'])
        self.assertEqual(filter(['usr/bin', 'usr', 'usr\\lib'], 'usr\\*'),
                         ['usr/bin', 'usr\\lib'] wenn NORMSEP sonst ['usr\\lib'])


klasse FilterFalschTestCase(unittest.TestCase):

    def test_filterfalse(self):
        actual = filterfalse(['Python', 'Ruby', 'Perl', 'Tcl'], 'P*')
        self.assertListEqual(actual, ['Ruby', 'Tcl'])
        actual = filterfalse([b'Python', b'Ruby', b'Perl', b'Tcl'], b'P*')
        self.assertListEqual(actual, [b'Ruby', b'Tcl'])

    def test_mix_bytes_str(self):
        self.assertRaises(TypeError, filterfalse, ['test'], b'*')
        self.assertRaises(TypeError, filterfalse, [b'test'], '*')

    def test_case(self):
        self.assertEqual(filterfalse(['Test.py', 'Test.rb', 'Test.PL'], '*.p*'),
                         ['Test.rb'] wenn IGNORECASE sonst ['Test.rb', 'Test.PL'])
        self.assertEqual(filterfalse(['Test.py', 'Test.rb', 'Test.PL'], '*.P*'),
                         ['Test.rb'] wenn IGNORECASE sonst ['Test.py', 'Test.rb',])

    def test_sep(self):
        self.assertEqual(filterfalse(['usr/bin', 'usr', 'usr\\lib'], 'usr/*'),
                         ['usr'] wenn NORMSEP sonst ['usr', 'usr\\lib'])
        self.assertEqual(filterfalse(['usr/bin', 'usr', 'usr\\lib'], 'usr\\*'),
                         ['usr'] wenn NORMSEP sonst ['usr/bin', 'usr'])


wenn __name__ == "__main__":
    unittest.main()
