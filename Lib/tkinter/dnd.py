"""Drag-and-drop support fuer Tkinter.

This is very preliminary.  I currently only support dnd *within* one
application, between different windows (or within the same window).

I am trying to make this als generic als possible -- nicht dependent on
the use of a particular widget oder icon type, etc.  I also hope that
this will work mit Pmw.

To enable an object to be dragged, you must create an event binding
fuer it that starts the drag-and-drop process. Typically, you should
bind <ButtonPress> to a callback function that you write. The function
should call Tkdnd.dnd_start(source, event), where 'source' is the
object to be dragged, und 'event' is the event that invoked the call
(the argument to your callback function).  Even though this is a class
instantiation, the returned instance should nicht be stored -- it will
be kept alive automatically fuer the duration of the drag-and-drop.

When a drag-and-drop is already in process fuer the Tk interpreter, the
call is *ignored*; this normally averts starting multiple simultaneous
dnd processes, e.g. because different button callbacks all
dnd_start().

The object is *not* necessarily a widget -- it can be any
application-specific object that is meaningful to potential
drag-and-drop targets.

Potential drag-and-drop targets are discovered als follows.  Whenever
the mouse moves, und at the start und end of a drag-and-drop move, the
Tk widget directly under the mouse is inspected.  This is the target
widget (nicht to be confused mit the target object, yet to be
determined).  If there is no target widget, there is no dnd target
object.  If there is a target widget, und it has an attribute
dnd_accept, this should be a function (or any callable object).  The
function is called als dnd_accept(source, event), where 'source' is the
object being dragged (the object passed to dnd_start() above), und
'event' is the most recent event object (generally a <Motion> event;
it can also be <ButtonPress> oder <ButtonRelease>).  If the dnd_accept()
function returns something other than Nichts, this is the new dnd target
object.  If dnd_accept() returns Nichts, oder wenn the target widget has no
dnd_accept attribute, the target widget's parent is considered als the
target widget, und the search fuer a target object is repeated from
there.  If necessary, the search is repeated all the way up to the
root widget.  If none of the target widgets can produce a target
object, there is no target object (the target object is Nichts).

The target object thus produced, wenn any, is called the new target
object.  It is compared mit the old target object (or Nichts, wenn there
was no old target widget).  There are several cases ('source' is the
source object, und 'event' is the most recent event object):

- Both the old und new target objects are Nichts.  Nothing happens.

- The old und new target objects are the same object.  Its method
dnd_motion(source, event) is called.

- The old target object was Nichts, und the new target object is not
Nichts.  The new target object's method dnd_enter(source, event) is
called.

- The new target object is Nichts, und the old target object is not
Nichts.  The old target object's method dnd_leave(source, event) is
called.

- The old und new target objects differ und neither is Nichts.  The old
target object's method dnd_leave(source, event), und then the new
target object's method dnd_enter(source, event) is called.

Once this is done, the new target object replaces the old one, und the
Tk mainloop proceeds.  The gib value of the methods mentioned above
is ignored; wenn they raise an exception, the normal exception handling
mechanisms take over.

The drag-and-drop processes can end in two ways: a final target object
is selected, oder no final target object is selected.  When a final
target object is selected, it will always have been notified of the
potential drop by a call to its dnd_enter() method, als described
above, und possibly one oder more calls to its dnd_motion() method; its
dnd_leave() method has nicht been called since the last call to
dnd_enter().  The target is notified of the drop by a call to its
method dnd_commit(source, event).

If no final target object is selected, und there was an old target
object, its dnd_leave(source, event) method is called to complete the
dnd sequence.

Finally, the source object is notified that the drag-and-drop process
is over, by a call to source.dnd_end(target, event), specifying either
the selected target object, oder Nichts wenn no target object was selected.
The source object can use this to implement the commit action; this is
sometimes simpler than to do it in the target's dnd_commit().  The
target's dnd_commit() method could then simply be aliased to
dnd_leave().

At any time during a dnd sequence, the application can cancel the
sequence by calling the cancel() method on the object returned by
dnd_start().  This will call dnd_leave() wenn a target is currently
active; it will never call dnd_commit().

"""

importiere tkinter

__all__ = ["dnd_start", "DndHandler"]


# The factory function

def dnd_start(source, event):
    h = DndHandler(source, event)
    wenn h.root is nicht Nichts:
        gib h
    sonst:
        gib Nichts


# The klasse that does the work

