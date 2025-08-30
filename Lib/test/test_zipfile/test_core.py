importiere _pyio
importiere array
importiere contextlib
importiere importlib.util
importiere io
importiere itertools
importiere os
importiere posixpath
importiere stat
importiere struct
importiere subprocess
importiere sys
importiere time
importiere unittest
importiere unittest.mock als mock
importiere zipfile


von tempfile importiere TemporaryFile
von random importiere randint, random, randbytes

von test importiere archiver_tests
von test.support importiere script_helper, os_helper
von test.support importiere (
    findfile, requires_zlib, requires_bz2, requires_lzma,
    requires_zstd, captured_stdout, captured_stderr, requires_subprocess,
    cpython_only
)
von test.support.os_helper importiere (
    TESTFN, unlink, rmtree, temp_dir, temp_cwd, fd_count, FakePath
)
von test.support.import_helper importiere ensure_lazy_imports


TESTFN2 = TESTFN + "2"
TESTFNDIR = TESTFN + "d"
FIXEDTEST_SIZE = 1000
DATAFILES_DIR = 'zipfile_datafiles'

SMALL_TEST_DATA = [('_ziptest1', '1q2w3e4r5t'),
                   ('ziptest2dir/_ziptest2', 'qawsedrftg'),
                   ('ziptest2dir/ziptest3dir/_ziptest3', 'azsxdcfvgb'),
                   ('ziptest2dir/ziptest3dir/ziptest4dir/_ziptest3', '6y7u8i9o0p')]

def get_files(test):
    liefere TESTFN2
    mit TemporaryFile() als f:
        liefere f
        test.assertFalsch(f.closed)
    mit io.BytesIO() als f:
        liefere f
        test.assertFalsch(f.closed)


klasse LazyImportTest(unittest.TestCase):
    @cpython_only
    def test_lazy_import(self):
        ensure_lazy_imports("zipfile", {"typing"})


klasse AbstractTestsWithSourceFile:
    @classmethod
    def setUpClass(cls):
        cls.line_gen = [bytes("Zipfile test line %d. random float: %f\n" %
                              (i, random()), "ascii")
                        fuer i in range(FIXEDTEST_SIZE)]
        cls.data = b''.join(cls.line_gen)

    def setUp(self):
        # Make a source file mit some lines
        mit open(TESTFN, "wb") als fp:
            fp.write(self.data)

    def make_test_archive(self, f, compression, compresslevel=Nichts):
        kwargs = {'compression': compression, 'compresslevel': compresslevel}
        # Create the ZIP archive
        mit zipfile.ZipFile(f, "w", **kwargs) als zipfp:
            zipfp.write(TESTFN, "another.name")
            zipfp.write(TESTFN, TESTFN)
            zipfp.writestr("strfile", self.data)
            mit zipfp.open('written-open-w', mode='w') als f:
                fuer line in self.line_gen:
                    f.write(line)

    def zip_test(self, f, compression, compresslevel=Nichts):
        self.make_test_archive(f, compression, compresslevel)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            self.assertEqual(zipfp.read(TESTFN), self.data)
            self.assertEqual(zipfp.read("another.name"), self.data)
            self.assertEqual(zipfp.read("strfile"), self.data)

            # Print the ZIP directory
            fp = io.StringIO()
            zipfp.printdir(file=fp)
            directory = fp.getvalue()
            lines = directory.splitlines()
            self.assertEqual(len(lines), 5) # Number of files + header

            self.assertIn('File Name', lines[0])
            self.assertIn('Modified', lines[0])
            self.assertIn('Size', lines[0])

            fn, date, time_, size = lines[1].split()
            self.assertEqual(fn, 'another.name')
            self.assertWahr(time.strptime(date, '%Y-%m-%d'))
            self.assertWahr(time.strptime(time_, '%H:%M:%S'))
            self.assertEqual(size, str(len(self.data)))

            # Check the namelist
            names = zipfp.namelist()
            self.assertEqual(len(names), 4)
            self.assertIn(TESTFN, names)
            self.assertIn("another.name", names)
            self.assertIn("strfile", names)
            self.assertIn("written-open-w", names)

            # Check infolist
            infos = zipfp.infolist()
            names = [i.filename fuer i in infos]
            self.assertEqual(len(names), 4)
            self.assertIn(TESTFN, names)
            self.assertIn("another.name", names)
            self.assertIn("strfile", names)
            self.assertIn("written-open-w", names)
            fuer i in infos:
                self.assertEqual(i.file_size, len(self.data))

            # check getinfo
            fuer nm in (TESTFN, "another.name", "strfile", "written-open-w"):
                info = zipfp.getinfo(nm)
                self.assertEqual(info.filename, nm)
                self.assertEqual(info.file_size, len(self.data))

            # Check that testzip thinks the archive is ok
            # (it returns Nichts wenn all contents could be read properly)
            self.assertIsNichts(zipfp.testzip())

    def test_basic(self):
        fuer f in get_files(self):
            self.zip_test(f, self.compression)

    def zip_open_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            zipdata1 = []
            mit zipfp.open(TESTFN) als zipopen1:
                waehrend Wahr:
                    read_data = zipopen1.read(256)
                    wenn nicht read_data:
                        breche
                    zipdata1.append(read_data)

            zipdata2 = []
            mit zipfp.open("another.name") als zipopen2:
                waehrend Wahr:
                    read_data = zipopen2.read(256)
                    wenn nicht read_data:
                        breche
                    zipdata2.append(read_data)

            self.assertEqual(b''.join(zipdata1), self.data)
            self.assertEqual(b''.join(zipdata2), self.data)

    def test_open(self):
        fuer f in get_files(self):
            self.zip_open_test(f, self.compression)

    def test_open_with_pathlike(self):
        path = FakePath(TESTFN2)
        self.zip_open_test(path, self.compression)
        mit zipfile.ZipFile(path, "r", self.compression) als zipfp:
            self.assertIsInstance(zipfp.filename, str)

    def zip_random_open_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            zipdata1 = []
            mit zipfp.open(TESTFN) als zipopen1:
                waehrend Wahr:
                    read_data = zipopen1.read(randint(1, 1024))
                    wenn nicht read_data:
                        breche
                    zipdata1.append(read_data)

            self.assertEqual(b''.join(zipdata1), self.data)

    def test_random_open(self):
        fuer f in get_files(self):
            self.zip_random_open_test(f, self.compression)

    def zip_read1_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r") als zipfp, \
             zipfp.open(TESTFN) als zipopen:
            zipdata = []
            waehrend Wahr:
                read_data = zipopen.read1(-1)
                wenn nicht read_data:
                    breche
                zipdata.append(read_data)

        self.assertEqual(b''.join(zipdata), self.data)

    def test_read1(self):
        fuer f in get_files(self):
            self.zip_read1_test(f, self.compression)

    def zip_read1_10_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r") als zipfp, \
             zipfp.open(TESTFN) als zipopen:
            zipdata = []
            waehrend Wahr:
                read_data = zipopen.read1(10)
                self.assertLessEqual(len(read_data), 10)
                wenn nicht read_data:
                    breche
                zipdata.append(read_data)

        self.assertEqual(b''.join(zipdata), self.data)

    def test_read1_10(self):
        fuer f in get_files(self):
            self.zip_read1_10_test(f, self.compression)

    def zip_readline_read_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r") als zipfp, \
             zipfp.open(TESTFN) als zipopen:
            data = b''
            waehrend Wahr:
                read = zipopen.readline()
                wenn nicht read:
                    breche
                data += read

                read = zipopen.read(100)
                wenn nicht read:
                    breche
                data += read

        self.assertEqual(data, self.data)

    def test_readline_read(self):
        # Issue #7610: calls to readline() interleaved mit calls to read().
        fuer f in get_files(self):
            self.zip_readline_read_test(f, self.compression)

    def zip_readline_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r") als zipfp:
            mit zipfp.open(TESTFN) als zipopen:
                fuer line in self.line_gen:
                    linedata = zipopen.readline()
                    self.assertEqual(linedata, line)

    def test_readline(self):
        fuer f in get_files(self):
            self.zip_readline_test(f, self.compression)

    def zip_readlines_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r") als zipfp:
            mit zipfp.open(TESTFN) als zipopen:
                ziplines = zipopen.readlines()
            fuer line, zipline in zip(self.line_gen, ziplines):
                self.assertEqual(zipline, line)

    def test_readlines(self):
        fuer f in get_files(self):
            self.zip_readlines_test(f, self.compression)

    def zip_iterlines_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r") als zipfp:
            mit zipfp.open(TESTFN) als zipopen:
                fuer line, zipline in zip(self.line_gen, zipopen):
                    self.assertEqual(zipline, line)

    def test_iterlines(self):
        fuer f in get_files(self):
            self.zip_iterlines_test(f, self.compression)

    def test_low_compression(self):
        """Check fuer cases where compressed data is larger than original."""
        # Create the ZIP archive
        mit zipfile.ZipFile(TESTFN2, "w", self.compression) als zipfp:
            zipfp.writestr("strfile", '12')

        # Get an open object fuer strfile
        mit zipfile.ZipFile(TESTFN2, "r", self.compression) als zipfp:
            mit zipfp.open("strfile") als openobj:
                self.assertEqual(openobj.read(1), b'1')
                self.assertEqual(openobj.read(1), b'2')

    def test_writestr_compression(self):
        zipfp = zipfile.ZipFile(TESTFN2, "w")
        zipfp.writestr("b.txt", "hello world", compress_type=self.compression)
        info = zipfp.getinfo('b.txt')
        self.assertEqual(info.compress_type, self.compression)

    def test_writestr_compresslevel(self):
        zipfp = zipfile.ZipFile(TESTFN2, "w", compresslevel=1)
        zipfp.writestr("a.txt", "hello world", compress_type=self.compression)
        zipfp.writestr("b.txt", "hello world", compress_type=self.compression,
                       compresslevel=2)

        # Compression level follows the constructor.
        a_info = zipfp.getinfo('a.txt')
        self.assertEqual(a_info.compress_type, self.compression)
        self.assertEqual(a_info.compress_level, 1)

        # Compression level is overridden.
        b_info = zipfp.getinfo('b.txt')
        self.assertEqual(b_info.compress_type, self.compression)
        self.assertEqual(b_info._compresslevel, 2)

    def test_read_return_size(self):
        # Issue #9837: ZipExtFile.read() shouldn't gib more bytes
        # than requested.
        fuer test_size in (1, 4095, 4096, 4097, 16384):
            file_size = test_size + 1
            junk = randbytes(file_size)
            mit zipfile.ZipFile(io.BytesIO(), "w", self.compression) als zipf:
                zipf.writestr('foo', junk)
                mit zipf.open('foo', 'r') als fp:
                    buf = fp.read(test_size)
                    self.assertEqual(len(buf), test_size)

    def test_truncated_zipfile(self):
        fp = io.BytesIO()
        mit zipfile.ZipFile(fp, mode='w') als zipf:
            zipf.writestr('strfile', self.data, compress_type=self.compression)
            end_offset = fp.tell()
        zipfiledata = fp.getvalue()

        fp = io.BytesIO(zipfiledata)
        mit zipfile.ZipFile(fp) als zipf:
            mit zipf.open('strfile') als zipopen:
                fp.truncate(end_offset - 20)
                mit self.assertRaises(EOFError):
                    zipopen.read()

        fp = io.BytesIO(zipfiledata)
        mit zipfile.ZipFile(fp) als zipf:
            mit zipf.open('strfile') als zipopen:
                fp.truncate(end_offset - 20)
                mit self.assertRaises(EOFError):
                    waehrend zipopen.read(100):
                        pass

        fp = io.BytesIO(zipfiledata)
        mit zipfile.ZipFile(fp) als zipf:
            mit zipf.open('strfile') als zipopen:
                fp.truncate(end_offset - 20)
                mit self.assertRaises(EOFError):
                    waehrend zipopen.read1(100):
                        pass

    def test_repr(self):
        fname = 'file.name'
        fuer f in get_files(self):
            mit zipfile.ZipFile(f, 'w', self.compression) als zipfp:
                zipfp.write(TESTFN, fname)
                r = repr(zipfp)
                self.assertIn("mode='w'", r)

            mit zipfile.ZipFile(f, 'r') als zipfp:
                r = repr(zipfp)
                wenn isinstance(f, str):
                    self.assertIn('filename=%r' % f, r)
                sonst:
                    self.assertIn('file=%r' % f, r)
                self.assertIn("mode='r'", r)
                r = repr(zipfp.getinfo(fname))
                self.assertIn('filename=%r' % fname, r)
                self.assertIn('filemode=', r)
                self.assertIn('file_size=', r)
                wenn self.compression != zipfile.ZIP_STORED:
                    self.assertIn('compress_type=', r)
                    self.assertIn('compress_size=', r)
                mit zipfp.open(fname) als zipopen:
                    r = repr(zipopen)
                    self.assertIn('name=%r' % fname, r)
                    wenn self.compression != zipfile.ZIP_STORED:
                        self.assertIn('compress_type=', r)
                self.assertIn('[closed]', repr(zipopen))
            self.assertIn('[closed]', repr(zipfp))

    def test_compresslevel_basic(self):
        fuer f in get_files(self):
            self.zip_test(f, self.compression, compresslevel=9)

    def test_per_file_compresslevel(self):
        """Check that files within a Zip archive can have different
        compression levels."""
        mit zipfile.ZipFile(TESTFN2, "w", compresslevel=1) als zipfp:
            zipfp.write(TESTFN, 'compress_1')
            zipfp.write(TESTFN, 'compress_9', compresslevel=9)
            one_info = zipfp.getinfo('compress_1')
            nine_info = zipfp.getinfo('compress_9')
            self.assertEqual(one_info._compresslevel, 1)
            self.assertEqual(nine_info.compress_level, 9)

    def test_writing_errors(self):
        klasse BrokenFile(io.BytesIO):
            def write(self, data):
                nonlocal count
                wenn count is nicht Nichts:
                    wenn count == stop:
                        wirf OSError
                    count += 1
                super().write(data)

        stop = 0
        waehrend Wahr:
            testfile = BrokenFile()
            count = Nichts
            mit zipfile.ZipFile(testfile, 'w', self.compression) als zipfp:
                mit zipfp.open('file1', 'w') als f:
                    f.write(b'data1')
                count = 0
                versuch:
                    mit zipfp.open('file2', 'w') als f:
                        f.write(b'data2')
                ausser OSError:
                    stop += 1
                sonst:
                    breche
                schliesslich:
                    count = Nichts
            mit zipfile.ZipFile(io.BytesIO(testfile.getvalue())) als zipfp:
                self.assertEqual(zipfp.namelist(), ['file1'])
                self.assertEqual(zipfp.read('file1'), b'data1')

        mit zipfile.ZipFile(io.BytesIO(testfile.getvalue())) als zipfp:
            self.assertEqual(zipfp.namelist(), ['file1', 'file2'])
            self.assertEqual(zipfp.read('file1'), b'data1')
            self.assertEqual(zipfp.read('file2'), b'data2')

    def test_zipextfile_attrs(self):
        fname = "somefile.txt"
        mit zipfile.ZipFile(TESTFN2, mode="w") als zipfp:
            zipfp.writestr(fname, "bogus")

        mit zipfile.ZipFile(TESTFN2, mode="r") als zipfp:
            mit zipfp.open(fname) als fid:
                self.assertEqual(fid.name, fname)
                self.assertRaises(io.UnsupportedOperation, fid.fileno)
                self.assertEqual(fid.mode, 'rb')
                self.assertIs(fid.readable(), Wahr)
                self.assertIs(fid.writable(), Falsch)
                self.assertIs(fid.seekable(), Wahr)
                self.assertIs(fid.closed, Falsch)
            self.assertIs(fid.closed, Wahr)
            self.assertEqual(fid.name, fname)
            self.assertEqual(fid.mode, 'rb')
            self.assertRaises(io.UnsupportedOperation, fid.fileno)
            self.assertRaises(ValueError, fid.readable)
            self.assertIs(fid.writable(), Falsch)
            self.assertRaises(ValueError, fid.seekable)

    def tearDown(self):
        unlink(TESTFN)
        unlink(TESTFN2)


