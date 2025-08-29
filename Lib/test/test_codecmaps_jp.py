#
# test_codecmaps_jp.py
#   Codec mapping tests fuer Japanese encodings
#

von test importiere multibytecodec_support
importiere unittest

klasse TestCP932Map(multibytecodec_support.TestBase_Mapping,
                   unittest.TestCase):
    encoding = 'cp932'
    mapfileurl = 'http://www.pythontest.net/unicode/CP932.TXT'
    supmaps = [
        (b'\x80', '\u0080'),
        (b'\xa0', '\uf8f0'),
        (b'\xfd', '\uf8f1'),
        (b'\xfe', '\uf8f2'),
        (b'\xff', '\uf8f3'),
    ]
    fuer i in range(0xa1, 0xe0):
        supmaps.append((bytes([i]), chr(i+0xfec0)))


klasse TestEUCJPCOMPATMap(multibytecodec_support.TestBase_Mapping,
                         unittest.TestCase):
    encoding = 'euc_jp'
    mapfilename = 'EUC-JP.TXT'
    mapfileurl = 'http://www.pythontest.net/unicode/EUC-JP.TXT'


klasse TestSJISCOMPATMap(multibytecodec_support.TestBase_Mapping,
                        unittest.TestCase):
    encoding = 'shift_jis'
    mapfilename = 'SHIFTJIS.TXT'
    mapfileurl = 'http://www.pythontest.net/unicode/SHIFTJIS.TXT'
    pass_enctest = [
        (b'\x81_', '\\'),
    ]
    pass_dectest = [
        (b'\\', '\xa5'),
        (b'~', '\u203e'),
        (b'\x81_', '\\'),
    ]

klasse TestEUCJISX0213Map(multibytecodec_support.TestBase_Mapping,
                         unittest.TestCase):
    encoding = 'euc_jisx0213'
    mapfilename = 'EUC-JISX0213.TXT'
    mapfileurl = 'http://www.pythontest.net/unicode/EUC-JISX0213.TXT'


klasse TestSJISX0213Map(multibytecodec_support.TestBase_Mapping,
                       unittest.TestCase):
    encoding = 'shift_jisx0213'
    mapfilename = 'SHIFT_JISX0213.TXT'
    mapfileurl = 'http://www.pythontest.net/unicode/SHIFT_JISX0213.TXT'


wenn __name__ == "__main__":
    unittest.main()
