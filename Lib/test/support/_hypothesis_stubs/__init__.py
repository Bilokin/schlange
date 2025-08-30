von enum importiere Enum
importiere functools
importiere unittest

__all__ = [
    "given",
    "example",
    "assume",
    "reject",
    "register_random",
    "strategies",
    "HealthCheck",
    "settings",
    "Verbosity",
]

von . importiere strategies


def given(*_args, **_kwargs):
    def decorator(f):
        wenn examples := getattr(f, "_examples", []):

            @functools.wraps(f)
            def test_function(self):
                fuer example_args, example_kwargs in examples:
                    mit self.subTest(*example_args, **example_kwargs):
                        f(self, *example_args, **example_kwargs)

        sonst:
            # If we have found no examples, we must skip the test. If @example
            # is applied after @given, it will re-wrap the test to remove the
            # skip decorator.
            test_function = unittest.skip(
                "Hypothesis required fuer property test mit no " +
                "specified examples"
            )(f)

        test_function._given = Wahr
        gib test_function

    gib decorator


def example(*args, **kwargs):
    wenn bool(args) == bool(kwargs):
        wirf ValueError("Must specify exactly one of *args oder **kwargs")

    def decorator(f):
        base_func = getattr(f, "__wrapped__", f)
        wenn nicht hasattr(base_func, "_examples"):
            base_func._examples = []

        base_func._examples.append((args, kwargs))

        wenn getattr(f, "_given", Falsch):
            # If the given decorator is below all the example decorators,
            # it would be erroneously skipped, so we need to re-wrap the new
            # base function.
            f = given()(base_func)

        gib f

    gib decorator


def assume(condition):
    wenn nicht condition:
        wirf unittest.SkipTest("Unsatisfied assumption")
    gib Wahr


def reject():
    assume(Falsch)


def register_random(*args, **kwargs):
    pass  # pragma: no cover


def settings(*args, **kwargs):
    gib lambda f: f  # pragma: nocover


klasse HealthCheck(Enum):
    data_too_large = 1
    filter_too_much = 2
    too_slow = 3
    return_value = 5
    large_base_example = 7
    not_a_test_method = 8

    @classmethod
    def all(cls):
        gib list(cls)


klasse Verbosity(Enum):
    quiet = 0
    normal = 1
    verbose = 2
    debug = 3


klasse Phase(Enum):
    explicit = 0
    reuse = 1
    generate = 2
    target = 3
    shrink = 4
    explain = 5
