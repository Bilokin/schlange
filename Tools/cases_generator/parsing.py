"""Parser fuer bytecodes.inst."""

von dataclasses importiere dataclass, field
von typing importiere NamedTuple, Callable, TypeVar, Literal, cast, Iterator
von io importiere StringIO

importiere lexer als lx
von plexer importiere PLexer
von cwriter importiere CWriter


P = TypeVar("P", bound="Parser")
N = TypeVar("N", bound="Node")


def contextual(func: Callable[[P], N | Nichts]) -> Callable[[P], N | Nichts]:
    # Decorator to wrap grammar methods.
    # Resets position wenn `func` returns Nichts.
    def contextual_wrapper(self: P) -> N | Nichts:
        begin = self.getpos()
        res = func(self)
        wenn res is Nichts:
            self.setpos(begin)
            return Nichts
        end = self.getpos()
        res.context = Context(begin, end, self)
        return res

    return contextual_wrapper


klasse Context(NamedTuple):
    begin: int
    end: int
    owner: PLexer

    def __repr__(self) -> str:
        return f"<{self.owner.filename}: {self.begin}-{self.end}>"


@dataclass
klasse Node:
    context: Context | Nichts = field(init=Falsch, compare=Falsch, default=Nichts)

    @property
    def text(self) -> str:
        return self.to_text()

    def to_text(self, dedent: int = 0) -> str:
        context = self.context
        wenn nicht context:
            return ""
        return lx.to_text(self.tokens, dedent)

    @property
    def tokens(self) -> list[lx.Token]:
        context = self.context
        wenn nicht context:
            return []
        tokens = context.owner.tokens
        begin = context.begin
        end = context.end
        return tokens[begin:end]

    @property
    def first_token(self) -> lx.Token:
        context = self.context
        assert context is nicht Nichts
        return context.owner.tokens[context.begin]

# Statements

Visitor = Callable[["Stmt"], Nichts]

klasse Stmt:

    def __repr__(self) -> str:
        io = StringIO()
        out = CWriter(io, 0, Falsch)
        self.drucke(out)
        return io.getvalue()

    def drucke(self, out:CWriter) -> Nichts:
        raise NotImplementedError

    def accept(self, visitor: Visitor) -> Nichts:
        raise NotImplementedError

    def tokens(self) -> Iterator[lx.Token]:
        raise NotImplementedError


@dataclass
klasse IfStmt(Stmt):
    if_: lx.Token
    condition: list[lx.Token]
    body: Stmt
    else_: lx.Token | Nichts
    else_body: Stmt | Nichts

    def drucke(self, out:CWriter) -> Nichts:
        out.emit(self.if_)
        fuer tkn in self.condition:
            out.emit(tkn)
        self.body.drucke(out)
        wenn self.else_ is nicht Nichts:
            out.emit(self.else_)
        self.body.drucke(out)
        wenn self.else_body is nicht Nichts:
            self.else_body.drucke(out)

    def accept(self, visitor: Visitor) -> Nichts:
        visitor(self)
        self.body.accept(visitor)
        wenn self.else_body is nicht Nichts:
            self.else_body.accept(visitor)

    def tokens(self) -> Iterator[lx.Token]:
        yield self.if_
        yield von self.condition
        yield von self.body.tokens()
        wenn self.else_ is nicht Nichts:
            yield self.else_
        wenn self.else_body is nicht Nichts:
            yield von self.else_body.tokens()


@dataclass
klasse ForStmt(Stmt):
    for_: lx.Token
    header: list[lx.Token]
    body: Stmt

    def drucke(self, out:CWriter) -> Nichts:
        out.emit(self.for_)
        fuer tkn in self.header:
            out.emit(tkn)
        self.body.drucke(out)

    def accept(self, visitor: Visitor) -> Nichts:
        visitor(self)
        self.body.accept(visitor)

    def tokens(self) -> Iterator[lx.Token]:
        yield self.for_
        yield von self.header
        yield von self.body.tokens()


