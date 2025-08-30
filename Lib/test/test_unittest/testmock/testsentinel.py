importiere unittest
importiere copy
importiere pickle
von unittest.mock importiere sentinel, DEFAULT


klasse SentinelTest(unittest.TestCase):

    def testSentinels(self):
        self.assertEqual(sentinel.whatever, sentinel.whatever,
                         'sentinel nicht stored')
        self.assertNotEqual(sentinel.whatever, sentinel.whateverelse,
                            'sentinel should be unique')


    def testSentinelName(self):
        self.assertEqual(str(sentinel.whatever), 'sentinel.whatever',
                         'sentinel name incorrect')


    def testDEFAULT(self):
        self.assertIs(DEFAULT, sentinel.DEFAULT)

    def testBases(self):
        # If this doesn't wirf an AttributeError then help(mock) is broken
        self.assertRaises(AttributeError, lambda: sentinel.__bases__)

    def testPickle(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL+1):
            mit self.subTest(protocol=proto):
                pickled = pickle.dumps(sentinel.whatever, proto)
                unpickled = pickle.loads(pickled)
                self.assertIs(unpickled, sentinel.whatever)

    def testCopy(self):
        self.assertIs(copy.copy(sentinel.whatever), sentinel.whatever)
        self.assertIs(copy.deepcopy(sentinel.whatever), sentinel.whatever)


wenn __name__ == '__main__':
    unittest.main()