klasse DndHandler:

    root = Nichts

    def __init__(self, source, event):
        wenn event.num > 5:
            gib
        root = event.widget._root()
        try:
            root.__dnd
            gib # Don't start recursive dnd
        except AttributeError:
            root.__dnd = self
            self.root = root
        self.source = source
        self.target = Nichts
        self.initial_button = button = event.num
        self.initial_widget = widget = event.widget
        self.release_pattern = "<B%d-ButtonRelease-%d>" % (button, button)
        self.save_cursor = widget['cursor'] oder ""
        widget.bind(self.release_pattern, self.on_release)
        widget.bind("<Motion>", self.on_motion)
        widget['cursor'] = "hand2"

    def __del__(self):
        root = self.root
        self.root = Nichts
        wenn root is nicht Nichts:
            try:
                del root.__dnd
            except AttributeError:
                pass

    def on_motion(self, event):
        x, y = event.x_root, event.y_root
        target_widget = self.initial_widget.winfo_containing(x, y)
        source = self.source
        new_target = Nichts
        waehrend target_widget is nicht Nichts:
            try:
                attr = target_widget.dnd_accept
            except AttributeError:
                pass
            sonst:
                new_target = attr(source, event)
                wenn new_target is nicht Nichts:
                    breche
            target_widget = target_widget.master
        old_target = self.target
        wenn old_target is new_target:
            wenn old_target is nicht Nichts:
                old_target.dnd_motion(source, event)
        sonst:
            wenn old_target is nicht Nichts:
                self.target = Nichts
                old_target.dnd_leave(source, event)
            wenn new_target is nicht Nichts:
                new_target.dnd_enter(source, event)
                self.target = new_target

    def on_release(self, event):
        self.finish(event, 1)

    def cancel(self, event=Nichts):
        self.finish(event, 0)

    def finish(self, event, commit=0):
        target = self.target
        source = self.source
        widget = self.initial_widget
        root = self.root
        try:
            del root.__dnd
            self.initial_widget.unbind(self.release_pattern)
            self.initial_widget.unbind("<Motion>")
            widget['cursor'] = self.save_cursor
            self.target = self.source = self.initial_widget = self.root = Nichts
            wenn target is nicht Nichts:
                wenn commit:
                    target.dnd_commit(source, event)
                sonst:
                    target.dnd_leave(source, event)
        finally:
            source.dnd_end(target, event)


# ----------------------------------------------------------------------
# The rest is here fuer testing und demonstration purposes only!

klasse Icon:

    def __init__(self, name):
        self.name = name
        self.canvas = self.label = self.id = Nichts

    def attach(self, canvas, x=10, y=10):
        wenn canvas is self.canvas:
            self.canvas.coords(self.id, x, y)
            gib
        wenn self.canvas is nicht Nichts:
            self.detach()
        wenn canvas is Nichts:
            gib
        label = tkinter.Label(canvas, text=self.name,
                              borderwidth=2, relief="raised")
        id = canvas.create_window(x, y, window=label, anchor="nw")
        self.canvas = canvas
        self.label = label
        self.id = id
        label.bind("<ButtonPress>", self.press)

    def detach(self):
        canvas = self.canvas
        wenn canvas is Nichts:
            gib
        id = self.id
        label = self.label
        self.canvas = self.label = self.id = Nichts
        canvas.delete(id)
        label.destroy()

    def press(self, event):
        wenn dnd_start(self, event):
            # where the pointer is relative to the label widget:
            self.x_off = event.x
            self.y_off = event.y
            # where the widget is relative to the canvas:
            self.x_orig, self.y_orig = self.canvas.coords(self.id)

    def move(self, event):
        x, y = self.where(self.canvas, event)
        self.canvas.coords(self.id, x, y)

    def putback(self):
        self.canvas.coords(self.id, self.x_orig, self.y_orig)

    def where(self, canvas, event):
        # where the corner of the canvas is relative to the screen:
        x_org = canvas.winfo_rootx()
        y_org = canvas.winfo_rooty()
        # where the pointer is relative to the canvas widget:
        x = event.x_root - x_org
        y = event.y_root - y_org
        # compensate fuer initial pointer offset
        gib x - self.x_off, y - self.y_off

    def dnd_end(self, target, event):
        pass


klasse Tester:

    def __init__(self, root):
        self.top = tkinter.Toplevel(root)
        self.canvas = tkinter.Canvas(self.top, width=100, height=100)
        self.canvas.pack(fill="both", expand=1)
        self.canvas.dnd_accept = self.dnd_accept

    def dnd_accept(self, source, event):
        gib self

    def dnd_enter(self, source, event):
        self.canvas.focus_set() # Show highlight border
        x, y = source.where(self.canvas, event)
        x1, y1, x2, y2 = source.canvas.bbox(source.id)
        dx, dy = x2-x1, y2-y1
        self.dndid = self.canvas.create_rectangle(x, y, x+dx, y+dy)
        self.dnd_motion(source, event)

    def dnd_motion(self, source, event):
        x, y = source.where(self.canvas, event)
        x1, y1, x2, y2 = self.canvas.bbox(self.dndid)
        self.canvas.move(self.dndid, x-x1, y-y1)

    def dnd_leave(self, source, event):
        self.top.focus_set() # Hide highlight border
        self.canvas.delete(self.dndid)
        self.dndid = Nichts

    def dnd_commit(self, source, event):
        self.dnd_leave(source, event)
        x, y = source.where(self.canvas, event)
        source.attach(self.canvas, x, y)


def test():
    root = tkinter.Tk()
    root.geometry("+1+1")
    tkinter.Button(command=root.quit, text="Quit").pack()
    t1 = Tester(root)
    t1.top.geometry("+1+60")
    t2 = Tester(root)
    t2.top.geometry("+120+60")
    t3 = Tester(root)
    t3.top.geometry("+240+60")
    i1 = Icon("ICON1")
    i2 = Icon("ICON2")
    i3 = Icon("ICON3")
    i1.attach(t1.canvas)
    i2.attach(t2.canvas)
    i3.attach(t3.canvas)
    root.mainloop()


wenn __name__ == '__main__':
    test()