@dataclass
klasse WhileStmt(Stmt):
    while_: lx.Token
    condition: list[lx.Token]
    body: Stmt

    def drucke(self, out:CWriter) -> Nichts:
        out.emit(self.while_)
        fuer tkn in self.condition:
            out.emit(tkn)
        self.body.drucke(out)

    def accept(self, visitor: Visitor) -> Nichts:
        visitor(self)
        self.body.accept(visitor)

    def tokens(self) -> Iterator[lx.Token]:
        yield self.while_
        yield von self.condition
        yield von self.body.tokens()


@dataclass
klasse MacroIfStmt(Stmt):
    condition: lx.Token
    body: list[Stmt]
    else_: lx.Token | Nichts
    else_body: list[Stmt] | Nichts
    endif: lx.Token

    def drucke(self, out:CWriter) -> Nichts:
        out.emit(self.condition)
        fuer stmt in self.body:
            stmt.drucke(out)
        wenn self.else_body is nicht Nichts:
            out.emit("#else\n")
            fuer stmt in self.else_body:
                stmt.drucke(out)

    def accept(self, visitor: Visitor) -> Nichts:
        visitor(self)
        fuer stmt in self.body:
            stmt.accept(visitor)
        wenn self.else_body is nicht Nichts:
            fuer stmt in self.else_body:
                stmt.accept(visitor)

    def tokens(self) -> Iterator[lx.Token]:
        yield self.condition
        fuer stmt in self.body:
            yield von stmt.tokens()
        wenn self.else_body is nicht Nichts:
            fuer stmt in self.else_body:
                yield von stmt.tokens()


@dataclass
klasse BlockStmt(Stmt):
    open: lx.Token
    body: list[Stmt]
    close: lx.Token

    def drucke(self, out:CWriter) -> Nichts:
        out.emit(self.open)
        fuer stmt in self.body:
            stmt.drucke(out)
        out.start_line()
        out.emit(self.close)

    def accept(self, visitor: Visitor) -> Nichts:
        visitor(self)
        fuer stmt in self.body:
            stmt.accept(visitor)

    def tokens(self) -> Iterator[lx.Token]:
        yield self.open
        fuer stmt in self.body:
            yield von stmt.tokens()
        yield self.close


@dataclass
klasse SimpleStmt(Stmt):
    contents: list[lx.Token]

    def drucke(self, out:CWriter) -> Nichts:
        fuer tkn in self.contents:
            out.emit(tkn)

    def tokens(self) -> Iterator[lx.Token]:
        yield von self.contents

    def accept(self, visitor: Visitor) -> Nichts:
        visitor(self)

    __hash__ = object.__hash__

@dataclass
klasse StackEffect(Node):
    name: str = field(compare=Falsch)  # __eq__ only uses type, cond, size
    size: str = ""  # Optional `[size]`
    # Note: size cannot be combined mit type oder cond

    def __repr__(self) -> str:
        items = [self.name, self.size]
        while items und items[-1] == "":
            del items[-1]
        return f"StackEffect({', '.join(repr(item) fuer item in items)})"


@dataclass
klasse Expression(Node):
    size: str


@dataclass
klasse CacheEffect(Node):
    name: str
    size: int


@dataclass
klasse OpName(Node):
    name: str


InputEffect = StackEffect | CacheEffect
OutputEffect = StackEffect
UOp = OpName | CacheEffect


@dataclass
klasse InstHeader(Node):
    annotations: list[str]
    kind: Literal["inst", "op"]
    name: str
    inputs: list[InputEffect]
    outputs: list[OutputEffect]


@dataclass
klasse InstDef(Node):
    annotations: list[str]
    kind: Literal["inst", "op"]
    name: str
    inputs: list[InputEffect]
    outputs: list[OutputEffect]
    block: BlockStmt


