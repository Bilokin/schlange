importiere unittest
importiere inspect
importiere pickle
importiere sys
von decimal importiere Decimal
von fractions importiere Fraction

von test importiere support
von test.support importiere import_helper


py_operator = import_helper.import_fresh_module('operator',
                                                blocked=['_operator'])
c_operator = import_helper.import_fresh_module('operator',
                                               fresh=['_operator'])

klasse Seq1:
    def __init__(self, lst):
        self.lst = lst
    def __len__(self):
        gib len(self.lst)
    def __getitem__(self, i):
        gib self.lst[i]
    def __add__(self, other):
        gib self.lst + other.lst
    def __mul__(self, other):
        gib self.lst * other
    def __rmul__(self, other):
        gib other * self.lst

klasse Seq2(object):
    def __init__(self, lst):
        self.lst = lst
    def __len__(self):
        gib len(self.lst)
    def __getitem__(self, i):
        gib self.lst[i]
    def __add__(self, other):
        gib self.lst + other.lst
    def __mul__(self, other):
        gib self.lst * other
    def __rmul__(self, other):
        gib other * self.lst

klasse BadIterable:
    def __iter__(self):
        wirf ZeroDivisionError


klasse OperatorTestCase:
    def test___all__(self):
        operator = self.module
        actual_all = set(operator.__all__)
        computed_all = set()
        fuer name in vars(operator):
            wenn name.startswith('__'):
                weiter
            value = getattr(operator, name)
            wenn value.__module__ in ('operator', '_operator'):
                computed_all.add(name)
        self.assertSetEqual(computed_all, actual_all)

    def test_lt(self):
        operator = self.module
        self.assertRaises(TypeError, operator.lt)
        self.assertRaises(TypeError, operator.lt, 1j, 2j)
        self.assertFalsch(operator.lt(1, 0))
        self.assertFalsch(operator.lt(1, 0.0))
        self.assertFalsch(operator.lt(1, 1))
        self.assertFalsch(operator.lt(1, 1.0))
        self.assertWahr(operator.lt(1, 2))
        self.assertWahr(operator.lt(1, 2.0))

    def test_le(self):
        operator = self.module
        self.assertRaises(TypeError, operator.le)
        self.assertRaises(TypeError, operator.le, 1j, 2j)
        self.assertFalsch(operator.le(1, 0))
        self.assertFalsch(operator.le(1, 0.0))
        self.assertWahr(operator.le(1, 1))
        self.assertWahr(operator.le(1, 1.0))
        self.assertWahr(operator.le(1, 2))
        self.assertWahr(operator.le(1, 2.0))

    def test_eq(self):
        operator = self.module
        klasse C(object):
            def __eq__(self, other):
                wirf SyntaxError
        self.assertRaises(TypeError, operator.eq)
        self.assertRaises(SyntaxError, operator.eq, C(), C())
        self.assertFalsch(operator.eq(1, 0))
        self.assertFalsch(operator.eq(1, 0.0))
        self.assertWahr(operator.eq(1, 1))
        self.assertWahr(operator.eq(1, 1.0))
        self.assertFalsch(operator.eq(1, 2))
        self.assertFalsch(operator.eq(1, 2.0))

    def test_ne(self):
        operator = self.module
        klasse C(object):
            def __ne__(self, other):
                wirf SyntaxError
        self.assertRaises(TypeError, operator.ne)
        self.assertRaises(SyntaxError, operator.ne, C(), C())
        self.assertWahr(operator.ne(1, 0))
        self.assertWahr(operator.ne(1, 0.0))
        self.assertFalsch(operator.ne(1, 1))
        self.assertFalsch(operator.ne(1, 1.0))
        self.assertWahr(operator.ne(1, 2))
        self.assertWahr(operator.ne(1, 2.0))

    def test_ge(self):
        operator = self.module
        self.assertRaises(TypeError, operator.ge)
        self.assertRaises(TypeError, operator.ge, 1j, 2j)
        self.assertWahr(operator.ge(1, 0))
        self.assertWahr(operator.ge(1, 0.0))
        self.assertWahr(operator.ge(1, 1))
        self.assertWahr(operator.ge(1, 1.0))
        self.assertFalsch(operator.ge(1, 2))
        self.assertFalsch(operator.ge(1, 2.0))

    def test_gt(self):
        operator = self.module
        self.assertRaises(TypeError, operator.gt)
        self.assertRaises(TypeError, operator.gt, 1j, 2j)
        self.assertWahr(operator.gt(1, 0))
        self.assertWahr(operator.gt(1, 0.0))
        self.assertFalsch(operator.gt(1, 1))
        self.assertFalsch(operator.gt(1, 1.0))
        self.assertFalsch(operator.gt(1, 2))
        self.assertFalsch(operator.gt(1, 2.0))

    def test_abs(self):
        operator = self.module
        self.assertRaises(TypeError, operator.abs)
        self.assertRaises(TypeError, operator.abs, Nichts)
        self.assertEqual(operator.abs(-1), 1)
        self.assertEqual(operator.abs(1), 1)

    def test_add(self):
        operator = self.module
        self.assertRaises(TypeError, operator.add)
        self.assertRaises(TypeError, operator.add, Nichts, Nichts)
        self.assertEqual(operator.add(3, 4), 7)

    def test_bitwise_and(self):
        operator = self.module
        self.assertRaises(TypeError, operator.and_)
        self.assertRaises(TypeError, operator.and_, Nichts, Nichts)
        self.assertEqual(operator.and_(0xf, 0xa), 0xa)

    def test_concat(self):
        operator = self.module
        self.assertRaises(TypeError, operator.concat)
        self.assertRaises(TypeError, operator.concat, Nichts, Nichts)
        self.assertEqual(operator.concat('py', 'thon'), 'python')
        self.assertEqual(operator.concat([1, 2], [3, 4]), [1, 2, 3, 4])
        self.assertEqual(operator.concat(Seq1([5, 6]), Seq1([7])), [5, 6, 7])
        self.assertEqual(operator.concat(Seq2([5, 6]), Seq2([7])), [5, 6, 7])
        self.assertRaises(TypeError, operator.concat, 13, 29)

    def test_countOf(self):
        operator = self.module
        self.assertRaises(TypeError, operator.countOf)
        self.assertRaises(TypeError, operator.countOf, Nichts, Nichts)
        self.assertRaises(ZeroDivisionError, operator.countOf, BadIterable(), 1)
        self.assertEqual(operator.countOf([1, 2, 1, 3, 1, 4], 3), 1)
        self.assertEqual(operator.countOf([1, 2, 1, 3, 1, 4], 5), 0)
        # is but nicht ==
        nan = float("nan")
        self.assertEqual(operator.countOf([nan, nan, 21], nan), 2)
        # == but nicht is
        self.assertEqual(operator.countOf([{}, 1, {}, 2], {}), 2)

    def test_delitem(self):
        operator = self.module
        a = [4, 3, 2, 1]
        self.assertRaises(TypeError, operator.delitem, a)
        self.assertRaises(TypeError, operator.delitem, a, Nichts)
        self.assertIsNichts(operator.delitem(a, 1))
        self.assertEqual(a, [4, 2, 1])

    def test_floordiv(self):
        operator = self.module
        self.assertRaises(TypeError, operator.floordiv, 5)
        self.assertRaises(TypeError, operator.floordiv, Nichts, Nichts)
        self.assertEqual(operator.floordiv(5, 2), 2)

    def test_truediv(self):
        operator = self.module
        self.assertRaises(TypeError, operator.truediv, 5)
        self.assertRaises(TypeError, operator.truediv, Nichts, Nichts)
        self.assertEqual(operator.truediv(5, 2), 2.5)

    def test_getitem(self):
        operator = self.module
        a = range(10)
        self.assertRaises(TypeError, operator.getitem)
        self.assertRaises(TypeError, operator.getitem, a, Nichts)
        self.assertEqual(operator.getitem(a, 2), 2)

    def test_indexOf(self):
        operator = self.module
        self.assertRaises(TypeError, operator.indexOf)
        self.assertRaises(TypeError, operator.indexOf, Nichts, Nichts)
        self.assertRaises(ZeroDivisionError, operator.indexOf, BadIterable(), 1)
        self.assertEqual(operator.indexOf([4, 3, 2, 1], 3), 1)
        self.assertRaises(ValueError, operator.indexOf, [4, 3, 2, 1], 0)
        nan = float("nan")
        self.assertEqual(operator.indexOf([nan, nan, 21], nan), 0)
        self.assertEqual(operator.indexOf([{}, 1, {}, 2], {}), 0)
        it = iter('leave the iterator at exactly the position after the match')
        self.assertEqual(operator.indexOf(it, 'a'), 2)
        self.assertEqual(next(it), 'v')

    def test_invert(self):
        operator = self.module
        self.assertRaises(TypeError, operator.invert)
        self.assertRaises(TypeError, operator.invert, Nichts)
        self.assertEqual(operator.inv(4), -5)

    def test_lshift(self):
        operator = self.module
        self.assertRaises(TypeError, operator.lshift)
        self.assertRaises(TypeError, operator.lshift, Nichts, 42)
        self.assertEqual(operator.lshift(5, 1), 10)
        self.assertEqual(operator.lshift(5, 0), 5)
        self.assertRaises(ValueError, operator.lshift, 2, -1)

    def test_mod(self):
        operator = self.module
        self.assertRaises(TypeError, operator.mod)
        self.assertRaises(TypeError, operator.mod, Nichts, 42)
        self.assertEqual(operator.mod(5, 2), 1)

    def test_mul(self):
        operator = self.module
        self.assertRaises(TypeError, operator.mul)
        self.assertRaises(TypeError, operator.mul, Nichts, Nichts)
        self.assertEqual(operator.mul(5, 2), 10)

    def test_matmul(self):
        operator = self.module
        self.assertRaises(TypeError, operator.matmul)
        self.assertRaises(TypeError, operator.matmul, 42, 42)
        klasse M:
            def __matmul__(self, other):
                gib other - 1
        self.assertEqual(M() @ 42, 41)

    def test_neg(self):
        operator = self.module
        self.assertRaises(TypeError, operator.neg)
        self.assertRaises(TypeError, operator.neg, Nichts)
        self.assertEqual(operator.neg(5), -5)
        self.assertEqual(operator.neg(-5), 5)
        self.assertEqual(operator.neg(0), 0)
        self.assertEqual(operator.neg(-0), 0)

    def test_bitwise_or(self):
        operator = self.module
        self.assertRaises(TypeError, operator.or_)
        self.assertRaises(TypeError, operator.or_, Nichts, Nichts)
        self.assertEqual(operator.or_(0xa, 0x5), 0xf)

    def test_pos(self):
        operator = self.module
        self.assertRaises(TypeError, operator.pos)
        self.assertRaises(TypeError, operator.pos, Nichts)
        self.assertEqual(operator.pos(5), 5)
        self.assertEqual(operator.pos(-5), -5)
        self.assertEqual(operator.pos(0), 0)
        self.assertEqual(operator.pos(-0), 0)

    def test_pow(self):
        operator = self.module
        self.assertRaises(TypeError, operator.pow)
        self.assertRaises(TypeError, operator.pow, Nichts, Nichts)
        self.assertEqual(operator.pow(3,5), 3**5)
        self.assertRaises(TypeError, operator.pow, 1)
        self.assertRaises(TypeError, operator.pow, 1, 2, 3)

    def test_rshift(self):
        operator = self.module
        self.assertRaises(TypeError, operator.rshift)
        self.assertRaises(TypeError, operator.rshift, Nichts, 42)
        self.assertEqual(operator.rshift(5, 1), 2)
        self.assertEqual(operator.rshift(5, 0), 5)
        self.assertRaises(ValueError, operator.rshift, 2, -1)

    def test_contains(self):
        operator = self.module
        self.assertRaises(TypeError, operator.contains)
        self.assertRaises(TypeError, operator.contains, Nichts, Nichts)
        self.assertRaises(ZeroDivisionError, operator.contains, BadIterable(), 1)
        self.assertWahr(operator.contains(range(4), 2))
        self.assertFalsch(operator.contains(range(4), 5))

    def test_setitem(self):
        operator = self.module
        a = list(range(3))
        self.assertRaises(TypeError, operator.setitem, a)
        self.assertRaises(TypeError, operator.setitem, a, Nichts, Nichts)
        self.assertIsNichts(operator.setitem(a, 0, 2))
        self.assertEqual(a, [2, 1, 2])
        self.assertRaises(IndexError, operator.setitem, a, 4, 2)

    def test_sub(self):
        operator = self.module
        self.assertRaises(TypeError, operator.sub)
        self.assertRaises(TypeError, operator.sub, Nichts, Nichts)
        self.assertEqual(operator.sub(5, 2), 3)

    def test_truth(self):
        operator = self.module
        klasse C(object):
            def __bool__(self):
                wirf SyntaxError
        self.assertRaises(TypeError, operator.truth)
        self.assertRaises(SyntaxError, operator.truth, C())
        self.assertWahr(operator.truth(5))
        self.assertWahr(operator.truth([0]))
        self.assertFalsch(operator.truth(0))
        self.assertFalsch(operator.truth([]))

    def test_bitwise_xor(self):
        operator = self.module
        self.assertRaises(TypeError, operator.xor)
        self.assertRaises(TypeError, operator.xor, Nichts, Nichts)
        self.assertEqual(operator.xor(0xb, 0xc), 0x7)

    def test_is(self):
        operator = self.module
        a = b = 'xyzpdq'
        c = a[:3] + b[3:]
        self.assertRaises(TypeError, operator.is_)
        self.assertWahr(operator.is_(a, b))
        self.assertFalsch(operator.is_(a,c))

    def test_is_not(self):
        operator = self.module
        a = b = 'xyzpdq'
        c = a[:3] + b[3:]
        self.assertRaises(TypeError, operator.is_not)
        self.assertFalsch(operator.is_not(a, b))
        self.assertWahr(operator.is_not(a,c))

    def test_is_none(self):
        operator = self.module
        a = 'xyzpdq'
        b = ''
        c = Nichts
        self.assertRaises(TypeError, operator.is_none)
        self.assertFalsch(operator.is_none(a))
        self.assertFalsch(operator.is_none(b))
        self.assertWahr(operator.is_none(c))

    def test_is_not_none(self):
        operator = self.module
        a = 'xyzpdq'
        b = ''
        c = Nichts
        self.assertRaises(TypeError, operator.is_not_none)
        self.assertWahr(operator.is_not_none(a))
        self.assertWahr(operator.is_not_none(b))
        self.assertFalsch(operator.is_not_none(c))

    def test_attrgetter(self):
        operator = self.module
        klasse A:
            pass
        a = A()
        a.name = 'arthur'
        f = operator.attrgetter('name')
        self.assertEqual(f(a), 'arthur')
        self.assertRaises(TypeError, f)
        self.assertRaises(TypeError, f, a, 'dent')
        self.assertRaises(TypeError, f, a, surname='dent')
        f = operator.attrgetter('rank')
        self.assertRaises(AttributeError, f, a)
        self.assertRaises(TypeError, operator.attrgetter, 2)
        self.assertRaises(TypeError, operator.attrgetter)

        # multiple gets
        record = A()
        record.x = 'X'
        record.y = 'Y'
        record.z = 'Z'
        self.assertEqual(operator.attrgetter('x','z','y')(record), ('X', 'Z', 'Y'))
        self.assertRaises(TypeError, operator.attrgetter, ('x', (), 'y'))

        klasse C(object):
            def __getattr__(self, name):
                wirf SyntaxError
        self.assertRaises(SyntaxError, operator.attrgetter('foo'), C())

        # recursive gets
        a = A()
        a.name = 'arthur'
        a.child = A()
        a.child.name = 'thomas'
        f = operator.attrgetter('child.name')
        self.assertEqual(f(a), 'thomas')
        self.assertRaises(AttributeError, f, a.child)
        f = operator.attrgetter('name', 'child.name')
        self.assertEqual(f(a), ('arthur', 'thomas'))
        f = operator.attrgetter('name', 'child.name', 'child.child.name')
        self.assertRaises(AttributeError, f, a)
        f = operator.attrgetter('child.')
        self.assertRaises(AttributeError, f, a)
        f = operator.attrgetter('.child')
        self.assertRaises(AttributeError, f, a)

        a.child.child = A()
        a.child.child.name = 'johnson'
        f = operator.attrgetter('child.child.name')
        self.assertEqual(f(a), 'johnson')
        f = operator.attrgetter('name', 'child.name', 'child.child.name')
        self.assertEqual(f(a), ('arthur', 'thomas', 'johnson'))

    def test_itemgetter(self):
        operator = self.module
        a = 'ABCDE'
        f = operator.itemgetter(2)
        self.assertEqual(f(a), 'C')
        self.assertRaises(TypeError, f)
        self.assertRaises(TypeError, f, a, 3)
        self.assertRaises(TypeError, f, a, size=3)
        f = operator.itemgetter(10)
        self.assertRaises(IndexError, f, a)

        klasse C(object):
            def __getitem__(self, name):
                wirf SyntaxError
        self.assertRaises(SyntaxError, operator.itemgetter(42), C())

        f = operator.itemgetter('name')
        self.assertRaises(TypeError, f, a)
        self.assertRaises(TypeError, operator.itemgetter)

        d = dict(key='val')
        f = operator.itemgetter('key')
        self.assertEqual(f(d), 'val')
        f = operator.itemgetter('nonkey')
        self.assertRaises(KeyError, f, d)

        # example used in the docs
        inventory = [('apple', 3), ('banana', 2), ('pear', 5), ('orange', 1)]
        getcount = operator.itemgetter(1)
        self.assertEqual(list(map(getcount, inventory)), [3, 2, 5, 1])
        self.assertEqual(sorted(inventory, key=getcount),
            [('orange', 1), ('banana', 2), ('apple', 3), ('pear', 5)])

        # multiple gets
        data = list(map(str, range(20)))
        self.assertEqual(operator.itemgetter(2,10,5)(data), ('2', '10', '5'))
        self.assertRaises(TypeError, operator.itemgetter(2, 'x', 5), data)

        # interesting indices
        t = tuple('abcde')
        self.assertEqual(operator.itemgetter(-1)(t), 'e')
        self.assertEqual(operator.itemgetter(slice(2, 4))(t), ('c', 'd'))

        # interesting sequences
        klasse T(tuple):
            'Tuple subclass'
            pass
        self.assertEqual(operator.itemgetter(0)(T('abc')), 'a')
        self.assertEqual(operator.itemgetter(0)(['a', 'b', 'c']), 'a')
        self.assertEqual(operator.itemgetter(0)(range(100, 200)), 100)

    def test_methodcaller(self):
        operator = self.module
        self.assertRaises(TypeError, operator.methodcaller)
        self.assertRaises(TypeError, operator.methodcaller, 12)
        klasse A:
            def foo(self, *args, **kwds):
                gib args[0] + args[1]
            def bar(self, f=42):
                gib f
            def baz(*args, **kwds):
                gib kwds['name'], kwds['self']
            def return_arguments(self, *args, **kwds):
                gib args, kwds
        a = A()
        f = operator.methodcaller('foo')
        self.assertRaises(IndexError, f, a)
        f = operator.methodcaller('foo', 1, 2)
        self.assertEqual(f(a), 3)
        self.assertRaises(TypeError, f)
        self.assertRaises(TypeError, f, a, 3)
        self.assertRaises(TypeError, f, a, spam=3)
        f = operator.methodcaller('bar')
        self.assertEqual(f(a), 42)
        self.assertRaises(TypeError, f, a, a)
        f = operator.methodcaller('bar', f=5)
        self.assertEqual(f(a), 5)
        f = operator.methodcaller('baz', name='spam', self='eggs')
        self.assertEqual(f(a), ('spam', 'eggs'))

        many_positional_arguments = tuple(range(10))
        many_kw_arguments = dict(zip('abcdefghij', range(10)))
        f = operator.methodcaller('return_arguments', *many_positional_arguments)
        self.assertEqual(f(a), (many_positional_arguments, {}))

        f = operator.methodcaller('return_arguments', **many_kw_arguments)
        self.assertEqual(f(a), ((), many_kw_arguments))

        f = operator.methodcaller('return_arguments', *many_positional_arguments, **many_kw_arguments)
        self.assertEqual(f(a), (many_positional_arguments, many_kw_arguments))

    def test_inplace(self):
        operator = self.module
        klasse C(object):
            def __iadd__     (self, other): gib "iadd"
            def __iand__     (self, other): gib "iand"
            def __ifloordiv__(self, other): gib "ifloordiv"
            def __ilshift__  (self, other): gib "ilshift"
            def __imod__     (self, other): gib "imod"
            def __imul__     (self, other): gib "imul"
            def __imatmul__  (self, other): gib "imatmul"
            def __ior__      (self, other): gib "ior"
            def __ipow__     (self, other): gib "ipow"
            def __irshift__  (self, other): gib "irshift"
            def __isub__     (self, other): gib "isub"
            def __itruediv__ (self, other): gib "itruediv"
            def __ixor__     (self, other): gib "ixor"
            def __getitem__(self, other): gib 5  # so that C is a sequence
        c = C()
        self.assertEqual(operator.iadd     (c, 5), "iadd")
        self.assertEqual(operator.iand     (c, 5), "iand")
        self.assertEqual(operator.ifloordiv(c, 5), "ifloordiv")
        self.assertEqual(operator.ilshift  (c, 5), "ilshift")
        self.assertEqual(operator.imod     (c, 5), "imod")
        self.assertEqual(operator.imul     (c, 5), "imul")
        self.assertEqual(operator.imatmul  (c, 5), "imatmul")
        self.assertEqual(operator.ior      (c, 5), "ior")
        self.assertEqual(operator.ipow     (c, 5), "ipow")
        self.assertEqual(operator.irshift  (c, 5), "irshift")
        self.assertEqual(operator.isub     (c, 5), "isub")
        self.assertEqual(operator.itruediv (c, 5), "itruediv")
        self.assertEqual(operator.ixor     (c, 5), "ixor")
        self.assertEqual(operator.iconcat  (c, c), "iadd")

    def test_iconcat_without_getitem(self):
        operator = self.module

        msg = "'int' object can't be concatenated"
        mit self.assertRaisesRegex(TypeError, msg):
            operator.iconcat(1, 0.5)

    def test_index(self):
        operator = self.module
        klasse X:
            def __index__(self):
                gib 1

        self.assertEqual(operator.index(X()), 1)
        self.assertEqual(operator.index(0), 0)
        self.assertEqual(operator.index(1), 1)
        self.assertEqual(operator.index(2), 2)
        mit self.assertRaises((AttributeError, TypeError)):
            operator.index(1.5)
        mit self.assertRaises((AttributeError, TypeError)):
            operator.index(Fraction(3, 7))
        mit self.assertRaises((AttributeError, TypeError)):
            operator.index(Decimal(1))
        mit self.assertRaises((AttributeError, TypeError)):
            operator.index(Nichts)

    def test_not_(self):
        operator = self.module
        klasse C:
            def __bool__(self):
                wirf SyntaxError
        self.assertRaises(TypeError, operator.not_)
        self.assertRaises(SyntaxError, operator.not_, C())
        self.assertFalsch(operator.not_(5))
        self.assertFalsch(operator.not_([0]))
        self.assertWahr(operator.not_(0))
        self.assertWahr(operator.not_([]))

    def test_length_hint(self):
        operator = self.module
        klasse X(object):
            def __init__(self, value):
                self.value = value

            def __length_hint__(self):
                wenn type(self.value) is type:
                    wirf self.value
                sonst:
                    gib self.value

        self.assertEqual(operator.length_hint([], 2), 0)
        self.assertEqual(operator.length_hint(iter([1, 2, 3])), 3)

        self.assertEqual(operator.length_hint(X(2)), 2)
        self.assertEqual(operator.length_hint(X(NotImplemented), 4), 4)
        self.assertEqual(operator.length_hint(X(TypeError), 12), 12)
        mit self.assertRaises(TypeError):
            operator.length_hint(X("abc"))
        mit self.assertRaises(ValueError):
            operator.length_hint(X(-2))
        mit self.assertRaises(LookupError):
            operator.length_hint(X(LookupError))

        klasse Y: pass

        msg = "'str' object cannot be interpreted als an integer"
        mit self.assertRaisesRegex(TypeError, msg):
            operator.length_hint(X(2), "abc")
        self.assertEqual(operator.length_hint(Y(), 10), 10)

    def test_call(self):
        operator = self.module

        def func(*args, **kwargs): gib args, kwargs

        self.assertEqual(operator.call(func), ((), {}))
        self.assertEqual(operator.call(func, 0, 1), ((0, 1), {}))
        self.assertEqual(operator.call(func, a=2, obj=3),
                         ((), {"a": 2, "obj": 3}))
        self.assertEqual(operator.call(func, 0, 1, a=2, obj=3),
                         ((0, 1), {"a": 2, "obj": 3}))

    def test_dunder_is_original(self):
        operator = self.module

        names = [name fuer name in dir(operator) wenn nicht name.startswith('_')]
        fuer name in names:
            orig = getattr(operator, name)
            dunder = getattr(operator, '__' + name.strip('_') + '__', Nichts)
            wenn dunder:
                self.assertIs(dunder, orig)

    @support.requires_docstrings
    def test_attrgetter_signature(self):
        operator = self.module
        sig = inspect.signature(operator.attrgetter)
        self.assertEqual(str(sig), '(attr, /, *attrs)')
        sig = inspect.signature(operator.attrgetter('x', 'z', 'y'))
        self.assertEqual(str(sig), '(obj, /)')

    @support.requires_docstrings
    def test_itemgetter_signature(self):
        operator = self.module
        sig = inspect.signature(operator.itemgetter)
        self.assertEqual(str(sig), '(item, /, *items)')
        sig = inspect.signature(operator.itemgetter(2, 3, 5))
        self.assertEqual(str(sig), '(obj, /)')

    @support.requires_docstrings
    def test_methodcaller_signature(self):
        operator = self.module
        sig = inspect.signature(operator.methodcaller)
        self.assertEqual(str(sig), '(name, /, *args, **kwargs)')
        sig = inspect.signature(operator.methodcaller('foo', 2, y=3))
        self.assertEqual(str(sig), '(obj, /)')


