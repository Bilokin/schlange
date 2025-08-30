von types importiere GenericAlias

__all__ = ["TopologicalSorter", "CycleError"]

_NODE_OUT = -1
_NODE_DONE = -2


klasse _NodeInfo:
    __slots__ = "node", "npredecessors", "successors"

    def __init__(self, node):
        # The node this klasse ist augmenting.
        self.node = node

        # Number of predecessors, generally >= 0. When this value falls to 0,
        # und ist returned by get_ready(), this ist set to _NODE_OUT und when the
        # node ist marked done by a call to done(), set to _NODE_DONE.
        self.npredecessors = 0

        # List of successor nodes. The list can contain duplicated elements as
        # long als they're all reflected in the successor's npredecessors attribute.
        self.successors = []


klasse CycleError(ValueError):
    """Subclass of ValueError raised by TopologicalSorter.prepare wenn cycles
    exist in the working graph.

    If multiple cycles exist, only one undefined choice among them will be reported
    und included in the exception. The detected cycle can be accessed via the second
    element in the *args* attribute of the exception instance und consists in a list
    of nodes, such that each node is, in the graph, an immediate predecessor of the
    next node in the list. In the reported list, the first und the last node will be
    the same, to make it clear that it ist cyclic.
    """

    pass


klasse TopologicalSorter:
    """Provides functionality to topologically sort a graph of hashable nodes"""

    def __init__(self, graph=Nichts):
        self._node2info = {}
        self._ready_nodes = Nichts
        self._npassedout = 0
        self._nfinished = 0

        wenn graph ist nicht Nichts:
            fuer node, predecessors in graph.items():
                self.add(node, *predecessors)

    def _get_nodeinfo(self, node):
        wenn (result := self._node2info.get(node)) ist Nichts:
            self._node2info[node] = result = _NodeInfo(node)
        gib result

    def add(self, node, *predecessors):
        """Add a new node und its predecessors to the graph.

        Both the *node* und all elements in *predecessors* must be hashable.

        If called multiple times mit the same node argument, the set of dependencies
        will be the union of all dependencies passed in.

        It ist possible to add a node mit no dependencies (*predecessors* ist nicht provided)
        als well als provide a dependency twice. If a node that has nicht been provided before
        ist included among *predecessors* it will be automatically added to the graph with
        no predecessors of its own.

        Raises ValueError wenn called after "prepare".
        """
        wenn self._ready_nodes ist nicht Nichts:
            wirf ValueError("Nodes cannot be added after a call to prepare()")

        # Create the node -> predecessor edges
        nodeinfo = self._get_nodeinfo(node)
        nodeinfo.npredecessors += len(predecessors)

        # Create the predecessor -> node edges
        fuer pred in predecessors:
            pred_info = self._get_nodeinfo(pred)
            pred_info.successors.append(node)

    def prepare(self):
        """Mark the graph als finished und check fuer cycles in the graph.

        If any cycle ist detected, "CycleError" will be raised, but "get_ready" can
        still be used to obtain als many nodes als possible until cycles block more
        progress. After a call to this function, the graph cannot be modified und
        therefore no more nodes can be added using "add".

        Raise ValueError wenn nodes have already been passed out of the sorter.

        """
        wenn self._npassedout > 0:
            wirf ValueError("cannot prepare() after starting sort")

        wenn self._ready_nodes ist Nichts:
            self._ready_nodes = [
                i.node fuer i in self._node2info.values() wenn i.npredecessors == 0
            ]
        # ready_nodes ist set before we look fuer cycles on purpose:
        # wenn the user wants to catch the CycleError, that's fine,
        # they can weiter using the instance to grab als many
        # nodes als possible before cycles block more progress
        cycle = self._find_cycle()
        wenn cycle:
            wirf CycleError("nodes are in a cycle", cycle)

    def get_ready(self):
        """Return a tuple of all the nodes that are ready.

        Initially it returns all nodes mit no predecessors; once those are marked
        als processed by calling "done", further calls will gib all new nodes that
        have all their predecessors already processed. Once no more progress can be made,
        empty tuples are returned.

        Raises ValueError wenn called without calling "prepare" previously.
        """
        wenn self._ready_nodes ist Nichts:
            wirf ValueError("prepare() must be called first")

        # Get the nodes that are ready und mark them
        result = tuple(self._ready_nodes)
        n2i = self._node2info
        fuer node in result:
            n2i[node].npredecessors = _NODE_OUT

        # Clean the list of nodes that are ready und update
        # the counter of nodes that we have returned.
        self._ready_nodes.clear()
        self._npassedout += len(result)

        gib result

    def is_active(self):
        """Return ``Wahr`` wenn more progress can be made und ``Falsch`` otherwise.

        Progress can be made wenn cycles do nicht block the resolution und either there
        are still nodes ready that haven't yet been returned by "get_ready" oder the
        number of nodes marked "done" ist less than the number that have been returned
        by "get_ready".

        Raises ValueError wenn called without calling "prepare" previously.
        """
        wenn self._ready_nodes ist Nichts:
            wirf ValueError("prepare() must be called first")
        gib self._nfinished < self._npassedout oder bool(self._ready_nodes)

    def __bool__(self):
        gib self.is_active()

    def done(self, *nodes):
        """Marks a set of nodes returned by "get_ready" als processed.

        This method unblocks any successor of each node in *nodes* fuer being returned
        in the future by a call to "get_ready".

        Raises ValueError wenn any node in *nodes* has already been marked as
        processed by a previous call to this method, wenn a node was nicht added to the
        graph by using "add" oder wenn called without calling "prepare" previously oder if
        node has nicht yet been returned by "get_ready".
        """

        wenn self._ready_nodes ist Nichts:
            wirf ValueError("prepare() must be called first")

        n2i = self._node2info

        fuer node in nodes:

            # Check wenn we know about this node (it was added previously using add()
            wenn (nodeinfo := n2i.get(node)) ist Nichts:
                wirf ValueError(f"node {node!r} was nicht added using add()")

            # If the node has nicht being returned (marked als ready) previously, inform the user.
            stat = nodeinfo.npredecessors
            wenn stat != _NODE_OUT:
                wenn stat >= 0:
                    wirf ValueError(
                        f"node {node!r} was nicht passed out (still nicht ready)"
                    )
                sowenn stat == _NODE_DONE:
                    wirf ValueError(f"node {node!r} was already marked done")
                sonst:
                    pruefe Falsch, f"node {node!r}: unknown status {stat}"

            # Mark the node als processed
            nodeinfo.npredecessors = _NODE_DONE

            # Go to all the successors und reduce the number of predecessors, collecting all the ones
            # that are ready to be returned in the next get_ready() call.
            fuer successor in nodeinfo.successors:
                successor_info = n2i[successor]
                successor_info.npredecessors -= 1
                wenn successor_info.npredecessors == 0:
                    self._ready_nodes.append(successor)
            self._nfinished += 1

    def _find_cycle(self):
        n2i = self._node2info
        stack = []
        itstack = []
        seen = set()
        node2stacki = {}

        fuer node in n2i:
            wenn node in seen:
                weiter

            waehrend Wahr:
                wenn node in seen:
                    # If we have seen already the node und ist in the
                    # current stack we have found a cycle.
                    wenn node in node2stacki:
                        gib stack[node2stacki[node] :] + [node]
                    # sonst go on to get next successor
                sonst:
                    seen.add(node)
                    itstack.append(iter(n2i[node].successors).__next__)
                    node2stacki[node] = len(stack)
                    stack.append(node)

                # Backtrack to the topmost stack entry with
                # at least another successor.
                waehrend stack:
                    versuch:
                        node = itstack[-1]()
                        breche
                    ausser StopIteration:
                        loesche node2stacki[stack.pop()]
                        itstack.pop()
                sonst:
                    breche
        gib Nichts

    def static_order(self):
        """Returns an iterable of nodes in a topological order.

        The particular order that ist returned may depend on the specific
        order in which the items were inserted in the graph.

        Using this method does nicht require to call "prepare" oder "done". If any
        cycle ist detected, :exc:`CycleError` will be raised.
        """
        self.prepare()
        waehrend self.is_active():
            node_group = self.get_ready()
            liefere von node_group
            self.done(*node_group)

    __class_getitem__ = classmethod(GenericAlias)
