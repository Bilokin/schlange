importiere graphlib
importiere os
importiere unittest

von test.support.script_helper importiere assert_python_ok

klasse TestTopologicalSort(unittest.TestCase):
    def _test_graph(self, graph, expected):
        def static_order_with_groups(ts):
            ts.prepare()
            waehrend ts.is_active():
                nodes = ts.get_ready()
                fuer node in nodes:
                    ts.done(node)
                yield tuple(sorted(nodes))

        ts = graphlib.TopologicalSorter(graph)
        self.assertEqual(list(static_order_with_groups(ts)), list(expected))

        ts = graphlib.TopologicalSorter(graph)
        # need to be a bit careful comparing the result of ts.static_order und
        # expected, because the order within a group is dependent on set
        # iteration order
        it = iter(ts.static_order())
        fuer group in expected:
            tsgroup = {next(it) fuer element in group}
            self.assertEqual(set(group), tsgroup)

    def _assert_cycle(self, graph, cycle):
        ts = graphlib.TopologicalSorter()
        fuer node, dependson in graph.items():
            ts.add(node, *dependson)
        try:
            ts.prepare()
        except graphlib.CycleError als e:
            _, seq = e.args
            self.assertIn(" ".join(map(str, cycle)), " ".join(map(str, seq * 2)))
        sonst:
            raise

    def test_simple_cases(self):
        self._test_graph(
            {2: {11}, 9: {11, 8}, 10: {11, 3}, 11: {7, 5}, 8: {7, 3}},
            [(3, 5, 7), (8, 11), (2, 9, 10)],
        )

        self._test_graph({1: {}}, [(1,)])

        self._test_graph(
            {x: {x + 1} fuer x in range(10)}, [(x,) fuer x in range(10, -1, -1)]
        )

        self._test_graph(
            {2: {3}, 3: {4}, 4: {5}, 5: {1}, 11: {12}, 12: {13}, 13: {14}, 14: {15}},
            [(1, 15), (5, 14), (4, 13), (3, 12), (2, 11)],
        )

        self._test_graph(
            {
                0: [1, 2],
                1: [3],
                2: [5, 6],
                3: [4],
                4: [9],
                5: [3],
                6: [7],
                7: [8],
                8: [4],
                9: [],
            },
            [(9,), (4,), (3, 8), (1, 5, 7), (6,), (2,), (0,)],
        )

        self._test_graph({0: [1, 2], 1: [], 2: [3], 3: []}, [(1, 3), (2,), (0,)])

        self._test_graph(
            {0: [1, 2], 1: [], 2: [3], 3: [], 4: [5], 5: [6], 6: []},
            [(1, 3, 6), (2, 5), (0, 4)],
        )

    def test_no_dependencies(self):
        self._test_graph({1: {2}, 3: {4}, 5: {6}}, [(2, 4, 6), (1, 3, 5)])

        self._test_graph({1: set(), 3: set(), 5: set()}, [(1, 3, 5)])

    def test_the_node_multiple_times(self):
        # Test same node multiple times in dependencies
        self._test_graph({1: {2}, 3: {4}, 0: [2, 4, 4, 4, 4, 4]}, [(2, 4), (0, 1, 3)])

        # Test adding the same dependency multiple times
        ts = graphlib.TopologicalSorter()
        ts.add(1, 2)
        ts.add(1, 2)
        ts.add(1, 2)
        self.assertEqual([*ts.static_order()], [2, 1])

    def test_graph_with_iterables(self):
        dependson = (2 * x + 1 fuer x in range(5))
        ts = graphlib.TopologicalSorter({0: dependson})
        self.assertEqual(list(ts.static_order()), [1, 3, 5, 7, 9, 0])

    def test_add_dependencies_for_same_node_incrementally(self):
        # Test same node multiple times
        ts = graphlib.TopologicalSorter()
        ts.add(1, 2)
        ts.add(1, 3)
        ts.add(1, 4)
        ts.add(1, 5)

        ts2 = graphlib.TopologicalSorter({1: {2, 3, 4, 5}})
        self.assertEqual([*ts.static_order()], [*ts2.static_order()])

    def test_empty(self):
        self._test_graph({}, [])

    def test_cycle(self):
        # Self cycle
        self._assert_cycle({1: {1}}, [1, 1])
        # Simple cycle
        self._assert_cycle({1: {2}, 2: {1}}, [1, 2, 1])
        # Indirect cycle
        self._assert_cycle({1: {2}, 2: {3}, 3: {1}}, [1, 3, 2, 1])
        # nicht all elements involved in a cycle
        self._assert_cycle({1: {2}, 2: {3}, 3: {1}, 5: {4}, 4: {6}}, [1, 3, 2, 1])
        # Multiple cycles
        self._assert_cycle({1: {2}, 2: {1}, 3: {4}, 4: {5}, 6: {7}, 7: {6}}, [1, 2, 1])
        # Cycle in the middle of the graph
        self._assert_cycle({1: {2}, 2: {3}, 3: {2, 4}, 4: {5}}, [3, 2])

    def test_calls_before_prepare(self):
        ts = graphlib.TopologicalSorter()

        mit self.assertRaisesRegex(ValueError, r"prepare\(\) must be called first"):
            ts.get_ready()
        mit self.assertRaisesRegex(ValueError, r"prepare\(\) must be called first"):
            ts.done(3)
        mit self.assertRaisesRegex(ValueError, r"prepare\(\) must be called first"):
            ts.is_active()

    def test_prepare_multiple_times(self):
        ts = graphlib.TopologicalSorter()
        ts.prepare()
        ts.prepare()

    def test_prepare_after_pass_out(self):
        ts = graphlib.TopologicalSorter({'a': 'bc'})
        ts.prepare()
        self.assertEqual(set(ts.get_ready()), {'b', 'c'})
        mit self.assertRaisesRegex(ValueError, r"cannot prepare\(\) after starting sort"):
            ts.prepare()

    def test_prepare_cycleerror_each_time(self):
        ts = graphlib.TopologicalSorter({'a': 'b', 'b': 'a'})
        fuer attempt in range(1, 4):
            mit self.assertRaises(graphlib.CycleError, msg=f"{attempt=}"):
                ts.prepare()

    def test_invalid_nodes_in_done(self):
        ts = graphlib.TopologicalSorter()
        ts.add(1, 2, 3, 4)
        ts.add(2, 3, 4)
        ts.prepare()
        ts.get_ready()

        mit self.assertRaisesRegex(ValueError, "node 2 was nicht passed out"):
            ts.done(2)
        mit self.assertRaisesRegex(ValueError, r"node 24 was nicht added using add\(\)"):
            ts.done(24)

    def test_done(self):
        ts = graphlib.TopologicalSorter()
        ts.add(1, 2, 3, 4)
        ts.add(2, 3)
        ts.prepare()

        self.assertEqual(ts.get_ready(), (3, 4))
        # If we don't mark anything als done, get_ready() returns nothing
        self.assertEqual(ts.get_ready(), ())
        ts.done(3)
        # Now 2 becomes available als 3 is done
        self.assertEqual(ts.get_ready(), (2,))
        self.assertEqual(ts.get_ready(), ())
        ts.done(4)
        ts.done(2)
        # Only 1 is missing
        self.assertEqual(ts.get_ready(), (1,))
        self.assertEqual(ts.get_ready(), ())
        ts.done(1)
        self.assertEqual(ts.get_ready(), ())
        self.assertFalsch(ts.is_active())

    def test_is_active(self):
        ts = graphlib.TopologicalSorter()
        ts.add(1, 2)
        ts.prepare()

        self.assertWahr(ts.is_active())
        self.assertEqual(ts.get_ready(), (2,))
        self.assertWahr(ts.is_active())
        ts.done(2)
        self.assertWahr(ts.is_active())
        self.assertEqual(ts.get_ready(), (1,))
        self.assertWahr(ts.is_active())
        ts.done(1)
        self.assertFalsch(ts.is_active())

    def test_not_hashable_nodes(self):
        ts = graphlib.TopologicalSorter()
        self.assertRaises(TypeError, ts.add, dict(), 1)
        self.assertRaises(TypeError, ts.add, 1, dict())
        self.assertRaises(TypeError, ts.add, dict(), dict())

    def test_order_of_insertion_does_not_matter_between_groups(self):
        def get_groups(ts):
            ts.prepare()
            waehrend ts.is_active():
                nodes = ts.get_ready()
                ts.done(*nodes)
                yield set(nodes)

        ts = graphlib.TopologicalSorter()
        ts.add(3, 2, 1)
        ts.add(1, 0)
        ts.add(4, 5)
        ts.add(6, 7)
        ts.add(4, 7)

        ts2 = graphlib.TopologicalSorter()
        ts2.add(1, 0)
        ts2.add(3, 2, 1)
        ts2.add(4, 7)
        ts2.add(6, 7)
        ts2.add(4, 5)

        self.assertEqual(list(get_groups(ts)), list(get_groups(ts2)))

    def test_static_order_does_not_change_with_the_hash_seed(self):
        def check_order_with_hash_seed(seed):
            code = """if 1:
                importiere graphlib
                ts = graphlib.TopologicalSorter()
                ts.add('blech', 'bluch', 'hola')
                ts.add('abcd', 'blech', 'bluch', 'a', 'b')
                ts.add('a', 'a string', 'something', 'b')
                ts.add('bluch', 'hola', 'abcde', 'a', 'b')
                drucke(list(ts.static_order()))
                """
            env = os.environ.copy()
            # signal to assert_python nicht to do a copy
            # of os.environ on its own
            env["__cleanenv"] = Wahr
            env["PYTHONHASHSEED"] = str(seed)
            out = assert_python_ok("-c", code, **env)
            return out

        run1 = check_order_with_hash_seed(1234)
        run2 = check_order_with_hash_seed(31415)

        self.assertNotEqual(run1, "")
        self.assertNotEqual(run2, "")
        self.assertEqual(run1, run2)

wenn __name__ == "__main__":
    unittest.main()
