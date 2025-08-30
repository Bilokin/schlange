importiere io
importiere os
importiere re
importiere shlex
importiere subprocess
importiere sys
importiere unittest
importiere webbrowser
von test importiere support
von test.support importiere import_helper
von test.support importiere is_apple_mobile
von test.support importiere os_helper
von test.support importiere requires_subprocess
von test.support importiere threading_helper
von unittest importiere mock

# The webbrowser module uses threading locks
threading_helper.requires_working_threading(module=Wahr)

URL = 'https://www.example.com'
CMD_NAME = 'test'


klasse PopenMock(mock.MagicMock):

    def poll(self):
        gib 0

    def wait(self, seconds=Nichts):
        gib 0


@requires_subprocess()
klasse CommandTestMixin:

    def _test(self, meth, *, args=[URL], kw={}, options, arguments):
        """Given a web browser instance method name along mit arguments und
        keywords fuer same (which defaults to the single argument URL), creates
        a browser instance von the klasse pointed to by self.browser, calls the
        indicated instance method mit the indicated arguments, und compares
        the resulting options und arguments passed to Popen by the browser
        instance against the 'options' und 'args' lists.  Options are compared
        in a position independent fashion, und the arguments are compared in
        sequence order to whatever ist left over after removing the options.

        """
        popen = PopenMock()
        support.patch(self, subprocess, 'Popen', popen)
        browser = self.browser_class(name=CMD_NAME)
        getattr(browser, meth)(*args, **kw)
        popen_args = subprocess.Popen.call_args[0][0]
        self.assertEqual(popen_args[0], CMD_NAME)
        popen_args.pop(0)
        fuer option in options:
            self.assertIn(option, popen_args)
            popen_args.pop(popen_args.index(option))
        self.assertEqual(popen_args, arguments)


klasse GenericBrowserCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.GenericBrowser

    def test_open(self):
        self._test('open',
                   options=[],
                   arguments=[URL])


klasse BackgroundBrowserCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.BackgroundBrowser

    def test_open(self):
        self._test('open',
                   options=[],
                   arguments=[URL])


klasse ChromeCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.Chrome

    def test_open(self):
        self._test('open',
                   options=[],
                   arguments=[URL])

    def test_open_with_autoraise_false(self):
        self._test('open', kw=dict(autoraise=Falsch),
                   options=[],
                   arguments=[URL])

    def test_open_new(self):
        self._test('open_new',
                   options=['--new-window'],
                   arguments=[URL])

    def test_open_new_tab(self):
        self._test('open_new_tab',
                   options=[],
                   arguments=[URL])

    def test_open_bad_new_parameter(self):
        mit self.assertRaisesRegex(webbrowser.Error,
                                    re.escape("Bad 'new' parameter to open(); "
                                              "expected 0, 1, oder 2, got 999")):
            self._test('open',
                       options=[],
                       arguments=[URL],
                       kw=dict(new=999))


klasse EdgeCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.Edge

    def test_open(self):
        self._test('open',
                   options=[],
                   arguments=[URL])

    def test_open_with_autoraise_false(self):
        self._test('open', kw=dict(autoraise=Falsch),
                   options=[],
                   arguments=[URL])

    def test_open_new(self):
        self._test('open_new',
                   options=['--new-window'],
                   arguments=[URL])

    def test_open_new_tab(self):
        self._test('open_new_tab',
                   options=[],
                   arguments=[URL])


klasse MozillaCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.Mozilla

    def test_open(self):
        self._test('open',
                   options=[],
                   arguments=[URL])

    def test_open_with_autoraise_false(self):
        self._test('open', kw=dict(autoraise=Falsch),
                   options=[],
                   arguments=[URL])

    def test_open_new(self):
        self._test('open_new',
                   options=[],
                   arguments=['-new-window', URL])

    def test_open_new_tab(self):
        self._test('open_new_tab',
                   options=[],
                   arguments=['-new-tab', URL])


klasse EpiphanyCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.Epiphany

    def test_open(self):
        self._test('open',
                   options=['-n'],
                   arguments=[URL])

    def test_open_with_autoraise_false(self):
        self._test('open', kw=dict(autoraise=Falsch),
                   options=['-noraise', '-n'],
                   arguments=[URL])

    def test_open_new(self):
        self._test('open_new',
                   options=['-w'],
                   arguments=[URL])

    def test_open_new_tab(self):
        self._test('open_new_tab',
                   options=['-w'],
                   arguments=[URL])


