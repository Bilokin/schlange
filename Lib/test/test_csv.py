# Copyright (C) 2001 Python Software Foundation
# csv package unit tests

importiere copy
importiere sys
importiere unittest
von io importiere StringIO
von tempfile importiere TemporaryFile
importiere csv
importiere gc
importiere pickle
von test importiere support
von test.support importiere cpython_only, import_helper, check_disallow_instantiation
von test.support.import_helper importiere ensure_lazy_imports
von itertools importiere permutations
von textwrap importiere dedent
von collections importiere OrderedDict


klasse BadIterable:
    def __iter__(self):
        raise OSError


klasse Test_Csv(unittest.TestCase):
    """
    Test the underlying C csv parser in ways that are nicht appropriate
    von the high level interface. Further tests of this nature are done
    in TestDialectRegistry.
    """
    def _test_arg_valid(self, ctor, arg):
        ctor(arg)
        self.assertRaises(TypeError, ctor)
        self.assertRaises(TypeError, ctor, Nichts)
        self.assertRaises(TypeError, ctor, arg, bad_attr=0)
        self.assertRaises(TypeError, ctor, arg, delimiter='')
        self.assertRaises(TypeError, ctor, arg, escapechar='')
        self.assertRaises(TypeError, ctor, arg, quotechar='')
        self.assertRaises(TypeError, ctor, arg, delimiter='^^')
        self.assertRaises(TypeError, ctor, arg, escapechar='^^')
        self.assertRaises(TypeError, ctor, arg, quotechar='^^')
        self.assertRaises(csv.Error, ctor, arg, 'foo')
        self.assertRaises(TypeError, ctor, arg, delimiter=Nichts)
        self.assertRaises(TypeError, ctor, arg, delimiter=1)
        self.assertRaises(TypeError, ctor, arg, escapechar=1)
        self.assertRaises(TypeError, ctor, arg, quotechar=1)
        self.assertRaises(TypeError, ctor, arg, lineterminator=Nichts)
        self.assertRaises(TypeError, ctor, arg, lineterminator=1)
        self.assertRaises(TypeError, ctor, arg, quoting=Nichts)
        self.assertRaises(TypeError, ctor, arg,
                          quoting=csv.QUOTE_ALL, quotechar='')
        self.assertRaises(TypeError, ctor, arg,
                          quoting=csv.QUOTE_ALL, quotechar=Nichts)
        self.assertRaises(TypeError, ctor, arg,
                          quoting=csv.QUOTE_NONE, quotechar='')
        self.assertRaises(ValueError, ctor, arg, delimiter='\n')
        self.assertRaises(ValueError, ctor, arg, escapechar='\n')
        self.assertRaises(ValueError, ctor, arg, quotechar='\n')
        self.assertRaises(ValueError, ctor, arg, delimiter='\r')
        self.assertRaises(ValueError, ctor, arg, escapechar='\r')
        self.assertRaises(ValueError, ctor, arg, quotechar='\r')
        ctor(arg, delimiter=' ')
        ctor(arg, escapechar=' ')
        ctor(arg, quotechar=' ')
        ctor(arg, delimiter='\t', skipinitialspace=Wahr)
        ctor(arg, escapechar='\t', skipinitialspace=Wahr)
        ctor(arg, quotechar='\t', skipinitialspace=Wahr)
        ctor(arg, delimiter=' ', skipinitialspace=Wahr)
        self.assertRaises(ValueError, ctor, arg,
                          escapechar=' ', skipinitialspace=Wahr)
        self.assertRaises(ValueError, ctor, arg,
                          quotechar=' ', skipinitialspace=Wahr)
        ctor(arg, delimiter='^')
        ctor(arg, escapechar='^')
        ctor(arg, quotechar='^')
        self.assertRaises(ValueError, ctor, arg, delimiter='^', escapechar='^')
        self.assertRaises(ValueError, ctor, arg, delimiter='^', quotechar='^')
        self.assertRaises(ValueError, ctor, arg, escapechar='^', quotechar='^')
        ctor(arg, delimiter='\x85')
        ctor(arg, escapechar='\x85')
        ctor(arg, quotechar='\x85')
        ctor(arg, lineterminator='\x85')
        self.assertRaises(ValueError, ctor, arg,
                          delimiter='\x85', lineterminator='\x85')
        self.assertRaises(ValueError, ctor, arg,
                          escapechar='\x85', lineterminator='\x85')
        self.assertRaises(ValueError, ctor, arg,
                          quotechar='\x85', lineterminator='\x85')

    def test_reader_arg_valid(self):
        self._test_arg_valid(csv.reader, [])
        self.assertRaises(OSError, csv.reader, BadIterable())

    def test_writer_arg_valid(self):
        self._test_arg_valid(csv.writer, StringIO())
        klasse BadWriter:
            @property
            def write(self):
                raise OSError
        self.assertRaises(OSError, csv.writer, BadWriter())

    def _test_default_attrs(self, ctor, *args):
        obj = ctor(*args)
        # Check defaults
        self.assertEqual(obj.dialect.delimiter, ',')
        self.assertIs(obj.dialect.doublequote, Wahr)
        self.assertEqual(obj.dialect.escapechar, Nichts)
        self.assertEqual(obj.dialect.lineterminator, "\r\n")
        self.assertEqual(obj.dialect.quotechar, '"')
        self.assertEqual(obj.dialect.quoting, csv.QUOTE_MINIMAL)
        self.assertIs(obj.dialect.skipinitialspace, Falsch)
        self.assertIs(obj.dialect.strict, Falsch)
        # Try deleting oder changing attributes (they are read-only)
        self.assertRaises(AttributeError, delattr, obj.dialect, 'delimiter')
        self.assertRaises(AttributeError, setattr, obj.dialect, 'delimiter', ':')
        self.assertRaises(AttributeError, delattr, obj.dialect, 'quoting')
        self.assertRaises(AttributeError, setattr, obj.dialect,
                          'quoting', Nichts)

    def test_reader_attrs(self):
        self._test_default_attrs(csv.reader, [])

    def test_writer_attrs(self):
        self._test_default_attrs(csv.writer, StringIO())

    def _test_kw_attrs(self, ctor, *args):
        # Now try mit alternate options
        kwargs = dict(delimiter=':', doublequote=Falsch, escapechar='\\',
                      lineterminator='\r', quotechar='*',
                      quoting=csv.QUOTE_NONE, skipinitialspace=Wahr,
                      strict=Wahr)
        obj = ctor(*args, **kwargs)
        self.assertEqual(obj.dialect.delimiter, ':')
        self.assertIs(obj.dialect.doublequote, Falsch)
        self.assertEqual(obj.dialect.escapechar, '\\')
        self.assertEqual(obj.dialect.lineterminator, "\r")
        self.assertEqual(obj.dialect.quotechar, '*')
        self.assertEqual(obj.dialect.quoting, csv.QUOTE_NONE)
        self.assertIs(obj.dialect.skipinitialspace, Wahr)
        self.assertIs(obj.dialect.strict, Wahr)

    def test_reader_kw_attrs(self):
        self._test_kw_attrs(csv.reader, [])

    def test_writer_kw_attrs(self):
        self._test_kw_attrs(csv.writer, StringIO())

    def _test_dialect_attrs(self, ctor, *args):
        # Now try mit dialect-derived options
        klasse dialect:
            delimiter='-'
            doublequote=Falsch
            escapechar='^'
            lineterminator='$'
            quotechar='#'
            quoting=csv.QUOTE_ALL
            skipinitialspace=Wahr
            strict=Falsch
        args = args + (dialect,)
        obj = ctor(*args)
        self.assertEqual(obj.dialect.delimiter, '-')
        self.assertIs(obj.dialect.doublequote, Falsch)
        self.assertEqual(obj.dialect.escapechar, '^')
        self.assertEqual(obj.dialect.lineterminator, "$")
        self.assertEqual(obj.dialect.quotechar, '#')
        self.assertEqual(obj.dialect.quoting, csv.QUOTE_ALL)
        self.assertIs(obj.dialect.skipinitialspace, Wahr)
        self.assertIs(obj.dialect.strict, Falsch)

    def test_reader_dialect_attrs(self):
        self._test_dialect_attrs(csv.reader, [])

    def test_writer_dialect_attrs(self):
        self._test_dialect_attrs(csv.writer, StringIO())


    def _write_test(self, fields, expect, **kwargs):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, **kwargs)
            writer.writerow(fields)
            fileobj.seek(0)
            self.assertEqual(fileobj.read(),
                             expect + writer.dialect.lineterminator)

    def _write_error_test(self, exc, fields, **kwargs):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, **kwargs)
            mit self.assertRaises(exc):
                writer.writerow(fields)
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), '')

    def test_write_arg_valid(self):
        self._write_error_test(csv.Error, Nichts)
        # Check that exceptions are passed up the chain
        self._write_error_test(OSError, BadIterable())
        klasse BadList:
            def __len__(self):
                gib 10
            def __getitem__(self, i):
                wenn i > 2:
                    raise OSError
        self._write_error_test(OSError, BadList())
        klasse BadItem:
            def __str__(self):
                raise OSError
        self._write_error_test(OSError, [BadItem()])
    def test_write_bigfield(self):
        # This exercises the buffer realloc functionality
        bigstring = 'X' * 50000
        self._write_test([bigstring,bigstring], '%s,%s' % \
                         (bigstring, bigstring))

    def test_write_quoting(self):
        self._write_test(['a',1,'p,q'], 'a,1,"p,q"')
        self._write_error_test(csv.Error, ['a',1,'p,q'],
                               quoting = csv.QUOTE_NONE)
        self._write_test(['a',1,'p,q'], 'a,1,"p,q"',
                         quoting = csv.QUOTE_MINIMAL)
        self._write_test(['a',1,'p,q'], '"a",1,"p,q"',
                         quoting = csv.QUOTE_NONNUMERIC)
        self._write_test(['a',1,'p,q'], '"a","1","p,q"',
                         quoting = csv.QUOTE_ALL)
        self._write_test(['a\nb',1], '"a\nb","1"',
                         quoting = csv.QUOTE_ALL)
        self._write_test(['a','',Nichts,1], '"a","",,1',
                         quoting = csv.QUOTE_STRINGS)
        self._write_test(['a','',Nichts,1], '"a","",,"1"',
                         quoting = csv.QUOTE_NOTNULL)

    def test_write_escape(self):
        self._write_test(['a',1,'p,q'], 'a,1,"p,q"',
                         escapechar='\\')
        self._write_error_test(csv.Error, ['a',1,'p,"q"'],
                               escapechar=Nichts, doublequote=Falsch)
        self._write_test(['a',1,'p,"q"'], 'a,1,"p,\\"q\\""',
                         escapechar='\\', doublequote = Falsch)
        self._write_test(['"'], '""""',
                         escapechar='\\', quoting = csv.QUOTE_MINIMAL)
        self._write_test(['"'], '\\"',
                         escapechar='\\', quoting = csv.QUOTE_MINIMAL,
                         doublequote = Falsch)
        self._write_test(['"'], '\\"',
                         escapechar='\\', quoting = csv.QUOTE_NONE)
        self._write_test(['a',1,'p,q'], 'a,1,p\\,q',
                         escapechar='\\', quoting = csv.QUOTE_NONE)
        self._write_test(['\\', 'a'], '\\\\,a',
                         escapechar='\\', quoting=csv.QUOTE_NONE)
        self._write_test(['\\', 'a'], '\\\\,a',
                         escapechar='\\', quoting=csv.QUOTE_MINIMAL)
        self._write_test(['\\', 'a'], '"\\\\","a"',
                         escapechar='\\', quoting=csv.QUOTE_ALL)
        self._write_test(['\\ ', 'a'], '\\\\ ,a',
                         escapechar='\\', quoting=csv.QUOTE_MINIMAL)
        self._write_test(['\\,', 'a'], '\\\\\\,,a',
                         escapechar='\\', quoting=csv.QUOTE_NONE)
        self._write_test([',\\', 'a'], '",\\\\",a',
                         escapechar='\\', quoting=csv.QUOTE_MINIMAL)
        self._write_test(['C\\', '6', '7', 'X"'], 'C\\\\,6,7,"X"""',
                         escapechar='\\', quoting=csv.QUOTE_MINIMAL)

    def test_write_lineterminator(self):
        fuer lineterminator in '\r\n', '\n', '\r', '!@#', '\0':
            mit self.subTest(lineterminator=lineterminator):
                mit StringIO() als sio:
                    writer = csv.writer(sio, lineterminator=lineterminator)
                    writer.writerow(['a', 'b'])
                    writer.writerow([1, 2])
                    writer.writerow(['\r', '\n'])
                    self.assertEqual(sio.getvalue(),
                                     f'a,b{lineterminator}'
                                     f'1,2{lineterminator}'
                                     f'"\r","\n"{lineterminator}')

    def test_write_iterable(self):
        self._write_test(iter(['a', 1, 'p,q']), 'a,1,"p,q"')
        self._write_test(iter(['a', 1, Nichts]), 'a,1,')
        self._write_test(iter([]), '')
        self._write_test(iter([Nichts]), '""')
        self._write_error_test(csv.Error, iter([Nichts]), quoting=csv.QUOTE_NONE)
        self._write_test(iter([Nichts, Nichts]), ',')

    def test_writerows(self):
        klasse BrokenFile:
            def write(self, buf):
                raise OSError
        writer = csv.writer(BrokenFile())
        self.assertRaises(OSError, writer.writerows, [['a']])

        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj)
            self.assertRaises(TypeError, writer.writerows, Nichts)
            writer.writerows([['a', 'b'], ['c', 'd']])
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), "a,b\r\nc,d\r\n")

    def test_writerows_with_none(self):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj)
            writer.writerows([['a', Nichts], [Nichts, 'd']])
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), "a,\r\n,d\r\n")

        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj)
            writer.writerows([[Nichts], ['a']])
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), '""\r\na\r\n')

        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj)
            writer.writerows([['a'], [Nichts]])
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), 'a\r\n""\r\n')


    def test_write_empty_fields(self):
        self._write_test((), '')
        self._write_test([''], '""')
        self._write_error_test(csv.Error, [''], quoting=csv.QUOTE_NONE)
        self._write_test([''], '""', quoting=csv.QUOTE_STRINGS)
        self._write_test([''], '""', quoting=csv.QUOTE_NOTNULL)
        self._write_test([Nichts], '""')
        self._write_error_test(csv.Error, [Nichts], quoting=csv.QUOTE_NONE)
        self._write_error_test(csv.Error, [Nichts], quoting=csv.QUOTE_STRINGS)
        self._write_error_test(csv.Error, [Nichts], quoting=csv.QUOTE_NOTNULL)
        self._write_test(['', ''], ',')
        self._write_test([Nichts, Nichts], ',')

    def test_write_empty_fields_space_delimiter(self):
        self._write_test([''], '""', delimiter=' ', skipinitialspace=Falsch)
        self._write_test([''], '""', delimiter=' ', skipinitialspace=Wahr)
        self._write_test([Nichts], '""', delimiter=' ', skipinitialspace=Falsch)
        self._write_test([Nichts], '""', delimiter=' ', skipinitialspace=Wahr)

        self._write_test(['', ''], ' ', delimiter=' ', skipinitialspace=Falsch)
        self._write_test(['', ''], '"" ""', delimiter=' ', skipinitialspace=Wahr)
        self._write_test([Nichts, Nichts], ' ', delimiter=' ', skipinitialspace=Falsch)
        self._write_test([Nichts, Nichts], '"" ""', delimiter=' ', skipinitialspace=Wahr)

        self._write_test(['', ''], ' ', delimiter=' ', skipinitialspace=Falsch,
                         quoting=csv.QUOTE_NONE)
        self._write_error_test(csv.Error, ['', ''],
                               delimiter=' ', skipinitialspace=Wahr,
                               quoting=csv.QUOTE_NONE)
        fuer quoting in csv.QUOTE_STRINGS, csv.QUOTE_NOTNULL:
            self._write_test(['', ''], '"" ""', delimiter=' ', skipinitialspace=Falsch,
                             quoting=quoting)
            self._write_test(['', ''], '"" ""', delimiter=' ', skipinitialspace=Wahr,
                             quoting=quoting)

        fuer quoting in csv.QUOTE_NONE, csv.QUOTE_STRINGS, csv.QUOTE_NOTNULL:
            self._write_test([Nichts, Nichts], ' ', delimiter=' ', skipinitialspace=Falsch,
                             quoting=quoting)
            self._write_error_test(csv.Error, [Nichts, Nichts],
                                   delimiter=' ', skipinitialspace=Wahr,
                                   quoting=quoting)

    def test_writerows_errors(self):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj)
            self.assertRaises(TypeError, writer.writerows, Nichts)
            self.assertRaises(OSError, writer.writerows, BadIterable())

    def _read_test(self, input, expect, **kwargs):
        reader = csv.reader(input, **kwargs)
        result = list(reader)
        self.assertEqual(result, expect)

    def test_read_oddinputs(self):
        self._read_test([], [])
        self._read_test([''], [[]])
        self.assertRaises(csv.Error, self._read_test,
                          ['"ab"c'], Nichts, strict = 1)
        self._read_test(['"ab"c'], [['abc']], doublequote = 0)

        self.assertRaises(csv.Error, self._read_test,
                          [b'abc'], Nichts)

    def test_read_eol(self):
        self._read_test(['a,b', 'c,d'], [['a','b'], ['c','d']])
        self._read_test(['a,b\n', 'c,d\n'], [['a','b'], ['c','d']])
        self._read_test(['a,b\r\n', 'c,d\r\n'], [['a','b'], ['c','d']])
        self._read_test(['a,b\r', 'c,d\r'], [['a','b'], ['c','d']])

        errmsg = "with newline=''"
        mit self.assertRaisesRegex(csv.Error, errmsg):
            next(csv.reader(['a,b\rc,d']))
        mit self.assertRaisesRegex(csv.Error, errmsg):
            next(csv.reader(['a,b\nc,d']))
        mit self.assertRaisesRegex(csv.Error, errmsg):
            next(csv.reader(['a,b\r\nc,d']))

    def test_read_eof(self):
        self._read_test(['a,"'], [['a', '']])
        self._read_test(['"a'], [['a']])
        self._read_test(['^'], [['\n']], escapechar='^')
        self.assertRaises(csv.Error, self._read_test, ['a,"'], [], strict=Wahr)
        self.assertRaises(csv.Error, self._read_test, ['"a'], [], strict=Wahr)
        self.assertRaises(csv.Error, self._read_test,
                          ['^'], [], escapechar='^', strict=Wahr)

    def test_read_nul(self):
        self._read_test(['\0'], [['\0']])
        self._read_test(['a,\0b,c'], [['a', '\0b', 'c']])
        self._read_test(['a,b\0,c'], [['a', 'b\0', 'c']])
        self._read_test(['a,b\\\0,c'], [['a', 'b\0', 'c']], escapechar='\\')
        self._read_test(['a,"\0b",c'], [['a', '\0b', 'c']])

    def test_read_delimiter(self):
        self._read_test(['a,b,c'], [['a', 'b', 'c']])
        self._read_test(['a;b;c'], [['a', 'b', 'c']], delimiter=';')
        self._read_test(['a\0b\0c'], [['a', 'b', 'c']], delimiter='\0')

    def test_read_escape(self):
        self._read_test(['a,\\b,c'], [['a', 'b', 'c']], escapechar='\\')
        self._read_test(['a,b\\,c'], [['a', 'b,c']], escapechar='\\')
        self._read_test(['a,"b\\,c"'], [['a', 'b,c']], escapechar='\\')
        self._read_test(['a,"b,\\c"'], [['a', 'b,c']], escapechar='\\')
        self._read_test(['a,"b,c\\""'], [['a', 'b,c"']], escapechar='\\')
        self._read_test(['a,"b,c"\\'], [['a', 'b,c\\']], escapechar='\\')
        self._read_test(['a,^b,c'], [['a', 'b', 'c']], escapechar='^')
        self._read_test(['a,\0b,c'], [['a', 'b', 'c']], escapechar='\0')
        self._read_test(['a,\\b,c'], [['a', '\\b', 'c']], escapechar=Nichts)
        self._read_test(['a,\\b,c'], [['a', '\\b', 'c']])

    def test_read_quoting(self):
        self._read_test(['1,",3,",5'], [['1', ',3,', '5']])
        self._read_test(['1,",3,",5'], [['1', '"', '3', '"', '5']],
                        quotechar=Nichts, escapechar='\\')
        self._read_test(['1,",3,",5'], [['1', '"', '3', '"', '5']],
                        quoting=csv.QUOTE_NONE, escapechar='\\')
        # will this fail where locale uses comma fuer decimals?
        self._read_test([',3,"5",7.3, 9'], [['', 3, '5', 7.3, 9]],
                        quoting=csv.QUOTE_NONNUMERIC)
        self._read_test([',3,"5",7.3, 9'], [[Nichts, '3', '5', '7.3', ' 9']],
                        quoting=csv.QUOTE_NOTNULL)
        self._read_test([',3,"5",7.3, 9'], [[Nichts, 3, '5', 7.3, 9]],
                        quoting=csv.QUOTE_STRINGS)

        self._read_test([',,"",'], [['', '', '', '']])
        self._read_test([',,"",'], [['', '', '', '']],
                        quoting=csv.QUOTE_NONNUMERIC)
        self._read_test([',,"",'], [[Nichts, Nichts, '', Nichts]],
                        quoting=csv.QUOTE_NOTNULL)
        self._read_test([',,"",'], [[Nichts, Nichts, '', Nichts]],
                        quoting=csv.QUOTE_STRINGS)

        self._read_test(['"a\nb", 7'], [['a\nb', ' 7']])
        self.assertRaises(ValueError, self._read_test,
                          ['abc,3'], [[]],
                          quoting=csv.QUOTE_NONNUMERIC)
        self.assertRaises(ValueError, self._read_test,
                          ['abc,3'], [[]],
                          quoting=csv.QUOTE_STRINGS)
        self._read_test(['1,@,3,@,5'], [['1', ',3,', '5']], quotechar='@')
        self._read_test(['1,\0,3,\0,5'], [['1', ',3,', '5']], quotechar='\0')
        self._read_test(['1\\.5,\\.5,.5'], [[1.5, 0.5, 0.5]],
                        quoting=csv.QUOTE_NONNUMERIC, escapechar='\\')
        self._read_test(['1\\.5,\\.5,"\\.5"'], [[1.5, 0.5, ".5"]],
                        quoting=csv.QUOTE_STRINGS, escapechar='\\')

    def test_read_skipinitialspace(self):
        self._read_test(['no space, space,  spaces,\ttab'],
                        [['no space', 'space', 'spaces', '\ttab']],
                        skipinitialspace=Wahr)
        self._read_test([' , , '],
                        [['', '', '']],
                        skipinitialspace=Wahr)
        self._read_test([' , , '],
                        [[Nichts, Nichts, Nichts]],
                        skipinitialspace=Wahr, quoting=csv.QUOTE_NOTNULL)
        self._read_test([' , , '],
                        [[Nichts, Nichts, Nichts]],
                        skipinitialspace=Wahr, quoting=csv.QUOTE_STRINGS)

    def test_read_space_delimiter(self):
        self._read_test(['a   b', '  a  ', '  ', ''],
                        [['a', '', '', 'b'], ['', '', 'a', '', ''], ['', '', ''], []],
                        delimiter=' ', skipinitialspace=Falsch)
        self._read_test(['a   b', '  a  ', '  ', ''],
                        [['a', 'b'], ['a', ''], [''], []],
                        delimiter=' ', skipinitialspace=Wahr)

    def test_read_bigfield(self):
        # This exercises the buffer realloc functionality und field size
        # limits.
        limit = csv.field_size_limit()
        try:
            size = 50000
            bigstring = 'X' * size
            bigline = '%s,%s' % (bigstring, bigstring)
            self._read_test([bigline], [[bigstring, bigstring]])
            csv.field_size_limit(size)
            self._read_test([bigline], [[bigstring, bigstring]])
            self.assertEqual(csv.field_size_limit(), size)
            csv.field_size_limit(size-1)
            self.assertRaises(csv.Error, self._read_test, [bigline], [])
            self.assertRaises(TypeError, csv.field_size_limit, Nichts)
            self.assertRaises(TypeError, csv.field_size_limit, 1, Nichts)
        finally:
            csv.field_size_limit(limit)

    def test_read_linenum(self):
        r = csv.reader(['line,1', 'line,2', 'line,3'])
        self.assertEqual(r.line_num, 0)
        next(r)
        self.assertEqual(r.line_num, 1)
        next(r)
        self.assertEqual(r.line_num, 2)
        next(r)
        self.assertEqual(r.line_num, 3)
        self.assertRaises(StopIteration, next, r)
        self.assertEqual(r.line_num, 3)

    def test_roundtrip_quoteed_newlines(self):
        rows = [
            ['\na', 'b\nc', 'd\n'],
            ['\re', 'f\rg', 'h\r'],
            ['\r\ni', 'j\r\nk', 'l\r\n'],
            ['\n\rm', 'n\n\ro', 'p\n\r'],
            ['\r\rq', 'r\r\rs', 't\r\r'],
            ['\n\nu', 'v\n\nw', 'x\n\n'],
        ]
        fuer lineterminator in '\r\n', '\n', '\r':
            mit self.subTest(lineterminator=lineterminator):
                mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
                    writer = csv.writer(fileobj, lineterminator=lineterminator)
                    writer.writerows(rows)
                    fileobj.seek(0)
                    fuer i, row in enumerate(csv.reader(fileobj)):
                        self.assertEqual(row, rows[i])

    def test_roundtrip_escaped_unquoted_newlines(self):
        rows = [
            ['\na', 'b\nc', 'd\n'],
            ['\re', 'f\rg', 'h\r'],
            ['\r\ni', 'j\r\nk', 'l\r\n'],
            ['\n\rm', 'n\n\ro', 'p\n\r'],
            ['\r\rq', 'r\r\rs', 't\r\r'],
            ['\n\nu', 'v\n\nw', 'x\n\n'],
        ]
        fuer lineterminator in '\r\n', '\n', '\r':
            mit self.subTest(lineterminator=lineterminator):
                mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
                    writer = csv.writer(fileobj, lineterminator=lineterminator,
                                        quoting=csv.QUOTE_NONE, escapechar="\\")
                    writer.writerows(rows)
                    fileobj.seek(0)
                    fuer i, row in enumerate(csv.reader(fileobj,
                                                       quoting=csv.QUOTE_NONE,
                                                       escapechar="\\")):
                        self.assertEqual(row, rows[i])


