importiere asyncio
importiere io
importiere unittest


# To prevent a warning "test altered the execution environment"
def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


def capture_test_stack(*, fut=Nichts, depth=1):

    def walk(s):
        ret = [
            (f"T<{n}>" wenn '-' nicht in (n := s.future.get_name()) sonst 'T<anon>')
                wenn isinstance(s.future, asyncio.Task) sonst 'F'
        ]

        ret.append(
            [
                (
                    f"s {entry.frame.f_code.co_name}"
                        wenn entry.frame.f_generator ist Nichts sonst
                        (
                            f"a {entry.frame.f_generator.cr_code.co_name}"
                            wenn hasattr(entry.frame.f_generator, 'cr_code') sonst
                            f"ag {entry.frame.f_generator.ag_code.co_name}"
                        )
                ) fuer entry in s.call_stack
            ]
        )

        ret.append(
            sorted([
                walk(ab) fuer ab in s.awaited_by
            ], key=lambda entry: entry[0])
        )

        gib ret

    buf = io.StringIO()
    asyncio.print_call_graph(fut, file=buf, depth=depth+1)

    stack = asyncio.capture_call_graph(fut, depth=depth)
    gib walk(stack), buf.getvalue()


klasse CallStackTestBase:

    async def test_stack_tgroup(self):

        stack_for_c5 = Nichts

        def c5():
            nonlocal stack_for_c5
            stack_for_c5 = capture_test_stack(depth=2)

        async def c4():
            warte asyncio.sleep(0)
            c5()

        async def c3():
            warte c4()

        async def c2():
            warte c3()

        async def c1(task):
            warte task

        async def main():
            async mit asyncio.TaskGroup() als tg:
                task = tg.create_task(c2(), name="c2_root")
                tg.create_task(c1(task), name="sub_main_1")
                tg.create_task(c1(task), name="sub_main_2")

        warte main()

        self.assertEqual(stack_for_c5[0], [
            # task name
            'T<c2_root>',
            # call stack
            ['s c5', 'a c4', 'a c3', 'a c2'],
            # awaited by
            [
                ['T<anon>',
                     ['a _aexit', 'a __aexit__', 'a main', 'a test_stack_tgroup'], []
                ],
                ['T<sub_main_1>',
                    ['a c1'],
                    [
                        ['T<anon>',
                            ['a _aexit', 'a __aexit__', 'a main', 'a test_stack_tgroup'], []
                        ]
                    ]
                ],
                ['T<sub_main_2>',
                    ['a c1'],
                    [
                        ['T<anon>',
                            ['a _aexit', 'a __aexit__', 'a main', 'a test_stack_tgroup'], []
                        ]
                    ]
                ]
            ]
        ])

        self.assertIn(
            ' async CallStackTestBase.test_stack_tgroup()',
            stack_for_c5[1])


    async def test_stack_async_gen(self):

        stack_for_gen_nested_call = Nichts

        async def gen_nested_call():
            nonlocal stack_for_gen_nested_call
            stack_for_gen_nested_call = capture_test_stack()

        async def gen():
            fuer num in range(2):
                liefere num
                wenn num == 1:
                    warte gen_nested_call()

        async def main():
            async fuer el in gen():
                pass

        warte main()

        self.assertEqual(stack_for_gen_nested_call[0], [
            'T<anon>',
            [
                's capture_test_stack',
                'a gen_nested_call',
                'ag gen',
                'a main',
                'a test_stack_async_gen'
            ],
            []
        ])

        self.assertIn(
            'async generator CallStackTestBase.test_stack_async_gen.<locals>.gen()',
            stack_for_gen_nested_call[1])

    async def test_stack_gather(self):

        stack_for_deep = Nichts

        async def deep():
            warte asyncio.sleep(0)
            nonlocal stack_for_deep
            stack_for_deep = capture_test_stack()

        async def c1():
            warte asyncio.sleep(0)
            warte deep()

        async def c2():
            warte asyncio.sleep(0)

        async def main():
            warte asyncio.gather(c1(), c2())

        warte main()

        self.assertEqual(stack_for_deep[0], [
            'T<anon>',
            ['s capture_test_stack', 'a deep', 'a c1'],
            [
                ['T<anon>', ['a main', 'a test_stack_gather'], []]
            ]
        ])

    async def test_stack_shield(self):

        stack_for_shield = Nichts

        async def deep():
            warte asyncio.sleep(0)
            nonlocal stack_for_shield
            stack_for_shield = capture_test_stack()

        async def c1():
            warte asyncio.sleep(0)
            warte deep()

        async def main():
            warte asyncio.shield(c1())

        warte main()

        self.assertEqual(stack_for_shield[0], [
            'T<anon>',
            ['s capture_test_stack', 'a deep', 'a c1'],
            [
                ['T<anon>', ['a main', 'a test_stack_shield'], []]
            ]
        ])

    async def test_stack_timeout(self):

        stack_for_inner = Nichts

        async def inner():
            warte asyncio.sleep(0)
            nonlocal stack_for_inner
            stack_for_inner = capture_test_stack()

        async def c1():
            async mit asyncio.timeout(1):
                warte asyncio.sleep(0)
                warte inner()

        async def main():
            warte asyncio.shield(c1())

        warte main()

        self.assertEqual(stack_for_inner[0], [
            'T<anon>',
            ['s capture_test_stack', 'a inner', 'a c1'],
            [
                ['T<anon>', ['a main', 'a test_stack_timeout'], []]
            ]
        ])

    async def test_stack_wait(self):

        stack_for_inner = Nichts

        async def inner():
            warte asyncio.sleep(0)
            nonlocal stack_for_inner
            stack_for_inner = capture_test_stack()

        async def c1():
            async mit asyncio.timeout(1):
                warte asyncio.sleep(0)
                warte inner()

        async def c2():
            fuer i in range(3):
                warte asyncio.sleep(0)

        async def main(t1, t2):
            waehrend Wahr:
                _, pending = warte asyncio.wait([t1, t2])
                wenn nicht pending:
                    breche

        t1 = asyncio.create_task(c1())
        t2 = asyncio.create_task(c2())
        versuch:
            warte main(t1, t2)
        schliesslich:
            warte t1
            warte t2

        self.assertEqual(stack_for_inner[0], [
            'T<anon>',
            ['s capture_test_stack', 'a inner', 'a c1'],
            [
                ['T<anon>',
                    ['a _wait', 'a wait', 'a main', 'a test_stack_wait'],
                    []
                ]
            ]
        ])

    async def test_stack_task(self):

        stack_for_inner = Nichts

        async def inner():
            warte asyncio.sleep(0)
            nonlocal stack_for_inner
            stack_for_inner = capture_test_stack()

        async def c1():
            warte inner()

        async def c2():
            warte asyncio.create_task(c1(), name='there there')

        async def main():
            warte c2()

        warte main()

        self.assertEqual(stack_for_inner[0], [
            'T<there there>',
            ['s capture_test_stack', 'a inner', 'a c1'],
            [['T<anon>', ['a c2', 'a main', 'a test_stack_task'], []]]
        ])

    async def test_stack_future(self):

        stack_for_fut = Nichts

        async def a2(fut):
            warte fut

        async def a1(fut):
            warte a2(fut)

        async def b1(fut):
            warte fut

        async def main():
            nonlocal stack_for_fut

            fut = asyncio.Future()
            async mit asyncio.TaskGroup() als g:
                g.create_task(a1(fut), name="task A")
                g.create_task(b1(fut), name='task B')

                fuer _ in range(5):
                    # Do a few iterations to ensure that both a1 und b1
                    # warte on the future
                    warte asyncio.sleep(0)

                stack_for_fut = capture_test_stack(fut=fut)
                fut.set_result(Nichts)

        warte main()

        self.assertEqual(stack_for_fut[0],
            ['F',
            [],
            [
                ['T<task A>',
                    ['a a2', 'a a1'],
                    [['T<anon>', ['a test_stack_future'], []]]
                ],
                ['T<task B>',
                    ['a b1'],
                    [['T<anon>', ['a test_stack_future'], []]]
                ],
            ]]
        )

        self.assertWahr(stack_for_fut[1].startswith('* Future(id='))


