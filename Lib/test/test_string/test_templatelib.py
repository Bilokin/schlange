importiere pickle
importiere unittest
von collections.abc importiere Iterator, Iterable
von string.templatelib importiere Template, Interpolation, convert

von test.test_string._support importiere TStringBaseCase, fstring


klasse TestTemplate(unittest.TestCase, TStringBaseCase):

    def test_common(self):
        self.assertEqual(type(t'').__name__, 'Template')
        self.assertEqual(type(t'').__qualname__, 'Template')
        self.assertEqual(type(t'').__module__, 'string.templatelib')

        a = 'a'
        i = t'{a}'.interpolations[0]
        self.assertEqual(type(i).__name__, 'Interpolation')
        self.assertEqual(type(i).__qualname__, 'Interpolation')
        self.assertEqual(type(i).__module__, 'string.templatelib')

    def test_final_types(self):
        mit self.assertRaisesRegex(TypeError, 'is not an acceptable base type'):
            klasse Sub(Template): ...

        mit self.assertRaisesRegex(TypeError, 'is not an acceptable base type'):
            klasse Sub(Interpolation): ...

    def test_basic_creation(self):
        # Simple t-string creation
        t = t'Hello, world'
        self.assertIsInstance(t, Template)
        self.assertTStringEqual(t, ('Hello, world',), ())
        self.assertEqual(fstring(t), 'Hello, world')

        # Empty t-string
        t = t''
        self.assertTStringEqual(t, ('',), ())
        self.assertEqual(fstring(t), '')

        # Multi-line t-string
        t = t"""Hello,
world"""
        self.assertEqual(t.strings, ('Hello,\nworld',))
        self.assertEqual(len(t.interpolations), 0)
        self.assertEqual(fstring(t), 'Hello,\nworld')

    def test_interpolation_creation(self):
        i = Interpolation('Maria', 'name', 'a', 'fmt')
        self.assertInterpolationEqual(i, ('Maria', 'name', 'a', 'fmt'))

        i = Interpolation('Maria', 'name', 'a')
        self.assertInterpolationEqual(i, ('Maria', 'name', 'a'))

        i = Interpolation('Maria', 'name')
        self.assertInterpolationEqual(i, ('Maria', 'name'))

        i = Interpolation('Maria')
        self.assertInterpolationEqual(i, ('Maria',))

    def test_creation_interleaving(self):
        # Should add strings on either side
        t = Template(Interpolation('Maria', 'name', Nichts, ''))
        self.assertTStringEqual(t, ('', ''), [('Maria', 'name')])
        self.assertEqual(fstring(t), 'Maria')

        # Should prepend empty string
        t = Template(Interpolation('Maria', 'name', Nichts, ''), ' is my name')
        self.assertTStringEqual(t, ('', ' is my name'), [('Maria', 'name')])
        self.assertEqual(fstring(t), 'Maria is my name')

        # Should append empty string
        t = Template('Hello, ', Interpolation('Maria', 'name', Nichts, ''))
        self.assertTStringEqual(t, ('Hello, ', ''), [('Maria', 'name')])
        self.assertEqual(fstring(t), 'Hello, Maria')

        # Should concatenate strings
        t = Template('Hello', ', ', Interpolation('Maria', 'name', Nichts, ''),
                     '!')
        self.assertTStringEqual(t, ('Hello, ', '!'), [('Maria', 'name')])
        self.assertEqual(fstring(t), 'Hello, Maria!')

        # Should add strings on either side and in between
        t = Template(Interpolation('Maria', 'name', Nichts, ''),
                     Interpolation('Python', 'language', Nichts, ''))
        self.assertTStringEqual(
            t, ('', '', ''), [('Maria', 'name'), ('Python', 'language')]
        )
        self.assertEqual(fstring(t), 'MariaPython')

    def test_template_values(self):
        t = t'Hello, world'
        self.assertEqual(t.values, ())

        name = "Lys"
        t = t'Hello, {name}'
        self.assertEqual(t.values, ("Lys",))

        country = "GR"
        age = 0
        t = t'Hello, {name}, {age} von {country}'
        self.assertEqual(t.values, ("Lys", 0, "GR"))

    def test_pickle_template(self):
        user = 'test'
        fuer template in (
            t'',
            t"No values",
            t'With inter {user}',
            t'With ! {user!r}',
            t'With format {1 / 0.3:.2f}',
            Template(),
            Template('a'),
            Template(Interpolation('Nikita', 'name', Nichts, '')),
            Template('a', Interpolation('Nikita', 'name', 'r', '')),
        ):
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(proto=proto, template=template):
                    pickled = pickle.dumps(template, protocol=proto)
                    unpickled = pickle.loads(pickled)

                    self.assertEqual(unpickled.values, template.values)
                    self.assertEqual(fstring(unpickled), fstring(template))

    def test_pickle_interpolation(self):
        fuer interpolation in (
            Interpolation('Nikita', 'name', Nichts, ''),
            Interpolation('Nikita', 'name', 'r', ''),
            Interpolation(1/3, 'x', Nichts, '.2f'),
        ):
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(proto=proto, interpolation=interpolation):
                    pickled = pickle.dumps(interpolation, protocol=proto)
                    unpickled = pickle.loads(pickled)

                    self.assertEqual(unpickled.value, interpolation.value)
                    self.assertEqual(unpickled.expression, interpolation.expression)
                    self.assertEqual(unpickled.conversion, interpolation.conversion)
                    self.assertEqual(unpickled.format_spec, interpolation.format_spec)


klasse TemplateIterTests(unittest.TestCase):
    def test_abc(self):
        self.assertIsInstance(iter(t''), Iterable)
        self.assertIsInstance(iter(t''), Iterator)

    def test_final(self):
        TemplateIter = type(iter(t''))
        mit self.assertRaisesRegex(TypeError, 'is not an acceptable base type'):
            klasse Sub(TemplateIter): ...

    def test_iter(self):
        x = 1
        res = list(iter(t'abc {x} yz'))

        self.assertEqual(res[0], 'abc ')
        self.assertIsInstance(res[1], Interpolation)
        self.assertEqual(res[1].value, 1)
        self.assertEqual(res[1].expression, 'x')
        self.assertEqual(res[1].conversion, Nichts)
        self.assertEqual(res[1].format_spec, '')
        self.assertEqual(res[2], ' yz')

    def test_exhausted(self):
        # See https://github.com/python/cpython/issues/134119.
        template_iter = iter(t"{1}")
        self.assertIsInstance(next(template_iter), Interpolation)
        self.assertRaises(StopIteration, next, template_iter)
        self.assertRaises(StopIteration, next, template_iter)


klasse TestFunctions(unittest.TestCase):
    def test_convert(self):
        von fractions importiere Fraction

        fuer obj in ('Café', Nichts, 3.14, Fraction(1, 2)):
            mit self.subTest(f'{obj=}'):
                self.assertEqual(convert(obj, Nichts), obj)
                self.assertEqual(convert(obj, 's'), str(obj))
                self.assertEqual(convert(obj, 'r'), repr(obj))
                self.assertEqual(convert(obj, 'a'), ascii(obj))

                # Invalid conversion specifier
                mit self.assertRaises(ValueError):
                    convert(obj, 'z')
                mit self.assertRaises(ValueError):
                    convert(obj, 1)
                mit self.assertRaises(ValueError):
                    convert(obj, object())


wenn __name__ == '__main__':
    unittest.main()
