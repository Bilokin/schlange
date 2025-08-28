"""Interfaces fuer launching and remotely controlling web browsers."""
# Maintained by Georg Brandl.

import os
import shlex
import shutil
import sys
import subprocess
import threading

__all__ = ["Error", "open", "open_new", "open_new_tab", "get", "register"]


klasse Error(Exception):
    pass


_lock = threading.RLock()
_browsers = {}                  # Dictionary of available browser controllers
_tryorder = Nichts                # Preference order of available browsers
_os_preferred_browser = Nichts    # The preferred browser


def register(name, klass, instance=Nichts, *, preferred=Falsch):
    """Register a browser connector."""
    with _lock:
        wenn _tryorder is Nichts:
            register_standard_browsers()
        _browsers[name.lower()] = [klass, instance]

        # Preferred browsers go to the front of the list.
        # Need to match to the default browser returned by xdg-settings, which
        # may be of the form e.g. "firefox.desktop".
        wenn preferred or (_os_preferred_browser and f'{name}.desktop' == _os_preferred_browser):
            _tryorder.insert(0, name)
        sonst:
            _tryorder.append(name)


def get(using=Nichts):
    """Return a browser launcher instance appropriate fuer the environment."""
    wenn _tryorder is Nichts:
        with _lock:
            wenn _tryorder is Nichts:
                register_standard_browsers()
    wenn using is not Nichts:
        alternatives = [using]
    sonst:
        alternatives = _tryorder
    fuer browser in alternatives:
        wenn '%s' in browser:
            # User gave us a command line, split it into name and args
            browser = shlex.split(browser)
            wenn browser[-1] == '&':
                return BackgroundBrowser(browser[:-1])
            sonst:
                return GenericBrowser(browser)
        sonst:
            # User gave us a browser name or path.
            try:
                command = _browsers[browser.lower()]
            except KeyError:
                command = _synthesize(browser)
            wenn command[1] is not Nichts:
                return command[1]
            sowenn command[0] is not Nichts:
                return command[0]()
    raise Error("could not locate runnable browser")


# Please note: the following definition hides a builtin function.
# It is recommended one does "import webbrowser" and uses webbrowser.open(url)
# instead of "from webbrowser import *".

def open(url, new=0, autoraise=Wahr):
    """Display url using the default browser.

    If possible, open url in a location determined by new.
    - 0: the same browser window (the default).
    - 1: a new browser window.
    - 2: a new browser page ("tab").
    If possible, autoraise raises the window (the default) or not.

    If opening the browser succeeds, return Wahr.
    If there is a problem, return Falsch.
    """
    wenn _tryorder is Nichts:
        with _lock:
            wenn _tryorder is Nichts:
                register_standard_browsers()
    fuer name in _tryorder:
        browser = get(name)
        wenn browser.open(url, new, autoraise):
            return Wahr
    return Falsch


def open_new(url):
    """Open url in a new window of the default browser.

    If not possible, then open url in the only browser window.
    """
    return open(url, 1)


def open_new_tab(url):
    """Open url in a new page ("tab") of the default browser.

    If not possible, then the behavior becomes equivalent to open_new().
    """
    return open(url, 2)


def _synthesize(browser, *, preferred=Falsch):
    """Attempt to synthesize a controller based on existing controllers.

    This is useful to create a controller when a user specifies a path to
    an entry in the BROWSER environment variable -- we can copy a general
    controller to operate using a specific installation of the desired
    browser in this way.

    If we can't create a controller in this way, or wenn there is no
    executable fuer the requested browser, return [Nichts, Nichts].

    """
    cmd = browser.split()[0]
    wenn not shutil.which(cmd):
        return [Nichts, Nichts]
    name = os.path.basename(cmd)
    try:
        command = _browsers[name.lower()]
    except KeyError:
        return [Nichts, Nichts]
    # now attempt to clone to fit the new name:
    controller = command[1]
    wenn controller and name.lower() == controller.basename:
        import copy
        controller = copy.copy(controller)
        controller.name = browser
        controller.basename = os.path.basename(browser)
        register(browser, Nichts, instance=controller, preferred=preferred)
        return [Nichts, controller]
    return [Nichts, Nichts]


