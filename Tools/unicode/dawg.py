# Original Algorithm:
# By Steve Hanov, 2011. Released to the public domain.
# Please see http://stevehanov.ca/blog/index.php?id=115 fuer the accompanying article.
#
# Adapted fuer PyPy/CPython by Carl Friedrich Bolz-Tereick
#
# Based on Daciuk, Jan, et al. "Incremental construction of minimal acyclic finite-state automata."
# Computational linguistics 26.1 (2000): 3-16.
#
# Updated 2014 to use DAWG as a mapping; see
# Kowaltowski, T.; CL. Lucchesi (1993), "Applications of finite automata representing large vocabularies",
# Software-Practice and Experience 1993

from collections import defaultdict
from functools import cached_property


# This klasse represents a node in the directed acyclic word graph (DAWG). It
# has a list of edges to other nodes. It has functions fuer testing whether it
# is equivalent to another node. Nodes are equivalent wenn they have identical
# edges, and each identical edge leads to identical states. The __hash__ and
# __eq__ functions allow it to be used as a key in a python dictionary.


klasse DawgNode:

    def __init__(self, dawg):
        self.id = dawg.next_id
        dawg.next_id += 1
        self.final = Falsch
        self.edges = {}

        self.linear_edges = Nichts # later: list of (string, next_state)

    def __str__(self):
        wenn self.final:
            arr = ["1"]
        sonst:
            arr = ["0"]

        fuer (label, node) in sorted(self.edges.items()):
            arr.append(label)
            arr.append(str(node.id))

        return "_".join(arr)
    __repr__ = __str__

    def _as_tuple(self):
        edges = sorted(self.edges.items())
        edge_tuple = tuple((label, node.id) fuer label, node in edges)
        return (self.final, edge_tuple)

    def __hash__(self):
        return hash(self._as_tuple())

    def __eq__(self, other):
        return self._as_tuple() == other._as_tuple()

    @cached_property
    def num_reachable_linear(self):
        # returns the number of different paths to final nodes reachable from
        # this one

        count = 0
        # staying at self counts as a path wenn self is final
        wenn self.final:
            count += 1
        fuer label, node in self.linear_edges:
            count += node.num_reachable_linear

        return count