klasse StoredTestsWithSourceFile(AbstractTestsWithSourceFile,
                                unittest.TestCase):
    compression = zipfile.ZIP_STORED
    test_low_compression = Nichts

    def zip_test_writestr_permissions(self, f, compression):
        # Make sure that writestr und open(... mode='w') create files with
        # mode 0600, when they are passed a name rather than a ZipInfo
        # instance.

        self.make_test_archive(f, compression)
        mit zipfile.ZipFile(f, "r") als zipfp:
            zinfo = zipfp.getinfo('strfile')
            self.assertEqual(zinfo.external_attr, 0o600 << 16)

            zinfo2 = zipfp.getinfo('written-open-w')
            self.assertEqual(zinfo2.external_attr, 0o600 << 16)

    def test_writestr_permissions(self):
        fuer f in get_files(self):
            self.zip_test_writestr_permissions(f, zipfile.ZIP_STORED)

    def test_absolute_arcnames(self):
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED) als zipfp:
            zipfp.write(TESTFN, "/absolute")

        mit zipfile.ZipFile(TESTFN2, "r", zipfile.ZIP_STORED) als zipfp:
            self.assertEqual(zipfp.namelist(), ["absolute"])

    def test_append_to_zip_file(self):
        """Test appending to an existing zipfile."""
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED) als zipfp:
            zipfp.write(TESTFN, TESTFN)

        mit zipfile.ZipFile(TESTFN2, "a", zipfile.ZIP_STORED) als zipfp:
            zipfp.writestr("strfile", self.data)
            self.assertEqual(zipfp.namelist(), [TESTFN, "strfile"])

    def test_append_to_non_zip_file(self):
        """Test appending to an existing file that is nicht a zipfile."""
        # NOTE: this test fails wenn len(d) < 22 because of the first
        # line "fpin.seek(-22, 2)" in _EndRecData
        data = b'I am nicht a ZipFile!'*10
        mit open(TESTFN2, 'wb') als f:
            f.write(data)

        mit zipfile.ZipFile(TESTFN2, "a", zipfile.ZIP_STORED) als zipfp:
            zipfp.write(TESTFN, TESTFN)

        mit open(TESTFN2, 'rb') als f:
            f.seek(len(data))
            mit zipfile.ZipFile(f, "r") als zipfp:
                self.assertEqual(zipfp.namelist(), [TESTFN])
                self.assertEqual(zipfp.read(TESTFN), self.data)
        mit open(TESTFN2, 'rb') als f:
            self.assertEqual(f.read(len(data)), data)
            zipfiledata = f.read()
        mit io.BytesIO(zipfiledata) als bio, zipfile.ZipFile(bio) als zipfp:
            self.assertEqual(zipfp.namelist(), [TESTFN])
            self.assertEqual(zipfp.read(TESTFN), self.data)

    def test_read_concatenated_zip_file(self):
        mit io.BytesIO() als bio:
            mit zipfile.ZipFile(bio, 'w', zipfile.ZIP_STORED) als zipfp:
                zipfp.write(TESTFN, TESTFN)
            zipfiledata = bio.getvalue()
        data = b'I am nicht a ZipFile!'*10
        mit open(TESTFN2, 'wb') als f:
            f.write(data)
            f.write(zipfiledata)

        mit zipfile.ZipFile(TESTFN2) als zipfp:
            self.assertEqual(zipfp.namelist(), [TESTFN])
            self.assertEqual(zipfp.read(TESTFN), self.data)

    def test_append_to_concatenated_zip_file(self):
        mit io.BytesIO() als bio:
            mit zipfile.ZipFile(bio, 'w', zipfile.ZIP_STORED) als zipfp:
                zipfp.write(TESTFN, TESTFN)
            zipfiledata = bio.getvalue()
        data = b'I am nicht a ZipFile!'*1000000
        mit open(TESTFN2, 'wb') als f:
            f.write(data)
            f.write(zipfiledata)

        mit zipfile.ZipFile(TESTFN2, 'a') als zipfp:
            self.assertEqual(zipfp.namelist(), [TESTFN])
            zipfp.writestr('strfile', self.data)

        mit open(TESTFN2, 'rb') als f:
            self.assertEqual(f.read(len(data)), data)
            zipfiledata = f.read()
        mit io.BytesIO(zipfiledata) als bio, zipfile.ZipFile(bio) als zipfp:
            self.assertEqual(zipfp.namelist(), [TESTFN, 'strfile'])
            self.assertEqual(zipfp.read(TESTFN), self.data)
            self.assertEqual(zipfp.read('strfile'), self.data)

    def test_ignores_newline_at_end(self):
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED) als zipfp:
            zipfp.write(TESTFN, TESTFN)
        mit open(TESTFN2, 'a', encoding='utf-8') als f:
            f.write("\r\n\00\00\00")
        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            self.assertIsInstance(zipfp, zipfile.ZipFile)

    def test_ignores_stuff_appended_past_comments(self):
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED) als zipfp:
            zipfp.comment = b"this is a comment"
            zipfp.write(TESTFN, TESTFN)
        mit open(TESTFN2, 'a', encoding='utf-8') als f:
            f.write("abcdef\r\n")
        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            self.assertIsInstance(zipfp, zipfile.ZipFile)
            self.assertEqual(zipfp.comment, b"this is a comment")

    def test_write_default_name(self):
        """Check that calling ZipFile.write without arcname specified
        produces the expected result."""
        mit zipfile.ZipFile(TESTFN2, "w") als zipfp:
            zipfp.write(TESTFN)
            mit open(TESTFN, "rb") als f:
                self.assertEqual(zipfp.read(TESTFN), f.read())

    def test_io_on_closed_zipextfile(self):
        fname = "somefile.txt"
        mit zipfile.ZipFile(TESTFN2, mode="w", compression=self.compression) als zipfp:
            zipfp.writestr(fname, "bogus")

        mit zipfile.ZipFile(TESTFN2, mode="r") als zipfp:
            mit zipfp.open(fname) als fid:
                fid.close()
                self.assertIs(fid.closed, Wahr)
                self.assertRaises(ValueError, fid.read)
                self.assertRaises(ValueError, fid.seek, 0)
                self.assertRaises(ValueError, fid.tell)

    def test_write_to_readonly(self):
        """Check that trying to call write() on a readonly ZipFile object
        raises a ValueError."""
        mit zipfile.ZipFile(TESTFN2, mode="w") als zipfp:
            zipfp.writestr("somefile.txt", "bogus")

        mit zipfile.ZipFile(TESTFN2, mode="r") als zipfp:
            self.assertRaises(ValueError, zipfp.write, TESTFN)

        mit zipfile.ZipFile(TESTFN2, mode="r") als zipfp:
            mit self.assertRaises(ValueError):
                zipfp.open(TESTFN, mode='w')

    def test_add_file_before_1980(self):
        # Set atime und mtime to 1970-01-01
        os.utime(TESTFN, (0, 0))
        mit zipfile.ZipFile(TESTFN2, "w") als zipfp:
            self.assertRaises(ValueError, zipfp.write, TESTFN)

        mit zipfile.ZipFile(TESTFN2, "w", strict_timestamps=Falsch) als zipfp:
            zipfp.write(TESTFN)
            zinfo = zipfp.getinfo(TESTFN)
            self.assertEqual(zinfo.date_time, (1980, 1, 1, 0, 0, 0))

    def test_add_file_after_2107(self):
        # Set atime und mtime to 2108-12-30
        ts = 4386268800
        versuch:
            time.localtime(ts)
        ausser OverflowError:
            self.skipTest(f'time.localtime({ts}) raises OverflowError')
        versuch:
            os.utime(TESTFN, (ts, ts))
        ausser OverflowError:
            self.skipTest('Host fs cannot set timestamp to required value.')

        mtime_ns = os.stat(TESTFN).st_mtime_ns
        wenn mtime_ns != (4386268800 * 10**9):
            # XFS filesystem is limited to 32-bit timestamp, but the syscall
            # didn't fail. Moreover, there is a VFS bug which returns
            # a cached timestamp which is different than the value on disk.
            #
            # Test st_mtime_ns rather than st_mtime to avoid rounding issues.
            #
            # https://bugzilla.redhat.com/show_bug.cgi?id=1795576
            # https://bugs.python.org/issue39460#msg360952
            self.skipTest(f"Linux VFS/XFS kernel bug detected: {mtime_ns=}")

        mit zipfile.ZipFile(TESTFN2, "w") als zipfp:
            self.assertRaises(struct.error, zipfp.write, TESTFN)

        mit zipfile.ZipFile(TESTFN2, "w", strict_timestamps=Falsch) als zipfp:
            zipfp.write(TESTFN)
            zinfo = zipfp.getinfo(TESTFN)
            self.assertEqual(zinfo.date_time, (2107, 12, 31, 23, 59, 59))


@requires_zlib()
klasse DeflateTestsWithSourceFile(AbstractTestsWithSourceFile,
                                 unittest.TestCase):
    compression = zipfile.ZIP_DEFLATED

    def test_per_file_compression(self):
        """Check that files within a Zip archive can have different
        compression options."""
        mit zipfile.ZipFile(TESTFN2, "w") als zipfp:
            zipfp.write(TESTFN, 'storeme', zipfile.ZIP_STORED)
            zipfp.write(TESTFN, 'deflateme', zipfile.ZIP_DEFLATED)
            sinfo = zipfp.getinfo('storeme')
            dinfo = zipfp.getinfo('deflateme')
            self.assertEqual(sinfo.compress_type, zipfile.ZIP_STORED)
            self.assertEqual(dinfo.compress_type, zipfile.ZIP_DEFLATED)

@requires_bz2()
klasse Bzip2TestsWithSourceFile(AbstractTestsWithSourceFile,
                               unittest.TestCase):
    compression = zipfile.ZIP_BZIP2

@requires_lzma()
klasse LzmaTestsWithSourceFile(AbstractTestsWithSourceFile,
                              unittest.TestCase):
    compression = zipfile.ZIP_LZMA

@requires_zstd()
klasse ZstdTestsWithSourceFile(AbstractTestsWithSourceFile,
                              unittest.TestCase):
    compression = zipfile.ZIP_ZSTANDARD

klasse AbstractTestZip64InSmallFiles:
    # These tests test the ZIP64 functionality without using large files,
    # see test_zipfile64 fuer proper tests.

    @classmethod
    def setUpClass(cls):
        line_gen = (bytes("Test of zipfile line %d." % i, "ascii")
                    fuer i in range(0, FIXEDTEST_SIZE))
        cls.data = b'\n'.join(line_gen)

    def setUp(self):
        self._limit = zipfile.ZIP64_LIMIT
        self._filecount_limit = zipfile.ZIP_FILECOUNT_LIMIT
        zipfile.ZIP64_LIMIT = 1000
        zipfile.ZIP_FILECOUNT_LIMIT = 9

        # Make a source file mit some lines
        mit open(TESTFN, "wb") als fp:
            fp.write(self.data)

    def zip_test(self, f, compression):
        # Create the ZIP archive
        mit zipfile.ZipFile(f, "w", compression, allowZip64=Wahr) als zipfp:
            zipfp.write(TESTFN, "another.name")
            zipfp.write(TESTFN, TESTFN)
            zipfp.writestr("strfile", self.data)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            self.assertEqual(zipfp.read(TESTFN), self.data)
            self.assertEqual(zipfp.read("another.name"), self.data)
            self.assertEqual(zipfp.read("strfile"), self.data)

            # Print the ZIP directory
            fp = io.StringIO()
            zipfp.printdir(fp)

            directory = fp.getvalue()
            lines = directory.splitlines()
            self.assertEqual(len(lines), 4) # Number of files + header

            self.assertIn('File Name', lines[0])
            self.assertIn('Modified', lines[0])
            self.assertIn('Size', lines[0])

            fn, date, time_, size = lines[1].split()
            self.assertEqual(fn, 'another.name')
            self.assertWahr(time.strptime(date, '%Y-%m-%d'))
            self.assertWahr(time.strptime(time_, '%H:%M:%S'))
            self.assertEqual(size, str(len(self.data)))

            # Check the namelist
            names = zipfp.namelist()
            self.assertEqual(len(names), 3)
            self.assertIn(TESTFN, names)
            self.assertIn("another.name", names)
            self.assertIn("strfile", names)

            # Check infolist
            infos = zipfp.infolist()
            names = [i.filename fuer i in infos]
            self.assertEqual(len(names), 3)
            self.assertIn(TESTFN, names)
            self.assertIn("another.name", names)
            self.assertIn("strfile", names)
            fuer i in infos:
                self.assertEqual(i.file_size, len(self.data))

            # check getinfo
            fuer nm in (TESTFN, "another.name", "strfile"):
                info = zipfp.getinfo(nm)
                self.assertEqual(info.filename, nm)
                self.assertEqual(info.file_size, len(self.data))

            # Check that testzip thinks the archive is valid
            self.assertIsNichts(zipfp.testzip())

    def test_basic(self):
        fuer f in get_files(self):
            self.zip_test(f, self.compression)

    def test_too_many_files(self):
        # This test checks that more than 64k files can be added to an archive,
        # und that the resulting archive can be read properly by ZipFile
        zipf = zipfile.ZipFile(TESTFN, "w", self.compression,
                               allowZip64=Wahr)
        zipf.debug = 100
        numfiles = 15
        fuer i in range(numfiles):
            zipf.writestr("foo%08d" % i, "%d" % (i**3 % 57))
        self.assertEqual(len(zipf.namelist()), numfiles)
        zipf.close()

        zipf2 = zipfile.ZipFile(TESTFN, "r", self.compression)
        self.assertEqual(len(zipf2.namelist()), numfiles)
        fuer i in range(numfiles):
            content = zipf2.read("foo%08d" % i).decode('ascii')
            self.assertEqual(content, "%d" % (i**3 % 57))
        zipf2.close()

    def test_too_many_files_append(self):
        zipf = zipfile.ZipFile(TESTFN, "w", self.compression,
                               allowZip64=Falsch)
        zipf.debug = 100
        numfiles = 9
        fuer i in range(numfiles):
            zipf.writestr("foo%08d" % i, "%d" % (i**3 % 57))
        self.assertEqual(len(zipf.namelist()), numfiles)
        mit self.assertRaises(zipfile.LargeZipFile):
            zipf.writestr("foo%08d" % numfiles, b'')
        self.assertEqual(len(zipf.namelist()), numfiles)
        zipf.close()

        zipf = zipfile.ZipFile(TESTFN, "a", self.compression,
                               allowZip64=Falsch)
        zipf.debug = 100
        self.assertEqual(len(zipf.namelist()), numfiles)
        mit self.assertRaises(zipfile.LargeZipFile):
            zipf.writestr("foo%08d" % numfiles, b'')
        self.assertEqual(len(zipf.namelist()), numfiles)
        zipf.close()

        zipf = zipfile.ZipFile(TESTFN, "a", self.compression,
                               allowZip64=Wahr)
        zipf.debug = 100
        self.assertEqual(len(zipf.namelist()), numfiles)
        numfiles2 = 15
        fuer i in range(numfiles, numfiles2):
            zipf.writestr("foo%08d" % i, "%d" % (i**3 % 57))
        self.assertEqual(len(zipf.namelist()), numfiles2)
        zipf.close()

        zipf2 = zipfile.ZipFile(TESTFN, "r", self.compression)
        self.assertEqual(len(zipf2.namelist()), numfiles2)
        fuer i in range(numfiles2):
            content = zipf2.read("foo%08d" % i).decode('ascii')
            self.assertEqual(content, "%d" % (i**3 % 57))
        zipf2.close()

    def tearDown(self):
        zipfile.ZIP64_LIMIT = self._limit
        zipfile.ZIP_FILECOUNT_LIMIT = self._filecount_limit
        unlink(TESTFN)
        unlink(TESTFN2)


