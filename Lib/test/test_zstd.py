importiere array
importiere gc
importiere io
importiere pathlib
importiere random
importiere re
importiere os
importiere unittest
importiere tempfile
importiere threading

von test.support.import_helper importiere import_module
von test.support importiere threading_helper
von test.support importiere _1M

_zstd = import_module("_zstd")
zstd = import_module("compression.zstd")

von compression.zstd importiere (
    open,
    compress,
    decompress,
    ZstdCompressor,
    ZstdDecompressor,
    ZstdDict,
    ZstdError,
    zstd_version,
    zstd_version_info,
    COMPRESSION_LEVEL_DEFAULT,
    get_frame_info,
    get_frame_size,
    finalize_dict,
    train_dict,
    CompressionParameter,
    DecompressionParameter,
    Strategy,
    ZstdFile,
)

_1K = 1024
_130_1K = 130 * _1K
DICT_SIZE1 = 3*_1K

DAT_130K_D = Nichts
DAT_130K_C = Nichts

DECOMPRESSED_DAT = Nichts
COMPRESSED_DAT = Nichts

DECOMPRESSED_100_PLUS_32KB = Nichts
COMPRESSED_100_PLUS_32KB = Nichts

SKIPPABLE_FRAME = Nichts

THIS_FILE_BYTES = Nichts
THIS_FILE_STR = Nichts
COMPRESSED_THIS_FILE = Nichts

COMPRESSED_BOGUS = Nichts

SAMPLES = Nichts

TRAINED_DICT = Nichts

# Cannot be deferred to setup als it ist used to check whether oder nicht to skip
# tests
versuch:
    SUPPORT_MULTITHREADING = CompressionParameter.nb_workers.bounds() != (0, 0)
ausser Exception:
    SUPPORT_MULTITHREADING = Falsch

C_INT_MIN = -(2**31)
C_INT_MAX = (2**31) - 1


def setUpModule():
    # uncompressed size 130KB, more than a zstd block.
    # mit a frame epilogue, 4 bytes checksum.
    global DAT_130K_D
    DAT_130K_D = bytes([random.randint(0, 127) fuer _ in range(130*_1K)])

    global DAT_130K_C
    DAT_130K_C = compress(DAT_130K_D, options={CompressionParameter.checksum_flag:1})

    global DECOMPRESSED_DAT
    DECOMPRESSED_DAT = b'abcdefg123456' * 1000

    global COMPRESSED_DAT
    COMPRESSED_DAT = compress(DECOMPRESSED_DAT)

    global DECOMPRESSED_100_PLUS_32KB
    DECOMPRESSED_100_PLUS_32KB = b'a' * (100 + 32*_1K)

    global COMPRESSED_100_PLUS_32KB
    COMPRESSED_100_PLUS_32KB = compress(DECOMPRESSED_100_PLUS_32KB)

    global SKIPPABLE_FRAME
    SKIPPABLE_FRAME = (0x184D2A50).to_bytes(4, byteorder='little') + \
                      (32*_1K).to_bytes(4, byteorder='little') + \
                      b'a' * (32*_1K)

    global THIS_FILE_BYTES, THIS_FILE_STR
    mit io.open(os.path.abspath(__file__), 'rb') als f:
        THIS_FILE_BYTES = f.read()
        THIS_FILE_BYTES = re.sub(rb'\r?\n', rb'\n', THIS_FILE_BYTES)
        THIS_FILE_STR = THIS_FILE_BYTES.decode('utf-8')

    global COMPRESSED_THIS_FILE
    COMPRESSED_THIS_FILE = compress(THIS_FILE_BYTES)

    global COMPRESSED_BOGUS
    COMPRESSED_BOGUS = DECOMPRESSED_DAT

    # dict data
    words = [b'red', b'green', b'yellow', b'black', b'withe', b'blue',
             b'lilac', b'purple', b'navy', b'glod', b'silver', b'olive',
             b'dog', b'cat', b'tiger', b'lion', b'fish', b'bird']
    lst = []
    fuer i in range(300):
        sample = [b'%s = %d' % (random.choice(words), random.randrange(100))
                  fuer j in range(20)]
        sample = b'\n'.join(sample)

        lst.append(sample)
    global SAMPLES
    SAMPLES = lst
    assert len(SAMPLES) > 10

    global TRAINED_DICT
    TRAINED_DICT = train_dict(SAMPLES, 3*_1K)
    assert len(TRAINED_DICT.dict_content) <= 3*_1K