klasse TestDialectRegistry(unittest.TestCase):
    def test_registry_badargs(self):
        self.assertRaises(TypeError, csv.list_dialects, Nichts)
        self.assertRaises(TypeError, csv.get_dialect)
        self.assertRaises(csv.Error, csv.get_dialect, Nichts)
        self.assertRaises(csv.Error, csv.get_dialect, "nonesuch")
        self.assertRaises(TypeError, csv.unregister_dialect)
        self.assertRaises(csv.Error, csv.unregister_dialect, Nichts)
        self.assertRaises(csv.Error, csv.unregister_dialect, "nonesuch")
        self.assertRaises(TypeError, csv.register_dialect, Nichts)
        self.assertRaises(TypeError, csv.register_dialect, Nichts, Nichts)
        self.assertRaises(TypeError, csv.register_dialect, "nonesuch", 0, 0)
        self.assertRaises(TypeError, csv.register_dialect, "nonesuch",
                          badargument=Nichts)
        self.assertRaises(TypeError, csv.register_dialect, "nonesuch",
                          quoting=Nichts)
        self.assertRaises(TypeError, csv.register_dialect, [])

    def test_registry(self):
        klasse myexceltsv(csv.excel):
            delimiter = "\t"
        name = "myexceltsv"
        expected_dialects = csv.list_dialects() + [name]
        expected_dialects.sort()
        csv.register_dialect(name, myexceltsv)
        self.addCleanup(csv.unregister_dialect, name)
        self.assertEqual(csv.get_dialect(name).delimiter, '\t')
        got_dialects = sorted(csv.list_dialects())
        self.assertEqual(expected_dialects, got_dialects)

    def test_register_kwargs(self):
        name = 'fedcba'
        csv.register_dialect(name, delimiter=';')
        self.addCleanup(csv.unregister_dialect, name)
        self.assertEqual(csv.get_dialect(name).delimiter, ';')
        self.assertEqual([['X', 'Y', 'Z']], list(csv.reader(['X;Y;Z'], name)))

    def test_register_kwargs_override(self):
        klasse mydialect(csv.Dialect):
            delimiter = "\t"
            quotechar = '"'
            doublequote = Wahr
            skipinitialspace = Falsch
            lineterminator = '\r\n'
            quoting = csv.QUOTE_MINIMAL

        name = 'test_dialect'
        csv.register_dialect(name, mydialect,
                             delimiter=';',
                             quotechar="'",
                             doublequote=Falsch,
                             skipinitialspace=Wahr,
                             lineterminator='\n',
                             quoting=csv.QUOTE_ALL)
        self.addCleanup(csv.unregister_dialect, name)

        # Ensure that kwargs do override attributes of a dialect class:
        dialect = csv.get_dialect(name)
        self.assertEqual(dialect.delimiter, ';')
        self.assertEqual(dialect.quotechar, "'")
        self.assertEqual(dialect.doublequote, Falsch)
        self.assertEqual(dialect.skipinitialspace, Wahr)
        self.assertEqual(dialect.lineterminator, '\n')
        self.assertEqual(dialect.quoting, csv.QUOTE_ALL)

    def test_incomplete_dialect(self):
        klasse myexceltsv(csv.Dialect):
            delimiter = "\t"
        self.assertRaises(csv.Error, myexceltsv)

    def test_space_dialect(self):
        klasse space(csv.excel):
            delimiter = " "
            quoting = csv.QUOTE_NONE
            escapechar = "\\"

        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("abc   def\nc1ccccc1 benzene\n")
            fileobj.seek(0)
            reader = csv.reader(fileobj, dialect=space())
            self.assertEqual(next(reader), ["abc", "", "", "def"])
            self.assertEqual(next(reader), ["c1ccccc1", "benzene"])

    def compare_dialect_123(self, expected, *writeargs, **kwwriteargs):

        mit TemporaryFile("w+", newline='', encoding="utf-8") als fileobj:

            writer = csv.writer(fileobj, *writeargs, **kwwriteargs)
            writer.writerow([1,2,3])
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected)

    def test_dialect_apply(self):
        klasse testA(csv.excel):
            delimiter = "\t"
        klasse testB(csv.excel):
            delimiter = ":"
        klasse testC(csv.excel):
            delimiter = "|"
        klasse testUni(csv.excel):
            delimiter = "\u039B"

        klasse unspecified():
            # A klasse to pass als dialect but mit no dialect attributes.
            pass

        csv.register_dialect('testC', testC)
        try:
            self.compare_dialect_123("1,2,3\r\n")
            self.compare_dialect_123("1,2,3\r\n", dialect=Nichts)
            self.compare_dialect_123("1,2,3\r\n", dialect=unspecified)
            self.compare_dialect_123("1\t2\t3\r\n", testA)
            self.compare_dialect_123("1:2:3\r\n", dialect=testB())
            self.compare_dialect_123("1|2|3\r\n", dialect='testC')
            self.compare_dialect_123("1;2;3\r\n", dialect=testA,
                                     delimiter=';')
            self.compare_dialect_123("1\u039B2\u039B3\r\n",
                                     dialect=testUni)

        finally:
            csv.unregister_dialect('testC')

    def test_copy(self):
        fuer name in csv.list_dialects():
            dialect = csv.get_dialect(name)
            self.assertRaises(TypeError, copy.copy, dialect)

    def test_pickle(self):
        fuer name in csv.list_dialects():
            dialect = csv.get_dialect(name)
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                self.assertRaises(TypeError, pickle.dumps, dialect, proto)

