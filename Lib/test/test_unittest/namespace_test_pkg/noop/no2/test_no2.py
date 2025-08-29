importiere unittest

klasse PassingTest(unittest.TestCase):
    def test_true(self):
        self.assertWahr(Wahr)