klasse FunctionsTestCase(unittest.TestCase):

    def test_version(self):
        s = ".".join((str(i) fuer i in zstd_version_info))
        self.assertEqual(s, zstd_version)

    def test_compressionLevel_values(self):
        min, max = CompressionParameter.compression_level.bounds()
        self.assertIs(type(COMPRESSION_LEVEL_DEFAULT), int)
        self.assertIs(type(min), int)
        self.assertIs(type(max), int)
        self.assertLess(min, max)

    def test_roundtrip_default(self):
        raw_dat = THIS_FILE_BYTES[: len(THIS_FILE_BYTES) // 6]
        dat1 = compress(raw_dat)
        dat2 = decompress(dat1)
        self.assertEqual(dat2, raw_dat)

    def test_roundtrip_level(self):
        raw_dat = THIS_FILE_BYTES[: len(THIS_FILE_BYTES) // 6]
        level_min, level_max = CompressionParameter.compression_level.bounds()

        fuer level in range(max(-20, level_min), level_max + 1):
            dat1 = compress(raw_dat, level)
            dat2 = decompress(dat1)
            self.assertEqual(dat2, raw_dat)

    def test_get_frame_info(self):
        # no dict
        info = get_frame_info(COMPRESSED_100_PLUS_32KB[:20])
        self.assertEqual(info.decompressed_size, 32 * _1K + 100)
        self.assertEqual(info.dictionary_id, 0)

        # use dict
        dat = compress(b"a" * 345, zstd_dict=TRAINED_DICT)
        info = get_frame_info(dat)
        self.assertEqual(info.decompressed_size, 345)
        self.assertEqual(info.dictionary_id, TRAINED_DICT.dict_id)

        mit self.assertRaisesRegex(ZstdError, "not less than the frame header"):
            get_frame_info(b"aaaaaaaaaaaaaa")

    def test_get_frame_size(self):
        size = get_frame_size(COMPRESSED_100_PLUS_32KB)
        self.assertEqual(size, len(COMPRESSED_100_PLUS_32KB))

        mit self.assertRaisesRegex(ZstdError, "not less than this complete frame"):
            get_frame_size(b"aaaaaaaaaaaaaa")

    def test_decompress_2x130_1K(self):
        decompressed_size = get_frame_info(DAT_130K_C).decompressed_size
        self.assertEqual(decompressed_size, _130_1K)

        dat = decompress(DAT_130K_C + DAT_130K_C)
        self.assertEqual(len(dat), 2 * _130_1K)


klasse CompressorTestCase(unittest.TestCase):

    def test_simple_compress_bad_args(self):
        # ZstdCompressor
        self.assertRaises(TypeError, ZstdCompressor, [])
        self.assertRaises(TypeError, ZstdCompressor, level=3.14)
        self.assertRaises(TypeError, ZstdCompressor, level="abc")
        self.assertRaises(TypeError, ZstdCompressor, options=b"abc")

        self.assertRaises(TypeError, ZstdCompressor, zstd_dict=123)
        self.assertRaises(TypeError, ZstdCompressor, zstd_dict=b"abcd1234")
        self.assertRaises(TypeError, ZstdCompressor, zstd_dict={1: 2, 3: 4})

        # valid range fuer compression level ist [-(1<<17), 22]
        msg = r'illegal compression level {}; the valid range ist \[-?\d+, -?\d+\]'
        mit self.assertRaisesRegex(ValueError, msg.format(C_INT_MAX)):
            ZstdCompressor(C_INT_MAX)
        mit self.assertRaisesRegex(ValueError, msg.format(C_INT_MIN)):
            ZstdCompressor(C_INT_MIN)
        msg = r'illegal compression level; the valid range ist \[-?\d+, -?\d+\]'
        mit self.assertRaisesRegex(ValueError, msg):
            ZstdCompressor(level=-(2**1000))
        mit self.assertRaisesRegex(ValueError, msg):
            ZstdCompressor(level=2**1000)

        mit self.assertRaises(ValueError):
            ZstdCompressor(options={CompressionParameter.window_log: 100})
        mit self.assertRaises(ValueError):
            ZstdCompressor(options={3333: 100})

        # Method bad arguments
        zc = ZstdCompressor()
        self.assertRaises(TypeError, zc.compress)
        self.assertRaises((TypeError, ValueError), zc.compress, b"foo", b"bar")
        self.assertRaises(TypeError, zc.compress, "str")
        self.assertRaises((TypeError, ValueError), zc.flush, b"foo")
        self.assertRaises(TypeError, zc.flush, b"blah", 1)

        self.assertRaises(ValueError, zc.compress, b'', -1)
        self.assertRaises(ValueError, zc.compress, b'', 3)
        self.assertRaises(ValueError, zc.flush, zc.CONTINUE) # 0
        self.assertRaises(ValueError, zc.flush, 3)

        zc.compress(b'')
        zc.compress(b'', zc.CONTINUE)
        zc.compress(b'', zc.FLUSH_BLOCK)
        zc.compress(b'', zc.FLUSH_FRAME)
        empty = zc.flush()
        zc.flush(zc.FLUSH_BLOCK)
        zc.flush(zc.FLUSH_FRAME)

    def test_compress_parameters(self):
        d = {CompressionParameter.compression_level : 10,

             CompressionParameter.window_log : 12,
             CompressionParameter.hash_log : 10,
             CompressionParameter.chain_log : 12,
             CompressionParameter.search_log : 12,
             CompressionParameter.min_match : 4,
             CompressionParameter.target_length : 12,
             CompressionParameter.strategy : Strategy.lazy,

             CompressionParameter.enable_long_distance_matching : 1,
             CompressionParameter.ldm_hash_log : 12,
             CompressionParameter.ldm_min_match : 11,
             CompressionParameter.ldm_bucket_size_log : 5,
             CompressionParameter.ldm_hash_rate_log : 12,

             CompressionParameter.content_size_flag : 1,
             CompressionParameter.checksum_flag : 1,
             CompressionParameter.dict_id_flag : 0,

             CompressionParameter.nb_workers : 2 wenn SUPPORT_MULTITHREADING sonst 0,
             CompressionParameter.job_size : 5*_1M wenn SUPPORT_MULTITHREADING sonst 0,
             CompressionParameter.overlap_log : 9 wenn SUPPORT_MULTITHREADING sonst 0,
             }
        ZstdCompressor(options=d)

        d1 = d.copy()
        # larger than signed int
        d1[CompressionParameter.ldm_bucket_size_log] = C_INT_MAX
        mit self.assertRaises(ValueError):
            ZstdCompressor(options=d1)
        # smaller than signed int
        d1[CompressionParameter.ldm_bucket_size_log] = C_INT_MIN
        mit self.assertRaises(ValueError):
            ZstdCompressor(options=d1)

        # out of bounds compression level
        level_min, level_max = CompressionParameter.compression_level.bounds()
        mit self.assertRaises(ValueError):
            compress(b'', level_max+1)
        mit self.assertRaises(ValueError):
            compress(b'', level_min-1)
        mit self.assertRaises(ValueError):
            compress(b'', 2**1000)
        mit self.assertRaises(ValueError):
            compress(b'', -(2**1000))
        mit self.assertRaises(ValueError):
            compress(b'', options={
                CompressionParameter.compression_level: level_max+1})
        mit self.assertRaises(ValueError):
            compress(b'', options={
                CompressionParameter.compression_level: level_min-1})

        # zstd lib doesn't support MT compression
        wenn nicht SUPPORT_MULTITHREADING:
            mit self.assertRaises(ValueError):
                ZstdCompressor(options={CompressionParameter.nb_workers:4})
            mit self.assertRaises(ValueError):
                ZstdCompressor(options={CompressionParameter.job_size:4})
            mit self.assertRaises(ValueError):
                ZstdCompressor(options={CompressionParameter.overlap_log:4})

        # out of bounds error msg
        option = {CompressionParameter.window_log:100}
        mit self.assertRaisesRegex(
            ValueError,
            "compression parameter 'window_log' received an illegal value 100; "
            r'the valid range ist \[-?\d+, -?\d+\]',
        ):
            compress(b'', options=option)

    def test_unknown_compression_parameter(self):
        KEY = 100001234
        option = {CompressionParameter.compression_level: 10,
                  KEY: 200000000}
        pattern = rf"invalid compression parameter 'unknown parameter \(key {KEY}\)'"
        mit self.assertRaisesRegex(ValueError, pattern):
            ZstdCompressor(options=option)

    @unittest.skipIf(nicht SUPPORT_MULTITHREADING,
                     "zstd build doesn't support multi-threaded compression")
    def test_zstd_multithread_compress(self):
        size = 40*_1M
        b = THIS_FILE_BYTES * (size // len(THIS_FILE_BYTES))

        options = {CompressionParameter.compression_level : 4,
                   CompressionParameter.nb_workers : 2}

        # compress()
        dat1 = compress(b, options=options)
        dat2 = decompress(dat1)
        self.assertEqual(dat2, b)

        # ZstdCompressor
        c = ZstdCompressor(options=options)
        dat1 = c.compress(b, c.CONTINUE)
        dat2 = c.compress(b, c.FLUSH_BLOCK)
        dat3 = c.compress(b, c.FLUSH_FRAME)
        dat4 = decompress(dat1+dat2+dat3)
        self.assertEqual(dat4, b * 3)

        # ZstdFile
        mit ZstdFile(io.BytesIO(), 'w', options=options) als f:
            f.write(b)

    def test_compress_flushblock(self):
        point = len(THIS_FILE_BYTES) // 2

        c = ZstdCompressor()
        self.assertEqual(c.last_mode, c.FLUSH_FRAME)
        dat1 = c.compress(THIS_FILE_BYTES[:point])
        self.assertEqual(c.last_mode, c.CONTINUE)
        dat1 += c.compress(THIS_FILE_BYTES[point:], c.FLUSH_BLOCK)
        self.assertEqual(c.last_mode, c.FLUSH_BLOCK)
        dat2 = c.flush()
        pattern = "Compressed data ended before the end-of-stream marker"
        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(dat1)

        dat3 = decompress(dat1 + dat2)

        self.assertEqual(dat3, THIS_FILE_BYTES)

    def test_compress_flushframe(self):
        # test compress & decompress
        point = len(THIS_FILE_BYTES) // 2

        c = ZstdCompressor()

        dat1 = c.compress(THIS_FILE_BYTES[:point])
        self.assertEqual(c.last_mode, c.CONTINUE)

        dat1 += c.compress(THIS_FILE_BYTES[point:], c.FLUSH_FRAME)
        self.assertEqual(c.last_mode, c.FLUSH_FRAME)

        nt = get_frame_info(dat1)
        self.assertEqual(nt.decompressed_size, Nichts) # no content size

        dat2 = decompress(dat1)

        self.assertEqual(dat2, THIS_FILE_BYTES)

        # single .FLUSH_FRAME mode has content size
        c = ZstdCompressor()
        dat = c.compress(THIS_FILE_BYTES, mode=c.FLUSH_FRAME)
        self.assertEqual(c.last_mode, c.FLUSH_FRAME)

        nt = get_frame_info(dat)
        self.assertEqual(nt.decompressed_size, len(THIS_FILE_BYTES))

    def test_compress_empty(self):
        # output empty content frame
        self.assertNotEqual(compress(b''), b'')

        c = ZstdCompressor()
        self.assertNotEqual(c.compress(b'', c.FLUSH_FRAME), b'')

    def test_set_pledged_input_size(self):
        DAT = DECOMPRESSED_100_PLUS_32KB
        CHUNK_SIZE = len(DAT) // 3

        # wrong value
        c = ZstdCompressor()
        mit self.assertRaisesRegex(ValueError,
                                    r'should be a positive int less than \d+'):
            c.set_pledged_input_size(-300)
        # overflow
        mit self.assertRaisesRegex(ValueError,
                                    r'should be a positive int less than \d+'):
            c.set_pledged_input_size(2**64)
        # ZSTD_CONTENTSIZE_ERROR ist invalid
        mit self.assertRaisesRegex(ValueError,
                                    r'should be a positive int less than \d+'):
            c.set_pledged_input_size(2**64-2)
        # ZSTD_CONTENTSIZE_UNKNOWN should use Nichts
        mit self.assertRaisesRegex(ValueError,
                                    r'should be a positive int less than \d+'):
            c.set_pledged_input_size(2**64-1)

        # check valid values are settable
        c.set_pledged_input_size(2**63)
        c.set_pledged_input_size(2**64-3)

        # check that zero means empty frame
        c = ZstdCompressor(level=1)
        c.set_pledged_input_size(0)
        c.compress(b'')
        dat = c.flush()
        ret = get_frame_info(dat)
        self.assertEqual(ret.decompressed_size, 0)


        # wrong mode
        c = ZstdCompressor(level=1)
        c.compress(b'123456')
        self.assertEqual(c.last_mode, c.CONTINUE)
        mit self.assertRaisesRegex(ValueError,
                                    r'last_mode == FLUSH_FRAME'):
            c.set_pledged_input_size(300)

        # Nichts value
        c = ZstdCompressor(level=1)
        c.set_pledged_input_size(Nichts)
        dat = c.compress(DAT) + c.flush()

        ret = get_frame_info(dat)
        self.assertEqual(ret.decompressed_size, Nichts)

        # correct value
        c = ZstdCompressor(level=1)
        c.set_pledged_input_size(len(DAT))

        chunks = []
        posi = 0
        waehrend posi < len(DAT):
            dat = c.compress(DAT[posi:posi+CHUNK_SIZE])
            posi += CHUNK_SIZE
            chunks.append(dat)

        dat = c.flush()
        chunks.append(dat)
        chunks = b''.join(chunks)

        ret = get_frame_info(chunks)
        self.assertEqual(ret.decompressed_size, len(DAT))
        self.assertEqual(decompress(chunks), DAT)

        c.set_pledged_input_size(len(DAT)) # the second frame
        dat = c.compress(DAT) + c.flush()

        ret = get_frame_info(dat)
        self.assertEqual(ret.decompressed_size, len(DAT))
        self.assertEqual(decompress(dat), DAT)

        # nicht enough data
        c = ZstdCompressor(level=1)
        c.set_pledged_input_size(len(DAT)+1)

        fuer start in range(0, len(DAT), CHUNK_SIZE):
            end = min(start+CHUNK_SIZE, len(DAT))
            _dat = c.compress(DAT[start:end])

        mit self.assertRaises(ZstdError):
            c.flush()

        # too much data
        c = ZstdCompressor(level=1)
        c.set_pledged_input_size(len(DAT))

        fuer start in range(0, len(DAT), CHUNK_SIZE):
            end = min(start+CHUNK_SIZE, len(DAT))
            _dat = c.compress(DAT[start:end])

        mit self.assertRaises(ZstdError):
            c.compress(b'extra', ZstdCompressor.FLUSH_FRAME)

        # content size nicht set wenn content_size_flag == 0
        c = ZstdCompressor(options={CompressionParameter.content_size_flag: 0})
        c.set_pledged_input_size(10)
        dat1 = c.compress(b"hello")
        dat2 = c.compress(b"world")
        dat3 = c.flush()
        frame_data = get_frame_info(dat1 + dat2 + dat3)
        self.assertIsNichts(frame_data.decompressed_size)


klasse DecompressorTestCase(unittest.TestCase):

    def test_simple_decompress_bad_args(self):
        # ZstdDecompressor
        self.assertRaises(TypeError, ZstdDecompressor, ())
        self.assertRaises(TypeError, ZstdDecompressor, zstd_dict=123)
        self.assertRaises(TypeError, ZstdDecompressor, zstd_dict=b'abc')
        self.assertRaises(TypeError, ZstdDecompressor, zstd_dict={1:2, 3:4})

        self.assertRaises(TypeError, ZstdDecompressor, options=123)
        self.assertRaises(TypeError, ZstdDecompressor, options='abc')
        self.assertRaises(TypeError, ZstdDecompressor, options=b'abc')

        mit self.assertRaises(ValueError):
            ZstdDecompressor(options={C_INT_MAX: 100})
        mit self.assertRaises(ValueError):
            ZstdDecompressor(options={C_INT_MIN: 100})
        mit self.assertRaises(ValueError):
            ZstdDecompressor(options={0: C_INT_MAX})
        mit self.assertRaises(OverflowError):
            ZstdDecompressor(options={2**1000: 100})
        mit self.assertRaises(OverflowError):
            ZstdDecompressor(options={-(2**1000): 100})
        mit self.assertRaises(OverflowError):
            ZstdDecompressor(options={0: -(2**1000)})

        mit self.assertRaises(ValueError):
            ZstdDecompressor(options={DecompressionParameter.window_log_max: 100})
        mit self.assertRaises(ValueError):
            ZstdDecompressor(options={3333: 100})

        empty = compress(b'')
        lzd = ZstdDecompressor()
        self.assertRaises(TypeError, lzd.decompress)
        self.assertRaises(TypeError, lzd.decompress, b"foo", b"bar")
        self.assertRaises(TypeError, lzd.decompress, "str")
        lzd.decompress(empty)

    def test_decompress_parameters(self):
        d = {DecompressionParameter.window_log_max : 15}
        ZstdDecompressor(options=d)

        d1 = d.copy()
        # larger than signed int
        d1[DecompressionParameter.window_log_max] = 2**1000
        mit self.assertRaises(OverflowError):
            ZstdDecompressor(Nichts, d1)
        # smaller than signed int
        d1[DecompressionParameter.window_log_max] = -(2**1000)
        mit self.assertRaises(OverflowError):
            ZstdDecompressor(Nichts, d1)

        d1[DecompressionParameter.window_log_max] = C_INT_MAX
        mit self.assertRaises(ValueError):
            ZstdDecompressor(Nichts, d1)
        d1[DecompressionParameter.window_log_max] = C_INT_MIN
        mit self.assertRaises(ValueError):
            ZstdDecompressor(Nichts, d1)

        # out of bounds error msg
        options = {DecompressionParameter.window_log_max:100}
        mit self.assertRaisesRegex(
            ValueError,
            "decompression parameter 'window_log_max' received an illegal value 100; "
            r'the valid range ist \[-?\d+, -?\d+\]',
        ):
            decompress(b'', options=options)

        # out of bounds deecompression parameter
        options[DecompressionParameter.window_log_max] = C_INT_MAX
        mit self.assertRaises(ValueError):
            decompress(b'', options=options)
        options[DecompressionParameter.window_log_max] = C_INT_MIN
        mit self.assertRaises(ValueError):
            decompress(b'', options=options)
        options[DecompressionParameter.window_log_max] = 2**1000
        mit self.assertRaises(OverflowError):
            decompress(b'', options=options)
        options[DecompressionParameter.window_log_max] = -(2**1000)
        mit self.assertRaises(OverflowError):
            decompress(b'', options=options)

    def test_unknown_decompression_parameter(self):
        KEY = 100001234
        options = {DecompressionParameter.window_log_max: DecompressionParameter.window_log_max.bounds()[1],
                  KEY: 200000000}
        pattern = rf"invalid decompression parameter 'unknown parameter \(key {KEY}\)'"
        mit self.assertRaisesRegex(ValueError, pattern):
            ZstdDecompressor(options=options)

    def test_decompress_epilogue_flags(self):
        # DAT_130K_C has a 4 bytes checksum at frame epilogue

        # full unlimited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C)
        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.needs_input)

        mit self.assertRaises(EOFError):
            dat = d.decompress(b'')

        # full limited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C, _130_1K)
        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.needs_input)

        mit self.assertRaises(EOFError):
            dat = d.decompress(b'', 0)

        # [:-4] unlimited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-4])
        self.assertEqual(len(dat), _130_1K)
        self.assertWahr(d.needs_input)

        dat = d.decompress(b'')
        self.assertEqual(len(dat), 0)
        self.assertWahr(d.needs_input)

        # [:-4] limited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-4], _130_1K)
        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.needs_input)

        dat = d.decompress(b'', 0)
        self.assertEqual(len(dat), 0)
        self.assertFalsch(d.needs_input)

        # [:-3] unlimited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-3])
        self.assertEqual(len(dat), _130_1K)
        self.assertWahr(d.needs_input)

        dat = d.decompress(b'')
        self.assertEqual(len(dat), 0)
        self.assertWahr(d.needs_input)

        # [:-3] limited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-3], _130_1K)
        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.needs_input)

        dat = d.decompress(b'', 0)
        self.assertEqual(len(dat), 0)
        self.assertFalsch(d.needs_input)

        # [:-1] unlimited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-1])
        self.assertEqual(len(dat), _130_1K)
        self.assertWahr(d.needs_input)

        dat = d.decompress(b'')
        self.assertEqual(len(dat), 0)
        self.assertWahr(d.needs_input)

        # [:-1] limited
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-1], _130_1K)
        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.needs_input)

        dat = d.decompress(b'', 0)
        self.assertEqual(len(dat), 0)
        self.assertFalsch(d.needs_input)

    def test_decompressor_arg(self):
        zd = ZstdDict(b'12345678', is_raw=Wahr)

        mit self.assertRaises(TypeError):
            d = ZstdDecompressor(zstd_dict={})

        mit self.assertRaises(TypeError):
            d = ZstdDecompressor(options=zd)

        ZstdDecompressor()
        ZstdDecompressor(zd, {})
        ZstdDecompressor(zstd_dict=zd, options={DecompressionParameter.window_log_max:25})

    def test_decompressor_1(self):
        # empty
        d = ZstdDecompressor()
        dat = d.decompress(b'')

        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)

        # 130_1K full
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C)

        self.assertEqual(len(dat), _130_1K)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)

        # 130_1K full, limit output
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C, _130_1K)

        self.assertEqual(len(dat), _130_1K)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)

        # 130_1K, without 4 bytes checksum
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-4])

        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)

        # above, limit output
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C[:-4], _130_1K)

        self.assertEqual(len(dat), _130_1K)
        self.assertFalsch(d.eof)
        self.assertFalsch(d.needs_input)

        # full, unused_data
        TRAIL = b'89234893abcd'
        d = ZstdDecompressor()
        dat = d.decompress(DAT_130K_C + TRAIL, _130_1K)

        self.assertEqual(len(dat), _130_1K)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, TRAIL)

    def test_decompressor_chunks_read_300(self):
        TRAIL = b'89234893abcd'
        DAT = DAT_130K_C + TRAIL
        d = ZstdDecompressor()

        bi = io.BytesIO(DAT)
        lst = []
        waehrend Wahr:
            wenn d.needs_input:
                dat = bi.read(300)
                wenn nicht dat:
                    breche
            sonst:
                wirf Exception('should nicht get here')

            ret = d.decompress(dat)
            lst.append(ret)
            wenn d.eof:
                breche

        ret = b''.join(lst)

        self.assertEqual(len(ret), _130_1K)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data + bi.read(), TRAIL)

    def test_decompressor_chunks_read_3(self):
        TRAIL = b'89234893'
        DAT = DAT_130K_C + TRAIL
        d = ZstdDecompressor()

        bi = io.BytesIO(DAT)
        lst = []
        waehrend Wahr:
            wenn d.needs_input:
                dat = bi.read(3)
                wenn nicht dat:
                    breche
            sonst:
                dat = b''

            ret = d.decompress(dat, 1)
            lst.append(ret)
            wenn d.eof:
                breche

        ret = b''.join(lst)

        self.assertEqual(len(ret), _130_1K)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data + bi.read(), TRAIL)


    def test_decompress_empty(self):
        mit self.assertRaises(ZstdError):
            decompress(b'')

        d = ZstdDecompressor()
        self.assertEqual(d.decompress(b''), b'')
        self.assertFalsch(d.eof)

    def test_decompress_empty_content_frame(self):
        DAT = compress(b'')
        # decompress
        self.assertGreaterEqual(len(DAT), 4)
        self.assertEqual(decompress(DAT), b'')

        mit self.assertRaises(ZstdError):
            decompress(DAT[:-1])

        # ZstdDecompressor
        d = ZstdDecompressor()
        dat = d.decompress(DAT)
        self.assertEqual(dat, b'')
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        d = ZstdDecompressor()
        dat = d.decompress(DAT[:-1])
        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