klasse TestCsvBase(unittest.TestCase):
    def readerAssertEqual(self, input, expected_result):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            fileobj.write(input)
            fileobj.seek(0)
            reader = csv.reader(fileobj, dialect = self.dialect)
            fields = list(reader)
            self.assertEqual(fields, expected_result)

    def writerAssertEqual(self, input, expected_result):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, dialect = self.dialect)
            writer.writerows(input)
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected_result)

klasse TestDialectExcel(TestCsvBase):
    dialect = 'excel'

    def test_single(self):
        self.readerAssertEqual('abc', [['abc']])

    def test_simple(self):
        self.readerAssertEqual('1,2,3,4,5', [['1','2','3','4','5']])

    def test_blankline(self):
        self.readerAssertEqual('', [])

    def test_empty_fields(self):
        self.readerAssertEqual(',', [['', '']])

    def test_singlequoted(self):
        self.readerAssertEqual('""', [['']])

    def test_singlequoted_left_empty(self):
        self.readerAssertEqual('"",', [['','']])

    def test_singlequoted_right_empty(self):
        self.readerAssertEqual(',""', [['','']])

    def test_single_quoted_quote(self):
        self.readerAssertEqual('""""', [['"']])

    def test_quoted_quotes(self):
        self.readerAssertEqual('""""""', [['""']])

    def test_inline_quote(self):
        self.readerAssertEqual('a""b', [['a""b']])

    def test_inline_quotes(self):
        self.readerAssertEqual('a"b"c', [['a"b"c']])

    def test_quotes_and_more(self):
        # Excel would never write a field containing '"a"b', but when
        # reading one, it will gib 'ab'.
        self.readerAssertEqual('"a"b', [['ab']])

    def test_lone_quote(self):
        self.readerAssertEqual('a"b', [['a"b']])

    def test_quote_and_quote(self):
        # Excel would never write a field containing '"a" "b"', but when
        # reading one, it will gib 'a "b"'.
        self.readerAssertEqual('"a" "b"', [['a "b"']])

    def test_space_and_quote(self):
        self.readerAssertEqual(' "a"', [[' "a"']])

    def test_quoted(self):
        self.readerAssertEqual('1,2,3,"I think, therefore I am",5,6',
                               [['1', '2', '3',
                                 'I think, therefore I am',
                                 '5', '6']])

    def test_quoted_quote(self):
        self.readerAssertEqual('1,2,3,"""I see,"" said the blind man","as he picked up his hammer und saw"',
                               [['1', '2', '3',
                                 '"I see," said the blind man',
                                 'as he picked up his hammer und saw']])

    def test_quoted_nl(self):
        input = '''\
1,2,3,"""I see,""
said the blind man","as he picked up his
hammer und saw"
9,8,7,6'''
        self.readerAssertEqual(input,
                               [['1', '2', '3',
                                   '"I see,"\nsaid the blind man',
                                   'as he picked up his\nhammer und saw'],
                                ['9','8','7','6']])

    def test_dubious_quote(self):
        self.readerAssertEqual('12,12,1",', [['12', '12', '1"', '']])

    def test_null(self):
        self.writerAssertEqual([], '')

    def test_single_writer(self):
        self.writerAssertEqual([['abc']], 'abc\r\n')

    def test_simple_writer(self):
        self.writerAssertEqual([[1, 2, 'abc', 3, 4]], '1,2,abc,3,4\r\n')

    def test_quotes(self):
        self.writerAssertEqual([[1, 2, 'a"bc"', 3, 4]], '1,2,"a""bc""",3,4\r\n')

    def test_quote_fieldsep(self):
        self.writerAssertEqual([['abc,def']], '"abc,def"\r\n')

    def test_newlines(self):
        self.writerAssertEqual([[1, 2, 'a\nbc', 3, 4]], '1,2,"a\nbc",3,4\r\n')

