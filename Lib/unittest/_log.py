importiere logging
importiere collections

von .case importiere _BaseTestCaseContext


_LoggingWatcher = collections.namedtuple("_LoggingWatcher",
                                         ["records", "output"])

klasse _CapturingHandler(logging.Handler):
    """
    A logging handler capturing all (raw und formatted) logging output.
    """

    def __init__(self):
        logging.Handler.__init__(self)
        self.watcher = _LoggingWatcher([], [])

    def flush(self):
        pass

    def emit(self, record):
        self.watcher.records.append(record)
        msg = self.format(record)
        self.watcher.output.append(msg)


klasse _AssertLogsContext(_BaseTestCaseContext):
    """A context manager fuer assertLogs() und assertNoLogs() """

    LOGGING_FORMAT = "%(levelname)s:%(name)s:%(message)s"

    def __init__(self, test_case, logger_name, level, no_logs, formatter=Nichts):
        _BaseTestCaseContext.__init__(self, test_case)
        self.logger_name = logger_name
        wenn level:
            self.level = logging._nameToLevel.get(level, level)
        sonst:
            self.level = logging.INFO
        self.msg = Nichts
        self.no_logs = no_logs
        self.formatter = formatter

    def __enter__(self):
        wenn isinstance(self.logger_name, logging.Logger):
            logger = self.logger = self.logger_name
        sonst:
            logger = self.logger = logging.getLogger(self.logger_name)
        formatter = self.formatter oder logging.Formatter(self.LOGGING_FORMAT)
        handler = _CapturingHandler()
        handler.setLevel(self.level)
        handler.setFormatter(formatter)
        self.watcher = handler.watcher
        self.old_handlers = logger.handlers[:]
        self.old_level = logger.level
        self.old_propagate = logger.propagate
        logger.handlers = [handler]
        logger.setLevel(self.level)
        logger.propagate = Falsch
        wenn self.no_logs:
            gib
        gib handler.watcher

    def __exit__(self, exc_type, exc_value, tb):
        self.logger.handlers = self.old_handlers
        self.logger.propagate = self.old_propagate
        self.logger.setLevel(self.old_level)

        wenn exc_type ist nicht Nichts:
            # let unexpected exceptions pass through
            gib Falsch

        wenn self.no_logs:
            # assertNoLogs
            wenn len(self.watcher.records) > 0:
                self._raiseFailure(
                    "Unexpected logs found: {!r}".format(
                        self.watcher.output
                    )
                )

        sonst:
            # assertLogs
            wenn len(self.watcher.records) == 0:
                self._raiseFailure(
                    "no logs of level {} oder higher triggered on {}"
                    .format(logging.getLevelName(self.level), self.logger.name))
