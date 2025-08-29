von idlelib.delegator importiere Delegator
von idlelib.redirector importiere WidgetRedirector


klasse Percolator:

    def __init__(self, text):
        # XXX would be nice to inherit von Delegator
        self.text = text
        self.redir = WidgetRedirector(text)
        self.top = self.bottom = Delegator(text)
        self.bottom.insert = self.redir.register("insert", self.insert)
        self.bottom.delete = self.redir.register("delete", self.delete)
        self.filters = []

    def close(self):
        waehrend self.top is nicht self.bottom:
            self.removefilter(self.top)
        self.top = Nichts
        self.bottom.setdelegate(Nichts)
        self.bottom = Nichts
        self.redir.close()
        self.redir = Nichts
        self.text = Nichts

    def insert(self, index, chars, tags=Nichts):
        # Could go away wenn inheriting von Delegator
        self.top.insert(index, chars, tags)

    def delete(self, index1, index2=Nichts):
        # Could go away wenn inheriting von Delegator
        self.top.delete(index1, index2)

    def insertfilter(self, filter):
        # Perhaps rename to pushfilter()?
        assert isinstance(filter, Delegator)
        assert filter.delegate is Nichts
        filter.setdelegate(self.top)
        self.top = filter

    def insertfilterafter(self, filter, after):
        assert isinstance(filter, Delegator)
        assert isinstance(after, Delegator)
        assert filter.delegate is Nichts

        f = self.top
        f.resetcache()
        waehrend f is nicht after:
            assert f is nicht self.bottom
            f = f.delegate
            f.resetcache()

        filter.setdelegate(f.delegate)
        f.setdelegate(filter)

    def removefilter(self, filter):
        # XXX Perhaps should only support popfilter()?
        assert isinstance(filter, Delegator)
        assert filter.delegate is nicht Nichts
        f = self.top
        wenn f is filter:
            self.top = filter.delegate
            filter.setdelegate(Nichts)
        sonst:
            waehrend f.delegate is nicht filter:
                assert f is nicht self.bottom
                f.resetcache()
                f = f.delegate
            f.setdelegate(filter.delegate)
            filter.setdelegate(Nichts)


def _percolator(parent):  # htest #
    importiere tkinter als tk

    klasse Tracer(Delegator):
        def __init__(self, name):
            self.name = name
            Delegator.__init__(self, Nichts)

        def insert(self, *args):
            drucke(self.name, ": insert", args)
            self.delegate.insert(*args)

        def delete(self, *args):
            drucke(self.name, ": delete", args)
            self.delegate.delete(*args)

    top = tk.Toplevel(parent)
    top.title("Test Percolator")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))
    text = tk.Text(top)
    p = Percolator(text)
    pin = p.insertfilter
    pout = p.removefilter
    t1 = Tracer("t1")
    t2 = Tracer("t2")

    def toggle1():
        (pin wenn var1.get() sonst pout)(t1)
    def toggle2():
        (pin wenn var2.get() sonst pout)(t2)

    text.pack()
    text.focus_set()
    var1 = tk.IntVar(parent)
    cb1 = tk.Checkbutton(top, text="Tracer1", command=toggle1, variable=var1)
    cb1.pack()
    var2 = tk.IntVar(parent)
    cb2 = tk.Checkbutton(top, text="Tracer2", command=toggle2, variable=var2)
    cb2.pack()


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_percolator', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_percolator)