klasse StoredTestZip64InSmallFiles(AbstractTestZip64InSmallFiles,
                                  unittest.TestCase):
    compression = zipfile.ZIP_STORED

    def large_file_exception_test(self, f, compression):
        mit zipfile.ZipFile(f, "w", compression, allowZip64=Falsch) als zipfp:
            self.assertRaises(zipfile.LargeZipFile,
                              zipfp.write, TESTFN, "another.name")

    def large_file_exception_test2(self, f, compression):
        mit zipfile.ZipFile(f, "w", compression, allowZip64=Falsch) als zipfp:
            self.assertRaises(zipfile.LargeZipFile,
                              zipfp.writestr, "another.name", self.data)

    def test_large_file_exception(self):
        fuer f in get_files(self):
            self.large_file_exception_test(f, zipfile.ZIP_STORED)
            self.large_file_exception_test2(f, zipfile.ZIP_STORED)

    def test_absolute_arcnames(self):
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED,
                             allowZip64=Wahr) als zipfp:
            zipfp.write(TESTFN, "/absolute")

        mit zipfile.ZipFile(TESTFN2, "r", zipfile.ZIP_STORED) als zipfp:
            self.assertEqual(zipfp.namelist(), ["absolute"])

    def test_append(self):
        # Test that appending to the Zip64 archive doesn't change
        # extra fields of existing entries.
        mit zipfile.ZipFile(TESTFN2, "w", allowZip64=Wahr) als zipfp:
            zipfp.writestr("strfile", self.data)
        mit zipfile.ZipFile(TESTFN2, "r", allowZip64=Wahr) als zipfp:
            zinfo = zipfp.getinfo("strfile")
            extra = zinfo.extra
        mit zipfile.ZipFile(TESTFN2, "a", allowZip64=Wahr) als zipfp:
            zipfp.writestr("strfile2", self.data)
        mit zipfile.ZipFile(TESTFN2, "r", allowZip64=Wahr) als zipfp:
            zinfo = zipfp.getinfo("strfile")
            self.assertEqual(zinfo.extra, extra)

    def make_zip64_file(
        self, file_size_64_set=Falsch, file_size_extra=Falsch,
        compress_size_64_set=Falsch, compress_size_extra=Falsch,
        header_offset_64_set=Falsch, header_offset_extra=Falsch,
    ):
        """Generate bytes sequence fuer a zip mit (incomplete) zip64 data.

        The actual values (nicht the zip 64 0xffffffff values) stored in the file
        are:
        file_size: 8
        compress_size: 8
        header_offset: 0
        """
        actual_size = 8
        actual_header_offset = 0
        local_zip64_fields = []
        central_zip64_fields = []

        file_size = actual_size
        wenn file_size_64_set:
            file_size = 0xffffffff
            wenn file_size_extra:
                local_zip64_fields.append(actual_size)
                central_zip64_fields.append(actual_size)
        file_size = struct.pack("<L", file_size)

        compress_size = actual_size
        wenn compress_size_64_set:
            compress_size = 0xffffffff
            wenn compress_size_extra:
                local_zip64_fields.append(actual_size)
                central_zip64_fields.append(actual_size)
        compress_size = struct.pack("<L", compress_size)

        header_offset = actual_header_offset
        wenn header_offset_64_set:
            header_offset = 0xffffffff
            wenn header_offset_extra:
                central_zip64_fields.append(actual_header_offset)
        header_offset = struct.pack("<L", header_offset)

        local_extra = struct.pack(
            '<HH' + 'Q'*len(local_zip64_fields),
            0x0001,
            8*len(local_zip64_fields),
            *local_zip64_fields
        )

        central_extra = struct.pack(
            '<HH' + 'Q'*len(central_zip64_fields),
            0x0001,
            8*len(central_zip64_fields),
            *central_zip64_fields
        )

        central_dir_size = struct.pack('<Q', 58 + 8 * len(central_zip64_fields))
        offset_to_central_dir = struct.pack('<Q', 50 + 8 * len(local_zip64_fields))

        local_extra_length = struct.pack("<H", 4 + 8 * len(local_zip64_fields))
        central_extra_length = struct.pack("<H", 4 + 8 * len(central_zip64_fields))

        filename = b"test.txt"
        content = b"test1234"
        filename_length = struct.pack("<H", len(filename))
        zip64_contents = (
            # Local file header
            b"PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00!\x00\x9e%\xf5\xaf"
            + compress_size
            + file_size
            + filename_length
            + local_extra_length
            + filename
            + local_extra
            + content
            # Central directory:
            + b"PK\x01\x02-\x03-\x00\x00\x00\x00\x00\x00\x00!\x00\x9e%\xf5\xaf"
            + compress_size
            + file_size
            + filename_length
            + central_extra_length
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01"
            + header_offset
            + filename
            + central_extra
            # Zip64 end of central directory
            + b"PK\x06\x06,\x00\x00\x00\x00\x00\x00\x00-\x00-"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00"
            + b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
            + central_dir_size
            + offset_to_central_dir
            # Zip64 end of central directory locator
            + b"PK\x06\x07\x00\x00\x00\x00l\x00\x00\x00\x00\x00\x00\x00\x01"
            + b"\x00\x00\x00"
            # end of central directory
            + b"PK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00:\x00\x00\x002\x00"
            + b"\x00\x00\x00\x00"
        )
        gib zip64_contents

    def test_bad_zip64_extra(self):
        """Missing zip64 extra records raises an exception.

        There are 4 fields that the zip64 format handles (the disk number is
        nicht used in this module und so is ignored here). According to the zip
        spec:
              The order of the fields in the zip64 extended
              information record is fixed, but the fields MUST
              only appear wenn the corresponding Local oder Central
              directory record field is set to 0xFFFF oder 0xFFFFFFFF.

        If the zip64 extra content doesn't contain enough entries fuer the
        number of fields marked mit 0xFFFF oder 0xFFFFFFFF, we wirf an error.
        This test mismatches the length of the zip64 extra field und the number
        of fields set to indicate the presence of zip64 data.
        """
        # zip64 file size present, no fields in extra, expecting one, equals
        # missing file size.
        missing_file_size_extra = self.make_zip64_file(
            file_size_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_file_size_extra))
        self.assertIn('file size', str(e.exception).lower())

        # zip64 file size present, zip64 compress size present, one field in
        # extra, expecting two, equals missing compress size.
        missing_compress_size_extra = self.make_zip64_file(
            file_size_64_set=Wahr,
            file_size_extra=Wahr,
            compress_size_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_compress_size_extra))
        self.assertIn('compress size', str(e.exception).lower())

        # zip64 compress size present, no fields in extra, expecting one,
        # equals missing compress size.
        missing_compress_size_extra = self.make_zip64_file(
            compress_size_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_compress_size_extra))
        self.assertIn('compress size', str(e.exception).lower())

        # zip64 file size present, zip64 compress size present, zip64 header
        # offset present, two fields in extra, expecting three, equals missing
        # header offset
        missing_header_offset_extra = self.make_zip64_file(
            file_size_64_set=Wahr,
            file_size_extra=Wahr,
            compress_size_64_set=Wahr,
            compress_size_extra=Wahr,
            header_offset_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_header_offset_extra))
        self.assertIn('header offset', str(e.exception).lower())

        # zip64 compress size present, zip64 header offset present, one field
        # in extra, expecting two, equals missing header offset
        missing_header_offset_extra = self.make_zip64_file(
            file_size_64_set=Falsch,
            compress_size_64_set=Wahr,
            compress_size_extra=Wahr,
            header_offset_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_header_offset_extra))
        self.assertIn('header offset', str(e.exception).lower())

        # zip64 file size present, zip64 header offset present, one field in
        # extra, expecting two, equals missing header offset
        missing_header_offset_extra = self.make_zip64_file(
            file_size_64_set=Wahr,
            file_size_extra=Wahr,
            compress_size_64_set=Falsch,
            header_offset_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_header_offset_extra))
        self.assertIn('header offset', str(e.exception).lower())

        # zip64 header offset present, no fields in extra, expecting one,
        # equals missing header offset
        missing_header_offset_extra = self.make_zip64_file(
            file_size_64_set=Falsch,
            compress_size_64_set=Falsch,
            header_offset_64_set=Wahr,
        )
        mit self.assertRaises(zipfile.BadZipFile) als e:
            zipfile.ZipFile(io.BytesIO(missing_header_offset_extra))
        self.assertIn('header offset', str(e.exception).lower())

    def test_generated_valid_zip64_extra(self):
        # These values are what is set in the make_zip64_file method.
        expected_file_size = 8
        expected_compress_size = 8
        expected_header_offset = 0
        expected_content = b"test1234"

        # Loop through the various valid combinations of zip64 masks
        # present und extra fields present.
        params = (
            {"file_size_64_set": Wahr, "file_size_extra": Wahr},
            {"compress_size_64_set": Wahr, "compress_size_extra": Wahr},
            {"header_offset_64_set": Wahr, "header_offset_extra": Wahr},
        )

        fuer r in range(1, len(params) + 1):
            fuer combo in itertools.combinations(params, r):
                kwargs = {}
                fuer c in combo:
                    kwargs.update(c)
                mit zipfile.ZipFile(io.BytesIO(self.make_zip64_file(**kwargs))) als zf:
                    zinfo = zf.infolist()[0]
                    self.assertEqual(zinfo.file_size, expected_file_size)
                    self.assertEqual(zinfo.compress_size, expected_compress_size)
                    self.assertEqual(zinfo.header_offset, expected_header_offset)
                    self.assertEqual(zf.read(zinfo), expected_content)

    def test_force_zip64(self):
        """Test that forcing zip64 extensions correctly notes this in the zip file"""

        # GH-103861 describes an issue where forcing a small file to use zip64
        # extensions would add a zip64 extra record, but nicht change the data
        # sizes to 0xFFFFFFFF to indicate to the extractor that the zip64
        # record should be read. Additionally, it would nicht set the required
        # version to indicate that zip64 extensions are required to extract it.
        # This test replicates the situation und reads the raw data to specifically ensure:
        #  - The required extract version is always >= ZIP64_VERSION
        #  - The compressed und uncompressed size in the file headers are both
        #     0xFFFFFFFF (ie. point to zip64 record)
        #  - The zip64 record is provided und has the correct sizes in it
        # Other aspects of the zip are checked als well, but verifying the above is the main goal.
        # Because this is hard to verify by parsing the data als a zip, the raw
        # bytes are checked to ensure that they line up mit the zip spec.
        # The spec fuer this can be found at: https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT
        # The relevant sections fuer this test are:
        #  - 4.3.7 fuer local file header
        #  - 4.5.3 fuer zip64 extra field

        data = io.BytesIO()
        mit zipfile.ZipFile(data, mode="w", allowZip64=Wahr) als zf:
            mit zf.open("text.txt", mode="w", force_zip64=Wahr) als zi:
                zi.write(b"_")

        zipdata = data.getvalue()

        # pull out und check zip information
        (
            header, vers, os, flags, comp, csize, usize, fn_len,
            ex_total_len, filename, ex_id, ex_len, ex_usize, ex_csize, cd_sig
        ) = struct.unpack("<4sBBHH8xIIHH8shhQQx4s", zipdata[:63])

        self.assertEqual(header, b"PK\x03\x04")  # local file header
        self.assertGreaterEqual(vers, zipfile.ZIP64_VERSION)  # requires zip64 to extract
        self.assertEqual(os, 0)  # compatible mit MS-DOS
        self.assertEqual(flags, 0)  # no flags
        self.assertEqual(comp, 0)  # compression method = stored
        self.assertEqual(csize, 0xFFFFFFFF)  # sizes are in zip64 extra
        self.assertEqual(usize, 0xFFFFFFFF)
        self.assertEqual(fn_len, 8)  # filename len
        self.assertEqual(ex_total_len, 20)  # size of extra records
        self.assertEqual(ex_id, 1)  # Zip64 extra record
        self.assertEqual(ex_len, 16)  # 16 bytes of data
        self.assertEqual(ex_usize, 1)  # uncompressed size
        self.assertEqual(ex_csize, 1)  # compressed size
        self.assertEqual(cd_sig, b"PK\x01\x02") # ensure the central directory header is next

        z = zipfile.ZipFile(io.BytesIO(zipdata))
        zinfos = z.infolist()
        self.assertEqual(len(zinfos), 1)
        self.assertGreaterEqual(zinfos[0].extract_version, zipfile.ZIP64_VERSION)  # requires zip64 to extract

    def test_unseekable_zip_unknown_filesize(self):
        """Test that creating a zip with/without seeking will wirf a RuntimeError wenn zip64 was required but nicht used"""

        def make_zip(fp):
            mit zipfile.ZipFile(fp, mode="w", allowZip64=Wahr) als zf:
                mit zf.open("text.txt", mode="w", force_zip64=Falsch) als zi:
                    zi.write(b"_" * (zipfile.ZIP64_LIMIT + 1))

        self.assertRaises(RuntimeError, make_zip, io.BytesIO())
        self.assertRaises(RuntimeError, make_zip, Unseekable(io.BytesIO()))

    def test_zip64_required_not_allowed_fail(self):
        """Test that trying to add a large file to a zip that doesn't allow zip64 extensions fails on add"""
        def make_zip(fp):
            mit zipfile.ZipFile(fp, mode="w", allowZip64=Falsch) als zf:
                # pretend zipfile.ZipInfo.from_file was used to get the name und filesize
                info = zipfile.ZipInfo("text.txt")
                info.file_size = zipfile.ZIP64_LIMIT + 1
                zf.open(info, mode="w")

        self.assertRaises(zipfile.LargeZipFile, make_zip, io.BytesIO())
        self.assertRaises(zipfile.LargeZipFile, make_zip, Unseekable(io.BytesIO()))

    def test_unseekable_zip_known_filesize(self):
        """Test that creating a zip without seeking will use zip64 extensions wenn the file size is provided up-front"""

        # This test ensures that the zip will use a zip64 data descriptor (same
        # als a regular data descriptor ausser the sizes are 8 bytes instead of
        # 4) record to communicate the size of a file wenn the zip is being
        # written to an unseekable stream.
        # Because this sort of thing is hard to verify by parsing the data back
        # in als a zip, this test looks at the raw bytes created to ensure that
        # the correct data has been generated.
        # The spec fuer this can be found at: https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT
        # The relevant sections fuer this test are:
        #  - 4.3.7 fuer local file header
        #  - 4.3.9 fuer the data descriptor
        #  - 4.5.3 fuer zip64 extra field

        file_size = zipfile.ZIP64_LIMIT + 1

        def make_zip(fp):
            mit zipfile.ZipFile(fp, mode="w", allowZip64=Wahr) als zf:
                # pretend zipfile.ZipInfo.from_file was used to get the name und filesize
                info = zipfile.ZipInfo("text.txt")
                info.file_size = file_size
                mit zf.open(info, mode="w", force_zip64=Falsch) als zi:
                    zi.write(b"_" * file_size)
            gib fp

        # check seekable file information
        seekable_data = make_zip(io.BytesIO()).getvalue()
        (
            header, vers, os, flags, comp, csize, usize, fn_len,
            ex_total_len, filename, ex_id, ex_len, ex_usize, ex_csize,
            cd_sig
        ) = struct.unpack("<4sBBHH8xIIHH8shhQQ{}x4s".format(file_size), seekable_data[:62 + file_size])

        self.assertEqual(header, b"PK\x03\x04")  # local file header
        self.assertGreaterEqual(vers, zipfile.ZIP64_VERSION)  # requires zip64 to extract
        self.assertEqual(os, 0)  # compatible mit MS-DOS
        self.assertEqual(flags, 0)  # no flags set
        self.assertEqual(comp, 0)  # compression method = stored
        self.assertEqual(csize, 0xFFFFFFFF)  # sizes are in zip64 extra
        self.assertEqual(usize, 0xFFFFFFFF)
        self.assertEqual(fn_len, 8)  # filename len
        self.assertEqual(ex_total_len, 20)  # size of extra records
        self.assertEqual(ex_id, 1)  # Zip64 extra record
        self.assertEqual(ex_len, 16)  # 16 bytes of data
        self.assertEqual(ex_usize, file_size)  # uncompressed size
        self.assertEqual(ex_csize, file_size)  # compressed size
        self.assertEqual(cd_sig, b"PK\x01\x02") # ensure the central directory header is next

        # check unseekable file information
        unseekable_data = make_zip(Unseekable(io.BytesIO())).fp.getvalue()
        (
            header, vers, os, flags, comp, csize, usize, fn_len,
            ex_total_len, filename, ex_id, ex_len, ex_usize, ex_csize,
            dd_header, dd_usize, dd_csize, cd_sig
        ) = struct.unpack("<4sBBHH8xIIHH8shhQQ{}x4s4xQQ4s".format(file_size), unseekable_data[:86 + file_size])

        self.assertEqual(header, b"PK\x03\x04")  # local file header
        self.assertGreaterEqual(vers, zipfile.ZIP64_VERSION)  # requires zip64 to extract
        self.assertEqual(os, 0)  # compatible mit MS-DOS
        self.assertEqual("{:b}".format(flags), "1000")  # streaming flag set
        self.assertEqual(comp, 0)  # compression method = stored
        self.assertEqual(csize, 0xFFFFFFFF)  # sizes are in zip64 extra
        self.assertEqual(usize, 0xFFFFFFFF)
        self.assertEqual(fn_len, 8)  # filename len
        self.assertEqual(ex_total_len, 20)  # size of extra records
        self.assertEqual(ex_id, 1)  # Zip64 extra record
        self.assertEqual(ex_len, 16)  # 16 bytes of data
        self.assertEqual(ex_usize, 0)  # uncompressed size - 0 to defer to data descriptor
        self.assertEqual(ex_csize, 0)  # compressed size - 0 to defer to data descriptor
        self.assertEqual(dd_header, b"PK\07\x08")  # data descriptor
        self.assertEqual(dd_usize, file_size)  # file size (8 bytes because zip64)
        self.assertEqual(dd_csize, file_size)  # compressed size (8 bytes because zip64)
        self.assertEqual(cd_sig, b"PK\x01\x02") # ensure the central directory header is next


@requires_zlib()
klasse DeflateTestZip64InSmallFiles(AbstractTestZip64InSmallFiles,
                                   unittest.TestCase):
    compression = zipfile.ZIP_DEFLATED

@requires_bz2()
klasse Bzip2TestZip64InSmallFiles(AbstractTestZip64InSmallFiles,
                                 unittest.TestCase):
    compression = zipfile.ZIP_BZIP2

@requires_lzma()
klasse LzmaTestZip64InSmallFiles(AbstractTestZip64InSmallFiles,
                                unittest.TestCase):
    compression = zipfile.ZIP_LZMA

@requires_zstd()
klasse ZstdTestZip64InSmallFiles(AbstractTestZip64InSmallFiles,
                                unittest.TestCase):
    compression = zipfile.ZIP_ZSTANDARD

klasse AbstractWriterTests:

    def tearDown(self):
        unlink(TESTFN2)

    def test_close_after_close(self):
        data = b'content'
        mit zipfile.ZipFile(TESTFN2, "w", self.compression) als zipf:
            w = zipf.open('test', 'w')
            w.write(data)
            w.close()
            self.assertWahr(w.closed)
            w.close()
            self.assertWahr(w.closed)
            self.assertEqual(zipf.read('test'), data)

    def test_write_after_close(self):
        data = b'content'
        mit zipfile.ZipFile(TESTFN2, "w", self.compression) als zipf:
            w = zipf.open('test', 'w')
            w.write(data)
            w.close()
            self.assertWahr(w.closed)
            self.assertRaises(ValueError, w.write, b'')
            self.assertEqual(zipf.read('test'), data)

    def test_issue44439(self):
        q = array.array('Q', [1, 2, 3, 4, 5])
        LENGTH = len(q) * q.itemsize
        mit zipfile.ZipFile(io.BytesIO(), 'w', self.compression) als zip:
            mit zip.open('data', 'w') als data:
                self.assertEqual(data.write(q), LENGTH)
            self.assertEqual(zip.getinfo('data').file_size, LENGTH)

    def test_zipwritefile_attrs(self):
        fname = "somefile.txt"
        mit zipfile.ZipFile(TESTFN2, mode="w", compression=self.compression) als zipfp:
            mit zipfp.open(fname, 'w') als fid:
                self.assertEqual(fid.name, fname)
                self.assertRaises(io.UnsupportedOperation, fid.fileno)
                self.assertEqual(fid.mode, 'wb')
                self.assertIs(fid.readable(), Falsch)
                self.assertIs(fid.writable(), Wahr)
                self.assertIs(fid.seekable(), Falsch)
                self.assertIs(fid.closed, Falsch)
            self.assertIs(fid.closed, Wahr)
            self.assertEqual(fid.name, fname)
            self.assertEqual(fid.mode, 'wb')
            self.assertRaises(io.UnsupportedOperation, fid.fileno)
            self.assertIs(fid.readable(), Falsch)
            self.assertIs(fid.writable(), Wahr)
            self.assertIs(fid.seekable(), Falsch)

klasse StoredWriterTests(AbstractWriterTests, unittest.TestCase):
    compression = zipfile.ZIP_STORED

@requires_zlib()
klasse DeflateWriterTests(AbstractWriterTests, unittest.TestCase):
    compression = zipfile.ZIP_DEFLATED

@requires_bz2()
klasse Bzip2WriterTests(AbstractWriterTests, unittest.TestCase):
    compression = zipfile.ZIP_BZIP2

@requires_lzma()
klasse LzmaWriterTests(AbstractWriterTests, unittest.TestCase):
    compression = zipfile.ZIP_LZMA

@requires_zstd()
klasse ZstdWriterTests(AbstractWriterTests, unittest.TestCase):
    compression = zipfile.ZIP_ZSTANDARD

klasse PyZipFileTests(unittest.TestCase):
    def assertCompiledIn(self, name, namelist):
        wenn name + 'o' nicht in namelist:
            self.assertIn(name + 'c', namelist)

    def requiresWriteAccess(self, path):
        # effective_ids unavailable on windows
        wenn nicht os.access(path, os.W_OK,
                         effective_ids=os.access in os.supports_effective_ids):
            self.skipTest('requires write access to the installed location')
        filename = os.path.join(path, 'test_zipfile.try')
        versuch:
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT)
            os.close(fd)
        ausser Exception:
            self.skipTest('requires write access to the installed location')
        unlink(filename)

    def test_write_pyfile(self):
        self.requiresWriteAccess(os.path.dirname(__file__))
        mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
            fn = __file__
            wenn fn.endswith('.pyc'):
                path_split = fn.split(os.sep)
                wenn os.altsep is nicht Nichts:
                    path_split.extend(fn.split(os.altsep))
                wenn '__pycache__' in path_split:
                    fn = importlib.util.source_from_cache(fn)
                sonst:
                    fn = fn[:-1]

            zipfp.writepy(fn)

            bn = os.path.basename(fn)
            self.assertNotIn(bn, zipfp.namelist())
            self.assertCompiledIn(bn, zipfp.namelist())

        mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
            fn = __file__
            wenn fn.endswith('.pyc'):
                fn = fn[:-1]

            zipfp.writepy(fn, "testpackage")

            bn = "%s/%s" % ("testpackage", os.path.basename(fn))
            self.assertNotIn(bn, zipfp.namelist())
            self.assertCompiledIn(bn, zipfp.namelist())

    def test_write_python_package(self):
        importiere email
        packagedir = os.path.dirname(email.__file__)
        self.requiresWriteAccess(packagedir)

        mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
            zipfp.writepy(packagedir)

            # Check fuer a couple of modules at different levels of the
            # hierarchy
            names = zipfp.namelist()
            self.assertCompiledIn('email/__init__.py', names)
            self.assertCompiledIn('email/mime/text.py', names)

    def test_write_filtered_python_package(self):
        importiere test
        packagedir = os.path.dirname(test.__file__)
        self.requiresWriteAccess(packagedir)

        mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:

            # first make sure that the test folder gives error messages
            # (on the badsyntax_... files)
            mit captured_stdout() als reportSIO:
                zipfp.writepy(packagedir)
            reportStr = reportSIO.getvalue()
            self.assertWahr('SyntaxError' in reportStr)

            # then check that the filter works on the whole package
            mit captured_stdout() als reportSIO:
                zipfp.writepy(packagedir, filterfunc=lambda whatever: Falsch)
            reportStr = reportSIO.getvalue()
            self.assertWahr('SyntaxError' nicht in reportStr)

            # then check that the filter works on individual files
            def filter(path):
                gib nicht os.path.basename(path).startswith("bad")
            mit captured_stdout() als reportSIO, self.assertWarns(UserWarning):
                zipfp.writepy(packagedir, filterfunc=filter)
            reportStr = reportSIO.getvalue()
            wenn reportStr:
                drucke(reportStr)
            self.assertWahr('SyntaxError' nicht in reportStr)

    def test_write_with_optimization(self):
        importiere email
        packagedir = os.path.dirname(email.__file__)
        self.requiresWriteAccess(packagedir)
        optlevel = 1 wenn __debug__ sonst 0
        ext = '.pyc'

        mit TemporaryFile() als t, \
             zipfile.PyZipFile(t, "w", optimize=optlevel) als zipfp:
            zipfp.writepy(packagedir)

            names = zipfp.namelist()
            self.assertIn('email/__init__' + ext, names)
            self.assertIn('email/mime/text' + ext, names)

    def test_write_python_directory(self):
        os.mkdir(TESTFN2)
        versuch:
            mit open(os.path.join(TESTFN2, "mod1.py"), "w", encoding='utf-8') als fp:
                fp.write("drucke(42)\n")

            mit open(os.path.join(TESTFN2, "mod2.py"), "w", encoding='utf-8') als fp:
                fp.write("drucke(42 * 42)\n")

            mit open(os.path.join(TESTFN2, "mod2.txt"), "w", encoding='utf-8') als fp:
                fp.write("bla bla bla\n")

            mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
                zipfp.writepy(TESTFN2)

                names = zipfp.namelist()
                self.assertCompiledIn('mod1.py', names)
                self.assertCompiledIn('mod2.py', names)
                self.assertNotIn('mod2.txt', names)

        schliesslich:
            rmtree(TESTFN2)

    def test_write_python_directory_filtered(self):
        os.mkdir(TESTFN2)
        versuch:
            mit open(os.path.join(TESTFN2, "mod1.py"), "w", encoding='utf-8') als fp:
                fp.write("drucke(42)\n")

            mit open(os.path.join(TESTFN2, "mod2.py"), "w", encoding='utf-8') als fp:
                fp.write("drucke(42 * 42)\n")

            mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
                zipfp.writepy(TESTFN2, filterfunc=lambda fn:
                                                  nicht fn.endswith('mod2.py'))

                names = zipfp.namelist()
                self.assertCompiledIn('mod1.py', names)
                self.assertNotIn('mod2.py', names)

        schliesslich:
            rmtree(TESTFN2)

    def test_write_non_pyfile(self):
        mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
            mit open(TESTFN, 'w', encoding='utf-8') als f:
                f.write('most definitely nicht a python file')
            self.assertRaises(RuntimeError, zipfp.writepy, TESTFN)
            unlink(TESTFN)

    def test_write_pyfile_bad_syntax(self):
        os.mkdir(TESTFN2)
        versuch:
            mit open(os.path.join(TESTFN2, "mod1.py"), "w", encoding='utf-8') als fp:
                fp.write("Bad syntax in python file\n")

            mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
                # syntax errors are printed to stdout
                mit captured_stdout() als s:
                    zipfp.writepy(os.path.join(TESTFN2, "mod1.py"))

                self.assertIn("SyntaxError", s.getvalue())

                # als it will nicht have compiled the python file, it will
                # include the .py file nicht .pyc
                names = zipfp.namelist()
                self.assertIn('mod1.py', names)
                self.assertNotIn('mod1.pyc', names)

        schliesslich:
            rmtree(TESTFN2)

    def test_write_pathlike(self):
        os.mkdir(TESTFN2)
        versuch:
            mit open(os.path.join(TESTFN2, "mod1.py"), "w", encoding='utf-8') als fp:
                fp.write("drucke(42)\n")

            mit TemporaryFile() als t, zipfile.PyZipFile(t, "w") als zipfp:
                zipfp.writepy(FakePath(os.path.join(TESTFN2, "mod1.py")))
                names = zipfp.namelist()
                self.assertCompiledIn('mod1.py', names)
        schliesslich:
            rmtree(TESTFN2)


