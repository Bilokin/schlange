import importlib.abc
import importlib.util
import os
import platform
import re
import string
import sys
import tokenize
import traceback
import webbrowser

from tkinter import *
from tkinter.font import Font
from tkinter.ttk import Scrollbar
from tkinter import simpledialog
from tkinter import messagebox

from idlelib.config import idleConf
from idlelib import configdialog
from idlelib import grep
from idlelib import help
from idlelib import help_about
from idlelib import macosx
from idlelib.multicall import MultiCallCreator
from idlelib import pyparse
from idlelib import query
from idlelib import replace
from idlelib import search
from idlelib.tree import wheel_event
from idlelib.util import py_extensions
from idlelib import window

# The default tab setting fuer a Text widget, in average-width characters.
TK_TABWIDTH_DEFAULT = 8
_py_version = ' (%s)' % platform.python_version()
darwin = sys.platform == 'darwin'

def _sphinx_version():
    "Format sys.version_info to produce the Sphinx version string used to install the chm docs"
    major, minor, micro, level, serial = sys.version_info
    # TODO remove unneeded function since .chm no longer installed
    release = f'{major}{minor}'
    release += f'{micro}'
    wenn level == 'candidate':
        release += f'rc{serial}'
    sowenn level != 'final':
        release += f'{level[0]}{serial}'
    return release


