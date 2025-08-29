# Test the windows specific win32reg module.
# Only win32reg functions nicht hit here: FlushKey, LoadKey und SaveKey

importiere gc
importiere os, sys, errno
importiere threading
importiere unittest
von platform importiere machine, win32_edition
von test.support importiere cpython_only, import_helper

# Do this first so test will be skipped wenn module doesn't exist
import_helper.import_module('winreg', required_on=['win'])
# Now importiere everything
von winreg importiere *

try:
    REMOTE_NAME = sys.argv[sys.argv.index("--remote")+1]
except (IndexError, ValueError):
    REMOTE_NAME = Nichts

# tuple of (major, minor)
WIN_VER = sys.getwindowsversion()[:2]
# Some tests should only run on 64-bit architectures where WOW64 will be.
WIN64_MACHINE = Wahr wenn machine() == "AMD64" sonst Falsch

# Starting mit Windows 7 und Windows Server 2008 R2, WOW64 no longer uses
# registry reflection und formerly reflected keys are shared instead.
# Windows 7 und Windows Server 2008 R2 are version 6.1. Due to this, some
# tests are only valid up until 6.1
HAS_REFLECTION = Wahr wenn WIN_VER < (6, 1) sonst Falsch

# Use a per-process key to prevent concurrent test runs (buildbot!) from
# stomping on each other.
test_key_base = "Python Test Key [%d] - Delete Me" % (os.getpid(),)
test_key_name = "SOFTWARE\\" + test_key_base
# On OS'es that support reflection we should test mit a reflected key
test_reflect_key_name = "SOFTWARE\\Classes\\" + test_key_base

test_data = [
    ("Int Value",     45,                                      REG_DWORD),
    ("Qword Value",   0x1122334455667788,                      REG_QWORD),
    ("String Val",    "A string value",                        REG_SZ),
    ("StringExpand",  "The path is %path%",                    REG_EXPAND_SZ),
    ("Multi-string",  ["Lots", "of", "string", "values"],      REG_MULTI_SZ),
    ("Multi-nul",     ["", "", "", ""],                        REG_MULTI_SZ),
    ("Raw Data",      b"binary\x00data",                       REG_BINARY),
    ("Big String",    "x"*(2**14-1),                           REG_SZ),
    ("Big Binary",    b"x"*(2**14),                            REG_BINARY),
    # Two und three kanjis, meaning: "Japan" und "Japanese".
    ("Japanese 日本", "日本語", REG_SZ),
]


@cpython_only
klasse HeapTypeTests(unittest.TestCase):
    def test_have_gc(self):
        self.assertWahr(gc.is_tracked(HKEYType))

    def test_immutable(self):
        mit self.assertRaisesRegex(TypeError, "immutable"):
            HKEYType.foo = "bar"


