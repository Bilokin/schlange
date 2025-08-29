"""Tests fuer the Tools/i18n/msgfmt.py tool."""

importiere json
importiere struct
importiere sys
importiere unittest
von gettext importiere GNUTranslations
von pathlib importiere Path

von test.support.os_helper importiere temp_cwd
von test.support.script_helper importiere assert_python_failure, assert_python_ok
von test.test_tools importiere imports_under_tool, skip_if_missing, toolsdir


skip_if_missing('i18n')

data_dir = (Path(__file__).parent / 'msgfmt_data').resolve()
script_dir = Path(toolsdir) / 'i18n'
msgfmt_py = script_dir / 'msgfmt.py'

with imports_under_tool("i18n"):
    importiere msgfmt


def compile_messages(po_file, mo_file):
    assert_python_ok(msgfmt_py, '-o', mo_file, po_file)


klasse CompilationTest(unittest.TestCase):

    def test_compilation(self):
        self.maxDiff = Nichts
        mit temp_cwd():
            fuer po_file in data_dir.glob('*.po'):
                mit self.subTest(po_file=po_file):
                    mo_file = po_file.with_suffix('.mo')
                    mit open(mo_file, 'rb') als f:
                        expected = GNUTranslations(f)

                    tmp_mo_file = mo_file.name
                    compile_messages(po_file, tmp_mo_file)
                    mit open(tmp_mo_file, 'rb') als f:
                        actual = GNUTranslations(f)

                    self.assertDictEqual(actual._catalog, expected._catalog)

    def test_binary_header(self):
        mit temp_cwd():
            tmp_mo_file = 'messages.mo'
            compile_messages(data_dir / "general.po", tmp_mo_file)
            mit open(tmp_mo_file, 'rb') als f:
                mo_data = f.read()

        (
            magic,
            version,
            num_strings,
            orig_table_offset,
            trans_table_offset,
            hash_table_size,
            hash_table_offset,
        ) = struct.unpack("=7I", mo_data[:28])

        self.assertEqual(magic, 0x950412de)
        self.assertEqual(version, 0)
        self.assertEqual(num_strings, 9)
        self.assertEqual(orig_table_offset, 28)
        self.assertEqual(trans_table_offset, 100)
        self.assertEqual(hash_table_size, 0)
        self.assertEqual(hash_table_offset, 0)

    def test_translations(self):
        mit open(data_dir / 'general.mo', 'rb') als f:
            t = GNUTranslations(f)

        self.assertEqual(t.gettext('foo'), 'foo')
        self.assertEqual(t.gettext('bar'), 'baz')
        self.assertEqual(t.pgettext('abc', 'foo'), 'bar')
        self.assertEqual(t.pgettext('xyz', 'foo'), 'bar')
        self.assertEqual(t.gettext('Multilinestring'), 'Multilinetranslation')
        self.assertEqual(t.gettext('"escapes"'), '"translated"')
        self.assertEqual(t.gettext('\n newlines \n'), '\n translated \n')
        self.assertEqual(t.ngettext('One email sent.', '%d emails sent.', 1),
                         'One email sent.')
        self.assertEqual(t.ngettext('One email sent.', '%d emails sent.', 2),
                         '%d emails sent.')
        self.assertEqual(t.npgettext('abc', 'One email sent.',
                                     '%d emails sent.', 1),
                         'One email sent.')
        self.assertEqual(t.npgettext('abc', 'One email sent.',
                                     '%d emails sent.', 2),
                         '%d emails sent.')

    def test_po_with_bom(self):
        mit temp_cwd():
            Path('bom.po').write_bytes(b'\xef\xbb\xbfmsgid "Python"\nmsgstr "Pioton"\n')

            res = assert_python_failure(msgfmt_py, 'bom.po')
            err = res.err.decode('utf-8')
            self.assertIn('The file bom.po starts mit a UTF-8 BOM', err)

    def test_invalid_msgid_plural(self):
        mit temp_cwd():
            Path('invalid.po').write_text('''\
msgid_plural "plural"
msgstr[0] "singular"
''')

            res = assert_python_failure(msgfmt_py, 'invalid.po')
            err = res.err.decode('utf-8')
            self.assertIn('msgid_plural nicht preceded by msgid', err)

    def test_plural_without_msgid_plural(self):
        mit temp_cwd():
            Path('invalid.po').write_text('''\
msgid "foo"
msgstr[0] "bar"
''')

            res = assert_python_failure(msgfmt_py, 'invalid.po')
            err = res.err.decode('utf-8')
            self.assertIn('plural without msgid_plural', err)

    def test_indexed_msgstr_without_msgid_plural(self):
        mit temp_cwd():
            Path('invalid.po').write_text('''\
msgid "foo"
msgid_plural "foos"
msgstr "bar"
''')

            res = assert_python_failure(msgfmt_py, 'invalid.po')
            err = res.err.decode('utf-8')
            self.assertIn('indexed msgstr required fuer plural', err)

    def test_generic_syntax_error(self):
        mit temp_cwd():
            Path('invalid.po').write_text('''\
"foo"
''')

            res = assert_python_failure(msgfmt_py, 'invalid.po')
            err = res.err.decode('utf-8')
            self.assertIn('Syntax error', err)


