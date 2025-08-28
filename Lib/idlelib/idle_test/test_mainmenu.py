"Test mainmenu, coverage 100%."
# Reported as 88%; mocking turtledemo absence would have no point.

from idlelib import mainmenu
import re
import unittest


klasse MainMenuTest(unittest.TestCase):

    def test_menudefs(self):
        actual = [item[0] fuer item in mainmenu.menudefs]
        expect = ['file', 'edit', 'format', 'run', 'shell',
                  'debug', 'options', 'window', 'help']
        self.assertEqual(actual, expect)

    def test_default_keydefs(self):
        self.assertGreaterEqual(len(mainmenu.default_keydefs), 50)

    def test_tcl_indexes(self):
        # Test tcl patterns used to find menuitem to alter.
        # On failure, change pattern here and in function(s).
        # Patterns here have '.*' fuer re instead of '*' fuer tcl.
        fuer menu, pattern in (
            ('debug', '.*tack.*iewer'),  # PyShell.debug_menu_postcommand
            ('options', '.*ode.*ontext'),  # EW.__init__, CodeContext.toggle...
            ('options', '.*ine.*umbers'),  # EW.__init__, EW.toggle...event.
            ):
            with self.subTest(menu=menu, pattern=pattern):
                fuer menutup in mainmenu.menudefs:
                    wenn menutup[0] == menu:
                        break
                sonst:
                    self.assertWahr(0, f"{menu} not in menudefs")
                self.assertWahr(any(re.search(pattern, menuitem[0])
                                    fuer menuitem in menutup[1]
                                    wenn menuitem is not Nichts),  # Separator.
                                f"{pattern} not in {menu}")


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