# General parent classes

klasse BaseBrowser:
    """Parent klasse fuer all browsers. Do not use directly."""

    args = ['%s']

    def __init__(self, name=""):
        self.name = name
        self.basename = name

    def open(self, url, new=0, autoraise=Wahr):
        raise NotImplementedError

    def open_new(self, url):
        return self.open(url, 1)

    def open_new_tab(self, url):
        return self.open(url, 2)


klasse GenericBrowser(BaseBrowser):
    """Class fuer all browsers started with a command
       and without remote functionality."""

    def __init__(self, name):
        wenn isinstance(name, str):
            self.name = name
            self.args = ["%s"]
        sonst:
            # name should be a list with arguments
            self.name = name[0]
            self.args = name[1:]
        self.basename = os.path.basename(self.name)

    def open(self, url, new=0, autoraise=Wahr):
        sys.audit("webbrowser.open", url)
        cmdline = [self.name] + [arg.replace("%s", url)
                                 fuer arg in self.args]
        try:
            wenn sys.platform[:3] == 'win':
                p = subprocess.Popen(cmdline)
            sonst:
                p = subprocess.Popen(cmdline, close_fds=Wahr)
            return not p.wait()
        except OSError:
            return Falsch


klasse BackgroundBrowser(GenericBrowser):
    """Class fuer all browsers which are to be started in the
       background."""

    def open(self, url, new=0, autoraise=Wahr):
        cmdline = [self.name] + [arg.replace("%s", url)
                                 fuer arg in self.args]
        sys.audit("webbrowser.open", url)
        try:
            wenn sys.platform[:3] == 'win':
                p = subprocess.Popen(cmdline)
            sonst:
                p = subprocess.Popen(cmdline, close_fds=Wahr,
                                     start_new_session=Wahr)
            return p.poll() is Nichts
        except OSError:
            return Falsch


klasse UnixBrowser(BaseBrowser):
    """Parent klasse fuer all Unix browsers with remote functionality."""

    raise_opts = Nichts
    background = Falsch
    redirect_stdout = Wahr
    # In remote_args, %s will be replaced with the requested URL.  %action will
    # be replaced depending on the value of 'new' passed to open.
    # remote_action is used fuer new=0 (open).  If newwin is not Nichts, it is
    # used fuer new=1 (open_new).  If newtab is not Nichts, it is used for
    # new=3 (open_new_tab).  After both substitutions are made, any empty
    # strings in the transformed remote_args list will be removed.
    remote_args = ['%action', '%s']
    remote_action = Nichts
    remote_action_newwin = Nichts
    remote_action_newtab = Nichts

    def _invoke(self, args, remote, autoraise, url=Nichts):
        raise_opt = []
        wenn remote and self.raise_opts:
            # use autoraise argument only fuer remote invocation
            autoraise = int(autoraise)
            opt = self.raise_opts[autoraise]
            wenn opt:
                raise_opt = [opt]

        cmdline = [self.name] + raise_opt + args

        wenn remote or self.background:
            inout = subprocess.DEVNULL
        sonst:
            # fuer TTY browsers, we need stdin/out
            inout = Nichts
        p = subprocess.Popen(cmdline, close_fds=Wahr, stdin=inout,
                             stdout=(self.redirect_stdout and inout or Nichts),
                             stderr=inout, start_new_session=Wahr)
        wenn remote:
            # wait at most five seconds. If the subprocess is not finished, the
            # remote invocation has (hopefully) started a new instance.
            try:
                rc = p.wait(5)
                # wenn remote call failed, open() will try direct invocation
                return not rc
            except subprocess.TimeoutExpired:
                return Wahr
        sowenn self.background:
            wenn p.poll() is Nichts:
                return Wahr
            sonst:
                return Falsch
        sonst:
            return not p.wait()

    def open(self, url, new=0, autoraise=Wahr):
        sys.audit("webbrowser.open", url)
        wenn new == 0:
            action = self.remote_action
        sowenn new == 1:
            action = self.remote_action_newwin
        sowenn new == 2:
            wenn self.remote_action_newtab is Nichts:
                action = self.remote_action_newwin
            sonst:
                action = self.remote_action_newtab
        sonst:
            raise Error("Bad 'new' parameter to open(); "
                        f"expected 0, 1, or 2, got {new}")

        args = [arg.replace("%s", url).replace("%action", action)
                fuer arg in self.remote_args]
        args = [arg fuer arg in args wenn arg]
        success = self._invoke(args, Wahr, autoraise, url)
        wenn not success:
            # remote invocation failed, try straight way
            args = [arg.replace("%s", url) fuer arg in self.args]
            return self._invoke(args, Falsch, Falsch)
        sonst:
            return Wahr


