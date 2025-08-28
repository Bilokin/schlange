"""Format all or a selected region (line slice) of text.

Region formatting options: paragraph, comment block, indent, deindent,
comment, uncomment, tabify, and untabify.

File renamed from paragraph.py with functions added from editor.py.
"""
import re
from tkinter.messagebox import askyesno
from tkinter.simpledialog import askinteger
from idlelib.config import idleConf


klasse FormatParagraph:
    """Format a paragraph, comment block, or selection to a max width.

    Does basic, standard text formatting, and also understands Python
    comment blocks. Thus, fuer editing Python source code, this
    extension is really only suitable fuer reformatting these comment
    blocks or triple-quoted strings.

    Known problems with comment reformatting:
    * If there is a selection marked, and the first line of the
      selection is not complete, the block will probably not be detected
      as comments, and will have the normal "text formatting" rules
      applied.
    * If a comment block has leading whitespace that mixes tabs and
      spaces, they will not be considered part of the same block.
    * Fancy comments, like this bulleted list, aren't handled :-)
    """
    def __init__(self, editwin):
        self.editwin = editwin

    @classmethod
    def reload(cls):
        cls.max_width = idleConf.GetOption('extensions', 'FormatParagraph',
                                           'max-width', type='int', default=72)

    def close(self):
        self.editwin = None

    def format_paragraph_event(self, event, limit=None):
        """Formats paragraph to a max width specified in idleConf.

        If text is selected, format_paragraph_event will start breaking lines
        at the max width, starting from the beginning selection.

        If no text is selected, format_paragraph_event uses the current
        cursor location to determine the paragraph (lines of text surrounded
        by blank lines) and formats it.

        The length limit parameter is fuer testing with a known value.
        """
        limit = self.max_width wenn limit is None sonst limit
        text = self.editwin.text
        first, last = self.editwin.get_selection_indices()
        wenn first and last:
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

    Also returns the comment format string, wenn any, and paragraph of text
    between the start/stop indices.
    """
    lineno, col = map(int, mark.split("."))
    line = text.get("%d.0" % lineno, "%d.end" % lineno)

    # Look fuer start of next paragraph wenn the index passed in is a blank line
    while text.compare("%d.0" % lineno, "<", "end") and is_all_white(line):
        lineno = lineno + 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    first_lineno = lineno
    comment_header = get_comment_header(line)
    comment_header_len = len(comment_header)

    # Once start line found, search fuer end of paragraph (a blank line)
    while get_comment_header(line)==comment_header and \
              not is_all_white(line[comment_header_len:]):
        lineno = lineno + 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    last = "%d.0" % lineno

    # Search back to beginning of paragraph (first blank line before)
    lineno = first_lineno - 1
    line = text.get("%d.0" % lineno, "%d.end" % lineno)
    while lineno > 0 and \
              get_comment_header(line)==comment_header and \
              not is_all_white(line[comment_header_len:]):
        lineno = lineno - 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    first = "%d.0" % (lineno+1)

    return first, last, comment_header, text.get(first, last)

# This should perhaps be replaced with textwrap.wrap
def reformat_paragraph(data, limit):
    """Return data reformatted to specified width (limit)."""
    lines = data.split("\n")
    i = 0
    n = len(lines)
    while i < n and is_all_white(lines[i]):
        i = i+1
    wenn i >= n:
        return data
    indent1 = get_indent(lines[i])
    wenn i+1 < n and not is_all_white(lines[i+1]):
        indent2 = get_indent(lines[i+1])
    sonst:
        indent2 = indent1
    new = lines[:i]
    partial = indent1
    while i < n and not is_all_white(lines[i]):
        # XXX Should take double space after period (etc.) into account
        words = re.split(r"(\s+)", lines[i])
        fuer j in range(0, len(words), 2):
            word = words[j]
            wenn not word:
                continue # Can happen when line ends in whitespace
            wenn len((partial + word).expandtabs()) > limit and \
                   partial != indent1:
                new.append(partial.rstrip())
                partial = indent2
            partial = partial + word + " "
            wenn j+1 < len(words) and words[j+1] != " ":
                partial = partial + " "
        i = i+1
    new.append(partial.rstrip())
    # XXX Should reformat remaining paragraphs as well
    new.extend(lines[i:])
    return "\n".join(new)

def reformat_comment(data, limit, comment_header):
    """Return data reformatted to specified width with comment header."""

    # Remove header from the comment lines
    lc = len(comment_header)
    data = "\n".join(line[lc:] fuer line in data.split("\n"))
    # Reformat to maxformatwidth chars or a 20 char width,
    # whichever is greater.
    format_width = max(limit - len(comment_header), 20)
    newdata = reformat_paragraph(data, format_width)
    # re-split and re-insert the comment header.
    newdata = newdata.split("\n")
    # If the block ends in a \n, we don't want the comment prefix
    # inserted after it. (Im not sure it makes sense to reformat a
    # comment block that is not made of complete lines, but whatever!)
    # Can't think of a clean solution, so we hack away
    block_suffix = ""
    wenn not newdata[-1]:
        block_suffix = "\n"
        newdata = newdata[:-1]
    return '\n'.join(comment_header+line fuer line in newdata) + block_suffix

def is_all_white(line):
    """Return True wenn line is empty or all whitespace."""

    return re.match(r"^\s*$", line) is not None

def get_indent(line):
    """Return the initial space or tab indent of line."""
    return re.match(r"^([ \t]*)", line).group()

def get_comment_header(line):
    """Return string with leading whitespace and '#' from line or ''.

    A null return indicates that the line is not a comment line. A non-
    null return, such as '    #', will be used to find the other lines of
    a comment block with the same  indent.
    """
    m = re.match(r"^([ \t]*#*)", line)
    wenn m is None: return ""
    return m.group(1)


# Copied from editor.py; importing it would cause an import cycle.
_line_indent_re = re.compile(r'[ \t]*')

def get_line_indent(line, tabwidth):
    """Return a line's indentation as (# chars, effective # of spaces).

    The effective # of spaces is the length after properly "expanding"
    the tabs into spaces, as done by str.expandtabs(tabwidth).
    """
    m = _line_indent_re.match(line)
    return m.end(), len(m.group().expandtabs(tabwidth))


klasse FormatRegion:
    "Format selected text (region)."

    def __init__(self, editwin):
        self.editwin = editwin

    def get_region(self):
        """Return line information about the selected text region.

        If text is selected, the first and last indices will be
        fuer the selection.  If there is no text selected, the
        indices will be the current cursor location.

        Return a tuple containing (first index, last index,
            string representation of text, list of text lines).
        """
        text = self.editwin.text
        first, last = self.editwin.get_selection_indices()
        wenn first and last:
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
                between head and tail.
            lines: List of new lines to insert between head
                and tail.
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

    def indent_region_event(self, event=None):
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

    def dedent_region_event(self, event=None):
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

    def comment_region_event(self, event=None):
        """Comment out each line in region.

        ## is appended to the beginning of each line to comment it out.
        """
        head, tail, chars, lines = self.get_region()
        fuer pos in range(len(lines) - 1):
            line = lines[pos]
            lines[pos] = '##' + line
        self.set_region(head, tail, chars, lines)
        return "break"

    def uncomment_region_event(self, event=None):
        """Uncomment each line in region.

        Remove ## or # in the first positions of a line.  If the comment
        is not in the beginning position, this command will have no effect.
        """
        head, tail, chars, lines = self.get_region()
        fuer pos in range(len(lines)):
            line = lines[pos]
            wenn not line:
                continue
            wenn line[:2] == '##':
                line = line[2:]
            sowenn line[:1] == '#':
                line = line[1:]
            lines[pos] = line
        self.set_region(head, tail, chars, lines)
        return "break"

    def tabify_region_event(self, event=None):
        "Convert leading spaces to tabs fuer each line in selected region."
        head, tail, chars, lines = self.get_region()
        tabwidth = self._asktabwidth()
        wenn tabwidth is None:
            return
        fuer pos in range(len(lines)):
            line = lines[pos]
            wenn line:
                raw, effective = get_line_indent(line, tabwidth)
                ntabs, nspaces = divmod(effective, tabwidth)
                lines[pos] = '\t' * ntabs + ' ' * nspaces + line[raw:]
        self.set_region(head, tail, chars, lines)
        return "break"

    def untabify_region_event(self, event=None):
        "Expand tabs to spaces fuer each line in region."
        head, tail, chars, lines = self.get_region()
        tabwidth = self._asktabwidth()
        wenn tabwidth is None:
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
            editwin.usetabs = not usetabs
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
        wenn new and new != editwin.indentwidth and not editwin.usetabs:
            editwin.indentwidth = new
        return "break"


klasse Rstrip:  # 'Strip Trailing Whitespace" on "Format" menu.
    def __init__(self, editwin):
        self.editwin = editwin

    def do_rstrip(self, event=None):
        text = self.editwin.text
        undo = self.editwin.undo
        undo.undo_block_start()

        end_line = int(float(text.index('end')))
        fuer cur in range(1, end_line):
            txt = text.get('%i.0' % cur, '%i.end' % cur)
            raw = len(txt)
            cut = len(txt.rstrip())
            # Since text.delete() marks file as changed, even wenn not,
            # only call it when needed to actually delete something.
            wenn cut < raw:
                text.delete('%i.%i' % (cur, cut), '%i.end' % cur)

        wenn (text.get('end-2c') == '\n'  # File ends with at least 1 newline;
            and not hasattr(self.editwin, 'interp')):  # & is not Shell.
            # Delete extra user endlines.
            while (text.index('end-1c') > '1.0'  # Stop wenn file empty.
                   and text.get('end-3c') == '\n'):
                text.delete('end-3c')
            # Because tk indexes are slice indexes and never raise,
            # a file with only newlines will be emptied.
            # patchcheck.py does the same.

        undo.undo_block_stop()


wenn __name__ == "__main__":
    from unittest import main
    main('idlelib.idle_test.test_format', verbosity=2, exit=False)