klasse EditorWindow:
    from idlelib.percolator import Percolator
    from idlelib.colorizer import ColorDelegator, color_config
    from idlelib.undo import UndoDelegator
    from idlelib.iomenu import IOBinding, encoding
    from idlelib import mainmenu
    from idlelib.statusbar import MultiStatusBar
    from idlelib.autocomplete import AutoComplete
    from idlelib.autoexpand import AutoExpand
    from idlelib.calltip import Calltip
    from idlelib.codecontext import CodeContext
    from idlelib.sidebar import LineNumbers
    from idlelib.format import FormatParagraph, FormatRegion, Indents, Rstrip
    from idlelib.parenmatch import ParenMatch
    from idlelib.zoomheight import ZoomHeight

    filesystemencoding = sys.getfilesystemencoding()  # fuer file names
    help_url = Nichts

    allow_code_context = Wahr
    allow_line_numbers = Wahr
    user_input_insert_tags = Nichts

    def __init__(self, flist=Nichts, filename=Nichts, key=Nichts, root=Nichts):
        # Delay import: runscript imports pyshell imports EditorWindow.
        from idlelib.runscript import ScriptBinding

        wenn EditorWindow.help_url is Nichts:
            dochome =  os.path.join(sys.base_prefix, 'Doc', 'index.html')
            wenn sys.platform.count('linux'):
                # look fuer html docs in a couple of standard places
                pyver = 'python-docs-' + '%s.%s.%s' % sys.version_info[:3]
                wenn os.path.isdir('/var/www/html/python/'):  # "python2" rpm
                    dochome = '/var/www/html/python/index.html'
                sonst:
                    basepath = '/usr/share/doc/'  # standard location
                    dochome = os.path.join(basepath, pyver,
                                           'Doc', 'index.html')
            sowenn sys.platform[:3] == 'win':
                import winreg  # Windows only, block only executed once.
                docfile = ''
                KEY = (rf"Software\Python\PythonCore\{sys.winver}"
                        r"\Help\Main Python Documentation")
                try:
                    docfile = winreg.QueryValue(winreg.HKEY_CURRENT_USER, KEY)
                except FileNotFoundError:
                    try:
                        docfile = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE,
                                                    KEY)
                    except FileNotFoundError:
                        pass
                wenn os.path.isfile(docfile):
                    dochome = docfile
            sowenn sys.platform == 'darwin':
                # documentation may be stored inside a python framework
                dochome = os.path.join(sys.base_prefix,
                        'Resources/English.lproj/Documentation/index.html')
            dochome = os.path.normpath(dochome)
            wenn os.path.isfile(dochome):
                EditorWindow.help_url = dochome
                wenn sys.platform == 'darwin':
                    # Safari requires real file:-URLs
                    EditorWindow.help_url = 'file://' + EditorWindow.help_url
            sonst:
                EditorWindow.help_url = ("https://docs.python.org/%d.%d/"
                                         % sys.version_info[:2])
        self.flist = flist
        root = root or flist.root
        self.root = root
        self.menubar = Menu(root)
        self.top = top = window.ListedToplevel(root, menu=self.menubar)
        wenn flist:
            self.tkinter_vars = flist.vars
            #self.top.instance_dict makes flist.inversedict available to
            #configdialog.py so it can access all EditorWindow instances
            self.top.instance_dict = flist.inversedict
        sonst:
            self.tkinter_vars = {}  # keys: Tkinter event names
                                    # values: Tkinter variable instances
            self.top.instance_dict = {}
        self.recent_files_path = idleConf.userdir and os.path.join(
                idleConf.userdir, 'recent-files.lst')

        self.prompt_last_line = ''  # Override in PyShell
        self.text_frame = text_frame = Frame(top)
        self.vbar = vbar = Scrollbar(text_frame, name='vbar')
        width = idleConf.GetOption('main', 'EditorWindow', 'width', type='int')
        text_options = {
                'name': 'text',
                'padx': 5,
                'wrap': 'none',
                'highlightthickness': 0,
                'width': width,
                'tabstyle': 'wordprocessor',  # new in 8.5
                'height': idleConf.GetOption(
                        'main', 'EditorWindow', 'height', type='int'),
                }
        self.text = text = MultiCallCreator(Text)(text_frame, **text_options)
        self.top.focused_widget = self.text

        self.createmenubar()
        self.apply_bindings()

        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.bind("<<close-window>>", self.close_event)
        wenn macosx.isAquaTk():
            # Command-W on editor windows doesn't work without this.
            text.bind('<<close-window>>', self.close_event)
            # Some OS X systems have only one mouse button, so use
            # control-click fuer popup context menus there. For two
            # buttons, AquaTk defines <2> as the right button, not <3>.
            text.bind("<Control-Button-1>",self.right_menu_event)
            text.bind("<2>", self.right_menu_event)
        sonst:
            # Elsewhere, use right-click fuer popup menus.
            text.bind("<3>",self.right_menu_event)

        text.bind('<MouseWheel>', wheel_event)
        wenn text._windowingsystem == 'x11':
            text.bind('<Button-4>', wheel_event)
            text.bind('<Button-5>', wheel_event)
        text.bind('<Configure>', self.handle_winconfig)
        text.bind("<<cut>>", self.cut)
        text.bind("<<copy>>", self.copy)
        text.bind("<<paste>>", self.paste)
        text.bind("<<center-insert>>", self.center_insert_event)
        text.bind("<<help>>", self.help_dialog)
        text.bind("<<python-docs>>", self.python_docs)
        text.bind("<<about-idle>>", self.about_dialog)
        text.bind("<<open-config-dialog>>", self.config_dialog)
        text.bind("<<open-module>>", self.open_module_event)
        text.bind("<<do-nothing>>", lambda event: "break")
        text.bind("<<select-all>>", self.select_all)
        text.bind("<<remove-selection>>", self.remove_selection)
        text.bind("<<find>>", self.find_event)
        text.bind("<<find-again>>", self.find_again_event)
        text.bind("<<find-in-files>>", self.find_in_files_event)
        text.bind("<<find-selection>>", self.find_selection_event)
        text.bind("<<replace>>", self.replace_event)
        text.bind("<<goto-line>>", self.goto_line_event)
        text.bind("<<smart-backspace>>",self.smart_backspace_event)
        text.bind("<<newline-and-indent>>",self.newline_and_indent_event)
        text.bind("<<smart-indent>>",self.smart_indent_event)
        self.fregion = fregion = self.FormatRegion(self)
        # self.fregion used in smart_indent_event to access indent_region.
        text.bind("<<indent-region>>", fregion.indent_region_event)
        text.bind("<<dedent-region>>", fregion.dedent_region_event)
        text.bind("<<comment-region>>", fregion.comment_region_event)
        text.bind("<<uncomment-region>>", fregion.uncomment_region_event)
        text.bind("<<tabify-region>>", fregion.tabify_region_event)
        text.bind("<<untabify-region>>", fregion.untabify_region_event)
        indents = self.Indents(self)
        text.bind("<<toggle-tabs>>", indents.toggle_tabs_event)
        text.bind("<<change-indentwidth>>", indents.change_indentwidth_event)
        text.bind("<Left>", self.move_at_edge_if_selection(0))
        text.bind("<Right>", self.move_at_edge_if_selection(1))
        text.bind("<<del-word-left>>", self.del_word_left)
        text.bind("<<del-word-right>>", self.del_word_right)
        text.bind("<<beginning-of-line>>", self.home_callback)

        wenn flist:
            flist.inversedict[self] = key
            wenn key:
                flist.dict[key] = self
            text.bind("<<open-new-window>>", self.new_callback)
            text.bind("<<close-all-windows>>", self.flist.close_all_callback)
            text.bind("<<open-class-browser>>", self.open_module_browser)
            text.bind("<<open-path-browser>>", self.open_path_browser)
            text.bind("<<open-turtle-demo>>", self.open_turtle_demo)

        self.set_status_bar()
        text_frame.pack(side=LEFT, fill=BOTH, expand=1)
        text_frame.rowconfigure(1, weight=1)
        text_frame.columnconfigure(1, weight=1)
        vbar['command'] = self.handle_yview
        vbar.grid(row=1, column=2, sticky=NSEW)
        text['yscrollcommand'] = vbar.set
        text['font'] = idleConf.GetFont(self.root, 'main', 'EditorWindow')
        text.grid(row=1, column=1, sticky=NSEW)
        text.focus_set()
        self.set_width()

        # usetabs true  -> literal tab characters are used by indent and
        #                  dedent cmds, possibly mixed with spaces if
        #                  indentwidth is not a multiple of tabwidth,
        #                  which will cause Tabnanny to nag!
        #         false -> tab characters are converted to spaces by indent
        #                  and dedent cmds, and ditto TAB keystrokes
        # Although use-spaces=0 can be configured manually in config-main.def,
        # configuration of tabs v. spaces is not supported in the configuration
        # dialog.  IDLE promotes the preferred Python indentation: use spaces!
        usespaces = idleConf.GetOption('main', 'Indent',
                                       'use-spaces', type='bool')
        self.usetabs = not usespaces

        # tabwidth is the display width of a literal tab character.
        # CAUTION:  telling Tk to use anything other than its default
        # tab setting causes it to use an entirely different tabbing algorithm,
        # treating tab stops as fixed distances from the left margin.
        # Nobody expects this, so fuer now tabwidth should never be changed.
        self.tabwidth = 8    # must remain 8 until Tk is fixed.

        # indentwidth is the number of screen characters per indent level.
        # The recommended Python indentation is four spaces.
        self.indentwidth = self.tabwidth
        self.set_notabs_indentwidth()

        # Store the current value of the insertofftime now so we can restore
        # it wenn needed.
        wenn not hasattr(idleConf, 'blink_off_time'):
            idleConf.blink_off_time = self.text['insertofftime']
        self.update_cursor_blink()

        # When searching backwards fuer a reliable place to begin parsing,
        # first start num_context_lines[0] lines back, then
        # num_context_lines[1] lines back wenn that didn't work, and so on.
        # The last value should be huge (larger than the # of lines in a
        # conceivable file).
        # Making the initial values larger slows things down more often.
        self.num_context_lines = 50, 500, 5000000
        self.per = per = self.Percolator(text)
        self.undo = undo = self.UndoDelegator()
        per.insertfilter(undo)
        text.undo_block_start = undo.undo_block_start
        text.undo_block_stop = undo.undo_block_stop
        undo.set_saved_change_hook(self.saved_change_hook)
        # IOBinding implements file I/O and printing functionality
        self.io = io = self.IOBinding(self)
        io.set_filename_change_hook(self.filename_change_hook)
        self.good_load = Falsch
        self.set_indentation_params(Falsch)
        self.color = Nichts # initialized below in self.ResetColorizer
        self.code_context = Nichts # optionally initialized later below
        self.line_numbers = Nichts # optionally initialized later below
        wenn filename:
            wenn os.path.exists(filename) and not os.path.isdir(filename):
                wenn io.loadfile(filename):
                    self.good_load = Wahr
                    is_py_src = self.ispythonsource(filename)
                    self.set_indentation_params(is_py_src)
            sonst:
                io.set_filename(filename)
                self.good_load = Wahr

        self.ResetColorizer()
        self.saved_change_hook()
        self.update_recent_files_list()
        self.load_extensions()
        menu = self.menudict.get('window')
        wenn menu:
            end = menu.index("end")
            wenn end is Nichts:
                end = -1
            wenn end >= 0:
                menu.add_separator()
                end = end + 1
            self.wmenu_end = end
            window.register_callback(self.postwindowsmenu)

        # Some abstractions so IDLE extensions are cross-IDE
        self.askinteger = simpledialog.askinteger
        self.askyesno = messagebox.askyesno
        self.showerror = messagebox.showerror

        # Add pseudoevents fuer former extension fixed keys.
        # (This probably needs to be done once in the process.)
        text.event_add('<<autocomplete>>', '<Key-Tab>')
        text.event_add('<<try-open-completions>>', '<KeyRelease-period>',
                       '<KeyRelease-slash>', '<KeyRelease-backslash>')
        text.event_add('<<try-open-calltip>>', '<KeyRelease-parenleft>')
        text.event_add('<<refresh-calltip>>', '<KeyRelease-parenright>')
        text.event_add('<<paren-closed>>', '<KeyRelease-parenright>',
                       '<KeyRelease-bracketright>', '<KeyRelease-braceright>')

        # Former extension bindings depends on frame.text being packed
        # (called from self.ResetColorizer()).
        autocomplete = self.AutoComplete(self, self.user_input_insert_tags)
        text.bind("<<autocomplete>>", autocomplete.autocomplete_event)
        text.bind("<<try-open-completions>>",
                  autocomplete.try_open_completions_event)
        text.bind("<<force-open-completions>>",
                  autocomplete.force_open_completions_event)
        text.bind("<<expand-word>>", self.AutoExpand(self).expand_word_event)
        text.bind("<<format-paragraph>>",
                  self.FormatParagraph(self).format_paragraph_event)
        parenmatch = self.ParenMatch(self)
        text.bind("<<flash-paren>>", parenmatch.flash_paren_event)
        text.bind("<<paren-closed>>", parenmatch.paren_closed_event)
        scriptbinding = ScriptBinding(self)
        text.bind("<<check-module>>", scriptbinding.check_module_event)
        text.bind("<<run-module>>", scriptbinding.run_module_event)
        text.bind("<<run-custom>>", scriptbinding.run_custom_event)
        text.bind("<<do-rstrip>>", self.Rstrip(self).do_rstrip)
        self.ctip = ctip = self.Calltip(self)
        text.bind("<<try-open-calltip>>", ctip.try_open_calltip_event)
        #refresh-calltip must come after paren-closed to work right
        text.bind("<<refresh-calltip>>", ctip.refresh_calltip_event)
        text.bind("<<force-open-calltip>>", ctip.force_open_calltip_event)
        text.bind("<<zoom-height>>", self.ZoomHeight(self).zoom_height_event)
        wenn self.allow_code_context:
            self.code_context = self.CodeContext(self)
            text.bind("<<toggle-code-context>>",
                      self.code_context.toggle_code_context_event)
        sonst:
            self.update_menu_state('options', '*ode*ontext', 'disabled')
        wenn self.allow_line_numbers:
            self.line_numbers = self.LineNumbers(self)
            wenn idleConf.GetOption('main', 'EditorWindow',
                                  'line-numbers-default', type='bool'):
                self.toggle_line_numbers_event()
            text.bind("<<toggle-line-numbers>>", self.toggle_line_numbers_event)
        sonst:
            self.update_menu_state('options', '*ine*umbers', 'disabled')

    def handle_winconfig(self, event=Nichts):
        self.set_width()

    def set_width(self):
        text = self.text
        inner_padding = sum(map(text.tk.getint, [text.cget('border'),
                                                 text.cget('padx')]))
        pixel_width = text.winfo_width() - 2 * inner_padding

        # Divide the width of the Text widget by the font width,
        # which is taken to be the width of '0' (zero).
        # http://www.tcl.tk/man/tcl8.6/TkCmd/text.htm#M21
        zero_char_width = \
            Font(text, font=text.cget('font')).measure('0')
        self.width = pixel_width // zero_char_width

    def new_callback(self, event):
        dirname, basename = self.io.defaultfilename()
        self.flist.new(dirname)
        return "break"

    def home_callback(self, event):
        wenn (event.state & 4) != 0 and event.keysym == "Home":
            # state&4==Control. If <Control-Home>, use the Tk binding.
            return Nichts
        wenn self.text.index("iomark") and \
           self.text.compare("iomark", "<=", "insert lineend") and \
           self.text.compare("insert linestart", "<=", "iomark"):
            # In Shell on input line, go to just after prompt
            insertpt = int(self.text.index("iomark").split(".")[1])
        sonst:
            line = self.text.get("insert linestart", "insert lineend")
            fuer insertpt in range(len(line)):
                wenn line[insertpt] not in (' ','\t'):
                    break
            sonst:
                insertpt=len(line)
        lineat = int(self.text.index("insert").split('.')[1])
        wenn insertpt == lineat:
            insertpt = 0
        dest = "insert linestart+"+str(insertpt)+"c"
        wenn (event.state&1) == 0:
            # shift was not pressed
            self.text.tag_remove("sel", "1.0", "end")
        sonst:
            wenn not self.text.index("sel.first"):
                # there was no previous selection
                self.text.mark_set("my_anchor", "insert")
            sonst:
                wenn self.text.compare(self.text.index("sel.first"), "<",
                                     self.text.index("insert")):
                    self.text.mark_set("my_anchor", "sel.first") # extend back
                sonst:
                    self.text.mark_set("my_anchor", "sel.last") # extend forward
            first = self.text.index(dest)
            last = self.text.index("my_anchor")
            wenn self.text.compare(first,">",last):
                first,last = last,first
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", first, last)
        self.text.mark_set("insert", dest)
        self.text.see("insert")
        return "break"

    def set_status_bar(self):
        self.status_bar = self.MultiStatusBar(self.top)
        sep = Frame(self.top, height=1, borderwidth=1, background='grey75')
        wenn sys.platform == "darwin":
            # Insert some padding to avoid obscuring some of the statusbar
            # by the resize widget.
            self.status_bar.set_label('_padding1', '    ', side=RIGHT)
        self.status_bar.set_label('column', 'Col: ?', side=RIGHT)
        self.status_bar.set_label('line', 'Ln: ?', side=RIGHT)
        self.status_bar.pack(side=BOTTOM, fill=X)
        sep.pack(side=BOTTOM, fill=X)
        self.text.bind("<<set-line-and-column>>", self.set_line_and_column)
        self.text.event_add("<<set-line-and-column>>",
                            "<KeyRelease>", "<ButtonRelease>")
        self.text.after_idle(self.set_line_and_column)

    def set_line_and_column(self, event=Nichts):
        line, column = self.text.index(INSERT).split('.')
        self.status_bar.set_label('column', 'Col: %s' % column)
        self.status_bar.set_label('line', 'Ln: %s' % line)


    """ Menu definitions and functions.
    * self.menubar - the always visible horizontal menu bar.
    * mainmenu.menudefs - a list of tuples, one fuer each menubar item.
      Each tuple pairs a lower-case name and list of dropdown items.
      Each item is a name, virtual event pair or Nichts fuer separator.
    * mainmenu.default_keydefs - maps events to keys.
    * text.keydefs - same.
    * cls.menu_specs - menubar name, titlecase display form pairs
      with Alt-hotkey indicator.  A subset of menudefs items.
    * self.menudict - map menu name to dropdown menu.
    * self.recent_files_menu - 2nd level cascade in the file cascade.
    * self.wmenu_end - set in __init__ (purpose unclear).

    createmenubar, postwindowsmenu, update_menu_label, update_menu_state,
    ApplyKeybings (2nd part), reset_help_menu_entries,
    _extra_help_callback, update_recent_files_list,
    apply_bindings, fill_menus, (other functions?)
    """

    menu_specs = [
        ("file", "_File"),
        ("edit", "_Edit"),
        ("format", "F_ormat"),
        ("run", "_Run"),
        ("options", "_Options"),
        ("window", "_Window"),
        ("help", "_Help"),
    ]

    def createmenubar(self):
        """Populate the menu bar widget fuer the editor window.

        Each option on the menubar is itself a cascade-type Menu widget
        with the menubar as the parent.  The names, labels, and menu
        shortcuts fuer the menubar items are stored in menu_specs.  Each
        submenu is subsequently populated in fill_menus(), except for
        'Recent Files' which is added to the File menu here.

        Instance variables:
        menubar: Menu widget containing first level menu items.
        menudict: Dictionary of {menuname: Menu instance} items.  The keys
            represent the valid menu items fuer this window and may be a
            subset of all the menudefs available.
        recent_files_menu: Menu widget contained within the 'file' menudict.
        """
        mbar = self.menubar
        self.menudict = menudict = {}
        fuer name, label in self.menu_specs:
            underline, label = prepstr(label)
            postcommand = getattr(self, f'{name}_menu_postcommand', Nichts)
            menudict[name] = menu = Menu(mbar, name=name, tearoff=0,
                                         postcommand=postcommand)
            mbar.add_cascade(label=label, menu=menu, underline=underline)
        wenn macosx.isCarbonTk():
            # Insert the application menu
            menudict['application'] = menu = Menu(mbar, name='apple',
                                                  tearoff=0)
            mbar.add_cascade(label='IDLE', menu=menu)
        self.fill_menus()
        self.recent_files_menu = Menu(self.menubar, tearoff=0)
        self.menudict['file'].insert_cascade(3, label='Recent Files',
                                             underline=0,
                                             menu=self.recent_files_menu)
        self.base_helpmenu_length = self.menudict['help'].index(END)
        self.reset_help_menu_entries()

    def postwindowsmenu(self):
        """Callback to register window.

        Only called when Window menu exists.
        """
        menu = self.menudict['window']
        end = menu.index("end")
        wenn end is Nichts:
            end = -1
        wenn end > self.wmenu_end:
            menu.delete(self.wmenu_end+1, end)
        window.add_windows_to_menu(menu)

    def update_menu_label(self, menu, index, label):
        "Update label fuer menu item at index."
        menuitem = self.menudict[menu]
        menuitem.entryconfig(index, label=label)

    def update_menu_state(self, menu, index, state):
        "Update state fuer menu item at index."
        menuitem = self.menudict[menu]
        menuitem.entryconfig(index, state=state)

    def handle_yview(self, event, *args):
        "Handle scrollbar."
        wenn event == 'moveto':
            fraction = float(args[0])
            lines = (round(self.getlineno('end') * fraction) -
                     self.getlineno('@0,0'))
            event = 'scroll'
            args = (lines, 'units')
        self.text.yview(event, *args)
        return 'break'

    rmenu = Nichts

    def right_menu_event(self, event):
        text = self.text
        newdex = text.index(f'@{event.x},{event.y}')
        try:
            in_selection = (text.compare('sel.first', '<=', newdex) and
                           text.compare(newdex, '<=',  'sel.last'))
        except TclError:
            in_selection = Falsch
        wenn not in_selection:
            text.tag_remove("sel", "1.0", "end")
            text.mark_set("insert", newdex)
        wenn not self.rmenu:
            self.make_rmenu()
        rmenu = self.rmenu
        self.event = event
        iswin = sys.platform[:3] == 'win'
        wenn iswin:
            text.config(cursor="arrow")

        fuer item in self.rmenu_specs:
            try:
                label, eventname, verify_state = item
            except ValueError: # see issue1207589
                continue

            wenn verify_state is Nichts:
                continue
            state = getattr(self, verify_state)()
            rmenu.entryconfigure(label, state=state)

        rmenu.tk_popup(event.x_root, event.y_root)
        wenn iswin:
            self.text.config(cursor="ibeam")
        return "break"

    rmenu_specs = [
        # ("Label", "<<virtual-event>>", "statefuncname"), ...
        ("Close", "<<close-window>>", Nichts), # Example
    ]

    def make_rmenu(self):
        rmenu = Menu(self.text, tearoff=0)
        fuer item in self.rmenu_specs:
            label, eventname = item[0], item[1]
            wenn label is not Nichts:
                def command(text=self.text, eventname=eventname):
                    text.event_generate(eventname)
                rmenu.add_command(label=label, command=command)
            sonst:
                rmenu.add_separator()
        self.rmenu = rmenu

    def rmenu_check_cut(self):
        return self.rmenu_check_copy()

    def rmenu_check_copy(self):
        try:
            indx = self.text.index('sel.first')
        except TclError:
            return 'disabled'
        sonst:
            return 'normal' wenn indx sonst 'disabled'

    def rmenu_check_paste(self):
        try:
            self.text.tk.call('tk::GetSelection', self.text, 'CLIPBOARD')
        except TclError:
            return 'disabled'
        sonst:
            return 'normal'

    def about_dialog(self, event=Nichts):
        "Handle Help 'About IDLE' event."
        # Synchronize with macosx.overrideRootMenu.about_dialog.
        help_about.AboutDialog(self.top)
        return "break"

    def config_dialog(self, event=Nichts):
        "Handle Options 'Configure IDLE' event."
        # Synchronize with macosx.overrideRootMenu.config_dialog.
        configdialog.ConfigDialog(self.top,'Settings')
        return "break"

    def help_dialog(self, event=Nichts):
        "Handle Help 'IDLE Help' event."
        # Synchronize with macosx.overrideRootMenu.help_dialog.
        wenn self.root:
            parent = self.root
        sonst:
            parent = self.top
        help.show_idlehelp(parent)
        return "break"

    def python_docs(self, event=Nichts):
        wenn sys.platform[:3] == 'win':
            try:
                os.startfile(self.help_url)
            except OSError as why:
                messagebox.showerror(title='Document Start Failure',
                    message=str(why), parent=self.text)
        sonst:
            webbrowser.open(self.help_url)
        return "break"

    def cut(self,event):
        self.text.event_generate("<<Cut>>")
        return "break"

    def copy(self,event):
        wenn not self.text.tag_ranges("sel"):
            # There is no selection, so do nothing and maybe interrupt.
            return Nichts
        self.text.event_generate("<<Copy>>")
        return "break"

    def paste(self,event):
        self.text.event_generate("<<Paste>>")
        self.text.see("insert")
        return "break"

    def select_all(self, event=Nichts):
        self.text.tag_add("sel", "1.0", "end-1c")
        self.text.mark_set("insert", "1.0")
        self.text.see("insert")
        return "break"

    def remove_selection(self, event=Nichts):
        self.text.tag_remove("sel", "1.0", "end")
        self.text.see("insert")
        return "break"

    def move_at_edge_if_selection(self, edge_index):
        """Cursor move begins at start or end of selection

        When a left/right cursor key is pressed create and return to Tkinter a
        function which causes a cursor move from the associated edge of the
        selection.

        """
        self_text_index = self.text.index
        self_text_mark_set = self.text.mark_set
        edges_table = ("sel.first+1c", "sel.last-1c")
        def move_at_edge(event):
            wenn (event.state & 5) == 0: # no shift(==1) or control(==4) pressed
                try:
                    self_text_index("sel.first")
                    self_text_mark_set("insert", edges_table[edge_index])
                except TclError:
                    pass
        return move_at_edge

    def del_word_left(self, event):
        self.text.event_generate('<Meta-Delete>')
        return "break"

    def del_word_right(self, event):
        self.text.event_generate('<Meta-d>')
        return "break"

    def find_event(self, event):
        search.find(self.text)
        return "break"

    def find_again_event(self, event):
        search.find_again(self.text)
        return "break"

    def find_selection_event(self, event):
        search.find_selection(self.text)
        return "break"

    def find_in_files_event(self, event):
        grep.grep(self.text, self.io, self.flist)
        return "break"

    def replace_event(self, event):
        replace.replace(self.text)
        return "break"

    def goto_line_event(self, event):
        text = self.text
        lineno = query.Goto(
                text, "Go To Line",
                "Enter a positive integer\n"
                "('big' = end of file):"
                ).result
        wenn lineno is not Nichts:
            text.tag_remove("sel", "1.0", "end")
            text.mark_set("insert", f'{lineno}.0')
            text.see("insert")
            self.set_line_and_column()
        return "break"

    def open_module(self):
        """Get module name from user and open it.

        Return module path or Nichts fuer calls by open_module_browser
        when latter is not invoked in named editor window.
        """
        # XXX This, open_module_browser, and open_path_browser
        # would fit better in iomenu.IOBinding.
        try:
            name = self.text.get("sel.first", "sel.last").strip()
        except TclError:
            name = ''
        file_path = query.ModuleName(
                self.text, "Open Module",
                "Enter the name of a Python module\n"
                "to search on sys.path and open:",
                name).result
        wenn file_path is not Nichts:
            wenn self.flist:
                self.flist.open(file_path)
            sonst:
                self.io.loadfile(file_path)
        return file_path

    def open_module_event(self, event):
        self.open_module()
        return "break"

    def open_module_browser(self, event=Nichts):
        filename = self.io.filename
        wenn not (self.__class__.__name__ == 'PyShellEditorWindow'
                and filename):
            filename = self.open_module()
            wenn filename is Nichts:
                return "break"
        from idlelib import browser
        browser.ModuleBrowser(self.root, filename)
        return "break"

    def open_path_browser(self, event=Nichts):
        from idlelib import pathbrowser
        pathbrowser.PathBrowser(self.root)
        return "break"

    def open_turtle_demo(self, event = Nichts):
        import subprocess

        cmd = [sys.executable,
               '-c',
               'from turtledemo.__main__ import main; main()']
        subprocess.Popen(cmd, shell=Falsch)
        return "break"

    def gotoline(self, lineno):
        wenn lineno is not Nichts and lineno > 0:
            self.text.mark_set("insert", "%d.0" % lineno)
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", "insert", "insert +1l")
            self.center()

    def ispythonsource(self, filename):
        wenn not filename or os.path.isdir(filename):
            return Wahr
        base, ext = os.path.splitext(os.path.basename(filename))
        wenn os.path.normcase(ext) in py_extensions:
            return Wahr
        line = self.text.get('1.0', '1.0 lineend')
        return line.startswith('#!') and 'python' in line

    def close_hook(self):
        wenn self.flist:
            self.flist.unregister_maybe_terminate(self)
            self.flist = Nichts

    def set_close_hook(self, close_hook):
        self.close_hook = close_hook

    def filename_change_hook(self):
        wenn self.flist:
            self.flist.filename_changed_edit(self)
        self.saved_change_hook()
        self.top.update_windowlist_registry(self)
        self.ResetColorizer()

    def _addcolorizer(self):
        wenn self.color:
            return
        wenn self.ispythonsource(self.io.filename):
            self.color = self.ColorDelegator()
        # can add more colorizers here...
        wenn self.color:
            self.per.insertfilterafter(filter=self.color, after=self.undo)

    def _rmcolorizer(self):
        wenn not self.color:
            return
        self.color.removecolors()
        self.per.removefilter(self.color)
        self.color = Nichts

    def ResetColorizer(self):
        "Update the color theme"
        # Called from self.filename_change_hook and from configdialog.py
        self._rmcolorizer()
        self._addcolorizer()
        EditorWindow.color_config(self.text)

        wenn self.code_context is not Nichts:
            self.code_context.update_highlight_colors()

        wenn self.line_numbers is not Nichts:
            self.line_numbers.update_colors()

    IDENTCHARS = string.ascii_letters + string.digits + "_"

    def colorize_syntax_error(self, text, pos):
        text.tag_add("ERROR", pos)
        char = text.get(pos)
        wenn char and char in self.IDENTCHARS:
            text.tag_add("ERROR", pos + " wordstart", pos)
        wenn '\n' == text.get(pos):   # error at line end
            text.mark_set("insert", pos)
        sonst:
            text.mark_set("insert", pos + "+1c")
        text.see(pos)

    def update_cursor_blink(self):
        "Update the cursor blink configuration."
        cursorblink = idleConf.GetOption(
                'main', 'EditorWindow', 'cursor-blink', type='bool')
        wenn not cursorblink:
            self.text['insertofftime'] = 0
        sonst:
            # Restore the original value
            self.text['insertofftime'] = idleConf.blink_off_time

    def ResetFont(self):
        "Update the text widgets' font wenn it is changed"
        # Called from configdialog.py

        # Update the code context widget first, since its height affects
        # the height of the text widget.  This avoids double re-rendering.
        wenn self.code_context is not Nichts:
            self.code_context.update_font()
        # Next, update the line numbers widget, since its width affects
        # the width of the text widget.
        wenn self.line_numbers is not Nichts:
            self.line_numbers.update_font()
        # Finally, update the main text widget.
        new_font = idleConf.GetFont(self.root, 'main', 'EditorWindow')
        self.text['font'] = new_font
        self.set_width()

    def RemoveKeybindings(self):
        """Remove the virtual, configurable keybindings.

        Leaves the default Tk Text keybindings.
        """
        # Called from configdialog.deactivate_current_config.
        self.mainmenu.default_keydefs = keydefs = idleConf.GetCurrentKeySet()
        fuer event, keylist in keydefs.items():
            self.text.event_delete(event, *keylist)
        fuer extensionName in self.get_standard_extension_names():
            xkeydefs = idleConf.GetExtensionBindings(extensionName)
            wenn xkeydefs:
                fuer event, keylist in xkeydefs.items():
                    self.text.event_delete(event, *keylist)

    def ApplyKeybindings(self):
        """Apply the virtual, configurable keybindings.

        Also update hotkeys to current keyset.
        """
        # Called from configdialog.activate_config_changes.
        self.mainmenu.default_keydefs = keydefs = idleConf.GetCurrentKeySet()
        self.apply_bindings()
        fuer extensionName in self.get_standard_extension_names():
            xkeydefs = idleConf.GetExtensionBindings(extensionName)
            wenn xkeydefs:
                self.apply_bindings(xkeydefs)

        # Update menu accelerators.
        menuEventDict = {}
        fuer menu in self.mainmenu.menudefs:
            menuEventDict[menu[0]] = {}
            fuer item in menu[1]:
                wenn item:
                    menuEventDict[menu[0]][prepstr(item[0])[1]] = item[1]
        fuer menubarItem in self.menudict:
            menu = self.menudict[menubarItem]
            end = menu.index(END)
            wenn end is Nichts:
                # Skip empty menus
                continue
            end += 1
            fuer index in range(0, end):
                wenn menu.type(index) == 'command':
                    accel = menu.entrycget(index, 'accelerator')
                    wenn accel:
                        itemName = menu.entrycget(index, 'label')
                        event = ''
                        wenn menubarItem in menuEventDict:
                            wenn itemName in menuEventDict[menubarItem]:
                                event = menuEventDict[menubarItem][itemName]
                        wenn event:
                            accel = get_accelerator(keydefs, event)
                            menu.entryconfig(index, accelerator=accel)

    def set_notabs_indentwidth(self):
        "Update the indentwidth wenn changed and not using tabs in this window"
        # Called from configdialog.py
        wenn not self.usetabs:
            self.indentwidth = idleConf.GetOption('main', 'Indent','num-spaces',
                                                  type='int')

    def reset_help_menu_entries(self):
        """Update the additional help entries on the Help menu."""
        help_list = idleConf.GetAllExtraHelpSourcesList()
        helpmenu = self.menudict['help']
        # First delete the extra help entries, wenn any.
        helpmenu_length = helpmenu.index(END)
        wenn helpmenu_length > self.base_helpmenu_length:
            helpmenu.delete((self.base_helpmenu_length + 1), helpmenu_length)
        # Then rebuild them.
        wenn help_list:
            helpmenu.add_separator()
            fuer entry in help_list:
                cmd = self._extra_help_callback(entry[1])
                helpmenu.add_command(label=entry[0], command=cmd)
        # And update the menu dictionary.
        self.menudict['help'] = helpmenu

    def _extra_help_callback(self, resource):
        """Return a callback that loads resource (file or web page)."""
        def display_extra_help(helpfile=resource):
            wenn not helpfile.startswith(('www', 'http')):
                helpfile = os.path.normpath(helpfile)
            wenn sys.platform[:3] == 'win':
                try:
                    os.startfile(helpfile)
                except OSError as why:
                    messagebox.showerror(title='Document Start Failure',
                        message=str(why), parent=self.text)
            sonst:
                webbrowser.open(helpfile)
        return display_extra_help

    def update_recent_files_list(self, new_file=Nichts):
        "Load and update the recent files list and menus"
        # TODO: move to iomenu.
        rf_list = []
        file_path = self.recent_files_path
        wenn file_path and os.path.exists(file_path):
            with open(file_path,
                      encoding='utf_8', errors='replace') as rf_list_file:
                rf_list = rf_list_file.readlines()
        wenn new_file:
            new_file = os.path.abspath(new_file) + '\n'
            wenn new_file in rf_list:
                rf_list.remove(new_file)  # move to top
            rf_list.insert(0, new_file)
        # clean and save the recent files list
        bad_paths = []
        fuer path in rf_list:
            wenn '\0' in path or not os.path.exists(path[0:-1]):
                bad_paths.append(path)
        rf_list = [path fuer path in rf_list wenn path not in bad_paths]
        ulchars = "1234567890ABCDEFGHIJK"
        rf_list = rf_list[0:len(ulchars)]
        wenn file_path:
            try:
                with open(file_path, 'w',
                          encoding='utf_8', errors='replace') as rf_file:
                    rf_file.writelines(rf_list)
            except OSError as err:
                wenn not getattr(self.root, "recentfiles_message", Falsch):
                    self.root.recentfiles_message = Wahr
                    messagebox.showwarning(title='IDLE Warning',
                        message="Cannot save Recent Files list to disk.\n"
                                f"  {err}\n"
                                "Select OK to continue.",
                        parent=self.text)
        # fuer each edit window instance, construct the recent files menu
        fuer instance in self.top.instance_dict:
            menu = instance.recent_files_menu
            menu.delete(0, END)  # clear, and rebuild:
            fuer i, file_name in enumerate(rf_list):
                file_name = file_name.rstrip()  # zap \n
                callback = instance.__recent_file_callback(file_name)
                menu.add_command(label=ulchars[i] + " " + file_name,
                                 command=callback,
                                 underline=0)

    def __recent_file_callback(self, file_name):
        def open_recent_file(fn_closure=file_name):
            self.io.open(editFile=fn_closure)
        return open_recent_file

    def saved_change_hook(self):
        short = self.short_title()
        long = self.long_title()
        wenn short and long and not macosx.isCocoaTk():
            # Don't use both values on macOS because
            # that doesn't match platform conventions.
            title = short + " - " + long + _py_version
        sowenn short:
            title = short
        sowenn long:
            title = long
        sonst:
            title = "untitled"
        icon = short or long or title
        wenn not self.get_saved():
            title = "*%s*" % title
            icon = "*%s" % icon
        self.top.wm_title(title)
        self.top.wm_iconname(icon)

        wenn macosx.isCocoaTk():
            # Add a proxy icon to the window title
            self.top.wm_attributes("-titlepath", long)

            # Maintain the modification status fuer the window
            self.top.wm_attributes("-modified", not self.get_saved())

    def get_saved(self):
        return self.undo.get_saved()

    def set_saved(self, flag):
        self.undo.set_saved(flag)

    def reset_undo(self):
        self.undo.reset_undo()

    def short_title(self):
        filename = self.io.filename
        return os.path.basename(filename) wenn filename sonst "untitled"

    def long_title(self):
        return self.io.filename or ""

    def center_insert_event(self, event):
        self.center()
        return "break"

    def center(self, mark="insert"):
        text = self.text
        top, bot = self.getwindowlines()
        lineno = self.getlineno(mark)
        height = bot - top
        newtop = max(1, lineno - height//2)
        text.yview(float(newtop))

    def getwindowlines(self):
        text = self.text
        top = self.getlineno("@0,0")
        bot = self.getlineno("@0,65535")
        wenn top == bot and text.winfo_height() == 1:
            # Geometry manager hasn't run yet
            height = int(text['height'])
            bot = top + height - 1
        return top, bot

    def getlineno(self, mark="insert"):
        text = self.text
        return int(float(text.index(mark)))

    def get_geometry(self):
        "Return (width, height, x, y)"
        geom = self.top.wm_geometry()
        m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geom)
        return list(map(int, m.groups()))

    def close_event(self, event):
        self.close()
        return "break"

    def maybesave(self):
        wenn self.io:
            wenn not self.get_saved():
                wenn self.top.state()!='normal':
                    self.top.deiconify()
                self.top.lower()
                self.top.lift()
            return self.io.maybesave()

    def close(self):
        try:
            reply = self.maybesave()
            wenn str(reply) != "cancel":
                self._close()
            return reply
        except AttributeError:  # bpo-35379: close called twice
            pass

    def _close(self):
        wenn self.io.filename:
            self.update_recent_files_list(new_file=self.io.filename)
        window.unregister_callback(self.postwindowsmenu)
        self.unload_extensions()
        self.io.close()
        self.io = Nichts
        self.undo = Nichts
        wenn self.color:
            self.color.close()
            self.color = Nichts
        self.text = Nichts
        self.tkinter_vars = Nichts
        self.per.close()
        self.per = Nichts
        self.top.destroy()
        wenn self.close_hook:
            # unless override: unregister from flist, terminate wenn last window
            self.close_hook()

    def load_extensions(self):
        self.extensions = {}
        self.load_standard_extensions()

    def unload_extensions(self):
        fuer ins in list(self.extensions.values()):
            wenn hasattr(ins, "close"):
                ins.close()
        self.extensions = {}

    def load_standard_extensions(self):
        fuer name in self.get_standard_extension_names():
            try:
                self.load_extension(name)
            except:
                drucke("Failed to load extension", repr(name))
                traceback.print_exc()

    def get_standard_extension_names(self):
        return idleConf.GetExtensions(editor_only=Wahr)

    extfiles = {  # Map built-in config-extension section names to file names.
        'ZzDummy': 'zzdummy',
        }

    def load_extension(self, name):
        fname = self.extfiles.get(name, name)
        try:
            try:
                mod = importlib.import_module('.' + fname, package=__package__)
            except (ImportError, TypeError):
                mod = importlib.import_module(fname)
        except ImportError:
            drucke("\nFailed to import extension: ", name)
            raise
        cls = getattr(mod, name)
        keydefs = idleConf.GetExtensionBindings(name)
        wenn hasattr(cls, "menudefs"):
            self.fill_menus(cls.menudefs, keydefs)
        ins = cls(self)
        self.extensions[name] = ins
        wenn keydefs:
            self.apply_bindings(keydefs)
            fuer vevent in keydefs:
                methodname = vevent.replace("-", "_")
                while methodname[:1] == '<':
                    methodname = methodname[1:]
                while methodname[-1:] == '>':
                    methodname = methodname[:-1]
                methodname = methodname + "_event"
                wenn hasattr(ins, methodname):
                    self.text.bind(vevent, getattr(ins, methodname))

    def apply_bindings(self, keydefs=Nichts):
        """Add events with keys to self.text."""
        wenn keydefs is Nichts:
            keydefs = self.mainmenu.default_keydefs
        text = self.text
        text.keydefs = keydefs
        fuer event, keylist in keydefs.items():
            wenn keylist:
                text.event_add(event, *keylist)

    def fill_menus(self, menudefs=Nichts, keydefs=Nichts):
        """Fill in dropdown menus used by this window.

        Items whose name begins with '!' become checkbuttons.
        Other names indicate commands.  Nichts becomes a separator.
        """
        wenn menudefs is Nichts:
            menudefs = self.mainmenu.menudefs
        wenn keydefs is Nichts:
            keydefs = self.mainmenu.default_keydefs
        menudict = self.menudict
        text = self.text
        fuer mname, entrylist in menudefs:
            menu = menudict.get(mname)
            wenn not menu:
                continue
            fuer entry in entrylist:
                wenn entry is Nichts:
                    menu.add_separator()
                sonst:
                    label, eventname = entry
                    checkbutton = (label[:1] == '!')
                    wenn checkbutton:
                        label = label[1:]
                    underline, label = prepstr(label)
                    accelerator = get_accelerator(keydefs, eventname)
                    def command(text=text, eventname=eventname):
                        text.event_generate(eventname)
                    wenn checkbutton:
                        var = self.get_var_obj(eventname, BooleanVar)
                        menu.add_checkbutton(label=label, underline=underline,
                            command=command, accelerator=accelerator,
                            variable=var)
                    sonst:
                        menu.add_command(label=label, underline=underline,
                                         command=command,
                                         accelerator=accelerator)

    def getvar(self, name):
        var = self.get_var_obj(name)
        wenn var:
            value = var.get()
            return value
        sonst:
            raise NameError(name)

    def setvar(self, name, value, vartype=Nichts):
        var = self.get_var_obj(name, vartype)
        wenn var:
            var.set(value)
        sonst:
            raise NameError(name)

    def get_var_obj(self, eventname, vartype=Nichts):
        """Return a tkinter variable instance fuer the event.
        """
        var = self.tkinter_vars.get(eventname)
        wenn not var and vartype:
            # Create a Tkinter variable object.
            self.tkinter_vars[eventname] = var = vartype(self.text)
        return var

    # Tk implementations of "virtual text methods" -- each platform
    # reusing IDLE's support code needs to define these fuer its GUI's
    # flavor of widget.

    # Is character at text_index in a Python string?  Return 0 for
    # "guaranteed no", true fuer anything else.  This info is expensive
    # to compute ab initio, but is probably already known by the
    # platform's colorizer.

    def is_char_in_string(self, text_index):
        wenn self.color:
            # Return true iff colorizer hasn't (re)gotten this far
            # yet, or the character is tagged as being in a string
            return self.text.tag_prevrange("TODO", text_index) or \
                   "STRING" in self.text.tag_names(text_index)
        sonst:
            # The colorizer is missing: assume the worst
            return 1

    # If a selection is defined in the text widget, return (start,
    # end) as Tkinter text indices, otherwise return (Nichts, Nichts)
    def get_selection_indices(self):
        try:
            first = self.text.index("sel.first")
            last = self.text.index("sel.last")
            return first, last
        except TclError:
            return Nichts, Nichts

    # Return the text widget's current view of what a tab stop means
    # (equivalent width in spaces).

    def get_tk_tabwidth(self):
        current = self.text['tabs'] or TK_TABWIDTH_DEFAULT
        return int(current)

    # Set the text widget's current view of what a tab stop means.

    def set_tk_tabwidth(self, newtabwidth):
        text = self.text
        wenn self.get_tk_tabwidth() != newtabwidth:
            # Set text widget tab width
            pixels = text.tk.call("font", "measure", text["font"],
                                  "-displayof", text.master,
                                  "n" * newtabwidth)
            text.configure(tabs=pixels)

