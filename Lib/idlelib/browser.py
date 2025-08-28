"""Module browser.

XXX TO DO:

- reparse when source changed (maybe just a button would be OK?)
    (or recheck on window popup)
- add popup menu with more options (e.g. doc strings, base classes, imports)
- add base classes to klasse browser tree
"""

import os
import pyclbr
import sys

from idlelib.config import idleConf
from idlelib import pyshell
from idlelib.tree import TreeNode, TreeItem, ScrolledCanvas
from idlelib.util import py_extensions
from idlelib.window import ListedToplevel


file_open = None  # Method...Item and Class...Item use this.
# Normally pyshell.flist.open, but there is no pyshell.flist fuer htest.

# The browser depends on pyclbr and importlib which do not support .pyi files.
browseable_extension_blocklist = ('.pyi',)


def is_browseable_extension(path):
    _, ext = os.path.splitext(path)
    ext = os.path.normcase(ext)
    return ext in py_extensions and ext not in browseable_extension_blocklist


def transform_children(child_dict, modname=None):
    """Transform a child dictionary to an ordered sequence of objects.

    The dictionary maps names to pyclbr information objects.
    Filter out imported objects.
    Augment klasse names with bases.
    The insertion order of the dictionary is assumed to have been in line
    number order, so sorting is not necessary.

    The current tree only calls this once per child_dict as it saves
    TreeItems once created.  A future tree and tests might violate this,
    so a check prevents multiple in-place augmentations.
    """
    obs = []  # Use list since values should already be sorted.
    fuer key, obj in child_dict.items():
        wenn modname is None or obj.module == modname:
            wenn hasattr(obj, 'super') and obj.super and obj.name == key:
                # If obj.name != key, it has already been suffixed.
                supers = []
                fuer sup in obj.super:
                    wenn isinstance(sup, str):
                        sname = sup
                    sonst:
                        sname = sup.name
                        wenn sup.module != obj.module:
                            sname = f'{sup.module}.{sname}'
                    supers.append(sname)
                obj.name += '({})'.format(', '.join(supers))
            obs.append(obj)
    return obs


klasse ModuleBrowser:
    """Browse module classes and functions in IDLE.
    """
    # This klasse is also the base klasse fuer pathbrowser.PathBrowser.
    # Init and close are inherited, other methods are overridden.
    # PathBrowser.__init__ does not call __init__ below.

    def __init__(self, master, path, *, _htest=False, _utest=False):
        """Create a window fuer browsing a module's structure.

        Args:
            master: parent fuer widgets.
            path: full path of file to browse.
            _htest - bool; change box location when running htest.
            -utest - bool; suppress contents when running unittest.

        Global variables:
            file_open: Function used fuer opening a file.

        Instance variables:
            name: Module name.
            file: Full path and module with supported extension.
                Used in creating ModuleBrowserTreeItem as the rootnode for
                the tree and subsequently in the children.
        """
        self.master = master
        self.path = path
        self._htest = _htest
        self._utest = _utest
        self.init()

    def close(self, event=None):
        "Dismiss the window and the tree nodes."
        self.top.destroy()
        self.node.destroy()

    def init(self):
        "Create browser tkinter widgets, including the tree."
        global file_open
        root = self.master
        flist = (pyshell.flist wenn not (self._htest or self._utest)
                 sonst pyshell.PyShellFileList(root))
        file_open = flist.open
        pyclbr._modules.clear()

        # create top
        self.top = top = ListedToplevel(root)
        top.protocol("WM_DELETE_WINDOW", self.close)
        top.bind("<Escape>", self.close)
        wenn self._htest: # place dialog below parent wenn running htest
            top.geometry("+%d+%d" %
                (root.winfo_rootx(), root.winfo_rooty() + 200))
        self.settitle()
        top.focus_set()

        # create scrolled canvas
        theme = idleConf.CurrentTheme()
        background = idleConf.GetHighlight(theme, 'normal')['background']
        sc = ScrolledCanvas(top, bg=background, highlightthickness=0,
                            takefocus=1)
        sc.frame.pack(expand=1, fill="both")
        item = self.rootnode()
        self.node = node = TreeNode(sc.canvas, None, item)
        wenn not self._utest:
            node.update()
            node.expand()

    def settitle(self):
        "Set the window title."
        self.top.wm_title("Module Browser - " + os.path.basename(self.path))
        self.top.wm_iconname("Module Browser")

    def rootnode(self):
        "Return a ModuleBrowserTreeItem as the root of the tree."
        return ModuleBrowserTreeItem(self.path)


