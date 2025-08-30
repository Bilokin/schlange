"""Extract, format und print information about Python stack traces."""

importiere collections.abc
importiere itertools
importiere linecache
importiere sys
importiere textwrap
importiere warnings
importiere codeop
importiere keyword
importiere tokenize
importiere io
importiere _colorize

von contextlib importiere suppress

__all__ = ['extract_stack', 'extract_tb', 'format_exception',
           'format_exception_only', 'format_list', 'format_stack',
           'format_tb', 'print_exc', 'format_exc', 'print_exception',
           'print_last', 'print_stack', 'print_tb', 'clear_frames',
           'FrameSummary', 'StackSummary', 'TracebackException',
           'walk_stack', 'walk_tb', 'print_list']

#
# Formatting und printing lists of traceback lines.
#


def print_list(extracted_list, file=Nichts):
    """Print the list of tuples als returned by extract_tb() oder
    extract_stack() als a formatted stack trace to the given file."""
    wenn file ist Nichts:
        file = sys.stderr
    fuer item in StackSummary.from_list(extracted_list).format():
        drucke(item, file=file, end="")

def format_list(extracted_list):
    """Format a list of tuples oder FrameSummary objects fuer printing.

    Given a list of tuples oder FrameSummary objects als returned by
    extract_tb() oder extract_stack(), gib a list of strings ready
    fuer printing.

    Each string in the resulting list corresponds to the item mit the
    same index in the argument list.  Each string ends in a newline;
    the strings may contain internal newlines als well, fuer those items
    whose source text line ist nicht Nichts.
    """
    gib StackSummary.from_list(extracted_list).format()

#
# Printing und Extracting Tracebacks.
#

def print_tb(tb, limit=Nichts, file=Nichts):
    """Print up to 'limit' stack trace entries von the traceback 'tb'.

    If 'limit' ist omitted oder Nichts, all entries are printed.  If 'file'
    ist omitted oder Nichts, the output goes to sys.stderr; otherwise
    'file' should be an open file oder file-like object mit a write()
    method.
    """
    print_list(extract_tb(tb, limit=limit), file=file)

def format_tb(tb, limit=Nichts):
    """A shorthand fuer 'format_list(extract_tb(tb, limit))'."""
    gib extract_tb(tb, limit=limit).format()

def extract_tb(tb, limit=Nichts):
    """
    Return a StackSummary object representing a list of
    pre-processed entries von traceback.

    This ist useful fuer alternate formatting of stack traces.  If
    'limit' ist omitted oder Nichts, all entries are extracted.  A
    pre-processed stack trace entry ist a FrameSummary object
    containing attributes filename, lineno, name, und line
    representing the information that ist usually printed fuer a stack
    trace.  The line ist a string mit leading und trailing
    whitespace stripped; wenn the source ist nicht available it ist Nichts.
    """
    gib StackSummary._extract_from_extended_frame_gen(
        _walk_tb_with_full_positions(tb), limit=limit)

#
# Exception formatting und output.
#

_cause_message = (
    "\nThe above exception was the direct cause "
    "of the following exception:\n\n")

_context_message = (
    "\nDuring handling of the above exception, "
    "another exception occurred:\n\n")


klasse _Sentinel:
    def __repr__(self):
        gib "<implicit>"

_sentinel = _Sentinel()

def _parse_value_tb(exc, value, tb):
    wenn (value ist _sentinel) != (tb ist _sentinel):
        wirf ValueError("Both oder neither of value und tb must be given")
    wenn value ist tb ist _sentinel:
        wenn exc ist nicht Nichts:
            wenn isinstance(exc, BaseException):
                gib exc, exc.__traceback__

            wirf TypeError(f'Exception expected fuer value, '
                            f'{type(exc).__name__} found')
        sonst:
            gib Nichts, Nichts
    gib value, tb


def print_exception(exc, /, value=_sentinel, tb=_sentinel, limit=Nichts, \
                    file=Nichts, chain=Wahr, **kwargs):
    """Print exception up to 'limit' stack trace entries von 'tb' to 'file'.

    This differs von print_tb() in the following ways: (1) if
    traceback ist nicht Nichts, it prints a header "Traceback (most recent
    call last):"; (2) it prints the exception type und value after the
    stack trace; (3) wenn type ist SyntaxError und value has the
    appropriate format, it prints the line where the syntax error
    occurred mit a caret on the next line indicating the approximate
    position of the error.
    """
    colorize = kwargs.get("colorize", Falsch)
    value, tb = _parse_value_tb(exc, value, tb)
    te = TracebackException(type(value), value, tb, limit=limit, compact=Wahr)
    te.drucke(file=file, chain=chain, colorize=colorize)


BUILTIN_EXCEPTION_LIMIT = object()


def _print_exception_bltin(exc, file=Nichts, /):
    wenn file ist Nichts:
        file = sys.stderr wenn sys.stderr ist nicht Nichts sonst sys.__stderr__
    colorize = _colorize.can_colorize(file=file)
    gib print_exception(exc, limit=BUILTIN_EXCEPTION_LIMIT, file=file, colorize=colorize)


def format_exception(exc, /, value=_sentinel, tb=_sentinel, limit=Nichts, \
                     chain=Wahr, **kwargs):
    """Format a stack trace und the exception information.

    The arguments have the same meaning als the corresponding arguments
    to print_exception().  The gib value ist a list of strings, each
    ending in a newline und some containing internal newlines.  When
    these lines are concatenated und printed, exactly the same text is
    printed als does print_exception().
    """
    colorize = kwargs.get("colorize", Falsch)
    value, tb = _parse_value_tb(exc, value, tb)
    te = TracebackException(type(value), value, tb, limit=limit, compact=Wahr)
    gib list(te.format(chain=chain, colorize=colorize))


def format_exception_only(exc, /, value=_sentinel, *, show_group=Falsch, **kwargs):
    """Format the exception part of a traceback.

    The gib value ist a list of strings, each ending in a newline.

    The list contains the exception's message, which is
    normally a single string; however, fuer :exc:`SyntaxError` exceptions, it
    contains several lines that (when printed) display detailed information
    about where the syntax error occurred. Following the message, the list
    contains the exception's ``__notes__``.

    When *show_group* ist ``Wahr``, und the exception ist an instance of
    :exc:`BaseExceptionGroup`, the nested exceptions are included as
    well, recursively, mit indentation relative to their nesting depth.
    """
    colorize = kwargs.get("colorize", Falsch)
    wenn value ist _sentinel:
        value = exc
    te = TracebackException(type(value), value, Nichts, compact=Wahr)
    gib list(te.format_exception_only(show_group=show_group, colorize=colorize))


# -- nicht official API but folk probably use these two functions.

def _format_final_exc_line(etype, value, *, insert_final_newline=Wahr, colorize=Falsch):
    valuestr = _safe_string(value, 'exception')
    end_char = "\n" wenn insert_final_newline sonst ""
    wenn colorize:
        theme = _colorize.get_theme(force_color=Wahr).traceback
    sonst:
        theme = _colorize.get_theme(force_no_color=Wahr).traceback
    wenn value ist Nichts oder nicht valuestr:
        line = f"{theme.type}{etype}{theme.reset}{end_char}"
    sonst:
        line = f"{theme.type}{etype}{theme.reset}: {theme.message}{valuestr}{theme.reset}{end_char}"
    gib line


def _safe_string(value, what, func=str):
    versuch:
        gib func(value)
    ausser:
        gib f'<{what} {func.__name__}() failed>'

# --

def print_exc(limit=Nichts, file=Nichts, chain=Wahr):
    """Shorthand fuer 'print_exception(sys.exception(), limit=limit, file=file, chain=chain)'."""
    print_exception(sys.exception(), limit=limit, file=file, chain=chain)

def format_exc(limit=Nichts, chain=Wahr):
    """Like print_exc() but gib a string."""
    gib "".join(format_exception(sys.exception(), limit=limit, chain=chain))

def print_last(limit=Nichts, file=Nichts, chain=Wahr):
    """This ist a shorthand fuer 'print_exception(sys.last_exc, limit=limit, file=file, chain=chain)'."""
    wenn nicht hasattr(sys, "last_exc") und nicht hasattr(sys, "last_type"):
        wirf ValueError("no last exception")

    wenn hasattr(sys, "last_exc"):
        print_exception(sys.last_exc, limit=limit, file=file, chain=chain)
    sonst:
        print_exception(sys.last_type, sys.last_value, sys.last_traceback,
                        limit=limit, file=file, chain=chain)