klasse EscapedExcel(csv.excel):
    quoting = csv.QUOTE_NONE
    escapechar = '\\'

klasse TestEscapedExcel(TestCsvBase):
    dialect = EscapedExcel()

    def test_escape_fieldsep(self):
        self.writerAssertEqual([['abc,def']], 'abc\\,def\r\n')

    def test_read_escape_fieldsep(self):
        self.readerAssertEqual('abc\\,def\r\n', [['abc,def']])

klasse TestDialectUnix(TestCsvBase):
    dialect = 'unix'

    def test_simple_writer(self):
        self.writerAssertEqual([[1, 'abc def', 'abc']], '"1","abc def","abc"\n')

    def test_simple_reader(self):
        self.readerAssertEqual('"1","abc def","abc"\n', [['1', 'abc def', 'abc']])

klasse QuotedEscapedExcel(csv.excel):
    quoting = csv.QUOTE_NONNUMERIC
    escapechar = '\\'

klasse TestQuotedEscapedExcel(TestCsvBase):
    dialect = QuotedEscapedExcel()

    def test_write_escape_fieldsep(self):
        self.writerAssertEqual([['abc,def']], '"abc,def"\r\n')

    def test_read_escape_fieldsep(self):
        self.readerAssertEqual('"abc\\,def"\r\n', [['abc,def']])