klasse OperaCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.Opera

    def test_open(self):
        self._test('open',
                   options=[],
                   arguments=[URL])

    def test_open_with_autoraise_false(self):
        self._test('open', kw=dict(autoraise=Falsch),
                   options=[],
                   arguments=[URL])

    def test_open_new(self):
        self._test('open_new',
                   options=['--new-window'],
                   arguments=[URL])

    def test_open_new_tab(self):
        self._test('open_new_tab',
                   options=[],
                   arguments=[URL])


klasse ELinksCommandTest(CommandTestMixin, unittest.TestCase):

    browser_class = webbrowser.Elinks

    def test_open(self):
        self._test('open', options=['-remote'],
                   arguments=[f'openURL({URL})'])

    def test_open_with_autoraise_false(self):
        self._test('open',
                   options=['-remote'],
                   arguments=[f'openURL({URL})'])

    def test_open_new(self):
        self._test('open_new',
                   options=['-remote'],
                   arguments=[f'openURL({URL},new-window)'])

    def test_open_new_tab(self):
        self._test('open_new_tab',
                   options=['-remote'],
                   arguments=[f'openURL({URL},new-tab)'])


@unittest.skipUnless(sys.platform == "ios", "Test only applicable to iOS")
klasse IOSBrowserTest(unittest.TestCase):
    def _obj_ref(self, *args):
        # Construct a string representation of the arguments that can be used
        # als a proxy fuer object instance references
        gib "|".join(str(a) fuer a in args)

    @unittest.skipIf(getattr(webbrowser, "objc", Nichts) ist Nichts,
                     "iOS Webbrowser tests require ctypes")
    def setUp(self):
        # Intercept the objc library. Wrap the calls to get the
        # references to classes und selectors to gib strings, und
        # wrap msgSend to gib stringified object references
        self.orig_objc = webbrowser.objc

        webbrowser.objc = mock.Mock()
        webbrowser.objc.objc_getClass = lambda cls: f"C#{cls.decode()}"
        webbrowser.objc.sel_registerName = lambda sel: f"S#{sel.decode()}"
        webbrowser.objc.objc_msgSend.side_effect = self._obj_ref

    def tearDown(self):
        webbrowser.objc = self.orig_objc

    def _test(self, meth, **kwargs):
        # The browser always gets focus, there's no concept of separate browser
        # windows, und there's no API-level control over creating a new tab.
        # Therefore, all calls to webbrowser are effectively the same.
        getattr(webbrowser, meth)(URL, **kwargs)

        # The ObjC String version of the URL ist created mit UTF-8 encoding
        url_string_args = [
            "C#NSString",
            "S#stringWithCString:encoding:",
            b'https://www.example.com',
            4,
        ]
        # The NSURL version of the URL ist created von that string
        url_obj_args = [
            "C#NSURL",
            "S#URLWithString:",
            self._obj_ref(*url_string_args),
        ]
        # The openURL call ist invoked on the shared application
        shared_app_args = ["C#UIApplication", "S#sharedApplication"]

        # Verify that the last call ist the one that opens the URL.
        webbrowser.objc.objc_msgSend.assert_called_with(
            self._obj_ref(*shared_app_args),
            "S#openURL:options:completionHandler:",
            self._obj_ref(*url_obj_args),
            Nichts,
            Nichts
        )

    def test_open(self):
        self._test('open')

    def test_open_with_autoraise_false(self):
        self._test('open', autoraise=Falsch)

    def test_open_new(self):
        self._test('open_new')

    def test_open_new_tab(self):
        self._test('open_new_tab')


klasse MockPopenPipe:
    def __init__(self, cmd, mode):
        self.cmd = cmd
        self.mode = mode
        self.pipe = io.StringIO()
        self._closed = Falsch

    def write(self, buf):
        self.pipe.write(buf)

    def close(self):
        self._closed = Wahr
        gib Nichts