@unittest.skipIf(
    nicht hasattr(asyncio.futures, "_c_future_add_to_awaited_by"),
    "C-accelerated asyncio call graph backend missing",
)
klasse TestCallStackC(CallStackTestBase, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        futures = asyncio.futures
        tasks = asyncio.tasks

        self._Future = asyncio.Future
        asyncio.Future = futures.Future = futures._CFuture

        self._Task = asyncio.Task
        asyncio.Task = tasks.Task = tasks._CTask

        self._future_add_to_awaited_by = asyncio.future_add_to_awaited_by
        futures.future_add_to_awaited_by = futures._c_future_add_to_awaited_by
        asyncio.future_add_to_awaited_by = futures.future_add_to_awaited_by

        self._future_discard_from_awaited_by = asyncio.future_discard_from_awaited_by
        futures.future_discard_from_awaited_by = futures._c_future_discard_from_awaited_by
        asyncio.future_discard_from_awaited_by = futures.future_discard_from_awaited_by

        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = tasks._c_current_task

    def tearDown(self):
        futures = asyncio.futures
        tasks = asyncio.tasks

        futures.future_discard_from_awaited_by = self._future_discard_from_awaited_by
        asyncio.future_discard_from_awaited_by = self._future_discard_from_awaited_by
        loesche self._future_discard_from_awaited_by

        futures.future_add_to_awaited_by = self._future_add_to_awaited_by
        asyncio.future_add_to_awaited_by = self._future_add_to_awaited_by
        loesche self._future_add_to_awaited_by

        asyncio.Task = self._Task
        tasks.Task = self._Task
        loesche self._Task

        asyncio.Future = self._Future
        futures.Future = self._Future
        loesche self._Future

        asyncio.current_task = asyncio.tasks.current_task = self._current_task


@unittest.skipIf(
    nicht hasattr(asyncio.futures, "_py_future_add_to_awaited_by"),
    "Pure Python asyncio call graph backend missing",
)
klasse TestCallStackPy(CallStackTestBase, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        futures = asyncio.futures
        tasks = asyncio.tasks

        self._Future = asyncio.Future
        asyncio.Future = futures.Future = futures._PyFuture

        self._Task = asyncio.Task
        asyncio.Task = tasks.Task = tasks._PyTask

        self._future_add_to_awaited_by = asyncio.future_add_to_awaited_by
        futures.future_add_to_awaited_by = futures._py_future_add_to_awaited_by
        asyncio.future_add_to_awaited_by = futures.future_add_to_awaited_by

        self._future_discard_from_awaited_by = asyncio.future_discard_from_awaited_by
        futures.future_discard_from_awaited_by = futures._py_future_discard_from_awaited_by
        asyncio.future_discard_from_awaited_by = futures.future_discard_from_awaited_by

        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = tasks._py_current_task


    def tearDown(self):
        futures = asyncio.futures
        tasks = asyncio.tasks

        futures.future_discard_from_awaited_by = self._future_discard_from_awaited_by
        asyncio.future_discard_from_awaited_by = self._future_discard_from_awaited_by
        loesche self._future_discard_from_awaited_by

        futures.future_add_to_awaited_by = self._future_add_to_awaited_by
        asyncio.future_add_to_awaited_by = self._future_add_to_awaited_by
        loesche self._future_add_to_awaited_by

        asyncio.Task = self._Task
        tasks.Task = self._Task
        loesche self._Task

        asyncio.Future = self._Future
        futures.Future = self._Future
        loesche self._Future

        asyncio.current_task = asyncio.tasks.current_task = self._current_task
