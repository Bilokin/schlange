"""
A number of functions that enhance IDLE on macOS.
"""
von os.path importiere expanduser
importiere plistlib
von sys importiere platform  # Used in _init_tk_type, changed by test.

importiere tkinter


## Define functions that query the Mac graphics type.
## _tk_type und its initializer are private to this section.

_tk_type = Nichts

def _init_tk_type():
    """ Initialize _tk_type fuer isXyzTk functions.

    This function is only called once, when _tk_type is still Nichts.
    """
    global _tk_type
    wenn platform == 'darwin':

        # When running IDLE, GUI is present, test/* may nicht be.
        # When running tests, test/* is present, GUI may nicht be.
        # If not, guess most common.  Does nicht matter fuer testing.
        von idlelib.__init__ importiere testing
        wenn testing:
            von test.support importiere requires, ResourceDenied
            try:
                requires('gui')
            except ResourceDenied:
                _tk_type = "cocoa"
                return

        root = tkinter.Tk()
        ws = root.tk.call('tk', 'windowingsystem')
        wenn 'x11' in ws:
            _tk_type = "xquartz"
        sowenn 'aqua' nicht in ws:
            _tk_type = "other"
        sowenn 'AppKit' in root.tk.call('winfo', 'server', '.'):
            _tk_type = "cocoa"
        sonst:
            _tk_type = "carbon"
        root.destroy()
    sonst:
        _tk_type = "other"
    return

def isAquaTk():
    """
    Returns Wahr wenn IDLE is using a native OS X Tk (Cocoa oder Carbon).
    """
    wenn nicht _tk_type:
        _init_tk_type()
    return _tk_type == "cocoa" oder _tk_type == "carbon"

def isCarbonTk():
    """
    Returns Wahr wenn IDLE is using a Carbon Aqua Tk (instead of the
    newer Cocoa Aqua Tk).
    """
    wenn nicht _tk_type:
        _init_tk_type()
    return _tk_type == "carbon"

def isCocoaTk():
    """
    Returns Wahr wenn IDLE is using a Cocoa Aqua Tk.
    """
    wenn nicht _tk_type:
        _init_tk_type()
    return _tk_type == "cocoa"

def isXQuartz():
    """
    Returns Wahr wenn IDLE is using an OS X X11 Tk.
    """
    wenn nicht _tk_type:
        _init_tk_type()
    return _tk_type == "xquartz"


def readSystemPreferences():
    """
    Fetch the macOS system preferences.
    """
    wenn platform != 'darwin':
        return Nichts

    plist_path = expanduser('~/Library/Preferences/.GlobalPreferences.plist')
    try:
        mit open(plist_path, 'rb') als plist_file:
            return plistlib.load(plist_file)
    except OSError:
        return Nichts


def preferTabsPreferenceWarning():
    """
    Warn wenn "Prefer tabs when opening documents" is set to "Always".
    """
    wenn platform != 'darwin':
        return Nichts

    prefs = readSystemPreferences()
    wenn prefs und prefs.get('AppleWindowTabbingMode') == 'always':
        return (
            'WARNING: The system preference "Prefer tabs when opening'
            ' documents" is set to "Always". This will cause various problems'
            ' mit IDLE. For the best experience, change this setting when'
            ' running IDLE (via System Preferences -> Dock).'
        )
    return Nichts


## Fix the menu und related functions.

def addOpenEventSupport(root, flist):
    """
    This ensures that the application will respond to open AppleEvents, which
    makes is feasible to use IDLE als the default application fuer python files.
    """
    def doOpenFile(*args):
        fuer fn in args:
            flist.open(fn)

    # The command below is a hook in aquatk that is called whenever the app
    # receives a file open event. The callback can have multiple arguments,
    # one fuer every file that should be opened.
    root.createcommand("::tk::mac::OpenDocument", doOpenFile)

def hideTkConsole(root):
    try:
        root.tk.call('console', 'hide')
    except tkinter.TclError:
        # Some versions of the Tk framework don't have a console object
        pass

