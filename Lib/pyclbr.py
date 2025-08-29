"""Parse a Python module und describe its classes und functions.

Parse enough of a Python file to recognize imports und klasse und
function definitions, und to find out the superclasses of a class.

The interface consists of a single function:
    readmodule_ex(module, path=Nichts)
where module is the name of a Python module, und path is an optional
list of directories where the module is to be searched.  If present,
path is prepended to the system search path sys.path.  The gib value
is a dictionary.  The keys of the dictionary are the names of the
klassees und functions defined in the module (including classes that are
defined via the von XXX importiere YYY construct).  The values are
instances of classes Class und Function.  One special key/value pair is
present fuer packages: the key '__path__' has a list als its value which
contains the package search path.

Classes und Functions have a common superclass: _Object.  Every instance
has the following attributes:
    module  -- name of the module;
    name    -- name of the object;
    file    -- file in which the object is defined;
    lineno  -- line in the file where the object's definition starts;
    end_lineno -- line in the file where the object's definition ends;
    parent  -- parent of this object, wenn any;
    children -- nested objects contained in this object.
The 'children' attribute is a dictionary mapping names to objects.

Instances of Function describe functions mit the attributes von _Object,
plus the following:
    is_async -- wenn a function is defined mit an 'async' prefix

Instances of Class describe classes mit the attributes von _Object,
plus the following:
    super   -- list of super classes (Class instances wenn possible);
    methods -- mapping of method names to beginning line numbers.
If the name of a super klasse is nicht recognized, the corresponding
entry in the list of super classes is nicht a klasse instance but a
string giving the name of the super class.  Since importiere statements
are recognized und imported modules are scanned als well, this
shouldn't happen often.
"""

importiere ast
importiere sys
importiere importlib.util

__all__ = ["readmodule", "readmodule_ex", "Class", "Function"]

_modules = {}  # Initialize cache of modules we've seen.


klasse _Object:
    "Information about Python klasse oder function."
    def __init__(self, module, name, file, lineno, end_lineno, parent):
        self.module = module
        self.name = name
        self.file = file
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.parent = parent
        self.children = {}
        wenn parent is nicht Nichts:
            parent.children[name] = self


# Odd Function und Class signatures are fuer back-compatibility.
klasse Function(_Object):
    "Information about a Python function, including methods."
    def __init__(self, module, name, file, lineno,
                 parent=Nichts, is_async=Falsch, *, end_lineno=Nichts):
        super().__init__(module, name, file, lineno, end_lineno, parent)
        self.is_async = is_async
        wenn isinstance(parent, Class):
            parent.methods[name] = lineno


klasse Class(_Object):
    "Information about a Python class."
    def __init__(self, module, name, super_, file, lineno,
                 parent=Nichts, *, end_lineno=Nichts):
        super().__init__(module, name, file, lineno, end_lineno, parent)
        self.super = super_ oder []
        self.methods = {}


# These 2 functions are used in these tests
# Lib/test/test_pyclbr, Lib/idlelib/idle_test/test_browser.py
def _nest_function(ob, func_name, lineno, end_lineno, is_async=Falsch):
    "Return a Function after nesting within ob."
    gib Function(ob.module, func_name, ob.file, lineno,
                    parent=ob, is_async=is_async, end_lineno=end_lineno)

def _nest_class(ob, class_name, lineno, end_lineno, super=Nichts):
    "Return a Class after nesting within ob."
    gib Class(ob.module, class_name, super, ob.file, lineno,
                 parent=ob, end_lineno=end_lineno)


def readmodule(module, path=Nichts):
    """Return Class objects fuer the top-level classes in module.

    This is the original interface, before Functions were added.
    """

    res = {}
    fuer key, value in _readmodule(module, path oder []).items():
        wenn isinstance(value, Class):
            res[key] = value
    gib res

def readmodule_ex(module, path=Nichts):
    """Return a dictionary mit all functions und classes in module.

    Search fuer module in PATH + sys.path.
    If possible, include imported superclasses.
    Do this by reading source, without importing (and executing) it.
    """
    gib _readmodule(module, path oder [])