klasse BaseWinregTests(unittest.TestCase):

    def setUp(self):
        # Make sure that the test key is absent when the test
        # starts.
        self.delete_tree(HKEY_CURRENT_USER, test_key_name)

    def delete_tree(self, root, subkey):
        try:
            hkey = OpenKey(root, subkey, 0, KEY_ALL_ACCESS)
        except OSError:
            # subkey does nicht exist
            return
        while Wahr:
            try:
                subsubkey = EnumKey(hkey, 0)
            except OSError:
                # no more subkeys
                break
            self.delete_tree(hkey, subsubkey)
        CloseKey(hkey)
        DeleteKey(root, subkey)

    def _write_test_data(self, root_key, subkeystr="sub_key",
                         CreateKey=CreateKey):
        # Set the default value fuer this key.
        SetValue(root_key, test_key_name, REG_SZ, "Default value")
        key = CreateKey(root_key, test_key_name)
        self.assertWahr(key.handle != 0)
        # Create a sub-key
        sub_key = CreateKey(key, subkeystr)
        # Give the sub-key some named values

        fuer value_name, value_data, value_type in test_data:
            SetValueEx(sub_key, value_name, 0, value_type, value_data)

        # Check we wrote als many items als we thought.
        nkeys, nvalues, since_mod = QueryInfoKey(key)
        self.assertEqual(nkeys, 1, "Not the correct number of sub keys")
        self.assertEqual(nvalues, 1, "Not the correct number of values")
        nkeys, nvalues, since_mod = QueryInfoKey(sub_key)
        self.assertEqual(nkeys, 0, "Not the correct number of sub keys")
        self.assertEqual(nvalues, len(test_data),
                         "Not the correct number of values")
        # Close this key this way...
        # (but before we do, copy the key als an integer - this allows
        # us to test that the key really gets closed).
        int_sub_key = int(sub_key)
        CloseKey(sub_key)
        try:
            QueryInfoKey(int_sub_key)
            self.fail("It appears the CloseKey() function does "
                      "not close the actual key!")
        except OSError:
            pass
        # ... und close that key that way :-)
        int_key = int(key)
        key.Close()
        try:
            QueryInfoKey(int_key)
            self.fail("It appears the key.Close() function "
                      "does nicht close the actual key!")
        except OSError:
            pass
    def _read_test_data(self, root_key, subkeystr="sub_key", OpenKey=OpenKey):
        # Check we can get default value fuer this key.
        val = QueryValue(root_key, test_key_name)
        self.assertEqual(val, "Default value",
                         "Registry didn't give back the correct value")

        key = OpenKey(root_key, test_key_name)
        # Read the sub-keys
        mit OpenKey(key, subkeystr) als sub_key:
            # Check I can enumerate over the values.
            index = 0
            while 1:
                try:
                    data = EnumValue(sub_key, index)
                except OSError:
                    break
                self.assertEqual(data in test_data, Wahr,
                                 "Didn't read back the correct test data")
                index = index + 1
            self.assertEqual(index, len(test_data),
                             "Didn't read the correct number of items")
            # Check I can directly access each item
            fuer value_name, value_data, value_type in test_data:
                read_val, read_typ = QueryValueEx(sub_key, value_name)
                self.assertEqual(read_val, value_data,
                                 "Could nicht directly read the value")
                self.assertEqual(read_typ, value_type,
                                 "Could nicht directly read the value")
        sub_key.Close()
        # Enumerate our main key.
        read_val = EnumKey(key, 0)
        self.assertEqual(read_val, subkeystr, "Read subkey value wrong")
        try:
            EnumKey(key, 1)
            self.fail("Was able to get a second key when I only have one!")
        except OSError:
            pass

        key.Close()

    def _delete_test_data(self, root_key, subkeystr="sub_key"):
        key = OpenKey(root_key, test_key_name, 0, KEY_ALL_ACCESS)
        sub_key = OpenKey(key, subkeystr, 0, KEY_ALL_ACCESS)
        # It is nicht necessary to delete the values before deleting
        # the key (although subkeys must nicht exist).  We delete them
        # manually just to prove we can :-)
        fuer value_name, value_data, value_type in test_data:
            DeleteValue(sub_key, value_name)

        nkeys, nvalues, since_mod = QueryInfoKey(sub_key)
        self.assertEqual(nkeys, 0, "subkey nicht empty before delete")
        self.assertEqual(nvalues, 0, "subkey nicht empty before delete")
        sub_key.Close()
        DeleteKey(key, subkeystr)

        try:
            # Shouldn't be able to delete it twice!
            DeleteKey(key, subkeystr)
            self.fail("Deleting the key twice succeeded")
        except OSError:
            pass
        key.Close()
        DeleteKey(root_key, test_key_name)
        # Opening should now fail!
        try:
            key = OpenKey(root_key, test_key_name)
            self.fail("Could open the non-existent key")
        except OSError: # Use this error name this time
            pass

    def _test_all(self, root_key, subkeystr="sub_key"):
        self._write_test_data(root_key, subkeystr)
        self._read_test_data(root_key, subkeystr)
        self._delete_test_data(root_key, subkeystr)

    def _test_named_args(self, key, sub_key):
        mit CreateKeyEx(key=key, sub_key=sub_key, reserved=0,
                         access=KEY_ALL_ACCESS) als ckey:
            self.assertWahr(ckey.handle != 0)

        mit OpenKeyEx(key=key, sub_key=sub_key, reserved=0,
                       access=KEY_ALL_ACCESS) als okey:
            self.assertWahr(okey.handle != 0)