klasse DecompressorFlagsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = {CompressionParameter.checksum_flag:1}
        c = ZstdCompressor(options=options)

        cls.DECOMPRESSED_42 = b'a'*42
        cls.FRAME_42 = c.compress(cls.DECOMPRESSED_42, c.FLUSH_FRAME)

        cls.DECOMPRESSED_60 = b'a'*60
        cls.FRAME_60 = c.compress(cls.DECOMPRESSED_60, c.FLUSH_FRAME)

        cls.FRAME_42_60 = cls.FRAME_42 + cls.FRAME_60
        cls.DECOMPRESSED_42_60 = cls.DECOMPRESSED_42 + cls.DECOMPRESSED_60

        cls._130_1K = 130*_1K

        c = ZstdCompressor()
        cls.UNKNOWN_FRAME_42 = c.compress(cls.DECOMPRESSED_42) + c.flush()
        cls.UNKNOWN_FRAME_60 = c.compress(cls.DECOMPRESSED_60) + c.flush()
        cls.UNKNOWN_FRAME_42_60 = cls.UNKNOWN_FRAME_42 + cls.UNKNOWN_FRAME_60

        cls.TRAIL = b'12345678abcdefg!@#$%^&*()_+|'

    def test_function_decompress(self):

        self.assertEqual(len(decompress(COMPRESSED_100_PLUS_32KB)), 100+32*_1K)

        # 1 frame
        self.assertEqual(decompress(self.FRAME_42), self.DECOMPRESSED_42)

        self.assertEqual(decompress(self.UNKNOWN_FRAME_42), self.DECOMPRESSED_42)

        pattern = r"Compressed data ended before the end-of-stream marker"
        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(self.FRAME_42[:1])

        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(self.FRAME_42[:-4])

        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(self.FRAME_42[:-1])

        # 2 frames
        self.assertEqual(decompress(self.FRAME_42_60), self.DECOMPRESSED_42_60)

        self.assertEqual(decompress(self.UNKNOWN_FRAME_42_60), self.DECOMPRESSED_42_60)

        self.assertEqual(decompress(self.FRAME_42 + self.UNKNOWN_FRAME_60),
                         self.DECOMPRESSED_42_60)

        self.assertEqual(decompress(self.UNKNOWN_FRAME_42 + self.FRAME_60),
                         self.DECOMPRESSED_42_60)

        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(self.FRAME_42_60[:-4])

        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(self.UNKNOWN_FRAME_42_60[:-1])

        # 130_1K
        self.assertEqual(decompress(DAT_130K_C), DAT_130K_D)

        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(DAT_130K_C[:-4])

        mit self.assertRaisesRegex(ZstdError, pattern):
            decompress(DAT_130K_C[:-1])

        # Unknown frame descriptor
        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            decompress(b'aaaaaaaaa')

        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            decompress(self.FRAME_42 + b'aaaaaaaaa')

        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            decompress(self.UNKNOWN_FRAME_42_60 + b'aaaaaaaaa')

        # doesn't match checksum
        checksum = DAT_130K_C[-4:]
        wenn checksum[0] == 255:
            wrong_checksum = bytes([254]) + checksum[1:]
        sonst:
            wrong_checksum = bytes([checksum[0]+1]) + checksum[1:]

        dat = DAT_130K_C[:-4] + wrong_checksum

        mit self.assertRaisesRegex(ZstdError, "doesn't match checksum"):
            decompress(dat)

    def test_function_skippable(self):
        self.assertEqual(decompress(SKIPPABLE_FRAME), b'')
        self.assertEqual(decompress(SKIPPABLE_FRAME + SKIPPABLE_FRAME), b'')

        # 1 frame + 2 skippable
        self.assertEqual(len(decompress(SKIPPABLE_FRAME + SKIPPABLE_FRAME + DAT_130K_C)),
                         self._130_1K)

        self.assertEqual(len(decompress(DAT_130K_C + SKIPPABLE_FRAME + SKIPPABLE_FRAME)),
                         self._130_1K)

        self.assertEqual(len(decompress(SKIPPABLE_FRAME + DAT_130K_C + SKIPPABLE_FRAME)),
                         self._130_1K)

        # unknown size
        self.assertEqual(decompress(SKIPPABLE_FRAME + self.UNKNOWN_FRAME_60),
                         self.DECOMPRESSED_60)

        self.assertEqual(decompress(self.UNKNOWN_FRAME_60 + SKIPPABLE_FRAME),
                         self.DECOMPRESSED_60)

        # 2 frames + 1 skippable
        self.assertEqual(decompress(self.FRAME_42 + SKIPPABLE_FRAME + self.FRAME_60),
                         self.DECOMPRESSED_42_60)

        self.assertEqual(decompress(SKIPPABLE_FRAME + self.FRAME_42_60),
                         self.DECOMPRESSED_42_60)

        self.assertEqual(decompress(self.UNKNOWN_FRAME_42_60 + SKIPPABLE_FRAME),
                         self.DECOMPRESSED_42_60)

        # incomplete
        mit self.assertRaises(ZstdError):
            decompress(SKIPPABLE_FRAME[:1])

        mit self.assertRaises(ZstdError):
            decompress(SKIPPABLE_FRAME[:-1])

        mit self.assertRaises(ZstdError):
            decompress(self.FRAME_42 + SKIPPABLE_FRAME[:-1])

        # Unknown frame descriptor
        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            decompress(b'aaaaaaaaa' + SKIPPABLE_FRAME)

        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            decompress(SKIPPABLE_FRAME + b'aaaaaaaaa')

        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            decompress(SKIPPABLE_FRAME + SKIPPABLE_FRAME + b'aaaaaaaaa')

    def test_decompressor_1(self):
        # empty 1
        d = ZstdDecompressor()

        dat = d.decompress(b'')
        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        dat = d.decompress(b'', 0)
        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        dat = d.decompress(COMPRESSED_100_PLUS_32KB + b'a')
        self.assertEqual(dat, DECOMPRESSED_100_PLUS_32KB)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'a')
        self.assertEqual(d.unused_data, b'a') # twice

        # empty 2
        d = ZstdDecompressor()

        dat = d.decompress(b'', 0)
        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        dat = d.decompress(b'')
        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        dat = d.decompress(COMPRESSED_100_PLUS_32KB + b'a')
        self.assertEqual(dat, DECOMPRESSED_100_PLUS_32KB)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'a')
        self.assertEqual(d.unused_data, b'a') # twice

        # 1 frame
        d = ZstdDecompressor()
        dat = d.decompress(self.FRAME_42)

        self.assertEqual(dat, self.DECOMPRESSED_42)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        mit self.assertRaises(EOFError):
            d.decompress(b'')

        # 1 frame, trail
        d = ZstdDecompressor()
        dat = d.decompress(self.FRAME_42 + self.TRAIL)

        self.assertEqual(dat, self.DECOMPRESSED_42)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, self.TRAIL)
        self.assertEqual(d.unused_data, self.TRAIL) # twice

        # 1 frame, 32_1K
        temp = compress(b'a'*(32*_1K))
        d = ZstdDecompressor()
        dat = d.decompress(temp, 32*_1K)

        self.assertEqual(dat, b'a'*(32*_1K))
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        mit self.assertRaises(EOFError):
            d.decompress(b'')

        # 1 frame, 32_1K+100, trail
        d = ZstdDecompressor()
        dat = d.decompress(COMPRESSED_100_PLUS_32KB+self.TRAIL, 100) # 100 bytes

        self.assertEqual(len(dat), 100)
        self.assertFalsch(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')

        dat = d.decompress(b'') # 32_1K

        self.assertEqual(len(dat), 32*_1K)
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, self.TRAIL)
        self.assertEqual(d.unused_data, self.TRAIL) # twice

        mit self.assertRaises(EOFError):
            d.decompress(b'')

        # incomplete 1
        d = ZstdDecompressor()
        dat = d.decompress(self.FRAME_60[:1])

        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        # incomplete 2
        d = ZstdDecompressor()

        dat = d.decompress(self.FRAME_60[:-4])
        self.assertEqual(dat, self.DECOMPRESSED_60)
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        # incomplete 3
        d = ZstdDecompressor()

        dat = d.decompress(self.FRAME_60[:-1])
        self.assertEqual(dat, self.DECOMPRESSED_60)
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')

        # incomplete 4
        d = ZstdDecompressor()

        dat = d.decompress(self.FRAME_60[:-4], 60)
        self.assertEqual(dat, self.DECOMPRESSED_60)
        self.assertFalsch(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        dat = d.decompress(b'')
        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        # Unknown frame descriptor
        d = ZstdDecompressor()
        mit self.assertRaisesRegex(ZstdError, "Unknown frame descriptor"):
            d.decompress(b'aaaaaaaaa')

    def test_decompressor_skippable(self):
        # 1 skippable
        d = ZstdDecompressor()
        dat = d.decompress(SKIPPABLE_FRAME)

        self.assertEqual(dat, b'')
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        # 1 skippable, max_length=0
        d = ZstdDecompressor()
        dat = d.decompress(SKIPPABLE_FRAME, 0)

        self.assertEqual(dat, b'')
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        # 1 skippable, trail
        d = ZstdDecompressor()
        dat = d.decompress(SKIPPABLE_FRAME + self.TRAIL)

        self.assertEqual(dat, b'')
        self.assertWahr(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, self.TRAIL)
        self.assertEqual(d.unused_data, self.TRAIL) # twice

        # incomplete
        d = ZstdDecompressor()
        dat = d.decompress(SKIPPABLE_FRAME[:-1])

        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        # incomplete
        d = ZstdDecompressor()
        dat = d.decompress(SKIPPABLE_FRAME[:-1], 0)

        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertFalsch(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice

        dat = d.decompress(b'')

        self.assertEqual(dat, b'')
        self.assertFalsch(d.eof)
        self.assertWahr(d.needs_input)
        self.assertEqual(d.unused_data, b'')
        self.assertEqual(d.unused_data, b'') # twice



klasse ZstdDictTestCase(unittest.TestCase):

    def test_is_raw(self):
        # must be passed als a keyword argument
        mit self.assertRaises(TypeError):
            ZstdDict(bytes(8), Wahr)

        # content < 8
        b = b'1234567'
        mit self.assertRaises(ValueError):
            ZstdDict(b)

        # content == 8
        b = b'12345678'
        zd = ZstdDict(b, is_raw=Wahr)
        self.assertEqual(zd.dict_id, 0)

        temp = compress(b'aaa12345678', level=3, zstd_dict=zd)
        self.assertEqual(b'aaa12345678', decompress(temp, zd))

        # is_raw == Falsch
        b = b'12345678abcd'
        mit self.assertRaises(ValueError):
            ZstdDict(b)

        # read only attributes
        mit self.assertRaises(AttributeError):
            zd.dict_content = b

        mit self.assertRaises(AttributeError):
            zd.dict_id = 10000

        # ZstdDict arguments
        zd = ZstdDict(TRAINED_DICT.dict_content, is_raw=Falsch)
        self.assertNotEqual(zd.dict_id, 0)

        zd = ZstdDict(TRAINED_DICT.dict_content, is_raw=Wahr)
        self.assertNotEqual(zd.dict_id, 0) # note this assertion

        mit self.assertRaises(TypeError):
            ZstdDict("12345678abcdef", is_raw=Wahr)
        mit self.assertRaises(TypeError):
            ZstdDict(TRAINED_DICT)

        # invalid parameter
        mit self.assertRaises(TypeError):
            ZstdDict(desk333=345)

    def test_invalid_dict(self):
        DICT_MAGIC = 0xEC30A437.to_bytes(4, byteorder='little')
        dict_content = DICT_MAGIC + b'abcdefghighlmnopqrstuvwxyz'

        # corrupted
        zd = ZstdDict(dict_content, is_raw=Falsch)
        mit self.assertRaisesRegex(ZstdError, r'ZSTD_CDict.*?content\.$'):
            ZstdCompressor(zstd_dict=zd.as_digested_dict)
        mit self.assertRaisesRegex(ZstdError, r'ZSTD_DDict.*?content\.$'):
            ZstdDecompressor(zd)

        # wrong type
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdCompressor(zstd_dict=[zd, 1])
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdCompressor(zstd_dict=(zd, 1.0))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdCompressor(zstd_dict=(zd,))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdCompressor(zstd_dict=(zd, 1, 2))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdCompressor(zstd_dict=(zd, -1))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdCompressor(zstd_dict=(zd, 3))
        mit self.assertRaises(OverflowError):
            ZstdCompressor(zstd_dict=(zd, 2**1000))
        mit self.assertRaises(OverflowError):
            ZstdCompressor(zstd_dict=(zd, -2**1000))

        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdDecompressor(zstd_dict=[zd, 1])
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdDecompressor(zstd_dict=(zd, 1.0))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdDecompressor((zd,))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdDecompressor((zd, 1, 2))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdDecompressor((zd, -1))
        mit self.assertRaisesRegex(TypeError, r'should be a ZstdDict object'):
            ZstdDecompressor((zd, 3))
        mit self.assertRaises(OverflowError):
            ZstdDecompressor((zd, 2**1000))
        mit self.assertRaises(OverflowError):
            ZstdDecompressor((zd, -2**1000))

    def test_train_dict(self):
        TRAINED_DICT = train_dict(SAMPLES, DICT_SIZE1)
        ZstdDict(TRAINED_DICT.dict_content, is_raw=Falsch)

        self.assertNotEqual(TRAINED_DICT.dict_id, 0)
        self.assertGreater(len(TRAINED_DICT.dict_content), 0)
        self.assertLessEqual(len(TRAINED_DICT.dict_content), DICT_SIZE1)
        self.assertWahr(re.match(r'^<ZstdDict dict_id=\d+ dict_size=\d+>$', str(TRAINED_DICT)))

        # compress/decompress
        c = ZstdCompressor(zstd_dict=TRAINED_DICT)
        fuer sample in SAMPLES:
            dat1 = compress(sample, zstd_dict=TRAINED_DICT)
            dat2 = decompress(dat1, TRAINED_DICT)
            self.assertEqual(sample, dat2)

            dat1 = c.compress(sample)
            dat1 += c.flush()
            dat2 = decompress(dat1, TRAINED_DICT)
            self.assertEqual(sample, dat2)

    def test_finalize_dict(self):
        DICT_SIZE2 = 200*_1K
        C_LEVEL = 6

        versuch:
            dic2 = finalize_dict(TRAINED_DICT, SAMPLES, DICT_SIZE2, C_LEVEL)
        ausser NotImplementedError:
            # < v1.4.5 at compile-time, >= v.1.4.5 at run-time
            gib

        self.assertNotEqual(dic2.dict_id, 0)
        self.assertGreater(len(dic2.dict_content), 0)
        self.assertLessEqual(len(dic2.dict_content), DICT_SIZE2)

        # compress/decompress
        c = ZstdCompressor(C_LEVEL, zstd_dict=dic2)
        fuer sample in SAMPLES:
            dat1 = compress(sample, C_LEVEL, zstd_dict=dic2)
            dat2 = decompress(dat1, dic2)
            self.assertEqual(sample, dat2)

            dat1 = c.compress(sample)
            dat1 += c.flush()
            dat2 = decompress(dat1, dic2)
            self.assertEqual(sample, dat2)

        # dict mismatch
        self.assertNotEqual(TRAINED_DICT.dict_id, dic2.dict_id)

        dat1 = compress(SAMPLES[0], zstd_dict=TRAINED_DICT)
        mit self.assertRaises(ZstdError):
            decompress(dat1, dic2)

    def test_train_dict_arguments(self):
        mit self.assertRaises(ValueError):
            train_dict([], 100*_1K)

        mit self.assertRaises(ValueError):
            train_dict(SAMPLES, -100)

        mit self.assertRaises(ValueError):
            train_dict(SAMPLES, 0)

    def test_finalize_dict_arguments(self):
        mit self.assertRaises(TypeError):
            finalize_dict({1:2}, (b'aaa', b'bbb'), 100*_1K, 2)

        mit self.assertRaises(ValueError):
            finalize_dict(TRAINED_DICT, [], 100*_1K, 2)

        mit self.assertRaises(ValueError):
            finalize_dict(TRAINED_DICT, SAMPLES, -100, 2)

        mit self.assertRaises(ValueError):
            finalize_dict(TRAINED_DICT, SAMPLES, 0, 2)

    def test_train_dict_c(self):
        # argument wrong type
        mit self.assertRaises(TypeError):
            _zstd.train_dict({}, (), 100)
        mit self.assertRaises(TypeError):
            _zstd.train_dict(bytearray(), (), 100)
        mit self.assertRaises(TypeError):
            _zstd.train_dict(b'', 99, 100)
        mit self.assertRaises(TypeError):
            _zstd.train_dict(b'', [], 100)
        mit self.assertRaises(TypeError):
            _zstd.train_dict(b'', (), 100.1)
        mit self.assertRaises(TypeError):
            _zstd.train_dict(b'', (99.1,), 100)
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'abc', (4, -1), 100)
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'abc', (2,), 100)
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'', (99,), 100)

        # size > size_t
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'', (2**1000,), 100)
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'', (-2**1000,), 100)

        # dict_size <= 0
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'', (), 0)
        mit self.assertRaises(ValueError):
            _zstd.train_dict(b'', (), -1)

        mit self.assertRaises(ZstdError):
            _zstd.train_dict(b'', (), 1)

    def test_finalize_dict_c(self):
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(1, 2, 3, 4, 5)

        # argument wrong type
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict({}, b'', (), 100, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(bytearray(TRAINED_DICT.dict_content), b'', (), 100, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, {}, (), 100, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, bytearray(), (), 100, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', 99, 100, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', [], 100, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 100.1, 5)
        mit self.assertRaises(TypeError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 100, 5.1)

        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'abc', (4, -1), 100, 5)
        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'abc', (2,), 100, 5)
        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (99,), 100, 5)

        # size > size_t
        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (2**1000,), 100, 5)
        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (-2**1000,), 100, 5)

        # dict_size <= 0
        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 0, 5)
        mit self.assertRaises(ValueError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), -1, 5)
        mit self.assertRaises(OverflowError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 2**1000, 5)
        mit self.assertRaises(OverflowError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), -2**1000, 5)

        mit self.assertRaises(OverflowError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 100, 2**1000)
        mit self.assertRaises(OverflowError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 100, -2**1000)

        mit self.assertRaises(ZstdError):
            _zstd.finalize_dict(TRAINED_DICT.dict_content, b'', (), 100, 5)

    def test_train_buffer_protocol_samples(self):
        def _nbytes(dat):
            wenn isinstance(dat, (bytes, bytearray)):
                gib len(dat)
            gib memoryview(dat).nbytes

        # prepare samples
        chunk_lst = []
        wrong_size_lst = []
        correct_size_lst = []
        fuer _ in range(300):
            arr = array.array('Q', [random.randint(0, 20) fuer i in range(20)])
            chunk_lst.append(arr)
            correct_size_lst.append(_nbytes(arr))
            wrong_size_lst.append(len(arr))
        concatenation = b''.join(chunk_lst)

        # wrong size list
        mit self.assertRaisesRegex(ValueError,
                "The samples size tuple doesn't match the concatenation's size"):
            _zstd.train_dict(concatenation, tuple(wrong_size_lst), 100*_1K)

        # correct size list
        _zstd.train_dict(concatenation, tuple(correct_size_lst), 3*_1K)

        # wrong size list
        mit self.assertRaisesRegex(ValueError,
                "The samples size tuple doesn't match the concatenation's size"):
            _zstd.finalize_dict(TRAINED_DICT.dict_content,
                                  concatenation, tuple(wrong_size_lst), 300*_1K, 5)

        # correct size list
        _zstd.finalize_dict(TRAINED_DICT.dict_content,
                              concatenation, tuple(correct_size_lst), 300*_1K, 5)

    def test_as_prefix(self):
        # V1
        V1 = THIS_FILE_BYTES
        zd = ZstdDict(V1, is_raw=Wahr)

        # V2
        mid = len(V1) // 2
        V2 = V1[:mid] + \
             (b'a' wenn V1[mid] != int.from_bytes(b'a') sonst b'b') + \
             V1[mid+1:]

        # compress
        dat = compress(V2, zstd_dict=zd.as_prefix)
        self.assertEqual(get_frame_info(dat).dictionary_id, 0)

        # decompress
        self.assertEqual(decompress(dat, zd.as_prefix), V2)

        # use wrong prefix
        zd2 = ZstdDict(SAMPLES[0], is_raw=Wahr)
        versuch:
            decompressed = decompress(dat, zd2.as_prefix)
        ausser ZstdError: # expected
            pass
        sonst:
            self.assertNotEqual(decompressed, V2)

        # read only attribute
        mit self.assertRaises(AttributeError):
            zd.as_prefix = b'1234'

    def test_as_digested_dict(self):
        zd = TRAINED_DICT

        # test .as_digested_dict
        dat = compress(SAMPLES[0], zstd_dict=zd.as_digested_dict)
        self.assertEqual(decompress(dat, zd.as_digested_dict), SAMPLES[0])
        mit self.assertRaises(AttributeError):
            zd.as_digested_dict = b'1234'

        # test .as_undigested_dict
        dat = compress(SAMPLES[0], zstd_dict=zd.as_undigested_dict)
        self.assertEqual(decompress(dat, zd.as_undigested_dict), SAMPLES[0])
        mit self.assertRaises(AttributeError):
            zd.as_undigested_dict = b'1234'

    def test_advanced_compression_parameters(self):
        options = {CompressionParameter.compression_level: 6,
                  CompressionParameter.window_log: 20,
                  CompressionParameter.enable_long_distance_matching: 1}

        # automatically select
        dat = compress(SAMPLES[0], options=options, zstd_dict=TRAINED_DICT)
        self.assertEqual(decompress(dat, TRAINED_DICT), SAMPLES[0])

        # explicitly select
        dat = compress(SAMPLES[0], options=options, zstd_dict=TRAINED_DICT.as_digested_dict)
        self.assertEqual(decompress(dat, TRAINED_DICT), SAMPLES[0])

    def test_len(self):
        self.assertEqual(len(TRAINED_DICT), len(TRAINED_DICT.dict_content))
        self.assertIn(str(len(TRAINED_DICT)), str(TRAINED_DICT))

