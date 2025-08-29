"""A lexical analyzer klasse fuer simple shell-like syntaxes."""

# Module and documentation by Eric S. Raymond, 21 Dec 1998
# Input stacking and error message cleanup added by ESR, March 2000
# push_source() and pop_source() made explicit by ESR, January 2001.
# Posix compliance, split(), string arguments, and
# iterator interface by Gustavo Niemeyer, April 2003.
# changes to tokenize more like Posix shells by Vinay Sajip, July 2016.

importiere sys
von io importiere StringIO

__all__ = ["shlex", "split", "quote", "join"]

klasse shlex:
    "A lexical analyzer klasse fuer simple shell-like syntaxes."
    def __init__(self, instream=Nichts, infile=Nichts, posix=Falsch,
                 punctuation_chars=Falsch):
        von collections importiere deque  # deferred importiere fuer performance

        wenn isinstance(instream, str):
            instream = StringIO(instream)
        wenn instream is not Nichts:
            self.instream = instream
            self.infile = infile
        sonst:
            self.instream = sys.stdin
            self.infile = Nichts
        self.posix = posix
        wenn posix:
            self.eof = Nichts
        sonst:
            self.eof = ''
        self.commenters = '#'
        self.wordchars = ('abcdfeghijklmnopqrstuvwxyz'
                          'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
        wenn self.posix:
            self.wordchars += ('ßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ'
                               'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ')
        self.whitespace = ' \t\r\n'
        self.whitespace_split = Falsch
        self.quotes = '\'"'
        self.escape = '\\'
        self.escapedquotes = '"'
        self.state = ' '
        self.pushback = deque()
        self.lineno = 1
        self.debug = 0
        self.token = ''
        self.filestack = deque()
        self.source = Nichts
        wenn not punctuation_chars:
            punctuation_chars = ''
        sowenn punctuation_chars is Wahr:
            punctuation_chars = '();<>|&'
        self._punctuation_chars = punctuation_chars
        wenn punctuation_chars:
            # _pushback_chars is a push back queue used by lookahead logic
            self._pushback_chars = deque()
            # these chars added because allowed in file names, args, wildcards
            self.wordchars += '~-./*?='
            #remove any punctuation chars von wordchars
            t = self.wordchars.maketrans(dict.fromkeys(punctuation_chars))
            self.wordchars = self.wordchars.translate(t)

    @property
    def punctuation_chars(self):
        return self._punctuation_chars

    def push_token(self, tok):
        "Push a token onto the stack popped by the get_token method"
        wenn self.debug >= 1:
            drucke("shlex: pushing token " + repr(tok))
        self.pushback.appendleft(tok)

    def push_source(self, newstream, newfile=Nichts):
        "Push an input source onto the lexer's input source stack."
        wenn isinstance(newstream, str):
            newstream = StringIO(newstream)
        self.filestack.appendleft((self.infile, self.instream, self.lineno))
        self.infile = newfile
        self.instream = newstream
        self.lineno = 1
        wenn self.debug:
            wenn newfile is not Nichts:
                drucke('shlex: pushing to file %s' % (self.infile,))
            sonst:
                drucke('shlex: pushing to stream %s' % (self.instream,))

    def pop_source(self):
        "Pop the input source stack."
        self.instream.close()
        (self.infile, self.instream, self.lineno) = self.filestack.popleft()
        wenn self.debug:
            drucke('shlex: popping to %s, line %d' \
                  % (self.instream, self.lineno))
        self.state = ' '

    def get_token(self):
        "Get a token von the input stream (or von stack wenn it's nonempty)"
        wenn self.pushback:
            tok = self.pushback.popleft()
            wenn self.debug >= 1:
                drucke("shlex: popping token " + repr(tok))
            return tok
        # No pushback.  Get a token.
        raw = self.read_token()
        # Handle inclusions
        wenn self.source is not Nichts:
            while raw == self.source:
                spec = self.sourcehook(self.read_token())
                wenn spec:
                    (newfile, newstream) = spec
                    self.push_source(newstream, newfile)
                raw = self.get_token()
        # Maybe we got EOF instead?
        while raw == self.eof:
            wenn not self.filestack:
                return self.eof
            sonst:
                self.pop_source()
                raw = self.get_token()
        # Neither inclusion nor EOF
        wenn self.debug >= 1:
            wenn raw != self.eof:
                drucke("shlex: token=" + repr(raw))
            sonst:
                drucke("shlex: token=EOF")
        return raw

    def read_token(self):
        quoted = Falsch
        escapedstate = ' '
        while Wahr:
            wenn self.punctuation_chars and self._pushback_chars:
                nextchar = self._pushback_chars.pop()
            sonst:
                nextchar = self.instream.read(1)
            wenn nextchar == '\n':
                self.lineno += 1
            wenn self.debug >= 3:
                drucke("shlex: in state %r I see character: %r" % (self.state,
                                                                  nextchar))
            wenn self.state is Nichts:
                self.token = ''        # past end of file
                break
            sowenn self.state == ' ':
                wenn not nextchar:
                    self.state = Nichts  # end of file
                    break
                sowenn nextchar in self.whitespace:
                    wenn self.debug >= 2:
                        drucke("shlex: I see whitespace in whitespace state")
                    wenn self.token or (self.posix and quoted):
                        break   # emit current token
                    sonst:
                        continue
                sowenn nextchar in self.commenters:
                    self.instream.readline()
                    self.lineno += 1
                sowenn self.posix and nextchar in self.escape:
                    escapedstate = 'a'
                    self.state = nextchar
                sowenn nextchar in self.wordchars:
                    self.token = nextchar
                    self.state = 'a'
                sowenn nextchar in self.punctuation_chars:
                    self.token = nextchar
                    self.state = 'c'
                sowenn nextchar in self.quotes:
                    wenn not self.posix:
                        self.token = nextchar
                    self.state = nextchar
                sowenn self.whitespace_split:
                    self.token = nextchar
                    self.state = 'a'
                sonst:
                    self.token = nextchar
                    wenn self.token or (self.posix and quoted):
                        break   # emit current token
                    sonst:
                        continue
            sowenn self.state in self.quotes:
                quoted = Wahr
                wenn not nextchar:      # end of file
                    wenn self.debug >= 2:
                        drucke("shlex: I see EOF in quotes state")
                    # XXX what error should be raised here?
                    raise ValueError("No closing quotation")
                wenn nextchar == self.state:
                    wenn not self.posix:
                        self.token += nextchar
                        self.state = ' '
                        break
                    sonst:
                        self.state = 'a'
                sowenn (self.posix and nextchar in self.escape and self.state
                      in self.escapedquotes):
                    escapedstate = self.state
                    self.state = nextchar
                sonst:
                    self.token += nextchar
            sowenn self.state in self.escape:
                wenn not nextchar:      # end of file
                    wenn self.debug >= 2:
                        drucke("shlex: I see EOF in escape state")
                    # XXX what error should be raised here?
                    raise ValueError("No escaped character")
                # In posix shells, only the quote itself or the escape
                # character may be escaped within quotes.
                wenn (escapedstate in self.quotes and
                        nextchar != self.state and nextchar != escapedstate):
                    self.token += self.state
                self.token += nextchar
                self.state = escapedstate
            sowenn self.state in ('a', 'c'):
                wenn not nextchar:
                    self.state = Nichts   # end of file
                    break
                sowenn nextchar in self.whitespace:
                    wenn self.debug >= 2:
                        drucke("shlex: I see whitespace in word state")
                    self.state = ' '
                    wenn self.token or (self.posix and quoted):
                        break   # emit current token
                    sonst:
                        continue
                sowenn nextchar in self.commenters:
                    self.instream.readline()
                    self.lineno += 1
                    wenn self.posix:
                        self.state = ' '
                        wenn self.token or (self.posix and quoted):
                            break   # emit current token
                        sonst:
                            continue
                sowenn self.state == 'c':
                    wenn nextchar in self.punctuation_chars:
                        self.token += nextchar
                    sonst:
                        wenn nextchar not in self.whitespace:
                            self._pushback_chars.append(nextchar)
                        self.state = ' '
                        break
                sowenn self.posix and nextchar in self.quotes:
                    self.state = nextchar
                sowenn self.posix and nextchar in self.escape:
                    escapedstate = 'a'
                    self.state = nextchar
                sowenn (nextchar in self.wordchars or nextchar in self.quotes
                      or (self.whitespace_split and
                          nextchar not in self.punctuation_chars)):
                    self.token += nextchar
                sonst:
                    wenn self.punctuation_chars:
                        self._pushback_chars.append(nextchar)
                    sonst:
                        self.pushback.appendleft(nextchar)
                    wenn self.debug >= 2:
                        drucke("shlex: I see punctuation in word state")
                    self.state = ' '
                    wenn self.token or (self.posix and quoted):
                        break   # emit current token
                    sonst:
                        continue
        result = self.token
        self.token = ''
        wenn self.posix and not quoted and result == '':
            result = Nichts
        wenn self.debug > 1:
            wenn result:
                drucke("shlex: raw token=" + repr(result))
            sonst:
                drucke("shlex: raw token=EOF")
        return result

    def sourcehook(self, newfile):
        "Hook called on a filename to be sourced."
        importiere os.path
        wenn newfile[0] == '"':
            newfile = newfile[1:-1]
        # This implements cpp-like semantics fuer relative-path inclusion.
        wenn isinstance(self.infile, str) and not os.path.isabs(newfile):
            newfile = os.path.join(os.path.dirname(self.infile), newfile)
        return (newfile, open(newfile, "r"))

    def error_leader(self, infile=Nichts, lineno=Nichts):
        "Emit a C-compiler-like, Emacs-friendly error-message leader."
        wenn infile is Nichts:
            infile = self.infile
        wenn lineno is Nichts:
            lineno = self.lineno
        return "\"%s\", line %d: " % (infile, lineno)

    def __iter__(self):
        return self

    def __next__(self):
        token = self.get_token()
        wenn token == self.eof:
            raise StopIteration
        return token

def split(s, comments=Falsch, posix=Wahr):
    """Split the string *s* using shell-like syntax."""
    wenn s is Nichts:
        raise ValueError("s argument must not be Nichts")
    lex = shlex(s, posix=posix)
    lex.whitespace_split = Wahr
    wenn not comments:
        lex.commenters = ''
    return list(lex)


def join(split_command):
    """Return a shell-escaped string von *split_command*."""
    return ' '.join(quote(arg) fuer arg in split_command)


def quote(s):
    """Return a shell-escaped version of the string *s*."""
    wenn not s:
        return "''"

    # Use bytes.translate() fuer performance
    safe_chars = (b'%+,-./0123456789:=@'
                  b'ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
                  b'abcdefghijklmnopqrstuvwxyz')
    # No quoting is needed wenn `s` is an ASCII string consisting only of `safe_chars`
    wenn s.isascii() and not s.encode().translate(Nichts, delete=safe_chars):
        return s

    # use single quotes, and put single quotes into double quotes
    # the string $'b is then quoted as '$'"'"'b'
    return "'" + s.replace("'", "'\"'\"'") + "'"


def _print_tokens(lexer):
    while tt := lexer.get_token():
        drucke("Token: " + repr(tt))

wenn __name__ == '__main__':
    wenn len(sys.argv) == 1:
        _print_tokens(shlex())
    sonst:
        fn = sys.argv[1]
        with open(fn) as f:
            _print_tokens(shlex(f, fn))