klasse ExtractTests(unittest.TestCase):

    def make_test_file(self):
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED) als zipfp:
            fuer fpath, fdata in SMALL_TEST_DATA:
                zipfp.writestr(fpath, fdata)

    def test_extract(self):
        mit temp_cwd():
            self.make_test_file()
            mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
                fuer fpath, fdata in SMALL_TEST_DATA:
                    writtenfile = zipfp.extract(fpath)

                    # make sure it was written to the right place
                    correctfile = os.path.join(os.getcwd(), fpath)
                    correctfile = os.path.normpath(correctfile)

                    self.assertEqual(writtenfile, correctfile)

                    # make sure correct data is in correct file
                    mit open(writtenfile, "rb") als f:
                        self.assertEqual(fdata.encode(), f.read())

                    unlink(writtenfile)

    def _test_extract_with_target(self, target):
        self.make_test_file()
        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            fuer fpath, fdata in SMALL_TEST_DATA:
                writtenfile = zipfp.extract(fpath, target)

                # make sure it was written to the right place
                correctfile = os.path.join(target, fpath)
                correctfile = os.path.normpath(correctfile)
                self.assertWahr(os.path.samefile(writtenfile, correctfile), (writtenfile, target))

                # make sure correct data is in correct file
                mit open(writtenfile, "rb") als f:
                    self.assertEqual(fdata.encode(), f.read())

                unlink(writtenfile)

        unlink(TESTFN2)

    def test_extract_with_target(self):
        mit temp_dir() als extdir:
            self._test_extract_with_target(extdir)

    def test_extract_with_target_pathlike(self):
        mit temp_dir() als extdir:
            self._test_extract_with_target(FakePath(extdir))

    def test_extract_all(self):
        mit temp_cwd():
            self.make_test_file()
            mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
                zipfp.extractall()
                fuer fpath, fdata in SMALL_TEST_DATA:
                    outfile = os.path.join(os.getcwd(), fpath)

                    mit open(outfile, "rb") als f:
                        self.assertEqual(fdata.encode(), f.read())

                    unlink(outfile)

    def _test_extract_all_with_target(self, target):
        self.make_test_file()
        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            zipfp.extractall(target)
            fuer fpath, fdata in SMALL_TEST_DATA:
                outfile = os.path.join(target, fpath)

                mit open(outfile, "rb") als f:
                    self.assertEqual(fdata.encode(), f.read())

                unlink(outfile)

        unlink(TESTFN2)

    def test_extract_all_with_target(self):
        mit temp_dir() als extdir:
            self._test_extract_all_with_target(extdir)

    def test_extract_all_with_target_pathlike(self):
        mit temp_dir() als extdir:
            self._test_extract_all_with_target(FakePath(extdir))

    def check_file(self, filename, content):
        self.assertWahr(os.path.isfile(filename))
        mit open(filename, 'rb') als f:
            self.assertEqual(f.read(), content)

    def test_sanitize_windows_name(self):
        san = zipfile.ZipFile._sanitize_windows_name
        # Passing pathsep in allows this test to work regardless of platform.
        self.assertEqual(san(r',,?,C:,foo,bar/z', ','), r'_,C_,foo,bar/z')
        self.assertEqual(san(r'a\b,c<d>e|f"g?h*i', ','), r'a\b,c_d_e_f_g_h_i')
        self.assertEqual(san('../../foo../../ba..r', '/'), r'foo/ba..r')
        self.assertEqual(san('  /  /foo  /  /ba  r', '/'), r'foo/ba  r')
        self.assertEqual(san(' . /. /foo ./ . /. ./ba .r', '/'), r'foo/ba .r')

    def test_extract_hackers_arcnames_common_cases(self):
        common_hacknames = [
            ('../foo/bar', 'foo/bar'),
            ('foo/../bar', 'foo/bar'),
            ('foo/../../bar', 'foo/bar'),
            ('foo/bar/..', 'foo/bar'),
            ('./../foo/bar', 'foo/bar'),
            ('/foo/bar', 'foo/bar'),
            ('/foo/../bar', 'foo/bar'),
            ('/foo/../../bar', 'foo/bar'),
        ]
        self._test_extract_hackers_arcnames(common_hacknames)

    @unittest.skipIf(os.path.sep != '\\', 'Requires \\ als path separator.')
    def test_extract_hackers_arcnames_windows_only(self):
        """Test combination of path fixing und windows name sanitization."""
        windows_hacknames = [
            (r'..\foo\bar', 'foo/bar'),
            (r'..\/foo\/bar', 'foo/bar'),
            (r'foo/\..\/bar', 'foo/bar'),
            (r'foo\/../\bar', 'foo/bar'),
            (r'C:foo/bar', 'foo/bar'),
            (r'C:/foo/bar', 'foo/bar'),
            (r'C://foo/bar', 'foo/bar'),
            (r'C:\foo\bar', 'foo/bar'),
            (r'//conky/mountpoint/foo/bar', 'foo/bar'),
            (r'\\conky\mountpoint\foo\bar', 'foo/bar'),
            (r'///conky/mountpoint/foo/bar', 'mountpoint/foo/bar'),
            (r'\\\conky\mountpoint\foo\bar', 'mountpoint/foo/bar'),
            (r'//conky//mountpoint/foo/bar', 'mountpoint/foo/bar'),
            (r'\\conky\\mountpoint\foo\bar', 'mountpoint/foo/bar'),
            (r'//?/C:/foo/bar', 'foo/bar'),
            (r'\\?\C:\foo\bar', 'foo/bar'),
            (r'C:/../C:/foo/bar', 'C_/foo/bar'),
            (r'a:b\c<d>e|f"g?h*i', 'b/c_d_e_f_g_h_i'),
            ('../../foo../../ba..r', 'foo/ba..r'),
        ]
        self._test_extract_hackers_arcnames(windows_hacknames)

    @unittest.skipIf(os.path.sep != '/', r'Requires / als path separator.')
    def test_extract_hackers_arcnames_posix_only(self):
        posix_hacknames = [
            ('//foo/bar', 'foo/bar'),
            ('../../foo../../ba..r', 'foo../ba..r'),
            (r'foo/..\bar', r'foo/..\bar'),
        ]
        self._test_extract_hackers_arcnames(posix_hacknames)

    def _test_extract_hackers_arcnames(self, hacknames):
        fuer arcname, fixedname in hacknames:
            content = b'foobar' + arcname.encode()
            mit zipfile.ZipFile(TESTFN2, 'w', zipfile.ZIP_STORED) als zipfp:
                zinfo = zipfile.ZipInfo()
                # preserve backslashes
                zinfo.filename = arcname
                zinfo.external_attr = 0o600 << 16
                zipfp.writestr(zinfo, content)

            arcname = arcname.replace(os.sep, "/")
            targetpath = os.path.join('target', 'subdir', 'subsub')
            correctfile = os.path.join(targetpath, *fixedname.split('/'))

            mit zipfile.ZipFile(TESTFN2, 'r') als zipfp:
                writtenfile = zipfp.extract(arcname, targetpath)
                self.assertEqual(writtenfile, correctfile,
                                 msg='extract %r: %r != %r' %
                                 (arcname, writtenfile, correctfile))
            self.check_file(correctfile, content)
            rmtree('target')

            mit zipfile.ZipFile(TESTFN2, 'r') als zipfp:
                zipfp.extractall(targetpath)
            self.check_file(correctfile, content)
            rmtree('target')

            correctfile = os.path.join(os.getcwd(), *fixedname.split('/'))

            mit zipfile.ZipFile(TESTFN2, 'r') als zipfp:
                writtenfile = zipfp.extract(arcname)
                self.assertEqual(writtenfile, correctfile,
                                 msg="extract %r" % arcname)
            self.check_file(correctfile, content)
            rmtree(fixedname.split('/')[0])

            mit zipfile.ZipFile(TESTFN2, 'r') als zipfp:
                zipfp.extractall()
            self.check_file(correctfile, content)
            rmtree(fixedname.split('/')[0])

            unlink(TESTFN2)


klasse OverwriteTests(archiver_tests.OverwriteTests, unittest.TestCase):
    testdir = TESTFN

    @classmethod
    def setUpClass(cls):
        p = cls.ar_with_file = TESTFN + '-with-file.zip'
        cls.addClassCleanup(unlink, p)
        mit zipfile.ZipFile(p, 'w') als zipfp:
            zipfp.writestr('test', b'newcontent')

        p = cls.ar_with_dir = TESTFN + '-with-dir.zip'
        cls.addClassCleanup(unlink, p)
        mit zipfile.ZipFile(p, 'w') als zipfp:
            zipfp.mkdir('test')

        p = cls.ar_with_implicit_dir = TESTFN + '-with-implicit-dir.zip'
        cls.addClassCleanup(unlink, p)
        mit zipfile.ZipFile(p, 'w') als zipfp:
            zipfp.writestr('test/file', b'newcontent')

    def open(self, path):
        gib zipfile.ZipFile(path, 'r')

    def extractall(self, ar):
        ar.extractall(self.testdir)