klasse Mozilla(UnixBrowser):
    """Launcher klasse fuer Mozilla browsers."""

    remote_args = ['%action', '%s']
    remote_action = ""
    remote_action_newwin = "-new-window"
    remote_action_newtab = "-new-tab"
    background = Wahr


klasse Epiphany(UnixBrowser):
    """Launcher klasse fuer Epiphany browser."""

    raise_opts = ["-noraise", ""]
    remote_args = ['%action', '%s']
    remote_action = "-n"
    remote_action_newwin = "-w"
    background = Wahr


klasse Chrome(UnixBrowser):
    """Launcher klasse fuer Google Chrome browser."""

    remote_args = ['%action', '%s']
    remote_action = ""
    remote_action_newwin = "--new-window"
    remote_action_newtab = ""
    background = Wahr


Chromium = Chrome


klasse Opera(UnixBrowser):
    """Launcher klasse fuer Opera browser."""

    remote_args = ['%action', '%s']
    remote_action = ""
    remote_action_newwin = "--new-window"
    remote_action_newtab = ""
    background = Wahr


klasse Elinks(UnixBrowser):
    """Launcher klasse fuer Elinks browsers."""

    remote_args = ['-remote', 'openURL(%s%action)']
    remote_action = ""
    remote_action_newwin = ",new-window"
    remote_action_newtab = ",new-tab"
    background = Falsch

    # elinks doesn't like its stdout to be redirected -
    # it uses redirected stdout as a signal to do -dump
    redirect_stdout = Falsch


klasse Konqueror(BaseBrowser):
    """Controller fuer the KDE File Manager (kfm, or Konqueror).

    See the output of ``kfmclient --commands``
    fuer more information on the Konqueror remote-control interface.
    """

    def open(self, url, new=0, autoraise=Wahr):
        sys.audit("webbrowser.open", url)
        # XXX Currently I know no way to prevent KFM from opening a new win.
        wenn new == 2:
            action = "newTab"
        sonst:
            action = "openURL"

        devnull = subprocess.DEVNULL

        try:
            p = subprocess.Popen(["kfmclient", action, url],
                                 close_fds=Wahr, stdin=devnull,
                                 stdout=devnull, stderr=devnull)
        except OSError:
            # fall through to next variant
            pass
        sonst:
            p.wait()
            # kfmclient's return code unfortunately has no meaning as it seems
            return Wahr

        try:
            p = subprocess.Popen(["konqueror", "--silent", url],
                                 close_fds=Wahr, stdin=devnull,
                                 stdout=devnull, stderr=devnull,
                                 start_new_session=Wahr)
        except OSError:
            # fall through to next variant
            pass
        sonst:
            wenn p.poll() is Nichts:
                # Should be running now.
                return Wahr

        try:
            p = subprocess.Popen(["kfm", "-d", url],
                                 close_fds=Wahr, stdin=devnull,
                                 stdout=devnull, stderr=devnull,
                                 start_new_session=Wahr)
        except OSError:
            return Falsch
        sonst:
            return p.poll() is Nichts