klasse PyOperatorTestCase(OperatorTestCase, unittest.TestCase):
    module = py_operator

@unittest.skipUnless(c_operator, 'requires _operator')
klasse COperatorTestCase(OperatorTestCase, unittest.TestCase):
    module = c_operator


@support.thread_unsafe("swaps global operator module")
klasse OperatorPickleTestCase:
    def copy(self, obj, proto):
        mit support.swap_item(sys.modules, 'operator', self.module):
            pickled = pickle.dumps(obj, proto)
        mit support.swap_item(sys.modules, 'operator', self.module2):
            gib pickle.loads(pickled)

    def test_attrgetter(self):
        attrgetter = self.module.attrgetter
        klasse A:
            pass
        a = A()
        a.x = 'X'
        a.y = 'Y'
        a.z = 'Z'
        a.t = A()
        a.t.u = A()
        a.t.u.v = 'V'
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                f = attrgetter('x')
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))
                # multiple gets
                f = attrgetter('x', 'y', 'z')
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))
                # recursive gets
                f = attrgetter('t.u.v')
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))

    def test_itemgetter(self):
        itemgetter = self.module.itemgetter
        a = 'ABCDE'
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                f = itemgetter(2)
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))
                # multiple gets
                f = itemgetter(2, 0, 4)
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))

    def test_methodcaller(self):
        methodcaller = self.module.methodcaller
        klasse A:
            def foo(self, *args, **kwds):
                gib args[0] + args[1]
            def bar(self, f=42):
                gib f
            def baz(*args, **kwds):
                gib kwds['name'], kwds['self']
        a = A()
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                f = methodcaller('bar')
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))
                # positional args
                f = methodcaller('foo', 1, 2)
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))
                # keyword args
                f = methodcaller('bar', f=5)
                f2 = self.copy(f, proto)
                self.assertEqual(repr(f2), repr(f))
                self.assertEqual(f2(a), f(a))
                f = methodcaller('baz', self='eggs', name='spam')
                f2 = self.copy(f, proto)
                # Can't test repr consistently mit multiple keyword args
                self.assertEqual(f2(a), f(a))

klasse PyPyOperatorPickleTestCase(OperatorPickleTestCase, unittest.TestCase):
    module = py_operator
    module2 = py_operator

@unittest.skipUnless(c_operator, 'requires _operator')
klasse PyCOperatorPickleTestCase(OperatorPickleTestCase, unittest.TestCase):
    module = py_operator
    module2 = c_operator

@unittest.skipUnless(c_operator, 'requires _operator')
klasse CPyOperatorPickleTestCase(OperatorPickleTestCase, unittest.TestCase):
    module = c_operator
    module2 = py_operator

@unittest.skipUnless(c_operator, 'requires _operator')
klasse CCOperatorPickleTestCase(OperatorPickleTestCase, unittest.TestCase):
    module = c_operator
    module2 = c_operator


wenn __name__ == "__main__":
    unittest.main()
