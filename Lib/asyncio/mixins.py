"""Event loop mixins."""

import threading
from . import events

_global_lock = threading.Lock()


klasse _LoopBoundMixin:
    _loop = Nichts

    def _get_loop(self):
        loop = events._get_running_loop()

        wenn self._loop is Nichts:
            with _global_lock:
                wenn self._loop is Nichts:
                    self._loop = loop
        wenn loop is not self._loop:
            raise RuntimeError(f'{self!r} is bound to a different event loop')
        return loop