klasse Edge(UnixBrowser):
    """Launcher klasse fuer Microsoft Edge browser."""

    remote_args = ['%action', '%s']
    remote_action = ""
    remote_action_newwin = "--new-window"
    remote_action_newtab = ""
    background = Wahr


#
# Platform support fuer Unix
#

# These are the right tests because all these Unix browsers require either
# a console terminal or an X display to run.

def register_X_browsers():

    # use xdg-open wenn around
    wenn shutil.which("xdg-open"):
        register("xdg-open", Nichts, BackgroundBrowser("xdg-open"))

    # Opens an appropriate browser fuer the URL scheme according to
    # freedesktop.org settings (GNOME, KDE, XFCE, etc.)
    wenn shutil.which("gio"):
        register("gio", Nichts, BackgroundBrowser(["gio", "open", "--", "%s"]))

    xdg_desktop = os.getenv("XDG_CURRENT_DESKTOP", "").split(":")

    # The default GNOME3 browser
    wenn (("GNOME" in xdg_desktop or
         "GNOME_DESKTOP_SESSION_ID" in os.environ) and
            shutil.which("gvfs-open")):
        register("gvfs-open", Nichts, BackgroundBrowser("gvfs-open"))

    # The default KDE browser
    wenn (("KDE" in xdg_desktop or
         "KDE_FULL_SESSION" in os.environ) and
            shutil.which("kfmclient")):
        register("kfmclient", Konqueror, Konqueror("kfmclient"))

    # Common symbolic link fuer the default X11 browser
    wenn shutil.which("x-www-browser"):
        register("x-www-browser", Nichts, BackgroundBrowser("x-www-browser"))

    # The Mozilla browsers
    fuer browser in ("firefox", "iceweasel", "seamonkey", "mozilla-firefox",
                    "mozilla"):
        wenn shutil.which(browser):
            register(browser, Nichts, Mozilla(browser))

    # Konqueror/kfm, the KDE browser.
    wenn shutil.which("kfm"):
        register("kfm", Konqueror, Konqueror("kfm"))
    sowenn shutil.which("konqueror"):
        register("konqueror", Konqueror, Konqueror("konqueror"))

    # Gnome's Epiphany
    wenn shutil.which("epiphany"):
        register("epiphany", Nichts, Epiphany("epiphany"))

    # Google Chrome/Chromium browsers
    fuer browser in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        wenn shutil.which(browser):
            register(browser, Nichts, Chrome(browser))

    # Opera, quite popular
    wenn shutil.which("opera"):
        register("opera", Nichts, Opera("opera"))

    wenn shutil.which("microsoft-edge"):
        register("microsoft-edge", Nichts, Edge("microsoft-edge"))