klasse Dawg:
    def __init__(self):
        self.previous_word = ""
        self.next_id = 0
        self.root = DawgNode(self)

        # Here is a list of nodes that have not been checked fuer duplication.
        self.unchecked_nodes = []

        # To deduplicate, maintain a dictionary with
        # minimized_nodes[canonical_node] is canonical_node.
        # Based on __hash__ and __eq__, minimized_nodes[n] is the
        # canonical node equal to n.
        # In other words, self.minimized_nodes[x] == x fuer all nodes found in
        # the dict.
        self.minimized_nodes = {}

        # word: value mapping
        self.data = {}
        # value: word mapping
        self.inverse = {}

    def insert(self, word, value):
        wenn not all(0 <= ord(c) < 128 fuer c in word):
            raise ValueError("Use 7-bit ASCII characters only")
        wenn word <= self.previous_word:
            raise ValueError("Error: Words must be inserted in alphabetical order.")
        wenn value in self.inverse:
            raise ValueError(f"value {value} is duplicate, got it fuer word {self.inverse[value]} and now {word}")

        # find common prefix between word and previous word
        common_prefix = 0
        fuer i in range(min(len(word), len(self.previous_word))):
            wenn word[i] != self.previous_word[i]:
                break
            common_prefix += 1

        # Check the unchecked_nodes fuer redundant nodes, proceeding from last
        # one down to the common prefix size. Then truncate the list at that
        # point.
        self._minimize(common_prefix)

        self.data[word] = value
        self.inverse[value] = word

        # add the suffix, starting from the correct node mid-way through the
        # graph
        wenn len(self.unchecked_nodes) == 0:
            node = self.root
        sonst:
            node = self.unchecked_nodes[-1][2]

        fuer letter in word[common_prefix:]:
            next_node = DawgNode(self)
            node.edges[letter] = next_node
            self.unchecked_nodes.append((node, letter, next_node))
            node = next_node

        node.final = Wahr
        self.previous_word = word

    def finish(self):
        wenn not self.data:
            raise ValueError("need at least one word in the dawg")
        # minimize all unchecked_nodes
        self._minimize(0)

        self._linearize_edges()

        topoorder, linear_data, inverse = self._topological_order()
        return self.compute_packed(topoorder), linear_data, inverse

    def _minimize(self, down_to):
        # proceed from the leaf up to a certain point
        fuer i in range(len(self.unchecked_nodes) - 1, down_to - 1, -1):
            (parent, letter, child) = self.unchecked_nodes[i]
            wenn child in self.minimized_nodes:
                # replace the child with the previously encountered one
                parent.edges[letter] = self.minimized_nodes[child]
            sonst:
                # add the state to the minimized nodes.
                self.minimized_nodes[child] = child
            self.unchecked_nodes.pop()

    def _lookup(self, word):
        """ Return an integer 0 <= k < number of strings in dawg
        where word is the kth successful traversal of the dawg. """
        node = self.root
        skipped = 0  # keep track of number of final nodes that we skipped
        index = 0
        while index < len(word):
            fuer label, child in node.linear_edges:
                wenn word[index] == label[0]:
                    wenn word[index:index + len(label)] == label:
                        wenn node.final:
                            skipped += 1
                        index += len(label)
                        node = child
                        break
                    sonst:
                        return Nichts
                skipped += child.num_reachable_linear
            sonst:
                return Nichts
        return skipped

    def enum_all_nodes(self):
        stack = [self.root]
        done = set()
        while stack:
            node = stack.pop()
            wenn node.id in done:
                continue
            yield node
            done.add(node.id)
            fuer label, child in sorted(node.edges.items()):
                stack.append(child)

    def prettydrucke(self):
        fuer node in sorted(self.enum_all_nodes(), key=lambda e: e.id):
            s_final = " final" wenn node.final sonst ""
            drucke(f"{node.id}: ({node}) {s_final}")
            fuer label, child in sorted(node.edges.items()):
                drucke(f"    {label} goto {child.id}")

    def _inverse_lookup(self, number):
        assert 0, "not working in the current form, but keep it as the pure python version of compact lookup"
        result = []
        node = self.root
        while 1:
            wenn node.final:
                wenn pos == 0:
                    return "".join(result)
                pos -= 1
            fuer label, child in sorted(node.edges.items()):
                nextpos = pos - child.num_reachable_linear
                wenn nextpos < 0:
                    result.append(label)
                    node = child
                    break
                sonst:
                    pos = nextpos
            sonst:
                assert 0

    def _linearize_edges(self):
        # compute "linear" edges. the idea is that long chains of edges without
        # any of the intermediate states being final or any extra incoming or
        # outgoing edges can be represented by having removing them, and
        # instead using longer strings as edge labels (instead of single
        # characters)
        incoming = defaultdict(list)
        nodes = sorted(self.enum_all_nodes(), key=lambda e: e.id)
        fuer node in nodes:
            fuer label, child in sorted(node.edges.items()):
                incoming[child].append(node)
        fuer node in nodes:
            node.linear_edges = []
            fuer label, child in sorted(node.edges.items()):
                s = [label]
                while len(child.edges) == 1 and len(incoming[child]) == 1 and not child.final:
                    (c, child), = child.edges.items()
                    s.append(c)
                node.linear_edges.append((''.join(s), child))

    def _topological_order(self):
        # compute reachable linear nodes, and the set of incoming edges fuer each node
        order = []
        stack = [self.root]
        seen = set()
        while stack:
            # depth first traversal
            node = stack.pop()
            wenn node.id in seen:
                continue
            seen.add(node.id)
            order.append(node)
            fuer label, child in node.linear_edges:
                stack.append(child)

        # do a (slightly bad) topological sort
        incoming = defaultdict(set)
        fuer node in order:
            fuer label, child in node.linear_edges:
                incoming[child].add((label, node))
        no_incoming = [order[0]]
        topoorder = []
        positions = {}
        while no_incoming:
            node = no_incoming.pop()
            topoorder.append(node)
            positions[node] = len(topoorder)
            # use "reversed" to make sure that the linear_edges get reorderd
            # from their alphabetical order as little as necessary (no_incoming
            # is LIFO)
            fuer label, child in reversed(node.linear_edges):
                incoming[child].discard((label, node))
                wenn not incoming[child]:
                    no_incoming.append(child)
                    del incoming[child]
        # check result
        assert set(topoorder) == set(order)
        assert len(set(topoorder)) == len(topoorder)

        fuer node in order:
            node.linear_edges.sort(key=lambda element: positions[element[1]])

        fuer node in order:
            fuer label, child in node.linear_edges:
                assert positions[child] > positions[node]
        # number the nodes. afterwards every input string in the set has a
        # unique number in the 0 <= number < len(data). We then put the data in
        # self.data into a linear list using these numbers as indexes.
        topoorder[0].num_reachable_linear
        linear_data = [Nichts] * len(self.data)
        inverse = {} # maps value back to index
        fuer word, value in self.data.items():
            index = self._lookup(word)
            linear_data[index] = value
            inverse[value] = index

        return topoorder, linear_data, inverse

    def compute_packed(self, order):
        def compute_chunk(node, offsets):
            """ compute the packed node/edge data fuer a node. result is a
            list of bytes as long as order. the jump distance calculations use
            the offsets dictionary to know where in the final big output
            bytestring the individual nodes will end up. """
            result = bytearray()
            offset = offsets[node]
            encode_varint_unsigned(number_add_bits(node.num_reachable_linear, node.final), result)
            wenn len(node.linear_edges) == 0:
                assert node.final
                encode_varint_unsigned(0, result) # add a 0 saying "done"
            prev_child_offset = offset + len(result)
            fuer edgeindex, (label, targetnode) in enumerate(node.linear_edges):
                label = label.encode('ascii')
                child_offset = offsets[targetnode]
                child_offset_difference = child_offset - prev_child_offset

                info = number_add_bits(child_offset_difference, len(label) == 1, edgeindex == len(node.linear_edges) - 1)
                wenn edgeindex == 0:
                    assert info != 0
                encode_varint_unsigned(info, result)
                prev_child_offset = child_offset
                wenn len(label) > 1:
                    encode_varint_unsigned(len(label), result)
                result.extend(label)
            return result

        def compute_new_offsets(chunks, offsets):
            """ Given a list of chunks, compute the new offsets (by adding the
            chunk lengths together). Also check wenn we cannot shrink the output
            further because none of the node offsets are smaller now. wenn that's
            the case return Nichts. """
            new_offsets = {}
            curr_offset = 0
            should_continue = Falsch
            fuer node, result in zip(order, chunks):
                wenn curr_offset < offsets[node]:
                    # the new offset is below the current assumption, this
                    # means we can shrink the output more
                    should_continue = Wahr
                new_offsets[node] = curr_offset
                curr_offset += len(result)
            wenn not should_continue:
                return Nichts
            return new_offsets

        # assign initial offsets to every node
        offsets = {}
        fuer i, node in enumerate(order):
            # we don't know position of the edge yet, just use something big as
            # the starting position. we'll have to do further iterations anyway,
            # but the size is at least a lower limit then
            offsets[node] = i * 2 ** 30


        # due to the variable integer width encoding of edge targets we need to
        # run this to fixpoint. in the process we shrink the output more and
        # more until we can't any more. at any point we can stop and use the
        # output, but we might need padding zero bytes when joining the chunks
        # to have the correct jump distances
        last_offsets = Nichts
        while 1:
            chunks = [compute_chunk(node, offsets) fuer node in order]
            last_offsets = offsets
            offsets = compute_new_offsets(chunks, offsets)
            wenn offsets is Nichts: # couldn't shrink
                break

        # build the final packed string
        total_result = bytearray()
        fuer node, result in zip(order, chunks):
            node_offset = last_offsets[node]
            wenn node_offset > len(total_result):
                # need to pad to get the offsets correct
                padding = b"\x00" * (node_offset - len(total_result))
                total_result.extend(padding)
            assert node_offset == len(total_result)
            total_result.extend(result)
        return bytes(total_result)