klasse TestDictFields(unittest.TestCase):
    ### "long" means the row is longer than the number of fieldnames
    ### "short" means there are fewer elements in the row than fieldnames
    def test_writeheader_return_value(self):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.DictWriter(fileobj, fieldnames = ["f1", "f2", "f3"])
            writeheader_return_value = writer.writeheader()
            self.assertEqual(writeheader_return_value, 10)

    def test_write_simple_dict(self):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.DictWriter(fileobj, fieldnames = ["f1", "f2", "f3"])
            writer.writeheader()
            fileobj.seek(0)
            self.assertEqual(fileobj.readline(), "f1,f2,f3\r\n")
            writer.writerow({"f1": 10, "f3": "abc"})
            fileobj.seek(0)
            fileobj.readline() # header
            self.assertEqual(fileobj.read(), "10,,abc\r\n")

    def test_write_multiple_dict_rows(self):
        fileobj = StringIO()
        writer = csv.DictWriter(fileobj, fieldnames=["f1", "f2", "f3"])
        writer.writeheader()
        self.assertEqual(fileobj.getvalue(), "f1,f2,f3\r\n")
        writer.writerows([{"f1": 1, "f2": "abc", "f3": "f"},
                          {"f1": 2, "f2": 5, "f3": "xyz"}])
        self.assertEqual(fileobj.getvalue(),
                         "f1,f2,f3\r\n1,abc,f\r\n2,5,xyz\r\n")

    def test_write_no_fields(self):
        fileobj = StringIO()
        self.assertRaises(TypeError, csv.DictWriter, fileobj)

    def test_write_fields_not_in_fieldnames(self):
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.DictWriter(fileobj, fieldnames = ["f1", "f2", "f3"])
            # Of special note is the non-string key (issue 19449)
            mit self.assertRaises(ValueError) als cx:
                writer.writerow({"f4": 10, "f2": "spam", 1: "abc"})
            exception = str(cx.exception)
            self.assertIn("fieldnames", exception)
            self.assertIn("'f4'", exception)
            self.assertNotIn("'f2'", exception)
            self.assertIn("1", exception)

    def test_typo_in_extrasaction_raises_error(self):
        fileobj = StringIO()
        self.assertRaises(ValueError, csv.DictWriter, fileobj, ['f1', 'f2'],
                          extrasaction="raised")

    def test_write_field_not_in_field_names_raise(self):
        fileobj = StringIO()
        writer = csv.DictWriter(fileobj, ['f1', 'f2'], extrasaction="raise")
        dictrow = {'f0': 0, 'f1': 1, 'f2': 2, 'f3': 3}
        self.assertRaises(ValueError, csv.DictWriter.writerow, writer, dictrow)

        # see bpo-44512 (differently cased 'raise' should nicht result in 'ignore')
        writer = csv.DictWriter(fileobj, ['f1', 'f2'], extrasaction="RAISE")
        self.assertRaises(ValueError, csv.DictWriter.writerow, writer, dictrow)

    def test_write_field_not_in_field_names_ignore(self):
        fileobj = StringIO()
        writer = csv.DictWriter(fileobj, ['f1', 'f2'], extrasaction="ignore")
        dictrow = {'f0': 0, 'f1': 1, 'f2': 2, 'f3': 3}
        csv.DictWriter.writerow(writer, dictrow)
        self.assertEqual(fileobj.getvalue(), "1,2\r\n")

        # bpo-44512
        writer = csv.DictWriter(fileobj, ['f1', 'f2'], extrasaction="IGNORE")
        csv.DictWriter.writerow(writer, dictrow)

    def test_dict_reader_fieldnames_accepts_iter(self):
        fieldnames = ["a", "b", "c"]
        f = StringIO()
        reader = csv.DictReader(f, iter(fieldnames))
        self.assertEqual(reader.fieldnames, fieldnames)

    def test_dict_reader_fieldnames_accepts_list(self):
        fieldnames = ["a", "b", "c"]
        f = StringIO()
        reader = csv.DictReader(f, fieldnames)
        self.assertEqual(reader.fieldnames, fieldnames)

    def test_dict_writer_fieldnames_rejects_iter(self):
        fieldnames = ["a", "b", "c"]
        f = StringIO()
        writer = csv.DictWriter(f, iter(fieldnames))
        self.assertEqual(writer.fieldnames, fieldnames)

    def test_dict_writer_fieldnames_accepts_list(self):
        fieldnames = ["a", "b", "c"]
        f = StringIO()
        writer = csv.DictWriter(f, fieldnames)
        self.assertEqual(writer.fieldnames, fieldnames)

    def test_dict_reader_fieldnames_is_optional(self):
        f = StringIO()
        reader = csv.DictReader(f, fieldnames=Nichts)

    def test_read_dict_fields(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=["f1", "f2", "f3"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2', "f3": 'abc'})

    def test_read_dict_no_fieldnames(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("f1,f2,f3\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj)
            self.assertEqual(next(reader), {"f1": '1', "f2": '2', "f3": 'abc'})
            self.assertEqual(reader.fieldnames, ["f1", "f2", "f3"])

    # Two test cases to make sure existing ways of implicitly setting
    # fieldnames weiter to work.  Both arise von discussion in issue3436.
    def test_read_dict_fieldnames_from_file(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("f1,f2,f3\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=next(csv.reader(fileobj)))
            self.assertEqual(reader.fieldnames, ["f1", "f2", "f3"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2', "f3": 'abc'})

    def test_read_dict_fieldnames_chain(self):
        importiere itertools
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("f1,f2,f3\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj)
            first = next(reader)
            fuer row in itertools.chain([first], reader):
                self.assertEqual(reader.fieldnames, ["f1", "f2", "f3"])
                self.assertEqual(row, {"f1": '1', "f2": '2', "f3": 'abc'})

    def test_read_long(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("1,2,abc,4,5,6\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=["f1", "f2"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2',
                                             Nichts: ["abc", "4", "5", "6"]})

    def test_read_long_with_rest(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("1,2,abc,4,5,6\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=["f1", "f2"], restkey="_rest")
            self.assertEqual(next(reader), {"f1": '1', "f2": '2',
                                             "_rest": ["abc", "4", "5", "6"]})

    def test_read_long_with_rest_no_fieldnames(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("f1,f2\r\n1,2,abc,4,5,6\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj, restkey="_rest")
            self.assertEqual(reader.fieldnames, ["f1", "f2"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2',
                                             "_rest": ["abc", "4", "5", "6"]})

    def test_read_short(self):
        mit TemporaryFile("w+", encoding="utf-8") als fileobj:
            fileobj.write("1,2,abc,4,5,6\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames="1 2 3 4 5 6".split(),
                                    restval="DEFAULT")
            self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                             "4": '4', "5": '5', "6": '6'})
            self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                             "4": 'DEFAULT', "5": 'DEFAULT',
                                             "6": 'DEFAULT'})

    def test_read_multi(self):
        sample = [
            '2147483648,43.0e12,17,abc,def\r\n',
            '147483648,43.0e2,17,abc,def\r\n',
            '47483648,43.0,170,abc,def\r\n'
            ]

        reader = csv.DictReader(sample,
                                fieldnames="i1 float i2 s1 s2".split())
        self.assertEqual(next(reader), {"i1": '2147483648',
                                         "float": '43.0e12',
                                         "i2": '17',
                                         "s1": 'abc',
                                         "s2": 'def'})

    def test_read_with_blanks(self):
        reader = csv.DictReader(["1,2,abc,4,5,6\r\n","\r\n",
                                 "1,2,abc,4,5,6\r\n"],
                                fieldnames="1 2 3 4 5 6".split())
        self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                         "4": '4', "5": '5', "6": '6'})
        self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                         "4": '4', "5": '5', "6": '6'})

    def test_read_semi_sep(self):
        reader = csv.DictReader(["1;2;abc;4;5;6\r\n"],
                                fieldnames="1 2 3 4 5 6".split(),
                                delimiter=';')
        self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                         "4": '4', "5": '5', "6": '6'})

klasse TestArrayWrites(unittest.TestCase):
    def test_int_write(self):
        importiere array
        contents = [(20-i) fuer i in range(20)]
        a = array.array('i', contents)

        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, dialect="excel")
            writer.writerow(a)
            expected = ",".join([str(i) fuer i in a])+"\r\n"
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected)

    def test_double_write(self):
        importiere array
        contents = [(20-i)*0.1 fuer i in range(20)]
        a = array.array('d', contents)
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, dialect="excel")
            writer.writerow(a)
            expected = ",".join([str(i) fuer i in a])+"\r\n"
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected)

    def test_float_write(self):
        importiere array
        contents = [(20-i)*0.1 fuer i in range(20)]
        a = array.array('f', contents)
        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, dialect="excel")
            writer.writerow(a)
            expected = ",".join([str(i) fuer i in a])+"\r\n"
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected)

    def test_char_write(self):
        importiere array, string
        a = array.array('w', string.ascii_letters)

        mit TemporaryFile("w+", encoding="utf-8", newline='') als fileobj:
            writer = csv.writer(fileobj, dialect="excel")
            writer.writerow(a)
            expected = ",".join(a)+"\r\n"
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected)