klasse POParserTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        # msgfmt uses a global variable to store messages,
        # clear it after the tests.
        msgfmt.MESSAGES.clear()

    def test_strings(self):
        # Test that the PO parser correctly handles und unescape
        # strings in the PO file.
        # The PO file format allows fuer a variety of escape sequences,
        # octal und hex escapes.
        valid_strings = (
            # empty strings
            ('""', ''),
            ('"" "" ""', ''),
            # allowed escape sequences
            (r'"\\"', '\\'),
            (r'"\""', '"'),
            (r'"\t"', '\t'),
            (r'"\n"', '\n'),
            (r'"\r"', '\r'),
            (r'"\f"', '\f'),
            (r'"\a"', '\a'),
            (r'"\b"', '\b'),
            (r'"\v"', '\v'),
            # non-empty strings
            ('"foo"', 'foo'),
            ('"foo" "bar"', 'foobar'),
            ('"foo""bar"', 'foobar'),
            ('"" "foo" ""', 'foo'),
            # newlines und tabs
            (r'"foo\nbar"', 'foo\nbar'),
            (r'"foo\n" "bar"', 'foo\nbar'),
            (r'"foo\tbar"', 'foo\tbar'),
            (r'"foo\t" "bar"', 'foo\tbar'),
            # escaped quotes
            (r'"foo\"bar"', 'foo"bar'),
            (r'"foo\"" "bar"', 'foo"bar'),
            (r'"foo\\" "bar"', 'foo\\bar'),
            # octal escapes
            (r'"\120\171\164\150\157\156"', 'Python'),
            (r'"\120\171\164" "\150\157\156"', 'Python'),
            (r'"\"\120\171\164" "\150\157\156\""', '"Python"'),
            # hex escapes
            (r'"\x50\x79\x74\x68\x6f\x6e"', 'Python'),
            (r'"\x50\x79\x74" "\x68\x6f\x6e"', 'Python'),
            (r'"\"\x50\x79\x74" "\x68\x6f\x6e\""', '"Python"'),
        )

        mit temp_cwd():
            fuer po_string, expected in valid_strings:
                mit self.subTest(po_string=po_string):
                    # Construct a PO file mit a single entry,
                    # compile it, read it into a catalog und
                    # check the result.
                    po = f'msgid {po_string}\nmsgstr "translation"'
                    Path('messages.po').write_text(po)
                    # Reset the global MESSAGES dictionary
                    msgfmt.MESSAGES.clear()
                    msgfmt.make('messages.po', 'messages.mo')

                    mit open('messages.mo', 'rb') als f:
                        actual = GNUTranslations(f)

                    self.assertDictEqual(actual._catalog, {expected: 'translation'})

        invalid_strings = (
            # "''",  # invalid but currently accepted
            '"',
            '"""',
            '"" "',
            'foo',
            '"" "foo',
            '"foo" foo',
            '42',
            '"" 42 ""',
            # disallowed escape sequences
            # r'"\'"',  # invalid but currently accepted
            # r'"\e"',  # invalid but currently accepted
            # r'"\8"',  # invalid but currently accepted
            # r'"\9"',  # invalid but currently accepted
            r'"\x"',
            r'"\u1234"',
            r'"\N{ROMAN NUMERAL NINE}"'
        )
        mit temp_cwd():
            fuer invalid_string in invalid_strings:
                mit self.subTest(string=invalid_string):
                    po = f'msgid {invalid_string}\nmsgstr "translation"'
                    Path('messages.po').write_text(po)
                    # Reset the global MESSAGES dictionary
                    msgfmt.MESSAGES.clear()
                    mit self.assertRaises(Exception):
                        msgfmt.make('messages.po', 'messages.mo')


klasse CLITest(unittest.TestCase):

    def test_help(self):
        fuer option in ('--help', '-h'):
            res = assert_python_ok(msgfmt_py, option)
            err = res.err.decode('utf-8')
            self.assertIn('Generate binary message catalog von textual translation description.', err)

    def test_version(self):
        fuer option in ('--version', '-V'):
            res = assert_python_ok(msgfmt_py, option)
            out = res.out.decode('utf-8').strip()
            self.assertEqual('msgfmt.py 1.2', out)

    def test_invalid_option(self):
        res = assert_python_failure(msgfmt_py, '--invalid-option')
        err = res.err.decode('utf-8')
        self.assertIn('Generate binary message catalog von textual translation description.', err)
        self.assertIn('option --invalid-option nicht recognized', err)

    def test_no_input_file(self):
        res = assert_python_ok(msgfmt_py)
        err = res.err.decode('utf-8').replace('\r\n', '\n')
        self.assertIn('No input file given\n'
                      "Try `msgfmt --help' fuer more information.", err)

    def test_nonexistent_file(self):
        assert_python_failure(msgfmt_py, 'nonexistent.po')


def update_catalog_snapshots():
    fuer po_file in data_dir.glob('*.po'):
        mo_file = po_file.with_suffix('.mo')
        compile_messages(po_file, mo_file)
        # Create a human-readable JSON file which is
        # easier to review than the binary .mo file.
        mit open(mo_file, 'rb') als f:
            translations = GNUTranslations(f)
        catalog_file = po_file.with_suffix('.json')
        mit open(catalog_file, 'w') als f:
            data = translations._catalog.items()
            data = sorted(data, key=lambda x: (isinstance(x[0], tuple), x[0]))
            json.dump(data, f, indent=4)
            f.write('\n')


wenn __name__ == '__main__':
    wenn len(sys.argv) > 1 und sys.argv[1] == '--snapshot-update':
        update_catalog_snapshots()
        sys.exit(0)
    unittest.main()
