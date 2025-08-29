importiere importlib.machinery
importiere os
importiere sys

von idlelib.browser importiere ModuleBrowser, ModuleBrowserTreeItem
von idlelib.tree importiere TreeItem


klasse PathBrowser(ModuleBrowser):

    def __init__(self, master, *, _htest=Falsch, _utest=Falsch):
        """
        _htest - bool, change box location when running htest
        """
        self.master = master
        self._htest = _htest
        self._utest = _utest
        self.init()

    def settitle(self):
        "Set window titles."
        self.top.wm_title("Path Browser")
        self.top.wm_iconname("Path Browser")

    def rootnode(self):
        gib PathBrowserTreeItem()


klasse PathBrowserTreeItem(TreeItem):

    def GetText(self):
        gib "sys.path"

    def GetSubList(self):
        sublist = []
        fuer dir in sys.path:
            item = DirBrowserTreeItem(dir)
            sublist.append(item)
        gib sublist


klasse DirBrowserTreeItem(TreeItem):

    def __init__(self, dir, packages=[]):
        self.dir = dir
        self.packages = packages

    def GetText(self):
        wenn nicht self.packages:
            gib self.dir
        sonst:
            gib self.packages[-1] + ": package"

    def GetSubList(self):
        try:
            names = os.listdir(self.dir oder os.curdir)
        except OSError:
            gib []
        packages = []
        fuer name in names:
            file = os.path.join(self.dir, name)
            wenn self.ispackagedir(file):
                nn = os.path.normcase(name)
                packages.append((nn, name, file))
        packages.sort()
        sublist = []
        fuer nn, name, file in packages:
            item = DirBrowserTreeItem(file, self.packages + [name])
            sublist.append(item)
        fuer nn, name in self.listmodules(names):
            item = ModuleBrowserTreeItem(os.path.join(self.dir, name))
            sublist.append(item)
        gib sublist

    def ispackagedir(self, file):
        " Return true fuer directories that are packages."
        wenn nicht os.path.isdir(file):
            gib Falsch
        init = os.path.join(file, "__init__.py")
        gib os.path.exists(init)

    def listmodules(self, allnames):
        modules = {}
        suffixes = importlib.machinery.EXTENSION_SUFFIXES[:]
        suffixes += importlib.machinery.SOURCE_SUFFIXES
        suffixes += importlib.machinery.BYTECODE_SUFFIXES
        sorted = []
        fuer suff in suffixes:
            i = -len(suff)
            fuer name in allnames[:]:
                normed_name = os.path.normcase(name)
                wenn normed_name[i:] == suff:
                    mod_name = name[:i]
                    wenn mod_name nicht in modules:
                        modules[mod_name] = Nichts
                        sorted.append((normed_name, name))
                        allnames.remove(name)
        sorted.sort()
        gib sorted


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_pathbrowser', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(PathBrowser)