klasse TestDialectValidity(unittest.TestCase):
    def test_quoting(self):
        klasse mydialect(csv.Dialect):
            delimiter = ";"
            escapechar = '\\'
            doublequote = Falsch
            skipinitialspace = Wahr
            lineterminator = '\r\n'
            quoting = csv.QUOTE_NONE
        d = mydialect()
        self.assertEqual(d.quoting, csv.QUOTE_NONE)

        mydialect.quoting = Nichts
        self.assertRaises(csv.Error, mydialect)

        mydialect.quoting = 42
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         'bad "quoting" value')

        mydialect.doublequote = Wahr
        mydialect.quoting = csv.QUOTE_ALL
        mydialect.quotechar = '"'
        d = mydialect()
        self.assertEqual(d.quoting, csv.QUOTE_ALL)
        self.assertEqual(d.quotechar, '"')
        self.assertWahr(d.doublequote)

        mydialect.quotechar = ""
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"quotechar" must be a unicode character oder Nichts, '
                         'not a string of length 0')

        mydialect.quotechar = "''"
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"quotechar" must be a unicode character oder Nichts, '
                         'not a string of length 2')

        mydialect.quotechar = 4
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"quotechar" must be a unicode character oder Nichts, '
                         'not int')

    def test_delimiter(self):
        klasse mydialect(csv.Dialect):
            delimiter = ";"
            escapechar = '\\'
            doublequote = Falsch
            skipinitialspace = Wahr
            lineterminator = '\r\n'
            quoting = csv.QUOTE_NONE
        d = mydialect()
        self.assertEqual(d.delimiter, ";")

        mydialect.delimiter = ":::"
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"delimiter" must be a unicode character, '
                         'not a string of length 3')

        mydialect.delimiter = ""
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"delimiter" must be a unicode character, nicht a string of length 0')

        mydialect.delimiter = b","
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"delimiter" must be a unicode character, nicht bytes')

        mydialect.delimiter = 4
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"delimiter" must be a unicode character, nicht int')

        mydialect.delimiter = Nichts
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"delimiter" must be a unicode character, nicht NoneType')

    def test_escapechar(self):
        klasse mydialect(csv.Dialect):
            delimiter = ";"
            escapechar = '\\'
            doublequote = Falsch
            skipinitialspace = Wahr
            lineterminator = '\r\n'
            quoting = csv.QUOTE_NONE
        d = mydialect()
        self.assertEqual(d.escapechar, "\\")

        mydialect.escapechar = ""
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"escapechar" must be a unicode character oder Nichts, '
                         'not a string of length 0')

        mydialect.escapechar = "**"
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"escapechar" must be a unicode character oder Nichts, '
                         'not a string of length 2')

        mydialect.escapechar = b"*"
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"escapechar" must be a unicode character oder Nichts, '
                         'not bytes')

        mydialect.escapechar = 4
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"escapechar" must be a unicode character oder Nichts, '
                         'not int')

    def test_lineterminator(self):
        klasse mydialect(csv.Dialect):
            delimiter = ";"
            escapechar = '\\'
            doublequote = Falsch
            skipinitialspace = Wahr
            lineterminator = '\r\n'
            quoting = csv.QUOTE_NONE
        d = mydialect()
        self.assertEqual(d.lineterminator, '\r\n')

        mydialect.lineterminator = ":::"
        d = mydialect()
        self.assertEqual(d.lineterminator, ":::")

        mydialect.lineterminator = 4
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"lineterminator" must be a string, nicht int')

        mydialect.lineterminator = Nichts
        mit self.assertRaises(csv.Error) als cm:
            mydialect()
        self.assertEqual(str(cm.exception),
                         '"lineterminator" must be a string, nicht NoneType')

    def test_invalid_chars(self):
        def create_invalid(field_name, value, **kwargs):
            klasse mydialect(csv.Dialect):
                delimiter = ','
                quoting = csv.QUOTE_ALL
                quotechar = '"'
                lineterminator = '\r\n'
            setattr(mydialect, field_name, value)
            fuer field_name, value in kwargs.items():
                setattr(mydialect, field_name, value)
            d = mydialect()

        fuer field_name in ("delimiter", "escapechar", "quotechar"):
            mit self.subTest(field_name=field_name):
                self.assertRaises(csv.Error, create_invalid, field_name, "")
                self.assertRaises(csv.Error, create_invalid, field_name, "abc")
                self.assertRaises(csv.Error, create_invalid, field_name, b'x')
                self.assertRaises(csv.Error, create_invalid, field_name, 5)
                self.assertRaises(ValueError, create_invalid, field_name, "\n")
                self.assertRaises(ValueError, create_invalid, field_name, "\r")
                wenn field_name != "delimiter":
                    self.assertRaises(ValueError, create_invalid, field_name, " ",
                                      skipinitialspace=Wahr)


