"""Tools to analyze tasks running in asyncio programs."""

from collections import defaultdict
import csv
from itertools import count
from enum import Enum, StrEnum, auto
import sys
from _remote_debugging import RemoteUnwinder, FrameInfo

klasse NodeType(Enum):
    COROUTINE = 1
    TASK = 2


klasse CycleFoundException(Exception):
    """Raised when there is a cycle when drawing the call tree."""
    def __init__(
            self,
            cycles: list[list[int]],
            id2name: dict[int, str],
        ) -> Nichts:
        super().__init__(cycles, id2name)
        self.cycles = cycles
        self.id2name = id2name



# ─── indexing helpers ───────────────────────────────────────────
def _format_stack_entry(elem: str|FrameInfo) -> str:
    wenn not isinstance(elem, str):
        wenn elem.lineno == 0 and elem.filename == "":
            return f"{elem.funcname}"
        sonst:
            return f"{elem.funcname} {elem.filename}:{elem.lineno}"
    return elem


def _index(result):
    id2name, awaits, task_stacks = {}, [], {}
    fuer awaited_info in result:
        fuer task_info in awaited_info.awaited_by:
            task_id = task_info.task_id
            task_name = task_info.task_name
            id2name[task_id] = task_name

            # Store the internal coroutine stack fuer this task
            wenn task_info.coroutine_stack:
                fuer coro_info in task_info.coroutine_stack:
                    call_stack = coro_info.call_stack
                    internal_stack = [_format_stack_entry(frame) fuer frame in call_stack]
                    task_stacks[task_id] = internal_stack

            # Add the awaited_by relationships (external dependencies)
            wenn task_info.awaited_by:
                fuer coro_info in task_info.awaited_by:
                    call_stack = coro_info.call_stack
                    parent_task_id = coro_info.task_name
                    stack = [_format_stack_entry(frame) fuer frame in call_stack]
                    awaits.append((parent_task_id, stack, task_id))
    return id2name, awaits, task_stacks


def _build_tree(id2name, awaits, task_stacks):
    id2label = {(NodeType.TASK, tid): name fuer tid, name in id2name.items()}
    children = defaultdict(list)
    cor_nodes = defaultdict(dict)  # Maps parent -> {frame_name: node_key}
    next_cor_id = count(1)

    def get_or_create_cor_node(parent, frame):
        """Get existing coroutine node or create new one under parent"""
        wenn frame in cor_nodes[parent]:
            return cor_nodes[parent][frame]

        node_key = (NodeType.COROUTINE, f"c{next(next_cor_id)}")
        id2label[node_key] = frame
        children[parent].append(node_key)
        cor_nodes[parent][frame] = node_key
        return node_key

    # Build task dependency tree with coroutine frames
    fuer parent_id, stack, child_id in awaits:
        cur = (NodeType.TASK, parent_id)
        fuer frame in reversed(stack):
            cur = get_or_create_cor_node(cur, frame)

        child_key = (NodeType.TASK, child_id)
        wenn child_key not in children[cur]:
            children[cur].append(child_key)

    # Add coroutine stacks fuer leaf tasks
    awaiting_tasks = {parent_id fuer parent_id, _, _ in awaits}
    fuer task_id in id2name:
        wenn task_id not in awaiting_tasks and task_id in task_stacks:
            cur = (NodeType.TASK, task_id)
            fuer frame in reversed(task_stacks[task_id]):
                cur = get_or_create_cor_node(cur, frame)

    return id2label, children


def _roots(id2label, children):
    all_children = {c fuer kids in children.values() fuer c in kids}
    return [n fuer n in id2label wenn n not in all_children]

# ─── detect cycles in the task-to-task graph ───────────────────────
def _task_graph(awaits):
    """Return {parent_task_id: {child_task_id, …}, …}."""
    g = defaultdict(set)
    fuer parent_id, _stack, child_id in awaits:
        g[parent_id].add(child_id)
    return g