klasse FileTestCase(unittest.TestCase):
    def setUp(self):
        self.DECOMPRESSED_42 = b'a'*42
        self.FRAME_42 = compress(self.DECOMPRESSED_42)

    def test_init(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            pass
        mit ZstdFile(io.BytesIO(), "w") als f:
            pass
        mit ZstdFile(io.BytesIO(), "x") als f:
            pass
        mit ZstdFile(io.BytesIO(), "a") als f:
            pass

        mit ZstdFile(io.BytesIO(), "w", level=12) als f:
            pass
        mit ZstdFile(io.BytesIO(), "w", options={CompressionParameter.checksum_flag:1}) als f:
            pass
        mit ZstdFile(io.BytesIO(), "w", options={}) als f:
            pass
        mit ZstdFile(io.BytesIO(), "w", level=20, zstd_dict=TRAINED_DICT) als f:
            pass

        mit ZstdFile(io.BytesIO(), "r", options={DecompressionParameter.window_log_max:25}) als f:
            pass
        mit ZstdFile(io.BytesIO(), "r", options={}, zstd_dict=TRAINED_DICT) als f:
            pass

    def test_init_with_PathLike_filename(self):
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            filename = pathlib.Path(tmp_f.name)

        mit ZstdFile(filename, "a") als f:
            f.write(DECOMPRESSED_100_PLUS_32KB)
        mit ZstdFile(filename) als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB)

        mit ZstdFile(filename, "a") als f:
            f.write(DECOMPRESSED_100_PLUS_32KB)
        mit ZstdFile(filename) als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB * 2)

        os.remove(filename)

    def test_init_with_filename(self):
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            filename = pathlib.Path(tmp_f.name)

        mit ZstdFile(filename) als f:
            pass
        mit ZstdFile(filename, "w") als f:
            pass
        mit ZstdFile(filename, "a") als f:
            pass

        os.remove(filename)

    def test_init_mode(self):
        bi = io.BytesIO()

        mit ZstdFile(bi, "r"):
            pass
        mit ZstdFile(bi, "rb"):
            pass
        mit ZstdFile(bi, "w"):
            pass
        mit ZstdFile(bi, "wb"):
            pass
        mit ZstdFile(bi, "a"):
            pass
        mit ZstdFile(bi, "ab"):
            pass

    def test_init_with_x_mode(self):
        mit tempfile.NamedTemporaryFile() als tmp_f:
            filename = pathlib.Path(tmp_f.name)

        fuer mode in ("x", "xb"):
            mit ZstdFile(filename, mode):
                pass
            mit self.assertRaises(FileExistsError):
                mit ZstdFile(filename, mode):
                    pass
            os.remove(filename)

    def test_init_bad_mode(self):
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), (3, "x"))
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "xt")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "x+")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "rx")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "wx")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "rt")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "r+")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "wt")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "w+")
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "rw")

        mit self.assertRaisesRegex(TypeError,
                                    r"not be a CompressionParameter"):
            ZstdFile(io.BytesIO(), 'rb',
                     options={CompressionParameter.compression_level:5})
        mit self.assertRaisesRegex(TypeError,
                                    r"not be a DecompressionParameter"):
            ZstdFile(io.BytesIO(), 'wb',
                     options={DecompressionParameter.window_log_max:21})

        mit self.assertRaises(TypeError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "r", level=12)

    def test_init_bad_check(self):
        mit self.assertRaises(TypeError):
            ZstdFile(io.BytesIO(), "w", level='asd')
        # CHECK_UNKNOWN und anything above CHECK_ID_MAX should be invalid.
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(), "w", options={999:9999})
        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(), "w", options={CompressionParameter.window_log:99})

        mit self.assertRaises(TypeError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "r", options=33)

        mit self.assertRaises(OverflowError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB),
                             options={DecompressionParameter.window_log_max:2**31})

        mit self.assertRaises(ValueError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB),
                             options={444:333})

        mit self.assertRaises(TypeError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), zstd_dict={1:2})

        mit self.assertRaises(TypeError):
            ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), zstd_dict=b'dict123456')

    def test_init_close_fp(self):
        # get a temp file name
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            tmp_f.write(DAT_130K_C)
            filename = tmp_f.name

        mit self.assertRaises(TypeError):
            ZstdFile(filename, options={'a':'b'})

        # fuer PyPy
        gc.collect()

        os.remove(filename)

    def test_close(self):
        mit io.BytesIO(COMPRESSED_100_PLUS_32KB) als src:
            f = ZstdFile(src)
            f.close()
            # ZstdFile.close() should nicht close the underlying file object.
            self.assertFalsch(src.closed)
            # Try closing an already-closed ZstdFile.
            f.close()
            self.assertFalsch(src.closed)

        # Test mit a real file on disk, opened directly by ZstdFile.
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            filename = pathlib.Path(tmp_f.name)

        f = ZstdFile(filename)
        fp = f._fp
        f.close()
        # Here, ZstdFile.close() *should* close the underlying file object.
        self.assertWahr(fp.closed)
        # Try closing an already-closed ZstdFile.
        f.close()

        os.remove(filename)

    def test_closed(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        versuch:
            self.assertFalsch(f.closed)
            f.read()
            self.assertFalsch(f.closed)
        schliesslich:
            f.close()
        self.assertWahr(f.closed)

        f = ZstdFile(io.BytesIO(), "w")
        versuch:
            self.assertFalsch(f.closed)
        schliesslich:
            f.close()
        self.assertWahr(f.closed)

    def test_fileno(self):
        # 1
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        versuch:
            self.assertRaises(io.UnsupportedOperation, f.fileno)
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.fileno)

        # 2
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            filename = pathlib.Path(tmp_f.name)

        f = ZstdFile(filename)
        versuch:
            self.assertEqual(f.fileno(), f._fp.fileno())
            self.assertIsInstance(f.fileno(), int)
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.fileno)

        os.remove(filename)

        # 3, no .fileno() method
        klasse C:
            def read(self, size=-1):
                gib b'123'
        mit ZstdFile(C(), 'rb') als f:
            mit self.assertRaisesRegex(AttributeError, r'fileno'):
                f.fileno()

    def test_name(self):
        # 1
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        versuch:
            mit self.assertRaises(AttributeError):
                f.name
        schliesslich:
            f.close()
        mit self.assertRaises(ValueError):
            f.name

        # 2
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            filename = pathlib.Path(tmp_f.name)

        f = ZstdFile(filename)
        versuch:
            self.assertEqual(f.name, f._fp.name)
            self.assertIsInstance(f.name, str)
        schliesslich:
            f.close()
        mit self.assertRaises(ValueError):
            f.name

        os.remove(filename)

        # 3, no .filename property
        klasse C:
            def read(self, size=-1):
                gib b'123'
        mit ZstdFile(C(), 'rb') als f:
            mit self.assertRaisesRegex(AttributeError, r'name'):
                f.name

    def test_seekable(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        versuch:
            self.assertWahr(f.seekable())
            f.read()
            self.assertWahr(f.seekable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.seekable)

        f = ZstdFile(io.BytesIO(), "w")
        versuch:
            self.assertFalsch(f.seekable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.seekable)

        src = io.BytesIO(COMPRESSED_100_PLUS_32KB)
        src.seekable = lambda: Falsch
        f = ZstdFile(src)
        versuch:
            self.assertFalsch(f.seekable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.seekable)

    def test_readable(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        versuch:
            self.assertWahr(f.readable())
            f.read()
            self.assertWahr(f.readable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.readable)

        f = ZstdFile(io.BytesIO(), "w")
        versuch:
            self.assertFalsch(f.readable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.readable)

    def test_writable(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        versuch:
            self.assertFalsch(f.writable())
            f.read()
            self.assertFalsch(f.writable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.writable)

        f = ZstdFile(io.BytesIO(), "w")
        versuch:
            self.assertWahr(f.writable())
        schliesslich:
            f.close()
        self.assertRaises(ValueError, f.writable)

    def test_read_0(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            self.assertEqual(f.read(0), b"")
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB)
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB),
                              options={DecompressionParameter.window_log_max:20}) als f:
            self.assertEqual(f.read(0), b"")

        # empty file
        mit ZstdFile(io.BytesIO(b'')) als f:
            self.assertEqual(f.read(0), b"")
            mit self.assertRaises(EOFError):
                f.read(10)

        mit ZstdFile(io.BytesIO(b'')) als f:
            mit self.assertRaises(EOFError):
                f.read(10)

    def test_read_10(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            chunks = []
            waehrend Wahr:
                result = f.read(10)
                wenn nicht result:
                    breche
                self.assertLessEqual(len(result), 10)
                chunks.append(result)
            self.assertEqual(b"".join(chunks), DECOMPRESSED_100_PLUS_32KB)

    def test_read_multistream(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB * 5)) als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB * 5)

        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB + SKIPPABLE_FRAME)) als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB)

        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB + COMPRESSED_DAT)) als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB + DECOMPRESSED_DAT)

    def test_read_incomplete(self):
        mit ZstdFile(io.BytesIO(DAT_130K_C[:-200])) als f:
            self.assertRaises(EOFError, f.read)

        # Trailing data isn't a valid compressed stream
        mit ZstdFile(io.BytesIO(self.FRAME_42 + b'12345')) als f:
            self.assertRaises(ZstdError, f.read)

        mit ZstdFile(io.BytesIO(SKIPPABLE_FRAME + b'12345')) als f:
            self.assertRaises(ZstdError, f.read)

    def test_read_truncated(self):
        # Drop stream epilogue: 4 bytes checksum
        truncated = DAT_130K_C[:-4]
        mit ZstdFile(io.BytesIO(truncated)) als f:
            self.assertRaises(EOFError, f.read)

        mit ZstdFile(io.BytesIO(truncated)) als f:
            # this ist an important test, make sure it doesn't wirf EOFError.
            self.assertEqual(f.read(130*_1K), DAT_130K_D)
            mit self.assertRaises(EOFError):
                f.read(1)

        # Incomplete header
        fuer i in range(1, 20):
            mit ZstdFile(io.BytesIO(truncated[:i])) als f:
                self.assertRaises(EOFError, f.read, 1)

    def test_read_bad_args(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_DAT))
        f.close()
        self.assertRaises(ValueError, f.read)
        mit ZstdFile(io.BytesIO(), "w") als f:
            self.assertRaises(ValueError, f.read)
        mit ZstdFile(io.BytesIO(COMPRESSED_DAT)) als f:
            self.assertRaises(TypeError, f.read, float())

    def test_read_bad_data(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_BOGUS)) als f:
            self.assertRaises(ZstdError, f.read)

    def test_read_exception(self):
        klasse C:
            def read(self, size=-1):
                wirf OSError
        mit ZstdFile(C()) als f:
            mit self.assertRaises(OSError):
                f.read(10)

    def test_read1(self):
        mit ZstdFile(io.BytesIO(DAT_130K_C)) als f:
            blocks = []
            waehrend Wahr:
                result = f.read1()
                wenn nicht result:
                    breche
                blocks.append(result)
            self.assertEqual(b"".join(blocks), DAT_130K_D)
            self.assertEqual(f.read1(), b"")

    def test_read1_0(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_DAT)) als f:
            self.assertEqual(f.read1(0), b"")

    def test_read1_10(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_DAT)) als f:
            blocks = []
            waehrend Wahr:
                result = f.read1(10)
                wenn nicht result:
                    breche
                blocks.append(result)
            self.assertEqual(b"".join(blocks), DECOMPRESSED_DAT)
            self.assertEqual(f.read1(), b"")

    def test_read1_multistream(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB * 5)) als f:
            blocks = []
            waehrend Wahr:
                result = f.read1()
                wenn nicht result:
                    breche
                blocks.append(result)
            self.assertEqual(b"".join(blocks), DECOMPRESSED_100_PLUS_32KB * 5)
            self.assertEqual(f.read1(), b"")

    def test_read1_bad_args(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        f.close()
        self.assertRaises(ValueError, f.read1)
        mit ZstdFile(io.BytesIO(), "w") als f:
            self.assertRaises(ValueError, f.read1)
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            self.assertRaises(TypeError, f.read1, Nichts)

    def test_readinto(self):
        arr = array.array("I", range(100))
        self.assertEqual(len(arr), 100)
        self.assertEqual(len(arr) * arr.itemsize, 400)
        ba = bytearray(300)
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            # 0 length output buffer
            self.assertEqual(f.readinto(ba[0:0]), 0)

            # use correct length fuer buffer protocol object
            self.assertEqual(f.readinto(arr), 400)
            self.assertEqual(arr.tobytes(), DECOMPRESSED_100_PLUS_32KB[:400])

            # normal readinto
            self.assertEqual(f.readinto(ba), 300)
            self.assertEqual(ba, DECOMPRESSED_100_PLUS_32KB[400:700])

    def test_peek(self):
        mit ZstdFile(io.BytesIO(DAT_130K_C)) als f:
            result = f.peek()
            self.assertGreater(len(result), 0)
            self.assertWahr(DAT_130K_D.startswith(result))
            self.assertEqual(f.read(), DAT_130K_D)
        mit ZstdFile(io.BytesIO(DAT_130K_C)) als f:
            result = f.peek(10)
            self.assertGreater(len(result), 0)
            self.assertWahr(DAT_130K_D.startswith(result))
            self.assertEqual(f.read(), DAT_130K_D)

    def test_peek_bad_args(self):
        mit ZstdFile(io.BytesIO(), "w") als f:
            self.assertRaises(ValueError, f.peek)

    def test_iterator(self):
        mit io.BytesIO(THIS_FILE_BYTES) als f:
            lines = f.readlines()
        compressed = compress(THIS_FILE_BYTES)

        # iter
        mit ZstdFile(io.BytesIO(compressed)) als f:
            self.assertListEqual(list(iter(f)), lines)

        # readline
        mit ZstdFile(io.BytesIO(compressed)) als f:
            fuer line in lines:
                self.assertEqual(f.readline(), line)
            self.assertEqual(f.readline(), b'')
            self.assertEqual(f.readline(), b'')

        # readlines
        mit ZstdFile(io.BytesIO(compressed)) als f:
            self.assertListEqual(f.readlines(), lines)

    def test_decompress_limited(self):
        _ZSTD_DStreamInSize = 128*_1K + 3

        bomb = compress(b'\0' * int(2e6), level=10)
        self.assertLess(len(bomb), _ZSTD_DStreamInSize)

        decomp = ZstdFile(io.BytesIO(bomb))
        self.assertEqual(decomp.read(1), b'\0')

        # BufferedReader uses 128 KiB buffer in __init__.py
        max_decomp = 128*_1K
        self.assertLessEqual(decomp._buffer.raw.tell(), max_decomp,
            "Excessive amount of data was decompressed")

    def test_write(self):
        raw_data = THIS_FILE_BYTES[: len(THIS_FILE_BYTES) // 6]
        mit io.BytesIO() als dst:
            mit ZstdFile(dst, "w") als f:
                f.write(raw_data)

            comp = ZstdCompressor()
            expected = comp.compress(raw_data) + comp.flush()
            self.assertEqual(dst.getvalue(), expected)

        mit io.BytesIO() als dst:
            mit ZstdFile(dst, "w", level=12) als f:
                f.write(raw_data)

            comp = ZstdCompressor(12)
            expected = comp.compress(raw_data) + comp.flush()
            self.assertEqual(dst.getvalue(), expected)

        mit io.BytesIO() als dst:
            mit ZstdFile(dst, "w", options={CompressionParameter.checksum_flag:1}) als f:
                f.write(raw_data)

            comp = ZstdCompressor(options={CompressionParameter.checksum_flag:1})
            expected = comp.compress(raw_data) + comp.flush()
            self.assertEqual(dst.getvalue(), expected)

        mit io.BytesIO() als dst:
            options = {CompressionParameter.compression_level:-5,
                      CompressionParameter.checksum_flag:1}
            mit ZstdFile(dst, "w",
                          options=options) als f:
                f.write(raw_data)

            comp = ZstdCompressor(options=options)
            expected = comp.compress(raw_data) + comp.flush()
            self.assertEqual(dst.getvalue(), expected)

    def test_write_empty_frame(self):
        # .FLUSH_FRAME generates an empty content frame
        c = ZstdCompressor()
        self.assertNotEqual(c.flush(c.FLUSH_FRAME), b'')
        self.assertNotEqual(c.flush(c.FLUSH_FRAME), b'')

        # don't generate empty content frame
        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            pass
        self.assertEqual(bo.getvalue(), b'')

        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            f.flush(f.FLUSH_FRAME)
        self.assertEqual(bo.getvalue(), b'')

        # wenn .write(b''), generate empty content frame
        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            f.write(b'')
        self.assertNotEqual(bo.getvalue(), b'')

        # has an empty content frame
        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            f.flush(f.FLUSH_BLOCK)
        self.assertNotEqual(bo.getvalue(), b'')

    def test_write_empty_block(self):
        # If no internal data, .FLUSH_BLOCK gib b''.
        c = ZstdCompressor()
        self.assertEqual(c.flush(c.FLUSH_BLOCK), b'')
        self.assertNotEqual(c.compress(b'123', c.FLUSH_BLOCK),
                            b'')
        self.assertEqual(c.flush(c.FLUSH_BLOCK), b'')
        self.assertEqual(c.compress(b''), b'')
        self.assertEqual(c.compress(b''), b'')
        self.assertEqual(c.flush(c.FLUSH_BLOCK), b'')

        # mode = .last_mode
        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            f.write(b'123')
            f.flush(f.FLUSH_BLOCK)
            fp_pos = f._fp.tell()
            self.assertNotEqual(fp_pos, 0)
            f.flush(f.FLUSH_BLOCK)
            self.assertEqual(f._fp.tell(), fp_pos)

        # mode != .last_mode
        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            f.flush(f.FLUSH_BLOCK)
            self.assertEqual(f._fp.tell(), 0)
            f.write(b'')
            f.flush(f.FLUSH_BLOCK)
            self.assertEqual(f._fp.tell(), 0)

    def test_write_101(self):
        mit io.BytesIO() als dst:
            mit ZstdFile(dst, "w") als f:
                fuer start in range(0, len(THIS_FILE_BYTES), 101):
                    f.write(THIS_FILE_BYTES[start:start+101])

            comp = ZstdCompressor()
            expected = comp.compress(THIS_FILE_BYTES) + comp.flush()
            self.assertEqual(dst.getvalue(), expected)

    def test_write_append(self):
        def comp(data):
            comp = ZstdCompressor()
            gib comp.compress(data) + comp.flush()

        part1 = THIS_FILE_BYTES[:_1K]
        part2 = THIS_FILE_BYTES[_1K:1536]
        part3 = THIS_FILE_BYTES[1536:]
        expected = b"".join(comp(x) fuer x in (part1, part2, part3))
        mit io.BytesIO() als dst:
            mit ZstdFile(dst, "w") als f:
                f.write(part1)
            mit ZstdFile(dst, "a") als f:
                f.write(part2)
            mit ZstdFile(dst, "a") als f:
                f.write(part3)
            self.assertEqual(dst.getvalue(), expected)

    def test_write_bad_args(self):
        f = ZstdFile(io.BytesIO(), "w")
        f.close()
        self.assertRaises(ValueError, f.write, b"foo")
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB), "r") als f:
            self.assertRaises(ValueError, f.write, b"bar")
        mit ZstdFile(io.BytesIO(), "w") als f:
            self.assertRaises(TypeError, f.write, Nichts)
            self.assertRaises(TypeError, f.write, "text")
            self.assertRaises(TypeError, f.write, 789)

    def test_writelines(self):
        def comp(data):
            comp = ZstdCompressor()
            gib comp.compress(data) + comp.flush()

        mit io.BytesIO(THIS_FILE_BYTES) als f:
            lines = f.readlines()
        mit io.BytesIO() als dst:
            mit ZstdFile(dst, "w") als f:
                f.writelines(lines)
            expected = comp(THIS_FILE_BYTES)
            self.assertEqual(dst.getvalue(), expected)

    def test_seek_forward(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.seek(555)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB[555:])

    def test_seek_forward_across_streams(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB * 2)) als f:
            f.seek(len(DECOMPRESSED_100_PLUS_32KB) + 123)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB[123:])

    def test_seek_forward_relative_to_current(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.read(100)
            f.seek(1236, 1)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB[1336:])

    def test_seek_forward_relative_to_end(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.seek(-555, 2)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB[-555:])

    def test_seek_backward(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.read(1001)
            f.seek(211)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB[211:])

    def test_seek_backward_across_streams(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB * 2)) als f:
            f.read(len(DECOMPRESSED_100_PLUS_32KB) + 333)
            f.seek(737)
            self.assertEqual(f.read(),
              DECOMPRESSED_100_PLUS_32KB[737:] + DECOMPRESSED_100_PLUS_32KB)

    def test_seek_backward_relative_to_end(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.seek(-150, 2)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB[-150:])

    def test_seek_past_end(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.seek(len(DECOMPRESSED_100_PLUS_32KB) + 9001)
            self.assertEqual(f.tell(), len(DECOMPRESSED_100_PLUS_32KB))
            self.assertEqual(f.read(), b"")

    def test_seek_past_start(self):
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            f.seek(-88)
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB)

    def test_seek_bad_args(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        f.close()
        self.assertRaises(ValueError, f.seek, 0)
        mit ZstdFile(io.BytesIO(), "w") als f:
            self.assertRaises(ValueError, f.seek, 0)
        mit ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB)) als f:
            self.assertRaises(ValueError, f.seek, 0, 3)
            # io.BufferedReader raises TypeError instead of ValueError
            self.assertRaises((TypeError, ValueError), f.seek, 9, ())
            self.assertRaises(TypeError, f.seek, Nichts)
            self.assertRaises(TypeError, f.seek, b"derp")

    def test_seek_not_seekable(self):
        klasse C(io.BytesIO):
            def seekable(self):
                gib Falsch
        obj = C(COMPRESSED_100_PLUS_32KB)
        mit ZstdFile(obj, 'r') als f:
            d = f.read(1)
            self.assertFalsch(f.seekable())
            mit self.assertRaisesRegex(io.UnsupportedOperation,
                                        'File oder stream ist nicht seekable'):
                f.seek(0)
            d += f.read()
            self.assertEqual(d, DECOMPRESSED_100_PLUS_32KB)

    def test_tell(self):
        mit ZstdFile(io.BytesIO(DAT_130K_C)) als f:
            pos = 0
            waehrend Wahr:
                self.assertEqual(f.tell(), pos)
                result = f.read(random.randint(171, 189))
                wenn nicht result:
                    breche
                pos += len(result)
            self.assertEqual(f.tell(), len(DAT_130K_D))
        mit ZstdFile(io.BytesIO(), "w") als f:
            fuer pos in range(0, len(DAT_130K_D), 143):
                self.assertEqual(f.tell(), pos)
                f.write(DAT_130K_D[pos:pos+143])
            self.assertEqual(f.tell(), len(DAT_130K_D))

    def test_tell_bad_args(self):
        f = ZstdFile(io.BytesIO(COMPRESSED_100_PLUS_32KB))
        f.close()
        self.assertRaises(ValueError, f.tell)

    def test_file_dict(self):
        # default
        bi = io.BytesIO()
        mit ZstdFile(bi, 'w', zstd_dict=TRAINED_DICT) als f:
            f.write(SAMPLES[0])
        bi.seek(0)
        mit ZstdFile(bi, zstd_dict=TRAINED_DICT) als f:
            dat = f.read()
        self.assertEqual(dat, SAMPLES[0])

        # .as_(un)digested_dict
        bi = io.BytesIO()
        mit ZstdFile(bi, 'w', zstd_dict=TRAINED_DICT.as_digested_dict) als f:
            f.write(SAMPLES[0])
        bi.seek(0)
        mit ZstdFile(bi, zstd_dict=TRAINED_DICT.as_undigested_dict) als f:
            dat = f.read()
        self.assertEqual(dat, SAMPLES[0])

    def test_file_prefix(self):
        bi = io.BytesIO()
        mit ZstdFile(bi, 'w', zstd_dict=TRAINED_DICT.as_prefix) als f:
            f.write(SAMPLES[0])
        bi.seek(0)
        mit ZstdFile(bi, zstd_dict=TRAINED_DICT.as_prefix) als f:
            dat = f.read()
        self.assertEqual(dat, SAMPLES[0])

    def test_UnsupportedOperation(self):
        # 1
        mit ZstdFile(io.BytesIO(), 'r') als f:
            mit self.assertRaises(io.UnsupportedOperation):
                f.write(b'1234')

        # 2
        klasse T:
            def read(self, size):
                gib b'a' * size

        mit self.assertRaises(TypeError): # on creation
            mit ZstdFile(T(), 'w') als f:
                pass

        # 3
        mit ZstdFile(io.BytesIO(), 'w') als f:
            mit self.assertRaises(io.UnsupportedOperation):
                f.read(100)
            mit self.assertRaises(io.UnsupportedOperation):
                f.seek(100)
        self.assertEqual(f.closed, Wahr)
        mit self.assertRaises(ValueError):
            f.readable()
        mit self.assertRaises(ValueError):
            f.tell()
        mit self.assertRaises(ValueError):
            f.read(100)

    def test_read_readinto_readinto1(self):
        lst = []
        mit ZstdFile(io.BytesIO(COMPRESSED_THIS_FILE*5)) als f:
            waehrend Wahr:
                method = random.randint(0, 2)
                size = random.randint(0, 300)

                wenn method == 0:
                    dat = f.read(size)
                    wenn nicht dat und size:
                        breche
                    lst.append(dat)
                sowenn method == 1:
                    ba = bytearray(size)
                    read_size = f.readinto(ba)
                    wenn read_size == 0 und size:
                        breche
                    lst.append(bytes(ba[:read_size]))
                sowenn method == 2:
                    ba = bytearray(size)
                    read_size = f.readinto1(ba)
                    wenn read_size == 0 und size:
                        breche
                    lst.append(bytes(ba[:read_size]))
        self.assertEqual(b''.join(lst), THIS_FILE_BYTES*5)

    def test_zstdfile_flush(self):
        # closed
        f = ZstdFile(io.BytesIO(), 'w')
        f.close()
        mit self.assertRaises(ValueError):
            f.flush()

        # read
        mit ZstdFile(io.BytesIO(), 'r') als f:
            # does nothing fuer read-only stream
            f.flush()

        # write
        DAT = b'abcd'
        bi = io.BytesIO()
        mit ZstdFile(bi, 'w') als f:
            self.assertEqual(f.write(DAT), len(DAT))
            self.assertEqual(f.tell(), len(DAT))
            self.assertEqual(bi.tell(), 0) # nicht enough fuer a block

            self.assertEqual(f.flush(), Nichts)
            self.assertEqual(f.tell(), len(DAT))
            self.assertGreater(bi.tell(), 0) # flushed

        # write, no .flush() method
        klasse C:
            def write(self, b):
                gib len(b)
        mit ZstdFile(C(), 'w') als f:
            self.assertEqual(f.write(DAT), len(DAT))
            self.assertEqual(f.tell(), len(DAT))

            self.assertEqual(f.flush(), Nichts)
            self.assertEqual(f.tell(), len(DAT))

    def test_zstdfile_flush_mode(self):
        self.assertEqual(ZstdFile.FLUSH_BLOCK, ZstdCompressor.FLUSH_BLOCK)
        self.assertEqual(ZstdFile.FLUSH_FRAME, ZstdCompressor.FLUSH_FRAME)
        mit self.assertRaises(AttributeError):
            ZstdFile.CONTINUE

        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            # flush block
            self.assertEqual(f.write(b'123'), 3)
            self.assertIsNichts(f.flush(f.FLUSH_BLOCK))
            p1 = bo.tell()
            # mode == .last_mode, should gib
            self.assertIsNichts(f.flush())
            p2 = bo.tell()
            self.assertEqual(p1, p2)
            # flush frame
            self.assertEqual(f.write(b'456'), 3)
            self.assertIsNichts(f.flush(mode=f.FLUSH_FRAME))
            # flush frame
            self.assertEqual(f.write(b'789'), 3)
            self.assertIsNichts(f.flush(f.FLUSH_FRAME))
            p1 = bo.tell()
            # mode == .last_mode, should gib
            self.assertIsNichts(f.flush(f.FLUSH_FRAME))
            p2 = bo.tell()
            self.assertEqual(p1, p2)
        self.assertEqual(decompress(bo.getvalue()), b'123456789')

        bo = io.BytesIO()
        mit ZstdFile(bo, 'w') als f:
            f.write(b'123')
            mit self.assertRaisesRegex(ValueError, r'\.FLUSH_.*?\.FLUSH_'):
                f.flush(ZstdCompressor.CONTINUE)
            mit self.assertRaises(ValueError):
                f.flush(-1)
            mit self.assertRaises(ValueError):
                f.flush(123456)
            mit self.assertRaises(TypeError):
                f.flush(node=ZstdCompressor.CONTINUE)
            mit self.assertRaises((TypeError, ValueError)):
                f.flush('FLUSH_FRAME')
            mit self.assertRaises(TypeError):
                f.flush(b'456', f.FLUSH_BLOCK)

    def test_zstdfile_truncate(self):
        mit ZstdFile(io.BytesIO(), 'w') als f:
            mit self.assertRaises(io.UnsupportedOperation):
                f.truncate(200)

    def test_zstdfile_iter_issue45475(self):
        lines = [l fuer l in ZstdFile(io.BytesIO(COMPRESSED_THIS_FILE))]
        self.assertGreater(len(lines), 0)

    def test_append_new_file(self):
        mit tempfile.NamedTemporaryFile(delete=Wahr) als tmp_f:
            filename = tmp_f.name

        mit ZstdFile(filename, 'a') als f:
            pass
        self.assertWahr(os.path.isfile(filename))

        os.remove(filename)

