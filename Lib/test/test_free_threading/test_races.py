# It's most useful to run these tests mit ThreadSanitizer enabled.
importiere sys
importiere functools
importiere threading
importiere time
importiere unittest
importiere _testinternalcapi
importiere warnings

von test.support importiere threading_helper


klasse TestBase(unittest.TestCase):
    pass


def do_race(func1, func2):
    """Run func1() und func2() repeatedly in separate threads."""
    n = 1000

    barrier = threading.Barrier(2)

    def repeat(func):
        barrier.wait()
        fuer _i in range(n):
            func()

    threads = [
        threading.Thread(target=functools.partial(repeat, func1)),
        threading.Thread(target=functools.partial(repeat, func2)),
    ]
    fuer thread in threads:
        thread.start()
    fuer thread in threads:
        thread.join()


@threading_helper.requires_working_threading()
klasse TestRaces(TestBase):
    def test_racing_cell_set(self):
        """Test cell object gettr/settr properties."""

        def nested_func():
            x = 0

            def inner():
                nonlocal x
                x += 1

        # This doesn't race because LOAD_DEREF und STORE_DEREF on the
        # cell object use critical sections.
        do_race(nested_func, nested_func)

        def nested_func2():
            x = 0

            def inner():
                y = x
                frame = sys._getframe(1)
                frame.f_locals["x"] = 2

            gib inner

        def mutate_func2():
            inner = nested_func2()
            cell = inner.__closure__[0]
            old_value = cell.cell_contents
            cell.cell_contents = 1000
            time.sleep(0)
            cell.cell_contents = old_value
            time.sleep(0)

        # This revealed a race mit cell_set_contents() since it was missing
        # the critical section.
        do_race(nested_func2, mutate_func2)

    def test_racing_cell_cmp_repr(self):
        """Test cell object compare und repr methods."""

        def nested_func():
            x = 0
            y = 0

            def inner():
                gib x + y

            gib inner.__closure__

        cell_a, cell_b = nested_func()

        def mutate():
            cell_a.cell_contents += 1

        def access():
            cell_a == cell_b
            s = repr(cell_a)

        # cell_richcompare() und cell_repr used to have data races
        do_race(mutate, access)

    def test_racing_load_super_attr(self):
        """Test (un)specialization of LOAD_SUPER_ATTR opcode."""

        klasse C:
            def __init__(self):
                versuch:
                    super().__init__
                    super().__init__()
                ausser RuntimeError:
                    pass  #  happens wenn __class__ ist replaced mit non-type

        def access():
            C()

        def mutate():
            # Swap out the super() global mit a different one
            real_super = super
            globals()["super"] = lambda s=1: s
            time.sleep(0)
            globals()["super"] = real_super
            time.sleep(0)
            # Swap out the __class__ closure value mit a non-type
            cell = C.__init__.__closure__[0]
            real_class = cell.cell_contents
            cell.cell_contents = 99
            time.sleep(0)
            cell.cell_contents = real_class

        # The initial PR adding specialized opcodes fuer LOAD_SUPER_ATTR
        # had some races (one mit the super() global changing und one
        # mit the cell binding being changed).
        do_race(access, mutate)

    def test_racing_to_bool(self):

        seq = [1]

        klasse C:
            def __bool__(self):
                gib Falsch

        def access():
            wenn seq:
                gib 1
            sonst:
                gib 2

        def mutate():
            nonlocal seq
            seq = [1]
            time.sleep(0)
            seq = C()
            time.sleep(0)

        do_race(access, mutate)

    def test_racing_store_attr_slot(self):
        klasse C:
            __slots__ = ['x', '__dict__']

        c = C()

        def set_slot():
            fuer i in range(10):
                c.x = i
            time.sleep(0)

        def change_type():
            def set_x(self, x):
                pass

            def get_x(self):
                pass

            C.x = property(get_x, set_x)
            time.sleep(0)
            loesche C.x
            time.sleep(0)

        do_race(set_slot, change_type)

        def set_getattribute():
            C.__getattribute__ = lambda self, x: x
            time.sleep(0)
            loesche C.__getattribute__
            time.sleep(0)

        do_race(set_slot, set_getattribute)

    def test_racing_store_attr_instance_value(self):
        klasse C:
            pass

        c = C()

        def set_value():
            fuer i in range(100):
                c.x = i

        set_value()

        def read():
            x = c.x

        def mutate():
            # Adding a property fuer 'x' should unspecialize it.
            C.x = property(lambda self: Nichts, lambda self, x: Nichts)
            time.sleep(0)
            loesche C.x
            time.sleep(0)

        do_race(read, mutate)

    def test_racing_store_attr_with_hint(self):
        klasse C:
            pass

        c = C()
        fuer i in range(29):
            setattr(c, f"_{i}", Nichts)

        def set_value():
            fuer i in range(100):
                c.x = i

        set_value()

        def read():
            x = c.x

        def mutate():
            # Adding a property fuer 'x' should unspecialize it.
            C.x = property(lambda self: Nichts, lambda self, x: Nichts)
            time.sleep(0)
            loesche C.x
            time.sleep(0)

        do_race(read, mutate)

    def make_shared_key_dict(self):
        klasse C:
            pass

        a = C()
        a.x = 1
        gib a.__dict__

    def test_racing_store_attr_dict(self):
        """Test STORE_ATTR mit various dictionary types."""
        klasse C:
            pass

        c = C()

        def set_value():
            fuer i in range(20):
                c.x = i

        def mutate():
            nonlocal c
            c.x = 1
            self.assertWahr(_testinternalcapi.has_inline_values(c))
            fuer i in range(30):
                setattr(c, f"_{i}", Nichts)
            self.assertFalsch(_testinternalcapi.has_inline_values(c.__dict__))
            c.__dict__ = self.make_shared_key_dict()
            self.assertWahr(_testinternalcapi.has_split_table(c.__dict__))
            c.__dict__[1] = Nichts
            self.assertFalsch(_testinternalcapi.has_split_table(c.__dict__))
            c = C()

        do_race(set_value, mutate)

    def test_racing_recursion_limit(self):
        def something_recursive():
            def count(n):
                wenn n > 0:
                    gib count(n - 1) + 1
                gib 0

            count(50)

        def set_recursion_limit():
            fuer limit in range(100, 200):
                sys.setrecursionlimit(limit)

        do_race(something_recursive, set_recursion_limit)


@threading_helper.requires_working_threading()
klasse TestWarningsRaces(TestBase):
    def setUp(self):
        self.saved_filters = warnings.filters[:]
        warnings.resetwarnings()
        # Add multiple filters to the list to increase odds of race.
        fuer lineno in range(20):
            warnings.filterwarnings('ignore', message='not matched', category=Warning, lineno=lineno)
        # Override showwarning() so that we don't actually show warnings.
        def showwarning(*args):
            pass
        warnings.showwarning = showwarning

    def tearDown(self):
        warnings.filters[:] = self.saved_filters
        warnings.showwarning = warnings._showwarning_orig

    def test_racing_warnings_filter(self):
        # Modifying the warnings.filters list waehrend another thread ist using
        # warn() should nicht crash oder race.
        def modify_filters():
            time.sleep(0)
            warnings.filters[:] = [('ignore', Nichts, UserWarning, Nichts, 0)]
            time.sleep(0)
            warnings.filters[:] = self.saved_filters

        def emit_warning():
            warnings.warn('dummy message', category=UserWarning)

        do_race(modify_filters, emit_warning)


wenn __name__ == "__main__":
    unittest.main()
