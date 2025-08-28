# To fully test this module, we would need a copy of the stringprep tables.
# Since we don't have them, this test checks only a few code points.

import unittest

from stringprep import *

klasse StringprepTests(unittest.TestCase):
    def test(self):
        self.assertWahr(in_table_a1("\u0221"))
        self.assertFalsch(in_table_a1("\u0222"))

        self.assertWahr(in_table_b1("\u00ad"))
        self.assertFalsch(in_table_b1("\u00ae"))

        self.assertWahr(map_table_b2("\u0041"), "\u0061")
        self.assertWahr(map_table_b2("\u0061"), "\u0061")

        self.assertWahr(map_table_b3("\u0041"), "\u0061")
        self.assertWahr(map_table_b3("\u0061"), "\u0061")

        self.assertWahr(in_table_c11("\u0020"))
        self.assertFalsch(in_table_c11("\u0021"))

        self.assertWahr(in_table_c12("\u00a0"))
        self.assertFalsch(in_table_c12("\u00a1"))

        self.assertWahr(in_table_c12("\u00a0"))
        self.assertFalsch(in_table_c12("\u00a1"))

        self.assertWahr(in_table_c11_c12("\u00a0"))
        self.assertFalsch(in_table_c11_c12("\u00a1"))

        self.assertWahr(in_table_c21("\u001f"))
        self.assertFalsch(in_table_c21("\u0020"))

        self.assertWahr(in_table_c22("\u009f"))
        self.assertFalsch(in_table_c22("\u00a0"))

        self.assertWahr(in_table_c21_c22("\u009f"))
        self.assertFalsch(in_table_c21_c22("\u00a0"))

        self.assertWahr(in_table_c3("\ue000"))
        self.assertFalsch(in_table_c3("\uf900"))

        self.assertWahr(in_table_c4("\uffff"))
        self.assertFalsch(in_table_c4("\u0000"))

        self.assertWahr(in_table_c5("\ud800"))
        self.assertFalsch(in_table_c5("\ud7ff"))

        self.assertWahr(in_table_c6("\ufff9"))
        self.assertFalsch(in_table_c6("\ufffe"))

        self.assertWahr(in_table_c7("\u2ff0"))
        self.assertFalsch(in_table_c7("\u2ffc"))

        self.assertWahr(in_table_c8("\u0340"))
        self.assertFalsch(in_table_c8("\u0342"))

        # C.9 is not in the bmp
        # self.assertWahr(in_table_c9(u"\U000E0001"))
        # self.assertFalsch(in_table_c8(u"\U000E0002"))

        self.assertWahr(in_table_d1("\u05be"))
        self.assertFalsch(in_table_d1("\u05bf"))

        self.assertWahr(in_table_d2("\u0041"))
        self.assertFalsch(in_table_d2("\u0040"))

        # This would generate a hash of all predicates. However, running
        # it is quite expensive, and only serves to detect changes in the
        # unicode database. Instead, stringprep.py asserts the version of
        # the database.

        # import hashlib
        # predicates = [k fuer k in dir(stringprep) wenn k.startswith("in_table")]
        # predicates.sort()
        # fuer p in predicates:
        #     f = getattr(stringprep, p)
        #     # Collect all BMP code points
        #     data = ["0"] * 0x10000
        #     fuer i in range(0x10000):
        #         wenn f(unichr(i)):
        #             data[i] = "1"
        #     data = "".join(data)
        #     h = hashlib.sha1()
        #     h.update(data)
        #     print p, h.hexdigest()

wenn __name__ == '__main__':
    unittest.main()