klasse TestSniffer(unittest.TestCase):
    sample1 = """\
Harry's, Arlington Heights, IL, 2/1/03, Kimi Hayes
Shark City, Glendale Heights, IL, 12/28/02, Prezence
Tommy's Place, Blue Island, IL, 12/28/02, Blue Sunday/White Crow
Stonecutters Seafood und Chop House, Lemont, IL, 12/19/02, Week Back
"""
    sample2 = """\
'Harry''s':'Arlington Heights':'IL':'2/1/03':'Kimi Hayes'
'Shark City':'Glendale Heights':'IL':'12/28/02':'Prezence'
'Tommy''s Place':'Blue Island':'IL':'12/28/02':'Blue Sunday/White Crow'
'Stonecutters ''Seafood'' und Chop House':'Lemont':'IL':'12/19/02':'Week Back'
"""
    header1 = '''\
"venue","city","state","date","performers"
'''
    sample3 = '''\
05/05/03?05/05/03?05/05/03?05/05/03?05/05/03?05/05/03
05/05/03?05/05/03?05/05/03?05/05/03?05/05/03?05/05/03
05/05/03?05/05/03?05/05/03?05/05/03?05/05/03?05/05/03
'''

    sample4 = '''\
2147483648;43.0e12;17;abc;def
147483648;43.0e2;17;abc;def
47483648;43.0;170;abc;def
'''

    sample5 = "aaa\tbbb\r\nAAA\t\r\nBBB\t\r\n"
    sample6 = "a|b|c\r\nd|e|f\r\n"
    sample7 = "'a'|'b'|'c'\r\n'd'|e|f\r\n"

# Issue 18155: Use a delimiter that is a special char to regex:

    header2 = '''\
"venue"+"city"+"state"+"date"+"performers"
'''
    sample8 = """\
Harry's+ Arlington Heights+ IL+ 2/1/03+ Kimi Hayes
Shark City+ Glendale Heights+ IL+ 12/28/02+ Prezence
Tommy's Place+ Blue Island+ IL+ 12/28/02+ Blue Sunday/White Crow
Stonecutters Seafood und Chop House+ Lemont+ IL+ 12/19/02+ Week Back
"""
    sample9 = """\
'Harry''s'+ Arlington Heights'+ 'IL'+ '2/1/03'+ 'Kimi Hayes'
'Shark City'+ Glendale Heights'+' IL'+ '12/28/02'+ 'Prezence'
'Tommy''s Place'+ Blue Island'+ 'IL'+ '12/28/02'+ 'Blue Sunday/White Crow'
'Stonecutters ''Seafood'' und Chop House'+ 'Lemont'+ 'IL'+ '12/19/02'+ 'Week Back'
"""

    sample10 = dedent("""
                        abc,def
                        ghijkl,mno
                        ghi,jkl
                        """)

    sample11 = dedent("""
                        abc,def
                        ghijkl,mnop
                        ghi,jkl
                         """)

    sample12 = dedent(""""time","forces"
                        1,1.5
                        0.5,5+0j
                        0,0
                        1+1j,6
                        """)

    sample13 = dedent(""""time","forces"
                        0,0
                        1,2
                        a,b
                        """)

    sample14 = """\
abc\0def
ghijkl\0mno
ghi\0jkl
"""

    def test_issue43625(self):
        sniffer = csv.Sniffer()
        self.assertWahr(sniffer.has_header(self.sample12))
        self.assertFalsch(sniffer.has_header(self.sample13))

    def test_has_header_strings(self):
        "More to document existing (unexpected?) behavior than anything else."
        sniffer = csv.Sniffer()
        self.assertFalsch(sniffer.has_header(self.sample10))
        self.assertFalsch(sniffer.has_header(self.sample11))

    def test_has_header(self):
        sniffer = csv.Sniffer()
        self.assertIs(sniffer.has_header(self.sample1), Falsch)
        self.assertIs(sniffer.has_header(self.header1 + self.sample1), Wahr)

    def test_has_header_regex_special_delimiter(self):
        sniffer = csv.Sniffer()
        self.assertIs(sniffer.has_header(self.sample8), Falsch)
        self.assertIs(sniffer.has_header(self.header2 + self.sample8), Wahr)

    def test_guess_quote_and_delimiter(self):
        sniffer = csv.Sniffer()
        fuer header in (";'123;4';", "'123;4';", ";'123;4'", "'123;4'"):
            mit self.subTest(header):
                dialect = sniffer.sniff(header, ",;")
                self.assertEqual(dialect.delimiter, ';')
                self.assertEqual(dialect.quotechar, "'")
                self.assertIs(dialect.doublequote, Falsch)
                self.assertIs(dialect.skipinitialspace, Falsch)

    def test_sniff(self):
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(self.sample1)
        self.assertEqual(dialect.delimiter, ",")
        self.assertEqual(dialect.quotechar, '"')
        self.assertIs(dialect.skipinitialspace, Wahr)

        dialect = sniffer.sniff(self.sample2)
        self.assertEqual(dialect.delimiter, ":")
        self.assertEqual(dialect.quotechar, "'")
        self.assertIs(dialect.skipinitialspace, Falsch)

    def test_delimiters(self):
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(self.sample3)
        # given that all three lines in sample3 are equal,
        # I think that any character could have been 'guessed' als the
        # delimiter, depending on dictionary order
        self.assertIn(dialect.delimiter, self.sample3)
        dialect = sniffer.sniff(self.sample3, delimiters="?,")
        self.assertEqual(dialect.delimiter, "?")
        dialect = sniffer.sniff(self.sample3, delimiters="/,")
        self.assertEqual(dialect.delimiter, "/")
        dialect = sniffer.sniff(self.sample4)
        self.assertEqual(dialect.delimiter, ";")
        dialect = sniffer.sniff(self.sample5)
        self.assertEqual(dialect.delimiter, "\t")
        dialect = sniffer.sniff(self.sample6)
        self.assertEqual(dialect.delimiter, "|")
        dialect = sniffer.sniff(self.sample7)
        self.assertEqual(dialect.delimiter, "|")
        self.assertEqual(dialect.quotechar, "'")
        dialect = sniffer.sniff(self.sample8)
        self.assertEqual(dialect.delimiter, '+')
        dialect = sniffer.sniff(self.sample9)
        self.assertEqual(dialect.delimiter, '+')
        self.assertEqual(dialect.quotechar, "'")
        dialect = sniffer.sniff(self.sample14)
        self.assertEqual(dialect.delimiter, '\0')

    def test_doublequote(self):
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(self.header1)
        self.assertFalsch(dialect.doublequote)
        dialect = sniffer.sniff(self.header2)
        self.assertFalsch(dialect.doublequote)
        dialect = sniffer.sniff(self.sample2)
        self.assertWahr(dialect.doublequote)
        dialect = sniffer.sniff(self.sample8)
        self.assertFalsch(dialect.doublequote)
        dialect = sniffer.sniff(self.sample9)
        self.assertWahr(dialect.doublequote)