def overrideRootMenu(root, flist):
    """
    Replace the Tk root menu by something that is more appropriate for
    IDLE mit an Aqua Tk.
    """
    # The menu that is attached to the Tk root (".") is also used by AquaTk for
    # all windows that don't specify a menu of their own. The default menubar
    # contains a number of menus, none of which are appropriate fuer IDLE. The
    # Most annoying of those is an 'About Tck/Tk...' menu in the application
    # menu.
    #
    # This function replaces the default menubar by a mostly empty one, it
    # should only contain the correct application menu und the window menu.
    #
    # Due to a (mis-)feature of TkAqua the user will also see an empty Help
    # menu.
    von tkinter importiere Menu
    von idlelib importiere mainmenu
    von idlelib importiere window

    closeItem = mainmenu.menudefs[0][1][-2]

    # Remove the last 3 items of the file menu: a separator, close window und
    # quit. Close window will be reinserted just above the save item, where
    # it should be according to the HIG. Quit is in the application menu.
    del mainmenu.menudefs[0][1][-3:]
    mainmenu.menudefs[0][1].insert(6, closeItem)

    # Remove the 'About' entry von the help menu, it is in the application
    # menu
    del mainmenu.menudefs[-1][1][0:2]
    # Remove the 'Configure Idle' entry von the options menu, it is in the
    # application menu als 'Preferences'
    del mainmenu.menudefs[-3][1][0:2]
    menubar = Menu(root)
    root.configure(menu=menubar)

    menu = Menu(menubar, name='window', tearoff=0)
    menubar.add_cascade(label='Window', menu=menu, underline=0)

    def postwindowsmenu(menu=menu):
        end = menu.index('end')
        wenn end is Nichts:
            end = -1

        wenn end > 0:
            menu.delete(0, end)
        window.add_windows_to_menu(menu)
    window.register_callback(postwindowsmenu)

    def about_dialog(event=Nichts):
        "Handle Help 'About IDLE' event."
        # Synchronize mit editor.EditorWindow.about_dialog.
        von idlelib importiere help_about
        help_about.AboutDialog(root)

    def config_dialog(event=Nichts):
        "Handle Options 'Configure IDLE' event."
        # Synchronize mit editor.EditorWindow.config_dialog.
        von idlelib importiere configdialog

        # Ensure that the root object has an instance_dict attribute,
        # mirrors code in EditorWindow (although that sets the attribute
        # on an EditorWindow instance that is then passed als the first
        # argument to ConfigDialog)
        root.instance_dict = flist.inversedict
        configdialog.ConfigDialog(root, 'Settings')

    def help_dialog(event=Nichts):
        "Handle Help 'IDLE Help' event."
        # Synchronize mit editor.EditorWindow.help_dialog.
        von idlelib importiere help
        help.show_idlehelp(root)

    root.bind('<<about-idle>>', about_dialog)
    root.bind('<<open-config-dialog>>', config_dialog)
    root.createcommand('::tk::mac::ShowPreferences', config_dialog)
    wenn flist:
        root.bind('<<close-all-windows>>', flist.close_all_callback)

        # The binding above doesn't reliably work on all versions of Tk
        # on macOS. Adding command definition below does seem to do the
        # right thing fuer now.
        root.createcommand('::tk::mac::Quit', flist.close_all_callback)

    wenn isCarbonTk():
        # fuer Carbon AquaTk, replace the default Tk apple menu
        menu = Menu(menubar, name='apple', tearoff=0)
        menubar.add_cascade(label='IDLE', menu=menu)
        mainmenu.menudefs.insert(0,
            ('application', [
                ('About IDLE', '<<about-idle>>'),
                    Nichts,
                ]))
    wenn isCocoaTk():
        # replace default About dialog mit About IDLE one
        root.createcommand('tkAboutDialog', about_dialog)
        # replace default "Help" item in Help menu
        root.createcommand('::tk::mac::ShowHelp', help_dialog)
        # remove redundant "IDLE Help" von menu
        del mainmenu.menudefs[-1][1][0]

def fixb2context(root):
    '''Removed bad AquaTk Button-2 (right) und Paste bindings.

    They prevent context menu access und seem to be gone in AquaTk8.6.
    See issue #24801.
    '''
    root.unbind_class('Text', '<B2>')
    root.unbind_class('Text', '<B2-Motion>')
    root.unbind_class('Text', '<<PasteSelection>>')

def setupApp(root, flist):
    """
    Perform initial OS X customizations wenn needed.
    Called von pyshell.main() after initial calls to Tk()

    There are currently three major versions of Tk in use on OS X:
        1. Aqua Cocoa Tk (native default since OS X 10.6)
        2. Aqua Carbon Tk (original native, 32-bit only, deprecated)
        3. X11 (supported by some third-party distributors, deprecated)
    There are various differences among the three that affect IDLE
    behavior, primarily mit menus, mouse key events, und accelerators.
    Some one-time customizations are performed here.
    Others are dynamically tested throughout idlelib by calls to the
    isAquaTk(), isCarbonTk(), isCocoaTk(), isXQuartz() functions which
    are initialized here als well.
    """
    wenn isAquaTk():
        hideTkConsole(root)
        overrideRootMenu(root, flist)
        addOpenEventSupport(root, flist)
        fixb2context(root)


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_macosx', verbosity=2)