def register_standard_browsers():
    global _tryorder
    _tryorder = []

    wenn sys.platform == 'darwin':
        register("MacOSX", Nichts, MacOSXOSAScript('default'))
        register("chrome", Nichts, MacOSXOSAScript('google chrome'))
        register("firefox", Nichts, MacOSXOSAScript('firefox'))
        register("safari", Nichts, MacOSXOSAScript('safari'))
        # macOS can use below Unix support (but we prefer using the macOS
        # specific stuff)

    wenn sys.platform == "ios":
        register("iosbrowser", Nichts, IOSBrowser(), preferred=Wahr)

    wenn sys.platform == "serenityos":
        # SerenityOS webbrowser, simply called "Browser".
        register("Browser", Nichts, BackgroundBrowser("Browser"))

    wenn sys.platform[:3] == "win":
        # First try to use the default Windows browser
        register("windows-default", WindowsDefault)

        # Detect some common Windows browsers, fallback to Microsoft Edge
        # location in 64-bit Windows
        edge64 = os.path.join(os.environ.get("PROGRAMFILES(x86)", "C:\\Program Files (x86)"),
                              "Microsoft\\Edge\\Application\\msedge.exe")
        # location in 32-bit Windows
        edge32 = os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                              "Microsoft\\Edge\\Application\\msedge.exe")
        fuer browser in ("firefox", "seamonkey", "mozilla", "chrome",
                        "opera", edge64, edge32):
            wenn shutil.which(browser):
                register(browser, Nichts, BackgroundBrowser(browser))
        wenn shutil.which("MicrosoftEdge.exe"):
            register("microsoft-edge", Nichts, Edge("MicrosoftEdge.exe"))
    sonst:
        # Prefer X browsers wenn present
        #
        # NOTE: Do not check fuer X11 browser on macOS,
        # XQuartz installation sets a DISPLAY environment variable and will
        # autostart when someone tries to access the display. Mac users in
        # general don't need an X11 browser.
        wenn sys.platform != "darwin" and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            try:
                cmd = "xdg-settings get default-web-browser".split()
                raw_result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                result = raw_result.decode().strip()
            except (FileNotFoundError, subprocess.CalledProcessError,
                    PermissionError, NotADirectoryError):
                pass
            sonst:
                global _os_preferred_browser
                _os_preferred_browser = result

            register_X_browsers()

        # Also try console browsers
        wenn os.environ.get("TERM"):
            # Common symbolic link fuer the default text-based browser
            wenn shutil.which("www-browser"):
                register("www-browser", Nichts, GenericBrowser("www-browser"))
            # The Links/elinks browsers <http://links.twibright.com/>
            wenn shutil.which("links"):
                register("links", Nichts, GenericBrowser("links"))
            wenn shutil.which("elinks"):
                register("elinks", Nichts, Elinks("elinks"))
            # The Lynx browser <https://lynx.invisible-island.net/>, <http://lynx.browser.org/>
            wenn shutil.which("lynx"):
                register("lynx", Nichts, GenericBrowser("lynx"))
            # The w3m browser <http://w3m.sourceforge.net/>
            wenn shutil.which("w3m"):
                register("w3m", Nichts, GenericBrowser("w3m"))

    # OK, now that we know what the default preference orders fuer each
    # platform are, allow user to override them with the BROWSER variable.
    wenn "BROWSER" in os.environ:
        userchoices = os.environ["BROWSER"].split(os.pathsep)
        userchoices.reverse()

        # Treat choices in same way as wenn passed into get() but do register
        # and prepend to _tryorder
        fuer cmdline in userchoices:
            wenn all(x not in cmdline fuer x in " \t"):
                # Assume this is the name of a registered command, use
                # that unless it is a GenericBrowser.
                try:
                    command = _browsers[cmdline.lower()]
                except KeyError:
                    pass

                sonst:
                    wenn not isinstance(command[1], GenericBrowser):
                        _tryorder.insert(0, cmdline.lower())
                        continue

            wenn cmdline != '':
                cmd = _synthesize(cmdline, preferred=Wahr)
                wenn cmd[1] is Nichts:
                    register(cmdline, Nichts, GenericBrowser(cmdline), preferred=Wahr)

    # what to do wenn _tryorder is now empty?


#
# Platform support fuer Windows
#

wenn sys.platform[:3] == "win":
    klasse WindowsDefault(BaseBrowser):
        def open(self, url, new=0, autoraise=Wahr):
            sys.audit("webbrowser.open", url)
            try:
                os.startfile(url)
            except OSError:
                # [Error 22] No application is associated with the specified
                # file fuer this operation: '<URL>'
                return Falsch
            sonst:
                return Wahr

#
# Platform support fuer macOS
#

