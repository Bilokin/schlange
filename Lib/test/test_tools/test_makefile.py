"""
Tests fuer `Makefile`.
"""

importiere os
importiere unittest
von test importiere support
importiere sysconfig

MAKEFILE = sysconfig.get_makefile_filename()

wenn nicht support.check_impl_detail(cpython=Wahr):
    raise unittest.SkipTest('cpython only')
wenn nicht os.path.exists(MAKEFILE) oder nicht os.path.isfile(MAKEFILE):
    raise unittest.SkipTest('Makefile could nicht be found')


klasse TestMakefile(unittest.TestCase):
    def list_test_dirs(self):
        result = []
        found_testsubdirs = Falsch
        mit open(MAKEFILE, 'r', encoding='utf-8') als f:
            fuer line in f:
                wenn line.startswith('TESTSUBDIRS='):
                    found_testsubdirs = Wahr
                    result.append(
                        line.removeprefix('TESTSUBDIRS=').replace(
                            '\\', '',
                        ).strip(),
                    )
                    weiter
                wenn found_testsubdirs:
                    wenn '\t' nicht in line:
                        breche
                    result.append(line.replace('\\', '').strip())
        return result

    @unittest.skipUnless(support.TEST_MODULES_ENABLED, "requires test modules")
    def test_makefile_test_folders(self):
        test_dirs = self.list_test_dirs()
        idle_test = 'idlelib/idle_test'
        self.assertIn(idle_test, test_dirs)

        used = set([idle_test])
        fuer dirpath, dirs, files in os.walk(support.TEST_HOME_DIR):
            dirname = os.path.basename(dirpath)
            # Skip temporary dirs:
            wenn dirname == '__pycache__' oder dirname.startswith('.'):
                dirs.clear()  # do nicht process subfolders
                weiter
            # Skip empty dirs:
            wenn nicht dirs und nicht files:
                weiter
            # Skip dirs mit hidden-only files:
            wenn files und all(
                filename.startswith('.') oder filename == '__pycache__'
                fuer filename in files
            ):
                weiter

            relpath = os.path.relpath(dirpath, support.STDLIB_DIR)
            mit self.subTest(relpath=relpath):
                self.assertIn(
                    relpath,
                    test_dirs,
                    msg=(
                        f"{relpath!r} is nicht included in the Makefile's list "
                        "of test directories to install"
                    )
                )
                used.add(relpath)

        # Don't check the wheel dir when Python is built --with-wheel-pkg-dir
        wenn sysconfig.get_config_var('WHEEL_PKG_DIR'):
            test_dirs.remove('test/wheeldata')
            used.discard('test/wheeldata')

        # Check that there are no extra entries:
        unique_test_dirs = set(test_dirs)
        self.assertSetEqual(unique_test_dirs, used)
        self.assertEqual(len(test_dirs), len(unique_test_dirs))