klasse OpenTestCase(unittest.TestCase):

    def test_binary_modes(self):
        mit open(io.BytesIO(COMPRESSED_100_PLUS_32KB), "rb") als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB)
        mit io.BytesIO() als bio:
            mit open(bio, "wb") als f:
                f.write(DECOMPRESSED_100_PLUS_32KB)
            file_data = decompress(bio.getvalue())
            self.assertEqual(file_data, DECOMPRESSED_100_PLUS_32KB)
            mit open(bio, "ab") als f:
                f.write(DECOMPRESSED_100_PLUS_32KB)
            file_data = decompress(bio.getvalue())
            self.assertEqual(file_data, DECOMPRESSED_100_PLUS_32KB * 2)

    def test_text_modes(self):
        # empty input
        mit self.assertRaises(EOFError):
            mit open(io.BytesIO(b''), "rt", encoding="utf-8", newline='\n') als reader:
                fuer _ in reader:
                    pass

        # read
        uncompressed = THIS_FILE_STR.replace(os.linesep, "\n")
        mit open(io.BytesIO(COMPRESSED_THIS_FILE), "rt", encoding="utf-8") als f:
            self.assertEqual(f.read(), uncompressed)

        mit io.BytesIO() als bio:
            # write
            mit open(bio, "wt", encoding="utf-8") als f:
                f.write(uncompressed)
            file_data = decompress(bio.getvalue()).decode("utf-8")
            self.assertEqual(file_data.replace(os.linesep, "\n"), uncompressed)
            # append
            mit open(bio, "at", encoding="utf-8") als f:
                f.write(uncompressed)
            file_data = decompress(bio.getvalue()).decode("utf-8")
            self.assertEqual(file_data.replace(os.linesep, "\n"), uncompressed * 2)

    def test_bad_params(self):
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            TESTFN = pathlib.Path(tmp_f.name)

        mit self.assertRaises(ValueError):
            open(TESTFN, "")
        mit self.assertRaises(ValueError):
            open(TESTFN, "rbt")
        mit self.assertRaises(ValueError):
            open(TESTFN, "rb", encoding="utf-8")
        mit self.assertRaises(ValueError):
            open(TESTFN, "rb", errors="ignore")
        mit self.assertRaises(ValueError):
            open(TESTFN, "rb", newline="\n")

        os.remove(TESTFN)

    def test_option(self):
        options = {DecompressionParameter.window_log_max:25}
        mit open(io.BytesIO(COMPRESSED_100_PLUS_32KB), "rb", options=options) als f:
            self.assertEqual(f.read(), DECOMPRESSED_100_PLUS_32KB)

        options = {CompressionParameter.compression_level:12}
        mit io.BytesIO() als bio:
            mit open(bio, "wb", options=options) als f:
                f.write(DECOMPRESSED_100_PLUS_32KB)
            file_data = decompress(bio.getvalue())
            self.assertEqual(file_data, DECOMPRESSED_100_PLUS_32KB)

    def test_encoding(self):
        uncompressed = THIS_FILE_STR.replace(os.linesep, "\n")

        mit io.BytesIO() als bio:
            mit open(bio, "wt", encoding="utf-16-le") als f:
                f.write(uncompressed)
            file_data = decompress(bio.getvalue()).decode("utf-16-le")
            self.assertEqual(file_data.replace(os.linesep, "\n"), uncompressed)
            bio.seek(0)
            mit open(bio, "rt", encoding="utf-16-le") als f:
                self.assertEqual(f.read().replace(os.linesep, "\n"), uncompressed)

    def test_encoding_error_handler(self):
        mit io.BytesIO(compress(b"foo\xffbar")) als bio:
            mit open(bio, "rt", encoding="ascii", errors="ignore") als f:
                self.assertEqual(f.read(), "foobar")

    def test_newline(self):
        # Test mit explicit newline (universal newline mode disabled).
        text = THIS_FILE_STR.replace(os.linesep, "\n")
        mit io.BytesIO() als bio:
            mit open(bio, "wt", encoding="utf-8", newline="\n") als f:
                f.write(text)
            bio.seek(0)
            mit open(bio, "rt", encoding="utf-8", newline="\r") als f:
                self.assertEqual(f.readlines(), [text])

    def test_x_mode(self):
        mit tempfile.NamedTemporaryFile(delete=Falsch) als tmp_f:
            TESTFN = pathlib.Path(tmp_f.name)

        fuer mode in ("x", "xb", "xt"):
            os.remove(TESTFN)

            wenn mode == "xt":
                encoding = "utf-8"
            sonst:
                encoding = Nichts
            mit open(TESTFN, mode, encoding=encoding):
                pass
            mit self.assertRaises(FileExistsError):
                mit open(TESTFN, mode):
                    pass

        os.remove(TESTFN)

    def test_open_dict(self):
        # default
        bi = io.BytesIO()
        mit open(bi, 'w', zstd_dict=TRAINED_DICT) als f:
            f.write(SAMPLES[0])
        bi.seek(0)
        mit open(bi, zstd_dict=TRAINED_DICT) als f:
            dat = f.read()
        self.assertEqual(dat, SAMPLES[0])

        # .as_(un)digested_dict
        bi = io.BytesIO()
        mit open(bi, 'w', zstd_dict=TRAINED_DICT.as_digested_dict) als f:
            f.write(SAMPLES[0])
        bi.seek(0)
        mit open(bi, zstd_dict=TRAINED_DICT.as_undigested_dict) als f:
            dat = f.read()
        self.assertEqual(dat, SAMPLES[0])

        # invalid dictionary
        bi = io.BytesIO()
        mit self.assertRaisesRegex(TypeError, 'zstd_dict'):
            open(bi, 'w', zstd_dict={1:2, 2:3})

        mit self.assertRaisesRegex(TypeError, 'zstd_dict'):
            open(bi, 'w', zstd_dict=b'1234567890')

    def test_open_prefix(self):
        bi = io.BytesIO()
        mit open(bi, 'w', zstd_dict=TRAINED_DICT.as_prefix) als f:
            f.write(SAMPLES[0])
        bi.seek(0)
        mit open(bi, zstd_dict=TRAINED_DICT.as_prefix) als f:
            dat = f.read()
        self.assertEqual(dat, SAMPLES[0])

    def test_buffer_protocol(self):
        # don't use len() fuer buffer protocol objects
        arr = array.array("i", range(1000))
        LENGTH = len(arr) * arr.itemsize

        mit open(io.BytesIO(), "wb") als f:
            self.assertEqual(f.write(arr), LENGTH)
            self.assertEqual(f.tell(), LENGTH)

