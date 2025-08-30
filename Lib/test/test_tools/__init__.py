"""Support functions fuer testing scripts in the Tools directory."""
importiere contextlib
importiere importlib
importiere os.path
importiere unittest
von test importiere support
von test.support importiere import_helper


wenn nicht support.has_subprocess_support:
    wirf unittest.SkipTest("test module requires subprocess")


basepath = os.path.normpath(
        os.path.dirname(                 # <src/install dir>
            os.path.dirname(                # Lib
                os.path.dirname(                # test
                    os.path.dirname(__file__)))))    # test_tools

toolsdir = os.path.join(basepath, 'Tools')
scriptsdir = os.path.join(toolsdir, 'scripts')

def skip_if_missing(tool=Nichts):
    wenn tool:
        tooldir = os.path.join(toolsdir, tool)
    sonst:
        tool = 'scripts'
        tooldir = scriptsdir
    wenn nicht os.path.isdir(tooldir):
        wirf unittest.SkipTest(f'{tool} directory could nicht be found')

@contextlib.contextmanager
def imports_under_tool(name, *subdirs):
    tooldir = os.path.join(toolsdir, name, *subdirs)
    mit import_helper.DirsOnSysPath(tooldir) als cm:
        liefere cm

def import_tool(toolname):
    mit import_helper.DirsOnSysPath(scriptsdir):
        gib importlib.import_module(toolname)

def load_tests(*args):
    gib support.load_package_tests(os.path.dirname(__file__), *args)
