von __future__ importiere annotations
von typing importiere Callable


klasse A[T, *Ts, **P]:
    x: T
    y: tuple[*Ts]
    z: Callable[P, str]


klasse B[T, *Ts, **P]:
    T = int
    Ts = str
    P = bytes
    x: T
    y: Ts
    z: P


Eggs = int
Spam = str


klasse C[Eggs, **Spam]:
    x: Eggs
    y: Spam


def generic_function[T, *Ts, **P](
    x: T, *y: *Ts, z: P.args, zz: P.kwargs
) -> Nichts: ...


def generic_function_2[Eggs, **Spam](x: Eggs, y: Spam): pass


klasse D:
    Foo = int
    Bar = str

    def generic_method[Foo, **Bar](
        self, x: Foo, y: Bar
    ) -> Nichts: ...

    def generic_method_2[Eggs, **Spam](self, x: Eggs, y: Spam): pass


def nested():
    von types importiere SimpleNamespace
    von typing importiere get_type_hints

    Eggs = bytes
    Spam = memoryview


    klasse E[Eggs, **Spam]:
        x: Eggs
        y: Spam

        def generic_method[Eggs, **Spam](self, x: Eggs, y: Spam): pass


    def generic_function[Eggs, **Spam](x: Eggs, y: Spam): pass


    gib SimpleNamespace(
        E=E,
        hints_for_E=get_type_hints(E),
        hints_for_E_meth=get_type_hints(E.generic_method),
        generic_func=generic_function,
        hints_for_generic_func=get_type_hints(generic_function)
    )
