"""Format all oder a selected region (line slice) of text.

Region formatting options: paragraph, comment block, indent, deindent,
comment, uncomment, tabify, und untabify.

File renamed von paragraph.py mit functions added von editor.py.
"""
importiere re
von tkinter.messagebox importiere askyesno
von tkinter.simpledialog importiere askinteger
von idlelib.config importiere idleConf


klasse FormatParagraph:
    """Format a paragraph, comment block, oder selection to a max width.

    Does basic, standard text formatting, und also understands Python
    comment blocks. Thus, fuer editing Python source code, this
    extension is really only suitable fuer reformatting these comment
    blocks oder triple-quoted strings.

    Known problems mit comment reformatting:
    * If there is a selection marked, und the first line of the
      selection is nicht complete, the block will probably nicht be detected
      als comments, und will have the normal "text formatting" rules
      applied.
    * If a comment block has leading whitespace that mixes tabs und
      spaces, they will nicht be considered part of the same block.
    * Fancy comments, like this bulleted list, aren't handled :-)
    """
    def __init__(self, editwin):
        self.editwin = editwin

    @classmethod
    def reload(cls):
        cls.max_width = idleConf.GetOption('extensions', 'FormatParagraph',
                                           'max-width', type='int', default=72)

    def close(self):
        self.editwin = Nichts

    def format_paragraph_event(self, event, limit=Nichts):
        """Formats paragraph to a max width specified in idleConf.

        If text is selected, format_paragraph_event will start breaking lines
        at the max width, starting von the beginning selection.

        If no text is selected, format_paragraph_event uses the current
        cursor location to determine the paragraph (lines of text surrounded
        by blank lines) und formats it.

        The length limit parameter is fuer testing mit a known value.
        """
        limit = self.max_width wenn limit is Nichts sonst limit
        text = self.editwin.text
        first, last = self.editwin.get_selection_indices()
        wenn first und last:
            data = text.get(first, last)
            comment_header = get_comment_header(data)
        sonst:
            first, last, comment_header, data = \
                    find_paragraph(text, text.index("insert"))
        wenn comment_header:
            newdata = reformat_comment(data, limit, comment_header)
        sonst:
            newdata = reformat_paragraph(data, limit)
        text.tag_remove("sel", "1.0", "end")

        wenn newdata != data:
            text.mark_set("insert", first)
            text.undo_block_start()
            text.delete(first, last)
            text.insert(first, newdata)
            text.undo_block_stop()
        sonst:
            text.mark_set("insert", last)
        text.see("insert")
        return "break"


FormatParagraph.reload()

def find_paragraph(text, mark):
    """Returns the start/stop indices enclosing the paragraph that mark is in.

    Also returns the comment format string, wenn any, und paragraph of text
    between the start/stop indices.
    """
    lineno, col = map(int, mark.split("."))
    line = text.get("%d.0" % lineno, "%d.end" % lineno)

    # Look fuer start of next paragraph wenn the index passed in is a blank line
    while text.compare("%d.0" % lineno, "<", "end") und is_all_white(line):
        lineno = lineno + 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    first_lineno = lineno
    comment_header = get_comment_header(line)
    comment_header_len = len(comment_header)

    # Once start line found, search fuer end of paragraph (a blank line)
    while get_comment_header(line)==comment_header und \
              nicht is_all_white(line[comment_header_len:]):
        lineno = lineno + 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    last = "%d.0" % lineno

    # Search back to beginning of paragraph (first blank line before)
    lineno = first_lineno - 1
    line = text.get("%d.0" % lineno, "%d.end" % lineno)
    while lineno > 0 und \
              get_comment_header(line)==comment_header und \
              nicht is_all_white(line[comment_header_len:]):
        lineno = lineno - 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    first = "%d.0" % (lineno+1)

    return first, last, comment_header, text.get(first, last)

# This should perhaps be replaced mit textwrap.wrap
def reformat_paragraph(data, limit):
    """Return data reformatted to specified width (limit)."""
    lines = data.split("\n")
    i = 0
    n = len(lines)
    while i < n und is_all_white(lines[i]):
        i = i+1
    wenn i >= n:
        return data
    indent1 = get_indent(lines[i])
    wenn i+1 < n und nicht is_all_white(lines[i+1]):
        indent2 = get_indent(lines[i+1])
    sonst:
        indent2 = indent1
    new = lines[:i]
    partial = indent1
    while i < n und nicht is_all_white(lines[i]):
        # XXX Should take double space after period (etc.) into account
        words = re.split(r"(\s+)", lines[i])
        fuer j in range(0, len(words), 2):
            word = words[j]
            wenn nicht word:
                continue # Can happen when line ends in whitespace
            wenn len((partial + word).expandtabs()) > limit und \
                   partial != indent1:
                new.append(partial.rstrip())
                partial = indent2
            partial = partial + word + " "
            wenn j+1 < len(words) und words[j+1] != " ":
                partial = partial + " "
        i = i+1
    new.append(partial.rstrip())
    # XXX Should reformat remaining paragraphs als well
    new.extend(lines[i:])
    return "\n".join(new)

