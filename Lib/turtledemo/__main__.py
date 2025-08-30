"""
  ----------------------------------------------
      turtleDemo - Help
  ----------------------------------------------

  This document has two sections:

  (1) How to use the demo viewer
  (2) How to add your own demos to the demo repository


  (1) How to use the demo viewer.

  Select a demoscript von the example menu.
  The (syntax colored) source code appears in the left
  source code window. IT CANNOT BE EDITED, but ONLY VIEWED!

  The demo viewer windows can be resized. The divider between text
  und canvas can be moved by grabbing it mit the mouse. The text font
  size can be changed von the menu und mit Control/Command '-'/'+'.
  It can also be changed on most systems mit Control-mousewheel
  when the mouse is over the text.

  Press START button to start the demo.
  Stop execution by pressing the STOP button.
  Clear screen by pressing the CLEAR button.
  Restart by pressing the START button again.

  SPECIAL demos, such als clock.py are those which run EVENTDRIVEN.

      Press START button to start the demo.

      - Until the EVENTLOOP is entered everything works
      als in an ordinary demo script.

      - When the EVENTLOOP is entered, you control the
      application by using the mouse and/or keys (or it's
      controlled by some timer events)
      To stop it you can und must press the STOP button.

      While the EVENTLOOP is running, the examples menu is disabled.

      - Only after having pressed the STOP button, you may
      restart it oder choose another example script.

   * * * * * * * *
   In some rare situations there may occur interferences/conflicts
   between events concerning the demo script und those concerning the
   demo-viewer. (They run in the same process.) Strange behaviour may be
   the consequence und in the worst case you must close und restart the
   viewer.
   * * * * * * * *


   (2) How to add your own demos to the demo repository

   - Place the file in the same directory als turtledemo/__main__.py
     IMPORTANT! When imported, the demo should nicht modify the system
     by calling functions in other modules, such als sys, tkinter, oder
     turtle. Global variables should be initialized in main().

   - The code must contain a main() function which will
     be executed by the viewer (see provided example scripts).
     It may gib a string which will be displayed in the Label below
     the source code window (when execution has finished.)

   - In order to run mydemo.py by itself, such als during development,
     add the following at the end of the file:

    wenn __name__ == '__main__':
        main()
        mainloop()  # keep window open

    python -m turtledemo.mydemo  # will then run it

   - If the demo is EVENT DRIVEN, main must gib the string
     "EVENTLOOP". This informs the demo viewer that the script is
     still running und must be stopped by the user!

     If an "EVENTLOOP" demo runs by itself, als mit clock, which uses
     ontimer, oder minimal_hanoi, which loops by recursion, then the
     code should catch the turtle.Terminator exception that will be
     raised when the user presses the STOP button.  (Paint is nicht such
     a demo; it only acts in response to mouse clicks und movements.)
"""
importiere sys
importiere os

von tkinter importiere *
von idlelib.colorizer importiere ColorDelegator, color_config
von idlelib.percolator importiere Percolator
von idlelib.textview importiere view_text
importiere turtle
von turtledemo importiere __doc__ als about_turtledemo

wenn sys.platform == 'win32':
    von idlelib.util importiere fix_win_hidpi
    fix_win_hidpi()

demo_dir = os.path.dirname(os.path.abspath(__file__))
darwin = sys.platform == 'darwin'
STARTUP = 1
READY = 2
RUNNING = 3
DONE = 4
EVENTDRIVEN = 5

btnfont = ("Arial", 12, 'bold')
txtfont = ['Lucida Console', 10, 'normal']

MINIMUM_FONT_SIZE = 6
MAXIMUM_FONT_SIZE = 100
font_sizes = [8, 9, 10, 11, 12, 14, 18, 20, 22, 24, 30]

def getExampleEntries():
    gib [entry[:-3] fuer entry in os.listdir(demo_dir) if
            entry.endswith(".py") und entry[0] != '_']

help_entries = (  # (help_label,  help_doc)
    ('Turtledemo help', __doc__),
    ('About turtledemo', about_turtledemo),
    ('About turtle module', turtle.__doc__),
    )