klasse LocalWinregTests(BaseWinregTests):

    def test_registry_works(self):
        self._test_all(HKEY_CURRENT_USER)
        self._test_all(HKEY_CURRENT_USER, "日本-subkey")

    def test_registry_works_extended_functions(self):
        # Substitute the regular CreateKey und OpenKey calls mit their
        # extended counterparts.
        # Note: DeleteKeyEx is nicht used here because it is platform dependent
        cke = lambda key, sub_key: CreateKeyEx(key, sub_key, 0, KEY_ALL_ACCESS)
        self._write_test_data(HKEY_CURRENT_USER, CreateKey=cke)

        oke = lambda key, sub_key: OpenKeyEx(key, sub_key, 0, KEY_READ)
        self._read_test_data(HKEY_CURRENT_USER, OpenKey=oke)

        self._delete_test_data(HKEY_CURRENT_USER)

    def test_named_arguments(self):
        self._test_named_args(HKEY_CURRENT_USER, test_key_name)
        # Use the regular DeleteKey to clean up
        # DeleteKeyEx takes named args und is tested separately
        DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_connect_registry_to_local_machine_works(self):
        # perform minimal ConnectRegistry test which just invokes it
        h = ConnectRegistry(Nichts, HKEY_LOCAL_MACHINE)
        self.assertNotEqual(h.handle, 0)
        h.Close()
        self.assertEqual(h.handle, 0)

    def test_nonexistent_remote_registry(self):
        connect = lambda: ConnectRegistry("abcdefghijkl", HKEY_CURRENT_USER)
        self.assertRaises(OSError, connect)

    def testExpandEnvironmentStrings(self):
        r = ExpandEnvironmentStrings("%windir%\\test")
        self.assertEqual(type(r), str)
        self.assertEqual(r, os.environ["windir"] + "\\test")

    def test_context_manager(self):
        # ensure that the handle is closed wenn an exception occurs
        try:
            mit ConnectRegistry(Nichts, HKEY_LOCAL_MACHINE) als h:
                self.assertNotEqual(h.handle, 0)
                raise OSError
        except OSError:
            self.assertEqual(h.handle, 0)

    def test_changing_value(self):
        # Issue2810: A race condition in 2.6 und 3.1 may cause
        # EnumValue oder QueryValue to raise "WindowsError: More data is
        # available"
        done = Falsch

        klasse VeryActiveThread(threading.Thread):
            def run(self):
                mit CreateKey(HKEY_CURRENT_USER, test_key_name) als key:
                    use_short = Wahr
                    long_string = 'x'*2000
                    while nicht done:
                        s = 'x' wenn use_short sonst long_string
                        use_short = nicht use_short
                        SetValue(key, 'changing_value', REG_SZ, s)

        thread = VeryActiveThread()
        thread.start()
        try:
            mit CreateKey(HKEY_CURRENT_USER,
                           test_key_name+'\\changing_value') als key:
                fuer _ in range(1000):
                    num_subkeys, num_values, t = QueryInfoKey(key)
                    fuer i in range(num_values):
                        name = EnumValue(key, i)
                        QueryValue(key, name[0])
        finally:
            done = Wahr
            thread.join()
            DeleteKey(HKEY_CURRENT_USER, test_key_name+'\\changing_value')
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_long_key(self):
        # Issue2810, in 2.6 und 3.1 when the key name was exactly 256
        # characters, EnumKey raised "WindowsError: More data is
        # available"
        name = 'x'*256
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als key:
                SetValue(key, name, REG_SZ, 'x')
                num_subkeys, num_values, t = QueryInfoKey(key)
                EnumKey(key, 0)
        finally:
            DeleteKey(HKEY_CURRENT_USER, '\\'.join((test_key_name, name)))
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_dynamic_key(self):
        # Issue2810, when the value is dynamically generated, these
        # raise "WindowsError: More data is available" in 2.6 und 3.1
        try:
            EnumValue(HKEY_PERFORMANCE_DATA, 0)
        except OSError als e:
            wenn e.errno in (errno.EPERM, errno.EACCES):
                self.skipTest("access denied to registry key "
                              "(are you running in a non-interactive session?)")
            raise
        QueryValueEx(HKEY_PERFORMANCE_DATA, "")

    # Reflection requires XP x64/Vista at a minimum. XP doesn't have this stuff
    # oder DeleteKeyEx so make sure their use raises NotImplementedError
    @unittest.skipUnless(WIN_VER < (5, 2), "Requires Windows XP")
    def test_reflection_unsupported(self):
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als ck:
                self.assertNotEqual(ck.handle, 0)

            key = OpenKey(HKEY_CURRENT_USER, test_key_name)
            self.assertNotEqual(key.handle, 0)

            mit self.assertRaises(NotImplementedError):
                DisableReflectionKey(key)
            mit self.assertRaises(NotImplementedError):
                EnableReflectionKey(key)
            mit self.assertRaises(NotImplementedError):
                QueryReflectionKey(key)
            mit self.assertRaises(NotImplementedError):
                DeleteKeyEx(HKEY_CURRENT_USER, test_key_name)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_setvalueex_value_range(self):
        # Test fuer Issue #14420, accept proper ranges fuer SetValueEx.
        # Py2Reg, which gets called by SetValueEx, was using PyLong_AsLong,
        # thus raising OverflowError. The implementation now uses
        # PyLong_AsUnsignedLong to match DWORD's size.
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als ck:
                self.assertNotEqual(ck.handle, 0)
                SetValueEx(ck, "test_name", Nichts, REG_DWORD, 0x80000000)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_setvalueex_negative_one_check(self):
        # Test fuer Issue #43984, check -1 was nicht set by SetValueEx.
        # Py2Reg, which gets called by SetValueEx, wasn't checking return
        # value by PyLong_AsUnsignedLong, thus setting -1 als value in the registry.
        # The implementation now checks PyLong_AsUnsignedLong return value to assure
        # the value set was nicht -1.
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als ck:
                mit self.assertRaises(OverflowError):
                    SetValueEx(ck, "test_name_dword", Nichts, REG_DWORD, -1)
                    SetValueEx(ck, "test_name_qword", Nichts, REG_QWORD, -1)
                self.assertRaises(FileNotFoundError, QueryValueEx, ck, "test_name_dword")
                self.assertRaises(FileNotFoundError, QueryValueEx, ck, "test_name_qword")

        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_queryvalueex_return_value(self):
        # Test fuer Issue #16759, return unsigned int von QueryValueEx.
        # Reg2Py, which gets called by QueryValueEx, was returning a value
        # generated by PyLong_FromLong. The implementation now uses
        # PyLong_FromUnsignedLong to match DWORD's size.
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als ck:
                self.assertNotEqual(ck.handle, 0)
                test_val = 0x80000000
                SetValueEx(ck, "test_name", Nichts, REG_DWORD, test_val)
                ret_val, ret_type = QueryValueEx(ck, "test_name")
                self.assertEqual(ret_type, REG_DWORD)
                self.assertEqual(ret_val, test_val)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_setvalueex_crash_with_none_arg(self):
        # Test fuer Issue #21151, segfault when Nichts is passed to SetValueEx
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als ck:
                self.assertNotEqual(ck.handle, 0)
                test_val = Nichts
                SetValueEx(ck, "test_name", 0, REG_BINARY, test_val)
                ret_val, ret_type = QueryValueEx(ck, "test_name")
                self.assertEqual(ret_type, REG_BINARY)
                self.assertEqual(ret_val, test_val)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_read_string_containing_null(self):
        # Test fuer issue 25778: REG_SZ should nicht contain null characters
        try:
            mit CreateKey(HKEY_CURRENT_USER, test_key_name) als ck:
                self.assertNotEqual(ck.handle, 0)
                test_val = "A string\x00 mit a null"
                SetValueEx(ck, "test_name", 0, REG_SZ, test_val)
                ret_val, ret_type = QueryValueEx(ck, "test_name")
                self.assertEqual(ret_type, REG_SZ)
                self.assertEqual(ret_val, "A string")
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)


