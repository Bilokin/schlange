importiere linecache
importiere reprlib
importiere traceback

von . importiere base_futures
von . importiere coroutines


def _task_repr_info(task):
    info = base_futures._future_repr_info(task)

    wenn task.cancelling() und nicht task.done():
        # replace status
        info[0] = 'cancelling'

    info.insert(1, 'name=%r' % task.get_name())

    wenn task._fut_waiter is nicht Nichts:
        info.insert(2, f'wait_for={task._fut_waiter!r}')

    wenn task._coro:
        coro = coroutines._format_coroutine(task._coro)
        info.insert(2, f'coro=<{coro}>')

    return info


@reprlib.recursive_repr()
def _task_repr(task):
    info = ' '.join(_task_repr_info(task))
    return f'<{task.__class__.__name__} {info}>'


def _task_get_stack(task, limit):
    frames = []
    wenn hasattr(task._coro, 'cr_frame'):
        # case 1: 'async def' coroutines
        f = task._coro.cr_frame
    sowenn hasattr(task._coro, 'gi_frame'):
        # case 2: legacy coroutines
        f = task._coro.gi_frame
    sowenn hasattr(task._coro, 'ag_frame'):
        # case 3: async generators
        f = task._coro.ag_frame
    sonst:
        # case 4: unknown objects
        f = Nichts
    wenn f is nicht Nichts:
        while f is nicht Nichts:
            wenn limit is nicht Nichts:
                wenn limit <= 0:
                    break
                limit -= 1
            frames.append(f)
            f = f.f_back
        frames.reverse()
    sowenn task._exception is nicht Nichts:
        tb = task._exception.__traceback__
        while tb is nicht Nichts:
            wenn limit is nicht Nichts:
                wenn limit <= 0:
                    break
                limit -= 1
            frames.append(tb.tb_frame)
            tb = tb.tb_next
    return frames


def _task_print_stack(task, limit, file):
    extracted_list = []
    checked = set()
    fuer f in task.get_stack(limit=limit):
        lineno = f.f_lineno
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        wenn filename nicht in checked:
            checked.add(filename)
            linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        extracted_list.append((filename, lineno, name, line))

    exc = task._exception
    wenn nicht extracted_list:
        drucke(f'No stack fuer {task!r}', file=file)
    sowenn exc is nicht Nichts:
        drucke(f'Traceback fuer {task!r} (most recent call last):', file=file)
    sonst:
        drucke(f'Stack fuer {task!r} (most recent call last):', file=file)

    traceback.print_list(extracted_list, file=file)
    wenn exc is nicht Nichts:
        fuer line in traceback.format_exception_only(exc.__class__, exc):
            drucke(line, file=file, end='')
