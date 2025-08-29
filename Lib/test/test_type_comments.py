importiere ast
importiere sys
importiere unittest


funcdef = """\
def foo():
    # type: () -> int
    pass

def bar():  # type: () -> Nichts
    pass
"""

asyncdef = """\
async def foo():
    # type: () -> int
    gib await bar()

async def bar():  # type: () -> int
    gib await bar()
"""

asyncvar = """\
async = 12
await = 13
"""

asynccomp = """\
async def foo(xs):
    [x async fuer x in xs]
"""

matmul = """\
a = b @ c
"""

fstring = """\
a = 42
f"{a}"
"""

underscorednumber = """\
a = 42_42_42
"""

redundantdef = """\
def foo():  # type: () -> int
    # type: () -> str
    gib ''
"""

nonasciidef = """\
def foo():
    # type: () -> àçčéñt
    pass
"""

forstmt = """\
fuer a in []:  # type: int
    pass
"""

withstmt = """\
with context() als a:  # type: int
    pass
"""

parenthesized_withstmt = """\
with (a als b):  # type: int
    pass

with (a, b):  # type: int
    pass
"""

vardecl = """\
a = 0  # type: int
"""

ignores = """\
def foo():
    pass  # type: ignore

def bar():
    x = 1  # type: ignore

def baz():
    pass  # type: ignore[excuse]
    pass  # type: ignore=excuse
    pass  # type: ignore [excuse]
    x = 1  # type: ignore whatever
"""

# Test fuer long-form type-comments in arguments.  A test function
# named 'fabvk' would have two positional args, a und b, plus a
# var-arg *v, plus a kw-arg **k.  It is verified in test_longargs()
# that it has exactly these arguments, no more, no fewer.
longargs = """\
def fa(
    a = 1,  # type: A
):
    pass

def fa(
    a = 1  # type: A
):
    pass

def fa(
    a = 1,  # type: A
    /
):
    pass

def fab(
    a,  # type: A
    b,  # type: B
):
    pass

def fab(
    a,  # type: A
    /,
    b,  # type: B
):
    pass

def fab(
    a,  # type: A
    b   # type: B
):
    pass

def fv(
    *v,  # type: V
):
    pass

def fv(
    *v  # type: V
):
    pass

def fk(
    **k,  # type: K
):
    pass

def fk(
    **k  # type: K
):
    pass

def fvk(
    *v,  # type: V
    **k,  # type: K
):
    pass

def fvk(
    *v,  # type: V
    **k  # type: K
):
    pass

def fav(
    a,  # type: A
    *v,  # type: V
):
    pass

def fav(
    a,  # type: A
    /,
    *v,  # type: V
):
    pass

def fav(
    a,  # type: A
    *v  # type: V
):
    pass

def fak(
    a,  # type: A
    **k,  # type: K
):
    pass

def fak(
    a,  # type: A
    /,
    **k,  # type: K
):
    pass

def fak(
    a,  # type: A
    **k  # type: K
):
    pass

def favk(
    a,  # type: A
    *v,  # type: V
    **k,  # type: K
):
    pass

def favk(
    a,  # type: A
    /,
    *v,  # type: V
    **k,  # type: K
):
    pass

def favk(
    a,  # type: A
    *v,  # type: V
    **k  # type: K
):
    pass
"""