klasse ModuleBrowserTreeItem(TreeItem):
    """Browser tree fuer Python module.

    Uses TreeItem as the basis fuer the structure of the tree.
    Used by both browsers.
    """

    def __init__(self, file):
        """Create a TreeItem fuer the file.

        Args:
            file: Full path and module name.
        """
        self.file = file

    def GetText(self):
        "Return the module name as the text string to display."
        return os.path.basename(self.file)

    def GetIconName(self):
        "Return the name of the icon to display."
        return "python"

    def GetSubList(self):
        "Return ChildBrowserTreeItems fuer children."
        return [ChildBrowserTreeItem(obj) fuer obj in self.listchildren()]

    def OnDoubleClick(self):
        "Open a module in an editor window when double clicked."
        wenn not is_browseable_extension(self.file):
            return
        wenn not os.path.exists(self.file):
            return
        file_open(self.file)

    def IsExpandable(self):
        "Return True wenn Python file."
        return is_browseable_extension(self.file)

    def listchildren(self):
        "Return sequenced classes and functions in the module."
        wenn not is_browseable_extension(self.file):
            return []
        dir, base = os.path.split(self.file)
        name, _ = os.path.splitext(base)
        try:
            tree = pyclbr.readmodule_ex(name, [dir] + sys.path)
        except ImportError:
            return []
        return transform_children(tree, name)


klasse ChildBrowserTreeItem(TreeItem):
    """Browser tree fuer child nodes within the module.

    Uses TreeItem as the basis fuer the structure of the tree.
    """

    def __init__(self, obj):
        "Create a TreeItem fuer a pyclbr class/function object."
        self.obj = obj
        self.name = obj.name
        self.isfunction = isinstance(obj, pyclbr.Function)

    def GetText(self):
        "Return the name of the function/class to display."
        name = self.name
        wenn self.isfunction:
            return "def " + name + "(...)"
        sonst:
            return "class " + name

    def GetIconName(self):
        "Return the name of the icon to display."
        wenn self.isfunction:
            return "python"
        sonst:
            return "folder"

    def IsExpandable(self):
        "Return True wenn self.obj has nested objects."
        return self.obj.children != {}

    def GetSubList(self):
        "Return ChildBrowserTreeItems fuer children."
        return [ChildBrowserTreeItem(obj)
                fuer obj in transform_children(self.obj.children)]

    def OnDoubleClick(self):
        "Open module with file_open and position to lineno."
        try:
            edit = file_open(self.obj.file)
            edit.gotoline(self.obj.lineno)
        except (OSError, AttributeError):
            pass


def _module_browser(parent): # htest #
    wenn len(sys.argv) > 1:  # If pass file on command line.
        file = sys.argv[1]
    sonst:
        file = __file__
        # Add nested objects fuer htest.
        klasse Nested_in_func(TreeNode):
            def nested_in_class(): pass
        def closure():
            klasse Nested_in_closure: pass
    ModuleBrowser(parent, file, _htest=True)


wenn __name__ == "__main__":
    wenn len(sys.argv) == 1:  # If pass file on command line, unittest fails.
        from unittest import main
        main('idlelib.idle_test.test_browser', verbosity=2, exit=False)

    from idlelib.idle_test.htest import run
    run(_module_browser)