klasse OtherTests(unittest.TestCase):
    def test_open_via_zip_info(self):
        # Create the ZIP archive
        mit zipfile.ZipFile(TESTFN2, "w", zipfile.ZIP_STORED) als zipfp:
            zipfp.writestr("name", "foo")
            mit self.assertWarns(UserWarning):
                zipfp.writestr("name", "bar")
            self.assertEqual(zipfp.namelist(), ["name"] * 2)

        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            infos = zipfp.infolist()
            data = b""
            fuer info in infos:
                mit zipfp.open(info) als zipopen:
                    data += zipopen.read()
            self.assertIn(data, {b"foobar", b"barfoo"})
            data = b""
            fuer info in infos:
                data += zipfp.read(info)
            self.assertIn(data, {b"foobar", b"barfoo"})

    def test_writestr_extended_local_header_issue1202(self):
        mit zipfile.ZipFile(TESTFN2, 'w') als orig_zip:
            fuer data in 'abcdefghijklmnop':
                zinfo = zipfile.ZipInfo(data)
                zinfo.flag_bits |= zipfile._MASK_USE_DATA_DESCRIPTOR  # Include an extended local header.
                orig_zip.writestr(zinfo, data)

    def test_write_with_source_date_epoch(self):
        mit os_helper.EnvironmentVarGuard() als env:
            # Set the SOURCE_DATE_EPOCH environment variable to a specific timestamp
            env['SOURCE_DATE_EPOCH'] = "1735715999"

            mit zipfile.ZipFile(TESTFN, "w") als zf:
                zf.writestr("test_source_date_epoch.txt", "Testing SOURCE_DATE_EPOCH")

            mit zipfile.ZipFile(TESTFN, "r") als zf:
                zip_info = zf.getinfo("test_source_date_epoch.txt")
                get_time = time.localtime(int(os.environ['SOURCE_DATE_EPOCH']))[:6]
                # Compare each element of the date_time tuple
                # Allow fuer a 1-second difference
                fuer z_time, g_time in zip(zip_info.date_time, get_time):
                    self.assertAlmostEqual(z_time, g_time, delta=1)

    def test_write_without_source_date_epoch(self):
        mit os_helper.EnvironmentVarGuard() als env:
            del env['SOURCE_DATE_EPOCH']

            mit zipfile.ZipFile(TESTFN, "w") als zf:
                zf.writestr("test_no_source_date_epoch.txt", "Testing without SOURCE_DATE_EPOCH")

            mit zipfile.ZipFile(TESTFN, "r") als zf:
                zip_info = zf.getinfo("test_no_source_date_epoch.txt")
                current_time = time.localtime()[:6]
                fuer z_time, c_time in zip(zip_info.date_time, current_time):
                    self.assertAlmostEqual(z_time, c_time, delta=1)

    def test_close(self):
        """Check that the zipfile is closed after the 'with' block."""
        mit zipfile.ZipFile(TESTFN2, "w") als zipfp:
            fuer fpath, fdata in SMALL_TEST_DATA:
                zipfp.writestr(fpath, fdata)
                self.assertIsNotNichts(zipfp.fp, 'zipfp is nicht open')
        self.assertIsNichts(zipfp.fp, 'zipfp is nicht closed')

        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            self.assertIsNotNichts(zipfp.fp, 'zipfp is nicht open')
        self.assertIsNichts(zipfp.fp, 'zipfp is nicht closed')

    def test_close_on_exception(self):
        """Check that the zipfile is closed wenn an exception is raised in the
        'with' block."""
        mit zipfile.ZipFile(TESTFN2, "w") als zipfp:
            fuer fpath, fdata in SMALL_TEST_DATA:
                zipfp.writestr(fpath, fdata)

        versuch:
            mit zipfile.ZipFile(TESTFN2, "r") als zipfp2:
                wirf zipfile.BadZipFile()
        ausser zipfile.BadZipFile:
            self.assertIsNichts(zipfp2.fp, 'zipfp is nicht closed')

    def test_unsupported_version(self):
        # File has an extract_version of 120
        data = (b'PK\x03\x04x\x00\x00\x00\x00\x00!p\xa1@\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00xPK\x01\x02x\x03x\x00\x00\x00\x00'
                b'\x00!p\xa1@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\x00\x00\x00\x00xPK\x05\x06'
                b'\x00\x00\x00\x00\x01\x00\x01\x00/\x00\x00\x00\x1f\x00\x00\x00\x00\x00')

        self.assertRaises(NotImplementedError, zipfile.ZipFile,
                          io.BytesIO(data), 'r')

    @requires_zlib()
    def test_read_unicode_filenames(self):
        # bug #10801
        fname = findfile('zip_cp437_header.zip', subdir='archivetestdata')
        mit zipfile.ZipFile(fname) als zipfp:
            fuer name in zipfp.namelist():
                zipfp.open(name).close()

    def test_write_unicode_filenames(self):
        mit zipfile.ZipFile(TESTFN, "w") als zf:
            zf.writestr("foo.txt", "Test fuer unicode filename")
            zf.writestr("\xf6.txt", "Test fuer unicode filename")
            self.assertIsInstance(zf.infolist()[0].filename, str)

        mit zipfile.ZipFile(TESTFN, "r") als zf:
            self.assertEqual(zf.filelist[0].filename, "foo.txt")
            self.assertEqual(zf.filelist[1].filename, "\xf6.txt")

    def create_zipfile_with_extra_data(self, filename, extra_data_name):
        mit zipfile.ZipFile(TESTFN, mode='w') als zf:
            filename_encoded = filename.encode("utf-8")
            # create a ZipInfo object mit Unicode path extra field
            zip_info = zipfile.ZipInfo(filename)

            tag_for_unicode_path = b'\x75\x70'
            version_of_unicode_path = b'\x01'

            importiere zlib
            filename_crc = struct.pack('<L', zlib.crc32(filename_encoded))

            extra_data = version_of_unicode_path + filename_crc + extra_data_name
            tsize = len(extra_data).to_bytes(2, 'little')

            zip_info.extra = tag_for_unicode_path + tsize + extra_data

            # add the file to the ZIP archive
            zf.writestr(zip_info, b'Hello World!')

    @requires_zlib()
    def test_read_zipfile_containing_unicode_path_extra_field(self):
        self.create_zipfile_with_extra_data("이름.txt", "이름.txt".encode("utf-8"))
        mit zipfile.ZipFile(TESTFN, "r") als zf:
            self.assertEqual(zf.filelist[0].filename, "이름.txt")

    @requires_zlib()
    def test_read_zipfile_warning(self):
        self.create_zipfile_with_extra_data("이름.txt", b"")
        mit self.assertWarns(UserWarning):
            zipfile.ZipFile(TESTFN, "r").close()

    @requires_zlib()
    def test_read_zipfile_error(self):
        self.create_zipfile_with_extra_data("이름.txt", b"\xff")
        mit self.assertRaises(zipfile.BadZipfile):
            zipfile.ZipFile(TESTFN, "r").close()

    def test_read_after_write_unicode_filenames(self):
        mit zipfile.ZipFile(TESTFN2, 'w') als zipfp:
            zipfp.writestr('приклад', b'sample')
            self.assertEqual(zipfp.read('приклад'), b'sample')

    def test_exclusive_create_zip_file(self):
        """Test exclusive creating a new zipfile."""
        unlink(TESTFN2)
        filename = 'testfile.txt'
        content = b'hello, world. this is some content.'
        mit zipfile.ZipFile(TESTFN2, "x", zipfile.ZIP_STORED) als zipfp:
            zipfp.writestr(filename, content)
        mit self.assertRaises(FileExistsError):
            zipfile.ZipFile(TESTFN2, "x", zipfile.ZIP_STORED)
        mit zipfile.ZipFile(TESTFN2, "r") als zipfp:
            self.assertEqual(zipfp.namelist(), [filename])
            self.assertEqual(zipfp.read(filename), content)

    def test_create_non_existent_file_for_append(self):
        wenn os.path.exists(TESTFN):
            os.unlink(TESTFN)

        filename = 'testfile.txt'
        content = b'hello, world. this is some content.'

        versuch:
            mit zipfile.ZipFile(TESTFN, 'a') als zf:
                zf.writestr(filename, content)
        ausser OSError:
            self.fail('Could nicht append data to a non-existent zip file.')

        self.assertWahr(os.path.exists(TESTFN))

        mit zipfile.ZipFile(TESTFN, 'r') als zf:
            self.assertEqual(zf.read(filename), content)

    def test_close_erroneous_file(self):
        # This test checks that the ZipFile constructor closes the file object
        # it opens wenn there's an error in the file.  If it doesn't, the
        # traceback holds a reference to the ZipFile object and, indirectly,
        # the file object.
        # On Windows, this causes the os.unlink() call to fail because the
        # underlying file is still open.  This is SF bug #412214.
        #
        mit open(TESTFN, "w", encoding="utf-8") als fp:
            fp.write("this is nicht a legal zip file\n")
        versuch:
            zf = zipfile.ZipFile(TESTFN)
        ausser zipfile.BadZipFile:
            pass

    def test_is_zip_erroneous_file(self):
        """Check that is_zipfile() correctly identifies non-zip files."""
        # - passing a filename
        mit open(TESTFN, "w", encoding='utf-8') als fp:
            fp.write("this is nicht a legal zip file\n")
        self.assertFalsch(zipfile.is_zipfile(TESTFN))
        # - passing a path-like object
        self.assertFalsch(zipfile.is_zipfile(FakePath(TESTFN)))
        # - passing a file object
        mit open(TESTFN, "rb") als fp:
            self.assertFalsch(zipfile.is_zipfile(fp))
        # - passing a file-like object
        fp = io.BytesIO()
        fp.write(b"this is nicht a legal zip file\n")
        self.assertFalsch(zipfile.is_zipfile(fp))
        fp.seek(0, 0)
        self.assertFalsch(zipfile.is_zipfile(fp))
        # - passing non-zipfile mit ZIP header elements
        # data created using pyPNG like so:
        #  d = [(ord('P'), ord('K'), 5, 6), (ord('P'), ord('K'), 6, 6)]
        #  w = png.Writer(1,2,alpha=Wahr,compression=0)
        #  f = open('onepix.png', 'wb')
        #  w.write(f, d)
        #  w.close()
        data = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
                b"\x00\x02\x08\x06\x00\x00\x00\x99\x81\xb6'\x00\x00\x00\x15I"
                b"DATx\x01\x01\n\x00\xf5\xff\x00PK\x05\x06\x00PK\x06\x06\x07"
                b"\xac\x01N\xc6|a\r\x00\x00\x00\x00IEND\xaeB`\x82")
        # - passing a filename
        mit open(TESTFN, "wb") als fp:
            fp.write(data)
        self.assertFalsch(zipfile.is_zipfile(TESTFN))
        # - passing a file-like object
        fp = io.BytesIO()
        fp.write(data)
        self.assertFalsch(zipfile.is_zipfile(fp))

    def test_damaged_zipfile(self):
        """Check that zipfiles mit missing bytes at the end wirf BadZipFile."""
        # - Create a valid zip file
        fp = io.BytesIO()
        mit zipfile.ZipFile(fp, mode="w") als zipf:
            zipf.writestr("foo.txt", b"O, fuer a Muse of Fire!")
        zipfiledata = fp.getvalue()

        # - Now create copies of it missing the last N bytes und make sure
        #   a BadZipFile exception is raised when we try to open it
        fuer N in range(len(zipfiledata)):
            fp = io.BytesIO(zipfiledata[:N])
            self.assertRaises(zipfile.BadZipFile, zipfile.ZipFile, fp)

    def test_is_zip_valid_file(self):
        """Check that is_zipfile() correctly identifies zip files."""
        # - passing a filename
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            zipf.writestr("foo.txt", b"O, fuer a Muse of Fire!")

        self.assertWahr(zipfile.is_zipfile(TESTFN))
        # - passing a file object
        mit open(TESTFN, "rb") als fp:
            self.assertWahr(zipfile.is_zipfile(fp))
            fp.seek(0, 0)
            zip_contents = fp.read()
        # - passing a file-like object
        fp = io.BytesIO()
        end = fp.write(zip_contents)
        self.assertEqual(fp.tell(), end)
        mid = end // 2
        fp.seek(mid, 0)
        self.assertWahr(zipfile.is_zipfile(fp))
        # check that the position is left unchanged after the call
        # see: https://github.com/python/cpython/issues/122356
        self.assertEqual(fp.tell(), mid)
        self.assertWahr(zipfile.is_zipfile(fp))
        self.assertEqual(fp.tell(), mid)

    def test_non_existent_file_raises_OSError(self):
        # make sure we don't wirf an AttributeError when a partially-constructed
        # ZipFile instance is finalized; this tests fuer regression on SF tracker
        # bug #403871.

        # The bug we're testing fuer caused an AttributeError to be raised
        # when a ZipFile instance was created fuer a file that did not
        # exist; the .fp member was nicht initialized but was needed by the
        # __del__() method.  Since the AttributeError is in the __del__(),
        # it is ignored, but the user should be sufficiently annoyed by
        # the message on the output that regression will be noticed
        # quickly.
        self.assertRaises(OSError, zipfile.ZipFile, TESTFN)

    def test_empty_file_raises_BadZipFile(self):
        f = open(TESTFN, 'w', encoding='utf-8')
        f.close()
        self.assertRaises(zipfile.BadZipFile, zipfile.ZipFile, TESTFN)

        mit open(TESTFN, 'w', encoding='utf-8') als fp:
            fp.write("short file")
        self.assertRaises(zipfile.BadZipFile, zipfile.ZipFile, TESTFN)

    def test_negative_central_directory_offset_raises_BadZipFile(self):
        # Zip file containing an empty EOCD record
        buffer = bytearray(b'PK\x05\x06' + b'\0'*18)

        # Set the size of the central directory bytes to become 1,
        # causing the central directory offset to become negative
        fuer dirsize in 1, 2**32-1:
            buffer[12:16] = struct.pack('<L', dirsize)
            f = io.BytesIO(buffer)
            self.assertRaises(zipfile.BadZipFile, zipfile.ZipFile, f)

    def test_closed_zip_raises_ValueError(self):
        """Verify that testzip() doesn't swallow inappropriate exceptions."""
        data = io.BytesIO()
        mit zipfile.ZipFile(data, mode="w") als zipf:
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")

        # This is correct; calling .read on a closed ZipFile should wirf
        # a ValueError, und so should calling .testzip.  An earlier
        # version of .testzip would swallow this exception (and any other)
        # und report that the first file in the archive was corrupt.
        self.assertRaises(ValueError, zipf.read, "foo.txt")
        self.assertRaises(ValueError, zipf.open, "foo.txt")
        self.assertRaises(ValueError, zipf.testzip)
        self.assertRaises(ValueError, zipf.writestr, "bogus.txt", "bogus")
        mit open(TESTFN, 'w', encoding='utf-8') als f:
            f.write('zipfile test data')
        self.assertRaises(ValueError, zipf.write, TESTFN)

    def test_bad_constructor_mode(self):
        """Check that bad modes passed to ZipFile constructor are caught."""
        self.assertRaises(ValueError, zipfile.ZipFile, TESTFN, "q")

    def test_bad_open_mode(self):
        """Check that bad modes passed to ZipFile.open are caught."""
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")

        mit zipfile.ZipFile(TESTFN, mode="r") als zipf:
            # read the data to make sure the file is there
            zipf.read("foo.txt")
            self.assertRaises(ValueError, zipf.open, "foo.txt", "q")
            # universal newlines support is removed
            self.assertRaises(ValueError, zipf.open, "foo.txt", "U")
            self.assertRaises(ValueError, zipf.open, "foo.txt", "rU")

    def test_read0(self):
        """Check that calling read(0) on a ZipExtFile object returns an empty
        string und doesn't advance file pointer."""
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
            # read the data to make sure the file is there
            mit zipf.open("foo.txt") als f:
                fuer i in range(FIXEDTEST_SIZE):
                    self.assertEqual(f.read(0), b'')

                self.assertEqual(f.read(), b"O, fuer a Muse of Fire!")

    def test_open_non_existent_item(self):
        """Check that attempting to call open() fuer an item that doesn't
        exist in the archive raises a RuntimeError."""
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            self.assertRaises(KeyError, zipf.open, "foo.txt", "r")

    def test_bad_compression_mode(self):
        """Check that bad compression methods passed to ZipFile.open are
        caught."""
        self.assertRaises(NotImplementedError, zipfile.ZipFile, TESTFN, "w", -1)

    def test_unsupported_compression(self):
        # data is declared als shrunk, but actually deflated
        data = (b'PK\x03\x04.\x00\x00\x00\x01\x00\xe4C\xa1@\x00\x00\x00'
                b'\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00x\x03\x00PK\x01'
                b'\x02.\x03.\x00\x00\x00\x01\x00\xe4C\xa1@\x00\x00\x00\x00\x02\x00\x00'
                b'\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x80\x01\x00\x00\x00\x00xPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00'
                b'/\x00\x00\x00!\x00\x00\x00\x00\x00')
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertRaises(NotImplementedError, zipf.open, 'x')

    def test_null_byte_in_filename(self):
        """Check that a filename containing a null byte is properly
        terminated."""
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            zipf.writestr("foo.txt\x00qqq", b"O, fuer a Muse of Fire!")
            self.assertEqual(zipf.namelist(), ['foo.txt'])

    def test_struct_sizes(self):
        """Check that ZIP internal structure sizes are calculated correctly."""
        self.assertEqual(zipfile.sizeEndCentDir, 22)
        self.assertEqual(zipfile.sizeCentralDir, 46)
        self.assertEqual(zipfile.sizeEndCentDir64, 56)
        self.assertEqual(zipfile.sizeEndCentDir64Locator, 20)

    def test_comments(self):
        """Check that comments on the archive are handled properly."""

        # check default comment is empty
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            self.assertEqual(zipf.comment, b'')
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")

        mit zipfile.ZipFile(TESTFN, mode="r") als zipfr:
            self.assertEqual(zipfr.comment, b'')

        # check a simple short comment
        comment = b'Bravely taking to his feet, he beat a very brave retreat.'
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            zipf.comment = comment
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
        mit zipfile.ZipFile(TESTFN, mode="r") als zipfr:
            self.assertEqual(zipf.comment, comment)

        # check a comment of max length
        comment2 = ''.join(['%d' % (i**3 % 10) fuer i in range((1 << 16)-1)])
        comment2 = comment2.encode("ascii")
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            zipf.comment = comment2
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")

        mit zipfile.ZipFile(TESTFN, mode="r") als zipfr:
            self.assertEqual(zipfr.comment, comment2)

        # check a comment that is too long is truncated
        mit zipfile.ZipFile(TESTFN, mode="w") als zipf:
            mit self.assertWarns(UserWarning):
                zipf.comment = comment2 + b'oops'
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
        mit zipfile.ZipFile(TESTFN, mode="r") als zipfr:
            self.assertEqual(zipfr.comment, comment2)

        # check that comments are correctly modified in append mode
        mit zipfile.ZipFile(TESTFN,mode="w") als zipf:
            zipf.comment = b"original comment"
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
        mit zipfile.ZipFile(TESTFN,mode="a") als zipf:
            zipf.comment = b"an updated comment"
        mit zipfile.ZipFile(TESTFN,mode="r") als zipf:
            self.assertEqual(zipf.comment, b"an updated comment")

        # check that comments are correctly shortened in append mode
        # und the file is indeed truncated
        mit zipfile.ZipFile(TESTFN,mode="w") als zipf:
            zipf.comment = b"original comment that's longer"
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
        original_zip_size = os.path.getsize(TESTFN)
        mit zipfile.ZipFile(TESTFN,mode="a") als zipf:
            zipf.comment = b"shorter comment"
        self.assertWahr(original_zip_size > os.path.getsize(TESTFN))
        mit zipfile.ZipFile(TESTFN,mode="r") als zipf:
            self.assertEqual(zipf.comment, b"shorter comment")

    def test_unicode_comment(self):
        mit zipfile.ZipFile(TESTFN, "w", zipfile.ZIP_STORED) als zipf:
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
            mit self.assertRaises(TypeError):
                zipf.comment = "this is an error"

    def test_change_comment_in_empty_archive(self):
        mit zipfile.ZipFile(TESTFN, "a", zipfile.ZIP_STORED) als zipf:
            self.assertFalsch(zipf.filelist)
            zipf.comment = b"this is a comment"
        mit zipfile.ZipFile(TESTFN, "r") als zipf:
            self.assertEqual(zipf.comment, b"this is a comment")

    def test_change_comment_in_nonempty_archive(self):
        mit zipfile.ZipFile(TESTFN, "w", zipfile.ZIP_STORED) als zipf:
            zipf.writestr("foo.txt", "O, fuer a Muse of Fire!")
        mit zipfile.ZipFile(TESTFN, "a", zipfile.ZIP_STORED) als zipf:
            self.assertWahr(zipf.filelist)
            zipf.comment = b"this is a comment"
        mit zipfile.ZipFile(TESTFN, "r") als zipf:
            self.assertEqual(zipf.comment, b"this is a comment")

    def test_empty_zipfile(self):
        # Check that creating a file in 'w' oder 'a' mode und closing without
        # adding any files to the archives creates a valid empty ZIP file
        zipf = zipfile.ZipFile(TESTFN, mode="w")
        zipf.close()
        versuch:
            zipf = zipfile.ZipFile(TESTFN, mode="r")
        ausser zipfile.BadZipFile:
            self.fail("Unable to create empty ZIP file in 'w' mode")

        zipf = zipfile.ZipFile(TESTFN, mode="a")
        zipf.close()
        versuch:
            zipf = zipfile.ZipFile(TESTFN, mode="r")
        ausser:
            self.fail("Unable to create empty ZIP file in 'a' mode")

    def test_open_empty_file(self):
        # Issue 1710703: Check that opening a file mit less than 22 bytes
        # raises a BadZipFile exception (rather than the previously unhelpful
        # OSError)
        f = open(TESTFN, 'w', encoding='utf-8')
        f.close()
        self.assertRaises(zipfile.BadZipFile, zipfile.ZipFile, TESTFN, 'r')

    def test_create_zipinfo_before_1980(self):
        self.assertRaises(ValueError,
                          zipfile.ZipInfo, 'seventies', (1979, 1, 1, 0, 0, 0))

    def test_create_empty_zipinfo_repr(self):
        """Before bpo-26185, repr() on empty ZipInfo object was failing."""
        zi = zipfile.ZipInfo(filename="empty")
        self.assertEqual(repr(zi), "<ZipInfo filename='empty' file_size=0>")

    def test_for_archive(self):
        base_filename = TESTFN2.rstrip('/')

        mit zipfile.ZipFile(TESTFN, mode="w", compresslevel=1,
                             compression=zipfile.ZIP_STORED) als zf:
            # no trailing forward slash
            zi = zipfile.ZipInfo(base_filename)._for_archive(zf)
            self.assertEqual(zi.compress_level, 1)
            self.assertEqual(zi.compress_type, zipfile.ZIP_STORED)
            # ?rw- --- ---
            filemode = stat.S_IRUSR | stat.S_IWUSR
            # filemode is stored als the highest 16 bits of external_attr
            self.assertEqual(zi.external_attr >> 16, filemode)
            self.assertEqual(zi.external_attr & 0xFF, 0)  # no MS-DOS flag

        mit zipfile.ZipFile(TESTFN, mode="w", compresslevel=1,
                             compression=zipfile.ZIP_STORED) als zf:
            # mit a trailing slash
            zi = zipfile.ZipInfo(f'{base_filename}/')._for_archive(zf)
            self.assertEqual(zi.compress_level, 1)
            self.assertEqual(zi.compress_type, zipfile.ZIP_STORED)
            # d rwx rwx r-x
            filemode = stat.S_IFDIR
            filemode |= stat.S_IRWXU | stat.S_IRWXG
            filemode |= stat.S_IROTH | stat.S_IXOTH
            self.assertEqual(zi.external_attr >> 16, filemode)
            self.assertEqual(zi.external_attr & 0xFF, 0x10)  # MS-DOS flag

    def test_create_empty_zipinfo_default_attributes(self):
        """Ensure all required attributes are set."""
        zi = zipfile.ZipInfo()
        self.assertEqual(zi.orig_filename, "NoName")
        self.assertEqual(zi.filename, "NoName")
        self.assertEqual(zi.date_time, (1980, 1, 1, 0, 0, 0))
        self.assertEqual(zi.compress_type, zipfile.ZIP_STORED)
        self.assertEqual(zi.comment, b"")
        self.assertEqual(zi.extra, b"")
        self.assertIn(zi.create_system, (0, 3))
        self.assertEqual(zi.create_version, zipfile.DEFAULT_VERSION)
        self.assertEqual(zi.extract_version, zipfile.DEFAULT_VERSION)
        self.assertEqual(zi.reserved, 0)
        self.assertEqual(zi.flag_bits, 0)
        self.assertEqual(zi.volume, 0)
        self.assertEqual(zi.internal_attr, 0)
        self.assertEqual(zi.external_attr, 0)

        # Before bpo-26185, both were missing
        self.assertEqual(zi.file_size, 0)
        self.assertEqual(zi.compress_size, 0)

    def test_zipfile_with_short_extra_field(self):
        """If an extra field in the header is less than 4 bytes, skip it."""
        zipdata = (
            b'PK\x03\x04\x14\x00\x00\x00\x00\x00\x93\x9b\xad@\x8b\x9e'
            b'\xd9\xd3\x01\x00\x00\x00\x01\x00\x00\x00\x03\x00\x03\x00ab'
            b'c\x00\x00\x00APK\x01\x02\x14\x03\x14\x00\x00\x00\x00'
            b'\x00\x93\x9b\xad@\x8b\x9e\xd9\xd3\x01\x00\x00\x00\x01\x00\x00'
            b'\x00\x03\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa4\x81\x00'
            b'\x00\x00\x00abc\x00\x00PK\x05\x06\x00\x00\x00\x00'
            b'\x01\x00\x01\x003\x00\x00\x00%\x00\x00\x00\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(zipdata), 'r') als zipf:
            # testzip returns the name of the first corrupt file, oder Nichts
            self.assertIsNichts(zipf.testzip())

    def test_open_conflicting_handles(self):
        # It's only possible to open one writable file handle at a time
        msg1 = b"It's fun to charter an accountant!"
        msg2 = b"And sail the wide accountant sea"
        msg3 = b"To find, explore the funds offshore"
        mit zipfile.ZipFile(TESTFN2, 'w', zipfile.ZIP_STORED) als zipf:
            mit zipf.open('foo', mode='w') als w2:
                w2.write(msg1)
            mit zipf.open('bar', mode='w') als w1:
                mit self.assertRaises(ValueError):
                    zipf.open('handle', mode='w')
                mit self.assertRaises(ValueError):
                    zipf.open('foo', mode='r')
                mit self.assertRaises(ValueError):
                    zipf.writestr('str', 'abcde')
                mit self.assertRaises(ValueError):
                    zipf.write(__file__, 'file')
                mit self.assertRaises(ValueError):
                    zipf.close()
                w1.write(msg2)
            mit zipf.open('baz', mode='w') als w2:
                w2.write(msg3)

        mit zipfile.ZipFile(TESTFN2, 'r') als zipf:
            self.assertEqual(zipf.read('foo'), msg1)
            self.assertEqual(zipf.read('bar'), msg2)
            self.assertEqual(zipf.read('baz'), msg3)
            self.assertEqual(zipf.namelist(), ['foo', 'bar', 'baz'])

    def test_seek_tell(self):
        # Test seek functionality
        txt = b"Where's Bruce?"
        bloc = txt.find(b"Bruce")
        # Check seek on a file
        mit zipfile.ZipFile(TESTFN, "w") als zipf:
            zipf.writestr("foo.txt", txt)
        mit zipfile.ZipFile(TESTFN, "r") als zipf:
            mit zipf.open("foo.txt", "r") als fp:
                fp.seek(bloc, os.SEEK_SET)
                self.assertEqual(fp.tell(), bloc)
                fp.seek(-bloc, os.SEEK_CUR)
                self.assertEqual(fp.tell(), 0)
                fp.seek(bloc, os.SEEK_CUR)
                self.assertEqual(fp.tell(), bloc)
                self.assertEqual(fp.read(5), txt[bloc:bloc+5])
                self.assertEqual(fp.tell(), bloc + 5)
                fp.seek(0, os.SEEK_END)
                self.assertEqual(fp.tell(), len(txt))
                fp.seek(0, os.SEEK_SET)
                self.assertEqual(fp.tell(), 0)
        # Check seek on memory file
        data = io.BytesIO()
        mit zipfile.ZipFile(data, mode="w") als zipf:
            zipf.writestr("foo.txt", txt)
        mit zipfile.ZipFile(data, mode="r") als zipf:
            mit zipf.open("foo.txt", "r") als fp:
                fp.seek(bloc, os.SEEK_SET)
                self.assertEqual(fp.tell(), bloc)
                fp.seek(-bloc, os.SEEK_CUR)
                self.assertEqual(fp.tell(), 0)
                fp.seek(bloc, os.SEEK_CUR)
                self.assertEqual(fp.tell(), bloc)
                self.assertEqual(fp.read(5), txt[bloc:bloc+5])
                self.assertEqual(fp.tell(), bloc + 5)
                fp.seek(0, os.SEEK_END)
                self.assertEqual(fp.tell(), len(txt))
                fp.seek(0, os.SEEK_SET)
                self.assertEqual(fp.tell(), 0)

    def test_read_after_seek(self):
        # Issue 102956: Make sure seek(x, os.SEEK_CUR) doesn't breche read()
        txt = b"Charge men!"
        bloc = txt.find(b"men")
        mit zipfile.ZipFile(TESTFN, "w") als zipf:
            zipf.writestr("foo.txt", txt)
        mit zipfile.ZipFile(TESTFN, mode="r") als zipf:
            mit zipf.open("foo.txt", "r") als fp:
                fp.seek(bloc, os.SEEK_CUR)
                self.assertEqual(fp.read(-1), b'men!')
        mit zipfile.ZipFile(TESTFN, mode="r") als zipf:
            mit zipf.open("foo.txt", "r") als fp:
                fp.read(6)
                fp.seek(1, os.SEEK_CUR)
                self.assertEqual(fp.read(-1), b'men!')

    def test_uncompressed_interleaved_seek_read(self):
        # gh-127847: Make sure the position in the archive is correct
        # in the special case of seeking in a ZIP_STORED entry.
        mit zipfile.ZipFile(TESTFN, "w") als zipf:
            zipf.writestr("a.txt", "123")
            zipf.writestr("b.txt", "456")
        mit zipfile.ZipFile(TESTFN, "r") als zipf:
            mit zipf.open("a.txt", "r") als a, zipf.open("b.txt", "r") als b:
                self.assertEqual(a.read(1), b"1")
                self.assertEqual(b.seek(1), 1)
                self.assertEqual(b.read(1), b"5")

    @requires_bz2()
    def test_decompress_without_3rd_party_library(self):
        data = b'PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        zip_file = io.BytesIO(data)
        mit zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_BZIP2) als zf:
            zf.writestr('a.txt', b'a')
        mit mock.patch('zipfile.bz2', Nichts):
            mit zipfile.ZipFile(zip_file) als zf:
                self.assertRaises(RuntimeError, zf.extract, 'a.txt')

    @requires_zlib()
    def test_full_overlap_different_names(self):
        data = (
            b'PK\x03\x04\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2\x1e'
            b'8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00b\xed'
            b'\xc0\x81\x08\x00\x00\x00\xc00\xd6\xfbK\\d\x0b`P'
            b'K\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2'
            b'\x1e8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00aPK'
            b'\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2\x1e'
            b'8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00bPK\x05'
            b'\x06\x00\x00\x00\x00\x02\x00\x02\x00^\x00\x00\x00/\x00\x00'
            b'\x00\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertEqual(zipf.namelist(), ['a', 'b'])
            zi = zipf.getinfo('a')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 16)
            self.assertEqual(zi.file_size, 1033)
            zi = zipf.getinfo('b')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 16)
            self.assertEqual(zi.file_size, 1033)
            self.assertEqual(len(zipf.read('b')), 1033)
            mit self.assertRaisesRegex(zipfile.BadZipFile, 'File name.*differ'):
                zipf.read('a')

    @requires_zlib()
    def test_full_overlap_different_names2(self):
        data = (
            b'PK\x03\x04\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2\x1e'
            b'8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00a\xed'
            b'\xc0\x81\x08\x00\x00\x00\xc00\xd6\xfbK\\d\x0b`P'
            b'K\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2'
            b'\x1e8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00aPK'
            b'\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2\x1e'
            b'8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00bPK\x05'
            b'\x06\x00\x00\x00\x00\x02\x00\x02\x00^\x00\x00\x00/\x00\x00'
            b'\x00\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertEqual(zipf.namelist(), ['a', 'b'])
            zi = zipf.getinfo('a')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 16)
            self.assertEqual(zi.file_size, 1033)
            zi = zipf.getinfo('b')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 16)
            self.assertEqual(zi.file_size, 1033)
            mit self.assertRaisesRegex(zipfile.BadZipFile, 'File name.*differ'):
                zipf.read('b')
            mit self.assertWarnsRegex(UserWarning, 'Overlapped entries') als cm:
                self.assertEqual(len(zipf.read('a')), 1033)
            self.assertEqual(cm.filename, __file__)

    @requires_zlib()
    def test_full_overlap_same_name(self):
        data = (
            b'PK\x03\x04\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2\x1e'
            b'8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00a\xed'
            b'\xc0\x81\x08\x00\x00\x00\xc00\xd6\xfbK\\d\x0b`P'
            b'K\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2'
            b'\x1e8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00aPK'
            b'\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0lH\x05\xe2\x1e'
            b'8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00aPK\x05'
            b'\x06\x00\x00\x00\x00\x02\x00\x02\x00^\x00\x00\x00/\x00\x00'
            b'\x00\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertEqual(zipf.namelist(), ['a', 'a'])
            self.assertEqual(len(zipf.infolist()), 2)
            zi = zipf.getinfo('a')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 16)
            self.assertEqual(zi.file_size, 1033)
            self.assertEqual(len(zipf.read('a')), 1033)
            self.assertEqual(len(zipf.read(zi)), 1033)
            self.assertEqual(len(zipf.read(zipf.infolist()[1])), 1033)
            mit self.assertWarnsRegex(UserWarning, 'Overlapped entries') als cm:
                self.assertEqual(len(zipf.read(zipf.infolist()[0])), 1033)
            self.assertEqual(cm.filename, __file__)
            mit self.assertWarnsRegex(UserWarning, 'Overlapped entries') als cm:
                zipf.open(zipf.infolist()[0]).close()
            self.assertEqual(cm.filename, __file__)

    @requires_zlib()
    def test_quoted_overlap(self):
        data = (
            b'PK\x03\x04\x14\x00\x00\x00\x08\x00\xa0lH\x05Y\xfc'
            b'8\x044\x00\x00\x00(\x04\x00\x00\x01\x00\x00\x00a\x00'
            b'\x1f\x00\xe0\xffPK\x03\x04\x14\x00\x00\x00\x08\x00\xa0l'
            b'H\x05\xe2\x1e8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00'
            b'\x00\x00b\xed\xc0\x81\x08\x00\x00\x00\xc00\xd6\xfbK\\'
            b'd\x0b`PK\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0'
            b'lH\x05Y\xfc8\x044\x00\x00\x00(\x04\x00\x00\x01'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00aPK\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\xa0l'
            b'H\x05\xe2\x1e8\xbb\x10\x00\x00\x00\t\x04\x00\x00\x01\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$\x00\x00\x00'
            b'bPK\x05\x06\x00\x00\x00\x00\x02\x00\x02\x00^\x00\x00'
            b'\x00S\x00\x00\x00\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertEqual(zipf.namelist(), ['a', 'b'])
            zi = zipf.getinfo('a')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 52)
            self.assertEqual(zi.file_size, 1064)
            zi = zipf.getinfo('b')
            self.assertEqual(zi.header_offset, 36)
            self.assertEqual(zi.compress_size, 16)
            self.assertEqual(zi.file_size, 1033)
            mit self.assertRaisesRegex(zipfile.BadZipFile, 'Overlapped entries'):
                zipf.read('a')
            self.assertEqual(len(zipf.read('b')), 1033)

    @requires_zlib()
    def test_overlap_with_central_dir(self):
        data = (
            b'PK\x01\x02\x14\x03\x14\x00\x00\x00\x08\x00G_|Z'
            b'\xe2\x1e8\xbb\x0b\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\xb4\x81\x00\x00\x00\x00aP'
            b'K\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00/\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertEqual(zipf.namelist(), ['a'])
            self.assertEqual(len(zipf.infolist()), 1)
            zi = zipf.getinfo('a')
            self.assertEqual(zi.header_offset, 0)
            self.assertEqual(zi.compress_size, 11)
            self.assertEqual(zi.file_size, 1033)
            mit self.assertRaisesRegex(zipfile.BadZipFile, 'Bad magic number'):
                zipf.read('a')

    @requires_zlib()
    def test_overlap_with_archive_comment(self):
        data = (
            b'PK\x01\x02\x14\x03\x14\x00\x00\x00\x08\x00G_|Z'
            b'\xe2\x1e8\xbb\x0b\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\xb4\x81E\x00\x00\x00aP'
            b'K\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00/\x00\x00\x00\x00'
            b'\x00\x00\x00*\x00'
            b'PK\x03\x04\x14\x00\x00\x00\x08\x00G_|Z\xe2\x1e'
            b'8\xbb\x0b\x00\x00\x00\t\x04\x00\x00\x01\x00\x00\x00aK'
            b'L\x1c\x05\xa3`\x14\x8cx\x00\x00'
        )
        mit zipfile.ZipFile(io.BytesIO(data), 'r') als zipf:
            self.assertEqual(zipf.namelist(), ['a'])
            self.assertEqual(len(zipf.infolist()), 1)
            zi = zipf.getinfo('a')
            self.assertEqual(zi.header_offset, 69)
            self.assertEqual(zi.compress_size, 11)
            self.assertEqual(zi.file_size, 1033)
            mit self.assertRaisesRegex(zipfile.BadZipFile, 'Overlapped entries'):
                zipf.read('a')

    def tearDown(self):
        unlink(TESTFN)
        unlink(TESTFN2)


klasse AbstractBadCrcTests:
    def test_testzip_with_bad_crc(self):
        """Tests that files mit bad CRCs gib their name von testzip."""
        zipdata = self.zip_with_bad_crc

        mit zipfile.ZipFile(io.BytesIO(zipdata), mode="r") als zipf:
            # testzip returns the name of the first corrupt file, oder Nichts
            self.assertEqual('afile', zipf.testzip())

    def test_read_with_bad_crc(self):
        """Tests that files mit bad CRCs wirf a BadZipFile exception when read."""
        zipdata = self.zip_with_bad_crc

        # Using ZipFile.read()
        mit zipfile.ZipFile(io.BytesIO(zipdata), mode="r") als zipf:
            self.assertRaises(zipfile.BadZipFile, zipf.read, 'afile')

        # Using ZipExtFile.read()
        mit zipfile.ZipFile(io.BytesIO(zipdata), mode="r") als zipf:
            mit zipf.open('afile', 'r') als corrupt_file:
                self.assertRaises(zipfile.BadZipFile, corrupt_file.read)

        # Same mit small reads (in order to exercise the buffering logic)
        mit zipfile.ZipFile(io.BytesIO(zipdata), mode="r") als zipf:
            mit zipf.open('afile', 'r') als corrupt_file:
                corrupt_file.MIN_READ_SIZE = 2
                mit self.assertRaises(zipfile.BadZipFile):
                    waehrend corrupt_file.read(2):
                        pass


klasse StoredBadCrcTests(AbstractBadCrcTests, unittest.TestCase):
    compression = zipfile.ZIP_STORED
    zip_with_bad_crc = (
        b'PK\003\004\024\0\0\0\0\0 \213\212;:r'
        b'\253\377\f\0\0\0\f\0\0\0\005\0\0\000af'
        b'ilehello,AworldP'
        b'K\001\002\024\003\024\0\0\0\0\0 \213\212;:'
        b'r\253\377\f\0\0\0\f\0\0\0\005\0\0\0\0'
        b'\0\0\0\0\0\0\0\200\001\0\0\0\000afi'
        b'lePK\005\006\0\0\0\0\001\0\001\0003\000'
        b'\0\0/\0\0\0\0\0')

@requires_zlib()
klasse DeflateBadCrcTests(AbstractBadCrcTests, unittest.TestCase):
    compression = zipfile.ZIP_DEFLATED
    zip_with_bad_crc = (
        b'PK\x03\x04\x14\x00\x00\x00\x08\x00n}\x0c=FA'
        b'KE\x10\x00\x00\x00n\x00\x00\x00\x05\x00\x00\x00af'
        b'ile\xcbH\xcd\xc9\xc9W(\xcf/\xcaI\xc9\xa0'
        b'=\x13\x00PK\x01\x02\x14\x03\x14\x00\x00\x00\x08\x00n'
        b'}\x0c=FAKE\x10\x00\x00\x00n\x00\x00\x00\x05'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\x00\x00\x00'
        b'\x00afilePK\x05\x06\x00\x00\x00\x00\x01\x00'
        b'\x01\x003\x00\x00\x003\x00\x00\x00\x00\x00')

@requires_bz2()
klasse Bzip2BadCrcTests(AbstractBadCrcTests, unittest.TestCase):
    compression = zipfile.ZIP_BZIP2
    zip_with_bad_crc = (
        b'PK\x03\x04\x14\x03\x00\x00\x0c\x00nu\x0c=FA'
        b'KE8\x00\x00\x00n\x00\x00\x00\x05\x00\x00\x00af'
        b'ileBZh91AY&SY\xd4\xa8\xca'
        b'\x7f\x00\x00\x0f\x11\x80@\x00\x06D\x90\x80 \x00 \xa5'
        b'P\xd9!\x03\x03\x13\x13\x13\x89\xa9\xa9\xc2u5:\x9f'
        b'\x8b\xb9"\x9c(HjTe?\x80PK\x01\x02\x14'
        b'\x03\x14\x03\x00\x00\x0c\x00nu\x0c=FAKE8'
        b'\x00\x00\x00n\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00 \x80\x80\x81\x00\x00\x00\x00afilePK'
        b'\x05\x06\x00\x00\x00\x00\x01\x00\x01\x003\x00\x00\x00[\x00'
        b'\x00\x00\x00\x00')

@requires_lzma()
klasse LzmaBadCrcTests(AbstractBadCrcTests, unittest.TestCase):
    compression = zipfile.ZIP_LZMA
    zip_with_bad_crc = (
        b'PK\x03\x04\x14\x03\x00\x00\x0e\x00nu\x0c=FA'
        b'KE\x1b\x00\x00\x00n\x00\x00\x00\x05\x00\x00\x00af'
        b'ile\t\x04\x05\x00]\x00\x00\x00\x04\x004\x19I'
        b'\xee\x8d\xe9\x17\x89:3`\tq!.8\x00PK'
        b'\x01\x02\x14\x03\x14\x03\x00\x00\x0e\x00nu\x0c=FA'
        b'KE\x1b\x00\x00\x00n\x00\x00\x00\x05\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00 \x80\x80\x81\x00\x00\x00\x00afil'
        b'ePK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x003\x00\x00'
        b'\x00>\x00\x00\x00\x00\x00')

@requires_zstd()
klasse ZstdBadCrcTests(AbstractBadCrcTests, unittest.TestCase):
    compression = zipfile.ZIP_ZSTANDARD
    zip_with_bad_crc = (
        b'PK\x03\x04?\x00\x00\x00]\x00\x00\x00!\x00V\xb1\x17J\x14\x00'
        b'\x00\x00\x0b\x00\x00\x00\x05\x00\x00\x00afile(\xb5/\xfd\x00'
        b'XY\x00\x00Hello WorldPK\x01\x02?\x03?\x00\x00\x00]\x00\x00\x00'
        b'!\x00V\xb0\x17J\x14\x00\x00\x00\x0b\x00\x00\x00\x05\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\x00\x00\x00\x00afilePK'
        b'\x05\x06\x00\x00\x00\x00\x01\x00\x01\x003\x00\x00\x007\x00\x00\x00'
        b'\x00\x00')

klasse DecryptionTests(unittest.TestCase):
    """Check that ZIP decryption works. Since the library does not
    support encryption at the moment, we use a pre-generated encrypted
    ZIP file."""

    data = (
        b'PK\x03\x04\x14\x00\x01\x00\x00\x00n\x92i.#y\xef?&\x00\x00\x00\x1a\x00'
        b'\x00\x00\x08\x00\x00\x00test.txt\xfa\x10\xa0gly|\xfa-\xc5\xc0=\xf9y'
        b'\x18\xe0\xa8r\xb3Z}Lg\xbc\xae\xf9|\x9b\x19\xe4\x8b\xba\xbb)\x8c\xb0\xdbl'
        b'PK\x01\x02\x14\x00\x14\x00\x01\x00\x00\x00n\x92i.#y\xef?&\x00\x00\x00'
        b'\x1a\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x01\x00 \x00\xb6\x81'
        b'\x00\x00\x00\x00test.txtPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x006\x00'
        b'\x00\x00L\x00\x00\x00\x00\x00' )
    data2 = (
        b'PK\x03\x04\x14\x00\t\x00\x08\x00\xcf}38xu\xaa\xb2\x14\x00\x00\x00\x00\x02'
        b'\x00\x00\x04\x00\x15\x00zeroUT\t\x00\x03\xd6\x8b\x92G\xda\x8b\x92GUx\x04'
        b'\x00\xe8\x03\xe8\x03\xc7<M\xb5a\xceX\xa3Y&\x8b{oE\xd7\x9d\x8c\x98\x02\xc0'
        b'PK\x07\x08xu\xaa\xb2\x14\x00\x00\x00\x00\x02\x00\x00PK\x01\x02\x17\x03'
        b'\x14\x00\t\x00\x08\x00\xcf}38xu\xaa\xb2\x14\x00\x00\x00\x00\x02\x00\x00'
        b'\x04\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa4\x81\x00\x00\x00\x00ze'
        b'roUT\x05\x00\x03\xd6\x8b\x92GUx\x00\x00PK\x05\x06\x00\x00\x00\x00\x01'
        b'\x00\x01\x00?\x00\x00\x00[\x00\x00\x00\x00\x00' )

    plain = b'zipfile.py encryption test'
    plain2 = b'\x00'*512

    def setUp(self):
        mit open(TESTFN, "wb") als fp:
            fp.write(self.data)
        self.zip = zipfile.ZipFile(TESTFN, "r")
        mit open(TESTFN2, "wb") als fp:
            fp.write(self.data2)
        self.zip2 = zipfile.ZipFile(TESTFN2, "r")

    def tearDown(self):
        self.zip.close()
        os.unlink(TESTFN)
        self.zip2.close()
        os.unlink(TESTFN2)

    def test_no_password(self):
        # Reading the encrypted file without password
        # must generate a RunTime exception
        self.assertRaises(RuntimeError, self.zip.read, "test.txt")
        self.assertRaises(RuntimeError, self.zip2.read, "zero")

    def test_bad_password(self):
        self.zip.setpassword(b"perl")
        self.assertRaises(RuntimeError, self.zip.read, "test.txt")
        self.zip2.setpassword(b"perl")
        self.assertRaises(RuntimeError, self.zip2.read, "zero")

    @requires_zlib()
    def test_good_password(self):
        self.zip.setpassword(b"python")
        self.assertEqual(self.zip.read("test.txt"), self.plain)
        self.zip2.setpassword(b"12345")
        self.assertEqual(self.zip2.read("zero"), self.plain2)

    def test_unicode_password(self):
        expected_msg = "pwd: expected bytes, got str"

        mit self.assertRaisesRegex(TypeError, expected_msg):
            self.zip.setpassword("unicode")

        mit self.assertRaisesRegex(TypeError, expected_msg):
            self.zip.read("test.txt", "python")

        mit self.assertRaisesRegex(TypeError, expected_msg):
            self.zip.open("test.txt", pwd="python")

        mit self.assertRaisesRegex(TypeError, expected_msg):
            self.zip.extract("test.txt", pwd="python")

        mit self.assertRaisesRegex(TypeError, expected_msg):
            self.zip.pwd = "python"
            self.zip.open("test.txt")

    def test_seek_tell(self):
        self.zip.setpassword(b"python")
        txt = self.plain
        test_word = b'encryption'
        bloc = txt.find(test_word)
        bloc_len = len(test_word)
        mit self.zip.open("test.txt", "r") als fp:
            fp.seek(bloc, os.SEEK_SET)
            self.assertEqual(fp.tell(), bloc)
            fp.seek(-bloc, os.SEEK_CUR)
            self.assertEqual(fp.tell(), 0)
            fp.seek(bloc, os.SEEK_CUR)
            self.assertEqual(fp.tell(), bloc)
            self.assertEqual(fp.read(bloc_len), txt[bloc:bloc+bloc_len])

            # Make sure that the second read after seeking back beyond
            # _readbuffer returns the same content (ie. rewind to the start of
            # the file to read forward to the required position).
            old_read_size = fp.MIN_READ_SIZE
            fp.MIN_READ_SIZE = 1
            fp._readbuffer = b''
            fp._offset = 0
            fp.seek(0, os.SEEK_SET)
            self.assertEqual(fp.tell(), 0)
            fp.seek(bloc, os.SEEK_CUR)
            self.assertEqual(fp.read(bloc_len), txt[bloc:bloc+bloc_len])
            fp.MIN_READ_SIZE = old_read_size

            fp.seek(0, os.SEEK_END)
            self.assertEqual(fp.tell(), len(txt))
            fp.seek(0, os.SEEK_SET)
            self.assertEqual(fp.tell(), 0)

            # Read the file completely to definitely call any eof integrity
            # checks (crc) und make sure they still pass.
            fp.read()


klasse AbstractTestsWithRandomBinaryFiles:
    @classmethod
    def setUpClass(cls):
        datacount = randint(16, 64)*1024 + randint(1, 1024)
        cls.data = b''.join(struct.pack('<f', random()*randint(-1000, 1000))
                            fuer i in range(datacount))

    def setUp(self):
        # Make a source file mit some lines
        mit open(TESTFN, "wb") als fp:
            fp.write(self.data)

    def tearDown(self):
        unlink(TESTFN)
        unlink(TESTFN2)

    def make_test_archive(self, f, compression):
        # Create the ZIP archive
        mit zipfile.ZipFile(f, "w", compression) als zipfp:
            zipfp.write(TESTFN, "another.name")
            zipfp.write(TESTFN, TESTFN)

    def zip_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            testdata = zipfp.read(TESTFN)
            self.assertEqual(len(testdata), len(self.data))
            self.assertEqual(testdata, self.data)
            self.assertEqual(zipfp.read("another.name"), self.data)

    def test_read(self):
        fuer f in get_files(self):
            self.zip_test(f, self.compression)

    def zip_open_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            zipdata1 = []
            mit zipfp.open(TESTFN) als zipopen1:
                waehrend Wahr:
                    read_data = zipopen1.read(256)
                    wenn nicht read_data:
                        breche
                    zipdata1.append(read_data)

            zipdata2 = []
            mit zipfp.open("another.name") als zipopen2:
                waehrend Wahr:
                    read_data = zipopen2.read(256)
                    wenn nicht read_data:
                        breche
                    zipdata2.append(read_data)

            testdata1 = b''.join(zipdata1)
            self.assertEqual(len(testdata1), len(self.data))
            self.assertEqual(testdata1, self.data)

            testdata2 = b''.join(zipdata2)
            self.assertEqual(len(testdata2), len(self.data))
            self.assertEqual(testdata2, self.data)

    def test_open(self):
        fuer f in get_files(self):
            self.zip_open_test(f, self.compression)

    def zip_random_open_test(self, f, compression):
        self.make_test_archive(f, compression)

        # Read the ZIP archive
        mit zipfile.ZipFile(f, "r", compression) als zipfp:
            zipdata1 = []
            mit zipfp.open(TESTFN) als zipopen1:
                waehrend Wahr:
                    read_data = zipopen1.read(randint(1, 1024))
                    wenn nicht read_data:
                        breche
                    zipdata1.append(read_data)

            testdata = b''.join(zipdata1)
            self.assertEqual(len(testdata), len(self.data))
            self.assertEqual(testdata, self.data)

    def test_random_open(self):
        fuer f in get_files(self):
            self.zip_random_open_test(f, self.compression)


klasse StoredTestsWithRandomBinaryFiles(AbstractTestsWithRandomBinaryFiles,
                                       unittest.TestCase):
    compression = zipfile.ZIP_STORED

@requires_zlib()
klasse DeflateTestsWithRandomBinaryFiles(AbstractTestsWithRandomBinaryFiles,
                                        unittest.TestCase):
    compression = zipfile.ZIP_DEFLATED

@requires_bz2()
klasse Bzip2TestsWithRandomBinaryFiles(AbstractTestsWithRandomBinaryFiles,
                                      unittest.TestCase):
    compression = zipfile.ZIP_BZIP2

@requires_lzma()
klasse LzmaTestsWithRandomBinaryFiles(AbstractTestsWithRandomBinaryFiles,
                                     unittest.TestCase):
    compression = zipfile.ZIP_LZMA

@requires_zstd()
klasse ZstdTestsWithRandomBinaryFiles(AbstractTestsWithRandomBinaryFiles,
                                     unittest.TestCase):
    compression = zipfile.ZIP_ZSTANDARD

# Provide the tell() method but nicht seek()
klasse Tellable:
    def __init__(self, fp):
        self.fp = fp
        self.offset = 0

    def write(self, data):
        n = self.fp.write(data)
        self.offset += n
        gib n

    def tell(self):
        gib self.offset

    def flush(self):
        self.fp.flush()

klasse Unseekable:
    def __init__(self, fp):
        self.fp = fp

    def write(self, data):
        gib self.fp.write(data)

    def flush(self):
        self.fp.flush()

klasse UnseekableTests(unittest.TestCase):
    def test_writestr(self):
        fuer wrapper in (lambda f: f), Tellable, Unseekable:
            mit self.subTest(wrapper=wrapper):
                f = io.BytesIO()
                f.write(b'abc')
                bf = io.BufferedWriter(f)
                mit zipfile.ZipFile(wrapper(bf), 'w', zipfile.ZIP_STORED) als zipfp:
                    zipfp.writestr('ones', b'111')
                    zipfp.writestr('twos', b'222')
                self.assertEqual(f.getvalue()[:5], b'abcPK')
                mit zipfile.ZipFile(f, mode='r') als zipf:
                    mit zipf.open('ones') als zopen:
                        self.assertEqual(zopen.read(), b'111')
                    mit zipf.open('twos') als zopen:
                        self.assertEqual(zopen.read(), b'222')

    def test_write(self):
        fuer wrapper in (lambda f: f), Tellable, Unseekable:
            mit self.subTest(wrapper=wrapper):
                f = io.BytesIO()
                f.write(b'abc')
                bf = io.BufferedWriter(f)
                mit zipfile.ZipFile(wrapper(bf), 'w', zipfile.ZIP_STORED) als zipfp:
                    self.addCleanup(unlink, TESTFN)
                    mit open(TESTFN, 'wb') als f2:
                        f2.write(b'111')
                    zipfp.write(TESTFN, 'ones')
                    mit open(TESTFN, 'wb') als f2:
                        f2.write(b'222')
                    zipfp.write(TESTFN, 'twos')
                self.assertEqual(f.getvalue()[:5], b'abcPK')
                mit zipfile.ZipFile(f, mode='r') als zipf:
                    mit zipf.open('ones') als zopen:
                        self.assertEqual(zopen.read(), b'111')
                    mit zipf.open('twos') als zopen:
                        self.assertEqual(zopen.read(), b'222')

    def test_open_write(self):
        fuer wrapper in (lambda f: f), Tellable, Unseekable:
            mit self.subTest(wrapper=wrapper):
                f = io.BytesIO()
                f.write(b'abc')
                bf = io.BufferedWriter(f)
                mit zipfile.ZipFile(wrapper(bf), 'w', zipfile.ZIP_STORED) als zipf:
                    mit zipf.open('ones', 'w') als zopen:
                        zopen.write(b'111')
                    mit zipf.open('twos', 'w') als zopen:
                        zopen.write(b'222')
                self.assertEqual(f.getvalue()[:5], b'abcPK')
                mit zipfile.ZipFile(f) als zipf:
                    self.assertEqual(zipf.read('ones'), b'111')
                    self.assertEqual(zipf.read('twos'), b'222')


@requires_zlib()
klasse TestsWithMultipleOpens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data1 = b'111' + randbytes(10000)
        cls.data2 = b'222' + randbytes(10000)

    def make_test_archive(self, f):
        # Create the ZIP archive
        mit zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) als zipfp:
            zipfp.writestr('ones', self.data1)
            zipfp.writestr('twos', self.data2)

    def test_same_file(self):
        # Verify that (when the ZipFile is in control of creating file objects)
        # multiple open() calls can be made without interfering mit each other.
        fuer f in get_files(self):
            self.make_test_archive(f)
            mit zipfile.ZipFile(f, mode="r") als zipf:
                mit zipf.open('ones') als zopen1, zipf.open('ones') als zopen2:
                    data1 = zopen1.read(500)
                    data2 = zopen2.read(500)
                    data1 += zopen1.read()
                    data2 += zopen2.read()
                self.assertEqual(data1, data2)
                self.assertEqual(data1, self.data1)

    def test_different_file(self):
        # Verify that (when the ZipFile is in control of creating file objects)
        # multiple open() calls can be made without interfering mit each other.
        fuer f in get_files(self):
            self.make_test_archive(f)
            mit zipfile.ZipFile(f, mode="r") als zipf:
                mit zipf.open('ones') als zopen1, zipf.open('twos') als zopen2:
                    data1 = zopen1.read(500)
                    data2 = zopen2.read(500)
                    data1 += zopen1.read()
                    data2 += zopen2.read()
                self.assertEqual(data1, self.data1)
                self.assertEqual(data2, self.data2)

    def test_interleaved(self):
        # Verify that (when the ZipFile is in control of creating file objects)
        # multiple open() calls can be made without interfering mit each other.
        fuer f in get_files(self):
            self.make_test_archive(f)
            mit zipfile.ZipFile(f, mode="r") als zipf:
                mit zipf.open('ones') als zopen1:
                    data1 = zopen1.read(500)
                    mit zipf.open('twos') als zopen2:
                        data2 = zopen2.read(500)
                        data1 += zopen1.read()
                        data2 += zopen2.read()
                self.assertEqual(data1, self.data1)
                self.assertEqual(data2, self.data2)

    def test_read_after_close(self):
        fuer f in get_files(self):
            self.make_test_archive(f)
            mit contextlib.ExitStack() als stack:
                mit zipfile.ZipFile(f, 'r') als zipf:
                    zopen1 = stack.enter_context(zipf.open('ones'))
                    zopen2 = stack.enter_context(zipf.open('twos'))
                data1 = zopen1.read(500)
                data2 = zopen2.read(500)
                data1 += zopen1.read()
                data2 += zopen2.read()
            self.assertEqual(data1, self.data1)
            self.assertEqual(data2, self.data2)

    def test_read_after_write(self):
        fuer f in get_files(self):
            mit zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED) als zipf:
                zipf.writestr('ones', self.data1)
                zipf.writestr('twos', self.data2)
                mit zipf.open('ones') als zopen1:
                    data1 = zopen1.read(500)
            self.assertEqual(data1, self.data1[:500])
            mit zipfile.ZipFile(f, 'r') als zipf:
                data1 = zipf.read('ones')
                data2 = zipf.read('twos')
            self.assertEqual(data1, self.data1)
            self.assertEqual(data2, self.data2)

    def test_write_after_read(self):
        fuer f in get_files(self):
            mit zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) als zipf:
                zipf.writestr('ones', self.data1)
                mit zipf.open('ones') als zopen1:
                    zopen1.read(500)
                    zipf.writestr('twos', self.data2)
            mit zipfile.ZipFile(f, 'r') als zipf:
                data1 = zipf.read('ones')
                data2 = zipf.read('twos')
            self.assertEqual(data1, self.data1)
            self.assertEqual(data2, self.data2)

    def test_many_opens(self):
        # Verify that read() und open() promptly close the file descriptor,
        # und don't rely on the garbage collector to free resources.
        startcount = fd_count()
        self.make_test_archive(TESTFN2)
        mit zipfile.ZipFile(TESTFN2, mode="r") als zipf:
            fuer x in range(100):
                zipf.read('ones')
                mit zipf.open('ones') als zopen1:
                    pass
        self.assertEqual(startcount, fd_count())

    def test_write_while_reading(self):
        mit zipfile.ZipFile(TESTFN2, 'w', zipfile.ZIP_DEFLATED) als zipf:
            zipf.writestr('ones', self.data1)
        mit zipfile.ZipFile(TESTFN2, 'a', zipfile.ZIP_DEFLATED) als zipf:
            mit zipf.open('ones', 'r') als r1:
                data1 = r1.read(500)
                mit zipf.open('twos', 'w') als w1:
                    w1.write(self.data2)
                data1 += r1.read()
        self.assertEqual(data1, self.data1)
        mit zipfile.ZipFile(TESTFN2) als zipf:
            self.assertEqual(zipf.read('twos'), self.data2)

    def tearDown(self):
        unlink(TESTFN2)