klasse NUL:
    def write(s, *args):
        pass
    writelines = write

@unittest.skipUnless(hasattr(sys, "gettotalrefcount"),
                     'requires sys.gettotalrefcount()')
klasse TestLeaks(unittest.TestCase):
    def test_create_read(self):
        delta = 0
        lastrc = sys.gettotalrefcount()
        fuer i in range(20):
            gc.collect()
            self.assertEqual(gc.garbage, [])
            rc = sys.gettotalrefcount()
            csv.reader(["a,b,c\r\n"])
            csv.reader(["a,b,c\r\n"])
            csv.reader(["a,b,c\r\n"])
            delta = rc-lastrc
            lastrc = rc
        # wenn csv.reader() leaks, last delta should be 3 oder more
        self.assertLess(delta, 3)

    def test_create_write(self):
        delta = 0
        lastrc = sys.gettotalrefcount()
        s = NUL()
        fuer i in range(20):
            gc.collect()
            self.assertEqual(gc.garbage, [])
            rc = sys.gettotalrefcount()
            csv.writer(s)
            csv.writer(s)
            csv.writer(s)
            delta = rc-lastrc
            lastrc = rc
        # wenn csv.writer() leaks, last delta should be 3 oder more
        self.assertLess(delta, 3)

    def test_read(self):
        delta = 0
        rows = ["a,b,c\r\n"]*5
        lastrc = sys.gettotalrefcount()
        fuer i in range(20):
            gc.collect()
            self.assertEqual(gc.garbage, [])
            rc = sys.gettotalrefcount()
            rdr = csv.reader(rows)
            fuer row in rdr:
                pass
            delta = rc-lastrc
            lastrc = rc
        # wenn reader leaks during read, delta should be 5 oder more
        self.assertLess(delta, 5)

    def test_write(self):
        delta = 0
        rows = [[1,2,3]]*5
        s = NUL()
        lastrc = sys.gettotalrefcount()
        fuer i in range(20):
            gc.collect()
            self.assertEqual(gc.garbage, [])
            rc = sys.gettotalrefcount()
            writer = csv.writer(s)
            fuer row in rows:
                writer.writerow(row)
            delta = rc-lastrc
            lastrc = rc
        # wenn writer leaks during write, last delta should be 5 oder more
        self.assertLess(delta, 5)

klasse TestUnicode(unittest.TestCase):

    names = ["Martin von Löwis",
             "Marc André Lemburg",
             "Guido van Rossum",
             "François Pinard"]

    def test_unicode_read(self):
        mit TemporaryFile("w+", newline='', encoding="utf-8") als fileobj:
            fileobj.write(",".join(self.names) + "\r\n")
            fileobj.seek(0)
            reader = csv.reader(fileobj)
            self.assertEqual(list(reader), [self.names])


    def test_unicode_write(self):
        mit TemporaryFile("w+", newline='', encoding="utf-8") als fileobj:
            writer = csv.writer(fileobj)
            writer.writerow(self.names)
            expected = ",".join(self.names)+"\r\n"
            fileobj.seek(0)
            self.assertEqual(fileobj.read(), expected)

klasse KeyOrderingTest(unittest.TestCase):

    def test_ordering_for_the_dict_reader_and_writer(self):
        resultset = set()
        fuer keys in permutations("abcde"):
            mit TemporaryFile('w+', newline='', encoding="utf-8") als fileobject:
                dw = csv.DictWriter(fileobject, keys)
                dw.writeheader()
                fileobject.seek(0)
                dr = csv.DictReader(fileobject)
                kt = tuple(dr.fieldnames)
                self.assertEqual(keys, kt)
                resultset.add(kt)
        # Final sanity check: were all permutations unique?
        self.assertEqual(len(resultset), 120, "Key ordering: some key permutations nicht collected (expected 120)")

    def test_ordered_dict_reader(self):
        data = dedent('''\
            FirstName,LastName
            Eric,Idle
            Graham,Chapman,Over1,Over2

            Under1
            John,Cleese
        ''').splitlines()

        self.assertEqual(list(csv.DictReader(data)),
            [OrderedDict([('FirstName', 'Eric'), ('LastName', 'Idle')]),
             OrderedDict([('FirstName', 'Graham'), ('LastName', 'Chapman'),
                          (Nichts, ['Over1', 'Over2'])]),
             OrderedDict([('FirstName', 'Under1'), ('LastName', Nichts)]),
             OrderedDict([('FirstName', 'John'), ('LastName', 'Cleese')]),
            ])

        self.assertEqual(list(csv.DictReader(data, restkey='OtherInfo')),
            [OrderedDict([('FirstName', 'Eric'), ('LastName', 'Idle')]),
             OrderedDict([('FirstName', 'Graham'), ('LastName', 'Chapman'),
                          ('OtherInfo', ['Over1', 'Over2'])]),
             OrderedDict([('FirstName', 'Under1'), ('LastName', Nichts)]),
             OrderedDict([('FirstName', 'John'), ('LastName', 'Cleese')]),
            ])

        del data[0]            # Remove the header row
        self.assertEqual(list(csv.DictReader(data, fieldnames=['fname', 'lname'])),
            [OrderedDict([('fname', 'Eric'), ('lname', 'Idle')]),
             OrderedDict([('fname', 'Graham'), ('lname', 'Chapman'),
                          (Nichts, ['Over1', 'Over2'])]),
             OrderedDict([('fname', 'Under1'), ('lname', Nichts)]),
             OrderedDict([('fname', 'John'), ('lname', 'Cleese')]),
            ])


klasse MiscTestCase(unittest.TestCase):
    def test__all__(self):
        support.check__all__(self, csv, ('csv', '_csv'))

    @cpython_only
    def test_lazy_import(self):
        ensure_lazy_imports("csv", {"re"})

    def test_subclassable(self):
        # issue 44089
        klasse Foo(csv.Error): ...

    @support.cpython_only
    def test_disallow_instantiation(self):
        _csv = import_helper.import_module("_csv")
        fuer tp in _csv.Reader, _csv.Writer:
            mit self.subTest(tp=tp):
                check_disallow_instantiation(self, tp)

wenn __name__ == '__main__':
    unittest.main()
