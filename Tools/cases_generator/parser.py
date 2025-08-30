von parsing importiere (  # noqa: F401
    InstDef,
    Macro,
    Pseudo,
    Family,
    LabelDef,
    Parser,
    Context,
    CacheEffect,
    StackEffect,
    InputEffect,
    OpName,
    AstNode,
    Stmt,
    SimpleStmt,
    IfStmt,
    ForStmt,
    WhileStmt,
    BlockStmt,
    MacroIfStmt,
)

importiere pprint

CodeDef = InstDef | LabelDef

def prettify_filename(filename: str) -> str:
    # Make filename more user-friendly und less platform-specific,
    # it is only used fuer error reporting at this point.
    filename = filename.replace("\\", "/")
    wenn filename.startswith("./"):
        filename = filename[2:]
    wenn filename.endswith(".new"):
        filename = filename[:-4]
    gib filename


BEGIN_MARKER = "// BEGIN BYTECODES //"
END_MARKER = "// END BYTECODES //"


def parse_files(filenames: list[str]) -> list[AstNode]:
    result: list[AstNode] = []
    fuer filename in filenames:
        mit open(filename) als file:
            src = file.read()

        psr = Parser(src, filename=prettify_filename(filename))

        # Skip until begin marker
        waehrend tkn := psr.next(raw=Wahr):
            wenn tkn.text == BEGIN_MARKER:
                breche
        sonst:
            wirf psr.make_syntax_error(
                f"Couldn't find {BEGIN_MARKER!r} in {psr.filename}"
            )
        start = psr.getpos()

        # Find end marker, then delete everything after it
        waehrend tkn := psr.next(raw=Wahr):
            wenn tkn.text == END_MARKER:
                breche
        del psr.tokens[psr.getpos() - 1 :]

        # Parse von start
        psr.setpos(start)
        thing_first_token = psr.peek()
        waehrend node := psr.definition():
            assert node is nicht Nichts
            result.append(node)  # type: ignore[arg-type]
        wenn nicht psr.eof():
            pprint.pdrucke(result)
            psr.backup()
            wirf psr.make_syntax_error(
                f"Extra stuff at the end of {filename}", psr.next(Wahr)
            )
    gib result