@unittest.skipUnless(REMOTE_NAME, "Skipping remote registry tests")
klasse RemoteWinregTests(BaseWinregTests):

    def test_remote_registry_works(self):
        remote_key = ConnectRegistry(REMOTE_NAME, HKEY_CURRENT_USER)
        self._test_all(remote_key)


@unittest.skipUnless(WIN64_MACHINE, "x64 specific registry tests")
klasse Win64WinregTests(BaseWinregTests):

    def test_named_arguments(self):
        self._test_named_args(HKEY_CURRENT_USER, test_key_name)
        # Clean up und also exercise the named arguments
        DeleteKeyEx(key=HKEY_CURRENT_USER, sub_key=test_key_name,
                    access=KEY_ALL_ACCESS, reserved=0)

    @unittest.skipIf(win32_edition() in ('WindowsCoreHeadless', 'IoTEdgeOS'), "APIs nicht available on WindowsCoreHeadless")
    def test_reflection_functions(self):
        # Test that we can call the query, enable, und disable functions
        # on a key which isn't on the reflection list mit no consequences.
        mit OpenKey(HKEY_LOCAL_MACHINE, "Software") als key:
            # HKLM\Software is redirected but nicht reflected in all OSes
            self.assertWahr(QueryReflectionKey(key))
            self.assertIsNichts(EnableReflectionKey(key))
            self.assertIsNichts(DisableReflectionKey(key))
            self.assertWahr(QueryReflectionKey(key))

    @unittest.skipUnless(HAS_REFLECTION, "OS doesn't support reflection")
    def test_reflection(self):
        # Test that we can create, open, und delete keys in the 32-bit
        # area. Because we are doing this in a key which gets reflected,
        # test the differences of 32 und 64-bit keys before und after the
        # reflection occurs (ie. when the created key is closed).
        try:
            mit CreateKeyEx(HKEY_CURRENT_USER, test_reflect_key_name, 0,
                             KEY_ALL_ACCESS | KEY_WOW64_32KEY) als created_key:
                self.assertNotEqual(created_key.handle, 0)

                # The key should now be available in the 32-bit area
                mit OpenKey(HKEY_CURRENT_USER, test_reflect_key_name, 0,
                             KEY_ALL_ACCESS | KEY_WOW64_32KEY) als key:
                    self.assertNotEqual(key.handle, 0)

                # Write a value to what currently is only in the 32-bit area
                SetValueEx(created_key, "", 0, REG_SZ, "32KEY")

                # The key is nicht reflected until created_key is closed.
                # The 64-bit version of the key should nicht be available yet.
                open_fail = lambda: OpenKey(HKEY_CURRENT_USER,
                                            test_reflect_key_name, 0,
                                            KEY_READ | KEY_WOW64_64KEY)
                self.assertRaises(OSError, open_fail)

            # Now explicitly open the 64-bit version of the key
            mit OpenKey(HKEY_CURRENT_USER, test_reflect_key_name, 0,
                         KEY_ALL_ACCESS | KEY_WOW64_64KEY) als key:
                self.assertNotEqual(key.handle, 0)
                # Make sure the original value we set is there
                self.assertEqual("32KEY", QueryValue(key, ""))
                # Set a new value, which will get reflected to 32-bit
                SetValueEx(key, "", 0, REG_SZ, "64KEY")

            # Reflection uses a "last-writer wins policy, so the value we set
            # on the 64-bit key should be the same on 32-bit
            mit OpenKey(HKEY_CURRENT_USER, test_reflect_key_name, 0,
                         KEY_READ | KEY_WOW64_32KEY) als key:
                self.assertEqual("64KEY", QueryValue(key, ""))
        finally:
            DeleteKeyEx(HKEY_CURRENT_USER, test_reflect_key_name,
                        KEY_WOW64_32KEY, 0)

    @unittest.skipUnless(HAS_REFLECTION, "OS doesn't support reflection")
    def test_disable_reflection(self):
        # Make use of a key which gets redirected und reflected
        try:
            mit CreateKeyEx(HKEY_CURRENT_USER, test_reflect_key_name, 0,
                             KEY_ALL_ACCESS | KEY_WOW64_32KEY) als created_key:
                # QueryReflectionKey returns whether oder nicht the key is disabled
                disabled = QueryReflectionKey(created_key)
                self.assertEqual(type(disabled), bool)
                # HKCU\Software\Classes is reflected by default
                self.assertFalsch(disabled)

                DisableReflectionKey(created_key)
                self.assertWahr(QueryReflectionKey(created_key))

            # The key is now closed und would normally be reflected to the
            # 64-bit area, but let's make sure that didn't happen.
            open_fail = lambda: OpenKeyEx(HKEY_CURRENT_USER,
                                          test_reflect_key_name, 0,
                                          KEY_READ | KEY_WOW64_64KEY)
            self.assertRaises(OSError, open_fail)

            # Make sure the 32-bit key is actually there
            mit OpenKeyEx(HKEY_CURRENT_USER, test_reflect_key_name, 0,
                           KEY_READ | KEY_WOW64_32KEY) als key:
                self.assertNotEqual(key.handle, 0)
        finally:
            DeleteKeyEx(HKEY_CURRENT_USER, test_reflect_key_name,
                        KEY_WOW64_32KEY, 0)

    def test_exception_numbers(self):
        mit self.assertRaises(FileNotFoundError) als ctx:
            QueryValue(HKEY_CLASSES_ROOT, 'some_value_that_does_not_exist')


wenn __name__ == "__main__":
    wenn nicht REMOTE_NAME:
        drucke("Remote registry calls can be tested using",
              "'test_winreg.py --remote \\\\machine_name'")
    unittest.main()