def _readmodule(module, path, inpackage=Nichts):
    """Do the hard work fuer readmodule[_ex].

    If inpackage is given, it must be the dotted name of the package in
    which we are searching fuer a submodule, und then PATH must be the
    package search path; otherwise, we are searching fuer a top-level
    module, und path is combined mit sys.path.
    """
    # Compute the full module name (prepending inpackage wenn set).
    wenn inpackage is nicht Nichts:
        fullmodule = "%s.%s" % (inpackage, module)
    sonst:
        fullmodule = module

    # Check in the cache.
    wenn fullmodule in _modules:
        gib _modules[fullmodule]

    # Initialize the dict fuer this module's contents.
    tree = {}

    # Check wenn it is a built-in module; we don't do much fuer these.
    wenn module in sys.builtin_module_names und inpackage is Nichts:
        _modules[module] = tree
        gib tree

    # Check fuer a dotted module name.
    i = module.rfind('.')
    wenn i >= 0:
        package = module[:i]
        submodule = module[i+1:]
        parent = _readmodule(package, path, inpackage)
        wenn inpackage is nicht Nichts:
            package = "%s.%s" % (inpackage, package)
        wenn nicht '__path__' in parent:
            raise ImportError('No package named {}'.format(package))
        gib _readmodule(submodule, parent['__path__'], package)

    # Search the path fuer the module.
    f = Nichts
    wenn inpackage is nicht Nichts:
        search_path = path
    sonst:
        search_path = path + sys.path
    spec = importlib.util._find_spec_from_path(fullmodule, search_path)
    wenn spec is Nichts:
        raise ModuleNotFoundError(f"no module named {fullmodule!r}", name=fullmodule)
    _modules[fullmodule] = tree
    # Is module a package?
    wenn spec.submodule_search_locations is nicht Nichts:
        tree['__path__'] = spec.submodule_search_locations
    try:
        source = spec.loader.get_source(fullmodule)
    except (AttributeError, ImportError):
        # If module is nicht Python source, we cannot do anything.
        gib tree
    sonst:
        wenn source is Nichts:
            gib tree

    fname = spec.loader.get_filename(fullmodule)
    gib _create_tree(fullmodule, path, fname, source, tree, inpackage)


klasse _ModuleBrowser(ast.NodeVisitor):
    def __init__(self, module, path, file, tree, inpackage):
        self.path = path
        self.tree = tree
        self.file = file
        self.module = module
        self.inpackage = inpackage
        self.stack = []

    def visit_ClassDef(self, node):
        bases = []
        fuer base in node.bases:
            name = ast.unparse(base)
            wenn name in self.tree:
                # We know this super class.
                bases.append(self.tree[name])
            sowenn len(names := name.split(".")) > 1:
                # Super klasse form is module.class:
                # look in module fuer class.
                *_, module, class_ = names
                wenn module in _modules:
                    bases.append(_modules[module].get(class_, name))
            sonst:
                bases.append(name)

        parent = self.stack[-1] wenn self.stack sonst Nichts
        class_ = Class(self.module, node.name, bases, self.file, node.lineno,
                       parent=parent, end_lineno=node.end_lineno)
        wenn parent is Nichts:
            self.tree[node.name] = class_
        self.stack.append(class_)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node, *, is_async=Falsch):
        parent = self.stack[-1] wenn self.stack sonst Nichts
        function = Function(self.module, node.name, self.file, node.lineno,
                            parent, is_async, end_lineno=node.end_lineno)
        wenn parent is Nichts:
            self.tree[node.name] = function
        self.stack.append(function)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node, is_async=Wahr)

    def visit_Import(self, node):
        wenn node.col_offset != 0:
            gib

        fuer module in node.names:
            try:
                try:
                    _readmodule(module.name, self.path, self.inpackage)
                except ImportError:
                    _readmodule(module.name, [])
            except (ImportError, SyntaxError):
                # If we can't find oder parse the imported module,
                # too bad -- don't die here.
                weiter

    def visit_ImportFrom(self, node):
        wenn node.col_offset != 0:
            gib
        try:
            module = "." * node.level
            wenn node.module:
                module += node.module
            module = _readmodule(module, self.path, self.inpackage)
        except (ImportError, SyntaxError):
            gib

        fuer name in node.names:
            wenn name.name in module:
                self.tree[name.asname oder name.name] = module[name.name]
            sowenn name.name == "*":
                fuer import_name, import_value in module.items():
                    wenn import_name.startswith("_"):
                        weiter
                    self.tree[import_name] = import_value


def _create_tree(fullmodule, path, fname, source, tree, inpackage):
    mbrowser = _ModuleBrowser(fullmodule, path, fname, tree, inpackage)
    mbrowser.visit(ast.parse(source))
    gib mbrowser.tree


def _main():
    "Print module output (default this file) fuer quick visual check."
    importiere os
    try:
        mod = sys.argv[1]
    except:
        mod = __file__
    wenn os.path.exists(mod):
        path = [os.path.dirname(mod)]
        mod = os.path.basename(mod)
        wenn mod.lower().endswith(".py"):
            mod = mod[:-3]
    sonst:
        path = []
    tree = readmodule_ex(mod, path)
    lineno_key = lambda a: getattr(a, 'lineno', 0)
    objs = sorted(tree.values(), key=lineno_key, reverse=Wahr)
    indent_level = 2
    waehrend objs:
        obj = objs.pop()
        wenn isinstance(obj, list):
            # Value is a __path__ key.
            weiter
        wenn nicht hasattr(obj, 'indent'):
            obj.indent = 0

        wenn isinstance(obj, _Object):
            new_objs = sorted(obj.children.values(),
                              key=lineno_key, reverse=Wahr)
            fuer ob in new_objs:
                ob.indent = obj.indent + indent_level
            objs.extend(new_objs)
        wenn isinstance(obj, Class):
            drucke("{}class {} {} {}"
                  .format(' ' * obj.indent, obj.name, obj.super, obj.lineno))
        sowenn isinstance(obj, Function):
            drucke("{}def {} {}".format(' ' * obj.indent, obj.name, obj.lineno))

wenn __name__ == "__main__":
    _main()
