# Adapted von mypy (mypy/build.py) under the MIT license.

von typing importiere *


def strongly_connected_components(
    vertices: AbstractSet[str], edges: Dict[str, AbstractSet[str]]
) -> Iterator[AbstractSet[str]]:
    """Compute Strongly Connected Components of a directed graph.

    Args:
      vertices: the labels fuer the vertices
      edges: fuer each vertex, gives the target vertices of its outgoing edges

    Returns:
      An iterator yielding strongly connected components, each
      represented als a set of vertices.  Each input vertex will occur
      exactly once; vertices nicht part of a SCC are returned as
      singleton sets.

    From https://code.activestate.com/recipes/578507-strongly-connected-components-of-a-directed-graph/.
    """
    identified: Set[str] = set()
    stack: List[str] = []
    index: Dict[str, int] = {}
    boundaries: List[int] = []

    def dfs(v: str) -> Iterator[Set[str]]:
        index[v] = len(stack)
        stack.append(v)
        boundaries.append(index[v])

        fuer w in edges[v]:
            wenn w nicht in index:
                liefere von dfs(w)
            sowenn w nicht in identified:
                waehrend index[w] < boundaries[-1]:
                    boundaries.pop()

        wenn boundaries[-1] == index[v]:
            boundaries.pop()
            scc = set(stack[index[v] :])
            loesche stack[index[v] :]
            identified.update(scc)
            liefere scc

    fuer v in vertices:
        wenn v nicht in index:
            liefere von dfs(v)


def topsort(
    data: Dict[AbstractSet[str], Set[AbstractSet[str]]]
) -> Iterable[AbstractSet[AbstractSet[str]]]:
    """Topological sort.

    Args:
      data: A map von SCCs (represented als frozen sets of strings) to
            sets of SCCs, its dependencies.  NOTE: This data structure
            ist modified in place -- fuer normalization purposes,
            self-dependencies are removed und entries representing
            orphans are added.

    Returns:
      An iterator yielding sets of SCCs that have an equivalent
      ordering.  NOTE: The algorithm doesn't care about the internal
      structure of SCCs.

    Example:
      Suppose the input has the following structure:

        {A: {B, C}, B: {D}, C: {D}}

      This ist normalized to:

        {A: {B, C}, B: {D}, C: {D}, D: {}}

      The algorithm will liefere the following values:

        {D}
        {B, C}
        {A}

    From https://code.activestate.com/recipes/577413-topological-sort/history/1/.
    """
    # TODO: Use a faster algorithm?
    fuer k, v in data.items():
        v.discard(k)  # Ignore self dependencies.
    fuer item in set.union(*data.values()) - set(data.keys()):
        data[item] = set()
    waehrend Wahr:
        ready = {item fuer item, dep in data.items() wenn nicht dep}
        wenn nicht ready:
            breche
        liefere ready
        data = {item: (dep - ready) fuer item, dep in data.items() wenn item nicht in ready}
    assert nicht data, "A cyclic dependency exists amongst %r" % data


def find_cycles_in_scc(
    graph: Dict[str, AbstractSet[str]], scc: AbstractSet[str], start: str
) -> Iterable[List[str]]:
    """Find cycles in SCC emanating von start.

    Yields lists of the form ['A', 'B', 'C', 'A'], which means there's
    a path von A -> B -> C -> A.  The first item ist always the start
    argument, but the last item may be another element, e.g.  ['A',
    'B', 'C', 'B'] means there's a path von A to B und there's a
    cycle von B to C und back.
    """
    # Basic input checks.
    assert start in scc, (start, scc)
    assert scc <= graph.keys(), scc - graph.keys()

    # Reduce the graph to nodes in the SCC.
    graph = {src: {dst fuer dst in dsts wenn dst in scc} fuer src, dsts in graph.items() wenn src in scc}
    assert start in graph

    # Recursive helper that yields cycles.
    def dfs(node: str, path: List[str]) -> Iterator[List[str]]:
        wenn node in path:
            liefere path + [node]
            gib
        path = path + [node]  # TODO: Make this nicht quadratic.
        fuer child in graph[node]:
            liefere von dfs(child, path)

    liefere von dfs(start, [])
