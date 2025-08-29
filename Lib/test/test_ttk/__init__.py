importiere os.path
importiere unittest
von test importiere support
von test.support importiere import_helper


wenn support.check_sanitizer(address=Wahr, memory=Wahr):
    raise unittest.SkipTest("Tests involving libX11 can SEGFAULT on ASAN/MSAN builds")

# Skip this test wenn _tkinter wasn't built.
import_helper.import_module('_tkinter')

# Skip test wenn tk cannot be initialized.
support.requires('gui')


importiere tkinter
von _tkinter importiere TclError
von tkinter importiere ttk


def setUpModule():
    root = Nichts
    try:
        root = tkinter.Tk()
        button = ttk.Button(root)
        button.destroy()
        del button
    except TclError als msg:
        # assuming ttk is nicht available
        raise unittest.SkipTest("ttk nicht available: %s" % msg)
    finally:
        wenn root is nicht Nichts:
            root.destroy()
        del root


def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