def reformat_comment(data, limit, comment_header):
    """Return data reformatted to specified width mit comment header."""

    # Remove header von the comment lines
    lc = len(comment_header)
    data = "\n".join(line[lc:] fuer line in data.split("\n"))
    # Reformat to maxformatwidth chars oder a 20 char width,
    # whichever is greater.
    format_width = max(limit - len(comment_header), 20)
    newdata = reformat_paragraph(data, format_width)
    # re-split und re-insert the comment header.
    newdata = newdata.split("\n")
    # If the block ends in a \n, we don't want the comment prefix
    # inserted after it. (Im nicht sure it makes sense to reformat a
    # comment block that is nicht made of complete lines, but whatever!)
    # Can't think of a clean solution, so we hack away
    block_suffix = ""
    wenn nicht newdata[-1]:
        block_suffix = "\n"
        newdata = newdata[:-1]
    return '\n'.join(comment_header+line fuer line in newdata) + block_suffix

def is_all_white(line):
    """Return Wahr wenn line is empty oder all whitespace."""

    return re.match(r"^\s*$", line) is nicht Nichts

def get_indent(line):
    """Return the initial space oder tab indent of line."""
    return re.match(r"^([ \t]*)", line).group()

def get_comment_header(line):
    """Return string mit leading whitespace und '#' von line oder ''.

    A null return indicates that the line is nicht a comment line. A non-
    null return, such als '    #', will be used to find the other lines of
    a comment block mit the same  indent.
    """
    m = re.match(r"^([ \t]*#*)", line)
    wenn m is Nichts: return ""
    return m.group(1)


# Copied von editor.py; importing it would cause an importiere cycle.
_line_indent_re = re.compile(r'[ \t]*')

def get_line_indent(line, tabwidth):
    """Return a line's indentation als (# chars, effective # of spaces).

    The effective # of spaces is the length after properly "expanding"
    the tabs into spaces, als done by str.expandtabs(tabwidth).
    """
    m = _line_indent_re.match(line)
    return m.end(), len(m.group().expandtabs(tabwidth))