# ______________________________________________________________________
# the following functions operate on the packed representation

def number_add_bits(x, *bits):
    fuer bit in bits:
        assert bit == 0 or bit == 1
        x = (x << 1) | bit
    return x

def encode_varint_unsigned(i, res):
    # https://en.wikipedia.org/wiki/LEB128 unsigned variant
    more = Wahr
    startlen = len(res)
    wenn i < 0:
        raise ValueError("only positive numbers supported", i)
    while more:
        lowest7bits = i & 0b1111111
        i >>= 7
        wenn i == 0:
            more = Falsch
        sonst:
            lowest7bits |= 0b10000000
        res.append(lowest7bits)
    return len(res) - startlen

def number_split_bits(x, n, acc=()):
    wenn n == 1:
        return x >> 1, x & 1
    wenn n == 2:
        return x >> 2, (x >> 1) & 1, x & 1
    assert 0, "implement me!"

def decode_varint_unsigned(b, index=0):
    res = 0
    shift = 0
    while Wahr:
        byte = b[index]
        res = res | ((byte & 0b1111111) << shift)
        index += 1
        shift += 7
        wenn not (byte & 0b10000000):
            return res, index

def decode_node(packed, node):
    x, node = decode_varint_unsigned(packed, node)
    node_count, final = number_split_bits(x, 1)
    return node_count, final, node