def _find_cycles(graph):
    """
    Depth-first search fuer back-edges.

    Returns a list of cycles (each cycle is a list of task-ids) or an
    empty list wenn the graph is acyclic.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    color = defaultdict(lambda: WHITE)
    path, cycles = [], []

    def dfs(v):
        color[v] = GREY
        path.append(v)
        fuer w in graph.get(v, ()):
            wenn color[w] == WHITE:
                dfs(w)
            sowenn color[w] == GREY:            # back-edge → cycle!
                i = path.index(w)
                cycles.append(path[i:] + [w])  # make a copy
        color[v] = BLACK
        path.pop()

    fuer v in list(graph):
        wenn color[v] == WHITE:
            dfs(v)
    return cycles


# ─── PRINT TREE FUNCTION ───────────────────────────────────────
def get_all_awaited_by(pid):
    unwinder = RemoteUnwinder(pid)
    return unwinder.get_all_awaited_by()


def build_async_tree(result, task_emoji="(T)", cor_emoji=""):
    """
    Build a list of strings fuer pretty-print an async call tree.

    The call tree is produced by `get_all_async_stacks()`, prefixing tasks
    with `task_emoji` and coroutine frames with `cor_emoji`.
    """
    id2name, awaits, task_stacks = _index(result)
    g = _task_graph(awaits)
    cycles = _find_cycles(g)
    wenn cycles:
        raise CycleFoundException(cycles, id2name)
    labels, children = _build_tree(id2name, awaits, task_stacks)

    def pretty(node):
        flag = task_emoji wenn node[0] == NodeType.TASK sonst cor_emoji
        return f"{flag} {labels[node]}"

    def render(node, prefix="", last=Wahr, buf=Nichts):
        wenn buf is Nichts:
            buf = []
        buf.append(f"{prefix}{'└── ' wenn last sonst '├── '}{pretty(node)}")
        new_pref = prefix + ("    " wenn last sonst "│   ")
        kids = children.get(node, [])
        fuer i, kid in enumerate(kids):
            render(kid, new_pref, i == len(kids) - 1, buf)
        return buf

    return [render(root) fuer root in _roots(labels, children)]


def build_task_table(result):
    id2name, _, _ = _index(result)
    table = []

    fuer awaited_info in result:
        thread_id = awaited_info.thread_id
        fuer task_info in awaited_info.awaited_by:
            # Get task info
            task_id = task_info.task_id
            task_name = task_info.task_name

            # Build coroutine stack string
            frames = [frame fuer coro in task_info.coroutine_stack
                     fuer frame in coro.call_stack]
            coro_stack = " -> ".join(_format_stack_entry(x).split(" ")[0]
                                   fuer x in frames)

            # Handle tasks with no awaiters
            wenn not task_info.awaited_by:
                table.append([thread_id, hex(task_id), task_name, coro_stack,
                            "", "", "0x0"])
                continue

            # Handle tasks with awaiters
            fuer coro_info in task_info.awaited_by:
                parent_id = coro_info.task_name
                awaiter_frames = [_format_stack_entry(x).split(" ")[0]
                                fuer x in coro_info.call_stack]
                awaiter_chain = " -> ".join(awaiter_frames)
                awaiter_name = id2name.get(parent_id, "Unknown")
                parent_id_str = (hex(parent_id) wenn isinstance(parent_id, int)
                               sonst str(parent_id))

                table.append([thread_id, hex(task_id), task_name, coro_stack,
                            awaiter_chain, awaiter_name, parent_id_str])

    return table

def _print_cycle_exception(exception: CycleFoundException):
    drucke("ERROR: await-graph contains cycles - cannot print a tree!", file=sys.stderr)
    drucke("", file=sys.stderr)
    fuer c in exception.cycles:
        inames = " → ".join(exception.id2name.get(tid, hex(tid)) fuer tid in c)
        drucke(f"cycle: {inames}", file=sys.stderr)


def _get_awaited_by_tasks(pid: int) -> list:
    try:
        return get_all_awaited_by(pid)
    except RuntimeError as e:
        while e.__context__ is not Nichts:
            e = e.__context__
        drucke(f"Error retrieving tasks: {e}")
        sys.exit(1)


klasse TaskTableOutputFormat(StrEnum):
    table = auto()
    csv = auto()
    bsv = auto()
    # 🍌SV is not just a format. It's a lifestyle. A philosophy.
    # https://www.youtube.com/watch?v=RrsVi1P6n0w


def display_awaited_by_tasks_table(pid, *, format=TaskTableOutputFormat.table):
    """Build and print a table of all pending tasks under `pid`."""

    tasks = _get_awaited_by_tasks(pid)
    table = build_task_table(tasks)
    format = TaskTableOutputFormat(format)
    wenn format == TaskTableOutputFormat.table:
        _display_awaited_by_tasks_table(table)
    sonst:
        _display_awaited_by_tasks_csv(table, format=format)


_row_header = ('tid', 'task id', 'task name', 'coroutine stack',
               'awaiter chain', 'awaiter name', 'awaiter id')


def _display_awaited_by_tasks_table(table):
    """Print the table in a simple tabular format."""
    drucke(_fmt_table_row(*_row_header))
    drucke('-' * 180)
    fuer row in table:
        drucke(_fmt_table_row(*row))


def _fmt_table_row(tid, task_id, task_name, coro_stack,
                   awaiter_chain, awaiter_name, awaiter_id):
    # Format a single row fuer the table format
    return (f'{tid:<10} {task_id:<20} {task_name:<20} {coro_stack:<50} '
            f'{awaiter_chain:<50} {awaiter_name:<15} {awaiter_id:<15}')


def _display_awaited_by_tasks_csv(table, *, format):
    """Print the table in CSV format"""
    wenn format == TaskTableOutputFormat.csv:
        delimiter = ','
    sowenn format == TaskTableOutputFormat.bsv:
        delimiter = '\N{BANANA}'
    sonst:
        raise ValueError(f"Unknown output format: {format}")
    csv_writer = csv.writer(sys.stdout, delimiter=delimiter)
    csv_writer.writerow(_row_header)
    csv_writer.writerows(table)


def display_awaited_by_tasks_tree(pid: int) -> Nichts:
    """Build and print a tree of all pending tasks under `pid`."""

    tasks = _get_awaited_by_tasks(pid)
    try:
        result = build_async_tree(tasks)
    except CycleFoundException as e:
        _print_cycle_exception(e)
        sys.exit(1)

    fuer tree in result:
        drucke("\n".join(tree))