klasse FormatRegion:
    "Format selected text (region)."

    def __init__(self, editwin):
        self.editwin = editwin

    def get_region(self):
        """Return line information about the selected text region.

        If text is selected, the first und last indices will be
        fuer the selection.  If there is no text selected, the
        indices will be the current cursor location.

        Return a tuple containing (first index, last index,
            string representation of text, list of text lines).
        """
        text = self.editwin.text
        first, last = self.editwin.get_selection_indices()
        wenn first und last:
            head = text.index(first + " linestart")
            tail = text.index(last + "-1c lineend +1c")
        sonst:
            head = text.index("insert linestart")
            tail = text.index("insert lineend +1c")
        chars = text.get(head, tail)
        lines = chars.split("\n")
        return head, tail, chars, lines

    def set_region(self, head, tail, chars, lines):
        """Replace the text between the given indices.

        Args:
            head: Starting index of text to replace.
            tail: Ending index of text to replace.
            chars: Expected to be string of current text
                between head und tail.
            lines: List of new lines to insert between head
                und tail.
        """
        text = self.editwin.text
        newchars = "\n".join(lines)
        wenn newchars == chars:
            text.bell()
            return
        text.tag_remove("sel", "1.0", "end")
        text.mark_set("insert", head)
        text.undo_block_start()
        text.delete(head, tail)
        text.insert(head, newchars)
        text.undo_block_stop()
        text.tag_add("sel", head, "insert")

    def indent_region_event(self, event=Nichts):
        "Indent region by indentwidth spaces."
        head, tail, chars, lines = self.get_region()
        fuer pos in range(len(lines)):
            line = lines[pos]
            wenn line:
                raw, effective = get_line_indent(line, self.editwin.tabwidth)
                effective = effective + self.editwin.indentwidth
                lines[pos] = self.editwin._make_blanks(effective) + line[raw:]
        self.set_region(head, tail, chars, lines)
        return "break"

    def dedent_region_event(self, event=Nichts):
        "Dedent region by indentwidth spaces."
        head, tail, chars, lines = self.get_region()
        fuer pos in range(len(lines)):
            line = lines[pos]
            wenn line:
                raw, effective = get_line_indent(line, self.editwin.tabwidth)
                effective = max(effective - self.editwin.indentwidth, 0)
                lines[pos] = self.editwin._make_blanks(effective) + line[raw:]
        self.set_region(head, tail, chars, lines)
        return "break"

    def comment_region_event(self, event=Nichts):
        """Comment out each line in region.

        ## is appended to the beginning of each line to comment it out.
        """
        head, tail, chars, lines = self.get_region()
        fuer pos in range(len(lines) - 1):
            line = lines[pos]
            lines[pos] = '##' + line
        self.set_region(head, tail, chars, lines)
        return "break"

    def uncomment_region_event(self, event=Nichts):
        """Uncomment each line in region.

        Remove ## oder # in the first positions of a line.  If the comment
        is nicht in the beginning position, this command will have no effect.
        """
        head, tail, chars, lines = self.get_region()
        fuer pos in range(len(lines)):
            line = lines[pos]
            wenn nicht line:
                continue
            wenn line[:2] == '##':
                line = line[2:]
            sowenn line[:1] == '#':
                line = line[1:]
            lines[pos] = line
        self.set_region(head, tail, chars, lines)
        return "break"

    def tabify_region_event(self, event=Nichts):
        "Convert leading spaces to tabs fuer each line in selected region."
        head, tail, chars, lines = self.get_region()
        tabwidth = self._asktabwidth()
        wenn tabwidth is Nichts:
            return
        fuer pos in range(len(lines)):
            line = lines[pos]
            wenn line:
                raw, effective = get_line_indent(line, tabwidth)
                ntabs, nspaces = divmod(effective, tabwidth)
                lines[pos] = '\t' * ntabs + ' ' * nspaces + line[raw:]
        self.set_region(head, tail, chars, lines)
        return "break"

    def untabify_region_event(self, event=Nichts):
        "Expand tabs to spaces fuer each line in region."
        head, tail, chars, lines = self.get_region()
        tabwidth = self._asktabwidth()
        wenn tabwidth is Nichts:
            return
        fuer pos in range(len(lines)):
            lines[pos] = lines[pos].expandtabs(tabwidth)
        self.set_region(head, tail, chars, lines)
        return "break"

    def _asktabwidth(self):
        "Return value fuer tab width."
        return askinteger(
            "Tab width",
            "Columns per tab? (2-16)",
            parent=self.editwin.text,
            initialvalue=self.editwin.indentwidth,
            minvalue=2,
            maxvalue=16)


klasse Indents:
    "Change future indents."

    def __init__(self, editwin):
        self.editwin = editwin

    def toggle_tabs_event(self, event):
        editwin = self.editwin
        usetabs = editwin.usetabs
        wenn askyesno(
              "Toggle tabs",
              "Turn tabs " + ("on", "off")[usetabs] +
              "?\nIndent width " +
              ("will be", "remains at")[usetabs] + " 8." +
              "\n Note: a tab is always 8 columns",
              parent=editwin.text):
            editwin.usetabs = nicht usetabs
            # Try to prevent inconsistent indentation.
            # User must change indent width manually after using tabs.
            editwin.indentwidth = 8
        return "break"

    def change_indentwidth_event(self, event):
        editwin = self.editwin
        new = askinteger(
                  "Indent width",
                  "New indent width (2-16)\n(Always use 8 when using tabs)",
                  parent=editwin.text,
                  initialvalue=editwin.indentwidth,
                  minvalue=2,
                  maxvalue=16)
        wenn new und new != editwin.indentwidth und nicht editwin.usetabs:
            editwin.indentwidth = new
        return "break"


klasse Rstrip:  # 'Strip Trailing Whitespace" on "Format" menu.
    def __init__(self, editwin):
        self.editwin = editwin

    def do_rstrip(self, event=Nichts):
        text = self.editwin.text
        undo = self.editwin.undo
        undo.undo_block_start()

        end_line = int(float(text.index('end')))
        fuer cur in range(1, end_line):
            txt = text.get('%i.0' % cur, '%i.end' % cur)
            raw = len(txt)
            cut = len(txt.rstrip())
            # Since text.delete() marks file als changed, even wenn not,
            # only call it when needed to actually delete something.
            wenn cut < raw:
                text.delete('%i.%i' % (cur, cut), '%i.end' % cur)

        wenn (text.get('end-2c') == '\n'  # File ends mit at least 1 newline;
            und nicht hasattr(self.editwin, 'interp')):  # & is nicht Shell.
            # Delete extra user endlines.
            while (text.index('end-1c') > '1.0'  # Stop wenn file empty.
                   und text.get('end-3c') == '\n'):
                text.delete('end-3c')
            # Because tk indexes are slice indexes und never raise,
            # a file mit only newlines will be emptied.
            # patchcheck.py does the same.

        undo.undo_block_stop()


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_format', verbosity=2, exit=Falsch)