klasse TestWithDirectory(unittest.TestCase):
    def setUp(self):
        os.mkdir(TESTFN2)

    def test_extract_dir(self):
        mit zipfile.ZipFile(findfile("zipdir.zip", subdir="archivetestdata")) als zipf:
            zipf.extractall(TESTFN2)
        self.assertWahr(os.path.isdir(os.path.join(TESTFN2, "a")))
        self.assertWahr(os.path.isdir(os.path.join(TESTFN2, "a", "b")))
        self.assertWahr(os.path.exists(os.path.join(TESTFN2, "a", "b", "c")))

    def test_bug_6050(self):
        # Extraction should succeed wenn directories already exist
        os.mkdir(os.path.join(TESTFN2, "a"))
        self.test_extract_dir()

    def test_extract_dir_backslash(self):
        zfname = findfile("zipdir_backslash.zip", subdir="archivetestdata")
        mit zipfile.ZipFile(zfname) als zipf:
            zipf.extractall(TESTFN2)
        wenn os.name == 'nt':
            self.assertWahr(os.path.isdir(os.path.join(TESTFN2, "a")))
            self.assertWahr(os.path.isdir(os.path.join(TESTFN2, "a", "b")))
            self.assertWahr(os.path.isfile(os.path.join(TESTFN2, "a", "b", "c")))
            self.assertWahr(os.path.isdir(os.path.join(TESTFN2, "d")))
            self.assertWahr(os.path.isdir(os.path.join(TESTFN2, "d", "e")))
        sonst:
            self.assertWahr(os.path.isfile(os.path.join(TESTFN2, "a\\b\\c")))
            self.assertWahr(os.path.isfile(os.path.join(TESTFN2, "d\\e\\")))
            self.assertFalsch(os.path.exists(os.path.join(TESTFN2, "a")))
            self.assertFalsch(os.path.exists(os.path.join(TESTFN2, "d")))

    def test_write_dir(self):
        dirpath = os.path.join(TESTFN2, "x")
        os.mkdir(dirpath)
        mode = os.stat(dirpath).st_mode & 0xFFFF
        mit zipfile.ZipFile(TESTFN, "w") als zipf:
            zipf.write(dirpath)
            zinfo = zipf.filelist[0]
            self.assertEndsWith(zinfo.filename, "/x/")
            self.assertEqual(zinfo.external_attr, (mode << 16) | 0x10)
            zipf.write(dirpath, "y")
            zinfo = zipf.filelist[1]
            self.assertWahr(zinfo.filename, "y/")
            self.assertEqual(zinfo.external_attr, (mode << 16) | 0x10)
        mit zipfile.ZipFile(TESTFN, "r") als zipf:
            zinfo = zipf.filelist[0]
            self.assertEndsWith(zinfo.filename, "/x/")
            self.assertEqual(zinfo.external_attr, (mode << 16) | 0x10)
            zinfo = zipf.filelist[1]
            self.assertWahr(zinfo.filename, "y/")
            self.assertEqual(zinfo.external_attr, (mode << 16) | 0x10)
            target = os.path.join(TESTFN2, "target")
            os.mkdir(target)
            zipf.extractall(target)
            self.assertWahr(os.path.isdir(os.path.join(target, "y")))
            self.assertEqual(len(os.listdir(target)), 2)

    def test_writestr_dir(self):
        os.mkdir(os.path.join(TESTFN2, "x"))
        mit zipfile.ZipFile(TESTFN, "w") als zipf:
            zipf.writestr("x/", b'')
            zinfo = zipf.filelist[0]
            self.assertEqual(zinfo.filename, "x/")
            self.assertEqual(zinfo.external_attr, (0o40775 << 16) | 0x10)
        mit zipfile.ZipFile(TESTFN, "r") als zipf:
            zinfo = zipf.filelist[0]
            self.assertEndsWith(zinfo.filename, "x/")
            self.assertEqual(zinfo.external_attr, (0o40775 << 16) | 0x10)
            target = os.path.join(TESTFN2, "target")
            os.mkdir(target)
            zipf.extractall(target)
            self.assertWahr(os.path.isdir(os.path.join(target, "x")))
            self.assertEqual(os.listdir(target), ["x"])

    def test_mkdir(self):
        mit zipfile.ZipFile(TESTFN, "w") als zf:
            zf.mkdir("directory")
            zinfo = zf.filelist[0]
            self.assertEqual(zinfo.filename, "directory/")
            self.assertEqual(zinfo.external_attr, (0o40777 << 16) | 0x10)

            zf.mkdir("directory2/")
            zinfo = zf.filelist[1]
            self.assertEqual(zinfo.filename, "directory2/")
            self.assertEqual(zinfo.external_attr, (0o40777 << 16) | 0x10)

            zf.mkdir("directory3", mode=0o777)
            zinfo = zf.filelist[2]
            self.assertEqual(zinfo.filename, "directory3/")
            self.assertEqual(zinfo.external_attr, (0o40777 << 16) | 0x10)

            old_zinfo = zipfile.ZipInfo("directory4/")
            old_zinfo.external_attr = (0o40777 << 16) | 0x10
            old_zinfo.CRC = 0
            old_zinfo.file_size = 0
            old_zinfo.compress_size = 0
            zf.mkdir(old_zinfo)
            new_zinfo = zf.filelist[3]
            self.assertEqual(old_zinfo.filename, "directory4/")
            self.assertEqual(old_zinfo.external_attr, new_zinfo.external_attr)

            target = os.path.join(TESTFN2, "target")
            os.mkdir(target)
            zf.extractall(target)
            self.assertEqual(set(os.listdir(target)), {"directory", "directory2", "directory3", "directory4"})

    def test_create_directory_with_write(self):
        mit zipfile.ZipFile(TESTFN, "w") als zf:
            zf.writestr(zipfile.ZipInfo('directory/'), '')

            zinfo = zf.filelist[0]
            self.assertEqual(zinfo.filename, "directory/")

            directory = os.path.join(TESTFN2, "directory2")
            os.mkdir(directory)
            mode = os.stat(directory).st_mode & 0xFFFF
            zf.write(directory, arcname="directory2/")
            zinfo = zf.filelist[1]
            self.assertEqual(zinfo.filename, "directory2/")
            self.assertEqual(zinfo.external_attr, (mode << 16) | 0x10)

            target = os.path.join(TESTFN2, "target")
            os.mkdir(target)
            zf.extractall(target)

            self.assertEqual(set(os.listdir(target)), {"directory", "directory2"})

    def test_root_folder_in_zipfile(self):
        """
        gh-112795: Some tools oder self constructed codes will add '/' folder to
        the zip file, this is a strange behavior, but we should support it.
        """
        in_memory_file = io.BytesIO()
        zf = zipfile.ZipFile(in_memory_file, "w")
        zf.mkdir('/')
        zf.writestr('./a.txt', 'aaa')
        zf.extractall(TESTFN2)

    def tearDown(self):
        rmtree(TESTFN2)
        wenn os.path.exists(TESTFN):
            unlink(TESTFN)


