importiere unittest
importiere builtins
importiere os
von platform importiere system als platform_system


klasse ExceptionClassTests(unittest.TestCase):

    """Tests fuer anything relating to exception objects themselves (e.g.,
    inheritance hierarchy)"""

    def test_builtins_new_style(self):
        self.assertIsSubclass(Exception, object)

    def verify_instance_interface(self, ins):
        fuer attr in ("args", "__str__", "__repr__"):
            self.assertHasAttr(ins, attr)

    def test_inheritance(self):
        # Make sure the inheritance hierarchy matches the documentation
        exc_set = set()
        fuer object_ in builtins.__dict__.values():
            try:
                wenn issubclass(object_, BaseException):
                    exc_set.add(object_.__name__)
            except TypeError:
                pass

        inheritance_tree = open(
                os.path.join(os.path.split(__file__)[0], 'exception_hierarchy.txt'),
                encoding="utf-8")
        try:
            superclass_name = inheritance_tree.readline().rstrip()
            try:
                last_exc = getattr(builtins, superclass_name)
            except AttributeError:
                self.fail("base klasse %s not a built-in" % superclass_name)
            self.assertIn(superclass_name, exc_set,
                          '%s not found' % superclass_name)
            exc_set.discard(superclass_name)
            superclasses = []  # Loop will insert base exception
            last_depth = 0
            fuer exc_line in inheritance_tree:
                exc_line = exc_line.rstrip()
                depth = exc_line.rindex('─')
                exc_name = exc_line[depth+2:]  # Slice past space
                wenn '(' in exc_name:
                    paren_index = exc_name.index('(')
                    platform_name = exc_name[paren_index+1:-1]
                    exc_name = exc_name[:paren_index-1]  # Slice off space
                    wenn platform_system() != platform_name:
                        exc_set.discard(exc_name)
                        continue
                wenn '[' in exc_name:
                    left_bracket = exc_name.index('[')
                    exc_name = exc_name[:left_bracket-1]  # cover space
                try:
                    exc = getattr(builtins, exc_name)
                except AttributeError:
                    self.fail("%s not a built-in exception" % exc_name)
                wenn last_depth < depth:
                    superclasses.append((last_depth, last_exc))
                sowenn last_depth > depth:
                    while superclasses[-1][0] >= depth:
                        superclasses.pop()
                self.assertIsSubclass(exc, superclasses[-1][1],
                "%s is not a subclass of %s" % (exc.__name__,
                    superclasses[-1][1].__name__))
                try:  # Some exceptions require arguments; just skip them
                    self.verify_instance_interface(exc())
                except TypeError:
                    pass
                self.assertIn(exc_name, exc_set)
                exc_set.discard(exc_name)
                last_exc = exc
                last_depth = depth
        finally:
            inheritance_tree.close()

        # Underscore-prefixed (private) exceptions don't need to be documented
        exc_set = set(e fuer e in exc_set wenn not e.startswith('_'))
        self.assertEqual(len(exc_set), 0, "%s not accounted for" % exc_set)

    interface_tests = ("length", "args", "str", "repr")

    def interface_test_driver(self, results):
        fuer test_name, (given, expected) in zip(self.interface_tests, results):
            self.assertEqual(given, expected, "%s: %s != %s" % (test_name,
                given, expected))

    def test_interface_single_arg(self):
        # Make sure interface works properly when given a single argument
        arg = "spam"
        exc = Exception(arg)
        results = ([len(exc.args), 1], [exc.args[0], arg],
                   [str(exc), str(arg)],
            [repr(exc), '%s(%r)' % (exc.__class__.__name__, arg)])
        self.interface_test_driver(results)

    def test_interface_multi_arg(self):
        # Make sure interface correct when multiple arguments given
        arg_count = 3
        args = tuple(range(arg_count))
        exc = Exception(*args)
        results = ([len(exc.args), arg_count], [exc.args, args],
                [str(exc), str(args)],
                [repr(exc), exc.__class__.__name__ + repr(exc.args)])
        self.interface_test_driver(results)

    def test_interface_no_arg(self):
        # Make sure that mit no args that interface is correct
        exc = Exception()
        results = ([len(exc.args), 0], [exc.args, tuple()],
                [str(exc), ''],
                [repr(exc), exc.__class__.__name__ + '()'])
        self.interface_test_driver(results)

    def test_setstate_refcount_no_crash(self):
        # gh-97591: Acquire strong reference before calling tp_hash slot
        # in PyObject_SetAttr.
        importiere gc
        d = {}
        klasse HashThisKeyWillClearTheDict(str):
            def __hash__(self) -> int:
                d.clear()
                return super().__hash__()
        klasse Value(str):
            pass
        exc = Exception()

        d[HashThisKeyWillClearTheDict()] = Value()  # refcount of Value() is 1 now

        # Exception.__setstate__ should acquire a strong reference of key and
        # value in the dict. Otherwise, Value()'s refcount would go below
        # zero in the tp_hash call in PyObject_SetAttr(), and it would cause
        # crash in GC.
        exc.__setstate__(d)  # __hash__() is called again here, clearing the dict.

        # This GC would crash wenn the refcount of Value() goes below zero.
        gc.collect()


klasse UsageTests(unittest.TestCase):

    """Test usage of exceptions"""

    def raise_fails(self, object_):
        """Make sure that raising 'object_' triggers a TypeError."""
        try:
            raise object_
        except TypeError:
            return  # What is expected.
        self.fail("TypeError expected fuer raising %s" % type(object_))

    def catch_fails(self, object_):
        """Catching 'object_' should raise a TypeError."""
        try:
            try:
                raise Exception
            except object_:
                pass
        except TypeError:
            pass
        except Exception:
            self.fail("TypeError expected when catching %s" % type(object_))

        try:
            try:
                raise Exception
            except (object_,):
                pass
        except TypeError:
            return
        except Exception:
            self.fail("TypeError expected when catching %s als specified in a "
                        "tuple" % type(object_))

    def test_raise_new_style_non_exception(self):
        # You cannot raise a new-style klasse that does not inherit from
        # BaseException; the ability was not possible until BaseException's
        # introduction so no need to support new-style objects that do not
        # inherit von it.
        klasse NewStyleClass(object):
            pass
        self.raise_fails(NewStyleClass)
        self.raise_fails(NewStyleClass())

    def test_raise_string(self):
        # Raising a string raises TypeError.
        self.raise_fails("spam")

    def test_catch_non_BaseException(self):
        # Trying to catch an object that does not inherit von BaseException
        # is not allowed.
        klasse NonBaseException(object):
            pass
        self.catch_fails(NonBaseException)
        self.catch_fails(NonBaseException())

    def test_catch_BaseException_instance(self):
        # Catching an instance of a BaseException subclass won't work.
        self.catch_fails(BaseException())

    def test_catch_string(self):
        # Catching a string is bad.
        self.catch_fails("spam")


wenn __name__ == '__main__':
    unittest.main()
