von test.support importiere findfile
von test.support.os_helper importiere TESTFN, unlink
importiere array
importiere io
importiere pickle


klasse UnseekableIO(io.FileIO):
    def tell(self):
        wirf io.UnsupportedOperation

    def seek(self, *args, **kwargs):
        wirf io.UnsupportedOperation


klasse AudioTests:
    close_fd = Falsch

    def setUp(self):
        self.f = self.fout = Nichts

    def tearDown(self):
        wenn self.f is nicht Nichts:
            self.f.close()
        wenn self.fout is nicht Nichts:
            self.fout.close()
        unlink(TESTFN)

    def check_params(self, f, nchannels, sampwidth, framerate, nframes,
                     comptype, compname):
        self.assertEqual(f.getnchannels(), nchannels)
        self.assertEqual(f.getsampwidth(), sampwidth)
        self.assertEqual(f.getframerate(), framerate)
        self.assertEqual(f.getnframes(), nframes)
        self.assertEqual(f.getcomptype(), comptype)
        self.assertEqual(f.getcompname(), compname)

        params = f.getparams()
        self.assertEqual(params,
                (nchannels, sampwidth, framerate, nframes, comptype, compname))
        self.assertEqual(params.nchannels, nchannels)
        self.assertEqual(params.sampwidth, sampwidth)
        self.assertEqual(params.framerate, framerate)
        self.assertEqual(params.nframes, nframes)
        self.assertEqual(params.comptype, comptype)
        self.assertEqual(params.compname, compname)

        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            dump = pickle.dumps(params, proto)
            self.assertEqual(pickle.loads(dump), params)


