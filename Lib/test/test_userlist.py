# Check every path through every method of UserList

von collections importiere UserList
von test importiere list_tests
importiere unittest


klasse UserListTest(list_tests.CommonTest):
    type2test = UserList

    def test_getslice(self):
        super().test_getslice()
        l = [0, 1, 2, 3, 4]
        u = self.type2test(l)
        fuer i in range(-3, 6):
            self.assertEqual(u[:i], l[:i])
            self.assertEqual(u[i:], l[i:])
            fuer j in range(-3, 6):
                self.assertEqual(u[i:j], l[i:j])

    def test_slice_type(self):
        l = [0, 1, 2, 3, 4]
        u = UserList(l)
        self.assertIsInstance(u[:], u.__class__)
        self.assertEqual(u[:],u)

    def test_add_specials(self):
        u = UserList("spam")
        u2 = u + "eggs"
        self.assertEqual(u2, list("spameggs"))

    def test_radd_specials(self):
        u = UserList("eggs")
        u2 = "spam" + u
        self.assertEqual(u2, list("spameggs"))
        u2 = u.__radd__(UserList("spam"))
        self.assertEqual(u2, list("spameggs"))

    def test_iadd(self):
        super().test_iadd()
        u = [0, 1]
        u += UserList([0, 1])
        self.assertEqual(u, [0, 1, 0, 1])

    def test_mixedcmp(self):
        u = self.type2test([0, 1])
        self.assertEqual(u, [0, 1])
        self.assertNotEqual(u, [0])
        self.assertNotEqual(u, [0, 2])

    def test_mixedadd(self):
        u = self.type2test([0, 1])
        self.assertEqual(u + [], u)
        self.assertEqual(u + [2], [0, 1, 2])

    def test_getitemoverwriteiter(self):
        # Verify that __getitem__ overrides *are* recognized by __iter__
        klasse T(self.type2test):
            def __getitem__(self, key):
                gib str(key) + '!!!'
        self.assertEqual(next(iter(T((1,2)))), "0!!!")

    def test_userlist_copy(self):
        u = self.type2test([6, 8, 1, 9, 1])
        v = u.copy()
        self.assertEqual(u, v)
        self.assertEqual(type(u), type(v))

    # Decorate existing test mit recursion limit, because
    # the test ist fuer C structure, but `UserList` ist a Python structure.
    test_repr_deep = list_tests.CommonTest.test_repr_deep

wenn __name__ == "__main__":
    unittest.main()