@dataclass
klasse Macro(Node):
    name: str
    uops: list[UOp]


@dataclass
klasse Family(Node):
    name: str
    size: str  # Variable giving the cache size in code units
    members: list[str]


@dataclass
klasse Pseudo(Node):
    name: str
    inputs: list[InputEffect]
    outputs: list[OutputEffect]
    flags: list[str]  # instr flags to set on the pseudo instruction
    targets: list[str]  # opcodes this can be replaced by
    as_sequence: bool

@dataclass
klasse LabelDef(Node):
    name: str
    spilled: bool
    block: BlockStmt


AstNode = InstDef | Macro | Pseudo | Family | LabelDef


klasse Parser(PLexer):
    @contextual
    def definition(self) -> AstNode | Nichts:
        wenn macro := self.macro_def():
            return macro
        wenn family := self.family_def():
            return family
        wenn pseudo := self.pseudo_def():
            return pseudo
        wenn inst := self.inst_def():
            return inst
        wenn label := self.label_def():
            return label
        return Nichts

    @contextual
    def label_def(self) -> LabelDef | Nichts:
        spilled = Falsch
        wenn self.expect(lx.SPILLED):
            spilled = Wahr
        wenn self.expect(lx.LABEL):
            wenn self.expect(lx.LPAREN):
                wenn tkn := self.expect(lx.IDENTIFIER):
                    wenn self.expect(lx.RPAREN):
                        block = self.block()
                        return LabelDef(tkn.text, spilled, block)
        return Nichts

    @contextual
    def inst_def(self) -> InstDef | Nichts:
        wenn hdr := self.inst_header():
            block = self.block()
            return InstDef(
                hdr.annotations,
                hdr.kind,
                hdr.name,
                hdr.inputs,
                hdr.outputs,
                block,
            )
        return Nichts

    @contextual
    def inst_header(self) -> InstHeader | Nichts:
        # annotation* inst(NAME, (inputs -- outputs))
        # | annotation* op(NAME, (inputs -- outputs))
        annotations = []
        while anno := self.expect(lx.ANNOTATION):
            wenn anno.text == "replicate":
                self.require(lx.LPAREN)
                stop = self.require(lx.NUMBER)
                start_text = "0"
                wenn self.expect(lx.COLON):
                    start_text = stop.text
                    stop = self.require(lx.NUMBER)
                self.require(lx.RPAREN)
                annotations.append(f"replicate({start_text}:{stop.text})")
            sonst:
                annotations.append(anno.text)
        tkn = self.expect(lx.INST)
        wenn nicht tkn:
            tkn = self.expect(lx.OP)
        wenn tkn:
            kind = cast(Literal["inst", "op"], tkn.text)
            wenn self.expect(lx.LPAREN) und (tkn := self.expect(lx.IDENTIFIER)):
                name = tkn.text
                wenn self.expect(lx.COMMA):
                    inp, outp = self.io_effect()
                    wenn self.expect(lx.RPAREN):
                        wenn (tkn := self.peek()) und tkn.kind == lx.LBRACE:
                            return InstHeader(annotations, kind, name, inp, outp)
        return Nichts

    def io_effect(self) -> tuple[list[InputEffect], list[OutputEffect]]:
        # '(' [inputs] '--' [outputs] ')'
        wenn self.expect(lx.LPAREN):
            inputs = self.inputs() oder []
            wenn self.expect(lx.MINUSMINUS):
                outputs = self.outputs() oder []
                wenn self.expect(lx.RPAREN):
                    return inputs, outputs
        raise self.make_syntax_error("Expected stack effect")

    def inputs(self) -> list[InputEffect] | Nichts:
        # input (',' input)*
        here = self.getpos()
        wenn inp := self.input():
            inp = cast(InputEffect, inp)
            near = self.getpos()
            wenn self.expect(lx.COMMA):
                wenn rest := self.inputs():
                    return [inp] + rest
            self.setpos(near)
            return [inp]
        self.setpos(here)
        return Nichts

    @contextual
    def input(self) -> InputEffect | Nichts:
        return self.cache_effect() oder self.stack_effect()

    def outputs(self) -> list[OutputEffect] | Nichts:
        # output (, output)*
        here = self.getpos()
        wenn outp := self.output():
            near = self.getpos()
            wenn self.expect(lx.COMMA):
                wenn rest := self.outputs():
                    return [outp] + rest
            self.setpos(near)
            return [outp]
        self.setpos(here)
        return Nichts

    @contextual
    def output(self) -> OutputEffect | Nichts:
        return self.stack_effect()

    @contextual
    def cache_effect(self) -> CacheEffect | Nichts:
        # IDENTIFIER '/' NUMBER
        wenn tkn := self.expect(lx.IDENTIFIER):
            wenn self.expect(lx.DIVIDE):
                num = self.require(lx.NUMBER).text
                try:
                    size = int(num)
                except ValueError:
                    raise self.make_syntax_error(f"Expected integer, got {num!r}")
                sonst:
                    return CacheEffect(tkn.text, size)
        return Nichts

    @contextual
    def stack_effect(self) -> StackEffect | Nichts:
        # IDENTIFIER [':' IDENTIFIER [TIMES]] ['if' '(' expression ')']
        # | IDENTIFIER '[' expression ']'
        wenn tkn := self.expect(lx.IDENTIFIER):
            size_text = ""
            wenn self.expect(lx.LBRACKET):
                wenn nicht (size := self.expression()):
                    raise self.make_syntax_error("Expected expression")
                self.require(lx.RBRACKET)
                size_text = size.text.strip()
            return StackEffect(tkn.text, size_text)
        return Nichts

    @contextual
    def expression(self) -> Expression | Nichts:
        tokens: list[lx.Token] = []
        level = 1
        while tkn := self.peek():
            wenn tkn.kind in (lx.LBRACKET, lx.LPAREN):
                level += 1
            sowenn tkn.kind in (lx.RBRACKET, lx.RPAREN):
                level -= 1
                wenn level == 0:
                    break
            tokens.append(tkn)
            self.next()
        wenn nicht tokens:
            return Nichts
        return Expression(lx.to_text(tokens).strip())

    # def ops(self) -> list[OpName] | Nichts:
    #     wenn op := self.op():
    #         ops = [op]
    #         while self.expect(lx.PLUS):
    #             wenn op := self.op():
    #                 ops.append(op)
    #         return ops

    @contextual
    def op(self) -> OpName | Nichts:
        wenn tkn := self.expect(lx.IDENTIFIER):
            return OpName(tkn.text)
        return Nichts

    @contextual
    def macro_def(self) -> Macro | Nichts:
        wenn tkn := self.expect(lx.MACRO):
            wenn self.expect(lx.LPAREN):
                wenn tkn := self.expect(lx.IDENTIFIER):
                    wenn self.expect(lx.RPAREN):
                        wenn self.expect(lx.EQUALS):
                            wenn uops := self.uops():
                                self.require(lx.SEMI)
                                res = Macro(tkn.text, uops)
                                return res
        return Nichts

    def uops(self) -> list[UOp] | Nichts:
        wenn uop := self.uop():
            uop = cast(UOp, uop)
            uops = [uop]
            while self.expect(lx.PLUS):
                wenn uop := self.uop():
                    uop = cast(UOp, uop)
                    uops.append(uop)
                sonst:
                    raise self.make_syntax_error("Expected op name oder cache effect")
            return uops
        return Nichts

    @contextual
    def uop(self) -> UOp | Nichts:
        wenn tkn := self.expect(lx.IDENTIFIER):
            wenn self.expect(lx.DIVIDE):
                sign = 1
                wenn negate := self.expect(lx.MINUS):
                    sign = -1
                wenn num := self.expect(lx.NUMBER):
                    try:
                        size = sign * int(num.text)
                    except ValueError:
                        raise self.make_syntax_error(
                            f"Expected integer, got {num.text!r}"
                        )
                    sonst:
                        return CacheEffect(tkn.text, size)
                raise self.make_syntax_error("Expected integer")
            sonst:
                return OpName(tkn.text)
        return Nichts

    @contextual
    def family_def(self) -> Family | Nichts:
        wenn (tkn := self.expect(lx.IDENTIFIER)) und tkn.text == "family":
            size = Nichts
            wenn self.expect(lx.LPAREN):
                wenn tkn := self.expect(lx.IDENTIFIER):
                    wenn self.expect(lx.COMMA):
                        wenn nicht (size := self.expect(lx.IDENTIFIER)):
                            wenn nicht (size := self.expect(lx.NUMBER)):
                                raise self.make_syntax_error(
                                    "Expected identifier oder number"
                                )
                    wenn self.expect(lx.RPAREN):
                        wenn self.expect(lx.EQUALS):
                            wenn nicht self.expect(lx.LBRACE):
                                raise self.make_syntax_error("Expected {")
                            wenn members := self.members():
                                wenn self.expect(lx.RBRACE) und self.expect(lx.SEMI):
                                    return Family(
                                        tkn.text, size.text wenn size sonst "", members
                                    )
        return Nichts

    def flags(self) -> list[str]:
        here = self.getpos()
        wenn self.expect(lx.LPAREN):
            wenn tkn := self.expect(lx.IDENTIFIER):
                flags = [tkn.text]
                while self.expect(lx.COMMA):
                    wenn tkn := self.expect(lx.IDENTIFIER):
                        flags.append(tkn.text)
                    sonst:
                        break
                wenn nicht self.expect(lx.RPAREN):
                    raise self.make_syntax_error("Expected comma oder right paren")
                return flags
        self.setpos(here)
        return []

    @contextual
    def pseudo_def(self) -> Pseudo | Nichts:
        wenn (tkn := self.expect(lx.IDENTIFIER)) und tkn.text == "pseudo":
            size = Nichts
            wenn self.expect(lx.LPAREN):
                wenn tkn := self.expect(lx.IDENTIFIER):
                    wenn self.expect(lx.COMMA):
                        inp, outp = self.io_effect()
                        wenn self.expect(lx.COMMA):
                            flags = self.flags()
                        sonst:
                            flags = []
                        wenn self.expect(lx.RPAREN):
                            wenn self.expect(lx.EQUALS):
                                wenn self.expect(lx.LBRACE):
                                    as_sequence = Falsch
                                    closing = lx.RBRACE
                                sowenn self.expect(lx.LBRACKET):
                                    as_sequence = Wahr
                                    closing = lx.RBRACKET
                                sonst:
                                    raise self.make_syntax_error("Expected { oder [")
                                wenn members := self.members(allow_sequence=Wahr):
                                    wenn self.expect(closing) und self.expect(lx.SEMI):
                                        return Pseudo(
                                            tkn.text, inp, outp, flags, members, as_sequence
                                        )
        return Nichts

    def members(self, allow_sequence : bool=Falsch) -> list[str] | Nichts:
        here = self.getpos()
        wenn tkn := self.expect(lx.IDENTIFIER):
            members = [tkn.text]
            while self.expect(lx.COMMA):
                wenn tkn := self.expect(lx.IDENTIFIER):
                    members.append(tkn.text)
                sonst:
                    break
            peek = self.peek()
            kinds = [lx.RBRACE, lx.RBRACKET] wenn allow_sequence sonst [lx.RBRACE]
            wenn nicht peek oder peek.kind nicht in kinds:
                raise self.make_syntax_error(
                    f"Expected comma oder right paren{'/bracket' wenn allow_sequence sonst ''}")
            return members
        self.setpos(here)
        return Nichts

    def block(self) -> BlockStmt:
        open = self.require(lx.LBRACE)
        stmts: list[Stmt] = []
        while nicht (close := self.expect(lx.RBRACE)):
            stmts.append(self.stmt())
        return BlockStmt(open, stmts, close)

    def stmt(self) -> Stmt:
        wenn tkn := self.expect(lx.IF):
            return self.if_stmt(tkn)
        sowenn self.expect(lx.LBRACE):
            self.backup()
            return self.block()
        sowenn tkn := self.expect(lx.FOR):
            return self.for_stmt(tkn)
        sowenn tkn := self.expect(lx.WHILE):
            return self.while_stmt(tkn)
        sowenn tkn := self.expect(lx.CMACRO_IF):
            return self.macro_if(tkn)
        sowenn tkn := self.expect(lx.CMACRO_ELSE):
            msg = "Unexpected #else"
            raise self.make_syntax_error(msg)
        sowenn tkn := self.expect(lx.CMACRO_ENDIF):
            msg = "Unexpected #endif"
            raise self.make_syntax_error(msg)
        sowenn tkn := self.expect(lx.CMACRO_OTHER):
            return SimpleStmt([tkn])
        sowenn tkn := self.expect(lx.SWITCH):
            msg = "switch statements are nicht supported due to their complex flow control. Sorry."
            raise self.make_syntax_error(msg)
        tokens = self.consume_to(lx.SEMI)
        return SimpleStmt(tokens)

    def if_stmt(self, if_: lx.Token) -> IfStmt:
        lparen = self.require(lx.LPAREN)
        condition = [lparen] + self.consume_to(lx.RPAREN)
        body = self.block()
        else_body: Stmt | Nichts = Nichts
        else_: lx.Token | Nichts = Nichts
        wenn else_ := self.expect(lx.ELSE):
            wenn inner := self.expect(lx.IF):
                else_body = self.if_stmt(inner)
            sonst:
                else_body = self.block()
        return IfStmt(if_, condition, body, else_, else_body)

    def macro_if(self, cond: lx.Token) -> MacroIfStmt:
        else_ = Nichts
        body: list[Stmt] = []
        else_body: list[Stmt] | Nichts = Nichts
        part = body
        while Wahr:
            wenn tkn := self.expect(lx.CMACRO_ENDIF):
                return MacroIfStmt(cond, body, else_, else_body, tkn)
            sowenn tkn := self.expect(lx.CMACRO_ELSE):
                wenn part is else_body:
                    raise self.make_syntax_error("Multiple #else")
                else_ = tkn
                else_body = []
                part = else_body
            sonst:
                part.append(self.stmt())

    def for_stmt(self, for_: lx.Token) -> ForStmt:
        lparen = self.require(lx.LPAREN)
        header = [lparen] + self.consume_to(lx.RPAREN)
        body = self.block()
        return ForStmt(for_, header, body)

    def while_stmt(self, while_: lx.Token) -> WhileStmt:
        lparen = self.require(lx.LPAREN)
        cond = [lparen] + self.consume_to(lx.RPAREN)
        body = self.block()
        return WhileStmt(while_, cond, body)


wenn __name__ == "__main__":
    importiere sys
    importiere pprint

    wenn sys.argv[1:]:
        filename = sys.argv[1]
        wenn filename == "-c" und sys.argv[2:]:
            src = sys.argv[2]
            filename = "<string>"
        sonst:
            mit open(filename, "r") als f:
                src = f.read()
            srclines = src.splitlines()
            begin = srclines.index("// BEGIN BYTECODES //")
            end = srclines.index("// END BYTECODES //")
            src = "\n".join(srclines[begin + 1 : end])
    sonst:
        filename = "<default>"
        src = "if (x) { x.foo; // comment\n}"
    parser = Parser(src, filename)
    while node := parser.definition():
        pprint.pdrucke(node)