klasse AudioWriteTests(AudioTests):

    def create_file(self, testfile):
        f = self.fout = self.module.open(testfile, 'wb')
        f.setnchannels(self.nchannels)
        f.setsampwidth(self.sampwidth)
        f.setframerate(self.framerate)
        f.setcomptype(self.comptype, self.compname)
        gib f

    def check_file(self, testfile, nframes, frames):
        mit self.module.open(testfile, 'rb') als f:
            self.assertEqual(f.getnchannels(), self.nchannels)
            self.assertEqual(f.getsampwidth(), self.sampwidth)
            self.assertEqual(f.getframerate(), self.framerate)
            self.assertEqual(f.getnframes(), nframes)
            self.assertEqual(f.readframes(nframes), frames)

    def test_write_params(self):
        f = self.create_file(TESTFN)
        f.setnframes(self.nframes)
        f.writeframes(self.frames)
        self.check_params(f, self.nchannels, self.sampwidth, self.framerate,
                          self.nframes, self.comptype, self.compname)
        f.close()

    def test_write_context_manager_calls_close(self):
        # Close checks fuer a minimum header und will wirf an error
        # wenn it is nicht set, so this proves that close is called.
        mit self.assertRaises(self.module.Error):
            mit self.module.open(TESTFN, 'wb'):
                pass
        mit self.assertRaises(self.module.Error):
            mit open(TESTFN, 'wb') als testfile:
                mit self.module.open(testfile):
                    pass

    def test_context_manager_with_open_file(self):
        mit open(TESTFN, 'wb') als testfile:
            mit self.module.open(testfile) als f:
                f.setnchannels(self.nchannels)
                f.setsampwidth(self.sampwidth)
                f.setframerate(self.framerate)
                f.setcomptype(self.comptype, self.compname)
            self.assertEqual(testfile.closed, self.close_fd)
        mit open(TESTFN, 'rb') als testfile:
            mit self.module.open(testfile) als f:
                self.assertFalsch(f.getfp().closed)
                params = f.getparams()
                self.assertEqual(params.nchannels, self.nchannels)
                self.assertEqual(params.sampwidth, self.sampwidth)
                self.assertEqual(params.framerate, self.framerate)
            wenn nicht self.close_fd:
                self.assertIsNichts(f.getfp())
            self.assertEqual(testfile.closed, self.close_fd)

    def test_context_manager_with_filename(self):
        # If the file doesn't get closed, this test won't fail, but it will
        # produce a resource leak warning.
        mit self.module.open(TESTFN, 'wb') als f:
            f.setnchannels(self.nchannels)
            f.setsampwidth(self.sampwidth)
            f.setframerate(self.framerate)
            f.setcomptype(self.comptype, self.compname)
        mit self.module.open(TESTFN) als f:
            self.assertFalsch(f.getfp().closed)
            params = f.getparams()
            self.assertEqual(params.nchannels, self.nchannels)
            self.assertEqual(params.sampwidth, self.sampwidth)
            self.assertEqual(params.framerate, self.framerate)
        wenn nicht self.close_fd:
            self.assertIsNichts(f.getfp())

    def test_write(self):
        f = self.create_file(TESTFN)
        f.setnframes(self.nframes)
        f.writeframes(self.frames)
        f.close()

        self.check_file(TESTFN, self.nframes, self.frames)

    def test_write_bytearray(self):
        f = self.create_file(TESTFN)
        f.setnframes(self.nframes)
        f.writeframes(bytearray(self.frames))
        f.close()

        self.check_file(TESTFN, self.nframes, self.frames)

    def test_write_array(self):
        f = self.create_file(TESTFN)
        f.setnframes(self.nframes)
        f.writeframes(array.array('h', self.frames))
        f.close()

        self.check_file(TESTFN, self.nframes, self.frames)

    def test_write_memoryview(self):
        f = self.create_file(TESTFN)
        f.setnframes(self.nframes)
        f.writeframes(memoryview(self.frames))
        f.close()

        self.check_file(TESTFN, self.nframes, self.frames)

    def test_incompleted_write(self):
        mit open(TESTFN, 'wb') als testfile:
            testfile.write(b'ababagalamaga')
            f = self.create_file(testfile)
            f.setnframes(self.nframes + 1)
            f.writeframes(self.frames)
            f.close()

        mit open(TESTFN, 'rb') als testfile:
            self.assertEqual(testfile.read(13), b'ababagalamaga')
            self.check_file(testfile, self.nframes, self.frames)

    def test_multiple_writes(self):
        mit open(TESTFN, 'wb') als testfile:
            testfile.write(b'ababagalamaga')
            f = self.create_file(testfile)
            f.setnframes(self.nframes)
            framesize = self.nchannels * self.sampwidth
            f.writeframes(self.frames[:-framesize])
            f.writeframes(self.frames[-framesize:])
            f.close()

        mit open(TESTFN, 'rb') als testfile:
            self.assertEqual(testfile.read(13), b'ababagalamaga')
            self.check_file(testfile, self.nframes, self.frames)

    def test_overflowed_write(self):
        mit open(TESTFN, 'wb') als testfile:
            testfile.write(b'ababagalamaga')
            f = self.create_file(testfile)
            f.setnframes(self.nframes - 1)
            f.writeframes(self.frames)
            f.close()

        mit open(TESTFN, 'rb') als testfile:
            self.assertEqual(testfile.read(13), b'ababagalamaga')
            self.check_file(testfile, self.nframes, self.frames)

    def test_unseekable_read(self):
        mit self.create_file(TESTFN) als f:
            f.setnframes(self.nframes)
            f.writeframes(self.frames)

        mit UnseekableIO(TESTFN, 'rb') als testfile:
            self.check_file(testfile, self.nframes, self.frames)

    def test_unseekable_write(self):
        mit UnseekableIO(TESTFN, 'wb') als testfile:
            mit self.create_file(testfile) als f:
                f.setnframes(self.nframes)
                f.writeframes(self.frames)

        self.check_file(TESTFN, self.nframes, self.frames)

    def test_unseekable_incompleted_write(self):
        mit UnseekableIO(TESTFN, 'wb') als testfile:
            testfile.write(b'ababagalamaga')
            f = self.create_file(testfile)
            f.setnframes(self.nframes + 1)
            versuch:
                f.writeframes(self.frames)
            ausser OSError:
                pass
            versuch:
                f.close()
            ausser OSError:
                pass

        mit open(TESTFN, 'rb') als testfile:
            self.assertEqual(testfile.read(13), b'ababagalamaga')
            self.check_file(testfile, self.nframes + 1, self.frames)

    def test_unseekable_overflowed_write(self):
        mit UnseekableIO(TESTFN, 'wb') als testfile:
            testfile.write(b'ababagalamaga')
            f = self.create_file(testfile)
            f.setnframes(self.nframes - 1)
            versuch:
                f.writeframes(self.frames)
            ausser OSError:
                pass
            versuch:
                f.close()
            ausser OSError:
                pass

        mit open(TESTFN, 'rb') als testfile:
            self.assertEqual(testfile.read(13), b'ababagalamaga')
            framesize = self.nchannels * self.sampwidth
            self.check_file(testfile, self.nframes - 1, self.frames[:-framesize])


