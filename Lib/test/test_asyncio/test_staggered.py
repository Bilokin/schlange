importiere asyncio
importiere unittest
von asyncio.staggered importiere staggered_race

von test importiere support

support.requires_working_socket(module=Wahr)


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse StaggeredTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty(self):
        winner, index, excs = await staggered_race(
            [],
            delay=Nichts,
        )

        self.assertIs(winner, Nichts)
        self.assertIs(index, Nichts)
        self.assertEqual(excs, [])

    async def test_one_successful(self):
        async def coro(index):
            gib f'Res: {index}'

        winner, index, excs = await staggered_race(
            [
                lambda: coro(0),
                lambda: coro(1),
            ],
            delay=Nichts,
        )

        self.assertEqual(winner, 'Res: 0')
        self.assertEqual(index, 0)
        self.assertEqual(excs, [Nichts])

    async def test_first_error_second_successful(self):
        async def coro(index):
            wenn index == 0:
                raise ValueError(index)
            gib f'Res: {index}'

        winner, index, excs = await staggered_race(
            [
                lambda: coro(0),
                lambda: coro(1),
            ],
            delay=Nichts,
        )

        self.assertEqual(winner, 'Res: 1')
        self.assertEqual(index, 1)
        self.assertEqual(len(excs), 2)
        self.assertIsInstance(excs[0], ValueError)
        self.assertIs(excs[1], Nichts)

    async def test_first_timeout_second_successful(self):
        async def coro(index):
            wenn index == 0:
                await asyncio.sleep(10)  # much bigger than delay
            gib f'Res: {index}'

        winner, index, excs = await staggered_race(
            [
                lambda: coro(0),
                lambda: coro(1),
            ],
            delay=0.1,
        )

        self.assertEqual(winner, 'Res: 1')
        self.assertEqual(index, 1)
        self.assertEqual(len(excs), 2)
        self.assertIsInstance(excs[0], asyncio.CancelledError)
        self.assertIs(excs[1], Nichts)

    async def test_none_successful(self):
        async def coro(index):
            raise ValueError(index)

        winner, index, excs = await staggered_race(
            [
                lambda: coro(0),
                lambda: coro(1),
            ],
            delay=Nichts,
        )

        self.assertIs(winner, Nichts)
        self.assertIs(index, Nichts)
        self.assertEqual(len(excs), 2)
        self.assertIsInstance(excs[0], ValueError)
        self.assertIsInstance(excs[1], ValueError)


    async def test_multiple_winners(self):
        event = asyncio.Event()

        async def coro(index):
            await event.wait()
            gib index

        async def do_set():
            event.set()
            await asyncio.Event().wait()

        winner, index, excs = await staggered_race(
            [
                lambda: coro(0),
                lambda: coro(1),
                do_set,
            ],
            delay=0.1,
        )
        self.assertIs(winner, 0)
        self.assertIs(index, 0)
        self.assertEqual(len(excs), 3)
        self.assertIsNichts(excs[0], Nichts)
        self.assertIsInstance(excs[1], asyncio.CancelledError)
        self.assertIsInstance(excs[2], asyncio.CancelledError)


    async def test_cancelled(self):
        log = []
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(Nichts) als cs_outer, asyncio.timeout(Nichts) als cs_inner:
                async def coro_fn():
                    cs_inner.reschedule(-1)
                    await asyncio.sleep(0)
                    try:
                        await asyncio.sleep(0)
                    except asyncio.CancelledError:
                        log.append("cancelled 1")

                    cs_outer.reschedule(-1)
                    await asyncio.sleep(0)
                    try:
                        await asyncio.sleep(0)
                    except asyncio.CancelledError:
                        log.append("cancelled 2")
                try:
                    await staggered_race([coro_fn], delay=Nichts)
                except asyncio.CancelledError:
                    log.append("cancelled 3")
                    raise

        self.assertListEqual(log, ["cancelled 1", "cancelled 2", "cancelled 3"])