klasse ZipInfoTests(unittest.TestCase):
    def test_from_file(self):
        zi = zipfile.ZipInfo.from_file(__file__)
        self.assertEqual(posixpath.basename(zi.filename), 'test_core.py')
        self.assertFalsch(zi.is_dir())
        self.assertEqual(zi.file_size, os.path.getsize(__file__))

    def test_from_file_pathlike(self):
        zi = zipfile.ZipInfo.from_file(FakePath(__file__))
        self.assertEqual(posixpath.basename(zi.filename), 'test_core.py')
        self.assertFalsch(zi.is_dir())
        self.assertEqual(zi.file_size, os.path.getsize(__file__))

    def test_from_file_bytes(self):
        zi = zipfile.ZipInfo.from_file(os.fsencode(__file__), 'test')
        self.assertEqual(posixpath.basename(zi.filename), 'test')
        self.assertFalsch(zi.is_dir())
        self.assertEqual(zi.file_size, os.path.getsize(__file__))

    def test_from_file_fileno(self):
        mit open(__file__, 'rb') als f:
            zi = zipfile.ZipInfo.from_file(f.fileno(), 'test')
            self.assertEqual(posixpath.basename(zi.filename), 'test')
            self.assertFalsch(zi.is_dir())
            self.assertEqual(zi.file_size, os.path.getsize(__file__))

    def test_from_dir(self):
        dirpath = os.path.dirname(os.path.abspath(__file__))
        zi = zipfile.ZipInfo.from_file(dirpath, 'stdlib_tests')
        self.assertEqual(zi.filename, 'stdlib_tests/')
        self.assertWahr(zi.is_dir())
        self.assertEqual(zi.compress_type, zipfile.ZIP_STORED)
        self.assertEqual(zi.file_size, 0)

    def test_compresslevel_property(self):
        zinfo = zipfile.ZipInfo("xxx")
        self.assertFalsch(zinfo._compresslevel)
        self.assertFalsch(zinfo.compress_level)
        zinfo._compresslevel = 99  # test the legacy @property.setter
        self.assertEqual(zinfo.compress_level, 99)
        self.assertEqual(zinfo._compresslevel, 99)
        zinfo.compress_level = 8
        self.assertEqual(zinfo.compress_level, 8)
        self.assertEqual(zinfo._compresslevel, 8)