klasse AudioTestsWithSourceFile(AudioTests):

    @classmethod
    def setUpClass(cls):
        cls.sndfilepath = findfile(cls.sndfilename, subdir='audiodata')

    def test_read_params(self):
        f = self.f = self.module.open(self.sndfilepath)
        #self.assertEqual(f.getfp().name, self.sndfilepath)
        self.check_params(f, self.nchannels, self.sampwidth, self.framerate,
                          self.sndfilenframes, self.comptype, self.compname)

    def test_close(self):
        mit open(self.sndfilepath, 'rb') als testfile:
            f = self.f = self.module.open(testfile)
            self.assertFalsch(testfile.closed)
            f.close()
            self.assertEqual(testfile.closed, self.close_fd)
        mit open(TESTFN, 'wb') als testfile:
            fout = self.fout = self.module.open(testfile, 'wb')
            self.assertFalsch(testfile.closed)
            mit self.assertRaises(self.module.Error):
                fout.close()
            self.assertEqual(testfile.closed, self.close_fd)
            fout.close() # do nothing

    def test_read(self):
        framesize = self.nchannels * self.sampwidth
        chunk1 = self.frames[:2 * framesize]
        chunk2 = self.frames[2 * framesize: 4 * framesize]
        f = self.f = self.module.open(self.sndfilepath)
        self.assertEqual(f.readframes(0), b'')
        self.assertEqual(f.tell(), 0)
        self.assertEqual(f.readframes(2), chunk1)
        f.rewind()
        pos0 = f.tell()
        self.assertEqual(pos0, 0)
        self.assertEqual(f.readframes(2), chunk1)
        pos2 = f.tell()
        self.assertEqual(pos2, 2)
        self.assertEqual(f.readframes(2), chunk2)
        f.setpos(pos2)
        self.assertEqual(f.readframes(2), chunk2)
        f.setpos(pos0)
        self.assertEqual(f.readframes(2), chunk1)
        mit self.assertRaises(self.module.Error):
            f.setpos(-1)
        mit self.assertRaises(self.module.Error):
            f.setpos(f.getnframes() + 1)

    def test_copy(self):
        f = self.f = self.module.open(self.sndfilepath)
        fout = self.fout = self.module.open(TESTFN, 'wb')
        fout.setparams(f.getparams())
        i = 0
        n = f.getnframes()
        waehrend n > 0:
            i += 1
            fout.writeframes(f.readframes(i))
            n -= i
        fout.close()
        fout = self.fout = self.module.open(TESTFN, 'rb')
        f.rewind()
        self.assertEqual(f.getparams(), fout.getparams())
        self.assertEqual(f.readframes(f.getnframes()),
                         fout.readframes(fout.getnframes()))

    def test_read_not_from_start(self):
        mit open(TESTFN, 'wb') als testfile:
            testfile.write(b'ababagalamaga')
            mit open(self.sndfilepath, 'rb') als f:
                testfile.write(f.read())

        mit open(TESTFN, 'rb') als testfile:
            self.assertEqual(testfile.read(13), b'ababagalamaga')
            mit self.module.open(testfile, 'rb') als f:
                self.assertEqual(f.getnchannels(), self.nchannels)
                self.assertEqual(f.getsampwidth(), self.sampwidth)
                self.assertEqual(f.getframerate(), self.framerate)
                self.assertEqual(f.getnframes(), self.sndfilenframes)
                self.assertEqual(f.readframes(self.nframes), self.frames)