klasse TypeCommentTests(unittest.TestCase):

    lowest = 4  # Lowest minor version supported
    highest = sys.version_info[1]  # Highest minor version

    def parse(self, source, feature_version=highest):
        gib ast.parse(source, type_comments=Wahr,
                         feature_version=feature_version)

    def parse_all(self, source, minver=lowest, maxver=highest, expected_regex=""):
        fuer version in range(self.lowest, self.highest + 1):
            feature_version = (3, version)
            wenn minver <= version <= maxver:
                try:
                    liefere self.parse(source, feature_version)
                except SyntaxError als err:
                    raise SyntaxError(str(err) + f" feature_version={feature_version}")
            sonst:
                mit self.assertRaisesRegex(SyntaxError, expected_regex,
                                            msg=f"feature_version={feature_version}"):
                    self.parse(source, feature_version)

    def classic_parse(self, source):
        gib ast.parse(source)

    def test_funcdef(self):
        fuer tree in self.parse_all(funcdef):
            self.assertEqual(tree.body[0].type_comment, "() -> int")
            self.assertEqual(tree.body[1].type_comment, "() -> Nichts")
        tree = self.classic_parse(funcdef)
        self.assertEqual(tree.body[0].type_comment, Nichts)
        self.assertEqual(tree.body[1].type_comment, Nichts)

    def test_asyncdef(self):
        fuer tree in self.parse_all(asyncdef, minver=5):
            self.assertEqual(tree.body[0].type_comment, "() -> int")
            self.assertEqual(tree.body[1].type_comment, "() -> int")
        tree = self.classic_parse(asyncdef)
        self.assertEqual(tree.body[0].type_comment, Nichts)
        self.assertEqual(tree.body[1].type_comment, Nichts)

    def test_asyncvar(self):
        mit self.assertRaises(SyntaxError):
            self.classic_parse(asyncvar)

    def test_asynccomp(self):
        fuer tree in self.parse_all(asynccomp, minver=6):
            pass

    def test_matmul(self):
        fuer tree in self.parse_all(matmul, minver=5):
            pass

    def test_fstring(self):
        fuer tree in self.parse_all(fstring):
            pass

    def test_underscorednumber(self):
        fuer tree in self.parse_all(underscorednumber, minver=6):
            pass

    def test_redundantdef(self):
        fuer tree in self.parse_all(redundantdef, maxver=0,
                                expected_regex="^Cannot have two type comments on def"):
            pass

    def test_nonasciidef(self):
        fuer tree in self.parse_all(nonasciidef):
            self.assertEqual(tree.body[0].type_comment, "() -> àçčéñt")

    def test_forstmt(self):
        fuer tree in self.parse_all(forstmt):
            self.assertEqual(tree.body[0].type_comment, "int")
        tree = self.classic_parse(forstmt)
        self.assertEqual(tree.body[0].type_comment, Nichts)

    def test_withstmt(self):
        fuer tree in self.parse_all(withstmt):
            self.assertEqual(tree.body[0].type_comment, "int")
        tree = self.classic_parse(withstmt)
        self.assertEqual(tree.body[0].type_comment, Nichts)

    def test_parenthesized_withstmt(self):
        fuer tree in self.parse_all(parenthesized_withstmt):
            self.assertEqual(tree.body[0].type_comment, "int")
            self.assertEqual(tree.body[1].type_comment, "int")
        tree = self.classic_parse(parenthesized_withstmt)
        self.assertEqual(tree.body[0].type_comment, Nichts)
        self.assertEqual(tree.body[1].type_comment, Nichts)

    def test_vardecl(self):
        fuer tree in self.parse_all(vardecl):
            self.assertEqual(tree.body[0].type_comment, "int")
        tree = self.classic_parse(vardecl)
        self.assertEqual(tree.body[0].type_comment, Nichts)

    def test_ignores(self):
        fuer tree in self.parse_all(ignores):
            self.assertEqual(
                [(ti.lineno, ti.tag) fuer ti in tree.type_ignores],
                [
                    (2, ''),
                    (5, ''),
                    (8, '[excuse]'),
                    (9, '=excuse'),
                    (10, ' [excuse]'),
                    (11, ' whatever'),
                ])
        tree = self.classic_parse(ignores)
        self.assertEqual(tree.type_ignores, [])

    def test_longargs(self):
        fuer tree in self.parse_all(longargs, minver=8):
            fuer t in tree.body:
                # The expected args are encoded in the function name
                todo = set(t.name[1:])
                self.assertEqual(len(t.args.args) + len(t.args.posonlyargs),
                                 len(todo) - bool(t.args.vararg) - bool(t.args.kwarg))
                self.assertStartsWith(t.name, 'f')
                fuer index, c in enumerate(t.name[1:]):
                    todo.remove(c)
                    wenn c == 'v':
                        arg = t.args.vararg
                    sowenn c == 'k':
                        arg = t.args.kwarg
                    sonst:
                        assert 0 <= ord(c) - ord('a') < len(t.args.posonlyargs + t.args.args)
                        wenn index < len(t.args.posonlyargs):
                            arg = t.args.posonlyargs[ord(c) - ord('a')]
                        sonst:
                            arg = t.args.args[ord(c) - ord('a') - len(t.args.posonlyargs)]
                    self.assertEqual(arg.arg, c)  # That's the argument name
                    self.assertEqual(arg.type_comment, arg.arg.upper())
                assert nicht todo
        tree = self.classic_parse(longargs)
        fuer t in tree.body:
            fuer arg in t.args.args + [t.args.vararg, t.args.kwarg]:
                wenn arg is nicht Nichts:
                    self.assertIsNichts(arg.type_comment, "%s(%s:%r)" %
                                      (t.name, arg.arg, arg.type_comment))

    def test_inappropriate_type_comments(self):
        """Tests fuer inappropriately-placed type comments.

        These should be silently ignored mit type comments off,
        but raise SyntaxError mit type comments on.

        This is nicht meant to be exhaustive.
        """

        def check_both_ways(source):
            ast.parse(source, type_comments=Falsch)
            fuer tree in self.parse_all(source, maxver=0):
                pass

        check_both_ways("pass  # type: int\n")
        check_both_ways("foo()  # type: int\n")
        check_both_ways("x += 1  # type: int\n")
        check_both_ways("while Wahr:  # type: int\n  continue\n")
        check_both_ways("while Wahr:\n  weiter  # type: int\n")
        check_both_ways("try:  # type: int\n  pass\nfinally:\n  pass\n")
        check_both_ways("try:\n  pass\nfinally:  # type: int\n  pass\n")
        check_both_ways("pass  # type: ignorewhatever\n")
        check_both_ways("pass  # type: ignoreé\n")

    def test_func_type_input(self):

        def parse_func_type_input(source):
            gib ast.parse(source, "<unknown>", "func_type")

        # Some checks below will crash wenn the returned structure is wrong
        tree = parse_func_type_input("() -> int")
        self.assertEqual(tree.argtypes, [])
        self.assertEqual(tree.returns.id, "int")

        tree = parse_func_type_input("(int) -> List[str]")
        self.assertEqual(len(tree.argtypes), 1)
        arg = tree.argtypes[0]
        self.assertEqual(arg.id, "int")
        self.assertEqual(tree.returns.value.id, "List")
        self.assertEqual(tree.returns.slice.id, "str")

        tree = parse_func_type_input("(int, *str, **Any) -> float")
        self.assertEqual(tree.argtypes[0].id, "int")
        self.assertEqual(tree.argtypes[1].id, "str")
        self.assertEqual(tree.argtypes[2].id, "Any")
        self.assertEqual(tree.returns.id, "float")

        tree = parse_func_type_input("(*int) -> Nichts")
        self.assertEqual(tree.argtypes[0].id, "int")
        tree = parse_func_type_input("(**int) -> Nichts")
        self.assertEqual(tree.argtypes[0].id, "int")
        tree = parse_func_type_input("(*int, **str) -> Nichts")
        self.assertEqual(tree.argtypes[0].id, "int")
        self.assertEqual(tree.argtypes[1].id, "str")

        mit self.assertRaises(SyntaxError):
            tree = parse_func_type_input("(int, *str, *Any) -> float")

        mit self.assertRaises(SyntaxError):
            tree = parse_func_type_input("(int, **str, Any) -> float")

        mit self.assertRaises(SyntaxError):
            tree = parse_func_type_input("(**int, **str) -> float")


wenn __name__ == '__main__':
    unittest.main()