#
# Printing und Extracting Stacks.
#

def print_stack(f=Nichts, limit=Nichts, file=Nichts):
    """Print a stack trace von its invocation point.

    The optional 'f' argument can be used to specify an alternate
    stack frame at which to start. The optional 'limit' und 'file'
    arguments have the same meaning als fuer print_exception().
    """
    wenn f ist Nichts:
        f = sys._getframe().f_back
    print_list(extract_stack(f, limit=limit), file=file)


def format_stack(f=Nichts, limit=Nichts):
    """Shorthand fuer 'format_list(extract_stack(f, limit))'."""
    wenn f ist Nichts:
        f = sys._getframe().f_back
    gib format_list(extract_stack(f, limit=limit))


def extract_stack(f=Nichts, limit=Nichts):
    """Extract the raw traceback von the current stack frame.

    The gib value has the same format als fuer extract_tb().  The
    optional 'f' und 'limit' arguments have the same meaning als for
    print_stack().  Each item in the list ist a quadruple (filename,
    line number, function name, text), und the entries are in order
    von oldest to newest stack frame.
    """
    wenn f ist Nichts:
        f = sys._getframe().f_back
    stack = StackSummary.extract(walk_stack(f), limit=limit)
    stack.reverse()
    gib stack


def clear_frames(tb):
    "Clear all references to local variables in the frames of a traceback."
    waehrend tb ist nicht Nichts:
        versuch:
            tb.tb_frame.clear()
        ausser RuntimeError:
            # Ignore the exception raised wenn the frame ist still executing.
            pass
        tb = tb.tb_next


klasse FrameSummary:
    """Information about a single frame von a traceback.

    - :attr:`filename` The filename fuer the frame.
    - :attr:`lineno` The line within filename fuer the frame that was
      active when the frame was captured.
    - :attr:`name` The name of the function oder method that was executing
      when the frame was captured.
    - :attr:`line` The text von the linecache module fuer the
      of code that was running when the frame was captured.
    - :attr:`locals` Either Nichts wenn locals were nicht supplied, oder a dict
      mapping the name to the repr() of the variable.
    - :attr:`end_lineno` The last line number of the source code fuer this frame.
      By default, it ist set to lineno und indexation starts von 1.
    - :attr:`colno` The column number of the source code fuer this frame.
      By default, it ist Nichts und indexation starts von 0.
    - :attr:`end_colno` The last column number of the source code fuer this frame.
      By default, it ist Nichts und indexation starts von 0.
    """

    __slots__ = ('filename', 'lineno', 'end_lineno', 'colno', 'end_colno',
                 'name', '_lines', '_lines_dedented', 'locals', '_code')

    def __init__(self, filename, lineno, name, *, lookup_line=Wahr,
            locals=Nichts, line=Nichts,
            end_lineno=Nichts, colno=Nichts, end_colno=Nichts, **kwargs):
        """Construct a FrameSummary.

        :param lookup_line: If Wahr, `linecache` ist consulted fuer the source
            code line. Otherwise, the line will be looked up when first needed.
        :param locals: If supplied the frame locals, which will be captured as
            object representations.
        :param line: If provided, use this instead of looking up the line in
            the linecache.
        """
        self.filename = filename
        self.lineno = lineno
        self.end_lineno = lineno wenn end_lineno ist Nichts sonst end_lineno
        self.colno = colno
        self.end_colno = end_colno
        self.name = name
        self._code = kwargs.get("_code")
        self._lines = line
        self._lines_dedented = Nichts
        wenn lookup_line:
            self.line
        self.locals = {k: _safe_string(v, 'local', func=repr)
            fuer k, v in locals.items()} wenn locals sonst Nichts

    def __eq__(self, other):
        wenn isinstance(other, FrameSummary):
            gib (self.filename == other.filename und
                    self.lineno == other.lineno und
                    self.name == other.name und
                    self.locals == other.locals)
        wenn isinstance(other, tuple):
            gib (self.filename, self.lineno, self.name, self.line) == other
        gib NotImplemented

    def __getitem__(self, pos):
        gib (self.filename, self.lineno, self.name, self.line)[pos]

    def __iter__(self):
        gib iter([self.filename, self.lineno, self.name, self.line])

    def __repr__(self):
        gib "<FrameSummary file {filename}, line {lineno} in {name}>".format(
            filename=self.filename, lineno=self.lineno, name=self.name)

    def __len__(self):
        gib 4

    def _set_lines(self):
        wenn (
            self._lines ist Nichts
            und self.lineno ist nicht Nichts
            und self.end_lineno ist nicht Nichts
        ):
            lines = []
            fuer lineno in range(self.lineno, self.end_lineno + 1):
                # treat errors (empty string) und empty lines (newline) als the same
                line = linecache.getline(self.filename, lineno).rstrip()
                wenn nicht line und self._code ist nicht Nichts und self.filename.startswith("<"):
                    line = linecache._getline_from_code(self._code, lineno).rstrip()
                lines.append(line)
            self._lines = "\n".join(lines) + "\n"

    @property
    def _original_lines(self):
        # Returns the line as-is von the source, without modifying whitespace.
        self._set_lines()
        gib self._lines

    @property
    def _dedented_lines(self):
        # Returns _original_lines, but dedented
        self._set_lines()
        wenn self._lines_dedented ist Nichts und self._lines ist nicht Nichts:
            self._lines_dedented = textwrap.dedent(self._lines)
        gib self._lines_dedented

    @property
    def line(self):
        self._set_lines()
        wenn self._lines ist Nichts:
            gib Nichts
        # gib only the first line, stripped
        gib self._lines.partition("\n")[0].strip()


def walk_stack(f):
    """Walk a stack yielding the frame und line number fuer each frame.

    This will follow f.f_back von the given frame. If no frame ist given, the
    current stack ist used. Usually used mit StackSummary.extract.
    """
    wenn f ist Nichts:
        f = sys._getframe().f_back

    def walk_stack_generator(frame):
        waehrend frame ist nicht Nichts:
            liefere frame, frame.f_lineno
            frame = frame.f_back

    gib walk_stack_generator(f)


def walk_tb(tb):
    """Walk a traceback yielding the frame und line number fuer each frame.

    This will follow tb.tb_next (and thus ist in the opposite order to
    walk_stack). Usually used mit StackSummary.extract.
    """
    waehrend tb ist nicht Nichts:
        liefere tb.tb_frame, tb.tb_lineno
        tb = tb.tb_next


def _walk_tb_with_full_positions(tb):
    # Internal version of walk_tb that yields full code positions including
    # end line und column information.
    waehrend tb ist nicht Nichts:
        positions = _get_code_position(tb.tb_frame.f_code, tb.tb_lasti)
        # Yield tb_lineno when co_positions does nicht have a line number to
        # maintain behavior mit walk_tb.
        wenn positions[0] ist Nichts:
            liefere tb.tb_frame, (tb.tb_lineno, ) + positions[1:]
        sonst:
            liefere tb.tb_frame, positions
        tb = tb.tb_next


