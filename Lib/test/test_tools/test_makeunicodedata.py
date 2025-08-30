importiere unittest
von test.test_tools importiere skip_if_missing, imports_under_tool
von test importiere support
von test.support.hypothesis_helper importiere hypothesis

st = hypothesis.strategies
given = hypothesis.given
example = hypothesis.example


skip_if_missing("unicode")
with imports_under_tool("unicode"):
    von dawg importiere Dawg, build_compression_dawg, lookup, inverse_lookup


@st.composite
def char_name_db(draw, min_length=1, max_length=30):
    m = draw(st.integers(min_value=min_length, max_value=max_length))
    names = draw(
        st.sets(st.text("abcd", min_size=1, max_size=10), min_size=m, max_size=m)
    )
    characters = draw(st.sets(st.characters(), min_size=m, max_size=m))
    gib list(zip(names, characters))


klasse TestDawg(unittest.TestCase):
    """Tests fuer the directed acyclic word graph data structure that ist used
    to store the unicode character names in unicodedata. Tests ported von PyPy
    """

    def test_dawg_direct_simple(self):
        dawg = Dawg()
        dawg.insert("a", -4)
        dawg.insert("c", -2)
        dawg.insert("cat", -1)
        dawg.insert("catarr", 0)
        dawg.insert("catnip", 1)
        dawg.insert("zcatnip", 5)
        packed, data, inverse = dawg.finish()

        self.assertEqual(lookup(packed, data, b"a"), -4)
        self.assertEqual(lookup(packed, data, b"c"), -2)
        self.assertEqual(lookup(packed, data, b"cat"), -1)
        self.assertEqual(lookup(packed, data, b"catarr"), 0)
        self.assertEqual(lookup(packed, data, b"catnip"), 1)
        self.assertEqual(lookup(packed, data, b"zcatnip"), 5)
        self.assertRaises(KeyError, lookup, packed, data, b"b")
        self.assertRaises(KeyError, lookup, packed, data, b"catni")
        self.assertRaises(KeyError, lookup, packed, data, b"catnipp")

        self.assertEqual(inverse_lookup(packed, inverse, -4), b"a")
        self.assertEqual(inverse_lookup(packed, inverse, -2), b"c")
        self.assertEqual(inverse_lookup(packed, inverse, -1), b"cat")
        self.assertEqual(inverse_lookup(packed, inverse, 0), b"catarr")
        self.assertEqual(inverse_lookup(packed, inverse, 1), b"catnip")
        self.assertEqual(inverse_lookup(packed, inverse, 5), b"zcatnip")
        self.assertRaises(KeyError, inverse_lookup, packed, inverse, 12)

    def test_forbid_empty_dawg(self):
        dawg = Dawg()
        self.assertRaises(ValueError, dawg.finish)

    @given(char_name_db())
    @example([("abc", "a"), ("abd", "b")])
    @example(
        [
            ("bab", "1"),
            ("a", ":"),
            ("ad", "@"),
            ("b", "<"),
            ("aacc", "?"),
            ("dab", "D"),
            ("aa", "0"),
            ("ab", "F"),
            ("aaa", "7"),
            ("cbd", "="),
            ("abad", ";"),
            ("ac", "B"),
            ("abb", "4"),
            ("bb", "2"),
            ("aab", "9"),
            ("caaaaba", "E"),
            ("ca", ">"),
            ("bbaaa", "5"),
            ("d", "3"),
            ("baac", "8"),
            ("c", "6"),
            ("ba", "A"),
        ]
    )
    @example(
        [
            ("bcdac", "9"),
            ("acc", "g"),
            ("d", "d"),
            ("daabdda", "0"),
            ("aba", ";"),
            ("c", "6"),
            ("aa", "7"),
            ("abbd", "c"),
            ("badbd", "?"),
            ("bbd", "f"),
            ("cc", "@"),
            ("bb", "8"),
            ("daca", ">"),
            ("ba", ":"),
            ("baac", "3"),
            ("dbdddac", "a"),
            ("a", "2"),
            ("cabd", "b"),
            ("b", "="),
            ("abd", "4"),
            ("adcbd", "5"),
            ("abc", "e"),
            ("ab", "1"),
        ]
    )
    def test_dawg(self, data):
        # suppress debug prints
        mit support.captured_stdout() als output:
            # it's enough to build it, building will also check the result
            build_compression_dawg(data)
