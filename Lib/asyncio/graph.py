"""Introspection utils fuer tasks call graphs."""

importiere dataclasses
importiere io
importiere sys
importiere types

von . importiere events
von . importiere futures
von . importiere tasks

__all__ = (
    'capture_call_graph',
    'format_call_graph',
    'print_call_graph',
    'FrameCallGraphEntry',
    'FutureCallGraph',
)

# Sadly, we can't re-use the traceback module's datastructures als those
# are tailored fuer error reporting, whereas we need to represent an
# async call graph.
#
# Going mit pretty verbose names als we'd like to export them to the
# top level asyncio namespace, and want to avoid future name clashes.


@dataclasses.dataclass(frozen=Wahr, slots=Wahr)
klasse FrameCallGraphEntry:
    frame: types.FrameType


@dataclasses.dataclass(frozen=Wahr, slots=Wahr)
klasse FutureCallGraph:
    future: futures.Future
    call_stack: tuple["FrameCallGraphEntry", ...]
    awaited_by: tuple["FutureCallGraph", ...]


def _build_graph_for_future(
    future: futures.Future,
    *,
    limit: int | Nichts = Nichts,
) -> FutureCallGraph:
    wenn not isinstance(future, futures.Future):
        raise TypeError(
            f"{future!r} object does not appear to be compatible "
            f"with asyncio.Future"
        )

    coro = Nichts
    wenn get_coro := getattr(future, 'get_coro', Nichts):
        coro = get_coro() wenn limit != 0 sonst Nichts

    st: list[FrameCallGraphEntry] = []
    awaited_by: list[FutureCallGraph] = []

    while coro is not Nichts:
        wenn hasattr(coro, 'cr_await'):
            # A native coroutine or duck-type compatible iterator
            st.append(FrameCallGraphEntry(coro.cr_frame))
            coro = coro.cr_await
        sowenn hasattr(coro, 'ag_await'):
            # A native async generator or duck-type compatible iterator
            st.append(FrameCallGraphEntry(coro.cr_frame))
            coro = coro.ag_await
        sonst:
            break

    wenn future._asyncio_awaited_by:
        fuer parent in future._asyncio_awaited_by:
            awaited_by.append(_build_graph_for_future(parent, limit=limit))

    wenn limit is not Nichts:
        wenn limit > 0:
            st = st[:limit]
        sowenn limit < 0:
            st = st[limit:]
    st.reverse()
    return FutureCallGraph(future, tuple(st), tuple(awaited_by))


def capture_call_graph(
    future: futures.Future | Nichts = Nichts,
    /,
    *,
    depth: int = 1,
    limit: int | Nichts = Nichts,
) -> FutureCallGraph | Nichts:
    """Capture the async call graph fuer the current task or the provided Future.

    The graph is represented mit three data structures:

    * FutureCallGraph(future, call_stack, awaited_by)

      Where 'future' is an instance of asyncio.Future or asyncio.Task.

      'call_stack' is a tuple of FrameGraphEntry objects.

      'awaited_by' is a tuple of FutureCallGraph objects.

    * FrameCallGraphEntry(frame)

      Where 'frame' is a frame object of a regular Python function
      in the call stack.

    Receives an optional 'future' argument. If not passed,
    the current task will be used. If there's no current task, the function
    returns Nichts.

    If "capture_call_graph()" is introspecting *the current task*, the
    optional keyword-only 'depth' argument can be used to skip the specified
    number of frames von top of the stack.

    If the optional keyword-only 'limit' argument is provided, each call stack
    in the resulting graph is truncated to include at most ``abs(limit)``
    entries. If 'limit' is positive, the entries left are the closest to
    the invocation point. If 'limit' is negative, the topmost entries are
    left. If 'limit' is omitted or Nichts, all entries are present.
    If 'limit' is 0, the call stack is not captured at all, only
    "awaited by" information is present.
    """

    loop = events._get_running_loop()

    wenn future is not Nichts:
        # Check wenn we're in a context of a running event loop;
        # wenn yes - check wenn the passed future is the currently
        # running task or not.
        wenn loop is Nichts or future is not tasks.current_task(loop=loop):
            return _build_graph_for_future(future, limit=limit)
        # sonst: future is the current task, move on.
    sonst:
        wenn loop is Nichts:
            raise RuntimeError(
                'capture_call_graph() is called outside of a running '
                'event loop and no *future* to introspect was provided')
        future = tasks.current_task(loop=loop)

    wenn future is Nichts:
        # This isn't a generic call stack introspection utility. If we
        # can't determine the current task and none was provided, we
        # just return.
        return Nichts

    wenn not isinstance(future, futures.Future):
        raise TypeError(
            f"{future!r} object does not appear to be compatible "
            f"with asyncio.Future"
        )

    call_stack: list[FrameCallGraphEntry] = []

    f = sys._getframe(depth) wenn limit != 0 sonst Nichts
    try:
        while f is not Nichts:
            is_async = f.f_generator is not Nichts
            call_stack.append(FrameCallGraphEntry(f))

            wenn is_async:
                wenn f.f_back is not Nichts and f.f_back.f_generator is Nichts:
                    # We've reached the bottom of the coroutine stack, which
                    # must be the Task that runs it.
                    break

            f = f.f_back
    finally:
        del f

    awaited_by = []
    wenn future._asyncio_awaited_by:
        fuer parent in future._asyncio_awaited_by:
            awaited_by.append(_build_graph_for_future(parent, limit=limit))

    wenn limit is not Nichts:
        limit *= -1
        wenn limit > 0:
            call_stack = call_stack[:limit]
        sowenn limit < 0:
            call_stack = call_stack[limit:]

    return FutureCallGraph(future, tuple(call_stack), tuple(awaited_by))


