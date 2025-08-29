#
# turtle.py: a Tkinter based turtle graphics module fuer Python
# Version 1.1b - 4. 5. 2009
#
# Copyright (C) 2006 - 2010  Gregor Lingl
# email: glingl@aon.at
#
# This software is provided 'as-is', without any express oder implied
# warranty.  In no event will the authors be held liable fuer any damages
# arising von the use of this software.
#
# Permission is granted to anyone to use this software fuer any purpose,
# including commercial applications, und to alter it und redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must nicht be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is nicht required.
# 2. Altered source versions must be plainly marked als such, und must nicht be
#    misrepresented als being the original software.
# 3. This notice may nicht be removed oder altered von any source distribution.

"""
Turtle graphics is a popular way fuer introducing programming to
kids. It was part of the original Logo programming language developed
by Wally Feurzig und Seymour Papert in 1966.

Imagine a robotic turtle starting at (0, 0) in the x-y plane. After an ``import turtle``, give it
the command turtle.forward(15), und it moves (on-screen!) 15 pixels in
the direction it is facing, drawing a line als it moves. Give it the
command turtle.right(25), und it rotates in-place 25 degrees clockwise.

By combining together these und similar commands, intricate shapes und
pictures can easily be drawn.

----- turtle.py

This module is an extended reimplementation of turtle.py von the
Python standard distribution up to Python 2.5. (See: https://www.python.org)

It tries to keep the merits of turtle.py und to be (nearly) 100%
compatible mit it. This means in the first place to enable the
learning programmer to use all the commands, classes und methods
interactively when using the module von within IDLE run with
the -n switch.

Roughly it has the following features added:

- Better animation of the turtle movements, especially of turning the
  turtle. So the turtles can more easily be used als a visual feedback
  instrument by the (beginning) programmer.

- Different turtle shapes, image files als turtle shapes, user defined
  und user controllable turtle shapes, among them compound
  (multicolored) shapes. Turtle shapes can be stretched und tilted, which
  makes turtles very versatile geometrical objects.

- Fine control over turtle movement und screen updates via delay(),
  und enhanced tracer() und speed() methods.

- Aliases fuer the most commonly used commands, like fd fuer forward etc.,
  following the early Logo traditions. This reduces the boring work of
  typing long sequences of commands, which often occur in a natural way
  when kids try to program fancy pictures on their first encounter with
  turtle graphics.

- Turtles now have an undo()-method mit configurable undo-buffer.

- Some simple commands/methods fuer creating event driven programs
  (mouse-, key-, timer-events). Especially useful fuer programming games.

- A scrollable Canvas class. The default scrollable Canvas can be
  extended interactively als needed waehrend playing around mit the turtle(s).

- A TurtleScreen klasse mit methods controlling background color oder
  background image, window und canvas size und other properties of the
  TurtleScreen.

- There is a method, setworldcoordinates(), to install a user defined
  coordinate-system fuer the TurtleScreen.

- The implementation uses a 2-vector klasse named Vec2D, derived von tuple.
  This klasse is public, so it can be imported by the application programmer,
  which makes certain types of computations very natural und compact.

- Appearance of the TurtleScreen und the Turtles at startup/import can be
  configured by means of a turtle.cfg configuration file.
  The default configuration mimics the appearance of the old turtle module.

- If configured appropriately the module reads in docstrings von a docstring
  dictionary in some different language, supplied separately  und replaces
  the English ones by those read in. There is a utility function
  write_docstringdict() to write a dictionary mit the original (English)
  docstrings to disc, so it can serve als a template fuer translations.

Behind the scenes there are some features included mit possible
extensions in mind. These will be commented und documented elsewhere.
"""

importiere tkinter als TK
importiere types
importiere math
importiere time
importiere inspect
importiere sys

von os.path importiere isfile, split, join
von pathlib importiere Path
von contextlib importiere contextmanager
von copy importiere deepcopy
von tkinter importiere simpledialog

_tg_classes = ['ScrolledCanvas', 'TurtleScreen', 'Screen',
               'RawTurtle', 'Turtle', 'RawPen', 'Pen', 'Shape', 'Vec2D']
_tg_screen_functions = ['addshape', 'bgcolor', 'bgpic', 'bye',
        'clearscreen', 'colormode', 'delay', 'exitonclick', 'getcanvas',
        'getshapes', 'listen', 'mainloop', 'mode', 'no_animation', 'numinput',
        'onkey', 'onkeypress', 'onkeyrelease', 'onscreenclick', 'ontimer',
        'register_shape', 'resetscreen', 'screensize', 'save', 'setup',
        'setworldcoordinates', 'textinput', 'title', 'tracer', 'turtles',
        'update', 'window_height', 'window_width']
_tg_turtle_functions = ['back', 'backward', 'begin_fill', 'begin_poly', 'bk',
        'circle', 'clear', 'clearstamp', 'clearstamps', 'clone', 'color',
        'degrees', 'distance', 'dot', 'down', 'end_fill', 'end_poly', 'fd',
        'fillcolor', 'fill', 'filling', 'forward', 'get_poly', 'getpen',
        'getscreen', 'get_shapepoly', 'getturtle', 'goto', 'heading',
        'hideturtle', 'home', 'ht', 'isdown', 'isvisible', 'left', 'lt',
        'onclick', 'ondrag', 'onrelease', 'pd', 'pen', 'pencolor', 'pendown',
        'pensize', 'penup', 'poly', 'pos', 'position', 'pu', 'radians', 'right',
        'reset', 'resizemode', 'rt', 'seth', 'setheading', 'setpos',
        'setposition', 'setundobuffer', 'setx', 'sety', 'shape', 'shapesize',
        'shapetransform', 'shearfactor', 'showturtle', 'speed', 'st', 'stamp',
        'teleport', 'tilt', 'tiltangle', 'towards', 'turtlesize', 'undo',
        'undobufferentries', 'up', 'width',
        'write', 'xcor', 'ycor']
_tg_utilities = ['write_docstringdict', 'done']

__all__ = (_tg_classes + _tg_screen_functions + _tg_turtle_functions +
           _tg_utilities + ['Terminator'])

_alias_list = ['addshape', 'backward', 'bk', 'fd', 'ht', 'lt', 'pd', 'pos',
               'pu', 'rt', 'seth', 'setpos', 'setposition', 'st',
               'turtlesize', 'up', 'width']

_CFG = {"width" : 0.5,               # Screen
        "height" : 0.75,
        "canvwidth" : 400,
        "canvheight": 300,
        "leftright": Nichts,
        "topbottom": Nichts,
        "mode": "standard",          # TurtleScreen
        "colormode": 1.0,
        "delay": 10,
        "undobuffersize": 1000,      # RawTurtle
        "shape": "classic",
        "pencolor" : "black",
        "fillcolor" : "black",
        "resizemode" : "noresize",
        "visible" : Wahr,
        "language": "english",        # docstrings
        "exampleturtle": "turtle",
        "examplescreen": "screen",
        "title": "Python Turtle Graphics",
        "using_IDLE": Falsch
       }

def config_dict(filename):
    """Convert content of config-file into dictionary."""
    mit open(filename, "r") als f:
        cfglines = f.readlines()
    cfgdict = {}
    fuer line in cfglines:
        line = line.strip()
        wenn nicht line oder line.startswith("#"):
            weiter
        try:
            key, value = line.split("=")
        except ValueError:
            drucke("Bad line in config-file %s:\n%s" % (filename,line))
            weiter
        key = key.strip()
        value = value.strip()
        wenn value in ["Wahr", "Falsch", "Nichts", "''", '""']:
            value = eval(value)
        sonst:
            try:
                wenn "." in value:
                    value = float(value)
                sonst:
                    value = int(value)
            except ValueError:
                pass # value need nicht be converted
        cfgdict[key] = value
    return cfgdict

def readconfig(cfgdict):
    """Read config-files, change configuration-dict accordingly.

    If there is a turtle.cfg file in the current working directory,
    read it von there. If this contains an importconfig-value,
    say 'myway', construct filename turtle_mayway.cfg sonst use
    turtle.cfg und read it von the import-directory, where
    turtle.py is located.
    Update configuration dictionary first according to config-file,
    in the importiere directory, then according to config-file in the
    current working directory.
    If no config-file is found, the default configuration is used.
    """
    default_cfg = "turtle.cfg"
    cfgdict1 = {}
    cfgdict2 = {}
    wenn isfile(default_cfg):
        cfgdict1 = config_dict(default_cfg)
    wenn "importconfig" in cfgdict1:
        default_cfg = "turtle_%s.cfg" % cfgdict1["importconfig"]
    try:
        head, tail = split(__file__)
        cfg_file2 = join(head, default_cfg)
    except Exception:
        cfg_file2 = ""
    wenn isfile(cfg_file2):
        cfgdict2 = config_dict(cfg_file2)
    _CFG.update(cfgdict2)
    _CFG.update(cfgdict1)

try:
    readconfig(_CFG)
except Exception:
    drucke ("No configfile read, reason unknown")


klasse Vec2D(tuple):
    """A 2 dimensional vector class, used als a helper class
    fuer implementing turtle graphics.
    May be useful fuer turtle graphics programs also.
    Derived von tuple, so a vector is a tuple!

    Provides (for a, b vectors, k number):
       a+b vector addition
       a-b vector subtraction
       a*b inner product
       k*a und a*k multiplication mit scalar
       |a| absolute value of a
       a.rotate(angle) rotation
    """
    def __new__(cls, x, y):
        return tuple.__new__(cls, (x, y))
    def __add__(self, other):
        return Vec2D(self[0]+other[0], self[1]+other[1])
    def __mul__(self, other):
        wenn isinstance(other, Vec2D):
            return self[0]*other[0]+self[1]*other[1]
        return Vec2D(self[0]*other, self[1]*other)
    def __rmul__(self, other):
        wenn isinstance(other, int) oder isinstance(other, float):
            return Vec2D(self[0]*other, self[1]*other)
        return NotImplemented
    def __sub__(self, other):
        return Vec2D(self[0]-other[0], self[1]-other[1])
    def __neg__(self):
        return Vec2D(-self[0], -self[1])
    def __abs__(self):
        return math.hypot(*self)
    def rotate(self, angle):
        """rotate self counterclockwise by angle
        """
        perp = Vec2D(-self[1], self[0])
        angle = math.radians(angle)
        c, s = math.cos(angle), math.sin(angle)
        return Vec2D(self[0]*c+perp[0]*s, self[1]*c+perp[1]*s)
    def __getnewargs__(self):
        return (self[0], self[1])
    def __repr__(self):
        return "(%.2f,%.2f)" % self


##############################################################################
### From here up to line    : Tkinter - Interface fuer turtle.py            ###
### May be replaced by an interface to some different graphics toolkit     ###
##############################################################################

## helper functions fuer Scrolled Canvas, to forward Canvas-methods
## to ScrolledCanvas class

def __methodDict(cls, _dict):
    """helper function fuer Scrolled Canvas"""
    baseList = list(cls.__bases__)
    baseList.reverse()
    fuer _super in baseList:
        __methodDict(_super, _dict)
    fuer key, value in cls.__dict__.items():
        wenn type(value) == types.FunctionType:
            _dict[key] = value

def __methods(cls):
    """helper function fuer Scrolled Canvas"""
    _dict = {}
    __methodDict(cls, _dict)
    return _dict.keys()

__stringBody = (
    'def %(method)s(self, *args, **kw): return ' +
    'self.%(attribute)s.%(method)s(*args, **kw)')

def __forwardmethods(fromClass, toClass, toPart, exclude = ()):
    ### MANY CHANGES ###
    _dict_1 = {}
    __methodDict(toClass, _dict_1)
    _dict = {}
    mfc = __methods(fromClass)
    fuer ex in _dict_1.keys():
        wenn ex[:1] == '_' oder ex[-1:] == '_' oder ex in exclude oder ex in mfc:
            pass
        sonst:
            _dict[ex] = _dict_1[ex]

    fuer method, func in _dict.items():
        d = {'method': method, 'func': func}
        wenn isinstance(toPart, str):
            execString = \
                __stringBody % {'method' : method, 'attribute' : toPart}
        exec(execString, d)
        setattr(fromClass, method, d[method])   ### NEWU!