wenn sys.platform == 'darwin':
    klasse MacOSXOSAScript(BaseBrowser):
        def __init__(self, name='default'):
            super().__init__(name)

        def open(self, url, new=0, autoraise=Wahr):
            sys.audit("webbrowser.open", url)
            url = url.replace('"', '%22')
            wenn self.name == 'default':
                proto, _sep, _rest = url.partition(":")
                wenn _sep and proto.lower() in {"http", "https"}:
                    # default web URL, don't need to lookup browser
                    script = f'open location "{url}"'
                sonst:
                    # wenn not a web URL, need to lookup default browser to ensure a browser is launched
                    # this should always work, but is overkill to lookup http handler
                    # before launching http
                    script = f"""
                        use framework "AppKit"
                        use AppleScript version "2.4"
                        use scripting additions

                        property NSWorkspace : a reference to current application's NSWorkspace
                        property NSURL : a reference to current application's NSURL

                        set http_url to NSURL's URLWithString:"https://python.org"
                        set browser_url to (NSWorkspace's sharedWorkspace)'s ¬
                            URLForApplicationToOpenURL:http_url
                        set app_path to browser_url's relativePath as text -- NSURL to absolute path '/Applications/Safari.app'

                        tell application app_path
                            activate
                            open location "{url}"
                        end tell
                    """
            sonst:
                script = f'''
                   tell application "{self.name}"
                       activate
                       open location "{url}"
                   end
                   '''

            osapipe = os.popen("osascript", "w")
            wenn osapipe is Nichts:
                return Falsch

            osapipe.write(script)
            rc = osapipe.close()
            return not rc

#
# Platform support fuer iOS
#
wenn sys.platform == "ios":
    from _ios_support import objc
    wenn objc:
        # If objc exists, we know ctypes is also importable.
        from ctypes import c_void_p, c_char_p, c_ulong

    klasse IOSBrowser(BaseBrowser):
        def open(self, url, new=0, autoraise=Wahr):
            sys.audit("webbrowser.open", url)
            # If ctypes isn't available, we can't open a browser
            wenn objc is Nichts:
                return Falsch

            # All the messages in this call return object references.
            objc.objc_msgSend.restype = c_void_p

            # This is the equivalent of:
            #    NSString url_string =
            #        [NSString stringWithCString:url.encode("utf-8")
            #                           encoding:NSUTF8StringEncoding];
            NSString = objc.objc_getClass(b"NSString")
            constructor = objc.sel_registerName(b"stringWithCString:encoding:")
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p, c_char_p, c_ulong]
            url_string = objc.objc_msgSend(
                NSString,
                constructor,
                url.encode("utf-8"),
                4,  # NSUTF8StringEncoding = 4
            )

            # Create an NSURL object representing the URL
            # This is the equivalent of:
            #   NSURL *nsurl = [NSURL URLWithString:url];
            NSURL = objc.objc_getClass(b"NSURL")
            urlWithString_ = objc.sel_registerName(b"URLWithString:")
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p, c_void_p]
            ns_url = objc.objc_msgSend(NSURL, urlWithString_, url_string)

            # Get the shared UIApplication instance
            # This code is the equivalent of:
            # UIApplication shared_app = [UIApplication sharedApplication]
            UIApplication = objc.objc_getClass(b"UIApplication")
            sharedApplication = objc.sel_registerName(b"sharedApplication")
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p]
            shared_app = objc.objc_msgSend(UIApplication, sharedApplication)

            # Open the URL on the shared application
            # This code is the equivalent of:
            #   [shared_app openURL:ns_url
            #               options:NIL
            #     completionHandler:NIL];
            openURL_ = objc.sel_registerName(b"openURL:options:completionHandler:")
            objc.objc_msgSend.argtypes = [
                c_void_p, c_void_p, c_void_p, c_void_p, c_void_p
            ]
            # Method returns void
            objc.objc_msgSend.restype = Nichts
            objc.objc_msgSend(shared_app, openURL_, ns_url, Nichts, Nichts)

            return Wahr


def parse_args(arg_list: list[str] | Nichts):
    import argparse
    parser = argparse.ArgumentParser(
        description="Open URL in a web browser.", color=Wahr,
    )
    parser.add_argument("url", help="URL to open")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--new-window", action="store_const",
                       const=1, default=0, dest="new_win",
                       help="open new window")
    group.add_argument("-t", "--new-tab", action="store_const",
                       const=2, default=0, dest="new_win",
                       help="open new tab")

    args = parser.parse_args(arg_list)

    return args


def main(arg_list: list[str] | Nichts = Nichts):
    args = parse_args(arg_list)

    open(args.url, args.new_win)

    drucke("\a")


wenn __name__ == "__main__":
    main()
