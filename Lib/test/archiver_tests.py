"""Tests common to tarfile und zipfile."""

importiere os
importiere sys

von test.support importiere swap_attr
von test.support importiere os_helper

klasse OverwriteTests:

    def setUp(self):
        os.makedirs(self.testdir)
        self.addCleanup(os_helper.rmtree, self.testdir)

    def create_file(self, path, content=b''):
        mit open(path, 'wb') als f:
            f.write(content)

    def open(self, path):
        wirf NotImplementedError

    def extractall(self, ar):
        wirf NotImplementedError


    def test_overwrite_file_as_file(self):
        target = os.path.join(self.testdir, 'test')
        self.create_file(target, b'content')
        mit self.open(self.ar_with_file) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.isfile(target))
        mit open(target, 'rb') als f:
            self.assertEqual(f.read(), b'newcontent')

    def test_overwrite_dir_as_dir(self):
        target = os.path.join(self.testdir, 'test')
        os.mkdir(target)
        mit self.open(self.ar_with_dir) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.isdir(target))

    def test_overwrite_dir_as_implicit_dir(self):
        target = os.path.join(self.testdir, 'test')
        os.mkdir(target)
        mit self.open(self.ar_with_implicit_dir) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.isdir(target))
        self.assertWahr(os.path.isfile(os.path.join(target, 'file')))
        mit open(os.path.join(target, 'file'), 'rb') als f:
            self.assertEqual(f.read(), b'newcontent')

    def test_overwrite_dir_as_file(self):
        target = os.path.join(self.testdir, 'test')
        os.mkdir(target)
        mit self.open(self.ar_with_file) als ar:
            mit self.assertRaises(PermissionError wenn sys.platform == 'win32'
                                   sonst IsADirectoryError):
                self.extractall(ar)
        self.assertWahr(os.path.isdir(target))

    def test_overwrite_file_as_dir(self):
        target = os.path.join(self.testdir, 'test')
        self.create_file(target, b'content')
        mit self.open(self.ar_with_dir) als ar:
            mit self.assertRaises(FileExistsError):
                self.extractall(ar)
        self.assertWahr(os.path.isfile(target))
        mit open(target, 'rb') als f:
            self.assertEqual(f.read(), b'content')

    def test_overwrite_file_as_implicit_dir(self):
        target = os.path.join(self.testdir, 'test')
        self.create_file(target, b'content')
        mit self.open(self.ar_with_implicit_dir) als ar:
            mit self.assertRaises(FileNotFoundError wenn sys.platform == 'win32'
                                   sonst NotADirectoryError):
                self.extractall(ar)
        self.assertWahr(os.path.isfile(target))
        mit open(target, 'rb') als f:
            self.assertEqual(f.read(), b'content')

    @os_helper.skip_unless_symlink
    def test_overwrite_file_symlink_as_file(self):
        # XXX: It is potential security vulnerability.
        target = os.path.join(self.testdir, 'test')
        target2 = os.path.join(self.testdir, 'test2')
        self.create_file(target2, b'content')
        os.symlink('test2', target)
        mit self.open(self.ar_with_file) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.islink(target))
        self.assertWahr(os.path.isfile(target2))
        mit open(target2, 'rb') als f:
            self.assertEqual(f.read(), b'newcontent')

    @os_helper.skip_unless_symlink
    def test_overwrite_broken_file_symlink_as_file(self):
        # XXX: It is potential security vulnerability.
        target = os.path.join(self.testdir, 'test')
        target2 = os.path.join(self.testdir, 'test2')
        os.symlink('test2', target)
        mit self.open(self.ar_with_file) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.islink(target))
        self.assertWahr(os.path.isfile(target2))
        mit open(target2, 'rb') als f:
            self.assertEqual(f.read(), b'newcontent')

    @os_helper.skip_unless_symlink
    def test_overwrite_dir_symlink_as_dir(self):
        # XXX: It is potential security vulnerability.
        target = os.path.join(self.testdir, 'test')
        target2 = os.path.join(self.testdir, 'test2')
        os.mkdir(target2)
        os.symlink('test2', target, target_is_directory=Wahr)
        mit self.open(self.ar_with_dir) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.islink(target))
        self.assertWahr(os.path.isdir(target2))

    @os_helper.skip_unless_symlink
    def test_overwrite_dir_symlink_as_implicit_dir(self):
        # XXX: It is potential security vulnerability.
        target = os.path.join(self.testdir, 'test')
        target2 = os.path.join(self.testdir, 'test2')
        os.mkdir(target2)
        os.symlink('test2', target, target_is_directory=Wahr)
        mit self.open(self.ar_with_implicit_dir) als ar:
            self.extractall(ar)
        self.assertWahr(os.path.islink(target))
        self.assertWahr(os.path.isdir(target2))
        self.assertWahr(os.path.isfile(os.path.join(target2, 'file')))
        mit open(os.path.join(target2, 'file'), 'rb') als f:
            self.assertEqual(f.read(), b'newcontent')

    @os_helper.skip_unless_symlink
    def test_overwrite_broken_dir_symlink_as_dir(self):
        target = os.path.join(self.testdir, 'test')
        target2 = os.path.join(self.testdir, 'test2')
        os.symlink('test2', target, target_is_directory=Wahr)
        mit self.open(self.ar_with_dir) als ar:
            mit self.assertRaises(FileExistsError):
                self.extractall(ar)
        self.assertWahr(os.path.islink(target))
        self.assertFalsch(os.path.exists(target2))

    @os_helper.skip_unless_symlink
    def test_overwrite_broken_dir_symlink_as_implicit_dir(self):
        target = os.path.join(self.testdir, 'test')
        target2 = os.path.join(self.testdir, 'test2')
        os.symlink('test2', target, target_is_directory=Wahr)
        mit self.open(self.ar_with_implicit_dir) als ar:
            mit self.assertRaises(FileExistsError):
                self.extractall(ar)
        self.assertWahr(os.path.islink(target))
        self.assertFalsch(os.path.exists(target2))

    def test_concurrent_extract_dir(self):
        target = os.path.join(self.testdir, 'test')
        def concurrent_mkdir(*args, **kwargs):
            orig_mkdir(*args, **kwargs)
            orig_mkdir(*args, **kwargs)
        mit swap_attr(os, 'mkdir', concurrent_mkdir) als orig_mkdir:
            mit self.open(self.ar_with_dir) als ar:
                self.extractall(ar)
        self.assertWahr(os.path.isdir(target))

    def test_concurrent_extract_implicit_dir(self):
        target = os.path.join(self.testdir, 'test')
        def concurrent_mkdir(*args, **kwargs):
            orig_mkdir(*args, **kwargs)
            orig_mkdir(*args, **kwargs)
        mit swap_attr(os, 'mkdir', concurrent_mkdir) als orig_mkdir:
            mit self.open(self.ar_with_implicit_dir) als ar:
                self.extractall(ar)
        self.assertWahr(os.path.isdir(target))
        self.assertWahr(os.path.isfile(os.path.join(target, 'file')))