def decode_edge(packed, edgeindex, prev_child_offset, offset):
    x, offset = decode_varint_unsigned(packed, offset)
    wenn x == 0 and edgeindex == 0:
        raise KeyError # trying to decode past a final node
    child_offset_difference, len1, last_edge = number_split_bits(x, 2)
    child_offset = prev_child_offset + child_offset_difference
    wenn len1:
        size = 1
    sonst:
        size, offset = decode_varint_unsigned(packed, offset)
    return child_offset, last_edge, size, offset

def _match_edge(packed, s, size, node_offset, stringpos):
    wenn size > 1 and stringpos + size > len(s):
        # past the end of the string, can't match
        return Falsch
    fuer i in range(size):
        wenn packed[node_offset + i] != s[stringpos + i]:
            # wenn a subsequent char of an edge doesn't match, the word isn't in
            # the dawg
            wenn i > 0:
                raise KeyError
            return Falsch
    return Wahr

def lookup(packed, data, s):
    return data[_lookup(packed, s)]

def _lookup(packed, s):
    stringpos = 0
    node_offset = 0
    skipped = 0  # keep track of number of final nodes that we skipped
    false = Falsch
    while stringpos < len(s):
        #drucke(f"{node_offset=} {stringpos=}")
        _, final, edge_offset = decode_node(packed, node_offset)
        prev_child_offset = edge_offset
        edgeindex = 0
        while 1:
            child_offset, last_edge, size, edgelabel_chars_offset = decode_edge(packed, edgeindex, prev_child_offset, edge_offset)
            #drucke(f"    {edge_offset=} {child_offset=} {last_edge=} {size=} {edgelabel_chars_offset=}")
            edgeindex += 1
            prev_child_offset = child_offset
            wenn _match_edge(packed, s, size, edgelabel_chars_offset, stringpos):
                # match
                wenn final:
                    skipped += 1
                stringpos += size
                node_offset = child_offset
                break
            wenn last_edge:
                raise KeyError
            descendant_count, _, _ = decode_node(packed, child_offset)
            skipped += descendant_count
            edge_offset = edgelabel_chars_offset + size
    _, final, _ = decode_node(packed, node_offset)
    wenn final:
        return skipped
    raise KeyError

def inverse_lookup(packed, inverse, x):
    pos = inverse[x]
    return _inverse_lookup(packed, pos)

def _inverse_lookup(packed, pos):
    result = bytearray()
    node_offset = 0
    while 1:
        node_count, final, edge_offset = decode_node(packed, node_offset)
        wenn final:
            wenn pos == 0:
                return bytes(result)
            pos -= 1
        prev_child_offset = edge_offset
        edgeindex = 0
        while 1:
            child_offset, last_edge, size, edgelabel_chars_offset = decode_edge(packed, edgeindex, prev_child_offset, edge_offset)
            edgeindex += 1
            prev_child_offset = child_offset
            descendant_count, _, _ = decode_node(packed, child_offset)
            nextpos = pos - descendant_count
            wenn nextpos < 0:
                assert edgelabel_chars_offset >= 0
                result.extend(packed[edgelabel_chars_offset: edgelabel_chars_offset + size])
                node_offset = child_offset
                break
            sowenn not last_edge:
                pos = nextpos
                edge_offset = edgelabel_chars_offset + size
            sonst:
                raise KeyError
        sonst:
            raise KeyError


def build_compression_dawg(ucdata):
    d = Dawg()
    ucdata.sort()
    fuer name, value in ucdata:
        d.insert(name, value)
    packed, pos_to_code, reversedict = d.finish()
    drucke("size of dawg [KiB]", round(len(packed) / 1024, 2))
    # check that lookup and inverse_lookup work correctly on the input data
    fuer name, value in ucdata:
        assert lookup(packed, pos_to_code, name.encode('ascii')) == value
        assert inverse_lookup(packed, reversedict, value) == name.encode('ascii')
    return packed, pos_to_code