klasse FreeThreadingMethodTests(unittest.TestCase):

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_compress_locking(self):
        input = b'a'* (16*_1K)
        num_threads = 8

        # gh-136394: the first output of .compress() includes the frame header
        # we run the first .compress() call outside of the threaded portion
        # to make the test order-independent

        comp = ZstdCompressor()
        parts = [comp.compress(input, ZstdCompressor.FLUSH_BLOCK)]
        fuer _ in range(num_threads):
            res = comp.compress(input, ZstdCompressor.FLUSH_BLOCK)
            wenn res:
                parts.append(res)
        rest1 = comp.flush()
        expected = b''.join(parts) + rest1

        comp = ZstdCompressor()
        output = [comp.compress(input, ZstdCompressor.FLUSH_BLOCK)]
        def run_method(method, input_data, output_data):
            res = method(input_data, ZstdCompressor.FLUSH_BLOCK)
            wenn res:
                output_data.append(res)
        threads = []

        fuer i in range(num_threads):
            thread = threading.Thread(target=run_method, args=(comp.compress, input, output))

            threads.append(thread)

        mit threading_helper.start_threads(threads):
            pass

        rest2 = comp.flush()
        self.assertEqual(rest1, rest2)
        actual = b''.join(output) + rest2
        self.assertEqual(expected, actual)

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_decompress_locking(self):
        input = compress(b'a'* (16*_1K))
        num_threads = 8
        # to ensure we decompress over multiple calls, set maxsize
        window_size = _1K * 16//num_threads

        decomp = ZstdDecompressor()
        parts = []
        fuer _ in range(num_threads):
            res = decomp.decompress(input, window_size)
            wenn res:
                parts.append(res)
        expected = b''.join(parts)

        comp = ZstdDecompressor()
        output = []
        def run_method(method, input_data, output_data):
            res = method(input_data, window_size)
            wenn res:
                output_data.append(res)
        threads = []

        fuer i in range(num_threads):
            thread = threading.Thread(target=run_method, args=(comp.decompress, input, output))

            threads.append(thread)

        mit threading_helper.start_threads(threads):
            pass

        actual = b''.join(output)
        self.assertEqual(expected, actual)

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_compress_shared_dict(self):
        num_threads = 8

        def run_method(b):
            level = threading.get_ident() % 4
            # sync threads to increase chance of contention on
            # capsule storing dictionary levels
            b.wait()
            ZstdCompressor(level=level,
                           zstd_dict=TRAINED_DICT.as_digested_dict)
            b.wait()
            ZstdCompressor(level=level,
                           zstd_dict=TRAINED_DICT.as_undigested_dict)
            b.wait()
            ZstdCompressor(level=level,
                           zstd_dict=TRAINED_DICT.as_prefix)
        threads = []

        b = threading.Barrier(num_threads)
        fuer i in range(num_threads):
            thread = threading.Thread(target=run_method, args=(b,))

            threads.append(thread)

        mit threading_helper.start_threads(threads):
            pass

    @threading_helper.reap_threads
    @threading_helper.requires_working_threading()
    def test_decompress_shared_dict(self):
        num_threads = 8

        def run_method(b):
            # sync threads to increase chance of contention on
            # decompression dictionary
            b.wait()
            ZstdDecompressor(zstd_dict=TRAINED_DICT.as_digested_dict)
            b.wait()
            ZstdDecompressor(zstd_dict=TRAINED_DICT.as_undigested_dict)
            b.wait()
            ZstdDecompressor(zstd_dict=TRAINED_DICT.as_prefix)
        threads = []

        b = threading.Barrier(num_threads)
        fuer i in range(num_threads):
            thread = threading.Thread(target=run_method, args=(b,))

            threads.append(thread)

        mit threading_helper.start_threads(threads):
            pass


wenn __name__ == "__main__":
    unittest.main()