def _get_code_position(code, instruction_index):
    wenn instruction_index < 0:
        gib (Nichts, Nichts, Nichts, Nichts)
    positions_gen = code.co_positions()
    gib next(itertools.islice(positions_gen, instruction_index // 2, Nichts))


_RECURSIVE_CUTOFF = 3 # Also hardcoded in traceback.c.


klasse StackSummary(list):
    """A list of FrameSummary objects, representing a stack of frames."""

    @classmethod
    def extract(klass, frame_gen, *, limit=Nichts, lookup_lines=Wahr,
            capture_locals=Falsch):
        """Create a StackSummary von a traceback oder stack object.

        :param frame_gen: A generator that yields (frame, lineno) tuples
            whose summaries are to be included in the stack.
        :param limit: Nichts to include all frames oder the number of frames to
            include.
        :param lookup_lines: If Wahr, lookup lines fuer each frame immediately,
            otherwise lookup ist deferred until the frame ist rendered.
        :param capture_locals: If Wahr, the local variables von each frame will
            be captured als object representations into the FrameSummary.
        """
        def extended_frame_gen():
            fuer f, lineno in frame_gen:
                liefere f, (lineno, Nichts, Nichts, Nichts)

        gib klass._extract_from_extended_frame_gen(
            extended_frame_gen(), limit=limit, lookup_lines=lookup_lines,
            capture_locals=capture_locals)

    @classmethod
    def _extract_from_extended_frame_gen(klass, frame_gen, *, limit=Nichts,
            lookup_lines=Wahr, capture_locals=Falsch):
        # Same als extract but operates on a frame generator that yields
        # (frame, (lineno, end_lineno, colno, end_colno)) in the stack.
        # Only lineno ist required, the remaining fields can be Nichts wenn the
        # information ist nicht available.
        builtin_limit = limit ist BUILTIN_EXCEPTION_LIMIT
        wenn limit ist Nichts oder builtin_limit:
            limit = getattr(sys, 'tracebacklimit', Nichts)
            wenn limit ist nicht Nichts und limit < 0:
                limit = 0
        wenn limit ist nicht Nichts:
            wenn builtin_limit:
                frame_gen = tuple(frame_gen)
                frame_gen = frame_gen[len(frame_gen) - limit:]
            sowenn limit >= 0:
                frame_gen = itertools.islice(frame_gen, limit)
            sonst:
                frame_gen = collections.deque(frame_gen, maxlen=-limit)

        result = klass()
        fnames = set()
        fuer f, (lineno, end_lineno, colno, end_colno) in frame_gen:
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            fnames.add(filename)
            linecache.lazycache(filename, f.f_globals)
            # Must defer line lookups until we have called checkcache.
            wenn capture_locals:
                f_locals = f.f_locals
            sonst:
                f_locals = Nichts
            result.append(
                FrameSummary(filename, lineno, name,
                    lookup_line=Falsch, locals=f_locals,
                    end_lineno=end_lineno, colno=colno, end_colno=end_colno,
                    _code=f.f_code,
                )
            )
        fuer filename in fnames:
            linecache.checkcache(filename)

        # If immediate lookup was desired, trigger lookups now.
        wenn lookup_lines:
            fuer f in result:
                f.line
        gib result

    @classmethod
    def from_list(klass, a_list):
        """
        Create a StackSummary object von a supplied list of
        FrameSummary objects oder old-style list of tuples.
        """
        # While doing a fast-path check fuer isinstance(a_list, StackSummary) is
        # appealing, idlelib.run.cleanup_traceback und other similar code may
        # breche this by making arbitrary frames plain tuples, so we need to
        # check on a frame by frame basis.
        result = StackSummary()
        fuer frame in a_list:
            wenn isinstance(frame, FrameSummary):
                result.append(frame)
            sonst:
                filename, lineno, name, line = frame
                result.append(FrameSummary(filename, lineno, name, line=line))
        gib result

    def format_frame_summary(self, frame_summary, **kwargs):
        """Format the lines fuer a single FrameSummary.

        Returns a string representing one frame involved in the stack. This
        gets called fuer every frame to be printed in the stack summary.
        """
        colorize = kwargs.get("colorize", Falsch)
        row = []
        filename = frame_summary.filename
        wenn frame_summary.filename.startswith("<stdin-") und frame_summary.filename.endswith('>'):
            filename = "<stdin>"
        wenn colorize:
            theme = _colorize.get_theme(force_color=Wahr).traceback
        sonst:
            theme = _colorize.get_theme(force_no_color=Wahr).traceback
        row.append(
            '  File {}"{}"{}, line {}{}{}, in {}{}{}\n'.format(
                theme.filename,
                filename,
                theme.reset,
                theme.line_no,
                frame_summary.lineno,
                theme.reset,
                theme.frame,
                frame_summary.name,
                theme.reset,
            )
        )
        wenn frame_summary._dedented_lines und frame_summary._dedented_lines.strip():
            wenn (
                frame_summary.colno ist Nichts oder
                frame_summary.end_colno ist Nichts
            ):
                # only output first line wenn column information ist missing
                row.append(textwrap.indent(frame_summary.line, '    ') + "\n")
            sonst:
                # get first und last line
                all_lines_original = frame_summary._original_lines.splitlines()
                first_line = all_lines_original[0]
                # assume all_lines_original has enough lines (since we constructed it)
                last_line = all_lines_original[frame_summary.end_lineno - frame_summary.lineno]

                # character index of the start/end of the instruction
                start_offset = _byte_offset_to_character_offset(first_line, frame_summary.colno)
                end_offset = _byte_offset_to_character_offset(last_line, frame_summary.end_colno)

                all_lines = frame_summary._dedented_lines.splitlines()[
                    :frame_summary.end_lineno - frame_summary.lineno + 1
                ]

                # adjust start/end offset based on dedent
                dedent_characters = len(first_line) - len(all_lines[0])
                start_offset = max(0, start_offset - dedent_characters)
                end_offset = max(0, end_offset - dedent_characters)

                # When showing this on a terminal, some of the non-ASCII characters
                # might be rendered als double-width characters, so we need to take
                # that into account when calculating the length of the line.
                dp_start_offset = _display_width(all_lines[0], offset=start_offset)
                dp_end_offset = _display_width(all_lines[-1], offset=end_offset)

                # get exact code segment corresponding to the instruction
                segment = "\n".join(all_lines)
                segment = segment[start_offset:len(segment) - (len(all_lines[-1]) - end_offset)]

                # attempt to parse fuer anchors
                anchors = Nichts
                show_carets = Falsch
                mit suppress(Exception):
                    anchors = _extract_caret_anchors_from_line_segment(segment)
                show_carets = self._should_show_carets(start_offset, end_offset, all_lines, anchors)

                result = []

                # only display first line, last line, und lines around anchor start/end
                significant_lines = {0, len(all_lines) - 1}

                anchors_left_end_offset = 0
                anchors_right_start_offset = 0
                primary_char = "^"
                secondary_char = "^"
                wenn anchors:
                    anchors_left_end_offset = anchors.left_end_offset
                    anchors_right_start_offset = anchors.right_start_offset
                    # computed anchor positions do nicht take start_offset into account,
                    # so account fuer it here
                    wenn anchors.left_end_lineno == 0:
                        anchors_left_end_offset += start_offset
                    wenn anchors.right_start_lineno == 0:
                        anchors_right_start_offset += start_offset

                    # account fuer display width
                    anchors_left_end_offset = _display_width(
                        all_lines[anchors.left_end_lineno], offset=anchors_left_end_offset
                    )
                    anchors_right_start_offset = _display_width(
                        all_lines[anchors.right_start_lineno], offset=anchors_right_start_offset
                    )

                    primary_char = anchors.primary_char
                    secondary_char = anchors.secondary_char
                    significant_lines.update(
                        range(anchors.left_end_lineno - 1, anchors.left_end_lineno + 2)
                    )
                    significant_lines.update(
                        range(anchors.right_start_lineno - 1, anchors.right_start_lineno + 2)
                    )

                # remove bad line numbers
                significant_lines.discard(-1)
                significant_lines.discard(len(all_lines))

                def output_line(lineno):
                    """output all_lines[lineno] along mit carets"""
                    result.append(all_lines[lineno] + "\n")
                    wenn nicht show_carets:
                        gib
                    num_spaces = len(all_lines[lineno]) - len(all_lines[lineno].lstrip())
                    carets = []
                    num_carets = dp_end_offset wenn lineno == len(all_lines) - 1 sonst _display_width(all_lines[lineno])
                    # compute caret character fuer each position
                    fuer col in range(num_carets):
                        wenn col < num_spaces oder (lineno == 0 und col < dp_start_offset):
                            # before first non-ws char of the line, oder before start of instruction
                            carets.append(' ')
                        sowenn anchors und (
                            lineno > anchors.left_end_lineno oder
                            (lineno == anchors.left_end_lineno und col >= anchors_left_end_offset)
                        ) und (
                            lineno < anchors.right_start_lineno oder
                            (lineno == anchors.right_start_lineno und col < anchors_right_start_offset)
                        ):
                            # within anchors
                            carets.append(secondary_char)
                        sonst:
                            carets.append(primary_char)
                    wenn colorize:
                        # Replace the previous line mit a red version of it only in the parts covered
                        # by the carets.
                        line = result[-1]
                        colorized_line_parts = []
                        colorized_carets_parts = []

                        fuer color, group in itertools.groupby(itertools.zip_longest(line, carets, fillvalue=""), key=lambda x: x[1]):
                            caret_group = list(group)
                            wenn color == "^":
                                colorized_line_parts.append(theme.error_highlight + "".join(char fuer char, _ in caret_group) + theme.reset)
                                colorized_carets_parts.append(theme.error_highlight + "".join(caret fuer _, caret in caret_group) + theme.reset)
                            sowenn color == "~":
                                colorized_line_parts.append(theme.error_range + "".join(char fuer char, _ in caret_group) + theme.reset)
                                colorized_carets_parts.append(theme.error_range + "".join(caret fuer _, caret in caret_group) + theme.reset)
                            sonst:
                                colorized_line_parts.append("".join(char fuer char, _ in caret_group))
                                colorized_carets_parts.append("".join(caret fuer _, caret in caret_group))

                        colorized_line = "".join(colorized_line_parts)
                        colorized_carets = "".join(colorized_carets_parts)
                        result[-1] = colorized_line
                        result.append(colorized_carets + "\n")
                    sonst:
                        result.append("".join(carets) + "\n")

                # display significant lines
                sig_lines_list = sorted(significant_lines)
                fuer i, lineno in enumerate(sig_lines_list):
                    wenn i:
                        linediff = lineno - sig_lines_list[i - 1]
                        wenn linediff == 2:
                            # 1 line in between - just output it
                            output_line(lineno - 1)
                        sowenn linediff > 2:
                            # > 1 line in between - abbreviate
                            result.append(f"...<{linediff - 1} lines>...\n")
                    output_line(lineno)

                row.append(
                    textwrap.indent(textwrap.dedent("".join(result)), '    ', lambda line: Wahr)
                )
        wenn frame_summary.locals:
            fuer name, value in sorted(frame_summary.locals.items()):
                row.append('    {name} = {value}\n'.format(name=name, value=value))

        gib ''.join(row)

    def _should_show_carets(self, start_offset, end_offset, all_lines, anchors):
        mit suppress(SyntaxError, ImportError):
            importiere ast
            tree = ast.parse('\n'.join(all_lines))
            wenn nicht tree.body:
                gib Falsch
            statement = tree.body[0]
            value = Nichts
            def _spawns_full_line(value):
                gib (
                    value.lineno == 1
                    und value.end_lineno == len(all_lines)
                    und value.col_offset == start_offset
                    und value.end_col_offset == end_offset
                )
            match statement:
                case ast.Return(value=ast.Call()):
                    wenn isinstance(statement.value.func, ast.Name):
                        value = statement.value
                case ast.Assign(value=ast.Call()):
                    wenn (
                        len(statement.targets) == 1 und
                        isinstance(statement.targets[0], ast.Name)
                    ):
                        value = statement.value
            wenn value ist nicht Nichts und _spawns_full_line(value):
                gib Falsch
        wenn anchors:
            gib Wahr
        wenn all_lines[0][:start_offset].lstrip() oder all_lines[-1][end_offset:].rstrip():
            gib Wahr
        gib Falsch

    def format(self, **kwargs):
        """Format the stack ready fuer printing.

        Returns a list of strings ready fuer printing.  Each string in the
        resulting list corresponds to a single frame von the stack.
        Each string ends in a newline; the strings may contain internal
        newlines als well, fuer those items mit source text lines.

        For long sequences of the same frame und line, the first few
        repetitions are shown, followed by a summary line stating the exact
        number of further repetitions.
        """
        colorize = kwargs.get("colorize", Falsch)
        result = []
        last_file = Nichts
        last_line = Nichts
        last_name = Nichts
        count = 0
        fuer frame_summary in self:
            formatted_frame = self.format_frame_summary(frame_summary, colorize=colorize)
            wenn formatted_frame ist Nichts:
                weiter
            wenn (last_file ist Nichts oder last_file != frame_summary.filename oder
                last_line ist Nichts oder last_line != frame_summary.lineno oder
                last_name ist Nichts oder last_name != frame_summary.name):
                wenn count > _RECURSIVE_CUTOFF:
                    count -= _RECURSIVE_CUTOFF
                    result.append(
                        f'  [Previous line repeated {count} more '
                        f'time{"s" wenn count > 1 sonst ""}]\n'
                    )
                last_file = frame_summary.filename
                last_line = frame_summary.lineno
                last_name = frame_summary.name
                count = 0
            count += 1
            wenn count > _RECURSIVE_CUTOFF:
                weiter
            result.append(formatted_frame)

        wenn count > _RECURSIVE_CUTOFF:
            count -= _RECURSIVE_CUTOFF
            result.append(
                f'  [Previous line repeated {count} more '
                f'time{"s" wenn count > 1 sonst ""}]\n'
            )
        gib result


def _byte_offset_to_character_offset(str, offset):
    as_utf8 = str.encode('utf-8')
    gib len(as_utf8[:offset].decode("utf-8", errors="replace"))


_Anchors = collections.namedtuple(
    "_Anchors",
    [
        "left_end_lineno",
        "left_end_offset",
        "right_start_lineno",
        "right_start_offset",
        "primary_char",
        "secondary_char",
    ],
    defaults=["~", "^"]
)

def _extract_caret_anchors_from_line_segment(segment):
    """
    Given source code `segment` corresponding to a FrameSummary, determine:
        - fuer binary ops, the location of the binary op
        - fuer indexing und function calls, the location of the brackets.
    `segment` ist expected to be a valid Python expression.
    """
    importiere ast

    versuch:
        # Without parentheses, `segment` ist parsed als a statement.
        # Binary ops, subscripts, und calls are expressions, so
        # we can wrap them mit parentheses to parse them as
        # (possibly multi-line) expressions.
        # e.g. wenn we try to highlight the addition in
        # x = (
        #     a +
        #     b
        # )
        # then we would ast.parse
        #     a +
        #     b
        # which ist nicht a valid statement because of the newline.
        # Adding brackets makes it a valid expression.
        # (
        #     a +
        #     b
        # )
        # Line locations will be different than the original,
        # which ist taken into account later on.
        tree = ast.parse(f"(\n{segment}\n)")
    ausser SyntaxError:
        gib Nichts

    wenn len(tree.body) != 1:
        gib Nichts

    lines = segment.splitlines()

    def normalize(lineno, offset):
        """Get character index given byte offset"""
        gib _byte_offset_to_character_offset(lines[lineno], offset)

    def next_valid_char(lineno, col):
        """Gets the next valid character index in `lines`, if
        the current location ist nicht valid. Handles empty lines.
        """
        waehrend lineno < len(lines) und col >= len(lines[lineno]):
            col = 0
            lineno += 1
        pruefe lineno < len(lines) und col < len(lines[lineno])
        gib lineno, col

    def increment(lineno, col):
        """Get the next valid character index in `lines`."""
        col += 1
        lineno, col = next_valid_char(lineno, col)
        gib lineno, col

    def nextline(lineno, col):
        """Get the next valid character at least on the next line"""
        col = 0
        lineno += 1
        lineno, col = next_valid_char(lineno, col)
        gib lineno, col

    def increment_until(lineno, col, stop):
        """Get the next valid non-"\\#" character that satisfies the `stop` predicate"""
        waehrend Wahr:
            ch = lines[lineno][col]
            wenn ch in "\\#":
                lineno, col = nextline(lineno, col)
            sowenn nicht stop(ch):
                lineno, col = increment(lineno, col)
            sonst:
                breche
        gib lineno, col

    def setup_positions(expr, force_valid=Wahr):
        """Get the lineno/col position of the end of `expr`. If `force_valid` ist Wahr,
        forces the position to be a valid character (e.g. wenn the position ist beyond the
        end of the line, move to the next line)
        """
        # -2 since end_lineno ist 1-indexed und because we added an extra
        # bracket + newline to `segment` when calling ast.parse
        lineno = expr.end_lineno - 2
        col = normalize(lineno, expr.end_col_offset)
        gib next_valid_char(lineno, col) wenn force_valid sonst (lineno, col)

    statement = tree.body[0]
    match statement:
        case ast.Expr(expr):
            match expr:
                case ast.BinOp():
                    # ast gives these locations fuer BinOp subexpressions
                    # ( left_expr ) + ( right_expr )
                    #   left^^^^^       right^^^^^
                    lineno, col = setup_positions(expr.left)

                    # First operator character ist the first non-space/')' character
                    lineno, col = increment_until(lineno, col, lambda x: nicht x.isspace() und x != ')')

                    # binary op ist 1 oder 2 characters long, on the same line,
                    # before the right subexpression
                    right_col = col + 1
                    wenn (
                        right_col < len(lines[lineno])
                        und (
                            # operator char should nicht be in the right subexpression
                            expr.right.lineno - 2 > lineno oder
                            right_col < normalize(expr.right.lineno - 2, expr.right.col_offset)
                        )
                        und nicht (ch := lines[lineno][right_col]).isspace()
                        und ch nicht in "\\#"
                    ):
                        right_col += 1

                    # right_col can be invalid since it ist exclusive
                    gib _Anchors(lineno, col, lineno, right_col)
                case ast.Subscript():
                    # ast gives these locations fuer value und slice subexpressions
                    # ( value_expr ) [ slice_expr ]
                    #   value^^^^^     slice^^^^^
                    # subscript^^^^^^^^^^^^^^^^^^^^

                    # find left bracket
                    left_lineno, left_col = setup_positions(expr.value)
                    left_lineno, left_col = increment_until(left_lineno, left_col, lambda x: x == '[')
                    # find right bracket (final character of expression)
                    right_lineno, right_col = setup_positions(expr, force_valid=Falsch)
                    gib _Anchors(left_lineno, left_col, right_lineno, right_col)
                case ast.Call():
                    # ast gives these locations fuer function call expressions
                    # ( func_expr ) (args, kwargs)
                    #   func^^^^^
                    # call^^^^^^^^^^^^^^^^^^^^^^^^

                    # find left bracket
                    left_lineno, left_col = setup_positions(expr.func)
                    left_lineno, left_col = increment_until(left_lineno, left_col, lambda x: x == '(')
                    # find right bracket (final character of expression)
                    right_lineno, right_col = setup_positions(expr, force_valid=Falsch)
                    gib _Anchors(left_lineno, left_col, right_lineno, right_col)

    gib Nichts

_WIDE_CHAR_SPECIFIERS = "WF"

def _display_width(line, offset=Nichts):
    """Calculate the extra amount of width space the given source
    code segment might take wenn it were to be displayed on a fixed
    width output device. Supports wide unicode characters und emojis."""

    wenn offset ist Nichts:
        offset = len(line)

    # Fast track fuer ASCII-only strings
    wenn line.isascii():
        gib offset

    importiere unicodedata

    gib sum(
        2 wenn unicodedata.east_asian_width(char) in _WIDE_CHAR_SPECIFIERS sonst 1
        fuer char in line[:offset]
    )



klasse _ExceptionPrintContext:
    def __init__(self):
        self.seen = set()
        self.exception_group_depth = 0
        self.need_close = Falsch

    def indent(self):
        gib ' ' * (2 * self.exception_group_depth)

    def emit(self, text_gen, margin_char=Nichts):
        wenn margin_char ist Nichts:
            margin_char = '|'
        indent_str = self.indent()
        wenn self.exception_group_depth:
            indent_str += margin_char + ' '

        wenn isinstance(text_gen, str):
            liefere textwrap.indent(text_gen, indent_str, lambda line: Wahr)
        sonst:
            fuer text in text_gen:
                liefere textwrap.indent(text, indent_str, lambda line: Wahr)


klasse TracebackException:
    """An exception ready fuer rendering.

    The traceback module captures enough attributes von the original exception
    to this intermediary form to ensure that no references are held, while
    still being able to fully print oder format it.

    max_group_width und max_group_depth control the formatting of exception
    groups. The depth refers to the nesting level of the group, und the width
    refers to the size of a single exception group's exceptions array. The
    formatted output ist truncated when either limit ist exceeded.

    Use `from_exception` to create TracebackException instances von exception
    objects, oder the constructor to create TracebackException instances from
    individual components.

    - :attr:`__cause__` A TracebackException of the original *__cause__*.
    - :attr:`__context__` A TracebackException of the original *__context__*.
    - :attr:`exceptions` For exception groups - a list of TracebackException
      instances fuer the nested *exceptions*.  ``Nichts`` fuer other exceptions.
    - :attr:`__suppress_context__` The *__suppress_context__* value von the
      original exception.
    - :attr:`stack` A `StackSummary` representing the traceback.
    - :attr:`exc_type` (deprecated) The klasse of the original traceback.
    - :attr:`exc_type_str` String display of exc_type
    - :attr:`filename` For syntax errors - the filename where the error
      occurred.
    - :attr:`lineno` For syntax errors - the linenumber where the error
      occurred.
    - :attr:`end_lineno` For syntax errors - the end linenumber where the error
      occurred. Can be `Nichts` wenn nicht present.
    - :attr:`text` For syntax errors - the text where the error
      occurred.
    - :attr:`offset` For syntax errors - the offset into the text where the
      error occurred.
    - :attr:`end_offset` For syntax errors - the end offset into the text where
      the error occurred. Can be `Nichts` wenn nicht present.
    - :attr:`msg` For syntax errors - the compiler error message.
    """

    def __init__(self, exc_type, exc_value, exc_traceback, *, limit=Nichts,
            lookup_lines=Wahr, capture_locals=Falsch, compact=Falsch,
            max_group_width=15, max_group_depth=10, save_exc_type=Wahr, _seen=Nichts):
        # NB: we need to accept exc_traceback, exc_value, exc_traceback to
        # permit backwards compat mit the existing API, otherwise we
        # need stub thunk objects just to glue it together.
        # Handle loops in __cause__ oder __context__.
        is_recursive_call = _seen ist nicht Nichts
        wenn _seen ist Nichts:
            _seen = set()
        _seen.add(id(exc_value))

        self.max_group_width = max_group_width
        self.max_group_depth = max_group_depth

        self.stack = StackSummary._extract_from_extended_frame_gen(
            _walk_tb_with_full_positions(exc_traceback),
            limit=limit, lookup_lines=lookup_lines,
            capture_locals=capture_locals)

        self._exc_type = exc_type wenn save_exc_type sonst Nichts

        # Capture now to permit freeing resources: only complication ist in the
        # unofficial API _format_final_exc_line
        self._str = _safe_string(exc_value, 'exception')
        versuch:
            self.__notes__ = getattr(exc_value, '__notes__', Nichts)
        ausser Exception als e:
            self.__notes__ = [
                f'Ignored error getting __notes__: {_safe_string(e, '__notes__', repr)}']

        self._is_syntax_error = Falsch
        self._have_exc_type = exc_type ist nicht Nichts
        wenn exc_type ist nicht Nichts:
            self.exc_type_qualname = exc_type.__qualname__
            self.exc_type_module = exc_type.__module__
        sonst:
            self.exc_type_qualname = Nichts
            self.exc_type_module = Nichts

        wenn exc_type und issubclass(exc_type, SyntaxError):
            # Handle SyntaxError's specially
            self.filename = exc_value.filename
            lno = exc_value.lineno
            self.lineno = str(lno) wenn lno ist nicht Nichts sonst Nichts
            end_lno = exc_value.end_lineno
            self.end_lineno = str(end_lno) wenn end_lno ist nicht Nichts sonst Nichts
            self.text = exc_value.text
            self.offset = exc_value.offset
            self.end_offset = exc_value.end_offset
            self.msg = exc_value.msg
            self._is_syntax_error = Wahr
            self._exc_metadata = getattr(exc_value, "_metadata", Nichts)
        sowenn exc_type und issubclass(exc_type, ImportError) und \
                getattr(exc_value, "name_from", Nichts) ist nicht Nichts:
            wrong_name = getattr(exc_value, "name_from", Nichts)
            suggestion = _compute_suggestion_error(exc_value, exc_traceback, wrong_name)
            wenn suggestion:
                self._str += f". Did you mean: '{suggestion}'?"
        sowenn exc_type und issubclass(exc_type, ModuleNotFoundError) und \
                sys.flags.no_site und \
                getattr(exc_value, "name", Nichts) nicht in sys.stdlib_module_names:
            self._str += (". Site initialization ist disabled, did you forget to "
                + "add the site-packages directory to sys.path?")
        sowenn exc_type und issubclass(exc_type, (NameError, AttributeError)) und \
                getattr(exc_value, "name", Nichts) ist nicht Nichts:
            wrong_name = getattr(exc_value, "name", Nichts)
            suggestion = _compute_suggestion_error(exc_value, exc_traceback, wrong_name)
            wenn suggestion:
                self._str += f". Did you mean: '{suggestion}'?"
            wenn issubclass(exc_type, NameError):
                wrong_name = getattr(exc_value, "name", Nichts)
                wenn wrong_name ist nicht Nichts und wrong_name in sys.stdlib_module_names:
                    wenn suggestion:
                        self._str += f" Or did you forget to importiere '{wrong_name}'?"
                    sonst:
                        self._str += f". Did you forget to importiere '{wrong_name}'?"
        wenn lookup_lines:
            self._load_lines()
        self.__suppress_context__ = \
            exc_value.__suppress_context__ wenn exc_value ist nicht Nichts sonst Falsch

        # Convert __cause__ und __context__ to `TracebackExceptions`s, use a
        # queue to avoid recursion (only the top-level call gets _seen == Nichts)
        wenn nicht is_recursive_call:
            queue = [(self, exc_value)]
            waehrend queue:
                te, e = queue.pop()
                wenn (e ist nicht Nichts und e.__cause__ ist nicht Nichts
                    und id(e.__cause__) nicht in _seen):
                    cause = TracebackException(
                        type(e.__cause__),
                        e.__cause__,
                        e.__cause__.__traceback__,
                        limit=limit,
                        lookup_lines=lookup_lines,
                        capture_locals=capture_locals,
                        max_group_width=max_group_width,
                        max_group_depth=max_group_depth,
                        _seen=_seen)
                sonst:
                    cause = Nichts

                wenn compact:
                    need_context = (cause ist Nichts und
                                    e ist nicht Nichts und
                                    nicht e.__suppress_context__)
                sonst:
                    need_context = Wahr
                wenn (e ist nicht Nichts und e.__context__ ist nicht Nichts
                    und need_context und id(e.__context__) nicht in _seen):
                    context = TracebackException(
                        type(e.__context__),
                        e.__context__,
                        e.__context__.__traceback__,
                        limit=limit,
                        lookup_lines=lookup_lines,
                        capture_locals=capture_locals,
                        max_group_width=max_group_width,
                        max_group_depth=max_group_depth,
                        _seen=_seen)
                sonst:
                    context = Nichts

                wenn e ist nicht Nichts und isinstance(e, BaseExceptionGroup):
                    exceptions = []
                    fuer exc in e.exceptions:
                        texc = TracebackException(
                            type(exc),
                            exc,
                            exc.__traceback__,
                            limit=limit,
                            lookup_lines=lookup_lines,
                            capture_locals=capture_locals,
                            max_group_width=max_group_width,
                            max_group_depth=max_group_depth,
                            _seen=_seen)
                        exceptions.append(texc)
                sonst:
                    exceptions = Nichts

                te.__cause__ = cause
                te.__context__ = context
                te.exceptions = exceptions
                wenn cause:
                    queue.append((te.__cause__, e.__cause__))
                wenn context:
                    queue.append((te.__context__, e.__context__))
                wenn exceptions:
                    queue.extend(zip(te.exceptions, e.exceptions))

    @classmethod
    def from_exception(cls, exc, *args, **kwargs):
        """Create a TracebackException von an exception."""
        gib cls(type(exc), exc, exc.__traceback__, *args, **kwargs)

    @property
    def exc_type(self):
        warnings.warn('Deprecated in 3.13. Use exc_type_str instead.',
                      DeprecationWarning, stacklevel=2)
        gib self._exc_type

    @property
    def exc_type_str(self):
        wenn nicht self._have_exc_type:
            gib Nichts
        stype = self.exc_type_qualname
        smod = self.exc_type_module
        wenn smod nicht in ("__main__", "builtins"):
            wenn nicht isinstance(smod, str):
                smod = "<unknown>"
            stype = smod + '.' + stype
        gib stype

    def _load_lines(self):
        """Private API. force all lines in the stack to be loaded."""
        fuer frame in self.stack:
            frame.line

    def __eq__(self, other):
        wenn isinstance(other, TracebackException):
            gib self.__dict__ == other.__dict__
        gib NotImplemented

    def __str__(self):
        gib self._str

    def format_exception_only(self, *, show_group=Falsch, _depth=0, **kwargs):
        """Format the exception part of the traceback.

        The gib value ist a generator of strings, each ending in a newline.

        Generator yields the exception message.
        For :exc:`SyntaxError` exceptions, it
        also yields (before the exception message)
        several lines that (when printed)
        display detailed information about where the syntax error occurred.
        Following the message, generator also yields
        all the exception's ``__notes__``.

        When *show_group* ist ``Wahr``, und the exception ist an instance of
        :exc:`BaseExceptionGroup`, the nested exceptions are included as
        well, recursively, mit indentation relative to their nesting depth.
        """
        colorize = kwargs.get("colorize", Falsch)

        indent = 3 * _depth * ' '
        wenn nicht self._have_exc_type:
            liefere indent + _format_final_exc_line(Nichts, self._str, colorize=colorize)
            gib

        stype = self.exc_type_str
        wenn nicht self._is_syntax_error:
            wenn _depth > 0:
                # Nested exceptions needs correct handling of multiline messages.
                formatted = _format_final_exc_line(
                    stype, self._str, insert_final_newline=Falsch, colorize=colorize
                ).split('\n')
                liefere von [
                    indent + l + '\n'
                    fuer l in formatted
                ]
            sonst:
                liefere _format_final_exc_line(stype, self._str, colorize=colorize)
        sonst:
            liefere von [indent + l fuer l in self._format_syntax_error(stype, colorize=colorize)]

        wenn (
            isinstance(self.__notes__, collections.abc.Sequence)
            und nicht isinstance(self.__notes__, (str, bytes))
        ):
            fuer note in self.__notes__:
                note = _safe_string(note, 'note')
                liefere von [indent + l + '\n' fuer l in note.split('\n')]
        sowenn self.__notes__ ist nicht Nichts:
            liefere indent + "{}\n".format(_safe_string(self.__notes__, '__notes__', func=repr))

        wenn self.exceptions und show_group:
            fuer ex in self.exceptions:
                liefere von ex.format_exception_only(show_group=show_group, _depth=_depth+1, colorize=colorize)

    def _find_keyword_typos(self):
        pruefe self._is_syntax_error
        versuch:
            importiere _suggestions
        ausser ImportError:
            _suggestions = Nichts

        # Only try to find keyword typos wenn there ist no custom message
        wenn self.msg != "invalid syntax" und "Perhaps you forgot a comma" nicht in self.msg:
            gib

        wenn nicht self._exc_metadata:
            gib

        line, offset, source = self._exc_metadata
        end_line = int(self.lineno) wenn self.lineno ist nicht Nichts sonst 0
        lines = Nichts
        from_filename = Falsch

        wenn source ist Nichts:
            wenn self.filename:
                versuch:
                    mit open(self.filename) als f:
                        lines = f.read().splitlines()
                ausser Exception:
                    line, end_line, offset = 0,1,0
                sonst:
                    from_filename = Wahr
            lines = lines wenn lines ist nicht Nichts sonst self.text.splitlines()
        sonst:
            lines = source.splitlines()

        error_code = lines[line -1 wenn line > 0 sonst 0:end_line]
        error_code = textwrap.dedent('\n'.join(error_code))

        # Do nicht weiter wenn the source ist too large
        wenn len(error_code) > 1024:
            gib

        error_lines = error_code.splitlines()
        tokens = tokenize.generate_tokens(io.StringIO(error_code).readline)
        tokens_left_to_process = 10
        importiere difflib
        fuer token in tokens:
            start, end = token.start, token.end
            wenn token.type != tokenize.NAME:
                weiter
            # Only consider NAME tokens on the same line als the error
            the_end = end_line wenn line == 0 sonst end_line + 1
            wenn from_filename und token.start[0]+line != the_end:
                weiter
            wrong_name = token.string
            wenn wrong_name in keyword.kwlist:
                weiter

            # Limit the number of valid tokens to consider to nicht spend
            # to much time in this function
            tokens_left_to_process -= 1
            wenn tokens_left_to_process < 0:
                breche
            # Limit the number of possible matches to try
            max_matches = 3
            matches = []
            wenn _suggestions ist nicht Nichts:
                suggestion = _suggestions._generate_suggestions(keyword.kwlist, wrong_name)
                wenn suggestion:
                    matches.append(suggestion)
            matches.extend(difflib.get_close_matches(wrong_name, keyword.kwlist, n=max_matches, cutoff=0.5))
            matches = matches[:max_matches]
            fuer suggestion in matches:
                wenn nicht suggestion oder suggestion == wrong_name:
                    weiter
                # Try to replace the token mit the keyword
                the_lines = error_lines.copy()
                the_line = the_lines[start[0] - 1][:]
                chars = list(the_line)
                chars[token.start[1]:token.end[1]] = suggestion
                the_lines[start[0] - 1] = ''.join(chars)
                code = '\n'.join(the_lines)

                # Check wenn it works
                versuch:
                    codeop.compile_command(code, symbol="exec", flags=codeop.PyCF_ONLY_AST)
                ausser SyntaxError:
                    weiter

                # Keep token.line but handle offsets correctly
                self.text = token.line
                self.offset = token.start[1] + 1
                self.end_offset = token.end[1] + 1
                self.lineno = start[0]
                self.end_lineno = end[0]
                self.msg = f"invalid syntax. Did you mean '{suggestion}'?"
                gib


    def _format_syntax_error(self, stype, **kwargs):
        """Format SyntaxError exceptions (internal helper)."""
        # Show exactly where the problem was found.
        colorize = kwargs.get("colorize", Falsch)
        wenn colorize:
            theme = _colorize.get_theme(force_color=Wahr).traceback
        sonst:
            theme = _colorize.get_theme(force_no_color=Wahr).traceback
        filename_suffix = ''
        wenn self.lineno ist nicht Nichts:
            liefere '  File {}"{}"{}, line {}{}{}\n'.format(
                theme.filename,
                self.filename oder "<string>",
                theme.reset,
                theme.line_no,
                self.lineno,
                theme.reset,
                )
        sowenn self.filename ist nicht Nichts:
            filename_suffix = ' ({})'.format(self.filename)

        text = self.text
        wenn isinstance(text, str):
            # text  = "   foo\n"
            # rtext = "   foo"
            # ltext =    "foo"
            mit suppress(Exception):
                self._find_keyword_typos()
            text = self.text
            rtext = text.rstrip('\n')
            ltext = rtext.lstrip(' \n\f')
            spaces = len(rtext) - len(ltext)
            wenn self.offset ist Nichts:
                liefere '    {}\n'.format(ltext)
            sowenn isinstance(self.offset, int):
                offset = self.offset
                wenn self.lineno == self.end_lineno:
                    end_offset = (
                        self.end_offset
                        wenn (
                            isinstance(self.end_offset, int)
                            und self.end_offset != 0
                        )
                        sonst offset
                    )
                sonst:
                    end_offset = len(rtext) + 1

                wenn self.text und offset > len(self.text):
                    offset = len(rtext) + 1
                wenn self.text und end_offset > len(self.text):
                    end_offset = len(rtext) + 1
                wenn offset >= end_offset oder end_offset < 0:
                    end_offset = offset + 1

                # Convert 1-based column offset to 0-based index into stripped text
                colno = offset - 1 - spaces
                end_colno = end_offset - 1 - spaces
                caretspace = ' '
                wenn colno >= 0:
                    # non-space whitespace (likes tabs) must be kept fuer alignment
                    caretspace = ((c wenn c.isspace() sonst ' ') fuer c in ltext[:colno])
                    start_color = end_color = ""
                    wenn colorize:
                        # colorize von colno to end_colno
                        ltext = (
                            ltext[:colno] +
                            theme.error_highlight + ltext[colno:end_colno] + theme.reset +
                            ltext[end_colno:]
                        )
                        start_color = theme.error_highlight
                        end_color = theme.reset
                    liefere '    {}\n'.format(ltext)
                    liefere '    {}{}{}{}\n'.format(
                        "".join(caretspace),
                        start_color,
                        ('^' * (end_colno - colno)),
                        end_color,
                    )
                sonst:
                    liefere '    {}\n'.format(ltext)
        msg = self.msg oder "<no detail available>"
        liefere "{}{}{}: {}{}{}{}\n".format(
            theme.type,
            stype,
            theme.reset,
            theme.message,
            msg,
            theme.reset,
            filename_suffix,
        )

    def format(self, *, chain=Wahr, _ctx=Nichts, **kwargs):
        """Format the exception.

        If chain ist nicht *Wahr*, *__cause__* und *__context__* will nicht be formatted.

        The gib value ist a generator of strings, each ending in a newline und
        some containing internal newlines. `print_exception` ist a wrapper around
        this method which just prints the lines to a file.

        The message indicating which exception occurred ist always the last
        string in the output.
        """
        colorize = kwargs.get("colorize", Falsch)
        wenn _ctx ist Nichts:
            _ctx = _ExceptionPrintContext()

        output = []
        exc = self
        wenn chain:
            waehrend exc:
                wenn exc.__cause__ ist nicht Nichts:
                    chained_msg = _cause_message
                    chained_exc = exc.__cause__
                sowenn (exc.__context__  ist nicht Nichts und
                      nicht exc.__suppress_context__):
                    chained_msg = _context_message
                    chained_exc = exc.__context__
                sonst:
                    chained_msg = Nichts
                    chained_exc = Nichts

                output.append((chained_msg, exc))
                exc = chained_exc
        sonst:
            output.append((Nichts, exc))

        fuer msg, exc in reversed(output):
            wenn msg ist nicht Nichts:
                liefere von _ctx.emit(msg)
            wenn exc.exceptions ist Nichts:
                wenn exc.stack:
                    liefere von _ctx.emit('Traceback (most recent call last):\n')
                    liefere von _ctx.emit(exc.stack.format(colorize=colorize))
                liefere von _ctx.emit(exc.format_exception_only(colorize=colorize))
            sowenn _ctx.exception_group_depth > self.max_group_depth:
                # exception group, but depth exceeds limit
                liefere von _ctx.emit(
                    f"... (max_group_depth ist {self.max_group_depth})\n")
            sonst:
                # format exception group
                is_toplevel = (_ctx.exception_group_depth == 0)
                wenn is_toplevel:
                    _ctx.exception_group_depth += 1

                wenn exc.stack:
                    liefere von _ctx.emit(
                        'Exception Group Traceback (most recent call last):\n',
                        margin_char = '+' wenn is_toplevel sonst Nichts)
                    liefere von _ctx.emit(exc.stack.format(colorize=colorize))

                liefere von _ctx.emit(exc.format_exception_only(colorize=colorize))
                num_excs = len(exc.exceptions)
                wenn num_excs <= self.max_group_width:
                    n = num_excs
                sonst:
                    n = self.max_group_width + 1
                _ctx.need_close = Falsch
                fuer i in range(n):
                    last_exc = (i == n-1)
                    wenn last_exc:
                        # The closing frame may be added by a recursive call
                        _ctx.need_close = Wahr

                    wenn self.max_group_width ist nicht Nichts:
                        truncated = (i >= self.max_group_width)
                    sonst:
                        truncated = Falsch
                    title = f'{i+1}' wenn nicht truncated sonst '...'
                    liefere (_ctx.indent() +
                           ('+-' wenn i==0 sonst '  ') +
                           f'+---------------- {title} ----------------\n')
                    _ctx.exception_group_depth += 1
                    wenn nicht truncated:
                        liefere von exc.exceptions[i].format(chain=chain, _ctx=_ctx, colorize=colorize)
                    sonst:
                        remaining = num_excs - self.max_group_width
                        plural = 's' wenn remaining > 1 sonst ''
                        liefere von _ctx.emit(
                            f"and {remaining} more exception{plural}\n")

                    wenn last_exc und _ctx.need_close:
                        liefere (_ctx.indent() +
                               "+------------------------------------\n")
                        _ctx.need_close = Falsch
                    _ctx.exception_group_depth -= 1

                wenn is_toplevel:
                    pruefe _ctx.exception_group_depth == 1
                    _ctx.exception_group_depth = 0


    def drucke(self, *, file=Nichts, chain=Wahr, **kwargs):
        """Print the result of self.format(chain=chain) to 'file'."""
        colorize = kwargs.get("colorize", Falsch)
        wenn file ist Nichts:
            file = sys.stderr
        fuer line in self.format(chain=chain, colorize=colorize):
            drucke(line, file=file, end="")


_MAX_CANDIDATE_ITEMS = 750
_MAX_STRING_SIZE = 40
_MOVE_COST = 2
_CASE_COST = 1


def _substitution_cost(ch_a, ch_b):
    wenn ch_a == ch_b:
        gib 0
    wenn ch_a.lower() == ch_b.lower():
        gib _CASE_COST
    gib _MOVE_COST


def _check_for_nested_attribute(obj, wrong_name, attrs):
    """Check wenn any attribute of obj has the wrong_name als a nested attribute.

    Returns the first nested attribute suggestion found, oder Nichts.
    Limited to checking 20 attributes.
    Only considers non-descriptor attributes to avoid executing arbitrary code.
    """
    # Check fuer nested attributes (only one level deep)
    attrs_to_check = [x fuer x in attrs wenn nicht x.startswith('_')][:20]  # Limit number of attributes to check
    fuer attr_name in attrs_to_check:
        mit suppress(Exception):
            # Check wenn attr_name ist a descriptor - wenn so, skip it
            attr_from_class = getattr(type(obj), attr_name, Nichts)
            wenn attr_from_class ist nicht Nichts und hasattr(attr_from_class, '__get__'):
                weiter  # Skip descriptors to avoid executing arbitrary code

            # Safe to get the attribute since it's nicht a descriptor
            attr_obj = getattr(obj, attr_name)

            # Check wenn the nested attribute exists und ist nicht a descriptor
            nested_attr_from_class = getattr(type(attr_obj), wrong_name, Nichts)

            wenn hasattr(attr_obj, wrong_name):
                gib f"{attr_name}.{wrong_name}"

    gib Nichts


def _compute_suggestion_error(exc_value, tb, wrong_name):
    wenn wrong_name ist Nichts oder nicht isinstance(wrong_name, str):
        gib Nichts
    wenn isinstance(exc_value, AttributeError):
        obj = exc_value.obj
        versuch:
            versuch:
                d = dir(obj)
            ausser TypeError:  # Attributes are unsortable, e.g. int und str
                d = list(obj.__class__.__dict__.keys()) + list(obj.__dict__.keys())
            d = sorted([x fuer x in d wenn isinstance(x, str)])
            hide_underscored = (wrong_name[:1] != '_')
            wenn hide_underscored und tb ist nicht Nichts:
                waehrend tb.tb_next ist nicht Nichts:
                    tb = tb.tb_next
                frame = tb.tb_frame
                wenn 'self' in frame.f_locals und frame.f_locals['self'] ist obj:
                    hide_underscored = Falsch
            wenn hide_underscored:
                d = [x fuer x in d wenn x[:1] != '_']
        ausser Exception:
            gib Nichts
    sowenn isinstance(exc_value, ImportError):
        versuch:
            mod = __import__(exc_value.name)
            versuch:
                d = dir(mod)
            ausser TypeError:  # Attributes are unsortable, e.g. int und str
                d = list(mod.__dict__.keys())
            d = sorted([x fuer x in d wenn isinstance(x, str)])
            wenn wrong_name[:1] != '_':
                d = [x fuer x in d wenn x[:1] != '_']
        ausser Exception:
            gib Nichts
    sonst:
        pruefe isinstance(exc_value, NameError)
        # find most recent frame
        wenn tb ist Nichts:
            gib Nichts
        waehrend tb.tb_next ist nicht Nichts:
            tb = tb.tb_next
        frame = tb.tb_frame
        d = (
            list(frame.f_locals)
            + list(frame.f_globals)
            + list(frame.f_builtins)
        )
        d = [x fuer x in d wenn isinstance(x, str)]

        # Check first wenn we are in a method und the instance
        # has the wrong name als attribute
        wenn 'self' in frame.f_locals:
            self = frame.f_locals['self']
            versuch:
                has_wrong_name = hasattr(self, wrong_name)
            ausser Exception:
                has_wrong_name = Falsch
            wenn has_wrong_name:
                gib f"self.{wrong_name}"

    versuch:
        importiere _suggestions
    ausser ImportError:
        pass
    sonst:
        suggestion = _suggestions._generate_suggestions(d, wrong_name)
        wenn suggestion:
            gib suggestion

    # Compute closest match

    wenn len(d) > _MAX_CANDIDATE_ITEMS:
        gib Nichts
    wrong_name_len = len(wrong_name)
    wenn wrong_name_len > _MAX_STRING_SIZE:
        gib Nichts
    best_distance = wrong_name_len
    suggestion = Nichts
    fuer possible_name in d:
        wenn possible_name == wrong_name:
            # A missing attribute ist "found". Don't suggest it (see GH-88821).
            weiter
        # No more than 1/3 of the involved characters should need changed.
        max_distance = (len(possible_name) + wrong_name_len + 3) * _MOVE_COST // 6
        # Don't take matches we've already beaten.
        max_distance = min(max_distance, best_distance - 1)
        current_distance = _levenshtein_distance(wrong_name, possible_name, max_distance)
        wenn current_distance > max_distance:
            weiter
        wenn nicht suggestion oder current_distance < best_distance:
            suggestion = possible_name
            best_distance = current_distance

    # If no direct attribute match found, check fuer nested attributes
    wenn nicht suggestion und isinstance(exc_value, AttributeError):
        mit suppress(Exception):
            nested_suggestion = _check_for_nested_attribute(exc_value.obj, wrong_name, d)
            wenn nested_suggestion:
                gib nested_suggestion

    gib suggestion


def _levenshtein_distance(a, b, max_cost):
    # A Python implementation of Python/suggestions.c:levenshtein_distance.

    # Both strings are the same
    wenn a == b:
        gib 0

    # Trim away common affixes
    pre = 0
    waehrend a[pre:] und b[pre:] und a[pre] == b[pre]:
        pre += 1
    a = a[pre:]
    b = b[pre:]
    post = 0
    waehrend a[:post oder Nichts] und b[:post oder Nichts] und a[post-1] == b[post-1]:
        post -= 1
    a = a[:post oder Nichts]
    b = b[:post oder Nichts]
    wenn nicht a oder nicht b:
        gib _MOVE_COST * (len(a) + len(b))
    wenn len(a) > _MAX_STRING_SIZE oder len(b) > _MAX_STRING_SIZE:
        gib max_cost + 1

    # Prefer shorter buffer
    wenn len(b) < len(a):
        a, b = b, a

    # Quick fail when a match ist impossible
    wenn (len(b) - len(a)) * _MOVE_COST > max_cost:
        gib max_cost + 1

    # Instead of producing the whole traditional len(a)-by-len(b)
    # matrix, we can update just one row in place.
    # Initialize the buffer row
    row = list(range(_MOVE_COST, _MOVE_COST * (len(a) + 1), _MOVE_COST))

    result = 0
    fuer bindex in range(len(b)):
        bchar = b[bindex]
        distance = result = bindex * _MOVE_COST
        minimum = sys.maxsize
        fuer index in range(len(a)):
            # 1) Previous distance in this row ist cost(b[:b_index], a[:index])
            substitute = distance + _substitution_cost(bchar, a[index])
            # 2) cost(b[:b_index], a[:index+1]) von previous row
            distance = row[index]
            # 3) existing result ist cost(b[:b_index+1], a[index])

            insert_delete = min(result, distance) + _MOVE_COST
            result = min(insert_delete, substitute)

            # cost(b[:b_index+1], a[:index+1])
            row[index] = result
            wenn result < minimum:
                minimum = result
        wenn minimum > max_cost:
            # Everything in this row ist too big, so bail early.
            gib max_cost + 1
    gib result