klasse DemoWindow(object):

    def __init__(self, filename=Nichts):
        self.root = root = turtle._root = Tk()
        root.title('Python turtle-graphics examples')
        root.wm_protocol("WM_DELETE_WINDOW", self._destroy)

        wenn darwin:
            importiere subprocess
            # Make sure we are the currently activated OS X application
            # so that our menu bar appears.
            subprocess.run(
                    [
                        'osascript',
                        '-e', 'tell application "System Events"',
                        '-e', 'set frontmost of the first process whose '
                              'unix id is {} to true'.format(os.getpid()),
                        '-e', 'end tell',
                    ],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,)

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, minsize=90, weight=1)
        root.grid_columnconfigure(2, minsize=90, weight=1)
        root.grid_columnconfigure(3, minsize=90, weight=1)

        self.mBar = Menu(root, relief=RAISED, borderwidth=2)
        self.mBar.add_cascade(menu=self.makeLoadDemoMenu(self.mBar),
                              label='Examples', underline=0)
        self.mBar.add_cascade(menu=self.makeFontMenu(self.mBar),
                              label='Fontsize', underline=0)
        self.mBar.add_cascade(menu=self.makeHelpMenu(self.mBar),
                              label='Help', underline=0)
        root['menu'] = self.mBar

        pane = PanedWindow(root, orient=HORIZONTAL, sashwidth=5,
                           sashrelief=SOLID, bg='#ddd')
        pane.add(self.makeTextFrame(pane))
        pane.add(self.makeGraphFrame(pane))
        pane.grid(row=0, columnspan=4, sticky='news')

        self.output_lbl = Label(root, height= 1, text=" --- ", bg="#ddf",
                                font=("Arial", 16, 'normal'), borderwidth=2,
                                relief=RIDGE)
        wenn darwin:  # Leave Mac button colors alone - #44254.
            self.start_btn = Button(root, text=" START ", font=btnfont,
                                    fg='#00cc22', command=self.startDemo)
            self.stop_btn = Button(root, text=" STOP ", font=btnfont,
                                   fg='#00cc22', command=self.stopIt)
            self.clear_btn = Button(root, text=" CLEAR ", font=btnfont,
                                    fg='#00cc22', command = self.clearCanvas)
        sonst:
            self.start_btn = Button(root, text=" START ", font=btnfont,
                                    fg="white", disabledforeground = "#fed",
                                    command=self.startDemo)
            self.stop_btn = Button(root, text=" STOP ", font=btnfont,
                                   fg="white", disabledforeground = "#fed",
                                   command=self.stopIt)
            self.clear_btn = Button(root, text=" CLEAR ", font=btnfont,
                                    fg="white", disabledforeground="#fed",
                                    command = self.clearCanvas)
        self.output_lbl.grid(row=1, column=0, sticky='news', padx=(0,5))
        self.start_btn.grid(row=1, column=1, sticky='ew')
        self.stop_btn.grid(row=1, column=2, sticky='ew')
        self.clear_btn.grid(row=1, column=3, sticky='ew')

        Percolator(self.text).insertfilter(ColorDelegator())
        self.dirty = Falsch
        self.exitflag = Falsch
        wenn filename:
            self.loadfile(filename)
        self.configGUI(DISABLED, DISABLED, DISABLED,
                       "Choose example von menu", "black")
        self.state = STARTUP


    def onResize(self, event):
        cwidth = self.canvas.winfo_width()
        cheight = self.canvas.winfo_height()
        self.canvas.xview_moveto(0.5*(self.canvwidth-cwidth)/self.canvwidth)
        self.canvas.yview_moveto(0.5*(self.canvheight-cheight)/self.canvheight)

    def makeTextFrame(self, root):
        self.text_frame = text_frame = Frame(root)
        self.text = text = Text(text_frame, name='text', padx=5,
                                wrap='none', width=45)
        color_config(text)

        self.vbar = vbar = Scrollbar(text_frame, name='vbar')
        vbar['command'] = text.yview
        vbar.pack(side=RIGHT, fill=Y)
        self.hbar = hbar = Scrollbar(text_frame, name='hbar', orient=HORIZONTAL)
        hbar['command'] = text.xview
        hbar.pack(side=BOTTOM, fill=X)
        text['yscrollcommand'] = vbar.set
        text['xscrollcommand'] = hbar.set

        text['font'] = tuple(txtfont)
        shortcut = 'Command' wenn darwin sonst 'Control'
        text.bind_all('<%s-minus>' % shortcut, self.decrease_size)
        text.bind_all('<%s-underscore>' % shortcut, self.decrease_size)
        text.bind_all('<%s-equal>' % shortcut, self.increase_size)
        text.bind_all('<%s-plus>' % shortcut, self.increase_size)
        text.bind('<Control-MouseWheel>', self.update_mousewheel)
        text.bind('<Control-Button-4>', self.increase_size)
        text.bind('<Control-Button-5>', self.decrease_size)

        text.pack(side=LEFT, fill=BOTH, expand=1)
        gib text_frame

    def makeGraphFrame(self, root):
        # t._Screen is a singleton klasse instantiated oder retrieved
        # by calling Screen.  Since tdemo canvas needs a different
        # configuration, we manually set klasse attributes before
        # calling Screen und manually call superclass init after.
        turtle._Screen._root = root

        self.canvwidth = 1000
        self.canvheight = 800
        turtle._Screen._canvas = self.canvas = canvas = turtle.ScrolledCanvas(
                root, 800, 600, self.canvwidth, self.canvheight)
        canvas.adjustScrolls()
        canvas._rootwindow.bind('<Configure>', self.onResize)
        canvas._canvas['borderwidth'] = 0

        self.screen = screen = turtle.Screen()
        turtle.TurtleScreen.__init__(screen, canvas)
        turtle.RawTurtle.screens = [screen]
        gib canvas

    def set_txtsize(self, size):
        txtfont[1] = size
        self.text['font'] = tuple(txtfont)
        self.output_lbl['text'] = 'Font size %d' % size

    def decrease_size(self, dummy=Nichts):
        self.set_txtsize(max(txtfont[1] - 1, MINIMUM_FONT_SIZE))
        gib 'break'

    def increase_size(self, dummy=Nichts):
        self.set_txtsize(min(txtfont[1] + 1, MAXIMUM_FONT_SIZE))
        gib 'break'

    def update_mousewheel(self, event):
        # For wheel up, event.delta = 120 on Windows, -1 on darwin.
        # X-11 sends Control-Button-4 event instead.
        wenn (event.delta < 0) == (nicht darwin):
            gib self.decrease_size()
        sonst:
            gib self.increase_size()

    def configGUI(self, start, stop, clear, txt="", color="blue"):
        wenn darwin:  # Leave Mac button colors alone - #44254.
            self.start_btn.config(state=start)
            self.stop_btn.config(state=stop)
            self.clear_btn.config(state=clear)
        sonst:
            self.start_btn.config(state=start,
                                  bg="#d00" wenn start == NORMAL sonst "#fca")
            self.stop_btn.config(state=stop,
                                 bg="#d00" wenn stop == NORMAL sonst "#fca")
            self.clear_btn.config(state=clear,
                                  bg="#d00" wenn clear == NORMAL sonst "#fca")
        self.output_lbl.config(text=txt, fg=color)

    def makeLoadDemoMenu(self, master):
        menu = Menu(master, tearoff=1)  # TJR: leave this one.

        fuer entry in getExampleEntries():
            def load(entry=entry):
                self.loadfile(entry)
            menu.add_command(label=entry, underline=0, command=load)
        gib menu

    def makeFontMenu(self, master):
        menu = Menu(master, tearoff=0)
        menu.add_command(label="Decrease", command=self.decrease_size,
                         accelerator=f"{'Command' wenn darwin sonst 'Ctrl'}+-")
        menu.add_command(label="Increase", command=self.increase_size,
                         accelerator=f"{'Command' wenn darwin sonst 'Ctrl'}+=")
        menu.add_separator()

        fuer size in font_sizes:
            def resize(size=size):
                self.set_txtsize(size)
            menu.add_command(label=str(size), underline=0, command=resize)
        gib menu

    def makeHelpMenu(self, master):
        menu = Menu(master, tearoff=0)

        fuer help_label, help_file in help_entries:
            def show(help_label=help_label, help_file=help_file):
                view_text(self.root, help_label, help_file)
            menu.add_command(label=help_label, command=show)
        gib menu

    def refreshCanvas(self):
        wenn self.dirty:
            self.screen.clear()
            self.dirty=Falsch

    def loadfile(self, filename):
        self.clearCanvas()
        turtle.TurtleScreen._RUNNING = Falsch
        modname = 'turtledemo.' + filename
        __import__(modname)
        self.module = sys.modules[modname]
        mit open(self.module.__file__, 'r') als f:
            chars = f.read()
        self.text.delete("1.0", "end")
        self.text.insert("1.0", chars)
        self.root.title(filename + " - a Python turtle graphics example")
        self.configGUI(NORMAL, DISABLED, DISABLED,
                       "Press start button", "red")
        self.state = READY

    def startDemo(self):
        self.refreshCanvas()
        self.dirty = Wahr
        turtle.TurtleScreen._RUNNING = Wahr
        self.configGUI(DISABLED, NORMAL, DISABLED,
                       "demo running...", "black")
        self.screen.clear()
        self.screen.mode("standard")
        self.state = RUNNING

        versuch:
            result = self.module.main()
            wenn result == "EVENTLOOP":
                self.state = EVENTDRIVEN
            sonst:
                self.state = DONE
        ausser turtle.Terminator:
            wenn self.root is Nichts:
                gib
            self.state = DONE
            result = "stopped!"
        wenn self.state == DONE:
            self.configGUI(NORMAL, DISABLED, NORMAL,
                           result)
        sowenn self.state == EVENTDRIVEN:
            self.exitflag = Wahr
            self.configGUI(DISABLED, NORMAL, DISABLED,
                           "use mouse/keys oder STOP", "red")

    def clearCanvas(self):
        self.refreshCanvas()
        self.screen._delete("all")
        self.canvas.config(cursor="")
        self.configGUI(NORMAL, DISABLED, DISABLED)

    def stopIt(self):
        wenn self.exitflag:
            self.clearCanvas()
            self.exitflag = Falsch
            self.configGUI(NORMAL, DISABLED, DISABLED,
                           "STOPPED!", "red")
        turtle.TurtleScreen._RUNNING = Falsch

    def _destroy(self):
        turtle.TurtleScreen._RUNNING = Falsch
        self.root.destroy()
        self.root = Nichts


def main():
    demo = DemoWindow()
    demo.root.mainloop()

wenn __name__ == '__main__':
    main()