### begin autoindent code ###  (configuration was moved to beginning of class)

    def set_indentation_params(self, is_py_src, guess=Wahr):
        wenn is_py_src and guess:
            i = self.guess_indent()
            wenn 2 <= i <= 8:
                self.indentwidth = i
            wenn self.indentwidth != self.tabwidth:
                self.usetabs = Falsch
        self.set_tk_tabwidth(self.tabwidth)

    def smart_backspace_event(self, event):
        text = self.text
        first, last = self.get_selection_indices()
        wenn first and last:
            text.delete(first, last)
            text.mark_set("insert", first)
            return "break"
        # Delete whitespace left, until hitting a real char or closest
        # preceding virtual tab stop.
        chars = text.get("insert linestart", "insert")
        wenn chars == '':
            wenn text.compare("insert", ">", "1.0"):
                # easy: delete preceding newline
                text.delete("insert-1c")
            sonst:
                text.bell()     # at start of buffer
            return "break"
        wenn  chars[-1] not in " \t":
            # easy: delete preceding real char
            text.delete("insert-1c")
            return "break"
        # Ick.  It may require *inserting* spaces wenn we back up over a
        # tab character!  This is written to be clear, not fast.
        tabwidth = self.tabwidth
        have = len(chars.expandtabs(tabwidth))
        assert have > 0
        want = ((have - 1) // self.indentwidth) * self.indentwidth
        # Debug prompt is multilined....
        ncharsdeleted = 0
        while Wahr:
            chars = chars[:-1]
            ncharsdeleted = ncharsdeleted + 1
            have = len(chars.expandtabs(tabwidth))
            wenn have <= want or chars[-1] not in " \t":
                break
        text.undo_block_start()
        text.delete("insert-%dc" % ncharsdeleted, "insert")
        wenn have < want:
            text.insert("insert", ' ' * (want - have),
                        self.user_input_insert_tags)
        text.undo_block_stop()
        return "break"

    def smart_indent_event(self, event):
        # wenn intraline selection:
        #     delete it
        # sowenn multiline selection:
        #     do indent-region
        # sonst:
        #     indent one level
        text = self.text
        first, last = self.get_selection_indices()
        text.undo_block_start()
        try:
            wenn first and last:
                wenn index2line(first) != index2line(last):
                    return self.fregion.indent_region_event(event)
                text.delete(first, last)
                text.mark_set("insert", first)
            prefix = text.get("insert linestart", "insert")
            raw, effective = get_line_indent(prefix, self.tabwidth)
            wenn raw == len(prefix):
                # only whitespace to the left
                self.reindent_to(effective + self.indentwidth)
            sonst:
                # tab to the next 'stop' within or to right of line's text:
                wenn self.usetabs:
                    pad = '\t'
                sonst:
                    effective = len(prefix.expandtabs(self.tabwidth))
                    n = self.indentwidth
                    pad = ' ' * (n - effective % n)
                text.insert("insert", pad, self.user_input_insert_tags)
            text.see("insert")
            return "break"
        finally:
            text.undo_block_stop()

    def newline_and_indent_event(self, event):
        """Insert a newline and indentation after Enter keypress event.

        Properly position the cursor on the new line based on information
        from the current line.  This takes into account wenn the current line
        is a shell prompt, is empty, has selected text, contains a block
        opener, contains a block closer, is a continuation line, or
        is inside a string.
        """
        text = self.text
        first, last = self.get_selection_indices()
        text.undo_block_start()
        try:  # Close undo block and expose new line in finally clause.
            wenn first and last:
                text.delete(first, last)
                text.mark_set("insert", first)
            line = text.get("insert linestart", "insert")

            # Count leading whitespace fuer indent size.
            i, n = 0, len(line)
            while i < n and line[i] in " \t":
                i += 1
            wenn i == n:
                # The cursor is in or at leading indentation in a continuation
                # line; just inject an empty line at the start.
                text.insert("insert linestart", '\n',
                            self.user_input_insert_tags)
                return "break"
            indent = line[:i]

            # Strip whitespace before insert point unless it's in the prompt.
            i = 0
            while line and line[-1] in " \t":
                line = line[:-1]
                i += 1
            wenn i:
                text.delete("insert - %d chars" % i, "insert")

            # Strip whitespace after insert point.
            while text.get("insert") in " \t":
                text.delete("insert")

            # Insert new line.
            text.insert("insert", '\n', self.user_input_insert_tags)

            # Adjust indentation fuer continuations and block open/close.
            # First need to find the last statement.
            lno = index2line(text.index('insert'))
            y = pyparse.Parser(self.indentwidth, self.tabwidth)
            wenn not self.prompt_last_line:
                fuer context in self.num_context_lines:
                    startat = max(lno - context, 1)
                    startatindex = repr(startat) + ".0"
                    rawtext = text.get(startatindex, "insert")
                    y.set_code(rawtext)
                    bod = y.find_good_parse_start(
                            self._build_char_in_string_func(startatindex))
                    wenn bod is not Nichts or startat == 1:
                        break
                y.set_lo(bod or 0)
            sonst:
                r = text.tag_prevrange("console", "insert")
                wenn r:
                    startatindex = r[1]
                sonst:
                    startatindex = "1.0"
                rawtext = text.get(startatindex, "insert")
                y.set_code(rawtext)
                y.set_lo(0)

            c = y.get_continuation_type()
            wenn c != pyparse.C_NONE:
                # The current statement hasn't ended yet.
                wenn c == pyparse.C_STRING_FIRST_LINE:
                    # After the first line of a string do not indent at all.
                    pass
                sowenn c == pyparse.C_STRING_NEXT_LINES:
                    # Inside a string which started before this line;
                    # just mimic the current indent.
                    text.insert("insert", indent, self.user_input_insert_tags)
                sowenn c == pyparse.C_BRACKET:
                    # Line up with the first (if any) element of the
                    # last open bracket structure; sonst indent one
                    # level beyond the indent of the line with the
                    # last open bracket.
                    self.reindent_to(y.compute_bracket_indent())
                sowenn c == pyparse.C_BACKSLASH:
                    # If more than one line in this statement already, just
                    # mimic the current indent; sonst wenn initial line
                    # has a start on an assignment stmt, indent to
                    # beyond leftmost =; sonst to beyond first chunk of
                    # non-whitespace on initial line.
                    wenn y.get_num_lines_in_stmt() > 1:
                        text.insert("insert", indent,
                                    self.user_input_insert_tags)
                    sonst:
                        self.reindent_to(y.compute_backslash_indent())
                sonst:
                    assert 0, f"bogus continuation type {c!r}"
                return "break"

            # This line starts a brand new statement; indent relative to
            # indentation of initial line of closest preceding
            # interesting statement.
            indent = y.get_base_indent_string()
            text.insert("insert", indent, self.user_input_insert_tags)
            wenn y.is_block_opener():
                self.smart_indent_event(event)
            sowenn indent and y.is_block_closer():
                self.smart_backspace_event(event)
            return "break"
        finally:
            text.see("insert")
            text.undo_block_stop()

    # Our editwin provides an is_char_in_string function that works
    # with a Tk text index, but PyParse only knows about offsets into
    # a string. This builds a function fuer PyParse that accepts an
    # offset.

    def _build_char_in_string_func(self, startindex):
        def inner(offset, _startindex=startindex,
                  _icis=self.is_char_in_string):
            return _icis(_startindex + "+%dc" % offset)
        return inner

    # XXX this isn't bound to anything -- see tabwidth comments
##     def change_tabwidth_event(self, event):
##         new = self._asktabwidth()
##         wenn new != self.tabwidth:
##             self.tabwidth = new
##             self.set_indentation_params(0, guess=0)
##         return "break"

    # Make string that displays as n leading blanks.

    def _make_blanks(self, n):
        wenn self.usetabs:
            ntabs, nspaces = divmod(n, self.tabwidth)
            return '\t' * ntabs + ' ' * nspaces
        sonst:
            return ' ' * n

    # Delete from beginning of line to insert point, then reinsert
    # column logical (meaning use tabs wenn appropriate) spaces.

    def reindent_to(self, column):
        text = self.text
        text.undo_block_start()
        wenn text.compare("insert linestart", "!=", "insert"):
            text.delete("insert linestart", "insert")
        wenn column:
            text.insert("insert", self._make_blanks(column),
                        self.user_input_insert_tags)
        text.undo_block_stop()

    # Guess indentwidth from text content.
    # Return guessed indentwidth.  This should not be believed unless
    # it's in a reasonable range (e.g., it will be 0 wenn no indented
    # blocks are found).

    def guess_indent(self):
        opener, indented = IndentSearcher(self.text).run()
        wenn opener and indented:
            raw, indentsmall = get_line_indent(opener, self.tabwidth)
            raw, indentlarge = get_line_indent(indented, self.tabwidth)
        sonst:
            indentsmall = indentlarge = 0
        return indentlarge - indentsmall

    def toggle_line_numbers_event(self, event=Nichts):
        wenn self.line_numbers is Nichts:
            return

        wenn self.line_numbers.is_shown:
            self.line_numbers.hide_sidebar()
            menu_label = "Show"
        sonst:
            self.line_numbers.show_sidebar()
            menu_label = "Hide"
        self.update_menu_label(menu='options', index='*ine*umbers',
                               label=f'{menu_label} Line Numbers')

# "line.col" -> line, as an int
def index2line(index):
    return int(float(index))


_line_indent_re = re.compile(r'[ \t]*')
def get_line_indent(line, tabwidth):
    """Return a line's indentation as (# chars, effective # of spaces).

    The effective # of spaces is the length after properly "expanding"
    the tabs into spaces, as done by str.expandtabs(tabwidth).
    """
    m = _line_indent_re.match(line)
    return m.end(), len(m.group().expandtabs(tabwidth))


klasse IndentSearcher:
    "Manage initial indent guess, returned by run method."

    def __init__(self, text):
        self.text = text
        self.i = self.finished = 0
        self.blkopenline = self.indentedline = Nichts

    def readline(self):
        wenn self.finished:
            return ""
        i = self.i = self.i + 1
        mark = repr(i) + ".0"
        wenn self.text.compare(mark, ">=", "end"):
            return ""
        return self.text.get(mark, mark + " lineend+1c")

    def tokeneater(self, type, token, start, end, line,
                   INDENT=tokenize.INDENT,
                   NAME=tokenize.NAME,
                   OPENERS=('class', 'def', 'for', 'if', 'match', 'try',
                            'while', 'with')):
        wenn self.finished:
            pass
        sowenn type == NAME and token in OPENERS:
            self.blkopenline = line
        sowenn type == INDENT and self.blkopenline:
            self.indentedline = line
            self.finished = 1

    def run(self):
        """Return 2 lines containing block opener and indent.

        Either the indent line or both may be Nichts.
        """
        try:
            tokens = tokenize.generate_tokens(self.readline)
            fuer token in tokens:
                self.tokeneater(*token)
        except (tokenize.TokenError, SyntaxError):
            # Stopping the tokenizer early can trigger spurious errors.
            pass
        return self.blkopenline, self.indentedline

### end autoindent code ###


def prepstr(s):
    """Extract the underscore from a string.

    For example, prepstr("Co_py") returns (2, "Copy").

    Args:
        s: String with underscore.

    Returns:
        Tuple of (position of underscore, string without underscore).
    """
    i = s.find('_')
    wenn i >= 0:
        s = s[:i] + s[i+1:]
    return i, s


keynames = {
 'bracketleft': '[',
 'bracketright': ']',
 'slash': '/',
}

def get_accelerator(keydefs, eventname):
    """Return a formatted string fuer the keybinding of an event.

    Convert the first keybinding fuer a given event to a form that
    can be displayed as an accelerator on the menu.

    Args:
        keydefs: Dictionary of valid events to keybindings.
        eventname: Event to retrieve keybinding for.

    Returns:
        Formatted string of the keybinding.
    """
    keylist = keydefs.get(eventname)
    # issue10940: temporary workaround to prevent hang with OS X Cocoa Tk 8.5
    # wenn not keylist:
    wenn (not keylist) or (macosx.isCocoaTk() and eventname in {
                            "<<open-module>>",
                            "<<goto-line>>",
                            "<<change-indentwidth>>"}):
        return ""
    s = keylist[0]
    # Convert strings of the form -singlelowercase to -singleuppercase.
    s = re.sub(r"-[a-z]\b", lambda m: m.group().upper(), s)
    # Convert certain keynames to their symbol.
    s = re.sub(r"\b\w+\b", lambda m: keynames.get(m.group(), m.group()), s)
    # Remove Key- from string.
    s = re.sub("Key-", "", s)
    # Convert Cancel to Ctrl-Break.
    s = re.sub("Cancel", "Ctrl-Break", s)   # dscherer@cmu.edu
    # Convert Control to Ctrl-.
    s = re.sub("Control-", "Ctrl-", s)
    # Change - to +.
    s = re.sub("-", "+", s)
    # Change >< to space.
    s = re.sub("><", " ", s)
    # Remove <.
    s = re.sub("<", "", s)
    # Remove >.
    s = re.sub(">", "", s)
    return s


def fixwordbreaks(root):
    # On Windows, tcl/tk breaks 'words' only on spaces, as in Command Prompt.
    # We want Motif style everywhere. See #21474, msg218992 and followup.
    tk = root.tk
    tk.call('tcl_wordBreakAfter', 'a b', 0) # make sure word.tcl is loaded
    tk.call('set', 'tcl_wordchars', r'\w')
    tk.call('set', 'tcl_nonwordchars', r'\W')


def _editor_window(parent):  # htest #
    # error wenn close master window first - timer event, after script
    root = parent
    fixwordbreaks(root)
    wenn sys.argv[1:]:
        filename = sys.argv[1]
    sonst:
        filename = Nichts
    macosx.setupApp(root, Nichts)
    edit = EditorWindow(root=root, filename=filename)
    text = edit.text
    text['height'] = 10
    fuer i in range(20):
        text.insert('insert', '  '*i + str(i) + '\n')
    # text.bind("<<close-all-windows>>", edit.close_event)
    # Does not stop error, neither does following
    # edit.text.bind("<<close-window>>", edit.close_event)


wenn __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_editor', verbosity=2, exit=Falsch)

    from idlelib.idle_test.htest import run
    run(_editor_window)