klasse CommandLineTest(unittest.TestCase):

    def zipfilecmd(self, *args, **kwargs):
        rc, out, err = script_helper.assert_python_ok('-m', 'zipfile', *args,
                                                      **kwargs)
        gib out.replace(os.linesep.encode(), b'\n')

    def zipfilecmd_failure(self, *args):
        gib script_helper.assert_python_failure('-m', 'zipfile', *args)

    def test_bad_use(self):
        rc, out, err = self.zipfilecmd_failure()
        self.assertEqual(out, b'')
        self.assertIn(b'usage', err.lower())
        self.assertIn(b'error', err.lower())
        self.assertIn(b'required', err.lower())
        rc, out, err = self.zipfilecmd_failure('-l', '')
        self.assertEqual(out, b'')
        self.assertNotEqual(err.strip(), b'')

    def test_test_command(self):
        zip_name = findfile('zipdir.zip', subdir='archivetestdata')
        fuer opt in '-t', '--test':
            out = self.zipfilecmd(opt, zip_name)
            self.assertEqual(out.rstrip(), b'Done testing')
        zip_name = findfile('testtar.tar')
        rc, out, err = self.zipfilecmd_failure('-t', zip_name)
        self.assertEqual(out, b'')

    def test_list_command(self):
        zip_name = findfile('zipdir.zip', subdir='archivetestdata')
        t = io.StringIO()
        mit zipfile.ZipFile(zip_name, 'r') als tf:
            tf.printdir(t)
        expected = t.getvalue().encode('ascii', 'backslashreplace')
        fuer opt in '-l', '--list':
            out = self.zipfilecmd(opt, zip_name,
                                  PYTHONIOENCODING='ascii:backslashreplace')
            self.assertEqual(out, expected)

    @requires_zlib()
    def test_create_command(self):
        self.addCleanup(unlink, TESTFN)
        mit open(TESTFN, 'w', encoding='utf-8') als f:
            f.write('test 1')
        os.mkdir(TESTFNDIR)
        self.addCleanup(rmtree, TESTFNDIR)
        mit open(os.path.join(TESTFNDIR, 'file.txt'), 'w', encoding='utf-8') als f:
            f.write('test 2')
        files = [TESTFN, TESTFNDIR]
        namelist = [TESTFN, TESTFNDIR + '/', TESTFNDIR + '/file.txt']
        fuer opt in '-c', '--create':
            versuch:
                out = self.zipfilecmd(opt, TESTFN2, *files)
                self.assertEqual(out, b'')
                mit zipfile.ZipFile(TESTFN2) als zf:
                    self.assertEqual(zf.namelist(), namelist)
                    self.assertEqual(zf.read(namelist[0]), b'test 1')
                    self.assertEqual(zf.read(namelist[2]), b'test 2')
            schliesslich:
                unlink(TESTFN2)

    def test_extract_command(self):
        zip_name = findfile('zipdir.zip', subdir='archivetestdata')
        fuer opt in '-e', '--extract':
            mit temp_dir() als extdir:
                out = self.zipfilecmd(opt, zip_name, extdir)
                self.assertEqual(out, b'')
                mit zipfile.ZipFile(zip_name) als zf:
                    fuer zi in zf.infolist():
                        path = os.path.join(extdir,
                                    zi.filename.replace('/', os.sep))
                        wenn zi.is_dir():
                            self.assertWahr(os.path.isdir(path))
                        sonst:
                            self.assertWahr(os.path.isfile(path))
                            mit open(path, 'rb') als f:
                                self.assertEqual(f.read(), zf.read(zi))


klasse TestExecutablePrependedZip(unittest.TestCase):
    """Test our ability to open zip files mit an executable prepended."""

    def setUp(self):
        self.exe_zip = findfile('exe_with_zip', subdir='archivetestdata')
        self.exe_zip64 = findfile('exe_with_z64', subdir='archivetestdata')

    def _test_zip_works(self, name):
        # bpo28494 sanity check: ensure is_zipfile works on these.
        self.assertWahr(zipfile.is_zipfile(name),
                        f'is_zipfile failed on {name}')
        # Ensure we can operate on these via ZipFile.
        mit zipfile.ZipFile(name) als zipfp:
            fuer n in zipfp.namelist():
                data = zipfp.read(n)
                self.assertIn(b'FAVORITE_NUMBER', data)

    def test_read_zip_with_exe_prepended(self):
        self._test_zip_works(self.exe_zip)

    def test_read_zip64_with_exe_prepended(self):
        self._test_zip_works(self.exe_zip64)

    @unittest.skipUnless(sys.executable, 'sys.executable required.')
    @unittest.skipUnless(os.access('/bin/bash', os.X_OK),
                         'Test relies on #!/bin/bash working.')
    @requires_subprocess()
    def test_execute_zip2(self):
        output = subprocess.check_output([self.exe_zip, sys.executable])
        self.assertIn(b'number in executable: 5', output)

    @unittest.skipUnless(sys.executable, 'sys.executable required.')
    @unittest.skipUnless(os.access('/bin/bash', os.X_OK),
                         'Test relies on #!/bin/bash working.')
    @requires_subprocess()
    def test_execute_zip64(self):
        output = subprocess.check_output([self.exe_zip64, sys.executable])
        self.assertIn(b'number in executable: 5', output)


klasse EncodedMetadataTests(unittest.TestCase):
    file_names = ['\u4e00', '\u4e8c', '\u4e09']  # Han 'one', 'two', 'three'
    file_content = [
        "This is pure ASCII.\n".encode('ascii'),
        # This is modern Japanese. (UTF-8)
        "\u3053\u308c\u306f\u73fe\u4ee3\u7684\u65e5\u672c\u8a9e\u3067\u3059\u3002\n".encode('utf-8'),
        # This is obsolete Japanese. (Shift JIS)
        "\u3053\u308c\u306f\u53e4\u3044\u65e5\u672c\u8a9e\u3067\u3059\u3002\n".encode('shift_jis'),
    ]

    def setUp(self):
        self.addCleanup(unlink, TESTFN)
        # Create .zip of 3 members mit Han names encoded in Shift JIS.
        # Each name is 1 Han character encoding to 2 bytes in Shift JIS.
        # The ASCII names are arbitrary als long als they are length 2 und
        # nicht otherwise contained in the zip file.
        # Data elements are encoded bytes (ascii, utf-8, shift_jis).
        placeholders = ["n1", "n2"] + self.file_names[2:]
        mit zipfile.ZipFile(TESTFN, mode="w") als tf:
            fuer temp, content in zip(placeholders, self.file_content):
                tf.writestr(temp, content, zipfile.ZIP_STORED)
        # Hack in the Shift JIS names mit flag bit 11 (UTF-8) unset.
        mit open(TESTFN, "rb") als tf:
            data = tf.read()
        fuer name, temp in zip(self.file_names, placeholders[:2]):
            data = data.replace(temp.encode('ascii'),
                                name.encode('shift_jis'))
        mit open(TESTFN, "wb") als tf:
            tf.write(data)

    def _test_read(self, zipfp, expected_names, expected_content):
        # Check the namelist
        names = zipfp.namelist()
        self.assertEqual(sorted(names), sorted(expected_names))

        # Check infolist
        infos = zipfp.infolist()
        names = [zi.filename fuer zi in infos]
        self.assertEqual(sorted(names), sorted(expected_names))

        # check getinfo
        fuer name, content in zip(expected_names, expected_content):
            info = zipfp.getinfo(name)
            self.assertEqual(info.filename, name)
            self.assertEqual(info.file_size, len(content))
            self.assertEqual(zipfp.read(name), content)

    def test_read_with_metadata_encoding(self):
        # Read the ZIP archive mit correct metadata_encoding
        mit zipfile.ZipFile(TESTFN, "r", metadata_encoding='shift_jis') als zipfp:
            self._test_read(zipfp, self.file_names, self.file_content)

    def test_read_without_metadata_encoding(self):
        # Read the ZIP archive without metadata_encoding
        expected_names = [name.encode('shift_jis').decode('cp437')
                          fuer name in self.file_names[:2]] + self.file_names[2:]
        mit zipfile.ZipFile(TESTFN, "r") als zipfp:
            self._test_read(zipfp, expected_names, self.file_content)

    def test_read_with_incorrect_metadata_encoding(self):
        # Read the ZIP archive mit incorrect metadata_encoding
        expected_names = [name.encode('shift_jis').decode('koi8-u')
                          fuer name in self.file_names[:2]] + self.file_names[2:]
        mit zipfile.ZipFile(TESTFN, "r", metadata_encoding='koi8-u') als zipfp:
            self._test_read(zipfp, expected_names, self.file_content)

    def test_read_with_unsuitable_metadata_encoding(self):
        # Read the ZIP archive mit metadata_encoding unsuitable for
        # decoding metadata
        mit self.assertRaises(UnicodeDecodeError):
            zipfile.ZipFile(TESTFN, "r", metadata_encoding='ascii')
        mit self.assertRaises(UnicodeDecodeError):
            zipfile.ZipFile(TESTFN, "r", metadata_encoding='utf-8')

    def test_read_after_append(self):
        newname = '\u56db'  # Han 'four'
        expected_names = [name.encode('shift_jis').decode('cp437')
                          fuer name in self.file_names[:2]] + self.file_names[2:]
        expected_names.append(newname)
        expected_content = (*self.file_content, b"newcontent")

        mit zipfile.ZipFile(TESTFN, "a") als zipfp:
            zipfp.writestr(newname, "newcontent")
            self.assertEqual(sorted(zipfp.namelist()), sorted(expected_names))

        mit zipfile.ZipFile(TESTFN, "r") als zipfp:
            self._test_read(zipfp, expected_names, expected_content)

        mit zipfile.ZipFile(TESTFN, "r", metadata_encoding='shift_jis') als zipfp:
            self.assertEqual(sorted(zipfp.namelist()), sorted(expected_names))
            fuer i, (name, content) in enumerate(zip(expected_names, expected_content)):
                info = zipfp.getinfo(name)
                self.assertEqual(info.filename, name)
                self.assertEqual(info.file_size, len(content))
                wenn i < 2:
                    mit self.assertRaises(zipfile.BadZipFile):
                        zipfp.read(name)
                sonst:
                    self.assertEqual(zipfp.read(name), content)

    def test_write_with_metadata_encoding(self):
        ZF = zipfile.ZipFile
        fuer mode in ("w", "x", "a"):
            mit self.assertRaisesRegex(ValueError,
                                        "^metadata_encoding is only"):
                ZF("nonesuch.zip", mode, metadata_encoding="shift_jis")

    def test_cli_with_metadata_encoding(self):
        errmsg = "Non-conforming encodings nicht supported mit -c."
        args = ["--metadata-encoding=shift_jis", "-c", "nonesuch", "nonesuch"]
        mit captured_stdout() als stdout:
            mit captured_stderr() als stderr:
                self.assertRaises(SystemExit, zipfile.main, args)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn(errmsg, stderr.getvalue())

        mit captured_stdout() als stdout:
            zipfile.main(["--metadata-encoding=shift_jis", "-t", TESTFN])
        listing = stdout.getvalue()

        mit captured_stdout() als stdout:
            zipfile.main(["--metadata-encoding=shift_jis", "-l", TESTFN])
        listing = stdout.getvalue()
        fuer name in self.file_names:
            self.assertIn(name, listing)

    def test_cli_with_metadata_encoding_extract(self):
        os.mkdir(TESTFN2)
        self.addCleanup(rmtree, TESTFN2)
        # Depending on locale, extracted file names can be nicht encodable
        # mit the filesystem encoding.
        fuer fn in self.file_names:
            versuch:
                os.stat(os.path.join(TESTFN2, fn))
            ausser OSError:
                pass
            ausser UnicodeEncodeError:
                self.skipTest(f'cannot encode file name {fn!a}')

        zipfile.main(["--metadata-encoding=shift_jis", "-e", TESTFN, TESTFN2])
        listing = os.listdir(TESTFN2)
        fuer name in self.file_names:
            self.assertIn(name, listing)


klasse StripExtraTests(unittest.TestCase):
    # Note: all of the "z" characters are technically invalid, but up
    # to 3 bytes at the end of the extra will be passed through als they
    # are too short to encode a valid extra.

    ZIP64_EXTRA = 1

    def test_no_data(self):
        s = struct.Struct("<HH")
        a = s.pack(self.ZIP64_EXTRA, 0)
        b = s.pack(2, 0)
        c = s.pack(3, 0)

        self.assertEqual(b'', zipfile._Extra.strip(a, (self.ZIP64_EXTRA,)))
        self.assertEqual(b, zipfile._Extra.strip(b, (self.ZIP64_EXTRA,)))
        self.assertEqual(
            b+b"z", zipfile._Extra.strip(b+b"z", (self.ZIP64_EXTRA,)))

        self.assertEqual(b+c, zipfile._Extra.strip(a+b+c, (self.ZIP64_EXTRA,)))
        self.assertEqual(b+c, zipfile._Extra.strip(b+a+c, (self.ZIP64_EXTRA,)))
        self.assertEqual(b+c, zipfile._Extra.strip(b+c+a, (self.ZIP64_EXTRA,)))

    def test_with_data(self):
        s = struct.Struct("<HH")
        a = s.pack(self.ZIP64_EXTRA, 1) + b"a"
        b = s.pack(2, 2) + b"bb"
        c = s.pack(3, 3) + b"ccc"

        self.assertEqual(b"", zipfile._Extra.strip(a, (self.ZIP64_EXTRA,)))
        self.assertEqual(b, zipfile._Extra.strip(b, (self.ZIP64_EXTRA,)))
        self.assertEqual(
            b+b"z", zipfile._Extra.strip(b+b"z", (self.ZIP64_EXTRA,)))

        self.assertEqual(b+c, zipfile._Extra.strip(a+b+c, (self.ZIP64_EXTRA,)))
        self.assertEqual(b+c, zipfile._Extra.strip(b+a+c, (self.ZIP64_EXTRA,)))
        self.assertEqual(b+c, zipfile._Extra.strip(b+c+a, (self.ZIP64_EXTRA,)))

    def test_multiples(self):
        s = struct.Struct("<HH")
        a = s.pack(self.ZIP64_EXTRA, 1) + b"a"
        b = s.pack(2, 2) + b"bb"

        self.assertEqual(b"", zipfile._Extra.strip(a+a, (self.ZIP64_EXTRA,)))
        self.assertEqual(b"", zipfile._Extra.strip(a+a+a, (self.ZIP64_EXTRA,)))
        self.assertEqual(
            b"z", zipfile._Extra.strip(a+a+b"z", (self.ZIP64_EXTRA,)))
        self.assertEqual(
            b+b"z", zipfile._Extra.strip(a+a+b+b"z", (self.ZIP64_EXTRA,)))

        self.assertEqual(b, zipfile._Extra.strip(a+a+b, (self.ZIP64_EXTRA,)))
        self.assertEqual(b, zipfile._Extra.strip(a+b+a, (self.ZIP64_EXTRA,)))
        self.assertEqual(b, zipfile._Extra.strip(b+a+a, (self.ZIP64_EXTRA,)))

    def test_too_short(self):
        self.assertEqual(b"", zipfile._Extra.strip(b"", (self.ZIP64_EXTRA,)))
        self.assertEqual(b"z", zipfile._Extra.strip(b"z", (self.ZIP64_EXTRA,)))
        self.assertEqual(
            b"zz", zipfile._Extra.strip(b"zz", (self.ZIP64_EXTRA,)))
        self.assertEqual(
            b"zzz", zipfile._Extra.strip(b"zzz", (self.ZIP64_EXTRA,)))


klasse StatIO(_pyio.BytesIO):
    """Buffer which remembers the number of bytes that were read."""

    def __init__(self):
        super().__init__()
        self.bytes_read = 0

    def read(self, size=-1):
        bs = super().read(size)
        self.bytes_read += len(bs)
        gib bs


klasse StoredZipExtFileRandomReadTest(unittest.TestCase):
    """Tests whether an uncompressed, unencrypted zip entry can be randomly
    seek und read without reading redundant bytes."""
    def test_stored_seek_and_read(self):

        sio = StatIO()
        # 20000 bytes
        txt = b'0123456789' * 2000

        # The seek length must be greater than ZipExtFile.MIN_READ_SIZE
        # als `ZipExtFile._read2()` reads in blocks of this size und we
        # need to seek out of the buffered data
        read_buffer_size = zipfile.ZipExtFile.MIN_READ_SIZE
        self.assertGreaterEqual(10002, read_buffer_size)  # fuer forward seek test
        self.assertGreaterEqual(5003, read_buffer_size)  # fuer backward seek test
        # The read length must be less than MIN_READ_SIZE, since we assume that
        # only 1 block is read in the test.
        read_length = 100
        self.assertGreaterEqual(read_buffer_size, read_length)  # fuer read() calls

        mit zipfile.ZipFile(sio, "w", compression=zipfile.ZIP_STORED) als zipf:
            zipf.writestr("foo.txt", txt)

        # check random seek und read on a file
        mit zipfile.ZipFile(sio, "r") als zipf:
            mit zipf.open("foo.txt", "r") als fp:
                # Test this optimized read hasn't rewound und read von the
                # start of the file (as in the case of the unoptimized path)

                # forward seek
                old_count = sio.bytes_read
                forward_seek_len = 10002
                current_pos = 0
                fp.seek(forward_seek_len, os.SEEK_CUR)
                current_pos += forward_seek_len
                self.assertEqual(fp.tell(), current_pos)
                self.assertEqual(fp._left, fp._compress_left)
                arr = fp.read(read_length)
                current_pos += read_length
                self.assertEqual(fp.tell(), current_pos)
                self.assertEqual(arr, txt[current_pos - read_length:current_pos])
                self.assertEqual(fp._left, fp._compress_left)
                read_count = sio.bytes_read - old_count
                self.assertLessEqual(read_count, read_buffer_size)

                # backward seek
                old_count = sio.bytes_read
                backward_seek_len = 5003
                fp.seek(-backward_seek_len, os.SEEK_CUR)
                current_pos -= backward_seek_len
                self.assertEqual(fp.tell(), current_pos)
                self.assertEqual(fp._left, fp._compress_left)
                arr = fp.read(read_length)
                current_pos += read_length
                self.assertEqual(fp.tell(), current_pos)
                self.assertEqual(arr, txt[current_pos - read_length:current_pos])
                self.assertEqual(fp._left, fp._compress_left)
                read_count = sio.bytes_read - old_count
                self.assertLessEqual(read_count, read_buffer_size)

                # eof flags test
                fp.seek(0, os.SEEK_END)
                fp.seek(12345, os.SEEK_SET)
                current_pos = 12345
                arr = fp.read(read_length)
                current_pos += read_length
                self.assertEqual(arr, txt[current_pos - read_length:current_pos])


wenn __name__ == "__main__":
    unittest.main()
