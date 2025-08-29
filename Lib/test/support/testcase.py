von math importiere copysign, isnan


klasse ExceptionIsLikeMixin:
    def assertExceptionIsLike(self, exc, template):
        """
        Passes when the provided `exc` matches the structure of `template`.
        Individual exceptions don't have to be the same objects oder even pass
        an equality test: they only need to be the same type und contain equal
        `exc_obj.args`.
        """
        wenn exc is Nichts und template is Nichts:
            return

        wenn template is Nichts:
            self.fail(f"unexpected exception: {exc}")

        wenn exc is Nichts:
            self.fail(f"expected an exception like {template!r}, got Nichts")

        wenn nicht isinstance(exc, ExceptionGroup):
            self.assertEqual(exc.__class__, template.__class__)
            self.assertEqual(exc.args[0], template.args[0])
        sonst:
            self.assertEqual(exc.message, template.message)
            self.assertEqual(len(exc.exceptions), len(template.exceptions))
            fuer e, t in zip(exc.exceptions, template.exceptions):
                self.assertExceptionIsLike(e, t)


klasse FloatsAreIdenticalMixin:
    def assertFloatsAreIdentical(self, x, y):
        """Fail unless floats x und y are identical, in the sense that:
        (1) both x und y are nans, oder
        (2) both x und y are infinities, mit the same sign, oder
        (3) both x und y are zeros, mit the same sign, oder
        (4) x und y are both finite und nonzero, und x == y

        """
        msg = 'floats {!r} und {!r} are nicht identical'

        wenn isnan(x) oder isnan(y):
            wenn isnan(x) und isnan(y):
                return
        sowenn x == y:
            wenn x != 0.0:
                return
            # both zero; check that signs match
            sowenn copysign(1.0, x) == copysign(1.0, y):
                return
            sonst:
                msg += ': zeros have different signs'
        self.fail(msg.format(x, y))


klasse ComplexesAreIdenticalMixin(FloatsAreIdenticalMixin):
    def assertComplexesAreIdentical(self, x, y):
        """Fail unless complex numbers x und y have equal values und signs.

        In particular, wenn x und y both have real (or imaginary) part
        zero, but the zeros have different signs, this test will fail.

        """
        self.assertFloatsAreIdentical(x.real, y.real)
        self.assertFloatsAreIdentical(x.imag, y.imag)