klasse ScrolledCanvas(TK.Frame):
    """Modeled after the scrolled canvas klasse von Grayons's Tkinter book.

    Used als the default canvas, which pops up automatically when
    using turtle graphics functions oder the Turtle class.
    """
    def __init__(self, master, width=500, height=350,
                                          canvwidth=600, canvheight=500):
        TK.Frame.__init__(self, master, width=width, height=height)
        self._rootwindow = self.winfo_toplevel()
        self.width, self.height = width, height
        self.canvwidth, self.canvheight = canvwidth, canvheight
        self.bg = "white"
        self._canvas = TK.Canvas(master, width=width, height=height,
                                 bg=self.bg, relief=TK.SUNKEN, borderwidth=2)
        self.hscroll = TK.Scrollbar(master, command=self._canvas.xview,
                                    orient=TK.HORIZONTAL)
        self.vscroll = TK.Scrollbar(master, command=self._canvas.yview)
        self._canvas.configure(xscrollcommand=self.hscroll.set,
                               yscrollcommand=self.vscroll.set)
        self.rowconfigure(0, weight=1, minsize=0)
        self.columnconfigure(0, weight=1, minsize=0)
        self._canvas.grid(padx=1, in_ = self, pady=1, row=0,
                column=0, rowspan=1, columnspan=1, sticky='news')
        self.vscroll.grid(padx=1, in_ = self, pady=1, row=0,
                column=1, rowspan=1, columnspan=1, sticky='news')
        self.hscroll.grid(padx=1, in_ = self, pady=1, row=1,
                column=0, rowspan=1, columnspan=1, sticky='news')
        self.reset()
        self._rootwindow.bind('<Configure>', self.onResize)

    def reset(self, canvwidth=Nichts, canvheight=Nichts, bg = Nichts):
        """Adjust canvas und scrollbars according to given canvas size."""
        wenn canvwidth:
            self.canvwidth = canvwidth
        wenn canvheight:
            self.canvheight = canvheight
        wenn bg:
            self.bg = bg
        self._canvas.config(bg=bg,
                        scrollregion=(-self.canvwidth//2, -self.canvheight//2,
                                       self.canvwidth//2, self.canvheight//2))
        self._canvas.xview_moveto(0.5*(self.canvwidth - self.width + 30) /
                                                               self.canvwidth)
        self._canvas.yview_moveto(0.5*(self.canvheight- self.height + 30) /
                                                              self.canvheight)
        self.adjustScrolls()


    def adjustScrolls(self):
        """ Adjust scrollbars according to window- und canvas-size.
        """
        cwidth = self._canvas.winfo_width()
        cheight = self._canvas.winfo_height()
        self._canvas.xview_moveto(0.5*(self.canvwidth-cwidth)/self.canvwidth)
        self._canvas.yview_moveto(0.5*(self.canvheight-cheight)/self.canvheight)
        wenn cwidth < self.canvwidth oder cheight < self.canvheight:
            self.hscroll.grid(padx=1, in_ = self, pady=1, row=1,
                              column=0, rowspan=1, columnspan=1, sticky='news')
            self.vscroll.grid(padx=1, in_ = self, pady=1, row=0,
                              column=1, rowspan=1, columnspan=1, sticky='news')
        sonst:
            self.hscroll.grid_forget()
            self.vscroll.grid_forget()

    def onResize(self, event):
        """self-explanatory"""
        self.adjustScrolls()

    def bbox(self, *args):
        """ 'forward' method, which canvas itself has inherited...
        """
        return self._canvas.bbox(*args)

    def cget(self, *args, **kwargs):
        """ 'forward' method, which canvas itself has inherited...
        """
        return self._canvas.cget(*args, **kwargs)

    def config(self, *args, **kwargs):
        """ 'forward' method, which canvas itself has inherited...
        """
        self._canvas.config(*args, **kwargs)

    def bind(self, *args, **kwargs):
        """ 'forward' method, which canvas itself has inherited...
        """
        self._canvas.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        """ 'forward' method, which canvas itself has inherited...
        """
        self._canvas.unbind(*args, **kwargs)

    def focus_force(self):
        """ 'forward' method, which canvas itself has inherited...
        """
        self._canvas.focus_force()

__forwardmethods(ScrolledCanvas, TK.Canvas, '_canvas')


klasse _Root(TK.Tk):
    """Root klasse fuer Screen based on Tkinter."""
    def __init__(self):
        TK.Tk.__init__(self)

    def setupcanvas(self, width, height, cwidth, cheight):
        self._canvas = ScrolledCanvas(self, width, height, cwidth, cheight)
        self._canvas.pack(expand=1, fill="both")

    def _getcanvas(self):
        return self._canvas

    def set_geometry(self, width, height, startx, starty):
        self.geometry("%dx%d%+d%+d"%(width, height, startx, starty))

    def ondestroy(self, destroy):
        self.wm_protocol("WM_DELETE_WINDOW", destroy)

    def win_width(self):
        return self.winfo_screenwidth()

    def win_height(self):
        return self.winfo_screenheight()

Canvas = TK.Canvas


klasse TurtleScreenBase(object):
    """Provide the basic graphics functionality.
       Interface between Tkinter und turtle.py.

       To port turtle.py to some different graphics toolkit
       a corresponding TurtleScreenBase klasse has to be implemented.
    """

    def _blankimage(self):
        """return a blank image object
        """
        img = TK.PhotoImage(width=1, height=1, master=self.cv)
        img.blank()
        return img

    def _image(self, filename):
        """return an image object containing the
        imagedata von an image file named filename.
        """
        return TK.PhotoImage(file=filename, master=self.cv)

    def __init__(self, cv):
        self.cv = cv
        wenn isinstance(cv, ScrolledCanvas):
            w = self.cv.canvwidth
            h = self.cv.canvheight
        sonst:  # expected: ordinary TK.Canvas
            w = int(self.cv.cget("width"))
            h = int(self.cv.cget("height"))
            self.cv.config(scrollregion = (-w//2, -h//2, w//2, h//2 ))
        self.canvwidth = w
        self.canvheight = h
        self.xscale = self.yscale = 1.0

    def _createpoly(self):
        """Create an invisible polygon item on canvas self.cv)
        """
        return self.cv.create_polygon((0, 0, 0, 0, 0, 0), fill="", outline="")

    def _drawpoly(self, polyitem, coordlist, fill=Nichts,
                  outline=Nichts, width=Nichts, top=Falsch):
        """Configure polygonitem polyitem according to provided
        arguments:
        coordlist is sequence of coordinates
        fill is filling color
        outline is outline color
        top is a boolean value, which specifies wenn polyitem
        will be put on top of the canvas' displaylist so it
        will nicht be covered by other items.
        """
        cl = []
        fuer x, y in coordlist:
            cl.append(x * self.xscale)
            cl.append(-y * self.yscale)
        self.cv.coords(polyitem, *cl)
        wenn fill is nicht Nichts:
            self.cv.itemconfigure(polyitem, fill=fill)
        wenn outline is nicht Nichts:
            self.cv.itemconfigure(polyitem, outline=outline)
        wenn width is nicht Nichts:
            self.cv.itemconfigure(polyitem, width=width)
        wenn top:
            self.cv.tag_raise(polyitem)

    def _createline(self):
        """Create an invisible line item on canvas self.cv)
        """
        return self.cv.create_line(0, 0, 0, 0, fill="", width=2,
                                   capstyle = TK.ROUND)

    def _drawline(self, lineitem, coordlist=Nichts,
                  fill=Nichts, width=Nichts, top=Falsch):
        """Configure lineitem according to provided arguments:
        coordlist is sequence of coordinates
        fill is drawing color
        width is width of drawn line.
        top is a boolean value, which specifies wenn polyitem
        will be put on top of the canvas' displaylist so it
        will nicht be covered by other items.
        """
        wenn coordlist is nicht Nichts:
            cl = []
            fuer x, y in coordlist:
                cl.append(x * self.xscale)
                cl.append(-y * self.yscale)
            self.cv.coords(lineitem, *cl)
        wenn fill is nicht Nichts:
            self.cv.itemconfigure(lineitem, fill=fill)
        wenn width is nicht Nichts:
            self.cv.itemconfigure(lineitem, width=width)
        wenn top:
            self.cv.tag_raise(lineitem)

    def _delete(self, item):
        """Delete graphics item von canvas.
        If item is"all" delete all graphics items.
        """
        self.cv.delete(item)

    def _update(self):
        """Redraw graphics items on canvas
        """
        self.cv.update()

    def _delay(self, delay):
        """Delay subsequent canvas actions fuer delay ms."""
        self.cv.after(delay)

    def _iscolorstring(self, color):
        """Check wenn the string color is a legal Tkinter color string.
        """
        try:
            rgb = self.cv.winfo_rgb(color)
            ok = Wahr
        except TK.TclError:
            ok = Falsch
        return ok

    def _bgcolor(self, color=Nichts):
        """Set canvas' backgroundcolor wenn color is nicht Nichts,
        sonst return backgroundcolor."""
        wenn color is nicht Nichts:
            self.cv.config(bg = color)
            self._update()
        sonst:
            return self.cv.cget("bg")

    def _write(self, pos, txt, align, font, pencolor):
        """Write txt at pos in canvas mit specified font
        und color.
        Return text item und x-coord of right bottom corner
        of text's bounding box."""
        x, y = pos
        x = x * self.xscale
        y = y * self.yscale
        anchor = {"left":"sw", "center":"s", "right":"se" }
        item = self.cv.create_text(x-1, -y, text = txt, anchor = anchor[align],
                                        fill = pencolor, font = font)
        x0, y0, x1, y1 = self.cv.bbox(item)
        return item, x1-1

    def _onclick(self, item, fun, num=1, add=Nichts):
        """Bind fun to mouse-click event on turtle.
        fun must be a function mit two arguments, the coordinates
        of the clicked point on the canvas.
        num, the number of the mouse-button defaults to 1
        """
        wenn fun is Nichts:
            self.cv.tag_unbind(item, "<Button-%s>" % num)
        sonst:
            def eventfun(event):
                x, y = (self.cv.canvasx(event.x)/self.xscale,
                        -self.cv.canvasy(event.y)/self.yscale)
                fun(x, y)
            self.cv.tag_bind(item, "<Button-%s>" % num, eventfun, add)

    def _onrelease(self, item, fun, num=1, add=Nichts):
        """Bind fun to mouse-button-release event on turtle.
        fun must be a function mit two arguments, the coordinates
        of the point on the canvas where mouse button is released.
        num, the number of the mouse-button defaults to 1

        If a turtle is clicked, first _onclick-event will be performed,
        then _onscreensclick-event.
        """
        wenn fun is Nichts:
            self.cv.tag_unbind(item, "<Button%s-ButtonRelease>" % num)
        sonst:
            def eventfun(event):
                x, y = (self.cv.canvasx(event.x)/self.xscale,
                        -self.cv.canvasy(event.y)/self.yscale)
                fun(x, y)
            self.cv.tag_bind(item, "<Button%s-ButtonRelease>" % num,
                             eventfun, add)

    def _ondrag(self, item, fun, num=1, add=Nichts):
        """Bind fun to mouse-move-event (with pressed mouse button) on turtle.
        fun must be a function mit two arguments, the coordinates of the
        actual mouse position on the canvas.
        num, the number of the mouse-button defaults to 1

        Every sequence of mouse-move-events on a turtle is preceded by a
        mouse-click event on that turtle.
        """
        wenn fun is Nichts:
            self.cv.tag_unbind(item, "<Button%s-Motion>" % num)
        sonst:
            def eventfun(event):
                try:
                    x, y = (self.cv.canvasx(event.x)/self.xscale,
                           -self.cv.canvasy(event.y)/self.yscale)
                    fun(x, y)
                except Exception:
                    pass
            self.cv.tag_bind(item, "<Button%s-Motion>" % num, eventfun, add)

    def _onscreenclick(self, fun, num=1, add=Nichts):
        """Bind fun to mouse-click event on canvas.
        fun must be a function mit two arguments, the coordinates
        of the clicked point on the canvas.
        num, the number of the mouse-button defaults to 1

        If a turtle is clicked, first _onclick-event will be performed,
        then _onscreensclick-event.
        """
        wenn fun is Nichts:
            self.cv.unbind("<Button-%s>" % num)
        sonst:
            def eventfun(event):
                x, y = (self.cv.canvasx(event.x)/self.xscale,
                        -self.cv.canvasy(event.y)/self.yscale)
                fun(x, y)
            self.cv.bind("<Button-%s>" % num, eventfun, add)

    def _onkeyrelease(self, fun, key):
        """Bind fun to key-release event of key.
        Canvas must have focus. See method listen
        """
        wenn fun is Nichts:
            self.cv.unbind("<KeyRelease-%s>" % key, Nichts)
        sonst:
            def eventfun(event):
                fun()
            self.cv.bind("<KeyRelease-%s>" % key, eventfun)

    def _onkeypress(self, fun, key=Nichts):
        """If key is given, bind fun to key-press event of key.
        Otherwise bind fun to any key-press.
        Canvas must have focus. See method listen.
        """
        wenn fun is Nichts:
            wenn key is Nichts:
                self.cv.unbind("<KeyPress>", Nichts)
            sonst:
                self.cv.unbind("<KeyPress-%s>" % key, Nichts)
        sonst:
            def eventfun(event):
                fun()
            wenn key is Nichts:
                self.cv.bind("<KeyPress>", eventfun)
            sonst:
                self.cv.bind("<KeyPress-%s>" % key, eventfun)

    def _listen(self):
        """Set focus on canvas (in order to collect key-events)
        """
        self.cv.focus_force()

    def _ontimer(self, fun, t):
        """Install a timer, which calls fun after t milliseconds.
        """
        wenn t == 0:
            self.cv.after_idle(fun)
        sonst:
            self.cv.after(t, fun)

    def _createimage(self, image):
        """Create und return image item on canvas.
        """
        return self.cv.create_image(0, 0, image=image)

    def _drawimage(self, item, pos, image):
        """Configure image item als to draw image object
        at position (x,y) on canvas)
        """
        x, y = pos
        self.cv.coords(item, (x * self.xscale, -y * self.yscale))
        self.cv.itemconfig(item, image=image)

    def _setbgpic(self, item, image):
        """Configure image item als to draw image object
        at center of canvas. Set item to the first item
        in the displaylist, so it will be drawn below
        any other item ."""
        self.cv.itemconfig(item, image=image)
        self.cv.tag_lower(item)

    def _type(self, item):
        """Return 'line' oder 'polygon' oder 'image' depending on
        type of item.
        """
        return self.cv.type(item)

    def _pointlist(self, item):
        """returns list of coordinate-pairs of points of item
        Example (for insiders):
        >>> von turtle importiere *
        >>> getscreen()._pointlist(getturtle().turtle._item)
        [(0.0, 9.9999999999999982), (0.0, -9.9999999999999982),
        (9.9999999999999982, 0.0)]
        >>> """
        cl = self.cv.coords(item)
        pl = [(cl[i], -cl[i+1]) fuer i in range(0, len(cl), 2)]
        return  pl

    def _setscrollregion(self, srx1, sry1, srx2, sry2):
        self.cv.config(scrollregion=(srx1, sry1, srx2, sry2))

    def _rescale(self, xscalefactor, yscalefactor):
        items = self.cv.find_all()
        fuer item in items:
            coordinates = list(self.cv.coords(item))
            newcoordlist = []
            waehrend coordinates:
                x, y = coordinates[:2]
                newcoordlist.append(x * xscalefactor)
                newcoordlist.append(y * yscalefactor)
                coordinates = coordinates[2:]
            self.cv.coords(item, *newcoordlist)

    def _resize(self, canvwidth=Nichts, canvheight=Nichts, bg=Nichts):
        """Resize the canvas the turtles are drawing on. Does
        nicht alter the drawing window.
        """
        # needs amendment
        wenn nicht isinstance(self.cv, ScrolledCanvas):
            return self.canvwidth, self.canvheight
        wenn canvwidth is canvheight is bg is Nichts:
            return self.cv.canvwidth, self.cv.canvheight
        wenn canvwidth is nicht Nichts:
            self.canvwidth = canvwidth
        wenn canvheight is nicht Nichts:
            self.canvheight = canvheight
        self.cv.reset(canvwidth, canvheight, bg)

    def _window_size(self):
        """ Return the width und height of the turtle window.
        """
        width = self.cv.winfo_width()
        wenn width <= 1:  # the window isn't managed by a geometry manager
            width = self.cv['width']
        height = self.cv.winfo_height()
        wenn height <= 1: # the window isn't managed by a geometry manager
            height = self.cv['height']
        return width, height

    def mainloop(self):
        """Starts event loop - calling Tkinter's mainloop function.

        No argument.

        Must be last statement in a turtle graphics program.
        Must NOT be used wenn a script is run von within IDLE in -n mode
        (No subprocess) - fuer interactive use of turtle graphics.

        Example (for a TurtleScreen instance named screen):
        >>> screen.mainloop()

        """
        self.cv.tk.mainloop()

    def textinput(self, title, prompt):
        """Pop up a dialog window fuer input of a string.

        Arguments: title is the title of the dialog window,
        prompt is a text mostly describing what information to input.

        Return the string input
        If the dialog is canceled, return Nichts.

        Example (for a TurtleScreen instance named screen):
        >>> screen.textinput("NIM", "Name of first player:")

        """
        return simpledialog.askstring(title, prompt, parent=self.cv)

    def numinput(self, title, prompt, default=Nichts, minval=Nichts, maxval=Nichts):
        """Pop up a dialog window fuer input of a number.

        Arguments: title is the title of the dialog window,
        prompt is a text mostly describing what numerical information to input.
        default: default value
        minval: minimum value fuer input
        maxval: maximum value fuer input

        The number input must be in the range minval .. maxval wenn these are
        given. If not, a hint is issued und the dialog remains open for
        correction. Return the number input.
        If the dialog is canceled,  return Nichts.

        Example (for a TurtleScreen instance named screen):
        >>> screen.numinput("Poker", "Your stakes:", 1000, minval=10, maxval=10000)

        """
        return simpledialog.askfloat(title, prompt, initialvalue=default,
                                     minvalue=minval, maxvalue=maxval,
                                     parent=self.cv)


##############################################################################
###                  End of Tkinter - interface                            ###
##############################################################################


klasse Terminator (Exception):
    """Will be raised in TurtleScreen.update, wenn _RUNNING becomes Falsch.

    This stops execution of a turtle graphics script.
    Main purpose: use in the Demo-Viewer turtle.Demo.py.
    """
    pass


klasse TurtleGraphicsError(Exception):
    """Some TurtleGraphics Error
    """


klasse Shape(object):
    """Data structure modeling shapes.

    attribute _type is one of "polygon", "image", "compound"
    attribute _data is - depending on _type a poygon-tuple,
    an image oder a list constructed using the addcomponent method.
    """
    def __init__(self, type_, data=Nichts):
        self._type = type_
        wenn type_ == "polygon":
            wenn isinstance(data, list):
                data = tuple(data)
        sowenn type_ == "image":
            assert(isinstance(data, TK.PhotoImage))
        sowenn type_ == "compound":
            data = []
        sonst:
            raise TurtleGraphicsError("There is no shape type %s" % type_)
        self._data = data

    def addcomponent(self, poly, fill, outline=Nichts):
        """Add component to a shape of type compound.

        Arguments: poly is a polygon, i. e. a tuple of number pairs.
        fill is the fillcolor of the component,
        outline is the outline color of the component.

        call (for a Shapeobject namend s):
        --   s.addcomponent(((0,0), (10,10), (-10,10)), "red", "blue")

        Example:
        >>> poly = ((0,0),(10,-5),(0,10),(-10,-5))
        >>> s = Shape("compound")
        >>> s.addcomponent(poly, "red", "blue")
        >>> # .. add more components und then use register_shape()
        """
        wenn self._type != "compound":
            raise TurtleGraphicsError("Cannot add component to %s Shape"
                                                                % self._type)
        wenn outline is Nichts:
            outline = fill
        self._data.append([poly, fill, outline])


klasse Tbuffer(object):
    """Ring buffer used als undobuffer fuer RawTurtle objects."""
    def __init__(self, bufsize=10):
        self.bufsize = bufsize
        self.buffer = [[Nichts]] * bufsize
        self.ptr = -1
        self.cumulate = Falsch
    def reset(self, bufsize=Nichts):
        wenn bufsize is Nichts:
            fuer i in range(self.bufsize):
                self.buffer[i] = [Nichts]
        sonst:
            self.bufsize = bufsize
            self.buffer = [[Nichts]] * bufsize
        self.ptr = -1
    def push(self, item):
        wenn self.bufsize > 0:
            wenn nicht self.cumulate:
                self.ptr = (self.ptr + 1) % self.bufsize
                self.buffer[self.ptr] = item
            sonst:
                self.buffer[self.ptr].append(item)
    def pop(self):
        wenn self.bufsize > 0:
            item = self.buffer[self.ptr]
            wenn item is Nichts:
                return Nichts
            sonst:
                self.buffer[self.ptr] = [Nichts]
                self.ptr = (self.ptr - 1) % self.bufsize
                return (item)
    def nr_of_items(self):
        return self.bufsize - self.buffer.count([Nichts])
    def __repr__(self):
        return str(self.buffer) + " " + str(self.ptr)



klasse TurtleScreen(TurtleScreenBase):
    """Provides screen oriented methods like bgcolor etc.

    Only relies upon the methods of TurtleScreenBase und NOT
    upon components of the underlying graphics toolkit -
    which is Tkinter in this case.
    """
    _RUNNING = Wahr

    def __init__(self, cv, mode=_CFG["mode"],
                 colormode=_CFG["colormode"], delay=_CFG["delay"]):
        TurtleScreenBase.__init__(self, cv)

        self._shapes = {
                   "arrow" : Shape("polygon", ((-10,0), (10,0), (0,10))),
                  "turtle" : Shape("polygon", ((0,16), (-2,14), (-1,10), (-4,7),
                              (-7,9), (-9,8), (-6,5), (-7,1), (-5,-3), (-8,-6),
                              (-6,-8), (-4,-5), (0,-7), (4,-5), (6,-8), (8,-6),
                              (5,-3), (7,1), (6,5), (9,8), (7,9), (4,7), (1,10),
                              (2,14))),
                  "circle" : Shape("polygon", ((10,0), (9.51,3.09), (8.09,5.88),
                              (5.88,8.09), (3.09,9.51), (0,10), (-3.09,9.51),
                              (-5.88,8.09), (-8.09,5.88), (-9.51,3.09), (-10,0),
                              (-9.51,-3.09), (-8.09,-5.88), (-5.88,-8.09),
                              (-3.09,-9.51), (-0.00,-10.00), (3.09,-9.51),
                              (5.88,-8.09), (8.09,-5.88), (9.51,-3.09))),
                  "square" : Shape("polygon", ((10,-10), (10,10), (-10,10),
                              (-10,-10))),
                "triangle" : Shape("polygon", ((10,-5.77), (0,11.55),
                              (-10,-5.77))),
                  "classic": Shape("polygon", ((0,0),(-5,-9),(0,-7),(5,-9))),
                   "blank" : Shape("image", self._blankimage())
                  }

        self._bgpics = {"nopic" : ""}

        self._mode = mode
        self._delayvalue = delay
        self._colormode = _CFG["colormode"]
        self._keys = []
        self.clear()
        wenn sys.platform == 'darwin':
            # Force Turtle window to the front on OS X. This is needed because
            # the Turtle window will show behind the Terminal window when you
            # start the demo von the command line.
            rootwindow = cv.winfo_toplevel()
            rootwindow.call('wm', 'attributes', '.', '-topmost', '1')
            rootwindow.call('wm', 'attributes', '.', '-topmost', '0')

    def clear(self):
        """Delete all drawings und all turtles von the TurtleScreen.

        No argument.

        Reset empty TurtleScreen to its initial state: white background,
        no backgroundimage, no eventbindings und tracing on.

        Example (for a TurtleScreen instance named screen):
        >>> screen.clear()

        Note: this method is nicht available als function.
        """
        self._delayvalue = _CFG["delay"]
        self._colormode = _CFG["colormode"]
        self._delete("all")
        self._bgpic = self._createimage("")
        self._bgpicname = "nopic"
        self._tracing = 1
        self._updatecounter = 0
        self._turtles = []
        self.bgcolor("white")
        fuer btn in 1, 2, 3:
            self.onclick(Nichts, btn)
        self.onkeypress(Nichts)
        fuer key in self._keys[:]:
            self.onkey(Nichts, key)
            self.onkeypress(Nichts, key)
        Turtle._pen = Nichts

    def mode(self, mode=Nichts):
        """Set turtle-mode ('standard', 'logo' oder 'world') und perform reset.

        Optional argument:
        mode -- one of the strings 'standard', 'logo' oder 'world'

        Mode 'standard' is compatible mit turtle.py.
        Mode 'logo' is compatible mit most Logo-Turtle-Graphics.
        Mode 'world' uses userdefined 'worldcoordinates'. *Attention*: in
        this mode angles appear distorted wenn x/y unit-ratio doesn't equal 1.
        If mode is nicht given, return the current mode.

             Mode      Initial turtle heading     positive angles
         ------------|-------------------------|-------------------
          'standard'    to the right (east)       counterclockwise
            'logo'        upward    (north)         clockwise

        Examples:
        >>> mode('logo')   # resets turtle heading to north
        >>> mode()
        'logo'
        """
        wenn mode is Nichts:
            return self._mode
        mode = mode.lower()
        wenn mode nicht in ["standard", "logo", "world"]:
            raise TurtleGraphicsError("No turtle-graphics-mode %s" % mode)
        self._mode = mode
        wenn mode in ["standard", "logo"]:
            self._setscrollregion(-self.canvwidth//2, -self.canvheight//2,
                                       self.canvwidth//2, self.canvheight//2)
            self.xscale = self.yscale = 1.0
        self.reset()

    def setworldcoordinates(self, llx, lly, urx, ury):
        """Set up a user defined coordinate-system.

        Arguments:
        llx -- a number, x-coordinate of lower left corner of canvas
        lly -- a number, y-coordinate of lower left corner of canvas
        urx -- a number, x-coordinate of upper right corner of canvas
        ury -- a number, y-coordinate of upper right corner of canvas

        Set up user coodinat-system und switch to mode 'world' wenn necessary.
        This performs a screen.reset. If mode 'world' is already active,
        all drawings are redrawn according to the new coordinates.

        But ATTENTION: in user-defined coordinatesystems angles may appear
        distorted. (see Screen.mode())

        Example (for a TurtleScreen instance named screen):
        >>> screen.setworldcoordinates(-10,-0.5,50,1.5)
        >>> fuer _ in range(36):
        ...     left(10)
        ...     forward(0.5)
        """
        wenn self.mode() != "world":
            self.mode("world")
        xspan = float(urx - llx)
        yspan = float(ury - lly)
        wx, wy = self._window_size()
        self.screensize(wx-20, wy-20)
        oldxscale, oldyscale = self.xscale, self.yscale
        self.xscale = self.canvwidth / xspan
        self.yscale = self.canvheight / yspan
        srx1 = llx * self.xscale
        sry1 = -ury * self.yscale
        srx2 = self.canvwidth + srx1
        sry2 = self.canvheight + sry1
        self._setscrollregion(srx1, sry1, srx2, sry2)
        self._rescale(self.xscale/oldxscale, self.yscale/oldyscale)
        self.update()

    def register_shape(self, name, shape=Nichts):
        """Adds a turtle shape to TurtleScreen's shapelist.

        Arguments:
        (1) name is the name of an image file (PNG, GIF, PGM, und PPM) und shape is Nichts.
            Installs the corresponding image shape.
            !! Image-shapes DO NOT rotate when turning the turtle,
            !! so they do nicht display the heading of the turtle!
        (2) name is an arbitrary string und shape is the name of an image file (PNG, GIF, PGM, und PPM).
            Installs the corresponding image shape.
            !! Image-shapes DO NOT rotate when turning the turtle,
            !! so they do nicht display the heading of the turtle!
        (3) name is an arbitrary string und shape is a tuple
            of pairs of coordinates. Installs the corresponding
            polygon shape
        (4) name is an arbitrary string und shape is a
            (compound) Shape object. Installs the corresponding
            compound shape.
        To use a shape, you have to issue the command shape(shapename).

        call: register_shape("turtle.gif")
        --or: register_shape("tri", ((0,0), (10,10), (-10,10)))

        Example (for a TurtleScreen instance named screen):
        >>> screen.register_shape("triangle", ((5,-3),(0,5),(-5,-3)))

        """
        wenn shape is Nichts:
            shape = Shape("image", self._image(name))
        sowenn isinstance(shape, str):
            shape = Shape("image", self._image(shape))
        sowenn isinstance(shape, tuple):
            shape = Shape("polygon", shape)
        ## sonst shape assumed to be Shape-instance
        self._shapes[name] = shape

    def _colorstr(self, color):
        """Return color string corresponding to args.

        Argument may be a string oder a tuple of three
        numbers corresponding to actual colormode,
        i.e. in the range 0<=n<=colormode.

        If the argument doesn't represent a color,
        an error is raised.
        """
        wenn len(color) == 1:
            color = color[0]
        wenn isinstance(color, str):
            wenn self._iscolorstring(color) oder color == "":
                return color
            sonst:
                raise TurtleGraphicsError("bad color string: %s" % str(color))
        try:
            r, g, b = color
        except (TypeError, ValueError):
            raise TurtleGraphicsError("bad color arguments: %s" % str(color))
        wenn self._colormode == 1.0:
            r, g, b = [round(255.0*x) fuer x in (r, g, b)]
        wenn nicht ((0 <= r <= 255) und (0 <= g <= 255) und (0 <= b <= 255)):
            raise TurtleGraphicsError("bad color sequence: %s" % str(color))
        return "#%02x%02x%02x" % (r, g, b)

    def _color(self, cstr):
        wenn nicht cstr.startswith("#"):
            return cstr
        wenn len(cstr) == 7:
            cl = [int(cstr[i:i+2], 16) fuer i in (1, 3, 5)]
        sowenn len(cstr) == 4:
            cl = [16*int(cstr[h], 16) fuer h in cstr[1:]]
        sonst:
            raise TurtleGraphicsError("bad colorstring: %s" % cstr)
        return tuple(c * self._colormode/255 fuer c in cl)

    def colormode(self, cmode=Nichts):
        """Return the colormode oder set it to 1.0 oder 255.

        Optional argument:
        cmode -- one of the values 1.0 oder 255

        r, g, b values of colortriples have to be in range 0..cmode.

        Example (for a TurtleScreen instance named screen):
        >>> screen.colormode()
        1.0
        >>> screen.colormode(255)
        >>> pencolor(240,160,80)
        """
        wenn cmode is Nichts:
            return self._colormode
        wenn cmode == 1.0:
            self._colormode = float(cmode)
        sowenn cmode == 255:
            self._colormode = int(cmode)

    def reset(self):
        """Reset all Turtles on the Screen to their initial state.

        No argument.

        Example (for a TurtleScreen instance named screen):
        >>> screen.reset()
        """
        fuer turtle in self._turtles:
            turtle._setmode(self._mode)
            turtle.reset()

    def turtles(self):
        """Return the list of turtles on the screen.

        Example (for a TurtleScreen instance named screen):
        >>> screen.turtles()
        [<turtle.Turtle object at 0x00E11FB0>]
        """
        return self._turtles

    def bgcolor(self, *args):
        """Set oder return backgroundcolor of the TurtleScreen.

        Arguments (if given): a color string oder three numbers
        in the range 0..colormode oder a 3-tuple of such numbers.

        Example (for a TurtleScreen instance named screen):
        >>> screen.bgcolor("orange")
        >>> screen.bgcolor()
        'orange'
        >>> screen.bgcolor(0.5,0,0.5)
        >>> screen.bgcolor()
        '#800080'
        """
        wenn args:
            color = self._colorstr(args)
        sonst:
            color = Nichts
        color = self._bgcolor(color)
        wenn color is nicht Nichts:
            color = self._color(color)
        return color

    def tracer(self, n=Nichts, delay=Nichts):
        """Turns turtle animation on/off und set delay fuer update drawings.

        Optional arguments:
        n -- nonnegative  integer
        delay -- nonnegative  integer

        If n is given, only each n-th regular screen update is really performed.
        (Can be used to accelerate the drawing of complex graphics.)
        Second arguments sets delay value (see RawTurtle.delay())

        Example (for a TurtleScreen instance named screen):
        >>> screen.tracer(8, 25)
        >>> dist = 2
        >>> fuer i in range(200):
        ...     fd(dist)
        ...     rt(90)
        ...     dist += 2
        """
        wenn n is Nichts:
            return self._tracing
        self._tracing = int(n)
        self._updatecounter = 0
        wenn delay is nicht Nichts:
            self._delayvalue = int(delay)
        wenn self._tracing:
            self.update()

    def delay(self, delay=Nichts):
        """ Return oder set the drawing delay in milliseconds.

        Optional argument:
        delay -- positive integer

        Example (for a TurtleScreen instance named screen):
        >>> screen.delay(15)
        >>> screen.delay()
        15
        """
        wenn delay is Nichts:
            return self._delayvalue
        self._delayvalue = int(delay)

    @contextmanager
    def no_animation(self):
        """Temporarily turn off auto-updating the screen.

        This is useful fuer drawing complex shapes where even the fastest setting
        is too slow. Once this context manager is exited, the drawing will
        be displayed.

        Example (for a TurtleScreen instance named screen
        und a Turtle instance named turtle):
        >>> mit screen.no_animation():
        ...    turtle.circle(50)
        """
        tracer = self.tracer()
        try:
            self.tracer(0)
            yield
        finally:
            self.tracer(tracer)

    def _incrementudc(self):
        """Increment update counter."""
        wenn nicht TurtleScreen._RUNNING:
            TurtleScreen._RUNNING = Wahr
            raise Terminator
        wenn self._tracing > 0:
            self._updatecounter += 1
            self._updatecounter %= self._tracing

    def update(self):
        """Perform a TurtleScreen update.
        """
        tracing = self._tracing
        self._tracing = Wahr
        fuer t in self.turtles():
            t._update_data()
            t._drawturtle()
        self._tracing = tracing
        self._update()

    def window_width(self):
        """ Return the width of the turtle window.

        Example (for a TurtleScreen instance named screen):
        >>> screen.window_width()
        640
        """
        return self._window_size()[0]

    def window_height(self):
        """ Return the height of the turtle window.

        Example (for a TurtleScreen instance named screen):
        >>> screen.window_height()
        480
        """
        return self._window_size()[1]

    def getcanvas(self):
        """Return the Canvas of this TurtleScreen.

        No argument.

        Example (for a Screen instance named screen):
        >>> cv = screen.getcanvas()
        >>> cv
        <turtle.ScrolledCanvas instance at 0x010742D8>
        """
        return self.cv

    def getshapes(self):
        """Return a list of names of all currently available turtle shapes.

        No argument.

        Example (for a TurtleScreen instance named screen):
        >>> screen.getshapes()
        ['arrow', 'blank', 'circle', ... , 'turtle']
        """
        return sorted(self._shapes.keys())

    def onclick(self, fun, btn=1, add=Nichts):
        """Bind fun to mouse-click event on canvas.

        Arguments:
        fun -- a function mit two arguments, the coordinates of the
               clicked point on the canvas.
        btn -- the number of the mouse-button, defaults to 1

        Example (for a TurtleScreen instance named screen)

        >>> screen.onclick(goto)
        >>> # Subsequently clicking into the TurtleScreen will
        >>> # make the turtle move to the clicked point.
        >>> screen.onclick(Nichts)
        """
        self._onscreenclick(fun, btn, add)

    def onkey(self, fun, key):
        """Bind fun to key-release event of key.

        Arguments:
        fun -- a function mit no arguments
        key -- a string: key (e.g. "a") oder key-symbol (e.g. "space")

        In order to be able to register key-events, TurtleScreen
        must have focus. (See method listen.)

        Example (for a TurtleScreen instance named screen):

        >>> def f():
        ...     fd(50)
        ...     lt(60)
        ...
        >>> screen.onkey(f, "Up")
        >>> screen.listen()

        Subsequently the turtle can be moved by repeatedly pressing
        the up-arrow key, consequently drawing a hexagon

        """
        wenn fun is Nichts:
            wenn key in self._keys:
                self._keys.remove(key)
        sowenn key nicht in self._keys:
            self._keys.append(key)
        self._onkeyrelease(fun, key)

    def onkeypress(self, fun, key=Nichts):
        """Bind fun to key-press event of key wenn key is given,
        oder to any key-press-event wenn no key is given.

        Arguments:
        fun -- a function mit no arguments
        key -- a string: key (e.g. "a") oder key-symbol (e.g. "space")

        In order to be able to register key-events, TurtleScreen
        must have focus. (See method listen.)

        Example (for a TurtleScreen instance named screen
        und a Turtle instance named turtle):

        >>> def f():
        ...     fd(50)
        ...     lt(60)
        ...
        >>> screen.onkeypress(f, "Up")
        >>> screen.listen()

        Subsequently the turtle can be moved by repeatedly pressing
        the up-arrow key, oder by keeping pressed the up-arrow key.
        consequently drawing a hexagon.
        """
        wenn fun is Nichts:
            wenn key in self._keys:
                self._keys.remove(key)
        sowenn key is nicht Nichts und key nicht in self._keys:
            self._keys.append(key)
        self._onkeypress(fun, key)

    def listen(self, xdummy=Nichts, ydummy=Nichts):
        """Set focus on TurtleScreen (in order to collect key-events)

        No arguments.
        Dummy arguments are provided in order
        to be able to pass listen to the onclick method.

        Example (for a TurtleScreen instance named screen):
        >>> screen.listen()
        """
        self._listen()

    def ontimer(self, fun, t=0):
        """Install a timer, which calls fun after t milliseconds.

        Arguments:
        fun -- a function mit no arguments.
        t -- a number >= 0

        Example (for a TurtleScreen instance named screen):

        >>> running = Wahr
        >>> def f():
        ...     wenn running:
        ...             fd(50)
        ...             lt(60)
        ...             screen.ontimer(f, 250)
        ...
        >>> f()   # makes the turtle marching around
        >>> running = Falsch
        """
        self._ontimer(fun, t)

    def bgpic(self, picname=Nichts):
        """Set background image oder return name of current backgroundimage.

        Optional argument:
        picname -- a string, name of an image file (PNG, GIF, PGM, und PPM) oder "nopic".

        If picname is a filename, set the corresponding image als background.
        If picname is "nopic", delete backgroundimage, wenn present.
        If picname is Nichts, return the filename of the current backgroundimage.

        Example (for a TurtleScreen instance named screen):
        >>> screen.bgpic()
        'nopic'
        >>> screen.bgpic("landscape.gif")
        >>> screen.bgpic()
        'landscape.gif'
        """
        wenn picname is Nichts:
            return self._bgpicname
        wenn picname nicht in self._bgpics:
            self._bgpics[picname] = self._image(picname)
        self._setbgpic(self._bgpic, self._bgpics[picname])
        self._bgpicname = picname

    def screensize(self, canvwidth=Nichts, canvheight=Nichts, bg=Nichts):
        """Resize the canvas the turtles are drawing on.

        Optional arguments:
        canvwidth -- positive integer, new width of canvas in pixels
        canvheight --  positive integer, new height of canvas in pixels
        bg -- colorstring oder color-tuple, new backgroundcolor
        If no arguments are given, return current (canvaswidth, canvasheight)

        Do nicht alter the drawing window. To observe hidden parts of
        the canvas use the scrollbars. (Can make visible those parts
        of a drawing, which were outside the canvas before!)

        Example (for a Turtle instance named turtle):
        >>> turtle.screensize(2000,1500)
        >>> # e.g. to search fuer an erroneously escaped turtle ;-)
        """
        return self._resize(canvwidth, canvheight, bg)

    def save(self, filename, *, overwrite=Falsch):
        """Save the drawing als a PostScript file

        Arguments:
        filename -- a string, the path of the created file.
                    Must end mit '.ps' oder '.eps'.

        Optional arguments:
        overwrite -- boolean, wenn true, then existing files will be overwritten

        Example (for a TurtleScreen instance named screen):
        >>> screen.save('my_drawing.eps')
        """
        filename = Path(filename)
        wenn nicht filename.parent.exists():
            raise FileNotFoundError(
                f"The directory '{filename.parent}' does nicht exist."
                " Cannot save to it."
            )
        wenn nicht overwrite und filename.exists():
            raise FileExistsError(
                f"The file '{filename}' already exists. To overwrite it use"
                " the 'overwrite=Wahr' argument of the save function."
            )
        wenn (ext := filename.suffix) nicht in {".ps", ".eps"}:
            raise ValueError(
                f"Unknown file extension: '{ext}',"
                 " must be one of {'.ps', '.eps'}"
            )

        postscript = self.cv.postscript()
        filename.write_text(postscript)

    onscreenclick = onclick
    resetscreen = reset
    clearscreen = clear
    addshape = register_shape
    onkeyrelease = onkey

klasse TNavigator(object):
    """Navigation part of the RawTurtle.
    Implements methods fuer turtle movement.
    """
    START_ORIENTATION = {
        "standard": Vec2D(1.0, 0.0),
        "world"   : Vec2D(1.0, 0.0),
        "logo"    : Vec2D(0.0, 1.0)  }
    DEFAULT_MODE = "standard"
    DEFAULT_ANGLEOFFSET = 0
    DEFAULT_ANGLEORIENT = 1

    def __init__(self, mode=DEFAULT_MODE):
        self._angleOffset = self.DEFAULT_ANGLEOFFSET
        self._angleOrient = self.DEFAULT_ANGLEORIENT
        self._mode = mode
        self.undobuffer = Nichts
        self.degrees()
        self._mode = Nichts
        self._setmode(mode)
        TNavigator.reset(self)

    def reset(self):
        """reset turtle to its initial values

        Will be overwritten by parent class
        """
        self._position = Vec2D(0.0, 0.0)
        self._orient =  TNavigator.START_ORIENTATION[self._mode]

    def _setmode(self, mode=Nichts):
        """Set turtle-mode to 'standard', 'world' oder 'logo'.
        """
        wenn mode is Nichts:
            return self._mode
        wenn mode nicht in ["standard", "logo", "world"]:
            return
        self._mode = mode
        wenn mode in ["standard", "world"]:
            self._angleOffset = 0
            self._angleOrient = 1
        sonst: # mode == "logo":
            self._angleOffset = self._fullcircle/4.
            self._angleOrient = -1

    def _setDegreesPerAU(self, fullcircle):
        """Helper function fuer degrees() und radians()"""
        self._fullcircle = fullcircle
        self._degreesPerAU = 360/fullcircle
        wenn self._mode == "standard":
            self._angleOffset = 0
        sonst:
            self._angleOffset = fullcircle/4.

    def degrees(self, fullcircle=360.0):
        """ Set angle measurement units to degrees.

        Optional argument:
        fullcircle -  a number

        Set angle measurement units, i. e. set number
        of 'degrees' fuer a full circle. Default value is
        360 degrees.

        Example (for a Turtle instance named turtle):
        >>> turtle.left(90)
        >>> turtle.heading()
        90

        Change angle measurement unit to grad (also known als gon,
        grade, oder gradian und equals 1/100-th of the right angle.)
        >>> turtle.degrees(400.0)
        >>> turtle.heading()
        100

        """
        self._setDegreesPerAU(fullcircle)

    def radians(self):
        """ Set the angle measurement units to radians.

        No arguments.

        Example (for a Turtle instance named turtle):
        >>> turtle.heading()
        90
        >>> turtle.radians()
        >>> turtle.heading()
        1.5707963267948966
        """
        self._setDegreesPerAU(math.tau)

    def _go(self, distance):
        """move turtle forward by specified distance"""
        ende = self._position + self._orient * distance
        self._goto(ende)

    def _rotate(self, angle):
        """Turn turtle counterclockwise by specified angle wenn angle > 0."""
        angle *= self._degreesPerAU
        self._orient = self._orient.rotate(angle)

    def _goto(self, end):
        """move turtle to position end."""
        self._position = end

    def teleport(self, x=Nichts, y=Nichts, *, fill_gap: bool = Falsch) -> Nichts:
        """To be overwritten by child klasse RawTurtle.
        Includes no TPen references."""
        new_x = x wenn x is nicht Nichts sonst self._position[0]
        new_y = y wenn y is nicht Nichts sonst self._position[1]
        self._position = Vec2D(new_x, new_y)

    def forward(self, distance):
        """Move the turtle forward by the specified distance.

        Aliases: forward | fd

        Argument:
        distance -- a number (integer oder float)

        Move the turtle forward by the specified distance, in the direction
        the turtle is headed.

        Example (for a Turtle instance named turtle):
        >>> turtle.position()
        (0.00, 0.00)
        >>> turtle.forward(25)
        >>> turtle.position()
        (25.00,0.00)
        >>> turtle.forward(-75)
        >>> turtle.position()
        (-50.00,0.00)
        """
        self._go(distance)

    def back(self, distance):
        """Move the turtle backward by distance.

        Aliases: back | backward | bk

        Argument:
        distance -- a number

        Move the turtle backward by distance, opposite to the direction the
        turtle is headed. Do nicht change the turtle's heading.

        Example (for a Turtle instance named turtle):
        >>> turtle.position()
        (0.00, 0.00)
        >>> turtle.backward(30)
        >>> turtle.position()
        (-30.00, 0.00)
        """
        self._go(-distance)

    def right(self, angle):
        """Turn turtle right by angle units.

        Aliases: right | rt

        Argument:
        angle -- a number (integer oder float)

        Turn turtle right by angle units. (Units are by default degrees,
        but can be set via the degrees() und radians() functions.)
        Angle orientation depends on mode. (See this.)

        Example (for a Turtle instance named turtle):
        >>> turtle.heading()
        22.0
        >>> turtle.right(45)
        >>> turtle.heading()
        337.0
        """
        self._rotate(-angle)

    def left(self, angle):
        """Turn turtle left by angle units.

        Aliases: left | lt

        Argument:
        angle -- a number (integer oder float)

        Turn turtle left by angle units. (Units are by default degrees,
        but can be set via the degrees() und radians() functions.)
        Angle orientation depends on mode. (See this.)

        Example (for a Turtle instance named turtle):
        >>> turtle.heading()
        22.0
        >>> turtle.left(45)
        >>> turtle.heading()
        67.0
        """
        self._rotate(angle)

    def pos(self):
        """Return the turtle's current location (x,y), als a Vec2D-vector.

        Aliases: pos | position

        No arguments.

        Example (for a Turtle instance named turtle):
        >>> turtle.pos()
        (0.00, 240.00)
        """
        return self._position

    def xcor(self):
        """ Return the turtle's x coordinate.

        No arguments.

        Example (for a Turtle instance named turtle):
        >>> reset()
        >>> turtle.left(60)
        >>> turtle.forward(100)
        >>> drucke(turtle.xcor())
        50.0
        """
        return self._position[0]

    def ycor(self):
        """ Return the turtle's y coordinate
        ---
        No arguments.

        Example (for a Turtle instance named turtle):
        >>> reset()
        >>> turtle.left(60)
        >>> turtle.forward(100)
        >>> drucke(turtle.ycor())
        86.6025403784
        """
        return self._position[1]


    def goto(self, x, y=Nichts):
        """Move turtle to an absolute position.

        Aliases: setpos | setposition | goto:

        Arguments:
        x -- a number      oder     a pair/vector of numbers
        y -- a number             Nichts

        call: goto(x, y)         # two coordinates
        --or: goto((x, y))       # a pair (tuple) of coordinates
        --or: goto(vec)          # e.g. als returned by pos()

        Move turtle to an absolute position. If the pen is down,
        a line will be drawn. The turtle's orientation does nicht change.

        Example (for a Turtle instance named turtle):
        >>> tp = turtle.pos()
        >>> tp
        (0.00, 0.00)
        >>> turtle.setpos(60,30)
        >>> turtle.pos()
        (60.00,30.00)
        >>> turtle.setpos((20,80))
        >>> turtle.pos()
        (20.00,80.00)
        >>> turtle.setpos(tp)
        >>> turtle.pos()
        (0.00,0.00)
        """
        wenn y is Nichts:
            self._goto(Vec2D(*x))
        sonst:
            self._goto(Vec2D(x, y))

    def home(self):
        """Move turtle to the origin - coordinates (0,0).

        No arguments.

        Move turtle to the origin - coordinates (0,0) und set its
        heading to its start-orientation (which depends on mode).

        Example (for a Turtle instance named turtle):
        >>> turtle.home()
        """
        self.goto(0, 0)
        self.setheading(0)

    def setx(self, x):
        """Set the turtle's first coordinate to x

        Argument:
        x -- a number (integer oder float)

        Set the turtle's first coordinate to x, leave second coordinate
        unchanged.

        Example (for a Turtle instance named turtle):
        >>> turtle.position()
        (0.00, 240.00)
        >>> turtle.setx(10)
        >>> turtle.position()
        (10.00, 240.00)
        """
        self._goto(Vec2D(x, self._position[1]))

    def sety(self, y):
        """Set the turtle's second coordinate to y

        Argument:
        y -- a number (integer oder float)

        Set the turtle's first coordinate to x, second coordinate remains
        unchanged.

        Example (for a Turtle instance named turtle):
        >>> turtle.position()
        (0.00, 40.00)
        >>> turtle.sety(-10)
        >>> turtle.position()
        (0.00, -10.00)
        """
        self._goto(Vec2D(self._position[0], y))

    def distance(self, x, y=Nichts):
        """Return the distance von the turtle to (x,y) in turtle step units.

        Arguments:
        x -- a number   oder  a pair/vector of numbers   oder   a turtle instance
        y -- a number       Nichts                            Nichts

        call: distance(x, y)         # two coordinates
        --or: distance((x, y))       # a pair (tuple) of coordinates
        --or: distance(vec)          # e.g. als returned by pos()
        --or: distance(mypen)        # where mypen is another turtle

        Example (for a Turtle instance named turtle):
        >>> turtle.pos()
        (0.00, 0.00)
        >>> turtle.distance(30,40)
        50.0
        >>> pen = Turtle()
        >>> pen.forward(77)
        >>> turtle.distance(pen)
        77.0
        """
        wenn y is nicht Nichts:
            pos = Vec2D(x, y)
        wenn isinstance(x, Vec2D):
            pos = x
        sowenn isinstance(x, tuple):
            pos = Vec2D(*x)
        sowenn isinstance(x, TNavigator):
            pos = x._position
        return abs(pos - self._position)

    def towards(self, x, y=Nichts):
        """Return the angle of the line von the turtle's position to (x, y).

        Arguments:
        x -- a number   oder  a pair/vector of numbers   oder   a turtle instance
        y -- a number       Nichts                            Nichts

        call: distance(x, y)         # two coordinates
        --or: distance((x, y))       # a pair (tuple) of coordinates
        --or: distance(vec)          # e.g. als returned by pos()
        --or: distance(mypen)        # where mypen is another turtle

        Return the angle, between the line von turtle-position to position
        specified by x, y und the turtle's start orientation. (Depends on
        modes - "standard" oder "logo")

        Example (for a Turtle instance named turtle):
        >>> turtle.pos()
        (10.00, 10.00)
        >>> turtle.towards(0,0)
        225.0
        """
        wenn y is nicht Nichts:
            pos = Vec2D(x, y)
        wenn isinstance(x, Vec2D):
            pos = x
        sowenn isinstance(x, tuple):
            pos = Vec2D(*x)
        sowenn isinstance(x, TNavigator):
            pos = x._position
        x, y = pos - self._position
        result = round(math.degrees(math.atan2(y, x)), 10) % 360.0
        result /= self._degreesPerAU
        return (self._angleOffset + self._angleOrient*result) % self._fullcircle

    def heading(self):
        """ Return the turtle's current heading.

        No arguments.

        Example (for a Turtle instance named turtle):
        >>> turtle.left(67)
        >>> turtle.heading()
        67.0
        """
        x, y = self._orient
        result = round(math.degrees(math.atan2(y, x)), 10) % 360.0
        result /= self._degreesPerAU
        return (self._angleOffset + self._angleOrient*result) % self._fullcircle

    def setheading(self, to_angle):
        """Set the orientation of the turtle to to_angle.

        Aliases:  setheading | seth

        Argument:
        to_angle -- a number (integer oder float)

        Set the orientation of the turtle to to_angle.
        Here are some common directions in degrees:

         standard - mode:          logo-mode:
        -------------------|--------------------
           0 - east                0 - north
          90 - north              90 - east
         180 - west              180 - south
         270 - south             270 - west

        Example (for a Turtle instance named turtle):
        >>> turtle.setheading(90)
        >>> turtle.heading()
        90
        """
        angle = (to_angle - self.heading())*self._angleOrient
        full = self._fullcircle
        angle = (angle+full/2.)%full - full/2.
        self._rotate(angle)

    def circle(self, radius, extent = Nichts, steps = Nichts):
        """ Draw a circle mit given radius.

        Arguments:
        radius -- a number
        extent (optional) -- a number
        steps (optional) -- an integer

        Draw a circle mit given radius. The center is radius units left
        of the turtle; extent - an angle - determines which part of the
        circle is drawn. If extent is nicht given, draw the entire circle.
        If extent is nicht a full circle, one endpoint of the arc is the
        current pen position. Draw the arc in counterclockwise direction
        wenn radius is positive, otherwise in clockwise direction. Finally
        the direction of the turtle is changed by the amount of extent.

        As the circle is approximated by an inscribed regular polygon,
        steps determines the number of steps to use. If nicht given,
        it will be calculated automatically. Maybe used to draw regular
        polygons.

        call: circle(radius)                  # full circle
        --or: circle(radius, extent)          # arc
        --or: circle(radius, extent, steps)
        --or: circle(radius, steps=6)         # 6-sided polygon

        Example (for a Turtle instance named turtle):
        >>> turtle.circle(50)
        >>> turtle.circle(120, 180)  # semicircle
        """
        wenn self.undobuffer:
            self.undobuffer.push(["seq"])
            self.undobuffer.cumulate = Wahr
        speed = self.speed()
        wenn extent is Nichts:
            extent = self._fullcircle
        wenn steps is Nichts:
            frac = abs(extent)/self._fullcircle
            steps = 1+int(min(11+abs(radius)/6.0, 59.0)*frac)
        w = 1.0 * extent / steps
        w2 = 0.5 * w
        l = 2.0 * radius * math.sin(math.radians(w2)*self._degreesPerAU)
        wenn radius < 0:
            l, w, w2 = -l, -w, -w2
        tr = self._tracer()
        dl = self._delay()
        wenn speed == 0:
            self._tracer(0, 0)
        sonst:
            self.speed(0)
        self._rotate(w2)
        fuer i in range(steps):
            self.speed(speed)
            self._go(l)
            self.speed(0)
            self._rotate(w)
        self._rotate(-w2)
        wenn speed == 0:
            self._tracer(tr, dl)
        self.speed(speed)
        wenn self.undobuffer:
            self.undobuffer.cumulate = Falsch

## three dummy methods to be implemented by child class:

    def speed(self, s=0):
        """dummy method - to be overwritten by child class"""
    def _tracer(self, a=Nichts, b=Nichts):
        """dummy method - to be overwritten by child class"""
    def _delay(self, n=Nichts):
        """dummy method - to be overwritten by child class"""

    fd = forward
    bk = back
    backward = back
    rt = right
    lt = left
    position = pos
    setpos = goto
    setposition = goto
    seth = setheading


klasse TPen(object):
    """Drawing part of the RawTurtle.
    Implements drawing properties.
    """
    def __init__(self, resizemode=_CFG["resizemode"]):
        self._resizemode = resizemode # oder "user" oder "noresize"
        self.undobuffer = Nichts
        TPen._reset(self)

    def _reset(self, pencolor=_CFG["pencolor"],
                     fillcolor=_CFG["fillcolor"]):
        self._pensize = 1
        self._shown = Wahr
        self._pencolor = pencolor
        self._fillcolor = fillcolor
        self._drawing = Wahr
        self._speed = 3
        self._stretchfactor = (1., 1.)
        self._shearfactor = 0.
        self._tilt = 0.
        self._shapetrafo = (1., 0., 0., 1.)
        self._outlinewidth = 1

    def resizemode(self, rmode=Nichts):
        """Set resizemode to one of the values: "auto", "user", "noresize".

        (Optional) Argument:
        rmode -- one of the strings "auto", "user", "noresize"

        Different resizemodes have the following effects:
          - "auto" adapts the appearance of the turtle
                   corresponding to the value of pensize.
          - "user" adapts the appearance of the turtle according to the
                   values of stretchfactor und outlinewidth (outline),
                   which are set by shapesize()
          - "noresize" no adaption of the turtle's appearance takes place.
        If no argument is given, return current resizemode.
        resizemode("user") is called by a call of shapesize mit arguments.


        Examples (for a Turtle instance named turtle):
        >>> turtle.resizemode("noresize")
        >>> turtle.resizemode()
        'noresize'
        """
        wenn rmode is Nichts:
            return self._resizemode
        rmode = rmode.lower()
        wenn rmode in ["auto", "user", "noresize"]:
            self.pen(resizemode=rmode)

    def pensize(self, width=Nichts):
        """Set oder return the line thickness.

        Aliases:  pensize | width

        Argument:
        width -- positive number

        Set the line thickness to width oder return it. If resizemode is set
        to "auto" und turtleshape is a polygon, that polygon is drawn with
        the same line thickness. If no argument is given, current pensize
        is returned.

        Example (for a Turtle instance named turtle):
        >>> turtle.pensize()
        1
        >>> turtle.pensize(10)   # von here on lines of width 10 are drawn
        """
        wenn width is Nichts:
            return self._pensize
        self.pen(pensize=width)


    def penup(self):
        """Pull the pen up -- no drawing when moving.

        Aliases: penup | pu | up

        No argument

        Example (for a Turtle instance named turtle):
        >>> turtle.penup()
        """
        wenn nicht self._drawing:
            return
        self.pen(pendown=Falsch)

    def pendown(self):
        """Pull the pen down -- drawing when moving.

        Aliases: pendown | pd | down

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.pendown()
        """
        wenn self._drawing:
            return
        self.pen(pendown=Wahr)

    def isdown(self):
        """Return Wahr wenn pen is down, Falsch wenn it's up.

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.penup()
        >>> turtle.isdown()
        Falsch
        >>> turtle.pendown()
        >>> turtle.isdown()
        Wahr
        """
        return self._drawing

    def speed(self, speed=Nichts):
        """ Return oder set the turtle's speed.

        Optional argument:
        speed -- an integer in the range 0..10 oder a speedstring (see below)

        Set the turtle's speed to an integer value in the range 0 .. 10.
        If no argument is given: return current speed.

        If input is a number greater than 10 oder smaller than 0.5,
        speed is set to 0.
        Speedstrings  are mapped to speedvalues in the following way:
            'fastest' :  0
            'fast'    :  10
            'normal'  :  6
            'slow'    :  3
            'slowest' :  1
        speeds von 1 to 10 enforce increasingly faster animation of
        line drawing und turtle turning.

        Attention:
        speed = 0 : *no* animation takes place. forward/back makes turtle jump
        und likewise left/right make the turtle turn instantly.

        Example (for a Turtle instance named turtle):
        >>> turtle.speed(3)
        """
        speeds = {'fastest':0, 'fast':10, 'normal':6, 'slow':3, 'slowest':1 }
        wenn speed is Nichts:
            return self._speed
        wenn speed in speeds:
            speed = speeds[speed]
        sowenn 0.5 < speed < 10.5:
            speed = int(round(speed))
        sonst:
            speed = 0
        self.pen(speed=speed)

    def color(self, *args):
        """Return oder set the pencolor und fillcolor.

        Arguments:
        Several input formats are allowed.
        They use 0, 1, 2, oder 3 arguments als follows:

        color()
            Return the current pencolor und the current fillcolor
            als a pair of color specification strings als are returned
            by pencolor und fillcolor.
        color(colorstring), color((r,g,b)), color(r,g,b)
            inputs als in pencolor, set both, fillcolor und pencolor,
            to the given value.
        color(colorstring1, colorstring2),
        color((r1,g1,b1), (r2,g2,b2))
            equivalent to pencolor(colorstring1) und fillcolor(colorstring2)
            und analogously, wenn the other input format is used.

        If turtleshape is a polygon, outline und interior of that polygon
        is drawn mit the newly set colors.
        For more info see: pencolor, fillcolor

        Example (for a Turtle instance named turtle):
        >>> turtle.color('red', 'green')
        >>> turtle.color()
        ('red', 'green')
        >>> colormode(255)
        >>> color((40, 80, 120), (160, 200, 240))
        >>> color()
        ('#285078', '#a0c8f0')
        """
        wenn args:
            l = len(args)
            wenn l == 1:
                pcolor = fcolor = args[0]
            sowenn l == 2:
                pcolor, fcolor = args
            sowenn l == 3:
                pcolor = fcolor = args
            pcolor = self._colorstr(pcolor)
            fcolor = self._colorstr(fcolor)
            self.pen(pencolor=pcolor, fillcolor=fcolor)
        sonst:
            return self._color(self._pencolor), self._color(self._fillcolor)

    def pencolor(self, *args):
        """ Return oder set the pencolor.

        Arguments:
        Four input formats are allowed:
          - pencolor()
            Return the current pencolor als color specification string,
            possibly in hex-number format (see example).
            May be used als input to another color/pencolor/fillcolor call.
          - pencolor(colorstring)
            s is a Tk color specification string, such als "red" oder "yellow"
          - pencolor((r, g, b))
            *a tuple* of r, g, und b, which represent, an RGB color,
            und each of r, g, und b are in the range 0..colormode,
            where colormode is either 1.0 oder 255
          - pencolor(r, g, b)
            r, g, und b represent an RGB color, und each of r, g, und b
            are in the range 0..colormode

        If turtleshape is a polygon, the outline of that polygon is drawn
        mit the newly set pencolor.

        Example (for a Turtle instance named turtle):
        >>> turtle.pencolor('brown')
        >>> tup = (0.2, 0.8, 0.55)
        >>> turtle.pencolor(tup)
        >>> turtle.pencolor()
        '#33cc8c'
        """
        wenn args:
            color = self._colorstr(args)
            wenn color == self._pencolor:
                return
            self.pen(pencolor=color)
        sonst:
            return self._color(self._pencolor)

    def fillcolor(self, *args):
        """ Return oder set the fillcolor.

        Arguments:
        Four input formats are allowed:
          - fillcolor()
            Return the current fillcolor als color specification string,
            possibly in hex-number format (see example).
            May be used als input to another color/pencolor/fillcolor call.
          - fillcolor(colorstring)
            s is a Tk color specification string, such als "red" oder "yellow"
          - fillcolor((r, g, b))
            *a tuple* of r, g, und b, which represent, an RGB color,
            und each of r, g, und b are in the range 0..colormode,
            where colormode is either 1.0 oder 255
          - fillcolor(r, g, b)
            r, g, und b represent an RGB color, und each of r, g, und b
            are in the range 0..colormode

        If turtleshape is a polygon, the interior of that polygon is drawn
        mit the newly set fillcolor.

        Example (for a Turtle instance named turtle):
        >>> turtle.fillcolor('violet')
        >>> col = turtle.pencolor()
        >>> turtle.fillcolor(col)
        >>> turtle.fillcolor(0, .5, 0)
        """
        wenn args:
            color = self._colorstr(args)
            wenn color == self._fillcolor:
                return
            self.pen(fillcolor=color)
        sonst:
            return self._color(self._fillcolor)

    def teleport(self, x=Nichts, y=Nichts, *, fill_gap: bool = Falsch) -> Nichts:
        """To be overwritten by child klasse RawTurtle.
        Includes no TNavigator references.
        """
        pendown = self.isdown()
        wenn pendown:
            self.pen(pendown=Falsch)
        self.pen(pendown=pendown)

    def showturtle(self):
        """Makes the turtle visible.

        Aliases: showturtle | st

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.hideturtle()
        >>> turtle.showturtle()
        """
        self.pen(shown=Wahr)

    def hideturtle(self):
        """Makes the turtle invisible.

        Aliases: hideturtle | ht

        No argument.

        It's a good idea to do this waehrend you're in the
        middle of a complicated drawing, because hiding
        the turtle speeds up the drawing observably.

        Example (for a Turtle instance named turtle):
        >>> turtle.hideturtle()
        """
        self.pen(shown=Falsch)

    def isvisible(self):
        """Return Wahr wenn the Turtle is shown, Falsch wenn it's hidden.

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.hideturtle()
        >>> drucke(turtle.isvisible())
        Falsch
        """
        return self._shown

    def pen(self, pen=Nichts, **pendict):
        """Return oder set the pen's attributes.

        Arguments:
            pen -- a dictionary mit some oder all of the below listed keys.
            **pendict -- one oder more keyword-arguments mit the below
                         listed keys als keywords.

        Return oder set the pen's attributes in a 'pen-dictionary'
        mit the following key/value pairs:
           "shown"      :   Wahr/Falsch
           "pendown"    :   Wahr/Falsch
           "pencolor"   :   color-string oder color-tuple
           "fillcolor"  :   color-string oder color-tuple
           "pensize"    :   positive number
           "speed"      :   number in range 0..10
           "resizemode" :   "auto" oder "user" oder "noresize"
           "stretchfactor": (positive number, positive number)
           "shearfactor":   number
           "outline"    :   positive number
           "tilt"       :   number

        This dictionary can be used als argument fuer a subsequent
        pen()-call to restore the former pen-state. Moreover one
        oder more of these attributes can be provided als keyword-arguments.
        This can be used to set several pen attributes in one statement.


        Examples (for a Turtle instance named turtle):
        >>> turtle.pen(fillcolor="black", pencolor="red", pensize=10)
        >>> turtle.pen()
        {'pensize': 10, 'shown': Wahr, 'resizemode': 'auto', 'outline': 1,
        'pencolor': 'red', 'pendown': Wahr, 'fillcolor': 'black',
        'stretchfactor': (1,1), 'speed': 3, 'shearfactor': 0.0}
        >>> penstate=turtle.pen()
        >>> turtle.color("yellow","")
        >>> turtle.penup()
        >>> turtle.pen()
        {'pensize': 10, 'shown': Wahr, 'resizemode': 'auto', 'outline': 1,
        'pencolor': 'yellow', 'pendown': Falsch, 'fillcolor': '',
        'stretchfactor': (1,1), 'speed': 3, 'shearfactor': 0.0}
        >>> p.pen(penstate, fillcolor="green")
        >>> p.pen()
        {'pensize': 10, 'shown': Wahr, 'resizemode': 'auto', 'outline': 1,
        'pencolor': 'red', 'pendown': Wahr, 'fillcolor': 'green',
        'stretchfactor': (1,1), 'speed': 3, 'shearfactor': 0.0}
        """
        _pd =  {"shown"         : self._shown,
                "pendown"       : self._drawing,
                "pencolor"      : self._pencolor,
                "fillcolor"     : self._fillcolor,
                "pensize"       : self._pensize,
                "speed"         : self._speed,
                "resizemode"    : self._resizemode,
                "stretchfactor" : self._stretchfactor,
                "shearfactor"   : self._shearfactor,
                "outline"       : self._outlinewidth,
                "tilt"          : self._tilt
               }

        wenn nicht (pen oder pendict):
            return _pd

        wenn isinstance(pen, dict):
            p = pen
        sonst:
            p = {}
        p.update(pendict)

        _p_buf = {}
        fuer key in p:
            _p_buf[key] = _pd[key]

        wenn self.undobuffer:
            self.undobuffer.push(("pen", _p_buf))

        newLine = Falsch
        wenn "pendown" in p:
            wenn self._drawing != p["pendown"]:
                newLine = Wahr
        wenn "pencolor" in p:
            wenn isinstance(p["pencolor"], tuple):
                p["pencolor"] = self._colorstr((p["pencolor"],))
            wenn self._pencolor != p["pencolor"]:
                newLine = Wahr
        wenn "pensize" in p:
            wenn self._pensize != p["pensize"]:
                newLine = Wahr
        wenn newLine:
            self._newLine()
        wenn "pendown" in p:
            self._drawing = p["pendown"]
        wenn "pencolor" in p:
            self._pencolor = p["pencolor"]
        wenn "pensize" in p:
            self._pensize = p["pensize"]
        wenn "fillcolor" in p:
            wenn isinstance(p["fillcolor"], tuple):
                p["fillcolor"] = self._colorstr((p["fillcolor"],))
            self._fillcolor = p["fillcolor"]
        wenn "speed" in p:
            self._speed = p["speed"]
        wenn "resizemode" in p:
            self._resizemode = p["resizemode"]
        wenn "stretchfactor" in p:
            sf = p["stretchfactor"]
            wenn isinstance(sf, (int, float)):
                sf = (sf, sf)
            self._stretchfactor = sf
        wenn "shearfactor" in p:
            self._shearfactor = p["shearfactor"]
        wenn "outline" in p:
            self._outlinewidth = p["outline"]
        wenn "shown" in p:
            self._shown = p["shown"]
        wenn "tilt" in p:
            self._tilt = p["tilt"]
        wenn "stretchfactor" in p oder "tilt" in p oder "shearfactor" in p:
            scx, scy = self._stretchfactor
            shf = self._shearfactor
            sa, ca = math.sin(self._tilt), math.cos(self._tilt)
            self._shapetrafo = ( scx*ca, scy*(shf*ca + sa),
                                -scx*sa, scy*(ca - shf*sa))
        self._update()

## three dummy methods to be implemented by child class:

    def _newLine(self, usePos = Wahr):
        """dummy method - to be overwritten by child class"""
    def _update(self, count=Wahr, forced=Falsch):
        """dummy method - to be overwritten by child class"""
    def _color(self, args):
        """dummy method - to be overwritten by child class"""
    def _colorstr(self, args):
        """dummy method - to be overwritten by child class"""

    width = pensize
    up = penup
    pu = penup
    pd = pendown
    down = pendown
    st = showturtle
    ht = hideturtle


klasse _TurtleImage(object):
    """Helper class: Datatype to store Turtle attributes
    """

    def __init__(self, screen, shapeIndex):
        self.screen = screen
        self._type = Nichts
        self._setshape(shapeIndex)

    def _setshape(self, shapeIndex):
        screen = self.screen
        self.shapeIndex = shapeIndex
        wenn self._type == "polygon" == screen._shapes[shapeIndex]._type:
            return
        wenn self._type == "image" == screen._shapes[shapeIndex]._type:
            return
        wenn self._type in ["image", "polygon"]:
            screen._delete(self._item)
        sowenn self._type == "compound":
            fuer item in self._item:
                screen._delete(item)
        self._type = screen._shapes[shapeIndex]._type
        wenn self._type == "polygon":
            self._item = screen._createpoly()
        sowenn self._type == "image":
            self._item = screen._createimage(screen._shapes["blank"]._data)
        sowenn self._type == "compound":
            self._item = [screen._createpoly() fuer item in
                                          screen._shapes[shapeIndex]._data]


klasse RawTurtle(TPen, TNavigator):
    """Animation part of the RawTurtle.
    Puts RawTurtle upon a TurtleScreen und provides tools for
    its animation.
    """
    screens = []

    def __init__(self, canvas=Nichts,
                 shape=_CFG["shape"],
                 undobuffersize=_CFG["undobuffersize"],
                 visible=_CFG["visible"]):
        wenn isinstance(canvas, _Screen):
            self.screen = canvas
        sowenn isinstance(canvas, TurtleScreen):
            wenn canvas nicht in RawTurtle.screens:
                RawTurtle.screens.append(canvas)
            self.screen = canvas
        sowenn isinstance(canvas, (ScrolledCanvas, Canvas)):
            fuer screen in RawTurtle.screens:
                wenn screen.cv == canvas:
                    self.screen = screen
                    breche
            sonst:
                self.screen = TurtleScreen(canvas)
                RawTurtle.screens.append(self.screen)
        sonst:
            raise TurtleGraphicsError("bad canvas argument %s" % canvas)

        screen = self.screen
        TNavigator.__init__(self, screen.mode())
        TPen.__init__(self)
        screen._turtles.append(self)
        self.drawingLineItem = screen._createline()
        self.turtle = _TurtleImage(screen, shape)
        self._poly = Nichts
        self._creatingPoly = Falsch
        self._fillitem = self._fillpath = Nichts
        self._shown = visible
        self._hidden_from_screen = Falsch
        self.currentLineItem = screen._createline()
        self.currentLine = [self._position]
        self.items = [self.currentLineItem]
        self.stampItems = []
        self._undobuffersize = undobuffersize
        self.undobuffer = Tbuffer(undobuffersize)
        self._update()

    def reset(self):
        """Delete the turtle's drawings und restore its default values.

        No argument.

        Delete the turtle's drawings von the screen, re-center the turtle
        und set variables to the default values.

        Example (for a Turtle instance named turtle):
        >>> turtle.position()
        (0.00,-22.00)
        >>> turtle.heading()
        100.0
        >>> turtle.reset()
        >>> turtle.position()
        (0.00,0.00)
        >>> turtle.heading()
        0.0
        """
        TNavigator.reset(self)
        TPen._reset(self)
        self._clear()
        self._drawturtle()
        self._update()

    def setundobuffer(self, size):
        """Set oder disable undobuffer.

        Argument:
        size -- an integer oder Nichts

        If size is an integer an empty undobuffer of given size is installed.
        Size gives the maximum number of turtle-actions that can be undone
        by the undo() function.
        If size is Nichts, no undobuffer is present.

        Example (for a Turtle instance named turtle):
        >>> turtle.setundobuffer(42)
        """
        wenn size is Nichts oder size <= 0:
            self.undobuffer = Nichts
        sonst:
            self.undobuffer = Tbuffer(size)

    def undobufferentries(self):
        """Return count of entries in the undobuffer.

        No argument.

        Example (for a Turtle instance named turtle):
        >>> waehrend undobufferentries():
        ...     undo()
        """
        wenn self.undobuffer is Nichts:
            return 0
        return self.undobuffer.nr_of_items()

    def _clear(self):
        """Delete all of pen's drawings"""
        self._fillitem = self._fillpath = Nichts
        fuer item in self.items:
            self.screen._delete(item)
        self.currentLineItem = self.screen._createline()
        self.currentLine = []
        wenn self._drawing:
            self.currentLine.append(self._position)
        self.items = [self.currentLineItem]
        self.clearstamps()
        self.setundobuffer(self._undobuffersize)


    def clear(self):
        """Delete the turtle's drawings von the screen. Do nicht move turtle.

        No arguments.

        Delete the turtle's drawings von the screen. Do nicht move turtle.
        State und position of the turtle als well als drawings of other
        turtles are nicht affected.

        Examples (for a Turtle instance named turtle):
        >>> turtle.clear()
        """
        self._clear()
        self._update()

    def _update_data(self):
        self.screen._incrementudc()
        wenn self.screen._updatecounter != 0:
            return
        wenn len(self.currentLine)>1:
            self.screen._drawline(self.currentLineItem, self.currentLine,
                                  self._pencolor, self._pensize)

    def _update(self):
        """Perform a Turtle-data update.
        """
        screen = self.screen
        wenn screen._tracing == 0:
            return
        sowenn screen._tracing == 1:
            self._update_data()
            self._drawturtle()
            screen._update()                  # TurtleScreenBase
            screen._delay(screen._delayvalue) # TurtleScreenBase
        sonst:
            self._update_data()
            wenn screen._updatecounter == 0:
                fuer t in screen.turtles():
                    t._drawturtle()
                screen._update()

    def _tracer(self, flag=Nichts, delay=Nichts):
        """Turns turtle animation on/off und set delay fuer update drawings.

        Optional arguments:
        n -- nonnegative  integer
        delay -- nonnegative  integer

        If n is given, only each n-th regular screen update is really performed.
        (Can be used to accelerate the drawing of complex graphics.)
        Second arguments sets delay value (see RawTurtle.delay())

        Example (for a Turtle instance named turtle):
        >>> turtle.tracer(8, 25)
        >>> dist = 2
        >>> fuer i in range(200):
        ...     turtle.fd(dist)
        ...     turtle.rt(90)
        ...     dist += 2
        """
        return self.screen.tracer(flag, delay)

    def _color(self, args):
        return self.screen._color(args)

    def _colorstr(self, args):
        return self.screen._colorstr(args)

    def _cc(self, args):
        """Convert colortriples to hexstrings.
        """
        wenn isinstance(args, str):
            return args
        try:
            r, g, b = args
        except (TypeError, ValueError):
            raise TurtleGraphicsError("bad color arguments: %s" % str(args))
        wenn self.screen._colormode == 1.0:
            r, g, b = [round(255.0*x) fuer x in (r, g, b)]
        wenn nicht ((0 <= r <= 255) und (0 <= g <= 255) und (0 <= b <= 255)):
            raise TurtleGraphicsError("bad color sequence: %s" % str(args))
        return "#%02x%02x%02x" % (r, g, b)

    def teleport(self, x=Nichts, y=Nichts, *, fill_gap: bool = Falsch) -> Nichts:
        """Instantly move turtle to an absolute position.

        Arguments:
        x -- a number      oder     Nichts
        y -- a number             Nichts
        fill_gap -- a boolean     This argument must be specified by name.

        call: teleport(x, y)         # two coordinates
        --or: teleport(x)            # teleport to x position, keeping y als is
        --or: teleport(y=y)          # teleport to y position, keeping x als is
        --or: teleport(x, y, fill_gap=Wahr)
                                     # teleport but fill the gap in between

        Move turtle to an absolute position. Unlike goto(x, y), a line will not
        be drawn. The turtle's orientation does nicht change. If currently
        filling, the polygon(s) teleported von will be filled after leaving,
        und filling will begin again after teleporting. This can be disabled
        mit fill_gap=Wahr, which makes the imaginary line traveled during
        teleporting act als a fill barrier like in goto(x, y).

        Example (for a Turtle instance named turtle):
        >>> tp = turtle.pos()
        >>> tp
        (0.00,0.00)
        >>> turtle.teleport(60)
        >>> turtle.pos()
        (60.00,0.00)
        >>> turtle.teleport(y=10)
        >>> turtle.pos()
        (60.00,10.00)
        >>> turtle.teleport(20, 30)
        >>> turtle.pos()
        (20.00,30.00)
        """
        pendown = self.isdown()
        was_filling = self.filling()
        wenn pendown:
            self.pen(pendown=Falsch)
        wenn was_filling und nicht fill_gap:
            self.end_fill()
        new_x = x wenn x is nicht Nichts sonst self._position[0]
        new_y = y wenn y is nicht Nichts sonst self._position[1]
        self._position = Vec2D(new_x, new_y)
        self.pen(pendown=pendown)
        wenn was_filling und nicht fill_gap:
            self.begin_fill()

    def clone(self):
        """Create und return a clone of the turtle.

        No argument.

        Create und return a clone of the turtle mit same position, heading
        und turtle properties.

        Example (for a Turtle instance named mick):
        mick = Turtle()
        joe = mick.clone()
        """
        screen = self.screen
        self._newLine(self._drawing)

        turtle = self.turtle
        self.screen = Nichts
        self.turtle = Nichts  # too make self deepcopy-able

        q = deepcopy(self)

        self.screen = screen
        self.turtle = turtle

        q.screen = screen
        q.turtle = _TurtleImage(screen, self.turtle.shapeIndex)

        screen._turtles.append(q)
        ttype = screen._shapes[self.turtle.shapeIndex]._type
        wenn ttype == "polygon":
            q.turtle._item = screen._createpoly()
        sowenn ttype == "image":
            q.turtle._item = screen._createimage(screen._shapes["blank"]._data)
        sowenn ttype == "compound":
            q.turtle._item = [screen._createpoly() fuer item in
                              screen._shapes[self.turtle.shapeIndex]._data]
        q.currentLineItem = screen._createline()
        q._update()
        return q

    def shape(self, name=Nichts):
        """Set turtle shape to shape mit given name / return current shapename.

        Optional argument:
        name -- a string, which is a valid shapename

        Set turtle shape to shape mit given name or, wenn name is nicht given,
        return name of current shape.
        Shape mit name must exist in the TurtleScreen's shape dictionary.
        Initially there are the following polygon shapes:
        'arrow', 'turtle', 'circle', 'square', 'triangle', 'classic'.
        To learn about how to deal mit shapes see Screen-method register_shape.

        Example (for a Turtle instance named turtle):
        >>> turtle.shape()
        'arrow'
        >>> turtle.shape("turtle")
        >>> turtle.shape()
        'turtle'
        """
        wenn name is Nichts:
            return self.turtle.shapeIndex
        wenn nicht name in self.screen.getshapes():
            raise TurtleGraphicsError("There is no shape named %s" % name)
        self.turtle._setshape(name)
        self._update()

    def shapesize(self, stretch_wid=Nichts, stretch_len=Nichts, outline=Nichts):
        """Set/return turtle's stretchfactors/outline. Set resizemode to "user".

        Optional arguments:
           stretch_wid : positive number
           stretch_len : positive number
           outline  : positive number

        Return oder set the pen's attributes x/y-stretchfactors and/or outline.
        Set resizemode to "user".
        If und only wenn resizemode is set to "user", the turtle will be displayed
        stretched according to its stretchfactors:
        stretch_wid is stretchfactor perpendicular to orientation
        stretch_len is stretchfactor in direction of turtles orientation.
        outline determines the width of the shapes's outline.

        Examples (for a Turtle instance named turtle):
        >>> turtle.resizemode("user")
        >>> turtle.shapesize(5, 5, 12)
        >>> turtle.shapesize(outline=8)
        """
        wenn stretch_wid is stretch_len is outline is Nichts:
            stretch_wid, stretch_len = self._stretchfactor
            return stretch_wid, stretch_len, self._outlinewidth
        wenn stretch_wid == 0 oder stretch_len == 0:
            raise TurtleGraphicsError("stretch_wid/stretch_len must nicht be zero")
        wenn stretch_wid is nicht Nichts:
            wenn stretch_len is Nichts:
                stretchfactor = stretch_wid, stretch_wid
            sonst:
                stretchfactor = stretch_wid, stretch_len
        sowenn stretch_len is nicht Nichts:
            stretchfactor = self._stretchfactor[0], stretch_len
        sonst:
            stretchfactor = self._stretchfactor
        wenn outline is Nichts:
            outline = self._outlinewidth
        self.pen(resizemode="user",
                 stretchfactor=stretchfactor, outline=outline)

    def shearfactor(self, shear=Nichts):
        """Set oder return the current shearfactor.

        Optional argument: shear -- number, tangent of the shear angle

        Shear the turtleshape according to the given shearfactor shear,
        which is the tangent of the shear angle. DO NOT change the
        turtle's heading (direction of movement).
        If shear is nicht given: return the current shearfactor, i. e. the
        tangent of the shear angle, by which lines parallel to the
        heading of the turtle are sheared.

        Examples (for a Turtle instance named turtle):
        >>> turtle.shape("circle")
        >>> turtle.shapesize(5,2)
        >>> turtle.shearfactor(0.5)
        >>> turtle.shearfactor()
        >>> 0.5
        """
        wenn shear is Nichts:
            return self._shearfactor
        self.pen(resizemode="user", shearfactor=shear)

    def tiltangle(self, angle=Nichts):
        """Set oder return the current tilt-angle.

        Optional argument: angle -- number

        Rotate the turtleshape to point in the direction specified by angle,
        regardless of its current tilt-angle. DO NOT change the turtle's
        heading (direction of movement).
        If angle is nicht given: return the current tilt-angle, i. e. the angle
        between the orientation of the turtleshape und the heading of the
        turtle (its direction of movement).

        Examples (for a Turtle instance named turtle):
        >>> turtle.shape("circle")
        >>> turtle.shapesize(5, 2)
        >>> turtle.tiltangle()
        0.0
        >>> turtle.tiltangle(45)
        >>> turtle.tiltangle()
        45.0
        >>> turtle.stamp()
        >>> turtle.fd(50)
        >>> turtle.tiltangle(-45)
        >>> turtle.tiltangle()
        315.0
        >>> turtle.stamp()
        >>> turtle.fd(50)
        """
        wenn angle is Nichts:
            tilt = -math.degrees(self._tilt) * self._angleOrient
            return (tilt / self._degreesPerAU) % self._fullcircle
        sonst:
            tilt = -angle * self._degreesPerAU * self._angleOrient
            tilt = math.radians(tilt) % math.tau
            self.pen(resizemode="user", tilt=tilt)

    def tilt(self, angle):
        """Rotate the turtleshape by angle.

        Argument:
        angle - a number

        Rotate the turtleshape by angle von its current tilt-angle,
        but do NOT change the turtle's heading (direction of movement).

        Examples (for a Turtle instance named turtle):
        >>> turtle.shape("circle")
        >>> turtle.shapesize(5,2)
        >>> turtle.tilt(30)
        >>> turtle.fd(50)
        >>> turtle.tilt(30)
        >>> turtle.fd(50)
        """
        self.tiltangle(angle + self.tiltangle())

    def shapetransform(self, t11=Nichts, t12=Nichts, t21=Nichts, t22=Nichts):
        """Set oder return the current transformation matrix of the turtle shape.

        Optional arguments: t11, t12, t21, t22 -- numbers.

        If none of the matrix elements are given, return the transformation
        matrix.
        Otherwise set the given elements und transform the turtleshape
        according to the matrix consisting of first row t11, t12 und
        second row t21, 22.
        Modify stretchfactor, shearfactor und tiltangle according to the
        given matrix.

        Examples (for a Turtle instance named turtle):
        >>> turtle.shape("square")
        >>> turtle.shapesize(4,2)
        >>> turtle.shearfactor(-0.5)
        >>> turtle.shapetransform()
        (4.0, -1.0, -0.0, 2.0)
        """
        wenn t11 is t12 is t21 is t22 is Nichts:
            return self._shapetrafo
        m11, m12, m21, m22 = self._shapetrafo
        wenn t11 is nicht Nichts: m11 = t11
        wenn t12 is nicht Nichts: m12 = t12
        wenn t21 is nicht Nichts: m21 = t21
        wenn t22 is nicht Nichts: m22 = t22
        wenn t11 * t22 - t12 * t21 == 0:
            raise TurtleGraphicsError("Bad shape transform matrix: must nicht be singular")
        self._shapetrafo = (m11, m12, m21, m22)
        alfa = math.atan2(-m21, m11) % math.tau
        sa, ca = math.sin(alfa), math.cos(alfa)
        a11, a12, a21, a22 = (ca*m11 - sa*m21, ca*m12 - sa*m22,
                              sa*m11 + ca*m21, sa*m12 + ca*m22)
        self._stretchfactor = a11, a22
        self._shearfactor = a12/a22
        self._tilt = alfa
        self.pen(resizemode="user")


    def _polytrafo(self, poly):
        """Computes transformed polygon shapes von a shape
        according to current position und heading.
        """
        screen = self.screen
        p0, p1 = self._position
        e0, e1 = self._orient
        e = Vec2D(e0, e1 * screen.yscale / screen.xscale)
        e0, e1 = (1.0 / abs(e)) * e
        return [(p0+(e1*x+e0*y)/screen.xscale, p1+(-e0*x+e1*y)/screen.yscale)
                                                           fuer (x, y) in poly]

    def get_shapepoly(self):
        """Return the current shape polygon als tuple of coordinate pairs.

        No argument.

        Examples (for a Turtle instance named turtle):
        >>> turtle.shape("square")
        >>> turtle.shapetransform(4, -1, 0, 2)
        >>> turtle.get_shapepoly()
        ((50, -20), (30, 20), (-50, 20), (-30, -20))

        """
        shape = self.screen._shapes[self.turtle.shapeIndex]
        wenn shape._type == "polygon":
            return self._getshapepoly(shape._data, shape._type == "compound")
        # sonst return Nichts

    def _getshapepoly(self, polygon, compound=Falsch):
        """Calculate transformed shape polygon according to resizemode
        und shapetransform.
        """
        wenn self._resizemode == "user" oder compound:
            t11, t12, t21, t22 = self._shapetrafo
        sowenn self._resizemode == "auto":
            l = max(1, self._pensize/5.0)
            t11, t12, t21, t22 = l, 0, 0, l
        sowenn self._resizemode == "noresize":
            return polygon
        return tuple((t11*x + t12*y, t21*x + t22*y) fuer (x, y) in polygon)

    def _drawturtle(self):
        """Manages the correct rendering of the turtle mit respect to
        its shape, resizemode, stretch und tilt etc."""
        screen = self.screen
        shape = screen._shapes[self.turtle.shapeIndex]
        ttype = shape._type
        titem = self.turtle._item
        wenn self._shown und screen._updatecounter == 0 und screen._tracing > 0:
            self._hidden_from_screen = Falsch
            tshape = shape._data
            wenn ttype == "polygon":
                wenn self._resizemode == "noresize": w = 1
                sowenn self._resizemode == "auto": w = self._pensize
                sonst: w =self._outlinewidth
                shape = self._polytrafo(self._getshapepoly(tshape))
                fc, oc = self._fillcolor, self._pencolor
                screen._drawpoly(titem, shape, fill=fc, outline=oc,
                                                      width=w, top=Wahr)
            sowenn ttype == "image":
                screen._drawimage(titem, self._position, tshape)
            sowenn ttype == "compound":
                fuer item, (poly, fc, oc) in zip(titem, tshape):
                    poly = self._polytrafo(self._getshapepoly(poly, Wahr))
                    screen._drawpoly(item, poly, fill=self._cc(fc),
                                     outline=self._cc(oc), width=self._outlinewidth, top=Wahr)
        sonst:
            wenn self._hidden_from_screen:
                return
            wenn ttype == "polygon":
                screen._drawpoly(titem, ((0, 0), (0, 0), (0, 0)), "", "")
            sowenn ttype == "image":
                screen._drawimage(titem, self._position,
                                          screen._shapes["blank"]._data)
            sowenn ttype == "compound":
                fuer item in titem:
                    screen._drawpoly(item, ((0, 0), (0, 0), (0, 0)), "", "")
            self._hidden_from_screen = Wahr

##############################  stamp stuff  ###############################

    def stamp(self):
        """Stamp a copy of the turtleshape onto the canvas und return its id.

        No argument.

        Stamp a copy of the turtle shape onto the canvas at the current
        turtle position. Return a stamp_id fuer that stamp, which can be
        used to delete it by calling clearstamp(stamp_id).

        Example (for a Turtle instance named turtle):
        >>> turtle.color("blue")
        >>> turtle.stamp()
        13
        >>> turtle.fd(50)
        """
        screen = self.screen
        shape = screen._shapes[self.turtle.shapeIndex]
        ttype = shape._type
        tshape = shape._data
        wenn ttype == "polygon":
            stitem = screen._createpoly()
            wenn self._resizemode == "noresize": w = 1
            sowenn self._resizemode == "auto": w = self._pensize
            sonst: w =self._outlinewidth
            shape = self._polytrafo(self._getshapepoly(tshape))
            fc, oc = self._fillcolor, self._pencolor
            screen._drawpoly(stitem, shape, fill=fc, outline=oc,
                                                  width=w, top=Wahr)
        sowenn ttype == "image":
            stitem = screen._createimage("")
            screen._drawimage(stitem, self._position, tshape)
        sowenn ttype == "compound":
            stitem = []
            fuer element in tshape:
                item = screen._createpoly()
                stitem.append(item)
            stitem = tuple(stitem)
            fuer item, (poly, fc, oc) in zip(stitem, tshape):
                poly = self._polytrafo(self._getshapepoly(poly, Wahr))
                screen._drawpoly(item, poly, fill=self._cc(fc),
                                 outline=self._cc(oc), width=self._outlinewidth, top=Wahr)
        self.stampItems.append(stitem)
        self.undobuffer.push(("stamp", stitem))
        return stitem

    def _clearstamp(self, stampid):
        """does the work fuer clearstamp() und clearstamps()
        """
        wenn stampid in self.stampItems:
            wenn isinstance(stampid, tuple):
                fuer subitem in stampid:
                    self.screen._delete(subitem)
            sonst:
                self.screen._delete(stampid)
            self.stampItems.remove(stampid)
        # Delete stampitem von undobuffer wenn necessary
        # wenn clearstamp is called directly.
        item = ("stamp", stampid)
        buf = self.undobuffer
        wenn item nicht in buf.buffer:
            return
        index = buf.buffer.index(item)
        buf.buffer.remove(item)
        wenn index <= buf.ptr:
            buf.ptr = (buf.ptr - 1) % buf.bufsize
        buf.buffer.insert((buf.ptr+1)%buf.bufsize, [Nichts])

    def clearstamp(self, stampid):
        """Delete stamp mit given stampid

        Argument:
        stampid - an integer, must be return value of previous stamp() call.

        Example (for a Turtle instance named turtle):
        >>> turtle.color("blue")
        >>> astamp = turtle.stamp()
        >>> turtle.fd(50)
        >>> turtle.clearstamp(astamp)
        """
        self._clearstamp(stampid)
        self._update()

    def clearstamps(self, n=Nichts):
        """Delete all oder first/last n of turtle's stamps.

        Optional argument:
        n -- an integer

        If n is Nichts, delete all of pen's stamps,
        sonst wenn n > 0 delete first n stamps
        sonst wenn n < 0 delete last n stamps.

        Example (for a Turtle instance named turtle):
        >>> fuer i in range(8):
        ...     turtle.stamp(); turtle.fd(30)
        ...
        >>> turtle.clearstamps(2)
        >>> turtle.clearstamps(-2)
        >>> turtle.clearstamps()
        """
        wenn n is Nichts:
            toDelete = self.stampItems[:]
        sowenn n >= 0:
            toDelete = self.stampItems[:n]
        sonst:
            toDelete = self.stampItems[n:]
        fuer item in toDelete:
            self._clearstamp(item)
        self._update()

    def _goto(self, end):
        """Move the pen to the point end, thereby drawing a line
        wenn pen is down. All other methods fuer turtle movement depend
        on this one.
        """
        ## Version mit undo-stuff
        go_modes = ( self._drawing,
                     self._pencolor,
                     self._pensize,
                     isinstance(self._fillpath, list))
        screen = self.screen
        undo_entry = ("go", self._position, end, go_modes,
                      (self.currentLineItem,
                      self.currentLine[:],
                      screen._pointlist(self.currentLineItem),
                      self.items[:])
                      )
        wenn self.undobuffer:
            self.undobuffer.push(undo_entry)
        start = self._position
        wenn self._speed und screen._tracing == 1:
            diff = (end-start)
            diffsq = (diff[0]*screen.xscale)**2 + (diff[1]*screen.yscale)**2
            nhops = 1+int((diffsq**0.5)/(3*(1.1**self._speed)*self._speed))
            delta = diff * (1.0/nhops)
            fuer n in range(1, nhops):
                wenn n == 1:
                    top = Wahr
                sonst:
                    top = Falsch
                self._position = start + delta * n
                wenn self._drawing:
                    screen._drawline(self.drawingLineItem,
                                     (start, self._position),
                                     self._pencolor, self._pensize, top)
                self._update()
            wenn self._drawing:
                screen._drawline(self.drawingLineItem, ((0, 0), (0, 0)),
                                               fill="", width=self._pensize)
        # Turtle now at end,
        wenn self._drawing: # now update currentLine
            self.currentLine.append(end)
        wenn isinstance(self._fillpath, list):
            self._fillpath.append(end)
        ######    vererbung!!!!!!!!!!!!!!!!!!!!!!
        self._position = end
        wenn self._creatingPoly:
            self._poly.append(end)
        wenn len(self.currentLine) > 42: # 42! answer to the ultimate question
                                       # of life, the universe und everything
            self._newLine()
        self._update() #count=Wahr)

    def _undogoto(self, entry):
        """Reverse a _goto. Used fuer undo()
        """
        old, new, go_modes, coodata = entry
        drawing, pc, ps, filling = go_modes
        cLI, cL, pl, items = coodata
        screen = self.screen
        wenn abs(self._position - new) > 0.5:
            drucke ("undogoto: HALLO-DA-STIMMT-WAS-NICHT!")
        # restore former situation
        self.currentLineItem = cLI
        self.currentLine = cL

        wenn pl == [(0, 0), (0, 0)]:
            usepc = ""
        sonst:
            usepc = pc
        screen._drawline(cLI, pl, fill=usepc, width=ps)

        todelete = [i fuer i in self.items wenn (i nicht in items) und
                                       (screen._type(i) == "line")]
        fuer i in todelete:
            screen._delete(i)
            self.items.remove(i)

        start = old
        wenn self._speed und screen._tracing == 1:
            diff = old - new
            diffsq = (diff[0]*screen.xscale)**2 + (diff[1]*screen.yscale)**2
            nhops = 1+int((diffsq**0.5)/(3*(1.1**self._speed)*self._speed))
            delta = diff * (1.0/nhops)
            fuer n in range(1, nhops):
                wenn n == 1:
                    top = Wahr
                sonst:
                    top = Falsch
                self._position = new + delta * n
                wenn drawing:
                    screen._drawline(self.drawingLineItem,
                                     (start, self._position),
                                     pc, ps, top)
                self._update()
            wenn drawing:
                screen._drawline(self.drawingLineItem, ((0, 0), (0, 0)),
                                               fill="", width=ps)
        # Turtle now at position old,
        self._position = old
        ##  wenn undo is done during creating a polygon, the last vertex
        ##  will be deleted. wenn the polygon is entirely deleted,
        ##  creatingPoly will be set to Falsch.
        ##  Polygons created before the last one will nicht be affected by undo()
        wenn self._creatingPoly:
            wenn len(self._poly) > 0:
                self._poly.pop()
            wenn self._poly == []:
                self._creatingPoly = Falsch
                self._poly = Nichts
        wenn filling:
            wenn self._fillpath == []:
                self._fillpath = Nichts
                drucke("Unwahrscheinlich in _undogoto!")
            sowenn self._fillpath is nicht Nichts:
                self._fillpath.pop()
        self._update() #count=Wahr)

    def _rotate(self, angle):
        """Turns pen clockwise by angle.
        """
        wenn self.undobuffer:
            self.undobuffer.push(("rot", angle, self._degreesPerAU))
        angle *= self._degreesPerAU
        neworient = self._orient.rotate(angle)
        tracing = self.screen._tracing
        wenn tracing == 1 und self._speed > 0:
            anglevel = 3.0 * self._speed
            steps = 1 + int(abs(angle)/anglevel)
            delta = 1.0*angle/steps
            fuer _ in range(steps):
                self._orient = self._orient.rotate(delta)
                self._update()
        self._orient = neworient
        self._update()

    def _newLine(self, usePos=Wahr):
        """Closes current line item und starts a new one.
           Remark: wenn current line became too long, animation
           performance (via _drawline) slowed down considerably.
        """
        wenn len(self.currentLine) > 1:
            self.screen._drawline(self.currentLineItem, self.currentLine,
                                      self._pencolor, self._pensize)
            self.currentLineItem = self.screen._createline()
            self.items.append(self.currentLineItem)
        sonst:
            self.screen._drawline(self.currentLineItem, top=Wahr)
        self.currentLine = []
        wenn usePos:
            self.currentLine = [self._position]

    def filling(self):
        """Return fillstate (Wahr wenn filling, Falsch else).

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.begin_fill()
        >>> wenn turtle.filling():
        ...     turtle.pensize(5)
        ... sonst:
        ...     turtle.pensize(3)
        """
        return isinstance(self._fillpath, list)

    @contextmanager
    def fill(self):
        """A context manager fuer filling a shape.

        Implicitly ensures the code block is wrapped with
        begin_fill() und end_fill().

        Example (for a Turtle instance named turtle):
        >>> turtle.color("black", "red")
        >>> mit turtle.fill():
        ...     turtle.circle(60)
        """
        self.begin_fill()
        try:
            yield
        finally:
            self.end_fill()

    def begin_fill(self):
        """Called just before drawing a shape to be filled.

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.color("black", "red")
        >>> turtle.begin_fill()
        >>> turtle.circle(60)
        >>> turtle.end_fill()
        """
        wenn nicht self.filling():
            self._fillitem = self.screen._createpoly()
            self.items.append(self._fillitem)
        self._fillpath = [self._position]
        self._newLine()
        wenn self.undobuffer:
            self.undobuffer.push(("beginfill", self._fillitem))
        self._update()

    def end_fill(self):
        """Fill the shape drawn after the call begin_fill().

        No argument.

        Example (for a Turtle instance named turtle):
        >>> turtle.color("black", "red")
        >>> turtle.begin_fill()
        >>> turtle.circle(60)
        >>> turtle.end_fill()
        """
        wenn self.filling():
            wenn len(self._fillpath) > 2:
                self.screen._drawpoly(self._fillitem, self._fillpath,
                                      fill=self._fillcolor)
                wenn self.undobuffer:
                    self.undobuffer.push(("dofill", self._fillitem))
            self._fillitem = self._fillpath = Nichts
            self._update()

    def dot(self, size=Nichts, *color):
        """Draw a dot mit diameter size, using color.

        Optional arguments:
        size -- an integer >= 1 (if given)
        color -- a colorstring oder a numeric color tuple

        Draw a circular dot mit diameter size, using color.
        If size is nicht given, the maximum of pensize+4 und 2*pensize is used.

        Example (for a Turtle instance named turtle):
        >>> turtle.dot()
        >>> turtle.fd(50); turtle.dot(20, "blue"); turtle.fd(50)
        """
        wenn nicht color:
            wenn isinstance(size, (str, tuple)):
                color = self._colorstr(size)
                size = self._pensize + max(self._pensize, 4)
            sonst:
                color = self._pencolor
                wenn nicht size:
                    size = self._pensize + max(self._pensize, 4)
        sonst:
            wenn size is Nichts:
                size = self._pensize + max(self._pensize, 4)
            color = self._colorstr(color)
        # If screen were to gain a dot function, see GH #104218.
        pen = self.pen()
        wenn self.undobuffer:
            self.undobuffer.push(["seq"])
            self.undobuffer.cumulate = Wahr
        try:
            wenn self.resizemode() == 'auto':
                self.ht()
            self.pendown()
            self.pensize(size)
            self.pencolor(color)
            self.forward(0)
        finally:
            self.pen(pen)
        wenn self.undobuffer:
            self.undobuffer.cumulate = Falsch

    def _write(self, txt, align, font):
        """Performs the writing fuer write()
        """
        item, end = self.screen._write(self._position, txt, align, font,
                                                          self._pencolor)
        self._update()
        self.items.append(item)
        wenn self.undobuffer:
            self.undobuffer.push(("wri", item))
        return end

    def write(self, arg, move=Falsch, align="left", font=("Arial", 8, "normal")):
        """Write text at the current turtle position.

        Arguments:
        arg -- info, which is to be written to the TurtleScreen
        move (optional) -- Wahr/Falsch
        align (optional) -- one of the strings "left", "center" oder right"
        font (optional) -- a triple (fontname, fontsize, fonttype)

        Write text - the string representation of arg - at the current
        turtle position according to align ("left", "center" oder right")
        und mit the given font.
        If move is Wahr, the pen is moved to the bottom-right corner
        of the text. By default, move is Falsch.

        Example (for a Turtle instance named turtle):
        >>> turtle.write('Home = ', Wahr, align="center")
        >>> turtle.write((0,0), Wahr)
        """
        wenn self.undobuffer:
            self.undobuffer.push(["seq"])
            self.undobuffer.cumulate = Wahr
        end = self._write(str(arg), align.lower(), font)
        wenn move:
            x, y = self.pos()
            self.setpos(end, y)
        wenn self.undobuffer:
            self.undobuffer.cumulate = Falsch

    @contextmanager
    def poly(self):
        """A context manager fuer recording the vertices of a polygon.

        Implicitly ensures that the code block is wrapped with
        begin_poly() und end_poly()

        Example (for a Turtle instance named turtle) where we create a
        triangle als the polygon und move the turtle 100 steps forward:
        >>> mit turtle.poly():
        ...     fuer side in range(3)
        ...         turtle.forward(50)
        ...         turtle.right(60)
        >>> turtle.forward(100)
        """
        self.begin_poly()
        try:
            yield
        finally:
            self.end_poly()

    def begin_poly(self):
        """Start recording the vertices of a polygon.

        No argument.

        Start recording the vertices of a polygon. Current turtle position
        is first point of polygon.

        Example (for a Turtle instance named turtle):
        >>> turtle.begin_poly()
        """
        self._poly = [self._position]
        self._creatingPoly = Wahr

    def end_poly(self):
        """Stop recording the vertices of a polygon.

        No argument.

        Stop recording the vertices of a polygon. Current turtle position is
        last point of polygon. This will be connected mit the first point.

        Example (for a Turtle instance named turtle):
        >>> turtle.end_poly()
        """
        self._creatingPoly = Falsch

    def get_poly(self):
        """Return the lastly recorded polygon.

        No argument.

        Example (for a Turtle instance named turtle):
        >>> p = turtle.get_poly()
        >>> turtle.register_shape("myFavouriteShape", p)
        """
        ## check wenn there is any poly?
        wenn self._poly is nicht Nichts:
            return tuple(self._poly)

    def getscreen(self):
        """Return the TurtleScreen object, the turtle is drawing  on.

        No argument.

        Return the TurtleScreen object, the turtle is drawing  on.
        So TurtleScreen-methods can be called fuer that object.

        Example (for a Turtle instance named turtle):
        >>> ts = turtle.getscreen()
        >>> ts
        <turtle.TurtleScreen object at 0x0106B770>
        >>> ts.bgcolor("pink")
        """
        return self.screen

    def getturtle(self):
        """Return the Turtleobject itself.

        No argument.

        Only reasonable use: als a function to return the 'anonymous turtle':

        Example:
        >>> pet = getturtle()
        >>> pet.fd(50)
        >>> pet
        <turtle.Turtle object at 0x0187D810>
        >>> turtles()
        [<turtle.Turtle object at 0x0187D810>]
        """
        return self

    getpen = getturtle


    ################################################################
    ### screen oriented methods recurring to methods of TurtleScreen
    ################################################################

    def _delay(self, delay=Nichts):
        """Set delay value which determines speed of turtle animation.
        """
        return self.screen.delay(delay)

    def onclick(self, fun, btn=1, add=Nichts):
        """Bind fun to mouse-click event on this turtle on canvas.

        Arguments:
        fun --  a function mit two arguments, to which will be assigned
                the coordinates of the clicked point on the canvas.
        btn --  number of the mouse-button defaults to 1 (left mouse button).
        add --  Wahr oder Falsch. If Wahr, new binding will be added, otherwise
                it will replace a former binding.

        Example fuer the anonymous turtle, i. e. the procedural way:

        >>> def turn(x, y):
        ...     left(360)
        ...
        >>> onclick(turn)  # Now clicking into the turtle will turn it.
        >>> onclick(Nichts)  # event-binding will be removed
        """
        self.screen._onclick(self.turtle._item, fun, btn, add)
        self._update()

    def onrelease(self, fun, btn=1, add=Nichts):
        """Bind fun to mouse-button-release event on this turtle on canvas.

        Arguments:
        fun -- a function mit two arguments, to which will be assigned
                the coordinates of the clicked point on the canvas.
        btn --  number of the mouse-button defaults to 1 (left mouse button).

        Example (for a MyTurtle instance named joe):
        >>> klasse MyTurtle(Turtle):
        ...     def glow(self,x,y):
        ...             self.fillcolor("red")
        ...     def unglow(self,x,y):
        ...             self.fillcolor("")
        ...
        >>> joe = MyTurtle()
        >>> joe.onclick(joe.glow)
        >>> joe.onrelease(joe.unglow)

        Clicking on joe turns fillcolor red, unclicking turns it to
        transparent.
        """
        self.screen._onrelease(self.turtle._item, fun, btn, add)
        self._update()

    def ondrag(self, fun, btn=1, add=Nichts):
        """Bind fun to mouse-move event on this turtle on canvas.

        Arguments:
        fun -- a function mit two arguments, to which will be assigned
               the coordinates of the clicked point on the canvas.
        btn -- number of the mouse-button defaults to 1 (left mouse button).

        Every sequence of mouse-move-events on a turtle is preceded by a
        mouse-click event on that turtle.

        Example (for a Turtle instance named turtle):
        >>> turtle.ondrag(turtle.goto)

        Subsequently clicking und dragging a Turtle will move it
        across the screen thereby producing handdrawings (if pen is
        down).
        """
        self.screen._ondrag(self.turtle._item, fun, btn, add)


    def _undo(self, action, data):
        """Does the main part of the work fuer undo()
        """
        wenn self.undobuffer is Nichts:
            return
        wenn action == "rot":
            angle, degPAU = data
            self._rotate(-angle*degPAU/self._degreesPerAU)
            dummy = self.undobuffer.pop()
        sowenn action == "stamp":
            stitem = data[0]
            self.clearstamp(stitem)
        sowenn action == "go":
            self._undogoto(data)
        sowenn action in ["wri", "dot"]:
            item = data[0]
            self.screen._delete(item)
            self.items.remove(item)
        sowenn action == "dofill":
            item = data[0]
            self.screen._drawpoly(item, ((0, 0),(0, 0),(0, 0)),
                                  fill="", outline="")
        sowenn action == "beginfill":
            item = data[0]
            self._fillitem = self._fillpath = Nichts
            wenn item in self.items:
                self.screen._delete(item)
                self.items.remove(item)
        sowenn action == "pen":
            TPen.pen(self, data[0])
            self.undobuffer.pop()

    def undo(self):
        """undo (repeatedly) the last turtle action.

        No argument.

        undo (repeatedly) the last turtle action.
        Number of available undo actions is determined by the size of
        the undobuffer.

        Example (for a Turtle instance named turtle):
        >>> fuer i in range(4):
        ...     turtle.fd(50); turtle.lt(80)
        ...
        >>> fuer i in range(8):
        ...     turtle.undo()
        ...
        """
        wenn self.undobuffer is Nichts:
            return
        item = self.undobuffer.pop()
        action = item[0]
        data = item[1:]
        wenn action == "seq":
            waehrend data:
                item = data.pop()
                self._undo(item[0], item[1:])
        sonst:
            self._undo(action, data)

    turtlesize = shapesize

RawPen = RawTurtle

###  Screen - Singleton  ########################

def Screen():
    """Return the singleton screen object.
    If none exists at the moment, create a new one und return it,
    sonst return the existing one."""
    wenn Turtle._screen is Nichts:
        Turtle._screen = _Screen()
    return Turtle._screen

klasse _Screen(TurtleScreen):

    _root = Nichts
    _canvas = Nichts
    _title = _CFG["title"]

    def __init__(self):
        wenn _Screen._root is Nichts:
            _Screen._root = self._root = _Root()
            self._root.title(_Screen._title)
            self._root.ondestroy(self._destroy)
        wenn _Screen._canvas is Nichts:
            width = _CFG["width"]
            height = _CFG["height"]
            canvwidth = _CFG["canvwidth"]
            canvheight = _CFG["canvheight"]
            leftright = _CFG["leftright"]
            topbottom = _CFG["topbottom"]
            self._root.setupcanvas(width, height, canvwidth, canvheight)
            _Screen._canvas = self._root._getcanvas()
            TurtleScreen.__init__(self, _Screen._canvas)
            self.setup(width, height, leftright, topbottom)

    def setup(self, width=_CFG["width"], height=_CFG["height"],
              startx=_CFG["leftright"], starty=_CFG["topbottom"]):
        """ Set the size und position of the main window.

        Arguments:
        width: als integer a size in pixels, als float a fraction of the screen.
          Default is 50% of screen.
        height: als integer the height in pixels, als float a fraction of the
          screen. Default is 75% of screen.
        startx: wenn positive, starting position in pixels von the left
          edge of the screen, wenn negative von the right edge
          Default, startx=Nichts is to center window horizontally.
        starty: wenn positive, starting position in pixels von the top
          edge of the screen, wenn negative von the bottom edge
          Default, starty=Nichts is to center window vertically.

        Examples (for a Screen instance named screen):
        >>> screen.setup (width=200, height=200, startx=0, starty=0)

        sets window to 200x200 pixels, in upper left of screen

        >>> screen.setup(width=.75, height=0.5, startx=Nichts, starty=Nichts)

        sets window to 75% of screen by 50% of screen und centers
        """
        wenn nicht hasattr(self._root, "set_geometry"):
            return
        sw = self._root.win_width()
        sh = self._root.win_height()
        wenn isinstance(width, float) und 0 <= width <= 1:
            width = sw*width
        wenn startx is Nichts:
            startx = (sw - width) / 2
        wenn isinstance(height, float) und 0 <= height <= 1:
            height = sh*height
        wenn starty is Nichts:
            starty = (sh - height) / 2
        self._root.set_geometry(width, height, startx, starty)
        self.update()

    def title(self, titlestring):
        """Set title of turtle-window

        Argument:
        titlestring -- a string, to appear in the titlebar of the
                       turtle graphics window.

        This is a method of Screen-class. Not available fuer TurtleScreen-
        objects.

        Example (for a Screen instance named screen):
        >>> screen.title("Welcome to the turtle-zoo!")
        """
        wenn _Screen._root is nicht Nichts:
            _Screen._root.title(titlestring)
        _Screen._title = titlestring

    def _destroy(self):
        root = self._root
        wenn root is _Screen._root:
            Turtle._pen = Nichts
            Turtle._screen = Nichts
            _Screen._root = Nichts
            _Screen._canvas = Nichts
        TurtleScreen._RUNNING = Falsch
        root.destroy()

    def bye(self):
        """Shut the turtlegraphics window.

        Example (for a TurtleScreen instance named screen):
        >>> screen.bye()
        """
        self._destroy()

    def exitonclick(self):
        """Go into mainloop until the mouse is clicked.

        No arguments.

        Bind bye() method to mouseclick on TurtleScreen.
        If "using_IDLE" - value in configuration dictionary is Falsch
        (default value), enter mainloop.
        If IDLE mit -n switch (no subprocess) is used, this value should be
        set to Wahr in turtle.cfg. In this case IDLE's mainloop
        is active also fuer the client script.

        This is a method of the Screen-class und nicht available for
        TurtleScreen instances.

        Example (for a Screen instance named screen):
        >>> screen.exitonclick()

        """
        def exitGracefully(x, y):
            """Screen.bye() mit two dummy-parameters"""
            self.bye()
        self.onclick(exitGracefully)
        wenn _CFG["using_IDLE"]:
            return
        try:
            mainloop()
        except AttributeError:
            exit(0)

klasse Turtle(RawTurtle):
    """RawTurtle auto-creating (scrolled) canvas.

    When a Turtle object is created oder a function derived von some
    Turtle method is called a TurtleScreen object is automatically created.
    """
    _pen = Nichts
    _screen = Nichts

    def __init__(self,
                 shape=_CFG["shape"],
                 undobuffersize=_CFG["undobuffersize"],
                 visible=_CFG["visible"]):
        wenn Turtle._screen is Nichts:
            Turtle._screen = Screen()
        RawTurtle.__init__(self, Turtle._screen,
                           shape=shape,
                           undobuffersize=undobuffersize,
                           visible=visible)

Pen = Turtle

def write_docstringdict(filename="turtle_docstringdict"):
    """Create und write docstring-dictionary to file.

    Optional argument:
    filename -- a string, used als filename
                default value is turtle_docstringdict

    Has to be called explicitly, (nicht used by the turtle-graphics classes)
    The docstring dictionary will be written to the Python script <filename>.py
    It is intended to serve als a template fuer translation of the docstrings
    into different languages.
    """
    docsdict = {}

    fuer methodname in _tg_screen_functions:
        key = "_Screen."+methodname
        docsdict[key] = eval(key).__doc__
    fuer methodname in _tg_turtle_functions:
        key = "Turtle."+methodname
        docsdict[key] = eval(key).__doc__

    mit open("%s.py" % filename,"w") als f:
        keys = sorted(x fuer x in docsdict
                      wenn x.split('.')[1] nicht in _alias_list)
        f.write('docsdict = {\n\n')
        fuer key in keys[:-1]:
            f.write('%s :\n' % repr(key))
            f.write('        """%s\n""",\n\n' % docsdict[key])
        key = keys[-1]
        f.write('%s :\n' % repr(key))
        f.write('        """%s\n"""\n\n' % docsdict[key])
        f.write("}\n")
        f.close()

def read_docstrings(lang):
    """Read in docstrings von lang-specific docstring dictionary.

    Transfer docstrings, translated to lang, von a dictionary-file
    to the methods of classes Screen und Turtle und - in revised form -
    to the corresponding functions.
    """
    modname = "turtle_docstringdict_%(language)s" % {'language':lang.lower()}
    module = __import__(modname)
    docsdict = module.docsdict
    fuer key in docsdict:
        try:
#            eval(key).im_func.__doc__ = docsdict[key]
            eval(key).__doc__ = docsdict[key]
        except Exception:
            drucke("Bad docstring-entry: %s" % key)

_LANGUAGE = _CFG["language"]

try:
    wenn _LANGUAGE != "english":
        read_docstrings(_LANGUAGE)
except ImportError:
    drucke("Cannot find docsdict for", _LANGUAGE)
except Exception:
    drucke ("Unknown Error when trying to importiere %s-docstring-dictionary" %
                                                                  _LANGUAGE)


def getmethparlist(ob):
    """Get strings describing the arguments fuer the given object

    Returns a pair of strings representing function parameter lists
    including parenthesis.  The first string is suitable fuer use in
    function definition und the second is suitable fuer use in function
    call.  The "self" parameter is nicht included.
    """
    orig_sig = inspect.signature(ob)
    # bit of a hack fuer methods - turn it into a function
    # but we drop the "self" param.
    # Try und build one fuer Python defined functions
    func_sig = orig_sig.replace(
        parameters=list(orig_sig.parameters.values())[1:],
    )

    call_args = []
    fuer param in func_sig.parameters.values():
        match param.kind:
            case (
                inspect.Parameter.POSITIONAL_ONLY
                | inspect.Parameter.POSITIONAL_OR_KEYWORD
            ):
                call_args.append(param.name)
            case inspect.Parameter.VAR_POSITIONAL:
                call_args.append(f'*{param.name}')
            case inspect.Parameter.KEYWORD_ONLY:
                call_args.append(f'{param.name}={param.name}')
            case inspect.Parameter.VAR_KEYWORD:
                call_args.append(f'**{param.name}')
            case _:
                raise RuntimeError('Unsupported parameter kind', param.kind)
    call_text = f'({', '.join(call_args)})'

    return str(func_sig), call_text

def _turtle_docrevise(docstr):
    """To reduce docstrings von RawTurtle klasse fuer functions
    """
    importiere re
    wenn docstr is Nichts:
        return Nichts
    turtlename = _CFG["exampleturtle"]
    newdocstr = docstr.replace("%s." % turtlename,"")
    parexp = re.compile(r' \(.+ %s\):' % turtlename)
    newdocstr = parexp.sub(":", newdocstr)
    return newdocstr

def _screen_docrevise(docstr):
    """To reduce docstrings von TurtleScreen klasse fuer functions
    """
    importiere re
    wenn docstr is Nichts:
        return Nichts
    screenname = _CFG["examplescreen"]
    newdocstr = docstr.replace("%s." % screenname,"")
    parexp = re.compile(r' \(.+ %s\):' % screenname)
    newdocstr = parexp.sub(":", newdocstr)
    return newdocstr

## The following mechanism makes all methods of RawTurtle und Turtle available
## als functions. So we can enhance, change, add, delete methods to these
## classes und do nicht need to change anything here.

__func_body = """\
def {name}{paramslist}:
    wenn {obj} is Nichts:
        wenn nicht TurtleScreen._RUNNING:
            TurtleScreen._RUNNING = Wahr
            raise Terminator
        {obj} = {init}
    try:
        return {obj}.{name}{argslist}
    except TK.TclError:
        wenn nicht TurtleScreen._RUNNING:
            TurtleScreen._RUNNING = Wahr
            raise Terminator
        raise
"""

def _make_global_funcs(functions, cls, obj, init, docrevise):
    fuer methodname in functions:
        method = getattr(cls, methodname)
        pl1, pl2 = getmethparlist(method)
        wenn pl1 == "":
            drucke(">>>>>>", pl1, pl2)
            weiter
        defstr = __func_body.format(obj=obj, init=init, name=methodname,
                                    paramslist=pl1, argslist=pl2)
        exec(defstr, globals())
        globals()[methodname].__doc__ = docrevise(method.__doc__)

_make_global_funcs(_tg_screen_functions, _Screen,
                   'Turtle._screen', 'Screen()', _screen_docrevise)
_make_global_funcs(_tg_turtle_functions, Turtle,
                   'Turtle._pen', 'Turtle()', _turtle_docrevise)


done = mainloop

wenn __name__ == "__main__":
    def switchpen():
        wenn isdown():
            pu()
        sonst:
            pd()

    def demo1():
        """Demo of old turtle.py - module"""
        reset()
        tracer(Wahr)
        up()
        backward(100)
        down()
        # draw 3 squares; the last filled
        width(3)
        fuer i in range(3):
            wenn i == 2:
                begin_fill()
            fuer _ in range(4):
                forward(20)
                left(90)
            wenn i == 2:
                color("maroon")
                end_fill()
            up()
            forward(30)
            down()
        width(1)
        color("black")
        # move out of the way
        tracer(Falsch)
        up()
        right(90)
        forward(100)
        right(90)
        forward(100)
        right(180)
        down()
        # some text
        write("startstart", 1)
        write("start", 1)
        color("red")
        # staircase
        fuer i in range(5):
            forward(20)
            left(90)
            forward(20)
            right(90)
        # filled staircase
        tracer(Wahr)
        begin_fill()
        fuer i in range(5):
            forward(20)
            left(90)
            forward(20)
            right(90)
        end_fill()
        # more text

    def demo2():
        """Demo of some new features."""
        speed(1)
        st()
        pensize(3)
        setheading(towards(0, 0))
        radius = distance(0, 0)/2.0
        rt(90)
        fuer _ in range(18):
            switchpen()
            circle(radius, 10)
        write("wait a moment...")
        waehrend undobufferentries():
            undo()
        reset()
        lt(90)
        colormode(255)
        laenge = 10
        pencolor("green")
        pensize(3)
        lt(180)
        fuer i in range(-2, 16):
            wenn i > 0:
                begin_fill()
                fillcolor(255-15*i, 0, 15*i)
            fuer _ in range(3):
                fd(laenge)
                lt(120)
            end_fill()
            laenge += 10
            lt(15)
            speed((speed()+1)%12)
        #end_fill()

        lt(120)
        pu()
        fd(70)
        rt(30)
        pd()
        color("red","yellow")
        speed(0)
        begin_fill()
        fuer _ in range(4):
            circle(50, 90)
            rt(90)
            fd(30)
            rt(90)
        end_fill()
        lt(90)
        pu()
        fd(30)
        pd()
        shape("turtle")

        tri = getturtle()
        tri.resizemode("auto")
        turtle = Turtle()
        turtle.resizemode("auto")
        turtle.shape("turtle")
        turtle.reset()
        turtle.left(90)
        turtle.speed(0)
        turtle.up()
        turtle.goto(280, 40)
        turtle.lt(30)
        turtle.down()
        turtle.speed(6)
        turtle.color("blue","orange")
        turtle.pensize(2)
        tri.speed(6)
        setheading(towards(turtle))
        count = 1
        waehrend tri.distance(turtle) > 4:
            turtle.fd(3.5)
            turtle.lt(0.6)
            tri.setheading(tri.towards(turtle))
            tri.fd(4)
            wenn count % 20 == 0:
                turtle.stamp()
                tri.stamp()
                switchpen()
            count += 1
        tri.write("CAUGHT! ", font=("Arial", 16, "bold"), align="right")
        tri.pencolor("black")
        tri.pencolor("red")

        def baba(xdummy, ydummy):
            clearscreen()
            bye()

        time.sleep(2)

        waehrend undobufferentries():
            tri.undo()
            turtle.undo()
        tri.fd(50)
        tri.write("  Click me!", font = ("Courier", 12, "bold") )
        tri.onclick(baba, 1)

    demo1()
    demo2()
    exitonclick()
