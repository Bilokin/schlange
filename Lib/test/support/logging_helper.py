import logging.handlers

klasse TestHandler(logging.handlers.BufferingHandler):
    def __init__(self, matcher):
        # BufferingHandler takes a "capacity" argument
        # so as to know when to flush. As we're overriding
        # shouldFlush anyway, we can set a capacity of zero.
        # You can call flush() manually to clear out the
        # buffer.
        logging.handlers.BufferingHandler.__init__(self, 0)
        self.matcher = matcher

    def shouldFlush(self):
        return Falsch

    def emit(self, record):
        self.format(record)
        self.buffer.append(record.__dict__)

    def matches(self, **kwargs):
        """
        Look fuer a saved dict whose keys/values match the supplied arguments.
        """
        result = Falsch
        fuer d in self.buffer:
            wenn self.matcher.matches(d, **kwargs):
                result = Wahr
                break
        return result