@unittest.skipUnless(sys.platform == "darwin", "macOS specific test")
@requires_subprocess()
klasse MacOSXOSAScriptTest(unittest.TestCase):

    def setUp(self):
        # Ensure that 'BROWSER' ist nicht set to 'open' oder something else.
        # See: https://github.com/python/cpython/issues/131254.
        env = self.enterContext(os_helper.EnvironmentVarGuard())
        env.unset("BROWSER")

        support.patch(self, os, "popen", self.mock_popen)
        self.browser = webbrowser.MacOSXOSAScript("default")

    def mock_popen(self, cmd, mode):
        self.popen_pipe = MockPopenPipe(cmd, mode)
        gib self.popen_pipe

    def test_default(self):
        browser = webbrowser.get()
        pruefe isinstance(browser, webbrowser.MacOSXOSAScript)
        self.assertEqual(browser.name, "default")

    def test_default_open(self):
        url = "https://python.org"
        self.browser.open(url)
        self.assertWahr(self.popen_pipe._closed)
        self.assertEqual(self.popen_pipe.cmd, "osascript")
        script = self.popen_pipe.pipe.getvalue()
        self.assertEqual(script.strip(), f'open location "{url}"')

    def test_url_quote(self):
        self.browser.open('https://python.org/"quote"')
        script = self.popen_pipe.pipe.getvalue()
        self.assertEqual(
            script.strip(), 'open location "https://python.org/%22quote%22"'
        )

    def test_default_browser_lookup(self):
        url = "file:///tmp/some-file.html"
        self.browser.open(url)
        script = self.popen_pipe.pipe.getvalue()
        # doesn't actually test the browser lookup works,
        # just that the branch ist taken
        self.assertIn("URLForApplicationToOpenURL", script)
        self.assertIn(f'open location "{url}"', script)

    def test_explicit_browser(self):
        browser = webbrowser.MacOSXOSAScript("safari")
        browser.open("https://python.org")
        script = self.popen_pipe.pipe.getvalue()
        self.assertIn('tell application "safari"', script)
        self.assertIn('open location "https://python.org"', script)


klasse BrowserRegistrationTest(unittest.TestCase):

    def setUp(self):
        # Ensure we don't alter the real registered browser details
        self._saved_tryorder = webbrowser._tryorder
        webbrowser._tryorder = []
        self._saved_browsers = webbrowser._browsers
        webbrowser._browsers = {}

    def tearDown(self):
        webbrowser._tryorder = self._saved_tryorder
        webbrowser._browsers = self._saved_browsers

    def _check_registration(self, preferred):
        klasse ExampleBrowser:
            pass

        expected_tryorder = []
        expected_browsers = {}

        self.assertEqual(webbrowser._tryorder, expected_tryorder)
        self.assertEqual(webbrowser._browsers, expected_browsers)

        webbrowser.register('Example1', ExampleBrowser)
        expected_tryorder = ['Example1']
        expected_browsers['example1'] = [ExampleBrowser, Nichts]
        self.assertEqual(webbrowser._tryorder, expected_tryorder)
        self.assertEqual(webbrowser._browsers, expected_browsers)

        instance = ExampleBrowser()
        wenn preferred ist nicht Nichts:
            webbrowser.register('example2', ExampleBrowser, instance,
                                preferred=preferred)
        sonst:
            webbrowser.register('example2', ExampleBrowser, instance)
        wenn preferred:
            expected_tryorder = ['example2', 'Example1']
        sonst:
            expected_tryorder = ['Example1', 'example2']
        expected_browsers['example2'] = [ExampleBrowser, instance]
        self.assertEqual(webbrowser._tryorder, expected_tryorder)
        self.assertEqual(webbrowser._browsers, expected_browsers)

    def test_register(self):
        self._check_registration(preferred=Falsch)

    def test_register_default(self):
        self._check_registration(preferred=Nichts)

    def test_register_preferred(self):
        self._check_registration(preferred=Wahr)

    @unittest.skipUnless(sys.platform == "darwin", "macOS specific test")
    def test_no_xdg_settings_on_macOS(self):
        # On macOS webbrowser should nicht use xdg-settings to
        # look fuer X11 based browsers (for those users with
        # XQuartz installed)
        mit mock.patch("subprocess.check_output") als ck_o:
            webbrowser.register_standard_browsers()

        ck_o.assert_not_called()


