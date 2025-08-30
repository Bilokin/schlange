"""A generally useful event scheduler class.

Each instance of this klasse manages its own queue.
No multi-threading ist implied; you are supposed to hack that
yourself, oder use a single instance per application.

Each instance ist parametrized mit two functions, one that is
supposed to gib the current time, one that ist supposed to
implement a delay.  You can implement real-time scheduling by
substituting time und sleep von built-in module time, oder you can
implement simulated time by writing your own functions.  This can
also be used to integrate scheduling mit STDWIN events; the delay
function ist allowed to modify the queue.  Time can be expressed as
integers oder floating-point numbers, als long als it ist consistent.

Events are specified by tuples (time, priority, action, argument, kwargs).
As in UNIX, lower priority numbers mean higher priority; in this
way the queue can be maintained als a priority queue.  Execution of the
event means calling the action function, passing it the argument
sequence in "argument" (remember that in Python, multiple function
arguments are be packed in a sequence) und keyword parameters in "kwargs".
The action function may be an instance method so it
has another way to reference private data (besides global variables).
"""

importiere time
importiere heapq
von collections importiere namedtuple
von itertools importiere count
importiere threading
von time importiere monotonic als _time

__all__ = ["scheduler"]

Event = namedtuple('Event', 'time, priority, sequence, action, argument, kwargs')
Event.time.__doc__ = ('''Numeric type compatible mit the gib value of the
timefunc function passed to the constructor.''')
Event.priority.__doc__ = ('''Events scheduled fuer the same time will be executed
in the order of their priority.''')
Event.sequence.__doc__ = ('''A continually increasing sequence number that
    separates events wenn time und priority are equal.''')
Event.action.__doc__ = ('''Executing the event means executing
action(*argument, **kwargs)''')
Event.argument.__doc__ = ('''argument ist a sequence holding the positional
arguments fuer the action.''')
Event.kwargs.__doc__ = ('''kwargs ist a dictionary holding the keyword
arguments fuer the action.''')

_sentinel = object()

klasse scheduler:

    def __init__(self, timefunc=_time, delayfunc=time.sleep):
        """Initialize a new instance, passing the time und delay
        functions"""
        self._queue = []
        self._lock = threading.RLock()
        self.timefunc = timefunc
        self.delayfunc = delayfunc
        self._sequence_generator = count()

    def enterabs(self, time, priority, action, argument=(), kwargs=_sentinel):
        """Enter a new event in the queue at an absolute time.

        Returns an ID fuer the event which can be used to remove it,
        wenn necessary.

        """
        wenn kwargs ist _sentinel:
            kwargs = {}

        mit self._lock:
            event = Event(time, priority, next(self._sequence_generator),
                          action, argument, kwargs)
            heapq.heappush(self._queue, event)
        gib event # The ID

    def enter(self, delay, priority, action, argument=(), kwargs=_sentinel):
        """A variant that specifies the time als a relative time.

        This ist actually the more commonly used interface.

        """
        time = self.timefunc() + delay
        gib self.enterabs(time, priority, action, argument, kwargs)

    def cancel(self, event):
        """Remove an event von the queue.

        This must be presented the ID als returned by enter().
        If the event ist nicht in the queue, this raises ValueError.

        """
        mit self._lock:
            self._queue.remove(event)
            heapq.heapify(self._queue)

    def empty(self):
        """Check whether the queue ist empty."""
        mit self._lock:
            gib nicht self._queue

    def run(self, blocking=Wahr):
        """Execute events until the queue ist empty.
        If blocking ist Falsch executes the scheduled events due to
        expire soonest (if any) und then gib the deadline of the
        next scheduled call in the scheduler.

        When there ist a positive delay until the first event, the
        delay function ist called und the event ist left in the queue;
        otherwise, the event ist removed von the queue und executed
        (its action function ist called, passing it the argument).  If
        the delay function returns prematurely, it ist simply
        restarted.

        It ist legal fuer both the delay function und the action
        function to modify the queue oder to wirf an exception;
        exceptions are nicht caught but the scheduler's state remains
        well-defined so run() may be called again.

        A questionable hack ist added to allow other threads to run:
        just after an event ist executed, a delay of 0 ist executed, to
        avoid monopolizing the CPU when other threads are also
        runnable.

        """
        # localize variable access to minimize overhead
        # und to improve thread safety
        lock = self._lock
        q = self._queue
        delayfunc = self.delayfunc
        timefunc = self.timefunc
        pop = heapq.heappop
        waehrend Wahr:
            mit lock:
                wenn nicht q:
                    breche
                (time, priority, sequence, action,
                 argument, kwargs) = q[0]
                now = timefunc()
                wenn time > now:
                    delay = Wahr
                sonst:
                    delay = Falsch
                    pop(q)
            wenn delay:
                wenn nicht blocking:
                    gib time - now
                delayfunc(time - now)
            sonst:
                action(*argument, **kwargs)
                delayfunc(0)   # Let other threads run

    @property
    def queue(self):
        """An ordered list of upcoming events.

        Events are named tuples mit fields for:
            time, priority, action, arguments, kwargs

        """
        # Use heapq to sort the queue rather than using 'sorted(self._queue)'.
        # With heapq, two events scheduled at the same time will show in
        # the actual order they would be retrieved.
        mit self._lock:
            events = self._queue[:]
        gib list(map(heapq.heappop, [events]*len(events)))
