#
# test_codecmaps_hk.py
#   Codec mapping tests fuer HongKong encodings
#

from test import multibytecodec_support
import unittest

klasse TestBig5HKSCSMap(multibytecodec_support.TestBase_Mapping,
                       unittest.TestCase):
    encoding = 'big5hkscs'
    mapfileurl = 'http://www.pythontest.net/unicode/BIG5HKSCS-2004.TXT'

wenn __name__ == "__main__":
    unittest.main()