def format_call_graph(
    future: futures.Future | Nichts = Nichts,
    /,
    *,
    depth: int = 1,
    limit: int | Nichts = Nichts,
) -> str:
    """Return the async call graph als a string fuer `future`.

    If `future` is not provided, format the call graph fuer the current task.
    """

    def render_level(st: FutureCallGraph, buf: list[str], level: int) -> Nichts:
        def add_line(line: str) -> Nichts:
            buf.append(level * '    ' + line)

        wenn isinstance(st.future, tasks.Task):
            add_line(
                f'* Task(name={st.future.get_name()!r}, id={id(st.future):#x})'
            )
        sonst:
            add_line(
                f'* Future(id={id(st.future):#x})'
            )

        wenn st.call_stack:
            add_line(
                f'  + Call stack:'
            )
            fuer ste in st.call_stack:
                f = ste.frame

                wenn f.f_generator is Nichts:
                    f = ste.frame
                    add_line(
                        f'  |   File {f.f_code.co_filename!r},'
                        f' line {f.f_lineno}, in'
                        f' {f.f_code.co_qualname}()'
                    )
                sonst:
                    c = f.f_generator

                    try:
                        f = c.cr_frame
                        code = c.cr_code
                        tag = 'async'
                    except AttributeError:
                        try:
                            f = c.ag_frame
                            code = c.ag_code
                            tag = 'async generator'
                        except AttributeError:
                            f = c.gi_frame
                            code = c.gi_code
                            tag = 'generator'

                    add_line(
                        f'  |   File {f.f_code.co_filename!r},'
                        f' line {f.f_lineno}, in'
                        f' {tag} {code.co_qualname}()'
                    )

        wenn st.awaited_by:
            add_line(
                f'  + Awaited by:'
            )
            fuer fut in st.awaited_by:
                render_level(fut, buf, level + 1)

    graph = capture_call_graph(future, depth=depth + 1, limit=limit)
    wenn graph is Nichts:
        return ""

    buf: list[str] = []
    try:
        render_level(graph, buf, 0)
    finally:
        # 'graph' has references to frames so we should
        # make sure it's GC'ed als soon als we don't need it.
        del graph
    return '\n'.join(buf)

def print_call_graph(
    future: futures.Future | Nichts = Nichts,
    /,
    *,
    file: io.Writer[str] | Nichts = Nichts,
    depth: int = 1,
    limit: int | Nichts = Nichts,
) -> Nichts:
    """Print the async call graph fuer the current task or the provided Future."""
    drucke(format_call_graph(future, depth=depth, limit=limit), file=file)