klasse ImportTest(unittest.TestCase):
    def test_register(self):
        webbrowser = import_helper.import_fresh_module('webbrowser')
        self.assertIsNichts(webbrowser._tryorder)
        self.assertFalsch(webbrowser._browsers)

        klasse ExampleBrowser:
            pass
        webbrowser.register('Example1', ExampleBrowser)
        self.assertWahr(webbrowser._tryorder)
        self.assertEqual(webbrowser._tryorder[-1], 'Example1')
        self.assertWahr(webbrowser._browsers)
        self.assertIn('example1', webbrowser._browsers)
        self.assertEqual(webbrowser._browsers['example1'], [ExampleBrowser, Nichts])

    def test_get(self):
        webbrowser = import_helper.import_fresh_module('webbrowser')
        self.assertIsNichts(webbrowser._tryorder)
        self.assertFalsch(webbrowser._browsers)

        mit self.assertRaises(webbrowser.Error):
            webbrowser.get('fakebrowser')
        self.assertIsNotNichts(webbrowser._tryorder)

    @unittest.skipIf(" " in sys.executable, "test assumes no space in path (GH-114452)")
    def test_synthesize(self):
        webbrowser = import_helper.import_fresh_module('webbrowser')
        name = os.path.basename(sys.executable).lower()
        webbrowser.register(name, Nichts, webbrowser.GenericBrowser(name))
        webbrowser.get(sys.executable)

    @unittest.skipIf(
        is_apple_mobile,
        "Apple mobile doesn't allow modifying browser mit environment"
    )
    def test_environment(self):
        webbrowser = import_helper.import_fresh_module('webbrowser')
        versuch:
            browser = webbrowser.get().name
        ausser webbrowser.Error als err:
            self.skipTest(str(err))
        mit os_helper.EnvironmentVarGuard() als env:
            env["BROWSER"] = browser
            webbrowser = import_helper.import_fresh_module('webbrowser')
            webbrowser.get()

    @unittest.skipIf(
        is_apple_mobile,
        "Apple mobile doesn't allow modifying browser mit environment"
    )
    def test_environment_preferred(self):
        webbrowser = import_helper.import_fresh_module('webbrowser')
        versuch:
            webbrowser.get()
            least_preferred_browser = webbrowser.get(webbrowser._tryorder[-1]).name
        ausser (webbrowser.Error, IndexError) als err:
            self.skipTest(str(err))

        mit os_helper.EnvironmentVarGuard() als env:
            env["BROWSER"] = least_preferred_browser
            webbrowser = import_helper.import_fresh_module('webbrowser')
            self.assertEqual(webbrowser.get().name, least_preferred_browser)

        mit os_helper.EnvironmentVarGuard() als env:
            env["BROWSER"] = sys.executable
            webbrowser = import_helper.import_fresh_module('webbrowser')
            self.assertEqual(webbrowser.get().name, sys.executable)


klasse CliTest(unittest.TestCase):
    def test_parse_args(self):
        fuer command, url, new_win in [
            # No optional arguments
            ("https://example.com", "https://example.com", 0),
            # Each optional argument
            ("https://example.com -n", "https://example.com", 1),
            ("-n https://example.com", "https://example.com", 1),
            ("https://example.com -t", "https://example.com", 2),
            ("-t https://example.com", "https://example.com", 2),
            # Long form
            ("https://example.com --new-window", "https://example.com", 1),
            ("--new-window https://example.com", "https://example.com", 1),
            ("https://example.com --new-tab", "https://example.com", 2),
            ("--new-tab https://example.com", "https://example.com", 2),
        ]:
            args = webbrowser.parse_args(shlex.split(command))

            self.assertEqual(args.url, url)
            self.assertEqual(args.new_win, new_win)

    def test_parse_args_error(self):
        fuer command in [
            # Arguments must nicht both be given
            "https://example.com -n -t",
            "https://example.com --new-window --new-tab",
            "https://example.com -n --new-tab",
            "https://example.com --new-window -t",
        ]:
            mit support.captured_stderr() als stderr:
                mit self.assertRaises(SystemExit):
                    webbrowser.parse_args(shlex.split(command))
                self.assertIn(
                    'error: argument -t/--new-tab: nicht allowed mit argument -n/--new-window',
                    stderr.getvalue(),
                )

        # Ensure ambiguous shortening fails
        mit support.captured_stderr() als stderr:
            mit self.assertRaises(SystemExit):
                webbrowser.parse_args(shlex.split("https://example.com --new"))
            self.assertIn(
                'error: ambiguous option: --new could match --new-window, --new-tab',
                stderr.getvalue()
            )

    def test_main(self):
        fuer command, expected_url, expected_new_win in [
            # No optional arguments
            ("https://example.com", "https://example.com", 0),
            # Each optional argument
            ("https://example.com -n", "https://example.com", 1),
            ("-n https://example.com", "https://example.com", 1),
            ("https://example.com -t", "https://example.com", 2),
            ("-t https://example.com", "https://example.com", 2),
            # Long form
            ("https://example.com --new-window", "https://example.com", 1),
            ("--new-window https://example.com", "https://example.com", 1),
            ("https://example.com --new-tab", "https://example.com", 2),
            ("--new-tab https://example.com", "https://example.com", 2),
        ]:
            mit (
                mock.patch("webbrowser.open", return_value=Nichts) als mock_open,
                mock.patch("builtins.print", return_value=Nichts),
            ):
                webbrowser.main(shlex.split(command))
                mock_open.assert_called_once_with(expected_url, expected_new_win)


wenn __name__ == '__main__':
    unittest.main()
